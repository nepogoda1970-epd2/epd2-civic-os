"""Reference administrative surfaces and observability
(PACK-13 §30, §32).

Seven narrow surfaces, no console, no SQL, no secrets, no raw data, no
bypass of a PACK-12 grant, and no surface claiming that production
infrastructure is active.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import NOW, scope, uid

from epd2_data_plane_service.administration import (
    ADMINISTRATIVE_SURFACES,
    FORBIDDEN_TELEMETRY_CONTENT,
    CompatibilityResultItem,
    ConsumerReadinessItem,
    DeadLetterReviewItem,
    MigrationStatusItem,
    OperationalLogRecord,
    OperationalStatus,
    OutboxBacklogItem,
    ProjectionHealthItem,
    SchemaReviewItem,
    TelemetryKind,
    TelemetrySample,
    TraceCorrelation,
    assemble_status_view,
    refuse_query_surface,
)
from epd2_data_plane_service.domain import (
    DATA_PLANE_IMPLEMENTATION_STATUS,
    GlobalUserIdentifierProhibitedError,
)
from epd2_data_plane_service.exceptions import (
    ManualSqlProhibitedError,
    PermissionDeniedError,
)
from epd2_data_plane_service.projections import ProjectionHealth


def _schema_item() -> SchemaReviewItem:
    return SchemaReviewItem(
        schema_version_id=uid(31000),
        family_name="membership.record",
        version_label="1.1.0",
        owner_domain="membership-service",
        lifecycle_state="under_review",
        content_digest="a" * 64,
        awaiting="semantic review",
    )


def _migration_item() -> MigrationStatusItem:
    return MigrationStatusItem(
        execution_id=uid(31001),
        plan_id=uid(31002),
        status="completed",
        migration_class="expand",
        checkpoints=3,
        destructive=False,
        approval_present=True,
        dry_run_present=True,
    )


def _projection_item() -> ProjectionHealthItem:
    return ProjectionHealthItem(
        projection_id=uid(31003),
        projection_name="membership-overview",
        health=ProjectionHealth.HEALTHY,
        lag_band="none",
        acceptable_for_consequential_use=True,
    )


def _backlog_item() -> OutboxBacklogItem:
    return OutboxBacklogItem(
        scope=scope(),
        pending_count=3,
        oldest_pending_age_seconds=12,
        alert_threshold=10,
        exceeds_threshold=False,
    )


def _dead_letter_item() -> DeadLetterReviewItem:
    return DeadLetterReviewItem(
        dead_letter_id=uid(31004),
        event_type="projection.updated",
        reason_code="EVENT_POISON_MESSAGE",
        attempt_count=3,
        classification_tier="restricted",
    )


# ---------------------------------------------------------------------------
# The seven surfaces
# ---------------------------------------------------------------------------


def test_exactly_seven_administrative_surfaces_exist() -> None:
    """`P13-FE-001` names seven administrative concerns; `P13-FE-002`
    forbids an eighth that aggregates them into a console."""
    assert len(ADMINISTRATIVE_SURFACES) == 7
    assert "schema_review" in ADMINISTRATIVE_SURFACES
    assert "outbox_backlog" in ADMINISTRATIVE_SURFACES
    assert "console" not in ADMINISTRATIVE_SURFACES


def test_the_schema_review_surface_shows_a_digest_never_the_document() -> None:
    view = _schema_item().to_view()
    assert view["content_digest"] == "a" * 64
    assert "schema_body" not in view


def test_the_compatibility_surface_shows_both_verdicts_separately() -> None:
    view = CompatibilityResultItem(
        assessment_id=uid(31005),
        automated_verdict="backward_compatible",
        human_verdict=None,
        combined_verdict="unknown_manual_review_required",
        semantic_risk_classes=("enum_meaning_change",),
        review_required=True,
    ).to_view()
    assert view["automated_verdict"] != view["combined_verdict"]
    assert view["human_verdict"] is None


def test_the_migration_surface_shows_counts_never_statements() -> None:
    view = _migration_item().to_view()
    assert view["checkpoints"] == 3
    for forbidden in ("statements", "sql", "rows", "row_data"):
        assert forbidden not in view


def test_the_consumer_readiness_surface_states_its_own_limit() -> None:
    view = ConsumerReadinessItem(
        family_id=uid(31006), target_version_id=uid(31007), ready_count=2, not_ready_count=1
    ).to_view()
    assert view["unregistered_consumers_receive_no_compatibility_protection"] is True


def test_the_dead_letter_surface_lists_but_does_not_open() -> None:
    """`P13-DEL-014`, `P13-FE-006`: opening a record is a privileged act
    performed elsewhere."""
    item = _dead_letter_item()
    view = item.to_view()
    assert view["requires_privileged_read"] is True
    assert "payload" not in view
    with pytest.raises(PermissionDeniedError, match="governed path"):
        item.open_record()


def test_the_projection_surface_shows_a_band_not_an_exact_lag() -> None:
    view = _projection_item().to_view()
    assert view["lag_band"] == "none"
    assert "events_behind" not in view


def test_the_backlog_surface_shows_counts_never_payloads() -> None:
    view = _backlog_item().to_view()
    assert view["pending_count"] == 3
    assert "records" not in view
    assert "payload" not in view


def test_a_surface_refuses_a_payload_carrying_a_prohibited_key() -> None:
    from dataclasses import replace

    item = replace(_schema_item(), family_name="membership.record")
    assert item.to_view()["family_name"] == "membership.record"

    with pytest.raises(GlobalUserIdentifierProhibitedError):
        from epd2_data_plane_service.administration import _safe_view

        _safe_view({"person_id": "x"}, surface="schema_review")


# ---------------------------------------------------------------------------
# No SQL from any surface
# ---------------------------------------------------------------------------


def test_no_surface_executes_a_query() -> None:
    """`P13-FE-005`."""
    with pytest.raises(ManualSqlProhibitedError, match="none of them evaluated"):
        refuse_query_surface("select * from membership_record")


def test_the_refusal_message_carries_no_query_text() -> None:
    """`P13-OBS-002`: a refusal message is telemetry."""
    try:
        refuse_query_surface("select secret from vault")
    except ManualSqlProhibitedError as exc:
        assert "select" not in str(exc)
        assert "vault" not in str(exc)
    else:  # pragma: no cover - the call above always raises
        raise AssertionError("refuse_query_surface must raise")


# ---------------------------------------------------------------------------
# Operational status
# ---------------------------------------------------------------------------


def test_the_operational_status_reports_the_truthful_implementation_state() -> None:
    status = OperationalStatus(observed_at=NOW)
    assert status.implementation_status == DATA_PLANE_IMPLEMENTATION_STATUS
    assert status.production_infrastructure_active is False
    assert status.legally_activated is False


def test_no_surface_claims_production_infrastructure_is_active() -> None:
    """`P13-FE-008`, FIR-INV-015."""
    with pytest.raises(PermissionDeniedError, match="production-readiness"):
        OperationalStatus(observed_at=NOW, production_infrastructure_active=True)
    with pytest.raises(PermissionDeniedError, match="legal-activation"):
        OperationalStatus(observed_at=NOW, legally_activated=True)


def test_no_surface_claims_a_stronger_implementation_status() -> None:
    with pytest.raises(PermissionDeniedError, match="reference_implementation"):
        OperationalStatus(observed_at=NOW, implementation_status="production")


def test_no_surface_describes_the_delivery_guarantee_with_the_stronger_phrase() -> None:
    """`P13-DEL-002`."""
    with pytest.raises(PermissionDeniedError, match="stronger phrase"):
        OperationalStatus(observed_at=NOW, delivery_guarantee="exactly-once delivery")


def test_the_status_view_composes_its_parts_without_reading_anything() -> None:
    view = assemble_status_view(
        status=OperationalStatus(observed_at=NOW),
        schema_review=[_schema_item()],
        migrations=[_migration_item()],
        projections=[_projection_item()],
        backlogs=[_backlog_item()],
    )
    assert view["implementation_status"] == DATA_PLANE_IMPLEMENTATION_STATUS
    assert len(view["schema_review"]) == 1  # type: ignore[arg-type]
    assert view["production_infrastructure_active"] is False


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------


def test_every_telemetry_kind_the_specification_names_is_exposed() -> None:
    """`P13-OBS-001`."""
    values = {k.value for k in TelemetryKind}
    for expected in (
        "queue_lag",
        "outbox_backlog",
        "migration_progress",
        "schema_compatibility_failure",
        "consumer_error",
        "retry_count",
        "dead_letter_volume",
        "projection_staleness",
        "database_saturation",
    ):
        assert expected in values


def test_the_seven_forbidden_telemetry_categories_are_enumerated() -> None:
    """`P13-OBS-002`."""
    assert len(FORBIDDEN_TELEMETRY_CONTENT) == 7
    assert "plaintext secrets" in FORBIDDEN_TELEMETRY_CONTENT
    assert "unrestricted query text" in FORBIDDEN_TELEMETRY_CONTENT


def test_a_telemetry_sample_refuses_a_prohibited_label() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        TelemetrySample(
            kind=TelemetryKind.CONSUMER_ERROR,
            value=1,
            labels={"person_id": "x"},
            observed_at=NOW,
        )


def test_a_telemetry_sample_with_safe_labels_constructs() -> None:
    sample = TelemetrySample(
        kind=TelemetryKind.OUTBOX_BACKLOG,
        value=12,
        labels={"organization_id": str(uid(1))},
        observed_at=NOW,
    )
    assert sample.value == 12


def test_a_trace_identifier_is_not_an_identity_correlation_identifier() -> None:
    """`P13-OBS-003`."""
    assert TraceCorrelation(
        trace_id=uid(31008), span_name="dispatch"
    ).carries_subject_reference is (False)
    with pytest.raises(PermissionDeniedError, match="identity correlation identifier"):
        TraceCorrelation(trace_id=uid(31008), span_name="dispatch", carries_subject_reference=True)


def test_an_operational_log_record_carries_a_classification() -> None:
    """`P13-OBS-004`: log volume is not an excuse for lower
    classification."""
    with pytest.raises(PermissionDeniedError, match="classification"):
        OperationalLogRecord(
            message="dispatch completed", classification_tier="", recorded_at=NOW, labels={}
        )


def test_a_log_message_never_claims_the_stronger_delivery_guarantee() -> None:
    with pytest.raises(PermissionDeniedError, match="stronger phrase"):
        OperationalLogRecord(
            message="achieved exactly-once delivery",
            classification_tier="internal",
            recorded_at=NOW,
            labels={},
        )


def test_a_well_formed_log_record_constructs() -> None:
    record = OperationalLogRecord(
        message="dispatch completed",
        classification_tier="internal",
        recorded_at=NOW,
        labels={"organization_id": str(uid(1))},
    )
    assert record.classification_tier == "internal"
