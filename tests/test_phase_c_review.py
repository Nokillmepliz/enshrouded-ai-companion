import copy
import json
from pathlib import Path
import unittest
import tempfile
import zipfile

from companion.compatibility import file_hash
from scripts.prepare_integrated_components import verified_members

from companion.residual_cleanup import compare_inventory, propose, validate_proposal

ROOT = Path(__file__).resolve().parents[1]


class ResidualReviewTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / 'compatibility/recovery/1287369'
        self.review = json.loads((base / 'phase_b/residual-review.json').read_text(encoding='utf-8'))
        self.old = {'game': {e['relative_path']: {'sha256': e['sha256'], 'bytes': e['size'], 'mtime_ns': 1}
                             for e in self.review['files']}, 'saves': {'world': {'sha256': 'fixture', 'bytes': 1}}}
        self.identity = {'game_build': 1287369, 'steam_build_id': 'fixture'}

    def plan(self, current=None):
        return propose(self.review, self.old, current or self.old, self.identity, self.identity)

    def test_exact_scope_no_authorization(self):
        plan = self.plan()
        self.assertEqual(sum(e['proposed_action'] == 'PROPOSE_MOD_QUARANTINE' for e in plan['entries']), 30)
        self.assertEqual(sum(e['proposed_action'] == 'REQUEST_SEPARATE_BAK_HOLD' for e in plan['entries']), 1)
        self.assertEqual(sum(e['proposed_action'] == 'KEEP_UNCHANGED' for e in plan['entries']), 20)
        self.assertFalse(plan['authorization'])
        self.assertFalse(plan['execution_supported'])
        self.assertEqual(validate_proposal(plan, self.review, self.old, self.old, self.identity), plan)

    def test_changed_inventory_is_not_silently_rebased(self):
        for change in ('new', 'hash', 'mtime', 'local', 'missing'):
            with self.subTest(change=change):
                data = copy.deepcopy(self.old)
                path = next(iter(data['game']))
                if change == 'new': data['game']['unknown.dll'] = {'sha256': 'new'}
                elif change == 'hash': data['game'][path]['sha256'] = 'changed'
                elif change == 'mtime': data['game'][path]['mtime_ns'] = 2
                elif change == 'local': data['saves']['world']['bytes'] = 2
                else: del data['game'][path]
                with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
                    self.plan(data)

    def test_changed_steam_build(self):
        with self.assertRaisesRegex(ValueError, 'BUILD_CHANGED'):
            propose(self.review, self.old, self.old, {**self.identity, 'steam_build_id': 'new'}, self.identity)

    def test_forged_proposal_or_hash(self):
        plan = self.plan()
        plan['authorization'] = True
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_MISMATCH'):
            validate_proposal(plan, self.review, self.old, self.old, self.identity)
        self.review['files'][0]['sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'REVIEWED_HASH'):
            self.plan()

    def test_unknown_dat_never_becomes_mod(self):
        item = next(e for e in self.review['files'] if e['relative_path'].endswith('.dat'))
        item['category'] = 'CONFIG_REUSE_BLOCKER'
        with self.assertRaisesRegex(ValueError, 'PROTECTED_FILE'):
            self.plan()

    def test_post_steam_diff_preserves_all_categories(self):
        data = copy.deepcopy(self.old)
        removed = next(iter(data['game']))
        del data['game'][removed]
        changed = next(iter(data['game']))
        data['game'][changed]['sha256'] = 'new'
        data['game']['new-file'] = {'bytes': 1}
        delta = compare_inventory(self.old, data)
        self.assertEqual(delta['game']['ADDED'], ['new-file'])
        self.assertEqual(delta['game']['REMOVED'], [removed])
        self.assertEqual(delta['game']['CHANGED'], [changed])
        self.assertEqual(delta['saves']['UNCHANGED'], ['world'])


class ComponentStagingTests(unittest.TestCase):
    def test_digest_and_exact_member_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('game/required.dll', b'fixture data only')
                z.writestr('install.cmd', b'never extracted')
            with self.assertRaisesRegex(ValueError, 'DIGEST_MISMATCH'):
                verified_members(archive, '0' * 64, ['game/required.dll'])
            self.assertEqual(verified_members(archive, file_hash(archive), ['game/required.dll']),
                             {'game/required.dll': b'fixture data only'})

    def test_duplicate_archive_paths_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('game/required.dll', b'a')
                z.writestr('game/REQUIRED.dll', b'b')
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_ARCHIVE_ENTRY'):
                verified_members(archive, file_hash(archive), ['game/required.dll'])
