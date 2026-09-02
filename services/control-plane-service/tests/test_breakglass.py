"""W6 — break-glass and emergency operations."""

from __future__ import annotations

from datetime import timedelta

import pytest
from _control_plane_builders import LAND_BE, PLATFORM, T0, World
from epd2_control_plane_service.breakglass import PROHIBITED_UNDER_BREAK_GLASS
from epd2_control_plane_service.domain import BreakGlassState
from epd2_control_plane_service.exceptions import AuthorizationRefused


def _state(world: World, grant_id: str) -> str:
    """Read a grant's state, failing the test rather than the type checker if
    the grant is missing."""
    grant = world.plane.emergency.grant(grant_id)
    assert grant is not None, f"grant {grant_id} does not exist"
    return grant.state.value


def _requested(world: World, grant_id: str = "grant-1", codes: set[str] | None = None):  # type: ignore[no-untyped-def]
    return world.plane.emergency.request(
        grant_id=grant_id,
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="incident INC-2026-0042: suspected service credential compromise",
        scope=PLATFORM,
        action_codes=codes or {"SERVICE_CRED.REVOKE"},
        requested_at=T0,
    )


def test_full_lifecycle_reaches_reviewed(world: World) -> None:
    emergency = world.plane.emergency
    _requested(world)
    assert _state(world, "grant-1") == BreakGlassState.REQUESTED.value
    emergency.approve("grant-1", approver_id="p.emergency.controller", approved_at=T0)
    assert _state(world, "grant-1") == BreakGlassState.APPROVED.value
    emergency.activate("grant-1", activated_at=T0)
    assert _state(world, "grant-1") == BreakGlassState.ACTIVE.value
    emergency.use(
        "grant-1",
        action_id="SERVICE_CRED.REVOKE",
        scope=PLATFORM,
        moment=T0 + timedelta(minutes=5),
        use_ref="use-1",
    )
    emergency.expire_due(T0 + timedelta(hours=2))
    assert _state(world, "grant-1") == BreakGlassState.EXPIRED.value
    emergency.review("grant-1", reviewer_id="p.auditor", review_ref="REVIEW-2026-0042")
    assert _state(world, "grant-1") == BreakGlassState.REVIEWED.value
    assert emergency.unreviewed() == ()


def test_reason_and_scope_are_mandatory(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.emergency.request(
            grant_id="grant-noscope",
            principal_id="p.security.operator",
            requested_by="p.privileged.operator",
            reason="incident",
            scope=PLATFORM,
            action_codes=set(),
            requested_at=T0,
        )
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_SCOPE"
    with pytest.raises(ValueError, match="explicit reason"):
        world.plane.emergency.request(
            grant_id="grant-noreason",
            principal_id="p.security.operator",
            requested_by="p.privileged.operator",
            reason="   ",
            scope=PLATFORM,
            action_codes={"SERVICE_CRED.REVOKE"},
            requested_at=T0,
        )


def test_approver_must_be_distinct_from_requester_and_subject(world: World) -> None:
    _requested(world, "grant-self")
    for approver in ("p.privileged.operator", "p.security.operator"):
        with pytest.raises(AuthorizationRefused) as excinfo:
            world.plane.emergency.approve("grant-self", approver_id=approver, approved_at=T0)
        assert excinfo.value.reason_code == "CTRL_SELF_APPROVAL"


def test_expiry_is_automatic_and_absolute(world: World) -> None:
    emergency = world.plane.emergency
    _requested(world, "grant-exp")
    emergency.approve("grant-exp", approver_id="p.emergency.controller", approved_at=T0)
    grant = emergency.activate("grant-exp", activated_at=T0)
    assert grant.expires_at == T0 + timedelta(seconds=1800)
    emergency.expire_due(T0 + timedelta(seconds=1801))
    assert _state(world, "grant-exp") == BreakGlassState.EXPIRED.value


def test_there_is_no_renewal_path(world: World) -> None:
    """An expired grant cannot be re-activated; a follow-on emergency needs its
    own REQUEST with its own approval."""
    emergency = world.plane.emergency
    _requested(world, "grant-renew")
    emergency.approve("grant-renew", approver_id="p.emergency.controller", approved_at=T0)
    emergency.activate("grant-renew", activated_at=T0)
    emergency.expire_due(T0 + timedelta(hours=1))
    with pytest.raises(AuthorizationRefused) as excinfo:
        emergency.activate("grant-renew", activated_at=T0 + timedelta(hours=1))
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_STATE"
    assert not hasattr(emergency, "renew")


def test_prohibited_actions_are_refused_even_under_break_glass(world: World) -> None:
    for action_id in sorted(PROHIBITED_UNDER_BREAK_GLASS):
        with pytest.raises(AuthorizationRefused) as excinfo:
            world.plane.emergency.request(
                grant_id=f"grant-prohibited-{action_id.split('.')[-1].lower()}",
                principal_id="p.security.operator",
                requested_by="p.privileged.operator",
                reason="attempt to reach a prohibited act",
                scope=LAND_BE,
                action_codes={action_id},
                requested_at=T0,
            )
        assert excinfo.value.reason_code == "CTRL_EMERGENCY_PROHIBITED_ACTION"


def test_non_emergency_eligible_actions_cannot_be_granted(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.emergency.request(
            grant_id="grant-noteligible",
            principal_id="p.security.operator",
            requested_by="p.privileged.operator",
            reason="attempt",
            scope=LAND_BE,
            action_codes={"TRANSPARENCY.PUBLISH"},
            requested_at=T0,
        )
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_NOT_ELIGIBLE"


def test_post_use_review_may_not_be_done_by_an_actor_of_the_grant(world: World) -> None:
    emergency = world.plane.emergency
    _requested(world, "grant-review")
    emergency.approve("grant-review", approver_id="p.emergency.controller", approved_at=T0)
    emergency.activate("grant-review", activated_at=T0)
    emergency.revoke("grant-review", revoked_at=T0 + timedelta(minutes=10))
    for actor in ("p.privileged.operator", "p.security.operator", "p.emergency.controller"):
        with pytest.raises(AuthorizationRefused) as excinfo:
            emergency.review("grant-review", reviewer_id=actor, review_ref="REVIEW-X")
        assert excinfo.value.reason_code == "CTRL_EMERGENCY_SELF_REVIEW"


def test_unreviewed_grants_are_reported(world: World) -> None:
    emergency = world.plane.emergency
    _requested(world, "grant-unreviewed")
    emergency.approve("grant-unreviewed", approver_id="p.emergency.controller", approved_at=T0)
    emergency.activate("grant-unreviewed", activated_at=T0)
    emergency.expire_due(T0 + timedelta(hours=2))
    assert [g.grant_id for g in emergency.unreviewed()] == ["grant-unreviewed"]
