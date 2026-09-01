"""Application-layer tests for compliance-service (PACK-09).

Organised by the required-scope test matrix: retention and destruction,
scope isolation, deadlines, processing registry, disputes - plus the
idempotency and audit conventions PACK-02 through PACK-08 already
require of every command.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_compliance_service.application import (
    RequestContext,
    advance_data_subject_request,
    assign_case_handler,
    assign_independent_decision_maker,
    authorize_destruction,
    change_processing_activity_status,
    complete_deadline,
    decide_data_subject_request,
    declare_conflict_of_interest,
    define_deadline,
    escalate_deadline,
    evaluate_disposal_eligibility,
    execute_destruction,
    expire_deadline,
    extend_deadline,
    file_appeal,
    intake_data_subject_request,
    mark_legal_hold_indeterminate,
    open_procedural_case,
    place_legal_hold,
    read_procedural_case,
    read_processing_activity,
    record_case_decision,
    record_retention_start,
    record_search_result_reference,
    register_data_asset,
    register_dispute_parties,
    register_governed_record,
    register_processing_activity,
    register_retention_policy,
    release_legal_hold,
    resume_deadline,
    set_identity_verification_status,
    start_deadline,
    supersede_retention_policy,
    suspend_deadline,
    transition_procedural_case,
)
from epd2_compliance_service.domain import (
    CaseStatus,
    CaseType,
    ConflictState,
    CrossScopeAuthorityGrant,
    DataAsset,
    DataSubjectRequestStatus,
    DataSubjectRequestType,
    DeadlineDefinition,
    DeadlineEventType,
    DeadlineStatus,
    DecisionOutcome,
    DispositionAction,
    GovernedRecord,
    GovernedRecordState,
    IdentityVerificationStatus,
    LegalBasis,
    LegalHoldScope,
    LegalHoldStatus,
    ProceduralCase,
    ProcessingActivity,
    RecordSensitivity,
    RegistryEntryStatus,
    ResponseDecision,
    RetentionPolicy,
    RetentionTrigger,
    ScopeCapability,
    mint_case_party_reference,
)
from epd2_compliance_service.exceptions import (
    ComplianceRecordNotFoundError,
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    CrossOrganizationCaseAccessDeniedError,
    CrossScopeAuthorityInvalidError,
    DeadlineSilentReplacementRejectedError,
    DecisionAuthorityMissingError,
    DestructionAuthorizationRequiredError,
    DestructionAuthorizationStaleError,
    IdentityVerificationInsufficientError,
    LegalHoldStateUnknownError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeUndeterminedError,
    ProceduralCaseClosedError,
    ProceduralIndependenceViolationError,
    RecordUnderLegalHoldError,
    RetentionStartUndeterminedError,
)
from epd2_compliance_service.storage import (
    InMemoryAppealReferenceStore,
    InMemoryCaseDecisionStore,
    InMemoryCaseRoleAssignmentStore,
    InMemoryConflictDeclarationStore,
    InMemoryCrossScopeAuthorityGrantStore,
    InMemoryDataAssetStore,
    InMemoryDataSubjectRequestStore,
    InMemoryDeadlineDefinitionStore,
    InMemoryDestructionAuthorizationStore,
    InMemoryDestructionEvidenceStore,
    InMemoryDisputePartiesStore,
    InMemoryGovernedRecordStore,
    InMemoryLegalHoldStore,
    InMemoryProceduralCaseStore,
    InMemoryProceduralDeadlineStore,
    InMemoryProcessingActivityStore,
    InMemoryRetentionPolicyStore,
    InMemoryRetentionStartEventStore,
)
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
BERLIN = "Europe/Berlin"
REASON = "COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED"


class _MovableClock:
    """A `Clock` whose instant the test moves explicitly.

    Used instead of `FixedClock` wherever a test must exercise "time has
    passed" without ever calling real system time."""

    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


@dataclass(slots=True)
class World:
    """One fully-wired compliance-service instance plus the two
    organizations most tests need."""

    policies: InMemoryRetentionPolicyStore
    records: InMemoryGovernedRecordStore
    starts: InMemoryRetentionStartEventStore
    holds: InMemoryLegalHoldStore
    authorizations: InMemoryDestructionAuthorizationStore
    evidence: InMemoryDestructionEvidenceStore
    assets: InMemoryDataAssetStore
    activities: InMemoryProcessingActivityStore
    cases: InMemoryProceduralCaseStore
    roles: InMemoryCaseRoleAssignmentStore
    conflicts: InMemoryConflictDeclarationStore
    decisions: InMemoryCaseDecisionStore
    appeals: InMemoryAppealReferenceStore
    parties: InMemoryDisputePartiesStore
    definitions: InMemoryDeadlineDefinitionStore
    deadlines: InMemoryProceduralDeadlineStore
    requests: InMemoryDataSubjectRequestStore
    grants: InMemoryCrossScopeAuthorityGrantStore
    audit: InMemoryAuditEventStore
    clock: _MovableClock
    land_a: UUID
    land_b: UUID
    bund: UUID


def _world(at: datetime = T0) -> World:
    return World(
        policies=InMemoryRetentionPolicyStore(),
        records=InMemoryGovernedRecordStore(),
        starts=InMemoryRetentionStartEventStore(),
        holds=InMemoryLegalHoldStore(),
        authorizations=InMemoryDestructionAuthorizationStore(),
        evidence=InMemoryDestructionEvidenceStore(),
        assets=InMemoryDataAssetStore(),
        activities=InMemoryProcessingActivityStore(),
        cases=InMemoryProceduralCaseStore(),
        roles=InMemoryCaseRoleAssignmentStore(),
        conflicts=InMemoryConflictDeclarationStore(),
        decisions=InMemoryCaseDecisionStore(),
        appeals=InMemoryAppealReferenceStore(),
        parties=InMemoryDisputePartiesStore(),
        definitions=InMemoryDeadlineDefinitionStore(),
        deadlines=InMemoryProceduralDeadlineStore(),
        requests=InMemoryDataSubjectRequestStore(),
        grants=InMemoryCrossScopeAuthorityGrantStore(),
        audit=InMemoryAuditEventStore(),
        clock=_MovableClock(at),
        land_a=uuid4(),
        land_b=uuid4(),
        bund=uuid4(),
    )


def _context(
    organization_id: UUID | None, *, authority_reference_ids: frozenset[UUID] = frozenset()
) -> RequestContext:
    return RequestContext(
        actor=ActorRef(actor_id=uuid4(), actor_type="service"),
        organization_id=organization_id,
        correlation_id=uuid4(),
        authority_reference_ids=authority_reference_ids,
    )


