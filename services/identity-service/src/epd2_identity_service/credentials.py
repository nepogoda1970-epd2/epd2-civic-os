"""Credential Registry - what an account can authenticate with, and what
this service is allowed to know about it.

The registry stores **metadata only**. No password, no TOTP seed, no
recovery-code value and no WebAuthn private key exists in any field of
any dataclass here: the password hash lives behind
`secret_storage.PasswordHasher`, the TOTP seed behind the deployment's
secret store, and the passkey public key is - by construction - public.
That is the structural version of the retention matrix's promise that
"no key material ever existed here".

The last rule is the one people are surprised by:
`CREDENTIAL_LAST_REMAINING` refuses removal of the only credential when
no recovery path exists. It is not paternalism; an account with no
credential and no recovery path is an account nobody can ever open again,
including its owner.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from epd2_identity_service.exceptions import (
    CredentialAlreadyEnrolledError,
    CredentialExpiredError,
    CredentialRevokedError,
    ForbiddenCredentialTransitionError,
    LastRemainingCredentialError,
    UnknownCredentialStatusError,
    UnknownCredentialTypeError,
)
from epd2_identity_service.identifiers import AccountId, CredentialId, require_timezone


class CredentialType(StrEnum):
    """The credential classes PACK-14 registers.

    `EXTERNAL_PROVIDER_REFERENCE` is a *reference*, never a subject claim
    used as a key (ADR-079 §3). `RECOVERY_EVIDENCE_REFERENCE` is the
    controlled evidence a recovery decision rests on, held by reference
    in PACK-11 rather than copied here.
    """

    PASSKEY = "passkey"
    PASSWORD_REFERENCE = "password_reference"
    TOTP = "totp"
    HARDWARE_SECURITY_KEY = "hardware_security_key"
    RECOVERY_CODE_SET = "recovery_code_set"
    EXTERNAL_PROVIDER_REFERENCE = "external_provider_reference"
    RECOVERY_EVIDENCE_REFERENCE = "recovery_evidence_reference"


def parse_credential_type(value: str) -> CredentialType:
    try:
        return CredentialType(value)
    except ValueError as exc:
        raise UnknownCredentialTypeError(f"unknown credential type: {value!r}") from exc


class CredentialStatus(StrEnum):
    PENDING_CONFIRMATION = "pending_confirmation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


def parse_credential_status(value: str) -> CredentialStatus:
    try:
        return CredentialStatus(value)
    except ValueError as exc:
        raise UnknownCredentialStatusError(f"unknown credential status: {value!r}") from exc


_ALLOWED_CREDENTIAL_TRANSITIONS: frozenset[tuple[CredentialStatus, CredentialStatus]] = frozenset(
    {
        (CredentialStatus.PENDING_CONFIRMATION, CredentialStatus.ACTIVE),
        (CredentialStatus.PENDING_CONFIRMATION, CredentialStatus.REVOKED),
        (CredentialStatus.ACTIVE, CredentialStatus.SUSPENDED),
        (CredentialStatus.ACTIVE, CredentialStatus.REVOKED),
        (CredentialStatus.ACTIVE, CredentialStatus.EXPIRED),
        (CredentialStatus.SUSPENDED, CredentialStatus.ACTIVE),
        (CredentialStatus.SUSPENDED, CredentialStatus.REVOKED),
        (CredentialStatus.EXPIRED, CredentialStatus.REVOKED),
    }
)


class CredentialBinding(StrEnum):
    """Device-bound or synced - recorded distinctly (ADR-081).

    This one field is why a synced passkey caps at `substantial`: the
    syncing cloud account is part of its trust chain, and that account is
    not this system's to assess. `NOT_APPLICABLE` covers credential types
    where the question is meaningless, such as a recovery code set.
    """

    DEVICE_BOUND = "device_bound"
    SYNCED = "synced"
    NOT_APPLICABLE = "not_applicable"


class AttestationState(StrEnum):
    """Attestation is **not** universally required (OD-P14-08).

    `NOT_REQUESTED` is the ordinary case and carries no penalty: no
    member is excluded from ordinary participation for lack of
    attestation (`FIR-INCLUSION-001`). It is requested only where a named
    risk assessment requires it for a named privileged action class.
    """

    NOT_REQUESTED = "not_requested"
    PRESENTED_UNVERIFIED = "presented_unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class CredentialMetadata:
    """Everything the registry may know about a credential.

    Deliberately free of any field that could hold secret material. The
    nickname is the user's own label so they can recognise a device in
    their inventory later; the field catalogue notes it needs no personal
    data, and nothing here requires one.
    """

    nickname: str
    binding: CredentialBinding
    attestation: AttestationState
    backup_eligible: bool
    backup_state: bool
    authenticator_class: str
    sign_counter: int | None = None

    def __post_init__(self) -> None:
        if not 1 <= len(self.nickname) <= 64:
            raise ValueError("credential nickname must be 1-64 characters")
        if self.sign_counter is not None and self.sign_counter < 0:
            raise ValueError("sign_counter must not be negative")


@dataclass(frozen=True, slots=True)
class CredentialRevocation:
    """Immutable, and it names who did it and why.

    `actor_class` rather than an actor identifier: an audit record needs
    to distinguish "the holder revoked their own passkey" from "a
    Security Admin revoked it", and it does not need to carry the
    identifier that would let a reader correlate across domains.
    """

    revoked_at: datetime
    reason_code: str
    actor_class: str

    def __post_init__(self) -> None:
        require_timezone(self.revoked_at, "revoked_at")
        if not self.reason_code:
            raise ValueError("a revocation carries a registered reason code")
        if not self.actor_class:
            raise ValueError("a revocation names the acting role class")


@dataclass(frozen=True, slots=True)
class Credential:
    """One credential on one account."""

    credential_id: CredentialId
    account_id: AccountId
    credential_type: CredentialType
    status: CredentialStatus
    metadata: CredentialMetadata
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    revocation: CredentialRevocation | None
    version: int

    def __post_init__(self) -> None:
        require_timezone(self.created_at, "created_at")
        if self.last_used_at is not None:
            require_timezone(self.last_used_at, "last_used_at")
        if self.expires_at is not None:
            require_timezone(self.expires_at, "expires_at")
        if (self.status is CredentialStatus.REVOKED) != (self.revocation is not None):
            raise ValueError("a revoked credential carries a revocation record, and only it does")

    def assert_usable(self, now: datetime) -> None:
        """Three distinct refusals, never merged into one.

        In an incident review the difference between "wrong secret",
        "revoked" and "expired" is the difference between a typo, a
        response that worked, and a housekeeping gap.
        """
        if self.status is CredentialStatus.REVOKED:
            raise CredentialRevokedError("the credential has been revoked")
        if self.status is CredentialStatus.EXPIRED:
            raise CredentialExpiredError("the credential is past its validity")
        if self.expires_at is not None and require_timezone(now, "now") >= self.expires_at:
            raise CredentialExpiredError("the credential is past its validity")
        if self.status is not CredentialStatus.ACTIVE:
            raise CredentialRevokedError(
                f"the credential is {self.status.value} and cannot authenticate"
            )

    def assert_transition_allowed(self, target: CredentialStatus) -> None:
        if (self.status, target) not in _ALLOWED_CREDENTIAL_TRANSITIONS:
            raise ForbiddenCredentialTransitionError(
                f"credential transition {self.status.value!r} -> {target.value!r} is not allowed"
            )

    def transitioned(self, target: CredentialStatus) -> Credential:
        """Only for transitions that need no companion record.

        Revocation goes through `revoked` instead: a revoked credential
        must carry its revocation record, and an intermediate without one
        would break that invariant on the way to satisfying it.
        """
        self.assert_transition_allowed(target)
        return replace(self, status=target, version=self.version + 1)

    def revoked(self, revocation: CredentialRevocation) -> Credential:
        self.assert_transition_allowed(CredentialStatus.REVOKED)
        return replace(
            self,
            status=CredentialStatus.REVOKED,
            revocation=revocation,
            version=self.version + 1,
        )

    def used_at(self, moment: datetime) -> Credential:
        return replace(self, last_used_at=require_timezone(moment, "moment"))


def enroll_credential(
    *,
    credential_id: CredentialId,
    account_id: AccountId,
    credential_type: CredentialType,
    metadata: CredentialMetadata,
    created_at: datetime,
    existing: tuple[Credential, ...],
    expires_at: datetime | None = None,
    requires_confirmation: bool = True,
) -> Credential:
    """Enroll a credential. Two of the same type with the same nickname
    would make revocation ambiguous, so the second is refused."""
    for other in existing:
        if other.status in (CredentialStatus.REVOKED, CredentialStatus.EXPIRED):
            continue
        if (
            other.credential_type is credential_type
            and other.metadata.nickname == metadata.nickname
        ):
            raise CredentialAlreadyEnrolledError(
                "a credential of this type with this nickname is already enrolled"
            )
    return Credential(
        credential_id=credential_id,
        account_id=account_id,
        credential_type=credential_type,
        status=(
            CredentialStatus.PENDING_CONFIRMATION
            if requires_confirmation
            else CredentialStatus.ACTIVE
        ),
        metadata=metadata,
        created_at=require_timezone(created_at, "created_at"),
        last_used_at=None,
        expires_at=expires_at,
        revocation=None,
        version=1,
    )


def active_credentials(credentials: tuple[Credential, ...]) -> tuple[Credential, ...]:
    return tuple(
        credential for credential in credentials if credential.status is CredentialStatus.ACTIVE
    )


def assert_removal_leaves_a_way_in(
    *,
    credential: Credential,
    all_credentials: tuple[Credential, ...],
    recovery_path_available: bool,
) -> None:
    """`CREDENTIAL_LAST_REMAINING`.

    `recovery_path_available` is passed in rather than inferred, because
    what counts as a recovery path is a policy question the recovery
    module owns - an unexhausted recovery code set, a verified
    independent channel, or an assisted channel the deployment supports.
    """
    remaining = [
        other
        for other in active_credentials(all_credentials)
        if other.credential_id != credential.credential_id
        and other.credential_type is not CredentialType.RECOVERY_EVIDENCE_REFERENCE
    ]
    if remaining or recovery_path_available:
        return
    raise LastRemainingCredentialError(
        "this is the only credential on the account and no recovery path exists"
    )


def credentials_compromised_response(
    credentials: tuple[Credential, ...],
    *,
    revoked_at: datetime,
    reason_code: str,
    actor_class: str,
) -> tuple[Credential, ...]:
    """The compromise workflow's first step: revoke, then the caller
    revokes the sessions those credentials could have produced.

    Returned rather than applied in place so the caller performs both
    halves in one transaction - a compromise response that revokes
    credentials and leaves sessions running has responded to nothing.
    """
    revocation = CredentialRevocation(
        revoked_at=require_timezone(revoked_at, "revoked_at"),
        reason_code=reason_code,
        actor_class=actor_class,
    )
    return tuple(
        credential.revoked(revocation)
        for credential in credentials
        if credential.status
        in (
            CredentialStatus.ACTIVE,
            CredentialStatus.SUSPENDED,
            CredentialStatus.PENDING_CONFIRMATION,
        )
    )
