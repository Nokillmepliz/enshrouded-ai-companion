"""Fail-closed visual fingerprint v2 for an EML humanoid clone."""
from __future__ import annotations
import hashlib, json, re
from typing import Any

VISUAL_COMPONENTS = ("keen::ecs::RenderEquipment", "keen::ecs::CharacterSetup",
 "keen::ecs::NewCharacterSetup", "keen::ecs::EquipmentCheck", "keen::ecs::InventorySetup",
 "keen::ecs::AnimationGraphResourceComponent2")
CHARACTER_SETUP_FIELDS = ("gender", "voicePackId", "presetId", "hair", "beard",
 "hairColorId", "beardColorId", "skinColor", "eyeBrowColor", "eyeColor",
 "useNewProportions")
EVIDENCE_STATUSES = frozenset({"CONFIRMED", "MISSING", "UNKNOWN", "UNSUPPORTED"})
PROVENANCE = frozenset({"SOURCE_KFC_VERIFIED", "CLONE_EML_VERIFIED",
 "RESOURCE_EXISTENCE_VERIFIED", "RUNTIME_RENDER_UNKNOWN"})
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)

class VisualFingerprintError(ValueError): pass
def canonical_fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
def _components(value):
    result = value.get("components")
    if not isinstance(result, list) or not all(isinstance(x, str) for x in result):
        raise VisualFingerprintError("invalid_components")
    return set(result)
def _setup(value):
    setup = value.get("character_setup")
    if setup is None: return None
    if not isinstance(setup, dict) or set(setup) != set(CHARACTER_SETUP_FIELDS):
        raise VisualFingerprintError("invalid_character_setup_fields")
    for name, field in setup.items():
        if not isinstance(field, dict) or field.get("status") not in EVIDENCE_STATUSES:
            raise VisualFingerprintError(f"invalid_character_setup_status:{name}")
        if field["status"] == "CONFIRMED" and ("value" not in field or not field.get("type")):
            raise VisualFingerprintError(f"confirmed_character_setup_without_value:{name}")
    return setup
def _references(value):
    if value.get("resource_references_complete") is not True: return None
    references = value.get("resource_references")
    if not isinstance(references, list) or not references:
        raise VisualFingerprintError("complete_references_must_be_nonempty")
    result = []
    for item in references:
        guid = item.get("guid") if isinstance(item, dict) else item
        if not isinstance(guid, str) or not GUID.fullmatch(guid):
            raise VisualFingerprintError("invalid_resource_reference")
        result.append(guid.lower())
    return tuple(sorted(result))
def assess_visual_pair(source, clone, *, resolved=None):
    sc, cc = _components(source), _components(clone); required = set(VISUAL_COMPONENTS)
    structural = (sc & required) == required and (cc & required) == required
    ss, cs = _setup(source), _setup(clone)
    setup_match = None if ss is None or cs is None else all(
        ss[n].get("status") == cs[n].get("status") == "CONFIRMED"
        and ss[n].get("type") == cs[n].get("type")
        and ss[n].get("value") == cs[n].get("value") for n in CHARACTER_SETUP_FIELDS)
    sr, cr = _references(source), _references(clone)
    refs_match = None if sr is None or cr is None else sr == cr
    deps = None
    if refs_match is True and resolved is not None:
        deps = set(resolved) == set(sr) and all(resolved.values())
    contract = {"format":"aic_visual_fingerprint_v2",
      "source_template_guid":source.get("template_guid"), "clone_template_guid":clone.get("template_guid"),
      "visual_components":sorted(sc & required), "levels":{"STRUCTURAL_MATCH":structural,
      "CHARACTER_SETUP_MATCH":setup_match, "RESOURCE_REFERENCES_MATCH":refs_match,
      "VISUAL_DEPENDENCIES_RESOLVED":deps, "RUNTIME_RENDER_CONFIRMED":None},
      "provenance":sorted(PROVENANCE), "spawn_ready":False}
    contract["canonical_sha256"] = canonical_fingerprint(contract)
    return contract
