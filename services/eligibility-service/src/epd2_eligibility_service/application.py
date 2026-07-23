"""Eligibility Service application layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_eligibility_service.domain import (
    EligibilityDecision,
    EligibilityDecisionValue,
    EligibilityRule,
    EligibilitySnapshot,
    compute_snapshot_digest,
)
from epd2_eligibility_service.events import (
    build_evaluated_event,
    build_snapshot_created_event,
    decision_state_payload,
    snapshot_state_payload,
)
from epd2_eligibility_service.exceptions import UnknownEligibilityRuleError
from epd2_eligibility_service.storage import (
    EligibilityDecisionStore,
    EligibilityRuleStore,
    EligibilitySnapshotStore,
)

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
