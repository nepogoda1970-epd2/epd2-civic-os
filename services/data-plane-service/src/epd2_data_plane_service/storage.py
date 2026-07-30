"""Storage ports and in-memory reference adapters (PACK-13 §8, §33).

Same shape PACK-02 through PACK-12 established: one explicit `Protocol`
per aggregate, plus a deliberately simple in-memory adapter. **No
production persistence is introduced here** — no PostgreSQL, no
connection pool, no SQL, no migration executed against a real engine.
`P13-PATH-001` names the existing storage ports as the migration seam,
and these ports are that seam for PACK-13's own aggregates: a production
adapter implements the same `Protocol` and the domain layer does not
change.

Seven storage rules are load-bearing and are therefore enforced *by the
store*, not merely by convention:

1. **No delete method exists anywhere in this module** — not on a port,
   not on an adapter (`P13-PATH-005`: no storage port acquires a delete
   method in the course of this work). The single module-level
   `delete_data_plane_record` exists to *refuse*, mirroring PACK-10's,
   PACK-11's and PACK-12's precedent.
2. **Applied migrations are append-only.** `AppliedMigrationStore.append`
   refuses to replace a stored record, so `P13-MIG-001`'s immutability
   cannot be undone through the storage layer.
3. **Schema versions are append-only**, and a historical
   `schema_version_id` is never re-pointed (`P13-REG-005g`).
4. **Outbox records change only their delivery metadata.** The store
   refuses a replacement whose event identity, type, version or envelope
   differs (`P13-OBX-003`).
5. **Scope isolation by default.** Every query that can return more than
   one record takes a required keyword-only `scope` and filters on it. A
   read with no scope is not a broader query, it is a missing
   authorization boundary.
6. **Owner-controlled writes.** `DomainOwnedStore` refuses a write from a
   domain that does not own the store (`P13-DP-014`).
7. **The adapters are reference implementations, not a data plane.** Not
   concurrency-safe, not durable, not transactional in any sense a
   database would recognise. `ReferenceUnitOfWork` simulates atomicity
   well enough to prove the outbox contract and no further.

**Audit persistence is not here.** PACK-13 defines no audit store: the
chain stays with PACK-02, this package reaches it through
`audit-core`'s own append-only port, and `DataPlaneAuditEventStore` is a
name for that port rather than a re-declaration of it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from epd2_audit_core.storage import AuditEventStore
from epd2_data_plane_service.backfill import BackfillCheckpoint, ReviewQueueEntry
from epd2_data_plane_service.concurrency import (
    AggregateVersion,
    CommandExecutionReference,
    TransactionBoundary,
    UnitOfWorkReference,
)
from epd2_data_plane_service.delivery import ConsumerCheckpoint, DeadLetterRecord
from epd2_data_plane_service.domain import (
    AggregateReference,
    DomainReference,
    OrganizationScopeReference,
)
from epd2_data_plane_service.exceptions import (
    CrossDomainDirectAccessDeniedError,
    GovernedRecordDeletionForbiddenError,
    IdempotencyKeyReusedWithDifferentPayloadError,
    MigrationAlreadyAppliedError,
    RecordNotFoundError,
    SchemaVersionIdentityImmutableError,
)
from epd2_data_plane_service.idempotency import IdempotencyKey, IdempotencyRecord
from epd2_data_plane_service.migrations import AppliedMigration
from epd2_data_plane_service.outbox import OutboxRecord, OutboxStatus
from epd2_data_plane_service.projections import ProjectedRow, ProjectionDefinition
from epd2_data_plane_service.registry import ConsumerRegistration, SchemaVersion

#: Audit Core's append-only event store port, named here so the PACK-13
#: application layer depends on *that* port rather than on a local
#: re-declaration. PACK-13 never defines its own audit store: the hash
#: chain, the conflict detection and the verification stay with PACK-02,
#: and this package holds no mutating control over them
#: (`P13-DP-014a`).
DataPlaneAuditEventStore = AuditEventStore


def delete_data_plane_record(record: object) -> None:
    """The single delete-shaped function in this package, and it refuses.

    Outbox records, applied migrations, schema versions, dead letters and
    projection rows are each material whose disposal is a governed
    decision belonging to PACK-09, reached through its own process. A
    port that offered `delete` would be publishing an act the domain
    forbids and inviting an adapter to implement it
    (`P13-PATH-005`)."""
    raise GovernedRecordDeletionForbiddenError(
        "PACK-13 storage ports carry no delete method; retention and disposal decisions "
        "belong to PACK-09 and reach this material through its own governed process, never "
        "through a storage-level delete"
    )


def _in_scope(record_scope: OrganizationScopeReference, scope: OrganizationScopeReference) -> bool:
    return record_scope.organization_id == scope.organization_id


class DomainOwnedStore:
    """Mixin enforcing owner-controlled writes (`P13-DP-014`).

    Every adapter below is constructed with the domain that owns it, and
    every write goes through `_require_owner`. The check is a comparison
    of domain names rather than an authorization decision: authorization
    is PACK-12's, ownership is the data plane's."""

    def __init__(self, owning_domain: DomainReference) -> None:
        self._owning_domain = owning_domain

    @property
    def owning_domain(self) -> DomainReference:
        return self._owning_domain

    def _require_owner(self, writing_domain: DomainReference, *, what: str) -> None:
        if writing_domain.domain_name != self._owning_domain.domain_name:
            raise CrossDomainDirectAccessDeniedError(
                f"{writing_domain.domain_name!r} attempted to write {what} owned by "
                f"{self._owning_domain.domain_name!r}; only the owner writes"
            )


# ---------------------------------------------------------------------------
# Aggregate versions and command executions
# ---------------------------------------------------------------------------


class AggregateVersionStore(Protocol):
    """Optimistic concurrency state for one domain's aggregates."""

    def current(self, aggregate: AggregateReference) -> AggregateVersion: ...

    def commit(
        self, version: AggregateVersion, *, writing_domain: DomainReference
    ) -> AggregateVersion: ...


