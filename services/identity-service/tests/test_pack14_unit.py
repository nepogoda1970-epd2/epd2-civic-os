"""PACK-14 unit tests (task section 30.1).

Account lifecycle, lock/restriction separation, contact normalization,
credential states, password fallback policy, passkey classification,
assurance calculation, step-up freshness, object-version binding, session
expiry, rotation and revocation, recovery states, dual control, identity
mapping scope, and reason codes.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from _pack14_builders import (
    NOW,
    SALT,
    account_id,
    assurance,
    credential_metadata,
    device,
    lock,
    new_credential_id,
    new_session_id,
    reference,
    restriction,
    scope,
    step_up_binding,
)

from epd2_identity_service.accounts import (
    AccountRegistryStatus,
    AccountRestrictionClass,
    AnonymizationState,
    ClosureRequestState,
    activate_account_record,
    assert_account_usable,
    begin_anonymization,
    cancel_closure_request,
    complete_anonymization,
    complete_closure,
    create_account_record,
    open_closure_request,
)
from epd2_identity_service.assurance import (
    ACTION_REQUIREMENTS,
    AssuranceEvidence,
    AuthenticationMethod,
    RiskState,
    apply_risk_downgrade,
    assurance_ceiling,
    assurance_for_passkey,
    combine_methods,
    evaluate_requirement,
)
from epd2_identity_service.configuration import (
    ActionClass,
    GovernanceAuthority,
    default_configuration,
    relax_freshness_window,
    tighten_freshness_window,
    tighten_session_timeout,
)
from epd2_identity_service.contacts import (
    ContactChannelClass,
    ContactStatus,
    assert_not_last_verified_channel,
    assert_unique_within_scope,
    build_contact,
    mask_contact,
    normalize_contact,
    refuse_auto_merge,
)
from epd2_identity_service.credentials import (
    CredentialBinding,
    CredentialStatus,
    CredentialType,
    assert_removal_leaves_a_way_in,
    enroll_credential,
)
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AccountLockedError,
    AccountQuarantinedError,
    AssuranceInsufficientError,
    AssuranceStaleError,
    ConfigurationDeadlineRemovalRefusedError,
    ConfigurationRelaxationNotGovernedError,
    ContactAlreadyInUseError,
    ContactAutoMergeRefusedError,
    ContactNotNormalizableError,
    CredentialRevokedError,
    ForbiddenAccountLifecycleTransitionError,
    ForbiddenClosureRequestTransitionError,
    IdentityMappingPurposeMismatchError,
    IdentityMappingScopeMismatchError,
    LastRemainingCredentialError,
    LastVerifiedChannelError,
    ResourceVersionStaleError,
    SessionExpiredError,
    SessionReplayDetectedError,
    SessionRevokedError,
    StepUpBindingMismatchError,
    StepUpExpiredError,
    StepUpObjectChangedError,
    UnrestrictedMappingLookupRefusedError,
)
from epd2_identity_service.identifiers import (
    MappingPurpose,
    OrganizationLevel,
    OrganizationScope,
    ScopedIdentityReference,
    SessionId,
)
from epd2_identity_service.mappings import (
    IdentityMapping,
    MappingAccessPolicy,
    MappingResolutionRequest,
    MappingStatus,
    refuse_unrestricted_lookup,
    resolve_mapping,
)
from epd2_identity_service.secret_storage import DeterministicSecureRandom
from epd2_identity_service.sessions import (
    RotationTrigger,
    SessionScope,
    SessionStatus,
    issue_session,
    refresh_session,
    revoke_session,
    rotate_session,
)
from epd2_identity_service.stepup import (
    StepUpBinding,
    StepUpResult,
    StepUpStatus,
    complete_step_up,
    issue_step_up_challenge,
    redeem_step_up,
)
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

# --- account lifecycle ------------------------------------------------------


def test_new_account_is_pending_and_activates_only_through_the_registry() -> None:
    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    assert record.account_status is AccountRegistryStatus.PENDING
    activated = activate_account_record(record, expected_version=1, activated_at=NOW)
    assert activated.account_status is AccountRegistryStatus.ACTIVE
    assert activated.activated_at == NOW
    assert activated.version == 2


def test_stale_version_is_refused() -> None:
    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    with pytest.raises(ResourceVersionStaleError):
        activate_account_record(record, expected_version=7, activated_at=NOW)


def test_canonical_status_enum_has_exactly_canon_seven_two_s_six_values() -> None:
    assert [status.value for status in AccountRegistryStatus] == [
        "pending",
        "active",
        "restricted",
        "suspended",
        "recovery_pending",
        "closed",
    ]
    for forbidden in ("locked", "closure_pending", "deleted_or_anonymized"):
        assert forbidden not in {status.value for status in AccountRegistryStatus}


def test_a_lock_does_not_change_the_account_status() -> None:
    """OD-P14-01: the lock is a record, the status is untouched."""
    record = activate_account_record(
        create_account_record(account_id=account_id(), scope=scope(), created_at=NOW),
        expected_version=1,
        activated_at=NOW,
    )
    held = lock(record.account_id)
    assert record.account_status is AccountRegistryStatus.ACTIVE
    with pytest.raises(AccountLockedError):
        assert_account_usable(record, locks=(held,), restrictions=(), now=NOW)
    assert record.account_status is AccountRegistryStatus.ACTIVE


def test_security_quarantine_is_a_restriction_not_a_status() -> None:
    record = activate_account_record(
        create_account_record(account_id=account_id(), scope=scope(), created_at=NOW),
        expected_version=1,
        activated_at=NOW,
    )
    quarantine = restriction(record.account_id)
    assert quarantine.restriction_class is AccountRestrictionClass.SECURITY_QUARANTINE
    with pytest.raises(AccountQuarantinedError):
        assert_account_usable(record, locks=(), restrictions=(quarantine,), now=NOW)


def test_a_lock_and_a_closure_request_can_hold_while_the_account_is_active() -> None:
    """The point of OD-P14-01's representation: three separate facts."""
    record = activate_account_record(
        create_account_record(account_id=account_id(), scope=scope(), created_at=NOW),
        expected_version=1,
        activated_at=NOW,
    )
    request = open_closure_request(
        record,
        existing=None,
        closure_request_id=uuid4(),
        closure_reason="member_request",
        requested_at=NOW,
        cooling_off=timedelta(days=14),
        retention_acknowledged=True,
        membership_notice_acknowledged=True,
    )
    assert record.account_status is AccountRegistryStatus.ACTIVE
    assert request.is_open()
    assert lock(record.account_id).is_in_force(NOW)


