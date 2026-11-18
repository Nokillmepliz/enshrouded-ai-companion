import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import os

from lupa import LuaRuntime
from companion.compatibility import file_hash, fingerprint
from companion.integrated_client import IntegratedClient
from companion.integrated_evidence import parse, fnv, FIELDS, verdict
from companion.integrated_deployment import validate_plan, preinstall, rollback_dry_run, installed
from scripts.prepare_phase_d_package import lua
from companion.integrated_writer import content_fingerprint, validate_state

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/'experimental/integrated_humanoid/patch.lua').read_text()

FIXTURE='''
function deep(t) if type(t)~='table' then return t end local r={} for k,v in pairs(t) do r[k]=deep(v) end return r end
profile={run_token=string.rep('a',32),plan_id=string.rep('b',64),profile_sha256=string.rep('c',64),
 baseline_sha256=string.rep('d',64),dependency_set_sha256=string.rep('e',64),accepted_limited_baseline=true,
 game_version='1287369|fixture',source_guid='source',clone_guid='clone',npc_id=2939921867,component_count=5,
 animation_graph='graph',gender='Male',use_new_proportions=false,template_count=1,
 hashkeys={beard=0,beardColorId=2,eyeBrowColor=3,eyeColor=4,hair=5,hairColorId=6,presetId=7,skinColor=8,voicePackId=9},
 dependencies={{guid='graph',type='Graph'}}}
setup={gender='Male',useNewProportions=false}
for k,v in pairs(profile.hashkeys) do setup[k]={value=v} end
source={guid='source',part=0,type={qualified_name='keen::ecs::TemplateResource'},data={name='source',components={
 {type='keen::ecs::CharacterSetup',value=setup},
 {type='keen::ecs::Faction',value={faction='Player'}},
 {type='keen::ecs::ActiveNpcState',value={npcId={value=12},nested={x=2}}},
 {type='keen::ecs::AnimationGraphResourceComponent2',value={animationGraph='graph'}},
 {type='keen::ecs::RenderEquipment',value={nested={a=true,b={1,2,3}}}}
}}}
resources={source=source,graph={data={}}}; frames={}; creates=0
profile.hierarchy_guid='hierarchy';profile.joint_count=2;profile.preset_collection_guid='presets'
profile.visual_references={{slot='head',guid='head',type='Item'}}
resources.hierarchy={data={hierarchyId='hierarchy',jointCount=2,jointNames={'a','b'}}}
resources.presets={data={presets={{presetId={value=7},references={head='head'}}}}}
resources.head={data={}}
game={version=profile.game_version,guid={hash=function() return profile.npc_id end},
 types={of=function(v) if v.type and v.value then return {primitive_type='BlobVariant'} end end,
 get=function() return {enum_fields={PlayerAlly={value=11}}} end},
 assets={get_resource=function(g) return resources[g] end,
 get_resources_by_type=function() return {source} end,
 create_resource=function(d,t,g,p)
 creates=creates+1; local r={guid=g,part=p,type={qualified_name=t},data=deep(d)}; resources[g]=r; return r
 end}}
loader={features={patch=true}}
local names={} for _,c in ipairs(source.data.components) do names[#names+1]=c.type end table.sort(names)
profile.component_fingerprint=patch.fnv(table.concat(names,','))
function run() patch.run(game,loader,profile,function(s) frames[#frames+1]=s end) end
'''


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().patch=self.lua.execute(PATCH)
        self.lua.execute(FIXTURE)

    def run_patch(self): self.lua.globals().run()

    def expected(self):
        p=self.lua.globals().profile
        keys=('run_token','plan_id','profile_sha256','baseline_sha256','source_guid','clone_guid',
              'component_count','component_fingerprint','animation_graph','npc_id','dependency_set_sha256',
              'gender','use_new_proportions')
        return {**{k:p[k] for k in keys},'hashkeys':dict(p.hashkeys),'dependencies_resolved':1,'npc_collision_scan':1,
                'hierarchy_guid':'hierarchy','joint_count':2,'visual_reference_count':1}

    def text(self): return '\n'.join(self.lua.globals().frames.values())

    def test_clone_preservation_and_real_emitter_parser_roundtrip(self):
        self.run_patch()
        values=parse(self.text(),self.expected())
        self.assertEqual(set(values),FIELDS)
        self.assertEqual(self.lua.eval('source.data.components[2].value.faction'),'Player')
        self.assertEqual(values['writer_status'],'REQUESTED_NOT_FINALIZED')
        self.assertFalse(verdict(values,{})['spawn_ready'])
        self.assertEqual(verdict(values,{})['verdict'],'LOAD_ONLY_UNCONFIRMED')

    def test_repeated_patch_refused_without_second_creation(self):
        self.run_patch()
        with self.assertRaisesRegex(Exception,'guid_collision'): self.run_patch()
        self.assertEqual(self.lua.globals().creates,1)

    def test_shallow_alias_source_mutation_detected(self):
        self.lua.execute('deep=function(v) return v end')
        with self.assertRaisesRegex(Exception,'source_mutated'): self.run_patch()
        self.assertEqual(len(self.lua.globals().frames),0)

    def test_uint32_userdata(self):
        self.assertEqual(self.lua.globals().patch.u32(SimpleNamespace(value=4294967295)),4294967295)
        for value in (True,-1,4294967296,1.5,'1',None):
            with self.subTest(value=value),self.assertRaises(Exception):
                self.lua.globals().patch.u32(SimpleNamespace(value=value))

    def test_canonical_integer_precision(self):
        self.assertTrue(self.lua.eval('patch.canonical(game,9007199254740992)~=patch.canonical(game,9007199254740993)'))

    def test_log_boundaries_stale_duplicate_and_corruption(self):
        self.run_patch(); text=self.text(); expected=self.expected()
        variants=[text.split('\n',1)[1], '\n'.join(text.splitlines()[:-1]), text+'\n'+text,
                  text.replace('a'*32,'f'*32),text.replace('END|','END|0'),
                  text.replace('source_unchanged|true','source_unchanged|false'),
                  text.replace('source_fnv32|','extra|'),text.replace('BEGIN|37','BEGIN|1')]
        # Count deliberately independent of future schema field additions.
        variants[-1]=text.replace('BEGIN|'+str(len(FIELDS)),'BEGIN|1')
        for altered in variants:
            with self.subTest(altered=altered[-70:]),self.assertRaises(ValueError): parse(altered,expected)

    def test_wrong_pinned_profile_and_values(self):
        self.run_patch()
        for key in ('plan_id','profile_sha256','component_count','dependency_set_sha256','npc_id','gender'):
            wrong=self.expected(); wrong[key]='wrong'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'MISMATCH'): parse(self.text(),wrong)


