"""Optimistic concurrency, transaction and unit-of-work contracts
(PACK-13 §6, §7; ADR-077).

Three decisions from ADR-077 are expressed as types here, because each
has a wrong default that a type can prevent:

1. **`ExpectedVersion` distinguishes "any version" from "must not
   exist".** Collapsing them turns a create-if-absent into a silent
   overwrite — a small modelling decision with a large failure mode
   (`P13-CC-009`).
2. **Last-write-wins is forbidden for consequential records.** The
   record class says whether overwrite resolution is admissible at all,
   and `ConcurrencyPolicy` refuses rather than resolving
   (`P13-CC-003`).
3. **An approval does not apply to a version that has changed since the
   approver saw it** (`P13-CC-005`). The approval carries the version it
   was taken against, and a moved aggregate returns it for a fresh
   decision with its own reason code.

`TransactionBoundary` and `UnitOfWorkReference` are contracts, not an
implementation: this package deploys no database. What they encode is
that one domain command executes within one local transaction boundary
in one domain's schema (`P13-TX-001`), that no external side effect
executes inside it (`P13-TX-004`), and that the authoritative state
change and its outbox record are committed together (`P13-TX-003`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    AggregateReference,
    ApprovalReference,
    DomainReference,
    OrganizationScopeReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    ConcurrencyApprovalOnChangedVersionError,
    ConcurrencyAuthorityLapsedError,
    ConcurrencyLastWriteWinsProhibitedError,
    ConcurrencyStaleAggregateVersionError,
    CrossDomainDirectAccessDeniedError,
)

# ---------------------------------------------------------------------------
# Aggregate and expected version
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AggregateVersion:
    """The monotonically increasing version of one aggregate instance
    (`P13-CC-001`).

    Version `0` means "does not yet exist". Every state-changing commit
    increments it by exactly one; a version that jumped is a lost write,
    not a fast writer."""

    aggregate: AggregateReference
    version: int

    def __post_init__(self) -> None:
        if self.version < 0:
            raise ValueError("AggregateVersion.version must not be negative")

    @property
    def exists(self) -> bool:
        return self.version > 0

    def next(self) -> AggregateVersion:
        return AggregateVersion(aggregate=self.aggregate, version=self.version + 1)


class ExpectedVersionKind(StrEnum):
    """The three distinct assertions a command can make about the version
    it is acting upon. They are three, not two, and never collapsed."""

    EXACT = "exact"
    ANY_EXISTING = "any_existing"
    MUST_NOT_EXIST = "must_not_exist"


@dataclass(frozen=True, slots=True)
class ExpectedVersion:
    """The version a command asserts it is acting upon.

    `MUST_NOT_EXIST` and `ANY_EXISTING` are separate kinds precisely so
    that a create-if-absent cannot silently become an overwrite
    (`P13-CC-009`). There is deliberately no "unspecified" kind: a
    command that does not state what it expects is a command whose
    concurrency behaviour nobody decided."""

    kind: ExpectedVersionKind
    version: int | None = None

    def __post_init__(self) -> None:
        if self.kind is ExpectedVersionKind.EXACT:
            if self.version is None:
                raise ValueError("ExpectedVersion.EXACT requires a version")
            if self.version < 1:
                raise ValueError("ExpectedVersion.EXACT requires a version of at least 1")
        elif self.version is not None:
            raise ValueError(f"ExpectedVersion.{self.kind.name} must not carry a version")

    @classmethod
    def exact(cls, version: int) -> ExpectedVersion:
        return cls(kind=ExpectedVersionKind.EXACT, version=version)

    @classmethod
    def any_existing(cls) -> ExpectedVersion:
        return cls(kind=ExpectedVersionKind.ANY_EXISTING)

    @classmethod
    def must_not_exist(cls) -> ExpectedVersion:
        return cls(kind=ExpectedVersionKind.MUST_NOT_EXIST)


# ---------------------------------------------------------------------------
# Decisions and conflicts
# ---------------------------------------------------------------------------


class ConcurrencyOutcome(StrEnum):
    PROCEED = "proceed"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class ConcurrencyConflict:
    """Everything a caller needs to act on a conflict (`P13-CC-008`).

    The caller learns *that* a conflict occurred, *on which aggregate*,
    *at which version*, and *whether a retry is admissible* — not merely
    that the request failed."""

    aggregate: AggregateReference
    expected: ExpectedVersion
    actual_version: int
    reason_code: str
    retry_admissible: bool


@dataclass(frozen=True, slots=True)
class ConcurrencyDecision:
    """The outcome of one version check."""

    outcome: ConcurrencyOutcome
    conflict: ConcurrencyConflict | None = None

    def __post_init__(self) -> None:
        if self.outcome is ConcurrencyOutcome.CONFLICT and self.conflict is None:
            raise ValueError("a CONFLICT decision must carry its ConcurrencyConflict")
        if self.outcome is ConcurrencyOutcome.PROCEED and self.conflict is not None:
            raise ValueError("a PROCEED decision must not carry a conflict")

    @property
    def proceeds(self) -> bool:
        return self.outcome is ConcurrencyOutcome.PROCEED


def evaluate_expected_version(
    current: AggregateVersion, expected: ExpectedVersion
) -> ConcurrencyDecision:
    """Evaluate `expected` against `current`, returning a decision.

    Returns rather than raises, because the caller decides whether a
    conflict is an exception or a value it hands back to a user
    interface. `ConcurrencyPolicy.require_proceed` turns a conflict into
    the registered refusal where an exception is what the call site
    wants."""
    if expected.kind is ExpectedVersionKind.MUST_NOT_EXIST:
        if current.exists:
            return _conflict(current, expected, retry_admissible=False)
        return ConcurrencyDecision(outcome=ConcurrencyOutcome.PROCEED)
    if expected.kind is ExpectedVersionKind.ANY_EXISTING:
        if not current.exists:
            return _conflict(current, expected, retry_admissible=False)
        return ConcurrencyDecision(outcome=ConcurrencyOutcome.PROCEED)
    if current.version != expected.version:
        # A stale expected version is retryable *after the caller re-reads*:
        # the state moved, and a fresh read plus a fresh decision may well
        # succeed. That is a different fact from "must not exist" failing,
        # where retrying the same command can never succeed.
        return _conflict(current, expected, retry_admissible=True)
    return ConcurrencyDecision(outcome=ConcurrencyOutcome.PROCEED)


def _conflict(
    current: AggregateVersion, expected: ExpectedVersion, *, retry_admissible: bool
) -> ConcurrencyDecision:
    return ConcurrencyDecision(
        outcome=ConcurrencyOutcome.CONFLICT,
        conflict=ConcurrencyConflict(
            aggregate=current.aggregate,
            expected=expected,
            actual_version=current.version,
            reason_code="CONCURRENCY_STALE_AGGREGATE_VERSION",
            retry_admissible=retry_admissible,
        ),
    )


class ConcurrencyPolicy:
    """The pure policy functions a command layer calls.

    A class rather than loose functions only so that the three rules read
    as one policy; it holds no state and performs no I/O."""

    @staticmethod
    def require_proceed(current: AggregateVersion, expected: ExpectedVersion) -> AggregateVersion:
        """Return the next version, or raise the registered refusal.

        There is no third branch. A silent overwrite is not among the
        outcomes this function can produce (`P13-CC-002`,
        `P13-CC-007`)."""
        decision = evaluate_expected_version(current, expected)
        conflict = decision.conflict
        if conflict is not None:
            raise ConcurrencyStaleAggregateVersionError(
                f"{conflict.aggregate.aggregate_type} "
                f"{conflict.aggregate.aggregate_id}: expected "
                f"{conflict.expected.kind.value}"
                + (f" {conflict.expected.version}" if conflict.expected.version else "")
                + f", actual version {conflict.actual_version}; "
                f"retry admissible after re-read: {conflict.retry_admissible}"
            )
        return current.next()

    @staticmethod
    def reject_last_write_wins(*, consequential: bool, context: str) -> None:
        """Refuse overwrite resolution for a consequential record.

        Where last-write-wins is admissible at all, the record class says
        so explicitly; this function is what makes "explicitly" mean
        something (`P13-CC-003`)."""
        if consequential:
            raise ConcurrencyLastWriteWinsProhibitedError(
                f"{context}: this record class bears a decision, an authorization, a "
                f"financial fact, a governed document state, a privileged grant, a "
                f"retention or hold state, or a legal effect; overwrite resolution is "
                f"refused and the conflict is returned to the caller"
            )

    @staticmethod
    def require_approval_still_current(
        approval: ApprovalReference, current: AggregateVersion
    ) -> None:
        """Refuse an approval taken against a version that has since
        moved (`P13-CC-005`).

        This is the concurrency expression of PACK-12's activation
        re-check, and it exists because "approve" means "approve
        *this*"."""
        if approval.approved_object_version != current.version:
            raise ConcurrencyApprovalOnChangedVersionError(
                f"approval {approval.approval_id} was taken against version "
                f"{approval.approved_object_version} of "
                f"{current.aggregate.aggregate_type} {current.aggregate.aggregate_id}, "
                f"which is now at version {current.version}; the approval is returned "
                f"for a fresh decision rather than applied to state the approver never saw"
            )

    @staticmethod
    def require_authority_effective_at_execution(
        *, authority_expires_at: datetime, executing_at: datetime, context: str
    ) -> None:
        """Re-check effective-dated authority at execution, not only at
        construction. Authority that lapsed in between is not authority
        (`P13-CC-006`)."""
        require_timezone(authority_expires_at, field="authority_expires_at")
        require_timezone(executing_at, field="executing_at")
        if executing_at >= authority_expires_at:
            raise ConcurrencyAuthorityLapsedError(
                f"{context}: the effective-dated authority expired at "
                f"{authority_expires_at.isoformat()} and execution is at "
                f"{executing_at.isoformat()}; authority is re-checked at execution"
            )


