"""Fail-closed preparation utilities for the Stage 10 EML load test.

All public planning functions are read-only. Mutation helpers require an
explicit ``apply=True`` and are intended for a separately approved phase B.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
from .eml_humanoid import validate_patch


EXPECTED_BUILD = 1_273_043
EXPECTED_GAME_SHA256 = "d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882"
EXPECTED_EMF_LOADER_SHA256 = "53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee"
EXPECTED_EML_DBGHELP_SHA256 = "038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa"
EXPECTED_EMM_SHA256 = "b1133f6b8ea7000596cc7710901bd8307b48165b0e650c0487a611d90ea49305"
EVIDENCE_RELATIVE = Path("export/aic_eml_humanoid/template_evidence_v1.txt")
EXPECTED_TEMPLATE_GUID = "a1c90001-5e4d-4a91-8a1c-000000000001"
EXPECTED_SOURCE_GUID = "e3736dff-0ad2-47fc-903c-66c1775836e8"
EXPECTED_PATCH_VERSION = "0.1.0"
RUN_TOKEN_PLACEHOLDER = "__AIC_STAGE10_RUN_TOKEN__"
RUN_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")
DIRECT_LOOKUP_STATUS = "UNAVAILABLE_WITHOUT_ENTITY"
RESULT_STATUSES = (
    "NOT_EXECUTED", "PREPARATION_READY", "PARTIAL_SUCCESS",
    "LOAD_ONLY_SUCCESS", "FAILED", "RECOVERY_REQUIRED",
)


class Stage10Error(RuntimeError):
    pass


def detect_game_process() -> bool:
    """Return whether Enshrouded is running; fail closed if Windows cannot answer."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq enshrouded.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Stage10Error("game_process_check_failed") from exc
    if result.returncode != 0:
        raise Stage10Error("game_process_check_failed")
    return re.search(r'"?enshrouded\.exe"?', result.stdout, re.IGNORECASE) is not None


def _ensure_game_stopped(apply: bool, game_running: bool | None) -> None:
    if not apply:
        return
    running = detect_game_process() if game_running is None else game_running
    if running:
        raise Stage10Error("game_process_running")


