"""Compliance Service application layer (PACK-09, ADR-038 through
ADR-042).

Every state-changing command here follows the four conventions PACK-02
through PACK-08 already establish across this repository, so PACK-09 is a
continuation of the existing architecture rather than a parallel one:

1. **Dependency-injected `Clock`** - no command reads system time.
2. **Caller-supplied `event_id` idempotency (CT-00-04)** - a retried
   command with the same `event_id` returns the already-recorded result
   instead of re-attempting a transition that would fail the second time
   round. Replay detection goes through Audit Core's own
   `get_by_event_id`, exactly as `governance-service` and
   `organization-service` do.
3. **Audit Core append on every critical action (CT-00-07/INV-04)** -
   with `before_hash`/`after_hash` computed from this service's own
   canonical state snapshots (`events.*_full_state_payload`).
4. **Reason-coded refusal (canon section 24)** - every denial raises one
   of `exceptions`' classes, each mapped to a code registered in
   `contracts/reason-codes/pack-09.yml`.

## Organizational scope isolation (invariant 2)

`RequestContext` carries the caller's own `organization_id` and the
cross-scope authority grants it explicitly presents. Two guard patterns
do all boundary work:

- `_raise_not_found` - used for reads, and for writes where the caller
  presented no authority at all. A record in a *different* organization
  is reported with the same `ComplianceRecordNotFoundError` as a record
  that does not exist, so a foreign resource id discloses nothing (the
  "resource ID from another organization must not reveal existence
  beyond a safe error" requirement).
- `_require_cross_scope_authority` - used when the caller *does* present
  authority references. Only then does the caller learn a specific
  `CROSS_ORGANIZATION_CASE_ACCESS_DENIED` /
  `CROSS_SCOPE_AUTHORITY_INVALID` refusal, because it has already
  asserted it believes it holds authority there.

There is deliberately **no hierarchical inheritance**: a Bund-level
organization gets nothing automatically over a Landesverband's or
Kreisverband's records, and a Kreisverband gets nothing over its parent
Land's. Crossing a boundary always needs a `CrossScopeAuthorityGrant`
issued *by the organization being reached into* and presented by the
caller.

A context whose `organization_id` is `None`, or an entity submitted
without an `organization_id`, is refused with
`OrganizationScopeUndeterminedError` - never defaulted (invariant 15).

## What this module deliberately does not do

No production persistence, no HTTP server, no event-bus publication, no
document storage, no finance ledger, no privileged/break-glass
administration, no identity acquisition, and no voting linkage. Those
belong to PACK-10 through PACK-18 (ADR-038 Consequences). This module
imports nothing from `epd2_voting_service`, `epd2_tally_service`,
`epd2_delegation_service`, `epd2_identity_service`,
`epd2_account_service` or `epd2_credential_service` - enforced by
`tests/repository/test_service_boundaries.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import NoReturn
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_compliance_service.casework import (
    SUBSTANTIVE_CASE_STATUSES,
    ActorClass,
    CaseParty,
    Filing,
    Hearing,
    InterimMeasure,
    JurisdictionDetermination,
    LegalCase,
    LegalCaseStatus,
    ProceduralDecision,
    RecusalRecord,
    Remedy,
    ReplacementAssignment,
    RepresentationAuthority,
    RepresentationMandate,
    assert_actor_not_recused,
    assert_due_process_complete,
    assert_may_decide_substantively,
)
from epd2_compliance_service.dataprotection import (
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    DPIAStatus,
    ProcessingActivationDecision,
    ProcessingActivationState,
    ProcessingRiskClass,
    assert_activation_permitted,
    assert_dpo_independence,
)
from epd2_compliance_service.domain import (
    DESTRUCTIVE_DISPOSITION_ACTIONS,
    AppealReference,
    CaseDecision,
    CaseRoleAssignment,
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
    DeadlineStatus,
    DecisionOutcome,
    DestructionAuthorization,
    DestructionEvidence,
    DisposalEligibility,
    DisputeParties,
    GovernedRecord,
    GovernedRecordState,
    HoldPropagationRecord,
    IdentityVerificationStatus,
    LegalHold,
    LegalHoldScope,
    ProceduralCase,
    ProceduralDeadline,
    ProceduralRole,
    ProcessingActivity,
    RecordClass,
    RegistryEntryStatus,
    ResponseDecision,
    RetentionPolicy,
    RetentionStartEvent,
    RetentionTrigger,
    ScopeCapability,
    assert_decision_maker_eligible,
    assert_hold_propagation_resolved,
    build_started_deadline,
    evaluate_hold_applicability,
)
from epd2_compliance_service.events import (
    build_case_party_registered_event,
    build_case_status_changed_event,
    build_deadline_state_changed_event,
    build_deadline_triggered_event,
    build_decision_effect_changed_event,
    build_decision_enforceability_changed_event,
    build_decision_finality_changed_event,
    build_disposal_authorized_event,
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
    build_legal_hold_status_changed_event,
    build_notice_effect_determined_event,
    build_notice_issued_event,
    build_procedural_decision_issued_event,
    build_processing_activation_decided_event,
    build_processing_activity_status_changed_event,
    build_record_class_registered_event,
    build_record_destroyed_event,
    build_recusal_recorded_event,
    build_remedy_registered_event,
    build_replacement_assigned_event,
    build_representation_registered_event,
    build_representation_revoked_event,
    build_request_status_changed_event,
    build_retention_started_event,
    build_service_attempt_recorded_event,
    data_subject_request_full_state_payload,
    deadline_trigger_full_state_payload,
    dpia_full_state_payload,
    filing_full_state_payload,
    governed_record_full_state_payload,
    hearing_full_state_payload,
    hold_propagation_full_state_payload,
    interim_measure_full_state_payload,
    jurisdiction_full_state_payload,
    legal_case_full_state_payload,
    legal_hold_full_state_payload,
    notice_effect_full_state_payload,
    official_notice_full_state_payload,
    procedural_case_full_state_payload,
    procedural_deadline_full_state_payload,
    procedural_decision_full_state_payload,
    processing_activation_full_state_payload,
    processing_activity_full_state_payload,
    record_class_full_state_payload,
    recusal_full_state_payload,
    remedy_full_state_payload,
    service_attempt_full_state_payload,
)
from epd2_compliance_service.exceptions import (
    ComplianceCommandConflictError,
    ComplianceRecordNotFoundError,
    ConflictOfInterestBlockingError,
    CrossOrganizationCaseAccessDeniedError,
    CrossScopeAccessDeniedError,
    CrossScopeAuthorityInvalidError,
    DeadlineSilentReplacementRejectedError,
    DecisionAuthorityMissingError,
    DestructionAuthorizationRequiredError,
    DestructionAuthorizationStaleError,
    FilingSequenceConflictError,
    IdentityVerificationInsufficientError,
    JurisdictionScopeMismatchError,
    JurisdictionTransferRequiredError,
    LegalHoldStateUnknownError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeUndeterminedError,
    ProceduralCaseClosedError,
    ProceduralCaseTransitionInvalidError,
    ProceduralIndependenceViolationError,
    RecordUnderLegalHoldError,
    RepresentationInvalidError,
    RetentionDispositionNotDueError,
    RetentionPolicyRebindRequiresReevaluationError,
    RetentionStartUndeterminedError,
)
from epd2_compliance_service.notices import (
    DeadlineTrigger,
    DeemedServiceRule,
    NoticeEffectDecision,
    NoticeProofPackageRef,
    OfficialNotice,
    ServiceAttempt,
    TriggerSource,
    assert_no_duplicate_legal_effect,
    assert_trigger_is_governed,
    determine_notice_effect,
)
from epd2_compliance_service.references import MinutesRef
from epd2_compliance_service.storage import (
    AppealReferenceStore,
    CaseDecisionStore,
    CasePartyStore,
    CaseRoleAssignmentStore,
    ConflictDeclarationStore,
    CrossScopeAuthorityGrantStore,
    DataAssetStore,
    DataSubjectRequestStore,
    DeadlineDefinitionStore,
    DeadlineTriggerStore,
    DestructionAuthorizationStore,
    DestructionEvidenceStore,
    DisputePartiesStore,
    DPIAStore,
    FilingStore,
    GovernedRecordStore,
    HearingStore,
    HoldPropagationStore,
    InterimMeasureStore,
    JurisdictionStore,
    LegalCaseStore,
    LegalHoldStore,
    NoticeEffectStore,
    OfficialNoticeStore,
    ProceduralCaseStore,
    ProceduralDeadlineStore,
    ProceduralDecisionStore,
    ProcessingActivationStore,
    ProcessingActivityStore,
    RecordClassStore,
    RecusalStore,
    RemedyStore,
    RepresentationStore,
    RetentionPolicyStore,
    RetentionStartEventStore,
    ServiceAttemptStore,
)
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope
from epd2_core.identifiers import generate_uuid

#: Audit Core policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "compliance-service"

#: Callable shape of a deadline transition applied by
#: `_apply_deadline_transition` - takes the loaded deadline and the
#: command's own `now`, returns the deadline with exactly one new history
#: entry appended.
DeadlineTransitionFn = Callable[[ProceduralDeadline, datetime], ProceduralDeadline]

# Audit `reason_code` classifications - one generic classification per
# logical action type, following the ADR-006/ADR-014/ADR-019/ADR-029
# pattern (canon section 24's own list is refusal-only and has no code
# meaning "this succeeded").
_RECORD_AUDIT = "COMPLIANCE_GOVERNED_RECORD_STATUS_CHANGED"
_HOLD_AUDIT = "COMPLIANCE_LEGAL_HOLD_STATUS_CHANGED"
_REGISTRY_AUDIT = "COMPLIANCE_PROCESSING_REGISTRY_STATUS_CHANGED"
_CASE_AUDIT = "COMPLIANCE_PROCEDURAL_CASE_STATUS_CHANGED"
_DEADLINE_AUDIT = "COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED"
_REQUEST_AUDIT = "COMPLIANCE_DATA_SUBJECT_REQUEST_STATUS_CHANGED"

#: Maps a governed record's `record_class` prefix onto the retention
#: trigger its start event records. An explicit closed table rather than
#: a free-text field, so the trigger a retention period ran from is
#: always one of `RetentionTrigger`'s own values.
_RECORD_CLASS_PREFIX_TRIGGERS: dict[str, RetentionTrigger] = {
    "case": RetentionTrigger.CASE_CLOSED_AT,
    "membership": RetentionTrigger.MEMBERSHIP_ENDED_AT,
    "contract": RetentionTrigger.CONTRACT_ENDED_AT,
    "processing": RetentionTrigger.PROCESSING_ENDED_AT,
}

#: Case types whose decision may only ever be recorded by the assigned
#: independent decision-maker (ADR-042).
_DISPUTE_CASE_TYPES: frozenset[CaseType] = frozenset(
    {CaseType.PARTY_ARBITRATION, CaseType.INTERNAL_DISPUTE}
)

#: Deadline states that still count as "live" for the no-silent-
#: replacement check in `start_deadline` (invariant 7).
_LIVE_DEADLINE_STATES: frozenset[DeadlineStatus] = frozenset(
    {DeadlineStatus.RUNNING, DeadlineStatus.SUSPENDED, DeadlineStatus.ESCALATED}
)


# ---------------------------------------------------------------------------
# Request context and scope guards
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Everything a command needs to know about who is asking.

    `organization_id` is `None` when the caller's scope could not be
    resolved - every command then fails closed rather than defaulting to
    any organization (invariant 15).

    `authority_reference_ids` are cross-scope grants the caller is
    *explicitly presenting* for this operation. An unpresented grant is
    never used, so a standing broad grant cannot be exercised by
    accident."""

    actor: ActorRef
    organization_id: UUID | None
    correlation_id: UUID
    authority_reference_ids: frozenset[UUID] = frozenset()


def _raise_not_found(what: str, identifier: UUID) -> NoReturn:
    """Raise the single, non-disclosing "not found for this caller" error.

    Deliberately identical whether the object does not exist at all or
    exists in another organization, so a foreign resource id reveals
    nothing. Typed `NoReturn` so every call site's `is None` check
    narrows the value afterwards without a cast."""
    raise ComplianceRecordNotFoundError(f"{what} {identifier} was not found")


def _require_scope(context: RequestContext) -> UUID:
    if context.organization_id is None:
        raise OrganizationScopeUndeterminedError(
            "the request context carries no resolvable organizational scope"
        )
    return context.organization_id


def _require_entity_scope(organization_id: UUID | None, *, what: str) -> UUID:
    if organization_id is None:
        raise OrganizationScopeUndeterminedError(f"{what} was submitted without an organization")
    return organization_id


def _require_cross_scope_authority(
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    target_organization_id: UUID,
    capability: ScopeCapability,
    now: datetime,
) -> CrossScopeAuthorityGrant:
    """Resolve one presented grant that actually permits `capability`
    inside `target_organization_id`, or refuse with a specific code.

    Only reachable when the caller presented at least one authority
    reference - see this module's docstring on why the "blind" path
    deliberately reports not-found instead."""
    caller_organization_id = _require_scope(context)
    if not context.authority_reference_ids:
        raise CrossOrganizationCaseAccessDeniedError(
            "no cross-scope authority was presented for this organization"
        )
    for grant_id in sorted(context.authority_reference_ids):
        grant = grant_store.get(grant_id)
        if grant is None:
            continue
        if grant.permits(
            granting_organization_id=target_organization_id,
            grantee_organization_id=caller_organization_id,
            capability=capability,
            at=now,
        ):
            return grant
    raise CrossScopeAuthorityInvalidError(
        f"no presented cross-scope grant permits {capability.value} in organization "
        f"{target_organization_id}"
    )


def _check_expected_version(actual: int, expected: int | None, *, what: str) -> None:
    if expected is not None and expected != actual:
        raise OptimisticConcurrencyConflictError(
            f"{what} is at version {actual}, caller expected {expected}"
        )


def _state_hash(payload: dict[str, object]) -> str:
    """Canonical, deterministic hash input for Audit Core's
    `before_hash`/`after_hash`. Uses the repository's own canonical JSON
    so two structurally-identical snapshots always hash identically."""
    return canonical_dumps(payload)


def _resolved_event_id(event_id: UUID | None) -> UUID:
    return event_id if event_id is not None else generate_uuid()


def _trigger_for(record: GovernedRecord) -> RetentionTrigger:
    prefix = record.record_class.split(".", 1)[0]
    return _RECORD_CLASS_PREFIX_TRIGGERS.get(prefix, RetentionTrigger.CREATED_AT)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GovernedRecordResult:
    record: GovernedRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DestructionResult:
    record: GovernedRecord
    evidence: DestructionEvidence
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class LegalHoldResult:
    hold: LegalHold
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProcessingActivityResult:
    activity: ProcessingActivity
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProceduralCaseResult:
    case: ProceduralCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProceduralDeadlineResult:
    deadline: ProceduralDeadline
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DataSubjectRequestResult:
    request: DataSubjectRequest
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------


def _append_audit(
    audit_store: AuditEventStore,
    *,
    audit_event_id: UUID,
    event_type: str,
    occurred_at: datetime,
    context: RequestContext,
    target_type: str,
    target_id: UUID,
    action: str,
    reason_code: str,
    before_hash: str,
    after_hash: str,
    clock: Clock,
) -> AuditEvent:
    return append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=audit_event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            actor_id=context.actor.actor_id,
            actor_type=context.actor.actor_type,
            target_type=target_type,
            target_id=target_id,
            action=action,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=context.correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=after_hash,
        ),
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Retention policies (ADR-039)
# ---------------------------------------------------------------------------


