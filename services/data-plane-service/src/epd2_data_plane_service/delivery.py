"""Event delivery semantics, ordering, dead-letter and replay
(PACK-13 §9, §10; ADR-072).

**The delivery guarantee is at-least-once.** The consumer effect is
effectively-once, achieved by consumer idempotency. The stronger phrase
is claimed nowhere in this module, and the distinction is not pedantry: a
system that believes it has the stronger guarantee stops writing
idempotent consumers, and then the first redelivery, months later,
double-posts a financial entry.

Every situation §9.1 says must be specified rather than discovered has a
type and a reason code here: duplicate delivery, delayed delivery,
out-of-order delivery, missing acknowledgement, bounded retry,
dead-lettering, replay, consumer checkpoints, poison events,
compatibility failure and ordering gaps.

Ordering (§10) is **scoped, never global**. Every event carries an
explicit sequence number within its declared ordering scope; timestamps
are metadata, not order (`P13-ORD-008`), so clock skew cannot disturb
ordering semantics (`P13-ORD-009`). There is deliberately no function in
this module that orders events by time.

**No real broker is implemented.** `ReferenceDispatcher` is an in-process
simulation whose purpose is to make the semantics testable, and
`BrokerPort` is the seam a production adapter would implement.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    ClassificationReference,
    EvidenceReference,
    OrganizationScopeReference,
    PrivilegedGrantReference,
    RetentionScheduleReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    BrokerUnavailableError,
    DeliveryAcknowledgementMissingError,
    EventDeadLetterRequiredError,
    EventOrderingGapDetectedError,
    EventOutOfOrderError,
    EventPoisonMessageError,
    EventReplayNotAuthorizedError,
    EventVersionUnsupportedError,
)
from epd2_data_plane_service.idempotency import DeduplicationRecord
from epd2_data_plane_service.outbox import (
    BrokerAcknowledgementReference,
    DeliveryAttempt,
    DeliveryOutcome,
    DestinationReference,
    OutboxRecord,
    OutboxStatus,
    PublicationEvidence,
)

# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


class OrderingScopeKind(StrEnum):
    """The admissible ordering scopes (`P13-ORD-002`).

    Global total ordering is **not** among them and is not promised
    (`P13-ORD-001`). A scope is declared per event family, never
    assumed."""

    PER_AGGREGATE = "per_aggregate"
    PER_STREAM = "per_stream"
    PER_ORGANIZATION_AND_AGGREGATE = "per_organization_and_aggregate"


@dataclass(frozen=True, slots=True)
class OrderingScope:
    """One declared ordering scope instance."""

    kind: OrderingScopeKind
    aggregate_id: UUID | None = None
    stream_name: str | None = None
    organization_scope: OrganizationScopeReference | None = None

    def __post_init__(self) -> None:
        if self.kind is OrderingScopeKind.PER_AGGREGATE and self.aggregate_id is None:
            raise ValueError("a per-aggregate ordering scope names its aggregate")
        if self.kind is OrderingScopeKind.PER_STREAM and not self.stream_name:
            raise ValueError("a per-stream ordering scope names its stream")
        if self.kind is OrderingScopeKind.PER_ORGANIZATION_AND_AGGREGATE and (
            self.aggregate_id is None or self.organization_scope is None
        ):
            raise ValueError(
                "a per-organization-and-aggregate ordering scope names both, because "
                "dropping either widens the scope silently"
            )

    @property
    def key(self) -> str:
        organization = (
            "" if self.organization_scope is None else str(self.organization_scope.organization_id)
        )
        return f"{self.kind.value}:{organization}:{self.aggregate_id}:{self.stream_name}"


class OrderingDecision(StrEnum):
    IN_ORDER = "in_order"
    DUPLICATE = "duplicate"
    GAP_DETECTED = "gap_detected"
    OUT_OF_ORDER = "out_of_order"


@dataclass(frozen=True, slots=True)
class OrderingAssessment:
    """What the consumer observed about sequence."""

    decision: OrderingDecision
    expected_sequence: int
    observed_sequence: int
    reason_code: str | None = None


def assess_ordering(*, checkpoint_position: int, observed_sequence: int) -> OrderingAssessment:
    """Compare an observed sequence against the consumer's checkpoint.

    Sequence, never timestamp (`P13-ORD-008`). The three non-happy
    outcomes are distinguished rather than collapsed into "unexpected",
    because a duplicate, a gap and a late arrival call for three
    different operator responses."""
    expected = checkpoint_position + 1
    if observed_sequence == expected:
        return OrderingAssessment(
            decision=OrderingDecision.IN_ORDER,
            expected_sequence=expected,
            observed_sequence=observed_sequence,
        )
    if observed_sequence <= checkpoint_position:
        return OrderingAssessment(
            decision=OrderingDecision.OUT_OF_ORDER,
            expected_sequence=expected,
            observed_sequence=observed_sequence,
            reason_code="EVENT_OUT_OF_ORDER",
        )
    return OrderingAssessment(
        decision=OrderingDecision.GAP_DETECTED,
        expected_sequence=expected,
        observed_sequence=observed_sequence,
        reason_code="EVENT_ORDERING_GAP_DETECTED",
    )


def require_in_order(assessment: OrderingAssessment, *, consumer_name: str) -> None:
    """Raise the registered refusal for a gap or a late arrival.

    Neither is applied silently as if in order (`P13-DEL-006`,
    `P13-ORD-005`); a gap is a governed fact that raises an event
    (`P13-ORD-006`), which the application layer does after catching
    this."""
    if assessment.decision is OrderingDecision.GAP_DETECTED:
        raise EventOrderingGapDetectedError(
            f"consumer {consumer_name!r}: expected sequence "
            f"{assessment.expected_sequence}, observed {assessment.observed_sequence}; the "
            f"gap is a governed fact, not a silent absence"
        )
    if assessment.decision is OrderingDecision.OUT_OF_ORDER:
        raise EventOutOfOrderError(
            f"consumer {consumer_name!r}: observed sequence {assessment.observed_sequence} is "
            f"at or behind the checkpoint position "
            f"{assessment.expected_sequence - 1}"
        )


# ---------------------------------------------------------------------------
# Consumer checkpoints
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConsumerCheckpoint:
    """What a consumer has durably processed (`P13-DEL-011`).

    Advancing it is a governed act; moving it **backwards** is a
    distinct, authorized operation, which is why `rewind_to` demands a
    privileged grant and `advance_to` does not."""

    consumer_name: str
    consumer_domain: str
    ordering_scope_key: str
    position: int
    updated_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.updated_at, field="ConsumerCheckpoint.updated_at")
        if self.position < 0:
            raise ValueError("a checkpoint position must not be negative")

    def advance_to(self, position: int, *, now: datetime) -> ConsumerCheckpoint:
        if position <= self.position:
            raise EventOutOfOrderError(
                f"consumer {self.consumer_name!r}: advancing a checkpoint from "
                f"{self.position} to {position} is not an advance; moving it backwards is a "
                f"distinct, authorized operation"
            )
        return replace(self, position=position, updated_at=require_timezone(now, field="now"))

    def rewind_to(
        self, position: int, *, grant: PrivilegedGrantReference, now: datetime
    ) -> ConsumerCheckpoint:
        """Move the checkpoint backwards under an explicit grant.

        Separated from `advance_to` because the two are different acts
        with different risk: a rewind replays already-processed events,
        which is safe only because consumers are idempotent, and is
        authorized rather than assumed."""
        if position >= self.position:
            raise ValueError("a rewind moves the checkpoint backwards")
        if grant.operation != "consumer_checkpoint_rewind":
            raise EventReplayNotAuthorizedError(
                f"the presented grant authorizes {grant.operation!r}, not a consumer "
                f"checkpoint rewind"
            )
        return replace(self, position=position, updated_at=require_timezone(now, field="now"))


# ---------------------------------------------------------------------------
# Dead letter and replay
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DeadLetterRecord:
    """A dead-lettered event, preserved with its failure context
    (`P13-DEL-009`).

    A dead-letter store is not a dumping ground: it has retention, access
    control and a review obligation, and it **may contain personal
    data**, so it carries a classification and is excluded from general
    operator visibility (`P13-DEL-014`). The record therefore holds a
    *reference* to the failed event rather than its payload
    (`P13-EVT-007`)."""

    dead_letter_id: UUID
    event_id: UUID
    event_type: str
    reason_code: str
    attempt_count: int
    failed_at: datetime
    classification: ClassificationReference
    retention_schedule: RetentionScheduleReference
    review_required: bool = True
    failure_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.failed_at, field="DeadLetterRecord.failed_at")
        if not self.review_required:
            raise ValueError(
                "a dead-letter store carries a review obligation; a record marked as needing "
                "no review is a dumping ground with a schema (P13-DEL-009)"
            )


@dataclass(frozen=True, slots=True)
class ReplayReference:
    """An explicit, authorized, scoped and evidenced replay
    (`P13-DEL-010`).

    It never rewrites history and never mints new logical event IDs for
    events that already existed — there is no field here that could carry
    a replacement event ID."""

    replay_id: UUID
    requested_by: ActorReference
    grant: PrivilegedGrantReference
    ordering_scope_key: str
    from_sequence: int
    to_sequence: int
    requested_at: datetime
    evidence: EvidenceReference
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, field="ReplayReference.requested_at")
        if self.from_sequence < 1 or self.to_sequence < self.from_sequence:
            raise ValueError("a replay range is a non-empty, ascending sequence range")
        if self.grant.operation != "event_replay":
            raise EventReplayNotAuthorizedError(
                f"the presented grant authorizes {self.grant.operation!r}, not an event replay"
            )


def replay_preserves_history(
    original: Sequence[OutboxRecord], replayed: Sequence[OutboxRecord]
) -> bool:
    """Whether a replay preserved the historical event sequence
    (`P13-ORD-007`) and the logical event IDs (`P13-DEL-010`).

    Returns a bool so both a test and an operator surface can use it. The
    check is by identity and sequence, not by payload equality: a payload
    comparison would pass for a replay that renumbered everything."""
    if len(original) != len(replayed):
        return False
    for before, after in zip(original, replayed, strict=True):
        if before.event_id != after.event_id:
            return False
        if before.sequence_number != after.sequence_number:
            return False
    return True


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded, backed-off retry terminating in dead-lettering
    (`P13-DEL-008`).

    Unbounded retry is not expressible: `max_attempts` has no sentinel
    for "forever"."""

    max_attempts: int
    initial_backoff: timedelta
    backoff_multiplier: int = 2

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts is at least 1 and has no unbounded value")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier is at least 1")

    def next_attempt_at(self, *, attempt_number: int, now: datetime) -> datetime:
        require_timezone(now, field="now")
        factor = int(self.backoff_multiplier ** max(attempt_number - 1, 0))
        return now + self.initial_backoff * factor


