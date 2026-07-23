"""Delegation Service exceptions, tied to stable reason codes.

Canon section-24 codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED` (defined in `application.py`, mirroring every other
service's own per-module `PermissionDeniedError`), `DELEGATION_CYCLE`,
`DELEGATION_EXPIRED`. Additive codes (this service's own, none of them
conflict with a canon-assigned code): `DELEGATION_SELF_REFERENCE_FORBIDDEN`,
`DELEGATION_SCOPE_CONFLICT`, `DELEGATION_SNAPSHOT_FROZEN`,
`DELEGATION_DUPLICATE_CREATION_CONFLICT`.
"""

from __future__ import annotations


class UnknownDelegationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenDelegationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownDelegationError(ValueError):
    """Raised for a plain lookup miss (no `Delegation` exists for the given
    `delegation_id`) - distinct from `UnknownDelegationStatusError`, which
    describes an out-of-enum status value on a delegation that does
    exist (see ADR-004's precedent, reused here)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class SelfDelegationError(ValueError):
    """Canon section 16.1 prohibition #1 ("самоделегирование"):
    `delegator_actor_id` and `delegate_actor_id` must never be equal.
    Raised both structurally, in `Delegation.__post_init__`, and again by
    `application.create_delegation` before it ever constructs a
    `Delegation` (belt-and-suspenders)."""

    reason_code = "DELEGATION_SELF_REFERENCE_FORBIDDEN"


class DelegationScopeConflictError(ValueError):
    """Canon section 16.1 prohibition #2 ("две конкурирующие активные
    делегации одного scope"): at most one `draft`/`active` `Delegation`
    may exist per `(delegator_actor_id, scope_type, scope_id)` triple -
    enforced by `storage.InMemoryDelegationStore.create`."""

    reason_code = "DELEGATION_SCOPE_CONFLICT"


class DelegationCreationConflictError(ValueError):
    """A repeated `create_delegation` request with the same
    `delegation_id` but different content (CT-00-04 analogue for
    creation, mirroring `epd2_voting_service.exceptions.BallotCreationConflictError`).
    """

    reason_code = "DELEGATION_DUPLICATE_CREATION_CONFLICT"


class DelegationCycleError(ValueError):
    """ADR-009 item 9: maximum delegation depth is 1 (no re-delegation
    chains) for this pilot. Raised by `application.create_delegation` when
    the proposed `delegate_actor_id` is themselves currently an active
    `delegator_actor_id` on another active `Delegation` for the same
    `(scope_type, scope_id)` - creating the requested delegation would
    produce a depth-2 chain, which this pilot's canon section-24
    `DELEGATION_CYCLE` code covers as a degenerate one-step cycle (full
    multi-hop cycle detection is future scope - see README.md)."""

    reason_code = "DELEGATION_CYCLE"


class DelegationExpiredError(ValueError):
    """Canon section-24 code reused verbatim: a `Delegation` was presented
    or relied upon after its own `valid_until` had already passed.
    Raised by `application.activate_delegation` when `clock.now()` is at
    or past a `draft` delegation's own `valid_until` at the moment of
    activation - activating an already-time-expired draft would be
    exactly this "relied upon after expiry" situation."""

    reason_code = "DELEGATION_EXPIRED"


class SnapshotFrozenError(ValueError):
    """Canon section 16.1 prohibition #4 ("изменение snapshot после
    открытия голосования") / CT-00-10 analogue: a `DelegationSnapshot` is
    immutable once created for a given `(ballot_id, input_hash)` key -
    raised by `storage.InMemoryDelegationSnapshotStore.save` when an
    attempt is made to persist different content under an already-used
    key."""

    reason_code = "DELEGATION_SNAPSHOT_FROZEN"
