"""`Delegation`, `DelegationSnapshot`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 16 (ADR-005
consolidates "Delegation Service" and "Delegation Resolution Engine" into
this one package).

No PACK-02 and no PACK-03↔PACK-03 import dependency (ADR-008 item 3): a
`DelegationSnapshot` is conceptually tied to a `Ballot`, but this module
only ever accepts `ballot_id: UUID` as an opaque reference, never a real
`Ballot` object, and never imports `epd2_voting_service` — see README.md.

Canon section 16.1's four explicit prohibitions ("Запреты") and how each
is enforced:

1. "самоделегирование" (self-delegation) — `Delegation.__post_init__`
   below rejects `delegator_actor_id == delegate_actor_id` structurally,
   independent of whether a caller goes through
   `application.create_delegation` at all. `application.create_delegation`
   re-checks the same condition itself before ever constructing a
   `Delegation` (belt-and-suspenders — see its own docstring).
2. "две конкурирующие активные делегации одного scope" (two competing
   active delegations of the same scope) — enforced in `storage.py`:
   `InMemoryDelegationStore.create` rejects a second `draft`/`active`
   `Delegation` for the same `(delegator_actor_id, scope_type, scope_id)`.
3. "скрытое бессрочное делегирование" (hidden indefinite delegation) —
   `valid_until: datetime | None` is an explicit, always-visible dataclass
   field; "indefinite" must be a conscious, explicit `None` a caller
   chose, never an implicit default nobody set (there is no default value
   for this field at all — every construction site must supply it). See
   README.md's "hidden indefinite delegation" section for the full
   argument; this module additionally requires `valid_until`, when set,
   to be strictly after `valid_from`.
4. "изменение snapshot после открытия голосования" (changing a snapshot
   after voting has opened) — `DelegationSnapshot` is immutable once
   created; the freeze-by-`input_hash` guarantee lives in
   `storage.InMemoryDelegationSnapshotStore.save`, mirroring
   `epd2_eligibility_service.storage.InMemoryEligibilityRuleStore.save`'s
   own "rule freeze" pattern exactly. See README.md.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_delegation_service.exceptions import (
    ForbiddenDelegationTransitionError,
    SelfDelegationError,
    UnknownDelegationStatusError,
)

# ============================================================================
# Identity-separation (mirrors epd2_voting_service.domain.FORBIDDEN_FIELD_NAMES)
# ============================================================================

#: Neither `Delegation` nor `DelegationSnapshot` may ever carry one of
#: these field names - both entities deal exclusively in opaque
#: `*_actor_id` references, never an `Account`/`IdentityRecord` reference.
#: See `tests/test_domain.py`'s
#: `assert set(__dataclass_fields__) & FORBIDDEN_FIELD_NAMES == set()`
#: checks on both dataclasses below.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "identity_record_id",
    }
)


# ============================================================================
# Delegation (canon 16.1)
# ============================================================================


class DelegationStatus(StrEnum):
    """Canon section 16.1's exact status list (6 values)."""

    DRAFT = "draft"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    INVALID = "invalid"


def parse_delegation_status(value: str) -> DelegationStatus:
    try:
        return DelegationStatus(value)
    except ValueError as exc:
        raise UnknownDelegationStatusError(f"unknown delegation status: {value!r}") from exc


#: Exact transition table given by spec.
ALLOWED_TRANSITIONS: frozenset[tuple[DelegationStatus, DelegationStatus]] = frozenset(
    {
        (DelegationStatus.DRAFT, DelegationStatus.ACTIVE),
        (DelegationStatus.ACTIVE, DelegationStatus.REVOKED),
        (DelegationStatus.ACTIVE, DelegationStatus.EXPIRED),
        (DelegationStatus.ACTIVE, DelegationStatus.SUSPENDED),
        (DelegationStatus.SUSPENDED, DelegationStatus.ACTIVE),
        (DelegationStatus.SUSPENDED, DelegationStatus.REVOKED),
        (DelegationStatus.DRAFT, DelegationStatus.INVALID),
        (DelegationStatus.ACTIVE, DelegationStatus.INVALID),
    }
)


