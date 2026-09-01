"""Evidence records, chains of custody and sealed evidence bundles."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from _builders import Fixture, at, governed_document, provenance, reason, scope, version

from epd2_document_service.documents import GovernedDocument
from epd2_document_service.domain import content_digest_of
from epd2_document_service.evidence import (
    BundleState,
    CustodyAction,
    CustodyEvent,
    EvidenceBundle,
    EvidenceBundleItem,
    EvidenceIntegrityState,
    EvidenceRecord,
    assert_evidence_admissible_shape,
    compute_bundle_digest,
    verify_custody_chain,
)
from epd2_document_service.exceptions import (
    DocumentFieldInvalidError,
    EvidenceBundleIncompleteError,
    EvidenceBundleSealedError,
    EvidenceCustodyBrokenError,
    OrganizationScopeMismatchError,
)
from epd2_document_service.versions import DocumentVersion, VersionState


def _cited(fixture: Fixture, document: GovernedDocument) -> DocumentVersion:
    """A version in a state evidence may actually cite."""
    draft = version(document, fixture.author)
    in_review = draft.with_state(
        VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
    )
    return in_review.with_state(
        VersionState.APPROVED, at=at(2), action="a", reason=reason(), authority=fixture.approver
    )


def _custody(
    fixture: Fixture,
    sequence: int,
    holder: str,
    *,
    action: CustodyAction = CustodyAction.TRANSFERRED,
    received_from: str | None = None,
    minutes: int | None = None,
) -> CustodyEvent:
    return CustodyEvent(
        sequence=sequence,
        occurred_at=at(sequence if minutes is None else minutes),
        action=action,
        holder_reference=holder,
        recorded_by=fixture.evidence_custodian,
        reason=reason("DOCUMENT_CUSTODY_TRANSFERRED"),
        received_from_reference=received_from,
    )


def _acquired(fixture: Fixture, holder: str = "registry-a") -> CustodyEvent:
    return _custody(fixture, 1, holder, action=CustodyAction.ACQUIRED)


def _record(
    fixture: Fixture, document: GovernedDocument, cited: DocumentVersion, **overrides: object
) -> EvidenceRecord:
    base = {
        "evidence_id": uuid4(),
        "scope": fixture.scope,
        "document_id": document.document_id,
        "version_number": cited.version_number,
        "version_hash": cited.version_hash,
        "matter_reference": "case-2026-11",
        "provenance": provenance(),
        "registered_at": at(3),
        "registered_by": fixture.evidence_custodian,
    }
    base.update(overrides)
    return EvidenceRecord(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Custody events
# ---------------------------------------------------------------------------


def test_only_the_first_event_may_be_an_acquisition() -> None:
    """A chain acquired twice is two chains."""
    fixture = Fixture()
    with pytest.raises(EvidenceCustodyBrokenError):
        _custody(fixture, 2, "registry-b", action=CustodyAction.ACQUIRED)


def test_a_non_acquisition_must_name_whom_it_came_from() -> None:
    """An unattributed hand-off is a gap in the chain."""
    fixture = Fixture()
    with pytest.raises(EvidenceCustodyBrokenError):
        _custody(fixture, 2, "registry-b", received_from=None)


def test_an_empty_custody_chain_is_refused() -> None:
    """Material with no recorded custody is not evidence."""
    with pytest.raises(EvidenceCustodyBrokenError):
        verify_custody_chain(())


def test_a_continuous_chain_verifies() -> None:
    fixture = Fixture()
    verify_custody_chain(
        (
            _acquired(fixture),
            _custody(fixture, 2, "registry-b", received_from="registry-a"),
            _custody(fixture, 3, "registry-c", received_from="registry-b"),
        )
    )


def test_a_gap_in_the_sequence_breaks_the_chain() -> None:
    fixture = Fixture()
    with pytest.raises(EvidenceCustodyBrokenError) as excinfo:
        verify_custody_chain(
            (
                _acquired(fixture),
                _custody(fixture, 3, "registry-c", received_from="registry-a"),
            )
        )
    assert "gap-free" in str(excinfo.value)


def test_a_forged_intermediate_link_breaks_the_chain() -> None:
    """The attack a per-event validity check misses: every field of the
    inserted event is individually valid, and only the continuity rule
    reveals that nobody handed the item to that holder."""
    fixture = Fixture()
    with pytest.raises(EvidenceCustodyBrokenError) as excinfo:
        verify_custody_chain(
            (
                _acquired(fixture),
                _custody(fixture, 2, "registry-x", received_from="registry-never-held-it"),
            )
        )
    assert "received from" in str(excinfo.value)


def test_time_may_not_run_backwards_between_custody_events() -> None:
    fixture = Fixture()
    with pytest.raises(EvidenceCustodyBrokenError):
        verify_custody_chain(
            (
                _custody(fixture, 1, "registry-a", action=CustodyAction.ACQUIRED, minutes=10),
                _custody(fixture, 2, "registry-b", received_from="registry-a", minutes=1),
            )
        )


def test_a_chain_that_does_not_start_with_an_acquisition_is_refused() -> None:
    """A well-formed transfer as the first event is still not a chain.

    The event itself is valid - it names whom the item came from - so
    per-event validation passes it. Only the chain-level rule notices that
    the item entered custody from somewhere nobody recorded acquiring it
    from."""
    fixture = Fixture()
    first = _custody(fixture, 1, "registry-b", received_from="registry-a")
    with pytest.raises(EvidenceCustodyBrokenError) as excinfo:
        verify_custody_chain((first,))
    assert "acquisition" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Evidence records
# ---------------------------------------------------------------------------


def test_an_evidence_record_preserves_the_version_hash_it_was_registered_at() -> None:
    """A citation that resolved the version at read time would silently
    follow the document forward, and evidence that follows the document
    forward is not evidence of anything."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    record = _record(fixture, document, cited)
    assert record.version_hash == cited.version_hash