def test_closure_completes_only_after_the_cooling_off_window() -> None:
    record = activate_account_record(
        create_account_record(account_id=account_id(), scope=scope(), created_at=NOW),
        expected_version=1,
        activated_at=NOW,
    )
    request = open_closure_request(
        record,
        existing=None,
        closure_request_id=uuid4(),
        closure_reason="member_request",
        requested_at=NOW,
        cooling_off=timedelta(days=14),
        retention_acknowledged=True,
        membership_notice_acknowledged=True,
    )
    with pytest.raises(ForbiddenClosureRequestTransitionError):
        complete_closure(record, request, expected_version=2, completed_at=NOW + timedelta(days=1))
    closed, completed = complete_closure(
        record, request, expected_version=2, completed_at=NOW + timedelta(days=15)
    )
    assert closed.account_status is AccountRegistryStatus.CLOSED
    assert completed.state is ClosureRequestState.COMPLETED


def test_a_closure_request_is_cancellable_during_cooling_off() -> None:
    record = activate_account_record(
        create_account_record(account_id=account_id(), scope=scope(), created_at=NOW),
        expected_version=1,
        activated_at=NOW,
    )
    request = open_closure_request(
        record,
        existing=None,
        closure_request_id=uuid4(),
        closure_reason="member_request",
        requested_at=NOW,
        cooling_off=timedelta(days=14),
        retention_acknowledged=True,
        membership_notice_acknowledged=False,
    )
    cancelled = cancel_closure_request(request, cancelled_at=NOW + timedelta(days=2))
    assert cancelled.state is ClosureRequestState.CANCELLED


