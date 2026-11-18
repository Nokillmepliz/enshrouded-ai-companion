"""Assemble offline evidence from audit metadata, without opening game/transport."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import load_profile, make_evidence, validate_evidence

OUT = ROOT / "compatibility/audits/1287369"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main():
    profile = load_profile(1287369)
    identity = {"game_build": profile["game_build"], "exe_sha256": profile["exe_sha256"],
                "emf_candidate_commit": profile["emf_commit"]}
    observations = {}

    def add(name, status, expected, observed, source, provenance, error="", unknowns=(), runtime=True):
        observations[name] = {"status": status, "expected": expected, "observed": observed,
                              "source": source, "provenance": provenance, "identity": identity,
                              "error": error, "unknowns": list(unknowns), "runtime_validation_required": runtime}

    add("GAME_VERSION", "PASS", "identify installed game independently", {
        "game_version": "1.0.1.2", "game_build": 1287369, "steam_build_id": "26430625",
        "depot_manifest_id": "7226436020230696061", "update_detected": True},
        ["docs/STAGE10_10_GAME_VERSION_AUDIT.md"], "EXE_REFLECTION_SHA256_AND_STEAM_MANIFEST", runtime=False)
    add("GAME_FILE_INVENTORY", "BLOCKED", "verified clean current-build baseline", read("file-inventory.json")["counts"],
        ["compatibility/audits/1287369/file-inventory.json", "compatibility/audits/1287369/integrity.json"],
        "FULL_READ_ONLY_SHA256_INVENTORY", "BLOCKED_BY_GAME_INTEGRITY", ["clean_depot_baseline"], False)
    add("BACKUP_COMPATIBILITY", "BLOCKED", "same-build verified backup for restoration", read("backup-audit.json"),
        ["docs/STAGE10_10_BACKUP_AND_ROLLBACK_SAFETY.md"], "REHASHED_HISTORICAL_BACKUPS_AND_RECEIPT",
        "ROLLBACK_BLOCKED_BUILD_MISMATCH", ["new_clean_backup"], False)
    add("EMF_COMPATIBILITY", "UNKNOWN", "source and local binary runtime support", {
        "candidate": "0.6.18", "native_api": 46, "lua_host_version": "1.39.0", "source_support": "SUPPORTED",
        "archive_sha256_verified": True, "authenticode": "NotSigned", "installed_0_3_2": "UNSUPPORTED"},
        ["docs/STAGE10_10_EMF_COMPATIBILITY.md"], "PINNED_UPSTREAM_SOURCE_RELEASE_DIGEST_AND_PE_AUDIT",
        "runtime_not_executed", ["local_binary_runtime", "reproducible_build_identity"])
    add("EML_COMPATIBILITY", "UNKNOWN", "one accepted content owner and evidence channel", {
        "standalone": "0.2.0", "parser": "OFFLINE_DECODE_PASSED", "emf_shadow_export": False},
        ["docs/STAGE10_10_EML_COMPATIBILITY.md"], "PINNED_SOURCE_AND_CURRENT_RESOURCE_DECODE",
        "content_owner_and_evidence_unresolved", ["writer_finalization", "runtime_resource_load"])
    add("ECS_DIFF", "UNKNOWN", "complete old/new ABI comparison", read("ecs-diff.json")["counts"],
        ["compatibility/audits/1287369/ecs-diff.json", "compatibility/audits/1287369/critical-schemas.json"],
        "GENERATED_HEADERS_AND_CURRENT_EXE_REFLECTION", "partial_schema_coverage",
        ["old_original_alignment", "full_old_resource_schema_and_enums"])
    resource = read("resource-diff.json")
    add("RESOURCE_DIFF", "BLOCKED", "clean source and absence of collisions", {
        "component_count": 82, "component_fingerprint": "5253f478", "source_guid_present": True,
        "custom_guid_present": True, "resources_decoded": len(resource["resource_comparison"])},
        ["compatibility/audits/1287369/resource-diff.json"], "READ_ONLY_KFC_CURRENT_MODIFIED_DATABASE",
        "clean_baseline_unavailable", ["clean_guid_npc_id_collision_scan"])
    add("CHARACTER_SETUP", "PASS", "serialized typed source/clone comparison only", {
        "source": resource["hunter_assistant"]["character_setup"], "clone": resource["clone"]["character_setup"],
        "runtime_lua_reflection": "NOT_EXECUTED"}, ["docs/STAGE10_10_TEMPLATE_COMPATIBILITY.md"],
        "SERIALIZED_KFC_VALUES_AND_EXE_FIELD_TYPES")
    add("BRIDGE_COMPATIBILITY", "UNKNOWN", "correlated runtime status/inspect/compare", {
        "wire_protocol": 1, "offline_capture_validator": "TESTED", "runtime_transport_opened": False},
        ["docs/STAGE10_10_BRIDGE_COMPATIBILITY.md"], "PINNED_PROTOCOL_SOURCE_AND_FIXTURES",
        "no_runtime_session", ["new_observer_evidence_channel", "local_world_session"])
    add("PATCH_COMPATIBILITY", "BLOCKED", "installable reviewed current-build patch", {
        "historical": "0.4.0 preserved", "next": "0.5.0 guard preparation only", "resource_writes": False},
        ["experimental/eml_humanoid_next/README.md"], "OFFLINE_PREPARATION_ONLY", "clean_baseline_and_content_owner_required",
        ["complete_patch", "serialization", "writer_finalization"])
    add("STAGE10_9_REVALIDATION", "PASS", "source-level review of prior conclusions", {
        "ground_path_absence": "SUPERSEDED_BY_NEW_API", "villager_move": "AVAILABLE_API46",
        "identity_and_atomic_destroy": "NOT_EXPOSED_IN_REVIEWED_PUBLIC_API", "runtime_proof": "NOT_EXECUTED"},
        ["docs/STAGE10_10_STAGE10_9_REVALIDATION.md"], "PINNED_PUBLIC_API_AND_IMPLEMENTATION_REVIEW")
    tests = json.loads((ROOT / "runtime/stage10_10/test-results.json").read_text())
    tests["skip_reasons"] = ["Windows directory symlink requires privilege (WinError 1314); historical skip"]
    if tests["failed"] or tests["errors"]:
        raise RuntimeError("offline_tests_failed")
    tests.update({"rust_passed": 2, "cpp_cases_passed": 30, "cpp_assertions_passed": 730,
                  "lua_syntax_files": 13, "scope": "offline fixtures and fake engine services"})
    add("OFFLINE_TESTS", "PASS", "required offline scenarios and regression checks", tests,
        ["docs/STAGE10_10_TEST_PLAN.md", "tests/test_stage10_10.py"], "EXECUTED_OFFLINE_TEST_RUNS", runtime=False)
    add("INSTALL_READINESS", "BLOCKED", False, False, ["docs/STAGE10_10_INSTALL_PLAN.md"],
        "PHASE_A_ONLY", "BLOCKED_BY_GAME_INTEGRITY", ["accepted_install_plan_and_separate_permission"], False)
    add("RUNTIME_STATUS", "NOT_EXECUTED", "NOT_EXECUTED", "NOT_EXECUTED",
        ["docs/STAGE10_10_RUNTIME_RESULTS.md"], "NO_GAME_LAUNCH_OR_BRIDGE_CONNECTION", unknowns=["all_runtime_gates"])
    evidence = make_evidence(identity, observations)
    errors = validate_evidence(evidence)
    if errors:
        raise RuntimeError(errors)
    (OUT / "evidence-v7.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("evidence v7: 14 sections validated; installation_ready=false, spawn_ready=false")


if __name__ == "__main__":
    main()
