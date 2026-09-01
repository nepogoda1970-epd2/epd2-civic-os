"""Immutable document versions and their cryptographically linked history
(PACK-11; FIR-INV-010, "historical versions must never be rewritten;
documents must preserve cryptographically linked history").

This module is the reason PACK-11 exists as its own context. Everything
else in the service - review, publication, evidence, projections - is
built on the guarantee stated here and would be worth much less without
it: **a stored version is never modified, and any modification of a stored
version is detectable.**

## The chain

Each `DocumentVersion` carries `previous_version_hash` and `version_hash`.
The rule is deliberately the same one `audit-core` uses for the audit log
(ADR-003), because two different chaining schemes in one repository is one
scheme too many, and an auditor who has verified one already knows how to
verify the other:

```text
version_hash = sha256(canonical_dumps(hashable_fields(version)) + previous_version_hash)
```

`canonical_dumps` comes from `epd2_core.canonical_json`, so two
independently-constructed representations of the same logical version
serialise byte-identically and therefore hash identically. Version 1 links
to `GENESIS_PREVIOUS_HASH`.

**What the chain proves and what it does not.** It proves that no version
in a retained sequence was altered or removed without the recomputation
failing - tamper *evidence*. It does not prove tamper *resistance*: an
actor with write access to the whole store could rewrite every version and
recompute every hash. Countersigning by an external party, and anchoring
the head hash somewhere this repository does not control, are the controls
that would close that gap; neither is in this round, and
`docs/handover/PACK-11-KNOWN-LIMITATIONS.md` says so rather than letting
the chain be read as more than it is. `verify_version_chain` is therefore
a *detection* mechanism to be run, not a property to be assumed.

## Why the content digest is inside the hashed fields

`content.digest` is part of `hashable_fields`, so the chain binds the
sequence of versions to the sequence of *contents*. Swapping the bytes
behind version 3 while leaving its record untouched breaks
`verify_version_content` (the digest no longer matches the bytes) but
leaves the chain intact; swapping the bytes *and* the recorded digest
leaves the content check intact but breaks the chain from version 3
onward. Both attacks have to be caught, and neither check alone catches
both, which is why `verify_document_integrity` runs the two together.

## What a version is not

A version is not a permission, not an approval and not a publication. It
is a frozen statement of content at a moment, plus who recorded it and
where it came from. Its lifecycle state lives on the version because a
document has several versions in different states at once; the *document*
aggregate in `documents` owns which of them is current.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_document_service.domain import (
    AuthorityReference,
    ContentDescriptor,
    DocumentKind,
    OrganizationalScopeRef,
    Provenance,
    ReasonCoded,
    SensitivityClass,
    content_digest_of,
    require_digest,
    require_text,
    require_timezone,
)
from epd2_document_service.exceptions import (
    DocumentContentDigestMismatchError,
    DocumentCorrectionTargetInvalidError,
    DocumentFieldInvalidError,
    DocumentStateUnknownError,
    DocumentTransitionInvalidError,
    DocumentVersionChainBrokenError,
    DocumentVersionSequenceInvalidError,
)

#: The `previous_version_hash` of version 1. Sixty-four zeros, the same
#: genesis constant `audit-core` uses, so the two chains are verifiable by
#: the same reader without a second convention to learn.
GENESIS_PREVIOUS_HASH = "0" * 64


class VersionState(StrEnum):
    """The lifecycle of one document version.

    Closed vocabulary. A value outside it raises `DocumentStateUnknownError`
    rather than being carried as an unrecognised string, because an
    unrecognised state is one that no transition table can refuse.

    `RETURNED_FOR_REVISION` is a terminal state *for that version*, not a
    way back to `DRAFT`: revising means creating version N+1, never
    reopening version N. That is what makes "historical versions are never
    rewritten" true of the workflow and not only of the storage layer."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    RETURNED_FOR_REVISION = "returned_for_revision"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


