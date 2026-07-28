"""Document Service exceptions, one class per stable, machine-readable
reason code (canon section 24's standard applied to PACK-11; ADR-004's
registry rule; ADR-055).

Every class below carries a `reason_code` class attribute whose literal
string is registered in `contracts/reason-codes/pack-11.yml`. No
document-service code path may raise a bare `ValueError` or
`PermissionError` with a free-text message in place of one of these: a
governed refusal that cannot be matched to a registered code is a refusal
no operator, reviewer or auditor can classify.

The hierarchy mirrors every earlier pack's, so a caller that already
distinguishes the two categories across PACK-02 through PACK-10 needs no
PACK-11-specific handling:

- structural, integrity and lifecycle violations subclass `ValueError`;
- authorization, scope, independence and separation-of-duties violations
  subclass `PermissionError`.

Codes fall into two groups:

- `DOCUMENT_*` codes introduced by this implementation round
  (`source: pack-11-service` in the registry). Canon 0.8.0 section 24
  registers **no** document or evidence code at all - canon 19f.22 names
  PACK-11 as the owner of documents but the canon round that would give
  the context its own section never happened, and `CANON_VERSION` stays
  `0.8.0` here (this round amends no canon). ADR-055 records the codes and
  why each one could not be expressed by an existing code.
- codes reused verbatim from earlier packs where the semantics are
  identical (`PERMISSION_DENIED`, `ORGANIZATION_SCOPE_MISMATCH`,
  `RECORD_UNDER_LEGAL_HOLD`, ...), never shadowed by a `DOCUMENT_`
  duplicate. Retention and legal hold remain PACK-09's domain, and
  organizational scope and authority remain PACK-08's; a
  `DOCUMENT_`-prefixed duplicate of either would create two codes for one
  fact and let the two drift apart.

**One deliberate asymmetry, stated rather than hidden.** There is no
`DocumentContentInvalidError` for "these bytes are not really a PDF". This
service verifies *integrity* (the content matches the digest that was
recorded for it), never *authenticity of format*. Format sniffing is a
different claim, made by a different component, and a reason code here
would imply this service had made it.
"""

from __future__ import annotations


class DocumentError(Exception):
    """Base class for every governed document/evidence refusal.

    `reason_code` is always a string registered in
    `contracts/reason-codes/pack-11.yml`. The default is the generic
    PACK-02 denial rather than a document-specific code, so a subclass
    that forgot to declare one denies rather than reporting a misleadingly
    specific cause."""

    reason_code: str = "PERMISSION_DENIED"


class DocumentTechnicalError(DocumentError, RuntimeError):
    """A non-business, infrastructure-level failure.

    Deliberately **not** a governed refusal: it carries the generic code
    only so that the base-class contract holds, and callers must not
    present it to a user as a reason-coded decision. See
    `docs/contracts/document-command-query-contracts.md`."""

    reason_code = "SERVICE_STATE_READ_ONLY"


# ---------------------------------------------------------------------------
# Scope, authority, separation of duties
# ---------------------------------------------------------------------------


class OrganizationScopeUndeterminedError(DocumentError, PermissionError):
    """The organizational scope of the request or of the target could not
    be determined. Undetermined denies; it never defaults to a scope."""

    reason_code = "ORGANIZATION_SCOPE_UNDETERMINED"


class OrganizationScopeMismatchError(DocumentError, PermissionError):
    """The presented scope is not the target record's scope (PACK-08
    default-deny regional isolation, FIR-INV-013)."""

    reason_code = "ORGANIZATION_SCOPE_MISMATCH"


class DocumentAuthorityMissingError(DocumentError, PermissionError):
    """No active, effective-dated, scope-matching authority exists for
    this action. A `role_code` string is never itself proof of
    authority."""

    reason_code = "DOCUMENT_AUTHORITY_MISSING"


class AuthorityRoleIncompatibleError(DocumentError, PermissionError):
    """The acting authority holds two roles the incompatibility matrix
    forbids holding together in one scope."""

    reason_code = "AUTHORITY_ROLE_INCOMPATIBLE"


class SelfApprovalProhibitedError(DocumentError, PermissionError):
    """The actor who authored, submitted or reviewed this version is the
    actor now trying to review, approve or publish it."""

    reason_code = "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"


