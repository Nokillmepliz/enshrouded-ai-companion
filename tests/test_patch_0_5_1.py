"""Pinned vendor reference conversion and minimal update regression fixtures."""
import copy
from datetime import datetime,timezone,timedelta
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

from lupa import LuaRuntime
from companion.compatibility import file_hash,fingerprint
from companion.integrated_evidence import parse
from companion.integrated_update import TARGETS,check_plan,preflight,rollback_plan,verify_updated,input_fingerprint
from companion.integrated_writer import validate_state,content_fingerprint
from test_integrated_phase_d import FIXTURE

ROOT=Path(__file__).resolve().parents[1]
GRAPH='402df515-5965-4b01-a17b-17d482a91af4'
ZERO='00000000-0000-0000-0000-000000000000'


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.patch=self.lua.execute((ROOT/'experimental/integrated_humanoid_0_5_1/patch.lua').read_text())
        self.lua.globals().patch=self.patch
        self.lua.execute(FIXTURE)
        # Real GUID syntax, and Reference(Guid::NONE) -> string, unlike the
        # historical fixture. Metadata strings are not stand-in GUID objects.
        self.lua.execute('''
        local mapping={source='e3736dff-0ad2-47fc-903c-66c1775836e8',
         clone='a1c90001-5e4d-4a91-8a1c-000000000001',
         graph='402df515-5965-4b01-a17b-17d482a91af4',hierarchy='87b29df6-6518-43ef-9298-e3f85a6204b9',
         head='11111111-1111-1111-1111-111111111111',presets='a1bea7fc-2122-4dd3-a471-2b815a65134b'}
        local function map(t)
         for k,v in pairs(t) do if type(v)=='table' then map(v) elseif mapping[v] then t[k]=mapping[v] end end
        end
        map(profile);map(source);map(resources)
        profile.visual_references[1].slot='head'
        local renamed={} for k,v in pairs(resources) do renamed[mapping[k] or k]=v end resources=renamed
        source.data.components[4].value.retargetData='00000000-0000-0000-0000-000000000000'
        profile.patch_version='0.5.1'
        ''')

    def test_guid_strings_and_case(self):
        for g in (GRAPH,GRAPH.upper()):
            self.assertEqual(self.patch.reference(g,False),(GRAPH,'GUID_STRING',None))

    def test_nullable_absence_representations(self):
        self.assertEqual(self.patch.reference(None,True),('null','LUA_NIL',None))
        self.assertEqual(self.patch.reference(ZERO,True),('null','GUID_STRING_ZERO',None))
        self.assertEqual(self.patch.reference(None,False)[2],'MISMATCH')
        self.assertEqual(self.patch.reference(ZERO,False)[2],'MISMATCH')

    def test_invalid_guids_not_coerced(self):
        for g in ('','null','nil',GRAPH+'x',GRAPH.replace('-',''),GRAPH.replace('4','z',1),' '+GRAPH):
            with self.subTest(g=g):self.assertEqual(self.patch.reference(g,True)[2],'MISMATCH')

    def test_unknown_types_rejected(self):
        for v in (False,1,1.5,self.lua.table(guid=GRAPH),SimpleNamespace(value=GRAPH),lambda:GRAPH):
            with self.subTest(v=type(v)):self.assertEqual(self.patch.reference(v,True)[2],'UNSUPPORTED_TYPE')

    def test_mapped_container_userdata_fields_are_strings(self):
        # Python userdata models __index of MappedStructValue, not a GUID wrapper.
        graph=SimpleNamespace(animationGraph=GRAPH,retargetData=ZERO)
        lines=[]
        self.patch.graph_check(graph,self.lua.globals().profile,lines.append)
        self.assertEqual(len(lines),2)
        self.assertTrue(all('container=userdata|lua_type=string' in s for s in lines))
        self.assertIn('method=GUID_STRING_ZERO',lines[1])

    def test_both_failures_diagnosed_before_assert(self):
        lines=[]
        graph=self.lua.table(animationGraph='bad',retargetData=GRAPH)
        with self.assertRaisesRegex(Exception,'ANIMATION_GRAPH_MISMATCH,RETARGET_DATA_MISMATCH'):
            self.patch.graph_check(graph,self.lua.globals().profile,lines.append)
        self.assertEqual(len(lines),2)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):
            parse('\n'.join(lines),{'run_token':'a'*32})

    def test_retarget_unsupported_independent(self):
        lines=[]
        with self.assertRaisesRegex(Exception,'RETARGET_DATA_UNSUPPORTED_TYPE'):
            self.patch.graph_check(self.lua.table(animationGraph=GRAPH,retargetData=False),self.lua.globals().profile,lines.append)
        self.assertIn('result=PASS',lines[0])

    def test_graph_unsupported_independent(self):
        lines=[]
        with self.assertRaisesRegex(Exception,'ANIMATION_GRAPH_UNSUPPORTED_TYPE'):
            self.patch.graph_check(self.lua.table(animationGraph=self.lua.table(),retargetData=ZERO),self.lua.globals().profile,lines.append)
        self.assertIn('result=PASS',lines[1])

    def test_original_bug_reproduced(self):
        self.assertFalse(self.lua.eval('source.data.components[4].value.retargetData==nil'))
        self.lua.globals().patch=self.lua.execute((ROOT/'experimental/integrated_humanoid/patch.lua').read_text())
        with self.assertRaisesRegex(Exception,'graph_changed'):self.lua.globals().run()
        self.assertEqual(self.lua.globals().creates,0)

    def test_graph_failure_never_creates_or_emits_success(self):
        self.lua.execute("source.data.components[4].value.animationGraph='bad'")
        with self.assertRaisesRegex(Exception,'ANIMATION_GRAPH_MISMATCH'):self.lua.globals().run()
        self.assertEqual(self.lua.globals().creates,0)
        self.assertTrue(all('AIC_EVIDENCE_V8' not in s for s in self.lua.globals().frames.values()))

    def test_preserved_safety_checks_still_refuse(self):
        changes=[("setup.hair.value=999",'source_hashkey'),
                 ("profile.template_count=2",'template_scan_count'),
                 ("source.data.components[3].value.npcId.value=profile.npc_id",'npc_collision'),
                 ("profile.joint_count=3",'skeleton_changed'),
                 ("profile.dependencies[1].guid='missing'",'dependency_missing'),
                 ("profile.component_count=999",'component_schema')]
        for change,error in changes:
            with self.subTest(error=error):
                self.setUp();self.lua.execute(change)
                with self.assertRaisesRegex(Exception,error):self.lua.globals().run()
                self.assertEqual(self.lua.globals().creates,0)

    def test_full_clone_evidence_roundtrip_and_source_unchanged(self):
        before=self.patch.canonical(self.lua.globals().game,self.lua.globals().source.data)
        self.lua.globals().run()
        p=self.lua.globals().profile
        expected={k:v for k,v in p.items()};expected['hashkeys']=dict(p.hashkeys)
        expected.update(dependencies_resolved=1,npc_collision_scan=1,visual_reference_count=1)
        text='\n'.join(self.lua.globals().frames.values())
        values=parse(text,expected)
        self.assertEqual(values['patch'],'0.5.1')
        self.assertEqual(values['retarget_data'],'null')
        self.assertEqual(before,self.patch.canonical(self.lua.globals().game,self.lua.globals().source.data))
        expected['patch_version']='0.5.0'
        with self.assertRaisesRegex(ValueError,'patch'):parse(text,expected)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.package=self.root/'package';self.game=self.root/'game';self.backup=self.root/'backup'
        self.game.mkdir();self.package.mkdir()
        self.rows=[];old=[]
        for i,name in enumerate(sorted(TARGETS)):
            a=self.game/name;b=self.package/'game'/name
            a.parent.mkdir(parents=True,exist_ok=True);b.parent.mkdir(parents=True,exist_ok=True)
            a.write_bytes(f'old-{i}'.encode());b.write_bytes(f'new-{i}'.encode())
            self.rows.append(dict(destination=name,current_sha256=file_hash(a),new_sha256=file_hash(b),new_bytes=b.stat().st_size,new_mtime_ns=b.stat().st_mtime_ns))
            old.append(dict(destination=name,sha256=file_hash(a),bytes=a.stat().st_size))
        self.parent=self.root/'receipt.json';self.parent.write_text(json.dumps({'entries':old}))
        self.sha=file_hash(self.parent)
        identity=dict(targets=sorted(TARGETS),parent_receipt_sha256=self.sha)
        self.plan=dict(format='aic_patch_update_v1',patch_version='0.5.1',identity=identity,plan_id=fingerprint(identity),entries=self.rows,current_install_entries=old)

    def check(self):return preflight(self.plan,self.package,self.game,self.parent,self.sha)

    def test_minimal_update_and_restore_dry_run_isolated(self):
        self.assertEqual(self.check()['files'],4)
        # Fixture-only copying; production code exposes no mutating entrypoint.
        shutil.copytree(self.game,self.backup)
        shutil.copytree(self.package/'game',self.game,dirs_exist_ok=True)
        result=rollback_plan(self.plan,self.game,self.backup)
        self.assertEqual(len(result['operations']),4)
        self.assertFalse(result['executed']);self.assertFalse(result['full_live_rollback_ready'])
        for r in self.rows:
            self.assertEqual(file_hash(self.game/r['destination']),r['new_sha256'])
        shutil.copytree(self.backup,self.game,dirs_exist_ok=True)
        self.assertEqual(self.check()['files'],4)

    def test_payload_tamper(self):
        (self.package/'game'/self.rows[0]['destination']).write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'PAYLOAD'):self.check()

    def test_current_tamper(self):
        (self.game/self.rows[0]['destination']).write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'CURRENT_INSTALL'):self.check()

    def test_immutable_parent_tamper(self):
        self.parent.write_text('{}')
        with self.assertRaisesRegex(ValueError,'PARENT'):self.check()

    def test_extra_package_refused(self):
        (self.package/'game/extra').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'EXTRA'):self.check()

    def test_original_hardlink_refused_without_writing(self):
        path=self.game/self.rows[0]['destination'];original=self.game/'original.dat'
        os.link(path,original)
        digest=file_hash(original)
        with self.assertRaises(ValueError):self.check()
        self.assertEqual(file_hash(original),digest)

    def test_template_receipt_cannot_enable_bridge(self):
        with self.assertRaisesRegex(ValueError,'NOT_EXECUTED'):
            verify_updated(self.plan,'a'*64,{'status':'TEMPLATE_NOT_EXECUTED'},self.game)

    def test_rollback_tampered_backup_refused(self):
        shutil.copytree(self.game,self.backup)
        shutil.copytree(self.package/'game',self.game,dirs_exist_ok=True)
        (self.backup/self.rows[0]['destination']).write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError,'ROLLBACK_HASH'):rollback_plan(self.plan,self.game,self.backup)

    def test_new_timestamp_required(self):
        p=self.package/'game'/self.rows[0]['destination'];os.utime(p,ns=(0,0))
        with self.assertRaisesRegex(ValueError,'METADATA'):self.check()


