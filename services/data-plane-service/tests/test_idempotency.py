"""Idempotency and deduplication (PACK-13 §11; ADR-077).

The six checks §13 of the implementation task requires: scope includes
domain and operation; a key is never a user identifier; the same key with
the same payload returns the first result; reuse with a different payload
conflicts; a consequential action does not silently duplicate after
expiry; and no sensitive payload is stored.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import NOW, idempotency_key, uid

from epd2_data_plane_service.exceptions import (
    IdempotencyGlobalIdentifierProhibitedError,
    IdempotencyKeyReusedWithDifferentPayloadError,
    IdempotencyKeyScopeInvalidError,
    IdempotencyRecordExpiredError,
)
from epd2_data_plane_service.idempotency import (
    CONSEQUENTIAL_OPERATION_CLASSES,
    BusinessFactGuard,
    DeduplicationRecord,
    IdempotencyKey,
    IdempotencyOutcome,
    IdempotencyPolicy,
    IdempotencyRecord,
    IdempotencyScope,
    OperationClass,
    compute_request_digest,
)

DIGEST = compute_request_digest({"membership_id": "m-1", "status": "active"})
OTHER_DIGEST = compute_request_digest({"membership_id": "m-1", "status": "suspended"})


def _record(key: IdempotencyKey, digest: str = DIGEST) -> IdempotencyRecord:
    return IdempotencyRecord(
        key=key,
        request_digest=digest,
        result_reference=uid(42),
        recorded_at=NOW,
        expires_at=NOW + timedelta(days=1),
    )


def test_a_scope_requires_both_a_domain_and_an_operation() -> None:
    with pytest.raises(IdempotencyKeyScopeInvalidError):
        IdempotencyScope(
            domain_name="", operation_name="record", operation_class=OperationClass.COMMAND
        )
    with pytest.raises(IdempotencyKeyScopeInvalidError):
        IdempotencyScope(
            domain_name="membership-service",
            operation_name="",
            operation_class=OperationClass.COMMAND,
        )


def test_the_same_key_value_in_two_domains_is_two_keys() -> None:
    left = idempotency_key("shared", domain="membership-service")
    right = idempotency_key("shared", domain="finance-service")
    assert left.qualified_key != right.qualified_key
    assert left.digest != right.digest


def test_a_key_derived_from_a_person_identifier_is_refused() -> None:
    with pytest.raises(IdempotencyGlobalIdentifierProhibitedError):
        idempotency_key("person_id")
    with pytest.raises(IdempotencyGlobalIdentifierProhibitedError):
        idempotency_key("email:someone@example.org")


def test_an_empty_key_is_refused() -> None:
    with pytest.raises(IdempotencyKeyScopeInvalidError):
        idempotency_key("")


def test_same_key_same_payload_replays_the_first_result() -> None:
    key = idempotency_key()
    existing = _record(key)
    decision = IdempotencyPolicy.evaluate(
        key=key, incoming_digest=DIGEST, existing=existing, now=NOW
    )
    assert decision.outcome is IdempotencyOutcome.REPLAY
    assert decision.record is not None
    assert decision.record.result_reference == uid(42)
    assert not decision.should_execute


def test_same_key_different_payload_is_a_conflict_not_a_replay() -> None:
    key = idempotency_key()
    decision = IdempotencyPolicy.evaluate(
        key=key, incoming_digest=OTHER_DIGEST, existing=_record(key), now=NOW
    )
    assert decision.outcome is IdempotencyOutcome.CONFLICT
    assert decision.reason_code == "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD"
    with pytest.raises(IdempotencyKeyReusedWithDifferentPayloadError):
        IdempotencyPolicy.require_no_conflict(decision, context="test")


def test_a_first_execution_is_the_outcome_when_no_record_exists() -> None:
    decision = IdempotencyPolicy.evaluate(
        key=idempotency_key(), incoming_digest=DIGEST, existing=None, now=NOW
    )
    assert decision.should_execute


def test_a_consequential_operation_requires_a_business_fact_guard() -> None:
    """ADR-077: the idempotency record is an optimisation; the guard is
    the control."""
    key = idempotency_key(
        "export-1", operation="generate_export", operation_class=OperationClass.EXPORT_GENERATION
    )
    with pytest.raises(IdempotencyRecordExpiredError, match="business-fact guard"):
        IdempotencyPolicy.evaluate(key=key, incoming_digest=DIGEST, existing=None, now=NOW)


def test_an_expired_record_does_not_silently_duplicate_a_consequential_action() -> None:
    key = idempotency_key(
        "export-1", operation="generate_export", operation_class=OperationClass.EXPORT_GENERATION
    )
    guard = BusinessFactGuard(guard_name="one_artifact_per_approval", fact_key="approval-1")
    decision = IdempotencyPolicy.evaluate(
        key=key,
        incoming_digest=DIGEST,
        existing=_record(key),
        now=NOW + timedelta(days=2),
        guard=guard,
        guarded_fact_already_exists=True,
    )
    assert decision.outcome is IdempotencyOutcome.EXPIRED
    with pytest.raises(IdempotencyRecordExpiredError):
        IdempotencyPolicy.require_no_conflict(decision, context="export generation")


def test_an_expired_record_admits_a_fresh_execution_when_the_fact_is_absent() -> None:
    key = idempotency_key(
        "export-2", operation="generate_export", operation_class=OperationClass.EXPORT_GENERATION
    )
    guard = BusinessFactGuard(guard_name="one_artifact_per_approval", fact_key="approval-2")
    decision = IdempotencyPolicy.evaluate(
        key=key,
        incoming_digest=DIGEST,
        existing=_record(key),
        now=NOW + timedelta(days=2),
        guard=guard,
        guarded_fact_already_exists=False,
    )
    assert decision.should_execute


def test_the_guard_blocks_a_first_execution_when_the_fact_already_exists() -> None:
    key = idempotency_key(
        "export-3", operation="generate_export", operation_class=OperationClass.EXPORT_GENERATION
    )
    guard = BusinessFactGuard(guard_name="one_artifact_per_approval", fact_key="approval-3")
    decision = IdempotencyPolicy.evaluate(
        key=key,
        incoming_digest=DIGEST,
        existing=None,
        now=NOW,
        guard=guard,
        guarded_fact_already_exists=True,
    )
    assert decision.outcome is IdempotencyOutcome.CONFLICT


def test_the_record_stores_a_digest_and_a_reference_not_a_payload() -> None:
    """`P13-IDEM-008`: a request digest, not the request."""
    record = _record(idempotency_key())
    fields = record.__slots__
    assert "request_digest" in fields
    assert "result_reference" in fields
    for forbidden in ("payload", "request", "body", "result"):
        assert forbidden not in fields


def test_deduplication_is_keyed_on_the_event_and_the_consumers_own_scope() -> None:
    """`P13-IDEM-009`: one event consumed by two consumers is two
    independent effects."""
    left = DeduplicationRecord(
        consumer_name="search-projection",
        consumer_domain="membership-service",
        event_id=uid(7),
        first_seen_at=NOW,
    )
    right = DeduplicationRecord(
        consumer_name="finance-projection",
        consumer_domain="finance-service",
        event_id=uid(7),
        first_seen_at=NOW,
    )
    assert left.dedup_key != right.dedup_key


def test_a_deduplication_record_requires_a_consumer_scope() -> None:
    with pytest.raises(IdempotencyKeyScopeInvalidError):
        DeduplicationRecord(
            consumer_name="",
            consumer_domain="membership-service",
            event_id=uid(7),
            first_seen_at=NOW,
        )


def test_observing_a_duplicate_counts_it_rather_than_discarding_it() -> None:
    record = DeduplicationRecord(
        consumer_name="c",
        consumer_domain="d",
        event_id=uid(7),
        first_seen_at=NOW,
    )
    assert record.observed_again().observation_count == 2
    assert record.observed_again().first_seen_at == NOW


def test_the_consequential_classes_are_the_ones_with_lasting_effects() -> None:
    assert OperationClass.EXPORT_GENERATION in CONSEQUENTIAL_OPERATION_CLASSES
    assert OperationClass.MIGRATION_EXECUTION in CONSEQUENTIAL_OPERATION_CLASSES
    assert OperationClass.SCHEMA_PUBLICATION in CONSEQUENTIAL_OPERATION_CLASSES
    assert OperationClass.EVENT_CONSUMER not in CONSEQUENTIAL_OPERATION_CLASSES


def test_a_business_fact_guard_requires_both_a_name_and_a_fact() -> None:
    with pytest.raises(ValueError, match="requires both"):
        BusinessFactGuard(guard_name="", fact_key="x")


def test_an_idempotency_record_expires_after_it_is_recorded() -> None:
    with pytest.raises(ValueError, match="after recorded_at"):
        IdempotencyRecord(
            key=idempotency_key(),
            request_digest=DIGEST,
            result_reference=uid(1),
            recorded_at=NOW,
            expires_at=NOW,
        )


def test_a_request_digest_is_stable_across_key_ordering() -> None:
    assert compute_request_digest({"a": 1, "b": 2}) == compute_request_digest({"b": 2, "a": 1})
