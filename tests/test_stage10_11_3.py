import json
import copy
from pathlib import Path
import tempfile
import unittest

from lupa.lua54 import LuaRuntime
from companion.compatibility import file_hash
from companion.smart_position import SmartPositionClient
from companion.interactive_spawn import run_interactive
from companion.experimental_spawn import GUID
from companion.smart_deployment import check_manifest,verify as verify_deployment,CHANGED
from unittest.mock import patch
from test_stage10_11 import FIXTURE, FakeTransport
import test_stage10_11 as legacy
from test_stage10_11_2 import Keyboard

ROOT=Path(__file__).resolve().parents[1]
SEARCH_FIXTURE='''
grounds={};paths={};events={}
api.ground=function(w,x,z,cb)
 table.insert(grounds,{x=x,z=z,cb=cb});return ground_ok
end
api.path=function(w,a,b,opts,cb)
 table.insert(paths,{at=b,cb=cb});options=opts;return path_ok and 1 or nil
end
api.diagnostic=function(event,data) table.insert(events,{event=event,data=data}) end
function answer(i,ok,y,fog,water,x,z)
 local q=grounds[i];q.cb({},ok~=false,x or q.x,y or 10,z or q.z,'api_reason',2,fog or 'none',water)
end
function all_ground() for i=1,#grounds do answer(i) end end
function path_answer(i,status)
 local q=paths[i];local at=q.at
 q.cb({},{status=status or 'found',reaches=true,length=4,count=1},{{x=at.x,y=at.y,z=at.z,move=0}})
end
function ready() begin();all_ground();path_answer(1) end
function reason_at(i)
 for _,e in ipairs(events) do if e.event=='REJECT' and e.data.candidate==i then return e.data.reason end end
end
'''


class SmartLuaTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE+SEARCH_FIXTURE)
        self.lua.globals().policy=self.lua.execute((ROOT/'mods/aic_first_spawn/controller.lua').read_text())
        self.lua.execute('c=policy.new(api,binding)')
    def run_lua(self,s):self.lua.execute(s)
    def val(self,s):return self.lua.eval(s)
    def test_eight_bounded_requests_at_four_metres(self):
        self.run_lua('begin()')
        self.assertEqual(self.val('#grounds'),8);self.assertEqual(self.val('c.status({}).pending'),8)
        for i in range(1,9):self.assertAlmostEqual(self.val(f'grounds[{i}].x^2+grounds[{i}].z^2'),16)
        self.assertEqual(self.val('#paths'),0);self.assertEqual(self.val('calls'),0)
    def test_waits_for_every_ground_then_first_direction(self):
        self.run_lua('begin();for i=8,2,-1 do answer(i) end')
        self.assertEqual(self.val('#paths'),0)
        self.run_lua('answer(1);path_answer(1)')
        self.assertEqual(self.val('c.status({}).candidate'),1)
    def test_next_direction_after_ground_wall_and_path_rejections(self):
        self.run_lua('''api.wall=function(w,a,b) return b.x>2 and b.z>2 end
begin();answer(1,false);for i=2,8 do answer(i) end;path_answer(1,'not_found');path_answer(2)''')
        self.assertEqual(self.val('c.status({}).candidate'),4)
        self.assertEqual(self.val('reason_at(1)'),'ground_api_not_ok')
        self.assertEqual(self.val('reason_at(2)'),'building_obstruction')
        self.assertEqual(self.val('reason_at(3)'),'path_not_found')
    def test_ground_diagnostics_and_reasons(self):
        cases=[('false,0','ground_api_not_ok'),('true,12','ground_height_delta'),
               ("true,10,'unknown'",'ground_fog_unknown'),("true,10,'shroud'",'ground_fog_unsafe'),
               ("true,10,'none',11",'ground_water_present'),("true,10,'none',nil,7",'ground_xz_mismatch'),
               ('true,0/0','ground_invalid_coordinates')]
        for args,expected in cases:
            with self.subTest(expected=expected):
                self.setUp();self.run_lua('begin();answer(1,'+args+')')
                self.assertEqual(self.val('reason_at(1)'),expected)
                data=self.val('events[9].data')
                self.assertEqual(data['requested_x'],4);self.assertEqual(data['player_y'],10)
                self.assertEqual(data['why'],'api_reason');self.assertEqual(data['hop_y'],2)
                self.assertIsNotNone(data['water_y']);self.assertIsNotNone(data['delta_y'])
    def test_api_failure_y_is_labelled_unmeasured(self):
        self.run_lua('begin();answer(1,false,0)')
        self.assertFalse(self.val('events[9].data.ground_y_measured'))
    def test_refused_ground_queue_is_drained(self):
        self.run_lua('ground_ok=false;begin()')
        self.assertEqual(self.val('c.reason'),'no_safe_candidate')
        self.assertEqual(self.val('reason_at(1)'),'ground_request_refused')
        self.assertEqual(self.val('c.status({}).pending'),0)
    def test_api_exception_blocks_new_queue(self):
        self.run_lua("api.ground=function() error('after submit unknown') end;begin()")
        self.assertEqual(self.val('c.reason'),'ground_api_error_pending_unknown')
        self.assertFalse(self.val('c.status({}).recoverable'))
        self.run_lua("c.probe({},session,player,'new')")
        self.assertEqual(self.val('c.reason'),'queries_pending')
    def test_timeout_does_not_abandon_pending_requests(self):
        self.run_lua("begin();t=121;c.status({});c.probe({},session,player,'second')")
        self.assertEqual(self.val('#grounds'),8)
        self.run_lua('all_ground()')
        self.assertEqual(self.val('#paths'),0);self.assertEqual(self.val('c.status({}).pending'),0)
        self.run_lua("c.probe({},session,player,'third')")
        self.assertEqual(self.val('#grounds'),16)
    def test_duplicate_callback_does_not_decrement_twice(self):
        self.run_lua('begin();answer(1);answer(1)')
        self.assertEqual(self.val('c.status({}).pending'),7)
    def test_new_manual_search_same_session_after_no_candidate(self):
        self.run_lua("begin();for i=1,8 do answer(i,false) end;c.probe({},session,player,'second')")
        self.assertEqual(self.val('#grounds'),16);self.assertEqual(self.val('c.state'),'GROUND')
    def test_same_nonce_is_rejected(self):
        self.run_lua('ready();begin()')
        self.assertEqual(self.val('c.reason'),'probe_nonce_reused');self.assertEqual(self.val('#grounds'),8)
    def test_old_duplicate_callback_does_not_affect_new_search(self):
        self.run_lua("ready();c.probe({},session,player,'new');answer(1)")
        self.assertEqual(self.val('c.status({}).pending'),8);self.assertEqual(self.val('c.state'),'GROUND')
    def test_path_failures_try_each_candidate_once(self):
        self.run_lua("begin();all_ground();for i=1,8 do path_answer(i,'not_found') end")
        self.assertEqual(self.val('#paths'),8);self.assertEqual(self.val('c.reason'),'no_safe_candidate')
    def test_path_submission_refused(self):
        self.run_lua('path_ok=false;begin();all_ground()')
        self.assertEqual(self.val('#paths'),8);self.assertEqual(self.val('c.status({}).pending'),0)
        self.assertEqual(self.val('reason_at(1)'),'path_refused')
    def test_path_exception_unknown_pending(self):
        self.run_lua("api.path=function() error('unknown') end;begin();all_ground()")
        self.assertEqual(self.val('c.reason'),'path_api_error_pending_unknown')
        self.assertFalse(self.val('c.status({}).recoverable'))
    def test_ground_callbacks_5_10_15_seconds_preserve_deadline(self):
        for delay in (5,10,15):
            with self.subTest(delay=delay):
                self.setUp();self.run_lua(f'begin();t=100+{delay};all_ground();path_answer(1)')
                self.assertEqual(self.val('c.state'),'READY')
                self.run_lua('t=121;spawn()');self.assertEqual(self.val('calls'),0)
    def test_final_revalidation_blocks_motion_session_wall_existing_npc(self):
        for change in ('px=1',"session='different'",'wall=true','candidate=true','t=121','spent=true'):
            with self.subTest(change=change):
                self.setUp();self.run_lua('ready();'+change+';spawn()');self.assertEqual(self.val('calls'),0)
    def test_partial_spawn_is_never_repeated_or_searched_again(self):
        for change in ('spawn_result=0','spawn_error=true','spawn_result=42'):
            with self.subTest(change=change):
                self.setUp();self.run_lua("ready();"+change+";spawn();c.probe({},session,player,'new');spawn()")
                self.assertEqual(self.val('calls'),1);self.assertEqual(self.val('#grounds'),8)
                self.assertFalse(self.val('c.status({}).recoverable'))
    def test_consume_failure_prevents_native_call(self):
        self.run_lua('ready();consume_ok=false;spawn()');self.assertEqual(self.val('calls'),0)
    def test_path_guards_are_preserved(self):
        for change,reason in [('r.reaches=false','path_not_reaching'),('r.count=2','path_count'),
                ('r.length=9','path_length'),('p[1].move=1','path_non_walk'),
                ('p[1].door=42','path_non_walk'),('p[1].x=99','path_endpoint'),
                ('p[1].y=0/0','path_non_walk')]:
            with self.subTest(reason=reason,change=change):
                self.setUp();self.run_lua('''begin();all_ground()
local r={status='found',reaches=true,length=4,count=1};local p={{x=4,y=10,z=0,move=0}}
'''+change+''';paths[1].cb({},r,p)''')
                self.assertEqual(self.val('reason_at(1)'),reason)
                self.assertEqual(self.val('c.state'),'PATH');self.assertEqual(self.val('#paths'),2)
    def test_wall_exception_stops_without_fallback(self):
        self.run_lua("api.wall=function() error('API failed') end;begin();all_ground()")
        self.assertEqual(self.val('c.reason'),'wall_api_error');self.assertEqual(self.val('#paths'),0)
    def test_late_path_cannot_make_stopped_controller_ready(self):
        self.run_lua('begin();all_ground();t=121;c.status({});path_answer(1)')
        self.assertEqual(self.val('c.state'),'STOPPED');self.assertEqual(self.val('c.status({}).pending'),0)


