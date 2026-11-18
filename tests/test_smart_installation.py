import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from companion.compatibility import file_hash
from companion.shadow_integrity import record
from companion.smart_deployment import CHANGED
from companion.smart_installation import replace,rollback_dry_run

class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.game=self.root/'game';self.package=self.root/'package';self.backup=self.root/'backup'
        self.baseline=dict(game={});rows=[];effective=[]
        for name in sorted(CHANGED)+['unchanged/'+str(i) for i in range(19)]:
            dst=self.game/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b'old')
            before=record(dst);self.baseline['game'][name]=before
            if name in CHANGED:
                src=self.package/'payload'/name;src.parent.mkdir(parents=True,exist_ok=True);src.write_bytes(b'new')
                saved=self.backup/'payload/game'/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(b'old')
                rows.append(dict(path=name,source='payload/'+name,before_sha256=before['sha256'],before_bytes=3,sha256=file_hash(src),bytes=3))
                effective.append(dict(path=name,sha256=file_hash(src),bytes=3))
            else:effective.append(dict(path=name,sha256=before['sha256'],bytes=3))
        self.manifest=dict(format='aic_smart_position_update_v1',version='0.1.1',entries=rows,effective_files=effective)
    def install(self,authorized=True):
        return replace(self.manifest,self.baseline,self.package,self.game,self.backup,self.root/'journal',authorized=authorized,live=lambda:None)
    def test_exact_install_and_dry_run(self):
        self.assertEqual(len(self.install()),4)
        self.assertEqual(rollback_dry_run(self.manifest,self.game,self.backup)['status'],'ROLLBACK_DRY_RUN_PASS')
        self.assertEqual((self.game/'unchanged/1').read_bytes(),b'old')
    def test_no_authorization_no_writes(self):
        with self.assertRaisesRegex(ValueError,'AUTHORIZED'):self.install(False)
        self.assertFalse((self.root/'journal').exists())
    def test_all_payloads_validated_before_first_write(self):
        (self.package/self.manifest['entries'][-1]['source']).write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'PAYLOAD'):self.install()
        self.assertFalse((self.root/'journal').exists())
        for name in CHANGED:self.assertEqual((self.game/name).read_bytes(),b'old')
    def test_replacement_failure_preserves_journal_no_rollback(self):
        import os
        original=os.replace;calls=[]
        def fail_second(a,b):
            calls.append(b)
            if len(calls)==2:raise PermissionError('simulated block')
            original(a,b)
        with patch('companion.smart_installation.os.replace',side_effect=fail_second):
            with self.assertRaises(PermissionError):self.install()
        self.assertTrue((self.root/'journal/failure.json').exists())
        self.assertEqual(sum((self.game/n).read_bytes()==b'new' for n in CHANGED),1)
    def test_existing_temp_is_not_deleted(self):
        p=self.game/self.manifest['entries'][0]['path'];temp=p.with_name(p.name+'.aic-smart-update.tmp');temp.write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError,'TEMP_CONFLICT'):self.install()
        self.assertEqual(temp.read_bytes(),b'unknown')

if __name__=='__main__':unittest.main()
