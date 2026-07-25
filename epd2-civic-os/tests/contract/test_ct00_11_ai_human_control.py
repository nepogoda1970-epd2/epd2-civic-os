"""CT-00-11 AI Human Control (canon section 27): "ИИ-результат не
становится официальным без требуемого подтверждения" - an AI-produced
result never becomes official without the required human confirmation.

PACK-06 (ai-processing-service, ADR-021 through ADR-025) is the first
pack in this repository to implement `AIProcessingRecord` (canon section
17.1/19c); every earlier pack (PACK-02, PACK-03, PACK-05) genuinely had
no AI-produced result for this gate to apply to and marked CT-00-11 not
applicable (`tests/contract/test_ct00_12_emergency_stop_not_applicable.py`,
formerly `test_ct00_11_12_not_applicable.py`, carries the historical
PACK-02/03/05 CT-00-11 exclusion). Required scope item 17 for this pack
is explicit: CT-00-11 must be extended "fully and centrally" here, not
left not-applicable - this is that central, fully-applicable test file.

Four required scope item 4/11/18 invariants are each proven end-to-end
against the real `epd2_ai_processing_service.application` command
surface (never a synthetic/mocked shortcut):

- A consequential AI output cannot be treated as official/final before a
  human reviewer has been assigned at all
  (`test_ct00_11_consequential_output_without_any_review_is_not_official`).
- Silence, i.e. simply never calling `review_ai_output`, never implies
  approval - `human_review_status` stays `pending` forever on its own,
  it does not time out into `approved`
  (`test_ct00_11_silence_never_implies_approval`).
- An explicitly `rejected` output never becomes official, distinct from
  the "never reviewed at all" case
  (`test_ct00_11_rejected_output_never_becomes_official`).
- Even after a human `approved` outcome, an *official-publication* use
  additionally requires a published `AIDisclosurePackage` receipt before
  `assert_disclosure_complete_for_official_finalization` will pass -
  human approval alone is necessary but not sufficient for the
  official-publication path (ADR-025 §5, required scope item 13's
  5-step mandatory disclosure protocol)
  (`test_ct00_11_official_publication_also_requires_published_disclosure`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_ai_processing_service.application import (
    assert_consequential_output_reviewed,
    assert_disclosure_complete_for_official_finalization,
    begin_processing,
    complete_processing_with_provider,
    create_disclosure_package,
    prepare_input,
    publish_ai_disclosure,
    request_ai_processing,
    review_ai_output,
)
from epd2_ai_processing_service.domain import (
    AIProcessingRecord,
    HumanReviewStatus,
    RedactionManifest,
    RedactionResult,
)
from epd2_ai_processing_service.exceptions import (
    AIHumanReviewerMissingError,
    AIOutputRejectedByHumanError,
    AIPublicDisclosureRequiredError,
)
from epd2_ai_processing_service.provider import ProviderOutcome, ScriptedAIModelProvider
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


def _grant_reviewer(role_store: InMemoryRoleAssignmentStore, role_code: str) -> RoleAssignment:
    return role_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code=role_code,
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=NOW,
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )


def _completed_consequential_record(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    clock: FixedClock,
    actor: ActorRef,
    *,
    disclosure_required: bool = False,
) -> AIProcessingRecord:
    created = request_ai_processing(
        record_store,
        audit_store,
        ai_processing_record_id=uuid4(),
        purpose_code="summarization",
        target_type="initiative",
        target_id=uuid4(),
        input_version="v1",
        model_provider="internal",
        model_name="internal-model",
        model_version="1.0",
        prompt_template_version="v1",
        is_consequential=True,
        disclosure_required=disclosure_required,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    record_id = created.record.ai_processing_record_id
    prepare_input(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        redaction_validator=ScriptedRedactionValidator(_manifest()),
        input_reference="input-ref-1",
        declared_input_classification="public",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    begin_processing(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
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
    completed = complete_processing_with_provider(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        provider=provider,
        prepared_input_reference="input-ref-1",
        timeout_seconds=30.0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return completed.record


@pytest.fixture
def record_store() -> InMemoryAIProcessingRecordStore:
    return InMemoryAIProcessingRecordStore()


@pytest.fixture
def role_store() -> InMemoryRoleAssignmentStore:
    return InMemoryRoleAssignmentStore()


@pytest.fixture
def audit_store() -> InMemoryAuditEventStore:
    return InMemoryAuditEventStore()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


def test_ct00_11_consequential_output_without_any_review_is_not_official(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    clock: FixedClock,
    actor: ActorRef,
) -> None:
    """A `completed`, consequential `AIProcessingRecord` that has never
    been through `review_ai_output` at all cannot be treated as
    official/final - `assert_consequential_output_reviewed` fails
    closed."""
    record = _completed_consequential_record(record_store, audit_store, clock, actor)
    assert record.human_review_status is HumanReviewStatus.PENDING
    with pytest.raises(AIHumanReviewerMissingError):
        assert_consequential_output_reviewed(record)


def test_ct00_11_silence_never_implies_approval(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    clock: FixedClock,
    actor: ActorRef,
) -> None:
    """Required scope item 4: silence, timeout, missing reviewer, or
    missing role verification must never imply approval. There is no
    command in this pack's entire application surface that transitions
    `human_review_status` on a timer or on inaction - re-fetching the
    same record after "time passes" (simulated by simply re-reading it)
    still shows `pending`, never a silently-defaulted `approved`."""
    record = _completed_consequential_record(record_store, audit_store, clock, actor)
    record_id = record.ai_processing_record_id

    # "Time passes" - nothing in this pack ever calls a state-changing
    # command on its own; the record is simply re-read.
    still_pending = record_store.get(record_id)
    assert still_pending is not None
    assert still_pending.human_review_status is HumanReviewStatus.PENDING
    assert still_pending.human_reviewer_reference is None
    with pytest.raises(AIHumanReviewerMissingError):
        assert_consequential_output_reviewed(still_pending)


def test_ct00_11_rejected_output_never_becomes_official(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    role_store: InMemoryRoleAssignmentStore,
    clock: FixedClock,
    actor: ActorRef,
) -> None:
    """An explicitly `rejected` human-review outcome is a distinct
    fail-closed case from "never reviewed" - `assert_consequential_
    output_reviewed` raises the more specific `AIOutputRejectedByHumanError`."""
    record = _completed_consequential_record(record_store, audit_store, clock, actor)
    reviewer = _grant_reviewer(role_store, "ai_output_reviewer")
    reviewed = review_ai_output(
        record_store,
        audit_store,
        role_store,
        ai_processing_record_id=record.ai_processing_record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=False,
        outcome=HumanReviewStatus.REJECTED,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).record
    assert reviewed.human_review_status is HumanReviewStatus.REJECTED
    with pytest.raises(AIOutputRejectedByHumanError):
        assert_consequential_output_reviewed(reviewed)


def test_ct00_11_approved_output_becomes_official(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    role_store: InMemoryRoleAssignmentStore,
    clock: FixedClock,
    actor: ActorRef,
) -> None:
    """The positive case: once (and only once) a real, role-verified
    human reviewer records `approved`, `assert_consequential_output_
    reviewed` passes - proving the gate is not merely fail-closed but
    also actually openable through the required confirmation."""
    record = _completed_consequential_record(record_store, audit_store, clock, actor)
    reviewer = _grant_reviewer(role_store, "ai_output_reviewer")
    reviewed = review_ai_output(
        record_store,
        audit_store,
        role_store,
        ai_processing_record_id=record.ai_processing_record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=False,
        outcome=HumanReviewStatus.APPROVED,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).record
    assert_consequential_output_reviewed(reviewed)  # must not raise


def test_ct00_11_official_publication_also_requires_published_disclosure(
    record_store: InMemoryAIProcessingRecordStore,
    audit_store: InMemoryAuditEventStore,
    role_store: InMemoryRoleAssignmentStore,
    clock: FixedClock,
    actor: ActorRef,
) -> None:
    """A human `approved` outcome alone is necessary but not sufficient
    for the official-publication path (required scope item 13's 5-step
    mandatory disclosure protocol, ADR-025 §5):
    `assert_disclosure_complete_for_official_finalization` still fails
    closed until a `PublicLedgerEntry` disclosure receipt has actually
    been published, even after human approval."""
    policy_store = InMemoryDisclosurePolicyStore()
    transparency_audit_store = InMemoryAuditEventStore()
    ledger_store = InMemoryPublicLedgerEntryStore()

    policy_id = uuid4()
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
    define_disclosure_policy(
        policy_store,
        transparency_audit_store,
        disclosure_policy_id=policy_id,
        applies_to_subject_type=LedgerSubjectType.AI_PROCESSING_RECORD.value,
        field_rules=tuple(
            FieldRule(
                field_path=path,
                disclosure_class=DisclosureClass.PUBLIC,
                transformation=Transformation.NONE,
                replacement_label=None,
            )
            for path in field_paths
        ),
        effective_from=NOW,
        version=1,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    activate_disclosure_policy(
        policy_store,
        transparency_audit_store,
        disclosure_policy_id=policy_id,
        approved_by_role_id=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    record = _completed_consequential_record(
        record_store, audit_store, clock, actor, disclosure_required=True
    )
    record_id = record.ai_processing_record_id
    reviewer = _grant_reviewer(role_store, "ai_publication_reviewer")
    review_ai_output(
        record_store,
        audit_store,
        role_store,
        ai_processing_record_id=record_id,
        reviewer_role_assignment_id=reviewer.role_assignment_id,
        reviewer_subject_scope_id=GLOBAL_SCOPE_ID,
        requesting_actor_reference=uuid4(),
        is_official_publication=True,
        outcome=HumanReviewStatus.APPROVED,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    # Human approval alone is not enough - no disclosure package yet.
    with pytest.raises(AIPublicDisclosureRequiredError):
        assert_disclosure_complete_for_official_finalization(
            record_store, ai_processing_record_id=record_id
        )

    package_result = create_disclosure_package(
        record_store,
        audit_store,
        ai_processing_record_id=record_id,
        approved_public_model_category="general-purpose-llm",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    # A package alone (not yet published) is still not enough.
    with pytest.raises(AIPublicDisclosureRequiredError):
        assert_disclosure_complete_for_official_finalization(
            record_store, ai_processing_record_id=record_id
        )

    publish_ai_disclosure(
        record_store,
        audit_store,
        ledger_store,
        policy_store,
        transparency_audit_store,
        ai_processing_record_id=record_id,
        package=package_result.package,
        published_by_role_id=uuid4(),
        subject_event_id=uuid4(),
        subject_type=LedgerSubjectType.AI_PROCESSING_RECORD,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    # Now, and only now, the official-publication gate passes.
    assert_disclosure_complete_for_official_finalization(
        record_store, ai_processing_record_id=record_id
    )
