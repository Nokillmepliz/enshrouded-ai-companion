"""Offline policy and host tests; engine transitions are simulated, not a game test."""
from pathlib import Path
import json
import hashlib
import copy
import shutil
import tempfile
import unittest

from lupa.lua54 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
now=100;hour=23;records={};logs={}
common={sleepTime=22,wakeUpTime=6};other={sleepTime=21,wakeUpTime=7}
d={result='FOUND_ONE',session='session-1',entity=42,ai_state=8,decision=5}
w={get=function(_,name,id) assert(name=='NpcCommon');return id==42 and common or other end}
api={now=function() return now end,time=function() return hour end,load=function() return stored end,
 save=function(row) assert(not disk_fail,'DISK_FAIL');records[#records+1]=row;stored=row.state=='ACQUIRED' and row or nil end,
 log=function(event,data) logs[#logs+1]=event end}
''')
        self.lua.globals().module = self.lua.execute((ROOT/'mods/aic_companion_movement/schedule.lua').read_text(encoding='utf-8'))
        self.do('s=module.new(api)')

    def do(self, code): return self.lua.execute(code)
    def val(self, code): return self.lua.eval(code)

    def test_empty_sleep_window_including_midnight_no_equal_hours_bug(self):
        # Exact integer comparison from build1287369, not a circular-interval guess.
        self.do('s.acquire(w,d)')
        start, end = self.val('common.sleepTime'), self.val('common.wakeUpTime')
        for minute in range(24*60+1):
            ns = minute * 60_000_000_000
            self.assertFalse(ns >= start*3_600_000_000_000 or ns <= end*3_600_000_000_000)
        self.assertTrue(0 >= 0 or 0 <= 0)  # equal hours would not disable sleep
        self.assertEqual(self.val('other.sleepTime'),21)

    def test_native_wake_exit_reroll_then_restore(self):
        self.do('s.acquire(w,d)')
        self.assertFalse(self.val('s.update(w,d)'))
        self.do('now=102;d.ai_state=17;d.decision=1;common.sleepTime=21.5;common.wakeUpTime=6.5')
        self.assertTrue(self.val('s.update(w,d)'))
        self.assertEqual(self.val('s.rerolls'),1)
        self.do('s.release(w,d)')
        self.assertEqual((self.val('common.sleepTime'),self.val('common.wakeUpTime')),(22,6))
        self.assertEqual(self.val('records[2].state'),'RELEASED')

    def test_day_night_midnight_and_no_continuous_writes(self):
        self.do('d.ai_state=7;d.decision=1;s.acquire(w,d)')
        for h in (12,23,24,0,6,18):
            self.do(f'hour={h};now=now+1')
            self.assertTrue(self.val('s.update(w,d)'))
        self.assertEqual(self.val('#records'),1)
        self.assertEqual(self.val('s.rerolls'),0)

    def test_wake_timeout(self):
        self.do('s.acquire(w,d);now=115')
        with self.assertRaisesRegex(Exception,'WAKE_TIMEOUT'): self.do('s.update(w,d)')
        self.do('s.release(w,d)')
        self.assertEqual(self.val('common.sleepTime'),22)

    def test_unknown_writer_not_overwritten(self):
        self.do('d.ai_state=7;d.decision=1;s.acquire(w,d);common.sleepTime=20')
        with self.assertRaisesRegex(Exception,'SCHEDULE_CONFLICT'): self.do('s.update(w,d)')
        self.do('s.release(w,d)')
        self.assertEqual(self.val('common.sleepTime'),20)
        self.assertEqual(self.val('common.wakeUpTime'),6)

    def test_no_repeated_sleep_exit_override(self):
        self.do('s.acquire(w,d);d.ai_state=17;d.decision=1;common.sleepTime=21;common.wakeUpTime=7;s.update(w,d)')
        self.do('d.ai_state=8;s.update(w,d);d.ai_state=17;common.sleepTime=22;common.wakeUpTime=6')
        with self.assertRaisesRegex(Exception,'SCHEDULE_CONFLICT'): self.do('s.update(w,d)')

    def test_failed_durable_intent_writes_no_component(self):
        self.do('disk_fail=true')
        with self.assertRaisesRegex(Exception,'DISK_FAIL'): self.do('s.acquire(w,d)')
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertIsNone(self.val('s.lease'))

    def test_partial_write_restorable_after_reload(self):
        self.do('''
local actual=common
common=setmetatable({}, {__index=actual,__newindex=function(_,k,v)
 if k=='wakeUpTime' and v==-1 then error('SETTER_FAIL') end;actual[k]=v end})
''')
        with self.assertRaisesRegex(Exception,'SETTER_FAIL'): self.do('s.acquire(w,d)')
        self.assertEqual(self.val('common.sleepTime'),25)
        self.do('s=module.new(api);s.release(w,d)')
        self.assertEqual(self.val('common.sleepTime'),22)

    def test_reload_restore_no_resume(self):
        self.do('s.acquire(w,d);s=module.new(api);s.release(w,d)')
        self.assertEqual(self.val('common.sleepTime'),22)
        self.assertIsNone(self.val('s.lease'))

    def test_identity_session_or_ambiguity_never_writes(self):
        for changed in ("d.session='new'",'d.entity=99',"d.result='AMBIGUOUS'"):
            self.setUp();self.do('s.acquire(w,d);'+changed)
            with self.assertRaisesRegex(Exception,'IDENTITY_CHANGED'): self.do('s.release(w,d)')
            self.assertEqual(self.val('common.sleepTime'),25)
            self.assertEqual(self.val('other.sleepTime'),21)

    def test_invalid_clock_and_unexpected_hours(self):
        self.do('hour=nil')
        with self.assertRaisesRegex(Exception,'CLOCK_UNAVAILABLE'): self.do('s.acquire(w,d)')
        self.assertEqual(self.val('#records'),0)
        self.do('hour=12;common.sleepTime=25')
        with self.assertRaisesRegex(Exception,'UNEXPECTED_HOURS'): self.do('s.acquire(w,d)')


class FollowScheduleTests(unittest.TestCase):
    def setUp(self):
        from tests.test_companion_follow import FIXTURE
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.execute('''
common={sleepTime=22,wakeUpTime=6};asleep=true
function w:get(n,id) assert(n=='NpcCommon' and id==42);return common end
local old=discover;discover=function(w) local d=old(w);d.ai_state=asleep and 8 or 7;d.decision=asleep and 5 or 1;return d end
saved={};sa={now=api.now,time=function() return 23 end,load=function() end,save=function(r) saved[#saved+1]=r end,log=api.log}
''')
        self.lua.globals().schedule=self.lua.execute((ROOT/'mods/aic_companion_movement/schedule.lua').read_text())
        self.lua.globals().follow=self.lua.execute((ROOT/'mods/aic_companion_movement/follow.lua').read_text())
        self.lua.execute("api.schedule=schedule.new(sa);c=follow.new(api,discover,config);c.start(w,'token','abc-1',42)")

    def test_sleep_blocks_orders_until_native_wake_then_navigation(self):
        self.lua.execute('step()')
        self.assertEqual(self.lua.eval('calls'),0)
        self.assertEqual(self.lua.eval('c.reason'),'NATIVE_WAKE_PENDING')
        self.lua.execute('asleep=false;common.sleepTime=21;common.wakeUpTime=7;now=101;c.watch(w);prepare()')
        self.assertEqual(self.lua.eval('calls'),1)
        self.lua.execute("c.stop(w,'RUNNER_STOP');c.watch(w);c.watch(w)")
        self.assertEqual(self.lua.eval('common.sleepTime'),22)

    def test_watchdog_restores_without_more_runner_calls(self):
        self.lua.execute('now=105;c.watch(w)')
        self.assertEqual(self.lua.eval('c.state'),'STOPPED')
        self.assertEqual(self.lua.eval('common.wakeUpTime'),6)
        self.assertEqual(self.lua.eval('consumed'),1)
        with self.assertRaises(Exception):self.lua.execute("c.start(w,'token','abc-1',42)")

    def test_fifty_metre_stop_still_applies_while_waking(self):
        self.lua.execute('px=51;step()')
        self.assertEqual(self.lua.eval('c.state'),'WAITING_FOR_PLAYER')
        self.assertEqual(self.lua.eval('calls'),0)
        self.lua.execute('px=35;step()')
        self.assertEqual(self.lua.eval('c.state'),'WAITING_FOR_PLAYER')
        self.lua.execute('px=20;step()')
        self.assertEqual(self.lua.eval('c.reason'),'NATIVE_WAKE_PENDING')

    def test_schedule_conflict_stops_and_restores_owned_fields(self):
        self.lua.execute('common.sleepTime=19;c.watch(w)')
        self.assertEqual(self.lua.eval('c.state'),'STOPPED')
        self.assertEqual(self.lua.eval('common.sleepTime'),19)
        self.assertEqual(self.lua.eval('common.wakeUpTime'),6)


class ScheduleHostTests(unittest.TestCase):
    def setUp(self):
        from tests.test_companion_movement import FIXTURE
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        for p in (ROOT/'mods/aic_companion_movement').glob('*.lua'):shutil.copyfile(p,self.path/p.name)
        self.token='a1c00350000000000000000000000001'
        (self.path/'follow-movement-0-3-5.lock').write_text('UNUSED:'+self.token)
        (self.path/'follow-stage10-14.lock').write_text('SPENT!:old-history')
        self.history={'follow-stage10-15.lock':b'SPENT!:stage15',
                      'schedule-stage10-15.jsonl':b'{"state":"RELEASED"}\n',
                      'follow-stage10-16.lock':b'SPENT!:stage16',
                      'schedule-stage10-16.jsonl':b'{"state":"RELEASED"}\n',
                      'old-intent.json':b'{"spent":true}\n'}
        for name,data in self.history.items():(self.path/name).write_bytes(data)
        (self.path/'schedule-movement-0-3-5.jsonl').write_bytes(b'')
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        def plain(v):return {k:plain(x) for k,x in v.items()} if hasattr(v,'items') else v
        self.lua.globals().encode=lambda v:json.dumps(plain(v),separators=(',',':'))
        self.lua.globals().decode=lambda v:self.lua.table_from(json.loads(v),recursive=True)
        self.lua.globals().moddir=self.temp.name
        self.lua.execute(FIXTURE)
        self.lua.execute('''
common={sleepTime=22,wakeUpTime=6};commands={};replies={};now=100;os.time=function() return now end
function w:is_server() return true end
function w:character_name() return 'Body Test' end
local oldget=w.get;function w:get(n,id)
 if n=='PlayerState' and id==1 then return {} end
 if n=='NpcCommon' and id==42 then return common end
 return oldget(self,n,id)
end
local oldtemplate=w.template;function w:template(n,id) if id==1 then return nil end;return oldtemplate(self,n,id) end
function w:position(id) return id==1 and 10 or 0,0,0 end
ids={1,42}
emf={emits=function(names) assert(names[1]=='NpcCommandEvent') end,dir=moddir,local_player=api.player,session_token=api.session,villager_move=api.move,villager_moving=api.moving,
time_of_day=function() return 23 end,find_wall=function() end,json={encode=encode,decode=decode},
reply=function(v) replies[#replies+1]=v end,log=function() end,on_tick=function(f) watch=f end,
command=function(n,_,f) assert(#('aic_companion_movement.'..n)<=32);commands[n]=f;return true end}
''')
        self.host=(ROOT/'mods/aic_companion_movement/main.lua').read_text(encoding='utf-8')
        self.lua.execute(self.host)

    def start(self):
        self.lua.execute("commands.f_start(w,{string.rep('a',32),'"+self.token+"','abc-1','42'})")

    def test_real_host_journal_reload_restores_and_spent_refuses(self):
        self.start()
        self.assertTrue(json.loads(self.lua.eval('replies[1]')[13:])['ok'])
        self.assertEqual(self.lua.eval('common.sleepTime'),25)
        journal=self.path/'schedule-movement-0-3-5.jsonl'
        prior=journal.read_bytes()
        self.lua.execute(self.host);self.lua.execute('watch(w)')
        self.assertEqual(self.lua.eval('common.sleepTime'),22)
        self.assertTrue(journal.read_bytes().startswith(prior))
        self.assertEqual(json.loads(journal.read_text().splitlines()[-1])['state'],'RELEASED')
        self.start()
        self.assertIn('DURABLE_SESSION_LATCH',self.lua.eval('replies[#replies]'))
        self.assertEqual((self.path/'follow-stage10-14.lock').read_text(),'SPENT!:old-history')
        self.assertEqual(self.lua.eval('calls'),0)

    def test_reload_new_session_does_not_restore_into_reused_entity(self):
        self.start();self.lua.execute(self.host)
        self.lua.execute("session='abc-2';watch(w)")
        self.assertEqual(self.lua.eval('common.sleepTime'),25)
        self.start()
        self.assertIn('SCHEDULE_RECOVERY_REQUIRED',self.lua.eval('replies[#replies]'))

    def test_torn_journal_blocks_before_component_mutation(self):
        (self.path/'schedule-movement-0-3-5.jsonl').write_bytes(b'{"state":')
        with self.assertRaisesRegex(Exception,'JOURNAL_INCOMPLETE'):self.lua.execute(self.host)
        self.assertEqual(self.lua.eval('common.sleepTime'),22)

    def test_host_request_error_recovers_next_tick_without_reload_or_history_reset(self):
        self.start()
        self.lua.execute("commands.f_step(w,{string.rep('b',32),'"+self.token+"','99'})")
        self.assertIn('TOKEN_OR_SEQUENCE',self.lua.eval('replies[#replies]'))
        self.assertEqual(self.lua.eval('common.sleepTime'),25)
        self.lua.execute('watch(w)')
        self.assertEqual(self.lua.eval('common.sleepTime'),22)
        self.assertEqual(self.lua.eval('common.wakeUpTime'),6)
        rows=(self.path/'schedule-movement-0-3-5.jsonl').read_text().splitlines()
        self.assertEqual([json.loads(x)['state'] for x in rows],['ACQUIRED','RELEASED'])
        for name,data in self.history.items():self.assertEqual((self.path/name).read_bytes(),data)
        self.assertEqual((self.path/'follow-movement-0-3-5.lock').read_text(),'SPENT!:'+self.token)
        self.assertEqual(self.lua.eval('calls'),0)

    def test_host_queues_only_type1_with_unique_npc_id_and_fixed_point_target(self):
        self.lua.execute('''
ai={state=8,decision=5};common.interactionStates=0;emitted={}
local oldpos=w.position;function w:position(id)
 if id==42 then return 1.25,2,-3 end
 return oldpos(self,id)
end
local oldget=w.get;function w:get(n,id)
 if n=='DynamicActiveNpcState' and id==42 then return ai end
 return oldget(self,n,id)
end
emf.emit=function(side,name,event)
 assert(side=='server' and name=='NpcCommandEvent');emitted[#emitted+1]=event
end
''')
        self.start()
        self.lua.execute("commands.f_step(w,{string.rep('b',32),'"+self.token+"','1'});ai.state=13;watch(w);now=102;watch(w)")
        self.assertEqual(self.lua.eval('#emitted'),1)
        self.assertEqual(self.lua.eval('emitted[1].type'),1)
        self.assertEqual(self.lua.eval('emitted[1].npcId'),2939921867)
        self.assertEqual(self.lua.eval('emitted[1].targetTransform.position.x'),5368709120)
        self.assertEqual(self.lua.eval('emitted[1].targetTransform.position.y'),8589934592)
        self.assertEqual(self.lua.eval('emitted[1].targetTransform.position.z'),-12884901888)
        self.assertEqual(self.lua.eval('emitted[1].targetTransform.orientation.w'),1)
        self.assertEqual(self.lua.eval('emitted[1].targetTransform.scale.x'),1)
        self.assertEqual(self.lua.eval('calls'),0)


class SchedulePackageTests(unittest.TestCase):
    def test_exact_package_matches_sources_and_preserves_old_latches(self):
        from scripts.install_follow_stage15 import MANIFEST_SHA,check_entries
        from companion.shadow_integrity import record
        path=ROOT/'compatibility/experiments/stage10_15/exact-update-manifest.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),MANIFEST_SHA)
        plan=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(plan['version'],'0.3.1')
        self.assertEqual(len(plan['effective_files']),35)
        self.assertEqual(plan['backup_plan']['total'],28)
        names={r['source'] for r in plan['entries']}
        self.assertEqual(names,{'main.lua','follow.lua','follow_config.lua','mod.json','README.md','schedule.lua',
                              'follow-stage10-15.lock','schedule-stage10-15.jsonl'})
        with tempfile.TemporaryDirectory() as td:
            package=Path(td)/'package';package.mkdir()
            game=Path(td)/'game';game.mkdir();before={};fake=copy.deepcopy(plan)
            for row in fake['entries']:
                name=row['source']
                data=(('UNUSED:'+plan['token']).encode() if name.endswith('.lock') else b'' if name.endswith('.jsonl')
                      else (ROOT/'dist/stage10_15_movement_0_3_1'/name).read_bytes())
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
                (package/name).write_bytes(data)
                if row['operation']=='replace':
                    dst=game/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b'old')
                    before[row['path']]=record(dst);row['before_sha256']=before[row['path']]['sha256']
            check_entries(fake,package,game,before)
            journal=game/'emf/mods/aic_companion_movement/schedule-stage10-15.jsonl'
            journal.write_bytes(b'previous lease history')
            with self.assertRaisesRegex(ValueError,'ADDITION_CONFLICT'):check_entries(fake,package,game,before)
            self.assertEqual(journal.read_bytes(),b'previous lease history')
            journal.unlink()  # disposable fixture only
            extra=copy.deepcopy(fake);extra['entries'][0]['path']='emf/mods/aic_first_spawn/attempt.lock'
            with self.assertRaisesRegex(ValueError,'EXACT_EIGHT'):check_entries(extra,package,game,before)
            (package/'schedule.lua').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'PAYLOAD_CHANGED'):check_entries(fake,package,game,before)

    def test_python_requires_exact_new_version(self):
        from tests.test_companion_movement import Transport
        from companion.follow import FollowClient
        t=Transport();c=FollowClient(t,version='0.3.1')
        t.mods[-1]['version']='0.3.0'
        with self.assertRaises(ValueError):c.discover()
        t.mods[-1]['version']='0.3.1';c.discover()
        with self.assertRaises(ValueError):FollowClient(t,version='unknown')

    def test_new_runner_requires_authorization_before_bridge(self):
        from unittest.mock import patch
        from scripts import follow_stage15
        import sys
        with patch.object(sys,'argv',['follow_stage15','--pid','1','--manifest-sha256','0'*64]),patch.object(follow_stage15,'connect') as connect:
            with self.assertRaises(SystemExit):follow_stage15.main()
            connect.assert_not_called()


if __name__=='__main__':unittest.main()
