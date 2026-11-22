import copy
import json
from pathlib import Path
import tempfile
import unittest

from lupa.lua54 import LuaRuntime
from companion.movement import MovementClient
from companion.experimental_spawn import validate_context

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = '''
session='abc-1'; player=1; calls=0; ids={42}; x=0; faction=11; valid=true; missing=false
w={}
function w:entities() return ids end
function w:template(name,id) return {npcId=2939921867} end
function w:get(name,id)
 if name=='PlayerState' then return nil end
 if name=='Faction' then return {faction=faction} end
 if missing and name=='DynamicPathWalker' then return nil end
 if name=='ActiveNpcStateSaved' then return {spawnPosition={x=0,y=0,z=0}} end
 return {state=3,decision=0}
end
function w:position(id) return x,0,0 end
api={allow_move=true,session=function() return session end,player=function() return player end,
context=function() return valid end,moving=function() return existing end,
move=function(world,id,target,opts,callback)
 calls=calls+1; options=opts; cb=callback
 if fault then error('uncertain') end
 if refuse then return nil,'outside home' end
 return 7
end}
function move() return c.move_to(w,'abc-1',42,{x=4,y=0,z=0},'APPROVE_PROFILE_ONLY_MOVE') end
'''


class LuaMovementTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.globals().policy = self.lua.execute((ROOT/'mods/aic_companion_movement/controller.lua').read_text())
        self.lua.execute('c=policy.new(api)')

    def val(self, text): return self.lua.eval(text)
    def run_lua(self, text): self.lua.execute(text)
    def test_read_only_found_profile(self):
        self.assertEqual(self.val('c.discover(w).result'), 'FOUND_ONE')
        self.assertFalse(self.val('c.discover(w).guid_verified'))
        self.assertEqual(self.val('calls'), 0)
    def test_not_found(self):
        self.run_lua('ids={}')
        self.assertEqual(self.val('c.discover(w).result'), 'NOT_FOUND')
    def test_duplicate_id_profile_refuses_move(self):
        self.run_lua('ids={42,43}')
        self.assertEqual(self.val('c.discover(w).result'), 'AMBIGUOUS')
        with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 0)
    def test_bad_faction_or_missing_components_ambiguous(self):
        for setup in ('faction=1', 'faction=11;missing=true'):
            self.run_lua(setup)
            self.assertEqual(self.val('c.discover(w).result'), 'AMBIGUOUS')
    def test_wrong_context(self):
        self.run_lua('valid=false')
        with self.assertRaises(Exception): self.run_lua('c.discover(w)')
    def test_disabled(self):
        self.run_lua('api.allow_move=false')
        with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 0)
    def test_session_or_entity_changed(self):
        for setup in ("session='abc-2'", "session='abc-1';ids={99}"):
            self.run_lua(setup)
            with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 0)
    def test_existing_order_not_replaced(self):
        self.run_lua('existing=3')
        with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 0)
    def test_bad_target(self):
        for x in ('0/0', 'math.huge', '0', '6'):
            with self.assertRaises(Exception):
                self.run_lua("c.move_to(w,'abc-1',42,{x="+x+",y=0,z=0},'APPROVE_PROFILE_ONLY_MOVE')")
        self.assertEqual(self.val('calls'), 0)
    def test_progress_and_strict_arrival(self):
        self.run_lua('move()')
        self.assertEqual(self.val('c.status(w).state'), 'ACCEPTED')
        self.assertFalse(self.val('c.status(w).displacement_observed'))
        self.run_lua("x=1;cb(w,7,'arrived')")
        self.assertTrue(self.val('c.status(w).progress_observed'))
        self.assertEqual(self.val('c.status(w).state'), 'ENGINE_ARRIVED_NOT_AT_TARGET')
        self.run_lua('x=4')
        self.assertEqual(self.val('c.status(w).state'), 'ARRIVAL_OBSERVED')
    def test_timeout_stuck_gone_cancelled(self):
        self.run_lua('move()')
        for status in ('timeout','stuck','gone','cancelled'):
            self.run_lua("cb(w,7,'"+status+"')")
            self.assertEqual(self.val('c.status(w).state'), status.upper())
        self.assertEqual(self.val('options.seconds'), 30)
        self.assertIsNone(self.val('options.hold'))
    def test_uncertain_result_no_retry(self):
        self.run_lua('fault=true')
        for _ in range(2):
            with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 1)
    def test_refused_no_retry(self):
        self.run_lua('refuse=true;move()')
        self.assertEqual(self.val('c.status(w).state'), 'REFUSED')
        with self.assertRaises(Exception): self.run_lua('move()')
        self.assertEqual(self.val('calls'), 1)
    def test_identity_lost_after_accepted(self):
        self.run_lua("move();session='abc-2'")
        self.assertEqual(self.val('c.status(w).state'), 'IDENTITY_LOST_NO_RETRY')
    def test_host_discovery_and_locked_move(self):
        def encode(value):
            def plain(v):
                return {k:plain(item) for k,item in v.items()} if hasattr(v,'items') else v
            return json.dumps(plain(value),separators=(',',':'))
        self.lua.globals().encode=encode
        self.lua.globals().moddir=str(ROOT/'mods/aic_companion_movement')
        self.run_lua('''
commands={}; replies={}
function w:is_server() return true end
function w:character_name(id) return 'Body Test' end
local get=w.get
function w:get(name,id) if name=='PlayerState' and id==1 then return {} end;return get(self,name,id) end
local template=w.template
function w:template(name,id) if id==1 then return nil end;return template(self,name,id) end
ids={1,42}
emf={dir=moddir,session_token=api.session,local_player=api.player,villager_move=api.move,
villager_moving=api.moving,json={encode=encode},reply=function(s) replies[#replies+1]=s end,
command=function(name,description,fn) commands[name]=fn;return true end}
''')
        self.lua.execute((ROOT/'mods/aic_companion_movement/main.lua').read_text())
        self.run_lua("commands.discover(w,{string.rep('a',32)})")
        reply=json.loads(self.val('replies[1]')[13:])
        self.assertTrue(reply['ok'])
        self.assertEqual(reply['value']['discovery']['result'],'FOUND_ONE')
        self.assertLess(len(self.val('replies[1]')),964)
        self.run_lua("commands.move_to(w,{string.rep('b',32),'abc-1','42','4','0','0','APPROVE_PROFILE_ONLY_MOVE'})")
        self.assertIn('MOVEMENT_DISABLED_PENDING_REVIEW',self.val('replies[2]'))
        self.assertEqual(self.val('calls'),0)


