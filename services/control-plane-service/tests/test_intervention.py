"""W4 — bounded regional intervention (FIR-GOV-004)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from _control_plane_builders import LAND_BE, T0, World
from epd2_control_plane_service.domain import InterventionType, ScopeLevel
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.intervention import (
    PRESERVED_MEMBER_CAPABILITIES,
    VOTING_DOMAIN_PROHIBITED_EFFECTS,
    InterventionService,
)

BASE: dict[str, Any] = dict(
    target_scope=LAND_BE,
    valid_from=T0,
    valid_until=T0 + timedelta(days=30),
    reason_code="GOV_INTERVENTION_ONGOING_REVIEW",
    rule_version="SATZUNG-2026.03",
    decision_ref="BUNDESVORSTAND-BESCHLUSS-2026-030",
    initiating_authority_id="a.bund.oversight",
    approving_authority_id="a.bund.chair",
    notification_evidence_ref="NOTIF-2026-030",
    review_deadline=T0 + timedelta(days=14),
)


def test_all_four_levels_exist_and_no_coarse_disable_does() -> None:
    assert {t.value for t in InterventionType} == {
        "SESSION_QUARANTINE",
        "AUTHORITY_SUSPENSION",
        "REGIONAL_ACTION_RESTRICTION",
        "TEMPORARY_SUPERVISION",
    }
    assert not any("DISABLE" in t.value for t in InterventionType)


def test_restriction_requires_named_action_codes() -> None:
    service = InterventionService()
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.open_restriction(
            restriction_id="restr-empty",
            intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
            affected_action_codes=set(),
            **BASE,
        )
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_UNBOUNDED"


def test_free_text_action_codes_are_rejected() -> None:
    service = InterventionService()
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.open_restriction(
            restriction_id="restr-freetext",
            intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
            affected_action_codes={"everything", "*"},
            **BASE,
        )
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_FREE_TEXT"


def test_restriction_may_not_freeze_read_and_evidence_actions() -> None:
    service = InterventionService()
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.open_restriction(
            restriction_id="restr-audit",
            intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
            affected_action_codes={"AUDIT.LOOKUP"},
            **BASE,
        )
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_TOUCHES_PRESERVED"


def test_indefinite_restriction_is_impossible() -> None:
    service = InterventionService()
    args: dict[str, Any] = dict(BASE)
    args["valid_until"] = None
    with pytest.raises(ValueError, match="mandatory valid_until"):
        service.open_restriction(
            restriction_id="restr-forever",
            intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
            affected_action_codes={"AUTH.ASSIGN"},
            **args,
        )


def test_levels_two_and_three_require_a_distinct_approver() -> None:
    service = InterventionService()
    args: dict[str, Any] = dict(BASE)
    args["approving_authority_id"] = None
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.open_restriction(
            restriction_id="restr-noapprover",
            intervention_type=InterventionType.AUTHORITY_SUSPENSION,
            affected_action_codes={"AUTH.ASSIGN"},
            **args,
        )
    assert excinfo.value.reason_code == "CTRL_QUORUM_INSUFFICIENT"

    args["approving_authority_id"] = BASE["initiating_authority_id"]
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.open_restriction(
            restriction_id="restr-selfapprove",
            intervention_type=InterventionType.AUTHORITY_SUSPENSION,
            affected_action_codes={"AUTH.ASSIGN"},
            **args,
        )
    assert excinfo.value.reason_code == "CTRL_SELF_APPROVAL"


def test_silent_extension_is_rejected_and_a_new_decision_supersedes() -> None:
    service = InterventionService()
    original = service.open_restriction(
        restriction_id="restr-ext-1",
        intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
        affected_action_codes={"AUTH.ASSIGN"},
        **BASE,
    )
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.extend(
            original,
            new_valid_until=T0 + timedelta(days=90),
            new_decision_ref=original.decision_ref,
            new_restriction_id="restr-ext-2",
            initiating_authority_id="a.bund.oversight",
            approving_authority_id="a.bund.chair",
            review_deadline=T0 + timedelta(days=60),
            notification_evidence_ref="NOTIF-2026-031",
        )
    assert excinfo.value.reason_code == "CTRL_SILENT_EXTENSION"

    extended = service.extend(
        original,
        new_valid_until=T0 + timedelta(days=90),
        new_decision_ref="BUNDESVORSTAND-BESCHLUSS-2026-041",
        new_restriction_id="restr-ext-2",
        initiating_authority_id="a.bund.oversight",
        approving_authority_id="a.bund.chair",
        review_deadline=T0 + timedelta(days=60),
        notification_evidence_ref="NOTIF-2026-031",
    )
    assert extended.decision_ref != original.decision_ref
    assert extended.valid_from == original.valid_until


def test_supervision_is_capped_at_ninety_days() -> None:
    service = InterventionService()
    with pytest.raises(ValueError, match="at most 90 days"):
        service.open_supervision(
            supervision_id="sup-toolong",
            supervised_scope=LAND_BE,
            supervisor_authority_id="a.bund.oversight",
            granted_action_codes={"MEMBERSHIP.ADMIN_MUTATE"},
            valid_from=T0,
            valid_until=T0 + timedelta(days=180),
            decision_ref="BESCHLUSS-2026-050",
            rule_version="SATZUNG-2026.03",
            review_deadline=T0 + timedelta(days=30),
            confirmation_organ="BUNDESPARTEITAG",
        )


def test_supervision_names_only_the_functions_it_substitutes() -> None:
    service = InterventionService()
    supervision = service.open_supervision(
        supervision_id="sup-ok",
        supervised_scope=LAND_BE,
        supervisor_authority_id="a.bund.oversight",
        granted_action_codes={"MEMBERSHIP.ADMIN_MUTATE"},
        valid_from=T0,
        valid_until=T0 + timedelta(days=60),
        decision_ref="BESCHLUSS-2026-050",
        rule_version="SATZUNG-2026.03",
        review_deadline=T0 + timedelta(days=30),
        confirmation_organ="BUNDESPARTEITAG",
    )
    assert supervision.granted_action_codes == frozenset({"MEMBERSHIP.ADMIN_MUTATE"})
    assert supervision.is_active_at(T0 + timedelta(days=1))
    assert not supervision.is_active_at(T0 + timedelta(days=61))


def test_preserved_member_capabilities_cannot_be_swept_up() -> None:
    service = InterventionService()
    with pytest.raises(AuthorizationRefused) as excinfo:
        service.assert_continuity(["ORDINARY_MEMBER_ACCESS_IN_EXISTING_SCOPE"])
    assert excinfo.value.reason_code == "CTRL_RESTRICTION_TOUCHES_PRESERVED"
    service.assert_continuity(["SOME_UNRELATED_ADMIN_CAPABILITY"])
    assert len(PRESERVED_MEMBER_CAPABILITIES) == 7


def test_intervention_produces_no_voting_domain_effect() -> None:
    service = InterventionService()
    for effect in VOTING_DOMAIN_PROHIBITED_EFFECTS:
        with pytest.raises(AuthorizationRefused) as excinfo:
            service.assert_no_voting_effect([effect])
        assert excinfo.value.reason_code == "CTRL_VOTING_BOUNDARY"


def test_restriction_binds_to_the_exact_scope_only(world: World) -> None:
    service = world.plane.interventions
    restriction = service.open_restriction(
        restriction_id="restr-scope",
        intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
        affected_action_codes={"AUTH.ASSIGN"},
        **BASE,
    )
    world.directory.put_restriction(restriction)
    from _control_plane_builders import LAND_BY

    assert (
        world.directory.blocking_restriction("AUTH.ASSIGN", LAND_BE, None, T0 + timedelta(days=1))
        is not None
    )
    assert (
        world.directory.blocking_restriction("AUTH.ASSIGN", LAND_BY, None, T0 + timedelta(days=1))
        is None
    )
    assert (
        world.directory.blocking_restriction(
            "TRANSPARENCY.PUBLISH", LAND_BE, None, T0 + timedelta(days=1)
        )
        is None
    )
    assert restriction.target_scope.level is ScopeLevel.LAND
