"""The `GovernedDocument` aggregate, review requirements, approval,
publication, supersession and revocation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from _builders import (
    T0,
    Fixture,
    at,
    governed_document,
    reason,
    retention_binding,
    scope,
    version,
)

from epd2_document_service.documents import (
    ApprovalRecord,
    DocumentState,
    GovernedDocument,
    PublicationAudience,
    PublicationAuthorization,
    PublicationRendition,
    ReviewKind,
    ReviewOutcome,
    ReviewRecord,
    ReviewRequirement,
    RevocationRecord,
    SupersessionRecord,
    assert_approval_current,
    assert_disposition_authorized,
    assert_no_destruction_under_hold,
    assert_publishable,
    assert_review_complete,
    default_review_requirement,
    resolve_document_state,
    unresolved_blocking_reviews,
)
from epd2_document_service.domain import (
    DispositionAuthorization,
    DocumentKind,
    HoldState,
    LegalHoldBinding,
)
from epd2_document_service.exceptions import (
    DispositionNotAuthorizedError,
    DocumentAlreadyPublishedError,
    DocumentApprovalMissingError,
    DocumentCorrectionTargetInvalidError,
    DocumentFieldInvalidError,
    DocumentPublicationNotAuthorizedError,
    DocumentReviewIncompleteError,
    DocumentRevocationInvalidError,
    DocumentStateUnknownError,
    DocumentSupersessionInvalidError,
    DocumentTransitionInvalidError,
    LegalHoldStateUnknownError,
    OrganizationScopeMismatchError,
    RecordUnderLegalHoldError,
    RetentionBindingMissingError,
)
from epd2_document_service.versions import DocumentVersion, VersionState


def _doc(**overrides: object) -> tuple[Fixture, GovernedDocument]:
    fixture = Fixture()
    return fixture, governed_document(fixture.scope, fixture.custodian, **overrides)


# ---------------------------------------------------------------------------
# Review requirements
# ---------------------------------------------------------------------------


def test_official_records_require_a_substantive_review() -> None:
    requirement = default_review_requirement(
        DocumentKind.MEETING_MINUTES, policy_reference="p", policy_version=1
    )
    assert ReviewKind.SUBSTANTIVE in requirement.required_kinds
    assert ReviewKind.EDITORIAL in requirement.required_kinds


def test_opinions_require_a_legal_review() -> None:
    for kind in (DocumentKind.LEGAL_OPINION, DocumentKind.EXPERT_OPINION):
        requirement = default_review_requirement(kind, policy_reference="p", policy_version=1)
        assert ReviewKind.LEGAL in requirement.required_kinds


def test_public_transparency_documents_require_a_data_protection_review() -> None:
    requirement = default_review_requirement(
        DocumentKind.PUBLIC_TRANSPARENCY_DOCUMENT, policy_reference="p", policy_version=1
    )
    assert ReviewKind.DATA_PROTECTION in requirement.required_kinds


def test_a_review_requirement_needs_a_policy_reference_and_version() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        ReviewRequirement(
            required_kinds=frozenset({ReviewKind.EDITORIAL}),
            policy_reference=" ",
            policy_version=1,
        )
    with pytest.raises(DocumentFieldInvalidError):
        ReviewRequirement(
            required_kinds=frozenset({ReviewKind.EDITORIAL}), policy_reference="p", policy_version=0
        )


# ---------------------------------------------------------------------------
# Review records
# ---------------------------------------------------------------------------


def _review(
    fixture: Fixture,
    document_id: object,
    *,
    kind: ReviewKind = ReviewKind.EDITORIAL,
    outcome: ReviewOutcome = ReviewOutcome.NO_FINDING,
    finding: str | None = None,
    resolves: object = None,
    version_number: int = 1,
    review_id: object = None,
) -> ReviewRecord:
    return ReviewRecord(
        review_id=review_id or uuid4(),  # type: ignore[arg-type]
        document_id=document_id,  # type: ignore[arg-type]
        version_number=version_number,
        scope=fixture.scope,
        review_kind=kind,
        outcome=outcome,
        reviewed_at=at(3),
        reviewer=fixture.reviewer,
        reason=reason("DOCUMENT_REVIEW_RECORDED"),
        finding_reference=finding,
        resolves_review_id=resolves,  # type: ignore[arg-type]
    )


def test_a_review_reporting_a_finding_must_reference_it() -> None:
    """A finding with nowhere to read it is not a finding."""
    fixture, document = _doc()
    with pytest.raises(DocumentFieldInvalidError):
        _review(fixture, document.document_id, outcome=ReviewOutcome.BLOCKING_FINDING)


def test_a_blocking_review_is_unresolved_until_a_later_review_names_it() -> None:
    """Resolution is an explicit, attributed act - not a consequence of
    somebody recording a cheerful second opinion."""
    fixture, document = _doc()
    blocking = _review(
        fixture,
        document.document_id,
        outcome=ReviewOutcome.BLOCKING_FINDING,
        finding="finding-1",
    )
    unrelated = _review(fixture, document.document_id)
    assert unresolved_blocking_reviews((blocking, unrelated)) == (blocking,)
    resolving = _review(fixture, document.document_id, resolves=blocking.review_id)
    assert unresolved_blocking_reviews((blocking, resolving)) == ()


def test_a_blocking_review_cannot_resolve_another_blocking_review() -> None:
    fixture, document = _doc()
    first = _review(
        fixture, document.document_id, outcome=ReviewOutcome.BLOCKING_FINDING, finding="f1"
    )
    second = _review(
        fixture,
        document.document_id,
        outcome=ReviewOutcome.BLOCKING_FINDING,
        finding="f2",
        resolves=first.review_id,
    )
    assert set(unresolved_blocking_reviews((first, second))) == {first, second}


def test_approval_requires_every_mandated_review_kind() -> None:
    """Counting reviews instead would let two general reviews stand in for
    a missing legal one."""
    fixture, document = _doc()
    editorial_only = (_review(fixture, document.document_id, kind=ReviewKind.EDITORIAL),)
    with pytest.raises(DocumentReviewIncompleteError) as excinfo:
        assert_review_complete(document.review_requirement, editorial_only, version_number=1)
    assert "substantive" in str(excinfo.value)


def test_approval_refuses_while_a_blocking_finding_is_open() -> None:
    fixture, document = _doc()
    reviews = (
        _review(fixture, document.document_id, kind=ReviewKind.EDITORIAL),
        _review(
            fixture,
            document.document_id,
            kind=ReviewKind.SUBSTANTIVE,
            outcome=ReviewOutcome.BLOCKING_FINDING,
            finding="f-1",
        ),
    )
    with pytest.raises(DocumentReviewIncompleteError) as excinfo:
        assert_review_complete(document.review_requirement, reviews, version_number=1)
    assert "blocking" in str(excinfo.value)


def test_reviews_of_another_version_do_not_satisfy_this_one() -> None:
    """A review is of a version, not of a document; letting version 1's
    reviews approve version 2 would make review optional after the first
    round."""
    fixture, document = _doc()
    reviews = (
        _review(fixture, document.document_id, kind=ReviewKind.EDITORIAL, version_number=1),
        _review(fixture, document.document_id, kind=ReviewKind.SUBSTANTIVE, version_number=1),
    )
    with pytest.raises(DocumentReviewIncompleteError):
        assert_review_complete(document.review_requirement, reviews, version_number=2)


def test_a_complete_review_set_passes() -> None:
    fixture, document = _doc()
    reviews = (
        _review(fixture, document.document_id, kind=ReviewKind.EDITORIAL),
        _review(fixture, document.document_id, kind=ReviewKind.SUBSTANTIVE),
    )
    assert_review_complete(document.review_requirement, reviews, version_number=1)


# ---------------------------------------------------------------------------
# Approval currency
# ---------------------------------------------------------------------------


def _approval(
    fixture: Fixture, document: GovernedDocument, recorded: DocumentVersion
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=uuid4(),
        document_id=document.document_id,
        version_number=recorded.version_number,
        scope=fixture.scope,
        approved_at=at(4),
        approver=fixture.approver,
        approved_version_hash=recorded.version_hash,
        reason=reason("DOCUMENT_VERSION_APPROVED"),
    )


def test_an_approval_names_the_exact_version_hash_it_approved() -> None:
    """An approval that could drift onto other content would let a
    document be changed after approval and stay "approved"."""
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    approval = _approval(fixture, document, recorded)
    assert_approval_current(approval, recorded)

    other = version(document, fixture.author, content=b"different content")
    with pytest.raises(DocumentApprovalMissingError):
        assert_approval_current(approval, other)


def test_an_approval_for_another_version_number_is_refused() -> None:
    fixture, document = _doc()
    first = version(document, fixture.author)
    second = version(document, fixture.author, number=2, previous_hash=first.version_hash)
    with pytest.raises(DocumentApprovalMissingError):
        assert_approval_current(_approval(fixture, document, first), second)


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------


def _authorization(
    fixture: Fixture,
    document: GovernedDocument,
    version_number: int = 1,
    audience: PublicationAudience = PublicationAudience.PUBLIC,
) -> PublicationAuthorization:
    return PublicationAuthorization(
        authorization_id=uuid4(),
        document_id=document.document_id,
        version_number=version_number,
        scope=fixture.scope,
        audience=audience,
        authorized_at=at(5),
        authorized_by=fixture.publisher,
        disclosure_obligation_reference="satzung-12-3",
        reason=reason("DOCUMENT_PUBLICATION_AUTHORIZED"),
    )


def test_publication_requires_an_approval() -> None:
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    with pytest.raises(DocumentApprovalMissingError):
        assert_publishable(document, recorded, None, _authorization(fixture, document))


def test_publication_requires_its_own_authorization() -> None:
    """Approval is not publication. This is the separation the whole
    publication lifecycle exists to enforce."""
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    with pytest.raises(DocumentPublicationNotAuthorizedError):
        assert_publishable(document, recorded, _approval(fixture, document, recorded), None)


def test_an_authorization_for_another_version_does_not_publish_this_one() -> None:
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    with pytest.raises(DocumentPublicationNotAuthorizedError):
        assert_publishable(
            document,
            recorded,
            _approval(fixture, document, recorded),
            _authorization(fixture, document, version_number=2),
        )


def test_a_published_version_cannot_be_published_twice() -> None:
    """A republication is a new rendition of a new version, never a silent
    overwrite."""
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    published = (
        recorded.with_state(
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
    with pytest.raises(DocumentAlreadyPublishedError):
        assert_publishable(
            document,
            published,
            _approval(fixture, document, published),
            _authorization(fixture, document),
        )


def test_a_publication_authorization_requires_a_disclosure_obligation() -> None:
    """A publication with no stated basis is one nobody can later be held
    to. This service does not decide what must be published."""
    fixture, document = _doc()
    with pytest.raises(DocumentFieldInvalidError):
        PublicationAuthorization(
            authorization_id=uuid4(),
            document_id=document.document_id,
            version_number=1,
            scope=fixture.scope,
            audience=PublicationAudience.PUBLIC,
            authorized_at=at(5),
            authorized_by=fixture.publisher,
            disclosure_obligation_reference="  ",
            reason=reason("DOCUMENT_PUBLICATION_AUTHORIZED"),
        )


def test_a_rendition_citation_carries_no_content() -> None:
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    rendition = PublicationRendition(
        rendition_id=uuid4(),
        document_id=document.document_id,
        version_number=1,
        scope=fixture.scope,
        audience=PublicationAudience.PUBLIC,
        media_type="application/pdf",
        rendition_digest="a" * 64,
        source_version_hash=recorded.version_hash,
        issued_at=at(6),
        issued_by=fixture.publisher,
    )
    citation = rendition.citation_reference
    assert citation.startswith("epd2-doc:")
    assert str(document.document_id) in citation
    payload = rendition.to_payload()
    assert "content" not in payload
    assert payload["source_version_hash"] == recorded.version_hash


# ---------------------------------------------------------------------------
# Supersession and revocation
# ---------------------------------------------------------------------------


def test_a_supersession_must_move_forward() -> None:
    fixture, document = _doc()
    for superseded, superseding in ((2, 1), (2, 2)):
        with pytest.raises(DocumentSupersessionInvalidError):
            SupersessionRecord(
                supersession_id=uuid4(),
                document_id=document.document_id,
                scope=fixture.scope,
                superseded_version_number=superseded,
                superseding_version_number=superseding,
                recorded_at=at(7),
                recorded_by=fixture.approver,
                reason=reason("DOCUMENT_VERSION_SUPERSEDED"),
            )


def test_a_revocation_carries_no_field_that_could_mean_deleted() -> None:
    """Revocation is a statement about *effect*. The material stays
    readable to authorized readers exactly as before."""
    fixture, document = _doc()
    record = RevocationRecord(
        revocation_id=uuid4(),
        document_id=document.document_id,
        scope=fixture.scope,
        version_number=1,
        revoked_at=at(8),
        revoked_by=fixture.approver,
        reason=reason("DOCUMENT_VERSION_REVOKED"),
    )
    payload = record.to_payload()
    assert not any("delete" in key or "destroy" in key or "purge" in key for key in payload)
    assert payload["version_number"] == 1


def test_a_replacement_version_must_be_later_than_the_revoked_one() -> None:
    fixture, document = _doc()
    with pytest.raises(DocumentRevocationInvalidError):
        RevocationRecord(
            revocation_id=uuid4(),
            document_id=document.document_id,
            scope=fixture.scope,
            version_number=3,
            revoked_at=at(8),
            revoked_by=fixture.approver,
            reason=reason("DOCUMENT_VERSION_REVOKED"),
            replacement_version_number=2,
        )


# ---------------------------------------------------------------------------
# The aggregate
# ---------------------------------------------------------------------------


def test_recording_a_version_advances_the_head_and_the_count() -> None:
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    updated = document.with_recorded_version(recorded, at=at(1), reason=reason())
    assert updated.version_count == 1
    assert updated.head_version_hash == recorded.version_hash
    assert updated.document_version == document.document_version + 1
    assert len(updated.history) == 1


def test_versions_must_arrive_in_order() -> None:
    fixture, document = _doc()
    out_of_order = version(document, fixture.author, number=2, previous_hash="a" * 64)
    with pytest.raises(DocumentTransitionInvalidError):
        document.with_recorded_version(out_of_order, at=at(1), reason=reason())


def test_a_version_from_another_document_is_refused() -> None:
    fixture, document = _doc()
    other = governed_document(fixture.scope, fixture.custodian)
    with pytest.raises(DocumentFieldInvalidError):
        document.with_recorded_version(version(other, fixture.author), at=at(1), reason=reason())


def test_no_version_may_be_recorded_on_a_closed_document() -> None:
    fixture, document = _doc()
    closed = document.with_state(
        DocumentState.CLOSED, at=at(1), reason=reason(), authority=fixture.custodian
    )
    with pytest.raises(DocumentTransitionInvalidError):
        closed.with_recorded_version(version(document, fixture.author), at=at(2), reason=reason())


def test_the_current_version_pointer_must_name_an_existing_version() -> None:
    fixture, document = _doc()
    with pytest.raises(DocumentCorrectionTargetInvalidError):
        document.with_current_version(1, at=at(1), reason=reason(), authority=fixture.approver)


def test_observing_the_same_hold_twice_replaces_rather_than_duplicates() -> None:
    """Two observations of one hold are not two holds; keeping both would
    leave a released hold looking active forever."""
    fixture, document = _doc()
    active = LegalHoldBinding(
        hold_reference="h-1", scope=fixture.scope, state=HoldState.ACTIVE, observed_at=T0
    )
    with_hold = document.with_legal_hold(
        active, at=at(1), reason=reason(), authority=fixture.custodian
    )
    assert with_hold.is_under_active_hold is True

    released = LegalHoldBinding(
        hold_reference="h-1", scope=fixture.scope, state=HoldState.RELEASED, observed_at=at(2)
    )
    updated = with_hold.with_legal_hold(
        released, at=at(2), reason=reason(), authority=fixture.custodian
    )
    assert len(updated.legal_holds) == 1
    assert updated.is_under_active_hold is False


def test_a_hold_from_another_scope_cannot_be_attached() -> None:
    fixture, document = _doc()
    foreign = LegalHoldBinding(
        hold_reference="h-1", scope=scope(), state=HoldState.ACTIVE, observed_at=T0
    )
    with pytest.raises(OrganizationScopeMismatchError):
        document.with_legal_hold(foreign, at=at(1), reason=reason(), authority=fixture.custodian)


def test_an_unknown_document_state_is_refused() -> None:
    with pytest.raises(DocumentStateUnknownError):
        resolve_document_state("nearly_closed")


def test_a_document_state_payload_covers_every_field() -> None:
    """A snapshot that is only nearly complete leaves the omitted fields
    outside the tamper-evidence hash and signals nothing about the gap."""
    _fixture, document = _doc()
    payload = document.to_state_payload()
    for expected in (
        "document_id",
        "scope",
        "kind",
        "sensitivity",
        "title_reference",
        "created_at",
        "custodian",
        "review_requirement",
        "state",
        "document_version",
        "current_version_number",
        "version_count",
        "head_version_hash",
        "retention",
        "legal_holds",
        "subject_reference",
        "history",
    ):
        assert expected in payload, expected


# ---------------------------------------------------------------------------
# Destruction guards (FIR-DATA-003 foundation)
# ---------------------------------------------------------------------------


def test_an_active_hold_blocks_destruction() -> None:
    fixture, document = _doc()
    held = document.with_legal_hold(
        LegalHoldBinding(
            hold_reference="h-1", scope=fixture.scope, state=HoldState.ACTIVE, observed_at=T0
        ),
        at=at(1),
        reason=reason(),
        authority=fixture.custodian,
    )
    with pytest.raises(RecordUnderLegalHoldError):
        assert_no_destruction_under_hold(held)


def test_an_indeterminate_hold_fails_closed_with_its_own_code() -> None:
    """Distinct from an active hold on purpose: collapsing the two would
    let "we could not reach PACK-09" be read later as "there was a
    hold"."""
    fixture, document = _doc()
    unknown = document.with_legal_hold(
        LegalHoldBinding(
            hold_reference="h-2",
            scope=fixture.scope,
            state=HoldState.INDETERMINATE,
            observed_at=T0,
        ),
        at=at(1),
        reason=reason(),
        authority=fixture.custodian,
    )
    with pytest.raises(LegalHoldStateUnknownError):
        assert_no_destruction_under_hold(unknown)


