"""Document Service domain primitives (PACK-11, FIR-ROADMAP-001,
FIR-INV-010).

The value objects, the identity-minimisation model, the typed taxonomies
and the pure invariant functions the rest of the service is built on. No
I/O, no clock, no storage: every function here is deterministic and
testable in isolation, exactly as `finance-service.domain` is for PACK-10
and `compliance-service.domain` is for PACK-09.

Four rules shape everything below.

- **Content is held, and content never travels.** PACK-11 is the one
  context canon 19f.22 makes the owner of document bytes. That ownership
  is what makes `ContentDigest` and the `ContentStore` port necessary -
  and it is also the reason `assert_no_document_content` exists: an event
  payload, an audit metadata field or a public projection that carried
  bytes would export the very thing this context was made to contain.
- **A document is never a person.** There is no `UserId`, `PersonId`,
  `MemberId`, author name or e-mail address anywhere in this module.
  Human beings appear only as `AuthorityReference` (a PACK-08 authority
  assignment) and as opaque `actor_reference` strings that resolve to
  nothing inside this service (FIR-INV-001).
- **Everything protected is scoped.** `OrganizationalScopeRef` travels
  with every record and every reference; an undeterminable scope denies
  rather than defaulting (FIR-INV-013).
- **The domain is neutral about *what* the document is.** `DocumentKind`
  enumerates the governed kinds later packages will attach - minutes,
  decisions, candidacy documents, legal and expert opinions, finance
  evidence, correspondence, SEPA mandate evidence - but this module
  implements none of those domains. It gives them one governed shape so
  that eleven packs do not grow eleven divergent document models.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_document_service.exceptions import (
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    DocumentContentLeakError,
    DocumentFieldInvalidError,
    DocumentReferenceInvalidError,
    DocumentTimestampNaiveError,
    ForbiddenIdentityLinkageError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    RetentionBindingMissingError,
    VotingLinkageForbiddenError,
)

# ---------------------------------------------------------------------------
# Structural helpers
# ---------------------------------------------------------------------------


def require_text(value: str, field_name: str) -> str:
    """Return `value` if it is a non-empty, non-whitespace string, else
    refuse with the structural code."""
    if not isinstance(value, str) or not value.strip():
        raise DocumentFieldInvalidError(f"{field_name} must be a non-empty string")
    return value


def require_timezone(moment: datetime, *, context: str) -> datetime:
    """Every stored instant is timezone-explicit (FIR-INV-010's history is
    only answerable if its timestamps are).

    A naive datetime is refused rather than assumed to be UTC: assuming a
    zone invents a fact, and the invented fact then travels into a hash
    that nobody can later contradict."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise DocumentTimestampNaiveError(
            f"{context}: a naive datetime is refused - an explicit timezone is required"
        )
    return moment


def deterministic_digest(*parts: str) -> str:
    """A stable content digest used for bundle seals, request digests and
    idempotency keys.

    Deterministic across processes and runs, which is what makes bundle
    immutability and idempotent replay checkable at all. Parts are joined
    with a separator that cannot occur in a hex digest or a UUID, so
    `("ab", "cd")` and `("abc", "d")` never collide - a plain
    concatenation would let them."""
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def content_digest_of(payload: bytes) -> str:
    """The canonical content digest of a byte string: lower-case hex
    SHA-256.

    One algorithm, named in one place. A per-call algorithm parameter
    would make two versions of one document hashable under two schemes,
    and "the digests differ" would then stop meaning "the content
    differs"."""
    if not isinstance(payload, bytes | bytearray):
        raise DocumentFieldInvalidError("content must be a byte string")
    return hashlib.sha256(bytes(payload)).hexdigest()


_HEX_DIGITS = frozenset("0123456789abcdef")


def require_digest(value: str, field_name: str) -> str:
    """A digest is 64 lower-case hex characters - the shape
    `content_digest_of` produces.

    Validated structurally rather than trusted, because a digest field
    holding something that merely looks like an identifier is a field that
    silently stops proving anything."""
    require_text(value, field_name)
    if len(value) != 64 or not set(value).issubset(_HEX_DIGITS):
        raise DocumentFieldInvalidError(
            f"{field_name} must be a 64-character lower-case hex SHA-256 digest"
        )
    return value


