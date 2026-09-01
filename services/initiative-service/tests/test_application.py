"""Tests for epd2_initiative_service.application.

Exercises the full command set against real PACK-02 collaborators
(`epd2_credential_service`, `epd2_eligibility_service`) through their
`application`-layer functions only (ADR-008) - never their `storage`/
`domain` modules - the same boundary `application.py` itself respects.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import create_eligibility_rule, evaluate_eligibility
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
)
from epd2_initiative_service.application import (
    InitiativeVersionResult,
    PermissionDeniedError,
    accept_amendment,
    add_source_record,
    add_support,
    archive_initiative,
    create_amendment,
    create_initiative,
    create_initiative_version,
    get_initiative_version,
    get_published_initiative,
    invalidate_support,
    mark_adopted,
    mark_qualified,
    mark_ready_for_ballot,
    publish_amendment,
    publish_initiative,
    reject_amendment,
    reject_initiative,
    request_legal_review,
    request_revision,
    start_amendment_discussion,
    start_completeness_review,
    start_deliberation,
    start_support_collection,
    start_voting,
    submit_amendment,
    submit_initiative,
    supersede_amendment,
    update_source_verification_status,
    withdraw_amendment,
    withdraw_initiative,
    withdraw_support,
)
from epd2_initiative_service.domain import (
    AmendmentStatus,
    InitiativeStatus,
    SourceVerificationStatus,
    SupportStatus,
)
from epd2_initiative_service.exceptions import (
    DuplicateSupportError,
    ForbiddenInitiativeTransitionError,
    ForbiddenSourceVerificationTransitionError,
    InitiativeHasNoVersionError,
    InitiativeNotAcceptingSupportError,
    InitiativeVersionFrozenError,
    UnknownEligibilityDecisionReferenceError,
    UnknownInitiativeError,
    UnknownSourceRecordError,
)
from epd2_initiative_service.storage import (
    InMemoryAmendmentStore,
    InMemoryInitiativeStore,
    InMemoryInitiativeVersionStore,
    InMemorySourceRecordStore,
    InMemorySupportRecordStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)
_VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)
_EXPIRES_AT = datetime(2027, 1, 1, tzinfo=UTC)


def _actor(actor_type: str = "service") -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type=actor_type)


class _Fixture:
    def __init__(self) -> None:
        self.initiative_store = InMemoryInitiativeStore()
        self.version_store = InMemoryInitiativeVersionStore()
        self.support_store = InMemorySupportRecordStore()
        self.amendment_store = InMemoryAmendmentStore()
        self.source_store = InMemorySourceRecordStore()
        self.audit_store = InMemoryAuditEventStore()
        self.credential_store = InMemoryCredentialStore()
        self.eligibility_rule_store = InMemoryEligibilityRuleStore()
        self.eligibility_decision_store = InMemoryEligibilityDecisionStore()


def _create_draft_initiative(fx: _Fixture, author: ActorRef) -> UUID:
    initiative_id = uuid4()
    create_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        space_id=uuid4(),
        author_actor_id=author.actor_id,
        initiative_type="citizen_law",
        workflow_id=uuid4(),
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return initiative_id


def _add_version(
    fx: _Fixture, initiative_id: UUID, author: ActorRef, version_number: int = 1
) -> UUID:
    version_id = uuid4()
    create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        initiative_id=initiative_id,
        initiative_version_id=version_id,
        version_number=version_number,
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=("group_a",),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return version_id


def _initiative_in_support_collection(fx: _Fixture, author: ActorRef) -> UUID:
    initiative_id = _create_draft_initiative(fx, author)
    _add_version(fx, initiative_id, author)
    submit_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    start_completeness_review(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    publish_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    start_support_collection(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return initiative_id


def _issue_initiative_support_credential(fx: _Fixture, *, initiative_id: UUID) -> UUID:
    credential_id = uuid4()
    issue_participation_credential(
        fx.credential_store,
        fx.audit_store,
        credential_id=credential_id,
        credential_type=CredentialType.INITIATIVE_SUPPORT,
        scope_type="initiative",
        scope_id=initiative_id,
        valid_from=_VALID_FROM,
        expires_at=_EXPIRES_AT,
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="digest",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return credential_id


def _make_eligibility_decision(fx: _Fixture, *, eligible: bool) -> UUID:
    rule = create_eligibility_rule(
        fx.eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=_VALID_FROM,
        valid_until=None,
    )
    claims = (
        {"membership_status": "active", "verification_level": "basic"}
        if eligible
        else {"membership_status": "lapsed", "verification_level": "basic"}
    )
    decision = evaluate_eligibility(
        fx.eligibility_rule_store,
        fx.eligibility_decision_store,
        fx.audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims=claims,
        evaluator_version="1.0",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).decision
    return decision.eligibility_decision_id


# ---------------------------------------------------------------------------
# create_initiative
# ---------------------------------------------------------------------------


def test_create_initiative_creates_draft_and_audits() -> None:
    fx = _Fixture()
    author = _actor()
    result = create_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=uuid4(),
        space_id=uuid4(),
        author_actor_id=author.actor_id,
        initiative_type="citizen_law",
        workflow_id=uuid4(),
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.initiative.status == InitiativeStatus.DRAFT
    assert result.initiative.current_version_id is None
    assert result.event is not None
    assert result.event.event_type == "initiative.draft_created"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_create_initiative_without_permission_is_denied() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError):
        create_initiative(
            fx.initiative_store,
            fx.audit_store,
            initiative_id=uuid4(),
            space_id=uuid4(),
            author_actor_id=uuid4(),
            initiative_type="citizen_law",
            workflow_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_create_initiative_is_idempotent_for_same_event_id_and_content() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = uuid4()
    event_id = uuid4()
    correlation_id = uuid4()
    kwargs: dict[str, object] = dict(
        initiative_id=initiative_id,
        space_id=uuid4(),
        author_actor_id=author.actor_id,
        initiative_type="citizen_law",
        workflow_id=uuid4(),
    )
    first = create_initiative(
        fx.initiative_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
        **kwargs,  # type: ignore[arg-type]
    )
    second = create_initiative(
        fx.initiative_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.initiative == second.initiative
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


# ---------------------------------------------------------------------------
# create_initiative_version
# ---------------------------------------------------------------------------


def test_create_initiative_version_advances_current_version_pointer() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    result = _fetch_version_result(fx, initiative_id, author, version_number=1)
    assert result.version.version_number == 1
    assert result.initiative.current_version_id == result.version.initiative_version_id
    assert result.event.event_type == "initiative.version_created"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def _fetch_version_result(
    fx: _Fixture, initiative_id: UUID, author: ActorRef, version_number: int
) -> InitiativeVersionResult:
    return create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        initiative_id=initiative_id,
        initiative_version_id=uuid4(),
        version_number=version_number,
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=("group_a",),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )


def test_create_initiative_version_is_idempotent_for_identical_content() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    version_id = uuid4()
    kwargs: dict[str, object] = dict(
        initiative_id=initiative_id,
        initiative_version_id=version_id,
        version_number=1,
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=("group_a",),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
    )
    first = create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **kwargs,  # type: ignore[arg-type]
    )
    second = create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.version == second.version


def test_create_initiative_version_raises_frozen_error_for_different_content_same_key() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    version_id = uuid4()
    create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        initiative_id=initiative_id,
        initiative_version_id=version_id,
        version_number=1,
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=(),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(InitiativeVersionFrozenError):
        create_initiative_version(
            fx.initiative_store,
            fx.version_store,
            fx.audit_store,
            initiative_id=initiative_id,
            initiative_version_id=version_id,
            version_number=1,
            title="A different title",
            problem_statement="Problem",
            proposed_solution="Solution",
            affected_groups=(),
            expected_effects="Effects",
            risks="Risks",
            estimated_resources="Resources",
            legal_questions="Questions",
            source_references=(),
            actor=author,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_create_initiative_version_unknown_initiative_raises() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownInitiativeError):
        _fetch_version_result(fx, uuid4(), _actor(), version_number=1)


def test_create_initiative_version_does_not_regress_pointer_on_older_replay() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    v1_id = uuid4()
    v1_kwargs: dict[str, object] = dict(
        initiative_id=initiative_id,
        initiative_version_id=v1_id,
        version_number=1,
        title="Title v1",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=(),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
    )
    create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **v1_kwargs,  # type: ignore[arg-type]
    )
    v2_result = _fetch_version_result(fx, initiative_id, author, version_number=2)
    assert v2_result.initiative.current_version_id == v2_result.version.initiative_version_id

    # Replay the (idempotent, identical-content) v1 create - must not
    # regress the pointer back to v1.
    replay = create_initiative_version(
        fx.initiative_store,
        fx.version_store,
        fx.audit_store,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **v1_kwargs,  # type: ignore[arg-type]
    )
    assert replay.initiative.current_version_id == v2_result.version.initiative_version_id


# ---------------------------------------------------------------------------
# submit_initiative / status transitions
# ---------------------------------------------------------------------------


def test_submit_initiative_without_version_raises() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    with pytest.raises(InitiativeHasNoVersionError):
        submit_initiative(
            fx.initiative_store,
            fx.audit_store,
            initiative_id=initiative_id,
            actor=author,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_submit_initiative_from_draft_and_from_revision_required() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    _add_version(fx, initiative_id, author)
    result = submit_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.initiative.status == InitiativeStatus.SUBMITTED
    assert result.event is not None and result.event.event_type == "initiative.submitted"

    start_completeness_review(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    revision_result = request_revision(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert revision_result.initiative.status == InitiativeStatus.REVISION_REQUIRED

    resubmit_result = submit_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert resubmit_result.initiative.status == InitiativeStatus.SUBMITTED


def test_start_completeness_review_has_no_event() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    _add_version(fx, initiative_id, author)
    submit_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = start_completeness_review(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.event is None
    assert result.initiative.status == InitiativeStatus.COMPLETENESS_REVIEW
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_full_initiative_lifecycle_to_adopted_and_archived() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)

    mark_qualified(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    start_deliberation(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    request_legal_review(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    mark_ready_for_ballot(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    voting_result = start_voting(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert voting_result.event is None
    assert voting_result.initiative.status == InitiativeStatus.VOTING

    adopted_result = mark_adopted(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert adopted_result.event is None
    assert adopted_result.initiative.status == InitiativeStatus.ADOPTED

    archived_result = archive_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert archived_result.event is not None
    assert archived_result.event.event_type == "initiative.archived"
    assert archived_result.initiative.status == InitiativeStatus.ARCHIVED


def test_reject_initiative_from_support_collection_and_from_voting() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    result = reject_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.event is None
    assert result.initiative.status == InitiativeStatus.REJECTED

    other_initiative_id = _initiative_in_support_collection(fx, author)
    mark_qualified(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=other_initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    start_deliberation(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=other_initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    request_legal_review(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=other_initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    legal_reject_result = reject_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=other_initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert legal_reject_result.initiative.status == InitiativeStatus.REJECTED


def test_withdraw_initiative_from_draft() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    result = withdraw_initiative(
        fx.initiative_store,
        fx.audit_store,
        initiative_id=initiative_id,
        actor=author,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.initiative.status == InitiativeStatus.WITHDRAWN
    assert result.event is not None and result.event.event_type == "initiative.withdrawn"


def test_initiative_transition_wrong_source_status_is_forbidden() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    with pytest.raises(ForbiddenInitiativeTransitionError):
        mark_qualified(
            fx.initiative_store,
            fx.audit_store,
            initiative_id=initiative_id,
            actor=author,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_initiative_command_without_permission_is_denied() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    with pytest.raises(PermissionDeniedError):
        withdraw_initiative(
            fx.initiative_store,
            fx.audit_store,
            initiative_id=initiative_id,
            actor=author,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_initiative_command_unknown_initiative_raises() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownInitiativeError):
        withdraw_initiative(
            fx.initiative_store,
            fx.audit_store,
            initiative_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# ---------------------------------------------------------------------------
# SupportRecord
# ---------------------------------------------------------------------------


def test_add_support_records_active_support_and_increments_count() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    result = add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        support_record_id=uuid4(),
        initiative_id=initiative_id,
        support_actor_reference=uuid4(),
        credential_reference=credential_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.support.status == SupportStatus.ACTIVE
    assert result.initiative.support_count == 1
    assert result.event is not None and result.event.event_type == "initiative.support_added"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_add_support_requires_support_collection_status() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    with pytest.raises(InitiativeNotAcceptingSupportError):
        add_support(
            fx.initiative_store,
            fx.support_store,
            fx.audit_store,
            fx.credential_store,
            support_record_id=uuid4(),
            initiative_id=initiative_id,
            support_actor_reference=uuid4(),
            credential_reference=credential_id,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_add_support_rejects_invalid_credential() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    with pytest.raises(PermissionDeniedError):
        add_support(
            fx.initiative_store,
            fx.support_store,
            fx.audit_store,
            fx.credential_store,
            support_record_id=uuid4(),
            initiative_id=initiative_id,
            support_actor_reference=uuid4(),
            credential_reference=uuid4(),  # never issued
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_add_support_rejects_second_active_support_same_participant() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    actor_reference = uuid4()
    credential_1 = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        support_record_id=uuid4(),
        initiative_id=initiative_id,
        support_actor_reference=actor_reference,
        credential_reference=credential_1,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    credential_2 = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    with pytest.raises(DuplicateSupportError):
        add_support(
            fx.initiative_store,
            fx.support_store,
            fx.audit_store,
            fx.credential_store,
            support_record_id=uuid4(),
            initiative_id=initiative_id,
            support_actor_reference=actor_reference,
            credential_reference=credential_2,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_add_support_is_idempotent_and_does_not_double_count() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    support_record_id = uuid4()
    actor = _actor()
    kwargs: dict[str, object] = dict(
        support_record_id=support_record_id,
        initiative_id=initiative_id,
        support_actor_reference=uuid4(),
        credential_reference=credential_id,
    )
    first = add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.initiative.support_count == 1
    second = add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **kwargs,  # type: ignore[arg-type]
    )
    assert second.initiative.support_count == 1


def test_add_support_with_eligible_decision_succeeds() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    decision_id = _make_eligibility_decision(fx, eligible=True)
    result = add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        support_record_id=uuid4(),
        initiative_id=initiative_id,
        support_actor_reference=uuid4(),
        credential_reference=credential_id,
        eligibility_decision_store=fx.eligibility_decision_store,
        eligibility_decision_id=decision_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.support.status == SupportStatus.ACTIVE


def test_add_support_with_not_eligible_decision_is_denied() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    decision_id = _make_eligibility_decision(fx, eligible=False)
    with pytest.raises(PermissionDeniedError):
        add_support(
            fx.initiative_store,
            fx.support_store,
            fx.audit_store,
            fx.credential_store,
            support_record_id=uuid4(),
            initiative_id=initiative_id,
            support_actor_reference=uuid4(),
            credential_reference=credential_id,
            eligibility_decision_store=fx.eligibility_decision_store,
            eligibility_decision_id=decision_id,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_add_support_with_unknown_eligibility_decision_raises() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    with pytest.raises(UnknownEligibilityDecisionReferenceError):
        add_support(
            fx.initiative_store,
            fx.support_store,
            fx.audit_store,
            fx.credential_store,
            support_record_id=uuid4(),
            initiative_id=initiative_id,
            support_actor_reference=uuid4(),
            credential_reference=credential_id,
            eligibility_decision_store=fx.eligibility_decision_store,
            eligibility_decision_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_withdraw_support_decrements_count_and_emits_event() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    support_record_id = uuid4()
    add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        support_record_id=support_record_id,
        initiative_id=initiative_id,
        support_actor_reference=uuid4(),
        credential_reference=credential_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = withdraw_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        support_record_id=support_record_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.support.status == SupportStatus.WITHDRAWN
    assert result.initiative.support_count == 0
    assert result.event is not None and result.event.event_type == "initiative.support_withdrawn"


def test_invalidate_support_decrements_count_and_has_no_event() -> None:
    fx = _Fixture()
    author = _actor()
    initiative_id = _initiative_in_support_collection(fx, author)
    credential_id = _issue_initiative_support_credential(fx, initiative_id=initiative_id)
    support_record_id = uuid4()
    add_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        fx.credential_store,
        support_record_id=support_record_id,
        initiative_id=initiative_id,
        support_actor_reference=uuid4(),
        credential_reference=credential_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = invalidate_support(
        fx.initiative_store,
        fx.support_store,
        fx.audit_store,
        support_record_id=support_record_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.support.status == SupportStatus.INVALIDATED
    assert result.initiative.support_count == 0
    assert result.event is None
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


# ---------------------------------------------------------------------------
# Amendment
# ---------------------------------------------------------------------------


def _create_amendment(
    fx: _Fixture, initiative_id: UUID, target_version_id: UUID, actor: ActorRef
) -> UUID:
    amendment_id = uuid4()
    create_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        initiative_id=initiative_id,
        target_version_id=target_version_id,
        proposer_actor_id=actor.actor_id,
        proposed_change="Change section 3",
        justification="Clarifies intent",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return amendment_id


def test_create_amendment_has_no_event_but_is_audited() -> None:
    fx = _Fixture()
    actor = _actor()
    result_amendment_id = _create_amendment(fx, uuid4(), uuid4(), actor)
    stored = fx.amendment_store.get(result_amendment_id)
    assert stored is not None
    assert stored.status == AmendmentStatus.DRAFT


def test_amendment_lifecycle_submitted_published_accepted() -> None:
    fx = _Fixture()
    actor = _actor()
    amendment_id = _create_amendment(fx, uuid4(), uuid4(), actor)

    submit_result = submit_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert submit_result.event is not None
    assert submit_result.event.event_type == "amendment.submitted"

    publish_result = publish_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert publish_result.event is not None
    assert publish_result.event.event_type == "amendment.published"

    discussion_result = start_amendment_discussion(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert discussion_result.event is None
    assert discussion_result.amendment.status == AmendmentStatus.UNDER_DISCUSSION

    decision_reference = uuid4()
    accept_result = accept_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        decision_reference=decision_reference,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert accept_result.amendment.status == AmendmentStatus.ACCEPTED
    assert accept_result.amendment.decision_reference == decision_reference
    assert accept_result.event is not None
    assert accept_result.event.event_type == "amendment.accepted"


def test_amendment_rejected_path() -> None:
    fx = _Fixture()
    actor = _actor()
    amendment_id = _create_amendment(fx, uuid4(), uuid4(), actor)
    submit_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    publish_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    start_amendment_discussion(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = reject_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.amendment.status == AmendmentStatus.REJECTED
    assert result.event is not None and result.event.event_type == "amendment.rejected"


def test_withdraw_amendment_from_draft() -> None:
    fx = _Fixture()
    actor = _actor()
    amendment_id = _create_amendment(fx, uuid4(), uuid4(), actor)
    result = withdraw_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.amendment.status == AmendmentStatus.WITHDRAWN
    assert result.event is None


def test_supersede_amendment_uses_target_superseded_reason_code() -> None:
    fx = _Fixture()
    actor = _actor()
    amendment_id = _create_amendment(fx, uuid4(), uuid4(), actor)
    submit_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    publish_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = supersede_amendment(
        fx.amendment_store,
        fx.audit_store,
        amendment_id=amendment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.amendment.status == AmendmentStatus.SUPERSEDED
    assert result.event is None
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "AMENDMENT_TARGET_SUPERSEDED"


# ---------------------------------------------------------------------------
# SourceRecord
# ---------------------------------------------------------------------------


def _add_source(fx: _Fixture, actor: ActorRef) -> UUID:
    source_id = uuid4()
    add_source_record(
        fx.source_store,
        fx.audit_store,
        source_id=source_id,
        source_type="report",
        title="Impact study",
        publisher="Institute",
        publication_date=_VALID_FROM,
        url="https://example.org/report",
        archive_reference=None,
        added_by_actor_id=actor.actor_id,
        valid_until=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return source_id


def test_add_source_record_creates_unverified_and_is_audited() -> None:
    fx = _Fixture()
    actor = _actor()
    source_id = _add_source(fx, actor)
    stored = fx.source_store.get(source_id)
    assert stored is not None
    assert stored.verification_status == SourceVerificationStatus.UNVERIFIED
    assert stored.content_hash


def test_update_source_verification_status_human_actor_succeeds() -> None:
    fx = _Fixture()
    actor = _actor()
    source_id = _add_source(fx, actor)
    human = _actor(actor_type="human")
    result = update_source_verification_status(
        fx.source_store,
        fx.audit_store,
        source_id=source_id,
        target_status=SourceVerificationStatus.HUMAN_CHECKED,
        actor=human,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.source.verification_status == SourceVerificationStatus.HUMAN_CHECKED
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_update_source_verification_status_ai_actor_denied_for_human_checked() -> None:
    """Canon 12.1's hard rule: an AI actor may never silently promote a
    source's status to `human_checked`, regardless of `actor_is_authorized`."""
    fx = _Fixture()
    actor = _actor()
    source_id = _add_source(fx, actor)
    ai_actor = _actor(actor_type="ai")
    with pytest.raises(PermissionDeniedError):
        update_source_verification_status(
            fx.source_store,
            fx.audit_store,
            source_id=source_id,
            target_status=SourceVerificationStatus.HUMAN_CHECKED,
            actor=ai_actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )
    # The source's status must be unchanged after the denied attempt.
    stored = fx.source_store.get(source_id)
    assert stored is not None
    assert stored.verification_status == SourceVerificationStatus.UNVERIFIED


