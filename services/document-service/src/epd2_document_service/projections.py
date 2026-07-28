"""Restricted and public projections (PACK-11).

Derived, versioned, non-authoritative read models - and the single surface
anything leaves this context through. Nothing here is a source of truth,
nothing here is written back into an aggregate, and every object carries
the provenance a reader needs to answer "what was this derived from, and
is it still current?" without asking the service.

Four rules shape the module.

- **A projection is never authoritative, and cannot be made to look it.**
  `is_authoritative` is a read-only property returning `False`, not a
  field. A field could be constructed `True`; a property cannot, and the
  distinction survives `dataclasses.replace`, deserialisation and every
  future field somebody adds.
- **Emission is one chokepoint.** Every builder runs
  `domain.assert_emission_safe` over its own `to_payload()` output
  *before* returning, so a projection that would leak content, an identity
  attribute or a voting linkage never comes into existence - not even to
  be discarded later by a caller who might forget. PACK-12 can attach DLP
  at exactly one place rather than auditing every call site.
- **Revocation and supersession are visible, never silent.** A public
  projection of a revoked version is a *tombstone*: it states that the
  document was published and that its publication was revoked, and it
  carries neither the content nor the rendition. Removing it entirely
  would be a silent retraction of something the public was already told.
- **Content never appears, in any projection, at any sensitivity.** Not
  the bytes, not extracted text, not a title string. The restricted
  projection is richer than the public one in *metadata* - state,
  provenance kind, review counts, determination status - and identical to
  it in carrying nothing of what the document says. Reading a document's
  content is `application.read_document_content`, an authority-checked,
  access-profile-checked, audited command, not a projection.

## Why the public projection carries a `disclosure_obligation_reference`

This module does not decide what must be published; that is a legal
question. The answer arrives as an obligation reference the caller
supplies and this module refuses to proceed without. `MINIMUM_*` guards
here are floors this code will not go below, not legal thresholds it
claims to know.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_document_service.determinations import (
    AdmissibilityDetermination,
    AdmissibilityStatus,
    SignatureDetermination,
    SignatureStatus,
    absent_admissibility_status,
    absent_signature_status,
)
from epd2_document_service.documents import (
    GovernedDocument,
    PublicationAudience,
    PublicationRendition,
    ReviewRecord,
    RevocationRecord,
    SupersessionRecord,
    unresolved_blocking_reviews,
)
from epd2_document_service.domain import (
    DocumentKind,
    OrganizationalScopeRef,
    SensitivityClass,
    assert_emission_safe,
    require_text,
    require_timezone,
)
from epd2_document_service.evidence import EvidenceBundle
from epd2_document_service.exceptions import (
    DocumentDisclosurePolicyViolationError,
    DocumentFieldInvalidError,
)
from epd2_document_service.versions import (
    PUBLICLY_REPRESENTABLE_STATES,
    DocumentVersion,
    VersionState,
)

#: The projection schema version. Bumped when a projection's shape
#: changes, so a consumer can tell a missing field from an older shape.
PROJECTION_VERSION = "document-projection/v1"


class CurrencyStatus(StrEnum):
    """Whether what a reader is looking at is still the current statement.

    Modelled on FIR-AI-002's `Aktuell / Veraltet / Neue Analyse
    erforderlich` triple and for the same reason: a superseded document
    shown without saying so is a document being presented as current when
    it is not."""

    CURRENT = "current"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"
    NOT_YET_EFFECTIVE = "not_yet_effective"


def currency_for(
    version: DocumentVersion,
    *,
    supersession: SupersessionRecord | None,
    revocation: RevocationRecord | None,
) -> CurrencyStatus:
    """Resolve currency from the governed records, in priority order.

    Revocation outranks supersession: a version that was superseded *and*
    later revoked is revoked, and reporting it as merely superseded would
    tell a reader the newer version replaced it when in fact it was
    withdrawn."""
    if revocation is not None or version.state is VersionState.REVOKED:
        return CurrencyStatus.REVOKED
    if supersession is not None or version.state is VersionState.SUPERSEDED:
        return CurrencyStatus.SUPERSEDED
    if version.state in {VersionState.APPROVED, VersionState.PUBLISHED}:
        return CurrencyStatus.CURRENT
    return CurrencyStatus.NOT_YET_EFFECTIVE


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentProjection:
    """The shape every projection here shares.

    `is_authoritative` is a `ClassVar`-backed property rather than a
    field, so no construction path and no deserialisation can produce a
    projection claiming authority."""

    projection_version: ClassVar[str] = PROJECTION_VERSION

    document_id: UUID
    scope: OrganizationalScopeRef
    generated_at: datetime
    source_version_number: int
    source_version_hash: str
    currency: CurrencyStatus

    def __post_init__(self) -> None:
        require_timezone(self.generated_at, context="projection generated_at")
        require_text(self.source_version_hash, "source_version_hash")
        if self.source_version_number < 1:
            raise DocumentFieldInvalidError("source_version_number must be a positive integer")

    @property
    def is_authoritative(self) -> bool:
        """Always `False`. The authoritative object is the approved
        version in the register; this is one derived view of it."""
        return False

    def _base_payload(self) -> dict[str, object]:
        return {
            "projection_version": self.projection_version,
            "is_authoritative": self.is_authoritative,
            "document_id": str(self.document_id),
            "organization_id": str(self.scope.organization_id),
            "generated_at": self.generated_at.isoformat(),
            "source_version_number": self.source_version_number,
            "source_version_hash": self.source_version_hash,
            "currency": str(self.currency),
        }


# ---------------------------------------------------------------------------
# Restricted projection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class RestrictedDocumentProjection(DocumentProjection):
    """What an authorized internal reader sees about a document.

    Rich in governance metadata and empty of content. `title_reference`
    travels because an authorized reader needs a handle to resolve; the
    title *string* does not, here or anywhere.

    `open_blocking_review_count` rather than the findings themselves: a
    reviewer's finding on a membership appeal is exactly the internal
    deliberation FIR-MEM-001 says the applicant must not see, and a
    projection that carried finding text would have to be re-audited every
    time a new reader class was added. A count answers "is this
    contested?" without answering "with what?"."""

    kind: DocumentKind
    sensitivity: SensitivityClass
    title_reference: str
    document_state: str
    version_state: VersionState
    version_count: int
    head_version_hash: str
    review_count: int
    open_blocking_review_count: int
    signature_status: SignatureStatus
    admissibility_status: AdmissibilityStatus
    has_retention_binding: bool
    active_legal_hold_count: int
    undetermined_legal_hold_count: int
    provenance_kind: str
    rendition_count: int

    def to_payload(self) -> dict[str, object]:
        payload = self._base_payload()
        payload.update(
            {
                "kind": str(self.kind),
                "sensitivity": str(self.sensitivity),
                "title_reference": self.title_reference,
                "document_state": self.document_state,
                "version_state": str(self.version_state),
                "version_count": self.version_count,
                "head_version_hash": self.head_version_hash,
                "review_count": self.review_count,
                "open_blocking_review_count": self.open_blocking_review_count,
                "signature_status": str(self.signature_status),
                "admissibility_status": str(self.admissibility_status),
                "has_retention_binding": self.has_retention_binding,
                "active_legal_hold_count": self.active_legal_hold_count,
                "undetermined_legal_hold_count": self.undetermined_legal_hold_count,
                "provenance_kind": self.provenance_kind,
                "rendition_count": self.rendition_count,
            }
        )
        return payload


def build_restricted_projection(
    document: GovernedDocument,
    version: DocumentVersion,
    *,
    generated_at: datetime,
    reviews: tuple[ReviewRecord, ...] = (),
    signature: SignatureDetermination | None = None,
    admissibility: AdmissibilityDetermination | None = None,
    supersession: SupersessionRecord | None = None,
    revocation: RevocationRecord | None = None,
    rendition_count: int = 0,
) -> RestrictedDocumentProjection:
    """Build and emission-check a restricted projection.

    Determination statuses default to the explicit `not_determined`
    values from `determinations`, never to a plausible-looking
    `not_signed` or `not_admitted`: "nobody has decided" and "somebody
    decided no" are different facts and a reader must be able to tell
    them apart."""
    document.scope.assert_matches(version.scope)
    for_version = tuple(r for r in reviews if r.version_number == version.version_number)
    projection = RestrictedDocumentProjection(
        document_id=document.document_id,
        scope=document.scope,
        generated_at=generated_at,
        source_version_number=version.version_number,
        source_version_hash=version.version_hash,
        currency=currency_for(version, supersession=supersession, revocation=revocation),
        kind=version.kind,
        sensitivity=version.sensitivity,
        title_reference=version.title_reference,
        document_state=str(document.state),
        version_state=version.state,
        version_count=document.version_count,
        head_version_hash=document.head_version_hash,
        review_count=len(for_version),
        open_blocking_review_count=len(unresolved_blocking_reviews(for_version)),
        signature_status=(absent_signature_status() if signature is None else signature.status),
        admissibility_status=(
            absent_admissibility_status() if admissibility is None else admissibility.status
        ),
        has_retention_binding=document.retention is not None,
        active_legal_hold_count=sum(1 for h in document.legal_holds if h.blocks_destruction),
        undetermined_legal_hold_count=sum(1 for h in document.legal_holds if h.is_undetermined),
        provenance_kind=str(version.provenance.kind),
        rendition_count=rendition_count,
    )
    assert_emission_safe(projection.to_payload(), context="restricted document projection")
    return projection


# ---------------------------------------------------------------------------
# Public projection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class PublicDocumentProjection:
    """What the public transparency surface may see.

    A separate type from `RestrictedDocumentProjection` rather than a
    filtered variant of it. A shared type with a "public" flag would mean
    one wrong flag exposes every restricted field at once; two types mean
    the public surface can only be handed something whose every field was
    chosen for it.

    `is_tombstone` marks a revoked publication: the projection exists,
    says a publication was revoked and when, and carries no rendition. It
    is the difference between "we withdrew this" and a document silently
    ceasing to appear."""

    projection_version: ClassVar[str] = PROJECTION_VERSION

    document_id: UUID
    organization_id: UUID
    generated_at: datetime
    kind: DocumentKind
    published_version_number: int
    published_version_hash: str
    audience: PublicationAudience
    disclosure_obligation_reference: str
    currency: CurrencyStatus
    published_at: datetime
    citation_reference: str | None = None
    rendition_media_type: str | None = None
    superseded_by_version_number: int | None = None
    revoked_at: datetime | None = None
    revocation_reason_code: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.generated_at, context="public projection generated_at")
        require_timezone(self.published_at, context="public projection published_at")
        require_text(self.disclosure_obligation_reference, "disclosure_obligation_reference")
        require_text(self.published_version_hash, "published_version_hash")
        if self.published_version_number < 1:
            raise DocumentFieldInvalidError("published_version_number must be positive")
        if self.currency is CurrencyStatus.REVOKED:
            if self.revoked_at is None or self.revocation_reason_code is None:
                raise DocumentDisclosurePolicyViolationError(
                    "a revoked public projection must state when the revocation happened and "
                    "under which reason code - an unexplained disappearance is a silent "
                    "retraction"
                )
            if self.citation_reference is not None:
                raise DocumentDisclosurePolicyViolationError(
                    "a revoked publication must not continue to offer a citable rendition"
                )
        if self.revoked_at is not None:
            require_timezone(self.revoked_at, context="public projection revoked_at")

    @property
    def is_authoritative(self) -> bool:
        return False

    @property
    def is_tombstone(self) -> bool:
        return self.currency is CurrencyStatus.REVOKED

    def to_payload(self) -> dict[str, object]:
        return {
            "projection_version": self.projection_version,
            "is_authoritative": self.is_authoritative,
            "is_tombstone": self.is_tombstone,
            "document_id": str(self.document_id),
            "organization_id": str(self.organization_id),
            "generated_at": self.generated_at.isoformat(),
            "kind": str(self.kind),
            "published_version_number": self.published_version_number,
            "published_version_hash": self.published_version_hash,
            "audience": str(self.audience),
            "disclosure_obligation_reference": self.disclosure_obligation_reference,
            "currency": str(self.currency),
            "published_at": self.published_at.isoformat(),
            "citation_reference": self.citation_reference,
            "rendition_media_type": self.rendition_media_type,
            "superseded_by_version_number": self.superseded_by_version_number,
            "revoked_at": None if self.revoked_at is None else self.revoked_at.isoformat(),
            "revocation_reason_code": self.revocation_reason_code,
        }


def build_public_projection(
    document: GovernedDocument,
    version: DocumentVersion,
    *,
    generated_at: datetime,
    published_at: datetime,
    audience: PublicationAudience,
    disclosure_obligation_reference: str,
    rendition: PublicationRendition | None = None,
    supersession: SupersessionRecord | None = None,
    revocation: RevocationRecord | None = None,
) -> PublicDocumentProjection:
    """Build and emission-check a public projection.

    Three refusals before anything is built, each closing a different way
    unpublished material reaches the public surface:

    1. a version in a state the public may never see (`draft`,
       `in_review`, `returned_for_revision`, `approved`-but-unpublished);
    2. an audience other than `PUBLIC` - "published to members" is a real
       publication and is not this surface;
    3. a restricted-classification version, which cannot become public by
       being published to a public audience. The classification is a
       property of the content; publishing does not change it, and a
       publication decision that appears to would be a reclassification
       nobody recorded."""
    if version.state not in PUBLICLY_REPRESENTABLE_STATES:
        raise DocumentDisclosurePolicyViolationError(
            f"a version in state {version.state.value!r} may not appear in a public projection"
        )
    if audience is not PublicationAudience.PUBLIC:
        raise DocumentDisclosurePolicyViolationError(
            f"a publication to audience {audience.value!r} does not belong on the public "
            "transparency surface"
        )
    if version.sensitivity is SensitivityClass.RESTRICTED:
        raise DocumentDisclosurePolicyViolationError(
            "a version classified 'restricted' may not be projected publicly; publication "
            "does not reclassify content"
        )

    currency = currency_for(version, supersession=supersession, revocation=revocation)
    is_revoked = currency is CurrencyStatus.REVOKED
    projection = PublicDocumentProjection(
        document_id=document.document_id,
        organization_id=document.scope.organization_id,
        generated_at=generated_at,
        kind=version.kind,
        published_version_number=version.version_number,
        published_version_hash=version.version_hash,
        audience=audience,
        disclosure_obligation_reference=disclosure_obligation_reference,
        currency=currency,
        published_at=published_at,
        citation_reference=(
            None if is_revoked or rendition is None else rendition.citation_reference
        ),
        rendition_media_type=(None if is_revoked or rendition is None else rendition.media_type),
        superseded_by_version_number=(
            None if supersession is None else supersession.superseding_version_number
        ),
        revoked_at=None if revocation is None else revocation.revoked_at,
        revocation_reason_code=(None if revocation is None else revocation.reason.reason_code),
    )
    assert_emission_safe(projection.to_payload(), context="public document projection")
    return projection


# ---------------------------------------------------------------------------
# Evidence bundle projection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceBundleProjection:
    """A citable summary of a sealed bundle for a consuming pack.

    Carries the digest and the item count so a citation is checkable, and
    the per-item version references so a consumer can verify each one -
    but no provenance, no custody and no matter substance. A PACK-09 case
    citing a bundle needs to know *which* material; who held it and where
    it came from stays here, behind an authorized read."""

    projection_version: ClassVar[str] = PROJECTION_VERSION

    bundle_id: UUID
    organization_id: UUID
    generated_at: datetime
    citation_reference: str
    bundle_digest: str
    item_count: int
    item_references: tuple[str, ...]
    sealed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.generated_at, context="bundle projection generated_at")
        require_timezone(self.sealed_at, context="bundle projection sealed_at")
        require_text(self.citation_reference, "citation_reference")
        require_text(self.bundle_digest, "bundle_digest")
        if self.item_count != len(self.item_references):
            raise DocumentFieldInvalidError(
                "item_count must equal the number of item references - a mismatch would let a "
                "bundle look larger or smaller than what it cites"
            )

    @property
    def is_authoritative(self) -> bool:
        return False

    def to_payload(self) -> dict[str, object]:
        return {
            "projection_version": self.projection_version,
            "is_authoritative": self.is_authoritative,
            "bundle_id": str(self.bundle_id),
            "organization_id": str(self.organization_id),
            "generated_at": self.generated_at.isoformat(),
            "citation_reference": self.citation_reference,
            "bundle_digest": self.bundle_digest,
            "item_count": self.item_count,
            "item_references": list(self.item_references),
            "sealed_at": self.sealed_at.isoformat(),
        }


def build_evidence_bundle_projection(
    bundle: EvidenceBundle, *, generated_at: datetime
) -> EvidenceBundleProjection:
    """Build and emission-check a bundle projection.

    Verifies the seal first. Projecting a bundle whose digest no longer
    matches its items would publish a citation to material that changed
    after it was sealed, which is the one thing a sealed bundle is
    supposed to make impossible."""
    bundle.verify_seal()
    citation = bundle.citation_reference
    if citation is None or bundle.bundle_digest is None or bundle.sealed_at is None:
        raise DocumentFieldInvalidError("an unsealed bundle has no citable projection")
    projection = EvidenceBundleProjection(
        bundle_id=bundle.bundle_id,
        organization_id=bundle.scope.organization_id,
        generated_at=generated_at,
        citation_reference=citation,
        bundle_digest=bundle.bundle_digest,
        item_count=len(bundle.items),
        item_references=tuple(
            f"epd2-doc:{item.document_id}:v{item.version_number}" for item in bundle.items
        ),
        sealed_at=bundle.sealed_at,
    )
    assert_emission_safe(projection.to_payload(), context="evidence bundle projection")
    return projection
