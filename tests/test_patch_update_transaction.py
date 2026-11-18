import os
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_patch_0_5_1 as fixtures
from companion.compatibility import file_hash
from companion.patch_update_transaction import verified_backup,verify_backup,replace_four,snapshot


class TransactionTests(unittest.TestCase):
    def setUp(self):
        fixtures.UpdateTests.setUp(self)
        for row in self.rows:
            s=(self.game/row['destination']).stat()
            row.update(current_bytes=s.st_size,current_mtime_ns=s.st_mtime_ns)
        self.bp={'files':[dict(group='game',path=r['destination'],sha256=r['current_sha256'],bytes=r['current_bytes']) for r in self.rows]}
        self.calls=0

    def live(self):self.calls+=1

    def backup_files(self):
        return verified_backup(self.bp,{'game':self.game},self.backup,live=self.live)

    def apply(self,authorized=True):
        return replace_four(self.plan,self.package,self.game,self.backup,self.root/'journal',authorized=authorized,live=self.live)

    def test_verified_backup_and_four_replacements(self):
        original=self.game/'original.dat';original.write_bytes(b'protected')
        shadow=self.game/'shadow.dat';os.link(original,shadow)
        protected=snapshot(self.game)
        bm=self.backup_files();verify_backup(self.backup,bm)
        done=self.apply();self.assertEqual(len(done),4)
        after=snapshot(self.game)
        self.assertEqual(protected['original.dat'],after['original.dat'])
        self.assertEqual(protected['shadow.dat'],after['shadow.dat'])
        for row in self.rows:self.assertEqual(file_hash(self.game/row['destination']),row['new_sha256'])
        self.assertEqual(len(list((self.root/'journal').glob('*-verified.json'))),4)
        self.assertFalse(list(self.game.rglob('*.tmp')))

    def test_no_authorization_no_write(self):
        with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):self.apply(False)
        self.assertFalse((self.root/'journal').exists())

    def test_bad_backup_source_stops_before_update(self):
        (self.game/self.rows[0]['destination']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):self.backup_files()
        self.assertFalse((self.backup/'manifest.json').exists())

    def test_partial_update_kept_without_rollback(self):
        self.backup_files();real=os.replace;calls=[]
        def fail_second(a,b):
            calls.append(str(b))
            if len(calls)==2:raise PermissionError('fixture denial')
            return real(a,b)
        with patch('companion.patch_update_transaction.os.replace',side_effect=fail_second):
            with self.assertRaises(PermissionError):self.apply()
        self.assertEqual(file_hash(self.game/self.rows[0]['destination']),self.rows[0]['new_sha256'])
        self.assertEqual(file_hash(self.game/self.rows[1]['destination']),self.rows[1]['current_sha256'])
        self.assertTrue((self.root/'journal/failure.json').exists())
        self.assertEqual(len(list(self.game.rglob('*.tmp'))),1)

    def test_changed_backup_stops(self):
        self.backup_files();(self.backup/'payload/game'/self.rows[0]['destination']).write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'BACKUP_CHANGED'):self.apply()
        self.assertEqual(file_hash(self.game/self.rows[0]['destination']),self.rows[0]['current_sha256'])

    def test_live_guard_stops(self):
        self.backup_files()
        self.live=lambda:(_ for _ in ()).throw(ValueError('GAME_RUNNING'))
        with self.assertRaisesRegex(ValueError,'GAME_RUNNING'):self.apply()
        self.assertFalse((self.root/'journal').exists())

    def test_hardlinked_destination_refused(self):
        self.backup_files();dst=self.game/self.rows[0]['destination'];os.link(dst,self.game/'extra')
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(file_hash(dst),self.rows[0]['current_sha256'])

    def make_38(self):
        self.bp['files']=[]
        for i in range(38):
            path=self.game/f'backup-{i}.bin';path.write_bytes(str(i).encode())
            self.bp['files'].append(dict(group='game',path=path.name,sha256=file_hash(path),bytes=path.stat().st_size))

    def test_invalid_38th_path_no_copy_or_directory(self):
        self.make_38();self.bp['files'][-1]['path']='bad\\receipt.json'
        with patch('companion.patch_update_transaction.shutil.copyfileobj') as copy:
            with self.assertRaises(ValueError):self.backup_files()
            copy.assert_not_called()
        self.assertFalse(self.backup.exists())

    def test_bad_38th_hash_no_copy_or_directory(self):
        self.make_38();self.bp['files'][-1]['sha256']='0'*64
        with patch('companion.patch_update_transaction.shutil.copyfileobj') as copy:
            with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):self.backup_files()
            copy.assert_not_called()
        self.assertFalse(self.backup.exists())

    def test_all_38_validated_and_copied(self):
        self.make_38();self.assertEqual(len(self.backup_files()['files']),38)

    def test_duplicate_casefold_before_copy(self):
        self.bp['files'].append(dict(self.bp['files'][0],path=self.bp['files'][0]['path'].upper()))
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.backup_files()
        self.assertFalse(self.backup.exists())

    def test_unknown_group_before_copy(self):
        self.bp['files'][-1]['group']='unknown'
        with self.assertRaisesRegex(ValueError,'UNKNOWN_BACKUP_GROUP'):self.backup_files()
        self.assertFalse(self.backup.exists())

    def test_wrong_total_before_copy(self):
        self.bp['payload_bytes']=0
        with self.assertRaisesRegex(ValueError,'TOTAL_MISMATCH'):self.backup_files()
        self.assertFalse(self.backup.exists())

    def test_partial_backup_cannot_resume(self):
        self.backup.mkdir();marker=self.backup/'existing';marker.write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError,'NEW_BACKUP_REQUIRED'):self.backup_files()
        self.assertEqual(marker.read_bytes(),b'preserve')

    def test_revision_2_preserves_payload_and_uses_posix(self):
        root=Path(__file__).resolve().parents[1];public=root/'compatibility/updates/1287369/0.5.1'
        old=json.loads((public/'backup-plan.json').read_text())
        new=json.loads((public/'backup-plan-revision-2.json').read_text())
        self.assertEqual(len(new['files']),38)
        self.assertEqual(new['payload_bytes'],old['payload_bytes'])
        for before,after in zip(old['files'],new['files']):
            self.assertEqual(dict(before,path=before['path'].replace('\\','/')),after)
        from pathlib import PureWindowsPath
        from companion.recovery import target
        for row in new['files']:
            target(self.root/'validation',row['group']+'/'+row['path'])
        self.assertEqual(new['files'][-1]['path'],PureWindowsPath(old['files'][-1]['path']).as_posix())
        source=(root/'scripts/prepare_patch_0_5_1.py').read_text()
        self.assertIn('parent.relative_to(ROOT).as_posix()',source)


if __name__=='__main__':unittest.main()