class DispatchAction(StrEnum):
    DISPATCH_NOW = "dispatch_now"
    DEFER = "defer"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True, slots=True)
class DispatchDecision:
    """Whether to dispatch now, defer, or dead-letter, with a reason code
    (§8.1)."""

    action: DispatchAction
    reason_code: str | None = None
    next_attempt_at: datetime | None = None


def decide_dispatch(
    record: OutboxRecord,
    *,
    policy: RetryPolicy,
    now: datetime,
    broker_available: bool,
    deterministic_failure_observed: bool = False,
) -> DispatchDecision:
    """Decide what the dispatcher should do with one record.

    The dispatcher **changes no domain semantics** (`P13-OBX-009`): this
    function reads status, attempt count and broker availability, and
    nothing about the event's content. It cannot filter on a business
    rule, because it is never given one."""
    require_timezone(now, field="now")
    if deterministic_failure_observed:
        # A poison event is detected as such rather than retried forever
        # (`P13-DEL-012`).
        return DispatchDecision(
            action=DispatchAction.DEAD_LETTER, reason_code="EVENT_POISON_MESSAGE"
        )
    if record.attempt_count >= policy.max_attempts:
        return DispatchDecision(
            action=DispatchAction.DEAD_LETTER, reason_code="EVENT_DEAD_LETTER_REQUIRED"
        )
    if not broker_available:
        # Commands still commit; the backlog grows; publication is
        # pending, not lost (§29).
        return DispatchDecision(
            action=DispatchAction.DEFER,
            reason_code="BROKER_UNAVAILABLE",
            next_attempt_at=policy.next_attempt_at(
                attempt_number=record.attempt_count + 1, now=now
            ),
        )
    return DispatchDecision(action=DispatchAction.DISPATCH_NOW)


