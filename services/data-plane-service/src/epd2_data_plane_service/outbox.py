"""The transactional outbox (PACK-13 §8; ADR-071).

The single most load-bearing requirement in the specification is
`P13-TX-003`: the authoritative state change and its outbox record are
written **atomically**, in the same transaction. That is what makes "the
event happened if and only if the state changed" true rather than
aspirational, and `OutboxWriter.write_within` is where this package makes
it structural — an outbox record cannot be produced except through a
unit of work, and a rolled-back unit produces none.

Four further properties are enforced by the types:

- **Immutable after commit, except delivery metadata**
  (`P13-OBX-003`). `OutboxRecord.envelope`, its event ID, type and
  version are frozen; `with_status`, `with_attempt` and
  `with_acknowledgement` return copies that touch only delivery state.
- **A stable event ID across republication** (`P13-OBX-005`). Retry
  reuses the logical event ID and never mints a new one; a consumer that
  has seen the ID has seen the event.
- **Published state and delivery evidence are distinct**
  (`P13-OBX-011`). "We dispatched it" and "the broker acknowledged it"
  are different fields, because conflating them makes a lost
  acknowledgement look like a successful delivery.
- **Secrets and unnecessary personal data are rejected before the record
  is written** (`P13-OBX-008`) — not before it is dispatched. A payload
  that reached storage has already leaked into backups.

The dispatcher lives in `delivery`; this module owns the record.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from epd2_core.event_envelope import EventEnvelope
from epd2_data_plane_service.concurrency import UnitOfWorkReference
from epd2_data_plane_service.domain import (
    AggregateReference,
    OrganizationScopeReference,
    RetentionScheduleReference,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    OutboxBacklogThresholdExceededError,
    OutboxPublicationPendingError,
    RecordUnderLegalHoldError,
)


class OutboxStatus(StrEnum):
    """§8.1's status set, exactly.

    `SUPERSEDED_BY_REPLAY` exists so a replay can mark a record without
    deleting it: replay never rewrites history (`P13-DEL-010`)."""

    PENDING = "pending"
    DISPATCHING = "dispatching"
    PUBLISHED = "published"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    SUPERSEDED_BY_REPLAY = "superseded_by_replay"


#: The declared status transitions. `PENDING -> ACKNOWLEDGED` is absent
#: deliberately: a record cannot be acknowledged without having been
#: published, because that is the exact confusion `P13-OBX-011` exists to
#: prevent.
OUTBOX_STATUS_TRANSITIONS: Mapping[OutboxStatus, frozenset[OutboxStatus]] = {
    OutboxStatus.PENDING: frozenset({OutboxStatus.DISPATCHING, OutboxStatus.SUPERSEDED_BY_REPLAY}),
    OutboxStatus.DISPATCHING: frozenset(
        {OutboxStatus.PUBLISHED, OutboxStatus.FAILED, OutboxStatus.DEAD_LETTERED}
    ),
    OutboxStatus.PUBLISHED: frozenset(
        {OutboxStatus.ACKNOWLEDGED, OutboxStatus.FAILED, OutboxStatus.DEAD_LETTERED}
    ),
    OutboxStatus.FAILED: frozenset({OutboxStatus.DISPATCHING, OutboxStatus.DEAD_LETTERED}),
    OutboxStatus.ACKNOWLEDGED: frozenset(),
    OutboxStatus.DEAD_LETTERED: frozenset({OutboxStatus.DISPATCHING}),
    OutboxStatus.SUPERSEDED_BY_REPLAY: frozenset(),
}


class DeliveryOutcome(StrEnum):
    """The outcome of one attempt.

    `ACKNOWLEDGEMENT_UNKNOWN` is a first-class outcome, not an error
    bucket: a missing acknowledgement is treated as *unknown*, not as
    failure and not as success (`P13-DEL-007`)."""

    PUBLISHED = "published"
    ACKNOWLEDGEMENT_UNKNOWN = "acknowledgement_unknown"
    TRANSIENT_FAILURE = "transient_failure"
    DETERMINISTIC_FAILURE = "deterministic_failure"
    BROKER_UNAVAILABLE = "broker_unavailable"


@dataclass(frozen=True, slots=True)
class DestinationReference:
    """An opaque reference to where a record was dispatched.

    Deliberately not a broker URL, topic name or connection string: this
    package prescribes no broker topology (`P13-VOTE-008` for the voting
    plane, and no reason to prescribe one for the general plane either),
    and a connection string in a record is a secret in a backup."""

    destination_id: UUID
    destination_name: str

    def __post_init__(self) -> None:
        if not self.destination_name:
            raise ValueError("destination_name must not be empty")


@dataclass(frozen=True, slots=True)
class BrokerAcknowledgementReference:
    """An opaque reference to the broker's own acknowledgement — never
    the broker's internal payload (§8.1)."""

    acknowledgement_reference: str
    received_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.received_at, field="BrokerAcknowledgementReference.received_at")
        if not self.acknowledgement_reference:
            raise ValueError("an acknowledgement reference must not be empty")


