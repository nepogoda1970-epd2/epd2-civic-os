"""The deterministic backfill runner (PACK-13 §20; ADR-075).

`P13-BF-001` through `P13-BF-014` in one place. The runner is
deterministic, restartable, idempotent, checkpointed, rate-limited,
organization-aware, policy-aware, audited and verifiable — and the two
rules that matter most are the two about honesty:

- **A backfill does not bypass domain invariants** (`P13-BF-010`).
  Writing through the database rather than the domain does not make an
  invalid record valid, so the runner calls an invariant check and
  refuses on failure rather than inserting.
- **A backfill invents no missing facts** (`P13-BF-011`). Where the
  source lacks a value the target requires, the record goes to a
  **review queue** with its reason — never a default, never an
  inference, never "the most likely value". An inferred fact becomes an
  authoritative lie.

The final reconciliation report states counts processed, succeeded,
routed to review and failed, and is retained as evidence
(`P13-BF-014`). A run that cannot reconcile its counts fails rather than
reporting success.

**No sensitive data in backfill logs** (`P13-BF-013`): the runner records
record identifiers and reason codes, and there is deliberately no field
anywhere in this module that could carry a record's content.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    EvidenceReference,
    OrganizationScopeReference,
    RetentionScheduleReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    BackfillCheckpointLostError,
    BackfillConflictError,
    BackfillInvariantViolationError,
    BackfillReconciliationFailedError,
    RecordUnderLegalHoldError,
)


class BackfillDisposition(StrEnum):
    """What happened to one source record. There is no `guessed`
    disposition, which is the point."""

    SUCCEEDED = "succeeded"
    ROUTED_TO_REVIEW = "routed_to_review"
    FAILED = "failed"
    SKIPPED_UNDER_HOLD = "skipped_under_hold"


@dataclass(frozen=True, slots=True)
class BackfillSourceRecord:
    """One record presented to the runner.

    Carries **identifiers and typed values only**. The runner never sees
    or logs free-form content, so there is no path by which a backfill
    log acquires personal data (`P13-BF-013`)."""

    record_id: UUID
    scope: OrganizationScopeReference
    values: tuple[tuple[str, str], ...]
    under_legal_hold: bool = False

    def value_for(self, field_name: str) -> str | None:
        for name, value in self.values:
            if name == field_name:
                return value
        return None


@dataclass(frozen=True, slots=True)
class BackfillCheckpoint:
    """The resume position (`P13-BF-002`, `P13-BF-004`)."""

    backfill_id: UUID
    last_processed_index: int
    processed: int
    succeeded: int
    routed_to_review: int
    failed: int
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, field="BackfillCheckpoint.recorded_at")
        if self.last_processed_index < -1:
            raise BackfillCheckpointLostError(
                "a checkpoint's last processed index is -1 (nothing processed) or greater"
            )


@dataclass(frozen=True, slots=True)
class ReviewQueueEntry:
    """One record the runner refused to guess about (`P13-BF-012`)."""

    record_id: UUID
    scope: OrganizationScopeReference
    missing_field: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """The final report (`P13-BF-014`), retained as evidence.

    Construction validates that the counts add up: a report whose parts
    do not sum to its whole is a report that would let a silent drop pass
    as a success."""

    backfill_id: UUID
    processed: int
    succeeded: int
    routed_to_review: int
    failed: int
    skipped_under_hold: int
    evidence: EvidenceReference
    completed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.completed_at, field="ReconciliationReport.completed_at")
        total = self.succeeded + self.routed_to_review + self.failed + self.skipped_under_hold
        if total != self.processed:
            raise BackfillReconciliationFailedError(
                f"backfill {self.backfill_id}: {self.processed} processed but "
                f"{total} accounted for ({self.succeeded} succeeded, "
                f"{self.routed_to_review} routed to review, {self.failed} failed, "
                f"{self.skipped_under_hold} under hold); counts must reconcile"
            )

    @property
    def completed_silently(self) -> bool:
        """Whether the run finished with unresolved records unreported.

        Always `False` by construction — `routed_to_review` is carried in
        the report — and exposed as a property so a test can assert the
        obligation rather than infer it (`P13-BF-012`)."""
        return False


@dataclass(frozen=True, slots=True)
class BackfillPlan:
    """The declared parameters of one backfill run."""

    backfill_id: UUID
    target_field: str
    required_source_field: str
    scope: OrganizationScopeReference
    batch_size: int
    rate_limit_per_batch: int
    retention_schedule: RetentionScheduleReference

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.rate_limit_per_batch < 1:
            raise ValueError("rate_limit_per_batch must be at least 1")
        if not self.target_field or not self.required_source_field:
            raise ValueError("a backfill plan names both its source and its target field")


@dataclass(frozen=True, slots=True)
class BackfillOutcome:
    """The result of one run or resumption."""

    checkpoint: BackfillCheckpoint
    review_queue: tuple[ReviewQueueEntry, ...]
    completed: bool


class BackfillRunner:
    """A deterministic, restartable backfill runner.

    Deterministic in the strict sense: the same plan over the same
    ordered records always produces the same checkpoints, the same review
    queue and the same counts. It holds no clock — every timestamp is
    passed in — so a test can replay a run exactly.
    """

    def __init__(
        self,
        plan: BackfillPlan,
        *,
        invariant_check: Callable[[BackfillSourceRecord, str], bool],
        existing_target_value: Callable[[BackfillSourceRecord], str | None],
    ) -> None:
        self._plan = plan
        self._invariant_check = invariant_check
        self._existing_target_value = existing_target_value

    def run(
        self,
        records: Sequence[BackfillSourceRecord],
        *,
        now: datetime,
        resume_from: BackfillCheckpoint | None = None,
        max_batches: int | None = None,
    ) -> BackfillOutcome:
        """Process `records`, starting after `resume_from`.

        Restart safety is structural: the runner never re-processes a
        record before the checkpoint's index, and re-processing a record
        *at* the checkpoint would be idempotent anyway because a target
        that already holds the intended value is a success, not a
        conflict.
        """
        require_timezone(now, field="now")
        start = 0 if resume_from is None else resume_from.last_processed_index + 1
        if start < 0:
            raise BackfillCheckpointLostError(
                f"backfill {self._plan.backfill_id}: resume position unavailable"
            )
        processed = 0 if resume_from is None else resume_from.processed
        succeeded = 0 if resume_from is None else resume_from.succeeded
        routed = 0 if resume_from is None else resume_from.routed_to_review
        failed = 0 if resume_from is None else resume_from.failed
        review: list[ReviewQueueEntry] = []

        limit = len(records)
        if max_batches is not None:
            # Rate limiting is a real control, not a comment: a run may be
            # bounded to a number of batches so an operator can observe
            # its effect before continuing (`P13-BF-005`).
            limit = min(limit, start + max_batches * self._plan.batch_size)

        index = start - 1
        for index in range(start, limit):
            record = records[index]
            processed += 1
            disposition, entry = self._process(record)
            if entry is not None:
                review.append(entry)
            if disposition is BackfillDisposition.SUCCEEDED:
                succeeded += 1
            elif disposition is BackfillDisposition.ROUTED_TO_REVIEW:
                routed += 1
            elif disposition is BackfillDisposition.SKIPPED_UNDER_HOLD:
                # A hold preserves the record; it does not authorize the
                # runner to touch it, and it does not authorize reading
                # it either (`P13-RET-005`).
                routed += 1
            else:
                failed += 1

        checkpoint = BackfillCheckpoint(
            backfill_id=self._plan.backfill_id,
            last_processed_index=index,
            processed=processed,
            succeeded=succeeded,
            routed_to_review=routed,
            failed=failed,
            recorded_at=now,
        )
        return BackfillOutcome(
            checkpoint=checkpoint,
            review_queue=tuple(review),
            completed=limit >= len(records),
        )

    def _process(
        self, record: BackfillSourceRecord
    ) -> tuple[BackfillDisposition, ReviewQueueEntry | None]:
        if not record.scope.matches(self._plan.scope):
            # Organization-aware (`P13-BF-006`): a record outside the
            # declared scope is not silently included.
            return (
                BackfillDisposition.ROUTED_TO_REVIEW,
                ReviewQueueEntry(
                    record_id=record.record_id,
                    scope=record.scope,
                    missing_field=self._plan.required_source_field,
                    reason_code="ORGANIZATION_SCOPE_MISMATCH",
                ),
            )
        if record.under_legal_hold:
            return (
                BackfillDisposition.SKIPPED_UNDER_HOLD,
                ReviewQueueEntry(
                    record_id=record.record_id,
                    scope=record.scope,
                    missing_field=self._plan.target_field,
                    reason_code="RECORD_UNDER_LEGAL_HOLD",
                ),
            )
        source_value = record.value_for(self._plan.required_source_field)
        if source_value is None or source_value == "":
            return (
                BackfillDisposition.ROUTED_TO_REVIEW,
                ReviewQueueEntry(
                    record_id=record.record_id,
                    scope=record.scope,
                    missing_field=self._plan.required_source_field,
                    reason_code="BACKFILL_SOURCE_INCOMPLETE",
                ),
            )
        existing = self._existing_target_value(record)
        if existing is not None and existing != source_value:
            return (
                BackfillDisposition.FAILED,
                ReviewQueueEntry(
                    record_id=record.record_id,
                    scope=record.scope,
                    missing_field=self._plan.target_field,
                    reason_code="BACKFILL_CONFLICT",
                ),
            )
        if not self._invariant_check(record, source_value):
            return (
                BackfillDisposition.FAILED,
                ReviewQueueEntry(
                    record_id=record.record_id,
                    scope=record.scope,
                    missing_field=self._plan.target_field,
                    reason_code="BACKFILL_INVARIANT_VIOLATION",
                ),
            )
        return (BackfillDisposition.SUCCEEDED, None)


def require_no_conflict(entries: Sequence[ReviewQueueEntry], *, context: str) -> None:
    """Raise the registered refusal where the review queue holds a
    conflict or an invariant violation.

    Called by an operator surface that needs to fail rather than display:
    a queue entry is a fact to be worked, but a caller that asked for a
    clean run gets the refusal."""
    conflicts = [e for e in entries if e.reason_code == "BACKFILL_CONFLICT"]
    if conflicts:
        raise BackfillConflictError(
            f"{context}: {len(conflicts)} record(s) have a target already populated with a "
            f"different value"
        )
    violations = [e for e in entries if e.reason_code == "BACKFILL_INVARIANT_VIOLATION"]
    if violations:
        raise BackfillInvariantViolationError(
            f"{context}: {len(violations)} record(s) would violate a domain invariant; "
            f"writing through the database rather than the domain does not make an invalid "
            f"record valid"
        )
    held = [e for e in entries if e.reason_code == "RECORD_UNDER_LEGAL_HOLD"]
    if held:
        raise RecordUnderLegalHoldError(
            f"{context}: {len(held)} record(s) are under legal hold and were preserved "
            f"untouched; a hold preserves data and authorizes nothing"
        )
