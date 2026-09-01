"""Typed references PACK-11 exports, and the ones it consumes (PACK-11;
ADR-053, ADR-060).

Two directions meet in one module, and conflating them is the mistake this
docstring exists to prevent.

- **Outward-facing.** The stable references *other* packs hold at material
  this context owns: `DocumentRef`, `DocumentVersionRef`, `EvidenceRef`,
  `EvidenceBundleRef`, `PublicationRenditionRef`,
  `SignatureDeterminationRef`, `AdmissibilityDeterminationRef`. These are
  what PACK-09's `references.DocumentRef`/`EvidenceRef`/`MinutesRef`
  placeholders and PACK-10's `references.DocumentReference` /
  `domain.EvidenceReference` placeholders were placeholders *for*. Every
  one is an identifier plus the organizational scope, and no content.
- **Inward-facing.** The typed pointers this context holds at records
  other contexts own - a PACK-08 organizational scope, a PACK-09 record
  class, legal hold, legal case and destruction authorization. Same shape,
  opposite direction: an identifier plus the minimum typed metadata, never
  the referenced record's content and never an assertion about it.

## Why PACK-11 re-declares PACK-09's reference types instead of importing

`services/document-service/pyproject.toml` declares `epd2-core` and
`epd2-audit-core` and nothing else, exactly as `finance-service`'s does.
Importing `epd2_compliance_service.references` would give this service an
undeclared dependency on another service package and turn what canon
19f.22 says must be "a typed reference and a published interface" into a
cross-service *code* edge. The shapes below are therefore PACK-11-side
mirrors, deliberately structurally identical to PACK-09's `ScopedRef` and
`PlaceholderRef`, carrying PACK-09's identifiers exactly as PACK-10's
`references` module already does. `tests/repository/test_service_boundaries.py`
enforces the import restriction; this docstring records why the
duplication is the intended shape rather than an oversight.

## The one asymmetry with PACK-10's mirror module, and why

PACK-10's `DocumentReference` deliberately has **no** `is_authentic`,
`is_signed`, `is_admitted`, `is_valid` or `is_publishable` field, because
PACK-10 may not assert any of those. PACK-11 may - it is the pack canon
19f.22 names as the owner of exactly those determinations - but it still
does not put them on a *reference*. They live on
`determinations.SignatureDetermination` and
`determinations.AdmissibilityDetermination`, as separate, authority-bound,
version-bound, reason-coded records, and a consumer that wants one asks
for the determination rather than reading a boolean off a pointer. A
reference stays a reference in both directions; the difference between the
packs is who may produce the determination, not whether a pointer may
carry it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_document_service.domain import (
    DocumentKind,
    OrganizationalScopeRef,
    require_reference,
)
from epd2_document_service.exceptions import DocumentReferenceKindMismatchError

# ---------------------------------------------------------------------------
# Outward: what other packs hold at this context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScopedRef:
    """The base shape every outward reference shares: an identifier plus
    the organization the referenced object lives in.

    Mirrors PACK-09's `ScopedRef` exactly. Subclasses add nothing but
    their own name - and the name matters: a `DocumentRef` and an
    `EvidenceRef` are not interchangeable even though both are
    `(UUID, UUID)` pairs, and mypy enforces that at every call site."""

    id: UUID
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class DocumentRef(ScopedRef):
    """Points at a `documents.GovernedDocument`.

    This is what PACK-09's placeholder `DocumentRef` and PACK-10's
    `DocumentReference` were holding a place for. Consumed by PACK-09
    (documents attached to a case, filing or hearing), PACK-10 (finance
    evidence), and the later packs the master register names: PACK-19
    candidacy, PACK-21 assemblies and minutes, PACK-22 correspondence."""


@dataclass(frozen=True, slots=True)
class DocumentVersionRef(ScopedRef):
    """Points at one exact, immutable `versions.DocumentVersion`.

    Carries the version number and hash as well as the id, because a
    reference to "the document" is a moving target and a reference to
    "the document as it was" is not. The hash is what lets a consumer
    check, later and independently, that the version it is looking at is
    the version it was pointed at."""

    version_number: int = 0
    version_hash: str = ""

    def __post_init__(self) -> None:
        if self.version_number < 1:
            raise DocumentReferenceKindMismatchError(
                "a document version reference must carry a positive version number"
            )
        require_reference(self.version_hash, "version_hash")


@dataclass(frozen=True, slots=True)
class EvidenceRef(ScopedRef):
    """Points at an `evidence.EvidenceRecord`.

    PACK-09's own `EvidenceRef` placeholder docstring names what a later
    admissibility decision needs: "provenance, integrity, custody,
    relevance decision and preserved version". The first three and the
    last are held behind this reference; the relevance decision is
    PACK-09's, and PACK-11 records it as an
    `AdmissibilityDetermination` without making it."""


@dataclass(frozen=True, slots=True)
class EvidenceBundleRef(ScopedRef):
    """Points at a sealed `evidence.EvidenceBundle`.

    Carries the bundle digest so a citation is checkable without a round
    trip: a consumer holding this reference can be handed the bundle's
    items later and verify that they are the ones the seal covered."""

    bundle_digest: str = ""

    def __post_init__(self) -> None:
        require_reference(self.bundle_digest, "bundle_digest")


@dataclass(frozen=True, slots=True)
class PublicationRenditionRef(ScopedRef):
    """Points at a `documents.PublicationRendition`.

    ADR-053's fourth interface requirement, in reference form: a public
    view cites this and gets existence, audience and media type - never
    content."""

    citation_reference: str = ""

    def __post_init__(self) -> None:
        require_reference(self.citation_reference, "citation_reference")


@dataclass(frozen=True, slots=True)
class SignatureDeterminationRef(ScopedRef):
    """Points at a `determinations.SignatureDetermination`.

    ADR-053's second interface requirement, in reference form. Note that
    it carries no status: a consumer that wants the answer resolves the
    determination and gets its version binding and staleness check with
    it. A status on the reference would be a cached answer that outlives
    the version it was true of."""


@dataclass(frozen=True, slots=True)
class AdmissibilityDeterminationRef(ScopedRef):
    """Points at a `determinations.AdmissibilityDetermination`.

    ADR-053's third interface requirement, in reference form. Same rule as
    above, plus one: admissibility is procedure-bound, so a cached status
    would also outlive the procedure it was decided in."""


# ---------------------------------------------------------------------------
# Inward: what this context holds at other packs
# ---------------------------------------------------------------------------


class ReferenceOwner(StrEnum):
    """Which context owns the record an inward reference points at.

    A `ClassVar` on each type below rather than a constructor argument: an
    owner a caller could pass in is an owner a caller could get wrong, and
    the whole point of these types is that the boundary is not negotiable
    at the call site."""

    PACK_08_ORGANIZATION = "pack-08-organization"
    PACK_09_COMPLIANCE = "pack-09-compliance"
    PACK_10_FINANCE = "pack-10-finance"
    PACK_11_DOCUMENTS = "pack-11-documents"


@dataclass(frozen=True, slots=True)
class ForeignRecordReference:
    """The shape every inward reference shares: an opaque external
    reference plus the organizational scope it lives in.

    The identifier is a string and not a `UUID` because PACK-11 does not
    get to decide the identifier shape of a domain it does not own, and
    the scope travels with it because a reference that lost its scope
    would be a reference usable to reach into another organization.

    `owner` is an unassigned `ClassVar` here: this base is never
    instantiated directly, and a subclass that forgot to declare its owner
    fails on attribute access rather than silently claiming PACK-11's."""

    owner: ClassVar[ReferenceOwner]

    external_reference: str
    scope: OrganizationalScopeRef

    def __post_init__(self) -> None:
        require_reference(self.external_reference, "external_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "owner": str(self.owner),
            "external_reference": self.external_reference,
            "organization_id": str(self.scope.organization_id),
        }