class Transport:
    def __init__(self):
        self.calls=[]; self.result='FOUND_ONE'; self.session='abc-1'; self.fail=False
        self.mods=[dict(id=k,version=v,status='loaded') for k,v in
            [('lua','1.39.0'),('aic_integrated_observer','0.3.0'),('aic_first_spawn','0.1.1'),('aic_companion_movement','0.1.0')]]
    def hello(self):
        return dict(ok=True,emf='0.6.18',api=46,protocol=1,game_build=1287369,process='client',pid=99)
    def state(self):
        return dict(ok=True,character=dict(storage='local',slot=1,name='Body Test'),
            world=dict(status='running',kind='server',slot=1,name='AI Body Test'),mods=self.mods,
            player=dict(id=1,health=dict(value=100)))
    def console(self, command, **kwargs):
        self.calls.append(command)
        if self.fail and '.move_to' in command: raise TimeoutError('unknown')
        reply=dict(schema=1,nonce=command.split()[1],ok=True,value=dict(state='ACCEPTED',
            discovery=dict(session=self.session,player=1,result=self.result,entity=42)))
        return dict(ok=True,status='ran',output=['AIC_MOVEMENT '+json.dumps(reply)])


class PythonMovementTests(unittest.TestCase):
    def setUp(self): self.t=Transport(); self.c=MovementClient(self.t)
    def test_new_profile_does_not_weaken_spawn_context(self):
        with self.assertRaisesRegex(ValueError,'UNREVIEWED_MODS'):
            validate_context(self.t.hello(),self.t.state(),body_version='0.1.1')
        self.c.discover()
    def test_wrong_local_context(self):
        original=self.t.state
        self.t.state=lambda: dict(original(),character=dict(storage='steam',slot=1,name='Body Test'))
        with self.assertRaises(ValueError): self.c.discover()
        self.assertEqual(self.t.calls,[])
    def test_session_change(self):
        self.c.discover(); self.t.session='abc-2'
        with self.assertRaisesRegex(ValueError,'SESSION_CHANGED'): self.c.discover()
    def test_durable_intent_prevents_retry_after_uncertain(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'movement-intent.json';self.t.fail=True
            with self.assertRaises(TimeoutError):
                self.c.move_to(4,0,0,approval='APPROVE_PROFILE_ONLY_MOVE',intent_path=path)
            before=path.read_bytes()
            with self.assertRaises(FileExistsError):
                self.c.move_to(4,0,0,approval='APPROVE_PROFILE_ONLY_MOVE',intent_path=path)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(sum('.move_to' in s for s in self.t.calls),1)
    def test_ambiguous_and_not_found_no_intent(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'intent.json'
            for result in ('AMBIGUOUS','NOT_FOUND'):
                self.t.result=result
                with self.assertRaises(ValueError): self.c.move_to(4,0,0,approval='APPROVE_PROFILE_ONLY_MOVE',intent_path=path)
            self.assertFalse(path.exists())
    def test_invalid_target_and_approval(self):
        for target,approval in ((float('nan'),'APPROVE_PROFILE_ONLY_MOVE'),(4,'no')):
            with self.assertRaises(ValueError): self.c.move_to(target,0,0,approval=approval,intent_path='unused')
        self.assertEqual(self.t.calls,[])
    def test_observation_timeout_read_only(self):
        ticks=[0]
        result=self.c.observe_until_terminal(seconds=1,clock=lambda:ticks[0],sleep=lambda dt:ticks.__setitem__(0,ticks[0]+dt))
        self.assertEqual(result['result'],'OBSERVATION_TIMEOUT_NO_RETRY')
        self.assertTrue(all('.status ' in s for s in self.t.calls))


if __name__=='__main__': unittest.main()
