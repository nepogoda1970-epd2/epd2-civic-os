"""Version immutability and the cryptographically linked history
(FIR-INV-010).

The most important tests in this package. Everything else in
`document-service` is worth less if these do not hold, so they are written
to exercise the *attacks* rather than the happy path: a rewritten field, a
removed version, a re-parented chain, a swapped content blob, a resealed
forgery.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from _builders import (
    Fixture,
    at,
    authority,
    chain,
    governed_document,
    provenance,
    reason,
    scope,
    tamper,
    version,
)

from epd2_document_service.authorization import DocumentRole
from epd2_document_service.documents import GovernedDocument
from epd2_document_service.domain import ContentDescriptor, content_digest_of
from epd2_document_service.exceptions import (
    DocumentContentDigestMismatchError,
    DocumentCorrectionTargetInvalidError,
    DocumentStateUnknownError,
    DocumentTransitionInvalidError,
    DocumentVersionChainBrokenError,
    DocumentVersionSequenceInvalidError,
)
from epd2_document_service.versions import (
    GENESIS_PREVIOUS_HASH,
    VersionState,
    assert_version_chain_intact,
    compute_version_hash,
    hashable_fields,
    next_version_hash_base,
    resolve_version_state,
    seal_version,
    verify_version_chain,
    verify_version_content,
)


def _document() -> tuple[Fixture, GovernedDocument]:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    return fixture, document


# ---------------------------------------------------------------------------
# Sealing and determinism
# ---------------------------------------------------------------------------


def test_a_sealed_version_hash_is_deterministic() -> None:
    fixture, document = _document()
    first = version(document, fixture.author)
    recomputed = compute_version_hash(first)
    assert first.version_hash == recomputed
    # Recomputing twice must give the same answer: `canonical_dumps` sorts
    # keys, so dict construction order can never change the hash.
    assert compute_version_hash(first) == recomputed


def test_two_logically_identical_versions_hash_identically() -> None:
    fixture, document = _document()
    first = version(document, fixture.author)
    twin = seal_version(replace(first, version_hash="0" * 64))
    assert twin.version_hash == first.version_hash


def test_version_one_must_link_to_genesis() -> None:
    fixture, document = _document()
    with pytest.raises(DocumentVersionChainBrokenError):
        version(document, fixture.author, number=1, previous_hash="a" * 64)


def test_only_version_one_may_link_to_genesis() -> None:
    fixture, document = _document()
    with pytest.raises(DocumentVersionChainBrokenError):
        version(document, fixture.author, number=2, previous_hash=GENESIS_PREVIOUS_HASH)


def test_version_numbers_start_at_one() -> None:
    fixture, document = _document()
    with pytest.raises(DocumentVersionSequenceInvalidError):
        version(document, fixture.author, number=0)


# ---------------------------------------------------------------------------
# What the hash covers, and what it deliberately does not
# ---------------------------------------------------------------------------


def test_the_hash_covers_the_content_digest() -> None:
    """Swapping the recorded digest changes the hash.

    This is the property that binds the chain of *records* to the chain of
    *contents*: without it, a version could be re-pointed at different
    bytes and the chain would still verify."""
    fixture, document = _document()
    original = version(document, fixture.author)
    altered = replace(
        original,
        content=ContentDescriptor(
            digest=content_digest_of(b"different"), media_type="text/plain", byte_length=9
        ),
    )
    assert compute_version_hash(altered) != original.version_hash


def test_the_hash_covers_the_recording_authority_in_full() -> None:
    """Attribution cannot be rewritten silently.

    `recorded_by` travels into the hash including `actor_reference`, so
    "who recorded this" is as protected as what was recorded."""
    fixture, document = _document()
    original = version(document, fixture.author)
    other = authority(DocumentRole.DOCUMENT_AUTHOR, fixture.scope, fixture.port)
    assert compute_version_hash(replace(original, recorded_by=other)) != original.version_hash


def test_the_hash_covers_provenance() -> None:
    fixture, document = _document()
    original = version(document, fixture.author)
    altered = replace(original, provenance=provenance(source_system_reference="somewhere-else"))
    assert compute_version_hash(altered) != original.version_hash


def test_the_hash_does_not_cover_state_or_history() -> None:
    """A governed transition must not break the chain for later versions.

    If `state` were hashed, approving version 3 would change its hash and
    invalidate versions 4..n - so the chain would break on legitimate acts
    and a real break would be indistinguishable from routine noise."""
    fixture, document = _document()
    original = version(document, fixture.author)
    moved = original.with_state(
        VersionState.IN_REVIEW,
        at=at(5),
        action="submitted_for_review",
        reason=reason(),
        authority=fixture.author,
    )
    assert moved.version_hash == original.version_hash
    assert compute_version_hash(moved) == original.version_hash
    assert len(moved.history) == 1


def test_hashable_fields_names_the_content_descriptor_not_content() -> None:
    """The key is `content_descriptor`, so the emission guard's blunt
    key-name check on `content` stays usable everywhere."""
    fixture, document = _document()
    fields = hashable_fields(version(document, fixture.author))
    assert "content_descriptor" in fields
    assert "content" not in fields


# ---------------------------------------------------------------------------
# Chain verification
# ---------------------------------------------------------------------------


def test_a_valid_chain_verifies_and_reports_its_head() -> None:
    fixture, document = _document()
    versions = chain(document, fixture.author, 4)
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is True
    assert result.version_count == 4
    assert result.head_hash == versions[-1].version_hash
    assert result.broken_at_version is None


def test_an_empty_sequence_is_not_a_valid_chain() -> None:
    """A document whose versions are all missing must not verify.

    Reporting "valid, length zero" would mean deleting every version of a
    document passes the integrity check that exists to detect exactly
    that."""
    result = verify_version_chain(uuid4(), ())
    assert result.valid is False
    assert "no versions" in (result.detail or "")


def test_a_rewritten_version_breaks_the_chain_at_that_version() -> None:
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 4))
    versions[1] = tamper(versions[1], title_reference="rewritten-title")
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is False
    assert result.broken_at_version == 2
    assert "recomputed hash" in (result.detail or "")


def test_a_removed_version_breaks_the_chain() -> None:
    """Deleting version 2 leaves a gap the sequence check catches.

    Note that this is caught by the *numbering* rule rather than the hash
    rule: the remaining versions' hashes are all individually correct, and
    only the gap reveals the removal."""
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 4))
    del versions[1]
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is False
    assert result.broken_at_version == 2
    assert "gap-free" in (result.detail or "")


def test_a_reparented_version_breaks_the_chain() -> None:
    """A version whose predecessor link was re-pointed.

    The way a rewritten history gets grafted back on: build an alternative
    version 2, and the link from 2 to 1 no longer matches."""
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 3))
    versions[1] = seal_version(replace(versions[1], previous_version_hash="b" * 64))
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is False
    assert result.broken_at_version == 2
    assert "previous_version_hash" in (result.detail or "")


def test_a_resealed_forgery_still_breaks_the_chain_downstream() -> None:
    """The attack a naive per-record hash would miss.

    Rewriting version 2 *and* resealing it makes version 2 itself
    self-consistent - but version 3 still links to the old hash, so the
    break simply moves one step later. Only rewriting the entire tail
    escapes detection, which is the tamper-evidence property this design
    claims and the limitations document is explicit about."""
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 3))
    versions[1] = seal_version(replace(versions[1], title_reference="rewritten"))
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is False
    assert result.broken_at_version == 3


def test_a_version_from_another_document_breaks_the_chain() -> None:
    fixture, document = _document()
    other_document = governed_document(fixture.scope, fixture.custodian)
    versions = [*chain(document, fixture.author, 2), version(other_document, fixture.author)]
    result = verify_version_chain(document.document_id, versions)
    assert result.valid is False
    assert "different document" in (result.detail or "")


def test_assert_version_chain_intact_raises_with_the_broken_version() -> None:
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 3))
    versions[2] = tamper(versions[2], title_reference="rewritten")
    with pytest.raises(DocumentVersionChainBrokenError) as excinfo:
        assert_version_chain_intact(document.document_id, versions)
    assert "version 3" in str(excinfo.value)


def test_chain_verification_is_order_independent() -> None:
    """Verification sorts by version number, so a store that returns
    versions in an arbitrary order still verifies correctly."""
    fixture, document = _document()
    versions = list(chain(document, fixture.author, 4))
    assert verify_version_chain(document.document_id, list(reversed(versions))).valid is True


# ---------------------------------------------------------------------------
# Content integrity
# ---------------------------------------------------------------------------


def test_content_verification_accepts_the_recorded_bytes() -> None:
    fixture, document = _document()
    recorded = version(document, fixture.author, content=b"exact bytes")
    verify_version_content(recorded, b"exact bytes")


def test_swapped_content_is_detected_even_though_the_chain_is_intact() -> None:
    """The attack the chain alone misses.

    The version record is untouched, so `verify_version_chain` passes;
    only the digest comparison catches it. This is why
    `verify_document_integrity` runs both."""
    fixture, document = _document()
    recorded = version(document, fixture.author, content=b"exact bytes")
    assert verify_version_chain(document.document_id, [recorded]).valid is True
    with pytest.raises(DocumentContentDigestMismatchError):
        verify_version_content(recorded, b"different bytes")


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------


def test_returned_for_revision_is_terminal_for_that_version() -> None:
    """A returned version cannot go back to draft.

    The workflow-level half of "historical versions are never rewritten":
    revising is version N+1, never a reopened version N."""
    fixture, document = _document()
    recorded = version(document, fixture.author)
    in_review = recorded.with_state(
        VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
    )
    returned = in_review.with_state(
        VersionState.RETURNED_FOR_REVISION,
        at=at(2),
        action="r",
        reason=reason(),
        authority=fixture.reviewer,
    )
    with pytest.raises(DocumentTransitionInvalidError):
        returned.with_state(
            VersionState.DRAFT, at=at(3), action="x", reason=reason(), authority=fixture.author
        )


def test_a_draft_cannot_be_published_without_review_and_approval() -> None:
    fixture, document = _document()
    recorded = version(document, fixture.author)
    with pytest.raises(DocumentTransitionInvalidError):
        recorded.with_state(
            VersionState.PUBLISHED, at=at(1), action="x", reason=reason(), authority=fixture.author
        )


def test_a_superseded_version_can_still_be_revoked() -> None:
    """Supersession and revocation say different things and can both be
    true: "there is a newer one" and "this one has no effect"."""
    fixture, document = _document()
    recorded = version(document, fixture.author)
    approved = (
        recorded.with_state(
            VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
        )
        .with_state(
            VersionState.APPROVED, at=at(2), action="a", reason=reason(), authority=fixture.approver
        )
        .with_state(
            VersionState.SUPERSEDED,
            at=at(3),
            action="sup",
            reason=reason(),
            authority=fixture.approver,
        )
    )
    revoked = approved.with_state(
        VersionState.REVOKED, at=at(4), action="rev", reason=reason(), authority=fixture.approver
    )
    assert revoked.is_revoked is True
    assert len(revoked.history) == 4


def test_history_is_append_only_and_sequenced() -> None:
    fixture, document = _document()
    recorded = version(document, fixture.author)
    moved = recorded.with_state(
        VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
    ).with_state(
        VersionState.APPROVED, at=at(2), action="a", reason=reason(), authority=fixture.approver
    )
    assert [entry.sequence for entry in moved.history] == [1, 2]
    assert recorded.history == ()


def test_an_unknown_state_is_refused() -> None:
    with pytest.raises(DocumentStateUnknownError):
        resolve_version_state("nearly_approved")


def test_every_known_state_resolves() -> None:
    for state in VersionState:
        assert resolve_version_state(state.value) is state


# ---------------------------------------------------------------------------
# Correction
# ---------------------------------------------------------------------------


def test_a_correction_must_target_an_earlier_version() -> None:
    fixture, document = _document()
    with pytest.raises(DocumentCorrectionTargetInvalidError):
        version(
            document,
            fixture.author,
            number=2,
            previous_hash="c" * 64,
            corrects_version_number=2,
        )


def test_a_correction_must_carry_a_reason() -> None:
    fixture, document = _document()
    with pytest.raises(DocumentCorrectionTargetInvalidError):
        version(
            document,
            fixture.author,
            number=2,
            previous_hash="c" * 64,
            corrects_version_number=1,
            correction_reason=None,
        )


def test_a_correction_does_not_alter_the_corrected_version() -> None:
    """The whole point of correction-by-new-version.

    Version 1 is byte-for-byte what it was before version 2 corrected
    it - same hash, same state, same history."""
    fixture, document = _document()
    first = version(document, fixture.author)
    before = (first.version_hash, first.state, first.history)
    second = version(
        document,
        fixture.author,
        number=2,
        previous_hash=first.version_hash,
        content=b"corrected content",
        corrects_version_number=1,
        correction_reason=reason("DOCUMENT_VERSION_CORRECTED"),
    )
    assert (first.version_hash, first.state, first.history) == before
    assert verify_version_chain(document.document_id, [first, second]).valid is True


# ---------------------------------------------------------------------------
# Next-version derivation
# ---------------------------------------------------------------------------


def test_next_version_base_starts_at_one_and_genesis() -> None:
    assert next_version_hash_base(()) == (1, GENESIS_PREVIOUS_HASH)


def test_next_version_base_follows_the_stored_head() -> None:
    fixture, document = _document()
    versions = chain(document, fixture.author, 3)
    number, previous = next_version_hash_base(versions)
    assert number == 4
    assert previous == versions[-1].version_hash


def test_next_version_base_ignores_input_ordering() -> None:
    fixture, document = _document()
    versions = chain(document, fixture.author, 3)
    assert next_version_hash_base(list(reversed(versions))) == next_version_hash_base(versions)


def test_versions_in_a_foreign_scope_are_still_hashed_over_their_scope() -> None:
    """Scope is inside the hash, so a version cannot be moved between
    organizations without the chain noticing."""
    fixture, document = _document()
    original = version(document, fixture.author)
    moved = replace(original, scope=scope())
    assert compute_version_hash(moved) != original.version_hash
