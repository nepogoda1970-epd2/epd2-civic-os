"""PACK-14 identifier spaces and the boundary that keeps them apart.

This is the module `FIR-INV-001` lives in. Thirteen packs were careful
never to know who anyone is; PACK-14 needs an identifier for
authentication, and the moment one exists every downstream domain has a
reason to store it. One `account_id` column added to a membership table,
a finance record and an event payload, and the correlation the
architecture was built to prevent exists - not as a policy failure, but
as an ordinary schema convenience nobody objected to.

So the identifier spaces here are **distinct Python types** even where
they are all UUIDs underneath. `AccountId` cannot be passed where
`PersonRecordId` is expected, mypy says so at the call site, and the
separation is a compile-time fact rather than a review note. This is the
same discipline `domain.py` already applies to `IdentityAssuranceLevel`
versus `AuthenticationAssuranceLevel`.

What crosses a domain boundary is never a raw identifier: it is a
`ScopedIdentityReference`, derived per purpose, per organizational scope
and per domain owner. Two references derived for two purposes from the
same account do not compare equal and cannot be joined, which is what
makes the absence of a global user ID structural (ADR-079, ADR-080).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType
from uuid import UUID

from epd2_identity_service.exceptions import (
    GlobalIdentifierRefusedError,
    SecretInPayloadRefusedError,
    UnknownIdentityMappingPurposeError,
    UnknownOrganizationLevelError,
)

# --- The identifier spaces (specification section 3) ------------------------

#: The technical account identifier. Authentication and session subject,
#: and nothing else. Not a person record, membership ID, member number,
#: communication persona, voting identifier, login handle or external
#: provider identifier.
AccountId = NewType("AccountId", UUID)

#: The protected person reference. Exists only where identity proofing
#: requires it, is **optional** (most accounts never acquire one), and is
#: never an integration key.
PersonRecordId = NewType("PersonRecordId", UUID)

#: An opaque reference to a membership held by the membership domain.
#: PACK-14 does not own membership identity and stores only this.
MembershipReference = NewType("MembershipReference", str)

#: An opaque reference to a communication persona. Never an
#: authentication or authorization input.
CommunicationPersonaReference = NewType("CommunicationPersonaReference", str)

#: An opaque reference to a credential this service owns.
CredentialId = NewType("CredentialId", UUID)

#: An opaque session identifier. Never appears in a URL.
SessionId = NewType("SessionId", UUID)


class IdentifierSpace(StrEnum):
    """The identifier spaces named in the identity separation matrix, as
    values, so a refusal can say which space was about to leak."""

    ACCOUNT = "account_id"
    PERSON_RECORD = "person_record_id"
    MEMBERSHIP = "membership_id"
    MEMBER_NUMBER = "member_number"
    APPLICANT = "applicant_reference"
    COMMUNICATION_PERSONA = "communication_persona_id"
    VOTING_CREDENTIAL = "voting_credential"
    PROVIDER_SUBJECT = "provider_subject"
    SCOPED_ACTOR = "scoped_actor_reference"


#: Identifier spaces that may **never** cross a domain boundary in a raw
#: form. `SCOPED_ACTOR` is deliberately absent: it is the one thing that
#: may cross, and it is the reason the others need not.
NEVER_CROSSES_A_BOUNDARY: frozenset[IdentifierSpace] = frozenset(
    {
        IdentifierSpace.ACCOUNT,
        IdentifierSpace.PERSON_RECORD,
        IdentifierSpace.MEMBERSHIP,
        IdentifierSpace.MEMBER_NUMBER,
        IdentifierSpace.APPLICANT,
        IdentifierSpace.COMMUNICATION_PERSONA,
        IdentifierSpace.VOTING_CREDENTIAL,
        IdentifierSpace.PROVIDER_SUBJECT,
    }
)

#: Payload keys no PACK-14 event, audit record, metric label or API
#: response may carry. Two groups, both structural rather than advisory:
#: the identifier keys that would create the global identity this pack
#: exists to prevent, and the secret-material keys section 29 of the
#: implementation task forbids from every log and every event.
PROHIBITED_IDENTIFIER_KEYS: frozenset[str] = frozenset(
    {
        "global_user_id",
        "universal_person_id",
        "person_id",
        "person_record_id",
        "membership_id",
        "member_number",
        "communication_persona_id",
        "voting_credential",
        "voting_credential_id",
        "ballot_id",
        "vote_id",
        "tally_id",
        "provider_subject",
        "provider_subject_id",
        "national_id",
        "eid_subject",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "contact_value",
    }
)

PROHIBITED_SECRET_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "password_hash",
        "passphrase",
        "otp",
        "otp_value",
        "one_time_code",
        "verification_code",
        "recovery_code",
        "recovery_codes",
        "totp_secret",
        "shared_secret",
        "private_key",
        "secret_key",
        "assertion",
        "authenticator_response",
        "client_data_json",
        "attestation_object",
        "signature_value",
        "refresh_token",
        "session_token",
        "bearer_token",
        "handoff_artifact",
        "artifact_value",
        "identity_document",
        "document_content",
    }
)


class OrganizationLevel(StrEnum):
    """`FIR-INV-013`'s isolation levels. A mapping, a reference and a
    session are each scoped to one of these, and a scope mismatch is a
    refusal rather than a widened query."""

    BUND = "bund"
    LAND = "land"
    KREIS = "kreis"
    ORTSVERBAND = "ortsverband"


def parse_organization_level(value: str) -> OrganizationLevel:
    try:
        return OrganizationLevel(value)
    except ValueError as exc:
        raise UnknownOrganizationLevelError(f"unknown organization level: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class OrganizationScope:
    """Where an act, a reference or a mapping is valid. Two scopes that
    differ in level or in unit are different scopes; there is no
    "contains" relation here, because a Bund-level reference silently
    satisfying a Kreis-level requirement is exactly the widening
    `FIR-INV-013` forbids."""

    level: OrganizationLevel
    organizational_unit_id: UUID

    def matches(self, other: OrganizationScope) -> bool:
        return (
            self.level is other.level
            and self.organizational_unit_id == other.organizational_unit_id
        )


class MappingPurpose(StrEnum):
    """Why a reference exists. A reference without a purpose is a
    general-purpose reference, which is the global identifier by another
    name - so there is no `GENERAL` member and none may be added."""

    AUTHENTICATION = "authentication"
    SESSION = "session"
    ACCOUNT_SECURITY = "account_security"
    RECOVERY = "recovery"
    IDENTITY_PROOFING = "identity_proofing"
    PRIVILEGED_REVIEW = "privileged_review"
    OFFICIAL_SUBMISSION = "official_submission"
    NOTIFICATION_DELIVERY = "notification_delivery"
    AUDIT_ATTRIBUTION = "audit_attribution"
    VOTING_ENTRY = "voting_entry"


def parse_mapping_purpose(value: str) -> MappingPurpose:
    try:
        return MappingPurpose(value)
    except ValueError as exc:
        raise UnknownIdentityMappingPurposeError(f"unknown mapping purpose: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class ScopedIdentityReference:
    """What a domain or an event actually carries in place of an
    identifier.

    The `reference` is a digest over (purpose, scope, domain owner,
    source space, source value, derivation salt). Two references derived
    for two purposes from one account therefore differ, and neither can
    be reversed to the account without the governed mapping in
    `mappings.py`. The derivation salt is supplied by the caller from the
    service's secret storage abstraction and never appears here, so this
    dataclass is safe to log, hash and put in an event payload - which is
    the whole point of it existing.
    """

    reference: str
    purpose: MappingPurpose
    scope: OrganizationScope
    domain_owner: str

    def __post_init__(self) -> None:
        if len(self.reference) != 64 or not all(c in "0123456789abcdef" for c in self.reference):
            raise ValueError("reference must be a 64-character lower-case hex digest")
        if not self.domain_owner:
            raise ValueError("domain_owner must not be empty")

    def as_payload(self) -> Mapping[str, str]:
        return {
            "reference": self.reference,
            "purpose": self.purpose.value,
            "scope_level": self.scope.level.value,
            "scope_unit_id": str(self.scope.organizational_unit_id),
            "domain_owner": self.domain_owner,
        }


def derive_scoped_reference(
    *,
    space: IdentifierSpace,
    value: str,
    purpose: MappingPurpose,
    scope: OrganizationScope,
    domain_owner: str,
    derivation_salt: bytes,
) -> ScopedIdentityReference:
    """Derive the purpose-scoped reference a domain outside this service
    is permitted to hold.

    `derivation_salt` must be a per-deployment secret held in the secret
    storage abstraction (`secrets.py`). Without it the digest would be
    computable by anyone holding an `account_id`, and a reference anyone
    can recompute from the raw identifier is not a boundary - it is the
    raw identifier with extra steps.
    """
    if len(derivation_salt) < 32:
        raise ValueError("derivation_salt must be at least 32 bytes")
    digest = hashlib.sha256()
    digest.update(derivation_salt)
    for part in (
        space.value,
        value,
        purpose.value,
        scope.level.value,
        str(scope.organizational_unit_id),
        domain_owner,
    ):
        digest.update(b"\x1f")
        digest.update(part.encode("utf-8"))
    return ScopedIdentityReference(
        reference=digest.hexdigest(),
        purpose=purpose,
        scope=scope,
        domain_owner=domain_owner,
    )


def reject_prohibited_payload_keys(payload: Mapping[str, object]) -> None:
    """Fail closed before an envelope, an audit record or a metric label
    exists.

    Called by every event builder and every audit path in this package,
    so a future contributor who reaches for a convenient identifier or a
    secret gets a refusal at construction rather than a review comment
    after the fact. Nested mappings are walked, because a prohibited key
    one level down is still in the payload.
    """
    for key, value in payload.items():
        if key in PROHIBITED_SECRET_KEYS:
            raise SecretInPayloadRefusedError(f"payload key {key!r} would carry secret material")
        if key in PROHIBITED_IDENTIFIER_KEYS:
            raise GlobalIdentifierRefusedError(
                f"payload key {key!r} would carry an identifier that may not cross this boundary"
            )
        if isinstance(value, Mapping):
            reject_prohibited_payload_keys(value)
        elif isinstance(value, list | tuple):
            for item in value:
                if isinstance(item, Mapping):
                    reject_prohibited_payload_keys(item)


def assert_reference_crosses_boundary(space: IdentifierSpace) -> None:
    """Refuse a raw identifier where only a scoped reference may go."""
    if space in NEVER_CROSSES_A_BOUNDARY:
        raise GlobalIdentifierRefusedError(
            f"{space.value} may not cross a domain boundary; derive a scoped reference instead"
        )


def require_timezone(moment: datetime, field_name: str) -> datetime:
    """Every timestamp in this package is timezone-aware. A naive
    datetime in a deadline calculation is a silently wrong deadline."""
    if moment.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return moment
