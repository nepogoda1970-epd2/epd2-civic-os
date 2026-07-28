"""The typed references this context exports and consumes (ADR-053,
ADR-060).

These are the shapes PACK-09's `DocumentRef`/`EvidenceRef`/`MinutesRef`
placeholders and PACK-10's `DocumentReference` /
`domain.EvidenceReference` placeholders were placeholders *for*. The tests
below hold the boundary: a reference carries identity and scope, never
content, and never an assertion.
"""

from __future__ import annotations

from dataclasses import fields
from uuid import uuid4

import pytest
from _builders import scope

from epd2_document_service.domain import DocumentKind, content_digest_of
from epd2_document_service.exceptions import (
    DocumentReferenceInvalidError,
    DocumentReferenceKindMismatchError,
)
from epd2_document_service.references import (
    AdmissibilityDeterminationRef,
    DestructionAuthorizationReference,
    DocumentRef,
    DocumentVersionRef,
    EvidenceBundleRef,
    EvidenceRef,
    FinanceRecordReference,
    ForeignRecordReference,
    LegalCaseReference,
    LegalHoldReference,
    OrganizationScopeReference,
    PublicationRenditionRef,
    RecordClassReference,
    ReferenceOwner,
    ScopedRef,
    SignatureDeterminationRef,
    assert_reference_kind,
    document_citation,
)

#: Every outward reference type. Kept as one list so the boundary tests
#: below cannot silently miss a type somebody adds later.
OUTWARD_TYPES = (
    DocumentRef,
    DocumentVersionRef,
    EvidenceRef,
    EvidenceBundleRef,
    PublicationRenditionRef,
    SignatureDeterminationRef,
    AdmissibilityDeterminationRef,
)

INWARD_TYPES = (
    OrganizationScopeReference,
    RecordClassReference,
    LegalHoldReference,
    LegalCaseReference,
    DestructionAuthorizationReference,
    FinanceRecordReference,
)

#: Field names that would turn a reference into a carrier of content or of
#: an assertion. PACK-11 *may* make signature and admissibility
#: determinations - it is the pack canon 19f.22 names as their owner - but
#: it still does not put them on a pointer: they live on their own
#: authority-bound, version-bound, reason-coded records.
FORBIDDEN_REFERENCE_FIELDS = frozenset(
    {
        "content",
        "bytes",
        "text",
        "body",
        "title",
        "extracted_text",
        "is_authentic",
        "is_signed",
        "is_admitted",
        "is_valid",
        "is_publishable",
        "signature_status",
        "admissibility_status",
        "status",
    }
)


# ---------------------------------------------------------------------------
# The boundary itself
# ---------------------------------------------------------------------------


def test_no_outward_reference_carries_content_or_an_assertion() -> None:
    offenders: list[str] = []
    for reference_type in OUTWARD_TYPES:
        for field in fields(reference_type):
            if field.name in FORBIDDEN_REFERENCE_FIELDS:
                offenders.append(f"{reference_type.__name__}.{field.name}")
    assert offenders == [], offenders


def test_no_inward_reference_carries_content_or_an_assertion() -> None:
    offenders: list[str] = []
    for reference_type in INWARD_TYPES:
        for field in fields(reference_type):
            if field.name in FORBIDDEN_REFERENCE_FIELDS:
                offenders.append(f"{reference_type.__name__}.{field.name}")
    assert offenders == [], offenders


def test_every_outward_reference_carries_its_scope() -> None:
    """A reference that lost its scope would be usable to reach into
    another organization."""
    for reference_type in OUTWARD_TYPES:
        names = {field.name for field in fields(reference_type)}
        assert "organization_id" in names, reference_type.__name__


def test_every_inward_reference_carries_its_scope_and_owner() -> None:
    for reference_type in INWARD_TYPES:
        names = {field.name for field in fields(reference_type)}
        assert "scope" in names, reference_type.__name__
        assert isinstance(reference_type.owner, ReferenceOwner), reference_type.__name__


def test_reference_types_are_not_interchangeable() -> None:
    """A `DocumentRef` and an `EvidenceRef` are not the same thing even
    though both are `(UUID, UUID)` pairs, and the name is what mypy
    enforces at every call site."""
    identifier, organization = uuid4(), uuid4()
    document = DocumentRef(id=identifier, organization_id=organization)
    evidence = EvidenceRef(id=identifier, organization_id=organization)
    assert type(document) is not type(evidence)
    assert isinstance(document, ScopedRef) and isinstance(evidence, ScopedRef)


