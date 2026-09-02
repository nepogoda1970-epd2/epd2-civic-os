from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from _ctrl03_builders import (
    NOW,
    approve_security,
    approve_trust,
    execute,
    object_for,
    request,
    service,
)
from epd2_control_plane_service.credential_lifecycle import (
    CredentialClass,
    LifecycleOperation,
    LifecycleState,
    Refusal,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import ApproverClass


def test_low_impact_revoke_uses_separate_request_approve_execute() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    approved = approve_security(svc)
    assert approved.state is LifecycleState.APPROVED
    updated = execute(svc)
    assert updated.state is LifecycleState.REVOKED
    assert svc.requests[0].executed_by == "custodian"


def test_high_impact_operation_requires_security_and_trust_quorum() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    request(svc, operation=LifecycleOperation.REVOKE)
    first = approve_security(svc)
    assert first.state is LifecycleState.PENDING_ACTIVATION
    second = approve_trust(svc)
    assert second.state is LifecycleState.APPROVED


def test_two_security_approvers_do_not_replace_trust_custodian() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    request(svc)
    approve_security(svc)
    second = svc.approve(
        "request-1",
        approver_id="security-2",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="security-2",
    )
    assert second.state is LifecycleState.PENDING_ACTIVATION


def test_self_approval_duplicate_approval_and_requester_execution_rejected() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.approve(
            "request-1",
            approver_id="requester",
            approver_class=ApproverClass.SECURITY,
            now=NOW + timedelta(minutes=1),
            idempotency_key="self",
        )
    assert error.value.reason_code == Refusal.SELF_APPROVAL
    approve_security(svc)
    with pytest.raises(AuthorizationRefused):
        svc.approve(
            "request-1",
            approver_id="security-1",
            approver_class=ApproverClass.SECURITY,
            now=NOW + timedelta(minutes=2),
            idempotency_key="duplicate",
        )
    with pytest.raises(AuthorizationRefused) as execute_error:
        svc.execute(
            "request-1",
            custodian_id="requester",
            now=NOW + timedelta(minutes=3),
            idempotency_key="self-execute",
        )
    assert execute_error.value.reason_code == Refusal.EXECUTION_SEPARATION


def test_human_credential_revocation_invalidates_dependent_sessions() -> None:
    svc = service()
    human = svc.register(object_for(CredentialClass.HUMAN_CREDENTIAL))
    session = svc.register(object_for(CredentialClass.SESSION, object_id="session:one"))
    assert human.subject_ref == session.subject_ref
    request(svc)
    approve_security(svc)
    execute(svc)
    states = {item.object_id: item.state for item in svc.objects}
    assert states["credential:old"] is LifecycleState.REVOKED
    assert states["session:one"] is LifecycleState.REVOKED


def test_request_and_execution_are_idempotent() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    first = request(svc)
    assert request(svc) == first
    approve_security(svc)
    result = execute(svc)
    assert execute(svc) == result
    assert len([event for event in svc.events if event.result == "COMPLETED"]) == 1


def test_idempotency_key_cannot_be_reused_for_different_intent() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.request_operation(
            request_id="request-2",
            operation=LifecycleOperation.SUSPEND,
            target_id="credential:old",
            requester_id="requester",
            reason="different governed intent",
            evidence_refs=("evidence:2",),
            now=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key="request:request-1",
        )
    assert error.value.reason_code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.parametrize(("reason", "evidence"), [("", ("e",)), ("valid", ())])
def test_request_requires_reason_and_evidence(reason: str, evidence: tuple[str, ...]) -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    with pytest.raises(AuthorizationRefused) as error:
        svc.request_operation(
            request_id="request-missing-evidence",
            operation=LifecycleOperation.REVOKE,
            target_id="credential:old",
            requester_id="requester",
            reason=reason,
            evidence_refs=evidence,
            now=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key=f"missing:{reason}:{len(evidence)}",
        )
    assert error.value.reason_code == "EVIDENCE_REQUIRED"


def test_duplicate_approver_with_distinct_idempotency_key_is_rejected() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    request(svc)
    approve_security(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.approve(
            "request-1",
            approver_id="security-1",
            approver_class=ApproverClass.SECURITY,
            now=NOW + timedelta(minutes=2),
            idempotency_key="different-command-key",
        )
    assert error.value.reason_code == Refusal.SELF_APPROVAL


def test_commit_time_reauth_detects_authority_provider_ctrl02_and_target_drift() -> None:
    mutations = ("authority", "provider", "ctrl02", "target")
    for mutation in mutations:
        svc = service()
        svc.register(object_for(CredentialClass.PASSKEY))
        request(svc)
        approve_security(svc)
        if mutation == "authority":
            svc.authorities.update("sec1")
        elif mutation == "provider":
            svc.provider.versions["credential:old"] = 2
        elif mutation == "ctrl02":
            svc.ctrl02.revision = 2
        else:
            svc._objects["credential:old"] = object_for(
                CredentialClass.PASSKEY, state=LifecycleState.ACTIVE
            )
            svc._objects["credential:old"] = __import__("dataclasses").replace(
                svc._objects["credential:old"], version=2
            )
        with pytest.raises(AuthorizationRefused):
            execute(svc)


def test_commit_time_reauth_detects_trust_version_drift() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.SERVICE_CREDENTIAL))
    request(svc)
    approve_security(svc)
    svc._objects["credential:old"] = replace(svc._objects["credential:old"], trust_version=4)
    with pytest.raises(AuthorizationRefused) as error:
        execute(svc)
    assert error.value.reason_code == Refusal.STALE_TRUST_SET


def test_dependencies_unavailable_fail_closed() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    svc.provider.available = False
    with pytest.raises(AuthorizationRefused) as error:
        request(svc)
    assert error.value.reason_code == Refusal.DEPENDENCY_UNAVAILABLE