def assert_delegation_transition_allowed(
    current: DelegationStatus, target: DelegationStatus
) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenDelegationTransitionError(
            f"delegation transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: Statuses `storage.InMemoryDelegationStore.create` treats as "blocking"
#: for canon prohibition #2 (two competing active delegations of the same
#: scope): a `draft` is pending activation and, per this service's own
#: documented choice (see README.md's "scope conflict" section), already
#: reserves its `(delegator_actor_id, scope_type, scope_id)` triple, not
#: just an `active` delegation.
BLOCKING_SCOPE_STATUSES: frozenset[DelegationStatus] = frozenset(
    {DelegationStatus.DRAFT, DelegationStatus.ACTIVE}
)


@dataclass(frozen=True, slots=True)
class Delegation:
    """Canon section 16.1 fields exactly - no extra public field.

    `revocation_status` is a canon field distinct from `status`; canon
    gives it no enumerated value list. Mirroring
    `epd2_voting_service.domain.Ballot`'s own precedent for policy strings
    canon leaves open (`secrecy_mode`, `quorum_rule`, `threshold_rule`),
    this service treats `revocation_status` as an opaque, caller-supplied
    `str` with no service-side enum validation - see README.md.
    """

    delegation_id: UUID
    delegator_actor_id: UUID
    delegate_actor_id: UUID
    scope_type: str
    scope_id: UUID
    valid_from: datetime
    valid_until: datetime | None
    revocation_status: str
    status: DelegationStatus

    def __post_init__(self) -> None:
        # Prohibition #1 ("самоделегирование") - structural, independent
        # of any application-layer check.
        if self.delegator_actor_id == self.delegate_actor_id:
            raise SelfDelegationError(
                f"delegator_actor_id and delegate_actor_id must differ "
                f"(both are {self.delegator_actor_id})"
            )
        if self.valid_from.tzinfo is None:
            raise ValueError("valid_from must be timezone-aware")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None:
                raise ValueError("valid_until must be timezone-aware")
            # Prohibition #3 ("скрытое бессрочное делегирование") support
            # check: an explicit valid_until must at least describe a
            # non-empty validity window.
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be strictly after valid_from")
        if not self.scope_type:
            raise ValueError("scope_type must not be empty")

    def with_status(self, new_status: DelegationStatus) -> Delegation:
        assert_delegation_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)


# ============================================================================
# DelegationSnapshot (canon 16.2)
# ============================================================================


@dataclass(frozen=True, slots=True)
class DelegationSnapshot:
    """Canon section 16.2 fields exactly. Immutable once created - see
    `storage.InMemoryDelegationSnapshotStore.save` for the freeze-by-
    `input_hash` enforcement (canon prohibition #4), mirroring
    `epd2_eligibility_service.domain.EligibilitySnapshot`'s own immutable-
    snapshot pattern.

    `resolved_weights`: delegate_actor_id -> total weight (how many
    delegators' votes that delegate carries after resolution).
    `cycle_records`: opaque diagnostic strings for any depth-limit
    rejections encountered during resolution - not full cycle detection,
    just a record of what was defensively excluded and why (see
    `application.resolve_delegation_snapshot`).
    """

    delegation_snapshot_id: UUID
    ballot_id: UUID
    policy_version: int
    created_at: datetime
    input_hash: str
    resolved_weights: Mapping[UUID, int]
    cycle_records: tuple[str, ...]
    snapshot_hash: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if not self.input_hash:
            raise ValueError("input_hash must not be empty")
        if not self.snapshot_hash:
            raise ValueError("snapshot_hash must not be empty")
        for delegate_actor_id, weight in self.resolved_weights.items():
            if weight < 1:
                raise ValueError(
                    f"resolved_weights[{delegate_actor_id}] must be >= 1, got {weight}"
                )


def compute_delegation_snapshot_input_hash(
    *,
    ballot_id: UUID,
    policy_version: int,
    scope_type: str,
    scope_id: UUID,
    delegator_actor_ids: frozenset[UUID],
    direct_voters: frozenset[UUID],
) -> str:
    """Deterministic digest over exactly the *inputs* to one resolution
    run - the `(ballot_id, input_hash)` pair is this service's freeze key
    (canon prohibition #4 / CT-00-10 analogue), mirroring
    `epd2_eligibility_service.domain.compute_snapshot_digest`'s style.
    Sorting the two id sets first makes the digest independent of
    collection/iteration order.
    """
    payload = {
        "ballot_id": ballot_id,
        "policy_version": policy_version,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "delegator_actor_ids": sorted(str(i) for i in delegator_actor_ids),
        "direct_voters": sorted(str(i) for i in direct_voters),
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


def compute_delegation_snapshot_hash(
    *,
    input_hash: str,
    resolved_weights: Mapping[UUID, int],
    cycle_records: tuple[str, ...],
) -> str:
    """Deterministic digest over one resolution run's *result* (folded
    together with its own `input_hash`), used by
    `storage.InMemoryDelegationSnapshotStore.save` to tell an idempotent
    replay (identical `snapshot_hash` for the same `(ballot_id,
    input_hash)` key) apart from a genuine attempt to change an
    already-frozen snapshot's content (different `snapshot_hash` for the
    same key - `SnapshotFrozenError`). Deliberately excludes
    `created_at`/`delegation_snapshot_id` so that two runs producing the
    same logical result at different wall-clock instants are recognized
    as the same content, not a spurious freeze violation. `resolved_weights`
    needs no explicit sort here - `canonical_dumps` already sorts every
    object's keys; `cycle_records` is a plain list, so it IS explicitly
    sorted, making the digest independent of the order diagnostics were
    appended in.
    """
    payload = {
        "input_hash": input_hash,
        "resolved_weights": {str(k): v for k, v in resolved_weights.items()},
        "cycle_records": sorted(cycle_records),
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()