def _policy(
    organization_id: UUID,
    *,
    retention_days: int = 30,
    disposition_action: DispositionAction = DispositionAction.DELETE,
    policy_id: UUID | None = None,
    policy_version: int = 1,
    supersedes: int | None = None,
) -> RetentionPolicy:
    return RetentionPolicy(
        policy_id=policy_id if policy_id is not None else uuid4(),
        organization_id=organization_id,
        record_class="case.disciplinary",
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        retention_days=retention_days,
        disposition_action=disposition_action,
        policy_version=policy_version,
        valid_from=T0,
        supersedes_policy_version=supersedes,
    )


def _record(policy: RetentionPolicy) -> GovernedRecord:
    return GovernedRecord(
        record_id=uuid4(),
        organization_id=policy.organization_id,
        record_class=policy.record_class,
        sensitivity=RecordSensitivity.CONFIDENTIAL,
        created_at=T0,
        retention_policy_id=policy.policy_id,
        retention_policy_version=policy.policy_version,
        source_reference="membership-service:case:1",
    )


def _governed(
    world: World,
    organization_id: UUID,
    *,
    retention_days: int = 30,
    disposition_action: DispositionAction = DispositionAction.DELETE,
    with_start: bool = True,
) -> tuple[RetentionPolicy, GovernedRecord]:
    context = _context(organization_id)
    policy = register_retention_policy(
        world.policies,
        context,
        _policy(
            organization_id,
            retention_days=retention_days,
            disposition_action=disposition_action,
        ),
    )
    record = register_governed_record(world.records, world.policies, context, _record(policy))
    if with_start:
        record = record_retention_start(
            world.records,
            world.starts,
            world.audit,
            context,
            record_id=record.record_id,
            trigger_occurred_at=T0,
            source_reference="case:1",
            clock=world.clock,
        ).record
    return policy, record


def _case(
    organization_id: UUID,
    *,
    case_type: CaseType = CaseType.PARTY_ARBITRATION,
    procedural_authority_reference: UUID | None = None,
) -> ProceduralCase:
    return ProceduralCase(
        case_id=uuid4(),
        organization_id=organization_id,
        case_type=case_type,
        status=CaseStatus.OPEN,
        opened_at=T0,
        subject_reference="dispute:2026-1",
        procedural_authority_reference=(
            procedural_authority_reference
            if procedural_authority_reference is not None
            else uuid4()
        ),
        workflow_type="party_arbitration_standard",
    )


def _open_case(world: World, organization_id: UUID, **kwargs: object) -> ProceduralCase:
    case = _case(organization_id, **kwargs)  # type: ignore[arg-type]
    return open_procedural_case(
        world.cases, world.audit, _context(organization_id), case, clock=world.clock
    ).case


def _definition(
    world: World, organization_id: UUID, *, duration_days: int = 10
) -> DeadlineDefinition:
    return define_deadline(
        world.definitions,
        _context(organization_id),
        DeadlineDefinition(
            definition_id=uuid4(),
            organization_id=organization_id,
            deadline_code="RESPONSE_DUE",
            duration_days=duration_days,
            timezone=BERLIN,
        ),
    )


def _activity(organization_id: UUID, retention_policy_reference: UUID) -> ProcessingActivity:
    return ProcessingActivity(
        activity_id=uuid4(),
        organization_id=organization_id,
        name="Mitgliederverwaltung",
        purpose="membership administration",
        legal_basis=LegalBasis.PARTY_STATUTE,
        data_subject_categories=("members",),
        personal_data_categories=("contact_data",),
        recipient_categories=("internal_administration",),
        retention_policy_reference=retention_policy_reference,
        technical_organizational_measures=("rbac",),
        controller_reference=uuid4(),
        process_owner_authority_reference=uuid4(),
        system_references=("membership-service",),
        status=RegistryEntryStatus.DRAFT,
        valid_from=T0,
    )


def _grant(
    world: World,
    *,
    granting: UUID,
    grantee: UUID,
    capabilities: frozenset[ScopeCapability],
) -> CrossScopeAuthorityGrant:
    return world.grants.save(
        CrossScopeAuthorityGrant(
            grant_id=uuid4(),
            granting_organization_id=granting,
            grantee_organization_id=grantee,
            capabilities=capabilities,
            valid_from=T0,
            valid_until=None,
            authorizing_decision_reference=uuid4(),
        )
    )


def _authorize_and_destroy(
    world: World, organization_id: UUID, record_id: UUID, *, event_id: UUID | None = None
) -> None:
    context = _context(organization_id)
    authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    execute_destruction(
        world.records,
        world.holds,
        world.authorizations,
        world.evidence,
        world.audit,
        context,
        record_id=record_id,
        executed_by_authority_reference=uuid4(),
        evidence_digest="sha256:deadbeef",
        clock=world.clock,
        event_id=event_id,
    )


# ===========================================================================
# Retention and destruction
# ===========================================================================


def test_a_record_that_has_not_reached_its_due_time_is_not_eligible() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=29)

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        _context(world.land_a),
        record_id=record.record_id,
        clock=world.clock,
    )
    assert not eligibility.eligible
    assert eligibility.reason_code == "RETENTION_DISPOSITION_NOT_DUE"
    assert eligibility.due_at == T0 + timedelta(days=30)


def test_a_record_that_has_reached_its_due_time_is_eligible() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=30)

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        _context(world.land_a),
        record_id=record.record_id,
        clock=world.clock,
    )
    assert eligibility.eligible
    assert eligibility.reason_code is None
    assert eligibility.blocking_hold_ids == ()


def test_a_record_without_a_recorded_retention_start_fails_closed() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, with_start=False)
    world.clock.at = T0 + timedelta(days=365)

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        _context(world.land_a),
        record_id=record.record_id,
        clock=world.clock,
    )
    assert not eligibility.eligible
    assert eligibility.reason_code == "RETENTION_START_UNDETERMINED"
    with pytest.raises(RetentionStartUndeterminedError):
        authorize_destruction(
            world.records,
            world.policies,
            world.holds,
            world.authorizations,
            world.audit,
            _context(world.land_a),
            record_id=record.record_id,
            authorized_by_authority_reference=uuid4(),
            clock=world.clock,
        )


def test_an_active_legal_hold_blocks_destruction_even_when_due() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    place_legal_hold(
        world.holds,
        world.audit,
        _context(world.land_a),
        hold_id=uuid4(),
        matter_reference="matter/1",
        scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=40)

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        _context(world.land_a),
        record_id=record.record_id,
        clock=world.clock,
    )
    assert not eligibility.eligible
    assert eligibility.reason_code == "RECORD_UNDER_LEGAL_HOLD"
    assert eligibility.blocking_hold_ids

    with pytest.raises(RecordUnderLegalHoldError):
        authorize_destruction(
            world.records,
            world.policies,
            world.holds,
            world.authorizations,
            world.audit,
            _context(world.land_a),
            record_id=record.record_id,
            authorized_by_authority_reference=uuid4(),
            clock=world.clock,
        )