class SmartHostTests(legacy.LuaHostIntegrationTests):
    """Run existing real Lua host safety tests against 0.1.1 as well as legacy fixtures."""
    def reload(self):
        self.lua.globals().policy=self.lua.execute((ROOT/'mods/aic_first_spawn/controller.lua').read_text())
        self.lua.execute('''
host_grounds={};logs={}
emf.ground_at=function(w,x,z,cb) ground_cb=cb;table.insert(host_grounds,{x=x,z=z,cb=cb});return true end
emf.log=function(s) table.insert(logs,s) end
function host_ready()
 command('probe',session,player)
 for _,q in ipairs(host_grounds) do q.cb(w,true,q.x,10,q.z,'ok',nil,'none',nil) end
 path_cb(w,{status='found',reaches=true,length=4,count=1},{{x=4,y=10,z=0,move=0}})
end
''')
        self.lua.execute((ROOT/'mods/aic_first_spawn/main.lua').read_text())
    def test_invalid_ground_diagnostic_is_valid_json(self):
        self.run_lua("command('probe',session,player);host_grounds[1].cb(w,true,4,0/0,0,'ok',nil,'none',nil)")
        lines=list(self.lua.globals().logs.values())
        records=[json.loads(s.split(' ',2)[2]) for s in lines if s.startswith('AIC_POSITION GROUND ')]
        self.assertEqual(len(records),1);self.assertIsInstance(records[0]['y'],str)
    def test_response_size_with_long_session_coordinates_and_observe(self):
        self.run_lua("session=string.rep('a',64);host_ready();host_spawn();command('observe')")
        self.assertEqual(self.reply()['state'],'RETURNED_UNVERIFIED')
        self.assertLessEqual(len(self.lua.globals().response.split(' ',1)[1]),930)


class SmartTransport(FakeTransport):
    def __init__(self):
        super().__init__();self.pending=0;self.recoverable=True
        self.changed_position=False;self.invalid_position=False
        for m in self.data['mods']:
            if m['id']=='aic_first_spawn':m['version']='0.1.1'
    def console(self,*args,**kwargs):
        result=super().console(*args,**kwargs)
        value=json.loads(result['output'][0].split(' ',1)[1])
        value.update(pending=self.pending,recoverable=self.recoverable,attempted=False)
        value['position']=dict(x=4,y=10,z=0)
        if self.changed_position:value['position']=dict(x=90,y=10,z=0)
        if self.invalid_position:value['position']=None
        if self.phase=='STOPPED':value['ok']=False
        result['output']=['AIC_EXPERIMENT '+json.dumps(value)]
        return result


class SmartPythonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'old-history.json').write_text('{}')
        self.history={'old-history.json':file_hash(self.root/'old-history.json')}
        self.t=SmartTransport();self.now=100.;self.mono=10.;self.unused=True
        self.c=SmartPositionClient(self.t,dict(guid=GUID,build=1287369,key='a'*32),self.root,self.history,
                                  lambda:self.unused,clock=lambda:self.now)
    def sleep(self,s):self.now+=s;self.mono+=s
    def run_local(self,events):
        self.c.open_search()
        return run_interactive(self.c,Keyboard(lambda:self.now,events),monotonic=lambda:self.mono,
                               sleep=self.sleep,output=lambda s:None)
    def test_cancel_settle_and_manual_same_session_search(self):
        self.run_local([(101,'N')]);first=self.c.journal;self.c.settle_search()
        first_hash=file_hash(first/'closed.json');self.c.open_search();self.c.prepare()
        self.assertEqual(file_hash(first/'closed.json'),first_hash)
        self.assertNotEqual(json.loads((first/'probe.json').read_text())['nonce'],
                            json.loads((self.c.journal/'probe.json').read_text())['nonce'])
    def test_pending_queue_cannot_settle_or_search_again(self):
        self.c.open_search();self.c.prepare();self.t.pending=1
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):self.c.settle_search()
        with self.assertRaisesRegex(ValueError,'NOT_RECOVERABLE'):self.c.open_search()
    def test_timeout_drained_status_can_be_settled(self):
        self.c.open_search();self.c.prepare();self.t.phase='STOPPED'
        self.c.settle_search();self.c.open_search();self.c.prepare()
    def test_unsettled_search_blocks_new_process(self):
        self.c.open_search();self.c.prepare()
        with self.assertRaisesRegex(ValueError,'NOT_SETTLED'):self.c.open_search()
    def test_session_change_blocks_settlement(self):
        self.c.open_search();self.c.prepare()
        self.t.session='changed'
        # FakeTransport uses a constant session; alter one status result explicitly.
        status=self.c.status();status['session']='changed'
        with self.assertRaisesRegex(ValueError,'SESSION'):self.c.ledger.settle(status)
    def test_original_history_tampering_blocks(self):
        (self.root/'old-history.json').write_text('changed')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_HISTORY'):self.c.open_search()
    def test_settled_history_tampering_blocks(self):
        self.run_local([(101,'N')]);old=self.c.journal;self.c.settle_search()
        (old/'probe.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'HISTORY_CHANGED'):self.c.open_search()
    def test_global_intent_blocks_any_new_search(self):
        self.run_local([(101,'Y')])
        with self.assertRaisesRegex(ValueError,'SPENT_OR_UNKNOWN'):self.c.open_search()
        self.assertEqual(sum(s.startswith('aic_first_spawn.spawn ') for s in self.t.sent),1)
    def test_lost_spawn_reply_keeps_global_intent(self):
        self.t.lose=True
        with self.assertRaises(TimeoutError):self.run_local([(101,'Y')])
        self.assertTrue(self.c.intent_file.exists())
        with self.assertRaisesRegex(ValueError,'SPENT_OR_UNKNOWN'):self.c.settle_search()
    def test_spent_latch_blocks(self):
        self.unused=False
        with self.assertRaisesRegex(ValueError,'SPENT_OR_UNKNOWN'):self.c.open_search()
    def test_prebuffered_y_is_not_consent(self):
        self.run_local([(99,'Y')]);self.assertFalse(self.c.intent_file.exists())
    def test_escape_cancels_without_intent(self):
        self.assertEqual(self.run_local([(101,'\x1b')])['status'],'CANCELLED_BY_USER')
        self.assertFalse(self.c.intent_file.exists())
    def test_expired_confirmation_no_intent(self):
        self.assertEqual(self.run_local([(119,'Y')])['status'],'CONFIRMATION_TIMEOUT')
        self.assertFalse(self.c.intent_file.exists())
    def test_prepare_without_explicit_new_search_is_forbidden(self):
        with self.assertRaisesRegex(ValueError,'EXPLICIT_SEARCH'):self.c.prepare()
    def test_settled_client_cannot_later_spawn(self):
        self.run_local([(101,'N')]);old=self.c.journal;self.c.settle_search();self.c.journal=old
        with self.assertRaisesRegex(ValueError,'ALREADY_SETTLED'):self.c.status()
    def test_actual_session_change_before_key_still_blocks(self):
        original=self.c.spawn_once
        def changed(**kwargs):
            self.t.data['player']['id']=2
            return original(**kwargs)
        self.c.spawn_once=changed
        with self.assertRaisesRegex(ValueError,'CONTEXT_CHANGED'):self.run_local([(101,'Y')])
        self.assertFalse(self.c.intent_file.exists())
    def test_old_mod_version_is_rejected(self):
        for m in self.t.data['mods']:
            if m['id']=='aic_first_spawn':m['version']='0.1.0'
        with self.assertRaisesRegex(ValueError,'MOD_VERSION'):self.c.open_search()
    def test_inconsistent_ground_state_cannot_be_settled(self):
        self.c.open_search();self.c.prepare();self.t.phase='GROUND'
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):self.c.settle_search()
    def test_selected_position_change_before_spawn_blocks_intent(self):
        original=self.c.spawn_once
        def changed(**kwargs):
            self.t.changed_position=True
            return original(**kwargs)
        self.c.spawn_once=changed
        with self.assertRaisesRegex(ValueError,'SELECTED_POSITION_CHANGED'):self.run_local([(101,'Y')])
        self.assertFalse(self.c.intent_file.exists())
    def test_missing_ready_coordinates_cannot_authorize_spawn(self):
        self.t.invalid_position=True
        with self.assertRaisesRegex(ValueError,'SELECTED_POSITION_INVALID'):self.run_local([(101,'Y')])
        self.assertFalse(self.c.intent_file.exists())


class SmartDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.game=self.root/'game';self.game.mkdir()
        self.binding=dict(key='a'*32,guid=GUID,build=1287369)
        self.baseline=dict(game={},saves={'test.ksd':dict(sha256='save',size=1)})
        paths=sorted(CHANGED)+['emf/mods/aic_first_spawn/attempt.lock']+['old/'+str(i) for i in range(18)]
        rows=[];effective=[]
        for name in paths:
            p=self.game/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(('UNUSED:'+'a'*32).encode() if name.endswith('attempt.lock') else b'installed')
            digest=file_hash(p);size=p.stat().st_size
            self.baseline['game'][name]=dict(sha256='before' if name in CHANGED else digest,size=size)
            effective.append(dict(path=name,sha256=digest,bytes=size))
            if name in CHANGED:rows.append(dict(path=name,sha256=digest,bytes=size,before_sha256='before',before_bytes=size))
        self.manifest=dict(format='aic_smart_position_update_v1',version='0.1.1',entries=rows,
                           effective_files=effective,game=str(self.game))
        self.receipt=dict(format='aic_smart_position_receipt_v1',status='INSTALLED',manifest_sha256='m',
            effective_files=copy.deepcopy(effective),backup_path=str(self.root/'backup'),backup_manifest_sha256='b')
        self.bm=dict(files=[dict(relative='saves/test.ksd',sha256='save',bytes=1)]+
            [dict(relative='game/'+p,sha256='before',bytes=self.baseline['game'][p]['size']) for p in sorted(CHANGED)])
        self.plan=dict(manifest_path='manifest',manifest_sha256='m',baseline_path='baseline',baseline_sha256='base',
                       binding_path='binding',binding_sha256='key')
    def gate(self):
        values={'manifest':self.manifest,'baseline':self.baseline,'binding':self.binding,
                'receipt':self.receipt,'manifest.json':self.bm}
        with patch('companion.smart_deployment.read_pinned',side_effect=lambda p,h:values[p.name]),\
             patch('companion.smart_deployment.verify_backup') as backup:
            value=verify_deployment(self.plan,Path('receipt'),'r');backup.assert_called_once();return value
    def test_verified_gate(self):self.assertEqual(self.gate()[0],self.binding)
    def test_old_or_uninstalled_receipt_rejected(self):
        self.receipt['status']='PLANNED'
        with self.assertRaisesRegex(ValueError,'RECEIPT'):self.gate()
    def test_only_four_reviewed_targets(self):
        self.manifest['entries'][0]['path']='emf/mods/aic_first_spawn/attempt.lock'
        with self.assertRaisesRegex(ValueError,'FOUR_FILE'):self.gate()
    def test_changed_preserved_file_rejected(self):
        (self.game/'old/1').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'INSTALLED_FILE'):self.gate()
    def test_missing_effective_hash_rejected(self):
        self.manifest['effective_files'].pop()
        with self.assertRaisesRegex(ValueError,'23_REQUIRED'):self.gate()
    def test_stale_backup_rejected(self):
        self.bm['files'][0]['sha256']='outdated'
        with self.assertRaisesRegex(ValueError,'BACKUP_BASELINE'):self.gate()
    def test_wrong_before_hash_rejected(self):
        self.manifest['entries'][0]['before_sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'BASELINE_MISMATCH'):self.gate()
    def test_unchanged_file_cannot_be_silently_updated(self):
        self.manifest['effective_files'][-1]['sha256']='new'
        with self.assertRaisesRegex(ValueError,'EFFECTIVE_HASH'):self.gate()
    def test_spent_latch_rejected(self):
        (self.game/'emf/mods/aic_first_spawn/attempt.lock').write_bytes(('SPENT!:'+'a'*32).encode())
        with self.assertRaisesRegex(ValueError,'INSTALLED_FILE'):self.gate()

if __name__=='__main__':unittest.main()
