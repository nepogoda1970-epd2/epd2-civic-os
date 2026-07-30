"""PACK-14 API-negative and security tests (task sections 30.4, 30.5).

Wrong audience, expired bootstrap, replay, stale version, insufficient
assurance, missing approval, recently changed contact, revoked
credential, restricted account, malformed WebAuthn data, invalid provider
assertion, identity-mapping scope violation - and then account
enumeration, CSRF, open redirect, token leakage, cookie flags, log
redaction, rate limiting, session fixation, privilege escalation and
recovery takeover.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from _pack14_builders import (
    NOW,
    account_id,
    assurance,
    device,
    new_session_id,
    reference,
    restriction,
    scope,
    service,
    step_up_binding,
)

from epd2_identity_service.administration import (
    AdminAction,
    BreakGlassInvocation,
    IdentityAdminRole,
    PrivilegedGrantRef,
    authorize_privileged_action,
    refuse_owner_change_by_support,
)
from epd2_identity_service.api import (
    ENDPOINTS,
    assert_consequential_contract,
    assert_response_safe,
    endpoint,
)
from epd2_identity_service.assurance import ACTION_REQUIREMENTS, AuthenticationMethod
from epd2_identity_service.authentication import (
    NON_DISCLOSABLE_REASON_CODES,
    UNIFORM_PUBLIC_REASON_CODE,
    AuthenticationOutcome,
    AuthenticationOutcomeKind,
    RateLimitBucket,
    RiskAssessment,
    RiskSignal,
    RiskSignalCategory,
    assert_uniform_failure,
    failed_outcome,
    issue_challenge,
    public_reason_code,
)
from epd2_identity_service.bootstrap import (
    BootstrapProofMethod,
    assert_redirect_allowlisted,
    create_bootstrap_request,
    issue_bootstrap_response,
    redeem_bootstrap_response,
    verify_proof,
)
from epd2_identity_service.configuration import default_configuration
from epd2_identity_service.contacts import ContactChannelClass
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AccountRestrictedError,
    AssuranceInsufficientError,
    AuthenticationThrottledError,
    BootstrapExpiredError,
    BootstrapProofVerificationFailedError,
    BreakGlassJustificationMissingError,
    GlobalIdentifierRefusedError,
    MalformedAuthenticatorResponseError,
    PrivilegedApprovalMissingError,
    RateLimitExceededError,
    RecoveryContactRecentlyChangedError,
    RedirectUriNotAllowlistedError,
    SecretInPayloadRefusedError,
    SeparationOfDutiesViolatedError,
    SessionIdentifierInUrlError,
    SupportActionNotPermittedError,
    SystemAdminIdentityAccessRefusedError,
)
from epd2_identity_service.identifiers import MappingPurpose
from epd2_identity_service.observability import (
    MINIMUM_DISCLOSABLE_COUNT,
    REDACTED,
    MetricLabels,
    MetricName,
    MetricsRecorder,
    assert_no_secret_in_log_line,
    redact,
)
from epd2_identity_service.passkeys import AuthenticatorResponse
from epd2_identity_service.passwords import initial_throttle_state
from epd2_identity_service.recovery import StatedRecoveryReason, open_recovery
from epd2_identity_service.secret_storage import DeterministicSecureRandom
from epd2_identity_service.sessions import (
    refuse_session_identifier_in_url,
    session_cookie_for,
)
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

# --- API contract negatives -------------------------------------------------


def test_every_endpoint_in_the_catalogue_satisfies_its_own_contract() -> None:
    for spec in ENDPOINTS:
        assert_consequential_contract(spec)


def test_a_consequential_endpoint_cannot_waive_an_obligation() -> None:
    from dataclasses import replace

    spec = replace(endpoint("credentials.revoke"), idempotency_key_required=False)
    with pytest.raises(ValueError, match="may not waive"):
        assert_consequential_contract(spec)


def test_the_two_unauthenticated_consequential_endpoints_state_why() -> None:
    exempt = [spec for spec in ENDPOINTS if spec.unauthenticated_by_design]
    assert {spec.operation for spec in exempt} == {
        "account.create",
        "voting_handoff.redeem",
    }
    for spec in exempt:
        assert len(spec.justification) > 40


def test_there_is_no_universal_identity_console_in_the_catalogue() -> None:
    operations = {spec.operation for spec in ENDPOINTS}
    for forbidden in ("account.list_all", "identity.export", "account.impersonate"):
        assert forbidden not in operations


def test_an_api_response_cannot_carry_a_secret_or_a_global_identifier() -> None:
    with pytest.raises(SecretInPayloadRefusedError):
        assert_response_safe({"refresh_token": "x"})
    with pytest.raises(GlobalIdentifierRefusedError):
        assert_response_safe({"member_number": "1234"})


def test_a_stale_resource_version_is_refused() -> None:
    from epd2_identity_service.accounts import activate_account_record, create_account_record
    from epd2_identity_service.exceptions import ResourceVersionStaleError

    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    with pytest.raises(ResourceVersionStaleError):
        activate_account_record(record, expected_version=99, activated_at=NOW)


def test_a_restricted_account_cannot_act() -> None:
    svc = service()
    account = account_id()
    svc.create_account(account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4())
    contact = svc.add_contact(
        contact_id=uuid4(),
        account_id=account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="a@b.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    svc.verify_contact(contact_id=contact.contact_id, correlation_id=uuid4(), event_id=uuid4())
    svc.activate_account(
        account_id=account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
    )
    from epd2_identity_service.accounts import AccountRestrictionClass

    svc.apply_restriction(
        restriction=restriction(account, restriction_class=AccountRestrictionClass.ABUSE_REVIEW),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    with pytest.raises(AccountRestrictedError):
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


def test_insufficient_assurance_and_a_missing_step_up_are_distinct_refusals() -> None:
    from epd2_identity_service.exceptions import StepUpRequiredError
    from epd2_identity_service.stepup import redeem_step_up

    with pytest.raises(AssuranceInsufficientError):
        from epd2_identity_service.assurance import evaluate_requirement

        evaluate_requirement(
            assurance=assurance(AuthenticationMethod.MAGIC_LINK),
            identity_assurance=None,
            requirement=ACTION_REQUIREMENTS["remove_passkey"],
            configuration=default_configuration(),
            now=NOW,
        )
    actor = reference(account_id())
    with pytest.raises(StepUpRequiredError):
        redeem_step_up(
            None,
            binding=step_up_binding(actor=actor, session_id=uuid4()),
            now=NOW,
        )


def test_malformed_webauthn_data_is_refused_before_verification() -> None:
    with pytest.raises(MalformedAuthenticatorResponseError):
        AuthenticatorResponse(
            credential_reference="",
            client_data_challenge="c",
            origin="https://app.epd.example",
            signature="s",
            sign_counter=1,
            backup_eligible=False,
            backup_state=False,
            device_bound=True,
            attestation_presented=False,
            authenticator_class="platform",
        )
    with pytest.raises(MalformedAuthenticatorResponseError):
        AuthenticatorResponse(
            credential_reference="c",
            client_data_challenge="c",
            origin="https://app.epd.example",
            signature="s",
            sign_counter=-1,
            backup_eligible=False,
            backup_state=False,
            device_bound=True,
            attestation_presented=False,
            authenticator_class="platform",
        )


def test_a_recently_changed_contact_cannot_carry_a_recovery() -> None:
    with pytest.raises(RecoveryContactRecentlyChangedError):
        open_recovery(
            recovery_id=uuid4(),
            account_id=account_id(),
            requester_reference=reference(account_id(), purpose=MappingPurpose.RECOVERY),
            stated_reason=StatedRecoveryReason.DEVICE_LOST,
            entry_channel_class="email",
            entry_channel_changed_at=NOW - timedelta(days=1),
            requested_at=NOW,
            contact_protective_window=timedelta(days=7),
        )


# --- account enumeration ----------------------------------------------------


def test_no_public_response_discloses_account_state() -> None:
    for internal in sorted(NON_DISCLOSABLE_REASON_CODES):
        assert public_reason_code(internal) == UNIFORM_PUBLIC_REASON_CODE
        outcome = failed_outcome(internal_reason_code=internal, method=None, occurred_at=NOW)
        assert_uniform_failure(outcome)
        assert outcome.public_reason_code == UNIFORM_PUBLIC_REASON_CODE


def test_an_outcome_cannot_be_constructed_with_a_disclosing_public_code() -> None:
    with pytest.raises(ValueError, match="may never be returned"):
        AuthenticationOutcome(
            kind=AuthenticationOutcomeKind.FAILED,
            internal_reason_code="ACCOUNT_LOCKED",
            public_reason_code="ACCOUNT_LOCKED",
            method=None,
            occurred_at=NOW,
        )


def test_a_challenge_is_issued_for_an_unknown_account_too() -> None:
    """The enumeration control: the shape does not vary."""
    known = issue_challenge(
        challenge_id=uuid4(),
        account_reference=reference(account_id()),
        workspace=WorkspaceId.MEMBER_APPLICATION,
        method=AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        issued_at=NOW,
        lifetime=timedelta(minutes=5),
        random=DeterministicSecureRandom(),
    )
    unknown = issue_challenge(
        challenge_id=uuid4(),
        account_reference=None,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        method=AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        issued_at=NOW,
        lifetime=timedelta(minutes=5),
        random=DeterministicSecureRandom(),
    )
    assert set(known.__dataclass_fields__) == set(unknown.__dataclass_fields__)
    assert len(known.nonce) == len(unknown.nonce)


# --- CSRF, cookies, redirects and session identifiers -----------------------


def test_session_cookies_are_always_secure_httponly_and_host_scoped() -> None:
    cookie = session_cookie_for(WorkspaceId.MEMBER_APPLICATION)
    assert cookie.secure and cookie.http_only
    assert cookie.same_site in ("Strict", "Lax")
    assert not cookie.host.startswith(".")


def test_no_parent_domain_cookie_can_be_constructed() -> None:
    from epd2_identity_service.sessions import SessionCookieAttributes

    with pytest.raises(ValueError, match="parent-domain"):
        SessionCookieAttributes(name="epd2_session", host=".epd.example")


def test_a_state_changing_request_without_a_csrf_token_is_refused() -> None:
    from epd2_identity_service.exceptions import SessionRevokedError
    from epd2_identity_service.sessions import SessionScope, issue_session

    session, _refresh, csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=SessionScope(
            workspace=WorkspaceId.MEMBER_APPLICATION,
            origin=workspace_origin(WorkspaceId.MEMBER_APPLICATION),
            capabilities=frozenset(),
        ),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    session.assert_csrf(csrf)
    with pytest.raises(SessionRevokedError):
        session.assert_csrf("not-the-token")


def test_no_session_identifier_may_appear_in_a_url() -> None:
    refuse_session_identifier_in_url("https://app.epd.example/dashboard")
    for bad in (
        "https://app.epd.example/x?session_id=abc",
        "https://app.epd.example/x?refresh_token=abc",
        "https://app.epd.example/x?SID=abc",
    ):
        with pytest.raises(SessionIdentifierInUrlError):
            refuse_session_identifier_in_url(bad)


def test_the_redirect_allowlist_is_exact_match() -> None:
    allowed = "https://app.epd.example/auth/callback"
    assert_redirect_allowlisted(allowed, frozenset({allowed}))
    for evil in (
        "https://app.epd.example/auth/callback/../../evil",
        "https://app.epd.example.evil.test/auth/callback",
        "https://app.epd.example/auth/callback?next=https://evil.test",
    ):
        with pytest.raises(RedirectUriNotAllowlistedError):
            assert_redirect_allowlisted(evil, frozenset({allowed}))


def test_the_plain_proof_method_is_refused() -> None:
    redirect = f"{workspace_origin(WorkspaceId.MEMBER_APPLICATION)}/cb"
    with pytest.raises(BootstrapProofVerificationFailedError):
        create_bootstrap_request(
            request_id=uuid4(),
            workspace=WorkspaceId.MEMBER_APPLICATION,
            redirect_uri=redirect,
            redirect_allowlist=frozenset({redirect}),
            proof_challenge="c",
            proof_method=BootstrapProofMethod.PLAIN,
            created_at=NOW,
            configuration=default_configuration(),
            random=DeterministicSecureRandom(),
        )


def test_a_bad_proof_and_an_expired_request_are_distinct_refusals() -> None:
    redirect = f"{workspace_origin(WorkspaceId.MEMBER_APPLICATION)}/cb"
    request = create_bootstrap_request(
        request_id=uuid4(),
        workspace=WorkspaceId.MEMBER_APPLICATION,
        redirect_uri=redirect,
        redirect_allowlist=frozenset({redirect}),
        proof_challenge="the-digest",
        proof_method=BootstrapProofMethod.S256,
        created_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    verify_proof(request, proof_verifier="v", digest_of_verifier="the-digest")
    with pytest.raises(BootstrapProofVerificationFailedError):
        verify_proof(request, proof_verifier="v", digest_of_verifier="wrong")
    with pytest.raises(BootstrapExpiredError):
        issue_bootstrap_response(
            request,
            response_id=uuid4(),
            actor_reference=reference(account_id(), purpose=MappingPurpose.SESSION),
            achieved_assurance=AuthenticationAssuranceLevel.HIGH,
            issued_at=NOW + timedelta(minutes=10),
            lifetime=timedelta(minutes=2),
            random=DeterministicSecureRandom(),
        )


def test_an_expired_bootstrap_response_cannot_be_redeemed() -> None:
    redirect = f"{workspace_origin(WorkspaceId.MEMBER_APPLICATION)}/cb"
    request = create_bootstrap_request(
        request_id=uuid4(),
        workspace=WorkspaceId.MEMBER_APPLICATION,
        redirect_uri=redirect,
        redirect_allowlist=frozenset({redirect}),
        proof_challenge="d",
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
        random=DeterministicSecureRandom(seed="r"),
    )
    with pytest.raises(BootstrapExpiredError):
        redeem_bootstrap_response(
            response,
            presented_value=value,
            presenting_workspace=request.workspace,
            presenting_origin=request.audience_origin,
            presented_nonce=request.nonce,
            redemption_id=uuid4(),
            now=NOW + timedelta(minutes=5),
        )


# --- rate limiting and throttling -------------------------------------------


def test_a_rate_limit_bucket_refuses_past_its_limit_and_resets_per_window() -> None:
    bucket = RateLimitBucket(
        key="authentication:account",
        window_started_at=NOW,
        count=0,
        limit=2,
        window=timedelta(minutes=1),
    )
    bucket = bucket.hit(now=NOW)
    bucket = bucket.hit(now=NOW)
    with pytest.raises(RateLimitExceededError):
        bucket.hit(now=NOW)
    reset = bucket.hit(now=NOW + timedelta(minutes=2))
    assert reset.count == 1


def test_repeated_failures_throttle_the_attempt_source() -> None:
    state = initial_throttle_state()
    for _ in range(5):
        state = state.after_failure(now=NOW, threshold=5, penalty=timedelta(minutes=15))
    with pytest.raises(AuthenticationThrottledError):
        state.assert_not_throttled(NOW + timedelta(minutes=1))
    state.assert_not_throttled(NOW + timedelta(minutes=20))


def test_impossible_travel_alone_never_reaches_a_denying_classification() -> None:
    assessment = RiskAssessment.classify(
        (
            RiskSignal(
                category=RiskSignalCategory.IMPOSSIBLE_TRAVEL,
                observed_at=NOW,
                explanation="two logins 4000 km apart within an hour",
            ),
        )
    )
    assert assessment.state.value == "normal"
    assert assessment.named_signals() == ("impossible_travel",)


# --- log redaction and metric disclosure ------------------------------------


def test_redaction_replaces_every_prohibited_value_including_nested_ones() -> None:
    redacted = redact(
        {
            "password": "hunter2",
            "outer": {"recovery_code": "abc", "keep": 1},
            "items": [{"email": "a@b.example"}],
            "safe": "value",
        }
    )
    assert redacted["password"] == REDACTED
    assert redacted["outer"]["recovery_code"] == REDACTED  # type: ignore[index]
    assert redacted["items"][0]["email"] == REDACTED  # type: ignore[index]
    assert redacted["safe"] == "value"
    assert "hunter2" not in str(redacted)


def test_a_secret_reaching_a_log_line_is_refused() -> None:
    assert_no_secret_in_log_line("session issued for workspace WS-02", known_secrets=("hunter2",))
    with pytest.raises(SecretInPayloadRefusedError):
        assert_no_secret_in_log_line("token=hunter2", known_secrets=("hunter2",))


def test_metric_labels_admit_no_per_person_dimension() -> None:
    with pytest.raises(ValueError, match="metric labels admit only"):
        MetricLabels(values={"account_id": "x"})
    MetricLabels(values={"workspace": "WS-02", "outcome": "succeeded"})


def test_a_rare_metric_series_is_suppressed_below_the_disclosure_floor() -> None:
    recorder = MetricsRecorder()
    labels = MetricLabels(values={"reason_code": "SESSION_REPLAY_DETECTED"})
    recorder.record(MetricName.SESSION_REPLAY_DETECTED, labels)
    assert recorder.disclosable() == {}
    for _ in range(MINIMUM_DISCLOSABLE_COUNT - 1):
        recorder.record(MetricName.SESSION_REPLAY_DETECTED, labels)
    assert recorder.disclosable()


# --- privilege escalation and recovery takeover -----------------------------


def _grant(role: IdentityAdminRole, purpose: str) -> PrivilegedGrantRef:
    return PrivilegedGrantRef(
        grant_reference="grant/1",
        role=role,
        purpose=purpose,
        granted_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def test_a_support_agent_cannot_approve_a_recovery_or_revoke_a_credential() -> None:
    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    for action in (AdminAction.APPROVE_RECOVERY, AdminAction.REVOKE_CREDENTIAL):
        with pytest.raises(SupportActionNotPermittedError):
            authorize_privileged_action(
                role=IdentityAdminRole.SUPPORT_AGENT,
                action=action,
                grant=_grant(IdentityAdminRole.SUPPORT_AGENT, action.value),
                actor_reference=actor,
                case_initiator_reference=None,
                case_subject_reference=None,
                now=NOW,
                audit_available=True,
            )


def test_a_support_agent_cannot_change_an_account_owner() -> None:
    with pytest.raises(SupportActionNotPermittedError):
        refuse_owner_change_by_support(IdentityAdminRole.SUPPORT_AGENT)


def test_a_system_admin_has_no_automatic_identity_content_access() -> None:
    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    with pytest.raises(SystemAdminIdentityAccessRefusedError):
        authorize_privileged_action(
            role=IdentityAdminRole.SYSTEM_ADMIN,
            action=AdminAction.READ_IDENTITY_CONTENT,
            grant=_grant(IdentityAdminRole.SYSTEM_ADMIN, "read_identity_content"),
            actor_reference=actor,
            case_initiator_reference=None,
            case_subject_reference=None,
            now=NOW,
            audit_available=True,
        )


def test_a_missing_or_expired_grant_is_refused() -> None:
    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    with pytest.raises(PrivilegedApprovalMissingError):
        authorize_privileged_action(
            role=IdentityAdminRole.RECOVERY_REVIEWER,
            action=AdminAction.APPROVE_RECOVERY,
            grant=None,
            actor_reference=actor,
            case_initiator_reference=None,
            case_subject_reference=None,
            now=NOW,
            audit_available=True,
        )
    with pytest.raises(PrivilegedApprovalMissingError):
        authorize_privileged_action(
            role=IdentityAdminRole.RECOVERY_REVIEWER,
            action=AdminAction.APPROVE_RECOVERY,
            grant=_grant(IdentityAdminRole.RECOVERY_REVIEWER, "approve_recovery"),
            actor_reference=actor,
            case_initiator_reference=None,
            case_subject_reference=None,
            now=NOW + timedelta(hours=2),
            audit_available=True,
        )


def test_a_reviewer_cannot_act_on_their_own_case() -> None:
    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    with pytest.raises(SeparationOfDutiesViolatedError):
        authorize_privileged_action(
            role=IdentityAdminRole.RECOVERY_REVIEWER,
            action=AdminAction.APPROVE_RECOVERY,
            grant=_grant(IdentityAdminRole.RECOVERY_REVIEWER, "approve_recovery"),
            actor_reference=actor,
            case_initiator_reference=actor,
            case_subject_reference=None,
            now=NOW,
            audit_available=True,
        )


def test_break_glass_needs_a_justification_and_a_second_actor() -> None:
    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    with pytest.raises(BreakGlassJustificationMissingError):
        BreakGlassInvocation(
            justification="",
            second_actor_reference=actor,
            invoked_at=NOW,
            reason_code="BREAK_GLASS_JUSTIFICATION_MISSING",
        )
    with pytest.raises(BreakGlassJustificationMissingError):
        authorize_privileged_action(
            role=IdentityAdminRole.SECURITY_ADMIN,
            action=AdminAction.BREAK_GLASS,
            grant=_grant(IdentityAdminRole.SECURITY_ADMIN, "break_glass"),
            actor_reference=actor,
            case_initiator_reference=None,
            case_subject_reference=None,
            now=NOW,
            audit_available=True,
            break_glass=None,
        )


def test_no_privileged_act_proceeds_while_audit_is_unavailable() -> None:
    from epd2_identity_service.exceptions import AuditUnavailableError

    actor = reference(account_id(), purpose=MappingPurpose.PRIVILEGED_REVIEW)
    with pytest.raises(AuditUnavailableError):
        authorize_privileged_action(
            role=IdentityAdminRole.SECURITY_ADMIN,
            action=AdminAction.APPLY_RESTRICTION,
            grant=_grant(IdentityAdminRole.SECURITY_ADMIN, "apply_restriction"),
            actor_reference=actor,
            case_initiator_reference=None,
            case_subject_reference=None,
            now=NOW,
            audit_available=False,
        )


# =============================================================================
# The breached-password boundary fails closed
#
# The correction round replaced a permissive default that reported
# nothing as breached. These tests are the proof that the replacement
# holds, and they are written against the boundary rather than against
# the class, so a future permissive default fails them too.
# =============================================================================


class _FixtureHasher:
    """Not a hash. It exists so these tests exercise the breach branch
    without depending on a memory-hard algorithm that is deliberately
    unbound in this repository."""

    algorithm_label = "fixture-not-a-hash"

    def hash(self, password: str) -> str:
        return f"fixture:{password}"

    def verify(self, password: str, stored_hash: str) -> bool:
        return stored_hash == f"fixture:{password}"

    def needs_rehash(self, stored_hash: str) -> bool:
        return True


def test_an_unbound_breach_checker_refuses_password_enrollment() -> None:
    """The default binding must refuse, and it must refuse with a
    registered code. A silent `False` here is the failure mode the whole
    correction exists to remove."""
    from epd2_identity_service.exceptions import BreachCheckUnavailableError
    from epd2_identity_service.passwords import enroll_password
    from epd2_identity_service.secret_storage import UnboundBreachedPasswordChecker

    with pytest.raises(BreachCheckUnavailableError) as refusal:
        enroll_password(
            credential_id=uuid4(),
            account_id=account_id(),
            password="ein-sehr-langes-passwort",
            created_at=NOW,
            hasher=_FixtureHasher(),
            breach_checker=UnboundBreachedPasswordChecker(),
            account_has_other_credential=True,
        )
    assert refusal.value.reason_code == BreachCheckUnavailableError.reason_code


def test_the_unbound_checker_never_returns_a_boolean() -> None:
    """Both booleans would be lies: `False` claims a check that did not
    happen, `True` refuses every password for the wrong reason."""
    from epd2_identity_service.exceptions import BreachCheckUnavailableError
    from epd2_identity_service.secret_storage import (
        UnboundBreachedPasswordChecker,
        assert_breach_check_available,
    )

    checker = UnboundBreachedPasswordChecker()
    for candidate in ("", "a", "ein-sehr-langes-passwort", "correct horse battery staple"):
        with pytest.raises(BreachCheckUnavailableError):
            checker.is_breached(candidate)
        with pytest.raises(BreachCheckUnavailableError):
            assert_breach_check_available(checker, candidate)


def test_no_permissive_breached_password_checker_remains_in_the_package() -> None:
    """The removed class is named here on purpose: reintroducing a
    checker that answers `False` without checking anything must fail a
    test rather than pass review."""
    import epd2_identity_service.secret_storage as secret_storage

    assert not hasattr(secret_storage, "NoBreachedPasswordChecker")
    source = Path(secret_storage.__file__).read_text(encoding="utf-8")
    assert "class NoBreachedPasswordChecker" not in source


def test_a_deterministic_checker_is_declared_as_a_test_double() -> None:
    """It may exist - both enrollment branches need testing - but it must
    say what it is, and it must not be what an unconfigured deployment
    gets."""
    from epd2_identity_service.secret_storage import (
        DeterministicBreachedPasswordChecker,
    )

    docstring = DeterministicBreachedPasswordChecker.__doc__ or ""
    assert "test double" in docstring.lower()
    checker = DeterministicBreachedPasswordChecker(frozenset({"ein-sehr-langes-passwort"}))
    assert checker.is_breached("ein-sehr-langes-passwort") is True
    assert checker.is_breached("ein-anderes-langes-passwort") is False


def test_a_known_breached_password_is_refused_when_a_checker_is_bound() -> None:
    from epd2_identity_service.exceptions import BreachedPasswordRefusedError
    from epd2_identity_service.passwords import enroll_password
    from epd2_identity_service.secret_storage import DeterministicBreachedPasswordChecker

    with pytest.raises(BreachedPasswordRefusedError):
        enroll_password(
            credential_id=uuid4(),
            account_id=account_id(),
            password="ein-sehr-langes-passwort",
            created_at=NOW,
            hasher=_FixtureHasher(),
            breach_checker=DeterministicBreachedPasswordChecker(
                frozenset({"ein-sehr-langes-passwort"})
            ),
            account_has_other_credential=True,
        )


def test_the_degraded_mode_decision_cannot_permit_enrollment() -> None:
    """The governed exception is authentication-only *by construction*:
    there is no field on it that a caller could set to re-open
    enrollment."""
    from dataclasses import fields

    from epd2_identity_service.secret_storage import PasswordDegradedModeDecision

    names = {field.name for field in fields(PasswordDegradedModeDecision)}
    assert names == {
        "authority_reference",
        "reason_code",
        "decided_at",
        "allows_authentication",
    }
    assert not {name for name in names if "enroll" in name or "replace" in name or "change" in name}


def test_a_degraded_mode_decision_requires_an_authority_and_a_reason_code() -> None:
    from epd2_identity_service.exceptions import BreachCheckUnavailableError
    from epd2_identity_service.secret_storage import PasswordDegradedModeDecision

    for authority, code in (("", "PASSWORD_BREACH_CHECK_DEGRADED"), ("board-2026-07", "")):
        with pytest.raises(BreachCheckUnavailableError):
            PasswordDegradedModeDecision(
                authority_reference=authority,
                reason_code=code,
                decided_at=NOW,
                allows_authentication=True,
            )
    permitted = PasswordDegradedModeDecision(
        authority_reference="board-2026-07",
        reason_code="PASSWORD_BREACH_CHECK_DEGRADED",
        decided_at=NOW,
        allows_authentication=True,
    )
    assert permitted.allows_authentication is True