class InMemoryAggregateVersionStore(DomainOwnedStore):
    """Reference adapter. Not concurrency-safe: two threads committing
    the same aggregate would both succeed, which a real database's
    conditional update would prevent. That limitation is stated rather
    than papered over — the *contract* this store implements is the
    optimistic-concurrency one, and a production adapter enforces it
    where it can actually be enforced."""

    def __init__(self, owning_domain: DomainReference) -> None:
        super().__init__(owning_domain)
        self._versions: dict[tuple[str, UUID], int] = {}

    def current(self, aggregate: AggregateReference) -> AggregateVersion:
        key = (aggregate.aggregate_type, aggregate.aggregate_id)
        return AggregateVersion(aggregate=aggregate, version=self._versions.get(key, 0))

    def commit(
        self, version: AggregateVersion, *, writing_domain: DomainReference
    ) -> AggregateVersion:
        self._require_owner(writing_domain, what=version.aggregate.aggregate_type)
        key = (version.aggregate.aggregate_type, version.aggregate.aggregate_id)
        self._versions[key] = version.version
        return version


class CommandExecutionStore(Protocol):
    def append(self, execution: CommandExecutionReference) -> None: ...

    def by_id(self, command_execution_id: UUID) -> CommandExecutionReference: ...

    def list_for_scope(
        self, *, scope: OrganizationScopeReference
    ) -> tuple[CommandExecutionReference, ...]: ...


class InMemoryCommandExecutionStore:
    def __init__(self) -> None:
        self._executions: dict[UUID, CommandExecutionReference] = {}

    def append(self, execution: CommandExecutionReference) -> None:
        self._executions[execution.command_execution_id] = execution

    def by_id(self, command_execution_id: UUID) -> CommandExecutionReference:
        found = self._executions.get(command_execution_id)
        if found is None:
            raise RecordNotFoundError(f"no command execution {command_execution_id}")
        return found

    def list_for_scope(
        self, *, scope: OrganizationScopeReference
    ) -> tuple[CommandExecutionReference, ...]:
        return tuple(e for e in self._executions.values() if _in_scope(e.scope, scope))


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class IdempotencyStore(Protocol):
    def find(self, key: IdempotencyKey) -> IdempotencyRecord | None: ...

    def put(self, record: IdempotencyRecord) -> None: ...


