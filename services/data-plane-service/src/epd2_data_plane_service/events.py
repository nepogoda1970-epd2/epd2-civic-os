"""Canonical events emitted by the Data Plane Service (PACK-13 Event
Catalog).

**Thirty-seven event types in four families, no more and no fewer.**
Names carry the **aggregate prefix**, never a service or pack prefix
(`P13-EVT-002`): `schema_version.approved`, never
`pack13.schema_approved`.

The envelope from canon §21 is used **unchanged** (`P13-EVT-001`,
`P13-OBX-004`). PACK-13 adds no envelope field, removes none and
reinterprets none — every piece of transport metadata (attempt counts,
broker references, dispatch timestamps) lives on the outbox record
instead. That is the specific decision that keeps this pack
canon-neutral (ADR-071).

Every payload is minimal (`P13-EVT-003`): identifiers, enum values,
timestamps, one reason code, version and policy references, opaque
references. Four things are deliberately absent from every payload in
this module:

- **No schema body** (`P13-EVT-005`) — the digest and the reference
  travel, never the document.
- **No migrated data** (`P13-EVT-006`) — counts and references, never
  rows.
- **No failed payload** (`P13-EVT-007`) — a dead-letter event carries a
  reference to the dead-lettered record, not its contents.
- **No query text, no personal data, no secrets** (`P13-EVT-008`).

Every assembled payload passes `reject_prohibited_payload_keys` before an
envelope exists, so a future builder that reaches for a secret, a person
key or a tally fails closed rather than shipping it.

**`PUBLIC_PROJECTION_ALLOWED` is empty** (`P13-EVT-004`). Every event
here describes internal data-plane machinery — schema governance,
migration, delivery, projection health. None is public information, and
an empty set is the honest answer rather than an oversight.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import (
    ActorRef,
    EventEnvelope,
    SubjectRef,
    build_event_envelope,
)
from epd2_data_plane_service.domain import (
    ActorReference,
    OrganizationScopeReference,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.exceptions import EventVersionUnsupportedError

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})
_PRODUCER = "data-plane-service"

DATA_PLANE_EVENT_TYPES: tuple[str, ...] = (
    # schema registry - 9
    "schema_version.proposed",
    "schema_version.compatibility_assessed",
    "schema_version.approved",
    "schema_version.activated",
    "schema_version.deprecated",
    "schema_version.retired",
    "schema_version.superseded",
    "schema_consumer.registered",
    "schema_consumer.incompatibility_detected",
    # migration - 11
    "migration.planned",
    "migration.approved",
    "migration.started",
    "migration.checkpointed",
    "migration.completed",
    "migration.failed",
    "migration.rollback_initiated",
    "migration.rollback_completed",
    "migration.verification_completed",
    "data_backfill.started",
    "data_backfill.completed",
    # outbox and delivery - 10
    "outbox_record.created",
    "outbox_record.dispatch_attempted",
    "outbox_record.published",
    "outbox_record.acknowledgement_received",
    "outbox_record.retry_scheduled",
    "outbox_record.dead_lettered",
    "event_replay.requested",
    "event_replay.completed",
    "consumer_checkpoint.advanced",
    "event_delivery.gap_detected",
    # projection - 7
    "projection.update_requested",
    "projection.updated",
    "projection.lag_detected",
    "projection.rebuild_started",
    "projection.rebuild_completed",
    "projection.deletion_propagated",
    "projection.tombstone_applied",
)

_EVENT_TYPE_SET: frozenset[str] = frozenset(DATA_PLANE_EVENT_TYPES)

#: The aggregate each event prefix belongs to, per the event catalog's own
#: tables. `event_delivery.gap_detected` maps to `consumer_checkpoint`
#: because the catalog assigns it there: the gap is a fact about a
#: consumer's position, not about a separate aggregate.
EVENT_AGGREGATE_BY_PREFIX: Mapping[str, str] = {
    "schema_version": "schema_version",
    "schema_consumer": "schema_consumer",
    "migration": "migration_execution",
    "data_backfill": "data_backfill",
    "outbox_record": "outbox_record",
    "event_replay": "event_replay",
    "consumer_checkpoint": "consumer_checkpoint",
    "event_delivery": "consumer_checkpoint",
    "projection": "projection",
}

#: Deliberately empty (`P13-EVT-004`).
PUBLIC_PROJECTION_ALLOWED: frozenset[str] = frozenset()


#: The `*_RECORDED` classification each event's audit row carries.
#: Canon §24 is refusal-only, and an act that *succeeds* still needs a
#: registered classification for its audit row — the same gap ADR-004
#: recorded for PACK-02 and `P13-RSN-006` restates here. Derived
#: mechanically from the event name so the two can never drift.
def recorded_reason_code_for(event_type: str) -> str:
    """The registered `*_RECORDED` code for a successfully-audited act."""
    assert_known_event_type(event_type)
    return f"{event_type.replace('.', '_').upper()}_RECORDED"


DATA_PLANE_RECORDED_REASON_CODES: tuple[str, ...] = tuple(
    f"{event_type.replace('.', '_').upper()}_RECORDED" for event_type in DATA_PLANE_EVENT_TYPES
)


def aggregate_for(event_type: str) -> str:
    prefix = event_type.split(".", 1)[0]
    aggregate = EVENT_AGGREGATE_BY_PREFIX.get(prefix)
    if aggregate is None:
        raise EventVersionUnsupportedError(f"unknown PACK-13 event prefix {prefix!r}")
    return aggregate


def assert_known_event_type(event_type: str) -> None:
    if event_type not in _EVENT_TYPE_SET:
        raise EventVersionUnsupportedError(f"unknown PACK-13 event type {event_type!r}")


def to_actor_ref(actor: ActorReference) -> ActorRef:
    """Project this package's scoped actor reference onto the canon's
    envelope `actor` object.

    The acting *domain* is folded into `actor_type` rather than dropped,
    because the envelope has no domain field and a bare actor ID would be
    exactly the un-scoped reference `P13-ID-003` forbids."""
    return ActorRef(
        actor_id=actor.actor_id,
        actor_type=f"{actor.acting_domain.domain_name}:{actor.actor_type}",
    )


def build_data_plane_event(
    *,
    event_id: UUID,
    event_type: str,
    occurred_at: datetime,
    actor: ActorReference,
    aggregate_id: UUID,
    scope: OrganizationScopeReference,
    payload: Mapping[str, object],
    correlation_id: UUID,
    sequence_number: int,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    """Build one canonical envelope.

    Three pieces of mandatory metadata are added here rather than by
    thirty-seven hand-written copies, so no builder can forget one: the
    organizational scope (`P13-CTX-002`), the stable aggregate identifier,
    and the **explicit sequence number** every event carries within its
    ordering scope (`P13-ORD-003`).

    The payload guard runs before the envelope exists: a payload that
    would carry a secret, a person key or ballot material never becomes an
    event, not even briefly."""
    assert_known_event_type(event_type)
    require_timezone(occurred_at, field="build_data_plane_event.occurred_at")
    if sequence_number < 1:
        raise ValueError("sequence_number starts at 1 within its ordering scope")
    body: dict[str, object] = dict(payload)
    body["organization_id"] = str(scope.organization_id)
    body["organization_scope_kind"] = scope.scope_kind.value
    body["aggregate_id"] = str(aggregate_id)
    body["sequence_number"] = sequence_number
    reject_prohibited_payload_keys(body, context=f"event {event_type}")
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=to_actor_ref(actor),
        subject=SubjectRef(subject_type=aggregate_for(event_type), subject_id=aggregate_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=body,
    )


# ---------------------------------------------------------------------------
# Schema registry payloads
# ---------------------------------------------------------------------------


def schema_version_proposed_payload(
    *,
    schema_version_id: UUID,
    family_name: str,
    version_label: str,
    owner_domain: str,
    schema_format: str,
    content_digest: str,
) -> dict[str, object]:
    """Carries the canonical digest and the reference — never the schema
    document (`P13-EVT-005`)."""
    return {
        "schema_version_id": str(schema_version_id),
        "family_name": family_name,
        "version_label": version_label,
        "owner_domain": owner_domain,
        "schema_format": schema_format,
        "content_digest": content_digest,
    }


def compatibility_assessed_payload(
    *,
    assessment_id: UUID,
    automated_verdict: str,
    human_verdict: str | None,
    declared_mode: str,
    reviewer_reference: str | None,
) -> dict[str, object]:
    """The automated and human verdicts stay separate fields (ADR-074);
    a payload that merged them would lose the fact that a reviewer
    disagreed."""
    return {
        "assessment_id": str(assessment_id),
        "automated_verdict": automated_verdict,
        "human_verdict": human_verdict,
        "declared_compatibility_mode": declared_mode,
        "reviewer_reference": reviewer_reference,
    }


def schema_version_approved_payload(
    *, approval_reference: UUID, approver_reference: str, compatibility_mode: str
) -> dict[str, object]:
    return {
        "approval_reference": str(approval_reference),
        "approver_reference": approver_reference,
        "compatibility_mode": compatibility_mode,
    }


def schema_version_activated_payload(
    *, effective_at: str, superseded_version_reference: str | None
) -> dict[str, object]:
    return {
        "effective_at": effective_at,
        "superseded_version_reference": superseded_version_reference,
    }


def schema_version_deprecated_payload(
    *, deprecated_at: str, replacement_reference: str | None, coexistence_ends_at: str
) -> dict[str, object]:
    return {
        "deprecated_at": deprecated_at,
        "replacement_reference": replacement_reference,
        "coexistence_ends_at": coexistence_ends_at,
    }


def schema_version_retired_payload(*, retired_at: str, reason_code: str) -> dict[str, object]:
    return {"retired_at": retired_at, "reason_code": reason_code}


def schema_version_superseded_payload(
    *, superseding_version_reference: str, reason_code: str
) -> dict[str, object]:
    return {
        "superseding_version_reference": superseding_version_reference,
        "reason_code": reason_code,
    }


def schema_consumer_registered_payload(
    *, consumer_reference: str, supported_version_ids: tuple[str, ...], consumer_domain: str
) -> dict[str, object]:
    return {
        "consumer_reference": consumer_reference,
        "supported_version_ids": sorted(supported_version_ids),
        "consumer_domain": consumer_domain,
    }


def schema_consumer_incompatibility_payload(
    *, consumer_reference: str, schema_version_id: UUID, reason_code: str
) -> dict[str, object]:
    return {
        "consumer_reference": consumer_reference,
        "schema_version_id": str(schema_version_id),
        "reason_code": reason_code,
    }


# ---------------------------------------------------------------------------
# Migration payloads
# ---------------------------------------------------------------------------


def migration_planned_payload(
    *,
    plan_id: UUID,
    migration_ids: tuple[str, ...],
    migration_class: str,
    target_schemas: tuple[str, ...],
    owner_domain: str,
) -> dict[str, object]:
    return {
        "plan_id": str(plan_id),
        "migration_ids": sorted(migration_ids),
        "migration_class": migration_class,
        "target_schemas": sorted(target_schemas),
        "owner_domain": owner_domain,
    }


def migration_approved_payload(
    *, approver_reference: str, separation_of_duties_evaluation_reference: str
) -> dict[str, object]:
    return {
        "approver_reference": approver_reference,
        "separation_of_duties_evaluation_reference": (separation_of_duties_evaluation_reference),
    }


def migration_started_payload(
    *, execution_id: UUID, plan_id: UUID, privileged_grant_reference: str
) -> dict[str, object]:
    return {
        "execution_id": str(execution_id),
        "plan_id": str(plan_id),
        "privileged_grant_reference": privileged_grant_reference,
    }


def migration_checkpointed_payload(
    *, checkpoint_id: UUID, position: int, records_processed: int
) -> dict[str, object]:
    """Counts and references, never rows (`P13-EVT-006`)."""
    return {
        "checkpoint_id": str(checkpoint_id),
        "position": position,
        "records_processed": records_processed,
    }


def migration_completed_payload(
    *, duration_seconds: int, records_affected: int, verification_reference: str
) -> dict[str, object]:
    return {
        "duration_seconds": duration_seconds,
        "records_affected": records_affected,
        "verification_reference": verification_reference,
    }


def migration_failed_payload(
    *, failure_position: int, reason_code: str, state_preserved: bool
) -> dict[str, object]:
    return {
        "failure_position": failure_position,
        "reason_code": reason_code,
        "state_preserved": state_preserved,
    }


def migration_rollback_initiated_payload(
    *, rollback_decision_reference: str, reason_code: str
) -> dict[str, object]:
    return {
        "rollback_decision_reference": rollback_decision_reference,
        "reason_code": reason_code,
    }


def migration_rollback_completed_payload(
    *, outcome: str, residual_state_reference: str | None
) -> dict[str, object]:
    return {"outcome": outcome, "residual_state_reference": residual_state_reference}


def migration_verification_completed_payload(
    *, verification_id: UUID, outcome: str, evidence_reference: str
) -> dict[str, object]:
    return {
        "verification_id": str(verification_id),
        "outcome": outcome,
        "evidence_reference": evidence_reference,
    }


def data_backfill_started_payload(
    *, backfill_id: UUID, scope_reference: str, rate_limit: int, batch_size: int
) -> dict[str, object]:
    return {
        "backfill_id": str(backfill_id),
        "scope_reference": scope_reference,
        "rate_limit": rate_limit,
        "batch_size": batch_size,
    }


def data_backfill_completed_payload(
    *,
    processed: int,
    succeeded: int,
    routed_to_review: int,
    failed: int,
    reconciliation_report_reference: str,
) -> dict[str, object]:
    """Routed-to-review is reported, never omitted: a backfill that
    completed silently would look identical to one that resolved
    everything (`P13-BF-012`)."""
    return {
        "processed": processed,
        "succeeded": succeeded,
        "routed_to_review": routed_to_review,
        "failed": failed,
        "reconciliation_report_reference": reconciliation_report_reference,
    }


# ---------------------------------------------------------------------------
# Outbox and delivery payloads
# ---------------------------------------------------------------------------


def outbox_record_created_payload(
    *,
    outbox_record_id: UUID,
    published_event_id: UUID,
    published_event_type: str,
    published_event_version: str,
) -> dict[str, object]:
    """Names the *published* event by ID and type only.

    The field names carry the `published_` prefix so that this event's
    own envelope fields and the record's subject event can never be
    confused by a consumer reading the payload."""
    return {
        "outbox_record_id": str(outbox_record_id),
        "published_event_id": str(published_event_id),
        "published_event_type": published_event_type,
        "published_event_version": published_event_version,
    }


def dispatch_attempted_payload(
    *, attempt_number: int, destination_reference: str
) -> dict[str, object]:
    return {"attempt_number": attempt_number, "destination_reference": destination_reference}


def outbox_published_payload(*, published_at: str, destination_reference: str) -> dict[str, object]:
    return {"published_at": published_at, "destination_reference": destination_reference}


def acknowledgement_received_payload(*, broker_acknowledgement_reference: str) -> dict[str, object]:
    return {"broker_acknowledgement_reference": broker_acknowledgement_reference}


def retry_scheduled_payload(
    *, attempt_number: int, next_attempt_at: str, reason_code: str
) -> dict[str, object]:
    return {
        "attempt_number": attempt_number,
        "next_attempt_at": next_attempt_at,
        "reason_code": reason_code,
    }


def dead_lettered_payload(
    *, reason_code: str, attempt_count: int, failure_reference: str
) -> dict[str, object]:
    """A reference to the dead-lettered record, not its contents
    (`P13-EVT-007`). The contents live in a classified,
    access-controlled store (`P13-DEL-014`)."""
    return {
        "reason_code": reason_code,
        "attempt_count": attempt_count,
        "failure_reference": failure_reference,
    }


def replay_requested_payload(
    *, replay_id: UUID, ordering_scope_key: str, authority_reference: str, reason_code: str
) -> dict[str, object]:
    return {
        "replay_id": str(replay_id),
        "ordering_scope_key": ordering_scope_key,
        "authority_reference": authority_reference,
        "reason_code": reason_code,
    }


def replay_completed_payload(
    *, replay_id: UUID, events_replayed: int, outcome: str
) -> dict[str, object]:
    return {
        "replay_id": str(replay_id),
        "events_replayed": events_replayed,
        "outcome": outcome,
    }


def checkpoint_advanced_payload(
    *, consumer_reference: str, position: int, previous_position: int
) -> dict[str, object]:
    return {
        "consumer_reference": consumer_reference,
        "position": position,
        "previous_position": previous_position,
    }


def gap_detected_payload(
    *,
    consumer_reference: str,
    ordering_scope_key: str,
    expected_sequence: int,
    observed_sequence: int,
) -> dict[str, object]:
    return {
        "consumer_reference": consumer_reference,
        "ordering_scope_key": ordering_scope_key,
        "expected_sequence": expected_sequence,
        "observed_sequence": observed_sequence,
    }


# ---------------------------------------------------------------------------
# Projection payloads
# ---------------------------------------------------------------------------


def projection_update_requested_payload(
    *, projection_id: UUID, source_event_reference: str
) -> dict[str, object]:
    return {
        "projection_id": str(projection_id),
        "source_event_reference": source_event_reference,
    }


def projection_updated_payload(
    *, projection_id: UUID, position: int, schema_version_id: UUID
) -> dict[str, object]:
    return {
        "projection_id": str(projection_id),
        "position": position,
        "schema_version_id": str(schema_version_id),
    }


def projection_lag_detected_payload(
    *, projection_id: UUID, lag_band: str, threshold_reference: str
) -> dict[str, object]:
    """Reports a **band, not an exact lag** (`P13-EVT-009`), for the same
    reason PACK-12 reports suppression bands: an exact figure across
    organizations is itself information."""
    return {
        "projection_id": str(projection_id),
        "lag_band": lag_band,
        "threshold_reference": threshold_reference,
    }


def projection_rebuild_started_payload(
    *, rebuild_id: UUID, source_range: str, authority_reference: str
) -> dict[str, object]:
    return {
        "rebuild_id": str(rebuild_id),
        "source_range": source_range,
        "authority_reference": authority_reference,
    }


def projection_rebuild_completed_payload(
    *, rebuild_id: UUID, outcome: str, records_rebuilt: int
) -> dict[str, object]:
    return {
        "rebuild_id": str(rebuild_id),
        "outcome": outcome,
        "records_rebuilt": records_rebuilt,
    }


def projection_deletion_propagated_payload(
    *, source_record_reference: str, propagation_outcome: str
) -> dict[str, object]:
    return {
        "source_record_reference": source_record_reference,
        "propagation_outcome": propagation_outcome,
    }


def projection_tombstone_applied_payload(
    *, tombstone_reference: str, source_decision_reference: str
) -> dict[str, object]:
    return {
        "tombstone_reference": tombstone_reference,
        "source_decision_reference": source_decision_reference,
    }
