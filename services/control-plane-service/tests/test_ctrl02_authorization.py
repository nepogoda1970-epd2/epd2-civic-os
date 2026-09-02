from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl02_builders import BAVARIA, BERLIN, NOW, approve_twice, request, service
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import (
    ApproverClass,
    Decision,
    InterventionLevel,
)


def test_self_approval_is_rejected() -> None:
    svc = service()
    request(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.approve(
            "request-1",
            approver_id="requester",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=1),
            idempotency_key="self",
        )
    assert error.value.reason_code == Decision.SELF_APPROVAL_FORBIDDEN


def test_duplicate_approver_identity_is_not_quorum() -> None:
    svc = service()
    request(svc)
    svc.approve(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="a1",
    )
    with pytest.raises(AuthorizationRefused):
        svc.approve(
            "request-1",
            approver_id="approver-1",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=2),
            idempotency_key="a1-again",
        )


def test_service_identity_cannot_approve_as_human() -> None:
    svc = service()
    request(svc)
    with pytest.raises(AuthorizationRefused):
        svc.approve(
            "request-1",
            approver_id="service-actor",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=1),
            idempotency_key="service",
        )


def test_bund_actor_does_not_inherit_regional_competence() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused) as error:
        svc.request_intervention(
            request_id="bund-takeover",
            level=InterventionLevel.TEMPORARY_SUPERVISION,
            requester_id="bund-actor",
            governance_basis="Bund hierarchy",
            scope=BERLIN,
            target_ids=("principal:bund-supervisor",),
            reason="implicit takeover",
            evidence_refs=("evidence:1",),
            not_before=NOW,
            expires_at=NOW + timedelta(hours=1),
            allowed_capabilities=("MEMBER.REVIEW",),
            target_version=1,
            idempotency_key="bund",
        )
    assert error.value.reason_code == Decision.WRONG_SCOPE
    assert BAVARIA != BERLIN


def test_commit_time_reauthorization_detects_revoked_approver() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.authorities.update("a2", revoked=True)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-stale",
        )
    assert error.value.reason_code == Decision.STALE_AUTHORITY


def test_commit_time_reauthorization_detects_approver_version_change() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.authorities.update("a2")
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-version-change",
        )
    assert error.value.reason_code == Decision.STALE_AUTHORITY


def test_commit_time_reauthorization_detects_target_change() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.set_target_version("action:MEMBER.UPDATE", 2)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-stale-target",
        )
    assert error.value.reason_code == Decision.STALE_TARGET


def test_authority_dependency_unavailable_fails_closed() -> None:
    svc = service()
    svc.authorities.available = False
    with pytest.raises(AuthorizationRefused) as error:
        request(svc)
    assert error.value.reason_code == Decision.DEPENDENCY_UNAVAILABLE


def test_approval_does_not_equal_execution() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="approver-1",
            now=NOW + timedelta(minutes=3),
            idempotency_key="bad-exec",
        )
    assert error.value.reason_code == "EXECUTION_SEPARATION"


def test_reviewer_cannot_execute() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    with pytest.raises(AuthorizationRefused):
        svc.activate(
            "request-1",
            executor_id="reviewer",
            now=NOW + timedelta(minutes=3),
            idempotency_key="reviewer-exec",
        )


@pytest.mark.parametrize(
    "capability",
    [
        "VOTER.LOOKUP",
        "BALLOT.READ",
        "BALLOT.CORRELATE_PERSON",
        "TALLY.READ_INTERMEDIATE",
        "VOTING.ADMIN",
    ],
)
def test_voting_boundary_is_absolute(capability: str) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        request(service(), capabilities=(capability,))
    assert error.value.reason_code == Decision.VOTING_BOUNDARY


@pytest.mark.parametrize("capability", ["AUTHORITY.UNIVERSAL_ADMIN", "SECRET.RAW_READ"])
def test_universal_admin_and_secret_capability_are_forbidden(capability: str) -> None:
    with pytest.raises(AuthorizationRefused):
        request(service(), capabilities=(capability,))
