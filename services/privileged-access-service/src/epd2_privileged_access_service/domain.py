"""Privileged Access Service domain primitives (PACK-12).

Value objects, the identity-minimisation model and the pure invariant
functions the three bounded contexts are built on. No I/O, no clock, no
storage: every function here is deterministic and testable in isolation,
exactly as `finance-service.domain` is for PACK-10 and
`document-service.domain` is for PACK-11.

Four rules shape everything below:

- **Scope travels with everything.** Every grant, query, export and
  policy carries an `OrganizationalScopeRef`; an undeterminable scope
  denies rather than defaulting (`P12-ORG-003`, `P12-ORG-004`).
- **Purpose is a first-class field, not a comment.** A grant, a query and
  an export each declare a purpose, and the purpose may only narrow what
  is reachable, never widen it (`P12-PAM-002`, `P12-SRCH-011`).
- **No secret ever enters a record.** `PROHIBITED_PAYLOAD_KEYS` is the
  structural backstop applied at every event and evidence boundary
  (`P12-SES-002`, `P12-EVT-003`).
- **No voting reference type exists.** There is deliberately no value
  object in this package capable of pointing at ballot content, a vote
  envelope or uncertified tally material (`P12-VOTE-002`). The
  prohibition is structural, so there is nothing to misconfigure.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_privileged_access_service.exceptions import (
    AssignmentNotEffectiveDatedError,
    JustificationMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    PrivilegedSessionSecretForbiddenError,
    PrivilegePurposeMismatchError,
    StandingAccessProhibitedError,
)

# ---------------------------------------------------------------------------
# Payload minimisation
# ---------------------------------------------------------------------------

#: Field names that may never appear in a PACK-12 record, an event
#: payload, session evidence or a projection (`P12-SES-002`,
#: `P12-EVT-003`). The list is about *shapes of secret and of identity*,
#: not about one service's naming: any of these arriving at a PACK-12
#: boundary is a forbidden payload, whoever produced it.
#:
#: The voting entries are the load-bearing ones. PACK-12 defines no type
#: that could carry them, so this set is a backstop for a payload
#: assembled somewhere else, not the primary defence (`P12-VOTE-002`).
PROHIBITED_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        # secrets and credentials
        "password",
        "passphrase",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "session_token",
        "api_key",
        "apikey",
        "private_key",
        "privatekey",
        "key_material",
        "credential",
        "credentials",
        "certificate_key",
        "signing_key",
        "seed",
        "nonce_secret",
        # identity attributes
        "user_id",
        "userid",
        "person_id",
        "personid",
        "global_user_id",
        "member_id",
        "membership_id",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "full_name",
        "first_name",
        "last_name",
        "address",
        "postal_address",
        "date_of_birth",
        "birth_date",
        "national_id",
        "iban",
        "bic",
        # voting material - structurally impossible here, refused anyway
        "ballot",
        "ballot_id",
        "ballot_content",
        "vote",
        "vote_id",
        "vote_content",
        "vote_envelope",
        "vote_selection",
        "voter_id",
        "voter_choice",
        "choice",
        "tally",
        "partial_tally",
        "intermediate_tally",
        "tally_input",
        "eligibility_token",
        "voting_credential",
        # bulk content
        "content",
        "body",
        "raw_content",
        "document_bytes",
        "file_bytes",
        "export_payload",
        "artifact_bytes",
        "extracted_text",
        "ocr_text",
        "query_text",
        "raw_query",
    }
)


def reject_prohibited_payload_keys(payload: object, *, context: str) -> None:
    """Raise if any prohibited key appears anywhere in `payload`.

    Applied at every event-construction, evidence-construction and
    projection boundary. Nested mappings and sequences are walked,
    because a prohibited key one level down is the same leak as one at
    the top.

    **What it does not catch.** A key-name check sees names, not values. A
    payload hiding a token in a field called `note_reference` passes here
    and is caught by nothing in this module. The structural defence is
    that no type in this package has a field for such a value; this
    function guards payloads assembled elsewhere."""

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                key_text = str(key)
                if key_text.lower() in PROHIBITED_PAYLOAD_KEYS:
                    raise PrivilegedSessionSecretForbiddenError(
                        f"{context}: prohibited key {key_text!r} at {path or '<root>'}"
                    )
                walk(value, f"{path}.{key_text}" if path else key_text)
        elif isinstance(node, list | tuple):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload, "")


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def require_timezone(moment: datetime, *, context: str) -> datetime:
    """Every stored instant is timezone-explicit; a naive datetime is
    refused rather than assumed to be UTC."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise AssignmentNotEffectiveDatedError(
            f"{context}: a naive datetime is refused - an explicit timezone is required"
        )
    return moment


