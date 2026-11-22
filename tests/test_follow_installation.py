import copy
from pathlib import Path
import tempfile
import unittest

from companion.compatibility import file_hash
from companion.shadow_integrity import record
from scripts.install_companion_follow import check_entries


class FollowInstallationTests(unittest.TestCase):
    def test_exact_package_and_conflicts_fail_before_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);game=root/'game';package=root/'package';package.mkdir()
            prefix='emf/mods/aic_companion_movement/'
            before={};rows=[]
            for name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua','follow-session.lock'):
                src=package/name;src.write_bytes(b'new')
                dest=game/prefix/name;dest.parent.mkdir(parents=True,exist_ok=True)
                old=name in ('main.lua','mod.json','README.md')
                if old: dest.write_bytes(b'old');before[prefix+name]=record(dest)
                rows.append(dict(path=prefix+name,source=name,operation='replace' if old else 'add',
                                 sha256=file_hash(src),bytes=3,before_sha256=file_hash(dest) if old else None))
            plan=dict(entries=rows)
            check_entries(plan,package,game,before)
            invalid=copy.deepcopy(plan);invalid['entries'][0]['path']='../foreign'
            with self.assertRaisesRegex(ValueError,'EXACT_SIX'):check_entries(invalid,package,game,before)
            (game/prefix/'follow-session.lock').write_bytes(b'SPENT!:existing')
            with self.assertRaisesRegex(ValueError,'ADDITION_CONFLICT'):check_entries(plan,package,game,before)
            self.assertEqual((game/prefix/'follow-session.lock').read_bytes(),b'SPENT!:existing')
            self.assertEqual((game/prefix/'main.lua').read_bytes(),b'old')

    def test_payload_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);package=root/'package';package.mkdir()
            (package/'main.lua').write_bytes(b'tampered')
            rows=[]
            for name in ('main.lua','mod.json','README.md','follow.lua','follow_config.lua','follow-session.lock'):
                rows.append(dict(path='emf/mods/aic_companion_movement/'+name,source=name,
                                 operation='replace' if name in ('main.lua','mod.json','README.md') else 'add',
                                 sha256='0'*64,bytes=3))
            with self.assertRaisesRegex(ValueError,'PAYLOAD_CHANGED'):
                check_entries(dict(entries=rows),package,root/'game',{})
            self.assertFalse((root/'game').exists())


if __name__=='__main__':unittest.main()
