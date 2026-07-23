"""Initiative Service application layer: the command set canon section
20.6-20.7 lists for this service, plus small unaudited-event (but always
audited) helper functions documented inline where a real transition
exists but canon names no domain event for it - mirroring
`epd2_voting_service.application`'s own precedent
(`submit_ballot_for_configuration_review`) for steps canon gives no event
name for.

PACK-02 boundary (ADR-008): this module calls exactly two PACK-02
`application`-layer functions -
`epd2_credential_service.application.validate_participation_credential`
(validate an `initiative_support` credential before accepting a
`SupportRecord`) and `epd2_eligibility_service.application.get_eligibility_decision`
(optionally confirm the `EligibilityDecision` backing a support action,
when a caller supplies one - see `add_support`'s docstring for why this
is optional rather than mandatory on every call). Both stores are
accepted as `Any`-typed passthrough parameters: this module deliberately
has no import of `epd2_credential_service.storage`/
`epd2_eligibility_service.storage` (or their `domain` modules) anywhere,
so it cannot even be tempted to reach past those two services' own
public application-layer contracts - `Any` is the honest type for "a
store object this module never inspects, constructs, or introspects,
only forwards".

No other PACK-03 service (`voting-service`) is ever imported here (ADR-008).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_credential_service.application import validate_participation_credential
from epd2_eligibility_service.application import get_eligibility_decision
from epd2_initiative_service.domain import (
    Amendment,
    AmendmentStatus,
    Initiative,
    InitiativeStatus,
    InitiativeVersion,
    SourceRecord,
    SourceVerificationStatus,
    SupportRecord,
    SupportStatus,
    compute_initiative_version_content_hash,
    compute_source_record_content_hash,
)
from epd2_initiative_service.events import (
    amendment_full_state_payload,
    build_amendment_accepted_event,
    build_amendment_published_event,
    build_amendment_rejected_event,
    build_amendment_submitted_event,
    build_archived_event,
    build_deliberation_started_event,
    build_draft_created_event,
    build_initiative_withdrawn_event,
    build_legal_review_requested_event,
    build_published_event,
    build_qualified_event,
    build_ready_for_ballot_event,
    build_revision_requested_event,
    build_submitted_event,
    build_support_added_event,
    build_support_withdrawn_event,
    build_version_created_event,
    initiative_full_state_payload,
    initiative_version_full_state_payload,
    source_record_full_state_payload,
    support_record_full_state_payload,
)
from epd2_initiative_service.exceptions import (
    AmendmentTargetSupersededError,
    InitiativeHasNoVersionError,
    InitiativeNotAcceptingSupportError,
    UnknownAmendmentError,
    UnknownEligibilityDecisionReferenceError,
    UnknownInitiativeError,
    UnknownSourceRecordError,
    UnknownSupportRecordError,
)
from epd2_initiative_service.storage import (
    AmendmentStore,
    InitiativeStore,
    InitiativeVersionStore,
    SourceRecordStore,
    SupportRecordStore,
)

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "initiative-service"

#: Audit reason_code by owned entity, one generic "status changed" code
#: per entity (mirroring `epd2_voting_service.application`'s single
#: `_BALLOT_STATUS_CHANGED` reused for every `Ballot` transition) - the
#: specific transition is already visible via `action`/`event_type` on
#: the audit record itself, so a separate code per transition would be
#: redundant.
_INITIATIVE_STATUS_CHANGED = "INITIATIVE_STATUS_CHANGED"
_INITIATIVE_VERSION_CREATED = "INITIATIVE_VERSION_CREATED"
_SUPPORT_RECORDED = "SUPPORT_RECORDED"
_SUPPORT_WITHDRAWN = "SUPPORT_WITHDRAWN"
#: Not one of canon's own commands (canon lists `support_withdrawn` but
#: not `support_invalidated`) - `invalidate_support` is this service's
#: own additive completion of `SupportRecord`'s `active -> invalidated`
#: edge (canon 11.3 lists the status but not who/how it is reached);
#: given its own audit code so it is never confused with a voluntary
#: withdrawal in the audit trail.
_SUPPORT_INVALIDATED = "SUPPORT_INVALIDATED"
_AMENDMENT_STATUS_CHANGED = "AMENDMENT_STATUS_CHANGED"
#: Reused from `AmendmentTargetSupersededError.reason_code` (see
#: exceptions.py) - the additive code canon's own text calls for under
#: `Amendment.status == superseded`.
_AMENDMENT_TARGET_SUPERSEDED = AmendmentTargetSupersededError.reason_code
_SOURCE_STATUS_CHANGED = "SOURCE_STATUS_CHANGED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class InitiativeResult:
    initiative: Initiative
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class InitiativeVersionResult:
    initiative: Initiative
    version: InitiativeVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SupportResult:
    initiative: Initiative
    support: SupportRecord
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AmendmentResult:
    amendment: Amendment
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SourceRecordResult:
    source: SourceRecord
    event: EventEnvelope | None
    audit_event: AuditEvent


# ============================================================================
# Initiative
# ============================================================================


def _initiative_audit_request(
    *,
    audit_event_id: UUID,
    event_type: str,
    initiative: Initiative,
    before_hash: str,
    actor: ActorRef,
    action: str,
    reason_code: str,
    correlation_id: UUID,
    occurred_at: Any,
) -> AppendAuditEventRequest:
    return AppendAuditEventRequest(
        audit_event_id=audit_event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="initiative",
        target_id=initiative.initiative_id,
        action=action,
        reason_code=reason_code,
        policy_version=AUDIT_POLICY_VERSION,
        correlation_id=correlation_id,
        source_service=_SOURCE_SERVICE,
        before_hash=before_hash,
        after_hash=compute_payload_hash(initiative_full_state_payload(initiative)),
    )


def create_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    space_id: UUID,
    author_actor_id: UUID,
    initiative_type: str,
    workflow_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """Create a new `Initiative` shell in `draft` (canon 11.1).
    `current_version_id` starts `None` - see `domain.Initiative`'s
    docstring for why - `create_initiative_version` must be called at
    least once (with `version_number=1`) before `submit_initiative` will
    accept this initiative (`InitiativeHasNoVersionError` otherwise)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an initiative")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    initiative = Initiative(
        initiative_id=initiative_id,
        space_id=space_id,
        current_version_id=None,
        author_actor_id=author_actor_id,
        initiative_type=initiative_type,
        workflow_id=workflow_id,
        status=InitiativeStatus.DRAFT,
        support_count=0,
        created_at=now,
    )
    stored = initiative_store.create(initiative)
    event = build_draft_created_event(
        event_id=resolved_event_id,
        initiative=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _initiative_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            initiative=stored,
            before_hash="",
            actor=actor,
            action="create",
            reason_code=_INITIATIVE_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return InitiativeResult(initiative=stored, event=event, audit_event=audit_event)


def create_initiative_version(
    initiative_store: InitiativeStore,
    version_store: InitiativeVersionStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    initiative_version_id: UUID,
    version_number: int,
    title: str,
    problem_statement: str,
    proposed_solution: str,
    affected_groups: tuple[str, ...],
    expected_effects: str,
    risks: str,
    estimated_resources: str,
    legal_questions: str,
    source_references: tuple[UUID, ...],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeVersionResult:
    """Create (or idempotently re-confirm) one immutable
    `InitiativeVersion` (canon 11.2: "Опубликованная версия не
    изменяется. Любая редакция создаёт новую версию" - a published
    version never changes; any edit creates a new version). Idempotent
    for an identical `(initiative_id, version_number)` + identical
    content; a resubmission of the same key with different content
    raises `VersionFrozenError` (via `InitiativeVersionStore.save`, see
    `storage.py`).

    Also advances `Initiative.current_version_id` to this version,
    *unless* a version with a higher `version_number` is already current
    (so a delayed retry of an older version never regresses the
    pointer). This is not a status transition, so it is folded into this
    same command/audit entry rather than a second one - the same "no
    extra command for a transition table has no edge for" shape
    `epd2_voting_service.application.open_ballot` uses for locking
    `BallotOption` rows alongside its own single audit entry."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an initiative version")

    initiative = initiative_store.get(initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {initiative_id}")

    content_hash = compute_initiative_version_content_hash(
        title=title,
        problem_statement=problem_statement,
        proposed_solution=proposed_solution,
        affected_groups=affected_groups,
        expected_effects=expected_effects,
        risks=risks,
        estimated_resources=estimated_resources,
        legal_questions=legal_questions,
        source_references=source_references,
    )
    version = InitiativeVersion(
        initiative_version_id=initiative_version_id,
        initiative_id=initiative_id,
        version_number=version_number,
        title=title,
        problem_statement=problem_statement,
        proposed_solution=proposed_solution,
        affected_groups=tuple(affected_groups),
        expected_effects=expected_effects,
        risks=risks,
        estimated_resources=estimated_resources,
        legal_questions=legal_questions,
        source_references=tuple(source_references),
        created_by_actor_id=actor.actor_id,
        content_hash=content_hash,
    )
    stored_version = version_store.save(version)

    current = (
        version_store.get_by_id(initiative.current_version_id)
        if initiative.current_version_id is not None
        else None
    )
    stored_initiative = initiative
    if current is None or stored_version.version_number > current.version_number:
        stored_initiative = initiative.with_current_version_id(stored_version.initiative_version_id)
        initiative_store.save(stored_initiative)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    event = build_version_created_event(
        event_id=resolved_event_id,
        version=stored_version,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="initiative_version",
            target_id=stored_version.initiative_version_id,
            action="create_version",
            reason_code=_INITIATIVE_VERSION_CREATED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(initiative_version_full_state_payload(stored_version)),
        ),
        clock=clock,
    )
    return InitiativeVersionResult(
        initiative=stored_initiative, version=stored_version, event=event, audit_event=audit_event
    )


def _initiative_transition(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    target_status: InitiativeStatus,
    action: str,
    build_event: Any,
    event_type_label: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None,
) -> InitiativeResult:
    """Shared shape for every `Initiative` status transition command
    (mirrors `epd2_voting_service.application._simple_ballot_transition`).
    `build_event` is `None` for a transition canon names no domain event
    for (e.g. `completeness_review`, `rejected`, `voting`, `adopted`) -
    persist + audit still happen (CT-00-07), just no `EventEnvelope` is
    built, mirroring `submit_ballot_for_configuration_review`'s own "no
    event for this step" precedent. `event_type_label` is always set (it
    becomes the audit record's own `event_type` field either way, real or
    synthetic) so the audit trail is never ambiguous about which
    transition occurred even when no wire event exists for it."""
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} an initiative")

    initiative = initiative_store.get(initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {initiative_id}")

    now = clock.now()
    before_hash = compute_payload_hash(initiative_full_state_payload(initiative))
    updated = initiative.with_status(target_status)
    initiative_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event: EventEnvelope | None = None
    if build_event is not None:
        event = build_event(
            event_id=resolved_event_id,
            initiative=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=now,
        )
    audit_event_id = event.event_id if event is not None else resolved_event_id
    audit_event_type = event.event_type if event is not None else event_type_label
    audit_event = append_audit_event(
        audit_store,
        _initiative_audit_request(
            audit_event_id=audit_event_id,
            event_type=audit_event_type,
            initiative=updated,
            before_hash=before_hash,
            actor=actor,
            action=action,
            reason_code=_INITIATIVE_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return InitiativeResult(initiative=updated, event=event, audit_event=audit_event)


def submit_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`draft -> submitted` or `revision_required -> submitted` (both
    land on `submitted`; canon names one event, `initiative.submitted`,
    for both source statuses - there is no separate "resubmit" command,
    mirroring how `epd2_voting_service.application.cast_vote` reuses one
    command across more than one legitimate calling context). Requires
    `Initiative.current_version_id` to already be set
    (`InitiativeHasNoVersionError` otherwise) - see
    `create_initiative_version`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit an initiative")

    initiative = initiative_store.get(initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {initiative_id}")
    if initiative.current_version_id is None:
        raise InitiativeHasNoVersionError(
            f"initiative {initiative_id} has no version yet; call create_initiative_version "
            "before submitting"
        )

    now = clock.now()
    before_hash = compute_payload_hash(initiative_full_state_payload(initiative))
    updated = initiative.with_status(InitiativeStatus.SUBMITTED)
    initiative_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_submitted_event(
        event_id=resolved_event_id,
        initiative=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _initiative_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            initiative=updated,
            before_hash=before_hash,
            actor=actor,
            action="submit",
            reason_code=_INITIATIVE_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return InitiativeResult(initiative=updated, event=event, audit_event=audit_event)


def start_completeness_review(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`submitted -> completeness_review`. Canon names no domain event
    for this step (only its two outcomes, `revision_required`/
    `published`, have names) - persist + audit only."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.COMPLETENESS_REVIEW,
        action="start_completeness_review",
        build_event=None,
        event_type_label="initiative.completeness_review_started",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def request_revision(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`completeness_review -> revision_required`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.REVISION_REQUIRED,
        action="request_revision",
        build_event=build_revision_requested_event,
        event_type_label="initiative.revision_requested",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def publish_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`completeness_review -> published`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.PUBLISHED,
        action="publish",
        build_event=build_published_event,
        event_type_label="initiative.published",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def start_support_collection(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`published -> support_collection`. Canon names no domain event for
    this step - persist + audit only."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.SUPPORT_COLLECTION,
        action="start_support_collection",
        build_event=None,
        event_type_label="initiative.support_collection_started",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def mark_qualified(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`support_collection -> qualified`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.QUALIFIED,
        action="mark_qualified",
        build_event=build_qualified_event,
        event_type_label="initiative.qualified",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def reject_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`support_collection -> rejected`, `legal_review -> rejected`, or
    `voting -> rejected` (all three land on `rejected`; canon names no
    domain event for this outcome on `Initiative` at all, unlike
    `Amendment.rejected`, which has `amendment.rejected` - persist + audit
    only)."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.REJECTED,
        action="reject",
        build_event=None,
        event_type_label="initiative.rejected",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def start_deliberation(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`qualified -> deliberation`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.DELIBERATION,
        action="start_deliberation",
        build_event=build_deliberation_started_event,
        event_type_label="initiative.deliberation_started",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def request_legal_review(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`deliberation -> legal_review`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.LEGAL_REVIEW,
        action="request_legal_review",
        build_event=build_legal_review_requested_event,
        event_type_label="initiative.legal_review_requested",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def mark_ready_for_ballot(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`legal_review -> ready_for_ballot`."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.READY_FOR_BALLOT,
        action="mark_ready_for_ballot",
        build_event=build_ready_for_ballot_event,
        event_type_label="initiative.ready_for_ballot",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def start_voting(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`ready_for_ballot -> voting`. Canon names no domain event for this
    step (the actual `Ballot` lifecycle events belong to `voting-service`,
    never this service - ADR-008) - persist + audit only."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.VOTING,
        action="start_voting",
        build_event=None,
        event_type_label="initiative.voting_started",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def mark_adopted(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`voting -> adopted`. Canon names no domain event for this step -
    persist + audit only."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.ADOPTED,
        action="mark_adopted",
        build_event=None,
        event_type_label="initiative.adopted",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def withdraw_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`{draft,submitted,completeness_review,revision_required,published,
    support_collection,qualified,deliberation,legal_review,
    ready_for_ballot} -> withdrawn` (the author's always-available early
    exit, pre-voting)."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.WITHDRAWN,
        action="withdraw",
        build_event=build_initiative_withdrawn_event,
        event_type_label="initiative.withdrawn",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def archive_initiative(
    initiative_store: InitiativeStore,
    audit_store: AuditEventStore,
    *,
    initiative_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> InitiativeResult:
    """`{adopted,rejected,withdrawn} -> archived` (fully terminal)."""
    return _initiative_transition(
        initiative_store,
        audit_store,
        initiative_id=initiative_id,
        target_status=InitiativeStatus.ARCHIVED,
        action="archive",
        build_event=build_archived_event,
        event_type_label="initiative.archived",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


# ============================================================================
# SupportRecord
# ============================================================================


def add_support(
    initiative_store: InitiativeStore,
    support_store: SupportRecordStore,
    audit_store: AuditEventStore,
    credential_store: Any,
    *,
    support_record_id: UUID,
    initiative_id: UUID,
    support_actor_reference: UUID,
    credential_reference: UUID,
    eligibility_decision_store: Any | None = None,
    eligibility_decision_id: UUID | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SupportResult:
    """Record one participant's active support for an initiative (canon
    11.3). `support_actor_reference`/`credential_reference` are opaque
    UUID references only - never an `account_id`/`identity_record_id`
    directly (see `domain.FORBIDDEN_FIELD_NAMES`).

    Order of checks, all fail-closed:
    1. `actor_is_authorized`.
    2. `Initiative` exists and `status == support_collection`
       (`InitiativeNotAcceptingSupportError` otherwise - this service's
       own additive completion of canon 11.3, see exceptions.py).
    3. The presented `credential_reference` validates as an
       `initiative_support` credential scoped to this initiative, via
       `epd2_credential_service.application.validate_participation_credential`
       (ADR-008) - an invalid credential raises `PermissionDeniedError`
       and no `SupportRecord` is ever persisted.
    4. *Optionally*, if the caller supplies `eligibility_decision_id` (and
       therefore `eligibility_decision_store`), the referenced
       `EligibilityDecision` is resolved via
       `epd2_eligibility_service.application.get_eligibility_decision`
       (ADR-008) and must itself say `decision == "eligible"`. This is
       deliberately optional rather than mandatory on every call: canon
       11.3 requires credential-gated support (`credential_reference` is
       a mandatory field on `SupportRecord` itself) but says nothing
       about *also* requiring a separately-modeled `EligibilityDecision`
       for every support action - some deployments may gate support
       purely on the `initiative_support` credential's own issuance
       policy, with no separate decision record to check. Callers that
       *do* model an eligibility-gated support pathway (e.g. "only
       verified residents of the affected region may support this
       initiative") pass both parameters and get the additional check;
       callers that do not, don't. See README.md.
    5. `storage.InMemorySupportRecordStore.create` itself enforces "one
       active support per participant per initiative"
       (`DuplicateSupportError`, canon section 24's `DUPLICATE_SUPPORT`,
       reused verbatim) and the plain creation-conflict/idempotency check
       (`SupportRecordCreationConflictError` / idempotent replay).

    `Initiative.support_count` is incremented in the same call, but only
    for a genuinely new `SupportRecord` - a CT-00-04 replay (same
    `support_record_id`, identical content) must not double-count."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to add support")

    initiative = initiative_store.get(initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {initiative_id}")
    if initiative.status != InitiativeStatus.SUPPORT_COLLECTION:
        raise InitiativeNotAcceptingSupportError(
            f"initiative {initiative_id} is not accepting support "
            f"(status {initiative.status.value!r})"
        )

    validation = validate_participation_credential(
        credential_store,
        credential_id=credential_reference,
        required_scope_type="initiative",
        required_scope_id=initiative_id,
        expected_rule_version=None,
        expected_digest=None,
        actor=actor,
        correlation_id=correlation_id,
        clock=clock,
    ).result
    if not validation.valid:
        raise PermissionDeniedError(
            f"credential {credential_reference} is not valid for initiative {initiative_id}: "
            f"{validation.reason_codes}"
        )

    if eligibility_decision_id is not None:
        if eligibility_decision_store is None:
            raise ValueError(
                "eligibility_decision_store is required when eligibility_decision_id is given"
            )
        decision = get_eligibility_decision(
            eligibility_decision_store, eligibility_decision_id=eligibility_decision_id
        )
        if decision is None:
            raise UnknownEligibilityDecisionReferenceError(
                f"unknown eligibility_decision_id: {eligibility_decision_id}"
            )
        if decision.decision.value != "eligible":
            raise PermissionDeniedError(
                f"eligibility_decision {eligibility_decision_id} is not 'eligible' "
                f"(got {decision.decision.value!r})"
            )

    now = clock.now()
    existing_before = support_store.get(support_record_id)
    support = SupportRecord(
        support_record_id=support_record_id,
        initiative_id=initiative_id,
        support_actor_reference=support_actor_reference,
        credential_reference=credential_reference,
        created_at=now,
        status=SupportStatus.ACTIVE,
    )
    stored_support = support_store.create(support)
    is_new = existing_before is None

    updated_initiative = initiative
    if is_new:
        updated_initiative = initiative.with_support_count(initiative.support_count + 1)
        initiative_store.save(updated_initiative)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_support_added_event(
        event_id=resolved_event_id,
        support=stored_support,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="support_record",
            target_id=stored_support.support_record_id,
            action="add_support",
            reason_code=_SUPPORT_RECORDED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(support_record_full_state_payload(stored_support)),
        ),
        clock=clock,
    )
    return SupportResult(
        initiative=updated_initiative, support=stored_support, event=event, audit_event=audit_event
    )


