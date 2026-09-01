"""Eligibility Service application layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_credential_service.application import issue_participation_credential
from epd2_eligibility_service.domain import (
    AgeThreshold,
    AssemblyDecision,
    AssemblyDecisionStatus,
    AssuranceRequirement,
    AtomicCapabilityResult,
    CriticalPolicyActivationGate,
    CriticalPolicyStatus,
    DigitalDecision,
    DigitalDecisionStatus,
    EligibilityDecision,
    EligibilityDecisionValue,
    EligibilityRule,
    EligibilitySnapshot,
    MembershipLayerClaims,
    ObservedAuthenticationState,
    ParticipantEligibilityPolicy,
    ProcessEligibilityClaims,
    ProcessEligibilityPolicy,
    StepUpAuthenticationRequirement,
    assert_assembly_decision_transition_allowed,
    assert_critical_policy_activation_gate,
    check_atomic_capability,
    check_step_up_requirement,
    compute_snapshot_digest,
)
from epd2_eligibility_service.events import (
    assembly_decision_state_payload,
    build_evaluated_event,
    build_formal_confirmation_recorded_event,
    build_formal_confirmation_requested_event,
    build_participation_rights_derived_event,
    build_snapshot_created_event,
    decision_state_payload,
    digital_decision_state_payload,
    snapshot_state_payload,
)
from epd2_eligibility_service.exceptions import (
    StepUpAuthenticationNotSatisfiedError,
    UnknownAssemblyDecisionError,
    UnknownDigitalDecisionError,
    UnknownEligibilityRuleError,
    UnknownParticipantEligibilityPolicyError,
    UnknownProcessEligibilityPolicyError,
    UnknownStepUpAuthenticationRequirementError,
)
from epd2_eligibility_service.storage import (
    AssemblyDecisionStore,
    DigitalDecisionStore,
    EligibilityDecisionStore,
    EligibilityRuleStore,
    EligibilitySnapshotStore,
    ParticipantEligibilityPolicyStore,
    ProcessEligibilityPolicyStore,
    StepUpAuthenticationRequirementStore,
)
from epd2_governance_service.application import verify_decision_authorizes_policy_activation

#: Audit Core's own policy version for entries this service appends -
#: independent of the wire event schema version.
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "eligibility-service"

#: Audit reason_code by decision outcome, for `evaluate_eligibility`
#: (ADR-004). `_decide()` below only ever returns ELIGIBLE, NOT_ELIGIBLE,
#: or MANUAL_REVIEW_REQUIRED - PENDING/EXPIRED are structurally part of
#: canon's decision-value enum (section 9.2) for a future pack's use
#: (e.g. a batch re-evaluation job), not reachable from this service's own
#: evaluation path today.
_AUDIT_REASON_FOR_DECISION: dict[EligibilityDecisionValue, str] = {
    EligibilityDecisionValue.ELIGIBLE: "ELIGIBILITY_MET",
    EligibilityDecisionValue.NOT_ELIGIBLE: "ELIGIBILITY_NOT_MET",
    EligibilityDecisionValue.MANUAL_REVIEW_REQUIRED: "ELIGIBILITY_PENDING",
    EligibilityDecisionValue.PENDING: "ELIGIBILITY_PENDING",
}
#: Fail-closed fallback (INV-10) if a decision value reaches the audit
#: call with no explicit mapping above (e.g. EXPIRED, from a future
#: batch process) - flags it as an integrity concern rather than
#: guessing a reason code silently.
_AUDIT_REASON_FALLBACK = "INTEGRITY_CHECK_FAILED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision: EligibilityDecision
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SnapshotResult:
    snapshot: EligibilitySnapshot
    event: EventEnvelope
    audit_event: AuditEvent


def create_eligibility_rule(
    store: EligibilityRuleStore,
    *,
    eligibility_rule_id: UUID,
    rule_version: int,
    scope_type: str,
    scope_id: UUID,
    required_membership_status: str,
    required_verification_level: str,
    region_constraint: str | None,
    minimum_membership_age: int | None,
    exclusion_conditions: Sequence[str],
    valid_from: datetime,
    valid_until: datetime | None,
) -> EligibilityRule:
    """Create (or idempotently re-confirm) one immutable rule version.
    Canon defines no domain event for rule creation itself - only its
    later evaluation/snapshot outcomes are audited (section 20.3). Not
    wired to Audit Core for the same reason: Audit Core's idempotency key
    is the domain event's own `event_id` (`application.py` docstrings on
    the other three functions), and there is no domain event here to key
    off; the rule-freeze guarantee (CT-00-10) is independently enforced by
    `EligibilityRuleStore`'s own conflict detection, not by the audit
    trail."""
    rule = EligibilityRule(
        eligibility_rule_id=eligibility_rule_id,
        rule_version=rule_version,
        scope_type=scope_type,
        scope_id=scope_id,
        required_membership_status=required_membership_status,
        required_verification_level=required_verification_level,
        region_constraint=region_constraint,
        minimum_membership_age=minimum_membership_age,
        exclusion_conditions=tuple(exclusion_conditions),
        valid_from=valid_from,
        valid_until=valid_until,
    )
    return store.save(rule)


def _decide(
    rule: EligibilityRule, evaluated_claims: Mapping[str, str]
) -> tuple[EligibilityDecisionValue, tuple[str, ...]]:
    """Minimal, documented evaluation policy: compare `evaluated_claims`
    against the rule's required attestations. This is intentionally
    simple (no region/age/exclusion-condition matching logic beyond
    presence checks) - a full eligibility rules engine is a future pack's
    concern; PACK-02 only needs *a* correct, fail-closed decision path to
    exercise the rest of the flow (see docs/review/OPEN_QUESTIONS.md).
    """
    membership_status = evaluated_claims.get("membership_status")
    verification_level = evaluated_claims.get("verification_level")

    if membership_status is None or verification_level is None:
        return EligibilityDecisionValue.MANUAL_REVIEW_REQUIRED, ("ELIGIBILITY_PENDING",)

    if (
        membership_status == rule.required_membership_status
        and verification_level == rule.required_verification_level
    ):
        return EligibilityDecisionValue.ELIGIBLE, ()

    return EligibilityDecisionValue.NOT_ELIGIBLE, ("ELIGIBILITY_NOT_MET",)


def evaluate_eligibility(
    rule_store: EligibilityRuleStore,
    decision_store: EligibilityDecisionStore,
    audit_store: AuditEventStore,
    *,
    eligibility_rule_id: UUID,
    rule_version: int,
    subject_reference: UUID,
    process_id: UUID,
    evaluated_claims: Mapping[str, str],
    evaluator_version: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> DecisionResult:
    """Evaluate one subject against one frozen rule version and emit
    `eligibility.evaluated`. `evaluated_claims` is a plain string mapping
    supplied by the caller - this function never imports or references
    `IdentityRecord` (see README.md's boundary note)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to evaluate eligibility")

    rule = rule_store.get(eligibility_rule_id, rule_version)
    if rule is None:
        raise UnknownEligibilityRuleError(
            f"unknown rule {eligibility_rule_id} version {rule_version}"
        )

    decision_value, reason_codes = _decide(rule, evaluated_claims)
    now = clock.now()
    decision = EligibilityDecision(
        eligibility_decision_id=generate_uuid(),
        subject_reference=subject_reference,
        process_id=process_id,
        eligibility_rule_id=eligibility_rule_id,
        rule_version=rule_version,
        decision=decision_value,
        reason_codes=reason_codes,
        evaluated_at=now,
        expires_at=rule.valid_until,
        correlation_id=correlation_id,
        evaluator_version=evaluator_version,
        evaluated_claims=dict(evaluated_claims),
    )
    decision_store.save(decision)
    event = build_evaluated_event(
        event_id=generate_uuid(),
        decision=decision,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: evaluating eligibility is a critical action
    # regardless of outcome - a NOT_ELIGIBLE or PENDING decision matters
    # for governance just as much as an ELIGIBLE one.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="eligibility_decision",
            target_id=decision.eligibility_decision_id,
            action="evaluate",
            reason_code=_AUDIT_REASON_FOR_DECISION.get(decision_value, _AUDIT_REASON_FALLBACK),
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(decision_state_payload(decision)),
        ),
        clock=clock,
    )
    return DecisionResult(decision=decision, event=event, audit_event=audit_event)


