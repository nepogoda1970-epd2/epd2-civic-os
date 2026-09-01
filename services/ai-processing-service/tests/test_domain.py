"""Domain-layer tests for AI Processing Service: `AIProcessingRecord`,
`RedactionManifest`, `ProcessingStatus`, `HumanReviewStatus`,
`DisclosureStatus`, `AIDisclosurePackage` — canon section 17.1/19c.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_ai_processing_service.domain import (
    PERMITTED_PURPOSE_TARGET_COMBINATIONS,
    AIDisclosurePackage,
    AIProcessingRecord,
    AITargetReferenceMalformedError,
    DisclosureStatus,
    ForbiddenHumanReviewStatusTransitionError,
    ForbiddenProcessingStatusTransitionError,
    HumanReviewStatus,
    ProcessingStatus,
    RedactionManifest,
    RedactionResult,
    UseClass,
    assert_purpose_target_combination_allowed,
    derive_disclosure_status,
    derive_effective_human_review_status,
    parse_human_review_status,
    parse_processing_status,
    required_reviewer_role_codes,
    review_requires_independent_reviewer,
)
from epd2_ai_processing_service.exceptions import (
    UnknownHumanReviewStatusError,
    UnknownProcessingStatusError,
)

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


def _manifest(**overrides: object) -> RedactionManifest:
    fields: dict[str, object] = {
        "redaction_policy_reference": "policy-1",
        "redaction_policy_version": "1.0",
        "input_classification": "public",
        "checked_field_categories": ("identity", "credential", "vote_linkage"),
        "removed_field_categories": (),
        "prepared_input_hash": "hash-1",
        "validator_version": "1.0",
        "validated_at": NOW,
        "result": RedactionResult.PASS,
    }
    fields.update(overrides)
    return RedactionManifest(**fields)  # type: ignore[arg-type]


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


def test_record_rejects_stored_superseded_human_review_status() -> None:
    with pytest.raises(ValueError, match="superseded"):
        _record(human_review_status=HumanReviewStatus.SUPERSEDED)


def test_record_requires_redaction_manifest_once_input_prepared() -> None:
    with pytest.raises(ValueError, match="redaction_manifest"):
        _record(processing_status=ProcessingStatus.INPUT_PREPARED, redaction_manifest=None)


def test_record_requires_redaction_manifest_once_completed() -> None:
    with pytest.raises(ValueError, match="redaction_manifest"):
        _record(processing_status=ProcessingStatus.COMPLETED, redaction_manifest=None)


def test_processing_status_transition_requested_to_input_prepared() -> None:
    record = _record()
    manifest = _manifest()
    updated = record.with_processing_status(
        ProcessingStatus.INPUT_PREPARED, redaction_manifest=manifest, input_hash="hash-1"
    )
    assert updated.processing_status is ProcessingStatus.INPUT_PREPARED
    assert updated.redaction_manifest is manifest
    assert updated.input_hash == "hash-1"
    # Original record is untouched (immutability).
    assert record.processing_status is ProcessingStatus.REQUESTED


def test_processing_status_forbids_backwards_transition() -> None:
    record = _record(processing_status=ProcessingStatus.COMPLETED, redaction_manifest=_manifest())
    with pytest.raises(ForbiddenProcessingStatusTransitionError):
        record.with_processing_status(ProcessingStatus.REQUESTED)


def test_processing_status_rejected_by_policy_directly_from_requested() -> None:
    record = _record()
    updated = record.with_processing_status(
        ProcessingStatus.REJECTED_BY_POLICY, reason_codes=("AI_REDACTION_FAILURE",)
    )
    assert updated.processing_status is ProcessingStatus.REJECTED_BY_POLICY


def test_human_review_status_pending_to_approved() -> None:
    record = _record(human_review_status=HumanReviewStatus.PENDING)
    reviewer = uuid4()
    updated = record.with_human_review_status(
        HumanReviewStatus.APPROVED, human_reviewer_reference=reviewer, reviewed_at=NOW
    )
    assert updated.human_review_status is HumanReviewStatus.APPROVED
    assert updated.human_reviewer_reference == reviewer


def test_human_review_status_forbids_not_required_to_approved() -> None:
    record = _record(human_review_status=HumanReviewStatus.NOT_REQUIRED)
    with pytest.raises(ForbiddenHumanReviewStatusTransitionError):
        record.with_human_review_status(
            HumanReviewStatus.APPROVED, human_reviewer_reference=uuid4(), reviewed_at=NOW
        )


def test_human_review_status_forbids_pending_to_pending() -> None:
    record = _record(human_review_status=HumanReviewStatus.PENDING)
    with pytest.raises(ForbiddenHumanReviewStatusTransitionError):
        record.with_human_review_status(
            HumanReviewStatus.PENDING, human_reviewer_reference=uuid4(), reviewed_at=NOW
        )


def test_derive_effective_human_review_status_superseded() -> None:
    record = _record(human_review_status=HumanReviewStatus.APPROVED)
    superseding = _record()
    assert derive_effective_human_review_status(record, superseding_record=None) == (
        HumanReviewStatus.APPROVED
    )
    assert derive_effective_human_review_status(record, superseding_record=superseding) == (
        HumanReviewStatus.SUPERSEDED
    )


def test_disclosure_status_lifecycle() -> None:
    record = _record(disclosure_required=False)
    assert derive_disclosure_status(record) is DisclosureStatus.NOT_REQUIRED

    record = _record(disclosure_required=True)
    assert derive_disclosure_status(record) is DisclosureStatus.PENDING_PACKAGE

    record = _record(disclosure_required=True, disclosure_package_reference=uuid4())
    assert derive_disclosure_status(record) is DisclosureStatus.PENDING_PUBLICATION

    record = _record(
        disclosure_required=True,
        disclosure_package_reference=uuid4(),
        disclosure_receipt_reference=uuid4(),
    )
    assert derive_disclosure_status(record) is DisclosureStatus.PUBLISHED


def test_disclosure_package_reference_requires_disclosure_required() -> None:
    with pytest.raises(ValueError, match="disclosure_required"):
        _record(disclosure_required=False, disclosure_package_reference=uuid4())


def test_disclosure_receipt_reference_requires_package_reference_first() -> None:
    with pytest.raises(ValueError, match="disclosure_package_reference"):
        _record(disclosure_required=True, disclosure_receipt_reference=uuid4())


def test_redaction_manifest_removed_must_be_subset_of_checked() -> None:
    with pytest.raises(ValueError, match="subset"):
        _manifest(checked_field_categories=("identity",), removed_field_categories=("credential",))


def test_ai_disclosure_package_requires_approved_outcome() -> None:
    with pytest.raises(ValueError, match="human-approved"):
        AIDisclosurePackage(
            ai_processing_record_reference=uuid4(),
            purpose_code="summarization",
            approved_public_model_category="general-purpose-llm",
            approved_public_model_version="1.0",
            processed_at=NOW,
            human_review_outcome=HumanReviewStatus.REJECTED,
            prompt_template_version="v1",
            system_policy_version="1.0",
        )


def test_ai_disclosure_package_to_raw_content_is_json_safe() -> None:
    package = AIDisclosurePackage(
        ai_processing_record_reference=uuid4(),
        purpose_code="summarization",
        approved_public_model_category="general-purpose-llm",
        approved_public_model_version="1.0",
        processed_at=NOW,
        human_review_outcome=HumanReviewStatus.APPROVED,
        prompt_template_version="v1",
        system_policy_version="1.0",
    )
    raw = package.to_raw_content()
    assert all(isinstance(v, (str, bool)) for v in raw.values())


def test_purpose_target_allow_list_rejects_unknown_target_type() -> None:
    with pytest.raises(AITargetReferenceMalformedError):
        assert_purpose_target_combination_allowed(UseClass.SUMMARIZATION, "not_a_real_target")


def test_purpose_target_allow_list_rejects_disallowed_combination() -> None:
    with pytest.raises(AITargetReferenceMalformedError):
        assert_purpose_target_combination_allowed(UseClass.ANOMALY_INDICATION, "initiative")


def test_purpose_target_allow_list_accepts_every_declared_combination() -> None:
    for use_class, target_types in PERMITTED_PURPOSE_TARGET_COMBINATIONS.items():
        for target_type in target_types:
            assert_purpose_target_combination_allowed(use_class, target_type)


def test_required_reviewer_role_codes_moderation_adjacent_classification() -> None:
    assert required_reviewer_role_codes(UseClass.CLASSIFICATION, "contribution") == frozenset(
        {"ai_moderation_reviewer"}
    )
    assert required_reviewer_role_codes(UseClass.CLASSIFICATION, "discussion_post") == frozenset(
        {"ai_output_reviewer"}
    )


def test_required_reviewer_role_codes_policy_compliance() -> None:
    assert required_reviewer_role_codes(
        UseClass.POLICY_COMPLIANCE_ASSISTANCE, "governance_policy_draft"
    ) == frozenset({"ai_governance_reviewer"})


def test_review_requires_independent_reviewer_for_moderation_and_governance() -> None:
    assert review_requires_independent_reviewer(
        UseClass.CLASSIFICATION, is_official_publication=False
    )
    assert review_requires_independent_reviewer(
        UseClass.POLICY_COMPLIANCE_ASSISTANCE, is_official_publication=False
    )
    assert not review_requires_independent_reviewer(
        UseClass.SUMMARIZATION, is_official_publication=False
    )
    assert review_requires_independent_reviewer(
        UseClass.SUMMARIZATION, is_official_publication=True
    )


# --- CT-00-02 (Unknown Status): parse_* functions ---------------------------


def test_parse_processing_status_accepts_every_known_value() -> None:
    for status in ProcessingStatus:
        assert parse_processing_status(status.value) is status


def test_parse_processing_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownProcessingStatusError) as excinfo:
        parse_processing_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_parse_human_review_status_accepts_every_known_value() -> None:
    for status in HumanReviewStatus:
        assert parse_human_review_status(status.value) is status


def test_parse_human_review_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownHumanReviewStatusError) as excinfo:
        parse_human_review_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"