# ---------------------------------------------------------------------------
# Identity minimisation (FIR-INV-001) and the content boundary
# ---------------------------------------------------------------------------

#: Field names that may never appear in a document event payload, in
#: audit metadata or in any projection this service emits (FIR-INV-001,
#: FIR-INIT-022). Deliberately about *shapes of identity* rather than one
#: service's naming: any of these arriving at a document boundary is a
#: forbidden identity linkage, whoever produced it.
PROHIBITED_IDENTITY_KEYS: frozenset[str] = frozenset(
    {
        "user_id",
        "userid",
        "person_id",
        "personid",
        "global_user_id",
        "member_id",
        "membership_id",
        "account_id",
        "identity_record_id",
        "credential_id",
        "voter_id",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "full_name",
        "first_name",
        "last_name",
        "name",
        "address",
        "postal_address",
        "date_of_birth",
        "birth_date",
        "national_id",
        "tax_id",
        "iban",
        "bic",
        "bank_account",
        "bank_account_number",
        "card_number",
        "pan",
        "password",
        "secret",
        "token",
    }
)

#: Field names that would carry a ballot, vote, tally, delegation or
#: participation-credential linkage (FIR-INV-002, FIR-INV-003). A minutes
#: document may *record* that a vote happened; it may never carry a
#: reference that could join a ballot to a person.
PROHIBITED_VOTING_KEYS: frozenset[str] = frozenset(
    {
        "ballot_id",
        "vote_id",
        "vote_envelope_id",
        "vote_receipt_id",
        "tally_id",
        "delegation_id",
        "delegation_snapshot_id",
        "participation_credential_id",
        "voting_token",
        "ballot_reference",
        "vote_reference",
    }
)

#: Field names that would carry a document's **content** rather than a
#: reference to it. This service holds content; it does not transmit it.
FORBIDDEN_CONTENT_KEYS: frozenset[str] = frozenset(
    {
        "content",
        "content_bytes",
        "document_content",
        "document_bytes",
        "file_bytes",
        "bytes",
        "body",
        "raw_content",
        "text",
        "full_text",
        "extracted_text",
        "ocr_text",
        "rendition_bytes",
        "attachment_bytes",
        "payload_bytes",
        "signature_value",
        "private_key",
    }
)


def _iter_keys(payload: object) -> list[tuple[str, str]]:
    """Every `(lower-case key, dotted path)` pair reachable in `payload`.

    One traversal shared by the three boundary assertions below. Written
    once rather than three times because three hand-copied traversals is
    three chances for one of them to stop descending into lists."""
    found: list[tuple[str, str]] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                key_text = str(key)
                found.append((key_text.lower(), f"{path}.{key_text}" if path else key_text))
                walk(value, f"{path}.{key_text}" if path else key_text)
        elif isinstance(node, Sequence) and not isinstance(node, str | bytes | bytearray):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload, "")
    return found


def reject_identity_payload_keys(payload: Mapping[str, object], *, context: str) -> None:
    """Raise if any prohibited identity key appears anywhere in `payload`.

    Applied at every event-construction, audit-metadata and projection
    boundary. Nested mappings and lists are walked, because a prohibited
    key one level down is the same leak as one at the top."""
    for key, where in _iter_keys(payload):
        if key in PROHIBITED_IDENTITY_KEYS:
            raise ForbiddenIdentityLinkageError(
                f"{context}: prohibited identity key {key!r} at {where}"
            )


def reject_voting_linkage_keys(payload: Mapping[str, object], *, context: str) -> None:
    """Raise if `payload` carries a ballot/vote/tally/delegation linkage.

    Separate from the identity check on purpose: they are different
    invariants with different reason codes, and merging them would report
    a voting-isolation breach under an identity code."""
    for key, where in _iter_keys(payload):
        if key in PROHIBITED_VOTING_KEYS:
            raise VotingLinkageForbiddenError(
                f"{context}: prohibited voting linkage key {key!r} at {where}"
            )


