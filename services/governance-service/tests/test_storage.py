"""Storage-layer tests for Governance Service's in-memory reference
adapters: idempotent-by-content `create()`, conflict detection, and the
derived-query helper methods each store adds beyond the plain CRUD
surface (`get_active_for_policy_type`, `get_current_result_finality_
determination`, `has_unresolved_challenges`)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    GovernancePolicy,
    GovernancePolicyStatus,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
    SubmitterAuthorizationType,
    TechnicalChallenge,
    TechnicalChallengeStatus,
)
from epd2_governance_service.exceptions import (
    GovernanceDecisionConflictError,
    GovernancePolicyConflictError,
    RoleAssignmentConflictError,
    TechnicalChallengeConflictError,
)
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
    InMemoryGovernancePolicyStore,
    InMemoryRoleAssignmentStore,
    InMemoryTechnicalChallengeStore,
)

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _role_assignment(**overrides: object) -> RoleAssignment:
    fields: dict[str, object] = {
        "role_assignment_id": uuid4(),
        "actor_id": uuid4(),
        "role_code": "observer",
        "scope_id": GLOBAL_SCOPE_ID,
        "valid_from": NOW,
        "valid_until": None,
        "assigned_by": uuid4(),
        "approval_reference": None,
        "status": RoleAssignmentStatus.PENDING,
    }
    fields.update(overrides)
    return RoleAssignment(**fields)  # type: ignore[arg-type]


def test_role_assignment_store_create_is_idempotent() -> None:
    store = InMemoryRoleAssignmentStore()
    assignment = _role_assignment()
    first = store.create(assignment)
    second = store.create(assignment)
    assert first == second


def test_role_assignment_store_create_conflict() -> None:
    store = InMemoryRoleAssignmentStore()
    assignment_id = uuid4()
    store.create(_role_assignment(role_assignment_id=assignment_id, role_code="observer"))
    with pytest.raises(RoleAssignmentConflictError):
        store.create(
            _role_assignment(role_assignment_id=assignment_id, role_code="oversight_reviewer")
        )


def test_role_assignment_store_list_by_actor() -> None:
    store = InMemoryRoleAssignmentStore()
    actor_id = uuid4()
    a = store.create(_role_assignment(actor_id=actor_id))
    b = store.create(_role_assignment(actor_id=actor_id))
    store.create(_role_assignment(actor_id=uuid4()))
    assignments = store.list_by_actor(actor_id)
    assert {a.role_assignment_id, b.role_assignment_id} == {
        x.role_assignment_id for x in assignments
    }


def _policy(**overrides: object) -> GovernancePolicy:
    fields: dict[str, object] = {
        "governance_policy_id": uuid4(),
        "policy_type": GovernancePolicyType.ROLE_TAXONOMY,
        "rule_definition": {},
        "effective_from": NOW,
        "proposed_by_role_id": uuid4(),
        "approved_by_role_id": uuid4(),
        "version": 1,
        "status": GovernancePolicyStatus.DRAFT,
    }
    fields.update(overrides)
    return GovernancePolicy(**fields)  # type: ignore[arg-type]


def test_governance_policy_store_create_conflict() -> None:
    store = InMemoryGovernancePolicyStore()
    policy_id = uuid4()
    store.create(_policy(governance_policy_id=policy_id, version=1))
    with pytest.raises(GovernancePolicyConflictError):
        store.create(_policy(governance_policy_id=policy_id, version=2))


def test_governance_policy_store_active_for_policy_type_and_supersede() -> None:
    store = InMemoryGovernancePolicyStore()
    v1 = store.create(_policy(version=1))
    store.save(v1.with_status(GovernancePolicyStatus.ACTIVE))
    assert store.get_active_for_policy_type(GovernancePolicyType.ROLE_TAXONOMY.value) is not None

    v1_active = store.get(v1.governance_policy_id)
    assert v1_active is not None
    superseded = v1_active.with_status(GovernancePolicyStatus.SUPERSEDED)
    store.save(superseded)
    assert store.get_active_for_policy_type(GovernancePolicyType.ROLE_TAXONOMY.value) is None


def test_governance_policy_store_latest_version() -> None:
    store = InMemoryGovernancePolicyStore()
    assert store.latest_version_for_policy_type(GovernancePolicyType.ROLE_TAXONOMY.value) == 0
    store.create(_policy(version=1))
    store.create(_policy(version=2))
    assert store.latest_version_for_policy_type(GovernancePolicyType.ROLE_TAXONOMY.value) == 2


def _decision(**overrides: object) -> GovernanceDecision:
    fields: dict[str, object] = {
        "governance_decision_id": uuid4(),
        "decision_type": GovernanceDecisionType.RESULT_FINALITY_DETERMINATION,
        "subject_reference": {"result_publication_id": str(uuid4())},
        "proposed_by_role_id": uuid4(),
        "approved_by_role_id": None,
        "rejected_by_role_id": None,
        "reason_code": "TEST_REASON",
        "evidence_references": (),
        "finality_outcome": None,
        "created_at": NOW,
        "decided_at": None,
        "supersedes_decision_id": None,
        "status": GovernanceDecisionStatus.PROPOSED,
    }
    fields.update(overrides)
    return GovernanceDecision(**fields)  # type: ignore[arg-type]


def test_governance_decision_store_create_conflict() -> None:
    store = InMemoryGovernanceDecisionStore()
    decision_id = uuid4()
    store.create(_decision(governance_decision_id=decision_id, reason_code="A"))
    with pytest.raises(GovernanceDecisionConflictError):
        store.create(_decision(governance_decision_id=decision_id, reason_code="B"))


def test_governance_decision_store_find_superseding() -> None:
    store = InMemoryGovernanceDecisionStore()
    result_publication_id = uuid4()
    original = store.create(
        _decision(subject_reference={"result_publication_id": str(result_publication_id)})
    )
    assert store.find_superseding(original.governance_decision_id) is None
    superseding = store.create(
        _decision(
            subject_reference={"result_publication_id": str(result_publication_id)},
            supersedes_decision_id=original.governance_decision_id,
            status=GovernanceDecisionStatus.APPROVED,
            approved_by_role_id=uuid4(),
            decided_at=NOW,
        )
    )
    found = store.find_superseding(original.governance_decision_id)
    assert found is not None
    assert found.governance_decision_id == superseding.governance_decision_id


def test_governance_decision_store_current_result_finality_determination() -> None:
    from epd2_governance_service.domain import FinalityOutcome

    store = InMemoryGovernanceDecisionStore()
    result_publication_id = uuid4()
    assert store.get_current_result_finality_determination(result_publication_id) is None

    approved = store.create(
        _decision(
            subject_reference={"result_publication_id": str(result_publication_id)},
            status=GovernanceDecisionStatus.APPROVED,
            approved_by_role_id=uuid4(),
            decided_at=NOW,
            finality_outcome=FinalityOutcome.FINAL,
        )
    )
    current = store.get_current_result_finality_determination(result_publication_id)
    assert current is not None
    assert current.governance_decision_id == approved.governance_decision_id


def _challenge(**overrides: object) -> TechnicalChallenge:
    fields: dict[str, object] = {
        "technical_challenge_id": uuid4(),
        "result_publication_id": uuid4(),
        "submitter_authorization_type": SubmitterAuthorizationType.PARTICIPATION_CREDENTIAL,
        "submitter_authorization_reference": "opaque-ref",
        "challenge_reason_code": "TEST_CHALLENGE",
        "evidence_references": (),
        "submitted_at": NOW,
        "governance_decision_id": None,
        "status": TechnicalChallengeStatus.SUBMITTED,
    }
    fields.update(overrides)
    return TechnicalChallenge(**fields)  # type: ignore[arg-type]


def test_technical_challenge_store_create_conflict() -> None:
    store = InMemoryTechnicalChallengeStore()
    challenge_id = uuid4()
    store.create(_challenge(technical_challenge_id=challenge_id, challenge_reason_code="A"))
    with pytest.raises(TechnicalChallengeConflictError):
        store.create(_challenge(technical_challenge_id=challenge_id, challenge_reason_code="B"))


def test_technical_challenge_store_has_unresolved_challenges() -> None:
    store = InMemoryTechnicalChallengeStore()
    result_publication_id = uuid4()
    assert store.has_unresolved_challenges(result_publication_id) is False
    store.create(_challenge(result_publication_id=result_publication_id))
    assert store.has_unresolved_challenges(result_publication_id) is True


def test_technical_challenge_store_list_by_result_publication() -> None:
    store = InMemoryTechnicalChallengeStore()
    result_publication_id = uuid4()
    a = store.create(_challenge(result_publication_id=result_publication_id))
    store.create(_challenge(result_publication_id=uuid4()))
    challenges = store.list_by_result_publication(result_publication_id)
    assert [c.technical_challenge_id for c in challenges] == [a.technical_challenge_id]