def test_anonymization_is_an_outcome_of_a_closed_account_and_runs_once() -> None:
    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    with pytest.raises(ForbiddenAccountLifecycleTransitionError):
        begin_anonymization(record, expected_version=1)
    closed = record.with_status(AccountRegistryStatus.CLOSED)
    started = begin_anonymization(closed, expected_version=2)
    assert started.anonymization_state is AnonymizationState.IN_PROGRESS
    completed = complete_anonymization(started, expected_version=3)
    assert completed.anonymization_state is AnonymizationState.COMPLETED


# --- contacts ---------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Anna.Beispiel@EPD.example ", "anna.beispiel@epd.example"),
        ("a@b.example", "a@b.example"),
    ],
)
def test_email_normalization(raw: str, expected: str) -> None:
    assert normalize_contact(ContactChannelClass.EMAIL, raw) == expected


def test_email_normalization_does_not_strip_dots_or_tags() -> None:
    """Two addresses at two providers are two people."""
    assert normalize_contact(ContactChannelClass.EMAIL, "a.b+x@c.example") == "a.b+x@c.example"


@pytest.mark.parametrize("raw", ["no-at-sign", "a@b", "a@@b.example", "a @b.example", "@b.example"])
def test_unnormalizable_email_fails_closed(raw: str) -> None:
    with pytest.raises(ContactNotNormalizableError):
        normalize_contact(ContactChannelClass.EMAIL, raw)


def test_phone_normalization_requires_e164() -> None:
    assert normalize_contact(ContactChannelClass.PHONE, "+49 (030) 1234-5678") == "+4903012345678"
    with pytest.raises(ContactNotNormalizableError):
        normalize_contact(ContactChannelClass.PHONE, "030 12345678")


def test_masked_contact_reveals_neither_local_part_nor_domain() -> None:
    masked = mask_contact(ContactChannelClass.EMAIL, "anna.beispiel@epd.example")
    assert masked == "a***@e***.example"
    assert "anna" not in masked


def test_contact_uniqueness_is_scoped_and_never_merges() -> None:
    left = build_contact(
        contact_id=uuid4(),
        account_id=account_id(),
        channel_class=ContactChannelClass.EMAIL,
        raw_value="familie@epd.example",
        scope=scope(),
        added_at=NOW,
    )
    other_account = account_id("44444444-4444-4444-8444-444444444444")
    right = build_contact(
        contact_id=uuid4(),
        account_id=other_account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="familie@epd.example",
        scope=scope(),
        added_at=NOW,
    )
    with pytest.raises(ContactAlreadyInUseError):
        assert_unique_within_scope(right, (left,))
    with pytest.raises(ContactAutoMergeRefusedError):
        refuse_auto_merge(left.account_id, right.account_id)


def test_a_contact_in_another_scope_is_not_a_collision() -> None:
    left = build_contact(
        contact_id=uuid4(),
        account_id=account_id(),
        channel_class=ContactChannelClass.EMAIL,
        raw_value="a@b.example",
        scope=scope(),
        added_at=NOW,
    )
    other_scope = OrganizationScope(
        level=OrganizationLevel.KREIS, organizational_unit_id=scope().organizational_unit_id
    )
    right = build_contact(
        contact_id=uuid4(),
        account_id=account_id("55555555-5555-4555-8555-555555555555"),
        channel_class=ContactChannelClass.EMAIL,
        raw_value="a@b.example",
        scope=other_scope,
        added_at=NOW,
    )
    assert_unique_within_scope(right, (left,))


def test_the_last_verified_channel_cannot_be_removed() -> None:
    contact = build_contact(
        contact_id=uuid4(),
        account_id=account_id(),
        channel_class=ContactChannelClass.EMAIL,
        raw_value="a@b.example",
        scope=scope(),
        added_at=NOW,
    ).transitioned(ContactStatus.VERIFICATION_PENDING, at=NOW)
    verified = contact.transitioned(ContactStatus.VERIFIED, at=NOW)
    with pytest.raises(LastVerifiedChannelError):
        assert_not_last_verified_channel(verified, (verified,))


