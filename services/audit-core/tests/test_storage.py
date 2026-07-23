"""Tests for epd2_audit_core.storage.InMemoryAuditEventStore.

Covers: append-only behavior, idempotent replay (CT-00-04), conflict on a
duplicate id with different content, and hash-chain verification
including detection of a tampered/broken chain (pack section 12.4).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.hash_chain import GENESIS_PREVIOUS_HASH, compute_event_hash
from epd2_audit_core.storage import InMemoryAuditEventStore


def _make_chained(store: InMemoryAuditEventStore, **overrides: object) -> AuditEvent:
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
        "previous_event_hash": store.head_hash(),
        "event_hash": "pending",
    }
    defaults.update(overrides)
    provisional = AuditEvent(**defaults)  # type: ignore[arg-type]
    return replace(provisional, event_hash=compute_event_hash(provisional))


def test_append_then_get_by_event_id() -> None:
    store = InMemoryAuditEventStore()
    event = _make_chained(store)
    store.append(event)
    assert store.get_by_event_id(event.audit_event_id) == event


def test_get_by_event_id_returns_none_when_absent() -> None:
    store = InMemoryAuditEventStore()
    assert store.get_by_event_id(uuid4()) is None


def test_idempotent_replay_of_identical_event_succeeds() -> None:
    store = InMemoryAuditEventStore()
    event = _make_chained(store)
    first = store.append(event)
    second = store.append(event)
    assert first == second
    assert len(store.list_by_aggregate(event.target_type, event.target_id)) == 1


def test_conflicting_replay_with_different_content_is_rejected() -> None:
    store = InMemoryAuditEventStore()
    event = _make_chained(store)
    store.append(event)
    conflicting = replace(event, action="revoke")
    with pytest.raises(AuditEventConflictError):
        store.append(conflicting)


def test_list_by_aggregate_filters_correctly() -> None:
    store = InMemoryAuditEventStore()
    target_a = uuid4()
    target_b = uuid4()
    event_a = _make_chained(store, target_type="account", target_id=target_a)
    store.append(event_a)
    event_b = _make_chained(store, target_type="account", target_id=target_b)
    store.append(event_b)
    result = store.list_by_aggregate("account", target_a)
    assert result == (event_a,)


def test_verify_chain_on_empty_store_is_intact() -> None:
    store = InMemoryAuditEventStore()
    result = store.verify_chain()
    assert result.is_intact
    assert result.checked_count == 0


def test_verify_chain_on_valid_sequence_is_intact() -> None:
    store = InMemoryAuditEventStore()
    for _ in range(3):
        store.append(_make_chained(store))
    result = store.verify_chain()
    assert result.is_intact
    assert result.checked_count == 3


def test_verify_chain_detects_tampered_payload() -> None:
    """Directly mutating a stored record's content without recomputing
    every subsequent hash must be detected by verify_chain."""
    store = InMemoryAuditEventStore()
    first = store.append(_make_chained(store))
    store.append(_make_chained(store))

    # Simulate tampering: replace the first stored event's action without
    # updating its own event_hash or any downstream previous_event_hash.
    tampered = replace(first, action="tampered")
    store._by_id[first.audit_event_id] = tampered
    index = store._events.index(first)
    store._events[index] = tampered

    result = store.verify_chain()
    assert not result.is_intact
    assert result.broken_at_index == 0
    assert result.broken_audit_event_id == first.audit_event_id


def test_verify_chain_detects_broken_previous_hash_link() -> None:
    store = InMemoryAuditEventStore()
    store.append(_make_chained(store))
    second = store.append(_make_chained(store))

    tampered_second = replace(second, previous_event_hash="f" * 64)
    store._by_id[second.audit_event_id] = tampered_second
    index = store._events.index(second)
    store._events[index] = tampered_second

    result = store.verify_chain()
    assert not result.is_intact
    assert result.broken_at_index == 1


def test_head_hash_starts_at_genesis() -> None:
    store = InMemoryAuditEventStore()
    assert store.head_hash() == GENESIS_PREVIOUS_HASH


def test_head_hash_advances_after_append() -> None:
    store = InMemoryAuditEventStore()
    event = _make_chained(store)
    store.append(event)
    assert store.head_hash() == event.event_hash


def test_list_all_returns_events_in_append_order() -> None:
    store = InMemoryAuditEventStore()
    first = _make_chained(store)
    store.append(first)
    second = _make_chained(store)
    store.append(second)
    assert store.list_all() == (first, second)


def test_list_all_empty_store() -> None:
    store = InMemoryAuditEventStore()
    assert store.list_all() == ()
