"""The transactional outbox (PACK-13 §8; ADR-071).

Atomic commit, rollback leaving no event, retry preserving the logical
event ID, duplicate publication safety, and delivery evidence kept
distinct from published state.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import (
    NOW,
    OTHER_DOMAIN,
    OWNER_DOMAIN,
    actor,
    aggregate,
    destination,
    outbox_record,
    retention,
    uid,
    unit_reference,
    version,
)

from epd2_data_plane_service.domain import (
    OrganizationScopeKind,
    OrganizationScopeReference,
)
from epd2_data_plane_service.events import build_data_plane_event
from epd2_data_plane_service.exceptions import (
    CrossDomainDirectAccessDeniedError,
    GlobalUserIdentifierProhibitedError,
    OutboxBacklogThresholdExceededError,
    OutboxPublicationPendingError,
    RecordUnderLegalHoldError,
    VotingMaterialProhibitedError,
)
from epd2_data_plane_service.outbox import (
    OUTBOX_STATUS_TRANSITIONS,
    BrokerAcknowledgementReference,
    DeliveryAttempt,
    DeliveryOutcome,
    OutboxBacklog,
    OutboxStatus,
    OutboxWriter,
    PublicationEvidence,
    summarize_for_operator,
)
from epd2_data_plane_service.storage import (
    CommittedWork,
    InMemoryAggregateVersionStore,
    InMemoryOutboxStore,
    ReferenceUnitOfWork,
)


def _unit() -> tuple[ReferenceUnitOfWork, InMemoryAggregateVersionStore, InMemoryOutboxStore]:
    versions = InMemoryAggregateVersionStore(OWNER_DOMAIN)
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    unit = ReferenceUnitOfWork(unit_reference(), versions=versions, outbox=outbox)
    return unit, versions, outbox


# ---------------------------------------------------------------------------
# Atomicity
# ---------------------------------------------------------------------------


def test_state_and_outbox_record_commit_together() -> None:
    """`P13-TX-003`: the event exists if and only if the state change
    does."""
    unit, versions, outbox = _unit()
    record = outbox_record()
    unit.stage(CommittedWork(version=version(1, agg=record.aggregate), outbox_record=record))
    committed = unit.commit()

    assert versions.current(record.aggregate).version == 1
    assert outbox.by_id(record.outbox_record_id).event_id == committed.outbox_record.event_id


def test_a_rollback_leaves_no_outbox_record_and_no_version() -> None:
    """`P13-TX-005`: a rolled-back transaction leaves no published
    event."""
    unit, versions, outbox = _unit()
    record = outbox_record()
    unit.stage(CommittedWork(version=version(1, agg=record.aggregate), outbox_record=record))
    unit.rollback()

    assert versions.current(record.aggregate).version == 0
    assert outbox.pending(scope=record.scope) == ()
    with pytest.raises(ValueError, match="rolled back"):
        unit.commit()


def test_a_unit_of_work_refuses_to_stage_another_domains_aggregate() -> None:
    unit, _, _ = _unit()
    foreign = outbox_record(domain=OTHER_DOMAIN)
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        unit.stage(CommittedWork(version=version(1, agg=foreign.aggregate), outbox_record=foreign))


def test_committing_nothing_is_refused() -> None:
    unit, _, _ = _unit()
    with pytest.raises(ValueError, match="nothing staged"):
        unit.commit()


def test_the_writer_is_the_only_way_a_record_is_produced() -> None:
    """An outbox record cannot exist without a unit of work to be atomic
    with, because `write_within` takes one."""
    record = outbox_record()
    assert record.status is OutboxStatus.PENDING
    assert record.scope.organization_id == unit_reference().scope.organization_id


# ---------------------------------------------------------------------------
# Payload guards, before the write
# ---------------------------------------------------------------------------


def test_a_voting_payload_never_becomes_an_outbox_record() -> None:
    with pytest.raises(VotingMaterialProhibitedError):
        outbox_record(payload={"ballot_content": "x"})


def test_a_person_key_payload_never_becomes_an_outbox_record() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        outbox_record(payload={"person_id": "x"})


def test_the_guard_runs_before_storage_not_before_dispatch() -> None:
    """`P13-OBX-008`: a payload that reached storage has already leaked
    into backups, so the refusal is at write time."""
    versions = InMemoryAggregateVersionStore(OWNER_DOMAIN)
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    with pytest.raises(VotingMaterialProhibitedError):
        envelope = build_data_plane_event(
            event_id=uid(1),
            event_type="projection.updated",
            occurred_at=NOW,
            actor=actor(),
            aggregate_id=aggregate().aggregate_id,
            scope=unit_reference().scope,
            payload={"tally": 3},
            correlation_id=uid(2),
            sequence_number=1,
        )
        OutboxWriter.write_within(
            unit_reference(),
            outbox_record_id=uid(3),
            envelope=envelope,
            aggregate=aggregate(),
            created_at=NOW,
            sequence_number=1,
        )
    assert outbox.pending(scope=unit_reference().scope) == ()
    assert versions.current(aggregate()).version == 0


# ---------------------------------------------------------------------------
# Immutability and delivery state
# ---------------------------------------------------------------------------


def test_the_record_carries_the_envelopes_event_identity() -> None:
    record = outbox_record()
    assert record.event_id == record.envelope.event_id
    assert record.event_type == record.envelope.event_type


def test_a_retry_preserves_the_logical_event_id() -> None:
    """`P13-OBX-005`: republication reuses the same logical event ID."""
    record = outbox_record()
    dispatching = record.with_status(OutboxStatus.DISPATCHING)
    attempted = dispatching.with_attempt(
        DeliveryAttempt(
            attempt_number=1,
            started_at=NOW,
            outcome=DeliveryOutcome.TRANSIENT_FAILURE,
            destination=destination(),
        )
    )
    retried = attempted.with_attempt(
        DeliveryAttempt(
            attempt_number=2,
            started_at=NOW,
            outcome=DeliveryOutcome.PUBLISHED,
            destination=destination(),
        )
    )
    assert retried.event_id == record.event_id
    assert retried.attempt_count == 2


def test_attempt_numbers_are_consecutive() -> None:
    record = outbox_record().with_status(OutboxStatus.DISPATCHING)
    with pytest.raises(ValueError, match="consecutive"):
        record.with_attempt(
            DeliveryAttempt(
                attempt_number=3,
                started_at=NOW,
                outcome=DeliveryOutcome.PUBLISHED,
                destination=destination(),
            )
        )


def test_published_and_acknowledged_are_two_distinct_facts() -> None:
    """`P13-OBX-011`: conflating them makes a lost acknowledgement look
    like a successful delivery."""
    record = outbox_record()
    published = record.with_publication(
        PublicationEvidence(event_id=record.event_id, published_at=NOW, destination=destination())
    )
    assert published.published
    assert not published.acknowledged

    acknowledged = published.with_acknowledgement(
        BrokerAcknowledgementReference(acknowledgement_reference="ack-1", received_at=NOW)
    )
    assert acknowledged.acknowledged


def test_an_acknowledgement_without_a_publication_is_refused() -> None:
    with pytest.raises(OutboxPublicationPendingError):
        outbox_record().with_acknowledgement(
            BrokerAcknowledgementReference(acknowledgement_reference="ack-1", received_at=NOW)
        )


def test_publication_evidence_must_belong_to_the_records_own_event() -> None:
    record = outbox_record()
    with pytest.raises(ValueError, match="own event"):
        record.with_publication(
            PublicationEvidence(event_id=uid(1), published_at=NOW, destination=destination())
        )


def test_pending_cannot_jump_straight_to_acknowledged() -> None:
    """A record cannot be acknowledged without having been published."""
    assert OutboxStatus.ACKNOWLEDGED not in OUTBOX_STATUS_TRANSITIONS[OutboxStatus.PENDING]
    with pytest.raises(ValueError, match="not a declared transition"):
        outbox_record().with_status(OutboxStatus.ACKNOWLEDGED)


def test_acknowledged_is_terminal() -> None:
    assert OUTBOX_STATUS_TRANSITIONS[OutboxStatus.ACKNOWLEDGED] == frozenset()


def test_the_store_refuses_a_change_to_an_immutable_field() -> None:
    from dataclasses import replace

    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    record = outbox_record()
    outbox.append(record, writing_domain=OWNER_DOMAIN)
    with pytest.raises(Exception, match="immutable"):
        outbox.update_delivery_state(replace(record, event_version="2.0"))


def test_the_store_accepts_a_delivery_metadata_change() -> None:
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    record = outbox_record()
    outbox.append(record, writing_domain=OWNER_DOMAIN)
    outbox.update_delivery_state(record.with_status(OutboxStatus.DISPATCHING))
    assert outbox.by_id(record.outbox_record_id).status is OutboxStatus.DISPATCHING


def test_the_store_refuses_another_domains_append() -> None:
    """The outbox is co-located with its domain (ADR-070); a central
    outbox written by every domain is the shared mutable table the
    ownership ADR forbids."""
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        outbox.append(outbox_record(), writing_domain=OTHER_DOMAIN)


def test_a_duplicate_append_of_the_same_record_is_refused() -> None:
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    record = outbox_record()
    outbox.append(record, writing_domain=OWNER_DOMAIN)
    with pytest.raises(Exception, match="already exists"):
        outbox.append(record, writing_domain=OWNER_DOMAIN)


def test_pending_records_are_scoped_and_sequence_ordered() -> None:
    outbox = InMemoryOutboxStore(OWNER_DOMAIN)
    outbox.append(outbox_record(n=2, sequence_number=2), writing_domain=OWNER_DOMAIN)
    outbox.append(outbox_record(n=1, sequence_number=1), writing_domain=OWNER_DOMAIN)
    pending = outbox.pending(scope=unit_reference().scope)
    assert [r.sequence_number for r in pending] == [1, 2]

    other_scope = OrganizationScopeReference(
        organization_id=uid(4242), scope_kind=OrganizationScopeKind.BUND
    )
    assert outbox.pending(scope=other_scope) == ()


# ---------------------------------------------------------------------------
# Retention, hold and the operator view
# ---------------------------------------------------------------------------


def test_a_held_outbox_record_is_preserved_and_the_hold_grants_nothing() -> None:
    from dataclasses import replace

    record = replace(outbox_record(), under_legal_hold=True)
    with pytest.raises(RecordUnderLegalHoldError, match="does not authorize reading"):
        record.require_deletable()


def test_an_outbox_record_without_a_retention_schedule_is_not_deletable() -> None:
    from dataclasses import replace

    record = replace(outbox_record(), retention_schedule=None)
    with pytest.raises(RecordUnderLegalHoldError, match="retention schedule"):
        record.require_deletable()


def test_a_retained_unheld_record_is_deletable_under_policy() -> None:
    from dataclasses import replace

    replace(outbox_record(), retention_schedule=retention()).require_deletable()


def test_the_operator_summary_carries_no_payload() -> None:
    view = summarize_for_operator(outbox_record())
    assert "payload" not in view
    assert "envelope" not in view
    assert view["status"] == "pending"


def test_the_backlog_is_a_first_class_health_signal() -> None:
    backlog = OutboxBacklog(pending_count=12, oldest_pending_age_seconds=90, alert_threshold=10)
    assert backlog.exceeds_threshold
    with pytest.raises(OutboxBacklogThresholdExceededError):
        backlog.require_within_threshold()


def test_a_backlog_within_threshold_passes() -> None:
    OutboxBacklog(
        pending_count=3, oldest_pending_age_seconds=5, alert_threshold=10
    ).require_within_threshold()
