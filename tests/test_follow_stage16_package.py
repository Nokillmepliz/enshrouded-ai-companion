import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_exact_seven_current_payload_and_preserved_stage15(self):
        from scripts.install_follow_stage16 import MANIFEST_SHA,check_entries
        from companion.shadow_integrity import record
        p=ROOT/'compatibility/experiments/stage10_16/exact-update-manifest.json'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),MANIFEST_SHA)
        plan=json.loads(p.read_text())
        self.assertEqual(plan['version'],'0.3.2')
        self.assertEqual(len(plan['effective_files']),37)
        self.assertEqual(plan['backup_plan']['total'],28)
        self.assertEqual(plan['session']['activation_horizontal'],20)
        self.assertEqual(plan['session']['deactivation_horizontal'],50)
        self.assertEqual(plan['session']['seconds'],180)
        paths={r['path'] for r in plan['entries']}
        self.assertEqual(len(paths),7)
        self.assertFalse(any('stage10-15' in n or n.endswith('schedule.lua') for n in paths))
        preserved={r['path'] for r in plan['preserved_intents']}
        self.assertIn('runtime/stage10_15/test-session.jsonl',preserved)
        self.assertIn('runtime/stage10_15/session507224/recovery-result.json',preserved)
        with tempfile.TemporaryDirectory() as td:
            package=Path(td)/'package';package.mkdir()
            game=Path(td)/'game';game.mkdir();before={};fake=copy.deepcopy(plan)
            for row in fake['entries']:
                n=row['source']
                data=(('UNUSED:'+plan['token']).encode() if n.endswith('.lock') else b'' if n.endswith('.jsonl')
                      else (ROOT/'dist/stage10_16_movement_0_3_2'/n).read_bytes())
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
                (package/n).write_bytes(data)
                if row['operation']=='replace':
                    dest=game/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b'previous')
                    before[row['path']]=record(dest);row['before_sha256']=before[row['path']]['sha256']
            check_entries(fake,package,game,before)
            conflict=game/'emf/mods/aic_companion_movement/follow-stage10-16.lock'
            conflict.write_bytes(b'SPENT!:preserve')
            with self.assertRaisesRegex(ValueError,'ADDITION_CONFLICT'):check_entries(fake,package,game,before)
            self.assertEqual(conflict.read_bytes(),b'SPENT!:preserve')
            bad=copy.deepcopy(fake);bad['entries'][0]['path']='emf/mods/aic_first_spawn/attempt.lock'
            with self.assertRaisesRegex(ValueError,'EXACT_SEVEN'):check_entries(bad,package,game,before)

    def test_runner_requires_new_authorization_and_version(self):
        import sys
        from scripts import follow_stage16
        from companion.follow import FollowClient
        from tests.test_companion_movement import Transport
        with patch.object(sys,'argv',['runner','--pid','1','--manifest-sha256','0'*64]),patch.object(follow_stage16,'connect') as connect:
            with self.assertRaises(SystemExit):follow_stage16.main()
            connect.assert_not_called()
        t=Transport();c=FollowClient(t,version='0.3.2')
        t.mods[-1]['version']='0.3.1'
        with self.assertRaises(ValueError):c.discover()
        t.mods[-1]['version']='0.3.2';c.discover()

    def test_authorized_runner_uses_stage16_receipt_and_session(self):
        import sys
        import io
        from contextlib import redirect_stdout
        from scripts import follow_stage16 as runner, install_follow_stage16 as installer
        plan=json.loads((ROOT/'compatibility/experiments/stage10_16/exact-update-manifest.json').read_text())
        with tempfile.TemporaryDirectory() as td:
            receipt=Path(td)
            (receipt/'receipt.json').write_text(json.dumps(dict(status='INSTALLED_READY_FOR_MANUAL_START',manifest_sha256=installer.MANIFEST_SHA)))
            with patch.object(sys,'argv',['runner','--pid','123','--manifest-sha256',installer.MANIFEST_SHA,'--authorized-session']), \
                 patch.object(installer,'RUN',receipt),patch.object(runner,'read_pinned',return_value=plan), \
                 patch.object(runner,'file_hash',return_value=plan['exe_sha256']),patch.object(runner,'preflight'), \
                 patch.object(runner,'connect',return_value=None),patch.object(runner,'FollowClient') as client, \
                 patch.object(runner,'run',return_value={}) as run,redirect_stdout(io.StringIO()):
                runner.main()
                client.assert_called_once_with(None,version='0.3.2')
                self.assertEqual(run.call_args.args[1],ROOT/'runtime/stage10_16/test-session.jsonl')
                self.assertEqual(run.call_args.args[2],plan['token'])


if __name__=='__main__':unittest.main()
