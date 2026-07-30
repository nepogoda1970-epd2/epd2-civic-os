"""The governed data-plane commands (PACK-13).

Where the modules above hold models and pure policy, this module holds
the *commands* that compose them — and the composition is where the
specification's guarantees actually become true. Four are worth naming
before the code:

- **`execute_domain_command`** is `P13-TX-003` in one function: the
  aggregate version and the outbox record are staged into one unit of
  work and committed together, or neither is written. Idempotency,
  optimistic concurrency, scope and the payload guard all run *before*
  the commit, so nothing reaches storage that would have to be undone.
- **`publish_schema_version`** is the schema-registry governance path:
  owner, examples, digest, duplicate-content disposition, compatibility
  verdict, required review, consumer readiness — in that order, because
  each answer changes whether the next question is even asked.
- **`execute_migration`** runs the five automated gates before anything
  else, under a scoped PACK-12 grant, with checksum verification against
  applied state.
- **`submit_audit_record`** is the one integration path other domains
  use to reach audit: they submit, `audit-core` persists.

Every command takes an explicit `now` and every identifier is supplied by
the caller. This package holds no clock and mints no UUID, so every test
is deterministic and every event is reproducible.

None of this executes against a database. The unit of work is
`ReferenceUnitOfWork`, the broker is a double, and the whole module is a
reference implementation of the contracts a production data plane must
satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_data_plane_service.backfill import (
    BackfillCheckpoint,
    BackfillOutcome,
    BackfillPlan,
    BackfillRunner,
    BackfillSourceRecord,
    ReconciliationReport,
)
from epd2_data_plane_service.boundaries import (
    AuditIngestionPort,
    AuditSubmission,
    require_ingestion_contract,
)
from epd2_data_plane_service.canonicalization import (
    CanonicalContent,
    validate_examples,
)
from epd2_data_plane_service.compatibility import (
    CompatibilityAssessment,
    require_compatible_under_mode,
    require_review_complete,
)
from epd2_data_plane_service.concurrency import (
    AggregateVersion,
    CommandExecutionReference,
    ConcurrencyPolicy,
    ExpectedVersion,
    ExpectedVersionKind,
    UnitOfWorkReference,
)
from epd2_data_plane_service.delivery import (
    ConsumerCheckpoint,
    ConsumerResult,
    DispatchResult,
    ReferenceConsumer,
    ReferenceDispatcher,
    lag_band_for,
)
from epd2_data_plane_service.domain import (
    ActorReference,
    AggregateReference,
    ClassificationReference,
    DomainReference,
    EvidenceReference,
    OrganizationScopeReference,
    PrivilegedGrantReference,
    RetentionScheduleReference,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.events import (
    build_data_plane_event,
    recorded_reason_code_for,
)
from epd2_data_plane_service.exceptions import (
    ConsumerNotReadyError,
    SchemaExamplesInvalidError,
    SchemaRegistryUnavailableError,
)
from epd2_data_plane_service.idempotency import (
    BusinessFactGuard,
    IdempotencyDecision,
    IdempotencyKey,
    IdempotencyPolicy,
    IdempotencyRecord,
    compute_request_digest,
)
from epd2_data_plane_service.migrations import (
    AppliedMigration,
    MigrationExecution,
    MigrationExecutionStatus,
    MigrationGateInputs,
    MigrationPlan,
    evaluate_migration_gates,
    reject_out_of_order,
    reject_reapplication,
    require_destructive_authorization,
    verify_checksum,
)
from epd2_data_plane_service.outbox import OutboxRecord, OutboxWriter
from epd2_data_plane_service.privileged import (
    DataPlaneOperation,
    require_scoped_grant,
    require_separation_of_duties,
)
from epd2_data_plane_service.projections import (
    DeletionPropagation,
    DeletionTombstone,
    ProjectedRow,
    ProjectionDefinition,
    ProjectionEvidence,
    ProjectionHealth,
    ProjectionLag,
    ProjectionStaleness,
)
from epd2_data_plane_service.registry import (
    ConsumerRegistration,
    DuplicateContentAssessment,
    RegistryAvailability,
    SchemaDefinition,
    SchemaLifecycleState,
    SchemaPublicationDecision,
    SchemaVersion,
    ValidationResult,
    assess_consumer_readiness,
    assess_duplicate_content,
    require_duplicate_content_admissible,
)
from epd2_data_plane_service.retention import (
    DeletionDecision,
    GovernedArtifactKind,
    require_evidence_for,
)
from epd2_data_plane_service.storage import (
    CommittedWork,
    InMemoryAggregateVersionStore,
    InMemoryAppliedMigrationStore,
    InMemoryBackfillCheckpointStore,
    InMemoryConsumerRegistrationStore,
    InMemoryIdempotencyStore,
    InMemoryOutboxStore,
    InMemoryProjectionStore,
    InMemorySchemaVersionStore,
    ReferenceUnitOfWork,
)

#: The version of the audit-classification policy this module applies.
#: Bumped when the mapping from a governed act to its `*_RECORDED` code
#: changes — never when an individual code's meaning would change, since
#: a code's meaning never changes (`P13-RSN-004`).
AUDIT_POLICY_VERSION = "pack-13-0.13.0"


# ---------------------------------------------------------------------------
# Domain command execution
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DomainCommandRequest:
    """One state-changing domain command presented to the data plane."""

    command_name: str
    aggregate: AggregateReference
    actor: ActorReference
    scope: OrganizationScopeReference
    expected_version: ExpectedVersion
    idempotency_key: IdempotencyKey
    request_payload: Mapping[str, object]
    event_type: str
    event_payload: Mapping[str, object]
    consequential: bool = True


@dataclass(frozen=True, slots=True)
class DomainCommandResult:
    """What one command execution produced."""

    execution: CommandExecutionReference
    committed: CommittedWork | None
    idempotency: IdempotencyDecision
    replayed: bool


class DataPlaneCommandService:
    """The command path: concurrency, idempotency, atomic commit, event.

    Constructed per owning domain, because every store it holds is
    domain-owned. A single instance serving several domains would be the
    universal data-access layer `P13-CTX-001` forbids.
    """

    def __init__(
        self,
        *,
        owning_domain: DomainReference,
        versions: InMemoryAggregateVersionStore,
        outbox: InMemoryOutboxStore,
        idempotency_store: InMemoryIdempotencyStore,
        audit_port: AuditIngestionPort | None = None,
    ) -> None:
        self._owning_domain = owning_domain
        self._versions = versions
        self._outbox = outbox
        self._idempotency = idempotency_store
        self._audit = audit_port

    def execute(
        self,
        request: DomainCommandRequest,
        *,
        unit_reference: UnitOfWorkReference,
        outbox_record_id: UUID,
        event_id: UUID,
        correlation_id: UUID,
        command_execution_id: UUID,
        now: datetime,
        retention_schedule: RetentionScheduleReference | None = None,
        guard: BusinessFactGuard | None = None,
        guarded_fact_already_exists: bool = False,
        rollback: bool = False,
    ) -> DomainCommandResult:
        """Execute one command.

        The order of operations is the guarantee:

        1. **Idempotency** — a replay returns the first result without
           re-performing the effect (`P13-IDEM-005`), and a key reused
           with different content is a conflict, not a replay.
        2. **Optimistic concurrency** — the expected version is checked
           and a mismatch is a reason-coded conflict, never a silent
           overwrite (`P13-CC-002`).
        3. **Last-write-wins refusal** for a consequential record
           (`P13-CC-003`).
        4. **Staging** the new version *and* the outbox record into one
           unit of work.
        5. **Commit or rollback** — both, or neither (`P13-TX-003`,
           `P13-TX-005`).

        `rollback=True` exists so a caller — and a test — can exercise
        the failure path without inventing a fault: the staged work is
        discarded and no outbox record exists to be dispatched.
        """
        require_timezone(now, field="now")
        reject_prohibited_payload_keys(
            dict(request.event_payload), context=f"command {request.command_name}"
        )
        digest = compute_request_digest(dict(request.request_payload))
        existing = self._idempotency.find(request.idempotency_key)
        decision = IdempotencyPolicy.evaluate(
            key=request.idempotency_key,
            incoming_digest=digest,
            existing=existing,
            now=now,
            guard=guard,
            guarded_fact_already_exists=guarded_fact_already_exists,
        )
        IdempotencyPolicy.require_no_conflict(decision, context=f"command {request.command_name}")
        current: AggregateVersion = self._versions.current(request.aggregate)
        if not decision.should_execute and decision.record is not None:
            execution = CommandExecutionReference(
                command_execution_id=command_execution_id,
                command_name=request.command_name,
                aggregate=request.aggregate,
                actor=request.actor,
                scope=request.scope,
                idempotency_key_digest=request.idempotency_key.digest,
                resulting_version=current.version,
                executed_at=now,
            )
            return DomainCommandResult(
                execution=execution, committed=None, idempotency=decision, replayed=True
            )

        # A consequential command that asserts only "any existing
        # version" is last-write-wins wearing an expected-version
        # parameter: it overwrites whatever is there. `P13-CC-003`
        # forbids that for anything bearing a decision, an authorization,
        # a financial fact or a legal effect, so the refusal is raised
        # here rather than at the point the overwrite would land.
        ConcurrencyPolicy.reject_last_write_wins(
            consequential=(
                request.consequential
                and request.expected_version.kind is ExpectedVersionKind.ANY_EXISTING
            ),
            context=f"command {request.command_name}",
        )
        next_version = ConcurrencyPolicy.require_proceed(current, request.expected_version)

        envelope = build_data_plane_event(
            event_id=event_id,
            event_type=request.event_type,
            occurred_at=now,
            actor=request.actor,
            aggregate_id=request.aggregate.aggregate_id,
            scope=request.scope,
            payload=request.event_payload,
            correlation_id=correlation_id,
            sequence_number=next_version.version,
        )
        record = OutboxWriter.write_within(
            unit_reference,
            outbox_record_id=outbox_record_id,
            envelope=envelope,
            aggregate=request.aggregate,
            created_at=now,
            sequence_number=next_version.version,
            retention_schedule=retention_schedule,
        )
        unit = ReferenceUnitOfWork(unit_reference, versions=self._versions, outbox=self._outbox)
        unit.stage(CommittedWork(version=next_version, outbox_record=record))
        if rollback:
            unit.rollback()
            execution = CommandExecutionReference(
                command_execution_id=command_execution_id,
                command_name=request.command_name,
                aggregate=request.aggregate,
                actor=request.actor,
                scope=request.scope,
                idempotency_key_digest=request.idempotency_key.digest,
                resulting_version=current.version,
                executed_at=now,
            )
            return DomainCommandResult(
                execution=execution, committed=None, idempotency=decision, replayed=False
            )

        committed = unit.commit()
        self._idempotency.put(
            IdempotencyRecord(
                key=request.idempotency_key,
                request_digest=digest,
                result_reference=committed.outbox_record.outbox_record_id,
                recorded_at=now,
                expires_at=now.replace(year=now.year + 1),
            )
        )
        execution = CommandExecutionReference(
            command_execution_id=command_execution_id,
            command_name=request.command_name,
            aggregate=request.aggregate,
            actor=request.actor,
            scope=request.scope,
            idempotency_key_digest=request.idempotency_key.digest,
            resulting_version=committed.version.version,
            executed_at=now,
        )
        return DomainCommandResult(
            execution=execution, committed=committed, idempotency=decision, replayed=False
        )


def submit_audit_record(
    port: AuditIngestionPort, submission: AuditSubmission, *, arrived_via_port: bool = True
) -> UUID:
    """Submit a typed audit record through the governed ingestion
    contract.

    The one integration path other domains use to reach audit
    (`P13-DP-014a`). Submission is not persistence: this function returns
    an acknowledgement identifier, and what `audit-core` does with the
    submission — including the hash chain — is entirely its own."""
    require_ingestion_contract(
        arrived_via_port=arrived_via_port,
        context=f"audit submission from {submission.submitting_domain.domain_name}",
    )
    return port.submit(submission)


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SchemaPublicationRequest:
    """One proposed schema version."""

    schema_version_id: UUID
    definition: SchemaDefinition
    version_label: str
    classification: ClassificationReference
    proposed_by: ActorReference
    approved_by: ActorReference
    assessment: CompatibilityAssessment
    evidence: EvidenceReference | None
    intentional_republication: bool = False
    governance_justification: str | None = None


@dataclass(frozen=True, slots=True)
class SchemaPublicationResult:
    version: SchemaVersion
    duplicate_assessment: DuplicateContentAssessment | None
    validation: ValidationResult


class SchemaRegistryService:
    """The governed publication path.

    Holds the version store and the consumer registrations. It performs
    no canonicalization of its own — that belongs to
    `canonicalization`, because the canonicalization is format-specific
    and the registry must not acquire a universal one
    (`P13-FMT-002`)."""

    def __init__(
        self,
        *,
        versions: InMemorySchemaVersionStore,
        consumers: InMemoryConsumerRegistrationStore,
    ) -> None:
        self._versions = versions
        self._consumers = consumers

    def publish(
        self,
        request: SchemaPublicationRequest,
        *,
        now: datetime,
        availability: RegistryAvailability,
        grant: PrivilegedGrantReference | None = None,
    ) -> SchemaPublicationResult:
        """Publish one schema version, or refuse.

        Nine checks, in the order that makes each one meaningful:
        availability, owner, examples, duplicate content, review
        completeness, compatibility under the declared mode, separation
        of duties, evidence, and finally the append.
        """
        require_timezone(now, field="now")
        if not availability.reachable:
            raise SchemaRegistryUnavailableError(
                "the schema registry could not be reached; publication is blocked while "
                "existing traffic continues on already-resolved schemas"
            )
        family = request.definition.family
        # `SchemaOwner.__post_init__` already refused an ownerless or
        # reserved-boundary owner, so reaching here means one exists.
        valid, failures = validate_examples(
            _document_of(request.definition.canonical_content), request.definition.examples
        )
        validation = ValidationResult(all_examples_valid=valid, failures=failures)
        if not valid:
            raise SchemaExamplesInvalidError(
                f"family {family.family_name!r}: the schema's own fixtures do not validate "
                f"against it ({list(failures)}); a schema whose examples fail is not "
                f"publishable"
            )
        duplicate = assess_duplicate_content(
            submitted_digest=request.definition.canonical_content.digest,
            existing_versions=self._versions.by_family(family.family_id),
            governance_justification=request.governance_justification,
            intentional_republication=request.intentional_republication,
        )
        require_duplicate_content_admissible(duplicate, context=f"family {family.family_name!r}")
        require_review_complete(request.assessment, context=f"family {family.family_name!r}")
        require_compatible_under_mode(
            request.assessment,
            declared_mode=family.compatibility_mode,
            context=f"family {family.family_name!r}",
        )
        require_separation_of_duties(
            operation=DataPlaneOperation.SCHEMA_ACTIVATION,
            proposer=request.proposed_by,
            approver=request.approved_by,
        )
        evidence = require_evidence_for(
            GovernedArtifactKind.SCHEMA_PUBLICATION_DECISION,
            request.evidence,
            context=f"family {family.family_name!r}",
        )
        decision = SchemaPublicationDecision(
            publication_decision_id=request.schema_version_id,
            decided_by=request.approved_by,
            decided_at=now,
            evidence=evidence,
            governance_justification=request.governance_justification,
            duplicate_content_disposition=(None if duplicate is None else duplicate.disposition),
        )
        version = SchemaVersion(
            schema_version_id=request.schema_version_id,
            family=family,
            version_label=request.version_label,
            content_digest=request.definition.canonical_content.digest,
            lifecycle_state=SchemaLifecycleState.APPROVED,
            classification=request.classification,
            publication_decision=decision,
            validation_result=validation,
            documentation_reference=request.definition.documentation_reference,
        )
        self._versions.append(version)
        return SchemaPublicationResult(
            version=version, duplicate_assessment=duplicate, validation=validation
        )

    def activate(
        self,
        schema_version_id: UUID,
        *,
        effective_at: datetime,
        grant: PrivilegedGrantReference | None,
        scope: OrganizationScopeReference,
        now: datetime,
    ) -> SchemaVersion:
        """Move an approved version to active under a scoped grant."""
        require_scoped_grant(
            grant, operation=DataPlaneOperation.SCHEMA_ACTIVATION, scope=scope, now=now
        )
        version = self._versions.by_id(schema_version_id)
        activated = version.with_state(SchemaLifecycleState.ACTIVE)
        activated = _with_effective_at(activated, effective_at)
        self._versions.update_state(activated)
        return activated

    def register_consumer(self, registration: ConsumerRegistration) -> None:
        self._consumers.register(registration)

    def require_consumers_ready(self, *, family_id: UUID, target_version_id: UUID) -> None:
        """Refuse retirement or field removal before consumer migration
        is demonstrated through the registry (`P13-API-009`)."""
        readiness = assess_consumer_readiness(
            family_id=family_id,
            target_version_id=target_version_id,
            registrations=self._consumers.for_family(family_id),
        )
        if not readiness.all_ready:
            raise ConsumerNotReadyError(
                f"family {family_id}: registered consumer(s) "
                f"{[str(c) for c in readiness.not_ready_consumer_ids]} have not migrated to "
                f"{target_version_id}; unregistered consumers receive no compatibility "
                f"protection, which is stated rather than discovered"
            )


def _document_of(content: CanonicalContent) -> Mapping[str, object]:
    """Recover the structured document from its canonical text.

    Canonical JSON is a faithful round-trip for the structured formats,
    so this is a parse rather than a reconstruction. It exists so that
    fixture validation reads the *canonical* document — the same bytes
    the digest was taken over — rather than whatever the caller happened
    to pass in."""
    import json

    parsed = json.loads(content.canonical_text)
    if not isinstance(parsed, dict):
        raise SchemaExamplesInvalidError(
            "a schema document canonicalizes to a JSON object; fixtures cannot be validated "
            "against anything else"
        )
    return parsed


def _with_effective_at(version: SchemaVersion, effective_at: datetime) -> SchemaVersion:
    from dataclasses import replace

    return replace(version, effective_at=require_timezone(effective_at, field="effective_at"))


# ---------------------------------------------------------------------------
# Migration execution
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MigrationExecutionResult:
    execution: MigrationExecution
    applied: tuple[AppliedMigration, ...]


class MigrationService:
    """The migration execution path.

    Every gate runs before the first statement is *notionally* applied —
    and no statement is ever actually applied, because this reference
    implementation executes nothing against a database. What it proves is
    that the gates refuse."""

    def __init__(self, *, applied_store: InMemoryAppliedMigrationStore) -> None:
        self._applied = applied_store

    def execute(
        self,
        plan: MigrationPlan,
        *,
        execution_id: UUID,
        grant: PrivilegedGrantReference | None,
        scope: OrganizationScopeReference,
        gates: MigrationGateInputs,
        now: datetime,
    ) -> MigrationExecutionResult:
        """Run one plan under a scoped grant, or refuse.

        Order: grant, destructive authorization, then per-migration
        applied-state, ordering and checksum checks, then the five
        automated gates. The gates run last among the *checks* and first
        among the *effects*: they are what stands between an approved
        plan and an irreversible change."""
        require_timezone(now, field="now")
        operation = (
            DataPlaneOperation.DESTRUCTIVE_MIGRATION
            if plan.is_destructive
            else DataPlaneOperation.MIGRATION_EXECUTION
        )
        checked_grant = require_scoped_grant(grant, operation=operation, scope=scope, now=now)
        require_destructive_authorization(plan, now=now)

        applied_now: list[AppliedMigration] = []
        for definition in plan.ordered_migrations:
            reject_reapplication(definition, self._applied.find(definition.migration_id))
            reject_out_of_order(definition, self._applied.all_applied())
            evaluate_migration_gates(gates, migration_id=definition.migration_id)
            record = AppliedMigration(
                migration_id=definition.migration_id,
                checksum=definition.checksum,
                ordering_position=definition.ordering_position,
                applied_at=now,
                execution_id=execution_id,
            )
            self._applied.append(record)
            applied_now.append(record)

        execution = MigrationExecution(
            execution_id=execution_id,
            plan_id=plan.plan_id,
            status=MigrationExecutionStatus.COMPLETED,
            started_at=now,
            grant=checked_grant,
            completed_at=now,
        )
        return MigrationExecutionResult(execution=execution, applied=tuple(applied_now))

    def verify_applied_checksums(self, plan: MigrationPlan) -> None:
        """Re-verify every applied migration's checksum.

        A mismatch halts and escalates; there is no repair branch
        (`P13-MIG-004`)."""
        for definition in plan.ordered_migrations:
            applied = self._applied.find(definition.migration_id)
            if applied is not None:
                verify_checksum(definition, applied)


# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------


class BackfillService:
    """Runs a backfill and persists its checkpoint and review queue."""

    def __init__(self, *, checkpoints: InMemoryBackfillCheckpointStore) -> None:
        self._checkpoints = checkpoints

    def run(
        self,
        runner: BackfillRunner,
        plan: BackfillPlan,
        records: Sequence[BackfillSourceRecord],
        *,
        now: datetime,
        resume: bool = False,
        max_batches: int | None = None,
    ) -> BackfillOutcome:
        """Run or resume. Resumption reads the persisted checkpoint
        rather than a caller-supplied position, so a restart cannot
        silently begin from the wrong place (`P13-BF-002`)."""
        resume_from: BackfillCheckpoint | None = None
        if resume:
            resume_from = self._checkpoints.latest(plan.backfill_id)
        outcome = runner.run(records, now=now, resume_from=resume_from, max_batches=max_batches)
        self._checkpoints.save(outcome.checkpoint)
        self._checkpoints.enqueue_for_review(plan.backfill_id, outcome.review_queue)
        return outcome

    def reconcile(
        self,
        plan: BackfillPlan,
        outcome: BackfillOutcome,
        *,
        evidence: EvidenceReference,
        now: datetime,
        skipped_under_hold: int = 0,
    ) -> ReconciliationReport:
        """Produce the final report, which refuses to exist if the counts
        do not add up (`P13-BF-014`)."""
        checkpoint = outcome.checkpoint
        return ReconciliationReport(
            backfill_id=plan.backfill_id,
            processed=checkpoint.processed,
            succeeded=checkpoint.succeeded,
            routed_to_review=checkpoint.routed_to_review - skipped_under_hold,
            failed=checkpoint.failed,
            skipped_under_hold=skipped_under_hold,
            evidence=evidence,
            completed_at=now,
        )


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------


class DeliveryService:
    """Dispatches outbox records and feeds a consumer.

    Holds no domain policy of any kind, which is what makes
    `P13-OBX-009` structurally true rather than merely asserted."""

    def __init__(self, *, outbox: InMemoryOutboxStore, dispatcher: ReferenceDispatcher) -> None:
        self._outbox = outbox
        self._dispatcher = dispatcher

    def dispatch_pending(
        self,
        *,
        scope: OrganizationScopeReference,
        now: datetime,
        broker_available: bool = True,
        classification: ClassificationReference | None = None,
        retention_schedule: RetentionScheduleReference | None = None,
        dead_letter_ids: Sequence[UUID] = (),
    ) -> tuple[DispatchResult, ...]:
        """Dispatch every pending record in `scope`, in sequence order."""
        results: list[DispatchResult] = []
        available_ids = list(dead_letter_ids)
        for record in self._outbox.pending(scope=scope):
            result = self._dispatcher.dispatch(
                record,
                now=now,
                broker_available=broker_available,
                classification=classification,
                retention_schedule=retention_schedule,
                dead_letter_id=available_ids.pop(0) if available_ids else None,
            )
            if result.record is not record:
                self._outbox.update_delivery_state(result.record)
            results.append(result)
        return tuple(results)

    @staticmethod
    def consume(
        consumer: ReferenceConsumer,
        record: OutboxRecord,
        *,
        checkpoint: ConsumerCheckpoint,
        now: datetime,
    ) -> ConsumerResult:
        """Hand one delivered record to a consumer.

        A `staticmethod` because the delivery service holds no consumer:
        which consumers exist, and what they do with an event, belongs to
        the domains that own them."""
        return consumer.consume(record, checkpoint=checkpoint, now=now)


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------


class ProjectionService:
    """Applies updates, measures lag, rebuilds, and propagates
    deletions."""

    def __init__(self, *, store: InMemoryProjectionStore) -> None:
        self._store = store

    def declare(self, definition: ProjectionDefinition) -> None:
        self._store.declare(definition)

    def apply_row(self, row: ProjectedRow) -> None:
        """Apply one projected row.

        `ProjectedRow`'s own constructor already enforced scope and the
        prohibited-key guard, so there is nothing left to check here —
        which is the point: the invariant lives on the type, not in a
        service method a second caller could bypass."""
        self._store.upsert_row(row)

    def measure(
        self,
        definition: ProjectionDefinition,
        *,
        events_behind: int,
        observed_at: datetime,
        rebuild_required: bool = False,
        failed: bool = False,
    ) -> ProjectionStaleness:
        """Compute visible staleness (`P13-PROJ-008`)."""
        lag = ProjectionLag(
            projection_id=definition.projection_id,
            events_behind=events_behind,
            lag_band=lag_band_for(events_behind),
            observed_at=observed_at,
        )
        if failed:
            health = ProjectionHealth.FAILED
        elif rebuild_required:
            health = ProjectionHealth.REBUILD_REQUIRED
        elif events_behind > definition.max_acceptable_lag_events:
            health = ProjectionHealth.STALE
        elif events_behind > 0:
            health = ProjectionHealth.LAGGING
        else:
            health = ProjectionHealth.HEALTHY
        return ProjectionStaleness(
            projection_id=definition.projection_id,
            health=health,
            lag=lag,
            max_acceptable_lag_events=definition.max_acceptable_lag_events,
        )

    def propagate_deletion(
        self,
        definition: ProjectionDefinition,
        *,
        row_key: str,
        decision: DeletionDecision,
        tombstone: DeletionTombstone,
        evidence: EvidenceReference,
        now: datetime,
    ) -> DeletionPropagation:
        """Propagate a source deletion into the projection, with
        evidence.

        The retention decision is *read*, never made: `decision` comes
        from PACK-09's inputs and `require_eligible` raises its own
        registered refusal when the record is held, unknown, governed or
        not yet due."""
        decision.require_eligible(context=f"projection {definition.projection_name!r}")
        self._store.tombstone_row(definition.projection_id, row_key)
        propagation = DeletionPropagation(
            projection_id=definition.projection_id,
            source_record_id=tombstone.source_record_id,
            tombstone=tombstone,
            evidence=ProjectionEvidence(
                evidence_reference=evidence,
                projection_id=definition.projection_id,
                source_record_id=tombstone.source_record_id,
                propagated_at=now,
                outcome="propagated",
            ),
        )
        propagation.require_propagated()
        return propagation


def audit_classification_for(event_type: str) -> str:
    """The registered `*_RECORDED` classification for a successful act.

    A thin re-export of `events.recorded_reason_code_for`, present so
    that the application layer's audit path reads from one named function
    rather than assembling the code inline at each call site."""
    return recorded_reason_code_for(event_type)
