"""Typed references PACK-12 holds at records other packs own, and the
refusals that keep foreign concepts out.

Two directions meet here:

- **Inward.** Typed pointers at PACK-08 scopes and authorities, PACK-09
  record classes, holds and retention, and PACK-11 documents, evidence
  and publication renditions. Every one is an opaque pointer plus the
  minimum typed metadata PACK-12 genuinely needs. None carries the
  referenced record's content, and none carries an assertion about it.
- **Outward.** The references later packs may hold at PACK-12 records.

**There is no voting reference type in this module, and there must never
be one** (`P12-VOTE-002`). A final certified result is reachable only as
`PublicationRenditionRef` - a pointer at an approved rendition the
authoritative voting and result-certification domain produced - and that
type carries no tally, no ballot and no correlation identifier.

Why PACK-12 re-declares PACK-09's and PACK-11's reference shapes instead
of importing them: importing `epd2_compliance_service.references` would
give this service an undeclared dependency on another service package -
its `pyproject.toml` declares `epd2-core` and `epd2-audit-core` and
nothing else - and would make a cross-service *code* edge out of what
must be a typed reference and a published interface. The shapes below are
PACK-12-side mirrors, deliberately structurally identical.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_privileged_access_service.domain import OrganizationalScopeRef, require_text
from epd2_privileged_access_service.exceptions import (
    ExportBallotContentProhibitedError,
    PrivilegedSessionSecretForbiddenError,
)


class ReferenceOwner(StrEnum):
    """Which context owns the record a reference points at.

    A `ClassVar` on each type below rather than a constructor argument:
    an owner a caller could pass in is an owner a caller could get wrong,
    and the whole point of these types is that the boundary is not
    negotiable at the call site."""

    PACK_02_AUDIT = "pack-02-audit"
    PACK_08_ORGANIZATION = "pack-08-organization"
    PACK_09_COMPLIANCE = "pack-09-compliance"
    PACK_11_DOCUMENTS = "pack-11-documents"
    PACK_12_PRIVILEGED = "pack-12-privileged"
    AUTHORITATIVE_VOTING_DOMAIN = "authoritative-voting-domain"


@dataclass(frozen=True, slots=True)
class ForeignRecordReference:
    """The shape every inward reference shares: an opaque external
    reference plus the organizational scope it lives in.

    The identifier is a string, not a `UUID`, because PACK-12 does not
    get to decide the identifier shape of a domain it does not own; the
    scope travels with it because a reference that lost its scope would
    be a reference usable to reach into another organization."""

    owner: ClassVar[ReferenceOwner]

    external_reference: str
    scope: OrganizationalScopeRef

    def __post_init__(self) -> None:
        require_text(self.external_reference, "external_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "owner": str(self.owner),
            "external_reference": self.external_reference,
            "organization_id": str(self.scope.organization_id),
        }


# --- PACK-02 ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuditEventRef(ForeignRecordReference):
    """Points at a PACK-02 `AuditEvent`.

    PACK-12 appends to that chain and reads it. It holds no mutating
    control over `audit-core` (`OD-P12-06`, `P12-ROLE-006`)."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_02_AUDIT


# --- PACK-08 ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrganizationalAuthorityRef(ForeignRecordReference):
    """Points at a PACK-08 `OrganizationalAuthority`. PACK-12 resolves
    authority through the port; it never stores or mints one."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_08_ORGANIZATION


# --- PACK-09 ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RecordClassRef(ForeignRecordReference):
    """Points at PACK-09's record class - the classification that binds a
    record to its retention schedule and disposition authority."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class LegalHoldRef(ForeignRecordReference):
    """Points at a PACK-09 `LegalHold`.

    PACK-12 observes hold state; it never decides it, and a hold is never
    authorization (`P12-EXP-017`)."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE

    hold_state: str = ""

    def __post_init__(self) -> None:
        ForeignRecordReference.__post_init__(self)
        require_text(self.hold_state, "hold_state")

    def to_payload(self) -> dict[str, object]:
        payload = ForeignRecordReference.to_payload(self)
        payload["hold_state"] = self.hold_state
        return payload


@dataclass(frozen=True, slots=True)
class RetentionBindingRef(ForeignRecordReference):
    """Points at the PACK-09 retention binding an export inherits
    (`P12-EXP-016`)."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


# --- PACK-11 ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentRef(ForeignRecordReference):
    """Points at a PACK-11 governed document. Identity only: no bytes, no
    extracted text, no rendition, no signature value."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_11_DOCUMENTS


@dataclass(frozen=True, slots=True)
class EvidenceBundleRef(ForeignRecordReference):
    """Points at a PACK-11 sealed evidence bundle.

    PACK-12 seals session evidence *into* PACK-11's bundles rather than
    defining a parallel evidence store (`P12-SES-005`)."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_11_DOCUMENTS


