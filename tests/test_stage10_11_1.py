import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from companion.experimental_spawn import ExperimentalClient, GUID, AUTHORIZATION
from companion.experimental_wait import wait_ready, ContinuationClient, verify_history
from companion.compatibility import file_hash
from test_stage10_11 import FakeTransport


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=100.;self.mono=10.;self.delay=5.;self.polls=[]
        self.c=ExperimentalClient(FakeTransport(),dict(guid=GUID,build=1287369,key='a'*32),
                                  self.tmp.name,clock=lambda:self.now)
        self.c.record('probe.json',dict(prepared_at=100.,session='abc-1',nonce='b'*32,
            guid=GUID,context=dict(player=1)))
    def sleep(self,n):self.now+=n;self.mono+=n
    def status(self):
        self.polls.append(self.now)
        phase='GROUND' if self.now-100<self.delay/2 else 'PATH'
        if self.now-100>=self.delay:phase='READY'
        return dict(state=phase,session='abc-1',probe='b'*32,player=1)
    def wait(self,**kwargs):
        with patch.object(self.c,'status',side_effect=self.status):
            return wait_ready(self.c,monotonic=lambda:self.mono,sleep=self.sleep,**kwargs)
    def test_callback_5_seconds(self):
        self.delay=5;r=self.wait();self.assertTrue(r['confirmation_window_sufficient'])
        self.assertAlmostEqual(r['remaining_seconds'],15)
    def test_callback_10_seconds(self):
        self.delay=10;r=self.wait();self.assertTrue(r['confirmation_window_sufficient'])
        self.assertAlmostEqual(r['confirmation_budget_seconds'],8)
    def test_callback_15_seconds(self):
        self.delay=15;r=self.wait();self.assertEqual(r['status'],'READY')
        self.assertFalse(r['confirmation_window_sufficient'])
        self.assertAlmostEqual(r['remaining_seconds'],5)
    def test_interval_500_ms(self):
        self.wait(interval=.5)
        self.assertTrue(all(b-a==.5 for a,b in zip(self.polls,self.polls[1:])))
    def test_interval_invalid(self):
        for n in (.1,1,float('nan')):
            with self.assertRaises(ValueError):self.wait(interval=n)
    def test_never_ready_full_deadline(self):
        self.delay=30
        with self.assertRaises(TimeoutError):self.wait()
        self.assertAlmostEqual(self.now,120)
        self.assertTrue((self.c.journal/'wait-stopped.json').exists())
        self.assertFalse(self.c.intent_file.exists())
    def test_ready_response_after_deadline(self):
        def status():self.sleep(21);return dict(state='READY')
        self.status=status
        with self.assertRaises(TimeoutError):self.wait()
    def test_stopped(self):
        self.status=lambda:dict(state='STOPPED',session='abc-1',probe='b'*32,player=1,reason='ground_refused')
        with self.assertRaisesRegex(ValueError,'ground_refused'):self.wait()
    def test_unknown_state(self):
        self.status=lambda:dict(state='NEW',session='abc-1',probe='b'*32,player=1)
        with self.assertRaisesRegex(ValueError,'PROBE_NEW'):self.wait()
    def test_session_change(self):
        self.status=lambda:dict(state='READY',session='new-2',probe='b'*32,player=1)
        with self.assertRaisesRegex(ValueError,'CONTEXT'):self.wait()
    def test_transport_timeout_not_retried(self):
        self.status=lambda:(_ for _ in ()).throw(TimeoutError('bridge'))
        with self.assertRaisesRegex(TimeoutError,'bridge'):self.wait()
        self.assertFalse(self.c.intent_file.exists())
    def test_clock_jump(self):
        def status():self.now-=2;return dict(state='GROUND')
        self.status=status
        with self.assertRaisesRegex(ValueError,'CLOCK'):self.wait()
    def test_resumed_wait_does_not_reset_deadline(self):
        self.now=117;self.delay=30
        with self.assertRaises(TimeoutError):self.wait()
        self.assertEqual(self.now,120)
    def test_stopped_wait_cannot_restart(self):
        self.c.record('wait-stopped.json',dict(error='bridge'))
        with self.assertRaisesRegex(ValueError,'ALREADY_STOPPED'):self.wait()


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.now=100
        (self.root/'probe.json').write_text('{"history":"preserve"}')
        self.old=(self.root/'probe.json').read_bytes()
        self.plan=dict(attempt='attempts/'+'c'*32,previous_session='old-1',
            history={'probe.json':file_hash(self.root/'probe.json')})
        self.t=FakeTransport();self.binding=dict(guid=GUID,build=1287369,key='a'*32)
        self.c=ContinuationClient(self.t,self.binding,self.root,self.plan,clock=lambda:self.now)
    def prepare(self):self.c.prepare()
    def window(self,sufficient=True):
        p=json.loads((self.c.journal/'probe.json').read_text())
        self.c.record('ready-window.json',dict(confirmation_window_sufficient=sufficient,
            probe=p['nonce'],session=p['session']))
    def spawn(self):return self.c.spawn_once(authorization=AUTHORIZATION,clear_area=True,disposable_risk=True)
    def test_previous_probe_preserved(self):
        self.prepare();self.assertEqual((self.root/'probe.json').read_bytes(),self.old)
    def test_second_prepare_forbidden(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'ALREADY_RECORDED'):self.prepare()
    def test_same_session_forbidden(self):
        self.plan['previous_session']='abc-1'
        with self.assertRaisesRegex(ValueError,'NEW_GAME_SESSION'):self.prepare()
    def test_history_tamper_forbidden(self):
        (self.root/'probe.json').write_text('changed')
        with self.assertRaisesRegex(ValueError,'HISTORY'):self.prepare()
    def test_global_intent_shared(self):
        self.prepare();self.window();self.spawn()
        self.assertTrue((self.root/'spawn-intent.json').exists())
        self.assertFalse((self.c.journal/'spawn-intent.json').exists())
        old=ExperimentalClient(self.t,self.binding,self.root,clock=lambda:self.now)
        with self.assertRaisesRegex(ValueError,'CONSUMED'):old.prepare()
        with self.assertRaisesRegex(ValueError,'CONSUMED'):
            ContinuationClient(self.t,self.binding,self.root,self.plan)
    def test_insufficient_confirmation(self):
        self.prepare();self.window(False)
        with self.assertRaisesRegex(ValueError,'CONFIRMATION'):self.spawn()
        self.assertFalse(self.c.intent_file.exists())
    def test_delayed_confirmation(self):
        self.prepare();self.window();self.now=121
        with self.assertRaisesRegex(ValueError,'EXPIRED'):self.spawn()
        self.assertFalse(self.c.intent_file.exists())
    def test_status_consumes_remaining_send_time(self):
        self.prepare();self.window()
        original=self.c.status
        def slow():
            result=original();self.now=119;return result
        self.c.status=slow
        with self.assertRaisesRegex(ValueError,'SEND_MARGIN'):self.spawn()
        self.assertFalse(self.c.intent_file.exists())
    def test_unknown_other_attempt_blocked(self):
        p=self.root/'attempts/other';p.mkdir();(p/'probe.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'HISTORY'):
            verify_history(self.root,self.plan['history'],self.plan['attempt'])
    def test_lost_spawn_response_keeps_global_intent(self):
        self.prepare();self.window();self.t.lose=True
        with self.assertRaises(TimeoutError):self.spawn()
        self.assertTrue(self.c.intent_file.exists())
        with self.assertRaisesRegex(ValueError,'CONSUMED'):
            ContinuationClient(self.t,self.binding,self.root,self.plan)
    def test_journal_delay_blocks_late_send(self):
        self.prepare();self.window();record=self.c.record
        def slow(name,value):
            record(name,value)
            if name=='spawn-intent.json':self.now=119
        self.c.record=slow
        with self.assertRaisesRegex(ValueError,'DEADLINE_AFTER_JOURNAL'):self.spawn()
        self.assertTrue(self.c.intent_file.exists())
        self.assertFalse(any(x.startswith('aic_first_spawn.spawn ') for x in self.t.sent))

if __name__=='__main__':unittest.main()
