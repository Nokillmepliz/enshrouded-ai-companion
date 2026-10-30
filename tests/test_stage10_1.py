import contextlib
import io
import json
import unittest

from companion.stage10 import (
    DIRECT_LOOKUP_STATUS, EXPECTED_BUILD, EXPECTED_PATCH_VERSION,
    EXPECTED_SOURCE_GUID, EXPECTED_TEMPLATE_GUID, evaluate_load_only,
)
from scripts.stage10 import main as stage10_main


TOKEN = "0123456789abcdef0123456789abcdef"


def artifacts():
    evidence = "\n".join((
        "format=aic_eml_humanoid_evidence_v1",
        f"patch_version={EXPECTED_PATCH_VERSION}",
        f"run_token={TOKEN}",
        f"template_guid={EXPECTED_TEMPLATE_GUID}",
        f"source_guid={EXPECTED_SOURCE_GUID}",
        "template_name=AIC_Humanoid_Companion_Experimental",
        "npc_id=2939921867",
        "faction=PlayerAlly",
        "source_faction=Vukah",
        "model_guid=human-model",
        "source_model_guid=human-model",
        "animation_graph_guid=human-graph",
        "source_animation_graph_guid=human-graph",
        "components=A,B",
        "source_components=A,B",
        "component_clone=true",
        "source_unchanged=true",
        "resource_lookup_after_create=true",
        "source_registered=true",
        "registry_added=true",
        "serialization_status=pending_writer_finalize",
    )) + "\n"
    reply = {
        "loaded": True, "read_only": True, "spawn_forbidden": True,
        "run_token": TOKEN, "direct_emf_template_lookup": DIRECT_LOOKUP_STATUS,
    }
    return {
        "eml_log": (
            "INFO Running mod mod_id=aic_eml_humanoid\n"
            f"AIC_EML_TEMPLATE_READY {TOKEN} {EXPECTED_TEMPLATE_GUID} "
            "2939921867 human-model human-graph true\n"
            "INFO Applied 1 patches\n"
        ),
        "evidence_text": evidence,
        "emf_log": (
            "emf_core 0.3.2 known build 1273043 Lua host 1.9.0\n"
            f"AIC_TEMPLATE_OBSERVER_READY {TOKEN}; read-only commands\n"
        ),
        "observer_results": {"responses": {
            "status": {
                **reply, "command": "status", "evidence_run_token": TOKEN,
                "new_template_eml_evidence": True,
                "original_template_eml_evidence": True,
            },
            "inspect": {**reply, "command": "inspect", "field_source": "EML_EXPORT"},
            "compare": {**reply, "command": "compare", "checks": {
                "evidence_present": True, "run_token": True, "format": True,
                "template_guid": True, "source_guid": True, "npc_id": True,
                "faction": True, "model_available": True,
                "model_matches_source": True, "animation_graph_available": True,
                "animation_graph_matches_source": True, "component_clone": True,
                "source_unchanged": True, "resource_lookup_after_create": True,
                "registry_consistent": True, "writer_finalization_confirmed": False,
            }},
        }},
        "bridge_diagnostics": {
            "run_token": TOKEN, "connected": True, "diagnose_ok": True,
            "status_ok": True, "emf_version": "0.3.2", "api": 20,
            "game_build": EXPECTED_BUILD, "errors": [],
        },
        "game_load_report": {
            "run_token": TOKEN, "game_build": EXPECTED_BUILD,
            "main_menu_reached": True, "local_test_world_loaded": True,
            "resource_errors": [], "game_errors": [],
        },
        "backup_verified": True,
        "integrity_report": {
            "run_token": TOKEN, "unknown_changes": [],
            "kfc_changes_reviewed": True, "dat_changes_reviewed": True,
            "save_integrity_verified": True, "non_target_saves_unchanged": True,
            "rollback_ready": True,
        },
        "install_receipt": {
            "state": "complete", "run_token": TOKEN,
            "game_build": EXPECTED_BUILD, "patch_version": EXPECTED_PATCH_VERSION,
        },
    }


