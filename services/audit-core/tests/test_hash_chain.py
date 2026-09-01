"""Tests for epd2_audit_core.hash_chain."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.hash_chain import GENESIS_PREVIOUS_HASH, compute_event_hash


def _make(**overrides: object) -> AuditEvent:
    defaults: dict[str, object] = {
        "audit_event_id": uuid4(),
        "event_type": "credential.issued",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "recorded_at": datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        "actor_id": uuid4(),
        "actor_type": "service",
        "target_type": "participation_credential",
        "target_id": uuid4(),
        "action": "issue",
        "reason_code": "CREDENTIAL_ISSUED",
        "policy_version": "1.0",
        "before_hash": "",
        "after_hash": "deadbeef",
        "correlation_id": uuid4(),
        "source_service": "credential-service",
        "previous_event_hash": GENESIS_PREVIOUS_HASH,
        "event_hash": "placeholder",
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)  # type: ignore[arg-type]


def test_hash_is_deterministic_for_identical_content() -> None:
    shared_fields = {
        "audit_event_id": uuid4(),
        "actor_id": uuid4(),
        "target_id": uuid4(),
        "correlation_id": uuid4(),
    }
    a = _make(**shared_fields)
    b = _make(**shared_fields)
    assert compute_event_hash(a) == compute_event_hash(b)


def test_hash_changes_when_any_field_changes() -> None:
    event = _make()
    tampered = replace(event, action="revoke")
    assert compute_event_hash(event) != compute_event_hash(tampered)


def test_hash_does_not_depend_on_the_event_hash_field_itself() -> None:
    event = _make(event_hash="aaaa")
    other = replace(event, event_hash="bbbb")
    assert compute_event_hash(event) == compute_event_hash(other)


def test_hash_depends_on_previous_event_hash() -> None:
    event = _make(previous_event_hash=GENESIS_PREVIOUS_HASH)
    chained = replace(event, previous_event_hash="1" * 64)
    assert compute_event_hash(event) != compute_event_hash(chained)


def test_hash_is_64_char_hex_sha256() -> None:
    event = _make()
    digest = compute_event_hash(event)
    assert len(digest) == 64
    int(digest, 16)  # raises ValueError if not valid hex