def assert_no_document_content(payload: Mapping[str, object], *, context: str) -> None:
    """Raise if `payload` carries document content in any nested position.

    **What this catches, and what it does not.** A key-name check sees
    names, not values. A payload that hides an extracted page in a field
    called `note_reference` passes here. The structural defence is that no
    wire type in this service has a field for such a value; this function
    is the backstop for payloads assembled somewhere else, and it also
    refuses any raw `bytes` value whatever its key - which is the one
    value-level check that is both cheap and unambiguous."""
    for key, where in _iter_keys(payload):
        if key in FORBIDDEN_CONTENT_KEYS:
            raise DocumentContentLeakError(
                f"{context}: document-content key {key!r} at {where} - a payload carries a "
                "reference to content, never the content"
            )

    def walk_values(node: object, path: str) -> None:
        if isinstance(node, bytes | bytearray):
            raise DocumentContentLeakError(
                f"{context}: raw byte value at {path or '<root>'} - content never travels"
            )
        if isinstance(node, Mapping):
            for key, value in node.items():
                walk_values(value, f"{path}.{key!s}" if path else str(key))
        elif isinstance(node, Sequence) and not isinstance(node, str):
            for index, value in enumerate(node):
                walk_values(value, f"{path}[{index}]")

    walk_values(payload, "")


def assert_emission_safe(payload: Mapping[str, object], *, context: str) -> None:
    """The three boundary checks, run in one call and in a fixed order.

    Every builder in `events` and `projections` runs this over its own
    assembled payload *before* returning it, so a payload that would leak
    never comes into existence - not even to be discarded later by a
    caller who might forget."""
    assert_no_document_content(payload, context=context)
    reject_identity_payload_keys(payload, context=context)
    reject_voting_linkage_keys(payload, context=context)


# ---------------------------------------------------------------------------
# Organizational scope (PACK-08)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrganizationalScopeRef:
    """A PACK-08 organizational scope, carried by every document record.

    Opaque by construction: an id plus the scope kind PACK-08 assigned.
    This service never interprets the hierarchy itself - inheritance,
    overlap and the six cross-scope access modes stay with
    `organization-service`."""

    organization_id: UUID
    scope_kind: str = "organization"

    def __post_init__(self) -> None:
        if not self.scope_kind or not self.scope_kind.strip():
            raise OrganizationScopeUndeterminedError("scope_kind must be a non-empty string")

    def assert_matches(self, other: OrganizationalScopeRef | None) -> None:
        """Raise unless `other` is the same scope. `None` is undetermined
        and denies rather than defaulting (FIR-INV-013)."""
        if other is None:
            raise OrganizationScopeUndeterminedError("organizational scope is undetermined")
        if other.organization_id != self.organization_id:
            raise OrganizationScopeMismatchError(
                "organizational scope does not match the target record's scope"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "organization_id": str(self.organization_id),
            "scope_kind": self.scope_kind,
        }


# ---------------------------------------------------------------------------
# The governed taxonomies
# ---------------------------------------------------------------------------


class DocumentKind(StrEnum):
    """The governed document kinds this context can hold.

    This is the taxonomy ADR-053 said "PACK-11, not PACK-10, defines" and
    that PACK-09's `PlaceholderRef.kind` left as an open string pending
    this round. It is deliberately a **closed** enum on this side of the
    boundary and an **open string** on the consumer side: a consumer that
    cannot yet name its kind can still hold a reference, while a document
    actually stored here always has a resolved, governed kind.

    Each member names a use later packages already have in the master
    register; none of those domains is implemented here. Adding a member
    is an additive change and requires an ADR entry, not a new model."""

    MEETING_MINUTES = "meeting_minutes"
    DECISION_RECORD = "decision_record"
    AGENDA = "agenda"
    MOTION_TEXT = "motion_text"
    CANDIDACY_DOCUMENT = "candidacy_document"
    NOMINATION_PACKAGE = "nomination_package"
    INITIATIVE_ATTACHMENT = "initiative_attachment"
    PROGRAMME_PROVISION = "programme_provision"
    LEGAL_OPINION = "legal_opinion"
    EXPERT_OPINION = "expert_opinion"
    AI_ANALYSIS_RECORD = "ai_analysis_record"
    FINANCE_EVIDENCE = "finance_evidence"
    OFFICIAL_CORRESPONDENCE = "official_correspondence"
    OFFICIAL_NOTICE_PROOF = "official_notice_proof"
    APPEAL_RECORD = "appeal_record"
    HEARING_RECORD = "hearing_record"
    SEPA_MANDATE_EVIDENCE = "sepa_mandate_evidence"
    PUBLIC_TRANSPARENCY_DOCUMENT = "public_transparency_document"
    POLICY_DOCUMENT = "policy_document"
    STATUTE_DOCUMENT = "statute_document"
    AUDIT_WORKING_PAPER = "audit_working_paper"
    OTHER_GOVERNED_DOCUMENT = "other_governed_document"


