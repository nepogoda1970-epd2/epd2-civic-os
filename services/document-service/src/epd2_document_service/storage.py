"""Storage ports and in-memory reference adapters (PACK-11).

Same shape PACK-02 through PACK-10 already established: one explicit
`Protocol` per aggregate, plus a deliberately simple in-memory adapter.
**No production persistence is introduced here** - real databases,
migrations, outbox tables and the production event plane stay assigned to
PACK-13.

Six storage rules are load-bearing for this pack's own invariants and are
therefore enforced *by the store*, not merely by convention.

1. **No delete method exists anywhere in this module** - not on a port,
   not on an adapter. FIR-INV-010 makes a stored version permanent and
   PACK-09's legal hold outranks any wish to destroy, so a port that
   offered `delete` would be publishing an act the domain forbids and
   inviting an adapter to implement it. The single module-level
   `delete_document_record` exists to *refuse*.
2. **Scope isolation by default.** Every query that can return more than
   one record takes a required keyword-only
   `scope: OrganizationalScopeRef` and filters on it. There is no
   "list everything" overload: a read with no scope is not a broader
   query, it is a missing authorization boundary. Single-record `get`
   returns whatever is stored under that id and leaves the scope
   assertion to the application layer - only the application layer knows
   which scope the *caller* presented.
3. **Append-only where the domain is append-only.** `DocumentVersionStore.
   append` refuses to replace a stored version at all, and refuses a
   version whose number is not exactly one past the head or whose
   `previous_version_hash` is not the head's hash. That is the storage-side
   half of FIR-INV-010: `versions.verify_version_chain` detects a rewrite
   after the fact, and this refuses to perform one in the first place.
4. **The content store is content-addressed and write-once.** `ContentStore.
   put` keyed by digest; putting different bytes under an existing digest
   is impossible by construction, and putting the same bytes twice is a
   no-op. This is what makes a version's `content.digest` a durable join
   rather than a hopeful one.
5. **Optimistic concurrency is the application layer's job.** No version
   column is invented here. `GovernedDocument.document_version` and
   `EvidenceRecord.record_version` already carry that state, so an
   `expected_*_version` check belongs where the command is decided. Two
   places able to answer "is this stale?" differently is worse than one.
6. **The in-memory adapters are reference implementations, not a data
   plane.** Not concurrency-safe, not durable, and they hold every record
   as a live object reference rather than a serialised row.

What this module does *not* contain: no store consults an authority, a
policy, a legal hold or a retention schedule, because a storage adapter
that quietly refused a write on governed grounds would be a second,
invisible decision point next to `application`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_audit_core.storage import AuditEventStore
from epd2_core.event_envelope import EventEnvelope
from epd2_document_service.determinations import (
    AdmissibilityDetermination,
    SignatureDetermination,
)
from epd2_document_service.documents import (
    ApprovalRecord,
    GovernedDocument,
    PublicationAuthorization,
    PublicationRendition,
    ReviewRecord,
    RevocationRecord,
    SupersessionRecord,
)
from epd2_document_service.domain import (
    OrganizationalScopeRef,
    content_digest_of,
    require_digest,
    require_timezone,
)
from epd2_document_service.evidence import EvidenceBundle, EvidenceRecord
from epd2_document_service.exceptions import (
    DocumentContentDigestMismatchError,
    DocumentContentMissingError,
    DocumentFieldInvalidError,
    DocumentVersionChainBrokenError,
    DocumentVersionImmutableError,
    DocumentVersionSequenceInvalidError,
    GovernedRecordDeletionForbiddenError,
)
from epd2_document_service.versions import (
    GENESIS_PREVIOUS_HASH,
    DocumentVersion,
    hashable_fields,
)

#: Audit Core's append-only event store port, named here so the document
#: application layer depends on *that* port rather than on a
#: document-local re-declaration of it. This service never defines its own
#: audit store: the hash chain, the conflict detection and the
#: verification live in `audit-core`, and a second implementation would be
#: a second, disagreeing tamper-evidence story.
DocumentAuditEventStore = AuditEventStore


def delete_document_record(record: object) -> None:
    """The only delete-shaped function in this service, and it refuses.

    Present on purpose. A reader looking for "how do I delete a document?"
    finds this, its reason code and this docstring, rather than finding
    nothing and concluding the capability is merely missing. Disposal is a
    PACK-09-authorized act recorded through
    `application.execute_disposition`; it leaves a tombstone and
    destruction evidence, and it is not this."""
    raise GovernedRecordDeletionForbiddenError(
        "governed documents, versions and evidence are never deleted; disposal is a "
        "PACK-09-authorized disposition that leaves a record, not a removal that leaves none"
    )


def _in_scope(record_scope: OrganizationalScopeRef, scope: OrganizationalScopeRef) -> bool:
    return record_scope.organization_id == scope.organization_id


# ---------------------------------------------------------------------------
# Idempotency and the event sink
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """What a completed command recorded about itself."""

    event_id: UUID
    command: str
    request_digest: str
    aggregate_id: UUID
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, context="IdempotencyRecord.recorded_at")
        if not self.command.strip():
            raise DocumentFieldInvalidError("command must be non-empty")


class CommandIdempotencyStore(Protocol):
    """Answers "did this exact request already execute, and what did it
    produce?".

    Distinct from Audit Core's own event-id idempotency, which makes the
    *audit append* idempotent and nothing more. A retried command carrying
    a fresh `event_id` would pass the audit check and mint a second
    version for one real submission; this store answers the command-level
    question. Neither subsumes the other."""

    def get(self, event_id: UUID) -> IdempotencyRecord | None: ...

    def put(self, record: IdempotencyRecord) -> None: ...


class InMemoryCommandIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[UUID, IdempotencyRecord] = {}

    def get(self, event_id: UUID) -> IdempotencyRecord | None:
        return self._records.get(event_id)

    def put(self, record: IdempotencyRecord) -> None:
        self._records[record.event_id] = record


class EventSink(Protocol):
    """Where canonical envelopes go. PACK-13 owns the real transport; this
    port exists so the command layer never depends on which."""

    def publish(self, envelope: EventEnvelope) -> None: ...

    def published(self) -> tuple[EventEnvelope, ...]: ...


class InMemoryEventSink:
    def __init__(self) -> None:
        self._published: list[EventEnvelope] = []

    def publish(self, envelope: EventEnvelope) -> None:
        self._published.append(envelope)

    def published(self) -> tuple[EventEnvelope, ...]:
        return tuple(self._published)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


class ContentStore(Protocol):
    """Content-addressed, write-once storage for document bytes.

    This is the port that makes PACK-11 the owner of document content
    rather than another holder of references. It is deliberately the
    narrowest possible interface - put by content, get by digest, ask
    whether a digest is present - because every additional operation
    (list, scan, search) is an operation PACK-12's controlled-search and
    DLP surface must later govern, and inventing them here would create a
    second export path outside that surface."""

    def put(self, payload: bytes) -> str:
        """Store `payload` and return its digest."""
        ...

    def get(self, digest: str) -> bytes:
        """Return the bytes stored under `digest`, or raise."""
        ...

    def has(self, digest: str) -> bool: ...


class InMemoryContentStore:
    """Reference adapter. Holds bytes in a dict keyed by digest.

    Write-once is not enforced by a flag but by the addressing: the key
    *is* the hash of the value, so "overwrite with different content"
    describes a hash collision, not an API call. A repeat `put` of
    identical bytes is a no-op, which is what makes storing the same
    attachment on two documents cost one copy."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def put(self, payload: bytes) -> str:
        digest = content_digest_of(payload)
        self._blobs.setdefault(digest, bytes(payload))
        return digest

    def get(self, digest: str) -> bytes:
        require_digest(digest, "digest")
        blob = self._blobs.get(digest)
        if blob is None:
            raise DocumentContentMissingError(
                f"no content is stored under digest {digest} - the version references content "
                "this store does not hold"
            )
        # Re-verified on the way out, not only on the way in. A store that
        # only checked at write time could still hand back bytes corrupted
        # in place, and the caller would have no way to know.
        actual = content_digest_of(blob)
        if actual != digest:  # pragma: no cover - unreachable while the dict is the store
            raise DocumentContentDigestMismatchError(
                f"stored content under {digest} now hashes to {actual}"
            )
        return blob

    def has(self, digest: str) -> bool:
        return digest in self._blobs


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


