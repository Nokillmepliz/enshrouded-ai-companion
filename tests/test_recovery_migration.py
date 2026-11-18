import copy
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from companion import recovery as r
from companion.compatibility import file_hash
from companion import migration_observer as obs


class RecoveryFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.roots = {k: self.base / k for k in ('game', 'saves')}
        for p in self.roots.values():
            p.mkdir()
        self.receipt = self.base / 'receipt.json'
        self.receipt.write_bytes(b'{"fixture":true}')
        files = {'game': {'enshrouded.exe': b'fake-executable', 'dinput8.dll': b'fake-loader',
                          'emf/test.lua': b'fake-mod', 'enshrouded_055.dat': b''},
                 'saves': {'test.save': b'world-state'}}
        self.identity = dict(game_build=1287369, exe_sha256='fixture', steam_build_id='fixture')
        self.plan = dict(format='aic_recovery_plan_v1', game_identity=self.identity,
                         roots={k: str(v) for k, v in self.roots.items()}, entries=[],
                         receipt_path=str(self.receipt), receipt_sha256=file_hash(self.receipt),
                         receipt_size=self.receipt.stat().st_size)
        for k, group in files.items():
            for name, raw in group.items():
                p = self.roots[k] / name
                p.parent.mkdir(exist_ok=True)
                p.write_bytes(raw)
                self.plan['entries'].append(dict(root=k, relative_path=name, absolute_path=str(p),
                    **r.measure(p), artifact_owner='EMF', confidence='HASH_CONFIRMED',
                    source_of_attribution='fixture archive SHA', backup_required=True,
                    proposed_action='QUARANTINE' if name in ('dinput8.dll', 'emf/test.lua') else 'KEEP'))
        self.backup = self.base / 'backup'
        self.dest = self.base / 'quarantine'

    def live(self):
        return dict(identity=self.identity, stopped=True, receipt_sha256=file_hash(self.receipt))

    def validate(self):
        r.validate_manifest(self.plan, self.roots, **self.live())

    def backup_now(self):
        return r.create_backup(self.plan, self.roots, self.backup, authorize=True, preflight=self.live)

    def test_valid_inventory(self):
        self.validate()

    def test_backup_round_trip_does_not_touch_source(self):
        before = {k: r.inventory(p) for k,p in self.roots.items()}
        self.backup_now()
        r.verify_backup(self.plan, self.backup)
        self.assertEqual(before, {k: r.inventory(p) for k,p in self.roots.items()})

    def test_quarantine_preserves_backup_saves_and_resources(self):
        self.backup_now()
        count = r.quarantine(self.plan, self.roots, self.backup, self.dest, authorize=True, preflight=self.live)
        self.assertEqual(count, 2)
        self.assertFalse((self.roots['game'] / 'dinput8.dll').exists())
        self.assertEqual((self.dest / 'dinput8.dll').read_bytes(), b'fake-loader')
        self.assertEqual((self.roots['saves'] / 'test.save').read_bytes(), b'world-state')
        self.assertTrue((self.roots['game'] / 'enshrouded_055.dat').is_file())
        r.verify_backup(self.plan, self.backup)

    def test_no_backup_without_authorization(self):
        with self.assertRaisesRegex(r.RecoveryError, 'NOT_AUTHORIZED'):
            r.create_backup(self.plan, self.roots, self.backup, preflight=self.live)
        self.assertFalse(self.backup.exists())

    def test_no_quarantine_without_authorization(self):
        with self.assertRaisesRegex(r.RecoveryError, 'NOT_AUTHORIZED'):
            r.quarantine(self.plan, self.roots, self.backup, self.dest, preflight=self.live)
        self.assertFalse(self.dest.exists())

    def test_unknown_added_file_blocks_all_changes(self):
        (self.roots['game'] / 'unknown.dll').write_bytes(b'x')
        with self.assertRaisesRegex(r.RecoveryError, 'INVENTORY_CHANGED'):
            self.validate()

    def test_hash_changed(self):
        (self.roots['game'] / 'dinput8.dll').write_bytes(b'edited')
        with self.assertRaisesRegex(r.RecoveryError, 'HASH_OR_SIZE'):
            self.validate()

    def test_missing_source(self):
        (self.roots['game'] / 'dinput8.dll').unlink()
        with self.assertRaises(FileNotFoundError):
            self.validate()

    def test_active_game_blocks_before_destination(self):
        live = {**self.live(), 'stopped': False}
        with self.assertRaisesRegex(r.RecoveryError, 'STOPPED'):
            r.create_backup(self.plan, self.roots, self.backup, authorize=True, preflight=lambda: live)
        self.assertFalse(self.backup.exists())

    def test_stale_receipt(self):
        self.receipt.write_bytes(b'new receipt')
        with self.assertRaisesRegex(r.RecoveryError, 'RECEIPT_MISMATCH'):
            self.validate()

    def test_cross_build(self):
        self.plan['game_identity'] = {**self.identity, 'game_build': 1273043}
        with self.assertRaisesRegex(r.RecoveryError, 'BUILD_MISMATCH'):
            self.validate()

    def test_backup_no_space(self):
        with patch.object(r.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 1})()):
            with self.assertRaisesRegex(r.RecoveryError, 'INSUFFICIENT_SPACE'):
                self.backup_now()
        self.assertFalse(self.backup.exists())

    def test_backup_corrupted(self):
        self.backup_now()
        (self.backup / 'game/dinput8.dll').write_bytes(b'broken')
        with self.assertRaisesRegex(r.RecoveryError, 'HASH_OR_SIZE'):
            r.quarantine(self.plan,self.roots,self.backup,self.dest,authorize=True,preflight=self.live)
        self.assertFalse(self.dest.exists())

    def test_backup_incomplete(self):
        self.backup_now()
        (self.backup / 'saves/test.save').unlink()
        with self.assertRaises(FileNotFoundError):
            r.verify_backup(self.plan,self.backup)

    def test_backup_wrong_restore_path(self):
        self.backup_now()
        data = json.loads((self.backup/'manifest.json').read_text())
        data['entries'][0]['absolute_path'] = str(self.base/'other')
        (self.backup/'manifest.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(r.RecoveryError, 'BACKUP_MANIFEST_MISMATCH'):
            r.verify_backup(self.plan,self.backup)

    def test_backup_from_other_build(self):
        self.backup_now()
        plan = copy.deepcopy(self.plan)
        plan['game_identity']['game_build'] = 1273043
        with self.assertRaisesRegex(r.RecoveryError, 'BACKUP_PLAN_MISMATCH'):
            r.verify_backup(plan,self.backup)

    def test_quarantine_destination_exists(self):
        self.backup_now()
        self.dest.mkdir()
        with self.assertRaisesRegex(r.RecoveryError, 'DESTINATION_EXISTS'):
            r.quarantine(self.plan,self.roots,self.backup,self.dest,authorize=True,preflight=self.live)

    def test_quarantine_inside_game(self):
        self.backup_now()
        with self.assertRaisesRegex(r.RecoveryError, 'OVERLAPS_SOURCE'):
            r.quarantine(self.plan,self.roots,self.backup,self.roots['game']/'q',authorize=True,preflight=self.live)

    def test_copy_failure_never_unlinks_source(self):
        self.backup_now()
        with patch.object(r.shutil, 'copyfileobj', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                r.quarantine(self.plan,self.roots,self.backup,self.dest,authorize=True,preflight=self.live)
        self.validate()

    def test_unlink_failure_keeps_verified_copy_and_journal(self):
        self.backup_now()
        with patch.object(Path, 'unlink', side_effect=PermissionError('fixture')):
            with self.assertRaises(PermissionError):
                r.quarantine(self.plan,self.roots,self.backup,self.dest,authorize=True,preflight=self.live)
        self.validate()
        self.assertIn('COPIED_VERIFIED_SOURCE_PRESENT', (self.dest/'journal.jsonl').read_text())
        self.assertNotIn('"QUARANTINED"', (self.dest/'journal.jsonl').read_text())

    def test_game_started_between_copy_and_unlink(self):
        self.backup_now()
        n = 0
        def changing():
            nonlocal n
            n += 1
            return {**self.live(), 'stopped': n == 1}
        with self.assertRaisesRegex(r.RecoveryError, 'STOPPED'):
            r.quarantine(self.plan,self.roots,self.backup,self.dest,authorize=True,preflight=changing)
        self.validate()

    def test_duplicate_case_alias(self):
        e = copy.deepcopy(self.plan['entries'][1]); e['relative_path']='DINPUT8.DLL'
        self.plan['entries'].append(e)
        with self.assertRaisesRegex(r.RecoveryError, 'INVALID_ENTRY'):
            self.validate()

    def test_hardlink_rejected(self):
        os.link(self.roots['game']/'dinput8.dll', self.base/'linked')
        with self.assertRaisesRegex(r.RecoveryError,'HARDLINK_REFUSED'):
            self.validate()

    @unittest.skipUnless(os.name == 'nt', 'Windows junction integration')
    def test_junction_escape_and_junction_root_refused(self):
        outside=self.base/'outside'; outside.mkdir()
        link=self.roots['game']/'junction'
        subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],check=True,capture_output=True)
        try:
            with self.assertRaisesRegex(r.RecoveryError,'REPARSE_POINT'):
                r.inventory(self.roots['game'])
            with self.assertRaisesRegex(r.RecoveryError,'REPARSE_POINT'):
                r.target(link,'file')
        finally:
            link.rmdir()  # removes only the temporary junction, never its target
        self.assertTrue(outside.is_dir())


