"""CTRL-04 action lifecycle, results and typed states."""

from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl04_builders import ARTIFACT_B, ARTIFACT_UNATTESTED, ARTIFACT_UNVERIFIED, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import AdapterCapability, BackendState
from epd2_control_plane_service.operations_console import (
    ACTION_CATALOGUE,
    ActionState,
    ActionType,
    ApprovalState,
    EnvironmentClass,
    ExecutionState,
    FailureClassification,
    ImpactClass,
    MaintenanceWindowState,
    OpsRefusal,
    ResultState,
    ReviewState,
)
from epd2_control_plane_service.regional_operations import ApproverClass


def refused(fn, code: OpsRefusal | str):  # type: ignore[no-untyped-def]
    with pytest.raises(AuthorizationRefused) as info:
        fn()
    expected = code.value if isinstance(code, OpsRefusal) else code
    assert str(info.value.reason_code) == expected, (info.value.reason_code, str(info.value))
    return info.value


def test_full_lifecycle_states_are_typed_and_terminal() -> None:
    w = World()
    action = w.request()
    assert action.state is ActionState.AWAITING_APPROVAL
    assert action.approval_state is ApprovalState.PENDING
    assert action.execution_state is ExecutionState.NOT_DISPATCHED
    assert action.result_state is ResultState.PENDING
    assert action.impact is ImpactClass.MEDIUM
    approved = w.approve(action.action_id)
    assert approved.state is ActionState.APPROVED
    assert approved.approval_state is ApprovalState.GRANTED
    executing = w.commit(action.action_id)
    assert executing.state is ActionState.EXECUTING
    assert executing.execution_state is ExecutionState.DISPATCHED
    # A dispatch acknowledgement is never success.
    assert executing.result_state is ResultState.PENDING
    assert executing.backend_operation_ref is not None
    done = w.resolve(action.action_id)
    assert done.state is ActionState.SUCCEEDED
    assert done.execution_state is ExecutionState.COMPLETED
    assert done.result_state is ResultState.SUCCEEDED
    result = w.service.result_of(action.action_id)
    assert result is not None and result.failure_classification is FailureClassification.NONE
    reviewed = w.review(action.action_id)
    assert reviewed.review_state is ReviewState.REVIEWED
    assert reviewed.reviewed_by == "reviewer"
    assert w.adapter.dispatch_count == 1
    assert w.adapter.dispatch_log[-1].target_id == "svc-web"
    assert w.adapter.dispatch_log[-1].execution_id == done.execution_id


def test_non_production_restart_needs_no_approval_but_still_reauthorizes() -> None:
    w = World(environment=EnvironmentClass.NON_PRODUCTION)
    action = w.request()
    assert action.state is ActionState.APPROVED
    assert action.approval_state is ApprovalState.NOT_REQUIRED
    assert action.required_approver_classes == ()
    refused(lambda: w.approve(action.action_id), OpsRefusal.APPROVAL_NOT_REQUIRED)
    w.commit(action.action_id)
    assert w.resolve(action.action_id).state is ActionState.SUCCEEDED
    decisions = w.service.decisions_of(action.action_id)
    assert [d.stage for d in decisions] == ["REQUEST", "APPROVE", "COMMIT"]
    assert [d.allowed for d in decisions] == [True, False, True]


def test_dispatch_ack_is_not_success_even_when_backend_is_slow() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=2)
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    first = w.resolve(action.action_id)
    assert first.state is ActionState.EXECUTING and first.execution_state is ExecutionState.RUNNING
    assert first.result_state is ResultState.PENDING
    second = w.resolve(action.action_id)
    assert second.state is ActionState.EXECUTING
    third = w.resolve(action.action_id)
    assert third.state is ActionState.SUCCEEDED


def test_provider_failure_is_explicit_failed_with_evidence() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.FAILED)
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    done = w.resolve(action.action_id)
    assert done.state is ActionState.FAILED
    assert done.result_state is ResultState.FAILED
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.failure_classification is FailureClassification.PROVIDER_FAILURE
    records = [r for r in w.service.journal.records() if r.correlation_ref == action.action_id]
    assert records[-1].result == "FAILED"
    assert records[-1].attributes["failure_classification"] == "PROVIDER_FAILURE"