def sha256(path: str | Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _regular(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise Stage10Error(f"reparse_point_refused:{path}")
    if not path.is_file():
        raise Stage10Error(f"regular_file_required:{path}")


def detect_logged_build(game_dir: str | Path) -> int | None:
    log = Path(game_dir) / "emf" / "emf_core.log"
    if not log.is_file():
        return None
    match = re.search(r"known build (\d+)", log.read_text(encoding="utf-8", errors="replace"))
    return int(match.group(1)) if match else None


def validate_observer(observer_dir: str | Path) -> tuple[str, ...]:
    root = Path(observer_dir)
    manifest_path, source_path = root / "mod.json", root / "main.lua"
    if not manifest_path.is_file() or not source_path.is_file() or not (root / "json.lua").is_file():
        raise Stage10Error("observer_layout_invalid")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Stage10Error("observer_manifest_invalid") from exc
    if manifest.get("id") != "aic_template_observer" or manifest.get("enabled") is not False:
        raise Stage10Error("observer_must_be_disabled_by_default")
    if manifest.get("emf") != 20 or manifest.get("depends", {}).get("lua") != ">=1.9":
        raise Stage10Error("observer_runtime_contract_invalid")
    source = source_path.read_text(encoding="utf-8")
    forbidden = (
        "emf.spawn", "emf.destroy", "emf.emit", "world:set", "on_tick",
        "Inventory", "save_world", "request_save", "os.remove", "io.open(path, 'w'",
    )
    if any(token in source for token in forbidden):
        raise Stage10Error("observer_mutation_path_forbidden")
    for command in ("status", "inspect", "compare"):
        if f"emf.command('{command}'" not in source:
            raise Stage10Error(f"observer_command_missing:{command}")
    if "UNAVAILABLE_WITHOUT_ENTITY" not in source or "spawn_forbidden = true" not in source:
        raise Stage10Error("observer_limitation_missing")
    if source.count(RUN_TOKEN_PLACEHOLDER) != 1 or "AIC_TEMPLATE_OBSERVER_READY" not in source:
        raise Stage10Error("observer_run_correlation_missing")
    return ("manifest", "disabled_default", "read_only", "run_correlation",
            "status", "inspect", "compare")


def parse_evidence(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([a-z_]+)=(.*)", line)
        if not match or match.group(1) in result:
            raise Stage10Error("evidence_malformed")
        result[match.group(1)] = match.group(2)
    return result


def evaluate_evidence(
    value: dict[str, str], *, writer_finalized: bool, expected_run_token: str | None = None,
) -> dict:
    required = {
        "format": "aic_eml_humanoid_evidence_v1",
        "template_guid": EXPECTED_TEMPLATE_GUID,
        "source_guid": EXPECTED_SOURCE_GUID,
        "npc_id": "2939921867",
        "faction": "PlayerAlly",
        "component_clone": "true",
        "source_unchanged": "true",
        "resource_lookup_after_create": "true",
        "patch_version": EXPECTED_PATCH_VERSION,
    }
    checks = {key: value.get(key) == expected for key, expected in required.items()}
    checks["model_available"] = value.get("model_guid") not in (None, "", "UNAVAILABLE")
    checks["model_matches_source"] = value.get("model_guid") == value.get("source_model_guid")
    checks["animation_graph_available"] = value.get("animation_graph_guid") not in (None, "", "UNAVAILABLE")
    checks["animation_graph_matches_source"] = (
        value.get("animation_graph_guid") == value.get("source_animation_graph_guid")
    )
    checks["component_fingerprint_complete"] = (
        bool(value.get("components")) and value.get("components") == value.get("source_components")
    )
    checks["registry_consistent"] = (
        value.get("source_registered") != "true" or value.get("registry_added") == "true"
    )
    checks["writer_finalized"] = writer_finalized
    if expected_run_token is not None:
        checks["run_token"] = value.get("run_token") == expected_run_token
    return {"ok": all(checks.values()), "checks": checks}


def eml_log_writer_finalized(text: str, run_token: str | None = None) -> bool:
    token = rf"{re.escape(run_token)}\s+" if run_token else r"(?:[0-9a-f]{32}\s+)?"
    ready = re.search(
        rf"AIC_EML_TEMPLATE_READY\s+{token}{re.escape(EXPECTED_TEMPLATE_GUID)}\s+2939921867\b",
        text,
    )
    if ready is None:
        return False
    return re.search(r"Applied\s+([1-9][0-9]*)\s+patches", text[ready.end():]) is not None


def preflight(
    game_dir: str | Path,
    eml_dbghelp: str | Path,
    patch_dir: str | Path,
    observer_dir: str | Path,
    *,
    expected_game_dir: str | Path | None = None,
    game_running: bool = False,
    backup_manifest: str | Path | None = None,
    receipt_path: str | Path | None = None,
) -> dict:
    game = Path(game_dir).resolve()
    if expected_game_dir is not None and game != Path(expected_game_dir).resolve():
        raise Stage10Error("unexpected_game_path")
    if game_running:
        raise Stage10Error("game_process_running")
    required = ("enshrouded.exe", "enshrouded.kfc", "enshrouded.kfc_resources", "dinput8.dll")
    for name in required:
        path = game / name
        if not path.is_file():
            raise Stage10Error(f"game_file_missing:{name}")
        _regular(path)
    if sha256(game / "enshrouded.exe") != EXPECTED_GAME_SHA256:
        raise Stage10Error("unknown_game_build")
    if detect_logged_build(game) != EXPECTED_BUILD:
        raise Stage10Error("build_marker_unconfirmed")
    if sha256(game / "dinput8.dll") != EXPECTED_EMF_LOADER_SHA256:
        raise Stage10Error("incompatible_emf_loader")
    eml = Path(eml_dbghelp).resolve()
    if not eml.is_file() or sha256(eml) != EXPECTED_EML_DBGHELP_SHA256:
        raise Stage10Error("eml_binary_missing_or_unverified")
    existing_dbghelp = game / "dbghelp.dll"
    if existing_dbghelp.exists():
        raise Stage10Error("conflicting_or_repeated_dbghelp_install")
    if (game / "eml.json").exists():
        raise Stage10Error("conflicting_or_repeated_eml_config")
    if (game / "enshrouded.kfc.bak").exists():
        raise Stage10Error("unexpected_kfc_backup")
    if (game / "mods" / "aic_eml_humanoid").exists():
        raise Stage10Error("patch_already_installed")
    eml_mods = game / "mods"
    if eml_mods.is_dir() and any(eml_mods.iterdir()):
        raise Stage10Error("conflicting_eml_mods_present")
    if (game / "emf" / "mods" / "aic_template_observer").exists():
        raise Stage10Error("observer_already_installed")
    if (game / "emf" / "config" / "aic_template_observer.ini").exists():
        raise Stage10Error("observer_config_already_installed")
    if (game / EVIDENCE_RELATIVE).exists():
        raise Stage10Error("stale_evidence_present")
    install_roots = (game, game / "mods", game / "emf")
    if any(
        any(root.rglob("*.stage10-install"))
        for root in install_roots if root.is_dir()
    ):
        raise Stage10Error("partial_install_temporary_present")
    if receipt_path is not None and Path(receipt_path).exists():
        raise Stage10Error("partial_or_repeated_install_receipt")
    patch_checks = validate_patch(patch_dir)
    observer_checks = validate_observer(observer_dir)
    if not os.access(game, os.W_OK):
        raise Stage10Error("game_directory_not_writable")
    required_free_bytes = (
        (game / "enshrouded.kfc").stat().st_size
        + (game / "enshrouded.kfc_resources").stat().st_size
        + 1024 ** 3
    )
    free_bytes = shutil.disk_usage(game).free
    if free_bytes < required_free_bytes:
        raise Stage10Error("insufficient_game_disk_space")
    baseline_dat = sorted(path.name for path in game.glob("enshrouded_[0-9][0-9][0-9].dat"))
    backup_verified = bool(backup_manifest and verify_backup(backup_manifest))
    blockers = [] if backup_verified else ["verified_backup_missing"]
    return {
        "ok": True,
        "status": "PREPARATION_READY",
        "mode": "dry_run",
        "game_dir": str(game),
        "build": EXPECTED_BUILD,
        "game_sha256": EXPECTED_GAME_SHA256,
        "emf_loader_sha256": EXPECTED_EMF_LOADER_SHA256,
        "eml_dbghelp_sha256": EXPECTED_EML_DBGHELP_SHA256,
        "patch_checks": list(patch_checks),
        "observer_checks": list(observer_checks),
        "baseline_dat": baseline_dat,
        "game_disk_free_bytes": free_bytes,
        "game_disk_required_bytes": required_free_bytes,
        "eml_state": "OFFLINE_VERIFIED",
        "emf_state": "INSTALLED_VERIFIED",
        "patch_state": "OFFLINE_VALIDATED",
        "observer_state": "OFFLINE_VALIDATED",
        "backup_verified": backup_verified,
        "rollback_ready": backup_verified,
        "installation_ready": backup_verified,
        "blockers": blockers,
        "direct_emf_template_lookup": DIRECT_LOOKUP_STATUS,
        "requires_user_approval": True,
        "phase_b_allowed": False,
    }


def _copy_verified(source: Path, destination: Path, reason: str) -> dict:
    _regular(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise Stage10Error(f"destination_exists:{destination}")
    shutil.copy2(source, destination)
    source_hash, copy_hash = sha256(source), sha256(destination)
    if source_hash != copy_hash:
        raise Stage10Error(f"copy_hash_mismatch:{source}")
    info = source.stat()
    return {
        "source": str(source), "backup": str(destination), "bytes": info.st_size,
        "mtime_ns": info.st_mtime_ns, "sha256": source_hash, "reason": reason, "verified": True,
    }


def create_backup(
    game_dir: str | Path,
    local_save_dir: str | Path,
    destination: str | Path,
    *,
    apply: bool = False,
    game_running: bool | None = None,
) -> dict:
    game, saves, output = Path(game_dir).resolve(), Path(local_save_dir).resolve(), Path(destination).resolve()
    _ensure_game_stopped(apply, game_running)
    sources = [game / "enshrouded.kfc", game / "enshrouded.kfc_resources"]
    if not saves.is_dir():
        raise Stage10Error("local_save_directory_missing")
    save_files = sorted(path for path in saves.rglob("*") if path.is_file())
    if not save_files:
        raise Stage10Error("local_save_files_missing")
    for path in sources + save_files:
        _regular(path)
    plan = {
        "mode": "apply" if apply else "dry_run",
        "verified": False,
        "destination": str(output),
        "files": len(sources) + len(save_files),
        "bytes": sum(path.stat().st_size for path in sources + save_files),
    }
    if not apply:
        return plan
    output.mkdir(parents=True, exist_ok=False)
    entries = []
    for path in sources:
        entries.append(_copy_verified(
            path, output / "game_data" / path.name,
            "EML may rewrite the KFC index or append serialized resources",
        ))
    for path in save_files:
        entries.append(_copy_verified(
            path, output / "local_saves" / path.relative_to(saves),
            "pre/post safeguard for the isolated LOCAL test profile",
        ))
    manifest = {
        **plan,
        "verified": True,
        "entries": entries,
        "baseline_game_root": sorted(path.name for path in game.iterdir()),
        "baseline_dat": sorted(path.name for path in game.glob("enshrouded_[0-9][0-9][0-9].dat")),
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if not verify_backup(manifest_path):
        raise Stage10Error("backup_verification_failed")
    return {"ok": True, "verified": True, "manifest": str(manifest_path), "files": len(entries)}


def verify_backup(manifest_path: str | Path) -> bool:
    path = Path(manifest_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries")
        if data.get("verified") is not True or not isinstance(entries, list) or not entries:
            return False
        for entry in entries:
            if not isinstance(entry, dict):
                return False
            if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                return False
            backup = Path(entry["backup"])
            if not backup.is_file() or backup.stat().st_size != entry["bytes"]:
                return False
            if sha256(backup) != entry["sha256"]:
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def installation_files(
    eml_dbghelp: str | Path, patch_dir: str | Path, observer_dir: str | Path,
    *, run_token: str | None = None,
) -> list[tuple[Path | None, Path, bytes | None]]:
    patch, observer = Path(patch_dir), Path(observer_dir)
    rendered_token = run_token or RUN_TOKEN_PLACEHOLDER
    if run_token is not None and RUN_TOKEN_PATTERN.fullmatch(run_token) is None:
        raise Stage10Error("invalid_run_token")
    result: list[tuple[Path | None, Path, bytes | None]] = [
        (Path(eml_dbghelp), Path("dbghelp.dll"), None),
        (None, Path("eml.json"), json.dumps({
            "enable_console": False,
            "use_export_flag": True,
            "export_directory": "export",
        }, indent=2).encode("utf-8") + b"\n"),
    ]
    for source in sorted(path for path in patch.rglob("*") if path.is_file()):
        relative = Path("mods/aic_eml_humanoid") / source.relative_to(patch)
        if source == patch / "src" / "mod.lua":
            raw = source.read_text(encoding="utf-8")
            if raw.count(RUN_TOKEN_PLACEHOLDER) != 1:
                raise Stage10Error("patch_run_token_placeholder_invalid")
            result.append((None, relative, raw.replace(
                RUN_TOKEN_PLACEHOLDER, rendered_token).encode("utf-8")))
        else:
            result.append((source, relative, None))
    for source in sorted(path for path in observer.rglob("*") if path.is_file()):
        relative = Path("emf/mods/aic_template_observer") / source.relative_to(observer)
        if source == observer / "main.lua":
            raw = source.read_text(encoding="utf-8")
            if raw.count(RUN_TOKEN_PLACEHOLDER) != 1:
                raise Stage10Error("observer_run_token_placeholder_invalid")
            result.append((None, relative, raw.replace(
                RUN_TOKEN_PLACEHOLDER, rendered_token).encode("utf-8")))
        else:
            result.append((source, relative, None))
    result.append((None, Path("emf/config/aic_template_observer.ini"),
                   b"[aic_template_observer]\nenabled=1\n"))
    return result


def install(
    game_dir: str | Path,
    eml_dbghelp: str | Path,
    patch_dir: str | Path,
    observer_dir: str | Path,
    backup_manifest: str | Path,
    receipt_path: str | Path,
    *,
    apply: bool = False,
    fail_after: int | None = None,
    game_running: bool | None = None,
) -> dict:
    game, receipt = Path(game_dir).resolve(), Path(receipt_path).resolve()
    _ensure_game_stopped(apply, game_running)
    if not verify_backup(backup_manifest):
        raise Stage10Error("verified_backup_required")
    eml = Path(eml_dbghelp).resolve()
    if not eml.is_file() or sha256(eml) != EXPECTED_EML_DBGHELP_SHA256:
        raise Stage10Error("eml_binary_missing_or_unverified")
    validate_patch(patch_dir)
    validate_observer(observer_dir)
    run_token = secrets.token_hex(16) if apply else None
    files = installation_files(
        eml_dbghelp, patch_dir, observer_dir, run_token=run_token)
    for _, relative, _ in files:
        if (game / relative).exists():
            raise Stage10Error(f"installation_collision:{relative.as_posix()}")
    plan = {
        "mode": "apply" if apply else "dry_run",
        "files": [str(x[1]) for x in files],
        "applied": [],
        "run_token": run_token or "GENERATED_ON_APPLY",
        "patch_version": EXPECTED_PATCH_VERSION,
        "game_build": EXPECTED_BUILD,
        "eml_sha256": EXPECTED_EML_DBGHELP_SHA256,
        "emf_sha256": EXPECTED_EMF_LOADER_SHA256,
    }
    if not apply:
        return plan
    if receipt.exists():
        raise Stage10Error("installation_receipt_exists")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({**plan, "state": "in_progress"}, indent=2), encoding="utf-8")
    for index, (source, relative, content) in enumerate(files):
        destination = game / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".stage10-install")
        if temporary.exists():
            raise Stage10Error(f"installation_temporary_exists:{relative.as_posix()}")
        try:
            if source is not None:
                shutil.copy2(source, temporary)
            else:
                temporary.write_bytes(content or b"")
            os.replace(temporary, destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        plan["applied"].append({"path": relative.as_posix(), "sha256": sha256(destination)})
        receipt.write_text(json.dumps({**plan, "state": "in_progress"}, indent=2), encoding="utf-8")
        if fail_after is not None and index + 1 >= fail_after:
            raise Stage10Error("injected_partial_install")
    receipt.write_text(json.dumps({**plan, "state": "complete"}, indent=2), encoding="utf-8")
    return {"ok": True, "receipt": str(receipt), "files": len(files), "run_token": run_token}


def rollback_added_files(
    game_dir: str | Path,
    receipt_path: str | Path,
    *,
    apply: bool = False,
    game_running: bool | None = None,
) -> dict:
    game, receipt = Path(game_dir).resolve(), Path(receipt_path).resolve()
    _ensure_game_stopped(apply, game_running)
    try:
        data = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage10Error("rollback_receipt_invalid") from exc
    applied = data.get("applied")
    if not isinstance(applied, list):
        raise Stage10Error("rollback_receipt_invalid")
    for entry in applied:
        path = game / entry["path"]
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise Stage10Error(f"rollback_state_unknown:{entry['path']}")
    if not apply:
        return {"mode": "dry_run", "removable": [entry["path"] for entry in applied]}
    for entry in reversed(applied):
        (game / entry["path"]).unlink()
    for relative in ("mods/aic_eml_humanoid", "emf/mods/aic_template_observer"):
        path = game / relative
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return {"ok": True, "removed": len(applied), "game_data_restored": False,
            "warning": "KFC restoration requires separately verified backup and post-run diff"}


def restore_game_data(
    game_dir: str | Path,
    backup_manifest: str | Path,
    *,
    approved_new_dat: tuple[str, ...] = (),
    apply: bool = False,
    game_running: bool | None = None,
    report_path: str | Path | None = None,
) -> dict:
    """Restore only EML-touched data after a reviewed post-run diff.

    New DAT files are never guessed: every one must be explicitly listed and
    must not have existed in the backup baseline.
    """
    game = Path(game_dir).resolve()
    _ensure_game_stopped(apply, game_running)
    manifest_path = Path(backup_manifest)
    if not verify_backup(manifest_path):
        raise Stage10Error("verified_backup_required")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {Path(item["source"]).name: item for item in data["entries"]}
    for name in ("enshrouded.kfc", "enshrouded.kfc_resources"):
        if name not in entries:
            raise Stage10Error(f"backup_entry_missing:{name}")
    baseline_dat = set(data.get("baseline_dat", ()))
    current_dat = {path.name for path in game.glob("enshrouded_[0-9][0-9][0-9].dat")}
    additions = current_dat - baseline_dat
    approved = set(approved_new_dat)
    if additions != approved:
        raise Stage10Error("unknown_runtime_outputs")
    if any(not re.fullmatch(r"enshrouded_[0-9]{3}\.dat", name) or name in baseline_dat for name in approved):
        raise Stage10Error("invalid_approved_runtime_output")
    bak = game / "enshrouded.kfc.bak"
    if bak.exists() and sha256(bak) != entries["enshrouded.kfc"]["sha256"]:
        raise Stage10Error("kfc_backup_identity_unknown")
    plan = {
        "mode": "apply" if apply else "dry_run",
        "restore": ["enshrouded.kfc", "enshrouded.kfc_resources"],
        "remove": sorted(approved | ({"enshrouded.kfc.bak"} if bak.exists() else set())),
    }
    if not apply:
        return plan
    report = Path(report_path) if report_path is not None else manifest_path.parent / "rollback-report.json"
    if report.exists():
        raise Stage10Error("rollback_report_exists")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({**plan, "state": "in_progress"}, indent=2), encoding="utf-8")
    for name in ("enshrouded.kfc", "enshrouded.kfc_resources"):
        source = Path(entries[name]["backup"])
        temporary = game / (name + ".stage10-restore")
        if temporary.exists():
            raise Stage10Error(f"restore_temporary_exists:{temporary.name}")
        shutil.copy2(source, temporary)
        if sha256(temporary) != entries[name]["sha256"]:
            raise Stage10Error(f"restore_hash_mismatch:{name}")
        os.replace(temporary, game / name)
    for name in approved:
        (game / name).unlink()
    if bak.exists():
        bak.unlink()
    for name in ("enshrouded.kfc", "enshrouded.kfc_resources"):
        if sha256(game / name) != entries[name]["sha256"]:
            raise Stage10Error(f"restore_verification_failed:{name}")
    result = {
        "ok": True, **plan,
        "verified_sha256": {
            name: sha256(game / name)
            for name in ("enshrouded.kfc", "enshrouded.kfc_resources")
        },
    }
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["report"] = str(report)
    return result


def _tri_state(checks: dict[str, bool | None]) -> bool | None:
    if any(value is False for value in checks.values()):
        return False
    if any(value is None for value in checks.values()):
        return None
    return True


def _log_has_failure(text: str) -> bool:
    patterns = (
        r"(?m)\bERROR\b", r"(?i)\bfatal\b", r"(?i)\bpanic(?:ked)?\b",
        r"(?i)serializ\w*.*(?:error|failed)", r"(?i)guid.*collision",
        r"(?i)resource.*(?:error|failed)",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _line_with(text: str, *needles: str) -> bool:
    return any(all(needle in line for needle in needles) for line in text.splitlines())


def _correlated_segment(
    text: str, marker: str, start_hint: str, *, marker_is_pattern: bool = False,
) -> str | None:
    if marker_is_pattern:
        matches = list(re.finditer(marker, text))
        if not matches:
            return None
        marker_at = matches[-1].start()
    else:
        marker_at = text.rfind(marker)
        if marker_at < 0:
            return None
    start_at = text.rfind(start_hint, 0, marker_at)
    return text[start_at if start_at >= 0 else marker_at:]


def evaluate_load_only(
    *,
    eml_log: str | None = None,
    evidence_text: str | None = None,
    emf_log: str | None = None,
    observer_results: dict | None = None,
    bridge_diagnostics: dict | None = None,
    game_load_report: dict | None = None,
    backup_verified: bool | None = None,
    integrity_report: dict | None = None,
    install_receipt: dict | None = None,
) -> dict:
    """Evaluate collected Stage 10.1 artifacts without touching the game.

    Every runtime artifact is correlated by the per-install run token. Missing
    data stays UNKNOWN; no caller can set load_only_success or spawn_ready.
    """
    errors: list[str] = []
    unknowns: list[str] = []
    confirmations: list[str] = []

    token = install_receipt.get("run_token") if isinstance(install_receipt, dict) else None
    receipt_checks: dict[str, bool | None] = {
        "receipt_complete": (
            install_receipt.get("state") == "complete"
            if isinstance(install_receipt, dict) else None
        ),
        "run_token_valid": (
            RUN_TOKEN_PATTERN.fullmatch(token) is not None if isinstance(token, str) else None
        ),
        "receipt_build": (
            install_receipt.get("game_build") == EXPECTED_BUILD
            if isinstance(install_receipt, dict) else None
        ),
        "receipt_patch_version": (
            install_receipt.get("patch_version") == EXPECTED_PATCH_VERSION
            if isinstance(install_receipt, dict) else None
        ),
    }

    runtime_present = any(value is not None for value in (
        eml_log, evidence_text, emf_log, observer_results, bridge_diagnostics,
        game_load_report, integrity_report, install_receipt,
    ))

    parsed_evidence: dict[str, str] | None = None
    evidence_checks: dict[str, bool | None] = {}
    if evidence_text is not None:
        try:
            parsed_evidence = parse_evidence(evidence_text)
        except Stage10Error:
            errors.append("evidence_malformed")

    a_present = any(value is not None for value in (eml_log, evidence_text, install_receipt))
    if not a_present:
        level_a = None
        unknowns.append("eml_patch_not_evaluated")
    else:
        evidence_result = None
        writer_finalized = False
        eml_segment = None
        if eml_log is None:
            unknowns.append("eml_log_missing")
        elif not isinstance(token, str):
            errors.append("eml_run_token_unavailable")
        else:
            eml_segment = _correlated_segment(
                eml_log,
                rf"AIC_EML_TEMPLATE_READY\s+{re.escape(token)}\b",
                "Running mod",
                marker_is_pattern=True,
            )
            writer_finalized = eml_log_writer_finalized(eml_log, token)
        if parsed_evidence is None:
            if evidence_text is None:
                unknowns.append("eml_evidence_missing")
        else:
            evidence_result = evaluate_evidence(
                parsed_evidence, writer_finalized=writer_finalized,
                expected_run_token=token if isinstance(token, str) else "",
            )
            evidence_checks = evidence_result["checks"]

        a_checks: dict[str, bool | None] = {
            **receipt_checks,
            "evidence_valid": evidence_result["ok"] if evidence_result is not None else None,
            "mod_loaded": (
                _line_with(eml_segment, "Running mod", "aic_eml_humanoid")
                if eml_segment is not None else (False if eml_log is not None else None)
            ),
            "ready_marker_correlated": (
                bool(isinstance(token, str) and eml_segment is not None and re.search(
                    rf"AIC_EML_TEMPLATE_READY\s+{re.escape(token)}\s+"
                    rf"{re.escape(EXPECTED_TEMPLATE_GUID)}\s+2939921867\b", eml_segment,
                )) if eml_log is not None else None
            ),
            "writer_finalized": writer_finalized if eml_log is not None else None,
            "eml_log_clean": (
                not _log_has_failure(eml_segment)
                if eml_segment is not None else (False if eml_log is not None else None)
            ),
        }
        level_a = _tri_state(a_checks)
        for name, value in a_checks.items():
            if value is False:
                errors.append(f"eml:{name}")
            elif value is None:
                unknowns.append(f"eml:{name}")
        if level_a:
            confirmations.append("EML_PATCH_APPLIED")

    source_template_unchanged = evidence_checks.get("source_unchanged")

    integrity_checks: dict[str, bool | None] = {
        "integrity_token": (
            integrity_report.get("run_token") == token
            if isinstance(integrity_report, dict) and isinstance(token, str) else None
        ),
        "known_file_changes": (
            integrity_report.get("unknown_changes") == []
            if isinstance(integrity_report, dict) else None
        ),
        "kfc_changes_reviewed": (
            integrity_report.get("kfc_changes_reviewed") is True
            if isinstance(integrity_report, dict) else None
        ),
        "dat_changes_reviewed": (
            integrity_report.get("dat_changes_reviewed") is True
            if isinstance(integrity_report, dict) else None
        ),
        "save_integrity_verified": (
            integrity_report.get("save_integrity_verified") is True
            if isinstance(integrity_report, dict) else None
        ),
        "non_target_saves_unchanged": (
            integrity_report.get("non_target_saves_unchanged") is True
            if isinstance(integrity_report, dict) else None
        ),
        "rollback_ready": (
            integrity_report.get("rollback_ready") is True
            if isinstance(integrity_report, dict) else None
        ),
    }
    save_integrity_verified = integrity_checks["save_integrity_verified"]
    rollback_ready = integrity_checks["rollback_ready"]

    b_present = game_load_report is not None or integrity_report is not None
    if not b_present:
        level_b = None
        unknowns.append("game_load_not_evaluated")
    else:
        b_checks: dict[str, bool | None] = {
            "game_report_token": (
                game_load_report.get("run_token") == token
                if isinstance(game_load_report, dict) and isinstance(token, str) else None
            ),
            "game_build": (
                game_load_report.get("game_build") == EXPECTED_BUILD
                if isinstance(game_load_report, dict) else None
            ),
            "main_menu_reached": (
                game_load_report.get("main_menu_reached") is True
                if isinstance(game_load_report, dict) else None
            ),
            "local_test_world_loaded": (
                game_load_report.get("local_test_world_loaded") is True
                if isinstance(game_load_report, dict) else None
            ),
            "resource_errors_absent": (
                game_load_report.get("resource_errors") == []
                if isinstance(game_load_report, dict) else None
            ),
            "game_errors_absent": (
                game_load_report.get("game_errors") == []
                if isinstance(game_load_report, dict) else None
            ),
            "backup_verified": backup_verified,
            **integrity_checks,
        }
        level_b = _tri_state(b_checks)
        for name, value in b_checks.items():
            if value is False:
                errors.append(f"game:{name}")
            elif value is None:
                unknowns.append(f"game:{name}")
        if level_b:
            confirmations.append("GAME_LOAD_CONFIRMED")

    c_present = any(value is not None for value in (emf_log, observer_results, bridge_diagnostics))
    if not c_present:
        level_c = None
        unknowns.append("emf_runtime_not_evaluated")
    else:
        emf_segment = (
            _correlated_segment(
                emf_log, f"AIC_TEMPLATE_OBSERVER_READY {token}", "emf_core 0.3.2")
            if emf_log is not None and isinstance(token, str) else None
        )
        responses = observer_results.get("responses") if isinstance(observer_results, dict) else None
        observer_checks: dict[str, bool | None] = {}
        for command in ("status", "inspect", "compare"):
            response = responses.get(command) if isinstance(responses, dict) else None
            observer_checks[f"observer_{command}"] = (
                isinstance(response, dict)
                and response.get("command") == command
                and response.get("loaded") is True
                and response.get("read_only") is True
                and response.get("spawn_forbidden") is True
                and response.get("run_token") == token
                and response.get("direct_emf_template_lookup") == DIRECT_LOOKUP_STATUS
            ) if response is not None else None
        inspect = responses.get("inspect") if isinstance(responses, dict) else None
        status_response = responses.get("status") if isinstance(responses, dict) else None
        compare = responses.get("compare") if isinstance(responses, dict) else None
        observer_checks["observer_field_source"] = (
            inspect.get("field_source") == "EML_EXPORT"
            if isinstance(inspect, dict) else None
        )
        observer_checks["observer_evidence_token"] = (
            status_response.get("evidence_run_token") == token
            if isinstance(status_response, dict) and isinstance(token, str) else None
        )
        observer_checks["observer_template_evidence"] = (
            status_response.get("new_template_eml_evidence") is True
            and status_response.get("original_template_eml_evidence") is True
            if isinstance(status_response, dict) else None
        )
        compare_checks = compare.get("checks") if isinstance(compare, dict) else None
        observer_checks["observer_compare"] = (
            all(value is True for key, value in compare_checks.items()
                if key != "writer_finalization_confirmed")
            and compare_checks.get("writer_finalization_confirmed") is False
            if isinstance(compare_checks, dict) and compare_checks else None
        )
        c_checks: dict[str, bool | None] = {
            "emf_log_correlated": (
                bool(isinstance(token, str) and
                     f"AIC_TEMPLATE_OBSERVER_READY {token}" in emf_log)
                if emf_log is not None else None
            ),
            "emf_version": (
                "emf_core 0.3.2" in emf_segment
                if emf_segment is not None else (False if emf_log is not None else None)
            ),
            "emf_build": (
                "known build 1273043" in emf_segment
                if emf_segment is not None else (False if emf_log is not None else None)
            ),
            "lua_host": (
                "Lua host 1.9.0" in emf_segment
                if emf_segment is not None else (False if emf_log is not None else None)
            ),
            "emf_log_clean": (
                not _log_has_failure(emf_segment)
                if emf_segment is not None else (False if emf_log is not None else None)
            ),
            **observer_checks,
            "bridge_token": (
                bridge_diagnostics.get("run_token") == token
                if isinstance(bridge_diagnostics, dict) and isinstance(token, str) else None
            ),
            "bridge_connected": (
                bridge_diagnostics.get("connected") is True
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_diagnose": (
                bridge_diagnostics.get("diagnose_ok") is True
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_status": (
                bridge_diagnostics.get("status_ok") is True
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_emf_version": (
                bridge_diagnostics.get("emf_version") == "0.3.2"
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_api": (
                bridge_diagnostics.get("api") == 20
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_build": (
                bridge_diagnostics.get("game_build") == EXPECTED_BUILD
                if isinstance(bridge_diagnostics, dict) else None
            ),
            "bridge_errors_absent": (
                bridge_diagnostics.get("errors") == []
                if isinstance(bridge_diagnostics, dict) else None
            ),
        }
        level_c = _tri_state(c_checks)
        for name, value in c_checks.items():
            if value is False:
                errors.append(f"emf:{name}")
            elif value is None:
                unknowns.append(f"emf:{name}")
        if level_c:
            confirmations.append("EMF_RUNTIME_CONFIRMED")

    recovery_required = any(value is False for value in (
        integrity_checks["known_file_changes"], save_integrity_verified,
        integrity_checks["non_target_saves_unchanged"], rollback_ready,
    ))
    all_levels = level_a is True and level_b is True and level_c is True
    safety_complete = (
        backup_verified is True and source_template_unchanged is True
        and save_integrity_verified is True and rollback_ready is True
    )
    load_only_success = all_levels and safety_complete and not errors

    if load_only_success:
        status = "LOAD_ONLY_SUCCESS"
    elif recovery_required:
        status = "RECOVERY_REQUIRED"
    elif any(level is False for level in (level_a, level_b, level_c)):
        status = "FAILED"
    elif any(level is True for level in (level_a, level_b, level_c)) or runtime_present:
        status = "PARTIAL_SUCCESS"
    else:
        status = "NOT_EXECUTED"

    if not runtime_present:
        status = "NOT_EXECUTED"
    assert status in RESULT_STATUSES
    return {
        "status": status,
        "levels": {
            "A": {"name": "EML_PATCH_APPLIED", "confirmed": level_a},
            "B": {"name": "GAME_LOAD_CONFIRMED", "confirmed": level_b},
            "C": {"name": "EMF_RUNTIME_CONFIRMED", "confirmed": level_c},
        },
        "eml_patch_applied": level_a,
        "game_load_confirmed": level_b,
        "emf_runtime_confirmed": level_c,
        "direct_emf_template_lookup": DIRECT_LOOKUP_STATUS,
        "backup_verified": backup_verified,
        "source_template_unchanged": source_template_unchanged,
        "save_integrity_verified": save_integrity_verified,
        "rollback_ready": rollback_ready,
        "load_only_success": load_only_success,
        "spawn_ready": False,
        "confirmations": confirmations,
        "errors": sorted(set(errors)),
        "unknowns": sorted(set(unknowns)),
        "next_stage_allowed": load_only_success,
        "next_stage_scope": "SEPARATE_RESEARCH_ONLY" if load_only_success else "BLOCKED",
    }


def audit_pe(path: str | Path) -> dict:
    """Return machine/imports without loading or executing a PE file."""
    data = Path(path).read_bytes()
    if data[:2] != b"MZ" or len(data) < 0x40:
        raise Stage10Error("not_pe")
    pe = int.from_bytes(data[0x3C:0x40], "little")
    if data[pe:pe + 4] != b"PE\0\0":
        raise Stage10Error("not_pe")
    machine = int.from_bytes(data[pe + 4:pe + 6], "little")
    sections_count = int.from_bytes(data[pe + 6:pe + 8], "little")
    optional_size = int.from_bytes(data[pe + 20:pe + 22], "little")
    optional = pe + 24
    magic = int.from_bytes(data[optional:optional + 2], "little")
    directory = optional + (112 if magic == 0x20B else 96)
    import_rva = int.from_bytes(data[directory + 8:directory + 12], "little")
    sections_at = optional + optional_size
    sections = []
    for index in range(sections_count):
        at = sections_at + index * 40
        virtual_size = int.from_bytes(data[at + 8:at + 12], "little")
        virtual = int.from_bytes(data[at + 12:at + 16], "little")
        raw_size = int.from_bytes(data[at + 16:at + 20], "little")
        raw = int.from_bytes(data[at + 20:at + 24], "little")
        sections.append((virtual, max(virtual_size, raw_size), raw))

    def offset(rva: int) -> int:
        for virtual, size, raw in sections:
            if virtual <= rva < virtual + size:
                return raw + rva - virtual
        raise Stage10Error("pe_rva_unmapped")

    imports = []
    if import_rva:
        at = offset(import_rva)
        while data[at:at + 20] != bytes(20):
            name_rva = int.from_bytes(data[at + 12:at + 16], "little")
            name_at = offset(name_rva)
            end = data.index(0, name_at)
            imports.append(data[name_at:end].decode("ascii", errors="replace"))
            at += 20
    return {"machine": f"0x{machine:04x}", "magic": f"0x{magic:03x}",
            "imports": sorted(set(imports), key=str.lower), "sha256": sha256(path)}
