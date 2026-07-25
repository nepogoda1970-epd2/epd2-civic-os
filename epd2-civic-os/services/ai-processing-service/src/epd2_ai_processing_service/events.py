"""Canonical events emitted by AI Processing Service — canon section
20.12 (corrected/expanded by canon 0.5.0, ADR-023). Five events are
unchanged (one with a corrected name); six are new, covering
`processing_status`, record replacement, and the disclosure lifecycle:

- `ai.processing_requested` — (unchanged) `AIProcessingRecord` created.
- `ai.input_prepared` — (new) `processing_status -> input_prepared`
  (`redaction_manifest.result = "pass"`).
- `ai.output_created` — (unchanged) `processing_status -> completed`.
- `ai.processing_failed` — (new) `processing_status -> failed`.
- `ai.processing_rejected_by_policy` — (new) `processing_status ->
  rejected_by_policy` (including a `redaction_manifest.result = "fail"`
  outcome).
- `ai.processing_record_superseded` — (new) emitted when a *new* record
  is created whose `supersedes_ai_processing_record_id` replaces a
  technical processing attempt (19c.2) — never on any change to the
  superseded record itself, which never changes.
- `ai.output_reviewed` — (unchanged) `human_review_status -> pending`.
- `ai.output_accepted` — (new) `human_review_status -> approved`.
- `ai.output_corrected` — (name corrected; was `ai.output.corrected`)
  `human_review_status -> approved_with_changes`.
- `ai.output_rejected` — (unchanged) `human_review_status -> rejected`.
- `ai.review_outcome_superseded` — (new) emitted when a *new* record
  replaces a review outcome (19c.2) — same mechanism as
  `ai.processing_record_superseded`, different semantic reason.

`processing_status: requested -> processing` (`begin_processing`) and
`input_prepared -> processing` deliberately emit **no** canonical event
(transient state, no canon 20.12 entry for it) — the same convention
`governance-service.begin_technical_challenge_review` already
establishes for its own `submitted -> under_review` transition: audited
(CT-00-07) but not represented as a domain event.

`human_reviewer_reference` is omitted from every `*_public_payload`,
mirroring `governance-service`'s own omission of every `*_role_id` field
from its event payloads (canon 19b.1/19b.3/19b.4 precedent) — an opaque
`RoleAssignment`-linked reference is never published verbatim by this
project's convention, even though nothing in canon 19c names it
explicitly for omission. `redaction_manifest` — already category-level,
never-raw metadata (19c.4) — is included in full in both payloads.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_ai_processing_service.domain import AIProcessingRecord, RedactionManifest
from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})

_PRODUCER = "ai-processing-service"
_SUBJECT_TYPE = "ai_processing_record"


def _redaction_manifest_payload(manifest: RedactionManifest | None) -> dict[str, object] | None:
    if manifest is None:
        return None
    return {
        "redaction_policy_reference": manifest.redaction_policy_reference,
        "redaction_policy_version": manifest.redaction_policy_version,
        "input_classification": manifest.input_classification,
        "checked_field_categories": list(manifest.checked_field_categories),
        "removed_field_categories": list(manifest.removed_field_categories),
        "prepared_input_hash": manifest.prepared_input_hash,
        "validator_version": manifest.validator_version,
        "validated_at": manifest.validated_at.isoformat(),
        "result": manifest.result.value,
    }


def ai_processing_record_public_payload(record: AIProcessingRecord) -> dict[str, object]:
    """Public event payload — omits `human_reviewer_reference` (see
    module docstring)."""
    return {
        "ai_processing_record_id": str(record.ai_processing_record_id),
        "purpose_code": record.purpose_code,
        "target_type": record.target_type,
        "target_id": str(record.target_id),
        "input_version": record.input_version,
        "model_provider": record.model_provider,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "prompt_template_version": record.prompt_template_version,
        "output_reference": record.output_reference,
        "created_at": record.created_at.isoformat(),
        "human_review_status": record.human_review_status.value,
        "correction_reference": record.correction_reference,
        "processing_status": record.processing_status.value,
        "supersedes_ai_processing_record_id": (
            str(record.supersedes_ai_processing_record_id)
            if record.supersedes_ai_processing_record_id is not None
            else None
        ),
        "deployment_version": record.deployment_version,
        "system_policy_version": record.system_policy_version,
        "generation_settings": (
            dict(record.generation_settings) if record.generation_settings is not None else None
        ),
        "processing_region": record.processing_region,
        "data_retention_mode": record.data_retention_mode,
        "external_provider_flag": record.external_provider_flag,
        "input_hash": record.input_hash,
        "output_hash": record.output_hash,
        "confidence_score": record.confidence_score,
        "uncertainty_indicator": record.uncertainty_indicator,
        "explanation_reference": record.explanation_reference,
        "reason_codes": list(record.reason_codes),
        "completed_at": (
            record.completed_at.isoformat() if record.completed_at is not None else None
        ),
        "reviewed_at": (record.reviewed_at.isoformat() if record.reviewed_at is not None else None),
        "redaction_manifest": _redaction_manifest_payload(record.redaction_manifest),
        "disclosure_required": record.disclosure_required,
        "disclosure_package_reference": (
            str(record.disclosure_package_reference)
            if record.disclosure_package_reference is not None
            else None
        ),
        "disclosure_receipt_reference": (
            str(record.disclosure_receipt_reference)
            if record.disclosure_receipt_reference is not None
            else None
        ),
    }


def ai_processing_record_full_state_payload(record: AIProcessingRecord) -> dict[str, object]:
    """Full snapshot including `human_reviewer_reference`, used only for
    Audit Core's `before_hash`/`after_hash`."""
    payload = ai_processing_record_public_payload(record)
    payload["human_reviewer_reference"] = (
        str(record.human_reviewer_reference)
        if record.human_reviewer_reference is not None
        else None
    )
    return payload


