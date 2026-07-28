"""Document Service command and query layer (PACK-11).

Every state-changing command below routes through **one** private frame,
`_guard`, and finishes through **one** private tail, `_finish`. That is
the design idea of this module: a guard a command can forget is a guard
that is not in force, so no command is allowed to assemble its own
sequence of checks.

`_guard` enforces, in this fixed order:

1. **Scope, before anything else.** `RequestContext.require_scope()`
   refuses an undeterminable scope before any other check, any read and
   any write. The target record's scope is then re-asserted against it, so
   a command that obtained its record by some other route still cannot act
   across a boundary (FIR-INV-013).
2. **Authority.** The action's required roles are resolved through
   `authorization.assert_authorized`, which resolves the *presented
   authority object* to an active, effective-dated, scope-matching
   assignment through `AuthorizationPort`. A `role_code` string is never
   proof, and an action absent from `ACTION_REQUIREMENTS` denies.
3. **Role incompatibility and self-approval.** The matrix is re-checked at
   the moment of the act over the roles the acting actor really holds, and
   every prior actor the command names is compared with the acting one
   through `assert_not_self_approval`.
4. **Conflict declaration.** `assert_conflict_declared` fails closed on
   `None` and on `undeclared`, and refuses a declared blocking conflict
   with its own code. This module treats **every** command as a protected
   action, which is stricter than necessary and never softer.
5. **Idempotency.** The caller supplies `RequestContext.event_id`. The
   same `event_id` with the same `request_digest` returns the recorded
   aggregate without re-attempting the transition; the same `event_id`
   with a different digest raises.
6. **Optimistic concurrency.** Every mutating command takes an optional
   `expected_*_version`; a mismatch raises. After idempotency on purpose:
   a true replay must not fail on a version the first execution already
   advanced past.

`_finish` then appends to Audit Core, publishes the canonical envelope to
the `EventSink`, and only then records the idempotency row. **Audit before
event**: an event that escaped without an audit row is an unaccountable
act, and the reverse ordering is the one that produces it.

## The integrity precondition

Every command that touches an existing document re-verifies the version
chain before acting (`_load_chain`). That is more expensive than checking
only at read time, and it is the point: a governed act recorded against a
history that no longer verifies is an act whose context nobody can trust,
and recording it would add a trustworthy-looking row to an untrustworthy
history.

## Two-tier scope errors (PACK-09's pattern, carried over unchanged)

`_load_scoped` reports a record in a foreign scope with the same
`DocumentRecordNotFoundError` and the same message shape as a record that
does not exist, so a foreign identifier discloses nothing. The specific
`ORGANIZATION_SCOPE_MISMATCH` refusal is reachable only by a caller that
already presented an authority scoped *to that organization*.

## What this module deliberately does not do

No production persistence, no HTTP surface, no real event bus (PACK-13),
no retention schedule or legal-hold decision (PACK-09 owns both; this
service records their answers and refuses without them), no privileged or
break-glass access (PACK-12), no identity of any kind, and no
signature-verification or admissibility *reasoning* - only the recording
of determinations made by an authority. It imports only `epd2_core`,
`epd2_audit_core` and its own package. No command reads system time: a
`Clock` is injected into every one of them.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope
from epd2_document_service import events as document_events
from epd2_document_service.authorization import (
    AuthorizationPort,
    DocumentAction,
    assert_access_permitted,
    assert_authorized,
    assert_not_self_approval,
    assert_reader_independent,
    assert_reviewer_qualified,
    assert_roles_compatible,
    resolve_document_role,
)
from epd2_document_service.determinations import (
    AdmissibilityDetermination,
    AdmissibilityStatus,
    DocumentResolution,
    SignatureDetermination,
    SignatureForm,
    SignatureStatus,
    absent_admissibility_status,
    absent_signature_status,
    require_admissibility_determination,
    require_signature_determination,
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
    assert_disposition_authorized,
    assert_no_destruction_under_hold,
    assert_publishable,
    assert_review_complete,
    default_review_requirement,
)
from epd2_document_service.domain import (
    AccessProfile,
    AuthorityReference,
    ContentDescriptor,
    DispositionAuthorization,
    DocumentKind,
    LegalHoldBinding,
    OrganizationalScopeRef,
    Provenance,
    ReasonCoded,
    RequestContext,
    RetentionBinding,
    SensitivityClass,
    assert_conflict_declared,
    content_digest_of,
    deterministic_digest,
)
from epd2_document_service.evidence import (
    CustodyAction,
    CustodyEvent,
    EvidenceBundle,
    EvidenceRecord,
    assert_evidence_admissible_shape,
)
from epd2_document_service.exceptions import (
    DocumentApprovalMissingError,
    DocumentCorrectionTargetInvalidError,
    DocumentDeterminationNotPermittedError,
    DocumentRecordNotFoundError,
    DocumentTransitionInvalidError,
    IdempotencyConflictError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeMismatchError,
)
from epd2_document_service.projections import (
    RestrictedDocumentProjection,
    build_restricted_projection,
)
from epd2_document_service.references import document_citation
from epd2_document_service.storage import (
    AdmissibilityDeterminationStore,
    ApprovalRecordStore,
    CommandIdempotencyStore,
    ContentStore,
    DocumentVersionStore,
    EventSink,
    EvidenceBundleStore,
    EvidenceRecordStore,
    GovernedDocumentStore,
    IdempotencyRecord,
    PublicationAuthorizationStore,
    PublicationRenditionStore,
    ReviewRecordStore,
    RevocationStore,
    SignatureDeterminationStore,
    SupersessionStore,
)
from epd2_document_service.versions import (
    ChainVerificationResult,
    DocumentVersion,
    VersionState,
    assert_version_chain_intact,
    next_version_hash_base,
    seal_version,
    verify_version_chain,
    verify_version_content,
)

#: The audit policy version recorded on every audit row this service
#: appends. A constant, not a parameter: a caller-supplied policy version
#: is a caller-controlled audit field.
AUDIT_POLICY_VERSION = "document-service/pack-11/v1"

_SOURCE_SERVICE = "document-service"


# ---------------------------------------------------------------------------
# The ports the caller assembles
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentStores:
    """Every store one command frame might need, in one object.

    A single parameter rather than fourteen. Passing them individually
    would make each command signature a list of infrastructure, and adding
    a store later would touch every command - which is how a command ends
    up quietly skipping the one it was not given."""

    documents: GovernedDocumentStore
    versions: DocumentVersionStore
    content: ContentStore
    reviews: ReviewRecordStore
    approvals: ApprovalRecordStore
    publication_authorizations: PublicationAuthorizationStore
    renditions: PublicationRenditionStore
    supersessions: SupersessionStore
    revocations: RevocationStore
    signatures: SignatureDeterminationStore
    admissibilities: AdmissibilityDeterminationStore
    evidence: EvidenceRecordStore
    bundles: EvidenceBundleStore
    idempotency: CommandIdempotencyStore
    audit: AuditEventStore
    sink: EventSink


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentResult:
    document: GovernedDocument
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class VersionResult:
    document: GovernedDocument
    version: DocumentVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ReviewResult:
    review: ReviewRecord
    version: DocumentVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ApprovalResult:
    approval: ApprovalRecord
    version: DocumentVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PublicationAuthorizationResult:
    authorization: PublicationAuthorization
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PublicationResult:
    version: DocumentVersion
    authorization: PublicationAuthorization
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RenditionResult:
    rendition: PublicationRendition
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SupersessionResult:
    record: SupersessionRecord
    superseded_version: DocumentVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RevocationResult:
    record: RevocationRecord
    version: DocumentVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SignatureDeterminationResult:
    determination: SignatureDetermination
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AdmissibilityDeterminationResult:
    determination: AdmissibilityDetermination
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class EvidenceResult:
    evidence: EvidenceRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class BundleResult:
    bundle: EvidenceBundle
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DispositionResult:
    document: GovernedDocument
    authorization: DispositionAuthorization
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# Private frame
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _CommandGuard:
    """Everything `_guard` resolved, handed to the command body."""

    command: str
    action: DocumentAction
    scope: OrganizationalScopeRef
    authority: AuthorityReference
    actor: ActorRef
    now: datetime
    event_id: UUID
    request_digest: str
    correlation_id: UUID
    causation_id: UUID | None
    replay: IdempotencyRecord | None


def _actor_for(authority: AuthorityReference) -> ActorRef:
    """The envelope actor.

    Derived from the *authority*, never from a person: `actor_id` is the
    authority assignment's own id, so the audit trail records which
    office acted. Which human exercised the office is deliberately not
    knowable from here (FIR-INV-001)."""
    return ActorRef(actor_id=authority.authority_id, actor_type="organizational_authority")


def _as_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


def _correlation_uuid(context: RequestContext, *, fallback: UUID) -> UUID:
    return _as_uuid(context.correlation_id) or fallback


def _request_digest(command: str, parts: Sequence[str]) -> str:
    return deterministic_digest(command, *parts)


def _raise_not_found(what: str, identifier: UUID) -> None:
    raise DocumentRecordNotFoundError(f"no {what} with id {identifier}")


def _guard(
    stores: DocumentStores,
    *,
    command: str,
    action: DocumentAction,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    request_parts: Sequence[str],
    target_scope: OrganizationalScopeRef | None = None,
    prior_actor_references: Sequence[str] = (),
    current_version: int | None = None,
    expected_version: int | None = None,
    version_label: str = "record",
) -> _CommandGuard:
    """The one frame every state-changing command routes through.

    The order of the six checks is the guarantee, not an implementation
    detail. Nothing here is conditional on a flag, an environment or a
    privileged grant: FIR-INV-006 forbids it and
    `authorization.NO_BREAK_GLASS_NOTE` states why in full."""
    scope = context.require_scope()
    if target_scope is not None:
        target_scope.assert_matches(scope)

    authority = assert_authorized(action, context.authorities, scope, port=port)

    acting_actor = authority.actor_reference.strip()
    if acting_actor:
        assert_roles_compatible(port.held_roles(acting_actor, scope))
    for prior in prior_actor_references:
        assert_not_self_approval(authority.actor_reference, prior, action=command)

    assert_conflict_declared(context.conflict, action=command)

    now = clock.now()
    event_id = context.event_id
    if event_id is None:
        raise IdempotencyConflictError(
            f"{command} requires a caller-supplied event_id on the request context"
        )
    digest = _request_digest(command, request_parts)
    recorded = stores.idempotency.get(event_id)
    if recorded is not None:
        if recorded.command != command or recorded.request_digest != digest:
            raise IdempotencyConflictError(
                f"event_id {event_id} was already used by {recorded.command} with different "
                "content; the same event_id may only replay the identical request"
            )
        return _CommandGuard(
            command=command,
            action=action,
            scope=scope,
            authority=authority,
            actor=_actor_for(authority),
            now=now,
            event_id=event_id,
            request_digest=digest,
            correlation_id=_correlation_uuid(context, fallback=event_id),
            causation_id=_as_uuid(context.causation_id),
            replay=recorded,
        )
    # The second line of defence. An audit row under this event_id with no
    # command record means a previous run appended its audit entry and died
    # before persisting the command record. Re-running the transition now
    # would mutate the aggregate a second time under one audit row.
    if stores.audit.get_by_event_id(event_id) is not None:
        raise IdempotencyConflictError(
            f"event_id {event_id} already has an audit entry but no recorded command result; "
            "the previous execution did not complete and is not safely replayable"
        )

    if current_version is not None and expected_version is not None:
        if current_version != expected_version:
            raise OptimisticConcurrencyConflictError(
                f"{version_label} version is {current_version}, caller expected {expected_version}"
            )

    return _CommandGuard(
        command=command,
        action=action,
        scope=scope,
        authority=authority,
        actor=_actor_for(authority),
        now=now,
        event_id=event_id,
        request_digest=digest,
        correlation_id=_correlation_uuid(context, fallback=event_id),
        causation_id=_as_uuid(context.causation_id),
        replay=None,
    )


def _finish(
    stores: DocumentStores,
    guard: _CommandGuard,
    *,
    event: EventEnvelope,
    aggregate_id: UUID,
    target_type: str,
    reason_code: str,
    before_hash: str,
    after_hash: str,
    clock: Clock,
) -> AuditEvent:
    """Append the audit row, publish the envelope, record the command.

    The order is the point. **Audit first**: an event that reached the
    stream without an audit row is an act nobody can account for.
    **Idempotency last**: the command record claims "this ran and produced
    that", and it must not be able to claim it before both durable effects
    exist."""
    audit_event = append_audit_event(
        stores.audit,
        AppendAuditEventRequest(
            audit_event_id=guard.event_id,
            event_type=event.event_type,
            occurred_at=guard.now,
            actor_id=guard.actor.actor_id,
            actor_type=guard.actor.actor_type,
            target_type=target_type,
            target_id=aggregate_id,
            action=guard.command,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=guard.correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=after_hash,
        ),
        clock=clock,
    )
    stores.sink.publish(event)
    stores.idempotency.put(
        IdempotencyRecord(
            event_id=guard.event_id,
            command=guard.command,
            request_digest=guard.request_digest,
            aggregate_id=aggregate_id,
            recorded_at=guard.now,
        )
    )
    return audit_event


def _replayed_audit(stores: DocumentStores, guard: _CommandGuard) -> AuditEvent:
    audit_event = stores.audit.get_by_event_id(guard.event_id)
    if audit_event is None:  # pragma: no cover - unreachable through _finish
        raise IdempotencyConflictError(
            f"event_id {guard.event_id} has a recorded command result but no audit entry"
        )
    return audit_event


def _state_hash(payload: dict[str, object]) -> str:
    """The canonical hash of a state snapshot, for audit before/after.

    Uses `epd2_core.canonical_json` so two independently-constructed
    representations of the same logical state hash identically - the same
    guarantee `versions.compute_version_hash` and `audit-core` rely on."""
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _load_document(
    stores: DocumentStores, document_id: UUID, scope: OrganizationalScopeRef
) -> GovernedDocument:
    """Load a document in the caller's scope, or report not-found.

    A record in a foreign scope reports the *same* not-found error as one
    that does not exist. That is deliberate: distinguishing them would let
    a caller confirm the existence of another organization's documents by
    probing identifiers."""
    document = stores.documents.get(document_id)
    if document is None or document.scope.organization_id != scope.organization_id:
        _raise_not_found("governed document", document_id)
        raise AssertionError  # pragma: no cover - _raise_not_found always raises
    return document


def _load_chain(stores: DocumentStores, document: GovernedDocument) -> tuple[DocumentVersion, ...]:
    """Load and verify a document's version chain before acting on it.

    Verified on *every* command, not only on reads. A governed act
    recorded against a history that no longer verifies is an act whose
    context nobody can trust; refusing costs a hash recomputation per
    version and buys the guarantee FIR-INV-010 states."""
    versions = stores.versions.list_for_document(document.document_id)
    if versions:
        assert_version_chain_intact(document.document_id, versions)
    return versions


def _load_version(
    stores: DocumentStores, document: GovernedDocument, version_number: int
) -> DocumentVersion:
    version = stores.versions.get_by_number(document.document_id, version_number)
    if version is None:
        raise DocumentRecordNotFoundError(
            f"document {document.document_id} has no version {version_number}"
        )
    return version


# ---------------------------------------------------------------------------
# Commands: registration and versions
# ---------------------------------------------------------------------------


def register_document(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    kind: DocumentKind,
    sensitivity: SensitivityClass,
    title_reference: str,
    reason: ReasonCoded,
    review_policy_reference: str,
    review_policy_version: int = 1,
    review_requirement: ReviewRequirement | None = None,
    subject_reference: str | None = None,
) -> DocumentResult:
    """Register a governed document. No version yet, no content yet.

    Registration and the first version are two acts on purpose: a document
    can legitimately exist before its first draft (a minutes record
    created when the meeting is convened), and collapsing the two would
    make "this document exists but has no content yet" unrepresentable."""
    guard = _guard(
        stores,
        command="register_document",
        action=DocumentAction.REGISTER_DOCUMENT,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(kind), str(sensitivity), title_reference),
    )
    if guard.replay is not None:
        existing = stores.documents.get(guard.replay.aggregate_id)
        if existing is None:  # pragma: no cover - replay implies it was stored
            _raise_not_found("governed document", guard.replay.aggregate_id)
            raise AssertionError  # pragma: no cover
        return DocumentResult(
            document=existing,
            event=_rebuilt_registration_event(existing, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    requirement = review_requirement or default_review_requirement(
        kind, policy_reference=review_policy_reference, policy_version=review_policy_version
    )
    document = GovernedDocument(
        document_id=document_id,
        scope=guard.scope,
        kind=kind,
        sensitivity=sensitivity,
        title_reference=title_reference,
        created_at=guard.now,
        custodian=guard.authority,
        review_requirement=requirement,
        subject_reference=subject_reference,
    )
    stores.documents.save(document)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="governed_document.registered",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=document.document_id,
        scope=guard.scope,
        payload=document_events.document_registered_payload(document),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=document.document_id,
        target_type="GovernedDocument",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(document.to_state_payload()),
        clock=clock,
    )
    return DocumentResult(document=document, event=event, audit_event=audit_event)


def _rebuilt_registration_event(document: GovernedDocument, guard: _CommandGuard) -> EventEnvelope:
    """Rebuild the envelope a replayed registration originally emitted.

    Deterministic: same event id, same payload, same hash. Returning a
    freshly-built envelope rather than a stored one keeps the sink free of
    a persistence responsibility it does not have in this round."""
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="governed_document.registered",
        occurred_at=document.created_at,
        actor=guard.actor,
        aggregate_id=document.document_id,
        scope=document.scope,
        payload=document_events.document_registered_payload(document),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def record_version(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_id: UUID,
    content: bytes,
    media_type: str,
    title_reference: str,
    provenance: Provenance,
    reason: ReasonCoded,
    filename_reference: str | None = None,
    corrects_version_number: int | None = None,
    correction_reason: ReasonCoded | None = None,
    expected_document_version: int | None = None,
) -> VersionResult:
    """Record a new immutable version, storing its content and sealing its
    place in the chain.

    Content goes into the content-addressed store *first*, so a version
    can never reference content that was not stored: the reverse ordering
    would leave a sealed, chained version pointing at nothing if the
    content write failed."""
    document = _load_document(stores, document_id, context.require_scope())
    guard = _guard(
        stores,
        command="record_version",
        action=DocumentAction.RECORD_VERSION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_id), content_digest_of(content)),
        target_scope=document.scope,
        current_version=document.document_version,
        expected_version=expected_document_version,
        version_label="document",
    )
    if guard.replay is not None:
        stored = stores.versions.get(version_id)
        if stored is None:  # pragma: no cover
            _raise_not_found("document version", version_id)
            raise AssertionError  # pragma: no cover
        return VersionResult(
            document=document,
            version=stored,
            event=_rebuilt_version_event(stored, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    if document.state is not DocumentState.ACTIVE:
        raise DocumentTransitionInvalidError(
            f"no version may be recorded on a {document.state.value} document"
        )
    existing = _load_chain(stores, document)
    if corrects_version_number is not None:
        target = stores.versions.get_by_number(document_id, corrects_version_number)
        if target is None:
            raise DocumentCorrectionTargetInvalidError(
                f"document {document_id} has no version {corrects_version_number} to correct"
            )
        if target.state is VersionState.REVOKED:
            raise DocumentCorrectionTargetInvalidError(
                "a revoked version cannot be corrected; it can only be replaced"
            )

    digest = stores.content.put(content)
    number, previous_hash = next_version_hash_base(existing)
    before_hash = _state_hash(document.to_state_payload())
    version = seal_version(
        DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            scope=document.scope,
            version_number=number,
            kind=document.kind,
            sensitivity=document.sensitivity,
            title_reference=title_reference,
            content=ContentDescriptor(
                digest=digest,
                media_type=media_type,
                byte_length=len(content),
                filename_reference=filename_reference,
            ),
            provenance=provenance,
            recorded_at=guard.now,
            recorded_by=guard.authority,
            previous_version_hash=previous_hash,
            version_hash="0" * 64,
            corrects_version_number=corrects_version_number,
            correction_reason=correction_reason,
        )
    )
    stores.versions.append(version)
    document = document.with_recorded_version(version, at=guard.now, reason=reason)
    stores.documents.save(document)

    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type=(
            "document_version.corrected"
            if corrects_version_number is not None
            else "document_version.recorded"
        ),
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=version.version_id,
        scope=guard.scope,
        payload=document_events.version_recorded_payload(version),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=version.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=before_hash,
        after_hash=_state_hash(document.to_state_payload()),
        clock=clock,
    )
    return VersionResult(document=document, version=version, event=event, audit_event=audit_event)


def _rebuilt_version_event(version: DocumentVersion, guard: _CommandGuard) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type=(
            "document_version.corrected"
            if version.corrects_version_number is not None
            else "document_version.recorded"
        ),
        occurred_at=version.recorded_at,
        actor=guard.actor,
        aggregate_id=version.version_id,
        scope=version.scope,
        payload=document_events.version_recorded_payload(version),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def _transition_version(
    stores: DocumentStores,
    guard: _CommandGuard,
    version: DocumentVersion,
    target: VersionState,
    *,
    action: str,
    reason: ReasonCoded,
    event_type: str,
    clock: Clock,
) -> tuple[DocumentVersion, EventEnvelope, AuditEvent]:
    """The shared tail for every version state change.

    One place that appends the history entry, writes it back through the
    store's narrow `record_state_change`, builds the envelope and finishes
    - so five commands cannot drift into five slightly different
    orderings."""
    before = _state_hash({"state": str(version.state), "hash": version.version_hash})
    updated = version.with_state(
        target, at=guard.now, action=action, reason=reason, authority=guard.authority
    )
    stores.versions.record_state_change(updated)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type=event_type,
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.version_id,
        scope=guard.scope,
        payload=document_events.version_state_changed_payload(updated, reason),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash({"state": str(updated.state), "hash": updated.version_hash}),
        clock=clock,
    )
    return updated, event, audit_event


def submit_for_review(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    reason: ReasonCoded,
) -> VersionResult:
    """Move a draft version into review."""
    document = _load_document(stores, document_id, context.require_scope())
    guard = _guard(
        stores,
        command="submit_for_review",
        action=DocumentAction.SUBMIT_FOR_REVIEW,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number)),
        target_scope=document.scope,
    )
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    if guard.replay is not None:
        return VersionResult(
            document=document,
            version=version,
            event=_rebuilt_version_event(version, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    updated, event, audit_event = _transition_version(
        stores,
        guard,
        version,
        VersionState.IN_REVIEW,
        action="submitted_for_review",
        reason=reason,
        event_type="document_version.submitted_for_review",
        clock=clock,
    )
    return VersionResult(document=document, version=updated, event=event, audit_event=audit_event)


def record_review(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    review_id: UUID,
    review_kind: ReviewKind,
    outcome: ReviewOutcome,
    reason: ReasonCoded,
    finding_reference: str | None = None,
    resolves_review_id: UUID | None = None,
) -> ReviewResult:
    """Record one review of one version.

    The reviewer must not be the actor who recorded the version: that is
    the first of the three separations, enforced here through
    `prior_actor_references` rather than left to the role matrix, because
    the matrix answers "may one person hold both roles?" and this answers
    "did one person perform both acts?"."""
    document = _load_document(stores, document_id, context.require_scope())
    versions = stores.versions.list_for_document(document_id)
    if versions:
        assert_version_chain_intact(document_id, versions)
    version = _load_version(stores, document, version_number)
    action = (
        DocumentAction.RECORD_LEGAL_REVIEW
        if review_kind is ReviewKind.LEGAL
        else DocumentAction.RECORD_REVIEW
    )
    guard = _guard(
        stores,
        command="record_review",
        action=action,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(review_id), str(review_kind)),
        target_scope=document.scope,
        prior_actor_references=(version.recorded_by.actor_reference,),
    )
    role = resolve_document_role(guard.authority.role_code)
    if role is not None:
        assert_reviewer_qualified(version.kind, role)
    if guard.replay is not None:
        stored_reviews = stores.reviews.list_for_version(document_id, version_number)
        for candidate in stored_reviews:
            if candidate.review_id == review_id:
                return ReviewResult(
                    review=candidate,
                    version=version,
                    event=_rebuilt_review_event(candidate, guard),
                    audit_event=_replayed_audit(stores, guard),
                )

    if version.state is not VersionState.IN_REVIEW:
        raise DocumentTransitionInvalidError(
            f"a review may only be recorded on a version in review; version "
            f"{version_number} is {version.state.value}"
        )
    review = ReviewRecord(
        review_id=review_id,
        document_id=document_id,
        version_number=version_number,
        scope=document.scope,
        review_kind=review_kind,
        outcome=outcome,
        reviewed_at=guard.now,
        reviewer=guard.authority,
        reason=reason,
        finding_reference=finding_reference,
        resolves_review_id=resolves_review_id,
    )
    stores.reviews.append(review)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.reviewed",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=version.version_id,
        scope=guard.scope,
        payload=document_events.version_reviewed_payload(review),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=version.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(review.to_payload()),
        clock=clock,
    )
    return ReviewResult(review=review, version=version, event=event, audit_event=audit_event)


def _rebuilt_review_event(review: ReviewRecord, guard: _CommandGuard) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.reviewed",
        occurred_at=review.reviewed_at,
        actor=guard.actor,
        aggregate_id=review.review_id,
        scope=review.scope,
        payload=document_events.version_reviewed_payload(review),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def approve_version(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    approval_id: UUID,
    reason: ReasonCoded,
) -> ApprovalResult:
    """Approve a reviewed version.

    Three separations are enforced here at once, and each closes a
    different hole: the approver is not the recorder of the version, the
    approver is not any of the reviewers, and every required review kind
    is present with no unresolved blocking finding."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    reviews = stores.reviews.list_for_version(document_id, version_number)
    prior_actors = [version.recorded_by.actor_reference]
    prior_actors.extend(r.reviewer.actor_reference for r in reviews)
    guard = _guard(
        stores,
        command="approve_version",
        action=DocumentAction.APPROVE_VERSION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(approval_id)),
        target_scope=document.scope,
        prior_actor_references=tuple(prior_actors),
    )
    if guard.replay is not None:
        stored = stores.approvals.get_for_version(document_id, version_number)
        if stored is not None:
            return ApprovalResult(
                approval=stored,
                version=version,
                event=_rebuilt_approval_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )

    assert_review_complete(document.review_requirement, reviews, version_number=version_number)
    approval = ApprovalRecord(
        approval_id=approval_id,
        document_id=document_id,
        version_number=version_number,
        scope=document.scope,
        approved_at=guard.now,
        approver=guard.authority,
        approved_version_hash=version.version_hash,
        reason=reason,
    )
    stores.approvals.create_once(approval)
    updated = version.with_state(
        VersionState.APPROVED,
        at=guard.now,
        action="approved",
        reason=reason,
        authority=guard.authority,
    )
    stores.versions.record_state_change(updated)
    document = document.with_current_version(
        version_number, at=guard.now, reason=reason, authority=guard.authority
    )
    stores.documents.save(document)

    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.approved",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.version_id,
        scope=guard.scope,
        payload=document_events.version_approved_payload(approval),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=_state_hash({"state": str(version.state)}),
        after_hash=_state_hash(approval.to_payload()),
        clock=clock,
    )
    return ApprovalResult(approval=approval, version=updated, event=event, audit_event=audit_event)