def register_retention_policy(
    policy_store: RetentionPolicyStore,
    context: RequestContext,
    policy: RetentionPolicy,
) -> RetentionPolicy:
    """Register a retention policy version, or replay an identical
    registration. Superseding an existing policy goes through
    `supersede_retention_policy` instead."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(policy.organization_id, what="retention policy")
    if policy.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a retention policy may only be registered inside the caller's own organization"
        )
    return policy_store.create_version(policy)


def supersede_retention_policy(
    policy_store: RetentionPolicyStore,
    record_store: GovernedRecordStore,
    context: RequestContext,
    *,
    superseding_policy: RetentionPolicy,
) -> tuple[RetentionPolicy, tuple[GovernedRecord, ...]]:
    """Register a newer version of an existing policy and *invalidate*
    every standing disposal authorization written under the old one.

    This is the executable half of invariant 5. Rewriting a retention
    schedule can never, by itself, make an already-governed record
    destroyable: each affected record is rebound to the new version, has
    its state reset to `active` and its `destruction_authorization_id`
    dropped, so a fresh eligibility evaluation and a fresh authorization
    are required before anything can be destroyed. Any active Legal Hold
    is untouched by this and keeps blocking (see
    `evaluate_disposal_eligibility`).

    Returns the stored new policy version plus every record rebound."""
    caller_organization_id = _require_scope(context)
    if superseding_policy.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a retention policy may only be superseded inside its own organization"
        )
    if superseding_policy.supersedes_policy_version is None:
        raise RetentionPolicyRebindRequiresReevaluationError(
            "a superseding policy version must name the version it supersedes"
        )
    previous = policy_store.get_version(
        superseding_policy.policy_id, superseding_policy.supersedes_policy_version
    )
    if previous is None:
        _raise_not_found("retention policy version", superseding_policy.policy_id)
    stored = policy_store.create_version(superseding_policy)

    rebound: list[GovernedRecord] = []
    for record in record_store.list_for_organization(caller_organization_id):
        if record.retention_policy_id != stored.policy_id:
            continue
        if record.state is GovernedRecordState.DESTROYED:
            continue
        if record.retention_policy_version >= stored.policy_version:
            continue
        rebound.append(record_store.save(record.rebound_to_policy_version(stored.policy_version)))
    return stored, tuple(rebound)


# ---------------------------------------------------------------------------
# Governed records, retention start, eligibility (ADR-039)
# ---------------------------------------------------------------------------


def register_governed_record(
    record_store: GovernedRecordStore,
    policy_store: RetentionPolicyStore,
    context: RequestContext,
    record: GovernedRecord,
) -> GovernedRecord:
    caller_organization_id = _require_scope(context)
    _require_entity_scope(record.organization_id, what="governed record")
    if record.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a governed record may only be registered inside the caller's own organization"
        )
    policy = policy_store.get_version(record.retention_policy_id, record.retention_policy_version)
    if policy is None:
        _raise_not_found("retention policy version", record.retention_policy_id)
    if policy.organization_id != record.organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a governed record may not reference another organization's retention policy"
        )
    return record_store.save(record)


def record_retention_start(
    record_store: GovernedRecordStore,
    start_event_store: RetentionStartEventStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    record_id: UUID,
    trigger_occurred_at: datetime,
    source_reference: str,
    clock: Clock,
    event_id: UUID | None = None,
    retention_start_event_id: UUID | None = None,
) -> GovernedRecordResult:
    """Record the explicit fact that this record's retention period has
    started. Idempotent on `event_id`."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    record = record_store.get_in_scope(record_id, caller_organization_id)
    if record is None:
        _raise_not_found("governed record", record_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        starts = start_event_store.list_for_record(record_id)
        if not starts:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no retention start"
            )
        event = build_retention_started_event(
            event_id=resolved_event_id,
            record=record,
            start_event=starts[-1],
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return GovernedRecordResult(record=record, event=event, audit_event=existing_audit)

    now = clock.now()
    before = _state_hash(governed_record_full_state_payload(record))
    stored_start = start_event_store.append(
        RetentionStartEvent(
            retention_start_event_id=(
                retention_start_event_id
                if retention_start_event_id is not None
                else generate_uuid()
            ),
            record_id=record.record_id,
            organization_id=record.organization_id,
            trigger=_trigger_for(record),
            occurred_at=trigger_occurred_at,
            recorded_at=now,
            source_reference=source_reference,
        )
    )
    updated = record_store.save(record.with_retention_start(stored_start))
    after = _state_hash(governed_record_full_state_payload(updated))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="governed_record.retention_started",
        occurred_at=now,
        context=context,
        target_type="governed_record",
        target_id=record.record_id,
        action="record_retention_start",
        reason_code=_RECORD_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_retention_started_event(
        event_id=resolved_event_id,
        record=updated,
        start_event=stored_start,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return GovernedRecordResult(record=updated, event=event, audit_event=audit_event)


def evaluate_disposal_eligibility(
    record_store: GovernedRecordStore,
    policy_store: RetentionPolicyStore,
    hold_store: LegalHoldStore,
    context: RequestContext,
    *,
    record_id: UUID,
    clock: Clock,
) -> DisposalEligibility:
    """Deterministically decide whether `record_id` may be disposed of.

    Fail-closed order (invariant 15) - unresolved scope, then unknown
    record, then unknown policy version, then *indeterminate* hold state,
    then unknown retention start, then active hold, then the due-time
    check. Each refusal carries its own reason code, so a caller can
    always tell which condition stopped it.

    An indeterminate hold raises rather than returning an ineligible
    verdict: "we could not determine the hold state" is a different fact
    from "this record is not yet eligible", and collapsing the two would
    let an unknown state read as an ordinary not-due answer."""
    caller_organization_id = _require_scope(context)
    record = record_store.get_in_scope(record_id, caller_organization_id)
    if record is None:
        _raise_not_found("governed record", record_id)

    policy = policy_store.get_version(record.retention_policy_id, record.retention_policy_version)
    if policy is None:
        _raise_not_found("retention policy version", record.retention_policy_id)
    now = clock.now()

    holds = hold_store.list_for_organization(record.organization_id)
    applicability = evaluate_hold_applicability(record, holds)
    if applicability.is_undetermined:
        raise LegalHoldStateUnknownError(
            f"hold state for record {record_id} could not be established; refusing to assess "
            f"disposal eligibility (indeterminate holds: "
            f"{sorted(str(value) for value in applicability.indeterminate_hold_ids)})"
        )

    if record.retention_start_at is None:
        return DisposalEligibility(
            record_id=record.record_id,
            organization_id=record.organization_id,
            evaluated_at=now,
            retention_policy_id=policy.policy_id,
            retention_policy_version=policy.policy_version,
            due_at=None,
            eligible=False,
            reason_code=RetentionStartUndeterminedError.reason_code,
        )

    due_at = policy.due_at(record.retention_start_at)

    if applicability.is_blocked and policy.disposition_action in DESTRUCTIVE_DISPOSITION_ACTIONS:
        return DisposalEligibility(
            record_id=record.record_id,
            organization_id=record.organization_id,
            evaluated_at=now,
            retention_policy_id=policy.policy_id,
            retention_policy_version=policy.policy_version,
            due_at=due_at,
            eligible=False,
            reason_code=RecordUnderLegalHoldError.reason_code,
            blocking_hold_ids=applicability.blocking_hold_ids,
        )

    if now < due_at:
        return DisposalEligibility(
            record_id=record.record_id,
            organization_id=record.organization_id,
            evaluated_at=now,
            retention_policy_id=policy.policy_id,
            retention_policy_version=policy.policy_version,
            due_at=due_at,
            eligible=False,
            reason_code=RetentionDispositionNotDueError.reason_code,
        )

    return DisposalEligibility(
        record_id=record.record_id,
        organization_id=record.organization_id,
        evaluated_at=now,
        retention_policy_id=policy.policy_id,
        retention_policy_version=policy.policy_version,
        due_at=due_at,
        eligible=True,
        reason_code=None,
    )


def _with_authorization(record: GovernedRecord, authorization_id: UUID) -> GovernedRecord:
    authorized = record.with_state(GovernedRecordState.DISPOSAL_AUTHORIZED)
    return replace(authorized, destruction_authorization_id=authorization_id)


def authorize_destruction(
    record_store: GovernedRecordStore,
    policy_store: RetentionPolicyStore,
    hold_store: LegalHoldStore,
    authorization_store: DestructionAuthorizationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    record_id: UUID,
    authorized_by_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
    authorization_id: UUID | None = None,
    expected_record_version: int | None = None,
) -> GovernedRecordResult:
    """Issue the separate `DestructionAuthorization` that
    `execute_destruction` requires (invariant 4).

    Re-runs the full eligibility evaluation itself rather than trusting a
    caller-supplied verdict, so a hold placed between evaluation and
    authorization still blocks."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    record = record_store.get_in_scope(record_id, caller_organization_id)
    if record is None:
        _raise_not_found("governed record", record_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        if record.destruction_authorization_id is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no authorization"
            )
        replayed = authorization_store.get(record.destruction_authorization_id)
        if replayed is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found a dangling "
                "authorization reference"
            )
        event = build_disposal_authorized_event(
            event_id=resolved_event_id,
            record=record,
            authorization_id=replayed.authorization_id,
            disposition_action=replayed.disposition_action.value,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return GovernedRecordResult(record=record, event=event, audit_event=existing_audit)

    _check_expected_version(record.record_version, expected_record_version, what="governed record")

    eligibility = evaluate_disposal_eligibility(
        record_store, policy_store, hold_store, context, record_id=record_id, clock=clock
    )
    if not eligibility.eligible:
        if eligibility.reason_code == RecordUnderLegalHoldError.reason_code:
            raise RecordUnderLegalHoldError(
                f"record {record_id} is protected by active Legal Hold(s) "
                f"{sorted(str(value) for value in eligibility.blocking_hold_ids)}"
            )
        if eligibility.reason_code == RetentionStartUndeterminedError.reason_code:
            raise RetentionStartUndeterminedError(
                f"record {record_id} has no recorded retention start"
            )
        raise RetentionDispositionNotDueError(
            f"record {record_id} is not due for disposal until "
            f"{eligibility.due_at.isoformat() if eligibility.due_at else 'an unknown time'}"
        )

    policy = policy_store.get_version(record.retention_policy_id, record.retention_policy_version)
    if policy is None:  # pragma: no cover - eligibility already resolved it
        _raise_not_found("retention policy version", record.retention_policy_id)

    now = clock.now()
    before = _state_hash(governed_record_full_state_payload(record))
    resolved_authorization_id = (
        authorization_id if authorization_id is not None else generate_uuid()
    )
    # Move the record into `disposal_authorized` FIRST, then bind the
    # authorization to the version that transition produced. Binding it to
    # the pre-transition version would make every authorization instantly
    # stale, since `with_state` increments `record_version` by design.
    updated = record_store.save(_with_authorization(record, resolved_authorization_id))
    stored_authorization = authorization_store.save(
        DestructionAuthorization(
            authorization_id=resolved_authorization_id,
            record_id=updated.record_id,
            organization_id=updated.organization_id,
            disposition_action=policy.disposition_action,
            retention_policy_id=policy.policy_id,
            retention_policy_version=policy.policy_version,
            authorized_record_version=updated.record_version,
            authorized_at=now,
            authorized_by_authority_reference=authorized_by_authority_reference,
            eligibility_evaluated_at=eligibility.evaluated_at,
        )
    )
    after = _state_hash(governed_record_full_state_payload(updated))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="governed_record.disposal_authorized",
        occurred_at=now,
        context=context,
        target_type="governed_record",
        target_id=record.record_id,
        action="authorize_destruction",
        reason_code=_RECORD_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_disposal_authorized_event(
        event_id=resolved_event_id,
        record=updated,
        authorization_id=stored_authorization.authorization_id,
        disposition_action=stored_authorization.disposition_action.value,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return GovernedRecordResult(record=updated, event=event, audit_event=audit_event)


def execute_destruction(
    record_store: GovernedRecordStore,
    hold_store: LegalHoldStore,
    authorization_store: DestructionAuthorizationStore,
    evidence_store: DestructionEvidenceStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    record_id: UUID,
    executed_by_authority_reference: UUID,
    evidence_digest: str,
    clock: Clock,
    event_id: UUID | None = None,
    evidence_id: UUID | None = None,
) -> DestructionResult:
    """Execute an authorized destruction, producing evidence exactly once.

    Guard order matters and is deliberate:

    1. scope (fail closed on an unresolved scope);
    2. idempotent replay - a retried command with the same `event_id`
       returns the existing evidence untouched;
    3. a matching, non-stale `DestructionAuthorization` must exist
       (invariant 4 - there is no ordinary delete path at all, and the
       store exposes no delete method);
    4. Legal Hold is re-checked *here*, at execution time, not only at
       authorization time - a hold placed after authorization still
       blocks (invariant 3), and an indeterminate hold fails closed
       (invariant 15);
    5. the authorization must still match the record's current version
       and policy version - a retention-policy supersession in between
       makes it stale (invariant 5).

    The record's metadata row survives with `state=destroyed` and its
    evidence reference attached; nothing is ever removed from storage."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    record = record_store.get_in_scope(record_id, caller_organization_id)
    if record is None:
        _raise_not_found("governed record", record_id)

    existing_evidence = evidence_store.get_for_record(record_id)
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None and existing_evidence is not None:
        event = build_record_destroyed_event(
            event_id=resolved_event_id,
            record=record,
            evidence=existing_evidence,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DestructionResult(
            record=record, evidence=existing_evidence, event=event, audit_event=existing_audit
        )

    if record.destruction_authorization_id is None:
        raise DestructionAuthorizationRequiredError(
            f"record {record_id} has no destruction authorization; governed records are never "
            "removed by an ordinary delete"
        )
    authorization = authorization_store.get(record.destruction_authorization_id)
    if authorization is None:
        raise DestructionAuthorizationRequiredError(
            f"destruction authorization {record.destruction_authorization_id} was not found"
        )

    holds = hold_store.list_for_organization(record.organization_id)
    applicability = evaluate_hold_applicability(record, holds)
    if applicability.is_undetermined:
        raise LegalHoldStateUnknownError(
            f"hold state for record {record_id} could not be established; refusing destruction"
        )
    if (
        applicability.is_blocked
        and authorization.disposition_action in DESTRUCTIVE_DISPOSITION_ACTIONS
    ):
        raise RecordUnderLegalHoldError(
            f"record {record_id} is protected by active Legal Hold(s) "
            f"{sorted(str(value) for value in applicability.blocking_hold_ids)}"
        )

    if (
        authorization.retention_policy_version != record.retention_policy_version
        or authorization.authorized_record_version != record.record_version
    ):
        raise DestructionAuthorizationStaleError(
            f"authorization {authorization.authorization_id} was issued against policy version "
            f"{authorization.retention_policy_version}/record version "
            f"{authorization.authorized_record_version}; the record is now at "
            f"{record.retention_policy_version}/{record.record_version}"
        )

    now = clock.now()
    before = _state_hash(governed_record_full_state_payload(record))
    stored_evidence = evidence_store.create_once(
        DestructionEvidence(
            evidence_id=evidence_id if evidence_id is not None else generate_uuid(),
            record_id=record.record_id,
            organization_id=record.organization_id,
            authorization_id=authorization.authorization_id,
            disposition_action=authorization.disposition_action,
            executed_at=now,
            executed_by_authority_reference=executed_by_authority_reference,
            evidence_digest=evidence_digest,
            retention_policy_id=authorization.retention_policy_id,
            retention_policy_version=authorization.retention_policy_version,
        )
    )
    destroyed = record_store.save(record.with_destruction_evidence(stored_evidence.evidence_id))
    after = _state_hash(governed_record_full_state_payload(destroyed))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="governed_record.destroyed",
        occurred_at=now,
        context=context,
        target_type="governed_record",
        target_id=record.record_id,
        action="execute_destruction",
        reason_code=_RECORD_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_record_destroyed_event(
        event_id=resolved_event_id,
        record=destroyed,
        evidence=stored_evidence,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return DestructionResult(
        record=destroyed, evidence=stored_evidence, event=event, audit_event=audit_event
    )


# ---------------------------------------------------------------------------
# Legal Hold (ADR-039)
# ---------------------------------------------------------------------------


def place_legal_hold(
    hold_store: LegalHoldStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hold_id: UUID,
    matter_reference: str,
    scope: LegalHoldScope,
    issued_by_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LegalHoldResult:
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        existing = hold_store.get_in_scope(hold_id, caller_organization_id)
        if existing is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no legal hold"
            )
        event = build_legal_hold_status_changed_event(
            event_id=resolved_event_id,
            hold=existing,
            action="issued",
            reason_code=_HOLD_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LegalHoldResult(hold=existing, event=event, audit_event=existing_audit)

    now = clock.now()
    stored = hold_store.save(
        LegalHold(
            hold_id=hold_id,
            organization_id=caller_organization_id,
            matter_reference=matter_reference,
            scope=scope,
            issued_at=now,
            issued_by_authority_reference=issued_by_authority_reference,
        ).with_issue_entry(reason_code=_HOLD_AUDIT)
    )
    after = _state_hash(legal_hold_full_state_payload(stored))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_hold.status_changed",
        occurred_at=now,
        context=context,
        target_type="legal_hold",
        target_id=hold_id,
        action="place_legal_hold",
        reason_code=_HOLD_AUDIT,
        before_hash="",
        after_hash=after,
        clock=clock,
    )
    event = build_legal_hold_status_changed_event(
        event_id=resolved_event_id,
        hold=stored,
        action="issued",
        reason_code=_HOLD_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return LegalHoldResult(hold=stored, event=event, audit_event=audit_event)


def release_legal_hold(
    hold_store: LegalHoldStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hold_id: UUID,
    released_by_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LegalHoldResult:
    """Release a hold. Appends to the hold's own history; never rewrites
    the issue entry, and never deletes the hold."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    hold = hold_store.get_in_scope(hold_id, caller_organization_id)
    if hold is None:
        _raise_not_found("legal hold", hold_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_legal_hold_status_changed_event(
            event_id=resolved_event_id,
            hold=hold,
            action="released",
            reason_code=_HOLD_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LegalHoldResult(hold=hold, event=event, audit_event=existing_audit)

    now = clock.now()
    before = _state_hash(legal_hold_full_state_payload(hold))
    released = hold_store.save(
        hold.release(
            now,
            released_by_authority_reference=released_by_authority_reference,
            reason_code=_HOLD_AUDIT,
        )
    )
    after = _state_hash(legal_hold_full_state_payload(released))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_hold.status_changed",
        occurred_at=now,
        context=context,
        target_type="legal_hold",
        target_id=hold_id,
        action="release_legal_hold",
        reason_code=_HOLD_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_legal_hold_status_changed_event(
        event_id=resolved_event_id,
        hold=released,
        action="released",
        reason_code=_HOLD_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return LegalHoldResult(hold=released, event=event, audit_event=audit_event)


def mark_legal_hold_indeterminate(
    hold_store: LegalHoldStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hold_id: UUID,
    actor_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LegalHoldResult:
    """Record that this hold's state can no longer be established.

    Every covered record then fails closed on eligibility assessment and
    destruction (invariant 15). This exists so "unknown" is a real,
    auditable state rather than an absence that silently reads as
    "unheld"."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    hold = hold_store.get_in_scope(hold_id, caller_organization_id)
    if hold is None:
        _raise_not_found("legal hold", hold_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_legal_hold_status_changed_event(
            event_id=resolved_event_id,
            hold=hold,
            action="marked_indeterminate",
            reason_code=LegalHoldStateUnknownError.reason_code,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LegalHoldResult(hold=hold, event=event, audit_event=existing_audit)

    now = clock.now()
    before = _state_hash(legal_hold_full_state_payload(hold))
    marked = hold_store.save(
        hold.mark_indeterminate(
            now,
            actor_authority_reference=actor_authority_reference,
            reason_code=LegalHoldStateUnknownError.reason_code,
        )
    )
    after = _state_hash(legal_hold_full_state_payload(marked))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_hold.status_changed",
        occurred_at=now,
        context=context,
        target_type="legal_hold",
        target_id=hold_id,
        action="mark_legal_hold_indeterminate",
        reason_code=LegalHoldStateUnknownError.reason_code,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_legal_hold_status_changed_event(
        event_id=resolved_event_id,
        hold=marked,
        action="marked_indeterminate",
        reason_code=LegalHoldStateUnknownError.reason_code,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return LegalHoldResult(hold=marked, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Data catalog & processing registry (ADR-040)
# ---------------------------------------------------------------------------


def register_data_asset(
    asset_store: DataAssetStore,
    policy_store: RetentionPolicyStore,
    context: RequestContext,
    asset: DataAsset,
) -> DataAsset:
    caller_organization_id = _require_scope(context)
    _require_entity_scope(asset.organization_id, what="data asset")
    if asset.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a data asset may only be registered inside the caller's own organization"
        )
    if policy_store.latest_version(asset.retention_policy_reference) is None:
        _raise_not_found("retention policy", asset.retention_policy_reference)
    return asset_store.save(asset)


def register_processing_activity(
    activity_store: ProcessingActivityStore,
    policy_store: RetentionPolicyStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    activity: ProcessingActivity,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProcessingActivityResult:
    """Register a processing activity.

    The mandatory retention reference is resolved against the policy
    store rather than merely type-checked, so a registry entry can never
    point at a retention policy that does not exist or belongs to another
    organization."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(activity.organization_id, what="processing activity")
    if activity.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a processing activity may only be registered inside the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        existing = activity_store.get_in_scope(activity.activity_id, caller_organization_id)
        if existing is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no activity"
            )
        event = build_processing_activity_status_changed_event(
            event_id=resolved_event_id,
            activity=existing,
            reason_code=_REGISTRY_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProcessingActivityResult(activity=existing, event=event, audit_event=existing_audit)

    policy = policy_store.latest_version(activity.retention_policy_reference)
    if policy is None:
        _raise_not_found("retention policy", activity.retention_policy_reference)
    if policy.organization_id != activity.organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a processing activity may not reference another organization's retention policy"
        )

    now = clock.now()
    stored = activity_store.save(activity)
    after = _state_hash(processing_activity_full_state_payload(stored))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="processing_activity.status_changed",
        occurred_at=now,
        context=context,
        target_type="processing_activity",
        target_id=stored.activity_id,
        action="register_processing_activity",
        reason_code=_REGISTRY_AUDIT,
        before_hash="",
        after_hash=after,
        clock=clock,
    )
    event = build_processing_activity_status_changed_event(
        event_id=resolved_event_id,
        activity=stored,
        reason_code=_REGISTRY_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProcessingActivityResult(activity=stored, event=event, audit_event=audit_event)


def change_processing_activity_status(
    activity_store: ProcessingActivityStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    activity_id: UUID,
    target_status: RegistryEntryStatus,
    clock: Clock,
    event_id: UUID | None = None,
    expected_activity_version: int | None = None,
) -> ProcessingActivityResult:
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)

    activity = activity_store.get_in_scope(activity_id, caller_organization_id)
    if activity is None:
        _raise_not_found("processing activity", activity_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_processing_activity_status_changed_event(
            event_id=resolved_event_id,
            activity=activity,
            reason_code=_REGISTRY_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProcessingActivityResult(activity=activity, event=event, audit_event=existing_audit)

    _check_expected_version(
        activity.activity_version, expected_activity_version, what="processing activity"
    )
    now = clock.now()
    before = _state_hash(processing_activity_full_state_payload(activity))
    updated = activity_store.save(activity.with_status(target_status))
    after = _state_hash(processing_activity_full_state_payload(updated))

    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="processing_activity.status_changed",
        occurred_at=now,
        context=context,
        target_type="processing_activity",
        target_id=activity_id,
        action="change_processing_activity_status",
        reason_code=_REGISTRY_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_processing_activity_status_changed_event(
        event_id=resolved_event_id,
        activity=updated,
        reason_code=_REGISTRY_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProcessingActivityResult(activity=updated, event=event, audit_event=audit_event)


def read_processing_activity(
    activity_store: ProcessingActivityStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    activity_id: UUID,
    clock: Clock,
) -> ProcessingActivity:
    """Read one processing activity.

    In-scope reads resolve normally. A caller presenting cross-scope
    authority may reach another organization's entry if a grant carrying
    `read_processing_registry` permits it; a caller presenting nothing
    gets the non-disclosing not-found error."""
    caller_organization_id = _require_scope(context)
    in_scope = activity_store.get_in_scope(activity_id, caller_organization_id)
    if in_scope is not None:
        return in_scope
    if not context.authority_reference_ids:
        _raise_not_found("processing activity", activity_id)
    now = clock.now()
    for grant_id in sorted(context.authority_reference_ids):
        grant = grant_store.get(grant_id)
        if grant is None:
            continue
        foreign = activity_store.get_in_scope(activity_id, grant.granting_organization_id)
        if foreign is None:
            continue
        _require_cross_scope_authority(
            grant_store,
            context,
            target_organization_id=grant.granting_organization_id,
            capability=ScopeCapability.READ_PROCESSING_REGISTRY,
            now=now,
        )
        return foreign
    _raise_not_found("processing activity", activity_id)


# ---------------------------------------------------------------------------
# Governed procedural cases (ADR-041/ADR-042)
# ---------------------------------------------------------------------------


def _require_case_open(case: ProceduralCase) -> None:
    """A closed case is not modifiable by ordinary commands.

    Challenging a decision goes through `file_appeal` - its own governed
    transition producing a separate case, never an in-place edit of a
    closed one."""
    if case.status is CaseStatus.CLOSED:
        raise ProceduralCaseClosedError(
            f"case {case.case_id} is closed; ordinary commands cannot modify it"
        )


def _load_case_for_write(
    case_store: ProceduralCaseStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    case_id: UUID,
    capability: ScopeCapability,
    now: datetime,
) -> ProceduralCase:
    """Resolve a case the caller may act on.

    In-scope: returned directly. Out of scope with a presented grant:
    checked against that grant. Out of scope with nothing presented:
    non-disclosing not-found."""
    caller_organization_id = _require_scope(context)
    in_scope = case_store.get_in_scope(case_id, caller_organization_id)
    if in_scope is not None:
        return in_scope
    if not context.authority_reference_ids:
        _raise_not_found("procedural case", case_id)
    foreign = case_store.get_unscoped(case_id)
    if foreign is None:
        _raise_not_found("procedural case", case_id)
    _require_cross_scope_authority(
        grant_store,
        context,
        target_organization_id=foreign.organization_id,
        capability=capability,
        now=now,
    )
    return foreign


def open_procedural_case(
    case_store: ProceduralCaseStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    case: ProceduralCase,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralCaseResult:
    """Open a governed case inside the caller's own organization.

    A case may never be opened into another organization's scope, even
    with a cross-scope grant: creating obligations inside a scope one
    does not own is not a capability this pack grants at all."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(case.organization_id, what="procedural case")
    if case.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a procedural case may only be opened inside the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        existing = case_store.get_in_scope(case.case_id, caller_organization_id)
        if existing is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no case"
            )
        event = build_case_status_changed_event(
            event_id=resolved_event_id,
            case=existing,
            reason_code=_CASE_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralCaseResult(case=existing, event=event, audit_event=existing_audit)

    now = clock.now()
    stored = case_store.save(case)
    after = _state_hash(procedural_case_full_state_payload(stored))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_case",
        target_id=case.case_id,
        action="open_procedural_case",
        reason_code=_CASE_AUDIT,
        before_hash="",
        after_hash=after,
        clock=clock,
    )
    event = build_case_status_changed_event(
        event_id=resolved_event_id,
        case=stored,
        reason_code=_CASE_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralCaseResult(case=stored, event=event, audit_event=audit_event)


def read_procedural_case(
    case_store: ProceduralCaseStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    case_id: UUID,
    clock: Clock,
) -> ProceduralCase:
    return _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.READ_CASE,
        now=clock.now(),
    )


def assign_case_handler(
    case_store: ProceduralCaseStore,
    role_store: CaseRoleAssignmentStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    case_id: UUID,
    handler_party_reference: UUID,
    assigned_by_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralCaseResult:
    """Assign the case handler - a role distinct from the procedural
    authority and from the independent decision-maker (invariant 8)."""
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    _require_case_open(case)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_case_status_changed_event(
            event_id=resolved_event_id,
            case=case,
            reason_code=_CASE_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralCaseResult(case=case, event=event, audit_event=existing_audit)

    before = _state_hash(procedural_case_full_state_payload(case))
    updated = case_store.save(case.with_case_handler(handler_party_reference))
    role_store.append(
        CaseRoleAssignment(
            assignment_id=generate_uuid(),
            case_id=case.case_id,
            organization_id=case.organization_id,
            role=ProceduralRole.CASE_HANDLER,
            party_reference=handler_party_reference,
            assigned_at=now,
            assigned_by_party_reference=assigned_by_party_reference,
        )
    )
    after = _state_hash(procedural_case_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_case",
        target_id=case_id,
        action="assign_case_handler",
        reason_code=_CASE_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_case_status_changed_event(
        event_id=resolved_event_id,
        case=updated,
        reason_code=_CASE_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralCaseResult(case=updated, event=event, audit_event=audit_event)


def declare_conflict_of_interest(
    case_store: ProceduralCaseStore,
    conflict_store: ConflictDeclarationStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    case_id: UUID,
    party_reference: UUID,
    state: ConflictState,
    basis_code: str,
    clock: Clock,
    declaration_id: UUID | None = None,
    decided_by_party_reference: UUID | None = None,
) -> ConflictOfInterestDeclaration:
    """File an explicit conflict-of-interest declaration (invariant 10).

    A declaration is required for anyone before they can become the
    independent decision-maker; a `declared` or `confirmed` state makes
    them ineligible."""
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    _require_case_open(case)
    decided = state in {ConflictState.CONFIRMED, ConflictState.WAIVED}
    return conflict_store.save(
        ConflictOfInterestDeclaration(
            declaration_id=declaration_id if declaration_id is not None else generate_uuid(),
            case_id=case.case_id,
            organization_id=case.organization_id,
            party_reference=party_reference,
            state=state,
            basis_code=basis_code,
            declared_at=now,
            decided_by_party_reference=decided_by_party_reference,
            decided_at=now if decided and decided_by_party_reference is not None else None,
        )
    )


def assign_independent_decision_maker(
    case_store: ProceduralCaseStore,
    role_store: CaseRoleAssignmentStore,
    conflict_store: ConflictDeclarationStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    case_id: UUID,
    candidate_party_reference: UUID,
    appointing_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralCaseResult:
    """Assign the independent decision-maker, enforcing invariants 8, 9
    and 10 through `domain.assert_decision_maker_eligible`."""
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    _require_case_open(case)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_case_status_changed_event(
            event_id=resolved_event_id,
            case=case,
            reason_code=_CASE_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralCaseResult(case=case, event=event, audit_event=existing_audit)

    assert_decision_maker_eligible(
        case=case,
        candidate_party_reference=candidate_party_reference,
        appointing_party_reference=appointing_party_reference,
        role_assignments=role_store.list_for_case(case_id),
        conflict_declarations=conflict_store.list_for_case(case_id),
    )

    before = _state_hash(procedural_case_full_state_payload(case))
    updated = case_store.save(case.with_decision_maker(candidate_party_reference))
    role_store.append(
        CaseRoleAssignment(
            assignment_id=generate_uuid(),
            case_id=case.case_id,
            organization_id=case.organization_id,
            role=ProceduralRole.INDEPENDENT_DECISION_MAKER,
            party_reference=candidate_party_reference,
            assigned_at=now,
            assigned_by_party_reference=appointing_party_reference,
        )
    )
    after = _state_hash(procedural_case_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_case",
        target_id=case_id,
        action="assign_independent_decision_maker",
        reason_code=_CASE_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_case_status_changed_event(
        event_id=resolved_event_id,
        case=updated,
        reason_code=_CASE_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralCaseResult(case=updated, event=event, audit_event=audit_event)


def register_dispute_parties(
    case_store: ProceduralCaseStore,
    parties_store: DisputePartiesStore,
    role_store: CaseRoleAssignmentStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    case_id: UUID,
    claimant_reference: UUID,
    respondent_reference: UUID,
    registered_by_party_reference: UUID,
    clock: Clock,
) -> DisputeParties:
    """Record the claimant/respondent handles for a dispute and their
    `CaseRoleAssignment` rows, so the independence checks in
    `assert_decision_maker_eligible` have something to see."""
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    _require_case_open(case)
    parties = parties_store.save(
        DisputeParties(
            case_id=case.case_id,
            organization_id=case.organization_id,
            claimant_reference=claimant_reference,
            respondent_reference=respondent_reference,
        )
    )
    for role, reference in (
        (ProceduralRole.CLAIMANT, claimant_reference),
        (ProceduralRole.RESPONDENT, respondent_reference),
    ):
        role_store.append(
            CaseRoleAssignment(
                assignment_id=generate_uuid(),
                case_id=case.case_id,
                organization_id=case.organization_id,
                role=role,
                party_reference=reference,
                assigned_at=now,
                assigned_by_party_reference=registered_by_party_reference,
            )
        )
    return parties


def _resolve_deciding_role(case: ProceduralCase, party_reference: UUID) -> ProceduralRole:
    if case.case_type in _DISPUTE_CASE_TYPES:
        if case.assigned_decision_maker_reference is None:
            raise DecisionAuthorityMissingError(
                "no independent decision-maker has been assigned to this dispute"
            )
        if party_reference != case.assigned_decision_maker_reference:
            raise DecisionAuthorityMissingError(
                "only the assigned independent decision-maker may decide this dispute"
            )
        return ProceduralRole.INDEPENDENT_DECISION_MAKER
    if party_reference == case.assigned_decision_maker_reference:
        return ProceduralRole.INDEPENDENT_DECISION_MAKER
    if party_reference == case.procedural_authority_reference:
        return ProceduralRole.PROCEDURAL_AUTHORITY
    raise DecisionAuthorityMissingError(
        "the acting party holds no procedural role permitted to decide this case"
    )


def record_case_decision(
    case_store: ProceduralCaseStore,
    decision_store: CaseDecisionStore,
    role_store: CaseRoleAssignmentStore,
    conflict_store: ConflictDeclarationStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    case_id: UUID,
    outcome: DecisionOutcome,
    decision_reason_code: str,
    decided_by_party_reference: UUID,
    clock: Clock,
    evidence_references: tuple[str, ...] = (),
    event_id: UUID | None = None,
    decision_id: UUID | None = None,
) -> ProceduralCaseResult:
    """Record the case decision.

    Only the assigned independent decision-maker (for dispute-shaped
    cases) or the procedural authority (for the remaining case types) may
    decide, and never anyone carrying a blocking conflict declaration."""
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    _require_case_open(case)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_case_status_changed_event(
            event_id=resolved_event_id,
            case=case,
            reason_code=_CASE_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralCaseResult(case=case, event=event, audit_event=existing_audit)

    decided_by_role = _resolve_deciding_role(case, decided_by_party_reference)
    for declaration in conflict_store.list_for_case(case_id):
        if declaration.party_reference == decided_by_party_reference and declaration.is_blocking:
            raise ConflictOfInterestBlockingError(
                "the deciding party has a declared or confirmed conflict of interest"
            )

    before = _state_hash(procedural_case_full_state_payload(case))
    decision = decision_store.create_once(
        CaseDecision(
            decision_id=decision_id if decision_id is not None else generate_uuid(),
            case_id=case.case_id,
            organization_id=case.organization_id,
            outcome=outcome,
            reason_code=decision_reason_code,
            decided_at=now,
            decided_by_party_reference=decided_by_party_reference,
            decided_by_role=decided_by_role,
            evidence_references=evidence_references,
        )
    )
    updated = case_store.save(case.with_decision(decision))
    after = _state_hash(procedural_case_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_case",
        target_id=case_id,
        action="record_case_decision",
        reason_code=_CASE_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_case_status_changed_event(
        event_id=resolved_event_id,
        case=updated,
        reason_code=_CASE_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralCaseResult(case=updated, event=event, audit_event=audit_event)


def transition_procedural_case(
    case_store: ProceduralCaseStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    case_id: UUID,
    target_status: CaseStatus,
    clock: Clock,
    closure_reason_code: str | None = None,
    event_id: UUID | None = None,
    expected_case_version: int | None = None,
) -> ProceduralCaseResult:
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_case_status_changed_event(
            event_id=resolved_event_id,
            case=case,
            reason_code=_CASE_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralCaseResult(case=case, event=event, audit_event=existing_audit)

    _check_expected_version(case.case_version, expected_case_version, what="procedural case")
    before = _state_hash(procedural_case_full_state_payload(case))
    updated = case_store.save(
        case.transition(target_status, now, closure_reason_code=closure_reason_code)
    )
    after = _state_hash(procedural_case_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_case",
        target_id=case_id,
        action="transition_procedural_case",
        reason_code=_CASE_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_case_status_changed_event(
        event_id=resolved_event_id,
        case=updated,
        reason_code=_CASE_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralCaseResult(case=updated, event=event, audit_event=audit_event)


def file_appeal(
    case_store: ProceduralCaseStore,
    appeal_store: AppealReferenceStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    original_case_id: UUID,
    appeal_case: ProceduralCase,
    filed_by_party_reference: UUID,
    clock: Clock,
    appeal_id: UUID | None = None,
) -> AppealReference:
    """File an appeal against a decided or closed case.

    The appeal is a *separate* governed case plus an `AppealReference`;
    the original case is never reopened or edited, which is what keeps
    "a closed case is not modifiable by an ordinary command" true."""
    caller_organization_id = _require_scope(context)
    now = clock.now()
    original = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=original_case_id,
        capability=ScopeCapability.MANAGE_CASE,
        now=now,
    )
    if original.status not in {CaseStatus.DECIDED, CaseStatus.CLOSED}:
        raise ProceduralIndependenceViolationError("only a decided or closed case can be appealed")
    if appeal_case.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "an appeal case must be opened inside the caller's own organization"
        )
    case_store.save(appeal_case)
    return appeal_store.append(
        AppealReference(
            appeal_id=appeal_id if appeal_id is not None else generate_uuid(),
            organization_id=original.organization_id,
            original_case_id=original.case_id,
            appeal_case_id=appeal_case.case_id,
            filed_at=now,
            filed_by_party_reference=filed_by_party_reference,
        )
    )


# ---------------------------------------------------------------------------
# Deadlines (ADR-041)
# ---------------------------------------------------------------------------


def define_deadline(
    definition_store: DeadlineDefinitionStore,
    context: RequestContext,
    definition: DeadlineDefinition,
) -> DeadlineDefinition:
    caller_organization_id = _require_scope(context)
    _require_entity_scope(definition.organization_id, what="deadline definition")
    if definition.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a deadline definition may only be created inside the caller's own organization"
        )
    return definition_store.save(definition)


def start_deadline(
    case_store: ProceduralCaseStore,
    definition_store: DeadlineDefinitionStore,
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    case_id: UUID,
    definition_id: UUID,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
    supersedes_deadline_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    """Start a deadline on a case.

    Invariant 7 is enforced here: if a live (running/suspended/escalated)
    deadline already exists for this `(case, deadline_code)` pair, the
    command refuses with `DEADLINE_SILENT_REPLACEMENT_REJECTED` unless
    the caller explicitly names it in `supersedes_deadline_id`. When it
    does, the old instance is *superseded* - it keeps its whole history
    and gains a `superseded_by_deadline_id` link - rather than being
    silently replaced or reset."""
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    case = _load_case_for_write(
        case_store,
        grant_store,
        context,
        case_id=case_id,
        capability=ScopeCapability.MANAGE_DEADLINE,
        now=now,
    )
    _require_case_open(case)

    definition = definition_store.get_in_scope(definition_id, case.organization_id)
    if definition is None:
        _raise_not_found("deadline definition", definition_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        existing = deadline_store.get_in_scope(deadline_id, case.organization_id)
        if existing is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no deadline"
            )
        event = build_deadline_state_changed_event(
            event_id=resolved_event_id,
            deadline=existing,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralDeadlineResult(deadline=existing, event=event, audit_event=existing_audit)

    live = [
        deadline
        for deadline in deadline_store.list_for_case(case_id)
        if deadline.deadline_code == definition.deadline_code
        and deadline.status in _LIVE_DEADLINE_STATES
    ]
    if live and supersedes_deadline_id is None:
        raise DeadlineSilentReplacementRejectedError(
            f"case {case_id} already has a live {definition.deadline_code!r} deadline "
            f"({live[0].deadline_id}); name it in supersedes_deadline_id to replace it explicitly"
        )
    if supersedes_deadline_id is not None:
        predecessor = deadline_store.get_in_scope(supersedes_deadline_id, case.organization_id)
        if predecessor is None:
            _raise_not_found("procedural deadline", supersedes_deadline_id)
        deadline_store.save(
            predecessor.supersede(
                now,
                successor_deadline_id=deadline_id,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    stored = deadline_store.save(
        build_started_deadline(
            deadline_id=deadline_id,
            definition=definition,
            case_id=case.case_id,
            organization_id=case.organization_id,
            started_at=now,
            reason_code=reason_code,
            actor_party_reference=actor_party_reference,
            supersedes_deadline_id=supersedes_deadline_id,
        )
    )
    after = _state_hash(procedural_deadline_full_state_payload(stored))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_deadline.state_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_deadline",
        target_id=deadline_id,
        action="start_deadline",
        reason_code=_DEADLINE_AUDIT,
        before_hash="",
        after_hash=after,
        clock=clock,
    )
    event = build_deadline_state_changed_event(
        event_id=resolved_event_id,
        deadline=stored,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralDeadlineResult(deadline=stored, event=event, audit_event=audit_event)


def _load_deadline_for_write(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    now: datetime,
) -> ProceduralDeadline:
    caller_organization_id = _require_scope(context)
    in_scope = deadline_store.get_in_scope(deadline_id, caller_organization_id)
    if in_scope is not None:
        return in_scope
    if not context.authority_reference_ids:
        _raise_not_found("procedural deadline", deadline_id)
    for grant_id in sorted(context.authority_reference_ids):
        grant = grant_store.get(grant_id)
        if grant is None:
            continue
        candidate = deadline_store.get_in_scope(deadline_id, grant.granting_organization_id)
        if candidate is None:
            continue
        _require_cross_scope_authority(
            grant_store,
            context,
            target_organization_id=candidate.organization_id,
            capability=ScopeCapability.MANAGE_DEADLINE,
            now=now,
        )
        return candidate
    _raise_not_found("procedural deadline", deadline_id)


def _apply_deadline_transition(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    action: str,
    apply: DeadlineTransitionFn,
    clock: Clock,
    event_id: UUID | None,
) -> ProceduralDeadlineResult:
    """Shared machinery for suspend/resume/extend/complete/escalate/expire.

    Every one of them appends to `history`; none of them can rewrite it,
    because `ProceduralDeadline` exposes no setter and
    `InMemoryProceduralDeadlineStore.save` additionally refuses any write
    whose history is not an extension of the stored prefix."""
    resolved_event_id = _resolved_event_id(event_id)
    now = clock.now()
    resolved = _load_deadline_for_write(
        deadline_store, grant_store, context, deadline_id=deadline_id, now=now
    )

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_deadline_state_changed_event(
            event_id=resolved_event_id,
            deadline=resolved,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ProceduralDeadlineResult(deadline=resolved, event=event, audit_event=existing_audit)

    before = _state_hash(procedural_deadline_full_state_payload(resolved))
    updated = deadline_store.save(apply(resolved, now))
    after = _state_hash(procedural_deadline_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_deadline.state_changed",
        occurred_at=now,
        context=context,
        target_type="procedural_deadline",
        target_id=deadline_id,
        action=action,
        reason_code=_DEADLINE_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_deadline_state_changed_event(
        event_id=resolved_event_id,
        deadline=updated,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return ProceduralDeadlineResult(deadline=updated, event=event, audit_event=audit_event)


def suspend_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="suspend_deadline",
        apply=lambda deadline, now: deadline.suspend(
            now, reason_code=reason_code, actor_party_reference=actor_party_reference
        ),
        clock=clock,
        event_id=event_id,
    )


def resume_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="resume_deadline",
        apply=lambda deadline, now: deadline.resume(
            now, reason_code=reason_code, actor_party_reference=actor_party_reference
        ),
        clock=clock,
        event_id=event_id,
    )


def extend_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    additional_days: int,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="extend_deadline",
        apply=lambda deadline, now: deadline.extend(
            now,
            additional_days=additional_days,
            reason_code=reason_code,
            actor_party_reference=actor_party_reference,
        ),
        clock=clock,
        event_id=event_id,
    )


def complete_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="complete_deadline",
        apply=lambda deadline, now: deadline.satisfy(
            now, reason_code=reason_code, actor_party_reference=actor_party_reference
        ),
        clock=clock,
        event_id=event_id,
    )


def escalate_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="escalate_deadline",
        apply=lambda deadline, now: deadline.escalate(
            now, reason_code=reason_code, actor_party_reference=actor_party_reference
        ),
        clock=clock,
        event_id=event_id,
    )


def expire_deadline(
    deadline_store: ProceduralDeadlineStore,
    grant_store: CrossScopeAuthorityGrantStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    reason_code: str,
    actor_party_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDeadlineResult:
    return _apply_deadline_transition(
        deadline_store,
        grant_store,
        audit_store,
        context,
        deadline_id=deadline_id,
        action="expire_deadline",
        apply=lambda deadline, now: deadline.expire(
            now, reason_code=reason_code, actor_party_reference=actor_party_reference
        ),
        clock=clock,
        event_id=event_id,
    )


# ---------------------------------------------------------------------------
# Data-subject and legal requests (ADR-040/ADR-041)
# ---------------------------------------------------------------------------


def intake_data_subject_request(
    case_store: ProceduralCaseStore,
    request_store: DataSubjectRequestStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    request_id: UUID,
    case: ProceduralCase,
    request_type: DataSubjectRequestType,
    requester_party_reference: UUID,
    scope_description_code: str,
    clock: Clock,
    event_id: UUID | None = None,
) -> DataSubjectRequestResult:
    """Take in a data-subject or legal request together with the governed
    case that carries its procedure.

    No identity attribute is accepted here at all: the requester is a
    per-case handle and verification starts at `not_verified`."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(case.organization_id, what="procedural case")
    if case.organization_id != caller_organization_id:
        raise CrossOrganizationCaseAccessDeniedError(
            "a data-subject request may only be taken in inside the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        existing = request_store.get_in_scope(request_id, caller_organization_id)
        if existing is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no request"
            )
        event = build_request_status_changed_event(
            event_id=resolved_event_id,
            request=existing,
            reason_code=_REQUEST_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DataSubjectRequestResult(request=existing, event=event, audit_event=existing_audit)

    now = clock.now()
    case_store.save(case)
    request = request_store.save(
        DataSubjectRequest(
            request_id=request_id,
            case_id=case.case_id,
            organization_id=case.organization_id,
            request_type=request_type,
            status=DataSubjectRequestStatus.RECEIVED,
            requester_party_reference=requester_party_reference,
            received_at=now,
            scope_description_code=scope_description_code,
            identity_verification_status=IdentityVerificationStatus.NOT_VERIFIED,
        )
    )
    after = _state_hash(data_subject_request_full_state_payload(request))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="data_subject_request.status_changed",
        occurred_at=now,
        context=context,
        target_type="data_subject_request",
        target_id=request_id,
        action="intake_data_subject_request",
        reason_code=_REQUEST_AUDIT,
        before_hash="",
        after_hash=after,
        clock=clock,
    )
    event = build_request_status_changed_event(
        event_id=resolved_event_id,
        request=request,
        reason_code=_REQUEST_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return DataSubjectRequestResult(request=request, event=event, audit_event=audit_event)


def set_identity_verification_status(
    request_store: DataSubjectRequestStore,
    context: RequestContext,
    *,
    request_id: UUID,
    status: IdentityVerificationStatus,
    verification_reference: UUID | None,
) -> DataSubjectRequest:
    """Record *only* the verification status plus an opaque reference to
    the service that performed it (invariant 11).

    There is deliberately no parameter here that could carry an identity
    attribute, document, eID assertion or KYC payload."""
    caller_organization_id = _require_scope(context)
    request = request_store.get_in_scope(request_id, caller_organization_id)
    if request is None:
        _raise_not_found("data-subject request", request_id)
    return request_store.save(
        request.with_identity_verification(status, verification_reference=verification_reference)
    )


def advance_data_subject_request(
    request_store: DataSubjectRequestStore,
    context: RequestContext,
    *,
    request_id: UUID,
    target_status: DataSubjectRequestStatus,
) -> DataSubjectRequest:
    caller_organization_id = _require_scope(context)
    request = request_store.get_in_scope(request_id, caller_organization_id)
    if request is None:
        _raise_not_found("data-subject request", request_id)
    return request_store.save(request.with_status(target_status))


def record_search_result_reference(
    request_store: DataSubjectRequestStore,
    context: RequestContext,
    *,
    request_id: UUID,
    search_result_reference: str,
) -> DataSubjectRequest:
    """Attach an opaque pointer to a search result set produced elsewhere.

    A *reference*, never the result content: compliance-service records
    that a search happened and where its output lives, not what it
    found."""
    caller_organization_id = _require_scope(context)
    request = request_store.get_in_scope(request_id, caller_organization_id)
    if request is None:
        _raise_not_found("data-subject request", request_id)
    return request_store.save(request.with_search_result_reference(search_result_reference))


def decide_data_subject_request(
    request_store: DataSubjectRequestStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    request_id: UUID,
    decision: ResponseDecision,
    limitation_reason_code: str | None,
    completion_evidence_reference: str | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> DataSubjectRequestResult:
    """Record the response decision.

    Refuses unless identity verification reached `verified` - a request
    is never answered on the strength of an unverified claim, and this
    service still never sees the identity data behind that status."""
    caller_organization_id = _require_scope(context)
    resolved_event_id = _resolved_event_id(event_id)
    request = request_store.get_in_scope(request_id, caller_organization_id)
    if request is None:
        _raise_not_found("data-subject request", request_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_request_status_changed_event(
            event_id=resolved_event_id,
            request=request,
            reason_code=_REQUEST_AUDIT,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DataSubjectRequestResult(request=request, event=event, audit_event=existing_audit)

    if request.identity_verification_status is not IdentityVerificationStatus.VERIFIED:
        raise IdentityVerificationInsufficientError(
            f"request {request_id} cannot be answered while identity verification is "
            f"{request.identity_verification_status.value}"
        )

    now = clock.now()
    before = _state_hash(data_subject_request_full_state_payload(request))
    target_status = (
        DataSubjectRequestStatus.REFUSED
        if decision is ResponseDecision.REFUSED
        else DataSubjectRequestStatus.ANSWERED
    )
    updated = request_store.save(
        request.with_response(
            decision,
            limitation_reason_code=limitation_reason_code,
            completion_evidence_reference=completion_evidence_reference,
        ).with_status(target_status)
    )
    after = _state_hash(data_subject_request_full_state_payload(updated))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="data_subject_request.status_changed",
        occurred_at=now,
        context=context,
        target_type="data_subject_request",
        target_id=request_id,
        action="decide_data_subject_request",
        reason_code=_REQUEST_AUDIT,
        before_hash=before,
        after_hash=after,
        clock=clock,
    )
    event = build_request_status_changed_event(
        event_id=resolved_event_id,
        request=updated,
        reason_code=_REQUEST_AUDIT,
        actor=context.actor,
        correlation_id=context.correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    return DataSubjectRequestResult(request=updated, event=event, audit_event=audit_event)


# ===========================================================================
# Architecture & Domain Framework 0.8.1 - legal-case substrate commands
#
# Every command below follows the same four conventions as the round-1
# commands above (injected `Clock`, `event_id` idempotency through Audit
# Core, audit append with canonical before/after hashes, reason-coded
# refusal) and adds one more that the Framework makes explicit:
#
# 5. **A capability check before every consequential act.** Deciding,
#    ordering, ruling or serving is gated on jurisdiction
#    (`assert_may_decide_substantively`), on non-recusal
#    (`assert_actor_not_recused`) and, for a final decision, on the full
#    due-process prerequisite set (`assert_due_process_complete`). None of
#    these are advisory: they raise, and the command does not proceed.
# ===========================================================================


_LEGAL_CASE_AUDIT = "COMPLIANCE_LEGAL_CASE_STATUS_CHANGED"
_JURISDICTION_AUDIT = "COMPLIANCE_JURISDICTION_STATUS_CHANGED"
_PARTY_AUDIT = "COMPLIANCE_CASE_PARTY_REGISTERED"
_REPRESENTATION_AUDIT = "COMPLIANCE_REPRESENTATION_STATUS_CHANGED"
_FILING_AUDIT = "COMPLIANCE_FILING_STATUS_CHANGED"
_HEARING_AUDIT = "COMPLIANCE_HEARING_STATUS_CHANGED"
_INTERIM_MEASURE_AUDIT = "COMPLIANCE_INTERIM_MEASURE_DECIDED"
_DECISION_AUDIT = "COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED"
_REMEDY_AUDIT = "COMPLIANCE_REMEDY_STATUS_CHANGED"
_RECUSAL_AUDIT = "COMPLIANCE_RECUSAL_RECORDED"
_NOTICE_AUDIT = "COMPLIANCE_OFFICIAL_NOTICE_ISSUED"
_SERVICE_ATTEMPT_AUDIT = "COMPLIANCE_SERVICE_ATTEMPT_RECORDED"
_NOTICE_EFFECT_AUDIT = "COMPLIANCE_NOTICE_EFFECT_DETERMINED"
_DEADLINE_TRIGGER_AUDIT = "COMPLIANCE_PROCEDURAL_DEADLINE_TRIGGERED"
_RECORD_CLASS_AUDIT = "COMPLIANCE_RECORD_CLASS_REGISTERED"
_HOLD_PROPAGATION_AUDIT = "COMPLIANCE_LEGAL_HOLD_PROPAGATION_REGISTERED"
_DPIA_AUDIT = "COMPLIANCE_DPIA_STATUS_CHANGED"
_ACTIVATION_AUDIT = "COMPLIANCE_PROCESSING_ACTIVATION_DECIDED"


class DecisionEffectAction(StrEnum):
    """Which of the three effect transitions `change_decision_effect` is
    being asked to perform.

    A closed enum rather than three separate commands because all three
    share one precondition set, one audit shape and one event type - and
    because a caller cannot then invent a fourth."""

    COMMENCE = "commence"
    SUSPEND = "suspend"
    RESUME = "resume"


#: The empty canonical snapshot used as `before_hash` when a command
#: creates an object that did not previously exist. A literal constant
#: rather than an empty string so the audit chain's before/after pair is
#: always two canonical JSON documents.
_NO_PRIOR_STATE = _state_hash({})


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LegalCaseResult:
    case: LegalCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class JurisdictionResult:
    determination: JurisdictionDetermination
    case: LegalCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CasePartyResult:
    party: CaseParty
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RepresentationResult:
    mandate: RepresentationMandate
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class FilingResult:
    filing: Filing
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class HearingResult:
    hearing: Hearing
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class InterimMeasureResult:
    measure: InterimMeasure
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProceduralDecisionResult:
    decision: ProceduralDecision
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RemedyResult:
    remedy: Remedy
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RecusalResult:
    recusal: RecusalRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ReplacementResult:
    assignment: ReplacementAssignment
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class OfficialNoticeResult:
    notice: OfficialNotice
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ServiceAttemptResult:
    attempt: ServiceAttempt
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class NoticeEffectResult:
    decision: NoticeEffectDecision
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DeadlineTriggerResult:
    trigger: DeadlineTrigger
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RecordClassResult:
    record_class: RecordClass
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class HoldPropagationResult:
    propagation: HoldPropagationRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DPIARequirementResult:
    determination: DPIARequirementDetermination
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DPIAResult:
    dpia: DataProtectionImpactAssessment
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProcessingActivationResult:
    decision: ProcessingActivationDecision
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# Shared guards for the legal-case substrate
# ---------------------------------------------------------------------------


def _load_legal_case(
    case_store: LegalCaseStore, context: RequestContext, legal_case_id: UUID
) -> tuple[LegalCase, UUID]:
    """Load a case that the caller's own organization may see, or raise
    the non-disclosing not-found error.

    Returns the case together with the caller's scope, because every
    caller of this helper needs both and re-deriving the scope invites
    the two drifting apart."""
    caller_organization_id = _require_scope(context)
    case = case_store.get_in_scope(legal_case_id, caller_organization_id)
    if case is None:
        _raise_not_found("legal case", legal_case_id)
    return case, caller_organization_id


def _require_legal_case_open(case: LegalCase) -> None:
    if case.is_closed:
        raise ProceduralCaseClosedError(
            f"legal case {case.legal_case_id} is closed and accepts no further procedural acts"
        )


def _effective_jurisdiction(
    jurisdiction_store: JurisdictionStore, case: LegalCase
) -> JurisdictionDetermination | None:
    if case.jurisdiction_id is None:
        return None
    return jurisdiction_store.get(case.jurisdiction_id)


def _guard_acting_authority(
    recusal_store: RecusalStore,
    *,
    case: LegalCase,
    acting_party_reference: UUID,
    at: datetime,
) -> None:
    """Refuse if the acting party is recused from this case.

    Framework hard invariant 53: recusal blocks capability. Applied to
    *every* consequential command rather than only to final decisions,
    because scheduling a hearing or ordering an interim measure is just as
    much an exercise of authority."""
    assert_actor_not_recused(
        actor_party_reference=acting_party_reference,
        recusals=recusal_store.list_for_case(case.legal_case_id),
        at=at,
    )


# ---------------------------------------------------------------------------
# Legal case lifecycle
# ---------------------------------------------------------------------------


def open_legal_case(
    case_store: LegalCaseStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    case: LegalCase,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> LegalCaseResult:
    """Open a legal case inside the caller's own organization.

    A case may be opened without jurisdiction - intake precedes competence
    - but it cannot then be moved into any substantive status until a
    jurisdiction determination exists. `LegalCase.transition` enforces
    that, so opening a case here grants no substantive capability."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(case.organization_id, what="legal case")
    if case.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a legal case may only be opened inside the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = case_store.get_in_scope(case.legal_case_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no legal case"
            )
        return LegalCaseResult(
            case=stored,
            event=build_legal_case_opened_event(
                event_id=resolved_event_id,
                case=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = case_store.save(case)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_case.opened",
        occurred_at=now,
        context=context,
        target_type="legal_case",
        target_id=stored.legal_case_id,
        action="open_legal_case",
        reason_code=_LEGAL_CASE_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(legal_case_full_state_payload(stored)),
        clock=clock,
    )
    return LegalCaseResult(
        case=stored,
        event=build_legal_case_opened_event(
            event_id=resolved_event_id,
            case=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def transition_legal_case(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    legal_case_id: UUID,
    target: LegalCaseStatus,
    reason_code: str,
    acting_authority_reference: UUID,
    closure_reason_code: str | None = None,
    clock: Clock,
    event_id: UUID | None = None,
    expected_case_version: int | None = None,
) -> LegalCaseResult:
    """Move a case to `target`.

    Three refusals stack here, in order, and each has its own code:
    the transition table (`PROCEDURAL_CASE_TRANSITION_INVALID`), the
    jurisdiction requirement for substantive statuses
    (`JURISDICTION_MISSING`), and recusal (`RECUSED_ACTOR_DENIED`)."""
    case, _ = _load_legal_case(case_store, context, legal_case_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        return LegalCaseResult(
            case=case,
            event=build_legal_case_status_changed_event(
                event_id=resolved_event_id,
                case=case,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    _check_expected_version(case.case_version, expected_case_version, what="legal case")
    now = clock.now()
    _guard_acting_authority(
        recusal_store, case=case, acting_party_reference=acting_authority_reference, at=now
    )
    if target in SUBSTANTIVE_CASE_STATUSES:
        assert_may_decide_substantively(
            case=case,
            jurisdiction=_effective_jurisdiction(jurisdiction_store, case),
            acting_authority_reference=acting_authority_reference,
            at=now,
        )

    before = _state_hash(legal_case_full_state_payload(case))
    updated = case_store.save(
        case.transition(
            target,
            now,
            reason_code=reason_code,
            actor_authority_reference=acting_authority_reference,
            closure_reason_code=closure_reason_code,
        )
    )
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_case.status_changed",
        occurred_at=now,
        context=context,
        target_type="legal_case",
        target_id=updated.legal_case_id,
        action="transition_legal_case",
        reason_code=_LEGAL_CASE_AUDIT,
        before_hash=before,
        after_hash=_state_hash(legal_case_full_state_payload(updated)),
        clock=clock,
    )
    return LegalCaseResult(
        case=updated,
        event=build_legal_case_status_changed_event(
            event_id=resolved_event_id,
            case=updated,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def reopen_legal_case(
    case_store: LegalCaseStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    prior_case_id: UUID,
    successor_case: LegalCase,
    clock: Clock,
    event_id: UUID | None = None,
) -> LegalCaseResult:
    """Open a successor case that points back at a closed one.

    Reopening does not resurrect the prior case and does not touch its
    closure: the prior case stays closed, with its closure reason, and the
    successor carries `reopened_from_case_id`. Anything else would make a
    closed case's history rewritable."""
    caller_organization_id = _require_scope(context)
    prior = case_store.get_in_scope(prior_case_id, caller_organization_id)
    if prior is None:
        _raise_not_found("legal case", prior_case_id)
    if successor_case.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a successor case must belong to the same organization as the case it reopens"
        )
    if successor_case.reopened_from_case_id != prior_case_id:
        raise ProceduralCaseTransitionInvalidError(
            "the successor case must name the case it reopens in reopened_from_case_id"
        )
    if not prior.is_closed:
        raise ProceduralCaseTransitionInvalidError(
            f"legal case {prior_case_id} is not closed and therefore cannot be reopened"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = case_store.get_in_scope(successor_case.legal_case_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no successor case"
            )
        return LegalCaseResult(
            case=stored,
            event=build_legal_case_reopened_event(
                event_id=resolved_event_id,
                case=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = case_store.save(successor_case)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_case.reopened",
        occurred_at=now,
        context=context,
        target_type="legal_case",
        target_id=stored.legal_case_id,
        action="reopen_legal_case",
        reason_code=_LEGAL_CASE_AUDIT,
        before_hash=_state_hash(legal_case_full_state_payload(prior)),
        after_hash=_state_hash(legal_case_full_state_payload(stored)),
        clock=clock,
    )
    return LegalCaseResult(
        case=stored,
        event=build_legal_case_reopened_event(
            event_id=resolved_event_id,
            case=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Jurisdiction
# ---------------------------------------------------------------------------


def determine_jurisdiction(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    determination: JurisdictionDetermination,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> JurisdictionResult:
    """Record which authority is competent for this case, and bind the
    case to that determination.

    The determination is *appended*: an earlier determination is never
    rewritten, so "who was competent, and until when" stays answerable
    after any number of challenges and transfers."""
    case, caller_organization_id = _load_legal_case(case_store, context, determination.case_id)
    if determination.organization_id != caller_organization_id:
        raise JurisdictionScopeMismatchError(
            "a jurisdiction determination must belong to the caller's own organization"
        )
    if determination.case_kind is not case.case_kind:
        raise JurisdictionScopeMismatchError(
            f"determination case kind {determination.case_kind.value} does not match case kind "
            f"{case.case_kind.value}"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = jurisdiction_store.get(determination.jurisdiction_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no determination"
            )
        return JurisdictionResult(
            determination=stored,
            case=case,
            event=build_jurisdiction_determined_event(
                event_id=resolved_event_id,
                determination=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = jurisdiction_store.append(determination)
    updated_case = case_store.save(case.with_jurisdiction(stored))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="jurisdiction.determined",
        occurred_at=now,
        context=context,
        target_type="jurisdiction_determination",
        target_id=stored.jurisdiction_id,
        action="determine_jurisdiction",
        reason_code=_JURISDICTION_AUDIT,
        before_hash=_state_hash(legal_case_full_state_payload(case)),
        after_hash=_state_hash(jurisdiction_full_state_payload(stored)),
        clock=clock,
    )
    return JurisdictionResult(
        determination=stored,
        case=updated_case,
        event=build_jurisdiction_determined_event(
            event_id=resolved_event_id,
            determination=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def challenge_jurisdiction(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    jurisdiction_id: UUID,
    reason_code: str,
    clock: Clock,
    event_id: UUID | None = None,
) -> JurisdictionResult:
    """Mark a determination challenged.

    A challenged determination stops permitting substantive decisions
    immediately - `assert_may_decide_substantively` refuses on it - which
    is the point: a contested competence must not silently keep producing
    binding outcomes while the challenge is pending."""
    caller_organization_id = _require_scope(context)
    determination = jurisdiction_store.get(jurisdiction_id)
    if determination is None or determination.organization_id != caller_organization_id:
        _raise_not_found("jurisdiction determination", jurisdiction_id)
    case, _ = _load_legal_case(case_store, context, determination.case_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = jurisdiction_store.get(jurisdiction_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("jurisdiction determination", jurisdiction_id)
        return JurisdictionResult(
            determination=stored,
            case=case,
            event=build_jurisdiction_challenged_event(
                event_id=resolved_event_id,
                determination=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    before = _state_hash(jurisdiction_full_state_payload(determination))
    stored = jurisdiction_store.save(determination.challenge(now, reason_code=reason_code))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="jurisdiction.challenged",
        occurred_at=now,
        context=context,
        target_type="jurisdiction_determination",
        target_id=stored.jurisdiction_id,
        action="challenge_jurisdiction",
        reason_code=_JURISDICTION_AUDIT,
        before_hash=before,
        after_hash=_state_hash(jurisdiction_full_state_payload(stored)),
        clock=clock,
    )
    return JurisdictionResult(
        determination=stored,
        case=case,
        event=build_jurisdiction_challenged_event(
            event_id=resolved_event_id,
            determination=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def transfer_jurisdiction(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    jurisdiction_id: UUID,
    successor: JurisdictionDetermination,
    reason_code: str,
    clock: Clock,
    event_id: UUID | None = None,
) -> JurisdictionResult:
    """Transfer competence to a successor determination.

    Both determinations survive. The outgoing one gains `valid_until` and
    a pointer to its successor; it is not rewritten to describe the new
    authority, because acts performed while it was competent must stay
    attributable to it (Framework 13.1, "preserved jurisdiction
    history")."""
    caller_organization_id = _require_scope(context)
    outgoing = jurisdiction_store.get(jurisdiction_id)
    if outgoing is None or outgoing.organization_id != caller_organization_id:
        _raise_not_found("jurisdiction determination", jurisdiction_id)
    if successor.organization_id != caller_organization_id:
        raise JurisdictionScopeMismatchError(
            "a successor determination must belong to the caller's own organization"
        )
    if successor.case_id != outgoing.case_id:
        raise JurisdictionScopeMismatchError(
            "a successor determination must belong to the same case"
        )
    if successor.supersedes_jurisdiction_id != jurisdiction_id:
        raise JurisdictionTransferRequiredError(
            "the successor determination must name the determination it supersedes"
        )
    case, _ = _load_legal_case(case_store, context, outgoing.case_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = jurisdiction_store.get(jurisdiction_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("jurisdiction determination", jurisdiction_id)
        return JurisdictionResult(
            determination=stored,
            case=case,
            event=build_jurisdiction_transferred_event(
                event_id=resolved_event_id,
                determination=stored,
                successor_jurisdiction_id=successor.jurisdiction_id,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    before = _state_hash(jurisdiction_full_state_payload(outgoing))
    stored_successor = jurisdiction_store.append(successor)
    stored = jurisdiction_store.save(
        outgoing.transfer_to(stored_successor.jurisdiction_id, at=now, reason_code=reason_code)
    )
    updated_case = case_store.save(case.with_jurisdiction(stored_successor))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="jurisdiction.transferred",
        occurred_at=now,
        context=context,
        target_type="jurisdiction_determination",
        target_id=stored.jurisdiction_id,
        action="transfer_jurisdiction",
        reason_code=_JURISDICTION_AUDIT,
        before_hash=before,
        after_hash=_state_hash(jurisdiction_full_state_payload(stored)),
        clock=clock,
    )
    return JurisdictionResult(
        determination=stored,
        case=updated_case,
        event=build_jurisdiction_transferred_event(
            event_id=resolved_event_id,
            determination=stored,
            successor_jurisdiction_id=stored_successor.jurisdiction_id,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Parties and representation
# ---------------------------------------------------------------------------


def register_case_party(
    case_store: LegalCaseStore,
    party_store: CasePartyStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    party: CaseParty,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> CasePartyResult:
    """Register a party on a case.

    `party.party_reference` must be a handle minted by
    `casework.mint_case_party_reference`; this command never accepts, and
    the store never records, anything that could resolve to a person
    outside this case (Framework hard invariant 1)."""
    case, caller_organization_id = _load_legal_case(case_store, context, party.case_id)
    _require_legal_case_open(case)
    if party.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a case party must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        for stored_party in party_store.list_for_case(party.case_id):
            if stored_party.case_party_id == party.case_party_id:
                return CasePartyResult(
                    party=stored_party,
                    event=build_case_party_registered_event(
                        event_id=resolved_event_id,
                        party=stored_party,
                        actor=context.actor,
                        correlation_id=context.correlation_id,
                        causation_id=None,
                        occurred_at=existing_audit.occurred_at,
                    ),
                    audit_event=existing_audit,
                )
        raise ComplianceCommandConflictError(
            f"idempotent replay for event_id {resolved_event_id} found no case party"
        )

    now = clock.now()
    stored = party_store.append(party)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="case_party.registered",
        occurred_at=now,
        context=context,
        target_type="case_party",
        target_id=stored.case_party_id,
        action="register_case_party",
        reason_code=_PARTY_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(
            {
                "case_party_id": str(stored.case_party_id),
                "case_id": str(stored.case_id),
                "organization_id": str(stored.organization_id),
                "party_reference": str(stored.party_reference),
                "role": stored.role.value,
                "registered_at": stored.registered_at.isoformat(),
                "is_authorized_service_recipient": stored.is_authorized_service_recipient,
            }
        ),
        clock=clock,
    )
    return CasePartyResult(
        party=stored,
        event=build_case_party_registered_event(
            event_id=resolved_event_id,
            party=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def _representation_state_payload(mandate: RepresentationMandate) -> dict[str, object]:
    return {
        "mandate_id": str(mandate.mandate_id),
        "case_id": str(mandate.case_id),
        "organization_id": str(mandate.organization_id),
        "represented_party_reference": str(mandate.represented_party_reference),
        "representative_reference": str(mandate.representative_reference),
        "authorities": sorted(authority.value for authority in mandate.authorities),
        "status": mandate.status.value,
        "valid_from": mandate.valid_from.isoformat(),
        "valid_until": mandate.valid_until.isoformat() if mandate.valid_until else None,
        "revoked_at": mandate.revoked_at.isoformat() if mandate.revoked_at else None,
        "revocation_reason_code": mandate.revocation_reason_code,
        "mandate_basis_reference": mandate.mandate_basis_reference,
    }


def register_representation(
    case_store: LegalCaseStore,
    representation_store: RepresentationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    mandate: RepresentationMandate,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> RepresentationResult:
    """Register a representation mandate with its enumerated authorities.

    A mandate is a *set of authorities*, not a role name. Framework hard
    invariant 15: a role name is not proof of authority - so nothing
    downstream may infer "this representative can settle" from the fact
    that a representative exists."""
    case, caller_organization_id = _load_legal_case(case_store, context, mandate.case_id)
    _require_legal_case_open(case)
    if mandate.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a representation mandate must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = representation_store.get(mandate.mandate_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no mandate"
            )
        return RepresentationResult(
            mandate=stored,
            event=build_representation_registered_event(
                event_id=resolved_event_id,
                mandate=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = representation_store.save(mandate)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="representation.registered",
        occurred_at=now,
        context=context,
        target_type="representation_mandate",
        target_id=stored.mandate_id,
        action="register_representation",
        reason_code=_REPRESENTATION_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(_representation_state_payload(stored)),
        clock=clock,
    )
    return RepresentationResult(
        mandate=stored,
        event=build_representation_registered_event(
            event_id=resolved_event_id,
            mandate=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def revoke_representation(
    representation_store: RepresentationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    mandate_id: UUID,
    reason_code: str,
    clock: Clock,
    event_id: UUID | None = None,
) -> RepresentationResult:
    """Revoke a mandate from now on.

    Revocation is forward-looking only. Filings already accepted under the
    mandate stay valid: the mandate was effective when they were made, and
    rewriting that would be rewriting the docket."""
    caller_organization_id = _require_scope(context)
    mandate = representation_store.get(mandate_id)
    if mandate is None or mandate.organization_id != caller_organization_id:
        _raise_not_found("representation mandate", mandate_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = representation_store.get(mandate_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("representation mandate", mandate_id)
        return RepresentationResult(
            mandate=stored,
            event=build_representation_revoked_event(
                event_id=resolved_event_id,
                mandate=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    before = _state_hash(_representation_state_payload(mandate))
    stored = representation_store.save(mandate.revoke(now, reason_code=reason_code))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="representation.revoked",
        occurred_at=now,
        context=context,
        target_type="representation_mandate",
        target_id=stored.mandate_id,
        action="revoke_representation",
        reason_code=_REPRESENTATION_AUDIT,
        before_hash=before,
        after_hash=_state_hash(_representation_state_payload(stored)),
        clock=clock,
    )
    return RepresentationResult(
        mandate=stored,
        event=build_representation_revoked_event(
            event_id=resolved_event_id,
            mandate=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Filings and the immutable docket
# ---------------------------------------------------------------------------


def receive_filing(
    case_store: LegalCaseStore,
    filing_store: FilingStore,
    representation_store: RepresentationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    filing: Filing,
    clock: Clock,
    event_id: UUID | None = None,
) -> FilingResult:
    """Append a filing to the case docket.

    The docket sequence is assigned by the store, never by the caller: a
    caller-chosen sequence would let two filings claim the same position
    or let a later filing be inserted before an earlier one. A
    caller-supplied sequence that disagrees with the store's next
    position is refused with `FILING_SEQUENCE_CONFLICT` rather than
    silently corrected.

    When the filing is made by a representative, the mandate is checked
    for the `FILE_SUBMISSIONS` authority at `received_at` - so an expired
    or revoked mandate produces a distinct, named refusal instead of a
    filing that quietly enters the record."""
    case, caller_organization_id = _load_legal_case(case_store, context, filing.case_id)
    _require_legal_case_open(case)
    if filing.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError("a filing must belong to the caller's own organization")
    if filing.filed_by_representative_reference is not None:
        mandate = _resolve_representation(
            representation_store,
            case_id=filing.case_id,
            represented_party_reference=filing.filed_by_party_reference,
            representative_reference=filing.filed_by_representative_reference,
        )
        mandate.assert_permits(RepresentationAuthority.FILE_SUBMISSIONS, at=filing.received_at)

    expected_sequence = filing_store.next_sequence(filing.case_id)
    if filing.docket_sequence != expected_sequence:
        raise FilingSequenceConflictError(
            f"the next docket position for case {filing.case_id} is {expected_sequence}, "
            f"not {filing.docket_sequence}"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = filing_store.get_in_scope(filing.filing_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no filing"
            )
        return FilingResult(
            filing=stored,
            event=build_filing_received_event(
                event_id=resolved_event_id,
                filing=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = filing_store.append(filing)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="filing.received",
        occurred_at=now,
        context=context,
        target_type="filing",
        target_id=stored.filing_id,
        action="receive_filing",
        reason_code=_FILING_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(filing_full_state_payload(stored)),
        clock=clock,
    )
    return FilingResult(
        filing=stored,
        event=build_filing_received_event(
            event_id=resolved_event_id,
            filing=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def _resolve_representation(
    representation_store: RepresentationStore,
    *,
    case_id: UUID,
    represented_party_reference: UUID,
    representative_reference: UUID,
) -> RepresentationMandate:
    for mandate in representation_store.list_for_case(case_id):
        if (
            mandate.represented_party_reference == represented_party_reference
            and mandate.representative_reference == representative_reference
        ):
            return mandate
    raise RepresentationInvalidError(
        f"no representation mandate links this representative to the party on case {case_id}"
    )


def decide_filing_admissibility(
    filing_store: FilingStore,
    recusal_store: RecusalStore,
    case_store: LegalCaseStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    filing_id: UUID,
    admit: bool,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> FilingResult:
    """Admit or reject a received filing.

    Receipt and admission are separate facts and a rejected filing is not
    removed: it stays on the docket at its original sequence, in
    `rejected` state, carrying its reason code. "This was filed and
    refused" is itself part of the record."""
    caller_organization_id = _require_scope(context)
    filing = filing_store.get_in_scope(filing_id, caller_organization_id)
    if filing is None:
        _raise_not_found("filing", filing_id)
    case, _ = _load_legal_case(case_store, context, filing.case_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = filing_store.get_in_scope(filing_id, caller_organization_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("filing", filing_id)
        return FilingResult(
            filing=stored,
            event=build_filing_admissibility_decided_event(
                event_id=resolved_event_id,
                filing=stored,
                reason_code=reason_code,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    _guard_acting_authority(
        recusal_store, case=case, acting_party_reference=acting_authority_reference, at=now
    )
    before = _state_hash(filing_full_state_payload(filing))
    decided = filing.admit() if admit else filing.reject(reason_code=reason_code)
    stored = filing_store.update_intake(decided)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="filing.admissibility_decided",
        occurred_at=now,
        context=context,
        target_type="filing",
        target_id=stored.filing_id,
        action="decide_filing_admissibility",
        reason_code=_FILING_AUDIT,
        before_hash=before,
        after_hash=_state_hash(filing_full_state_payload(stored)),
        clock=clock,
    )
    return FilingResult(
        filing=stored,
        event=build_filing_admissibility_decided_event(
            event_id=resolved_event_id,
            filing=stored,
            reason_code=reason_code,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def supersede_filing(
    filing_store: FilingStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    filing_id: UUID,
    successor_filing_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> FilingResult:
    """Point a filing at the filing that replaces it.

    Correction is supersession, not mutation. The superseded filing keeps
    its docket sequence, its timestamps and its document references; the
    store's `update_intake` compares every immutable field and refuses a
    save that changed any of them."""
    caller_organization_id = _require_scope(context)
    filing = filing_store.get_in_scope(filing_id, caller_organization_id)
    if filing is None:
        _raise_not_found("filing", filing_id)
    successor = filing_store.get_in_scope(successor_filing_id, caller_organization_id)
    if successor is None:
        _raise_not_found("filing", successor_filing_id)
    if successor.case_id != filing.case_id:
        raise FilingSequenceConflictError(
            "a filing can only be superseded by a filing on the same case"
        )
    if successor.docket_sequence <= filing.docket_sequence:
        raise FilingSequenceConflictError(
            "a superseding filing must occupy a later docket position"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = filing_store.get_in_scope(filing_id, caller_organization_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("filing", filing_id)
        return FilingResult(
            filing=stored,
            event=build_filing_superseded_event(
                event_id=resolved_event_id,
                filing=stored,
                successor_filing_id=successor_filing_id,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    before = _state_hash(filing_full_state_payload(filing))
    stored = filing_store.update_intake(filing.mark_superseded(successor_filing_id))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="filing.superseded",
        occurred_at=now,
        context=context,
        target_type="filing",
        target_id=stored.filing_id,
        action="supersede_filing",
        reason_code=_FILING_AUDIT,
        before_hash=before,
        after_hash=_state_hash(filing_full_state_payload(stored)),
        clock=clock,
    )
    return FilingResult(
        filing=stored,
        event=build_filing_superseded_event(
            event_id=resolved_event_id,
            filing=stored,
            successor_filing_id=successor_filing_id,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Hearings
# ---------------------------------------------------------------------------


def schedule_hearing(
    case_store: LegalCaseStore,
    hearing_store: HearingStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    hearing: Hearing,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> HearingResult:
    """Schedule a hearing on an open case."""
    case, caller_organization_id = _load_legal_case(case_store, context, hearing.case_id)
    _require_legal_case_open(case)
    if hearing.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError("a hearing must belong to the caller's own organization")
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = hearing_store.get_in_scope(hearing.hearing_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no hearing"
            )
        return HearingResult(
            hearing=stored,
            event=build_hearing_scheduled_event(
                event_id=resolved_event_id,
                hearing=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    _guard_acting_authority(
        recusal_store,
        case=case,
        acting_party_reference=hearing.convening_authority_reference,
        at=now,
    )
    stored = hearing_store.save(hearing)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="hearing.scheduled",
        occurred_at=now,
        context=context,
        target_type="hearing",
        target_id=stored.hearing_id,
        action="schedule_hearing",
        reason_code=_HEARING_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(hearing_full_state_payload(stored)),
        clock=clock,
    )
    return HearingResult(
        hearing=stored,
        event=build_hearing_scheduled_event(
            event_id=resolved_event_id,
            hearing=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


HearingTransitionFn = Callable[[Hearing, datetime], Hearing]


def _apply_hearing_transition(
    hearing_store: HearingStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hearing_id: UUID,
    transition: HearingTransitionFn,
    event_type: str,
    action: str,
    build: Callable[[UUID, Hearing, datetime], EventEnvelope],
    clock: Clock,
    event_id: UUID | None,
) -> HearingResult:
    """One transition path shared by reschedule/cancel/complete.

    Keeping the idempotency check, the audit hashes and the event build in
    a single place is what makes it impossible for one of the three
    transitions to quietly skip the audit append."""
    caller_organization_id = _require_scope(context)
    hearing = hearing_store.get_in_scope(hearing_id, caller_organization_id)
    if hearing is None:
        _raise_not_found("hearing", hearing_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = hearing_store.get_in_scope(hearing_id, caller_organization_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("hearing", hearing_id)
        return HearingResult(
            hearing=stored,
            event=build(resolved_event_id, stored, existing_audit.occurred_at),
            audit_event=existing_audit,
        )

    now = clock.now()
    before = _state_hash(hearing_full_state_payload(hearing))
    stored = hearing_store.save(transition(hearing, now))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type=event_type,
        occurred_at=now,
        context=context,
        target_type="hearing",
        target_id=stored.hearing_id,
        action=action,
        reason_code=_HEARING_AUDIT,
        before_hash=before,
        after_hash=_state_hash(hearing_full_state_payload(stored)),
        clock=clock,
    )
    return HearingResult(
        hearing=stored,
        event=build(resolved_event_id, stored, now),
        audit_event=audit_event,
    )


def reschedule_hearing(
    hearing_store: HearingStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hearing_id: UUID,
    new_scheduled_at: datetime,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> HearingResult:
    """Move a hearing.

    Rescheduling a hearing does **not** move any deadline attached to it.
    Framework hard invariant 60: a deadline changes only through its own
    governed decision, so a submissions deadline tied to a rescheduled
    hearing keeps running until somebody decides otherwise on the record."""
    return _apply_hearing_transition(
        hearing_store,
        audit_store,
        context,
        hearing_id=hearing_id,
        transition=lambda hearing, now: hearing.reschedule(
            now,
            new_scheduled_at=new_scheduled_at,
            reason_code=reason_code,
            actor_authority_reference=acting_authority_reference,
        ),
        event_type="hearing.rescheduled",
        action="reschedule_hearing",
        build=lambda resolved_event_id, hearing, occurred_at: build_hearing_rescheduled_event(
            event_id=resolved_event_id,
            hearing=hearing,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=occurred_at,
        ),
        clock=clock,
        event_id=event_id,
    )


def cancel_hearing(
    hearing_store: HearingStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hearing_id: UUID,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> HearingResult:
    return _apply_hearing_transition(
        hearing_store,
        audit_store,
        context,
        hearing_id=hearing_id,
        transition=lambda hearing, now: hearing.cancel(
            now,
            reason_code=reason_code,
            actor_authority_reference=acting_authority_reference,
        ),
        event_type="hearing.cancelled",
        action="cancel_hearing",
        build=lambda resolved_event_id, hearing, occurred_at: build_hearing_cancelled_event(
            event_id=resolved_event_id,
            hearing=hearing,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=occurred_at,
        ),
        clock=clock,
        event_id=event_id,
    )


def complete_hearing(
    hearing_store: HearingStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    hearing_id: UUID,
    reason_code: str,
    acting_authority_reference: UUID,
    minutes_reference: MinutesRef | None = None,
    clock: Clock,
    event_id: UUID | None = None,
) -> HearingResult:
    """Complete a hearing, optionally pointing at its minutes.

    `minutes_reference` is a `MinutesRef` placeholder: PACK-09 records
    that minutes exist and where, never their content (Framework 13.2)."""
    return _apply_hearing_transition(
        hearing_store,
        audit_store,
        context,
        hearing_id=hearing_id,
        transition=lambda hearing, now: hearing.complete(
            now,
            reason_code=reason_code,
            actor_authority_reference=acting_authority_reference,
            minutes_reference=minutes_reference,
        ),
        event_type="hearing.completed",
        action="complete_hearing",
        build=lambda resolved_event_id, hearing, occurred_at: build_hearing_completed_event(
            event_id=resolved_event_id,
            hearing=hearing,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=occurred_at,
        ),
        clock=clock,
        event_id=event_id,
    )


# ---------------------------------------------------------------------------
# Interim measures
# ---------------------------------------------------------------------------


def decide_interim_measure(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    measure_store: InterimMeasureStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    measure: InterimMeasure,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> InterimMeasureResult:
    """Grant, refuse or record an interim measure.

    Four gates, all structural rather than advisory:

    1. The case must be open and within a competent, unchallenged
       jurisdiction (`assert_may_decide_substantively`).
    2. The deciding authority must not be recused.
    3. `InterimMeasure.__post_init__` refuses to construct a *granted*
       measure unless `decided_by_actor_class` is
       `ActorClass.HUMAN_AUTHORITY` (Framework hard invariant 69).
    4. The same constructor requires an end or a review date and a
       reasons reference, so an indefinite unreasoned measure is not
       expressible."""
    case, caller_organization_id = _load_legal_case(case_store, context, measure.case_id)
    _require_legal_case_open(case)
    if measure.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "an interim measure must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = measure_store.get_in_scope(measure.measure_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no interim measure"
            )
        return InterimMeasureResult(
            measure=stored,
            event=build_interim_measure_decided_event(
                event_id=resolved_event_id,
                measure=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    assert_may_decide_substantively(
        case=case,
        jurisdiction=_effective_jurisdiction(jurisdiction_store, case),
        acting_authority_reference=measure.decided_by_authority_reference,
        at=now,
    )
    _guard_acting_authority(
        recusal_store,
        case=case,
        acting_party_reference=measure.decided_by_authority_reference,
        at=now,
    )
    stored = measure_store.save(measure)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="interim_measure.decided",
        occurred_at=now,
        context=context,
        target_type="interim_measure",
        target_id=stored.measure_id,
        action="decide_interim_measure",
        reason_code=_INTERIM_MEASURE_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(interim_measure_full_state_payload(stored)),
        clock=clock,
    )
    return InterimMeasureResult(
        measure=stored,
        event=build_interim_measure_decided_event(
            event_id=resolved_event_id,
            measure=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Procedural decisions: effect, finality and enforceability
# ---------------------------------------------------------------------------


def issue_procedural_decision(
    case_store: LegalCaseStore,
    jurisdiction_store: JurisdictionStore,
    decision_store: ProceduralDecisionStore,
    notice_effect_store: NoticeEffectStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    decision: ProceduralDecision,
    *,
    notice_effect_id: UUID | None,
    response_opportunity_given: bool,
    remedy_available: bool,
    decided_by_actor_class: ActorClass,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProceduralDecisionResult:
    """Issue a procedural decision.

    This is the command Framework hard invariant 52 is about: no
    consequential outcome without jurisdiction, notice, an opportunity to
    respond, a human decision, reasons and a remedy. All six are checked
    by `assert_due_process_complete`, and `notice_effect_id` is resolved
    against the notice-effect store rather than trusted - a caller cannot
    assert "notice was effective" by passing a flag.

    Issuance alone establishes neither effect, finality nor
    enforceability. Those are three separate later transitions."""
    case, caller_organization_id = _load_legal_case(case_store, context, decision.case_id)
    _require_legal_case_open(case)
    if decision.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a procedural decision must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = decision_store.get_in_scope(decision.decision_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no decision"
            )
        return ProceduralDecisionResult(
            decision=stored,
            event=build_procedural_decision_issued_event(
                event_id=resolved_event_id,
                decision=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    jurisdiction = _effective_jurisdiction(jurisdiction_store, case)
    assert_may_decide_substantively(
        case=case,
        jurisdiction=jurisdiction,
        acting_authority_reference=decision.deciding_authority_reference,
        at=now,
    )
    _guard_acting_authority(
        recusal_store,
        case=case,
        acting_party_reference=decision.decided_by_party_reference,
        at=now,
    )

    notice_effect_established = False
    if notice_effect_id is not None:
        effect = notice_effect_store.get_in_scope(notice_effect_id, caller_organization_id)
        if effect is None:
            _raise_not_found("notice effect decision", notice_effect_id)
        if effect.case_id != decision.case_id:
            raise CrossScopeAccessDeniedError(
                "the referenced notice effect belongs to a different case"
            )
        notice_effect_established = effect.establishes_legal_effect

    assert_due_process_complete(
        jurisdiction_confirmed=jurisdiction is not None
        and jurisdiction.permits_substantive_decision_at(now),
        notice_effect_established=notice_effect_established,
        response_opportunity_given=response_opportunity_given,
        decided_by_actor_class=decided_by_actor_class,
        reasons_reference=decision.reasons_reference,
        remedy_available=remedy_available,
    )

    stored = decision_store.save(decision)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_decision.issued",
        occurred_at=now,
        context=context,
        target_type="procedural_decision",
        target_id=stored.decision_id,
        action="issue_procedural_decision",
        reason_code=_DECISION_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(procedural_decision_full_state_payload(stored)),
        clock=clock,
    )
    return ProceduralDecisionResult(
        decision=stored,
        event=build_procedural_decision_issued_event(
            event_id=resolved_event_id,
            decision=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


DecisionTransitionFn = Callable[[ProceduralDecision, datetime], ProceduralDecision]


def _apply_decision_transition(
    decision_store: ProceduralDecisionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    decision_id: UUID,
    transition: DecisionTransitionFn,
    event_type: str,
    action: str,
    build: Callable[[UUID, ProceduralDecision, datetime], EventEnvelope],
    clock: Clock,
    event_id: UUID | None,
    expected_decision_version: int | None = None,
) -> ProceduralDecisionResult:
    caller_organization_id = _require_scope(context)
    decision = decision_store.get_in_scope(decision_id, caller_organization_id)
    if decision is None:
        _raise_not_found("procedural decision", decision_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = decision_store.get_in_scope(decision_id, caller_organization_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("procedural decision", decision_id)
        return ProceduralDecisionResult(
            decision=stored,
            event=build(resolved_event_id, stored, existing_audit.occurred_at),
            audit_event=existing_audit,
        )

    _check_expected_version(
        decision.decision_version, expected_decision_version, what="procedural decision"
    )
    now = clock.now()
    before = _state_hash(procedural_decision_full_state_payload(decision))
    stored = decision_store.save(transition(decision, now))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type=event_type,
        occurred_at=now,
        context=context,
        target_type="procedural_decision",
        target_id=stored.decision_id,
        action=action,
        reason_code=_DECISION_AUDIT,
        before_hash=before,
        after_hash=_state_hash(procedural_decision_full_state_payload(stored)),
        clock=clock,
    )
    return ProceduralDecisionResult(
        decision=stored,
        event=build(resolved_event_id, stored, now),
        audit_event=audit_event,
    )


def change_decision_effect(
    decision_store: ProceduralDecisionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    decision_id: UUID,
    action: DecisionEffectAction,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
    expected_decision_version: int | None = None,
) -> ProceduralDecisionResult:
    """Commence, suspend or resume a decision's legal effect.

    Suspending effect also stays enforceability - a suspended decision
    that stayed enforceable would be exactly the failure mode Framework
    hard invariant 52 exists to prevent - and `ProceduralDecision`
    implements that coupling, so no caller can suspend one without the
    other."""

    def transition(decision: ProceduralDecision, now: datetime) -> ProceduralDecision:
        if action is DecisionEffectAction.COMMENCE:
            return decision.commence_effect(
                now,
                reason_code=reason_code,
                actor_authority_reference=acting_authority_reference,
            )
        if action is DecisionEffectAction.SUSPEND:
            return decision.suspend_effect(
                now,
                reason_code=reason_code,
                actor_authority_reference=acting_authority_reference,
            )
        return decision.resume_effect(
            now,
            reason_code=reason_code,
            actor_authority_reference=acting_authority_reference,
        )

    return _apply_decision_transition(
        decision_store,
        audit_store,
        context,
        decision_id=decision_id,
        transition=transition,
        event_type="procedural_decision.effect_changed",
        action=f"change_decision_effect:{action.value}",
        build=lambda resolved_event_id, decision, occurred_at: build_decision_effect_changed_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=occurred_at,
        ),
        clock=clock,
        event_id=event_id,
        expected_decision_version=expected_decision_version,
    )


def make_decision_final(
    decision_store: ProceduralDecisionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    decision_id: UUID,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
    expected_decision_version: int | None = None,
) -> ProceduralDecisionResult:
    """Record that the remedy window closed or was exhausted.

    Finality does not imply enforceability and this service never derives
    one from the other: `make_decision_enforceable` is a separate command
    with its own precondition."""
    return _apply_decision_transition(
        decision_store,
        audit_store,
        context,
        decision_id=decision_id,
        transition=lambda decision, now: decision.become_final(
            now, reason_code=reason_code, actor_authority_reference=acting_authority_reference
        ),
        event_type="procedural_decision.finality_changed",
        action="make_decision_final",
        build=lambda resolved_event_id, decision, occurred_at: (
            build_decision_finality_changed_event(
                event_id=resolved_event_id,
                decision=decision,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=occurred_at,
            )
        ),
        clock=clock,
        event_id=event_id,
        expected_decision_version=expected_decision_version,
    )


def make_decision_enforceable(
    decision_store: ProceduralDecisionStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    decision_id: UUID,
    reason_code: str,
    acting_authority_reference: UUID,
    clock: Clock,
    event_id: UUID | None = None,
    expected_decision_version: int | None = None,
) -> ProceduralDecisionResult:
    """Make a decision enforceable.

    Refuses with `DECISION_NOT_ENFORCEABLE` unless the decision is
    actually in effect. A final decision whose effect is suspended is not
    enforceable, and that combination is inexpressible here rather than
    merely discouraged."""
    return _apply_decision_transition(
        decision_store,
        audit_store,
        context,
        decision_id=decision_id,
        transition=lambda decision, now: decision.become_enforceable(
            now, reason_code=reason_code, actor_authority_reference=acting_authority_reference
        ),
        event_type="procedural_decision.enforceability_changed",
        action="make_decision_enforceable",
        build=lambda resolved_event_id, decision, occurred_at: (
            build_decision_enforceability_changed_event(
                event_id=resolved_event_id,
                decision=decision,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=occurred_at,
            )
        ),
        clock=clock,
        event_id=event_id,
        expected_decision_version=expected_decision_version,
    )


def register_remedy(
    decision_store: ProceduralDecisionStore,
    remedy_store: RemedyStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    remedy: Remedy,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> RemedyResult:
    """Attach an appeal/review route to a decision and bind the decision
    back to it."""
    caller_organization_id = _require_scope(context)
    decision = decision_store.get_in_scope(remedy.decision_id, caller_organization_id)
    if decision is None:
        _raise_not_found("procedural decision", remedy.decision_id)
    if remedy.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError("a remedy must belong to the caller's own organization")
    if remedy.case_id != decision.case_id:
        raise CrossScopeAccessDeniedError("a remedy must belong to its decision's case")
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = remedy_store.get_in_scope(remedy.remedy_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no remedy"
            )
        return RemedyResult(
            remedy=stored,
            event=build_remedy_registered_event(
                event_id=resolved_event_id,
                remedy=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = remedy_store.save(remedy)
    decision_store.save(decision.with_remedy(stored.remedy_id))
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="remedy.registered",
        occurred_at=now,
        context=context,
        target_type="remedy",
        target_id=stored.remedy_id,
        action="register_remedy",
        reason_code=_REMEDY_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(remedy_full_state_payload(stored)),
        clock=clock,
    )
    return RemedyResult(
        remedy=stored,
        event=build_remedy_registered_event(
            event_id=resolved_event_id,
            remedy=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Recusal and replacement
# ---------------------------------------------------------------------------


def record_recusal(
    case_store: LegalCaseStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    recusal: RecusalRecord,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> RecusalResult:
    """Record a conflict assessment outcome and, where it blocks, the
    recusal that follows from it.

    Two Framework invariants meet here. 53: recusal blocks capability
    without erasing history - `prior_participation_codes` stays on the
    record and nothing this command does removes the recused actor's
    earlier acts. 54: declarations are versioned, not overwritten - a
    superseding assessment names the one it supersedes rather than
    replacing it."""
    case, caller_organization_id = _load_legal_case(case_store, context, recusal.case_id)
    if recusal.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a recusal record must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        for stored_recusal in recusal_store.list_for_case(case.legal_case_id):
            if stored_recusal.recusal_id == recusal.recusal_id:
                return RecusalResult(
                    recusal=stored_recusal,
                    event=build_recusal_recorded_event(
                        event_id=resolved_event_id,
                        recusal=stored_recusal,
                        actor=context.actor,
                        correlation_id=context.correlation_id,
                        causation_id=None,
                        occurred_at=existing_audit.occurred_at,
                    ),
                    audit_event=existing_audit,
                )
        raise ComplianceCommandConflictError(
            f"idempotent replay for event_id {resolved_event_id} found no recusal record"
        )

    now = clock.now()
    stored = recusal_store.append(recusal)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="recusal.recorded",
        occurred_at=now,
        context=context,
        target_type="recusal_record",
        target_id=stored.recusal_id,
        action="record_recusal",
        reason_code=_RECUSAL_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(recusal_full_state_payload(stored)),
        clock=clock,
    )
    return RecusalResult(
        recusal=stored,
        event=build_recusal_recorded_event(
            event_id=resolved_event_id,
            recusal=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def assign_replacement(
    case_store: LegalCaseStore,
    recusal_store: RecusalStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    assignment: ReplacementAssignment,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> ReplacementResult:
    """Assign a replacement for a recused actor.

    Refuses if the replacement is themselves recused from this case -
    otherwise a recusal could be "resolved" by handing the matter to
    somebody equally conflicted."""
    case, caller_organization_id = _load_legal_case(case_store, context, assignment.case_id)
    if assignment.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a replacement assignment must belong to the caller's own organization"
        )
    recusals = recusal_store.list_for_case(case.legal_case_id)
    if not any(record.recusal_id == assignment.recusal_id for record in recusals):
        _raise_not_found("recusal record", assignment.recusal_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        for stored_assignment in recusal_store.list_replacements_for_case(case.legal_case_id):
            if stored_assignment.assignment_id == assignment.assignment_id:
                return ReplacementResult(
                    assignment=stored_assignment,
                    event=build_replacement_assigned_event(
                        event_id=resolved_event_id,
                        assignment=stored_assignment,
                        actor=context.actor,
                        correlation_id=context.correlation_id,
                        causation_id=None,
                        occurred_at=existing_audit.occurred_at,
                    ),
                    audit_event=existing_audit,
                )
        raise ComplianceCommandConflictError(
            f"idempotent replay for event_id {resolved_event_id} found no replacement assignment"
        )

    now = clock.now()
    assert_actor_not_recused(
        actor_party_reference=assignment.replacement_party_reference,
        recusals=recusals,
        at=assignment.assigned_at,
    )
    stored = recusal_store.append_replacement(assignment)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="replacement.assigned",
        occurred_at=now,
        context=context,
        target_type="replacement_assignment",
        target_id=stored.assignment_id,
        action="assign_replacement",
        reason_code=_RECUSAL_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(
            {
                "assignment_id": str(stored.assignment_id),
                "case_id": str(stored.case_id),
                "organization_id": str(stored.organization_id),
                "recusal_id": str(stored.recusal_id),
                "replacement_party_reference": str(stored.replacement_party_reference),
                "assigned_by_authority_reference": str(stored.assigned_by_authority_reference),
                "assigned_at": stored.assigned_at.isoformat(),
            }
        ),
        clock=clock,
    )
    return ReplacementResult(
        assignment=stored,
        event=build_replacement_assigned_event(
            event_id=resolved_event_id,
            assignment=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Official notice: the three-step trust boundary
# ---------------------------------------------------------------------------


def issue_official_notice(
    case_store: LegalCaseStore,
    notice_store: OfficialNoticeStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    notice: OfficialNotice,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> OfficialNoticeResult:
    """Create an authorized notice object.

    **Step 1 of 3.** Issuing a notice starts nothing: no deadline runs, no
    presumption applies and no legal effect exists. Framework hard
    invariant 40 requires an authorized object, a valid method, proof and
    a governed effect decision - this command supplies only the first."""
    case, caller_organization_id = _load_legal_case(case_store, context, notice.case_id)
    _require_legal_case_open(case)
    if notice.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "an official notice must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = notice_store.get_in_scope(notice.notice_id, caller_organization_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no notice"
            )
        return OfficialNoticeResult(
            notice=stored,
            event=build_notice_issued_event(
                event_id=resolved_event_id,
                notice=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = notice_store.save(notice)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="official_notice.issued",
        occurred_at=now,
        context=context,
        target_type="official_notice",
        target_id=stored.notice_id,
        action="issue_official_notice",
        reason_code=_NOTICE_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(official_notice_full_state_payload(stored)),
        clock=clock,
    )
    return OfficialNoticeResult(
        notice=stored,
        event=build_notice_issued_event(
            event_id=resolved_event_id,
            notice=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def record_service_attempt(
    notice_store: OfficialNoticeStore,
    attempt_store: ServiceAttemptStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    attempt: ServiceAttempt,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> ServiceAttemptResult:
    """Record one attempt to serve a notice, with its provider telemetry.

    **Step 2 of 3.** Still not a legal effect. The method is checked
    against the notice's `authorized_methods` here so that an attempt over
    an unauthorized channel is refused at recording time
    (`NOTICE_METHOD_INVALID`) rather than silently accumulating as
    evidence that later looks like proof of service."""
    caller_organization_id = _require_scope(context)
    notice = notice_store.get_in_scope(attempt.notice_id, caller_organization_id)
    if notice is None:
        _raise_not_found("official notice", attempt.notice_id)
    if attempt.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a service attempt must belong to the caller's own organization"
        )
    notice.assert_method_authorized(attempt.method)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        for stored_attempt in attempt_store.list_for_notice(attempt.notice_id):
            if stored_attempt.attempt_id == attempt.attempt_id:
                return ServiceAttemptResult(
                    attempt=stored_attempt,
                    event=build_service_attempt_recorded_event(
                        event_id=resolved_event_id,
                        attempt=stored_attempt,
                        actor=context.actor,
                        correlation_id=context.correlation_id,
                        causation_id=None,
                        occurred_at=existing_audit.occurred_at,
                    ),
                    audit_event=existing_audit,
                )
        raise ComplianceCommandConflictError(
            f"idempotent replay for event_id {resolved_event_id} found no service attempt"
        )

    now = clock.now()
    stored = attempt_store.append(attempt)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="service_attempt.recorded",
        occurred_at=now,
        context=context,
        target_type="service_attempt",
        target_id=stored.attempt_id,
        action="record_service_attempt",
        reason_code=_SERVICE_ATTEMPT_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(service_attempt_full_state_payload(stored)),
        clock=clock,
    )
    return ServiceAttemptResult(
        attempt=stored,
        event=build_service_attempt_recorded_event(
            event_id=resolved_event_id,
            attempt=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def reconcile_service_attempt(
    notice_store: OfficialNoticeStore,
    attempt_store: ServiceAttemptStore,
    context: RequestContext,
    *,
    notice_id: UUID,
    attempt_id: UUID,
    proof_package_reference: NoticeProofPackageRef,
) -> ServiceAttempt:
    """Mark an attempt reconciled against an evidence-grade proof package.

    Framework hard invariant 57: a provider's status is not an internal
    legal effect without validation and reconciliation. Until this runs,
    `determine_notice_effect` will not count the attempt as supporting any
    deemed-service rule, no matter what the provider reported."""
    caller_organization_id = _require_scope(context)
    notice = notice_store.get_in_scope(notice_id, caller_organization_id)
    if notice is None:
        _raise_not_found("official notice", notice_id)
    for attempt in attempt_store.list_for_notice(notice_id):
        if attempt.attempt_id == attempt_id:
            return attempt_store.save(
                attempt.reconcile(proof_package_reference=proof_package_reference)
            )
    _raise_not_found("service attempt", attempt_id)


def determine_service_effect(
    notice_store: OfficialNoticeStore,
    attempt_store: ServiceAttemptStore,
    effect_store: NoticeEffectStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    notice_id: UUID,
    deemed_service_rule: DeemedServiceRule,
    rule_reference: str,
    decided_by_authority_reference: UUID,
    effective_at: datetime,
    clock: Clock,
    event_id: UUID | None = None,
    effect_id: UUID | None = None,
) -> NoticeEffectResult:
    """Decide whether a notice took legal effect.

    **Step 3 of 3, and the only step that can.** The determination is
    delegated to `notices.determine_notice_effect`, which applies the
    ordered refusals, and the result is written through
    `NoticeEffectStore.create_once` - so a replayed command cannot
    manufacture a second legal effect for the same notice (Framework hard
    invariant 59)."""
    caller_organization_id = _require_scope(context)
    notice = notice_store.get_in_scope(notice_id, caller_organization_id)
    if notice is None:
        _raise_not_found("official notice", notice_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = effect_store.get_for_notice(notice_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no notice effect"
            )
        return NoticeEffectResult(
            decision=stored,
            event=build_notice_effect_determined_event(
                event_id=resolved_event_id,
                decision=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    determined = determine_notice_effect(
        effect_id=effect_id if effect_id is not None else generate_uuid(),
        notice=notice,
        attempts=attempt_store.list_for_notice(notice_id),
        deemed_service_rule=deemed_service_rule,
        rule_reference=rule_reference,
        decided_at=now,
        decided_by_authority_reference=decided_by_authority_reference,
        effective_at=effective_at,
        existing_effect=effect_store.get_for_notice(notice_id),
    )
    stored = effect_store.create_once(determined)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="notice_effect.determined",
        occurred_at=now,
        context=context,
        target_type="notice_effect_decision",
        target_id=stored.effect_id,
        action="determine_service_effect",
        reason_code=_NOTICE_EFFECT_AUDIT,
        before_hash=_state_hash(official_notice_full_state_payload(notice)),
        after_hash=_state_hash(notice_effect_full_state_payload(stored)),
        clock=clock,
    )
    return NoticeEffectResult(
        decision=stored,
        event=build_notice_effect_determined_event(
            event_id=resolved_event_id,
            decision=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def trigger_procedural_deadline(
    deadline_store: ProceduralDeadlineStore,
    effect_store: NoticeEffectStore,
    trigger_store: DeadlineTriggerStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    deadline_id: UUID,
    source: TriggerSource,
    notice_effect_id: UUID | None,
    source_reference: str,
    clock: Clock,
    event_id: UUID | None = None,
    trigger_id: UUID | None = None,
) -> DeadlineTriggerResult:
    """Record the governed trigger that started a deadline.

    Two refusals that exist specifically because of the Framework:

    - `assert_trigger_is_governed` rejects
      `TriggerSource.DELIVERY_TELEMETRY` and
      `TriggerSource.READ_TELEMETRY` **by name**. Those members exist in
      the enum precisely so the refusal is explicit rather than an
      omission (hard invariant 39).
    - `assert_no_duplicate_legal_effect` plus the trigger store's
      `create_once` mean a replay cannot start the same deadline twice
      from the same notice effect (hard invariant 59).

    An outage does not reach this command at all: a deadline whose
    infrastructure was unavailable is suspended and resumed through
    `suspend_deadline` / `resume_deadline`, each of which records its own
    reason code (hard invariant 60)."""
    caller_organization_id = _require_scope(context)
    deadline = deadline_store.get_in_scope(deadline_id, caller_organization_id)
    if deadline is None:
        _raise_not_found("procedural deadline", deadline_id)

    effect: NoticeEffectDecision | None = None
    if notice_effect_id is not None:
        effect = effect_store.get_in_scope(notice_effect_id, caller_organization_id)
        if effect is None:
            _raise_not_found("notice effect decision", notice_effect_id)
    assert_trigger_is_governed(source, effect=effect, case_id=deadline.case_id)
    if effect is not None:
        assert_no_duplicate_legal_effect(
            existing_triggers=trigger_store.list_for_case(deadline.case_id),
            notice_effect_id=effect.effect_id,
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = trigger_store.get_for_deadline(deadline_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no deadline trigger"
            )
        return DeadlineTriggerResult(
            trigger=stored,
            event=build_deadline_triggered_event(
                event_id=resolved_event_id,
                trigger=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = trigger_store.create_once(
        DeadlineTrigger(
            trigger_id=trigger_id if trigger_id is not None else generate_uuid(),
            deadline_id=deadline_id,
            case_id=deadline.case_id,
            organization_id=caller_organization_id,
            source=source,
            triggered_at=now,
            notice_effect_id=effect.effect_id if effect is not None else None,
            source_reference=source_reference,
        )
    )
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="procedural_deadline.triggered",
        occurred_at=now,
        context=context,
        target_type="procedural_deadline",
        target_id=deadline_id,
        action="trigger_procedural_deadline",
        reason_code=_DEADLINE_TRIGGER_AUDIT,
        before_hash=_state_hash(procedural_deadline_full_state_payload(deadline)),
        after_hash=_state_hash(deadline_trigger_full_state_payload(stored)),
        clock=clock,
    )
    return DeadlineTriggerResult(
        trigger=stored,
        event=build_deadline_triggered_event(
            event_id=resolved_event_id,
            trigger=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Records classification and Legal Hold propagation
# ---------------------------------------------------------------------------


def register_record_class(
    record_class_store: RecordClassStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    record_class: RecordClass,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> RecordClassResult:
    """Register a record class: category, sensitivity, data
    classification, custodian, disposition authority, retention schedule
    and search/export eligibility, as one versioned object.

    `RecordClass.__post_init__` refuses to let the record owner also be
    the disposition authority - separating who owns a record from who may
    authorize destroying it is the whole point of the class."""
    caller_organization_id = _require_scope(context)
    _require_entity_scope(record_class.organization_id, what="record class")
    if record_class.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a record class may only be registered inside the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = record_class_store.get_in_scope(
            record_class.record_class_id, caller_organization_id
        )
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no record class"
            )
        return RecordClassResult(
            record_class=stored,
            event=build_record_class_registered_event(
                event_id=resolved_event_id,
                record_class=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = record_class_store.save(record_class)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="record_class.registered",
        occurred_at=now,
        context=context,
        target_type="record_class",
        target_id=stored.record_class_id,
        action="register_record_class",
        reason_code=_RECORD_CLASS_AUDIT,
        before_hash=_NO_PRIOR_STATE,
        after_hash=_state_hash(record_class_full_state_payload(stored)),
        clock=clock,
    )
    return RecordClassResult(
        record_class=stored,
        event=build_record_class_registered_event(
            event_id=resolved_event_id,
            record_class=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def register_hold_propagation(
    hold_store: LegalHoldStore,
    propagation_store: HoldPropagationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    propagation: HoldPropagationRecord,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> HoldPropagationResult:
    """Record how far a Legal Hold has actually reached.

    A hold that exists on the primary record but has not reached a
    replica, index or export is not an effective hold. Recording
    `PropagationState.UNKNOWN`, `PENDING` or `FAILED` is what lets
    `assert_hold_propagation_resolved` block destruction - so an honest
    "we do not know" is more useful here than an optimistic silence."""
    caller_organization_id = _require_scope(context)
    hold = hold_store.get_in_scope(propagation.hold_id, caller_organization_id)
    if hold is None:
        _raise_not_found("legal hold", propagation.hold_id)
    if propagation.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a hold propagation record must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        for stored_record in propagation_store.list_for_hold(propagation.hold_id):
            if stored_record.propagation_id == propagation.propagation_id:
                return HoldPropagationResult(
                    propagation=stored_record,
                    event=build_hold_propagation_registered_event(
                        event_id=resolved_event_id,
                        propagation=stored_record,
                        actor=context.actor,
                        correlation_id=context.correlation_id,
                        causation_id=None,
                        occurred_at=existing_audit.occurred_at,
                    ),
                    audit_event=existing_audit,
                )
        raise ComplianceCommandConflictError(
            f"idempotent replay for event_id {resolved_event_id} found no propagation record"
        )

    now = clock.now()
    stored = propagation_store.save(propagation)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="legal_hold.propagation_registered",
        occurred_at=now,
        context=context,
        target_type="legal_hold",
        target_id=stored.hold_id,
        action="register_hold_propagation",
        reason_code=_HOLD_PROPAGATION_AUDIT,
        before_hash=_state_hash(legal_hold_full_state_payload(hold)),
        after_hash=_state_hash(hold_propagation_full_state_payload(stored)),
        clock=clock,
    )
    return HoldPropagationResult(
        propagation=stored,
        event=build_hold_propagation_registered_event(
            event_id=resolved_event_id,
            propagation=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def assert_destruction_propagation_resolved(
    record_store: GovernedRecordStore,
    hold_store: LegalHoldStore,
    propagation_store: HoldPropagationStore,
    context: RequestContext,
    *,
    record_id: UUID,
) -> None:
    """Refuse destruction while any hold that ever covered this record has
    an unresolved derivative.

    Deliberately a *separate* assertion rather than a change to
    `authorize_destruction`'s signature: PACK-09 round 1 already shipped
    that command and its callers, and widening a shipped command's
    required dependencies would be a breaking change for no gain. A caller
    that participates in hold propagation calls this first; a caller in a
    deployment with no derivatives at all has nothing to call it with.

    Note it checks every hold whose *scope* covers the record, including
    released ones - a hold released before its export copy was purged
    still leaves an unresolved derivative."""
    caller_organization_id = _require_scope(context)
    record = record_store.get_in_scope(record_id, caller_organization_id)
    if record is None:
        _raise_not_found("governed record", record_id)
    for hold in hold_store.list_for_organization(caller_organization_id):
        if not hold.covers(record):
            continue
        assert_hold_propagation_resolved(
            propagation_store.list_for_hold(hold.hold_id), hold_id=hold.hold_id
        )


# ---------------------------------------------------------------------------
# Data-protection governance and the DPIA gate
# ---------------------------------------------------------------------------


def determine_dpia_requirement(
    activity_store: ProcessingActivityStore,
    dpia_store: DPIAStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    determination: DPIARequirementDetermination,
    *,
    clock: Clock,
    event_id: UUID | None = None,
) -> DPIARequirementResult:
    """Record whether this processing activity requires a DPIA.

    The determination is recorded even when the answer is "no", because
    its *absence* is what blocks activation: `assert_activation_permitted`
    fails closed when no requirement determination exists at all, so
    "nobody ever asked" and "we asked and the answer was no" are different
    states with different outcomes."""
    caller_organization_id = _require_scope(context)
    activity = activity_store.get_in_scope(determination.activity_id, caller_organization_id)
    if activity is None:
        _raise_not_found("processing activity", determination.activity_id)
    if determination.organization_id != caller_organization_id:
        raise CrossScopeAccessDeniedError(
            "a DPIA requirement determination must belong to the caller's own organization"
        )
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = dpia_store.get_requirement(determination.activity_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no determination"
            )
        return DPIARequirementResult(
            determination=stored,
            event=build_dpia_requirement_determined_event(
                event_id=resolved_event_id,
                determination=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    stored = dpia_store.save_requirement(determination)
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="dpia.requirement_determined",
        occurred_at=now,
        context=context,
        target_type="dpia_requirement_determination",
        target_id=stored.determination_id,
        action="determine_dpia_requirement",
        reason_code=_DPIA_AUDIT,
        before_hash=_state_hash(processing_activity_full_state_payload(activity)),
        after_hash=_state_hash(
            {
                "determination_id": str(stored.determination_id),
                "activity_id": str(stored.activity_id),
                "organization_id": str(stored.organization_id),
                "risk_class": stored.risk_class.value,
                "dpia_required": stored.dpia_required,
                "determined_at": stored.determined_at.isoformat(),
                "determined_by_party_reference": str(stored.determined_by_party_reference),
                "basis_reference": stored.basis_reference,
            }
        ),
        clock=clock,
    )
    return DPIARequirementResult(
        determination=stored,
        event=build_dpia_requirement_determined_event(
            event_id=resolved_event_id,
            determination=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def change_dpia_status(
    dpia_store: DPIAStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    dpia_id: UUID,
    target: DPIAStatus,
    approval_reference: str | None = None,
    outcome_reason_code: str | None = None,
    valid_until: datetime | None = None,
    controller_reference: UUID | None = None,
    process_owner_authority_reference: UUID | None = None,
    clock: Clock,
    event_id: UUID | None = None,
    expected_dpia_version: int | None = None,
) -> DPIAResult:
    """Move a DPIA through its lifecycle.

    When the target is `APPROVED` and both the controller and the process
    owner are supplied, `assert_dpo_independence` refuses an approval
    where the reviewer is the controller or the process owner. A DPIA
    signed off by the person who wants the processing is not a review."""
    caller_organization_id = _require_scope(context)
    dpia = dpia_store.get_in_scope(dpia_id, caller_organization_id)
    if dpia is None:
        _raise_not_found("data protection impact assessment", dpia_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = dpia_store.get_in_scope(dpia_id, caller_organization_id)
        if stored is None:  # pragma: no cover - resolved immediately above
            _raise_not_found("data protection impact assessment", dpia_id)
        return DPIAResult(
            dpia=stored,
            event=build_dpia_status_changed_event(
                event_id=resolved_event_id,
                dpia=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    _check_expected_version(
        dpia.dpia_version, expected_dpia_version, what="data protection impact assessment"
    )
    if (
        target is DPIAStatus.APPROVED
        and controller_reference is not None
        and process_owner_authority_reference is not None
    ):
        assert_dpo_independence(
            reviewer_party_reference=dpia.reviewer_party_reference,
            controller_reference=controller_reference,
            process_owner_authority_reference=process_owner_authority_reference,
        )

    now = clock.now()
    before = _state_hash(dpia_full_state_payload(dpia))
    stored = dpia_store.save(
        dpia.with_status(
            target,
            now,
            approval_reference=approval_reference,
            outcome_reason_code=outcome_reason_code,
            valid_until=valid_until,
        )
    )
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="dpia.status_changed",
        occurred_at=now,
        context=context,
        target_type="data_protection_impact_assessment",
        target_id=stored.dpia_id,
        action="change_dpia_status",
        reason_code=_DPIA_AUDIT,
        before_hash=before,
        after_hash=_state_hash(dpia_full_state_payload(stored)),
        clock=clock,
    )
    return DPIAResult(
        dpia=stored,
        event=build_dpia_status_changed_event(
            event_id=resolved_event_id,
            dpia=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )


def decide_processing_activation(
    activity_store: ProcessingActivityStore,
    dpia_store: DPIAStore,
    activation_store: ProcessingActivationStore,
    audit_store: AuditEventStore,
    context: RequestContext,
    *,
    activity_id: UUID,
    risk_class: ProcessingRiskClass,
    decided_by_authority_reference: UUID,
    reason_code: str,
    effective_from: datetime | None = None,
    clock: Clock,
    event_id: UUID | None = None,
    activation_decision_id: UUID | None = None,
) -> ProcessingActivationResult:
    """Activate a processing activity - or record, with a reason, that it
    was blocked.

    `assert_activation_permitted` runs the four-step gate before anything
    is written: risk class -> requirement determination exists -> DPIA
    exists where required -> DPIA is activating *at this instant*. A
    refusal propagates as `DPIA_REQUIRED`, `DPIA_NOT_APPROVED` or
    `PROCESSING_ACTIVATION_BLOCKED`, and nothing is stored - the caller
    does not get a half-activated activity."""
    caller_organization_id = _require_scope(context)
    activity = activity_store.get_in_scope(activity_id, caller_organization_id)
    if activity is None:
        _raise_not_found("processing activity", activity_id)
    resolved_event_id = _resolved_event_id(event_id)

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        stored = activation_store.get_for_activity(activity_id)
        if stored is None:
            raise ComplianceCommandConflictError(
                f"idempotent replay for event_id {resolved_event_id} found no activation decision"
            )
        return ProcessingActivationResult(
            decision=stored,
            event=build_processing_activation_decided_event(
                event_id=resolved_event_id,
                decision=stored,
                actor=context.actor,
                correlation_id=context.correlation_id,
                causation_id=None,
                occurred_at=existing_audit.occurred_at,
            ),
            audit_event=existing_audit,
        )

    now = clock.now()
    dpia = dpia_store.get_for_activity(activity_id)
    assert_activation_permitted(
        risk_class=risk_class,
        requirement=dpia_store.get_requirement(activity_id),
        dpia=dpia,
        at=now,
    )
    stored = activation_store.save(
        ProcessingActivationDecision(
            activation_decision_id=(
                activation_decision_id if activation_decision_id is not None else generate_uuid()
            ),
            activity_id=activity_id,
            organization_id=caller_organization_id,
            state=ProcessingActivationState.ACTIVATED,
            decided_at=now,
            decided_by_authority_reference=decided_by_authority_reference,
            reason_code=reason_code,
            dpia_id=dpia.dpia_id if dpia is not None else None,
            effective_from=effective_from if effective_from is not None else now,
        )
    )
    audit_event = _append_audit(
        audit_store,
        audit_event_id=resolved_event_id,
        event_type="processing_activity.activation_decided",
        occurred_at=now,
        context=context,
        target_type="processing_activation_decision",
        target_id=stored.activation_decision_id,
        action="decide_processing_activation",
        reason_code=_ACTIVATION_AUDIT,
        before_hash=_state_hash(processing_activity_full_state_payload(activity)),
        after_hash=_state_hash(processing_activation_full_state_payload(stored)),
        clock=clock,
    )
    return ProcessingActivationResult(
        decision=stored,
        event=build_processing_activation_decided_event(
            event_id=resolved_event_id,
            decision=stored,
            actor=context.actor,
            correlation_id=context.correlation_id,
            causation_id=None,
            occurred_at=now,
        ),
        audit_event=audit_event,
    )
