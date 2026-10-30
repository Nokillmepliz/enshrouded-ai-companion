"""Fault injection against the actual Lua adapter; no native EMF or game process."""
import unittest
from pathlib import Path
import tempfile

from lupa.lua54 import LuaRuntime

from companion.client import BodyClient, ClientError
from tests.test_body import BodyRig, ROOT
from tests.test_client import BridgeFake

LOCK = 'FAKE/runtime.lock'


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.rig = BodyRig()
        self.fake = self.rig.fake

    def dismiss(self, rid='cleanup', ticks=10):
        result = self.rig.request('dismiss', rid)
        if 'error' not in result:
            self.rig.step(ticks)
            return self.rig.status(rid)
        return result

    def test_untrusted_body_never_deleted_or_promoted_by_later_fingerprint(self):
        self.fake.no_model = True
        result = self.rig.request('spawn')
        entity = result['state']['entity_id']
        self.fake.no_model = False
        result = self.dismiss()
        self.assertEqual(result['request']['code'], 'identity_unconfirmed')
        self.assertEqual(self.fake.destroys, 0)
        self.assertIsNotNone(self.fake.entities[entity])
        self.assertIsNotNone(self.fake.files[LOCK])
        self.assertEqual(self.rig.request('spawn', 'again')['error'], 'recovery_required')
        # Observation-only recovery is allowed if the unknown object disappears independently.
        self.fake.entities[entity] = None
        self.assertEqual(self.dismiss('observe-absence')['request']['status'], 'succeeded')
        self.assertEqual(self.fake.destroys, 0)
        self.assertIsNone(self.fake.files[LOCK])

    def test_zero_or_exception_after_spawn_preserves_uncertainty_and_lock(self):
        for failure in ('spawn_zero_after_create', 'spawn_throws_after_create'):
            with self.subTest(failure=failure):
                rig = BodyRig()
                rig.fake[failure] = True
                rig.request('spawn')
                state = rig.status()['state']
                self.assertTrue(state['uncertain_spawn'])
                self.assertEqual(state['recovery_action'], 'manual_world_restore')
                self.assertEqual(rig.request('dismiss', 'd')['error'], 'manual_world_restore_required')
                self.assertEqual(rig.request('spawn', 'again')['error'], 'recovery_required')
                rig.fake.session = 'another-session'
                rig.fake[failure] = False
                self.assertEqual(rig.request('spawn', 'new-session')['error'], 'recovery_required')
                self.assertEqual(rig.fake.spawns, 1)
                self.assertIsNotNone(rig.fake.entities[100])
                self.assertIsNotNone(rig.fake.files[LOCK])

    def test_exception_during_fingerprint_capture_keeps_untrusted_handle(self):
        self.fake.inspect_error = True
        self.assertEqual(self.rig.request('spawn')['error'], 'callback_error')
        state = self.rig.status()['state']
        self.assertEqual(state['entity_id'], 100)
        self.assertFalse(state['body_trusted'])
        self.assertEqual(state['observation_error'], 'inspect_failed')
        self.fake.inspect_error = False
        self.assertEqual(self.dismiss()['request']['code'], 'identity_unconfirmed')
        self.assertEqual(self.fake.destroys, 0)

    def test_faction_refusal_or_exception_keeps_trusted_body_for_cleanup(self):
        for failure in ('ally_refused', 'ally_error'):
            with self.subTest(failure=failure):
                rig = BodyRig()
                rig.fake[failure] = True
                rig.request('spawn')
                self.assertTrue(rig.status()['state']['body_trusted'])
                self.assertEqual(rig.fake.destroys, 0)
                self.assertEqual(len(rig.fake.events), 0)
                rig.request('dismiss', 'd'); rig.step(10)
                self.assertEqual(rig.status('d')['request']['status'], 'succeeded')
                self.assertIsNone(rig.fake.files[LOCK])

    def test_unknown_marker_does_not_prevent_cleanup_of_trusted_body(self):
        self.rig.spawned()
        self.fake.no_model = True
        # Existing body fingerprint must stay readable; only the newly spawned marker lacks it.
        self.rig.lua.execute("""
          local original = world.template
          function world:template(name, id)
            if id >= 101 then return nil end
            local old = fake.no_model; fake.no_model = false
            local result = original(self, name, id); fake.no_model = old; return result
          end
        """)
        result = self.rig.request('stay', 's')
        self.assertEqual(result['request']['code'], 'marker_fingerprint_missing')
        marker = result['state']['marker_id']
        result = self.dismiss()
        self.assertEqual(result['request']['code'], 'identity_unconfirmed')
        self.assertIsNone(self.fake.entities[100])
        self.assertIsNotNone(self.fake.entities[marker])
        self.assertEqual(self.fake.destroys, 1)
        self.fake.entities[marker] = None
        self.assertEqual(self.dismiss('resume')['request']['status'], 'succeeded')

    def test_destroy_false_is_not_proof_of_no_effect_and_is_not_replayed(self):
        self.rig.spawned()
        self.fake.destroy_refused = True
        result = self.dismiss()
        self.assertEqual(result['request']['code'], 'destroy_refused')
        count = self.fake.destroys
        self.fake.destroy_refused = False
        self.rig.step(20)
        self.assertEqual(self.fake.destroys, count)
        self.assertEqual(self.rig.request('dismiss', 'cleanup')['request']['status'], 'failed')
        self.assertEqual(self.fake.destroys, count)
        self.assertEqual(self.dismiss('resume')['request']['status'], 'accepted')
        self.assertEqual(self.fake.destroys, count)
        self.fake.entities[100] = None # late removal / disappearance, not a repeated destroy
        self.rig.step(10)
        self.assertEqual(self.rig.status('resume')['request']['status'], 'succeeded')

    def test_native_destroy_false_after_side_effect_can_finish_by_observation(self):
        self.rig.spawned()
        self.fake.destroy_false_after_accept = True
        result = self.dismiss()
        self.assertEqual(result['request']['code'], 'destroy_refused')
        self.assertEqual(result['state']['body_destroy_result'], 'refused_or_unknown')
        self.assertEqual(self.dismiss('resume')['request']['status'], 'succeeded')
        self.assertEqual(self.fake.destroys, 1)

    def test_accepted_destroy_timeout_can_resume_observation_without_resend(self):
        self.rig.spawned()
        self.rig.request('stay', 's'); self.rig.step()
        self.fake.destroy_delayed = True
        result = self.dismiss(ticks=1802)
        self.assertEqual(result['request']['code'], 'cleanup_timeout')
        self.assertTrue(result['state']['recovery_required'])
        self.assertEqual(self.fake.destroys, 2)
        self.assertIsNotNone(self.fake.files[LOCK])
        self.assertEqual(self.rig.request('spawn', 'again')['error'], 'recovery_required')
        self.rig.request('dismiss', 'resume'); self.rig.step(8)
        self.assertEqual(self.fake.destroys, 2)
        self.fake.destroy_delayed = False
        self.rig.step(8)
        self.assertEqual(self.rig.status('resume')['request']['status'], 'succeeded')
        self.assertEqual(self.fake.destroys, 2)
        self.assertIsNone(self.fake.files[LOCK])

    def test_throw_after_destroy_does_not_replay_it(self):
        self.rig.spawned()
        self.fake.destroy_throws_after_accept = True
        self.fake.destroy_delayed = True
        self.assertEqual(self.dismiss()['request']['code'], 'destroy_outcome_unknown')
        self.assertEqual(self.fake.destroys, 1)
        self.fake.destroy_throws_after_accept = False
        self.rig.request('dismiss', 'resume'); self.rig.step(8)
        self.assertEqual(self.fake.destroys, 1)
        self.fake.destroy_delayed = False
        self.rig.step(8)
        self.assertEqual(self.rig.status('resume')['request']['status'], 'succeeded')

    def test_partial_cleanup_never_reacquires_id_after_observed_absence(self):
        self.rig.spawned()
        self.rig.request('stay', 's'); self.rig.step()
        marker = self.rig.status()['state']['marker_id']
        self.fake.destroy_refused_id = marker
        self.dismiss()
        # Observe the disappeared body's ID over three callbacks while retrying cleanup.
        for i in range(3):
            self.dismiss('partial' + str(i))
        self.rig.lua.execute("fake.entities[100] = {position={x=2,y=0,z=0}, model='vukah-model', kind='enemy', health=119, faction=11, ready=true}")
        self.fake.entities[marker] = None # late removal, no replay of a failed native call
        count = self.fake.destroys
        self.assertEqual(self.dismiss('finish')['request']['status'], 'succeeded')
        self.assertEqual(self.fake.destroys, count)
        self.assertIsNotNone(self.fake.entities[100])

    def test_identity_mismatch_is_latched_even_if_model_changes_back(self):
        entity = self.rig.spawned()
        self.fake.entities[entity].model = 'foreign'
        self.assertTrue(self.rig.status()['state']['body_identity_invalidated'])
        self.fake.entities[entity].model = 'vukah-model'
        self.assertEqual(self.dismiss()['request']['code'], 'identity_changed')
        self.assertEqual(self.fake.destroys, 0)

    def test_one_absent_observation_then_same_id_reappears_cannot_be_deleted(self):
        entity = self.rig.spawned()
        old = self.fake.entities[entity]
        self.fake.entities[entity] = None
        self.rig.status()
        self.fake.entities[entity] = old
        self.assertEqual(self.dismiss()['request']['code'], 'identity_changed')
        self.assertEqual(self.fake.destroys, 0)

    def test_missing_position_is_not_absence(self):
        entity = self.rig.spawned()
        self.fake.position_missing = entity
        result = self.dismiss()
        self.assertEqual(result['request']['code'], 'entity_unreadable')
        self.assertEqual(self.fake.destroys, 0)
        self.assertIsNotNone(self.fake.files[LOCK])
        self.fake.position_missing = None
        self.assertEqual(self.dismiss('retry')['request']['status'], 'succeeded')

    def test_unavailable_entity_snapshot_cannot_prove_removal(self):
        for failure in ('entities_empty', 'entities_error'):
            with self.subTest(failure=failure):
                rig = BodyRig(); rig.spawned()
                rig.fake[failure] = True
                rig.request('dismiss', 'd'); rig.step(10)
                self.assertEqual(rig.status('d')['request']['status'], 'failed')
                self.assertIsNotNone(rig.fake.files[LOCK])
                rig.fake[failure] = False
                rig.request('dismiss', 'retry'); rig.step(10)
                self.assertEqual(rig.status('retry')['request']['status'], 'succeeded')

    def test_death_event_during_dismiss_does_not_cancel_cleanup(self):
        self.rig.spawned()
        self.rig.request('dismiss', 'd')
        self.fake.handlers['EntityDiedEvent'](self.rig.lua.globals().world,
                                            self.rig.lua.table_from({'deadEntityId': 100}))
        self.rig.step(10)
        self.assertEqual(self.rig.status('d')['request']['status'], 'succeeded')

    def test_stop_guard_enqueue_error_does_not_prevent_owned_cleanup(self):
        self.rig.spawned(); self.fake.emit_error = True
        result = self.dismiss()
        self.assertEqual(result['request']['event_submission'], 'enqueue_failed')
        self.assertEqual(result['request']['status'], 'succeeded')

    def test_command_evidence_never_claims_long_term_behavior(self):
        self.fake.drop_events = True
        result = self.rig.request('spawn')
        self.assertEqual(result['request']['phase'], 'event_queued')
        self.assertEqual(result['request']['status'], 'accepted')
        self.assertFalse(result['request']['state_confirmed'])
        self.rig.step(20)
        self.assertFalse(self.rig.status('req1')['request']['state_confirmed'])
        self.fake.drop_events = False
        self.rig.request('dismiss', 'd'); self.rig.step(10)
        self.assertTrue(self.rig.status('d')['request']['state_confirmed'])
        self.assertFalse(self.rig.status('d')['request']['behavior_verified'])

    def test_repeated_status_in_same_callback_does_not_confirm_absence(self):
        self.rig.spawned(); self.rig.request('dismiss', 'd')
        self.rig.step(3) # destroy requested, then one observation of absence
        for _ in range(10):
            self.assertEqual(self.rig.status('d')['request']['status'], 'accepted')
        self.assertIsNotNone(self.fake.files[LOCK])
        self.rig.step(2)
        self.assertEqual(self.rig.status('d')['request']['status'], 'succeeded')

    def test_stay_cannot_guard_marker_with_pending_destroy(self):
        self.rig.spawned(); self.rig.request('stay', 's'); self.rig.step()
        self.fake.destroy_delayed = True
        self.rig.request('follow', 'f'); self.rig.step(1802)
        self.assertEqual(self.rig.status('f')['request']['code'], 'verification_timeout')
        self.assertEqual(self.rig.request('stay', 's2')['error'], 'cleanup_required')
        self.assertEqual(self.fake.spawns, 2)