#: Kinds whose approved version is, by its nature, the official record of
#: a governed proceeding. They may not be published to the public
#: projection without an explicit disclosure obligation reference, and
#: they may never be revoked without a superseding version - a proceeding
#: whose record simply vanished would leave the proceeding unrecorded.
OFFICIAL_RECORD_KINDS: frozenset[DocumentKind] = frozenset(
    {
        DocumentKind.MEETING_MINUTES,
        DocumentKind.DECISION_RECORD,
        DocumentKind.APPEAL_RECORD,
        DocumentKind.HEARING_RECORD,
        DocumentKind.OFFICIAL_NOTICE_PROOF,
    }
)

#: Kinds that carry a mandatory expert or legal qualification claim, so
#: their approval requires the matching reviewer role rather than the
#: general one (FIR-PROG-002's mandatory legal and expert opinions - this
#: is the foundation those later rounds build the adoption gate on).
QUALIFIED_OPINION_KINDS: frozenset[DocumentKind] = frozenset(
    {DocumentKind.LEGAL_OPINION, DocumentKind.EXPERT_OPINION}
)


class SensitivityClass(StrEnum):
    """Classification of a document's content, mirroring PACK-09's
    `RecordSensitivity` term-for-term so the two never disagree about what
    "restricted" means."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


#: The ordering used by access-profile checks. Explicit rather than
#: derived from declaration order: an enum reordering is a refactor, and a
#: refactor must not be able to widen access.
_SENSITIVITY_ORDER: dict[SensitivityClass, int] = {
    SensitivityClass.PUBLIC: 0,
    SensitivityClass.INTERNAL: 1,
    SensitivityClass.CONFIDENTIAL: 2,
    SensitivityClass.RESTRICTED: 3,
}


def sensitivity_rank(value: SensitivityClass) -> int:
    """The comparable rank of a sensitivity class (higher is stricter)."""
    return _SENSITIVITY_ORDER[value]


class ProvenanceKind(StrEnum):
    """How material entered this context. Always recorded, never
    inferred: "we do not know where this came from" is not a value here,
    it is a refusal (`EvidenceProvenanceMissingError`)."""

    AUTHORED_IN_PLATFORM = "authored_in_platform"
    UPLOADED_BY_PARTICIPANT = "uploaded_by_participant"
    RECEIVED_FROM_EXTERNAL_PARTY = "received_from_external_party"
    IMPORTED_FROM_SOURCE_SYSTEM = "imported_from_source_system"
    GENERATED_BY_SYSTEM = "generated_by_system"
    GENERATED_BY_AI_ANALYSIS = "generated_by_ai_analysis"
    CAPTURED_FROM_PROCEEDING = "captured_from_proceeding"


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ContentDescriptor:
    """What a document version says about its own content, without being
    the content.

    `digest` is the content's SHA-256 and is the only join between a
    version record and the bytes in the `ContentStore`: the store is
    content-addressed, so a version cannot point at content that was
    swapped underneath it without the digest changing and
    `verify_version_content` failing.

    `media_type` and `byte_length` are metadata, not assertions. A
    `media_type` of `application/pdf` records what the submitter declared,
    never that this service parsed a valid PDF."""

    digest: str
    media_type: str
    byte_length: int
    filename_reference: str | None = None

    def __post_init__(self) -> None:
        require_digest(self.digest, "digest")
        require_text(self.media_type, "media_type")
        if self.byte_length < 0:
            raise DocumentFieldInvalidError("byte_length must be non-negative")
        if self.filename_reference is not None:
            require_text(self.filename_reference, "filename_reference")

    def to_payload(self) -> dict[str, object]:
        """The wire form: the digest, the declared type and the size.
        Never the bytes, never the extracted text, never a rendition."""
        return {
            "content_digest": self.digest,
            "media_type": self.media_type,
            "byte_length": self.byte_length,
            "filename_reference": self.filename_reference,
        }


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a document version or evidence item came from.

    `source_system_reference` and `source_party_reference` are opaque
    strings. `source_party_reference` is emphatically **not** a person
    identifier: it is a per-document handle minted by the caller that
    resolves to nothing inside this service, which is what keeps a
    document's origin recordable without creating a cross-domain
    correlation key (FIR-INV-001).

    `analysis_provenance_reference` is the hook FIR-AI-002 needs: when a
    version was produced by an AI analysis, the AI provenance contract
    (model version, prompt-template version, snapshot digest) lives in the
    AI accountability context and is *pointed at* from here. PACK-11 does
    not restate it, because a restated provenance is one that can disagree
    with the original."""

    kind: ProvenanceKind
    captured_at: datetime
    recorded_at: datetime
    source_system_reference: str
    source_party_reference: str | None = None
    analysis_provenance_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.captured_at, context="Provenance.captured_at")
        require_timezone(self.recorded_at, context="Provenance.recorded_at")
        require_text(self.source_system_reference, "source_system_reference")
        if self.recorded_at < self.captured_at:
            raise DocumentFieldInvalidError("recorded_at must not precede captured_at")
        if self.source_party_reference is not None:
            require_text(self.source_party_reference, "source_party_reference")
        if (
            self.kind is ProvenanceKind.GENERATED_BY_AI_ANALYSIS
            and not self.analysis_provenance_reference
        ):
            raise DocumentFieldInvalidError(
                "AI-generated material requires analysis_provenance_reference - an AI output "
                "with no provenance contract is not attributable (FIR-AI-002)"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "provenance_kind": str(self.kind),
            "captured_at": self.captured_at.isoformat(),
            "recorded_at": self.recorded_at.isoformat(),
            "source_system_reference": self.source_system_reference,
            "source_party_reference": self.source_party_reference,
            "analysis_provenance_reference": self.analysis_provenance_reference,
        }