def _rebuilt_approval_event(
    approval: ApprovalRecord, guard: _CommandGuard, scope: OrganizationalScopeRef
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.approved",
        occurred_at=approval.approved_at,
        actor=guard.actor,
        aggregate_id=approval.approval_id,
        scope=scope,
        payload=document_events.version_approved_payload(approval),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def return_for_revision(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    reason: ReasonCoded,
) -> VersionResult:
    """Return a version in review for revision.

    Terminal for that version. The revision is version N+1, recorded
    through `record_version` - which is what makes "historical versions
    are never rewritten" true of the workflow and not only of storage."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="return_for_revision",
        action=DocumentAction.RETURN_FOR_REVISION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number)),
        target_scope=document.scope,
        prior_actor_references=(version.recorded_by.actor_reference,),
    )
    if guard.replay is not None:
        return VersionResult(
            document=document,
            version=version,
            event=_rebuilt_version_event(version, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    updated, event, audit_event = _transition_version(
        stores,
        guard,
        version,
        VersionState.RETURNED_FOR_REVISION,
        action="returned_for_revision",
        reason=reason,
        event_type="document_version.returned_for_revision",
        clock=clock,
    )
    return VersionResult(document=document, version=updated, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Commands: publication
# ---------------------------------------------------------------------------


def authorize_publication(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    authorization_id: UUID,
    audience: PublicationAudience,
    disclosure_obligation_reference: str,
    reason: ReasonCoded,
) -> PublicationAuthorizationResult:
    """Authorize publication of an approved version.

    Separate from `publish_version` and from `approve_version`, held by a
    third role. The publication officer is not the approver and not the
    author, so reaching the public requires three distinct actors."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    approval = stores.approvals.get_for_version(document_id, version_number)
    prior_actors = [version.recorded_by.actor_reference]
    if approval is not None:
        prior_actors.append(approval.approver.actor_reference)
    guard = _guard(
        stores,
        command="authorize_publication",
        action=DocumentAction.AUTHORIZE_PUBLICATION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(authorization_id)),
        target_scope=document.scope,
        prior_actor_references=tuple(prior_actors),
    )
    if guard.replay is not None:
        stored = stores.publication_authorizations.get_for_version(document_id, version_number)
        if stored is not None:
            return PublicationAuthorizationResult(
                authorization=stored,
                event=_rebuilt_publication_authorization_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )

    if approval is None:
        raise DocumentApprovalMissingError(
            "publication may only be authorized for an approved version"
        )
    authorization = PublicationAuthorization(
        authorization_id=authorization_id,
        document_id=document_id,
        version_number=version_number,
        scope=document.scope,
        audience=audience,
        authorized_at=guard.now,
        authorized_by=guard.authority,
        disclosure_obligation_reference=disclosure_obligation_reference,
        reason=reason,
    )
    stores.publication_authorizations.create_once(authorization)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_publication.authorized",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=authorization.authorization_id,
        scope=guard.scope,
        payload=document_events.publication_authorized_payload(authorization),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=authorization.authorization_id,
        target_type="PublicationRendition",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(authorization.to_payload()),
        clock=clock,
    )
    return PublicationAuthorizationResult(
        authorization=authorization, event=event, audit_event=audit_event
    )


