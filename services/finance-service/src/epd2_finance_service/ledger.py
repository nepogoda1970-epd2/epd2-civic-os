"""Finance Service ledger - accounts, accounting periods, the double-entry
register and the transaction register (PACK-10 sections 4.1-4.3 and
8.2.1-8.2.4; canon 0.8.0 sections 19f.4-19f.6).

This module is pure. It performs no I/O, reads no clock, opens no storage
and imports from no other service: every identifier, every timestamp and
every sequence number is passed in by the application layer, exactly as
`compliance-service.domain` is for PACK-09.

The model is layered with a single authoritative money layer (ADR-049,
canon 19f.4/19f.6). `JournalEntry` with its ordered `PostingLine` tuple is
the authoritative record of *monetary effect*; trial balances, period
totals and every public view are derived read models, authoritative for
nothing. `FinancialTransaction` is the authoritative record of the
*business fact and its provenance*. Neither is a cache of the other, and
a transaction with monetary effect and no balanced, posted entry is an
incomplete state that fails closed on reporting.

Four rules shape everything below:

- **Balance is checked twice.** `assert_balanced` runs in the
  `JournalEntry` constructor and again inside `post`, per currency, never
  netting across currencies (`ФИН-07`, `ФИН-09`).
- **A posted entry is content-immutable.** `amend_draft` refuses anything
  but a draft; the only way to change monetary effect after posting is a
  new reversing or correcting entry citing the original and carrying a
  reason code (`ФИН-05`, `ФИН-06`).
- **The period lock lives inside the posting command.** `post` requires
  the `AccountingPeriod` and asks it directly; there is deliberately no
  overload that posts without one, because canon 19f.5 requires that no
  ordinary write path can reach a closed period (`ФИН-10`).
- **Reopening is dual control.** `assert_reopening_dual_control` refuses
  self-approval, and every reopening leaves a create-once
  `PeriodReopeningRecord` digesting the closed state (`ФИН-11`).

**Re-posting after a reversal has no special API, and that is
deliberate.** Once an entry has been reversed, the corrected monetary
effect is booked as an *ordinary* new `JournalEntry`, drafted and posted
through the same `post` command as any other entry. It is not a "re-post"
of the reversed entry, it does not reuse that entry's `entry_sequence`,
and it does not carry `reverses_entry_id`. Modelling it as a distinct
operation would create a second write path into the register - precisely
the bypass canon 19f.4 forbids. Where the new entry is semantically a
replacement rather than an independent booking, the caller links it with
`correct`, which sets `corrects_entry_id` and leaves the original's
posted status intact.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from epd2_finance_service.domain import (
    AuthorityReference,
    EvidenceReference,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    ReportingPeriodRef,
    RetentionBinding,
    deterministic_digest,
    require_timezone,
    sum_money,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodClosedError,
    AccountingPeriodUndeterminedError,
    ForbiddenIdentityLinkageError,
    ImmutableRecordModificationAttemptedError,
    ImportProvenanceMissingError,
    InvalidCorrectionTargetError,
    JournalEntryUnbalancedError,
    MonetaryAmountInvalidError,
    OptimisticConcurrencyConflictError,
    PeriodReopeningNotAuthorizedError,
    PolicyMissingError,
    UnauthorizedStateTransitionError,
)

# ---------------------------------------------------------------------------
# Shared structural helpers
# ---------------------------------------------------------------------------

#: The only shape a party may take anywhere in the finance domain: the
#: opaque string `FinancePartyHandle.as_reference()` produces. Anything
#: else presented as a party is a forbidden identity linkage, whatever it
#: happens to contain (canon 19f.15, `ФИН-01`, `ФИН-02`).
PARTY_HANDLE_REFERENCE_PREFIX = "fph:"


def _require_text(value: str, field_name: str) -> None:
    """Structural non-emptiness check.

    Raises `MonetaryAmountInvalidError` because that is the code
    `domain.py` already assigns to structural field validation here; a
    bare `ValueError` is never raised in finance code (`ФИН-40`)."""
    if not value or not value.strip():
        raise MonetaryAmountInvalidError(f"{field_name} must be a non-empty string")


def _require_party_handle_reference(value: str, field_name: str) -> None:
    """Refuse anything that is not an opaque party-handle reference.

    Checking the prefix structurally is what stops a caller smuggling a
    name, an IBAN or a user id into a party field (`ФИН-01`)."""
    if not value.startswith(PARTY_HANDLE_REFERENCE_PREFIX):
        raise ForbiddenIdentityLinkageError(
            f"{field_name} must be an opaque party-handle reference, not a direct identity"
        )


def _require_positive(value: int, field_name: str) -> None:
    if value < 1:
        raise MonetaryAmountInvalidError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class LedgerHistoryEntry:
    """One append-only entry in an account's or a period's own history.

    Nothing here is rewritten or dropped: a later status change appends,
    so what an account's classification was when a past entry posted
    against it stays answerable (`ФИН-05`, canon 19f.4)."""

    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    acting_authority: AuthorityReference
    state_after: str
    policy: PolicyBinding | None = None

    def __post_init__(self) -> None:
        _require_positive(self.sequence, "sequence")
        _require_text(self.action, "action")
        _require_text(self.state_after, "state_after")
        require_timezone(self.occurred_at, context="LedgerHistoryEntry.occurred_at")


def _next_sequence(history: tuple[LedgerHistoryEntry, ...]) -> int:
    return len(history) + 1


# ---------------------------------------------------------------------------
# Chart of accounts
# ---------------------------------------------------------------------------


class AccountStatus(StrEnum):
    """Lifecycle of a `FinanceAccount` (spec 8.2.1, canon 19f.4).

    `CLOSED` is terminal: no transition leaves it and no deletion exists,
    because a closed account still has to explain the postings made
    against it (`ФИН-05`)."""

    DRAFT = "draft"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    CLOSED = "closed"


#: The complete set of permitted account transitions. Anything absent is
#: refused with `UnauthorizedStateTransitionError`; `closed` reaches
#: nothing at all.
_ALLOWED_ACCOUNT_TRANSITIONS: frozenset[tuple[AccountStatus, AccountStatus]] = frozenset(
    {
        (AccountStatus.DRAFT, AccountStatus.ACTIVE),
        (AccountStatus.ACTIVE, AccountStatus.RESTRICTED),
        (AccountStatus.RESTRICTED, AccountStatus.ACTIVE),
        (AccountStatus.ACTIVE, AccountStatus.CLOSED),
        (AccountStatus.RESTRICTED, AccountStatus.CLOSED),
    }
)


@dataclass(frozen=True, slots=True)
class FinanceAccount:
    """A node of the chart of accounts, owned by exactly one scope.

    An account is never shared across scopes, and a consolidating scope
    reads it but never posts into it (`ФИН-03`, canon 19f.4/19f.19).
    `code` and `classification_code` come from the active
    `FinancePolicy(chart_of_accounts)` and neither may change once the
    account has carried a posting - which `has_postings` records
    explicitly, rather than inferring from an entry count this pure module
    cannot see (`ФИН-13`). `retention` binds the account to a PACK-09
    record class; retention and legal-hold semantics stay PACK-09's
    (`ФИН-22`)."""

    account_id: UUID
    code: str
    classification_code: str
    scope: OrganizationalScopeRef
    retention: RetentionBinding
    status: AccountStatus = AccountStatus.DRAFT
    has_postings: bool = False
    classification_policy: PolicyBinding | None = None
    history: tuple[LedgerHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        _require_text(self.classification_code, "classification_code")

    def _transition(
        self,
        target: AccountStatus,
        *,
        at: datetime,
        by_authority: AuthorityReference,
        reason: ReasonCoded,
        action: str,
    ) -> FinanceAccount:
        """Apply one enumerated transition, appending history. The table
        is consulted first, so a `closed` account refuses every request
        rather than partially applying one (`ФИН-05`)."""
        if (self.status, target) not in _ALLOWED_ACCOUNT_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.status!s} finance account cannot transition to {target!s}"
            )
        self.scope.assert_matches(by_authority.scope)
        entry = LedgerHistoryEntry(
            sequence=_next_sequence(self.history),
            occurred_at=at,
            action=action,
            reason=reason,
            acting_authority=by_authority,
            state_after=str(target),
        )
        return replace(self, status=target, history=(*self.history, entry))

    def activate(
        self, *, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> FinanceAccount:
        """Make a drafted account postable (spec 8.2.1)."""
        return self._transition(
            AccountStatus.ACTIVE,
            at=at,
            by_authority=by_authority,
            reason=reason,
            action="activated",
        )

    def restrict(
        self, *, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> FinanceAccount:
        """Suspend an active account. Restriction is reversible; closure
        is not."""
        return self._transition(
            AccountStatus.RESTRICTED,
            at=at,
            by_authority=by_authority,
            reason=reason,
            action="restricted",
        )

    def close(
        self, *, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> FinanceAccount:
        """Close the account permanently.

        The open-balance and open-reference preconditions of spec 8.2.1
        are resolved by the application layer against the register; what
        this aggregate guarantees is that `closed` is terminal."""
        return self._transition(
            AccountStatus.CLOSED, at=at, by_authority=by_authority, reason=reason, action="closed"
        )

    def mark_first_posting(self) -> FinanceAccount:
        """Latch `has_postings`. Once set it never clears: it is what
        freezes `code` and `classification_code` (`ФИН-13`)."""
        return self if self.has_postings else replace(self, has_postings=True)

    def reclassify(
        self,
        *,
        classification_code: str,
        policy: PolicyBinding,
        at: datetime,
        by_authority: AuthorityReference,
        reason: ReasonCoded,
    ) -> FinanceAccount:
        """Change the account's classification as an explicit, authorized,
        append-only act.

        Refused once the account has carried a posting: at that point the
        classification is part of what already-posted entries mean, and
        rewriting it would rewrite history (`ФИН-13`, canon 19f.4)."""
        _require_text(classification_code, "classification_code")
        if self.has_postings:
            raise ImmutableRecordModificationAttemptedError(
                "classification_code is frozen once the account has carried a posting"
            )
        if self.status is AccountStatus.CLOSED:
            raise UnauthorizedStateTransitionError(
                "a closed finance account cannot be reclassified"
            )
        entry = LedgerHistoryEntry(
            sequence=_next_sequence(self.history),
            occurred_at=at,
            action="reclassified",
            reason=reason,
            acting_authority=by_authority,
            state_after=str(self.status),
            policy=policy,
        )
        return replace(
            self,
            classification_code=classification_code,
            classification_policy=policy,
            history=(*self.history, entry),
        )

    def recode(
        self, *, code: str, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> FinanceAccount:
        """Change the scope-unique account code. Frozen after the first
        posting for the same reason as `reclassify` (`ФИН-13`)."""
        _require_text(code, "code")
        if self.has_postings:
            raise ImmutableRecordModificationAttemptedError(
                "code is frozen once the account has carried a posting"
            )
        entry = LedgerHistoryEntry(
            sequence=_next_sequence(self.history),
            occurred_at=at,
            action="recoded",
            reason=reason,
            acting_authority=by_authority,
            state_after=str(self.status),
        )
        return replace(self, code=code, history=(*self.history, entry))


# ---------------------------------------------------------------------------
# Accounting periods
# ---------------------------------------------------------------------------


class PeriodStatus(StrEnum):
    """Lifecycle of an `AccountingPeriod` (spec 8.2.2, canon 19f.5).

    `CLOSING` is a real, storable state and not a transient: it freezes
    new postings while corrections already in flight settle, which is why
    it denies `assert_open_for_posting` exactly as `CLOSED` does."""

    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    REOPENED = "reopened"


#: Period statuses in which an ordinary posting command may write.
#: Deliberately an enumerated set rather than "not closed": `closing` must
#: deny, and any future status must deny by default (`ФИН-10`).
_POSTABLE_PERIOD_STATUSES: frozenset[PeriodStatus] = frozenset(
    {PeriodStatus.OPEN, PeriodStatus.REOPENED}
)

_ALLOWED_PERIOD_TRANSITIONS: frozenset[tuple[PeriodStatus, PeriodStatus]] = frozenset(
    {
        (PeriodStatus.OPEN, PeriodStatus.CLOSING),
        (PeriodStatus.CLOSING, PeriodStatus.CLOSED),
        (PeriodStatus.OPEN, PeriodStatus.CLOSED),
        (PeriodStatus.CLOSED, PeriodStatus.REOPENED),
        (PeriodStatus.REOPENED, PeriodStatus.CLOSING),
        (PeriodStatus.REOPENED, PeriodStatus.CLOSED),
    }
)


def resolve_period_timezone(timezone_name: str) -> ZoneInfo:
    """Resolve an explicit IANA timezone name, or refuse to proceed.

    Period arithmetic is only meaningful against a named civil timezone;
    an empty, missing or unknown name is a fail-closed refusal, never a
    silent fallback to UTC (`ФИН-39`, `ФИН-42`)."""
    if not timezone_name or not timezone_name.strip():
        raise AccountingPeriodUndeterminedError("an explicit IANA timezone name is required")
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise AccountingPeriodUndeterminedError(f"unknown IANA timezone {timezone_name!r}") from exc


def assert_reopening_dual_control(
    requested_by: AuthorityReference, approved_by: AuthorityReference
) -> None:
    """Refuse a period reopening that one actor both requested and
    approved (`ФИН-11`, `ФИН-32`; canon 19f.5).

    Two things are compared, not one: distinct `authority_id`s are not
    enough if the same natural actor holds both assignments, so
    `actor_reference` is compared too whenever both sides carry one - a
    dual-control rule one person can satisfy alone is not one."""
    if requested_by.authority_id == approved_by.authority_id:
        raise PeriodReopeningNotAuthorizedError(
            "the approving authority must differ from the requesting authority"
        )
    requester_actor = requested_by.actor_reference.strip()
    approver_actor = approved_by.actor_reference.strip()
    if requester_actor and approver_actor and requester_actor == approver_actor:
        raise PeriodReopeningNotAuthorizedError(
            "the approving actor must differ from the requesting actor - self-approval is refused"
        )


@dataclass(frozen=True, slots=True)
class PeriodReopeningRecord:
    """The create-once record of one controlled reopening (`ФИН-11`).

    Create-once by design: no method here returns a modified copy, and the
    period only ever appends whole records. `closed_state_digest`
    snapshots what the period looked like when it was locked, so a later
    dispute about *what* was reopened is answerable from the record rather
    than a reconstruction (`ФИН-24`). Every reopening carries an explicit
    authority, an approving authority that is not the requester, a
    `ReasonCoded` and the bound policy version - silent reopening does not
    exist."""

    record_id: UUID
    period_id: UUID
    requested_by: AuthorityReference
    approved_by: AuthorityReference
    reason: ReasonCoded
    policy: PolicyBinding
    requested_at: datetime
    approved_at: datetime
    closed_state_digest: str
    legal_case_reference: str | None = None
    hold_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, context="PeriodReopeningRecord.requested_at")
        require_timezone(self.approved_at, context="PeriodReopeningRecord.approved_at")
        _require_text(self.closed_state_digest, "closed_state_digest")
        if self.approved_at < self.requested_at:
            raise PeriodReopeningNotAuthorizedError(
                "a reopening cannot be approved before it was requested"
            )
        assert_reopening_dual_control(self.requested_by, self.approved_by)


@dataclass(frozen=True, slots=True)
class AccountingPeriod:
    """The posting lock for one organizational scope (spec 8.2.2).

    Every posting command consults this aggregate; no ordinary write path
    reaches a closed period (`ФИН-10`). The period always carries a named
    IANA timezone - boundaries are civil-calendar facts and a naive
    datetime is refused rather than assumed to be UTC (`ФИН-39`,
    `ФИН-42`). `reopening_records` is append-only: each reopening adds one
    create-once record and none is ever rewritten."""

    period_id: UUID
    label: str
    scope: OrganizationalScopeRef
    timezone_name: str
    opens_at: datetime
    closes_at: datetime
    status: PeriodStatus = PeriodStatus.OPEN
    reopening_records: tuple[PeriodReopeningRecord, ...] = ()
    history: tuple[LedgerHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.label, "label")
        require_timezone(self.opens_at, context="AccountingPeriod.opens_at")
        require_timezone(self.closes_at, context="AccountingPeriod.closes_at")
        resolve_period_timezone(self.timezone_name)
        if self.closes_at <= self.opens_at:
            raise AccountingPeriodUndeterminedError("closes_at must be strictly after opens_at")

    def as_reference(self) -> ReportingPeriodRef:
        """The form this period takes on a record or in an event payload:
        an id, a label and a scope, never the lock state itself."""
        return ReportingPeriodRef(period_id=self.period_id, label=self.label, scope=self.scope)

    def assert_open_for_posting(self) -> None:
        """Raise unless an ordinary posting may be written into this
        period.

        `closing` denies as firmly as `closed`: it exists to freeze new
        postings while in-flight corrections settle, and a caller that
        treated it as "still open" would defeat the freeze (`ФИН-10`)."""
        if self.status not in _POSTABLE_PERIOD_STATUSES:
            raise AccountingPeriodClosedError(
                f"accounting period {self.label} is {self.status!s} and refuses ordinary postings"
            )

    def state_digest(self) -> str:
        """A deterministic digest of the period's identity, boundaries and
        lock state, used as the closed-state snapshot a reopening record
        carries. Derived only from stable stored values, so the same
        closed period always yields the same digest (`ФИН-24`)."""
        return deterministic_digest(
            str(self.period_id),
            self.label,
            str(self.scope.organization_id),
            self.timezone_name,
            self.opens_at.isoformat(),
            self.closes_at.isoformat(),
            str(self.status),
            str(len(self.reopening_records)),
        )

    def _transition(
        self,
        target: PeriodStatus,
        *,
        at: datetime,
        by_authority: AuthorityReference,
        reason: ReasonCoded,
        action: str,
        reopening_records: tuple[PeriodReopeningRecord, ...] | None = None,
    ) -> AccountingPeriod:
        if (self.status, target) not in _ALLOWED_PERIOD_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.status!s} accounting period cannot transition to {target!s}"
            )
        self.scope.assert_matches(by_authority.scope)
        entry = LedgerHistoryEntry(
            sequence=_next_sequence(self.history),
            occurred_at=at,
            action=action,
            reason=reason,
            acting_authority=by_authority,
            state_after=str(target),
        )
        records = self.reopening_records if reopening_records is None else reopening_records
        return replace(
            self, status=target, reopening_records=records, history=(*self.history, entry)
        )

    def begin_closing(
        self, *, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> AccountingPeriod:
        """Freeze new postings while corrections in flight settle."""
        return self._transition(
            PeriodStatus.CLOSING,
            at=at,
            by_authority=by_authority,
            reason=reason,
            action="closing_started",
        )

    def close(
        self, *, at: datetime, by_authority: AuthorityReference, reason: ReasonCoded
    ) -> AccountingPeriod:
        """Lock the period. The only route back to a postable state is
        `request_reopening` then `reopen` - dual-controlled, reason-coded
        and leaving a create-once record (`ФИН-10`, `ФИН-11`)."""
        return self._transition(
            PeriodStatus.CLOSED, at=at, by_authority=by_authority, reason=reason, action="closed"
        )

    def request_reopening(
        self,
        *,
        record_id: UUID,
        requested_by: AuthorityReference,
        approved_by: AuthorityReference,
        reason: ReasonCoded,
        policy: PolicyBinding,
        requested_at: datetime,
        approved_at: datetime,
        legal_case_reference: str | None = None,
        hold_reference: str | None = None,
    ) -> PeriodReopeningRecord:
        """Build the create-once reopening record for this period.

        Separate from `reopen` on purpose: the record *is* the evidence
        that dual control happened, and constructing it performs the
        checks. It snapshots the closed-state digest, so it is built
        before the status changes and only for a closed period
        (`ФИН-11`)."""
        if self.status is not PeriodStatus.CLOSED:
            raise UnauthorizedStateTransitionError(
                f"only a closed accounting period can be reopened; this one is {self.status!s}"
            )
        self.scope.assert_matches(requested_by.scope)
        self.scope.assert_matches(approved_by.scope)
        return PeriodReopeningRecord(
            record_id=record_id,
            period_id=self.period_id,
            requested_by=requested_by,
            approved_by=approved_by,
            reason=reason,
            policy=policy,
            requested_at=requested_at,
            approved_at=approved_at,
            closed_state_digest=self.state_digest(),
            legal_case_reference=legal_case_reference,
            hold_reference=hold_reference,
        )

    def reopen(self, record: PeriodReopeningRecord, *, at: datetime) -> AccountingPeriod:
        """Apply a reopening record, moving the period to `reopened`.

        The record must belong to this period and must snapshot *this*
        closed state, so a stale approval cannot be replayed against a
        period that has since moved on (`ФИН-11`, `ФИН-24`)."""
        if record.period_id != self.period_id:
            raise PeriodReopeningNotAuthorizedError(
                "the reopening record does not belong to this accounting period"
            )
        if record.closed_state_digest != self.state_digest():
            raise PeriodReopeningNotAuthorizedError(
                "the reopening record snapshots a different closed state than the current one"
            )
        assert_reopening_dual_control(record.requested_by, record.approved_by)
        return self._transition(
            PeriodStatus.REOPENED,
            at=at,
            by_authority=record.approved_by,
            reason=record.reason,
            action="reopened",
            reopening_records=(*self.reopening_records, record),
        )


# ---------------------------------------------------------------------------
# Posting lines and the balancing rule
# ---------------------------------------------------------------------------


class PostingSide(StrEnum):
    """Which side of the register a posting line falls on.

    Direction is carried here and only here, so a "negative debit" - a
    second, undeclared way of expressing a credit - cannot exist."""

    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True, slots=True)
class PostingLine:
    """One line of a journal entry: an account, a side and an amount.

    A value object with no identity of its own: lines are not addressable,
    not individually versioned and never edited, so changing one means
    drafting a new entry (`ФИН-05`, canon 19f.4).
    `dimension_references` carries opaque analytical dimensions - cost
    centre, campaign, project - as references only; no dimension is ever a
    party, and none is resolved here."""

    account_id: UUID
    side: PostingSide
    amount: Money
    dimension_references: tuple[str, ...] = ()
    memo_reference: str | None = None

    def __post_init__(self) -> None:
        for dimension in self.dimension_references:
            _require_text(dimension, "dimension_reference")

    @property
    def is_debit(self) -> bool:
        return self.side is PostingSide.DEBIT

    def opposite(self) -> PostingLine:
        """The equal and opposite line, used to build a reversal. The
        amount is unchanged and only the side flips; reversal by negation
        would produce a second representation of the same effect."""
        flipped = PostingSide.CREDIT if self.is_debit else PostingSide.DEBIT
        return replace(self, side=flipped)


def assert_balanced(lines: tuple[PostingLine, ...]) -> None:
    """Raise unless debits equal credits, per currency (`ФИН-07`).

    An empty line set is refused - it would balance vacuously. A
    zero-value line is refused via `Money.assert_non_zero`, because a zero
    posting is the wrong tool for a non-monetary fact (canon 19f.4). A
    negative magnitude is refused, because direction belongs to
    `PostingSide`. Totals are accumulated and compared per currency and
    the failure names the offending one; nothing is ever netted across
    currencies, since no conversion has been recorded (`ФИН-09`)."""
    if not lines:
        raise JournalEntryUnbalancedError("a journal entry must carry at least one posting line")
    for index, line in enumerate(lines):
        line.amount.assert_non_zero(context=f"posting line {index}")
        if line.amount.minor_units < 0:
            raise MonetaryAmountInvalidError(
                f"posting line {index}: a negative magnitude is refused - "
                "direction is carried by the posting side"
            )
    debit_totals = sum_money(tuple(line.amount for line in lines if line.is_debit))
    credit_totals = sum_money(tuple(line.amount for line in lines if not line.is_debit))
    for currency in sorted(set(debit_totals) | set(credit_totals)):
        debit = debit_totals.get(currency, 0)
        credit = credit_totals.get(currency, 0)
        if debit != credit:
            raise JournalEntryUnbalancedError(
                f"currency {currency}: debit total {debit} does not equal credit total {credit}"
            )


# ---------------------------------------------------------------------------
# Journal entries
# ---------------------------------------------------------------------------


class EntryStatus(StrEnum):
    """Lifecycle of a `JournalEntry`: `draft` -> `posted` -> (`reversed`)
    (spec 8.2.3, canon 19f.4)."""

    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """The authoritative record of one monetary effect.

    The constructor runs `assert_balanced`, so an unbalanced entry cannot
    exist even as a draft (`ФИН-07`). `entry_sequence` is assigned at
    posting, per (scope, period), and never reused - not even by an entry
    replacing a reversed one; a draft carries `None`. The entry is its own
    history: `reverses_entry_id` and `corrects_entry_id` link it to what
    it acts on, and `correction_chain` refuses cycles (`ФИН-06`)."""

    entry_id: UUID
    scope: OrganizationalScopeRef
    period: ReportingPeriodRef
    lines: tuple[PostingLine, ...]
    reason: ReasonCoded
    status: EntryStatus = EntryStatus.DRAFT
    entry_sequence: int | None = None
    transaction_id: UUID | None = None
    reverses_entry_id: UUID | None = None
    corrects_entry_id: UUID | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        assert_balanced(self.lines)
        self.scope.assert_matches(self.period.scope)
        if self.status is EntryStatus.DRAFT and self.entry_sequence is not None:
            raise UnauthorizedStateTransitionError(
                "a draft journal entry carries no entry_sequence - it is assigned at posting"
            )
        if self.status is not EntryStatus.DRAFT:
            if self.entry_sequence is None:
                raise UnauthorizedStateTransitionError(
                    f"a {self.status!s} journal entry must carry an entry_sequence"
                )
            _require_positive(self.entry_sequence, "entry_sequence")
        if self.reverses_entry_id == self.entry_id:
            raise InvalidCorrectionTargetError("a journal entry cannot reverse itself")
        if self.corrects_entry_id == self.entry_id:
            raise InvalidCorrectionTargetError("a journal entry cannot correct itself")

    @property
    def is_mutable(self) -> bool:
        """Only a draft may be edited at all."""
        return self.status is EntryStatus.DRAFT


def assert_entry_mutable(entry: JournalEntry) -> None:
    """Raise unless `entry` may still be edited (`ФИН-05`).

    The refusal names immutability rather than a transition, because
    editing a posted entry is not a disallowed transition - it is an
    attempt to rewrite an authoritative record."""
    if not entry.is_mutable:
        raise ImmutableRecordModificationAttemptedError(
            f"a {entry.status!s} journal entry is content-immutable; "
            "correct or reverse it with a new entry instead"
        )


def amend_draft(
    entry: JournalEntry,
    *,
    lines: tuple[PostingLine, ...] | None = None,
    reason: ReasonCoded | None = None,
    evidence: tuple[EvidenceReference, ...] | None = None,
    transaction_id: UUID | None = None,
) -> JournalEntry:
    """Edit a draft entry, returning a new instance.

    This is the *only* edit path in the module and it refuses anything
    that is not a draft, so "editing any field of a posted entry" raises
    `ImmutableRecordModificationAttemptedError` by construction rather
    than by a per-field check (`ФИН-05`)."""
    assert_entry_mutable(entry)
    return replace(
        entry,
        lines=entry.lines if lines is None else lines,
        reason=entry.reason if reason is None else reason,
        evidence=entry.evidence if evidence is None else evidence,
        transaction_id=entry.transaction_id if transaction_id is None else transaction_id,
    )


def post(entry: JournalEntry, sequence: int, *, period: AccountingPeriod) -> JournalEntry:
    """Post a draft entry into an open period, returning a new instance.

    `period` is required and keyword-only on purpose: canon 19f.5 says the
    closed-period refusal must happen *inside the posting command*, so an
    overload that posted without a period would be the bypass `ФИН-10`
    forbids. The order of checks is fixed - draft status first (posting a
    posted entry is an immutability violation, not a transition error,
    `ФИН-05`), then scope (`ФИН-03`, `ФИН-04`), then the period lock, then
    balance re-asserted because the constructor guarantee is about the
    object and this one is about the act (`ФИН-07`)."""
    if entry.status is not EntryStatus.DRAFT:
        raise ImmutableRecordModificationAttemptedError(
            f"a {entry.status!s} journal entry cannot be posted again"
        )
    entry.scope.assert_matches(period.scope)
    if entry.period.period_id != period.period_id:
        raise AccountingPeriodUndeterminedError(
            "the entry's reporting period does not match the accounting period presented"
        )
    period.assert_open_for_posting()
    assert_balanced(entry.lines)
    _require_positive(sequence, "entry_sequence")
    return replace(entry, status=EntryStatus.POSTED, entry_sequence=sequence)


def assert_correction_target(entry: JournalEntry | None) -> JournalEntry:
    """Raise unless `entry` is a legitimate reversal or correction target,
    and return it narrowed (`ФИН-06`).

    `None` models the unknown target: a caller that could not resolve the
    original gets the same refusal as one that named a draft, because
    neither should be disclosed differently (`ФИН-03`)."""
    if entry is None:
        raise InvalidCorrectionTargetError(
            "the correction or reversal target does not exist in this scope"
        )
    if entry.status is EntryStatus.DRAFT:
        raise InvalidCorrectionTargetError(
            "a draft journal entry has no monetary effect to correct or reverse"
        )
    if entry.status is EntryStatus.REVERSED:
        raise InvalidCorrectionTargetError(
            "this journal entry has already been reversed; a further act is an ordinary new entry"
        )
    return entry


def reverse(
    entry: JournalEntry | None,
    *,
    entry_id: UUID,
    reason: ReasonCoded,
    evidence: tuple[EvidenceReference, ...] = (),
    transaction_id: UUID | None = None,
) -> tuple[JournalEntry, JournalEntry]:
    """Reverse a posted entry.

    Returns `(original_marked_reversed, reversal_entry)` - both halves of
    one act, so a caller cannot record the reversal while leaving the
    original still reversible. The reversal is a NEW draft entry with
    equal and opposite lines (each side flipped, each amount unchanged),
    `reverses_entry_id` set and its own reason code; it is posted through
    the ordinary `post` command and gets its own never-reused
    `entry_sequence` (`ФИН-06`). Reversing an already-reversed entry, a
    draft or an unresolved target raises `InvalidCorrectionTargetError`.
    Re-booking the corrected effect is an ordinary new entry."""
    target = assert_correction_target(entry)
    reversal = JournalEntry(
        entry_id=entry_id,
        scope=target.scope,
        period=target.period,
        lines=tuple(line.opposite() for line in target.lines),
        reason=reason,
        status=EntryStatus.DRAFT,
        transaction_id=transaction_id,
        reverses_entry_id=target.entry_id,
        evidence=evidence,
    )
    return replace(target, status=EntryStatus.REVERSED), reversal


def correct(
    entry: JournalEntry | None,
    replacement_lines: tuple[PostingLine, ...],
    *,
    entry_id: UUID,
    reason: ReasonCoded,
    period: ReportingPeriodRef | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
    transaction_id: UUID | None = None,
) -> JournalEntry:
    """Correct a posted entry with a NEW entry linked by
    `corrects_entry_id`.

    The original is left `posted` and untouched. A correction is not a
    reversal: it states that a further, differently-shaped booking belongs
    with the original, whose own effect stands until separately reversed -
    both links exist so the two acts stay distinguishable in the chain
    (`ФИН-06`). `replacement_lines` is balanced in its own right by the
    `JournalEntry` constructor, not against the original (`ФИН-07`), and
    `period` lets the correction be booked into a later reporting period
    when the original's has closed."""
    target = assert_correction_target(entry)
    target_period = target.period if period is None else period
    target.scope.assert_matches(target_period.scope)
    return JournalEntry(
        entry_id=entry_id,
        scope=target.scope,
        period=target_period,
        lines=replacement_lines,
        reason=reason,
        status=EntryStatus.DRAFT,
        transaction_id=transaction_id,
        corrects_entry_id=target.entry_id,
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# The transaction register
# ---------------------------------------------------------------------------


class TransactionStatus(StrEnum):
    """Lifecycle of a `FinancialTransaction` (spec 8.2.4, canon 19f.6)."""

    RECORDED = "recorded"
    CLASSIFIED = "classified"
    POSTED = "posted"
    CORRECTED = "corrected"
    REVERSED = "reversed"


_ALLOWED_TRANSACTION_TRANSITIONS: frozenset[tuple[TransactionStatus, TransactionStatus]] = (
    frozenset(
        {
            (TransactionStatus.RECORDED, TransactionStatus.CLASSIFIED),
            (TransactionStatus.CLASSIFIED, TransactionStatus.CLASSIFIED),
            (TransactionStatus.CLASSIFIED, TransactionStatus.POSTED),
            (TransactionStatus.POSTED, TransactionStatus.CORRECTED),
            (TransactionStatus.POSTED, TransactionStatus.REVERSED),
            (TransactionStatus.CORRECTED, TransactionStatus.REVERSED),
        }
    )
)

#: Statuses asserting a completed monetary effect, which therefore require
#: a posted `JournalEntry` to point at. A transaction claiming one of
#: these without an entry is the incomplete state canon 19f.6 says must
#: fail closed rather than be silently accepted.
_ENTRY_BEARING_TRANSACTION_STATUSES: frozenset[TransactionStatus] = frozenset(
    {TransactionStatus.POSTED, TransactionStatus.CORRECTED, TransactionStatus.REVERSED}
)


@dataclass(frozen=True, slots=True)
class FinancialTransaction:
    """The authoritative record of a business fact and its provenance.

    Not a cache of the register and not cached by it (ADR-049, canon
    19f.6): it owns *what happened* - the dates, the origin, the policy
    version that classified it, the evidence cited, the purpose-scoped
    handle it touched and the posted entry realising its money.

    Constructor invariants: `IMPORTED` provenance without an
    `import_batch_reference` is refused, since an imported fact whose
    batch cannot be named cannot be audited (`ФИН-38`); a status
    asserting monetary effect without a `journal_entry_id` is the
    incomplete state canon 19f.6 fails closed on; a status at or beyond
    `classified` without a bound policy version is refused, because
    classification is never inferred from the amount and never resolved at
    read time (`ФИН-23`); a party is only ever an opaque handle reference
    (`ФИН-01`). `transaction_date`, `provenance` and the import-batch
    reference are frozen after `recorded` (`ФИН-40`), and `version`
    carries optimistic concurrency so two concurrent classifications
    cannot both land."""

    transaction_id: UUID
    scope: OrganizationalScopeRef
    provenance: Provenance
    transaction_date: date
    posting_date: date
    recorded_at: datetime
    reporting_period: ReportingPeriodRef
    value_date: date | None = None
    classification_code: str = ""
    classification_policy: PolicyBinding | None = None
    party_handle_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    status: TransactionStatus = TransactionStatus.RECORDED
    journal_entry_id: UUID | None = None
    internal_transfer_reference: str | None = None
    corrects_transaction_id: UUID | None = None
    reverses_transaction_id: UUID | None = None
    version: int = 1

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, context="FinancialTransaction.recorded_at")
        _require_positive(self.version, "version")
        self.scope.assert_matches(self.reporting_period.scope)
        if (
            self.provenance.kind is ProvenanceKind.IMPORTED
            and not (self.provenance.import_batch_reference or "").strip()
        ):
            raise ImportProvenanceMissingError(
                "an imported transaction must name the import batch it arrived in"
            )
        if self.party_handle_reference is not None:
            _require_party_handle_reference(self.party_handle_reference, "party_handle_reference")
        if self.status is not TransactionStatus.RECORDED:
            if not self.classification_code.strip():
                raise PolicyMissingError(
                    f"a {self.status!s} transaction must carry a classification code"
                )
            if self.classification_policy is None:
                raise PolicyMissingError(
                    f"a {self.status!s} transaction must bind the policy version that classified it"
                )
        if self.status in _ENTRY_BEARING_TRANSACTION_STATUSES and self.journal_entry_id is None:
            raise UnauthorizedStateTransitionError(
                f"a {self.status!s} transaction without a balanced, posted journal entry is "
                "an incomplete state and is refused"
            )
        if self.corrects_transaction_id == self.transaction_id:
            raise InvalidCorrectionTargetError("a transaction cannot correct itself")
        if self.reverses_transaction_id == self.transaction_id:
            raise InvalidCorrectionTargetError("a transaction cannot reverse itself")

    def _check_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise OptimisticConcurrencyConflictError(
                f"expected transaction version {expected_version}, found {self.version}"
            )

    def _transition(
        self,
        target: TransactionStatus,
        *,
        classification_code: str | None = None,
        classification_policy: PolicyBinding | None = None,
        journal_entry_id: UUID | None = None,
    ) -> FinancialTransaction:
        """Apply one enumerated transition and re-assert what is frozen,
        so `assert_provenance_unchanged` cannot be forgotten on a future
        transition (`ФИН-40`)."""
        if (self.status, target) not in _ALLOWED_TRANSACTION_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.status!s} transaction cannot transition to {target!s}"
            )
        policy = (
            self.classification_policy if classification_policy is None else classification_policy
        )
        updated = replace(
            self,
            status=target,
            version=self.version + 1,
            classification_code=(
                self.classification_code if classification_code is None else classification_code
            ),
            classification_policy=policy,
            journal_entry_id=(
                self.journal_entry_id if journal_entry_id is None else journal_entry_id
            ),
        )
        assert_provenance_unchanged(self, updated)
        return updated

    def classify(
        self, *, classification_code: str, policy: PolicyBinding, expected_version: int
    ) -> FinancialTransaction:
        """Bind a classification and the exact policy version that
        produced it.

        Reclassification is a permitted, append-only act; what is refused
        is a classification with no bound policy version, since a decision
        resolving its policy at read time can be silently rewritten by a
        later policy change (`ФИН-23`). Whether a reclassification drops a
        disclosure, review, aggregation or reporting obligation is a
        policy question the application layer answers with
        `ReclassificationBypassDeniedError` (`ФИН-13`)."""
        _require_text(classification_code, "classification_code")
        self._check_version(expected_version)
        return self._transition(
            TransactionStatus.CLASSIFIED,
            classification_code=classification_code,
            classification_policy=policy,
        )

    def mark_posted(self, *, journal_entry_id: UUID, expected_version: int) -> FinancialTransaction:
        """Bind the balanced, posted `JournalEntry` realising this
        transaction's monetary effect (`ФИН-07`, canon 19f.6)."""
        self._check_version(expected_version)
        return self._transition(TransactionStatus.POSTED, journal_entry_id=journal_entry_id)

    def mark_corrected(self, *, expected_version: int) -> FinancialTransaction:
        """Record that a correcting transaction now exists for this one.
        The original stays authoritative for what it recorded (`ФИН-06`)."""
        self._check_version(expected_version)
        return self._transition(TransactionStatus.CORRECTED)

    def mark_reversed(self, *, expected_version: int) -> FinancialTransaction:
        """Record that this transaction has been reversed. Terminal: a
        reversed transaction is never reversed twice (`ФИН-06`)."""
        self._check_version(expected_version)
        return self._transition(TransactionStatus.REVERSED)


