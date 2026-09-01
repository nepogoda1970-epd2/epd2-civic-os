"""Account Registry - the lifecycle model that does **not** extend the
canonical status enum.

Canon 7.2's six statuses (`pending`, `active`, `restricted`, `suspended`,
`recovery_pending`, `closed`) are the whole normative list, they stay in
`account-service`, and PACK-14 adds none. `locked`, `closure_pending` and
`deleted_or_anonymized` are therefore **not statuses here either**; each
is represented by the construct that actually owns it:

===================== ================================================
Situation             Representation
===================== ================================================
Technical lock        `AccountLock` - cause, threshold, expiry,
                      unlock condition, reason code
Security quarantine   `AccountRestriction` of the security class -
                      authority, scope, reason code, review obligation
Closure requested     `AccountClosureRequest` state - requested,
                      cooling-off, cancelled, completed
Anonymized/deleted    a lifecycle **outcome** and its events
===================== ================================================

Several may hold at once, and that is the point (OD-P14-01): an account
can be `active` with a lock in force and a closure request pending, and
each of the three facts is separately queryable, separately explainable
and separately reversible. Collapsing them into one enum value would have
destroyed exactly that - and would have required a canon amendment to do
it.

**Four situations are never the same thing**, and this module keeps them
apart by type: a technical lock (`AccountLock`), a security quarantine
(`AccountRestriction`), a membership suspension decided by a party organ
(`AccountRegistryStatus.SUSPENDED`, with the decision owned by the
membership domain), and a voluntary closure (`AccountClosureRequest`).

**On the deliberately duplicated status enum.** `AccountRegistryStatus`
below repeats canon 7.2's six values and `account-service`'s allowed
transition set rather than importing them: `tests/repository/
test_service_boundaries.py` forbids an `identity-service` ->
`account-service` import outright, and `epd2_core`'s own charter forbids
it holding business rules. This is the same trade PACK-07 made three
times, and it is kept honest the same way - `tests/repository/
test_pack14_duplicated_logic_parity.py` asserts value-for-value and
transition-for-transition equality with `epd2_account_service.domain`, so
a future edit to either copy fails loudly instead of drifting.
**Ownership of canon 7.2's `Account` is unchanged: it stays with
`account-service`.**
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    AccountClosedError,
    AccountLockedError,
    AccountNotActivatedError,
    AccountQuarantinedError,
    AccountRestrictedError,
    AnonymizationInProgressError,
    AnonymizationNotStartedError,
    ClosureAlreadyRequestedError,
    ClosureNotRequestedError,
    ForbiddenAccountLifecycleTransitionError,
    ForbiddenClosureRequestTransitionError,
    ResourceVersionStaleError,
    UnknownAccountLockCauseError,
    UnknownAccountRestrictionClassError,
    UnknownAccountStatusValueError,
    UnknownClosureRequestStateError,
)
from epd2_identity_service.identifiers import AccountId, OrganizationScope, require_timezone


class AccountRegistryStatus(StrEnum):
    """Canon 7.2's exact status list - six values, not seven.

    A verbatim copy of `epd2_account_service.domain.AccountStatus`, held
    here only because a cross-service import is forbidden (module
    docstring). `locked`, `closure_pending` and `deleted_or_anonymized`
    are deliberately absent and no PACK-14 code path adds them: each is
    represented by `AccountLock`, `AccountClosureRequest` state and a
    lifecycle outcome respectively (OD-P14-01).
    """

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    RECOVERY_PENDING = "recovery_pending"
    CLOSED = "closed"


def parse_account_status(value: str) -> AccountRegistryStatus:
    try:
        return AccountRegistryStatus(value)
    except ValueError as exc:
        raise UnknownAccountStatusValueError(f"unknown account status: {value!r}") from exc


class AccountLockCause(StrEnum):
    """Why a lock exists. Each cause has its own clearing condition, so a
    single `LOCKED` value would tell an operator nothing about how the
    holder gets back in."""

    REPEATED_AUTHENTICATION_FAILURE = "repeated_authentication_failure"
    CREDENTIAL_COMPROMISE_SUSPECTED = "credential_compromise_suspected"
    SESSION_REPLAY_DETECTED = "session_replay_detected"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    ADMINISTRATIVE_HOLD = "administrative_hold"


def parse_lock_cause(value: str) -> AccountLockCause:
    try:
        return AccountLockCause(value)
    except ValueError as exc:
        raise UnknownAccountLockCauseError(f"unknown account lock cause: {value!r}") from exc


class AccountRestrictionClass(StrEnum):
    """Restriction classes. `SECURITY_QUARANTINE` is the one OD-P14-01
    moved out of the status enum: it is a restriction with a named
    authority and a review obligation, not a different kind of
    account."""

    SECURITY_QUARANTINE = "security_quarantine"
    ABUSE_REVIEW = "abuse_review"
    LEGAL_HOLD_RELATED = "legal_hold_related"
    COMPLIANCE_REVIEW = "compliance_review"


def parse_restriction_class(value: str) -> AccountRestrictionClass:
    try:
        return AccountRestrictionClass(value)
    except ValueError as exc:
        raise UnknownAccountRestrictionClassError(f"unknown restriction class: {value!r}") from exc


class ClosureRequestState(StrEnum):
    """The lifecycle that belongs to the *request*, not to the account.
    While a request is open the account is still `active`, which is why
    "closure pending" was never an account status."""

    REQUESTED = "requested"
    COOLING_OFF = "cooling_off"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


def parse_closure_state(value: str) -> ClosureRequestState:
    try:
        return ClosureRequestState(value)
    except ValueError as exc:
        raise UnknownClosureRequestStateError(f"unknown closure request state: {value!r}") from exc


_ALLOWED_CLOSURE_TRANSITIONS: frozenset[tuple[ClosureRequestState, ClosureRequestState]] = (
    frozenset(
        {
            (ClosureRequestState.REQUESTED, ClosureRequestState.COOLING_OFF),
            (ClosureRequestState.REQUESTED, ClosureRequestState.CANCELLED),
            (ClosureRequestState.COOLING_OFF, ClosureRequestState.CANCELLED),
            (ClosureRequestState.COOLING_OFF, ClosureRequestState.COMPLETED),
        }
    )
)


class AnonymizationState(StrEnum):
    """Anonymization is an **outcome** an account reaches, tracked here so
    a run can be resumed and audited - never a status the account is
    reported as being in."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class AccountLock:
    """A technical lock. Temporary, automatic and self-clearing.

    `expires_at` is mandatory: a lock without an expiry is a suspension
    wearing a lock's clothes, and suspension is a governed status decided
    by a party organ, not something a failed-login counter may reach.
    """

    lock_id: UUID
    account_id: AccountId
    cause: AccountLockCause
    reason_code: str
    locked_at: datetime
    expires_at: datetime
    unlock_condition: str
    released_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.locked_at, "locked_at")
        require_timezone(self.expires_at, "expires_at")
        if self.released_at is not None:
            require_timezone(self.released_at, "released_at")
        if self.expires_at <= self.locked_at:
            raise ValueError("a lock must expire after it was applied")
        if not self.unlock_condition:
            raise ValueError("unlock_condition must not be empty")

    def is_in_force(self, now: datetime) -> bool:
        return self.released_at is None and now < self.expires_at

    def released(self, *, released_at: datetime) -> AccountLock:
        return replace(self, released_at=require_timezone(released_at, "released_at"))