def patch_refusal(change,error,creates=0):
    def test(self):
        self.lua.execute(change)
        with self.assertRaisesRegex(Exception,error): self.run_patch()
        self.assertEqual(self.lua.globals().creates,creates)
        self.assertEqual(len(self.lua.globals().frames),0)
    return test


for name,change,error in [
 ('build',"game.version='1273043|old'",'UNSUPPORTED'),
 ('acceptance','profile.accepted_limited_baseline=false','baseline'),
 ('guid',"resources.clone={}",'guid_collision'),
 ('npc','source.data.components[3].value.npcId.value=profile.npc_id','npc_collision'),
 ('fractional_hash','setup.hair.value=1.5','HashKey32'),
 ('changed_hash','setup.hair.value=6','source_hashkey'),
 ('graph',"source.data.components[4].value.animationGraph='other'",'graph_changed'),
 ('dependency','resources.graph=nil','dependency_missing'),
 ('scan','profile.template_count=2','template_scan_count'),
 ('skeleton','resources.hierarchy.data.jointCount=3','skeleton_changed'),
 ('visual_reference',"resources.presets.data.presets[1].references.head='other'",'visual_reference_changed'),
 ('schema','profile.component_count=82','component_schema'),
 ('enum',"game.types.get=function() return {enum_fields={PlayerAlly={value=10}}} end",'faction_enum'),
 ('create_api',"game.assets.create_resource=function() error('api_refused') end",'api_refused')]:
    setattr(PatchTests,'test_refuse_'+name,patch_refusal(change,error))