def _rebuilt_publication_authorization_event(
    authorization: PublicationAuthorization,
    guard: _CommandGuard,
    scope: OrganizationalScopeRef,
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_publication.authorized",
        occurred_at=authorization.authorized_at,
        actor=guard.actor,
        aggregate_id=authorization.authorization_id,
        scope=scope,
        payload=document_events.publication_authorized_payload(authorization),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def publish_version(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    reason: ReasonCoded,
) -> PublicationResult:
    """Publish an approved, publication-authorized version."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="publish_version",
        action=DocumentAction.PUBLISH_VERSION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number)),
        target_scope=document.scope,
    )
    authorization = stores.publication_authorizations.get_for_version(document_id, version_number)
    if guard.replay is not None and authorization is not None:
        return PublicationResult(
            version=version,
            authorization=authorization,
            event=_rebuilt_version_event(version, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    approval = stores.approvals.get_for_version(document_id, version_number)
    assert_publishable(document, version, approval, authorization)
    if authorization is None:  # pragma: no cover - assert_publishable already refused
        raise DocumentApprovalMissingError("publication authorization disappeared mid-command")

    before = _state_hash({"state": str(version.state)})
    updated = version.with_state(
        VersionState.PUBLISHED,
        at=guard.now,
        action="published",
        reason=reason,
        authority=guard.authority,
    )
    stores.versions.record_state_change(updated)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_publication.published",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.version_id,
        scope=guard.scope,
        payload=document_events.version_published_payload(updated, authorization),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash({"state": str(updated.state)}),
        clock=clock,
    )
    return PublicationResult(
        version=updated, authorization=authorization, event=event, audit_event=audit_event
    )


def issue_publication_rendition(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    rendition_id: UUID,
    rendition_content: bytes,
    media_type: str,
    reason: ReasonCoded,
) -> RenditionResult:
    """**ADR-053 interface requirement 4.**

    Produce a citable rendition identifier for a published version. The
    rendition's bytes go into the same content-addressed store as the
    source content; what leaves this service is
    `rendition.citation_reference`, which a public view can quote without
    the content travelling with it."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="issue_publication_rendition",
        action=DocumentAction.ISSUE_PUBLICATION_RENDITION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(rendition_id)),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.renditions.get(rendition_id)
        if stored is not None:
            return RenditionResult(
                rendition=stored,
                event=_rebuilt_rendition_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )

    authorization = stores.publication_authorizations.get_for_version(document_id, version_number)
    if authorization is None or version.state is not VersionState.PUBLISHED:
        raise DocumentApprovalMissingError(
            "a rendition may only be issued for a published, publication-authorized version"
        )
    digest = stores.content.put(rendition_content)
    rendition = PublicationRendition(
        rendition_id=rendition_id,
        document_id=document_id,
        version_number=version_number,
        scope=document.scope,
        audience=authorization.audience,
        media_type=media_type,
        rendition_digest=digest,
        source_version_hash=version.version_hash,
        issued_at=guard.now,
        issued_by=guard.authority,
    )
    stores.renditions.append(rendition)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_publication.rendition_issued",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=rendition.rendition_id,
        scope=guard.scope,
        payload=document_events.rendition_issued_payload(rendition),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=rendition.rendition_id,
        target_type="PublicationRendition",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(rendition.to_payload()),
        clock=clock,
    )
    return RenditionResult(rendition=rendition, event=event, audit_event=audit_event)