def test_a_hold_placed_after_authorization_still_blocks_execution() -> None:
    """The hold check is re-run at execution time, not only when the
    authorization was issued (invariant 3)."""
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    context = _context(world.land_a)
    authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record.record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    place_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=uuid4(),
        matter_reference="matter/late",
        scope=LegalHoldScope(record_classes=frozenset({record.record_class})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    with pytest.raises(RecordUnderLegalHoldError):
        execute_destruction(
            world.records,
            world.holds,
            world.authorizations,
            world.evidence,
            world.audit,
            context,
            record_id=record.record_id,
            executed_by_authority_reference=uuid4(),
            evidence_digest="sha256:1",
            clock=world.clock,
        )
    assert world.evidence.get_for_record(record.record_id) is None


def test_releasing_a_hold_restores_eligibility_assessment() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    context = _context(world.land_a)
    hold = place_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=uuid4(),
        matter_reference="matter/1",
        scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    ).hold
    world.clock.at = T0 + timedelta(days=40)

    released = release_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=hold.hold_id,
        released_by_authority_reference=uuid4(),
        clock=world.clock,
    ).hold
    assert released.status is LegalHoldStatus.RELEASED

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        context,
        record_id=record.record_id,
        clock=world.clock,
    )
    assert eligibility.eligible


def test_an_indeterminate_hold_state_fails_closed_on_assessment_and_destruction() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    context = _context(world.land_a)
    hold = place_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=uuid4(),
        matter_reference="matter/1",
        scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    ).hold
    world.clock.at = T0 + timedelta(days=40)
    mark_legal_hold_indeterminate(
        world.holds,
        world.audit,
        context,
        hold_id=hold.hold_id,
        actor_authority_reference=uuid4(),
        clock=world.clock,
    )

    with pytest.raises(LegalHoldStateUnknownError):
        evaluate_disposal_eligibility(
            world.records,
            world.policies,
            world.holds,
            context,
            record_id=record.record_id,
            clock=world.clock,
        )
    with pytest.raises(LegalHoldStateUnknownError):
        authorize_destruction(
            world.records,
            world.policies,
            world.holds,
            world.authorizations,
            world.audit,
            context,
            record_id=record.record_id,
            authorized_by_authority_reference=uuid4(),
            clock=world.clock,
        )


def test_changing_the_retention_policy_does_not_bypass_an_active_hold() -> None:
    """Invariant 5 + invariant 3 together: shortening retention to zero
    and superseding the policy neither authorizes destruction nor lifts
    the hold."""
    world = _world()
    context = _context(world.land_a)
    policy = register_retention_policy(
        world.policies, context, _policy(world.land_a, retention_days=3650)
    )
    record = register_governed_record(world.records, world.policies, context, _record(policy))
    record = record_retention_start(
        world.records,
        world.starts,
        world.audit,
        context,
        record_id=record.record_id,
        trigger_occurred_at=T0,
        source_reference="case:1",
        clock=world.clock,
    ).record
    place_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=uuid4(),
        matter_reference="matter/1",
        scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    )

    world.clock.at = T0 + timedelta(days=1)
    supersede_retention_policy(
        world.policies,
        world.records,
        context,
        superseding_policy=_policy(
            world.land_a,
            retention_days=0,
            policy_id=policy.policy_id,
            policy_version=2,
            supersedes=1,
        ),
    )

    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        context,
        record_id=record.record_id,
        clock=world.clock,
    )
    assert not eligibility.eligible
    assert eligibility.reason_code == "RECORD_UNDER_LEGAL_HOLD"


def test_superseding_a_policy_invalidates_a_standing_authorization() -> None:
    """Invariant 5 on its own: an authorization written under version 1
    can never be executed after version 2 lands."""
    world = _world()
    context = _context(world.land_a)
    policy = register_retention_policy(
        world.policies, context, _policy(world.land_a, retention_days=30)
    )
    record = register_governed_record(world.records, world.policies, context, _record(policy))
    record_retention_start(
        world.records,
        world.starts,
        world.audit,
        context,
        record_id=record.record_id,
        trigger_occurred_at=T0,
        source_reference="case:1",
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=40)
    authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record.record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    stored = world.records.get_in_scope(record.record_id, world.land_a)
    assert stored is not None
    assert stored.state is GovernedRecordState.DISPOSAL_AUTHORIZED

    _, rebound = supersede_retention_policy(
        world.policies,
        world.records,
        context,
        superseding_policy=_policy(
            world.land_a,
            retention_days=60,
            policy_id=policy.policy_id,
            policy_version=2,
            supersedes=1,
        ),
    )
    assert len(rebound) == 1
    assert rebound[0].state is GovernedRecordState.ACTIVE
    assert rebound[0].destruction_authorization_id is None

    with pytest.raises(DestructionAuthorizationRequiredError):
        execute_destruction(
            world.records,
            world.holds,
            world.authorizations,
            world.evidence,
            world.audit,
            context,
            record_id=record.record_id,
            executed_by_authority_reference=uuid4(),
            evidence_digest="sha256:1",
            clock=world.clock,
        )


def test_a_stale_authorization_is_refused_with_its_own_reason_code() -> None:
    world = _world()
    context = _context(world.land_a)
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record.record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    # An unrelated record-version bump makes the standing authorization
    # stale without touching the policy.
    stored = world.records.get_in_scope(record.record_id, world.land_a)
    assert stored is not None
    world.records.save(replace(stored, record_version=stored.record_version + 1))

    with pytest.raises(DestructionAuthorizationStaleError):
        execute_destruction(
            world.records,
            world.holds,
            world.authorizations,
            world.evidence,
            world.audit,
            context,
            record_id=record.record_id,
            executed_by_authority_reference=uuid4(),
            evidence_digest="sha256:1",
            clock=world.clock,
        )


def test_destruction_requires_an_authorization_there_is_no_plain_delete() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=0)
    with pytest.raises(DestructionAuthorizationRequiredError):
        execute_destruction(
            world.records,
            world.holds,
            world.authorizations,
            world.evidence,
            world.audit,
            _context(world.land_a),
            record_id=record.record_id,
            executed_by_authority_reference=uuid4(),
            evidence_digest="sha256:1",
            clock=world.clock,
        )
    assert not any(name in dir(world.records) for name in ("delete", "remove", "purge", "drop"))


