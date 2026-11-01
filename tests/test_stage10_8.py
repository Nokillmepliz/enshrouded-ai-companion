import dataclasses
import json
from pathlib import Path
import unittest

from companion.safe_spawn import (
    ANIMATION_GRAPH, BUILD, CHARACTER, COMPONENT_COUNT, COMPONENT_FINGERPRINT,
    EVIDENCE_SECTIONS, FORMAT, RENDER_LEVELS, SLOT, TEMPLATE_FINGERPRINT,
    TEMPLATE_GUID, WORLD, GameEvidence, RuntimeCapabilities, SafeSpawnController,
    State, TemplateEvidence, evaluate_preflight, offline_research_verdict,
    public_evidence, validate_evidence_v5,
)
from companion.stage10_7 import evaluate as evaluate_v4

ROOT = Path(__file__).parents[1]
MOD = ROOT / "experimental" / "emf_safe_spawn"


def replace(value, **changes):
    return dataclasses.replace(value, **changes)


def report(game=None, template=None, capabilities=None):
    return evaluate_preflight(game or GameEvidence(), template or TemplateEvidence(),
                              capabilities or RuntimeCapabilities())


def evidence_v5():
    levels = {name: "UNKNOWN" for name in RENDER_LEVELS}
    return {"format": FORMAT, "run_token": "a" * 32, "build": BUILD,
            "template_guid": TEMPLATE_GUID, "template_fingerprint": TEMPLATE_FINGERPRINT,
            "sections": {
                "PRE_SPAWN": {"character_identity": "local-slot-1", "world_identity": "local-slot-1",
                    "spawn_api": "emf.spawn(world,guid,x,y,z)", "spawn_safety_verdict": "BLOCKED",
                    "faction_verification": "TEMPLATE_ONLY", "position_validation": "UNKNOWN",
                    "persistence_status": "UNKNOWN"},
                "SPAWN_RESULT": {"entity_handle": None, "entity_identity": "UNKNOWN",
                                 "failure_reason": "NOT_EXECUTED"},
                "RENDER_OBSERVATION": {"levels": levels},
                "DESPAWN_RESULT": {"despawn_api": "emf.destroy(world,entity_id)",
                    "despawn_verification": "NOT_EXECUTED", "recovery_status": "NOT_REQUIRED"},
                "POST_RUN_INTEGRITY": {"source_unchanged": None},
            }}