def test_dispatch_refusal_is_failed_not_swallowed() -> None:
    w = World()
    w.adapter.refuse_dispatch.add("svc-web")
    action = w.request()
    w.approve(action.action_id)
    done = w.commit(action.action_id)
    assert done.state is ActionState.FAILED
    result = w.service.result_of(action.action_id)
    assert (
        result is not None
        and result.failure_classification is FailureClassification.PROVIDER_FAILURE
    )
    assert "refused" in result.detail


def test_partial_failure_is_represented_explicitly() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.PARTIAL)
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    done = w.resolve(action.action_id)
    assert done.state is ActionState.PARTIAL_FAILURE
    assert done.result_state is ResultState.PARTIAL_FAILURE
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.failure_classification is FailureClassification.PARTIAL_PROVIDER_FAILURE


def test_unsupported_capability_is_explicit_unsupported_state() -> None:
    w = World()
    # svc-legacy's backend supports MAINTENANCE only.
    action = w.request(ActionType.SERVICE_RESTART, "svc-legacy")
    w.approve(action.action_id)
    done = w.commit(action.action_id)
    assert done.state is ActionState.UNSUPPORTED
    assert done.result_state is ResultState.UNSUPPORTED
    assert done.execution_state is ExecutionState.UNSUPPORTED
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.failure_classification is FailureClassification.UNSUPPORTED_CAPABILITY
    assert w.adapter.dispatch_count == 0


def test_runtime_unsupported_report_maps_to_unsupported() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.UNSUPPORTED)
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    assert w.resolve(action.action_id).state is ActionState.UNSUPPORTED


def test_adapter_unavailable_at_dispatch_is_failed() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.adapter.available = False
    done = w.commit(action.action_id)
    assert done.state is ActionState.FAILED
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.failure_classification is FailureClassification.ADAPTER_UNAVAILABLE


def test_execution_timeout_is_terminal_failure() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=100)
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    w.now = w.now + timedelta(minutes=31)
    done = w.resolve(action.action_id)
    assert done.state is ActionState.FAILED
    assert done.execution_state is ExecutionState.TIMED_OUT
    result = w.service.result_of(action.action_id)
    assert result is not None and result.failure_classification is FailureClassification.TIMEOUT


def test_cancellation_and_expiry_are_explicit_terminal_states() -> None:
    w = World()
    action = w.request()
    w.tick()
    cancelled = w.service.cancel(
        action_id=action.action_id, actor_ref="requester", session_id="sess-requester", now=w.now
    )
    assert cancelled.state is ActionState.CANCELLED
    assert cancelled.result_state is ResultState.CANCELLED
    records = [r for r in w.service.journal.records() if r.correlation_ref == action.action_id]
    assert records[-1].result == "CANCELLED"
    refused(lambda: w.commit(action.action_id), OpsRefusal.DUPLICATE_EXECUTION)
    other = w.request(idempotency_key="k-expire")
    w.now = w.now + timedelta(hours=5)
    assert w.service.expire_due(now=w.now) == (other.action_id,)
    assert w.service.action(other.action_id).state is ActionState.EXPIRED
    assert w.service.action(other.action_id).result_state is ResultState.EXPIRED


def test_expired_request_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.now = w.now + timedelta(hours=5)
    refused(lambda: w.commit(action.action_id), OpsRefusal.REQUEST_EXPIRED)
    assert w.service.action(action.action_id).state is ActionState.EXPIRED


def test_only_requester_cancels_and_not_during_execution() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=3)
    action = w.request()
    w.tick()
    refused(
        lambda: w.service.cancel(
            action_id=action.action_id, actor_ref="executor", session_id="sess-executor", now=w.now
        ),
        OpsRefusal.WRONG_STATE,
    )
    w.approve(action.action_id)
    w.commit(action.action_id)
    w.tick()
    refused(
        lambda: w.service.cancel(
            action_id=action.action_id,
            actor_ref="requester",
            session_id="sess-requester",
            now=w.now,
        ),
        OpsRefusal.WRONG_STATE,
    )


def test_idempotent_request_returns_same_action_and_conflict_is_refused() -> None:
    w = World()
    first = w.request(idempotency_key="idem-1")
    again = w.request(idempotency_key="idem-1")
    assert again.action_id == first.action_id
    assert len(w.service.actions()) == 1
    refused(
        lambda: w.request(idempotency_key="idem-1", parameters={"reason": "different"}),
        OpsRefusal.IDEMPOTENCY_CONFLICT,
    )
    assert len(w.service.actions()) == 1


