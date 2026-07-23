"""Tally Service application layer: `start_tally`, `complete_tally`,
`verify_tally`, `publish_result` - the tally/result subset of canon events
section 20.10, verbatim (`tally.started`, `tally.completed`,
`tally.verified`, `result.published`).

Every command follows the same idempotency shape (CT-00-04): a caller
retrying an exact command should pass the same `event_id` it used on the
original attempt (alongside the same other arguments), so both the stored
entity and the audit trail converge on the same single record rather than
duplicating on retry.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_tally_service.domain import (
    QuorumResult,
    ResultPublication,
    Tally,
    TallyVerificationStatus,
    ThresholdResult,
    compute_challenge_deadline,
    compute_quorum_result,
    compute_threshold_result,
)
from epd2_tally_service.events import (
    build_result_published_event,
    build_tally_completed_event,
    build_tally_started_event,
    build_tally_verified_event,
    result_publication_state_payload,
    tally_full_state_payload,
)
from epd2_tally_service.exceptions import ForbiddenTallyTransitionError, UnknownTallyError
from epd2_tally_service.storage import ResultPublicationStore, TallyStore

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "tally-service"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


def _publish_result_reason_code(
    *, quorum_result: QuorumResult, threshold_result: ThresholdResult
) -> str:
    """Additive, info-severity audit classification code for a successful
    `publish_result` call (ADR-009 items 5/11's outcomes are always a
    legitimate, non-error `ResultPublication` - never an exception - but
    the audit trail should still say *which* of these two noteworthy,
    documented outcomes occurred, rather than a single generic
    "published" code for every case).

    Priority: a tied result (`TIE_NO_DECISION`, ADR-009 item 11) is the
    more specific/rarer condition, checked first; then a missed-quorum
    result (`QUORUM_NOT_MET`, ADR-009 item 5); otherwise the plain
    `RESULT_PUBLISHED` classification applies. Neither
    `TALLY_QUORUM_NOT_MET` nor `TALLY_THRESHOLD_TIE_NO_DECISION` is an
    error reason code - `publish_result` never raises for either
    condition; both are simply classified outcomes.
    """
    if threshold_result == ThresholdResult.TIE_NO_DECISION:
        return "TALLY_THRESHOLD_TIE_NO_DECISION"
    if quorum_result == QuorumResult.QUORUM_NOT_MET:
        return "TALLY_QUORUM_NOT_MET"
    return "RESULT_PUBLISHED"


@dataclass(frozen=True, slots=True)
class StartTallyResult:
    tally: Tally
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CompleteTallyResult:
    tally: Tally
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class VerifyTallyResult:
    tally: Tally
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PublishResultResult:
    result: ResultPublication
    event: EventEnvelope
    audit_event: AuditEvent


def start_tally(
    store: TallyStore,
    audit_store: AuditEventStore,
    *,
    tally_id: UUID,
    ballot_id: UUID,
    input_set_hash: str,
    algorithm_version: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> StartTallyResult:
    """Create a new `Tally` in `pending`, then immediately transition it
    `pending -> running`, emitting `tally.started`. `input_set_hash` and
    `algorithm_version` are caller-supplied - the caller (whatever wires
    `voting-service` and `tally-service` together) is responsible for
    having already validated the vote set this tally covers; this
    function never imports `epd2_voting_service` (see README.md)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to start a tally")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    pending = Tally(
        tally_id=tally_id,
        ballot_id=ballot_id,
        input_set_hash=input_set_hash,
        algorithm_version=algorithm_version,
        started_at=now,
        completed_at=None,
        result_data={},
        invalid_vote_count=0,
        tally_signature=None,
        verification_status=TallyVerificationStatus.PENDING,
    )
    running = pending.with_status(TallyVerificationStatus.RUNNING)
    stored = store.create(running)

    event = build_tally_started_event(
        event_id=resolved_event_id,
        tally=stored,
        actor=actor,
        correlation_id=correlation_id,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: starting a tally is a critical, politically
    # significant action and must leave an audit trail.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="tally",
            target_id=stored.tally_id,
            action="start",
            reason_code="TALLY_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(tally_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return StartTallyResult(tally=stored, event=event, audit_event=audit_event)


def complete_tally(
    store: TallyStore,
    audit_store: AuditEventStore,
    *,
    tally_id: UUID,
    result_data: Mapping[str, int],
    invalid_vote_count: int,
    tally_signature: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CompleteTallyResult:
    """`running -> completed`, recording the caller-computed
    `result_data`/`invalid_vote_count`/`tally_signature`, emitting
    `tally.completed`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to complete a tally")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    tally = store.get(tally_id)
    if tally is None:
        raise UnknownTallyError(f"unknown tally_id: {tally_id}")
    now = clock.now()

    if tally.verification_status == TallyVerificationStatus.COMPLETED:
        # Idempotent replay (CT-00-04): `running -> completed` cannot be
        # re-run, so a retry is only legitimate if it would have produced
        # exactly the same recorded content; anything else is a genuine
        # conflict, not a retry.
        if not (
            dict(tally.result_data) == dict(result_data)
            and tally.invalid_vote_count == invalid_vote_count
            and tally.tally_signature == tally_signature
        ):
            raise ForbiddenTallyTransitionError(
                f"tally {tally_id} is already completed with different content"
            )
        updated = tally
        occurred_at = tally.completed_at if tally.completed_at is not None else now
        before_hash = compute_payload_hash(tally_full_state_payload(tally))
    else:
        before_hash = compute_payload_hash(tally_full_state_payload(tally))
        updated = tally.with_completion(
            completed_at=now,
            result_data=result_data,
            invalid_vote_count=invalid_vote_count,
            tally_signature=tally_signature,
        )
        store.save(updated)
        occurred_at = now

    event = build_tally_completed_event(
        event_id=resolved_event_id,
        tally=updated,
        actor=actor,
        correlation_id=correlation_id,
        occurred_at=occurred_at,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=occurred_at,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="tally",
            target_id=updated.tally_id,
            action="complete",
            reason_code="TALLY_STATUS_CHANGED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(tally_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return CompleteTallyResult(tally=updated, event=event, audit_event=audit_event)


def verify_tally(
    store: TallyStore,
    audit_store: AuditEventStore,
    *,
    tally_id: UUID,
    verification_passed: bool,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> VerifyTallyResult:
    """`completed -> verified` (on success) or `completed ->
    verification_failed` (on failure). `tally.verified` is emitted only
    on success - canon events section 20.10 names no event for a failed
    verification, so a failure is persisted and audited
    (`INTEGRITY_CHECK_FAILED`, canon section 24) only, with no domain
    event returned (`VerifyTallyResult.event` is `None`)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to verify a tally")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    tally = store.get(tally_id)
    if tally is None:
        raise UnknownTallyError(f"unknown tally_id: {tally_id}")
    now = clock.now()

    target = (
        TallyVerificationStatus.VERIFIED
        if verification_passed
        else TallyVerificationStatus.VERIFICATION_FAILED
    )
    reason_code = "TALLY_STATUS_CHANGED" if verification_passed else "INTEGRITY_CHECK_FAILED"
    action = "verify" if verification_passed else "verify_failed"

    before_hash = compute_payload_hash(tally_full_state_payload(tally))
    if tally.verification_status == target:
        # Idempotent replay (CT-00-04): already at the target status.
        updated = tally
    else:
        updated = tally.with_status(target)
        store.save(updated)

    event: EventEnvelope | None
    if verification_passed:
        event = build_tally_verified_event(
            event_id=resolved_event_id,
            tally=updated,
            actor=actor,
            correlation_id=correlation_id,
            occurred_at=now,
        )
        audit_event_type = event.event_type
    else:
        event = None
        # `tally.verification_failed` is not a canon event name (canon
        # events section 20.10 has none for this transition) - this is
        # only the audit record's own descriptive `event_type` field.
        audit_event_type = "tally.verification_failed"

    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=audit_event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="tally",
            target_id=updated.tally_id,
            action=action,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(tally_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return VerifyTallyResult(tally=updated, event=event, audit_event=audit_event)


def publish_result(
    tally_store: TallyStore,
    result_store: ResultPublicationStore,
    audit_store: AuditEventStore,
    *,
    result_publication_id: UUID,
    ballot_id: UUID,
    tally_id: UUID,
    eligible_count: int,
    credential_count: int,
    accepted_vote_count: int,
    rejected_vote_count: int,
    quorum_threshold: int | None,
    option_counts: Mapping[str, int],
    challenge_window_hours: int | None,
    audit_package_reference: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> PublishResultResult:
    """Create a `ResultPublication` from a `verified` `Tally`, emitting
    `result.published`.

    `quorum_threshold` and `option_counts` are plain caller-supplied
    parameters - see `domain.compute_quorum_result`/
    `domain.compute_threshold_result` for exactly how `quorum_result`/
    `threshold_result` are derived from them. `challenge_window_hours` is
    the real `Ballot.challenge_window_hours` (or `None`), read and passed
    in by the caller per ADR-010/ADR-008 item 3 - this function never
    reads a `Ballot` itself.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to publish a result")

    resolved_event_id = event_id if event_id is not None else generate_uuid()

    tally = tally_store.get(tally_id)
    if tally is None:
        raise UnknownTallyError(f"unknown tally_id: {tally_id}")
    if tally.ballot_id != ballot_id:
        raise ValueError(f"tally {tally_id} belongs to ballot {tally.ballot_id}, not {ballot_id}")
    if tally.verification_status != TallyVerificationStatus.VERIFIED:
        raise ForbiddenTallyTransitionError(
            f"cannot publish a result for tally {tally_id}: verification_status is "
            f"{tally.verification_status.value!r}, not 'verified'"
        )

    quorum_result = compute_quorum_result(
        accepted_vote_count=accepted_vote_count, quorum_threshold=quorum_threshold
    )
    threshold_result = compute_threshold_result(option_counts)

    now = clock.now()
    challenge_deadline_at = compute_challenge_deadline(now, challenge_window_hours)

    result = ResultPublication(
        result_publication_id=result_publication_id,
        ballot_id=ballot_id,
        tally_id=tally_id,
        eligible_count=eligible_count,
        credential_count=credential_count,
        accepted_vote_count=accepted_vote_count,
        rejected_vote_count=rejected_vote_count,
        quorum_result=quorum_result,
        threshold_result=threshold_result,
        published_at=now,
        audit_package_reference=audit_package_reference,
        challenge_deadline_at=challenge_deadline_at,
    )
    stored = result_store.create(result)

    event = build_result_published_event(
        event_id=resolved_event_id,
        result=stored,
        actor=actor,
        correlation_id=correlation_id,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: publishing a result is a critical, politically
    # significant action and must leave an audit trail. Per ADR-009 item
    # 15, `result_publication_state_payload` only ever carries aggregate
    # counts and administrative fields - never individual vote contents,
    # which this service has no access to in the first place.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="result_publication",
            target_id=stored.result_publication_id,
            action="publish",
            reason_code=_publish_result_reason_code(
                quorum_result=quorum_result, threshold_result=threshold_result
            ),
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(result_publication_state_payload(stored)),
        ),
        clock=clock,
    )
    return PublishResultResult(result=stored, event=event, audit_event=audit_event)
