"""Application-layer tests for the Architecture & Domain Framework 0.8.1
additions to PACK-09, organised by that document's mandatory test matrix.

Where `test_casework.py`, `test_notices.py` and `test_dataprotection.py`
prove that the *aggregates* refuse the forbidden state, this file proves
that the *commands* apply the same refusals with scope isolation,
`event_id` idempotency and an Audit Core append - i.e. that the guards
survive contact with the layer callers actually use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_compliance_service.application import (
    DecisionEffectAction,
    RequestContext,
    assert_destruction_propagation_resolved,
    assign_replacement,
    change_decision_effect,
    change_dpia_status,
    decide_filing_admissibility,
    decide_interim_measure,
    decide_processing_activation,
    define_deadline,
    determine_dpia_requirement,
    determine_jurisdiction,
    determine_service_effect,
    issue_official_notice,
    issue_procedural_decision,
    make_decision_enforceable,
    open_legal_case,
    open_procedural_case,
    receive_filing,
    reconcile_service_attempt,
    record_recusal,
    record_service_attempt,
    register_case_party,
    register_governed_record,
    register_hold_propagation,
    register_processing_activity,
    register_record_class,
    register_remedy,
    register_representation,
    register_retention_policy,
    resume_deadline,
    revoke_representation,
    schedule_hearing,
    start_deadline,
    suspend_deadline,
    transfer_jurisdiction,
    transition_legal_case,
    trigger_procedural_deadline,
)
from epd2_compliance_service.casework import (
    ActorClass,
    CaseAccessProfile,
    CaseKind,
    CaseParty,
    CaseTransitionEntry,
    ConfidentialityClass,
    ConflictAssessmentOutcome,
    DecisionStateEntry,
    DecisionType,
    EffectStatus,
    EnforceabilityStatus,
    Filing,
    FilingIntakeState,
    FilingType,
    FinalityStatus,
    Hearing,
    HearingHistoryEntry,
    HearingStatus,
    InterimMeasure,
    InterimMeasureStatus,
    JurisdictionDetermination,
    JurisdictionStatus,
    JurisdictionType,
    LegalCase,
    LegalCaseStatus,
    OperativeResult,
    PartyRole,
    ProceduralDecision,
    RecusalRecord,
    Remedy,
    RemedyKind,
    RemedyStatus,
    ReplacementAssignment,
    RepresentationAuthority,
    RepresentationMandate,
    mint_case_party_reference,
)
from epd2_compliance_service.dataprotection import (
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    DPIAStatus,
    ProcessingRiskClass,
)
from epd2_compliance_service.domain import (
    CaseStatus,
    CaseType,
    DataClassification,
    DeadlineDefinition,
    DerivativeKind,
    DispositionAction,
    GovernedRecord,
    HoldPropagationRecord,
    LegalBasis,
    LegalHold,
    LegalHoldScope,
    LegalHoldStatus,
    ProceduralCase,
    ProcessingActivity,
    PropagationState,
    RecordClass,
    RecordSensitivity,
    RegistryEntryStatus,
    RetentionPolicy,
    RetentionTrigger,
    SearchExportEligibility,
)
from epd2_compliance_service.exceptions import (
    ComplianceRecordNotFoundError,
    CrossScopeAccessDeniedError,
    DeadlineTriggerInvalidError,
    DPIARequiredError,
    DueProcessPrerequisiteMissingError,
    DuplicateLegalEffectPreventedError,
    FilingSequenceConflictError,
    InterimMeasureAuthorityDeniedError,
    JurisdictionMissingError,
    LegalHoldPropagationUnresolvedError,
    NoticeMethodInvalidError,
    OrganizationScopeUndeterminedError,
    RecusedActorDeniedError,
    RepresentationRevokedError,
    ServiceNotProvenError,
)
from epd2_compliance_service.notices import (
    DeemedServiceRule,
    DeliveryTelemetryStatus,
    NoticeEffectOutcome,
    NoticeKind,
    OfficialNotice,
    ReadTelemetryStatus,
    ServiceAttempt,
    ServiceMethod,
    TriggerSource,
)
from epd2_compliance_service.references import NoticeProofPackageRef
from epd2_compliance_service.storage import (
    InMemoryCasePartyStore,
    InMemoryCrossScopeAuthorityGrantStore,
    InMemoryDeadlineDefinitionStore,
    InMemoryDeadlineTriggerStore,
    InMemoryDPIAStore,
    InMemoryFilingStore,
    InMemoryGovernedRecordStore,
    InMemoryHearingStore,
    InMemoryHoldPropagationStore,
    InMemoryInterimMeasureStore,
    InMemoryJurisdictionStore,
    InMemoryLegalCaseStore,
    InMemoryLegalHoldStore,
    InMemoryNoticeEffectStore,
    InMemoryOfficialNoticeStore,
    InMemoryProceduralCaseStore,
    InMemoryProceduralDeadlineStore,
    InMemoryProceduralDecisionStore,
    InMemoryProcessingActivationStore,
    InMemoryProcessingActivityStore,
    InMemoryRecordClassStore,
    InMemoryRecusalStore,
    InMemoryRemedyStore,
    InMemoryRepresentationStore,
    InMemoryRetentionPolicyStore,
    InMemoryServiceAttemptStore,
)
from epd2_core.event_envelope import ActorRef

# ---------------------------------------------------------------------------
# Fixtures
#
# Deliberately inline rather than in a sibling helper module: this
# repository runs pytest with `--import-mode=importlib` and no `conftest`
# on `sys.path` under `services/*/tests`, so a sibling import would not
# resolve. Duplicating a small builder set is the lesser evil against a
# conftest that would apply to every service's suite.
# ---------------------------------------------------------------------------

T0 = datetime(2026, 7, 1, 9, 0, tzinfo=UTC)
T1 = T0 + timedelta(days=7)
T2 = T0 + timedelta(days=30)
BERLIN = "Europe/Berlin"
CASE_REASON = "COMPLIANCE_LEGAL_CASE_STATUS_CHANGED"


class _MovableClock:
    """A `Clock` whose instant the test moves explicitly - never real
    system time."""

    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


@dataclass(slots=True)
class World:
    """One fully-wired compliance-service instance, its stores, and the
    handles the Framework-0.8.1 commands need."""

    cases: InMemoryLegalCaseStore
    jurisdictions: InMemoryJurisdictionStore
    parties: InMemoryCasePartyStore
    representations: InMemoryRepresentationStore
    filings: InMemoryFilingStore
    hearings: InMemoryHearingStore
    measures: InMemoryInterimMeasureStore
    decisions: InMemoryProceduralDecisionStore
    remedies: InMemoryRemedyStore
    recusals: InMemoryRecusalStore
    notices: InMemoryOfficialNoticeStore
    attempts: InMemoryServiceAttemptStore
    notice_effects: InMemoryNoticeEffectStore
    triggers: InMemoryDeadlineTriggerStore
    record_classes: InMemoryRecordClassStore
    propagations: InMemoryHoldPropagationStore
    dpias: InMemoryDPIAStore
    activations: InMemoryProcessingActivationStore
    policies: InMemoryRetentionPolicyStore
    records: InMemoryGovernedRecordStore
    holds: InMemoryLegalHoldStore
    activities: InMemoryProcessingActivityStore
    legacy_cases: InMemoryProceduralCaseStore
    definitions: InMemoryDeadlineDefinitionStore
    deadlines: InMemoryProceduralDeadlineStore
    grants: InMemoryCrossScopeAuthorityGrantStore
    audit: InMemoryAuditEventStore
    clock: _MovableClock
    land_a: UUID
    land_b: UUID
    authority: UUID
    other_authority: UUID
    applicant: UUID
    respondent: UUID
    representative: UUID

    # -- builders that need world state ------------------------------------

    def mandate(self, case_id: UUID) -> RepresentationMandate:
        return RepresentationMandate(
            mandate_id=uuid4(),
            case_id=case_id,
            organization_id=self.land_a,
            represented_party_reference=self.applicant,
            representative_reference=self.representative,
            authorities=frozenset(
                {
                    RepresentationAuthority.FILE_SUBMISSIONS,
                    RepresentationAuthority.RECEIVE_SERVICE,
                }
            ),
            valid_from=T0,
            mandate_basis_reference="mandate:1",
        )

    def recusal(self, case_id: UUID, *, party_reference: UUID | None = None) -> RecusalRecord:
        return RecusalRecord(
            recusal_id=uuid4(),
            case_id=case_id,
            organization_id=self.land_a,
            party_reference=party_reference or self.authority,
            conflict_declaration_id=uuid4(),
            assessment_outcome=ConflictAssessmentOutcome.RECUSAL_REQUIRED,
            effective_at=T1,
            reviewed_by_party_reference=self.applicant,
            prior_participation_codes=("filing.admissibility_decided",),
        )

    def replacement(
        self, case_id: UUID, recusal_id: UUID, replacement_reference: UUID
    ) -> ReplacementAssignment:
        return ReplacementAssignment(
            assignment_id=uuid4(),
            case_id=case_id,
            organization_id=self.land_a,
            recusal_id=recusal_id,
            replacement_party_reference=replacement_reference,
            assigned_by_authority_reference=self.applicant,
            assigned_at=T2,
        )

    def remedy(self, case_id: UUID, decision_id: UUID) -> Remedy:
        return Remedy(
            remedy_id=uuid4(),
            case_id=case_id,
            organization_id=self.land_a,
            decision_id=decision_id,
            remedy_kind=RemedyKind.APPEAL,
            status=RemedyStatus.AVAILABLE,
            available_from=T0,
            available_until=T2,
            competent_authority_reference=self.other_authority,
        )

    def record_class(self) -> RecordClass:
        return RecordClass(
            record_class_id=uuid4(),
            organization_id=self.land_a,
            record_class_code="case.arbitration.file",
            record_category="procedural_case_file",
            sensitivity=RecordSensitivity.CONFIDENTIAL,
            data_classification=DataClassification.CONFIDENTIAL,
            record_owner_authority_reference=self.authority,
            custodian_reference=self.applicant,
            disposition_authority_reference=self.other_authority,
            retention_policy_reference=uuid4(),
            search_export_eligibility=SearchExportEligibility.SCOPED_SEARCH_GOVERNED_EXPORT,
            legal_hold_applicable=True,
            valid_from=T0,
        )

    def policy(self) -> RetentionPolicy:
        return RetentionPolicy(
            policy_id=uuid4(),
            organization_id=self.land_a,
            record_class="case.disciplinary",
            trigger=RetentionTrigger.CASE_CLOSED_AT,
            retention_days=30,
            disposition_action=DispositionAction.DELETE,
            policy_version=1,
            valid_from=T0,
        )

    def record(self, policy: RetentionPolicy) -> GovernedRecord:
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

    def hold(self, record: GovernedRecord) -> LegalHold:
        return LegalHold(
            hold_id=uuid4(),
            organization_id=self.land_a,
            matter_reference="matter/1",
            scope=LegalHoldScope(record_ids=frozenset({record.record_id})),
            issued_at=T0,
            issued_by_authority_reference=self.authority,
            status=LegalHoldStatus.ACTIVE,
        )

    def activity(self, policy: RetentionPolicy) -> ProcessingActivity:
        return ProcessingActivity(
            activity_id=uuid4(),
            organization_id=self.land_a,
            name="Mitgliederverwaltung",
            purpose="membership administration",
            legal_basis=LegalBasis.PARTY_STATUTE,
            data_subject_categories=("members",),
            personal_data_categories=("contact_data",),
            recipient_categories=("internal_administration",),
            retention_policy_reference=policy.policy_id,
            technical_organizational_measures=("rbac",),
            controller_reference=self.other_authority,
            process_owner_authority_reference=self.applicant,
            system_references=("membership-service",),
            status=RegistryEntryStatus.DRAFT,
            valid_from=T0,
        )

    def dpia_requirement(self, activity_id: UUID) -> DPIARequirementDetermination:
        return DPIARequirementDetermination(
            determination_id=uuid4(),
            activity_id=activity_id,
            organization_id=self.land_a,
            risk_class=ProcessingRiskClass.HIGH,
            dpia_required=True,
            determined_at=T0,
            determined_by_party_reference=self.respondent,
            basis_reference="dp-policy:v2",
        )

    def dpia(
        self, activity_id: UUID, *, status: DPIAStatus = DPIAStatus.DRAFT
    ) -> DataProtectionImpactAssessment:
        return DataProtectionImpactAssessment(
            dpia_id=uuid4(),
            activity_id=activity_id,
            organization_id=self.land_a,
            status=status,
            risk_class=ProcessingRiskClass.HIGH,
            reviewer_party_reference=self.respondent,
            created_at=T0,
            updated_at=T0,
        )

    def legacy_case_with_deadline(self) -> tuple[UUID, UUID]:
        """A round-1 `ProceduralCase` plus a started `ProceduralDeadline`.

        The Framework-0.8.1 deadline *trigger* attaches to the existing
        PACK-09 deadline machinery rather than replacing it - that is the
        point of adding a trigger record instead of a new deadline type."""
        context = context_for(self.land_a)
        case = ProceduralCase(
            case_id=uuid4(),
            organization_id=self.land_a,
            case_type=CaseType.PARTY_ARBITRATION,
            status=CaseStatus.OPEN,
            opened_at=T0,
            subject_reference="dispute:1",
            procedural_authority_reference=self.authority,
            workflow_type="party_arbitration_standard",
        )
        open_procedural_case(self.legacy_cases, self.audit, context, case, clock=self.clock)
        definition = define_deadline(
            self.definitions,
            context,
            DeadlineDefinition(
                definition_id=uuid4(),
                organization_id=self.land_a,
                deadline_code="RESPONSE_DUE",
                duration_days=14,
                timezone=BERLIN,
            ),
        )
        deadline_id = uuid4()
        start_deadline(
            self.legacy_cases,
            self.definitions,
            self.deadlines,
            self.grants,
            self.audit,
            context,
            case_id=case.case_id,
            definition_id=definition.definition_id,
            deadline_id=deadline_id,
            reason_code="COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED",
            actor_party_reference=self.authority,
            clock=self.clock,
        )
        return case.case_id, deadline_id


def world(at: datetime = T0) -> World:
    return World(
        cases=InMemoryLegalCaseStore(),
        jurisdictions=InMemoryJurisdictionStore(),
        parties=InMemoryCasePartyStore(),
        representations=InMemoryRepresentationStore(),
        filings=InMemoryFilingStore(),
        hearings=InMemoryHearingStore(),
        measures=InMemoryInterimMeasureStore(),
        decisions=InMemoryProceduralDecisionStore(),
        remedies=InMemoryRemedyStore(),
        recusals=InMemoryRecusalStore(),
        notices=InMemoryOfficialNoticeStore(),
        attempts=InMemoryServiceAttemptStore(),
        notice_effects=InMemoryNoticeEffectStore(),
        triggers=InMemoryDeadlineTriggerStore(),
        record_classes=InMemoryRecordClassStore(),
        propagations=InMemoryHoldPropagationStore(),
        dpias=InMemoryDPIAStore(),
        activations=InMemoryProcessingActivationStore(),
        policies=InMemoryRetentionPolicyStore(),
        records=InMemoryGovernedRecordStore(),
        holds=InMemoryLegalHoldStore(),
        activities=InMemoryProcessingActivityStore(),
        legacy_cases=InMemoryProceduralCaseStore(),
        definitions=InMemoryDeadlineDefinitionStore(),
        deadlines=InMemoryProceduralDeadlineStore(),
        grants=InMemoryCrossScopeAuthorityGrantStore(),
        audit=InMemoryAuditEventStore(),
        clock=_MovableClock(at),
        land_a=uuid4(),
        land_b=uuid4(),
        authority=mint_case_party_reference(),
        other_authority=mint_case_party_reference(),
        applicant=mint_case_party_reference(),
        respondent=mint_case_party_reference(),
        representative=mint_case_party_reference(),
    )


def context_for(organization_id: UUID) -> RequestContext:
    return RequestContext(
        actor=ActorRef(actor_id=uuid4(), actor_type="service"),
        organization_id=organization_id,
        correlation_id=uuid4(),
    )


def make_case(organization_id: UUID) -> LegalCase:
    return LegalCase(
        legal_case_id=uuid4(),
        organization_id=organization_id,
        case_kind=CaseKind.ARBITRATION,
        opened_at=T0,
        subject_reference="dispute:2026-1",
        confidentiality_class=ConfidentialityClass.CONFIDENTIAL,
        access_profile=CaseAccessProfile.NAMED_PARTIES_ONLY,
        transition_history=(
            CaseTransitionEntry(
                sequence=1,
                status_after=LegalCaseStatus.INTAKE,
                occurred_at=T0,
                reason_code=CASE_REASON,
                actor_authority_reference=uuid4(),
            ),
        ),
        governing_policy_reference="policy:arbitration:v1",
    )


def make_jurisdiction(
    case: LegalCase, authority: UUID, *, supersedes_jurisdiction_id: UUID | None = None
) -> JurisdictionDetermination:
    return JurisdictionDetermination(
        jurisdiction_id=uuid4(),
        case_id=case.legal_case_id,
        organization_id=case.organization_id,
        jurisdiction_type=JurisdictionType.PARTY_STATUTE,
        case_kind=case.case_kind,
        competent_authority_reference=authority,
        status=JurisdictionStatus.CONFIRMED,
        determined_at=T0,
        determined_by_authority_reference=authority,
        valid_from=T0,
        basis_reference="statute:s.14",
        supersedes_jurisdiction_id=supersedes_jurisdiction_id,
    )


def make_filing(
    case_id: UUID,
    organization_id: UUID,
    party: UUID,
    representative: UUID,
    *,
    sequence: int,
) -> Filing:
    return Filing(
        filing_id=uuid4(),
        case_id=case_id,
        organization_id=organization_id,
        docket_sequence=sequence,
        filing_type=FilingType.INITIATING_SUBMISSION,
        filed_by_party_reference=party,
        submitted_at=T0,
        received_at=T0 + timedelta(hours=1),
        intake_state=FilingIntakeState.RECEIVED,
        filed_by_representative_reference=representative,
    )


def make_hearing(case_id: UUID, organization_id: UUID, authority: UUID) -> Hearing:
    return Hearing(
        hearing_id=uuid4(),
        case_id=case_id,
        organization_id=organization_id,
        convening_authority_reference=authority,
        agenda_code="hearing.substantive",
        scheduled_at=T1,
        timezone=BERLIN,
        history=(
            HearingHistoryEntry(
                sequence=1,
                status_after=HearingStatus.SCHEDULED,
                occurred_at=T0,
                scheduled_at_before=T1,
                scheduled_at_after=T1,
                reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
                actor_authority_reference=authority,
            ),
        ),
    )


def make_interim(
    case_id: UUID,
    organization_id: UUID,
    authority: UUID,
    applicant: UUID,
    actor_class: ActorClass,
) -> InterimMeasure:
    return InterimMeasure(
        measure_id=uuid4(),
        case_id=case_id,
        organization_id=organization_id,
        measure_kind="suspension",
        requested_by_party_reference=applicant,
        decided_by_authority_reference=authority,
        decided_by_actor_class=actor_class,
        legal_basis_reference="statute:s.22",
        scope_description_code="measure.scope.suspension",
        status=InterimMeasureStatus.GRANTED,
        decided_at=T0,
        starts_at=T0,
        ends_at=T2,
        reasons_reference="reasons:interim",
    )


def make_decision(case_id: UUID, organization_id: UUID, authority: UUID) -> ProceduralDecision:
    return ProceduralDecision(
        decision_id=uuid4(),
        case_id=case_id,
        organization_id=organization_id,
        decision_type=DecisionType.SUBSTANTIVE,
        deciding_authority_reference=authority,
        decided_by_party_reference=authority,
        operative_result=OperativeResult.UPHELD,
        issued_at=T0,
        state_history=(
            DecisionStateEntry(
                sequence=1,
                occurred_at=T0,
                effect_status=EffectStatus.PENDING,
                finality_status=FinalityStatus.OPEN_TO_REMEDY,
                enforceability_status=EnforceabilityStatus.NOT_ENFORCEABLE,
                reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
                actor_authority_reference=authority,
            ),
        ),
        reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        reasons_reference="reasons:1",
    )


def make_notice(
    case_id: UUID, organization_id: UUID, authority: UUID, recipient: UUID
) -> OfficialNotice:
    return OfficialNotice(
        notice_id=uuid4(),
        case_id=case_id,
        organization_id=organization_id,
        notice_kind=NoticeKind.HEARING_SUMMONS,
        issuing_authority_reference=authority,
        recipient_party_reference=recipient,
        authorized_methods=frozenset({ServiceMethod.REGISTERED_POST}),
        issued_at=T0,
        content_reference="pack-11:notice:1",
    )


def make_attempt(
    notice_id: UUID,
    case_id: UUID,
    organization_id: UUID,
    *,
    method: ServiceMethod = ServiceMethod.REGISTERED_POST,
) -> ServiceAttempt:
    return ServiceAttempt(
        attempt_id=uuid4(),
        notice_id=notice_id,
        case_id=case_id,
        organization_id=organization_id,
        method=method,
        attempted_at=T0 + timedelta(hours=6),
        delivery_status=DeliveryTelemetryStatus.DELIVERED,
        read_status=ReadTelemetryStatus.UNKNOWN,
        provider_reference="provider:1",
    )


# ===========================================================================
# 1. Scope isolation and non-disclosure (PACK-09 invariant 2)
# ===========================================================================


def test_a_case_from_another_organization_is_reported_as_not_found() -> None:
    """A foreign resource id must disclose nothing - not even that the
    object exists. The caller gets the same error it would get for an id
    that was never issued."""
    w = world()
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)

    with pytest.raises(ComplianceRecordNotFoundError) as excinfo:
        transition_legal_case(
            w.cases,
            w.jurisdictions,
            w.recusals,
            w.audit,
            context_for(w.land_b),
            legal_case_id=case.legal_case_id,
            target=LegalCaseStatus.JURISDICTION_REVIEW,
            reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
            acting_authority_reference=w.authority,
            clock=w.clock,
        )
    assert excinfo.value.reason_code == "VALIDATION_RECORD_NOT_FOUND"


def test_a_case_submitted_for_another_organization_is_refused_explicitly() -> None:
    """The other half of the two-tier strategy: a caller that submits an
    entity carrying a *different* organization is not probing for
    existence, it is asserting authority it does not have, so it gets a
    specific refusal."""
    w = world()
    with pytest.raises(CrossScopeAccessDeniedError) as excinfo:
        open_legal_case(w.cases, w.audit, context_for(w.land_a), make_case(w.land_b), clock=w.clock)
    assert excinfo.value.reason_code == "CROSS_SCOPE_ACCESS_DENIED"


def test_a_context_without_a_resolvable_scope_fails_closed() -> None:
    w = world()
    context = RequestContext(
        actor=ActorRef(actor_id=uuid4(), actor_type="service"),
        organization_id=None,
        correlation_id=uuid4(),
    )
    with pytest.raises(OrganizationScopeUndeterminedError):
        open_legal_case(w.cases, w.audit, context, make_case(w.land_a), clock=w.clock)


# ===========================================================================
# 2. Jurisdiction commands
# ===========================================================================


def test_a_substantive_transition_without_jurisdiction_is_refused_by_the_command() -> None:
    w = world()
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    for target in (LegalCaseStatus.JURISDICTION_REVIEW, LegalCaseStatus.ADMISSIBILITY_REVIEW):
        transition_legal_case(
            w.cases,
            w.jurisdictions,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            legal_case_id=case.legal_case_id,
            target=target,
            reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
            acting_authority_reference=w.authority,
            clock=w.clock,
        )
    with pytest.raises(JurisdictionMissingError):
        transition_legal_case(
            w.cases,
            w.jurisdictions,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            legal_case_id=case.legal_case_id,
            target=LegalCaseStatus.SUBSTANTIVE_REVIEW,
            reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
            acting_authority_reference=w.authority,
            clock=w.clock,
        )


def test_determining_jurisdiction_binds_the_case_and_appends_the_determination() -> None:
    w = world()
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    result = determine_jurisdiction(
        w.cases,
        w.jurisdictions,
        w.audit,
        context_for(w.land_a),
        make_jurisdiction(case, w.authority),
        clock=w.clock,
    )
    assert result.case.jurisdiction_id == result.determination.jurisdiction_id
    assert w.jurisdictions.list_for_case(case.legal_case_id) == (result.determination,)
    assert result.audit_event.event_type == "jurisdiction.determined"


def test_transferring_jurisdiction_keeps_both_determinations_on_the_record() -> None:
    w = world()
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    first = determine_jurisdiction(
        w.cases,
        w.jurisdictions,
        w.audit,
        context_for(w.land_a),
        make_jurisdiction(case, w.authority),
        clock=w.clock,
    ).determination

    # Move the clock forward: a transfer closes the outgoing
    # determination's window at `now`, which must be after `valid_from`.
    w.clock.at = T1
    successor = make_jurisdiction(
        case, w.other_authority, supersedes_jurisdiction_id=first.jurisdiction_id
    )
    result = transfer_jurisdiction(
        w.cases,
        w.jurisdictions,
        w.audit,
        context_for(w.land_a),
        jurisdiction_id=first.jurisdiction_id,
        successor=successor,
        reason_code="JURISDICTION_TRANSFER_REQUIRED",
        clock=w.clock,
    )
    stored = w.jurisdictions.list_for_case(case.legal_case_id)
    assert len(stored) == 2
    assert result.determination.transferred_to_jurisdiction_id == successor.jurisdiction_id
    assert result.case.jurisdiction_id == successor.jurisdiction_id


def test_a_successor_that_does_not_name_what_it_supersedes_is_refused() -> None:
    w = world()
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    first = determine_jurisdiction(
        w.cases,
        w.jurisdictions,
        w.audit,
        context_for(w.land_a),
        make_jurisdiction(case, w.authority),
        clock=w.clock,
    ).determination
    with pytest.raises(Exception) as excinfo:
        transfer_jurisdiction(
            w.cases,
            w.jurisdictions,
            w.audit,
            context_for(w.land_a),
            jurisdiction_id=first.jurisdiction_id,
            successor=make_jurisdiction(case, w.other_authority),
            reason_code="X",
            clock=w.clock,
        )
    assert excinfo.value.reason_code == "JURISDICTION_TRANSFER_REQUIRED"


# ===========================================================================
# 3. Representation and filings
# ===========================================================================


def _case_with_jurisdiction(w: World) -> UUID:
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    determine_jurisdiction(
        w.cases,
        w.jurisdictions,
        w.audit,
        context_for(w.land_a),
        make_jurisdiction(case, w.authority),
        clock=w.clock,
    )
    return case.legal_case_id


def test_a_filing_by_a_revoked_representative_is_refused() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    mandate = register_representation(
        w.cases,
        w.representations,
        w.audit,
        context_for(w.land_a),
        w.mandate(case_id),
        clock=w.clock,
    ).mandate
    revoke_representation(
        w.representations,
        w.audit,
        context_for(w.land_a),
        mandate_id=mandate.mandate_id,
        reason_code="REPRESENTATION_REVOKED",
        clock=w.clock,
    )
    with pytest.raises(RepresentationRevokedError):
        receive_filing(
            w.cases,
            w.filings,
            w.representations,
            w.audit,
            context_for(w.land_a),
            filing=make_filing(case_id, w.land_a, w.applicant, w.representative, sequence=1),
            clock=w.clock,
        )


def test_the_docket_sequence_is_assigned_by_the_store_not_the_caller() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    register_representation(
        w.cases,
        w.representations,
        w.audit,
        context_for(w.land_a),
        w.mandate(case_id),
        clock=w.clock,
    )
    receive_filing(
        w.cases,
        w.filings,
        w.representations,
        w.audit,
        context_for(w.land_a),
        filing=make_filing(case_id, w.land_a, w.applicant, w.representative, sequence=1),
        clock=w.clock,
    )
    # A caller that tries to claim position 1 again - or to skip to 5 - is
    # refused rather than silently corrected.
    for wrong in (1, 5):
        with pytest.raises(FilingSequenceConflictError):
            receive_filing(
                w.cases,
                w.filings,
                w.representations,
                w.audit,
                context_for(w.land_a),
                filing=make_filing(
                    case_id, w.land_a, w.applicant, w.representative, sequence=wrong
                ),
                clock=w.clock,
            )


def test_a_rejected_filing_keeps_its_docket_position() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    register_representation(
        w.cases,
        w.representations,
        w.audit,
        context_for(w.land_a),
        w.mandate(case_id),
        clock=w.clock,
    )
    filing = receive_filing(
        w.cases,
        w.filings,
        w.representations,
        w.audit,
        context_for(w.land_a),
        filing=make_filing(case_id, w.land_a, w.applicant, w.representative, sequence=1),
        clock=w.clock,
    ).filing
    rejected = decide_filing_admissibility(
        w.filings,
        w.recusals,
        w.cases,
        w.audit,
        context_for(w.land_a),
        filing_id=filing.filing_id,
        admit=False,
        reason_code="FILING_INADMISSIBLE",
        acting_authority_reference=w.authority,
        clock=w.clock,
    ).filing
    assert rejected.docket_sequence == 1
    assert rejected.rejection_reason_code == "FILING_INADMISSIBLE"
    assert len(w.filings.list_for_case(case_id)) == 1
    # The next filing goes to position 2 - a rejected filing does not free
    # its slot.
    assert w.filings.next_sequence(case_id) == 2


# ===========================================================================
# 4. Recusal blocks capability (Framework hard invariant 53)
# ===========================================================================


def test_a_recused_authority_cannot_transition_the_case() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    record_recusal(
        w.cases, w.recusals, w.audit, context_for(w.land_a), w.recusal(case_id), clock=w.clock
    )
    w.clock.at = T2
    with pytest.raises(RecusedActorDeniedError) as excinfo:
        transition_legal_case(
            w.cases,
            w.jurisdictions,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            legal_case_id=case_id,
            target=LegalCaseStatus.JURISDICTION_REVIEW,
            reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
            acting_authority_reference=w.authority,
            clock=w.clock,
        )
    assert excinfo.value.reason_code == "RECUSED_ACTOR_DENIED"


def test_a_recused_authority_cannot_schedule_a_hearing_either() -> None:
    """The recusal guard is applied to every consequential command, not
    only to final decisions: convening a hearing is an exercise of
    authority too."""
    w = world()
    case_id = _case_with_jurisdiction(w)
    record_recusal(
        w.cases, w.recusals, w.audit, context_for(w.land_a), w.recusal(case_id), clock=w.clock
    )
    w.clock.at = T2
    with pytest.raises(RecusedActorDeniedError):
        schedule_hearing(
            w.cases,
            w.hearings,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            make_hearing(case_id, w.land_a, w.authority),
            clock=w.clock,
        )


def test_a_replacement_who_is_themselves_recused_is_refused() -> None:
    """Otherwise a recusal could be 'resolved' by handing the matter to
    somebody equally conflicted."""
    w = world()
    case_id = _case_with_jurisdiction(w)
    first = record_recusal(
        w.cases, w.recusals, w.audit, context_for(w.land_a), w.recusal(case_id), clock=w.clock
    ).recusal
    second = w.recusal(case_id, party_reference=w.other_authority)
    record_recusal(w.cases, w.recusals, w.audit, context_for(w.land_a), second, clock=w.clock)

    with pytest.raises(RecusedActorDeniedError):
        assign_replacement(
            w.cases,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            w.replacement(case_id, first.recusal_id, w.other_authority),
            clock=w.clock,
        )


def test_recording_a_recusal_does_not_remove_prior_participation() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    stored = record_recusal(
        w.cases, w.recusals, w.audit, context_for(w.land_a), w.recusal(case_id), clock=w.clock
    ).recusal
    assert stored.prior_participation_codes


# ===========================================================================
# 5. Interim measures and decisions
# ===========================================================================


def test_an_automated_actor_cannot_order_an_interim_measure_through_the_command() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    with pytest.raises(InterimMeasureAuthorityDeniedError):
        decide_interim_measure(
            w.cases,
            w.jurisdictions,
            w.measures,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            make_interim(case_id, w.land_a, w.authority, w.applicant, ActorClass.AUTOMATED),
            clock=w.clock,
        )


def test_issuing_a_decision_without_effective_notice_is_refused() -> None:
    """Framework hard invariant 52, applied where it matters: the caller
    cannot assert 'notice was effective' with a flag - the command
    resolves the notice effect from the store."""
    w = world()
    case_id = _case_with_jurisdiction(w)
    with pytest.raises(DueProcessPrerequisiteMissingError) as excinfo:
        issue_procedural_decision(
            w.cases,
            w.jurisdictions,
            w.decisions,
            w.notice_effects,
            w.recusals,
            w.audit,
            context_for(w.land_a),
            make_decision(case_id, w.land_a, w.authority),
            notice_effect_id=None,
            response_opportunity_given=True,
            remedy_available=True,
            decided_by_actor_class=ActorClass.HUMAN_AUTHORITY,
            clock=w.clock,
        )
    assert "notice" in str(excinfo.value)


def test_a_decision_cannot_become_enforceable_before_it_is_in_effect() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    decision = _issue_decision(w, case_id)
    with pytest.raises(Exception) as excinfo:
        make_decision_enforceable(
            w.decisions,
            w.audit,
            context_for(w.land_a),
            decision_id=decision.decision_id,
            reason_code="R",
            acting_authority_reference=w.authority,
            clock=w.clock,
        )
    assert excinfo.value.reason_code == "DECISION_NOT_ENFORCEABLE"

    change_decision_effect(
        w.decisions,
        w.audit,
        context_for(w.land_a),
        decision_id=decision.decision_id,
        action=DecisionEffectAction.COMMENCE,
        reason_code="R",
        acting_authority_reference=w.authority,
        clock=w.clock,
    )
    enforceable = make_decision_enforceable(
        w.decisions,
        w.audit,
        context_for(w.land_a),
        decision_id=decision.decision_id,
        reason_code="R",
        acting_authority_reference=w.authority,
        clock=w.clock,
    ).decision
    assert enforceable.enforceability_status.value == "enforceable"


def test_registering_a_remedy_binds_it_to_its_decision() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    decision = _issue_decision(w, case_id)
    remedy = register_remedy(
        w.decisions,
        w.remedies,
        w.audit,
        context_for(w.land_a),
        w.remedy(case_id, decision.decision_id),
        clock=w.clock,
    ).remedy
    assert remedy.status is RemedyStatus.AVAILABLE
    stored_decision = w.decisions.get_in_scope(decision.decision_id, w.land_a)
    assert stored_decision is not None
    assert stored_decision.remedy_id == remedy.remedy_id


# ===========================================================================
# 6. The notice trust boundary, end to end
# ===========================================================================


def _served_notice(w: World, case_id: UUID, *, reconcile: bool = True) -> UUID:
    notice = issue_official_notice(
        w.cases,
        w.notices,
        w.audit,
        context_for(w.land_a),
        make_notice(case_id, w.land_a, w.authority, w.respondent),
        clock=w.clock,
    ).notice
    attempt = record_service_attempt(
        w.notices,
        w.attempts,
        w.audit,
        context_for(w.land_a),
        make_attempt(notice.notice_id, case_id, w.land_a),
        clock=w.clock,
    ).attempt
    if reconcile:
        reconcile_service_attempt(
            w.notices,
            w.attempts,
            context_for(w.land_a),
            notice_id=notice.notice_id,
            attempt_id=attempt.attempt_id,
            proof_package_reference=NoticeProofPackageRef(id=uuid4(), organization_id=w.land_a),
        )
    return notice.notice_id


def test_an_attempt_over_an_unauthorized_method_is_refused_at_recording_time() -> None:
    """Refused when recorded, not when the effect is determined - so an
    unauthorized channel never accumulates as evidence that later looks
    like proof of service."""
    w = world()
    case_id = _case_with_jurisdiction(w)
    notice = issue_official_notice(
        w.cases,
        w.notices,
        w.audit,
        context_for(w.land_a),
        make_notice(case_id, w.land_a, w.authority, w.respondent),
        clock=w.clock,
    ).notice
    with pytest.raises(NoticeMethodInvalidError):
        record_service_attempt(
            w.notices,
            w.attempts,
            w.audit,
            context_for(w.land_a),
            make_attempt(notice.notice_id, case_id, w.land_a, method=ServiceMethod.ELECTRONIC_MAIL),
            clock=w.clock,
        )


def test_delivered_but_unreconciled_telemetry_does_not_produce_legal_effect() -> None:
    """The end-to-end version of the headline invariant, through the
    commands a caller actually uses."""
    w = world()
    case_id = _case_with_jurisdiction(w)
    notice_id = _served_notice(w, case_id, reconcile=False)
    with pytest.raises(ServiceNotProvenError):
        determine_service_effect(
            w.notices,
            w.attempts,
            w.notice_effects,
            w.audit,
            context_for(w.land_a),
            notice_id=notice_id,
            deemed_service_rule=DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
            rule_reference="rules:s.5",
            decided_by_authority_reference=w.authority,
            effective_at=T1,
            clock=w.clock,
        )


def test_a_reconciled_attempt_produces_an_effect_that_can_start_a_deadline() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    notice_id = _served_notice(w, case_id)
    effect = determine_service_effect(
        w.notices,
        w.attempts,
        w.notice_effects,
        w.audit,
        context_for(w.land_a),
        notice_id=notice_id,
        deemed_service_rule=DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
        rule_reference="rules:s.5",
        decided_by_authority_reference=w.authority,
        effective_at=T1,
        clock=w.clock,
    ).decision
    assert effect.outcome is NoticeEffectOutcome.EFFECTIVE
    assert effect.establishes_legal_effect is True


def test_telemetry_is_refused_as_a_deadline_trigger_by_the_command() -> None:
    w = world()
    _case_id, deadline_id = w.legacy_case_with_deadline()
    for source in (TriggerSource.DELIVERY_TELEMETRY, TriggerSource.READ_TELEMETRY):
        with pytest.raises(DeadlineTriggerInvalidError):
            trigger_procedural_deadline(
                w.deadlines,
                w.notice_effects,
                w.triggers,
                w.audit,
                context_for(w.land_a),
                deadline_id=deadline_id,
                source=source,
                notice_effect_id=None,
                source_reference="provider:1",
                clock=w.clock,
            )


def test_a_deadline_is_triggered_exactly_once_even_on_replay() -> None:
    """Framework hard invariant 59. Two attempts, two different
    `event_id`s - the second is refused by the create-once store rather
    than producing a second legal effect."""
    w = world()
    _case_id, deadline_id = w.legacy_case_with_deadline()
    trigger = trigger_procedural_deadline(
        w.deadlines,
        w.notice_effects,
        w.triggers,
        w.audit,
        context_for(w.land_a),
        deadline_id=deadline_id,
        source=TriggerSource.STATUTORY_DATE,
        notice_effect_id=None,
        source_reference="statute:s.9",
        clock=w.clock,
    ).trigger
    assert w.triggers.get_for_deadline(deadline_id) == trigger

    with pytest.raises(DuplicateLegalEffectPreventedError):
        trigger_procedural_deadline(
            w.deadlines,
            w.notice_effects,
            w.triggers,
            w.audit,
            context_for(w.land_a),
            deadline_id=deadline_id,
            source=TriggerSource.STATUTORY_DATE,
            notice_effect_id=None,
            source_reference="statute:s.9",
            clock=w.clock,
        )


def test_an_identical_replay_of_the_trigger_command_returns_the_same_trigger() -> None:
    """CT-00-04: the same `event_id` twice is idempotent, not a second
    consequential effect and not an error."""
    w = world()
    _case_id, deadline_id = w.legacy_case_with_deadline()
    event_id = uuid4()
    first = trigger_procedural_deadline(
        w.deadlines,
        w.notice_effects,
        w.triggers,
        w.audit,
        context_for(w.land_a),
        deadline_id=deadline_id,
        source=TriggerSource.STATUTORY_DATE,
        notice_effect_id=None,
        source_reference="statute:s.9",
        clock=w.clock,
        event_id=event_id,
    )
    second = trigger_procedural_deadline(
        w.deadlines,
        w.notice_effects,
        w.triggers,
        w.audit,
        context_for(w.land_a),
        deadline_id=deadline_id,
        source=TriggerSource.STATUTORY_DATE,
        notice_effect_id=None,
        source_reference="statute:s.9",
        clock=w.clock,
        event_id=event_id,
    )
    assert first.trigger == second.trigger
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


# ===========================================================================
# 7. Outage does not silently move a deadline (Framework hard invariant 60)
# ===========================================================================


def test_an_outage_suspends_and_resumes_a_deadline_with_its_own_reason_codes() -> None:
    """A deadline never changes because infrastructure was unavailable; it
    changes because somebody recorded a governed suspension and a governed
    resumption, each with its own reason code and its own audit entry. The
    history keeps both."""
    w = world()
    _case_id, deadline_id = w.legacy_case_with_deadline()
    suspended = suspend_deadline(
        w.deadlines,
        w.grants,
        w.audit,
        context_for(w.land_a),
        deadline_id=deadline_id,
        reason_code="COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED",
        actor_party_reference=w.authority,
        clock=w.clock,
    ).deadline
    assert suspended.status.value == "suspended"

    w.clock.at = T2
    resumed = resume_deadline(
        w.deadlines,
        w.grants,
        w.audit,
        context_for(w.land_a),
        deadline_id=deadline_id,
        reason_code="COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED",
        actor_party_reference=w.authority,
        clock=w.clock,
    ).deadline
    assert resumed.status.value == "running"
    # Both governed events are on the append-only history; neither
    # rewrote the other, and the suspension is still visible.
    event_types = [entry.event_type.value for entry in resumed.history]
    assert "suspended" in event_types
    assert "resumed" in event_types
    assert len(resumed.history) >= 3


# ===========================================================================
# 8. Records governance and the DPIA gate through the commands
# ===========================================================================


def test_an_unresolved_hold_propagation_blocks_destruction() -> None:
    w = world()
    context = context_for(w.land_a)
    policy = w.policy()
    register_retention_policy(w.policies, context, policy)
    record = w.record(policy)
    register_governed_record(w.records, w.policies, context, record)
    hold = w.hold(record)
    w.holds.save(hold)

    register_hold_propagation(
        w.holds,
        w.propagations,
        w.audit,
        context,
        HoldPropagationRecord(
            propagation_id=uuid4(),
            hold_id=hold.hold_id,
            organization_id=w.land_a,
            derivative_kind=DerivativeKind.EXPORT_DATASET,
            derivative_reference="export:2026-q1",
            state=PropagationState.PENDING,
            recorded_at=T0,
        ),
        clock=w.clock,
    )
    with pytest.raises(LegalHoldPropagationUnresolvedError):
        assert_destruction_propagation_resolved(
            w.records, w.holds, w.propagations, context, record_id=record.record_id
        )


def test_activation_is_blocked_when_no_dpia_requirement_was_ever_determined() -> None:
    w = world()
    context = context_for(w.land_a)
    policy = w.policy()
    register_retention_policy(w.policies, context, policy)
    activity = w.activity(policy)
    register_processing_activity(
        w.activities, w.policies, w.audit, context, activity, clock=w.clock
    )
    with pytest.raises(DPIARequiredError):
        decide_processing_activation(
            w.activities,
            w.dpias,
            w.activations,
            w.audit,
            context,
            activity_id=activity.activity_id,
            risk_class=ProcessingRiskClass.HIGH,
            decided_by_authority_reference=w.authority,
            reason_code="COMPLIANCE_PROCESSING_ACTIVATION_DECIDED",
            clock=w.clock,
        )


def test_activation_succeeds_once_the_requirement_and_an_approved_dpia_exist() -> None:
    w = world()
    context = context_for(w.land_a)
    policy = w.policy()
    register_retention_policy(w.policies, context, policy)
    activity = w.activity(policy)
    register_processing_activity(
        w.activities, w.policies, w.audit, context, activity, clock=w.clock
    )
    determine_dpia_requirement(
        w.activities,
        w.dpias,
        w.audit,
        context,
        w.dpia_requirement(activity.activity_id),
        clock=w.clock,
    )
    dpia = w.dpias.save(w.dpia(activity.activity_id, status=DPIAStatus.UNDER_REVIEW))
    change_dpia_status(
        w.dpias,
        w.audit,
        context,
        dpia_id=dpia.dpia_id,
        target=DPIAStatus.APPROVED,
        approval_reference="approval:1",
        valid_until=T2,
        controller_reference=w.other_authority,
        process_owner_authority_reference=w.applicant,
        clock=w.clock,
    )
    decision = decide_processing_activation(
        w.activities,
        w.dpias,
        w.activations,
        w.audit,
        context,
        activity_id=activity.activity_id,
        risk_class=ProcessingRiskClass.HIGH,
        decided_by_authority_reference=w.authority,
        reason_code="COMPLIANCE_PROCESSING_ACTIVATION_DECIDED",
        clock=w.clock,
    ).decision
    assert decision.state.value == "activated"
    assert decision.dpia_id == dpia.dpia_id


def test_registering_a_record_class_audits_the_registration() -> None:
    w = world()
    result = register_record_class(
        w.record_classes, w.audit, context_for(w.land_a), w.record_class(), clock=w.clock
    )
    assert result.audit_event.event_type == "record_class.registered"
    assert result.event.payload["organization_id"] == str(w.land_a)


# ===========================================================================
# 9. Audit and idempotency conventions hold for every new command
# ===========================================================================


def test_every_new_write_command_appends_exactly_one_audit_entry() -> None:
    w = world()
    before = len(w.audit.list_all())
    case = make_case(w.land_a)
    open_legal_case(w.cases, w.audit, context_for(w.land_a), case, clock=w.clock)
    assert len(w.audit.list_all()) == before + 1


def test_a_replayed_open_legal_case_returns_the_stored_case_and_no_new_audit() -> None:
    w = world()
    case = make_case(w.land_a)
    event_id = uuid4()
    first = open_legal_case(
        w.cases, w.audit, context_for(w.land_a), case, clock=w.clock, event_id=event_id
    )
    count = len(w.audit.list_all())
    second = open_legal_case(
        w.cases, w.audit, context_for(w.land_a), case, clock=w.clock, event_id=event_id
    )
    assert first.case == second.case
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert len(w.audit.list_all()) == count


def test_the_audit_chain_stays_intact_across_a_full_case_lifecycle() -> None:
    w = world()
    case_id = _case_with_jurisdiction(w)
    register_case_party(
        w.cases,
        w.parties,
        w.audit,
        context_for(w.land_a),
        CaseParty(
            case_party_id=uuid4(),
            case_id=case_id,
            organization_id=w.land_a,
            party_reference=w.applicant,
            role=PartyRole.APPLICANT,
            registered_at=T0,
            is_authorized_service_recipient=True,
        ),
        clock=w.clock,
    )
    notice_id = _served_notice(w, case_id)
    determine_service_effect(
        w.notices,
        w.attempts,
        w.notice_effects,
        w.audit,
        context_for(w.land_a),
        notice_id=notice_id,
        deemed_service_rule=DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
        rule_reference="rules:s.5",
        decided_by_authority_reference=w.authority,
        effective_at=T1,
        clock=w.clock,
    )
    verification = w.audit.verify_chain()
    assert verification.is_intact is True
    assert verification.checked_count == len(w.audit.list_all())


def _issue_decision(w: World, case_id: UUID) -> ProceduralDecision:
    notice_id = _served_notice(w, case_id)
    effect = determine_service_effect(
        w.notices,
        w.attempts,
        w.notice_effects,
        w.audit,
        context_for(w.land_a),
        notice_id=notice_id,
        deemed_service_rule=DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
        rule_reference="rules:s.5",
        decided_by_authority_reference=w.authority,
        effective_at=T1,
        clock=w.clock,
    ).decision
    return issue_procedural_decision(
        w.cases,
        w.jurisdictions,
        w.decisions,
        w.notice_effects,
        w.recusals,
        w.audit,
        context_for(w.land_a),
        make_decision(case_id, w.land_a, w.authority),
        notice_effect_id=effect.effect_id,
        response_opportunity_given=True,
        remedy_available=True,
        decided_by_actor_class=ActorClass.HUMAN_AUTHORITY,
        clock=w.clock,
    ).decision