# ---------------------------------------------------------------------------
# Transaction and unit-of-work boundaries
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TransactionBoundary:
    """One local transaction boundary in one domain's schema
    (`P13-TX-001`).

    `permits_external_effect` exists as a field fixed to `False` rather
    than as a comment: `P13-TX-004` forbids any HTTP call, broker
    publish, file write or email inside a transaction, and a field that
    can only ever be `False` is a rule a future edit has to argue with."""

    owning_domain: DomainReference
    schema_name: str
    permits_external_effect: bool = False

    def __post_init__(self) -> None:
        if self.permits_external_effect:
            raise ValueError(
                "no external side effect executes inside a database transaction "
                "(P13-TX-004); an external effect begins only after durable intent is "
                "committed"
            )
        if not self.schema_name:
            raise ValueError("TransactionBoundary requires a schema name")


@dataclass(frozen=True, slots=True)
class UnitOfWorkReference:
    """A stable reference to one unit of work.

    The authoritative state change and the outbox record are written
    inside the same unit (`P13-TX-003`), and a rolled-back unit leaves
    no published event (`P13-TX-005`)."""

    unit_of_work_id: UUID
    boundary: TransactionBoundary
    scope: OrganizationScopeReference
    started_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.started_at, field="UnitOfWorkReference.started_at")

    def assert_same_domain(self, aggregate: AggregateReference) -> None:
        """Refuse a write to another domain's aggregate inside this unit
        of work (`P13-DP-014`). Not for convenience, not for
        performance, not during migration."""
        if aggregate.owning_domain.domain_name != self.boundary.owning_domain.domain_name:
            raise CrossDomainDirectAccessDeniedError(
                f"unit of work {self.unit_of_work_id} belongs to "
                f"{self.boundary.owning_domain.domain_name!r} and cannot write "
                f"{aggregate.aggregate_type} {aggregate.aggregate_id}, which is owned by "
                f"{aggregate.owning_domain.domain_name!r}; cross-domain consistency is "
                f"reached through governed contracts and events"
            )