def _rebuilt_rendition_event(
    rendition: PublicationRendition, guard: _CommandGuard, scope: OrganizationalScopeRef
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_publication.rendition_issued",
        occurred_at=rendition.issued_at,
        actor=guard.actor,
        aggregate_id=rendition.rendition_id,
        scope=scope,
        payload=document_events.rendition_issued_payload(rendition),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


# ---------------------------------------------------------------------------
# Commands: supersession and revocation
# ---------------------------------------------------------------------------


def supersede_version(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    superseded_version_number: int,
    superseding_version_number: int,
    supersession_id: UUID,
    reason: ReasonCoded,
) -> SupersessionResult:
    """Record that a later version replaces an earlier one.

    Both versions must exist and the superseding one must itself be
    approved: "superseded by a draft" would make a governed record
    non-current on the strength of something nobody has approved."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    superseded = _load_version(stores, document, superseded_version_number)
    superseding = _load_version(stores, document, superseding_version_number)
    guard = _guard(
        stores,
        command="supersede_version",
        action=DocumentAction.SUPERSEDE_VERSION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(document_id),
            str(superseded_version_number),
            str(superseding_version_number),
        ),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.supersessions.get_for_version(document_id, superseded_version_number)
        if stored is not None:
            return SupersessionResult(
                record=stored,
                superseded_version=superseded,
                event=_rebuilt_supersession_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )

    if not superseding.is_citable:
        raise DocumentTransitionInvalidError(
            f"version {superseding_version_number} is {superseding.state.value} and cannot "
            "supersede anything until it is approved"
        )
    record = SupersessionRecord(
        supersession_id=supersession_id,
        document_id=document_id,
        scope=document.scope,
        superseded_version_number=superseded_version_number,
        superseding_version_number=superseding_version_number,
        recorded_at=guard.now,
        recorded_by=guard.authority,
        reason=reason,
    )
    stores.supersessions.append(record)
    updated = superseded.with_state(
        VersionState.SUPERSEDED,
        at=guard.now,
        action="superseded",
        reason=reason,
        authority=guard.authority,
    )
    stores.versions.record_state_change(updated)
    document = document.with_current_version(
        superseding_version_number, at=guard.now, reason=reason, authority=guard.authority
    )
    stores.documents.save(document)

    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.superseded",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.version_id,
        scope=guard.scope,
        payload=document_events.version_superseded_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=_state_hash({"state": str(superseded.state)}),
        after_hash=_state_hash(record.to_payload()),
        clock=clock,
    )
    return SupersessionResult(
        record=record, superseded_version=updated, event=event, audit_event=audit_event
    )


def _rebuilt_supersession_event(
    record: SupersessionRecord, guard: _CommandGuard, scope: OrganizationalScopeRef
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.superseded",
        occurred_at=record.recorded_at,
        actor=guard.actor,
        aggregate_id=record.supersession_id,
        scope=scope,
        payload=document_events.version_superseded_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def revoke_version(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    revocation_id: UUID,
    reason: ReasonCoded,
    replacement_version_number: int | None = None,
) -> RevocationResult:
    """Withdraw a version's effect. The version itself is untouched.

    Nothing is deleted, the chain is not re-computed, and a previously
    published version remains publicly representable as a tombstone. A
    revocation that removed the record would make the revocation itself
    unprovable."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="revoke_version",
        action=DocumentAction.REVOKE_VERSION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(revocation_id)),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.revocations.get_for_version(document_id, version_number)
        if stored is not None:
            return RevocationResult(
                record=stored,
                version=version,
                event=_rebuilt_revocation_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )

    record = RevocationRecord(
        revocation_id=revocation_id,
        document_id=document_id,
        scope=document.scope,
        version_number=version_number,
        revoked_at=guard.now,
        revoked_by=guard.authority,
        reason=reason,
        replacement_version_number=replacement_version_number,
    )
    stores.revocations.append(record)
    updated = version.with_state(
        VersionState.REVOKED,
        at=guard.now,
        action="revoked",
        reason=reason,
        authority=guard.authority,
    )
    stores.versions.record_state_change(updated)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.revoked",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.version_id,
        scope=guard.scope,
        payload=document_events.version_revoked_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="DocumentVersion",
        reason_code=reason.reason_code,
        before_hash=_state_hash({"state": str(version.state)}),
        after_hash=_state_hash(record.to_payload()),
        clock=clock,
    )
    return RevocationResult(record=record, version=updated, event=event, audit_event=audit_event)


