"""Regression: a synchronous native cancel invalidates the invoking Lua world."""
import json
from pathlib import Path
import tempfile
import unittest
from lupa.lua54 import LuaRuntime
from tests.test_companion_follow import FIXTURE, FakeClient
from companion.follow import run

ROOT=Path(__file__).resolve().parents[1]


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.execute('''
generation=0;invalid_reads=0;writes=0;logs={};saved={};common={sleepTime=22,wakeUpTime=6}
local function check(w)
 if w.g~=generation then invalid_reads=invalid_reads+1;error('INVALID_WORLD') end
end
function fresh_world()
 generation=generation+1
 w={g=generation,get=function(self,n,id) check(self);assert(n=='NpcCommon' and id==42);return common end}
end
local old=discover;discover=function(w) check(w);return old(w) end
local pos=api.position;api.position=function(w,id) check(w);return pos(w,id) end
api.moving=function(w) check(w);return active end
api.log=function(event,data) logs[#logs+1]=event end
api.cancel=function(id)
 cancelled=cancelled+1
 if not cancel_pending then active=nil;move_cb(w,id,'cancelled') end
 generation=generation+1 -- EMF move_cb_body increments generation after nested callback.
 if cancel_throw then error('NATIVE_FAILURE_AFTER_CALLBACK') end
 return true
end
local move=api.move;api.move=function(w,...) check(w);assert(not active,'OVERLAPPING_ORDER');return move(w,...) end
function tick() fresh_world();c.watch(w) end
function request() fresh_world();seq=seq+1;c.step(w,'token',seq);return c.status(w) end
function step() request() end
fresh_world()
sa={now=api.now,time=function() return 23 end,load=function() end,
 save=function(r) assert(not disk_fail,'DISK_FAIL');saved[#saved+1]=r end,log=api.log}
''')
        self.lua.globals().schedule=self.lua.execute((ROOT/'mods/aic_companion_movement/schedule.lua').read_text())
        self.lua.globals().follow=self.lua.execute((ROOT/'mods/aic_companion_movement/follow.lua').read_text())
        self.do("api.schedule=schedule.new(sa);c=follow.new(api,discover,config)")
        if getattr(self,'start_controller',True):
            self.do("c.start(w,'token','abc-1',42)")

    def do(self,s):return self.lua.execute(s)
    def val(self,s):return self.lua.eval(s)

    def test_cancel_invalidates_world_but_next_tick_continues(self):
        self.do('prepare();px=25;now=105;request();now=109;request()')
        self.assertEqual(self.val('cancelled'),0)  # Command response still uses a valid world.
        self.do('tick()')
        self.assertEqual(self.val('cancelled'),1)
        self.assertEqual(self.val('invalid_reads'),0)
        self.do('tick();now=110;request();now=113;request();ground();path();now=114;request()')
        self.assertEqual(self.val('calls'),2)
        self.assertEqual(self.val('invalid_reads'),0)
        self.assertNotEqual(self.val('c.state'),'STOPPED')

    def test_request_error_stops_then_fresh_ticks_restore_without_reload(self):
        self.do("prepare();generation=generation+1;c.stop(w,'REQUEST_ERROR')")
        self.assertEqual(self.val('common.sleepTime'),25)
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.do('tick()')  # cancels, invalidates world; restoration must wait.
        self.assertEqual(self.val('common.sleepTime'),25)
        self.do('tick()')
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertEqual(self.val('common.wakeUpTime'),6)
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('saved[2].state'),'RELEASED')
        self.assertEqual(self.val('invalid_reads'),0)
        self.do('tick();request()')
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('consumed'),1)
        with self.assertRaises(Exception):self.do("c.start(w,'token','abc-1',42)")

    def test_native_cancel_exception_never_reads_invalid_world(self):
        self.do("prepare();cancel_throw=true;px=51;now=102;request();tick();tick()")
        self.assertEqual(self.val('invalid_reads'),0)
        self.assertEqual(self.val('cancelled'),1)
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('common.sleepTime'),22)

    def test_move_exception_stops_and_releases_without_another_order(self):
        self.do('uncertain=true;request();ground();path();now=101')
        with self.assertRaisesRegex(Exception,'UNCERTAIN'):self.do('request()')
        self.do("c.stop(w,'REQUEST_ERROR');tick();request();tick()")
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('cancelled'),0)
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('common.sleepTime'),22)

    def test_pending_cancel_blocks_second_order_and_times_out_without_retry(self):
        self.do('prepare();cancel_pending=true;px=51;now=102;request();tick();px=10;now=103;request();tick()')
        self.assertEqual(self.val('calls'),1)
        self.do('now=107;request();tick();tick()')
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('cancelled'),1)
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('common.sleepTime'),22)

    def test_identity_loss_blocks_cleanup_until_original_identity_returns(self):
        self.do("c.stop(w,'REQUEST_ERROR');session='other-1';tick()")
        self.assertEqual(self.val('common.sleepTime'),25)
        self.assertEqual(self.val('c.cleanup'),'PENDING')
        self.do("session='abc-1';now=101;tick()")
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertEqual(self.val('calls'),0)

    def test_release_disk_failure_retains_lease_and_retries_no_movement(self):
        self.do("disk_fail=true;c.stop(w,'REQUEST_ERROR');tick()")
        self.assertEqual(self.val('c.cleanup'),'PENDING')
        self.assertIsNotNone(self.val('api.schedule.lease'))
        self.do('disk_fail=false;now=101;tick();tick()')
        self.assertEqual(self.val('saved[2].state'),'RELEASED')
        self.assertEqual(self.val('#saved'),2)
        self.assertEqual(self.val('calls'),0)

    def test_foreign_order_is_not_cancelled_and_does_not_block_schedule_cleanup(self):
        self.do("prepare();c.stop(w,'REQUEST_ERROR');active=99;tick()")
        self.assertEqual(self.val('active'),99)
        self.assertEqual(self.val('cancelled'),0)
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertEqual(self.val('c.cleanup'),'DONE')


class CleanupRunnerTests(unittest.TestCase):
    def test_error_only_reads_cleanup_and_never_retries_mutation(self):
        class Client(FakeClient):
            version='0.3.2'
            def _request(self,name,*args):
                if name=='f_status':
                    self.calls.append(name)
                    return dict(state='STOPPED',cleanup='DONE')
                return super()._request(name,*args)
        with tempfile.TemporaryDirectory() as td:
            c=Client();c.fail=True;p=Path(td)/'journal'
            with self.assertRaises(ValueError):run(c,p,'token',sleep=lambda _:None)
            self.assertEqual(c.calls,['f_start','f_step','f_status'])
            self.assertIn('CLEANUP_OBSERVATION',[json.loads(x)['kind'] for x in p.read_text().splitlines()])

    def test_cleanup_timeout_is_unconfirmed_not_success(self):
        class Client(FakeClient):
            version='0.3.2'
            def _request(self,name,*args):
                if name=='f_status':
                    self.calls.append(name)
                    return dict(state='STOPPED',cleanup='PENDING')
                return super()._request(name,*args)
        with tempfile.TemporaryDirectory() as td:
            c=Client();p=Path(td)/'journal';now=[0]
            def sleep(t):now[0]+=t
            result=run(c,p,'token',clock=lambda:now[0],sleep=sleep)
            self.assertEqual(result['schedule_cleanup'],'UNCONFIRMED')
            self.assertLessEqual(c.calls.count('f_status'),16)
            self.assertEqual(c.calls.count('f_start'),1)
            self.assertEqual(c.calls.count('f_step'),1)
            self.assertNotIn('f_stop',c.calls)


if __name__=='__main__':unittest.main()