@dataclass(frozen=True, slots=True)
class PublicationRenditionRef(ForeignRecordReference):
    """Points at an approved publication rendition.

    This is the **only** way a final certified voting result can be
    referenced from PACK-12 (`P12-VOTE-004`). It carries the
    certification and publication decision references so an auditor can
    verify the governed path was followed, and it carries no result
    content, no tally, no ballot-level data and no correlation
    identifier."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_11_DOCUMENTS

    certification_reference: str = ""
    publication_decision_reference: str = ""

    def __post_init__(self) -> None:
        ForeignRecordReference.__post_init__(self)
        require_text(self.certification_reference, "certification_reference")
        require_text(self.publication_decision_reference, "publication_decision_reference")

    def to_payload(self) -> dict[str, object]:
        payload = ForeignRecordReference.to_payload(self)
        payload["certification_reference"] = self.certification_reference
        payload["publication_decision_reference"] = self.publication_decision_reference
        return payload


# --- outward ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScopedRef:
    """Base shape for the references PACK-12 exports to later packs."""

    id: UUID
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class PrivilegedGrantRef(ScopedRef):
    """Points at a `PrivilegedAccessGrant`."""


@dataclass(frozen=True, slots=True)
class PrivilegedSessionRef(ScopedRef):
    """Points at a sealed privileged session."""


@dataclass(frozen=True, slots=True)
class QueryAuditRef(ScopedRef):
    """Points at a `QueryAudit` record.

    PACK-12 owns the typed record and its event semantics; the audit
    chain it appends to remains PACK-02's (`OD-P12-06`)."""


@dataclass(frozen=True, slots=True)
class ExportRequestRef(ScopedRef):
    """Points at a governed export request."""


@dataclass(frozen=True, slots=True)
class ExportArtifactRef(ScopedRef):
    """Points at an export artifact. Not an authoritative record."""


@dataclass(frozen=True, slots=True)
class DisclosureAssessmentRef(ScopedRef):
    """Points at a disclosure-risk assessment."""


# ---------------------------------------------------------------------------
# The boundary, made enforceable
# ---------------------------------------------------------------------------

#: Field names that would amount to voting material. PACK-12 defines no
#: type that can carry one; this set is the backstop for a payload
#: assembled elsewhere (`P12-VOTE-001`, `P12-VOTE-002`).
FORBIDDEN_VOTING_KEYS: frozenset[str] = frozenset(
    {
        "ballot",
        "ballot_id",
        "ballot_content",
        "ballot_reference",
        "vote",
        "vote_id",
        "vote_content",
        "vote_envelope",
        "vote_selection",
        "voter_id",
        "voter_reference",
        "voter_choice",
        "tally",
        "tally_id",
        "partial_tally",
        "intermediate_tally",
        "tally_input",
        "uncertified_tally",
        "eligibility_token",
        "voting_credential",
        "credential_to_ballot",
    }
)

#: Field names that would amount to an assertion PACK-12 may not make
#: about another domain's record.
FORBIDDEN_ASSERTION_KEYS: frozenset[str] = frozenset(
    {
        "is_authentic",
        "is_signed",
        "is_admitted",
        "is_certified",
        "is_final_result",
        "is_publishable",
        "is_legally_valid",
    }
)


def assert_no_voting_material(payload: Mapping[str, object], *, context: str = "") -> None:
    """Raise if a payload carries voting material, or an assertion
    PACK-12 may not make, in any nested position.

    Two different failures, two different reason codes: carrying ballot
    or tally material is `EXPORT_BALLOT_CONTENT_PROHIBITED`; claiming
    that something is certified, authentic or publishable is a claim only
    the owning domain may make, and surfaces as the secret-forbidden
    code because PACK-12 has no registered code for "you asserted
    somebody else's determination" and inventing one here would put an
    unregistered string on a governed refusal."""

    def walk(node: object, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                key_text = str(key).lower()
                where = path or "<root>"
                location = f"{context}: " if context else ""
                if key_text in FORBIDDEN_VOTING_KEYS:
                    raise ExportBallotContentProhibitedError(
                        f"{location}voting key {key!s} at {where} - PACK-12 defines no type "
                        "that may carry ballot-level or tally material"
                    )
                if key_text in FORBIDDEN_ASSERTION_KEYS:
                    raise PrivilegedSessionSecretForbiddenError(
                        f"{location}assertion key {key!s} at {where} - only the owning domain "
                        "may assert authenticity, certification or publishability"
                    )
                walk(value, f"{path}.{key!s}" if path else str(key))
        elif isinstance(node, list | tuple):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload, "")
