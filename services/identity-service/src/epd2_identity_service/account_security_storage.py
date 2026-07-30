"""Storage ports and in-memory reference adapters, **one set per module
boundary**.

Specification §4.1 binding rule 2: the six contexts are internally
separated modules with separate storage boundaries, and a module reaches
another module's store through that module's own interface, never
directly. This file is where that separation is expressed - six store
groups, no shared table object, and no cross-module query.

Two operations are deliberately absent from every port here:

- **There is no `delete`.** Disposition goes through
  `persistence.assert_disposition_permitted`, which refuses while a legal
  hold or an open dispute exists and while `OD-P14-07` leaves the
  schedule unconfirmed. A `delete` on a port is a way around that.
- **There is no unrestricted `list_all`.** `IdentityMappingStore.resolve`
  takes a purpose and a scope and returns one mapping; anything shaped
  like "give me every mapping" raises through
  `mappings.refuse_unrestricted_lookup`.

Every adapter below is in memory. **No production database is deployed by
this round**, and none of these is a production adapter.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_identity_service.accounts import (
    AccountClosureRequest,
    AccountLock,
    AccountRegistryRecord,
    AccountRestriction,
)
from epd2_identity_service.authentication import AuthenticationAttempt, AuthenticationChallenge
from epd2_identity_service.bootstrap import (
    AuthenticationBootstrapRequest,
    AuthenticationBootstrapResponse,
    BootstrapRedemption,
)
from epd2_identity_service.contacts import AccountContact
from epd2_identity_service.credentials import Credential
from epd2_identity_service.identifiers import (
    AccountId,
    CredentialId,
    MappingPurpose,
    OrganizationScope,
    ScopedIdentityReference,
    SessionId,
)
from epd2_identity_service.linking import AccountLinkRequest
from epd2_identity_service.mappings import (
    IdentityMapping,
    MappingResolutionRequest,
    refuse_unrestricted_lookup,
)
from epd2_identity_service.mfa import MfaFactor, RecoveryCodeSet
from epd2_identity_service.passkeys import PasskeyCredentialRecord, WebAuthnChallenge
from epd2_identity_service.persistence import IdempotencyRecord, ReplayNonceRecord
from epd2_identity_service.proofing import IdentityProofingCase
from epd2_identity_service.recovery import RecoveryRequest
from epd2_identity_service.sessions import SessionRecord
from epd2_identity_service.stepup import StepUpChallenge, StepUpResult
from epd2_identity_service.voting_handoff import (
    VotingHandoffIssuance,
    VotingHandoffRedemptionReference,
)

# --- Account Registry -------------------------------------------------------


class AccountRegistryStore(Protocol):
    def save(self, record: AccountRegistryRecord) -> None: ...

    def get(self, account_id: AccountId) -> AccountRegistryRecord | None: ...

    def save_lock(self, lock: AccountLock) -> None: ...

    def locks_for(self, account_id: AccountId) -> tuple[AccountLock, ...]: ...

    def save_restriction(self, restriction: AccountRestriction) -> None: ...

    def restrictions_for(self, account_id: AccountId) -> tuple[AccountRestriction, ...]: ...

    def save_closure_request(self, request: AccountClosureRequest) -> None: ...

    def open_closure_request(self, account_id: AccountId) -> AccountClosureRequest | None: ...


class InMemoryAccountRegistryStore:
    def __init__(self) -> None:
        self._records: dict[AccountId, AccountRegistryRecord] = {}
        self._locks: dict[UUID, AccountLock] = {}
        self._restrictions: dict[UUID, AccountRestriction] = {}
        self._closures: dict[UUID, AccountClosureRequest] = {}

    def save(self, record: AccountRegistryRecord) -> None:
        self._records[record.account_id] = record

    def get(self, account_id: AccountId) -> AccountRegistryRecord | None:
        return self._records.get(account_id)

    def save_lock(self, lock: AccountLock) -> None:
        self._locks[lock.lock_id] = lock

    def locks_for(self, account_id: AccountId) -> tuple[AccountLock, ...]:
        return tuple(lock for lock in self._locks.values() if lock.account_id == account_id)

    def save_restriction(self, restriction: AccountRestriction) -> None:
        self._restrictions[restriction.restriction_id] = restriction

    def restrictions_for(self, account_id: AccountId) -> tuple[AccountRestriction, ...]:
        return tuple(
            restriction
            for restriction in self._restrictions.values()
            if restriction.account_id == account_id
        )

    def save_closure_request(self, request: AccountClosureRequest) -> None:
        self._closures[request.closure_request_id] = request

    def open_closure_request(self, account_id: AccountId) -> AccountClosureRequest | None:
        for request in self._closures.values():
            if request.account_id == account_id and request.is_open():
                return request
        return None


# --- Contacts ---------------------------------------------------------------


class AccountContactStore(Protocol):
    def save(self, contact: AccountContact) -> None: ...

    def get(self, contact_id: UUID) -> AccountContact | None: ...

    def for_account(self, account_id: AccountId) -> tuple[AccountContact, ...]: ...

    def within_scope(self, contact: AccountContact) -> tuple[AccountContact, ...]: ...


class InMemoryAccountContactStore:
    def __init__(self) -> None:
        self._contacts: dict[UUID, AccountContact] = {}

    def save(self, contact: AccountContact) -> None:
        self._contacts[contact.contact_id] = contact

    def get(self, contact_id: UUID) -> AccountContact | None:
        return self._contacts.get(contact_id)

    def for_account(self, account_id: AccountId) -> tuple[AccountContact, ...]:
        return tuple(
            contact for contact in self._contacts.values() if contact.account_id == account_id
        )

    def within_scope(self, contact: AccountContact) -> tuple[AccountContact, ...]:
        """Scoped, never global.

        Returns only contacts in the candidate's own uniqueness scope, so
        the uniqueness check cannot become a cross-scope lookup by
        accident - which would make the address the join key
        `FIR-INV-013` forbids.
        """
        return tuple(
            other
            for other in self._contacts.values()
            if other.uniqueness_scope.matches(contact.uniqueness_scope)
        )


# --- Credential registry ----------------------------------------------------


class CredentialStore(Protocol):
    def save(self, credential: Credential) -> None: ...

    def get(self, credential_id: CredentialId) -> Credential | None: ...

    def for_account(self, account_id: AccountId) -> tuple[Credential, ...]: ...

    def save_passkey(self, record: PasskeyCredentialRecord) -> None: ...

    def passkey_by_reference(self, credential_reference: str) -> PasskeyCredentialRecord | None: ...

    def save_factor(self, factor: MfaFactor) -> None: ...

    def factors_for(self, account_id: AccountId) -> tuple[MfaFactor, ...]: ...

    def save_recovery_codes(self, code_set: RecoveryCodeSet) -> None: ...

    def active_recovery_codes(self, account_id: AccountId) -> RecoveryCodeSet | None: ...


class InMemoryCredentialStore:
    def __init__(self) -> None:
        self._credentials: dict[CredentialId, Credential] = {}
        self._passkeys: dict[str, PasskeyCredentialRecord] = {}
        self._factors: dict[UUID, MfaFactor] = {}
        self._code_sets: dict[UUID, RecoveryCodeSet] = {}

    def save(self, credential: Credential) -> None:
        self._credentials[credential.credential_id] = credential

    def get(self, credential_id: CredentialId) -> Credential | None:
        return self._credentials.get(credential_id)

    def for_account(self, account_id: AccountId) -> tuple[Credential, ...]:
        return tuple(
            credential
            for credential in self._credentials.values()
            if credential.account_id == account_id
        )

    def save_passkey(self, record: PasskeyCredentialRecord) -> None:
        self._passkeys[record.credential_reference] = record

    def passkey_by_reference(self, credential_reference: str) -> PasskeyCredentialRecord | None:
        return self._passkeys.get(credential_reference)

    def save_factor(self, factor: MfaFactor) -> None:
        self._factors[factor.factor_id] = factor

    def factors_for(self, account_id: AccountId) -> tuple[MfaFactor, ...]:
        return tuple(factor for factor in self._factors.values() if factor.account_id == account_id)

    def save_recovery_codes(self, code_set: RecoveryCodeSet) -> None:
        self._code_sets[code_set.set_id] = code_set

    def active_recovery_codes(self, account_id: AccountId) -> RecoveryCodeSet | None:
        for code_set in self._code_sets.values():
            if code_set.account_id == account_id and code_set.is_active():
                return code_set
        return None


# --- Authentication ---------------------------------------------------------


class AuthenticationStore(Protocol):
    def save_attempt(self, attempt: AuthenticationAttempt) -> None: ...

    def save_challenge(self, challenge: AuthenticationChallenge) -> None: ...

    def get_challenge(self, challenge_id: UUID) -> AuthenticationChallenge | None: ...

    def save_webauthn_challenge(self, challenge: WebAuthnChallenge) -> None: ...

    def get_webauthn_challenge(self, challenge_id: UUID) -> WebAuthnChallenge | None: ...


class InMemoryAuthenticationStore:
    def __init__(self) -> None:
        self._attempts: dict[UUID, AuthenticationAttempt] = {}
        self._challenges: dict[UUID, AuthenticationChallenge] = {}
        self._webauthn: dict[UUID, WebAuthnChallenge] = {}

    def save_attempt(self, attempt: AuthenticationAttempt) -> None:
        self._attempts[attempt.attempt_id] = attempt

    def save_challenge(self, challenge: AuthenticationChallenge) -> None:
        self._challenges[challenge.challenge_id] = challenge

    def get_challenge(self, challenge_id: UUID) -> AuthenticationChallenge | None:
        return self._challenges.get(challenge_id)

    def save_webauthn_challenge(self, challenge: WebAuthnChallenge) -> None:
        self._webauthn[challenge.challenge_id] = challenge

    def get_webauthn_challenge(self, challenge_id: UUID) -> WebAuthnChallenge | None:
        return self._webauthn.get(challenge_id)


# --- Sessions and step-up ---------------------------------------------------


class SessionStore(Protocol):
    def save(self, session: SessionRecord) -> None: ...

    def get(self, session_id: SessionId) -> SessionRecord | None: ...

    def for_account(self, account_id: AccountId) -> tuple[SessionRecord, ...]: ...

    def save_step_up_challenge(self, challenge: StepUpChallenge) -> None: ...

    def get_step_up_challenge(self, challenge_id: UUID) -> StepUpChallenge | None: ...

    def save_step_up_result(self, result: StepUpResult) -> None: ...

    def get_step_up_result(self, challenge_id: UUID) -> StepUpResult | None: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[SessionId, SessionRecord] = {}
        self._step_up_challenges: dict[UUID, StepUpChallenge] = {}
        self._step_up_results: dict[UUID, StepUpResult] = {}

    def save(self, session: SessionRecord) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: SessionId) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def for_account(self, account_id: AccountId) -> tuple[SessionRecord, ...]:
        return tuple(
            session for session in self._sessions.values() if session.account_id == account_id
        )

    def save_step_up_challenge(self, challenge: StepUpChallenge) -> None:
        self._step_up_challenges[challenge.challenge_id] = challenge

    def get_step_up_challenge(self, challenge_id: UUID) -> StepUpChallenge | None:
        return self._step_up_challenges.get(challenge_id)

    def save_step_up_result(self, result: StepUpResult) -> None:
        self._step_up_results[result.challenge_id] = result

    def get_step_up_result(self, challenge_id: UUID) -> StepUpResult | None:
        return self._step_up_results.get(challenge_id)


# --- Recovery ---------------------------------------------------------------


class RecoveryStore(Protocol):
    def save(self, request: RecoveryRequest) -> None: ...

    def get(self, recovery_id: UUID) -> RecoveryRequest | None: ...

    def open_case_for(self, account_id: AccountId) -> RecoveryRequest | None: ...


class InMemoryRecoveryStore:
    def __init__(self) -> None:
        self._cases: dict[UUID, RecoveryRequest] = {}

    def save(self, request: RecoveryRequest) -> None:
        self._cases[request.recovery_id] = request

    def get(self, recovery_id: UUID) -> RecoveryRequest | None:
        return self._cases.get(recovery_id)

    def open_case_for(self, account_id: AccountId) -> RecoveryRequest | None:
        from epd2_identity_service.recovery import RecoveryState

        terminal = {
            RecoveryState.COMPLETED,
            RecoveryState.REJECTED,
            RecoveryState.CANCELLED,
        }
        for case in self._cases.values():
            if case.account_id == account_id and case.state not in terminal:
                return case
        return None


# --- Identity proofing ------------------------------------------------------


class IdentityProofingStore(Protocol):
    def save(self, case: IdentityProofingCase) -> None: ...

    def get(self, case_id: UUID) -> IdentityProofingCase | None: ...

    def for_account(self, account_id: AccountId) -> tuple[IdentityProofingCase, ...]: ...


class InMemoryIdentityProofingStore:
    def __init__(self) -> None:
        self._cases: dict[UUID, IdentityProofingCase] = {}

    def save(self, case: IdentityProofingCase) -> None:
        self._cases[case.case_id] = case

    def get(self, case_id: UUID) -> IdentityProofingCase | None:
        return self._cases.get(case_id)

    def for_account(self, account_id: AccountId) -> tuple[IdentityProofingCase, ...]:
        return tuple(case for case in self._cases.values() if case.account_id == account_id)


# --- Bootstrap and voting handoff -------------------------------------------


class BootstrapStore(Protocol):
    def save_request(self, request: AuthenticationBootstrapRequest) -> None: ...

    def get_request(self, request_id: UUID) -> AuthenticationBootstrapRequest | None: ...

    def save_response(self, response: AuthenticationBootstrapResponse) -> None: ...

    def get_response(self, response_id: UUID) -> AuthenticationBootstrapResponse | None: ...

    def save_redemption(self, redemption: BootstrapRedemption) -> None: ...

    def redemption_for(self, response_id: UUID) -> BootstrapRedemption | None: ...


class InMemoryBootstrapStore:
    def __init__(self) -> None:
        self._requests: dict[UUID, AuthenticationBootstrapRequest] = {}
        self._responses: dict[UUID, AuthenticationBootstrapResponse] = {}
        self._redemptions: dict[UUID, BootstrapRedemption] = {}

    def save_request(self, request: AuthenticationBootstrapRequest) -> None:
        self._requests[request.request_id] = request

    def get_request(self, request_id: UUID) -> AuthenticationBootstrapRequest | None:
        return self._requests.get(request_id)

    def save_response(self, response: AuthenticationBootstrapResponse) -> None:
        self._responses[response.response_id] = response

    def get_response(self, response_id: UUID) -> AuthenticationBootstrapResponse | None:
        return self._responses.get(response_id)

    def save_redemption(self, redemption: BootstrapRedemption) -> None:
        self._redemptions[redemption.response_id] = redemption

    def redemption_for(self, response_id: UUID) -> BootstrapRedemption | None:
        return self._redemptions.get(response_id)


class VotingHandoffStore(Protocol):
    """Note what is **not** here.

    There is no `issuances_for_account`, because `VotingHandoffIssuance`
    carries no account. There is no `account_for_redemption`, because
    that operation is the reverse bridge ADR-088 forbids -
    `voting_handoff.refuse_reverse_resolution` is the only thing on the
    other side of that question.
    """

    def save_issuance(self, issuance: VotingHandoffIssuance) -> None: ...

    def get_issuance(self, artifact_id: UUID) -> VotingHandoffIssuance | None: ...

    def save_redemption(self, redemption: VotingHandoffRedemptionReference) -> None: ...


class InMemoryVotingHandoffStore:
    def __init__(self) -> None:
        self._issuances: dict[UUID, VotingHandoffIssuance] = {}
        self._redemptions: dict[UUID, VotingHandoffRedemptionReference] = {}

    def save_issuance(self, issuance: VotingHandoffIssuance) -> None:
        self._issuances[issuance.artifact_id] = issuance

    def get_issuance(self, artifact_id: UUID) -> VotingHandoffIssuance | None:
        return self._issuances.get(artifact_id)

    def save_redemption(self, redemption: VotingHandoffRedemptionReference) -> None:
        self._redemptions[redemption.redemption_id] = redemption


# --- Mappings, linking and replay prevention --------------------------------


class IdentityMappingStore(Protocol):
    def save(self, mapping: IdentityMapping) -> None: ...

    def resolve(self, request: MappingResolutionRequest) -> IdentityMapping | None: ...

    def enumerate(
        self, *, purpose: MappingPurpose | None, scope: OrganizationScope | None
    ) -> tuple[IdentityMapping, ...]: ...


class InMemoryIdentityMappingStore:
    def __init__(self) -> None:
        self._mappings: dict[tuple[MappingPurpose, str, str], IdentityMapping] = {}

    @staticmethod
    def _key(
        purpose: MappingPurpose, scope: OrganizationScope, source: ScopedIdentityReference
    ) -> tuple[MappingPurpose, str, str]:
        return (purpose, f"{scope.level.value}:{scope.organizational_unit_id}", source.reference)

    def save(self, mapping: IdentityMapping) -> None:
        self._mappings[self._key(mapping.purpose, mapping.scope, mapping.source_reference)] = (
            mapping
        )

    def resolve(self, request: MappingResolutionRequest) -> IdentityMapping | None:
        return self._mappings.get(
            self._key(request.purpose, request.scope, request.source_reference)
        )

    def enumerate(
        self, *, purpose: MappingPurpose | None, scope: OrganizationScope | None
    ) -> tuple[IdentityMapping, ...]:
        """Enumeration requires both a purpose and a scope.

        `refuse_unrestricted_lookup` raises when either is missing, so
        there is no call shape that returns every mapping - the
        correlation surface the mapping boundary exists to deny.
        """
        refuse_unrestricted_lookup(purpose=purpose, scope=scope)
        return tuple(
            mapping
            for mapping in self._mappings.values()
            if mapping.purpose is purpose and scope is not None and mapping.scope.matches(scope)
        )


class AccountLinkStore(Protocol):
    def save(self, request: AccountLinkRequest) -> None: ...

    def get(self, link_request_id: UUID) -> AccountLinkRequest | None: ...

    def for_account(self, account_id: AccountId) -> tuple[AccountLinkRequest, ...]: ...


class InMemoryAccountLinkStore:
    def __init__(self) -> None:
        self._links: dict[UUID, AccountLinkRequest] = {}

    def save(self, request: AccountLinkRequest) -> None:
        self._links[request.link_request_id] = request

    def get(self, link_request_id: UUID) -> AccountLinkRequest | None:
        return self._links.get(link_request_id)

    def for_account(self, account_id: AccountId) -> tuple[AccountLinkRequest, ...]:
        return tuple(link for link in self._links.values() if link.account_id == account_id)


class ReplayPreventionStore(Protocol):
    def record_nonce(self, record: ReplayNonceRecord) -> None: ...

    def seen_nonce_digests(self) -> frozenset[str]: ...

    def record_idempotency(self, record: IdempotencyRecord) -> None: ...

    def get_idempotency(self, idempotency_key: str) -> IdempotencyRecord | None: ...

    def seen_assertion_ids(self) -> frozenset[str]: ...

    def record_assertion_id(self, assertion_id: str) -> None: ...


class InMemoryReplayPreventionStore:
    def __init__(self) -> None:
        self._nonces: dict[str, ReplayNonceRecord] = {}
        self._idempotency: dict[str, IdempotencyRecord] = {}
        self._assertions: set[str] = set()

    def record_nonce(self, record: ReplayNonceRecord) -> None:
        self._nonces[record.nonce_digest.digest] = record

    def seen_nonce_digests(self) -> frozenset[str]:
        return frozenset(self._nonces)

    def record_idempotency(self, record: IdempotencyRecord) -> None:
        self._idempotency[record.idempotency_key] = record

    def get_idempotency(self, idempotency_key: str) -> IdempotencyRecord | None:
        return self._idempotency.get(idempotency_key)

    def seen_assertion_ids(self) -> frozenset[str]:
        return frozenset(self._assertions)

    def record_assertion_id(self, assertion_id: str) -> None:
        self._assertions.add(assertion_id)
