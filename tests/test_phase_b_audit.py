"""Post-operation proof must reject any unapproved difference, not just count files."""
import copy
from pathlib import Path
import struct
import tempfile
import unittest

from scripts.stage10_10_1_phase_b_audit import verify_delta, kfc_header


class PostCleanupAudit(unittest.TestCase):
    def setUp(self):
        v = dict(bytes=4, sha256='a'*64, mtime_ns=123)
        self.before = dict(game={'loader.dll':dict(v),'unknown.lua':dict(v),'base.dat':dict(v)},
                           saves={'world':dict(v)})
        self.after = copy.deepcopy(self.before)
        del self.after['game']['loader.dll']
        self.plan = {'entries':[
            dict(root='game',relative_path='loader.dll',size=4,sha256='a'*64,proposed_action='QUARANTINE'),
            dict(root='game',relative_path='unknown.lua',size=4,sha256='a'*64,proposed_action='MANUAL_REVIEW'),
            dict(root='game',relative_path='base.dat',size=4,sha256='a'*64,proposed_action='STEAM_REPAIR'),
            dict(root='saves',relative_path='world',size=4,sha256='a'*64,proposed_action='KEEP')]}

    def test_exact_allowed_delta(self):
        result=verify_delta(self.plan,self.before,self.after)
        self.assertEqual(result['quarantined'],1)
        self.assertEqual(result['manual_review_unchanged'],1)
        self.assertEqual(result['local_files_unchanged'],1)

    def test_same_counts_wrong_file_removed(self):
        self.after['game']['loader.dll']=self.before['game']['loader.dll']
        del self.after['game']['unknown.lua']
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_additional_file_rejected(self):
        self.after['game']['new.dll']=dict(self.before['game']['loader.dll'])
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_protected_dat_hash_changed(self):
        self.after['game']['base.dat']['sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_timestamp_only_change_rejected(self):
        self.after['game']['unknown.lua']['mtime_ns']+=1
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_local_save_change_rejected(self):
        self.after['saves']['world']['sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_preflight_plan_mismatch_rejected(self):
        self.plan['entries'][0]['sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'BEFORE_DOES_NOT_MATCH'):
            verify_delta(self.plan,self.before,self.after)

    def test_missing_expected_removal(self):
        self.after['game']['loader.dll']=self.before['game']['loader.dll']
        with self.assertRaisesRegex(ValueError,'INTEGRITY_MISMATCH'):
            verify_delta(self.plan,self.before,self.after)


class KfcHeaderProof(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'index'

    def test_container_count_is_read_not_assumed(self):
        data=bytearray(100)
        data[:4]=b'KFC4'
        struct.pack_into('<II',data,16,16,7)
        struct.pack_into('<I',data,28,64)
        data[32:39]=b'1287369'
        self.path.write_bytes(data)
        self.assertEqual(kfc_header(self.path)['containers'],64)
        self.assertEqual(kfc_header(self.path)['version'],'1287369')

    def test_invalid_header_rejected(self):
        self.path.write_bytes(b'not an index')
        with self.assertRaisesRegex(ValueError,'INVALID'):
            kfc_header(self.path)

    def test_out_of_bounds_version_rejected(self):
        data=bytearray(32);data[:4]=b'KFC4'
        struct.pack_into('<II',data,16,4000,200)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'BOUNDS'):
            kfc_header(self.path)


if __name__ == '__main__':
    unittest.main()