def assert_provenance_unchanged(before: FinancialTransaction, after: FinancialTransaction) -> None:
    """Raise if a transition altered anything frozen after `recorded`.

    Transaction date, provenance and import-batch reference are the audit
    trail's anchor: once the fact is recorded, changing where it came from
    would rewrite that anchor while leaving every downstream reference
    intact (`ФИН-40`, canon 19f.6)."""
    if before.transaction_date != after.transaction_date:
        raise ImmutableRecordModificationAttemptedError(
            "transaction_date is frozen once the transaction is recorded"
        )
    if before.provenance != after.provenance:
        raise ImmutableRecordModificationAttemptedError(
            "provenance is frozen once the transaction is recorded"
        )
    if before.provenance.import_batch_reference != after.provenance.import_batch_reference:
        raise ImmutableRecordModificationAttemptedError(
            "import_batch_reference is frozen once the transaction is recorded"
        )


# ---------------------------------------------------------------------------
# Correction and reversal chains
# ---------------------------------------------------------------------------

#: What `correction_chain` accepts. Entries and transactions share the
#: shape - an identity plus at most one backward link - but not a base
#: class, because they are two different authoritative layers and a common
#: ancestor would invite code treating one as a substitute for the other
#: (ADR-049).
CorrectableRecord = JournalEntry | FinancialTransaction