class FakeBridge:
    def __init__(self,expected):
        self.expected=expected; self.calls=[]; self.session=1; self.mutate=None
        self.world=dict(status='running',kind='server',slot=1,name='AI Body Test')
        self.char=dict(storage='local',slot=1,name='Body Test')
    def hello(self):
        return dict(ok=True,emf='0.6.18',api=46,protocol=1,game_build=1287369,process='client',pid=100)
    def state(self):
        return copy.deepcopy(dict(ok=True,world=self.world,character=self.char,mods=[
            dict(id='lua',version='1.39.0',status='loaded'),
            dict(id='aic_integrated_observer',version='0.3.0',status='script')]))
    def console(self,text,**kwargs):
        self.calls.append(text); command,nonce=text.split(); command=command.split('.')[1]
        value=dict(schema=8,command=command,nonce=nonce,ok=True,read_only=True,spawn_ready=False,
            character='Body Test',context_provenance='WORLD_LOCAL_AND_API_REQUIRE_BRIDGE_STATE',
            eml_runtime_lookup='UNAVAILABLE_CONTENT_UNLOADED',
            evidence_operation='SESSION_ONLY' if command=='status' else 'PYTHON_LOCAL_VALIDATION_REQUIRED',
            session_token='abc-'+str(self.session),session=self.session,**self.expected)
        if self.mutate: self.mutate(value)
        return dict(ok=True,status='ran',output=['AIC_OBSERVER_V8 '+json.dumps(value,separators=(',',':'))])


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.expected=dict(run_token='a'*32,plan_id='b'*64,profile_sha256='c'*64)
        self.transport=FakeBridge(self.expected); self.client=IntegratedClient(self.transport,self.expected)
    def test_actual_protocol_shape(self):
        result=self.client.observe('status'); self.assertTrue(result['ok']); self.assertFalse(result['spawn_ready'])
        self.assertEqual(len(self.transport.calls),2)
    def test_forbidden_before_transport(self):
        for command in ('spawn','dismiss','quit','status\nspawn','load_world'):
            with self.assertRaisesRegex(ValueError,'FORBIDDEN'): self.client.observe(command)
            with self.assertRaisesRegex(ValueError,'FORBIDDEN'): self.client.request(command)
        self.assertEqual(self.transport.calls,[])
    def test_wrong_world_or_cloud_before_console(self):
        for obj,key,value in [(self.transport.world,'slot',257),(self.transport.world,'name','other'),
                              (self.transport.char,'storage','steam')]:
            old=obj[key];obj[key]=value
            with self.assertRaises(ValueError): self.client.observe('status')
            obj[key]=old
        self.assertEqual(self.transport.calls,[])
    def test_stale_nonce_plan_and_error(self):
        for key,value in [('nonce','a'*32),('run_token','f'*32),('plan_id','f'*64),('ok',False),('session',0)]:
            self.transport.mutate=lambda v:v.update({key:value})
            with self.subTest(key=key),self.assertRaises(ValueError): self.client.observe('status')
    def test_session_change_between_replies(self):
        self.transport.mutate=lambda v:setattr(self.transport,'session',self.transport.session+1)
        with self.assertRaisesRegex(ValueError,'SESSION_CHANGED'): self.client.observe('status')
    def test_world_change_during_request(self):
        self.transport.mutate=lambda v:self.transport.world.update(name='other')
        with self.assertRaisesRegex(ValueError,'WORLD_CONTEXT'): self.client.observe('status')
    def test_inspect_requires_evidence(self):
        with self.assertRaisesRegex(ValueError,'BUILD_EVIDENCE_REQUIRED'): self.client.observe('inspect')


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.package=root/'package';self.game=root/'game'
        self.game.mkdir();(self.game/'original').write_bytes(b'original')
        p=self.package/'game/emf/mods/test/main.lua';p.parent.mkdir(parents=True);p.write_bytes(b'fixture')
        self.baseline={'game':{'original':dict(bytes=8,sha256=file_hash(self.game/'original'))}}
        identity=dict(targets=['emf/mods/test/main.lua'],baseline_sha256=fingerprint(self.baseline))
        row=dict(source='game/emf/mods/test/main.lua',destination='emf/mods/test/main.lua',bytes=7,
                 sha256=file_hash(p),before_sha256=None,rollback='REMOVE_ONLY_IF_INSTALLED_HASH_MATCHES')
        self.plan=dict(format='aic_integrated_install_v1',build=1287369,identity=identity,plan_id=fingerprint(identity),entries=[row])
        self.receipt=dict(format='aic_integrated_receipt_v1',status='INSTALLED',build=1287369,plan_sha256='pinned',
                          plan_id=self.plan['plan_id'],entries=self.plan['entries'])
    def install_fixture(self): shutil.copytree(self.package/'game',self.game,dirs_exist_ok=True)
    def test_preflight_and_rollback_dry_run_do_not_write(self):
        self.assertEqual(preinstall(self.plan,self.package,self.game,self.baseline)['targets_absent'],1)
        self.install_fixture(); result=rollback_dry_run(self.plan,'pinned',self.receipt,self.game)
        self.assertFalse(result['executed']);self.assertTrue((self.game/'emf/mods/test/main.lua').exists())
        self.assertEqual((self.game/'original').read_bytes(),b'original')
    def test_corrupt_staging_and_unreviewed_extra(self):
        (self.package/'game/extra').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'UNREVIEWED'): validate_plan(self.plan,self.package)
    def test_existing_target_conflict(self):
        self.install_fixture()
        with self.assertRaisesRegex(ValueError,'CONFLICT'): preinstall(self.plan,self.package,self.game,self.baseline)
    def test_bad_receipt_or_changed_installed_refuses_cleanup(self):
        self.install_fixture()
        bad=copy.deepcopy(self.receipt);bad['build']=1273043
        with self.assertRaises(ValueError): rollback_dry_run(self.plan,'pinned',bad,self.game)
        (self.game/'emf/mods/test/main.lua').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'): rollback_dry_run(self.plan,'pinned',self.receipt,self.game)
    def test_unknown_shadow_blocks_cleanup(self):
        self.install_fixture();(self.game/'emf/content/client').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'SHADOW_REQUIRES'): rollback_dry_run(self.plan,'pinned',self.receipt,self.game)


