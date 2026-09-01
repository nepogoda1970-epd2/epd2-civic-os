"""The thirty-seven canonical events (PACK-13 Event Catalog).

The envelope is canon §21's, unchanged. Names carry the aggregate prefix.
Every payload is minimal, and four things are absent from all of them:
the schema body, migrated rows, the failed payload, and any query text,
personal data or secret.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from _data_plane_builders import NOW, OWNER_DOMAIN, actor, scope, uid

from epd2_core.event_envelope import EventEnvelope, parse_major_version
from epd2_data_plane_service.events import (
    DATA_PLANE_EVENT_TYPES,
    DATA_PLANE_RECORDED_REASON_CODES,
    EVENT_AGGREGATE_BY_PREFIX,
    EVENT_VERSION,
    PUBLIC_PROJECTION_ALLOWED,
    SUPPORTED_MAJOR_VERSIONS,
    aggregate_for,
    assert_known_event_type,
    build_data_plane_event,
    compatibility_assessed_payload,
    data_backfill_completed_payload,
    dead_lettered_payload,
    migration_checkpointed_payload,
    projection_lag_detected_payload,
    recorded_reason_code_for,
    schema_version_proposed_payload,
    to_actor_ref,
)
from epd2_data_plane_service.exceptions import (
    EventVersionUnsupportedError,
    GlobalUserIdentifierProhibitedError,
    VotingMaterialProhibitedError,
)


def _envelope(
    event_type: str = "schema_version.approved",
    payload: Mapping[str, object] | None = None,
    sequence: int = 1,
) -> EventEnvelope:
    return build_data_plane_event(
        event_id=uid(10001),
        event_type=event_type,
        occurred_at=NOW,
        actor=actor(),
        aggregate_id=uid(10002),
        scope=scope(),
        payload=payload or {"approval_reference": str(uid(1))},
        correlation_id=uid(10003),
        sequence_number=sequence,
    )


# ---------------------------------------------------------------------------
# The catalog
# ---------------------------------------------------------------------------


def test_there_are_exactly_thirty_seven_event_types() -> None:
    assert len(DATA_PLANE_EVENT_TYPES) == 37
    assert len(set(DATA_PLANE_EVENT_TYPES)) == 37


def test_the_four_families_have_their_declared_counts() -> None:
    counts = {"schema": 0, "migration": 0, "delivery": 0, "projection": 0}
    for event_type in DATA_PLANE_EVENT_TYPES:
        prefix = event_type.split(".", 1)[0]
        if prefix in ("schema_version", "schema_consumer"):
            counts["schema"] += 1
        elif prefix in ("migration", "data_backfill"):
            counts["migration"] += 1
        elif prefix in ("outbox_record", "event_replay", "consumer_checkpoint", "event_delivery"):
            counts["delivery"] += 1
        else:
            counts["projection"] += 1
    assert counts == {"schema": 9, "migration": 11, "delivery": 10, "projection": 7}


def test_every_name_carries_an_aggregate_prefix_never_a_pack_prefix() -> None:
    """`P13-EVT-002`: `schema_version.approved`, never
    `pack13.schema_approved`."""
    for event_type in DATA_PLANE_EVENT_TYPES:
        prefix, _, suffix = event_type.partition(".")
        assert suffix, event_type
        assert prefix in EVENT_AGGREGATE_BY_PREFIX
        assert not prefix.startswith("pack")


def test_every_event_type_resolves_to_an_aggregate() -> None:
    for event_type in DATA_PLANE_EVENT_TYPES:
        assert aggregate_for(event_type)


def test_an_unknown_event_type_is_refused() -> None:
    with pytest.raises(EventVersionUnsupportedError):
        assert_known_event_type("pack13.something")


def test_an_unknown_prefix_is_refused() -> None:
    with pytest.raises(EventVersionUnsupportedError):
        aggregate_for("unknown_aggregate.happened")


def test_the_public_projection_allowance_is_empty() -> None:
    """`P13-EVT-004`: every event here describes internal data-plane
    machinery, and an empty set is the honest answer."""
    assert frozenset() == PUBLIC_PROJECTION_ALLOWED


# ---------------------------------------------------------------------------
# The envelope
# ---------------------------------------------------------------------------


def test_the_envelope_is_the_canons_and_pack_13_adds_no_field() -> None:
    """`P13-EVT-001`, `P13-OBX-004`."""
    envelope = _envelope()
    assert envelope.event_version == EVENT_VERSION
    assert parse_major_version(envelope.event_version) in SUPPORTED_MAJOR_VERSIONS
    assert set(envelope.__slots__) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "producer",
        "actor",
        "subject",
        "correlation_id",
        "causation_id",
        "payload",
        "integrity",
    }


def test_transport_metadata_stays_off_the_envelope() -> None:
    """ADR-071: attempt counts, broker references and dispatch
    timestamps live on the outbox record, which is what keeps this pack
    canon-neutral."""
    envelope = _envelope()
    for forbidden in ("attempt_count", "destination", "acknowledgement", "status"):
        assert forbidden not in envelope.__slots__
        assert forbidden not in envelope.payload


def test_every_envelope_carries_scope_aggregate_and_sequence() -> None:
    """`P13-CTX-002`, `P13-ORD-003`."""
    envelope = _envelope(sequence=4)
    assert envelope.payload["organization_id"] == str(scope().organization_id)
    assert envelope.payload["organization_scope_kind"] == scope().scope_kind.value
    assert envelope.payload["aggregate_id"] == str(uid(10002))
    assert envelope.payload["sequence_number"] == 4


def test_a_sequence_number_starts_at_one() -> None:
    with pytest.raises(ValueError, match="starts at 1"):
        _envelope(sequence=0)


def test_the_actor_reference_carries_its_acting_domain() -> None:
    """`P13-ID-003`: a bare actor ID would be the un-scoped reference the
    identity boundary forbids."""
    reference = to_actor_ref(actor(domain=OWNER_DOMAIN))
    assert reference.actor_type.startswith("membership-service:")


def test_the_payload_hash_is_deterministic() -> None:
    assert _envelope().integrity.payload_hash == _envelope().integrity.payload_hash


def test_a_voting_payload_never_becomes_an_event() -> None:
    with pytest.raises(VotingMaterialProhibitedError):
        _envelope(payload={"ballot_id": "x"})


def test_a_person_key_payload_never_becomes_an_event() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        _envelope(payload={"email": "a@b.c"})


def test_a_naive_timestamp_is_refused() -> None:
    from datetime import datetime

    with pytest.raises(ValueError, match="timezone-aware"):
        build_data_plane_event(
            event_id=uid(1),
            event_type="schema_version.approved",
            occurred_at=datetime(2026, 1, 1),
            actor=actor(),
            aggregate_id=uid(2),
            scope=scope(),
            payload={},
            correlation_id=uid(3),
            sequence_number=1,
        )


# ---------------------------------------------------------------------------
# Payload minimisation
# ---------------------------------------------------------------------------


def test_a_schema_event_carries_the_digest_never_the_document() -> None:
    """`P13-EVT-005`."""
    payload = schema_version_proposed_payload(
        schema_version_id=uid(1),
        family_name="membership.record",
        version_label="1.0.0",
        owner_domain="membership-service",
        schema_format="json_schema",
        content_digest="a" * 64,
    )
    assert payload["content_digest"] == "a" * 64
    assert "schema_body" not in payload
    assert "schema_document" not in payload


def test_a_migration_event_carries_counts_never_rows() -> None:
    """`P13-EVT-006`."""
    payload = migration_checkpointed_payload(
        checkpoint_id=uid(1), position=4, records_processed=1000
    )
    assert payload["records_processed"] == 1000
    assert "rows" not in payload
    assert "row_data" not in payload


def test_a_dead_letter_event_carries_a_reference_never_the_contents() -> None:
    """`P13-EVT-007`."""
    payload = dead_lettered_payload(
        reason_code="EVENT_POISON_MESSAGE", attempt_count=3, failure_reference="dl-1"
    )
    assert payload["failure_reference"] == "dl-1"
    assert "failed_payload" not in payload
    assert "payload" not in payload


def test_a_lag_event_reports_a_band_not_an_exact_figure() -> None:
    """`P13-EVT-009`: an exact figure across organizations is itself
    information."""
    payload = projection_lag_detected_payload(
        projection_id=uid(1), lag_band="moderate", threshold_reference="t-1"
    )
    assert payload["lag_band"] == "moderate"
    assert "events_behind" not in payload
    assert "exact_lag" not in payload


def test_a_compatibility_event_keeps_the_two_verdicts_separate() -> None:
    payload = compatibility_assessed_payload(
        assessment_id=uid(1),
        automated_verdict="backward_compatible",
        human_verdict=None,
        declared_mode="backward_compatible",
        reviewer_reference=None,
    )
    assert "automated_verdict" in payload
    assert "human_verdict" in payload
    assert "verdict" not in payload


def test_a_backfill_completion_reports_records_routed_to_review() -> None:
    """`P13-BF-012`: a run that completed silently would look identical to
    one that resolved everything."""
    payload = data_backfill_completed_payload(
        processed=10,
        succeeded=8,
        routed_to_review=2,
        failed=0,
        reconciliation_report_reference="r-1",
    )
    assert payload["routed_to_review"] == 2


def test_every_payload_builder_output_passes_the_guard_when_enveloped() -> None:
    payload = schema_version_proposed_payload(
        schema_version_id=uid(1),
        family_name="f",
        version_label="1",
        owner_domain="d",
        schema_format="json_schema",
        content_digest="a" * 64,
    )
    envelope = _envelope(event_type="schema_version.proposed", payload=payload)
    assert envelope.payload["family_name"] == "f"


# ---------------------------------------------------------------------------
# `*_RECORDED` classifications
# ---------------------------------------------------------------------------


def test_there_is_one_recorded_classification_per_event() -> None:
    """`P13-RSN-006`: canon §24 is refusal-only, and a successful act's
    audit row needs a registered code too."""
    assert len(DATA_PLANE_RECORDED_REASON_CODES) == len(DATA_PLANE_EVENT_TYPES)
    assert len(set(DATA_PLANE_RECORDED_REASON_CODES)) == 37


def test_a_recorded_code_is_derived_mechanically_from_the_event_name() -> None:
    assert recorded_reason_code_for("schema_version.approved") == "SCHEMA_VERSION_APPROVED_RECORDED"
    assert recorded_reason_code_for("projection.updated") == "PROJECTION_UPDATED_RECORDED"


def test_a_recorded_code_for_an_unknown_event_is_refused() -> None:
    with pytest.raises(EventVersionUnsupportedError):
        recorded_reason_code_for("pack13.invented")


def test_every_recorded_code_is_registered_in_the_pack_13_registry() -> None:
    """The registry and the derivation cannot drift, and this asserts it
    rather than assuming it."""
    import pathlib

    yaml = pytest.importorskip("yaml")
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    registry = yaml.safe_load(
        (repo_root / "contracts" / "reason-codes" / "pack-13.yml").read_text(encoding="utf-8")
    )
    registered = {entry["code"] for entry in registry}
    missing = sorted(set(DATA_PLANE_RECORDED_REASON_CODES) - registered)
    assert missing == []
