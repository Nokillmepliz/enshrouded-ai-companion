import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from companion.compatibility import file_hash
from companion.follow import run, FollowClient
from companion.shadow_integrity import record
from scripts import install_follow_033 as installer
from scripts.audit_follow_stage16_closed import short_snapshot

ROOT=Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_exact_payload_and_history_preserved(self):
        plan=json.loads((installer.PACKAGE/'exact-update-manifest.json').read_text())
        self.assertEqual(file_hash(installer.PACKAGE/'exact-update-manifest.json'),installer.MANIFEST_SHA)
        self.assertEqual(file_hash(ROOT/'compatibility/experiments/movement_0_3_3/exact-update-manifest.json'),installer.MANIFEST_SHA)
        self.assertEqual(len(plan['entries']),8)
        self.assertEqual(len(plan['effective_files']),40)
        self.assertEqual(plan['session']['seconds'],210)
        self.assertEqual(plan['backup_plan']['total'],28)
        history={r['path'] for r in plan['preserved_intents']}
        self.assertIn('runtime/stage10_16/test-session.jsonl',history)
        with tempfile.TemporaryDirectory() as td:
            game=Path(td);before={};fake=copy.deepcopy(plan)
            for row in fake['entries']:
                source=installer.PACKAGE/row['source']
                self.assertEqual(file_hash(source),row['sha256'])
                self.assertNotIn('stage10-16',row['path'])
                if row['source'].endswith(('.lua','.md','.json')):
                    self.assertEqual(source.read_bytes(),(ROOT/'dist/movement_0_3_3'/row['source']).read_bytes().replace(b'\r\n',b'\n'))
                if row['operation']=='replace':
                    p=game/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'old')
                    before[row['path']]=record(p);row['before_sha256']=before[row['path']]['sha256']
            installer.check_entries(fake,installer.PACKAGE,game,before)
            (game/'emf/mods/aic_companion_movement/wake.lua').write_bytes(b'foreign')
            with self.assertRaisesRegex(ValueError,'ADDITION_CONFLICT'):
                installer.check_entries(fake,installer.PACKAGE,game,before)

    def test_short_audit_rejects_changed_dat_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'enshrouded_000.dat';p.write_bytes(b'original')
            baseline={p.name:record(p)}
            self.assertEqual(short_snapshot(root,baseline),baseline)
            p.write_bytes(b'changed and longer')
            with self.assertRaisesRegex(ValueError,'DAT_METADATA_CHANGED'):
                short_snapshot(root,baseline)

    def test_runner_window_covers_180_after_maximum_wake_delay(self):
        class Client:
            version='0.3.3'
            def __init__(self):self.calls=[];self.stopped=False
            def context(self):pass
            def discover(self):return {'discovery':dict(result='FOUND_ONE',session='s',entity=42)}
            def _request(self,name,*args):
                self.calls.append(name)
                if name=='f_stop':self.stopped=True
                return dict(state='STOPPED' if self.stopped else 'MOVING',reason='',orders=1,
                            distance=5,cleanup='DONE' if self.stopped else 'NONE')
        with tempfile.TemporaryDirectory() as td:
            now=[0];client=Client();journal=Path(td)/'journal'
            def sleep(t):now[0]+=t
            result=run(client,journal,'new-token',clock=lambda:now[0],sleep=sleep)
            rows=[json.loads(s) for s in journal.read_text().splitlines()]
            stop=next(r['time'] for r in rows if r['kind']=='STOP_GRANT')
            self.assertGreaterEqual(stop-(15+8),180)
            self.assertLess(stop,210)
            self.assertEqual(client.calls.count('f_start'),1)
            self.assertEqual(client.calls.count('f_stop'),1)
            self.assertEqual(result['schedule_cleanup'],'CONFIRMED')
            with self.assertRaises(FileExistsError):run(client,journal,'new-token')
            self.assertEqual(client.calls.count('f_start'),1)

    def test_lua_duration_and_version_gate(self):
        from tests.test_companion_follow import FollowLuaTests
        fixture=FollowLuaTests();fixture.setUp()
        fixture.do("config.seconds=210;for t=101,280 do now=t;px=51;step() end")
        self.assertNotEqual(fixture.val('c.state'),'STOPPED')
        fixture.do('now=310;c.watch(w)')
        self.assertEqual(fixture.val('c.state'),'STOPPED')
        from tests.test_companion_movement import Transport
        t=Transport();c=FollowClient(t,version='0.3.3')
        with self.assertRaises(ValueError):c.discover()
        t.mods[-1]['version']='0.3.3';c.discover()


    def test_authorized_runner_uses_033_receipt_and_session(self):
        import sys
        import io
        from contextlib import redirect_stdout
        from scripts import follow_033 as runner, install_follow_033 as installer
        plan=json.loads((ROOT/'compatibility/experiments/movement_0_3_3/exact-update-manifest.json').read_text())
        with tempfile.TemporaryDirectory() as td:
            receipt=Path(td)
            (receipt/'receipt.json').write_text(json.dumps(dict(status='INSTALLED_READY_FOR_MANUAL_START',manifest_sha256=installer.MANIFEST_SHA)))
            with patch.object(sys,'argv',['runner','--pid','123','--manifest-sha256',installer.MANIFEST_SHA,'--authorized-session']), \
                 patch.object(installer,'RUN',receipt),patch.object(runner,'read_pinned',return_value=plan), \
                 patch.object(runner,'file_hash',return_value=plan['exe_sha256']),patch.object(runner,'preflight'), \
                 patch.object(runner,'connect',return_value=None),patch.object(runner,'FollowClient') as client, \
                 patch.object(runner,'run',return_value={}) as run,redirect_stdout(io.StringIO()):
                runner.main()
                client.assert_called_once_with(None,version='0.3.3')
                self.assertEqual(run.call_args.args[1],ROOT/'runtime/movement_0_3_3/test-session.jsonl')
                self.assertEqual(run.call_args.args[2],plan['token'])

if __name__=='__main__':unittest.main()
