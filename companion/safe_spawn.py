"""Fail-closed Stage 10.8 humanoid spawn preparation.

This module is deliberately engine independent.  Phase A cannot call EMF, spawn,
destroy, install files, or write saves.  It models the gates and evidence that a
future separately authorised runtime adapter would have to satisfy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Mapping, Sequence

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


# Stage 10.9 keeps the legacy Stage 10.8 report above for compatibility, but
# models every safety property independently.  These are pure/offline types:
# no function below accepts an EMF transport or performs a game mutation.
class GateName(str, Enum):
    INSTANCE_IDENTITY = "INSTANCE_IDENTITY"
    OWNERSHIP = "OWNERSHIP"
    POSITION = "POSITION"
    PERSISTENCE = "PERSISTENCE"
    FACTION = "FACTION"
    DESTROY = "DESTROY"
    TEMPLATE = "TEMPLATE"
    WORLD_CONTEXT = "WORLD_CONTEXT"


class GateStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass(frozen=True)
class SafetyGate:
    name: GateName
    status: GateStatus
    reason: str
    provenance: tuple[str, ...]
    evidence: Mapping[str, Any] = field(default_factory=dict)
    session_identity: str | None = None
    observed_at: str | None = None
    confidence: Confidence = Confidence.NONE
    mandatory: bool = True
    risk_absence_proven: bool = False

    def valid(self) -> bool:
        if not self.reason or not self.provenance:
            return False
        if self.status is GateStatus.NOT_APPLICABLE and not self.risk_absence_proven:
            return False
        if self.status is GateStatus.CONFIRMED and self.confidence is Confidence.NONE:
            return False
        return True


@dataclass(frozen=True)
class SafetyGateAssessment:
    gates: Mapping[GateName, SafetyGate]
    phase: str = "STAGE10_9_PHASE_A"

    @property
    def blocking_gates(self) -> tuple[GateName, ...]:
        blocked: list[GateName] = []
        for name in GateName:
            gate = self.gates.get(name)
            if gate is None or not gate.valid():
                blocked.append(name)
            elif gate.mandatory and gate.status not in {
                GateStatus.CONFIRMED, GateStatus.NOT_APPLICABLE
            }:
                blocked.append(name)
        return tuple(blocked)

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "gates": {
                name.value: ({
                    "status": gate.status.value,
                    "reason": gate.reason,
                    "provenance": list(gate.provenance),
                    "evidence": dict(gate.evidence),
                    "session_identity": gate.session_identity,
                    "observed_at": gate.observed_at,
                    "confidence": gate.confidence.value,
                    "mandatory": gate.mandatory,
                    "risk_absence_proven": gate.risk_absence_proven,
                } if gate else None)
                for name in GateName
                for gate in (self.gates.get(name),)
            },
            "blocking_gates": [name.value for name in self.blocking_gates],
            # Phase A can describe a future authorization boundary but never
            # turns source research or mocks into runtime permission.
            "spawn_ready": False,
        }


class OwnedIdentityState(str, Enum):
    CONFIRMED = "CONFIRMED"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"
    REUSED = "REUSED"
    LOST = "LOST"


@dataclass(frozen=True)
class OwnedEntityIdentity:
    instance_token: str | None
    entity_id: int | None
    entity_generation: int | None
    template_guid: str | None
    session_identity: str | None
    ownership_marker: str | None
    marker_attached_at_spawn: bool
    state: OwnedIdentityState
    provenance: tuple[str, ...] = ()

    @property
    def permits_targeted_destroy(self) -> bool:
        return (
            self.state is OwnedIdentityState.CONFIRMED
            and bool(self.instance_token)
            and isinstance(self.entity_id, int) and self.entity_id > 0
            and isinstance(self.entity_generation, int)
            and bool(self.template_guid)
            and bool(self.session_identity)
            and self.ownership_marker == self.instance_token
            and self.marker_attached_at_spawn
            and bool(self.provenance)
        )


@dataclass(frozen=True)
class IdentityObservation:
    entity_id: int | None
    entity_generation: int | None
    template_guid: str | None
    session_identity: str | None
    ownership_marker: str | None
    candidates: int = 1
    marker_integrity: bool | None = None


def classify_owned_identity(expected: OwnedEntityIdentity,
                            current: IdentityObservation | None) -> OwnedIdentityState:
    """Classify an observation without inventing a missing engine generation."""
    if current is None or current.entity_id is None:
        return OwnedIdentityState.LOST
    if not expected.session_identity or current.session_identity != expected.session_identity:
        return OwnedIdentityState.STALE
    if current.candidates != 1:
        return OwnedIdentityState.AMBIGUOUS
    if expected.entity_id != current.entity_id:
        return OwnedIdentityState.LOST
    if expected.entity_generation is None or current.entity_generation is None:
        return OwnedIdentityState.AMBIGUOUS
    if expected.entity_generation != current.entity_generation:
        return OwnedIdentityState.REUSED
    if (not expected.marker_attached_at_spawn or not expected.instance_token
            or current.ownership_marker != expected.instance_token
            or current.marker_integrity is not True):
        return OwnedIdentityState.AMBIGUOUS
    if not expected.template_guid or current.template_guid != expected.template_guid:
        return OwnedIdentityState.REUSED
    return OwnedIdentityState.CONFIRMED


class PositionStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PositionEvidence:
    requested_world: str | None
    observed_world: str | None
    ground_hit: bool | None
    surface_normal_ok: bool | None
    collision_clearance: bool | None
    walkable: bool | None
    safe_distance: bool | None
    area_available: bool | None
    height_ok: bool | None
    danger_clear: bool | None
    query_provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class PositionValidation:
    status: PositionStatus
    reason: str
    evidence: PositionEvidence


def validate_spawn_position(evidence: PositionEvidence) -> PositionValidation:
    checks = {
        "world_identity": bool(evidence.requested_world)
            and evidence.requested_world == evidence.observed_world,
        "ground_hit": evidence.ground_hit,
        "surface_normal": evidence.surface_normal_ok,
        "collision_clearance": evidence.collision_clearance,
        "walkability": evidence.walkable,
        "safe_distance": evidence.safe_distance,
        "area_available": evidence.area_available,
        "height": evidence.height_ok,
        "danger": evidence.danger_clear,
    }
    failed = [name for name, value in checks.items() if value is False]
    if failed:
        return PositionValidation(PositionStatus.INVALID, ",".join(failed), evidence)
    unknown = [name for name, value in checks.items() if value is None]
    if not evidence.query_provenance:
        unknown.append("provenance")
    if unknown:
        return PositionValidation(PositionStatus.UNKNOWN, ",".join(unknown), evidence)
    return PositionValidation(PositionStatus.VALID, "all_required_queries_confirmed", evidence)


class PersistenceStatus(str, Enum):
    TEMPORARY_CONFIRMED = "TEMPORARY_CONFIRMED"
    PERSISTENT_CONFIRMED = "PERSISTENT_CONFIRMED"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PersistenceEvidence:
    force_save: bool | None
    active_npc_state: bool | None
    active_npc_state_saved: bool | None
    do_not_save: bool | None
    unique_npc_collision: bool | None
    absent_after_reload: bool | None
    restored_after_destroy: bool | None
    runtime_provenance: tuple[str, ...] = ()


def classify_persistence(evidence: PersistenceEvidence) -> PersistenceStatus:
    if evidence.unique_npc_collision is True or evidence.restored_after_destroy is True:
        return PersistenceStatus.CONFLICT
    if not evidence.runtime_provenance or evidence.absent_after_reload is None:
        return PersistenceStatus.UNKNOWN
    if evidence.absent_after_reload is True:
        return PersistenceStatus.TEMPORARY_CONFIRMED
    if evidence.absent_after_reload is False:
        return PersistenceStatus.PERSISTENT_CONFIRMED
    return PersistenceStatus.UNKNOWN


class DestroyStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    ACCEPTED_UNVERIFIED = "ACCEPTED_UNVERIFIED"
    REMOVED_CONFIRMED = "REMOVED_CONFIRMED"
    REMAINS = "REMAINS"
    REAPPEARED = "REAPPEARED"
    TIMEOUT = "TIMEOUT"
    CRASHED = "CRASHED"


@dataclass(frozen=True)
class DestroyAssessment:
    status: DestroyStatus
    reason: str
    retry_allowed: bool = False


def authorize_destroy(identity: OwnedEntityIdentity, observation: IdentityObservation | None,
                      *, atomic_check_and_destroy: bool) -> DestroyAssessment:
    state = classify_owned_identity(identity, observation)
    if state is not OwnedIdentityState.CONFIRMED or not identity.permits_targeted_destroy:
        return DestroyAssessment(DestroyStatus.BLOCKED, f"identity_{state.value.lower()}")
    if not atomic_check_and_destroy:
        return DestroyAssessment(DestroyStatus.BLOCKED, "toctou_check_destroy_not_atomic")
    return DestroyAssessment(DestroyStatus.AUTHORIZED, "exact_owned_identity_atomic_boundary")


def verify_destroy_result(*, accepted: bool | None, presence_by_tick: Sequence[bool],
                          crashed: bool = False, timed_out: bool = False) -> DestroyAssessment:
    if crashed:
        return DestroyAssessment(DestroyStatus.CRASHED, "destroy_outcome_unknown")
    if timed_out:
        return DestroyAssessment(DestroyStatus.TIMEOUT, "absence_not_confirmed")
    if accepted is not True:
        return DestroyAssessment(DestroyStatus.BLOCKED, "destroy_not_accepted")
    if not presence_by_tick:
        return DestroyAssessment(DestroyStatus.ACCEPTED_UNVERIFIED, "no_post_destroy_observation")
    if any(presence_by_tick):
        if False in presence_by_tick and presence_by_tick[-1] is True:
            return DestroyAssessment(DestroyStatus.REAPPEARED, "entity_reappeared")
        return DestroyAssessment(DestroyStatus.REMAINS, "entity_still_present")
    if len(presence_by_tick) < 3:
        return DestroyAssessment(DestroyStatus.ACCEPTED_UNVERIFIED, "fewer_than_three_absent_ticks")
    return DestroyAssessment(DestroyStatus.REMOVED_CONFIRMED, "absent_for_three_server_ticks")


def stage10_9_gate_assessment() -> SafetyGateAssessment:
    """Current source-backed result; runtime-dependent gates remain explicit."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source = ("EMF@08d600155fcadc8e45cc9c6f3932a67c717345be",)
    unknown = {
        GateName.INSTANCE_IDENTITY: "no_entity_generation_or_atomic_instance_marker",
        GateName.OWNERSHIP: "ownership_metadata_not_exposed",
        GateName.POSITION: "no_read_only_clearance_and_walkability_query",
        GateName.PERSISTENCE: "custom_villager_reload_lifecycle_not_tested",
        GateName.FACTION: "template_PlayerAlly_only_runtime_ai_unknown",
        GateName.DESTROY: "no_atomic_identity_check_and_destroy",
    }
    gates: dict[GateName, SafetyGate] = {
        name: SafetyGate(name, GateStatus.UNKNOWN, reason, source,
                         observed_at=now, confidence=Confidence.NONE)
        for name, reason in unknown.items()
    }
    gates[GateName.TEMPLATE] = SafetyGate(
        GateName.TEMPLATE, GateStatus.CONFIRMED,
        "stage10_7_load_only_template_evidence_v4_pass", ("STAGE10_7_PHASE_C",),
        {"guid": TEMPLATE_GUID, "component_count": COMPONENT_COUNT},
        observed_at=now, confidence=Confidence.HIGH)
    gates[GateName.WORLD_CONTEXT] = SafetyGate(
        GateName.WORLD_CONTEXT, GateStatus.UNKNOWN,
        "phase_a_runtime_not_executed", source, observed_at=now, confidence=Confidence.NONE)
    return SafetyGateAssessment(gates)