def test_appending_a_custody_event_re_verifies_the_whole_chain() -> None:
    """A chain that was already broken must not accept new links and look
    healthy at the tip."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    record = _record(fixture, document, cited).with_custody_event(_acquired(fixture))
    updated = record.with_custody_event(
        _custody(fixture, 2, "registry-b", received_from="registry-a")
    )
    assert updated.current_holder_reference == "registry-b"
    assert updated.record_version == record.record_version + 1

    with pytest.raises(EvidenceCustodyBrokenError):
        updated.with_custody_event(_custody(fixture, 3, "registry-c", received_from="registry-a"))


def test_an_unverified_integrity_state_is_not_the_same_as_intact() -> None:
    """An item nobody has checked is an item nobody can say is unaltered,
    and a bundle sealing over it would be sealing over an assumption."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    assert record.integrity_state is EvidenceIntegrityState.UNVERIFIED
    assert record.integrity_verified_at is None

    verified = record.with_integrity(EvidenceIntegrityState.INTACT, at=at(9))
    assert verified.integrity_verified_at == at(9)


def test_a_verified_state_must_record_when_it_was_verified() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    with pytest.raises(DocumentFieldInvalidError):
        _record(
            fixture,
            document,
            cited,
            integrity_state=EvidenceIntegrityState.INTACT,
        )


def test_an_evidence_payload_carries_no_provenance_substance_on_the_wire() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    payload = _record(fixture, document, _cited(fixture, document)).to_payload()
    assert "provenance" not in payload
    assert "custody" not in payload
    assert payload["custody_event_count"] == 0


def test_an_evidence_state_payload_is_complete_for_hashing() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    payload = _record(fixture, document, _cited(fixture, document)).to_state_payload()
    for expected in ("scope", "provenance", "registered_by", "custody", "record_version"):
        assert expected in payload


# ---------------------------------------------------------------------------
# Admissible shape
# ---------------------------------------------------------------------------


def test_a_draft_version_may_not_be_cited_as_evidence() -> None:
    """Nobody has taken responsibility for a draft, and evidence is
    precisely material somebody has."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    draft = version(document, fixture.author)
    record = _record(fixture, document, draft)
    with pytest.raises(EvidenceBundleIncompleteError):
        assert_evidence_admissible_shape(record, draft)


def test_material_that_changed_after_registration_is_refused() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    record = _record(fixture, document, cited, version_hash=content_digest_of(b"something else"))
    with pytest.raises(EvidenceBundleIncompleteError) as excinfo:
        assert_evidence_admissible_shape(record, cited)
    assert "changed after it was registered" in str(excinfo.value)


def test_a_record_describing_another_version_is_refused() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    record = _record(fixture, document, cited, version_number=2)
    with pytest.raises(EvidenceBundleIncompleteError):
        assert_evidence_admissible_shape(record, cited)


def test_a_well_formed_evidence_record_passes() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    cited = _cited(fixture, document)
    assert_evidence_admissible_shape(_record(fixture, document, cited), cited)


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------


def _bundle(fixture: Fixture) -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id=uuid4(),
        scope=fixture.scope,
        matter_reference="case-2026-11",
        purpose_reference="hearing-bundle",
        created_at=at(4),
        created_by=fixture.evidence_custodian,
    )


def test_an_empty_bundle_cannot_be_sealed() -> None:
    """ "The empty set of evidence, sealed" is a citable object that says
    nothing while looking authoritative."""
    fixture = Fixture()
    with pytest.raises(EvidenceBundleIncompleteError):
        _bundle(fixture).seal(at=at(5), sealed_by=fixture.evidence_custodian)


def test_a_sealed_bundle_refuses_further_items() -> None:
    """A bundle that could still grow would make every prior citation of
    it ambiguous."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    sealed = _bundle(fixture).with_item(record).seal(at=at(5), sealed_by=fixture.evidence_custodian)
    assert sealed.state is BundleState.SEALED
    with pytest.raises(EvidenceBundleSealedError):
        sealed.with_item(_record(fixture, document, _cited(fixture, document)))


