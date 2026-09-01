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
from epd2_ai_processing_service.application import (
    begin_processing,
    complete_processing_with_provider,
    prepare_input,
    request_ai_processing,
    review_ai_output,
)
from epd2_ai_processing_service.domain import HumanReviewStatus, RedactionManifest, RedactionResult
from epd2_ai_processing_service.exceptions import (
    AIReviewSelfApprovalProhibitedError,
)
from epd2_ai_processing_service.exceptions import (
    PermissionDeniedError as AIProcessingPermissionDeniedError,
)
from epd2_ai_processing_service.provider import ProviderOutcome, ScriptedAIModelProvider
from epd2_ai_processing_service.redaction import ScriptedRedactionValidator
from epd2_ai_processing_service.storage import InMemoryAIProcessingRecordStore
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
    activate_participant_eligibility_policy,
    create_eligibility_rule,
    create_eligibility_snapshot,
    evaluate_eligibility,
    propose_participant_eligibility_policy,
    record_digital_decision,
)
from epd2_eligibility_service.domain import (
    CriticalPolicyStatus as EligibilityCriticalPolicyStatus,
)
from epd2_eligibility_service.storage import (
    InMemoryAssemblyDecisionStore,
    InMemoryDigitalDecisionStore,
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
    InMemoryParticipantEligibilityPolicyStore,
)
from epd2_governance_service.application import (
    activate_governance_policy,
    propose_governance_policy,
)
from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    GovernancePolicyStatus,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
)
from epd2_governance_service.exceptions import SameActorApprovalRejectedError
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
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
from epd2_identity_service.domain import IdentityAssuranceLevel, IdentityRecord, VerificationStatus
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_membership_service.application import (
    PermissionDeniedError as MembershipPermissionDeniedError,
)
from epd2_membership_service.application import (
    activate_membership,
    declare_affiliation,
    evaluate_membership_application_eligibility,
    record_membership_human_decision,
    submit_membership_application,
)
from epd2_membership_service.domain import (
    CriticalPolicyStatus as MembershipCriticalPolicyStatus,
)
from epd2_membership_service.domain import (
    MembershipApplicationStatus,
    PartyMembershipEligibilityPolicy,
)
from epd2_membership_service.storage import (
    InMemoryAffiliationDeclarationStore,
    InMemoryMembershipApplicationStore,
    InMemoryMembershipStore,
    InMemoryPartyMembershipEligibilityPolicyStore,
)
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


# =============================================================================
# PACK-06: a plain `actor_is_authorized=False` rejection
# (`request_ai_processing`), plus this pack's own flagship two-actor
# authorization test (`review_ai_output`'s self-review prohibition for
# moderation-adjacent uses, ADR-025 §3) - mirroring the PACK-03/PACK-05
# rejection-then-success pattern above.
# =============================================================================


def _manifest_for_ct00_06() -> RedactionManifest:
    from datetime import datetime as _datetime

    return RedactionManifest(
        redaction_policy_reference="policy-1",
        redaction_policy_version="1.0",
        input_classification="public",
        checked_field_categories=("identity", "credential", "vote_linkage"),
        removed_field_categories=(),
        prepared_input_hash="hash-1",
        validator_version="1.0",
        validated_at=_datetime(2026, 1, 1, tzinfo=UTC),
        result=RedactionResult.PASS,
    )