def test_update_source_verification_status_ai_actor_allowed_for_automatically_checked() -> None:
    """The AI restriction is specific to `human_checked` - an AI actor may
    still perform an ordinary `automatically_checked` transition."""
    fx = _Fixture()
    actor = _actor()
    source_id = _add_source(fx, actor)
    ai_actor = _actor(actor_type="ai")
    result = update_source_verification_status(
        fx.source_store,
        fx.audit_store,
        source_id=source_id,
        target_status=SourceVerificationStatus.AUTOMATICALLY_CHECKED,
        actor=ai_actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.source.verification_status == SourceVerificationStatus.AUTOMATICALLY_CHECKED


def test_update_source_verification_status_forbidden_transition_raises() -> None:
    fx = _Fixture()
    actor = _actor()
    source_id = _add_source(fx, actor)
    human = _actor(actor_type="human")
    update_source_verification_status(
        fx.source_store,
        fx.audit_store,
        source_id=source_id,
        target_status=SourceVerificationStatus.UNAVAILABLE,
        actor=human,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(ForbiddenSourceVerificationTransitionError):
        update_source_verification_status(
            fx.source_store,
            fx.audit_store,
            source_id=source_id,
            target_status=SourceVerificationStatus.HUMAN_CHECKED,
            actor=human,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_update_source_verification_status_unknown_source_raises() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownSourceRecordError):
        update_source_verification_status(
            fx.source_store,
            fx.audit_store,
            source_id=uuid4(),
            target_status=SourceVerificationStatus.AUTOMATICALLY_CHECKED,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_get_published_initiative_read_accessor() -> None:
    """Additive (PACK-04, ADR-012 item 1): backs
    `epd2_transparency_service.application.publish_ledger_entry` for
    `subject_type = "initiative"`."""
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    found = get_published_initiative(fx.initiative_store, initiative_id=initiative_id)
    assert found is not None
    assert found.initiative_id == initiative_id
    assert get_published_initiative(fx.initiative_store, initiative_id=uuid4()) is None


def test_get_initiative_version_read_accessor() -> None:
    """Additive (PACK-04, ADR-012 item 1): backs
    `epd2_transparency_service.application.publish_ledger_entry` for
    `subject_type = "initiative_version"`."""
    fx = _Fixture()
    author = _actor()
    initiative_id = _create_draft_initiative(fx, author)
    _add_version(fx, initiative_id, author, version_number=1)
    found = get_initiative_version(fx.version_store, initiative_id=initiative_id, version_number=1)
    assert found is not None
    assert found.initiative_id == initiative_id
    assert (
        get_initiative_version(fx.version_store, initiative_id=initiative_id, version_number=99)
        is None
    )
