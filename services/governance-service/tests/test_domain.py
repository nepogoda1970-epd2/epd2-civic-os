"""Domain-layer tests for Governance Service: `RoleAssignment`,
`GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge` — canon
section 19b / 8.4. Covers CT-00-02 (unknown status) and CT-00-03
(forbidden transition) for all four entities.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    PILOT_ROLE_CODES,
    FinalityOutcome,
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    GovernancePolicy,
    GovernancePolicyStatus,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
    SubmitterAuthorizationType,
    TechnicalChallenge,
    TechnicalChallengeStatus,
    parse_governance_decision_status,
    parse_governance_policy_status,
    parse_role_assignment_status,
    parse_technical_challenge_status,
    scope_covers,
)
from epd2_governance_service.exceptions import (
    ForbiddenGovernanceDecisionTransitionError,
    ForbiddenGovernancePolicyTransitionError,
    ForbiddenRoleAssignmentTransitionError,
    ForbiddenTechnicalChallengeTransitionError,
    UnknownGovernanceDecisionStatusError,
    UnknownGovernancePolicyStatusError,
    UnknownRoleAssignmentStatusError,
    UnknownTechnicalChallengeStatusError,
)

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _role_assignment(**overrides: object) -> RoleAssignment:
    fields: dict[str, object] = {
        "role_assignment_id": uuid4(),
        "actor_id": uuid4(),
        "role_code": "observer",
        "scope_id": GLOBAL_SCOPE_ID,
        "valid_from": NOW,
        "valid_until": None,
        "assigned_by": uuid4(),
        "approval_reference": None,
        "status": RoleAssignmentStatus.PENDING,
    }
    fields.update(overrides)
    return RoleAssignment(**fields)  # type: ignore[arg-type]


def _policy(**overrides: object) -> GovernancePolicy:
    fields: dict[str, object] = {
        "governance_policy_id": uuid4(),
        "policy_type": GovernancePolicyType.ROLE_TAXONOMY,
        "rule_definition": {"allowed_role_codes": sorted(PILOT_ROLE_CODES)},
        "effective_from": NOW,
        "proposed_by_role_id": uuid4(),
        "approved_by_role_id": uuid4(),
        "version": 1,
        "status": GovernancePolicyStatus.DRAFT,
    }
    fields.update(overrides)
    return GovernancePolicy(**fields)  # type: ignore[arg-type]


def _decision(**overrides: object) -> GovernanceDecision:
    fields: dict[str, object] = {
        "governance_decision_id": uuid4(),
        "decision_type": GovernanceDecisionType.BALLOT_INVALIDATION,
        "subject_reference": {"ballot_id": str(uuid4())},
        "proposed_by_role_id": uuid4(),
        "approved_by_role_id": None,
        "rejected_by_role_id": None,
        "reason_code": "TEST_REASON",
        "evidence_references": (),
        "finality_outcome": None,
        "created_at": NOW,
        "decided_at": None,
        "supersedes_decision_id": None,
        "status": GovernanceDecisionStatus.PROPOSED,
    }
    fields.update(overrides)
    return GovernanceDecision(**fields)  # type: ignore[arg-type]


def _challenge(**overrides: object) -> TechnicalChallenge:
    fields: dict[str, object] = {
        "technical_challenge_id": uuid4(),
        "result_publication_id": uuid4(),
        "submitter_authorization_type": SubmitterAuthorizationType.PARTICIPATION_CREDENTIAL,
        "submitter_authorization_reference": "opaque-ref",
        "challenge_reason_code": "TEST_CHALLENGE",
        "evidence_references": (),
        "submitted_at": NOW,
        "governance_decision_id": None,
        "status": TechnicalChallengeStatus.SUBMITTED,
    }
    fields.update(overrides)
    return TechnicalChallenge(**fields)  # type: ignore[arg-type]


# --- scope_covers ------------------------------------------------------------


def test_scope_covers_exact_match() -> None:
    scope_id = uuid4()
    assert scope_covers(scope_id, scope_id) is True


def test_scope_covers_global() -> None:
    assert scope_covers(GLOBAL_SCOPE_ID, uuid4()) is True


def test_scope_covers_mismatch() -> None:
    assert scope_covers(uuid4(), uuid4()) is False


# --- RoleAssignment -----------------------------------------------------------


def test_role_assignment_unknown_status_rejected() -> None:
    with pytest.raises(UnknownRoleAssignmentStatusError):
        parse_role_assignment_status("not-a-status")


def test_role_assignment_forbidden_transition_rejected() -> None:
    assignment = _role_assignment(status=RoleAssignmentStatus.REVOKED)
    with pytest.raises(ForbiddenRoleAssignmentTransitionError):
        assignment.with_status(RoleAssignmentStatus.ACTIVE)


def test_role_assignment_allowed_transition() -> None:
    assignment = _role_assignment(status=RoleAssignmentStatus.PENDING)
    activated = assignment.with_status(RoleAssignmentStatus.ACTIVE)
    assert activated.status is RoleAssignmentStatus.ACTIVE
    assert activated.role_assignment_id == assignment.role_assignment_id


def test_role_assignment_requires_tz_aware_valid_from() -> None:
    with pytest.raises(ValueError, match="valid_from"):
        _role_assignment(valid_from=datetime(2026, 7, 23, 12, 0))


def test_role_assignment_valid_until_must_be_after_valid_from() -> None:
    with pytest.raises(ValueError, match="valid_until"):
        _role_assignment(valid_from=NOW, valid_until=NOW - timedelta(days=1))


def test_role_assignment_is_active_at() -> None:
    assignment = _role_assignment(
        status=RoleAssignmentStatus.ACTIVE, valid_from=NOW, valid_until=NOW + timedelta(days=1)
    )
    assert assignment.is_active_at(NOW) is True
    assert assignment.is_active_at(NOW + timedelta(days=2)) is False
    assert assignment.is_active_at(NOW - timedelta(days=1)) is False


def test_role_assignment_empty_role_code_rejected() -> None:
    with pytest.raises(ValueError, match="role_code"):
        _role_assignment(role_code="")


# --- GovernancePolicy ---------------------------------------------------------


def test_governance_policy_unknown_status_rejected() -> None:
    with pytest.raises(UnknownGovernancePolicyStatusError):
        parse_governance_policy_status("not-a-status")


def test_governance_policy_forbidden_transition_rejected() -> None:
    policy = _policy(status=GovernancePolicyStatus.SUPERSEDED)
    with pytest.raises(ForbiddenGovernancePolicyTransitionError):
        policy.with_status(GovernancePolicyStatus.ACTIVE)


def test_governance_policy_allowed_transition() -> None:
    policy = _policy(status=GovernancePolicyStatus.DRAFT)
    activated = policy.with_status(GovernancePolicyStatus.ACTIVE)
    assert activated.status is GovernancePolicyStatus.ACTIVE


def test_governance_policy_rejects_same_actor_proposer_approver_ids() -> None:
    same_id = uuid4()
    with pytest.raises(ValueError, match="approved_by_role_id must differ"):
        _policy(proposed_by_role_id=same_id, approved_by_role_id=same_id)


def test_governance_policy_requires_version_ge_1() -> None:
    with pytest.raises(ValueError, match="version"):
        _policy(version=0)


# --- GovernanceDecision --------------------------------------------------------


def test_governance_decision_unknown_status_rejected() -> None:
    with pytest.raises(UnknownGovernanceDecisionStatusError):
        parse_governance_decision_status("not-a-status")


def test_governance_decision_forbidden_transition_rejected() -> None:
    decision = _decision(
        status=GovernanceDecisionStatus.APPROVED,
        approved_by_role_id=uuid4(),
        decided_at=NOW,
    )
    with pytest.raises(ForbiddenGovernanceDecisionTransitionError):
        decision.with_rejected(rejected_by_role_id=uuid4(), decided_at=NOW)


def test_governance_decision_approve() -> None:
    decision = _decision()
    approved = decision.with_approved(
        approved_by_role_id=uuid4(), decided_at=NOW, finality_outcome=None
    )
    assert approved.status is GovernanceDecisionStatus.APPROVED
    assert approved.decided_at == NOW


def test_governance_decision_reject() -> None:
    decision = _decision()
    rejected = decision.with_rejected(rejected_by_role_id=uuid4(), decided_at=NOW)
    assert rejected.status is GovernanceDecisionStatus.REJECTED


def test_governance_decision_no_superseded_stored_value() -> None:
    assert "superseded" not in {s.value for s in GovernanceDecisionStatus}


def test_governance_decision_finality_outcome_requires_result_finality_type() -> None:
    with pytest.raises(ValueError, match="finality_outcome"):
        _decision(
            decision_type=GovernanceDecisionType.BALLOT_INVALIDATION,
            status=GovernanceDecisionStatus.APPROVED,
            approved_by_role_id=uuid4(),
            decided_at=NOW,
            finality_outcome=FinalityOutcome.FINAL,
        )


def test_governance_decision_finality_outcome_requires_approved_status() -> None:
    with pytest.raises(ValueError, match="finality_outcome"):
        _decision(
            decision_type=GovernanceDecisionType.RESULT_FINALITY_DETERMINATION,
            subject_reference={"result_publication_id": str(uuid4())},
            status=GovernanceDecisionStatus.PROPOSED,
            finality_outcome=FinalityOutcome.FINAL,
        )


def test_governance_decision_rejects_vote_envelope_subject_reference() -> None:
    with pytest.raises(ValueError, match="VoteEnvelope"):
        _decision(subject_reference={"vote_envelope_id": str(uuid4())})


def test_governance_decision_approved_by_must_differ_from_proposed_by() -> None:
    same_id = uuid4()
    with pytest.raises(ValueError, match="differ"):
        _decision(
            proposed_by_role_id=same_id,
            approved_by_role_id=same_id,
            status=GovernanceDecisionStatus.APPROVED,
            decided_at=NOW,
        )


def test_governance_decision_decided_at_consistency() -> None:
    with pytest.raises(ValueError, match="decided_at"):
        _decision(status=GovernanceDecisionStatus.PROPOSED, decided_at=NOW)


# --- TechnicalChallenge --------------------------------------------------------


def test_technical_challenge_unknown_status_rejected() -> None:
    with pytest.raises(UnknownTechnicalChallengeStatusError):
        parse_technical_challenge_status("not-a-status")


def test_technical_challenge_forbidden_transition_rejected() -> None:
    challenge = _challenge(status=TechnicalChallengeStatus.UPHELD, governance_decision_id=uuid4())
    with pytest.raises(ForbiddenTechnicalChallengeTransitionError):
        challenge.with_status(TechnicalChallengeStatus.UNDER_REVIEW)


def test_technical_challenge_allowed_transition() -> None:
    challenge = _challenge(status=TechnicalChallengeStatus.SUBMITTED)
    under_review = challenge.with_status(TechnicalChallengeStatus.UNDER_REVIEW)
    assert under_review.status is TechnicalChallengeStatus.UNDER_REVIEW
    upheld = under_review.with_status(
        TechnicalChallengeStatus.UPHELD, governance_decision_id=uuid4()
    )
    assert upheld.status is TechnicalChallengeStatus.UPHELD
    assert upheld.governance_decision_id is not None


def test_technical_challenge_terminal_status_requires_governance_decision_id() -> None:
    with pytest.raises(ValueError, match="governance_decision_id"):
        _challenge(status=TechnicalChallengeStatus.UPHELD, governance_decision_id=None)


def test_technical_challenge_empty_authorization_reference_rejected() -> None:
    with pytest.raises(ValueError, match="submitter_authorization_reference"):
        _challenge(submitter_authorization_reference="")
