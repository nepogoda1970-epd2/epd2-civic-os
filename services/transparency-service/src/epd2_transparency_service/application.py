"""Transparency Service application layer: `publish_ledger_entry`,
`correct_ledger_entry`, `generate_audit_export_package`,
`publish_audit_export_package`, `verify_audit_export_package`,
`define_disclosure_policy`, `activate_disclosure_policy`,
`submit_lobby_log_entry`, `publish_lobby_log_entry`,
`correct_lobby_log_entry` — canon section 19a, canon section 20.14's
ten-event catalog, ADR-011/012/013/014/015.

Every command below accepts an optional caller-supplied `event_id`
(CT-00-04), exactly the same idempotency pattern every PACK-02/03 service
already established: a retried call with the same `event_id` returns the
already-recorded result instead of re-attempting a transition that would
otherwise fail once the entity has moved past its starting state.

Read-only cross-pack dependency (ADR-012, the first time this project
reads from another same-generation pack rather than an older one): this
module calls `epd2_audit_core.application.list_by_target_types` (a new,
additive, read-only Audit Core function) directly, from
`generate_audit_export_package` below.

ADR-012 additionally sanctions four upstream `.application`-layer read
functions as an allowed (not mandatory) boundary for a future
strict-verification mode: `epd2_initiative_service.application.
get_published_initiative`/`get_initiative_version`,
`epd2_moderation_service.application.get_moderation_decision`,
`epd2_voting_service.application.get_ballot`,
`epd2_tally_service.application.get_result_publication`. Those four are
implemented and unit-tested at their own service boundary and enforced
in `tests/repository/test_service_boundaries.py` as PACK-04's only
permitted upstream `.application`-module imports — but no command body
in *this* module currently calls them: `publish_ledger_entry`,
`correct_ledger_entry`, and `submit_lobby_log_entry` all take
caller-supplied content (`raw_content`) instead of fetching it
internally, since sourcing the correct upstream snapshot is the
caller's responsibility and this service's own job is disclosure
filtering plus immutable publication. They remain available,
import-legal, and boundary-tested for a later verify-before-publish
enhancement. No PACK-02 identity/credential service, no
`deliberation-service`, and no `delegation-service` is ever imported
here (ADR-012 Decision, explicit exclusions) — see
`tests/repository/test_service_boundaries.py`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import (
    AppendAuditEventRequest,
    append_audit_event,
    list_by_target_types,
)
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_transparency_service.domain import (
    DEFAULT_SMALL_CELL_THRESHOLD,
    AuditExportPackage,
    AuditExportPackageStatus,
    ChainProofItem,
    DisclosurePolicy,
    DisclosurePolicyStatus,
    FieldRule,
    IncludedTargetType,
    LedgerSubjectType,
    LobbyLogContactMethod,
    LobbyLogEntry,
    LobbyLogEntryStatus,
    LobbyLogRelatedSubjectType,
    PublicLedgerEntry,
    PublicLedgerEntryStatus,
    apply_disclosure_policy,
    assert_no_forbidden_fields,
)
from epd2_transparency_service.events import (
    audit_export_package_full_state_payload,
    build_audit_export_generated_event,
    build_audit_export_published_event,
    build_disclosure_policy_activated_event,
    build_disclosure_policy_defined_event,
    build_disclosure_policy_superseded_event,
    build_ledger_entry_corrected_event,
    build_ledger_entry_published_event,
    build_lobby_log_entry_corrected_event,
    build_lobby_log_entry_published_event,
    build_lobby_log_entry_submitted_event,
    disclosure_policy_full_state_payload,
    ledger_entry_full_state_payload,
    lobby_log_entry_full_state_payload,
    lobby_log_entry_public_payload,
)
from epd2_transparency_service.exceptions import (
    LedgerEntryAlreadyPublishedError,
    LobbyLogEntryIncompleteError,
    PublicationNotAllowedError,
    UnknownAuditExportPackageError,
    UnknownDisclosurePolicyError,
    UnknownLobbyLogEntryError,
    UnknownPublicLedgerEntryError,
)
from epd2_transparency_service.storage import (
    AuditExportPackageStore,
    DisclosurePolicyStore,
    LobbyLogEntryStore,
    PublicLedgerEntryStore,
)

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "transparency-service"

#: Audit `reason_code` classifications (ADR-006/ADR-014 pattern: one
#: generic classification per logical action-type).
_LEDGER_ENTRY_PUBLISHED = "TRANSPARENCY_LEDGER_ENTRY_PUBLISHED"
_AUDIT_EXPORT_STATUS_CHANGED = "TRANSPARENCY_AUDIT_EXPORT_STATUS_CHANGED"
_DISCLOSURE_POLICY_STATUS_CHANGED = "TRANSPARENCY_DISCLOSURE_POLICY_STATUS_CHANGED"
_LOBBY_LOG_ENTRY_STATUS_CHANGED = "TRANSPARENCY_LOBBY_LOG_ENTRY_STATUS_CHANGED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class LedgerEntryResult:
    entry: PublicLedgerEntry
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class GenerateAuditExportPackageResult:
    package: AuditExportPackage
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PublishAuditExportPackageResult:
    package: AuditExportPackage
    superseded_package: AuditExportPackage | None
    event: EventEnvelope
    superseded_event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class VerifyAuditExportPackageResult:
    """Result of `verify_audit_export_package` — the public,
    chain-continuity/ordering/non-modification check canon section
    19a.2's "Семантика проверки" describes. `is_intact=False` means the
    recomputed digest over the package's own `chain_proof` does not match
    its stored `package_digest`; it never means anything about the
    original private `AuditEvent.event_hash` values (this package does
    not, and cannot, recompute those)."""

    is_intact: bool
    recomputed_digest: str


@dataclass(frozen=True, slots=True)
class DisclosurePolicyResult:
    policy: DisclosurePolicy
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ActivateDisclosurePolicyResult:
    policy: DisclosurePolicy
    superseded_policy: DisclosurePolicy | None
    event: EventEnvelope
    superseded_event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class LobbyLogEntryResult:
    entry: LobbyLogEntry
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# PublicLedgerEntry commands
# ---------------------------------------------------------------------------


def publish_ledger_entry(
    ledger_store: PublicLedgerEntryStore,
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    public_ledger_entry_id: UUID,
    subject_type: LedgerSubjectType,
    subject_id: UUID,
    subject_event_id: UUID,
    raw_content: Mapping[str, object],
    published_by_role_id: UUID,
    redaction_notice: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LedgerEntryResult:
    """Create a new `PublicLedgerEntry` in `published` status for
    `subject_type`/`subject_id` (canon section 19a.1/19a.5).

    Requires an `active` `DisclosurePolicy` for `subject_type.value`
    (`PublicationNotAllowedError` otherwise, fail-closed) and rejects a
    second, unrelated publication for the same `subject_event_id`
    (`LedgerEntryAlreadyPublishedError` — use `correct_ledger_entry`
    instead). `raw_content` is filtered through
    `domain.apply_disclosure_policy` before being stored as
    `content_snapshot` — the caller-supplied `raw_content` itself is never
    persisted or published verbatim.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to publish a ledger entry")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        entry = ledger_store.get(public_ledger_entry_id)
        if entry is None:
            raise UnknownPublicLedgerEntryError(
                f"idempotent replay for event_id {resolved_event_id} found no ledger entry "
                f"{public_ledger_entry_id}"
            )
        event = build_ledger_entry_published_event(
            event_id=resolved_event_id,
            entry=entry,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LedgerEntryResult(entry=entry, event=event, audit_event=existing_audit)

    policy = policy_store.get_active_for_subject_type(subject_type.value)
    if policy is None:
        raise PublicationNotAllowedError(
            f"no active DisclosurePolicy for subject_type {subject_type.value!r}"
        )
    already = ledger_store.get_by_subject_event_id(subject_event_id)
    if already is not None:
        raise LedgerEntryAlreadyPublishedError(
            f"subject_event_id {subject_event_id} already has a published ledger entry "
            f"({already.public_ledger_entry_id}); use correct_ledger_entry for a correction"
        )

    content_snapshot = apply_disclosure_policy(policy, raw_content)
    assert_no_forbidden_fields(content_snapshot)
    content_hash = compute_payload_hash(content_snapshot)
    now = clock.now()
    entry = PublicLedgerEntry(
        public_ledger_entry_id=public_ledger_entry_id,
        subject_type=subject_type,
        subject_id=subject_id,
        subject_event_id=subject_event_id,
        published_at=now,
        published_by_role_id=published_by_role_id,
        content_snapshot=content_snapshot,
        content_hash=content_hash,
        previous_entry_hash=ledger_store.head_hash(),
        disclosure_policy_id=policy.disclosure_policy_id,
        redaction_notice=redaction_notice,
        supersedes_entry_id=None,
        status=PublicLedgerEntryStatus.PUBLISHED,
    )
    stored = ledger_store.create(entry)
    event = build_ledger_entry_published_event(
        event_id=resolved_event_id,
        entry=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="public_ledger_entry",
            target_id=stored.public_ledger_entry_id,
            action="publish_ledger_entry",
            reason_code=_LEDGER_ENTRY_PUBLISHED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(ledger_entry_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return LedgerEntryResult(entry=stored, event=event, audit_event=audit_event)


def correct_ledger_entry(
    ledger_store: PublicLedgerEntryStore,
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    new_public_ledger_entry_id: UUID,
    supersedes_entry_id: UUID,
    raw_content: Mapping[str, object],
    published_by_role_id: UUID,
    redaction_notice: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LedgerEntryResult:
    """Create a new `PublicLedgerEntry` with `supersedes_entry_id` set,
    correcting `supersedes_entry_id`'s content (canon section 19a.1's
    "Неизменяемость и исправления" — the original row is never rewritten).
    Emits `transparency.ledger_entry_corrected`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to correct a ledger entry")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        entry = ledger_store.get(new_public_ledger_entry_id)
        if entry is None:
            raise UnknownPublicLedgerEntryError(
                f"idempotent replay for event_id {resolved_event_id} found no ledger entry "
                f"{new_public_ledger_entry_id}"
            )
        event = build_ledger_entry_corrected_event(
            event_id=resolved_event_id,
            entry=entry,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LedgerEntryResult(entry=entry, event=event, audit_event=existing_audit)

    original = ledger_store.get(supersedes_entry_id)
    if original is None:
        raise UnknownPublicLedgerEntryError(
            f"unknown public_ledger_entry_id: {supersedes_entry_id}"
        )

    policy = policy_store.get_active_for_subject_type(original.subject_type.value)
    if policy is None:
        raise PublicationNotAllowedError(
            f"no active DisclosurePolicy for subject_type {original.subject_type.value!r}"
        )

    content_snapshot = apply_disclosure_policy(policy, raw_content)
    assert_no_forbidden_fields(content_snapshot)
    content_hash = compute_payload_hash(content_snapshot)
    now = clock.now()
    entry = PublicLedgerEntry(
        public_ledger_entry_id=new_public_ledger_entry_id,
        subject_type=original.subject_type,
        subject_id=original.subject_id,
        subject_event_id=original.subject_event_id,
        published_at=now,
        published_by_role_id=published_by_role_id,
        content_snapshot=content_snapshot,
        content_hash=content_hash,
        previous_entry_hash=ledger_store.head_hash(),
        disclosure_policy_id=policy.disclosure_policy_id,
        redaction_notice=redaction_notice,
        supersedes_entry_id=supersedes_entry_id,
        status=PublicLedgerEntryStatus.PUBLISHED,
    )
    stored = ledger_store.create(entry)
    event = build_ledger_entry_corrected_event(
        event_id=resolved_event_id,
        entry=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="public_ledger_entry",
            target_id=stored.public_ledger_entry_id,
            action="correct_ledger_entry",
            reason_code=_LEDGER_ENTRY_PUBLISHED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(ledger_entry_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return LedgerEntryResult(entry=stored, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# AuditExportPackage commands
# ---------------------------------------------------------------------------


def _build_chain_proof(events: Sequence[AuditEvent]) -> tuple[ChainProofItem, ...]:
    items: list[ChainProofItem] = []
    previous_hash = "0" * 64
    for position, event in enumerate(events, start=1):
        items.append(
            ChainProofItem(
                event_hash=event.event_hash,
                previous_event_hash=previous_hash,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                target_type=event.target_type,
                target_id=event.target_id,
                action=event.action,
                reason_code=event.reason_code,
                correlation_id=event.correlation_id,
                source_service=event.source_service,
                sequence_position=position,
            )
        )
        previous_hash = event.event_hash
    return tuple(items)


def _compute_package_digest(chain_proof: tuple[ChainProofItem, ...]) -> str:
    from epd2_transparency_service.events import audit_export_package_public_payload

    # A minimal stand-in package used only to get a canonical, deterministic
    # serialization of chain_proof for hashing - package_digest must be
    # computable from chain_proof alone, before package_digest itself exists.
    serialized = [
        {
            "event_hash": item.event_hash,
            "previous_event_hash": item.previous_event_hash,
            "event_type": item.event_type,
            "occurred_at": item.occurred_at.isoformat(),
            "target_type": item.target_type,
            "target_id": str(item.target_id),
            "action": item.action,
            "reason_code": item.reason_code,
            "correlation_id": str(item.correlation_id),
            "source_service": item.source_service,
            "sequence_position": item.sequence_position,
        }
        for item in chain_proof
    ]
    del audit_export_package_public_payload  # imported for symmetry/documentation only
    return compute_payload_hash({"chain_proof": serialized})


def _compute_integrity_proof(package_digest: str, event_count: int, generated_at: datetime) -> str:
    """A deterministic, publicly-recomputable value derived from
    `package_digest`/`event_count`/`generated_at` — NOT a cryptographic
    signature (no signing key is implemented in this pack; see canon
    section 19a.2's own "Семантика проверки", which never claims signature
    verification, only chain-continuity/ordering/non-modification).
    A future pack that adds real signing would replace this function's
    body without changing `AuditExportPackage.integrity_proof`'s shape
    (a plain string)."""
    material = f"{package_digest}:{event_count}:{generated_at.isoformat()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def generate_audit_export_package(
    package_store: AuditExportPackageStore,
    audit_store: AuditEventStore,
    *,
    audit_export_package_id: UUID,
    scope_description: str,
    requested_by_role_id: UUID,
    included_target_types: tuple[IncludedTargetType, ...],
    redaction_notice: str | None,
    supersedes_package_id: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> GenerateAuditExportPackageResult:
    """Generate a new `AuditExportPackage` in `generated` status (canon
    section 19a.2), reading the matching `AuditEvent` records from Audit
    Core via the new, additive, read-only
    `epd2_audit_core.application.list_by_target_types` function.
    `vote_envelope`/`delegation` can never appear in
    `included_target_types` (`domain.IncludedTargetType` has no such
    members, so this is enforced by the type itself)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to generate an audit export package")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        package = package_store.get(audit_export_package_id)
        if package is None:
            raise UnknownAuditExportPackageError(
                f"idempotent replay for event_id {resolved_event_id} found no package "
                f"{audit_export_package_id}"
            )
        event = build_audit_export_generated_event(
            event_id=resolved_event_id,
            package=package,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return GenerateAuditExportPackageResult(
            package=package, event=event, audit_event=existing_audit
        )

    target_type_values = frozenset(t.value for t in included_target_types)
    source_events = list_by_target_types(audit_store, target_type_values)
    chain_proof = _build_chain_proof(source_events)
    package_digest = _compute_package_digest(chain_proof)
    now = clock.now()
    integrity_proof = _compute_integrity_proof(package_digest, len(chain_proof), now)
    package = AuditExportPackage(
        audit_export_package_id=audit_export_package_id,
        scope_description=scope_description,
        requested_by_role_id=requested_by_role_id,
        included_target_types=included_target_types,
        event_count=len(chain_proof),
        chain_proof=chain_proof,
        package_digest=package_digest,
        integrity_proof=integrity_proof,
        generated_at=now,
        redaction_notice=redaction_notice,
        supersedes_package_id=supersedes_package_id,
        status=AuditExportPackageStatus.GENERATED,
    )
    stored = package_store.create(package)
    event = build_audit_export_generated_event(
        event_id=resolved_event_id,
        package=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="audit_export_package",
            target_id=stored.audit_export_package_id,
            action="generate_audit_export_package",
            reason_code=_AUDIT_EXPORT_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(audit_export_package_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return GenerateAuditExportPackageResult(package=stored, event=event, audit_event=audit_event)


def publish_audit_export_package(
    package_store: AuditExportPackageStore,
    audit_store: AuditEventStore,
    *,
    audit_export_package_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> PublishAuditExportPackageResult:
    """`generated -> published`. If the package's own `supersedes_package_id`
    is set, this call also transitions the referenced OLD package
    `published -> superseded` (canon section 19a.2: superseding only ever
    happens this way, driven by the new package, never a standalone
    command) — that old package's own content is never touched, only its
    `status`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to publish an audit export package")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        package = package_store.get(audit_export_package_id)
        if package is None:
            raise UnknownAuditExportPackageError(
                f"unknown audit_export_package_id: {audit_export_package_id}"
            )
        superseded = (
            package_store.get(package.supersedes_package_id)
            if package.supersedes_package_id is not None
            else None
        )
        event = build_audit_export_published_event(
            event_id=resolved_event_id,
            package=package,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return PublishAuditExportPackageResult(
            package=package,
            superseded_package=superseded,
            event=event,
            superseded_event=None,
            audit_event=existing_audit,
        )

    package = package_store.get(audit_export_package_id)
    if package is None:
        raise UnknownAuditExportPackageError(
            f"unknown audit_export_package_id: {audit_export_package_id}"
        )

    superseded_package: AuditExportPackage | None = None
    superseded_event: EventEnvelope | None = None
    if package.supersedes_package_id is not None:
        old_package = package_store.get(package.supersedes_package_id)
        if old_package is None:
            raise UnknownAuditExportPackageError(
                f"unknown supersedes_package_id: {package.supersedes_package_id}"
            )
        old_updated = old_package.with_status(AuditExportPackageStatus.SUPERSEDED)
        package_store.save(old_updated)
        superseded_package = old_updated
        superseded_now = clock.now()
        superseded_event = build_audit_export_published_event(
            event_id=generate_uuid(),
            package=old_updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=superseded_now,
        )
        append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=generate_uuid(),
                event_type="transparency.audit_export_published",
                occurred_at=superseded_now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="audit_export_package",
                target_id=old_updated.audit_export_package_id,
                action="supersede_audit_export_package",
                reason_code=_AUDIT_EXPORT_STATUS_CHANGED,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=compute_payload_hash(
                    audit_export_package_full_state_payload(old_package)
                ),
                after_hash=compute_payload_hash(
                    audit_export_package_full_state_payload(old_updated)
                ),
            ),
            clock=clock,
        )

    before_hash = compute_payload_hash(audit_export_package_full_state_payload(package))
    updated = package.with_status(AuditExportPackageStatus.PUBLISHED)
    package_store.save(updated)
    now = clock.now()
    event = build_audit_export_published_event(
        event_id=resolved_event_id,
        package=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="audit_export_package",
            target_id=updated.audit_export_package_id,
            action="publish_audit_export_package",
            reason_code=_AUDIT_EXPORT_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(audit_export_package_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return PublishAuditExportPackageResult(
        package=updated,
        superseded_package=superseded_package,
        event=event,
        superseded_event=superseded_event,
        audit_event=audit_event,
    )


def verify_audit_export_package(package: AuditExportPackage) -> VerifyAuditExportPackageResult:
    """Recompute the digest over `package.chain_proof` and compare it to
    the stored `package_digest` — exactly the public verification canon
    section 19a.2 describes (continuity/ordering/non-modification of the
    exported segment). Never recomputes or checks any original private
    `AuditEvent.event_hash`."""
    recomputed = _compute_package_digest(package.chain_proof)
    return VerifyAuditExportPackageResult(
        is_intact=(recomputed == package.package_digest), recomputed_digest=recomputed
    )


# ---------------------------------------------------------------------------
# DisclosurePolicy commands
# ---------------------------------------------------------------------------


def define_disclosure_policy(
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    disclosure_policy_id: UUID,
    applies_to_subject_type: str,
    field_rules: tuple[FieldRule, ...],
    effective_from: datetime,
    version: int,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    small_cell_threshold: int = DEFAULT_SMALL_CELL_THRESHOLD,
    event_id: UUID | None = None,
) -> DisclosurePolicyResult:
    """Create a new `DisclosurePolicy` in `draft` status (canon section
    19a.3). Emits `transparency.disclosure_policy_defined`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to define a disclosure policy")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        policy = policy_store.get(disclosure_policy_id)
        if policy is None:
            raise UnknownDisclosurePolicyError(
                f"idempotent replay for event_id {resolved_event_id} found no policy "
                f"{disclosure_policy_id}"
            )
        event = build_disclosure_policy_defined_event(
            event_id=resolved_event_id,
            policy=policy,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DisclosurePolicyResult(policy=policy, event=event, audit_event=existing_audit)

    policy = DisclosurePolicy(
        disclosure_policy_id=disclosure_policy_id,
        applies_to_subject_type=applies_to_subject_type,
        field_rules=field_rules,
        small_cell_threshold=small_cell_threshold,
        effective_from=effective_from,
        approved_by_role_id=None,
        version=version,
        status=DisclosurePolicyStatus.DRAFT,
    )
    stored = policy_store.create(policy)
    now = clock.now()
    event = build_disclosure_policy_defined_event(
        event_id=resolved_event_id,
        policy=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="disclosure_policy",
            target_id=stored.disclosure_policy_id,
            action="define_disclosure_policy",
            reason_code=_DISCLOSURE_POLICY_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(disclosure_policy_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return DisclosurePolicyResult(policy=stored, event=event, audit_event=audit_event)


def activate_disclosure_policy(
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    disclosure_policy_id: UUID,
    approved_by_role_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ActivateDisclosurePolicyResult:
    """`draft -> active` (requires `approved_by_role_id`, INV-08
    separation of authority). If another policy is already `active` for
    the same `applies_to_subject_type`, this call also transitions it
    `active -> superseded` (canon section 19a.3: "не более одной активной
    версии одновременно" — only ever enforced this way, never a
    standalone command)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate a disclosure policy")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        policy = policy_store.get(disclosure_policy_id)
        if policy is None:
            raise UnknownDisclosurePolicyError(
                f"unknown disclosure_policy_id: {disclosure_policy_id}"
            )
        event = build_disclosure_policy_activated_event(
            event_id=resolved_event_id,
            policy=policy,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ActivateDisclosurePolicyResult(
            policy=policy,
            superseded_policy=None,
            event=event,
            superseded_event=None,
            audit_event=existing_audit,
        )

    policy = policy_store.get(disclosure_policy_id)
    if policy is None:
        raise UnknownDisclosurePolicyError(f"unknown disclosure_policy_id: {disclosure_policy_id}")

    superseded_policy: DisclosurePolicy | None = None
    superseded_event: EventEnvelope | None = None
    currently_active = policy_store.get_active_for_subject_type(policy.applies_to_subject_type)
    if (
        currently_active is not None
        and currently_active.disclosure_policy_id != disclosure_policy_id
    ):
        superseded_now = clock.now()
        superseded_updated = currently_active.with_status(DisclosurePolicyStatus.SUPERSEDED)
        policy_store.save(superseded_updated)
        superseded_policy = superseded_updated
        superseded_event = build_disclosure_policy_superseded_event(
            event_id=generate_uuid(),
            policy=superseded_updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=superseded_now,
        )
        append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=generate_uuid(),
                event_type="transparency.disclosure_policy_superseded",
                occurred_at=superseded_now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="disclosure_policy",
                target_id=superseded_updated.disclosure_policy_id,
                action="supersede_disclosure_policy",
                reason_code=_DISCLOSURE_POLICY_STATUS_CHANGED,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=compute_payload_hash(
                    disclosure_policy_full_state_payload(currently_active)
                ),
                after_hash=compute_payload_hash(
                    disclosure_policy_full_state_payload(superseded_updated)
                ),
            ),
            clock=clock,
        )

    before_hash = compute_payload_hash(disclosure_policy_full_state_payload(policy))
    updated = policy.with_status(
        DisclosurePolicyStatus.ACTIVE, approved_by_role_id=approved_by_role_id
    )
    policy_store.save(updated)
    now = clock.now()
    event = build_disclosure_policy_activated_event(
        event_id=resolved_event_id,
        policy=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="disclosure_policy",
            target_id=updated.disclosure_policy_id,
            action="activate_disclosure_policy",
            reason_code=_DISCLOSURE_POLICY_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(disclosure_policy_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return ActivateDisclosurePolicyResult(
        policy=updated,
        superseded_policy=superseded_policy,
        event=event,
        superseded_event=superseded_event,
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# LobbyLogEntry commands
# ---------------------------------------------------------------------------

_LOBBY_LOG_MANDATORY_STRING_FIELDS = ("organization_name", "topic_summary")


def submit_lobby_log_entry(
    store: LobbyLogEntryStore,
    audit_store: AuditEventStore,
    *,
    lobby_log_entry_id: UUID,
    submitted_by_role_id: UUID,
    organization_name: str,
    related_subject_type: LobbyLogRelatedSubjectType,
    related_subject_id: UUID,
    contact_date: datetime,
    contact_method: LobbyLogContactMethod,
    topic_summary: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LobbyLogEntryResult:
    """Submit a new `LobbyLogEntry` in `submitted` status (canon section
    19a.4). Rejects a submission missing any mandatory field
    (`LobbyLogEntryIncompleteError`) before ever constructing the domain
    object — canon: an entry "отсутствующим обязательным полем
    отклоняется при подаче" (rejected on submission if a mandatory field
    is missing)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit a lobby log entry")
    if not organization_name or not topic_summary:
        raise LobbyLogEntryIncompleteError(
            "organization_name and topic_summary are mandatory and must not be empty"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        entry = store.get(lobby_log_entry_id)
        if entry is None:
            raise UnknownLobbyLogEntryError(
                f"idempotent replay for event_id {resolved_event_id} found no lobby log entry "
                f"{lobby_log_entry_id}"
            )
        event = build_lobby_log_entry_submitted_event(
            event_id=resolved_event_id,
            entry=entry,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LobbyLogEntryResult(entry=entry, event=event, audit_event=existing_audit)

    now = clock.now()
    entry = LobbyLogEntry(
        lobby_log_entry_id=lobby_log_entry_id,
        submitted_by_role_id=submitted_by_role_id,
        organization_name=organization_name,
        related_subject_type=related_subject_type,
        related_subject_id=related_subject_id,
        contact_date=contact_date,
        contact_method=contact_method,
        topic_summary=topic_summary,
        submitted_at=now,
        published_at=None,
        supersedes_entry_id=None,
        status=LobbyLogEntryStatus.SUBMITTED,
    )
    stored = store.create(entry)
    event = build_lobby_log_entry_submitted_event(
        event_id=resolved_event_id,
        entry=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="lobby_log_entry",
            target_id=stored.lobby_log_entry_id,
            action="submit_lobby_log_entry",
            reason_code=_LOBBY_LOG_ENTRY_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(lobby_log_entry_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return LobbyLogEntryResult(entry=stored, event=event, audit_event=audit_event)


def publish_lobby_log_entry(
    store: LobbyLogEntryStore,
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    lobby_log_entry_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LobbyLogEntryResult:
    """`submitted -> published` (canon section 19a.4). Mandatory automated
    validation before publication: field completeness (re-checked here),
    absence of structurally forbidden fields (trivial for this entity's
    fixed shape, re-asserted for defense-in-depth), and an `active`
    `DisclosurePolicy` for `"lobby_log_entry"` (`PublicationNotAllowedError`
    otherwise). No mandatory human pre-publication review (ADR-015 item
    4, amended)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to publish a lobby log entry")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        entry = store.get(lobby_log_entry_id)
        if entry is None:
            raise UnknownLobbyLogEntryError(f"unknown lobby_log_entry_id: {lobby_log_entry_id}")
        event = build_lobby_log_entry_published_event(
            event_id=resolved_event_id,
            entry=entry,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LobbyLogEntryResult(entry=entry, event=event, audit_event=existing_audit)

    entry = store.get(lobby_log_entry_id)
    if entry is None:
        raise UnknownLobbyLogEntryError(f"unknown lobby_log_entry_id: {lobby_log_entry_id}")
    if not entry.organization_name or not entry.topic_summary:
        raise LobbyLogEntryIncompleteError(
            f"lobby_log_entry_id {lobby_log_entry_id} is missing a mandatory field"
        )
    assert_no_forbidden_fields(lobby_log_entry_public_payload(entry))
    policy = policy_store.get_active_for_subject_type("lobby_log_entry")
    if policy is None:
        raise PublicationNotAllowedError("no active DisclosurePolicy for 'lobby_log_entry'")

    before_hash = compute_payload_hash(lobby_log_entry_full_state_payload(entry))
    now = clock.now()
    updated = entry.with_published(now)
    store.save(updated)
    event = build_lobby_log_entry_published_event(
        event_id=resolved_event_id,
        entry=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="lobby_log_entry",
            target_id=updated.lobby_log_entry_id,
            action="publish_lobby_log_entry",
            reason_code=_LOBBY_LOG_ENTRY_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(lobby_log_entry_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return LobbyLogEntryResult(entry=updated, event=event, audit_event=audit_event)


def correct_lobby_log_entry(
    store: LobbyLogEntryStore,
    policy_store: DisclosurePolicyStore,
    audit_store: AuditEventStore,
    *,
    new_lobby_log_entry_id: UUID,
    supersedes_entry_id: UUID,
    submitted_by_role_id: UUID,
    organization_name: str,
    related_subject_type: LobbyLogRelatedSubjectType,
    related_subject_id: UUID,
    contact_date: datetime,
    contact_method: LobbyLogContactMethod,
    topic_summary: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> LobbyLogEntryResult:
    """Create a new, already-`published` `LobbyLogEntry` with
    `supersedes_entry_id` set, correcting a previously `published` entry
    (canon section 19a.4 — only a `published` entry can be corrected;
    the original row is never rewritten). Emits
    `transparency.lobby_log_entry_corrected`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to correct a lobby log entry")
    if not organization_name or not topic_summary:
        raise LobbyLogEntryIncompleteError(
            "organization_name and topic_summary are mandatory and must not be empty"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        entry = store.get(new_lobby_log_entry_id)
        if entry is None:
            raise UnknownLobbyLogEntryError(
                f"idempotent replay for event_id {resolved_event_id} found no lobby log entry "
                f"{new_lobby_log_entry_id}"
            )
        event = build_lobby_log_entry_corrected_event(
            event_id=resolved_event_id,
            entry=entry,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return LobbyLogEntryResult(entry=entry, event=event, audit_event=existing_audit)

    original = store.get(supersedes_entry_id)
    if original is None:
        raise UnknownLobbyLogEntryError(f"unknown lobby_log_entry_id: {supersedes_entry_id}")
    if original.status is not LobbyLogEntryStatus.PUBLISHED:
        raise UnknownLobbyLogEntryError(
            f"lobby_log_entry_id {supersedes_entry_id} is not yet published; only a "
            "published entry can be corrected"
        )
    policy = policy_store.get_active_for_subject_type("lobby_log_entry")
    if policy is None:
        raise PublicationNotAllowedError("no active DisclosurePolicy for 'lobby_log_entry'")

    now = clock.now()
    entry = LobbyLogEntry(
        lobby_log_entry_id=new_lobby_log_entry_id,
        submitted_by_role_id=submitted_by_role_id,
        organization_name=organization_name,
        related_subject_type=related_subject_type,
        related_subject_id=related_subject_id,
        contact_date=contact_date,
        contact_method=contact_method,
        topic_summary=topic_summary,
        submitted_at=now,
        published_at=now,
        supersedes_entry_id=supersedes_entry_id,
        status=LobbyLogEntryStatus.PUBLISHED,
    )
    stored = store.create(entry)
    event = build_lobby_log_entry_corrected_event(
        event_id=resolved_event_id,
        entry=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="lobby_log_entry",
            target_id=stored.lobby_log_entry_id,
            action="correct_lobby_log_entry",
            reason_code=_LOBBY_LOG_ENTRY_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(lobby_log_entry_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return LobbyLogEntryResult(entry=stored, event=event, audit_event=audit_event)
