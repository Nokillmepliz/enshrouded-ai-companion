import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from companion.experimental_spawn import GUID,AUTHORIZATION
from companion.experimental_wait import ContinuationClient
from companion.interactive_spawn import run_interactive,WindowsKeyboard
from companion.compatibility import file_hash
from test_stage10_11 import FakeTransport


class Keyboard:
    def __init__(self,clock,events=(),held_until=0):
        self.clock=clock;self.events=list(events);self.held_until=held_until;self.discarded=[]
    def drain(self):
        while self.events and self.events[0][0]<=self.clock():self.discarded.append(self.events.pop(0)[1])
        return True
    def released(self):return self.clock()>=self.held_until
    def poll(self):
        if self.events and self.events[0][0]<=self.clock():return self.events.pop(0)[1]
        return None


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.now=100.;self.mono=10.;self.lines=[]
        (self.root/'probe.json').write_text('{"old":true}')
        self.plan=dict(attempt='attempts/'+'b'*32,previous_session='old-1',
            previous_sessions=['old-1','old-2'],confirmation_mode='local_key_after_ready',
            history={'probe.json':file_hash(self.root/'probe.json')})
        self.t=FakeTransport();self.binding=dict(guid=GUID,build=1287369,key='a'*32)
        self.c=ContinuationClient(self.t,self.binding,self.root,self.plan,clock=lambda:self.now)
    def sleep(self,seconds):self.now+=seconds;self.mono+=seconds
    def run_cli(self,events=(),held_until=0,**kwargs):
        self.k=Keyboard(lambda:self.now,events,held_until)
        return run_interactive(self.c,self.k,monotonic=lambda:self.mono,sleep=self.sleep,
            output=self.lines.append,**kwargs)
    def spawn_count(self):return sum(s.startswith('aic_first_spawn.spawn ') for s in self.t.sent)
    def assert_none(self):self.assertEqual(self.spawn_count(),0);self.assertFalse(self.c.intent_file.exists())
    def test_fresh_y_without_enter(self):
        r=self.run_cli([(101,'Y')]);self.assertEqual(r['status'],'SPAWN_REPLY_RECEIVED_UNVERIFIED')
        self.assertEqual(self.spawn_count(),1);self.assertTrue(self.c.intent_file.exists())
        self.assertTrue((self.c.journal/'local-confirmation.json').exists())
    def test_lowercase_y(self):self.run_cli([(101,'y')]);self.assertEqual(self.spawn_count(),1)
    def test_n_cancels(self):
        self.assertEqual(self.run_cli([(101,'N')])['status'],'CANCELLED_BY_USER');self.assert_none()
    def test_escape_cancels(self):
        self.assertEqual(self.run_cli([(101,'\x1b')])['status'],'CANCELLED_BY_USER');self.assert_none()
    def test_n_during_arming_cancels(self):
        self.assertEqual(self.run_cli([(100.1,'N')])['status'],'CANCELLED_BY_USER');self.assert_none()
    def test_deadline_cancels(self):
        self.assertEqual(self.run_cli()['status'],'CONFIRMATION_TIMEOUT');self.assert_none()
    def test_late_y_cannot_spawn(self):self.run_cli([(119,'Y')]);self.assert_none()
    def test_prebuffered_y_discarded(self):
        self.run_cli([(99,'Y')]);self.assertIn('Y',self.k.discarded);self.assert_none()
    def test_y_during_arming_discarded(self):self.run_cli([(100.1,'Y')]);self.assert_none()
    def test_held_early_y_repeat_discarded(self):
        self.run_cli([(t,'Y') for t in (99,100,101,102,103,104)],held_until=105);self.assert_none()
    def test_fresh_press_after_release(self):
        self.run_cli([(99,'Y'),(101,'Y'),(103,'Y'),(106,'Y')],held_until=105)
        self.assertEqual(self.spawn_count(),1)
    def test_held_until_deadline(self):self.run_cli([(99,'Y')],held_until=130);self.assert_none()
    def test_enter_is_not_consent(self):self.run_cli([(101,'\r')]);self.assert_none()
    def test_countdown_and_coordinates_shown(self):
        self.run_cli([(101,'N')])
        self.assertTrue(any(s.startswith('READY:') for s in self.lines))
        self.assertTrue(any('До отмены:' in s for s in self.lines))
    def test_restart_after_cancel_forbidden(self):
        self.run_cli([(101,'N')]);sent=list(self.t.sent)
        with self.assertRaises(FileExistsError):self.run_cli([(102,'Y')])
        self.assertEqual(self.t.sent,sent)
    def test_no_repeat_after_success(self):
        self.run_cli([(101,'Y')])
        with self.assertRaises(FileExistsError):self.run_cli([(102,'Y')])
        self.assertEqual(self.spawn_count(),1)
    def test_no_repeat_after_lost_reply(self):
        self.t.lose=True
        with self.assertRaises(TimeoutError):self.run_cli([(101,'Y')])
        self.assertEqual(self.spawn_count(),1);self.assertTrue(self.c.intent_file.exists())
        with self.assertRaises(FileExistsError):self.run_cli([(102,'Y')])
    def test_generic_spawn_without_local_key_rejected(self):
        self.c.prepare()
        p=json.loads((self.c.journal/'probe.json').read_text())
        self.c.record('ready-window.json',dict(probe=p['nonce'],session=p['session'],confirmation_window_sufficient=True))
        with self.assertRaisesRegex(ValueError,'LOCAL_KEY_CONFIRMATION_REQUIRED'):
            self.c.spawn_once(authorization=AUTHORIZATION,clear_area=True,disposable_risk=True)
        self.assert_none()
    def test_previous_session_rejected(self):
        self.plan['previous_sessions'].append('abc-1')
        with self.assertRaisesRegex(ValueError,'NEW_GAME_SESSION'):self.run_cli([(101,'Y')])
        self.assert_none()
    def test_session_changed_before_y(self):
        original=self.c.spawn_once
        def changed(**kwargs):
            self.t.data['player']['id']=2
            return original(**kwargs)
        self.c.spawn_once=changed
        with self.assertRaisesRegex(ValueError,'CONTEXT'):self.run_cli([(101,'Y')])
        self.assert_none()
    def test_confirmation_journal_delay(self):
        record=self.c.record
        def slow(name,value):
            record(name,value)
            if name=='local-confirmation.json':self.sleep(20)
        self.c.record=slow
        r=self.run_cli([(101,'Y')]);self.assertEqual(r['status'],'CONFIRMATION_TIMEOUT_AFTER_JOURNAL');self.assert_none()
    def test_clock_jump_cancels(self):
        def jump(seconds):self.now+=seconds+1;self.mono+=seconds
        self.sleep=jump
        with self.assertRaisesRegex(ValueError,'CLOCK_CHANGED'):self.run_cli([(101,'Y')])
        self.assert_none()
    def test_insufficient_ready_window(self):
        def late(client,**kwargs):
            self.sleep(15)
            return dict(deadline_unix=120,confirmation_window_sufficient=False)
        r=self.run_cli([(116,'Y')],waiter=late)
        self.assertEqual(r['status'],'INSUFFICIENT_CONFIRMATION_WINDOW');self.assert_none()
    def test_cancel_during_wait(self):
        def waiting(client,**kwargs):
            self.sleep(1)
            if kwargs['cancelled']():raise ValueError('CANCELLED_BY_USER')
            self.fail('Expected cancel')
        with self.assertRaisesRegex(ValueError,'CANCELLED_BY_USER'):self.run_cli([(101,'N')],waiter=waiting)
        self.assert_none()
    def test_non_console_rejected(self):
        with patch('sys.stdin.isatty',return_value=False):
            with self.assertRaisesRegex(ValueError,'CONSOLE'):WindowsKeyboard()
    def test_extended_key_scan_code_y_is_discarded(self):
        from unittest.mock import Mock
        keyboard=WindowsKeyboard.__new__(WindowsKeyboard)
        keyboard.msvcrt=Mock()
        keyboard.msvcrt.kbhit.side_effect=[True,True]
        keyboard.msvcrt.getwch.side_effect=['\xe0','Y']
        self.assertIsNone(keyboard.poll())
    def test_incomplete_extended_key_fails_closed(self):
        from unittest.mock import Mock
        keyboard=WindowsKeyboard.__new__(WindowsKeyboard)
        keyboard.msvcrt=Mock()
        keyboard.msvcrt.kbhit.side_effect=[True,False]
        keyboard.msvcrt.getwch.return_value='\xe0'
        with self.assertRaisesRegex(ValueError,'EXTENDED'):keyboard.poll()

if __name__=='__main__':unittest.main()
