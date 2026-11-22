"""Real Lua policy with simulated engine ticks; not proof of a game transition."""
from pathlib import Path
import unittest
from lupa.lua54 import LuaRuntime
from tests import test_follow_lifecycle as lifecycle

ROOT=Path(__file__).resolve().parents[1]


class WakeTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
now=100;generation=0;sent=0;invalid=0;active=nil;logs={}
common={sleepTime=25,wakeUpTime=-1,interactionStates=0,currentTargetPosition={x=1,y=2,z=3}}
ai={state=13,previousState=8,decision=5};walker={state=0}
d={result='FOUND_ONE',session='abc',entity=42,npc=2939921867,ai_state=13,decision=5,position={x=1,y=2,z=3}}
function world()
 generation=generation+1
 return {g=generation,get=function(self,n,id)
  if self.g~=generation then invalid=invalid+1;error('INVALID_WORLD') end
  assert(id==42);return ({NpcCommon=common,DynamicActiveNpcState=ai,DynamicPathWalker=walker})[n]
 end}
end
api={now=function() return now end,moving=function(w) assert(w.g==generation);return active end,
 log=function(e,v) logs[#logs+1]=e end,
 emit=function(n,p) assert(n==2939921867);sent=sent+1;generation=generation+1
  if fail_emit then error('UNCERTAIN_EMIT') end end}
''')
        self.lua.globals().module=self.lua.execute((ROOT/'mods/aic_companion_movement/wake.lua').read_text())
        self.do('s=module.new(api)')

    def do(self,s):return self.lua.execute(s)
    def val(self,s):return self.lua.eval(s)
    def queue(self):self.do('s.tick(world(),d);now=102;s.tick(world(),d)')

    def test_sticky_decision_requires_two_seconds_and_single_emit(self):
        self.do('s.tick(world(),d);now=101;s.tick(world(),d)')
        self.assertEqual(self.val('sent'),0)
        self.do('now=102;s.tick(world(),d);s.tick(world(),d)')
        self.assertEqual(self.val('sent'),1)
        self.assertTrue(self.val('s.pending'))
        self.assertEqual(self.val('invalid'),0)

    def test_fresh_tick_requires_terminal_arrival_not_just_decision(self):
        self.queue()
        self.do('ai.state=7;ai.decision=1;walker.state=2')
        self.assertTrue(self.do('return s.tick(world(),d)'))
        self.do('ai.state=3;ai.previousState=7;walker.state=8;d.decision=1')
        self.assertFalse(self.do('return s.tick(world(),d)'))
        self.assertEqual(self.val('s.state'),'CONFIRMED')
        self.do('d.decision=5;now=110;s.tick(world(),d)')
        self.assertEqual(self.val('sent'),1)

    def test_sleep_busy_or_normal_awake_sends_nothing(self):
        for state,decision in ((8,5),(2,5),(9,5),(16,5),(7,1)):
            self.setUp();self.do(f'd.ai_state={state};d.decision={decision}')
            self.queue();self.assertEqual(self.val('sent'),0)

    def test_foreign_order_and_missing_override_prevent_emit(self):
        for alteration in ('active=99','common.sleepTime=22',"d.npc=1"):
            self.setUp();self.do('s.tick(world(),d);now=102;'+alteration)
            with self.assertRaises(Exception):self.do('s.tick(world(),d)')
            self.assertEqual(self.val('sent'),0)

    def test_interaction_is_not_forced(self):
        self.do('common.interactionStates=1');self.queue()
        self.assertEqual(self.val('sent'),0)

    def test_emit_error_is_spent_and_does_not_read_old_world(self):
        self.do('s.tick(world(),d);now=102;fail_emit=true')
        with self.assertRaisesRegex(Exception,'UNCERTAIN_EMIT'):self.do('s.tick(world(),d)')
        self.assertTrue(self.val('s.used'));self.assertEqual(self.val('invalid'),0)
        self.do('s.tick(world(),d)');self.assertEqual(self.val('sent'),1)

    def test_timeout_wrong_target_or_identity_never_hands_off(self):
        self.queue();self.do('now=110')
        with self.assertRaisesRegex(Exception,'HANDOFF_TIMEOUT'):self.do('s.tick(world(),d)')
        self.assertEqual(self.val('sent'),1)
        self.setUp();self.queue();self.do("d.session='new'")
        with self.assertRaisesRegex(Exception,'IDENTITY_CHANGED'):self.do('s.tick(world(),d)')
        self.setUp();self.queue()
        self.do('ai.state=3;ai.previousState=7;ai.decision=1;walker.state=8;common.currentTargetPosition.x=99')
        self.assertTrue(self.do('return s.tick(world(),d)'))


class WakeFollowTests(unittest.TestCase):
    def setUp(self):
        fixture=lifecycle.LifecycleTests();fixture.start_controller=False;fixture.setUp();self.lua=fixture.lua
        self.lua.globals().fail_emit=getattr(self,'emit_failure',False)
        self.lua.globals().wake_module=self.lua.execute((ROOT/'mods/aic_companion_movement/wake.lua').read_text())
        self.do('''
ai={state=8,previousState=7,decision=5};walker={state=0};sent=0
common.interactionStates=0;common.currentTargetPosition={x=0,y=0,z=0}
local old=discover;discover=function(w)
 local d=old(w);d.ai_state=ai.state;d.decision=ai.decision;d.npc=2939921867;return d
end
local oldfresh=fresh_world;function fresh_world()
 oldfresh();local get=w.get
 w.get=function(self,n,id)
  if self.g~=generation then invalid_reads=invalid_reads+1;error('INVALID_WORLD') end
  if n=='DynamicActiveNpcState' then return ai elseif n=='DynamicPathWalker' then return walker end
  return get(self,n,id)
 end
end
api.wake=wake_module.new({now=api.now,log=api.log,moving=api.moving,
 emit=function(n,p) assert(not active);sent=sent+1;generation=generation+1
  if fail_emit then error('EMIT_FAILED') end end})
c=follow.new(api,discover,config);fresh_world();c.start(w,'token','abc-1',42)
request();ai.state=13;common.sleepTime=21;common.wakeUpTime=7;tick()
now=102;request();tick()
''')

    def do(self,s):return self.lua.execute(s)
    def val(self,s):return self.lua.eval(s)

    def test_no_overlap_then_follow_uses_native_navigation(self):
        self.assertEqual(self.val('sent'),1)
        self.do('request();tick();request()')
        self.assertEqual(self.val('calls'),0)
        self.do('ai.state=7;ai.decision=1;walker.state=2;tick();request()')
        self.assertEqual(self.val('calls'),0)
        self.do('ai.state=3;ai.previousState=7;walker.state=8;tick();request();ground();path();now=103;request()')
        self.assertEqual(self.val('calls'),1)
        self.assertEqual(self.val('invalid_reads'),0)

    def test_timeout_restores_schedule_without_retry(self):
        self.do('for t=103,110 do now=t;request();tick() end;tick()')
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertEqual(self.val('common.wakeUpTime'),6)
        self.assertEqual(self.val('sent'),1);self.assertEqual(self.val('calls'),0)
        self.assertEqual(self.val('invalid_reads'),0)

    def test_stopped_pending_event_does_not_resume(self):
        self.do("c.stop(nil,'REQUEST_ERROR');tick();ai.state=3;ai.previousState=7;ai.decision=1;walker.state=8;tick();request()")
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('calls'),0)
        self.assertEqual(self.val('common.sleepTime'),22)
        with self.assertRaises(Exception):self.do("c.start(w,'token','abc-1',42)")

    def test_ambiguous_emit_error_restores_on_fresh_tick_no_resend(self):
        self.emit_failure=True;self.setUp()
        self.assertEqual(self.val('c.state'),'STOPPED')
        self.assertEqual(self.val('common.sleepTime'),25) # no access to invalid world
        self.do('tick();request();tick()')
        self.assertEqual(self.val('c.cleanup'),'DONE')
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertEqual(self.val('common.wakeUpTime'),6)
        self.assertEqual(self.val('invalid_reads'),0)
        self.assertEqual(self.val('sent'),1)
        self.assertEqual(self.val('calls'),0)


if __name__=='__main__':unittest.main()