def test_a_bundle_cannot_be_sealed_twice() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    sealed = _bundle(fixture).with_item(record).seal(at=at(5), sealed_by=fixture.evidence_custodian)
    with pytest.raises(EvidenceBundleSealedError):
        sealed.seal(at=at(6), sealed_by=fixture.evidence_custodian)


def test_the_same_evidence_may_not_appear_twice_in_one_bundle() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    bundle = _bundle(fixture).with_item(record)
    with pytest.raises(EvidenceBundleIncompleteError):
        bundle.with_item(record)


def test_evidence_from_another_scope_cannot_enter_a_bundle() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    foreign = _record(fixture, document, _cited(fixture, document), scope=scope())
    with pytest.raises(OrganizationScopeMismatchError):
        _bundle(fixture).with_item(foreign)


def test_the_bundle_digest_covers_order() -> None:
    """A numbered exhibit list is not a set: two bundles over the same
    material in different orders are different bundles."""
    bundle_id = uuid4()
    doc_a, doc_b = uuid4(), uuid4()
    ev_a, ev_b = uuid4(), uuid4()
    hash_a, hash_b = content_digest_of(b"a"), content_digest_of(b"b")

    def item(
        ordinal: int, evidence_id: UUID, document_id: UUID, version_hash: str
    ) -> EvidenceBundleItem:
        return EvidenceBundleItem(
            ordinal=ordinal,
            evidence_id=evidence_id,
            document_id=document_id,
            version_number=1,
            version_hash=version_hash,
        )

    first = (item(1, ev_a, doc_a, hash_a), item(2, ev_b, doc_b, hash_b))
    swapped = (item(1, ev_b, doc_b, hash_b), item(2, ev_a, doc_a, hash_a))
    assert compute_bundle_digest(bundle_id, first) != compute_bundle_digest(bundle_id, swapped)


def test_the_bundle_digest_is_deterministic_and_order_insensitive_at_input() -> None:
    """Input ordering must not matter (the ordinals define the order), but
    the ordinals themselves must."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    records = [_record(fixture, document, _cited(fixture, document)) for _ in range(3)]
    bundle = _bundle(fixture)
    for record in records:
        bundle = bundle.with_item(record)
    digest = compute_bundle_digest(bundle.bundle_id, bundle.items)
    assert compute_bundle_digest(bundle.bundle_id, tuple(reversed(bundle.items))) == digest


def test_a_tampered_sealed_bundle_fails_seal_verification() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    sealed = _bundle(fixture).with_item(record).seal(at=at(5), sealed_by=fixture.evidence_custodian)
    sealed.verify_seal()

    tampered = replace(sealed, items=())
    with pytest.raises(EvidenceBundleIncompleteError):
        tampered.verify_seal()


def test_an_unsealed_bundle_has_no_citation_and_no_seal_to_verify() -> None:
    """An open bundle has nothing stable to cite."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    bundle = _bundle(fixture).with_item(_record(fixture, document, _cited(fixture, document)))
    assert bundle.citation_reference is None
    with pytest.raises(EvidenceBundleIncompleteError):
        bundle.verify_seal()


def test_a_sealed_bundle_citation_carries_the_digest_prefix() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    record = _record(fixture, document, _cited(fixture, document))
    sealed = _bundle(fixture).with_item(record).seal(at=at(5), sealed_by=fixture.evidence_custodian)
    citation = sealed.citation_reference
    assert citation is not None
    assert citation.startswith("epd2-bundle:")
    assert sealed.bundle_digest is not None
    assert sealed.bundle_digest[:16] in citation


def test_bundle_ordinals_must_be_gap_free() -> None:
    fixture = Fixture()
    item = EvidenceBundleItem(
        ordinal=2,
        evidence_id=uuid4(),
        document_id=uuid4(),
        version_number=1,
        version_hash=content_digest_of(b"a"),
    )
    with pytest.raises(EvidenceBundleIncompleteError):
        replace(_bundle(fixture), items=(item,))
