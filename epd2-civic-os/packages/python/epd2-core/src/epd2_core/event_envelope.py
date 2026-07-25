"""Canonical event envelope, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 21 ("Стандарт
события").

This module implements only the envelope shape and its generic validation
rules (unknown major version rejected, required fields present, payload
hash computed deterministically) - no domain-specific event types, names,
or payloads. Per CLAUDE-PACK-02 section 4.2, shared packages may contain
"canonical event envelope primitives" but not domain business logic; which
event types exist, and what each payload contains, is decided by each
service that owns the corresponding entity.

See ADR-002 for why this envelope's fields intentionally do not match
CLAUDE-PACK-02's own suggested field list (section 8.1) - the canon's
section-21 shape takes priority per the pack's own section 2.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps


class UnsupportedEventVersionError(ValueError):
    """Raised when an event's major version is not one the caller supports.

    Per canon section 21: "неизвестная major-версия события не
    обрабатывается" (an unknown major version is not processed).
    """


class InvalidEventEnvelopeError(ValueError):
    """Raised when an event envelope is missing a required field or has an
    invalid value. Per canon section 21: "отсутствующее обязательное поле
    вызывает fail-closed" (a missing required field causes fail-closed).
    """


@dataclass(frozen=True, slots=True)
class ActorRef:
    """The `actor` object of the canonical envelope (canon section 21)."""

    actor_id: UUID
    actor_type: str

    def __post_init__(self) -> None:
        if not self.actor_type:
            raise InvalidEventEnvelopeError("actor.actor_type must not be empty")


@dataclass(frozen=True, slots=True)
class SubjectRef:
    """The `subject` object of the canonical envelope (canon section 21)."""

    subject_type: str
    subject_id: UUID

    def __post_init__(self) -> None:
        if not self.subject_type:
            raise InvalidEventEnvelopeError("subject.subject_type must not be empty")


@dataclass(frozen=True, slots=True)
class EventIntegrity:
    """The `integrity` object of the canonical envelope (canon section 21).

    `signature` is optional per the canon's own example payload
    (`"signature": "optional-signature"`); PACK-02 does not implement
    cryptographic signing, so it is always `None` here.
    """

    payload_hash: str
    signature: str | None = None


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """The canonical event envelope (canon section 21)."""

    event_id: UUID
    event_type: str
    event_version: str
    occurred_at: datetime
    producer: str
    actor: ActorRef
    subject: SubjectRef
    correlation_id: UUID
    causation_id: UUID | None
    payload: Mapping[str, Any]
    integrity: EventIntegrity = field(compare=False)

    def __post_init__(self) -> None:
        if not self.event_type:
            raise InvalidEventEnvelopeError("event_type must not be empty")
        if not self.producer:
            raise InvalidEventEnvelopeError("producer must not be empty")
        if self.occurred_at.tzinfo is None:
            raise InvalidEventEnvelopeError("occurred_at must be timezone-aware")
        parse_major_version(self.event_version)


def parse_major_version(event_version: str) -> int:
    """Parse the major version number out of an `event_version` string
    like `"1.0"`. Raises `InvalidEventEnvelopeError` if the string is not
    of the form `<major>.<minor>` with non-negative integers.
    """
    parts = event_version.split(".")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise InvalidEventEnvelopeError(
            f"event_version must be of the form '<major>.<minor>', got {event_version!r}"
        )
    return int(parts[0])


def compute_payload_hash(payload: Mapping[str, Any]) -> str:
    """Compute the deterministic `integrity.payload_hash` for `payload`."""
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


def build_event_envelope(
    *,
    event_id: UUID,
    event_type: str,
    event_version: str,
    occurred_at: datetime,
    producer: str,
    actor: ActorRef,
    subject: SubjectRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    payload: Mapping[str, Any],
) -> EventEnvelope:
    """Construct an `EventEnvelope`, computing `integrity.payload_hash`
    deterministically from `payload` so callers cannot forget to do so or
    compute it inconsistently.
    """
    integrity = EventIntegrity(payload_hash=compute_payload_hash(payload), signature=None)
    return EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        event_version=event_version,
        occurred_at=occurred_at,
        producer=producer,
        actor=actor,
        subject=subject,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
        integrity=integrity,
    )


def assert_supported_major_version(event_version: str, supported_majors: frozenset[int]) -> None:
    """Raise `UnsupportedEventVersionError` if `event_version`'s major
    version is not in `supported_majors`. Callers (services) decide which
    majors they support for each event type; this helper only enforces
    fail-closed rejection of the rest (CT-00-05).
    """
    major = parse_major_version(event_version)
    if major not in supported_majors:
        raise UnsupportedEventVersionError(
            f"unsupported major version {major} for event_version {event_version!r}; "
            f"supported majors: {sorted(supported_majors)}"
        )