# --- credentials and passkeys -----------------------------------------------


def test_credential_state_refusals_are_distinct() -> None:
    credential = enroll_credential(
        credential_id=new_credential_id(),
        account_id=account_id(),
        credential_type=CredentialType.PASSKEY,
        metadata=credential_metadata(),
        created_at=NOW,
        existing=(),
        requires_confirmation=False,
    )
    from epd2_identity_service.credentials import CredentialRevocation

    revoked = credential.revoked(
        CredentialRevocation(revoked_at=NOW, reason_code="CREDENTIAL_REVOKED", actor_class="holder")
    )
    with pytest.raises(CredentialRevokedError):
        revoked.assert_usable(NOW)
    assert revoked.status is CredentialStatus.REVOKED


def test_the_only_credential_cannot_be_removed_without_a_recovery_path() -> None:
    credential = enroll_credential(
        credential_id=new_credential_id(),
        account_id=account_id(),
        credential_type=CredentialType.PASSKEY,
        metadata=credential_metadata(),
        created_at=NOW,
        existing=(),
        requires_confirmation=False,
    )
    with pytest.raises(LastRemainingCredentialError):
        assert_removal_leaves_a_way_in(
            credential=credential,
            all_credentials=(credential,),
            recovery_path_available=False,
        )
    assert_removal_leaves_a_way_in(
        credential=credential, all_credentials=(credential,), recovery_path_available=True
    )


def test_a_synced_passkey_never_reaches_high() -> None:
    """OD-P14-08, at the level the decision is made."""
    assert assurance_for_passkey(CredentialBinding.SYNCED) is (
        AuthenticationAssuranceLevel.SUBSTANTIAL
    )
    assert assurance_for_passkey(CredentialBinding.DEVICE_BOUND) is (
        AuthenticationAssuranceLevel.HIGH
    )


# --- assurance --------------------------------------------------------------


def test_sms_otp_carries_no_assurance_level_at_all() -> None:
    assert assurance_ceiling(AuthenticationMethod.SMS_OTP) is AuthenticationAssuranceLevel.NONE


def test_two_substantial_methods_do_not_add_up_to_high() -> None:
    combined = combine_methods(
        (AuthenticationMethod.PASSWORD_WITH_MFA, AuthenticationMethod.PASSKEY_SYNCED)
    )
    assert combined is AuthenticationAssuranceLevel.SUBSTANTIAL


def test_risk_lowers_effective_assurance_and_never_raises_it() -> None:
    assert (
        apply_risk_downgrade(AuthenticationAssuranceLevel.HIGH, RiskState.ELEVATED)
        is AuthenticationAssuranceLevel.SUBSTANTIAL
    )
    assert (
        apply_risk_downgrade(AuthenticationAssuranceLevel.LOW, RiskState.NORMAL)
        is AuthenticationAssuranceLevel.LOW
    )
    assert (
        apply_risk_downgrade(AuthenticationAssuranceLevel.HIGH, RiskState.SUSPICIOUS)
        is AuthenticationAssuranceLevel.LOW
    )


def test_a_non_normal_risk_state_must_name_its_signals() -> None:
    with pytest.raises(ValueError, match="name its signals"):
        AssuranceEvidence(
            methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
            credential_binding=CredentialBinding.DEVICE_BOUND,
            risk_state=RiskState.SUSPICIOUS,
            named_signals=(),
        )


