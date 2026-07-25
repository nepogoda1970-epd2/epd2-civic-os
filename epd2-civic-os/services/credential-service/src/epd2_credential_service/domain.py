"""`ParticipationCredential`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 10.1, plus
CLAUDE-PACK-02 section 6.1's additive fields (ADR-002).

This is an opaque reference credential for MVP (pack section 6): no blind
signatures, no zero-knowledge proofs, no anonymity claim beyond "this
object structurally cannot be traced back to an identity" - see
`docs/review/PACK-02-THREAT-MODEL.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_credential_service.exceptions import (
    ForbiddenCredentialTransitionError,
    UnknownCredentialStatusError,
)

CURRENT_CREDENTIAL_VERSION = 1
SUPPORTED_CREDENTIAL_VERSIONS = frozenset({1})


class CredentialType(StrEnum):
    """Canon section 10.1's exact type list."""

    SPACE_ACCESS = "space_access"
    INITIATIVE_SUPPORT = "initiative_support"
    BALLOT_ACCESS = "ballot_access"
    DELEGATION_ACCESS = "delegation_access"
    AUDIT_ACCESS = "audit_access"


class CredentialStatus(StrEnum):
    """Canon section 10.1's exact status list."""

    ISSUED = "issued"
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


ALLOWED_TRANSITIONS: frozenset[tuple[CredentialStatus, CredentialStatus]] = frozenset(
    {
        (CredentialStatus.ISSUED, CredentialStatus.ACTIVE),
        (CredentialStatus.ISSUED, CredentialStatus.REVOKED),
        (CredentialStatus.ISSUED, CredentialStatus.EXPIRED),
        (CredentialStatus.ACTIVE, CredentialStatus.USED),
        (CredentialStatus.ACTIVE, CredentialStatus.EXPIRED),
        (CredentialStatus.ACTIVE, CredentialStatus.REVOKED),
        (CredentialStatus.USED, CredentialStatus.EXPIRED),
        (CredentialStatus.USED, CredentialStatus.REVOKED),
    }
)


def parse_status(value: str) -> CredentialStatus:
    try:
        return CredentialStatus(value)
    except ValueError as exc:
        raise UnknownCredentialStatusError(f"unknown credential status: {value!r}") from exc


def assert_transition_allowed(current: CredentialStatus, target: CredentialStatus) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenCredentialTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


# The complete, allowed public field set. Any field NOT in this set must
# never appear on ParticipationCredential - enforced by
# tests/contract/test_identity_leakage.py at the repository root.
FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "identity_record_id",
        "person_id",
        "account_id",
        "full_name",
        "date_of_birth",
        "address",
        "email",
        "eid_subject",
    }
)


@dataclass(frozen=True, slots=True)
class ParticipationCredential:
    """The public credential DTO. Structurally cannot carry identity data
    - it only has the fields listed here, all of which are either canon
    section 10.1 fields or pack section 6.1's additive fields (ADR-002).
    """

    credential_id: UUID
    credential_type: CredentialType
    scope_type: str
    scope_id: UUID
    issued_at: datetime
    valid_from: datetime
    expires_at: datetime
    status: CredentialStatus
    usage_limit: int | None
    usage_counter: int
    revocation_status: str
    issuer_signature: str | None
    credential_version: int
    rule_version: int
    eligibility_snapshot_digest: str

    def __post_init__(self) -> None:
        for name in ("issued_at", "valid_from", "expires_at"):
            value = getattr(self, name)
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.usage_counter < 0:
            raise ValueError("usage_counter must not be negative")
        if self.usage_limit is not None and self.usage_counter > self.usage_limit:
            raise ValueError("usage_counter must not exceed usage_limit")

    def with_status(self, new_status: CredentialStatus) -> ParticipationCredential:
        assert_transition_allowed(self.status, new_status)
        return _replace_status(self, new_status)


def _replace_status(
    credential: ParticipationCredential, new_status: CredentialStatus
) -> ParticipationCredential:
    return ParticipationCredential(
        credential_id=credential.credential_id,
        credential_type=credential.credential_type,
        scope_type=credential.scope_type,
        scope_id=credential.scope_id,
        issued_at=credential.issued_at,
        valid_from=credential.valid_from,
        expires_at=credential.expires_at,
        status=new_status,
        usage_limit=credential.usage_limit,
        usage_counter=credential.usage_counter,
        revocation_status=(
            "revoked" if new_status == CredentialStatus.REVOKED else credential.revocation_status
        ),
        issuer_signature=credential.issuer_signature,
        credential_version=credential.credential_version,
        rule_version=credential.rule_version,
        eligibility_snapshot_digest=credential.eligibility_snapshot_digest,
    )


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Pack section 6.3: valid/invalid, allowed scope, expiry, reason
    codes, credential version - nothing else. Never includes identity
    data, by construction (there is no identity-shaped field to include).
    """

    valid: bool
    scope_type: str | None
    scope_id: UUID | None
    expires_at: datetime | None
    reason_codes: tuple[str, ...]
    credential_version: int
