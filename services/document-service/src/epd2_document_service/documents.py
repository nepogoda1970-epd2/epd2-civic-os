"""The `GovernedDocument` aggregate and its controlled lifecycle
(PACK-11; ADR-055, ADR-057).

`versions` owns what a version *is* and how the chain proves it was not
rewritten. This module owns what happens *around* versions: which one is
current, what review a class of document requires before approval, how
publication is separated from approval, and how correction, supersession
and revocation are recorded so that nothing is ever silently removed.

Pure, like `versions`: no I/O, no clock, no storage. Every function takes
what it needs and returns a new frozen object.

## The separation that matters most

**Approval is not publication and publication is not approval.** They are
two authorities (`DOCUMENT_APPROVER`, `PUBLICATION_OFFICER`), two acts,
two records (`ApprovalRecord`, `PublicationAuthorization`) and two
lifecycle transitions. A single "release" act would be simpler and would
also mean that whoever could approve could publish, which is precisely the
control a governed document register exists to provide. `publish` refuses
without both.

## Why the document holds review *requirements* rather than a review count

`ReviewRequirement` names which review kinds a version of this class must
carry before approval. Approval then checks that every required kind has a
recorded, non-negative review. Counting reviews instead ("at least two")
would let two general reviews stand in for the missing legal one, and
FIR-PROG-002's whole point is that a legal opinion is not substitutable.

## Revocation, and what it does not do

`revoke` removes a version's *effect*. It never removes the version, never
edits it and never breaks the chain: the version stays exactly where it
is, its state becomes `revoked`, and a `RevocationRecord` says who did it,
when and under which reason code. A published version that is revoked
remains publicly representable as a tombstone (see
`versions.PUBLICLY_REPRESENTABLE_STATES`), because a published document
that simply vanished would be a silent retraction of something the public
was already told.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_document_service.domain import (
    OFFICIAL_RECORD_KINDS,
    AuthorityReference,
    DispositionAuthorization,
    DocumentKind,
    LegalHoldBinding,
    OrganizationalScopeRef,
    ReasonCoded,
    RetentionBinding,
    SensitivityClass,
    require_text,
    require_timezone,
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
    RecordUnderLegalHoldError,
    RetentionBindingMissingError,
)
from epd2_document_service.versions import DocumentVersion, VersionState

# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


class ReviewKind(StrEnum):
    """The kinds of review a document version can carry.

    Closed vocabulary, because `ReviewRequirement` refers to it and an
    open string there would let a requirement be satisfied by a review
    whose kind nobody defined."""

    EDITORIAL = "editorial"
    SUBSTANTIVE = "substantive"
    LEGAL = "legal"
    DATA_PROTECTION = "data_protection"
    SECURITY = "security"
    FINANCIAL = "financial"
    ACCESSIBILITY = "accessibility"


class ReviewOutcome(StrEnum):
    """What a recorded review concluded.

    `BLOCKING_FINDING` is not "rejected": a review does not decide the
    document's fate, it states a finding. Whether a blocking finding ends
    the version is the approver's decision, and `approve` refuses while
    one is unresolved."""

    NO_FINDING = "no_finding"
    NON_BLOCKING_FINDING = "non_blocking_finding"
    BLOCKING_FINDING = "blocking_finding"


@dataclass(frozen=True, slots=True)
class ReviewRequirement:
    """Which review kinds a version of this document must carry before it
    may be approved.

    Held on the document rather than derived from the kind at approval
    time, so that a later change to the default requirements for a class
    cannot retroactively invalidate documents already approved under the
    old ones - the same reasoning PACK-09 applies to retention policy
    versions."""

    required_kinds: frozenset[ReviewKind]
    policy_reference: str
    policy_version: int

    def __post_init__(self) -> None:
        require_text(self.policy_reference, "policy_reference")
        if self.policy_version < 1:
            raise DocumentFieldInvalidError("policy_version must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {
            "required_review_kinds": sorted(str(k) for k in self.required_kinds),
            "review_policy_reference": self.policy_reference,
            "review_policy_version": self.policy_version,
        }


def default_review_requirement(
    kind: DocumentKind, *, policy_reference: str, policy_version: int
) -> ReviewRequirement:
    """The review kinds this service will not let a class of document skip.

    A floor, not a legal threshold. It encodes two things the register
    already asks for - an official record gets a substantive review, and a
    legal or expert opinion gets a legal one (FIR-PROG-002) - and leaves
    everything else to the caller's own policy. This function claims no
    knowledge of what German party law requires of any document."""
    required: set[ReviewKind] = {ReviewKind.EDITORIAL}
    if kind in OFFICIAL_RECORD_KINDS:
        required.add(ReviewKind.SUBSTANTIVE)
    if kind in {DocumentKind.LEGAL_OPINION, DocumentKind.EXPERT_OPINION}:
        required.add(ReviewKind.LEGAL)
    if kind is DocumentKind.PUBLIC_TRANSPARENCY_DOCUMENT:
        required.add(ReviewKind.DATA_PROTECTION)
    return ReviewRequirement(
        required_kinds=frozenset(required),
        policy_reference=policy_reference,
        policy_version=policy_version,
    )


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    """One recorded review of one version.

    Immutable. A reviewer who changes their mind records a *second*
    review; the first stays, because "the reviewer originally found X"
    is exactly the kind of fact a governed register must not lose."""

    review_id: UUID
    document_id: UUID
    version_number: int
    scope: OrganizationalScopeRef
    review_kind: ReviewKind
    outcome: ReviewOutcome
    reviewed_at: datetime
    reviewer: AuthorityReference
    reason: ReasonCoded
    finding_reference: str | None = None
    resolves_review_id: UUID | None = None

    def __post_init__(self) -> None:
        require_timezone(self.reviewed_at, context="ReviewRecord.reviewed_at")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")
        if self.outcome is not ReviewOutcome.NO_FINDING and not self.finding_reference:
            raise DocumentFieldInvalidError(
                "a review reporting a finding must carry a finding_reference - a finding with "
                "nowhere to read it is not a finding"
            )

    @property
    def is_blocking(self) -> bool:
        return self.outcome is ReviewOutcome.BLOCKING_FINDING

    def to_payload(self) -> dict[str, object]:
        return {
            "review_id": str(self.review_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "review_kind": str(self.review_kind),
            "outcome": str(self.outcome),
            "reviewed_at": self.reviewed_at.isoformat(),
            "reviewer": self.reviewer.to_payload(),
            "reason": self.reason.to_payload(),
            "finding_reference": self.finding_reference,
            "resolves_review_id": (
                None if self.resolves_review_id is None else str(self.resolves_review_id)
            ),
        }


def unresolved_blocking_reviews(reviews: tuple[ReviewRecord, ...]) -> tuple[ReviewRecord, ...]:
    """The blocking findings that no later review has resolved.

    A blocking review is resolved by a later review that names it in
    `resolves_review_id` and does not itself block. Resolution is
    therefore an explicit, attributed act - not an implicit consequence of
    somebody recording a cheerful second opinion."""
    resolved = {
        review.resolves_review_id
        for review in reviews
        if review.resolves_review_id is not None and not review.is_blocking
    }
    return tuple(r for r in reviews if r.is_blocking and r.review_id not in resolved)


def assert_review_complete(
    requirement: ReviewRequirement, reviews: tuple[ReviewRecord, ...], *, version_number: int
) -> None:
    """Raise unless every required review kind is present for this version
    and no blocking finding is unresolved."""
    for_version = tuple(r for r in reviews if r.version_number == version_number)
    present = {r.review_kind for r in for_version}
    missing = requirement.required_kinds - present
    if missing:
        raise DocumentReviewIncompleteError(
            "approval requires a recorded review of each of: "
            + ", ".join(sorted(k.value for k in missing))
        )
    blocking = unresolved_blocking_reviews(for_version)
    if blocking:
        raise DocumentReviewIncompleteError(
            f"{len(blocking)} unresolved blocking review finding(s) on version {version_number}"
        )


# ---------------------------------------------------------------------------
# Approval, publication authorization, renditions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """The act that turns a proposed version into a record.

    Bound to `approved_version_hash`: the approval names the exact bytes
    and metadata it approved. If the version's recomputed hash ever
    differs from this, the approval no longer describes what is stored,
    and `assert_approval_current` refuses rather than letting an approval
    drift onto content nobody approved."""

    approval_id: UUID
    document_id: UUID
    version_number: int
    scope: OrganizationalScopeRef
    approved_at: datetime
    approver: AuthorityReference
    approved_version_hash: str
    reason: ReasonCoded

    def __post_init__(self) -> None:
        require_timezone(self.approved_at, context="ApprovalRecord.approved_at")
        require_text(self.approved_version_hash, "approved_version_hash")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {
            "approval_id": str(self.approval_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "approved_at": self.approved_at.isoformat(),
            "approver": self.approver.to_payload(),
            "approved_version_hash": self.approved_version_hash,
            "reason": self.reason.to_payload(),
        }


def assert_approval_current(approval: ApprovalRecord, version: DocumentVersion) -> None:
    """Raise unless `approval` still describes `version` as stored."""
    if approval.version_number != version.version_number:
        raise DocumentApprovalMissingError(
            "the approval on file was issued for a different version number"
        )
    if approval.approved_version_hash != version.version_hash:
        raise DocumentApprovalMissingError(
            "the approval on file names a different version hash than the stored version - the "
            "approval does not describe what is stored"
        )


class PublicationAudience(StrEnum):
    """Who a publication is for.

    `PUBLIC` is the only audience the public projection will emit; the
    others exist so that "published to the membership" is a recordable,
    distinguishable fact rather than a half-public state nobody can
    query."""

    PUBLIC = "public"
    MEMBERS = "members"
    BODY_INTERNAL = "body_internal"
    ADDRESSEE_ONLY = "addressee_only"


@dataclass(frozen=True, slots=True)
class PublicationAuthorization:
    """The separate authority to publish an approved version.

    Requires a `disclosure_obligation_reference`: this service does not
    decide what must or may be published - that is a legal question - and
    refuses to proceed without the caller naming the obligation or
    decision it is acting under. A publication with no stated basis is one
    nobody can later be held to."""

    authorization_id: UUID
    document_id: UUID
    version_number: int
    scope: OrganizationalScopeRef
    audience: PublicationAudience
    authorized_at: datetime
    authorized_by: AuthorityReference
    disclosure_obligation_reference: str
    reason: ReasonCoded

    def __post_init__(self) -> None:
        require_timezone(self.authorized_at, context="PublicationAuthorization.authorized_at")
        require_text(
            self.disclosure_obligation_reference, "disclosure_obligation_reference"
        )
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {
            "publication_authorization_id": str(self.authorization_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "audience": str(self.audience),
            "authorized_at": self.authorized_at.isoformat(),
            "authorized_by": self.authorized_by.to_payload(),
            "disclosure_obligation_reference": self.disclosure_obligation_reference,
            "reason": self.reason.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class PublicationRendition:
    """A citable identifier for a published form of a version.

    **This is ADR-053's fourth PACK-11 interface requirement**: "produce a
    publication rendition identifier that a public finance view can cite
    without exposing document content". `rendition_digest` identifies the
    rendition's bytes; the bytes themselves live in the content store and
    never travel with the identifier.

    A rendition is derived and non-authoritative. The authoritative object
    is the approved version; a rendition is one presentation of it, and
    `source_version_hash` binds the two so a citation can always be
    checked back to what it claims to render."""

    rendition_id: UUID
    document_id: UUID
    version_number: int
    scope: OrganizationalScopeRef
    audience: PublicationAudience
    media_type: str
    rendition_digest: str
    source_version_hash: str
    issued_at: datetime
    issued_by: AuthorityReference

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, context="PublicationRendition.issued_at")
        require_text(self.media_type, "media_type")
        require_text(self.rendition_digest, "rendition_digest")
        require_text(self.source_version_hash, "source_version_hash")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")

    @property
    def citation_reference(self) -> str:
        """The opaque string a consuming pack cites.

        Deliberately carries the document, the version and the rendition
        and nothing else: a consumer can quote it, resolve it through this
        service and get back existence, kind and audience - never
        content."""
        return f"epd2-doc:{self.document_id}:v{self.version_number}:r{self.rendition_id}"

    def to_payload(self) -> dict[str, object]:
        return {
            "rendition_id": str(self.rendition_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "audience": str(self.audience),
            "media_type": self.media_type,
            "rendition_digest": self.rendition_digest,
            "source_version_hash": self.source_version_hash,
            "issued_at": self.issued_at.isoformat(),
            "citation_reference": self.citation_reference,
        }


# ---------------------------------------------------------------------------
# Supersession, correction, revocation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SupersessionRecord:
    """"Version N is no longer the current statement; version M is."

    Explicit and stored, rather than inferred from "M has the highest
    number". Inference would be wrong exactly when it matters: a version
    can be recorded and never approved, and the highest-numbered version
    is then not the current one."""

    supersession_id: UUID
    document_id: UUID
    scope: OrganizationalScopeRef
    superseded_version_number: int
    superseding_version_number: int
    recorded_at: datetime
    recorded_by: AuthorityReference
    reason: ReasonCoded

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, context="SupersessionRecord.recorded_at")
        if self.superseded_version_number < 1 or self.superseding_version_number < 1:
            raise DocumentSupersessionInvalidError("version numbers must be positive integers")
        if self.superseding_version_number <= self.superseded_version_number:
            raise DocumentSupersessionInvalidError(
                "the superseding version must be later than the superseded one"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "supersession_id": str(self.supersession_id),
            "document_id": str(self.document_id),
            "superseded_version_number": self.superseded_version_number,
            "superseding_version_number": self.superseding_version_number,
            "recorded_at": self.recorded_at.isoformat(),
            "recorded_by": self.recorded_by.to_payload(),
            "reason": self.reason.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class RevocationRecord:
    """"This version no longer has effect."

    Note what is absent: any field that could mean "and it is gone".
    Revocation is a statement about effect, and the material it concerns
    stays readable to authorized readers exactly as before."""

    revocation_id: UUID
    document_id: UUID
    scope: OrganizationalScopeRef
    version_number: int
    revoked_at: datetime
    revoked_by: AuthorityReference
    reason: ReasonCoded
    replacement_version_number: int | None = None

    def __post_init__(self) -> None:
        require_timezone(self.revoked_at, context="RevocationRecord.revoked_at")
        if self.version_number < 1:
            raise DocumentRevocationInvalidError("version_number must be a positive integer")
        if (
            self.replacement_version_number is not None
            and self.replacement_version_number <= self.version_number
        ):
            raise DocumentRevocationInvalidError(
                "a replacement version must be later than the revoked one"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "revocation_id": str(self.revocation_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "revoked_at": self.revoked_at.isoformat(),
            "revoked_by": self.revoked_by.to_payload(),
            "reason": self.reason.to_payload(),
            "replacement_version_number": self.replacement_version_number,
        }


# ---------------------------------------------------------------------------
# The aggregate
# ---------------------------------------------------------------------------


class DocumentState(StrEnum):
    """The lifecycle of the document as a whole, distinct from any one
    version's.

    `CLOSED` means no further versions may be recorded - the proceeding
    the document belongs to is over. `DISPOSED` means PACK-09 authorized a
    disposition and it was executed; the document record survives as a
    tombstone with its history, because a governed disposal that left no
    trace would be indistinguishable from a deletion."""

    ACTIVE = "active"
    CLOSED = "closed"
    DISPOSED = "disposed"


_ALLOWED_DOCUMENT_TRANSITIONS: frozenset[tuple[DocumentState, DocumentState]] = frozenset(
    {
        (DocumentState.ACTIVE, DocumentState.CLOSED),
        (DocumentState.CLOSED, DocumentState.ACTIVE),
        (DocumentState.CLOSED, DocumentState.DISPOSED),
    }
)


def resolve_document_state(value: str) -> DocumentState:
    try:
        return DocumentState(value)
    except ValueError as exc:
        raise DocumentStateUnknownError(f"unknown document state {value!r}") from exc


@dataclass(frozen=True, slots=True)
class DocumentHistoryEntry:
    """One append-only entry in the document's own history."""

    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    authority: AuthorityReference
    state_after: DocumentState

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="DocumentHistoryEntry.occurred_at")
        require_text(self.action, "action")
        if self.sequence < 1:
            raise DocumentFieldInvalidError("sequence must be a positive integer")

    def to_state(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "action": self.action,
            "reason": self.reason.to_payload(),
            "authority": self.authority.to_state(),
            "state_after": str(self.state_after),
        }


