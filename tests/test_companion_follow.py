import json
from pathlib import Path
import tempfile
import unittest
import shutil
import hashlib

from lupa.lua54 import LuaRuntime
from companion.follow import run, summarize, FollowClient

ROOT=Path(__file__).resolve().parents[1]
FIXTURE='''
now=100;px=10;nx=0;session='abc-1';entity=42;unique=true;valid=true;calls=0;cancelled=0;consumed=0
active=nil;ground_calls=0;path_calls=0;py=0;ny=0
w={}
function discover(w)
 assert(valid,'CONTEXT')
 return {result=unique and 'FOUND_ONE' or 'AMBIGUOUS',session=session,player=1,entity=entity,
 position={x=nx,y=ny,z=0},home={x=0,y=0,z=0},ai_state=3,decision=busy and 5 or 1}
end
api={now=function() return now end,log=function() end,
 position=function(w,id) return {x=px,y=py,z=0} end,
 moving=function() return active end,
 consume=function() consumed=consumed+1;return consumed==1 end,
 cancel=function(id) cancelled=cancelled+1;if cancel_fail then return false end;active=nil;return true end,
 wall=function() return wall end,
 ground=function(w,x,z,fn) ground_calls=ground_calls+1;gx=x;gz=z;ground_cb=fn;return not ground_refused end,
 path=function(w,a,b,opts,fn) path_calls=path_calls+1;path_options=opts;target=b;path_cb=fn;return not path_refused end,
 move=function(w,id,t,opts,fn)
  calls=calls+1;options=opts;move_cb=fn;move_target=t
  if uncertain then error('UNCERTAIN') end
  if refuse then return nil,'outside home' end
  active=calls;return active
 end}
config={token='token',roaming='native'}
seq=0
function step() seq=seq+1;c.step(w,'token',seq) end
function ground() ground_cb(w,true,gx,py,gz,nil,nil,'none',nil) end
function path() path_cb(w,{status='found',reaches=true,count=1,length=8},{{x=target.x,y=target.y,z=target.z,move=0}}) end
function prepare() step();ground();path();now=now+1;step() end
'''


class FollowLuaTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.globals().policy=self.lua.execute((ROOT/'mods/aic_companion_movement/follow.lua').read_text(encoding='utf-8'))
        self.lua.execute("c=policy.new(api,discover,config);c.start(w,'token','abc-1',42)")
    def do(self,s): self.lua.execute(s)
    def val(self,s): return self.lua.eval(s)
    def test_far_no_move_no_probe(self):
        self.do('px=51;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.assertEqual(self.val('ground_calls'),0)
    def test_boundary_hysteresis(self):
        self.do('px=30;step()')
        self.assertEqual(self.val('ground_calls'),0)
        self.do('px=20;now=101;step()')
        self.assertEqual(self.val('ground_calls'),1)
    def test_offset_ground_path_then_single_move(self):
        self.do('prepare()')
        self.assertAlmostEqual(self.val('move_target.x'),8.2)
        self.assertEqual(self.val('calls'),1)
        self.do('now=102;step()')
        self.assertEqual(self.val('calls'),1)
    def test_close_no_probe(self):
        self.do('px=1.8;step()')
        self.assertEqual(self.val('c.state'),'IDLE_NEAR_PLAYER')
        self.assertEqual(self.val('ground_calls'),0)
        self.do('px=2.5;now=101;step()')
        self.assertEqual(self.val('ground_calls'),0)
    def test_far_cancels_only_owned(self):
        self.do('prepare();px=51;now=102;step()')
        self.assertEqual(self.val('cancelled'),1)
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
    def test_foreign_order(self):
        self.do('active=99')
        with self.assertRaises(Exception): self.do('step()')
        self.assertEqual(self.val('calls'),0)
    def test_near_cancels_move(self):
        self.do('prepare();nx=8.3;now=102;step()')
        self.assertEqual(self.val('c.state'),'IDLE_NEAR_PLAYER')
        self.assertEqual(self.val('cancelled'),1)
    def test_reenter_radius(self):
        self.do('px=51;step();px=18;now=101;step()')
        self.assertEqual(self.val('ground_calls'),1)
    def test_player_motion_does_not_invalidate_destination(self):
        self.do('step();px=13;ground()')
        self.assertEqual(self.val('path_calls'),1)
        self.assertEqual(self.val('calls'),0)
    def test_stale_ready_no_move(self):
        self.do('step();ground();path();busy=true;now=103;step();busy=false;now=105;step()')
        self.assertEqual(self.val('calls'),0)
        self.assertEqual(self.val('c.reason'),'STALE_PATH')
    def test_ground_fog_water_failure_try_alternative(self):
        for args in ("true,gx,0,gz,nil,nil,'deadly',nil", "true,gx,0,gz,nil,nil,'none',1", "false,gx,0,gz,nil,nil,'none',nil"):
            self.setUp();self.do('step();ground_cb(w,'+args+')')
            self.assertEqual(self.val('c.state'),'RECOVERING')
            self.assertEqual(self.val('calls'),0)
    def test_direct_wall_still_uses_native_path(self):
        self.do('step();wall=true;ground()')
        self.assertEqual(self.val('path_calls'),1)
    def test_path_not_reaching(self):
        self.do("step();ground();path_cb(w,{status='found',reaches=false,count=0,length=1},{})")
        self.assertEqual(self.val('c.reason'),'PATH_REFUSED')
    def test_watchdog_cancels_owned(self):
        self.do('prepare();now=107;c.watch(w)')
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('cancelled'),1)
    def test_world_loss_never_cancel_reused_identity(self):
        self.do("prepare();session='abc-2';c.watch(w)")
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('cancelled'),0)
    def test_duplicate_stops_watchdog(self):
        self.do('prepare();unique=false;c.watch(w)')
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('cancelled'),0)
    def test_unknown_move_no_retry(self):
        self.do('uncertain=true;step();ground();path();now=101')
        with self.assertRaises(Exception): self.do('step()')
        self.do("c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('cancelled'),0)
    def test_explicit_refusal_tries_another_candidate(self):
        self.do('refuse=true;prepare()')
        self.assertEqual(self.val('c.state'),'RECOVERING')
    def test_stuck_not_arrived_limited_recovery(self):
        self.do("prepare();active=nil;move_cb(w,1,'stuck');now=102;step()")
        self.assertEqual(self.val('c.state'),'STUCK')
        self.assertEqual(self.val('c.recoveries'),1)
        self.assertEqual(self.val('calls'),1)
        self.do('c.recoveries=2;now=106;step();ground();path();now=107;step()')
        self.do("active=nil;move_cb(w,2,'stuck');now=108;step()")
        self.assertEqual(self.val('c.reason'),'RECOVERY_LIMIT')
    def test_cancel_failure_stops_without_retry(self):
        self.do('prepare();cancel_fail=true;px=51;now=102')
        with self.assertRaises(Exception): self.do('step()')
        self.do("c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('calls'),1)
    def test_sequence_and_rearm_rejected(self):
        with self.assertRaises(Exception): self.do("c.step(w,'token',5)")
        with self.assertRaises(Exception): self.do("c.start(w,'token','abc-1',42)")
        self.assertEqual(self.val('consumed'),1)
    def test_expiry_and_late_callback(self):
        self.do('step();now=281;c.watch(w);ground()')
        self.assertEqual(self.val('path_calls'),0)
        self.assertEqual(self.val('c.state'),'STOPPED')
    def test_hold_is_finite_and_reversible(self):
        self.do("config.roaming='hold';prepare();nx=8.2;move_cb(w,1,'arrived');now=102;step()")
        self.assertEqual(self.val('options.hold'),5)
        self.assertEqual(self.val('c.state'),'IDLE_NEAR_PLAYER')
        self.do("c.stop(w,'END')")
        self.assertEqual(self.val('cancelled'),1)
    def test_short_engine_arrival_not_success(self):
        self.do("prepare();active=nil;move_cb(w,1,'arrived');now=102;step()")
        self.assertEqual(self.val('c.reason'),'ENGINE_ARRIVED_SHORT')
    def test_order_budget(self):
        self.do('c.orders=24;prepare()')
        self.assertEqual(self.val('calls'),0)
        self.assertEqual(self.val('c.reason'),'ORDER_LIMIT')
    def test_invalidated_probe_cannot_accumulate_requests(self):
        self.do('step();px=51;now=101;step();px=10;now=102;step()')
        self.assertEqual(self.val('ground_calls'),1)
        self.do('ground();now=103;step()')
        self.assertEqual(self.val('ground_calls'),2)
        self.assertEqual(self.val('path_calls'),0)
    def test_probe_budget(self):
        self.do('c.probes=30;step()')
        self.assertEqual(self.val('c.reason'),'PROBE_LIMIT')
    def test_duplicate_callback_no_extra_path(self):
        self.do('step();ground();ground()')
        self.assertEqual(self.val('path_calls'),1)
    def test_cancel_is_not_retried_on_exception(self):
        self.do('prepare();cancel_fail=true;px=51;now=102')
        with self.assertRaises(Exception): self.do('step()')
        self.do("c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('cancelled'),1)

    def test_vertical_twenty_metres_both_directions(self):
        for height in (-20,20):
            self.setUp();self.do(f'py={height};prepare()')
            self.assertEqual(self.val('calls'),1)
            self.assertEqual(self.val('move_target.y'),height)
    def test_same_xz_different_floor_not_idle(self):
        self.do('px=0;py=20;prepare()')
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('c.state'),'MOVING')
    def test_jump_down_route_native_execution_no_height_limit(self):
        self.do("py=-20;step();ground();path_cb(w,{status='found',reaches=true,count=1,length=40},{{x=target.x,y=target.y,z=target.z,move=3}});now=101;step()")
        self.assertEqual(self.val('calls'),1)
        self.assertTrue(self.val('path_options.jumps'))
        self.assertEqual(self.val('path_options.max_jump_down'),0)
    def test_failed_route_rotates_then_success(self):
        self.do("step();firstx=gx;firstz=gz;ground();path_cb(w,{status='no_path'},{});now=104;step()")
        self.assertNotEqual(self.val('gz'),self.val('firstz'))
        self.do('ground();path();now=105;step()')
        self.assertEqual(self.val('calls'),1)
    def test_walking_player_and_npc_do_not_starve_probe(self):
        self.do('step();px=13;nx=1;ground();px=15;nx=5;path();now=101;step()')
        self.assertEqual(self.val('calls'),1)
    def test_small_player_motion_does_not_cancel_route(self):
        self.do('prepare();px=14;now=104;step()')
        self.assertEqual(self.val('cancelled'),0)
    def test_stop_reason_survives_step_and_second_stop(self):
        self.do("c.stop(w,'GROUND_REFUSED');step();c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('c.reason'),'GROUND_REFUSED')
    def test_long_detour_accepted(self):
        self.do("step();wall=true;ground();path_cb(w,{status='found',reaches=true,count=1,length=100},{{x=target.x,y=0,z=target.z,move=0}});now=101;step()")
        self.assertEqual(self.val('calls'),1)

    def test_busy_waits_then_resumes(self):
        self.do('busy=true;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_NPC')
        self.do('busy=false;now=101;prepare()')
        self.assertEqual(self.val('calls'),1)
    def test_all_candidates_fail_without_unbounded_queue(self):
        self.do("for i=1,30 do step();ground_cb(w,false,gx,0,gz,'no ground',nil,'none',nil);now=now+4 end;step()")
        self.assertEqual(self.val('ground_calls'),30)
        self.assertEqual(self.val('calls'),0)
        self.assertEqual(self.val('c.reason'),'PROBE_LIMIT')

    def test_twenty_fifty_hysteresis_complete_cycle(self):
        self.do('px=30;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.do('px=20;now=101;prepare()')
        self.assertEqual(self.val('calls'),1)
        for distance in (35,49,50):
            self.do(f'px={distance};now=now+1;step()')
            self.assertNotEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.do('px=50.01;now=now+1;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.assertEqual(self.val('cancelled'),1)
        self.do('px=35;now=now+1;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.do('px=20;now=now+1;step()')
        self.assertNotEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
    def test_retarget_current_player_single_order(self):
        self.do('prepare();px=25')
        for t in range(102,110):self.do(f'now={t};step()')
        self.assertEqual(self.val('cancelled'),1)
        self.assertEqual(self.val('calls'),1)
        for t in range(110,114):self.do(f'now={t};step()')
        self.do('ground();path();now=114;step()')
        self.assertEqual(self.val('calls'),2)
        self.assertAlmostEqual(self.val('move_target.x'),23.2)
    def test_thresholds_ignore_vertical_separation(self):
        for height in (-20,-10,10,20):
            self.setUp();self.do(f'py={height};px=20;prepare()')
            self.assertEqual(self.val('calls'),1)
            self.do('px=35;now=102;step()')
            self.assertNotEqual(self.val('c.state'),'WAITING_FOR_PLAYER')


class FakeClient:
    def __init__(self): self.calls=[];self.fail=False
    def context(self): return {}
    def discover(self): return {'discovery':{'result':'FOUND_ONE','session':'abc-1','entity':42}}
    def _request(self,name,*args):
        self.calls.append(name)
        if self.fail and name=='f_step': raise ValueError('UNKNOWN')
        return dict(state='STOPPED' if name=='f_step' else 'WAITING_FOR_PLAYER',reason='END',orders=0)


class RunnerTests(unittest.TestCase):
    def test_durable_single_session(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'session.jsonl';client=FakeClient()
            r=run(client,path,'token',sleep=lambda _:None)
            self.assertEqual(r['samples'],2)
            before=list(client.calls)
            with self.assertRaises(FileExistsError):run(client,path,'token')
            self.assertEqual(client.calls,before)
            rows=[json.loads(s) for s in path.read_text().splitlines()]
            self.assertEqual(rows[0]['kind'],'SESSION_INTENT')
            self.assertIn('STEP_GRANT',[r['kind'] for r in rows])
    def test_unknown_never_retries_or_sends_cleanup_rpc(self):
        with tempfile.TemporaryDirectory() as td:
            client=FakeClient();client.fail=True
            with self.assertRaises(ValueError):run(client,Path(td)/'s','token',sleep=lambda _:None)
            self.assertEqual(client.calls,['f_start','f_step'])
    def test_stuck_not_success(self):
        r=summarize([dict(state='STUCK',distance=1.8,orders=1)])
        self.assertFalse(r['arrival_observed'])
        self.assertFalse(r['roaming_disabled'])
    def test_no_manual_move_endpoint(self):
        with self.assertRaises(ValueError):FollowClient(None).move_to(1,2,3)
    def test_audited_append_preserves_history_and_is_single_use(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'session.jsonl';prior=b'{"kind":"PREVIOUS_REFUSED"}\n';path.write_bytes(prior)
            proof=dict(prior_journal_sha256=hashlib.sha256(prior).hexdigest())
            client=FakeClient()
            run(client,path,'token',sleep=lambda _:None,continuation=proof)
            self.assertTrue(path.read_bytes().startswith(prior))
            self.assertEqual(json.loads(path.read_text().splitlines()[1])['kind'],'AUDITED_CONTINUATION')
            calls=list(client.calls)
            with self.assertRaisesRegex(ValueError,'ALREADY_USED'):
                run(client,path,'token',sleep=lambda _:None,continuation=proof)
            self.assertEqual(client.calls,calls)
    def test_changed_prior_journal_refuses_without_rpc(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'session.jsonl';path.write_bytes(b'changed\n');client=FakeClient()
            with self.assertRaises(ValueError):
                run(client,path,'token',continuation=dict(prior_journal_sha256='0'*64))
            self.assertEqual(path.read_bytes(),b'changed\n');self.assertEqual(client.calls,[])
    def test_follow_version_and_local_context(self):
        from tests.test_companion_movement import Transport
        t=Transport();client=FollowClient(t)
        with self.assertRaises(ValueError):client.discover()
        t.mods[-1]['version']='0.3.0'
        client.discover()
        old=t.state
        t.state=lambda:dict(old(),character=dict(storage='steam',slot=1,name='Body Test'))
        count=len(t.calls)
        with self.assertRaises(ValueError):client._request('f_step','token',1)
        self.assertEqual(len(t.calls),count)


class HostFollowTests(unittest.TestCase):
    def test_real_host_latch_reload_and_reply_size(self):
        from tests.test_companion_movement import FIXTURE as WORLD
        with tempfile.TemporaryDirectory() as td:
            for p in (ROOT/'mods/aic_companion_movement').glob('*.lua'):
                shutil.copyfile(p,Path(td)/p.name)
            token='a1c10140000000000000000000000001'
            lock=Path(td)/'follow-stage10-14.lock'
            lock.write_text('UNUSED:'+token,encoding='ascii')
            old_lock=Path(td)/'follow-session.lock';old_lock.write_bytes(b'SPENT!:previous')
            lua=LuaRuntime(unpack_returned_tuples=True)
            def encode(v):
                def plain(x): return {k:plain(y) for k,y in x.items()} if hasattr(x,'items') else x
                return json.dumps(plain(v),separators=(',',':'))
            lua.globals().encode=encode;lua.globals().moddir=td
            lua.execute(WORLD)
            lua.execute('''
commands={};replies={};now=100;os.time=function() return now end
function w:is_server() return true end
function w:character_name() return 'Body Test' end
local oldget=w.get;function w:get(n,id) if n=='PlayerState' and id==1 then return {} end;return oldget(self,n,id) end
local oldtemplate=w.template;function w:template(n,id) if id==1 then return nil end;return oldtemplate(self,n,id) end
function w:position(id) return id==1 and 10 or 0,0,0 end
ids={1,42}
emf={dir=moddir,local_player=api.player,session_token=api.session,villager_move=api.move,villager_moving=api.moving,
find_wall=function() return nil end,json={encode=encode},reply=function(s) replies[#replies+1]=s end,
command=function(n,d,f) if #('aic_companion_movement.'..n)>32 then return false end;commands[n]=f;return true end,on_tick=function(f) watch=f end,log=function() end,
ground_at=function(w,x,z,f) ground=f;return true end}
''')
            host=(ROOT/'mods/aic_companion_movement/main.lua').read_text(encoding='utf-8')
            lua.execute(host)
            actual={k for k,v in lua.globals().commands.items()}
            self.assertEqual(actual,{'discover','status','move_to','f_start','f_step','f_stop','f_status'})
            self.assertEqual(set(FollowClient.commands)-{'discover'},actual-{'discover','status','move_to'})
            for name in actual:self.assertLessEqual(len('aic_companion_movement.'+name),32)
            self.assertFalse(lua.eval("emf.command('follow_start','',function() end)"))
            with self.assertRaises(Exception):
                lua.execute(host.replace("'f_start'","'follow_start'"))
            lua.execute(host)
            lua.execute("commands.f_start(w,{string.rep('a',32),'"+token+"','abc-1','42'})")
            self.assertEqual(lock.read_text(),'SPENT!:'+token)
            reply=lua.eval('replies[1]')
            self.assertLess(len(reply.encode()),964)
            self.assertTrue(json.loads(reply[13:])['ok'])
            lua.execute("commands.f_step(w,{string.rep('b',32),'"+token+"','1'})")
            self.assertTrue(json.loads(lua.eval('replies[2]')[13:])['ok'])
            lua.execute(host)  # real Lua reload, with the same durable lock
            lua.execute("commands.f_start(w,{string.rep('c',32),'"+token+"','abc-1','42'})")
            self.assertIn('DURABLE_SESSION_LATCH',lua.eval('replies[3]'))
            self.assertEqual(lua.eval('calls'),0)
            self.assertEqual(old_lock.read_bytes(),b'SPENT!:previous')


if __name__=='__main__': unittest.main()