@dataclass(frozen=True, slots=True)
class AccountRestriction:
    """A restriction with a **named authority**.

    The authority reference is mandatory and non-empty. That single
    requirement is what separates a restriction from a lock: someone
    decided this, someone is answerable for it, and someone can be asked
    to lift it.
    """

    restriction_id: UUID
    account_id: AccountId
    restriction_class: AccountRestrictionClass
    authority_reference: str
    reason_code: str
    scope: OrganizationScope
    applied_at: datetime
    review_due_at: datetime
    expires_at: datetime | None = None
    lifted_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.applied_at, "applied_at")
        require_timezone(self.review_due_at, "review_due_at")
        if self.expires_at is not None:
            require_timezone(self.expires_at, "expires_at")
        if self.lifted_at is not None:
            require_timezone(self.lifted_at, "lifted_at")
        if not self.authority_reference:
            raise ValueError("a restriction requires a named authority")
        if not self.reason_code:
            raise ValueError("a restriction requires a registered reason code")

    def is_in_force(self, now: datetime) -> bool:
        if self.lifted_at is not None:
            return False
        return self.expires_at is None or now < self.expires_at

    def lifted(self, *, lifted_at: datetime) -> AccountRestriction:
        return replace(self, lifted_at=require_timezone(lifted_at, "lifted_at"))