class InMemoryIdempotencyStore:
    """Stores the request digest, never the request (`P13-IDEM-008`) —
    guaranteed by `IdempotencyRecord` itself, which has no field for
    one."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def find(self, key: IdempotencyKey) -> IdempotencyRecord | None:
        return self._records.get(key.qualified_key)

    def put(self, record: IdempotencyRecord) -> None:
        existing = self._records.get(record.key.qualified_key)
        if existing is not None and existing.request_digest != record.request_digest:
            raise IdempotencyKeyReusedWithDifferentPayloadError(
                f"idempotency key {record.key.qualified_key} is already recorded with a "
                f"different request digest"
            )
        self._records[record.key.qualified_key] = record


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------


class OutboxStore(Protocol):
    def append(self, record: OutboxRecord, *, writing_domain: DomainReference) -> None: ...

    def update_delivery_state(self, record: OutboxRecord) -> None: ...

    def by_id(self, outbox_record_id: UUID) -> OutboxRecord: ...

    def pending(self, *, scope: OrganizationScopeReference) -> tuple[OutboxRecord, ...]: ...


class InMemoryOutboxStore(DomainOwnedStore):
    """The outbox is **co-located with its domain** (ADR-070).

    A central outbox table written by every domain is precisely the
    shared mutable table the ownership ADR forbids, so this adapter is
    constructed per owning domain and refuses another's writes."""

    def __init__(self, owning_domain: DomainReference) -> None:
        super().__init__(owning_domain)
        self._records: dict[UUID, OutboxRecord] = {}

    def append(self, record: OutboxRecord, *, writing_domain: DomainReference) -> None:
        self._require_owner(writing_domain, what="an outbox record")
        if record.outbox_record_id in self._records:
            raise IdempotencyKeyReusedWithDifferentPayloadError(
                f"outbox record {record.outbox_record_id} already exists; a republication "
                f"reuses the record and its logical event ID rather than appending a second"
            )
        self._records[record.outbox_record_id] = record

    def update_delivery_state(self, record: OutboxRecord) -> None:
        """Replace a record, refusing any change outside delivery
        metadata (`P13-OBX-003`).

        The four immutable facts are checked explicitly rather than by
        comparing whole objects, so the error message can say which one
        changed."""
        existing = self._records.get(record.outbox_record_id)
        if existing is None:
            raise RecordNotFoundError(f"no outbox record {record.outbox_record_id}")
        for attribute in ("event_id", "event_type", "event_version", "sequence_number"):
            if getattr(existing, attribute) != getattr(record, attribute):
                raise SchemaVersionIdentityImmutableError(
                    f"outbox record {record.outbox_record_id}: {attribute} is immutable after "
                    f"commit; only delivery metadata changes"
                )
        if existing.envelope.integrity.payload_hash != record.envelope.integrity.payload_hash:
            raise SchemaVersionIdentityImmutableError(
                f"outbox record {record.outbox_record_id}: the event payload is immutable "
                f"after commit"
            )
        self._records[record.outbox_record_id] = record

    def by_id(self, outbox_record_id: UUID) -> OutboxRecord:
        found = self._records.get(outbox_record_id)
        if found is None:
            raise RecordNotFoundError(f"no outbox record {outbox_record_id}")
        return found

    def pending(self, *, scope: OrganizationScopeReference) -> tuple[OutboxRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._records.values()
                    if record.status is OutboxStatus.PENDING and _in_scope(record.scope, scope)
                ),
                key=lambda record: record.sequence_number,
            )
        )

    def all_for_scope(self, *, scope: OrganizationScopeReference) -> tuple[OutboxRecord, ...]:
        return tuple(
            sorted(
                (r for r in self._records.values() if _in_scope(r.scope, scope)),
                key=lambda r: r.sequence_number,
            )
        )


# ---------------------------------------------------------------------------
# Reference unit of work
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommittedWork:
    """What one unit of work committed: the new aggregate version and the
    outbox record written with it, atomically."""

    version: AggregateVersion
    outbox_record: OutboxRecord