#: The allowed transitions. Every pair is listed explicitly: a rule
#: expressed as "anything except..." is a rule that silently admits every
#: state somebody adds later.
_ALLOWED_VERSION_TRANSITIONS: frozenset[tuple[VersionState, VersionState]] = frozenset(
    {
        (VersionState.DRAFT, VersionState.IN_REVIEW),
        # A draft that is abandoned is revoked, not deleted: the record of
        # the attempt survives (FIR-INV-010).
        (VersionState.DRAFT, VersionState.REVOKED),
        (VersionState.IN_REVIEW, VersionState.RETURNED_FOR_REVISION),
        (VersionState.IN_REVIEW, VersionState.APPROVED),
        (VersionState.IN_REVIEW, VersionState.REVOKED),
        (VersionState.RETURNED_FOR_REVISION, VersionState.REVOKED),
        (VersionState.APPROVED, VersionState.PUBLISHED),
        (VersionState.APPROVED, VersionState.SUPERSEDED),
        (VersionState.APPROVED, VersionState.REVOKED),
        (VersionState.PUBLISHED, VersionState.SUPERSEDED),
        (VersionState.PUBLISHED, VersionState.REVOKED),
        # A superseded version can still be revoked: supersession says
        # "there is a newer one", revocation says "this one no longer has
        # effect", and both can be true.
        (VersionState.SUPERSEDED, VersionState.REVOKED),
    }
)

#: States in which a version may be cited as evidence or relied on. A
#: draft is a working paper and an `in_review` version is a proposal; a
#: consumer that cited either would be citing something nobody has yet
#: taken responsibility for.
CITABLE_VERSION_STATES: frozenset[VersionState] = frozenset(
    {VersionState.APPROVED, VersionState.PUBLISHED, VersionState.SUPERSEDED}
)

#: States that a public projection may represent at all. `REVOKED` is
#: present on purpose: a revoked version that had been published leaves a
#: tombstone stating that a revocation occurred, because a published
#: document that simply disappeared from the public view would be a silent
#: retraction (`FIR-INIT-002`'s "never silently discarded", applied to
#: publication).
PUBLICLY_REPRESENTABLE_STATES: frozenset[VersionState] = frozenset(
    {VersionState.PUBLISHED, VersionState.SUPERSEDED, VersionState.REVOKED}
)


def resolve_version_state(value: str) -> VersionState:
    """Resolve a state string to a `VersionState`, refusing anything
    outside the closed vocabulary (CT-00-02)."""
    try:
        return VersionState(value)
    except ValueError as exc:
        raise DocumentStateUnknownError(f"unknown document version state {value!r}") from exc


def assert_version_transition_allowed(current: VersionState, target: VersionState) -> None:
    """Raise unless `current -> target` is in the transition table
    (CT-00-03)."""
    if (current, target) not in _ALLOWED_VERSION_TRANSITIONS:
        raise DocumentTransitionInvalidError(
            f"invalid document version transition {current.value} -> {target.value}"
        )


