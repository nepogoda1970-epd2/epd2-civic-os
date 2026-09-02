"""W9 — commit-time reauthorization.

Each test approves a request legitimately, changes one element of the world,
and then commits. The commit must refuse. Together they prove there is no
time-of-check/time-of-use window: the request-time decision is never reused.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _control_plane_builders import LAND_BE, PLATFORM, T0, World, _authority
from epd2_control_plane_service.domain import (
    AuthorityState,
    CredentialState,
    InterventionType,
    Right,
    SessionState,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused

REQUEST_AT = T0
APPROVE_AT = T0 + timedelta(minutes=1)
COMMIT_AT = T0 + timedelta(minutes=5)


def _approved_assign(world: World, request_id: str = "req-reauth") -> None:
    world.plane.submit_request(
        request_id=request_id,
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="governed assignment",
        moment=REQUEST_AT,
    )
    for approver in ("p.land.be.deputy", "p.land.be.secretary"):
        world.plane.approve(
            request_id=request_id,
            principal_id=approver,
            session_id=f"s.{approver}",
            moment=APPROVE_AT,
        )


def _commit(world: World, request_id: str = "req-reauth", *, principal: str = "p.land.be.chair"):  # type: ignore[no-untyped-def]
    return world.plane.execute(
        request_id=request_id, principal_id=principal, session_id=f"s.{principal}", moment=COMMIT_AT
    )


def test_baseline_commit_succeeds_when_nothing_changed(world: World) -> None:
    """The control case. Without it, every test below could pass for the wrong
    reason — a workflow that never commits proves nothing about TOCTOU."""
    _approved_assign(world)
    outcome = _commit(world)
    assert outcome.request.executed_at == COMMIT_AT


def test_1_authority_revoked_after_request(world: World) -> None:
    _approved_assign(world)
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.REVOKED, recorded_at=APPROVE_AT, recorded_by="governance"
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_AUTHORITY_REVOKED"


def test_2_intervention_activated_during_workflow(world: World) -> None:
    _approved_assign(world)
    restriction = world.plane.interventions.open_restriction(
        restriction_id="restr-reauth-2",
        intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
        target_scope=LAND_BE,
        affected_action_codes={"AUTH.ASSIGN"},
        valid_from=APPROVE_AT,
        valid_until=APPROVE_AT + timedelta(days=30),
        reason_code="GOV_INTERVENTION_ONGOING_REVIEW",
        rule_version="SATZUNG-2026.03",
        decision_ref="BUNDESVORSTAND-BESCHLUSS-2026-020",
        initiating_authority_id="a.bund.oversight",
        approving_authority_id="a.bund.chair",
        notification_evidence_ref="NOTIF-2026-020",
        review_deadline=APPROVE_AT + timedelta(days=14),
    )
    world.directory.put_restriction(restriction)
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_ACTIVE"


def test_3_emergency_grant_expires_before_commit(world: World) -> None:
    emergency = world.plane.emergency
    emergency.request(
        grant_id="grant-reauth-3",
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="incident containment",
        scope=PLATFORM,
        action_codes={"SERVICE_CRED.REVOKE"},
        requested_at=REQUEST_AT,
    )
    emergency.approve(
        "grant-reauth-3", approver_id="p.emergency.controller", approved_at=REQUEST_AT
    )
    emergency.activate("grant-reauth-3", activated_at=REQUEST_AT)

    # A principal with no ordinary execute right for the action, relying on the grant.
    world.directory.record_authority(
        _authority(
            "a.incident.requester",
            "p.emergency.controller",
            "INCIDENT_REQUESTER",
            PLATFORM,
            {Right.REQUEST, Right.READ_METADATA},
            {"SERVICE_CRED.REVOKE"},
        ),
        recorded_at=REQUEST_AT,
        recorded_by="test",
    )
    world.plane.submit_request(
        request_id="req-reauth-3",
        action_id="SERVICE_CRED.REVOKE",
        principal_id="p.emergency.controller",
        session_id="s.p.emergency.controller",
        scope=PLATFORM,
        object_ref="svc.cred.scheduler",
        purpose="emergency revoke",
        moment=REQUEST_AT,
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.execute(
            request_id="req-reauth-3",
            principal_id="p.emergency.controller",
            session_id="s.p.emergency.controller",
            moment=REQUEST_AT + timedelta(hours=3),
            emergency_grant_id="grant-reauth-3",
        )
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_EXPIRED"


def test_4_quorum_changes_when_an_approver_loses_authority(world: World) -> None:
    _approved_assign(world)
    world.directory.set_authority_state(
        "a.land.be.deputy",
        AuthorityState.SUSPENDED,
        recorded_at=APPROVE_AT,
        recorded_by="governance",
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_COMMIT_TIME_REAUTH_FAILED"


def test_5_target_object_scope_changes(world: World) -> None:
    """Reorganization moves the executor's office to another scope. The approved
    request still names Land Berlin, so the commit no longer resolves."""
    _approved_assign(world)
    world.directory.record_authority(
        _authority(
            "a.land.be.chair",
            "p.land.be.chair",
            "LANDESVORSITZ",
            world.directory.current_authority("a.land.by.chair").scope,  # type: ignore[union-attr]
            {Right.REQUEST, Right.EXECUTE, Right.READ_METADATA},
            {"AUTH.ASSIGN"},
            decision="REORGANISATION-2026-031",
        ),
        recorded_at=APPROVE_AT,
        recorded_by="governance",
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_SCOPE_ISOLATION"


def test_6_session_quarantined_before_commit(world: World) -> None:
    _approved_assign(world)
    world.directory.set_session_state("s.p.land.be.chair", SessionState.QUARANTINED)
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_SESSION_NOT_ACTIVE"


def test_7_credential_revoked_before_commit(world: World) -> None:
    _approved_assign(world)
    world.directory.set_human_credential_state("cred.p.land.be.chair", CredentialState.REVOKED)
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_CREDENTIAL_NOT_ACTIVE"


def test_8_region_restriction_begins_before_commit(world: World) -> None:
    """A level-2 authority suspension naming the executor's exact authority."""
    _approved_assign(world)
    restriction = world.plane.interventions.open_restriction(
        restriction_id="restr-reauth-8",
        intervention_type=InterventionType.AUTHORITY_SUSPENSION,
        target_scope=LAND_BE,
        affected_action_codes={"AUTH.ASSIGN", "MEMBERSHIP.ADMIN_MUTATE"},
        affected_authority_ids={"a.land.be.chair"},
        valid_from=APPROVE_AT,
        valid_until=APPROVE_AT + timedelta(days=60),
        reason_code="GOV_AUTHORITY_SUSPENSION",
        rule_version="SATZUNG-2026.03",
        decision_ref="BUNDESVORSTAND-BESCHLUSS-2026-021",
        initiating_authority_id="a.bund.oversight",
        approving_authority_id="a.bund.chair",
        notification_evidence_ref="NOTIF-2026-021",
        review_deadline=APPROVE_AT + timedelta(days=14),
    )
    world.directory.put_restriction(restriction)
    with pytest.raises(AuthorizationRefused) as excinfo:
        _commit(world)
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_ACTIVE"


def test_refusals_are_recorded_as_evidence(world: World) -> None:
    _approved_assign(world)
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.REVOKED, recorded_at=APPROVE_AT, recorded_by="governance"
    )
    with pytest.raises(AuthorizationRefused):
        _commit(world)
    refusals = world.journal.find(result="REFUSED")
    assert len(refusals) == 1
    assert refusals[0].action_id == "AUTH.ASSIGN"
    world.journal.verify()
