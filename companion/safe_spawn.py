"""Fail-closed Stage 10.8 humanoid spawn preparation.

This module is deliberately engine independent.  Phase A cannot call EMF, spawn,
destroy, install files, or write saves.  It models the gates and evidence that a
future separately authorised runtime adapter would have to satisfy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping

from .eml_humanoid import EXPECTED_NPC_ID, SOURCE_TEMPLATE_GUID, TEMPLATE_GUID

FORMAT = "aic_humanoid_spawn_evidence_v5"
BUILD = 1273043
TEMPLATE_TYPE = "keen::ecs::TemplateResource"
COMPONENT_COUNT = 81
COMPONENT_FINGERPRINT = "412d61b0"
TEMPLATE_FINGERPRINT = "a7f38d80"
ANIMATION_GRAPH = "402df515-5965-4b01-a17b-17d482a91af4"
CHARACTER = "Body Test"
WORLD = "AI Body Test"
SLOT = 1
RUN_TOKEN = re.compile(r"^[0-9a-f]{32}$")
EVIDENCE_SECTIONS = (
    "PRE_SPAWN", "SPAWN_RESULT", "RENDER_OBSERVATION", "DESPAWN_RESULT", "POST_RUN_INTEGRITY"
)
RENDER_LEVELS = (
    "ENTITY_CREATED", "ENTITY_IDENTITY_CONFIRMED", "MODEL_LOADED",
    "SKELETON_CONFIRMED", "ANIMATION_CONFIRMED", "RUNTIME_RENDER_CONFIRMED",
)


class State(str, Enum):
    DISABLED = "DISABLED"
    PREFLIGHT_REQUIRED = "PREFLIGHT_REQUIRED"
    READY_FOR_CONFIRMATION = "READY_FOR_CONFIRMATION"
    SPAWN_REQUESTED = "SPAWN_REQUESTED"
    ENTITY_ACTIVE = "ENTITY_ACTIVE"
    DESPAWN_REQUESTED = "DESPAWN_REQUESTED"
    ENTITY_REMOVED = "ENTITY_REMOVED"
    FAILED = "FAILED"
    LOCKED = "LOCKED"


@dataclass(frozen=True)
class GameEvidence:
    build: int = BUILD
    character: str = CHARACTER
    character_slot: int = SLOT
    world: str = WORLD
    world_slot: int = SLOT
    storage: str = "local"
    dedicated_server: bool = False
    multiplayer: bool = False
    combat_active: bool | None = False
    critical_errors: tuple[str, ...] = ()
    receipt_valid: bool = True
    backup_verified: bool = True
    dat_expected: bool = True
    local_mutation_expected: bool = True
    bridge_connected: bool = True
    observer_responding: bool = True


@dataclass(frozen=True)
class TemplateEvidence:
    guid: str = TEMPLATE_GUID
    resource_type: str = TEMPLATE_TYPE
    component_count: int = COMPONENT_COUNT
    component_fingerprint: str = COMPONENT_FINGERPRINT
    template_fingerprint: str = TEMPLATE_FINGERPRINT
    hashkey32_match: bool = True
    animation_graph: str = ANIMATION_GRAPH
    visual_references_resolved: bool = True
    source_unchanged: bool = True
    faction: str = "PlayerAlly"
    faction_value: int = 11
    lookup_confirmed: bool = True
    unknown_components: tuple[str, ...] = ()
    runtime_override: bool = False


@dataclass(frozen=True)
class RuntimeCapabilities:
    spawn_method: str = "emf.spawn(world,guid,x,y,z)"
    despawn_method: str = "emf.destroy(world,entity_id)"
    spawn_returns_entity_id: bool = True
    faction_in_template_before_spawn: bool = True
    exact_instance_identity: bool = False
    ownership_proven: bool = False
    safe_position_prevalidated: bool = False
    despawn_disappearance_verifiable: bool = True
    persistence_for_forcesave_known: bool = False


@dataclass
class GateReport:
    checks: dict[str, bool]
    blockers: list[str]
    state: State
    spawn_ready: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"checks": self.checks, "blockers": self.blockers,
                "state": self.state.value, "spawn_ready": False}


def evaluate_preflight(game: GameEvidence, template: TemplateEvidence,
                       capabilities: RuntimeCapabilities) -> GateReport:
    """Evaluate every known gate.  Unknown is represented as false, never PASS."""
    checks = {
        "build": game.build == BUILD,
        "character": game.character == CHARACTER and game.character_slot == SLOT,
        "world": game.world == WORLD and game.world_slot == SLOT,
        "local_context": game.storage == "local" and not game.dedicated_server and not game.multiplayer,
        "combat_inactive": game.combat_active is False,
        "game_errors_clear": not game.critical_errors,
        "receipt": game.receipt_valid,
        "backup": game.backup_verified,
        "dat": game.dat_expected,
        "local_integrity": game.local_mutation_expected,
        "bridge": game.bridge_connected,
        "observer": game.observer_responding,
        "template_guid": template.guid == TEMPLATE_GUID,
        "template_type": template.resource_type == TEMPLATE_TYPE,
        "component_count": template.component_count == COMPONENT_COUNT,
        "component_fingerprint": template.component_fingerprint == COMPONENT_FINGERPRINT,
        "template_fingerprint": template.template_fingerprint == TEMPLATE_FINGERPRINT,
        "template_lookup": template.lookup_confirmed,
        "hashkey32": template.hashkey32_match,
        "animation": template.animation_graph == ANIMATION_GRAPH,
        "visual_references": template.visual_references_resolved,
        "source_unchanged": template.source_unchanged,
        "components_known": not template.unknown_components and not template.runtime_override,
        "faction": (template.faction, template.faction_value) == ("PlayerAlly", 11)
                   and capabilities.faction_in_template_before_spawn,
        "spawn_api": capabilities.spawn_returns_entity_id
                     and capabilities.spawn_method == "emf.spawn(world,guid,x,y,z)",
        "exact_instance_identity": capabilities.exact_instance_identity,
        "ownership": capabilities.ownership_proven,
        "safe_position": capabilities.safe_position_prevalidated,
        "despawn_api": capabilities.despawn_method == "emf.destroy(world,entity_id)"
                       and capabilities.despawn_disappearance_verifiable,
        "persistence": capabilities.persistence_for_forcesave_known,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    state = State.READY_FOR_CONFIRMATION if not blockers else State.LOCKED
    # Phase A never turns offline evidence into permission to spawn.
    return GateReport(checks, blockers, state, False)


class SafeSpawnController:
    """Offline controller contract; all mutation commands are disabled in Phase A."""

    def __init__(self, *, phase_a: bool = True) -> None:
        self.phase_a = phase_a
        self.state = State.DISABLED
        self.last_error = ""
        self.entity_handle: int | None = None
        self.identity: dict[str, Any] | None = None
        self.destroy_requested = False
        self.spawn_attempted = False
        self.session_generation = 0
        self.report: GateReport | None = None

    def status(self) -> dict[str, Any]:
        return {"format": FORMAT, "state": self.state.value, "last_error": self.last_error,
                "entity_handle": self.entity_handle, "identity": self.identity,
                "spawn_attempted": self.spawn_attempted, "destroy_requested": self.destroy_requested,
                "phase_a": self.phase_a, "spawn_ready": False, "automatic_retry": False,
                "runtime_render_confirmed": "UNKNOWN"}

    def require_preflight(self) -> dict[str, Any]:
        if self.state not in {State.DISABLED, State.ENTITY_REMOVED}:
            return self._lock("invalid_state_for_preflight")
        self.state = State.PREFLIGHT_REQUIRED
        return self.status()

    def preflight(self, game: GameEvidence, template: TemplateEvidence,
                  capabilities: RuntimeCapabilities) -> dict[str, Any]:
        if self.state != State.PREFLIGHT_REQUIRED:
            return self._lock("preflight_not_requested")
        self.report = evaluate_preflight(game, template, capabilities)
        self.state = self.report.state
        self.last_error = ",".join(self.report.blockers)
        result = self.status()
        result["gates"] = self.report.as_dict()
        return result

    def inspect(self) -> dict[str, Any]:
        result = self.status()
        result["read_only"] = True
        result["render_levels"] = {name: "UNKNOWN" for name in RENDER_LEVELS}
        return result

    def spawn_once(self, *, explicit_confirmation: bool, run_token: str,
                   reconnect: bool = False, reload: bool = False) -> dict[str, Any]:
        # No environment or transport is accepted here: Phase A has no mutation path.
        if self.phase_a:
            return self._lock("phase_a_mutation_prohibited")
        if reconnect or reload:
            return self._lock("spawn_after_reconnect_or_reload")
        if self.state != State.READY_FOR_CONFIRMATION or not explicit_confirmation:
            return self._lock("explicit_confirmation_required")
        if not RUN_TOKEN.fullmatch(run_token):
            return self._lock("invalid_run_token")
        if self.spawn_attempted or self.entity_handle is not None:
            return self._lock("single_spawn_limit")
        # A future authorised runtime implementation must replace this fail-closed edge.
        self.spawn_attempted = True
        return self._lock("runtime_spawn_not_implemented")

    def despawn(self, *, handle: int | None = None, guid: str | None = None) -> dict[str, Any]:
        if self.phase_a:
            return self._lock("phase_a_mutation_prohibited")
        if self.state != State.ENTITY_ACTIVE or handle != self.entity_handle:
            return self._lock("entity_identity_not_confirmed")
        if not self.identity or guid != TEMPLATE_GUID or self.identity.get("guid") != TEMPLATE_GUID:
            return self._lock("entity_identity_not_confirmed")
        self.destroy_requested = True
        self.state = State.DESPAWN_REQUESTED
        self.last_error = "runtime_despawn_not_implemented"
        return self.status()

    def emergency_stop(self, *, mock_removed: bool | None = None) -> dict[str, Any]:
        if mock_removed is True:
            self.entity_handle = None
            self.identity = None
            self.state = State.ENTITY_REMOVED
            self.last_error = "mock_only"
            return self.status()
        return self._lock("recovery_required")

    def on_disconnect(self) -> dict[str, Any]:
        return self._lock("bridge_disconnected")

    def on_reload(self) -> dict[str, Any]:
        self.session_generation += 1
        return self._lock("reload_ownership_lost")

    def _lock(self, reason: str) -> dict[str, Any]:
        self.state = State.LOCKED
        self.last_error = reason
        return self.status()


def validate_evidence_v5(document: Mapping[str, Any]) -> list[str]:
    """Return fail-closed validation errors for a complete five-section record."""
    errors: list[str] = []
    if document.get("format") != FORMAT:
        errors.append("format")
    token = document.get("run_token")
    if not isinstance(token, str) or not RUN_TOKEN.fullmatch(token):
        errors.append("run_token")
    if document.get("build") != BUILD:
        errors.append("build")
    if document.get("template_guid") != TEMPLATE_GUID:
        errors.append("template_guid")
    if document.get("template_fingerprint") != TEMPLATE_FINGERPRINT:
        errors.append("template_fingerprint")
    sections = document.get("sections")
    if not isinstance(sections, Mapping):
        return errors + ["sections"]
    for name in EVIDENCE_SECTIONS:
        section = sections.get(name)
        if not isinstance(section, Mapping):
            errors.append(f"section:{name}")
    pre = sections.get("PRE_SPAWN", {})
    required_pre = ("character_identity", "world_identity", "spawn_api", "spawn_safety_verdict",
                    "faction_verification", "position_validation", "persistence_status")
    for key in required_pre:
        if key not in pre:
            errors.append(f"PRE_SPAWN:{key}")
    spawn = sections.get("SPAWN_RESULT", {})
    for key in ("entity_handle", "entity_identity", "failure_reason"):
        if key not in spawn:
            errors.append(f"SPAWN_RESULT:{key}")
    despawn = sections.get("DESPAWN_RESULT", {})
    for key in ("despawn_api", "despawn_verification", "recovery_status"):
        if key not in despawn:
            errors.append(f"DESPAWN_RESULT:{key}")
    render = sections.get("RENDER_OBSERVATION", {})
    levels = render.get("levels") if isinstance(render, Mapping) else None
    if not isinstance(levels, Mapping) or any(name not in levels for name in RENDER_LEVELS):
        errors.append("RENDER_OBSERVATION:levels")
    post = sections.get("POST_RUN_INTEGRITY", {})
    if not isinstance(post, Mapping) or "source_unchanged" not in post:
        errors.append("POST_RUN_INTEGRITY:source_unchanged")
    return errors


def public_evidence(document: Mapping[str, Any]) -> dict[str, Any]:
    """Produce a publication-safe copy; runtime tokens and local identities stay private."""
    copy = dict(document)
    copy.pop("run_token", None)
    copy["run_token_published"] = False
    sections = {name: dict(value) for name, value in document.get("sections", {}).items()
                if isinstance(value, Mapping)}
    for section in sections.values():
        section.pop("character_identity", None)
        section.pop("world_identity", None)
        section.pop("entity_handle", None)
    copy["sections"] = sections
    return copy


def offline_research_verdict() -> dict[str, Any]:
    """The current source-backed Phase A conclusion, kept separate from runtime facts."""
    report = evaluate_preflight(GameEvidence(), TemplateEvidence(), RuntimeCapabilities())
    return {"verdict": "BLOCKED_FOR_SPAWN", "runtime": "NOT_EXECUTED",
            "runtime_render_confirmed": "UNKNOWN", "spawn_ready": False,
            "blockers": report.blockers, "source_npc_guid": SOURCE_TEMPLATE_GUID,
            "template_guid": TEMPLATE_GUID, "npc_id": EXPECTED_NPC_ID}
