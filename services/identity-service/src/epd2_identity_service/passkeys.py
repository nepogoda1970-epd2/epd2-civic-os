"""Passkeys / WebAuthn - the contract and the verification **boundary**.

**No WebAuthn cryptography is implemented in this repository.** The task
forbids it and the forbidding is correct: a hand-written COSE parser and
signature verifier that passes its own tests is the most dangerous kind
of working code. What exists here is:

- `WebAuthnVerifier`, a `Protocol` a deployment binds to a mature,
  audited library;
- `UnboundWebAuthnVerifier`, the default binding, which **refuses**;
- `DeterministicWebAuthnVerifier`, an explicit test double that verifies
  a fixture format and says so in its own name;
- the ceremony state machine, the replay controls, the origin binding,
  the sign-counter rule and the credential classification - all of which
  are protocol discipline rather than cryptography, and all of which are
  this pack's to get right.

A real browser ceremony cannot run in CI, so the protocol fixtures and
the negative tests are how the boundary is exercised. The verifier port
is the seam; everything on this side of it is tested for real.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from epd2_identity_service.credentials import (
    AttestationState,
    CredentialBinding,
    CredentialMetadata,
)
from epd2_identity_service.exceptions import (
    MalformedAuthenticatorResponseError,
    PasskeyChallengeExpiredError,
    PasskeyOriginMismatchError,
    PasskeySignCounterRegressionError,
    PasskeyVerificationFailedError,
)
from epd2_identity_service.identifiers import AccountId, CredentialId, require_timezone
from epd2_identity_service.secret_storage import SecureRandom, constant_time_equals

#: The ceremonies this module models. Registration and authentication use
#: separate challenge stores so a registration challenge can never be
#: replayed into an authentication.
CEREMONY_REGISTRATION = "registration"
CEREMONY_AUTHENTICATION = "authentication"


@dataclass(frozen=True, slots=True)
class WebAuthnChallenge:
    """A single-use challenge, bound to one ceremony, one account and one
    origin."""

    challenge_id: UUID
    challenge: str
    ceremony: str
    account_id: AccountId
    relying_party_origin: str
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.consumed_at is not None:
            require_timezone(self.consumed_at, "consumed_at")
        if self.ceremony not in (CEREMONY_REGISTRATION, CEREMONY_AUTHENTICATION):
            raise MalformedAuthenticatorResponseError(f"unknown ceremony {self.ceremony!r}")
        if self.expires_at <= self.issued_at:
            raise ValueError("a challenge must expire after it was issued")

    def assert_open(self, now: datetime) -> None:
        if self.consumed_at is not None:
            raise PasskeyChallengeExpiredError("the challenge has already been consumed")
        if require_timezone(now, "now") >= self.expires_at:
            raise PasskeyChallengeExpiredError("the challenge has expired")


@dataclass(frozen=True, slots=True)
class AuthenticatorResponse:
    """The subset of a WebAuthn response this boundary needs.

    Deliberately a small, named structure rather than a raw blob: the
    full `clientDataJSON` and `attestationObject` stay on the wire and in
    the verifier, never in a record, an event or a log. `signature` is
    present because the verifier needs it as an argument and is never
    stored.
    """

    credential_reference: str
    client_data_challenge: str
    origin: str
    signature: str
    sign_counter: int | None
    backup_eligible: bool
    backup_state: bool
    device_bound: bool
    attestation_presented: bool
    authenticator_class: str

    def __post_init__(self) -> None:
        for name in ("credential_reference", "client_data_challenge", "origin", "signature"):
            if not getattr(self, name):
                raise MalformedAuthenticatorResponseError(f"{name} must not be empty")
        if self.sign_counter is not None and self.sign_counter < 0:
            raise MalformedAuthenticatorResponseError("sign_counter must not be negative")


@dataclass(frozen=True, slots=True)
class PasskeyCredentialRecord:
    """What is stored after a successful registration ceremony.

    `public_key` is public by definition. There is no private-key field
    and no field a private key could be put in.
    """

    credential_id: CredentialId
    account_id: AccountId
    credential_reference: str
    public_key: str
    sign_counter: int | None
    binding: CredentialBinding
    attestation: AttestationState
    backup_eligible: bool
    backup_state: bool
    authenticator_class: str
    relying_party_origin: str

    def to_metadata(self, nickname: str) -> CredentialMetadata:
        return CredentialMetadata(
            nickname=nickname,
            binding=self.binding,
            attestation=self.attestation,
            backup_eligible=self.backup_eligible,
            backup_state=self.backup_state,
            authenticator_class=self.authenticator_class,
            sign_counter=self.sign_counter,
        )


class WebAuthnVerifier(Protocol):
    """The verification port.

    A deployment binds this to a mature library. The two methods take
    everything the library needs and return the facts this package
    records - never the assertion itself, so no caller can accidentally
    persist one.
    """

    def verify_registration(
        self, response: AuthenticatorResponse, *, challenge: WebAuthnChallenge
    ) -> str: ...

    def verify_assertion(
        self,
        response: AuthenticatorResponse,
        *,
        challenge: WebAuthnChallenge,
        stored_public_key: str,
    ) -> bool: ...


class UnboundWebAuthnVerifier:
    """The default binding: refuses both operations.

    Fail-closed by construction. A deployment that has not bound a real
    verifier cannot register or authenticate a passkey, and gets a
    refusal that names the missing dependency rather than a quietly
    permissive stub.
    """

    def verify_registration(
        self, response: AuthenticatorResponse, *, challenge: WebAuthnChallenge
    ) -> str:
        raise PasskeyVerificationFailedError(
            "no WebAuthn verifier is bound; bind an audited library before enabling passkeys"
        )

    def verify_assertion(
        self,
        response: AuthenticatorResponse,
        *,
        challenge: WebAuthnChallenge,
        stored_public_key: str,
    ) -> bool:
        raise PasskeyVerificationFailedError("no WebAuthn verifier is bound")


class DeterministicWebAuthnVerifier:
    """A **test provider**, and it says so in its name.

    It performs no cryptography. A fixture "signature" is accepted when
    it equals `f"{challenge}:{credential_reference}"` for registration
    and `f"{challenge}:{public_key}"` for assertion - a deterministic
    protocol fixture that lets the ceremony state machine, the replay
    controls, the counter rule and every negative path be tested without
    a browser, while remaining obviously not a verifier to any reader.
    """

    def verify_registration(
        self, response: AuthenticatorResponse, *, challenge: WebAuthnChallenge
    ) -> str:
        expected = f"{challenge.challenge}:{response.credential_reference}"
        if not constant_time_equals(response.signature, expected):
            raise PasskeyVerificationFailedError("fixture registration signature did not match")
        return f"public-key-for-{response.credential_reference}"

    def verify_assertion(
        self,
        response: AuthenticatorResponse,
        *,
        challenge: WebAuthnChallenge,
        stored_public_key: str,
    ) -> bool:
        expected = f"{challenge.challenge}:{stored_public_key}"
        return constant_time_equals(response.signature, expected)


def issue_challenge(
    *,
    challenge_id: UUID,
    ceremony: str,
    account_id: AccountId,
    relying_party_origin: str,
    issued_at: datetime,
    lifetime: timedelta,
    random: SecureRandom,
) -> WebAuthnChallenge:
    return WebAuthnChallenge(
        challenge_id=challenge_id,
        challenge=random.token(),
        ceremony=ceremony,
        account_id=account_id,
        relying_party_origin=relying_party_origin,
        issued_at=require_timezone(issued_at, "issued_at"),
        expires_at=require_timezone(issued_at, "issued_at") + lifetime,
    )


def _assert_ceremony_preconditions(
    response: AuthenticatorResponse, challenge: WebAuthnChallenge, now: datetime
) -> None:
    challenge.assert_open(now)
    if not constant_time_equals(response.client_data_challenge, challenge.challenge):
        raise PasskeyVerificationFailedError("the response does not carry this challenge")
    if response.origin != challenge.relying_party_origin:
        raise PasskeyOriginMismatchError(
            f"the assertion was produced for {response.origin!r}, "
            f"not {challenge.relying_party_origin!r}"
        )


def classify_binding(response: AuthenticatorResponse) -> CredentialBinding:
    """Device-bound or synced (ADR-081, OD-P14-08).

    A credential that is backup-eligible is treated as synced even before
    it has actually been backed up: eligibility means the cloud account
    is already in its trust chain, and waiting for `backup_state` would
    classify it generously for exactly as long as the attacker needs.
    """
    if response.device_bound and not response.backup_eligible:
        return CredentialBinding.DEVICE_BOUND
    return CredentialBinding.SYNCED


def complete_registration(
    *,
    credential_id: CredentialId,
    response: AuthenticatorResponse,
    challenge: WebAuthnChallenge,
    verifier: WebAuthnVerifier,
    now: datetime,
    attestation_required: bool = False,
) -> PasskeyCredentialRecord:
    """Verify a registration ceremony and produce the stored record.

    `attestation_required` defaults to `False` because OD-P14-08 decided
    there is no universal attestation requirement; it is set only by a
    named risk assessment for a named privileged action class, and no
    ordinary member path passes `True`.
    """
    if challenge.ceremony != CEREMONY_REGISTRATION:
        raise PasskeyVerificationFailedError("this challenge was not issued for registration")
    _assert_ceremony_preconditions(response, challenge, now)
    if attestation_required and not response.attestation_presented:
        raise PasskeyVerificationFailedError(
            "this action class requires attestation and none was presented"
        )
    public_key = verifier.verify_registration(response, challenge=challenge)
    attestation = (
        AttestationState.PRESENTED_UNVERIFIED
        if response.attestation_presented
        else AttestationState.NOT_REQUESTED
    )
    return PasskeyCredentialRecord(
        credential_id=credential_id,
        account_id=challenge.account_id,
        credential_reference=response.credential_reference,
        public_key=public_key,
        sign_counter=response.sign_counter,
        binding=classify_binding(response),
        attestation=attestation,
        backup_eligible=response.backup_eligible,
        backup_state=response.backup_state,
        authenticator_class=response.authenticator_class,
        relying_party_origin=challenge.relying_party_origin,
    )


def verify_assertion(
    *,
    response: AuthenticatorResponse,
    challenge: WebAuthnChallenge,
    record: PasskeyCredentialRecord,
    verifier: WebAuthnVerifier,
    now: datetime,
) -> int | None:
    """Verify an authentication ceremony; return the new sign counter.

    The counter rule is the one piece of replay-related metadata this
    boundary enforces itself: where the authenticator supports counters,
    a value that does not strictly increase means two authenticators are
    presenting the same credential, which is the cloned-authenticator
    signal. Where the authenticator reports no counter - as most platform
    authenticators do - `None` is recorded and no inference is drawn,
    rather than a zero being invented and compared.
    """
    if challenge.ceremony != CEREMONY_AUTHENTICATION:
        raise PasskeyVerificationFailedError("this challenge was not issued for authentication")
    _assert_ceremony_preconditions(response, challenge, now)
    if response.credential_reference != record.credential_reference:
        raise PasskeyVerificationFailedError("the assertion names a different credential")
    if not verifier.verify_assertion(
        response, challenge=challenge, stored_public_key=record.public_key
    ):
        raise PasskeyVerificationFailedError("assertion verification failed")
    if (
        record.sign_counter is not None
        and response.sign_counter is not None
        and response.sign_counter <= record.sign_counter
    ):
        raise PasskeySignCounterRegressionError(
            f"sign counter {response.sign_counter} did not advance beyond "
            f"the stored {record.sign_counter}"
        )
    return response.sign_counter