def _rebuilt_revocation_event(
    record: RevocationRecord, guard: _CommandGuard, scope: OrganizationalScopeRef
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_version.revoked",
        occurred_at=record.revoked_at,
        actor=guard.actor,
        aggregate_id=record.revocation_id,
        scope=scope,
        payload=document_events.version_revoked_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


# ---------------------------------------------------------------------------
# Commands: retention, legal hold, disposition
# ---------------------------------------------------------------------------


def bind_retention(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    binding: RetentionBinding,
    reason: ReasonCoded,
) -> DocumentResult:
    """Bind a document to a PACK-09 record class and retention policy
    version. PACK-11 stores the binding; PACK-09 owns the schedule."""
    document = _load_document(stores, document_id, context.require_scope())
    guard = _guard(
        stores,
        command="bind_retention",
        action=DocumentAction.BIND_RETENTION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), binding.record_class_reference),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        return DocumentResult(
            document=document,
            event=_rebuilt_registration_event(document, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    before = _state_hash(document.to_state_payload())
    document = document.with_retention(
        binding, at=guard.now, reason=reason, authority=guard.authority
    )
    stores.documents.save(document)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="governed_document.retention_bound",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=document.document_id,
        scope=guard.scope,
        payload=document_events.retention_bound_payload(document, binding),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=document.document_id,
        target_type="GovernedDocument",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash(document.to_state_payload()),
        clock=clock,
    )
    return DocumentResult(document=document, event=event, audit_event=audit_event)


def record_legal_hold(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    binding: LegalHoldBinding,
    reason: ReasonCoded,
) -> DocumentResult:
    """Record PACK-09's answer about a legal hold covering this document.

    This never *decides* a hold. It records an observation, with the
    moment it was observed, so that a later refusal can say which answer
    it acted on. An observation of an `indeterminate` hold is a valid,
    storable answer and makes every destructive act on this document fail
    closed (FIR-DATA-003)."""
    document = _load_document(stores, document_id, context.require_scope())
    guard = _guard(
        stores,
        command="record_legal_hold",
        action=DocumentAction.RECORD_LEGAL_HOLD,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), binding.hold_reference, str(binding.state)),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        return DocumentResult(
            document=document,
            event=_rebuilt_registration_event(document, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    before = _state_hash(document.to_state_payload())
    document = document.with_legal_hold(
        binding, at=guard.now, reason=reason, authority=guard.authority
    )
    stores.documents.save(document)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="governed_document.legal_hold_observed",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=document.document_id,
        scope=guard.scope,
        payload=document_events.legal_hold_observed_payload(document, binding),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=document.document_id,
        target_type="GovernedDocument",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash(document.to_state_payload()),
        clock=clock,
    )
    return DocumentResult(document=document, event=event, audit_event=audit_event)


def authorize_disposition(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    authorization: DispositionAuthorization,
    reason: ReasonCoded,
) -> DispositionResult:
    """Record a PACK-09 destruction authorization against this document.

    Refuses under an active or indeterminate hold, refuses without a
    retention binding, and refuses a stale authorization. This service
    still destroys nothing: PACK-13 owns the data plane, and executing a
    disposal against an in-memory reference store would be a claim about
    durability this round has no basis for. The authorization is recorded
    and the document is closed, which is the governed half PACK-11 owns."""
    document = _load_document(stores, document_id, context.require_scope())
    guard = _guard(
        stores,
        command="authorize_disposition",
        action=DocumentAction.AUTHORIZE_DISPOSITION,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), authorization.authorization_reference),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        return DispositionResult(
            document=document,
            authorization=authorization,
            event=_rebuilt_registration_event(document, guard),
            audit_event=_replayed_audit(stores, guard),
        )
    assert_no_destruction_under_hold(document)
    assert_disposition_authorized(document, authorization)
    before = _state_hash(document.to_state_payload())
    if document.state is DocumentState.ACTIVE:
        document = document.with_state(
            DocumentState.CLOSED, at=guard.now, reason=reason, authority=guard.authority
        )
    stores.documents.save(document)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="governed_document.disposition_authorized",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=document.document_id,
        scope=guard.scope,
        payload=document_events.disposition_authorized_payload(document, authorization),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=document.document_id,
        target_type="GovernedDocument",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash(document.to_state_payload()),
        clock=clock,
    )
    return DispositionResult(
        document=document, authorization=authorization, event=event, audit_event=audit_event
    )


