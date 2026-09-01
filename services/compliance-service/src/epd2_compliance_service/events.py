"""Canonical events emitted by Compliance Service (PACK-09, ADR-038).

Forty-one event types, following the envelope contract in
`epd2_core.event_envelope` (canon section 21) and the payload discipline
every earlier pack's own `events.py` already establishes.

**Records governance and data protection (PACK-09 round 1):**

- `governed_record.retention_started`
- `governed_record.disposal_authorized`
- `governed_record.destroyed`
- `legal_hold.status_changed` (issued / released / marked_indeterminate)
- `processing_activity.status_changed`
- `procedural_case.status_changed`
- `procedural_deadline.state_changed`
- `data_subject_request.status_changed`

**Legal-case substrate (Architecture & Domain Framework 0.8.1, section
13.1 - "общий legal-case substrate"):**

- `legal_case.opened`, `legal_case.status_changed`, `legal_case.reopened`
- `jurisdiction.determined`, `.challenged`, `.transferred`
- `case_party.registered`
- `representation.registered`, `representation.revoked`
- `filing.received`, `filing.admissibility_decided`, `filing.superseded`
- `hearing.scheduled`, `.rescheduled`, `.cancelled`, `.completed`
- `interim_measure.decided`
- `procedural_decision.issued`
- `procedural_decision.effect_changed`
- `procedural_decision.finality_changed`
- `procedural_decision.enforceability_changed`
- `remedy.registered`
- `recusal.recorded`, `replacement.assigned`

**Official notice as a separate trust boundary (Framework hard
invariants 39 and 40) - three distinct event types on purpose:**

- `official_notice.issued` - an authorized object now exists. Nothing is
  served, nothing is due.
- `service_attempt.recorded` - provider telemetry. Explicitly *not* a
  legal effect (Framework 57: "provider status != internal legal effect").
- `notice_effect.determined` - the governed decision. The only event in
  this repository whose subject can start a procedural deadline.
- `procedural_deadline.triggered` - records which governed trigger
  started which deadline, exactly once (Framework 59).

**Records classification, holds and DPIA gate:**

- `record_class.registered`
- `legal_hold.propagation_registered`
- `dpia.requirement_determined`, `dpia.status_changed`
- `processing_activity.activation_decided`

**Payload discipline (invariant 13, Framework section 11).** Every wire
payload below carries only identifiers of non-personal objects, enum
values, timestamps, counts and reason codes. It never carries: a document
or its bytes, document/message content, a vote/ballot/tally/delegation
reference, an authentication secret, an identity/eID/KYC attribute, a
free-text case narrative, or the name of any natural person.

It also never carries a **party or authority reference**. Those handles
are unlinkable across cases by construction
(`casework.mint_case_party_reference`), but a broadcast payload is the
wrong place for them regardless: a subscriber that never needs to know
*who* acted should not be handed a handle it could accumulate. Party and
authority references therefore appear only in the audit snapshots below,
which are hashed into Audit Core and never published.

Every wire payload carries `organization_id` (scope), a `reason_code`
where the event records a decision, `recorded_at`, and the aggregate's
version or history sequence where one exists - so a consumer can detect a
gap and apply `event_id` idempotency (CT-00-04) without this service ever
re-sending, or being able to rewrite, an earlier entry.

The `*_full_state_payload` helpers are a separate concern: they are the
canonically-hashable snapshots fed to Audit Core's
`before_hash`/`after_hash`, never broadcast as a wire payload. They may
contain more fields than the corresponding event payload, but are still
bound by the same no-identity/no-document/no-vote rule.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_compliance_service.casework import (
    CaseParty,
    Filing,
    Hearing,
    InterimMeasure,
    JurisdictionDetermination,
    LegalCase,
    ProceduralDecision,
    RecusalRecord,
    Remedy,
    ReplacementAssignment,
    RepresentationMandate,
)
from epd2_compliance_service.dataprotection import (
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    ProcessingActivationDecision,
)
from epd2_compliance_service.domain import (
    DataSubjectRequest,
    DestructionEvidence,
    GovernedRecord,
    HoldPropagationRecord,
    LegalHold,
    ProceduralCase,
    ProceduralDeadline,
    ProcessingActivity,
    RecordClass,
    RetentionStartEvent,
)
from epd2_compliance_service.notices import (
    DeadlineTrigger,
    NoticeEffectDecision,
    OfficialNotice,
    ServiceAttempt,
)
from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})

PRODUCER = "compliance-service"

EVENT_TYPE_RETENTION_STARTED = "governed_record.retention_started"
EVENT_TYPE_DISPOSAL_AUTHORIZED = "governed_record.disposal_authorized"
EVENT_TYPE_RECORD_DESTROYED = "governed_record.destroyed"
EVENT_TYPE_LEGAL_HOLD_STATUS_CHANGED = "legal_hold.status_changed"
EVENT_TYPE_PROCESSING_ACTIVITY_STATUS_CHANGED = "processing_activity.status_changed"
EVENT_TYPE_CASE_STATUS_CHANGED = "procedural_case.status_changed"
EVENT_TYPE_DEADLINE_STATE_CHANGED = "procedural_deadline.state_changed"
EVENT_TYPE_REQUEST_STATUS_CHANGED = "data_subject_request.status_changed"

# --- Legal-case substrate (Framework 0.8.1 section 13.1) -------------------

EVENT_TYPE_LEGAL_CASE_OPENED = "legal_case.opened"
EVENT_TYPE_LEGAL_CASE_STATUS_CHANGED = "legal_case.status_changed"
EVENT_TYPE_LEGAL_CASE_REOPENED = "legal_case.reopened"
EVENT_TYPE_JURISDICTION_DETERMINED = "jurisdiction.determined"
EVENT_TYPE_JURISDICTION_CHALLENGED = "jurisdiction.challenged"
EVENT_TYPE_JURISDICTION_TRANSFERRED = "jurisdiction.transferred"
EVENT_TYPE_CASE_PARTY_REGISTERED = "case_party.registered"
EVENT_TYPE_REPRESENTATION_REGISTERED = "representation.registered"
EVENT_TYPE_REPRESENTATION_REVOKED = "representation.revoked"
EVENT_TYPE_FILING_RECEIVED = "filing.received"
EVENT_TYPE_FILING_ADMISSIBILITY_DECIDED = "filing.admissibility_decided"
EVENT_TYPE_FILING_SUPERSEDED = "filing.superseded"
EVENT_TYPE_HEARING_SCHEDULED = "hearing.scheduled"
EVENT_TYPE_HEARING_RESCHEDULED = "hearing.rescheduled"
EVENT_TYPE_HEARING_CANCELLED = "hearing.cancelled"
EVENT_TYPE_HEARING_COMPLETED = "hearing.completed"
EVENT_TYPE_INTERIM_MEASURE_DECIDED = "interim_measure.decided"
EVENT_TYPE_PROCEDURAL_DECISION_ISSUED = "procedural_decision.issued"
EVENT_TYPE_DECISION_EFFECT_CHANGED = "procedural_decision.effect_changed"
EVENT_TYPE_DECISION_FINALITY_CHANGED = "procedural_decision.finality_changed"
EVENT_TYPE_DECISION_ENFORCEABILITY_CHANGED = "procedural_decision.enforceability_changed"
EVENT_TYPE_REMEDY_REGISTERED = "remedy.registered"
EVENT_TYPE_RECUSAL_RECORDED = "recusal.recorded"
EVENT_TYPE_REPLACEMENT_ASSIGNED = "replacement.assigned"

# --- Official notice trust boundary (Framework hard invariants 39/40) ------

EVENT_TYPE_NOTICE_ISSUED = "official_notice.issued"
EVENT_TYPE_SERVICE_ATTEMPT_RECORDED = "service_attempt.recorded"
EVENT_TYPE_NOTICE_EFFECT_DETERMINED = "notice_effect.determined"
EVENT_TYPE_DEADLINE_TRIGGERED = "procedural_deadline.triggered"

# --- Records classification, holds, data protection ------------------------

EVENT_TYPE_RECORD_CLASS_REGISTERED = "record_class.registered"
EVENT_TYPE_HOLD_PROPAGATION_REGISTERED = "legal_hold.propagation_registered"
EVENT_TYPE_DPIA_REQUIREMENT_DETERMINED = "dpia.requirement_determined"
EVENT_TYPE_DPIA_STATUS_CHANGED = "dpia.status_changed"
EVENT_TYPE_PROCESSING_ACTIVATION_DECIDED = "processing_activity.activation_decided"

#: Every event type this service is allowed to publish. Contract tests
#: assert that the registry, the JSON Schema directory and this set agree,
#: so an event added in code but not in `contracts/` fails CI.
ALL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_TYPE_RETENTION_STARTED,
        EVENT_TYPE_DISPOSAL_AUTHORIZED,
        EVENT_TYPE_RECORD_DESTROYED,
        EVENT_TYPE_LEGAL_HOLD_STATUS_CHANGED,
        EVENT_TYPE_PROCESSING_ACTIVITY_STATUS_CHANGED,
        EVENT_TYPE_CASE_STATUS_CHANGED,
        EVENT_TYPE_DEADLINE_STATE_CHANGED,
        EVENT_TYPE_REQUEST_STATUS_CHANGED,
        EVENT_TYPE_LEGAL_CASE_OPENED,
        EVENT_TYPE_LEGAL_CASE_STATUS_CHANGED,
        EVENT_TYPE_LEGAL_CASE_REOPENED,
        EVENT_TYPE_JURISDICTION_DETERMINED,
        EVENT_TYPE_JURISDICTION_CHALLENGED,
        EVENT_TYPE_JURISDICTION_TRANSFERRED,
        EVENT_TYPE_CASE_PARTY_REGISTERED,
        EVENT_TYPE_REPRESENTATION_REGISTERED,
        EVENT_TYPE_REPRESENTATION_REVOKED,
        EVENT_TYPE_FILING_RECEIVED,
        EVENT_TYPE_FILING_ADMISSIBILITY_DECIDED,
        EVENT_TYPE_FILING_SUPERSEDED,
        EVENT_TYPE_HEARING_SCHEDULED,
        EVENT_TYPE_HEARING_RESCHEDULED,
        EVENT_TYPE_HEARING_CANCELLED,
        EVENT_TYPE_HEARING_COMPLETED,
        EVENT_TYPE_INTERIM_MEASURE_DECIDED,
        EVENT_TYPE_PROCEDURAL_DECISION_ISSUED,
        EVENT_TYPE_DECISION_EFFECT_CHANGED,
        EVENT_TYPE_DECISION_FINALITY_CHANGED,
        EVENT_TYPE_DECISION_ENFORCEABILITY_CHANGED,
        EVENT_TYPE_REMEDY_REGISTERED,
        EVENT_TYPE_RECUSAL_RECORDED,
        EVENT_TYPE_REPLACEMENT_ASSIGNED,
        EVENT_TYPE_NOTICE_ISSUED,
        EVENT_TYPE_SERVICE_ATTEMPT_RECORDED,
        EVENT_TYPE_NOTICE_EFFECT_DETERMINED,
        EVENT_TYPE_DEADLINE_TRIGGERED,
        EVENT_TYPE_RECORD_CLASS_REGISTERED,
        EVENT_TYPE_HOLD_PROPAGATION_REGISTERED,
        EVENT_TYPE_DPIA_REQUIREMENT_DETERMINED,
        EVENT_TYPE_DPIA_STATUS_CHANGED,
        EVENT_TYPE_PROCESSING_ACTIVATION_DECIDED,
    }
)

#: The event types that PACK-22 (communications) must NOT treat as
#: establishing legally effective notice, listed by name so the
#: prohibition is testable rather than merely documented. Framework hard
#: invariant 39: "delivery/read telemetry != legally effective notice".
NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES: frozenset[str] = frozenset(
    {EVENT_TYPE_NOTICE_ISSUED, EVENT_TYPE_SERVICE_ATTEMPT_RECORDED}
)


# ---------------------------------------------------------------------------
# Audit snapshots (never broadcast)
# ---------------------------------------------------------------------------


def governed_record_full_state_payload(record: GovernedRecord) -> dict[str, object]:
    return {
        "record_id": str(record.record_id),
        "organization_id": str(record.organization_id),
        "record_class": record.record_class,
        "sensitivity": record.sensitivity.value,
        "created_at": record.created_at.isoformat(),
        "retention_policy_id": str(record.retention_policy_id),
        "retention_policy_version": record.retention_policy_version,
        "source_reference": record.source_reference,
        "state": record.state.value,
        "record_version": record.record_version,
        "retention_start_at": (
            record.retention_start_at.isoformat() if record.retention_start_at else None
        ),
        "destruction_authorization_id": (
            str(record.destruction_authorization_id)
            if record.destruction_authorization_id
            else None
        ),
        "destruction_evidence_id": (
            str(record.destruction_evidence_id) if record.destruction_evidence_id else None
        ),
    }


def legal_hold_full_state_payload(hold: LegalHold) -> dict[str, object]:
    return {
        "hold_id": str(hold.hold_id),
        "organization_id": str(hold.organization_id),
        "matter_reference": hold.matter_reference,
        "status": hold.status.value,
        "issued_at": hold.issued_at.isoformat(),
        "released_at": hold.released_at.isoformat() if hold.released_at else None,
        "scope_record_ids": sorted(str(value) for value in hold.scope.record_ids),
        "scope_record_classes": sorted(hold.scope.record_classes),
        "scope_case_ids": sorted(str(value) for value in hold.scope.case_ids),
        "history_length": len(hold.history),
    }


def processing_activity_full_state_payload(activity: ProcessingActivity) -> dict[str, object]:
    return {
        "activity_id": str(activity.activity_id),
        "organization_id": str(activity.organization_id),
        "name": activity.name,
        "purpose": activity.purpose,
        "legal_basis": activity.legal_basis.value,
        "status": activity.status.value,
        "activity_version": activity.activity_version,
        "retention_policy_reference": str(activity.retention_policy_reference),
        "data_subject_categories": list(activity.data_subject_categories),
        "personal_data_categories": list(activity.personal_data_categories),
        "recipient_categories": list(activity.recipient_categories),
        "system_references": list(activity.system_references),
        "valid_from": activity.valid_from.isoformat(),
    }


def procedural_case_full_state_payload(case: ProceduralCase) -> dict[str, object]:
    return {
        "case_id": str(case.case_id),
        "organization_id": str(case.organization_id),
        "case_type": case.case_type.value,
        "workflow_type": case.workflow_type,
        "status": case.status.value,
        "opened_at": case.opened_at.isoformat(),
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "case_version": case.case_version,
        "procedural_authority_reference": str(case.procedural_authority_reference),
        "case_handler_reference": (
            str(case.case_handler_reference) if case.case_handler_reference else None
        ),
        "assigned_decision_maker_reference": (
            str(case.assigned_decision_maker_reference)
            if case.assigned_decision_maker_reference
            else None
        ),
        "decision_id": str(case.decision_id) if case.decision_id else None,
        "outstanding_steps": list(case.outstanding_steps),
        "evidence_reference_count": len(case.evidence_references),
    }


def procedural_deadline_full_state_payload(deadline: ProceduralDeadline) -> dict[str, object]:
    return {
        "deadline_id": str(deadline.deadline_id),
        "definition_id": str(deadline.definition_id),
        "case_id": str(deadline.case_id),
        "organization_id": str(deadline.organization_id),
        "deadline_code": deadline.deadline_code,
        "timezone": deadline.timezone,
        "status": deadline.status.value,
        "due_at": deadline.due_at.isoformat() if deadline.due_at else None,
        "history": [
            {
                "sequence": entry.sequence,
                "event_type": entry.event_type.value,
                "occurred_at": entry.occurred_at.isoformat(),
                "due_at_before": (entry.due_at_before.isoformat() if entry.due_at_before else None),
                "due_at_after": entry.due_at_after.isoformat() if entry.due_at_after else None,
                "remaining_seconds": entry.remaining_seconds,
                "reason_code": entry.reason_code,
            }
            for entry in deadline.history
        ],
        "superseded_by_deadline_id": (
            str(deadline.superseded_by_deadline_id) if deadline.superseded_by_deadline_id else None
        ),
    }


def data_subject_request_full_state_payload(request: DataSubjectRequest) -> dict[str, object]:
    return {
        "request_id": str(request.request_id),
        "case_id": str(request.case_id),
        "organization_id": str(request.organization_id),
        "request_type": request.request_type.value,
        "status": request.status.value,
        "received_at": request.received_at.isoformat(),
        "scope_description_code": request.scope_description_code,
        "identity_verification_status": request.identity_verification_status.value,
        "response_decision": (
            request.response_decision.value if request.response_decision else None
        ),
        "limitation_reason_code": request.limitation_reason_code,
        "request_version": request.request_version,
        "search_result_reference_count": len(request.search_result_references),
    }


# ---------------------------------------------------------------------------
# Wire events
# ---------------------------------------------------------------------------


def build_retention_started_event(
    *,
    event_id: UUID,
    record: GovernedRecord,
    start_event: RetentionStartEvent,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "record_id": str(record.record_id),
        "organization_id": str(record.organization_id),
        "record_class": record.record_class,
        "trigger": start_event.trigger.value,
        "retention_started_at": start_event.occurred_at.isoformat(),
        "retention_policy_id": str(record.retention_policy_id),
        "retention_policy_version": record.retention_policy_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_RETENTION_STARTED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="governed_record", subject_id=record.record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_disposal_authorized_event(
    *,
    event_id: UUID,
    record: GovernedRecord,
    authorization_id: UUID,
    disposition_action: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "record_id": str(record.record_id),
        "organization_id": str(record.organization_id),
        "authorization_id": str(authorization_id),
        "disposition_action": disposition_action,
        "retention_policy_id": str(record.retention_policy_id),
        "retention_policy_version": record.retention_policy_version,
        "record_version": record.record_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DISPOSAL_AUTHORIZED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="governed_record", subject_id=record.record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_record_destroyed_event(
    *,
    event_id: UUID,
    record: GovernedRecord,
    evidence: DestructionEvidence,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """The `governed_record.destroyed` payload deliberately carries the
    *evidence identifier and digest*, never the destroyed content or any
    reconstruction of it."""
    payload: dict[str, object] = {
        "record_id": str(record.record_id),
        "organization_id": str(record.organization_id),
        "evidence_id": str(evidence.evidence_id),
        "authorization_id": str(evidence.authorization_id),
        "disposition_action": evidence.disposition_action.value,
        "evidence_digest": evidence.evidence_digest,
        "executed_at": evidence.executed_at.isoformat(),
        "retention_policy_id": str(evidence.retention_policy_id),
        "retention_policy_version": evidence.retention_policy_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_RECORD_DESTROYED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="governed_record", subject_id=record.record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_legal_hold_status_changed_event(
    *,
    event_id: UUID,
    hold: LegalHold,
    action: str,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "hold_id": str(hold.hold_id),
        "organization_id": str(hold.organization_id),
        "matter_reference": hold.matter_reference,
        "action": action,
        "status": hold.status.value,
        "reason_code": reason_code,
        "scope_record_count": len(hold.scope.record_ids),
        "scope_record_classes": sorted(hold.scope.record_classes),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_LEGAL_HOLD_STATUS_CHANGED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="legal_hold", subject_id=hold.hold_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_processing_activity_status_changed_event(
    *,
    event_id: UUID,
    activity: ProcessingActivity,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "activity_id": str(activity.activity_id),
        "organization_id": str(activity.organization_id),
        "status": activity.status.value,
        "activity_version": activity.activity_version,
        "legal_basis": activity.legal_basis.value,
        "retention_policy_reference": str(activity.retention_policy_reference),
        "reason_code": reason_code,
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_PROCESSING_ACTIVITY_STATUS_CHANGED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="processing_activity", subject_id=activity.activity_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_case_status_changed_event(
    *,
    event_id: UUID,
    case: ProceduralCase,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "case_id": str(case.case_id),
        "organization_id": str(case.organization_id),
        "case_type": case.case_type.value,
        "workflow_type": case.workflow_type,
        "status": case.status.value,
        "case_version": case.case_version,
        "reason_code": reason_code,
        "outstanding_step_count": len(case.outstanding_steps),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_CASE_STATUS_CHANGED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="procedural_case", subject_id=case.case_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_deadline_state_changed_event(
    *,
    event_id: UUID,
    deadline: ProceduralDeadline,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries the *last* history entry's before/after due times plus the
    entry's sequence number, so a consumer can detect a gap without this
    service ever re-sending (or being able to rewrite) earlier
    entries."""
    latest = deadline.history[-1]
    payload: dict[str, object] = {
        "deadline_id": str(deadline.deadline_id),
        "case_id": str(deadline.case_id),
        "organization_id": str(deadline.organization_id),
        "deadline_code": deadline.deadline_code,
        "timezone": deadline.timezone,
        "status": deadline.status.value,
        "sequence": latest.sequence,
        "event_type": latest.event_type.value,
        "due_at_before": latest.due_at_before.isoformat() if latest.due_at_before else None,
        "due_at_after": latest.due_at_after.isoformat() if latest.due_at_after else None,
        "remaining_seconds": latest.remaining_seconds,
        "reason_code": latest.reason_code,
        "superseded_by_deadline_id": (
            str(deadline.superseded_by_deadline_id) if deadline.superseded_by_deadline_id else None
        ),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DEADLINE_STATE_CHANGED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="procedural_deadline", subject_id=deadline.deadline_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_request_status_changed_event(
    *,
    event_id: UUID,
    request: DataSubjectRequest,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries the identity-verification *status* only - never a
    verification attribute, document or eID assertion (invariant 11)."""
    payload: dict[str, object] = {
        "request_id": str(request.request_id),
        "case_id": str(request.case_id),
        "organization_id": str(request.organization_id),
        "request_type": request.request_type.value,
        "status": request.status.value,
        "identity_verification_status": request.identity_verification_status.value,
        "response_decision": (
            request.response_decision.value if request.response_decision else None
        ),
        "limitation_reason_code": request.limitation_reason_code,
        "reason_code": reason_code,
        "request_version": request.request_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_REQUEST_STATUS_CHANGED,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="data_subject_request", subject_id=request.request_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Framework 0.8.1 - audit snapshots for the legal-case substrate
# ---------------------------------------------------------------------------


def legal_case_full_state_payload(case: LegalCase) -> dict[str, object]:
    return {
        "legal_case_id": str(case.legal_case_id),
        "organization_id": str(case.organization_id),
        "case_kind": case.case_kind.value,
        "status": case.status.value,
        "opened_at": case.opened_at.isoformat(),
        "subject_reference": case.subject_reference,
        "confidentiality_class": case.confidentiality_class.value,
        "access_profile": case.access_profile.value,
        "governing_policy_reference": case.governing_policy_reference,
        "jurisdiction_id": str(case.jurisdiction_id) if case.jurisdiction_id else None,
        "parent_case_id": str(case.parent_case_id) if case.parent_case_id else None,
        "prior_case_id": str(case.prior_case_id) if case.prior_case_id else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "closure_reason_code": case.closure_reason_code,
        "reopened_at": case.reopened_at.isoformat() if case.reopened_at else None,
        "reopened_from_case_id": (
            str(case.reopened_from_case_id) if case.reopened_from_case_id else None
        ),
        "case_version": case.case_version,
        "transition_history": [
            {
                "sequence": entry.sequence,
                "status_after": entry.status_after.value,
                "occurred_at": entry.occurred_at.isoformat(),
                "reason_code": entry.reason_code,
                "actor_authority_reference": str(entry.actor_authority_reference),
            }
            for entry in case.transition_history
        ],
    }


def jurisdiction_full_state_payload(
    determination: JurisdictionDetermination,
) -> dict[str, object]:
    return {
        "jurisdiction_id": str(determination.jurisdiction_id),
        "case_id": str(determination.case_id),
        "organization_id": str(determination.organization_id),
        "jurisdiction_type": determination.jurisdiction_type.value,
        "case_kind": determination.case_kind.value,
        "competent_authority_reference": str(determination.competent_authority_reference),
        "status": determination.status.value,
        "determined_at": determination.determined_at.isoformat(),
        "determined_by_authority_reference": str(determination.determined_by_authority_reference),
        "valid_from": determination.valid_from.isoformat(),
        "valid_until": (
            determination.valid_until.isoformat() if determination.valid_until else None
        ),
        "basis_reference": determination.basis_reference,
        "transferred_to_jurisdiction_id": (
            str(determination.transferred_to_jurisdiction_id)
            if determination.transferred_to_jurisdiction_id
            else None
        ),
        "supersedes_jurisdiction_id": (
            str(determination.supersedes_jurisdiction_id)
            if determination.supersedes_jurisdiction_id
            else None
        ),
        "reason_code": determination.reason_code,
    }


def filing_full_state_payload(filing: Filing) -> dict[str, object]:
    """Carries the *counts* of referenced documents and evidence, never
    the references' contents and never the documents themselves - PACK-09
    stores no document bytes (Framework 13.2)."""
    return {
        "filing_id": str(filing.filing_id),
        "case_id": str(filing.case_id),
        "organization_id": str(filing.organization_id),
        "docket_sequence": filing.docket_sequence,
        "filing_type": filing.filing_type.value,
        "filed_by_party_reference": str(filing.filed_by_party_reference),
        "filed_by_representative_reference": (
            str(filing.filed_by_representative_reference)
            if filing.filed_by_representative_reference
            else None
        ),
        "submitted_at": filing.submitted_at.isoformat(),
        "received_at": filing.received_at.isoformat(),
        "intake_state": filing.intake_state.value,
        "document_reference_count": len(filing.document_references),
        "evidence_reference_count": len(filing.evidence_references),
        "supersedes_filing_id": (
            str(filing.supersedes_filing_id) if filing.supersedes_filing_id else None
        ),
        "superseded_by_filing_id": (
            str(filing.superseded_by_filing_id) if filing.superseded_by_filing_id else None
        ),
        "rejection_reason_code": filing.rejection_reason_code,
    }


def hearing_full_state_payload(hearing: Hearing) -> dict[str, object]:
    return {
        "hearing_id": str(hearing.hearing_id),
        "case_id": str(hearing.case_id),
        "organization_id": str(hearing.organization_id),
        "convening_authority_reference": str(hearing.convening_authority_reference),
        "agenda_code": hearing.agenda_code,
        "scheduled_at": hearing.scheduled_at.isoformat(),
        "timezone": hearing.timezone,
        "status": hearing.status.value,
        "submissions_deadline_id": (
            str(hearing.submissions_deadline_id) if hearing.submissions_deadline_id else None
        ),
        "has_minutes_reference": hearing.minutes_reference is not None,
        "evidence_reference_count": len(hearing.evidence_references),
        "attendance": [
            {
                "party_reference": str(record.party_reference),
                "state": record.state.value,
                "recorded_at": record.recorded_at.isoformat(),
            }
            for record in hearing.attendance
        ],
        "history": [
            {
                "sequence": entry.sequence,
                "status_after": entry.status_after.value,
                "occurred_at": entry.occurred_at.isoformat(),
                "scheduled_at_before": (
                    entry.scheduled_at_before.isoformat() if entry.scheduled_at_before else None
                ),
                "scheduled_at_after": (
                    entry.scheduled_at_after.isoformat() if entry.scheduled_at_after else None
                ),
                "reason_code": entry.reason_code,
                "actor_authority_reference": str(entry.actor_authority_reference),
            }
            for entry in hearing.history
        ],
    }


def interim_measure_full_state_payload(measure: InterimMeasure) -> dict[str, object]:
    return {
        "measure_id": str(measure.measure_id),
        "case_id": str(measure.case_id),
        "organization_id": str(measure.organization_id),
        "measure_kind": measure.measure_kind,
        "requested_by_party_reference": str(measure.requested_by_party_reference),
        "decided_by_authority_reference": str(measure.decided_by_authority_reference),
        "decided_by_actor_class": measure.decided_by_actor_class.value,
        "legal_basis_reference": measure.legal_basis_reference,
        "scope_description_code": measure.scope_description_code,
        "status": measure.status.value,
        "decided_at": measure.decided_at.isoformat(),
        "starts_at": measure.starts_at.isoformat(),
        "ends_at": measure.ends_at.isoformat() if measure.ends_at else None,
        "review_due_at": measure.review_due_at.isoformat() if measure.review_due_at else None,
        "reasons_reference": measure.reasons_reference,
        "evidence_reference_count": len(measure.evidence_references),
        "remedy_id": str(measure.remedy_id) if measure.remedy_id else None,
        "lapsed_at": measure.lapsed_at.isoformat() if measure.lapsed_at else None,
        "revoked_at": measure.revoked_at.isoformat() if measure.revoked_at else None,
    }


def procedural_decision_full_state_payload(decision: ProceduralDecision) -> dict[str, object]:
    """The three governed statuses are *derived* from `state_history` and
    are snapshotted alongside it, so an auditor can re-derive them and
    detect any attempt to publish a status the history does not support
    (Framework: effect, finality and enforceability are separate)."""
    return {
        "decision_id": str(decision.decision_id),
        "case_id": str(decision.case_id),
        "organization_id": str(decision.organization_id),
        "decision_type": decision.decision_type.value,
        "deciding_authority_reference": str(decision.deciding_authority_reference),
        "decided_by_party_reference": str(decision.decided_by_party_reference),
        "operative_result": decision.operative_result.value,
        "issued_at": decision.issued_at.isoformat(),
        "effective_at": decision.effective_at.isoformat() if decision.effective_at else None,
        "effect_status": decision.effect_status.value,
        "finality_status": decision.finality_status.value,
        "enforceability_status": decision.enforceability_status.value,
        "reason_code": decision.reason_code,
        "reasons_reference": decision.reasons_reference,
        "evidence_reference_count": len(decision.evidence_references),
        "remedy_id": str(decision.remedy_id) if decision.remedy_id else None,
        "appeal_case_id": str(decision.appeal_case_id) if decision.appeal_case_id else None,
        "reopening_case_id": (
            str(decision.reopening_case_id) if decision.reopening_case_id else None
        ),
        "enforcement_action_reference": decision.enforcement_action_reference,
        "supersedes_decision_id": (
            str(decision.supersedes_decision_id) if decision.supersedes_decision_id else None
        ),
        "decision_version": decision.decision_version,
        "state_history": [
            {
                "sequence": entry.sequence,
                "occurred_at": entry.occurred_at.isoformat(),
                "effect_status": entry.effect_status.value,
                "finality_status": entry.finality_status.value,
                "enforceability_status": entry.enforceability_status.value,
                "reason_code": entry.reason_code,
                "actor_authority_reference": str(entry.actor_authority_reference),
            }
            for entry in decision.state_history
        ],
    }


def remedy_full_state_payload(remedy: Remedy) -> dict[str, object]:
    return {
        "remedy_id": str(remedy.remedy_id),
        "case_id": str(remedy.case_id),
        "organization_id": str(remedy.organization_id),
        "decision_id": str(remedy.decision_id),
        "remedy_kind": remedy.remedy_kind.value,
        "status": remedy.status.value,
        "available_from": remedy.available_from.isoformat(),
        "available_until": (remedy.available_until.isoformat() if remedy.available_until else None),
        "competent_authority_reference": str(remedy.competent_authority_reference),
        "deadline_id": str(remedy.deadline_id) if remedy.deadline_id else None,
        "exercised_at": remedy.exercised_at.isoformat() if remedy.exercised_at else None,
        "resulting_case_id": (str(remedy.resulting_case_id) if remedy.resulting_case_id else None),
    }


def recusal_full_state_payload(recusal: RecusalRecord) -> dict[str, object]:
    """Framework hard invariant 53: recusal blocks capability without
    erasing history. The snapshot therefore keeps
    `prior_participation_codes` - the record of what the recused actor
    already did - rather than deleting it."""
    return {
        "recusal_id": str(recusal.recusal_id),
        "case_id": str(recusal.case_id),
        "organization_id": str(recusal.organization_id),
        "party_reference": str(recusal.party_reference),
        "conflict_declaration_id": str(recusal.conflict_declaration_id),
        "assessment_outcome": recusal.assessment_outcome.value,
        "effective_at": recusal.effective_at.isoformat(),
        "reviewed_by_party_reference": str(recusal.reviewed_by_party_reference),
        "prior_participation_codes": list(recusal.prior_participation_codes),
        "replacement_assignment_id": (
            str(recusal.replacement_assignment_id) if recusal.replacement_assignment_id else None
        ),
        "supersedes_recusal_id": (
            str(recusal.supersedes_recusal_id) if recusal.supersedes_recusal_id else None
        ),
        "blocks_decision_capability": recusal.blocks_decision_capability,
    }


def official_notice_full_state_payload(notice: OfficialNotice) -> dict[str, object]:
    return {
        "notice_id": str(notice.notice_id),
        "case_id": str(notice.case_id),
        "organization_id": str(notice.organization_id),
        "notice_kind": notice.notice_kind.value,
        "issuing_authority_reference": str(notice.issuing_authority_reference),
        "recipient_party_reference": str(notice.recipient_party_reference),
        "authorized_methods": sorted(method.value for method in notice.authorized_methods),
        "issued_at": notice.issued_at.isoformat(),
        "content_reference": notice.content_reference,
        "recipient_is_authorized_service_recipient": (
            notice.recipient_is_authorized_service_recipient
        ),
    }


def service_attempt_full_state_payload(attempt: ServiceAttempt) -> dict[str, object]:
    return {
        "attempt_id": str(attempt.attempt_id),
        "notice_id": str(attempt.notice_id),
        "case_id": str(attempt.case_id),
        "organization_id": str(attempt.organization_id),
        "method": attempt.method.value,
        "attempted_at": attempt.attempted_at.isoformat(),
        "delivery_status": attempt.delivery_status.value,
        "read_status": attempt.read_status.value,
        "provider_reference": attempt.provider_reference,
        "is_reconciled": attempt.is_reconciled,
        "has_proof_package": attempt.proof_package_reference is not None,
        "failure_reason_code": attempt.failure_reason_code,
        "supersedes_attempt_id": (
            str(attempt.supersedes_attempt_id) if attempt.supersedes_attempt_id else None
        ),
    }


def notice_effect_full_state_payload(decision: NoticeEffectDecision) -> dict[str, object]:
    return {
        "effect_id": str(decision.effect_id),
        "notice_id": str(decision.notice_id),
        "case_id": str(decision.case_id),
        "organization_id": str(decision.organization_id),
        "outcome": decision.outcome.value,
        "decided_at": decision.decided_at.isoformat(),
        "decided_by_authority_reference": str(decision.decided_by_authority_reference),
        "deemed_service_rule": decision.deemed_service_rule.value,
        "supporting_attempt_ids": sorted(str(value) for value in decision.supporting_attempt_ids),
        "rule_reference": decision.rule_reference,
        "effective_at": decision.effective_at.isoformat() if decision.effective_at else None,
        "reason_code": decision.reason_code,
        "has_proof_package": decision.proof_package_reference is not None,
        "establishes_legal_effect": decision.establishes_legal_effect,
    }


def deadline_trigger_full_state_payload(trigger: DeadlineTrigger) -> dict[str, object]:
    return {
        "trigger_id": str(trigger.trigger_id),
        "deadline_id": str(trigger.deadline_id),
        "case_id": str(trigger.case_id),
        "organization_id": str(trigger.organization_id),
        "source": trigger.source.value,
        "triggered_at": trigger.triggered_at.isoformat(),
        "notice_effect_id": (str(trigger.notice_effect_id) if trigger.notice_effect_id else None),
        "source_reference": trigger.source_reference,
    }


def record_class_full_state_payload(record_class: RecordClass) -> dict[str, object]:
    return {
        "record_class_id": str(record_class.record_class_id),
        "organization_id": str(record_class.organization_id),
        "record_class_code": record_class.record_class_code,
        "record_category": record_class.record_category,
        "sensitivity": record_class.sensitivity.value,
        "data_classification": record_class.data_classification.value,
        "record_owner_authority_reference": str(record_class.record_owner_authority_reference),
        "custodian_reference": str(record_class.custodian_reference),
        "disposition_authority_reference": str(record_class.disposition_authority_reference),
        "retention_policy_reference": str(record_class.retention_policy_reference),
        "search_export_eligibility": record_class.search_export_eligibility.value,
        "legal_hold_applicable": record_class.legal_hold_applicable,
        "valid_from": record_class.valid_from.isoformat(),
        "valid_until": (record_class.valid_until.isoformat() if record_class.valid_until else None),
        "record_class_version": record_class.record_class_version,
    }


def hold_propagation_full_state_payload(record: HoldPropagationRecord) -> dict[str, object]:
    return {
        "propagation_id": str(record.propagation_id),
        "hold_id": str(record.hold_id),
        "organization_id": str(record.organization_id),
        "derivative_kind": record.derivative_kind.value,
        "derivative_reference": record.derivative_reference,
        "state": record.state.value,
        "recorded_at": record.recorded_at.isoformat(),
        "evidence_reference": record.evidence_reference,
        "failure_reason_code": record.failure_reason_code,
        "is_resolved": record.is_resolved,
    }


def dpia_full_state_payload(dpia: DataProtectionImpactAssessment) -> dict[str, object]:
    return {
        "dpia_id": str(dpia.dpia_id),
        "activity_id": str(dpia.activity_id),
        "organization_id": str(dpia.organization_id),
        "status": dpia.status.value,
        "risk_class": dpia.risk_class.value,
        "reviewer_party_reference": str(dpia.reviewer_party_reference),
        "created_at": dpia.created_at.isoformat(),
        "updated_at": dpia.updated_at.isoformat(),
        "approval_reference": dpia.approval_reference,
        "approved_at": dpia.approved_at.isoformat() if dpia.approved_at else None,
        "valid_until": dpia.valid_until.isoformat() if dpia.valid_until else None,
        "outcome_reason_code": dpia.outcome_reason_code,
        "dpia_version": dpia.dpia_version,
    }


def processing_activation_full_state_payload(
    decision: ProcessingActivationDecision,
) -> dict[str, object]:
    return {
        "activation_decision_id": str(decision.activation_decision_id),
        "activity_id": str(decision.activity_id),
        "organization_id": str(decision.organization_id),
        "state": decision.state.value,
        "decided_at": decision.decided_at.isoformat(),
        "decided_by_authority_reference": str(decision.decided_by_authority_reference),
        "reason_code": decision.reason_code,
        "dpia_id": str(decision.dpia_id) if decision.dpia_id else None,
        "effective_from": (
            decision.effective_from.isoformat() if decision.effective_from else None
        ),
        "revoked_at": decision.revoked_at.isoformat() if decision.revoked_at else None,
    }


# ---------------------------------------------------------------------------
# Framework 0.8.1 - wire events
# ---------------------------------------------------------------------------


def _envelope(
    *,
    event_id: UUID,
    event_type: str,
    subject_type: str,
    subject_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    payload: dict[str, object],
) -> EventEnvelope:
    """Single construction point for every event added in this section.

    Keeping it in one place is what makes the payload discipline
    reviewable: `EVENT_VERSION` and `PRODUCER` cannot drift per event, and
    a reader checking "does any payload carry a party reference?" has
    exactly one funnel to inspect."""
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type=subject_type, subject_id=subject_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


# --- Legal case ------------------------------------------------------------


def build_legal_case_opened_event(
    *,
    event_id: UUID,
    case: LegalCase,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A case exists. It carries no jurisdiction yet unless one was
    determined at intake, and `jurisdiction_id: null` is published
    deliberately - a subscriber must be able to see that no competent
    authority has been established (Framework hard invariant 52)."""
    payload: dict[str, object] = {
        "legal_case_id": str(case.legal_case_id),
        "organization_id": str(case.organization_id),
        "case_kind": case.case_kind.value,
        "status": case.status.value,
        "opened_at": case.opened_at.isoformat(),
        "confidentiality_class": case.confidentiality_class.value,
        "access_profile": case.access_profile.value,
        "governing_policy_reference": case.governing_policy_reference,
        "jurisdiction_id": str(case.jurisdiction_id) if case.jurisdiction_id else None,
        "parent_case_id": str(case.parent_case_id) if case.parent_case_id else None,
        "case_version": case.case_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_LEGAL_CASE_OPENED,
        subject_type="legal_case",
        subject_id=case.legal_case_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_legal_case_status_changed_event(
    *,
    event_id: UUID,
    case: LegalCase,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries the newest transition entry's sequence and reason code. The
    status itself is derived from the append-only history, never stored,
    so this payload cannot disagree with the record."""
    latest = case.transition_history[-1]
    payload: dict[str, object] = {
        "legal_case_id": str(case.legal_case_id),
        "organization_id": str(case.organization_id),
        "case_kind": case.case_kind.value,
        "status": case.status.value,
        "sequence": latest.sequence,
        "reason_code": latest.reason_code,
        "confidentiality_class": case.confidentiality_class.value,
        "jurisdiction_id": str(case.jurisdiction_id) if case.jurisdiction_id else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "closure_reason_code": case.closure_reason_code,
        "case_version": case.case_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_LEGAL_CASE_STATUS_CHANGED,
        subject_type="legal_case",
        subject_id=case.legal_case_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_legal_case_reopened_event(
    *,
    event_id: UUID,
    case: LegalCase,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Reopening produces a *new* case that points at the prior one. The
    prior case is not resurrected and its closure is not erased
    (Framework: history is append-only)."""
    latest = case.transition_history[-1]
    payload: dict[str, object] = {
        "legal_case_id": str(case.legal_case_id),
        "organization_id": str(case.organization_id),
        "case_kind": case.case_kind.value,
        "status": case.status.value,
        "reopened_at": case.reopened_at.isoformat() if case.reopened_at else None,
        "reopened_from_case_id": (
            str(case.reopened_from_case_id) if case.reopened_from_case_id else None
        ),
        "prior_case_id": str(case.prior_case_id) if case.prior_case_id else None,
        "sequence": latest.sequence,
        "reason_code": latest.reason_code,
        "case_version": case.case_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_LEGAL_CASE_REOPENED,
        subject_type="legal_case",
        subject_id=case.legal_case_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Jurisdiction ----------------------------------------------------------


def _jurisdiction_payload(
    determination: JurisdictionDetermination, occurred_at: datetime
) -> dict[str, object]:
    return {
        "jurisdiction_id": str(determination.jurisdiction_id),
        "case_id": str(determination.case_id),
        "organization_id": str(determination.organization_id),
        "jurisdiction_type": determination.jurisdiction_type.value,
        "case_kind": determination.case_kind.value,
        "status": determination.status.value,
        "determined_at": determination.determined_at.isoformat(),
        "valid_from": determination.valid_from.isoformat(),
        "valid_until": (
            determination.valid_until.isoformat() if determination.valid_until else None
        ),
        "basis_reference": determination.basis_reference,
        "reason_code": determination.reason_code,
        "recorded_at": occurred_at.isoformat(),
    }


def build_jurisdiction_determined_event(
    *,
    event_id: UUID,
    determination: JurisdictionDetermination,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes that competence was *decided*, and on what basis - never
    which authority holds it. Framework hard invariant 15: a role name is
    not proof of authority, so a subscriber that needs the competent
    authority must ask this service and present a `RequestContext`."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_JURISDICTION_DETERMINED,
        subject_type="jurisdiction_determination",
        subject_id=determination.jurisdiction_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_jurisdiction_payload(determination, occurred_at),
    )


def build_jurisdiction_challenged_event(
    *,
    event_id: UUID,
    determination: JurisdictionDetermination,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A challenged determination no longer permits a substantive
    decision. Subscribers that gate on jurisdiction must react to this,
    which is why it is a distinct event type rather than a status field on
    a generic `jurisdiction.changed`."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_JURISDICTION_CHALLENGED,
        subject_type="jurisdiction_determination",
        subject_id=determination.jurisdiction_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_jurisdiction_payload(determination, occurred_at),
    )


def build_jurisdiction_transferred_event(
    *,
    event_id: UUID,
    determination: JurisdictionDetermination,
    successor_jurisdiction_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Transfer closes the outgoing determination's validity window and
    names its successor. It does not delete the outgoing determination:
    what the previously-competent authority did while competent stays on
    the record."""
    payload = _jurisdiction_payload(determination, occurred_at)
    payload["successor_jurisdiction_id"] = str(successor_jurisdiction_id)
    payload["transferred_to_jurisdiction_id"] = (
        str(determination.transferred_to_jurisdiction_id)
        if determination.transferred_to_jurisdiction_id
        else None
    )
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_JURISDICTION_TRANSFERRED,
        subject_type="jurisdiction_determination",
        subject_id=determination.jurisdiction_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Parties and representation --------------------------------------------


def build_case_party_registered_event(
    *,
    event_id: UUID,
    party: CaseParty,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes the *role* and the fact that a party now exists on the
    case - never the party handle itself, and emphatically never anything
    that could identify a person (Framework hard invariant 1)."""
    payload: dict[str, object] = {
        "case_party_id": str(party.case_party_id),
        "case_id": str(party.case_id),
        "organization_id": str(party.organization_id),
        "role": party.role.value,
        "registered_at": party.registered_at.isoformat(),
        "is_authorized_service_recipient": party.is_authorized_service_recipient,
        "display_label_code": party.display_label_code,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_CASE_PARTY_REGISTERED,
        subject_type="case_party",
        subject_id=party.case_party_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def _representation_payload(
    mandate: RepresentationMandate, occurred_at: datetime
) -> dict[str, object]:
    return {
        "mandate_id": str(mandate.mandate_id),
        "case_id": str(mandate.case_id),
        "organization_id": str(mandate.organization_id),
        "status": mandate.status.value,
        "authorities": sorted(authority.value for authority in mandate.authorities),
        "valid_from": mandate.valid_from.isoformat(),
        "valid_until": mandate.valid_until.isoformat() if mandate.valid_until else None,
        "revoked_at": mandate.revoked_at.isoformat() if mandate.revoked_at else None,
        "revocation_reason_code": mandate.revocation_reason_code,
        "mandate_basis_reference": mandate.mandate_basis_reference,
        "recorded_at": occurred_at.isoformat(),
    }


def build_representation_registered_event(
    *,
    event_id: UUID,
    mandate: RepresentationMandate,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries the enumerated authorities the mandate grants. A consumer
    can therefore tell that a representative may receive service but may
    not settle, without learning who either party is."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_REPRESENTATION_REGISTERED,
        subject_type="representation_mandate",
        subject_id=mandate.mandate_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_representation_payload(mandate, occurred_at),
    )


def build_representation_revoked_event(
    *,
    event_id: UUID,
    mandate: RepresentationMandate,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Revocation is a separate event because it invalidates *future*
    acts only: filings already accepted under the mandate stay valid, and
    nothing in this payload suggests otherwise."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_REPRESENTATION_REVOKED,
        subject_type="representation_mandate",
        subject_id=mandate.mandate_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_representation_payload(mandate, occurred_at),
    )


# --- Filings and docket ----------------------------------------------------


def _filing_payload(filing: Filing, occurred_at: datetime) -> dict[str, object]:
    return {
        "filing_id": str(filing.filing_id),
        "case_id": str(filing.case_id),
        "organization_id": str(filing.organization_id),
        "docket_sequence": filing.docket_sequence,
        "filing_type": filing.filing_type.value,
        "submitted_at": filing.submitted_at.isoformat(),
        "received_at": filing.received_at.isoformat(),
        "intake_state": filing.intake_state.value,
        "document_reference_count": len(filing.document_references),
        "evidence_reference_count": len(filing.evidence_references),
        "supersedes_filing_id": (
            str(filing.supersedes_filing_id) if filing.supersedes_filing_id else None
        ),
        "superseded_by_filing_id": (
            str(filing.superseded_by_filing_id) if filing.superseded_by_filing_id else None
        ),
        "rejection_reason_code": filing.rejection_reason_code,
        "recorded_at": occurred_at.isoformat(),
    }


def build_filing_received_event(
    *,
    event_id: UUID,
    filing: Filing,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`submitted_at` and `received_at` are both published and are
    deliberately distinct: procedural deadlines that run from receipt must
    not silently use the submitter's clock."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_FILING_RECEIVED,
        subject_type="filing",
        subject_id=filing.filing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_filing_payload(filing, occurred_at),
    )


def build_filing_admissibility_decided_event(
    *,
    event_id: UUID,
    filing: Filing,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Receipt and admission are separate facts. A rejected filing stays
    on the docket at its original sequence with a reason code; it is never
    removed."""
    payload = _filing_payload(filing, occurred_at)
    payload["reason_code"] = reason_code
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_FILING_ADMISSIBILITY_DECIDED,
        subject_type="filing",
        subject_id=filing.filing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_filing_superseded_event(
    *,
    event_id: UUID,
    filing: Filing,
    successor_filing_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Correction is supersession, not mutation: the superseded filing
    keeps its docket sequence and its content reference, and points
    forward."""
    payload = _filing_payload(filing, occurred_at)
    payload["successor_filing_id"] = str(successor_filing_id)
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_FILING_SUPERSEDED,
        subject_type="filing",
        subject_id=filing.filing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Hearings --------------------------------------------------------------


def _hearing_payload(hearing: Hearing, occurred_at: datetime) -> dict[str, object]:
    latest = hearing.history[-1]
    return {
        "hearing_id": str(hearing.hearing_id),
        "case_id": str(hearing.case_id),
        "organization_id": str(hearing.organization_id),
        "agenda_code": hearing.agenda_code,
        "scheduled_at": hearing.scheduled_at.isoformat(),
        "timezone": hearing.timezone,
        "status": hearing.status.value,
        "sequence": latest.sequence,
        "reason_code": latest.reason_code,
        "scheduled_at_before": (
            latest.scheduled_at_before.isoformat() if latest.scheduled_at_before else None
        ),
        "scheduled_at_after": (
            latest.scheduled_at_after.isoformat() if latest.scheduled_at_after else None
        ),
        "submissions_deadline_id": (
            str(hearing.submissions_deadline_id) if hearing.submissions_deadline_id else None
        ),
        "attendance_record_count": len(hearing.attendance),
        "has_minutes_reference": hearing.minutes_reference is not None,
        "recorded_at": occurred_at.isoformat(),
    }


def build_hearing_scheduled_event(
    *,
    event_id: UUID,
    hearing: Hearing,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes the scheduled instant *and* the hearing's timezone, so a
    consumer computing a local-time notice period cannot silently apply
    its own."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_HEARING_SCHEDULED,
        subject_type="hearing",
        subject_id=hearing.hearing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_hearing_payload(hearing, occurred_at),
    )


def build_hearing_rescheduled_event(
    *,
    event_id: UUID,
    hearing: Hearing,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries both the previous and the new instant. Rescheduling a
    hearing does not by itself move any deadline - that requires its own
    governed decision (Framework hard invariant 60)."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_HEARING_RESCHEDULED,
        subject_type="hearing",
        subject_id=hearing.hearing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_hearing_payload(hearing, occurred_at),
    )


def build_hearing_cancelled_event(
    *,
    event_id: UUID,
    hearing: Hearing,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_HEARING_CANCELLED,
        subject_type="hearing",
        subject_id=hearing.hearing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_hearing_payload(hearing, occurred_at),
    )


def build_hearing_completed_event(
    *,
    event_id: UUID,
    hearing: Hearing,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`has_minutes_reference` is a boolean, not the reference: PACK-11
    owns the minutes and decides who may resolve a pointer to them."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_HEARING_COMPLETED,
        subject_type="hearing",
        subject_id=hearing.hearing_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_hearing_payload(hearing, occurred_at),
    )


# --- Interim measures ------------------------------------------------------


def build_interim_measure_decided_event(
    *,
    event_id: UUID,
    measure: InterimMeasure,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes `decided_by_actor_class` by name.

    Framework hard invariant 69: AI decides no consequential legal
    outcomes. A granted interim measure can only be constructed with
    `ActorClass.HUMAN_AUTHORITY`, and putting that class on the wire makes
    the guarantee checkable by any subscriber rather than only by this
    service's own tests."""
    payload: dict[str, object] = {
        "measure_id": str(measure.measure_id),
        "case_id": str(measure.case_id),
        "organization_id": str(measure.organization_id),
        "measure_kind": measure.measure_kind,
        "decided_by_actor_class": measure.decided_by_actor_class.value,
        "legal_basis_reference": measure.legal_basis_reference,
        "scope_description_code": measure.scope_description_code,
        "status": measure.status.value,
        "decided_at": measure.decided_at.isoformat(),
        "starts_at": measure.starts_at.isoformat(),
        "ends_at": measure.ends_at.isoformat() if measure.ends_at else None,
        "review_due_at": measure.review_due_at.isoformat() if measure.review_due_at else None,
        "has_reasons_reference": bool(measure.reasons_reference),
        "remedy_id": str(measure.remedy_id) if measure.remedy_id else None,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_INTERIM_MEASURE_DECIDED,
        subject_type="interim_measure",
        subject_id=measure.measure_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Procedural decisions --------------------------------------------------


def _decision_payload(decision: ProceduralDecision, occurred_at: datetime) -> dict[str, object]:
    latest = decision.state_history[-1]
    return {
        "decision_id": str(decision.decision_id),
        "case_id": str(decision.case_id),
        "organization_id": str(decision.organization_id),
        "decision_type": decision.decision_type.value,
        "operative_result": decision.operative_result.value,
        "issued_at": decision.issued_at.isoformat(),
        "effective_at": decision.effective_at.isoformat() if decision.effective_at else None,
        "effect_status": decision.effect_status.value,
        "finality_status": decision.finality_status.value,
        "enforceability_status": decision.enforceability_status.value,
        "sequence": latest.sequence,
        "reason_code": latest.reason_code,
        "has_reasons_reference": bool(decision.reasons_reference),
        "remedy_id": str(decision.remedy_id) if decision.remedy_id else None,
        "appeal_case_id": str(decision.appeal_case_id) if decision.appeal_case_id else None,
        "supersedes_decision_id": (
            str(decision.supersedes_decision_id) if decision.supersedes_decision_id else None
        ),
        "decision_version": decision.decision_version,
        "recorded_at": occurred_at.isoformat(),
    }


def build_procedural_decision_issued_event(
    *,
    event_id: UUID,
    decision: ProceduralDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Issuance is not effect, finality or enforceability. All three are
    published as separate fields on the same payload precisely so a
    consumer cannot collapse them: a decision may be issued and in effect
    while still appealable, and appealable while not yet enforceable."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_PROCEDURAL_DECISION_ISSUED,
        subject_type="procedural_decision",
        subject_id=decision.decision_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_decision_payload(decision, occurred_at),
    )


def build_decision_effect_changed_event(
    *,
    event_id: UUID,
    decision: ProceduralDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Commencement, suspension and resumption of legal effect. Suspending
    effect also stays enforceability, and the payload carries both statuses
    so a subscriber cannot act on a stale enforceability value."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DECISION_EFFECT_CHANGED,
        subject_type="procedural_decision",
        subject_id=decision.decision_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_decision_payload(decision, occurred_at),
    )


def build_decision_finality_changed_event(
    *,
    event_id: UUID,
    decision: ProceduralDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Finality means the remedy window closed or was exhausted. It does
    not imply enforceability, and this service never derives one from the
    other."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DECISION_FINALITY_CHANGED,
        subject_type="procedural_decision",
        subject_id=decision.decision_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_decision_payload(decision, occurred_at),
    )


def build_decision_enforceability_changed_event(
    *,
    event_id: UUID,
    decision: ProceduralDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Enforceability is the narrowest of the three and the only one that
    licenses a consequential action downstream. `ProceduralDecision`
    refuses to become enforceable unless it is in effect, so a subscriber
    can rely on `effect_status` in this payload being `IN_EFFECT`."""
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DECISION_ENFORCEABILITY_CHANGED,
        subject_type="procedural_decision",
        subject_id=decision.decision_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=_decision_payload(decision, occurred_at),
    )


def build_remedy_registered_event(
    *,
    event_id: UUID,
    remedy: Remedy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Framework hard invariant 52 requires a remedy route to exist before
    a sanction may stand. Publishing the remedy - its kind, its window and
    the deadline that governs it - is what lets a downstream pack verify
    that requirement instead of assuming it."""
    payload: dict[str, object] = {
        "remedy_id": str(remedy.remedy_id),
        "case_id": str(remedy.case_id),
        "organization_id": str(remedy.organization_id),
        "decision_id": str(remedy.decision_id),
        "remedy_kind": remedy.remedy_kind.value,
        "status": remedy.status.value,
        "available_from": remedy.available_from.isoformat(),
        "available_until": (remedy.available_until.isoformat() if remedy.available_until else None),
        "deadline_id": str(remedy.deadline_id) if remedy.deadline_id else None,
        "exercised_at": remedy.exercised_at.isoformat() if remedy.exercised_at else None,
        "resulting_case_id": (str(remedy.resulting_case_id) if remedy.resulting_case_id else None),
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_REMEDY_REGISTERED,
        subject_type="remedy",
        subject_id=remedy.remedy_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Recusal and replacement -----------------------------------------------


def build_recusal_recorded_event(
    *,
    event_id: UUID,
    recusal: RecusalRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes `blocks_decision_capability` and the *count* of prior
    participations, never the participations themselves and never the
    recused party's handle. Framework hard invariant 53: capability is
    blocked, history is not erased."""
    payload: dict[str, object] = {
        "recusal_id": str(recusal.recusal_id),
        "case_id": str(recusal.case_id),
        "organization_id": str(recusal.organization_id),
        "conflict_declaration_id": str(recusal.conflict_declaration_id),
        "assessment_outcome": recusal.assessment_outcome.value,
        "effective_at": recusal.effective_at.isoformat(),
        "blocks_decision_capability": recusal.blocks_decision_capability,
        "prior_participation_count": len(recusal.prior_participation_codes),
        "replacement_assignment_id": (
            str(recusal.replacement_assignment_id) if recusal.replacement_assignment_id else None
        ),
        "supersedes_recusal_id": (
            str(recusal.supersedes_recusal_id) if recusal.supersedes_recusal_id else None
        ),
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_RECUSAL_RECORDED,
        subject_type="recusal_record",
        subject_id=recusal.recusal_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_replacement_assigned_event(
    *,
    event_id: UUID,
    assignment: ReplacementAssignment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A recusal that blocks capability without a replacement leaves the
    case unable to proceed. This event is what tells a workflow consumer
    that the gap was closed - without naming who closed it."""
    payload: dict[str, object] = {
        "assignment_id": str(assignment.assignment_id),
        "case_id": str(assignment.case_id),
        "organization_id": str(assignment.organization_id),
        "recusal_id": str(assignment.recusal_id),
        "assigned_at": assignment.assigned_at.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_REPLACEMENT_ASSIGNED,
        subject_type="replacement_assignment",
        subject_id=assignment.assignment_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Official notice: three events, three trust levels ---------------------


def build_notice_issued_event(
    *,
    event_id: UUID,
    notice: OfficialNotice,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """An authorized notice object now exists.

    This event starts nothing. It carries `establishes_legal_effect:
    false` as a literal field so that a subscriber which mistakenly wires
    this event to a deadline has to override an explicit denial rather
    than merely omit a check (Framework hard invariant 40)."""
    payload: dict[str, object] = {
        "notice_id": str(notice.notice_id),
        "case_id": str(notice.case_id),
        "organization_id": str(notice.organization_id),
        "notice_kind": notice.notice_kind.value,
        "authorized_methods": sorted(method.value for method in notice.authorized_methods),
        "issued_at": notice.issued_at.isoformat(),
        "recipient_is_authorized_service_recipient": (
            notice.recipient_is_authorized_service_recipient
        ),
        "establishes_legal_effect": False,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_NOTICE_ISSUED,
        subject_type="official_notice",
        subject_id=notice.notice_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_service_attempt_recorded_event(
    *,
    event_id: UUID,
    attempt: ServiceAttempt,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Provider telemetry, and nothing more.

    `delivery_status` and `read_status` are published under names that say
    "telemetry", and `establishes_legal_effect: false` is again literal.
    Framework hard invariant 39 ("delivery/read telemetry is not legally
    effective notice") and 57 ("provider status is not internal legal
    effect without validation and reconciliation") are both about this
    event specifically - which is why `is_reconciled` travels with it."""
    payload: dict[str, object] = {
        "attempt_id": str(attempt.attempt_id),
        "notice_id": str(attempt.notice_id),
        "case_id": str(attempt.case_id),
        "organization_id": str(attempt.organization_id),
        "method": attempt.method.value,
        "attempted_at": attempt.attempted_at.isoformat(),
        "delivery_telemetry_status": attempt.delivery_status.value,
        "read_telemetry_status": attempt.read_status.value,
        "is_reconciled": attempt.is_reconciled,
        "has_proof_package": attempt.proof_package_reference is not None,
        "failure_reason_code": attempt.failure_reason_code,
        "supersedes_attempt_id": (
            str(attempt.supersedes_attempt_id) if attempt.supersedes_attempt_id else None
        ),
        "establishes_legal_effect": False,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_SERVICE_ATTEMPT_RECORDED,
        subject_type="service_attempt",
        subject_id=attempt.attempt_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_notice_effect_determined_event(
    *,
    event_id: UUID,
    decision: NoticeEffectDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """The governed determination - the only notice event that can carry
    `establishes_legal_effect: true`.

    It publishes the deemed-service rule applied, the rule reference, and
    the *count* of supporting attempts. The attempt ids themselves stay in
    the audit snapshot: a consumer that needs to re-examine the evidence
    must come back through an authorized read, not reconstruct it from a
    broadcast."""
    payload: dict[str, object] = {
        "effect_id": str(decision.effect_id),
        "notice_id": str(decision.notice_id),
        "case_id": str(decision.case_id),
        "organization_id": str(decision.organization_id),
        "outcome": decision.outcome.value,
        "decided_at": decision.decided_at.isoformat(),
        "deemed_service_rule": decision.deemed_service_rule.value,
        "rule_reference": decision.rule_reference,
        "supporting_attempt_count": len(decision.supporting_attempt_ids),
        "effective_at": decision.effective_at.isoformat() if decision.effective_at else None,
        "reason_code": decision.reason_code,
        "has_proof_package": decision.proof_package_reference is not None,
        "establishes_legal_effect": decision.establishes_legal_effect,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_NOTICE_EFFECT_DETERMINED,
        subject_type="notice_effect_decision",
        subject_id=decision.effect_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_deadline_triggered_event(
    *,
    event_id: UUID,
    trigger: DeadlineTrigger,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Records which governed source started which deadline, once.

    The trigger store is create-once per deadline, so a replayed command
    cannot produce a second `procedural_deadline.triggered` for the same
    deadline (Framework hard invariant 59: retry/replay does not repeat a
    consequential legal effect). `notice_effect_id` is non-null whenever
    `source` is the notice-effect source, and a consumer can assert that
    pairing."""
    payload: dict[str, object] = {
        "trigger_id": str(trigger.trigger_id),
        "deadline_id": str(trigger.deadline_id),
        "case_id": str(trigger.case_id),
        "organization_id": str(trigger.organization_id),
        "source": trigger.source.value,
        "triggered_at": trigger.triggered_at.isoformat(),
        "notice_effect_id": (str(trigger.notice_effect_id) if trigger.notice_effect_id else None),
        "source_reference": trigger.source_reference,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DEADLINE_TRIGGERED,
        subject_type="procedural_deadline",
        subject_id=trigger.deadline_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Records classification and hold propagation ---------------------------


def build_record_class_registered_event(
    *,
    event_id: UUID,
    record_class: RecordClass,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Publishes the class's data classification, search/export
    eligibility and hold applicability - the three facts a downstream pack
    needs to decide whether it may index, export or delete something -
    without publishing the custodian or the disposition authority."""
    payload: dict[str, object] = {
        "record_class_id": str(record_class.record_class_id),
        "organization_id": str(record_class.organization_id),
        "record_class_code": record_class.record_class_code,
        "record_category": record_class.record_category,
        "sensitivity": record_class.sensitivity.value,
        "data_classification": record_class.data_classification.value,
        "search_export_eligibility": record_class.search_export_eligibility.value,
        "legal_hold_applicable": record_class.legal_hold_applicable,
        "retention_policy_reference": str(record_class.retention_policy_reference),
        "valid_from": record_class.valid_from.isoformat(),
        "valid_until": (record_class.valid_until.isoformat() if record_class.valid_until else None),
        "record_class_version": record_class.record_class_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_RECORD_CLASS_REGISTERED,
        subject_type="record_class",
        subject_id=record_class.record_class_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_hold_propagation_registered_event(
    *,
    event_id: UUID,
    propagation: HoldPropagationRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A legal hold that has not reached a replica, index or export is not
    an effective hold. `state` is published explicitly - including
    `UNKNOWN` and `FAILED` - so an unresolved propagation is visible
    rather than silently absent (Framework section 11)."""
    payload: dict[str, object] = {
        "propagation_id": str(propagation.propagation_id),
        "hold_id": str(propagation.hold_id),
        "organization_id": str(propagation.organization_id),
        "derivative_kind": propagation.derivative_kind.value,
        "derivative_reference": propagation.derivative_reference,
        "state": propagation.state.value,
        "is_resolved": propagation.is_resolved,
        "failure_reason_code": propagation.failure_reason_code,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_HOLD_PROPAGATION_REGISTERED,
        subject_type="legal_hold",
        subject_id=propagation.hold_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


# --- Data-protection governance and the DPIA gate --------------------------


def build_dpia_requirement_determined_event(
    *,
    event_id: UUID,
    determination: DPIARequirementDetermination,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """The determination is published even when `dpia_required` is false,
    because its *absence* is what blocks activation. A consumer that never
    sees this event for an activity knows the gate has not been evaluated,
    not that it passed."""
    payload: dict[str, object] = {
        "determination_id": str(determination.determination_id),
        "activity_id": str(determination.activity_id),
        "organization_id": str(determination.organization_id),
        "risk_class": determination.risk_class.value,
        "dpia_required": determination.dpia_required,
        "determined_at": determination.determined_at.isoformat(),
        "basis_reference": determination.basis_reference,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DPIA_REQUIREMENT_DETERMINED,
        subject_type="dpia_requirement_determination",
        subject_id=determination.determination_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_dpia_status_changed_event(
    *,
    event_id: UUID,
    dpia: DataProtectionImpactAssessment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Carries `is_activating` as evaluated at this event's own
    `occurred_at`, so a subscriber cannot read `status: APPROVED` and miss
    that the approval had already expired."""
    payload: dict[str, object] = {
        "dpia_id": str(dpia.dpia_id),
        "activity_id": str(dpia.activity_id),
        "organization_id": str(dpia.organization_id),
        "status": dpia.status.value,
        "risk_class": dpia.risk_class.value,
        "approved_at": dpia.approved_at.isoformat() if dpia.approved_at else None,
        "valid_until": dpia.valid_until.isoformat() if dpia.valid_until else None,
        "outcome_reason_code": dpia.outcome_reason_code,
        "is_activating": dpia.is_activating_at(occurred_at),
        "dpia_version": dpia.dpia_version,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_DPIA_STATUS_CHANGED,
        subject_type="data_protection_impact_assessment",
        subject_id=dpia.dpia_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def build_processing_activation_decided_event(
    *,
    event_id: UUID,
    decision: ProcessingActivationDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A processing activity does not become active because a DPIA was
    approved; it becomes active because someone with authority decided so
    and that decision was recorded. Blocked and revoked activations are
    published through this same event type, with the reason code, so a
    consumer sees the refusal rather than silence."""
    payload: dict[str, object] = {
        "activation_decision_id": str(decision.activation_decision_id),
        "activity_id": str(decision.activity_id),
        "organization_id": str(decision.organization_id),
        "state": decision.state.value,
        "decided_at": decision.decided_at.isoformat(),
        "reason_code": decision.reason_code,
        "dpia_id": str(decision.dpia_id) if decision.dpia_id else None,
        "effective_from": (
            decision.effective_from.isoformat() if decision.effective_from else None
        ),
        "revoked_at": decision.revoked_at.isoformat() if decision.revoked_at else None,
        "recorded_at": occurred_at.isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=EVENT_TYPE_PROCESSING_ACTIVATION_DECIDED,
        subject_type="processing_activation_decision",
        subject_id=decision.activation_decision_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        payload=payload,
    )