@dataclass(frozen=True, slots=True)
class GovernedDocument:
    """A document owned by one organization, holding an immutable,
    hash-linked sequence of versions.

    The aggregate holds *pointers and governance*, not versions: the
    versions live in their own store, keyed by document. That split is
    what keeps a document with two hundred versions from being one
    object that has to be loaded whole to answer "what is the current
    version number?".

    `head_version_hash` is the chain head, kept here so a caller can
    detect a rewritten history without loading every version - and so
    that an external anchor for the head has one obvious place to be
    recorded when a later round adds one."""

    document_id: UUID
    scope: OrganizationalScopeRef
    kind: DocumentKind
    sensitivity: SensitivityClass
    title_reference: str
    created_at: datetime
    custodian: AuthorityReference
    review_requirement: ReviewRequirement
    state: DocumentState = DocumentState.ACTIVE
    document_version: int = 1
    current_version_number: int | None = None
    version_count: int = 0
    head_version_hash: str = "0" * 64
    retention: RetentionBinding | None = None
    legal_holds: tuple[LegalHoldBinding, ...] = ()
    subject_reference: str | None = None
    history: tuple[DocumentHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.title_reference, "title_reference")
        require_timezone(self.created_at, context="GovernedDocument.created_at")
        if self.document_version < 1:
            raise DocumentFieldInvalidError("document_version must be a positive integer")
        if self.version_count < 0:
            raise DocumentFieldInvalidError("version_count must be non-negative")
        if self.current_version_number is not None and self.current_version_number < 1:
            raise DocumentFieldInvalidError("current_version_number must be a positive integer")
        if self.subject_reference is not None:
            require_text(self.subject_reference, "subject_reference")

    # -- helpers -------------------------------------------------------

    @property
    def is_under_active_hold(self) -> bool:
        return any(h.blocks_destruction for h in self.legal_holds)

    @property
    def has_undetermined_hold(self) -> bool:
        return any(h.is_undetermined for h in self.legal_holds)

    def _appended(
        self,
        *,
        at: datetime,
        action: str,
        reason: ReasonCoded,
        authority: AuthorityReference,
        state: DocumentState | None = None,
        current_version_number: int | None = None,
        version_count: int | None = None,
        head_version_hash: str | None = None,
        retention: RetentionBinding | None = None,
        legal_holds: tuple[LegalHoldBinding, ...] | None = None,
    ) -> GovernedDocument:
        """One private tail for every mutation, so no method can forget to
        append history or to advance the optimistic-concurrency version.

        Every changeable field is an explicit, typed parameter rather than
        a `**changes` bag. A bag would type-check as `object` and let a
        misspelled field name become a silent no-op - which on an
        aggregate whose whole job is not losing facts is the worst
        possible failure mode."""
        target = self.state if state is None else state
        entry = DocumentHistoryEntry(
            sequence=len(self.history) + 1,
            occurred_at=at,
            action=action,
            reason=reason,
            authority=authority,
            state_after=target,
        )
        return replace(
            self,
            state=target,
            document_version=self.document_version + 1,
            history=(*self.history, entry),
            current_version_number=(
                self.current_version_number
                if current_version_number is None
                else current_version_number
            ),
            version_count=self.version_count if version_count is None else version_count,
            head_version_hash=(
                self.head_version_hash if head_version_hash is None else head_version_hash
            ),
            retention=self.retention if retention is None else retention,
            legal_holds=self.legal_holds if legal_holds is None else legal_holds,
        )

    # -- governed transitions ------------------------------------------

    def with_recorded_version(
        self, version: DocumentVersion, *, at: datetime, reason: ReasonCoded
    ) -> GovernedDocument:
        """Advance the head after a new version was sealed and stored."""
        if self.state is not DocumentState.ACTIVE:
            raise DocumentTransitionInvalidError(
                f"no version may be recorded on a {self.state.value} document"
            )
        if version.document_id != self.document_id:
            raise DocumentFieldInvalidError("the version belongs to a different document")
        self.scope.assert_matches(version.scope)
        if version.version_number != self.version_count + 1:
            raise DocumentTransitionInvalidError(
                f"expected version {self.version_count + 1}, got {version.version_number}"
            )
        return self._appended(
            at=at,
            action="version_recorded",
            reason=reason,
            authority=version.recorded_by,
            version_count=version.version_number,
            head_version_hash=version.version_hash,
        )

    def with_current_version(
        self,
        version_number: int,
        *,
        at: datetime,
        reason: ReasonCoded,
        authority: AuthorityReference,
    ) -> GovernedDocument:
        """Move the "this is the current statement" pointer."""
        if version_number < 1 or version_number > self.version_count:
            raise DocumentCorrectionTargetInvalidError(
                f"version {version_number} does not exist on this document"
            )
        return self._appended(
            at=at,
            action="current_version_changed",
            reason=reason,
            authority=authority,
            current_version_number=version_number,
        )

    def with_retention(
        self,
        binding: RetentionBinding,
        *,
        at: datetime,
        reason: ReasonCoded,
        authority: AuthorityReference,
    ) -> GovernedDocument:
        return self._appended(
            at=at,
            action="retention_bound",
            reason=reason,
            authority=authority,
            retention=binding,
        )

    def with_legal_hold(
        self,
        binding: LegalHoldBinding,
        *,
        at: datetime,
        reason: ReasonCoded,
        authority: AuthorityReference,
    ) -> GovernedDocument:
        """Record PACK-09's answer about a hold, replacing any previous
        observation of the *same* hold.

        Replacing by `hold_reference` rather than appending is deliberate:
        two observations of one hold are not two holds, and keeping both
        would leave a released hold looking active forever."""
        self.scope.assert_matches(binding.scope)
        kept = tuple(h for h in self.legal_holds if h.hold_reference != binding.hold_reference)
        return self._appended(
            at=at,
            action="legal_hold_observed",
            reason=reason,
            authority=authority,
            legal_holds=(*kept, binding),
        )

    def with_state(
        self,
        target: DocumentState,
        *,
        at: datetime,
        reason: ReasonCoded,
        authority: AuthorityReference,
    ) -> GovernedDocument:
        if (self.state, target) not in _ALLOWED_DOCUMENT_TRANSITIONS:
            raise DocumentTransitionInvalidError(
                f"invalid document transition {self.state.value} -> {target.value}"
            )
        return self._appended(
            at=at,
            action=f"document_{target.value}",
            reason=reason,
            authority=authority,
            state=target,
        )

    def to_state_payload(self) -> dict[str, object]:
        """The complete, canonically-hashable snapshot used for audit
        `before_hash`/`after_hash`. Covers every field, deliberately: a
        snapshot that is only nearly complete leaves the omitted fields
        outside the tamper-evidence hash and signals nothing about the
        gap."""
        return {
            "document_id": str(self.document_id),
            "scope": self.scope.to_payload(),
            "kind": str(self.kind),
            "sensitivity": str(self.sensitivity),
            "title_reference": self.title_reference,
            "created_at": self.created_at.isoformat(),
            "custodian": self.custodian.to_state(),
            "review_requirement": self.review_requirement.to_payload(),
            "state": str(self.state),
            "document_version": self.document_version,
            "current_version_number": self.current_version_number,
            "version_count": self.version_count,
            "head_version_hash": self.head_version_hash,
            "retention": None if self.retention is None else self.retention.to_payload(),
            "legal_holds": [h.to_payload() for h in self.legal_holds],
            "subject_reference": self.subject_reference,
            "history": [entry.to_state() for entry in self.history],
        }