class ConflictOfInterestUndeclaredError(DocumentError, PermissionError):
    """A protected action was attempted with no conflict-of-interest
    declaration. Silence is not "no conflict"; it is unknown, and unknown
    fails closed."""

    reason_code = "CONFLICT_OF_INTEREST_UNDECLARED"


class ConflictOfInterestBlockingError(DocumentError, PermissionError):
    """A declared, blocking conflict of interest forbids this actor from
    taking this action."""

    reason_code = "CONFLICT_OF_INTEREST_BLOCKING"


class AuditorIndependenceViolationError(DocumentError, PermissionError):
    """An independent reader's access was requested for a scope in which
    that reader is not independent."""

    reason_code = "DOCUMENT_AUDITOR_INDEPENDENCE_VIOLATION"


class RestrictedAccessDeniedError(DocumentError, PermissionError):
    """The caller's access profile does not cover this document's
    sensitivity classification."""

    reason_code = "DOCUMENT_ACCESS_PROFILE_INSUFFICIENT"


# ---------------------------------------------------------------------------
# Structure, validation, lookup
# ---------------------------------------------------------------------------


class DocumentRecordNotFoundError(DocumentError, ValueError):
    """No such document, version, evidence item or bundle in the caller's
    scope.

    Deliberately the *same* error and message shape for "does not exist"
    and "exists in another organization": a foreign identifier must not be
    confirmable by probing."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class DocumentFieldInvalidError(DocumentError, ValueError):
    """A required structural field is absent, empty or malformed."""

    reason_code = "DOCUMENT_FIELD_INVALID"


class DocumentTimestampNaiveError(DocumentError, ValueError):
    """A naive datetime reached a stored instant. Every recorded moment is
    timezone-explicit; assuming UTC would silently invent a fact."""

    reason_code = "DOCUMENT_TIMESTAMP_NOT_TIMEZONE_EXPLICIT"


class DocumentClassUndeterminedError(DocumentError, ValueError):
    """The document class could not be determined, so neither the
    retention schedule nor the review requirements are knowable."""

    reason_code = "DOCUMENT_CLASS_UNDETERMINED"


class DocumentReferenceInvalidError(DocumentError, ValueError):
    """A typed reference is absent, empty, or points outside the scope it
    was presented in."""

    reason_code = "DOCUMENT_REFERENCE_INVALID"


class DocumentReferenceKindMismatchError(DocumentError, ValueError):
    """A reference of one governed kind was presented where another kind
    is required. Kinds are not interchangeable: a legal opinion is not a
    SEPA mandate evidence item even when both are documents."""

    reason_code = "DOCUMENT_REFERENCE_KIND_MISMATCH"


# ---------------------------------------------------------------------------
# Version integrity (FIR-INV-010)
# ---------------------------------------------------------------------------


class DocumentVersionImmutableError(DocumentError, ValueError):
    """An attempt to modify a stored document version. Historical versions
    are never rewritten (FIR-INV-010); a change becomes a NEW version."""

    reason_code = "DOCUMENT_VERSION_IMMUTABLE"


class DocumentVersionChainBrokenError(DocumentError, ValueError):
    """The cryptographically linked version history does not verify: a
    link's `previous_version_hash` does not match its predecessor's
    `version_hash`, or a recomputed hash differs from the stored one."""

    reason_code = "DOCUMENT_VERSION_CHAIN_BROKEN"


class DocumentVersionSequenceInvalidError(DocumentError, ValueError):
    """Version numbers must start at 1 and increase by exactly 1 with no
    gaps. A gap is either a lost version or a rewritten one, and this
    service cannot tell which - so it refuses rather than guessing."""

    reason_code = "DOCUMENT_VERSION_SEQUENCE_INVALID"


class DocumentContentDigestMismatchError(DocumentError, ValueError):
    """Stored content does not hash to the digest recorded for it. The
    content, the digest, or both have changed."""

    reason_code = "DOCUMENT_CONTENT_DIGEST_MISMATCH"


class DocumentContentMissingError(DocumentError, ValueError):
    """A version references content that the content store does not
    hold. A version without retrievable content is not a governed
    document; it is a claim about one."""

    reason_code = "DOCUMENT_CONTENT_MISSING"


# ---------------------------------------------------------------------------
# Lifecycle: review, approval, publication, correction, revocation
# ---------------------------------------------------------------------------


class DocumentTransitionInvalidError(DocumentError, ValueError):
    """A lifecycle transition that the state machine does not allow."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class DocumentStateUnknownError(DocumentError, ValueError):
    """A state value outside the closed lifecycle vocabulary."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class DocumentReviewIncompleteError(DocumentError, ValueError):
    """Approval was attempted before every mandatory review for this
    document class had been recorded."""

    reason_code = "DOCUMENT_REVIEW_INCOMPLETE"


class DocumentApprovalMissingError(DocumentError, ValueError):
    """Publication or an evidence-grade use was attempted on a version
    that carries no approval decision."""

    reason_code = "DOCUMENT_APPROVAL_MISSING"


class DocumentPublicationNotAuthorizedError(DocumentError, PermissionError):
    """Publication was attempted without its own, separate publication
    authorization. Approval is not publication and publication is not
    approval."""

    reason_code = "PUBLICATION_NOT_ALLOWED"


class DocumentDisclosurePolicyViolationError(DocumentError, ValueError):
    """The requested projection would emit more than the document's
    sensitivity classification and the applicable disclosure obligation
    permit."""

    reason_code = "DISCLOSURE_POLICY_VIOLATION"


class DocumentCorrectionTargetInvalidError(DocumentError, ValueError):
    """The version a correction names is not correctable: it does not
    exist in this document, or it is itself already a withdrawn or revoked
    version."""

    reason_code = "DOCUMENT_CORRECTION_TARGET_INVALID"


class DocumentSupersessionInvalidError(DocumentError, ValueError):
    """A supersession record does not describe a valid supersession: the
    superseding version is not later than the superseded one, the two
    belong to different documents, or the target is already superseded by
    something else."""

    reason_code = "DOCUMENT_SUPERSESSION_INVALID"


class DocumentRevocationInvalidError(DocumentError, ValueError):
    """A revocation was attempted on a version that cannot be revoked, or
    without the reason code and authority a revocation requires. A
    revocation removes *effect*, never the record (FIR-INV-010)."""

    reason_code = "DOCUMENT_REVOCATION_INVALID"


class DocumentAlreadyPublishedError(DocumentError, ValueError):
    """A second publication of the same version was attempted. A
    republication is a new rendition of a new version, never a silent
    overwrite of the published one."""

    reason_code = "DOCUMENT_ALREADY_PUBLISHED"


# ---------------------------------------------------------------------------
# Governed determinations (the four ADR-053 consumer requirements)
# ---------------------------------------------------------------------------


class DocumentDeterminationMissingError(DocumentError, ValueError):
    """A governed determination (signature, admissibility) was required
    and none exists. This service never infers one: an absent
    determination is reported as absent, exactly as ADR-053 requires of
    PACK-11's consumer interface."""

    reason_code = "DOCUMENT_DETERMINATION_MISSING"