@dataclass(frozen=True, slots=True)
class AccountClosureRequest:
    """The request's own lifecycle. Cancellable during cooling-off, per
    the workflow matrix."""

    closure_request_id: UUID
    account_id: AccountId
    state: ClosureRequestState
    closure_reason: str
    requested_at: datetime
    cooling_off_ends_at: datetime
    retention_acknowledged: bool
    membership_notice_acknowledged: bool
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, "requested_at")
        require_timezone(self.cooling_off_ends_at, "cooling_off_ends_at")
        if self.resolved_at is not None:
            require_timezone(self.resolved_at, "resolved_at")
        if not self.retention_acknowledged:
            raise ValueError(
                "closure requires an explicit acknowledgement that some records are retained"
            )

    def is_open(self) -> bool:
        return self.state in (ClosureRequestState.REQUESTED, ClosureRequestState.COOLING_OFF)

    def transitioned(self, target: ClosureRequestState, *, at: datetime) -> AccountClosureRequest:
        if (self.state, target) not in _ALLOWED_CLOSURE_TRANSITIONS:
            raise ForbiddenClosureRequestTransitionError(
                f"closure request transition {self.state.value!r} -> "
                f"{target.value!r} is not allowed"
            )
        resolved = (
            require_timezone(at, "at")
            if target in (ClosureRequestState.CANCELLED, ClosureRequestState.COMPLETED)
            else None
        )
        return replace(self, state=target, resolved_at=resolved)


#: The transitions the registry itself permits between canon's six
#: statuses. Deliberately the same set `account-service` already enforces
#: - PACK-14 reuses the canonical lifecycle and does not fork it. The
#: registry checks it again here because a caller reaching this module
#: never touches `account-service.domain` directly.
ALLOWED_STATUS_TRANSITIONS: frozenset[tuple[AccountRegistryStatus, AccountRegistryStatus]] = (
    frozenset(
        {
            (AccountRegistryStatus.PENDING, AccountRegistryStatus.ACTIVE),
            (AccountRegistryStatus.PENDING, AccountRegistryStatus.CLOSED),
            (AccountRegistryStatus.ACTIVE, AccountRegistryStatus.RESTRICTED),
            (AccountRegistryStatus.ACTIVE, AccountRegistryStatus.SUSPENDED),
            (AccountRegistryStatus.ACTIVE, AccountRegistryStatus.RECOVERY_PENDING),
            (AccountRegistryStatus.ACTIVE, AccountRegistryStatus.CLOSED),
            (AccountRegistryStatus.RESTRICTED, AccountRegistryStatus.ACTIVE),
            (AccountRegistryStatus.RESTRICTED, AccountRegistryStatus.SUSPENDED),
            (AccountRegistryStatus.RESTRICTED, AccountRegistryStatus.CLOSED),
            (AccountRegistryStatus.SUSPENDED, AccountRegistryStatus.ACTIVE),
            (AccountRegistryStatus.SUSPENDED, AccountRegistryStatus.CLOSED),
            (AccountRegistryStatus.RECOVERY_PENDING, AccountRegistryStatus.ACTIVE),
            (AccountRegistryStatus.RECOVERY_PENDING, AccountRegistryStatus.CLOSED),
        }
    )
)


