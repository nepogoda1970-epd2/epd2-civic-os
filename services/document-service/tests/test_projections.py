"""Restricted and public projections — the single surface anything leaves
this context through.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields, replace
from uuid import uuid4

import pytest
from _builders import Fixture, T0, at, governed_document, reason, version

from epd2_document_service.determinations import (
    AdmissibilityStatus,
    SignatureStatus,
)
from epd2_document_service.documents import (
    PublicationAudience,
    PublicationRendition,
    ReviewKind,
    ReviewOutcome,
    ReviewRecord,
    RevocationRecord,
    SupersessionRecord,
)
from epd2_document_service.domain import (
    HoldState,
    LegalHoldBinding,
    SensitivityClass,
    content_digest_of,
)
from epd2_document_service.evidence import EvidenceBundle
from epd2_document_service.exceptions import (
    DocumentDisclosurePolicyViolationError,
    DocumentFieldInvalidError,
    EvidenceBundleIncompleteError,
)
from epd2_document_service.projections import (
    PROJECTION_VERSION,
    CurrencyStatus,
    PublicDocumentProjection,
    build_evidence_bundle_projection,
    build_public_projection,
    build_restricted_projection,
    currency_for,
)
from epd2_document_service.versions import VersionState


def _published(fixture: Fixture, document: object) -> object:
    draft = version(document, fixture.author)
    return (
        draft.with_state(
            VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
        )
        .with_state(
            VersionState.APPROVED, at=at(2), action="a", reason=reason(), authority=fixture.approver
        )
        .with_state(
            VersionState.PUBLISHED,
            at=at(3),
            action="p",
            reason=reason(),
            authority=fixture.publisher,
        )
    )


def _rendition(fixture: Fixture, document: object, published: object) -> PublicationRendition:
    return PublicationRendition(
        rendition_id=uuid4(),
        document_id=document.document_id,
        version_number=published.version_number,
        scope=fixture.scope,
        audience=PublicationAudience.PUBLIC,
        media_type="application/pdf",
        rendition_digest=content_digest_of(b"rendition"),
        source_version_hash=published.version_hash,
        issued_at=at(4),
        issued_by=fixture.publisher,
    )


def _revocation(fixture: Fixture, document: object, number: int = 1) -> RevocationRecord:
    return RevocationRecord(
        revocation_id=uuid4(),
        document_id=document.document_id,
        scope=fixture.scope,
        version_number=number,
        revoked_at=at(9),
        revoked_by=fixture.approver,
        reason=reason("DOCUMENT_VERSION_REVOKED"),
    )


# ---------------------------------------------------------------------------
# Non-authoritativeness
# ---------------------------------------------------------------------------


def test_no_projection_can_be_constructed_claiming_authority() -> None:
    """`is_authoritative` is a read-only property, not a field. A field
    could be constructed `True`; a property cannot, and the distinction
    survives `replace`, deserialisation and every future field."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    restricted = build_restricted_projection(document, published, generated_at=T0)
    assert restricted.is_authoritative is False
    assert restricted.to_payload()["is_authoritative"] is False

    # A property, not a field: it is absent from `fields()`, so no
    # construction path, no `replace` call and no deserialisation from a
    # payload can set it - which a boolean field would allow.
    assert "is_authoritative" not in {f.name for f in dataclass_fields(restricted)}
    assert isinstance(type(restricted).is_authoritative, property)
    with pytest.raises(TypeError):
        replace(restricted, is_authoritative=True)  # type: ignore[misc]


def test_every_projection_declares_its_schema_version() -> None:
    """So a consumer can tell a missing field from an older shape."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    projection = build_restricted_projection(document, published, generated_at=T0)
    assert projection.to_payload()["projection_version"] == PROJECTION_VERSION


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------


def test_revocation_outranks_supersession() -> None:
    """A version that was superseded and later revoked is revoked;
    reporting it as merely superseded would tell a reader the newer
    version replaced it when in fact it was withdrawn."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    supersession = SupersessionRecord(
        supersession_id=uuid4(),
        document_id=document.document_id,
        scope=fixture.scope,
        superseded_version_number=1,
        superseding_version_number=2,
        recorded_at=at(8),
        recorded_by=fixture.approver,
        reason=reason("DOCUMENT_VERSION_SUPERSEDED"),
    )
    revocation = _revocation(fixture, document)
    assert (
        currency_for(published, supersession=supersession, revocation=revocation)
        is CurrencyStatus.REVOKED
    )
    assert (
        currency_for(published, supersession=supersession, revocation=None)
        is CurrencyStatus.SUPERSEDED
    )
    assert currency_for(published, supersession=None, revocation=None) is CurrencyStatus.CURRENT


def test_an_unapproved_version_is_not_yet_effective() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    draft = version(document, fixture.author)
    assert (
        currency_for(draft, supersession=None, revocation=None)
        is CurrencyStatus.NOT_YET_EFFECTIVE
    )


# ---------------------------------------------------------------------------
# Restricted projection
# ---------------------------------------------------------------------------