def invalid_target_test(path):
    def test(self):
        with self.assertRaises(r.RecoveryError):
            r.target(self.roots['game'], path)
    return test


for i, path in enumerate(('../escape','/absolute','C:/other','emf/../../other','emf\\a','a//b',
                           'a/./b','file:stream','a./b','CON.txt','NUL','x/COM1.json')):
    setattr(RecoveryFixture, f'test_path_refusal_{i}', invalid_target_test(path))


def protected_test(index, mutate):
    def test(self):
        e = self.plan['entries'][index]
        e['proposed_action']='QUARANTINE'
        e.update(mutate)
        with self.assertRaisesRegex(r.RecoveryError,'UNKNOWN_OR_PROTECTED_TARGET'):
            self.validate()
    return test


for name, index, change in [('game_exe',0,{}), ('dat_collision',3,{}), ('saves',4,{}),
                            ('unknown_owner',1,{'artifact_owner':'UNKNOWN'}),
                            ('no_provenance',1,{'source_of_attribution':''}),
                            ('uncertain_hash',1,{'confidence':'PARTIAL'}),
                            ('no_backup',1,{'backup_required':False})]:
    setattr(RecoveryFixture, 'test_protected_'+name, protected_test(index,change))


class MigrationContracts(unittest.TestCase):
    def test_baseline_all_positive_without_depot_is_partial(self):
        e={k:dict(status='PASS',source='fixture') for k in r.BASELINE_KEYS}
        self.assertEqual(r.clean_baseline(e)['status'],'CLEAN_BASELINE_PARTIAL')
        e['independent_depot_hashes']=True
        result=r.clean_baseline(e)
        self.assertEqual(result['status'],'CLEAN_BASELINE_CONFIRMED')
        self.assertFalse(result['spawn_ready'])
        self.assertFalse(result['installation_ready'])

    def test_steam_success_alone_unknown(self):
        self.assertEqual(r.clean_baseline({'steam_verify':'success'})['status'],'CLEAN_BASELINE_UNKNOWN')

    def test_no_provenance_is_not_pass(self):
        self.assertEqual(r.clean_baseline({'build':{'status':'PASS'}})['status'],'CLEAN_BASELINE_UNKNOWN')

    def test_each_failed_baseline_gate(self):
        for key in r.BASELINE_KEYS:
            with self.subTest(key=key):
                self.assertEqual(r.clean_baseline({key:{'status':'FAIL'}})['status'],'CLEAN_BASELINE_FAILED')

    def test_content_owners_and_risks(self):
        good=dict(integrated=True,reflection_supported=True,evidence_available=True,shadow_path_valid=True,
                  private_indexes=True,dat_writer_unlinks_first=True)
        self.assertEqual(r.content_owner(good)['recommended_owner'],'integrated')
        for changes in ({'standalone':True},{'integrated':False},{'requires_export':True},
                        {'reflection_supported':False},{'evidence_available':False},{'shadow_path_valid':False},
                        {'private_indexes':False},{'dat_writer_unlinks_first':False}):
            with self.subTest(changes=changes), self.assertRaises(r.RecoveryError):
                r.content_owner({**good,**changes})
        self.assertEqual(r.content_owner(dict(standalone=True,reflection_supported=True,
                         evidence_available=True,export_available=True))['recommended_owner'],'standalone')

    def test_mutations_never_accepted(self):
        for command in ('spawn','destroy','move','teleport','set_faction','set_inventory','other','status;spawn'):
            self.assertEqual(obs.inspect(command,{}, {})['error'],'COMMAND_FORBIDDEN')

    def test_missing_context_has_diagnostic(self):
        self.assertEqual(obs.inspect('status',{}, {})['error'],'UNSUPPORTED_BUILD')

    def test_all_session_contracts_fail_closed(self):
        e=dict(build=1287369,api=46,emf='0.6.18',lua_host='1.39.0',protocol=1,
               session=9,world=1,content_owner='integrated',patch='0.5.0',receipt_sha256='x',run_token='y')
        for key in e:
            with self.subTest(key=key):
                result=obs.inspect('inspect',{**e,key:None},e)
                self.assertFalse(result['ok'])
                self.assertFalse(result['spawn_ready'])
        self.assertEqual(obs.inspect('compare',e,e)['error'],'MISSING_EVIDENCE')
        self.assertEqual(obs.inspect('compare',e,e,{'print':'done'})['error'],'WRITER_OR_READBACK_UNCONFIRMED')

    def frames(self):
        token='a'*32
        fields={k:'fixture' for k in obs.FIELDS}
        fields['count']=str(len(obs.FIELDS)-1)
        fields['hashkeys']=json.dumps({name:i for i,name in enumerate(sorted(obs.HASHKEYS))})
        return '\n'.join('prefix AIC_EVIDENCE_V8|'+token+'|'+k+'|'+v for k,v in fields.items())

    def test_complete_frames(self):
        self.assertEqual(len(obs.parse_frames(self.frames(),'a'*32)),len(obs.FIELDS))

    def test_truncated_frame_set(self):
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):
            obs.parse_frames('\n'.join(self.frames().splitlines()[:-1]),'a'*32)

    def test_stale_frame_set(self):
        with self.assertRaisesRegex(ValueError,'STALE'):
            obs.parse_frames(self.frames(),'b'*32)

    def test_duplicate_frame(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            obs.parse_frames(self.frames()+'\n'+self.frames().splitlines()[0],'a'*32)

    def test_hashkey_types(self):
        raw=self.frames().replace('"beard": 0','"beard": true')
        with self.assertRaisesRegex(ValueError,'HASHKEY32_TYPE'):
            obs.parse_frames(raw,'a'*32)

    def test_wrong_nine_hashkey_names(self):
        with self.assertRaisesRegex(ValueError,'HASHKEY32_COUNT'):
            obs.parse_frames(self.frames().replace('"beard":','"other":'),'a'*32)

    def test_duplicate_hashkey_json(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_HASHKEY32'):
            obs.parse_frames(self.frames().replace('"beard": 0','"beard": 1, "beard": 0'),'a'*32)

    def test_invalid_evidence_cannot_pass_with_writer_flags(self):
        e=dict(build=1287369,api=46,emf='0.6.18',lua_host='1.39.0',protocol=1,
               session=9,world=1,content_owner='integrated',patch='0.5.0',receipt_sha256='x',run_token='y')
        ctx={**e,'writer_finalized':True,'shadow_readback_verified':True}
        self.assertEqual(obs.inspect('compare',ctx,e,{'fake':'done'})['error'],'EVIDENCE_BASELINE_UNAVAILABLE')
        baseline=obs.parse_frames(self.frames(),'a'*32)
        e['evidence']=baseline
        self.assertEqual(obs.inspect('compare',ctx,e,{'fake':'done'})['error'],'EVIDENCE_MISMATCH')
        good=obs.inspect('compare',ctx,e,baseline)
        self.assertTrue(good['ok'])
        self.assertFalse(good['spawn_ready'])
        self.assertEqual(good['runtime_status'],'NOT_EXECUTED')


class ObserverLua(unittest.TestCase):
    def test_lua_offline_registration_has_only_three_readonly_commands(self):
        from lupa import LuaRuntime
        lua=LuaRuntime(unpack_returned_tuples=True)
        mod=lua.execute(Path('experimental/observer_next/observer.lua').read_text())
        registered={}
        api=lua.table_from({'command':lambda name,help,fn:registered.update({name:fn}),
                            'reply':lambda text:None})
        mod.register(api,lua.table_from({'encode':lambda x:'{}'}),lambda:None,lua.table())
        self.assertEqual(set(registered),{'status','inspect','compare'})
        for command in ('spawn','destroy','move','teleport','set_inventory','set_faction'):
            self.assertEqual(mod.inspect(command,lua.table(),lua.table(),None)['error'],'COMMAND_FORBIDDEN')

    def test_emitter_print_round_trip_and_incomplete_no_partial_output(self):
        from lupa import LuaRuntime
        lua=LuaRuntime(unpack_returned_tuples=True)
        mod=lua.execute(Path('experimental/eml_humanoid_next/evidence_log.lua').read_text())
        values={k:'fixture' for k in obs.FIELDS if k!='count'}
        values['hashkeys']=json.dumps({name:i for i,name in enumerate(sorted(obs.HASHKEYS))})
        lines=[]
        mod.emit(lines.append,'a'*32,lua.table_from(values))
        obs.parse_frames('\n'.join(lines),'a'*32)
        lines.clear();values['source_integrity']='bad\nvalue'
        with self.assertRaises(Exception):
            mod.emit(lines.append,'a'*32,lua.table_from(values))
        self.assertEqual(lines,[])


if __name__ == '__main__':
    unittest.main()