def create_eligibility_snapshot(
    snapshot_store: EligibilitySnapshotStore,
    audit_store: AuditEventStore,
    *,
    eligibility_rule_id: UUID,
    rule_version: int,
    eligible_decisions: Sequence[EligibilityDecision],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> SnapshotResult:
    """Create an immutable snapshot from a set of `eligible` decisions,
    all against the same frozen rule version. Fail-closed if any supplied
    decision does not match that rule/version or is not `eligible`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an eligibility snapshot")

    for d in eligible_decisions:
        if d.eligibility_rule_id != eligibility_rule_id or d.rule_version != rule_version:
            raise ValueError(
                f"decision {d.eligibility_decision_id} does not match rule "
                f"{eligibility_rule_id} version {rule_version}"
            )
        if d.decision != EligibilityDecisionValue.ELIGIBLE:
            raise ValueError(
                f"decision {d.eligibility_decision_id} is not eligible "
                f"({d.decision.value}); only eligible decisions may enter a snapshot"
            )

    now = clock.now()
    decision_ids = tuple(d.eligibility_decision_id for d in eligible_decisions)
    digest = compute_snapshot_digest(
        eligibility_rule_id=eligibility_rule_id,
        rule_version=rule_version,
        created_at=now,
        eligible_decision_ids=decision_ids,
    )
    snapshot = EligibilitySnapshot(
        eligibility_snapshot_id=generate_uuid(),
        eligibility_rule_id=eligibility_rule_id,
        rule_version=rule_version,
        created_at=now,
        eligible_decision_ids=decision_ids,
        eligible_count=len(decision_ids),
        digest=digest,
    )
    snapshot_store.save(snapshot)
    event = build_snapshot_created_event(
        event_id=generate_uuid(),
        snapshot=snapshot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="eligibility_snapshot",
            target_id=snapshot.eligibility_snapshot_id,
            action="create_snapshot",
            reason_code="ELIGIBILITY_SNAPSHOT_CREATED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(snapshot_state_payload(snapshot)),
        ),
        clock=clock,
    )
    return SnapshotResult(snapshot=snapshot, event=event, audit_event=audit_event)


def get_eligibility_decision(
    decision_store: EligibilityDecisionStore,
    *,
    eligibility_decision_id: UUID,
) -> EligibilityDecision | None:
    """Plain, unaudited read of one `EligibilityDecision` by id.

    Added under ADR-008 ("PACK-03 to PACK-02 integration boundary"),
    which names `epd2_eligibility_service.application` (never
    `epd2_eligibility_service.storage`) as the only legitimate way a
    PACK-03 service (`initiative-service`) may read "eligibility
    decisions backing a support action". This is a pure lookup with no
    state change - no canonical event, no audit entry - mirroring
    `epd2_credential_service.application.validate_participation_credential`'s
    own precedent for a query that is not itself a domain command.
    """
    return decision_store.get(eligibility_decision_id)


def get_eligibility_snapshot(
    snapshot_store: EligibilitySnapshotStore,
    *,
    eligibility_snapshot_id: UUID,
) -> EligibilitySnapshot | None:
    """Plain, unaudited read of one `EligibilitySnapshot` by id.

    Added under ADR-008, which names `epd2_eligibility_service.application`
    as the only legitimate way a PACK-03 service (`voting-service`) may
    "freeze against a real EligibilitySnapshot" (canon section 9.1: "after
    opening a vote, the rule version used is frozen"). Pure lookup, no
    state change - same rationale as `get_eligibility_decision` above.
    """
    return snapshot_store.get(eligibility_snapshot_id)


# =============================================================================
# PACK-07 additions (canon 19d.4-19d.14, canon-0.6.0, ADR-026 through
# ADR-031). `governance_decision_store`/`identity_record_store`/
# `authentication_context_store`/`membership_*` passthrough parameters below
# are accepted as `Any` - the same convention `epd2_voting_service.
# application.invalidate_ballot` (ADR-017) and `epd2_ai_processing_service.
# application.review_ai_output` (ADR-022) already establish for a
# cross-pack store this module must never import the type of (`tests/
# repository/test_service_boundaries.py` allows `.application` imports
# only, never `.storage`/`.domain`).
# =============================================================================

_POLICY_AUDIT_POLICY_VERSION = "1.0"


def _verify_activation_gate(
    governance_decision_store: object,
    *,
    adopted_by_decision_id: UUID,
    signed_policy_digest_reference: str | None,
    transparency_log_commitment_reference: str | None,
) -> None:
    """Shared four-gate check (canon 19d.7) behind every `activate_*`
    function below. Raises fail-closed via
    `assert_critical_policy_activation_gate` when any gate fails."""
    authorization = verify_decision_authorizes_policy_activation(
        governance_decision_store,  # type: ignore[arg-type]
        governance_decision_id=adopted_by_decision_id,
    )
    gate = CriticalPolicyActivationGate(
        decision_authorized=authorization.authorized,
        multi_person_approval_met=authorization.multi_person_approval_met,
        signed_policy_digest_reference=signed_policy_digest_reference,
        transparency_log_commitment_reference=transparency_log_commitment_reference,
    )
    assert_critical_policy_activation_gate(gate)


def propose_participant_eligibility_policy(
    store: ParticipantEligibilityPolicyStore,
    *,
    policy_id: UUID,
    policy_version: int,
    scope_type: str | None,
    scope_id: UUID | None,
    effective_from: datetime | None,
    effective_until: datetime | None,
    adopted_by_decision_id: UUID,
    age_thresholds: Sequence[AgeThreshold] = (),
    citizenship_conditions: Sequence[Mapping[str, object]] = (),
    residence_conditions: Sequence[Mapping[str, object]] = (),
    exemptions: Sequence[Mapping[str, object]] = (),
    transitional_rules: Sequence[Mapping[str, object]] = (),
    supersedes_policy_id: UUID | None = None,
    signed_policy_digest_reference: str | None = None,
    transparency_log_commitment_reference: str | None = None,
) -> ParticipantEligibilityPolicy:
    """Create one immutable `draft` `ParticipantEligibilityPolicy` version
    (canon 19d.4). No canonical event/audit entry - canon defines none for
    proposal itself (mirroring `create_eligibility_rule`'s own precedent);
    `activate_participant_eligibility_policy` below is the audited,
    critical action."""
    policy = ParticipantEligibilityPolicy(
        policy_id=policy_id,
        policy_version=policy_version,
        status=CriticalPolicyStatus.DRAFT,
        scope_type=scope_type,
        scope_id=scope_id,
        effective_from=effective_from,
        effective_until=effective_until,
        adopted_by_decision_id=adopted_by_decision_id,
        age_thresholds=tuple(age_thresholds),
        citizenship_conditions=tuple(citizenship_conditions),
        residence_conditions=tuple(residence_conditions),
        exemptions=tuple(exemptions),
        transitional_rules=tuple(transitional_rules),
        supersedes_policy_id=supersedes_policy_id,
        signed_policy_digest_reference=signed_policy_digest_reference,
        transparency_log_commitment_reference=transparency_log_commitment_reference,
    )
    store.save(policy)
    return policy


def activate_participant_eligibility_policy(
    store: ParticipantEligibilityPolicyStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    policy_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> ParticipantEligibilityPolicy:
    """Transition a `draft` `ParticipantEligibilityPolicy` to `active`
    (canon 19d.7's four-gate rule). Fail-closed and audited - this is the
    critical, append-only activation record task 14 requires."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this policy")
    policy = store.get(policy_id)
    if policy is None:
        raise UnknownParticipantEligibilityPolicyError(f"unknown policy_id: {policy_id}")
    _verify_activation_gate(
        governance_decision_store,
        adopted_by_decision_id=policy.adopted_by_decision_id,
        signed_policy_digest_reference=policy.signed_policy_digest_reference,
        transparency_log_commitment_reference=policy.transparency_log_commitment_reference,
    )
    activated = policy.with_status(CriticalPolicyStatus.ACTIVE)
    store.save(activated)
    now = clock.now()
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type="eligibility.participant_eligibility_policy_activated",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="participant_eligibility_policy",
            target_id=policy_id,
            action="activate",
            reason_code="CRITICAL_POLICY_ACTIVATED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash({"policy_id": str(policy_id), "status": "active"}),
        ),
        clock=clock,
    )
    return activated


def propose_process_eligibility_policy(
    store: ProcessEligibilityPolicyStore,
    *,
    policy_id: UUID,
    policy_version: int,
    process_type: str,
    jurisdiction: str,
    scope_type: str | None,
    scope_id: UUID | None,
    adopted_by: UUID,
    eligible_citizenship_set: Sequence[str] = (),
    citizenship_rule_reference: str | None = None,
    residence_rule: Mapping[str, object] | None = None,
    habitual_residence_rule: Mapping[str, object] | None = None,
    minimum_age: int | None = None,
    active_electoral_eligibility_rule: Mapping[str, object] | None = None,
    passive_electoral_eligibility_rule: Mapping[str, object] | None = None,
    party_internal_voting_rule: Mapping[str, object] | None = None,
    party_office_candidacy_rule: Mapping[str, object] | None = None,
    effective_from: datetime | None = None,
    effective_until: datetime | None = None,
    legal_basis: str | None = None,
    supersedes_policy_id: UUID | None = None,
    signed_policy_digest_reference: str | None = None,
    transparency_log_commitment_reference: str | None = None,
    decision_effect: str = "advisory",
    formal_confirmation_required: bool = False,
    formal_confirmation_authority: str | None = None,
    secret_ballot_required: bool = False,
    permitted_participation_mode: Sequence[str] = (),
    required_assurance_level: AssuranceRequirement | None = None,
    accessibility_profile: str | None = None,
) -> ProcessEligibilityPolicy:
    """Create one immutable `draft` `ProcessEligibilityPolicy` version
    (canon 19d.5). No canonical event/audit entry - see
    `propose_participant_eligibility_policy`'s own rationale."""
    from epd2_eligibility_service.domain import DecisionEffect as _DecisionEffect

    policy = ProcessEligibilityPolicy(
        policy_id=policy_id,
        policy_version=policy_version,
        status=CriticalPolicyStatus.DRAFT,
        process_type=process_type,
        jurisdiction=jurisdiction,
        scope_type=scope_type,
        scope_id=scope_id,
        adopted_by=adopted_by,
        eligible_citizenship_set=tuple(eligible_citizenship_set),
        citizenship_rule_reference=citizenship_rule_reference,
        residence_rule=residence_rule,
        habitual_residence_rule=habitual_residence_rule,
        minimum_age=minimum_age,
        active_electoral_eligibility_rule=active_electoral_eligibility_rule,
        passive_electoral_eligibility_rule=passive_electoral_eligibility_rule,
        party_internal_voting_rule=party_internal_voting_rule,
        party_office_candidacy_rule=party_office_candidacy_rule,
        effective_from=effective_from,
        effective_until=effective_until,
        legal_basis=legal_basis,
        supersedes_policy_id=supersedes_policy_id,
        signed_policy_digest_reference=signed_policy_digest_reference,
        transparency_log_commitment_reference=transparency_log_commitment_reference,
        decision_effect=_DecisionEffect(decision_effect),
        formal_confirmation_required=formal_confirmation_required,
        formal_confirmation_authority=formal_confirmation_authority,
        secret_ballot_required=secret_ballot_required,
        permitted_participation_mode=tuple(permitted_participation_mode),
        required_assurance_level=required_assurance_level,
        accessibility_profile=accessibility_profile,
    )
    store.save(policy)
    return policy


def activate_process_eligibility_policy(
    store: ProcessEligibilityPolicyStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    policy_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> ProcessEligibilityPolicy:
    """Transition a `draft` `ProcessEligibilityPolicy` to `active`
    (canon 19d.7). See `activate_participant_eligibility_policy`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this policy")
    policy = store.get(policy_id)
    if policy is None:
        raise UnknownProcessEligibilityPolicyError(f"unknown policy_id: {policy_id}")
    _verify_activation_gate(
        governance_decision_store,
        adopted_by_decision_id=policy.adopted_by,
        signed_policy_digest_reference=policy.signed_policy_digest_reference,
        transparency_log_commitment_reference=policy.transparency_log_commitment_reference,
    )
    activated = policy.with_status(CriticalPolicyStatus.ACTIVE)
    store.save(activated)
    now = clock.now()
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type="eligibility.process_eligibility_policy_activated",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="process_eligibility_policy",
            target_id=policy_id,
            action="activate",
            reason_code="CRITICAL_POLICY_ACTIVATED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash({"policy_id": str(policy_id), "status": "active"}),
        ),
        clock=clock,
    )
    return activated


def resolve_process_eligibility_policy(
    store: ProcessEligibilityPolicyStore,
    *,
    process_type: str,
    jurisdiction: str,
    scope_type: str | None,
    scope_id: UUID | None,
    effective_date: datetime,
) -> ProcessEligibilityPolicy | None:
    """ADR-030 item 6's resolution procedure - plain, unaudited read of
    exactly one applicable `active` version, never a standing cache."""
    return store.resolve_for_evaluation(
        process_type=process_type,
        jurisdiction=jurisdiction,
        scope_type=scope_type,
        scope_id=scope_id,
        effective_date=effective_date,
    )


def propose_step_up_authentication_requirement(
    store: StepUpAuthenticationRequirementStore,
    *,
    requirement_id: UUID,
    requirement_version: int,
    action_code: str,
    required_authentication_context: str,
    assurance_requirement: AssuranceRequirement,
    fresh_authentication_required: bool,
    reauthentication_reason: str,
    maximum_authentication_age: timedelta | None = None,
    effective_from: datetime | None = None,
    effective_until: datetime | None = None,
    supersedes_requirement_id: UUID | None = None,
    signed_policy_digest_reference: str | None = None,
    transparency_log_commitment_reference: str | None = None,
) -> StepUpAuthenticationRequirement:
    """Create one immutable `draft` `StepUpAuthenticationRequirement`
    version (canon 19d.8)."""
    requirement = StepUpAuthenticationRequirement(
        requirement_id=requirement_id,
        requirement_version=requirement_version,
        status=CriticalPolicyStatus.DRAFT,
        action_code=action_code,
        required_authentication_context=required_authentication_context,
        assurance_requirement=assurance_requirement,
        fresh_authentication_required=fresh_authentication_required,
        reauthentication_reason=reauthentication_reason,
        maximum_authentication_age=maximum_authentication_age,
        effective_from=effective_from,
        effective_until=effective_until,
        supersedes_requirement_id=supersedes_requirement_id,
        signed_policy_digest_reference=signed_policy_digest_reference,
        transparency_log_commitment_reference=transparency_log_commitment_reference,
    )
    store.save(requirement)
    return requirement


def activate_step_up_authentication_requirement(
    store: StepUpAuthenticationRequirementStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    requirement_id: UUID,
    adopted_by_decision_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> StepUpAuthenticationRequirement:
    """Transition a `draft` `StepUpAuthenticationRequirement` to `active`
    (canon 19d.7). `adopted_by_decision_id` is supplied here rather than
    stored on the entity itself - canon 19d.8 names no such field on
    `StepUpAuthenticationRequirement`, unlike the two Policy entities."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this requirement")
    requirement = store.get(requirement_id)
    if requirement is None:
        raise UnknownStepUpAuthenticationRequirementError(
            f"unknown requirement_id: {requirement_id}"
        )
    _verify_activation_gate(
        governance_decision_store,
        adopted_by_decision_id=adopted_by_decision_id,
        signed_policy_digest_reference=requirement.signed_policy_digest_reference,
        transparency_log_commitment_reference=requirement.transparency_log_commitment_reference,
    )
    activated = requirement.with_status(CriticalPolicyStatus.ACTIVE)
    store.save(activated)
    now = clock.now()
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type="eligibility.step_up_authentication_requirement_activated",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="step_up_authentication_requirement",
            target_id=requirement_id,
            action="activate",
            reason_code="CRITICAL_POLICY_ACTIVATED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(
                {"requirement_id": str(requirement_id), "status": "active"}
            ),
        ),
        clock=clock,
    )
    return activated


