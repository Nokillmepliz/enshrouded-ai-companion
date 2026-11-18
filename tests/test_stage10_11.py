import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lupa.lua54 import LuaRuntime
from companion.experimental_spawn import AUTHORIZATION, GUID, ExperimentalClient, readiness, validate_context
from companion.experimental_install_check import verify as verify_install
from companion.compatibility import file_hash

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = '''
calls=0; writes=0; spent=false; t=100; session='abc-1'; player=1
px=0; faction=11; npc=2939921867; context_ok=true; candidate=false
spawn_result=42; spawn_error=false; consume_ok=true; ground_ok=true; path_ok=true
api={now=function() return t end,session=function() return session end,player=function() return player end,
context=function(w,s,p) return context_ok and s==session and p==player end,
position=function(w,id) return {x=px,y=10,z=0} end,
unused=function() return not spent end,
consume=function() writes=writes+1;if not consume_ok then return false end;spent=true;return true end,
log=function(s) end,has_candidate=function(w,n) return candidate end,
wall=function() return wall or false end,
ground=function(w,x,z,cb) ground_cb=cb;return ground_ok end,
path=function(w,a,b,opts,cb) options=opts;path_cb=cb;return path_ok and 1 or nil end,
spawn=function(w,g,x,y,z) calls=calls+1;spawn_guid=g;spawn_y=y;if spawn_error then error('partial fault') end;return spawn_result end,
inspect=function(w,id) return {npc=npc,faction=faction,player=false} end}
binding={guid='a1c90001-5e4d-4a91-8a1c-000000000001',build=1287369}
function begin() c.probe({},session,player,string.rep('a',32)) end
function ground(fog,water,y) ground_cb({},true,4,y or 10,0,'ok',nil,fog or 'none',water) end
function path(status,reaches,move,x)
 path_cb({},{status=status or 'found',reaches=reaches~=false,length=4,count=1},{{x=x or 4,y=10,z=0,move=move or 0}})
end
function ready() begin();ground();path() end
function spawn(auth) c.spawn({},session,player,string.rep('a',32),auth or 'I_APPROVE_ONE_DISPOSABLE_SPAWN') end
'''


class LuaExperimentalTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.globals().policy = self.lua.execute((ROOT/'mods/aic_first_spawn/controller.lua').read_text())
        self.lua.execute('c=policy.new(api,binding)')

    def run_lua(self, script): self.lua.execute(script)
    def val(self, expr): return self.lua.eval(expr)
    def assert_no_spawn(self): self.assertEqual(self.val('calls'), 0)

    def test_load_does_not_spawn(self): self.assert_no_spawn()
    def test_missing_authorization(self):
        self.run_lua("ready();spawn('no')")
        self.assert_no_spawn()
    def test_wrong_guid_binding(self):
        with self.assertRaises(Exception): self.run_lua("binding.guid='bad';policy.new(api,binding)")
    def test_no_position_confirmation(self):
        self.run_lua('begin();spawn()');self.assert_no_spawn()
    def test_success_exact_guid_distance_and_no_overrides(self):
        self.run_lua('ready();spawn()')
        self.assertEqual(self.val('calls'),1);self.assertEqual(self.val('spawn_guid'),GUID)
        self.assertAlmostEqual(self.val('spawn_y'),10.1)
        self.assertEqual(self.val('c.state'),'RETURNED_UNVERIFIED')
        self.assertFalse(self.val('c.status({}).spawn_ready'))
    def test_duplicate_spawn(self):
        self.run_lua('ready();spawn();spawn()');self.assertEqual(self.val('calls'),1)
    def test_reload_keeps_latch(self):
        self.run_lua('ready();spawn();c=policy.new(api,binding);begin();spawn()')
        self.assertEqual(self.val('calls'),1)
    def test_zero_return_is_ambiguous_consumed(self):
        self.run_lua('ready();spawn_result=0;spawn();spawn()')
        self.assertEqual(self.val('calls'),1);self.assertTrue(self.val('spent'))
    def test_partial_native_fault_consumes_attempt(self):
        self.run_lua('ready();spawn_error=true;spawn();spawn()')
        self.assertEqual(self.val('calls'),1);self.assertEqual(self.val('c.reason'),'not_ready_or_spent')
    def test_write_failure_prevents_spawn(self):
        self.run_lua('ready();consume_ok=false;spawn()');self.assert_no_spawn()
    def test_session_change_during_probe(self):
        self.run_lua("begin();session='new-2';ground();spawn()");self.assert_no_spawn()
    def test_session_change_before_spawn(self):
        self.run_lua("ready();session='new-2';spawn()");self.assert_no_spawn()
    def test_player_movement(self):
        self.run_lua('ready();px=1;spawn()');self.assert_no_spawn()
    def test_candidate_already_present(self):
        self.run_lua('candidate=true;begin();spawn()');self.assert_no_spawn()
    def test_candidate_appears_after_probe(self):
        self.run_lua('ready();candidate=true;spawn()');self.assert_no_spawn()
    def test_ground_api_refused(self):
        self.run_lua('ground_ok=false;begin();spawn()');self.assert_no_spawn()
    def test_unknown_fog(self):
        self.run_lua("begin();ground('unknown');spawn()");self.assert_no_spawn()
    def test_shroud(self):
        self.run_lua("begin();ground('shroud');spawn()");self.assert_no_spawn()
    def test_water(self):
        self.run_lua("begin();ground('none',12);spawn()");self.assert_no_spawn()
    def test_large_height_delta(self):
        self.run_lua("begin();ground('none',nil,12);spawn()");self.assert_no_spawn()
    def test_nan_ground(self):
        self.run_lua('begin();ground(nil,nil,0/0);spawn()');self.assert_no_spawn()
    def test_ground_delay(self):
        self.run_lua('begin();t=121;ground();spawn()');self.assert_no_spawn()
    def test_no_callback_times_out_on_status(self):
        self.run_lua('begin();t=121;c.status({})')
        self.assertEqual(self.val('c.reason'),'query_timeout');self.assert_no_spawn()
    def test_path_api_refused(self):
        self.run_lua('begin();path_ok=false;ground();spawn()');self.assert_no_spawn()
    def test_path_reaches_false(self):
        self.run_lua("begin();ground();path('found',false);spawn()");self.assert_no_spawn()
    def test_path_endpoint_too_far(self):
        self.run_lua("begin();ground();path('found',true,0,3);spawn()");self.assert_no_spawn()
    def test_jump_rejected(self):
        self.run_lua("begin();ground();path('found',true,2);spawn()");self.assert_no_spawn()
    def test_wall(self):
        self.run_lua('begin();wall=true;ground();spawn()');self.assert_no_spawn()
    def test_expired_ready(self):
        self.run_lua('ready();t=121;spawn()');self.assert_no_spawn()
    def test_late_callback_after_stop(self):
        self.run_lua("begin();c.stop('cancel');ground();spawn()");self.assert_no_spawn()
    def test_faction_mismatch_does_not_delete(self):
        self.run_lua('ready();spawn();faction=3;c.observe({})')
        self.assertEqual(self.val('c.state'),'STOPPED');self.assertEqual(self.val('calls'),1)
    def test_npc_mismatch_is_not_adopted(self):
        self.run_lua('ready();spawn();npc=100;c.observe({})')
        self.assertEqual(self.val('c.state'),'STOPPED')
    def test_no_delete_interface(self):
        self.assertIsNone(self.val('c.destroy'));self.assertIsNone(self.val('c.dismiss'))
    def test_refused_context(self):
        self.run_lua('context_ok=false;begin();spawn()');self.assert_no_spawn()


def good_state():
    return {'ok':True,'character':{'storage':'local','slot':1,'name':'Body Test'},
        'world':{'status':'running','kind':'server','slot':1,'name':'AI Body Test'},
        'player':{'id':1,'health':{'value':100}},
        'mods':[dict(id=i,version=v,status=s,reason='') for i,v,s in
            [('lua','1.39.0','loaded'),('aic_integrated_observer','0.3.0','script'),('aic_first_spawn','0.1.0','script')]]}