@dataclass(frozen=True, slots=True)
class CommandExecutionReference:
    """A stable reference to one command execution.

    It links the three things that must be correlatable after the fact
    and are otherwise three unrelated rows: the idempotency record, the
    audit row, and the resulting aggregate version (`P13-CC` §7.1)."""

    command_execution_id: UUID
    command_name: str
    aggregate: AggregateReference
    actor: ActorReference
    scope: OrganizationScopeReference
    idempotency_key_digest: str
    resulting_version: int
    executed_at: datetime
    audit_reference: UUID | None = None
    conflicts: tuple[ConcurrencyConflict, ...] = field(default=())

    def __post_init__(self) -> None:
        require_timezone(self.executed_at, field="CommandExecutionReference.executed_at")
        if not self.command_name:
            raise ValueError("CommandExecutionReference requires a command name")
        if self.resulting_version < 0:
            raise ValueError("resulting_version must not be negative")


@dataclass(frozen=True, slots=True)
class OrganizationScopeAssertion:
    """A recorded assertion that a given record carried scope at a given
    boundary.

    Used by the migration and projection gates to make "scope was not
    lost" a checkable fact rather than a reviewer's impression
    (`P13-MIG-012`, `P13-PROJ-011`)."""

    asserted_at_boundary: str
    scope: OrganizationScopeReference
    record_count: int

    def __post_init__(self) -> None:
        if self.record_count < 0:
            raise ValueError("record_count must not be negative")
