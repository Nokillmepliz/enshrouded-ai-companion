import json
import unittest
from unittest.mock import patch
from tests import test_integrated_phase_d as fixtures
from companion.integrated_install import copy_approved
from companion.integrated_deployment import rollback_dry_run


class InstallerTests(unittest.TestCase):
    setUp=fixtures.DeploymentTests.setUp

    def run_copy(self,authorized=True,live=lambda:None):
        return copy_approved(self.plan,'pinned',self.package,self.game,self.package.parent/'transaction',
                             authorized=authorized,live=live)

    def test_verified_install_receipt_and_dry_run(self):
        receipt=self.run_copy()
        transaction=self.package.parent/'transaction'
        self.assertEqual(json.loads((transaction/'install-receipt.json').read_text()),receipt)
        self.assertTrue((transaction/'01-intent.json').exists())
        self.assertTrue((transaction/'01-verified.json').exists())
        self.assertEqual(rollback_dry_run(self.plan,'pinned',receipt,self.game)['status'],'ROLLBACK_DRY_RUN_PASS')
        self.assertEqual((self.game/'original').read_bytes(),b'original')
        with self.assertRaisesRegex(ValueError,'NEW_TRANSACTION'):self.run_copy()

    def test_no_authorization_no_write(self):
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):self.run_copy(False)
        self.assertFalse((self.game/'emf').exists())

    def test_partial_copy_preserved_and_journalled_no_receipt(self):
        def fail(a,b,*args):
            b.write(b'pa');raise OSError('fixture disk failure')
        with patch('companion.integrated_install.shutil.copyfileobj',side_effect=fail):
            with self.assertRaisesRegex(OSError,'disk failure'):self.run_copy()
        self.assertEqual((self.game/'emf/mods/test/main.lua').read_bytes(),b'pa')
        transaction=self.package.parent/'transaction'
        self.assertTrue((transaction/'failure.json').exists())
        self.assertFalse((transaction/'install-receipt.json').exists())

    def test_conflict_not_overwritten(self):
        p=self.game/'emf/mods/test/main.lua';p.parent.mkdir(parents=True);p.write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError,'CONFLICT'):self.run_copy()
        self.assertEqual(p.read_bytes(),b'unknown')

    def test_process_start_between_files_stops(self):
        calls=[]
        def live():
            calls.append(1)
            if len(calls)==2:raise ValueError('GAME_RUNNING')
        with self.assertRaisesRegex(ValueError,'GAME_RUNNING'):self.run_copy(live=live)
        self.assertFalse((self.game/'emf').exists())

    def test_source_changed_after_initial_validation(self):
        def live(): (self.package/'game/emf/mods/test/main.lua').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):self.run_copy(live=live)
        self.assertFalse((self.game/'emf').exists())
