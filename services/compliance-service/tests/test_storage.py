"""Storage-adapter tests for compliance-service (PACK-09).

These cover the three storage rules `storage.py`'s own docstring names -
no delete method anywhere, create-once destruction evidence, and scoped
lookups that report a foreign record as absent - plus the append-only
guards on the retention-policy, role-assignment and deadline stores.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_compliance_service.domain import (
    CaseDecision,
    CaseRoleAssignment,
    CaseStatus,
    CaseType,
    DeadlineDefinition,
    DecisionOutcome,
    DestructionEvidence,
    DispositionAction,
    GovernedRecord,
    ProceduralCase,
    ProceduralRole,
    RecordSensitivity,
    RetentionPolicy,
    RetentionStartEvent,
    RetentionTrigger,
    build_started_deadline,
    mint_case_party_reference,
)
from epd2_compliance_service.exceptions import (
    DestructionAlreadyExecutedError,
    ProceduralCaseTransitionInvalidError,
    RetentionPolicyVersionConflictError,
)
from epd2_compliance_service.storage import (
    CaseDecisionStore,
    CaseRoleAssignmentStore,
    DestructionEvidenceStore,
    GovernedRecordStore,
    InMemoryCaseDecisionStore,
    InMemoryCaseRoleAssignmentStore,
    InMemoryDestructionEvidenceStore,
    InMemoryGovernedRecordStore,
    InMemoryProceduralCaseStore,
    InMemoryProceduralDeadlineStore,
    InMemoryRetentionPolicyStore,
    InMemoryRetentionStartEventStore,
    ProceduralCaseStore,
    ProceduralDeadlineStore,
    RetentionPolicyStore,
    RetentionStartEventStore,
)

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
BERLIN = "Europe/Berlin"
REASON = "COMPLIANCE_PROCEDURAL_DEADLINE_STATE_CHANGED"

#: Method names that would let a caller remove governed material through
#: storage. None of PACK-09's stores may expose any of them (invariant 4).
_DELETE_LIKE_METHOD_NAMES = frozenset(
    {"delete", "remove", "purge", "drop", "destroy", "erase", "clear", "truncate"}
)


def _policy(
    *, organization_id: UUID | None = None, policy_id: UUID | None = None, version: int = 1
) -> RetentionPolicy:
    return RetentionPolicy(
        policy_id=policy_id if policy_id is not None else uuid4(),
        organization_id=organization_id if organization_id is not None else uuid4(),
        record_class="case.disciplinary",
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        retention_days=30,
        disposition_action=DispositionAction.DELETE,
        policy_version=version,
        valid_from=T0,
        supersedes_policy_version=version - 1 if version > 1 else None,
    )


def _record(policy: RetentionPolicy) -> GovernedRecord:
    return GovernedRecord(
        record_id=uuid4(),
        organization_id=policy.organization_id,
        record_class=policy.record_class,
        sensitivity=RecordSensitivity.INTERNAL,
        created_at=T0,
        retention_policy_id=policy.policy_id,
        retention_policy_version=policy.policy_version,
        source_reference="membership-service:case:1",
    )


def _evidence(record: GovernedRecord, *, digest: str = "sha256:1") -> DestructionEvidence:
    return DestructionEvidence(
        evidence_id=uuid4(),
        record_id=record.record_id,
        organization_id=record.organization_id,
        authorization_id=uuid4(),
        disposition_action=DispositionAction.DELETE,
        executed_at=T0,
        executed_by_authority_reference=uuid4(),
        evidence_digest=digest,
        retention_policy_id=record.retention_policy_id,
        retention_policy_version=record.retention_policy_version,
    )


def _case(organization_id: UUID) -> ProceduralCase:
    return ProceduralCase(
        case_id=uuid4(),
        organization_id=organization_id,
        case_type=CaseType.INTERNAL_DISPUTE,
        status=CaseStatus.OPEN,
        opened_at=T0,
        subject_reference="dispute:1",
        procedural_authority_reference=uuid4(),
        workflow_type="internal_dispute",
    )


# ---------------------------------------------------------------------------
# Rule 1: no delete method exists anywhere (invariant 4)
# ---------------------------------------------------------------------------


def test_no_store_protocol_or_adapter_exposes_a_delete_like_method() -> None:
    for candidate in (
        RetentionPolicyStore,
        RetentionStartEventStore,
        GovernedRecordStore,
        DestructionEvidenceStore,
        ProceduralCaseStore,
        CaseRoleAssignmentStore,
        CaseDecisionStore,
        ProceduralDeadlineStore,
        InMemoryRetentionPolicyStore,
        InMemoryRetentionStartEventStore,
        InMemoryGovernedRecordStore,
        InMemoryDestructionEvidenceStore,
        InMemoryProceduralCaseStore,
        InMemoryCaseRoleAssignmentStore,
        InMemoryCaseDecisionStore,
        InMemoryProceduralDeadlineStore,
    ):
        offending = {name for name in dir(candidate) if name in _DELETE_LIKE_METHOD_NAMES}
        assert not offending, f"{candidate.__name__} exposes {sorted(offending)}"


# ---------------------------------------------------------------------------
# Rule 2: create-once destruction evidence
# ---------------------------------------------------------------------------


def test_destruction_evidence_is_create_once_and_replays_identically() -> None:
    store = InMemoryDestructionEvidenceStore()
    policy = _policy()
    record = _record(policy)
    evidence = _evidence(record)

    assert store.create_once(evidence) == evidence
    assert store.create_once(evidence) == evidence
    assert store.get_for_record(record.record_id) == evidence


def test_a_second_divergent_destruction_evidence_is_refused() -> None:
    store = InMemoryDestructionEvidenceStore()
    policy = _policy()
    record = _record(policy)
    store.create_once(_evidence(record, digest="sha256:1"))
    with pytest.raises(DestructionAlreadyExecutedError):
        store.create_once(_evidence(record, digest="sha256:2"))


# ---------------------------------------------------------------------------
# Rule 3: scoped lookups never disclose a foreign record
# ---------------------------------------------------------------------------


def test_scoped_lookups_return_none_for_another_organizations_record() -> None:
    store = InMemoryGovernedRecordStore()
    policy = _policy()
    record = store.save(_record(policy))

    assert store.get_in_scope(record.record_id, record.organization_id) == record
    assert store.get_in_scope(record.record_id, uuid4()) is None
    # The unscoped variant exists only for the application layer's own
    # authority resolution and still finds it.
    assert store.get_unscoped(record.record_id) == record


def test_list_for_organization_never_leaks_across_scopes() -> None:
    store = InMemoryGovernedRecordStore()
    org_a = uuid4()
    org_b = uuid4()
    record_a = store.save(_record(_policy(organization_id=org_a)))
    store.save(_record(_policy(organization_id=org_b)))

    assert store.list_for_organization(org_a) == (record_a,)


def test_case_lookups_are_scoped_the_same_way() -> None:
    store = InMemoryProceduralCaseStore()
    case = store.save(_case(uuid4()))
    assert store.get_in_scope(case.case_id, case.organization_id) == case
    assert store.get_in_scope(case.case_id, uuid4()) is None


# ---------------------------------------------------------------------------
# Append-only guards
# ---------------------------------------------------------------------------


def test_a_retention_policy_version_is_never_rewritten() -> None:
    store = InMemoryRetentionPolicyStore()
    policy = _policy()
    store.create_version(policy)
    assert store.create_version(policy) == policy
    with pytest.raises(RetentionPolicyVersionConflictError):
        store.create_version(replace(policy, retention_days=1))


def test_policy_versions_are_listed_in_order_and_the_latest_wins() -> None:
    store = InMemoryRetentionPolicyStore()
    policy_id = uuid4()
    organization_id = uuid4()
    first = store.create_version(
        _policy(policy_id=policy_id, organization_id=organization_id, version=1)
    )
    second = store.create_version(
        _policy(policy_id=policy_id, organization_id=organization_id, version=2)
    )
    assert store.list_versions(policy_id) == (first, second)
    assert store.latest_version(policy_id) == second
    assert store.get_version(policy_id, 1) == first


def test_retention_start_events_accumulate_and_replay_by_id() -> None:
    store = InMemoryRetentionStartEventStore()
    record_id = uuid4()
    event = RetentionStartEvent(
        retention_start_event_id=uuid4(),
        record_id=record_id,
        organization_id=uuid4(),
        trigger=RetentionTrigger.CASE_CLOSED_AT,
        occurred_at=T0,
        recorded_at=T0,
        source_reference="case:1",
    )
    assert store.append(event) == event
    assert store.append(event) == event
    assert store.list_for_record(record_id) == (event,)


def test_case_role_assignments_are_append_only_and_replay_by_id() -> None:
    store = InMemoryCaseRoleAssignmentStore()
    case = _case(uuid4())
    assignment = CaseRoleAssignment(
        assignment_id=uuid4(),
        case_id=case.case_id,
        organization_id=case.organization_id,
        role=ProceduralRole.CASE_HANDLER,
        party_reference=mint_case_party_reference(),
        assigned_at=T0,
        assigned_by_party_reference=mint_case_party_reference(),
    )
    store.append(assignment)
    store.append(assignment)
    assert store.list_for_case(case.case_id) == (assignment,)


def test_a_case_decision_is_create_once_per_case() -> None:
    store = InMemoryCaseDecisionStore()
    case = _case(uuid4())
    decision = CaseDecision(
        decision_id=uuid4(),
        case_id=case.case_id,
        organization_id=case.organization_id,
        outcome=DecisionOutcome.UPHELD,
        reason_code="PROCEDURAL_CASE_TRANSITION_INVALID",
        decided_at=T0,
        decided_by_party_reference=mint_case_party_reference(),
        decided_by_role=ProceduralRole.INDEPENDENT_DECISION_MAKER,
    )
    assert store.create_once(decision) == decision
    assert store.create_once(decision) == decision
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        store.create_once(replace(decision, outcome=DecisionOutcome.DISMISSED))


def test_the_deadline_store_only_accepts_history_extensions() -> None:
    """A second, independent guard for invariant 6 that does not rely on
    the caller going through the domain's own transition methods."""
    store = InMemoryProceduralDeadlineStore()
    organization_id = uuid4()
    definition = DeadlineDefinition(
        definition_id=uuid4(),
        organization_id=organization_id,
        deadline_code="RESPONSE_DUE",
        duration_days=10,
        timezone=BERLIN,
    )
    deadline = build_started_deadline(
        deadline_id=uuid4(),
        definition=definition,
        case_id=uuid4(),
        organization_id=organization_id,
        started_at=T0,
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    store.save(deadline)
    suspended = deadline.suspend(
        T0 + timedelta(days=1),
        reason_code=REASON,
        actor_party_reference=mint_case_party_reference(),
    )
    store.save(suspended)

    with pytest.raises(ValueError, match="append-only"):
        store.save(deadline)

    rewritten_prefix = replace(
        suspended,
        history=(
            replace(suspended.history[0], reason_code="TAMPERED_REASON_CODE"),
            suspended.history[1],
        ),
    )
    with pytest.raises(ValueError, match="append-only"):
        store.save(rewritten_prefix)


def test_deadlines_are_listed_per_case_and_scoped_per_organization() -> None:
    store = InMemoryProceduralDeadlineStore()
    organization_id = uuid4()
    case_id = uuid4()
    definition = DeadlineDefinition(
        definition_id=uuid4(),
        organization_id=organization_id,
        deadline_code="RESPONSE_DUE",
        duration_days=5,
        timezone=BERLIN,
    )
    deadline = store.save(
        build_started_deadline(
            deadline_id=uuid4(),
            definition=definition,
            case_id=case_id,
            organization_id=organization_id,
            started_at=T0,
            reason_code=REASON,
            actor_party_reference=mint_case_party_reference(),
        )
    )
    assert store.list_for_case(case_id) == (deadline,)
    assert store.get_in_scope(deadline.deadline_id, organization_id) == deadline
    assert store.get_in_scope(deadline.deadline_id, uuid4()) is None
