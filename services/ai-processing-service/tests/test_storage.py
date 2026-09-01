"""Storage-layer tests for AI Processing Service's `InMemoryAIProcessingRecordStore`."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_ai_processing_service.domain import (
    AIProcessingRecord,
    HumanReviewStatus,
    ProcessingStatus,
    RedactionManifest,
    RedactionResult,
)
from epd2_ai_processing_service.exceptions import AIProcessingRecordConflictError
from epd2_ai_processing_service.storage import InMemoryAIProcessingRecordStore

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


def _manifest() -> RedactionManifest:
    return RedactionManifest(
        redaction_policy_reference="policy-1",
        redaction_policy_version="1.0",
        input_classification="public",
        checked_field_categories=("identity", "credential", "vote_linkage"),
        removed_field_categories=(),
        prepared_input_hash="hash-1",
        validator_version="1.0",
        validated_at=NOW,
        result=RedactionResult.PASS,
    )


def _record(**overrides: object) -> AIProcessingRecord:
    fields: dict[str, object] = {
        "ai_processing_record_id": uuid4(),
        "purpose_code": "summarization",
        "target_type": "initiative",
        "target_id": uuid4(),
        "input_version": "v1",
        "model_provider": "internal",
        "model_name": "internal-model",
        "model_version": "1.0",
        "prompt_template_version": "v1",
        "output_reference": None,
        "created_at": NOW,
        "human_review_status": HumanReviewStatus.NOT_REQUIRED,
        "correction_reference": None,
        "processing_status": ProcessingStatus.REQUESTED,
        "supersedes_ai_processing_record_id": None,
        "deployment_version": None,
        "system_policy_version": None,
        "generation_settings": None,
        "processing_region": None,
        "data_retention_mode": None,
        "external_provider_flag": False,
        "input_hash": None,
        "output_hash": None,
        "confidence_score": None,
        "uncertainty_indicator": None,
        "explanation_reference": None,
        "reason_codes": (),
        "human_reviewer_reference": None,
        "completed_at": None,
        "reviewed_at": None,
        "redaction_manifest": None,
        "disclosure_required": False,
        "disclosure_package_reference": None,
        "disclosure_receipt_reference": None,
    }
    fields.update(overrides)
    return AIProcessingRecord(**fields)  # type: ignore[arg-type]


def test_create_is_idempotent_by_identical_content() -> None:
    store = InMemoryAIProcessingRecordStore()
    record = _record()
    first = store.create(record)
    second = store.create(record)
    assert first == second


def test_create_conflicts_on_same_id_different_content() -> None:
    store = InMemoryAIProcessingRecordStore()
    record_id = uuid4()
    store.create(_record(ai_processing_record_id=record_id, input_version="v1"))
    with pytest.raises(AIProcessingRecordConflictError):
        store.create(_record(ai_processing_record_id=record_id, input_version="v2"))


def test_get_returns_none_for_unknown_id() -> None:
    store = InMemoryAIProcessingRecordStore()
    assert store.get(uuid4()) is None


def test_save_persists_the_same_row() -> None:
    store = InMemoryAIProcessingRecordStore()
    record = store.create(_record())
    updated = record.with_processing_status(
        ProcessingStatus.INPUT_PREPARED, redaction_manifest=_manifest()
    )
    store.save(updated)
    fetched = store.get(record.ai_processing_record_id)
    assert fetched is not None
    assert fetched.processing_status is ProcessingStatus.INPUT_PREPARED


def test_find_superseding_returns_none_until_a_replacement_exists() -> None:
    store = InMemoryAIProcessingRecordStore()
    original = store.create(_record())
    assert store.find_superseding(original.ai_processing_record_id) is None

    replacement = store.create(
        _record(supersedes_ai_processing_record_id=original.ai_processing_record_id)
    )
    found = store.find_superseding(original.ai_processing_record_id)
    assert found is not None
    assert found.ai_processing_record_id == replacement.ai_processing_record_id


def test_list_by_target() -> None:
    store = InMemoryAIProcessingRecordStore()
    target_id = uuid4()
    a = store.create(_record(target_type="initiative", target_id=target_id))
    b = store.create(_record(target_type="initiative", target_id=target_id))
    store.create(_record(target_type="initiative", target_id=uuid4()))
    listed = store.list_by_target("initiative", target_id)
    assert {r.ai_processing_record_id for r in listed} == {
        a.ai_processing_record_id,
        b.ai_processing_record_id,
    }