class ReferenceUnitOfWork:
    """An in-process simulation of `P13-TX-003`'s atomicity.

    Deliberately minimal. It buffers the state change and the outbox
    record and applies both on `commit`, or neither on `rollback`. That
    is enough to make the outbox contract testable and is emphatically
    **not** a transaction: there is no isolation, no durability and no
    recovery. A production adapter gets those from the database, which is
    the only place they can come from.
    """

    def __init__(
        self,
        reference: UnitOfWorkReference,
        *,
        versions: InMemoryAggregateVersionStore,
        outbox: InMemoryOutboxStore,
    ) -> None:
        self._reference = reference
        self._versions = versions
        self._outbox = outbox
        self._pending: CommittedWork | None = None
        self._committed = False
        self._rolled_back = False

    @property
    def reference(self) -> UnitOfWorkReference:
        return self._reference

    @property
    def boundary(self) -> TransactionBoundary:
        return self._reference.boundary

    def stage(self, work: CommittedWork) -> None:
        """Buffer the state change and its outbox record together.

        They are staged as one object rather than two calls, because two
        calls is exactly the shape in which one of them gets
        forgotten."""
        if self._committed or self._rolled_back:
            raise ValueError("this unit of work has already ended")
        self._reference.assert_same_domain(work.version.aggregate)
        self._pending = work

    def commit(self) -> CommittedWork:
        """Apply both, or neither. There is no branch here that applies
        one without the other."""
        if self._rolled_back:
            raise ValueError("this unit of work was rolled back")
        if self._pending is None:
            raise ValueError("nothing staged to commit")
        work = self._pending
        self._versions.commit(work.version, writing_domain=self.boundary.owning_domain)
        self._outbox.append(work.outbox_record, writing_domain=self.boundary.owning_domain)
        self._committed = True
        return work

    def rollback(self) -> None:
        """Discard the staged work. A rolled-back transaction leaves
        **no published event** (`P13-TX-005`) — and here, no outbox
        record at all, which is the stronger and simpler guarantee."""
        self._pending = None
        self._rolled_back = True

    @property
    def committed(self) -> bool:
        return self._committed


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------


class SchemaVersionStore(Protocol):
    def append(self, version: SchemaVersion) -> None: ...

    def update_state(self, version: SchemaVersion) -> None: ...

    def by_id(self, schema_version_id: UUID) -> SchemaVersion: ...

    def by_family(self, family_id: UUID) -> tuple[SchemaVersion, ...]: ...


class InMemorySchemaVersionStore:
    """Append-only for identity, mutable only for lifecycle.

    `append` refuses a second version with an existing ID
    (`P13-REG-005g`); `update_state` refuses any change to the digest or
    the family, so a lifecycle transition can never quietly become a
    content replacement."""

    def __init__(self) -> None:
        self._versions: dict[UUID, SchemaVersion] = {}

    def append(self, version: SchemaVersion) -> None:
        if version.schema_version_id in self._versions:
            raise SchemaVersionIdentityImmutableError(
                f"schema version {version.schema_version_id} already exists; a later "
                f"publication does not merge into, replace or re-point an earlier version"
            )
        self._versions[version.schema_version_id] = version

    def update_state(self, version: SchemaVersion) -> None:
        existing = self._versions.get(version.schema_version_id)
        if existing is None:
            raise RecordNotFoundError(f"no schema version {version.schema_version_id}")
        if existing.content_digest != version.content_digest:
            raise SchemaVersionIdentityImmutableError(
                f"schema version {version.schema_version_id}: the content digest is immutable; "
                f"a changed digest is a new version with its own publication decision"
            )
        if existing.family.family_id != version.family.family_id:
            raise SchemaVersionIdentityImmutableError(
                f"schema version {version.schema_version_id}: a version does not move between "
                f"families"
            )
        self._versions[version.schema_version_id] = version

    def by_id(self, schema_version_id: UUID) -> SchemaVersion:
        found = self._versions.get(schema_version_id)
        if found is None:
            raise RecordNotFoundError(f"no schema version {schema_version_id}")
        return found

    def by_family(self, family_id: UUID) -> tuple[SchemaVersion, ...]:
        return tuple(
            sorted(
                (v for v in self._versions.values() if v.family.family_id == family_id),
                key=lambda v: v.version_label,
            )
        )