def _record_identity(record: CorrectableRecord) -> UUID:
    if isinstance(record, JournalEntry):
        return record.entry_id
    return record.transaction_id


def _record_predecessor(record: CorrectableRecord) -> UUID | None:
    """The single record this one acts on, if any. A record links backward
    through at most one pointer; if both are set the chain is ambiguous
    and is refused, because "which original does this correct" would have
    two answers (`ФИН-06`)."""
    if isinstance(record, JournalEntry):
        corrects, reverses = record.corrects_entry_id, record.reverses_entry_id
    else:
        corrects, reverses = record.corrects_transaction_id, record.reverses_transaction_id
    if corrects is not None and reverses is not None:
        raise InvalidCorrectionTargetError(
            "a record may correct or reverse one predecessor, never both"
        )
    return corrects if corrects is not None else reverses


def _assert_chain_acyclic(predecessors: dict[UUID, UUID | None]) -> None:
    """Walk every backward link to its origin, refusing any revisit.

    Kept separate from `correction_chain` so the cycle rule is testable on
    its own and the walk is provably bounded: `settled` guarantees each
    node is resolved at most once."""
    settled: set[UUID] = set()
    for start in predecessors:
        if start in settled:
            continue
        path: list[UUID] = []
        seen: set[UUID] = set()
        cursor: UUID | None = start
        while cursor is not None and cursor not in settled:
            if cursor in seen:
                raise InvalidCorrectionTargetError(
                    f"correction chain contains a cycle through record {cursor}"
                )
            seen.add(cursor)
            path.append(cursor)
            cursor = predecessors.get(cursor)
        settled.update(path)


