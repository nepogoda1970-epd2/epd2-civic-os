from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl02_builders import BERLIN, NOW, activate, approve_twice, request, service
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import (
    ApproverClass,
    Decision,
    InterventionLevel,
    WorkflowState,
)


def test_regional_restriction_full_lifecycle() -> None:
    svc = service()
    created = request(svc)
    assert created.state is WorkflowState.REQUESTED
    approved = approve_twice(svc)
    assert approved.state is WorkflowState.APPROVED
    active = activate(svc)
    assert active.state is WorkflowState.ACTIVE
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id=None,
            capability="MEMBER.UPDATE",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
        )
        is Decision.ACTION_RESTRICTED
    )
    revoked = svc.revoke(
        "request-1",
        actor_id="revoker",
        now=NOW + timedelta(minutes=5),
        idempotency_key="revoke:1",
    )
    assert revoked.state is WorkflowState.REVOKED
    reviewed = svc.post_review(
        "request-1",
        reviewer_id="reviewer",
        review_ref="review:1",
        now=NOW + timedelta(minutes=6),
    )
    assert reviewed.state is WorkflowState.POST_REVIEWED


def test_l1_quarantine_is_exact_session_only() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.SESSION_QUARANTINE,
        targets=("session:s-1",),
        capabilities=("SESSION.USE",),
    )
    approved = svc.approve(
        "request-1",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=1),
        idempotency_key="l1:approve",
    )
    assert approved.state is WorkflowState.APPROVED
    activate(svc)
    assert (
        svc.effective_decision(
            session_id="session:s-1",
            authority_id=None,
            capability="SESSION.USE",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
        )
        is Decision.SESSION_QUARANTINED
    )


def test_subject_quarantine_applies_to_a_new_session() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.SESSION_QUARANTINE,
        targets=("subject:member-1",),
        capabilities=("SESSION.USE",),
    )
    svc.approve(
        "request-1",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=1),
        idempotency_key="subject-quarantine:approve",
    )
    activate(svc)
    assert (
        svc.effective_decision(
            session_id="session:new",
            session_owner_id="member-1",
            authority_id=None,
            capability="SESSION.USE",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
        )
        is Decision.SESSION_QUARANTINED
    )


def test_l2_suspends_exact_authority_without_deleting_history() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.AUTHORITY_SUSPENSION,
        targets=("authority:regional-chair",),
        capabilities=("AUTHORITY.ACT",),
    )
    approve_twice(svc)
    activate(svc)
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id="authority:regional-chair",
            capability="AUTHORITY.ACT",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
        )
        is Decision.AUTHORITY_SUSPENDED
    )
    assert any(event.target == "request-1" for event in svc.events)


def test_l4_requires_governance_and_security_classes() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.TEMPORARY_SUPERVISION,
        targets=("principal:supervisor",),
        capabilities=("MEMBER.REVIEW",),
    )
    first = svc.approve(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="l4:a1",
    )
    assert first.state is WorkflowState.REVIEWING
    second = svc.approve(
        "request-1",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="l4:sec",
    )
    assert second.state is WorkflowState.APPROVED


def test_l4_two_governance_approvals_do_not_replace_security_approval() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.TEMPORARY_SUPERVISION,
        targets=("principal:supervisor",),
        capabilities=("MEMBER.REVIEW",),
    )
    svc.approve(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="l4:g1",
    )
    second = svc.approve(
        "request-1",
        approver_id="approver-2",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=2),
        idempotency_key="l4:g2",
    )
    assert second.state is WorkflowState.REVIEWING


def test_l3_one_approval_is_not_quorum() -> None:
    svc = service()
    request(svc)
    first = svc.approve(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="l3:one",
    )
    assert first.state is WorkflowState.REVIEWING


@pytest.mark.parametrize("target", ["*", "ALL", "REGION_DISABLED", "GLOBAL", "item:*"], ids=str)
def test_coarse_targets_are_rejected(target: str) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        request(service(), targets=(target,))
    assert error.value.reason_code == Decision.WRONG_SCOPE


def test_expiry_is_automatic_and_does_not_renew() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    activate(svc)
    assert svc.expire_due(NOW + timedelta(hours=3)) == ("request-1",)
    assert svc.requests[0].state is WorkflowState.EXPIRED
    assert svc.expire_due(NOW + timedelta(minutes=1)) == ()
    assert svc.requests[0].state is WorkflowState.EXPIRED


def test_clock_rollback_does_not_reactivate_elapsed_restriction() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    activate(svc)
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id=None,
            capability="MEMBER.UPDATE",
            scope=BERLIN,
            now=NOW + timedelta(hours=3),
        )
        is Decision.ALLOW
    )
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id=None,
            capability="MEMBER.UPDATE",
            scope=BERLIN,
            now=NOW + timedelta(hours=1),
        )
        is Decision.ALLOW
    )


def test_duplicate_request_is_idempotent() -> None:
    svc = service()
    first = request(svc)
    second = request(svc)
    assert first == second
    assert len(svc.requests) == 1
    assert len(svc.events) == 1


def test_duplicate_activation_with_new_key_has_no_second_effect() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    activate(svc)
    before = len(svc.events)
    with pytest.raises(AuthorizationRefused):
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=4),
            idempotency_key="activate:new-key",
        )
    assert len(svc.events) == before


def test_supervision_over_ninety_days_is_rejected() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused):
        svc.request_intervention(
            request_id="long-supervision",
            level=InterventionLevel.TEMPORARY_SUPERVISION,
            requester_id="requester",
            governance_basis="FIR-GOV-004",
            scope=BERLIN,
            target_ids=("principal:supervisor",),
            reason="too long",
            evidence_refs=("evidence:1",),
            not_before=NOW,
            expires_at=NOW + timedelta(days=91),
            allowed_capabilities=("MEMBER.REVIEW",),
            target_version=1,
            idempotency_key="long-supervision",
        )


def test_reject_and_cancel_are_terminal_without_side_effects() -> None:
    svc = service()
    request(svc)
    rejected = svc.reject(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        reason="basis insufficient",
        now=NOW + timedelta(minutes=1),
    )
    assert rejected.state is WorkflowState.REJECTED

    other = service()
    request(other)
    cancelled = other.cancel("request-1", requester_id="requester", now=NOW + timedelta(minutes=1))
    assert cancelled.state is WorkflowState.CANCELLED


def test_restoration_requires_valid_original_authority_and_no_newer_conflict() -> None:
    svc = service()
    request(
        svc,
        level=InterventionLevel.AUTHORITY_SUSPENSION,
        targets=("authority:regional-chair",),
        capabilities=("AUTHORITY.ACT",),
    )
    approve_twice(svc)
    activate(svc)
    svc.revoke(
        "request-1",
        actor_id="revoker",
        now=NOW + timedelta(minutes=4),
        idempotency_key="restore:revoke",
    )
    with pytest.raises(AuthorizationRefused):
        svc.restore(
            "request-1",
            actor_id="restorer",
            original_authority_valid=False,
            newer_conflict=False,
            now=NOW + timedelta(minutes=5),
        )
    restored = svc.restore(
        "request-1",
        actor_id="restorer",
        original_authority_valid=True,
        newer_conflict=False,
        now=NOW + timedelta(minutes=6),
    )
    assert restored.state is WorkflowState.COMPLETED