# ---------------------------------------------------------------------------
# Commands: determinations (ADR-053 requirements 2 and 3)
# ---------------------------------------------------------------------------


def determine_signature_status(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    determination_id: UUID,
    status: SignatureStatus,
    reason: ReasonCoded,
    form: object = None,
    verification_basis_reference: str | None = None,
    signatory_role_reference: str | None = None,
) -> SignatureDeterminationResult:
    """**ADR-053 interface requirement 2.**

    Record a governed signature determination. Nothing here inspects the
    content: the determination is the authority's, and this service stores
    it with the exact version hash it was made against."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="determine_signature_status",
        action=DocumentAction.DETERMINE_SIGNATURE_STATUS,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(determination_id)),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.signatures.latest_for_version(document_id, version_number)
        if stored is not None:
            return SignatureDeterminationResult(
                determination=stored,
                event=_rebuilt_signature_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )
    if form is not None and not isinstance(form, SignatureForm):
        raise DocumentDeterminationNotPermittedError(
            "signature form must be a governed SignatureForm value"
        )
    determination = SignatureDetermination(
        determination_id=determination_id,
        scope=document.scope,
        document_id=document_id,
        version_number=version_number,
        determined_version_hash=version.version_hash,
        status=status,
        determined_at=guard.now,
        determined_by=guard.authority,
        reason=reason,
        form=form,
        verification_basis_reference=verification_basis_reference,
        signatory_role_reference=signatory_role_reference,
    )
    stores.signatures.append(determination)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_determination.signature_recorded",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=determination.determination_id,
        scope=guard.scope,
        payload=document_events.signature_determination_payload(determination),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=determination.determination_id,
        target_type="DocumentDetermination",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(determination.to_payload()),
        clock=clock,
    )
    return SignatureDeterminationResult(
        determination=determination, event=event, audit_event=audit_event
    )


def _rebuilt_signature_event(
    determination: SignatureDetermination,
    guard: _CommandGuard,
    scope: OrganizationalScopeRef,
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_determination.signature_recorded",
        occurred_at=determination.determined_at,
        actor=guard.actor,
        aggregate_id=determination.determination_id,
        scope=scope,
        payload=document_events.signature_determination_payload(determination),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def determine_admissibility(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    determination_id: UUID,
    procedure_reference: str,
    status: AdmissibilityStatus,
    reason: ReasonCoded,
    limitation_reference: str | None = None,
    evidence_bundle_reference: str | None = None,
) -> AdmissibilityDeterminationResult:
    """**ADR-053 interface requirement 3.**

    Record a governed admissibility determination for one procedure. The
    action requires the `legal_reviewer` role, and this service makes no
    legal judgement of its own."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="determine_admissibility",
        action=DocumentAction.DETERMINE_ADMISSIBILITY,
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(document_id),
            str(version_number),
            str(determination_id),
            procedure_reference,
        ),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.admissibilities.latest_for_version(
            document_id, version_number, procedure_reference=procedure_reference
        )
        if stored is not None:
            return AdmissibilityDeterminationResult(
                determination=stored,
                event=_rebuilt_admissibility_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )
    determination = AdmissibilityDetermination(
        determination_id=determination_id,
        scope=document.scope,
        document_id=document_id,
        version_number=version_number,
        determined_version_hash=version.version_hash,
        procedure_reference=procedure_reference,
        status=status,
        determined_at=guard.now,
        determined_by=guard.authority,
        reason=reason,
        limitation_reference=limitation_reference,
        evidence_bundle_reference=evidence_bundle_reference,
    )
    stores.admissibilities.append(determination)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_determination.admissibility_recorded",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=determination.determination_id,
        scope=guard.scope,
        payload=document_events.admissibility_determination_payload(determination),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=determination.determination_id,
        target_type="DocumentDetermination",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(determination.to_payload()),
        clock=clock,
    )
    return AdmissibilityDeterminationResult(
        determination=determination, event=event, audit_event=audit_event
    )


