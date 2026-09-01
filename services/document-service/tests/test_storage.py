"""Storage ports and in-memory adapters — the six storage rules."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from _builders import (
    Fixture,
    at,
    chain,
    governed_document,
    reason,
    scope,
    tamper,
    version,
)

import epd2_document_service.storage as storage_module
from epd2_document_service.domain import content_digest_of
from epd2_document_service.exceptions import (
    DocumentContentMissingError,
    DocumentFieldInvalidError,
    DocumentVersionChainBrokenError,
    DocumentVersionImmutableError,
    DocumentVersionSequenceInvalidError,
    GovernedRecordDeletionForbiddenError,
)
from epd2_document_service.storage import (
    InMemoryApprovalRecordStore,
    InMemoryCommandIdempotencyStore,
    InMemoryContentStore,
    InMemoryDocumentVersionStore,
    InMemoryGovernedDocumentStore,
    InMemoryPublicationRenditionStore,
    InMemoryRevocationStore,
    InMemorySupersessionStore,
    delete_document_record,
)
from epd2_document_service.versions import GENESIS_PREVIOUS_HASH, VersionState

# ---------------------------------------------------------------------------
# Rule 1 — no delete exists anywhere
# ---------------------------------------------------------------------------


def test_no_store_defines_a_delete_shaped_method() -> None:
    """The structural half of FIR-INV-010, checked over the module itself
    rather than trusted to code review.

    A port that offered `delete` would be publishing an act the domain
    forbids and inviting an adapter to implement it."""
    offenders: list[str] = []
    for name in dir(storage_module):
        if name == "delete_document_record":
            continue
        obj = getattr(storage_module, name)
        if not isinstance(obj, type):
            continue
        for attribute in dir(obj):
            lowered = attribute.lower()
            if any(word in lowered for word in ("delete", "remove", "purge", "destroy", "drop")):
                offenders.append(f"{name}.{attribute}")
    assert offenders == [], offenders


def test_the_one_delete_shaped_function_refuses() -> None:
    """Present on purpose, so a reader looking for "how do I delete a
    document?" finds the refusal and its reason rather than nothing."""
    with pytest.raises(GovernedRecordDeletionForbiddenError):
        delete_document_record(object())


# ---------------------------------------------------------------------------
# Rule 2 — scope isolation on every multi-record query
# ---------------------------------------------------------------------------


def test_listing_documents_filters_by_scope() -> None:
    fixture = Fixture()
    here = governed_document(fixture.scope, fixture.custodian)
    elsewhere = governed_document(scope(), fixture.custodian)
    store = InMemoryGovernedDocumentStore()
    store.save(here)
    store.save(elsewhere)
    listed = store.list_for_scope(scope=fixture.scope)
    assert [d.document_id for d in listed] == [here.document_id]


def test_get_returns_a_foreign_record_and_leaves_the_scope_check_to_the_caller() -> None:
    """Only the application layer knows which scope the *caller*
    presented, so the store returns and `application._load_document`
    decides."""
    fixture = Fixture()
    elsewhere = governed_document(scope(), fixture.custodian)
    store = InMemoryGovernedDocumentStore()
    store.save(elsewhere)
    assert store.get(elsewhere.document_id) is elsewhere


# ---------------------------------------------------------------------------
# Rule 3 — append-only versions
# ---------------------------------------------------------------------------


def test_a_stored_version_is_never_replaced() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    first = version(document, fixture.author)
    store.append(first)
    with pytest.raises(DocumentVersionImmutableError):
        store.append(first)


def test_a_version_out_of_sequence_is_refused() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    with pytest.raises(DocumentVersionSequenceInvalidError):
        store.append(version(document, fixture.author, number=2, previous_hash="a" * 64))


def test_a_reparenting_append_is_refused_before_it_happens() -> None:
    """The storage-side half of FIR-INV-010: `verify_version_chain`
    detects a rewrite after the fact, and this refuses to perform one."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    first = version(document, fixture.author)
    store.append(first)
    forked = version(document, fixture.author, number=2, previous_hash="b" * 64)
    with pytest.raises(DocumentVersionChainBrokenError):
        store.append(forked)


def test_a_valid_chain_appends_cleanly_and_reports_its_head() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    versions = chain(document, fixture.author, 3)
    for entry in versions:
        store.append(entry)
    assert store.head(document.document_id) == versions[-1]
    assert len(store.list_for_document(document.document_id)) == 3
    assert store.get_by_number(document.document_id, 2) == versions[1]
    assert store.get_by_number(document.document_id, 9) is None


def test_a_state_change_may_not_alter_anything_the_hash_covers() -> None:
    """`record_state_change` exists only because `state` and `history` are
    deliberately outside the chain. It must not become a general-purpose
    edit."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    first = version(document, fixture.author)
    store.append(first)
    with pytest.raises(DocumentVersionImmutableError):
        store.record_state_change(tamper(first, title_reference="rewritten"))


def test_a_state_change_may_not_shorten_history() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    first = version(document, fixture.author)
    store.append(first)
    moved = first.with_state(
        VersionState.IN_REVIEW, at=at(1), action="s", reason=reason(), authority=fixture.author
    )
    store.record_state_change(moved)
    with pytest.raises(DocumentVersionImmutableError):
        store.record_state_change(replace(moved, history=()))


def test_a_state_change_on_an_unstored_version_is_refused() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    with pytest.raises(DocumentVersionImmutableError):
        store.record_state_change(version(document, fixture.author))


def test_two_documents_keep_independent_sequences() -> None:
    fixture = Fixture()
    first_document = governed_document(fixture.scope, fixture.custodian)
    second_document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryDocumentVersionStore()
    store.append(version(first_document, fixture.author))
    store.append(version(second_document, fixture.author))
    assert store.head(first_document.document_id) is not None
    assert store.head(second_document.document_id) is not None


