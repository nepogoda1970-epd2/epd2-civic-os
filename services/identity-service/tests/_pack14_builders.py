"""Shared fixtures for the PACK-14 test suite.

Every builder produces a *valid* object, so a test that wants an invalid
one has to say which field it is breaking. That keeps the negative tests
honest: they fail for the reason they name rather than for an unrelated
missing argument.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_identity_service.account_security_application import AccountSecurityService
from epd2_identity_service.account_security_storage import (
    InMemoryAccountContactStore,
    InMemoryAccountLinkStore,
    InMemoryAccountRegistryStore,
    InMemoryAuthenticationStore,
    InMemoryBootstrapStore,
    InMemoryCredentialStore,
    InMemoryIdentityMappingStore,
    InMemoryIdentityProofingStore,
    InMemoryRecoveryStore,
    InMemoryReplayPreventionStore,
    InMemorySessionStore,
    InMemoryVotingHandoffStore,
)
from epd2_identity_service.accounts import (
    AccountLock,
    AccountLockCause,
    AccountRestriction,
    AccountRestrictionClass,
)
from epd2_identity_service.assurance import (
    AssuranceEvidence,
    AuthenticationAssurance,
    AuthenticationMethod,
    RiskState,
    evaluate_assurance,
)
from epd2_identity_service.credentials import (
    AttestationState,
    CredentialBinding,
    CredentialMetadata,
)
from epd2_identity_service.identifiers import (
    AccountId,
    CredentialId,
    IdentifierSpace,
    MappingPurpose,
    OrganizationLevel,
    OrganizationScope,
    ScopedIdentityReference,
    SessionId,
    derive_scoped_reference,
)
from epd2_identity_service.passkeys import (
    CEREMONY_AUTHENTICATION,
    CEREMONY_REGISTRATION,
    AuthenticatorResponse,
    DeterministicWebAuthnVerifier,
    WebAuthnChallenge,
)
from epd2_identity_service.secret_storage import DeterministicSecureRandom
from epd2_identity_service.sessions import DeviceReference
from epd2_identity_service.stepup import StepUpBinding
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
SALT = b"\x11" * 32
UNIT_ID = UUID("11111111-1111-4111-8111-111111111111")


def scope() -> OrganizationScope:
    return OrganizationScope(level=OrganizationLevel.LAND, organizational_unit_id=UNIT_ID)


def account_id(value: str = "22222222-2222-4222-8222-222222222222") -> AccountId:
    return AccountId(UUID(value))


def new_credential_id() -> CredentialId:
    """A fresh `CredentialId`. Tests use this rather than a bare `uuid4()`
    so the distinct-type discipline `identifiers.py` establishes holds in
    the suite too - mypy would otherwise never see it exercised."""
    return CredentialId(uuid4())


def new_session_id() -> SessionId:
    """A fresh `SessionId`, for the same reason."""
    return SessionId(uuid4())


def reference(
    account: AccountId,
    *,
    purpose: MappingPurpose = MappingPurpose.ACCOUNT_SECURITY,
    domain_owner: str = "identity-service",
) -> ScopedIdentityReference:
    return derive_scoped_reference(
        space=IdentifierSpace.ACCOUNT,
        value=str(account),
        purpose=purpose,
        scope=scope(),
        domain_owner=domain_owner,
        derivation_salt=SALT,
    )


def assurance(
    level: AuthenticationMethod = AuthenticationMethod.PASSKEY_DEVICE_BOUND,
    *,
    at: datetime = NOW,
    binding: CredentialBinding = CredentialBinding.DEVICE_BOUND,
    risk: RiskState = RiskState.NORMAL,
    signals: tuple[str, ...] = (),
) -> AuthenticationAssurance:
    return evaluate_assurance(
        evidence=AssuranceEvidence(
            methods=(level,),
            credential_binding=binding,
            risk_state=risk,
            named_signals=signals,
        ),
        authenticated_at=at,
    )


def device() -> DeviceReference:
    return DeviceReference(device_label="Laptop zu Hause", device_digest="ab" * 32)


def credential_metadata(
    *,
    nickname: str = "Diensthandy",
    binding: CredentialBinding = CredentialBinding.DEVICE_BOUND,
) -> CredentialMetadata:
    return CredentialMetadata(
        nickname=nickname,
        binding=binding,
        attestation=AttestationState.NOT_REQUESTED,
        backup_eligible=binding is CredentialBinding.SYNCED,
        backup_state=False,
        authenticator_class="platform",
        sign_counter=1,
    )


def step_up_binding(
    *,
    actor: ScopedIdentityReference,
    session_id: UUID,
    action_code: str = "voting_handoff",
    resource_id: UUID | None = None,
    resource_version: int = 1,
) -> StepUpBinding:
    return StepUpBinding(
        actor_reference=actor,
        session_id=SessionId(session_id),
        action_code=action_code,
        resource_type="voting_context",
        resource_id=resource_id or UUID("33333333-3333-4333-8333-333333333333"),
        resource_version=resource_version,
    )


def webauthn_challenge(
    *,
    account: AccountId,
    ceremony: str = CEREMONY_REGISTRATION,
    workspace: WorkspaceId = WorkspaceId.MEMBER_APPLICATION,
    issued_at: datetime = NOW,
    challenge: str = "challenge-value",
) -> WebAuthnChallenge:
    return WebAuthnChallenge(
        challenge_id=uuid4(),
        challenge=challenge,
        ceremony=ceremony,
        account_id=account,
        relying_party_origin=workspace_origin(workspace),
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=5),
    )


def authenticator_response(
    *,
    challenge: WebAuthnChallenge,
    credential_reference: str = "cred-1",
    signature: str | None = None,
    device_bound: bool = True,
    backup_eligible: bool = False,
    sign_counter: int | None = 1,
    origin: str | None = None,
) -> AuthenticatorResponse:
    return AuthenticatorResponse(
        credential_reference=credential_reference,
        client_data_challenge=challenge.challenge,
        origin=origin or challenge.relying_party_origin,
        signature=signature or f"{challenge.challenge}:{credential_reference}",
        sign_counter=sign_counter,
        backup_eligible=backup_eligible,
        backup_state=False,
        device_bound=device_bound,
        attestation_presented=False,
        authenticator_class="platform",
    )


def assertion_response(
    *,
    challenge: WebAuthnChallenge,
    public_key: str,
    credential_reference: str = "cred-1",
    sign_counter: int | None = 2,
) -> AuthenticatorResponse:
    return AuthenticatorResponse(
        credential_reference=credential_reference,
        client_data_challenge=challenge.challenge,
        origin=challenge.relying_party_origin,
        signature=f"{challenge.challenge}:{public_key}",
        sign_counter=sign_counter,
        backup_eligible=False,
        backup_state=False,
        device_bound=True,
        attestation_presented=False,
        authenticator_class="platform",
    )


def authentication_challenge_for(account: AccountId) -> WebAuthnChallenge:
    return webauthn_challenge(account=account, ceremony=CEREMONY_AUTHENTICATION)


def lock(account: AccountId, *, at: datetime = NOW) -> AccountLock:
    return AccountLock(
        lock_id=uuid4(),
        account_id=account,
        cause=AccountLockCause.REPEATED_AUTHENTICATION_FAILURE,
        reason_code="ACCOUNT_LOCKED",
        locked_at=at,
        expires_at=at + timedelta(minutes=15),
        unlock_condition="expiry or an administrative release",
    )


def restriction(
    account: AccountId,
    *,
    at: datetime = NOW,
    restriction_class: AccountRestrictionClass = AccountRestrictionClass.SECURITY_QUARANTINE,
) -> AccountRestriction:
    return AccountRestriction(
        restriction_id=uuid4(),
        account_id=account,
        restriction_class=restriction_class,
        authority_reference="security-admin/2026-07",
        reason_code="ACCOUNT_QUARANTINED",
        scope=scope(),
        applied_at=at,
        review_due_at=at + timedelta(days=14),
    )


def service(*, now: datetime = NOW) -> AccountSecurityService:
    """A fully wired service with in-memory adapters and deterministic
    randomness.

    The WebAuthn verifier is the **deterministic test provider**, named
    as such: no production path acquires a test branch, and every test
    that exercises a ceremony is exercising the state machine rather than
    a fake verifier pretending to be a real one.
    """
    return AccountSecurityService(
        account_store=InMemoryAccountRegistryStore(),
        contact_store=InMemoryAccountContactStore(),
        credential_store=InMemoryCredentialStore(),
        authentication_store=InMemoryAuthenticationStore(),
        session_store=InMemorySessionStore(),
        recovery_store=InMemoryRecoveryStore(),
        proofing_store=InMemoryIdentityProofingStore(),
        bootstrap_store=InMemoryBootstrapStore(),
        voting_handoff_store=InMemoryVotingHandoffStore(),
        mapping_store=InMemoryIdentityMappingStore(),
        replay_store=InMemoryReplayPreventionStore(),
        audit_store=InMemoryAuditEventStore(),
        clock=FixedClock(now),
        derivation_salt=SALT,
        random=DeterministicSecureRandom(),
        webauthn_verifier=DeterministicWebAuthnVerifier(),
    )


def link_store() -> InMemoryAccountLinkStore:
    return InMemoryAccountLinkStore()