def test_a_repeated_destruction_command_is_idempotent_and_evidence_is_created_once() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    context = _context(world.land_a)
    authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record.record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    event_id = uuid4()
    first = execute_destruction(
        world.records,
        world.holds,
        world.authorizations,
        world.evidence,
        world.audit,
        context,
        record_id=record.record_id,
        executed_by_authority_reference=uuid4(),
        evidence_digest="sha256:1",
        clock=world.clock,
        event_id=event_id,
    )
    second = execute_destruction(
        world.records,
        world.holds,
        world.authorizations,
        world.evidence,
        world.audit,
        context,
        record_id=record.record_id,
        executed_by_authority_reference=uuid4(),
        evidence_digest="sha256:1",
        clock=world.clock,
        event_id=event_id,
    )

    assert first.evidence == second.evidence
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert first.record.state is GovernedRecordState.DESTROYED
    assert world.evidence.get_for_record(record.record_id) == first.evidence
    destroyed_audit = [
        event
        for event in world.audit.list_by_aggregate("governed_record", record.record_id)
        if event.action == "execute_destruction"
    ]
    assert len(destroyed_audit) == 1


def test_the_destroyed_record_row_survives_with_its_evidence_reference() -> None:
    """ "No silent deletion": after destruction the metadata row is still
    readable and points at the evidence."""
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    _authorize_and_destroy(world, world.land_a, record.record_id)

    stored = world.records.get_in_scope(record.record_id, world.land_a)
    assert stored is not None
    assert stored.state is GovernedRecordState.DESTROYED
    assert stored.destruction_evidence_id is not None
    evidence = world.evidence.get_for_record(record.record_id)
    assert evidence is not None
    assert evidence.evidence_id == stored.destruction_evidence_id


def test_an_archive_disposition_is_not_blocked_by_a_hold() -> None:
    """Only destructive dispositions are hold-blocked; archiving a held
    record into managed storage stays available."""
    world = _world()
    _, record = _governed(
        world, world.land_a, retention_days=30, disposition_action=DispositionAction.ARCHIVE
    )
    context = _context(world.land_a)
    place_legal_hold(
        world.holds,
        world.audit,
        context,
        hold_id=uuid4(),
        matter_reference="matter/1",
        scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=40)
    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        context,
        record_id=record.record_id,
        clock=world.clock,
    )
    assert eligibility.eligible


def test_authorize_destruction_honours_optimistic_concurrency() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    with pytest.raises(OptimisticConcurrencyConflictError):
        authorize_destruction(
            world.records,
            world.policies,
            world.holds,
            world.authorizations,
            world.audit,
            _context(world.land_a),
            record_id=record.record_id,
            authorized_by_authority_reference=uuid4(),
            clock=world.clock,
            expected_record_version=99,
        )


# ===========================================================================
# Scope isolation
# ===========================================================================


def test_a_context_without_a_resolvable_scope_is_refused() -> None:
    world = _world()
    with pytest.raises(OrganizationScopeUndeterminedError):
        register_retention_policy(world.policies, _context(None), _policy(world.land_a))


def test_an_entity_submitted_without_an_organization_is_refused() -> None:
    world = _world()
    context = _context(world.land_a)
    policy = register_retention_policy(world.policies, context, _policy(world.land_a))
    record = _record(policy)
    with pytest.raises(OrganizationScopeUndeterminedError):
        register_governed_record(
            world.records,
            world.policies,
            context,
            replace(record, organization_id=None),  # type: ignore[arg-type]
        )


def test_land_a_cannot_read_land_b_cases_and_learns_nothing_from_the_id() -> None:
    world = _world()
    case_b = _open_case(world, world.land_b)

    with pytest.raises(ComplianceRecordNotFoundError) as seen:
        read_procedural_case(
            world.cases,
            world.grants,
            _context(world.land_a),
            case_id=case_b.case_id,
            clock=world.clock,
        )
    unknown_id = uuid4()
    with pytest.raises(ComplianceRecordNotFoundError) as unseen:
        read_procedural_case(
            world.cases, world.grants, _context(world.land_a), case_id=unknown_id, clock=world.clock
        )
    # The two messages differ only by the id the caller already supplied -
    # nothing about existence leaks.
    assert str(seen.value).replace(str(case_b.case_id), "<id>") == str(unseen.value).replace(
        str(unknown_id), "<id>"
    )


def test_bund_gets_no_automatic_access_to_land_records() -> None:
    """There is no hierarchy-derived inheritance: a Bund-level caller is
    just another organization until a Land issues it a grant."""
    world = _world()
    case_a = _open_case(world, world.land_a)
    with pytest.raises(ComplianceRecordNotFoundError):
        read_procedural_case(
            world.cases,
            world.grants,
            _context(world.bund),
            case_id=case_a.case_id,
            clock=world.clock,
        )

    grant = _grant(
        world,
        granting=world.land_a,
        grantee=world.bund,
        capabilities=frozenset({ScopeCapability.READ_CASE}),
    )
    resolved = read_procedural_case(
        world.cases,
        world.grants,
        _context(world.bund, authority_reference_ids=frozenset({grant.grant_id})),
        case_id=case_a.case_id,
        clock=world.clock,
    )
    assert resolved.case_id == case_a.case_id


def test_a_kreis_cannot_modify_a_parent_land_case_without_explicit_authority() -> None:
    world = _world()
    kreis = uuid4()
    case_a = _open_case(world, world.land_a)

    # No authority presented at all: non-disclosing not-found.
    with pytest.raises(ComplianceRecordNotFoundError):
        assign_case_handler(
            world.cases,
            world.roles,
            world.grants,
            world.audit,
            _context(kreis),
            case_id=case_a.case_id,
            handler_party_reference=mint_case_party_reference(),
            assigned_by_party_reference=mint_case_party_reference(),
            clock=world.clock,
        )

    # A grant that exists but carries the wrong capability: an explicit,
    # deterministic refusal, because the caller claimed authority.
    read_only = _grant(
        world,
        granting=world.land_a,
        grantee=kreis,
        capabilities=frozenset({ScopeCapability.READ_CASE}),
    )
    with pytest.raises(CrossScopeAuthorityInvalidError):
        assign_case_handler(
            world.cases,
            world.roles,
            world.grants,
            world.audit,
            _context(kreis, authority_reference_ids=frozenset({read_only.grant_id})),
            case_id=case_a.case_id,
            handler_party_reference=mint_case_party_reference(),
            assigned_by_party_reference=mint_case_party_reference(),
            clock=world.clock,
        )


