import dataclasses
from pathlib import Path
import unittest

from companion.safe_spawn import (
    Confidence, DestroyStatus, GateName, GateStatus, IdentityObservation,
    OwnedEntityIdentity, OwnedIdentityState, PersistenceEvidence,
    PersistenceStatus, PositionEvidence, PositionStatus, SafetyGate,
    SafetyGateAssessment, authorize_destroy, classify_owned_identity,
    classify_persistence, stage10_9_gate_assessment, validate_spawn_position,
    verify_destroy_result,
)
from companion.stage10_7 import evaluate as evaluate_v4
from companion.safe_spawn import offline_research_verdict

ROOT = Path(__file__).parents[1]


def owned(**changes):
    base = OwnedEntityIdentity(
        instance_token="tok", entity_id=42, entity_generation=7,
        template_guid="guid", session_identity="session", ownership_marker="tok",
        marker_attached_at_spawn=True, state=OwnedIdentityState.CONFIRMED,
        provenance=("mock_atomic_spawn",),
    )
    return dataclasses.replace(base, **changes)


def observation(**changes):
    base = IdentityObservation(42, 7, "guid", "session", "tok", 1, True)
    return dataclasses.replace(base, **changes)


def position(**changes):
    base = PositionEvidence("world", "world", True, True, True, True, True,
                            True, True, True, ("mock_query",))
    return dataclasses.replace(base, **changes)


def persistence(**changes):
    base = PersistenceEvidence(False, False, False, True, False, True, False,
                               ("mock_reload",))
    return dataclasses.replace(base, **changes)


class IdentityTests(unittest.TestCase):
    def test_01_generation_matches(self):
        self.assertEqual(classify_owned_identity(owned(), observation()), OwnedIdentityState.CONFIRMED)

    def test_02_generation_changed(self):
        self.assertEqual(classify_owned_identity(owned(), observation(entity_generation=8)), OwnedIdentityState.REUSED)

    def test_03_id_reused_with_template_change(self):
        self.assertEqual(classify_owned_identity(owned(), observation(template_guid="foreign")), OwnedIdentityState.REUSED)

    def test_04_session_changed(self):
        self.assertEqual(classify_owned_identity(owned(), observation(session_identity="next")), OwnedIdentityState.STALE)

    def test_05_marker_absent(self):
        self.assertEqual(classify_owned_identity(owned(), observation(ownership_marker=None)), OwnedIdentityState.AMBIGUOUS)

    def test_06_marker_forged(self):
        self.assertEqual(classify_owned_identity(owned(), observation(marker_integrity=False)), OwnedIdentityState.AMBIGUOUS)

    def test_07_ownership_unknown(self):
        self.assertFalse(owned(ownership_marker=None).permits_targeted_destroy)

    def test_08_multiple_candidates(self):
        self.assertEqual(classify_owned_identity(owned(), observation(candidates=2)), OwnedIdentityState.AMBIGUOUS)

    def test_09_missing_native_generation_is_not_faked(self):
        self.assertEqual(classify_owned_identity(owned(entity_generation=None), observation(entity_generation=None)),
                         OwnedIdentityState.AMBIGUOUS)

    def test_10_missing_entity_is_lost(self):
        self.assertEqual(classify_owned_identity(owned(), None), OwnedIdentityState.LOST)

    def test_11_different_entity_id_is_lost(self):
        self.assertEqual(classify_owned_identity(owned(), observation(entity_id=43)), OwnedIdentityState.LOST)

    def test_12_non_atomic_check_destroy_blocked(self):
        self.assertEqual(authorize_destroy(owned(), observation(), atomic_check_and_destroy=False).status,
                         DestroyStatus.BLOCKED)


