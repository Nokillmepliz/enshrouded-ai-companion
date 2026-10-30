"""Offline evidence catalog and fail-closed identity policy for a future human body.

This module does not call EMF and cannot spawn, move or delete an entity.  It makes
the current blocker executable: a known survivor template is still unavailable for
runtime use until its model fingerprint and safe lifecycle are verified.
"""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class Evidence(str, Enum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class Capability:
    evidence: Evidence
    implemented: bool
    scope: str


@dataclass(frozen=True)
class HumanCandidate:
    key: str
    npc_id: int
    template_guid: str
    staff_guid: str
    capabilities: MappingProxyType
    runtime_enabled: bool = False


def _capabilities():
    # GoToPosition is confirmed only for an already active survivor.  It does
    # not prove that a directly spawned duplicate is controllable or owned.
    return MappingProxyType({
        "spawn": Capability(Evidence.UNKNOWN, False, "direct EMF spawn not verified"),
        "follow": Capability(Evidence.UNKNOWN, False, "no persistent follow command verified"),
        "stay": Capability(Evidence.LIKELY, False, "repeated GoToPosition may hold an active survivor"),
        "moveTo": Capability(Evidence.CONFIRMED, False, "NpcCommandEvent on an existing ActiveNpcState"),
        "attack": Capability(Evidence.UNKNOWN, False, "no survivor combat-control API verified"),
        "interact": Capability(Evidence.UNKNOWN, False, "no generic NPC interaction API verified"),
        "dismiss": Capability(Evidence.UNKNOWN, False, "duplicate ownership and safe deletion unverified"),
        "inventory": Capability(Evidence.LIKELY, False, "InventorySetup observed; companion transaction unverified"),
        "equipment": Capability(Evidence.UNKNOWN, False, "player equipment path is not verified for survivors"),
    })


def _candidate(key, npc_id, staff, template):
    return HumanCandidate(key, npc_id, template, staff, _capabilities())


# Enshwick's pinned WORKSHOP_SURVIVORS table.  These are candidates, not a
# runtime allow-list.  Keeping all entries prevents a hand-written, invented
# GUID from silently becoming selectable.
_CANDIDATES = {
    c.key: c for c in (
        _candidate("blacksmith", 1_201_801_546, "505ccfbc-440d-4d63-a3d6-d689d3d55e78", "c313f0a8-ed2e-444e-8384-a540f6bbd98e"),
        _candidate("blacksmith_assistant", 1_731_045_065, "a514d932-4cf0-4eac-b25c-d8cf32f6d394", "04d42ed2-beb4-4013-8f10-5d63efae2015"),
        _candidate("alchemist", 4_057_418_535, "b500ea01-9d3f-40c3-a3b1-14127f313755", "7456862b-53fe-4b94-8a75-d3079afc9323"),
        _candidate("alchemist_assistant", 3_159_593_666, "b8e3be95-1811-43ba-8e25-a6f1b6b1ca04", "27e2fb44-4975-4b61-988d-c7b4e16ed325"),
        _candidate("carpenter", 2_103_948_589, "3431ac56-3dc6-4230-ba4a-3bf5e0f2d086", "8045836c-0647-4a0a-9a00-7d299b4599f8"),
        _candidate("carpenter_assistant", 2_031_808_579, "b5ba37e3-3cc5-46dd-9398-89ecbc6a9bd7", "31ff0824-2c28-4934-a236-d3aa5c0306b9"),
        _candidate("hunter", 2_242_206_866, "3dbdc1d0-98e7-4b25-9327-937444b6ac87", "a6db3870-a426-494e-a203-64789389e7d7"),
        _candidate("hunter_assistant", 1_633_192_162, "eeae5607-6361-4067-b608-26e93c7cef71", "e3736dff-0ad2-47fc-903c-66c1775836e8"),
        _candidate("farmer", 974_506_154, "2ba6961c-f842-49bd-9551-654c82cb6de0", "1b533365-f465-42e0-a51f-7d66e9cf3659"),
        _candidate("farmer_assistant", 1_669_027_340, "79a17ecf-390b-4c1c-baec-5f5ac48a95f1", "a6bab01b-a848-4645-84fb-6ae22b532eb0"),
        _candidate("bard", 218_342_694, "b3923138-2f51-44db-9a85-c400a342ff7b", "23a61977-ae52-443d-ab6f-23826a2cda5a"),
        _candidate("bard_assistant", 1_640_210_983, "b55d2fef-1d05-43ea-aa2a-7fe0fcd27bc2", "ff6cd2cf-b566-482c-ba14-075d1a918b3d"),
        _candidate("crypt_keeper", 757_847_452, "48aee0f0-ba8f-4045-9595-42b0723d67a2", "b61da3e5-b8f2-4933-84f8-48e7ecfcba39"),
        _candidate("crypt_keeper_assistant", 2_159_156_280, "f0e9d8f1-9af1-4426-8cdb-5bbf1453fb32", "aa51d579-d35f-433e-be91-d4f7133d62c5"),
        _candidate("barber", 3_689_431_984, "828d1363-f824-4552-8f0a-1303bd369d14", "f63dc05f-88ed-4f5a-9640-1d19d980bb37"),
        _candidate("researcher", 1_095_951_179, "a343beaa-e10f-4395-981d-ac3e8ca6a785", "35afe333-75a0-45ec-90d4-5abddb08fdc5"),
        _candidate("trader", 2_797_365_275, "05e5697b-983f-4a99-a1c9-77a39bead07a", "877ab652-90f8-45da-8865-70e4e0fedc57"),
        _candidate("fisher", 4_192_796_482, "d2561878-5596-4b29-bfa2-0ce0da1f65d5", "e7666cd3-e530-4f9d-9586-519e4ab969dc"),
    )
}
CANDIDATES = MappingProxyType(_CANDIDATES)


class BodyUnavailable(RuntimeError):
    pass


def candidate(key: str) -> HumanCandidate:
    try:
        return CANDIDATES[key]
    except (KeyError, TypeError) as exc:
        raise BodyUnavailable("unknown_human_body") from exc


def require_runtime_body(key: str) -> HumanCandidate:
    body = candidate(key)
    if not body.runtime_enabled:
        raise BodyUnavailable("human_body_not_runtime_verified")
    return body


@dataclass(frozen=True)
class IdentityObservation:
    entity_id: int
    session: str
    model_guid: str | None
    npc_id: int | None
    kind: str | None


class IdentityGate:
    """Latch identity failures and require consecutive complete observations.

    The gate is usable only after a model GUID has been obtained by a read-only
    resource survey.  It still cannot distinguish an instantaneous replacement
    with an identical entity; that engine limitation remains documented.
    """

    def __init__(self, body: HumanCandidate, *, session: str, entity_id: int,
                 model_guid: str | None, stable_observations: int = 3,
                 acquisition_limit: int = 30):
        if stable_observations < 2 or acquisition_limit < stable_observations:
            raise ValueError("invalid_identity_window")
        self.body = body
        self.session = session
        self.entity_id = entity_id
        self.model_guid = model_guid
        self.stable_observations = stable_observations
        self.acquisition_limit = acquisition_limit
        self.observations = 0
        self.stable = 0
        self.invalidated = False
        self.reason = "fingerprint_pending"

    @property
    def trusted(self):
        return not self.invalidated and self.stable >= self.stable_observations

    @property
    def deletable(self):
        return self.trusted

    def observe(self, value: IdentityObservation | None, *, reflection_error=False):
        if self.invalidated:
            return "identity_changed"
        self.observations += 1
        if self.model_guid is None:
            self.reason = "expected_model_unknown"
            return "blocked"
        if reflection_error:
            self.stable = 0
            self.reason = "reflection_error"
        elif value is None or value.model_guid is None or value.npc_id is None or value.kind is None:
            self.stable = 0
            self.reason = "fingerprint_incomplete"
        elif (value.entity_id != self.entity_id or value.session != self.session
              or value.model_guid != self.model_guid or value.npc_id != self.body.npc_id
              or value.kind != "active_npc"):
            self.invalidated = True
            self.stable = 0
            self.reason = "identity_changed"
            return self.reason
        else:
            self.stable += 1
            self.reason = "trusted" if self.trusted else "fingerprint_stabilizing"
            return self.reason
        if self.observations >= self.acquisition_limit:
            self.invalidated = True
            self.reason = "fingerprint_timeout"
        return self.reason

    def permits_delete(self, current: IdentityObservation | None):
        if not self.trusted or current is None:
            return False
        expected = IdentityObservation(self.entity_id, self.session, self.model_guid,
                                       self.body.npc_id, "active_npc")
        if current != expected:
            self.invalidated = True
            self.reason = "identity_changed"
            return False
        return True