def _build_event(
    *,
    event_type: str,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    extra_payload: dict[str, object] | None = None,
) -> EventEnvelope:
    payload = ai_processing_record_public_payload(record)
    if extra_payload is not None:
        payload.update(extra_payload)
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type=_SUBJECT_TYPE, subject_id=record.ai_processing_record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_processing_requested_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.processing_requested",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_input_prepared_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.input_prepared",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_output_created_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.output_created",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_processing_failed_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.processing_failed",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_processing_rejected_by_policy_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.processing_rejected_by_policy",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_processing_record_superseded_event(
    *,
    event_id: UUID,
    superseded_record: AIProcessingRecord,
    superseding_record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Canon 20.12: emitted when `superseding_record` (already created,
    with `supersedes_ai_processing_record_id ==
    superseded_record.ai_processing_record_id`) replaces a *technical
    processing attempt* — never in response to any change to
    `superseded_record` itself, which never changes (19c.1/19c.2)."""
    return _build_event(
        event_type="ai.processing_record_superseded",
        event_id=event_id,
        record=superseded_record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        extra_payload={
            "superseded_by_ai_processing_record_id": str(superseding_record.ai_processing_record_id)
        },
    )


def build_output_reviewed_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.output_reviewed",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_output_accepted_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.output_accepted",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_output_corrected_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`ai.output_corrected` — canon 0.5.0 corrected this event's name
    (previously the typo `ai.output.corrected`)."""
    return _build_event(
        event_type="ai.output_corrected",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_output_rejected_event(
    *,
    event_id: UUID,
    record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_event(
        event_type="ai.output_rejected",
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_review_outcome_superseded_event(
    *,
    event_id: UUID,
    superseded_record: AIProcessingRecord,
    superseding_record: AIProcessingRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Canon 20.12: the same mechanism as
    `build_processing_record_superseded_event`, emitted instead when the
    replacement is of a *human review outcome* (19c.2)."""
    return _build_event(
        event_type="ai.review_outcome_superseded",
        event_id=event_id,
        record=superseded_record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        extra_payload={
            "superseded_by_ai_processing_record_id": str(superseding_record.ai_processing_record_id)
        },
    )
