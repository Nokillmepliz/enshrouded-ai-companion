import copy
from pathlib import Path
import tempfile
import unittest

from companion.compatibility import file_hash
from companion.shadow_integrity import record
from scripts.install_follow_stage14 import check_entries


class Stage14InstallationTests(unittest.TestCase):
    def test_exact_package_and_conflicts_fail_before_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);game=root/'game';package=root/'package';package.mkdir()
            prefix='emf/mods/aic_companion_movement/'
            before={};rows=[]
            for name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua','follow-stage10-14.lock'):
                src=package/name;src.write_bytes(b'new')
                dest=game/prefix/name;dest.parent.mkdir(parents=True,exist_ok=True)
                old=name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua')
                if old: dest.write_bytes(b'old');before[prefix+name]=record(dest)
                rows.append(dict(path=prefix+name,source=name,operation='replace' if old else 'add',
                                 sha256=file_hash(src),bytes=3,before_sha256=file_hash(dest) if old else None))
            plan=dict(entries=rows)
            check_entries(plan,package,game,before)
            invalid=copy.deepcopy(plan);invalid['entries'][0]['path']='../foreign'
            with self.assertRaisesRegex(ValueError,'EXACT_SIX'):check_entries(invalid,package,game,before)
            (game/prefix/'follow-stage10-14.lock').write_bytes(b'SPENT!:existing')
            with self.assertRaisesRegex(ValueError,'ADDITION_CONFLICT'):check_entries(plan,package,game,before)
            self.assertEqual((game/prefix/'follow-stage10-14.lock').read_bytes(),b'SPENT!:existing')
            self.assertEqual((game/prefix/'main.lua').read_bytes(),b'old')

    def test_payload_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);package=root/'package';package.mkdir()
            (package/'main.lua').write_bytes(b'tampered')
            rows=[]
            for name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua','follow-stage10-14.lock'):
                rows.append(dict(path='emf/mods/aic_companion_movement/'+name,source=name,
                                 operation='replace' if name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua') else 'add',
                                 sha256='0'*64,bytes=3))
            with self.assertRaisesRegex(ValueError,'PAYLOAD_CHANGED'):
                check_entries(dict(entries=rows),package,root/'game',{})
            self.assertFalse((root/'game').exists())

    def test_pinned_historical_manifest_matches_receipt_and_preserves_old_lock(self):
        import json,hashlib
        from scripts.install_follow_stage14 import MANIFEST_SHA
        root=Path(__file__).resolve().parents[1]
        path=root/'compatibility/experiments/stage10_14/exact-update-manifest.json'
        self.assertEqual(file_hash(path),MANIFEST_SHA)
        plan=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(plan['session']['activation_horizontal'],20)
        self.assertEqual(plan['session']['deactivation_horizontal'],50)
        self.assertTrue(plan['session']['requires_separate_authorization'])
        self.assertEqual(len(plan['effective_files']),32)
        self.assertNotIn('emf/mods/aic_companion_movement/follow-session.lock',{r['path'] for r in plan['entries']})
        self.assertIn('runtime/stage10_13/test-session.jsonl',{r['path'] for r in plan['preserved_intents']})
        # 0.3.0 is historical; current source hashes are checked by Stage10.15 tests.
        receipt=json.loads((root/'compatibility/experiments/stage10_14/installation/receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['manifest_sha256'],MANIFEST_SHA)
        records={r['path']:r['record'] for r in receipt['installed_records']}
        self.assertEqual(set(records),{r['path'] for r in plan['entries']})
        for row in plan['entries']:
            self.assertEqual(records[row['path']]['sha256'],row['sha256'])
            self.assertEqual(records[row['path']]['size'],row['bytes'])
            if row['operation']=='add':
                self.assertEqual(hashlib.sha256(('UNUSED:'+plan['token']).encode()).hexdigest(),row['sha256'])
    def test_runner_requires_explicit_authorization_before_access(self):
        import sys
        from unittest.mock import patch
        from scripts import follow_stage14
        with patch.object(sys,'argv',['follow_stage14','--pid','1','--manifest-sha256','0'*64]),patch.object(follow_stage14,'connect') as connect:
            with self.assertRaises(SystemExit):follow_stage14.main()
            connect.assert_not_called()


if __name__=='__main__':unittest.main()