class DocumentDeterminationStaleError(DocumentError, ValueError):
    """A determination exists but was made against a different version of
    the document than the one presented. A determination is bound to the
    exact version it examined and does not travel forward."""

    reason_code = "DOCUMENT_DETERMINATION_STALE"


class DocumentDeterminationNotPermittedError(DocumentError, PermissionError):
    """The actor recording this determination does not hold the authority
    the determination kind requires (a signature determination is not a
    legal-admissibility determination and the two are not
    interchangeable)."""

    reason_code = "DOCUMENT_DETERMINATION_NOT_PERMITTED"


# ---------------------------------------------------------------------------
# Evidence, provenance, custody
# ---------------------------------------------------------------------------


class EvidenceProvenanceMissingError(DocumentError, ValueError):
    """An evidence item was recorded without provenance. Evidence with no
    recorded origin is material, not evidence."""

    reason_code = "DOCUMENT_EVIDENCE_PROVENANCE_MISSING"


class EvidenceCustodyBrokenError(DocumentError, ValueError):
    """The custody chain of an evidence item does not verify: a gap, an
    out-of-order transfer, or a hand-off whose recipient is not the next
    entry's holder."""

    reason_code = "DOCUMENT_EVIDENCE_CUSTODY_BROKEN"


class EvidenceBundleSealedError(DocumentError, ValueError):
    """A sealed evidence bundle cannot take further items or be sealed
    again. The bundle digest is what makes the bundle citable; a bundle
    that could still grow would make every prior citation ambiguous.

    The code is `..._ALREADY_SEALED`, not `..._SEALED`: the latter is the
    `AuditEvent.reason_code` that classifies a *successful* seal, and one
    string meaning both "this worked" and "this was refused" would make
    every audit query over it ambiguous."""

    reason_code = "DOCUMENT_EVIDENCE_BUNDLE_ALREADY_SEALED"


