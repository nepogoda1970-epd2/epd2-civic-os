"""Tests for epd2_eligibility_service.application's PACK-07 additions
(canon 19d.4-19d.14, ADR-026 through ADR-031)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import (
    PermissionDeniedError,
    activate_participant_eligibility_policy,
    activate_process_eligibility_policy,
    activate_step_up_authentication_requirement,
    authenticate_step_up_for_action,
    check_process_eligibility_atomic_capability,
    derive_and_issue_scoped_capability_token,
    evaluate_process_eligibility,
    propose_participant_eligibility_policy,
    propose_process_eligibility_policy,
    propose_step_up_authentication_requirement,
    record_assembly_decision,
    record_digital_decision,
    resolve_process_eligibility_policy,
)
from epd2_eligibility_service.domain import (
    AssuranceRequirement,
    CriticalPolicyStatus,
    ObservedAuthenticationState,
    ProcessEligibilityClaims,
)
from epd2_eligibility_service.exceptions import (
    CriticalPolicyActivationNotAuthorizedError,
    StepUpAuthenticationNotSatisfiedError,
    UnknownParticipantEligibilityPolicyError,
)
from epd2_eligibility_service.storage import (
    InMemoryAssemblyDecisionStore,
    InMemoryDigitalDecisionStore,
    InMemoryParticipantEligibilityPolicyStore,
    InMemoryProcessEligibilityPolicyStore,
    InMemoryStepUpAuthenticationRequirementStore,
)
from epd2_governance_service.domain import (
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
)
from epd2_governance_service.storage import InMemoryGovernanceDecisionStore

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _make_approved_governance_decision(
    store: InMemoryGovernanceDecisionStore,
) -> GovernanceDecision:
    proposed_by = uuid4()
    approved_by = uuid4()
    decision = GovernanceDecision(
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.MANDATE,
        subject_reference={"kind": "eligibility_policy"},
        proposed_by_role_id=proposed_by,
        approved_by_role_id=None,
        rejected_by_role_id=None,
        reason_code="MANDATE_ISSUED",
        evidence_references=(),
        finality_outcome=None,
        created_at=_CLOCK.now(),
        decided_at=None,
        supersedes_decision_id=None,
        status=GovernanceDecisionStatus.PROPOSED,
    )
    store.create(decision)
    approved = decision.with_approved(
        approved_by_role_id=approved_by, decided_at=_CLOCK.now(), finality_outcome=None
    )
    store.save(approved)
    return approved


# =============================================================================
# ParticipantEligibilityPolicy propose/activate (canon 19d.4/19d.7)
# =============================================================================


def test_activate_participant_eligibility_policy_requires_all_four_gates() -> None:
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    policy = propose_participant_eligibility_policy(
        policy_store,
        policy_id=uuid4(),
        policy_version=1,
        scope_type=None,
        scope_id=None,
        effective_from=_CLOCK.now(),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    with pytest.raises(CriticalPolicyActivationNotAuthorizedError):
        activate_participant_eligibility_policy(
            policy_store,
            governance_store,
            InMemoryAuditEventStore(),
            policy_id=policy.policy_id,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_activate_participant_eligibility_policy_succeeds_with_all_gates_met() -> None:
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    decision = _make_approved_governance_decision(governance_store)
    policy = propose_participant_eligibility_policy(
        policy_store,
        policy_id=uuid4(),
        policy_version=1,
        scope_type=None,
        scope_id=None,
        effective_from=_CLOCK.now(),
        effective_until=None,
        adopted_by_decision_id=decision.governance_decision_id,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    activated = activate_participant_eligibility_policy(
        policy_store,
        governance_store,
        audit_store,
        policy_id=policy.policy_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert activated.status is CriticalPolicyStatus.ACTIVE


def test_activate_participant_eligibility_policy_without_permission_is_denied() -> None:
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    policy = propose_participant_eligibility_policy(
        policy_store,
        policy_id=uuid4(),
        policy_version=1,
        scope_type=None,
        scope_id=None,
        effective_from=_CLOCK.now(),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    with pytest.raises(PermissionDeniedError):
        activate_participant_eligibility_policy(
            policy_store,
            governance_store,
            InMemoryAuditEventStore(),
            policy_id=policy.policy_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_activate_participant_eligibility_policy_unknown_policy_raises() -> None:
    policy_store = InMemoryParticipantEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    with pytest.raises(UnknownParticipantEligibilityPolicyError):
        activate_participant_eligibility_policy(
            policy_store,
            governance_store,
            InMemoryAuditEventStore(),
            policy_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# =============================================================================
# ProcessEligibilityPolicy propose/activate/resolve (canon 19d.5, ADR-030 item 6)
# =============================================================================


def _propose_and_activate_process_policy(
    policy_store: InMemoryProcessEligibilityPolicyStore,
    governance_store: InMemoryGovernanceDecisionStore,
    *,
    policy_version: int = 1,
    effective_from: datetime | None = None,
    **overrides: object,
) -> UUID:
    decision = _make_approved_governance_decision(governance_store)
    kwargs: dict[str, object] = {
        "policy_id": uuid4(),
        "policy_version": policy_version,
        "process_type": "epd_member_vote",
        "jurisdiction": "DE",
        "scope_type": None,
        "scope_id": None,
        "adopted_by": decision.governance_decision_id,
        "effective_from": effective_from or _CLOCK.now() - timedelta(days=1),
        "signed_policy_digest_reference": "digest",
        "transparency_log_commitment_reference": "commitment",
    }
    kwargs.update(overrides)
    policy = propose_process_eligibility_policy(policy_store, **kwargs)  # type: ignore[arg-type]
    activate_process_eligibility_policy(
        policy_store,
        governance_store,
        InMemoryAuditEventStore(),
        policy_id=policy.policy_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return policy.policy_id


def test_resolve_process_eligibility_policy_picks_highest_matching_version() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_process_policy(policy_store, governance_store, policy_version=1)
    _propose_and_activate_process_policy(policy_store, governance_store, policy_version=2)
    resolved = resolve_process_eligibility_policy(
        policy_store,
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
    )
    assert resolved is not None
    assert resolved.policy_version == 2


def test_resolve_process_eligibility_policy_returns_none_when_no_match() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    resolved = resolve_process_eligibility_policy(
        policy_store,
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
    )
    assert resolved is None


# =============================================================================
# StepUpAuthenticationRequirement (canon 19d.7/19d.8)
# =============================================================================


def _propose_and_activate_step_up_requirement(
    requirement_store: InMemoryStepUpAuthenticationRequirementStore,
    governance_store: InMemoryGovernanceDecisionStore,
    *,
    action_code: str = "cast_ballot",
) -> UUID:
    requirement = propose_step_up_authentication_requirement(
        requirement_store,
        requirement_id=uuid4(),
        requirement_version=1,
        action_code=action_code,
        required_authentication_context="session",
        assurance_requirement=AssuranceRequirement(
            required_identity_assurance_level="substantial",
            required_authentication_assurance_level="substantial",
        ),
        fresh_authentication_required=True,
        reauthentication_reason="high-stakes action",
        maximum_authentication_age=timedelta(minutes=15),
        effective_from=_CLOCK.now() - timedelta(days=1),
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    decision = _make_approved_governance_decision(governance_store)
    activate_step_up_authentication_requirement(
        requirement_store,
        governance_store,
        InMemoryAuditEventStore(),
        requirement_id=requirement.requirement_id,
        adopted_by_decision_id=decision.governance_decision_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return requirement.requirement_id


def test_authenticate_step_up_for_action_succeeds_when_all_conditions_met() -> None:
    requirement_store = InMemoryStepUpAuthenticationRequirementStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_step_up_requirement(requirement_store, governance_store)
    observed = ObservedAuthenticationState(
        identity_assurance_level="substantial",
        authentication_assurance_level="substantial",
        session_authenticated_at=_CLOCK.now() - timedelta(minutes=5),
        attribute_verified_at=None,
    )
    authenticate_step_up_for_action(
        requirement_store,
        action_code="cast_ballot",
        observed=observed,
        evaluated_at=_CLOCK.now(),
    )  # does not raise


def test_authenticate_step_up_for_action_fails_closed_with_no_observed_state() -> None:
    requirement_store = InMemoryStepUpAuthenticationRequirementStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_step_up_requirement(requirement_store, governance_store)
    with pytest.raises(StepUpAuthenticationNotSatisfiedError):
        authenticate_step_up_for_action(
            requirement_store,
            action_code="cast_ballot",
            observed=None,
            evaluated_at=_CLOCK.now(),
        )


def test_authenticate_step_up_for_action_fails_closed_with_no_active_requirement() -> None:
    requirement_store = InMemoryStepUpAuthenticationRequirementStore()
    observed = ObservedAuthenticationState(
        identity_assurance_level="substantial",
        authentication_assurance_level="substantial",
        session_authenticated_at=_CLOCK.now(),
        attribute_verified_at=None,
    )
    with pytest.raises(StepUpAuthenticationNotSatisfiedError):
        authenticate_step_up_for_action(
            requirement_store,
            action_code="unknown_action",
            observed=observed,
            evaluated_at=_CLOCK.now(),
        )


# =============================================================================
# check_process_eligibility_atomic_capability (canon 19d.14)
# =============================================================================


def test_check_process_eligibility_atomic_capability_authorized_when_claim_met() -> None:
    result = check_process_eligibility_atomic_capability(
        claim_met=True, denial_reason_code="ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET"
    )
    assert result.authorized is True
    assert result.reason_code is None


def test_check_process_eligibility_atomic_capability_denied_with_reason_when_claim_not_met() -> (
    None
):
    result = check_process_eligibility_atomic_capability(
        claim_met=False, denial_reason_code="ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET"
    )
    assert result.authorized is False
    assert result.reason_code == "ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET"


# =============================================================================
# derive_and_issue_scoped_capability_token (canon 19d.14)
# =============================================================================


_CLAIMS = ProcessEligibilityClaims(
    active_electoral_eligibility_met=True,
    active_electoral_eligibility_reason_codes=(),
    passive_electoral_eligibility_met=True,
    passive_electoral_eligibility_reason_codes=(),
    party_internal_voting_eligibility_met=False,
    party_internal_voting_eligibility_reason_codes=("PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET",),
    party_office_candidacy_eligibility_met=False,
    party_office_candidacy_eligibility_reason_codes=("PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET",),
)


def test_derive_and_issue_scoped_capability_token_issues_credential_when_authorized() -> None:
    credential_store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    result = derive_and_issue_scoped_capability_token(
        credential_store,
        audit_store,
        subject_reference=uuid4(),
        process_id=uuid4(),
        action_code="cast_ballot",
        claims=_CLAIMS,
        claim_met=True,
        denial_reason_code="ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET",
        credential_id=uuid4(),
        credential_type="ballot_access",
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=_CLOCK.now(),
        expires_at=_CLOCK.now() + timedelta(days=1),
        usage_limit=1,
        applicable_policy_version=1,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.credential_id is not None
    assert result.event.event_type == "eligibility.participation_rights_derived"


def test_derive_and_issue_scoped_capability_token_still_emits_event_when_denied() -> None:
    """Canon 19d.14: ParticipationRightsDerived is emitted whether or not
    a token was actually issued - the derivation itself happened either
    way."""
    credential_store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    result = derive_and_issue_scoped_capability_token(
        credential_store,
        audit_store,
        subject_reference=uuid4(),
        process_id=uuid4(),
        action_code="cast_ballot",
        claims=_CLAIMS,
        claim_met=False,
        denial_reason_code="ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET",
        credential_id=uuid4(),
        credential_type="ballot_access",
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=_CLOCK.now(),
        expires_at=_CLOCK.now() + timedelta(days=1),
        usage_limit=1,
        applicable_policy_version=1,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.credential_id is None
    assert result.event.event_type == "eligibility.participation_rights_derived"


# =============================================================================
# record_digital_decision / record_assembly_decision (canon 19d.12, ADR-030 item 8)
# =============================================================================


def test_record_digital_decision_final_path_creates_no_assembly_decision() -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    assembly_decision_store = InMemoryAssemblyDecisionStore()
    audit_store = InMemoryAuditEventStore()
    result = record_digital_decision(
        digital_decision_store,
        assembly_decision_store,
        audit_store,
        digital_decision_id=uuid4(),
        process_reference={"process_id": str(uuid4())},
        digital_result="approved",
        decision_effect="internally_binding",
        formal_confirmation_required=False,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.assembly_decision is None
    assert result.event is None
    assert result.digital_decision.status.value == "final"


def test_record_digital_decision_confirmation_required_path_creates_assembly_decision() -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    assembly_decision_store = InMemoryAssemblyDecisionStore()
    audit_store = InMemoryAuditEventStore()
    result = record_digital_decision(
        digital_decision_store,
        assembly_decision_store,
        audit_store,
        digital_decision_id=uuid4(),
        process_reference={"process_id": str(uuid4())},
        digital_result="approved",
        decision_effect="requires_formal_confirmation",
        formal_confirmation_required=True,
        confirming_authority="election_committee",
        legal_basis="BWahlG",
        confirmation_deadline=_CLOCK.now() + timedelta(days=7),
        protocol_or_evidence_reference="protocol-1",
        assembly_decision_id=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.assembly_decision is not None
    assert result.event is not None
    assert result.event.event_type == "eligibility.formal_confirmation_requested"


def test_record_digital_decision_confirmation_required_missing_fields_raises() -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    assembly_decision_store = InMemoryAssemblyDecisionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(ValueError, match="required when formal_confirmation_required"):
        record_digital_decision(
            digital_decision_store,
            assembly_decision_store,
            audit_store,
            digital_decision_id=uuid4(),
            process_reference={},
            digital_result="approved",
            decision_effect="requires_formal_confirmation",
            formal_confirmation_required=True,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_assembly_decision_requires_divergence_explanation_when_diverging() -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    assembly_decision_store = InMemoryAssemblyDecisionStore()
    audit_store = InMemoryAuditEventStore()
    digital_result = record_digital_decision(
        digital_decision_store,
        assembly_decision_store,
        audit_store,
        digital_decision_id=uuid4(),
        process_reference={},
        digital_result="approved",
        decision_effect="requires_formal_confirmation",
        formal_confirmation_required=True,
        confirming_authority="election_committee",
        legal_basis="BWahlG",
        confirmation_deadline=_CLOCK.now() + timedelta(days=7),
        protocol_or_evidence_reference="protocol-1",
        assembly_decision_id=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert digital_result.assembly_decision is not None
    with pytest.raises(Exception):  # noqa: B017 - AssemblyDecisionDivergenceExplanationRequiredError
        record_assembly_decision(
            assembly_decision_store,
            digital_decision_store,
            audit_store,
            assembly_decision_id=digital_result.assembly_decision.assembly_decision_id,
            new_status="confirmed",
            final_legal_decision="rejected",
            divergence_explanation=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_assembly_decision_confirms_without_divergence() -> None:
    digital_decision_store = InMemoryDigitalDecisionStore()
    assembly_decision_store = InMemoryAssemblyDecisionStore()
    audit_store = InMemoryAuditEventStore()
    digital_result = record_digital_decision(
        digital_decision_store,
        assembly_decision_store,
        audit_store,
        digital_decision_id=uuid4(),
        process_reference={},
        digital_result="approved",
        decision_effect="requires_formal_confirmation",
        formal_confirmation_required=True,
        confirming_authority="election_committee",
        legal_basis="BWahlG",
        confirmation_deadline=_CLOCK.now() + timedelta(days=7),
        protocol_or_evidence_reference="protocol-1",
        assembly_decision_id=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert digital_result.assembly_decision is not None
    result = record_assembly_decision(
        assembly_decision_store,
        digital_decision_store,
        audit_store,
        assembly_decision_id=digital_result.assembly_decision.assembly_decision_id,
        new_status="confirmed",
        final_legal_decision="approved",
        divergence_explanation=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.assembly_decision.status.value == "confirmed"
    assert result.event.event_type == "eligibility.formal_confirmation_recorded"


# =============================================================================
# evaluate_process_eligibility (main PACK-07 use case, ADR-027)
# =============================================================================


class _FakeIdentityClaims:
    def __init__(self, *, identity_verified: bool) -> None:
        self.identity_verified = identity_verified
        self.age_requirement_met = identity_verified
        self.citizenship_requirement_met = identity_verified
        self.residence_requirement_met = identity_verified


def _fake_identity_reader(*, identity_verified: bool) -> object:
    def _reader(**_kwargs: object) -> _FakeIdentityClaims:
        return _FakeIdentityClaims(identity_verified=identity_verified)

    return _reader


def test_evaluate_process_eligibility_returns_none_when_no_policy_resolves() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    result = evaluate_process_eligibility(
        policy_store,
        _fake_identity_reader(identity_verified=True),
        lambda **_kwargs: None,
        subject_reference=uuid4(),
        identity_record_id=uuid4(),
        process_id=uuid4(),
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
    )
    assert result is None


def test_evaluate_process_eligibility_computes_active_and_passive_claims_from_identity() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_process_policy(policy_store, governance_store)
    result = evaluate_process_eligibility(
        policy_store,
        _fake_identity_reader(identity_verified=True),
        lambda **_kwargs: None,
        subject_reference=uuid4(),
        identity_record_id=uuid4(),
        process_id=uuid4(),
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
    )
    assert result is not None
    claims, applicable_policy_version = result
    assert claims.active_electoral_eligibility_met is True
    assert claims.passive_electoral_eligibility_met is True
    # No party dimension on this policy - party claims are always False,
    # never silently treated as met (canon 19d.3).
    assert claims.party_internal_voting_eligibility_met is False
    assert claims.party_office_candidacy_eligibility_met is False
    assert applicable_policy_version == 1


def test_evaluate_process_eligibility_denies_active_claim_when_identity_not_verified() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_process_policy(policy_store, governance_store)
    result = evaluate_process_eligibility(
        policy_store,
        _fake_identity_reader(identity_verified=False),
        lambda **_kwargs: None,
        subject_reference=uuid4(),
        identity_record_id=uuid4(),
        process_id=uuid4(),
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
    )
    assert result is not None
    claims, _ = result
    assert claims.active_electoral_eligibility_met is False
    assert (
        "ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET" in claims.active_electoral_eligibility_reason_codes
    )


def test_evaluate_process_eligibility_reads_membership_layer_when_party_dimension_present() -> None:
    policy_store = InMemoryProcessEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    _propose_and_activate_process_policy(
        policy_store,
        governance_store,
        process_type="epd_party_office_election",
        party_internal_voting_rule={"kind": "simple_majority"},
    )

    class _FakeMembershipClaims:
        required_membership_status_met = True
        membership_duration_requirement_met = True

    def _membership_reader(**_kwargs: object) -> _FakeMembershipClaims:
        return _FakeMembershipClaims()

    result = evaluate_process_eligibility(
        policy_store,
        _fake_identity_reader(identity_verified=True),
        _membership_reader,
        subject_reference=uuid4(),
        identity_record_id=uuid4(),
        process_id=uuid4(),
        process_type="epd_party_office_election",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
        membership_subject_reference=uuid4(),
    )
    assert result is not None
    claims, _ = result
    assert claims.party_internal_voting_eligibility_met is True
