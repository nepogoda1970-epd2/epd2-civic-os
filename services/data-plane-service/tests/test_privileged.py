"""Privileged data-plane operations (PACK-13 §26).

Migration execution under a scoped grant, separation of duties for
destructive migration and schema activation, no arbitrary SQL, no
universal database administrator, and break-glass that adds obligations
rather than removing them.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import (
    NOW,
    OWNER_DOMAIN,
    actor,
    evidence,
    grant,
    scope,
    uid,
)

from epd2_data_plane_service.domain import OrganizationScopeKind, OrganizationScopeReference
from epd2_data_plane_service.exceptions import (
    ManualSqlProhibitedError,
    MigrationSeparationOfDutiesMissingError,
    OperatorPrivilegeInsufficientError,
    PrivilegeAuthorityMissingError,
)
from epd2_data_plane_service.privileged import (
    GRANT_CONFERS_NOTHING_ELSE,
    INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS,
    SEPARATION_OF_DUTIES_OPERATIONS,
    BreakGlassContext,
    DataPlaneOperation,
    DataPlaneRole,
    PrivilegedActionRecord,
    SqlExecutionContext,
    reject_incompatible_roles,
    require_domain_content_authority,
    require_governed_sql_context,
    require_scoped_grant,
    require_separation_of_duties,
)


def _break_glass(*, notified: bool = True, same_subject: bool = False) -> BreakGlassContext:
    return BreakGlassContext(
        break_glass_id=uid(7100),
        activated_by=actor(1),
        independent_reviewer=actor(1 if same_subject else 2),
        activated_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        evidence=evidence(),
        notification_sent=notified,
    )


# ---------------------------------------------------------------------------
# Scoped grants
# ---------------------------------------------------------------------------


def test_migration_execution_requires_a_scoped_grant() -> None:
    """`P13-SEC-002`."""
    with pytest.raises(PrivilegeAuthorityMissingError, match="scoped PACK-12 privileged grant"):
        require_scoped_grant(
            None, operation=DataPlaneOperation.MIGRATION_EXECUTION, scope=scope(), now=NOW
        )


def test_a_grant_for_another_operation_does_not_transfer() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="never widen"):
        require_scoped_grant(
            grant("event_replay"),
            operation=DataPlaneOperation.MIGRATION_EXECUTION,
            scope=scope(),
            now=NOW,
        )


def test_an_expired_grant_is_not_authority() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="lapsed"):
        require_scoped_grant(
            grant("migration_execution"),
            operation=DataPlaneOperation.MIGRATION_EXECUTION,
            scope=scope(),
            now=NOW + timedelta(hours=3),
        )


def test_a_grant_for_another_scope_is_refused() -> None:
    other = OrganizationScopeReference(
        organization_id=uid(9999), scope_kind=OrganizationScopeKind.BUND
    )
    with pytest.raises(PrivilegeAuthorityMissingError, match="scoped to organization"):
        require_scoped_grant(
            grant("migration_execution"),
            operation=DataPlaneOperation.MIGRATION_EXECUTION,
            scope=other,
            now=NOW,
        )


def test_a_matching_unexpired_scoped_grant_is_accepted() -> None:
    checked = require_scoped_grant(
        grant("migration_execution"),
        operation=DataPlaneOperation.MIGRATION_EXECUTION,
        scope=scope(),
        now=NOW,
    )
    assert checked.operation == "migration_execution"


# ---------------------------------------------------------------------------
# Separation of duties
# ---------------------------------------------------------------------------


def test_destructive_migration_and_schema_activation_are_the_separated_ops() -> None:
    """`P13-SEC-004`."""
    assert (
        frozenset({DataPlaneOperation.DESTRUCTIVE_MIGRATION, DataPlaneOperation.SCHEMA_ACTIVATION})
        == SEPARATION_OF_DUTIES_OPERATIONS
    )


def test_one_subject_cannot_both_propose_and_approve_a_destructive_migration() -> None:
    with pytest.raises(MigrationSeparationOfDutiesMissingError):
        require_separation_of_duties(
            operation=DataPlaneOperation.DESTRUCTIVE_MIGRATION,
            proposer=actor(1),
            approver=actor(1),
        )


def test_two_subjects_satisfy_separation_of_duties() -> None:
    require_separation_of_duties(
        operation=DataPlaneOperation.SCHEMA_ACTIVATION, proposer=actor(1), approver=actor(2)
    )


def test_a_non_separated_operation_needs_no_second_subject() -> None:
    require_separation_of_duties(
        operation=DataPlaneOperation.PROJECTION_REBUILD, proposer=actor(1), approver=actor(1)
    )


# ---------------------------------------------------------------------------
# Operator privilege
# ---------------------------------------------------------------------------


def test_cluster_privilege_is_not_domain_content_authority() -> None:
    """`P13-SEC-001`: holding the highest role on the cluster confers no
    right to read a membership record."""
    with pytest.raises(OperatorPrivilegeInsufficientError, match="not domain-content authority"):
        require_domain_content_authority(
            holds_cluster_privilege=True,
            holds_domain_content_authority=False,
            domain=OWNER_DOMAIN,
        )


def test_no_authority_at_all_is_also_refused() -> None:
    with pytest.raises(OperatorPrivilegeInsufficientError, match="no domain-content authority"):
        require_domain_content_authority(
            holds_cluster_privilege=False,
            holds_domain_content_authority=False,
            domain=OWNER_DOMAIN,
        )


def test_genuine_domain_content_authority_passes() -> None:
    require_domain_content_authority(
        holds_cluster_privilege=False,
        holds_domain_content_authority=True,
        domain=OWNER_DOMAIN,
    )


def test_no_universal_database_administrator_exists() -> None:
    """`P13-SEC-005`, FIR-INV-014: the role that operates the cluster and
    the role that may read a domain's content are different roles."""
    forbidden = frozenset({DataPlaneRole.CLUSTER_OPERATOR, DataPlaneRole.DOMAIN_CONTENT_READER})
    assert forbidden in INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS
    with pytest.raises(OperatorPrivilegeInsufficientError):
        reject_incompatible_roles(forbidden, subject=actor())