def correction_chain(
    entries_or_transactions: Sequence[CorrectableRecord],
) -> tuple[CorrectableRecord, ...]:
    """Order a set of linked records from the original through its
    corrections and reversals (`ФИН-06`, canon 19f.4).

    Pure and total over its input: only the identity and backward link on
    each record are read, and a predecessor id absent from the input is
    "outside this chain" - which makes the function usable on a
    scope-filtered slice without leaking records in another scope
    (`ФИН-03`). Refusals, all `InvalidCorrectionTargetError`: a cycle
    (chains are append-only and cycle-free), a duplicate identity, more
    than one origin, and a branch - canon 19f.4 describes a chain, not a
    tree, and silently picking one branch would hide the other. An empty
    input returns an empty tuple."""
    records = tuple(entries_or_transactions)
    if not records:
        return ()

    by_id: dict[UUID, CorrectableRecord] = {}
    for record in records:
        identity = _record_identity(record)
        if identity in by_id:
            raise InvalidCorrectionTargetError(
                f"record {identity} appears twice in the presented chain"
            )
        by_id[identity] = record

    predecessors: dict[UUID, UUID | None] = {}
    successors: dict[UUID, UUID] = {}
    roots: list[UUID] = []
    for identity, record in by_id.items():
        predecessor = _record_predecessor(record)
        if predecessor is None or predecessor not in by_id:
            predecessors[identity] = None
            roots.append(identity)
            continue
        predecessors[identity] = predecessor
        if predecessor in successors:
            raise InvalidCorrectionTargetError(
                f"record {predecessor} is corrected or reversed by more than one record"
            )
        successors[predecessor] = identity

    _assert_chain_acyclic(predecessors)

    if len(roots) != 1:
        raise InvalidCorrectionTargetError(
            f"a correction chain must have exactly one origin, found {len(roots)}"
        )

    ordered: list[CorrectableRecord] = []
    cursor: UUID | None = roots[0]
    while cursor is not None:
        ordered.append(by_id[cursor])
        cursor = successors.get(cursor)
    if len(ordered) != len(records):
        raise InvalidCorrectionTargetError(
            "the presented records do not form a single connected correction chain"
        )
    return tuple(ordered)
