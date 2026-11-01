"""Stage 10.7 evidence v4 validation.  Offline and side-effect free."""
from __future__ import annotations

import re
from typing import Any

from .eml_humanoid import EXPECTED_NPC_ID, SOURCE_TEMPLATE_GUID, TEMPLATE_GUID
from .stage10_6 import evaluate_visual_load as evaluate_v3
from .visual_fingerprint import CHARACTER_SETUP_FIELDS

FORMAT = "aic_eml_humanoid_evidence_v4"
V3_FORMAT = "aic_eml_humanoid_evidence_v3"
RUN_TOKEN = re.compile(r"^[0-9a-f]{32}$")
UINT32_MAX = 0xFFFFFFFF
HASH_FIELDS = tuple(x for x in CHARACTER_SETUP_FIELDS if x not in {"gender", "useNewProportions"})
VALID_PROVENANCE = {"SOURCE_EML_REFLECTION", "CLONE_EML_REFLECTION"}


class EvidenceV4Error(ValueError):
    pass


def decode_hashkey32(value: Any, provenance: str) -> dict[str, Any]:
    """Validate an already reflected UInt32; never coerce or substitute it."""
    if value is None:
        return {"status": "MISSING", "type": "HashKey32", "value": None, "provenance": provenance}
    if isinstance(value, bool) or not isinstance(value, int):
        return {"status": "UNSUPPORTED", "type": "HashKey32", "value": None, "provenance": provenance}
    if not 0 <= value <= UINT32_MAX:
        return {"status": "INVALID", "type": "HashKey32", "value": None, "provenance": provenance}
    if provenance not in VALID_PROVENANCE:
        return {"status": "INVALID", "type": "HashKey32", "value": value, "provenance": provenance}
    return {"status": "CONFIRMED", "type": "HashKey32", "value": value, "provenance": provenance}


