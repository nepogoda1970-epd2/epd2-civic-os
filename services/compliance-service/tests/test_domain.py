"""Pure-domain tests for PACK-09's entities (ADR-038 through ADR-042).

Everything here exercises `epd2_compliance_service.domain` directly, with
no stores and no clock - the structural invariants that must hold on
every construction path, independent of which command produced the value.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from epd2_compliance_service.domain import (
    AppealReference,
    CaseDecision,
    CaseRoleAssignment,
    CaseStatus,
    CaseType,
    ConflictOfInterestDeclaration,
    ConflictState,
    CrossScopeAuthorityGrant,
    DataAsset,
    DataSubjectRequest,
    DataSubjectRequestStatus,
    DataSubjectRequestType,
    DeadlineDefinition,
    DeadlineEventType,
    DeadlineStatus,
    DecisionOutcome,
    DestructionAuthorization,
    DestructionEvidence,
    DispositionAction,
    DisputeParties,
    GovernedRecord,
    GovernedRecordState,
    IdentityVerificationStatus,
    LegalBasis,
    LegalHold,
    LegalHoldScope,
    LegalHoldStatus,
    ProceduralCase,
    ProceduralDeadline,
    ProceduralRole,
    ProceduralStep,
    ProcessingActivity,
    RecordSensitivity,
    RegistryEntryStatus,
    ResponseDecision,
    RetentionPolicy,
    RetentionStartEvent,
    RetentionTrigger,
    ScopeCapability,
    assert_decision_maker_eligible,
    build_started_deadline,
    evaluate_hold_applicability,
    mint_case_party_reference,
    reject_identity_payload_keys,
    require_timezone,
)
from epd2_compliance_service.exceptions import (
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    DataSubjectRequestTransitionInvalidError,
    DeadlineTimezoneUndeterminedError,
    DeadlineTransitionInvalidError,
    LegalHoldScopeMismatchError,
    LegalHoldTransitionInvalidError,
    ProceduralCaseTransitionInvalidError,
    ProceduralIndependenceViolationError,
    ProceduralRoleConflictError,
    ProcessingActivityTransitionInvalidError,
    ProcessingRegistryIdentityPayloadRejectedError,
    ProcessingRegistryIncompleteError,
)

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
BERLIN = "Europe/Berlin"
REASON = "COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _policy(
    *,
    organization_id: UUID | None = None,
    retention_days: int = 30,
    disposition_action: DispositionAction = DispositionAction.DELETE,
    policy_version: int = 1,
    supersedes: int | None = None,
) -> RetentionPolicy:
    return RetentionPolicy(
        policy_id=uuid4(),
        organization_id=organization_id if organization_id is not None else uuid4(),
        record_class="case.disciplinary",
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        retention_days=retention_days,
        disposition_action=disposition_action,
        policy_version=policy_version,
        valid_from=T0,
        supersedes_policy_version=supersedes,
    )


def _record(
    policy: RetentionPolicy, *, retention_start_at: datetime | None = None
) -> GovernedRecord:
    return GovernedRecord(
        record_id=uuid4(),
        organization_id=policy.organization_id,
        record_class=policy.record_class,
        sensitivity=RecordSensitivity.CONFIDENTIAL,
        created_at=T0,
        retention_policy_id=policy.policy_id,
        retention_policy_version=policy.policy_version,
        source_reference="membership-service:case:1",
        retention_start_at=retention_start_at,
    )


def _hold(
    record: GovernedRecord,
    *,
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE,
    by_class: bool = False,
) -> LegalHold:
    scope = (
        LegalHoldScope(record_classes=frozenset({record.record_class}))
        if by_class
        else LegalHoldScope(record_ids=frozenset({record.record_id}))
    )
    return LegalHold(
        hold_id=uuid4(),
        organization_id=record.organization_id,
        matter_reference="matter/2026-1",
        scope=scope,
        issued_at=T0,
        issued_by_authority_reference=uuid4(),
        status=status,
    )


def _case(
    *,
    organization_id: UUID | None = None,
    case_type: CaseType = CaseType.PARTY_ARBITRATION,
    status: CaseStatus = CaseStatus.OPEN,
    procedural_authority_reference: UUID | None = None,
    case_handler_reference: UUID | None = None,
) -> ProceduralCase:
    return ProceduralCase(
        case_id=uuid4(),
        organization_id=organization_id if organization_id is not None else uuid4(),
        case_type=case_type,
        status=status,
        opened_at=T0,
        subject_reference="dispute:2026-1",
        procedural_authority_reference=(
            procedural_authority_reference
            if procedural_authority_reference is not None
            else uuid4()
        ),
        workflow_type="party_arbitration_standard",
        case_handler_reference=case_handler_reference,
    )


def _definition(
    *, organization_id: UUID, duration_days: int = 10, timezone: str = BERLIN
) -> DeadlineDefinition:
    return DeadlineDefinition(
        definition_id=uuid4(),
        organization_id=organization_id,
        deadline_code="RESPONSE_DUE",
        duration_days=duration_days,
        timezone=timezone,
    )


def _deadline(*, duration_days: int = 10, started_at: datetime = T0) -> ProceduralDeadline:
    organization_id = uuid4()
    return build_started_deadline(
        deadline_id=uuid4(),
        definition=_definition(organization_id=organization_id, duration_days=duration_days),
        case_id=uuid4(),
        organization_id=organization_id,
        started_at=started_at,
        reason_code=REASON,
        actor_party_reference=uuid4(),
    )


def _processing_activity(
    *,
    organization_id: UUID | None = None,
    status: RegistryEntryStatus = RegistryEntryStatus.DRAFT,
    additional_metadata: dict[str, str] | None = None,
    data_subject_categories: tuple[str, ...] = ("members",),
) -> ProcessingActivity:
    return ProcessingActivity(
        activity_id=uuid4(),
        organization_id=organization_id if organization_id is not None else uuid4(),
        name="Mitgliederverwaltung",
        purpose="membership administration",
        legal_basis=LegalBasis.PARTY_STATUTE,
        data_subject_categories=data_subject_categories,
        personal_data_categories=("contact_data",),
        recipient_categories=("internal_administration",),
        retention_policy_reference=uuid4(),
        technical_organizational_measures=("rbac",),
        controller_reference=uuid4(),
        process_owner_authority_reference=uuid4(),
        system_references=("membership-service",),
        status=status,
        valid_from=T0,
        additional_metadata=dict(additional_metadata or {}),
    )


def _role(case: ProceduralCase, role: ProceduralRole, party: UUID) -> CaseRoleAssignment:
    return CaseRoleAssignment(
        assignment_id=uuid4(),
        case_id=case.case_id,
        organization_id=case.organization_id,
        role=role,
        party_reference=party,
        assigned_at=T0,
        assigned_by_party_reference=uuid4(),
    )


def _declaration(
    case: ProceduralCase, party: UUID, state: ConflictState
) -> ConflictOfInterestDeclaration:
    decided = state in {ConflictState.CONFIRMED, ConflictState.WAIVED}
    return ConflictOfInterestDeclaration(
        declaration_id=uuid4(),
        case_id=case.case_id,
        organization_id=case.organization_id,
        party_reference=party,
        state=state,
        basis_code="same_local_branch",
        declared_at=T0,
        decided_by_party_reference=uuid4() if decided else None,
        decided_at=T0 if decided else None,
    )


def _request(
    *,
    status: DataSubjectRequestStatus = DataSubjectRequestStatus.RECEIVED,
    verification: IdentityVerificationStatus = IdentityVerificationStatus.NOT_VERIFIED,
) -> DataSubjectRequest:
    return DataSubjectRequest(
        request_id=uuid4(),
        case_id=uuid4(),
        organization_id=uuid4(),
        request_type=DataSubjectRequestType.ACCESS,
        status=status,
        requester_party_reference=mint_case_party_reference(),
        received_at=T0,
        scope_description_code="all_membership_data",
        identity_verification_status=verification,
    )


# ---------------------------------------------------------------------------
# Timezone-awareness is structural, everywhere
# ---------------------------------------------------------------------------


def test_every_entity_rejects_a_naive_datetime() -> None:
    """No entity accepts a naive datetime on any of its own datetime
    fields - a single missed field would let an ambiguous local time into
    a retention or deadline calculation."""
    naive = datetime(2026, 1, 1, 9, 0)
    org = uuid4()

    with pytest.raises(ValueError, match="timezone-aware"):
        RetentionPolicy(
            policy_id=uuid4(),
            organization_id=org,
            record_class="case.x",
            trigger=RetentionTrigger.CREATED_AT,
            retention_days=1,
            disposition_action=DispositionAction.DELETE,
            policy_version=1,
            valid_from=naive,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        GovernedRecord(
            record_id=uuid4(),
            organization_id=org,
            record_class="case.x",
            sensitivity=RecordSensitivity.INTERNAL,
            created_at=naive,
            retention_policy_id=uuid4(),
            retention_policy_version=1,
            source_reference="x:1",
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        LegalHold(
            hold_id=uuid4(),
            organization_id=org,
            matter_reference="m",
            scope=LegalHoldScope(record_classes=frozenset({"case.x"})),
            issued_at=naive,
            issued_by_authority_reference=uuid4(),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _case().transition(CaseStatus.ADMISSIBILITY_REVIEW, naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        ProceduralStep(step_code="hearing", required=True, completed_at=naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        CaseRoleAssignment(
            assignment_id=uuid4(),
            case_id=uuid4(),
            organization_id=org,
            role=ProceduralRole.CASE_HANDLER,
            party_reference=uuid4(),
            assigned_at=naive,
            assigned_by_party_reference=uuid4(),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _deadline().suspend(naive, reason_code=REASON, actor_party_reference=uuid4())


def test_deadline_definition_requires_a_known_iana_timezone() -> None:
    org = uuid4()
    with pytest.raises(DeadlineTimezoneUndeterminedError):
        _definition(organization_id=org, timezone="")
    with pytest.raises(DeadlineTimezoneUndeterminedError):
        _definition(organization_id=org, timezone="Mars/Olympus_Mons")
    assert require_timezone(BERLIN) == ZoneInfo(BERLIN)


def test_deadline_due_date_is_computed_on_the_local_civil_clock() -> None:
    """A ten-day period that crosses the March DST change lands on the
    same wall-clock time, not an hour earlier or later."""
    definition = _definition(organization_id=uuid4(), duration_days=10)
    started = datetime(2026, 3, 25, 14, 0, tzinfo=ZoneInfo(BERLIN))
    local = definition.due_at(started).astimezone(ZoneInfo(BERLIN))
    assert (local.year, local.month, local.day) == (2026, 4, 4)
    assert (local.hour, local.minute) == (14, 0)


def test_a_deadline_started_just_before_midnight_local_time_is_due_on_the_expected_date() -> None:
    """Timezone-boundary case: 23:30 Berlin on 1 January is 22:30 UTC on
    1 January, so a one-day deadline is due on 2 January *local* - not on
    3 January, which a naive UTC-date computation would produce."""
    definition = _definition(organization_id=uuid4(), duration_days=1)
    started = datetime(2026, 1, 1, 23, 30, tzinfo=ZoneInfo(BERLIN))
    local = definition.due_at(started).astimezone(ZoneInfo(BERLIN))
    assert (local.year, local.month, local.day) == (2026, 1, 2)
    assert (local.hour, local.minute) == (23, 30)


# ---------------------------------------------------------------------------
# No global user id / no identity payloads (invariants 1, 11, 13)
# ---------------------------------------------------------------------------


def test_case_party_references_are_minted_per_case_and_never_shared() -> None:
    first = mint_case_party_reference()
    second = mint_case_party_reference()
    assert first != second
    assert isinstance(first, UUID)


def test_registry_metadata_rejects_identity_field_names() -> None:
    with pytest.raises(ProcessingRegistryIdentityPayloadRejectedError):
        reject_identity_payload_keys({"email": "x"}, where="test")
    with pytest.raises(ProcessingRegistryIdentityPayloadRejectedError):
        reject_identity_payload_keys({"user_id": "x", "purpose": "y"}, where="test")
    reject_identity_payload_keys({"purpose_note_code": "y"}, where="test")


def test_processing_activity_rejects_identity_metadata() -> None:
    with pytest.raises(ProcessingRegistryIdentityPayloadRejectedError):
        _processing_activity(additional_metadata={"national_id": "redacted"})


def test_processing_activity_requires_its_mandatory_categories() -> None:
    with pytest.raises(ProcessingRegistryIncompleteError):
        _processing_activity(data_subject_categories=())


def test_processing_activity_lifecycle_is_a_closed_state_machine() -> None:
    activity = _processing_activity()
    activated = activity.with_status(RegistryEntryStatus.ACTIVE)
    assert activated.status is RegistryEntryStatus.ACTIVE
    assert activated.activity_version == activity.activity_version + 1
    deprecated = activated.with_status(RegistryEntryStatus.DEPRECATED)
    with pytest.raises(ProcessingActivityTransitionInvalidError):
        deprecated.with_status(RegistryEntryStatus.ACTIVE)


def test_legal_basis_is_a_closed_managed_vocabulary() -> None:
    """ "Legal basis as a managed field" means a closed enum, not free
    text. It asserts nothing about legal sufficiency (ADR-040)."""
    assert LegalBasis("party_statute") is LegalBasis.PARTY_STATUTE
    with pytest.raises(ValueError):
        LegalBasis("whatever_the_operator_typed")


def test_data_asset_requires_its_catalog_fields() -> None:
    with pytest.raises(ProcessingRegistryIncompleteError):
        DataAsset(
            asset_id=uuid4(),
            organization_id=uuid4(),
            name="",
            asset_class="database",
            system_reference="membership-service",
            record_class="membership.record",
            retention_policy_reference=uuid4(),
            status=RegistryEntryStatus.DRAFT,
            valid_from=T0,
            owner_authority_reference=uuid4(),
        )


# ---------------------------------------------------------------------------
# Retention and Legal Hold (invariants 3, 4, 5)
# ---------------------------------------------------------------------------


def test_retention_due_at_uses_the_recorded_retention_start() -> None:
    policy = _policy(retention_days=30)
    assert policy.due_at(T0) == T0 + timedelta(days=30)


def test_retention_policy_version_rules() -> None:
    with pytest.raises(ValueError, match="policy_version"):
        _policy(policy_version=0)
    with pytest.raises(ValueError, match="supersedes_policy_version"):
        _policy(policy_version=2, supersedes=2)


def test_retention_policy_effectivity_window() -> None:
    policy = replace(_policy(), valid_until=T0 + timedelta(days=10))
    assert not policy.is_effective_at(T0 - timedelta(days=1))
    assert policy.is_effective_at(T0)
    assert not policy.is_effective_at(T0 + timedelta(days=10))


def test_hold_covers_by_record_id_and_by_class_but_never_across_organizations() -> None:
    policy = _policy()
    record = _record(policy)
    assert _hold(record).covers(record)
    assert _hold(record, by_class=True).covers(record)

    foreign = replace(record, organization_id=uuid4())
    assert not _hold(record).covers(foreign)
    assert not _hold(record, by_class=True).covers(foreign)


def test_hold_applicability_separates_blocking_from_indeterminate() -> None:
    policy = _policy()
    record = _record(policy)
    active = _hold(record)
    unknown = _hold(record, status=LegalHoldStatus.INDETERMINATE)
    released = _hold(record).release(
        T0 + timedelta(days=1), released_by_authority_reference=uuid4(), reason_code=REASON
    )

    blocked = evaluate_hold_applicability(record, (active, released))
    assert blocked.is_blocked
    assert not blocked.is_undetermined

    undetermined = evaluate_hold_applicability(record, (unknown,))
    assert not undetermined.is_blocked
    assert undetermined.is_undetermined

    clear = evaluate_hold_applicability(record, (released,))
    assert not clear.is_blocked
    assert not clear.is_undetermined


def test_hold_history_is_append_only_across_release() -> None:
    policy = _policy()
    record = _record(policy)
    issued = _hold(record).with_issue_entry(reason_code=REASON)
    released = issued.release(
        T0 + timedelta(days=2), released_by_authority_reference=uuid4(), reason_code=REASON
    )
    assert [entry.action for entry in released.history] == ["issued", "released"]
    assert released.history[0] == issued.history[0]
    assert released.status is LegalHoldStatus.RELEASED


def test_a_released_hold_cannot_be_released_again_or_become_indeterminate() -> None:
    policy = _policy()
    record = _record(policy)
    released = _hold(record).release(
        T0, released_by_authority_reference=uuid4(), reason_code=REASON
    )
    with pytest.raises(LegalHoldTransitionInvalidError):
        released.release(T0, released_by_authority_reference=uuid4(), reason_code=REASON)
    with pytest.raises(LegalHoldTransitionInvalidError):
        released.mark_indeterminate(T0, actor_authority_reference=uuid4(), reason_code=REASON)


def test_rebinding_a_record_to_a_new_policy_version_drops_its_authorization() -> None:
    """Invariant 5's structural half: a policy supersession can never
    leave a standing destruction authorization usable."""
    policy = _policy()
    record = _record(policy, retention_start_at=T0)
    authorized = replace(
        record.with_state(GovernedRecordState.DISPOSAL_AUTHORIZED),
        destruction_authorization_id=uuid4(),
    )

    rebound = authorized.rebound_to_policy_version(2)
    assert rebound.retention_policy_version == 2
    assert rebound.state is GovernedRecordState.ACTIVE
    assert rebound.destruction_authorization_id is None
    assert rebound.record_version > authorized.record_version


def test_governed_record_state_machine_forbids_active_to_destroyed() -> None:
    policy = _policy()
    record = _record(policy)
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        record.with_state(GovernedRecordState.DESTROYED)


def test_a_destroyed_record_must_reference_its_evidence() -> None:
    policy = _policy()
    record = _record(policy)
    with pytest.raises(ValueError, match="destruction evidence"):
        replace(record, state=GovernedRecordState.DESTROYED)


def test_a_retention_start_event_from_another_organization_is_refused() -> None:
    policy = _policy()
    record = _record(policy)
    foreign_start = RetentionStartEvent(
        retention_start_event_id=uuid4(),
        record_id=record.record_id,
        organization_id=uuid4(),
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        occurred_at=T0,
        recorded_at=T0,
        source_reference="case:1",
    )
    with pytest.raises(LegalHoldScopeMismatchError):
        record.with_retention_start(foreign_start)


def test_destruction_authorization_and_evidence_carry_no_content() -> None:
    """Both entities exist to prove *that* something happened; neither
    has a field that could hold the destroyed material."""
    forbidden = {"content", "payload", "document", "document_bytes", "body", "attachment"}
    assert not set(DestructionAuthorization.__dataclass_fields__) & forbidden
    assert not set(DestructionEvidence.__dataclass_fields__) & forbidden


def test_retention_start_event_rejects_recording_before_occurrence() -> None:
    with pytest.raises(ValueError, match="recorded_at"):
        RetentionStartEvent(
            retention_start_event_id=uuid4(),
            record_id=uuid4(),
            organization_id=uuid4(),
            trigger=RetentionTrigger.CASE_CLOSED_AT,
            occurred_at=T0,
            recorded_at=T0 - timedelta(seconds=1),
            source_reference="case:1",
        )


# ---------------------------------------------------------------------------
# Deadlines (invariants 6, 7)
# ---------------------------------------------------------------------------


def test_status_and_due_at_are_derived_properties_not_stored_fields() -> None:
    """The structural half of invariant 6: there is no `status` or
    `due_at` field a caller could assign, so the only way either changes
    is by appending a history entry."""
    stored_fields = set(ProceduralDeadline.__dataclass_fields__)
    assert "status" not in stored_fields
    assert "due_at" not in stored_fields
    assert "history" in stored_fields

    deadline = _deadline()
    assert deadline.status is DeadlineStatus.RUNNING
    assert deadline.due_at is not None


def test_suspension_preserves_remaining_time_and_appends_history() -> None:
    deadline = _deadline(duration_days=10)
    original_due = deadline.due_at
    suspended = deadline.suspend(
        T0 + timedelta(days=2), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert suspended.status is DeadlineStatus.SUSPENDED
    assert suspended.remaining_seconds == 8 * 86400
    assert len(suspended.history) == 2
    assert suspended.history[0] == deadline.history[0]
    assert suspended.history[1].due_at_before == original_due


def test_resume_recomputes_the_due_time_from_the_remaining_period() -> None:
    deadline = _deadline(duration_days=10)
    suspended = deadline.suspend(
        T0 + timedelta(days=2), reason_code=REASON, actor_party_reference=uuid4()
    )
    resumed = suspended.resume(
        T0 + timedelta(days=5), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert resumed.status is DeadlineStatus.RUNNING
    assert resumed.due_at == T0 + timedelta(days=13)
    assert [entry.event_type for entry in resumed.history] == [
        DeadlineEventType.STARTED,
        DeadlineEventType.SUSPENDED,
        DeadlineEventType.RESUMED,
    ]


def test_extension_records_both_the_old_and_new_due_time() -> None:
    deadline = _deadline(duration_days=10)
    before = deadline.due_at
    assert before is not None
    extended = deadline.extend(
        T0 + timedelta(days=1),
        additional_days=5,
        reason_code=REASON,
        actor_party_reference=uuid4(),
    )
    entry = extended.history[-1]
    assert entry.event_type is DeadlineEventType.EXTENDED
    assert entry.due_at_before == before
    assert entry.due_at_after is not None
    assert entry.due_at_after > before


def test_completion_expiry_and_escalation_transitions() -> None:
    deadline = _deadline(duration_days=10)
    escalated = deadline.escalate(
        T0 + timedelta(days=8), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert escalated.status is DeadlineStatus.ESCALATED

    expired = escalated.expire(
        T0 + timedelta(days=11), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert expired.status is DeadlineStatus.EXPIRED

    satisfied = deadline.satisfy(
        T0 + timedelta(days=3), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert satisfied.status is DeadlineStatus.SATISFIED


def test_the_whole_history_survives_every_transition_in_order() -> None:
    """Invariant 6 end to end: after start -> suspend -> resume ->
    extend -> satisfy, all five entries are present, contiguous, and
    none of the earlier ones changed."""
    started = _deadline(duration_days=10)
    suspended = started.suspend(
        T0 + timedelta(days=2), reason_code=REASON, actor_party_reference=uuid4()
    )
    resumed = suspended.resume(
        T0 + timedelta(days=3), reason_code=REASON, actor_party_reference=uuid4()
    )
    extended = resumed.extend(
        T0 + timedelta(days=4),
        additional_days=2,
        reason_code=REASON,
        actor_party_reference=uuid4(),
    )
    final = extended.satisfy(
        T0 + timedelta(days=5), reason_code=REASON, actor_party_reference=uuid4()
    )

    assert [entry.event_type for entry in final.history] == [
        DeadlineEventType.STARTED,
        DeadlineEventType.SUSPENDED,
        DeadlineEventType.RESUMED,
        DeadlineEventType.EXTENDED,
        DeadlineEventType.SATISFIED,
    ]
    assert [entry.sequence for entry in final.history] == [1, 2, 3, 4, 5]
    assert final.history[:4] == extended.history
    assert final.history[0] == started.history[0]


def test_a_deadline_cannot_expire_before_its_own_due_time() -> None:
    deadline = _deadline(duration_days=10)
    with pytest.raises(DeadlineTransitionInvalidError):
        deadline.expire(T0 + timedelta(days=1), reason_code=REASON, actor_party_reference=uuid4())


def test_terminal_deadlines_reject_further_transitions() -> None:
    satisfied = _deadline(duration_days=10).satisfy(
        T0 + timedelta(days=1), reason_code=REASON, actor_party_reference=uuid4()
    )
    for call in (
        lambda: satisfied.suspend(T0, reason_code=REASON, actor_party_reference=uuid4()),
        lambda: satisfied.resume(T0, reason_code=REASON, actor_party_reference=uuid4()),
        lambda: satisfied.expire(T0, reason_code=REASON, actor_party_reference=uuid4()),
        lambda: satisfied.extend(
            T0, additional_days=1, reason_code=REASON, actor_party_reference=uuid4()
        ),
        lambda: satisfied.supersede(
            T0,
            successor_deadline_id=uuid4(),
            reason_code=REASON,
            actor_party_reference=uuid4(),
        ),
    ):
        with pytest.raises(DeadlineTransitionInvalidError):
            call()


def test_an_extension_must_add_a_positive_number_of_days() -> None:
    deadline = _deadline()
    with pytest.raises(DeadlineTransitionInvalidError):
        deadline.extend(T0, additional_days=0, reason_code=REASON, actor_party_reference=uuid4())


def test_supersession_keeps_the_old_history_and_links_the_successor() -> None:
    """Invariant 7: a replaced deadline is explicitly superseded, keeping
    its entire history, never silently reset."""
    deadline = _deadline(duration_days=10)
    successor_id = uuid4()
    superseded = deadline.supersede(
        T0 + timedelta(days=1),
        successor_deadline_id=successor_id,
        reason_code=REASON,
        actor_party_reference=uuid4(),
    )
    assert superseded.superseded_by_deadline_id == successor_id
    assert superseded.history[0] == deadline.history[0]
    assert superseded.history[-1].event_type is DeadlineEventType.SUPERSEDED
    assert superseded.status is DeadlineStatus.CANCELLED


def test_deadline_history_must_be_contiguous_and_start_with_started() -> None:
    deadline = _deadline()
    with pytest.raises(DeadlineTransitionInvalidError):
        replace(deadline, history=())
    suspended = deadline.suspend(
        T0 + timedelta(days=1), reason_code=REASON, actor_party_reference=uuid4()
    )
    with pytest.raises(DeadlineTransitionInvalidError):
        replace(suspended, history=(suspended.history[1],))


def test_a_deadline_definition_cannot_be_used_by_another_organization() -> None:
    definition = _definition(organization_id=uuid4())
    with pytest.raises(LegalHoldScopeMismatchError):
        build_started_deadline(
            deadline_id=uuid4(),
            definition=definition,
            case_id=uuid4(),
            organization_id=uuid4(),
            started_at=T0,
            reason_code=REASON,
            actor_party_reference=uuid4(),
        )


def test_is_overdue_at_only_reports_live_deadlines() -> None:
    deadline = _deadline(duration_days=10)
    assert not deadline.is_overdue_at(T0 + timedelta(days=9))
    assert deadline.is_overdue_at(T0 + timedelta(days=11))
    suspended = deadline.suspend(
        T0 + timedelta(days=1), reason_code=REASON, actor_party_reference=uuid4()
    )
    assert not suspended.is_overdue_at(T0 + timedelta(days=99))


# ---------------------------------------------------------------------------
# Cases, roles, conflicts, disputes (invariants 8, 9, 10)
# ---------------------------------------------------------------------------


def test_the_three_separated_roles_must_be_three_distinct_references() -> None:
    shared = uuid4()
    with pytest.raises(ProceduralRoleConflictError):
        ProceduralCase(
            case_id=uuid4(),
            organization_id=uuid4(),
            case_type=CaseType.INTERNAL_DISPUTE,
            status=CaseStatus.OPEN,
            opened_at=T0,
            subject_reference="dispute:1",
            procedural_authority_reference=shared,
            workflow_type="internal_dispute",
            case_handler_reference=shared,
        )


def test_case_handler_and_decision_maker_cannot_collide_with_other_roles() -> None:
    authority = uuid4()
    case = _case(procedural_authority_reference=authority)
    with pytest.raises(ProceduralRoleConflictError):
        case.with_case_handler(authority)
    handler = uuid4()
    with_handler = case.with_case_handler(handler)
    with pytest.raises(ProceduralIndependenceViolationError):
        with_handler.with_decision_maker(handler)
    with pytest.raises(ProceduralIndependenceViolationError):
        with_handler.with_decision_maker(authority)


def test_case_state_machine_rejects_unlisted_transitions_and_undecided_closure() -> None:
    case = _case()
    active = case.transition(CaseStatus.ADMISSIBILITY_REVIEW, T0).transition(CaseStatus.ACTIVE, T0)
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        active.transition(CaseStatus.OPEN, T0)
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        active.transition(CaseStatus.DECIDED, T0)


def test_closing_a_case_requires_an_explicit_closure_reason_code() -> None:
    case = _case().transition(CaseStatus.ADMISSIBILITY_REVIEW, T0)
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        case.transition(CaseStatus.CLOSED, T0)
    closed = case.transition(CaseStatus.CLOSED, T0, closure_reason_code="PROCEDURAL_CASE_CLOSED")
    assert closed.closed_at == T0


def test_required_steps_track_what_is_still_outstanding() -> None:
    case = ProceduralCase(
        case_id=uuid4(),
        organization_id=uuid4(),
        case_type=CaseType.COMPLIANCE_REVIEW,
        status=CaseStatus.OPEN,
        opened_at=T0,
        subject_reference="review:1",
        procedural_authority_reference=uuid4(),
        workflow_type="compliance_review",
        required_steps=(
            ProceduralStep(step_code="intake", required=True),
            ProceduralStep(step_code="hearing", required=False),
        ),
    )
    assert case.outstanding_steps == ("intake",)
    assert case.with_completed_step("intake", T0).outstanding_steps == ()
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        case.with_completed_step("unknown", T0)


def test_evidence_references_are_appended_once_and_never_carry_content() -> None:
    case = _case()
    once = case.with_evidence_reference("pack-11:document:1")
    assert once.evidence_references == ("pack-11:document:1",)
    assert once.with_evidence_reference("pack-11:document:1") is once


def test_dispute_parties_must_be_distinct() -> None:
    shared = uuid4()
    with pytest.raises(ProceduralRoleConflictError):
        DisputeParties(
            case_id=uuid4(),
            organization_id=uuid4(),
            claimant_reference=shared,
            respondent_reference=shared,
        )


def test_nobody_may_appoint_themselves_as_independent_decision_maker() -> None:
    case = _case()
    candidate = uuid4()
    with pytest.raises(ProceduralIndependenceViolationError, match="themselves"):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=candidate,
            appointing_party_reference=candidate,
            role_assignments=(),
            conflict_declarations=(_declaration(case, candidate, ConflictState.NONE_DECLARED),),
        )


def test_a_party_to_the_dispute_may_neither_appoint_nor_become_the_decision_maker() -> None:
    case = _case()
    claimant = uuid4()
    candidate = uuid4()
    roles = (_role(case, ProceduralRole.CLAIMANT, claimant),)

    with pytest.raises(ProceduralIndependenceViolationError, match="claimant"):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=candidate,
            appointing_party_reference=claimant,
            role_assignments=roles,
            conflict_declarations=(_declaration(case, candidate, ConflictState.NONE_DECLARED),),
        )

    with pytest.raises(ProceduralIndependenceViolationError, match="party to the dispute"):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=claimant,
            appointing_party_reference=case.procedural_authority_reference,
            role_assignments=roles,
            conflict_declarations=(_declaration(case, claimant, ConflictState.NONE_DECLARED),),
        )


def test_the_case_handler_may_neither_appoint_nor_become_the_decision_maker() -> None:
    handler = uuid4()
    case = _case(case_handler_reference=handler)
    candidate = uuid4()

    with pytest.raises(ProceduralIndependenceViolationError, match="case handler"):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=candidate,
            appointing_party_reference=handler,
            role_assignments=(),
            conflict_declarations=(_declaration(case, candidate, ConflictState.NONE_DECLARED),),
        )

    with pytest.raises(ProceduralIndependenceViolationError):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=handler,
            appointing_party_reference=case.procedural_authority_reference,
            role_assignments=(),
            conflict_declarations=(_declaration(case, handler, ConflictState.NONE_DECLARED),),
        )


def test_an_undeclared_conflict_fails_closed_and_a_blocking_one_refuses() -> None:
    case = _case()
    candidate = uuid4()

    with pytest.raises(ConflictOfInterestUndeclaredError):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=candidate,
            appointing_party_reference=case.procedural_authority_reference,
            role_assignments=(),
            conflict_declarations=(),
        )

    for blocking in (ConflictState.DECLARED, ConflictState.CONFIRMED):
        with pytest.raises(ConflictOfInterestBlockingError):
            assert_decision_maker_eligible(
                case=case,
                candidate_party_reference=candidate,
                appointing_party_reference=case.procedural_authority_reference,
                role_assignments=(),
                conflict_declarations=(_declaration(case, candidate, blocking),),
            )


def test_a_clean_or_waived_declaration_permits_the_appointment() -> None:
    case = _case()
    candidate = uuid4()
    for permitted in (ConflictState.NONE_DECLARED, ConflictState.WAIVED):
        assert_decision_maker_eligible(
            case=case,
            candidate_party_reference=candidate,
            appointing_party_reference=case.procedural_authority_reference,
            role_assignments=(),
            conflict_declarations=(_declaration(case, candidate, permitted),),
        )


def test_a_confirmed_or_waived_declaration_must_record_who_decided_it() -> None:
    case = _case()
    with pytest.raises(ValueError, match="who decided it"):
        ConflictOfInterestDeclaration(
            declaration_id=uuid4(),
            case_id=case.case_id,
            organization_id=case.organization_id,
            party_reference=uuid4(),
            state=ConflictState.CONFIRMED,
            basis_code="same_local_branch",
            declared_at=T0,
        )


def test_an_appeal_must_reference_a_different_case() -> None:
    case_id = uuid4()
    with pytest.raises(ValueError, match="different case"):
        AppealReference(
            appeal_id=uuid4(),
            organization_id=uuid4(),
            original_case_id=case_id,
            appeal_case_id=case_id,
            filed_at=T0,
            filed_by_party_reference=uuid4(),
        )


def test_case_decision_carries_a_reason_code_and_only_evidence_references() -> None:
    case = _case()
    decision = CaseDecision(
        decision_id=uuid4(),
        case_id=case.case_id,
        organization_id=case.organization_id,
        outcome=DecisionOutcome.DISMISSED,
        reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_at=T0,
        decided_by_party_reference=uuid4(),
        decided_by_role=ProceduralRole.INDEPENDENT_DECISION_MAKER,
        evidence_references=("pack-11:document:7",),
    )
    assert decision.evidence_references == ("pack-11:document:7",)
    assert "content" not in CaseDecision.__dataclass_fields__


def test_a_case_cannot_take_a_decision_belonging_to_another_case() -> None:
    case = _case()
    other = CaseDecision(
        decision_id=uuid4(),
        case_id=uuid4(),
        organization_id=case.organization_id,
        outcome=DecisionOutcome.UPHELD,
        reason_code="X",
        decided_at=T0,
        decided_by_party_reference=uuid4(),
        decided_by_role=ProceduralRole.INDEPENDENT_DECISION_MAKER,
    )
    with pytest.raises(ValueError, match="does not belong"):
        case.with_decision(other)


# ---------------------------------------------------------------------------
# Data-subject requests (invariant 11)
# ---------------------------------------------------------------------------


def test_data_subject_request_stores_no_identity_attribute() -> None:
    fields = set(DataSubjectRequest.__dataclass_fields__)
    forbidden = {
        "email",
        "full_name",
        "first_name",
        "last_name",
        "address",
        "date_of_birth",
        "national_id",
        "eid_attributes",
        "kyc_payload",
        "user_id",
        "person_id",
        "member_id",
    }
    assert not fields & forbidden
    assert "identity_verification_status" in fields
    assert "identity_verification_reference" in fields


def test_request_state_machine_rejects_unlisted_transitions() -> None:
    request = _request()
    with pytest.raises(DataSubjectRequestTransitionInvalidError):
        request.with_status(DataSubjectRequestStatus.ANSWERED)
    assert request.with_status(DataSubjectRequestStatus.CLASSIFIED).status is (
        DataSubjectRequestStatus.CLASSIFIED
    )


def test_a_limited_response_must_carry_a_limitation_reason_code() -> None:
    request = _request()
    with pytest.raises(ValueError, match="limitation reason code"):
        request.with_response(
            ResponseDecision.REFUSED,
            limitation_reason_code=None,
            completion_evidence_reference=None,
        )
    refused = request.with_response(
        ResponseDecision.REFUSED,
        limitation_reason_code="IDENTITY_VERIFICATION_INSUFFICIENT",
        completion_evidence_reference="pack-11:letter:2",
    )
    assert refused.limitation_reason_code == "IDENTITY_VERIFICATION_INSUFFICIENT"


def test_search_result_references_are_references_not_results() -> None:
    request = _request()
    once = request.with_search_result_reference("search:2026-1")
    assert once.search_result_references == ("search:2026-1",)
    assert once.with_search_result_reference("search:2026-1") is once


# ---------------------------------------------------------------------------
# Cross-scope authority grants (invariant 2)
# ---------------------------------------------------------------------------


def test_a_grant_permits_only_its_own_pair_capability_and_window() -> None:
    granting = uuid4()
    grantee = uuid4()
    grant = CrossScopeAuthorityGrant(
        grant_id=uuid4(),
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capabilities=frozenset({ScopeCapability.READ_CASE}),
        valid_from=T0,
        valid_until=T0 + timedelta(days=30),
        authorizing_decision_reference=uuid4(),
    )
    assert grant.permits(
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capability=ScopeCapability.READ_CASE,
        at=T0 + timedelta(days=1),
    )
    assert not grant.permits(
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capability=ScopeCapability.MANAGE_CASE,
        at=T0 + timedelta(days=1),
    )
    # A grant is never symmetric: reversing the pair revokes nothing but
    # permits nothing either.
    assert not grant.permits(
        granting_organization_id=grantee,
        grantee_organization_id=granting,
        capability=ScopeCapability.READ_CASE,
        at=T0 + timedelta(days=1),
    )
    assert not grant.permits(
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capability=ScopeCapability.READ_CASE,
        at=T0 + timedelta(days=31),
    )


def test_a_revoked_grant_stops_permitting_from_its_revocation_instant() -> None:
    granting = uuid4()
    grantee = uuid4()
    grant = CrossScopeAuthorityGrant(
        grant_id=uuid4(),
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capabilities=frozenset({ScopeCapability.MANAGE_CASE}),
        valid_from=T0,
        valid_until=None,
        authorizing_decision_reference=uuid4(),
        revoked_at=T0 + timedelta(days=5),
    )
    assert grant.permits(
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capability=ScopeCapability.MANAGE_CASE,
        at=T0 + timedelta(days=4),
    )
    assert not grant.permits(
        granting_organization_id=granting,
        grantee_organization_id=grantee,
        capability=ScopeCapability.MANAGE_CASE,
        at=T0 + timedelta(days=5),
    )


def test_a_grant_must_name_two_different_organizations_and_a_capability() -> None:
    org = uuid4()
    with pytest.raises(ValueError, match="two different organizations"):
        CrossScopeAuthorityGrant(
            grant_id=uuid4(),
            granting_organization_id=org,
            grantee_organization_id=org,
            capabilities=frozenset({ScopeCapability.READ_CASE}),
            valid_from=T0,
            valid_until=None,
            authorizing_decision_reference=uuid4(),
        )
    with pytest.raises(ValueError, match="at least one capability"):
        CrossScopeAuthorityGrant(
            grant_id=uuid4(),
            granting_organization_id=org,
            grantee_organization_id=uuid4(),
            capabilities=frozenset(),
            valid_from=T0,
            valid_until=None,
            authorizing_decision_reference=uuid4(),
        )


def test_a_legal_hold_scope_must_name_something() -> None:
    with pytest.raises(ValueError, match="at least one record, class or case"):
        LegalHoldScope()
