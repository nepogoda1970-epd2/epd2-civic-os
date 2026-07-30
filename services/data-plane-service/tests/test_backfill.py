"""The backfill runner (PACK-13 §20; ADR-075).

Deterministic, restartable, idempotent, checkpointed, rate-limited,
organization-aware, policy-aware — and above all inventing nothing.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import NOW, evidence, retention, scope, uid

from epd2_data_plane_service.backfill import (
    BackfillPlan,
    BackfillRunner,
    BackfillSourceRecord,
    ReconciliationReport,
    require_no_conflict,
)
from epd2_data_plane_service.domain import OrganizationScopeKind, OrganizationScopeReference
from epd2_data_plane_service.exceptions import (
    BackfillConflictError,
    BackfillInvariantViolationError,
    BackfillReconciliationFailedError,
    RecordUnderLegalHoldError,
)

PLAN = BackfillPlan(
    backfill_id=uid(2100),
    target_field="scope_kind",
    required_source_field="organization_kind",
    scope=scope(),
    batch_size=2,
    rate_limit_per_batch=2,
    retention_schedule=retention(),
)


def _record(
    n: int,
    *,
    value: str | None = "land",
    held: bool = False,
    record_scope: OrganizationScopeReference | None = None,
) -> BackfillSourceRecord:
    values = () if value is None else (("organization_kind", value),)
    return BackfillSourceRecord(
        record_id=uid(2200 + n),
        scope=record_scope or scope(),
        values=values,
        under_legal_hold=held,
    )


def _runner(*, existing: str | None = None, invariant_ok: bool = True) -> BackfillRunner:
    return BackfillRunner(
        PLAN,
        invariant_check=lambda record, value: invariant_ok,
        existing_target_value=lambda record: existing,
    )


def test_a_clean_run_succeeds_for_every_record() -> None:
    outcome = _runner().run([_record(1), _record(2), _record(3)], now=NOW)
    assert outcome.checkpoint.processed == 3
    assert outcome.checkpoint.succeeded == 3
    assert outcome.review_queue == ()
    assert outcome.completed


def test_the_run_is_deterministic_across_repetitions() -> None:
    records = [_record(1), _record(2, value=None), _record(3)]
    first = _runner().run(records, now=NOW)
    second = _runner().run(records, now=NOW)
    assert first.checkpoint == second.checkpoint
    assert first.review_queue == second.review_queue


def test_a_missing_source_fact_is_routed_to_review_never_invented() -> None:
    """`P13-BF-011`: an inferred fact becomes an authoritative lie."""
    outcome = _runner().run([_record(1, value=None)], now=NOW)
    assert outcome.checkpoint.routed_to_review == 1
    assert outcome.review_queue[0].reason_code == "BACKFILL_SOURCE_INCOMPLETE"
    assert outcome.review_queue[0].missing_field == "organization_kind"


def test_an_empty_source_value_is_treated_as_missing() -> None:
    outcome = _runner().run([_record(1, value="")], now=NOW)
    assert outcome.checkpoint.routed_to_review == 1


def test_a_populated_target_with_a_different_value_conflicts() -> None:
    outcome = _runner(existing="kreis").run([_record(1)], now=NOW)
    assert outcome.checkpoint.failed == 1
    assert outcome.review_queue[0].reason_code == "BACKFILL_CONFLICT"


def test_a_populated_target_with_the_same_value_is_idempotent() -> None:
    """`P13-BF-003`: re-processing a record whose target already holds the
    intended value is a success, not a conflict."""
    outcome = _runner(existing="land").run([_record(1)], now=NOW)
    assert outcome.checkpoint.succeeded == 1


def test_a_domain_invariant_violation_fails_rather_than_writing() -> None:
    outcome = _runner(invariant_ok=False).run([_record(1)], now=NOW)
    assert outcome.checkpoint.failed == 1
    assert outcome.review_queue[0].reason_code == "BACKFILL_INVARIANT_VIOLATION"


def test_a_record_outside_the_declared_scope_is_not_silently_included() -> None:
    """`P13-BF-006`: organization-aware."""
    other = OrganizationScopeReference(
        organization_id=uid(9999), scope_kind=OrganizationScopeKind.KREIS
    )
    outcome = _runner().run([_record(1, record_scope=other)], now=NOW)
    assert outcome.checkpoint.routed_to_review == 1
    assert outcome.review_queue[0].reason_code == "ORGANIZATION_SCOPE_MISMATCH"


def test_a_held_record_is_preserved_untouched() -> None:
    outcome = _runner().run([_record(1, held=True)], now=NOW)
    assert outcome.review_queue[0].reason_code == "RECORD_UNDER_LEGAL_HOLD"
    assert outcome.checkpoint.succeeded == 0


def test_a_rate_limited_run_stops_and_resumes_from_its_checkpoint() -> None:
    records = [_record(n) for n in range(1, 6)]
    first = _runner().run(records, now=NOW, max_batches=1)
    assert first.checkpoint.processed == 2
    assert not first.completed

    second = _runner().run(records, now=NOW, resume_from=first.checkpoint)
    assert second.checkpoint.processed == 5
    assert second.completed


def test_a_resumed_run_never_reprocesses_a_record_before_the_checkpoint() -> None:
    records = [_record(n) for n in range(1, 6)]
    first = _runner().run(records, now=NOW, max_batches=1)
    second = _runner().run(records, now=NOW, resume_from=first.checkpoint)
    assert second.checkpoint.succeeded == 5


def test_the_review_queue_is_reported_rather_than_swallowed() -> None:
    outcome = _runner().run([_record(1, value=None), _record(2)], now=NOW)
    assert len(outcome.review_queue) == 1


def test_a_reconciliation_report_refuses_counts_that_do_not_add_up() -> None:
    with pytest.raises(BackfillReconciliationFailedError):
        ReconciliationReport(
            backfill_id=PLAN.backfill_id,
            processed=10,
            succeeded=5,
            routed_to_review=1,
            failed=1,
            skipped_under_hold=0,
            evidence=evidence(),
            completed_at=NOW,
        )


def test_a_reconciling_report_constructs_and_never_completes_silently() -> None:
    report = ReconciliationReport(
        backfill_id=PLAN.backfill_id,
        processed=7,
        succeeded=5,
        routed_to_review=1,
        failed=1,
        skipped_under_hold=0,
        evidence=evidence(),
        completed_at=NOW,
    )
    assert report.completed_silently is False


def test_a_plan_requires_a_positive_batch_size_and_rate_limit() -> None:
    with pytest.raises(ValueError, match="batch_size"):
        BackfillPlan(
            backfill_id=uid(1),
            target_field="a",
            required_source_field="b",
            scope=scope(),
            batch_size=0,
            rate_limit_per_batch=1,
            retention_schedule=retention(),
        )


def test_a_plan_names_both_its_source_and_its_target_field() -> None:
    with pytest.raises(ValueError, match="names both"):
        BackfillPlan(
            backfill_id=uid(1),
            target_field="",
            required_source_field="b",
            scope=scope(),
            batch_size=1,
            rate_limit_per_batch=1,
            retention_schedule=retention(),
        )


def test_require_no_conflict_raises_the_registered_refusals() -> None:
    conflict = _runner(existing="kreis").run([_record(1)], now=NOW)
    with pytest.raises(BackfillConflictError):
        require_no_conflict(conflict.review_queue, context="run")

    violation = _runner(invariant_ok=False).run([_record(2)], now=NOW)
    with pytest.raises(BackfillInvariantViolationError):
        require_no_conflict(violation.review_queue, context="run")

    held = _runner().run([_record(3, held=True)], now=NOW)
    with pytest.raises(RecordUnderLegalHoldError):
        require_no_conflict(held.review_queue, context="run")


def test_require_no_conflict_is_silent_on_a_clean_queue() -> None:
    require_no_conflict((), context="run")


def test_a_source_record_carries_typed_values_not_free_content() -> None:
    """`P13-BF-013`: there is no field anywhere here that could carry a
    record's content into a log."""
    record = _record(1)
    assert set(record.__slots__) == {"record_id", "scope", "values", "under_legal_hold"}