def test_duplicate_execution_prevented() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    refused(lambda: w.commit(action.action_id), OpsRefusal.DUPLICATE_EXECUTION)
    w.resolve(action.action_id)
    refused(lambda: w.commit(action.action_id), OpsRefusal.DUPLICATE_EXECUTION)
    assert w.adapter.dispatch_count == 1


def test_conflicting_concurrent_execution_on_same_target_refused() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=5)
    first = w.request(idempotency_key="c1")
    second = w.request(idempotency_key="c2", principal="requester-2")
    w.approve(first.action_id)
    w.approve(second.action_id)
    w.commit(first.action_id)
    refused(lambda: w.commit(second.action_id), OpsRefusal.CONFLICTING_EXECUTION)
    assert w.adapter.dispatch_count == 1
    for _ in range(6):
        w.resolve(first.action_id)
    assert w.service.action(first.action_id).state is ActionState.SUCCEEDED
    w.commit(second.action_id)
    assert w.adapter.dispatch_count == 2


def test_adapter_replay_of_execution_id_is_refused() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.commit(action.action_id)
    request = w.adapter.dispatch_log[-1]
    ack = w.adapter.dispatch(request)
    assert not ack.accepted and ack.duplicate


def test_rollback_only_to_verified_allowed_artifact() -> None:
    w = World()
    refused(
        lambda: w.request(
            ActionType.DEPLOYMENT_ROLLBACK,
            parameters={"reason": "bad release", "target_artifact_digest": ARTIFACT_UNVERIFIED},
        ),
        OpsRefusal.UNVERIFIED_ARTIFACT,
    )
    # Attested by nothing in CTRL-03 even though the deployment record says verified.
    refused(
        lambda: w.request(
            ActionType.DEPLOYMENT_ROLLBACK,
            parameters={"reason": "bad release", "target_artifact_digest": ARTIFACT_UNATTESTED},
        ),
        OpsRefusal.UNVERIFIED_ARTIFACT,
    )
    action = w.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "bad release", "target_artifact_digest": ARTIFACT_B},
        principal="req-exec",
    )
    assert action.required_approver_classes == ("INCIDENT_COMMANDER", "SECURITY")
    assert action.impact is ImpactClass.HIGH
    w.approve(action.action_id)
    assert w.service.action(action.action_id).state is ActionState.AWAITING_APPROVAL
    w.approve(action.action_id, "security-officer", ApproverClass.SECURITY)
    assert w.service.action(action.action_id).state is ActionState.APPROVED
    refused(lambda: w.commit(action.action_id, principal="req-exec"), OpsRefusal.REQUESTER_EXECUTES)
    w.commit(action.action_id)
    assert w.resolve(action.action_id).state is ActionState.SUCCEEDED
    assert w.adapter.dispatch_log[-1].parameters["target_artifact_digest"] == ARTIFACT_B


def test_rollback_refused_when_trust_retracted_between_request_and_commit() -> None:
    w = World()
    action = w.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "bad release", "target_artifact_digest": ARTIFACT_B},
    )
    w.approve(action.action_id)
    w.approve(action.action_id, "security-officer", ApproverClass.SECURITY)
    w.ctrl03.retract(ARTIFACT_B)
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_CTRL03_TRUST)


def test_maintenance_window_lifecycle_and_expiry() -> None:
    w = World()
    refused(
        lambda: w.request(
            ActionType.MAINTENANCE_ENTER, parameters={"reason": "x", "duration_minutes": "600"}
        ),
        OpsRefusal.MAINTENANCE_WINDOW_INVALID,
    )
    window_id = w.active_window("svc-web", minutes=30)
    assert window_id is not None
    window = {x.window_id: x for x in w.service.maintenance_windows()}[window_id]
    assert window.state is MaintenanceWindowState.ACTIVE and window.is_active_at(w.now)
    w.now = w.now + timedelta(minutes=31)
    assert not window.is_active_at(w.now)
    w.service.expire_due(now=w.now)
    window = {x.window_id: x for x in w.service.maintenance_windows()}[window_id]
    assert window.state is MaintenanceWindowState.EXPIRED
    exit_action = w.request(
        ActionType.MAINTENANCE_EXIT,
        "svc-web",
        parameters={"reason": "done", "window_id": window_id},
    )
    assert exit_action.state is ActionState.APPROVED  # LOW impact: no approval
    w.commit(exit_action.action_id)
    w.resolve(exit_action.action_id)
    window = {x.window_id: x for x in w.service.maintenance_windows()}[window_id]
    assert window.state is MaintenanceWindowState.CLOSED
    assert window.closed_by_action_id == exit_action.action_id