def withdraw_support(
    initiative_store: InitiativeStore,
    support_store: SupportRecordStore,
    audit_store: AuditEventStore,
    *,
    support_record_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SupportResult:
    """`active -> withdrawn`. Decrements `Initiative.support_count` in the
    same call (never lets the denormalized counter drift from the count
    of `active` `SupportRecord`s)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to withdraw support")

    support = support_store.get(support_record_id)
    if support is None:
        raise UnknownSupportRecordError(f"unknown support_record_id: {support_record_id}")
    initiative = initiative_store.get(support.initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {support.initiative_id}")

    now = clock.now()
    before_hash = compute_payload_hash(support_record_full_state_payload(support))
    updated_support = support.with_status(SupportStatus.WITHDRAWN)
    support_store.save(updated_support)
    updated_initiative = initiative.with_support_count(max(0, initiative.support_count - 1))
    initiative_store.save(updated_initiative)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_support_withdrawn_event(
        event_id=resolved_event_id,
        support=updated_support,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="support_record",
            target_id=updated_support.support_record_id,
            action="withdraw_support",
            reason_code=_SUPPORT_WITHDRAWN,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(support_record_full_state_payload(updated_support)),
        ),
        clock=clock,
    )
    return SupportResult(
        initiative=updated_initiative, support=updated_support, event=event, audit_event=audit_event
    )


def invalidate_support(
    initiative_store: InitiativeStore,
    support_store: SupportRecordStore,
    audit_store: AuditEventStore,
    *,
    support_record_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SupportResult:
    """`active -> invalidated` (e.g. a later credential revocation or
    fraud finding invalidates a previously-accepted support). Canon lists
    the `invalidated` status but names no domain event for reaching it -
    persist + audit only. Also decrements `Initiative.support_count`,
    exactly like `withdraw_support`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to invalidate support")

    support = support_store.get(support_record_id)
    if support is None:
        raise UnknownSupportRecordError(f"unknown support_record_id: {support_record_id}")
    initiative = initiative_store.get(support.initiative_id)
    if initiative is None:
        raise UnknownInitiativeError(f"unknown initiative_id: {support.initiative_id}")

    now = clock.now()
    before_hash = compute_payload_hash(support_record_full_state_payload(support))
    updated_support = support.with_status(SupportStatus.INVALIDATED)
    support_store.save(updated_support)
    updated_initiative = initiative.with_support_count(max(0, initiative.support_count - 1))
    initiative_store.save(updated_initiative)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="initiative.support_invalidated",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="support_record",
            target_id=updated_support.support_record_id,
            action="invalidate_support",
            reason_code=_SUPPORT_INVALIDATED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(support_record_full_state_payload(updated_support)),
        ),
        clock=clock,
    )
    return SupportResult(
        initiative=updated_initiative, support=updated_support, event=None, audit_event=audit_event
    )


