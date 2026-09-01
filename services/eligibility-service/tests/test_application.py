"""Tests for epd2_eligibility_service.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_eligibility_service.application import (
    PermissionDeniedError,
    create_eligibility_rule,
    create_eligibility_snapshot,
    evaluate_eligibility,
    get_eligibility_decision,
    get_eligibility_snapshot,
)
from epd2_eligibility_service.domain import EligibilityDecisionValue, EligibilityRule
from epd2_eligibility_service.exceptions import RuleVersionFrozenError, UnknownEligibilityRuleError
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _make_rule(
    rule_store: InMemoryEligibilityRuleStore,
    rule_id: UUID | None = None,
    scope_id: UUID | None = None,
) -> EligibilityRule:
    return create_eligibility_rule(
        rule_store,
        eligibility_rule_id=rule_id or uuid4(),
        rule_version=1,
        scope_type="civic_space",
        scope_id=scope_id or uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )


def test_create_rule_is_idempotent_for_identical_content() -> None:
    store = InMemoryEligibilityRuleStore()
    rule_id = uuid4()
    scope_id = uuid4()
    first = _make_rule(store, rule_id, scope_id)
    second = _make_rule(store, rule_id, scope_id)
    assert first == second


def test_create_rule_rejects_conflicting_resubmission() -> None:
    """Rule freeze (canon 9.1): a version's content cannot change once created."""
    store = InMemoryEligibilityRuleStore()
    rule_id = uuid4()
    _make_rule(store, rule_id)
    with pytest.raises(RuleVersionFrozenError):
        create_eligibility_rule(
            store,
            eligibility_rule_id=rule_id,
            rule_version=1,
            scope_type="civic_space",
            scope_id=uuid4(),  # different scope_id -> different content
            required_membership_status="active",
            required_verification_level="basic",
            region_constraint=None,
            minimum_membership_age=None,
            exclusion_conditions=(),
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
            valid_until=None,
        )


def test_evaluate_eligibility_grants_when_claims_match() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)
    result = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.decision.decision == EligibilityDecisionValue.ELIGIBLE
    assert result.event.event_type == "eligibility.evaluated"
    assert result.audit_event.reason_code == "ELIGIBILITY_MET"


def test_evaluate_eligibility_creates_audit_event() -> None:
    """CT-00-07 / INV-04: evaluating eligibility is a critical action
    regardless of outcome."""
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)
    result = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None
    assert result.audit_event.target_type == "eligibility_decision"


def test_evaluate_eligibility_denies_when_claims_do_not_match() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)
    result = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "suspended", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.decision.decision == EligibilityDecisionValue.NOT_ELIGIBLE
    assert "ELIGIBILITY_NOT_MET" in result.decision.reason_codes
    assert result.audit_event.reason_code == "ELIGIBILITY_NOT_MET"


def test_evaluate_eligibility_requires_manual_review_when_claims_missing() -> None:
    """Fail-closed (INV-10): incomplete attestations never default to eligible."""
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)
    result = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.decision.decision == EligibilityDecisionValue.MANUAL_REVIEW_REQUIRED
    assert result.audit_event.reason_code == "ELIGIBILITY_PENDING"


def test_evaluate_eligibility_without_permission_is_denied() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)
    with pytest.raises(PermissionDeniedError):
        evaluate_eligibility(
            rule_store,
            decision_store,
            audit_store,
            eligibility_rule_id=rule.eligibility_rule_id,
            rule_version=1,
            subject_reference=uuid4(),
            process_id=uuid4(),
            evaluated_claims={"membership_status": "active", "verification_level": "basic"},
            evaluator_version="1.0",
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_evaluate_eligibility_unknown_rule_raises() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownEligibilityRuleError):
        evaluate_eligibility(
            rule_store,
            decision_store,
            audit_store,
            eligibility_rule_id=uuid4(),
            rule_version=1,
            subject_reference=uuid4(),
            process_id=uuid4(),
            evaluated_claims={"membership_status": "active", "verification_level": "basic"},
            evaluator_version="1.0",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_create_snapshot_from_eligible_decisions() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    snapshot_store = InMemoryEligibilitySnapshotStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)

    decisions = [
        evaluate_eligibility(
            rule_store,
            decision_store,
            audit_store,
            eligibility_rule_id=rule.eligibility_rule_id,
            rule_version=1,
            subject_reference=uuid4(),
            process_id=uuid4(),
            evaluated_claims={"membership_status": "active", "verification_level": "basic"},
            evaluator_version="1.0",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        ).decision
        for _ in range(3)
    ]

    result = create_eligibility_snapshot(
        snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=decisions,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.snapshot.eligible_count == 3
    assert result.event.event_type == "eligibility.snapshot_created"
    assert result.audit_event.reason_code == "ELIGIBILITY_SNAPSHOT_CREATED"


def test_create_snapshot_rejects_non_eligible_decision() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    snapshot_store = InMemoryEligibilitySnapshotStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)

    not_eligible = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "suspended", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).decision

    with pytest.raises(ValueError, match="not eligible"):
        create_eligibility_snapshot(
            snapshot_store,
            audit_store,
            eligibility_rule_id=rule.eligibility_rule_id,
            rule_version=1,
            eligible_decisions=[not_eligible],
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_get_eligibility_decision_returns_none_for_unknown_id() -> None:
    decision_store = InMemoryEligibilityDecisionStore()
    assert get_eligibility_decision(decision_store, eligibility_decision_id=uuid4()) is None


def test_get_eligibility_decision_returns_saved_decision() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)

    result = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    fetched = get_eligibility_decision(
        decision_store, eligibility_decision_id=result.decision.eligibility_decision_id
    )
    assert fetched == result.decision


def test_get_eligibility_snapshot_returns_none_for_unknown_id() -> None:
    snapshot_store = InMemoryEligibilitySnapshotStore()
    assert get_eligibility_snapshot(snapshot_store, eligibility_snapshot_id=uuid4()) is None


def test_get_eligibility_snapshot_returns_saved_snapshot() -> None:
    rule_store = InMemoryEligibilityRuleStore()
    decision_store = InMemoryEligibilityDecisionStore()
    snapshot_store = InMemoryEligibilitySnapshotStore()
    audit_store = InMemoryAuditEventStore()
    rule = _make_rule(rule_store)

    eligible = evaluate_eligibility(
        rule_store,
        decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).decision

    snapshot_result = create_eligibility_snapshot(
        snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=[eligible],
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )

    fetched = get_eligibility_snapshot(
        snapshot_store, eligibility_snapshot_id=snapshot_result.snapshot.eligibility_snapshot_id
    )
    assert fetched == snapshot_result.snapshot