class RuntimeLockTests(unittest.TestCase):
    def test_actual_lua_io_write_flush_read_remove_and_reload_in_temp_directory(self):
        # Real Lua file operations, but fake EMF and only a disposable directory.
        with tempfile.TemporaryDirectory() as tmp:
            rig = BodyRig.__new__(BodyRig)
            rig.lua = LuaRuntime(unpack_returned_tuples=True)
            rig.lua.execute("package.path = ... .. '/?.lua;' .. package.path", (ROOT / 'mods/aic_body').as_posix())
            rig.lua.execute('saved_io=io; saved_remove=os.remove')
            rig.lua.execute((ROOT / 'tests/fake_emf.lua').read_text(encoding='utf-8'))
            rig.lua.execute('io=saved_io; os.remove=saved_remove; emf.dir=...', Path(tmp).as_posix())
            rig.fake = rig.lua.globals().fake
            rig.reload()
            rig.spawned()
            lock = Path(tmp) / 'runtime.lock'
            self.assertEqual(lock.read_text(), 'aic-body-lock-v2\n' + rig.status()['state']['epoch'] + '\n')
            rig.request('dismiss', 'd'); rig.step(10)
            self.assertEqual(rig.status('d')['request']['status'], 'succeeded')
            self.assertFalse(lock.exists())
            rig.request('spawn', 'again'); rig.step()
            before = lock.read_bytes()
            rig.reload()
            self.assertEqual(rig.request('spawn', 'reload')['error'], 'recovery_required')
            self.assertEqual(lock.read_bytes(), before)

    def test_read_error_or_malformed_or_legacy_lock_blocks_spawn(self):
        for content in ('', 'partial', 'old-session\n', 'aic-body-lock-v2\nforeign\n'):
            with self.subTest(content=content):
                rig = BodyRig(); rig.fake.files[LOCK] = content
                self.assertEqual(rig.request('spawn')['error'], 'recovery_required')
                self.assertEqual(rig.fake.spawns, 0)
                self.assertEqual(rig.fake.files[LOCK], content)
        rig = BodyRig(); rig.fake.io_read_error = True
        self.assertEqual(rig.request('spawn')['error'], 'recovery_required')
        self.assertEqual(rig.fake.spawns, 0)

    def test_write_flush_close_failures_never_spawn_or_erase_partial_lock(self):
        for failure in ('io_write_error', 'write_failed', 'flush_failed', 'close_failed'):
            with self.subTest(failure=failure):
                rig = BodyRig(); rig.status() # obtain session before injection
                rig.fake[failure] = True
                self.assertEqual(rig.request('spawn')['request']['code'], 'runtime_lock_write_failed')
                self.assertEqual(rig.fake.spawns, 0)
                self.assertEqual(rig.fake.remove_calls or 0, 0)
                rig.fake[failure] = False
                self.assertEqual(rig.request('spawn', 'again')['error'], 'recovery_required')

    def test_lock_appearing_between_status_and_spawn_is_not_overwritten(self):
        rig = BodyRig(); epoch = rig.status()['state']['epoch']
        rig.fake.files[LOCK] = 'someone-else'
        result = rig.request('spawn', epoch=epoch)
        self.assertEqual(result['request']['code'], 'runtime_lock_write_failed')
        self.assertEqual(rig.fake.files[LOCK], 'someone-else')
        self.assertEqual(rig.fake.spawns, 0)

    def test_remove_failure_then_explicit_retry_after_entities_are_gone(self):
        rig = BodyRig(); rig.spawned(); rig.fake.remove_failed = True
        rig.request('dismiss', 'd'); rig.step(10)
        self.assertEqual(rig.status('d')['request']['code'], 'runtime_lock_remove_failed')
        self.assertIsNotNone(rig.fake.files[LOCK])
        count = rig.fake.destroys
        rig.fake.remove_failed = False
        rig.request('dismiss', 'retry'); rig.step(10)
        self.assertEqual(rig.status('retry')['request']['status'], 'succeeded')
        self.assertEqual(rig.fake.destroys, count)

    def test_unreadable_changed_or_missing_lock_never_reports_success(self):
        for failure in ('unreadable', 'changed', 'missing', 'read_failed'):
            with self.subTest(failure=failure):
                rig = BodyRig(); rig.spawned()
                if failure == 'unreadable': rig.fake.io_read_error = True
                elif failure == 'read_failed': rig.fake.read_failed = True
                else: rig.fake.files[LOCK] = 'foreign' if failure == 'changed' else None
                rig.request('dismiss', 'd'); rig.step(10)
                self.assertEqual(rig.status('d')['request']['code'], 'runtime_lock_remove_failed')
                self.assertEqual(rig.fake.remove_calls or 0, 0)
                self.assertEqual(rig.request('spawn', 'again')['error'], 'recovery_required')

    def test_remove_success_requires_file_actually_absent(self):
        rig = BodyRig(); rig.spawned(); rig.fake.replace_after_remove = True
        rig.request('dismiss', 'd'); rig.step(10)
        self.assertEqual(rig.status('d')['request']['code'], 'runtime_lock_remove_failed')
        self.assertEqual(rig.fake.files[LOCK], 'foreign-lock')
        rig.request('dismiss', 'retry'); rig.step(10)
        self.assertEqual(rig.fake.remove_calls, 1)

    def test_reload_and_session_changes_never_use_previous_handles_or_clear_lock(self):
        rig = BodyRig(); rig.spawned()
        lock = rig.fake.files[LOCK]
        for operation in ('reload', 'new-world', 'new-process'):
            with self.subTest(operation=operation):
                if operation == 'reload': rig.reload()
                else: rig.fake.session = operation
                self.assertEqual(rig.request('dismiss', 'd')['error'], 'manual_world_restore_required')
                self.assertEqual(rig.request('spawn', 's')['error'], 'recovery_required')
                self.assertEqual(rig.fake.files[LOCK], lock)
                self.assertEqual(rig.fake.destroys, 0)

    def test_clean_dismiss_allows_new_session_and_new_personality(self):
        rig = BodyRig(); rig.spawned()
        rig.request('dismiss', 'd'); rig.step(10)
        self.assertIsNone(rig.fake.files[LOCK])
        rig.fake.session = 'clean-new-session'
        rig.request('spawn', 's', identity='new-personality'); rig.step(10)
        self.assertEqual(rig.status('s')['request']['status'], 'succeeded')


