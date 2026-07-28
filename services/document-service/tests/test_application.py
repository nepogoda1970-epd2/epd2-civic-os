"""The command and query layer: the guard frame, the full governed
lifecycle, idempotency, optimistic concurrency and the integrity
precondition.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from _builders import (
    Fixture,
    at,
    authority,
    clock_at,
    provenance,
    reason,
    retention_binding,
    scope,
    tamper,
)

from epd2_document_service import application as app
from epd2_document_service.authorization import DocumentRole
from epd2_document_service.determinations import (
    AdmissibilityStatus,
    SignatureForm,
    SignatureStatus,
)
from epd2_document_service.documents import (
    PublicationAudience,
    ReviewKind,
    ReviewOutcome,
)
from epd2_document_service.domain import (
    ConflictDeclaration,
    DispositionAuthorization,
    DocumentKind,
    HoldState,
    LegalHoldBinding,
    RequestContext,
    SensitivityClass,
    content_digest_of,
)
from epd2_document_service.evidence import CustodyAction
from epd2_document_service.exceptions import (
    AuthorityRoleIncompatibleError,
    ConflictOfInterestUndeclaredError,
    DispositionNotAuthorizedError,
    DocumentApprovalMissingError,
    DocumentAuthorityMissingError,
    DocumentCorrectionTargetInvalidError,
    DocumentDeterminationNotPermittedError,
    DocumentRecordNotFoundError,
    DocumentReviewIncompleteError,
    DocumentTransitionInvalidError,
    DocumentVersionChainBrokenError,
    IdempotencyConflictError,
    LegalHoldStateUnknownError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeUndeterminedError,
    RecordUnderLegalHoldError,
    SelfApprovalProhibitedError,
)
from epd2_document_service.versions import VersionState

# ---------------------------------------------------------------------------
# A reusable governed lifecycle
# ---------------------------------------------------------------------------


class Flow:
    """Drives the standard lifecycle so each test can stop where it means
    to.

    Each step returns its own result and leaves the fixture in a state the
    next step can continue from - which is what lets a test say "get to
    approved, then try to publish without an authorization" in two lines
    instead of thirty."""

    def __init__(self, *, kind: DocumentKind = DocumentKind.MEETING_MINUTES) -> None:
        self.f = Fixture()
        self.kind = kind
        self.document_id = uuid4()
        self.minute = 0

    def _clock(self):
        self.minute += 1
        return clock_at(self.minute)

    def register(self, **overrides):
        return app.register_document(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.custodian)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            kind=self.kind,
            sensitivity=overrides.pop("sensitivity", SensitivityClass.INTERNAL),
            title_reference="title-ref-1",
            reason=reason("DOCUMENT_REGISTERED"),
            review_policy_reference="review-policy/minutes",
            **overrides,
        )

    def record(self, content: bytes = b"minutes v1", **overrides):
        return app.record_version(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.author)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_id=overrides.pop("version_id", uuid4()),
            content=content,
            media_type="text/plain",
            title_reference="title-ref-1",
            provenance=provenance(),
            reason=reason("DOCUMENT_VERSION_RECORDED"),
            **overrides,
        )

    def submit(self, number: int = 1, **overrides):
        return app.submit_for_review(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.author)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_number=number,
            reason=reason("DOCUMENT_SUBMITTED_FOR_REVIEW"),
        )

    def review(self, kind: ReviewKind, number: int = 1, **overrides):
        reviewer = overrides.pop(
            "reviewer", self.f.legal_reviewer if kind is ReviewKind.LEGAL else self.f.reviewer
        )
        return app.record_review(
            self.f.stores,
            context=overrides.pop("context", self.f.context(reviewer)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_number=number,
            review_id=uuid4(),
            review_kind=kind,
            outcome=overrides.pop("outcome", ReviewOutcome.NO_FINDING),
            reason=reason("DOCUMENT_REVIEW_RECORDED"),
            **overrides,
        )

    def review_all(self, number: int = 1) -> None:
        requirement = self.f.stores.documents.get(self.document_id).review_requirement
        for kind in sorted(requirement.required_kinds, key=str):
            self.review(kind, number)

    def approve(self, number: int = 1, **overrides):
        return app.approve_version(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.approver)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_number=number,
            approval_id=overrides.pop("approval_id", uuid4()),
            reason=reason("DOCUMENT_VERSION_APPROVED"),
        )

    def authorize_publication(self, number: int = 1, **overrides):
        return app.authorize_publication(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.publisher)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_number=number,
            authorization_id=uuid4(),
            audience=overrides.pop("audience", PublicationAudience.PUBLIC),
            disclosure_obligation_reference="satzung-12-3",
            reason=reason("DOCUMENT_PUBLICATION_AUTHORIZED"),
        )

    def publish(self, number: int = 1, **overrides):
        return app.publish_version(
            self.f.stores,
            context=overrides.pop("context", self.f.context(self.f.publisher)),
            port=self.f.port,
            clock=self._clock(),
            document_id=self.document_id,
            version_number=number,
            reason=reason("DOCUMENT_PUBLISHED"),
        )

    def to_approved(self):
        self.register()
        self.record()
        self.submit()
        self.review_all()
        return self.approve()

    def to_published(self):
        self.to_approved()
        self.authorize_publication()
        return self.publish()


# ---------------------------------------------------------------------------
# The guard frame
# ---------------------------------------------------------------------------


def test_an_undetermined_scope_denies_before_anything_else() -> None:
    """Check 1 of the frame: refused before any read and any write."""
    flow = Flow()
    with pytest.raises(OrganizationScopeUndeterminedError):
        flow.register(
            context=RequestContext(scope=None, authorities=(flow.f.custodian,), event_id=uuid4())
        )
    assert flow.f.stores.sink.published() == ()


def test_a_wrong_role_denies() -> None:
    flow = Flow()
    with pytest.raises(DocumentAuthorityMissingError):
        flow.register(context=flow.f.context(flow.f.reviewer))


def test_an_undeclared_conflict_fails_closed() -> None:
    """Every command is treated as a protected action, which is stricter
    than necessary and never softer."""
    flow = Flow()
    with pytest.raises(ConflictOfInterestUndeclaredError):
        flow.register(
            context=RequestContext(
                scope=flow.f.scope,
                authorities=(flow.f.custodian,),
                conflict=None,
                event_id=uuid4(),
            )
        )


def test_a_missing_event_id_is_refused() -> None:
    flow = Flow()
    with pytest.raises(IdempotencyConflictError):
        flow.register(
            context=RequestContext(
                scope=flow.f.scope,
                authorities=(flow.f.custodian,),
                conflict=ConflictDeclaration(state="none", declared_by="a"),
                event_id=None,
            )
        )


def test_a_replayed_command_does_not_act_twice() -> None:
    """The same `event_id` with the same content returns the recorded
    aggregate without re-running the transition."""
    flow = Flow()
    flow.register()
    flow.record()
    context = flow.f.context(flow.f.author)
    version_id = uuid4()
    first = flow.record(content=b"minutes v2", context=context, version_id=version_id)
    published_before = len(flow.f.stores.sink.published())
    second = flow.record(content=b"minutes v2", context=context, version_id=version_id)
    assert second.version.version_id == first.version.version_id
    assert len(flow.f.stores.sink.published()) == published_before
    assert len(flow.f.stores.versions.list_for_document(flow.document_id)) == 2


def test_the_same_event_id_with_different_content_conflicts() -> None:
    flow = Flow()
    flow.register()
    context = flow.f.context(flow.f.author)
    version_id = uuid4()
    flow.record(content=b"minutes v1", context=context, version_id=version_id)
    with pytest.raises(IdempotencyConflictError):
        flow.record(content=b"different content", context=context, version_id=version_id)


def test_optimistic_concurrency_is_enforced_on_the_document() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    with pytest.raises(OptimisticConcurrencyConflictError):
        flow.record(content=b"minutes v2", expected_document_version=999)


def test_audit_is_appended_before_the_event_is_published() -> None:
    """An event that reached the stream without an audit row is an act
    nobody can account for."""
    flow = Flow()
    result = flow.register()
    assert flow.f.stores.audit.get_by_event_id(result.audit_event.audit_event_id) is not None
    assert flow.f.stores.audit.verify_chain().is_intact is True


def test_every_command_leaves_an_audit_row_and_one_event() -> None:
    flow = Flow()
    flow.to_published()
    audit_rows = flow.f.stores.audit.list_all()
    assert len(audit_rows) == len(flow.f.stores.sink.published())
    assert all(row.source_service == "document-service" for row in audit_rows)
    assert all(row.policy_version == app.AUDIT_POLICY_VERSION for row in audit_rows)


def test_the_audit_actor_is_the_authority_and_never_a_person() -> None:
    flow = Flow()
    result = flow.register()
    assert result.audit_event.actor_type == "organizational_authority"
    assert result.audit_event.actor_id == flow.f.custodian.authority_id


# ---------------------------------------------------------------------------
# Two-tier scope errors
# ---------------------------------------------------------------------------


def test_a_foreign_document_is_reported_exactly_as_a_missing_one() -> None:
    """Distinguishing them would let a caller confirm the existence of
    another organization's documents by probing identifiers."""
    flow = Flow()
    flow.register()

    other = Fixture()
    other.stores = flow.f.stores
    other_custodian = authority(DocumentRole.DOCUMENT_CUSTODIAN, other.scope, other.port)

    with pytest.raises(DocumentRecordNotFoundError) as foreign:
        app.record_version(
            other.stores,
            context=other.context(other_custodian),
            port=other.port,
            clock=clock_at(9),
            document_id=flow.document_id,
            version_id=uuid4(),
            content=b"x",
            media_type="text/plain",
            title_reference="t",
            provenance=provenance(),
            reason=reason("DOCUMENT_VERSION_RECORDED"),
        )
    with pytest.raises(DocumentRecordNotFoundError) as missing:
        app.record_version(
            other.stores,
            context=other.context(other_custodian),
            port=other.port,
            clock=clock_at(9),
            document_id=uuid4(),
            version_id=uuid4(),
            content=b"x",
            media_type="text/plain",
            title_reference="t",
            provenance=provenance(),
            reason=reason("DOCUMENT_VERSION_RECORDED"),
        )
    assert str(foreign.value).split(" id ")[0] == str(missing.value).split(" id ")[0]


