from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from companion.compatibility import file_hash
from companion.experimental_install import PATHS,validate,copy_seven,removal_dry_run


class AdditiveInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.game=self.root/'game';self.game.mkdir()
        self.package=self.root/'package';self.package.mkdir();self.journal=self.root/'journal'
        self.rows=[]
        for name in sorted(PATHS):
            p=self.package/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
            self.rows.append(dict(path=name,source='payload/'+name,sha256=file_hash(p),bytes=p.stat().st_size,before_sha256=None))
        self.m=dict(format='aic_stage10_11_additive_install_v1',build=1287369,entries=self.rows)
        self.guard=lambda:None
    def install(self,authorized=True):
        return copy_seven(self.m,self.package,self.game,self.journal,authorized=authorized,live=self.guard)
    def test_success_and_dry_run_no_removal(self):
        rows=self.install();receipt=dict(status='INSTALLED',entries=self.rows,installed_records=rows)
        dry=removal_dry_run(self.m,receipt,self.game)
        self.assertFalse(dry['executed']);self.assertEqual(dry['count'],7)
        self.assertEqual(len([p for p in self.game.rglob('*') if p.is_file()]),7)
    def test_authorization_required(self):
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):self.install(False)
        self.assertFalse(self.journal.exists())
    def test_existing_file_never_overwritten(self):
        p=self.game/self.rows[-1]['path'];p.parent.mkdir(parents=True);p.write_bytes(b'user file')
        with self.assertRaisesRegex(ValueError,'CONFLICT'):self.install()
        self.assertEqual(p.read_bytes(),b'user file');self.assertFalse(self.journal.exists())
    def test_unknown_path_rejected(self):
        self.rows[-1]['path']='enshrouded.kfc'
        with self.assertRaisesRegex(ValueError,'SEVEN'):self.install()
    def test_changed_source_rejected_before_any_copy(self):
        (self.package/self.rows[-1]['source']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE'):self.install()
        self.assertFalse(self.journal.exists())
    def test_partial_failure_keeps_journal_and_no_rollback(self):
        import shutil
        real=shutil.copyfileobj;calls=[]
        def copy(a,b,*args):
            calls.append(1)
            if len(calls)==2:
                b.write(b'partial');raise OSError('copy denied')
            return real(a,b,*args)
        with patch('companion.experimental_install.shutil.copyfileobj',side_effect=copy):
            with self.assertRaises(OSError):self.install()
        self.assertTrue((self.journal/'failed.json').exists())
        self.assertEqual((self.game/self.rows[0]['path']).read_bytes(),self.rows[0]['path'].encode())
        self.assertEqual((self.game/self.rows[1]['path']).read_bytes(),b'partial')
    def test_game_running_guard_prevents_write(self):
        def refuse():raise ValueError('GAME_RUNNING')
        self.guard=refuse
        with self.assertRaisesRegex(ValueError,'RUNNING'):self.install()
        self.assertFalse(self.journal.exists())
    def test_changed_file_blocks_removal_plan(self):
        rows=self.install();(self.game/self.rows[0]['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'NOT_REMOVABLE'):
            removal_dry_run(self.m,dict(status='INSTALLED',entries=self.rows,installed_records=rows),self.game)
    def test_no_existing_mod_directory_adoption(self):
        (self.game/'emf/mods/aic_first_spawn').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'DIRECTORY_CONFLICT'):self.install()


if __name__=='__main__':unittest.main()
