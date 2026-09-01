"""Deliberation Service application layer: `open_discussion`,
`close_discussion`, `create_contribution`, `edit_contribution`,
`flag_contribution`, `hide_contribution`, `restore_contribution` (canon
section 20.8's exact event list, one command per event), plus
`limit_discussion`, `set_discussion_read_only`, `reopen_discussion`,
`archive_discussion` - the four `Discussion` transitions canon's
transition table (section 13.1) defines but section 20.8 names no event
for. Those four persist + audit only (see `DiscussionTransitionResult`)
and never build an `EventEnvelope`.

Every state-changing command here follows the same idempotency shape
`issue_participation_credential` (credential-service) established: the
caller may pass a stable `event_id`, which is reused as the audit call's
`audit_event_id` (CT-00-04). Commands whose domain transition is not
naturally idempotent on retry (`close_discussion`, `edit_contribution`,
`hide_contribution`, `restore_contribution`, and the four no-event
transitions - each mutates state such that blindly re-applying the same
transition on a second call would raise a forbidden-transition error,
since by then the entity already reflects the first call's result) look
up any existing audit record for `event_id` *before* touching the store,
and short-circuit to the original result on a genuine replay.
`open_discussion`/`create_contribution` rely on their store's own
content-based dedup instead (mirroring `CredentialStore.issue`), and
`flag_contribution` needs no special handling at all, since it never
mutates stored state.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_deliberation_service.domain import (
    Contribution,
    ContributionType,
    ContributionVisibilityStatus,
    Discussion,
    DiscussionStatus,
    compute_contribution_content_hash,
)
from epd2_deliberation_service.events import (
    build_contribution_created_event,
    build_contribution_edited_event,
    build_contribution_flagged_event,
    build_contribution_hidden_event,
    build_contribution_restored_event,
    build_discussion_closed_event,
    build_discussion_opened_event,
    contribution_full_state_payload,
    discussion_full_state_payload,
)
from epd2_deliberation_service.exceptions import (
    ForbiddenContributionVisibilityTransitionError,
    UnknownContributionError,
    UnknownDiscussionError,
)
from epd2_deliberation_service.storage import ContributionStore, DiscussionStore

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "deliberation-service"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class OpenDiscussionResult:
    discussion: Discussion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CloseDiscussionResult:
    discussion: Discussion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DiscussionTransitionResult:
    """Result shape for the `Discussion` transitions canon section 20.8
    names no event for (`limited`, `read_only`, reopening back to `open`,
    `archived` - see `_simple_discussion_transition_no_event` and
    README.md's "no-domain-event Discussion transitions" section). Unlike
    every other result type in this module, there is deliberately no
    `event: EventEnvelope` field here - canon defines no event for any of
    these four transitions, so none is ever built; CT-00-07 / INV-04 still
    requires the audit entry, which is why `audit_event` remains."""

    discussion: Discussion
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CreateContributionResult:
    contribution: Contribution
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class EditContributionResult:
    contribution: Contribution
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class FlagContributionResult:
    contribution: Contribution
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class HideContributionResult:
    contribution: Contribution
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class RestoreContributionResult:
    contribution: Contribution
    event: EventEnvelope
    audit_event: AuditEvent


def open_discussion(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    subject_type: str,
    subject_id: UUID,
    space_id: UUID,
    moderation_policy_id: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> OpenDiscussionResult:
    """Open a new `Discussion` in `open` status.

    `event_id` is CT-00-04's idempotency key: a caller retrying this exact
    command (same `event_id`, `discussion_id`, and content) gets back the
    original result. This relies on `DiscussionStore.create`'s own
    content-based dedup (the same shape as `CredentialStore.issue`): a
    retried call with identical content produces an identical `Discussion`
    object, so `store.create` returns the existing record unchanged, and
    the subsequent `append_audit_event` call - built from that same
    unchanged object, the same `event_id`, and (assuming the same `clock`
    value, e.g. a `FixedClock` in tests) the same `occurred_at` - is
    itself idempotent by construction.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to open a discussion")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    discussion = Discussion(
        discussion_id=discussion_id,
        subject_type=subject_type,
        subject_id=subject_id,
        space_id=space_id,
        status=DiscussionStatus.OPEN,
        moderation_policy_id=moderation_policy_id,
    )
    stored = store.create(discussion)
    event = build_discussion_opened_event(
        event_id=resolved_event_id,
        discussion=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: opening a discussion is a critical, politically
    # significant action and must leave an audit trail.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="discussion",
            target_id=stored.discussion_id,
            action="open",
            reason_code="DISCUSSION_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(discussion_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return OpenDiscussionResult(discussion=stored, event=event, audit_event=audit_event)


def close_discussion(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> CloseDiscussionResult:
    """Close an `open`/`limited`/`read_only` discussion (canon 13.1's
    transition table - `assert_discussion_transition_allowed` via
    `Discussion.with_status` enforces exactly those three source
    statuses).

    Idempotency (CT-00-04): unlike `open_discussion`, blindly re-running
    this function's transition on a replayed call would fail, because by
    the time of the replay `store.get(discussion_id)` already returns the
    *closed* discussion from the first call, and `closed -> closed` is not
    an allowed transition. So this function checks
    `audit_store.get_by_event_id(resolved_event_id)` first: if a matching
    audit record already exists, it returns the current stored state and
    that existing audit entry directly, without re-attempting the
    transition or appending a second audit entry.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to close a discussion")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    discussion = store.get(discussion_id)
    if discussion is None:
        raise UnknownDiscussionError(f"unknown discussion_id: {discussion_id}")

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_discussion_closed_event(
            event_id=resolved_event_id,
            discussion=discussion,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=existing_audit.occurred_at,
        )
        return CloseDiscussionResult(discussion=discussion, event=event, audit_event=existing_audit)

    before_hash = compute_payload_hash(discussion_full_state_payload(discussion))
    updated = discussion.with_status(DiscussionStatus.CLOSED)
    store.save(updated)
    now = clock.now()
    event = build_discussion_closed_event(
        event_id=resolved_event_id,
        discussion=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type="discussion",
            target_id=updated.discussion_id,
            action="close",
            reason_code="DISCUSSION_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(discussion_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return CloseDiscussionResult(discussion=updated, event=event, audit_event=audit_event)


def _simple_discussion_transition_no_event(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    target_status: DiscussionStatus,
    action: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None,
) -> DiscussionTransitionResult:
    """Shared body for the four `Discussion` transitions canon section
    20.8 names no event for: `open -> limited`, `open|limited ->
    read_only`, `limited|read_only -> open` (reopening), and `closed ->
    archived`. Every one of these is still a real, politically relevant
    status change, so it is still persisted and audited (CT-00-07 /
    INV-04) exactly like every evented transition - it simply never
    builds an `EventEnvelope`, mirroring
    `epd2_voting_service.application.submit_ballot_for_configuration_review`'s
    own "no event for this step" precedent. The specific source status
    each caller may transition from is enforced entirely by
    `Discussion.with_status` (`assert_discussion_transition_allowed`
    against canon's own transition table) - this helper does not
    re-validate it.

    Idempotency (CT-00-04): same replay hazard `close_discussion` has (a
    naive re-application would see the already-transitioned discussion and
    raise a forbidden-transition error) - checked via
    `audit_store.get_by_event_id` before mutating, same pattern.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} a discussion")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    discussion = store.get(discussion_id)
    if discussion is None:
        raise UnknownDiscussionError(f"unknown discussion_id: {discussion_id}")

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        return DiscussionTransitionResult(discussion=discussion, audit_event=existing_audit)

    before_hash = compute_payload_hash(discussion_full_state_payload(discussion))
    updated = discussion.with_status(target_status)
    store.save(updated)
    now = clock.now()
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=f"discussion.{action}",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="discussion",
            target_id=updated.discussion_id,
            action=action,
            reason_code="DISCUSSION_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(discussion_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return DiscussionTransitionResult(discussion=updated, audit_event=audit_event)


def limit_discussion(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DiscussionTransitionResult:
    """`open -> limited`. Canon section 20.8 names no event for this
    transition - persist + audit only (see `DiscussionTransitionResult`
    and README.md)."""
    return _simple_discussion_transition_no_event(
        store,
        audit_store,
        discussion_id=discussion_id,
        target_status=DiscussionStatus.LIMITED,
        action="limit",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def set_discussion_read_only(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DiscussionTransitionResult:
    """`open|limited -> read_only`. Canon section 20.8 names no event for
    this transition - persist + audit only."""
    return _simple_discussion_transition_no_event(
        store,
        audit_store,
        discussion_id=discussion_id,
        target_status=DiscussionStatus.READ_ONLY,
        action="set_read_only",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def reopen_discussion(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DiscussionTransitionResult:
    """`limited|read_only -> open`. Canon section 20.8 names no event for
    this transition - persist + audit only. (Distinct from
    `open_discussion`, which creates a brand-new `Discussion` in `open`
    status; this reopens an existing one.)"""
    return _simple_discussion_transition_no_event(
        store,
        audit_store,
        discussion_id=discussion_id,
        target_status=DiscussionStatus.OPEN,
        action="reopen",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def archive_discussion(
    store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    discussion_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DiscussionTransitionResult:
    """`closed -> archived`, canon's one terminal transition. Canon
    section 20.8 names no event for this transition - persist + audit
    only."""
    return _simple_discussion_transition_no_event(
        store,
        audit_store,
        discussion_id=discussion_id,
        target_status=DiscussionStatus.ARCHIVED,
        action="archive",
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def create_contribution(
    contribution_store: ContributionStore,
    discussion_store: DiscussionStore,
    audit_store: AuditEventStore,
    *,
    contribution_id: UUID,
    discussion_id: UUID,
    author_actor_id: UUID,
    parent_contribution_id: UUID | None,
    contribution_type: ContributionType,
    content: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> CreateContributionResult:
    """Create a new `Contribution` in `visible` status.

    Validates `discussion_id` references an existing `Discussion`, and -
    if given - that `parent_contribution_id` references an existing
    `Contribution` in that *same* discussion (spec section 3). Idempotent
    the same way `open_discussion` is: relies on `ContributionStore.create`'s
    content-based dedup.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create a contribution")

    if discussion_store.get(discussion_id) is None:
        raise UnknownDiscussionError(f"unknown discussion_id: {discussion_id}")

    if parent_contribution_id is not None:
        parent = contribution_store.get(parent_contribution_id)
        if parent is None or parent.discussion_id != discussion_id:
            raise UnknownContributionError(
                f"parent_contribution_id {parent_contribution_id} does not reference an "
                f"existing contribution in discussion {discussion_id}"
            )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    content_hash = compute_contribution_content_hash(
        content=content, contribution_type=contribution_type
    )
    contribution = Contribution(
        contribution_id=contribution_id,
        discussion_id=discussion_id,
        author_actor_id=author_actor_id,
        parent_contribution_id=parent_contribution_id,
        contribution_type=contribution_type,
        content=content,
        content_hash=content_hash,
        visibility_status=ContributionVisibilityStatus.VISIBLE,
        created_at=now,
        edited_version=1,
    )
    stored = contribution_store.create(contribution)
    event = build_contribution_created_event(
        event_id=resolved_event_id,
        contribution=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type="contribution",
            target_id=stored.contribution_id,
            action="create",
            reason_code="CONTRIBUTION_CREATED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(contribution_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return CreateContributionResult(contribution=stored, event=event, audit_event=audit_event)


def edit_contribution(
    store: ContributionStore,
    audit_store: AuditEventStore,
    *,
    contribution_id: UUID,
    new_content: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> EditContributionResult:
    """Edit a `Contribution`'s content: creates a new `edited_version` and
    recomputes `content_hash`; does not change `visibility_status` (spec
    section 3).

    Idempotency (CT-00-04): the same replay problem `close_discussion` has
    - a naive re-application would increment `edited_version` a second
    time and produce a different `content_hash`-bearing audit request,
    which `append_audit_event` would then reject as a conflict rather than
    recognize as a replay. Checked via `audit_store.get_by_event_id`
    before mutating, same as `close_discussion`.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to edit a contribution")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    contribution = store.get(contribution_id)
    if contribution is None:
        raise UnknownContributionError(f"unknown contribution_id: {contribution_id}")

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_contribution_edited_event(
            event_id=resolved_event_id,
            contribution=contribution,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=existing_audit.occurred_at,
        )
        return EditContributionResult(
            contribution=contribution, event=event, audit_event=existing_audit
        )

    before_hash = compute_payload_hash(contribution_full_state_payload(contribution))
    updated = contribution.with_edited_content(new_content)
    store.save(updated)
    now = clock.now()
    event = build_contribution_edited_event(
        event_id=resolved_event_id,
        contribution=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type="contribution",
            target_id=updated.contribution_id,
            action="edit",
            reason_code="CONTRIBUTION_EDITED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(contribution_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return EditContributionResult(contribution=updated, event=event, audit_event=audit_event)


def flag_contribution(
    store: ContributionStore,
    audit_store: AuditEventStore,
    *,
    contribution_id: UUID,
    flag_reason_code: str,
    note: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> FlagContributionResult:
    """Record that `actor` flagged `contribution_id` for moderation
    review. `flag_reason_code` is typically canon section 24's
    `MODERATION_POLICY_VIOLATION`, but this function accepts any
    non-empty string reason so it does not hard-code a closed enum canon
    does not itself define for flagging specifically.

    This command never changes `visibility_status` by itself - a flag is
    what typically triggers a `moderation-service` `ModerationCase`
    (canon section 14.1) in the full system, which then independently
    decides whether to hide the contribution. Per ADR-005/ADR-008,
    `deliberation-service` has **no** dependency on `moderation-service`
    (neither is in the other's allowed-edge list) - this function must
    not, and does not, import or call into it; it only emits
    `contribution.flagged` for some other process to react to.

    Idempotency: this command never mutates `Contribution` state, so a
    replayed call (same `event_id`, same `clock` value) naturally
    produces an identical `AppendAuditEventRequest`, which
    `append_audit_event` recognizes as a replay on its own - no
    pre-check needed here (unlike `close_discussion`/`edit_contribution`/
    `hide_contribution`/`restore_contribution`).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to flag a contribution")
    if not flag_reason_code:
        raise ValueError("flag_reason_code must not be empty")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    contribution = store.get(contribution_id)
    if contribution is None:
        raise UnknownContributionError(f"unknown contribution_id: {contribution_id}")

    now = clock.now()
    event = build_contribution_flagged_event(
        event_id=resolved_event_id,
        contribution=contribution,
        flag_reason_code=flag_reason_code,
        note=note,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    # No visibility_status change: before_hash == after_hash. CT-00-07 /
    # INV-04 still requires an audit entry for the flagging action itself,
    # even though the flagged Contribution's own state is untouched.
    state_hash = compute_payload_hash(contribution_full_state_payload(contribution))
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="contribution",
            target_id=contribution.contribution_id,
            action="flag",
            reason_code="CONTRIBUTION_FLAGGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=state_hash,
            after_hash=state_hash,
        ),
        clock=clock,
    )
    return FlagContributionResult(contribution=contribution, event=event, audit_event=audit_event)


def hide_contribution(
    store: ContributionStore,
    audit_store: AuditEventStore,
    *,
    contribution_id: UUID,
    target_status: ContributionVisibilityStatus,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> HideContributionResult:
    """Move a `visible` contribution to `temporarily_hidden`, `restricted`,
    or `removed_from_public_view` (the caller passes the exact target;
    `Contribution.with_visibility_status` validates it is one of those
    three via `assert_contribution_visibility_transition_allowed` - any
    other `target_status`, or a `contribution` not currently `visible`,
    is rejected as a forbidden transition).

    Idempotency (CT-00-04): same replay problem as `close_discussion` -
    checked via `audit_store.get_by_event_id` before mutating.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to hide a contribution")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    contribution = store.get(contribution_id)
    if contribution is None:
        raise UnknownContributionError(f"unknown contribution_id: {contribution_id}")

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_contribution_hidden_event(
            event_id=resolved_event_id,
            contribution=contribution,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=existing_audit.occurred_at,
        )
        return HideContributionResult(
            contribution=contribution, event=event, audit_event=existing_audit
        )

    before_hash = compute_payload_hash(contribution_full_state_payload(contribution))
    updated = contribution.with_visibility_status(target_status)
    store.save(updated)
    now = clock.now()
    event = build_contribution_hidden_event(
        event_id=resolved_event_id,
        contribution=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type="contribution",
            target_id=updated.contribution_id,
            action="hide",
            reason_code="CONTRIBUTION_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(contribution_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return HideContributionResult(contribution=updated, event=event, audit_event=audit_event)


def _next_restore_target(
    current: ContributionVisibilityStatus,
) -> ContributionVisibilityStatus:
    """Design choice for `restore_contribution` (see its docstring):
    canon section 20.8 defines exactly one event, `contribution.restored`,
    for the entire "moving back out of a hidden state" direction - there
    is no second canonical event name for the `restored -> visible` leg.
    Rather than inventing an event name canon does not define, this
    service reuses `restore_contribution`/`contribution.restored` for
    both legs of the journey, dispatching the actual target status on
    the contribution's *current* status:
    - `temporarily_hidden`/`restricted`/`removed_from_public_view` -> `restored`
    - `restored` -> `visible`
    Each call is still its own transition and its own audit entry - no
    hop is silently skipped. A caller that wants a `temporarily_hidden`
    contribution to end up fully `visible` again must call
    `restore_contribution` twice, once per hop.
    """
    if current in (
        ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        ContributionVisibilityStatus.RESTRICTED,
        ContributionVisibilityStatus.REMOVED_FROM_PUBLIC_VIEW,
    ):
        return ContributionVisibilityStatus.RESTORED
    if current == ContributionVisibilityStatus.RESTORED:
        return ContributionVisibilityStatus.VISIBLE
    raise ForbiddenContributionVisibilityTransitionError(
        f"no restore transition is defined from {current.value!r}"
    )


def restore_contribution(
    store: ContributionStore,
    audit_store: AuditEventStore,
    *,
    contribution_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
    event_id: UUID | None = None,
) -> RestoreContributionResult:
    """Restore a hidden/restricted/removed contribution one step back
    towards visibility (see `_next_restore_target` for the two-leg
    design rationale). Emits `contribution.restored` for both legs.

    Idempotency (CT-00-04): same replay problem as `close_discussion` -
    checked via `audit_store.get_by_event_id` before mutating.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to restore a contribution")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    contribution = store.get(contribution_id)
    if contribution is None:
        raise UnknownContributionError(f"unknown contribution_id: {contribution_id}")

    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        event = build_contribution_restored_event(
            event_id=resolved_event_id,
            contribution=contribution,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=existing_audit.occurred_at,
        )
        return RestoreContributionResult(
            contribution=contribution, event=event, audit_event=existing_audit
        )

    target_status = _next_restore_target(contribution.visibility_status)
    before_hash = compute_payload_hash(contribution_full_state_payload(contribution))
    updated = contribution.with_visibility_status(target_status)
    store.save(updated)
    now = clock.now()
    event = build_contribution_restored_event(
        event_id=resolved_event_id,
        contribution=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type="contribution",
            target_id=updated.contribution_id,
            action="restore",
            reason_code="CONTRIBUTION_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(contribution_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return RestoreContributionResult(contribution=updated, event=event, audit_event=audit_event)