def test_assurance_evaluation_is_a_conjunction_with_no_or() -> None:
    configuration = default_configuration()
    requirement = ACTION_REQUIREMENTS["remove_passkey"]
    with pytest.raises(AssuranceInsufficientError):
        evaluate_requirement(
            assurance=None,
            identity_assurance=None,
            requirement=requirement,
            configuration=configuration,
            now=NOW,
        )
    weak = assurance(
        AuthenticationMethod.PASSWORD_WITH_MFA, binding=CredentialBinding.NOT_APPLICABLE
    )
    with pytest.raises(AssuranceInsufficientError):
        evaluate_requirement(
            assurance=weak,
            identity_assurance=None,
            requirement=requirement,
            configuration=configuration,
            now=NOW,
        )
    strong = assurance()
    evaluate_requirement(
        assurance=strong,
        identity_assurance=None,
        requirement=requirement,
        configuration=configuration,
        now=NOW,
    )
    with pytest.raises(AssuranceStaleError):
        evaluate_requirement(
            assurance=strong,
            identity_assurance=None,
            requirement=requirement,
            configuration=configuration,
            now=NOW + timedelta(minutes=16),
        )


# --- configuration ----------------------------------------------------------


def test_governed_defaults_match_the_specification_table() -> None:
    configuration = default_configuration()
    assert configuration.idle_timeout(AuthenticationAssuranceLevel.LOW) == timedelta(minutes=30)
    assert configuration.absolute_timeout(AuthenticationAssuranceLevel.LOW) == timedelta(days=7)
    assert configuration.idle_timeout(AuthenticationAssuranceLevel.SUBSTANTIAL) == timedelta(
        minutes=30
    )
    assert configuration.absolute_timeout(AuthenticationAssuranceLevel.SUBSTANTIAL) == timedelta(
        hours=24
    )
    assert configuration.idle_timeout(AuthenticationAssuranceLevel.HIGH) == timedelta(minutes=15)
    assert configuration.absolute_timeout(AuthenticationAssuranceLevel.HIGH) == timedelta(hours=8)
    assert configuration.freshness_window(ActionClass.CONSEQUENTIAL_ACTION) == timedelta(minutes=15)
    assert configuration.freshness_window(ActionClass.OFFICIAL_SUBMISSION) == timedelta(minutes=60)
    assert configuration.freshness_window(ActionClass.SECURITY_OR_CONTACT_CHANGE) == timedelta(
        minutes=15
    )


def test_stricter_is_free_and_relaxing_is_governed() -> None:
    configuration = default_configuration()
    tightened = tighten_freshness_window(
        configuration, action_class=ActionClass.CONSEQUENTIAL_ACTION, proposed=timedelta(minutes=5)
    )
    assert tightened.freshness_window(ActionClass.CONSEQUENTIAL_ACTION) == timedelta(minutes=5)
    with pytest.raises(ConfigurationRelaxationNotGovernedError):
        tighten_freshness_window(
            configuration,
            action_class=ActionClass.CONSEQUENTIAL_ACTION,
            proposed=timedelta(hours=2),
        )
    with pytest.raises(ConfigurationRelaxationNotGovernedError):
        relax_freshness_window(
            configuration,
            action_class=ActionClass.CONSEQUENTIAL_ACTION,
            proposed=timedelta(hours=2),
            authority=None,
        )
    relaxed = relax_freshness_window(
        configuration,
        action_class=ActionClass.CONSEQUENTIAL_ACTION,
        proposed=timedelta(minutes=20),
        authority=GovernanceAuthority(
            authority_reference="board/2026-07", reason_code="CONFIGURATION_RELAXATION_NOT_GOVERNED"
        ),
    )
    assert relaxed.freshness_window(ActionClass.CONSEQUENTIAL_ACTION) == timedelta(minutes=20)


def test_no_configuration_can_remove_a_deadline() -> None:
    configuration = default_configuration()
    with pytest.raises(ConfigurationDeadlineRemovalRefusedError):
        tighten_session_timeout(
            configuration, level=AuthenticationAssuranceLevel.HIGH, idle=timedelta(0)
        )


# --- sessions ---------------------------------------------------------------


def _session_scope(workspace: WorkspaceId = WorkspaceId.MEMBER_APPLICATION) -> SessionScope:
    return SessionScope(
        workspace=workspace,
        origin=workspace_origin(workspace),
        capabilities=frozenset({"member-shell"}),
    )


