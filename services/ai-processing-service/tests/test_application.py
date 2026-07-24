"""Application-layer tests for AI Processing Service. Covers CT-00-04
(event idempotency), CT-00-06 (missing permission), CT-00-07 (audit
creation), plus the pack's own processing/review/supersession/disclosure
lifecycle rules (ADR-021 through ADR-025) and the eight required
end-to-end fail-closed proofs (required scope item 18).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_ai_processing_service import application as app
from epd2_ai_processing_service.domain import (
    AIProcessingRecord,
    ForbiddenProcessingStatusTransitionError,
    HumanReviewStatus,
    ProcessingStatus,
    RedactionManifest,
    RedactionResult,
)
from epd2_ai_processing_service.exceptions import (
    AIHumanReviewerMissingError,
    AIOutputRejectedByHumanError,
    AIPolicyConflictError,
    AIProcessingRecordSupersededError,
    AIPublicDisclosureRequiredError,
    AIReviewerRoleInvalidError,
    AIReviewerScopeMismatchError,
    AIReviewSelfApprovalProhibitedError,
    PermissionDeniedError,
)
from epd2_ai_processing_service.provider import (
    PreparedInputSubmission,
    ProviderOutcome,
    ScriptedAIModelProvider,
)
from epd2_ai_processing_service.redaction import ScriptedRedactionValidator
from epd2_ai_processing_service.storage import InMemoryAIProcessingRecordStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_governance_service.domain import GLOBAL_SCOPE_ID, RoleAssignment, RoleAssignmentStatus
from epd2_governance_service.storage import InMemoryRoleAssignmentStore
from epd2_transparency_service.application import (
    activate_disclosure_policy,
    define_disclosure_policy,
)
from epd2_transparency_service.domain import (
    DisclosureClass,
    FieldRule,
    LedgerSubjectType,
    Transformation,
)
from epd2_transparency_service.storage import (
    InMemoryDisclosurePolicyStore,
    InMemoryPublicLedgerEntryStore,
)

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


class Fixture:
    def __init__(self) -> None:
        self.clock = FixedClock(NOW)
        self.audit_store = InMemoryAuditEventStore()
        self.record_store = InMemoryAIProcessingRecordStore()
        self.role_store = InMemoryRoleAssignmentStore()
        self.ledger_store = InMemoryPublicLedgerEntryStore()
        self.policy_store = InMemoryDisclosurePolicyStore()
        self.transparency_audit_store = InMemoryAuditEventStore()

    def grant_reviewer(
        self, role_code: str, *, scope_id: object = GLOBAL_SCOPE_ID
    ) -> RoleAssignment:
        return self.role_store.create(
            RoleAssignment(
                role_assignment_id=uuid4(),
                actor_id=uuid4(),
                role_code=role_code,
                scope_id=scope_id,  # type: ignore[arg-type]
                valid_from=NOW,
                valid_until=None,
                assigned_by=uuid4(),
                approval_reference=None,
                status=RoleAssignmentStatus.ACTIVE,
            )
        )

    def request_record(
        self, *, is_consequential: bool = False, **overrides: object
    ) -> app.RequestAIProcessingResult:
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
            "is_consequential": is_consequential,
            "actor": ACTOR,
            "actor_is_authorized": True,
            "correlation_id": uuid4(),
            "clock": self.clock,
        }
        fields.update(overrides)
        return app.request_ai_processing(self.record_store, self.audit_store, **fields)  # type: ignore[arg-type]

    def activate_ai_processing_disclosure_policy(self) -> None:
        """Pure test-fixture setup: constructs an active `DisclosurePolicy`
        for `subject_type = ai_processing_record` using transparency-
        service's own already-existing application functions directly -
        no ADR authorizes ai-processing-service (or this implementation
        task) to create/activate this policy as production code; it is
        transparency-service's own separate governance concern."""
        field_paths = [
            "ai_processing_record_reference",
            "purpose_code",
            "approved_public_model_category",
            "approved_public_model_version",
            "processed_at",
            "human_review_outcome",
            "prompt_template_version",
            "system_policy_version",
        ]
        rules = tuple(
            FieldRule(
                field_path=path,
                disclosure_class=DisclosureClass.PUBLIC,
                transformation=Transformation.NONE,
                replacement_label=None,
            )
            for path in field_paths
        )
        policy_id = uuid4()
        define_disclosure_policy(
            self.policy_store,
            self.transparency_audit_store,
            disclosure_policy_id=policy_id,
            applies_to_subject_type=LedgerSubjectType.AI_PROCESSING_RECORD.value,
            field_rules=rules,
            effective_from=NOW,
            version=1,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=self.clock,
        )
        activate_disclosure_policy(
            self.policy_store,
            self.transparency_audit_store,
            disclosure_policy_id=policy_id,
            approved_by_role_id=uuid4(),
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=self.clock,
        )