def test_a_migration_executor_may_not_also_be_the_schema_steward() -> None:
    with pytest.raises(OperatorPrivilegeInsufficientError):
        reject_incompatible_roles(
            frozenset({DataPlaneRole.MIGRATION_EXECUTOR, DataPlaneRole.SCHEMA_STEWARD}),
            subject=actor(),
        )


def test_a_permitted_role_combination_passes() -> None:
    reject_incompatible_roles(
        frozenset({DataPlaneRole.MIGRATION_EXECUTOR, DataPlaneRole.DOMAIN_CONTENT_READER}),
        subject=actor(),
    )


# ---------------------------------------------------------------------------
# Direct SQL
# ---------------------------------------------------------------------------


def test_ad_hoc_sql_is_refused_by_name() -> None:
    """`P13-MIG-011`, `P13-SEC-003`: there is no manual, undocumented
    production SQL."""
    with pytest.raises(ManualSqlProhibitedError):
        require_governed_sql_context(
            SqlExecutionContext.AD_HOC,
            grant=None,
            break_glass=None,
            scope=scope(),
            now=NOW,
        )


def test_governed_migration_sql_requires_its_grant() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError):
        require_governed_sql_context(
            SqlExecutionContext.GOVERNED_MIGRATION,
            grant=None,
            break_glass=None,
            scope=scope(),
            now=NOW,
        )


def test_governed_migration_sql_with_a_direct_sql_grant_is_admitted() -> None:
    require_governed_sql_context(
        SqlExecutionContext.GOVERNED_MIGRATION,
        grant=grant("direct_sql"),
        break_glass=None,
        scope=scope(),
        now=NOW,
    )


def test_emergency_sql_requires_an_activated_break_glass_context() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="break-glass"):
        require_governed_sql_context(
            SqlExecutionContext.BREAK_GLASS_EMERGENCY,
            grant=None,
            break_glass=None,
            scope=scope(),
            now=NOW,
        )


def test_an_expired_break_glass_context_is_refused() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="expired"):
        require_governed_sql_context(
            SqlExecutionContext.BREAK_GLASS_EMERGENCY,
            grant=None,
            break_glass=_break_glass(),
            scope=scope(),
            now=NOW + timedelta(hours=2),
        )


def test_a_live_break_glass_context_admits_emergency_sql() -> None:
    require_governed_sql_context(
        SqlExecutionContext.BREAK_GLASS_EMERGENCY,
        grant=None,
        break_glass=_break_glass(),
        scope=scope(),
        now=NOW,
    )


# ---------------------------------------------------------------------------
# Break-glass adds obligations
# ---------------------------------------------------------------------------


def test_break_glass_disables_no_audit() -> None:
    """`P13-SEC-006`, FIR-INV-006."""
    assert _break_glass().disables_audit is False


def test_break_glass_has_no_field_that_could_disable_an_obligation() -> None:
    fields = _break_glass().__slots__
    for forbidden in ("skip_audit", "bypass_invariant", "suppress_notification", "disable_audit"):
        assert forbidden not in fields


def test_break_glass_requires_an_independent_reviewer() -> None:
    with pytest.raises(MigrationSeparationOfDutiesMissingError):
        _break_glass(same_subject=True)


def test_break_glass_requires_notification() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="friendlier name"):
        _break_glass(notified=False)


def test_break_glass_expires() -> None:
    with pytest.raises(ValueError, match="expires after"):
        BreakGlassContext(
            break_glass_id=uid(7100),
            activated_by=actor(1),
            independent_reviewer=actor(2),
            activated_at=NOW,
            expires_at=NOW,
            evidence=evidence(),
            notification_sent=True,
        )


# ---------------------------------------------------------------------------
# Privileged action records
# ---------------------------------------------------------------------------


def test_a_privileged_action_is_reason_coded() -> None:
    with pytest.raises(PrivilegeAuthorityMissingError, match="free text is not a reason"):
        PrivilegedActionRecord(
            action_id=uid(7200),
            operation=DataPlaneOperation.MIGRATION_EXECUTION,
            actor=actor(),
            scope=scope(),
            grant_id=uid(7001),
            reason_code="",
            performed_at=NOW,
            evidence=evidence(),
        )


def test_a_privileged_action_record_carries_no_query_text() -> None:
    """`P13-OBS-002`: an action record is telemetry that outlives the
    action."""
    record = PrivilegedActionRecord(
        action_id=uid(7200),
        operation=DataPlaneOperation.MIGRATION_EXECUTION,
        actor=actor(),
        scope=scope(),
        grant_id=uid(7001),
        reason_code="MIGRATION_STARTED_RECORDED",
        performed_at=NOW,
        evidence=evidence(),
    )
    for forbidden in ("query_text", "sql", "statements", "affected_rows"):
        assert forbidden not in record.__slots__


def test_a_grant_confers_nothing_beyond_its_operation() -> None:
    assert "domain_content_read" in GRANT_CONFERS_NOTHING_ELSE
    assert "export" in GRANT_CONFERS_NOTHING_ELSE
    assert "audit_mutation" in GRANT_CONFERS_NOTHING_ELSE
    assert "voting_material" in GRANT_CONFERS_NOTHING_ELSE
