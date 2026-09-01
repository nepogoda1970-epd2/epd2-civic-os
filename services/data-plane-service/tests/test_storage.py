"""Storage ports and reference adapters (PACK-13 §8, §33).

No delete method on any port; append-only applied migrations and schema
versions; owner-controlled writes; scope-filtered reads; and a tombstone
that is a tombstone rather than a delete wearing a different name.
"""

from __future__ import annotations

import inspect
from typing import Protocol

import pytest
from _data_plane_builders import (
    NOW,
    OTHER_DOMAIN,
    OWNER_DOMAIN,
    actor,
    aggregate,
    classification,
    evidence,
    family,
    idempotency_key,
    outbox_record,
    record_class,
    retention,
    scope,
    uid,
)

from epd2_data_plane_service import storage as storage_module
from epd2_data_plane_service.backfill import BackfillCheckpoint, ReviewQueueEntry
from epd2_data_plane_service.concurrency import CommandExecutionReference
from epd2_data_plane_service.delivery import ConsumerCheckpoint, DeadLetterRecord
from epd2_data_plane_service.domain import (
    OrganizationScopeKind,
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
from epd2_data_plane_service.idempotency import IdempotencyRecord
from epd2_data_plane_service.migrations import AppliedMigration
from epd2_data_plane_service.projections import (
    AuthorizationTier,
    ProjectedRow,
    ProjectionDefinition,
    ProjectionSource,
    RebuildStrategy,
)
from epd2_data_plane_service.registry import (
    ClassificationReference,
    SchemaLifecycleState,
    SchemaVersion,
)
from epd2_data_plane_service.storage import (
    DataPlaneAuditEventStore,
    InMemoryAggregateVersionStore,
    InMemoryAppliedMigrationStore,
    InMemoryBackfillCheckpointStore,
    InMemoryCommandExecutionStore,
    InMemoryConsumerCheckpointStore,
    InMemoryDeadLetterStore,
    InMemoryIdempotencyStore,
    InMemoryOutboxStore,
    InMemoryProjectionStore,
    InMemorySchemaVersionStore,
    delete_data_plane_record,
)

OTHER_SCOPE = OrganizationScopeReference(
    organization_id=uid(9999), scope_kind=OrganizationScopeKind.BUND
)


def _schema_version(*, n: int = 1, digest: str | None = None) -> SchemaVersion:
    return SchemaVersion(
        schema_version_id=uid(11000 + n),
        family=family(),
        version_label=f"1.{n}.0",
        content_digest=digest or ("a" * 64),
        lifecycle_state=SchemaLifecycleState.APPROVED,
        classification=ClassificationReference(classification_id=uid(1), tier="restricted"),
    )


# ---------------------------------------------------------------------------
# No delete method anywhere
# ---------------------------------------------------------------------------


def test_no_port_or_adapter_in_this_module_has_a_delete_method() -> None:
    """`P13-PATH-005`: no storage port acquires a delete method in the
    course of this work."""
    offenders: list[str] = []
    for name, member in vars(storage_module).items():
        if not inspect.isclass(member) or member.__module__ != storage_module.__name__:
            continue
        for attribute in dir(member):
            if attribute.startswith("delete") or attribute in ("remove", "purge", "drop"):
                offenders.append(f"{name}.{attribute}")
    assert offenders == []


def test_the_single_delete_shaped_function_refuses() -> None:
    with pytest.raises(GovernedRecordDeletionForbiddenError, match="carry no delete method"):
        delete_data_plane_record(outbox_record())


def test_pack_13_defines_no_audit_store_of_its_own() -> None:
    """The chain stays with PACK-02; this is a name for that port, not a
    re-declaration of it."""
    from epd2_audit_core.storage import AuditEventStore

    assert DataPlaneAuditEventStore is AuditEventStore
    assert issubclass(DataPlaneAuditEventStore, Protocol)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Aggregate versions and command executions
# ---------------------------------------------------------------------------


def test_an_unknown_aggregate_is_at_version_zero() -> None:
    assert InMemoryAggregateVersionStore(OWNER_DOMAIN).current(aggregate()).version == 0


def test_only_the_owner_commits_a_version() -> None:
    store = InMemoryAggregateVersionStore(OWNER_DOMAIN)
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        store.commit(store.current(aggregate()).next(), writing_domain=OTHER_DOMAIN)


def test_a_committed_version_is_readable() -> None:
    store = InMemoryAggregateVersionStore(OWNER_DOMAIN)
    store.commit(store.current(aggregate()).next(), writing_domain=OWNER_DOMAIN)
    assert store.current(aggregate()).version == 1


def test_command_executions_are_scope_filtered() -> None:
    store = InMemoryCommandExecutionStore()
    execution = CommandExecutionReference(
        command_execution_id=uid(12000),
        command_name="record_membership",
        aggregate=aggregate(),
        actor=actor(),
        scope=scope(),
        idempotency_key_digest="d",
        resulting_version=1,
        executed_at=NOW,
    )
    store.append(execution)
    assert store.list_for_scope(scope=scope()) == (execution,)
    assert store.list_for_scope(scope=OTHER_SCOPE) == ()


def test_an_unknown_command_execution_is_not_found() -> None:
    with pytest.raises(RecordNotFoundError):
        InMemoryCommandExecutionStore().by_id(uid(1))


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def _idempotency_record(digest: str) -> IdempotencyRecord:
    from datetime import timedelta

    return IdempotencyRecord(
        key=idempotency_key(),
        request_digest=digest,
        result_reference=uid(1),
        recorded_at=NOW,
        expires_at=NOW + timedelta(days=1),
    )


def test_an_idempotency_record_round_trips() -> None:
    store = InMemoryIdempotencyStore()
    store.put(_idempotency_record("d1"))
    found = store.find(idempotency_key())
    assert found is not None
    assert found.request_digest == "d1"


def test_the_same_key_with_a_different_digest_is_refused_at_the_store() -> None:
    store = InMemoryIdempotencyStore()
    store.put(_idempotency_record("d1"))
    with pytest.raises(IdempotencyKeyReusedWithDifferentPayloadError):
        store.put(_idempotency_record("d2"))


# ---------------------------------------------------------------------------
# Schema versions
# ---------------------------------------------------------------------------


def test_a_schema_version_identity_cannot_be_appended_twice() -> None:
    store = InMemorySchemaVersionStore()
    store.append(_schema_version())
    with pytest.raises(SchemaVersionIdentityImmutableError, match="already exists"):
        store.append(_schema_version())


def test_a_lifecycle_update_cannot_change_the_digest() -> None:
    from dataclasses import replace

    store = InMemorySchemaVersionStore()
    version = _schema_version()
    store.append(version)
    with pytest.raises(SchemaVersionIdentityImmutableError, match="content digest is immutable"):
        store.update_state(replace(version, content_digest="b" * 64))


def test_a_lifecycle_update_cannot_move_a_version_between_families() -> None:
    from dataclasses import replace

    store = InMemorySchemaVersionStore()
    version = _schema_version()
    store.append(version)
    with pytest.raises(SchemaVersionIdentityImmutableError, match="between"):
        store.update_state(replace(version, family=family(n=2)))


def test_a_lifecycle_transition_is_persisted() -> None:
    store = InMemorySchemaVersionStore()
    version = _schema_version()
    store.append(version)
    store.update_state(version.with_state(SchemaLifecycleState.ACTIVE))
    assert store.by_id(version.schema_version_id).lifecycle_state is SchemaLifecycleState.ACTIVE


def test_versions_are_listed_by_family_in_a_stable_order() -> None:
    store = InMemorySchemaVersionStore()
    store.append(_schema_version(n=2, digest="b" * 64))
    store.append(_schema_version(n=1))
    labels = [v.version_label for v in store.by_family(family().family_id)]
    assert labels == sorted(labels)


# ---------------------------------------------------------------------------
# Applied migrations
# ---------------------------------------------------------------------------


def _applied(migration_id: str = "0001", position: int = 1) -> AppliedMigration:
    return AppliedMigration(
        migration_id=migration_id,
        checksum="c" * 64,
        ordering_position=position,
        applied_at=NOW,
        execution_id=uid(1),
    )


def test_an_applied_migration_record_is_immutable_at_the_storage_layer() -> None:
    """`P13-MIG-001`: an edit to an applied migration is impossible here
    rather than merely discouraged."""
    store = InMemoryAppliedMigrationStore()
    store.append(_applied())
    with pytest.raises(MigrationAlreadyAppliedError, match="immutable"):
        store.append(_applied())


def test_applied_migrations_are_listed_in_ordering_position() -> None:
    store = InMemoryAppliedMigrationStore()
    store.append(_applied("0002", 2))
    store.append(_applied("0001", 1))
    assert [a.migration_id for a in store.all_applied()] == ["0001", "0002"]


def test_an_unapplied_migration_is_absent() -> None:
    assert InMemoryAppliedMigrationStore().find("0001") is None


# ---------------------------------------------------------------------------
# Backfill checkpoints and dead letters
# ---------------------------------------------------------------------------


def test_a_backfill_checkpoint_and_its_review_queue_persist_together() -> None:
    store = InMemoryBackfillCheckpointStore()
    checkpoint = BackfillCheckpoint(
        backfill_id=uid(13000),
        last_processed_index=4,
        processed=5,
        succeeded=4,
        routed_to_review=1,
        failed=0,
        recorded_at=NOW,
    )
    store.save(checkpoint)
    store.enqueue_for_review(
        uid(13000),
        [
            ReviewQueueEntry(
                record_id=uid(1),
                scope=scope(),
                missing_field="organization_kind",
                reason_code="BACKFILL_SOURCE_INCOMPLETE",
            )
        ],
    )
    assert store.latest(uid(13000)) == checkpoint
    assert len(store.review_queue(uid(13000))) == 1


def test_the_dead_letter_store_returns_identifiers_not_records() -> None:
    """`P13-DEL-014`: a dead-letter store may contain personal data and is
    excluded from general operator visibility."""
    store = InMemoryDeadLetterStore()
    record = DeadLetterRecord(
        dead_letter_id=uid(14000),
        event_id=uid(1),
        event_type="projection.updated",
        reason_code="EVENT_POISON_MESSAGE",
        attempt_count=3,
        failed_at=NOW,
        classification=classification(),
        retention_schedule=retention(),
    )
    store.append(record)
    assert store.awaiting_review() == (uid(14000),)
    assert store.by_id(uid(14000)).reason_code == "EVENT_POISON_MESSAGE"


def test_an_unknown_dead_letter_is_not_found() -> None:
    with pytest.raises(RecordNotFoundError):
        InMemoryDeadLetterStore().by_id(uid(1))


def test_a_consumer_checkpoint_round_trips_and_is_keyed_by_scope() -> None:
    store = InMemoryConsumerCheckpointStore()
    checkpoint = ConsumerCheckpoint(
        consumer_name="c",
        consumer_domain="d",
        ordering_scope_key="k",
        position=3,
        updated_at=NOW,
    )
    store.save(checkpoint)
    assert store.latest(consumer_name="c", ordering_scope_key="k").position == 3
    with pytest.raises(RecordNotFoundError):
        store.latest(consumer_name="c", ordering_scope_key="other")


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------


def _definition() -> ProjectionDefinition:
    return ProjectionDefinition(
        projection_id=uid(15000),
        projection_name="membership-overview",
        owner=OWNER_DOMAIN,
        sources=(
            ProjectionSource(
                owning_domain=OWNER_DOMAIN,
                event_families=("membership.recorded",),
                authorization_tier=AuthorizationTier.ORGANIZATION_MEMBER,
            ),
        ),
        schema_version_id=uid(15001),
        rebuild_strategy=RebuildStrategy.FROM_SOURCE_EVENTS,
        max_acceptable_lag_events=5,
    )


def _row(key: str = "m-1", *, row_scope: OrganizationScopeReference | None = None) -> ProjectedRow:
    return ProjectedRow(
        projection_id=uid(15000),
        row_key=key,
        scope=row_scope or scope(),
        values={"status": "active"},
        source_schema_version_id=uid(15001),
    )


def test_projection_rows_are_scope_filtered() -> None:
    store = InMemoryProjectionStore()
    store.declare(_definition())
    store.upsert_row(_row())
    assert len(store.rows(uid(15000), scope=scope())) == 1
    assert store.rows(uid(15000), scope=OTHER_SCOPE) == ()


def test_tombstoning_removes_the_row_and_records_that_it_existed() -> None:
    store = InMemoryProjectionStore()
    store.declare(_definition())
    store.upsert_row(_row())
    store.tombstone_row(uid(15000), "m-1")
    assert store.rows(uid(15000), scope=scope()) == ()
    assert store.is_tombstoned(uid(15000), "m-1")


def test_a_tombstoned_row_cannot_be_resurrected() -> None:
    store = InMemoryProjectionStore()
    store.declare(_definition())
    store.upsert_row(_row())
    store.tombstone_row(uid(15000), "m-1")
    with pytest.raises(GovernedRecordDeletionForbiddenError, match="resurrect"):
        store.upsert_row(_row())


def test_an_undeclared_projection_has_no_definition() -> None:
    with pytest.raises(RecordNotFoundError):
        InMemoryProjectionStore().definition(uid(1))


# ---------------------------------------------------------------------------
# The outbox store's scope filter
# ---------------------------------------------------------------------------


def test_outbox_reads_require_a_scope_and_filter_on_it() -> None:
    store = InMemoryOutboxStore(OWNER_DOMAIN)
    store.append(outbox_record(), writing_domain=OWNER_DOMAIN)
    assert len(store.all_for_scope(scope=scope())) == 1
    assert store.all_for_scope(scope=OTHER_SCOPE) == ()


def test_an_unknown_outbox_record_is_not_found() -> None:
    with pytest.raises(RecordNotFoundError):
        InMemoryOutboxStore(OWNER_DOMAIN).by_id(uid(1))


def test_updating_an_absent_outbox_record_is_not_found() -> None:
    with pytest.raises(RecordNotFoundError):
        InMemoryOutboxStore(OWNER_DOMAIN).update_delivery_state(outbox_record())


def test_the_builders_used_here_produce_consistent_fixtures() -> None:
    assert record_class().consequential
    assert evidence().content_digest