# ---------------------------------------------------------------------------
# Version references
# ---------------------------------------------------------------------------


def test_a_version_reference_pins_the_number_and_the_hash() -> None:
    """A reference to "the document" is a moving target; a reference to
    "the document as it was" is not."""
    reference = DocumentVersionRef(
        id=uuid4(),
        organization_id=uuid4(),
        version_number=3,
        version_hash=content_digest_of(b"v3"),
    )
    assert reference.version_number == 3


def test_a_version_reference_refuses_a_missing_number_or_hash() -> None:
    with pytest.raises(DocumentReferenceKindMismatchError):
        DocumentVersionRef(id=uuid4(), organization_id=uuid4(), version_hash="h")
    with pytest.raises(DocumentReferenceInvalidError):
        DocumentVersionRef(id=uuid4(), organization_id=uuid4(), version_number=1, version_hash="  ")


def test_a_bundle_reference_carries_the_digest_so_a_citation_is_checkable() -> None:
    reference = EvidenceBundleRef(
        id=uuid4(), organization_id=uuid4(), bundle_digest=content_digest_of(b"bundle")
    )
    assert reference.bundle_digest


def test_a_bundle_reference_without_a_digest_is_refused() -> None:
    with pytest.raises(DocumentReferenceInvalidError):
        EvidenceBundleRef(id=uuid4(), organization_id=uuid4(), bundle_digest="")


def test_a_rendition_reference_carries_only_a_citation() -> None:
    reference = PublicationRenditionRef(
        id=uuid4(), organization_id=uuid4(), citation_reference="epd2-doc:x:v1:r2"
    )
    assert reference.citation_reference == "epd2-doc:x:v1:r2"


def test_a_determination_reference_carries_no_cached_status() -> None:
    """A status on the reference would be a cached answer that outlives
    the version - and, for admissibility, the procedure - it was true
    of."""
    for reference_type in (SignatureDeterminationRef, AdmissibilityDeterminationRef):
        names = {field.name for field in fields(reference_type)}
        assert names == {"id", "organization_id"}, reference_type.__name__


# ---------------------------------------------------------------------------
# Inward references
# ---------------------------------------------------------------------------


def test_inward_references_declare_the_owning_pack() -> None:
    assert RecordClassReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert LegalHoldReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert LegalCaseReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert DestructionAuthorizationReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert OrganizationScopeReference.owner is ReferenceOwner.PACK_08_ORGANIZATION
    assert FinanceRecordReference.owner is ReferenceOwner.PACK_10_FINANCE


def test_the_base_reference_declares_no_owner_of_its_own() -> None:
    """A subclass that forgot to declare its owner must fail on attribute
    access rather than silently claiming PACK-11's."""
    with pytest.raises(AttributeError):
        _ = ForeignRecordReference.owner


def test_an_inward_reference_payload_is_opaque_and_scoped() -> None:
    here = scope()
    reference = RecordClassReference(external_reference="pack-09:rc:minutes", scope=here)
    payload = reference.to_payload()
    assert payload == {
        "owner": "pack-09-compliance",
        "external_reference": "pack-09:rc:minutes",
        "organization_id": str(here.organization_id),
    }


def test_an_empty_external_reference_is_refused() -> None:
    with pytest.raises(DocumentReferenceInvalidError):
        LegalHoldReference(external_reference="   ", scope=scope())


# ---------------------------------------------------------------------------
# Kind checking across the boundary
# ---------------------------------------------------------------------------


def test_a_consumer_kind_mismatch_is_caught_here_rather_than_downstream() -> None:
    """Consumers hold `kind` as an open string. This is the one place that
    open string meets this context's closed taxonomy, so a consumer that
    asks for the legal opinion and is handed a SEPA mandate finds out now."""
    assert_reference_kind("legal_opinion", DocumentKind.LEGAL_OPINION, context="test")
    with pytest.raises(DocumentReferenceKindMismatchError):
        assert_reference_kind("sepa_mandate_evidence", DocumentKind.LEGAL_OPINION, context="test")


def test_the_citation_format_is_produced_in_one_place() -> None:
    """One grammar for a future parser to handle."""
    identifier = uuid4()
    assert document_citation(identifier, 4) == f"epd2-doc:{identifier}:v4"
