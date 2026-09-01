"""Tests for `epd2_finance_service.storage` - the storage ports, the
in-memory reference adapters, scope isolation and the append-only rules
storage itself enforces.

The first test in this module is the structural one: **no port and no
adapter anywhere in this package offers a delete-shaped method.** `ФИН-05`
makes a posted register entry immutable and `ФИН-22` puts a PACK-09 legal
hold above any wish to destroy, so a `delete` on a port would be
publishing an act the domain forbids.
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

import epd2_finance_service
from epd2_finance_service import (
    application,
    authorization,
    domain,
    events,
    ledger,
    projections,
    records,
    references,
    reporting,
    storage,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    FinancePartyHandle,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    ReportingPeriodRef,
    RetentionBinding,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    DuplicateImportError,
    FinanceRecordNotFoundError,
    GovernedRecordDeletionForbiddenError,
    ImmutableRecordModificationAttemptedError,
    ImportProvenanceMissingError,
    MonetaryAmountInvalidError,
)
from epd2_finance_service.ledger import (
    AccountingPeriod,
    EntryStatus,
    FinanceAccount,
    FinancialTransaction,
    JournalEntry,
    PostingLine,
    PostingSide,
    post,
    reverse,
)
from epd2_finance_service.records import (
    ContributionKind,
    ContributionReceipt,
    FinanceContribution,
)
from epd2_finance_service.reporting import (
    PublicationAuthorization,
    ReportingPerimeterDefinition,
    ReportSnapshot,
    freeze_perimeter,
)
from epd2_finance_service.storage import (
    ImportBatchRecord,
    ImportBatchStatus,
    InMemoryAccountingPeriodStore,
    InMemoryFinanceAccountStore,
    InMemoryFinanceContributionStore,
    InMemoryFinancePartyHandleStore,
    InMemoryFinancialTransactionStore,
    InMemoryImportBatchStore,
    InMemoryJournalEntryStore,
    InMemoryPerimeterSnapshotStore,
    InMemoryPublicationAuthorizationStore,
    InMemoryReportSnapshotStore,
    delete_finance_record,
    transaction_fingerprint,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)

#: Name fragments that would make a method a deletion. `ФИН-05`: a
#: governed finance record is corrected, reversed or superseded, never
#: removed, so none of these may name a port method or an adapter method.
DELETE_SHAPED_NAMES: tuple[str, ...] = (
    "delete",
    "remove",
    "drop",
    "purge",
    "destroy",
    "erase",
    "truncate",
    "expunge",
    "wipe",
    "forget",
)

#: Every module of the package, for the structural scans below.
PACKAGE_MODULES = (
    application,
    authorization,
    domain,
    events,
    ledger,
    projections,
    records,
    references,
    reporting,
    storage,
)


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _authority(scope: OrganizationalScopeRef, *, actor: str = "actor-admin") -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(),
        role_code="finance_administrator",
        scope=scope,
        actor_reference=actor,
    )


def _account(scope: OrganizationalScopeRef, code: str = "1000") -> FinanceAccount:
    return FinanceAccount(
        account_id=uuid4(),
        code=code,
        classification_code="asset",
        scope=scope,
        retention=_RETENTION,
    )


def _period(scope: OrganizationalScopeRef) -> AccountingPeriod:
    return AccountingPeriod(
        period_id=uuid4(),
        label="2026",
        scope=scope,
        timezone_name="Europe/Berlin",
        opens_at=datetime(2026, 1, 1, tzinfo=UTC),
        closes_at=datetime(2027, 1, 1, tzinfo=UTC),
    )


def _lines(amount: int = 10_000) -> tuple[PostingLine, ...]:
    return (
        PostingLine(account_id=uuid4(), side=PostingSide.DEBIT, amount=Money(amount, "EUR")),
        PostingLine(account_id=uuid4(), side=PostingSide.CREDIT, amount=Money(amount, "EUR")),
    )


def _entry(
    scope: OrganizationalScopeRef, period: AccountingPeriod, *, amount: int = 10_000
) -> JournalEntry:
    return JournalEntry(
        entry_id=uuid4(),
        scope=scope,
        period=period.as_reference(),
        lines=_lines(amount),
        reason=_REASON,
    )


def _transaction(
    scope: OrganizationalScopeRef,
    period: AccountingPeriod,
    *,
    external_reference: str = "stmt-1",
) -> FinancialTransaction:
    return FinancialTransaction(
        transaction_id=uuid4(),
        scope=scope,
        provenance=Provenance(
            kind=ProvenanceKind.IMPORTED,
            source_system_reference="bank-feed",
            recorded_by_authority="treasury",
            import_batch_reference="fp-2026-03",
            external_reference=external_reference,
        ),
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        recorded_at=_NOW,
        reporting_period=period.as_reference(),
    )


def _contribution(
    scope: OrganizationalScopeRef,
    *,
    handle_reference: str,
    received_at: datetime = datetime(2026, 2, 10, tzinfo=UTC),
) -> FinanceContribution:
    receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=received_at,
        method="bank_transfer",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=handle_reference,
    )
    return FinanceContribution(
        contribution_id=uuid4(), scope=scope, receipt=receipt, retention=_RETENTION
    )


def _snapshot(scope: OrganizationalScopeRef, period: ReportingPeriodRef) -> ReportSnapshot:
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(scope,),
        state=reporting.PerimeterDefinitionState.ACTIVE,
    )
    return ReportSnapshot.freeze(
        snapshot_id=uuid4(),
        scope=scope,
        period=period,
        perimeter=freeze_perimeter(definition, _NOW),
        frozen_at=_NOW,
        policy_bindings=(_POLICY,),
        included_transaction_ids=(uuid4(),),
        included_entry_ids=(uuid4(),),
    )


def _batch(scope: OrganizationalScopeRef, *, fingerprint: str = "fp-2026-03") -> ImportBatchRecord:
    return ImportBatchRecord(
        batch_id=uuid4(),
        scope=scope,
        provenance=Provenance(
            kind=ProvenanceKind.IMPORTED,
            source_system_reference="bank-feed",
            recorded_by_authority="treasury",
            import_batch_reference=fingerprint,
        ),
        fingerprint=fingerprint,
        registered_at=_NOW,
        record_count=1,
    )


def _package_classes() -> list[type]:
    """Every class the package itself defines, ports and adapters alike."""
    found: dict[str, type] = {}
    for module in PACKAGE_MODULES:
        for _, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__.startswith(epd2_finance_service.__name__):
                found[f"{member.__module__}.{member.__qualname__}"] = member
    return list(found.values())


def _own_attribute_names(cls: type) -> set[str]:
    """The attribute names `cls` and its in-package bases actually declare.

    Names inherited from a builtin base are excluded: a `StrEnum` gets
    `str.removeprefix` for free, and that is not this package publishing a
    removal API."""
    names: set[str] = set()
    for base in cls.__mro__:
        if base.__module__.startswith(epd2_finance_service.__name__):
            names.update(vars(base))
    return names


# =============================================================================
# No deletion exists anywhere (`ФИН-05`, `ФИН-22`)
# =============================================================================


def test_no_port_or_adapter_exposes_any_delete_shaped_method() -> None:
    offending: list[str] = []
    for cls in _package_classes():
        for name in _own_attribute_names(cls):
            if name.startswith("__"):
                continue
            if any(fragment in name.lower() for fragment in DELETE_SHAPED_NAMES):
                offending.append(f"{cls.__module__}.{cls.__qualname__}.{name}")
    assert offending == []


def test_the_storage_module_names_deletion_exactly_once_and_only_to_refuse() -> None:
    functions = {
        name
        for name, member in inspect.getmembers(storage, inspect.isfunction)
        if member.__module__ == storage.__name__
        and any(fragment in name.lower() for fragment in DELETE_SHAPED_NAMES)
    }
    assert functions == {"delete_finance_record"}


def test_delete_finance_record_raises() -> None:
    scope = _scope()
    with pytest.raises(GovernedRecordDeletionForbiddenError) as excinfo:
        delete_finance_record(_account(scope))
    assert excinfo.value.reason_code == "GOVERNED_RECORD_DELETION_FORBIDDEN"


def test_delete_finance_record_refuses_whatever_it_is_handed() -> None:
    scope = _scope()
    period = _period(scope)
    for record in (period, _entry(scope, period), _transaction(scope, period), object()):
        with pytest.raises(GovernedRecordDeletionForbiddenError):
            delete_finance_record(record)


# =============================================================================
# Scope isolation (`ФИН-03`)
# =============================================================================


def test_a_scoped_list_never_returns_another_scopes_record() -> None:
    here, elsewhere = _scope(), _scope()
    accounts = InMemoryFinanceAccountStore()
    mine = _account(here)
    theirs = _account(elsewhere)
    accounts.save(mine)
    accounts.save(theirs)
    assert accounts.list_for_scope(scope=here) == (mine,)
    assert accounts.list_for_scope(scope=elsewhere) == (theirs,)
    assert accounts.find_by_code(scope=here, code="1000") == mine
    assert accounts.find_by_code(scope=elsewhere, code="1000") == theirs


def test_every_scoped_list_across_the_stores_filters_on_the_scope() -> None:
    here, elsewhere = _scope(), _scope()
    periods = InMemoryAccountingPeriodStore()
    entries = InMemoryJournalEntryStore()
    transactions = InMemoryFinancialTransactionStore()
    contributions = InMemoryFinanceContributionStore()

    here_period, other_period = _period(here), _period(elsewhere)
    periods.save(here_period)
    periods.save(other_period)
    assert periods.list_for_scope(scope=here) == (here_period,)

    entries.save(_entry(here, here_period))
    entries.save(_entry(elsewhere, other_period))
    assert len(entries.list_for_period(scope=here, period_id=here_period.period_id)) == 1
    assert entries.list_for_period(scope=here, period_id=other_period.period_id) == ()

    transactions.save(_transaction(here, here_period))
    transactions.save(_transaction(elsewhere, other_period))
    assert len(transactions.list_for_scope(scope=here)) == 1

    handle_reference = "fph:contribution:" + str(uuid4())
    contributions.save(_contribution(here, handle_reference=handle_reference))
    contributions.save(_contribution(elsewhere, handle_reference=handle_reference))
    assert len(contributions.list_for_scope(scope=here)) == 1
    assert (
        len(
            contributions.list_for_party_in_window(
                scope=here,
                party_handle_reference=handle_reference,
                window_start=datetime(2026, 1, 1, tzinfo=UTC),
                window_end=datetime(2027, 1, 1, tzinfo=UTC),
            )
        )
        == 1
    )


def test_the_aggregation_window_is_half_open_so_a_boundary_receipt_is_counted_once() -> None:
    scope = _scope()
    contributions = InMemoryFinanceContributionStore()
    handle_reference = "fph:contribution:" + str(uuid4())
    boundary = datetime(2026, 7, 1, tzinfo=UTC)
    contributions.save(
        _contribution(scope, handle_reference=handle_reference, received_at=boundary)
    )
    first_half = contributions.list_for_party_in_window(
        scope=scope,
        party_handle_reference=handle_reference,
        window_start=datetime(2026, 1, 1, tzinfo=UTC),
        window_end=boundary,
    )
    second_half = contributions.list_for_party_in_window(
        scope=scope,
        party_handle_reference=handle_reference,
        window_start=boundary,
        window_end=datetime(2027, 1, 1, tzinfo=UTC),
    )
    assert first_half == ()
    assert len(second_half) == 1


def test_an_unattributed_contribution_is_never_aggregated_to_a_stranger() -> None:
    scope = _scope()
    contributions = InMemoryFinanceContributionStore()
    unattributed = FinanceContribution(
        contribution_id=uuid4(),
        scope=scope,
        receipt=ContributionReceipt(
            receipt_id=uuid4(),
            kind=ContributionKind.DONATION,
            received_at=datetime(2026, 2, 10, tzinfo=UTC),
            method="cash",
            amount=Money(50_000, "EUR"),
            contributor_handle_reference=None,
        ),
        retention=_RETENTION,
    )
    contributions.save(unattributed)
    assert (
        contributions.list_for_party_in_window(
            scope=scope,
            party_handle_reference="fph:contribution:" + str(uuid4()),
            window_start=datetime(2026, 1, 1, tzinfo=UTC),
            window_end=datetime(2027, 1, 1, tzinfo=UTC),
        )
        == ()
    )


def test_a_scoped_query_has_no_list_everything_overload() -> None:
    for name, member in inspect.getmembers(storage, inspect.isclass):
        if not name.startswith("InMemory"):
            continue
        for method_name in dir(member):
            if not method_name.startswith("list_"):
                continue
            signature = inspect.signature(getattr(member, method_name))
            assert "scope" in signature.parameters, f"{name}.{method_name} takes no scope"


# =============================================================================
# Append-only storage (`ФИН-05`, `ФИН-24`)
# =============================================================================


def test_a_posted_entry_cannot_be_silently_replaced() -> None:
    scope = _scope()
    period = _period(scope)
    entries = InMemoryJournalEntryStore()
    posted = post(_entry(scope, period), 1, period=period)
    entries.save(posted)
    rewritten = replace(posted, lines=_lines(99_000))
    with pytest.raises(ImmutableRecordModificationAttemptedError) as excinfo:
        entries.save(rewritten)
    assert excinfo.value.reason_code == "FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED"
    stored = entries.get(posted.entry_id)
    assert stored is not None
    assert stored.lines == posted.lines


def test_storing_an_identical_posted_entry_again_is_a_harmless_replay() -> None:
    scope = _scope()
    period = _period(scope)
    entries = InMemoryJournalEntryStore()
    posted = post(_entry(scope, period), 1, period=period)
    entries.save(posted)
    entries.save(posted)
    assert entries.get(posted.entry_id) == posted


def test_marking_a_posted_entry_reversed_is_the_one_permitted_difference() -> None:
    scope = _scope()
    period = _period(scope)
    entries = InMemoryJournalEntryStore()
    posted = post(_entry(scope, period), 1, period=period)
    entries.save(posted)
    marked, reversal = reverse(posted, entry_id=uuid4(), reason=_REASON)
    entries.save(marked)
    entries.save(reversal)
    stored = entries.get(posted.entry_id)
    assert stored is not None
    assert stored.status is EntryStatus.REVERSED
    assert stored.lines == posted.lines


def test_the_posting_sequence_allocator_is_gap_free_per_scope_and_period() -> None:
    here, elsewhere = _scope(), _scope()
    entries = InMemoryJournalEntryStore()
    here_period, other_period = _period(here), _period(elsewhere)
    allocated = [
        entries.next_sequence(scope=here, period_id=here_period.period_id) for _ in range(3)
    ]
    assert allocated == [1, 2, 3]
    assert entries.next_sequence(scope=elsewhere, period_id=other_period.period_id) == 1


def test_the_sequence_allocator_does_not_reissue_a_number_a_stored_posting_carries() -> None:
    scope = _scope()
    period = _period(scope)
    entries = InMemoryJournalEntryStore()
    entries.save(post(_entry(scope, period), 7, period=period))
    assert entries.next_sequence(scope=scope, period_id=period.period_id) == 8


def test_a_frozen_snapshot_cannot_be_replaced() -> None:
    scope = _scope()
    period = ReportingPeriodRef(period_id=uuid4(), label="2026", scope=scope)
    snapshots = InMemoryReportSnapshotStore()
    snapshot = _snapshot(scope, period)
    snapshots.save(snapshot)
    with pytest.raises(ImmutableRecordModificationAttemptedError) as excinfo:
        snapshots.save(snapshot)
    assert excinfo.value.reason_code == "FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED"
    assert snapshots.get(snapshot.snapshot_id) == snapshot


def test_a_frozen_perimeter_is_returned_rather_than_refrozen_and_a_differing_one_refuses() -> None:
    scope = _scope()
    other = _scope()
    perimeters = InMemoryPerimeterSnapshotStore()
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(scope,),
        state=reporting.PerimeterDefinitionState.ACTIVE,
    )
    first = perimeters.freeze_once(freeze_perimeter(definition, _NOW))
    again = perimeters.freeze_once(freeze_perimeter(definition, datetime(2026, 4, 1, tzinfo=UTC)))
    assert again is first
    widened = replace(definition, included_scopes=(scope, other))
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        perimeters.freeze_once(freeze_perimeter(widened, _NOW))


def test_a_granted_publication_permission_is_never_rewritten() -> None:
    scope = _scope()
    publications = InMemoryPublicationAuthorizationStore()
    authorization_record = PublicationAuthorization(
        authorization_id=uuid4(),
        scope=scope,
        authorized_by=_authority(scope, actor="actor-orgadmin"),
        authorized_at=_NOW,
        reason=_REASON,
    )
    publications.save(authorization_record)
    publications.save(authorization_record)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        publications.save(replace(authorization_record, policy=_POLICY))


def test_a_party_handle_is_never_re_purposed_or_re_scoped() -> None:
    scope = _scope()
    handles = InMemoryFinancePartyHandleStore()
    handle = FinancePartyHandle(
        handle_id=uuid4(), purpose=HandlePurpose.CONTRIBUTION, perimeter=scope
    )
    handles.put(handle)
    handles.put(handle)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        handles.put(replace(handle, purpose=HandlePurpose.SPONSORSHIP))
    stored = handles.get(handle.handle_id)
    assert stored is not None
    assert stored.purpose is HandlePurpose.CONTRIBUTION


def test_handles_cannot_be_listed_across_purposes() -> None:
    scope = _scope()
    handles = InMemoryFinancePartyHandleStore()
    contribution_handle = FinancePartyHandle(
        handle_id=uuid4(), purpose=HandlePurpose.CONTRIBUTION, perimeter=scope
    )
    sponsorship_handle = FinancePartyHandle(
        handle_id=uuid4(), purpose=HandlePurpose.SPONSORSHIP, perimeter=scope
    )
    handles.put(contribution_handle)
    handles.put(sponsorship_handle)
    listed = handles.list_for_purpose(scope=scope, purpose=HandlePurpose.CONTRIBUTION)
    assert listed == (contribution_handle,)
    signature = inspect.signature(InMemoryFinancePartyHandleStore.list_for_purpose)
    assert "purpose" in signature.parameters


# =============================================================================
# Import batches (`ФИН-38`)
# =============================================================================


def test_an_applied_import_fingerprint_cannot_be_applied_twice() -> None:
    scope = _scope()
    batches = InMemoryImportBatchStore()
    batch = batches.register(_batch(scope))
    batches.mark_applied(
        batch_id=batch.batch_id, applied_at=_NOW, accepted_count=1, rejected_count=0
    )
    with pytest.raises(DuplicateImportError) as excinfo:
        batches.register(_batch(scope))
    assert excinfo.value.reason_code == "FINANCE_DUPLICATE_IMPORT"
    with pytest.raises(DuplicateImportError):
        batches.mark_applied(
            batch_id=batch.batch_id, applied_at=_NOW, accepted_count=1, rejected_count=0
        )


def test_the_fingerprint_index_is_scoped_so_one_unit_never_blocks_another() -> None:
    here, elsewhere = _scope(), _scope()
    batches = InMemoryImportBatchStore()
    mine = batches.register(_batch(here))
    batches.mark_applied(
        batch_id=mine.batch_id, applied_at=_NOW, accepted_count=1, rejected_count=0
    )
    theirs = batches.register(_batch(elsewhere))
    assert theirs.status is ImportBatchStatus.REGISTERED
    assert batches.find_by_fingerprint(scope=elsewhere, fingerprint="fp-2026-03") == theirs


def test_re_registering_the_identical_batch_is_an_idempotent_replay() -> None:
    scope = _scope()
    batches = InMemoryImportBatchStore()
    batch = _batch(scope)
    assert batches.register(batch) is batch
    assert batches.register(batch) is batch
    with pytest.raises(DuplicateImportError):
        batches.register(replace(batch, record_count=2))


def test_applying_an_unregistered_batch_answers_not_found() -> None:
    batches = InMemoryImportBatchStore()
    with pytest.raises(FinanceRecordNotFoundError) as excinfo:
        batches.mark_applied(batch_id=uuid4(), applied_at=_NOW, accepted_count=1, rejected_count=0)
    assert excinfo.value.reason_code == "VALIDATION_RECORD_NOT_FOUND"


def test_an_import_batch_with_no_fingerprint_cannot_be_checked_for_replay() -> None:
    scope = _scope()
    with pytest.raises(ImportProvenanceMissingError):
        ImportBatchRecord(
            batch_id=uuid4(),
            scope=scope,
            provenance=Provenance(
                kind=ProvenanceKind.IMPORTED,
                source_system_reference="bank-feed",
                recorded_by_authority="treasury",
                import_batch_reference="fp",
            ),
            fingerprint="  ",
            registered_at=_NOW,
        )


def test_the_transaction_fingerprint_is_deterministic_and_scope_sensitive() -> None:
    here, elsewhere = _scope(), _scope()
    here_period = _period(here)
    first = _transaction(here, here_period)
    assert transaction_fingerprint(first) == transaction_fingerprint(first)
    other_scope_transaction = _transaction(elsewhere, _period(elsewhere))
    assert transaction_fingerprint(first) != transaction_fingerprint(other_scope_transaction)
    different_reference = _transaction(here, here_period, external_reference="stmt-2")
    assert transaction_fingerprint(first) != transaction_fingerprint(different_reference)


def test_a_journal_entry_store_returns_every_entry_that_cites_one_transaction() -> None:
    scope = _scope()
    period = _period(scope)
    entries = InMemoryJournalEntryStore()
    transaction_id = uuid4()
    original = replace(post(_entry(scope, period), 1, period=period), transaction_id=transaction_id)
    entries.save(original)
    _, reversal = reverse(original, entry_id=uuid4(), reason=_REASON)
    entries.save(replace(reversal, transaction_id=transaction_id))
    cited = entries.list_for_transaction(scope=scope, transaction_id=transaction_id)
    assert len(cited) == 2


def test_a_period_covering_query_answers_within_its_own_scope_only() -> None:
    here, elsewhere = _scope(), _scope()
    periods = InMemoryAccountingPeriodStore()
    period = _period(here)
    periods.save(period)
    moment = datetime(2026, 6, 1, tzinfo=UTC)
    assert periods.find_covering(scope=here, moment=moment) == period
    assert periods.find_covering(scope=elsewhere, moment=moment) is None


def test_a_period_covering_query_refuses_a_naive_moment() -> None:
    scope = _scope()
    periods = InMemoryAccountingPeriodStore()
    periods.save(_period(scope))
    with pytest.raises(AccountingPeriodUndeterminedError):
        periods.find_covering(scope=scope, moment=datetime(2026, 6, 1))


def test_an_unknown_identifier_answers_none_rather_than_raising() -> None:
    accounts = InMemoryFinanceAccountStore()
    assert accounts.get(uuid4()) is None
    entries = InMemoryJournalEntryStore()
    assert entries.get(uuid4()) is None
    snapshots = InMemoryReportSnapshotStore()
    assert snapshots.get(uuid4()) is None


def test_the_finance_audit_event_store_port_is_audit_cores_own_and_not_a_local_copy() -> None:
    from epd2_audit_core.storage import AuditEventStore

    assert storage.FinanceAuditEventStore is AuditEventStore


def test_an_idempotency_record_requires_a_command_a_digest_and_a_zoned_instant() -> None:
    record = storage.IdempotencyRecord(
        event_id=uuid4(),
        command="record_contribution",
        request_digest="digest-1",
        aggregate_id=uuid4(),
        recorded_at=_NOW,
    )
    assert record.command == "record_contribution"
    with pytest.raises(MonetaryAmountInvalidError) as excinfo:
        storage.IdempotencyRecord(
            event_id=uuid4(),
            command="  ",
            request_digest="digest-1",
            aggregate_id=uuid4(),
            recorded_at=_NOW,
        )
    assert excinfo.value.reason_code == "FINANCE_MONETARY_AMOUNT_INVALID"


def test_the_event_sink_records_what_the_command_layer_published_in_order() -> None:
    sink = storage.InMemoryEventSink()
    assert sink.published() == ()


def test_a_uuid_keyed_store_never_mutates_the_record_it_was_handed() -> None:
    scope = _scope()
    accounts = InMemoryFinanceAccountStore()
    account = _account(scope)
    accounts.save(account)
    stored = accounts.get(account.account_id)
    assert stored is account
    assert isinstance(account.account_id, UUID)