def test_an_unheld_document_passes_the_destruction_guard() -> None:
    _fixture, document = _doc()
    assert_no_destruction_under_hold(document)


def test_disposition_requires_a_retention_binding() -> None:
    _fixture, document = _doc()
    with pytest.raises(RetentionBindingMissingError):
        assert_disposition_authorized(document, None)


def test_disposition_requires_a_pack_09_authorization() -> None:
    """This service never authorizes its own disposals."""
    fixture, document = _doc()
    bound = document.with_retention(
        retention_binding(), at=at(1), reason=reason(), authority=fixture.custodian
    )
    with pytest.raises(DispositionNotAuthorizedError):
        assert_disposition_authorized(bound, None)


def test_an_authorization_covering_fewer_versions_is_stale() -> None:
    """PACK-09 authorized the disposal of material it had seen; versions
    added afterwards are material it did not."""
    fixture, document = _doc()
    recorded = version(document, fixture.author)
    bound = document.with_retention(
        retention_binding(), at=at(1), reason=reason(), authority=fixture.custodian
    ).with_recorded_version(recorded, at=at(2), reason=reason())
    authorization = DispositionAuthorization(
        authorization_reference="pack-09:auth:1",
        scope=fixture.scope,
        authorized_at=at(3),
        authorized_version_count=1,
        disposition_action="delete",
    )
    # The authorization covers one version and the document has one, so it
    # is current and must pass. The point of the test is what happens next.
    assert assert_disposition_authorized(bound, authorization) is authorization

    second = version(document, fixture.author, number=2, previous_hash=recorded.version_hash)
    grown = bound.with_recorded_version(second, at=at(4), reason=reason())
    with pytest.raises(DispositionNotAuthorizedError) as excinfo:
        assert_disposition_authorized(grown, authorization)
    assert "stale" in str(excinfo.value)
