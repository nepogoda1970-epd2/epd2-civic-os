from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl02_builders import BERLIN, NOW, activate, service
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import (
    ApproverClass,
    Decision,
    PrivilegeKind,
    WorkflowState,
)


def _active_grant(kind: PrivilegeKind = PrivilegeKind.JIT):
    svc = service()
    svc.create_privilege_request(
        request_id="priv-1",
        kind=kind,
        principal_id="operator",
        requester_id="requester",
        scope=BERLIN,
        capabilities=("SERVICE.RESTART",),
        reason="bounded maintenance",
        evidence_refs=("change:1",),
        now=NOW,
        expires_at=NOW + timedelta(minutes=30),
        target_version=1,
        idempotency_key="priv:req",
    )
    svc.approve(
        "priv-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="priv:a1",
    )
    svc.approve(
        "priv-1",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="priv:sec",
    )
    activate(svc, "priv-1")
    grant = svc.materialize_privilege("priv-1", kind=kind, principal_id="operator")
    return svc, grant


def test_jit_exact_target_use_and_evidence() -> None:
    svc, grant = _active_grant()
    used = svc.use_privilege(
        grant.grant_id,
        principal_id="operator",
        capability="SERVICE.RESTART",
        scope=BERLIN,
        now=NOW + timedelta(minutes=4),
        use_ref="use:1",
    )
    assert used.use_refs == ("use:1",)


def test_breakglass_has_strict_expiry() -> None:
    svc, grant = _active_grant(PrivilegeKind.BREAK_GLASS)
    with pytest.raises(AuthorizationRefused) as error:
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(hours=2),
            use_ref="late",
        )
    assert error.value.reason_code == Decision.GRANT_EXPIRED


def test_breakglass_request_cannot_exceed_one_hour() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused):
        svc.create_privilege_request(
            request_id="too-long",
            kind=PrivilegeKind.BREAK_GLASS,
            principal_id="operator",
            requester_id="requester",
            scope=BERLIN,
            capabilities=("SERVICE.RESTART",),
            reason="too long",
            evidence_refs=("incident:1",),
            now=NOW,
            expires_at=NOW + timedelta(hours=2),
            target_version=1,
            idempotency_key="too-long",
        )


def test_jit_cannot_expand_scope_or_target() -> None:
    svc, grant = _active_grant()
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="someone-else",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
            use_ref="wrong-target",
        )

    from _ctrl02_builders import BAVARIA

    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BAVARIA,
            now=NOW + timedelta(minutes=5),
            use_ref="wrong-scope",
        )


def test_approval_does_not_materialize_privilege() -> None:
    svc = service()
    svc.create_privilege_request(
        request_id="priv-pending",
        kind=PrivilegeKind.JIT,
        principal_id="operator",
        requester_id="requester",
        scope=BERLIN,
        capabilities=("SERVICE.RESTART",),
        reason="maintenance",
        evidence_refs=("change:1",),
        now=NOW,
        expires_at=NOW + timedelta(minutes=30),
        target_version=1,
        idempotency_key="priv-pending",
    )
    svc.approve(
        "priv-pending",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="priv-pending:a1",
    )
    svc.approve(
        "priv-pending",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="priv-pending:sec",
    )
    with pytest.raises(AuthorizationRefused):
        svc.materialize_privilege("priv-pending", kind=PrivilegeKind.JIT, principal_id="operator")


def test_active_restriction_overrides_narrow_jit_grant() -> None:
    svc, grant = _active_grant()
    from _ctrl02_builders import approve_twice, request

    request(
        svc,
        request_id="restriction-2",
        targets=("action:SERVICE.RESTART",),
        capabilities=("SERVICE.RESTART",),
    )
    approve_twice(svc, "restriction-2")
    activate(svc, "restriction-2")
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=5),
            use_ref="restricted",
        )


def test_raw_secret_visibility_is_never_implied() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused):
        svc.create_privilege_request(
            request_id="secret",
            kind=PrivilegeKind.BREAK_GLASS,
            principal_id="operator",
            requester_id="requester",
            scope=BERLIN,
            capabilities=("SECRET.RAW_READ",),
            reason="not allowed",
            evidence_refs=("incident:1",),
            now=NOW,
            expires_at=NOW + timedelta(minutes=10),
            target_version=1,
            idempotency_key="secret",
        )


def test_clock_rollback_cannot_revive_expired_grant() -> None:
    svc, grant = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    assert svc.grants[0].state is WorkflowState.EXPIRED
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=5),
            use_ref="rollback",
        )


def test_checkpoint_preserves_terminal_and_evidence_state() -> None:
    svc, _ = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    snapshot = svc.checkpoint()
    assert snapshot["grants"]["jit:priv-1"]["state"] is WorkflowState.EXPIRED
    assert snapshot["events"]
    assert snapshot["events"][-1]["event_hash"]


def test_recovery_does_not_resurrect_expired_grant() -> None:
    svc, grant = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    recovered = type(svc).from_checkpoint(svc.authorities, svc.checkpoint())
    assert recovered.grants[0].state is WorkflowState.EXPIRED
    with pytest.raises(AuthorizationRefused):
        recovered.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(hours=2),
            use_ref="after-restart",
        )


def test_service_credential_control_exposes_no_secret() -> None:
    svc = service()
    ref = svc.service_credential_control(
        credential_id="workload:api",
        operation="EMERGENCY_CONTAIN",
        actor_id="security-operator",
        scope=BERLIN,
        now=NOW,
        evidence_ref="incident:credential-1",
    )
    assert ref.startswith("service-credential:")
    assert "forbidden" not in str(svc.events)
    with pytest.raises(AuthorizationRefused):
        svc.service_credential_control(
            credential_id="workload:api",
            operation="REVOKE",
            actor_id="security-operator",
            scope=BERLIN,
            now=NOW + timedelta(minutes=1),
            evidence_ref="incident:credential-1",
            secret_material="forbidden",
        )


def test_key_trust_operation_is_request_only() -> None:
    svc = service()
    ref = svc.key_trust_change_request(
        request_ref="trust-request:1",
        operation="CONTAIN_COMPROMISE",
        key_reference="keyref:regional-issuer",
        actor_id="trust-requester",
        scope=BERLIN,
        now=NOW,
        evidence_ref="incident:key-1",
    )
    assert ref == "trust-request:1"
    assert svc.events[-1].result == "REQUEST_RECORDED_NOT_EXECUTED"
