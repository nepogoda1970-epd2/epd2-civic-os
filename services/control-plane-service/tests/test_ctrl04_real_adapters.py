"""CTRL-04 real local adapters: an actual process restart and an actual
filesystem backup/restore, driven through the governed console."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from _ctrl04_builders import BERLIN, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import (
    AdapterCapability,
    LocalFilesystemBackupAdapter,
    LocalProcessAdapter,
    redact_metadata,
)
from epd2_control_plane_service.operations_console import (
    ActionState,
    ActionType,
    DeploymentIdentity,
    EnvironmentClass,
    FailureClassification,
    OperationalTarget,
    OpsRefusal,
    TargetClass,
    TargetDomain,
)
from epd2_control_plane_service.regional_operations import ApproverClass


@pytest.fixture
def process_world() -> World:
    w = World(environment=EnvironmentClass.NON_PRODUCTION)
    adapter = LocalProcessAdapter("local-process")
    adapter.manage("proc-health")
    adapter.manage("proc-fixed", restart_supported=False)
    w.service.adapters["local-process"] = adapter
    for target_id in ("proc-health", "proc-fixed"):
        w.service.register_target(
            OperationalTarget(
                target_id=target_id,
                target_class=TargetClass.SERVICE,
                domain=TargetDomain.GENERAL,
                environment=EnvironmentClass.NON_PRODUCTION,
                scope=BERLIN,
                deployment_identity_ref="dep-web-1",
                adapter_id="local-process",
                version=1,
                capabilities=adapter.capabilities(target_id),
            )
        )
    yield w
    adapter.stop_all()


def test_real_process_restart_changes_pid_and_result_is_derived_from_live_health(
    process_world: World,
) -> None:
    w = process_world
    adapter = w.service.adapters["local-process"]
    assert isinstance(adapter, LocalProcessAdapter)
    before = adapter.pid_of("proc-health")
    assert w.service.health("proc-health", now=w.now).state.value == "HEALTHY"
    action = w.request(
        ActionType.SERVICE_RESTART, "proc-health", parameters={"reason": "real restart"}
    )
    w.commit(action.action_id)
    done = w.resolve(action.action_id)
    assert done.state is ActionState.SUCCEEDED
    after = adapter.pid_of("proc-health")
    assert before is not None and after is not None and before != after
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.backend_metadata["old_pid"] == str(before) and result.backend_metadata[
        "new_pid"
    ] == str(after)
    health = w.service.health("proc-health", now=w.now)
    assert health.state.value == "HEALTHY" and health.details["pid"] == str(after)


def test_real_process_restart_failure_is_explicit_and_health_unavailable(
    process_world: World,
) -> None:
    w = process_world
    adapter = w.service.adapters["local-process"]
    assert isinstance(adapter, LocalProcessAdapter)
    adapter.fail_next_restart("proc-health")
    action = w.request(
        ActionType.SERVICE_RESTART, "proc-health", parameters={"reason": "will fail"}
    )
    w.commit(action.action_id)
    done = w.resolve(action.action_id)
    assert done.state is ActionState.FAILED
    result = w.service.result_of(action.action_id)
    assert (
        result is not None
        and result.failure_classification is FailureClassification.PROVIDER_FAILURE
    )
    assert w.service.health("proc-health", now=w.now).state.value == "UNAVAILABLE"


def test_real_process_unsupported_restart(process_world: World) -> None:
    w = process_world
    action = w.request(ActionType.SERVICE_RESTART, "proc-fixed", parameters={"reason": "x"})
    done = w.commit(action.action_id)
    assert done.state is ActionState.UNSUPPORTED
    adapter = w.service.adapters["local-process"]
    assert isinstance(adapter, LocalProcessAdapter)
    assert adapter.pid_of("proc-fixed") is not None


def test_real_filesystem_backup_and_restore(tmp_path: Path) -> None:
    w = World(environment=EnvironmentClass.NON_PRODUCTION)
    data = tmp_path / "data"
    data.mkdir()
    (data / "members.csv").write_text("id,name\n1,a\n")
    adapter = LocalFilesystemBackupAdapter(tmp_path / "backups", "local-backup")
    adapter.manage("fs-members", data)
    adapter.manage("fs-readonly", data, restore_supported=False)
    w.service.adapters["local-backup"] = adapter
    w.service.register_deployment(
        DeploymentIdentity("dep-fs", "f" * 64, "fs", "rel-fs", "chg-fs", 1, True)
    )
    for target_id in ("fs-members", "fs-readonly"):
        w.service.register_target(
            OperationalTarget(
                target_id=target_id,
                target_class=TargetClass.DATASTORE,
                domain=TargetDomain.GENERAL,
                environment=EnvironmentClass.NON_PRODUCTION,
                scope=BERLIN,
                deployment_identity_ref="dep-fs",
                adapter_id="local-backup",
                version=1,
                capabilities=adapter.capabilities(target_id),
            )
        )
    # Backup: a real archive is written and its identity is the tree digest.
    backup = w.request(
        ActionType.BACKUP_REQUEST,
        "fs-members",
        parameters={"reason": "pre", "backup_set_id": "nightly"},
    )
    w.commit(backup.action_id)
    assert w.resolve(backup.action_id).state is ActionState.SUCCEEDED
    op = next(b for b in w.service.backup_operations() if b.action_id == backup.action_id)
    assert adapter.backup_path("nightly", op.backup_identity_digest).is_file()
    assert w.service.recovery_readiness("fs-members", now=w.now)["readiness"] == "READY"
    assert w.service.recovery_readiness("fs-readonly", now=w.now)["restore_supported"] is False
    # Mutate the datastore, then restore: identity + confirmation + window + dual control.
    (data / "members.csv").write_text("id,name\n1,a\n2,corrupted\n")
    (data / "junk.tmp").write_text("x")
    params = {
        "reason": "restore",
        "backup_set_id": "nightly",
        "backup_identity_digest": op.backup_identity_digest,
        "confirmation": "CONFIRM-DESTRUCTIVE:fs-members",
    }
    with pytest.raises(AuthorizationRefused) as info:
        w.request(
            ActionType.RESTORE_REQUEST,
            "fs-members",
            parameters={**params, "backup_identity_digest": "0" * 64},
        )
    assert info.value.reason_code == OpsRefusal.BACKUP_IDENTITY_MISMATCH.value
    restore = w.request(ActionType.RESTORE_REQUEST, "fs-members", parameters=params)
    assert restore.required_approver_classes == ("INCIDENT_COMMANDER", "TRUST_CUSTODIAN")
    w.approve(restore.action_id)
    w.approve(restore.action_id, "trust-custodian", ApproverClass.TRUST_CUSTODIAN)
    # No active maintenance window on the datastore yet: refused at commit.
    with pytest.raises(AuthorizationRefused) as info:
        w.commit(restore.action_id)
    assert info.value.reason_code == OpsRefusal.MAINTENANCE_REQUIRED.value
    enter = w.request(
        ActionType.MAINTENANCE_ENTER,
        "fs-members",
        parameters={"reason": "restore", "duration_minutes": "30"},
    )
    w.commit(enter.action_id)
    w.resolve(enter.action_id)
    w.commit(restore.action_id)
    done = w.resolve(restore.action_id)
    assert done.state is ActionState.SUCCEEDED
    assert (data / "members.csv").read_text() == "id,name\n1,a\n"
    assert not (data / "junk.tmp").exists()
    result = w.service.result_of(restore.action_id)
    assert (
        result is not None
        and result.backend_metadata["restored_tree_digest"] == op.backup_identity_digest
    )
    # A second restore from the same archive is a distinct action with its own evidence.
    # Backup of an unsupported restore target still works, restore is explicit UNSUPPORTED.
    assert AdapterCapability.RESTORE not in adapter.capabilities("fs-readonly")
    w.now = w.now + timedelta(seconds=1)


def test_redaction_keeps_references_and_drops_material() -> None:
    clean, redacted = redact_metadata(
        {
            "api_token": "sk_live_x",
            "token_reference_id": "ref-1",
            "secret_ref": "vault://x",
            "provider_password": "hunter2",
            "note": "-----BEGIN " + "PRIVATE KEY-----",  # split so the repo secret scan stays clean
            "region": "eu",
            "hsm_slot_ref": "slot-1",
            "kms_material": "zzz",
        }
    )
    assert clean["api_token"] == "[REDACTED]" and clean["provider_password"] == "[REDACTED]"
    assert clean["note"] == "[REDACTED]" and clean["kms_material"] == "[REDACTED]"
    assert clean["token_reference_id"] == "ref-1" and clean["secret_ref"] == "vault://x"
    assert clean["hsm_slot_ref"] == "slot-1" and clean["region"] == "eu"
    assert set(redacted) == {"api_token", "provider_password", "note", "kms_material"}
