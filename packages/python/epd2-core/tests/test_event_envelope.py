"""Tests for epd2_core.event_envelope."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_core.event_envelope import (
    ActorRef,
    EventEnvelope,
    InvalidEventEnvelopeError,
    SubjectRef,
    UnsupportedEventVersionError,
    assert_supported_major_version,
    build_event_envelope,
    compute_payload_hash,
    parse_major_version,
)


def _build(**overrides: object) -> EventEnvelope:
    defaults: dict[str, object] = {
        "event_id": uuid4(),
        "event_type": "account.created",
        "event_version": "1.0",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "producer": "account-service",
        "actor": ActorRef(actor_id=uuid4(), actor_type="user"),
        "subject": SubjectRef(subject_type="account", subject_id=uuid4()),
        "correlation_id": uuid4(),
        "causation_id": None,
        "payload": {"account_status": "pending"},
    }
    defaults.update(overrides)
    return build_event_envelope(**defaults)  # type: ignore[arg-type]


def test_build_event_envelope_computes_payload_hash() -> None:
    envelope = _build()
    assert envelope.integrity.payload_hash == compute_payload_hash({"account_status": "pending"})
    assert envelope.integrity.signature is None


def test_payload_hash_is_deterministic_regardless_of_key_order() -> None:
    a = compute_payload_hash({"b": 1, "a": 2})
    b = compute_payload_hash({"a": 2, "b": 1})
    assert a == b


def test_parse_major_version() -> None:
    assert parse_major_version("1.0") == 1
    assert parse_major_version("2.3") == 2


@pytest.mark.parametrize("bad_version", ["1", "1.x", "v1.0", "", "1.0.0"])
def test_parse_major_version_rejects_malformed_strings(bad_version: str) -> None:
    with pytest.raises(InvalidEventEnvelopeError):
        parse_major_version(bad_version)


def test_assert_supported_major_version_accepts_known_major() -> None:
    assert_supported_major_version("1.0", frozenset({1, 2}))


def test_assert_supported_major_version_rejects_unknown_major() -> None:
    with pytest.raises(UnsupportedEventVersionError):
        assert_supported_major_version("3.0", frozenset({1, 2}))


def test_empty_event_type_is_rejected() -> None:
    with pytest.raises(InvalidEventEnvelopeError):
        _build(event_type="")


def test_naive_occurred_at_is_rejected() -> None:
    with pytest.raises(InvalidEventEnvelopeError):
        _build(occurred_at=datetime(2026, 1, 1))


def test_actor_ref_rejects_empty_actor_type() -> None:
    with pytest.raises(InvalidEventEnvelopeError):
        ActorRef(actor_id=uuid4(), actor_type="")


def test_subject_ref_rejects_empty_subject_type() -> None:
    with pytest.raises(InvalidEventEnvelopeError):
        SubjectRef(subject_type="", subject_id=uuid4())