def authenticate_step_up_for_action(
    store: StepUpAuthenticationRequirementStore,
    *,
    action_code: str,
    observed: ObservedAuthenticationState | None,
    evaluated_at: datetime,
) -> None:
    """Resolves the single active `StepUpAuthenticationRequirement` for
    `action_code` (ADR-030 item 7) and checks it against a caller-supplied
    `ObservedAuthenticationState` snapshot. Raises
    `StepUpAuthenticationNotSatisfiedError` fail-closed, including when no
    active requirement can be resolved at all - callers that already
    called `identity-service.application.check_authentication_step_up_satisfied`
    directly (ADR-027's actual cross-pack read boundary) do not need this
    wrapper; it exists for callers that already hold both the requirement
    and an `ObservedAuthenticationState` locally (e.g. tests, or a caller
    that pre-fetched both)."""
    requirement = store.resolve_for_action(action_code=action_code, effective_date=evaluated_at)
    if requirement is None:
        raise StepUpAuthenticationNotSatisfiedError(
            f"no active StepUpAuthenticationRequirement for action_code={action_code!r}"
        )
    check_step_up_requirement(requirement, observed, evaluated_at=evaluated_at)


def check_process_eligibility_atomic_capability(
    *, claim_met: bool, denial_reason_code: str
) -> AtomicCapabilityResult:
    """Application-layer passthrough to `domain.check_atomic_capability`
    (canon 19d.14) - the only authorization mechanism, alongside a scoped
    capability token, this pack's design permits (ADR-027's enforcement-
    mechanism decision). No event, no audit entry: a synchronous read, not
    a domain command."""
    return check_atomic_capability(claim_met=claim_met, denial_reason_code=denial_reason_code)