class BrokerPort(Protocol):
    """The seam a production broker adapter would implement.

    A `Protocol`, not a class: PACK-13 prescribes no transport provider,
    no topic naming and no broker topology, for the general plane or the
    voting plane (`P13-VOTE-008`)."""

    def publish(
        self, record: OutboxRecord, destination: DestinationReference
    ) -> BrokerAcknowledgementReference | None:
        """Publish, returning the broker's acknowledgement reference or
        `None` when the acknowledgement is unknown."""
        ...


class ReferenceBroker:
    """An in-process, deterministic broker double.

    Not a broker. It records what it was asked to publish and returns
    whatever outcome the test configured, so the delivery semantics can
    be exercised without a network."""

    def __init__(
        self,
        *,
        available: bool = True,
        acknowledge: bool = True,
        acknowledgement_prefix: str = "ack",
    ) -> None:
        self.available = available
        self.acknowledge = acknowledge
        self._prefix = acknowledgement_prefix
        self.published: list[UUID] = []

    def publish(
        self, record: OutboxRecord, destination: DestinationReference
    ) -> BrokerAcknowledgementReference | None:
        if not self.available:
            raise BrokerUnavailableError(
                f"broker {destination.destination_name!r} could not be reached; the command "
                f"has committed and publication is pending, not lost"
            )
        self.published.append(record.event_id)
        if not self.acknowledge:
            return None
        return BrokerAcknowledgementReference(
            acknowledgement_reference=f"{self._prefix}-{record.event_id}",
            received_at=record.created_at,
        )


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """What one dispatch attempt produced."""

    record: OutboxRecord
    decision: DispatchDecision
    dead_letter: DeadLetterRecord | None = None