@dataclass(frozen=True, slots=True)
class VersionHistoryEntry:
    """One append-only entry in a version's own history.

    History is appended, never rewritten, and is **not** part of
    `hashable_fields`: a version's hash covers what the version *is*, not
    the sequence of governed acts performed on it afterwards. Including
    history would make the hash of version 3 change every time somebody
    reviewed it, which would break the chain for versions 4..n on a
    perfectly legitimate act - the chain would then be broken so routinely
    that a real break would go unnoticed."""

    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    authority: AuthorityReference
    state_after: VersionState

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="VersionHistoryEntry.occurred_at")
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
class DocumentVersion:
    """One immutable version of a governed document.

    Frozen and slotted, so the ordinary Python route to mutation is
    closed. The governed route to change is `with_state`, which returns a
    NEW object and never edits the stored one; the store then refuses to
    replace a stored version with a differing one, so the two defences are
    independent.

    `corrects_version_number` records that this version exists to correct
    an earlier one. The earlier version stays exactly where it was, in
    whatever state it reached: a correction is a new statement, not an
    erasure of the old one."""

    version_id: UUID
    document_id: UUID
    scope: OrganizationalScopeRef
    version_number: int
    kind: DocumentKind
    sensitivity: SensitivityClass
    title_reference: str
    content: ContentDescriptor
    provenance: Provenance
    recorded_at: datetime
    recorded_by: AuthorityReference
    previous_version_hash: str
    version_hash: str
    state: VersionState = VersionState.DRAFT
    corrects_version_number: int | None = None
    correction_reason: ReasonCoded | None = None
    history: tuple[VersionHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        if self.version_number < 1:
            raise DocumentVersionSequenceInvalidError(
                "version_number must be a positive integer starting at 1"
            )
        require_text(self.title_reference, "title_reference")
        require_timezone(self.recorded_at, context="DocumentVersion.recorded_at")
        require_digest(self.previous_version_hash, "previous_version_hash")
        require_digest(self.version_hash, "version_hash")
        if self.version_number == 1 and self.previous_version_hash != GENESIS_PREVIOUS_HASH:
            raise DocumentVersionChainBrokenError(
                "version 1 must link to the genesis previous-version hash"
            )
        if self.version_number > 1 and self.previous_version_hash == GENESIS_PREVIOUS_HASH:
            raise DocumentVersionChainBrokenError(
                "only version 1 may link to the genesis previous-version hash"
            )
        if self.corrects_version_number is not None:
            if self.corrects_version_number >= self.version_number:
                raise DocumentCorrectionTargetInvalidError(
                    "a correction must target an earlier version number"
                )
            if self.correction_reason is None:
                raise DocumentCorrectionTargetInvalidError(
                    "a correcting version must carry a reason-coded correction reason"
                )

    # -- governed transitions ------------------------------------------

    def with_state(
        self,
        target: VersionState,
        *,
        at: datetime,
        action: str,
        reason: ReasonCoded,
        authority: AuthorityReference,
    ) -> DocumentVersion:
        """Return a NEW version object in `target`, with one history entry
        appended.

        `version_hash` is deliberately **not** recomputed. The hash covers
        `hashable_fields`, which does not include `state` or `history`; a
        governed transition is a fact *about* the version, not a change
        *to* it, and recomputing would make every review break the chain
        for every later version."""
        assert_version_transition_allowed(self.state, target)
        require_timezone(at, context="DocumentVersion.with_state.at")
        entry = VersionHistoryEntry(
            sequence=len(self.history) + 1,
            occurred_at=at,
            action=action,
            reason=reason,
            authority=authority,
            state_after=target,
        )
        return replace(self, state=target, history=(*self.history, entry))

    @property
    def is_citable(self) -> bool:
        return self.state in CITABLE_VERSION_STATES

    @property
    def is_revoked(self) -> bool:
        return self.state is VersionState.REVOKED


def hashable_fields(version: DocumentVersion) -> dict[str, object]:
    """The fields the chain covers, in one place.

    **Key naming.** The content descriptor serialises under
    `content_descriptor`, not `content`: `content` is in
    `domain.FORBIDDEN_CONTENT_KEYS`, because in every wire payload in this
    repository that name means the bytes themselves. The rename is not
    cosmetic - it is the reason the emission check can stay blunt and
    key-name-based, and it keeps the hashed form and the wire form using
    one name for one thing.

    **What is in, and why.** Identity (`version_id`, `document_id`,
    `version_number`), scope, kind, sensitivity, the title reference, the
    complete content descriptor, the complete provenance, the recording
    moment and the recording authority, and the correction linkage. Change
    any of these on a stored version and the recomputed hash differs.

    **What is out, and why.** `state`, `history` and `version_hash`
    itself. The first two are governed facts appended after the version
    was recorded (see `with_state`); the third cannot be an input to its
    own computation.

    **`recorded_by` is included in full, `actor_reference` and all.** A
    version whose recording authority could be changed without breaking
    the chain would let "who recorded this" be rewritten silently, which
    is the attribution half of what FIR-INV-010 is protecting."""
    return {
        "version_id": str(version.version_id),
        "document_id": str(version.document_id),
        "organization_id": str(version.scope.organization_id),
        "scope_kind": version.scope.scope_kind,
        "version_number": version.version_number,
        "kind": str(version.kind),
        "sensitivity": str(version.sensitivity),
        "title_reference": version.title_reference,
        "content_descriptor": version.content.to_payload(),
        "provenance": version.provenance.to_payload(),
        "recorded_at": version.recorded_at.isoformat(),
        "recorded_by": version.recorded_by.to_state(),
        "corrects_version_number": version.corrects_version_number,
        "correction_reason": (
            None if version.correction_reason is None else version.correction_reason.to_payload()
        ),
    }


def compute_version_hash(version: DocumentVersion) -> str:
    """Compute the `version_hash` for `version`, given the
    `previous_version_hash` already set on it.

    Identical in construction to `audit-core.hash_chain.compute_event_hash`
    - deliberately, so that anyone who has verified an audit chain in this
    repository can verify a document chain without learning a second
    scheme."""
    serialized = canonical_dumps(hashable_fields(version))
    return hashlib.sha256((serialized + version.previous_version_hash).encode("utf-8")).hexdigest()


def seal_version(version: DocumentVersion) -> DocumentVersion:
    """Return `version` with its `version_hash` set to the computed value.

    Used at construction time by the application layer. A caller cannot
    supply a hash of its own choosing and have it survive
    `verify_version_chain`, so this is a convenience rather than a trust
    boundary - but making it the single construction path means no command
    can forget to seal."""
    return replace(version, version_hash=compute_version_hash(version))


@dataclass(frozen=True, slots=True)
class ChainVerificationResult:
    """The outcome of verifying one document's version chain.

    Carries the head hash so a caller can record or externally anchor it,
    and `broken_at_version` so an operator knows *where* the history stops
    being trustworthy rather than only *that* it does."""

    document_id: UUID
    valid: bool
    version_count: int
    head_hash: str
    broken_at_version: int | None = None
    detail: str | None = None


def verify_version_chain(
    document_id: UUID, versions: Sequence[DocumentVersion]
) -> ChainVerificationResult:
    """Verify sequence, linkage and every stored hash, without raising.

    Returns a result rather than raising, because verification is
    something an operator runs over a whole store: an exception on the
    first bad document would stop the sweep at the first finding, which is
    exactly the run where finding *all* of them matters. The command layer
    turns a `valid=False` result into `DocumentVersionChainBrokenError`
    where a refusal is the right response.

    An empty sequence is **not** valid. A document with no versions is not
    an intact chain of length zero; it is a document whose versions are
    missing, and reporting that as `valid` would let deletion of every
    version pass verification."""
    ordered = sorted(versions, key=lambda v: v.version_number)
    if not ordered:
        return ChainVerificationResult(
            document_id=document_id,
            valid=False,
            version_count=0,
            head_hash=GENESIS_PREVIOUS_HASH,
            broken_at_version=None,
            detail="no versions: a governed document has at least one version",
        )

    previous_hash = GENESIS_PREVIOUS_HASH
    for index, version in enumerate(ordered, start=1):
        if version.document_id != document_id:
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(ordered),
                head_hash=previous_hash,
                broken_at_version=version.version_number,
                detail="version belongs to a different document",
            )
        if version.version_number != index:
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(ordered),
                head_hash=previous_hash,
                broken_at_version=index,
                detail=(
                    f"version numbers must be gap-free and start at 1; expected {index}, "
                    f"found {version.version_number}"
                ),
            )
        if version.previous_version_hash != previous_hash:
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(ordered),
                head_hash=previous_hash,
                broken_at_version=version.version_number,
                detail="previous_version_hash does not match the predecessor's version_hash",
            )
        recomputed = compute_version_hash(version)
        if recomputed != version.version_hash:
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(ordered),
                head_hash=previous_hash,
                broken_at_version=version.version_number,
                detail="stored version_hash does not match the recomputed hash",
            )
        previous_hash = version.version_hash

    return ChainVerificationResult(
        document_id=document_id,
        valid=True,
        version_count=len(ordered),
        head_hash=previous_hash,
    )