def test_a_case_can_never_be_opened_into_another_organization() -> None:
    world = _world()
    with pytest.raises(CrossOrganizationCaseAccessDeniedError):
        open_procedural_case(
            world.cases, world.audit, _context(world.land_a), _case(world.land_b), clock=world.clock
        )


def test_a_hold_from_one_organization_cannot_reach_another_organizations_record() -> None:
    world = _world()
    _, record_b = _governed(world, world.land_b, retention_days=0)
    place_legal_hold(
        world.holds,
        world.audit,
        _context(world.land_a),
        hold_id=uuid4(),
        matter_reference="matter/a",
        scope=LegalHoldScope(record_ids=frozenset({record_b.record_id})),
        issued_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=1)
    eligibility = evaluate_disposal_eligibility(
        world.records,
        world.policies,
        world.holds,
        _context(world.land_b),
        record_id=record_b.record_id,
        clock=world.clock,
    )
    assert eligibility.eligible


def test_a_governed_record_cannot_reference_another_organizations_policy() -> None:
    world = _world()
    policy_b = register_retention_policy(
        world.policies, _context(world.land_b), _policy(world.land_b)
    )
    record = replace(_record(policy_b), organization_id=world.land_a)
    with pytest.raises(CrossOrganizationCaseAccessDeniedError):
        register_governed_record(world.records, world.policies, _context(world.land_a), record)


def test_cross_scope_reads_of_the_processing_registry_need_the_matching_capability() -> None:
    world = _world()
    policy_a = register_retention_policy(
        world.policies, _context(world.land_a), _policy(world.land_a)
    )
    activity = register_processing_activity(
        world.activities,
        world.policies,
        world.audit,
        _context(world.land_a),
        _activity(world.land_a, policy_a.policy_id),
        clock=world.clock,
    ).activity

    with pytest.raises(ComplianceRecordNotFoundError):
        read_processing_activity(
            world.activities,
            world.grants,
            _context(world.land_b),
            activity_id=activity.activity_id,
            clock=world.clock,
        )

    wrong = _grant(
        world,
        granting=world.land_a,
        grantee=world.land_b,
        capabilities=frozenset({ScopeCapability.READ_CASE}),
    )
    with pytest.raises(CrossScopeAuthorityInvalidError):
        read_processing_activity(
            world.activities,
            world.grants,
            _context(world.land_b, authority_reference_ids=frozenset({wrong.grant_id})),
            activity_id=activity.activity_id,
            clock=world.clock,
        )

    right = _grant(
        world,
        granting=world.land_a,
        grantee=world.land_b,
        capabilities=frozenset({ScopeCapability.READ_PROCESSING_REGISTRY}),
    )
    resolved = read_processing_activity(
        world.activities,
        world.grants,
        _context(world.land_b, authority_reference_ids=frozenset({right.grant_id})),
        activity_id=activity.activity_id,
        clock=world.clock,
    )
    assert resolved.activity_id == activity.activity_id


# ===========================================================================
# Deadlines
# ===========================================================================


def test_starting_a_deadline_computes_its_due_date_from_the_definition() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    definition = _definition(world, world.land_a, duration_days=10)
    result = start_deadline(
        world.cases,
        world.definitions,
        world.deadlines,
        world.grants,
        world.audit,
        _context(world.land_a),
        case_id=case.case_id,
        definition_id=definition.definition_id,
        deadline_id=uuid4(),
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
        clock=world.clock,
    )
    assert result.deadline.status is DeadlineStatus.RUNNING
    assert result.deadline.timezone == BERLIN
    assert result.deadline.due_at is not None


def _running_deadline(world: World, case: ProceduralCase, *, duration_days: int = 10) -> UUID:
    definition = _definition(world, case.organization_id, duration_days=duration_days)
    deadline_id = uuid4()
    start_deadline(
        world.cases,
        world.definitions,
        world.deadlines,
        world.grants,
        world.audit,
        _context(case.organization_id),
        case_id=case.case_id,
        definition_id=definition.definition_id,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
        clock=world.clock,
    )
    return deadline_id


def test_suspend_resume_extend_and_complete_all_append_to_the_history() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    deadline_id = _running_deadline(world, case)
    context = _context(world.land_a)
    actor = mint_case_party_reference()

    world.clock.at = T0 + timedelta(days=2)
    suspend_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=4)
    resume_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=5)
    extend_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        additional_days=3,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=6)
    final = complete_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    ).deadline

    assert [entry.event_type for entry in final.history] == [
        DeadlineEventType.STARTED,
        DeadlineEventType.SUSPENDED,
        DeadlineEventType.RESUMED,
        DeadlineEventType.EXTENDED,
        DeadlineEventType.SATISFIED,
    ]
    assert final.status is DeadlineStatus.SATISFIED


def test_escalation_and_expiry_are_recorded_as_their_own_history_entries() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    deadline_id = _running_deadline(world, case, duration_days=5)
    context = _context(world.land_a)
    actor = mint_case_party_reference()

    world.clock.at = T0 + timedelta(days=4)
    escalate_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    )
    world.clock.at = T0 + timedelta(days=10)
    expired = expire_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
    ).deadline
    assert expired.status is DeadlineStatus.EXPIRED
    assert [entry.event_type for entry in expired.history] == [
        DeadlineEventType.STARTED,
        DeadlineEventType.ESCALATED,
        DeadlineEventType.EXPIRED,
    ]


def test_a_repeated_deadline_command_replays_instead_of_corrupting_the_history() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    deadline_id = _running_deadline(world, case)
    context = _context(world.land_a)
    actor = mint_case_party_reference()
    event_id = uuid4()

    world.clock.at = T0 + timedelta(days=2)
    first = suspend_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
        event_id=event_id,
    )
    second = suspend_deadline(
        world.deadlines,
        world.grants,
        world.audit,
        context,
        deadline_id=deadline_id,
        reason_code=REASON,
        actor_party_reference=actor,
        clock=world.clock,
        event_id=event_id,
    )
    assert first.deadline.history == second.deadline.history
    assert len(second.deadline.history) == 2