@dataclass(frozen=True, slots=True)
class DeliveryAttempt:
    """One auditable delivery attempt (`P13-OBX-010`): when, to which
    destination, with what outcome."""

    attempt_number: int
    started_at: datetime
    outcome: DeliveryOutcome
    destination: DestinationReference
    error_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.started_at, field="DeliveryAttempt.started_at")
        if self.attempt_number < 1:
            raise ValueError("attempt_number starts at 1")


@dataclass(frozen=True, slots=True)
class PublicationEvidence:
    """What was published, when, and the acknowledgement that proves it.

    `acknowledgement` is optional and its absence is meaningful: a record
    published without an acknowledgement is published, not
    acknowledged."""

    event_id: UUID
    published_at: datetime
    destination: DestinationReference
    acknowledgement: BrokerAcknowledgementReference | None = None

    def __post_init__(self) -> None:
        require_timezone(self.published_at, field="PublicationEvidence.published_at")

    @property
    def acknowledged(self) -> bool:
        return self.acknowledgement is not None


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    """One outbox record.

    Carries the canonical envelope unchanged (`P13-OBX-004`): PACK-13
    adds no envelope field, and all transport metadata — attempt counts,
    broker references, dispatch timestamps — lives here on the record
    rather than on the event. That separation is the specific decision
    that keeps PACK-13 canon-neutral (ADR-071)."""

    outbox_record_id: UUID
    event_id: UUID
    event_type: str
    event_version: str
    envelope: EventEnvelope
    aggregate: AggregateReference
    scope: OrganizationScopeReference
    created_at: datetime
    status: OutboxStatus = OutboxStatus.PENDING
    sequence_number: int = 1
    attempts: tuple[DeliveryAttempt, ...] = ()
    publication_evidence: PublicationEvidence | None = None
    retention_schedule: RetentionScheduleReference | None = None
    under_legal_hold: bool = False

    def __post_init__(self) -> None:
        require_timezone(self.created_at, field="OutboxRecord.created_at")
        if self.event_id != self.envelope.event_id:
            raise ValueError(
                "the outbox record's event ID is the envelope's event ID; a second identifier "
                "would let a republication mint a new logical event (P13-OBX-005)"
            )
        if self.event_type != self.envelope.event_type:
            raise ValueError("the outbox record's event type is the envelope's event type")
        if self.sequence_number < 1:
            raise ValueError("sequence_number starts at 1 within its ordering scope")

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    @property
    def published(self) -> bool:
        """Whether the record was dispatched and the broker accepted it.

        Distinct from `acknowledged`. Two properties, two facts."""
        return self.publication_evidence is not None

    @property
    def acknowledged(self) -> bool:
        return self.publication_evidence is not None and self.publication_evidence.acknowledged

    def with_status(self, new_status: OutboxStatus) -> OutboxRecord:
        """Return a copy in `new_status`, refusing an undeclared
        transition. Only delivery metadata changes; identity, type,
        version and envelope do not (`P13-OBX-003`)."""
        permitted = OUTBOX_STATUS_TRANSITIONS[self.status]
        if new_status not in permitted:
            raise ValueError(
                f"outbox record {self.outbox_record_id}: {self.status.value} -> "
                f"{new_status.value} is not a declared transition; declared: "
                f"{sorted(s.value for s in permitted)}"
            )
        return replace(self, status=new_status)

    def with_attempt(self, attempt: DeliveryAttempt) -> OutboxRecord:
        """Append a delivery attempt. The logical event ID is unchanged
        by construction — there is no parameter here that could alter
        it."""
        if attempt.attempt_number != self.attempt_count + 1:
            raise ValueError(
                f"attempt numbers are consecutive; expected {self.attempt_count + 1}, got "
                f"{attempt.attempt_number}"
            )
        return replace(self, attempts=(*self.attempts, attempt))

    def with_publication(self, evidence: PublicationEvidence) -> OutboxRecord:
        if evidence.event_id != self.event_id:
            raise ValueError("publication evidence belongs to the record's own event")
        return replace(self, publication_evidence=evidence)

    def with_acknowledgement(self, acknowledgement: BrokerAcknowledgementReference) -> OutboxRecord:
        """Record the broker's acknowledgement.

        Refuses when there is no publication to acknowledge: an
        acknowledgement without a publication is the conflation
        `P13-OBX-011` forbids, arriving from the other direction."""
        if self.publication_evidence is None:
            raise OutboxPublicationPendingError(
                f"outbox record {self.outbox_record_id} has not been published; there is "
                f"nothing for an acknowledgement to prove"
            )
        return replace(
            self,
            publication_evidence=replace(
                self.publication_evidence, acknowledgement=acknowledgement
            ),
        )

    def require_deletable(self) -> None:
        """Outbox cleanup obeys retention policy and is a governed
        deletion, not a maintenance script's side effect
        (`P13-OBX-012`).

        A record under legal hold is preserved — and the hold widens no
        access to its payload (`P13-OBX-013`)."""
        if self.under_legal_hold:
            raise RecordUnderLegalHoldError(
                f"outbox record {self.outbox_record_id} is under legal hold and is preserved; "
                f"the hold does not authorize reading its payload"
            )
        if self.retention_schedule is None:
            raise RecordUnderLegalHoldError(
                f"outbox record {self.outbox_record_id} carries no retention schedule "
                f"reference; deletion without a policy decision is refused"
            )