@dataclass(frozen=True, slots=True)
class ParticipationRightsDerivationResult:
    claims: ProcessEligibilityClaims
    event: EventEnvelope
    audit_event: AuditEvent
    credential_id: UUID | None


def derive_and_issue_scoped_capability_token(
    credential_store: object,
    audit_store: AuditEventStore,
    *,
    subject_reference: UUID,
    process_id: UUID,
    action_code: str,
    claims: ProcessEligibilityClaims,
    claim_met: bool,
    denial_reason_code: str,
    credential_id: UUID,
    credential_type: str,
    scope_type: str,
    scope_id: UUID,
    valid_from: datetime,
    expires_at: datetime,
    usage_limit: int | None,
    applicable_policy_version: int,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> ParticipationRightsDerivationResult:
    """Canon 19d.14's single-purpose scoped capability token mechanism:
    performs the atomic capability check for exactly one
    `(subject_reference, process_id, action_code)` question and, only if
    it is met, delegates to `credential-service.application.
    issue_participation_credential` (canon 10.1, reused unmodified - never
    duplicated) to mint one narrowly-scoped `ParticipationCredential`.
    Always emits `ParticipationRightsDerived` (canon 19d.14) - the
    participant-side capability derivation event - whether or not a token
    was actually issued, since the derivation itself (the atomic check)
    happened either way; `credential_id` on the result is `None` when the
    capability check failed.

    `credential_type` is a plain `str` (never `epd2_credential_service.
    domain.CredentialType` - this module may import `epd2_credential_service.
    application` only, never `.domain`, per `tests/repository/
    test_service_boundaries.py`); `credential-service.application.
    issue_participation_credential` itself validates it fail-closed.

    Never persists or exposes a `ParticipationRightsProfile` - only this
    one action's derived result is computed and returned (canon 19d.1/
    19d.14: internal, derived, non-authoritative, non-persisted)."""
    capability = check_atomic_capability(claim_met=claim_met, denial_reason_code=denial_reason_code)

    now = clock.now()
    issued_credential_id: UUID | None = None
    if capability.authorized:
        issue_result = issue_participation_credential(
            credential_store,  # type: ignore[arg-type]
            audit_store,
            credential_id=credential_id,
            credential_type=credential_type,
            scope_type=scope_type,
            scope_id=scope_id,
            valid_from=valid_from,
            expires_at=expires_at,
            usage_limit=usage_limit,
            rule_version=applicable_policy_version,
            eligibility_snapshot_digest=f"process-eligibility-policy-v{applicable_policy_version}",
            actor=actor,
            actor_is_authorized=actor_is_authorized,
            correlation_id=correlation_id,
            clock=clock,
        )
        issued_credential_id = issue_result.credential.credential_id

    event = build_participation_rights_derived_event(
        event_id=generate_uuid(),
        subject_reference=subject_reference,
        process_id=process_id,
        action_code=action_code,
        claims=claims,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="process_eligibility_claims",
            target_id=process_id,
            action="derive_participation_rights",
            reason_code=(
                "PARTICIPATION_RIGHTS_DERIVED" if capability.authorized else capability.reason_code
            )
            or "PARTICIPATION_RIGHTS_DERIVED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(
                {
                    "subject_reference": str(subject_reference),
                    "process_id": str(process_id),
                    "action_code": action_code,
                    "authorized": capability.authorized,
                }
            ),
        ),
        clock=clock,
    )
    return ParticipationRightsDerivationResult(
        claims=claims, event=event, audit_event=audit_event, credential_id=issued_credential_id
    )


