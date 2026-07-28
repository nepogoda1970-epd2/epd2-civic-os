"""Canonical events emitted by Document Service (PACK-11).

Twenty-five event types, no more and no fewer. `DOCUMENT_EVENT_TYPES`
carries them with aggregate prefixes and **no** `document.` service prefix
bolted on, following the convention canon section 20 uses throughout
(`finance_account.created`, not `finance.finance_account_created`).

`document-service` is the sole owner of every one of them; no other
service publishes into this stream. The envelope from canon section 21 is
used unchanged, so `event_version` stays at `1.0`.

## Three distinct payload jobs, deliberately not interchangeable

- **State payloads** (`*_state_payload`, defined on the aggregates
  themselves) are full, canonically-hashable snapshots for Audit Core's
  `before_hash`/`after_hash`. They cover *every* field of their aggregate.
  A snapshot that is only nearly complete is worse than an obviously
  partial one, because nothing signals the gap. None of these is ever a
  wire payload: they carry the complete `AuthorityReference` including
  `actor_reference`, which is fine inside a hash that never leaves the
  service and forbidden on the wire.
- **Wire payloads** are what the builders below assemble: identifiers,
  enum values, timestamps, digests, one reason code and opaque outward
  references. Nothing else.
- **Safe metadata** - the organizational scope and the stable aggregate
  identifier - is added by `build_document_event` and not by twenty-five
  hand-written copies, so no builder can forget it.

## What no payload in this module carries

A document's content, extracted text, a rendition's bytes, a signature
value, a title *string* (only a `title_reference`), a name, an address, a
bank detail, an identity document, any voting information, a credential
value or a secret. `domain.assert_emission_safe` runs over every assembled
payload as a structural backstop, so a future builder that reaches for one
of those key names fails closed rather than shipping it.

**Why `title_reference` and not `title`.** A document's title is content -
"Beschwerde gegen den Aufnahmebescheid von …" names a person as reliably
as a `full_name` field would. The reference is an opaque pointer resolved
by an authorized read, and the wire never carries the string.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import (
    ActorRef,
    EventEnvelope,
    SubjectRef,
    assert_supported_major_version,
    build_event_envelope,
)
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
    AuthorityReference,
    DispositionAuthorization,
    LegalHoldBinding,
    OrganizationalScopeRef,
    ReasonCoded,
    RetentionBinding,
    assert_emission_safe,
    require_timezone,
)
from epd2_document_service.evidence import CustodyEvent, EvidenceBundle, EvidenceRecord
from epd2_document_service.exceptions import (
    UnknownDocumentEventTypeError,
    UnsupportedEventVersionError,
)
from epd2_document_service.versions import ChainVerificationResult, DocumentVersion

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})

_PRODUCER = "document-service"


#: The closed catalogue. A type outside it raises rather than being
#: published: an event nobody registered is an event no consumer can be
#: expected to handle and no schema covers.
DOCUMENT_EVENT_TYPES: tuple[str, ...] = (
    # governed_document
    "governed_document.registered",
    "governed_document.closed",
    "governed_document.reopened",
    "governed_document.retention_bound",
    "governed_document.legal_hold_observed",
    "governed_document.disposition_authorized",
    "governed_document.disposed",
    "governed_document.integrity_verified",
    "governed_document.integrity_failed",
    # document_version
    "document_version.recorded",
    "document_version.submitted_for_review",
    "document_version.reviewed",
    "document_version.returned_for_revision",
    "document_version.approved",
    "document_version.superseded",
    "document_version.revoked",
    "document_version.corrected",
    # publication
    "document_publication.authorized",
    "document_publication.published",
    "document_publication.rendition_issued",
    # determinations
    "document_determination.signature_recorded",
    "document_determination.admissibility_recorded",
    # evidence
    "document_evidence.registered",
    "document_evidence.custody_transferred",
    "document_evidence.bundle_sealed",
)

_DOCUMENT_EVENT_TYPE_SET: frozenset[str] = frozenset(DOCUMENT_EVENT_TYPES)

#: Aggregate name per prefix, so `build_document_event` can derive the
#: `SubjectRef.subject_type` rather than take it from a caller who could
#: get it wrong.
DOCUMENT_EVENT_AGGREGATE_BY_PREFIX: dict[str, str] = {
    "governed_document": "GovernedDocument",
    "document_version": "DocumentVersion",
    "document_publication": "PublicationRendition",
    "document_determination": "DocumentDetermination",
    "document_evidence": "EvidenceRecord",
}


def _aggregate_for(event_type: str) -> str:
    prefix = event_type.split(".", 1)[0]
    aggregate = DOCUMENT_EVENT_AGGREGATE_BY_PREFIX.get(prefix)
    if aggregate is None:
        raise UnknownDocumentEventTypeError(f"unknown document event prefix in {event_type!r}")
    return aggregate


#: The subset a public projection may ever represent.
#:
#: Deliberately tiny. Only publication is a public act; registration,
#: review, approval, evidence and every determination are internal
#: governance, and a public stream carrying "a legal opinion was
#: registered for case X" would disclose the existence of proceedings the
#: publication rules never authorized disclosing.
PUBLIC_PROJECTION_ALLOWED: frozenset[str] = frozenset(
    {
        "document_publication.published",
        "document_publication.rendition_issued",
        "document_version.revoked",
        "document_version.superseded",
    }
)


def assert_known_event_type(event_type: str) -> str:
    if event_type not in _DOCUMENT_EVENT_TYPE_SET:
        raise UnknownDocumentEventTypeError(
            f"{event_type!r} is not a document-service event type"
        )
    return event_type


def assert_supported_version(event_version: str) -> None:
    """Reject an unsupported major version, fail-closed (CT-00-05)."""
    try:
        assert_supported_major_version(event_version, SUPPORTED_MAJOR_VERSIONS)
    except Exception as exc:  # noqa: BLE001 - re-raised as this service's own code
        raise UnsupportedEventVersionError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Wire helpers
# ---------------------------------------------------------------------------


def _instant(value: datetime | None) -> str | None:
    if value is None:
        return None
    return require_timezone(value, context="event payload instant").isoformat()


def _identifier(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _authority_on_the_wire(authority: AuthorityReference | None) -> dict[str, object] | None:
    """Emit `authority_id` and `role_code`, and drop `actor_reference`.

    `actor_reference` is the closest thing this service holds to an
    actor-level identifier. Disclosure of the *authority* is permitted
    where the authority is itself a public office; disclosure of which
    natural person exercised it is not, and an event carrying it would put
    a correlatable per-actor handle on every governed act in the
    stream."""
    if authority is None:
        return None
    return authority.to_payload()


def _reason(reason: ReasonCoded | None) -> dict[str, object] | None:
    return None if reason is None else reason.to_payload()


# ---------------------------------------------------------------------------
# The envelope builder
# ---------------------------------------------------------------------------


def build_document_event(
    *,
    event_id: UUID,
    event_type: str,
    occurred_at: datetime,
    actor: ActorRef,
    aggregate_id: UUID,
    scope: OrganizationalScopeRef,
    payload: Mapping[str, object],
    correlation_id: UUID,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    """Build a canonical envelope for a document-service event.

    The one place safe metadata is added and the one place the emission
    boundary is enforced. Every builder below routes through it, so the
    scope, the aggregate identifier and the three emission checks cannot
    be forgotten by an individual builder - and a new builder added later
    inherits all of them by construction."""
    assert_known_event_type(event_type)
    assert_supported_version(EVENT_VERSION)
    full_payload: dict[str, object] = dict(payload)
    full_payload["organization_id"] = str(scope.organization_id)
    full_payload["aggregate_id"] = str(aggregate_id)
    assert_emission_safe(full_payload, context=f"event {event_type}")
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=require_timezone(occurred_at, context="event occurred_at"),
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type=_aggregate_for(event_type), subject_id=aggregate_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=full_payload,
    )


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def document_registered_payload(document: GovernedDocument) -> dict[str, object]:
    return {
        "document_id": str(document.document_id),
        "kind": str(document.kind),
        "sensitivity": str(document.sensitivity),
        "title_reference": document.title_reference,
        "subject_reference": document.subject_reference,
        "created_at": document.created_at.isoformat(),
        "custodian": _authority_on_the_wire(document.custodian),
        "review_requirement": document.review_requirement.to_payload(),
        "document_version": document.document_version,
    }


def document_state_changed_payload(
    document: GovernedDocument, reason: ReasonCoded
) -> dict[str, object]:
    return {
        "document_id": str(document.document_id),
        "state": str(document.state),
        "document_version": document.document_version,
        "version_count": document.version_count,
        "current_version_number": document.current_version_number,
        "head_version_hash": document.head_version_hash,
        "reason": _reason(reason),
    }


def retention_bound_payload(
    document: GovernedDocument, binding: RetentionBinding
) -> dict[str, object]:
    return {
        "document_id": str(document.document_id),
        "retention": binding.to_payload(),
        "document_version": document.document_version,
    }


def legal_hold_observed_payload(
    document: GovernedDocument, binding: LegalHoldBinding
) -> dict[str, object]:
    """Note what travels: the hold reference and the observed state, never
    the matter's substance. A hold's *existence* is an operational fact
    this stream needs; what the hold is about is PACK-09's, and often
    privileged."""
    return {
        "document_id": str(document.document_id),
        "legal_hold": binding.to_payload(),
        "document_version": document.document_version,
    }


def disposition_authorized_payload(
    document: GovernedDocument, authorization: DispositionAuthorization
) -> dict[str, object]:
    return {
        "document_id": str(document.document_id),
        "disposition_authorization": authorization.to_payload(),
        "document_version": document.document_version,
    }


def integrity_verified_payload(result: ChainVerificationResult) -> dict[str, object]:
    """The result of a chain verification, published either way.

    A failed verification is published, not swallowed. An integrity check
    whose negative result stayed inside the service would leave the only
    party who could act on it - the operator - uninformed, which defeats
    the purpose of running it."""
    return {
        "document_id": str(result.document_id),
        "valid": result.valid,
        "version_count": result.version_count,
        "head_version_hash": result.head_hash,
        "broken_at_version": result.broken_at_version,
        "detail": result.detail,
    }


def version_recorded_payload(version: DocumentVersion) -> dict[str, object]:
    """The wire form of a new version.

    Carries the content *digest* under `content_descriptor` (never
    `content`, which `domain.FORBIDDEN_CONTENT_KEYS` reserves for the
    bytes) and never the content itself, the `title_reference` and never
    the title, and the full chain linkage so a
    consumer can verify the chain from the stream alone without asking
    this service for anything."""
    return {
        "document_id": str(version.document_id),
        "version_id": str(version.version_id),
        "version_number": version.version_number,
        "kind": str(version.kind),
        "sensitivity": str(version.sensitivity),
        "title_reference": version.title_reference,
        "content_descriptor": version.content.to_payload(),
        "provenance": version.provenance.to_payload(),
        "recorded_at": version.recorded_at.isoformat(),
        "recorded_by": _authority_on_the_wire(version.recorded_by),
        "previous_version_hash": version.previous_version_hash,
        "version_hash": version.version_hash,
        "state": str(version.state),
        "corrects_version_number": version.corrects_version_number,
    }


def version_state_changed_payload(
    version: DocumentVersion, reason: ReasonCoded
) -> dict[str, object]:
    return {
        "document_id": str(version.document_id),
        "version_id": str(version.version_id),
        "version_number": version.version_number,
        "version_hash": version.version_hash,
        "state": str(version.state),
        "reason": _reason(reason),
    }


def version_reviewed_payload(review: ReviewRecord) -> dict[str, object]:
    """Note that the *finding* travels as a reference, never as text.

    A review finding on a membership appeal or a legal opinion is exactly
    the kind of internal deliberation FIR-MEM-001 says the applicant must
    not see; putting it on the event stream would publish it to every
    consumer at once."""
    return review.to_payload()


def version_approved_payload(approval: ApprovalRecord) -> dict[str, object]:
    return approval.to_payload()


def publication_authorized_payload(
    authorization: PublicationAuthorization,
) -> dict[str, object]:
    return authorization.to_payload()


def version_published_payload(
    version: DocumentVersion, authorization: PublicationAuthorization
) -> dict[str, object]:
    return {
        "document_id": str(version.document_id),
        "version_number": version.version_number,
        "version_hash": version.version_hash,
        "audience": str(authorization.audience),
        "disclosure_obligation_reference": authorization.disclosure_obligation_reference,
        "published_at": _instant(authorization.authorized_at),
    }


def rendition_issued_payload(rendition: PublicationRendition) -> dict[str, object]:
    return rendition.to_payload()


def version_superseded_payload(record: SupersessionRecord) -> dict[str, object]:
    return record.to_payload()


def version_revoked_payload(record: RevocationRecord) -> dict[str, object]:
    return record.to_payload()


def signature_determination_payload(
    determination: SignatureDetermination,
) -> dict[str, object]:
    return determination.to_payload()


def admissibility_determination_payload(
    determination: AdmissibilityDetermination,
) -> dict[str, object]:
    return determination.to_payload()


def evidence_registered_payload(record: EvidenceRecord) -> dict[str, object]:
    return record.to_payload()


def custody_transferred_payload(
    record: EvidenceRecord, event: CustodyEvent
) -> dict[str, object]:
    return {
        "evidence_id": str(record.evidence_id),
        "document_id": str(record.document_id),
        "version_number": record.version_number,
        "custody_event": event.to_payload(),
        "record_version": record.record_version,
    }


def bundle_sealed_payload(bundle: EvidenceBundle) -> dict[str, object]:
    return bundle.to_payload()


# ---------------------------------------------------------------------------
# Public projection filter
# ---------------------------------------------------------------------------


def is_publicly_projectable(event_type: str) -> bool:
    """Whether an event type may appear in a public projection at all.

    A closed allow-list rather than a deny-list: a deny-list admits every
    event type somebody adds later, and the default for a governance
    stream must be "not public"."""
    assert_known_event_type(event_type)
    return event_type in PUBLIC_PROJECTION_ALLOWED


def event_aggregate(event_type: str) -> str:
    """The aggregate name an event type belongs to."""
    assert_known_event_type(event_type)
    return _aggregate_for(event_type)


DOCUMENT_EVENT_AGGREGATES: dict[str, str] = {
    event_type: _aggregate_for(event_type) for event_type in DOCUMENT_EVENT_TYPES
}