def assert_version_chain_intact(
    document_id: UUID, versions: Sequence[DocumentVersion]
) -> ChainVerificationResult:
    """`verify_version_chain`, raising on failure.

    The form commands use: a command that would act on a document whose
    history no longer verifies must refuse, because every governed act it
    is about to record would be recorded against a history nobody can
    trust."""
    result = verify_version_chain(document_id, versions)
    if not result.valid:
        raise DocumentVersionChainBrokenError(
            f"document {document_id} version chain is broken at version "
            f"{result.broken_at_version}: {result.detail}"
        )
    return result


def verify_version_content(version: DocumentVersion, content: bytes) -> None:
    """Raise unless `content` hashes to the digest recorded on `version`.

    The other half of `verify_document_integrity`: the chain proves the
    *record* was not altered, this proves the *bytes* behind it were not.
    Neither implies the other."""
    actual = content_digest_of(content)
    if actual != version.content.digest:
        raise DocumentContentDigestMismatchError(
            f"content for version {version.version_number} of document {version.document_id} "
            f"hashes to {actual}, but {version.content.digest} was recorded"
        )


def next_version_hash_base(versions: Sequence[DocumentVersion]) -> tuple[int, str]:
    """The `(version_number, previous_version_hash)` a new version must
    take.

    Derived from the stored sequence rather than from a counter the caller
    supplies, so two concurrent writers cannot both believe they are
    creating version 4 with different predecessors - the second one's
    stored chain will not verify, and the store's own append check refuses
    it first."""
    ordered = sorted(versions, key=lambda v: v.version_number)
    if not ordered:
        return 1, GENESIS_PREVIOUS_HASH
    head = ordered[-1]
    return head.version_number + 1, head.version_hash
