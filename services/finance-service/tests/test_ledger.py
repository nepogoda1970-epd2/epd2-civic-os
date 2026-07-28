"""Tests for `epd2_finance_service.ledger` - the double-entry register,
accounting periods, correction chains and the transaction register.

Two tests here reach into `application`: canon 19f.5 requires the
closed-period refusal to happen *inside the posting command* and the
posting sequence to be gap-free, and neither claim can be proved against
the pure aggregate alone.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_finance_service import application as app
from epd2_finance_service.authorization import FinanceRole
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    ReportingPeriodRef,
    RequestContext,
    RetentionBinding,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodClosedError,
    AccountingPeriodUndeterminedError,
    ImmutableRecordModificationAttemptedError,
    ImportProvenanceMissingError,
    InvalidCorrectionTargetError,
    JournalEntryUnbalancedError,
    MonetaryAmountInvalidError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeMismatchError,
    PeriodReopeningNotAuthorizedError,
    PolicyMissingError,
    UnauthorizedStateTransitionError,
)
from epd2_finance_service.ledger import (
    AccountingPeriod,
    AccountStatus,
    EntryStatus,
    FinanceAccount,
    FinancialTransaction,
    JournalEntry,
    PeriodStatus,
    PostingLine,
    PostingSide,
    TransactionStatus,
    amend_draft,
    assert_balanced,
    assert_entry_mutable,
    assert_provenance_unchanged,
    assert_reopening_dual_control,
    correct,
    correction_chain,
    post,
    resolve_period_timezone,
    reverse,
)
from epd2_finance_service.storage import (
    InMemoryAccountingPeriodStore,
    InMemoryCommandIdempotencyStore,
    InMemoryEventSink,
    InMemoryFinanceAccountStore,
    InMemoryJournalEntryStore,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_OPENS = datetime(2026, 1, 1, tzinfo=UTC)
_CLOSES = datetime(2027, 1, 1, tzinfo=UTC)
_BERLIN = "Europe/Berlin"
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _authority(role_code: str, *, scope: OrganizationalScopeRef, actor: str) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(), role_code=role_code, scope=scope, actor_reference=actor
    )


def _period(
    scope: OrganizationalScopeRef, *, status: PeriodStatus = PeriodStatus.OPEN
) -> AccountingPeriod:
    return AccountingPeriod(
        period_id=uuid4(),
        label="2026",
        scope=scope,
        timezone_name=_BERLIN,
        opens_at=_OPENS,
        closes_at=_CLOSES,
        status=status,
    )


def _account(scope: OrganizationalScopeRef, code: str = "1000") -> FinanceAccount:
    return FinanceAccount(
        account_id=uuid4(),
        code=code,
        classification_code="asset",
        scope=scope,
        retention=_RETENTION,
    )


def _lines(
    debit_account: UUID, credit_account: UUID, debit: int, credit: int | None = None
) -> tuple[PostingLine, ...]:
    return (
        PostingLine(account_id=debit_account, side=PostingSide.DEBIT, amount=Money(debit, "EUR")),
        PostingLine(
            account_id=credit_account,
            side=PostingSide.CREDIT,
            amount=Money(debit if credit is None else credit, "EUR"),
        ),
    )


def _entry(
    scope: OrganizationalScopeRef,
    period: AccountingPeriod,
    *,
    debit: int = 10_000,
    credit: int | None = None,
    entry_id: UUID | None = None,
) -> JournalEntry:
    return JournalEntry(
        entry_id=uuid4() if entry_id is None else entry_id,
        scope=scope,
        period=period.as_reference(),
        lines=_lines(uuid4(), uuid4(), debit, credit),
        reason=_REASON,
    )


def _transaction(
    scope: OrganizationalScopeRef,
    period: AccountingPeriod,
    *,
    provenance: Provenance | None = None,
    status: TransactionStatus = TransactionStatus.RECORDED,
    classification_code: str = "",
    classification_policy: PolicyBinding | None = None,
    journal_entry_id: UUID | None = None,
) -> FinancialTransaction:
    return FinancialTransaction(
        transaction_id=uuid4(),
        scope=scope,
        provenance=(
            Provenance(
                kind=ProvenanceKind.MANUAL_ENTRY,
                source_system_reference="treasury-desk",
                recorded_by_authority="treasury",
            )
            if provenance is None
            else provenance
        ),
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        recorded_at=_NOW,
        reporting_period=period.as_reference(),
        status=status,
        classification_code=classification_code,
        classification_policy=classification_policy,
        journal_entry_id=journal_entry_id,
    )


# =============================================================================
# The application wiring the two command-level tests need
# =============================================================================


class _Port:
    """Test double for `authorization.AuthorizationPort`."""

    def __init__(self, held: dict[str, frozenset[FinanceRole]]) -> None:
        self.active: set[UUID] = set()
        self.held = held

    def resolve_active_authority(
        self, authority: AuthorityReference, scope: OrganizationalScopeRef
    ) -> bool:
        return (
            authority.authority_id in self.active
            and authority.scope.organization_id == scope.organization_id
        )

    def held_roles(
        self, actor_reference: str, scope: OrganizationalScopeRef
    ) -> frozenset[FinanceRole]:
        return self.held.get(actor_reference, frozenset())


@dataclass(slots=True)
class _World:
    """One wired finance-service instance and the authorities it needs."""

    entries: InMemoryJournalEntryStore
    periods: InMemoryAccountingPeriodStore
    accounts: InMemoryFinanceAccountStore
    idempotency: InMemoryCommandIdempotencyStore
    audit: InMemoryAuditEventStore
    sink: InMemoryEventSink
    clock: FixedClock
    port: _Port
    scope: OrganizationalScopeRef
    admin: AuthorityReference
    orgadmin: AuthorityReference


def _world() -> _World:
    scope = _scope()
    admin = _authority("finance_administrator", scope=scope, actor="actor-admin")
    orgadmin = _authority("organizational_administrator", scope=scope, actor="actor-orgadmin")
    port = _Port(
        {
            "actor-admin": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
            "actor-orgadmin": frozenset({FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}),
        }
    )
    port.active.update({admin.authority_id, orgadmin.authority_id})
    return _World(
        entries=InMemoryJournalEntryStore(),
        periods=InMemoryAccountingPeriodStore(),
        accounts=InMemoryFinanceAccountStore(),
        idempotency=InMemoryCommandIdempotencyStore(),
        audit=InMemoryAuditEventStore(),
        sink=InMemoryEventSink(),
        clock=FixedClock(_NOW),
        port=port,
        scope=scope,
        admin=admin,
        orgadmin=orgadmin,
    )


def _context(*authorities: AuthorityReference, scope: OrganizationalScopeRef) -> RequestContext:
    return RequestContext(
        scope=scope,
        authorities=authorities,
        conflict=ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board"),
        event_id=uuid4(),
        correlation_id="ledger-workflow",
    )


def _opened_period(world: _World) -> UUID:
    period_id = uuid4()
    app.open_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        label="2026",
        timezone_name=_BERLIN,
        opens_at=_OPENS,
        closes_at=_CLOSES,
    )
    return period_id


def _active_accounts(world: _World) -> tuple[UUID, UUID]:
    identifiers: list[UUID] = []
    for code, classification in (("1000", "asset"), ("4000", "income")):
        account_id = uuid4()
        app.create_finance_account(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world.admin, scope=world.scope),
            port=world.port,
            clock=world.clock,
            account_id=account_id,
            code=code,
            classification_code=classification,
            retention=_RETENTION,
        )
        app.change_finance_account_status(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world.admin, scope=world.scope),
            port=world.port,
            clock=world.clock,
            account_id=account_id,
            target_status=AccountStatus.ACTIVE,
            reason=_REASON,
        )
        identifiers.append(account_id)
    return identifiers[0], identifiers[1]


def _drafted(world: _World, period_id: UUID, cash: UUID, income: UUID, amount: int) -> UUID:
    entry_id = uuid4()
    app.draft_journal_entry(
        world.entries,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
        period_id=period_id,
        lines=_lines(cash, income, amount),
        reason=_REASON,
    )
    return entry_id


def _posted(world: _World, entry_id: UUID) -> JournalEntry:
    return app.post_journal_entry(
        world.entries,
        world.periods,
        world.accounts,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
    ).entry


# =============================================================================
# Balance (`ФИН-07`, `ФИН-09`)
# =============================================================================


def test_a_posted_entry_balances_per_currency() -> None:
    scope = _scope()
    period = _period(scope)
    entry = _entry(scope, period)
    posted = post(entry, 1, period=period)
    debits = sum(line.amount.minor_units for line in posted.lines if line.is_debit)
    credits = sum(line.amount.minor_units for line in posted.lines if not line.is_debit)
    assert posted.status is EntryStatus.POSTED
    assert debits == credits == 10_000
    assert {line.amount.currency for line in posted.lines} == {"EUR"}


def test_an_unbalanced_entry_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    with pytest.raises(JournalEntryUnbalancedError) as excinfo:
        _entry(scope, period, debit=10_000, credit=5_000)
    assert excinfo.value.reason_code == "FINANCE_JOURNAL_ENTRY_UNBALANCED"


def test_an_entry_with_no_posting_line_refuses_rather_than_balancing_vacuously() -> None:
    with pytest.raises(JournalEntryUnbalancedError):
        assert_balanced(())


def test_a_negative_magnitude_refuses_because_direction_belongs_to_the_posting_side() -> None:
    lines = (
        PostingLine(account_id=uuid4(), side=PostingSide.DEBIT, amount=Money(-500, "EUR")),
        PostingLine(account_id=uuid4(), side=PostingSide.CREDIT, amount=Money(-500, "EUR")),
    )
    with pytest.raises(MonetaryAmountInvalidError):
        assert_balanced(lines)


def test_a_zero_value_posting_line_refuses() -> None:
    lines = (
        PostingLine(account_id=uuid4(), side=PostingSide.DEBIT, amount=Money(0, "EUR")),
        PostingLine(account_id=uuid4(), side=PostingSide.CREDIT, amount=Money(0, "EUR")),
    )
    with pytest.raises(MonetaryAmountInvalidError):
        assert_balanced(lines)


# =============================================================================
# Immutability (`ФИН-05`)
# =============================================================================


def test_a_posted_journal_entry_is_content_immutable() -> None:
    scope = _scope()
    period = _period(scope)
    posted = post(_entry(scope, period), 1, period=period)
    with pytest.raises(ImmutableRecordModificationAttemptedError) as excinfo:
        amend_draft(posted, lines=_lines(uuid4(), uuid4(), 20_000))
    assert excinfo.value.reason_code == "FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED"
    assert posted.status is EntryStatus.POSTED
    assert posted.lines[0].amount == Money(10_000, "EUR")


def test_a_draft_entry_is_the_only_editable_entry() -> None:
    scope = _scope()
    period = _period(scope)
    draft = _entry(scope, period)
    assert_entry_mutable(draft)
    amended = amend_draft(draft, lines=_lines(uuid4(), uuid4(), 20_000))
    assert amended.lines[0].amount == Money(20_000, "EUR")
    assert draft.lines[0].amount == Money(10_000, "EUR")


def test_a_posted_entry_cannot_be_posted_again() -> None:
    scope = _scope()
    period = _period(scope)
    posted = post(_entry(scope, period), 1, period=period)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        post(posted, 2, period=period)


def test_a_draft_carries_no_entry_sequence_and_a_posted_entry_must_carry_one() -> None:
    scope = _scope()
    period = _period(scope)
    with pytest.raises(UnauthorizedStateTransitionError):
        JournalEntry(
            entry_id=uuid4(),
            scope=scope,
            period=period.as_reference(),
            lines=_lines(uuid4(), uuid4(), 1_000),
            reason=_REASON,
            entry_sequence=7,
        )
    with pytest.raises(UnauthorizedStateTransitionError):
        JournalEntry(
            entry_id=uuid4(),
            scope=scope,
            period=period.as_reference(),
            lines=_lines(uuid4(), uuid4(), 1_000),
            reason=_REASON,
            status=EntryStatus.POSTED,
        )


def test_an_account_classification_freezes_once_the_account_has_carried_a_posting() -> None:
    scope = _scope()
    admin = _authority("finance_administrator", scope=scope, actor="actor-admin")
    account = _account(scope).activate(at=_NOW, by_authority=admin, reason=_REASON)
    posted_against = account.mark_first_posting()
    assert posted_against.has_postings is True
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        posted_against.reclassify(
            classification_code="income",
            policy=_POLICY,
            at=_NOW,
            by_authority=admin,
            reason=_REASON,
        )
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        posted_against.recode(code="9999", at=_NOW, by_authority=admin, reason=_REASON)


def test_a_closed_account_is_terminal() -> None:
    scope = _scope()
    admin = _authority("finance_administrator", scope=scope, actor="actor-admin")
    closed = (
        _account(scope)
        .activate(at=_NOW, by_authority=admin, reason=_REASON)
        .close(at=_NOW, by_authority=admin, reason=_REASON)
    )
    assert closed.status is AccountStatus.CLOSED
    with pytest.raises(UnauthorizedStateTransitionError):
        closed.activate(at=_NOW, by_authority=admin, reason=_REASON)


# =============================================================================
# Periods (`ФИН-10`, `ФИН-11`, `ФИН-39`)
# =============================================================================


def test_the_pure_aggregate_refuses_a_posting_into_a_closed_period() -> None:
    scope = _scope()
    period = _period(scope, status=PeriodStatus.CLOSED)
    with pytest.raises(AccountingPeriodClosedError) as excinfo:
        post(_entry(scope, period), 1, period=period)
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_CLOSED"


def test_a_closing_period_denies_a_posting_as_firmly_as_a_closed_one() -> None:
    scope = _scope()
    period = _period(scope, status=PeriodStatus.CLOSING)
    with pytest.raises(AccountingPeriodClosedError):
        period.assert_open_for_posting()


def test_posting_into_a_closed_period_is_refused_by_the_command() -> None:
    world = _world()
    period_id = _opened_period(world)
    cash, income = _active_accounts(world)
    entry_id = _drafted(world, period_id, cash, income, 2_500)
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    with pytest.raises(AccountingPeriodClosedError) as excinfo:
        _posted(world, entry_id)
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_CLOSED"
    stored = world.entries.get(entry_id)
    assert stored is not None
    assert stored.status is EntryStatus.DRAFT


def test_the_posting_sequence_is_gap_free_across_a_close_and_a_reopening() -> None:
    world = _world()
    period_id = _opened_period(world)
    cash, income = _active_accounts(world)
    first = _drafted(world, period_id, cash, income, 10_000)
    second = _drafted(world, period_id, cash, income, 2_500)
    third = _drafted(world, period_id, cash, income, 500)
    assert _posted(world, first).entry_sequence == 1
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    with pytest.raises(AccountingPeriodClosedError):
        _posted(world, second)
    reopening = app.request_period_reopening(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reopening_record_id=uuid4(),
        approving_authority=world.orgadmin,
        reason=_REASON,
        policy=_POLICY,
    ).reopening_record
    app.reopen_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.orgadmin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reopening_record=reopening,
    )
    assert _posted(world, second).entry_sequence == 2
    assert _posted(world, third).entry_sequence == 3
    sequences = sorted(
        entry.entry_sequence
        for entry in world.entries.list_for_period(scope=world.scope, period_id=period_id)
        if entry.entry_sequence is not None
    )
    assert sequences == list(range(1, len(sequences) + 1))


def test_reopening_without_dual_control_refuses() -> None:
    world = _world()
    period_id = _opened_period(world)
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world.admin, scope=world.scope),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    with pytest.raises(PeriodReopeningNotAuthorizedError) as excinfo:
        app.request_period_reopening(
            world.periods,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world.admin, scope=world.scope),
            port=world.port,
            clock=world.clock,
            period_id=period_id,
            reopening_record_id=uuid4(),
            approving_authority=world.admin,
            reason=_REASON,
            policy=_POLICY,
        )
    assert excinfo.value.reason_code == "FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED"


def test_reopening_refuses_when_one_actor_holds_both_sides_of_the_dual_control() -> None:
    scope = _scope()
    requester = _authority("finance_administrator", scope=scope, actor="actor-same")
    approver = _authority("organizational_administrator", scope=scope, actor="actor-same")
    with pytest.raises(PeriodReopeningNotAuthorizedError):
        assert_reopening_dual_control(requester, approver)


def test_a_reopening_record_snapshots_the_closed_state_it_reopens() -> None:
    scope = _scope()
    requester = _authority("finance_administrator", scope=scope, actor="actor-admin")
    approver = _authority("organizational_administrator", scope=scope, actor="actor-orgadmin")
    closed = _period(scope, status=PeriodStatus.CLOSED)
    record = closed.request_reopening(
        record_id=uuid4(),
        requested_by=requester,
        approved_by=approver,
        reason=_REASON,
        policy=_POLICY,
        requested_at=_NOW,
        approved_at=_NOW,
    )
    assert record.closed_state_digest == closed.state_digest()
    assert record.policy is _POLICY
    reopened = closed.reopen(record, at=_NOW)
    assert reopened.status is PeriodStatus.REOPENED
    assert reopened.reopening_records == (record,)


def test_a_stale_reopening_record_cannot_be_replayed_against_a_moved_on_period() -> None:
    scope = _scope()
    requester = _authority("finance_administrator", scope=scope, actor="actor-admin")
    approver = _authority("organizational_administrator", scope=scope, actor="actor-orgadmin")
    closed = _period(scope, status=PeriodStatus.CLOSED)
    record = closed.request_reopening(
        record_id=uuid4(),
        requested_by=requester,
        approved_by=approver,
        reason=_REASON,
        policy=_POLICY,
        requested_at=_NOW,
        approved_at=_NOW,
    )
    moved_on = replace(closed, label="2026-restated")
    with pytest.raises(PeriodReopeningNotAuthorizedError):
        moved_on.reopen(record, at=_NOW)


def test_only_a_closed_period_can_be_reopened() -> None:
    scope = _scope()
    requester = _authority("finance_administrator", scope=scope, actor="actor-admin")
    approver = _authority("organizational_administrator", scope=scope, actor="actor-orgadmin")
    with pytest.raises(UnauthorizedStateTransitionError):
        _period(scope).request_reopening(
            record_id=uuid4(),
            requested_by=requester,
            approved_by=approver,
            reason=_REASON,
            policy=_POLICY,
            requested_at=_NOW,
            approved_at=_NOW,
        )


def test_a_period_requires_an_explicit_named_timezone() -> None:
    assert resolve_period_timezone(_BERLIN) is not None
    with pytest.raises(AccountingPeriodUndeterminedError):
        resolve_period_timezone("  ")
    with pytest.raises(AccountingPeriodUndeterminedError):
        resolve_period_timezone("Mars/Olympus_Mons")


def test_a_period_refuses_naive_boundaries_and_a_non_increasing_window() -> None:
    scope = _scope()
    with pytest.raises(AccountingPeriodUndeterminedError):
        AccountingPeriod(
            period_id=uuid4(),
            label="2026",
            scope=scope,
            timezone_name=_BERLIN,
            opens_at=datetime(2026, 1, 1),
            closes_at=_CLOSES,
        )
    with pytest.raises(AccountingPeriodUndeterminedError):
        AccountingPeriod(
            period_id=uuid4(),
            label="2026",
            scope=scope,
            timezone_name=_BERLIN,
            opens_at=_CLOSES,
            closes_at=_OPENS,
        )


def test_posting_an_entry_against_another_period_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    other = _period(scope)
    with pytest.raises(AccountingPeriodUndeterminedError):
        post(_entry(scope, period), 1, period=other)


# =============================================================================
# Correction and reversal (`ФИН-06`)
# =============================================================================


def test_correction_by_reversal_produces_a_reversal_and_leaves_the_original_readable() -> None:
    scope = _scope()
    period = _period(scope)
    original = post(_entry(scope, period), 1, period=period)
    marked, reversal = reverse(original, entry_id=uuid4(), reason=_REASON)
    assert marked.status is EntryStatus.REVERSED
    assert marked.lines == original.lines
    assert marked.entry_sequence == 1
    assert reversal.status is EntryStatus.DRAFT
    assert reversal.reverses_entry_id == original.entry_id
    assert reversal.entry_sequence is None
    assert [line.side for line in reversal.lines] == [PostingSide.CREDIT, PostingSide.DEBIT]
    assert [line.amount for line in reversal.lines] == [line.amount for line in original.lines]


def test_a_reversal_gets_its_own_never_reused_sequence() -> None:
    scope = _scope()
    period = _period(scope)
    original = post(_entry(scope, period), 1, period=period)
    _, reversal = reverse(original, entry_id=uuid4(), reason=_REASON)
    posted_reversal = post(reversal, 2, period=period)
    assert posted_reversal.entry_sequence == 2


def test_a_correction_leaves_the_original_posted_and_links_the_new_entry() -> None:
    scope = _scope()
    period = _period(scope)
    original = post(_entry(scope, period), 1, period=period)
    correcting = correct(
        original, _lines(uuid4(), uuid4(), 12_000), entry_id=uuid4(), reason=_REASON
    )
    assert original.status is EntryStatus.POSTED
    assert correcting.corrects_entry_id == original.entry_id
    assert correcting.reverses_entry_id is None


def test_reversing_a_draft_or_an_already_reversed_entry_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    draft = _entry(scope, period)
    with pytest.raises(InvalidCorrectionTargetError) as excinfo:
        reverse(draft, entry_id=uuid4(), reason=_REASON)
    assert excinfo.value.reason_code == "FINANCE_CORRECTION_TARGET_INVALID"
    marked, _ = reverse(post(draft, 1, period=period), entry_id=uuid4(), reason=_REASON)
    with pytest.raises(InvalidCorrectionTargetError):
        reverse(marked, entry_id=uuid4(), reason=_REASON)


def test_an_unresolvable_correction_target_answers_the_same_refusal_as_a_draft() -> None:
    with pytest.raises(InvalidCorrectionTargetError):
        reverse(None, entry_id=uuid4(), reason=_REASON)


def test_an_entry_cannot_reverse_or_correct_itself() -> None:
    scope = _scope()
    period = _period(scope)
    entry_id = uuid4()
    with pytest.raises(InvalidCorrectionTargetError):
        JournalEntry(
            entry_id=entry_id,
            scope=scope,
            period=period.as_reference(),
            lines=_lines(uuid4(), uuid4(), 1_000),
            reason=_REASON,
            reverses_entry_id=entry_id,
        )
    with pytest.raises(InvalidCorrectionTargetError):
        JournalEntry(
            entry_id=entry_id,
            scope=scope,
            period=period.as_reference(),
            lines=_lines(uuid4(), uuid4(), 1_000),
            reason=_REASON,
            corrects_entry_id=entry_id,
        )


def test_a_correction_chain_orders_the_original_before_its_successors() -> None:
    scope = _scope()
    period = _period(scope)
    original = post(_entry(scope, period), 1, period=period)
    correcting = correct(
        original, _lines(uuid4(), uuid4(), 12_000), entry_id=uuid4(), reason=_REASON
    )
    chain = correction_chain((correcting, original))
    assert chain == (original, correcting)


def test_a_correction_chain_that_would_cycle_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    first_id, second_id = uuid4(), uuid4()
    first = JournalEntry(
        entry_id=first_id,
        scope=scope,
        period=period.as_reference(),
        lines=_lines(uuid4(), uuid4(), 1_000),
        reason=_REASON,
        status=EntryStatus.POSTED,
        entry_sequence=1,
        corrects_entry_id=second_id,
    )
    second = JournalEntry(
        entry_id=second_id,
        scope=scope,
        period=period.as_reference(),
        lines=_lines(uuid4(), uuid4(), 1_000),
        reason=_REASON,
        status=EntryStatus.POSTED,
        entry_sequence=2,
        corrects_entry_id=first_id,
    )
    with pytest.raises(InvalidCorrectionTargetError) as excinfo:
        correction_chain((first, second))
    assert excinfo.value.reason_code == "FINANCE_CORRECTION_TARGET_INVALID"


def test_a_record_that_both_corrects_and_reverses_a_predecessor_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    ambiguous = JournalEntry(
        entry_id=uuid4(),
        scope=scope,
        period=period.as_reference(),
        lines=_lines(uuid4(), uuid4(), 1_000),
        reason=_REASON,
        status=EntryStatus.POSTED,
        entry_sequence=1,
        corrects_entry_id=uuid4(),
        reverses_entry_id=uuid4(),
    )
    with pytest.raises(InvalidCorrectionTargetError):
        correction_chain((ambiguous,))


def test_a_branching_chain_refuses_rather_than_silently_picking_one_branch() -> None:
    scope = _scope()
    period = _period(scope)
    original = post(_entry(scope, period), 1, period=period)
    first = correct(original, _lines(uuid4(), uuid4(), 11_000), entry_id=uuid4(), reason=_REASON)
    second = correct(original, _lines(uuid4(), uuid4(), 12_000), entry_id=uuid4(), reason=_REASON)
    with pytest.raises(InvalidCorrectionTargetError):
        correction_chain((original, first, second))


def test_an_empty_chain_is_empty_rather_than_an_error() -> None:
    assert correction_chain(()) == ()


# =============================================================================
# The transaction register (`ФИН-23`, `ФИН-38`)
# =============================================================================


def test_an_imported_transaction_without_a_batch_reference_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    imported_without_batch = Provenance(
        kind=ProvenanceKind.IMPORTED,
        source_system_reference="bank-feed",
        recorded_by_authority="treasury",
    )
    with pytest.raises(ImportProvenanceMissingError) as excinfo:
        _transaction(scope, period, provenance=imported_without_batch)
    assert excinfo.value.reason_code == "FINANCE_IMPORT_PROVENANCE_MISSING"


def test_a_classified_transaction_binds_the_policy_version_that_classified_it() -> None:
    scope = _scope()
    period = _period(scope)
    recorded = _transaction(scope, period)
    classified = recorded.classify(
        classification_code="income.donation", policy=_POLICY, expected_version=1
    )
    assert classified.status is TransactionStatus.CLASSIFIED
    assert classified.classification_policy is _POLICY
    assert classified.version == 2
    with pytest.raises(PolicyMissingError) as excinfo:
        _transaction(
            scope,
            period,
            status=TransactionStatus.CLASSIFIED,
            classification_code="income.donation",
        )
    assert excinfo.value.reason_code == "FINANCE_POLICY_MISSING"


def test_a_stale_expected_version_refuses_a_reclassification() -> None:
    scope = _scope()
    period = _period(scope)
    recorded = _transaction(scope, period)
    with pytest.raises(OptimisticConcurrencyConflictError) as excinfo:
        recorded.classify(
            classification_code="income.donation", policy=_POLICY, expected_version=99
        )
    assert excinfo.value.reason_code == "OPTIMISTIC_CONCURRENCY_CONFLICT"


def test_a_status_asserting_monetary_effect_without_a_posted_entry_refuses() -> None:
    scope = _scope()
    period = _period(scope)
    with pytest.raises(UnauthorizedStateTransitionError):
        _transaction(
            scope,
            period,
            status=TransactionStatus.POSTED,
            classification_code="income.donation",
            classification_policy=_POLICY,
        )


def test_provenance_and_the_transaction_date_are_frozen_after_recording() -> None:
    scope = _scope()
    period = _period(scope)
    recorded = _transaction(scope, period)
    rewritten = replace(recorded, transaction_date=date(2026, 5, 1))
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        assert_provenance_unchanged(recorded, rewritten)


def test_a_reporting_period_reference_must_share_the_records_scope() -> None:
    with pytest.raises(OrganizationScopeMismatchError) as excinfo:
        JournalEntry(
            entry_id=uuid4(),
            scope=_scope(),
            period=ReportingPeriodRef(period_id=uuid4(), label="2026", scope=_scope()),
            lines=_lines(uuid4(), uuid4(), 1_000),
            reason=_REASON,
        )
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_MISMATCH"