class GovernedDocumentStore(Protocol):
    def save(self, document: GovernedDocument) -> None: ...

    def get(self, document_id: UUID) -> GovernedDocument | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[GovernedDocument, ...]: ...


class InMemoryGovernedDocumentStore:
    def __init__(self) -> None:
        self._documents: dict[UUID, GovernedDocument] = {}

    def save(self, document: GovernedDocument) -> None:
        self._documents[document.document_id] = document

    def get(self, document_id: UUID) -> GovernedDocument | None:
        return self._documents.get(document_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[GovernedDocument, ...]:
        return tuple(
            sorted(
                (d for d in self._documents.values() if _in_scope(d.scope, scope)),
                key=lambda d: d.created_at,
            )
        )


# ---------------------------------------------------------------------------
# Versions - the append-only store
# ---------------------------------------------------------------------------


class DocumentVersionStore(Protocol):
    """Append-only per document.

    Note what is absent: no `save`, no `update`, no `replace`. `append`
    and `record_state_change` are the only two writes, and the second one
    exists solely because a governed transition changes `state` and
    `history`, which `versions.hashable_fields` deliberately excludes from
    the chain. Everything the chain covers is genuinely write-once."""

    def append(self, version: DocumentVersion) -> DocumentVersion: ...

    def record_state_change(self, version: DocumentVersion) -> DocumentVersion: ...

    def get(self, version_id: UUID) -> DocumentVersion | None: ...

    def get_by_number(self, document_id: UUID, version_number: int) -> DocumentVersion | None: ...

    def list_for_document(self, document_id: UUID) -> tuple[DocumentVersion, ...]: ...

    def head(self, document_id: UUID) -> DocumentVersion | None: ...


class InMemoryDocumentVersionStore:
    """Reference adapter enforcing storage rule 3.

    `append` refuses three things, each of which is a distinct way a
    history gets rewritten:

    - re-appending an existing `version_id` (a replay that would overwrite);
    - a version number that is not exactly `head + 1` (a fork or a gap);
    - a `previous_version_hash` that is not the head's `version_hash` (a
      re-parenting, which is how a rewritten history is grafted back on).

    `record_state_change` allows exactly the fields the chain excludes to
    change, and refuses if anything the chain covers differs. That check
    is what stops "record a state change" from becoming a general-purpose
    edit."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, DocumentVersion] = {}
        self._by_document: dict[UUID, list[UUID]] = {}

    def _versions(self, document_id: UUID) -> list[DocumentVersion]:
        return [self._by_id[vid] for vid in self._by_document.get(document_id, [])]

    def append(self, version: DocumentVersion) -> DocumentVersion:
        if version.version_id in self._by_id:
            raise DocumentVersionImmutableError(
                f"version {version.version_id} is already stored; a stored version is never "
                "replaced"
            )
        existing = self._versions(version.document_id)
        expected_number = len(existing) + 1
        if version.version_number != expected_number:
            raise DocumentVersionSequenceInvalidError(
                f"expected version number {expected_number} for document "
                f"{version.document_id}, got {version.version_number}"
            )
        expected_previous = (
            GENESIS_PREVIOUS_HASH if not existing else existing[-1].version_hash
        )
        if version.previous_version_hash != expected_previous:
            raise DocumentVersionChainBrokenError(
                "previous_version_hash does not link to the stored head - this append would "
                "re-parent the history"
            )
        self._by_id[version.version_id] = version
        self._by_document.setdefault(version.document_id, []).append(version.version_id)
        return version

    def record_state_change(self, version: DocumentVersion) -> DocumentVersion:
        stored = self._by_id.get(version.version_id)
        if stored is None:
            raise DocumentVersionImmutableError(
                f"version {version.version_id} is not stored; a state change applies to a "
                "stored version"
            )
        if stored.version_hash != version.version_hash:
            raise DocumentVersionImmutableError(
                "a state change may not alter the stored version hash"
            )
        # Comparing the hashed *fields*, not only the stored hash. A caller
        # that altered a covered field without resealing would leave
        # `version_hash` unchanged and slip past a hash-only comparison -
        # and the tampered record would then be what the store returns,
        # with `verify_version_chain` only catching it on the next sweep.
        # This makes the write itself impossible.
        if hashable_fields(stored) != hashable_fields(version):
            raise DocumentVersionImmutableError(
                "a state change may not alter any field the version hash covers"
            )
        if len(version.history) < len(stored.history):
            raise DocumentVersionImmutableError(
                "version history is append-only; entries may not be removed"
            )
        self._by_id[version.version_id] = version
        return version

    def get(self, version_id: UUID) -> DocumentVersion | None:
        return self._by_id.get(version_id)

    def get_by_number(self, document_id: UUID, version_number: int) -> DocumentVersion | None:
        for version in self._versions(document_id):
            if version.version_number == version_number:
                return version
        return None

    def list_for_document(self, document_id: UUID) -> tuple[DocumentVersion, ...]:
        return tuple(sorted(self._versions(document_id), key=lambda v: v.version_number))

    def head(self, document_id: UUID) -> DocumentVersion | None:
        versions = self.list_for_document(document_id)
        return versions[-1] if versions else None


# ---------------------------------------------------------------------------
# Reviews, approvals, publication
# ---------------------------------------------------------------------------


class ReviewRecordStore(Protocol):
    def append(self, review: ReviewRecord) -> None: ...

    def list_for_version(
        self, document_id: UUID, version_number: int
    ) -> tuple[ReviewRecord, ...]: ...


class InMemoryReviewRecordStore:
    """Append-only: a review is never edited, and a reviewer who changes
    their mind records a second one."""

    def __init__(self) -> None:
        self._reviews: dict[UUID, ReviewRecord] = {}

    def append(self, review: ReviewRecord) -> None:
        if review.review_id in self._reviews:
            raise DocumentVersionImmutableError(
                f"review {review.review_id} is already recorded; reviews are append-only"
            )
        self._reviews[review.review_id] = review

    def list_for_version(
        self, document_id: UUID, version_number: int
    ) -> tuple[ReviewRecord, ...]:
        return tuple(
            sorted(
                (
                    r
                    for r in self._reviews.values()
                    if r.document_id == document_id and r.version_number == version_number
                ),
                key=lambda r: r.reviewed_at,
            )
        )


class ApprovalRecordStore(Protocol):
    def create_once(self, approval: ApprovalRecord) -> ApprovalRecord: ...

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> ApprovalRecord | None: ...


class InMemoryApprovalRecordStore:
    """One approval per version, created once.

    A second approval of the same version is refused rather than
    overwriting the first. Two approvals would leave "who approved this?"
    with two answers, and the whole reason approval exists is that the
    question has one."""

    def __init__(self) -> None:
        self._approvals: dict[tuple[UUID, int], ApprovalRecord] = {}

    def create_once(self, approval: ApprovalRecord) -> ApprovalRecord:
        key = (approval.document_id, approval.version_number)
        existing = self._approvals.get(key)
        if existing is not None:
            if existing.approval_id == approval.approval_id:
                return existing
            raise DocumentVersionImmutableError(
                f"version {approval.version_number} of document {approval.document_id} is "
                "already approved"
            )
        self._approvals[key] = approval
        return approval

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> ApprovalRecord | None:
        return self._approvals.get((document_id, version_number))


class PublicationAuthorizationStore(Protocol):
    def create_once(
        self, authorization: PublicationAuthorization
    ) -> PublicationAuthorization: ...

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> PublicationAuthorization | None: ...


class InMemoryPublicationAuthorizationStore:
    def __init__(self) -> None:
        self._authorizations: dict[tuple[UUID, int], PublicationAuthorization] = {}

    def create_once(
        self, authorization: PublicationAuthorization
    ) -> PublicationAuthorization:
        key = (authorization.document_id, authorization.version_number)
        existing = self._authorizations.get(key)
        if existing is not None:
            if existing.authorization_id == authorization.authorization_id:
                return existing
            raise DocumentVersionImmutableError(
                "a publication authorization already exists for this version"
            )
        self._authorizations[key] = authorization
        return authorization

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> PublicationAuthorization | None:
        return self._authorizations.get((document_id, version_number))


class PublicationRenditionStore(Protocol):
    def append(self, rendition: PublicationRendition) -> None: ...

    def get(self, rendition_id: UUID) -> PublicationRendition | None: ...

    def list_for_version(
        self, document_id: UUID, version_number: int
    ) -> tuple[PublicationRendition, ...]: ...


class InMemoryPublicationRenditionStore:
    """Several renditions per version are legitimate - a PDF and an
    accessible HTML form of one approved minutes document are two
    renditions of one record - so this store appends rather than
    creating-once."""

    def __init__(self) -> None:
        self._renditions: dict[UUID, PublicationRendition] = {}

    def append(self, rendition: PublicationRendition) -> None:
        if rendition.rendition_id in self._renditions:
            raise DocumentVersionImmutableError(
                f"rendition {rendition.rendition_id} is already stored"
            )
        self._renditions[rendition.rendition_id] = rendition

    def get(self, rendition_id: UUID) -> PublicationRendition | None:
        return self._renditions.get(rendition_id)

    def list_for_version(
        self, document_id: UUID, version_number: int
    ) -> tuple[PublicationRendition, ...]:
        return tuple(
            sorted(
                (
                    r
                    for r in self._renditions.values()
                    if r.document_id == document_id and r.version_number == version_number
                ),
                key=lambda r: r.issued_at,
            )
        )


# ---------------------------------------------------------------------------
# Supersession and revocation
# ---------------------------------------------------------------------------


class SupersessionStore(Protocol):
    def append(self, record: SupersessionRecord) -> None: ...

    def get_for_version(
        self, document_id: UUID, superseded_version_number: int
    ) -> SupersessionRecord | None: ...

    def list_for_document(self, document_id: UUID) -> tuple[SupersessionRecord, ...]: ...


class InMemorySupersessionStore:
    def __init__(self) -> None:
        self._records: dict[tuple[UUID, int], SupersessionRecord] = {}

    def append(self, record: SupersessionRecord) -> None:
        key = (record.document_id, record.superseded_version_number)
        if key in self._records:
            raise DocumentVersionImmutableError(
                f"version {record.superseded_version_number} is already superseded; a version "
                "is superseded once"
            )
        self._records[key] = record

    def get_for_version(
        self, document_id: UUID, superseded_version_number: int
    ) -> SupersessionRecord | None:
        return self._records.get((document_id, superseded_version_number))

    def list_for_document(self, document_id: UUID) -> tuple[SupersessionRecord, ...]:
        return tuple(
            sorted(
                (r for r in self._records.values() if r.document_id == document_id),
                key=lambda r: r.superseded_version_number,
            )
        )


class RevocationStore(Protocol):
    def append(self, record: RevocationRecord) -> None: ...

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> RevocationRecord | None: ...


class InMemoryRevocationStore:
    def __init__(self) -> None:
        self._records: dict[tuple[UUID, int], RevocationRecord] = {}

    def append(self, record: RevocationRecord) -> None:
        key = (record.document_id, record.version_number)
        if key in self._records:
            raise DocumentVersionImmutableError(
                f"version {record.version_number} is already revoked"
            )
        self._records[key] = record

    def get_for_version(
        self, document_id: UUID, version_number: int
    ) -> RevocationRecord | None:
        return self._records.get((document_id, version_number))


# ---------------------------------------------------------------------------
# Determinations
# ---------------------------------------------------------------------------


class SignatureDeterminationStore(Protocol):
    def append(self, determination: SignatureDetermination) -> None: ...

    def latest_for_version(
        self, document_id: UUID, version_number: int
    ) -> SignatureDetermination | None: ...


class InMemorySignatureDeterminationStore:
    """Append-only, with `latest_for_version` returning the most recent.

    Determinations are not overwritten: a signature determination that
    was later revised is itself a fact, and the sequence of
    determinations is sometimes exactly what a dispute is about."""

    def __init__(self) -> None:
        self._determinations: dict[UUID, SignatureDetermination] = {}

    def append(self, determination: SignatureDetermination) -> None:
        if determination.determination_id in self._determinations:
            raise DocumentVersionImmutableError(
                "this signature determination is already recorded"
            )
        self._determinations[determination.determination_id] = determination

    def latest_for_version(
        self, document_id: UUID, version_number: int
    ) -> SignatureDetermination | None:
        candidates = [
            d
            for d in self._determinations.values()
            if d.document_id == document_id and d.version_number == version_number
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d.determined_at)


class AdmissibilityDeterminationStore(Protocol):
    def append(self, determination: AdmissibilityDetermination) -> None: ...

    def latest_for_version(
        self, document_id: UUID, version_number: int, *, procedure_reference: str
    ) -> AdmissibilityDetermination | None: ...


class InMemoryAdmissibilityDeterminationStore:
    def __init__(self) -> None:
        self._determinations: dict[UUID, AdmissibilityDetermination] = {}

    def append(self, determination: AdmissibilityDetermination) -> None:
        if determination.determination_id in self._determinations:
            raise DocumentVersionImmutableError(
                "this admissibility determination is already recorded"
            )
        self._determinations[determination.determination_id] = determination

    def latest_for_version(
        self, document_id: UUID, version_number: int, *, procedure_reference: str
    ) -> AdmissibilityDetermination | None:
        candidates = [
            d
            for d in self._determinations.values()
            if d.document_id == document_id
            and d.version_number == version_number
            and d.procedure_reference == procedure_reference
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d.determined_at)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class EvidenceRecordStore(Protocol):
    def save(self, record: EvidenceRecord) -> None: ...

    def get(self, evidence_id: UUID) -> EvidenceRecord | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[EvidenceRecord, ...]: ...

    def list_for_document(self, document_id: UUID) -> tuple[EvidenceRecord, ...]: ...


class InMemoryEvidenceRecordStore:
    def __init__(self) -> None:
        self._records: dict[UUID, EvidenceRecord] = {}

    def save(self, record: EvidenceRecord) -> None:
        stored = self._records.get(record.evidence_id)
        if stored is not None and stored.version_hash != record.version_hash:
            raise DocumentVersionImmutableError(
                "an evidence record's preserved version hash may not change - re-registering "
                "different material is a new evidence item"
            )
        self._records[record.evidence_id] = record

    def get(self, evidence_id: UUID) -> EvidenceRecord | None:
        return self._records.get(evidence_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[EvidenceRecord, ...]:
        return tuple(
            sorted(
                (r for r in self._records.values() if _in_scope(r.scope, scope)),
                key=lambda r: r.registered_at,
            )
        )

    def list_for_document(self, document_id: UUID) -> tuple[EvidenceRecord, ...]:
        return tuple(
            sorted(
                (r for r in self._records.values() if r.document_id == document_id),
                key=lambda r: r.registered_at,
            )
        )


class EvidenceBundleStore(Protocol):
    def save(self, bundle: EvidenceBundle) -> None: ...

    def get(self, bundle_id: UUID) -> EvidenceBundle | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[EvidenceBundle, ...]: ...


class InMemoryEvidenceBundleStore:
    """Sealed bundles are frozen at the storage layer too.

    A sealed bundle whose stored digest differs from the incoming one is a
    modification of something that was sealed, and the store refuses it -
    so a caller that reconstructed a bundle object cannot write a
    different set of items back under the same id."""

    def __init__(self) -> None:
        self._bundles: dict[UUID, EvidenceBundle] = {}

    def save(self, bundle: EvidenceBundle) -> None:
        stored = self._bundles.get(bundle.bundle_id)
        if (
            stored is not None
            and stored.bundle_digest is not None
            and stored.bundle_digest != bundle.bundle_digest
        ):
            raise DocumentVersionImmutableError(
                f"bundle {bundle.bundle_id} is sealed; its contents may not change"
            )
        self._bundles[bundle.bundle_id] = bundle

    def get(self, bundle_id: UUID) -> EvidenceBundle | None:
        return self._bundles.get(bundle_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[EvidenceBundle, ...]:
        return tuple(
            sorted(
                (b for b in self._bundles.values() if _in_scope(b.scope, scope)),
                key=lambda b: b.created_at,
            )
        )
