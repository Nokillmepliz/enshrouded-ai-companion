"""Controlled Stage 10.7 Phase B audit/rollback/reinstall.

This script never starts Enshrouded and never edits LOCAL saves.  ``audit`` is
read-only.  ``apply`` re-runs the audit and then performs only the attributed
rollback and the nine-file install described by the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from companion.stage10 import (create_backup, install, preflight, restore_game_data,
                               rollback_added_files, sha256, verify_backup)

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r"D:\SteamLibrary\steamapps\common\Enshrouded")
SAVES = Path(r"C:\Users\user\Saved Games\keen games\Enshrouded\default")
EML = ROOT / "runtime/stage10/downloads/dbghelp.dll"
PATCH = ROOT / "experimental/eml_humanoid"
OBSERVER = ROOT / "mods/aic_template_observer"
OLD_BACKUP = ROOT / "runtime/backups/stage10-6-pre-eml-20261101T083034Z/manifest.json"
OLD_RECEIPT = ROOT / "runtime/stage10_6/install-receipt-remediated.json"
OLD_BASELINE = ROOT / "runtime/stage10_6/pre-run-integrity.json"
OLD_POST = ROOT / "runtime/stage10_6/evidence/post-run-integrity.json"
WORK = ROOT / "runtime/stage10_7"
NEW_BACKUP_DIR = ROOT / "runtime/backups/stage10-7-pre-eml-20261101"
NEW_BACKUP = NEW_BACKUP_DIR / "manifest.json"
NEW_PLAN = WORK / "install-plan.json"
NEW_RECEIPT = WORK / "install-receipt.json"
ROLLBACK_REPORT = WORK / "rollback-report.json"
AUDIT_REPORT = WORK / "phase-b-audit.json"
RESULT = WORK / "phase-b-result.json"
EXPECTED_PATHS = {
    "dbghelp.dll", "eml.json", "mods/aic_eml_humanoid/mod.json",
    "mods/aic_eml_humanoid/README.md", "mods/aic_eml_humanoid/src/mod.lua",
    "emf/mods/aic_template_observer/json.lua", "emf/mods/aic_template_observer/main.lua",
    "emf/mods/aic_template_observer/mod.json", "emf/config/aic_template_observer.ini",
}
ATTRIBUTED_DIRS = (".cache", "export", "logs")
ATTRIBUTED_DAT = tuple(f"enshrouded_{i:03d}.dat" for i in range(55, 64))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stopped() -> bool:
    for image in ("enshrouded.exe", "enshrouded_server.exe"):
        proc = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
                              capture_output=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"process_check_failed:{image}")
        if image.encode().lower() in proc.stdout.lower():
            return False
    return True


def require_stopped() -> None:
    if not stopped():
        raise RuntimeError("game_or_server_running")


def snapshot_saves() -> dict[str, str]:
    return {str(p.relative_to(SAVES)).replace("/", "\\"): sha256(p)
            for p in SAVES.rglob("*") if p.is_file()}


def receipt() -> tuple[dict, dict[str, str]]:
    data = load(OLD_RECEIPT)
    applied = data.get("applied")
    if data.get("state") != "complete" or not isinstance(applied, list) or len(applied) != 9:
        raise RuntimeError("old_receipt_not_complete_9")
    hashes = {e["path"].replace("\\", "/"): e["sha256"] for e in applied}
    if set(hashes) != EXPECTED_PATHS:
        raise RuntimeError("old_receipt_path_set_mismatch")
    for relative, expected in hashes.items():
        path = GAME / relative
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"old_install_hash_mismatch:{relative}")
    return data, hashes


def audit() -> dict:
    require_stopped()
    if not verify_backup(OLD_BACKUP):
        raise RuntimeError("old_backup_verification_failed")
    backup = load(OLD_BACKUP)
    if backup.get("files") != 24 or len(backup.get("entries", [])) != 24:
        raise RuntimeError("old_backup_not_24")
    old_receipt, hashes = receipt()
    baseline, post = load(OLD_BASELINE), load(OLD_POST)
    base_dat = {x["name"]: x for x in baseline["dat"]}
    current_dat = {p.name: p for p in GAME.glob("enshrouded_[0-9][0-9][0-9].dat")}
    if set(base_dat) != {f"enshrouded_{i:03d}.dat" for i in range(55)}:
        raise RuntimeError("baseline_dat_set_not_55")
    for name, expected in base_dat.items():
        path = current_dat.get(name)
        if path is None or path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise RuntimeError(f"baseline_dat_mismatch:{name}")
    additions = sorted(set(current_dat) - set(base_dat))
    if additions != list(ATTRIBUTED_DAT) or any(current_dat[n].stat().st_size != 0 for n in additions):
        raise RuntimeError("attributed_dat_mismatch")
    entries = {Path(x["source"]).name: x for x in backup["entries"]}
    bak = GAME / "enshrouded.kfc.bak"
    if not bak.is_file() or sha256(bak) != entries["enshrouded.kfc"]["sha256"]:
        raise RuntimeError("kfc_bak_baseline_mismatch")
    if sha256(GAME / "enshrouded.kfc") == entries["enshrouded.kfc"]["sha256"]:
        raise RuntimeError("kfc_not_marked_as_eml_changed")
    if sha256(GAME / "enshrouded.kfc_resources") == entries["enshrouded.kfc_resources"]["sha256"]:
        raise RuntimeError("resources_not_marked_as_eml_changed")
    if post.get("unknown_changes") != [] or post.get("installed_files_match_receipt") is not True:
        raise RuntimeError("prior_attribution_not_clean")
    if set(post.get("known_runtime_outputs", ())) != set(ATTRIBUTED_DIRS) | {"enshrouded.kfc.bak"} | set(ATTRIBUTED_DAT):
        raise RuntimeError("known_runtime_output_set_mismatch")
    current_saves, old_saves = snapshot_saves(), {x["path"]: x["sha256"] for x in baseline["local_saves"]}
    if set(current_saves) != set(old_saves):
        raise RuntimeError("local_save_set_changed")
    changed = sorted(k for k in current_saves if current_saves[k] != old_saves[k])
    if len(changed) != 6:
        raise RuntimeError(f"unexpected_local_save_change_count:{len(changed)}")
    return {"status": "READY", "game_and_server_stopped": True,
            "receipt_sha256": sha256(OLD_RECEIPT), "receipt_state": old_receipt["state"],
            "installed_files_verified": len(hashes), "backup_files_verified": 24,
            "baseline_dat_verified": 55, "attributed_dat": additions,
            "kfc_changed_by_eml": True, "resources_changed_by_eml": True,
            "kfc_bak_matches_baseline": True, "local_save_files": len(current_saves),
            "local_save_changed": changed, "unknown_changes": []}


def clean_attributed_dirs(post: dict) -> list[str]:
    known = set(post.get("known_runtime_outputs", ()))
    removed = []
    game_root = GAME.resolve()
    for relative in ATTRIBUTED_DIRS:
        if relative not in known:
            raise RuntimeError(f"directory_not_attributed:{relative}")
        path = (GAME / relative).resolve()
        if path.parent != game_root:
            raise RuntimeError(f"unsafe_attributed_path:{path}")
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(relative)
        elif path.exists():
            raise RuntimeError(f"attributed_path_not_directory:{relative}")
    return removed


def verify_clean(old_backup: dict, saves_before: dict[str, str]) -> dict:
    entries = {Path(x["source"]).name: x for x in old_backup["entries"]}
    if sha256(GAME / "enshrouded.kfc") != entries["enshrouded.kfc"]["sha256"]:
        raise RuntimeError("clean_kfc_mismatch")
    if sha256(GAME / "enshrouded.kfc_resources") != entries["enshrouded.kfc_resources"]["sha256"]:
        raise RuntimeError("clean_resources_mismatch")
    dat = sorted(p.name for p in GAME.glob("enshrouded_[0-9][0-9][0-9].dat"))
    if dat != [f"enshrouded_{i:03d}.dat" for i in range(55)]:
        raise RuntimeError("clean_dat_set_mismatch")
    if (GAME / "enshrouded.kfc.bak").exists() or any((GAME / x).exists() for x in ATTRIBUTED_DIRS):
        raise RuntimeError("attributed_runtime_output_remains")
    if any((GAME / x).exists() for x in EXPECTED_PATHS):
        raise RuntimeError("old_install_path_remains")
    if snapshot_saves() != saves_before:
        raise RuntimeError("local_saves_changed_by_phase_b")
    return {"kfc_resources_baseline": True, "dat_files": 55,
            "install_paths_absent": 9, "local_saves_unchanged": True, "unknown_changes": []}


def apply() -> dict:
    if any(p.exists() for p in (NEW_BACKUP_DIR, NEW_PLAN, NEW_RECEIPT, ROLLBACK_REPORT, RESULT)):
        raise RuntimeError("stage10_7_output_collision")
    WORK.mkdir(parents=True, exist_ok=True)
    initial = audit()
    AUDIT_REPORT.write_text(json.dumps(initial, indent=2, ensure_ascii=False), encoding="utf-8")
    saves_before = snapshot_saves()
    old_backup, post = load(OLD_BACKUP), load(OLD_POST)
    old_receipt_sha = sha256(OLD_RECEIPT)
    result = {"status": "IN_PROGRESS", "started_utc": datetime.now(timezone.utc).isoformat(),
              "audit": initial, "stage": "rollback"}
    try:
        require_stopped()
        result["rollback_files"] = rollback_added_files(
            GAME, OLD_RECEIPT, apply=True, game_running=False)["removed"]
        result["restore"] = restore_game_data(
            GAME, OLD_BACKUP, approved_new_dat=ATTRIBUTED_DAT, apply=True,
            game_running=False, report_path=ROLLBACK_REPORT)
        result["removed_runtime_dirs"] = clean_attributed_dirs(post)
        if sha256(OLD_RECEIPT) != old_receipt_sha:
            raise RuntimeError("old_receipt_history_changed")
        result["clean"] = verify_clean(old_backup, saves_before)
        result["stage"] = "backup"
        backup_plan = create_backup(GAME, SAVES, NEW_BACKUP_DIR, apply=False)
        if backup_plan["files"] != 24:
            raise RuntimeError(f"new_backup_plan_not_24:{backup_plan['files']}")
        result["new_backup"] = create_backup(
            GAME, SAVES, NEW_BACKUP_DIR, apply=True, game_running=False)
        if not verify_backup(NEW_BACKUP):
            raise RuntimeError("new_backup_verification_failed")
        result["stage"] = "install"
        require_stopped()
        pf = preflight(GAME, EML, PATCH, OBSERVER, expected_game_dir=GAME,
                       game_running=False, backup_manifest=NEW_BACKUP, receipt_path=NEW_RECEIPT)
        if not pf.get("installation_ready") or not pf.get("rollback_ready"):
            raise RuntimeError(f"preflight_not_ready:{pf.get('blockers')}")
        plan = install(GAME, EML, PATCH, OBSERVER, NEW_BACKUP, NEW_RECEIPT, apply=False)
        if set(x.replace("\\", "/") for x in plan["files"]) != EXPECTED_PATHS:
            raise RuntimeError("new_plan_path_set_mismatch")
        NEW_PLAN.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        installed = install(GAME, EML, PATCH, OBSERVER, NEW_BACKUP, NEW_RECEIPT,
                            apply=True, game_running=False)
        receipt_data = load(NEW_RECEIPT)
        if receipt_data.get("state") != "complete" or receipt_data.get("patch_version") != "0.4.0":
            raise RuntimeError("new_receipt_identity_mismatch")
        actual = {}
        for entry in receipt_data["applied"]:
            path = GAME / entry["path"]
            actual[entry["path"]] = sha256(path)
            if actual[entry["path"]] != entry["sha256"]:
                raise RuntimeError(f"post_install_hash_mismatch:{entry['path']}")
        installed_lua = (GAME / "mods/aic_eml_humanoid/src/mod.lua").read_text(encoding="utf-8")
        installed_manifest = load(GAME / "mods/aic_eml_humanoid/mod.json")
        installed_observer = (GAME / "emf/mods/aic_template_observer/main.lua").read_text(encoding="utf-8")
        token = receipt_data["run_token"]
        if installed_manifest.get("version") != "0.4.0" or "evidence_v4" not in installed_lua:
            raise RuntimeError("installed_patch_semantics_mismatch")
        if "template_evidence_v4.txt" not in installed_observer or token not in installed_lua or token not in installed_observer:
            raise RuntimeError("installed_observer_or_token_mismatch")
        if "__AIC_STAGE10_RUN_TOKEN__" in installed_lua + installed_observer:
            raise RuntimeError("installed_token_placeholder_remains")
        if snapshot_saves() != saves_before:
            raise RuntimeError("local_saves_changed_during_install")
        result.update({"stage": "complete", "status": "COMPLETE",
                       "new_receipt_sha256": sha256(NEW_RECEIPT),
                       "new_receipt_state": receipt_data["state"],
                       "installed_files_verified": len(actual),
                       "patch_version": installed_manifest["version"],
                       "evidence_version": "v4", "observer_v4_compatible": True,
                       "run_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                       "rollback_dry_run": rollback_added_files(GAME, NEW_RECEIPT)["removable"],
                       "new_backup_verified": verify_backup(NEW_BACKUP),
                       "local_saves_unchanged": True, "game_and_server_stopped": stopped(),
                       "spawn_ready": False, "finished_utc": datetime.now(timezone.utc).isoformat()})
        RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
    except BaseException as exc:
        result.update({"status": "FAILED", "error": f"{type(exc).__name__}:{exc}",
                       "finished_utc": datetime.now(timezone.utc).isoformat()})
        RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        raise


def verify_installed() -> dict:
    require_stopped()
    if not verify_backup(NEW_BACKUP):
        raise RuntimeError("new_backup_verification_failed")
    data = load(NEW_RECEIPT)
    applied = data.get("applied")
    if data.get("state") != "complete" or data.get("patch_version") != "0.4.0":
        raise RuntimeError("new_receipt_identity_mismatch")
    if not isinstance(applied, list) or len(applied) != 9:
        raise RuntimeError("new_receipt_not_complete_9")
    if {x["path"].replace("\\", "/") for x in applied} != EXPECTED_PATHS:
        raise RuntimeError("new_receipt_path_set_mismatch")
    for entry in applied:
        path = GAME / entry["path"]
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"new_install_hash_mismatch:{entry['path']}")
    manifest = load(NEW_BACKUP)
    for entry in manifest["entries"]:
        source = Path(entry["source"])
        if not source.is_file() or sha256(source) != entry["sha256"]:
            raise RuntimeError(f"new_backup_source_changed:{source}")
    if sorted(p.name for p in GAME.glob("enshrouded_[0-9][0-9][0-9].dat")) != [
            f"enshrouded_{i:03d}.dat" for i in range(55)]:
        raise RuntimeError("post_install_dat_set_mismatch")
    if (GAME / "enshrouded.kfc.bak").exists() or any((GAME / x).exists() for x in ATTRIBUTED_DIRS):
        raise RuntimeError("unexpected_runtime_output_before_phase_c")
    lua = (GAME / "mods/aic_eml_humanoid/src/mod.lua").read_text(encoding="utf-8")
    observer = (GAME / "emf/mods/aic_template_observer/main.lua").read_text(encoding="utf-8")
    token = data["run_token"]
    if token not in lua or token not in observer or "evidence_v4" not in lua:
        raise RuntimeError("installed_token_or_evidence_mismatch")
    removable = rollback_added_files(GAME, NEW_RECEIPT)["removable"]
    return {"status": "READY_FOR_PHASE_C_REVIEW", "game_and_server_stopped": True,
            "receipt_sha256": sha256(NEW_RECEIPT), "receipt_state": data["state"],
            "installed_files_verified": 9, "backup_files_verified": len(manifest["entries"]),
            "backup_sources_verified": len(manifest["entries"]), "dat_files": 55,
            "patch_version": data["patch_version"], "evidence_version": "v4",
            "observer_v4_compatible": "template_evidence_v4.txt" in observer,
            "run_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "rollback_dry_run_files": len(removable), "runtime_outputs_absent": True,
            "local_saves_unchanged_since_new_backup": True, "spawn_ready": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("audit", "apply", "verify"))
    args = parser.parse_args()
    data = audit() if args.mode == "audit" else apply() if args.mode == "apply" else verify_installed()
    public = {k: v for k, v in data.items() if k not in {"run_token"}}
    print(json.dumps(public, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
