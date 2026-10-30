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
import shutil
import stat
import subprocess
from typing import Callable

from .eml_humanoid import validate_patch


EXPECTED_BUILD = 1_273_043
EXPECTED_GAME_SHA256 = "d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882"
EXPECTED_EMF_LOADER_SHA256 = "53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee"
EXPECTED_EML_DBGHELP_SHA256 = "038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa"
EXPECTED_EMM_SHA256 = "b1133f6b8ea7000596cc7710901bd8307b48165b0e650c0487a611d90ea49305"
EVIDENCE_RELATIVE = Path("export/aic_eml_humanoid/template_evidence_v1.txt")
EXPECTED_TEMPLATE_GUID = "a1c90001-5e4d-4a91-8a1c-000000000001"
EXPECTED_SOURCE_GUID = "e3736dff-0ad2-47fc-903c-66c1775836e8"


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
    return ("manifest", "disabled_default", "read_only", "status", "inspect", "compare")


def parse_evidence(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([a-z_]+)=(.*)", line)
        if not match or match.group(1) in result:
            raise Stage10Error("evidence_malformed")
        result[match.group(1)] = match.group(2)
    return result


def evaluate_evidence(value: dict[str, str], *, writer_finalized: bool) -> dict:
    required = {
        "format": "aic_eml_humanoid_evidence_v1",
        "template_guid": EXPECTED_TEMPLATE_GUID,
        "source_guid": EXPECTED_SOURCE_GUID,
        "npc_id": "2939921867",
        "faction": "PlayerAlly",
        "component_clone": "true",
        "source_unchanged": "true",
        "resource_lookup_after_create": "true",
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
    return {"ok": all(checks.values()), "checks": checks}


def eml_log_writer_finalized(text: str) -> bool:
    ready = re.search(
        rf"AIC_EML_TEMPLATE_READY\s+{re.escape(EXPECTED_TEMPLATE_GUID)}\s+2939921867\b", text
    )
    applied = re.search(r"Applied\s+([1-9][0-9]*)\s+patches", text)
    return ready is not None and applied is not None


def preflight(
    game_dir: str | Path,
    eml_dbghelp: str | Path,
    patch_dir: str | Path,
    observer_dir: str | Path,
    *,
    expected_game_dir: str | Path | None = None,
    game_running: bool = False,
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
    if (game / "mods" / "aic_eml_humanoid").exists():
        raise Stage10Error("patch_already_installed")
    if (game / "emf" / "mods" / "aic_template_observer").exists():
        raise Stage10Error("observer_already_installed")
    if (game / EVIDENCE_RELATIVE).exists():
        raise Stage10Error("stale_evidence_present")
    patch_checks = validate_patch(patch_dir)
    observer_checks = validate_observer(observer_dir)
    if not os.access(game, os.W_OK):
        raise Stage10Error("game_directory_not_writable")
    baseline_dat = sorted(path.name for path in game.glob("enshrouded_[0-9][0-9][0-9].dat"))
    return {
        "ok": True,
        "mode": "dry_run",
        "game_dir": str(game),
        "build": EXPECTED_BUILD,
        "game_sha256": EXPECTED_GAME_SHA256,
        "emf_loader_sha256": EXPECTED_EMF_LOADER_SHA256,
        "eml_dbghelp_sha256": EXPECTED_EML_DBGHELP_SHA256,
        "patch_checks": list(patch_checks),
        "observer_checks": list(observer_checks),
        "baseline_dat": baseline_dat,
        "direct_emf_template_lookup": "UNAVAILABLE_WITHOUT_ENTITY",
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
        if data.get("verified") is not True or not data.get("entries"):
            return False
        for entry in data["entries"]:
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
    eml_dbghelp: str | Path, patch_dir: str | Path, observer_dir: str | Path
) -> list[tuple[Path | None, Path, bytes | None]]:
    patch, observer = Path(patch_dir), Path(observer_dir)
    result: list[tuple[Path | None, Path, bytes | None]] = [
        (Path(eml_dbghelp), Path("dbghelp.dll"), None),
        (None, Path("eml.json"), json.dumps({
            "enable_console": False,
            "use_export_flag": True,
            "export_directory": "export",
        }, indent=2).encode("utf-8") + b"\n"),
    ]
    for source in sorted(path for path in patch.rglob("*") if path.is_file()):
        result.append((source, Path("mods/aic_eml_humanoid") / source.relative_to(patch), None))
    for source in sorted(path for path in observer.rglob("*") if path.is_file()):
        result.append((source, Path("emf/mods/aic_template_observer") / source.relative_to(observer), None))
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
    files = installation_files(eml_dbghelp, patch_dir, observer_dir)
    for _, relative, _ in files:
        if (game / relative).exists():
            raise Stage10Error(f"installation_collision:{relative.as_posix()}")
    plan = {"mode": "apply" if apply else "dry_run", "files": [str(x[1]) for x in files], "applied": []}
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
    return {"ok": True, "receipt": str(receipt), "files": len(files)}


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
