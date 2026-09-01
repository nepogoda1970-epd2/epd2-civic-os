"""CT-00-07 Audit Creation (canon section 27): a critical action creates
an `AuditEvent`, for every service that owns one. Per-service unit tests
already cover this (services/*/tests/test_application.py); this file is
the cross-service, pack-numbered aggregation the pack itself asks for
(section 12.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from epd2_account_service.application import create_account
from epd2_account_service.storage import InMemoryAccountStore
from epd2_ai_processing_service.application import request_ai_processing
from epd2_ai_processing_service.storage import InMemoryAIProcessingRecordStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_delegation_service.application import create_delegation
from epd2_delegation_service.storage import InMemoryDelegationStore
from epd2_deliberation_service.application import open_discussion
from epd2_deliberation_service.storage import InMemoryDiscussionStore
from epd2_eligibility_service.application import (
    activate_participant_eligibility_policy,
    create_eligibility_rule,
    evaluate_eligibility,
    propose_participant_eligibility_policy,
    record_digital_decision,
)
from epd2_eligibility_service.storage import (
    InMemoryAssemblyDecisionStore,
    InMemoryDigitalDecisionStore,
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryParticipantEligibilityPolicyStore,
)
from epd2_governance_service.application import request_role_assignment
from epd2_governance_service.domain import (
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    RoleAssignment,
    RoleAssignmentStatus,
)
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
    InMemoryRoleAssignmentStore,
)
from epd2_identity_service.application import start_identity_verification
from epd2_identity_service.domain import IdentityAssuranceLevel, IdentityRecord, VerificationStatus
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_initiative_service.application import create_initiative
from epd2_initiative_service.storage import InMemoryInitiativeStore
from epd2_membership_service.application import (
    activate_membership,
    evaluate_membership_application_eligibility,
    open_conflict_assessment,
    record_membership_human_decision,
    submit_membership_application,
)
from epd2_membership_service.domain import CriticalPolicyStatus, PartyMembershipEligibilityPolicy
from epd2_membership_service.storage import (
    InMemoryConflictAssessmentStore,
    InMemoryMembershipApplicationStore,
    InMemoryMembershipStore,
    InMemoryPartyMembershipEligibilityPolicyStore,
)
from epd2_moderation_service.application import open_moderation_case
from epd2_moderation_service.storage import InMemoryModerationCaseStore
from epd2_tally_service.application import start_tally
from epd2_tally_service.storage import InMemoryTallyStore
from epd2_voting_service.application import create_ballot
from epd2_voting_service.domain import BallotMethod
from epd2_voting_service.storage import InMemoryBallotStore


def test_account_creation_creates_an_audit_event(
    account_store: InMemoryAccountStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_account(
        account_store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.audit_event is not None
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_identity_verification_start_creates_an_audit_event(
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = start_identity_verification(
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
    )
    assert result.audit_event is not None
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_eligibility_evaluation_creates_an_audit_event(
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
    result = evaluate_eligibility(
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
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_credential_issuance_creates_an_audit_event(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = issue_participation_credential(
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
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_denied_command_creates_no_audit_event(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A refused command must never fabricate an audit trail entry for an
    action that never happened (complements CT-00-06)."""
    import pytest

    from epd2_credential_service.application import PermissionDeniedError

    credential_id = uuid4()
    with pytest.raises(PermissionDeniedError):
        issue_participation_credential(
            credential_store,
            audit_store,
            credential_id=credential_id,
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
    assert audit_store.list_by_aggregate("participation_credential", credential_id) == ()


# =============================================================================
# PACK-03: one audit-creation test per service (6 total), each a real,
# state-changing command whose resulting `AuditEvent` is retrievable via
# `audit_store.get_by_event_id`, mirroring the PACK-02 tests above exactly.
# =============================================================================


def test_initiative_creation_creates_an_audit_event(
    initiative_store: InMemoryInitiativeStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_initiative(
        initiative_store,
        audit_store,
        initiative_id=uuid4(),
        space_id=uuid4(),
        author_actor_id=uuid4(),
        initiative_type="citizen_initiative",
        workflow_id=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_discussion_opening_creates_an_audit_event(
    discussion_store: InMemoryDiscussionStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = open_discussion(
        discussion_store,
        audit_store,
        discussion_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        space_id=uuid4(),
        moderation_policy_id=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_moderation_case_opening_creates_an_audit_event(
    moderation_case_store: InMemoryModerationCaseStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = open_moderation_case(
        moderation_case_store,
        audit_store,
        moderation_case_id=uuid4(),
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
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_ballot_creation_creates_an_audit_event(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    from datetime import timedelta

    result = create_ballot(
        ballot_store,
        audit_store,
        ballot_id=uuid4(),
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
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_tally_start_creates_an_audit_event(
    tally_store: InMemoryTallyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = start_tally(
        tally_store,
        audit_store,
        tally_id=uuid4(),
        ballot_id=uuid4(),
        input_set_hash="a" * 64,
        algorithm_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_delegation_creation_creates_an_audit_event(
    delegation_store: InMemoryDelegationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_delegation(
        delegation_store,
        audit_store,
        delegation_id=uuid4(),
        delegator_actor_id=uuid4(),
        delegate_actor_id=uuid4(),
        scope_type="ballot",
        scope_id=uuid4(),
        valid_from=clock.now(),
        valid_until=None,
        revocation_status="not_revoked",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_role_assignment_request_creates_an_audit_event(
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """PACK-05: `request_role_assignment` (governance-service)."""
    granter = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="governance_policy_approver",
            scope_id=uuid4(),
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    result = request_role_assignment(
        role_assignment_store,
        audit_store,
        role_assignment_id=uuid4(),
        actor_id=uuid4(),
        role_code="observer",
        scope_id=uuid4(),
        valid_from=clock.now(),
        valid_until=None,
        granter_role_assignment_id=granter.role_assignment_id,
        approval_reference=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_request_ai_processing_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """PACK-06: `request_ai_processing` (ai-processing-service)."""
    result = request_ai_processing(
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
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


# =============================================================================
# PACK-07: eligibility-service and membership-service (canon 19d.4-19d.16,
# canon-0.6.0, ADR-026 through ADR-031). A representative sample of the new
# critical/consequential commands across both services, each asserted
# against the full CT-00-07 field set (`event_type`/`target_type`/
# `target_id`/`reason_code`/`before_hash`/`after_hash`), not merely "an
# audit event exists" like the PACK-02-06 tests above.
# =============================================================================


def _make_approved_governance_decision(
    store: InMemoryGovernanceDecisionStore, *, clock: FixedClock
) -> GovernanceDecision:
    """Mirrors both services' own
    `tests/test_application*.py::_make_approved_governance_decision` helper -
    a `GovernanceDecision` that satisfies `verify_decision_authorizes_policy_activation`."""
    proposed_by = uuid4()
    approved_by = uuid4()
    decision = GovernanceDecision(
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.MANDATE,
        subject_reference={"kind": "pack07_contract_test"},
        proposed_by_role_id=proposed_by,
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
        approved_by_role_id=approved_by, decided_at=clock.now(), finality_outcome=None
    )
    store.save(approved)
    return approved


def test_activate_participant_eligibility_policy_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """eligibility-service: `activate_participant_eligibility_policy`
    (canon 19d.4/19d.7's four-gate critical-policy activation)."""
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    decision = _make_approved_governance_decision(governance_decision_store, clock=clock)
    policy = propose_participant_eligibility_policy(
        policy_store,
        policy_id=uuid4(),
        policy_version=1,
        scope_type=None,
        scope_id=None,
        effective_from=clock.now(),
        effective_until=None,
        adopted_by_decision_id=decision.governance_decision_id,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    activate_participant_eligibility_policy(
        policy_store,
        governance_decision_store,
        audit_store,
        policy_id=policy.policy_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    events = audit_store.list_by_aggregate("participant_eligibility_policy", policy.policy_id)
    assert len(events) == 1
    audit_event = events[0]
    assert audit_event.event_type == "eligibility.participant_eligibility_policy_activated"
    assert audit_event.target_type == "participant_eligibility_policy"
    assert audit_event.target_id == policy.policy_id
    assert audit_event.action == "activate"
    assert audit_event.reason_code == "CRITICAL_POLICY_ACTIVATED"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""


def test_record_digital_decision_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """eligibility-service: `record_digital_decision` (canon 19d.12,
    ADR-030 item 8), final path - no formal confirmation required, so the
    audit entry is created immediately for the `DigitalDecision` itself."""
    digital_decision_id = uuid4()
    result = record_digital_decision(
        InMemoryDigitalDecisionStore(),
        InMemoryAssemblyDecisionStore(),
        audit_store,
        digital_decision_id=digital_decision_id,
        process_reference={"process_id": str(uuid4())},
        digital_result="approved",
        decision_effect="internally_binding",
        formal_confirmation_required=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    audit_event = audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit_event is not None
    assert audit_event.target_type == "digital_decision"
    assert audit_event.target_id == digital_decision_id
    assert audit_event.action == "record"
    assert audit_event.reason_code == "DIGITAL_DECISION_FINAL"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""


def test_submit_membership_application_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """membership-service: `submit_membership_application` (canon 19d.9,
    entering Stage A)."""
    membership_application_id = uuid4()
    result = submit_membership_application(
        InMemoryMembershipApplicationStore(),
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    audit_event = audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit_event is not None
    assert audit_event.event_type == "membership.membership_application_submitted"
    assert audit_event.target_type == "membership_application"
    assert audit_event.target_id == membership_application_id
    assert audit_event.action == "submit"
    assert audit_event.reason_code == "MEMBERSHIP_APPLICATION_SUBMITTED"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""


def _submit_and_move_to_human_decision_pending(
    *,
    application_store: InMemoryMembershipApplicationStore,
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> UUID:
    """Shared setup for the two tests below that need a
    `MembershipApplication` already past Stage A (canon 19d.9) - mirrors
    `services/membership-service/tests/test_application.py::_submit_and_evaluate`."""
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
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    policy_store.save(
        PartyMembershipEligibilityPolicy(
            policy_id=uuid4(),
            policy_version=1,
            status=CriticalPolicyStatus.ACTIVE,
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


def test_record_membership_human_decision_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    identity_store: InMemoryIdentityRecordStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """membership-service: `record_membership_human_decision` (canon
    19d.9 Stage B, the sole authorized human decision path)."""
    application_store = InMemoryMembershipApplicationStore()
    membership_application_id = _submit_and_move_to_human_decision_pending(
        application_store=application_store,
        identity_store=identity_store,
        audit_store=audit_store,
        actor=actor,
        clock=clock,
    )
    decision = _make_approved_governance_decision(governance_decision_store, clock=clock)
    result = record_membership_human_decision(
        application_store,
        InMemoryMembershipStore(),
        governance_decision_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="approved",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="MEMBERSHIP_APPROVED",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    audit_event = audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit_event is not None
    assert audit_event.target_type == "membership_application"
    assert audit_event.target_id == membership_application_id
    assert audit_event.action == "record_human_decision"
    assert audit_event.reason_code == "MEMBERSHIP_APPROVED"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""


def test_activate_membership_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    governance_decision_store: InMemoryGovernanceDecisionStore,
    identity_store: InMemoryIdentityRecordStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """membership-service: `activate_membership` (ADR-030 item 2's
    distinct final step - the only code path that may set
    `Membership.membership_status = active`)."""
    application_store = InMemoryMembershipApplicationStore()
    membership_store = InMemoryMembershipStore()
    membership_application_id = _submit_and_move_to_human_decision_pending(
        application_store=application_store,
        identity_store=identity_store,
        audit_store=audit_store,
        actor=actor,
        clock=clock,
    )
    decision = _make_approved_governance_decision(governance_decision_store, clock=clock)
    record_membership_human_decision(
        application_store,
        membership_store,
        governance_decision_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="approved",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="MEMBERSHIP_APPROVED",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    membership_id = uuid4()
    result = activate_membership(
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
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    audit_event = audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit_event is not None
    assert audit_event.event_type == "membership.membership_activated"
    assert audit_event.target_type == "membership"
    assert audit_event.target_id == membership_id
    assert audit_event.action == "activate"
    assert audit_event.reason_code == "MEMBERSHIP_ACTIVATED"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""


def test_open_conflict_assessment_creates_an_audit_event(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """membership-service: `open_conflict_assessment` (canon 19d.11)."""
    conflict_assessment_id = uuid4()
    result = open_conflict_assessment(
        InMemoryConflictAssessmentStore(),
        audit_store,
        conflict_assessment_id=conflict_assessment_id,
        subject_reference=uuid4(),
        conflict_type="dual_party_membership",
        reviewed_by_role_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    audit_event = audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit_event is not None
    assert audit_event.event_type == "membership.conflict_assessment_opened"
    assert audit_event.target_type == "conflict_assessment"
    assert audit_event.target_id == conflict_assessment_id
    assert audit_event.action == "open"
    assert audit_event.reason_code == "CONFLICT_ASSESSMENT_OPENED"
    assert audit_event.before_hash == ""
    assert audit_event.after_hash != ""
