"""Stage 10.10.1 recovery primitives. No implicit game paths or operations.

The CLI is dry-run by default. Backup and quarantine need separate authorization.
Quarantine copies, verifies, journals and then unlinks ONE attributed file; never
removes a directory. A failure leaves its journal and requires human review.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import stat

from .compatibility import file_hash, fingerprint


class RecoveryError(ValueError):
    pass


ACTIONS = {"KEEP", "BACKUP_ONLY", "QUARANTINE", "STEAM_REPAIR", "MANUAL_REVIEW", "UNKNOWN"}
FLAGS = dict(cleanup_executed=False, clean_baseline_confirmed=False,
             installation_ready=False, runtime_status="NOT_EXECUTED",
             RUNTIME_RENDER_CONFIRMED="UNKNOWN", spawn_ready=False)


def steam_identity(path):
    """Select public build identifiers; never return LastOwner/account metadata."""
    raw = path.read_text(encoding='utf-8-sig')
    build = re.search(r'"buildid"\s+"(\d+)"', raw)
    depot = re.search(r'"1203621"\s*\{[^}]*"manifest"\s+"(\d+)"', raw)
    if not build or not depot:
        raise RecoveryError('STEAM_IDENTITY_UNAVAILABLE')
    return {'steam_build_id': build[1], 'depot_manifest': depot[1]}


def no_links(path: Path):
    """Check the root itself and every existing ancestor, including reparse tags."""
    path = path.absolute()
    for p in (path, *path.parents):
        if p.is_symlink():
            raise RecoveryError("REPARSE_POINT")
        try:
            s = p.lstat()
        except FileNotFoundError:
            continue
        if getattr(s, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RecoveryError("REPARSE_POINT")
        if stat.S_ISREG(s.st_mode) and s.st_nlink != 1:
            raise RecoveryError("HARDLINK_REFUSED")


def target(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative
            or PurePosixPath(relative).is_absolute()
            or any(p in ("", ".", "..") or p.endswith((".", " ")) for p in relative.split("/"))):
        raise RecoveryError("INVALID_PATH")
    for part in relative.split("/"):
        if part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(10)], *[f"LPT{i}" for i in range(10)]}:
            raise RecoveryError("INVALID_PATH")
    p = root.absolute() / relative
    no_links(p)
    if not p.resolve().is_relative_to(root.resolve()):
        raise RecoveryError("PATH_ESCAPE")
    return p


def measure(path: Path) -> dict:
    no_links(path)
    a = path.stat()
    if not path.is_file():
        raise RecoveryError("NOT_A_FILE")
    sha = file_hash(path)
    b = path.stat()
    if (a.st_size, a.st_mtime_ns, a.st_ino) != (b.st_size, b.st_mtime_ns, b.st_ino):
        raise RecoveryError("SOURCE_CHANGED")
    return {"sha256": sha, "size": b.st_size}


def match(path: Path, entry: dict):
    if measure(path) != {"sha256": entry["sha256"], "size": entry["size"]}:
        raise RecoveryError("HASH_OR_SIZE_MISMATCH:" + path.name)


def inventory(root: Path) -> dict:
    no_links(root)
    if not root.is_dir():
        raise RecoveryError("ROOT_MISSING")
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(base) / name
            no_links(p)
            if p.is_file():
                result[p.relative_to(root).as_posix()] = measure(p)
    return result


def validate_manifest(plan: dict, roots: dict[str, Path], identity: dict,
                      stopped: bool, receipt_sha256: str):
    if stopped is not True:
        raise RecoveryError("GAME_NOT_CONFIRMED_STOPPED")
    if plan.get("format") != "aic_recovery_plan_v1" or not plan.get("entries"):
        raise RecoveryError("INVALID_MANIFEST")
    if not identity or identity != plan.get("game_identity"):
        raise RecoveryError("BUILD_MISMATCH")
    if receipt_sha256 != plan.get("receipt_sha256"):
        raise RecoveryError("RECEIPT_MISMATCH")
    if set(roots) != set(plan.get("roots", {})):
        raise RecoveryError("ROOT_MISMATCH")
    for key, root in roots.items():
        no_links(root)
        if root.resolve() != Path(plan["roots"][key]).resolve():
            raise RecoveryError("ROOT_MISMATCH")
    seen = set()
    for e in plan["entries"]:
        k = (e["root"], e["relative_path"].casefold())
        if k in seen or e["root"] not in roots or e["proposed_action"] not in ACTIONS:
            raise RecoveryError("INVALID_ENTRY")
        seen.add(k)
        p = target(roots[e["root"]], e["relative_path"])
        if p.absolute() != Path(e["absolute_path"]).absolute():
            raise RecoveryError("ABSOLUTE_PATH_MISMATCH")
        if e["proposed_action"] == "QUARANTINE":
            # Game resources (including empty DATs), executables and saves are
            # never eligible for this tool, even if somebody edits the plan.
            if (e["root"] != "game" or p.suffix.lower() in {".dat", ".kfc", ".kfc_resources", ".exe", ".ksd"}
                    or p.name.lower().endswith(".kfc.bak") or e["artifact_owner"] not in {"EMF", "EML", "AIC"}
                    or e["confidence"] != "HASH_CONFIRMED" or not e["source_of_attribution"]
                    or e.get("backup_required") is not True):
                raise RecoveryError("UNKNOWN_OR_PROTECTED_TARGET")
        match(p, e)
    # Detect extra files, not merely modifications of the known ones.
    for key, root in roots.items():
        expected = {e["relative_path"]: {"sha256": e["sha256"], "size": e["size"]}
                    for e in plan["entries"] if e["root"] == key}
        if inventory(root) != expected:
            raise RecoveryError("INVENTORY_CHANGED")


def backup_entries(plan):
    return [e for e in plan["entries"] if e["backup_required"]]


def external_destination(dest: Path, roots: dict, *, fresh=True):
    no_links(dest)
    for root in roots.values():
        if dest.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(dest.resolve()):
            raise RecoveryError("DESTINATION_OVERLAPS_SOURCE")
    if fresh and dest.exists():
        raise RecoveryError("DESTINATION_EXISTS")
    if not dest.parent.is_dir():
        raise RecoveryError("DESTINATION_PARENT_MISSING")


def write_json_new(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def create_backup(plan, roots, dest, *, authorize=False, preflight):
    if authorize is not True:
        raise RecoveryError("BACKUP_NOT_AUTHORIZED")
    live = preflight()
    validate_manifest(plan, roots, **live)
    external_destination(dest, roots)
    entries = backup_entries(plan)
    needed = sum(e["size"] for e in entries) + plan["receipt_size"] + 16 * 1024 * 1024
    if shutil.disk_usage(dest.parent).free < needed:
        raise RecoveryError("INSUFFICIENT_SPACE")
    dest.mkdir()
    # Includes ALL DAT digests even though their bodies are intentionally omitted.
    write_json_new(dest / "plan.json", plan)
    receipt = Path(plan["receipt_path"])
    receipt_entry = {"sha256": plan["receipt_sha256"], "size": plan["receipt_size"]}
    match(receipt, receipt_entry)
    with receipt.open("rb") as src, (dest / "install-receipt.json").open("xb") as out:
        shutil.copyfileobj(src, out)
    match(dest / "install-receipt.json", receipt_entry)
    for e in entries:
        check_live(plan, preflight())
        src = target(roots[e["root"]], e["relative_path"])
        match(src, e)
        out = target(dest, e["root"] + "/" + e["relative_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as inp, out.open("xb") as stream:
            shutil.copyfileobj(inp, stream, 4 * 1024 * 1024)
            stream.flush()
            os.fsync(stream.fileno())
        match(out, e)
        match(src, e)
    check_live(plan, preflight())
    record = {"format": "aic_recovery_backup_v1", "plan_sha256": fingerprint(plan),
              "game_identity": plan["game_identity"], "created_utc": datetime.now(timezone.utc).isoformat(),
              "entries": [dict(e, backup_path=str(target(dest, e['root'] + '/' + e['relative_path']))) for e in entries],
              "restore_policy": "EXACT_PATH_BUILD_REVIEW_ONLY_NO_AUTOMATIC_RESTORE",
              "full_mixed_state_restore": False}
    write_json_new(dest / "manifest.json", record)
    verify_backup(plan, dest)
    return record


def verify_backup(plan, dest):
    no_links(dest / "manifest.json")
    saved_plan = json.loads(target(dest, "plan.json").read_text(encoding="utf-8"))
    if saved_plan != plan:
        raise RecoveryError("BACKUP_PLAN_MISMATCH")
    record = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    if (record.get("format") != "aic_recovery_backup_v1" or record.get("plan_sha256") != fingerprint(plan)
            or record.get("game_identity") != plan["game_identity"]
            or record.get("entries") != [dict(e, backup_path=str(target(dest, e['root'] + '/' + e['relative_path'])))
                                          for e in backup_entries(plan)]):
        raise RecoveryError("BACKUP_MANIFEST_MISMATCH")
    for e in record["entries"]:
        match(target(dest, e["root"] + "/" + e["relative_path"]), e)
    match(target(dest, "install-receipt.json"),
          {"sha256": plan["receipt_sha256"], "size": plan["receipt_size"]})
    return record


def check_live(plan, live):
    if live.get("stopped") is not True:
        raise RecoveryError("GAME_NOT_CONFIRMED_STOPPED")
    if live.get("identity") != plan["game_identity"]:
        raise RecoveryError("BUILD_MISMATCH")
    if live.get("receipt_sha256") != plan["receipt_sha256"]:
        raise RecoveryError("RECEIPT_MISMATCH")


def quarantine(plan, roots, backup, dest, *, authorize=False, preflight):
    if authorize is not True:
        raise RecoveryError("CLEANUP_NOT_AUTHORIZED")
    validate_manifest(plan, roots, **preflight())
    verify_backup(plan, backup)
    external_destination(dest, roots)
    if dest.resolve().is_relative_to(backup.resolve()) or backup.resolve().is_relative_to(dest.resolve()):
        raise RecoveryError("DESTINATION_OVERLAPS_BACKUP")
    entries = [e for e in plan["entries"] if e["proposed_action"] == "QUARANTINE"]
    if shutil.disk_usage(dest.parent).free < sum(e["size"] for e in entries) + 1024 * 1024:
        raise RecoveryError("INSUFFICIENT_SPACE")
    dest.mkdir()
    # Journal is append-only. No retry, auto-resume, or reverse writes on failure.
    with (dest / "journal.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        def event(e, state):
            log.write(json.dumps({"relative_path": e["relative_path"], "sha256": e["sha256"],
                                  "state": state, "plan_sha256": fingerprint(plan)}) + "\n")
            log.flush()
            os.fsync(log.fileno())
        for e in entries:
            # Full inventory preflight cannot run after the first unlink. The
            # caller repeats live process/build/receipt guards here instead.
            src = target(roots[e["root"]], e["relative_path"])
            match(src, e)
            match(target(backup, e["root"] + "/" + e["relative_path"]), e)
            out = target(dest, e["relative_path"])
            out.parent.mkdir(parents=True, exist_ok=True)
            with src.open("rb") as inp, out.open("xb") as stream:
                shutil.copyfileobj(inp, stream, 4 * 1024 * 1024)
                stream.flush()
                os.fsync(stream.fileno())
            match(out, e)
            event(e, "COPIED_VERIFIED_SOURCE_PRESENT")
            check_live(plan, preflight())
            match(src, e)
            src.unlink()
            event(e, "QUARANTINED")
    return len(entries)


BASELINE_KEYS = ("build", "recovery_source", "fresh_inventory", "official_resources",
                 "no_old_loaders", "no_old_patch_observer", "no_custom_clone", "no_unknown_changes",
                 "no_guid_npc_collision", "local_saves_intact")


def clean_baseline(evidence: dict):
    """Only evidence with a provenance source may pass; Steam's dialog is insufficient."""
    checks = {k: evidence.get(k, {}) for k in BASELINE_KEYS}
    failed = [k for k, v in checks.items() if v.get("status") == "FAIL"]
    passed = [k for k, v in checks.items() if v.get("status") == "PASS" and v.get("source")]
    status = ("CLEAN_BASELINE_FAILED" if failed else "CLEAN_BASELINE_CONFIRMED"
              if len(passed) == len(checks) and evidence.get("independent_depot_hashes") is True
              else "CLEAN_BASELINE_PARTIAL" if passed else "CLEAN_BASELINE_UNKNOWN")
    return {"status": status, "failed": failed, "unknown": sorted(set(checks) - set(passed) - set(failed)),
            "independent_depot_hashes": evidence.get("independent_depot_hashes") is True,
            **FLAGS}  # Phase A never authorizes cleanup/install/spawn.


def content_owner(facts: dict):
    owners = [k for k in ("standalone", "integrated") if facts.get(k) is True]
    if len(owners) != 1:
        raise RecoveryError("CONTENT_OWNER_CONFLICT" if owners else "CONTENT_OWNER_MISSING")
    owner = owners[0]
    for key in ("reflection_supported", "evidence_available"):
        if facts.get(key) is not True:
            raise RecoveryError(key.upper())
    if owner == "integrated":
        for key in ("shadow_path_valid", "private_indexes", "dat_writer_unlinks_first"):
            if facts.get(key) is not True:
                raise RecoveryError(key.upper())
        if facts.get("requires_export") is True:
            raise RecoveryError("EXPORT_UNAVAILABLE")
    elif facts.get("export_available") is not True:
        raise RecoveryError("EXPORT_UNAVAILABLE")
    return {"recommended_owner": owner, **FLAGS}