class StateTests(unittest.TestCase):
    def test_stale_failed_old_version_and_fingerprint_refused(self):
        now=datetime.now(timezone.utc)
        state=dict(fingerprint='sha256:'+'a'*64,code=0,unloaded=True,truncated=False,errors=[],warnings=[],mods=['aic_eml_humanoid 0.5.1'],built_at=now.isoformat())
        def check(s):return validate_state(s,state['fingerprint'],not_before=now-timedelta(seconds=1),not_after=now+timedelta(seconds=1),patch_version='0.5.1')
        self.assertEqual(check(state)['status'],'PASS')
        for changes in ({'code':2},{'mods':['aic_eml_humanoid 0.5.0']},{'fingerprint':'sha256:'+'b'*64},
                        {'built_at':(now-timedelta(hours=1)).isoformat()}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):check(dict(state,**changes))

    def test_version_changes_fingerprint_with_same_file_facts(self):
        facts={n:dict(size=1,mtime_ns=0) for n in ['enshrouded.exe','enshrouded.kfc','enshrouded.kfc_resources','emf/emf_content.dll',
               'mods/aic_eml_humanoid/mod.json','mods/aic_eml_humanoid/README.md','mods/aic_eml_humanoid/src/mod.lua']}
        self.assertNotEqual(input_fingerprint(facts,'0.5.0'),input_fingerprint(facts,'0.5.1'))
        old=input_fingerprint(facts,'0.5.1');facts['mods/aic_eml_humanoid/src/mod.lua']['size']=2
        self.assertNotEqual(old,input_fingerprint(facts,'0.5.1'))


if __name__=='__main__':unittest.main()