@dataclass(frozen=True, slots=True)
class AccountRegistryRecord:
    """The Account Registry's own record about an account.

    It holds the canonical `AccountStatus` value and the operational
    facts PACK-14 adds around it. It does **not** hold identity data -
    no name, no date of birth, no address - for the same structural
    reason canon 7.2's `Account` does not: the field set makes it
    impossible rather than discouraged.

    `version` is the optimistic-concurrency counter every consequential
    operation checks (ADR-077's discipline, applied to identity
    aggregates).
    """

    account_id: AccountId
    account_status: AccountRegistryStatus
    scope: OrganizationScope
    created_at: datetime
    activated_at: datetime | None
    anonymization_state: AnonymizationState
    version: int

    def __post_init__(self) -> None:
        require_timezone(self.created_at, "created_at")
        if self.activated_at is not None:
            require_timezone(self.activated_at, "activated_at")
        if self.version < 1:
            raise ValueError("version starts at 1")

    def assert_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise ResourceVersionStaleError(
                f"expected account version {expected_version}, stored version is {self.version}"
            )

    def with_status(self, target: AccountRegistryStatus) -> AccountRegistryRecord:
        if (self.account_status, target) not in ALLOWED_STATUS_TRANSITIONS:
            raise ForbiddenAccountLifecycleTransitionError(
                f"account status transition {self.account_status.value!r} -> "
                f"{target.value!r} is not allowed"
            )
        return replace(self, account_status=target, version=self.version + 1)


def create_account_record(
    *,
    account_id: AccountId,
    scope: OrganizationScope,
    created_at: datetime,
) -> AccountRegistryRecord:
    """A new account starts `pending`. It becomes `active` only when a
    contact channel has been verified - never on creation, because an
    unverified account that can act is an unowned account that can act."""
    return AccountRegistryRecord(
        account_id=account_id,
        account_status=AccountRegistryStatus.PENDING,
        scope=scope,
        created_at=require_timezone(created_at, "created_at"),
        activated_at=None,
        anonymization_state=AnonymizationState.NOT_STARTED,
        version=1,
    )


def activate_account_record(
    record: AccountRegistryRecord,
    *,
    expected_version: int,
    activated_at: datetime,
) -> AccountRegistryRecord:
    record.assert_version(expected_version)
    activated = record.with_status(AccountRegistryStatus.ACTIVE)
    return replace(activated, activated_at=require_timezone(activated_at, "activated_at"))


def begin_anonymization(
    record: AccountRegistryRecord, *, expected_version: int
) -> AccountRegistryRecord:
    """Anonymization runs only against a closed account, and only once.

    A second concurrent run would race the first over the same records,
    and a half-anonymized account is exactly the state from which a
    correlation vulnerability is reconstructed.
    """
    record.assert_version(expected_version)
    if record.account_status is not AccountRegistryStatus.CLOSED:
        raise ForbiddenAccountLifecycleTransitionError(
            "anonymization runs only against a closed account"
        )
    if record.anonymization_state is AnonymizationState.IN_PROGRESS:
        raise AnonymizationInProgressError("anonymization is already in progress")
    if record.anonymization_state is AnonymizationState.COMPLETED:
        raise AnonymizationInProgressError("anonymization has already completed")
    return replace(
        record, anonymization_state=AnonymizationState.IN_PROGRESS, version=record.version + 1
    )