def test_backup_then_restore_guarded_by_identity_confirmation_window_and_dual_control() -> None:
    w = World()
    backup = w.completed_backup()
    assert backup.backup_identity_digest
    base = {
        "reason": "restore",
        "backup_set_id": "set-1",
        "backup_identity_digest": backup.backup_identity_digest,
    }
    refused(
        lambda: w.request(ActionType.RESTORE_REQUEST, "db-members", parameters=base),
        OpsRefusal.CONFIRMATION_MISSING,
    )
    refused(
        lambda: w.request(
            ActionType.RESTORE_REQUEST,
            "db-members",
            parameters={**base, "confirmation": "CONFIRM-DESTRUCTIVE:db-archive"},
        ),
        OpsRefusal.CONFIRMATION_MISSING,
    )
    confirmed = {**base, "confirmation": "CONFIRM-DESTRUCTIVE:db-members"}
    refused(
        lambda: w.request(
            ActionType.RESTORE_REQUEST,
            "db-members",
            parameters={**confirmed, "backup_identity_digest": "0" * 64},
        ),
        OpsRefusal.BACKUP_IDENTITY_MISMATCH,
    )
    refused(
        lambda: w.request(
            ActionType.RESTORE_REQUEST,
            "db-archive",
            parameters={**confirmed, "confirmation": "CONFIRM-DESTRUCTIVE:db-archive"},
        ),
        OpsRefusal.BACKUP_IDENTITY_MISMATCH,
    )
    action = w.request(
        ActionType.RESTORE_REQUEST, "db-members", parameters=confirmed, principal="req-exec"
    )
    assert action.impact is ImpactClass.DESTRUCTIVE
    assert action.required_approver_classes == ("INCIDENT_COMMANDER", "SECURITY", "TRUST_CUSTODIAN")
    w.approve(action.action_id)
    w.approve(action.action_id, "security-officer", ApproverClass.SECURITY)
    refused(lambda: w.commit(action.action_id), OpsRefusal.QUORUM_NOT_MET)
    w.approve(action.action_id, "trust-custodian", ApproverClass.TRUST_CUSTODIAN)
    # No active maintenance window on the datastore yet.
    refused(lambda: w.commit(action.action_id), OpsRefusal.MAINTENANCE_REQUIRED)
    w.active_window("db-members", minutes=60)
    refused(lambda: w.commit(action.action_id, principal="req-exec"), OpsRefusal.REQUESTER_EXECUTES)
    w.commit(action.action_id)
    assert w.resolve(action.action_id).state is ActionState.SUCCEEDED
    ops = [b for b in w.service.backup_operations() if b.kind == "RESTORE"]
    assert ops and ops[-1].backup_identity_digest == backup.backup_identity_digest


def test_restore_refused_when_maintenance_window_expired() -> None:
    w = World()
    backup = w.completed_backup()
    w.active_window("db-members", minutes=10)
    action = w.request(
        ActionType.RESTORE_REQUEST,
        "db-members",
        parameters={
            "reason": "restore",
            "backup_set_id": "set-1",
            "backup_identity_digest": backup.backup_identity_digest,
            "confirmation": "CONFIRM-DESTRUCTIVE:db-members",
        },
    )
    for principal, cls in (
        ("incident-commander", ApproverClass.INCIDENT_COMMANDER),
        ("security-officer", ApproverClass.SECURITY),
        ("trust-custodian", ApproverClass.TRUST_CUSTODIAN),
    ):
        w.approve(action.action_id, principal, cls)
    w.now = w.now + timedelta(minutes=11)
    refused(lambda: w.commit(action.action_id), OpsRefusal.MAINTENANCE_REQUIRED)


def test_restore_unsupported_backend_is_explicit() -> None:
    w = World()
    backup = w.completed_backup("db-archive", "set-a")
    w.active_window("db-archive", minutes=60) if False else None  # db-archive: no maintenance cap
    action = w.request(
        ActionType.RESTORE_REQUEST,
        "db-archive",
        parameters={
            "reason": "restore",
            "backup_set_id": "set-a",
            "backup_identity_digest": backup.backup_identity_digest,
            "confirmation": "CONFIRM-DESTRUCTIVE:db-archive",
        },
    )
    assert action.state is ActionState.AWAITING_APPROVAL
    readiness = w.service.recovery_readiness("db-archive", now=w.now)
    assert readiness["restore_supported"] is False and readiness["readiness"] == "NOT_READY"
    assert w.service.recovery_readiness("db-members", now=w.now)["readiness"] == "NOT_READY"
    w.completed_backup("db-members")
    assert w.service.recovery_readiness("db-members", now=w.now)["readiness"] == "READY"


