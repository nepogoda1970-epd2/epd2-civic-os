"""CT-00-01 Schema Validation (canon section 27), PACK-09 additions
(Compliance, Records Governance & Legal Workflows; ADR-038 through
ADR-042) - added alongside (never replacing)
`test_ct00_01_schema_validation.py`'s PACK-02 through PACK-07 coverage and
`test_ct00_01_pack08_schema_validation.py`'s PACK-08 coverage, following
the precedent those two files set for a new, schema-heavy pack: a
dedicated new file rather than an edit to the giant pre-existing one.

Validates every PACK-09 entity schema under `contracts/schemas/` and every
PACK-09 event payload schema under `contracts/events/` against real,
directly-constructed domain instances and real event envelopes built by
`epd2_compliance_service.events` - each one satisfying every structural
`__post_init__` invariant the domain class enforces. A schema that
drifted from the code it documents fails here rather than in production.

Requires nothing beyond `epd2_core.minimal_json_schema` (always
available, stdlib-only) for validation itself.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from _schema_helpers import load_event_schema, load_schema, to_jsonable

from epd2_compliance_service.domain import (
    CaseDecision,
    CaseStatus,
    CaseType,
    ConflictOfInterestDeclaration,
    ConflictState,
    CrossScopeAuthorityGrant,
    DataAsset,
    DataSubjectRequest,
    DataSubjectRequestStatus,
    DataSubjectRequestType,
    DeadlineDefinition,
    DecisionOutcome,
    DestructionAuthorization,
    DestructionEvidence,
    DispositionAction,
    GovernedRecord,
    GovernedRecordState,
    IdentityVerificationStatus,
    LegalBasis,
    LegalHold,
    LegalHoldScope,
    ProceduralCase,
    ProceduralDeadline,
    ProceduralRole,
    ProceduralStep,
    ProcessingActivity,
    RecordSensitivity,
    RegistryEntryStatus,
    RetentionPolicy,
    RetentionStartEvent,
    RetentionTrigger,
    ScopeCapability,
    build_started_deadline,
    mint_case_party_reference,
)
from epd2_compliance_service.events import (
    build_case_status_changed_event,
    build_deadline_state_changed_event,
    build_disposal_authorized_event,
    build_legal_hold_status_changed_event,
    build_processing_activity_status_changed_event,
    build_record_destroyed_event,
    build_request_status_changed_event,
    build_retention_started_event,
)
from epd2_core.event_envelope import ActorRef
from epd2_core.minimal_json_schema import validate

_OCCURRED_AT = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
_ORGANIZATION_ID = uuid4()
_BERLIN = "Europe/Berlin"
_REASON = "COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED"


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


def _policy(*, version: int = 1, policy_id: UUID | None = None) -> RetentionPolicy:
    return RetentionPolicy(
        policy_id=policy_id if policy_id is not None else uuid4(),
        organization_id=_ORGANIZATION_ID,
        record_class="case.disciplinary",
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        retention_days=30,
        disposition_action=DispositionAction.DELETE,
        policy_version=version,
        valid_from=_OCCURRED_AT,
        valid_until=None,
        supersedes_policy_version=version - 1 if version > 1 else None,
        authorizing_decision_reference=uuid4(),
    )


def _record(policy: RetentionPolicy, **overrides: Any) -> GovernedRecord:
    base = {
        "record_id": uuid4(),
        "organization_id": policy.organization_id,
        "record_class": policy.record_class,
        "sensitivity": RecordSensitivity.CONFIDENTIAL,
        "created_at": _OCCURRED_AT,
        "retention_policy_id": policy.policy_id,
        "retention_policy_version": policy.policy_version,
        "source_reference": "membership-service:case:1",
        "retention_start_at": _OCCURRED_AT,
    }
    base.update(overrides)
    return GovernedRecord(**base)  # type: ignore[arg-type]


def _instance(entity: Any, fields: dict[str, Any]) -> dict[str, Any]:
    """Round-trip a hand-built wire instance through `to_jsonable` so
    UUID/datetime/Enum values become the plain JSON types a real payload
    would carry."""
    assert entity is not None
    return to_jsonable(fields)


# ---------------------------------------------------------------------------
# Entity schemas (contracts/schemas/)
# ---------------------------------------------------------------------------


def test_retention_policy_instance_validates() -> None:
    policy = _policy(version=2)
    validate(
        _instance(
            policy,
            {
                "policy_id": policy.policy_id,
                "organization_id": policy.organization_id,
                "record_class": policy.record_class,
                "trigger": policy.trigger.value,
                "retention_days": policy.retention_days,
                "disposition_action": policy.disposition_action.value,
                "policy_version": policy.policy_version,
                "valid_from": policy.valid_from.isoformat(),
                "valid_until": None,
                "supersedes_policy_version": policy.supersedes_policy_version,
                "authorizing_decision_reference": policy.authorizing_decision_reference,
            },
        ),
        load_schema("retention-policy.schema.json"),
    )


def test_governed_record_instance_validates() -> None:
    policy = _policy()
    record = _record(policy)
    validate(
        _instance(
            record,
            {
                "record_id": record.record_id,
                "organization_id": record.organization_id,
                "record_class": record.record_class,
                "sensitivity": record.sensitivity.value,
                "created_at": record.created_at.isoformat(),
                "retention_policy_id": record.retention_policy_id,
                "retention_policy_version": record.retention_policy_version,
                "source_reference": record.source_reference,
                "state": record.state.value,
                "record_version": record.record_version,
                "retention_start_at": record.retention_start_at.isoformat()
                if record.retention_start_at
                else None,
                "destruction_authorization_id": None,
                "destruction_evidence_id": None,
            },
        ),
        load_schema("governed-record.schema.json"),
    )


def test_retention_start_event_instance_validates() -> None:
    event = RetentionStartEvent(
        retention_start_event_id=uuid4(),
        record_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        occurred_at=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
        source_reference="case:1",
    )
    validate(
        _instance(
            event,
            {
                "retention_start_event_id": event.retention_start_event_id,
                "record_id": event.record_id,
                "organization_id": event.organization_id,
                "trigger": event.trigger.value,
                "occurred_at": event.occurred_at.isoformat(),
                "recorded_at": event.recorded_at.isoformat(),
                "source_reference": event.source_reference,
            },
        ),
        load_schema("retention-start-event.schema.json"),
    )


def _hold() -> LegalHold:
    return LegalHold(
        hold_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        matter_reference="matter/2026-1",
        scope=LegalHoldScope(
            record_ids=frozenset({uuid4()}),
            record_classes=frozenset({"case.disciplinary"}),
            case_ids=frozenset(),
        ),
        issued_at=_OCCURRED_AT,
        issued_by_authority_reference=uuid4(),
    ).with_issue_entry(reason_code=_REASON)


def test_legal_hold_instance_validates_issued_and_released() -> None:
    issued = _hold()
    released = issued.release(
        _OCCURRED_AT + timedelta(days=1),
        released_by_authority_reference=uuid4(),
        reason_code=_REASON,
    )
    schema = load_schema("legal-hold.schema.json")
    for hold in (issued, released):
        validate(
            _instance(
                hold,
                {
                    "hold_id": hold.hold_id,
                    "organization_id": hold.organization_id,
                    "matter_reference": hold.matter_reference,
                    "scope": {
                        "record_ids": sorted(str(value) for value in hold.scope.record_ids),
                        "record_classes": sorted(hold.scope.record_classes),
                        "case_ids": sorted(str(value) for value in hold.scope.case_ids),
                    },
                    "issued_at": hold.issued_at.isoformat(),
                    "issued_by_authority_reference": hold.issued_by_authority_reference,
                    "status": hold.status.value,
                    "released_at": hold.released_at.isoformat() if hold.released_at else None,
                    "released_by_authority_reference": hold.released_by_authority_reference,
                    "history": [
                        {
                            "sequence": entry.sequence,
                            "occurred_at": entry.occurred_at.isoformat(),
                            "action": entry.action,
                            "reason_code": entry.reason_code,
                            "actor_authority_reference": entry.actor_authority_reference,
                            "status_after": entry.status_after.value,
                        }
                        for entry in hold.history
                    ],
                },
            ),
            schema,
        )


def test_destruction_authorization_instance_validates() -> None:
    authorization = DestructionAuthorization(
        authorization_id=uuid4(),
        record_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        disposition_action=DispositionAction.DELETE,
        retention_policy_id=uuid4(),
        retention_policy_version=1,
        authorized_record_version=2,
        authorized_at=_OCCURRED_AT,
        authorized_by_authority_reference=uuid4(),
        eligibility_evaluated_at=_OCCURRED_AT,
    )
    validate(
        _instance(
            authorization,
            {
                "authorization_id": authorization.authorization_id,
                "record_id": authorization.record_id,
                "organization_id": authorization.organization_id,
                "disposition_action": authorization.disposition_action.value,
                "retention_policy_id": authorization.retention_policy_id,
                "retention_policy_version": authorization.retention_policy_version,
                "authorized_record_version": authorization.authorized_record_version,
                "authorized_at": authorization.authorized_at.isoformat(),
                "authorized_by_authority_reference": (
                    authorization.authorized_by_authority_reference
                ),
                "eligibility_evaluated_at": authorization.eligibility_evaluated_at.isoformat(),
            },
        ),
        load_schema("destruction-authorization.schema.json"),
    )


def _evidence() -> DestructionEvidence:
    return DestructionEvidence(
        evidence_id=uuid4(),
        record_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        authorization_id=uuid4(),
        disposition_action=DispositionAction.DELETE,
        executed_at=_OCCURRED_AT,
        executed_by_authority_reference=uuid4(),
        evidence_digest="sha256:deadbeef",
        retention_policy_id=uuid4(),
        retention_policy_version=1,
    )


def test_destruction_evidence_instance_validates() -> None:
    evidence = _evidence()
    validate(
        _instance(
            evidence,
            {
                "evidence_id": evidence.evidence_id,
                "record_id": evidence.record_id,
                "organization_id": evidence.organization_id,
                "authorization_id": evidence.authorization_id,
                "disposition_action": evidence.disposition_action.value,
                "executed_at": evidence.executed_at.isoformat(),
                "executed_by_authority_reference": evidence.executed_by_authority_reference,
                "evidence_digest": evidence.evidence_digest,
                "retention_policy_id": evidence.retention_policy_id,
                "retention_policy_version": evidence.retention_policy_version,
            },
        ),
        load_schema("destruction-evidence.schema.json"),
    )


def test_data_asset_instance_validates() -> None:
    asset = DataAsset(
        asset_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        name="Mitgliederdatenbank",
        asset_class="database",
        system_reference="membership-service",
        record_class="membership.record",
        retention_policy_reference=uuid4(),
        status=RegistryEntryStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        owner_authority_reference=uuid4(),
    )
    validate(
        _instance(
            asset,
            {
                "asset_id": asset.asset_id,
                "organization_id": asset.organization_id,
                "name": asset.name,
                "asset_class": asset.asset_class,
                "system_reference": asset.system_reference,
                "record_class": asset.record_class,
                "retention_policy_reference": asset.retention_policy_reference,
                "status": asset.status.value,
                "valid_from": asset.valid_from.isoformat(),
                "owner_authority_reference": asset.owner_authority_reference,
                "asset_version": asset.asset_version,
            },
        ),
        load_schema("data-asset.schema.json"),
    )


def _activity() -> ProcessingActivity:
    return ProcessingActivity(
        activity_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        name="Mitgliederverwaltung",
        purpose="membership administration",
        legal_basis=LegalBasis.PARTY_STATUTE,
        data_subject_categories=("members",),
        personal_data_categories=("contact_data",),
        recipient_categories=("internal_administration",),
        retention_policy_reference=uuid4(),
        technical_organizational_measures=("rbac",),
        controller_reference=uuid4(),
        process_owner_authority_reference=uuid4(),
        system_references=("membership-service",),
        data_asset_references=(uuid4(),),
        status=RegistryEntryStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        dpo_review_reference=uuid4(),
    )


def test_processing_activity_instance_validates() -> None:
    activity = _activity()
    validate(
        _instance(
            activity,
            {
                "activity_id": activity.activity_id,
                "organization_id": activity.organization_id,
                "name": activity.name,
                "purpose": activity.purpose,
                "legal_basis": activity.legal_basis.value,
                "data_subject_categories": list(activity.data_subject_categories),
                "personal_data_categories": list(activity.personal_data_categories),
                "recipient_categories": list(activity.recipient_categories),
                "retention_policy_reference": activity.retention_policy_reference,
                "technical_organizational_measures": list(
                    activity.technical_organizational_measures
                ),
                "controller_reference": activity.controller_reference,
                "process_owner_authority_reference": activity.process_owner_authority_reference,
                "system_references": list(activity.system_references),
                "data_asset_references": [str(v) for v in activity.data_asset_references],
                "status": activity.status.value,
                "valid_from": activity.valid_from.isoformat(),
                "activity_version": activity.activity_version,
                "supersedes_activity_version": None,
                "dpo_review_reference": activity.dpo_review_reference,
            },
        ),
        load_schema("processing-activity.schema.json"),
    )


def _case() -> ProceduralCase:
    return ProceduralCase(
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        case_type=CaseType.PARTY_ARBITRATION,
        status=CaseStatus.OPEN,
        opened_at=_OCCURRED_AT,
        subject_reference="dispute:2026-1",
        procedural_authority_reference=mint_case_party_reference(),
        workflow_type="party_arbitration_standard",
        required_steps=(ProceduralStep(step_code="hearing", required=True),),
        evidence_references=("pack-11:document:1",),
        case_handler_reference=mint_case_party_reference(),
        assigned_decision_maker_reference=mint_case_party_reference(),
    )


def test_procedural_case_instance_validates() -> None:
    case = _case()
    validate(
        _instance(
            case,
            {
                "case_id": case.case_id,
                "organization_id": case.organization_id,
                "case_type": case.case_type.value,
                "status": case.status.value,
                "opened_at": case.opened_at.isoformat(),
                "subject_reference": case.subject_reference,
                "procedural_authority_reference": case.procedural_authority_reference,
                "workflow_type": case.workflow_type,
                "required_steps": [
                    {
                        "step_code": step.step_code,
                        "required": step.required,
                        "completed_at": None,
                    }
                    for step in case.required_steps
                ],
                "evidence_references": list(case.evidence_references),
                "case_handler_reference": case.case_handler_reference,
                "assigned_decision_maker_reference": case.assigned_decision_maker_reference,
                "decision_id": None,
                "closure_reason_code": None,
                "closed_at": None,
                "case_version": case.case_version,
            },
        ),
        load_schema("procedural-case.schema.json"),
    )


def test_case_decision_instance_validates() -> None:
    decision = CaseDecision(
        decision_id=uuid4(),
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        outcome=DecisionOutcome.PARTIALLY_UPHELD,
        reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_at=_OCCURRED_AT,
        decided_by_party_reference=mint_case_party_reference(),
        decided_by_role=ProceduralRole.INDEPENDENT_DECISION_MAKER,
        evidence_references=("pack-11:document:7",),
    )
    validate(
        _instance(
            decision,
            {
                "decision_id": decision.decision_id,
                "case_id": decision.case_id,
                "organization_id": decision.organization_id,
                "outcome": decision.outcome.value,
                "reason_code": decision.reason_code,
                "decided_at": decision.decided_at.isoformat(),
                "decided_by_party_reference": decision.decided_by_party_reference,
                "decided_by_role": decision.decided_by_role.value,
                "evidence_references": list(decision.evidence_references),
            },
        ),
        load_schema("case-decision.schema.json"),
    )


def test_conflict_of_interest_declaration_instance_validates() -> None:
    declaration = ConflictOfInterestDeclaration(
        declaration_id=uuid4(),
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        party_reference=mint_case_party_reference(),
        state=ConflictState.CONFIRMED,
        basis_code="same_local_branch",
        declared_at=_OCCURRED_AT,
        decided_by_party_reference=mint_case_party_reference(),
        decided_at=_OCCURRED_AT,
    )
    validate(
        _instance(
            declaration,
            {
                "declaration_id": declaration.declaration_id,
                "case_id": declaration.case_id,
                "organization_id": declaration.organization_id,
                "party_reference": declaration.party_reference,
                "state": declaration.state.value,
                "basis_code": declaration.basis_code,
                "declared_at": declaration.declared_at.isoformat(),
                "decided_by_party_reference": declaration.decided_by_party_reference,
                "decided_at": declaration.decided_at.isoformat()
                if declaration.decided_at
                else None,
            },
        ),
        load_schema("conflict-of-interest-declaration.schema.json"),
    )


def _definition() -> DeadlineDefinition:
    return DeadlineDefinition(
        definition_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        deadline_code="RESPONSE_DUE",
        duration_days=10,
        timezone=_BERLIN,
        escalation_after_days=7,
        description="Standard response window",
    )


def test_deadline_definition_instance_validates() -> None:
    definition = _definition()
    validate(
        _instance(
            definition,
            {
                "definition_id": definition.definition_id,
                "organization_id": definition.organization_id,
                "deadline_code": definition.deadline_code,
                "duration_days": definition.duration_days,
                "timezone": definition.timezone,
                "escalation_after_days": definition.escalation_after_days,
                "description": definition.description,
            },
        ),
        load_schema("deadline-definition.schema.json"),
    )


def _deadline() -> ProceduralDeadline:
    started = build_started_deadline(
        deadline_id=uuid4(),
        definition=_definition(),
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        started_at=_OCCURRED_AT,
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    suspended = started.suspend(
        _OCCURRED_AT + timedelta(days=1),
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    return suspended.resume(
        _OCCURRED_AT + timedelta(days=2),
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )


def _deadline_instance(deadline: ProceduralDeadline) -> dict[str, Any]:
    return to_jsonable(
        {
            "deadline_id": deadline.deadline_id,
            "definition_id": deadline.definition_id,
            "case_id": deadline.case_id,
            "organization_id": deadline.organization_id,
            "deadline_code": deadline.deadline_code,
            "timezone": deadline.timezone,
            "started_at": deadline.started_at.isoformat(),
            "status": deadline.status.value,
            "due_at": deadline.due_at.isoformat() if deadline.due_at else None,
            "history": [
                {
                    "sequence": entry.sequence,
                    "event_type": entry.event_type.value,
                    "occurred_at": entry.occurred_at.isoformat(),
                    "due_at_before": entry.due_at_before.isoformat()
                    if entry.due_at_before
                    else None,
                    "due_at_after": entry.due_at_after.isoformat() if entry.due_at_after else None,
                    "remaining_seconds": entry.remaining_seconds,
                    "reason_code": entry.reason_code,
                    "actor_party_reference": entry.actor_party_reference,
                }
                for entry in deadline.history
            ],
            "supersedes_deadline_id": None,
            "superseded_by_deadline_id": None,
        }
    )


def test_procedural_deadline_instance_validates_with_its_full_history() -> None:
    deadline = _deadline()
    assert len(deadline.history) == 3
    validate(_deadline_instance(deadline), load_schema("procedural-deadline.schema.json"))


def _request() -> DataSubjectRequest:
    return DataSubjectRequest(
        request_id=uuid4(),
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        request_type=DataSubjectRequestType.ACCESS,
        status=DataSubjectRequestStatus.IN_PROGRESS,
        requester_party_reference=mint_case_party_reference(),
        received_at=_OCCURRED_AT,
        scope_description_code="all_membership_data",
        identity_verification_status=IdentityVerificationStatus.VERIFIED,
        identity_verification_reference=uuid4(),
        search_result_references=("search:2026-1",),
    )


def test_data_subject_request_instance_validates() -> None:
    request = _request()
    validate(
        _instance(
            request,
            {
                "request_id": request.request_id,
                "case_id": request.case_id,
                "organization_id": request.organization_id,
                "request_type": request.request_type.value,
                "status": request.status.value,
                "requester_party_reference": request.requester_party_reference,
                "received_at": request.received_at.isoformat(),
                "scope_description_code": request.scope_description_code,
                "identity_verification_status": request.identity_verification_status.value,
                "identity_verification_reference": request.identity_verification_reference,
                "assigned_handler_reference": None,
                "search_result_references": list(request.search_result_references),
                "response_decision": None,
                "limitation_reason_code": None,
                "completion_evidence_reference": None,
                "request_version": request.request_version,
            },
        ),
        load_schema("data-subject-request.schema.json"),
    )


def test_cross_scope_authority_grant_instance_validates() -> None:
    grant = CrossScopeAuthorityGrant(
        grant_id=uuid4(),
        granting_organization_id=uuid4(),
        grantee_organization_id=uuid4(),
        capabilities=frozenset({ScopeCapability.READ_CASE, ScopeCapability.MANAGE_DEADLINE}),
        valid_from=_OCCURRED_AT,
        valid_until=_OCCURRED_AT + timedelta(days=30),
        authorizing_decision_reference=uuid4(),
        revoked_at=None,
    )
    validate(
        _instance(
            grant,
            {
                "grant_id": grant.grant_id,
                "granting_organization_id": grant.granting_organization_id,
                "grantee_organization_id": grant.grantee_organization_id,
                "capabilities": sorted(value.value for value in grant.capabilities),
                "valid_from": grant.valid_from.isoformat(),
                "valid_until": grant.valid_until.isoformat() if grant.valid_until else None,
                "authorizing_decision_reference": grant.authorizing_decision_reference,
                "revoked_at": None,
            },
        ),
        load_schema("cross-scope-authority-grant.schema.json"),
    )


# ---------------------------------------------------------------------------
# Event payload schemas (contracts/events/)
# ---------------------------------------------------------------------------


def test_retention_started_event_payload_validates() -> None:
    policy = _policy()
    record = _record(policy)
    start_event = RetentionStartEvent(
        retention_start_event_id=uuid4(),
        record_id=record.record_id,
        organization_id=record.organization_id,
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        occurred_at=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
        source_reference="case:1",
    )
    envelope = build_retention_started_event(
        event_id=uuid4(),
        record=record,
        start_event=start_event,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("governed-record-retention-started-payload.v1.schema.json"),
    )


def test_disposal_authorized_event_payload_validates() -> None:
    policy = _policy()
    record = _record(policy, state=GovernedRecordState.DISPOSAL_AUTHORIZED, record_version=2)
    envelope = build_disposal_authorized_event(
        event_id=uuid4(),
        record=record,
        authorization_id=uuid4(),
        disposition_action=DispositionAction.DELETE.value,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("governed-record-disposal-authorized-payload.v1.schema.json"),
    )


def test_record_destroyed_event_payload_validates() -> None:
    policy = _policy()
    evidence = _evidence()
    record = _record(
        policy,
        record_id=evidence.record_id,
        state=GovernedRecordState.DESTROYED,
        record_version=3,
        destruction_evidence_id=evidence.evidence_id,
    )
    envelope = build_record_destroyed_event(
        event_id=uuid4(),
        record=record,
        evidence=evidence,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("governed-record-destroyed-payload.v1.schema.json"),
    )


def test_legal_hold_status_changed_event_payload_validates_for_every_action() -> None:
    schema = load_event_schema("legal-hold-status-changed-payload.v1.schema.json")
    issued = _hold()
    released = issued.release(
        _OCCURRED_AT + timedelta(days=1),
        released_by_authority_reference=uuid4(),
        reason_code=_REASON,
    )
    indeterminate = _hold().mark_indeterminate(
        _OCCURRED_AT + timedelta(days=1),
        actor_authority_reference=uuid4(),
        reason_code="LEGAL_HOLD_STATE_UNKNOWN",
    )
    for hold, action in (
        (issued, "issued"),
        (released, "released"),
        (indeterminate, "marked_indeterminate"),
    ):
        envelope = build_legal_hold_status_changed_event(
            event_id=uuid4(),
            hold=hold,
            action=action,
            reason_code="COMPLIANCE_LEGAL_HOLD_STATUS_CHANGED",
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        )
        validate(to_jsonable(envelope.payload), schema)


def test_processing_activity_status_changed_event_payload_validates() -> None:
    envelope = build_processing_activity_status_changed_event(
        event_id=uuid4(),
        activity=_activity(),
        reason_code="COMPLIANCE_PROCESSING_REGISTRY_STATUS_CHANGED",
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("processing-activity-status-changed-payload.v1.schema.json"),
    )


def test_case_status_changed_event_payload_validates() -> None:
    envelope = build_case_status_changed_event(
        event_id=uuid4(),
        case=_case(),
        reason_code="COMPLIANCE_PROCEDURAL_CASE_STATUS_CHANGED",
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("procedural-case-status-changed-payload.v1.schema.json"),
    )


def test_deadline_state_changed_event_payload_validates_for_each_transition() -> None:
    schema = load_event_schema("procedural-deadline-state-changed-payload.v1.schema.json")
    started = build_started_deadline(
        deadline_id=uuid4(),
        definition=_definition(),
        case_id=uuid4(),
        organization_id=_ORGANIZATION_ID,
        started_at=_OCCURRED_AT,
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    suspended = started.suspend(
        _OCCURRED_AT + timedelta(days=1),
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    resumed = suspended.resume(
        _OCCURRED_AT + timedelta(days=2),
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    extended = resumed.extend(
        _OCCURRED_AT + timedelta(days=3),
        additional_days=2,
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    satisfied = extended.satisfy(
        _OCCURRED_AT + timedelta(days=4),
        reason_code=_REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    for deadline in (started, suspended, resumed, extended, satisfied):
        envelope = build_deadline_state_changed_event(
            event_id=uuid4(),
            deadline=deadline,
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        )
        validate(to_jsonable(envelope.payload), schema)


def test_data_subject_request_status_changed_event_payload_validates() -> None:
    envelope = build_request_status_changed_event(
        event_id=uuid4(),
        request=_request(),
        reason_code="COMPLIANCE_DATA_SUBJECT_REQUEST_STATUS_CHANGED",
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(envelope.payload),
        load_event_schema("data-subject-request-status-changed-payload.v1.schema.json"),
    )


# ---------------------------------------------------------------------------
# Envelope conformance
# ---------------------------------------------------------------------------


def test_every_pack09_event_envelope_validates_against_the_shared_schema() -> None:
    """Each PACK-09 event is a canonical envelope (canon section 21), not
    a bespoke message shape - the same check every earlier pack applies to
    its own events."""
    from _schema_helpers import envelope_to_jsonable

    schema = load_schema("event-envelope.schema.json")
    envelopes = [
        build_case_status_changed_event(
            event_id=uuid4(),
            case=_case(),
            reason_code="COMPLIANCE_PROCEDURAL_CASE_STATUS_CHANGED",
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        ),
        build_deadline_state_changed_event(
            event_id=uuid4(),
            deadline=_deadline(),
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        ),
        build_request_status_changed_event(
            event_id=uuid4(),
            request=_request(),
            reason_code="COMPLIANCE_DATA_SUBJECT_REQUEST_STATUS_CHANGED",
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        ),
    ]
    for envelope in envelopes:
        validate(envelope_to_jsonable(envelope), schema)
        assert envelope.producer == "compliance-service"
        assert envelope.event_version == "1.0"
        assert envelope.integrity.payload_hash
