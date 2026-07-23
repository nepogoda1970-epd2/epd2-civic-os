"""Tests for epd2_moderation_service.storage.

Confirms the shared create/get idempotent-or-conflict shape for
`InMemoryModerationCaseStore`/`InMemoryModerationDecisionStore`/
`InMemoryAppealStore` (mirroring `epd2_voting_service.storage`'s own
`InMemoryBallotStore`/`InMemoryVoteEnvelopeStore` precedent), plus
`ModerationDecisionStore`'s deliberate lack of a `save` method (canon
14.2: a `ModerationDecision` is immutable once created).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from epd2_moderation_service.domain import (
    Appeal,
    AppealStatus,
    ModerationCase,
    ModerationCaseStatus,
    ModerationDecision,
    ModerationDecisionType,
)
from epd2_moderation_service.exceptions import (
    AppealConflictError,
    ModerationCaseConflictError,
    ModerationDecisionConflictError,
)
from epd2_moderation_service.storage import (
    InMemoryAppealStore,
    InMemoryModerationCaseStore,
    InMemoryModerationDecisionStore,
)

_EFFECTIVE_FROM = datetime(2026, 1, 1, tzinfo=UTC)


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
        "effective_until": None,
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


# --- InMemoryModerationCaseStore ----------------------------------------------


def test_case_create_then_get_round_trips() -> None:
    store = InMemoryModerationCaseStore()
    case = _make_case()
    stored = store.create(case)
    assert stored == case
    assert store.get(case.moderation_case_id) == case


def test_case_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryModerationCaseStore()
    case = _make_case()
    first = store.create(case)
    second = store.create(replace(case))
    assert first == second == case


def test_case_create_conflicts_on_different_content_same_id() -> None:
    store = InMemoryModerationCaseStore()
    case = _make_case()
    store.create(case)
    conflicting = replace(case, trigger_type="different_trigger")
    try:
        store.create(conflicting)
        raised = False
    except ModerationCaseConflictError as exc:
        raised = True
        assert exc.reason_code == "MODERATION_CASE_DUPLICATE_CONFLICT"
    assert raised


def test_case_save_persists_an_update() -> None:
    store = InMemoryModerationCaseStore()
    case = _make_case()
    store.create(case)
    updated = case.with_assigned_moderator(uuid4())
    store.save(updated)
    assert store.get(case.moderation_case_id) == updated


def test_case_get_returns_none_for_unknown_id() -> None:
    store = InMemoryModerationCaseStore()
    assert store.get(uuid4()) is None


# --- InMemoryModerationDecisionStore -------------------------------------------


def test_decision_create_then_get_round_trips() -> None:
    store = InMemoryModerationDecisionStore()
    decision = _make_decision()
    stored = store.create(decision)
    assert stored == decision
    assert store.get(decision.moderation_decision_id) == decision


def test_decision_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryModerationDecisionStore()
    decision = _make_decision()
    first = store.create(decision)
    second = store.create(replace(decision))
    assert first == second == decision


def test_decision_create_conflicts_on_different_content_same_id() -> None:
    store = InMemoryModerationDecisionStore()
    decision = _make_decision()
    store.create(decision)
    conflicting = replace(decision, public_explanation="a different explanation entirely")
    try:
        store.create(conflicting)
        raised = False
    except ModerationDecisionConflictError as exc:
        raised = True
        assert exc.reason_code == "MODERATION_DECISION_DUPLICATE_CONFLICT"
    assert raised


def test_decision_store_exposes_no_save_method() -> None:
    """Canon 14.2: `ModerationDecision` is immutable once created - there
    is no update path, so `ModerationDecisionStore` deliberately has no
    `save` (unlike `ModerationCaseStore`/`AppealStore`)."""
    store = InMemoryModerationDecisionStore()
    assert not hasattr(store, "save")


def test_decision_get_returns_none_for_unknown_id() -> None:
    store = InMemoryModerationDecisionStore()
    assert store.get(uuid4()) is None


# --- InMemoryAppealStore -------------------------------------------------------


def test_appeal_create_then_get_round_trips() -> None:
    store = InMemoryAppealStore()
    appeal = _make_appeal()
    stored = store.create(appeal)
    assert stored == appeal
    assert store.get(appeal.appeal_id) == appeal


def test_appeal_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryAppealStore()
    appeal = _make_appeal()
    first = store.create(appeal)
    second = store.create(replace(appeal))
    assert first == second == appeal


def test_appeal_create_conflicts_on_different_content_same_id() -> None:
    store = InMemoryAppealStore()
    appeal = _make_appeal()
    store.create(appeal)
    conflicting = replace(appeal, grounds="a wholly different set of grounds")
    try:
        store.create(conflicting)
        raised = False
    except AppealConflictError as exc:
        raised = True
        assert exc.reason_code == "APPEAL_DUPLICATE_SUBMISSION_CONFLICT"
    assert raised


def test_appeal_save_persists_an_update() -> None:
    store = InMemoryAppealStore()
    appeal = _make_appeal()
    store.create(appeal)
    reviewer_id = uuid4()
    updated = appeal.with_reviewer_and_status(
        reviewer_actor_id=reviewer_id,
        new_status=AppealStatus.ADMISSIBILITY_REVIEW,
        result=None,
    )
    store.save(updated)
    assert store.get(appeal.appeal_id) == updated


def test_appeal_get_returns_none_for_unknown_id() -> None:
    store = InMemoryAppealStore()
    assert store.get(uuid4()) is None