class OutboxWriter:
    """The only way an outbox record is produced.

    Every method takes a `UnitOfWorkReference`, so a record cannot exist
    without a transaction to be atomic with (`P13-TX-003`). The writer
    performs **no dispatch**: `P13-TX-004` forbids an external effect
    inside a transaction, and there is no method here that could perform
    one.
    """

    @staticmethod
    def write_within(
        unit: UnitOfWorkReference,
        *,
        outbox_record_id: UUID,
        envelope: EventEnvelope,
        aggregate: AggregateReference,
        created_at: datetime,
        sequence_number: int,
        retention_schedule: RetentionScheduleReference | None = None,
    ) -> OutboxRecord:
        """Create the outbox record for a state change, inside `unit`.

        Three refusals happen here rather than at dispatch time:

        1. **Cross-domain write** — the unit belongs to one domain and
           the aggregate must be its own (`P13-DP-014`).
        2. **Prohibited payload keys** — checked *before* the record is
           written, because a payload that reached storage has already
           leaked into backups (`P13-OBX-008`).
        3. **Scope** — the record carries the unit's scope, which is the
           scope the domain assigned; scope is never invented here
           (`P13-CTX-002`).
        """
        unit.assert_same_domain(aggregate)
        reject_prohibited_payload_keys(
            envelope.payload, context=f"outbox payload for {envelope.event_type}"
        )
        return OutboxRecord(
            outbox_record_id=outbox_record_id,
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            event_version=envelope.event_version,
            envelope=envelope,
            aggregate=aggregate,
            scope=unit.scope,
            created_at=created_at,
            sequence_number=sequence_number,
            retention_schedule=retention_schedule,
        )


@dataclass(frozen=True, slots=True)
class OutboxBacklog:
    """The backlog as a first-class health signal (§29).

    Reports a **count and a threshold**, never the records themselves: a
    backlog surface that showed payloads would be an unrestricted read of
    every domain's events."""

    pending_count: int
    oldest_pending_age_seconds: int
    alert_threshold: int

    def __post_init__(self) -> None:
        if self.pending_count < 0 or self.alert_threshold < 1:
            raise ValueError("pending_count must not be negative and a threshold is positive")

    @property
    def exceeds_threshold(self) -> bool:
        return self.pending_count > self.alert_threshold

    def require_within_threshold(self) -> None:
        if self.exceeds_threshold:
            raise OutboxBacklogThresholdExceededError(
                f"outbox backlog is {self.pending_count}, past its alert threshold of "
                f"{self.alert_threshold}; backlog is a first-class health signal and the "
                f"oldest pending record is {self.oldest_pending_age_seconds}s old"
            )


def summarize_for_operator(record: OutboxRecord) -> Mapping[str, Any]:
    """The operator-visible view of one outbox record.

    Deliberately excludes the payload. An operator surface needs status,
    counts, timing and references; the event's content belongs to its
    owning domain and reaches an operator only through a PACK-12 governed
    path (`P13-FE-004`)."""
    return {
        "outbox_record_id": str(record.outbox_record_id),
        "event_type": record.event_type,
        "event_version": record.event_version,
        "status": record.status.value,
        "attempt_count": record.attempt_count,
        "published": record.published,
        "acknowledged": record.acknowledged,
        "sequence_number": record.sequence_number,
        "organization_id": str(record.scope.organization_id),
    }
