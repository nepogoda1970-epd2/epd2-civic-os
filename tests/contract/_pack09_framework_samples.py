"""Canonical sample instances for the Architecture & Domain Framework
0.8.1 additions to PACK-09 (legal-case substrate, official notice trust
boundary, records classification, data-protection governance).

One place that builds a *valid* instance of every new entity and a real
`EventEnvelope` for every new event type. Two consumers share it:

- `test_ct00_01_pack09_framework_schema_validation.py`, which validates
  each sample against the JSON Schema that documents it, so a schema that
  drifts from its dataclass fails in CI rather than in production;
- the schema generator used to produce those files in the first place,
  which reads the same samples - so the schemas cannot have been produced
  from a shape the code never actually emits.

Every sample satisfies every `__post_init__` invariant its class
enforces. Nothing here is a mock: they are the real frozen dataclasses,
constructed the way the application layer constructs them.

Party and authority references are handles from
`casework.mint_case_party_reference` - unlinkable across cases by
construction and resolvable to no person anywhere (Framework hard
invariant 1).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TypedDict
from uuid import UUID, uuid4

from epd2_compliance_service.casework import (
    ActorClass,
    AttendanceState,
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
    HearingAttendance,
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
    RepresentationStatus,
    mint_case_party_reference,
)
from epd2_compliance_service.dataprotection import (
    ConsentWithdrawalRecord,
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    DPIAStatus,
    ProcessingActivationDecision,
    ProcessingActivationState,
    ProcessingRiskClass,
    TransferAssessment,
    TransferMechanism,
)
from epd2_compliance_service.domain import (
    DataClassification,
    DerivativeKind,
    HoldPropagationRecord,
    PropagationState,
    RecordClass,
    RecordSensitivity,
    SearchExportEligibility,
)
from epd2_compliance_service.events import (
    build_case_party_registered_event,
    build_deadline_triggered_event,
    build_decision_effect_changed_event,
    build_decision_enforceability_changed_event,
    build_decision_finality_changed_event,
    build_dpia_requirement_determined_event,
    build_dpia_status_changed_event,
    build_filing_admissibility_decided_event,
    build_filing_received_event,
    build_filing_superseded_event,
    build_hearing_cancelled_event,
    build_hearing_completed_event,
    build_hearing_rescheduled_event,
    build_hearing_scheduled_event,
    build_hold_propagation_registered_event,
    build_interim_measure_decided_event,
    build_jurisdiction_challenged_event,
    build_jurisdiction_determined_event,
    build_jurisdiction_transferred_event,
    build_legal_case_opened_event,
    build_legal_case_reopened_event,
    build_legal_case_status_changed_event,
    build_notice_effect_determined_event,
    build_notice_issued_event,
    build_procedural_decision_issued_event,
    build_processing_activation_decided_event,
    build_record_class_registered_event,
    build_recusal_recorded_event,
    build_remedy_registered_event,
    build_replacement_assigned_event,
    build_representation_registered_event,
    build_representation_revoked_event,
    build_service_attempt_recorded_event,
)
from epd2_compliance_service.notices import (
    DeadlineTrigger,
    DeemedServiceRule,
    DeliveryTelemetryStatus,
    NoticeEffectDecision,
    NoticeEffectOutcome,
    NoticeKind,
    OfficialNotice,
    ReadTelemetryStatus,
    ServiceAttempt,
    ServiceMethod,
    TriggerSource,
)
from epd2_compliance_service.references import (
    DocumentRef,
    EvidenceRef,
    MinutesRef,
    NoticeProofPackageRef,
    PlaceholderOwner,
)
from epd2_core.event_envelope import ActorRef, EventEnvelope

AT = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)
LATER = AT + timedelta(days=7)
MUCH_LATER = AT + timedelta(days=30)
BERLIN = "Europe/Berlin"

ORGANIZATION_ID = UUID("11111111-1111-4111-8111-111111111111")
LEGAL_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")
PRIOR_CASE_ID = UUID("22222222-2222-4222-8222-222222222299")
ACTOR = ActorRef(actor_id=UUID("33333333-3333-4333-8333-333333333333"), actor_type="service")
CORRELATION_ID = UUID("44444444-4444-4444-8444-444444444444")

APPLICANT = mint_case_party_reference()
RESPONDENT = mint_case_party_reference()
REPRESENTATIVE = mint_case_party_reference()
AUTHORITY = mint_case_party_reference()
REVIEWER = mint_case_party_reference()
REPLACEMENT = mint_case_party_reference()


# ---------------------------------------------------------------------------
# Placeholder references owned by later packs
# ---------------------------------------------------------------------------


def document_ref() -> DocumentRef:
    return DocumentRef(
        owner=PlaceholderOwner.PACK_11_DOCUMENTS,
        kind="submission",
        external_reference="pack-11:doc:0001",
        organization_id=ORGANIZATION_ID,
    )


def evidence_ref() -> EvidenceRef:
    return EvidenceRef(
        owner=PlaceholderOwner.PACK_11_DOCUMENTS,
        kind="exhibit",
        external_reference="pack-11:evidence:0001",
        organization_id=ORGANIZATION_ID,
    )


def minutes_ref() -> MinutesRef:
    return MinutesRef(
        owner=PlaceholderOwner.PACK_11_DOCUMENTS,
        kind="hearing_minutes",
        external_reference="pack-11:minutes:0001",
        organization_id=ORGANIZATION_ID,
    )


def proof_package_ref() -> NoticeProofPackageRef:
    return NoticeProofPackageRef(
        id=UUID("55555555-5555-4555-8555-555555555555"),
        organization_id=ORGANIZATION_ID,
    )


# ---------------------------------------------------------------------------
# Legal-case substrate
# ---------------------------------------------------------------------------


def jurisdiction(
    *,
    jurisdiction_id: UUID | None = None,
    status: JurisdictionStatus = JurisdictionStatus.CONFIRMED,
) -> JurisdictionDetermination:
    return JurisdictionDetermination(
        jurisdiction_id=jurisdiction_id or UUID("66666666-6666-4666-8666-666666666666"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        jurisdiction_type=JurisdictionType.PARTY_STATUTE,
        case_kind=CaseKind.ARBITRATION,
        competent_authority_reference=AUTHORITY,
        status=status,
        determined_at=AT,
        determined_by_authority_reference=AUTHORITY,
        valid_from=AT,
        basis_reference="statute:s.14(2)",
    )


def transferred_jurisdiction() -> JurisdictionDetermination:
    return jurisdiction().transfer_to(
        UUID("66666666-6666-4666-8666-666666666677"),
        at=LATER,
        reason_code="JURISDICTION_TRANSFER_REQUIRED",
    )


def legal_case(
    *,
    status_path: tuple[LegalCaseStatus, ...] = (LegalCaseStatus.INTAKE,),
    jurisdiction_id: UUID | None = None,
    closed: bool = False,
    reopened: bool = False,
) -> LegalCase:
    history = tuple(
        CaseTransitionEntry(
            sequence=index + 1,
            status_after=status,
            occurred_at=AT + timedelta(hours=index),
            reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
            actor_authority_reference=AUTHORITY,
        )
        for index, status in enumerate(status_path)
    )
    return LegalCase(
        legal_case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        case_kind=CaseKind.ARBITRATION,
        opened_at=AT,
        subject_reference="dispute:2026-0007",
        confidentiality_class=ConfidentialityClass.CONFIDENTIAL,
        access_profile=CaseAccessProfile.NAMED_PARTIES_ONLY,
        transition_history=history,
        governing_policy_reference="policy:arbitration-rules:v3",
        jurisdiction_id=jurisdiction_id,
        closed_at=MUCH_LATER if closed else None,
        closure_reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED" if closed else None,
        reopened_at=MUCH_LATER if reopened else None,
        reopened_from_case_id=PRIOR_CASE_ID if reopened else None,
        prior_case_id=PRIOR_CASE_ID if reopened else None,
        case_version=len(history),
    )


def closed_case() -> LegalCase:
    return legal_case(
        status_path=(
            LegalCaseStatus.INTAKE,
            LegalCaseStatus.JURISDICTION_REVIEW,
            LegalCaseStatus.ADMISSIBILITY_REVIEW,
            LegalCaseStatus.SUBSTANTIVE_REVIEW,
            LegalCaseStatus.DECIDED,
            LegalCaseStatus.CLOSED,
        ),
        jurisdiction_id=jurisdiction().jurisdiction_id,
        closed=True,
    )


def reopened_case() -> LegalCase:
    return legal_case(
        status_path=(LegalCaseStatus.INTAKE,),
        jurisdiction_id=jurisdiction().jurisdiction_id,
        reopened=True,
    )


def case_party(*, role: PartyRole = PartyRole.APPLICANT) -> CaseParty:
    return CaseParty(
        case_party_id=UUID("77777777-7777-4777-8777-777777777777"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        party_reference=APPLICANT,
        role=role,
        registered_at=AT,
        is_authorized_service_recipient=True,
        display_label_code="party.applicant",
    )


def representation(
    *, status: RepresentationStatus = RepresentationStatus.ACTIVE
) -> RepresentationMandate:
    mandate = RepresentationMandate(
        mandate_id=UUID("88888888-8888-4888-8888-888888888888"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        represented_party_reference=APPLICANT,
        representative_reference=REPRESENTATIVE,
        authorities=frozenset(
            {
                RepresentationAuthority.FILE_SUBMISSIONS,
                RepresentationAuthority.RECEIVE_SERVICE,
            }
        ),
        valid_from=AT,
        mandate_basis_reference="mandate:2026-0007",
    )
    if status is RepresentationStatus.REVOKED:
        return mandate.revoke(LATER, reason_code="REPRESENTATION_REVOKED")
    return mandate


def filing(
    *,
    intake_state: FilingIntakeState = FilingIntakeState.RECEIVED,
    docket_sequence: int = 1,
) -> Filing:
    base = Filing(
        filing_id=UUID("99999999-9999-4999-8999-999999999999"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        docket_sequence=docket_sequence,
        filing_type=FilingType.INITIATING_SUBMISSION,
        filed_by_party_reference=APPLICANT,
        submitted_at=AT,
        received_at=AT + timedelta(hours=2),
        intake_state=FilingIntakeState.RECEIVED,
        filed_by_representative_reference=REPRESENTATIVE,
        document_references=(document_ref(),),
        evidence_references=(evidence_ref(),),
    )
    if intake_state is FilingIntakeState.ADMITTED:
        return base.admit()
    if intake_state is FilingIntakeState.REJECTED:
        return base.reject(reason_code="FILING_INADMISSIBLE")
    if intake_state is FilingIntakeState.SUPERSEDED:
        return base.mark_superseded(UUID("99999999-9999-4999-8999-999999999988"))
    return base


def hearing(*, status: HearingStatus = HearingStatus.SCHEDULED) -> Hearing:
    base = Hearing(
        hearing_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        convening_authority_reference=AUTHORITY,
        agenda_code="hearing.substantive",
        scheduled_at=LATER,
        timezone=BERLIN,
        history=(
            HearingHistoryEntry(
                sequence=1,
                status_after=HearingStatus.SCHEDULED,
                occurred_at=AT,
                scheduled_at_before=LATER,
                scheduled_at_after=LATER,
                reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
                actor_authority_reference=AUTHORITY,
            ),
        ),
        attendance=(
            HearingAttendance(
                party_reference=APPLICANT,
                state=AttendanceState.PRESENT,
                recorded_at=LATER,
            ),
            HearingAttendance(
                party_reference=RESPONDENT,
                state=AttendanceState.REPRESENTED,
                recorded_at=LATER,
            ),
        ),
        evidence_references=(evidence_ref(),),
    )
    if status is HearingStatus.RESCHEDULED:
        return base.reschedule(
            AT + timedelta(days=1),
            new_scheduled_at=MUCH_LATER,
            reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
            actor_authority_reference=AUTHORITY,
        )
    if status is HearingStatus.CANCELLED:
        return base.cancel(
            AT + timedelta(days=1),
            reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
            actor_authority_reference=AUTHORITY,
        )
    if status is HearingStatus.COMPLETED:
        return base.complete(
            MUCH_LATER,
            reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
            actor_authority_reference=AUTHORITY,
            minutes_reference=minutes_ref(),
        )
    return base


def interim_measure(
    *, status: InterimMeasureStatus = InterimMeasureStatus.GRANTED
) -> InterimMeasure:
    return InterimMeasure(
        measure_id=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        measure_kind="suspension_of_office",
        requested_by_party_reference=APPLICANT,
        decided_by_authority_reference=AUTHORITY,
        decided_by_actor_class=ActorClass.HUMAN_AUTHORITY,
        legal_basis_reference="statute:s.22",
        scope_description_code="measure.scope.office_suspension",
        status=status,
        decided_at=AT,
        starts_at=AT,
        ends_at=MUCH_LATER,
        review_due_at=LATER,
        reasons_reference="reasons:2026-0007-interim",
        evidence_references=(evidence_ref(),),
    )


def procedural_decision(
    *,
    effect: EffectStatus = EffectStatus.PENDING,
    finality: FinalityStatus = FinalityStatus.OPEN_TO_REMEDY,
    enforceability: EnforceabilityStatus = EnforceabilityStatus.NOT_ENFORCEABLE,
) -> ProceduralDecision:
    return ProceduralDecision(
        decision_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        decision_type=DecisionType.SUBSTANTIVE,
        deciding_authority_reference=AUTHORITY,
        decided_by_party_reference=AUTHORITY,
        operative_result=OperativeResult.PARTIALLY_UPHELD,
        issued_at=AT,
        state_history=(
            DecisionStateEntry(
                sequence=1,
                occurred_at=AT,
                effect_status=effect,
                finality_status=finality,
                enforceability_status=enforceability,
                reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
                actor_authority_reference=AUTHORITY,
            ),
        ),
        reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        effective_at=LATER,
        reasons_reference="reasons:2026-0007-final",
        evidence_references=(evidence_ref(),),
    )


def effective_decision() -> ProceduralDecision:
    return procedural_decision().commence_effect(
        LATER,
        reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        actor_authority_reference=AUTHORITY,
    )


def enforceable_decision() -> ProceduralDecision:
    return effective_decision().become_enforceable(
        MUCH_LATER,
        reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        actor_authority_reference=AUTHORITY,
    )


def final_decision() -> ProceduralDecision:
    return effective_decision().become_final(
        MUCH_LATER,
        reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        actor_authority_reference=AUTHORITY,
    )


def remedy(*, status: RemedyStatus = RemedyStatus.AVAILABLE) -> Remedy:
    return Remedy(
        remedy_id=UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        decision_id=procedural_decision().decision_id,
        remedy_kind=RemedyKind.APPEAL,
        status=status,
        available_from=AT,
        available_until=MUCH_LATER,
        competent_authority_reference=AUTHORITY,
        deadline_id=UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
    )


def recusal(
    *, outcome: ConflictAssessmentOutcome = ConflictAssessmentOutcome.RECUSAL_REQUIRED
) -> RecusalRecord:
    return RecusalRecord(
        recusal_id=UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        party_reference=AUTHORITY,
        conflict_declaration_id=UUID("ffffffff-ffff-4fff-8fff-fffffffffff1"),
        assessment_outcome=outcome,
        effective_at=AT,
        reviewed_by_party_reference=REVIEWER,
        prior_participation_codes=("filing.admissibility_decided",),
    )


def replacement() -> ReplacementAssignment:
    return ReplacementAssignment(
        assignment_id=UUID("ffffffff-ffff-4fff-8fff-fffffffffff2"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        recusal_id=recusal().recusal_id,
        replacement_party_reference=REPLACEMENT,
        assigned_by_authority_reference=REVIEWER,
        assigned_at=LATER,
    )


# ---------------------------------------------------------------------------
# Official notice trust boundary
# ---------------------------------------------------------------------------


def official_notice() -> OfficialNotice:
    return OfficialNotice(
        notice_id=UUID("10101010-1010-4010-8010-101010101010"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        notice_kind=NoticeKind.HEARING_SUMMONS,
        issuing_authority_reference=AUTHORITY,
        recipient_party_reference=RESPONDENT,
        authorized_methods=frozenset(
            {ServiceMethod.REGISTERED_POST, ServiceMethod.ELECTRONIC_PORTAL}
        ),
        issued_at=AT,
        content_reference="pack-11:notice-content:0001",
        recipient_is_authorized_service_recipient=True,
    )


def service_attempt(
    *,
    delivery: DeliveryTelemetryStatus = DeliveryTelemetryStatus.DELIVERED,
    read: ReadTelemetryStatus = ReadTelemetryStatus.UNKNOWN,
    reconciled: bool = True,
) -> ServiceAttempt:
    attempt = ServiceAttempt(
        attempt_id=UUID("20202020-2020-4020-8020-202020202020"),
        notice_id=official_notice().notice_id,
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        method=ServiceMethod.REGISTERED_POST,
        attempted_at=AT + timedelta(hours=4),
        delivery_status=delivery,
        read_status=read,
        provider_reference="provider:post:tracking-abc",
    )
    if reconciled:
        return attempt.reconcile(proof_package_reference=proof_package_ref())
    return attempt


def notice_effect(
    *, outcome: NoticeEffectOutcome = NoticeEffectOutcome.EFFECTIVE
) -> NoticeEffectDecision:
    return NoticeEffectDecision(
        effect_id=UUID("30303030-3030-4030-8030-303030303030"),
        notice_id=official_notice().notice_id,
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        outcome=outcome,
        decided_at=LATER,
        decided_by_authority_reference=AUTHORITY,
        deemed_service_rule=DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
        supporting_attempt_ids=(service_attempt().attempt_id,),
        rule_reference="rules:service:s.5(1)",
        effective_at=LATER if outcome is NoticeEffectOutcome.EFFECTIVE else None,
        reason_code=None if outcome is NoticeEffectOutcome.EFFECTIVE else "SERVICE_NOT_PROVEN",
        proof_package_reference=proof_package_ref(),
    )


def deadline_trigger() -> DeadlineTrigger:
    return DeadlineTrigger(
        trigger_id=UUID("40404040-4040-4040-8040-404040404040"),
        deadline_id=UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
        case_id=LEGAL_CASE_ID,
        organization_id=ORGANIZATION_ID,
        source=TriggerSource.NOTICE_EFFECT_DECISION,
        triggered_at=LATER,
        notice_effect_id=notice_effect().effect_id,
        source_reference="notice-effect:30303030",
    )


# ---------------------------------------------------------------------------
# Records classification and hold propagation
# ---------------------------------------------------------------------------


def record_class() -> RecordClass:
    return RecordClass(
        record_class_id=UUID("50505050-5050-4050-8050-505050505050"),
        organization_id=ORGANIZATION_ID,
        record_class_code="case.arbitration.file",
        record_category="procedural_case_file",
        sensitivity=RecordSensitivity.CONFIDENTIAL,
        data_classification=DataClassification.CONFIDENTIAL,
        record_owner_authority_reference=AUTHORITY,
        custodian_reference=REVIEWER,
        disposition_authority_reference=REPLACEMENT,
        retention_policy_reference=UUID("50505050-5050-4050-8050-505050505011"),
        search_export_eligibility=SearchExportEligibility.SCOPED_SEARCH_GOVERNED_EXPORT,
        legal_hold_applicable=True,
        valid_from=AT,
    )


def hold_propagation(
    *, state: PropagationState = PropagationState.CONFIRMED
) -> HoldPropagationRecord:
    return HoldPropagationRecord(
        propagation_id=UUID("60606060-6060-4060-8060-606060606060"),
        hold_id=UUID("60606060-6060-4060-8060-606060606011"),
        organization_id=ORGANIZATION_ID,
        derivative_kind=DerivativeKind.SEARCH_INDEX,
        derivative_reference="index:case-files:primary",
        state=state,
        recorded_at=AT,
        evidence_reference="propagation-evidence:0001",
        failure_reason_code=(
            "LEGAL_HOLD_PROPAGATION_UNRESOLVED" if state is PropagationState.FAILED else None
        ),
    )


# ---------------------------------------------------------------------------
# Data-protection governance
# ---------------------------------------------------------------------------


ACTIVITY_ID = UUID("70707070-7070-4070-8070-707070707070")


def dpia_requirement(*, required: bool = True) -> DPIARequirementDetermination:
    return DPIARequirementDetermination(
        determination_id=UUID("70707070-7070-4070-8070-707070707011"),
        activity_id=ACTIVITY_ID,
        organization_id=ORGANIZATION_ID,
        risk_class=ProcessingRiskClass.HIGH if required else ProcessingRiskClass.LOW,
        dpia_required=required,
        determined_at=AT,
        determined_by_party_reference=REVIEWER,
        basis_reference="dp-policy:risk-matrix:v2",
    )


def dpia(*, status: DPIAStatus = DPIAStatus.APPROVED) -> DataProtectionImpactAssessment:
    return DataProtectionImpactAssessment(
        dpia_id=UUID("70707070-7070-4070-8070-707070707022"),
        activity_id=ACTIVITY_ID,
        organization_id=ORGANIZATION_ID,
        status=status,
        risk_class=ProcessingRiskClass.HIGH,
        reviewer_party_reference=REVIEWER,
        created_at=AT,
        updated_at=AT,
        approval_reference="dpia-approval:0001" if status is DPIAStatus.APPROVED else None,
        approved_at=AT if status is DPIAStatus.APPROVED else None,
        valid_until=MUCH_LATER,
        outcome_reason_code=None,
    )


def processing_activation(
    *, state: ProcessingActivationState = ProcessingActivationState.ACTIVATED
) -> ProcessingActivationDecision:
    return ProcessingActivationDecision(
        activation_decision_id=UUID("70707070-7070-4070-8070-707070707033"),
        activity_id=ACTIVITY_ID,
        organization_id=ORGANIZATION_ID,
        state=state,
        decided_at=AT,
        decided_by_authority_reference=AUTHORITY,
        reason_code="COMPLIANCE_PROCESSING_ACTIVATION_DECIDED",
        dpia_id=dpia().dpia_id,
        effective_from=AT,
    )


def transfer_assessment() -> TransferAssessment:
    return TransferAssessment(
        assessment_id=UUID("70707070-7070-4070-8070-707070707044"),
        activity_id=ACTIVITY_ID,
        organization_id=ORGANIZATION_ID,
        mechanism=TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES,
        recipient_category="processor.hosting",
        assessed_at=AT,
        assessed_by_party_reference=REVIEWER,
        assessment_reference="tia:0001",
    )


def consent_withdrawal() -> ConsentWithdrawalRecord:
    return ConsentWithdrawalRecord(
        withdrawal_id=UUID("70707070-7070-4070-8070-707070707055"),
        activity_id=ACTIVITY_ID,
        organization_id=ORGANIZATION_ID,
        withdrawn_at=AT,
        subject_party_reference=APPLICANT,
        affects_records_of_class="case.arbitration.file",
        retention_obligation_persists=True,
    )


# ---------------------------------------------------------------------------
# Every entity, by the schema file that documents it
# ---------------------------------------------------------------------------


def entity_samples() -> dict[str, object]:
    """Schema stem -> a valid instance of the entity it documents."""
    return {
        "legal-case": closed_case(),
        "jurisdiction-determination": jurisdiction(),
        "case-party": case_party(),
        "representation-mandate": representation(),
        "filing": filing(intake_state=FilingIntakeState.ADMITTED),
        "hearing": hearing(status=HearingStatus.COMPLETED),
        "interim-measure": interim_measure(),
        "procedural-decision": enforceable_decision(),
        "remedy": remedy(),
        "recusal-record": recusal(),
        "replacement-assignment": replacement(),
        "official-notice": official_notice(),
        "service-attempt": service_attempt(),
        "notice-effect-decision": notice_effect(),
        "deadline-trigger": deadline_trigger(),
        "record-class": record_class(),
        "hold-propagation-record": hold_propagation(),
        "dpia-requirement-determination": dpia_requirement(),
        "data-protection-impact-assessment": dpia(),
        "processing-activation-decision": processing_activation(),
        "transfer-assessment": transfer_assessment(),
        "consent-withdrawal-record": consent_withdrawal(),
    }


# ---------------------------------------------------------------------------
# Every event, by the payload schema file that documents it
# ---------------------------------------------------------------------------


class _CommonEventArguments(TypedDict):
    """The four envelope arguments every builder takes.

    A `TypedDict` rather than a plain dict so `**common` keeps its types
    through mypy's strict mode - a `dict[str, object]` would erase them
    and turn every call site into an `arg-type` error."""

    actor: ActorRef
    correlation_id: UUID
    causation_id: UUID | None
    occurred_at: datetime


def _kwargs() -> _CommonEventArguments:
    return {
        "actor": ACTOR,
        "correlation_id": CORRELATION_ID,
        "causation_id": None,
        "occurred_at": AT,
    }


def event_samples() -> dict[str, EventEnvelope]:
    """Payload-schema stem -> a real envelope built by `events`."""
    common = _kwargs()
    return {
        "legal-case-opened-payload": build_legal_case_opened_event(
            event_id=uuid4(), case=legal_case(), **common
        ),
        "legal-case-status-changed-payload": build_legal_case_status_changed_event(
            event_id=uuid4(), case=closed_case(), **common
        ),
        "legal-case-reopened-payload": build_legal_case_reopened_event(
            event_id=uuid4(), case=reopened_case(), **common
        ),
        "jurisdiction-determined-payload": build_jurisdiction_determined_event(
            event_id=uuid4(), determination=jurisdiction(), **common
        ),
        "jurisdiction-challenged-payload": build_jurisdiction_challenged_event(
            event_id=uuid4(),
            determination=jurisdiction().challenge(LATER, reason_code="JURISDICTION_NOT_COMPETENT"),
            **common,
        ),
        "jurisdiction-transferred-payload": build_jurisdiction_transferred_event(
            event_id=uuid4(),
            determination=transferred_jurisdiction(),
            successor_jurisdiction_id=UUID("66666666-6666-4666-8666-666666666677"),
            **common,
        ),
        "case-party-registered-payload": build_case_party_registered_event(
            event_id=uuid4(), party=case_party(), **common
        ),
        "representation-registered-payload": build_representation_registered_event(
            event_id=uuid4(), mandate=representation(), **common
        ),
        "representation-revoked-payload": build_representation_revoked_event(
            event_id=uuid4(),
            mandate=representation(status=RepresentationStatus.REVOKED),
            **common,
        ),
        "filing-received-payload": build_filing_received_event(
            event_id=uuid4(), filing=filing(), **common
        ),
        "filing-admissibility-decided-payload": build_filing_admissibility_decided_event(
            event_id=uuid4(),
            filing=filing(intake_state=FilingIntakeState.REJECTED),
            reason_code="FILING_INADMISSIBLE",
            **common,
        ),
        "filing-superseded-payload": build_filing_superseded_event(
            event_id=uuid4(),
            filing=filing(intake_state=FilingIntakeState.SUPERSEDED),
            successor_filing_id=UUID("99999999-9999-4999-8999-999999999988"),
            **common,
        ),
        "hearing-scheduled-payload": build_hearing_scheduled_event(
            event_id=uuid4(), hearing=hearing(), **common
        ),
        "hearing-rescheduled-payload": build_hearing_rescheduled_event(
            event_id=uuid4(), hearing=hearing(status=HearingStatus.RESCHEDULED), **common
        ),
        "hearing-cancelled-payload": build_hearing_cancelled_event(
            event_id=uuid4(), hearing=hearing(status=HearingStatus.CANCELLED), **common
        ),
        "hearing-completed-payload": build_hearing_completed_event(
            event_id=uuid4(), hearing=hearing(status=HearingStatus.COMPLETED), **common
        ),
        "interim-measure-decided-payload": build_interim_measure_decided_event(
            event_id=uuid4(), measure=interim_measure(), **common
        ),
        "procedural-decision-issued-payload": build_procedural_decision_issued_event(
            event_id=uuid4(), decision=procedural_decision(), **common
        ),
        "decision-effect-changed-payload": build_decision_effect_changed_event(
            event_id=uuid4(), decision=effective_decision(), **common
        ),
        "decision-finality-changed-payload": build_decision_finality_changed_event(
            event_id=uuid4(), decision=final_decision(), **common
        ),
        "decision-enforceability-changed-payload": (
            build_decision_enforceability_changed_event(
                event_id=uuid4(), decision=enforceable_decision(), **common
            )
        ),
        "remedy-registered-payload": build_remedy_registered_event(
            event_id=uuid4(), remedy=remedy(), **common
        ),
        "recusal-recorded-payload": build_recusal_recorded_event(
            event_id=uuid4(), recusal=recusal(), **common
        ),
        "replacement-assigned-payload": build_replacement_assigned_event(
            event_id=uuid4(), assignment=replacement(), **common
        ),
        "official-notice-issued-payload": build_notice_issued_event(
            event_id=uuid4(), notice=official_notice(), **common
        ),
        "service-attempt-recorded-payload": build_service_attempt_recorded_event(
            event_id=uuid4(), attempt=service_attempt(), **common
        ),
        "notice-effect-determined-payload": build_notice_effect_determined_event(
            event_id=uuid4(), decision=notice_effect(), **common
        ),
        "deadline-triggered-payload": build_deadline_triggered_event(
            event_id=uuid4(), trigger=deadline_trigger(), **common
        ),
        "record-class-registered-payload": build_record_class_registered_event(
            event_id=uuid4(), record_class=record_class(), **common
        ),
        "hold-propagation-registered-payload": build_hold_propagation_registered_event(
            event_id=uuid4(), propagation=hold_propagation(), **common
        ),
        "dpia-requirement-determined-payload": build_dpia_requirement_determined_event(
            event_id=uuid4(), determination=dpia_requirement(), **common
        ),
        "dpia-status-changed-payload": build_dpia_status_changed_event(
            event_id=uuid4(), dpia=dpia(), **common
        ),
        "processing-activation-decided-payload": build_processing_activation_decided_event(
            event_id=uuid4(), decision=processing_activation(), **common
        ),
    }


# ---------------------------------------------------------------------------
# Wire serialization
# ---------------------------------------------------------------------------


def to_wire(value: object) -> object:
    """Convert a frozen domain dataclass into the plain JSON shape its
    schema documents.

    Mechanical rather than hand-written on purpose: a hand-built wire dict
    can quietly disagree with the dataclass it is supposed to represent,
    and then the schema test validates a shape the code never emits.
    Frozen sets become sorted arrays so the output is deterministic."""
    import dataclasses as _dc
    from enum import Enum as _Enum

    if _dc.is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_wire(getattr(value, field.name)) for field in _dc.fields(value)}
    if isinstance(value, _Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, frozenset | set):
        return sorted(to_wire(item) for item in value)  # type: ignore[type-var]
    if isinstance(value, tuple | list):
        return [to_wire(item) for item in value]
    return value
