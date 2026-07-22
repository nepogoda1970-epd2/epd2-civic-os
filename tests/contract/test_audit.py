"""Audit tests (pack section 12.4): append-only; idempotent replay;
conflict on duplicate event id with different body; detection of changed
payload; detection of broken hash chain; deterministic canonical
serialization.

Audit Core's own unit tests (services/audit-core/tests/) already cover
each of these individually and in more depth; this file is the
pack-numbered, single-location aggregation pack section 12.4 asks for,
using the real in-memory store directly (not via any domain service)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import hashable_fields
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.hash_chain import GENESIS_PREVIOUS_HASH, compute_event_hash
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import FixedClock


def _request(**overrides: object) -> AppendAuditEventRequest:
    defaults = dict(
        audit_event_id=uuid4(),
        event_type="credential.issued",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        actor_id=uuid4(),
        actor_type="service",
        target_type="participation_credential",
        target_id=uuid4(),
        action="issue",
        reason_code="CREDENTIAL_ISSUED",
        policy_version="1.0",
        correlation_id=uuid4(),
        source_service="credential-service",
    )
    defaults.update(overrides)
    return AppendAuditEventRequest(**defaults)  # type: ignore[arg-type]


def test_append_only_no_update_or_delete_method_exists(
    audit_store: InMemoryAuditEventStore,
) -> None:
    """Ordinary API access can never update or delete a recorded
    AuditEvent - structurally, InMemoryAuditEventStore exposes no such
    method at all."""
    assert not hasattr(audit_store, "update")
    assert not hasattr(audit_store, "delete")
    assert not hasattr(audit_store, "remove")


def test_idempotent_replay_of_identical_request_succeeds(
    audit_store: InMemoryAuditEventStore, clock: FixedClock
) -> None:
    request = _request()
    first = append_audit_event(audit_store, request, clock=clock)
    second = append_audit_event(audit_store, request, clock=clock)
    assert first == second
    assert len(audit_store._events) == 1


def test_conflict_on_duplicate_event_id_with_different_body(
    audit_store: InMemoryAuditEventStore, clock: FixedClock
) -> None:
    shared_id = uuid4()
    append_audit_event(audit_store, _request(audit_event_id=shared_id), clock=clock)
    with pytest.raises(AuditEventConflictError):
        append_audit_event(
            audit_store,
            _request(audit_event_id=shared_id, action="revoke"),
            clock=clock,
        )


def test_verify_chain_detects_a_tampered_payload(
    audit_store: InMemoryAuditEventStore, clock: FixedClock
) -> None:
    """Directly mutating a stored event's `action` (simulating an
    out-of-band tamper attempt) must be detectable by `verify_chain`,
    since the recomputed hash no longer matches the stored `event_hash`."""
    from dataclasses import replace

    event = append_audit_event(audit_store, _request(), clock=clock)
    tampered = replace(event, action="tampered-action")
    audit_store._by_id[event.audit_event_id] = tampered
    audit_store._events[0] = tampered

    result = audit_store.verify_chain()
    assert result.is_intact is False
    assert result.broken_audit_event_id == event.audit_event_id


def test_verify_chain_detects_a_broken_previous_hash_link(
    audit_store: InMemoryAuditEventStore, clock: FixedClock
) -> None:
    append_audit_event(audit_store, _request(), clock=clock)
    second = append_audit_event(audit_store, _request(audit_event_id=uuid4()), clock=clock)
    from dataclasses import replace

    corrupted = replace(second, previous_event_hash="0" * 64)
    audit_store._by_id[second.audit_event_id] = corrupted
    audit_store._events[1] = corrupted

    result = audit_store.verify_chain()
    assert result.is_intact is False
    assert result.broken_audit_event_id == second.audit_event_id


def test_canonical_serialization_is_deterministic_regardless_of_key_order() -> None:
    a = canonical_dumps({"b": 1, "a": 2})
    b = canonical_dumps({"a": 2, "b": 1})
    assert a == b


def test_event_hash_is_deterministic_for_identical_content(clock: FixedClock) -> None:
    """Two independently-appended events with identical hashable content,
    on independent empty chains (so both see the same `previous_hash`),
    hash identically - determinism, not randomness, drives the chain."""
    from dataclasses import replace

    shared_id = uuid4()
    request_a = _request(audit_event_id=shared_id)
    request_b = replace(request_a)  # identical content, same shared_id

    store_a = InMemoryAuditEventStore()
    store_b = InMemoryAuditEventStore()
    event_a = append_audit_event(store_a, request_a, clock=clock)
    event_b = append_audit_event(store_b, request_b, clock=clock)
    assert compute_event_hash(event_a) == compute_event_hash(event_b)


def test_hashable_fields_excludes_event_hash_itself(
    audit_store: InMemoryAuditEventStore, clock: FixedClock
) -> None:
    event = append_audit_event(audit_store, _request(), clock=clock)
    fields = hashable_fields(event)
    assert "event_hash" not in fields
    assert fields["previous_event_hash"] == GENESIS_PREVIOUS_HASH