def parse_evidence(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line or "=" not in line:
            raise EvidenceV4Error("malformed_line")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[a-z0-9_]+", key) or key in result:
            raise EvidenceV4Error("duplicate_or_invalid_key")
        result[key] = value
    return result


def _bool(value: str | None) -> bool | None:
    return True if value == "true" else False if value == "false" else None


def _key(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _hash_gate(e: dict[str, str]) -> tuple[bool, dict[str, bool]]:
    checks: dict[str, bool] = {}
    for name in HASH_FIELDS:
        key = _key(name)
        sp = e.get(f"source_{key}_provenance", "")
        cp = e.get(f"clone_{key}_provenance", "")
        sv, cv = e.get(f"source_{key}_value", ""), e.get(f"clone_{key}_value", "")
        try:
            si, ci = int(sv), int(cv)
        except ValueError:
            si = ci = -1
        checks[name] = all((e.get(f"source_{key}_status") == "CONFIRMED",
                            e.get(f"clone_{key}_status") == "CONFIRMED",
                            e.get(f"source_{key}_type") == "HashKey32",
                            e.get(f"clone_{key}_type") == "HashKey32",
                            decode_hashkey32(si, sp)["status"] == "CONFIRMED",
                            decode_hashkey32(ci, cp)["status"] == "CONFIRMED",
                            si == ci))
    checks["no_unsupported_fields"] = e.get("hashkey32_unsupported_fields", "") == ""
    checks["method"] = e.get("hashkey32_extraction_method") == "EML_MAPPED_STRUCT_VALUE_UINT32"
    return all(checks.values()), checks


def evaluate(evidence_text: str | None, *, observer=None, game_report=None, integrity=None) -> dict[str, Any]:
    empty = {"A": None, "H": None, "R": None, "V": None, "B": None, "C": None}
    if evidence_text is None:
        return {"status": "NOT_EXECUTED", "levels": empty, "spawn_ready": False,
                "errors": [], "unknowns": ["runtime_evidence_absent"]}
    try:
        e = parse_evidence(evidence_text)
    except EvidenceV4Error as exc:
        return {"status": "FAILED", "levels": {**empty, "A": False}, "spawn_ready": False,
                "errors": [str(exc)], "unknowns": []}
    if e.get("format") == V3_FORMAT:
        old = evaluate_v3(evidence_text, observer=observer, game_report=game_report, integrity=integrity)
        return {**old, "status": "V3_COMPATIBILITY_ONLY", "levels": {"A": old["levels"]["A"],
                "H": False, "R": False, "V": old["levels"]["V"], "B": old["levels"]["B"],
                "C": old["levels"]["C"]}, "spawn_ready": False,
                "unknowns": old.get("unknowns", []) + ["v4_hash_and_registration_absent"]}
    token = e.get("run_token", "")
    a = {
        "format": e.get("format") == FORMAT,
        "patch_applied": _bool(e.get("patch_applied")) is True,
        "guid": e.get("template_guid") == TEMPLATE_GUID,
        "npc_id": e.get("npc_id") == str(EXPECTED_NPC_ID),
        "faction": e.get("faction") == "PlayerAlly",
        "source": e.get("source_guid") == SOURCE_TEMPLATE_GUID and _bool(e.get("source_unchanged")) is True,
        "token": bool(RUN_TOKEN.fullmatch(token)),
        "writer": bool(observer and observer.get("writer_finalized") is True and observer.get("run_token") == token),
    }
    h_pass, h = _hash_gate(e)
    r = {
        "created": e.get("resource_created") == "CONFIRMED",
        "serialized": bool(observer and observer.get("writer_finalized") is True),
        "registry": e.get("guid_registry_status") in {"NOT_REQUIRED", "CONFIRMED"},
        "lookup_available": e.get("template_lookup_available") == "true",
        "lookup_confirmed": e.get("template_lookup_confirmed") == "true",
        "lookup_method": e.get("template_lookup_method") == "EML_ASSET_MANAGER_GET_RESOURCE",
        "identity": all((e.get("lookup_guid") == TEMPLATE_GUID,
                         e.get("lookup_resource_type") == "keen::ecs::TemplateResource",
                         e.get("lookup_component_count") == e.get("component_count"),
                         e.get("lookup_fingerprint") == e.get("fingerprint_hash"))),
    }
    required = {"keen::ecs::CharacterSetup", "keen::ecs::RenderEquipment",
                "keen::ecs::AnimationGraphResourceComponent2", "keen::ecs::ForceSave", "keen::ecs::ActiveNpcState"}
    comps = set(filter(None, e.get("components", "").split(",")))
    source_comps = set(filter(None, e.get("source_components", "").split(",")))
    v = {"structural": required <= comps and comps == source_comps,
         "character_setup": h_pass and _bool(e.get("character_setup_match")) is True,
         "animation": e.get("animation_graph_guid") == e.get("source_animation_graph_guid") not in {None, ""},
         "references": _bool(e.get("visual_references_match")) is True,
         "dependencies": _bool(e.get("visual_dependencies_resolved")) is True}
    b = None if game_report is None or integrity is None else all((
        game_report.get("local_test_world_loaded") is True, game_report.get("resource_errors") == [],
        game_report.get("game_errors") == [], integrity.get("source_unchanged") is True))
    c = None if observer is None else all((observer.get("read_only") is True,
        observer.get("spawn_forbidden") is True, observer.get("run_token") == token,
        observer.get("bridge_available") is True, observer.get("truncated") is False))
    levels = {"A": all(a.values()), "H": h_pass, "R": all(r.values()), "V": all(v.values()), "B": b, "C": c}
    errors = [f"{gate}:{name}" for gate, checks in (("A", a), ("H", h), ("R", r), ("V", v))
              for name, ok in checks.items() if not ok]
    success = all(value is True for value in levels.values())
    return {"status": "LOAD_ONLY_SUCCESS" if success else "FAILED", "levels": levels,
            "checks": {"A": a, "H": h, "R": r, "V": v}, "spawn_ready": False,
            "errors": errors, "unknowns": ([] if b is not None else ["game_load_not_evaluated"]) +
            ([] if c is not None else ["observer_not_evaluated"])}