def test_job_queue_pause_and_resume() -> None:
    w = World()
    snap = w.service.job_queue("queue-mail", now=w.now)
    assert snap.state == "RUNNING" and snap.depth == 12
    pause = w.request(ActionType.JOB_QUEUE_PAUSE, "queue-mail", parameters={"reason": "drain"})
    w.approve(pause.action_id)
    w.commit(pause.action_id)
    assert w.resolve(pause.action_id).state is ActionState.SUCCEEDED
    assert w.service.job_queue("queue-mail", now=w.now).state == "PAUSED"
    resume = w.request(ActionType.JOB_QUEUE_RESUME, "queue-mail", parameters={"reason": "ok"})
    assert resume.state is ActionState.APPROVED
    w.commit(resume.action_id)
    w.resolve(resume.action_id)
    assert w.service.job_queue("queue-mail", now=w.now).state == "RUNNING"
    refused(
        lambda: w.request(ActionType.JOB_QUEUE_PAUSE, "svc-web", parameters={"reason": "x"}),
        OpsRefusal.PARAMETER_INVALID,
    )


def test_incident_linkage_is_a_governed_mutation_with_evidence() -> None:
    w = World()
    restart = w.full_restart()
    link = w.request(
        ActionType.INCIDENT_LINK,
        "svc-web",
        parameters={"incident_id": "INC-1", "linked_action_id": restart.action_id},
    )
    assert link.state is ActionState.APPROVED
    done = w.commit(link.action_id)
    assert done.state is ActionState.SUCCEEDED
    incident = {i.incident_id: i for i in w.service.incidents()}["INC-1"]
    assert restart.action_id in incident.linked_action_ids
    assert w.service.action(restart.action_id).incident_ref == "INC-1"
    assert any(r.correlation_ref == link.action_id for r in w.service.journal.records())
    refused(
        lambda: w.request(
            ActionType.INCIDENT_LINK,
            "svc-web",
            parameters={"incident_id": "INC-404", "linked_action_id": restart.action_id},
        ),
        OpsRefusal.NOT_FOUND,
    )


def test_parameters_are_allow_listed_and_bounded() -> None:
    w = World()
    refused(
        lambda: w.request(parameters={"reason": "x", "shell": "rm -rf /"}),
        OpsRefusal.PARAMETER_INVALID,
    )
    refused(lambda: w.request(parameters={"reason": "x" * 600}), OpsRefusal.PARAMETER_INVALID)
    refused(
        lambda: w.request(ActionType.DEPLOYMENT_ROLLBACK, parameters={"reason": "x"}),
        OpsRefusal.PARAMETER_INVALID,
    )
    refused(lambda: w.request(target_id="*"), OpsRefusal.COARSE_TARGET)
    refused(lambda: w.request(target_id="svc-unknown"), OpsRefusal.UNKNOWN_TARGET)


def test_catalogue_invariants() -> None:
    for spec in ACTION_CATALOGUE.values():
        if spec.mutation:
            assert spec.required_right == "OPS.REQUEST"
            assert spec.capability is not None or spec.action_type is ActionType.INCIDENT_LINK
        else:
            assert spec.required_right == "OPS.READ" and spec.capability is None
        if spec.impact in {ImpactClass.HIGH, ImpactClass.DESTRUCTIVE}:
            assert len(spec.approver_classes_production) >= 2, spec.action_type
            assert not spec.requester_may_execute
        if spec.impact is ImpactClass.DESTRUCTIVE:
            assert spec.destructive_confirmation and spec.requires_maintenance_window
            assert "TRUST_CUSTODIAN" in spec.approver_classes_production
    assert {c for c in AdapterCapability} == {
        s.capability for s in ACTION_CATALOGUE.values() if s.capability is not None
    }


def test_clock_rollback_is_refused() -> None:
    w = World()
    w.request()
    w.now = w.now - timedelta(minutes=5)
    refused(lambda: w.request(idempotency_key="rollback"), OpsRefusal.CLOCK_ROLLBACK)