class ConsumerRegistrationStore(Protocol):
    def register(self, registration: ConsumerRegistration) -> None: ...

    def for_family(self, family_id: UUID) -> tuple[ConsumerRegistration, ...]: ...


class InMemoryConsumerRegistrationStore:
    def __init__(self) -> None:
        self._registrations: dict[UUID, ConsumerRegistration] = {}

    def register(self, registration: ConsumerRegistration) -> None:
        self._registrations[registration.consumer_id] = registration

    def for_family(self, family_id: UUID) -> tuple[ConsumerRegistration, ...]:
        return tuple(
            sorted(
                (r for r in self._registrations.values() if r.family_id == family_id),
                key=lambda r: r.consumer_name,
            )
        )


# ---------------------------------------------------------------------------
# Migration metadata
# ---------------------------------------------------------------------------


class AppliedMigrationStore(Protocol):
    def append(self, applied: AppliedMigration) -> None: ...

    def find(self, migration_id: str) -> AppliedMigration | None: ...

    def all_applied(self) -> tuple[AppliedMigration, ...]: ...


class InMemoryAppliedMigrationStore:
    """Migration metadata storage, append-only.

    `append` refuses to replace an applied record, which is
    `P13-MIG-001`'s immutability at the storage layer: an edit to an
    applied migration is impossible here rather than merely
    discouraged."""

    def __init__(self) -> None:
        self._applied: dict[str, AppliedMigration] = {}

    def append(self, applied: AppliedMigration) -> None:
        existing = self._applied.get(applied.migration_id)
        if existing is not None:
            raise MigrationAlreadyAppliedError(
                f"migration {applied.migration_id} was applied at "
                f"{existing.applied_at.isoformat()} and its record is immutable; a correction "
                f"is a new migration"
            )
        self._applied[applied.migration_id] = applied

    def find(self, migration_id: str) -> AppliedMigration | None:
        return self._applied.get(migration_id)

    def all_applied(self) -> tuple[AppliedMigration, ...]:
        return tuple(sorted(self._applied.values(), key=lambda a: a.ordering_position))


class BackfillCheckpointStore(Protocol):
    def save(self, checkpoint: BackfillCheckpoint) -> None: ...

    def latest(self, backfill_id: UUID) -> BackfillCheckpoint | None: ...

    def review_queue(self, backfill_id: UUID) -> tuple[ReviewQueueEntry, ...]: ...

    def enqueue_for_review(
        self, backfill_id: UUID, entries: Sequence[ReviewQueueEntry]
    ) -> None: ...


class InMemoryBackfillCheckpointStore:
    def __init__(self) -> None:
        self._checkpoints: dict[UUID, BackfillCheckpoint] = {}
        self._review: dict[UUID, list[ReviewQueueEntry]] = {}

    def save(self, checkpoint: BackfillCheckpoint) -> None:
        self._checkpoints[checkpoint.backfill_id] = checkpoint

    def latest(self, backfill_id: UUID) -> BackfillCheckpoint | None:
        return self._checkpoints.get(backfill_id)

    def review_queue(self, backfill_id: UUID) -> tuple[ReviewQueueEntry, ...]:
        return tuple(self._review.get(backfill_id, ()))

    def enqueue_for_review(self, backfill_id: UUID, entries: Sequence[ReviewQueueEntry]) -> None:
        self._review.setdefault(backfill_id, []).extend(entries)


# ---------------------------------------------------------------------------
# Delivery state
# ---------------------------------------------------------------------------


class ConsumerCheckpointStore(Protocol):
    def save(self, checkpoint: ConsumerCheckpoint) -> None: ...

    def latest(self, *, consumer_name: str, ordering_scope_key: str) -> ConsumerCheckpoint: ...


