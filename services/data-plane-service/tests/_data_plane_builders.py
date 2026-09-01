"""Deterministic builders shared by the PACK-13 test suite.

Every identifier is derived from a fixed seed and every timestamp comes
from a fixed instant, so two runs of the same test produce byte-identical
events, digests and checkpoints. The package under test holds no clock
and mints no UUID precisely so that this is possible.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from epd2_data_plane_service.canonicalization import (
    CanonicalContent,
    SchemaFormat,
    canonicalize,
)
from epd2_data_plane_service.compatibility import (
    CompatibilityAssessment,
    HumanVerdict,
    SemanticRiskClass,
    StructuralVerdict,
    assess_structural_change,
)
from epd2_data_plane_service.concurrency import (
    AggregateVersion,
    TransactionBoundary,
    UnitOfWorkReference,
)
from epd2_data_plane_service.domain import (
    ActorReference,
    AggregateReference,
    ClassificationReference,
    DomainReference,
    EvidenceReference,
    OrganizationScopeKind,
    OrganizationScopeReference,
    PrivilegedGrantReference,
    RecordClassReference,
    RetentionScheduleReference,
)
from epd2_data_plane_service.events import build_data_plane_event
from epd2_data_plane_service.idempotency import (
    IdempotencyKey,
    IdempotencyScope,
    OperationClass,
)
from epd2_data_plane_service.migrations import (
    DryRunEvidence,
    MigrationApproval,
    MigrationClass,
    MigrationDefinition,
    MigrationGateInputs,
    MigrationPlan,
    MigrationRollbackDecision,
)
from epd2_data_plane_service.outbox import DestinationReference, OutboxRecord, OutboxWriter
from epd2_data_plane_service.registry import (
    CompatibilityMode,
    DocumentationReference,
    SchemaDefinition,
    SchemaFamily,
    SchemaOwner,
)

#: One fixed instant for the whole suite.
NOW = datetime(2026, 3, 2, 9, 30, tzinfo=UTC)

#: The domain under test in most cases.
OWNER_DOMAIN = DomainReference(domain_name="membership-service")
OTHER_DOMAIN = DomainReference(domain_name="finance-service")
AUDIT_DOMAIN = DomainReference(domain_name="audit-core")


def uid(n: int) -> UUID:
    """A deterministic UUID from a small integer."""
    return UUID(int=n)


def scope(
    n: int = 1, kind: OrganizationScopeKind = OrganizationScopeKind.LAND
) -> OrganizationScopeReference:
    return OrganizationScopeReference(organization_id=uid(1000 + n), scope_kind=kind)


def actor(n: int = 1, *, domain: DomainReference = OWNER_DOMAIN) -> ActorReference:
    return ActorReference(
        actor_id=uid(2000 + n), actor_type="operational_role", acting_domain=domain
    )


def aggregate(n: int = 1, *, domain: DomainReference = OWNER_DOMAIN) -> AggregateReference:
    return AggregateReference(
        aggregate_type="membership", aggregate_id=uid(3000 + n), owning_domain=domain
    )


def classification(tier: str = "restricted") -> ClassificationReference:
    return ClassificationReference(classification_id=uid(4001), tier=tier)


def record_class(*, consequential: bool = True) -> RecordClassReference:
    return RecordClassReference(
        record_class_id=uid(4002),
        record_class_name="operational_record",
        consequential=consequential,
    )


def evidence(n: int = 1) -> EvidenceReference:
    return EvidenceReference(evidence_bundle_id=uid(5000 + n), content_digest="a" * 64)


def retention(n: int = 1) -> RetentionScheduleReference:
    return RetentionScheduleReference(schedule_id=uid(6000 + n), schedule_name="operational-7y")


def grant(
    operation: str,
    *,
    n: int = 1,
    at: datetime = NOW,
    organization: OrganizationScopeReference | None = None,
) -> PrivilegedGrantReference:
    return PrivilegedGrantReference(
        grant_id=uid(7000 + n),
        purpose="data_plane_operation",
        operation=operation,
        scope=organization or scope(),
        expires_at=at + timedelta(hours=2),
    )


def boundary(*, domain: DomainReference = OWNER_DOMAIN) -> TransactionBoundary:
    return TransactionBoundary(owning_domain=domain, schema_name=f"{domain.domain_name}_schema")


def unit_reference(
    n: int = 1, *, domain: DomainReference = OWNER_DOMAIN, at: datetime = NOW
) -> UnitOfWorkReference:
    return UnitOfWorkReference(
        unit_of_work_id=uid(8000 + n),
        boundary=boundary(domain=domain),
        scope=scope(),
        started_at=at,
    )


def version(n: int, *, agg: AggregateReference | None = None) -> AggregateVersion:
    return AggregateVersion(aggregate=agg or aggregate(), version=n)


def idempotency_key(
    value: str = "req-1",
    *,
    operation: str = "record_membership",
    operation_class: OperationClass = OperationClass.COMMAND,
    domain: str = "membership-service",
) -> IdempotencyKey:
    return IdempotencyKey(
        scope=IdempotencyScope(
            domain_name=domain, operation_name=operation, operation_class=operation_class
        ),
        key_value=value,
    )


def destination(n: int = 1) -> DestinationReference:
    return DestinationReference(destination_id=uid(9000 + n), destination_name="reference-topic")


def outbox_record(
    *,
    n: int = 1,
    event_type: str = "projection.updated",
    at: datetime = NOW,
    sequence_number: int = 1,
    domain: DomainReference = OWNER_DOMAIN,
    payload: Mapping[str, object] | None = None,
) -> OutboxRecord:
    """One committed outbox record, built through the writer so the
    atomicity and payload guards actually ran."""
    reference = unit_reference(n, domain=domain, at=at)
    agg = aggregate(n, domain=domain)
    envelope = build_data_plane_event(
        event_id=uid(10000 + n),
        event_type=event_type,
        occurred_at=at,
        actor=actor(domain=domain),
        aggregate_id=agg.aggregate_id,
        scope=scope(),
        payload=payload or {"projection_id": str(uid(11000)), "position": 1},
        correlation_id=uid(12000 + n),
        sequence_number=sequence_number,
    )
    return OutboxWriter.write_within(
        reference,
        outbox_record_id=uid(13000 + n),
        envelope=envelope,
        aggregate=agg,
        created_at=at,
        sequence_number=sequence_number,
        retention_schedule=retention(),
    )


# ---------------------------------------------------------------------------
# Schema registry fixtures
# ---------------------------------------------------------------------------

BASE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "membership_id": {"type": "string", "format": "uuid"},
        "organization_id": {"type": "string", "format": "uuid"},
        "status": {"type": "string", "enum": ["active", "suspended"]},
    },
    "required": ["membership_id", "organization_id", "status"],
    "additionalProperties": False,
}

BASE_EXAMPLE: dict[str, Any] = {
    "membership_id": "00000000-0000-0000-0000-000000000001",
    "organization_id": "00000000-0000-0000-0000-000000000002",
    "status": "active",
}


def owner(*, domain: DomainReference = OWNER_DOMAIN) -> SchemaOwner:
    return SchemaOwner(domain=domain, accountable_role="membership_data_steward")


def family(
    *,
    n: int = 1,
    mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    schema_format: SchemaFormat = SchemaFormat.JSON_SCHEMA,
    domain: DomainReference = OWNER_DOMAIN,
) -> SchemaFamily:
    return SchemaFamily(
        family_id=uid(14000 + n),
        family_name="membership.record",
        owner=owner(domain=domain),
        schema_format=schema_format,
        compatibility_mode=mode,
    )


def canonical(document: Mapping[str, Any] | None = None) -> CanonicalContent:
    return canonicalize(SchemaFormat.JSON_SCHEMA, document or BASE_SCHEMA)


def definition(
    *,
    document: Mapping[str, Any] | None = None,
    fam: SchemaFamily | None = None,
    examples: Sequence[Mapping[str, Any]] | None = None,
) -> SchemaDefinition:
    return SchemaDefinition(
        family=fam or family(),
        canonical_content=canonical(document),
        documentation_reference=DocumentationReference(
            documentation_id=uid(15000), title="Membership record schema"
        ),
        examples=tuple(examples if examples is not None else (BASE_EXAMPLE,)),
    )


def clean_assessment(
    *,
    previous: Mapping[str, Any] | None = None,
    proposed: Mapping[str, Any] | None = None,
    risks: frozenset[SemanticRiskClass] = frozenset(),
    human: HumanVerdict | None = None,
    n: int = 1,
) -> CompatibilityAssessment:
    """An assessment over two documents. With no arguments the two are
    identical, so the structural verdict is `FULL`."""
    structural: StructuralVerdict = assess_structural_change(
        previous or BASE_SCHEMA, proposed or BASE_SCHEMA
    )
    return CompatibilityAssessment(
        assessment_id=uid(16000 + n),
        family_id=uid(14001),
        previous_version_id=None,
        proposed_version_label="1.0.0",
        structural=structural,
        semantic_risk_classes=risks,
        human=human,
    )


def human_verdict(
    verdict: CompatibilityMode = CompatibilityMode.BACKWARD, *, at: datetime = NOW
) -> HumanVerdict:
    return HumanVerdict(
        verdict=verdict,
        reviewer=actor(9),
        reviewed_at=at,
        rationale="Reviewed against the family's declared mode and recorded consumers.",
    )


# ---------------------------------------------------------------------------
# Migration fixtures
# ---------------------------------------------------------------------------


def migration_definition(
    *,
    migration_id: str = "0001_add_scope_column",
    position: int = 1,
    migration_class: MigrationClass = MigrationClass.EXPAND,
    statements: tuple[str, ...] = ("add column organization_id",),
    destructive: bool = False,
) -> MigrationDefinition:
    return MigrationDefinition(
        migration_id=migration_id,
        owning_domain=OWNER_DOMAIN,
        migration_class=migration_class,
        ordering_position=position,
        statements=statements,
        declared_destructive=destructive,
    )


def rollback(*, available: bool = True, tested: bool = True) -> MigrationRollbackDecision:
    if available:
        return MigrationRollbackDecision(
            rollback_available=True,
            tested=tested,
            forward_fix_only=False,
            statement="Rehearsed against a copy of the reference fixtures.",
        )
    return MigrationRollbackDecision(
        rollback_available=False,
        tested=False,
        forward_fix_only=True,
        statement="Forward-fix only; no rollback exists and none is implied.",
    )


def approval(*, n: int = 1, at: datetime = NOW) -> MigrationApproval:
    return MigrationApproval(
        approval_id=uid(17000 + n),
        proposed_by=actor(1),
        approved_by=actor(2),
        approved_at=at,
        evidence=evidence(2),
    )


def dry_run(*, at: datetime = NOW) -> DryRunEvidence:
    return DryRunEvidence(
        dry_run_id=uid(18000), performed_at=at, rows_would_be_affected=12, evidence=evidence(3)
    )


def migration_plan(
    *,
    n: int = 1,
    migration_class: MigrationClass = MigrationClass.EXPAND,
    migrations: tuple[MigrationDefinition, ...] | None = None,
    with_approval: bool = False,
    with_dry_run: bool = False,
    old_writes_stopped_at: datetime | None = None,
    reconciliation: str | None = None,
) -> MigrationPlan:
    return MigrationPlan(
        plan_id=uid(19000 + n),
        owning_domain=OWNER_DOMAIN,
        migration_class=migration_class,
        migrations=migrations or (migration_definition(),),
        rollback_decision=rollback(),
        evidence=evidence(4),
        approval=approval() if with_approval else None,
        dry_run=dry_run() if with_dry_run else None,
        old_writes_stopped_at=old_writes_stopped_at,
        dual_write_reconciliation_strategy=reconciliation,
    )


def passing_gates() -> MigrationGateInputs:
    return MigrationGateInputs(
        organization_scope_preserved=True,
        legal_hold_state_resolved=True,
        retention_records_preserved=True,
        evidence_linkage_preserved=True,
        creates_cross_domain_person_key=False,
        weakens_ballot_unlinkability=False,
    )
