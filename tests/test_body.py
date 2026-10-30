import json
from pathlib import Path
import unittest

# Import failure is deliberate if test prerequisites are missing: never silently skip Lua tests.
from lupa.lua54 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


class BodyRig:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute("package.path = ... .. '/?.lua;' .. package.path", (ROOT / "mods/aic_body").as_posix())
        self.lua.execute((ROOT / "tests/fake_emf.lua").read_text(encoding="utf-8"))
        self.reload()
        self.fake = self.lua.globals().fake

    def reload(self):
        self.lua.execute((ROOT / "mods/aic_body/main.lua").read_text(encoding="utf-8"))

    def command(self, name, *args):
        raw = self.lua.globals().fake.command(name, self.lua.table_from(args))
        assert raw.startswith("AIC_BODY ")
        return json.loads(raw[len("AIC_BODY "):])

    def status(self, rid=None):
        return self.command("status", *([rid] if rid else []))

    def request(self, action, rid="req1", identity="companion1", epoch=None):
        return self.command("request", rid, epoch or self.status()["state"]["epoch"], identity, action)

    def step(self, count=5):
        self.fake.step(count)

    def spawned(self):
        self.request("spawn")
        self.step()
        return self.status("req1")["state"]["entity_id"]


class BodyTests(unittest.TestCase):
    def setUp(self):
        self.rig = BodyRig()

    def test_load_and_status_never_spawn(self):
        self.rig.step(400)
        self.assertEqual(self.rig.status()["state"]["mode"], "absent")
        self.assertEqual(self.rig.fake.spawns, 0)

    def test_spawn_needs_observation_not_emit_return(self):
        r = self.rig.request("spawn")
        self.assertEqual(r["request"]["status"], "accepted")
        self.rig.step()
        r = self.rig.status("req1")
        self.assertEqual(r["request"]["status"], "succeeded")
        self.assertEqual(r["state"]["faction"], 11)
        self.assertEqual(r["state"]["guard_target"], 1)

    def test_missing_optional_spawn_time_does_not_block(self):
        entity = self.rig.spawned()
        self.assertIsNone(self.rig.fake.entities[entity].birth)
        self.assertEqual(self.rig.status("req1")["request"]["status"], "succeeded")

    def test_duplicate_request_and_different_id_cannot_duplicate_body(self):
        self.rig.spawned()
        self.assertEqual(self.rig.request("spawn")["request"]["status"], "succeeded")
        self.assertEqual(self.rig.request("spawn", "req2")["error"], "body_exists_or_cleanup_required")
        self.assertEqual(self.rig.fake.spawns, 1)

    def test_reusing_request_id_for_different_action_refused(self):
        self.rig.spawned()
        self.assertEqual(self.rig.request("stay")["error"], "request_id_conflict")

    def test_stay_marker_and_follow_cleanup(self):
        entity = self.rig.spawned()
        self.rig.request("stay", "stay1"); self.rig.step()
        state = self.rig.status("stay1")["state"]
        marker = state["marker_id"]
        self.assertEqual(state["guard_target"], marker)
        self.assertEqual(self.rig.status("stay1")["request"]["status"], "succeeded")
        self.rig.fake.entities[1].position.x = 25
        self.rig.request("follow", "follow1"); self.rig.step()
        self.assertEqual(self.rig.status("follow1")["request"]["status"], "accepted")
        # Simulated movement: a guard assignment alone must not be called successful.
        self.rig.fake.entities[entity].position.x = 23
        self.rig.step(7)
        self.assertEqual(self.rig.status("follow1")["request"]["status"], "succeeded")
        self.assertIsNone(self.rig.fake.entities[marker])

    def test_dismiss_waits_for_observed_removal(self):
        self.rig.spawned()
        self.rig.request("stay", "s"); self.rig.step()
        self.rig.fake.destroy_delayed = True
        self.rig.request("dismiss", "d"); self.rig.step()
        self.assertEqual(self.rig.status("d")["request"]["status"], "accepted")
        self.rig.fake.destroy_delayed = False
        self.rig.step()
        self.assertEqual(self.rig.status("d")["request"]["status"], "succeeded")
        self.assertEqual(self.rig.status()["state"]["mode"], "absent")
        self.assertIsNone(self.rig.fake.files["FAKE/runtime.lock"])

    def test_stale_session_never_touches_reused_entity(self):
        entity = self.rig.spawned()
        old = self.rig.status()["state"]["epoch"]
        self.rig.fake.session = "testrun-2"
        result = self.rig.request("dismiss", "d", epoch=old)
        self.assertEqual(result["error"], "stale_epoch")
        self.assertEqual(self.rig.fake.destroys, 0)
        self.assertIsNotNone(self.rig.fake.entities[entity])

    def test_same_session_reused_id_is_not_destroyed(self):
        entity = self.rig.spawned()
        self.rig.fake.entities[entity].model = "villager-model"
        self.rig.step()
        self.rig.request("dismiss", "d"); self.rig.step()
        self.assertEqual(self.rig.status("d")["request"]["code"], "identity_changed")
        self.assertEqual(self.rig.fake.destroys, 0)

    def test_hot_reload_blocks_all_mutations(self):
        self.rig.spawned(); old = self.rig.status()["state"]["epoch"]
        self.rig.reload()
        self.assertNotEqual(old, self.rig.status()["state"]["epoch"])
        self.assertTrue(self.rig.status()["state"]["recovery_required"])
        self.assertEqual(self.rig.request("spawn", "again")["error"], "recovery_required")
        self.assertEqual(self.rig.fake.spawns, 1)

    def test_dropped_event_times_out_without_false_success(self):
        self.rig.fake.drop_events = True
        self.rig.request("spawn"); self.rig.step(1802)
        self.assertEqual(self.rig.status("req1")["request"]["code"], "verification_timeout")

    def test_not_ready_cannot_succeed(self):
        self.rig.fake.not_ready = True
        self.rig.request("spawn"); self.rig.step()
        self.assertEqual(self.rig.status("req1")["request"]["status"], "accepted")

    def test_destroy_failure_is_reported(self):
        self.rig.spawned(); self.rig.fake.destroy_refused = True
        self.rig.request("dismiss", "d"); self.rig.step()
        self.assertEqual(self.rig.status("d")["request"]["code"], "destroy_refused")

    def test_profile_mismatch_refused(self):
        self.rig.spawned()
        self.assertEqual(self.rig.request("dismiss", "d", identity="other")["error"], "different_companion")

    def test_bad_tokens_rejected_without_spawn(self):
        self.assertEqual(self.rig.request("spawn", "id;destroy")["error"], "invalid_request")
        self.assertEqual(self.rig.fake.spawns, 0)

    def test_storage_failure_blocks_spawn(self):
        self.rig.fake.io_write_error = True
        r = self.rig.request("spawn")
        self.assertEqual(r["request"]["code"], "runtime_lock_write_failed")
        self.assertEqual(self.rig.fake.spawns, 0)

    def test_missing_model_keeps_untrusted_id_and_locks(self):
        self.rig.fake.no_model = True
        r = self.rig.request("spawn")
        self.assertEqual(r["request"]["status"], "failed")
        self.assertTrue(r["state"]["recovery_required"])
        self.assertEqual(self.rig.fake.destroys, 0)
        self.assertFalse(r['state']['body_trusted'])

    def test_missing_faction_keeps_handle_for_explicit_cleanup_without_guard(self):
        self.rig.fake.no_faction = True
        r = self.rig.request('spawn')
        self.assertTrue(r['state']['recovery_required'])
        self.assertEqual(self.rig.fake.destroys, 0)
        self.assertTrue(r['state']['body_trusted'])
        self.assertEqual(len(self.rig.fake.events), 0)
        self.rig.request('dismiss', 'cleanup'); self.rig.step(8)
        self.assertEqual(self.rig.status('cleanup')['request']['status'], 'succeeded')

    def test_full_cache_still_allows_cleanup(self):
        self.rig.spawned()
        for i in range(127):
            self.rig.request('follow', f'f{i}'); self.rig.step()
        self.assertEqual(self.rig.request('stay', 'over')['error'], 'request_capacity_restart_world')
        self.rig.request('dismiss', 'cleanup'); self.rig.step()
        self.assertEqual(self.rig.status('cleanup')['request']['status'], 'succeeded')

    def test_changed_spawn_time_detects_replacement_of_same_model(self):
        # Optional extra discriminator when this component exists on a build/template.
        self.rig.request('spawn')
        entity = self.rig.status()['state']['entity_id']
        self.rig.fake.entities[entity].birth = 777
        self.rig.request('dismiss', 'd'); self.rig.step()
        self.assertEqual(self.rig.status('d')['request']['code'], 'identity_changed')
        self.assertEqual(self.rig.fake.destroys, 0)

    def test_marker_failure_does_not_claim_stay(self):
        self.rig.spawned(); self.rig.fake.spawn_refused = True
        r = self.rig.request('stay', 's')
        self.assertEqual(r['request']['code'], 'marker_spawn_outcome_unknown')
        self.assertEqual(r['state']['mode'], 'recovery_required')

    def test_missing_marker_fails_instead_of_guarding_reused_id(self):
        self.rig.spawned(); self.rig.request('stay', 's')
        marker = self.rig.status()['state']['marker_id']
        self.rig.fake.entities[marker].model = 'some-other-object'
        self.rig.step()
        self.assertEqual(self.rig.status('s')['request']['code'], 'marker_identity_changed')

    def test_stay_revalidates_existing_marker_before_sending_event(self):
        self.rig.spawned(); self.rig.request('stay', 's'); self.rig.step()
        marker = self.rig.status()['state']['marker_id']
        self.rig.fake.entities[marker].model = 'replacement'
        r = self.rig.request('stay', 's2')
        self.assertEqual(r['request']['code'], 'marker_identity_changed')
        self.assertEqual(len(self.rig.fake.events), 0)

    def test_lost_body_cannot_receive_new_follow_orders(self):
        entity = self.rig.spawned()
        self.rig.fake.entities[entity].health = 0
        self.rig.step()
        self.rig.fake.entities[entity].health = 119
        self.assertEqual(self.rig.request('follow', 'f')['error'], 'cleanup_required')

    def test_enqueue_failure_is_reported(self):
        self.rig.fake.emit_error = True
        self.assertEqual(self.rig.request('spawn')['request']['code'], 'guard_enqueue_failed')

    def test_remote_world_cannot_mutate(self):
        self.rig.fake.server = False
        r = self.rig.command('request', 'id', 'epoch', 'companion1', 'spawn')
        self.assertEqual(r['error'], 'host_required')
        self.assertEqual(self.rig.fake.spawns, 0)

    def test_death_does_not_respawn_and_dismiss_can_remove_corpse(self):
        entity = self.rig.spawned()
        self.rig.fake.entities[entity].health = 0
        self.rig.fake.handlers["EntityDiedEvent"](self.rig.lua.globals().world,
                                                  self.rig.lua.table_from({"deadEntityId": entity}))
        self.rig.step()
        self.assertEqual(self.rig.status()["state"]["mode"], "lost")
        self.assertEqual(self.rig.fake.spawns, 1)
        self.rig.request("dismiss", "d"); self.rig.step()
        self.assertEqual(self.rig.status("d")["request"]["status"], "succeeded")

    def test_dismiss_cancels_pending_follow(self):
        self.rig.request("spawn")
        self.rig.request("dismiss", "d"); self.rig.step()
        self.assertEqual(self.rig.status("req1")["request"]["status"], "cancelled")
        self.assertEqual(self.rig.status("d")["request"]["status"], "succeeded")

    def test_chat_cannot_change_host_body(self):
        self.rig.fake.chat = True
        self.assertEqual(self.rig.request("spawn")["error"], "local_console_only")
        self.assertEqual(self.rig.fake.spawns, 0)

    def test_spawn_zero_is_unknown_and_later_spawn_refused(self):
        self.rig.fake.spawn_refused = True
        self.assertEqual(self.rig.request("spawn")["request"]["code"], "spawn_outcome_unknown")
        self.rig.fake.spawn_refused = False
        self.assertEqual(self.rig.request("spawn", "retry")['error'], 'recovery_required')
        self.assertIsNotNone(self.rig.fake.files['FAKE/runtime.lock'])

    def test_json_escapes_control_characters(self):
        encode = self.rig.lua.eval("require('json').encode")
        raw = encode(self.rig.lua.table_from({"text": 'строка\n"\\\0'}))
        self.assertEqual(json.loads(raw)["text"], 'строка\n"\\\0')


if __name__ == "__main__":
    unittest.main()
