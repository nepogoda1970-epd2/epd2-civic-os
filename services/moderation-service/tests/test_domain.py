"""Tests for epd2_moderation_service.domain.

Covers every `*_ALLOWED_TRANSITIONS`-listed pair (plus at least one
forbidden transition) for each of the three owned entities'
state/type machines, `__post_init__` structural validation, and the
domain-only reachability of the transitions this service's
`application.py` documents as "known gaps" (no dedicated command, but
still domain-legal and tested here) - see README.md's "Known gaps"
section.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_moderation_service.domain import (
    APPEAL_ALLOWED_TRANSITIONS,
    CASE_ALLOWED_TRANSITIONS,
    FINAL_APPEAL_OUTCOMES,
    Appeal,
    AppealStatus,
    ModerationCase,
    ModerationCaseStatus,
    ModerationDecision,
    ModerationDecisionType,
    parse_appeal_status,
    parse_case_status,
    parse_decision_type,
)
from epd2_moderation_service.exceptions import (
    ForbiddenAppealTransitionError,
    ForbiddenModerationCaseTransitionError,
    UnknownAppealStatusError,
    UnknownModerationCaseStatusError,
    UnknownModerationDecisionTypeError,
)

_EFFECTIVE_FROM = datetime(2026, 1, 1, tzinfo=UTC)
_EFFECTIVE_UNTIL = datetime(2026, 2, 1, tzinfo=UTC)


def _make_case(**overrides: object) -> ModerationCase:
    defaults: dict[str, object] = {
        "moderation_case_id": uuid4(),
        "target_type": "contribution",
        "target_id": uuid4(),
        "opened_by": uuid4(),
        "trigger_type": "user_report",
        "policy_version": "1.0",
        "status": ModerationCaseStatus.OPEN,
        "assigned_moderator": None,
    }
    defaults.update(overrides)
    return ModerationCase(**defaults)  # type: ignore[arg-type]


def _make_decision(**overrides: object) -> ModerationDecision:
    defaults: dict[str, object] = {
        "moderation_decision_id": uuid4(),
        "case_id": uuid4(),
        "decision_type": ModerationDecisionType.WARNING,
        "reason_code": "MODERATION_POLICY_VIOLATION",
        "policy_reference": "policy-v1#section-3",
        "decided_by": uuid4(),
        "effective_from": _EFFECTIVE_FROM,
        "effective_until": _EFFECTIVE_UNTIL,
        "public_explanation": "Content violated community guidelines.",
        "audit_reference": str(uuid4()),
    }
    defaults.update(overrides)
    return ModerationDecision(**defaults)  # type: ignore[arg-type]


def _make_appeal(**overrides: object) -> Appeal:
    defaults: dict[str, object] = {
        "appeal_id": uuid4(),
        "decision_id": uuid4(),
        "submitted_by": uuid4(),
        "grounds": "The decision misapplied policy section 3.",
        "status": AppealStatus.SUBMITTED,
        "reviewer_actor_id": None,
        "result": None,
    }
    defaults.update(overrides)
    return Appeal(**defaults)  # type: ignore[arg-type]


# --- ModerationCase ----------------------------------------------------------


@pytest.mark.parametrize("current,target", sorted(CASE_ALLOWED_TRANSITIONS))
def test_every_allowed_case_transition_succeeds(
    current: ModerationCaseStatus, target: ModerationCaseStatus
) -> None:
    case = _make_case(status=current)
    if target == ModerationCaseStatus.UNDER_REVIEW:
        updated = case.with_assigned_moderator(uuid4())
    else:
        updated = case.with_status(target)
    assert updated.status == target


def test_forbidden_case_transition_raises() -> None:
    case = _make_case(status=ModerationCaseStatus.OPEN)
    with pytest.raises(ForbiddenModerationCaseTransitionError) as exc_info:
        case.with_status(ModerationCaseStatus.DECIDED)
    assert exc_info.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_closed_case_has_no_outgoing_transition() -> None:
    case = _make_case(status=ModerationCaseStatus.CLOSED)
    for target in ModerationCaseStatus:
        with pytest.raises(ForbiddenModerationCaseTransitionError):
            case.with_status(target)


def test_with_assigned_moderator_sets_moderator_and_transitions() -> None:
    case = _make_case(status=ModerationCaseStatus.OPEN, assigned_moderator=None)
    moderator_id = uuid4()
    updated = case.with_assigned_moderator(moderator_id)
    assert updated.status == ModerationCaseStatus.UNDER_REVIEW
    assert updated.assigned_moderator == moderator_id


def test_with_assigned_moderator_forbidden_outside_open() -> None:
    case = _make_case(status=ModerationCaseStatus.UNDER_REVIEW)
    with pytest.raises(ForbiddenModerationCaseTransitionError):
        case.with_assigned_moderator(uuid4())


def test_parse_case_status_round_trips() -> None:
    for status in ModerationCaseStatus:
        assert parse_case_status(status.value) is status


def test_parse_case_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownModerationCaseStatusError) as exc_info:
        parse_case_status("not_a_real_status")
    assert exc_info.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


@pytest.mark.parametrize("field", ["target_type", "trigger_type", "policy_version"])
def test_case_rejects_empty_required_string_fields(field: str) -> None:
    with pytest.raises(ValueError):
        _make_case(**{field: ""})


# --- ModerationDecision --------------------------------------------------------


def test_parse_decision_type_round_trips() -> None:
    for decision_type in ModerationDecisionType:
        assert parse_decision_type(decision_type.value) is decision_type


def test_parse_decision_type_rejects_unknown_value() -> None:
    with pytest.raises(UnknownModerationDecisionTypeError) as exc_info:
        parse_decision_type("not_a_real_decision_type")
    assert exc_info.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_decision_has_no_status_field_or_transition_table() -> None:
    """Canon section 14.2 gives `ModerationDecision` no status/transition
    table (unlike `ModerationCase`/`Appeal`) - it is created once and is
    immutable thereafter, like `epd2_initiative_service`'s
    `InitiativeVersion`."""
    fields = ModerationDecision.__dataclass_fields__
    assert "status" not in fields


@pytest.mark.parametrize("field", ["reason_code", "policy_reference", "audit_reference"])
def test_decision_rejects_empty_required_string_fields(field: str) -> None:
    with pytest.raises(ValueError):
        _make_decision(**{field: ""})


def test_decision_rejects_naive_effective_from() -> None:
    with pytest.raises(ValueError):
        _make_decision(effective_from=datetime(2026, 1, 1))


def test_decision_rejects_naive_effective_until() -> None:
    with pytest.raises(ValueError):
        _make_decision(effective_until=datetime(2026, 2, 1))


def test_decision_rejects_effective_until_before_effective_from() -> None:
    with pytest.raises(ValueError):
        _make_decision(
            effective_from=datetime(2026, 2, 1, tzinfo=UTC),
            effective_until=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_decision_allows_no_effective_until() -> None:
    decision = _make_decision(effective_until=None)
    assert decision.effective_until is None


def test_decision_reason_code_field_is_opaque_decision_content() -> None:
    """`ModerationDecision.reason_code` (canon's own field name) holds a
    reason-code-registry *value* describing the decision's own
    justification - completely distinct from any exception class's
    `reason_code` *class attribute* in `exceptions.py`. This test only
    documents that the field accepts an ordinary opaque string; no
    registry lookup happens in the domain layer."""
    decision = _make_decision(reason_code="MODERATION_POLICY_VIOLATION")
    assert decision.reason_code == "MODERATION_POLICY_VIOLATION"


# --- Appeal --------------------------------------------------------------------


@pytest.mark.parametrize("current,target", sorted(APPEAL_ALLOWED_TRANSITIONS))
def test_every_allowed_appeal_transition_succeeds(
    current: AppealStatus, target: AppealStatus
) -> None:
    appeal = _make_appeal(status=current)
    updated = appeal.with_status(target)
    assert updated.status == target


def test_forbidden_appeal_transition_raises() -> None:
    appeal = _make_appeal(status=AppealStatus.SUBMITTED)
    with pytest.raises(ForbiddenAppealTransitionError) as exc_info:
        appeal.with_status(AppealStatus.UPHELD)
    assert exc_info.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


@pytest.mark.parametrize(
    "terminal_status", [*sorted(FINAL_APPEAL_OUTCOMES), AppealStatus.WITHDRAWN]
)
def test_terminal_appeal_statuses_have_no_outgoing_transition(
    terminal_status: AppealStatus,
) -> None:
    appeal = _make_appeal(status=terminal_status)
    for target in AppealStatus:
        with pytest.raises(ForbiddenAppealTransitionError):
            appeal.with_status(target)


def test_admissibility_review_can_reject_without_reaching_under_review() -> None:
    """Canon section 14.3's transition table has a direct
    `admissibility_review -> rejected` edge distinct from
    `under_review -> rejected` - domain-legal even though
    `application.decide_appeal` always walks through `under_review` (see
    README.md's "Appeal review walk" section) rather than exposing this
    edge as its own application-layer path."""
    appeal = _make_appeal(status=AppealStatus.ADMISSIBILITY_REVIEW)
    updated = appeal.with_status(AppealStatus.REJECTED)
    assert updated.status == AppealStatus.REJECTED


def test_withdrawn_reachable_from_every_non_terminal_status() -> None:
    """Domain-legal per `APPEAL_ALLOWED_TRANSITIONS`, even though this
    pack exposes no dedicated `withdraw_appeal` application command (see
    README.md's "Known gaps" section)."""
    non_terminal_statuses = (
        AppealStatus.SUBMITTED,
        AppealStatus.ADMISSIBILITY_REVIEW,
        AppealStatus.UNDER_REVIEW,
    )
    for status in non_terminal_statuses:
        appeal = _make_appeal(status=status)
        updated = appeal.with_status(AppealStatus.WITHDRAWN)
        assert updated.status == AppealStatus.WITHDRAWN


def test_final_appeal_outcomes_excludes_withdrawn() -> None:
    expected = {
        AppealStatus.UPHELD,
        AppealStatus.PARTIALLY_UPHELD,
        AppealStatus.REJECTED,
    }
    assert AppealStatus.WITHDRAWN not in FINAL_APPEAL_OUTCOMES
    assert expected == FINAL_APPEAL_OUTCOMES


def test_parse_appeal_status_round_trips() -> None:
    for status in AppealStatus:
        assert parse_appeal_status(status.value) is status


def test_parse_appeal_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownAppealStatusError) as exc_info:
        parse_appeal_status("not_a_real_status")
    assert exc_info.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_appeal_rejects_empty_grounds() -> None:
    with pytest.raises(ValueError):
        _make_appeal(grounds="")


def test_with_reviewer_and_status_sets_both_atomically() -> None:
    appeal = _make_appeal(status=AppealStatus.SUBMITTED)
    reviewer_id = uuid4()
    updated = appeal.with_reviewer_and_status(
        reviewer_actor_id=reviewer_id,
        new_status=AppealStatus.ADMISSIBILITY_REVIEW,
        result=None,
    )
    assert updated.status == AppealStatus.ADMISSIBILITY_REVIEW
    assert updated.reviewer_actor_id == reviewer_id
    assert updated.result is None


def test_with_reviewer_and_status_records_result_on_final_outcome() -> None:
    appeal = _make_appeal(status=AppealStatus.UNDER_REVIEW, reviewer_actor_id=uuid4())
    updated = appeal.with_reviewer_and_status(
        reviewer_actor_id=appeal.reviewer_actor_id,  # type: ignore[arg-type]
        new_status=AppealStatus.UPHELD,
        result="Original decision overturned; content restored.",
    )
    assert updated.status == AppealStatus.UPHELD
    assert updated.result == "Original decision overturned; content restored."
