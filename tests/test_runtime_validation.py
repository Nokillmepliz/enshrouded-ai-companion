import copy
import hashlib
import unittest
from companion.runtime_validation import bridge_error,reassess_post_close,semantic_readback,canonical,redirection


def row(i=1,mtime=10):
    return dict(sha256=hashlib.sha256(b'').hexdigest(),size=0,volume=1,file_id=i,links=1,mtime_ns=mtime)


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.archive='backup/enshrouded_2026-11-18T16-46-15.log'
        self.before={'enshrouded.log':row(),'emf/chain_status.txt':row(2)}
        self.after=copy.deepcopy(self.before);self.after[self.archive]=row()
        self.after['enshrouded.log']=row(3,25);self.after['emf/chain_status.txt']['mtime_ns']=21
        self.kw=dict(archive=self.archive,session_start_ns=20,session_end_ns=30)
    def check(self):return reassess_post_close(self.before,self.after,**self.kw)
    def test_precise_rotation_and_same_chain(self):self.assertEqual(self.check()['status'],'ATTRIBUTION_PASS')
    def test_chain_content(self):
        self.after['emf/chain_status.txt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'CHAIN_CONTENT'):self.check()
    def test_chain_identity(self):
        self.after['emf/chain_status.txt']['file_id']=99
        with self.assertRaisesRegex(ValueError,'CHAIN_CONTENT'):self.check()
    def test_chain_time(self):
        self.after['emf/chain_status.txt']['mtime_ns']=31
        with self.assertRaisesRegex(ValueError,'OUTSIDE'):self.check()
    def test_archive_content(self):
        self.after[self.archive]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'EXACT_PREVIOUS'):self.check()
    def test_archive_recreated(self):
        self.after[self.archive]['file_id']=6
        with self.assertRaisesRegex(ValueError,'RENAMED'):self.check()
    def test_archive_hardlink(self):
        self.after[self.archive]['links']=2
        with self.assertRaises(ValueError):self.check()
    def test_unexpected_backup(self):
        self.after['backup/unknown.dll']=row(9)
        with self.assertRaisesRegex(ValueError,'UNATTRIBUTED'):self.check()
    def test_unexpected_emf(self):
        self.after['emf/unknown.ini']=row(9)
        with self.assertRaisesRegex(ValueError,'UNATTRIBUTED'):self.check()
    def test_removal(self):
        self.before['original.dat']=row(9)
        with self.assertRaisesRegex(ValueError,'REMOVAL'):self.check()


class BridgeTests(unittest.TestCase):
    def test_access_not_busy(self):
        r=bridge_error('could not connect (error 5; 8 clients connected already?)')
        self.assertEqual(r['category'],'ACCESS_DENIED');self.assertEqual(r['client_limit_reached'],'UNPROVEN')
    def test_not_found(self):self.assertEqual(bridge_error('no pipe x: is the game running?')['category'],'PIPE_NOT_FOUND')
    def test_busy_not_limit_proof(self):self.assertEqual(bridge_error('error 231')['category'],'PIPE_BUSY')
    def test_timeout(self):self.assertEqual(bridge_error('error 121')['category'],'WAIT_TIMEOUT')
    def test_unknown_hint(self):self.assertEqual(bridge_error('8 clients already?')['category'],'UNKNOWN')


class RedirectionTests(unittest.TestCase):
    def setUp(self):
        self.game=r'D:\Game';self.header='# started 2026-11-18 16:46:15 local time; exe\n# redirect_test=1\n'
        self.line='+1ms t2 CreateFileW "D:\\Game\\enshrouded.kfc" => "D:\\Game\\emf\\content\\client\\enshrouded.kfc" access=0x80000000(GENERIC_READ) disp=OPEN_EXISTING -> handle 0x123'
    def check(self,line=None):return redirection(self.header+(self.line if line is None else line),self.game,{'enshrouded.kfc'},started_local='2026-11-18 16:46:15')
    def test_read_open(self):self.assertEqual(self.check()['status'],'PASS')
    def test_metadata_not_read(self):self.assertEqual(self.check(self.line.replace('CreateFileW','GetFileAttributesW'))['status'],'INCOMPLETE')
    def test_failed_handle(self):self.assertEqual(self.check(self.line.replace('handle 0x123','error 5'))['status'],'INCOMPLETE')
    def test_write_not_read(self):self.assertEqual(self.check(self.line.replace('0x80000000','0x40000000'))['status'],'INCOMPLETE')
    def test_wrong_target(self):
        with self.assertRaisesRegex(ValueError,'WRONG_REDIRECT'):self.check(self.line.replace('content\\client','content\\server'))
    def test_stale_log(self):
        self.header=self.header.replace('16:46:15','16:46:16')
        with self.assertRaisesRegex(ValueError,'SESSION'):self.check()


