import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from companion import residual_quarantine as q
from companion.compatibility import fingerprint
from companion.recovery import RecoveryError, measure

ROOT = Path(__file__).resolve().parents[1]


class ResidualQuarantineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.roots = {k: self.base / k for k in ('game', 'saves')}
        for p in self.roots.values():
            p.mkdir()
        self.backup = self.base / 'backup'
        self.old_quarantine = self.base / 'old-quarantine'
        self.old_quarantine.mkdir()
        self.old_marker = self.old_quarantine / 'preserve.txt'
        self.old_marker.write_bytes(b'prior quarantine fixture')
        self.dest = self.base / 'new-quarantine'
        self.proposal = json.loads((ROOT / 'compatibility/recovery/1287369/phase_c/residual-proposal.json').read_text())
        # Real reviewed names/scope, synthetic bytes. No game data in these tests.
        for e in self.proposal['entries']:
            p = self.roots['game'] / e['relative_path']
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(('synthetic:' + e['relative_path']).encode())
            e.update(measure(p))
        for n in ('enshrouded.exe', 'enshrouded.kfc', 'enshrouded.kfc_resources', 'enshrouded_000.dat'):
            (self.roots['game'] / n).write_bytes(('protected fixture:' + n).encode())
        (self.roots['saves'] / 'world').write_bytes(b'local fixture')
        shutil.copytree(self.roots['game'], self.backup / 'game')
        self.before = q.capture(self.roots)
        self.proposal['inventory_identity'] = fingerprint({g: self.before[g] for g in ('game', 'saves')})
        self.identity = self.proposal['game_identity']

    def live(self):
        return {'stopped': True, 'identity': self.identity}

    def run_move(self, **kwargs):
        return q.quarantine(self.proposal, self.roots, self.backup, self.old_quarantine,
                            self.dest, self.before, authorize_mods=True,
                            authorize_bak=True, live=kwargs.pop('live', self.live), **kwargs)

    def unchanged(self):
        now = q.capture(self.roots)
        self.assertEqual(now['game'], self.before['game'])
        self.assertEqual(now['saves'], self.before['saves'])

    def test_exact_31_and_bak_hold_without_restore(self):
        self.assertEqual(self.run_move(), 31)
        after = q.capture(self.roots)
        delta = q.verify_after(self.proposal, self.before, after)
        self.assertEqual(len(delta['game']['REMOVED']), 31)
        self.assertEqual(self.before['game']['enshrouded.kfc'], after['game']['enshrouded.kfc'])
        self.assertEqual(self.old_marker.read_bytes(), b'prior quarantine fixture')
        journal = [json.loads(line) for line in (self.dest / 'journal.jsonl').read_text().splitlines()]
        self.assertEqual(len(journal), 62)
        self.assertEqual([r['state'] for r in journal], ['COPIED_VERIFIED_SOURCE_PRESENT'] * 31 + ['QUARANTINED'] * 31)
        for e in q.selected(self.proposal):
            self.assertEqual(measure(self.dest / e['relative_path']), {'sha256': e['sha256'], 'size': e['size']})

    def test_requires_both_explicit_authorizations(self):
        for mods, bak in ((False, False), (True, False), (False, True)):
            with self.subTest(mods=mods, bak=bak), self.assertRaisesRegex(RecoveryError, 'AUTHORIZATIONS'):
                q.quarantine(self.proposal, self.roots, self.backup, self.old_quarantine,
                             self.dest, self.before, authorize_mods=mods, authorize_bak=bak, live=self.live)
        self.assertFalse(self.dest.exists())
        self.unchanged()

    def test_reviewed_inventory_change_blocks_before_copy(self):
        for group, name in (('game', 'unexpected.dll'), ('saves', 'world')):
            with self.subTest(group=group):
                current = copy.deepcopy(self.before)
                current[group][name] = {'sha256': 'changed', 'bytes': 2, 'mtime_ns': 2}
                with self.assertRaisesRegex(RecoveryError, 'INVENTORY_CHANGED'):
                    q.validate_before(self.proposal, self.roots, current, self.backup)
        self.assertFalse(self.dest.exists())

    def test_changed_source_or_corrupt_backup_refused(self):
        entry = q.selected(self.proposal)[0]
        for root in (self.roots['game'], self.backup / 'game'):
            with self.subTest(root=root):
                p = root / entry['relative_path']
                original = p.read_bytes()
                p.write_bytes(b'corrupt fixture')
                with self.assertRaisesRegex(RecoveryError, 'HASH_OR_SIZE'):
                    self.run_move()
                p.write_bytes(original)
        self.assertFalse(self.dest.exists())

    def test_protected_targets_cannot_be_mislabeled(self):
        mod = q.selected(self.proposal)[0]
        name = mod['relative_path']
        for replacement in ('enshrouded.kfc', 'enshrouded.exe', 'enshrouded_000.dat', 'emf/evil.dat', '../outside.lua'):
            with self.subTest(path=replacement):
                mod['relative_path'] = replacement
                with self.assertRaises(RecoveryError):
                    self.run_move()
        mod['relative_path'] = name
        bak = next(e for e in self.proposal['entries'] if e['proposed_action'] == 'REQUEST_SEPARATE_BAK_HOLD')
        bak['relative_path'] = 'other.kfc.bak'
        with self.assertRaisesRegex(RecoveryError, 'ONLY_EXACT_KFC_BAK'):
            self.run_move()
        self.assertFalse(self.dest.exists())

    def test_destination_overlap_and_reuse_refused(self):
        for dest in (self.roots['game'] / 'q', self.backup / 'q', self.old_quarantine / 'q', self.old_quarantine):
            with self.subTest(dest=dest):
                self.dest = dest
                with self.assertRaisesRegex(RecoveryError, 'OVERLAPS|EXISTS'):
                    self.run_move()
        self.unchanged()

    def test_all_copy_failures_leave_sources_intact(self):
        count, original = 0, shutil.copyfileobj
        def copy_then_fail(src, dst, length):
            nonlocal count
            count += 1
            if count == 12:
                raise OSError('fixture disk error')
            return original(src, dst, length)
        with patch.object(q.shutil, 'copyfileobj', side_effect=copy_then_fail), self.assertRaises(OSError):
            self.run_move()
        self.unchanged()
        self.assertNotIn('"QUARANTINED"', (self.dest / 'journal.jsonl').read_text())

    def test_unlink_failure_keeps_all_copies_and_partial_journal(self):
        original, count = Path.unlink, 0
        def fail_second(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                raise PermissionError('fixture access denial')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'unlink', fail_second), self.assertRaises(PermissionError):
            self.run_move()
        entries = q.selected(self.proposal)
        self.assertTrue(all((self.dest / e['relative_path']).is_file() for e in entries))
        self.assertFalse((self.roots['game'] / entries[0]['relative_path']).exists())
        self.assertTrue(all((self.roots['game'] / e['relative_path']).exists() for e in entries[1:]))
        journal = [json.loads(l) for l in (self.dest / 'journal.jsonl').read_text().splitlines()]
        self.assertEqual(sum(e['state'] == 'QUARANTINED' for e in journal), 1)
        with self.assertRaises(RecoveryError):
            self.run_move()  # No automatic retry/resume.

    def test_process_start_or_build_change_before_unlink(self):
        for change in ('process', 'build'):
            with self.subTest(change=change):
                self.dest = self.base / ('dest-' + change)
                count = 0
                def live():
                    nonlocal count
                    count += 1
                    value = self.live()
                    if count == 33:  # initial check +31 copies; first unlink guard
                        if change == 'process': value['stopped'] = False
                        else: value['identity'] = {'game_build': 999}
                    return value
                with self.assertRaisesRegex(RecoveryError, 'NOT_STOPPED|BUILD_CHANGED'):
                    self.run_move(live=live)
                self.unchanged()

    def test_hardlinked_target_refused(self):
        entry = q.selected(self.proposal)[0]
        os.link(self.roots['game'] / entry['relative_path'], self.base / 'linked')
        with self.assertRaisesRegex(RecoveryError, 'HARDLINK'):
            self.run_move()
        self.assertFalse(self.dest.exists())

    def test_post_audit_detects_protected_mutation_and_wrong_removed_set(self):
        self.run_move()
        valid = q.capture(self.roots)
        for change in ('local', 'dat', 'new', 'kept'):
            after = copy.deepcopy(valid)
            if change == 'local': after['saves']['world']['sha256'] = 'changed'
            elif change == 'dat': after['game']['enshrouded_000.dat']['sha256'] = 'changed'
            elif change == 'new': after['game']['extra.dll'] = {'sha256': 'extra'}
            else: del after['game']['enshrouded_local.json']
            with self.subTest(change=change), self.assertRaisesRegex(RecoveryError, 'INTEGRITY_MISMATCH'):
                q.verify_after(self.proposal, self.before, after)

    def test_duplicate_or_reclassified_keep_refused(self):
        original = copy.deepcopy(self.proposal)
        self.proposal['entries'].append(copy.deepcopy(self.proposal['entries'][0]))
        with self.assertRaisesRegex(RecoveryError, 'DUPLICATE'):
            self.run_move()
        self.proposal = original
        e = next(e for e in self.proposal['entries'] if e['proposed_action'] == 'KEEP_UNCHANGED')
        e['proposed_action'] = 'PROPOSE_MOD_QUARANTINE'
        with self.assertRaises(RecoveryError):
            self.run_move()
        self.assertFalse(self.dest.exists())
