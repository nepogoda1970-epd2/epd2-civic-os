"""Tests for epd2_moderation_service.application.

Exercises the full command set (`open_moderation_case`,
`assign_moderator`, `propose_action`, `issue_decision`,
`enforce_decision`, `submit_appeal`, `decide_appeal`) against in-memory
stores only - this service has no PACK-02 dependency (ADR-008) and no
other PACK-03 service dependency, so nothing beyond `epd2_core`/
`epd2_audit_core` collaborators is ever needed to test it.

`test_decide_appeal_rejects_the_original_decider_as_reviewer` /
`test_decide_appeal_succeeds_for_a_different_reviewer` are this
service's flagship pair (CT-00-06 / canon section 14.3's hard rule) -
see README.md.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_moderation_service.application import (
    PermissionDeniedError,
    assign_moderator,
    decide_appeal,
    enforce_decision,
    get_moderation_decision,
    issue_decision,
    open_moderation_case,
    propose_action,
    submit_appeal,
)
from epd2_moderation_service.domain import (
    AppealStatus,
    ModerationCaseStatus,
    ModerationDecisionType,
)
from epd2_moderation_service.exceptions import (
    UnknownAppealError,
    UnknownModerationCaseError,
    UnknownModerationDecisionError,
)
from epd2_moderation_service.storage import (
    InMemoryAppealStore,
    InMemoryModerationCaseStore,
    InMemoryModerationDecisionStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)
_EFFECTIVE_FROM = datetime(2026, 1, 5, tzinfo=UTC)


def _actor(actor_id: UUID | None = None) -> ActorRef:
    return ActorRef(actor_id=actor_id if actor_id is not None else uuid4(), actor_type="service")


class _Fixture:
    """One fully-wired set of in-memory stores for one test."""

    def __init__(self) -> None:
        self.case_store = InMemoryModerationCaseStore()
        self.decision_store = InMemoryModerationDecisionStore()
        self.appeal_store = InMemoryAppealStore()
        self.audit_store = InMemoryAuditEventStore()


def _open_case(fx: _Fixture, *, actor: ActorRef | None = None) -> UUID:
    case_id = uuid4()
    open_moderation_case(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        target_type="contribution",
        target_id=uuid4(),
        opened_by=uuid4(),
        trigger_type="user_report",
        policy_version="1.0",
        actor=actor if actor is not None else _actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return case_id


def _advance_to_action_proposed(fx: _Fixture, case_id: UUID) -> None:
    assign_moderator(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        moderator_id=uuid4(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    propose_action(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )


def _issue_decision(
    fx: _Fixture, case_id: UUID, *, decided_by: UUID | None = None
) -> tuple[UUID, UUID]:
    """Advance a fresh case through to `decided`, returning
    `(moderation_decision_id, decided_by)`."""
    _advance_to_action_proposed(fx, case_id)
    decision_id = uuid4()
    decider = decided_by if decided_by is not None else uuid4()
    result = issue_decision(
        fx.case_store,
        fx.decision_store,
        fx.audit_store,
        moderation_case_id=case_id,
        moderation_decision_id=decision_id,
        decision_type=ModerationDecisionType.TEMPORARY_HIDE,
        reason_code="MODERATION_POLICY_VIOLATION",
        policy_reference="policy-v1#section-3",
        decided_by=decider,
        effective_from=_EFFECTIVE_FROM,
        effective_until=None,
        public_explanation="Content temporarily hidden pending review.",
        actor=_actor(decider),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return result.decision.moderation_decision_id, decider


def _submit_appeal(fx: _Fixture, decision_id: UUID) -> UUID:
    appeal_id = uuid4()
    submit_appeal(
        fx.case_store,
        fx.decision_store,
        fx.appeal_store,
        fx.audit_store,
        appeal_id=appeal_id,
        decision_id=decision_id,
        submitted_by=uuid4(),
        grounds="The decision misapplied policy section 3.",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return appeal_id


# --- open_moderation_case -------------------------------------------------------


def test_open_moderation_case_creates_case_in_open_status() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    case = fx.case_store.get(case_id)
    assert case is not None
    assert case.status == ModerationCaseStatus.OPEN
    assert case.assigned_moderator is None


def test_open_moderation_case_emits_event_and_audit_entry() -> None:
    fx = _Fixture()
    actor = _actor()
    case_id = uuid4()
    result = open_moderation_case(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        target_type="contribution",
        target_id=uuid4(),
        opened_by=uuid4(),
        trigger_type="user_report",
        policy_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.event.event_type == "moderation.case_opened"
    assert result.audit_event.reason_code == "MODERATION_CASE_STATUS_CHANGED"
    assert result.audit_event.target_type == "moderation_case"
    assert result.audit_event.target_id == case_id
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) == result.audit_event


def test_open_moderation_case_rejects_unauthorized_actor() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError) as exc_info:
        open_moderation_case(
            fx.case_store,
            fx.audit_store,
            moderation_case_id=uuid4(),
            target_type="contribution",
            target_id=uuid4(),
            opened_by=uuid4(),
            trigger_type="user_report",
            policy_version="1.0",
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )
    assert exc_info.value.reason_code == "PERMISSION_DENIED"


def test_open_moderation_case_is_idempotent_for_a_repeated_event_id() -> None:
    fx = _Fixture()
    actor = _actor()
    case_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        moderation_case_id=case_id,
        target_type="contribution",
        target_id=uuid4(),
        opened_by=uuid4(),
        trigger_type="user_report",
        policy_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        event_id=event_id,
    )
    first = open_moderation_case(fx.case_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    second = open_moderation_case(fx.case_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert first.case == second.case
    # Confirms no second AuditEvent was appended for the replay.
    assert len(fx.audit_store.list_by_aggregate("moderation_case", case_id)) == 1


# --- assign_moderator ------------------------------------------------------------


def test_assign_moderator_transitions_case_and_sets_moderator() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    moderator_id = uuid4()
    result = assign_moderator(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        moderator_id=moderator_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.case.status == ModerationCaseStatus.UNDER_REVIEW
    assert result.case.assigned_moderator == moderator_id
    assert result.event.event_type == "moderation.case_assigned"


def test_assign_moderator_raises_for_unknown_case() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownModerationCaseError):
        assign_moderator(
            fx.case_store,
            fx.audit_store,
            moderation_case_id=uuid4(),
            moderator_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- propose_action --------------------------------------------------------------


def test_propose_action_transitions_case_with_no_event() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    assign_moderator(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        moderator_id=uuid4(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = propose_action(
        fx.case_store,
        fx.audit_store,
        moderation_case_id=case_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.case.status == ModerationCaseStatus.ACTION_PROPOSED
    assert not hasattr(result, "event")
    assert result.audit_event.reason_code == "MODERATION_CASE_STATUS_CHANGED"


# --- issue_decision ---------------------------------------------------------------


def test_issue_decision_creates_decision_and_closes_case_to_decided() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, decided_by = _issue_decision(fx, case_id)
    case = fx.case_store.get(case_id)
    decision = fx.decision_store.get(decision_id)
    assert case is not None and case.status == ModerationCaseStatus.DECIDED
    assert decision is not None
    assert decision.decided_by == decided_by
    assert decision.reason_code == "MODERATION_POLICY_VIOLATION"


def test_issue_decision_sets_audit_reference_to_the_audit_event_id() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    _advance_to_action_proposed(fx, case_id)
    event_id = uuid4()
    decider = uuid4()
    result = issue_decision(
        fx.case_store,
        fx.decision_store,
        fx.audit_store,
        moderation_case_id=case_id,
        moderation_decision_id=uuid4(),
        decision_type=ModerationDecisionType.WARNING,
        reason_code="MODERATION_POLICY_VIOLATION",
        policy_reference="policy-v1#section-3",
        decided_by=decider,
        effective_from=_EFFECTIVE_FROM,
        effective_until=None,
        public_explanation="Warning issued.",
        actor=_actor(decider),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        event_id=event_id,
    )
    assert result.decision.audit_reference == str(event_id)
    assert result.audit_event.audit_event_id == event_id


def test_issue_decision_emits_event_and_audit_with_correct_reason_code() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _ = _issue_decision(fx, case_id)
    decision = fx.decision_store.get(decision_id)
    assert decision is not None
    audit_events = fx.audit_store.list_by_aggregate("moderation_decision", decision_id)
    assert len(audit_events) == 1
    assert audit_events[0].reason_code == "MODERATION_DECISION_ISSUED"


# --- enforce_decision -------------------------------------------------------------


def test_enforce_decision_emits_event_without_mutating_decision() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _ = _issue_decision(fx, case_id)
    before = fx.decision_store.get(decision_id)
    result = enforce_decision(
        fx.case_store,
        fx.decision_store,
        fx.audit_store,
        moderation_decision_id=decision_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    after = fx.decision_store.get(decision_id)
    assert before == after  # ModerationDecision has no mutable "enforced" field.
    assert result.event.event_type == "moderation.decision_enforced"
    assert result.audit_event.reason_code == "MODERATION_DECISION_ENFORCED"
    assert result.audit_event.before_hash == result.audit_event.after_hash
    assert result.case.status == ModerationCaseStatus.DECIDED  # case status untouched


def test_enforce_decision_raises_for_unknown_decision() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownModerationDecisionError):
        enforce_decision(
            fx.case_store,
            fx.decision_store,
            fx.audit_store,
            moderation_decision_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- submit_appeal -----------------------------------------------------------------


def test_submit_appeal_creates_appeal_and_transitions_case_to_appealed() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _ = _issue_decision(fx, case_id)
    appeal_id = _submit_appeal(fx, decision_id)
    appeal = fx.appeal_store.get(appeal_id)
    case = fx.case_store.get(case_id)
    assert appeal is not None
    assert appeal.status == AppealStatus.SUBMITTED
    assert appeal.decision_id == decision_id
    assert case is not None and case.status == ModerationCaseStatus.APPEALED


def test_submit_appeal_raises_for_unknown_decision() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownModerationDecisionError):
        submit_appeal(
            fx.case_store,
            fx.decision_store,
            fx.appeal_store,
            fx.audit_store,
            appeal_id=uuid4(),
            decision_id=uuid4(),
            submitted_by=uuid4(),
            grounds="Grounds for appeal.",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- decide_appeal: THE flagship reviewer-!=-original-decider check ---------------


def test_decide_appeal_rejects_the_original_decider_as_reviewer() -> None:
    """CT-00-06 / canon section 14.3: "an appeal must not be finally
    decided by the author of the original decision". The single most
    important test in this service - see README.md."""
    fx = _Fixture()
    case_id = _open_case(fx)
    decided_by = uuid4()
    decision_id, decided_by = _issue_decision(fx, case_id, decided_by=decided_by)
    appeal_id = _submit_appeal(fx, decision_id)

    with pytest.raises(PermissionDeniedError) as exc_info:
        decide_appeal(
            fx.case_store,
            fx.decision_store,
            fx.appeal_store,
            fx.audit_store,
            appeal_id=appeal_id,
            reviewer_actor_id=decided_by,  # same actor as the original decision
            outcome=AppealStatus.REJECTED,
            result="Appeal rejected.",
            actor=_actor(decided_by),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )
    assert exc_info.value.reason_code == "PERMISSION_DENIED"

    # No mutation happened: the appeal is still submitted, the case is
    # still appealed, and no `appeal_decided` audit entry was appended
    # beyond the one `submit_appeal` already recorded.
    appeal = fx.appeal_store.get(appeal_id)
    case = fx.case_store.get(case_id)
    assert appeal is not None and appeal.status == AppealStatus.SUBMITTED
    assert case is not None and case.status == ModerationCaseStatus.APPEALED
    audit_events = fx.audit_store.list_by_aggregate("appeal", appeal_id)
    assert len(audit_events) == 1
    assert audit_events[0].action == "submit_appeal"


def test_decide_appeal_succeeds_for_a_different_reviewer() -> None:
    """The mirror-image of the test above: a genuinely different reviewer
    is accepted, the appeal reaches its final outcome, and the case
    closes."""
    fx = _Fixture()
    case_id = _open_case(fx)
    decided_by = uuid4()
    decision_id, decided_by = _issue_decision(fx, case_id, decided_by=decided_by)
    appeal_id = _submit_appeal(fx, decision_id)

    reviewer_id = uuid4()
    assert reviewer_id != decided_by
    result = decide_appeal(
        fx.case_store,
        fx.decision_store,
        fx.appeal_store,
        fx.audit_store,
        appeal_id=appeal_id,
        reviewer_actor_id=reviewer_id,
        outcome=AppealStatus.UPHELD,
        result="Original decision overturned; content restored.",
        actor=_actor(reviewer_id),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.appeal.status == AppealStatus.UPHELD
    assert result.appeal.reviewer_actor_id == reviewer_id
    assert result.appeal.result == "Original decision overturned; content restored."
    assert result.case.status == ModerationCaseStatus.CLOSED
    assert result.event.event_type == "moderation.appeal_decided"
    assert result.audit_event.reason_code == "APPEAL_DECIDED"


def test_decide_appeal_rejects_withdrawn_as_an_outcome() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _decided_by = _issue_decision(fx, case_id)
    appeal_id = _submit_appeal(fx, decision_id)
    with pytest.raises(ValueError):
        decide_appeal(
            fx.case_store,
            fx.decision_store,
            fx.appeal_store,
            fx.audit_store,
            appeal_id=appeal_id,
            reviewer_actor_id=uuid4(),
            outcome=AppealStatus.WITHDRAWN,
            result="withdrawn",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_decide_appeal_raises_for_unknown_appeal() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownAppealError):
        decide_appeal(
            fx.case_store,
            fx.decision_store,
            fx.appeal_store,
            fx.audit_store,
            appeal_id=uuid4(),
            reviewer_actor_id=uuid4(),
            outcome=AppealStatus.REJECTED,
            result="n/a",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_decide_appeal_is_idempotent_for_a_repeated_event_id() -> None:
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _decided_by = _issue_decision(fx, case_id)
    appeal_id = _submit_appeal(fx, decision_id)
    reviewer_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        appeal_id=appeal_id,
        reviewer_actor_id=reviewer_id,
        outcome=AppealStatus.REJECTED,
        result="Appeal rejected after full review.",
        actor=_actor(reviewer_id),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        event_id=event_id,
    )
    first = decide_appeal(
        fx.case_store,
        fx.decision_store,
        fx.appeal_store,
        fx.audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = decide_appeal(
        fx.case_store,
        fx.decision_store,
        fx.appeal_store,
        fx.audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert first.appeal == second.appeal
    # One audit entry from `submit_appeal`, one from `decide_appeal` - the
    # replayed second `decide_appeal` call must not add a third.
    assert len(fx.audit_store.list_by_aggregate("appeal", appeal_id)) == 2


def test_decide_appeal_admissibility_reject_reaches_rejected_without_full_review() -> None:
    """Exercises the `admissibility_review -> rejected` edge indirectly:
    `decide_appeal` always walks through `under_review` internally (see
    README.md's "Appeal review walk" section), but the *outcome*
    `rejected` is reachable regardless of whether a full review actually
    happened - this test documents that `decide_appeal` does not
    distinguish the two paths at the application layer today."""
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _decided_by = _issue_decision(fx, case_id)
    appeal_id = _submit_appeal(fx, decision_id)
    reviewer_id = uuid4()
    result = decide_appeal(
        fx.case_store,
        fx.decision_store,
        fx.appeal_store,
        fx.audit_store,
        appeal_id=appeal_id,
        reviewer_actor_id=reviewer_id,
        outcome=AppealStatus.REJECTED,
        result="Inadmissible: outside the appeal window.",
        actor=_actor(reviewer_id),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.appeal.status == AppealStatus.REJECTED


def test_get_moderation_decision_read_accessor() -> None:
    """Additive (PACK-04, ADR-012 item 2): backs
    `epd2_transparency_service.application.publish_ledger_entry` for
    `subject_type = "moderation_decision"`."""
    fx = _Fixture()
    case_id = _open_case(fx)
    decision_id, _ = _issue_decision(fx, case_id)
    found = get_moderation_decision(fx.decision_store, moderation_decision_id=decision_id)
    assert found is not None
    assert found.moderation_decision_id == decision_id
    assert get_moderation_decision(fx.decision_store, moderation_decision_id=uuid4()) is None
