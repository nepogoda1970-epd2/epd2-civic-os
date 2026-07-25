"""PACK-07 (canon-0.6.0, ADR-026 through ADR-031) deliberately duplicates
three pieces of business logic across service boundaries rather than
sharing a Python type or function through `epd2_core` (whose own charter
forbids holding business rules - `packages/python/epd2-core/README.md`,
"Границы") or through a forbidden cross-service `.domain` import
(`tests/repository/test_service_boundaries.py`):

1. The critical-policy four-gate activation check (canon 19d.7):
   `epd2_eligibility_service.domain.assert_critical_policy_activation_gate`
   and `epd2_membership_service.domain.assert_critical_policy_activation_gate`.
2. The canonical polymorphic `Appeal` entity (canon 14.3):
   `epd2_moderation_service.domain.Appeal` and
   `epd2_membership_service.domain.Appeal`.
3. The step-up authentication assurance-ordering/evaluation logic (canon
   19d.8): `epd2_eligibility_service.domain._ASSURANCE_ORDER`/
   `check_step_up_requirement` and
   `epd2_identity_service.domain._ASSURANCE_ORDER`/
   `evaluate_step_up_satisfaction`.

Each copy's own module docstring points here. This file is what keeps
that promise honest: every duplicate is asserted to accept/reject the
exact same inputs as its sibling, so a future edit to one copy that
silently drifts from the other fails loudly here, rather than only
being caught (if at all) by an unrelated service's own test suite.

Must be run from the repository root (with PYTHONPATH covering both
services' `src/` directories, per `LOCAL_VERIFICATION.md`)."""

from __future__ import annotations

import dataclasses
import itertools
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import epd2_eligibility_service.domain as eligibility_domain
import epd2_identity_service.domain as identity_domain
import epd2_membership_service.domain as membership_domain
import epd2_moderation_service.domain as moderation_domain

_NOW = datetime(2026, 1, 1, tzinfo=UTC)

# =============================================================================
# 1. Critical-policy four-gate activation (canon 19d.7)
# =============================================================================


def _gate_truth_table() -> list[tuple[bool, bool, str | None, str | None]]:
    """Every combination of the four gate conditions - 2 booleans x 2
    "reference present or not" flags = 16 rows."""
    rows: list[tuple[bool, bool, str | None, str | None]] = []
    for (
        decision_authorized,
        multi_person_approval_met,
        has_digest,
        has_commitment,
    ) in itertools.product([True, False], repeat=4):
        rows.append(
            (
                decision_authorized,
                multi_person_approval_met,
                "digest" if has_digest else None,
                "commitment" if has_commitment else None,
            )
        )
    return rows


def test_critical_policy_activation_gate_parity_across_all_sixteen_combinations() -> None:
    for (
        decision_authorized,
        multi_person_approval_met,
        digest,
        commitment,
    ) in _gate_truth_table():
        eligibility_gate = eligibility_domain.CriticalPolicyActivationGate(
            decision_authorized=decision_authorized,
            multi_person_approval_met=multi_person_approval_met,
            signed_policy_digest_reference=digest,
            transparency_log_commitment_reference=commitment,
        )
        membership_gate = membership_domain.CriticalPolicyActivationGate(
            decision_authorized=decision_authorized,
            multi_person_approval_met=multi_person_approval_met,
            signed_policy_digest_reference=digest,
            transparency_log_commitment_reference=commitment,
        )

        eligibility_result = _passes(
            eligibility_domain.assert_critical_policy_activation_gate, eligibility_gate
        )
        membership_result = _passes(
            membership_domain.assert_critical_policy_activation_gate, membership_gate
        )

        assert eligibility_result == membership_result, (
            f"gate parity mismatch for decision_authorized={decision_authorized!r}, "
            f"multi_person_approval_met={multi_person_approval_met!r}, digest={digest!r}, "
            f"commitment={commitment!r}: eligibility-service={eligibility_result!r}, "
            f"membership-service={membership_result!r}"
        )


def _passes(fn: object, *args: object) -> bool:
    try:
        fn(*args)  # type: ignore[operator]
    except Exception:
        return False
    return True


# =============================================================================
# 2. Appeal entity (canon 14.3) - moderation-service (canonical) vs
#    membership-service (documented duplicate, ADR-030 item 4).
# =============================================================================


