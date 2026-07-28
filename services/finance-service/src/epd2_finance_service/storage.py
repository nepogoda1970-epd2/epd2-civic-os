"""Storage ports and in-memory reference adapters for Finance Service's
authoritative aggregates (PACK-10, canon 0.8.0 section 19f).

Same shape PACK-02 through PACK-09 already established (see
`services/compliance-service/src/epd2_compliance_service/storage.py`): one
explicit `Protocol` per aggregate, plus a deliberately simple in-memory
adapter. **No production persistence is introduced here** - real
databases, migrations, outbox tables and the production event plane stay
assigned to PACK-13 (ADR-038).

Six storage rules are load-bearing for this pack's own invariants and are
therefore enforced *by the store*, not merely by convention:

1. **No delete method exists anywhere in this module** - not on a port,
   not on an adapter. `ФИН-05` makes a posted register entry immutable and
   `ФИН-22` plus PACK-09's legal hold outrank any wish to destroy, so a
   port that offered `delete` would be publishing an act the domain
   forbids and inviting an adapter to implement it. The single
   module-level `delete_finance_record` exists to *refuse*, mirroring
   `reporting.delete_report_version`.
2. **Scope isolation by default (`ФИН-03`).** Every query that can return
   more than one record takes a required keyword-only
   `scope: OrganizationalScopeRef` and filters on it. There is no
   "list everything" overload: a read with no scope is not a broader
   query, it is a missing authorisation boundary. Single-record `get`
   returns whatever is stored under that id and leaves the scope
   assertion to the application layer - exactly as PACK-07's
   `MembershipStore.get` and PACK-09's `get_unscoped` do, and for the
   same reason: only the application layer knows which scope the *caller*
   presented, and the aggregates carry `scope.assert_matches` for it.
3. **Append-only where the domain is append-only.** `save` on an
   immutable-once-posted aggregate refuses to replace a stored instance
   with a differing one (`InMemoryJournalEntryStore`,
   `InMemoryReimbursementStore`, `InMemoryPublicationAuthorizationStore`,
   `InMemoryFinancePartyHandleStore`); a `ReportSnapshot` refuses
   replacement outright (`ФИН-24`).
4. **Sequence allocation is a storage concern, ordering guarantees are
   not.** `JournalEntryStore.next_sequence` hands out the gap-free
   per-(scope, period) posting sequence `ledger.post` requires; see its
   docstring for what this adapter deliberately does *not* promise.
5. **Optimistic concurrency is the application layer's job.** There is no
   version column invented here. `FinancialTransaction.version`,
   `ReportingPerimeterDefinition.version`, `FinanceReportVersion.version`
   and every aggregate's `history` tuple already carry that state, so an
   `expected_*_version` check belongs where the command is decided. A
   storage-level check would be a second, disagreeing source of truth:
   two places able to answer "is this stale?" differently is worse than
   one place answering it.
6. **The in-memory adapters are reference implementations, not a data
   plane.** They are not concurrency-safe, not durable, and hold every
   record as a live object reference rather than a serialised row.

What this module does *not* contain: no query returns a projection, a
total or a trial balance (`projections` owns derived read models, and they
are authoritative for nothing); no store resolves a party handle to a
person (`ФИН-01`); no store consults a policy, a period lock, an
authority or a legal hold, because a storage adapter that quietly refused
a write on governed grounds would be a second, invisible decision point
next to `application`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_audit_core.storage import AuditEventStore
from epd2_core.event_envelope import EventEnvelope
from epd2_finance_service.domain import (
    FinancePartyHandle,
    HandlePurpose,
    OrganizationalScopeRef,
    Provenance,
    deterministic_digest,
    require_timezone,
)
from epd2_finance_service.exceptions import (
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
)
from epd2_finance_service.records import (
    ExpenseClaim,
    ExternalFinancialBenefit,
    FinanceContribution,
    FinancialAsset,
    FinancialObligation,
    GovernedTransfer,
    PaymentAuthorization,
    Reimbursement,
    SponsorshipAgreement,
)
from epd2_finance_service.reporting import (
    AuditEngagement,
    FinanceReportVersion,
    PerimeterDefinitionState,
    PerimeterSnapshot,
    PublicationAuthorization,
    ReportingObligation,
    ReportingPerimeterDefinition,
    ReportSnapshot,
)

#: Audit Core's append-only event store port, named here so the finance
#: application layer depends on *that* port rather than on a
#: finance-local re-declaration of it. Finance never defines its own
#: audit store: the hash chain, the conflict detection and the
#: `get_by_event_id` idempotency of the audit append all belong to
#: PACK-02's implementation, and a second protocol describing the same
#: table would eventually drift from it.
FinanceAuditEventStore = AuditEventStore


# ---------------------------------------------------------------------------
# The forbidden act, published as a refusal
# ---------------------------------------------------------------------------


def delete_finance_record(record: object) -> None:
    """Always raises `GovernedRecordDeletionForbiddenError`.

    The one place in this module that names deletion at all, and it exists
    to refuse. The honest API for an act the domain forbids is a
    reason-coded refusal, not a missing function: a caller that reaches
    for deletion gets `FINANCE_GOVERNED_RECORD_DELETION_FORBIDDEN` and the
    reason, instead of an `AttributeError` that says nothing about why, or
    - far worse - an adapter-local `delete` someone added because "the
    port was obviously incomplete".

    Deliberately typed `object`: every finance aggregate is equally
    undeletable, and narrowing the parameter to a union would suggest the
    listed types are the deletable ones. Mirrors
    `reporting.delete_report_version`, which refuses the same act for the
    one aggregate whose replacement most looks like a deletion
    (`ФИН-05`, `ФИН-22`)."""
    raise GovernedRecordDeletionForbiddenError(
        f"{type(record).__name__} is a governed finance record and is never deleted; "
        "a wrong record is corrected, reversed or superseded and remains readable"
    )


def _in_scope(record_scope: OrganizationalScopeRef, scope: OrganizationalScopeRef) -> bool:
    """Whether `record_scope` is the scope the caller asked about.

    Compares `organization_id` only, exactly as
    `OrganizationalScopeRef.assert_matches` does. `scope_kind` is
    PACK-08's label for the node, not part of its identity; comparing it
    too would silently hide records from a caller that named the same
    organization with a different kind string, and a hidden record reads
    as a deleted one."""
    return record_scope.organization_id == scope.organization_id


# ---------------------------------------------------------------------------
# Command idempotency
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """What one already-executed command left behind, keyed by the
    caller-supplied `event_id` from `RequestContext`.

    Lives in this module because it is an infrastructure record of a
    *command execution*, not a canonical finance aggregate: nothing in
    canon 19f owns it, no event is emitted about it and it appears in no
    report."""

    event_id: UUID
    command: str
    request_digest: str
    aggregate_id: UUID
    recorded_at: datetime

    def __post_init__(self) -> None:
        # `MonetaryAmountInvalidError` for non-monetary emptiness follows
        # `domain.Provenance` and `domain.AuthorityReference`, which use it
        # the same way. It reads oddly here; adding a new exception class
        # to carry "a required string was blank" would fragment the reason
        # codes further, which reads worse.
        if not self.command.strip():
            raise MonetaryAmountInvalidError("command must be non-empty")
        if not self.request_digest.strip():
            raise MonetaryAmountInvalidError("request_digest must be non-empty")
        require_timezone(self.recorded_at, context="IdempotencyRecord.recorded_at")


class CommandIdempotencyStore(Protocol):
    """Idempotency for the *command* layer, keyed by `event_id`.

    Audit Core's `AuditEventStore.get_by_event_id` (plus the conflict
    check in its `append`) already makes the **audit append** idempotent:
    replaying an audit event with the same id and identical content is a
    no-op. That guarantees nothing about the aggregate. Without this
    store, a retried `record_contribution` would pass the audit's
    idempotency check on a *fresh* event id and mint a second
    contribution - two governed records for one real receipt, which
    `ФИН-14` aggregation would then count twice.

    A replay carrying the same `event_id` with a *different*
    `request_digest` is not idempotent and not a duplicate - it is a
    conflict, and the application layer raises `IdempotencyConflictError`
    for it. That decision is not duplicated here: see this module's rule
    5 for why one decision point beats two."""

    def get(self, event_id: UUID) -> IdempotencyRecord | None: ...

    def put(self, record: IdempotencyRecord) -> None: ...


class InMemoryCommandIdempotencyStore:
    """Reference adapter: one dict keyed by `event_id`.

    `put` stores what it is given and performs no conflict check, because
    the conflict is a command-layer judgement (see the port's docstring).
    A durable backend would key this table on `event_id` with a unique
    index and let the insert itself fail, which is the only version of
    this check that survives concurrent retries - this adapter cannot,
    and does not pretend to."""

    def __init__(self) -> None:
        self._records: dict[UUID, IdempotencyRecord] = {}

    def get(self, event_id: UUID) -> IdempotencyRecord | None:
        return self._records.get(event_id)

    def put(self, record: IdempotencyRecord) -> None:
        self._records[record.event_id] = record


# ---------------------------------------------------------------------------
# Event sink
# ---------------------------------------------------------------------------


class EventSink(Protocol):
    """Where the command layer writes the canonical envelopes it emits.

    **This is not a production event bus and must not be read as one.**
    PACK-13 owns the production event plane: the outbox, the broker, the
    delivery guarantees, the retry and dead-letter behaviour, the
    consumer contracts. None of that exists in PACK-10.

    The port exists for two honest reasons. The command layer must write
    its events *somewhere* it does not own, so that emitting an event is
    a call to a boundary rather than an `append` to a list some service
    module happens to hold; and contract tests must be able to assert on
    the exact envelopes emitted - event type, version, subject, payload
    hash - because `ФИН-02` (no identity key in any payload) is a claim
    about emitted envelopes, not about intentions."""

    def publish(self, envelope: EventEnvelope) -> None: ...

    def published(self) -> tuple[EventEnvelope, ...]: ...


class InMemoryEventSink:
    """Reference `EventSink`: an ordered in-process list.

    Delivers to nobody. Publication order is call order, which is *not* a
    guarantee any real bus makes and which tests should therefore assert
    on only where the command layer's own ordering is what is under
    test."""

    def __init__(self) -> None:
        self._published: list[EventEnvelope] = []

    def publish(self, envelope: EventEnvelope) -> None:
        self._published.append(envelope)

    def published(self) -> tuple[EventEnvelope, ...]:
        return tuple(self._published)


# ---------------------------------------------------------------------------
# Import batches (`ФИН-38`, `ФИН-41`)
# ---------------------------------------------------------------------------


class ImportBatchStatus(StrEnum):
    """`registered` -> (`applied` | `rejected`).

    An import batch is registered before anything is booked from it, so a
    crash between registration and application leaves a `registered` row
    rather than a silently re-appliable file (`ФИН-38`)."""

    REGISTERED = "registered"
    APPLIED = "applied"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ImportBatchRecord:
    """The record of one ingestion act: what was imported, from where,
    under which fingerprint, and whether it was applied.

    Defined in this module, and nowhere earlier, on purpose. It is an
    **infrastructure-level record of an ingestion act**, not a canonical
    finance aggregate: canon 19f names no `ImportBatch` entity, it carries
    no monetary effect, it appears in no report and no reporting perimeter
    includes it. What canon 19f.6 and `ФИН-38` require is that every
    imported transaction cites a provenance with an
    `import_batch_reference` and that an already-applied batch cannot be
    applied twice - which needs a place to remember fingerprints, and
    that place is storage.

    `fingerprint` is the ingestion adapter's content digest of the source
    file or feed window, not something this module computes: only the
    adapter sees the bytes. The counts are what the adapter *reported*
    and are authoritative for nothing - the transaction register is."""

    batch_id: UUID
    scope: OrganizationalScopeRef
    provenance: Provenance
    fingerprint: str
    registered_at: datetime
    status: ImportBatchStatus = ImportBatchStatus.REGISTERED
    record_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    applied_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.fingerprint.strip():
            raise ImportProvenanceMissingError(
                "an import batch with no fingerprint cannot be checked for replay"
            )
        require_timezone(self.registered_at, context="ImportBatchRecord.registered_at")
        if min(self.record_count, self.accepted_count, self.rejected_count) < 0:
            raise MonetaryAmountInvalidError("import batch counts must not be negative")
        if self.applied_at is not None:
            require_timezone(self.applied_at, context="ImportBatchRecord.applied_at")
        if self.status is ImportBatchStatus.APPLIED and self.applied_at is None:
            raise ImportProvenanceMissingError(
                "an applied import batch must record when it was applied"
            )


class ImportBatchStore(Protocol):
    """Replay detection for imports, keyed by `(scope, fingerprint)`.

    No delete: a rejected batch stays recorded, because "this feed was
    ingested and refused" is the answer to a later reconciliation
    question, and removing the row would make a re-submission of the same
    bytes look like a first arrival (`ФИН-38`)."""

    def register(self, batch: ImportBatchRecord) -> ImportBatchRecord: ...

    def get(self, batch_id: UUID) -> ImportBatchRecord | None: ...

    def find_by_fingerprint(
        self, *, scope: OrganizationalScopeRef, fingerprint: str
    ) -> ImportBatchRecord | None: ...

    def mark_applied(
        self, *, batch_id: UUID, applied_at: datetime, accepted_count: int, rejected_count: int
    ) -> ImportBatchRecord: ...


class InMemoryImportBatchStore:
    """Reference adapter. The fingerprint index is scoped, because two
    organizations may legitimately import byte-identical files (the same
    published funding statement, say) and one unit's ingestion must never
    block another's (`ФИН-03`).

    `register` refuses a fingerprint that already reached `applied`
    (`DuplicateImportError`); re-registering the *same* batch id with
    identical content is an idempotent replay and returns the stored
    record. A durable backend would carry a unique index on
    `(organization_id, fingerprint)` where status is `applied`, so the
    refusal survives two workers racing - this adapter's check does
    not."""

    def __init__(self) -> None:
        self._batches: dict[UUID, ImportBatchRecord] = {}
        self._order: list[UUID] = []

    def register(self, batch: ImportBatchRecord) -> ImportBatchRecord:
        existing = self._batches.get(batch.batch_id)
        if existing is not None:
            if existing != batch:
                raise DuplicateImportError(
                    f"import batch {batch.batch_id} is already registered with different content"
                )
            return existing
        applied = self.find_by_fingerprint(scope=batch.scope, fingerprint=batch.fingerprint)
        if applied is not None and applied.status is ImportBatchStatus.APPLIED:
            raise DuplicateImportError(
                f"import fingerprint {batch.fingerprint} was already applied as batch "
                f"{applied.batch_id}"
            )
        self._batches[batch.batch_id] = batch
        self._order.append(batch.batch_id)
        return batch

    def get(self, batch_id: UUID) -> ImportBatchRecord | None:
        return self._batches.get(batch_id)

    def find_by_fingerprint(
        self, *, scope: OrganizationalScopeRef, fingerprint: str
    ) -> ImportBatchRecord | None:
        applied: ImportBatchRecord | None = None
        first: ImportBatchRecord | None = None
        for batch_id in self._order:
            batch = self._batches[batch_id]
            if not _in_scope(batch.scope, scope) or batch.fingerprint != fingerprint:
                continue
            if batch.status is ImportBatchStatus.APPLIED:
                # An applied batch is the answer that matters: it is the
                # one that makes a re-arrival a duplicate. Returning the
                # earliest *registered* one instead would let a rejected
                # first attempt mask the applied second.
                applied = batch if applied is None else applied
            first = batch if first is None else first
        return applied if applied is not None else first

    def mark_applied(
        self, *, batch_id: UUID, applied_at: datetime, accepted_count: int, rejected_count: int
    ) -> ImportBatchRecord:
        batch = self._batches.get(batch_id)
        if batch is None:
            raise FinanceRecordNotFoundError(f"import batch {batch_id} is not registered")
        if batch.status is ImportBatchStatus.APPLIED:
            raise DuplicateImportError(
                f"import batch {batch_id} is already applied; applying it again would re-book "
                "every transaction it carried"
            )
        require_timezone(applied_at, context="mark_applied.applied_at")
        updated = replace(
            batch,
            status=ImportBatchStatus.APPLIED,
            applied_at=applied_at,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
        )
        self._batches[batch_id] = updated
        return updated


# ---------------------------------------------------------------------------
# Chart of accounts
# ---------------------------------------------------------------------------


class FinanceAccountStore(Protocol):
    """An account belongs to exactly one scope and is never shared, so
    `code` is unique only *within* a scope - which is why
    `find_by_code` takes one (`ФИН-03`, canon 19f.4)."""

    def save(self, account: FinanceAccount) -> None: ...

    def get(self, account_id: UUID) -> FinanceAccount | None: ...

    def find_by_code(
        self, *, scope: OrganizationalScopeRef, code: str
    ) -> FinanceAccount | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinanceAccount, ...]: ...


class InMemoryFinanceAccountStore:
    """Reference adapter.

    `save` accepts a replacement freely: `FinanceAccount` is a mutable
    aggregate whose own transitions guard `code`, `classification_code`
    and `has_postings` (`ФИН-13`). Re-checking that here would put the
    chart-of-accounts rule in two places, and the store's copy would be
    the one nobody updates."""

    def __init__(self) -> None:
        self._accounts: dict[UUID, FinanceAccount] = {}

    def save(self, account: FinanceAccount) -> None:
        self._accounts[account.account_id] = account

    def get(self, account_id: UUID) -> FinanceAccount | None:
        return self._accounts.get(account_id)

    def find_by_code(self, *, scope: OrganizationalScopeRef, code: str) -> FinanceAccount | None:
        for account in self._accounts.values():
            if _in_scope(account.scope, scope) and account.code == code:
                return account
        return None

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinanceAccount, ...]:
        return tuple(
            account for account in self._accounts.values() if _in_scope(account.scope, scope)
        )


# ---------------------------------------------------------------------------
# Accounting periods
# ---------------------------------------------------------------------------


class AccountingPeriodStore(Protocol):
    """Periods, and the lookup `ledger.post` depends on.

    There is deliberately no `PeriodReopeningRecordStore`: a reopening
    record is create-once *on the period aggregate*
    (`AccountingPeriod.reopening_records`), and a separate table would
    make it possible to store a period whose reopening history disagrees
    with its own status (`ФИН-11`).

    `find_covering` returns `None` when no period covers the moment. It
    does **not** raise `AccountingPeriodUndeterminedError`: "no period
    here" is a storage answer, "and therefore this posting is refused" is
    the command's decision (`ФИН-10`, `ФИН-39`)."""

    def save(self, period: AccountingPeriod) -> None: ...

    def get(self, period_id: UUID) -> AccountingPeriod | None: ...

    def find_covering(
        self, *, scope: OrganizationalScopeRef, moment: datetime
    ) -> AccountingPeriod | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[AccountingPeriod, ...]: ...


class InMemoryAccountingPeriodStore:
    def __init__(self) -> None:
        self._periods: dict[UUID, AccountingPeriod] = {}

    def save(self, period: AccountingPeriod) -> None:
        self._periods[period.period_id] = period

    def get(self, period_id: UUID) -> AccountingPeriod | None:
        return self._periods.get(period_id)

    def find_covering(
        self, *, scope: OrganizationalScopeRef, moment: datetime
    ) -> AccountingPeriod | None:
        """Half-open `[opens_at, closes_at)`, so two adjacent periods
        never both claim the boundary instant and never both disown it.

        `moment` must be timezone-explicit; a naive instant is refused
        rather than compared against timezone-aware bounds, where Python
        would raise an opaque `TypeError` instead of naming the defect
        (`ФИН-39`)."""
        require_timezone(moment, context="find_covering.moment")
        for period in self._periods.values():
            if _in_scope(period.scope, scope) and period.opens_at <= moment < period.closes_at:
                return period
        return None

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[AccountingPeriod, ...]:
        return tuple(period for period in self._periods.values() if _in_scope(period.scope, scope))


# ---------------------------------------------------------------------------
# The accounting register
# ---------------------------------------------------------------------------


class JournalEntryStore(Protocol):
    """The authoritative register of monetary effect.

    No delete, and no edit path either: `save` here is how a draft is
    amended and how a posting is recorded, and it refuses to overwrite a
    posted entry with a differing one (`ФИН-05`). The only ways to change
    monetary effect after posting are `ledger.reverse` and
    `ledger.correct`, both of which write *new* entries."""

    def save(self, entry: JournalEntry) -> None: ...

    def get(self, entry_id: UUID) -> JournalEntry | None: ...

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[JournalEntry, ...]: ...

    def list_for_transaction(
        self, *, scope: OrganizationalScopeRef, transaction_id: UUID
    ) -> tuple[JournalEntry, ...]: ...

    def next_sequence(self, *, scope: OrganizationalScopeRef, period_id: UUID) -> int: ...


class InMemoryJournalEntryStore:
    """Reference adapter enforcing the one rule storage can enforce here:
    a posted entry is not rewritten.

    `save` raises `ImmutableRecordModificationAttemptedError` when an
    entry already stored as `EntryStatus.POSTED` (or `REVERSED`) is
    replaced by a different object. Exactly one difference is permitted:
    `POSTED` -> `REVERSED` with every other field unchanged, because
    `ledger.reverse` returns precisely that alongside the new reversal
    entry, and both halves of one act must be storable. An earlier draft
    of this check refused any change to a posted entry and would have
    made `ledger.reverse` impossible to persist - the store would have
    been enforcing a stricter rule than the domain, which is not a safer
    store but a broken one.

    Storing an identical object again is a no-op replay, not a
    violation."""

    def __init__(self) -> None:
        self._entries: dict[UUID, JournalEntry] = {}
        self._sequences: dict[tuple[UUID, UUID], int] = {}

    @staticmethod
    def _is_reversal_marking(stored: JournalEntry, incoming: JournalEntry) -> bool:
        return (
            stored.status is EntryStatus.POSTED
            and incoming.status is EntryStatus.REVERSED
            and replace(stored, status=EntryStatus.REVERSED) == incoming
        )

    def save(self, entry: JournalEntry) -> None:
        stored = self._entries.get(entry.entry_id)
        if (
            stored is not None
            and stored.status in (EntryStatus.POSTED, EntryStatus.REVERSED)
            and stored != entry
            and not self._is_reversal_marking(stored, entry)
        ):
            raise ImmutableRecordModificationAttemptedError(
                f"journal entry {entry.entry_id} is stored as {stored.status!s} and is "
                "content-immutable; reverse or correct it with a new entry instead"
            )
        self._entries[entry.entry_id] = entry

    def get(self, entry_id: UUID) -> JournalEntry | None:
        return self._entries.get(entry_id)

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[JournalEntry, ...]:
        return tuple(
            entry
            for entry in self._entries.values()
            if _in_scope(entry.scope, scope) and entry.period.period_id == period_id
        )

    def list_for_transaction(
        self, *, scope: OrganizationalScopeRef, transaction_id: UUID
    ) -> tuple[JournalEntry, ...]:
        """More than one entry may cite one transaction: the original
        posting, its reversal and any correction all do. Returning a
        tuple rather than an optional single entry is what lets the
        correction chain be reconstructed at all (`ФИН-06`)."""
        return tuple(
            entry
            for entry in self._entries.values()
            if _in_scope(entry.scope, scope) and entry.transaction_id == transaction_id
        )

    def next_sequence(self, *, scope: OrganizationalScopeRef, period_id: UUID) -> int:
        """The next posting sequence for `(scope, period_id)`:
        monotonically increasing, gap-free, and independent per period.

        Sequences are per (scope, period) because the register is
        per-scope (`ФИН-03`) and a period's postings are what a report
        enumerates; a service-wide counter would make one unit's
        ingestion volume visible in another's sequence numbers.

        The high-water mark is taken from the stored entries as well as
        from the counter, so a re-hydrated store does not restart at 1 and
        re-issue a number an existing posting already carries.

        **Deliberately not concurrency-safe.** Two callers interleaving
        here receive two different numbers only because CPython happens
        not to preempt inside this method; nothing enforces it. A durable
        backend allocates from a database sequence (or an `INSERT`
        returning a serial column), which is the only mechanism that
        keeps the guarantee under concurrency. It is also the only
        mechanism that keeps it *gap-free in effect*: a number handed out
        here and then discarded because the posting was refused leaves a
        hole, and a hole in a posting sequence is exactly what an auditor
        reads as a removed entry. The command layer therefore allocates
        last, after every check has passed."""
        key = (scope.organization_id, period_id)
        highest = self._sequences.get(key, 0)
        for entry in self._entries.values():
            if (
                entry.entry_sequence is not None
                and entry.scope.organization_id == key[0]
                and entry.period.period_id == period_id
            ):
                highest = max(highest, entry.entry_sequence)
        allocated = highest + 1
        self._sequences[key] = allocated
        return allocated


# ---------------------------------------------------------------------------
# The transaction register
# ---------------------------------------------------------------------------


def transaction_fingerprint(transaction: FinancialTransaction) -> str:
    """The intake-identity digest of a transaction, for duplicate and
    replay detection (`ФИН-38`, `ФИН-41`).

    Covers the scope, the source system, the external and import-batch
    references, and the transaction and posting dates - the fields fixed
    at intake and guarded afterwards by
    `ledger.assert_provenance_unchanged`.

    Two honest limits. The **amount is not in the digest**: under the
    single authoritative money layer (ADR-049) monetary effect lives on
    the `JournalEntry`, not on the transaction, so the transaction alone
    cannot fingerprint it. And for a `MANUAL_ENTRY` with no
    `external_reference`, two genuinely distinct same-day intakes in one
    scope produce the *same* digest. This function therefore answers
    "has something already arrived under this identity?", never "is this
    a duplicate?" - the second question is `DuplicateTransactionError`'s
    and the command layer's. A durable backend would carry a unique index
    only where `external_reference` is present, since that is the only
    case where uniqueness is a fact rather than a guess."""
    provenance = transaction.provenance
    return deterministic_digest(
        str(transaction.scope.organization_id),
        "|",
        provenance.source_system_reference,
        "|",
        provenance.external_reference or "",
        "|",
        provenance.import_batch_reference or "",
        "|",
        transaction.transaction_date.isoformat(),
        "|",
        transaction.posting_date.isoformat(),
    )


class FinancialTransactionStore(Protocol):
    """The authoritative register of business fact and provenance.

    `save` accepts replacements: a transaction is classified, posted,
    corrected and reversed through its own guarded transitions, and it
    carries its own `version` for the application layer's
    `expected_version` check (rule 5)."""

    def save(self, transaction: FinancialTransaction) -> None: ...

    def get(self, transaction_id: UUID) -> FinancialTransaction | None: ...

    def find_by_fingerprint(
        self, *, scope: OrganizationalScopeRef, fingerprint: str
    ) -> FinancialTransaction | None: ...

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[FinancialTransaction, ...]: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[FinancialTransaction, ...]: ...


class InMemoryFinancialTransactionStore:
    """Reference adapter. `find_by_fingerprint` returns the **earliest
    recorded** match, because the question it answers is "what already
    exists that this may be a replay of", and the answer must be stable
    as later arrivals accumulate."""

    def __init__(self) -> None:
        self._transactions: dict[UUID, FinancialTransaction] = {}
        self._order: list[UUID] = []

    def save(self, transaction: FinancialTransaction) -> None:
        if transaction.transaction_id not in self._transactions:
            self._order.append(transaction.transaction_id)
        self._transactions[transaction.transaction_id] = transaction

    def get(self, transaction_id: UUID) -> FinancialTransaction | None:
        return self._transactions.get(transaction_id)

    def find_by_fingerprint(
        self, *, scope: OrganizationalScopeRef, fingerprint: str
    ) -> FinancialTransaction | None:
        for transaction_id in self._order:
            transaction = self._transactions[transaction_id]
            if not _in_scope(transaction.scope, scope):
                continue
            if transaction_fingerprint(transaction) == fingerprint:
                return transaction
        return None

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[FinancialTransaction, ...]:
        return tuple(
            self._transactions[transaction_id]
            for transaction_id in self._order
            if _in_scope(self._transactions[transaction_id].scope, scope)
            and self._transactions[transaction_id].reporting_period.period_id == period_id
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinancialTransaction, ...]:
        return tuple(
            self._transactions[transaction_id]
            for transaction_id in self._order
            if _in_scope(self._transactions[transaction_id].scope, scope)
        )


# ---------------------------------------------------------------------------
# Governed transfers
# ---------------------------------------------------------------------------


class GovernedTransferStore(Protocol):
    """Two-scoped by construction, and owned by neither scope.

    A `GovernedTransfer` has no single `scope` field: it holds one leg per
    unit. `list_for_scope` therefore means "transfers with a leg in this
    scope", and the same transfer legitimately answers for both units.
    That is the point - consolidation recognises the *pair* through
    `internal_transfer_reference` and eliminates it exactly once, without
    a higher scope ever writing into a lower one (`ФИН-37`)."""

    def save(self, transfer: GovernedTransfer) -> None: ...

    def get(self, transfer_id: UUID) -> GovernedTransfer | None: ...

    def find_by_internal_transfer_reference(
        self, *, scope: OrganizationalScopeRef, internal_transfer_reference: str
    ) -> GovernedTransfer | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[GovernedTransfer, ...]: ...


class InMemoryGovernedTransferStore:
    def __init__(self) -> None:
        self._transfers: dict[UUID, GovernedTransfer] = {}

    def save(self, transfer: GovernedTransfer) -> None:
        self._transfers[transfer.transfer_id] = transfer

    def get(self, transfer_id: UUID) -> GovernedTransfer | None:
        return self._transfers.get(transfer_id)

    def find_by_internal_transfer_reference(
        self, *, scope: OrganizationalScopeRef, internal_transfer_reference: str
    ) -> GovernedTransfer | None:
        """Scoped even though the reference is meant to be unique: a
        caller may only discover a transfer it has a leg in. Answering
        for a reference guessed from another unit's records would make
        this a cross-scope existence probe (`ФИН-03`)."""
        for transfer in self._transfers.values():
            if transfer.internal_transfer_reference != internal_transfer_reference:
                continue
            if any(_in_scope(leg.scope, scope) for leg in transfer.legs):
                return transfer
        return None

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[GovernedTransfer, ...]:
        return tuple(
            transfer
            for transfer in self._transfers.values()
            if any(_in_scope(leg.scope, scope) for leg in transfer.legs)
        )


# ---------------------------------------------------------------------------
# Contributions
# ---------------------------------------------------------------------------


class FinanceContributionStore(Protocol):
    """Contributions, including the window query the aggregation rule
    needs.

    `list_for_party_in_window` exists because `ФИН-14`/`ФИН-15` are about
    *sums*, not single receipts: a contributor splitting one donation
    into six payments below a threshold must be visible as one aggregate,
    and a store that could only fetch contributions one id at a time
    would make the threshold rule unimplementable - which is how split
    donations stay invisible in practice."""

    def save(self, contribution: FinanceContribution) -> None: ...

    def get(self, contribution_id: UUID) -> FinanceContribution | None: ...

    def list_for_party_in_window(
        self,
        *,
        scope: OrganizationalScopeRef,
        party_handle_reference: str,
        window_start: datetime,
        window_end: datetime,
    ) -> tuple[FinanceContribution, ...]: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[FinanceContribution, ...]: ...


class InMemoryFinanceContributionStore:
    def __init__(self) -> None:
        self._contributions: dict[UUID, FinanceContribution] = {}

    def save(self, contribution: FinanceContribution) -> None:
        self._contributions[contribution.contribution_id] = contribution

    def get(self, contribution_id: UUID) -> FinanceContribution | None:
        return self._contributions.get(contribution_id)

    def list_for_party_in_window(
        self,
        *,
        scope: OrganizationalScopeRef,
        party_handle_reference: str,
        window_start: datetime,
        window_end: datetime,
    ) -> tuple[FinanceContribution, ...]:
        """Half-open `[window_start, window_end)` on
        `receipt.received_at`.

        Half-open so two adjacent windows neither double-count a
        contribution received at the boundary instant nor drop it -
        either error changes an aggregate, and an aggregate is what a
        threshold decision is taken on (`ФИН-14`).

        Matches on the **receipt's** `contributor_handle_reference`. A
        handle is purpose- and perimeter-scoped, so this query cannot
        reach across purposes or perimeters even if a caller supplies a
        handle reference from one (`ФИН-01`). Contributions whose source
        could not be established carry `None` and are therefore never
        returned here: they are not "somebody else's", they are
        unattributed, and they sit in `QUARANTINED` waiting for a
        decision rather than being silently aggregated to a stranger
        (`ФИН-16`)."""
        require_timezone(window_start, context="list_for_party_in_window.window_start")
        require_timezone(window_end, context="list_for_party_in_window.window_end")
        return tuple(
            contribution
            for contribution in self._contributions.values()
            if (
                _in_scope(contribution.scope, scope)
                and contribution.receipt.contributor_handle_reference == party_handle_reference
                and window_start <= contribution.receipt.received_at < window_end
            )
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinanceContribution, ...]:
        return tuple(
            contribution
            for contribution in self._contributions.values()
            if _in_scope(contribution.scope, scope)
        )


# ---------------------------------------------------------------------------
# Sponsorship and external financial benefit
# ---------------------------------------------------------------------------


class SponsorshipAgreementStore(Protocol):
    def save(self, agreement: SponsorshipAgreement) -> None: ...

    def get(self, agreement_id: UUID) -> SponsorshipAgreement | None: ...

    def list_for_sponsor(
        self, *, scope: OrganizationalScopeRef, sponsor_handle_reference: str
    ) -> tuple[SponsorshipAgreement, ...]: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[SponsorshipAgreement, ...]: ...


class InMemorySponsorshipAgreementStore:
    """`list_for_sponsor` is here for the same reason the contribution
    window query is: a sponsor's total across agreements is what a
    disclosure decision looks at, and a per-id store hides it. It is
    deliberately *not* a window query - a sponsorship carries its own
    `period_start`/`period_end`, so the period filter belongs to the
    caller's policy rather than to a received-at instant."""

    def __init__(self) -> None:
        self._agreements: dict[UUID, SponsorshipAgreement] = {}

    def save(self, agreement: SponsorshipAgreement) -> None:
        self._agreements[agreement.agreement_id] = agreement

    def get(self, agreement_id: UUID) -> SponsorshipAgreement | None:
        return self._agreements.get(agreement_id)

    def list_for_sponsor(
        self, *, scope: OrganizationalScopeRef, sponsor_handle_reference: str
    ) -> tuple[SponsorshipAgreement, ...]:
        return tuple(
            agreement
            for agreement in self._agreements.values()
            if (
                _in_scope(agreement.scope, scope)
                and agreement.sponsor_handle_reference == sponsor_handle_reference
            )
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[SponsorshipAgreement, ...]:
        return tuple(
            agreement
            for agreement in self._agreements.values()
            if _in_scope(agreement.scope, scope)
        )


class ExternalFinancialBenefitStore(Protocol):
    def save(self, benefit: ExternalFinancialBenefit) -> None: ...

    def get(self, benefit_id: UUID) -> ExternalFinancialBenefit | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[ExternalFinancialBenefit, ...]: ...


class InMemoryExternalFinancialBenefitStore:
    def __init__(self) -> None:
        self._benefits: dict[UUID, ExternalFinancialBenefit] = {}

    def save(self, benefit: ExternalFinancialBenefit) -> None:
        self._benefits[benefit.benefit_id] = benefit

    def get(self, benefit_id: UUID) -> ExternalFinancialBenefit | None:
        return self._benefits.get(benefit_id)

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[ExternalFinancialBenefit, ...]:
        return tuple(
            benefit for benefit in self._benefits.values() if _in_scope(benefit.scope, scope)
        )


# ---------------------------------------------------------------------------
# Expenses, payment authorization, reimbursement
# ---------------------------------------------------------------------------


class ExpenseClaimStore(Protocol):
    def save(self, claim: ExpenseClaim) -> None: ...

    def get(self, claim_id: UUID) -> ExpenseClaim | None: ...

    def list_for_claimant(
        self, *, scope: OrganizationalScopeRef, claimant_handle_reference: str
    ) -> tuple[ExpenseClaim, ...]: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[ExpenseClaim, ...]: ...


class InMemoryExpenseClaimStore:
    def __init__(self) -> None:
        self._claims: dict[UUID, ExpenseClaim] = {}

    def save(self, claim: ExpenseClaim) -> None:
        self._claims[claim.claim_id] = claim

    def get(self, claim_id: UUID) -> ExpenseClaim | None:
        return self._claims.get(claim_id)

    def list_for_claimant(
        self, *, scope: OrganizationalScopeRef, claimant_handle_reference: str
    ) -> tuple[ExpenseClaim, ...]:
        return tuple(
            claim
            for claim in self._claims.values()
            if (
                _in_scope(claim.scope, scope)
                and claim.claimant_handle_reference == claimant_handle_reference
            )
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[ExpenseClaim, ...]:
        return tuple(claim for claim in self._claims.values() if _in_scope(claim.scope, scope))


class PaymentAuthorizationStore(Protocol):
    """`list_for_payable` returns a **tuple**, not one authorization.

    One payable may legitimately accumulate several: a revoked
    authorization stays stored (nothing is deleted, rule 1) and a fresh
    one is issued after it. Returning "the" authorization would force
    this store to pick, and picking is where a revoked authorization
    quietly becomes the one a payment cites (`ФИН-31`)."""

    def save(self, authorization: PaymentAuthorization) -> None: ...

    def get(self, authorization_id: UUID) -> PaymentAuthorization | None: ...

    def list_for_payable(
        self, *, scope: OrganizationalScopeRef, payable_kind: str, payable_reference: UUID
    ) -> tuple[PaymentAuthorization, ...]: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[PaymentAuthorization, ...]: ...


class InMemoryPaymentAuthorizationStore:
    def __init__(self) -> None:
        self._authorizations: dict[UUID, PaymentAuthorization] = {}

    def save(self, authorization: PaymentAuthorization) -> None:
        self._authorizations[authorization.authorization_id] = authorization

    def get(self, authorization_id: UUID) -> PaymentAuthorization | None:
        return self._authorizations.get(authorization_id)

    def list_for_payable(
        self, *, scope: OrganizationalScopeRef, payable_kind: str, payable_reference: UUID
    ) -> tuple[PaymentAuthorization, ...]:
        return tuple(
            authorization
            for authorization in self._authorizations.values()
            if (
                _in_scope(authorization.scope, scope)
                and authorization.payable_kind == payable_kind
                and authorization.payable_reference == payable_reference
            )
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[PaymentAuthorization, ...]:
        return tuple(
            authorization
            for authorization in self._authorizations.values()
            if _in_scope(authorization.scope, scope)
        )


class ReimbursementStore(Protocol):
    """A payout record has no mutator in `records` at all, so storage
    refuses to replace one with a differing object: a wrong
    reimbursement is answered by a correcting claim and a new record, not
    by a rewritten row (`ФИН-05`, `ФИН-31`)."""

    def save(self, reimbursement: Reimbursement) -> None: ...

    def get(self, reimbursement_id: UUID) -> Reimbursement | None: ...

    def find_for_claim(
        self, *, scope: OrganizationalScopeRef, claim_id: UUID
    ) -> Reimbursement | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[Reimbursement, ...]: ...


class InMemoryReimbursementStore:
    def __init__(self) -> None:
        self._reimbursements: dict[UUID, Reimbursement] = {}

    def save(self, reimbursement: Reimbursement) -> None:
        stored = self._reimbursements.get(reimbursement.reimbursement_id)
        if stored is not None and stored != reimbursement:
            raise ImmutableRecordModificationAttemptedError(
                f"reimbursement {reimbursement.reimbursement_id} is already recorded; a payout "
                "record is never rewritten"
            )
        self._reimbursements[reimbursement.reimbursement_id] = reimbursement

    def get(self, reimbursement_id: UUID) -> Reimbursement | None:
        return self._reimbursements.get(reimbursement_id)

    def find_for_claim(
        self, *, scope: OrganizationalScopeRef, claim_id: UUID
    ) -> Reimbursement | None:
        for reimbursement in self._reimbursements.values():
            if _in_scope(reimbursement.scope, scope) and reimbursement.claim_id == claim_id:
                return reimbursement
        return None

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[Reimbursement, ...]:
        return tuple(
            reimbursement
            for reimbursement in self._reimbursements.values()
            if _in_scope(reimbursement.scope, scope)
        )


# ---------------------------------------------------------------------------
# Assets and obligations
# ---------------------------------------------------------------------------


class FinancialAssetStore(Protocol):
    def save(self, asset: FinancialAsset) -> None: ...

    def get(self, asset_id: UUID) -> FinancialAsset | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinancialAsset, ...]: ...


class InMemoryFinancialAssetStore:
    """A disposed or written-off asset stays stored: its terminal state is
    guarded by the aggregate, and the record still has to explain the
    valuation it left the books at (`ФИН-05`)."""

    def __init__(self) -> None:
        self._assets: dict[UUID, FinancialAsset] = {}

    def save(self, asset: FinancialAsset) -> None:
        self._assets[asset.asset_id] = asset

    def get(self, asset_id: UUID) -> FinancialAsset | None:
        return self._assets.get(asset_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinancialAsset, ...]:
        return tuple(asset for asset in self._assets.values() if _in_scope(asset.scope, scope))


class FinancialObligationStore(Protocol):
    def save(self, obligation: FinancialObligation) -> None: ...

    def get(self, obligation_id: UUID) -> FinancialObligation | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[FinancialObligation, ...]: ...


class InMemoryFinancialObligationStore:
    def __init__(self) -> None:
        self._obligations: dict[UUID, FinancialObligation] = {}

    def save(self, obligation: FinancialObligation) -> None:
        self._obligations[obligation.obligation_id] = obligation

    def get(self, obligation_id: UUID) -> FinancialObligation | None:
        return self._obligations.get(obligation_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[FinancialObligation, ...]:
        return tuple(
            obligation
            for obligation in self._obligations.values()
            if _in_scope(obligation.scope, scope)
        )


# ---------------------------------------------------------------------------
# Reporting obligations and the perimeter
# ---------------------------------------------------------------------------


class ReportingObligationStore(Protocol):
    def save(self, obligation: ReportingObligation) -> None: ...

    def get(self, obligation_id: UUID) -> ReportingObligation | None: ...

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[ReportingObligation, ...]: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[ReportingObligation, ...]: ...


class InMemoryReportingObligationStore:
    """A waived or superseded obligation is still listed. `ФИН-40` is
    only meaningful if an unfulfilled duty stays visible: a store that
    filtered terminal states by default would let a silent waiver look
    like an absent obligation, which is the failure the invariant is
    about."""

    def __init__(self) -> None:
        self._obligations: dict[UUID, ReportingObligation] = {}

    def save(self, obligation: ReportingObligation) -> None:
        self._obligations[obligation.obligation_id] = obligation

    def get(self, obligation_id: UUID) -> ReportingObligation | None:
        return self._obligations.get(obligation_id)

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[ReportingObligation, ...]:
        return tuple(
            obligation
            for obligation in self._obligations.values()
            if _in_scope(obligation.scope, scope) and obligation.period.period_id == period_id
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[ReportingObligation, ...]:
        return tuple(
            obligation
            for obligation in self._obligations.values()
            if _in_scope(obligation.scope, scope)
        )


class ReportingPerimeterDefinitionStore(Protocol):
    """Versioned by `(definition_id, version)`.

    A change to a perimeter is a new version, never an edit of an active
    one (`ФИН-25`), so this store is keyed by the pair and an older
    version stays readable: it is what a past report's meaning depends
    on."""

    def save(self, definition: ReportingPerimeterDefinition) -> None: ...

    def get_version(
        self, definition_id: UUID, version: int
    ) -> ReportingPerimeterDefinition | None: ...

    def latest_version(self, definition_id: UUID) -> ReportingPerimeterDefinition | None: ...

    def resolve_active(
        self, *, scope: OrganizationalScopeRef, effective_on: date
    ) -> ReportingPerimeterDefinition | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[ReportingPerimeterDefinition, ...]: ...


class InMemoryReportingPerimeterDefinitionStore:
    """`resolve_active` answers with the highest active version whose
    effective window covers `effective_on`, and with `None` when there is
    none.

    `None` is not "the perimeter is the hierarchy as it stands now" -
    canon 19f.16 forbids exactly that inference. It means the perimeter is
    undetermined, and `ReportingPerimeterUndeterminedError` is the
    command layer's to raise, on its own evidence."""

    def __init__(self) -> None:
        self._definitions: dict[tuple[UUID, int], ReportingPerimeterDefinition] = {}

    def save(self, definition: ReportingPerimeterDefinition) -> None:
        self._definitions[(definition.definition_id, definition.version)] = definition

    def get_version(self, definition_id: UUID, version: int) -> ReportingPerimeterDefinition | None:
        return self._definitions.get((definition_id, version))

    def latest_version(self, definition_id: UUID) -> ReportingPerimeterDefinition | None:
        versions = [
            definition
            for (stored_id, _), definition in self._definitions.items()
            if stored_id == definition_id
        ]
        if not versions:
            return None
        return max(versions, key=lambda definition: definition.version)

    def resolve_active(
        self, *, scope: OrganizationalScopeRef, effective_on: date
    ) -> ReportingPerimeterDefinition | None:
        candidates = [
            definition
            for definition in self._definitions.values()
            if (
                _in_scope(definition.scope, scope)
                and definition.state is PerimeterDefinitionState.ACTIVE
                and definition.effective_from <= effective_on
                and (
                    definition.effective_until is None or effective_on < definition.effective_until
                )
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda definition: definition.version)

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[ReportingPerimeterDefinition, ...]:
        return tuple(
            definition
            for definition in self._definitions.values()
            if _in_scope(definition.scope, scope)
        )


class PerimeterSnapshotStore(Protocol):
    """Frozen perimeters, keyed by `(definition_id, definition_version)`.

    A `PerimeterSnapshot` has no id of its own and no owning scope - it
    names the scopes it *includes*. `list_for_scope` therefore asks "which
    frozen perimeters included this scope", which is the question a unit
    asks when it wants to know which consolidations its figures appear
    in."""

    def freeze_once(self, snapshot: PerimeterSnapshot) -> PerimeterSnapshot: ...

    def get(self, definition_id: UUID, definition_version: int) -> PerimeterSnapshot | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[PerimeterSnapshot, ...]: ...


class InMemoryPerimeterSnapshotStore:
    """`freeze_once` compares on `digest`, not on the whole object.

    The digest covers the definition, its version and its scope ids -
    everything the snapshot *asserts*. `frozen_at` records when the
    freeze happened, so re-freezing the same definition version at a
    later instant yields an object that differs in `frozen_at` and in
    nothing that matters; the first freeze stands and is returned. A
    freeze whose digest differs is a claim that the same perimeter
    version covers different scopes, and that is refused (`ФИН-24`,
    `ФИН-25`)."""

    def __init__(self) -> None:
        self._snapshots: dict[tuple[UUID, int], PerimeterSnapshot] = {}

    def freeze_once(self, snapshot: PerimeterSnapshot) -> PerimeterSnapshot:
        key = (snapshot.definition_id, snapshot.definition_version)
        stored = self._snapshots.get(key)
        if stored is not None:
            if stored.digest != snapshot.digest:
                raise ImmutableRecordModificationAttemptedError(
                    f"perimeter definition {snapshot.definition_id} version "
                    f"{snapshot.definition_version} is already frozen with a different digest"
                )
            return stored
        self._snapshots[key] = snapshot
        return snapshot

    def get(self, definition_id: UUID, definition_version: int) -> PerimeterSnapshot | None:
        return self._snapshots.get((definition_id, definition_version))

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[PerimeterSnapshot, ...]:
        return tuple(
            snapshot
            for snapshot in self._snapshots.values()
            if any(_in_scope(included, scope) for included in snapshot.included_scopes)
        )


# ---------------------------------------------------------------------------
# Report snapshots
# ---------------------------------------------------------------------------


class ReportSnapshotStore(Protocol):
    """Create-once, and stricter than every other store here.

    A snapshot is created once and survives every later report version:
    a restatement computes a *new* snapshot and the old one stays, because
    the earlier version's figures are only answerable against the state
    they were computed from (`ФИН-24`, `ФИН-25`)."""

    def save(self, snapshot: ReportSnapshot) -> None: ...

    def get(self, snapshot_id: UUID) -> ReportSnapshot | None: ...

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[ReportSnapshot, ...]: ...


class InMemoryReportSnapshotStore:
    """`save` refuses to replace an existing snapshot **at all** - not
    only a differing one.

    Every other append-only store here permits an identical re-save as a
    harmless replay. This one does not, and the difference is deliberate:
    a `ReportSnapshot` re-derives and re-checks its own `content_digest`
    in `__post_init__`, so two objects with the same `snapshot_id` and
    equal content are already indistinguishable, and a second `save` can
    only mean the command ran twice. That case belongs to
    `CommandIdempotencyStore`, which returns the first snapshot's id
    instead of freezing again. Letting storage absorb it silently would
    hide a double-executed freeze - and a freeze that ran twice may have
    read two different register states between the two runs (`ФИН-24`)."""

    def __init__(self) -> None:
        self._snapshots: dict[UUID, ReportSnapshot] = {}

    def save(self, snapshot: ReportSnapshot) -> None:
        if snapshot.snapshot_id in self._snapshots:
            raise ImmutableRecordModificationAttemptedError(
                f"report snapshot {snapshot.snapshot_id} is already frozen; a snapshot is "
                "created once and is never replaced or recomputed"
            )
        self._snapshots[snapshot.snapshot_id] = snapshot

    def get(self, snapshot_id: UUID) -> ReportSnapshot | None:
        return self._snapshots.get(snapshot_id)

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[ReportSnapshot, ...]:
        return tuple(
            snapshot
            for snapshot in self._snapshots.values()
            if _in_scope(snapshot.scope, scope) and snapshot.period.period_id == period_id
        )


# ---------------------------------------------------------------------------
# Report versions, publication authorization, audit engagements
# ---------------------------------------------------------------------------


class FinanceReportVersionStore(Protocol):
    """Versions of one report, keyed by `version_id` and grouped by
    `report_id`.

    Every version stays stored, including superseded ones: a newer
    version never destroys an earlier submitted, acknowledged or
    published one (`ФИН-05`, and see `reporting.delete_report_version`,
    which refuses that act explicitly)."""

    def save(self, version: FinanceReportVersion) -> None: ...

    def get(self, version_id: UUID) -> FinanceReportVersion | None: ...

    def list_for_report(
        self, *, scope: OrganizationalScopeRef, report_id: UUID
    ) -> tuple[FinanceReportVersion, ...]: ...

    def latest_version(
        self, *, scope: OrganizationalScopeRef, report_id: UUID
    ) -> FinanceReportVersion | None: ...


class InMemoryFinanceReportVersionStore:
    """`save` accepts replacements, because a report version is a
    long-lived aggregate with twelve states and its own field-immutability
    rules: `FinanceReportVersion.with_changes` already refuses an edit in
    a submitted, accepted, published or superseded state, while the
    governed transitions out of those states legitimately produce a new
    object under the same `version_id`. A storage-level refusal keyed on
    state would have to encode that twelve-state table a second time and
    would sooner or later disagree with it (rule 5)."""

    def __init__(self) -> None:
        self._versions: dict[UUID, FinanceReportVersion] = {}

    def save(self, version: FinanceReportVersion) -> None:
        self._versions[version.version_id] = version

    def get(self, version_id: UUID) -> FinanceReportVersion | None:
        return self._versions.get(version_id)

    def list_for_report(
        self, *, scope: OrganizationalScopeRef, report_id: UUID
    ) -> tuple[FinanceReportVersion, ...]:
        return tuple(
            sorted(
                (
                    version
                    for version in self._versions.values()
                    if _in_scope(version.scope, scope) and version.report_id == report_id
                ),
                key=lambda version: version.version,
            )
        )

    def latest_version(
        self, *, scope: OrganizationalScopeRef, report_id: UUID
    ) -> FinanceReportVersion | None:
        """Highest `version` number, not "most recently saved".

        Insertion order would make the answer depend on the order the
        application layer happened to write, and "which version is
        current" is a claim a restatement must not be able to change by
        touching an older one."""
        versions = self.list_for_report(scope=scope, report_id=report_id)
        return versions[-1] if versions else None


class PublicationAuthorizationStore(Protocol):
    """Publication authorizations, stored separately from approvals
    because approval and publication are different decisions (`ФИН-28`,
    `ФИН-34`).

    Create-once: `PublicationAuthorization` has no mutator in `reporting`,
    so a differing replacement would be a rewritten permission - and a
    rewritten permission is how a publication ends up citing an
    authorisation nobody gave in that form."""

    def save(self, authorization: PublicationAuthorization) -> None: ...

    def get(self, authorization_id: UUID) -> PublicationAuthorization | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[PublicationAuthorization, ...]: ...


class InMemoryPublicationAuthorizationStore:
    def __init__(self) -> None:
        self._authorizations: dict[UUID, PublicationAuthorization] = {}

    def save(self, authorization: PublicationAuthorization) -> None:
        stored = self._authorizations.get(authorization.authorization_id)
        if stored is not None and stored != authorization:
            raise ImmutableRecordModificationAttemptedError(
                f"publication authorization {authorization.authorization_id} is already "
                "recorded; a granted publication permission is never rewritten"
            )
        self._authorizations[authorization.authorization_id] = authorization

    def get(self, authorization_id: UUID) -> PublicationAuthorization | None:
        return self._authorizations.get(authorization_id)

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[PublicationAuthorization, ...]:
        return tuple(
            authorization
            for authorization in self._authorizations.values()
            if _in_scope(authorization.scope, scope)
        )


class AuditEngagementStore(Protocol):
    def save(self, engagement: AuditEngagement) -> None: ...

    def get(self, engagement_id: UUID) -> AuditEngagement | None: ...

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[AuditEngagement, ...]: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[AuditEngagement, ...]: ...


class InMemoryAuditEngagementStore:
    """Findings and the conclusion live on the aggregate, so there is no
    `AuditFindingStore` and no `AuditConclusionStore`.

    That is not a shortcut: a finding table writable independently of the
    engagement would let a finding be added to a concluded engagement
    without the independence re-check the aggregate performs at every
    finding (`ФИН-29`, `ФИН-30`)."""

    def __init__(self) -> None:
        self._engagements: dict[UUID, AuditEngagement] = {}

    def save(self, engagement: AuditEngagement) -> None:
        self._engagements[engagement.engagement_id] = engagement

    def get(self, engagement_id: UUID) -> AuditEngagement | None:
        return self._engagements.get(engagement_id)

    def list_for_period(
        self, *, scope: OrganizationalScopeRef, period_id: UUID
    ) -> tuple[AuditEngagement, ...]:
        return tuple(
            engagement
            for engagement in self._engagements.values()
            if _in_scope(engagement.scope, scope) and engagement.period.period_id == period_id
        )

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[AuditEngagement, ...]:
        return tuple(
            engagement
            for engagement in self._engagements.values()
            if _in_scope(engagement.scope, scope)
        )


# ---------------------------------------------------------------------------
# Party handles
# ---------------------------------------------------------------------------


class FinancePartyHandleStore(Protocol):
    """The purpose-scoped party references this service mints (`ФИН-01`).

    Two things this port deliberately cannot do. It cannot resolve a
    handle to a person: re-identification is the party registry's act and
    is audited there (`ФИН-36`), and a `resolve` method here would make
    finance the place that holds the join. And it cannot list handles
    across purposes - `list_for_purpose` requires the purpose, because a
    scope-wide handle listing is precisely the correlation surface the
    purpose scoping exists to remove."""

    def put(self, handle: FinancePartyHandle) -> None: ...

    def get(self, handle_id: UUID) -> FinancePartyHandle | None: ...

    def list_for_purpose(
        self, *, scope: OrganizationalScopeRef, purpose: HandlePurpose
    ) -> tuple[FinancePartyHandle, ...]: ...


class InMemoryFinancePartyHandleStore:
    """`put` refuses to replace a stored handle with a different one.

    A handle's purpose and perimeter are fixed at minting; re-putting the
    same `handle_id` with another purpose would re-point every record that
    already cites it, which is a silent cross-purpose join rather than an
    update (`ФИН-01`)."""

    def __init__(self) -> None:
        self._handles: dict[UUID, FinancePartyHandle] = {}

    def put(self, handle: FinancePartyHandle) -> None:
        stored = self._handles.get(handle.handle_id)
        if stored is not None and stored != handle:
            raise ImmutableRecordModificationAttemptedError(
                f"party handle {handle.handle_id} is already minted for purpose "
                f"{stored.purpose!s}; a handle is never re-purposed or re-scoped"
            )
        self._handles[handle.handle_id] = handle

    def get(self, handle_id: UUID) -> FinancePartyHandle | None:
        return self._handles.get(handle_id)

    def list_for_purpose(
        self, *, scope: OrganizationalScopeRef, purpose: HandlePurpose
    ) -> tuple[FinancePartyHandle, ...]:
        return tuple(
            handle
            for handle in self._handles.values()
            if _in_scope(handle.perimeter, scope) and handle.purpose is purpose
        )
