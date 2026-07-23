"""Tests for epd2_audit_core.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.application import (
    AppendAuditEventRequest,
    append_audit_event,
    get_by_event_id,
    list_by_aggregate,
    list_by_target_types,
    verify_chain,
)
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock

_CLOCK = FixedClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))


def _request(**overrides: object) -> AppendAuditEventRequest:
    defaults: dict[str, object] = {
        "audit_event_id": uuid4(),
        "event_type": "credential.issued",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "actor_id": uuid4(),
        "actor_type": "service",
        "target_type": "participation_credential",
        "target_id": uuid4(),
        "action": "issue",
        "reason_code": "CREDENTIAL_ISSUED",
        "policy_version": "1.0",
        "correlation_id": uuid4(),
        "source_service": "credential-service",
    }
    defaults.update(overrides)
    return AppendAuditEventRequest(**defaults)  # type: ignore[arg-type]


def test_append_audit_event_sets_recorded_at_from_clock() -> None:
    store = InMemoryAuditEventStore()
    event = append_audit_event(store, _request(), clock=_CLOCK)
    assert event.recorded_at == _CLOCK.now()


def test_append_audit_event_chains_previous_hash() -> None:
    store = InMemoryAuditEventStore()
    first = append_audit_event(store, _request(), clock=_CLOCK)
    second = append_audit_event(store, _request(), clock=_CLOCK)
    assert second.previous_event_hash == first.event_hash


def test_critical_action_creates_retrievable_audit_event() -> None:
    """CT-00-07: a critical action creates an AuditEvent."""
    store = InMemoryAuditEventStore()
    request = _request()
    append_audit_event(store, request, clock=_CLOCK)
    found = get_by_event_id(store, request.audit_event_id)
    assert found is not None
    assert found.event_type == "credential.issued"


def test_idempotent_replay_of_same_request_succeeds() -> None:
    """CT-00-04: repeating the same event_id does not create a second action."""
    store = InMemoryAuditEventStore()
    request = _request()
    first = append_audit_event(store, request, clock=_CLOCK)
    second = append_audit_event(store, request, clock=_CLOCK)
    assert first == second
    assert len(list_by_aggregate(store, request.target_type, request.target_id)) == 1


def test_conflicting_replay_is_rejected_fail_closed() -> None:
    store = InMemoryAuditEventStore()
    request = _request()
    append_audit_event(store, request, clock=_CLOCK)
    conflicting = _request(audit_event_id=request.audit_event_id, action="revoke")
    with pytest.raises(AuditEventConflictError):
        append_audit_event(store, conflicting, clock=_CLOCK)


def test_verify_chain_reports_intact_after_several_appends() -> None:
    store = InMemoryAuditEventStore()
    for _ in range(5):
        append_audit_event(store, _request(), clock=_CLOCK)
    assert verify_chain(store).is_intact


def test_list_by_target_types_filters_and_preserves_order() -> None:
    """Additive (PACK-04, ADR-012 item 4): backs
    `epd2_transparency_service.application.generate_audit_export_package`.
    """
    store = InMemoryAuditEventStore()
    append_audit_event(store, _request(target_type="initiative"), clock=_CLOCK)
    append_audit_event(store, _request(target_type="moderation_case"), clock=_CLOCK)
    append_audit_event(store, _request(target_type="initiative"), clock=_CLOCK)
    matched = list_by_target_types(store, frozenset({"initiative"}))
    assert len(matched) == 2
    assert all(event.target_type == "initiative" for event in matched)


def test_list_by_target_types_returns_empty_for_no_match() -> None:
    store = InMemoryAuditEventStore()
    append_audit_event(store, _request(target_type="initiative"), clock=_CLOCK)
    assert list_by_target_types(store, frozenset({"ballot"})) == ()