@pytest.fixture
def fx() -> Fixture:
    return Fixture()


def _manifest(*, result: RedactionResult = RedactionResult.PASS) -> RedactionManifest:
    return RedactionManifest(
        redaction_policy_reference="policy-1",
        redaction_policy_version="1.0",
        input_classification="public",
        checked_field_categories=("identity", "credential", "vote_linkage"),
        removed_field_categories=() if result is RedactionResult.PASS else ("identity",),
        prepared_input_hash="hash-1",
        validator_version="1.0",
        validated_at=NOW,
        result=result,
    )


# --- request_ai_processing ---------------------------------------------------


def test_request_ai_processing_non_consequential_starts_not_required(fx: Fixture) -> None:
    result = fx.request_record(is_consequential=False)
    assert result.record.human_review_status is HumanReviewStatus.NOT_REQUIRED
    assert result.review_requested_event is None


def test_request_ai_processing_consequential_starts_pending_and_emits_review_event(
    fx: Fixture,
) -> None:
    result = fx.request_record(is_consequential=True)
    assert result.record.human_review_status is HumanReviewStatus.PENDING
    assert result.review_requested_event is not None
    assert result.review_requested_event.event_type == "ai.output_reviewed"


def test_request_ai_processing_permission_denied(fx: Fixture) -> None:
    with pytest.raises(PermissionDeniedError):
        fx.request_record(actor_is_authorized=False)


def test_request_ai_processing_rejects_disallowed_purpose_target_combination(fx: Fixture) -> None:
    with pytest.raises(ValueError):
        fx.request_record(purpose_code="anomaly_indication", target_type="initiative")


def test_request_ai_processing_external_provider_forbidden_for_anomaly_indication(
    fx: Fixture,
) -> None:
    with pytest.raises(AIPolicyConflictError):
        fx.request_record(
            purpose_code="anomaly_indication",
            target_type="participation_pattern_report",
            external_provider_flag=True,
            processing_region="eu",
            data_retention_mode="none",
        )


def test_request_ai_processing_idempotent_replay(fx: Fixture) -> None:
    event_id = uuid4()
    record_id = uuid4()
    first = fx.request_record(ai_processing_record_id=record_id, event_id=event_id)
    second = fx.request_record(ai_processing_record_id=record_id, event_id=event_id)
    assert first.record == second.record
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


# --- prepare_input -------------------------------------------------------------


