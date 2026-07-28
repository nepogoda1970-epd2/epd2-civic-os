"""Governed determinations about documents (PACK-11; ADR-053, ADR-059).

ADR-053 fixed four interface requirements that PACK-10 would consume once
PACK-11 existed, and recorded that until all four exist, PACK-10 "records
the reference and the absence of the assertion - it does not simulate any
of the four with a local heuristic". This module is where three of those
four are answered, and `documents.PublicationRendition` is the fourth:

1. **resolve a reference to a document's existence and kind within an
   organizational scope** - `DocumentResolution`, produced by
   `application.resolve_document_reference`;
2. **report a signature or signed-original status as a governed
   determination, not an inferred one** - `SignatureDetermination`;
3. **report an admissibility determination** - `AdmissibilityDetermination`;
4. **produce a publication rendition identifier that a public view can
   cite without exposing document content** -
   `documents.PublicationRendition.citation_reference`.

## The one design rule this module exists to enforce

**A determination is recorded, never computed.** There is no function here
that inspects a file and concludes "this is signed". Every determination
carries the authority that made it, the moment it was made, the exact
version hash it examined and a registered reason code. Where no
determination exists, the answer is `absent` with its own reason code -
never a default, never an inference, never a heuristic.

That is not caution for its own sake. A signature check is a
cryptographic, PKI-dependent and jurisdiction-dependent judgement; an
admissibility determination is a legal one. A service that guessed either
would produce an answer that *looks* authoritative to every consumer
downstream, and consumers do not re-derive what an authoritative source
already told them. The wrong answer would then propagate exactly as far as
the right one.

## Staleness is structural

Every determination stores `determined_version_hash`. `assert_current`
compares it with the version as stored, and a mismatch raises
`DocumentDeterminationStaleError` rather than returning a slightly-wrong
answer. A determination therefore cannot travel forward onto a version it
never examined - which is the same rule FIR-AI-002 states for AI analyses
and FIR-PROG-002 states for pre-adoption opinions, applied here to the two
determinations this context owns.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_document_service.domain import (
    AuthorityReference,
    DocumentKind,
    OrganizationalScopeRef,
    ReasonCoded,
    require_digest,
    require_text,
    require_timezone,
)
from epd2_document_service.exceptions import (
    DocumentDeterminationMissingError,
    DocumentDeterminationNotPermittedError,
    DocumentDeterminationStaleError,
    DocumentFieldInvalidError,
)
from epd2_document_service.versions import DocumentVersion

# ---------------------------------------------------------------------------
# 1. Reference resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentResolution:
    """ADR-053 requirement 1: existence and kind within a scope.

    Note what is *not* here: no title text, no content, no author, no
    review state and no assertion of any kind. A consumer resolving a
    reference is asking "does this exist, in my scope, and what kind of
    thing is it?" - and every additional field would be an answer to a
    question it did not ask, exported across a bounded-context boundary
    where it becomes a second source of truth.

    `exists = False` is a normal, returnable answer. The alternative -
    raising - would let a consumer distinguish "not in your scope" from
    "does not exist" by catching two different exceptions, which is
    exactly the probing oracle `application`'s two-tier scope errors are
    built to deny."""

    reference: str
    scope: OrganizationalScopeRef
    exists: bool
    kind: DocumentKind | None = None
    current_version_number: int | None = None
    is_revoked: bool = False

    def __post_init__(self) -> None:
        require_text(self.reference, "reference")
        if self.exists and self.kind is None:
            raise DocumentFieldInvalidError("a resolved document must report its kind")
        if not self.exists and self.kind is not None:
            raise DocumentFieldInvalidError(
                "an unresolved reference must not report a kind - it would confirm the "
                "existence the resolution just denied"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "reference": self.reference,
            "organization_id": str(self.scope.organization_id),
            "exists": self.exists,
            "kind": None if self.kind is None else str(self.kind),
            "current_version_number": self.current_version_number,
            "is_revoked": self.is_revoked,
        }


# ---------------------------------------------------------------------------
# 2. Signature status
# ---------------------------------------------------------------------------


class SignatureStatus(StrEnum):
    """The governed answer to "is this a signed original?".

    `NOT_DETERMINED` is the default a consumer gets when nobody has made
    the determination, and it is a first-class value rather than an
    absence: a consumer that receives it knows it must fail closed, while
    a consumer that received `None` might read it as `NOT_SIGNED`.

    `SIGNED_UNVERIFIED` is the honest answer for material that carries a
    signature this platform cannot validate - an ink signature on a
    scanned page, or a certificate chain no configured trust anchor
    covers. Collapsing it into either `SIGNED` or `NOT_SIGNED` would be
    this service inventing the verification it just said it could not
    perform."""

    NOT_DETERMINED = "not_determined"
    NOT_SIGNED = "not_signed"
    SIGNED_UNVERIFIED = "signed_unverified"
    SIGNED_VERIFIED = "signed_verified"
    SIGNATURE_INVALID = "signature_invalid"


class SignatureForm(StrEnum):
    """What kind of signature the determination concerns.

    Named because the legal weight differs sharply between them and a
    consumer that only learned "signed" would flatten that difference.
    This service records which form was determined; it does not rank
    them, because ranking is jurisdiction-dependent law."""

    HANDWRITTEN_ON_PAPER = "handwritten_on_paper"
    SCANNED_HANDWRITTEN = "scanned_handwritten"
    SIMPLE_ELECTRONIC = "simple_electronic"
    ADVANCED_ELECTRONIC = "advanced_electronic"
    QUALIFIED_ELECTRONIC = "qualified_electronic"
    ORGANIZATIONAL_SEAL = "organizational_seal"


@dataclass(frozen=True, slots=True)
class SignatureDetermination:
    """ADR-053 requirement 2: a *recorded* signature determination.

    `verification_basis_reference` points at whatever the determiner
    relied on - a validation report, a notarial certificate, a witnessed
    inspection. This service stores the pointer and never the reasoning:
    restating somebody else's verification in this service's own words
    would create a second version of it that can disagree with the
    original."""

    determination_id: UUID
    scope: OrganizationalScopeRef
    document_id: UUID
    version_number: int
    determined_version_hash: str
    status: SignatureStatus
    determined_at: datetime
    determined_by: AuthorityReference
    reason: ReasonCoded
    form: SignatureForm | None = None
    verification_basis_reference: str | None = None
    signatory_role_reference: str | None = None

    def __post_init__(self) -> None:
        require_digest(self.determined_version_hash, "determined_version_hash")
        require_timezone(self.determined_at, context="SignatureDetermination.determined_at")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")
        if self.status is SignatureStatus.NOT_DETERMINED:
            raise DocumentFieldInvalidError(
                "a recorded determination cannot have status 'not_determined' - that value is "
                "what a consumer receives when no determination exists"
            )
        if (
            self.status in {SignatureStatus.SIGNED_VERIFIED, SignatureStatus.SIGNATURE_INVALID}
            and not self.verification_basis_reference
        ):
            raise DocumentFieldInvalidError(
                f"status {self.status.value!r} asserts that a verification was performed and "
                "must reference what it relied on"
            )
        if self.status is not SignatureStatus.NOT_SIGNED and self.form is None:
            raise DocumentFieldInvalidError(
                "a determination that material is signed must record which signature form"
            )
        if self.signatory_role_reference is not None:
            require_text(self.signatory_role_reference, "signatory_role_reference")

    @property
    def is_signed_original(self) -> bool:
        """The single boolean a consumer may read off this record.

        Deliberately narrow: only a *verified* signature counts. A
        consumer that wanted the looser reading has the full `status` and
        must decide for itself, in the open, rather than inheriting a
        loose default from here."""
        return self.status is SignatureStatus.SIGNED_VERIFIED

    def to_payload(self) -> dict[str, object]:
        return {
            "determination_id": str(self.determination_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "determined_version_hash": self.determined_version_hash,
            "signature_status": str(self.status),
            "signature_form": None if self.form is None else str(self.form),
            "determined_at": self.determined_at.isoformat(),
            "determined_by": self.determined_by.to_payload(),
            "verification_basis_reference": self.verification_basis_reference,
            "signatory_role_reference": self.signatory_role_reference,
            "reason": self.reason.to_payload(),
        }


# ---------------------------------------------------------------------------
# 3. Admissibility
# ---------------------------------------------------------------------------


class AdmissibilityStatus(StrEnum):
    """The governed answer to "may this be relied on in this procedure?".

    `NOT_DETERMINED` is again the consumer-facing absence value.
    `ADMITTED_WITH_LIMITATION` exists because the realistic outcome of a
    contested evidence question is rarely a clean yes: material may be
    admitted for one purpose and not another, and a two-valued
    determination would force that nuance into whichever of the two
    answers happened to be closer."""

    NOT_DETERMINED = "not_determined"
    ADMITTED = "admitted"
    ADMITTED_WITH_LIMITATION = "admitted_with_limitation"
    NOT_ADMITTED = "not_admitted"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class AdmissibilityDetermination:
    """ADR-053 requirement 3: a *recorded* admissibility determination.

    Bound to a `procedure_reference`: admissibility is never a property of
    a document in the abstract, it is a decision about a document *in a
    procedure*. A determination with no procedure would be a general
    licence, which is not a thing any body has the power to issue.

    The determination is made by a `LEGAL_REVIEWER` authority (see
    `authorization.ACTION_REQUIREMENTS`). This service records who decided
    and under which reason code; it makes no legal judgement of its own
    and none of its outputs may be read as one."""

    determination_id: UUID
    scope: OrganizationalScopeRef
    document_id: UUID
    version_number: int
    determined_version_hash: str
    procedure_reference: str
    status: AdmissibilityStatus
    determined_at: datetime
    determined_by: AuthorityReference
    reason: ReasonCoded
    limitation_reference: str | None = None
    evidence_bundle_reference: str | None = None

    def __post_init__(self) -> None:
        require_digest(self.determined_version_hash, "determined_version_hash")
        require_text(self.procedure_reference, "procedure_reference")
        require_timezone(self.determined_at, context="AdmissibilityDetermination.determined_at")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")
        if self.status is AdmissibilityStatus.NOT_DETERMINED:
            raise DocumentFieldInvalidError(
                "a recorded determination cannot have status 'not_determined'"
            )
        if (
            self.status is AdmissibilityStatus.ADMITTED_WITH_LIMITATION
            and not self.limitation_reference
        ):
            raise DocumentFieldInvalidError(
                "an admission with limitation must reference the limitation - an unstated "
                "limitation is no limitation"
            )

    @property
    def permits_reliance(self) -> bool:
        """Whether a consumer may rely on this material in this procedure.

        `ADMITTED_WITH_LIMITATION` returns `True` and the consumer is
        expected to read `limitation_reference`. Returning `False` would
        be safer-looking and wrong: it would suppress material a competent
        body admitted."""
        return self.status in {
            AdmissibilityStatus.ADMITTED,
            AdmissibilityStatus.ADMITTED_WITH_LIMITATION,
        }

    def to_payload(self) -> dict[str, object]:
        return {
            "determination_id": str(self.determination_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "determined_version_hash": self.determined_version_hash,
            "procedure_reference": self.procedure_reference,
            "admissibility_status": str(self.status),
            "determined_at": self.determined_at.isoformat(),
            "determined_by": self.determined_by.to_payload(),
            "limitation_reference": self.limitation_reference,
            "evidence_bundle_reference": self.evidence_bundle_reference,
            "reason": self.reason.to_payload(),
        }


# ---------------------------------------------------------------------------
# Currency and absence
# ---------------------------------------------------------------------------


def assert_determination_current(
    determination: SignatureDetermination | AdmissibilityDetermination,
    version: DocumentVersion,
) -> None:
    """Raise unless the determination examined this exact stored version.

    Both fields are checked. Comparing only the version *number* would
    pass for a version whose record was altered; comparing only the *hash*
    would pass for a determination copied onto a different version that
    happens to hash the same, which cannot occur but costs nothing to
    exclude."""
    if determination.document_id != version.document_id:
        raise DocumentDeterminationStaleError(
            "the determination concerns a different document"
        )
    if determination.version_number != version.version_number:
        raise DocumentDeterminationStaleError(
            f"the determination was made against version {determination.version_number}, but "
            f"version {version.version_number} was presented"
        )
    if determination.determined_version_hash != version.version_hash:
        raise DocumentDeterminationStaleError(
            "the determination was made against a different state of this version - it does "
            "not carry forward to the version as stored"
        )


def require_signature_determination(
    determination: SignatureDetermination | None, version: DocumentVersion
) -> SignatureDetermination:
    """Return a current signature determination, or refuse.

    The shape ADR-053 asked for: a consumer that needs the assertion gets
    it or gets a reason-coded refusal, and never gets a guess."""
    if determination is None:
        raise DocumentDeterminationMissingError(
            f"no signature determination exists for version {version.version_number} of "
            f"document {version.document_id}; this service does not infer one"
        )
    assert_determination_current(determination, version)
    return determination


def require_admissibility_determination(
    determination: AdmissibilityDetermination | None,
    version: DocumentVersion,
    *,
    procedure_reference: str,
) -> AdmissibilityDetermination:
    """Return a current admissibility determination for this procedure, or
    refuse.

    The procedure is checked as well as the version: an admission in one
    procedure says nothing about another, and silently reusing it would be
    this service extending a body's decision beyond what that body
    decided."""
    if determination is None:
        raise DocumentDeterminationMissingError(
            f"no admissibility determination exists for version {version.version_number} of "
            f"document {version.document_id} in procedure {procedure_reference!r}"
        )
    assert_determination_current(determination, version)
    if determination.procedure_reference != procedure_reference:
        raise DocumentDeterminationNotPermittedError(
            f"the admissibility determination on file concerns procedure "
            f"{determination.procedure_reference!r}, not {procedure_reference!r}"
        )
    return determination


def absent_signature_status() -> SignatureStatus:
    """The value a consumer receives when nothing has been determined.

    A function rather than a bare constant so that every consumer-facing
    absence goes through one named place, and so the choice is greppable
    when a later round revisits it."""
    return SignatureStatus.NOT_DETERMINED


def absent_admissibility_status() -> AdmissibilityStatus:
    """The value a consumer receives when nothing has been determined."""
    return AdmissibilityStatus.NOT_DETERMINED