class PositionTests(unittest.TestCase):
    def test_13_valid_surface(self):
        self.assertEqual(validate_spawn_position(position()).status, PositionStatus.VALID)

    def test_14_no_surface(self):
        self.assertEqual(validate_spawn_position(position(ground_hit=False)).status, PositionStatus.INVALID)

    def test_15_wall(self):
        self.assertEqual(validate_spawn_position(position(surface_normal_ok=False)).status, PositionStatus.INVALID)

    def test_16_cliff(self):
        self.assertEqual(validate_spawn_position(position(height_ok=False)).status, PositionStatus.INVALID)

    def test_17_unwalkable(self):
        self.assertEqual(validate_spawn_position(position(walkable=False)).status, PositionStatus.INVALID)

    def test_18_danger_zone(self):
        self.assertEqual(validate_spawn_position(position(danger_clear=False)).status, PositionStatus.INVALID)

    def test_19_unknown_world(self):
        self.assertEqual(validate_spawn_position(position(observed_world=None)).status, PositionStatus.INVALID)

    def test_20_collision_query_unavailable(self):
        self.assertEqual(validate_spawn_position(position(collision_clearance=None)).status, PositionStatus.UNKNOWN)

    def test_21_geometry_unknown(self):
        self.assertEqual(validate_spawn_position(position(surface_normal_ok=None)).status, PositionStatus.UNKNOWN)

    def test_22_area_unavailable(self):
        self.assertEqual(validate_spawn_position(position(area_available=False)).status, PositionStatus.INVALID)

    def test_23_enemy_distance_unknown(self):
        self.assertEqual(validate_spawn_position(position(safe_distance=None)).status, PositionStatus.UNKNOWN)

    def test_24_missing_provenance(self):
        self.assertEqual(validate_spawn_position(position(query_provenance=())).status, PositionStatus.UNKNOWN)


class PersistenceTests(unittest.TestCase):
    def test_25_force_save_present_without_runtime_is_unknown(self):
        p = persistence(force_save=True, runtime_provenance=(), absent_after_reload=None)
        self.assertEqual(classify_persistence(p), PersistenceStatus.UNKNOWN)

    def test_26_force_save_absent_without_runtime_is_unknown(self):
        p = persistence(force_save=False, runtime_provenance=(), absent_after_reload=None)
        self.assertEqual(classify_persistence(p), PersistenceStatus.UNKNOWN)

    def test_27_active_saved_present_without_runtime_is_unknown(self):
        p = persistence(active_npc_state_saved=True, runtime_provenance=(), absent_after_reload=None)
        self.assertEqual(classify_persistence(p), PersistenceStatus.UNKNOWN)

    def test_28_unique_npc_collision(self):
        self.assertEqual(classify_persistence(persistence(unique_npc_collision=True)), PersistenceStatus.CONFLICT)

    def test_29_reload_duplicate(self):
        self.assertEqual(classify_persistence(persistence(unique_npc_collision=True, absent_after_reload=False)),
                         PersistenceStatus.CONFLICT)

    def test_30_destroyed_entity_restored(self):
        self.assertEqual(classify_persistence(persistence(restored_after_destroy=True)), PersistenceStatus.CONFLICT)

    def test_31_persistence_unknown(self):
        self.assertEqual(classify_persistence(persistence(runtime_provenance=(), absent_after_reload=None)),
                         PersistenceStatus.UNKNOWN)

    def test_32_backup_missing_blocks_gate(self):
        a = stage10_9_gate_assessment().as_dict()
        self.assertFalse(a["spawn_ready"])
        self.assertIn("PERSISTENCE", a["blocking_gates"])

    def test_33_temporary_confirmed_only_by_reload_evidence(self):
        self.assertEqual(classify_persistence(persistence()), PersistenceStatus.TEMPORARY_CONFIRMED)

    def test_34_persistent_confirmed_only_by_reload_evidence(self):
        self.assertEqual(classify_persistence(persistence(absent_after_reload=False)),
                         PersistenceStatus.PERSISTENT_CONFIRMED)