@dataclass(frozen=True, slots=True)
class DigitalDecisionResult:
    digital_decision: DigitalDecision
    assembly_decision: AssemblyDecision | None
    event: EventEnvelope | None
    audit_event: AuditEvent


def record_digital_decision(
    digital_decision_store: DigitalDecisionStore,
    assembly_decision_store: AssemblyDecisionStore,
    audit_store: AuditEventStore,
    *,
    digital_decision_id: UUID,
    process_reference: Mapping[str, object],
    digital_result: str,
    decision_effect: str,
    formal_confirmation_required: bool,
    confirming_authority: str | None = None,
    legal_basis: str | None = None,
    confirmation_deadline: datetime | None = None,
    protocol_or_evidence_reference: str | None = None,
    assembly_decision_id: UUID | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> DigitalDecisionResult:
    """ADR-030 item 8's creation/confirmation-required path. Where
    `formal_confirmation_required` is `False`, `DigitalDecision.status` is
    `final` immediately and no `AssemblyDecision` is created - no event
    either, mirroring `create_eligibility_rule`'s "no canonical event for
    the row's own creation" precedent, since `EligibilityEvaluated`
    (already emitted by `evaluate_eligibility`/a future
    `evaluate_process_eligibility`) is what canon 19d.16's event list
    associates with the eligibility side of this flow. Where confirmation
    is required, exactly one `AssemblyDecision` (`pending`) is created and
    `FormalConfirmationRequested` is emitted."""
    from epd2_eligibility_service.domain import DecisionEffect as _DecisionEffect

    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record a digital decision")

    now = clock.now()
    status = (
        DigitalDecisionStatus.FORMAL_CONFIRMATION_REQUIRED
        if formal_confirmation_required
        else DigitalDecisionStatus.FINAL
    )
    digital_decision = DigitalDecision(
        digital_decision_id=digital_decision_id,
        process_reference=dict(process_reference),
        digital_result=digital_result,
        decision_effect=_DecisionEffect(decision_effect),
        formal_confirmation_required=formal_confirmation_required,
        status=status,
        recorded_at=now,
    )
    digital_decision_store.save(digital_decision)

    if not formal_confirmation_required:
        audit_event = append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=generate_uuid(),
                event_type="eligibility.digital_decision_recorded",
                occurred_at=now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="digital_decision",
                target_id=digital_decision_id,
                action="record",
                reason_code="DIGITAL_DECISION_FINAL",
                policy_version=_POLICY_AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash="",
                after_hash=compute_payload_hash(digital_decision_state_payload(digital_decision)),
            ),
            clock=clock,
        )
        return DigitalDecisionResult(
            digital_decision=digital_decision,
            assembly_decision=None,
            event=None,
            audit_event=audit_event,
        )

    if (
        confirming_authority is None
        or legal_basis is None
        or confirmation_deadline is None
        or protocol_or_evidence_reference is None
        or assembly_decision_id is None
    ):
        raise ValueError(
            "confirming_authority, legal_basis, confirmation_deadline, "
            "protocol_or_evidence_reference, and assembly_decision_id are all "
            "required when formal_confirmation_required is True"
        )
    assembly_decision = AssemblyDecision(
        assembly_decision_id=assembly_decision_id,
        digital_decision_id=digital_decision_id,
        confirming_authority=confirming_authority,
        legal_basis=legal_basis,
        confirmation_deadline=confirmation_deadline,
        protocol_or_evidence_reference=protocol_or_evidence_reference,
        status=AssemblyDecisionStatus.PENDING,
    )
    assembly_decision_store.save(assembly_decision)
    event = build_formal_confirmation_requested_event(
        event_id=generate_uuid(),
        assembly_decision=assembly_decision,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="assembly_decision",
            target_id=assembly_decision.assembly_decision_id,
            action="request_formal_confirmation",
            reason_code="FORMAL_CONFIRMATION_REQUESTED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(assembly_decision_state_payload(assembly_decision)),
        ),
        clock=clock,
    )
    return DigitalDecisionResult(
        digital_decision=digital_decision,
        assembly_decision=assembly_decision,
        event=event,
        audit_event=audit_event,
    )