@dataclass(frozen=True, slots=True)
class OrganizationScopeReference(ForeignRecordReference):
    """A PACK-08 organizational scope, referenced as a foreign record."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_08_ORGANIZATION


@dataclass(frozen=True, slots=True)
class RecordClassReference(ForeignRecordReference):
    """A PACK-09 record class - the classification that binds material to
    its retention schedule, custodian and disposition authority.

    PACK-11 stores this and never interprets it: the schedule, the
    trigger and the disposition action stay PACK-09's."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class LegalHoldReference(ForeignRecordReference):
    """A PACK-09 legal hold.

    Held as a reference and re-read before every destruction-relevant act
    rather than cached as a state, because a hold's state is PACK-09's
    answer and a cached copy is a second, stale one."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class LegalCaseReference(ForeignRecordReference):
    """A PACK-09 legal case a document or evidence bundle belongs to.

    Holding this reference makes the document *about* the case; it does
    not make PACK-11 a participant in the case, and nothing here may
    assert a procedural fact about it."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class DestructionAuthorizationReference(ForeignRecordReference):
    """A PACK-09 destruction authorization.

    The only thing that can permit a disposition here. PACK-11 never
    authorizes its own disposals, which is why this is an inward
    reference and not a locally-constructed decision."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class FinanceRecordReference(ForeignRecordReference):
    """A PACK-10 finance record a piece of finance evidence belongs to.

    The mirror image of PACK-10's `EvidenceReference`: PACK-10 points at
    the document, this points back at the finance record, and neither
    holds the other's content. Both directions exist because "which
    finance record is this invoice evidence for?" and "which invoice
    evidences this finance record?" are asked by different services."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_10_FINANCE


# ---------------------------------------------------------------------------
# The consumer-facing kind vocabulary
# ---------------------------------------------------------------------------


def assert_reference_kind(reference_kind: str, expected: DocumentKind, *, context: str) -> None:
    """Raise unless a consumer-supplied kind string names `expected`.

    Consumers hold `kind` as an open string (PACK-09's and PACK-10's
    placeholders both do). This is the one place that open string is
    checked against this context's closed taxonomy, so a consumer that
    asks for "the legal opinion" and is handed a SEPA mandate finds out
    here rather than three services later."""
    if reference_kind != str(expected):
        raise DocumentReferenceKindMismatchError(
            f"{context}: expected a reference of kind {str(expected)!r}, got {reference_kind!r}"
        )


def document_citation(document_id: UUID, version_number: int) -> str:
    """The canonical opaque citation string for a document version.

    One format, produced in one place, so every consumer that stores a
    citation stores the same shape and a future parser has exactly one
    grammar to handle."""
    return f"epd2-doc:{document_id}:v{version_number}"
