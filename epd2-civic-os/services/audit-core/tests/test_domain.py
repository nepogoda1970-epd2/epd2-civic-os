"""Tests for epd2_audit_core.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.domain import AuditEvent, hashable_fields


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
        "previous_event_hash": "0" * 64,
        "event_hash": "a" * 64,
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)  # type: ignore[arg-type]


def test_valid_audit_event_constructs() -> None:
    event = _make()
    assert event.action == "issue"


@pytest.mark.parametrize(
    "field",
    ["event_type", "actor_type", "target_type", "action", "reason_code", "source_service"],
)
def test_empty_required_string_field_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        _make(**{field: ""})


def test_naive_occurred_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make(occurred_at=datetime(2026, 1, 1))


def test_naive_recorded_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make(recorded_at=datetime(2026, 1, 1))


def test_recorded_at_before_occurred_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="recorded_at must not be before"):
        _make(
            occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_hashable_fields_excludes_event_hash() -> None:
    event = _make()
    fields = hashable_fields(event)
    assert "event_hash" not in fields
    assert fields["previous_event_hash"] == event.previous_event_hash
    assert fields["audit_event_id"] == event.audit_event_id