def _rebuilt_admissibility_event(
    determination: AdmissibilityDetermination,
    guard: _CommandGuard,
    scope: OrganizationalScopeRef,
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_determination.admissibility_recorded",
        occurred_at=determination.determined_at,
        actor=guard.actor,
        aggregate_id=determination.determination_id,
        scope=scope,
        payload=document_events.admissibility_determination_payload(determination),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


# ---------------------------------------------------------------------------
# Commands: evidence
# ---------------------------------------------------------------------------


def register_evidence(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
    evidence_id: UUID,
    matter_reference: str,
    provenance: Provenance,
    holder_reference: str,
    reason: ReasonCoded,
) -> EvidenceResult:
    """Register a document version as evidence, opening its custody chain.

    The version must be citable (approved, published or superseded). A
    draft cannot become evidence: nobody has yet taken responsibility for
    it, and evidence is precisely material somebody has."""
    document = _load_document(stores, document_id, context.require_scope())
    _load_chain(stores, document)
    version = _load_version(stores, document, version_number)
    guard = _guard(
        stores,
        command="register_evidence",
        action=DocumentAction.REGISTER_EVIDENCE,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(document_id), str(version_number), str(evidence_id)),
        target_scope=document.scope,
    )
    if guard.replay is not None:
        stored = stores.evidence.get(evidence_id)
        if stored is not None:
            return EvidenceResult(
                evidence=stored,
                event=_rebuilt_evidence_event(stored, guard, document.scope),
                audit_event=_replayed_audit(stores, guard),
            )
    if not version.is_citable:
        raise DocumentTransitionInvalidError(
            f"a version in state {version.state.value!r} may not be registered as evidence"
        )
    record = EvidenceRecord(
        evidence_id=evidence_id,
        scope=document.scope,
        document_id=document_id,
        version_number=version_number,
        version_hash=version.version_hash,
        matter_reference=matter_reference,
        provenance=provenance,
        registered_at=guard.now,
        registered_by=guard.authority,
    ).with_custody_event(
        CustodyEvent(
            sequence=1,
            occurred_at=guard.now,
            action=CustodyAction.ACQUIRED,
            holder_reference=holder_reference,
            recorded_by=guard.authority,
            reason=reason,
        )
    )
    assert_evidence_admissible_shape(record, version)
    stores.evidence.save(record)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_evidence.registered",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=record.evidence_id,
        scope=guard.scope,
        payload=document_events.evidence_registered_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=record.evidence_id,
        target_type="EvidenceRecord",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(record.to_state_payload()),
        clock=clock,
    )
    return EvidenceResult(evidence=record, event=event, audit_event=audit_event)


def _rebuilt_evidence_event(
    record: EvidenceRecord, guard: _CommandGuard, scope: OrganizationalScopeRef
) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_evidence.registered",
        occurred_at=record.registered_at,
        actor=guard.actor,
        aggregate_id=record.evidence_id,
        scope=scope,
        payload=document_events.evidence_registered_payload(record),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


def transfer_custody(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    evidence_id: UUID,
    action: CustodyAction,
    holder_reference: str,
    reason: ReasonCoded,
    location_reference: str | None = None,
    expected_record_version: int | None = None,
) -> EvidenceResult:
    """Append a custody event, re-verifying the whole chain."""
    scope = context.require_scope()
    record = stores.evidence.get(evidence_id)
    if record is None or record.scope.organization_id != scope.organization_id:
        _raise_not_found("evidence record", evidence_id)
        raise AssertionError  # pragma: no cover
    guard = _guard(
        stores,
        command="transfer_custody",
        action=DocumentAction.TRANSFER_CUSTODY,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(evidence_id), str(action), holder_reference),
        target_scope=record.scope,
        current_version=record.record_version,
        expected_version=expected_record_version,
        version_label="evidence record",
    )
    if guard.replay is not None:
        return EvidenceResult(
            evidence=record,
            event=_rebuilt_evidence_event(record, guard, record.scope),
            audit_event=_replayed_audit(stores, guard),
        )
    before = _state_hash(record.to_state_payload())
    event_entry = CustodyEvent(
        sequence=len(record.custody) + 1,
        occurred_at=guard.now,
        action=action,
        holder_reference=holder_reference,
        recorded_by=guard.authority,
        reason=reason,
        received_from_reference=record.current_holder_reference,
        location_reference=location_reference,
    )
    updated = record.with_custody_event(event_entry)
    stores.evidence.save(updated)
    envelope = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_evidence.custody_transferred",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=updated.evidence_id,
        scope=guard.scope,
        payload=document_events.custody_transferred_payload(updated, event_entry),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=envelope,
        aggregate_id=updated.evidence_id,
        target_type="EvidenceRecord",
        reason_code=reason.reason_code,
        before_hash=before,
        after_hash=_state_hash(updated.to_state_payload()),
        clock=clock,
    )
    return EvidenceResult(evidence=updated, event=envelope, audit_event=audit_event)


def seal_evidence_bundle(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    bundle_id: UUID,
    matter_reference: str,
    purpose_reference: str,
    evidence_ids: Sequence[UUID],
    reason: ReasonCoded,
) -> BundleResult:
    """Assemble and seal an evidence bundle in one governed act.

    Assembly and sealing are one command rather than two, which is the
    opposite of the approval/publication split - and for the opposite
    reason. There, two acts by two roles is the control. Here, an
    *unsealed* bundle is not a governed object at all: it is a working
    set, and letting one exist between two commands would create a window
    in which a bundle is citable but still mutable."""
    scope = context.require_scope()
    guard = _guard(
        stores,
        command="seal_evidence_bundle",
        action=DocumentAction.SEAL_EVIDENCE_BUNDLE,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(bundle_id), matter_reference, *(str(e) for e in evidence_ids)),
    )
    if guard.replay is not None:
        stored = stores.bundles.get(bundle_id)
        if stored is not None:
            return BundleResult(
                bundle=stored,
                event=_rebuilt_bundle_event(stored, guard),
                audit_event=_replayed_audit(stores, guard),
            )
    bundle = EvidenceBundle(
        bundle_id=bundle_id,
        scope=scope,
        matter_reference=matter_reference,
        purpose_reference=purpose_reference,
        created_at=guard.now,
        created_by=guard.authority,
    )
    for evidence_id in evidence_ids:
        record = stores.evidence.get(evidence_id)
        if record is None or record.scope.organization_id != scope.organization_id:
            _raise_not_found("evidence record", evidence_id)
            raise AssertionError  # pragma: no cover
        document = _load_document(stores, record.document_id, scope)
        version = _load_version(stores, document, record.version_number)
        assert_evidence_admissible_shape(record, version)
        bundle = bundle.with_item(record)
    bundle = bundle.seal(at=guard.now, sealed_by=guard.authority)
    stores.bundles.save(bundle)
    event = document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_evidence.bundle_sealed",
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=bundle.bundle_id,
        scope=scope,
        payload=document_events.bundle_sealed_payload(bundle),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )
    audit_event = _finish(
        stores,
        guard,
        event=event,
        aggregate_id=bundle.bundle_id,
        target_type="EvidenceRecord",
        reason_code=reason.reason_code,
        before_hash="",
        after_hash=_state_hash(bundle.to_state_payload()),
        clock=clock,
    )
    return BundleResult(bundle=bundle, event=event, audit_event=audit_event)