def test_a_second_live_deadline_of_the_same_code_needs_an_explicit_supersession() -> None:
    """Invariant 7: no silent deadline replacement."""
    world = _world()
    case = _open_case(world, world.land_a)
    definition = _definition(world, world.land_a)
    first_id = uuid4()
    context = _context(world.land_a)
    start_deadline(
        world.cases,
        world.definitions,
        world.deadlines,
        world.grants,
        world.audit,
        context,
        case_id=case.case_id,
        definition_id=definition.definition_id,
        deadline_id=first_id,
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
        clock=world.clock,
    )

    with pytest.raises(DeadlineSilentReplacementRejectedError):
        start_deadline(
            world.cases,
            world.definitions,
            world.deadlines,
            world.grants,
            world.audit,
            context,
            case_id=case.case_id,
            definition_id=definition.definition_id,
            deadline_id=uuid4(),
            reason_code=REASON,
            actor_party_reference=mint_case_party_reference(),
            clock=world.clock,
        )

    second_id = uuid4()
    world.clock.at = T0 + timedelta(days=1)
    second = start_deadline(
        world.cases,
        world.definitions,
        world.deadlines,
        world.grants,
        world.audit,
        context,
        case_id=case.case_id,
        definition_id=definition.definition_id,
        deadline_id=second_id,
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
        clock=world.clock,
        supersedes_deadline_id=first_id,
    ).deadline

    predecessor = world.deadlines.get_in_scope(first_id, world.land_a)
    assert predecessor is not None
    assert predecessor.superseded_by_deadline_id == second_id
    assert predecessor.history[-1].event_type is DeadlineEventType.SUPERSEDED
    assert predecessor.history[0].event_type is DeadlineEventType.STARTED
    assert second.supersedes_deadline_id == first_id


