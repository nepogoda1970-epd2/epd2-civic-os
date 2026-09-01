"""Tests for epd2_tally_service.domain.

Covers every `ALLOWED_TRANSITIONS` pair (plus a forbidden transition) for
`Tally`'s status machine, the tie -> `tie_no_decision` rule (ADR-009 item
11), the quorum-optional rule (ADR-009 item 5), `compute_finality_state`'s
two-value-only guarantee (ADR-010), and the `FORBIDDEN_FIELD_NAMES`
absence guarantee on both owned entities (ADR-009 item 15).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_tally_service.domain import (
    ALLOWED_TRANSITIONS,
    DEFAULT_CHALLENGE_WINDOW_HOURS,
    FORBIDDEN_FIELD_NAMES,
    FinalityState,
    QuorumResult,
    ResultPublication,
    Tally,
    TallyVerificationStatus,
    ThresholdResult,
    compute_challenge_deadline,
    compute_finality_state,
    compute_input_set_hash,
    compute_quorum_result,
    compute_threshold_result,
    parse_quorum_result,
    parse_threshold_result,
    parse_verification_status,
)
from epd2_tally_service.exceptions import (
    ForbiddenTallyTransitionError,
    UnknownQuorumResultError,
    UnknownTallyVerificationStatusError,
    UnknownThresholdResultError,
)

_STARTED_AT = datetime(2026, 1, 1, tzinfo=UTC)
_PUBLISHED_AT = datetime(2026, 1, 10, tzinfo=UTC)


def _make_tally(**overrides: object) -> Tally:
    defaults: dict[str, object] = {
        "tally_id": uuid4(),
        "ballot_id": uuid4(),
        "input_set_hash": "a" * 64,
        "algorithm_version": "1.0",
        "started_at": _STARTED_AT,
        "completed_at": None,
        "result_data": {},
        "invalid_vote_count": 0,
        "tally_signature": None,
        "verification_status": TallyVerificationStatus.PENDING,
    }
    defaults.update(overrides)
    return Tally(**defaults)  # type: ignore[arg-type]


def _make_result(**overrides: object) -> ResultPublication:
    defaults: dict[str, object] = {
        "result_publication_id": uuid4(),
        "ballot_id": uuid4(),
        "tally_id": uuid4(),
        "eligible_count": 100,
        "credential_count": 90,
        "accepted_vote_count": 80,
        "rejected_vote_count": 5,
        "quorum_result": QuorumResult.NOT_REQUIRED,
        "threshold_result": ThresholdResult.THRESHOLD_MET,
        "published_at": _PUBLISHED_AT,
        "audit_package_reference": "audit-package-1",
        "challenge_deadline_at": _PUBLISHED_AT + timedelta(hours=72),
    }
    defaults.update(overrides)
    return ResultPublication(**defaults)  # type: ignore[arg-type]


# --- Tally status machine ----------------------------------------------------


def test_parse_verification_status_accepts_known_values() -> None:
    assert parse_verification_status("running") == TallyVerificationStatus.RUNNING


def test_parse_verification_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownTallyVerificationStatusError):
        parse_verification_status("half_done")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_TRANSITIONS))
def test_every_allowed_tally_transition_succeeds(
    current: TallyVerificationStatus, target: TallyVerificationStatus
) -> None:
    tally = _make_tally(verification_status=current)
    if target == TallyVerificationStatus.COMPLETED:
        updated = tally.with_completion(
            completed_at=_STARTED_AT + timedelta(hours=1),
            result_data={"yes": 1},
            invalid_vote_count=0,
            tally_signature=None,
        )
    else:
        updated = tally.with_status(target)
    assert updated.verification_status == target


def test_tally_forbidden_transition_pending_to_completed() -> None:
    tally = _make_tally(verification_status=TallyVerificationStatus.PENDING)
    with pytest.raises(ForbiddenTallyTransitionError):
        tally.with_status(TallyVerificationStatus.COMPLETED)


def test_tally_forbidden_transition_running_to_verified() -> None:
    tally = _make_tally(verification_status=TallyVerificationStatus.RUNNING)
    with pytest.raises(ForbiddenTallyTransitionError):
        tally.with_status(TallyVerificationStatus.VERIFIED)


def test_tally_superseded_is_terminal() -> None:
    tally = _make_tally(verification_status=TallyVerificationStatus.SUPERSEDED)
    with pytest.raises(ForbiddenTallyTransitionError):
        tally.with_status(TallyVerificationStatus.RUNNING)


def test_tally_with_completion_records_result() -> None:
    tally = _make_tally(verification_status=TallyVerificationStatus.RUNNING)
    completed = tally.with_completion(
        completed_at=_STARTED_AT + timedelta(hours=1),
        result_data={"yes": 10, "no": 5},
        invalid_vote_count=2,
        tally_signature="sig",
    )
    assert completed.verification_status == TallyVerificationStatus.COMPLETED
    assert dict(completed.result_data) == {"yes": 10, "no": 5}
    assert completed.invalid_vote_count == 2
    assert completed.tally_signature == "sig"


def test_tally_requires_timezone_aware_started_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_tally(started_at=datetime(2026, 1, 1))


def test_tally_rejects_negative_invalid_vote_count() -> None:
    with pytest.raises(ValueError, match="invalid_vote_count"):
        _make_tally(invalid_vote_count=-1)


def test_tally_rejects_negative_result_data_count() -> None:
    with pytest.raises(ValueError, match="result_data"):
        _make_tally(result_data={"yes": -1})


# --- compute_input_set_hash ---------------------------------------------------


def test_compute_input_set_hash_is_order_independent() -> None:
    e1, e2 = uuid4(), uuid4()
    a = compute_input_set_hash([(e1, "yes"), (e2, "no")])
    b = compute_input_set_hash([(e2, "no"), (e1, "yes")])
    assert a == b
    assert len(a) == 64


def test_compute_input_set_hash_changes_with_content() -> None:
    e1, e2 = uuid4(), uuid4()
    a = compute_input_set_hash([(e1, "yes"), (e2, "no")])
    b = compute_input_set_hash([(e1, "yes"), (e2, "yes")])
    assert a != b


def test_compute_input_set_hash_empty_set_is_deterministic() -> None:
    a = compute_input_set_hash([])
    b = compute_input_set_hash([])
    assert a == b


# --- compute_quorum_result (ADR-009 item 5: quorum is optional) --------------


def test_compute_quorum_result_none_threshold_is_not_required() -> None:
    assert (
        compute_quorum_result(accepted_vote_count=0, quorum_threshold=None)
        == QuorumResult.NOT_REQUIRED
    )


def test_compute_quorum_result_met() -> None:
    assert (
        compute_quorum_result(accepted_vote_count=50, quorum_threshold=50)
        == QuorumResult.QUORUM_MET
    )


def test_compute_quorum_result_not_met() -> None:
    assert (
        compute_quorum_result(accepted_vote_count=10, quorum_threshold=50)
        == QuorumResult.QUORUM_NOT_MET
    )


def test_compute_quorum_result_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError, match="quorum_threshold"):
        compute_quorum_result(accepted_vote_count=10, quorum_threshold=-1)


def test_parse_quorum_result_rejects_unknown_value() -> None:
    with pytest.raises(UnknownQuorumResultError):
        parse_quorum_result("half_met")


def test_only_three_quorum_result_values_exist() -> None:
    assert {v.value for v in QuorumResult} == {"quorum_met", "quorum_not_met", "not_required"}


# --- compute_threshold_result / tie -> tie_no_decision (ADR-009 item 11) ----


def test_compute_threshold_result_clear_majority_is_met() -> None:
    assert compute_threshold_result({"yes": 60, "no": 40}) == ThresholdResult.THRESHOLD_MET


def test_compute_threshold_result_plurality_without_majority_is_not_met() -> None:
    """A three-way split where the leader has 40% is `THRESHOLD_NOT_MET`,
    not a false "met" via mere plurality."""
    result = compute_threshold_result({"a": 40, "b": 35, "c": 25})
    assert result == ThresholdResult.THRESHOLD_NOT_MET


def test_compute_threshold_result_tie_is_tie_no_decision() -> None:
    """The dedicated ADR-009 item 11 test: a tied `result_data` must
    produce `TIE_NO_DECISION`, never an arbitrarily-chosen winner."""
    result = compute_threshold_result({"yes": 50, "no": 50})
    assert result == ThresholdResult.TIE_NO_DECISION


def test_compute_threshold_result_three_way_tie_is_tie_no_decision() -> None:
    result = compute_threshold_result({"a": 30, "b": 30, "c": 30})
    assert result == ThresholdResult.TIE_NO_DECISION


def test_compute_threshold_result_empty_is_not_met_not_tie() -> None:
    """ "Nobody voted" is distinct from "a genuine contest ended in a
    tie" - both share a maximum count across all options, but only the
    latter is `TIE_NO_DECISION`."""
    assert compute_threshold_result({}) == ThresholdResult.THRESHOLD_NOT_MET


def test_compute_threshold_result_all_zero_is_not_met_not_tie() -> None:
    assert compute_threshold_result({"yes": 0, "no": 0}) == ThresholdResult.THRESHOLD_NOT_MET


def test_compute_threshold_result_rejects_negative_count() -> None:
    with pytest.raises(ValueError, match="option_counts"):
        compute_threshold_result({"yes": -1})


def test_parse_threshold_result_rejects_unknown_value() -> None:
    with pytest.raises(UnknownThresholdResultError):
        parse_threshold_result("half_met")


def test_only_three_threshold_result_values_exist() -> None:
    assert {v.value for v in ThresholdResult} == {
        "threshold_met",
        "threshold_not_met",
        "tie_no_decision",
    }


# --- challenge_deadline_at / DEFAULT_CHALLENGE_WINDOW_HOURS (ADR-010) --------


def test_default_challenge_window_hours_is_72() -> None:
    assert DEFAULT_CHALLENGE_WINDOW_HOURS == 72


def test_compute_challenge_deadline_uses_default_when_none() -> None:
    deadline = compute_challenge_deadline(_PUBLISHED_AT, None)
    assert deadline == _PUBLISHED_AT + timedelta(hours=72)


def test_compute_challenge_deadline_honors_override() -> None:
    deadline = compute_challenge_deadline(_PUBLISHED_AT, 48)
    assert deadline == _PUBLISHED_AT + timedelta(hours=48)


def test_compute_challenge_deadline_requires_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        compute_challenge_deadline(datetime(2026, 1, 1), None)


def test_compute_challenge_deadline_rejects_non_positive_hours() -> None:
    with pytest.raises(ValueError, match="challenge_window_hours"):
        compute_challenge_deadline(_PUBLISHED_AT, 0)


# --- FinalityState / compute_finality_state (ADR-010's non-finality) --------


def test_finality_state_has_exactly_two_values_neither_meaning_final() -> None:
    """Structural guarantee: `FinalityState` must never gain a third
    member meaning "final" - ADR-010's Owner decision is binding."""
    values = {v.value for v in FinalityState}
    assert values == {"provisional_before_deadline", "provisional_pending_challenge_mechanism"}
    assert "final" not in values
    assert len(FinalityState) == 2