@dataclass(frozen=True, slots=True)
class AssemblyDecisionResult:
    assembly_decision: AssemblyDecision
    event: EventEnvelope
    audit_event: AuditEvent


def record_assembly_decision(
    store: AssemblyDecisionStore,
    digital_decision_store: DigitalDecisionStore,
    audit_store: AuditEventStore,
    *,
    assembly_decision_id: UUID,
    new_status: str,
    final_legal_decision: str,
    divergence_explanation: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> AssemblyDecisionResult:
    """ADR-030 item 8's confirmation/rejection/return-for-revision
    recording. Fail-closed on a divergent `final_legal_decision` missing
    `divergence_explanation` (`domain.AssemblyDecision.with_decision`).
    Neither `DigitalDecision` nor `AssemblyDecision` is ever rewritten -
    this always produces a new, terminal `AssemblyDecision` state, never a
    silent auto-finalization (ADR-030 item 8: 'no silent
    auto-finalization')."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record an assembly decision")
    assembly_decision = store.get(assembly_decision_id)
    if assembly_decision is None:
        raise UnknownAssemblyDecisionError(f"unknown assembly_decision_id: {assembly_decision_id}")
    digital_decision = digital_decision_store.get(assembly_decision.digital_decision_id)
    if digital_decision is None:
        raise UnknownDigitalDecisionError(
            f"unknown digital_decision_id: {assembly_decision.digital_decision_id}"
        )
    assert_assembly_decision_transition_allowed(
        assembly_decision.status, AssemblyDecisionStatus(new_status)
    )
    now = clock.now()
    updated = assembly_decision.with_decision(
        new_status=AssemblyDecisionStatus(new_status),
        final_legal_decision=final_legal_decision,
        digital_result=digital_decision.digital_result,
        divergence_explanation=divergence_explanation,
        decided_at=now,
    )
    store.save(updated)
    event = build_formal_confirmation_recorded_event(
        event_id=generate_uuid(),
        assembly_decision=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="assembly_decision",
            target_id=updated.assembly_decision_id,
            action="record_assembly_decision",
            reason_code="FORMAL_CONFIRMATION_RECORDED",
            policy_version=_POLICY_AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(assembly_decision_state_payload(updated)),
        ),
        clock=clock,
    )
    return AssemblyDecisionResult(assembly_decision=updated, event=event, audit_event=audit_event)


def evaluate_process_eligibility(
    policy_store: ProcessEligibilityPolicyStore,
    identity_record_store: object,
    membership_derived_claims_reader: object,
    *,
    subject_reference: UUID,
    identity_record_id: UUID,
    process_id: UUID,
    process_type: str,
    jurisdiction: str,
    scope_type: str | None,
    scope_id: UUID | None,
    effective_date: datetime,
    membership_subject_reference: UUID | None = None,
) -> tuple[ProcessEligibilityClaims, int] | None:
    """The main PACK-07 process-eligibility use case (canon 19d.3, ADR-027,
    ADR-030 item 6): resolves the single applicable `ProcessEligibilityPolicy`
    version, reads the identity layer via `identity-service.application.
    get_identity_participation_claims` (ADR-027's new cross-pack edge -
    `identity_record_store` here is actually that function itself,
    injected by the caller to avoid this module importing
    `epd2_identity_service.application` at module scope purely for a type
    it cannot express without also importing `.storage`), and, only where
    the resolved policy has a party dimension, reads the membership layer
    via `membership-service.application.get_membership_derived_claims`
    (`membership_derived_claims_reader`, same injection pattern). Returns
    `None` (fail-closed) when no applicable policy version can be
    resolved for `effective_date` - never a default-eligible claim set.

    Returns `(claims, applicable_policy_version)` - the caller is
    responsible for recording `applicable_policy_version` wherever this
    determination needs to remain historically reproducible (ADR-030 item
    6), and for emitting `EligibilityEvaluated`/`ParticipationRightsDerived`
    at whichever of this function's call sites actually needs a domain
    event (this pure resolution step itself emits none).
    """
    policy = policy_store.resolve_for_evaluation(
        process_type=process_type,
        jurisdiction=jurisdiction,
        scope_type=scope_type,
        scope_id=scope_id,
        effective_date=effective_date,
    )
    if policy is None:
        return None

    identity_claims = identity_record_store(  # type: ignore[operator]
        identity_record_id=identity_record_id,
        required_identity_assurance_level=(
            policy.required_assurance_level.required_identity_assurance_level
            if policy.required_assurance_level
            else "none"
        ),
        minimum_age=policy.minimum_age,
        eligible_citizenship_set=policy.eligible_citizenship_set,
        residence_rule=policy.residence_rule,
        territorial_scope_rule=policy.habitual_residence_rule,
        evaluated_at=effective_date,
    )

    membership_layer: MembershipLayerClaims | None = None
    needs_membership = (
        policy.party_internal_voting_rule is not None
        or policy.party_office_candidacy_rule is not None
    )
    if needs_membership and membership_subject_reference is not None:
        membership_layer = membership_derived_claims_reader(  # type: ignore[operator]
            subject_reference=membership_subject_reference,
        )

    claims = _claims_from_identity_and_membership(
        policy, identity_claims, membership_layer, subject_reference=subject_reference
    )
    return claims, policy.policy_version


def _claims_from_identity_and_membership(
    policy: ProcessEligibilityPolicy,
    identity_claims: object,
    membership_layer: MembershipLayerClaims | None,
    *,
    subject_reference: UUID,
) -> ProcessEligibilityClaims:
    """Assembles canon 19d.3's four claims directly from identity-
    service's/membership-service's already-derived booleans (ADR-027) -
    deliberately does NOT call `domain.evaluate_process_eligibility_claims`
    (that pure function's own `IdentityLayerClaims` shape models a
    caller that holds raw age/citizenship facts, which this application
    layer never does once ADR-027's narrow reads are in effect). Kept as
    its own small function so the two evaluation paths (raw-claims, for
    tests and other narrow contexts; derived-claims, for this live
    cross-pack flow) are each independently readable."""
    del subject_reference
    identity_verified = bool(getattr(identity_claims, "identity_verified", False))
    age_met = bool(getattr(identity_claims, "age_requirement_met", False))
    citizenship_met = bool(getattr(identity_claims, "citizenship_requirement_met", False))
    residence_met = bool(getattr(identity_claims, "residence_requirement_met", False))

    active_met = identity_verified and age_met and citizenship_met and residence_met
    passive_met = active_met
    reasons_active = () if active_met else ("ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET",)
    reasons_passive = () if passive_met else ("PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET",)

    if policy.party_internal_voting_rule is None:
        party_internal_met = False
        reasons_party_internal: tuple[str, ...] = ("PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET",)
    else:
        party_internal_met = bool(
            membership_layer is not None and membership_layer.required_membership_status_met
        )
        reasons_party_internal = (
            () if party_internal_met else ("PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET",)
        )

    if policy.party_office_candidacy_rule is None:
        party_office_met = False
        reasons_party_office: tuple[str, ...] = ("PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET",)
    else:
        party_office_met = bool(
            membership_layer is not None
            and membership_layer.required_membership_status_met
            and membership_layer.membership_duration_requirement_met
        )
        reasons_party_office = (
            () if party_office_met else ("PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET",)
        )

    return ProcessEligibilityClaims(
        active_electoral_eligibility_met=active_met,
        active_electoral_eligibility_reason_codes=reasons_active,
        passive_electoral_eligibility_met=passive_met,
        passive_electoral_eligibility_reason_codes=reasons_passive,
        party_internal_voting_eligibility_met=party_internal_met,
        party_internal_voting_eligibility_reason_codes=reasons_party_internal,
        party_office_candidacy_eligibility_met=party_office_met,
        party_office_candidacy_eligibility_reason_codes=reasons_party_office,
    )