class SemanticTests(unittest.TestCase):
    def setUp(self):
        data={'name':'source','components':[{'$type':'keen::ecs::'+k,'$value':v} for k,v in
            [('Faction',{'faction':'Neutral'}),('ActiveNpcState',{'npcId':{'value':1}}),
             ('CharacterSetup',{'presetId':{'value':2}}),('AnimationGraphResourceComponent2',{'retargetData':None}),
             ('RenderEquipment',{'preserve':[1,2]})]]}
        self.source=dict(mode='READ_ONLY',guid='source',part=0,type='keen::ecs::TemplateResource',resource=data)
        self.ss=copy.deepcopy(self.source);self.clone=copy.deepcopy(self.source);self.clone['guid']='clone'
        self.clone['resource']['name']='AIC_Humanoid_Companion_Experimental'
        self.clone['resource']['components'][0]['$value']['faction']='PlayerAlly'
        self.clone['resource']['components'][1]['$value']['npcId']['value']=42
        meta=dict(canonical_resource_sha256=hashlib.sha256(canonical(data).encode()).hexdigest(),component_count=5,
            character_setup={'presetId':{'value':2}},animation={'retargetData':None},hierarchy_guid='hierarchy',joints=102,
            decoded_preset_references=[dict(slot='head',guid='head')])
        self.p=dict(source_guid='source',clone_guid='clone',npc_id=42,expected_resource_metadata=meta,dependencies=[dict(guid='head',type='keen::ItemInfo')])
        self.h=dict(mode='READ_ONLY',guid='hierarchy',part=0,type='keen::ModelHierarchyResource',resource={'jointCount':102})
        self.presets=dict(mode='READ_ONLY',guid='a1bea7fc-2122-4dd3-a471-2b815a65134b',resource={'presets':[dict(presetId={'value':2},references={'head':'head'})]})
        self.lookup=[dict(mode='READ_ONLY_GUID_LOOKUP',guid='head',count=2,resources=[dict(guid='head',part=0,type='keen::ItemInfo'),dict(guid='head',part=0,type='keen::UiTextureResource')])]
    def check(self):return semantic_readback(self.source,self.ss,self.clone,self.h,self.presets,self.lookup,self.p)
    def test_composite_resource_identity(self):self.assertEqual(self.check()['status'],'PASS')
    def test_unexpected_component_mutation(self):
        self.clone['resource']['components'][-1]['$value']['preserve'][0]=7
        with self.assertRaisesRegex(ValueError,'CLONE_CHANGE'):self.check()
    def test_source_mutation(self):
        self.ss['resource']['name']='changed'
        with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):self.check()
    def test_wrong_npc(self):
        self.clone['resource']['components'][1]['$value']['npcId']['value']=43
        with self.assertRaisesRegex(ValueError,'CLONE_CHANGE'):self.check()
    def test_dependency_wrong_type(self):
        self.lookup[0]['resources'][0]['type']='wrong'
        with self.assertRaisesRegex(ValueError,'DEPENDENCY_TYPE'):self.check()
    def test_duplicate_dependency(self):
        self.lookup[0]['resources'][1]=copy.deepcopy(self.lookup[0]['resources'][0])
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.check()
    def test_visual_reference_changed(self):
        self.presets['resource']['presets'][0]['references']['head']='wrong'
        with self.assertRaisesRegex(ValueError,'VISUAL_REFERENCE'):self.check()
    def test_skeleton_count(self):
        self.h['resource']['jointCount']=101
        with self.assertRaisesRegex(ValueError,'SKELETON'):self.check()


if __name__=='__main__':unittest.main()