class Stage101AcceptanceTests(unittest.TestCase):
    def evaluate(self, **changes):
        values = artifacts()
        values.update(changes)
        return evaluate_load_only(**values)

    def test_all_three_levels_produce_load_only_success_without_spawn_permission(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "LOAD_ONLY_SUCCESS")
        self.assertTrue(result["eml_patch_applied"])
        self.assertTrue(result["game_load_confirmed"])
        self.assertTrue(result["emf_runtime_confirmed"])
        self.assertTrue(result["load_only_success"])
        self.assertFalse(result["spawn_ready"])

    def test_missing_writer_finalization_fails_level_a(self):
        value = artifacts()
        value["eml_log"] = value["eml_log"].replace("INFO Applied 1 patches\n", "")
        result = evaluate_load_only(**value)
        self.assertFalse(result["eml_patch_applied"])
        self.assertEqual(result["status"], "FAILED")

    def test_stale_evidence_from_another_run_is_rejected(self):
        value = artifacts()
        value["evidence_text"] = value["evidence_text"].replace(TOKEN, "f" * 32)
        self.assertFalse(evaluate_load_only(**value)["eml_patch_applied"])

    def test_wrong_template_guid_is_rejected(self):
        value = artifacts()
        value["evidence_text"] = value["evidence_text"].replace(
            EXPECTED_TEMPLATE_GUID, "ffffffff-ffff-4fff-8fff-ffffffffffff")
        self.assertFalse(evaluate_load_only(**value)["eml_patch_applied"])

    def test_wrong_npc_id_is_rejected(self):
        value = artifacts()
        value["evidence_text"] = value["evidence_text"].replace(
            "npc_id=2939921867", "npc_id=1")
        self.assertFalse(evaluate_load_only(**value)["eml_patch_applied"])

    def test_wrong_faction_is_rejected(self):
        value = artifacts()
        value["evidence_text"] = value["evidence_text"].replace(
            "faction=PlayerAlly", "faction=Vukah")
        self.assertFalse(evaluate_load_only(**value)["eml_patch_applied"])

    def test_incomplete_model_or_animation_fingerprint_is_rejected(self):
        for old in ("model_guid=human-model", "animation_graph_guid=human-graph"):
            with self.subTest(field=old):
                value = artifacts()
                value["evidence_text"] = value["evidence_text"].replace(old, old.split("=")[0] + "=UNAVAILABLE", 1)
                self.assertFalse(evaluate_load_only(**value)["eml_patch_applied"])

    def test_matching_lua_nil_model_values_do_not_pass_level_a(self):
        value = artifacts()
        value["evidence_text"] = value["evidence_text"].replace(
            "model_guid=human-model", "model_guid=nil", 1).replace(
            "source_model_guid=human-model", "source_model_guid=nil", 1)
        result = evaluate_load_only(**value)
        self.assertFalse(result["eml_patch_applied"])
        self.assertEqual(result["status"], "FAILED")

    def test_missing_observer_keeps_emf_runtime_unknown(self):
        result = self.evaluate(observer_results=None)
        self.assertIsNone(result["emf_runtime_confirmed"])
        self.assertEqual(result["status"], "PARTIAL_SUCCESS")

    def test_missing_bridge_keeps_emf_runtime_unknown(self):
        result = self.evaluate(bridge_diagnostics=None)
        self.assertIsNone(result["emf_runtime_confirmed"])

    def test_game_load_error_fails_level_b(self):
        report = artifacts()["game_load_report"]
        report["resource_errors"] = ["asset database error"]
        result = self.evaluate(game_load_report=report)
        self.assertFalse(result["game_load_confirmed"])
        self.assertEqual(result["status"], "FAILED")

    def test_unknown_kfc_or_dat_change_requires_recovery(self):
        report = artifacts()["integrity_report"]
        report["unknown_changes"] = ["enshrouded_055.dat"]
        result = self.evaluate(integrity_report=report)
        self.assertEqual(result["status"], "RECOVERY_REQUIRED")

    def test_non_target_save_change_requires_recovery(self):
        report = artifacts()["integrity_report"]
        report["non_target_saves_unchanged"] = False
        self.assertEqual(self.evaluate(integrity_report=report)["status"], "RECOVERY_REQUIRED")

    def test_missing_backup_blocks_success(self):
        result = self.evaluate(backup_verified=False)
        self.assertFalse(result["game_load_confirmed"])
        self.assertFalse(result["load_only_success"])

    def test_rollback_error_requires_recovery(self):
        report = artifacts()["integrity_report"]
        report["rollback_ready"] = False
        self.assertEqual(self.evaluate(integrity_report=report)["status"], "RECOVERY_REQUIRED")

    def test_unavailable_direct_lookup_is_expected_and_does_not_block_success(self):
        result = self.evaluate()
        self.assertEqual(result["direct_emf_template_lookup"], DIRECT_LOOKUP_STATUS)
        self.assertTrue(result["load_only_success"])

    def test_old_log_errors_before_correlated_run_are_ignored(self):
        value = artifacts()
        value["eml_log"] = "ERROR old unrelated launch\n" + value["eml_log"]
        value["emf_log"] = "emf_core 0.3.2 ERROR old launch\n" + value["emf_log"]
        self.assertTrue(evaluate_load_only(**value)["load_only_success"])

    def test_real_lua_tab_separated_ready_marker_is_correlated(self):
        value = artifacts()
        value["eml_log"] = value["eml_log"].replace(
            f"AIC_EML_TEMPLATE_READY {TOKEN} {EXPECTED_TEMPLATE_GUID} 2939921867",
            f"AIC_EML_TEMPLATE_READY\t{TOKEN}\t{EXPECTED_TEMPLATE_GUID}\t2939921867",
        )
        self.assertTrue(evaluate_load_only(**value)["load_only_success"])

    def test_empty_evaluation_is_not_executed(self):
        result = evaluate_load_only()
        self.assertEqual(result["status"], "NOT_EXECUTED")
        self.assertFalse(result["load_only_success"])
        self.assertFalse(result["spawn_ready"])

    def test_evaluate_cli_without_artifacts_reports_not_executed(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = stage10_main(["evaluate"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "NOT_EXECUTED")


if __name__ == "__main__":
    unittest.main()