def require_text(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise AssignmentNotEffectiveDatedError(f"{field_name} must be a non-empty string")
    return value


def deterministic_digest(*parts: str) -> str:
    """A stable content digest used for manifests, evidence sealing and
    idempotency keys. Deterministic across processes and runs."""
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Organizational scope
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrganizationalScopeRef:
    """A PACK-08 organizational scope, carried by every PACK-12 record.

    Opaque by construction: an id plus the scope kind PACK-08 assigned.
    This service never interprets the hierarchy itself - inheritance and
    the six cross-scope access modes stay with `organization-service`
    (`P12-ORG-006`)."""

    organization_id: UUID
    scope_kind: str = "organization"

    def __post_init__(self) -> None:
        require_text(self.scope_kind, "scope_kind")

    def assert_matches(self, other: OrganizationalScopeRef | None) -> None:
        """Raise unless `other` is the same scope. `None` is undetermined
        and denies rather than defaulting (`P12-ORG-004`)."""
        if other is None:
            raise OrganizationScopeUndeterminedError("organizational scope is undetermined")
        if other.organization_id != self.organization_id:
            raise OrganizationScopeMismatchError(
                "organizational scope does not match the target record's scope"
            )

    def to_payload(self) -> dict[str, object]:
        return {"organization_id": str(self.organization_id), "scope_kind": self.scope_kind}


# ---------------------------------------------------------------------------
# Purpose
# ---------------------------------------------------------------------------


class Purpose(StrEnum):
    """The declared purposes a grant, query or export may serve.

    A closed set on purpose: an open string would let "purpose-bound"
    mean whatever the caller typed, and purpose is one of the nine
    properties `P12-PAM-002` makes jointly mandatory.

    `INVESTIGATION` is the resolution of `OD-P12-02`: rather than a
    separate unrestricted investigative search mode, investigation is a
    *purpose* inside the ordinary scoped search. It narrows like every
    other purpose and expands nothing (`P12-SRCH-011`)."""

    OPERATIONS = "operations"
    INCIDENT_RESPONSE = "incident_response"
    INVESTIGATION = "investigation"
    COMPLIANCE_REVIEW = "compliance_review"
    AUDIT = "audit"
    DATA_SUBJECT_REQUEST = "data_subject_request"
    LEGAL_PROCEEDING = "legal_proceeding"
    STATISTICAL_RELEASE = "statistical_release"
    TRANSPARENCY_PUBLICATION = "transparency_publication"
    SECURITY_ADMINISTRATION = "security_administration"
    SYSTEM_ADMINISTRATION = "system_administration"


@dataclass(frozen=True, slots=True)
class PurposeBinding:
    """The purpose a governed act declares, plus the basis reference the
    policy requires for it where one is required."""

    purpose: Purpose
    justification_reference: str
    basis_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.justification_reference or not self.justification_reference.strip():
            raise JustificationMissingError(
                "a purpose binding requires a non-empty justification reference"
            )

    def assert_admits(self, requested: Purpose) -> None:
        """Purpose may narrow, never widen. An operation whose purpose is
        not the declared one is refused (`P12-PAM-002`)."""
        if requested is not self.purpose:
            raise PrivilegePurposeMismatchError(
                f"operation declares purpose {requested!s}, grant is bound to {self.purpose!s}"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "purpose": str(self.purpose),
            "justification_reference": self.justification_reference,
            "basis_reference": self.basis_reference,
        }


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuthorityReference:
    """A PACK-08 institutional authority assignment, as presented by the
    caller. The service resolves it through the authorization port; a
    `role_code` string alone is never proof of authority
    (`P12-ROLE-017`)."""

    authority_id: UUID
    role_code: str
    scope: OrganizationalScopeRef
    actor_reference: str = ""

    def __post_init__(self) -> None:
        require_text(self.role_code, "role_code")

    def to_payload(self) -> dict[str, object]:
        """The wire form. `actor_reference` is dropped: it is the closest
        thing this service holds to an actor-level identifier, and canon
        20 permits a reference to the acting authority but never the
        identity behind it."""
        return {"authority_id": str(self.authority_id), "role_code": self.role_code}

    def to_state_payload(self) -> dict[str, object]:
        """The hashed form, used only inside audit state snapshots that
        are never transmitted. Covers every field, because an omitted
        field is a field nobody can prove was not changed."""
        return {
            "authority_id": str(self.authority_id),
            "role_code": self.role_code,
            "scope": self.scope.to_payload(),
            "actor_reference": self.actor_reference or None,
        }


@dataclass(frozen=True, slots=True)
class ReasonCoded:
    """A recorded reason for a governed act: the registered code plus the
    authority that invoked it. Free text is not a reason
    (`P12-RSN-002`)."""

    reason_code: str
    authority_reference: str
    note_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.reason_code.strip() or self.reason_code != self.reason_code.upper():
            raise AssignmentNotEffectiveDatedError(
                "reason_code must be a non-empty upper-case registered code"
            )
        require_text(self.authority_reference, "authority_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "reason_code": self.reason_code,
            "authority_reference": self.authority_reference,
            "note_reference": self.note_reference,
        }


# ---------------------------------------------------------------------------
# Effective dating
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EffectiveWindow:
    """The validity window every grant and assignment carries.

    There is no "no end" option, and that is the point: `P12-PAM-003`
    forbids a permanent standing superuser as a designable mode, so an
    unbounded window is not constructible rather than merely
    discouraged."""

    valid_from: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        require_timezone(self.valid_from, context="EffectiveWindow.valid_from")
        require_timezone(self.valid_until, context="EffectiveWindow.valid_until")
        if self.valid_until <= self.valid_from:
            raise StandingAccessProhibitedError("valid_until must be strictly after valid_from")

    @property
    def duration(self) -> timedelta:
        return self.valid_until - self.valid_from

    def covers(self, at: datetime) -> bool:
        require_timezone(at, context="EffectiveWindow.covers")
        return self.valid_from <= at < self.valid_until

    def assert_covers(self, at: datetime) -> None:
        if not self.covers(at):
            raise StandingAccessProhibitedError(
                "the effective window does not cover the requested instant"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat(),
        }


# ---------------------------------------------------------------------------
# Request context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequestContext:
    """What a caller presents with every command.

    Mirrors PACK-09's, PACK-10's and PACK-11's `RequestContext`: the
    caller's own scope, the authorities it asserts, the caller-supplied
    `event_id` that makes the command idempotent, and the correlation
    chain."""

    scope: OrganizationalScopeRef | None
    authorities: tuple[AuthorityReference, ...] = ()
    event_id: UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    declared_purpose: Purpose | None = None
    grant_reference: UUID | None = None
    session_reference: UUID | None = None
    policy_version: str = ""
    evidence_references: tuple[str, ...] = field(default_factory=tuple)

    def require_scope(self) -> OrganizationalScopeRef:
        if self.scope is None:
            raise OrganizationScopeUndeterminedError(
                "organizational scope is undetermined - default deny"
            )
        return self.scope


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------


class RiskClass(StrEnum):
    """How much scrutiny a privileged request needs.

    Drives the required approver count through the versioned policy, so
    that "how many approvers" is a configuration decision recorded once
    rather than a number scattered through the command layer."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


#: Risk classes for which a single approver is never sufficient. Stated
#: here rather than derived, so the rule survives a policy file that
#: forgot it.
DUAL_CONTROL_RISK_CLASSES: frozenset[RiskClass] = frozenset({RiskClass.HIGH, RiskClass.CRITICAL})