def test_request_ai_processing_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    with pytest.raises(AIProcessingPermissionDeniedError) as excinfo:
        request_ai_processing(
            InMemoryAIProcessingRecordStore(),
            audit_store,
            ai_processing_record_id=uuid4(),
            purpose_code="summarization",
            target_type="initiative",
            target_id=uuid4(),
            input_version="v1",
            model_provider="internal",
            model_name="internal-model",
            model_version="1.0",
            prompt_template_version="v1",
            is_consequential=False,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def _completed_moderation_classification_record(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> UUID:
    """Real `request -> input_prepared -> processing -> completed` chain
    for a `classification` use on a `contribution` target (moderation-
    adjacent, requiring an independent reviewer per ADR-025 §3) -
    `review_ai_output`'s own self-review check needs a real completed,
    consequential record to review. Returns `ai_processing_record_id`."""
    created = request_ai_processing(
        record_store,
        audit_store,
        ai_processing_record_id=uuid4(),
        purpose_code="classification",
        target_type="contribution",
        target_id=uuid4(),
        input_version="v1",
        model_provider="internal",
        model_name="internal-model",
        model_version="1.0",
        prompt_template_version="v1",
        is_consequential=True,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    record_id = created.record.ai_processing_record_id
    prepare_input(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        redaction_validator=ScriptedRedactionValidator(_manifest_for_ct00_06()),
        input_reference="input-ref-1",
        declared_input_classification="public",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    begin_processing(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    complete_processing_with_provider(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        provider=ScriptedAIModelProvider(
            outcome=ProviderOutcome(
                output_reference="output-ref-1",
                output_hash="output-hash-1",
                confidence_score=0.9,
                uncertainty_indicator=None,
                explanation_reference=None,
                reason_codes=(),
            )
        ),
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return record_id


def test_review_ai_output_rejects_the_requesting_actor_as_reviewer(
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """ADR-025 §3: a `classification` review of a moderation-adjacent
    target requires an independent reviewer - the same actor who
    requested the AI processing may never also approve its own output."""
    record_store = InMemoryAIProcessingRecordStore()
    record_id = _completed_moderation_classification_record(record_store, audit_store, actor, clock)
    requesting_actor_reference = uuid4()
    reviewer = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=requesting_actor_reference,
            role_code="ai_moderation_reviewer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    with pytest.raises(AIReviewSelfApprovalProhibitedError) as excinfo:
        review_ai_output(
            record_store,
            audit_store,
            role_assignment_store,
            ai_processing_record_id=record_id,
            reviewer_role_assignment_id=reviewer.role_assignment_id,
            reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
            requesting_actor_reference=requesting_actor_reference,
            is_official_publication=False,
            outcome=HumanReviewStatus.APPROVED,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "AI_REVIEW_SELF_APPROVAL_PROHIBITED"


def test_review_ai_output_succeeds_for_a_different_reviewer(
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    record_store = InMemoryAIProcessingRecordStore()
    record_id = _completed_moderation_classification_record(record_store, audit_store, actor, clock)
    reviewer = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="ai_moderation_reviewer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    result = review_ai_output(
        record_store,
        audit_store,
        role_assignment_store,
        ai_processing_record_id=record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=False,
        outcome=HumanReviewStatus.APPROVED,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.record.human_review_status is HumanReviewStatus.APPROVED


# =============================================================================
# PACK-07 (canon-0.6.0, canon 19d.4-19d.14, ADR-026 through ADR-031): a plain
# `actor_is_authorized=False` rejection across a representative sample of
# both new services' critical commands - `eligibility-service`'s critical
# policy activation and formal digital-decision recording, and
# `membership-service`'s application submission, Stage B human decision,
# activation, and affiliation declaration. Each also asserts the state
# change did not happen, mirroring this file's own established pattern.
# =============================================================================


def test_activate_participant_eligibility_policy_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    policy = propose_participant_eligibility_policy(
        policy_store,
        policy_id=uuid4(),
        policy_version=1,
        scope_type=None,
        scope_id=None,
        effective_from=clock.now(),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    with pytest.raises(EligibilityPermissionDeniedError) as excinfo:
        activate_participant_eligibility_policy(
            policy_store,
            governance_decision_store,
            audit_store,
            policy_id=policy.policy_id,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    unchanged = policy_store.get(policy.policy_id)
    assert unchanged is not None
    assert unchanged.status == EligibilityCriticalPolicyStatus.DRAFT


def test_record_digital_decision_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    digital_decision_id = uuid4()
    with pytest.raises(EligibilityPermissionDeniedError) as excinfo:
        record_digital_decision(
            digital_decision_store,
            InMemoryAssemblyDecisionStore(),
            audit_store,
            digital_decision_id=digital_decision_id,
            process_reference={"process_id": str(uuid4())},
            digital_result="result",
            decision_effect="advisory",
            formal_confirmation_required=False,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    assert digital_decision_store.get(digital_decision_id) is None


def test_submit_membership_application_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    application_store = InMemoryMembershipApplicationStore()
    membership_application_id = uuid4()
    with pytest.raises(MembershipPermissionDeniedError) as excinfo:
        submit_membership_application(
            application_store,
            audit_store,
            membership_application_id=membership_application_id,
            subject_reference=uuid4(),
            supersedes_membership_application_id=None,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    assert application_store.get(membership_application_id) is None


def _approved_governance_decision_for_membership(
    store: InMemoryGovernanceDecisionStore, clock: FixedClock
) -> GovernanceDecision:
    """Real `proposed -> approved` `GovernanceDecision`, mirroring
    `_make_approved_governance_decision` in
    `services/membership-service/tests/test_application.py` -
    `record_membership_human_decision`'s own decision-authority check
    (`_verify_decision_authority`) needs a real approved decision to
    resolve against."""
    decision = GovernanceDecision(
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.MANDATE,
        subject_reference={"kind": "membership_decision"},
        proposed_by_role_id=uuid4(),
        approved_by_role_id=None,
        rejected_by_role_id=None,
        reason_code="MANDATE_ISSUED",
        evidence_references=(),
        finality_outcome=None,
        created_at=clock.now(),
        decided_at=None,
        supersedes_decision_id=None,
        status=GovernanceDecisionStatus.PROPOSED,
    )
    store.create(decision)
    approved = decision.with_approved(
        approved_by_role_id=uuid4(), decided_at=clock.now(), finality_outcome=None
    )
    store.save(approved)
    return approved


def _membership_application_pending_human_decision(
    application_store: InMemoryMembershipApplicationStore,
    policy_store: InMemoryPartyMembershipEligibilityPolicyStore,
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> UUID:
    """Real `submit -> Stage A evaluate` chain, landing a real
    `MembershipApplication` in `human_decision_pending` -
    `record_membership_human_decision`'s own rejection case needs a real
    pending application to verify was not mutated. Mirrors
    `_submit_and_evaluate` in `services/membership-service/tests/
    test_application.py`. Returns `membership_application_id`."""
    membership_application_id = uuid4()
    submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    policy_store.save(
        PartyMembershipEligibilityPolicy(
            policy_id=uuid4(),
            policy_version=1,
            status=MembershipCriticalPolicyStatus.ACTIVE,
            scope_type=None,
            scope_id=None,
            effective_from=datetime(2025, 1, 1, tzinfo=UTC),
            effective_until=None,
            adopted_by_decision_id=uuid4(),
            incompatibility_rules=(),
            signed_policy_digest_reference="digest",
            transparency_log_commitment_reference="commitment",
        )
    )
    identity_record_id = uuid4()
    identity_store.save(
        IdentityRecord(
            identity_record_id=identity_record_id,
            account_id=uuid4(),
            verification_provider="provider",
            verification_level="substantial",
            verification_status=VerificationStatus.VERIFIED,
            verified_at=clock.now(),
            expires_at=None,
            country="DE",
            duplicate_check_status="unique",
            provider_reference="ref",
            identity_assurance_level=IdentityAssuranceLevel.SUBSTANTIAL,
        )
    )
    evaluate_membership_application_eligibility(
        application_store,
        policy_store,
        identity_store,
        audit_store,
        membership_application_id=membership_application_id,
        identity_record_id=identity_record_id,
        scope_type=None,
        scope_id=None,
        effective_date=clock.now(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return membership_application_id


def test_record_membership_human_decision_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_application_id = _membership_application_pending_human_decision(
        application_store, policy_store, identity_store, audit_store, actor, clock
    )
    decision = _approved_governance_decision_for_membership(governance_decision_store, clock)
    with pytest.raises(MembershipPermissionDeniedError) as excinfo:
        record_membership_human_decision(
            application_store,
            InMemoryMembershipStore(),
            governance_decision_store,
            audit_store,
            membership_application_id=membership_application_id,
            outcome="approved",
            decision_authority_reference=decision.governance_decision_id,
            applied_policy_version=1,
            reason_code="OK",
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    unchanged = application_store.get(membership_application_id)
    assert unchanged is not None
    assert unchanged.status == MembershipApplicationStatus.HUMAN_DECISION_PENDING


def test_activate_membership_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    membership_application_id = _membership_application_pending_human_decision(
        application_store, policy_store, identity_store, audit_store, actor, clock
    )
    decision = _approved_governance_decision_for_membership(governance_decision_store, clock)
    record_membership_human_decision(
        application_store,
        membership_store,
        governance_decision_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="approved",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="OK",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    membership_id = uuid4()
    with pytest.raises(MembershipPermissionDeniedError) as excinfo:
        activate_membership(
            application_store,
            membership_store,
            audit_store,
            membership_application_id=membership_application_id,
            membership_id=membership_id,
            account_reference=uuid4(),
            organization_id=uuid4(),
            membership_type="party",
            region_code=None,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    unchanged = application_store.get(membership_application_id)
    assert unchanged is not None
    assert unchanged.status == MembershipApplicationStatus.APPROVED
    assert membership_store.get(membership_id) is None


def test_declare_affiliation_without_permission_is_denied(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    store = InMemoryAffiliationDeclarationStore()
    affiliation_declaration_id = uuid4()
    with pytest.raises(MembershipPermissionDeniedError) as excinfo:
        declare_affiliation(
            store,
            audit_store,
            affiliation_declaration_id=affiliation_declaration_id,
            subject_reference=uuid4(),
            affiliation_type="other_party_membership",
            declared_reference="ref-1",
            valid_from=clock.now(),
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"
    assert store.get(affiliation_declaration_id) is None