def test_a_session_always_carries_both_deadlines() -> None:
    session, _refresh, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=_session_scope(),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    assert session.idle_deadline == NOW + timedelta(minutes=15)
    assert session.absolute_deadline == NOW + timedelta(hours=8)
    assert session.effective_expiry() == session.idle_deadline


def test_idle_and_absolute_deadlines_are_both_enforced() -> None:
    session, _refresh, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=_session_scope(),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    with pytest.raises(SessionExpiredError):
        session.assert_presentable(origin=session.scope.origin, now=NOW + timedelta(minutes=16))
    with pytest.raises(SessionExpiredError):
        session.assert_presentable(origin=session.scope.origin, now=NOW + timedelta(hours=9))


def test_rotation_changes_the_session_identifier() -> None:
    session, _refresh, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=_session_scope(),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    rotated, new_refresh = rotate_session(
        session,
        new_session_id=new_session_id(),
        trigger=RotationTrigger.AUTHENTICATION,
        rotated_at=NOW + timedelta(minutes=1),
        configuration=default_configuration(),
        random=DeterministicSecureRandom(seed="rotation"),
    )
    assert rotated.session_id != session.session_id
    assert rotated.rotation_count == 1
    assert new_refresh


def test_a_revoked_session_cannot_refresh() -> None:
    session, refresh_token, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=_session_scope(),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    revoked = revoke_session(
        session, reason_code="SESSION_REVOKED", actor_class="holder", revoked_at=NOW
    )
    assert revoked.status is SessionStatus.REVOKED
    with pytest.raises(SessionRevokedError):
        refresh_session(
            revoked,
            presented_refresh_token=refresh_token,
            refreshed_at=NOW + timedelta(minutes=1),
            configuration=default_configuration(),
            random=DeterministicSecureRandom(),
        )


def test_a_rotated_refresh_token_presented_again_is_a_replay() -> None:
    session, refresh_token, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=_session_scope(),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    refreshed, _new_token = refresh_session(
        session,
        presented_refresh_token=refresh_token,
        refreshed_at=NOW + timedelta(minutes=1),
        configuration=default_configuration(),
        random=DeterministicSecureRandom(seed="second"),
    )
    with pytest.raises(SessionReplayDetectedError):
        refresh_session(
            refreshed,
            presented_refresh_token=refresh_token,
            refreshed_at=NOW + timedelta(minutes=2),
            configuration=default_configuration(),
            random=DeterministicSecureRandom(seed="third"),
        )


# --- step-up ----------------------------------------------------------------