class FactionAndGateTests(unittest.TestCase):
    def test_35_player_ally_template_does_not_confirm_runtime_gate(self):
        gate = stage10_9_gate_assessment().gates[GateName.FACTION]
        self.assertEqual(gate.status, GateStatus.UNKNOWN)

    def test_36_hostile_override_is_failed(self):
        gate = SafetyGate(GateName.FACTION, GateStatus.FAILED, "hostile_override",
                          ("mock",), confidence=Confidence.HIGH)
        self.assertIn(GateName.FACTION, SafetyGateAssessment({GateName.FACTION: gate}).blocking_gates)

    def test_37_dynamic_faction_mismatch_failed(self):
        gate = SafetyGate(GateName.FACTION, GateStatus.FAILED, "dynamic_mismatch",
                          ("mock",), confidence=Confidence.HIGH)
        self.assertFalse(gate.status is GateStatus.CONFIRMED)

    def test_38_combat_behavior_unknown_blocks(self):
        self.assertIn(GateName.FACTION, stage10_9_gate_assessment().blocking_gates)

    def test_39_not_applicable_requires_proof(self):
        gate = SafetyGate(GateName.FACTION, GateStatus.NOT_APPLICABLE, "none", ("mock",))
        self.assertFalse(gate.valid())

    def test_40_not_applicable_with_proof_is_valid(self):
        gate = SafetyGate(GateName.FACTION, GateStatus.NOT_APPLICABLE, "risk_absent",
                          ("mock",), risk_absence_proven=True)
        self.assertTrue(gate.valid())


class DestroyTests(unittest.TestCase):
    def test_41_exact_identity_atomic_authorized(self):
        self.assertEqual(authorize_destroy(owned(), observation(), atomic_check_and_destroy=True).status,
                         DestroyStatus.AUTHORIZED)

    def test_42_reused_entity_blocked(self):
        self.assertEqual(authorize_destroy(owned(), observation(entity_generation=8),
                                           atomic_check_and_destroy=True).status, DestroyStatus.BLOCKED)

    def test_43_foreign_entity_blocked(self):
        self.assertEqual(authorize_destroy(owned(), observation(ownership_marker="foreign"),
                                           atomic_check_and_destroy=True).status, DestroyStatus.BLOCKED)

    def test_44_destroy_true_entity_remains(self):
        self.assertEqual(verify_destroy_result(accepted=True, presence_by_tick=[True, True, True]).status,
                         DestroyStatus.REMAINS)

    def test_45_destroy_timeout(self):
        self.assertEqual(verify_destroy_result(accepted=True, presence_by_tick=[], timed_out=True).status,
                         DestroyStatus.TIMEOUT)

    def test_46_disappears_then_reappears(self):
        self.assertEqual(verify_destroy_result(accepted=True, presence_by_tick=[False, False, True]).status,
                         DestroyStatus.REAPPEARED)

    def test_47_crash_during_destroy(self):
        self.assertEqual(verify_destroy_result(accepted=None, presence_by_tick=[], crashed=True).status,
                         DestroyStatus.CRASHED)

    def test_48_stale_token_blocked(self):
        self.assertEqual(authorize_destroy(owned(), observation(session_identity="new"),
                                           atomic_check_and_destroy=True).status, DestroyStatus.BLOCKED)

    def test_49_three_absent_ticks_confirm_removal(self):
        self.assertEqual(verify_destroy_result(accepted=True, presence_by_tick=[False]*3).status,
                         DestroyStatus.REMOVED_CONFIRMED)

    def test_50_two_absent_ticks_are_insufficient(self):
        self.assertEqual(verify_destroy_result(accepted=True, presence_by_tick=[False]*2).status,
                         DestroyStatus.ACCEPTED_UNVERIFIED)


class RegressionTests(unittest.TestCase):
    def test_51_stage10_7_evaluator_remains_callable(self):
        self.assertTrue(callable(evaluate_v4))

    def test_52_stage10_8_remains_blocked(self):
        self.assertEqual(offline_research_verdict()["verdict"], "BLOCKED_FOR_SPAWN")

    def test_53_no_autospawn_or_game_mutation_in_python_module(self):
        source = (ROOT / "companion" / "safe_spawn.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("ctypes", source)

    def test_54_phase_a_all_mandatory_unknowns_block(self):
        result = stage10_9_gate_assessment().as_dict()
        self.assertFalse(result["spawn_ready"])
        self.assertEqual(set(result["gates"]), {name.value for name in GateName})


if __name__ == "__main__":
    unittest.main()