class ReferenceDispatcher:
    """The reference dispatcher.

    Reads the outbox, publishes, records the outcome. It does not enrich,
    transform, filter on business rules, or decide whether an event
    "should" be sent (`P13-OBX-009`) — and the way that is guaranteed is
    that it is never given the means: it receives a record and a broker
    port, and has no access to any domain policy.
    """

    def __init__(
        self,
        broker: BrokerPort,
        *,
        destination: DestinationReference,
        policy: RetryPolicy,
    ) -> None:
        self._broker = broker
        self._destination = destination
        self._policy = policy

    def dispatch(
        self,
        record: OutboxRecord,
        *,
        now: datetime,
        broker_available: bool = True,
        deterministic_failure: bool = False,
        classification: ClassificationReference | None = None,
        retention_schedule: RetentionScheduleReference | None = None,
        dead_letter_id: UUID | None = None,
    ) -> DispatchResult:
        """Attempt one dispatch of `record`.

        The logical event ID is never regenerated: every branch either
        returns the same record or a copy of it, and there is no code
        path here that constructs a new envelope."""
        require_timezone(now, field="now")
        decision = decide_dispatch(
            record,
            policy=self._policy,
            now=now,
            broker_available=broker_available,
            deterministic_failure_observed=deterministic_failure,
        )
        if decision.action is DispatchAction.DEFER:
            return DispatchResult(record=record, decision=decision)
        if decision.action is DispatchAction.DEAD_LETTER:
            if classification is None or retention_schedule is None or dead_letter_id is None:
                raise EventDeadLetterRequiredError(
                    f"event {record.event_id} must be dead-lettered, and a dead-letter record "
                    f"requires a classification, a retention schedule and an identifier; a "
                    f"dead-letter store without those is a dumping ground"
                )
            dead_letter = DeadLetterRecord(
                dead_letter_id=dead_letter_id,
                event_id=record.event_id,
                event_type=record.event_type,
                reason_code=decision.reason_code or "EVENT_DEAD_LETTER_REQUIRED",
                attempt_count=record.attempt_count,
                failed_at=now,
                classification=classification,
                retention_schedule=retention_schedule,
            )
            moved = record
            if moved.status is OutboxStatus.PENDING:
                moved = moved.with_status(OutboxStatus.DISPATCHING)
            moved = moved.with_status(OutboxStatus.DEAD_LETTERED)
            return DispatchResult(record=moved, decision=decision, dead_letter=dead_letter)

        dispatching = record.with_status(OutboxStatus.DISPATCHING)
        acknowledgement = self._broker.publish(dispatching, self._destination)
        outcome = (
            DeliveryOutcome.PUBLISHED
            if acknowledgement is not None
            else DeliveryOutcome.ACKNOWLEDGEMENT_UNKNOWN
        )
        attempted = dispatching.with_attempt(
            DeliveryAttempt(
                attempt_number=dispatching.attempt_count + 1,
                started_at=now,
                outcome=outcome,
                destination=self._destination,
            )
        )
        published = attempted.with_publication(
            PublicationEvidence(
                event_id=record.event_id,
                published_at=now,
                destination=self._destination,
                acknowledgement=acknowledgement,
            )
        ).with_status(OutboxStatus.PUBLISHED)
        if acknowledgement is not None:
            published = published.with_status(OutboxStatus.ACKNOWLEDGED)
        return DispatchResult(record=published, decision=decision)