class ObserverBootstrapTests(unittest.TestCase):
    def test_registered_readonly_commands_and_response_binding(self):
        runtime=LuaRuntime(unpack_returned_tuples=True)
        runtime.execute('''
        replies={}; commands={}; emf={dir='fixture',session=function() return 1 end,
        session_token=function() return 'abc-1' end,local_player=function() return 42 end,
        command=function(n,help,f) commands[n]=f end,reply=function(v) replies[#replies+1]=v end,
        json={encode=function(v) last=v; return 'fixture' end}}
        dofile=function() return {schema=8,run_token=string.rep('a',32),plan_id='b',profile_sha256='c'} end
        world={is_server=function() return true end,character_name=function() return 'Body Test' end}
        ''')
        runtime.execute((ROOT/'mods/aic_integrated_observer/main.lua').read_text())
        self.assertEqual(set(runtime.globals().commands),{'status','inspect','compare'})
        runtime.execute("commands.inspect(world,{string.rep('d',32)})")
        self.assertTrue(runtime.globals().last.ok);self.assertFalse(runtime.globals().last.spawn_ready)
        runtime.execute("commands.status(world,{'bad'})")
        self.assertIn('invalid_nonce',runtime.globals().replies[2])


class WriterTests(unittest.TestCase):
    def test_state_freshness_unload_and_no_inferred_readback(self):
        now=datetime.now(timezone.utc)
        state=dict(fingerprint='sha256:'+'a'*64,code=0,unloaded=True,truncated=False,errors=[],warnings=[],
                   mods=['aic_eml_humanoid 0.5.0'],built_at=now.isoformat())
        validate=lambda s:validate_state(s,state['fingerprint'],not_before=now-timedelta(seconds=1),not_after=now+timedelta(seconds=1))
        self.assertEqual(validate(state)['shadow_readback'],'UNKNOWN')
        for key,value in [('code',1),('unloaded',False),('truncated',True),('fingerprint','sha256:'+'b'*64),
                          ('errors',['failure']),('mods',['aic_eml_humanoid 0.4.0']),
                          ('built_at',(now-timedelta(minutes=1)).isoformat())]:
            with self.subTest(key=key),self.assertRaises(ValueError): validate(dict(state,**{key:value}))

    def test_upstream_fingerprint_fixture_and_metadata_limitation(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)
            names=['enshrouded.exe','enshrouded.kfc','enshrouded.kfc_resources','emf/emf_content.dll',
                   'mods/aic_eml_humanoid/mod.json','mods/aic_eml_humanoid/README.md','mods/aic_eml_humanoid/src/mod.lua']
            for name in names:
                p=game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'a');os.utime(p,ns=(0,0))
            for i in range(64): (game/f'enshrouded_{i:03}.dat').write_bytes(b'')
            timestamp=116444736000000000
            text='emf content fingerprint 2\nemf\t0.6.18\n'
            for label,name in [('base','enshrouded.kfc'),('kfc','enshrouded.kfc'),('resources','enshrouded.kfc_resources'),
                               ('exe','enshrouded.exe'),('dll','emf_content.dll')]:
                text+=f'{label}\t{name}\t1\t{timestamp}\n'
            text+='dats\t55\t64\nmod\taic_eml_humanoid\t0.5.0\t3\n'
            for name in ['mod.json','README.md','src\\mod.lua']: text+=f'file\t{name}\t1\t{timestamp}\n'
            expected='sha256:'+hashlib.sha256(text.encode()).hexdigest()
            self.assertEqual(content_fingerprint(game),expected)
            exe=game/'enshrouded.exe';exe.write_bytes(b'b');os.utime(exe,ns=(0,0))
            # Upstream fingerprint intentionally cannot detect same-size/time tampering.
            self.assertEqual(content_fingerprint(game),expected)
            other=game/'mods/other';other.mkdir()
            with self.assertRaisesRegex(ValueError,'UNREVIEWED_CONTENT_MOD'): content_fingerprint(game)
            other.rmdir()  # empty directory created by this fixture
            (game/'enshrouded.kfc.bak').write_bytes(b'old')
            with self.assertRaisesRegex(ValueError,'LEGACY'): content_fingerprint(game)