class FakeTransport:
    def __init__(self):
        self.data=good_state();self.phase='NEW';self.probe=None;self.sent=[];self.lose=False
    def hello(self): return dict(ok=True,emf='0.6.18',api=46,protocol=1,game_build=1287369,process='client',pid=42)
    def state(self): return copy.deepcopy(self.data)
    def console(self, text, **kwargs):
        self.sent.append(text);parts=text.split();cmd=parts[0].split('.')[-1]
        if cmd=='probe': self.phase='READY';self.probe=parts[1]
        if cmd=='spawn':
            self.phase='RETURNED_UNVERIFIED'
            if self.lose: raise TimeoutError('reply lost after mutation')
        r=dict(schema=1,nonce=parts[1],ok=True,state=self.phase,session='abc-1',player=1,
               probe=self.probe,production_spawn_ready=False,spawn_ready=False)
        return dict(ok=True,status='ran',output=['AIC_EXPERIMENT '+json.dumps(r)])


class PythonExperimentalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.transport=FakeTransport();self.now=100
        self.binding=dict(guid=GUID,build=1287369,key='a'*32)
        self.client=ExperimentalClient(self.transport,self.binding,self.temp.name,clock=lambda:self.now)
    def spawn(self):
        return self.client.spawn_once(authorization=AUTHORIZATION,clear_area=True,disposable_risk=True)
    def test_no_authorization(self):
        with self.assertRaises(ValueError): self.client.spawn_once(authorization=None)
        self.assertFalse(self.transport.sent)
    def test_missing_visual_or_disposable_consent(self):
        for a,b in [(False,True),(True,False)]:
            with self.assertRaises(ValueError): self.client.spawn_once(authorization=AUTHORIZATION,clear_area=a,disposable_risk=b)
    def test_not_local(self):
        self.transport.data['character']['storage']='cloud'
        with self.assertRaisesRegex(ValueError,'LOCAL'):self.client.prepare()
    def test_wrong_world_slot(self):
        self.transport.data['world']['slot']=2
        with self.assertRaisesRegex(ValueError,'LOCAL'):self.client.prepare()
    def test_wrong_character(self):
        self.transport.data['character']['name']='Other'
        with self.assertRaisesRegex(ValueError,'LOCAL'):self.client.prepare()
    def test_wrong_build(self):
        h=self.transport.hello();h['game_build']=1273043
        with self.assertRaises(ValueError):validate_context(h,self.transport.state())
    def test_wrong_guid(self):
        with self.assertRaises(ValueError): ExperimentalClient(self.transport,dict(self.binding,guid='wrong'),self.temp.name)
    def test_success_and_exclusive_retry_block(self):
        self.client.prepare();self.spawn()
        with self.assertRaisesRegex(ValueError,'CONSUMED'): self.spawn()
        self.assertEqual(sum(t.startswith('aic_first_spawn.spawn ') for t in self.transport.sent),1)
    def test_lost_response_reconnect_no_retry(self):
        self.client.prepare();self.transport.lose=True
        with self.assertRaises(TimeoutError):self.spawn()
        self.client=ExperimentalClient(self.transport,self.binding,self.temp.name,clock=lambda:self.now)
        with self.assertRaisesRegex(ValueError,'CONSUMED'):self.spawn()
    def test_context_changes_after_prepare(self):
        self.client.prepare();self.transport.data['player']['id']=2
        with self.assertRaisesRegex(ValueError,'CONTEXT'):self.spawn()
    def test_unconfirmed_position(self):
        self.client.prepare();self.transport.phase='GROUND'
        with self.assertRaisesRegex(ValueError,'UNCONFIRMED'):self.spawn()
    def test_expired_probe(self):
        self.client.prepare();self.now=121
        with self.assertRaisesRegex(ValueError,'EXPIRED'):self.spawn()
    def test_unexpected_mod(self):
        self.transport.data['mods'].append(dict(id='other',status='loaded'))
        with self.assertRaisesRegex(ValueError,'MODS'):self.client.prepare()
    def test_dead_player(self):
        self.transport.data['player']['health']['value']=0
        with self.assertRaisesRegex(ValueError,'ALIVE'):self.client.prepare()
    def test_mutation_surface_is_separate_and_no_destroy(self):
        with self.assertRaisesRegex(ValueError,'FORBIDDEN'):self.client.request('destroy',42)
    def test_direct_spawn_request_not_authorized(self):
        with self.assertRaisesRegex(ValueError,'DURABLE_INTENT'):self.client.request('spawn','abc-1',1,'a'*32,AUTHORIZATION)
        self.assertFalse(self.transport.sent)
    def test_readiness_is_not_runtime_success(self):
        r=readiness()
        for k in ['spawn_ready','production_spawn_ready','experimental_spawn_executed']:self.assertFalse(r[k])
        self.assertEqual(r['RUNTIME_RENDER_CONFIRMED'],'UNKNOWN')


class LuaHostIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.globals().policy=self.lua.execute((ROOT/'mods/aic_first_spawn/controller.lua').read_text())
        def encode(value):
            def convert(v):
                if hasattr(v,'items'):return {k:convert(x) for k,x in v.items()}
                return v
            return json.dumps(convert(value),separators=(',',':'))
        self.lua.globals().encode=encode
        self.lua.execute('''
key=string.rep('b',32);binding.key=key;nonce=string.rep('a',32)
latch_value='UNUSED:'..key;commands={};write_fail=false;flush_fail=false;close_fail=false
io={open=function(path,mode)
 if missing_file then return nil end
 return {read=function() return latch_value end,
 write=function(self,s) if write_fail then return nil end;latch_value=s;return self end,
 flush=function() if flush_fail then return nil end;return true end,
 close=function() if close_fail then return nil end;return true end}
end}
os={time=function() return t end}
dofile=function(path) if path:match('binding.lua$') then return binding end;return policy end
w={is_server=function() return true end,character_name=function() return 'Body Test' end,
entities=function() if extra_player then return {1,2} end;return {1} end,
get=function(self,name,id)
 if name=='PlayerState' then if id==1 or (id==2 and extra_player) then return {} end;return nil end
 if name=='Faction' then return {faction=11} end
 return nil end,
template=function(self,name,id) if id==42 and name=='ActiveNpcState' then return {npcId=2939921867} end;return nil end,
position=function(self,id) return px,10,0 end}
emf={dir='mock',session_token=api.session,session=function() return 1 end,local_player=api.player,
ground_at=api.ground,path_find=api.path,find_wall=function() return nil end,spawn=api.spawn,
log=function(s) end,reply=function(s) response=s end,json={encode=encode},
command=function(name,help,fn) commands[name]=fn;return true end}
function command(name,...) commands[name](w,{nonce,key,...}) end
function host_ready() command('probe',session,player);ground_cb(w,true,4,10,0,'ok',nil,'none',nil);
 path_cb(w,{status='found',reaches=true,length=4,count=1},{{x=4,y=10,z=0,move=0}}) end
function host_spawn() command('spawn',session,player,nonce,'I_APPROVE_ONE_DISPOSABLE_SPAWN') end
''')
        self.reload()
    def reload(self): self.lua.execute((ROOT/'mods/aic_first_spawn/main.lua').read_text())
    def run_lua(self,s):self.lua.execute(s)
    def reply(self):return json.loads(self.lua.globals().response.split(' ',1)[1])
    def test_actual_host_spawn_and_readonly_observation(self):
        self.run_lua("host_ready();host_spawn();command('observe')")
        self.assertEqual(self.lua.globals().calls,1)
        self.assertEqual(self.reply()['observation']['faction'],11)
        self.assertLessEqual(len(self.lua.globals().response),950)
    def test_spent_file_survives_actual_host_reload(self):
        self.run_lua('host_ready();host_spawn()');self.reload()
        self.run_lua('host_spawn()');self.assertEqual(self.lua.globals().calls,1)
    def test_missing_latch_file_blocks_actual_host(self):
        self.run_lua('missing_file=true');self.reload()
        self.run_lua('host_spawn()');self.assertEqual(self.lua.globals().calls,0)
    def test_io_write_failure(self):
        self.run_lua('host_ready();write_fail=true;host_spawn()');self.assertEqual(self.lua.globals().calls,0)
    def test_io_flush_failure_keeps_spent_no_spawn(self):
        self.run_lua('host_ready();flush_fail=true;host_spawn()')
        self.assertEqual(self.lua.globals().calls,0)
        self.assertTrue(self.lua.globals().latch_value.startswith('SPENT!:'))
    def test_io_close_failure(self):
        self.run_lua('host_ready();close_fail=true;host_spawn()');self.assertEqual(self.lua.globals().calls,0)
    def test_two_players_rejected(self):
        self.run_lua("extra_player=true;command('probe',session,player);host_spawn()")
        self.assertEqual(self.lua.globals().calls,0)
    def test_bad_capability_no_spawn(self):
        self.run_lua("host_ready();key='wrong';host_spawn()")
        self.assertEqual(self.lua.globals().calls,0)
    def test_async_exception_is_stopped(self):
        self.run_lua("command('probe',session,player);w.position=function() error('unavailable') end;ground_cb(w,true,4,10,0,'ok',nil,'none',nil)")
        self.run_lua("w.position=function() return 0,10,0 end;command('status')")
        self.assertEqual(self.reply()['state'],'STOPPED')
        self.assertEqual(self.lua.globals().calls,0)


class InstallationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.game=self.root/'game';self.game.mkdir()
        self.file=self.game/'main.lua';self.file.write_bytes(b'code')
        self.latch=self.game/'attempt.lock';self.latch.write_bytes(b'UNUSED:'+b'a'*32)
        self.binding=dict(guid=GUID,build=1287369,key='a'*32)
        self.entries=[dict(path='main.lua',sha256=file_hash(self.file),bytes=4),
                      dict(path='attempt.lock',sha256=file_hash(self.latch),bytes=39)]
        self.manifest=dict(format='aic_stage10_11_additive_install_v1',game=str(self.game),entries=self.entries,
            client_binding_sha256='bind',backup_plan_sha256='bp',prior_receipt_sha256='prior',
            runtime_mutable_file=dict(path='attempt.lock'))
        self.receipt=dict(format='aic_experiment_receipt_v1',status='INSTALLED',manifest_sha256='manifest',
            entries=self.entries,backup_path=str(self.root/'backup'),backup_manifest_sha256='bm')
        self.backup_plan=dict(files=[dict(group='saves',path='character0.ksd',sha256='expected',bytes=4)])
        self.bm=dict(files=[dict(relative='saves/character0.ksd',sha256='expected',bytes=4)])
        def read(path,digest):
            return {'exact-install-manifest.json':self.manifest,'receipt.json':self.receipt if digest=='receipt' else {},
                'client-binding.json':self.binding,'backup-plan.json':self.backup_plan,'manifest.json':self.bm,
                'update-manifest.json':dict(local_package=str(self.root),update_plan_sha256='old'),
                'update-plan.json':{}}[path.name]
        self.read=patch('companion.experimental_install_check.read_pinned',side_effect=read);self.read.start();self.addCleanup(self.read.stop)
        for name in ['check_plan','verify_updated','verify_backup']:
            p=patch('companion.experimental_install_check.'+name);p.start();self.addCleanup(p.stop)
    def check(self):return verify_install(self.root,'manifest',self.root/'receipt.json','receipt',self.root)
    def test_verified_receipt_gate(self):self.assertEqual(self.check(),self.binding)
    def test_missing_install_status_blocks(self):
        self.receipt['status']='PLANNED'
        with self.assertRaisesRegex(ValueError,'RECEIPT'):self.check()
    def test_changed_installed_code_blocks(self):
        self.file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'CHANGED'):self.check()
    def test_wrong_backup_baseline_blocks(self):
        self.bm['files'][0]['sha256']='older'
        with self.assertRaisesRegex(ValueError,'BACKUP'):self.check()
    def test_corrupt_lock_blocks(self):
        self.latch.write_bytes(b'SPENT!:other')
        with self.assertRaisesRegex(ValueError,'LATCH'):self.check()
    def test_spent_latch_permits_only_diagnostics_gate(self):
        self.latch.write_bytes(b'SPENT!:'+b'a'*32)
        self.assertEqual(self.check(),self.binding)  # spawn policy independently rejects spent


if __name__=='__main__':unittest.main()