class EvidenceBundleIncompleteError(DocumentError, ValueError):
    """A bundle was sealed or cited with no items, or with an item whose
    referenced version no longer verifies."""

    reason_code = "DOCUMENT_EVIDENCE_BUNDLE_INCOMPLETE"


# ---------------------------------------------------------------------------
# Retention and legal hold (PACK-09 remains the owner)
# ---------------------------------------------------------------------------


class RetentionBindingMissingError(DocumentError, ValueError):
    """A governed document exists with no PACK-09 record-class binding, so
    no retention schedule can be resolved for it."""

    reason_code = "DOCUMENT_RETENTION_BINDING_MISSING"


class RecordUnderLegalHoldError(DocumentError, ValueError):
    """A destructive disposition was attempted on material an active
    PACK-09 legal hold covers."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


class LegalHoldStateUnknownError(DocumentError, ValueError):
    """A legal hold covering this material is in an indeterminate state.
    Unknown fails closed and is a different refusal from a known active
    hold - conflating the two would let an unverifiable hold be read as
    "no hold"."""

    reason_code = "LEGAL_HOLD_STATE_UNKNOWN"


class GovernedRecordDeletionForbiddenError(DocumentError, ValueError):
    """A delete was attempted. There is no delete path in this service:
    disposition is a PACK-09-authorized act that leaves destruction
    evidence, never a removal that leaves nothing."""

    reason_code = "GOVERNED_RECORD_DELETION_FORBIDDEN"


class DispositionNotAuthorizedError(DocumentError, PermissionError):
    """A disposition was attempted without the PACK-09 destruction
    authorization it requires, or with one that has gone stale."""

    reason_code = "DOCUMENT_DISPOSITION_NOT_AUTHORIZED"


# ---------------------------------------------------------------------------
# Privacy, events, concurrency
# ---------------------------------------------------------------------------


class ForbiddenIdentityLinkageError(DocumentError, ValueError):
    """A payload, projection or metadata field carries an identity
    attribute or a global person identifier (FIR-INV-001)."""

    reason_code = "DOCUMENT_FORBIDDEN_IDENTITY_LINKAGE"


class VotingLinkageForbiddenError(DocumentError, ValueError):
    """A document record or payload was linked to a ballot, vote, tally,
    delegation or participation credential (FIR-INV-002, FIR-INV-003)."""

    reason_code = "DOCUMENT_VOTING_LINKAGE_FORBIDDEN"


class DocumentContentLeakError(DocumentError, ValueError):
    """Document content, extracted text or a rendition byte string reached
    an event payload, an audit metadata field or a public projection.
    PACK-11 owns content; that ownership is precisely the reason content
    must not travel on the wire."""

    reason_code = "DOCUMENT_CONTENT_LEAK_PREVENTED"


class IdempotencyConflictError(DocumentError, ValueError):
    """The same `event_id` was presented for a different request, or a
    previous execution left an audit row without a recorded command
    result."""

    reason_code = "DOCUMENT_IDEMPOTENCY_CONFLICT"


class OptimisticConcurrencyConflictError(DocumentError, ValueError):
    """The caller's `expected_*_version` does not match the stored
    version: something changed between read and write."""

    reason_code = "OPTIMISTIC_CONCURRENCY_CONFLICT"


class UnsupportedEventVersionError(DocumentError, ValueError):
    """An event envelope carried a major version this service does not
    support. An unknown major version is not processed."""

    reason_code = "EVENT_VERSION_UNSUPPORTED"


class UnknownDocumentEventTypeError(DocumentError, ValueError):
    """An event type outside this service's closed catalogue."""

    reason_code = "DOCUMENT_EVENT_TYPE_UNKNOWN"
