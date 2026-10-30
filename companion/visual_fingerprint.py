"""Fail-closed offline contract for a future humanoid visual fingerprint.

The Stage 10 evaluator does not consume this contract yet. It describes only
confirmed component names and never treats structural equality as rendered
model proof.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


VISUAL_COMPONENTS = (
    "keen::ecs::RenderEquipment",
    "keen::ecs::CharacterSetup",
    "keen::ecs::NewCharacterSetup",
    "keen::ecs::EquipmentCheck",
    "keen::ecs::InventorySetup",
    "keen::ecs::AnimationGraphResourceComponent2",
)
GUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class VisualFingerprintError(ValueError):
    pass


def canonical_fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _components(value: dict[str, Any]) -> set[str]:
    components = value.get("components")
    if not isinstance(components, list) or not all(isinstance(x, str) for x in components):
        raise VisualFingerprintError("invalid_components")
    return set(components)


def _references(value: dict[str, Any]) -> tuple[str, ...] | None:
    if value.get("resource_references_complete") is not True:
        return None
    references = value.get("resource_references")
    if not isinstance(references, list) or not references:
        raise VisualFingerprintError("complete_references_must_be_nonempty")
    if not all(isinstance(item, str) and GUID.fullmatch(item) for item in references):
        raise VisualFingerprintError("invalid_resource_reference")
    return tuple(sorted(item.lower() for item in references))


def assess_visual_pair(
    source: dict[str, Any], clone: dict[str, Any], *, resolved: dict[str, bool] | None = None,
) -> dict[str, Any]:
    source_components, clone_components = _components(source), _components(clone)
    source_visual = source_components.intersection(VISUAL_COMPONENTS)
    clone_visual = clone_components.intersection(VISUAL_COMPONENTS)
    required = set(VISUAL_COMPONENTS)
    structural = source_visual == required and clone_visual == required
    structural_match = structural and source_visual == clone_visual

    source_refs, clone_refs = _references(source), _references(clone)
    if source_refs is None or clone_refs is None:
        references_match = None
    else:
        references_match = source_refs == clone_refs

    if references_match is not True or resolved is None:
        dependencies_resolved = None
    else:
        dependencies_resolved = (
            set(resolved) == set(source_refs)
            and all(resolved.get(reference) is True for reference in source_refs)
        )

    contract = {
        "format": "aic_visual_fingerprint_design_v1",
        "source_template_guid": source.get("template_guid"),
        "clone_template_guid": clone.get("template_guid"),
        "visual_components": sorted(source_visual),
        "source_resource_references": list(source_refs) if source_refs is not None else None,
        "clone_resource_references": list(clone_refs) if clone_refs is not None else None,
        "levels": {
            "STRUCTURAL_MATCH": structural_match,
            "RESOURCE_REFERENCES_MATCH": references_match,
            "VISUAL_DEPENDENCIES_RESOLVED": dependencies_resolved,
            "RUNTIME_RENDER_CONFIRMED": None,
        },
        "spawn_ready": False,
    }
    contract["canonical_sha256"] = canonical_fingerprint(contract)
    return contract