def test_compute_finality_state_before_deadline() -> None:
    result = _make_result()
    now = result.published_at + timedelta(hours=1)
    assert compute_finality_state(result, now) == FinalityState.PROVISIONAL_BEFORE_DEADLINE


def test_compute_finality_state_long_after_deadline_never_implies_finality() -> None:
    """Behavioral test: `now` far beyond `challenge_deadline_at` (years,
    not hours) still returns the pending-challenge-mechanism state, never
    anything implying finality - ADR-010's Owner decision forbids PACK-03
    from ever declaring a result final merely because the deadline
    elapsed."""
    result = _make_result()
    now = result.challenge_deadline_at + timedelta(days=3650)
    state = compute_finality_state(result, now)
    assert state == FinalityState.PROVISIONAL_PENDING_CHALLENGE_MECHANISM
    assert "final" not in state.value


def test_compute_finality_state_exactly_at_deadline_is_pending() -> None:
    result = _make_result()
    state = compute_finality_state(result, result.challenge_deadline_at)
    assert state == FinalityState.PROVISIONAL_PENDING_CHALLENGE_MECHANISM


def test_compute_finality_state_requires_timezone_aware_now() -> None:
    result = _make_result()
    with pytest.raises(ValueError, match="timezone-aware"):
        compute_finality_state(result, datetime(2026, 1, 1))


