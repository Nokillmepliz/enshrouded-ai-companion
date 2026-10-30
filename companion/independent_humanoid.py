"""Fail-closed contracts for an independent humanoid NPC body.

This module is deliberately offline.  It records what a future EMF adapter
must prove; importing or using it cannot connect to Enshrouded.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from .human_body import CANDIDATES, Evidence


class Uniqueness(Enum):
    UNIQUE_STORY_NPC = "unique_story_npc"
    NON_UNIQUE = "non_unique"
    UNKNOWN = "unknown"


class Lifecycle(Enum):
    DISABLED = "disabled"
    PREFLIGHT = "preflight"
    SPAWN_REQUESTED = "spawn_requested"
    IDENTITY_VERIFIED = "identity_verified"
    SAFE_INACTIVE = "safe_inactive"
    ACTIVE = "active"
    DISMISSING = "dismissing"
    ABSENT = "absent"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True)
class Capability:
    evidence: Evidence
    runtime_enabled: bool
    scope: str


@dataclass(frozen=True)
class HumanBodyDescriptor:
    key: str
    template_guid: str
    source: str
    npc_id: int | None
    model_guid: str | None
    animation_graph_guid: str | None
    initial_faction: int | None
    uniqueness: Uniqueness
    creation_marker: str | None
    ownership_proof: str | None
    safe_dismiss_proven: bool
    capabilities: MappingProxyType
    runtime_enabled: bool = False


def _capabilities() -> MappingProxyType:
    return MappingProxyType({
        "spawn": Capability(Evidence.UNKNOWN, False, "safe inactive/friendly creation unproven"),
        "moveTo": Capability(Evidence.CONFIRMED, False, "existing active survivor only"),
        "follow": Capability(Evidence.UNKNOWN, False, "persistent follow unproven"),
        "stay": Capability(Evidence.UNKNOWN, False, "long-lived hold behavior unproven"),
        "lookAt": Capability(Evidence.UNKNOWN, False, "no confirmed public command"),
        "stop": Capability(Evidence.UNKNOWN, False, "no confirmed public command"),
        "attack": Capability(Evidence.UNKNOWN, False, "survivor combat control unproven"),
        "interact": Capability(Evidence.UNKNOWN, False, "generic world interaction unproven"),
        "inventory": Capability(Evidence.LIKELY, False, "InventorySetup exists; companion storage unproven"),
        "equipment": Capability(Evidence.UNKNOWN, False, "NPC equip path and visuals unproven"),
        "dismiss": Capability(Evidence.UNKNOWN, False, "ownership and deletion unproven"),
        "persist": Capability(Evidence.CONFIRMED, False, "villagers ForceSave, but unsafe for a duplicate"),
    })


# Pinned Enshwick data proves these templates and npcIds, while EMF research
# proves that villager uniqueness is keyed by template GUID.  They are useful
# survey subjects, never a spawn allow-list.
DESCRIPTORS = MappingProxyType({
    key: HumanBodyDescriptor(
        key=key,
        template_guid=body.template_guid,
        source="enshwick:WORKSHOP_SURVIVORS",
        npc_id=body.npc_id,
        model_guid=None,
        animation_graph_guid=None,
        initial_faction=None,
        uniqueness=Uniqueness.UNIQUE_STORY_NPC,
        creation_marker=None,
        ownership_proof=None,
        safe_dismiss_proven=False,
        capabilities=_capabilities(),
    )
    for key, body in CANDIDATES.items()
})


class HumanoidBlocked(RuntimeError):
    pass


def descriptor(key: str) -> HumanBodyDescriptor:
    try:
        return DESCRIPTORS[key]
    except (KeyError, TypeError) as exc:
        raise HumanoidBlocked("unknown_humanoid_template") from exc


@dataclass(frozen=True)
class BodyObservation:
    session: str
    entity_id: int
    template_guid: str | None
    model_guid: str | None
    npc_id: int | None
    faction: int | None
    kind: str | None
    creation_marker: str | None


class IndependentHumanoidGate:
    """Lifecycle and ownership gate for a future humanoid backend.

    A descriptor cannot pass preflight until every dangerous property is
    confirmed.  The current catalog intentionally cannot pass.
    """

    def __init__(self, body: HumanBodyDescriptor, *, session: str):
        self.body = body
        self.session = session
        self.state = Lifecycle.DISABLED
        self.entity_id: int | None = None
        self.expected_marker: str | None = None
        self._last_observation: BodyObservation | None = None
        self._stable = 0
        self._spawn_uncertain = False
        self.reason = "runtime_disabled"

    @property
    def owned(self) -> bool:
        return self.state in {
            Lifecycle.IDENTITY_VERIFIED, Lifecycle.SAFE_INACTIVE,
            Lifecycle.ACTIVE, Lifecycle.DISMISSING,
        } and self._stable >= 3

    def preflight(self) -> bool:
        blockers = []
        if not self.body.runtime_enabled:
            blockers.append("runtime_disabled")
        if self.body.uniqueness is not Uniqueness.NON_UNIQUE:
            blockers.append("template_not_proven_non_unique")
        if not self.body.model_guid:
            blockers.append("model_guid_unknown")
        if not self.body.animation_graph_guid:
            blockers.append("animation_graph_unknown")
        if self.body.initial_faction != 11:
            blockers.append("safe_initial_faction_unknown")
        if not self.body.creation_marker or not self.body.ownership_proof:
            blockers.append("ownership_unproven")
        if not self.body.safe_dismiss_proven:
            blockers.append("safe_dismiss_unproven")
        if blockers:
            self.state = Lifecycle.DISABLED
            self.reason = ",".join(blockers)
            return False
        self.state = Lifecycle.PREFLIGHT
        self.reason = "preflight_passed"
        return True

    def spawn_requested(self, *, entity_id: int | None, marker: str | None,
                        outcome_known: bool) -> None:
        if self.state is not Lifecycle.PREFLIGHT:
            raise HumanoidBlocked("preflight_required")
        self.state = Lifecycle.SPAWN_REQUESTED
        self.entity_id = entity_id
        self.expected_marker = marker
        self._spawn_uncertain = not outcome_known or entity_id in (None, 0)
        if self._spawn_uncertain:
            self.state = Lifecycle.RECOVERY_REQUIRED
            self.reason = "spawn_outcome_uncertain"
        else:
            self.reason = "identity_pending"

    def observe(self, value: BodyObservation | None, *, reflection_error=False) -> str:
        if self.state is Lifecycle.RECOVERY_REQUIRED:
            return self.reason
        if self.state not in {Lifecycle.SPAWN_REQUESTED, Lifecycle.IDENTITY_VERIFIED,
                              Lifecycle.SAFE_INACTIVE, Lifecycle.ACTIVE,
                              Lifecycle.DISMISSING}:
            return "observation_not_expected"
        if reflection_error or value is None:
            self._stable = 0
            self.reason = "reflection_error" if reflection_error else "fingerprint_incomplete"
            return self.reason
        complete = all((value.template_guid, value.model_guid, value.npc_id is not None,
                        value.faction is not None, value.kind, value.creation_marker))
        if not complete:
            self._stable = 0
            self.reason = "fingerprint_incomplete"
            return self.reason
        expected = (
            value.session == self.session
            and value.entity_id == self.entity_id
            and value.template_guid == self.body.template_guid
            and value.model_guid == self.body.model_guid
            and value.npc_id == self.body.npc_id
            and value.kind == "active_npc"
            and value.creation_marker == self.expected_marker
        )
        if not expected or (self._last_observation and value != self._last_observation):
            self._stable = 0
            self.state = Lifecycle.RECOVERY_REQUIRED
            self.reason = "identity_changed"
            return self.reason
        self._last_observation = value
        self._stable += 1
        if self._stable >= 3:
            self.state = Lifecycle.IDENTITY_VERIFIED
            self.reason = "identity_verified"
        else:
            self.reason = "fingerprint_stabilizing"
        return self.reason

    def mark_safe_inactive(self) -> None:
        if not self.owned or not self._last_observation or self._last_observation.faction != 11:
            raise HumanoidBlocked("verified_safe_identity_required")
        self.state = Lifecycle.SAFE_INACTIVE
        self.reason = "safe_inactive"

    def activate(self) -> None:
        if self.state is not Lifecycle.SAFE_INACTIVE:
            raise HumanoidBlocked("safe_inactive_required")
        self.state = Lifecycle.ACTIVE
        self.reason = "active"

    def begin_dismiss(self, current: BodyObservation | None) -> None:
        if not self.body.safe_dismiss_proven:
            raise HumanoidBlocked("safe_dismiss_unproven")
        if not self.owned or current is None or current != self._last_observation:
            raise HumanoidBlocked("current_ownership_unconfirmed")
        self.state = Lifecycle.DISMISSING
        self.reason = "dismiss_observation_pending"

    def confirm_absent(self, *, consecutive_absent: int) -> bool:
        if self.state is not Lifecycle.DISMISSING:
            raise HumanoidBlocked("dismiss_not_started")
        if consecutive_absent < 3:
            return False
        self.state = Lifecycle.ABSENT
        self.reason = "confirmed_absent"
        return True

    def require_operation(self, operation: str) -> None:
        cap = self.body.capabilities.get(operation)
        if cap is None:
            raise HumanoidBlocked("unknown_humanoid_operation")
        if self.state is not Lifecycle.ACTIVE:
            raise HumanoidBlocked("active_owned_body_required")
        if not cap.runtime_enabled:
            raise HumanoidBlocked("capability_not_runtime_verified")

    def reload(self, session: str) -> None:
        if session == self.session:
            return
        self.session = session
        self._stable = 0
        self._last_observation = None
        if self.entity_id is not None or self._spawn_uncertain:
            self.state = Lifecycle.RECOVERY_REQUIRED
            self.reason = "reload_with_uncertain_entity"
        else:
            self.state = Lifecycle.DISABLED
            self.reason = "runtime_disabled"
