"""Evidence model for a future player-character companion.

This module is deliberately offline.  It neither opens character saves nor calls
EMF.  Stage 7 has not established a supported way to create or control a second
player entity, so every mutating operation remains fail-closed.
"""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from companion.human_body import Evidence


class Variant(str, Enum):
    IN_PROCESS_PLAYER = "A"
    CHARACTER_REPLICA = "B"
    SECOND_CLIENT = "C"


@dataclass(frozen=True)
class VariantAssessment:
    evidence: Evidence
    real_player: bool
    native_inventory: bool
    independent_client: bool
    summary: str


VARIANTS = MappingProxyType({
    Variant.IN_PROCESS_PLAYER: VariantAssessment(
        Evidence.UNSUPPORTED,
        real_player=True,
        native_inventory=True,
        independent_client=False,
        summary="no supported EMF API creates a player slot or loads a character save",
    ),
    Variant.CHARACTER_REPLICA: VariantAssessment(
        Evidence.UNKNOWN,
        real_player=False,
        native_inventory=False,
        independent_client=False,
        summary="a visual or NPC replica would not establish player authority or persistence",
    ),
    Variant.SECOND_CLIENT: VariantAssessment(
        Evidence.LIKELY,
        real_player=True,
        native_inventory=True,
        independent_client=True,
        summary="multiplayer supplies a real player; an AI control channel is still unverified",
    ),
})


@dataclass(frozen=True)
class CommandAssessment:
    evidence: Evidence
    runtime_enabled: bool
    mechanism: str
    verification: str


COMMANDS = MappingProxyType({
    "observe": CommandAssessment(
        Evidence.CONFIRMED,
        False,
        "host EMF can read connected-player identity, components and position",
        "match session, player slot, account key, entity and required components",
    ),
    "moveTo": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client input or a new supported API",
        "position converges while the same player binding remains live",
    ),
    "follow": CommandAssessment(
        Evidence.UNKNOWN, False, "repeated observed movement under second-client authority",
        "sustained distance envelope during a manual route",
    ),
    "stay": CommandAssessment(
        Evidence.UNKNOWN, False, "neutral input under second-client authority",
        "position stays within tolerance for a timed interval",
    ),
    "lookAt": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client camera/aim input",
        "replicated orientation faces the intended target",
    ),
    "attack": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client action input",
        "target receives the expected attributed hit event",
    ),
    "defend": CommandAssessment(
        Evidence.UNKNOWN, False, "brain policy composed from observe/move/attack",
        "manual hostile encounter; no target substitution",
    ),
    "interact": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client interaction input",
        "specific interaction state/event is confirmed",
    ),
    "useItem": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client item action",
        "the exact stack instance and resulting state are confirmed",
    ),
    "equip": CommandAssessment(
        Evidence.UNKNOWN, False, "second-client equipment action",
        "inventory slot and replicated equipment both confirm the change",
    ),
    "transferItem": CommandAssessment(
        Evidence.LIKELY, False, "host-side inventory transaction with permission checks",
        "source and destination stacks reconcile by item instance",
    ),
})


REQUIRED_PLAYER_COMPONENTS = frozenset({
    "PlayerInput", "ServerConsumedPlayerInput", "InventorySetup",
    "CharacterSetup", "SlotSelection",
})


@dataclass(frozen=True)
class PlayerObservation:
    session_token: str
    entity_id: int
    account_key: str
    player_slot: int
    connected: bool
    network_peer_confirmed: bool
    components: frozenset[str]


class PlayerBodyUnavailable(RuntimeError):
    pass


class PlayerCompanionGate:
    """Validate a distinct connected player without granting control authority."""

    def __init__(self, *, session_token: str, host_entity_id: int,
                 host_account_key: str, companion_account_key: str,
                 stable_observations: int = 3):
        if not session_token or host_entity_id <= 0:
            raise ValueError("invalid_host_identity")
        if not host_account_key or not companion_account_key:
            raise ValueError("missing_account_identity")
        if host_account_key == companion_account_key:
            raise ValueError("companion_must_use_distinct_account")
        if stable_observations < 2:
            raise ValueError("invalid_identity_window")
        self.session_token = session_token
        self.host_entity_id = host_entity_id
        self.host_account_key = host_account_key
        self.companion_account_key = companion_account_key
        self.stable_observations = stable_observations
        self._stable = 0
        self._entity_id = None
        self._player_slot = None
        self.invalidated = False
        self.reason = "not_observed"

    @property
    def trusted_identity(self):
        return not self.invalidated and self._stable >= self.stable_observations

    @property
    def runtime_control_enabled(self):
        # Identity is necessary but does not prove a supported control backend.
        return False

    def observe(self, value: PlayerObservation | None):
        if self.invalidated:
            return self.reason
        if value is None or not value.connected:
            return self._invalidate("player_not_connected")
        if value.session_token != self.session_token:
            return self._invalidate("session_changed")
        if value.entity_id <= 0 or value.entity_id == self.host_entity_id:
            return self._invalidate("host_companion_identity_collision")
        if value.account_key != self.companion_account_key:
            return self._invalidate("account_identity_changed")
        if value.account_key == self.host_account_key:
            return self._invalidate("host_account_reused")
        if not 0 <= value.player_slot <= 15:
            return self._invalidate("invalid_player_slot")
        if not value.network_peer_confirmed:
            self._stable = 0
            self.reason = "network_authority_unknown"
            return self.reason
        missing = REQUIRED_PLAYER_COMPONENTS.difference(value.components)
        if missing:
            self._stable = 0
            self.reason = "player_components_missing"
            return self.reason
        if self._entity_id is None:
            self._entity_id = value.entity_id
            self._player_slot = value.player_slot
        elif value.entity_id != self._entity_id or value.player_slot != self._player_slot:
            return self._invalidate("player_binding_changed")
        self._stable += 1
        self.reason = "trusted_identity" if self.trusted_identity else "identity_stabilizing"
        return self.reason

    def require_runtime_control(self, operation: str):
        if operation not in COMMANDS:
            raise PlayerBodyUnavailable("unknown_player_body_operation")
        if not self.trusted_identity:
            raise PlayerBodyUnavailable("player_identity_not_trusted")
        raise PlayerBodyUnavailable("player_control_backend_not_verified")

    def _invalidate(self, reason):
        self.invalidated = True
        self._stable = 0
        self.reason = reason
        return reason


def recommended_variant() -> Variant:
    """The only route that preserves native player semantics."""
    return Variant.SECOND_CLIENT