def test_appeal_status_enum_values_match() -> None:
    moderation_values = {status.value for status in moderation_domain.AppealStatus}
    membership_values = {status.value for status in membership_domain.AppealStatus}
    assert moderation_values == membership_values


def test_appeal_final_outcomes_match() -> None:
    moderation_final = {status.value for status in moderation_domain.FINAL_APPEAL_OUTCOMES}
    membership_final = {status.value for status in membership_domain.FINAL_APPEAL_OUTCOMES}
    assert moderation_final == membership_final


def test_appeal_allowed_transitions_match() -> None:
    moderation_transitions = {
        (current.value, target.value)
        for current, target in moderation_domain.APPEAL_ALLOWED_TRANSITIONS
    }
    membership_transitions = {
        (current.value, target.value)
        for current, target in membership_domain.APPEAL_ALLOWED_TRANSITIONS
    }
    assert moderation_transitions == membership_transitions


def test_appeal_field_set_matches() -> None:
    moderation_fields = {f.name for f in dataclasses.fields(moderation_domain.Appeal)}
    membership_fields = {f.name for f in dataclasses.fields(membership_domain.Appeal)}
    assert moderation_fields == membership_fields


def test_appeal_reviewer_separation_transition_behavior_matches() -> None:
    """Both copies must walk the same submitted -> admissibility_review
    -> under_review -> <final> path via `with_reviewer_and_status`, and
    both must reject the same invalid direct jump."""
    moderation_appeal = moderation_domain.Appeal(
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        status=moderation_domain.AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    membership_appeal = membership_domain.Appeal(
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        status=membership_domain.AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    reviewer_id = uuid4()

    moderation_final = (
        moderation_appeal.with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=moderation_domain.AppealStatus.ADMISSIBILITY_REVIEW,
            result=None,
        )
        .with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=moderation_domain.AppealStatus.UNDER_REVIEW,
            result=None,
        )
        .with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=moderation_domain.AppealStatus.UPHELD,
            result="upheld",
        )
    )
    membership_final = (
        membership_appeal.with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=membership_domain.AppealStatus.ADMISSIBILITY_REVIEW,
            result=None,
        )
        .with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=membership_domain.AppealStatus.UNDER_REVIEW,
            result=None,
        )
        .with_reviewer_and_status(
            reviewer_actor_id=reviewer_id,
            new_status=membership_domain.AppealStatus.UPHELD,
            result="upheld",
        )
    )
    assert moderation_final.status.value == membership_final.status.value == "upheld"

    moderation_rejects_direct_jump = not _passes(
        moderation_appeal.with_status, moderation_domain.AppealStatus.UPHELD
    )
    membership_rejects_direct_jump = not _passes(
        membership_appeal.with_status, membership_domain.AppealStatus.UPHELD
    )
    assert moderation_rejects_direct_jump == membership_rejects_direct_jump is True


# =============================================================================
# 3. Step-up authentication assurance ordering (canon 19d.8) -
#    eligibility-service's `check_step_up_requirement` vs identity-
#    service's `evaluate_step_up_satisfaction`.
# =============================================================================


def test_assurance_order_dict_matches() -> None:
    assert eligibility_domain._ASSURANCE_ORDER == identity_domain._ASSURANCE_ORDER