# --- ResultPublication validation --------------------------------------------


def test_result_publication_requires_timezone_aware_published_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_result(published_at=datetime(2026, 1, 1))


def test_result_publication_rejects_deadline_before_published_at() -> None:
    with pytest.raises(ValueError, match="challenge_deadline_at"):
        _make_result(challenge_deadline_at=_PUBLISHED_AT - timedelta(hours=1))


def test_result_publication_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="eligible_count"):
        _make_result(eligible_count=-1)


def test_result_publication_rejects_empty_audit_package_reference() -> None:
    with pytest.raises(ValueError, match="audit_package_reference"):
        _make_result(audit_package_reference="")


# --- Identity separation (ADR-009 item 15) -----------------------------------


def test_tally_has_no_forbidden_identity_field() -> None:
    field_names = set(Tally.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)
    assert "account_id" not in field_names
    assert "person_id" not in field_names
    assert "identity_record_id" not in field_names


def test_result_publication_has_no_forbidden_identity_field() -> None:
    field_names = set(ResultPublication.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)
    assert "account_id" not in field_names
    assert "person_id" not in field_names
    assert "identity_record_id" not in field_names


def test_forbidden_field_names_is_exactly_the_documented_set() -> None:
    assert frozenset({"account_id", "person_id", "identity_record_id"}) == FORBIDDEN_FIELD_NAMES