def test_an_empty_document_has_no_head() -> None:
    store = InMemoryDocumentVersionStore()
    assert store.head(uuid4()) is None


# ---------------------------------------------------------------------------
# Rule 4 — the content store is content-addressed and write-once
# ---------------------------------------------------------------------------


def test_content_is_addressed_by_its_own_hash() -> None:
    store = InMemoryContentStore()
    digest = store.put(b"governed content")
    assert digest == content_digest_of(b"governed content")
    assert store.get(digest) == b"governed content"
    assert store.has(digest) is True


def test_storing_identical_content_twice_is_a_no_op() -> None:
    """Which is what makes attaching one file to two documents cost one
    copy rather than two."""
    store = InMemoryContentStore()
    first = store.put(b"same")
    second = store.put(b"same")
    assert first == second


def test_different_content_gets_a_different_address() -> None:
    """ "Overwrite with different content" describes a hash collision, not
    an API call - which is how write-once is enforced by construction
    rather than by a flag."""
    store = InMemoryContentStore()
    assert store.put(b"a") != store.put(b"b")


def test_missing_content_is_a_reason_coded_refusal() -> None:
    store = InMemoryContentStore()
    with pytest.raises(DocumentContentMissingError):
        store.get(content_digest_of(b"never stored"))


def test_the_content_store_rejects_a_malformed_digest() -> None:
    store = InMemoryContentStore()
    with pytest.raises(DocumentFieldInvalidError):
        store.get("not-a-digest")


# ---------------------------------------------------------------------------
# Create-once stores
# ---------------------------------------------------------------------------


def test_a_version_is_approved_once() -> None:
    """Two approvals would leave "who approved this?" with two answers,
    and the whole reason approval exists is that the question has one."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    recorded = version(document, fixture.author)
    store = InMemoryApprovalRecordStore()
    from epd2_document_service.documents import ApprovalRecord

    def approval() -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=uuid4(),
            document_id=document.document_id,
            version_number=1,
            scope=fixture.scope,
            approved_at=at(4),
            approver=fixture.approver,
            approved_version_hash=recorded.version_hash,
            reason=reason("DOCUMENT_VERSION_APPROVED"),
        )

    first = store.create_once(approval())
    assert store.create_once(first) is first
    with pytest.raises(DocumentVersionImmutableError):
        store.create_once(approval())


def test_a_version_is_superseded_once() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemorySupersessionStore()
    from epd2_document_service.documents import SupersessionRecord

    def record() -> SupersessionRecord:
        return SupersessionRecord(
            supersession_id=uuid4(),
            document_id=document.document_id,
            scope=fixture.scope,
            superseded_version_number=1,
            superseding_version_number=2,
            recorded_at=at(7),
            recorded_by=fixture.approver,
            reason=reason("DOCUMENT_VERSION_SUPERSEDED"),
        )

    store.append(record())
    with pytest.raises(DocumentVersionImmutableError):
        store.append(record())


def test_a_version_is_revoked_once() -> None:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    store = InMemoryRevocationStore()
    from epd2_document_service.documents import RevocationRecord

    def record() -> RevocationRecord:
        return RevocationRecord(
            revocation_id=uuid4(),
            document_id=document.document_id,
            scope=fixture.scope,
            version_number=1,
            revoked_at=at(8),
            revoked_by=fixture.approver,
            reason=reason("DOCUMENT_VERSION_REVOKED"),
        )

    store.append(record())
    with pytest.raises(DocumentVersionImmutableError):
        store.append(record())


def test_several_renditions_of_one_version_are_legitimate() -> None:
    """A PDF and an accessible HTML form of one approved minutes document
    are two renditions of one record."""
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    recorded = version(document, fixture.author)
    store = InMemoryPublicationRenditionStore()
    from epd2_document_service.documents import PublicationAudience, PublicationRendition

    for index, media_type in enumerate(("application/pdf", "text/html")):
        store.append(
            PublicationRendition(
                rendition_id=uuid4(),
                document_id=document.document_id,
                version_number=1,
                scope=fixture.scope,
                audience=PublicationAudience.PUBLIC,
                media_type=media_type,
                rendition_digest=content_digest_of(media_type.encode()),
                source_version_hash=recorded.version_hash,
                issued_at=at(9 + index),
                issued_by=fixture.publisher,
            )
        )
    assert len(store.list_for_version(document.document_id, 1)) == 2


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_the_idempotency_store_round_trips_a_command_record() -> None:
    from epd2_document_service.storage import IdempotencyRecord

    store = InMemoryCommandIdempotencyStore()
    event_id = uuid4()
    assert store.get(event_id) is None
    record = IdempotencyRecord(
        event_id=event_id,
        command="register_document",
        request_digest="d" * 64,
        aggregate_id=uuid4(),
        recorded_at=at(0),
    )
    store.put(record)
    assert store.get(event_id) == record


def test_an_idempotency_record_requires_a_command_name() -> None:
    from epd2_document_service.storage import IdempotencyRecord

    with pytest.raises(DocumentFieldInvalidError):
        IdempotencyRecord(
            event_id=uuid4(),
            command="  ",
            request_digest="d" * 64,
            aggregate_id=uuid4(),
            recorded_at=at(0),
        )


def test_the_genesis_constant_matches_the_audit_core_convention() -> None:
    """Two chaining conventions in one repository is one too many."""
    from epd2_audit_core.hash_chain import GENESIS_PREVIOUS_HASH as AUDIT_GENESIS

    assert GENESIS_PREVIOUS_HASH == AUDIT_GENESIS
