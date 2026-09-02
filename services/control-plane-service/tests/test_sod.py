"""W3 — separation of duties."""

from __future__ import annotations

from datetime import timedelta

import pytest
from _control_plane_builders import LAND_BE, PLATFORM, T0, World, run_governed_flow
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.inventory import INVENTORY
from epd2_control_plane_service.sod import SOD_RULES, Responsibility, SodEngine


def test_matrix_covers_the_nine_required_pairs() -> None:
    required = {
        (Responsibility.REQUEST, Responsibility.APPROVE),
        (Responsibility.APPROVE, Responsibility.EXECUTE),
        (Responsibility.EXECUTE, Responsibility.AUDIT),
        (Responsibility.SECRET_VISIBILITY, Responsibility.APPROVE),
        (Responsibility.CREDENTIAL_ISSUANCE, Responsibility.AUDIT),
        (Responsibility.KEY_CUSTODY, Responsibility.POLICY_APPROVAL),
        (Responsibility.EMERGENCY_GRANT, Responsibility.EMERGENCY_REVIEW),
        (Responsibility.DESTRUCTIVE_OPERATION, Responsibility.DESTRUCTIVE_CONFIRMATION),
        (Responsibility.REGIONAL_ACTION, Responsibility.BUND_OVERSIGHT),
    }
    present = {rule.pair() for rule in SOD_RULES}
    for left, right in required:
        assert frozenset({left, right}) in present, f"missing SoD rule {left}/{right}"


@pytest.mark.parametrize("rule", SOD_RULES, ids=[r.rule_id for r in SOD_RULES])
def test_every_rule_detects_concentration(rule) -> None:  # type: ignore[no-untyped-def]
    engine = SodEngine()
    violations = engine.evaluate({rule.left: ("p.same",), rule.right: ("p.same",)})
    assert any(v.rule_id == rule.rule_id for v in violations)


@pytest.mark.parametrize("rule", SOD_RULES, ids=[r.rule_id for r in SOD_RULES])
def test_distinct_principals_do_not_violate(rule) -> None:  # type: ignore[no-untyped-def]
    engine = SodEngine()
    violations = engine.evaluate({rule.left: ("p.a",), rule.right: ("p.b",)})
    assert not [v for v in violations if v.rule_id == rule.rule_id]


def test_executor_may_not_also_be_the_named_auditor(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as excinfo:
        run_governed_flow(
            world,
            request_id="req-sod-audit",
            action_id="AUTH.ASSIGN",
            requester="p.land.be.chair",
            approvers=("p.land.be.deputy", "p.land.be.secretary"),
            executor="p.land.be.chair",
            scope=LAND_BE,
            auditor_id="p.land.be.chair",
        )
    assert excinfo.value.reason_code == "CTRL_EXECUTE_AUDIT_MERGED"


def test_key_custody_may_not_supply_its_own_policy_approval(world: World) -> None:
    """The custodian executes; the policy approver approves. Concentrating both
    in the custodian must be refused (SOD-06)."""
    world.plane.submit_request(
        request_id="req-sod-key",
        action_id="KEY.ROTATE",
        principal_id="p.key.custodian",
        session_id="s.p.key.custodian",
        scope=PLATFORM,
        object_ref="key.platform.signing.1",
        purpose="scheduled rotation",
        moment=T0,
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.approve(
            request_id="req-sod-key",
            principal_id="p.key.custodian",
            session_id="s.p.key.custodian",
            moment=T0 + timedelta(minutes=1),
        )
    assert excinfo.value.reason_code == "CTRL_SELF_APPROVAL"


def test_governed_key_rotation_with_separated_duties_succeeds(world: World) -> None:
    outcome = run_governed_flow(
        world,
        request_id="req-sod-key-ok",
        action_id="KEY.ROTATE",
        requester="p.key.custodian",
        approvers=("p.key.policy.approver", "p.service.owner"),
        executor="p.key.custodian",
        scope=PLATFORM,
        object_ref="key.platform.signing.1",
    )
    assert outcome.approver_ids == ("p.key.policy.approver", "p.service.owner")


def test_every_four_eyes_action_declares_at_least_two_approvals() -> None:
    for action in INVENTORY:
        if action.four_eyes:
            assert action.quorum_required >= 2, action.action_id


def test_responsibilities_for_intervention_include_oversight() -> None:
    engine = SodEngine()
    action = INVENTORY.get("INTERVENE.REGIONAL_ACTION_RESTRICTION")
    responsibilities = engine.responsibilities_for(action)
    assert Responsibility.REGIONAL_ACTION in responsibilities
    assert Responsibility.BUND_OVERSIGHT in responsibilities