# ---------------------------------------------------------------------------
# The lifecycle
# ---------------------------------------------------------------------------


def test_the_full_lifecycle_reaches_published() -> None:
    flow = Flow()
    result = flow.to_published()
    assert result.version.state is VersionState.PUBLISHED
    document = flow.f.stores.documents.get(flow.document_id)
    assert document.current_version_number == 1
    assert document.version_count == 1


def test_content_is_stored_and_retrievable_by_its_digest() -> None:
    flow = Flow()
    flow.register()
    result = flow.record(content=b"the actual minutes")
    assert flow.f.stores.content.get(result.version.content.digest) == b"the actual minutes"
    assert result.version.content.digest == content_digest_of(b"the actual minutes")


def test_approval_requires_every_mandated_review() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    flow.submit()
    flow.review(ReviewKind.EDITORIAL)
    with pytest.raises(DocumentReviewIncompleteError):
        flow.approve()


def test_approval_refuses_while_a_blocking_finding_is_open() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    flow.submit()
    flow.review(ReviewKind.EDITORIAL)
    flow.review(
        ReviewKind.SUBSTANTIVE,
        outcome=ReviewOutcome.BLOCKING_FINDING,
        finding_reference="finding-doc-1",
    )
    with pytest.raises(DocumentReviewIncompleteError):
        flow.approve()