# ============================================================================
# Amendment
# ============================================================================


def _amendment_audit_request(
    *,
    audit_event_id: UUID,
    event_type: str,
    amendment: Amendment,
    before_hash: str,
    actor: ActorRef,
    action: str,
    reason_code: str,
    correlation_id: UUID,
    occurred_at: Any,
) -> AppendAuditEventRequest:
    return AppendAuditEventRequest(
        audit_event_id=audit_event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="amendment",
        target_id=amendment.amendment_id,
        action=action,
        reason_code=reason_code,
        policy_version=AUDIT_POLICY_VERSION,
        correlation_id=correlation_id,
        source_service=_SOURCE_SERVICE,
        before_hash=before_hash,
        after_hash=compute_payload_hash(amendment_full_state_payload(amendment)),
    )


def create_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    initiative_id: UUID,
    target_version_id: UUID,
    proposer_actor_id: UUID,
    proposed_change: str,
    justification: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """Create a new `Amendment` in `draft` (canon 11.4). Canon names no
    domain event for this creation step (only `submitted`/`published`/
    `accepted`/`rejected` have names) - persist + audit only."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an amendment")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    amendment = Amendment(
        amendment_id=amendment_id,
        initiative_id=initiative_id,
        target_version_id=target_version_id,
        proposer_actor_id=proposer_actor_id,
        proposed_change=proposed_change,
        justification=justification,
        status=AmendmentStatus.DRAFT,
        decision_reference=None,
    )
    stored = amendment_store.create(amendment)
    audit_event = append_audit_event(
        audit_store,
        _amendment_audit_request(
            audit_event_id=resolved_event_id,
            event_type="amendment.draft_created",
            amendment=stored,
            before_hash="",
            actor=actor,
            action="create",
            reason_code=_AMENDMENT_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return AmendmentResult(amendment=stored, event=None, audit_event=audit_event)


def _amendment_transition(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    target_status: AmendmentStatus,
    action: str,
    build_event: Any,
    event_type_label: str,
    reason_code: str,
    decision_reference: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None,
) -> AmendmentResult:
    """Shared shape for every `Amendment` status transition command
    (mirrors `_initiative_transition` above)."""
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} an amendment")

    amendment = amendment_store.get(amendment_id)
    if amendment is None:
        raise UnknownAmendmentError(f"unknown amendment_id: {amendment_id}")

    now = clock.now()
    before_hash = compute_payload_hash(amendment_full_state_payload(amendment))
    updated = amendment.with_status(target_status)
    if decision_reference is not None:
        updated = updated.with_decision_reference(decision_reference)
    amendment_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event: EventEnvelope | None = None
    if build_event is not None:
        event = build_event(
            event_id=resolved_event_id,
            amendment=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=now,
        )
    audit_event_id = event.event_id if event is not None else resolved_event_id
    audit_event_type = event.event_type if event is not None else event_type_label
    audit_event = append_audit_event(
        audit_store,
        _amendment_audit_request(
            audit_event_id=audit_event_id,
            event_type=audit_event_type,
            amendment=updated,
            before_hash=before_hash,
            actor=actor,
            action=action,
            reason_code=reason_code,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return AmendmentResult(amendment=updated, event=event, audit_event=audit_event)


def submit_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`draft -> submitted`."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.SUBMITTED,
        action="submit",
        build_event=build_amendment_submitted_event,
        event_type_label="amendment.submitted",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def publish_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`submitted -> published`."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.PUBLISHED,
        action="publish",
        build_event=build_amendment_published_event,
        event_type_label="amendment.published",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def start_amendment_discussion(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`published -> under_discussion`. Canon names no domain event for
    this step - persist + audit only."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.UNDER_DISCUSSION,
        action="start_discussion",
        build_event=None,
        event_type_label="amendment.discussion_started",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def accept_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    decision_reference: UUID | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`under_discussion -> accepted`. `decision_reference` may be
    recorded in the same call (the outcome of whatever deliberation/
    decision process accepted it - an opaque reference this service never
    resolves, per the PACK-03 boundary)."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.ACCEPTED,
        action="accept",
        build_event=build_amendment_accepted_event,
        event_type_label="amendment.accepted",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def reject_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    decision_reference: UUID | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`under_discussion -> rejected`."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.REJECTED,
        action="reject",
        build_event=build_amendment_rejected_event,
        event_type_label="amendment.rejected",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def withdraw_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`{draft,submitted,published,under_discussion} -> withdrawn`. Canon
    names no domain event for this step - persist + audit only."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.WITHDRAWN,
        action="withdraw",
        build_event=None,
        event_type_label="amendment.withdrawn",
        reason_code=_AMENDMENT_STATUS_CHANGED,
        decision_reference=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def supersede_amendment(
    amendment_store: AmendmentStore,
    audit_store: AuditEventStore,
    *,
    amendment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AmendmentResult:
    """`{published,under_discussion} -> superseded` - this amendment's
    `target_version_id` is no longer the initiative's current version (a
    newer `InitiativeVersion` was published before a decision was
    reached). Canon names no domain event for this outcome - persist +
    audit only, using the additive `AMENDMENT_TARGET_SUPERSEDED` reason
    code (distinct from the generic `AMENDMENT_STATUS_CHANGED` every
    other transition uses) so the audit trail can tell "superseded by a
    newer version" apart from an ordinary status change at a glance."""
    return _amendment_transition(
        amendment_store,
        audit_store,
        amendment_id=amendment_id,
        target_status=AmendmentStatus.SUPERSEDED,
        action="supersede",
        build_event=None,
        event_type_label="amendment.superseded",
        reason_code=_AMENDMENT_TARGET_SUPERSEDED,
        decision_reference=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


# ============================================================================
# SourceRecord
# ============================================================================


def add_source_record(
    source_store: SourceRecordStore,
    audit_store: AuditEventStore,
    *,
    source_id: UUID,
    source_type: str,
    title: str,
    publisher: str,
    publication_date: datetime | None,
    url: str,
    archive_reference: str | None,
    added_by_actor_id: UUID,
    valid_until: datetime | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SourceRecordResult:
    """Create a new `SourceRecord` in `unverified` (canon 12.1). Canon
    names no domain event for `SourceRecord` at all (section 20.6-20.7
    lists no `source.*` event) - persist + audit only, for every command
    in this section."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to add a source record")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    content_hash = compute_source_record_content_hash(
        source_type=source_type,
        title=title,
        publisher=publisher,
        publication_date=publication_date,
        url=url,
        archive_reference=archive_reference,
    )
    source = SourceRecord(
        source_id=source_id,
        source_type=source_type,
        title=title,
        publisher=publisher,
        publication_date=publication_date,
        url=url,
        archive_reference=archive_reference,
        verification_status=SourceVerificationStatus.UNVERIFIED,
        added_by_actor_id=added_by_actor_id,
        accessed_at=now,
        content_hash=content_hash,
        valid_until=valid_until,
    )
    stored = source_store.create(source)
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="source_record.added",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="source_record",
            target_id=stored.source_id,
            action="create",
            reason_code=_SOURCE_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(source_record_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return SourceRecordResult(source=stored, event=None, audit_event=audit_event)


def update_source_verification_status(
    source_store: SourceRecordStore,
    audit_store: AuditEventStore,
    *,
    source_id: UUID,
    target_status: SourceVerificationStatus,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SourceRecordResult:
    """Transition a `SourceRecord`'s `verification_status` (canon 12.1's
    `ALLOWED_SOURCE_VERIFICATION_TRANSITIONS`). Canon's hard rule: "ИИ не
    может незаметно повысить статус источника до `human_checked`" (an AI
    actor may not silently promote a source's status to `human_checked`)
    - enforced here: if `target_status == human_checked` and
    `actor.actor_type == "ai"`, raises `PermissionDeniedError` before any
    other check, regardless of `actor_is_authorized` (an authorization
    flag from an upstream policy engine is not a substitute for this
    structural, actor-*type*-based rule - the same shape
    `epd2_voting_service.application.approve_ballot_configuration` uses
    for its own actor-identity check, ADR-009 item 7)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to update source verification status")
    if target_status == SourceVerificationStatus.HUMAN_CHECKED and actor.actor_type == "ai":
        raise PermissionDeniedError(
            "an AI actor may not promote a source record to human_checked "
            "(canon 12.1: 'ИИ не может незаметно повысить статус источника до human_checked')"
        )

    source = source_store.get(source_id)
    if source is None:
        raise UnknownSourceRecordError(f"unknown source_id: {source_id}")

    now = clock.now()
    before_hash = compute_payload_hash(source_record_full_state_payload(source))
    updated = source.with_verification_status(target_status)
    source_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="source_record.verification_status_changed",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="source_record",
            target_id=updated.source_id,
            action="update_verification_status",
            reason_code=_SOURCE_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(source_record_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return SourceRecordResult(source=updated, event=None, audit_event=audit_event)