class InMemoryConsumerCheckpointStore:
    def __init__(self) -> None:
        self._checkpoints: dict[tuple[str, str], ConsumerCheckpoint] = {}

    def save(self, checkpoint: ConsumerCheckpoint) -> None:
        self._checkpoints[(checkpoint.consumer_name, checkpoint.ordering_scope_key)] = checkpoint

    def latest(self, *, consumer_name: str, ordering_scope_key: str) -> ConsumerCheckpoint:
        found = self._checkpoints.get((consumer_name, ordering_scope_key))
        if found is None:
            raise RecordNotFoundError(
                f"no checkpoint for consumer {consumer_name!r} in scope {ordering_scope_key!r}"
            )
        return found


class DeadLetterStore(Protocol):
    """A classified, access-controlled store with a review obligation
    (`P13-DEL-014`).

    The port exposes no bulk read: every read is by identifier and every
    listing is scoped, because a dead-letter store may contain personal
    data and is excluded from general operator visibility."""

    def append(self, record: DeadLetterRecord) -> None: ...

    def by_id(self, dead_letter_id: UUID) -> DeadLetterRecord: ...

    def awaiting_review(self) -> tuple[UUID, ...]: ...


class InMemoryDeadLetterStore:
    def __init__(self) -> None:
        self._records: dict[UUID, DeadLetterRecord] = {}

    def append(self, record: DeadLetterRecord) -> None:
        self._records[record.dead_letter_id] = record

    def by_id(self, dead_letter_id: UUID) -> DeadLetterRecord:
        found = self._records.get(dead_letter_id)
        if found is None:
            raise RecordNotFoundError(f"no dead-letter record {dead_letter_id}")
        return found

    def awaiting_review(self) -> tuple[UUID, ...]:
        """Identifiers only.

        Returning records would hand an operator surface the classified
        contents of every failure; the review path fetches one record at
        a time, under PACK-12."""
        return tuple(sorted(r.dead_letter_id for r in self._records.values() if r.review_required))


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------


class ProjectionStore(Protocol):
    def declare(self, definition: ProjectionDefinition) -> None: ...

    def upsert_row(self, row: ProjectedRow) -> None: ...

    def rows(
        self, projection_id: UUID, *, scope: OrganizationScopeReference
    ) -> tuple[ProjectedRow, ...]: ...

    def tombstone_row(self, projection_id: UUID, row_key: str) -> None: ...


class InMemoryProjectionStore:
    """A projection store whose "delete" is a tombstone.

    `tombstone_row` removes the row's values and records that something
    was there — which is what `P13-RET-003` means by a tombstone, and
    what makes deletion propagation visible rather than silent. It is not
    named `delete` because it is not one, and because
    `P13-PATH-005` forbids a storage port acquiring a delete method."""

    def __init__(self) -> None:
        self._definitions: dict[UUID, ProjectionDefinition] = {}
        self._rows: dict[tuple[UUID, str], ProjectedRow] = {}
        self._tombstoned: set[tuple[UUID, str]] = set()

    def declare(self, definition: ProjectionDefinition) -> None:
        self._definitions[definition.projection_id] = definition

    def definition(self, projection_id: UUID) -> ProjectionDefinition:
        found = self._definitions.get(projection_id)
        if found is None:
            raise RecordNotFoundError(f"no projection {projection_id}")
        return found

    def upsert_row(self, row: ProjectedRow) -> None:
        if (row.projection_id, row.row_key) in self._tombstoned:
            raise GovernedRecordDeletionForbiddenError(
                f"projection row {row.row_key!r} was tombstoned; re-creating it would "
                f"resurrect a deleted source record"
            )
        self._rows[(row.projection_id, row.row_key)] = row

    def rows(
        self, projection_id: UUID, *, scope: OrganizationScopeReference
    ) -> tuple[ProjectedRow, ...]:
        return tuple(
            sorted(
                (
                    row
                    for (pid, _), row in self._rows.items()
                    if pid == projection_id and _in_scope(row.scope, scope)
                ),
                key=lambda row: row.row_key,
            )
        )

    def tombstone_row(self, projection_id: UUID, row_key: str) -> None:
        self._rows.pop((projection_id, row_key), None)
        self._tombstoned.add((projection_id, row_key))

    def is_tombstoned(self, projection_id: UUID, row_key: str) -> bool:
        return (projection_id, row_key) in self._tombstoned