# ---------------------------------------------------------------------------
# Authority, conflicts, reasons
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuthorityReference:
    """A PACK-08 institutional authority assignment, as presented by the
    caller.

    The service resolves it through `authorization.AuthorizationPort`; a
    `role_code` string alone is never proof of authority. `actor_reference`
    is an opaque per-actor string used only for separation-of-duties
    comparison (is the approver the same actor as the author?) and never
    resolved to a person here."""

    authority_id: UUID
    role_code: str
    scope: OrganizationalScopeRef
    actor_reference: str = ""

    def __post_init__(self) -> None:
        require_text(self.role_code, "role_code")

    def to_payload(self) -> dict[str, object]:
        """The wire form. `actor_reference` is deliberately dropped: it is
        the closest thing this service holds to an actor-level identifier,
        and an event that carried it would put a correlatable handle on
        every governed act."""
        return {"authority_id": str(self.authority_id), "role_code": self.role_code}

    def to_state(self) -> dict[str, object]:
        """The hashed form, used only inside audit state payloads that
        never leave the service. Complete on purpose: an omitted field in
        a tamper-evidence hash is a field nobody can prove was not
        changed."""
        return {
            "authority_id": str(self.authority_id),
            "role_code": self.role_code,
            "organization_id": str(self.scope.organization_id),
            "actor_reference": self.actor_reference or None,
        }


