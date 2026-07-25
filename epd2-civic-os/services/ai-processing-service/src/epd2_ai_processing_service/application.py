"""AI Processing Service application layer: `request_ai_processing`,
`prepare_input`, `begin_processing`, `complete_processing_with_provider`,
`fail_processing`, `reject_processing_by_policy`, `review_ai_output`,
`supersede_ai_processing_record`, `create_disclosure_package`,
`publish_ai_disclosure`, plus the read functions
`get_ai_processing_record`, `get_disclosure_status`,
`get_effective_human_review_status`, and the two assert-style read
helpers other services call before their own finalize command,
`assert_consequential_output_reviewed` and
`assert_disclosure_complete_for_official_finalization` — canon section
17.1/19c, canon section 20.12's event catalog, ADR-021 through ADR-025.

Every state-changing command below accepts an optional caller-supplied
`event_id` (CT-00-04), the same idempotency pattern every prior pack's
services already establish.

**Cross-pack boundary (ADR-022):** this module imports exactly one
`governance-service` function,
`epd2_governance_service.application.verify_role_assignment_for_action`
— never `.domain`, never any other `.application` function. Its own
`role_assignment_store` parameter is accepted as `Any` (the same
convention `epd2_voting_service.application.invalidate_ballot` already
uses for its own `governance_decision_store` passthrough parameter,
ADR-017) — this module has no import of
`epd2_governance_service.storage`/`.domain` anywhere, so it cannot reach
past `governance-service`'s own public application-layer contract, and
never sees, stores, or recomputes a `RoleAssignment`'s own fields
(`role_code`, `scope_id`, `status`, `valid_from`/`valid_until`) — see
`tests/repository/test_service_boundaries.py`.

**Disclosure protocol (ADR-025 §5):** `publish_ai_disclosure` calls
`epd2_transparency_service.application.publish_ledger_entry` directly
(its own `ledger_store`/`policy_store`/`transparency_audit_store`
parameters are likewise `Any` passthroughs) — `ai-processing-service`
never writes `PublicLedgerEntry` itself; `transparency-service` remains
the sole writer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_ai_processing_service.domain import (
    PURPOSE_CODES,
    AIDisclosurePackage,
    AIProcessingRecord,
    DisclosureStatus,
    HumanReviewStatus,
    ProcessingStatus,
    RedactionResult,
    UseClass,
    assert_purpose_target_combination_allowed,
    derive_disclosure_status,
    derive_effective_human_review_status,
    required_reviewer_role_codes,
    review_requires_independent_reviewer,
)
from epd2_ai_processing_service.events import (
    ai_processing_record_full_state_payload,
    build_input_prepared_event,
    build_output_accepted_event,
    build_output_corrected_event,
    build_output_created_event,
    build_output_rejected_event,
    build_output_reviewed_event,
    build_processing_failed_event,
    build_processing_record_superseded_event,
    build_processing_rejected_by_policy_event,
    build_processing_requested_event,
    build_review_outcome_superseded_event,
)
from epd2_ai_processing_service.exceptions import (
    AIConsequentialOutputNotReviewedError,
    AIHumanReviewerMissingError,
    AIInputProvenanceUnverifiedError,
    AIOutputRejectedByHumanError,
    AIPolicyConflictError,
    AIProcessingRecordSupersededError,
    AIPublicDisclosureRequiredError,
    AIReviewerRoleInvalidError,
    AIReviewerScopeMismatchError,
    AIReviewSelfApprovalProhibitedError,
    PermissionDeniedError,
    UnknownAIProcessingRecordError,
)
from epd2_ai_processing_service.provider import (
    AIModelProvider,
    PreparedInputSubmission,
    assert_external_provider_use_allowed,
)
from epd2_ai_processing_service.redaction import RedactionValidationRequest, RedactionValidator
from epd2_ai_processing_service.storage import AIProcessingRecordStore
from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_governance_service.application import verify_role_assignment_for_action
from epd2_transparency_service.application import publish_ledger_entry

AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "ai-processing-service"
_RECORD_AUDIT = "AI_PROCESSING_RECORD_STATUS_CHANGED"


def _require_record(
    store: AIProcessingRecordStore, ai_processing_record_id: UUID
) -> AIProcessingRecord:
    record = store.get(ai_processing_record_id)
    if record is None:
        raise UnknownAIProcessingRecordError(
            f"unknown ai_processing_record_id: {ai_processing_record_id}"
        )
    return record


def _append_audit(
    audit_store: AuditEventStore,
    *,
    resolved_event_id: UUID,
    action: str,
    reason_code: str,
    target_id: UUID,
    correlation_id: UUID,
    actor: ActorRef,
    before_hash: str,
    after_hash: str,
    clock: Clock,
) -> AuditEvent:
    return append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="ai_processing_record_status_changed",
            occurred_at=clock.now(),
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="ai_processing_record",
            target_id=target_id,
            action=action,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=after_hash,
        ),
        clock=clock,
    )


@dataclass(frozen=True, slots=True)
class RequestAIProcessingResult:
    record: AIProcessingRecord
    event: EventEnvelope
    review_requested_event: EventEnvelope | None
    audit_event: AuditEvent


def request_ai_processing(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    purpose_code: str,
    target_type: str,
    target_id: UUID,
    input_version: str,
    model_provider: str,
    model_name: str,
    model_version: str,
    prompt_template_version: str,
    is_consequential: bool,
    disclosure_required: bool = False,
    deployment_version: str | None = None,
    system_policy_version: str | None = None,
    generation_settings: dict[str, object] | None = None,
    processing_region: str | None = None,
    data_retention_mode: str | None = None,
    external_provider_flag: bool = False,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> RequestAIProcessingResult:
    """Create a new `AIProcessingRecord` in `processing_status =
    requested` (canon 17.1/19c.1). `human_review_status` is decided once,
    here: `pending` if `is_consequential` (19c.1: must start from the value
    "pending"), else `not_required` (19c.8: only ever admissible
    for non-consequential output). When `is_consequential`, this command
    emits a *second* event, `ai.output_reviewed`, alongside
    `ai.processing_requested` — the same "one command, two events"
    convention `governance-service.activate_governance_policy` already
    establishes for its own paired transition (`ActivateGovernancePolicyResult`).

    `purpose_code`/`target_type` are validated against this pack's own
    repository-side closed allow-lists (ADR-025 §2) before the record is
    created at all.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to request AI processing")
    if purpose_code not in PURPOSE_CODES:
        raise ValueError(f"purpose_code {purpose_code!r} is not a recognized use class")
    use_class = UseClass(purpose_code)
    assert_purpose_target_combination_allowed(use_class, target_type)
    assert_external_provider_use_allowed(
        use_class,
        external_provider_flag=external_provider_flag,
        processing_region=processing_region,
        data_retention_mode=data_retention_mode,
    )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = record_store.get(ai_processing_record_id)
        if record is None:
            raise UnknownAIProcessingRecordError(
                f"idempotent replay for event_id {resolved_event_id} found no ai_processing_record "
                f"{ai_processing_record_id}"
            )
        event = build_processing_requested_event(
            event_id=resolved_event_id,
            record=record,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        review_requested_event = (
            build_output_reviewed_event(
                event_id=generate_uuid(),
                record=record,
                actor=actor,
                correlation_id=correlation_id,
                causation_id=resolved_event_id,
                occurred_at=existing_audit.occurred_at,
            )
            if is_consequential
            else None
        )
        return RequestAIProcessingResult(
            record=record,
            event=event,
            review_requested_event=review_requested_event,
            audit_event=existing_audit,
        )

    now = clock.now()
    record = AIProcessingRecord(
        ai_processing_record_id=ai_processing_record_id,
        purpose_code=purpose_code,
        target_type=target_type,
        target_id=target_id,
        input_version=input_version,
        model_provider=model_provider,
        model_name=model_name,
        model_version=model_version,
        prompt_template_version=prompt_template_version,
        output_reference=None,
        created_at=now,
        human_review_status=(
            HumanReviewStatus.PENDING if is_consequential else HumanReviewStatus.NOT_REQUIRED
        ),
        correction_reference=None,
        processing_status=ProcessingStatus.REQUESTED,
        supersedes_ai_processing_record_id=None,
        deployment_version=deployment_version,
        system_policy_version=system_policy_version,
        generation_settings=generation_settings,
        processing_region=processing_region,
        data_retention_mode=data_retention_mode,
        external_provider_flag=external_provider_flag,
        input_hash=None,
        output_hash=None,
        confidence_score=None,
        uncertainty_indicator=None,
        explanation_reference=None,
        reason_codes=(),
        human_reviewer_reference=None,
        completed_at=None,
        reviewed_at=None,
        redaction_manifest=None,
        disclosure_required=disclosure_required,
        disclosure_package_reference=None,
        disclosure_receipt_reference=None,
    )
    record = record_store.create(record)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="request_ai_processing",
        reason_code=_RECORD_AUDIT,
        target_id=record.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash="",
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(record)),
        clock=clock,
    )
    event = build_processing_requested_event(
        event_id=resolved_event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    review_requested_event = (
        build_output_reviewed_event(
            event_id=generate_uuid(),
            record=record,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=audit_event.occurred_at,
        )
        if is_consequential
        else None
    )
    return RequestAIProcessingResult(
        record=record,
        event=event,
        review_requested_event=review_requested_event,
        audit_event=audit_event,
    )


@dataclass(frozen=True, slots=True)
class PrepareInputResult:
    record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def prepare_input(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    redaction_validator: RedactionValidator,
    input_reference: str,
    declared_input_classification: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> PrepareInputResult:
    """`requested -> input_prepared` (or, on a failed validation,
    `requested -> rejected_by_policy` directly — canon 19c.1's allowed
    transitions). **`ai-processing-service` performs the redaction/
    provenance check itself**, by calling `redaction_validator.validate`
    — never by trusting a caller-supplied `redaction_applied`-style flag
    (required scope item 6). `declared_input_classification` must be
    non-empty; an unclassified/unverifiable input is rejected before any
    validator call at all (`AIInputProvenanceUnverifiedError`, required
    scope item 11's "unverified input provenance")."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to prepare AI processing input")
    if not declared_input_classification:
        raise AIInputProvenanceUnverifiedError(
            "declared_input_classification must be established before redaction validation can run"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        event = _build_prepare_result_event(
            record, resolved_event_id, actor, correlation_id, existing_audit.occurred_at
        )
        return PrepareInputResult(record=record, event=event, audit_event=existing_audit)

    record = _require_record(record_store, ai_processing_record_id)
    now = clock.now()
    manifest = redaction_validator.validate(
        RedactionValidationRequest(
            ai_processing_record_id=ai_processing_record_id,
            input_reference=input_reference,
            declared_input_classification=declared_input_classification,
            now=now,
        )
    )
    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))

    if manifest.result is RedactionResult.FAIL:
        updated = record.with_processing_status(
            ProcessingStatus.REJECTED_BY_POLICY,
            redaction_manifest=manifest,
            reason_codes=("AI_REDACTION_FAILURE",),
        )
        event_builder = build_processing_rejected_by_policy_event
        action = "reject_processing_by_policy_redaction_failure"
    else:
        updated = record.with_processing_status(
            ProcessingStatus.INPUT_PREPARED,
            redaction_manifest=manifest,
            input_hash=manifest.prepared_input_hash,
        )
        event_builder = build_input_prepared_event
        action = "prepare_input"

    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action=action,
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    event = event_builder(
        event_id=resolved_event_id,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return PrepareInputResult(record=updated, event=event, audit_event=audit_event)


def _build_prepare_result_event(
    record: AIProcessingRecord,
    event_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    builder = (
        build_processing_rejected_by_policy_event
        if record.processing_status is ProcessingStatus.REJECTED_BY_POLICY
        else build_input_prepared_event
    )
    return builder(
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=occurred_at,
    )


@dataclass(frozen=True, slots=True)
class BeginProcessingResult:
    record: AIProcessingRecord
    audit_event: AuditEvent


def begin_processing(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> BeginProcessingResult:
    """`input_prepared -> processing` — a transient state with no canon
    20.12 event of its own (audited only), the same convention
    `governance-service.begin_technical_challenge_review` already
    establishes."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to begin AI processing")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        return BeginProcessingResult(record=record, audit_event=existing_audit)

    record = _require_record(record_store, ai_processing_record_id)
    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    updated = record.with_processing_status(ProcessingStatus.PROCESSING)
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="begin_processing",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    return BeginProcessingResult(record=updated, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class CompleteProcessingResult:
    record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def complete_processing_with_provider(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    provider: AIModelProvider,
    prepared_input_reference: str,
    timeout_seconds: float,
    confidence_threshold: float = 0.0,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CompleteProcessingResult:
    """`processing -> completed` on a usable provider result at or above
    `confidence_threshold`; `processing -> failed` on any provider error
    (`exceptions.AIModelUnavailableError`/`AIProcessingTimeoutError`/
    `AIOutputMalformedError`/`AIModelVersionUnsupportedError`) or a
    below-threshold confidence score (fail-closed, required scope item
    11). `provider` is never handed any callback/tool/command interface
    (see `provider.AIModelProvider`'s own docstring) — Civic OS mutation
    authority never reaches a model provider."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to complete AI processing")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        builder = (
            build_processing_failed_event
            if record.processing_status is ProcessingStatus.FAILED
            else build_output_created_event
        )
        event = builder(
            event_id=resolved_event_id,
            record=record,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return CompleteProcessingResult(record=record, event=event, audit_event=existing_audit)

    record = _require_record(record_store, ai_processing_record_id)
    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    now = clock.now()

    try:
        outcome = provider.submit(
            PreparedInputSubmission(
                ai_processing_record_id=ai_processing_record_id,
                model_provider=record.model_provider,
                model_name=record.model_name,
                model_version=record.model_version,
                deployment_version=record.deployment_version,
                processing_region=record.processing_region,
                data_retention_mode=record.data_retention_mode,
                external_provider_flag=record.external_provider_flag,
                prepared_input_reference=prepared_input_reference,
                generation_settings=(
                    dict(record.generation_settings)
                    if record.generation_settings is not None
                    else None
                ),
                timeout_seconds=timeout_seconds,
            )
        )
    except Exception as exc:
        reason_code = getattr(exc, "reason_code", "AI_MODEL_UNAVAILABLE")
        updated = record.with_processing_status(
            ProcessingStatus.FAILED, reason_codes=(reason_code,), completed_at=now
        )
        record_store.save(updated)
        audit_event = _append_audit(
            audit_store,
            resolved_event_id=resolved_event_id,
            action="fail_processing_provider_error",
            reason_code=_RECORD_AUDIT,
            target_id=updated.ai_processing_record_id,
            correlation_id=correlation_id,
            actor=actor,
            before_hash=before_hash,
            after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
            clock=clock,
        )
        event = build_processing_failed_event(
            event_id=resolved_event_id,
            record=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=audit_event.occurred_at,
        )
        return CompleteProcessingResult(record=updated, event=event, audit_event=audit_event)

    if outcome.confidence_score is not None and outcome.confidence_score < confidence_threshold:
        updated = record.with_processing_status(
            ProcessingStatus.FAILED,
            reason_codes=("AI_CONFIDENCE_BELOW_THRESHOLD", *outcome.reason_codes),
            completed_at=now,
        )
        record_store.save(updated)
        audit_event = _append_audit(
            audit_store,
            resolved_event_id=resolved_event_id,
            action="fail_processing_low_confidence",
            reason_code=_RECORD_AUDIT,
            target_id=updated.ai_processing_record_id,
            correlation_id=correlation_id,
            actor=actor,
            before_hash=before_hash,
            after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
            clock=clock,
        )
        event = build_processing_failed_event(
            event_id=resolved_event_id,
            record=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=audit_event.occurred_at,
        )
        return CompleteProcessingResult(record=updated, event=event, audit_event=audit_event)

    updated = record.with_processing_status(
        ProcessingStatus.COMPLETED,
        output_reference=outcome.output_reference,
        output_hash=outcome.output_hash,
        confidence_score=outcome.confidence_score,
        uncertainty_indicator=outcome.uncertainty_indicator,
        explanation_reference=outcome.explanation_reference,
        reason_codes=outcome.reason_codes,
        completed_at=now,
    )
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="complete_processing",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    event = build_output_created_event(
        event_id=resolved_event_id,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return CompleteProcessingResult(record=updated, event=event, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class FailProcessingResult:
    record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def fail_processing(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    reason_codes: tuple[str, ...],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> FailProcessingResult:
    """`processing -> failed`, for a failure this pack's own
    orchestration detects independently of a specific `provider.submit`
    call (e.g. an externally observed timeout) — the direct counterpart
    to `complete_processing_with_provider`'s own internal failure path."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to fail AI processing")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        event = build_processing_failed_event(
            event_id=resolved_event_id,
            record=record,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return FailProcessingResult(record=record, event=event, audit_event=existing_audit)

    record = _require_record(record_store, ai_processing_record_id)
    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    updated = record.with_processing_status(
        ProcessingStatus.FAILED, reason_codes=reason_codes, completed_at=clock.now()
    )
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="fail_processing",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    event = build_processing_failed_event(
        event_id=resolved_event_id,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return FailProcessingResult(record=updated, event=event, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class RejectProcessingByPolicyResult:
    record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def reject_processing_by_policy(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    reason_codes: tuple[str, ...],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> RejectProcessingByPolicyResult:
    """`{requested | input_prepared | processing} -> rejected_by_policy`
    for a policy rejection unrelated to redaction (e.g. a detected
    prompt-injection signal or prohibited-data finding surfaced by
    orchestration outside `prepare_input`'s own redaction check)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to reject AI processing by policy")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        event = build_processing_rejected_by_policy_event(
            event_id=resolved_event_id,
            record=record,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return RejectProcessingByPolicyResult(
            record=record, event=event, audit_event=existing_audit
        )

    record = _require_record(record_store, ai_processing_record_id)
    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    updated = record.with_processing_status(
        ProcessingStatus.REJECTED_BY_POLICY, reason_codes=reason_codes, completed_at=clock.now()
    )
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="reject_processing_by_policy",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    event = build_processing_rejected_by_policy_event(
        event_id=resolved_event_id,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return RejectProcessingByPolicyResult(record=updated, event=event, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class ReviewAIOutputResult:
    record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def review_ai_output(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    role_assignment_store: Any,
    *,
    ai_processing_record_id: UUID,
    reviewer_role_assignment_id: UUID,
    reviewer_subject_scope_id: UUID,
    requesting_actor_reference: UUID,
    is_official_publication: bool,
    outcome: HumanReviewStatus,
    corrected_output_reference: str | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ReviewAIOutputResult:
    """`pending -> {approved | approved_with_changes | rejected}`
    (19c.1). Caller-supplied `actor_is_authorized` alone is never
    sufficient here (ADR-022) — reviewer authorization is additionally,
    always verified via `governance-service.verify_role_assignment_for_action`.
    `requesting_actor_reference` is the opaque actor reference the
    caller itself resolved for whoever originally submitted this AI
    processing run (this pack stores no such field on
    `AIProcessingRecord` itself, canon 17.1/19c has none) — compared
    against the verified reviewer's own actor reference to enforce
    19c.8's "the reviewer must differ from the actor who submitted the
    request" rule wherever `review_requires_independent_reviewer` says
    self-review is prohibited outright, not merely discouraged.

    `is_official_publication = True` requires the reviewer hold
    `ai_publication_reviewer` specifically (this pack's own reading of
    ADR-022/ADR-025 §3's "one plus `ai_publication_reviewer`" — see
    `README.md`), superseding the use class's ordinary base role for
    this one review call.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to review AI output")
    if outcome not in (
        HumanReviewStatus.APPROVED,
        HumanReviewStatus.APPROVED_WITH_CHANGES,
        HumanReviewStatus.REJECTED,
    ):
        raise ValueError("outcome must be approved, approved_with_changes, or rejected")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        record = _require_record(record_store, ai_processing_record_id)
        event = _build_review_event(
            record, resolved_event_id, actor, correlation_id, existing_audit.occurred_at
        )
        return ReviewAIOutputResult(record=record, event=event, audit_event=existing_audit)

    record = _require_record(record_store, ai_processing_record_id)
    if record.human_review_status is not HumanReviewStatus.PENDING:
        raise AIConsequentialOutputNotReviewedError(
            f"ai_processing_record {ai_processing_record_id} is not awaiting review "
            f"(human_review_status={record.human_review_status.value!r})"
        )

    use_class = UseClass(record.purpose_code)
    required_roles = (
        frozenset({"ai_publication_reviewer"})
        if is_official_publication
        else required_reviewer_role_codes(use_class, record.target_type)
    )
    now = clock.now()
    verification = verify_role_assignment_for_action(
        role_assignment_store,
        role_assignment_id=reviewer_role_assignment_id,
        required_role_codes=required_roles,
        required_scope_id=reviewer_subject_scope_id,
        action_code=f"ai_review:{use_class.value}",
        evaluated_at=now,
    )
    if not verification.authorized:
        if verification.reason_code == "ROLE_ASSIGNMENT_SCOPE_MISMATCH":
            raise AIReviewerScopeMismatchError(
                f"reviewer_role_assignment_id {reviewer_role_assignment_id} does not cover "
                f"scope {reviewer_subject_scope_id}"
            )
        raise AIReviewerRoleInvalidError(
            f"reviewer_role_assignment_id {reviewer_role_assignment_id} is not an active, "
            f"correctly-roled reviewer for this action (governance reason_code="
            f"{verification.reason_code!r})"
        )

    if (
        review_requires_independent_reviewer(
            use_class, is_official_publication=is_official_publication
        )
        and verification.verified_actor_reference == requesting_actor_reference
    ):
        raise AIReviewSelfApprovalProhibitedError(
            "the reviewer must be a different actor from the one who submitted this AI "
            "processing request for this use class"
        )

    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    reviewer_reference = verification.verified_actor_reference
    assert reviewer_reference is not None  # guaranteed by authorized=True above

    if outcome is HumanReviewStatus.REJECTED:
        updated = record.with_human_review_status(
            HumanReviewStatus.REJECTED,
            human_reviewer_reference=reviewer_reference,
            reviewed_at=now,
        )
        event_builder = build_output_rejected_event
        action = "reject_ai_output"
    elif outcome is HumanReviewStatus.APPROVED:
        updated = record.with_human_review_status(
            HumanReviewStatus.APPROVED,
            human_reviewer_reference=reviewer_reference,
            reviewed_at=now,
        )
        event_builder = build_output_accepted_event
        action = "accept_ai_output"
    else:
        updated = record.with_human_review_status(
            HumanReviewStatus.APPROVED_WITH_CHANGES,
            human_reviewer_reference=reviewer_reference,
            reviewed_at=now,
            output_reference=corrected_output_reference,
        )
        event_builder = build_output_corrected_event
        action = "correct_ai_output"

    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action=action,
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    event = event_builder(
        event_id=resolved_event_id,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return ReviewAIOutputResult(record=updated, event=event, audit_event=audit_event)


def _build_review_event(
    record: AIProcessingRecord,
    event_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    builder = {
        HumanReviewStatus.REJECTED: build_output_rejected_event,
        HumanReviewStatus.APPROVED: build_output_accepted_event,
        HumanReviewStatus.APPROVED_WITH_CHANGES: build_output_corrected_event,
    }[record.human_review_status]
    return builder(
        event_id=event_id,
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=occurred_at,
    )


@dataclass(frozen=True, slots=True)
class SupersedeResult:
    superseded_record: AIProcessingRecord
    superseding_record: AIProcessingRecord
    event: EventEnvelope
    audit_event: AuditEvent


def supersede_ai_processing_record(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    superseded_ai_processing_record_id: UUID,
    new_record: AIProcessingRecord,
    supersession_kind: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> SupersedeResult:
    """Creates `new_record` (a brand-new row, already constructed by the
    caller with `supersedes_ai_processing_record_id ==
    superseded_ai_processing_record_id`) — the *only* mechanism by which
    either a technical processing attempt or a human review outcome is
    ever corrected (19c.2); the superseded row's own fields are never
    rewritten. `supersession_kind` (`"processing"` or `"review"`)
    selects which of the two canon 20.12 events fires — the field itself
    does not determine this; the caller's own reason for the
    replacement does."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to supersede an AI processing record")
    if supersession_kind not in ("processing", "review"):
        raise ValueError("supersession_kind must be 'processing' or 'review'")
    if new_record.supersedes_ai_processing_record_id != superseded_ai_processing_record_id:
        raise ValueError(
            "new_record.supersedes_ai_processing_record_id must equal "
            "superseded_ai_processing_record_id"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        superseded = _require_record(record_store, superseded_ai_processing_record_id)
        superseding = _require_record(record_store, new_record.ai_processing_record_id)
        event_builder = (
            build_processing_record_superseded_event
            if supersession_kind == "processing"
            else build_review_outcome_superseded_event
        )
        event = event_builder(
            event_id=resolved_event_id,
            superseded_record=superseded,
            superseding_record=superseding,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return SupersedeResult(
            superseded_record=superseded,
            superseding_record=superseding,
            event=event,
            audit_event=existing_audit,
        )

    superseded = _require_record(record_store, superseded_ai_processing_record_id)
    if record_store.find_superseding(superseded_ai_processing_record_id) is not None:
        raise AIProcessingRecordSupersededError(
            f"ai_processing_record {superseded_ai_processing_record_id} has already been superseded"
        )

    superseding = record_store.create(new_record)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action=f"supersede_ai_processing_record_{supersession_kind}",
        reason_code=_RECORD_AUDIT,
        target_id=superseding.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash="",
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(superseding)),
        clock=clock,
    )
    event_builder = (
        build_processing_record_superseded_event
        if supersession_kind == "processing"
        else build_review_outcome_superseded_event
    )
    event = event_builder(
        event_id=resolved_event_id,
        superseded_record=superseded,
        superseding_record=superseding,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=audit_event.occurred_at,
    )
    return SupersedeResult(
        superseded_record=superseded,
        superseding_record=superseding,
        event=event,
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# Mandatory disclosure protocol (19c.7, ADR-025 §5)
# ---------------------------------------------------------------------------


def assert_consequential_output_reviewed(record: AIProcessingRecord) -> None:
    """Fail-closed gate (required scope item 11/18): a consequential
    output may never be incorporated, published, or acted upon before
    `human_review_status` has reached `approved`/`approved_with_changes`
    (`AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`, ADR-024). Distinguishes a
    never-reviewed record (`AI_HUMAN_REVIEWER_MISSING`) from an
    explicitly rejected one (`AI_OUTPUT_REJECTED_BY_HUMAN`) for a more
    specific error where possible."""
    if record.human_review_status in (
        HumanReviewStatus.APPROVED,
        HumanReviewStatus.APPROVED_WITH_CHANGES,
    ):
        return
    if record.human_review_status is HumanReviewStatus.REJECTED:
        raise AIOutputRejectedByHumanError(
            f"ai_processing_record {record.ai_processing_record_id} was rejected by human review"
        )
    if record.human_reviewer_reference is None:
        raise AIHumanReviewerMissingError(
            f"ai_processing_record {record.ai_processing_record_id} "
            "has no human reviewer assigned yet"
        )
    raise AIConsequentialOutputNotReviewedError(
        f"ai_processing_record {record.ai_processing_record_id} has not completed human review "
        f"(human_review_status={record.human_review_status.value!r})"
    )


@dataclass(frozen=True, slots=True)
class CreateDisclosurePackageResult:
    record: AIProcessingRecord
    package: AIDisclosurePackage
    audit_event: AuditEvent


def create_disclosure_package(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    *,
    ai_processing_record_id: UUID,
    approved_public_model_category: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CreateDisclosurePackageResult:
    """Disclosure protocol step 1-2 (19c.7): requires verified human
    approval first (`assert_consequential_output_reviewed`), then
    constructs the immutable `AIDisclosurePackage` and records its
    (this pack's own, freshly-minted) opaque reference in
    `disclosure_package_reference` — `DisclosureStatus` becomes
    `pending_publication`. No canon 20.12 event is defined for this step
    specifically (audited only); the package itself is never persisted
    (19c.6)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an AI disclosure package")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    record = _require_record(record_store, ai_processing_record_id)
    if not record.disclosure_required:
        raise AIPolicyConflictError(
            f"ai_processing_record {ai_processing_record_id} does not require disclosure"
        )
    assert_consequential_output_reviewed(record)

    package = AIDisclosurePackage(
        ai_processing_record_reference=record.ai_processing_record_id,
        purpose_code=record.purpose_code,
        approved_public_model_category=approved_public_model_category,
        approved_public_model_version=record.model_version,
        processed_at=record.completed_at if record.completed_at is not None else clock.now(),
        human_review_outcome=record.human_review_status,
        prompt_template_version=record.prompt_template_version,
        system_policy_version=record.system_policy_version or "",
    )

    if existing_audit is not None:
        return CreateDisclosurePackageResult(
            record=record, package=package, audit_event=existing_audit
        )

    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    disclosure_package_reference = generate_uuid()
    updated = record.with_disclosure_package_reference(disclosure_package_reference)
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="create_disclosure_package",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    return CreateDisclosurePackageResult(record=updated, package=package, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class PublishAIDisclosureResult:
    record: AIProcessingRecord
    disclosure_receipt_reference: UUID
    audit_event: AuditEvent


def publish_ai_disclosure(
    record_store: AIProcessingRecordStore,
    audit_store: AuditEventStore,
    ledger_store: Any,
    policy_store: Any,
    transparency_audit_store: Any,
    *,
    ai_processing_record_id: UUID,
    package: AIDisclosurePackage,
    published_by_role_id: UUID,
    subject_event_id: UUID,
    subject_type: Any,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> PublishAIDisclosureResult:
    """Disclosure protocol steps 3-4 (19c.7): publishes `package` through
    `transparency-service`'s existing `publish_ledger_entry` — never a
    direct write to `PublicLedgerEntry`, `transparency-service` remains
    the sole writer — and records the returned
    `public_ledger_entry_id` as `disclosure_receipt_reference`;
    `DisclosureStatus` becomes `published`. Failure to obtain a receipt
    is fail-closed by construction: if `publish_ledger_entry` raises,
    this function propagates the failure and `disclosure_receipt_reference`
    is never set.

    `subject_type` is accepted as `Any` (expected:
    `epd2_transparency_service.domain.LedgerSubjectType.AI_PROCESSING_RECORD`)
    and passed straight through to `publish_ledger_entry` — this module
    never imports `epd2_transparency_service.domain` itself (INV-03: a
    cross-pack dependency is `.application`-only, never `.domain`/
    `.storage`; `tests/repository/test_service_boundaries.py`). The
    caller (whichever composition root already has both services wired)
    resolves the actual enum value."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to publish an AI disclosure")

    record = _require_record(record_store, ai_processing_record_id)
    if record.disclosure_package_reference is None:
        raise AIPublicDisclosureRequiredError(
            f"ai_processing_record {ai_processing_record_id} has no disclosure package to publish"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None and record.disclosure_receipt_reference is not None:
        return PublishAIDisclosureResult(
            record=record,
            disclosure_receipt_reference=record.disclosure_receipt_reference,
            audit_event=existing_audit,
        )

    ledger_result = publish_ledger_entry(
        ledger_store,
        policy_store,
        transparency_audit_store,
        public_ledger_entry_id=generate_uuid(),
        subject_type=subject_type,
        subject_id=record.ai_processing_record_id,
        subject_event_id=subject_event_id,
        raw_content=package.to_raw_content(),
        published_by_role_id=published_by_role_id,
        redaction_notice=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )

    before_hash = compute_payload_hash(ai_processing_record_full_state_payload(record))
    disclosure_receipt_reference = ledger_result.entry.public_ledger_entry_id
    updated = record.with_disclosure_receipt_reference(disclosure_receipt_reference)
    record_store.save(updated)
    audit_event = _append_audit(
        audit_store,
        resolved_event_id=resolved_event_id,
        action="publish_ai_disclosure",
        reason_code=_RECORD_AUDIT,
        target_id=updated.ai_processing_record_id,
        correlation_id=correlation_id,
        actor=actor,
        before_hash=before_hash,
        after_hash=compute_payload_hash(ai_processing_record_full_state_payload(updated)),
        clock=clock,
    )
    return PublishAIDisclosureResult(
        record=updated,
        disclosure_receipt_reference=disclosure_receipt_reference,
        audit_event=audit_event,
    )


def assert_disclosure_complete_for_official_finalization(
    record_store: AIProcessingRecordStore, *, ai_processing_record_id: UUID
) -> None:
    """The read-only gate an *owning* service calls, from its own
    finalize command, before completing an official/public artifact
    (19c.7 step 5) — `ai-processing-service` never marks another
    entity "finalized" itself; it only ever answers this question,
    mirroring `governance-service.get_finality_status`'s own role as a
    read another service's command consults. Raises
    `AIPublicDisclosureRequiredError` (fail-closed) unless
    `disclosure_required` is `False`, or `DisclosureStatus = published`
    and `disclosure_receipt_reference` is present."""
    record = _require_record(record_store, ai_processing_record_id)
    if not record.disclosure_required:
        return
    if (
        derive_disclosure_status(record) is not DisclosureStatus.PUBLISHED
        or record.disclosure_receipt_reference is None
    ):
        raise AIPublicDisclosureRequiredError(
            f"ai_processing_record {ai_processing_record_id} requires a published disclosure "
            "before the owning artifact may be finalized"
        )


# ---------------------------------------------------------------------------
# Plain reads
# ---------------------------------------------------------------------------


def get_ai_processing_record(
    store: AIProcessingRecordStore, *, ai_processing_record_id: UUID
) -> AIProcessingRecord | None:
    """Plain, unaudited read of one `AIProcessingRecord` by id."""
    return store.get(ai_processing_record_id)


def get_disclosure_status(
    store: AIProcessingRecordStore, *, ai_processing_record_id: UUID
) -> DisclosureStatus:
    record = _require_record(store, ai_processing_record_id)
    return derive_disclosure_status(record)


def get_effective_human_review_status(
    store: AIProcessingRecordStore, *, ai_processing_record_id: UUID
) -> HumanReviewStatus:
    """The derived read model surfacing `human_review_status =
    superseded` (19c.1) — never the stored field directly."""
    record = _require_record(store, ai_processing_record_id)
    superseding = store.find_superseding(ai_processing_record_id)
    return derive_effective_human_review_status(record, superseding_record=superseding)