def complete_anonymization(
    record: AccountRegistryRecord, *, expected_version: int
) -> AccountRegistryRecord:
    record.assert_version(expected_version)
    if record.anonymization_state is not AnonymizationState.IN_PROGRESS:
        raise AnonymizationNotStartedError("anonymization was never begun for this account")
    return replace(
        record, anonymization_state=AnonymizationState.COMPLETED, version=record.version + 1
    )


def open_closure_request(
    record: AccountRegistryRecord,
    *,
    existing: AccountClosureRequest | None,
    closure_request_id: UUID,
    closure_reason: str,
    requested_at: datetime,
    cooling_off: timedelta,
    retention_acknowledged: bool,
    membership_notice_acknowledged: bool,
) -> AccountClosureRequest:
    if record.account_status is AccountRegistryStatus.CLOSED:
        raise AccountClosedError("the account is already closed")
    if existing is not None and existing.is_open():
        raise ClosureAlreadyRequestedError("a closure request is already open for this account")
    requested = require_timezone(requested_at, "requested_at")
    return AccountClosureRequest(
        closure_request_id=closure_request_id,
        account_id=record.account_id,
        state=ClosureRequestState.COOLING_OFF,
        closure_reason=closure_reason,
        requested_at=requested,
        cooling_off_ends_at=requested + cooling_off,
        retention_acknowledged=retention_acknowledged,
        membership_notice_acknowledged=membership_notice_acknowledged,
    )


def cancel_closure_request(
    request: AccountClosureRequest | None, *, cancelled_at: datetime
) -> AccountClosureRequest:
    if request is None or not request.is_open():
        raise ClosureNotRequestedError("no open closure request exists for this account")
    return request.transitioned(ClosureRequestState.CANCELLED, at=cancelled_at)


def complete_closure(
    record: AccountRegistryRecord,
    request: AccountClosureRequest | None,
    *,
    expected_version: int,
    completed_at: datetime,
) -> tuple[AccountRegistryRecord, AccountClosureRequest]:
    """Closure completes only after the cooling-off window has elapsed.

    The window is the whole control: it is the interval in which a person
    who did not request closure can stop it.
    """
    record.assert_version(expected_version)
    if request is None or not request.is_open():
        raise ClosureNotRequestedError("no open closure request exists for this account")
    moment = require_timezone(completed_at, "completed_at")
    if moment < request.cooling_off_ends_at:
        raise ForbiddenClosureRequestTransitionError(
            "the closure cooling-off window has not elapsed"
        )
    return (
        record.with_status(AccountRegistryStatus.CLOSED),
        request.transitioned(ClosureRequestState.COMPLETED, at=moment),
    )


def assert_account_usable(
    record: AccountRegistryRecord,
    *,
    locks: tuple[AccountLock, ...],
    restrictions: tuple[AccountRestriction, ...],
    now: datetime,
) -> None:
    """The gate every authentication and every consequential action
    passes.

    Order matters and is deliberate: closure first (terminal), then
    activation (the account is not yet anyone's), then quarantine, then
    other restrictions, then locks. Each raises its own code, so a person
    is told which of five different situations they are actually in
    rather than "account unavailable".
    """
    if record.account_status is AccountRegistryStatus.CLOSED:
        raise AccountClosedError("the account is closed")
    if record.account_status is AccountRegistryStatus.PENDING:
        raise AccountNotActivatedError("the account has not been activated")
    for restriction in restrictions:
        if not restriction.is_in_force(now):
            continue
        if restriction.restriction_class is AccountRestrictionClass.SECURITY_QUARANTINE:
            raise AccountQuarantinedError(
                f"a security quarantine applied by {restriction.authority_reference} is in force"
            )
        raise AccountRestrictedError(
            f"a {restriction.restriction_class.value} restriction applied by "
            f"{restriction.authority_reference} is in force"
        )
    for lock in locks:
        if lock.is_in_force(now):
            raise AccountLockedError(
                f"a technical lock ({lock.cause.value}) is in force until {lock.expires_at}"
            )