@dataclass(frozen=True, slots=True)
class ConflictDeclaration:
    """The conflict-of-interest state declared for a protected action.

    `UNDECLARED` is a real state and it fails closed: the service refuses
    the protected action rather than treating silence as "no conflict"."""

    state: str
    declared_by: str
    related_party_group_reference: str | None = None

    UNDECLARED = "undeclared"
    NONE = "none"
    DECLARED_NON_BLOCKING = "declared_non_blocking"
    BLOCKING = "blocking"

    @property
    def is_blocking(self) -> bool:
        return self.state == self.BLOCKING

    @property
    def is_undeclared(self) -> bool:
        return self.state == self.UNDECLARED

    def to_state(self) -> dict[str, object]:
        return {
            "state": self.state,
            "declared_by": self.declared_by,
            "related_party_group_reference": self.related_party_group_reference,
        }


def assert_conflict_declared(declaration: ConflictDeclaration | None, *, action: str) -> None:
    """Fail closed on `None` and on `undeclared`; refuse a declared
    blocking conflict with its own code.

    `None` and `undeclared` are the same answer - unknown - and both
    deny. They raise the same error for that reason: a caller that
    supplied nothing and a caller that supplied "I have not checked" have
    told this service exactly as much."""
    if declaration is None or declaration.is_undeclared:
        raise ConflictOfInterestUndeclaredError(
            f"{action}: a conflict-of-interest declaration is required and none was made"
        )
    if declaration.is_blocking:
        raise ConflictOfInterestBlockingError(
            f"{action}: a declared blocking conflict of interest forbids this action"
        )


@dataclass(frozen=True, slots=True)
class ReasonCoded:
    """A recorded reason for a governed act: the registered code plus the
    authority that invoked it.

    Free text is not a reason. `note_reference` may point at a narrative
    held as its own governed document - which is exactly the shape this
    service exists to provide - but the *decision* is the code."""

    reason_code: str
    authority_reference: str
    note_reference: str | None = None

    def __post_init__(self) -> None:
        require_text(self.reason_code, "reason_code")
        if self.reason_code != self.reason_code.upper():
            raise DocumentFieldInvalidError("reason_code must be an upper-case registered code")
        require_text(self.authority_reference, "authority_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "reason_code": self.reason_code,
            "authority_reference": self.authority_reference,
            "note_reference": self.note_reference,
        }


# ---------------------------------------------------------------------------
# Retention and legal hold - PACK-09 stays the owner
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RetentionBinding:
    """The PACK-09 record class and retention policy version a document is
    bound to.

    PACK-11 stores the binding and refuses to dispose of anything without
    a PACK-09 authorization; it never computes a retention period, never
    decides a disposition and never releases a hold. Two services able to
    answer "may this be destroyed?" differently is worse than one service
    answering it."""

    record_class_reference: str
    retention_policy_reference: str
    retention_policy_version: int
    bound_at: datetime

    def __post_init__(self) -> None:
        if not self.record_class_reference.strip():
            raise RetentionBindingMissingError("record_class_reference must be non-empty")
        if not self.retention_policy_reference.strip():
            raise RetentionBindingMissingError("retention_policy_reference must be non-empty")
        if self.retention_policy_version < 1:
            raise DocumentFieldInvalidError("retention_policy_version must be a positive integer")
        require_timezone(self.bound_at, context="RetentionBinding.bound_at")

    def to_payload(self) -> dict[str, object]:
        return {
            "record_class_reference": self.record_class_reference,
            "retention_policy_reference": self.retention_policy_reference,
            "retention_policy_version": self.retention_policy_version,
            "bound_at": self.bound_at.isoformat(),
        }


