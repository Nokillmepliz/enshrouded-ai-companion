import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from companion import clean_backup as b
from companion.compatibility import fingerprint, file_hash


class CleanBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.roots = {k: root / k for k in ('game', 'saves')}
        self.baseline = {}
        for group, folder in self.roots.items():
            folder.mkdir(); self.baseline[group] = {}
            for name in b.GAME_PAYLOAD if group == 'game' else ('world0.ksd',):
                p = folder / name; p.write_bytes(b'fixture')
                self.baseline[group][name] = {'bytes': 7, 'sha256': file_hash(p)}
        self.accept = {'accepted': True, 'baseline_sha256': fingerprint(self.baseline)}
        self.dest = root / 'new-backup'

    def create(self, live=lambda: None):
        return b.create(self.dest, self.roots, self.baseline, self.accept, [], live=live)

    def test_roundtrip_and_corruption(self):
        self.assertEqual(self.create()['payload_bytes'], 35)
        b.verify(self.dest)
        (self.dest / 'game/enshrouded.exe').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'PAYLOAD_CHANGED'): b.verify(self.dest)
        self.assertEqual((self.roots['game'] / 'enshrouded.exe').read_bytes(), b'fixture')

    def test_no_acceptance_or_stale_source(self):
        self.accept['accepted'] = False
        with self.assertRaisesRegex(ValueError, 'ACCEPTANCE'): self.create()
        self.accept['accepted'] = True
        (self.roots['saves'] / 'world0.ksd').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHANGED'): self.create()
        self.assertFalse(self.dest.exists())

    def test_failure_preserves_partial_copy_and_never_resumes(self):
        with patch.object(b.shutil, 'copyfileobj', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): self.create()
        self.assertFalse((self.dest / 'manifest.json').exists())
        with self.assertRaisesRegex(ValueError, 'NEW_NONOVERLAPPING'): self.create()
        self.assertEqual((self.roots['game'] / 'enshrouded.exe').read_bytes(), b'fixture')

    def test_active_game_and_unknown_file(self):
        with self.assertRaisesRegex(ValueError, 'PROCESS'):
            self.create(lambda: (_ for _ in ()).throw(ValueError('PROCESS_RUNNING')))
        self.assertFalse(self.dest.exists())
        self.create(); (self.dest / 'unknown').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError, 'FILE_SET'): b.verify(self.dest)
