"""Offline contract and validator for the experimental EML humanoid patch.

Nothing in this module opens Enshrouded, invokes EML, or mutates game data.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType

from .human_body import Evidence


PATCH_ID = "aic_eml_humanoid"
PATCH_VERSION = "0.2.0"
TEMPLATE_GUID = "a1c90001-5e4d-4a91-8a1c-000000000001"
SOURCE_TEMPLATE_GUID = "e3736dff-0ad2-47fc-903c-66c1775836e8"
EXPECTED_FACTION = "PlayerAlly"
EXPECTED_FACTION_ID = 11
EXPECTED_NPC_ID = 2_939_921_867


class UniquenessPolicy(str, Enum):
    SINGLE_CUSTOM_NPC = "single_custom_npc"


# Only resources established by the pinned source catalog are admitted by the
# offline validator.  This is not a dump of the installed game database.
KNOWN_RESOURCES = frozenset({SOURCE_TEMPLATE_GUID})
STORY_TEMPLATE_GUIDS = frozenset({
    "c313f0a8-ed2e-444e-8384-a540f6bbd98e",
    "04d42ed2-beb4-4013-8f10-5d63efae2015",
    "7456862b-53fe-4b94-8a75-d3079afc9323",
    "27e2fb44-4975-4b61-988d-c7b4e16ed325",
    "8045836c-0647-4a0a-9a00-7d299b4599f8",
    "31ff0824-2c28-4934-a236-d3aa5c0306b9",
    "a6db3870-a426-494e-a203-64789389e7d7",
    SOURCE_TEMPLATE_GUID,
    "1b533365-f465-42e0-a51f-7d66e9cf3659",
    "a6bab01b-a848-4645-84fb-6ae22b532eb0",
    "23a61977-ae52-443d-ab6f-23826a2cda5a",
    "ff6cd2cf-b566-482c-ba14-075d1a918b3d",
    "b61da3e5-b8f2-4933-84f8-48e7ecfcba39",
    "aa51d579-d35f-433e-be91-d4f7133d62c5",
    "f63dc05f-88ed-4f5a-9640-1d19d980bb37",
    "35afe333-75a0-45ec-90d4-5abddb08fdc5",
    "877ab652-90f8-45da-8865-70e4e0fedc57",
    "e7666cd3-e530-4f9d-9586-519e4ab969dc",
})


@dataclass(frozen=True)
class EmlHumanoidDescriptor:
    template_guid: str
    source_patch: str
    patch_version: str
    source_template_guid: str
    expected_model_guid: str | None
    expected_animation_graph_guid: str | None
    expected_faction: int
    expected_npc_id: int
    uniqueness: UniquenessPolicy
    creation_marker: str | None
    ownership_proof: str | None
    safe_dismiss_proven: bool
    capabilities: MappingProxyType
    evidence: Evidence
    runtime_enabled: bool = False


DESCRIPTOR = EmlHumanoidDescriptor(
    template_guid=TEMPLATE_GUID,
    source_patch=PATCH_ID,
    patch_version=PATCH_VERSION,
    source_template_guid=SOURCE_TEMPLATE_GUID,
    expected_model_guid=None,
    expected_animation_graph_guid=None,
    expected_faction=EXPECTED_FACTION_ID,
    expected_npc_id=EXPECTED_NPC_ID,
    uniqueness=UniquenessPolicy.SINGLE_CUSTOM_NPC,
    creation_marker=None,
    ownership_proof=None,
    safe_dismiss_proven=False,
    capabilities=MappingProxyType({
        "patch_load": Evidence.CONFIRMED,
        "spawn": Evidence.UNKNOWN,
        "moveTo": Evidence.LIKELY,
        "follow": Evidence.UNKNOWN,
        "stay": Evidence.UNKNOWN,
        "combat": Evidence.UNKNOWN,
        "inventory": Evidence.UNKNOWN,
        "equipment": Evidence.UNKNOWN,
        "dismiss": Evidence.UNKNOWN,
    }),
    evidence=Evidence.LIKELY,
)


class PatchValidationError(ValueError):
    pass


def guid_id(value: str) -> int:
    """Return the game's FNV-1a id over a GUID's in-memory bytes."""
    result = 0x811C9DC5
    for byte in uuid.UUID(value).bytes_le:
        result ^= byte
        result = (result * 0x01000193) & 0xFFFFFFFF
    return result


def require_runtime_descriptor(descriptor: EmlHumanoidDescriptor = DESCRIPTOR) -> None:
    blockers = []
    if not descriptor.runtime_enabled:
        blockers.append("runtime_disabled")
    if descriptor.template_guid in STORY_TEMPLATE_GUIDS:
        blockers.append("story_npc_template_forbidden")
    if descriptor.expected_model_guid is None:
        blockers.append("model_resource_unconfirmed")
    if descriptor.expected_animation_graph_guid is None:
        blockers.append("animation_graph_unconfirmed")
    if descriptor.expected_faction != EXPECTED_FACTION_ID:
        blockers.append("safe_faction_unconfirmed")
    if descriptor.creation_marker is None:
        blockers.append("creation_marker_missing")
    if descriptor.ownership_proof is None:
        blockers.append("ownership_unproven")
    if not descriptor.safe_dismiss_proven:
        blockers.append("safe_dismiss_unproven")
    if blockers:
        raise PatchValidationError(",".join(blockers))


def validate_patch(root: str | Path, *, known_resources=KNOWN_RESOURCES,
                   occupied_guids=frozenset()) -> tuple[str, ...]:
    """Validate the repository prototype without executing its Lua code."""
    root = Path(root)
    manifest_path = root / "mod.json"
    lua_path = root / "src" / "mod.lua"
    if not manifest_path.is_file() or not lua_path.is_file():
        raise PatchValidationError("unsupported_patch_layout")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PatchValidationError("invalid_manifest") from exc
    if manifest.get("id") != PATCH_ID or manifest.get("version") != PATCH_VERSION:
        raise PatchValidationError("unexpected_manifest_identity")
    if manifest.get("capabilities") != ["patch", "export"]:
        raise PatchValidationError("unsupported_capabilities")

    lua = lua_path.read_text(encoding="utf-8")
    required = {
        f'local TEMPLATE_GUID = "{TEMPLATE_GUID}"': "unknown_template_guid",
        f'local SOURCE_GUID = "{SOURCE_TEMPLATE_GUID}"': "unknown_source_guid",
        '"keen::ecs::TemplateResource"': "template_resource_missing",
        "game.assets.create_resource": "resource_creation_missing",
        f'comp.value.faction = "{EXPECTED_FACTION}"': "safe_faction_unconfirmed",
        "comp.value.npcId = { value = NPC_ID }": "npc_identity_missing",
        'local RUN_TOKEN = "__AIC_STAGE10_RUN_TOKEN__"': "run_token_placeholder_missing",
        '"run_token=" .. RUN_TOKEN': "run_token_evidence_missing",
        '"model_status=" .. new_model_fingerprint.status': "typed_model_evidence_missing",
        'print("AIC_EML_TEMPLATE_READY", RUN_TOKEN': "run_token_log_marker_missing",
    }
    for marker, error in required.items():
        if marker not in lua:
            raise PatchValidationError(error)
    if SOURCE_TEMPLATE_GUID not in known_resources:
        raise PatchValidationError("missing_source_resource")
    if TEMPLATE_GUID in occupied_guids or TEMPLATE_GUID in known_resources:
        raise PatchValidationError("template_guid_conflict")
    if guid_id(TEMPLATE_GUID) != EXPECTED_NPC_ID:
        raise PatchValidationError("npc_id_mismatch")
    if re.search(r"\bemf\.(spawn|destroy)\b|NpcCommandEvent|StartGuardingEvent", lua):
        raise PatchValidationError("runtime_command_forbidden")
    if re.search(r"\b(spawn|autospawn)\s*\(", lua, re.IGNORECASE):
        raise PatchValidationError("automatic_spawn_forbidden")
    if re.search(r"savegame|character\d*\.ksd|world\d*\.ksd", lua, re.IGNORECASE):
        raise PatchValidationError("save_access_forbidden")
    if re.search(r"create_resource\s*\([^\n]+SOURCE_GUID", lua):
        raise PatchValidationError("vanilla_guid_mutation")
    return ("layout", "manifest", "fixed_guid", "source_reference", "safe_faction",
            "npc_identity", "run_correlation", "no_autospawn", "no_runtime_commands",
            "no_save_access")
