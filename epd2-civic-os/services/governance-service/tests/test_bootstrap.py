"""Tests for the deployment-time bootstrap seed (ADR-020 item 6):
exactly two distinct initial actors, an immutable manifest with a
checksum, real `AuditEvent`s, and permanent self-disabling after the
first successful execution."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_governance_service.bootstrap import (
    BOOTSTRAP_ASSIGNED_BY_MARKER,
    BootstrapAlreadyExecutedError,
    BootstrapResult,
    InMemoryBootstrapSeedStore,
    run_bootstrap_seed,
)
from epd2_governance_service.domain import GLOBAL_SCOPE_ID, RoleAssignmentStatus
from epd2_governance_service.exceptions import SameActorApprovalRejectedError
from epd2_governance_service.storage import InMemoryRoleAssignmentStore

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _run(
    role_store: InMemoryRoleAssignmentStore,
    bootstrap_store: InMemoryBootstrapSeedStore,
    audit_store: InMemoryAuditEventStore,
    *,
    first_actor_id: UUID | None = None,
    second_actor_id: UUID | None = None,
) -> BootstrapResult:
    return run_bootstrap_seed(
        role_store,
        bootstrap_store,
        audit_store,
        first_role_assignment_id=uuid4(),
        first_actor_id=first_actor_id if first_actor_id is not None else uuid4(),
        first_role_code="governance_policy_proposer",
        first_scope_id=GLOBAL_SCOPE_ID,
        second_role_assignment_id=uuid4(),
        second_actor_id=second_actor_id if second_actor_id is not None else uuid4(),
        second_role_code="governance_policy_approver",
        second_scope_id=GLOBAL_SCOPE_ID,
        valid_from=NOW,
        correlation_id=uuid4(),
        clock=FixedClock(NOW),
    )


def test_bootstrap_creates_two_active_distinct_role_assignments() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()

    result = _run(role_store, bootstrap_store, audit_store)

    assert result.first_assignment.status is RoleAssignmentStatus.ACTIVE
    assert result.second_assignment.status is RoleAssignmentStatus.ACTIVE
    assert result.first_assignment.actor_id != result.second_assignment.actor_id
    assert result.first_assignment.assigned_by == BOOTSTRAP_ASSIGNED_BY_MARKER
    assert result.second_assignment.assigned_by == BOOTSTRAP_ASSIGNED_BY_MARKER


def test_bootstrap_produces_immutable_manifest_with_checksum() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()

    result = _run(role_store, bootstrap_store, audit_store)

    assert result.manifest.checksum
    assert bootstrap_store.get_manifest() == result.manifest


def test_bootstrap_produces_real_audit_events() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()

    result = _run(role_store, bootstrap_store, audit_store)

    assert result.first_audit_event.target_id == result.first_assignment.role_assignment_id
    assert result.second_audit_event.target_id == result.second_assignment.role_assignment_id


def test_bootstrap_permanently_disabled_after_first_execution() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()

    _run(role_store, bootstrap_store, audit_store)

    with pytest.raises(BootstrapAlreadyExecutedError):
        _run(role_store, bootstrap_store, audit_store)


def test_bootstrap_rejects_same_actor_for_both_seats() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()
    same_actor = uuid4()

    with pytest.raises(SameActorApprovalRejectedError):
        _run(
            role_store,
            bootstrap_store,
            audit_store,
            first_actor_id=same_actor,
            second_actor_id=same_actor,
        )


def test_bootstrap_rejects_role_code_outside_pilot_taxonomy() -> None:
    role_store = InMemoryRoleAssignmentStore()
    bootstrap_store = InMemoryBootstrapSeedStore()
    audit_store = InMemoryAuditEventStore()

    with pytest.raises(ValueError, match="pilot role taxonomy"):
        run_bootstrap_seed(
            role_store,
            bootstrap_store,
            audit_store,
            first_role_assignment_id=uuid4(),
            first_actor_id=uuid4(),
            first_role_code="not_a_real_role",
            first_scope_id=GLOBAL_SCOPE_ID,
            second_role_assignment_id=uuid4(),
            second_actor_id=uuid4(),
            second_role_code="observer",
            second_scope_id=GLOBAL_SCOPE_ID,
            valid_from=NOW,
            correlation_id=uuid4(),
            clock=FixedClock(NOW),
        )
