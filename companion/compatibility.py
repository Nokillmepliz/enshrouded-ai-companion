"""Offline compatibility contracts. No transport, installation or game effects.

Profiles identify observations, not permission to run. Historical manifests are
readable but cannot authorize restoration without build and baseline identities.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re


class CompatibilityError(ValueError):
    pass


SECTIONS = tuple("GAME_VERSION GAME_FILE_INVENTORY BACKUP_COMPATIBILITY EMF_COMPATIBILITY "
                 "EML_COMPATIBILITY ECS_DIFF RESOURCE_DIFF CHARACTER_SETUP BRIDGE_COMPATIBILITY "
                 "PATCH_COMPATIBILITY STAGE10_9_REVALIDATION OFFLINE_TESTS INSTALL_READINESS "
                 "RUNTIME_STATUS".split())
SECTION_FIELDS = {"status", "expected", "observed", "source", "provenance", "identity",
                  "error", "unknowns", "runtime_validation_required"}
SHA = re.compile(r"[0-9a-f]{64}\Z")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fingerprint(value) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=True).encode())


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    p = PurePosixPath(relative)
    if p.is_absolute() or any(x in (".", "..") for x in relative.split("/")):
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    base = root.resolve()
    result = base.joinpath(*p.parts)
    for parent in (result, *result.parents):
        if parent == base:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    if not result.resolve().is_relative_to(base):
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    return result


def load_profile(build: int, directory: Path | None = None) -> dict:
    if type(build) is not int:
        raise CompatibilityError("UNSUPPORTED_GAME_BUILD")
    root = directory or Path(__file__).resolve().parents[1] / "compatibility/profiles"
    try:
        index = json.loads((root / "index.json").read_text(encoding="utf-8"))
        expected = index.get(str(build))
        if not isinstance(expected, str) or not SHA.fullmatch(expected):
            raise CompatibilityError("UNSUPPORTED_GAME_BUILD")
        raw = (root / f"{build}.json").read_bytes()
        if digest_bytes(raw) != expected:
            raise CompatibilityError("PROFILE_HASH_MISMATCH")
        profile = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityError("PROFILE_MISSING_OR_INVALID") from exc
    if profile.get("game_build") != build or not SHA.fullmatch(profile.get("exe_sha256", "")):
        raise CompatibilityError("PROFILE_IDENTITY_MISMATCH")
    return profile


def detect_build(exe_sha256: str | None, profiles: list[dict], *,
                 metadata_build: int | None = None, steam_build: str | None = None) -> dict:
    if exe_sha256 is None:
        raise CompatibilityError("GAME_EXECUTABLE_MISSING")
    matches = [p for p in profiles if p.get("exe_sha256") == exe_sha256]
    if len(matches) != 1:
        raise CompatibilityError("UNSUPPORTED_GAME_BUILD")
    result = matches[0]
    if metadata_build is not None and metadata_build != result["game_build"]:
        raise CompatibilityError("BUILD_METADATA_MISMATCH")
    if steam_build is not None and steam_build != result.get("steam_build_id"):
        raise CompatibilityError("STEAM_BUILD_ID_MISMATCH")
    return result


def classify_file(current: str | None, previous: str | None, *,
                  artifact: str | None = None, official: str | None = None) -> str:
    """official must be a per-file digest, not a depot number or filename guess."""
    if current is None:
        return "MISSING"
    if official is not None and current == official and current != previous:
        return "UPDATED_BY_GAME"
    if artifact is not None and current == artifact:
        return "PREVIOUS_MOD_ARTIFACT"
    if previous == current:
        return "UNCHANGED"
    if previous is None and artifact is None:
        return "NEW"
    return "MODIFIED_UNKNOWN"


def baseline_identity(game_identity: dict, hashes: dict[str, str]) -> str:
    return fingerprint({"game_identity": game_identity, "game_data": hashes})


def validate_rollback_identity(current: dict, record: dict, baseline: dict) -> None:
    recorded = record.get("game_identity")
    # Legacy build fields can prove a mismatch, but never prove an identity.
    recorded_build = recorded.get("game_build") if isinstance(recorded, dict) else record.get("game_build")
    if recorded_build is not None and recorded_build != current.get("game_build"):
        raise CompatibilityError("ROLLBACK_BLOCKED_BUILD_MISMATCH")
    if recorded is not None and recorded != current:
        raise CompatibilityError("ROLLBACK_BLOCKED_BUILD_MISMATCH")
    if not recorded or not current.get("exe_sha256") or not current.get("game_build"):
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    if baseline.get("game_identity") != current:
        raise CompatibilityError("ROLLBACK_BLOCKED_BUILD_MISMATCH")
    hashes = baseline.get("game_data_hashes")
    if (not isinstance(hashes, dict) or not hashes or
            any(not isinstance(v, str) or not SHA.fullmatch(v) for v in hashes.values())):
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    expected = baseline_identity(current, hashes)
    if baseline.get("baseline_identity") != expected or record.get("baseline_identity") != expected:
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT:stale_baseline")


def validate_targets(game: Path, expected: dict[str, str]) -> None:
    if not isinstance(expected, dict) or not expected:
        raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
    for relative, sha in expected.items():
        target = safe_target(game, relative)
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise CompatibilityError("ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT")
        if not target.is_file() or file_hash(target) != sha:
            raise CompatibilityError("ROLLBACK_BLOCKED_FILE_MISMATCH:" + relative)


def check_runtime_contract(profile: dict, observed: dict, *, experimental_approved=False) -> list[str]:
    errors = []
    for name in ("emf_version", "eml_version", "lua_api", "native_api", "bridge_protocol", "schema"):
        if observed.get(name) != profile.get(name) or profile.get(name) is None:
            errors.append(name + "_mismatch")
    if observed.get("experimental") and not experimental_approved:
        errors.append("experimental_release_unapproved")
    if observed.get("compatibility") not in ("SUPPORTED",):
        errors.append("compatibility_unconfirmed")
    if not set(profile.get("required_api", ())).issubset(observed.get("available_api", ())):
        errors.append("required_api_missing")
    return errors


def compare_schema(old: dict | None, new: dict | None) -> str:
    if old is None:
        return "ADDED" if new is not None else "UNKNOWN"
    if new is None:
        return "REMOVED"
    required = {"hash", "size", "fields"}
    if not required.issubset(old) or not required.issubset(new):
        return "UNKNOWN"
    if old["hash"] != new["hash"]:
        return "TYPE_ID_CHANGED"
    if old["size"] != new["size"] or old.get("alignment") != new.get("alignment"):
        return "LAYOUT_CHANGED"
    if old["fields"] != new["fields"] or old.get("enums") != new.get("enums"):
        return "FIELDS_CHANGED"
    return "IDENTICAL"


def validate_template(expected: dict, observed: dict) -> list[str]:
    errors = []
    for key in ("source_guid", "component_count", "component_fingerprint", "animation_graph"):
        if key not in observed or observed[key] != expected.get(key):
            errors.append(key + "_mismatch")
    for key in ("custom_guid_collision", "npc_id_collision"):
        if observed.get(key) is not False:
            errors.append(key)
    for key in ("visual_references_valid", "dependencies_valid", "source_integrity"):
        if observed.get(key) is not True:
            errors.append(key)
    return errors


def validate_hashkeys(source: dict, clone: dict, expected: dict) -> list[str]:
    errors = []
    for name, value in expected.items():
        pair = [source.get(name), clone.get(name)]
        if any(not isinstance(p, dict) or p.get("type") != "HashKey32" or
               p.get("reflection") != "MappedStructValue.value" or
               type(p.get("value")) is not int or not 0 <= p["value"] <= 0xffffffff for p in pair):
            errors.append(name + ":unsupported_typed_value")
        elif pair[0]["value"] != pair[1]["value"]:
            errors.append(name + ":source_clone_mismatch")
        elif pair[0]["value"] != value:
            errors.append(name + ":profile_value_changed")
    return errors


def validate_observer_capture(command: str, response: dict, *, profile: dict,
                              run_token: str, session: str) -> list[str]:
    """Project capture envelope, NOT new fields claimed to exist on EMF's wire.

    A future collector must bind handshake/world/session and observer reply into
    this envelope. This function opens no pipe and cannot send a command.
    """
    if command not in ("status", "inspect", "compare"):
        return ["mutation_command_rejected"]
    expected = {"protocol": profile["bridge_protocol"], "game_build": profile["game_build"],
                "response_version": 1, "session": session, "run_token": run_token,
                "command": command, "read_only": True, "spawn_forbidden": True}
    return [key + "_mismatch" for key, value in expected.items()
            if type(response.get(key)) is not type(value) or response.get(key) != value]


def make_evidence(identity: dict, observations: dict) -> dict:
    sections = {}
    for name in SECTIONS:
        value = observations.get(name, {})
        sections[name] = {"status": "UNKNOWN", "expected": None, "observed": None,
                          "source": [], "provenance": "not_collected", "identity": identity,
                          "error": "not_collected", "unknowns": [name],
                          "runtime_validation_required": True, **value}
    return {"format": "aic_game_compatibility_evidence_v7", "phase": "A", "sections": sections,
            "installation_ready": False, "runtime_status": "NOT_EXECUTED",
            "RUNTIME_RENDER_CONFIRMED": "UNKNOWN", "spawn_ready": False}


def validate_evidence(value: dict) -> list[str]:
    errors = []
    expected = {"format": "aic_game_compatibility_evidence_v7", "phase": "A",
                "installation_ready": False, "runtime_status": "NOT_EXECUTED",
                "RUNTIME_RENDER_CONFIRMED": "UNKNOWN", "spawn_ready": False}
    for key, item in expected.items():
        if type(value.get(key)) is not type(item) or value.get(key) != item:
            errors.append(key)
    sections = value.get("sections")
    if not isinstance(sections, dict) or set(sections) != set(SECTIONS):
        return errors + ["sections"]
    for name, section in sections.items():
        if not isinstance(section, dict) or not SECTION_FIELDS.issubset(section):
            errors.append(name + ":missing_fields")
            continue
        if (section["status"] not in ("PASS", "FAIL", "UNKNOWN", "BLOCKED", "NOT_EXECUTED") or
                type(section["runtime_validation_required"]) is not bool or
                not isinstance(section["unknowns"], list) or not isinstance(section["source"], list) or
                not isinstance(section["identity"], dict) or not section["provenance"]):
            errors.append(name + ":invalid_fields")
        if section["status"] == "PASS" and (section["unknowns"] or section["error"] or not section["source"]):
            errors.append(name + ":unsupported_pass")
    return errors
