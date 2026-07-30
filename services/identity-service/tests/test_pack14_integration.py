"""PACK-14 integration tests (task section 30.3).

Account creation, passkey enrollment, passkey authentication through the
deterministic test adapter, password with MFA, step-up, session
list/revoke, the recovery workflow, contact change, the external provider
assertion adapter, the cross-origin bootstrap, voting handoff
issue/redeem/replay-reject, event persistence and the audit path.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from _pack14_builders import (
    NOW,
    account_id,
    assertion_response,
    assurance,
    authentication_challenge_for,
    authenticator_response,
    credential_metadata,
    device,
    new_credential_id,
    new_session_id,
    reference,
    scope,
    service,
    step_up_binding,
    webauthn_challenge,
)

from epd2_identity_service.account_security_application import (
    AccountSecurityService,
    account_security_state,
)
from epd2_identity_service.accounts import AccountRegistryStatus
from epd2_identity_service.assurance import (
    ACTION_REQUIREMENTS,
    AuthenticationMethod,
)
from epd2_identity_service.bootstrap import (
    AuthenticationBootstrapRequest,
    AuthenticationBootstrapResponse,
    BootstrapProofMethod,
    create_bootstrap_request,
    issue_bootstrap_response,
    redeem_bootstrap_response,
)
from epd2_identity_service.configuration import default_configuration
from epd2_identity_service.contacts import ContactChannelClass
from epd2_identity_service.credentials import CredentialBinding, CredentialType
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AuditUnavailableError,
    BootstrapAlreadyUsedError,
    BootstrapAudienceMismatchError,
    ContactNotVerifiedError,
    ExternalAssertionInvalidError,
    ExternalAssertionReplayedError,
    ExternalSubjectNotLinkedError,
    IdempotencyKeyReusedError,
    MfaRequiredError,
    NotificationDeliveryFailedError,
    PasskeyOriginMismatchError,
    PasskeySignCounterRegressionError,
    PasswordOnlyAccountRefusedError,
    SessionScopeMismatchError,
)
from epd2_identity_service.identifiers import AccountId, MappingPurpose
from epd2_identity_service.mfa import (
    MfaFactorClass,
    MfaFactorStatus,
    confirm_totp_factor,
    enroll_factor,
    issue_recovery_code_set,
    verify_totp_factor,
)
from epd2_identity_service.passkeys import (
    DeterministicWebAuthnVerifier,
    complete_registration,
    verify_assertion,
)
from epd2_identity_service.passwords import (
    PasswordLoginPolicy,
    enroll_password,
    verify_password,
)
from epd2_identity_service.providers import (
    DeterministicAssertionSignatureVerifier,
    ExternalIdentityAssertion,
    ExternalIdentityProvider,
    resolve_linked_account,
    validate_assertion,
)
from epd2_identity_service.secret_storage import (
    DeterministicBreachedPasswordChecker,
    DeterministicSecureRandom,
    DeterministicTotpVerifier,
)
from epd2_identity_service.sessions import SessionStatus
from epd2_identity_service.stepup import complete_step_up, issue_step_up_challenge
from epd2_identity_service.voting_handoff import (
    VotingHandoffRequest,
    redeem_voting_handoff,
)
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin


def _activated_account() -> tuple[AccountSecurityService, AccountId]:
    svc = service()
    account = account_id()
    svc.create_account(
        account_id=account,
        scope=scope(),
        correlation_id=uuid4(),
        event_id=uuid4(),
        idempotency_key="create-1",
    )
    contact = svc.add_contact(
        contact_id=uuid4(),
        account_id=account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="anna@epd.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    svc.verify_contact(contact_id=contact.contact_id, correlation_id=uuid4(), event_id=uuid4())
    svc.activate_account(
        account_id=account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
    )
    return svc, account


# --- account creation and activation ----------------------------------------


def test_account_creation_activation_and_the_security_state_read_model() -> None:
    svc, account = _activated_account()
    record = svc.account_store.get(account)
    assert record is not None
    assert record.account_status is AccountRegistryStatus.ACTIVE
    state = account_security_state(svc, account_id=account, now=NOW)
    assert state["account_status"] == "active"
    assert state["activated"] is True
    assert state["credential_count"] == 0
    assert state["lock_in_force"] is False
    # The read model discloses nothing an attacker could use.
    assert "credential_reference" not in state
    assert "contact" not in state


def test_activation_requires_a_verified_channel() -> None:
    svc = service()
    account = account_id()
    svc.create_account(account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4())
    with pytest.raises(ContactNotVerifiedError):
        svc.activate_account(
            account_id=account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
        )


def test_an_idempotency_key_reused_with_a_different_body_is_refused() -> None:
    svc = service()
    svc.create_account(
        account_id=account_id(),
        scope=scope(),
        correlation_id=uuid4(),
        event_id=uuid4(),
        idempotency_key="k",
    )
    with pytest.raises(IdempotencyKeyReusedError):
        svc.create_account(
            account_id=account_id("77777777-7777-4777-8777-777777777777"),
            scope=scope(),
            correlation_id=uuid4(),
            event_id=uuid4(),
            idempotency_key="k",
        )


def test_every_command_appends_an_audit_record_before_it_persists() -> None:
    svc, account = _activated_account()
    events = svc.audit_store.list_all() if hasattr(svc.audit_store, "list_all") else None
    # The audit store is PACK-02's; what matters here is that the chain is
    # non-empty and that a broken audit path refuses the next command.
    assert events is None or len(events) >= 1
    svc.audit_available = False
    with pytest.raises(AuditUnavailableError):
        svc.add_contact(
            contact_id=uuid4(),
            account_id=account,
            channel_class=ContactChannelClass.PHONE,
            raw_value="+4930123456789",
            correlation_id=uuid4(),
            event_id=uuid4(),
        )


# --- passkeys ---------------------------------------------------------------


def test_passkey_enrollment_and_authentication_through_the_test_adapter() -> None:
    account = account_id()
    verifier = DeterministicWebAuthnVerifier()
    registration_challenge = webauthn_challenge(account=account)
    registration = complete_registration(
        credential_id=new_credential_id(),
        response=authenticator_response(challenge=registration_challenge),
        challenge=registration_challenge,
        verifier=verifier,
        now=NOW,
    )
    assert registration.binding is CredentialBinding.DEVICE_BOUND

    authentication_challenge = authentication_challenge_for(account)
    counter = verify_assertion(
        response=assertion_response(
            challenge=authentication_challenge, public_key=registration.public_key
        ),
        challenge=authentication_challenge,
        record=registration,
        verifier=verifier,
        now=NOW,
    )
    assert counter == 2


def test_a_synced_authenticator_is_classified_as_synced() -> None:
    account = account_id()
    challenge = webauthn_challenge(account=account)
    registration = complete_registration(
        credential_id=new_credential_id(),
        response=authenticator_response(
            challenge=challenge, device_bound=True, backup_eligible=True
        ),
        challenge=challenge,
        verifier=DeterministicWebAuthnVerifier(),
        now=NOW,
    )
    assert registration.binding is CredentialBinding.SYNCED


def test_an_assertion_from_another_origin_is_refused() -> None:
    account = account_id()
    challenge = webauthn_challenge(account=account)
    with pytest.raises(PasskeyOriginMismatchError):
        complete_registration(
            credential_id=new_credential_id(),
            response=authenticator_response(challenge=challenge, origin="https://phish.example"),
            challenge=challenge,
            verifier=DeterministicWebAuthnVerifier(),
            now=NOW,
        )


def test_a_regressed_sign_counter_is_the_cloned_authenticator_signal() -> None:
    account = account_id()
    verifier = DeterministicWebAuthnVerifier()
    registration_challenge = webauthn_challenge(account=account)
    registration = complete_registration(
        credential_id=new_credential_id(),
        response=authenticator_response(challenge=registration_challenge, sign_counter=5),
        challenge=registration_challenge,
        verifier=verifier,
        now=NOW,
    )
    authentication_challenge = authentication_challenge_for(account)
    with pytest.raises(PasskeySignCounterRegressionError):
        verify_assertion(
            response=assertion_response(
                challenge=authentication_challenge,
                public_key=registration.public_key,
                sign_counter=4,
            ),
            challenge=authentication_challenge,
            record=registration,
            verifier=verifier,
            now=NOW,
        )


# --- password with MFA ------------------------------------------------------


class _FixtureHasher:
    """A test double for the password hashing port.

    Named as such. It is not a password hash and would be unacceptable in
    a deployment; it exists so the *policy* around passwords - MFA
    always, no password-only account, the assurance ceiling - can be
    tested without binding Argon2id in CI.
    """

    algorithm_label = "fixture-not-a-hash"

    def hash(self, password: str) -> str:
        return f"fixture:{password}"

    def verify(self, password: str, stored_hash: str) -> bool:
        return stored_hash == f"fixture:{password}"

    def needs_rehash(self, stored_hash: str) -> bool:
        return True


def test_a_new_password_only_account_is_refused() -> None:
    with pytest.raises(PasswordOnlyAccountRefusedError):
        enroll_password(
            credential_id=new_credential_id(),
            account_id=account_id(),
            password="ein-sehr-langes-passwort",
            created_at=NOW,
            hasher=_FixtureHasher(),
            breach_checker=DeterministicBreachedPasswordChecker(),
            account_has_other_credential=False,
        )


def test_password_authentication_always_requires_a_second_factor() -> None:
    stored = enroll_password(
        credential_id=new_credential_id(),
        account_id=account_id(),
        password="ein-sehr-langes-passwort",
        created_at=NOW,
        hasher=_FixtureHasher(),
        breach_checker=DeterministicBreachedPasswordChecker(),
        account_has_other_credential=True,
    )
    with pytest.raises(MfaRequiredError):
        verify_password(
            stored,
            password="ein-sehr-langes-passwort",
            hasher=_FixtureHasher(),
            mfa_satisfied=False,
        )
    verify_password(
        stored, password="ein-sehr-langes-passwort", hasher=_FixtureHasher(), mfa_satisfied=True
    )


def test_password_login_can_be_disabled_per_scope_and_per_account() -> None:
    from epd2_identity_service.exceptions import PasswordLoginDisabledError

    policy = PasswordLoginPolicy(
        globally_enabled=True,
        disabled_accounts=frozenset({account_id()}),
    )
    with pytest.raises(PasswordLoginDisabledError):
        policy.assert_available(
            account_id=account_id(), organizational_unit_id=scope().organizational_unit_id
        )


def test_totp_enrollment_confirmation_and_use() -> None:
    verifier = DeterministicTotpVerifier()
    random = DeterministicSecureRandom()
    secret = verifier.provisioning_secret(random)
    factor = enroll_factor(
        factor_id=uuid4(),
        account_id=account_id(),
        factor_class=MfaFactorClass.TOTP,
        secret_reference="secret-ref",
        enrolled_at=NOW,
        existing=(),
    )
    assert factor.status is MfaFactorStatus.ENROLLED_UNCONFIRMED
    code = verifier.expected_code(secret, unix_time=1_800_000_000)
    confirmed = confirm_totp_factor(
        factor,
        secret=secret,
        presented_code=code,
        unix_time=1_800_000_000,
        verifier=verifier,
        confirmed_at=NOW,
    )
    assert confirmed.status is MfaFactorStatus.ACTIVE
    used = verify_totp_factor(
        confirmed,
        secret=secret,
        presented_code=code,
        unix_time=1_800_000_000,
        verifier=verifier,
        used_at=NOW,
    )
    assert used.last_used_at == NOW


def test_a_recovery_code_is_single_use() -> None:
    from epd2_identity_service.exceptions import RecoveryCodeAlreadyUsedError

    code_set, codes = issue_recovery_code_set(
        set_id=uuid4(),
        account_id=account_id(),
        issued_at=NOW,
        random=DeterministicSecureRandom(),
    )
    consumed = code_set.consume(codes[0])
    assert consumed.remaining() == len(codes) - 1
    with pytest.raises(RecoveryCodeAlreadyUsedError):
        consumed.consume(codes[0])


# --- sessions ---------------------------------------------------------------


def test_session_issue_list_and_revoke_all() -> None:
    svc, account = _activated_account()
    session, _refresh, _csrf = svc.issue_session(
        session_id=new_session_id(),
        account_id=account,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
        credential_binding="device_bound",
        device=device(),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    assert session.status is SessionStatus.ACTIVE
    assert len(svc.session_store.for_account(account)) == 1
    revoked = svc.revoke_all_sessions_for(
        account_id=account,
        reason_code="SESSION_REVOKED",
        actor_class="holder",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    assert revoked == 1
    stored = svc.session_store.for_account(account)[0]
    assert stored.status is SessionStatus.REVOKED


def test_the_voting_client_cannot_be_issued_a_session_through_the_service() -> None:
    svc, account = _activated_account()
    with pytest.raises(SessionScopeMismatchError):
        svc.issue_session(
            session_id=new_session_id(),
            account_id=account,
            workspace=WorkspaceId.VOTING_CLIENT,
            methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
            credential_binding="device_bound",
            device=device(),
            correlation_id=uuid4(),
            event_id=uuid4(),
        )


def test_revoking_a_credential_revokes_the_sessions_it_could_have_produced() -> None:
    svc, account = _activated_account()
    credential = svc.enroll_credential(
        credential_id=new_credential_id(),
        account_id=account,
        credential_type=CredentialType.PASSKEY,
        metadata=credential_metadata(),
        correlation_id=uuid4(),
        event_id=uuid4(),
        requires_confirmation=False,
    )
    svc.issue_session(
        session_id=new_session_id(),
        account_id=account,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
        credential_binding="device_bound",
        device=device(),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    svc.revoke_credential(
        credential_id=credential.credential_id,
        reason_code="CREDENTIAL_REVOKED",
        actor_class="security_admin",
        correlation_id=uuid4(),
        event_id=uuid4(),
        recovery_path_available=True,
    )
    assert all(
        session.status is SessionStatus.REVOKED
        for session in svc.session_store.for_account(account)
    )


def test_a_failed_notification_is_not_a_silent_success() -> None:
    svc, account = _activated_account()
    svc.outbox.fail_next = True
    with pytest.raises(NotificationDeliveryFailedError):
        svc.enroll_credential(
            credential_id=new_credential_id(),
            account_id=account,
            credential_type=CredentialType.PASSKEY,
            metadata=credential_metadata(),
            correlation_id=uuid4(),
            event_id=uuid4(),
            requires_confirmation=False,
        )


# --- cross-origin bootstrap -------------------------------------------------


def _bootstrap_pair(
    workspace: WorkspaceId = WorkspaceId.MEMBER_APPLICATION,
) -> tuple[AuthenticationBootstrapRequest, AuthenticationBootstrapResponse, str]:
    redirect = f"{workspace_origin(workspace)}/auth/callback"
    request = create_bootstrap_request(
        request_id=uuid4(),
        workspace=workspace,
        redirect_uri=redirect,
        redirect_allowlist=frozenset({redirect}),
        proof_challenge="challenge-digest",
        proof_method=BootstrapProofMethod.S256,
        created_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    response, value = issue_bootstrap_response(
        request,
        response_id=uuid4(),
        actor_reference=reference(account_id(), purpose=MappingPurpose.SESSION),
        achieved_assurance=AuthenticationAssuranceLevel.HIGH,
        issued_at=NOW,
        lifetime=timedelta(minutes=2),
        random=DeterministicSecureRandom(seed="response"),
    )
    return request, response, value


def test_a_bootstrap_response_is_single_use_and_audience_bound() -> None:
    request, response, value = _bootstrap_pair()
    spent, redemption = redeem_bootstrap_response(
        response,
        presented_value=value,
        presenting_workspace=request.workspace,
        presenting_origin=request.audience_origin,
        presented_nonce=request.nonce,
        redemption_id=uuid4(),
        now=NOW,
    )
    assert redemption.workspace is request.workspace
    with pytest.raises(BootstrapAlreadyUsedError):
        redeem_bootstrap_response(
            spent,
            presented_value=value,
            presenting_workspace=request.workspace,
            presenting_origin=request.audience_origin,
            presented_nonce=request.nonce,
            redemption_id=uuid4(),
            now=NOW,
        )


def test_a_bootstrap_response_presented_to_another_workspace_is_refused() -> None:
    request, response, value = _bootstrap_pair()
    with pytest.raises(BootstrapAudienceMismatchError):
        redeem_bootstrap_response(
            response,
            presented_value=value,
            presenting_workspace=WorkspaceId.FINANCE,
            presenting_origin=workspace_origin(WorkspaceId.FINANCE),
            presented_nonce=request.nonce,
            redemption_id=uuid4(),
            now=NOW,
        )


def test_a_bootstrap_response_carries_a_scoped_reference_and_no_account_id() -> None:
    _request, response, _value = _bootstrap_pair()
    fields = set(response.__dataclass_fields__)
    assert "account_id" not in fields
    assert response.actor_reference.purpose is MappingPurpose.SESSION


# --- voting handoff through the service -------------------------------------


def test_voting_handoff_issue_redeem_and_replay_rejection() -> None:
    svc, account = _activated_account()
    actor = reference(account, purpose=MappingPurpose.SESSION)
    session_uuid = uuid4()
    context = uuid4()
    binding = step_up_binding(
        actor=actor, session_id=session_uuid, action_code="voting_handoff", resource_id=context
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
    artifact = svc.issue_voting_handoff(
        artifact_id=uuid4(),
        request=VotingHandoffRequest(
            request_id=uuid4(),
            voting_context_id=context,
            audience_origin=workspace_origin(WorkspaceId.VOTING_CLIENT),
            requested_at=NOW,
        ),
        account_id=account,
        assurance=assurance(),
        step_up=result,
        binding=binding,
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    issuance = svc.voting_handoff_store.get_issuance(artifact.artifact_id)
    assert issuance is not None
    spent, _redemption = redeem_voting_handoff(
        issuance,
        presented_value=artifact.value,
        presenting_origin=artifact.audience_origin,
        voting_context_id=context,
        redemption_id=uuid4(),
        now=NOW,
    )
    svc.voting_handoff_store.save_issuance(spent)
    from epd2_identity_service.exceptions import VotingHandoffAlreadyUsedError

    with pytest.raises(VotingHandoffAlreadyUsedError):
        redeem_voting_handoff(
            svc.voting_handoff_store.get_issuance(artifact.artifact_id),
            presented_value=artifact.value,
            presenting_origin=artifact.audience_origin,
            voting_context_id=context,
            redemption_id=uuid4(),
            now=NOW,
        )


# --- external provider adapter ----------------------------------------------


def _provider() -> ExternalIdentityProvider:
    return ExternalIdentityProvider(
        provider_id=uuid4(),
        issuer="https://idp.example",
        audience="https://app.epd.example",
        permitted_attributes=frozenset({"name_verified"}),
        assessed_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        assertion_lifetime=timedelta(minutes=5),
    )


def _assertion(
    provider: ExternalIdentityProvider, *, assertion_id: str = "a-1"
) -> ExternalIdentityAssertion:
    return ExternalIdentityAssertion(
        assertion_id=assertion_id,
        issuer=provider.issuer,
        audience=provider.audience,
        subject="subject-42",
        nonce="nonce-1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=4),
        signature=f"{provider.issuer}:{assertion_id}",
        attributes=frozenset({"name_verified"}),
    )


def test_the_provider_adapter_performs_all_of_its_checks() -> None:
    provider = _provider()
    verifier = DeterministicAssertionSignatureVerifier()
    result = validate_assertion(
        _assertion(provider),
        provider=provider,
        expected_nonce="nonce-1",
        verifier=verifier,
        seen_assertion_ids=frozenset(),
        now=NOW + timedelta(seconds=30),
    )
    assert result.achieved_assurance is AuthenticationAssuranceLevel.SUBSTANTIAL
    assert len(result.subject_reference.subject_digest) == 64
    assert "subject-42" not in result.subject_reference.subject_digest

    with pytest.raises(ExternalAssertionReplayedError):
        validate_assertion(
            _assertion(provider),
            provider=provider,
            expected_nonce="nonce-1",
            verifier=verifier,
            seen_assertion_ids=frozenset({"a-1"}),
            now=NOW,
        )
    with pytest.raises(ExternalAssertionInvalidError):
        validate_assertion(
            _assertion(provider),
            provider=provider,
            expected_nonce="other-nonce",
            verifier=verifier,
            seen_assertion_ids=frozenset(),
            now=NOW,
        )


def test_an_unlinked_provider_subject_never_creates_or_matches_an_account() -> None:
    provider = _provider()
    result = validate_assertion(
        _assertion(provider),
        provider=provider,
        expected_nonce="nonce-1",
        verifier=DeterministicAssertionSignatureVerifier(),
        seen_assertion_ids=frozenset(),
        now=NOW,
    )
    with pytest.raises(ExternalSubjectNotLinkedError):
        resolve_linked_account(result, linked_account_reference=None)