def test_a_restricted_projection_carries_no_content_and_no_title() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    payload = build_restricted_projection(
        document, _published(fixture, document), generated_at=T0
    ).to_payload()
    assert "content" not in payload
    assert "title" not in payload
    assert payload["title_reference"] == document.title_reference


def test_a_restricted_projection_reports_review_counts_not_finding_text() -> None:
    """A reviewer's finding on a membership appeal is exactly the internal
    deliberation FIR-MEM-001 says the applicant must not see. A count
    answers "is this contested?" without answering "with what?"."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    reviews = (
        ReviewRecord(
            review_id=uuid4(),
            document_id=document.document_id,
            version_number=1,
            scope=fixture.scope,
            review_kind=ReviewKind.SUBSTANTIVE,
            outcome=ReviewOutcome.BLOCKING_FINDING,
            reviewed_at=at(2),
            reviewer=fixture.reviewer,
            reason=reason("DOCUMENT_REVIEW_RECORDED"),
            finding_reference="finding-doc-77",
        ),
    )
    payload = build_restricted_projection(
        document, published, generated_at=T0, reviews=reviews
    ).to_payload()
    assert payload["review_count"] == 1
    assert payload["open_blocking_review_count"] == 1
    assert "finding_reference" not in payload
    assert "finding-doc-77" not in str(payload)


def test_absent_determinations_are_reported_as_not_determined() -> None:
    """"Nobody has decided" and "somebody decided no" are different facts
    and a reader must be able to tell them apart."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    projection = build_restricted_projection(
        document, _published(fixture, document), generated_at=T0
    )
    assert projection.signature_status is SignatureStatus.NOT_DETERMINED
    assert projection.admissibility_status is AdmissibilityStatus.NOT_DETERMINED


def test_a_restricted_projection_reports_hold_counts() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian).with_legal_hold(
        LegalHoldBinding(
            hold_reference="h-1", scope=fixture.scope, state=HoldState.ACTIVE, observed_at=T0
        ),
        at=at(1),
        reason=reason(),
        authority=fixture.custodian,
    )
    projection = build_restricted_projection(
        document, _published(fixture, document), generated_at=T0
    )
    assert projection.active_legal_hold_count == 1
    assert projection.undetermined_legal_hold_count == 0


# ---------------------------------------------------------------------------
# Public projection
# ---------------------------------------------------------------------------


def test_an_unpublished_version_may_not_be_projected_publicly() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    draft = version(document, fixture.author)
    with pytest.raises(DocumentDisclosurePolicyViolationError):
        build_public_projection(
            document,
            draft,
            generated_at=T0,
            published_at=T0,
            audience=PublicationAudience.PUBLIC,
            disclosure_obligation_reference="satzung-12-3",
        )


def test_a_member_only_publication_does_not_reach_the_public_surface() -> None:
    """"Published to members" is a real publication and is not this
    surface."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    with pytest.raises(DocumentDisclosurePolicyViolationError):
        build_public_projection(
            document,
            _published(fixture, document),
            generated_at=T0,
            published_at=T0,
            audience=PublicationAudience.MEMBERS,
            disclosure_obligation_reference="satzung-12-3",
        )


def test_publishing_does_not_reclassify_restricted_content() -> None:
    """A publication decision that appeared to reclassify content would be
    a reclassification nobody recorded."""
    fixture = Fixture()
    document = governed_document(
        fixture.scope, fixture.custodian, sensitivity=SensitivityClass.RESTRICTED
    )
    with pytest.raises(DocumentDisclosurePolicyViolationError) as excinfo:
        build_public_projection(
            document,
            _published(fixture, document),
            generated_at=T0,
            published_at=T0,
            audience=PublicationAudience.PUBLIC,
            disclosure_obligation_reference="satzung-12-3",
        )
    assert "reclassify" in str(excinfo.value)


def test_a_public_projection_requires_a_disclosure_obligation_reference() -> None:
    """This module does not decide what must be published; the answer
    arrives as a reference it refuses to proceed without."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    with pytest.raises(DocumentFieldInvalidError):
        build_public_projection(
            document,
            _published(fixture, document),
            generated_at=T0,
            published_at=T0,
            audience=PublicationAudience.PUBLIC,
            disclosure_obligation_reference="   ",
        )


def test_a_published_version_projects_with_its_rendition_citation() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    rendition = _rendition(fixture, document, published)
    projection = build_public_projection(
        document,
        published,
        generated_at=T0,
        published_at=at(3),
        audience=PublicationAudience.PUBLIC,
        disclosure_obligation_reference="satzung-12-3",
        rendition=rendition,
    )
    assert projection.citation_reference == rendition.citation_reference
    assert projection.currency is CurrencyStatus.CURRENT
    assert projection.is_tombstone is False


