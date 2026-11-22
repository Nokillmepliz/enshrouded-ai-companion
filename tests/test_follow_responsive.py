"""Targeted regression for Movement 0.3.5; no engine/game writes."""
import unittest
from pathlib import Path
from lupa.lua54 import LuaRuntime
from tests import test_follow_lifecycle as lifecycle
from tests.test_companion_movement import FIXTURE

ROOT=Path(__file__).resolve().parents[1]


class ResponsiveTests(unittest.TestCase):
    def setUp(self):
        self.f=lifecycle.LifecycleTests();self.f.start_controller=False;self.f.setUp()
        self.f.do('config.responsive=true;c=follow.new(api,discover,config)')
        self.f.do('c.start(w,"token","abc-1",42)')

    def test_retarget_two_seconds_and_fresh_tick_only(self):
        f=self.f
        f.do('prepare();px=14;now=102;request()')
        self.assertEqual(f.val('cancelled'),0)
        f.do('now=103;request()')
        self.assertEqual(f.val('cancelled'),0)
        f.do('tick()')
        self.assertEqual(f.val('cancelled'),1)
        self.assertEqual(f.val('calls'),1)
        self.assertEqual(f.val('invalid_reads'),0)
        f.do('tick();now=104;request();ground();path();now=105;request()')
        self.assertEqual(f.val('calls'),2)
        self.assertEqual(f.val('invalid_reads'),0)

    def test_small_motion_keeps_order_and_pending_cancel_never_overlaps(self):
        f=self.f;f.do('prepare();px=13;now=103;request();tick()')
        self.assertEqual(f.val('cancelled'),0)
        f.do('cancel_pending=true;px=14;now=104;request();tick();now=105;request();tick()')
        self.assertEqual(f.val('calls'),1)
        self.assertEqual(f.val('cancelled'),1)

    def test_anchor_uses_query_player_not_dispatch_player(self):
        f=self.f;f.do('request();px=14;ground();path();now=101;request();now=103;request();tick()')
        self.assertEqual(f.val('cancelled'),1)

    def test_refusal_backoff_and_budget_unchanged(self):
        f=self.f;f.do('refuse=true;prepare();request()')
        self.assertEqual(f.val('ground_calls'),1)
        f.do('now=102;request()')
        self.assertEqual(f.val('ground_calls'),1)
        f.do('now=105;request()')
        self.assertEqual(f.val('ground_calls'),2)
        f.do('ground();path();c.orders=24;now=106;request();tick()')
        self.assertEqual(f.val('calls'),1)
        self.assertEqual(f.val('c.reason'),'ORDER_LIMIT')
        self.assertEqual(f.val('common.sleepTime'),22)

    def test_hysteresis_and_vertical_proximity_unchanged(self):
        f=self.f;f.do('px=30;request();px=20;py=20;request();ground();path();now=101;request()')
        self.assertEqual(f.val('calls'),1)
        for x in (35,49,50):
            f.do(f'px={x};request()')
            self.assertNotEqual(f.val('c.state'),'WAITING_FOR_PLAYER')
        f.do('px=51;request();tick();tick();px=35;now=102;request()')
        self.assertEqual(f.val('c.state'),'WAITING_FOR_PLAYER')
        f.do('px=20;request()')
        self.assertNotEqual(f.val('c.state'),'WAITING_FOR_PLAYER')

    def test_finite_native_hold_is_released_when_player_moves(self):
        f=self.f;f.do("config.roaming='hold';prepare();nx=8.2;move_cb(w,1,'arrived');now=102;request()")
        self.assertEqual(f.val('options.hold'),5)
        self.assertEqual(f.val('c.state'),'IDLE_NEAR_PLAYER')
        self.assertEqual(f.val('cancelled'),0)
        f.do('px=11.5;now=103;request();tick();tick()')
        self.assertEqual(f.val('cancelled'),1)
        self.assertEqual(f.val('invalid_reads'),0)
        f.do("c.stop(w,'END');tick()")
        self.assertEqual(f.val('common.sleepTime'),22)


class NavigationInfoTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True);self.lua.execute(FIXTURE)
        self.lua.execute('''
function readonly(t)
 local p={};return setmetatable(p,{__index=function(_,k)
  local v=t[k];return type(v)=='table' and readonly(v) or v end,
  __newindex=function() error('WRITE_FORBIDDEN') end})
end
saved={spawnPosition={x=1,y=2,z=3},overrideRoamingRange=false,roamingRange=0}
template={npcId=2939921867,roamingSetup={maxRadiusFromSpawn=10},searchTargetSetup={targetRadius=8,bedRadius=50}}
function w:template() return readonly(template) end
local old=w.get;function w:get(n,id) if n=='ActiveNpcStateSaved' then return readonly(saved) end;return old(self,n,id) end
''')
        self.lua.globals().p=self.lua.execute((ROOT/'mods/aic_companion_movement/controller.lua').read_text())
        self.lua.execute('c=p.new(api)')

    def test_source_and_saved_override_are_distinguished_without_writes(self):
        d=self.lua.eval('c.navigation(w).navigation')
        self.assertEqual(d['effective_radius'],10);self.assertEqual(d['leash'],50)
        self.lua.execute('saved.overrideRoamingRange=true;saved.roamingRange=30')
        self.assertEqual(self.lua.eval('c.navigation(w).navigation.effective_radius'),30)
        self.lua.execute('saved.roamingRange=0')
        self.assertEqual(self.lua.eval('c.navigation(w).navigation.effective_radius'),0)
        self.assertEqual(self.lua.eval('calls'),0)

    def test_ambiguous_and_missing_fields_fail_closed(self):
        self.lua.execute('ids={42,43}')
        with self.assertRaisesRegex(Exception,'NO_UNIQUE_NPC'):self.lua.execute('c.navigation(w)')
        self.lua.execute('ids={42};saved.overrideRoamingRange=nil')
        with self.assertRaisesRegex(Exception,'NAV_FIELDS_UNCONFIRMED'):self.lua.execute('c.navigation(w)')

if __name__=='__main__':unittest.main()