class Stage108RequiredScenarios(unittest.TestCase):
    def assert_blocked(self, result, key):
        self.assertFalse(result.spawn_ready)
        self.assertIn(key, result.blockers)
        self.assertEqual(result.state, State.LOCKED)

    def test_01_wrong_build(self):
        self.assert_blocked(report(game=replace(GameEvidence(), build=1)), "build")

    def test_02_wrong_character(self):
        self.assert_blocked(report(game=replace(GameEvidence(), character="Other")), "character")

    def test_03_wrong_world(self):
        self.assert_blocked(report(game=replace(GameEvidence(), world="Other")), "world")

    def test_04_multiplayer(self):
        self.assert_blocked(report(game=replace(GameEvidence(), multiplayer=True)), "local_context")

    def test_05_unknown_game_context(self):
        self.assert_blocked(report(game=replace(GameEvidence(), combat_active=None)), "combat_inactive")

    def test_06_wrong_guid(self):
        self.assert_blocked(report(template=replace(TemplateEvidence(), guid="bad")), "template_guid")

    def test_07_wrong_fingerprint(self):
        self.assert_blocked(report(template=replace(TemplateEvidence(), template_fingerprint="bad")),
                            "template_fingerprint")

    def test_08_template_lookup_failed(self):
        r = report(template=replace(TemplateEvidence(), lookup_confirmed=False))
        self.assert_blocked(r, "template_lookup")

    def test_09_hashkey32_mismatch(self):
        self.assert_blocked(report(template=replace(TemplateEvidence(), hashkey32_match=False)), "hashkey32")

    def test_10_faction_unconfirmed(self):
        c = replace(RuntimeCapabilities(), faction_in_template_before_spawn=False)
        self.assert_blocked(report(capabilities=c), "faction")

    def test_11_hostile_faction(self):
        t = replace(TemplateEvidence(), faction="Vukah", faction_value=3)
        self.assert_blocked(report(template=t), "faction")

    def test_12_despawn_api_missing(self):
        c = replace(RuntimeCapabilities(), despawn_method="UNAVAILABLE")
        self.assert_blocked(report(capabilities=c), "despawn_api")

    def test_13_ownership_unconfirmed(self):
        self.assert_blocked(report(), "ownership")

    def test_14_invalid_position(self):
        self.assert_blocked(report(), "safe_position")

    def test_15_unknown_geometry(self):
        c = replace(RuntimeCapabilities(), safe_position_prevalidated=False)
        self.assert_blocked(report(capabilities=c), "safe_position")

    def test_16_spawn_without_permission(self):
        c = SafeSpawnController(phase_a=False)
        c.state = State.READY_FOR_CONFIRMATION
        self.assertEqual(c.spawn_once(explicit_confirmation=False, run_token="a"*32)["state"], "LOCKED")

    def test_17_repeated_spawn(self):
        c = SafeSpawnController(phase_a=False); c.state = State.READY_FOR_CONFIRMATION; c.spawn_attempted = True
        self.assertEqual(c.spawn_once(explicit_confirmation=True, run_token="a"*32)["last_error"], "single_spawn_limit")

    def test_18_spawn_after_reconnect(self):
        c = SafeSpawnController(phase_a=False); c.state = State.READY_FOR_CONFIRMATION
        self.assertEqual(c.spawn_once(explicit_confirmation=True, run_token="a"*32, reconnect=True)["state"], "LOCKED")

    def test_19_spawn_after_reload(self):
        c = SafeSpawnController(phase_a=False); c.state = State.READY_FOR_CONFIRMATION
        self.assertEqual(c.spawn_once(explicit_confirmation=True, run_token="a"*32, reload=True)["state"], "LOCKED")

    def test_20_spawn_with_active_entity(self):
        c = SafeSpawnController(phase_a=False); c.state = State.READY_FOR_CONFIRMATION; c.entity_handle = 7
        self.assertEqual(c.spawn_once(explicit_confirmation=True, run_token="a"*32)["last_error"], "single_spawn_limit")

    def test_21_lost_entity_handle(self):
        c = SafeSpawnController(phase_a=False); c.state = State.ENTITY_ACTIVE
        self.assertEqual(c.despawn(handle=None, guid=TEMPLATE_GUID)["state"], "LOCKED")

    def test_22_wrong_entity_handle(self):
        c = SafeSpawnController(phase_a=False); c.state = State.ENTITY_ACTIVE; c.entity_handle = 8
        self.assertEqual(c.despawn(handle=9, guid=TEMPLATE_GUID)["last_error"], "entity_identity_not_confirmed")

    def test_23_wrong_guid_on_despawn(self):
        c = SafeSpawnController(phase_a=False); c.state = State.ENTITY_ACTIVE; c.entity_handle = 8; c.identity={"guid":TEMPLATE_GUID}
        self.assertEqual(c.despawn(handle=8, guid="bad")["state"], "LOCKED")

    def test_24_foreign_entity_despawn(self):
        c = SafeSpawnController(phase_a=False); c.state = State.ENTITY_ACTIVE; c.entity_handle = 8; c.identity={"guid":"foreign"}
        self.assertEqual(c.despawn(handle=8, guid=TEMPLATE_GUID)["state"], "LOCKED")

    def test_25_despawn_timeout(self):
        c = SafeSpawnController(phase_a=False); c.state = State.DESPAWN_REQUESTED
        self.assertEqual(c.emergency_stop()["last_error"], "recovery_required")

    def test_26_crash_before_despawn(self):
        c = SafeSpawnController(phase_a=False); c.state = State.ENTITY_ACTIVE; c.entity_handle=8
        self.assertEqual(c.on_reload()["last_error"], "reload_ownership_lost")

    def test_27_persistence_after_reload(self):
        self.assert_blocked(report(), "persistence")

    def test_28_observer_failure(self):
        self.assert_blocked(report(game=replace(GameEvidence(), observer_responding=False)), "observer")

    def test_29_bridge_disconnect(self):
        c = SafeSpawnController(); self.assertEqual(c.on_disconnect()["state"], "LOCKED")

    def test_30_stale_run_token(self):
        c = SafeSpawnController(phase_a=False); c.state=State.READY_FOR_CONFIRMATION
        self.assertEqual(c.spawn_once(explicit_confirmation=True, run_token="stale")["last_error"], "invalid_run_token")

    def test_31_invalid_receipt(self):
        self.assert_blocked(report(game=replace(GameEvidence(), receipt_valid=False)), "receipt")

    def test_32_backup_missing(self):
        self.assert_blocked(report(game=replace(GameEvidence(), backup_verified=False)), "backup")

    def test_33_unexpected_dat(self):
        self.assert_blocked(report(game=replace(GameEvidence(), dat_expected=False)), "dat")

    def test_34_unexpected_local_mutation(self):
        self.assert_blocked(report(game=replace(GameEvidence(), local_mutation_expected=False)), "local_integrity")

    def test_35_emergency_stop_mock_only(self):
        c = SafeSpawnController(); c.entity_handle=8
        s=c.emergency_stop(mock_removed=True); self.assertEqual(s["state"], "ENTITY_REMOVED"); self.assertIsNone(s["entity_handle"])

    def test_36_controller_lockout(self):
        c=SafeSpawnController(); c.spawn_once(explicit_confirmation=True,run_token="a"*32)
        self.assertEqual(c.state,State.LOCKED); self.assertFalse(c.status()["spawn_ready"])

    def test_37_no_automatic_retry(self):
        self.assertFalse(SafeSpawnController().status()["automatic_retry"])

    def test_38_no_auto_spawn(self):
        source=(MOD/"main.lua").read_text(encoding="utf-8")
        self.assertNotIn("on_load",source); self.assertNotIn("on_tick",source)

    def test_39_no_background_spawn(self):
        source=(MOD/"main.lua").read_text(encoding="utf-8")
        for item in ("emf.spawn", "emf.destroy", "emf.emit", "os.execute"):
            self.assertNotIn(item,source)

    def test_40_evidence_v5_validation(self):
        self.assertEqual(validate_evidence_v5(evidence_v5()),[])

    def test_41_render_unknown(self):
        levels=SafeSpawnController().inspect()["render_levels"]
        self.assertTrue(all(value=="UNKNOWN" for value in levels.values()))

    def test_42_partial_render(self):
        doc=evidence_v5(); doc["sections"]["RENDER_OBSERVATION"]["levels"]["MODEL_LOADED"]="CONFIRMED"
        self.assertEqual(doc["sections"]["RENDER_OBSERVATION"]["levels"]["RUNTIME_RENDER_CONFIRMED"],"UNKNOWN")

    def test_43_entity_exists_without_visible_model(self):
        doc=evidence_v5(); levels=doc["sections"]["RENDER_OBSERVATION"]["levels"]
        levels["ENTITY_CREATED"]="CONFIRMED"; self.assertEqual(levels["MODEL_LOADED"],"UNKNOWN")

    def test_44_successful_despawn_on_mock(self):
        c=SafeSpawnController(); c.entity_handle=44
        self.assertEqual(c.emergency_stop(mock_removed=True)["state"],"ENTITY_REMOVED")

    def test_45_recovery_required(self):
        c=SafeSpawnController(); self.assertEqual(c.emergency_stop()["last_error"],"recovery_required")

    def test_46_source_npc_unchanged(self):
        self.assert_blocked(report(template=replace(TemplateEvidence(),source_unchanged=False)),"source_unchanged")

    def test_47_no_hostile_template_fallback(self):
        source=(MOD/"main.lua").read_text(encoding="utf-8")
        self.assertNotIn("Enemy_Vukah",source); self.assertEqual(source.count(TEMPLATE_GUID),1)

    def test_48_stage10_7_regression(self):
        self.assertFalse(evaluate_v4(None)["spawn_ready"])
        self.assertEqual(COMPONENT_COUNT,81); self.assertEqual(COMPONENT_FINGERPRINT,"412d61b0")

    def test_49_full_contract_constants(self):
        self.assertEqual((BUILD,CHARACTER,WORLD,SLOT),(1273043,"Body Test","AI Body Test",1))
        self.assertEqual(ANIMATION_GRAPH,"402df515-5965-4b01-a17b-17d482a91af4")

    def test_50_phase_a_mutation_prohibition(self):
        c=SafeSpawnController()
        for result in (c.spawn_once(explicit_confirmation=True,run_token="a"*32),c.despawn(),c.emergency_stop()):
            self.assertEqual(result["state"],"LOCKED")
        manifest=json.loads((MOD/"mod.json").read_text(encoding="utf-8")); self.assertFalse(manifest["enabled"])


class Stage108AdditionalSafetyTests(unittest.TestCase):
    def test_offline_verdict_is_blocked(self):
        value=offline_research_verdict()
        self.assertEqual(value["verdict"],"BLOCKED_FOR_SPAWN")
        self.assertFalse(value["spawn_ready"])

    def test_public_evidence_redacts_runtime_identity(self):
        result=public_evidence(evidence_v5())
        self.assertNotIn("run_token",result)
        self.assertNotIn("character_identity",result["sections"]["PRE_SPAWN"])
        self.assertNotIn("entity_handle",result["sections"]["SPAWN_RESULT"])

    def test_missing_evidence_section_fails(self):
        value=evidence_v5(); del value["sections"][EVIDENCE_SECTIONS[0]]
        self.assertIn("section:PRE_SPAWN",validate_evidence_v5(value))

    def test_lua_source_compiles(self):
        from lupa import LuaRuntime
        result=LuaRuntime(unpack_returned_tuples=True).eval("load")((MOD/"main.lua").read_text(encoding="utf-8"),"main.lua")
        if isinstance(result,tuple): self.fail(result[1])
        self.assertTrue(callable(result))


if __name__ == "__main__":
    unittest.main()