def test_a_review_may_only_be_recorded_on_a_version_in_review() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    with pytest.raises(DocumentTransitionInvalidError):
        flow.review(ReviewKind.EDITORIAL)


def test_publication_requires_its_own_authorization() -> None:
    """Approval is not publication."""
    flow = Flow()
    flow.to_approved()
    with pytest.raises(Exception) as excinfo:
        flow.publish()
    assert "publication" in str(excinfo.value).lower()


def test_publication_authorization_requires_an_approved_version() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    with pytest.raises(DocumentApprovalMissingError):
        flow.authorize_publication()


def test_a_rendition_requires_a_published_version() -> None:
    flow = Flow()
    flow.to_approved()
    with pytest.raises(DocumentApprovalMissingError):
        app.issue_publication_rendition(
            flow.f.stores,
            context=flow.f.context(flow.f.publisher),
            port=flow.f.port,
            clock=clock_at(20),
            document_id=flow.document_id,
            version_number=1,
            rendition_id=uuid4(),
            rendition_content=b"<html/>",
            media_type="text/html",
            reason=reason("DOCUMENT_RENDITION_ISSUED"),
        )


def test_a_rendition_citation_resolves_the_version_it_renders() -> None:
    """ADR-053 interface requirement 4."""
    flow = Flow()
    flow.to_published()
    result = app.issue_publication_rendition(
        flow.f.stores,
        context=flow.f.context(flow.f.publisher),
        port=flow.f.port,
        clock=clock_at(20),
        document_id=flow.document_id,
        version_number=1,
        rendition_id=uuid4(),
        rendition_content=b"<html>minutes</html>",
        media_type="text/html",
        reason=reason("DOCUMENT_RENDITION_ISSUED"),
    )
    version_record = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert result.rendition.source_version_hash == version_record.version_hash
    assert str(flow.document_id) in result.rendition.citation_reference