def test_a_revoked_publication_becomes_a_tombstone_rather_than_disappearing() -> None:
    """A published document that simply vanished would be a silent
    retraction of something the public was already told."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    revoked = published.with_state(
        VersionState.REVOKED,
        at=at(9),
        action="revoked",
        reason=reason(),
        authority=fixture.approver,
    )
    projection = build_public_projection(
        document,
        revoked,
        generated_at=T0,
        published_at=at(3),
        audience=PublicationAudience.PUBLIC,
        disclosure_obligation_reference="satzung-12-3",
        rendition=_rendition(fixture, document, published),
        revocation=_revocation(fixture, document),
    )
    assert projection.is_tombstone is True
    assert projection.revocation_reason_code == "DOCUMENT_VERSION_REVOKED"
    assert projection.revoked_at == at(9)


def test_a_revoked_publication_no_longer_offers_a_citable_rendition() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    projection = build_public_projection(
        document,
        published.with_state(
            VersionState.REVOKED,
            at=at(9),
            action="revoked",
            reason=reason(),
            authority=fixture.approver,
        ),
        generated_at=T0,
        published_at=at(3),
        audience=PublicationAudience.PUBLIC,
        disclosure_obligation_reference="satzung-12-3",
        rendition=_rendition(fixture, document, published),
        revocation=_revocation(fixture, document),
    )
    assert projection.citation_reference is None
    assert projection.rendition_media_type is None


def test_a_tombstone_must_state_when_and_why() -> None:
    """An unexplained disappearance is a silent retraction."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    with pytest.raises(DocumentDisclosurePolicyViolationError):
        PublicDocumentProjection(
            document_id=document.document_id,
            organization_id=fixture.scope.organization_id,
            generated_at=T0,
            kind=document.kind,
            published_version_number=1,
            published_version_hash=published.version_hash,
            audience=PublicationAudience.PUBLIC,
            disclosure_obligation_reference="satzung-12-3",
            currency=CurrencyStatus.REVOKED,
            published_at=at(3),
        )


def test_a_public_projection_carries_no_content_and_no_title() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    payload = build_public_projection(
        document,
        published,
        generated_at=T0,
        published_at=at(3),
        audience=PublicationAudience.PUBLIC,
        disclosure_obligation_reference="satzung-12-3",
    ).to_payload()
    for forbidden in ("content", "title", "title_reference", "subject_reference"):
        assert forbidden not in payload


def test_the_public_projection_is_a_separate_type_not_a_filtered_variant() -> None:
    """A shared type with a "public" flag would mean one wrong flag exposes
    every restricted field at once."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    published = _published(fixture, document)
    public = build_public_projection(
        document,
        published,
        generated_at=T0,
        published_at=at(3),
        audience=PublicationAudience.PUBLIC,
        disclosure_obligation_reference="satzung-12-3",
    )
    restricted = build_restricted_projection(document, published, generated_at=T0)
    assert type(public) is not type(restricted)
    assert set(public.to_payload()) & {"sensitivity", "review_count", "document_state"} == set()


# ---------------------------------------------------------------------------
# Evidence bundle projection
# ---------------------------------------------------------------------------


def _sealed_bundle(fixture: Fixture, document: object) -> EvidenceBundle:
    from epd2_document_service.evidence import EvidenceRecord
    from _builders import provenance

    published = _published(fixture, document)
    record = EvidenceRecord(
        evidence_id=uuid4(),
        scope=fixture.scope,
        document_id=document.document_id,
        version_number=published.version_number,
        version_hash=published.version_hash,
        matter_reference="case-2026-11",
        provenance=provenance(),
        registered_at=at(3),
        registered_by=fixture.evidence_custodian,
    )
    bundle = EvidenceBundle(
        bundle_id=uuid4(),
        scope=fixture.scope,
        matter_reference="case-2026-11",
        purpose_reference="hearing-bundle",
        created_at=at(4),
        created_by=fixture.evidence_custodian,
    ).with_item(record)
    return bundle.seal(at=at(5), sealed_by=fixture.evidence_custodian)


def test_a_bundle_projection_cites_versions_without_provenance_or_custody() -> None:
    """A case citing a bundle needs to know *which* material; who held it
    and where it came from stays behind an authorized read."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    payload = build_evidence_bundle_projection(
        _sealed_bundle(fixture, document), generated_at=T0
    ).to_payload()
    assert payload["item_count"] == 1
    assert payload["item_references"][0].startswith("epd2-doc:")
    for forbidden in ("provenance", "custody", "matter_reference", "purpose_reference"):
        assert forbidden not in payload


def test_an_unsealed_bundle_has_no_projection() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    bundle = EvidenceBundle(
        bundle_id=uuid4(),
        scope=fixture.scope,
        matter_reference="case-2026-11",
        purpose_reference="hearing-bundle",
        created_at=at(4),
        created_by=fixture.evidence_custodian,
    )
    with pytest.raises(EvidenceBundleIncompleteError):
        build_evidence_bundle_projection(bundle, generated_at=T0)


def test_a_bundle_projection_verifies_the_seal_before_publishing_a_citation() -> None:
    """Projecting a bundle whose digest no longer matches its items would
    publish a citation to material that changed after it was sealed."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    tampered = replace(_sealed_bundle(fixture, document), items=())
    with pytest.raises(EvidenceBundleIncompleteError):
        build_evidence_bundle_projection(tampered, generated_at=T0)
