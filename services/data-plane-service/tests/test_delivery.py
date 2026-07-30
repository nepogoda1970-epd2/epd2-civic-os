"""Delivery semantics, ordering, dead-letter and replay
(PACK-13 §9, §10; ADR-072).

Duplicate, delayed, out-of-order, missing acknowledgement, retry,
dead-letter, replay, poison event, unsupported schema version, consumer
checkpoint and ordering gap — every situation §9.1 says must be
specified rather than discovered.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import (
    NOW,
    classification,
    destination,
    grant,
    outbox_record,
    retention,
    scope,
    uid,
)

from epd2_data_plane_service.delivery import (
    LAG_BANDS,
    ConsumerCheckpoint,
    ConsumerEffect,
    DeadLetterRecord,
    DispatchAction,
    OrderingDecision,
    OrderingScope,
    OrderingScopeKind,
    ReferenceBroker,
    ReferenceConsumer,
    ReferenceDispatcher,
    ReplayReference,
    RetryPolicy,
    assess_ordering,
    decide_dispatch,
    lag_band_for,
    replay_preserves_history,
    require_acknowledged,
    require_in_order,
)
from epd2_data_plane_service.domain import ActorReference, DomainReference
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
from epd2_data_plane_service.outbox import OutboxStatus

POLICY = RetryPolicy(max_attempts=3, initial_backoff=timedelta(seconds=10))
CONSUMER_DOMAIN = DomainReference(domain_name="transparency-service")


def _checkpoint(position: int = 0) -> ConsumerCheckpoint:
    return ConsumerCheckpoint(
        consumer_name="transparency-projection",
        consumer_domain="transparency-service",
        ordering_scope_key="per_aggregate::x:None",
        position=position,
        updated_at=NOW,
    )


def _consumer(
    *, consequential: bool = True, versions: frozenset[str] = frozenset({"1.0"})
) -> ReferenceConsumer:
    return ReferenceConsumer(
        consumer_name="transparency-projection",
        consumer_domain="transparency-service",
        supported_event_versions=versions,
        consequential=consequential,
    )


def _dispatcher(broker: ReferenceBroker) -> ReferenceDispatcher:
    return ReferenceDispatcher(broker, destination=destination(), policy=POLICY)


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def test_the_next_sequence_is_in_order() -> None:
    assessment = assess_ordering(checkpoint_position=4, observed_sequence=5)
    assert assessment.decision is OrderingDecision.IN_ORDER
    require_in_order(assessment, consumer_name="c")


def test_a_skipped_sequence_is_a_detected_gap() -> None:
    assessment = assess_ordering(checkpoint_position=4, observed_sequence=7)
    assert assessment.decision is OrderingDecision.GAP_DETECTED
    assert assessment.reason_code == "EVENT_ORDERING_GAP_DETECTED"
    with pytest.raises(EventOrderingGapDetectedError):
        require_in_order(assessment, consumer_name="c")


def test_a_sequence_at_or_behind_the_checkpoint_is_out_of_order() -> None:
    assessment = assess_ordering(checkpoint_position=4, observed_sequence=4)
    assert assessment.decision is OrderingDecision.OUT_OF_ORDER
    with pytest.raises(EventOutOfOrderError):
        require_in_order(assessment, consumer_name="c")


def test_ordering_is_scoped_never_global() -> None:
    """`P13-ORD-001`: global total ordering is not promised and is not
    among the admissible scopes."""
    assert {k.value for k in OrderingScopeKind} == {
        "per_aggregate",
        "per_stream",
        "per_organization_and_aggregate",
    }


def test_a_per_aggregate_scope_names_its_aggregate() -> None:
    with pytest.raises(ValueError, match="names its aggregate"):
        OrderingScope(kind=OrderingScopeKind.PER_AGGREGATE)


def test_a_per_organization_scope_names_both() -> None:
    with pytest.raises(ValueError, match="names both"):
        OrderingScope(kind=OrderingScopeKind.PER_ORGANIZATION_AND_AGGREGATE, aggregate_id=uid(1))


def test_a_complete_ordering_scope_produces_a_stable_key() -> None:
    left = OrderingScope(
        kind=OrderingScopeKind.PER_ORGANIZATION_AND_AGGREGATE,
        aggregate_id=uid(1),
        organization_scope=scope(),
    )
    assert left.key == left.key
    assert str(scope().organization_id) in left.key


# ---------------------------------------------------------------------------
# Consumer checkpoints
# ---------------------------------------------------------------------------


def test_advancing_a_checkpoint_forward_is_an_ordinary_act() -> None:
    assert _checkpoint(3).advance_to(4, now=NOW).position == 4


def test_advancing_a_checkpoint_backwards_is_not_an_advance() -> None:
    with pytest.raises(EventOutOfOrderError):
        _checkpoint(4).advance_to(3, now=NOW)


def test_rewinding_a_checkpoint_requires_its_own_grant() -> None:
    """`P13-DEL-011`: moving a checkpoint backwards is a distinct,
    authorized operation."""
    with pytest.raises(EventReplayNotAuthorizedError):
        _checkpoint(4).rewind_to(2, grant=grant("event_replay"), now=NOW)


def test_a_correctly_scoped_grant_permits_a_rewind() -> None:
    rewound = _checkpoint(4).rewind_to(2, grant=grant("consumer_checkpoint_rewind"), now=NOW)
    assert rewound.position == 2


def test_a_rewind_must_move_backwards() -> None:
    with pytest.raises(ValueError, match="moves the checkpoint backwards"):
        _checkpoint(4).rewind_to(6, grant=grant("consumer_checkpoint_rewind"), now=NOW)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def test_an_available_broker_dispatches_now() -> None:
    decision = decide_dispatch(outbox_record(), policy=POLICY, now=NOW, broker_available=True)
    assert decision.action is DispatchAction.DISPATCH_NOW


def test_an_unavailable_broker_defers_with_a_backed_off_next_attempt() -> None:
    """§29: commands still commit; the backlog grows; publication is
    pending, not lost."""
    decision = decide_dispatch(outbox_record(), policy=POLICY, now=NOW, broker_available=False)
    assert decision.action is DispatchAction.DEFER
    assert decision.reason_code == "BROKER_UNAVAILABLE"
    assert decision.next_attempt_at == NOW + timedelta(seconds=10)


def test_a_deterministic_failure_dead_letters_rather_than_retrying_forever() -> None:
    decision = decide_dispatch(
        outbox_record(),
        policy=POLICY,
        now=NOW,
        broker_available=True,
        deterministic_failure_observed=True,
    )
    assert decision.action is DispatchAction.DEAD_LETTER
    assert decision.reason_code == "EVENT_POISON_MESSAGE"


def test_retry_is_bounded_and_terminates_in_dead_lettering() -> None:
    record = outbox_record().with_status(OutboxStatus.DISPATCHING)
    from epd2_data_plane_service.outbox import DeliveryAttempt, DeliveryOutcome

    for attempt in range(1, 4):
        record = record.with_attempt(
            DeliveryAttempt(
                attempt_number=attempt,
                started_at=NOW,
                outcome=DeliveryOutcome.TRANSIENT_FAILURE,
                destination=destination(),
            )
        )
    decision = decide_dispatch(record, policy=POLICY, now=NOW, broker_available=True)
    assert decision.action is DispatchAction.DEAD_LETTER
    assert decision.reason_code == "EVENT_DEAD_LETTER_REQUIRED"


def test_a_retry_policy_has_no_unbounded_value() -> None:
    with pytest.raises(ValueError, match="no unbounded value"):
        RetryPolicy(max_attempts=0, initial_backoff=timedelta(seconds=1))


def test_backoff_grows_with_the_attempt_number() -> None:
    assert POLICY.next_attempt_at(attempt_number=1, now=NOW) == NOW + timedelta(seconds=10)
    assert POLICY.next_attempt_at(attempt_number=3, now=NOW) == NOW + timedelta(seconds=40)


def test_a_successful_dispatch_records_publication_and_acknowledgement() -> None:
    result = _dispatcher(ReferenceBroker()).dispatch(outbox_record(), now=NOW)
    assert result.record.published
    assert result.record.acknowledged
    assert result.record.status is OutboxStatus.ACKNOWLEDGED
    assert result.record.attempt_count == 1


def test_a_missing_acknowledgement_is_unknown_not_success_and_not_failure() -> None:
    """`P13-DEL-007`."""
    result = _dispatcher(ReferenceBroker(acknowledge=False)).dispatch(outbox_record(), now=NOW)
    assert result.record.published
    assert not result.record.acknowledged
    assert result.record.status is OutboxStatus.PUBLISHED
    with pytest.raises(DeliveryAcknowledgementMissingError):
        require_acknowledged(result.record)


def test_an_unreachable_broker_raises_rather_than_marking_delivered() -> None:
    with pytest.raises(BrokerUnavailableError):
        _dispatcher(ReferenceBroker(available=False)).dispatch(outbox_record(), now=NOW)


def test_dead_lettering_requires_a_classification_and_a_retention_schedule() -> None:
    """`P13-DEL-009`: a dead-letter store is not a dumping ground."""
    with pytest.raises(EventDeadLetterRequiredError):
        _dispatcher(ReferenceBroker()).dispatch(
            outbox_record(), now=NOW, deterministic_failure=True
        )


def test_a_dead_lettered_record_preserves_its_failure_context() -> None:
    result = _dispatcher(ReferenceBroker()).dispatch(
        outbox_record(),
        now=NOW,
        deterministic_failure=True,
        classification=classification(),
        retention_schedule=retention(),
        dead_letter_id=uid(3300),
    )
    assert result.dead_letter is not None
    assert result.dead_letter.reason_code == "EVENT_POISON_MESSAGE"
    assert result.record.status is OutboxStatus.DEAD_LETTERED


def test_a_dead_letter_record_carries_a_reference_not_the_payload() -> None:
    """`P13-EVT-007`: the contents live in a classified,
    access-controlled store."""
    record = DeadLetterRecord(
        dead_letter_id=uid(3301),
        event_id=uid(1),
        event_type="projection.updated",
        reason_code="EVENT_POISON_MESSAGE",
        attempt_count=3,
        failed_at=NOW,
        classification=classification(),
        retention_schedule=retention(),
    )
    assert "payload" not in record.__slots__
    assert "envelope" not in record.__slots__
    assert record.review_required


def test_a_dead_letter_record_cannot_waive_its_review_obligation() -> None:
    with pytest.raises(ValueError, match="review obligation"):
        DeadLetterRecord(
            dead_letter_id=uid(3302),
            event_id=uid(1),
            event_type="projection.updated",
            reason_code="EVENT_POISON_MESSAGE",
            attempt_count=3,
            failed_at=NOW,
            classification=classification(),
            retention_schedule=retention(),
            review_required=False,
        )


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------


def test_a_first_delivery_is_applied_and_advances_the_checkpoint() -> None:
    consumer = _consumer()
    result = consumer.consume(outbox_record(sequence_number=1), checkpoint=_checkpoint(0), now=NOW)
    assert result.effect is ConsumerEffect.APPLIED
    assert result.checkpoint is not None
    assert result.checkpoint.position == 1


def test_a_duplicate_delivery_produces_no_second_effect() -> None:
    """`P13-DEL-004`: duplicate delivery is expected, detected and
    absorbed."""
    consumer = _consumer()
    record = outbox_record(sequence_number=1)
    consumer.consume(record, checkpoint=_checkpoint(0), now=NOW)
    second = consumer.consume(record, checkpoint=_checkpoint(1), now=NOW)
    assert second.effect is ConsumerEffect.SUPPRESSED_DUPLICATE
    assert second.reason_code == "EVENT_DUPLICATE_SUPPRESSED"
    assert consumer.applied_event_ids == [record.event_id]
    assert second.deduplication is not None
    assert second.deduplication.observation_count == 2


def test_the_consumer_effect_is_effectively_once_under_repeated_delivery() -> None:
    consumer = _consumer()
    record = outbox_record(sequence_number=1)
    for _ in range(5):
        consumer.consume(record, checkpoint=_checkpoint(0), now=NOW)
    assert len(consumer.applied_event_ids) == 1


def test_an_out_of_order_delivery_is_refused_not_silently_applied() -> None:
    consumer = _consumer()
    result = consumer.consume(
        outbox_record(n=2, sequence_number=5), checkpoint=_checkpoint(0), now=NOW
    )
    assert result.effect is ConsumerEffect.REFUSED
    assert result.reason_code == "EVENT_ORDERING_GAP_DETECTED"


def test_a_consequential_consumer_fails_closed_on_an_unsupported_version() -> None:
    """`P13-DEL-013`: it does not guess, does not skip, and does not
    apply a partial interpretation."""
    consumer = _consumer(versions=frozenset({"2.0"}))
    with pytest.raises(EventVersionUnsupportedError):
        consumer.consume(outbox_record(), checkpoint=_checkpoint(0), now=NOW)


def test_a_non_consequential_consumer_dead_letters_an_unsupported_version() -> None:
    consumer = _consumer(consequential=False, versions=frozenset({"2.0"}))
    result = consumer.consume(outbox_record(), checkpoint=_checkpoint(0), now=NOW)
    assert result.effect is ConsumerEffect.DEAD_LETTERED
    assert result.reason_code == "EVENT_VERSION_UNSUPPORTED"


def test_deduplication_precedes_the_version_check() -> None:
    """A version narrowing must not turn already-applied events into
    dead letters."""
    consumer = _consumer()
    record = outbox_record(sequence_number=1)
    consumer.consume(record, checkpoint=_checkpoint(0), now=NOW)
    consumer.supported_event_versions = frozenset({"9.9"})
    again = consumer.consume(record, checkpoint=_checkpoint(1), now=NOW)
    assert again.effect is ConsumerEffect.SUPPRESSED_DUPLICATE


def test_a_poison_event_is_detected_rather_than_retried_indefinitely() -> None:
    with pytest.raises(EventPoisonMessageError):
        _consumer().detect_poison(outbox_record(), failure_count=5, threshold=3)


def test_below_the_poison_threshold_nothing_is_raised() -> None:
    _consumer().detect_poison(outbox_record(), failure_count=1, threshold=3)


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def _replay(operation: str = "event_replay") -> ReplayReference:
    from _data_plane_builders import actor, evidence

    return ReplayReference(
        replay_id=uid(3400),
        requested_by=actor(),
        grant=grant(operation),
        ordering_scope_key="per_aggregate::x:None",
        from_sequence=1,
        to_sequence=10,
        requested_at=NOW,
        evidence=evidence(),
        reason_code="EVENT_REPLAY_NOT_AUTHORIZED",
    )


def test_a_replay_requires_a_grant_for_replay() -> None:
    with pytest.raises(EventReplayNotAuthorizedError):
        _replay(operation="migration_execution")


def test_an_authorized_replay_constructs_and_is_scoped_and_evidenced() -> None:
    replay = _replay()
    assert replay.from_sequence == 1
    assert replay.evidence.content_digest
    assert replay.ordering_scope_key


def test_a_replay_range_is_non_empty_and_ascending() -> None:
    from _data_plane_builders import actor, evidence

    with pytest.raises(ValueError, match="ascending"):
        ReplayReference(
            replay_id=uid(3401),
            requested_by=actor(),
            grant=grant("event_replay"),
            ordering_scope_key="k",
            from_sequence=5,
            to_sequence=2,
            requested_at=NOW,
            evidence=evidence(),
            reason_code="EVENT_REPLAY_NOT_AUTHORIZED",
        )


def test_a_replay_preserving_ids_and_sequence_preserves_history() -> None:
    """`P13-ORD-007`, `P13-DEL-010`."""
    original = [outbox_record(n=1, sequence_number=1), outbox_record(n=2, sequence_number=2)]
    assert replay_preserves_history(original, list(original))


def test_a_replay_that_renumbers_does_not_preserve_history() -> None:
    original = [outbox_record(n=1, sequence_number=1)]
    renumbered = [outbox_record(n=1, sequence_number=2)]
    assert not replay_preserves_history(original, renumbered)


def test_a_replay_that_mints_new_event_ids_does_not_preserve_history() -> None:
    original = [outbox_record(n=1, sequence_number=1)]
    reminted = [outbox_record(n=5, sequence_number=1)]
    assert not replay_preserves_history(original, reminted)


# ---------------------------------------------------------------------------
# Lag bands
# ---------------------------------------------------------------------------


def test_lag_is_reported_as_a_band_not_an_exact_figure() -> None:
    assert lag_band_for(0) == "none"
    assert lag_band_for(5) == "low"
    assert lag_band_for(50) == "moderate"
    assert lag_band_for(500) == "high"
    assert lag_band_for(50_000) == "severe"


def test_every_band_has_a_declared_range() -> None:
    assert set(LAG_BANDS) == {"none", "low", "moderate", "high", "severe"}


def test_a_negative_lag_is_refused() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        lag_band_for(-1)


def test_the_reference_broker_records_what_it_published() -> None:
    broker = ReferenceBroker()
    record = outbox_record()
    _dispatcher(broker).dispatch(record, now=NOW)
    assert broker.published == [record.event_id]


def test_a_consumer_checkpoint_position_is_never_negative() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        _checkpoint(-1)


def test_an_actor_reference_used_for_replay_is_domain_scoped() -> None:
    from _data_plane_builders import actor

    reference: ActorReference = actor(domain=CONSUMER_DOMAIN)
    assert reference.acting_domain.domain_name == "transparency-service"
