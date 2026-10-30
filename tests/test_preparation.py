import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from companion.journal import Journal
from companion.client import BodyClient, ClientError
from scripts import backup
from tests.test_client import BridgeFake


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / 'source'
        self.source.mkdir()
        (self.source / 'save.bin').write_bytes(b'original save')
        self.destination = root / 'backups'
        self.config = {'destination': str(self.destination), 'sources': {
            'saves': {'path': str(self.source), 'required': True}}}

    def test_plan_does_not_copy_or_require_process_shutdown(self):
        with patch.object(backup, 'ensure_closed') as closed:
            _, entries, report = backup.prepare(self.config)
        closed.assert_not_called()
        self.assertFalse(self.destination.exists())
        self.assertEqual(report['files'], 1)
        self.assertEqual(report['bytes'], len(b'original save'))

    def test_verified_copy_and_source_unchanged(self):
        with patch.object(backup, 'ensure_closed') as closed:
            result = backup.execute(self.config)
        self.assertEqual(closed.call_count, 2)
        manifest = Path(result['manifest'])
        data = json.loads(manifest.read_text())
        self.assertTrue(data['verified'])
        self.assertEqual(backup.sha256(self.source / 'save.bin'), data['entries']['saves/save.bin']['sha256'])
        self.assertEqual((manifest.parent / 'saves/save.bin').read_bytes(), b'original save')
        self.assertEqual((self.source / 'save.bin').read_bytes(), b'original save')

    def test_overlap_and_missing_required_source_refused(self):
        with self.assertRaises(ValueError):
            backup.prepare(self.config | {'destination': str(self.source / 'backup')})
        (self.source / 'save.bin').unlink()
        with self.assertRaises(ValueError):
            backup.prepare(self.config)
        self.source.rmdir()
        with self.assertRaises(FileNotFoundError):
            backup.prepare(self.config)

    def test_active_process_prevents_creation(self):
        with patch.object(backup, 'ensure_closed', side_effect=RuntimeError('steam running')):
            with self.assertRaises(RuntimeError):
                backup.execute(self.config)
        self.assertFalse(self.destination.exists())

    def test_hash_mismatch_cannot_mark_backup_verified(self):
        with patch.object(backup, 'ensure_closed'), patch.object(backup, 'sha256', return_value='corrupt'):
            with self.assertRaises(RuntimeError):
                backup.execute(self.config)
        manifest, = self.destination.glob('*/manifest.json')
        self.assertFalse(json.loads(manifest.read_text())['verified'])


class JournalTests(unittest.TestCase):
    def test_disconnect_records_request_and_unknown_outcome_without_retry(self):
        bridge = BridgeFake()
        original = bridge.console
        def disconnected(line, **kwargs):
            response = original(line, **kwargs)
            if '.request' in line:
                raise OSError('disconnected after send')
            return response
        bridge.console = disconnected
        with tempfile.TemporaryDirectory() as tmp:
            journal = Journal(tmp)
            client = BodyClient(bridge, trace=journal.emit)
            with self.assertRaises(ClientError):
                client.execute('spawn', 'companion1', allow_mutations=True, request_id='log-test',
                               world_slot=1, character_slot=2, character_name='Body Test')
            journal.close()
            rows = [json.loads(line) for line in journal.path.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(bridge.rig.fake.spawns, 1)
        self.assertEqual(rows[-1]['event'], 'console_error')
        self.assertIn('log-test', rows[-1]['data']['command'])
        self.assertEqual(rows[-1]['data']['outcome'], 'unknown')
        self.assertTrue(all('utc' in row and 'run_id' in row for row in rows))

    def test_log_disk_failure_does_not_interrupt_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Journal(tmp)
            with patch.object(journal, '_write', side_effect=OSError('disk full')), contextlib.redirect_stderr(io.StringIO()) as err:
                journal.emit('console_received', {})
                journal.emit('completed', {})
            journal.close()
        self.assertTrue(journal.failed)
        self.assertIn('verification continues', err.getvalue())

    def test_lua_lifecycle_diagnostics_without_tick_spam(self):
        bridge = BridgeFake()
        client = BodyClient(bridge, clock=lambda: bridge.now, sleep=bridge.sleep)
        client.execute('spawn', 'companion1', allow_mutations=True, request_id='log-test',
                       world_slot=1, character_slot=2, character_name='Body Test')
        lines = list(bridge.rig.fake.log.values())
        self.assertTrue(any(line.startswith('AIC_STATE ') for line in lines))
        self.assertTrue(any(line.startswith('AIC_REQUEST ') for line in lines))
        count = len(lines)
        client.status()
        client.status()
        self.assertEqual(len(bridge.rig.fake.log), count)
