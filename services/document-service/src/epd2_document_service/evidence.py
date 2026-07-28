"""Evidence items, custody chains and sealed evidence bundles (PACK-11;
ADR-058).

Canon 19f.22 names PACK-11 the owner of "evidence content and the chain of
custody", and PACK-09's `references.EvidenceRef` docstring records what a
later admissibility decision will need from this context: "provenance,
integrity, custody, relevance decision and preserved version". This module
implements the first three and the last; the *relevance* decision belongs
to whichever body is deciding the matter, and `determinations` records it
rather than making it.

Pure, like `versions` and `documents`.

## Evidence is a governed *use* of a document version, not a second kind
## of object

An `EvidenceRecord` points at an exact `DocumentVersion` (by id, number
**and** version hash) and adds what makes that version usable as evidence:
who has held it, since when, and under which matter. It deliberately does
not duplicate the content descriptor, the provenance or the review state -
duplicating them would create a second place where "what is this
document?" is answered, and two answers that can drift apart is exactly
the failure mode ADR-053 was written to prevent between packs.

## Custody is a chain, verified as one

`CustodyEvent` entries form a sequence in which each transfer's recipient
must be the next entry's holder. A gap, an overlap or a hand-off to
somebody who never appears as the next holder makes
`verify_custody_chain` fail. This is a *continuity* check, not an identity
check: the holders are opaque `custodian_reference` strings that resolve
to nothing inside this service.

## A sealed bundle is immutable, and that is the whole point of sealing

`EvidenceBundle.seal` computes `bundle_digest` over the ordered item
references. Once sealed, adding an item raises. A bundle that could still
grow would make every prior citation of it ambiguous - "the bundle" would
mean different sets of material to two readers at two times, which is the
one thing a citable evidence bundle must never mean.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_document_service.domain import (
    AuthorityReference,
    OrganizationalScopeRef,
    Provenance,
    ReasonCoded,
    deterministic_digest,
    require_digest,
    require_text,
    require_timezone,
)
from epd2_document_service.exceptions import (
    DocumentFieldInvalidError,
    EvidenceBundleIncompleteError,
    EvidenceBundleSealedError,
    EvidenceCustodyBrokenError,
)
from epd2_document_service.versions import DocumentVersion

# ---------------------------------------------------------------------------
# Custody
# ---------------------------------------------------------------------------


class CustodyAction(StrEnum):
    """What happened to custody of an evidence item.

    `ACQUIRED` opens a chain and may appear exactly once, first. Every
    other action continues it. There is no `DESTROYED`: destruction of
    evidence is a PACK-09-authorized disposition recorded on the document,
    not a custody event this service can record on its own."""

    ACQUIRED = "acquired"
    TRANSFERRED = "transferred"
    SEALED = "sealed"
    UNSEALED_FOR_EXAMINATION = "unsealed_for_examination"
    RETURNED = "returned"


@dataclass(frozen=True, slots=True)
class CustodyEvent:
    """One link in an evidence item's chain of custody.

    `holder_reference` and `received_from_reference` are opaque, per-matter
    strings. They are not person identifiers and resolve to nothing here:
    the chain needs continuity (was there always somebody accountable?),
    not identity (who was it?), and asking for identity would put a
    cross-domain correlation key on every piece of evidence."""

    sequence: int
    occurred_at: datetime
    action: CustodyAction
    holder_reference: str
    recorded_by: AuthorityReference
    reason: ReasonCoded
    received_from_reference: str | None = None
    location_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="CustodyEvent.occurred_at")
        require_text(self.holder_reference, "holder_reference")
        if self.sequence < 1:
            raise DocumentFieldInvalidError("sequence must be a positive integer")
        if self.action is CustodyAction.ACQUIRED and self.sequence != 1:
            raise EvidenceCustodyBrokenError(
                "only the first custody event may be an acquisition - a chain acquired twice "
                "is two chains"
            )
        if self.action is not CustodyAction.ACQUIRED and self.received_from_reference is None:
            raise EvidenceCustodyBrokenError(
                f"a {self.action.value!r} custody event must name whom the item was received "
                "from - an unattributed hand-off is a gap in the chain"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "action": str(self.action),
            "holder_reference": self.holder_reference,
            "received_from_reference": self.received_from_reference,
            "location_reference": self.location_reference,
            "recorded_by": self.recorded_by.to_payload(),
            "reason": self.reason.to_payload(),
        }


def verify_custody_chain(events: Sequence[CustodyEvent]) -> None:
    """Raise unless the custody chain is continuous and well-ordered.

    Three conditions, each of which is a real way a chain breaks:

    1. the sequence numbers are gap-free and start at 1 - a gap is either
       a lost hand-off or a removed one, and this service cannot tell
       which;
    2. time never runs backwards between consecutive events;
    3. each event's `received_from_reference` is the previous event's
       `holder_reference` - the hand-off connects to the hand that was
       actually holding it.

    Condition 3 is the one that catches a forged intermediate link: an
    inserted event naming a holder nobody handed the item to fails here
    even though its own fields are all individually valid."""
    if not events:
        raise EvidenceCustodyBrokenError(
            "an evidence item has at least one custody event - material with no recorded "
            "custody is not evidence"
        )
    ordered = sorted(events, key=lambda e: e.sequence)
    if ordered[0].action is not CustodyAction.ACQUIRED:
        raise EvidenceCustodyBrokenError("the first custody event must be an acquisition")
    previous: CustodyEvent | None = None
    for index, event in enumerate(ordered, start=1):
        if event.sequence != index:
            raise EvidenceCustodyBrokenError(
                f"custody sequence must be gap-free and start at 1; expected {index}, found "
                f"{event.sequence}"
            )
        if previous is not None:
            if event.occurred_at < previous.occurred_at:
                raise EvidenceCustodyBrokenError(
                    f"custody event {event.sequence} occurred before event {previous.sequence}"
                )
            if event.received_from_reference != previous.holder_reference:
                raise EvidenceCustodyBrokenError(
                    f"custody event {event.sequence} was received from "
                    f"{event.received_from_reference!r}, but event {previous.sequence} left the "
                    f"item with {previous.holder_reference!r}"
                )
        previous = event


# ---------------------------------------------------------------------------
# Evidence items
# ---------------------------------------------------------------------------


class EvidenceIntegrityState(StrEnum):
    """The integrity picture for one evidence item, as last verified.

    `UNVERIFIED` is a real state and is *not* the same as `INTACT`: an
    item nobody has checked since it was registered is an item nobody can
    say is unaltered, and a bundle that sealed over it would be sealing
    over an assumption."""

    UNVERIFIED = "unverified"
    INTACT = "intact"
    COMPROMISED = "compromised"


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One piece of evidence: an exact document version, plus provenance,
    custody and an integrity state.

    `version_hash` is stored, not looked up. That is the "preserved
    version" PACK-09's `EvidenceRef` docstring asks for: a citation that
    resolved the version at read time would silently follow the document
    forward, and evidence that follows the document forward is not
    evidence of anything."""

    evidence_id: UUID
    scope: OrganizationalScopeRef
    document_id: UUID
    version_number: int
    version_hash: str
    matter_reference: str
    provenance: Provenance
    registered_at: datetime
    registered_by: AuthorityReference
    custody: tuple[CustodyEvent, ...] = ()
    integrity_state: EvidenceIntegrityState = EvidenceIntegrityState.UNVERIFIED
    integrity_verified_at: datetime | None = None
    record_version: int = 1

    def __post_init__(self) -> None:
        require_digest(self.version_hash, "version_hash")
        require_text(self.matter_reference, "matter_reference")
        require_timezone(self.registered_at, context="EvidenceRecord.registered_at")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")
        if self.record_version < 1:
            raise DocumentFieldInvalidError("record_version must be a positive integer")
        if self.integrity_verified_at is not None:
            require_timezone(
                self.integrity_verified_at, context="EvidenceRecord.integrity_verified_at"
            )
        if (
            self.integrity_state is not EvidenceIntegrityState.UNVERIFIED
            and self.integrity_verified_at is None
        ):
            raise DocumentFieldInvalidError(
                "a verified integrity state must record when the verification happened"
            )

    @property
    def current_holder_reference(self) -> str | None:
        if not self.custody:
            return None
        return max(self.custody, key=lambda e: e.sequence).holder_reference

    def with_custody_event(self, event: CustodyEvent) -> EvidenceRecord:
        """Append a custody event, verifying the whole chain afterwards.

        Verifying the *whole* chain rather than only the new link is
        deliberate and cheap: a chain that was already broken must not be
        allowed to accept new links and look healthy at the tip."""
        chain = (*self.custody, event)
        verify_custody_chain(chain)
        return replace(self, custody=chain, record_version=self.record_version + 1)

    def with_integrity(
        self, state: EvidenceIntegrityState, *, at: datetime
    ) -> EvidenceRecord:
        require_timezone(at, context="EvidenceRecord.with_integrity.at")
        return replace(
            self,
            integrity_state=state,
            integrity_verified_at=at,
            record_version=self.record_version + 1,
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "evidence_id": str(self.evidence_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "version_hash": self.version_hash,
            "matter_reference": self.matter_reference,
            "integrity_state": str(self.integrity_state),
            "integrity_verified_at": (
                None
                if self.integrity_verified_at is None
                else self.integrity_verified_at.isoformat()
            ),
            "custody_event_count": len(self.custody),
            "registered_at": self.registered_at.isoformat(),
        }

    def to_state_payload(self) -> dict[str, object]:
        """The complete snapshot for audit hashing - every field, including
        the ones `to_payload` drops for the wire."""
        payload = self.to_payload()
        payload["scope"] = self.scope.to_payload()
        payload["provenance"] = self.provenance.to_payload()
        payload["registered_by"] = self.registered_by.to_state()
        payload["custody"] = [e.to_payload() for e in self.custody]
        payload["record_version"] = self.record_version
        return payload


def assert_evidence_admissible_shape(
    record: EvidenceRecord, version: DocumentVersion
) -> None:
    """Raise unless `record` still describes a citable, unaltered version.

    Called before an evidence item is added to a bundle or cited in a
    determination. Deliberately *not* an admissibility decision: it checks
    the four structural preconditions this service can actually verify -
    the version exists, the stored hash still matches, the version is in a
    citable state, and provenance is present. Whether the evidence is
    *relevant and admissible* is a governed human decision recorded in
    `determinations`."""
    if version.document_id != record.document_id or version.version_number != record.version_number:
        raise EvidenceBundleIncompleteError(
            "the evidence record does not describe the presented version"
        )
    if version.version_hash != record.version_hash:
        raise EvidenceBundleIncompleteError(
            "the version hash recorded on the evidence item differs from the stored version - "
            "the material changed after it was registered as evidence"
        )
    if not version.is_citable:
        raise EvidenceBundleIncompleteError(
            f"a version in state {version.state.value!r} may not be cited as evidence"
        )


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenceBundleItem:
    """One item's place in a bundle.

    Carries the evidence id, the version hash and the ordinal. The version
    hash is repeated here rather than resolved through the evidence record
    at seal time so that the bundle digest is computed over material the
    bundle itself asserts - a bundle whose digest depended on a lookup
    would change meaning if the lookup ever changed."""

    ordinal: int
    evidence_id: UUID
    document_id: UUID
    version_number: int
    version_hash: str

    def __post_init__(self) -> None:
        require_digest(self.version_hash, "version_hash")
        if self.ordinal < 1:
            raise DocumentFieldInvalidError("ordinal must be a positive integer")
        if self.version_number < 1:
            raise DocumentFieldInvalidError("version_number must be a positive integer")

    def digest_parts(self) -> tuple[str, ...]:
        return (
            str(self.ordinal),
            str(self.evidence_id),
            str(self.document_id),
            str(self.version_number),
            self.version_hash,
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "evidence_id": str(self.evidence_id),
            "document_id": str(self.document_id),
            "version_number": self.version_number,
            "version_hash": self.version_hash,
        }


class BundleState(StrEnum):
    OPEN = "open"
    SEALED = "sealed"


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """An ordered, sealable set of evidence items citable as one thing.

    The bundle is what a PACK-09 case, a PACK-19 candidacy appeal or a
    PACK-10 audit engagement cites when it needs to say "this material,
    exactly this, and nothing else". `bundle_digest` is what makes that
    citation checkable."""

    bundle_id: UUID
    scope: OrganizationalScopeRef
    matter_reference: str
    purpose_reference: str
    created_at: datetime
    created_by: AuthorityReference
    items: tuple[EvidenceBundleItem, ...] = ()
    state: BundleState = BundleState.OPEN
    bundle_digest: str | None = None
    sealed_at: datetime | None = None
    sealed_by: AuthorityReference | None = None
    bundle_version: int = 1

    def __post_init__(self) -> None:
        require_text(self.matter_reference, "matter_reference")
        require_text(self.purpose_reference, "purpose_reference")
        require_timezone(self.created_at, context="EvidenceBundle.created_at")
        if self.bundle_version < 1:
            raise DocumentFieldInvalidError("bundle_version must be a positive integer")
        if self.state is BundleState.SEALED:
            if self.bundle_digest is None or self.sealed_at is None:
                raise EvidenceBundleIncompleteError(
                    "a sealed bundle must carry its digest and the moment it was sealed"
                )
            require_timezone(self.sealed_at, context="EvidenceBundle.sealed_at")
        ordinals = [item.ordinal for item in self.items]
        if ordinals != list(range(1, len(ordinals) + 1)):
            raise EvidenceBundleIncompleteError(
                "bundle item ordinals must be gap-free and start at 1"
            )

    def with_item(self, record: EvidenceRecord) -> EvidenceBundle:
        """Add an evidence item. Refuses once sealed."""
        if self.state is BundleState.SEALED:
            raise EvidenceBundleSealedError(
                f"bundle {self.bundle_id} is sealed; a sealed bundle cannot take further items"
            )
        self.scope.assert_matches(record.scope)
        if any(item.evidence_id == record.evidence_id for item in self.items):
            raise EvidenceBundleIncompleteError(
                f"evidence {record.evidence_id} is already in this bundle"
            )
        item = EvidenceBundleItem(
            ordinal=len(self.items) + 1,
            evidence_id=record.evidence_id,
            document_id=record.document_id,
            version_number=record.version_number,
            version_hash=record.version_hash,
        )
        return replace(
            self, items=(*self.items, item), bundle_version=self.bundle_version + 1
        )

    def seal(self, *, at: datetime, sealed_by: AuthorityReference) -> EvidenceBundle:
        """Freeze the bundle and compute its digest.

        An empty bundle cannot be sealed. "The empty set of evidence,
        sealed" is a citable object that says nothing while looking
        authoritative, and a case citing one would look evidenced."""
        if self.state is BundleState.SEALED:
            raise EvidenceBundleSealedError(f"bundle {self.bundle_id} is already sealed")
        if not self.items:
            raise EvidenceBundleIncompleteError("an empty evidence bundle cannot be sealed")
        require_timezone(at, context="EvidenceBundle.seal.at")
        digest = compute_bundle_digest(self.bundle_id, self.items)
        return replace(
            self,
            state=BundleState.SEALED,
            bundle_digest=digest,
            sealed_at=at,
            sealed_by=sealed_by,
            bundle_version=self.bundle_version + 1,
        )

    def verify_seal(self) -> None:
        """Raise unless a sealed bundle's stored digest still matches its
        items."""
        if self.state is not BundleState.SEALED:
            raise EvidenceBundleIncompleteError("an unsealed bundle has no seal to verify")
        expected = compute_bundle_digest(self.bundle_id, self.items)
        if expected != self.bundle_digest:
            raise EvidenceBundleIncompleteError(
                f"bundle {self.bundle_id} digest does not match its items - the bundle changed "
                "after it was sealed"
            )

    @property
    def citation_reference(self) -> str | None:
        """The opaque string a consuming pack cites, available only once
        sealed - an open bundle has nothing stable to cite."""
        if self.state is not BundleState.SEALED or self.bundle_digest is None:
            return None
        return f"epd2-bundle:{self.bundle_id}:{self.bundle_digest[:16]}"

    def to_payload(self) -> dict[str, object]:
        return {
            "bundle_id": str(self.bundle_id),
            "matter_reference": self.matter_reference,
            "purpose_reference": self.purpose_reference,
            "state": str(self.state),
            "item_count": len(self.items),
            "bundle_digest": self.bundle_digest,
            "sealed_at": None if self.sealed_at is None else self.sealed_at.isoformat(),
            "citation_reference": self.citation_reference,
        }

    def to_state_payload(self) -> dict[str, object]:
        payload = self.to_payload()
        payload["scope"] = self.scope.to_payload()
        payload["created_at"] = self.created_at.isoformat()
        payload["created_by"] = self.created_by.to_state()
        payload["sealed_by"] = None if self.sealed_by is None else self.sealed_by.to_state()
        payload["items"] = [item.to_payload() for item in self.items]
        payload["bundle_version"] = self.bundle_version
        return payload


def compute_bundle_digest(bundle_id: UUID, items: Sequence[EvidenceBundleItem]) -> str:
    """The digest that makes a sealed bundle citable.

    Covers the bundle id and every item's ordinal, identity and version
    hash. Order is part of the digest: two bundles over the same material
    in different orders are different bundles, because a numbered exhibit
    list is not a set."""
    parts: list[str] = [str(bundle_id)]
    for item in sorted(items, key=lambda i: i.ordinal):
        parts.extend(item.digest_parts())
    return deterministic_digest(*parts)