def require_acknowledged(record: OutboxRecord) -> None:
    """Refuse to treat an unacknowledged publication as delivered.

    "We dispatched it" and "the broker acknowledged it" are different
    facts; this function is the place a caller is stopped from reading
    the first as the second (`P13-OBX-011`, `P13-DEL-007`)."""
    if not record.acknowledged:
        raise DeliveryAcknowledgementMissingError(
            f"event {record.event_id} was dispatched and its acknowledgement is unknown; the "
            f"record is in that state rather than marked delivered, and redelivery is safe "
            f"because consumers are idempotent"
        )


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------


class ConsumerEffect(StrEnum):
    APPLIED = "applied"
    SUPPRESSED_DUPLICATE = "suppressed_duplicate"
    DEAD_LETTERED = "dead_lettered"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class ConsumerResult:
    """What one consumption produced."""

    effect: ConsumerEffect
    reason_code: str | None = None
    checkpoint: ConsumerCheckpoint | None = None
    deduplication: DeduplicationRecord | None = None
    ordering: OrderingAssessment | None = None


class ReferenceConsumer:
    """An idempotent reference consumer (`P13-DEL-003`).

    Every consumer is idempotent; a consumer that cannot be made
    idempotent is a design defect, not a tolerated exception. This one
    deduplicates on the event ID **plus its own scope**
    (`P13-IDEM-009`), so the same event consumed by two consumers is two
    independent effects.

    A compatibility failure fails **closed** for a consequential consumer
    (`P13-DEL-013`): it does not guess, does not skip, and does not apply
    a partial interpretation.
    """

    def __init__(
        self,
        *,
        consumer_name: str,
        consumer_domain: str,
        supported_event_versions: frozenset[str],
        consequential: bool = True,
    ) -> None:
        self.consumer_name = consumer_name
        self.consumer_domain = consumer_domain
        self.supported_event_versions = supported_event_versions
        self.consequential = consequential
        self._seen: dict[str, DeduplicationRecord] = {}
        self.applied_event_ids: list[UUID] = []

    def consume(
        self,
        record: OutboxRecord,
        *,
        checkpoint: ConsumerCheckpoint,
        now: datetime,
    ) -> ConsumerResult:
        """Consume one delivered record.

        Order of checks: deduplication, then version support, then
        ordering. Deduplication comes first because a redelivery of an
        event this consumer already applied must be absorbed even if the
        consumer's supported-version set has since changed — otherwise a
        version narrowing would turn old, already-applied events into
        dead letters."""
        require_timezone(now, field="now")
        key = f"{self.consumer_domain}:{self.consumer_name}:{record.event_id}"
        existing = self._seen.get(key)
        if existing is not None:
            self._seen[key] = existing.observed_again()
            return ConsumerResult(
                effect=ConsumerEffect.SUPPRESSED_DUPLICATE,
                reason_code="EVENT_DUPLICATE_SUPPRESSED",
                checkpoint=checkpoint,
                deduplication=self._seen[key],
            )
        if record.event_version not in self.supported_event_versions:
            if self.consequential:
                raise EventVersionUnsupportedError(
                    f"consumer {self.consumer_name!r} supports "
                    f"{sorted(self.supported_event_versions)} and received "
                    f"{record.event_version!r}; a consequential consumer fails closed rather "
                    f"than applying a partial interpretation"
                )
            return ConsumerResult(
                effect=ConsumerEffect.DEAD_LETTERED, reason_code="EVENT_VERSION_UNSUPPORTED"
            )
        assessment = assess_ordering(
            checkpoint_position=checkpoint.position, observed_sequence=record.sequence_number
        )
        if assessment.decision is not OrderingDecision.IN_ORDER:
            return ConsumerResult(
                effect=ConsumerEffect.REFUSED,
                reason_code=assessment.reason_code,
                checkpoint=checkpoint,
                ordering=assessment,
            )
        self._seen[key] = DeduplicationRecord(
            consumer_name=self.consumer_name,
            consumer_domain=self.consumer_domain,
            event_id=record.event_id,
            first_seen_at=now,
        )
        self.applied_event_ids.append(record.event_id)
        return ConsumerResult(
            effect=ConsumerEffect.APPLIED,
            checkpoint=checkpoint.advance_to(record.sequence_number, now=now),
            deduplication=self._seen[key],
            ordering=assessment,
        )

    def detect_poison(self, record: OutboxRecord, *, failure_count: int, threshold: int) -> None:
        """Refuse to keep retrying a deterministically-failing event.

        Called by the application layer when a consumer has failed the
        same event the same way repeatedly. A poison event is routed to
        dead-letter with its own reason code rather than retried forever
        (`P13-DEL-012`)."""
        if failure_count >= threshold:
            raise EventPoisonMessageError(
                f"event {record.event_id} has failed deterministically {failure_count} times "
                f"at consumer {self.consumer_name!r}; it is routed to dead-letter rather "
                f"than retried indefinitely"
            )


@dataclass(frozen=True, slots=True)
class ConsumerLag:
    """Consumer lag, exposed rather than inferred (§29).

    Reported as a **band**, for the same reason PACK-12 reports
    suppression bands and `P13-EVT-009` reports lag bands: an exact
    figure across organizations is itself information."""

    consumer_name: str
    ordering_scope_key: str
    lag_band: str
    observed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="ConsumerLag.observed_at")


#: The lag bands. Bands, not exact figures.
LAG_BANDS: Mapping[str, tuple[int, int | None]] = {
    "none": (0, 0),
    "low": (1, 10),
    "moderate": (11, 100),
    "high": (101, 1000),
    "severe": (1001, None),
}


def lag_band_for(events_behind: int) -> str:
    """Map a raw lag to its band."""
    if events_behind < 0:
        raise ValueError("events_behind must not be negative")
    for name, (low, high) in LAG_BANDS.items():
        if events_behind >= low and (high is None or events_behind <= high):
            return name
    return "severe"