def test_the_deadline_store_refuses_a_write_that_would_rewrite_history() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    deadline_id = _running_deadline(world, case)
    stored = world.deadlines.get_in_scope(deadline_id, world.land_a)
    assert stored is not None
    truncated = replace(stored, history=stored.history[:1], deadline_id=stored.deadline_id)
    suspended = stored.suspend(
        T0 + timedelta(days=1),
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    world.deadlines.save(suspended)
    with pytest.raises(ValueError, match="append-only"):
        world.deadlines.save(truncated)


def test_deadlines_are_scoped_to_their_organization() -> None:
    world = _world()
    case = _open_case(world, world.land_a)
    deadline_id = _running_deadline(world, case)
    with pytest.raises(ComplianceRecordNotFoundError):
        suspend_deadline(
            world.deadlines,
            world.grants,
            world.audit,
            _context(world.land_b),
            deadline_id=deadline_id,
            reason_code=REASON,
            actor_party_reference=mint_case_party_reference(),
            clock=world.clock,
        )


# ===========================================================================
# Processing registry
# ===========================================================================


def test_a_processing_activity_requires_a_resolvable_retention_reference() -> None:
    world = _world()
    with pytest.raises(ComplianceRecordNotFoundError):
        register_processing_activity(
            world.activities,
            world.policies,
            world.audit,
            _context(world.land_a),
            _activity(world.land_a, uuid4()),
            clock=world.clock,
        )


def test_a_processing_activity_cannot_reference_another_organizations_policy() -> None:
    world = _world()
    policy_b = register_retention_policy(
        world.policies, _context(world.land_b), _policy(world.land_b)
    )
    with pytest.raises(CrossOrganizationCaseAccessDeniedError):
        register_processing_activity(
            world.activities,
            world.policies,
            world.audit,
            _context(world.land_a),
            _activity(world.land_a, policy_b.policy_id),
            clock=world.clock,
        )


def test_processing_activity_version_and_status_lifecycle() -> None:
    world = _world()
    context = _context(world.land_a)
    policy = register_retention_policy(world.policies, context, _policy(world.land_a))
    activity = register_processing_activity(
        world.activities,
        world.policies,
        world.audit,
        context,
        _activity(world.land_a, policy.policy_id),
        clock=world.clock,
    ).activity

    activated = change_processing_activity_status(
        world.activities,
        world.audit,
        context,
        activity_id=activity.activity_id,
        target_status=RegistryEntryStatus.ACTIVE,
        clock=world.clock,
        expected_activity_version=activity.activity_version,
    ).activity
    assert activated.status is RegistryEntryStatus.ACTIVE
    assert activated.activity_version == activity.activity_version + 1

    deprecated = change_processing_activity_status(
        world.activities,
        world.audit,
        context,
        activity_id=activity.activity_id,
        target_status=RegistryEntryStatus.DEPRECATED,
        clock=world.clock,
    ).activity
    assert deprecated.status is RegistryEntryStatus.DEPRECATED

    with pytest.raises(OptimisticConcurrencyConflictError):
        change_processing_activity_status(
            world.activities,
            world.audit,
            context,
            activity_id=activity.activity_id,
            target_status=RegistryEntryStatus.ACTIVE,
            clock=world.clock,
            expected_activity_version=1,
        )


def test_a_data_asset_requires_a_resolvable_retention_reference() -> None:
    world = _world()
    with pytest.raises(ComplianceRecordNotFoundError):
        register_data_asset(
            world.assets,
            world.policies,
            _context(world.land_a),
            DataAsset(
                asset_id=uuid4(),
                organization_id=world.land_a,
                name="Mitgliederdatenbank",
                asset_class="database",
                system_reference="membership-service",
                record_class="membership.record",
                retention_policy_reference=uuid4(),
                status=RegistryEntryStatus.DRAFT,
                valid_from=T0,
                owner_authority_reference=uuid4(),
            ),
        )


def test_processing_registry_writes_carry_no_identity_payload_into_audit() -> None:
    world = _world()
    context = _context(world.land_a)
    policy = register_retention_policy(world.policies, context, _policy(world.land_a))
    result = register_processing_activity(
        world.activities,
        world.policies,
        world.audit,
        context,
        _activity(world.land_a, policy.policy_id),
        clock=world.clock,
    )
    serialized = str(result.event.payload) + result.audit_event.after_hash
    for forbidden in ("email", "national_id", "date_of_birth", "user_id", "person_id"):
        assert forbidden not in serialized


# ===========================================================================
# Disputes
# ===========================================================================


def _dispute(world: World) -> tuple[ProceduralCase, UUID, UUID, UUID]:
    """An open arbitration case with claimant, respondent and a case
    handler already assigned."""
    authority = mint_case_party_reference()
    case = _open_case(
        world,
        world.land_a,
        case_type=CaseType.PARTY_ARBITRATION,
        procedural_authority_reference=authority,
    )
    claimant = mint_case_party_reference()
    respondent = mint_case_party_reference()
    register_dispute_parties(
        world.cases,
        world.parties,
        world.roles,
        world.grants,
        _context(world.land_a),
        case_id=case.case_id,
        claimant_reference=claimant,
        respondent_reference=respondent,
        registered_by_party_reference=authority,
        clock=world.clock,
    )
    handler = mint_case_party_reference()
    case = assign_case_handler(
        world.cases,
        world.roles,
        world.grants,
        world.audit,
        world_context := _context(world.land_a),
        case_id=case.case_id,
        handler_party_reference=handler,
        assigned_by_party_reference=authority,
        clock=world.clock,
    ).case
    assert world_context.organization_id == world.land_a
    return case, claimant, respondent, handler


def test_a_party_cannot_appoint_themselves_as_independent_decision_maker() -> None:
    world = _world()
    case, claimant, _, _ = _dispute(world)
    declare_conflict_of_interest(
        world.cases,
        world.conflicts,
        world.grants,
        _context(world.land_a),
        case_id=case.case_id,
        party_reference=claimant,
        state=ConflictState.NONE_DECLARED,
        basis_code="none",
        clock=world.clock,
    )
    with pytest.raises(ProceduralIndependenceViolationError):
        assign_independent_decision_maker(
            world.cases,
            world.roles,
            world.conflicts,
            world.grants,
            world.audit,
            _context(world.land_a),
            case_id=case.case_id,
            candidate_party_reference=claimant,
            appointing_party_reference=claimant,
            clock=world.clock,
        )


def test_the_case_handler_cannot_appoint_themselves_as_independent_decision_maker() -> None:
    world = _world()
    case, _, _, handler = _dispute(world)
    declare_conflict_of_interest(
        world.cases,
        world.conflicts,
        world.grants,
        _context(world.land_a),
        case_id=case.case_id,
        party_reference=handler,
        state=ConflictState.NONE_DECLARED,
        basis_code="none",
        clock=world.clock,
    )
    with pytest.raises(ProceduralIndependenceViolationError):
        assign_independent_decision_maker(
            world.cases,
            world.roles,
            world.conflicts,
            world.grants,
            world.audit,
            _context(world.land_a),
            case_id=case.case_id,
            candidate_party_reference=handler,
            appointing_party_reference=handler,
            clock=world.clock,
        )


def test_a_declared_conflict_makes_a_candidate_ineligible() -> None:
    world = _world()
    case, _, _, _ = _dispute(world)
    candidate = mint_case_party_reference()
    declare_conflict_of_interest(
        world.cases,
        world.conflicts,
        world.grants,
        _context(world.land_a),
        case_id=case.case_id,
        party_reference=candidate,
        state=ConflictState.DECLARED,
        basis_code="same_local_branch",
        clock=world.clock,
    )
    with pytest.raises(ConflictOfInterestBlockingError):
        assign_independent_decision_maker(
            world.cases,
            world.roles,
            world.conflicts,
            world.grants,
            world.audit,
            _context(world.land_a),
            case_id=case.case_id,
            candidate_party_reference=candidate,
            appointing_party_reference=case.procedural_authority_reference,
            clock=world.clock,
        )


def test_an_appointment_without_any_declaration_fails_closed() -> None:
    world = _world()
    case, _, _, _ = _dispute(world)
    with pytest.raises(ConflictOfInterestUndeclaredError):
        assign_independent_decision_maker(
            world.cases,
            world.roles,
            world.conflicts,
            world.grants,
            world.audit,
            _context(world.land_a),
            case_id=case.case_id,
            candidate_party_reference=mint_case_party_reference(),
            appointing_party_reference=case.procedural_authority_reference,
            clock=world.clock,
        )


def _decided_dispute(world: World) -> tuple[ProceduralCase, UUID]:
    case, _, _, _ = _dispute(world)
    decision_maker = mint_case_party_reference()
    declare_conflict_of_interest(
        world.cases,
        world.conflicts,
        world.grants,
        _context(world.land_a),
        case_id=case.case_id,
        party_reference=decision_maker,
        state=ConflictState.NONE_DECLARED,
        basis_code="none",
        clock=world.clock,
    )
    case = assign_independent_decision_maker(
        world.cases,
        world.roles,
        world.conflicts,
        world.grants,
        world.audit,
        _context(world.land_a),
        case_id=case.case_id,
        candidate_party_reference=decision_maker,
        appointing_party_reference=case.procedural_authority_reference,
        clock=world.clock,
    ).case
    return case, decision_maker


def test_only_the_assigned_independent_decision_maker_may_decide_a_dispute() -> None:
    world = _world()
    case, decision_maker = _decided_dispute(world)

    with pytest.raises(DecisionAuthorityMissingError):
        record_case_decision(
            world.cases,
            world.decisions,
            world.roles,
            world.conflicts,
            world.grants,
            world.audit,
            _context(world.land_a),
            case_id=case.case_id,
            outcome=DecisionOutcome.DISMISSED,
            decision_reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
            decided_by_party_reference=case.procedural_authority_reference,
            clock=world.clock,
        )

    decided = record_case_decision(
        world.cases,
        world.decisions,
        world.roles,
        world.conflicts,
        world.grants,
        world.audit,
        _context(world.land_a),
        case_id=case.case_id,
        outcome=DecisionOutcome.DISMISSED,
        decision_reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_by_party_reference=decision_maker,
        evidence_references=("pack-11:document:1",),
        clock=world.clock,
    ).case
    assert decided.decision_id is not None


def test_a_closed_case_is_not_modifiable_by_an_ordinary_command() -> None:
    world = _world()
    case, decision_maker = _decided_dispute(world)
    context = _context(world.land_a)
    record_case_decision(
        world.cases,
        world.decisions,
        world.roles,
        world.conflicts,
        world.grants,
        world.audit,
        context,
        case_id=case.case_id,
        outcome=DecisionOutcome.UPHELD,
        decision_reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_by_party_reference=decision_maker,
        clock=world.clock,
    )
    for target in (CaseStatus.ADMISSIBILITY_REVIEW, CaseStatus.ACTIVE, CaseStatus.DECIDED):
        transition_procedural_case(
            world.cases,
            world.grants,
            world.audit,
            context,
            case_id=case.case_id,
            target_status=target,
            clock=world.clock,
        )
    transition_procedural_case(
        world.cases,
        world.grants,
        world.audit,
        context,
        case_id=case.case_id,
        target_status=CaseStatus.CLOSED,
        closure_reason_code="PROCEDURAL_CASE_CLOSED",
        clock=world.clock,
    )

    with pytest.raises(ProceduralCaseClosedError):
        assign_case_handler(
            world.cases,
            world.roles,
            world.grants,
            world.audit,
            context,
            case_id=case.case_id,
            handler_party_reference=mint_case_party_reference(),
            assigned_by_party_reference=mint_case_party_reference(),
            clock=world.clock,
        )


def test_an_appeal_is_a_separate_case_linked_by_reference() -> None:
    world = _world()
    case, decision_maker = _decided_dispute(world)
    context = _context(world.land_a)
    record_case_decision(
        world.cases,
        world.decisions,
        world.roles,
        world.conflicts,
        world.grants,
        world.audit,
        context,
        case_id=case.case_id,
        outcome=DecisionOutcome.UPHELD,
        decision_reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_by_party_reference=decision_maker,
        clock=world.clock,
    )
    for target in (CaseStatus.ADMISSIBILITY_REVIEW, CaseStatus.ACTIVE, CaseStatus.DECIDED):
        transition_procedural_case(
            world.cases,
            world.grants,
            world.audit,
            context,
            case_id=case.case_id,
            target_status=target,
            clock=world.clock,
        )

    appeal_case = _case(world.land_a, case_type=CaseType.PARTY_ARBITRATION)
    reference = file_appeal(
        world.cases,
        world.appeals,
        world.grants,
        context,
        original_case_id=case.case_id,
        appeal_case=appeal_case,
        filed_by_party_reference=mint_case_party_reference(),
        clock=world.clock,
    )
    assert reference.original_case_id == case.case_id
    assert reference.appeal_case_id == appeal_case.case_id
    original = world.cases.get_in_scope(case.case_id, world.land_a)
    assert original is not None
    assert original.status is CaseStatus.DECIDED


def test_cross_scope_dispute_access_is_denied() -> None:
    world = _world()
    case, _, _, _ = _dispute(world)
    with pytest.raises(ComplianceRecordNotFoundError):
        declare_conflict_of_interest(
            world.cases,
            world.conflicts,
            world.grants,
            _context(world.land_b),
            case_id=case.case_id,
            party_reference=mint_case_party_reference(),
            state=ConflictState.NONE_DECLARED,
            basis_code="none",
            clock=world.clock,
        )


# ===========================================================================
# Data-subject requests
# ===========================================================================


def test_a_request_cannot_be_answered_before_identity_verification_succeeds() -> None:
    world = _world()
    context = _context(world.land_a)
    case = _case(world.land_a, case_type=CaseType.DATA_SUBJECT_REQUEST)
    request = intake_data_subject_request(
        world.cases,
        world.requests,
        world.audit,
        context,
        request_id=uuid4(),
        case=case,
        request_type=DataSubjectRequestType.ACCESS,
        requester_party_reference=mint_case_party_reference(),
        scope_description_code="all_membership_data",
        clock=world.clock,
    ).request
    assert request.identity_verification_status is IdentityVerificationStatus.NOT_VERIFIED

    with pytest.raises(IdentityVerificationInsufficientError):
        decide_data_subject_request(
            world.requests,
            world.audit,
            context,
            request_id=request.request_id,
            decision=ResponseDecision.GRANTED,
            limitation_reason_code=None,
            completion_evidence_reference="pack-11:letter:1",
            clock=world.clock,
        )

    set_identity_verification_status(
        world.requests,
        context,
        request_id=request.request_id,
        status=IdentityVerificationStatus.VERIFIED,
        verification_reference=uuid4(),
    )
    advance_data_subject_request(
        world.requests,
        context,
        request_id=request.request_id,
        target_status=DataSubjectRequestStatus.CLASSIFIED,
    )
    advance_data_subject_request(
        world.requests,
        context,
        request_id=request.request_id,
        target_status=DataSubjectRequestStatus.IN_PROGRESS,
    )
    record_search_result_reference(
        world.requests,
        context,
        request_id=request.request_id,
        search_result_reference="search:2026-1",
    )
    answered = decide_data_subject_request(
        world.requests,
        world.audit,
        context,
        request_id=request.request_id,
        decision=ResponseDecision.GRANTED,
        limitation_reason_code=None,
        completion_evidence_reference="pack-11:letter:1",
        clock=world.clock,
    ).request
    assert answered.status is DataSubjectRequestStatus.ANSWERED
    assert answered.search_result_references == ("search:2026-1",)


def test_a_request_from_another_organization_is_not_readable() -> None:
    world = _world()
    case = _case(world.land_a, case_type=CaseType.DATA_SUBJECT_REQUEST)
    request = intake_data_subject_request(
        world.cases,
        world.requests,
        world.audit,
        _context(world.land_a),
        request_id=uuid4(),
        case=case,
        request_type=DataSubjectRequestType.ERASURE,
        requester_party_reference=mint_case_party_reference(),
        scope_description_code="all_membership_data",
        clock=world.clock,
    ).request
    with pytest.raises(ComplianceRecordNotFoundError):
        set_identity_verification_status(
            world.requests,
            _context(world.land_b),
            request_id=request.request_id,
            status=IdentityVerificationStatus.VERIFIED,
            verification_reference=uuid4(),
        )


# ===========================================================================
# Idempotency and audit conventions
# ===========================================================================


def test_every_command_writes_exactly_one_audit_entry_per_event_id() -> None:
    world = _world()
    context = _context(world.land_a)
    case = _case(world.land_a)
    event_id = uuid4()
    first = open_procedural_case(
        world.cases, world.audit, context, case, clock=world.clock, event_id=event_id
    )
    second = open_procedural_case(
        world.cases, world.audit, context, case, clock=world.clock, event_id=event_id
    )
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert len(world.audit.list_by_aggregate("procedural_case", case.case_id)) == 1


def test_audit_entries_record_before_and_after_state_hashes() -> None:
    world = _world()
    context = _context(world.land_a)
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    result = authorize_destruction(
        world.records,
        world.policies,
        world.holds,
        world.authorizations,
        world.audit,
        context,
        record_id=record.record_id,
        authorized_by_authority_reference=uuid4(),
        clock=world.clock,
    )
    assert result.audit_event.before_hash
    assert result.audit_event.after_hash
    assert result.audit_event.before_hash != result.audit_event.after_hash
    assert result.audit_event.source_service == "compliance-service"


def test_the_audit_chain_stays_verifiable_across_a_full_workflow() -> None:
    world = _world()
    _, record = _governed(world, world.land_a, retention_days=30)
    world.clock.at = T0 + timedelta(days=40)
    _authorize_and_destroy(world, world.land_a, record.record_id)
    verification = world.audit.verify_chain()
    assert verification.is_intact
    assert verification.broken_at_index is None
    assert verification.checked_count > 0


def test_a_fixed_clock_is_all_a_command_ever_reads() -> None:
    """No command reaches for system time: driving the whole flow from a
    `FixedClock` produces identical timestamps everywhere."""
    world = _world()
    fixed = FixedClock(T0)
    context = _context(world.land_a)
    policy = register_retention_policy(
        world.policies, context, _policy(world.land_a, retention_days=0)
    )
    record = register_governed_record(world.records, world.policies, context, _record(policy))
    result = record_retention_start(
        world.records,
        world.starts,
        world.audit,
        context,
        record_id=record.record_id,
        trigger_occurred_at=T0,
        source_reference="case:1",
        clock=fixed,
    )
    assert result.audit_event.occurred_at == T0
    assert result.event.occurred_at == T0
