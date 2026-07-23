"""Voting Service application layer: the command set canon section 20.10
lists for this service, plus small unaudited/no-event helper functions
documented inline where they depart from a one-command-one-event shape
(mirroring `epd2_eligibility_service.application`'s own precedent for
steps canon gives no event name for).

PACK-02 boundary (ADR-008): this module calls exactly two PACK-02
`application`-layer functions -
`epd2_credential_service.application.validate_participation_credential`
(validate a `ballot_access` credential before accepting a `VoteEnvelope`)
and `epd2_eligibility_service.application.get_eligibility_snapshot`
(freeze a ballot's configuration against a real `EligibilitySnapshot`).
Both stores are accepted as `Any`-typed passthrough parameters: this
module deliberately has no import of
`epd2_credential_service.storage`/`epd2_eligibility_service.storage` (or
their `domain` modules) anywhere, so it cannot even be tempted to reach
past those two services' own public application-layer contracts - `Any`
is the honest type for "a store object this module never inspects,
constructs, or introspects, only forwards".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_credential_service.application import validate_participation_credential
from epd2_eligibility_service.application import get_eligibility_snapshot
from epd2_voting_service.domain import (
    Ballot,
    BallotMethod,
    BallotOption,
    BallotOptionStatus,
    BallotStatus,
    VoteEnvelope,
    VoteEnvelopeStatus,
    VoteReceipt,
    VoteReceiptVerificationStatus,
    compute_ballot_configuration_hash,
    compute_vote_envelope_integrity_hash,
    compute_vote_receipt_hash,
    effective_challenge_window_hours,
)
from epd2_voting_service.events import (
    ballot_full_state_payload,
    build_ballot_cancelled_event,
    build_ballot_closed_event,
    build_ballot_configuration_locked_event,
    build_ballot_created_event,
    build_ballot_opened_event,
    build_ballot_paused_event,
    build_ballot_resumed_event,
    build_ballot_scheduled_event,
    build_vote_received_event,
    build_vote_rejected_event,
    build_vote_superseded_event,
    build_vote_validated_event,
    vote_envelope_full_state_payload,
)
from epd2_voting_service.exceptions import (
    BallotAlreadyClosedError,
    BallotConfigurationLockedError,
    BallotNotOpenError,
    DuplicateVoteError,
    UnknownBallotError,
    UnknownEligibilitySnapshotReferenceError,
    UnknownVoteEnvelopeError,
    VoteEnvelopeNotReceiptEligibleError,
)
from epd2_voting_service.storage import (
    BallotOptionStore,
    BallotStore,
    VoteEnvelopeStore,
    VoteReceiptStore,
)

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "voting-service"

#: Audit reason_code for every `Ballot` status transition (create,
#: submit-for-review, approve/lock, open, pause, resume, close, cancel).
#: Canon gives this service only one ballot-lifecycle audit
#: classification, not one per event type - the specific transition is
#: already visible via `action`/`event_type` on the audit record itself.
_BALLOT_STATUS_CHANGED = "BALLOT_STATUS_CHANGED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class BallotResult:
    ballot: Ballot
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ApproveBallotConfigurationResult:
    """`approve_ballot_configuration` performs the single
    `configuration_review -> scheduled` transition available in
    `ALLOWED_TRANSITIONS` but must emit BOTH `ballot.configuration_locked`
    and `ballot.scheduled` (see README.md's "why one command, two
    events" note) - so it returns both events/audit records rather than
    forcing an artificial second command onto a transition that does not
    exist twice in the state machine."""

    ballot: Ballot
    configuration_locked_event: EventEnvelope
    configuration_locked_audit_event: AuditEvent
    scheduled_event: EventEnvelope
    scheduled_audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class OpenBallotResult:
    ballot: Ballot
    locked_options: tuple[BallotOption, ...]
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CastVoteResult:
    envelope: VoteEnvelope
    event: EventEnvelope
    audit_event: AuditEvent
    superseded_envelope: VoteEnvelope | None
    superseded_event: EventEnvelope | None
    superseded_audit_event: AuditEvent | None


@dataclass(frozen=True, slots=True)
class ValidateVoteResult:
    envelope: VoteEnvelope
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class IssueReceiptResult:
    receipt: VoteReceipt
    audit_event: AuditEvent


def _ballot_audit_request(
    *,
    audit_event_id: UUID,
    event_type: str,
    ballot: Ballot,
    before_hash: str,
    actor: ActorRef,
    action: str,
    correlation_id: UUID,
    occurred_at: Any,
) -> AppendAuditEventRequest:
    return AppendAuditEventRequest(
        audit_event_id=audit_event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="ballot",
        target_id=ballot.ballot_id,
        action=action,
        reason_code=_BALLOT_STATUS_CHANGED,
        policy_version=AUDIT_POLICY_VERSION,
        correlation_id=correlation_id,
        source_service=_SOURCE_SERVICE,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ballot_full_state_payload(ballot)),
    )


def create_ballot(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    space_id: UUID,
    subject_type: str,
    subject_id: UUID,
    question: str,
    ballot_method: BallotMethod,
    secrecy_mode: str,
    eligibility_rule_version: int,
    delegation_policy_version: int,
    quorum_rule: str,
    threshold_rule: str,
    opens_at: Any,
    closes_at: Any,
    challenge_window_hours: int | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """Create a new `Ballot` in `draft` (canon 15.1). All configuration
    fields are supplied up front; they remain mutable (via a fresh
    `create_ballot`-then-`ballot_store.save` cycle, or direct
    `ballot_store.save`) only while `status == draft` - `InMemoryBallotStore.save`
    itself enforces CT-00-10's freeze from `configuration_review` onward,
    so no separate "update draft configuration" command is needed here.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create a ballot")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    ballot = Ballot(
        ballot_id=ballot_id,
        space_id=space_id,
        subject_type=subject_type,
        subject_id=subject_id,
        question=question,
        ballot_method=ballot_method,
        secrecy_mode=secrecy_mode,
        eligibility_rule_version=eligibility_rule_version,
        delegation_policy_version=delegation_policy_version,
        quorum_rule=quorum_rule,
        threshold_rule=threshold_rule,
        opens_at=opens_at,
        closes_at=closes_at,
        status=BallotStatus.DRAFT,
        configuration_hash=None,
        challenge_window_hours=challenge_window_hours,
    )
    stored = ballot_store.create(ballot, created_by_actor_id=actor.actor_id)
    event = build_ballot_created_event(
        event_id=resolved_event_id,
        ballot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            ballot=stored,
            before_hash="",
            actor=actor,
            action="create",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return BallotResult(ballot=stored, event=event, audit_event=audit_event)


def submit_ballot_for_configuration_review(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    eligibility_snapshot_store: Any,
    *,
    ballot_id: UUID,
    eligibility_snapshot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """`draft -> configuration_review`: computes and freezes
    `configuration_hash` (CT-00-10), confirming the referenced
    `EligibilitySnapshot` is real via
    `epd2_eligibility_service.application.get_eligibility_snapshot`
    (ADR-008) and folding its `digest` into the hash. Canon names no
    domain event for this specific sub-step (only `approve_ballot_configuration`'s
    later `configuration_review -> scheduled` step emits
    `ballot.configuration_locked`) - this function still persists and
    audits (every state-changing command must, per CT-00-07), it simply
    builds no `EventEnvelope`, mirroring
    `epd2_eligibility_service.application.create_eligibility_rule`'s own
    "no event for this step" precedent (that function goes further and
    skips the audit entirely, since it precedes any real transition;
    here there *is* a real ballot status transition, so unlike that
    precedent, an audit entry is still required)."""
    if not actor_is_authorized:
        raise PermissionDeniedError(
            "actor is not authorized to submit a ballot for configuration review"
        )

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")

    snapshot = get_eligibility_snapshot(
        eligibility_snapshot_store, eligibility_snapshot_id=eligibility_snapshot_id
    )
    if snapshot is None:
        raise UnknownEligibilitySnapshotReferenceError(
            f"unknown eligibility_snapshot_id: {eligibility_snapshot_id}"
        )
    if snapshot.rule_version != ballot.eligibility_rule_version:
        raise ValueError(
            "eligibility_snapshot rule_version "
            f"{snapshot.rule_version} does not match ballot.eligibility_rule_version "
            f"{ballot.eligibility_rule_version}"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    before_hash = compute_payload_hash(ballot_full_state_payload(ballot))

    configuration_hash = compute_ballot_configuration_hash(
        ballot_method=ballot.ballot_method,
        secrecy_mode=ballot.secrecy_mode,
        eligibility_rule_version=ballot.eligibility_rule_version,
        delegation_policy_version=ballot.delegation_policy_version,
        quorum_rule=ballot.quorum_rule,
        threshold_rule=ballot.threshold_rule,
        opens_at=ballot.opens_at,
        closes_at=ballot.closes_at,
        challenge_window_hours=effective_challenge_window_hours(ballot),
        eligibility_snapshot_digest=snapshot.digest,
    )
    updated = ballot.with_configuration_locked(configuration_hash)
    stored = ballot_store.save(updated)
    ballot_store.set_frozen_eligibility_snapshot_digest(ballot_id, snapshot.digest)

    audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=resolved_event_id,
            event_type="ballot.configuration_review_submitted",
            ballot=stored,
            before_hash=before_hash,
            actor=actor,
            action="submit_for_configuration_review",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return BallotResult(ballot=stored, event=None, audit_event=audit_event)


def approve_ballot_configuration(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ApproveBallotConfigurationResult:
    """`configuration_review -> scheduled` (the only transition into
    `scheduled` `ALLOWED_TRANSITIONS` has). ADR-009 item 7 / INV-08: the
    approving actor must differ from the ballot's own creator
    (`created_by_actor_id_for`, internal bookkeeping - see storage.py).

    Emits BOTH `ballot.configuration_locked` and `ballot.scheduled` for
    this one transition: canon's command list (section 20.10) names both
    events, but `ALLOWED_TRANSITIONS` has only one edge landing on
    `scheduled`, so there is no second, separate transition a
    stand-alone `schedule_ballot` command could perform - see
    `ApproveBallotConfigurationResult`'s docstring and README.md."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to approve a ballot configuration")

    created_by = ballot_store.created_by_actor_id_for(ballot_id)
    if created_by is not None and created_by == actor.actor_id:
        raise PermissionDeniedError(
            "the actor who created this ballot may not approve its own configuration "
            "(ADR-009 item 7 / INV-08)"
        )

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")

    now = clock.now()
    before_hash = compute_payload_hash(ballot_full_state_payload(ballot))
    updated = ballot.with_status(BallotStatus.SCHEDULED)
    stored = ballot_store.save(updated)

    locked_event_id = event_id if event_id is not None else generate_uuid()
    locked_event = build_ballot_configuration_locked_event(
        event_id=locked_event_id,
        ballot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    locked_audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=locked_event.event_id,
            event_type=locked_event.event_type,
            ballot=stored,
            before_hash=before_hash,
            actor=actor,
            action="approve_configuration",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )

    scheduled_event = build_ballot_scheduled_event(
        event_id=generate_uuid(),
        ballot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=locked_event.event_id,
        occurred_at=now,
    )
    scheduled_audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=scheduled_event.event_id,
            event_type=scheduled_event.event_type,
            ballot=stored,
            before_hash=before_hash,
            actor=actor,
            action="schedule",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return ApproveBallotConfigurationResult(
        ballot=stored,
        configuration_locked_event=locked_event,
        configuration_locked_audit_event=locked_audit_event,
        scheduled_event=scheduled_event,
        scheduled_audit_event=scheduled_audit_event,
    )


def add_ballot_option(
    ballot_store: BallotStore,
    option_store: BallotOptionStore,
    *,
    ballot_id: UUID,
    ballot_option_id: UUID,
    option_code: str,
    label: str,
    description: str,
    display_order: int,
    actor_is_authorized: bool,
) -> BallotOption:
    """Add one `BallotOption` while a ballot is still `draft` (canon 15.2
    names no event for this entity at all, and no command for it appears
    in canon section 20.10's list either - this is this service's own
    minimal, documented completion of "a `Ballot` needs `BallotOption`
    rows before its configuration can be frozen"). Per ADR-009 item 3:
    abstention is just another option row here (e.g. `option_code =
    "abstain"`) - there is no separate abstention path. Not audited: the
    same "not yet a committed, critical action" reasoning
    `epd2_eligibility_service.application.create_eligibility_rule` gives
    for skipping Audit Core while still pre-freeze."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to add a ballot option")

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")
    if ballot.status != BallotStatus.DRAFT:
        raise BallotConfigurationLockedError(
            f"ballot {ballot_id} configuration is frozen "
            f"(status {ballot.status.value!r}); no new options may be added"
        )

    option = BallotOption(
        ballot_option_id=ballot_option_id,
        ballot_id=ballot_id,
        option_code=option_code,
        label=label,
        description=description,
        display_order=display_order,
        status=BallotOptionStatus.ACTIVE,
    )
    return option_store.add(option)


def open_ballot(
    ballot_store: BallotStore,
    option_store: BallotOptionStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> OpenBallotResult:
    """`scheduled -> open`; locks every `BallotOption` for this ballot in
    the same call (canon 15.2: "После открытия Ballot варианты
    блокируются")."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to open a ballot")

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")

    now = clock.now()
    before_hash = compute_payload_hash(ballot_full_state_payload(ballot))
    updated = ballot.with_status(BallotStatus.OPEN)
    stored = ballot_store.save(updated)

    locked_options = []
    for option in option_store.list_for_ballot(ballot_id):
        if option.status == BallotOptionStatus.ACTIVE:
            locked_options.append(option_store.save(option.with_status(BallotOptionStatus.LOCKED)))
        else:
            locked_options.append(option)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_ballot_opened_event(
        event_id=resolved_event_id,
        ballot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            ballot=stored,
            before_hash=before_hash,
            actor=actor,
            action="open",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return OpenBallotResult(
        ballot=stored, locked_options=tuple(locked_options), event=event, audit_event=audit_event
    )


def _simple_ballot_transition(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    target_status: BallotStatus,
    action: str,
    build_event: Any,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None,
) -> BallotResult:
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} a ballot")

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")

    now = clock.now()
    before_hash = compute_payload_hash(ballot_full_state_payload(ballot))
    updated = ballot.with_status(target_status)
    stored = ballot_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_event(
        event_id=resolved_event_id,
        ballot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _ballot_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            ballot=stored,
            before_hash=before_hash,
            actor=actor,
            action=action,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return BallotResult(ballot=stored, event=event, audit_event=audit_event)


def pause_ballot(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """`open -> paused`."""
    return _simple_ballot_transition(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        target_status=BallotStatus.PAUSED,
        action="pause",
        build_event=build_ballot_paused_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def resume_ballot(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """`paused -> open`."""
    return _simple_ballot_transition(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        target_status=BallotStatus.OPEN,
        action="resume",
        build_event=build_ballot_resumed_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def close_ballot(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """`open -> closed`."""
    return _simple_ballot_transition(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        target_status=BallotStatus.CLOSED,
        action="close",
        build_event=build_ballot_closed_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def cancel_ballot(
    ballot_store: BallotStore,
    audit_store: AuditEventStore,
    *,
    ballot_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BallotResult:
    """`draft|configuration_review|scheduled -> cancelled`. Per ADR-009
    item 14 (amended), cancellation is a normal, always-available
    withdrawal path with no special authorization concern - unlike
    invalidation, which this service structurally cannot reach at all
    (see README.md)."""
    return _simple_ballot_transition(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        target_status=BallotStatus.CANCELLED,
        action="cancel",
        build_event=build_ballot_cancelled_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def cast_vote(
    ballot_store: BallotStore,
    envelope_store: VoteEnvelopeStore,
    audit_store: AuditEventStore,
    credential_store: Any,
    *,
    vote_envelope_id: UUID,
    ballot_id: UUID,
    credential_proof: UUID,
    encrypted_or_encoded_choice: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CastVoteResult:
    """Cast (or change) a vote. `credential_proof` must be the
    `credential_id` of an already-issued `ballot_access`
    `ParticipationCredential` - never an `account_id` (canon 15.3).

    Order of checks, all fail-closed:
    1. `actor_is_authorized`.
    2. `Ballot` exists and `status == open` (`BALLOT_NOT_OPEN`).
    3. `now < Ballot.closes_at`, else `BALLOT_ALREADY_CLOSED` - unless a
       `validated` envelope for this `(ballot_id, credential_proof)`
       already exists, in which case this is a genuine post-close
       resubmission attempt (`DUPLICATE_VOTE`) rather than a first,
       merely-late vote (ADR-009 items 1-2's own distinction).
    4. The presented credential validates via
       `validate_participation_credential` (ADR-008), scoped to this
       ballot and cross-checked against the exact
       `eligibility_rule_version`/`EligibilitySnapshot.digest` this
       ballot's own configuration was frozen against
       (`frozen_eligibility_snapshot_digest_for`) - an invalid credential
       raises `PermissionDeniedError` and no `VoteEnvelope` is ever
       persisted (validated *before* accepting the envelope, per spec).

    Vote-change/supersession (ADR-009 items 1-2): if a `validated`
    envelope already exists for this `(ballot_id, credential_proof)`, it
    is transitioned to `superseded` as part of this same call, and
    `vote.superseded` is emitted alongside `vote.received`.

    Idempotent (CT-00-04): a retry with the same `vote_envelope_id` and
    `event_id` (and, under a `FixedClock`, therefore identical computed
    `integrity_hash`) is a no-op at every layer - `VoteEnvelopeStore.create`
    detects identical content, `append_audit_event` detects the repeated
    `audit_event_id`, and supersession itself does not double-fire
    because by the time of a retry the previously-`validated` envelope is
    already `superseded` (so `find_validated_for_credential` no longer
    finds it)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to cast a vote")

    ballot = ballot_store.get(ballot_id)
    if ballot is None:
        raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")
    if ballot.status != BallotStatus.OPEN:
        raise BallotNotOpenError(f"ballot {ballot_id} is not open (status {ballot.status.value!r})")

    now = clock.now()
    existing_validated = envelope_store.find_validated_for_credential(ballot_id, credential_proof)
    if now >= ballot.closes_at:
        if existing_validated is not None:
            raise DuplicateVoteError(
                f"credential already has a validated vote on ballot {ballot_id}; "
                "resubmission after closes_at is rejected"
            )
        raise BallotAlreadyClosedError(
            f"ballot {ballot_id} closed at {ballot.closes_at.isoformat()}"
        )

    expected_digest = ballot_store.frozen_eligibility_snapshot_digest_for(ballot_id)
    validation = validate_participation_credential(
        credential_store,
        credential_id=credential_proof,
        required_scope_type="ballot",
        required_scope_id=ballot_id,
        expected_rule_version=ballot.eligibility_rule_version,
        expected_digest=expected_digest,
        actor=actor,
        correlation_id=correlation_id,
        clock=clock,
    ).result
    if not validation.valid:
        raise PermissionDeniedError(
            f"credential {credential_proof} is not valid for ballot {ballot_id}: "
            f"{validation.reason_codes}"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    integrity_hash = compute_vote_envelope_integrity_hash(
        ballot_id=ballot_id,
        credential_proof=credential_proof,
        encrypted_or_encoded_choice=encrypted_or_encoded_choice,
        submitted_at=now,
    )
    new_envelope = VoteEnvelope(
        vote_envelope_id=vote_envelope_id,
        ballot_id=ballot_id,
        credential_proof=credential_proof,
        encrypted_or_encoded_choice=encrypted_or_encoded_choice,
        submitted_at=now,
        integrity_hash=integrity_hash,
        validation_status=VoteEnvelopeStatus.RECEIVED,
        included_in_tally=False,
    )
    stored_envelope = envelope_store.create(new_envelope)

    superseded_envelope = None
    superseded_event = None
    superseded_audit_event = None
    if existing_validated is not None:
        before_hash = compute_payload_hash(vote_envelope_full_state_payload(existing_validated))
        superseded_envelope = existing_validated.with_status(VoteEnvelopeStatus.SUPERSEDED)
        envelope_store.save(superseded_envelope)
        superseded_event = build_vote_superseded_event(
            event_id=generate_uuid(),
            envelope=superseded_envelope,
            superseded_by=stored_envelope.vote_envelope_id,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=now,
        )
        superseded_audit_event = append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=superseded_event.event_id,
                event_type=superseded_event.event_type,
                occurred_at=now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="vote_envelope",
                target_id=superseded_envelope.vote_envelope_id,
                action="supersede",
                reason_code="VOTE_SUPERSEDED",
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=before_hash,
                after_hash=compute_payload_hash(
                    vote_envelope_full_state_payload(superseded_envelope)
                ),
            ),
            clock=clock,
        )

    event = build_vote_received_event(
        event_id=resolved_event_id,
        envelope=stored_envelope,
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
            target_type="vote_envelope",
            target_id=stored_envelope.vote_envelope_id,
            action="cast",
            reason_code="VOTE_RECEIVED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(vote_envelope_full_state_payload(stored_envelope)),
        ),
        clock=clock,
    )
    return CastVoteResult(
        envelope=stored_envelope,
        event=event,
        audit_event=audit_event,
        superseded_envelope=superseded_envelope,
        superseded_event=superseded_event,
        superseded_audit_event=superseded_audit_event,
    )


def validate_vote(
    envelope_store: VoteEnvelopeStore,
    audit_store: AuditEventStore,
    *,
    vote_envelope_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ValidateVoteResult:
    """`received -> validated` or `received -> rejected`, based on
    recomputing `integrity_hash` from the envelope's own stored fields
    (a structural tamper-evidence check - full ballot-specific validation,
    e.g. decoding/checking `encrypted_or_encoded_choice` against
    `BallotOption` rows, is a future pack's concern the same way
    `epd2_eligibility_service.application._decide`'s own minimal policy
    documents its own scope limit)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to validate a vote")

    envelope = envelope_store.get(vote_envelope_id)
    if envelope is None:
        raise UnknownVoteEnvelopeError(f"unknown vote_envelope_id: {vote_envelope_id}")

    now = clock.now()
    before_hash = compute_payload_hash(vote_envelope_full_state_payload(envelope))
    expected_hash = compute_vote_envelope_integrity_hash(
        ballot_id=envelope.ballot_id,
        credential_proof=envelope.credential_proof,
        encrypted_or_encoded_choice=envelope.encrypted_or_encoded_choice,
        submitted_at=envelope.submitted_at,
    )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    if expected_hash != envelope.integrity_hash:
        updated = envelope.with_status(VoteEnvelopeStatus.REJECTED)
        stored = envelope_store.save(updated)
        event = build_vote_rejected_event(
            event_id=resolved_event_id,
            envelope=stored,
            reason_codes=("VOTE_INTEGRITY_HASH_MISMATCH",),
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=now,
        )
        reason_code = "VOTE_REJECTED"
    else:
        updated = envelope.with_status(VoteEnvelopeStatus.VALIDATED)
        stored = envelope_store.save(updated)
        event = build_vote_validated_event(
            event_id=resolved_event_id,
            envelope=stored,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=now,
        )
        reason_code = "VOTE_VALIDATED"

    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="vote_envelope",
            target_id=stored.vote_envelope_id,
            action="validate",
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(vote_envelope_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return ValidateVoteResult(envelope=stored, event=event, audit_event=audit_event)


def issue_vote_receipt(
    envelope_store: VoteEnvelopeStore,
    receipt_store: VoteReceiptStore,
    audit_store: AuditEventStore,
    *,
    receipt_id: UUID,
    vote_envelope_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> IssueReceiptResult:
    """Issue a `VoteReceipt` for an already-`validated`/`included`
    `VoteEnvelope`. Canon names no domain event for receipt issuance
    (section 20.10 does not list one) - persist+audit only, same "no
    event" shape as `submit_ballot_for_configuration_review`.
    `receipt_hash` is built only from `vote_envelope_id`/`integrity_hash`
    (`compute_vote_receipt_hash`) - never from
    `encrypted_or_encoded_choice` - so the receipt cannot reveal the
    chosen option (canon 15.4)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to issue a vote receipt")

    envelope = envelope_store.get(vote_envelope_id)
    if envelope is None:
        raise UnknownVoteEnvelopeError(f"unknown vote_envelope_id: {vote_envelope_id}")
    receipt_eligible = (VoteEnvelopeStatus.VALIDATED, VoteEnvelopeStatus.INCLUDED)
    if envelope.validation_status not in receipt_eligible:
        raise VoteEnvelopeNotReceiptEligibleError(
            f"vote_envelope {vote_envelope_id} is not eligible for a receipt "
            f"(status {envelope.validation_status.value!r})"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    receipt_hash = compute_vote_receipt_hash(
        vote_envelope_id=envelope.vote_envelope_id, integrity_hash=envelope.integrity_hash
    )
    receipt = VoteReceipt(
        receipt_id=receipt_id,
        ballot_id=envelope.ballot_id,
        vote_envelope_reference=envelope.vote_envelope_id,
        receipt_hash=receipt_hash,
        issued_at=now,
        verification_status=VoteReceiptVerificationStatus.ISSUED,
    )
    stored = receipt_store.save(receipt)

    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="vote_receipt.issued",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="vote_receipt",
            target_id=stored.receipt_id,
            action="issue",
            reason_code="RECEIPT_ISSUED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(
                {
                    "receipt_id": str(stored.receipt_id),
                    "ballot_id": str(stored.ballot_id),
                    "vote_envelope_reference": str(stored.vote_envelope_reference),
                    "receipt_hash": stored.receipt_hash,
                    "verification_status": stored.verification_status.value,
                }
            ),
        ),
        clock=clock,
    )
    return IssueReceiptResult(receipt=stored, audit_event=audit_event)