class ClientRecoveryTests(unittest.TestCase):
    def test_client_can_resume_dismiss_in_recovery_with_preflight(self):
        bridge = BridgeFake()
        client = BodyClient(bridge, clock=lambda: bridge.now, sleep=bridge.sleep)
        options = dict(allow_mutations=True, world_slot=1, character_slot=2, character_name='Body Test')
        bridge.rig.fake.no_faction = True
        with self.assertRaises(ClientError):
            client.execute('spawn', 'companion1', request_id='spawn', **options)
        bridge.state_data['world']['slot'] = 2
        with self.assertRaises(ClientError) as error:
            client.execute('dismiss', 'companion1', request_id='wrong-world', **options)
        self.assertEqual(error.exception.code, 'wrong_test_world')
        self.assertEqual(bridge.rig.fake.destroys, 0)
        bridge.state_data['world']['slot'] = 1
        result = client.execute('dismiss', 'companion1', request_id='cleanup', **options)
        self.assertEqual(result['request']['status'], 'succeeded')

    def test_old_adapter_revision_cannot_receive_mutations(self):
        bridge = BridgeFake()
        def mangle(response):
            import json
            data = json.loads(response['output'][0][9:])
            data['state'].pop('safety_revision', None)
            return response | {'output': ['AIC_BODY ' + json.dumps(data)]}
        bridge.mangle = mangle
        client = BodyClient(bridge)
        with self.assertRaises(ClientError) as error:
            client.execute('spawn', 'companion1', allow_mutations=True)
        self.assertEqual(error.exception.code, 'unsupported_adapter_safety_revision')
        self.assertEqual(bridge.rig.fake.spawns, 0)

    def test_success_without_state_evidence_is_rejected(self):
        bridge = BridgeFake()
        def mangle(response):
            import json
            data = json.loads(response['output'][0][9:])
            if data.get('request', {}).get('status') == 'succeeded':
                data['request']['state_confirmed'] = False
            return response | {'output': ['AIC_BODY ' + json.dumps(data)]}
        bridge.mangle = mangle
        client = BodyClient(bridge, clock=lambda: bridge.now, sleep=bridge.sleep)
        with self.assertRaises(ClientError) as error:
            client.execute('spawn', 'companion1', allow_mutations=True, world_slot=1,
                           character_slot=2, character_name='Body Test')
        self.assertEqual(error.exception.code, 'unconfirmed_command_result')
        self.assertEqual(bridge.rig.fake.spawns, 1)
