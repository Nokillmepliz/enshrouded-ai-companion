import copy
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from companion.shadow_integrity import ShadowError, audit_shadow, capture_originals, contained
from companion.compatibility import file_hash


class ShadowTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.game = Path(tmp.name) / 'fixture-game'
        self.game.mkdir()
        for n in ('enshrouded.exe', 'enshrouded.kfc', 'enshrouded.kfc_resources', 'enshrouded_000.dat'):
            (self.game / n).write_bytes(('fixture:' + n).encode())
        self.baseline = capture_originals(self.game)
        self.shadow = self.game / 'emf/content/client'
        self.shadow.mkdir(parents=True)
        self.expected = {}
        for n in self.baseline:
            if n.endswith(('.exe', '.dat')):
                os.link(self.game / n, self.shadow / n)
                role = 'BASE_LINK'
            else:
                shutil.copyfile(self.game / n, self.shadow / n)
                role = 'PRIVATE_INDEX'
            self.expected[n] = {'role': role, 'sha256': file_hash(self.shadow / n)}
        self.add('enshrouded_001.dat', b'fixture-clone', 'GENERATED_DAT')
        self.add('mods/aic/mod.lua', b'fixture-only', 'MOD_COPY')
        self.add('.cache/types.json', b'{}', 'CACHE')
        self.add('shadow.txt', b'fixture-metadata', 'METADATA')

    def add(self, name, data, role):
        p = self.shadow / name
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_bytes(data)
        self.expected[name] = {'role': role, 'sha256': file_hash(p)}

    def audit(self):
        return audit_shadow(self.game, self.shadow, self.baseline, self.expected)

    def test_safe_private_copies_and_read_links(self):
        result = self.audit()
        self.assertEqual(result['filesystem_integrity'], 'PASS')
        self.assertEqual(result['writer_completion'], 'UNKNOWN')
        self.assertEqual(result['redirection'], 'UNKNOWN')
        self.assertEqual(result['runtime_status'], 'NOT_EXECUTED')
        self.assertFalse(result['spawn_ready'])

    def test_private_writer_does_not_mutate_original(self):
        name = 'enshrouded.kfc'
        (self.shadow / name).write_bytes(b'fixture-cloned-private-index')
        self.expected[name]['sha256'] = file_hash(self.shadow / name)
        self.assertEqual(self.audit()['filesystem_integrity'], 'PASS')
        self.assertEqual(file_hash(self.game / name), self.baseline[name]['sha256'])

    def test_write_through_dat_hardlink_is_critical(self):
        (self.shadow / 'enshrouded_000.dat').write_bytes(b'bad fixture writer')
        with self.assertRaisesRegex(ShadowError, 'ORIGINAL_MUTATION'):
            self.audit()

    def test_unexpected_original_mutation(self):
        (self.game / 'enshrouded.kfc_resources').write_bytes(b'unexpected change')
        with self.assertRaisesRegex(ShadowError, 'ORIGINAL_MUTATION'):
            self.audit()

    def test_index_hardlink_rejected_even_when_bytes_match(self):
        p = self.shadow / 'enshrouded.kfc'
        p.unlink()
        os.link(self.game / p.name, p)
        with self.assertRaisesRegex(ShadowError, 'LINK_COUNT'):
            self.audit()

    def test_private_link_to_external_file_rejected(self):
        p = self.shadow / 'enshrouded_001.dat'
        external = self.game.parent / 'external-fixture'
        os.link(p, external)
        with self.assertRaisesRegex(ShadowError, 'PRIVATE_FILE_IS_HARDLINK'):
            self.audit()

    def test_identity_not_only_equal_hash(self):
        p = self.shadow / 'enshrouded.exe'
        p.unlink()
        shutil.copyfile(self.game / p.name, p)
        with self.assertRaisesRegex(ShadowError, 'LINK_COUNT|IDENTITY_MISMATCH'):
            self.audit()

    def test_unlink_before_new_dat_write_preserves_original(self):
        p = self.shadow / 'enshrouded_001.dat'
        p.unlink()
        os.link(self.game / 'enshrouded_000.dat', p)
        p.unlink()  # Writer must remove the name BEFORE opening its new output.
        p.write_bytes(b'new-private-fixture')
        self.expected[p.name]['sha256'] = file_hash(p)
        self.assertEqual(self.audit()['filesystem_integrity'], 'PASS')

    def test_unknown_file_or_tmp_blocks_finalized_shadow(self):
        (self.shadow / 'unexpected.dll').write_bytes(b'fixture')
        with self.assertRaisesRegex(ShadowError, 'FILE_SET_MISMATCH'):
            self.audit()
        (self.shadow / 'unexpected.dll').unlink()
        self.add('pending.tmp', b'fixture', 'TEMPORARY')
        with self.assertRaisesRegex(ShadowError, 'TEMPORARY'):
            self.audit()

    def test_wrong_hash_and_missing_index(self):
        prior = copy.deepcopy(self.expected)
        self.expected['enshrouded.kfc']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ShadowError, 'HASH_MISMATCH'):
            self.audit()
        self.expected = prior
        del self.expected['enshrouded.kfc']
        with self.assertRaisesRegex(ShadowError, 'PRIVATE_INDEX_MISSING'):
            self.audit()

    def test_bak_cannot_be_trusted_clean_base(self):
        (self.game / 'enshrouded.kfc.bak').write_bytes(b'old fixture')
        with self.assertRaisesRegex(ShadowError, 'UNTRUSTED_BAK_BASE'):
            self.audit()

    def test_paths_roles_and_case_aliases(self):
        for name in ('../outside', '/outside', 'C:/outside', 'mods\\a', 'mods/a:stream', 'NUL', 'mods/a.', 'mods//a'):
            with self.subTest(path=name), self.assertRaises(ShadowError):
                contained(self.shadow, name)
        with self.assertRaisesRegex(ShadowError, 'INCORRECT_SHADOW_PATH'):
            audit_shadow(self.game, self.game / 'other', self.baseline, self.expected)
        self.expected['SHADOW.TXT'] = self.expected['shadow.txt']
        with self.assertRaisesRegex(ShadowError, 'INVALID_ALLOWLIST'):
            self.audit()

    def test_unknown_dat_set_requires_review(self):
        (self.game / 'enshrouded_055.dat').write_bytes(b'')
        with self.assertRaisesRegex(ShadowError, 'DAT_SET_REVIEW'):
            self.audit()

    def test_unreferenced_root_dat_stays_private_and_unchanged(self):
        # Steam leaves a zero-byte old DAT behind; clean KFC references only 000.
        name = 'enshrouded_001.dat'
        (self.game / name).write_bytes(b'')
        current = capture_originals(self.game)
        self.baseline[name] = current[name]
        result = audit_shadow(self.game, self.shadow, self.baseline, self.expected, base_dat_count=1)
        self.assertEqual(result['filesystem_integrity'], 'PASS')
        self.assertEqual(result['original_files'][name]['links'], 1)
        self.assertEqual((self.game / name).read_bytes(), b'')
        (self.shadow / name).unlink()
        os.link(self.game / name, self.shadow / name)
        with self.assertRaisesRegex(ShadowError, 'LINK_COUNT'):
            audit_shadow(self.game, self.shadow, self.baseline, self.expected, base_dat_count=1)

    def test_base_container_count_is_not_guessed_from_untrusted_values(self):
        for count in (True, 0, -1, 2, '1'):
            with self.subTest(count=count), self.assertRaisesRegex(ShadowError, 'COUNT'):
                audit_shadow(self.game, self.shadow, self.baseline, self.expected, base_dat_count=count)

    @unittest.skipUnless(os.name == 'nt', 'Windows junction check')
    def test_junction_in_shadow_is_rejected(self):
        outside = self.game.parent / 'outside'
        outside.mkdir()
        link = self.shadow / 'escape'
        # Fixture-only junction creation; remove the junction itself, never target.
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], check=True, capture_output=True)
        try:
            with self.assertRaisesRegex(ShadowError, 'REPARSE_POINT'):
                self.audit()
        finally:
            link.rmdir()
