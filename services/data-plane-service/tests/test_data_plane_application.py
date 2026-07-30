"""The governed data-plane commands, end to end (PACK-13).

Named `test_data_plane_application.py` rather than `test_application.py`
deliberately. `services/document-service/tests/test_privacy_boundary.py`
imports a helper with `from test_application import Flow` — a bare
module-name import that resolves through `sys.path`, and a second
`test_application` module collected earlier in directory order would
shadow the one it means. Renaming here is the change that touches no
earlier pack.

Command execution with concurrency, idempotency and the atomic outbox
commit; the schema publication path; migration execution under a scoped
grant; the backfill service; dispatch and consumption; projection
updates and deletion propagation; and the audit ingestion contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import timedelta
from uuid import UUID

import pytest
from _data_plane_builders import (
    NOW,
    OWNER_DOMAIN,
    actor,
    aggregate,
    classification,
    clean_assessment,
    definition,
    evidence,
    family,
    grant,
    human_verdict,
    idempotency_key,
    migration_definition,
    migration_plan,
    passing_gates,
    record_class,
    retention,
    scope,
    uid,
    unit_reference,
)

from epd2_data_plane_service.application import (
    AUDIT_POLICY_VERSION,
    BackfillService,
    DataPlaneCommandService,
    DeliveryService,
    DomainCommandRequest,
    DomainCommandResult,
    MigrationService,
    ProjectionService,
    SchemaPublicationRequest,
    SchemaRegistryService,
    audit_classification_for,
    submit_audit_record,
)
from epd2_data_plane_service.backfill import (
    BackfillPlan,
    BackfillRunner,
    BackfillSourceRecord,
)
from epd2_data_plane_service.boundaries import AuditSubmission
from epd2_data_plane_service.compatibility import CompatibilityAssessment, SemanticRiskClass
from epd2_data_plane_service.concurrency import ExpectedVersion
from epd2_data_plane_service.delivery import (
    ConsumerCheckpoint,
    ConsumerEffect,
    ReferenceBroker,
    ReferenceConsumer,
    ReferenceDispatcher,
    RetryPolicy,
)
from epd2_data_plane_service.exceptions import (
    ConcurrencyLastWriteWinsProhibitedError,
    ConcurrencyStaleAggregateVersionError,
    ConsumerNotReadyError,
    IdempotencyKeyReusedWithDifferentPayloadError,
    MigrationGlobalIdentifierProhibitedError,
    PrivilegeAuthorityMissingError,
    SchemaDuplicateContentError,
    SchemaExamplesInvalidError,
    SchemaRegistryUnavailableError,
    SemanticReviewRequiredError,
)
from epd2_data_plane_service.migrations import MigrationClass
from epd2_data_plane_service.outbox import DestinationReference
from epd2_data_plane_service.projections import (
    AuthorizationTier,
    DeletionTombstone,
    ProjectedRow,
    ProjectionDefinition,
    ProjectionHealth,
    ProjectionSource,
    RebuildStrategy,
)
from epd2_data_plane_service.registry import (
    ConsumerRegistration,
    RegistryAvailability,
)
from epd2_data_plane_service.retention import (
    DeletionDecision,
    InfrastructurePersistentClass,
    LegalHoldObservation,
    LegalHoldState,
    RetentionBinding,
)
from epd2_data_plane_service.storage import (
    InMemoryAggregateVersionStore,
    InMemoryAppliedMigrationStore,
    InMemoryBackfillCheckpointStore,
    InMemoryConsumerRegistrationStore,
    InMemoryIdempotencyStore,
    InMemoryOutboxStore,
    InMemoryProjectionStore,
    InMemorySchemaVersionStore,
)

AVAILABLE = RegistryAvailability(reachable=True, checked_at=NOW)


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------


def _command_service() -> tuple[
    DataPlaneCommandService, InMemoryAggregateVersionStore, InMemoryOutboxStore
]:
    versions = InMemoryAggregateVersionStore(OWNER_DOMAIN)
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    service = DataPlaneCommandService(
        owning_domain=OWNER_DOMAIN,
        versions=versions,
        outbox=outbox,
        idempotency_store=InMemoryIdempotencyStore(),
    )
    return service, versions, outbox


def _request(
    *,
    key_value: str = "req-1",
    payload: dict[str, object] | None = None,
    expected: ExpectedVersion | None = None,
    consequential: bool = True,
) -> DomainCommandRequest:
    return DomainCommandRequest(
        command_name="record_membership",
        aggregate=aggregate(),
        actor=actor(),
        scope=scope(),
        expected_version=expected or ExpectedVersion.must_not_exist(),
        idempotency_key=idempotency_key(key_value),
        request_payload=payload or {"status": "active"},
        event_type="projection.updated",
        event_payload={"projection_id": str(uid(1)), "position": 1},
        consequential=consequential,
    )


def _execute(
    service: DataPlaneCommandService,
    request: DomainCommandRequest,
    *,
    n: int = 1,
    **kw: object,
) -> DomainCommandResult:
    return service.execute(
        request,
        unit_reference=unit_reference(),
        outbox_record_id=uid(20000 + n),
        event_id=uid(21000 + n),
        correlation_id=uid(22000 + n),
        command_execution_id=uid(23000 + n),
        now=NOW,
        retention_schedule=retention(),
        **kw,  # type: ignore[arg-type]
    )


def test_a_command_commits_state_and_its_outbox_record_together() -> None:
    service, versions, outbox = _command_service()
    result = _execute(service, _request())
    assert result.committed is not None
    assert versions.current(aggregate()).version == 1
    assert outbox.by_id(uid(20001)).event_id == uid(21001)
    assert result.execution.resulting_version == 1


def test_a_rolled_back_command_leaves_no_version_and_no_event() -> None:
    service, versions, outbox = _command_service()
    result = _execute(service, _request(), rollback=True)
    assert result.committed is None
    assert versions.current(aggregate()).version == 0
    assert outbox.pending(scope=scope()) == ()


def test_a_replayed_command_returns_the_first_result_without_re_executing() -> None:
    service, versions, _ = _command_service()
    _execute(service, _request())
    replay = _execute(service, _request(expected=ExpectedVersion.exact(1)), n=2)
    assert replay.replayed
    assert replay.committed is None
    assert versions.current(aggregate()).version == 1


def test_the_same_key_with_a_different_payload_conflicts() -> None:
    service, _, _ = _command_service()
    _execute(service, _request())
    with pytest.raises(IdempotencyKeyReusedWithDifferentPayloadError):
        _execute(service, _request(payload={"status": "suspended"}), n=2)


def test_a_stale_expected_version_is_refused_before_anything_is_written() -> None:
    service, versions, outbox = _command_service()
    _execute(service, _request())
    with pytest.raises(ConcurrencyStaleAggregateVersionError):
        _execute(
            service,
            _request(key_value="req-2", expected=ExpectedVersion.exact(7)),
            n=2,
        )
    assert versions.current(aggregate()).version == 1
    assert len(outbox.all_for_scope(scope=scope())) == 1


def test_a_consequential_command_may_not_assert_only_any_existing_version() -> None:
    """`P13-CC-003`: that is last-write-wins wearing an expected-version
    parameter."""
    service, _, _ = _command_service()
    _execute(service, _request())
    with pytest.raises(ConcurrencyLastWriteWinsProhibitedError):
        _execute(
            service,
            _request(key_value="req-3", expected=ExpectedVersion.any_existing()),
            n=3,
        )


def test_a_non_consequential_command_may_assert_any_existing_version() -> None:
    service, _, _ = _command_service()
    _execute(service, _request())
    result = _execute(
        service,
        _request(key_value="req-4", expected=ExpectedVersion.any_existing(), consequential=False),
        n=4,
    )
    assert result.committed is not None


def test_the_command_execution_reference_links_idempotency_and_version() -> None:
    service, _, _ = _command_service()
    result = _execute(service, _request())
    assert result.execution.idempotency_key_digest == idempotency_key("req-1").digest
    assert result.execution.command_name == "record_membership"


# ---------------------------------------------------------------------------
# Audit ingestion
# ---------------------------------------------------------------------------


class _RecordingAuditPort:
    """A double for `audit-core`'s ingestion port.

    It records what it was handed and returns an acknowledgement — which
    is exactly what a submission contract offers: no chain position, no
    previous hash, no sequence number."""

    def __init__(self) -> None:
        self.submissions: list[AuditSubmission] = []

    def submit(self, submission: AuditSubmission) -> UUID:
        self.submissions.append(submission)
        return uid(24000)


def test_a_domain_submits_an_audit_record_through_the_governed_port() -> None:
    port = _RecordingAuditPort()
    submission = AuditSubmission(
        submission_id=uid(24001),
        submitting_domain=OWNER_DOMAIN,
        actor=actor(),
        scope=scope(),
        action="membership.recorded",
        reason_code="PROJECTION_UPDATED_RECORDED",
        submitted_at=NOW,
        payload={"aggregate_id": str(uid(1))},
    )
    assert submit_audit_record(port, submission) == uid(24000)
    assert port.submissions == [submission]


def test_an_audit_record_arriving_outside_the_port_is_refused() -> None:
    from epd2_data_plane_service.exceptions import AuditIngestionContractRequiredError

    port = _RecordingAuditPort()
    submission = AuditSubmission(
        submission_id=uid(24002),
        submitting_domain=OWNER_DOMAIN,
        actor=actor(),
        scope=scope(),
        action="membership.recorded",
        reason_code="PROJECTION_UPDATED_RECORDED",
        submitted_at=NOW,
        payload={},
    )
    with pytest.raises(AuditIngestionContractRequiredError):
        submit_audit_record(port, submission, arrived_via_port=False)
    assert port.submissions == []


def test_the_audit_classification_for_a_successful_act_is_registered() -> None:
    assert audit_classification_for("projection.updated") == "PROJECTION_UPDATED_RECORDED"
    assert AUDIT_POLICY_VERSION.startswith("pack-13-")


# ---------------------------------------------------------------------------
# Schema publication
# ---------------------------------------------------------------------------


def _registry() -> tuple[SchemaRegistryService, InMemorySchemaVersionStore]:
    versions = InMemorySchemaVersionStore()
    return (
        SchemaRegistryService(versions=versions, consumers=InMemoryConsumerRegistrationStore()),
        versions,
    )


def _publication(
    *,
    n: int = 1,
    assessment: CompatibilityAssessment | None = None,
    intentional: bool = False,
    justification: str | None = None,
    fixtures: Sequence[Mapping[str, object]] | None = None,
) -> SchemaPublicationRequest:
    return SchemaPublicationRequest(
        schema_version_id=uid(25000 + n),
        definition=definition(examples=fixtures),
        version_label=f"1.{n}.0",
        classification=classification(),
        proposed_by=actor(1),
        approved_by=actor(2),
        assessment=assessment or clean_assessment(),
        evidence=evidence(),
        intentional_republication=intentional,
        governance_justification=justification,
    )


def test_a_clean_publication_records_its_decision_and_validation() -> None:
    service, versions = _registry()
    result = service.publish(_publication(), now=NOW, availability=AVAILABLE)
    assert result.version.publication_decision_id == uid(25001)
    assert result.validation.all_examples_valid
    assert versions.by_id(uid(25001)).content_digest == result.version.content_digest


def test_publication_is_blocked_while_the_registry_is_unreachable() -> None:
    service, _ = _registry()
    unavailable = RegistryAvailability(
        reachable=False, checked_at=NOW, unreachable_reason_code="SCHEMA_REGISTRY_UNAVAILABLE"
    )
    with pytest.raises(SchemaRegistryUnavailableError):
        service.publish(_publication(), now=NOW, availability=unavailable)


def test_a_schema_whose_own_examples_fail_is_not_publishable() -> None:
    service, _ = _registry()
    with pytest.raises(SchemaExamplesInvalidError):
        service.publish(
            _publication(fixtures=[{"membership_id": "not-a-uuid"}]),
            now=NOW,
            availability=AVAILABLE,
        )


def test_accidental_republication_of_identical_content_is_blocked() -> None:
    service, _ = _registry()
    service.publish(_publication(), now=NOW, availability=AVAILABLE)
    with pytest.raises(SchemaDuplicateContentError):
        service.publish(_publication(n=2), now=NOW, availability=AVAILABLE)


def test_justified_republication_of_identical_content_is_admitted() -> None:
    service, _ = _registry()
    service.publish(_publication(), now=NOW, availability=AVAILABLE)
    result = service.publish(
        _publication(
            n=2, intentional=True, justification="re-issued under a corrected ownership assignment"
        ),
        now=NOW,
        availability=AVAILABLE,
    )
    assert result.duplicate_assessment is not None
    assert result.duplicate_assessment.admits_publication
    assert result.version.governance_justification


def test_a_semantic_risk_class_blocks_publication_until_reviewed() -> None:
    service, _ = _registry()
    with pytest.raises(SemanticReviewRequiredError):
        service.publish(
            _publication(
                assessment=clean_assessment(
                    risks=frozenset({SemanticRiskClass.ENUM_MEANING_CHANGE})
                )
            ),
            now=NOW,
            availability=AVAILABLE,
        )


def test_a_reviewed_semantic_risk_publishes() -> None:
    service, _ = _registry()
    result = service.publish(
        _publication(
            assessment=clean_assessment(
                risks=frozenset({SemanticRiskClass.ENUM_MEANING_CHANGE}), human=human_verdict()
            )
        ),
        now=NOW,
        availability=AVAILABLE,
    )
    assert result.version.schema_version_id == uid(25001)


def test_activation_requires_a_scoped_grant() -> None:
    service, _ = _registry()
    service.publish(_publication(), now=NOW, availability=AVAILABLE)
    with pytest.raises(PrivilegeAuthorityMissingError):
        service.activate(uid(25001), effective_at=NOW, grant=None, scope=scope(), now=NOW)


def test_activation_under_a_grant_moves_the_version_and_dates_it() -> None:
    service, _ = _registry()
    service.publish(_publication(), now=NOW, availability=AVAILABLE)
    activated = service.activate(
        uid(25001),
        effective_at=NOW + timedelta(days=1),
        grant=grant("schema_activation"),
        scope=scope(),
        now=NOW,
    )
    assert activated.effective_at == NOW + timedelta(days=1)


def test_consumer_readiness_blocks_retirement_until_every_consumer_migrates() -> None:
    service, _ = _registry()
    fam = family()
    service.register_consumer(
        ConsumerRegistration(
            consumer_id=uid(26000),
            consumer_name="lagging",
            consumer_domain=OWNER_DOMAIN,
            family_id=fam.family_id,
            supported_version_ids=(uid(1),),
            registered_at=NOW,
        )
    )
    with pytest.raises(ConsumerNotReadyError):
        service.require_consumers_ready(family_id=fam.family_id, target_version_id=uid(2))


def test_readiness_passes_once_the_consumer_has_migrated() -> None:
    service, _ = _registry()
    fam = family()
    service.register_consumer(
        ConsumerRegistration(
            consumer_id=uid(26001),
            consumer_name="ready",
            consumer_domain=OWNER_DOMAIN,
            family_id=fam.family_id,
            supported_version_ids=(uid(2),),
            registered_at=NOW,
            migrated_to_version_id=uid(2),
        )
    )
    service.require_consumers_ready(family_id=fam.family_id, target_version_id=uid(2))


# ---------------------------------------------------------------------------
# Migration execution
# ---------------------------------------------------------------------------


def test_a_migration_runs_under_a_scoped_grant_and_records_applied_state() -> None:
    store = InMemoryAppliedMigrationStore()
    service = MigrationService(applied_store=store)
    result = service.execute(
        migration_plan(),
        execution_id=uid(27000),
        grant=grant("migration_execution"),
        scope=scope(),
        gates=passing_gates(),
        now=NOW,
    )
    assert len(result.applied) == 1
    assert store.find("0001_add_scope_column") is not None


def test_a_migration_without_a_grant_is_refused() -> None:
    service = MigrationService(applied_store=InMemoryAppliedMigrationStore())
    with pytest.raises(PrivilegeAuthorityMissingError):
        service.execute(
            migration_plan(),
            execution_id=uid(27001),
            grant=None,
            scope=scope(),
            gates=passing_gates(),
            now=NOW,
        )


def test_a_failing_gate_stops_the_migration_before_it_is_recorded() -> None:
    from dataclasses import replace

    store = InMemoryAppliedMigrationStore()
    service = MigrationService(applied_store=store)
    with pytest.raises(MigrationGlobalIdentifierProhibitedError):
        service.execute(
            migration_plan(),
            execution_id=uid(27002),
            grant=grant("migration_execution"),
            scope=scope(),
            gates=replace(passing_gates(), creates_cross_domain_person_key=True),
            now=NOW,
        )
    assert store.all_applied() == ()


def test_a_destructive_plan_needs_its_full_authorization_chain() -> None:
    from epd2_data_plane_service.exceptions import MigrationNotApprovedError

    service = MigrationService(applied_store=InMemoryAppliedMigrationStore())
    plan = migration_plan(
        migration_class=MigrationClass.CONTRACT,
        migrations=(
            migration_definition(
                migration_id="0009_drop_old",
                migration_class=MigrationClass.CONTRACT,
                position=9,
                destructive=True,
            ),
        ),
    )
    with pytest.raises(MigrationNotApprovedError):
        service.execute(
            plan,
            execution_id=uid(27003),
            grant=grant("destructive_migration"),
            scope=scope(),
            gates=passing_gates(),
            now=NOW,
        )


def test_applied_checksums_are_re_verified_without_a_repair_path() -> None:
    store = InMemoryAppliedMigrationStore()
    service = MigrationService(applied_store=store)
    plan = migration_plan()
    service.execute(
        plan,
        execution_id=uid(27004),
        grant=grant("migration_execution"),
        scope=scope(),
        gates=passing_gates(),
        now=NOW,
    )
    service.verify_applied_checksums(plan)


# ---------------------------------------------------------------------------
# Backfill service
# ---------------------------------------------------------------------------


def test_the_backfill_service_persists_its_checkpoint_and_review_queue() -> None:
    plan = BackfillPlan(
        backfill_id=uid(28000),
        target_field="scope_kind",
        required_source_field="organization_kind",
        scope=scope(),
        batch_size=2,
        rate_limit_per_batch=2,
        retention_schedule=retention(),
    )
    checkpoints = InMemoryBackfillCheckpointStore()
    service = BackfillService(checkpoints=checkpoints)
    runner = BackfillRunner(
        plan,
        invariant_check=lambda record, value: True,
        existing_target_value=lambda record: None,
    )
    records = [
        BackfillSourceRecord(
            record_id=uid(28100 + n),
            scope=scope(),
            values=(("organization_kind", "land"),) if n != 2 else (),
        )
        for n in range(1, 4)
    ]
    outcome = service.run(runner, plan, records, now=NOW)
    assert outcome.checkpoint.processed == 3
    assert checkpoints.latest(uid(28000)) is not None
    assert len(checkpoints.review_queue(uid(28000))) == 1

    report = service.reconcile(plan, outcome, evidence=evidence(), now=NOW)
    assert report.processed == 3
    assert report.routed_to_review == 1


def test_a_resumed_backfill_reads_its_persisted_checkpoint() -> None:
    plan = BackfillPlan(
        backfill_id=uid(28001),
        target_field="scope_kind",
        required_source_field="organization_kind",
        scope=scope(),
        batch_size=1,
        rate_limit_per_batch=1,
        retention_schedule=retention(),
    )
    checkpoints = InMemoryBackfillCheckpointStore()
    service = BackfillService(checkpoints=checkpoints)
    runner = BackfillRunner(
        plan,
        invariant_check=lambda record, value: True,
        existing_target_value=lambda record: None,
    )
    records = [
        BackfillSourceRecord(
            record_id=uid(28200 + n), scope=scope(), values=(("organization_kind", "land"),)
        )
        for n in range(1, 4)
    ]
    service.run(runner, plan, records, now=NOW, max_batches=1)
    resumed = service.run(runner, plan, records, now=NOW, resume=True)
    assert resumed.checkpoint.processed == 3
    assert resumed.completed


# ---------------------------------------------------------------------------
# Delivery service
# ---------------------------------------------------------------------------


def test_pending_records_dispatch_in_sequence_and_the_consumer_applies_them() -> None:
    service, _, outbox = _command_service()
    _execute(service, _request())

    delivery = DeliveryService(
        outbox=outbox,
        dispatcher=ReferenceDispatcher(
            ReferenceBroker(),
            destination=DestinationReference(
                destination_id=uid(29000), destination_name="reference-topic"
            ),
            policy=RetryPolicy(max_attempts=3, initial_backoff=timedelta(seconds=5)),
        ),
    )
    results = delivery.dispatch_pending(scope=scope(), now=NOW)
    assert len(results) == 1
    assert results[0].record.acknowledged

    consumer = ReferenceConsumer(
        consumer_name="transparency-projection",
        consumer_domain="transparency-service",
        supported_event_versions=frozenset({"1.0"}),
    )
    checkpoint = ConsumerCheckpoint(
        consumer_name="transparency-projection",
        consumer_domain="transparency-service",
        ordering_scope_key="k",
        position=0,
        updated_at=NOW,
    )
    outcome = DeliveryService.consume(consumer, results[0].record, checkpoint=checkpoint, now=NOW)
    assert outcome.effect is ConsumerEffect.APPLIED


def test_an_unavailable_broker_leaves_the_record_pending_not_lost() -> None:
    service, _, outbox = _command_service()
    _execute(service, _request())
    delivery = DeliveryService(
        outbox=outbox,
        dispatcher=ReferenceDispatcher(
            ReferenceBroker(),
            destination=DestinationReference(
                destination_id=uid(29001), destination_name="reference-topic"
            ),
            policy=RetryPolicy(max_attempts=3, initial_backoff=timedelta(seconds=5)),
        ),
    )
    results = delivery.dispatch_pending(scope=scope(), now=NOW, broker_available=False)
    assert results[0].decision.reason_code == "BROKER_UNAVAILABLE"
    assert len(outbox.pending(scope=scope())) == 1


# ---------------------------------------------------------------------------
# Projection service
# ---------------------------------------------------------------------------


def _projection_definition() -> ProjectionDefinition:
    return ProjectionDefinition(
        projection_id=uid(30000),
        projection_name="membership-overview",
        owner=OWNER_DOMAIN,
        sources=(
            ProjectionSource(
                owning_domain=OWNER_DOMAIN,
                event_families=("membership.recorded",),
                authorization_tier=AuthorizationTier.ORGANIZATION_MEMBER,
            ),
        ),
        schema_version_id=uid(30001),
        rebuild_strategy=RebuildStrategy.FROM_SOURCE_EVENTS,
        max_acceptable_lag_events=5,
    )


def test_measuring_a_projection_produces_a_visible_health_and_band() -> None:
    service = ProjectionService(store=InMemoryProjectionStore())
    definition_ = _projection_definition()
    healthy = service.measure(definition_, events_behind=0, observed_at=NOW)
    assert healthy.health is ProjectionHealth.HEALTHY
    assert healthy.lag.lag_band == "none"

    stale = service.measure(definition_, events_behind=50, observed_at=NOW)
    assert stale.health is ProjectionHealth.STALE
    assert stale.lag.lag_band == "moderate"

    failed = service.measure(definition_, events_behind=0, observed_at=NOW, failed=True)
    assert failed.health is ProjectionHealth.FAILED


def test_a_deletion_propagates_into_the_projection_with_evidence() -> None:
    store = InMemoryProjectionStore()
    service = ProjectionService(store=store)
    definition_ = _projection_definition()
    service.declare(definition_)
    service.apply_row(
        ProjectedRow(
            projection_id=uid(30000),
            row_key="m-1",
            scope=scope(),
            values={"status": "active"},
            source_schema_version_id=uid(30001),
        )
    )
    decision = DeletionDecision(
        record_id=uid(30002),
        binding=RetentionBinding(
            persistent_class=InfrastructurePersistentClass.PROJECTION_ROW,
            record_class=record_class(consequential=False),
            retention_schedule=retention(),
        ),
        hold=LegalHoldObservation(
            record_id=uid(30002),
            state=LegalHoldState.NOT_HELD,
            observed_at=NOW,
            observed_by=actor(),
        ),
        retention_due=True,
    )
    propagation = service.propagate_deletion(
        definition_,
        row_key="m-1",
        decision=decision,
        tombstone=DeletionTombstone(
            tombstone_id=uid(30003),
            source_record_id=uid(30002),
            scope=scope(),
            source_decision_reference=uid(30004),
            applied_at=NOW,
        ),
        evidence=evidence(),
        now=NOW,
    )
    assert propagation.evidence is not None
    assert store.rows(uid(30000), scope=scope()) == ()
    assert store.is_tombstoned(uid(30000), "m-1")


def test_a_held_source_blocks_propagation_and_authorizes_nothing() -> None:
    from epd2_data_plane_service.exceptions import RecordUnderLegalHoldError

    service = ProjectionService(store=InMemoryProjectionStore())
    definition_ = _projection_definition()
    service.declare(definition_)
    decision = DeletionDecision(
        record_id=uid(30005),
        binding=RetentionBinding(
            persistent_class=InfrastructurePersistentClass.PROJECTION_ROW,
            record_class=record_class(consequential=False),
            retention_schedule=retention(),
        ),
        hold=LegalHoldObservation(
            record_id=uid(30005),
            state=LegalHoldState.HELD,
            observed_at=NOW,
            observed_by=actor(),
            hold_reference=uid(30006),
        ),
        retention_due=True,
    )
    with pytest.raises(RecordUnderLegalHoldError):
        service.propagate_deletion(
            definition_,
            row_key="m-1",
            decision=decision,
            tombstone=DeletionTombstone(
                tombstone_id=uid(30007),
                source_record_id=uid(30005),
                scope=scope(),
                source_decision_reference=uid(30008),
                applied_at=NOW,
            ),
            evidence=evidence(),
            now=NOW,
        )
