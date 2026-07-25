"""Storage protocol and in-memory reference adapter for AI Processing
Service's one owned entity: `AIProcessingRecord` (canon 17.1/19c). A
durable backend can implement this same protocol without any change to
`application.py`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_ai_processing_service.domain import AIProcessingRecord
from epd2_ai_processing_service.exceptions import AIProcessingRecordConflictError


class AIProcessingRecordStore(Protocol):
    def create(self, record: AIProcessingRecord) -> AIProcessingRecord:
        """Create a new `AIProcessingRecord`. Idempotent by content: if
        `record.ai_processing_record_id` already exists with identical
        content, returns the existing record; if it exists with
        different content, raises `AIProcessingRecordConflictError`."""
        ...

    def save(self, record: AIProcessingRecord) -> None:
        """Persist a `processing_status`/`human_review_status`/
        disclosure-field transition on the *same* row (same
        `ai_processing_record_id`) — never used for a correction, which
        is always a `create` of a brand-new row (19c.2)."""
        ...

    def get(self, ai_processing_record_id: UUID) -> AIProcessingRecord | None: ...

    def find_superseding(self, ai_processing_record_id: UUID) -> AIProcessingRecord | None:
        """Return the other `AIProcessingRecord` whose own
        `supersedes_ai_processing_record_id` equals
        `ai_processing_record_id`, or `None` if this record has not been
        superseded. The derived "is this record superseded" check
        (19c.1/19c.2) — never a stored value on the superseded row
        itself."""
        ...

    def list_by_target(self, target_type: str, target_id: UUID) -> tuple[AIProcessingRecord, ...]:
        """Every `AIProcessingRecord` ever created for this opaque
        `target_type`/`target_id` pair, in creation order."""
        ...


class InMemoryAIProcessingRecordStore:
    def __init__(self) -> None:
        self._records: dict[UUID, AIProcessingRecord] = {}
        self._by_target: dict[tuple[str, UUID], list[UUID]] = {}

    def create(self, record: AIProcessingRecord) -> AIProcessingRecord:
        existing = self._records.get(record.ai_processing_record_id)
        if existing is not None:
            if existing == record:
                return existing
            raise AIProcessingRecordConflictError(
                f"ai_processing_record_id {record.ai_processing_record_id} already exists "
                "with different content"
            )
        self._records[record.ai_processing_record_id] = record
        self._by_target.setdefault((record.target_type, record.target_id), []).append(
            record.ai_processing_record_id
        )
        return record

    def save(self, record: AIProcessingRecord) -> None:
        self._records[record.ai_processing_record_id] = record

    def get(self, ai_processing_record_id: UUID) -> AIProcessingRecord | None:
        return self._records.get(ai_processing_record_id)

    def find_superseding(self, ai_processing_record_id: UUID) -> AIProcessingRecord | None:
        for record in self._records.values():
            if record.supersedes_ai_processing_record_id == ai_processing_record_id:
                return record
        return None

    def list_by_target(self, target_type: str, target_id: UUID) -> tuple[AIProcessingRecord, ...]:
        ids = self._by_target.get((target_type, target_id), [])
        return tuple(self._records[i] for i in ids)