def _issued_step_up(
    resource_version: int = 1,
) -> tuple[ScopedIdentityReference, SessionId, StepUpBinding, StepUpResult]:
    actor = reference(account_id())
    session_uuid = new_session_id()
    binding = step_up_binding(
        actor=actor, session_id=session_uuid, resource_version=resource_version
    )
    challenge = issue_step_up_challenge(
        challenge_id=uuid4(),
        binding=binding,
        requirement=ACTION_REQUIREMENTS["voting_handoff"],
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    result = complete_step_up(
        challenge,
        presented_nonce=challenge.nonce,
        method=AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        achieved_assurance=AuthenticationAssuranceLevel.HIGH,
        completed_at=NOW,
    )
    return actor, session_uuid, binding, result


def test_a_changed_object_version_voids_the_confirmation() -> None:
    actor, session_uuid, _binding, result = _issued_step_up(resource_version=1)
    later = step_up_binding(actor=actor, session_id=session_uuid, resource_version=2)
    with pytest.raises(StepUpObjectChangedError):
        redeem_step_up(result, binding=later, now=NOW)


def test_a_confirmation_is_bound_to_its_action_and_actor() -> None:
    actor, session_uuid, _binding, result = _issued_step_up()
    other = step_up_binding(
        actor=actor, session_id=session_uuid, action_code="remove_passkey", resource_version=1
    )
    with pytest.raises(StepUpBindingMismatchError):
        redeem_step_up(result, binding=other, now=NOW)


def test_a_confirmation_authorises_exactly_one_act() -> None:
    _actor, _session, binding, result = _issued_step_up()
    consumed = redeem_step_up(result, binding=binding, now=NOW)
    assert consumed.status is StepUpStatus.CONSUMED
    from epd2_identity_service.exceptions import StepUpAlreadyConsumedError

    with pytest.raises(StepUpAlreadyConsumedError):
        redeem_step_up(consumed, binding=binding, now=NOW)


def test_step_up_freshness_is_the_governed_window() -> None:
    _actor, _session, binding, result = _issued_step_up()
    with pytest.raises(StepUpExpiredError):
        redeem_step_up(result, binding=binding, now=NOW + timedelta(minutes=16))


# --- identity mappings ------------------------------------------------------


def _mapping(purpose: MappingPurpose = MappingPurpose.AUDIT_ATTRIBUTION) -> IdentityMapping:
    source = reference(account_id(), purpose=purpose)
    target = reference(account_id(), purpose=purpose, domain_owner="finance-service")
    from epd2_identity_service.identifiers import IdentifierSpace

    return IdentityMapping(
        mapping_id=uuid4(),
        purpose=purpose,
        scope=scope(),
        domain_owner="identity-service",
        source_space=IdentifierSpace.ACCOUNT,
        target_space=IdentifierSpace.SCOPED_ACTOR,
        source_reference=source,
        target_reference=target,
        access_policy=MappingAccessPolicy(
            permitted_domain_owners=frozenset({"finance-service"}),
            requires_privileged_grant=False,
        ),
        status=MappingStatus.ACTIVE,
        retention_class="account_record",
        audit_reference="audit/mapping/1",
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )


def test_a_mapping_resolves_only_for_its_own_purpose_and_scope() -> None:
    mapping = _mapping()
    ok = MappingResolutionRequest(
        purpose=MappingPurpose.AUDIT_ATTRIBUTION,
        scope=scope(),
        requesting_domain_owner="finance-service",
        source_reference=mapping.source_reference,
    )
    assert resolve_mapping(mapping, ok, now=NOW) == mapping.target_reference

    wrong_purpose = MappingResolutionRequest(
        purpose=MappingPurpose.VOTING_ENTRY,
        scope=scope(),
        requesting_domain_owner="finance-service",
        source_reference=mapping.source_reference,
    )
    with pytest.raises(IdentityMappingPurposeMismatchError):
        resolve_mapping(mapping, wrong_purpose, now=NOW)

    other_scope = OrganizationScope(
        level=OrganizationLevel.BUND, organizational_unit_id=scope().organizational_unit_id
    )
    wrong_scope = MappingResolutionRequest(
        purpose=MappingPurpose.AUDIT_ATTRIBUTION,
        scope=other_scope,
        requesting_domain_owner="finance-service",
        source_reference=mapping.source_reference,
    )
    with pytest.raises(IdentityMappingScopeMismatchError):
        resolve_mapping(mapping, wrong_scope, now=NOW)


def test_there_is_no_unrestricted_mapping_enumeration() -> None:
    with pytest.raises(UnrestrictedMappingLookupRefusedError):
        refuse_unrestricted_lookup(purpose=None, scope=None)
    with pytest.raises(UnrestrictedMappingLookupRefusedError):
        refuse_unrestricted_lookup(purpose=MappingPurpose.AUDIT_ATTRIBUTION, scope=None)


def test_two_purposes_produce_two_unrelatable_references() -> None:
    account = account_id()
    left = reference(account, purpose=MappingPurpose.SESSION)
    right = reference(account, purpose=MappingPurpose.VOTING_ENTRY)
    assert left.reference != right.reference


def test_the_derivation_needs_a_deployment_secret() -> None:
    from epd2_identity_service.identifiers import IdentifierSpace, derive_scoped_reference

    with pytest.raises(ValueError, match="at least 32 bytes"):
        derive_scoped_reference(
            space=IdentifierSpace.ACCOUNT,
            value="x",
            purpose=MappingPurpose.SESSION,
            scope=scope(),
            domain_owner="identity-service",
            derivation_salt=b"short",
        )
    assert len(SALT) == 32