# ---------------------------------------------------------------------------
# Cross-cutting guards
# ---------------------------------------------------------------------------


def assert_publishable(
    document: GovernedDocument,
    version: DocumentVersion,
    approval: ApprovalRecord | None,
    authorization: PublicationAuthorization | None,
) -> None:
    """The full publication gate, in one function so no command can
    assemble a partial version of it.

    Order is deliberate: approval before authorization, because
    "authorized to publish something that was never approved" is the
    error worth naming first."""
    if version.state is VersionState.PUBLISHED:
        raise DocumentAlreadyPublishedError(
            f"version {version.version_number} of document {document.document_id} is already "
            "published; a republication is a new version, not an overwrite"
        )
    if approval is None:
        raise DocumentApprovalMissingError(
            "publication requires an approval decision on this exact version"
        )
    assert_approval_current(approval, version)
    if authorization is None:
        raise DocumentPublicationNotAuthorizedError(
            "publication requires its own publication authorization - approval is not "
            "publication"
        )
    if authorization.version_number != version.version_number:
        raise DocumentPublicationNotAuthorizedError(
            "the publication authorization on file was issued for a different version"
        )
    document.scope.assert_matches(authorization.scope)


def assert_no_destruction_under_hold(document: GovernedDocument) -> None:
    """Refuse any destructive act while a hold applies or is unknown.

    Two distinct refusals rather than one: a known active hold and an
    unconfirmable hold are different facts, and collapsing them would let
    "we could not reach PACK-09" be read later as "there was a hold"."""
    if document.has_undetermined_hold:
        raise LegalHoldStateUnknownError(
            f"document {document.document_id} is covered by a legal hold whose state could not "
            "be confirmed - destruction fails closed"
        )
    if document.is_under_active_hold:
        raise RecordUnderLegalHoldError(
            f"document {document.document_id} is under an active legal hold"
        )


def assert_disposition_authorized(
    document: GovernedDocument, authorization: DispositionAuthorization | None
) -> DispositionAuthorization:
    """Raise unless a current PACK-09 destruction authorization covers this
    document as it stands now.

    An authorization issued against a smaller version count is stale, not
    merely old: PACK-09 authorized the disposal of material it had seen,
    and versions added afterwards are material it did not."""
    if document.retention is None:
        raise RetentionBindingMissingError(
            "a document with no retention binding cannot be disposed of - no schedule applies"
        )
    if authorization is None:
        raise DispositionNotAuthorizedError(
            "disposition requires a PACK-09 destruction authorization; this service never "
            "authorizes its own disposals"
        )
    document.scope.assert_matches(authorization.scope)
    if authorization.authorized_version_count != document.version_count:
        raise DispositionNotAuthorizedError(
            f"the destruction authorization covers {authorization.authorized_version_count} "
            f"version(s); the document now has {document.version_count} - the authorization "
            "is stale and must be re-issued"
        )
    return authorization
