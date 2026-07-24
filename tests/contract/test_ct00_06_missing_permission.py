"""CT-00-06 Missing Permission (canon section 27): an action without
authorization is rejected, for every service's critical commands."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_account_service.application import PermissionDeniedError as AccountPermissionDeniedError
from epd2_account_service.application import change_account_status, create_account
from epd2_account_service.domain import AccountStatus
from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import (
    PermissionDeniedError as CredentialPermissionDeniedError,
)
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import (
    PermissionDeniedError as EligibilityPermissionDeniedError,
)
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
    evaluate_eligibility,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_governance_service.application import (
    activate_governance_policy,
    propose_governance_policy,
)
from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    GovernancePolicyStatus,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
)
from epd2_governance_service.exceptions import SameActorApprovalRejectedError
from epd2_governance_service.storage import (
    InMemoryGovernancePolicyStore,
    InMemoryRoleAssignmentStore,
)
from epd2_identity_service.application import (
    PermissionDeniedError as IdentityPermissionDeniedError,
)
from epd2_identity_service.application import (
    record_verification_result,
    start_identity_verification,
)
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_moderation_service.application import (
    PermissionDeniedError as ModerationPermissionDeniedError,
)
from epd2_moderation_service.application import (
    assign_moderator,
    decide_appeal,
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
from epd2_moderation_service.storage import (
    InMemoryAppealStore,
    InMemoryModerationCaseStore,
    InMemoryModerationDecisionStore,
)
from epd2_voting_service.application import (
    PermissionDeniedError as VotingPermissionDeniedError,
)
from epd2_voting_service.application import (
    approve_ballot_configuration,
    create_ballot,
    submit_ballot_for_configuration_review,
)
from epd2_voting_service.domain import BallotMethod, BallotStatus
from epd2_voting_service.storage import InMemoryBallotStore


def test_account_status_change_without_permission_is_denied(
    account_store: InMemoryAccountStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    created = create_account(
        account_store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    ).account
    with pytest.raises(AccountPermissionDeniedError) as excinfo:
        change_account_status(
            account_store,
            audit_store,
            account_id=created.account_id,
            target_status=AccountStatus.ACTIVE,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_identity_verification_result_without_permission_is_denied(
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    record = start_identity_verification(
        identity_store,
        audit_store,
        account_id=uuid4(),
        verification_provider="p",
        verification_level="basic",
        country="DE",
        provider_reference="r",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    ).record
    with pytest.raises(IdentityPermissionDeniedError) as excinfo:
        record_verification_result(
            identity_store,
            audit_store,
            identity_record_id=record.identity_record_id,
            outcome=VerificationStatus.VERIFIED,
            expires_at=None,
            duplicate_check_status=None,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_eligibility_evaluation_without_permission_is_denied(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_decision_store: InMemoryEligibilityDecisionStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    with pytest.raises(EligibilityPermissionDeniedError) as excinfo:
        evaluate_eligibility(
            eligibility_rule_store,
            eligibility_decision_store,
            audit_store,
            eligibility_rule_id=rule.eligibility_rule_id,
            rule_version=1,
            subject_reference=uuid4(),
            process_id=uuid4(),
            evaluated_claims={"membership_status": "active", "verification_level": "basic"},
            evaluator_version="1.0",
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_credential_issuance_without_permission_is_denied(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    with pytest.raises(CredentialPermissionDeniedError) as excinfo:
        issue_participation_credential(
            credential_store,
            audit_store,
            credential_id=uuid4(),
            credential_type=CredentialType.SPACE_ACCESS,
            scope_type="civic_space",
            scope_id=uuid4(),
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
            expires_at=datetime(2027, 1, 1, tzinfo=UTC),
            usage_limit=None,
            rule_version=1,
            eligibility_snapshot_digest="a" * 64,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


# =============================================================================
# PACK-03: the two flagship CT-00-06 authorization tests named explicitly by
# the pack spec - moderation-service's `decide_appeal` (a reviewer must
# differ from the original decision's `decided_by`, canon section 14.3) and
# voting-service's `approve_ballot_configuration` (the approving actor must
# differ from the ballot's own creator, ADR-009 item 7 / INV-08). Each has a
# rejection case and a real, end-to-end success case for the "different
# actor" path, so the check is proven to be about *identity*, not a blanket
# permission failure.
# =============================================================================


def _issued_decision(
    case_store: InMemoryModerationCaseStore,
    decision_store: InMemoryModerationDecisionStore,
    audit_store: InMemoryAuditEventStore,
    *,
    decided_by: UUID,
    actor: ActorRef,
    clock: FixedClock,
) -> tuple[UUID, UUID]:
    """Real `open -> under_review -> action_proposed -> decided` chain,
    landing a real `ModerationDecision` whose `decided_by` is
    caller-specified - `decide_appeal`'s own reviewer-identity check
    needs a real prior decision to compare `reviewer_actor_id` against.
    Returns `(moderation_case_id, moderation_decision_id)`."""
    case_id = uuid4()
    open_moderation_case(
        case_store,
        audit_store,
        moderation_case_id=case_id,
        target_type="contribution",
        target_id=uuid4(),
        opened_by=uuid4(),
        trigger_type="report",
        policy_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assign_moderator(
        case_store,
        audit_store,
        moderation_case_id=case_id,
        moderator_id=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    propose_action(
        case_store,
        audit_store,
        moderation_case_id=case_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    decision_id = uuid4()
    issue_decision(
        case_store,
        decision_store,
        audit_store,
        moderation_case_id=case_id,
        moderation_decision_id=decision_id,
        decision_type=ModerationDecisionType.WARNING,
        reason_code="MODERATION_POLICY_VIOLATION",
        policy_reference="policy-1",
        decided_by=decided_by,
        effective_from=clock.now(),
        effective_until=None,
        public_explanation="explanation",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return case_id, decision_id


def test_decide_appeal_rejects_the_original_decider_as_reviewer(
    moderation_case_store: InMemoryModerationCaseStore,
    moderation_decision_store: InMemoryModerationDecisionStore,
    appeal_store: InMemoryAppealStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    decider_id = uuid4()
    _case_id, decision_id = _issued_decision(
        moderation_case_store,
        moderation_decision_store,
        audit_store,
        decided_by=decider_id,
        actor=actor,
        clock=clock,
    )
    appeal_id = uuid4()
    submit_appeal(
        moderation_case_store,
        moderation_decision_store,
        appeal_store,
        audit_store,
        appeal_id=appeal_id,
        decision_id=decision_id,
        submitted_by=uuid4(),
        grounds="the decision was wrong",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(ModerationPermissionDeniedError) as excinfo:
        decide_appeal(
            moderation_case_store,
            moderation_decision_store,
            appeal_store,
            audit_store,
            appeal_id=appeal_id,
            reviewer_actor_id=decider_id,
            outcome=AppealStatus.REJECTED,
            result="not upheld",
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_decide_appeal_succeeds_for_a_different_reviewer(
    moderation_case_store: InMemoryModerationCaseStore,
    moderation_decision_store: InMemoryModerationDecisionStore,
    appeal_store: InMemoryAppealStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    decider_id = uuid4()
    reviewer_id = uuid4()
    _case_id, decision_id = _issued_decision(
        moderation_case_store,
        moderation_decision_store,
        audit_store,
        decided_by=decider_id,
        actor=actor,
        clock=clock,
    )
    appeal_id = uuid4()
    submit_appeal(
        moderation_case_store,
        moderation_decision_store,
        appeal_store,
        audit_store,
        appeal_id=appeal_id,
        decision_id=decision_id,
        submitted_by=uuid4(),
        grounds="the decision was wrong",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    result = decide_appeal(
        moderation_case_store,
        moderation_decision_store,
        appeal_store,
        audit_store,
        appeal_id=appeal_id,
        reviewer_actor_id=reviewer_id,
        outcome=AppealStatus.UPHELD,
        result="upheld on review",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.appeal.status == AppealStatus.UPHELD
    assert result.appeal.reviewer_actor_id == reviewer_id
    assert result.case.status == ModerationCaseStatus.CLOSED


def _ballot_in_configuration_review(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    *,
    creator: ActorRef,
    clock: FixedClock,
) -> UUID:
    """Real `create_ballot -> submit_ballot_for_configuration_review`
    chain, landing a real `Ballot` in `configuration_review` -
    `approve_ballot_configuration`'s own ADR-009 item 7 check needs a real
    ballot to check the creator identity of. Returns `ballot_id`."""
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=clock.now(),
        valid_until=None,
    )
    snapshot = create_eligibility_snapshot(
        eligibility_snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=(),
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=clock,
    ).snapshot

    ballot_id = uuid4()
    create_ballot(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    submit_ballot_for_configuration_review(
        ballot_store,
        audit_store,
        eligibility_snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot.eligibility_snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return ballot_id


def test_approve_ballot_configuration_rejects_the_ballots_own_creator(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    clock: FixedClock,
) -> None:
    creator = ActorRef(actor_id=uuid4(), actor_type="service")
    ballot_id = _ballot_in_configuration_review(
        ballot_store,
        audit_store,
        eligibility_rule_store,
        eligibility_snapshot_store,
        creator=creator,
        clock=clock,
    )
    with pytest.raises(VotingPermissionDeniedError) as excinfo:
        approve_ballot_configuration(
            ballot_store,
            audit_store,
            ballot_id=ballot_id,
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_approve_ballot_configuration_succeeds_for_a_different_actor(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    clock: FixedClock,
) -> None:
    creator = ActorRef(actor_id=uuid4(), actor_type="service")
    approver = ActorRef(actor_id=uuid4(), actor_type="service")
    ballot_id = _ballot_in_configuration_review(
        ballot_store,
        audit_store,
        eligibility_rule_store,
        eligibility_snapshot_store,
        creator=creator,
        clock=clock,
    )
    result = approve_ballot_configuration(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        actor=approver,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.ballot.status == BallotStatus.SCHEDULED


# =============================================================================
# PACK-05: the flagship two-actor authorization test named explicitly by the
# pack's required scope (item 4) - `activate_governance_policy`'s proposer
# and approver `RoleAssignment`s must resolve to distinct actors (ADR-020
# item 1). Mirrors the PACK-03 `decide_appeal`/
# `approve_ballot_configuration` pattern above: a rejection case and a real,
# end-to-end success case for the "different actor" path.
# =============================================================================


def test_propose_governance_policy_rejects_same_actor_as_proposer_and_approver(
    governance_policy_store: InMemoryGovernancePolicyStore,
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Both `proposed_by_role_id` and `approved_by_role_id` must resolve
    to distinct actors, even when they are two different `RoleAssignment`
    records (ADR-020 item 1: 'no role may approve or grant its own
    assignment' applies to two-actor approval generally, not only literal
    self-approval)."""
    same_actor_id = uuid4()
    proposer_role = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=same_actor_id,
            role_code="governance_policy_proposer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    approver_role = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=same_actor_id,
            role_code="governance_policy_approver",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    with pytest.raises(SameActorApprovalRejectedError) as excinfo:
        propose_governance_policy(
            governance_policy_store,
            role_assignment_store,
            audit_store,
            governance_policy_id=uuid4(),
            policy_type=GovernancePolicyType.ROLE_TAXONOMY,
            rule_definition={},
            effective_from=clock.now(),
            proposed_by_role_id=proposer_role.role_assignment_id,
            approved_by_role_id=approver_role.role_assignment_id,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "SAME_ACTOR_APPROVAL_REJECTED"


def test_activate_governance_policy_succeeds_for_distinct_proposer_and_approver(
    governance_policy_store: InMemoryGovernancePolicyStore,
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    proposer_role = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="governance_policy_proposer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    approver_role = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="governance_policy_approver",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    policy = propose_governance_policy(
        governance_policy_store,
        role_assignment_store,
        audit_store,
        governance_policy_id=uuid4(),
        policy_type=GovernancePolicyType.ROLE_TAXONOMY,
        rule_definition={},
        effective_from=clock.now(),
        proposed_by_role_id=proposer_role.role_assignment_id,
        approved_by_role_id=approver_role.role_assignment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).policy
    result = activate_governance_policy(
        governance_policy_store,
        role_assignment_store,
        audit_store,
        governance_policy_id=policy.governance_policy_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.policy.status == GovernancePolicyStatus.ACTIVE