def test_a_returned_version_is_revised_as_a_new_version() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    flow.submit()
    app.return_for_revision(
        flow.f.stores,
        context=flow.f.context(flow.f.reviewer),
        port=flow.f.port,
        clock=clock_at(10),
        document_id=flow.document_id,
        version_number=1,
        reason=reason("DOCUMENT_RETURNED_FOR_REVISION"),
    )
    second = flow.record(content=b"minutes v2")
    assert second.version.version_number == 2
    first = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert first.state is VersionState.RETURNED_FOR_REVISION


# ---------------------------------------------------------------------------
# Separation of duties, in practice
# ---------------------------------------------------------------------------


def test_incompatible_roles_are_refused_before_separation_is_even_considered() -> None:
    """Two independent defences, and the outer one fires first.

    An actor who holds both author and approver in one scope is refused by
    the *matrix* at the moment of the act - `assert_not_self_approval` is
    never reached, because the act-time role check already denied. That
    ordering matters: the matrix answers "may one person hold both roles?"
    and denies the whole class of act, while separation answers "did one
    person perform both acts?" for role pairs that are legitimately
    combinable."""
    flow = Flow()
    shared = "actor-wearing-two-hats"
    author = authority(
        DocumentRole.DOCUMENT_AUTHOR,
        flow.f.scope,
        flow.f.port,
        actor_reference=shared,
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    flow.register()
    with pytest.raises(AuthorityRoleIncompatibleError):
        flow.record(context=flow.f.context(author))


def test_the_recorder_may_not_approve_their_own_version() -> None:
    """The case the matrix cannot catch, and separation must.

    `document_custodian` and `document_approver` are legitimately
    combinable - custody is administrative, and forcing two people onto
    ordinary record-keeping would buy no governance. But a custodian who
    recorded a version still may not be the approver of it, and only the
    per-act comparison sees that."""
    flow = Flow()
    shared = "actor-custodian-and-approver"
    custodian = authority(
        DocumentRole.DOCUMENT_CUSTODIAN,
        flow.f.scope,
        flow.f.port,
        actor_reference=shared,
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    approver = authority(
        DocumentRole.DOCUMENT_APPROVER,
        flow.f.scope,
        flow.f.port,
        actor_reference=shared,
        also_holds=(DocumentRole.DOCUMENT_CUSTODIAN,),
    )
    flow.register(context=flow.f.context(custodian))
    flow.record(context=flow.f.context(custodian))
    flow.submit(context=flow.f.context(custodian))
    flow.review_all()
    with pytest.raises(SelfApprovalProhibitedError):
        flow.approve(context=flow.f.context(approver))


def test_the_approver_may_not_authorize_publication_of_their_own_approval() -> None:
    """`document_approver` and `publication_officer` are combinable roles,
    so reaching the public still takes two distinct actors even in a small
    organization where one person holds both."""
    flow = Flow()
    shared = "actor-approver-and-publisher"
    approver = authority(
        DocumentRole.DOCUMENT_APPROVER,
        flow.f.scope,
        flow.f.port,
        actor_reference=shared,
        also_holds=(DocumentRole.PUBLICATION_OFFICER,),
    )
    publisher = authority(
        DocumentRole.PUBLICATION_OFFICER,
        flow.f.scope,
        flow.f.port,
        actor_reference=shared,
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    flow.register()
    flow.record()
    flow.submit()
    flow.review_all()
    flow.approve(context=flow.f.context(approver))
    with pytest.raises(SelfApprovalProhibitedError):
        flow.authorize_publication(context=flow.f.context(publisher))


def test_a_reviewer_may_not_also_be_an_approver_at_all() -> None:
    """Reviewer and approver are the pair the matrix forbids outright: the
    three-eyes structure collapses if one person can hold two of the
    three, so this is refused at the role level rather than per act."""
    flow = Flow()
    reviewer = authority(
        DocumentRole.DOCUMENT_REVIEWER,
        flow.f.scope,
        flow.f.port,
        actor_reference="actor-reviewer-and-approver",
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    flow.register()
    flow.record()
    flow.submit()
    with pytest.raises(AuthorityRoleIncompatibleError):
        flow.review(ReviewKind.EDITORIAL, reviewer=reviewer)


def test_a_legal_opinion_requires_a_legal_reviewer() -> None:
    """FIR-PROG-002's foundation, end to end."""
    flow = Flow(kind=DocumentKind.LEGAL_OPINION)
    flow.register()
    flow.record()
    flow.submit()
    with pytest.raises(DocumentAuthorityMissingError):
        flow.review(ReviewKind.EDITORIAL, reviewer=flow.f.reviewer)


# ---------------------------------------------------------------------------
# The integrity precondition
# ---------------------------------------------------------------------------


def test_a_command_refuses_to_act_on_a_document_whose_history_is_broken() -> None:
    """A governed act recorded against a history that no longer verifies
    would add a trustworthy-looking row to an untrustworthy history."""
    flow = Flow()
    flow.register()
    flow.record()
    stored = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    flow.f.stores.versions._by_id[stored.version_id] = tamper(
        stored, title_reference="rewritten-behind-the-service"
    )
    with pytest.raises(DocumentVersionChainBrokenError):
        flow.submit()


def test_verify_document_integrity_reports_a_swapped_content_blob() -> None:
    """The chain alone would pass: the record is untouched and only the
    bytes changed."""
    flow = Flow()
    flow.register()
    result = flow.record(content=b"original minutes")
    flow.f.stores.content._blobs[result.version.content.digest] = b"swapped"
    outcome = app.verify_document_integrity(
        flow.f.stores, document_id=flow.document_id, scope=flow.f.scope
    )
    assert outcome.valid is False
    assert outcome.broken_at_version == 1


def test_verify_document_integrity_reports_missing_content() -> None:
    flow = Flow()
    flow.register()
    result = flow.record()
    del flow.f.stores.content._blobs[result.version.content.digest]
    outcome = app.verify_document_integrity(
        flow.f.stores, document_id=flow.document_id, scope=flow.f.scope
    )
    assert outcome.valid is False
    assert "does not hold" in (outcome.detail or "")


def test_verify_document_integrity_passes_for_an_intact_document() -> None:
    flow = Flow()
    flow.to_published()
    outcome = app.verify_document_integrity(
        flow.f.stores, document_id=flow.document_id, scope=flow.f.scope
    )
    assert outcome.valid is True
    assert outcome.version_count == 1


def test_verify_document_integrity_refuses_a_foreign_document() -> None:
    flow = Flow()
    flow.register()
    with pytest.raises(DocumentRecordNotFoundError):
        app.verify_document_integrity(flow.f.stores, document_id=flow.document_id, scope=scope())


# ---------------------------------------------------------------------------
# Correction, supersession, revocation
# ---------------------------------------------------------------------------


def test_a_correction_leaves_the_corrected_version_untouched() -> None:
    flow = Flow()
    flow.to_approved()
    before = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    result = flow.record(
        content=b"corrected minutes",
        corrects_version_number=1,
        correction_reason=reason("DOCUMENT_VERSION_CORRECTED"),
    )
    after = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert after.version_hash == before.version_hash
    assert after.state is before.state
    assert result.version.corrects_version_number == 1
    assert result.event.event_type == "document_version.corrected"


def test_a_correction_cannot_target_a_missing_version() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    with pytest.raises(DocumentCorrectionTargetInvalidError):
        flow.record(
            content=b"x",
            corrects_version_number=7,
            correction_reason=reason("DOCUMENT_VERSION_CORRECTED"),
        )


def test_supersession_moves_the_current_version_pointer() -> None:
    flow = Flow()
    flow.to_approved()
    flow.record(content=b"minutes v2")
    flow.submit(2)
    flow.review_all(2)
    flow.approve(2)
    app.supersede_version(
        flow.f.stores,
        context=flow.f.context(flow.f.approver),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        superseded_version_number=1,
        superseding_version_number=2,
        supersession_id=uuid4(),
        reason=reason("DOCUMENT_VERSION_SUPERSEDED"),
    )
    document = flow.f.stores.documents.get(flow.document_id)
    assert document.current_version_number == 2
    first = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert first.state is VersionState.SUPERSEDED


def test_an_unapproved_version_cannot_supersede_anything() -> None:
    """ "Superseded by a draft" would make a governed record non-current on
    the strength of something nobody has approved."""
    flow = Flow()
    flow.to_approved()
    flow.record(content=b"minutes v2")
    with pytest.raises(DocumentTransitionInvalidError):
        app.supersede_version(
            flow.f.stores,
            context=flow.f.context(flow.f.approver),
            port=flow.f.port,
            clock=clock_at(30),
            document_id=flow.document_id,
            superseded_version_number=1,
            superseding_version_number=2,
            supersession_id=uuid4(),
            reason=reason("DOCUMENT_VERSION_SUPERSEDED"),
        )


def test_revocation_removes_effect_and_keeps_the_record() -> None:
    flow = Flow()
    flow.to_published()
    before = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    app.revoke_version(
        flow.f.stores,
        context=flow.f.context(flow.f.approver),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        revocation_id=uuid4(),
        reason=reason("DOCUMENT_VERSION_REVOKED"),
    )
    after = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert after.state is VersionState.REVOKED
    assert after.version_hash == before.version_hash
    assert flow.f.stores.content.has(after.content.digest) is True
    assert (
        app.verify_document_integrity(
            flow.f.stores, document_id=flow.document_id, scope=flow.f.scope
        ).valid
        is True
    )


# ---------------------------------------------------------------------------
# Determinations
# ---------------------------------------------------------------------------


def test_a_signature_determination_is_recorded_and_bound_to_the_version() -> None:
    flow = Flow()
    flow.to_approved()
    result = app.determine_signature_status(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        determination_id=uuid4(),
        status=SignatureStatus.SIGNED_VERIFIED,
        form=SignatureForm.QUALIFIED_ELECTRONIC,
        verification_basis_reference="validation-report-7",
        reason=reason("DOCUMENT_SIGNATURE_DETERMINED"),
    )
    version_record = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    assert result.determination.determined_version_hash == version_record.version_hash
    assert (
        app.get_signature_status(
            flow.f.stores, document_id=flow.document_id, version_number=1, scope=flow.f.scope
        )
        is SignatureStatus.SIGNED_VERIFIED
    )


def test_an_absent_signature_determination_reports_not_determined() -> None:
    """ADR-053 requirement 2: absent is reported as absent, never
    inferred."""
    flow = Flow()
    flow.to_approved()
    assert (
        app.get_signature_status(
            flow.f.stores, document_id=flow.document_id, version_number=1, scope=flow.f.scope
        )
        is SignatureStatus.NOT_DETERMINED
    )


def test_a_foreign_scope_gets_not_determined_rather_than_an_answer() -> None:
    flow = Flow()
    flow.to_approved()
    assert (
        app.get_signature_status(
            flow.f.stores, document_id=flow.document_id, version_number=1, scope=scope()
        )
        is SignatureStatus.NOT_DETERMINED
    )


def test_a_signature_form_must_be_a_governed_value() -> None:
    flow = Flow()
    flow.to_approved()
    with pytest.raises(DocumentDeterminationNotPermittedError):
        app.determine_signature_status(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(30),
            document_id=flow.document_id,
            version_number=1,
            determination_id=uuid4(),
            status=SignatureStatus.SIGNED_UNVERIFIED,
            form="a squiggle",
            reason=reason("DOCUMENT_SIGNATURE_DETERMINED"),
        )


def test_admissibility_requires_the_legal_reviewer_role() -> None:
    flow = Flow()
    flow.to_approved()
    with pytest.raises(DocumentAuthorityMissingError):
        app.determine_admissibility(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(30),
            document_id=flow.document_id,
            version_number=1,
            determination_id=uuid4(),
            procedure_reference="case-2026-11",
            status=AdmissibilityStatus.ADMITTED,
            reason=reason("DOCUMENT_ADMISSIBILITY_DETERMINED"),
        )


def test_an_admissibility_answer_is_scoped_to_its_procedure() -> None:
    flow = Flow()
    flow.to_approved()
    app.determine_admissibility(
        flow.f.stores,
        context=flow.f.context(flow.f.legal_reviewer),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        determination_id=uuid4(),
        procedure_reference="case-2026-11",
        status=AdmissibilityStatus.ADMITTED,
        reason=reason("DOCUMENT_ADMISSIBILITY_DETERMINED"),
    )
    assert (
        app.get_admissibility_status(
            flow.f.stores,
            document_id=flow.document_id,
            version_number=1,
            procedure_reference="case-2026-11",
            scope=flow.f.scope,
        )
        is AdmissibilityStatus.ADMITTED
    )
    assert (
        app.get_admissibility_status(
            flow.f.stores,
            document_id=flow.document_id,
            version_number=1,
            procedure_reference="a-different-case",
            scope=flow.f.scope,
        )
        is AdmissibilityStatus.NOT_DETERMINED
    )


# ---------------------------------------------------------------------------
# Reference resolution (ADR-053 requirement 1)
# ---------------------------------------------------------------------------


def test_resolution_reports_existence_and_kind_in_scope() -> None:
    flow = Flow()
    flow.to_approved()
    resolution = app.resolve_document_reference(
        flow.f.stores, reference_document_id=flow.document_id, scope=flow.f.scope
    )
    assert resolution.exists is True
    assert resolution.kind is DocumentKind.MEETING_MINUTES
    assert resolution.current_version_number == 1


def test_resolution_across_scopes_reports_the_same_answer_as_a_missing_document() -> None:
    """A resolution that distinguished them would be a cross-organization
    existence oracle."""
    flow = Flow()
    flow.to_approved()
    foreign = app.resolve_document_reference(
        flow.f.stores, reference_document_id=flow.document_id, scope=scope()
    )
    missing = app.resolve_document_reference(
        flow.f.stores, reference_document_id=uuid4(), scope=flow.f.scope
    )
    assert (foreign.exists, foreign.kind) == (False, None)
    assert (missing.exists, missing.kind) == (False, None)


def test_resolution_reports_a_revoked_current_version() -> None:
    flow = Flow()
    flow.to_published()
    app.revoke_version(
        flow.f.stores,
        context=flow.f.context(flow.f.approver),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        revocation_id=uuid4(),
        reason=reason("DOCUMENT_VERSION_REVOKED"),
    )
    resolution = app.resolve_document_reference(
        flow.f.stores, reference_document_id=flow.document_id, scope=flow.f.scope
    )
    assert resolution.is_revoked is True


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def test_a_draft_cannot_be_registered_as_evidence() -> None:
    flow = Flow()
    flow.register()
    flow.record()
    with pytest.raises(DocumentTransitionInvalidError):
        app.register_evidence(
            flow.f.stores,
            context=flow.f.context(flow.f.evidence_custodian),
            port=flow.f.port,
            clock=clock_at(30),
            document_id=flow.document_id,
            version_number=1,
            evidence_id=uuid4(),
            matter_reference="case-2026-11",
            provenance=provenance(),
            holder_reference="registry-a",
            reason=reason("DOCUMENT_EVIDENCE_REGISTERED"),
        )


def test_evidence_registration_opens_a_custody_chain() -> None:
    flow = Flow()
    flow.to_approved()
    result = app.register_evidence(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        evidence_id=uuid4(),
        matter_reference="case-2026-11",
        provenance=provenance(),
        holder_reference="registry-a",
        reason=reason("DOCUMENT_EVIDENCE_REGISTERED"),
    )
    assert len(result.evidence.custody) == 1
    assert result.evidence.current_holder_reference == "registry-a"


def test_a_sealed_bundle_is_citable_and_immutable() -> None:
    flow = Flow()
    flow.to_approved()
    evidence = app.register_evidence(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        evidence_id=uuid4(),
        matter_reference="case-2026-11",
        provenance=provenance(),
        holder_reference="registry-a",
        reason=reason("DOCUMENT_EVIDENCE_REGISTERED"),
    )
    app.transfer_custody(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(31),
        evidence_id=evidence.evidence.evidence_id,
        action=CustodyAction.TRANSFERRED,
        holder_reference="registry-b",
        reason=reason("DOCUMENT_CUSTODY_TRANSFERRED"),
    )
    bundle = app.seal_evidence_bundle(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(32),
        bundle_id=uuid4(),
        matter_reference="case-2026-11",
        purpose_reference="hearing-bundle",
        evidence_ids=[evidence.evidence.evidence_id],
        reason=reason("DOCUMENT_EVIDENCE_BUNDLE_SEALED"),
    )
    assert bundle.bundle.citation_reference is not None
    bundle.bundle.verify_seal()


def test_custody_transfer_enforces_optimistic_concurrency() -> None:
    flow = Flow()
    flow.to_approved()
    evidence = app.register_evidence(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        version_number=1,
        evidence_id=uuid4(),
        matter_reference="case-2026-11",
        provenance=provenance(),
        holder_reference="registry-a",
        reason=reason("DOCUMENT_EVIDENCE_REGISTERED"),
    )
    with pytest.raises(OptimisticConcurrencyConflictError):
        app.transfer_custody(
            flow.f.stores,
            context=flow.f.context(flow.f.evidence_custodian),
            port=flow.f.port,
            clock=clock_at(31),
            evidence_id=evidence.evidence.evidence_id,
            action=CustodyAction.TRANSFERRED,
            holder_reference="registry-b",
            reason=reason("DOCUMENT_CUSTODY_TRANSFERRED"),
            expected_record_version=99,
        )


# ---------------------------------------------------------------------------
# Retention, hold and disposition
# ---------------------------------------------------------------------------


def test_disposition_is_refused_under_an_active_hold() -> None:
    flow = Flow()
    flow.to_approved()
    app.bind_retention(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        binding=retention_binding(),
        reason=reason("DOCUMENT_RETENTION_BOUND"),
    )
    app.record_legal_hold(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(31),
        document_id=flow.document_id,
        binding=LegalHoldBinding(
            hold_reference="pack-09:hold:1",
            scope=flow.f.scope,
            state=HoldState.ACTIVE,
            observed_at=at(31),
        ),
        reason=reason("DOCUMENT_LEGAL_HOLD_OBSERVED"),
    )
    with pytest.raises(RecordUnderLegalHoldError):
        app.authorize_disposition(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(32),
            document_id=flow.document_id,
            authorization=DispositionAuthorization(
                authorization_reference="pack-09:auth:1",
                scope=flow.f.scope,
                authorized_at=at(32),
                authorized_version_count=1,
                disposition_action="delete",
            ),
            reason=reason("DOCUMENT_DISPOSITION_AUTHORIZED"),
        )


def test_disposition_fails_closed_under_an_indeterminate_hold() -> None:
    flow = Flow()
    flow.to_approved()
    app.bind_retention(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        binding=retention_binding(),
        reason=reason("DOCUMENT_RETENTION_BOUND"),
    )
    app.record_legal_hold(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(31),
        document_id=flow.document_id,
        binding=LegalHoldBinding(
            hold_reference="pack-09:hold:2",
            scope=flow.f.scope,
            state=HoldState.INDETERMINATE,
            observed_at=at(31),
        ),
        reason=reason("DOCUMENT_LEGAL_HOLD_OBSERVED"),
    )
    with pytest.raises(LegalHoldStateUnknownError):
        app.authorize_disposition(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(32),
            document_id=flow.document_id,
            authorization=DispositionAuthorization(
                authorization_reference="pack-09:auth:1",
                scope=flow.f.scope,
                authorized_at=at(32),
                authorized_version_count=1,
                disposition_action="delete",
            ),
            reason=reason("DOCUMENT_DISPOSITION_AUTHORIZED"),
        )


def test_disposition_requires_a_pack_09_authorization_and_closes_the_document() -> None:
    flow = Flow()
    flow.to_approved()
    app.bind_retention(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        binding=retention_binding(),
        reason=reason("DOCUMENT_RETENTION_BOUND"),
    )
    result = app.authorize_disposition(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(32),
        document_id=flow.document_id,
        authorization=DispositionAuthorization(
            authorization_reference="pack-09:auth:1",
            scope=flow.f.scope,
            authorized_at=at(32),
            authorized_version_count=1,
            disposition_action="delete",
        ),
        reason=reason("DOCUMENT_DISPOSITION_AUTHORIZED"),
    )
    assert result.document.state.value == "closed"
    # The record survives the authorization: PACK-11 records the governed
    # half and destroys nothing (PACK-13 owns the data plane).
    assert flow.f.stores.versions.get_by_number(flow.document_id, 1) is not None


def test_disposition_without_a_retention_binding_is_refused() -> None:
    flow = Flow()
    flow.to_approved()
    with pytest.raises(Exception) as excinfo:
        app.authorize_disposition(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(32),
            document_id=flow.document_id,
            authorization=DispositionAuthorization(
                authorization_reference="pack-09:auth:1",
                scope=flow.f.scope,
                authorized_at=at(32),
                authorized_version_count=1,
                disposition_action="delete",
            ),
            reason=reason("DOCUMENT_DISPOSITION_AUTHORIZED"),
        )
    assert "retention" in str(excinfo.value).lower()


def test_a_stale_disposition_authorization_is_refused() -> None:
    flow = Flow()
    flow.to_approved()
    app.bind_retention(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(30),
        document_id=flow.document_id,
        binding=retention_binding(),
        reason=reason("DOCUMENT_RETENTION_BOUND"),
    )
    with pytest.raises(DispositionNotAuthorizedError):
        app.authorize_disposition(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(32),
            document_id=flow.document_id,
            authorization=DispositionAuthorization(
                authorization_reference="pack-09:auth:1",
                scope=flow.f.scope,
                authorized_at=at(32),
                authorized_version_count=5,
                disposition_action="delete",
            ),
            reason=reason("DOCUMENT_DISPOSITION_AUTHORIZED"),
        )