def _rebuilt_bundle_event(bundle: EvidenceBundle, guard: _CommandGuard) -> EventEnvelope:
    return document_events.build_document_event(
        event_id=guard.event_id,
        event_type="document_evidence.bundle_sealed",
        occurred_at=bundle.created_at,
        actor=guard.actor,
        aggregate_id=bundle.bundle_id,
        scope=bundle.scope,
        payload=document_events.bundle_sealed_payload(bundle),
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def resolve_document_reference(
    stores: DocumentStores,
    *,
    reference_document_id: UUID,
    scope: OrganizationalScopeRef,
) -> DocumentResolution:
    """**ADR-053 interface requirement 1.**

    Resolve a reference to existence and kind within an organizational
    scope. Returns `exists=False` for a document in another scope, exactly
    as for one that does not exist: a resolution that distinguished them
    would be a cross-organization existence oracle."""
    document = stores.documents.get(reference_document_id)
    if document is None or document.scope.organization_id != scope.organization_id:
        return DocumentResolution(reference=str(reference_document_id), scope=scope, exists=False)
    current = document.current_version_number
    revoked = False
    if current is not None:
        revocation = stores.revocations.get_for_version(document.document_id, current)
        revoked = revocation is not None
    reference = (
        str(reference_document_id)
        if current is None
        else document_citation(document.document_id, current)
    )
    return DocumentResolution(
        reference=reference,
        scope=scope,
        exists=True,
        kind=document.kind,
        current_version_number=current,
        is_revoked=revoked,
    )


def get_signature_status(
    stores: DocumentStores, *, document_id: UUID, version_number: int, scope: OrganizationalScopeRef
) -> SignatureStatus:
    """The consumer-facing signature answer, defaulting to
    `not_determined`. Never inferred."""
    document = stores.documents.get(document_id)
    if document is None or document.scope.organization_id != scope.organization_id:
        return absent_signature_status()
    determination = stores.signatures.latest_for_version(document_id, version_number)
    version = stores.versions.get_by_number(document_id, version_number)
    if determination is None or version is None:
        return absent_signature_status()
    try:
        require_signature_determination(determination, version)
    except Exception:  # noqa: BLE001 - a stale determination is reported as absent
        # A determination made against a different state of this version is
        # not "no" and not "yes": it does not apply. Reporting it as absent
        # is the honest answer and makes the consumer fail closed.
        return absent_signature_status()
    return determination.status


def get_admissibility_status(
    stores: DocumentStores,
    *,
    document_id: UUID,
    version_number: int,
    procedure_reference: str,
    scope: OrganizationalScopeRef,
) -> AdmissibilityStatus:
    """The consumer-facing admissibility answer for one procedure,
    defaulting to `not_determined`."""
    document = stores.documents.get(document_id)
    if document is None or document.scope.organization_id != scope.organization_id:
        return absent_admissibility_status()
    determination = stores.admissibilities.latest_for_version(
        document_id, version_number, procedure_reference=procedure_reference
    )
    version = stores.versions.get_by_number(document_id, version_number)
    if determination is None or version is None:
        return absent_admissibility_status()
    try:
        require_admissibility_determination(
            determination, version, procedure_reference=procedure_reference
        )
    except Exception:  # noqa: BLE001 - a stale determination is reported as absent
        return absent_admissibility_status()
    return determination.status


def read_document_content(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    document_id: UUID,
    version_number: int,
) -> bytes:
    """Read a version's content, authority-checked and integrity-checked.

    The one path by which content leaves this service, and the reason
    every projection can be content-free. Four checks, in order: scope,
    authority for a restricted read, the access profile against the
    version's classification, and independence where the reader claims it.
    Then the bytes are re-verified against the recorded digest before they
    are returned, so a caller never receives content this service cannot
    show is the content that was recorded."""
    scope = context.require_scope()
    document = _load_document(stores, document_id, scope)
    authority = assert_authorized(
        DocumentAction.READ_RESTRICTED_DOCUMENT, context.authorities, scope, port=port
    )
    assert_reader_independent(authority, scope, port=port)
    version = _load_version(stores, document, version_number)
    assert_access_permitted(context.access_profile, version.sensitivity, scope)
    payload = stores.content.get(version.content.digest)
    verify_version_content(version, payload)
    return payload


def verify_document_integrity(
    stores: DocumentStores, *, document_id: UUID, scope: OrganizationalScopeRef
) -> ChainVerificationResult:
    """Verify a document's chain **and** every version's content digest.

    The two checks together. The chain alone would miss content swapped
    behind an untouched record; the content check alone would miss a
    record rewritten together with its digest. Returns a result rather
    than raising, so an operator sweeping a whole store gets every finding
    rather than stopping at the first."""
    document = stores.documents.get(document_id)
    if document is None or document.scope.organization_id != scope.organization_id:
        raise DocumentRecordNotFoundError(f"no governed document with id {document_id}")
    versions = stores.versions.list_for_document(document_id)
    result = verify_version_chain(document_id, versions)
    if not result.valid:
        return result
    for version in versions:
        if not stores.content.has(version.content.digest):
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(versions),
                head_hash=result.head_hash,
                broken_at_version=version.version_number,
                detail="the content store does not hold this version's recorded content",
            )
        try:
            verify_version_content(version, stores.content.get(version.content.digest))
        except Exception as exc:  # noqa: BLE001 - reported, not raised, for sweep runs
            return ChainVerificationResult(
                document_id=document_id,
                valid=False,
                version_count=len(versions),
                head_hash=result.head_hash,
                broken_at_version=version.version_number,
                detail=str(exc),
            )
    return result


def restricted_projection(
    stores: DocumentStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    document_id: UUID,
    version_number: int,
) -> RestrictedDocumentProjection:
    """Build a restricted projection for an authorized reader."""
    scope = context.require_scope()
    document = _load_document(stores, document_id, scope)
    authority = assert_authorized(
        DocumentAction.READ_RESTRICTED_DOCUMENT, context.authorities, scope, port=port
    )
    assert_reader_independent(authority, scope, port=port)
    version = _load_version(stores, document, version_number)
    assert_access_permitted(context.access_profile, version.sensitivity, scope)
    return build_restricted_projection(
        document,
        version,
        generated_at=clock.now(),
        reviews=stores.reviews.list_for_version(document_id, version_number),
        signature=stores.signatures.latest_for_version(document_id, version_number),
        supersession=stores.supersessions.get_for_version(document_id, version_number),
        revocation=stores.revocations.get_for_version(document_id, version_number),
        rendition_count=len(stores.renditions.list_for_version(document_id, version_number)),
    )


__all__ = [
    "AUDIT_POLICY_VERSION",
    "AccessProfile",
    "AdmissibilityDeterminationResult",
    "ApprovalResult",
    "BundleResult",
    "DispositionResult",
    "DocumentResult",
    "DocumentStores",
    "EvidenceResult",
    "PublicationAuthorizationResult",
    "PublicationResult",
    "RenditionResult",
    "ReviewResult",
    "RevocationResult",
    "SignatureDeterminationResult",
    "SupersessionResult",
    "VersionResult",
    "approve_version",
    "authorize_disposition",
    "authorize_publication",
    "bind_retention",
    "determine_admissibility",
    "determine_signature_status",
    "get_admissibility_status",
    "get_signature_status",
    "issue_publication_rendition",
    "publish_version",
    "read_document_content",
    "record_legal_hold",
    "record_review",
    "record_version",
    "register_document",
    "register_evidence",
    "resolve_document_reference",
    "restricted_projection",
    "return_for_revision",
    "revoke_version",
    "seal_evidence_bundle",
    "submit_for_review",
    "supersede_version",
    "transfer_custody",
    "verify_document_integrity",
]