def test_prepare_input_pass_transitions_to_input_prepared(fx: Fixture) -> None:
    created = fx.request_record()
    validator = ScriptedRedactionValidator(_manifest(result=RedactionResult.PASS))
    result = app.prepare_input(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=created.record.ai_processing_record_id,
        redaction_validator=validator,
        input_reference="input-ref-1",
        declared_input_classification="public",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.processing_status is ProcessingStatus.INPUT_PREPARED
    assert result.record.input_hash == "hash-1"


def test_prepare_input_fail_rejects_by_policy(fx: Fixture) -> None:
    """Required scope item 18: failed redaction prevents provider access
    (the record can never reach `processing` from `rejected_by_policy`)."""
    created = fx.request_record()
    validator = ScriptedRedactionValidator(_manifest(result=RedactionResult.FAIL))
    result = app.prepare_input(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=created.record.ai_processing_record_id,
        redaction_validator=validator,
        input_reference="input-ref-1",
        declared_input_classification="public",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.processing_status is ProcessingStatus.REJECTED_BY_POLICY
    with pytest.raises(ForbiddenProcessingStatusTransitionError):
        app.begin_processing(
            fx.record_store,
            fx.audit_store,
            ai_processing_record_id=result.record.ai_processing_record_id,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_prepare_input_requires_declared_classification(fx: Fixture) -> None:
    created = fx.request_record()
    validator = ScriptedRedactionValidator(_manifest())
    from epd2_ai_processing_service.exceptions import AIInputProvenanceUnverifiedError

    with pytest.raises(AIInputProvenanceUnverifiedError):
        app.prepare_input(
            fx.record_store,
            fx.audit_store,
            ai_processing_record_id=created.record.ai_processing_record_id,
            redaction_validator=validator,
            input_reference="input-ref-1",
            declared_input_classification="",
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


# --- begin_processing / complete_processing_with_provider -----------------------


def _advance_to_processing(fx: Fixture, record_id: UUID) -> None:
    validator = ScriptedRedactionValidator(_manifest())
    app.prepare_input(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        redaction_validator=validator,
        input_reference="input-ref-1",
        declared_input_classification="public",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    app.begin_processing(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )


def test_complete_processing_success(fx: Fixture) -> None:
    created = fx.request_record()
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.9,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    result = app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.processing_status is ProcessingStatus.COMPLETED
    assert result.record.output_reference == "output-ref-1"
    assert len(provider.submitted) == 1


def test_complete_processing_model_unavailable_fails_closed(fx: Fixture) -> None:
    """Required scope item 18 (fail-closed behavior): a provider error
    transitions to `failed`, never `completed`."""
    from epd2_ai_processing_service.exceptions import AIModelUnavailableError

    created = fx.request_record()
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(raises=AIModelUnavailableError("down"))
    result = app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.processing_status is ProcessingStatus.FAILED
    assert "AI_MODEL_UNAVAILABLE" in result.record.reason_codes


def test_complete_processing_low_confidence_fails_closed(fx: Fixture) -> None:
    created = fx.request_record()
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.1,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    result = app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        confidence_threshold=0.5,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.processing_status is ProcessingStatus.FAILED
    assert "AI_CONFIDENCE_BELOW_THRESHOLD" in result.record.reason_codes


# --- review_ai_output -----------------------------------------------------------


def _completed_consequential_record(fx: Fixture) -> AIProcessingRecord:
    created = fx.request_record(is_consequential=True)
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.9,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    completed = app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    return completed.record


def test_review_ai_output_approves(fx: Fixture) -> None:
    record = _completed_consequential_record(fx)
    reviewer = fx.grant_reviewer("ai_output_reviewer")
    result = app.review_ai_output(
        fx.record_store,
        fx.audit_store,
        fx.role_store,
        ai_processing_record_id=record.ai_processing_record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=False,
        outcome=HumanReviewStatus.APPROVED,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.record.human_review_status is HumanReviewStatus.APPROVED
    assert result.record.human_reviewer_reference == reviewer.actor_id


def test_review_ai_output_rejects_invalid_reviewer_role(fx: Fixture) -> None:
    """Required scope item 18: invalid reviewer role is rejected."""
    record = _completed_consequential_record(fx)
    observer = fx.grant_reviewer("observer")
    with pytest.raises(AIReviewerRoleInvalidError):
        app.review_ai_output(
            fx.record_store,
            fx.audit_store,
            fx.role_store,
            ai_processing_record_id=record.ai_processing_record_id,
            reviewer_role_assignment_id=observer.role_assignment_id,
            reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
            requesting_actor_reference=uuid4(),
            is_official_publication=False,
            outcome=HumanReviewStatus.APPROVED,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_review_ai_output_rejects_scope_mismatch(fx: Fixture) -> None:
    """Required scope item 18: reviewer scope mismatch is rejected."""
    record = _completed_consequential_record(fx)
    reviewer = fx.grant_reviewer("ai_output_reviewer", scope_id=uuid4())
    with pytest.raises(AIReviewerScopeMismatchError):
        app.review_ai_output(
            fx.record_store,
            fx.audit_store,
            fx.role_store,
            ai_processing_record_id=record.ai_processing_record_id,
            reviewer_role_assignment_id=reviewer.role_assignment_id,
            reviewer_subject_scope_id=uuid4(),
            requesting_actor_reference=uuid4(),
            is_official_publication=False,
            outcome=HumanReviewStatus.APPROVED,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


def test_review_ai_output_rejects_self_review_for_moderation(fx: Fixture) -> None:
    """Required scope item 18: self-review is rejected where required."""
    created = fx.request_record(
        is_consequential=True, purpose_code="classification", target_type="contribution"
    )
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.9,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    completed = app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    reviewer = fx.grant_reviewer("ai_moderation_reviewer")
    with pytest.raises(AIReviewSelfApprovalProhibitedError):
        app.review_ai_output(
            fx.record_store,
            fx.audit_store,
            fx.role_store,
            ai_processing_record_id=completed.record.ai_processing_record_id,
            reviewer_role_assignment_id=reviewer.role_assignment_id,
            reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
            requesting_actor_reference=reviewer.actor_id,
            is_official_publication=False,
            outcome=HumanReviewStatus.APPROVED,
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


# --- supersede_ai_processing_record ---------------------------------------------


def test_supersede_ai_processing_record(fx: Fixture) -> None:
    created = fx.request_record()
    original = created.record
    # Build the superseding record explicitly (frozen dataclass has no __dict__).
    from dataclasses import replace

    new_record = replace(
        original,
        ai_processing_record_id=uuid4(),
        supersedes_ai_processing_record_id=original.ai_processing_record_id,
    )
    result = app.supersede_ai_processing_record(
        fx.record_store,
        fx.audit_store,
        superseded_ai_processing_record_id=original.ai_processing_record_id,
        new_record=new_record,
        supersession_kind="processing",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert result.event.event_type == "ai.processing_record_superseded"
    assert fx.record_store.find_superseding(original.ai_processing_record_id) is not None


def test_supersede_ai_processing_record_rejects_double_supersession(fx: Fixture) -> None:
    from dataclasses import replace

    created = fx.request_record()
    original = created.record
    first_replacement = replace(
        original,
        ai_processing_record_id=uuid4(),
        supersedes_ai_processing_record_id=original.ai_processing_record_id,
    )
    app.supersede_ai_processing_record(
        fx.record_store,
        fx.audit_store,
        superseded_ai_processing_record_id=original.ai_processing_record_id,
        new_record=first_replacement,
        supersession_kind="processing",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    second_replacement = replace(
        original,
        ai_processing_record_id=uuid4(),
        supersedes_ai_processing_record_id=original.ai_processing_record_id,
    )
    with pytest.raises(AIProcessingRecordSupersededError):
        app.supersede_ai_processing_record(
            fx.record_store,
            fx.audit_store,
            superseded_ai_processing_record_id=original.ai_processing_record_id,
            new_record=second_replacement,
            supersession_kind="processing",
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


# --- assert_consequential_output_reviewed / disclosure protocol ----------------


def test_assert_consequential_output_reviewed_missing_reviewer(fx: Fixture) -> None:
    """Required scope item 18: missing reviewer fails closed."""
    record = _completed_consequential_record(fx)
    with pytest.raises(AIHumanReviewerMissingError):
        app.assert_consequential_output_reviewed(record)


def test_assert_consequential_output_reviewed_rejected(fx: Fixture) -> None:
    record = _completed_consequential_record(fx)
    reviewer = fx.grant_reviewer("ai_output_reviewer")
    reviewed = app.review_ai_output(
        fx.record_store,
        fx.audit_store,
        fx.role_store,
        ai_processing_record_id=record.ai_processing_record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=False,
        outcome=HumanReviewStatus.REJECTED,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    ).record
    with pytest.raises(AIOutputRejectedByHumanError):
        app.assert_consequential_output_reviewed(reviewed)


def test_full_disclosure_protocol_end_to_end(fx: Fixture) -> None:
    """Required scope item 18: disclosure receipt is required before
    official completion - proves the full 5-step protocol (19c.7)."""
    fx.activate_ai_processing_disclosure_policy()
    created = fx.request_record(is_consequential=True, disclosure_required=True)
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.9,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )

    # Step 5 check must fail-closed before any approval exists.
    with pytest.raises(AIPublicDisclosureRequiredError):
        app.assert_disclosure_complete_for_official_finalization(
            fx.record_store, ai_processing_record_id=record_id
        )

    reviewer = fx.grant_reviewer("ai_publication_reviewer")
    app.review_ai_output(
        fx.record_store,
        fx.audit_store,
        fx.role_store,
        ai_processing_record_id=record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=True,
        outcome=HumanReviewStatus.APPROVED,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )

    package_result = app.create_disclosure_package(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        approved_public_model_category="general-purpose-llm",
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert package_result.record.disclosure_package_reference is not None

    with pytest.raises(AIPublicDisclosureRequiredError):
        app.assert_disclosure_complete_for_official_finalization(
            fx.record_store, ai_processing_record_id=record_id
        )

    published = app.publish_ai_disclosure(
        fx.record_store,
        fx.audit_store,
        fx.ledger_store,
        fx.policy_store,
        fx.transparency_audit_store,
        ai_processing_record_id=record_id,
        package=package_result.package,
        published_by_role_id=uuid4(),
        subject_event_id=uuid4(),
        subject_type=LedgerSubjectType.AI_PROCESSING_RECORD,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    assert published.record.disclosure_receipt_reference is not None

    # Now the finalization gate passes.
    app.assert_disclosure_complete_for_official_finalization(
        fx.record_store, ai_processing_record_id=record_id
    )
    assert fx.ledger_store.get(published.disclosure_receipt_reference) is not None


def test_create_disclosure_package_requires_reviewed_output(fx: Fixture) -> None:
    """Required scope item 18: unreviewed consequential output cannot
    become official. A record that has never been through
    `review_ai_output` has no `human_reviewer_reference` yet, so this
    surfaces as the more specific `AIHumanReviewerMissingError` rather
    than the generic `AIConsequentialOutputNotReviewedError` (which is
    reserved for a state `assert_consequential_output_reviewed` cannot
    actually reach given the domain's transition invariants — see that
    function's docstring)."""
    created = fx.request_record(is_consequential=True, disclosure_required=True)
    record_id = created.record.ai_processing_record_id
    _advance_to_processing(fx, record_id)
    provider = ScriptedAIModelProvider(
        outcome=ProviderOutcome(
            output_reference="output-ref-1",
            output_hash="output-hash-1",
            confidence_score=0.9,
            uncertainty_indicator=None,
            explanation_reference=None,
            reason_codes=(),
        )
    )
    app.complete_processing_with_provider(
        fx.record_store,
        fx.audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=fx.clock,
    )
    with pytest.raises(AIHumanReviewerMissingError):
        app.create_disclosure_package(
            fx.record_store,
            fx.audit_store,
            ai_processing_record_id=record_id,
            approved_public_model_category="general-purpose-llm",
            actor=ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=fx.clock,
        )


# --- provider abstraction never mutates Civic OS --------------------------------


def test_provider_protocol_has_no_mutation_capability() -> None:
    """Required scope item 18: AIProcessingRecord (via the provider
    abstraction) cannot authorize another service's mutation - the
    Protocol itself carries no such parameter."""
    import inspect

    from epd2_ai_processing_service.provider import AIModelProvider

    signature = inspect.signature(AIModelProvider.submit)
    assert set(signature.parameters) == {"self", "submission"}
    assert PreparedInputSubmission.__dataclass_fields__.keys() == {
        "ai_processing_record_id",
        "model_provider",
        "model_name",
        "model_version",
        "deployment_version",
        "processing_region",
        "data_retention_mode",
        "external_provider_flag",
        "prepared_input_reference",
        "generation_settings",
        "timeout_seconds",
    }


def test_anomaly_indication_never_reconstructs_vote_linkage(fx: Fixture) -> None:
    """Required scope item 18: anomaly indication cannot reconstruct vote
    linkage - the closed target_type allow-list for anomaly_indication
    contains no vote/ballot-shaped target_type at all."""
    from epd2_ai_processing_service.domain import PERMITTED_PURPOSE_TARGET_COMBINATIONS, UseClass

    allowed = PERMITTED_PURPOSE_TARGET_COMBINATIONS[UseClass.ANOMALY_INDICATION]
    assert allowed == frozenset({"participation_pattern_report"})
    assert "vote_envelope" not in allowed
    assert "ballot" not in allowed
