import json
from pathlib import Path
import tempfile
import unittest
import shutil

from lupa.lua54 import LuaRuntime
from companion.follow import run, summarize, FollowClient

ROOT=Path(__file__).resolve().parents[1]
FIXTURE='''
now=100;px=10;nx=0;session='abc-1';entity=42;unique=true;valid=true;calls=0;cancelled=0;consumed=0
active=nil;ground_calls=0;path_calls=0
w={}
function discover(w)
 assert(valid,'CONTEXT')
 return {result=unique and 'FOUND_ONE' or 'AMBIGUOUS',session=session,player=1,entity=entity,
 position={x=nx,y=0,z=0},home={x=0,y=0,z=0},ai_state=3,decision=1}
end
api={now=function() return now end,log=function() end,
 position=function(w,id) return {x=px,y=0,z=0} end,
 moving=function() return active end,
 consume=function() consumed=consumed+1;return consumed==1 end,
 cancel=function(id) cancelled=cancelled+1;if cancel_fail then return false end;active=nil;return true end,
 wall=function() return wall end,
 ground=function(w,x,z,fn) ground_calls=ground_calls+1;gx=x;gz=z;ground_cb=fn;return not ground_refused end,
 path=function(w,a,b,opts,fn) path_calls=path_calls+1;target=b;path_cb=fn;return not path_refused end,
 move=function(w,id,t,opts,fn)
  calls=calls+1;options=opts;move_cb=fn;move_target=t
  if uncertain then error('UNCERTAIN') end
  if refuse then return nil,'outside home' end
  active=calls;return active
 end}
config={token='token',roaming='native'}
seq=0
function step() seq=seq+1;c.step(w,'token',seq) end
function ground() ground_cb(w,true,gx,0,gz,nil,nil,'none',nil) end
function path() path_cb(w,{status='found',reaches=true,count=1,length=8},{{x=target.x,y=0,z=target.z,move=0}}) end
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
        self.do('px=21;step()')
        self.assertEqual(self.val('c.state'),'WAITING_FOR_PLAYER')
        self.assertEqual(self.val('ground_calls'),0)
    def test_boundary_hysteresis(self):
        self.do('px=20;step()')
        self.assertEqual(self.val('ground_calls'),0)
        self.do('px=19;now=101;step()')
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
        self.do('prepare();px=21;now=102;step()')
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
        self.do('px=21;step();px=18;now=101;step()')
        self.assertEqual(self.val('ground_calls'),1)
    def test_target_motion_invalidates_probe(self):
        self.do('step();px=13;ground()')
        self.assertEqual(self.val('path_calls'),0)
        self.assertEqual(self.val('calls'),0)
    def test_stale_ready_no_move(self):
        self.do('step();ground();path();now=103;step()')
        self.assertEqual(self.val('calls'),0)
    def test_ground_fog_water_height_rejected(self):
        for args in ("true,gx,0,gz,nil,nil,'deadly',nil", "true,gx,0,gz,nil,nil,'none',1", "true,gx,2,gz,nil,nil,'none',nil", "false,gx,0,gz,nil,nil,'none',nil"):
            self.setUp();self.do('step();ground_cb(w,'+args+')')
            self.assertEqual(self.val('c.state'),'STOPPED')
            self.assertEqual(self.val('calls'),0)
    def test_wall_rejected(self):
        self.do('step();wall=true;ground()')
        self.assertEqual(self.val('c.reason'),'WALL_REFUSED')
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
    def test_refused_is_terminal(self):
        self.do('refuse=true;prepare()')
        self.assertEqual(self.val('c.state'),'STOPPED')
    def test_stuck_not_arrived_limited_recovery(self):
        self.do("prepare();active=nil;move_cb(w,1,'stuck');now=102;step()")
        self.assertEqual(self.val('c.state'),'STUCK')
        self.assertEqual(self.val('c.recoveries'),1)
        self.assertEqual(self.val('calls'),1)
        self.do('c.recoveries=2;now=106;step();ground();path();now=107;step()')
        self.do("active=nil;move_cb(w,2,'stuck');now=108;step()")
        self.assertEqual(self.val('c.reason'),'RECOVERY_LIMIT')
    def test_cancel_failure_stops_without_retry(self):
        self.do('prepare();cancel_fail=true;px=21;now=102')
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
        self.do('step();px=21;now=101;step();px=10;now=102;step()')
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
        self.do('prepare();cancel_fail=true;px=21;now=102')
        with self.assertRaises(Exception): self.do('step()')
        self.do("c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('cancelled'),1)


class FakeClient:
    def __init__(self): self.calls=[];self.fail=False
    def context(self): return {}
    def discover(self): return {'discovery':{'result':'FOUND_ONE','session':'abc-1','entity':42}}
    def _request(self,name,*args):
        self.calls.append(name)
        if self.fail and name=='follow_step': raise ValueError('UNKNOWN')
        return dict(state='STOPPED' if name=='follow_step' else 'WAITING_FOR_PLAYER',reason='END',orders=0)


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
            self.assertEqual(client.calls,['follow_start','follow_step'])
    def test_stuck_not_success(self):
        r=summarize([dict(state='STUCK',distance=1.8,orders=1)])
        self.assertFalse(r['arrival_observed'])
        self.assertFalse(r['roaming_disabled'])
    def test_no_manual_move_endpoint(self):
        with self.assertRaises(ValueError):FollowClient(None).move_to(1,2,3)
    def test_follow_version_and_local_context(self):
        from tests.test_companion_movement import Transport
        t=Transport();client=FollowClient(t)
        with self.assertRaises(ValueError):client.discover()
        t.mods[-1]['version']='0.2.0'
        client.discover()
        old=t.state
        t.state=lambda:dict(old(),character=dict(storage='steam',slot=1,name='Body Test'))
        count=len(t.calls)
        with self.assertRaises(ValueError):client._request('follow_step','token',1)
        self.assertEqual(len(t.calls),count)


class HostFollowTests(unittest.TestCase):
    def test_real_host_latch_reload_and_reply_size(self):
        from tests.test_companion_movement import FIXTURE as WORLD
        with tempfile.TemporaryDirectory() as td:
            for p in (ROOT/'mods/aic_companion_movement').glob('*.lua'):
                shutil.copyfile(p,Path(td)/p.name)
            token='a1c10130000000000000000000000001'
            lock=Path(td)/'follow-session.lock'
            lock.write_text('UNUSED:'+token,encoding='ascii')
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
command=function(n,d,f) commands[n]=f end,on_tick=function(f) watch=f end,log=function() end,
ground_at=function(w,x,z,f) ground=f;return true end}
''')
            host=(ROOT/'mods/aic_companion_movement/main.lua').read_text(encoding='utf-8')
            lua.execute(host)
            lua.execute("commands.follow_start(w,{string.rep('a',32),'"+token+"','abc-1','42'})")
            self.assertEqual(lock.read_text(),'SPENT!:'+token)
            reply=lua.eval('replies[1]')
            self.assertLess(len(reply.encode()),964)
            self.assertTrue(json.loads(reply[13:])['ok'])
            lua.execute("commands.follow_step(w,{string.rep('b',32),'"+token+"','1'})")
            self.assertTrue(json.loads(lua.eval('replies[2]')[13:])['ok'])
            lua.execute(host)  # real Lua reload, with the same durable lock
            lua.execute("commands.follow_start(w,{string.rep('c',32),'"+token+"','abc-1','42'})")
            self.assertIn('DURABLE_SESSION_LATCH',lua.eval('replies[3]'))
            self.assertEqual(lua.eval('calls'),0)


if __name__=='__main__': unittest.main()