class HoldState(StrEnum):
    """The state of a PACK-09 legal hold as this service was told it.

    `INDETERMINATE` is a real, storable state and not a placeholder: it is
    what a binding carries when PACK-09's answer could not be confirmed.
    Material touched by an indeterminate hold fails closed with its own
    code rather than being treated as unheld (FIR-DATA-003)."""

    ACTIVE = "active"
    RELEASED = "released"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class LegalHoldBinding:
    """A PACK-09 legal hold, as it applies to material in this context.

    The state is *read from* PACK-09 before every destruction-relevant act
    and deliberately not cached across acts: a hold that was released an
    hour ago and a hold that was issued a minute ago are both facts this
    service must not be a stale second opinion about."""

    hold_reference: str
    scope: OrganizationalScopeRef
    state: HoldState
    observed_at: datetime
    matter_reference: str | None = None

    def __post_init__(self) -> None:
        require_text(self.hold_reference, "hold_reference")
        require_timezone(self.observed_at, context="LegalHoldBinding.observed_at")
        if self.matter_reference is not None:
            require_text(self.matter_reference, "matter_reference")

    @property
    def blocks_destruction(self) -> bool:
        return self.state is HoldState.ACTIVE

    @property
    def is_undetermined(self) -> bool:
        return self.state is HoldState.INDETERMINATE

    def to_payload(self) -> dict[str, object]:
        return {
            "hold_reference": self.hold_reference,
            "hold_state": str(self.state),
            "observed_at": self.observed_at.isoformat(),
            "matter_reference": self.matter_reference,
        }


@dataclass(frozen=True, slots=True)
class DispositionAuthorization:
    """A PACK-09 destruction authorization, as presented to this service.

    Bound to the exact document version count it was issued against, so a
    version added after the authorization makes it stale rather than
    letting it silently cover material PACK-09 never saw."""

    authorization_reference: str
    scope: OrganizationalScopeRef
    authorized_at: datetime
    authorized_version_count: int
    disposition_action: str

    def __post_init__(self) -> None:
        require_text(self.authorization_reference, "authorization_reference")
        require_text(self.disposition_action, "disposition_action")
        require_timezone(self.authorized_at, context="DispositionAuthorization.authorized_at")
        if self.authorized_version_count < 1:
            raise DocumentFieldInvalidError("authorized_version_count must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {
            "authorization_reference": self.authorization_reference,
            "authorized_at": self.authorized_at.isoformat(),
            "authorized_version_count": self.authorized_version_count,
            "disposition_action": self.disposition_action,
        }


# ---------------------------------------------------------------------------
# Access profile
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AccessProfile:
    """What a reader is permitted to see, presented with a read request.

    Deliberately a *ceiling* and never a grant: holding an
    `AccessProfile` naming `RESTRICTED` does not let a caller read a
    restricted document - it lets a caller who *also* passes the authority
    check read one. Two independent conditions, so neither alone is
    enough."""

    max_sensitivity: SensitivityClass
    scope: OrganizationalScopeRef
    purpose_reference: str

    def __post_init__(self) -> None:
        require_text(self.purpose_reference, "purpose_reference")

    def permits(self, sensitivity: SensitivityClass) -> bool:
        return sensitivity_rank(sensitivity) <= sensitivity_rank(self.max_sensitivity)


# ---------------------------------------------------------------------------
# Request context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequestContext:
    """What a caller presents with every command.

    Mirrors PACK-09's and PACK-10's `RequestContext` field for field: the
    caller's own scope, the authorities it asserts, the conflict state it
    declares, and the caller-supplied `event_id` that makes the command
    idempotent. Same shape on purpose - a caller that already builds one
    for finance builds this one the same way."""

    scope: OrganizationalScopeRef | None
    authorities: tuple[AuthorityReference, ...] = ()
    conflict: ConflictDeclaration | None = None
    event_id: UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    access_profile: AccessProfile | None = None
    legal_holds: tuple[LegalHoldBinding, ...] = field(default_factory=tuple)

    def require_scope(self) -> OrganizationalScopeRef:
        if self.scope is None:
            raise OrganizationScopeUndeterminedError(
                "organizational scope is undetermined - default deny"
            )
        return self.scope


# ---------------------------------------------------------------------------
# Opaque outward reference helper
# ---------------------------------------------------------------------------


def require_reference(value: str, field_name: str) -> str:
    """Structural non-emptiness check for a reference field.

    Raises `DocumentReferenceInvalidError` rather than the generic field
    code, because every string this validates *is* a reference and an
    empty one is precisely "a required reference is absent"."""
    if not isinstance(value, str) or not value.strip():
        raise DocumentReferenceInvalidError(f"{field_name} must be a non-empty reference")
    return value
