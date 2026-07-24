"""Application-layer tests for Governance Service. Covers CT-00-04
(event idempotency), CT-00-06 (missing permission), CT-00-07 (audit
creation), CT-00-08 (identity leakage — no `*_role_id`/`actor_id` in
public payloads), plus the pack's own two-actor approval, superseding,
and multiple-challenge/finality rules (ADR-020, canon 19b.5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_governance_service import application as app
from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    FinalityOutcome,
    FinalityStatus,
    GovernanceDecisionType,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
    SubmitterAuthorizationType,
)
from epd2_governance_service.events import (
    governance_decision_public_payload,
    governance_policy_public_payload,
    role_assignment_public_payload,
    technical_challenge_public_payload,
)
from epd2_governance_service.exceptions import (
    ResultFinalityBlockedByOpenChallengeError,
    ResultFinalityDeterminationDuplicateError,
    SameActorApprovalRejectedError,
    TechnicalChallengeSubmitterIneligibleError,
    TechnicalChallengeWindowClosedError,
)
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
    InMemoryGovernancePolicyStore,
    InMemoryRoleAssignmentStore,
    InMemoryTechnicalChallengeStore,
)
from epd2_tally_service.domain import QuorumResult, ResultPublication, ThresholdResult
from epd2_tally_service.storage import InMemoryResultPublicationStore

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
ACTOR = ActorRef(actor_id=uuid4(), actor_type="user")


class Fixture:
    def __init__(self) -> None:
        self.clock = FixedClock(NOW)
        self.audit_store = InMemoryAuditEventStore()
        self.role_store = InMemoryRoleAssignmentStore()
        self.policy_store = InMemoryGovernancePolicyStore()
        self.decision_store = InMemoryGovernanceDecisionStore()
        self.challenge_store = InMemoryTechnicalChallengeStore()
        self.result_publication_store = InMemoryResultPublicationStore()

    def grant_active_role(
        self, role_code: str, *, scope_id: UUID = GLOBAL_SCOPE_ID
    ) -> RoleAssignment:
        assignment = self.role_store.create(
            _direct_role_assignment(role_code=role_code, scope_id=scope_id)
        )
        return assignment


def _direct_role_assignment(*, role_code: str, scope_id: UUID) -> RoleAssignment:
    return RoleAssignment(
        role_assignment_id=uuid4(),
        actor_id=uuid4(),
        role_code=role_code,
        scope_id=scope_id,
        valid_from=NOW,
        valid_until=None,
        assigned_by=uuid4(),
        approval_reference=None,
        status=RoleAssignmentStatus.ACTIVE,
    )


@pytest.fixture
def fx() -> Fixture:
    return Fixture()


# --- RoleAssignment commands ---------------------------------------------------


def test_request_role_assignment_permission_denied(fx: Fixture) -> None:
    granter = fx.grant_active_role("oversight_reviewer")
    with pytest.raises(app.PermissionDeniedError):
        app.request_role_assignment(
            fx.role_store,
            fx.audit_store,
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="observer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=NOW,
            valid_until=None,
            granter_role_assignment_id=granter.role_assignment_id,
            approval_reference=None,
            actor=ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_request_role_assignment_rejects_self_grant(fx: Fixture) -> None:
    granter = fx.grant_active_role("oversight_reviewer")
    with pytest.raises(SameActorApprovalRejectedError):
        app.request_role_assignment(
            fx.role_store,
            fx.audit_store,
            role_assignment_id=uuid4(),
            actor_id=granter.actor_id,
            role_code="observer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=NOW,
            valid_until=None,
            granter_role_assignment_id=granter.role_assignment_id,
            approval_reference=None,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_request_activate_revoke_role_assignment_lifecycle_and_audit(fx: Fixture) -> None:
    granter = fx.grant_active_role("oversight_reviewer")
    assignment_id = uuid4()
    result = app.request_role_assignment(
        fx.role_store,
        fx.audit_store,
        role_assignment_id=assignment_id,
        actor_id=uuid4(),
        role_code="observer",
        scope_id=GLOBAL_SCOPE_ID,
        valid_from=NOW,
        valid_until=None,
        granter_role_assignment_id=granter.role_assignment_id,
        approval_reference="grant-1",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.assignment.status.value == "pending"
    assert result.audit_event.target_id == assignment_id

    activated = app.activate_role_assignment(
        fx.role_store,
        fx.audit_store,
        role_assignment_id=assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert activated.assignment.status.value == "active"

    revoked = app.revoke_role_assignment(
        fx.role_store,
        fx.audit_store,
        role_assignment_id=assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert revoked.assignment.status.value == "revoked"


def test_request_role_assignment_idempotent_replay(fx: Fixture) -> None:
    granter = fx.grant_active_role("oversight_reviewer")
    event_id = uuid4()
    assignment_id = uuid4()
    kwargs = dict(
        role_assignment_id=assignment_id,
        actor_id=uuid4(),
        role_code="observer",
        scope_id=GLOBAL_SCOPE_ID,
        valid_from=NOW,
        valid_until=None,
        granter_role_assignment_id=granter.role_assignment_id,
        approval_reference=None,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
        event_id=event_id,
    )
    first = app.request_role_assignment(fx.role_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    second = app.request_role_assignment(fx.role_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert first.assignment == second.assignment


def test_role_assignment_public_payload_omits_actor_and_assigned_by(fx: Fixture) -> None:
    assignment = fx.grant_active_role("observer")
    payload = role_assignment_public_payload(assignment)
    assert "actor_id" not in payload
    assert "assigned_by" not in payload


# --- GovernancePolicy commands --------------------------------------------------


def test_propose_and_activate_governance_policy_supersedes_prior(fx: Fixture) -> None:
    proposer = fx.grant_active_role("governance_policy_proposer")
    approver = fx.grant_active_role("governance_policy_approver")

    first = app.propose_governance_policy(
        fx.policy_store,
        fx.role_store,
        fx.audit_store,
        governance_policy_id=uuid4(),
        policy_type=GovernancePolicyType.ROLE_TAXONOMY,
        rule_definition={"v": 1},
        effective_from=NOW,
        proposed_by_role_id=proposer.role_assignment_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    activated_first = app.activate_governance_policy(
        fx.policy_store,
        fx.role_store,
        fx.audit_store,
        governance_policy_id=first.policy.governance_policy_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert activated_first.policy.status.value == "active"
    assert activated_first.superseded_policy is None

    second = app.propose_governance_policy(
        fx.policy_store,
        fx.role_store,
        fx.audit_store,
        governance_policy_id=uuid4(),
        policy_type=GovernancePolicyType.ROLE_TAXONOMY,
        rule_definition={"v": 2},
        effective_from=NOW,
        proposed_by_role_id=proposer.role_assignment_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert second.policy.version == 2

    activated_second = app.activate_governance_policy(
        fx.policy_store,
        fx.role_store,
        fx.audit_store,
        governance_policy_id=second.policy.governance_policy_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert activated_second.superseded_policy is not None
    assert activated_second.superseded_policy.status.value == "superseded"


def test_governance_policy_public_payload_omits_role_ids(fx: Fixture) -> None:
    proposer = fx.grant_active_role("governance_policy_proposer")
    approver = fx.grant_active_role("governance_policy_approver")
    result = app.propose_governance_policy(
        fx.policy_store,
        fx.role_store,
        fx.audit_store,
        governance_policy_id=uuid4(),
        policy_type=GovernancePolicyType.APPROVAL_RULE,
        rule_definition={},
        effective_from=NOW,
        proposed_by_role_id=proposer.role_assignment_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    payload = governance_policy_public_payload(result.policy)
    assert "proposed_by_role_id" not in payload
    assert "approved_by_role_id" not in payload


# --- GovernanceDecision commands -------------------------------------------------


def _propose_ballot_invalidation(
    fx: Fixture, proposer_role: RoleAssignment, ballot_id: UUID
) -> app.GovernanceDecisionResult:
    return app.propose_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.BALLOT_INVALIDATION,
        subject_reference={"ballot_id": str(ballot_id)},
        proposed_by_role_id=proposer_role.role_assignment_id,
        reason_code="TEST",
        evidence_references=[],
        supersedes_decision_id=None,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )


def test_propose_and_approve_governance_decision(fx: Fixture) -> None:
    ballot_id = uuid4()
    proposer = fx.grant_active_role("ballot_invalidation_proposer", scope_id=ballot_id)
    approver = fx.grant_active_role("ballot_invalidation_approver", scope_id=ballot_id)

    proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)
    assert proposed.decision.status.value == "proposed"

    approved = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=proposed.decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert approved.decision.status.value == "approved"
    assert app.is_current_approved_decision(fx.decision_store, approved.decision) is True


def test_approve_governance_decision_rejects_same_actor(fx: Fixture) -> None:
    ballot_id = uuid4()
    from epd2_governance_service.domain import RoleAssignment, RoleAssignmentStatus

    same_actor = uuid4()
    proposer = fx.role_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=same_actor,
            role_code="ballot_invalidation_proposer",
            scope_id=ballot_id,
            valid_from=NOW,
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    approver = fx.role_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=same_actor,
            role_code="ballot_invalidation_approver",
            scope_id=ballot_id,
            valid_from=NOW,
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)
    with pytest.raises(SameActorApprovalRejectedError):
        app.approve_governance_decision(
            fx.decision_store,
            fx.role_store,
            fx.challenge_store,
            fx.audit_store,
            governance_decision_id=proposed.decision.governance_decision_id,
            approved_by_role_id=approver.role_assignment_id,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_reject_governance_decision(fx: Fixture) -> None:
    ballot_id = uuid4()
    proposer = fx.grant_active_role("ballot_invalidation_proposer", scope_id=ballot_id)
    rejecter = fx.grant_active_role("ballot_invalidation_approver", scope_id=ballot_id)
    proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)

    rejected = app.reject_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=proposed.decision.governance_decision_id,
        rejected_by_role_id=rejecter.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert rejected.decision.status.value == "rejected"


def test_approve_governance_decision_idempotent_replay(fx: Fixture) -> None:
    ballot_id = uuid4()
    proposer = fx.grant_active_role("ballot_invalidation_proposer", scope_id=ballot_id)
    approver = fx.grant_active_role("ballot_invalidation_approver", scope_id=ballot_id)
    proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)
    event_id = uuid4()

    first = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=proposed.decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
        event_id=event_id,
    )
    second = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=proposed.decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
        event_id=event_id,
    )
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


def test_governance_decision_public_payload_omits_role_ids(fx: Fixture) -> None:
    ballot_id = uuid4()
    proposer = fx.grant_active_role("ballot_invalidation_proposer", scope_id=ballot_id)
    proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)
    payload = governance_decision_public_payload(proposed.decision)
    assert "proposed_by_role_id" not in payload
    assert "approved_by_role_id" not in payload
    assert "rejected_by_role_id" not in payload


def test_decision_superseding_emits_superseded_event(fx: Fixture) -> None:
    ballot_id = uuid4()
    proposer = fx.grant_active_role("ballot_invalidation_proposer", scope_id=ballot_id)
    approver = fx.grant_active_role("ballot_invalidation_approver", scope_id=ballot_id)

    first_proposed = _propose_ballot_invalidation(fx, proposer, ballot_id)
    first_approved = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=first_proposed.decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )

    second_proposed = app.propose_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.BALLOT_INVALIDATION,
        subject_reference={"ballot_id": str(ballot_id)},
        proposed_by_role_id=proposer.role_assignment_id,
        reason_code="CORRECTION",
        evidence_references=[],
        supersedes_decision_id=first_approved.decision.governance_decision_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    second_approved = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=second_proposed.decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert second_approved.superseded_decision is not None
    assert second_approved.superseded_event is not None
    assert second_approved.superseded_event.event_type == "governance.decision_superseded"
    assert app.is_current_approved_decision(fx.decision_store, first_approved.decision) is False


# --- TechnicalChallenge + result finality ----------------------------------------


def _seed_result_publication(fx: Fixture, *, challenge_deadline_at: datetime) -> ResultPublication:
    result_publication = ResultPublication(
        result_publication_id=uuid4(),
        ballot_id=uuid4(),
        tally_id=uuid4(),
        eligible_count=100,
        credential_count=100,
        accepted_vote_count=60,
        rejected_vote_count=2,
        quorum_result=QuorumResult.QUORUM_MET,
        threshold_result=ThresholdResult.THRESHOLD_MET,
        published_at=NOW - timedelta(days=1),
        audit_package_reference="ref-1",
        challenge_deadline_at=challenge_deadline_at,
    )
    fx.result_publication_store.create(result_publication)
    return result_publication


def test_submit_technical_challenge_role_assignment_path(fx: Fixture) -> None:
    result_publication = _seed_result_publication(fx, challenge_deadline_at=NOW + timedelta(days=1))
    reviewer = fx.grant_active_role(
        "technical_challenge_reviewer", scope_id=result_publication.result_publication_id
    )
    result = app.submit_technical_challenge(
        fx.challenge_store,
        fx.role_store,
        fx.result_publication_store,
        fx.audit_store,
        technical_challenge_id=uuid4(),
        result_publication_id=result_publication.result_publication_id,
        submitter_authorization_type=SubmitterAuthorizationType.ROLE_ASSIGNMENT,
        submitter_authorization_reference=str(reviewer.role_assignment_id),
        challenge_reason_code="INTEGRITY_CONCERN",
        evidence_references=["evidence"],
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.challenge.status.value == "submitted"


def test_submit_technical_challenge_participation_credential_path_never_dereferenced(
    fx: Fixture,
) -> None:
    result_publication = _seed_result_publication(fx, challenge_deadline_at=NOW + timedelta(days=1))
    result = app.submit_technical_challenge(
        fx.challenge_store,
        fx.role_store,
        fx.result_publication_store,
        fx.audit_store,
        technical_challenge_id=uuid4(),
        result_publication_id=result_publication.result_publication_id,
        submitter_authorization_type=SubmitterAuthorizationType.PARTICIPATION_CREDENTIAL,
        submitter_authorization_reference="opaque-commitment-value",
        challenge_reason_code="INTEGRITY_CONCERN",
        evidence_references=[],
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.challenge.status.value == "submitted"


def test_submit_technical_challenge_rejects_ineligible_role_assignment(fx: Fixture) -> None:
    result_publication = _seed_result_publication(fx, challenge_deadline_at=NOW + timedelta(days=1))
    other_scope_reviewer = fx.grant_active_role("technical_challenge_reviewer", scope_id=uuid4())
    with pytest.raises(TechnicalChallengeSubmitterIneligibleError):
        app.submit_technical_challenge(
            fx.challenge_store,
            fx.role_store,
            fx.result_publication_store,
            fx.audit_store,
            technical_challenge_id=uuid4(),
            result_publication_id=result_publication.result_publication_id,
            submitter_authorization_type=SubmitterAuthorizationType.ROLE_ASSIGNMENT,
            submitter_authorization_reference=str(other_scope_reviewer.role_assignment_id),
            challenge_reason_code="INTEGRITY_CONCERN",
            evidence_references=[],
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_submit_technical_challenge_rejects_after_deadline(fx: Fixture) -> None:
    result_publication = _seed_result_publication(
        fx, challenge_deadline_at=NOW - timedelta(hours=1)
    )
    with pytest.raises(TechnicalChallengeWindowClosedError):
        app.submit_technical_challenge(
            fx.challenge_store,
            fx.role_store,
            fx.result_publication_store,
            fx.audit_store,
            technical_challenge_id=uuid4(),
            result_publication_id=result_publication.result_publication_id,
            submitter_authorization_type=SubmitterAuthorizationType.PARTICIPATION_CREDENTIAL,
            submitter_authorization_reference="opaque",
            challenge_reason_code="TOO_LATE",
            evidence_references=[],
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_technical_challenge_public_payload_omits_authorization_reference(fx: Fixture) -> None:
    result_publication = _seed_result_publication(fx, challenge_deadline_at=NOW + timedelta(days=1))
    result = app.submit_technical_challenge(
        fx.challenge_store,
        fx.role_store,
        fx.result_publication_store,
        fx.audit_store,
        technical_challenge_id=uuid4(),
        result_publication_id=result_publication.result_publication_id,
        submitter_authorization_type=SubmitterAuthorizationType.PARTICIPATION_CREDENTIAL,
        submitter_authorization_reference="opaque-commitment-value",
        challenge_reason_code="INTEGRITY_CONCERN",
        evidence_references=[],
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    payload = technical_challenge_public_payload(result.challenge)
    assert "submitter_authorization_reference" not in payload


def test_finality_blocked_while_challenge_unresolved_then_approved(fx: Fixture) -> None:
    result_publication = _seed_result_publication(fx, challenge_deadline_at=NOW + timedelta(days=1))
    proposer = fx.grant_active_role(
        "technical_challenge_reviewer", scope_id=result_publication.result_publication_id
    )
    reviewer_finality = fx.grant_active_role(
        "governance_reviewer", scope_id=result_publication.result_publication_id
    )

    submitted = app.submit_technical_challenge(
        fx.challenge_store,
        fx.role_store,
        fx.result_publication_store,
        fx.audit_store,
        technical_challenge_id=uuid4(),
        result_publication_id=result_publication.result_publication_id,
        submitter_authorization_type=SubmitterAuthorizationType.ROLE_ASSIGNMENT,
        submitter_authorization_reference=str(proposer.role_assignment_id),
        challenge_reason_code="INTEGRITY_CONCERN",
        evidence_references=[],
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )

    status = app.get_finality_status(
        fx.decision_store,
        fx.challenge_store,
        result_publication_id=result_publication.result_publication_id,
    )
    assert status is FinalityStatus.FINALITY_BLOCKED

    # Result finality proposal is blocked while the challenge is unresolved.
    with pytest.raises(ResultFinalityBlockedByOpenChallengeError):
        app.propose_governance_decision(
            fx.decision_store,
            fx.role_store,
            fx.challenge_store,
            fx.audit_store,
            governance_decision_id=uuid4(),
            decision_type=GovernanceDecisionType.RESULT_FINALITY_DETERMINATION,
            subject_reference={
                "result_publication_id": str(result_publication.result_publication_id)
            },
            proposed_by_role_id=reviewer_finality.role_assignment_id,
            reason_code="FINALITY",
            evidence_references=[],
            supersedes_decision_id=None,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )

    app.begin_technical_challenge_review(
        fx.challenge_store,
        fx.audit_store,
        technical_challenge_id=submitted.challenge.technical_challenge_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )

    adjudication_proposed = app.propose_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.TECHNICAL_CHALLENGE_ADJUDICATION,
        subject_reference={
            "technical_challenge_id": str(submitted.challenge.technical_challenge_id)
        },
        proposed_by_role_id=proposer.role_assignment_id,
        reason_code="ADJUDICATION",
        evidence_references=[],
        supersedes_decision_id=None,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    adjudication_approved = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=adjudication_proposed.decision.governance_decision_id,
        approved_by_role_id=reviewer_finality.role_assignment_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert adjudication_approved.challenge is not None
    assert adjudication_approved.challenge.status.value == "upheld"
    assert adjudication_approved.challenge_event is not None
    assert (
        adjudication_approved.challenge_event.event_type
        == "governance.technical_challenge_adjudicated"
    )

    status_after = app.get_finality_status(
        fx.decision_store,
        fx.challenge_store,
        result_publication_id=result_publication.result_publication_id,
    )
    assert status_after is FinalityStatus.PROVISIONAL

    finality_proposed = app.propose_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.RESULT_FINALITY_DETERMINATION,
        subject_reference={"result_publication_id": str(result_publication.result_publication_id)},
        proposed_by_role_id=reviewer_finality.role_assignment_id,
        reason_code="FINALITY",
        evidence_references=[],
        supersedes_decision_id=None,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    oversight_role = fx.grant_active_role(
        "oversight_reviewer", scope_id=result_publication.result_publication_id
    )
    finality_approved = app.approve_governance_decision(
        fx.decision_store,
        fx.role_store,
        fx.challenge_store,
        fx.audit_store,
        governance_decision_id=finality_proposed.decision.governance_decision_id,
        approved_by_role_id=oversight_role.role_assignment_id,
        finality_outcome=FinalityOutcome.FINAL,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert finality_approved.decision.finality_outcome is FinalityOutcome.FINAL

    final_status = app.get_finality_status(
        fx.decision_store,
        fx.challenge_store,
        result_publication_id=result_publication.result_publication_id,
    )
    assert final_status is FinalityStatus.FINAL

    # A second, independent result_finality_determination is rejected
    # already at proposal time (the fast-feedback check).
    with pytest.raises(ResultFinalityDeterminationDuplicateError):
        app.propose_governance_decision(
            fx.decision_store,
            fx.role_store,
            fx.challenge_store,
            fx.audit_store,
            governance_decision_id=uuid4(),
            decision_type=GovernanceDecisionType.RESULT_FINALITY_DETERMINATION,
            subject_reference={
                "result_publication_id": str(result_publication.result_publication_id)
            },
            proposed_by_role_id=reviewer_finality.role_assignment_id,
            reason_code="DUPLICATE_ATTEMPT",
            evidence_references=[],
            supersedes_decision_id=None,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_get_finality_status_provisional_when_nothing_recorded(fx: Fixture) -> None:
    status = app.get_finality_status(
        fx.decision_store, fx.challenge_store, result_publication_id=uuid4()
    )
    assert status is FinalityStatus.PROVISIONAL