def _eligibility_step_up_satisfied(
    *,
    identity_assurance_level: str,
    authentication_assurance_level: str,
    required_identity_assurance_level: str,
    required_authentication_assurance_level: str,
    fresh_authentication_required: bool,
    maximum_authentication_age: timedelta | None,
    session_authenticated_at: datetime | None,
    required_attribute_freshness: timedelta | None,
    attribute_verified_at: datetime | None,
    evaluated_at: datetime,
) -> bool:
    requirement = eligibility_domain.StepUpAuthenticationRequirement(
        requirement_id=uuid4(),
        requirement_version=1,
        status=eligibility_domain.CriticalPolicyStatus.ACTIVE,
        action_code="cast_ballot",
        required_authentication_context="session",
        assurance_requirement=eligibility_domain.AssuranceRequirement(
            required_identity_assurance_level=required_identity_assurance_level,
            required_authentication_assurance_level=required_authentication_assurance_level,
            required_attribute_freshness=required_attribute_freshness,
        ),
        fresh_authentication_required=fresh_authentication_required,
        reauthentication_reason="parity test",
        maximum_authentication_age=maximum_authentication_age,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    observed = eligibility_domain.ObservedAuthenticationState(
        identity_assurance_level=identity_assurance_level,
        authentication_assurance_level=authentication_assurance_level,
        session_authenticated_at=session_authenticated_at,
        attribute_verified_at=attribute_verified_at,
    )
    return _passes_kw(
        eligibility_domain.check_step_up_requirement,
        requirement,
        observed,
        evaluated_at=evaluated_at,
    )


def _passes_kw(fn: object, *args: object, **kwargs: object) -> bool:
    try:
        fn(*args, **kwargs)  # type: ignore[operator]
    except Exception:
        return False
    return True


def _identity_step_up_satisfied(
    *,
    identity_assurance_level: str,
    authentication_assurance_level: str,
    required_identity_assurance_level: str,
    required_authentication_assurance_level: str,
    fresh_authentication_required: bool,
    maximum_authentication_age: timedelta | None,
    session_authenticated_at: datetime | None,
    required_attribute_freshness: timedelta | None,
    attribute_verified_at: datetime | None,
    evaluated_at: datetime,
) -> bool:
    context = (
        identity_domain.AuthenticationContext(
            authentication_context_id=uuid4(),
            account_id=uuid4(),
            authentication_method="password+otp",
            authentication_assurance_level=identity_domain.AuthenticationAssuranceLevel(
                authentication_assurance_level
            ),
            session_authenticated_at=session_authenticated_at,
            provider_reference="ref",
        )
        if session_authenticated_at is not None
        else None
    )
    result = identity_domain.evaluate_step_up_satisfaction(
        context=context,
        identity_assurance_level=identity_domain.IdentityAssuranceLevel(identity_assurance_level),
        attribute_verified_at=attribute_verified_at,
        required_authentication_assurance_level=required_authentication_assurance_level,
        required_identity_assurance_level=required_identity_assurance_level,
        fresh_authentication_required=fresh_authentication_required,
        maximum_authentication_age=maximum_authentication_age,
        required_attribute_freshness=required_attribute_freshness,
        reauthentication_reason="parity test",
        evaluated_at=evaluated_at,
    )
    return result.satisfied


_STEP_UP_SCENARIOS: tuple[dict[str, object], ...] = (
    # All conditions met.
    {
        "identity_assurance_level": "substantial",
        "authentication_assurance_level": "substantial",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": _NOW - timedelta(minutes=5),
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
    # Authentication assurance below requirement.
    {
        "identity_assurance_level": "substantial",
        "authentication_assurance_level": "low",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": _NOW - timedelta(minutes=5),
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
    # Identity assurance below requirement.
    {
        "identity_assurance_level": "low",
        "authentication_assurance_level": "substantial",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": _NOW - timedelta(minutes=5),
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
    # Session too old.
    {
        "identity_assurance_level": "substantial",
        "authentication_assurance_level": "substantial",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": _NOW - timedelta(hours=2),
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
    # Attribute verification stale.
    {
        "identity_assurance_level": "substantial",
        "authentication_assurance_level": "substantial",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": _NOW - timedelta(minutes=5),
        "required_attribute_freshness": timedelta(days=365),
        "attribute_verified_at": _NOW - timedelta(days=400),
        "evaluated_at": _NOW,
    },
    # No observed session/context at all - fails closed.
    {
        "identity_assurance_level": "substantial",
        "authentication_assurance_level": "substantial",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": True,
        "maximum_authentication_age": timedelta(minutes=15),
        "session_authenticated_at": None,
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
    # High assurance exceeds requirement - still satisfied.
    {
        "identity_assurance_level": "high",
        "authentication_assurance_level": "high",
        "required_identity_assurance_level": "substantial",
        "required_authentication_assurance_level": "substantial",
        "fresh_authentication_required": False,
        "maximum_authentication_age": None,
        "session_authenticated_at": _NOW - timedelta(days=30),
        "required_attribute_freshness": None,
        "attribute_verified_at": None,
        "evaluated_at": _NOW,
    },
)


def test_step_up_evaluation_parity_across_representative_scenarios() -> None:
    for scenario in _STEP_UP_SCENARIOS:
        eligibility_result = _eligibility_step_up_satisfied(**scenario)  # type: ignore[arg-type]
        identity_result = _identity_step_up_satisfied(**scenario)  # type: ignore[arg-type]
        assert eligibility_result == identity_result, (
            f"step-up evaluation parity mismatch for scenario {scenario!r}: "
            f"eligibility-service={eligibility_result!r}, identity-service={identity_result!r}"
        )
