"""W1/W2/W7 — inventory completeness, read models, and API contract coverage."""

from __future__ import annotations

import pytest
from _control_plane_builders import LAND_BE, T0, World, run_governed_flow
from epd2_control_plane_service.api import (
    CONSOLE_CAPABILITIES,
    build_contracts,
    contracts_to_json_obj,
)
from epd2_control_plane_service.domain import ActorClass, Right
from epd2_control_plane_service.exceptions import InventoryError
from epd2_control_plane_service.inventory import INVENTORY, NO_UI_DECISIONS, inventory_to_json_obj

REQUIRED_DESKS = {
    "DESK_PLATFORM_OPERATIONS",
    "DESK_SECURITY_OPERATIONS",
    "DESK_PRIVILEGED_ACCESS",
    "DESK_AUDIT_OVERSIGHT",
    "DESK_DPO_PRIVACY",
    "DESK_ELECTION_ADMIN",
    "DESK_MEMBERSHIP_ADMIN",
    "DESK_OFFICES_MANDATES",
    "DESK_ASSEMBLIES",
    "DESK_CORRESPONDENCE",
    "DESK_COMPLAINTS_OMBUDS",
    "DESK_PROTECTED_REPORTING",
    "DESK_FINANCE",
    "DESK_PROCUREMENT",
    "DESK_RECORDS_RETENTION",
    "DESK_TRANSPARENCY_PUBLICATION",
    "DESK_REPRESENTATIVE_OPEN_DESK",
    "DESK_CITIZEN_OFFICE",
    "DESK_MODERATION",
    "DESK_AI_OVERSIGHT",
    "DESK_EMERGENCY",
    "DESK_CREDENTIAL_OPERATIONS",
    "DESK_RECOVERY",
    "DESK_SERVICE_IDENTITY",
    "DESK_KEY_CUSTODY",
    "DESK_ORG_AUTHORITY",
    "DESK_REGIONAL_INTERVENTION",
}


def test_every_required_desk_is_covered() -> None:
    assert INVENTORY.desks() >= REQUIRED_DESKS


def test_no_universal_administrator_action_exists() -> None:
    """No single action carries the full right set, and no action id or desk
    claims universal administration."""
    all_rights = set(Right)
    for action in INVENTORY:
        held = {
            action.required_right_request,
            action.required_right_execute,
            action.required_right_audit,
        }
        held |= {
            r
            for r in (action.required_right_approve, action.required_right_revoke)
            if r is not None
        }
        assert held != all_rights, action.action_id
        assert "ADMIN_ALL" not in action.action_id.upper()
        assert "SUPERUSER" not in action.desk_id.upper()


def test_every_action_declares_a_full_right_and_evidence_contract() -> None:
    for action in INVENTORY:
        assert action.governing_fir_refs
        assert action.object_class
        assert action.immutable_evidence_required
        if action.mutation:
            assert action.commit_time_reauthorization
            assert action.required_right_revoke is not None, (
                f"{action.action_id}: every mutation must declare a revoke/rollback right"
            )


def test_runtime_mutations_and_inventory_are_congruent(world: World) -> None:
    assert world.plane.runtime_mutation_ids() == INVENTORY.mutation_ids()
    assert set(world.plane.runtime_routes().values()) == INVENTORY.action_ids()


def test_an_unmapped_action_fails_closed(world: World) -> None:
    with pytest.raises(InventoryError):
        world.plane.submit_request(
            request_id="req-unmapped",
            action_id="ADMIN.DO_ANYTHING",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="o",
            purpose="undocumented endpoint",
            moment=T0,
        )


def test_routes_are_unique() -> None:
    routes = [a.route for a in INVENTORY]
    assert len(routes) == len(set(routes))


def test_no_ui_decisions_are_explicit() -> None:
    roles = {entry["role"] for entry in NO_UI_DECISIONS}
    assert "UNIVERSAL_SYSTEM_ADMINISTRATOR" in roles
    assert "VOTING_TRUSTEE" in roles
    for entry in NO_UI_DECISIONS:
        assert entry["decision"] == "NO_UI"
        assert entry["rationale"]


def test_all_eleven_console_capabilities_are_covered() -> None:
    payload = contracts_to_json_obj()
    assert payload["uncovered_console_capabilities"] == []
    assert len(CONSOLE_CAPABILITIES) == 11


def test_every_mutating_contract_declares_server_side_authorization() -> None:
    for contract in build_contracts():
        if contract.mutation:
            assert contract.server_side_authorization
            assert contract.commit_time_reauthorization
        assert contract.evidence_emitted


def test_service_actions_reject_human_principals_and_vice_versa(world: World) -> None:
    service_actions = [a for a in INVENTORY if a.actor_class is ActorClass.SERVICE]
    assert service_actions, "at least one workload-only action must exist"
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.submit_request(
            request_id="req-actorclass",
            action_id=service_actions[0].action_id,
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=world.directory.current_authority("a.svc.scheduler").scope,  # type: ignore[union-attr]
            object_ref="task.1",
            purpose="human running a workload action",
            moment=T0,
        )
    assert excinfo.value.reason_code == "CTRL_ACTOR_CLASS"


def test_read_model_summarizes_without_erasing_history(world: World) -> None:
    from epd2_control_plane_service.domain import AuthorityState

    world.directory.set_authority_state(
        "a.land.be.chair",
        AuthorityState.SUSPENDED,
        recorded_at=T0,
        recorded_by="governance",
        note="level 2",
    )
    world.directory.set_authority_state(
        "a.land.be.chair",
        AuthorityState.ACTIVE,
        recorded_at=T0,
        recorded_by="governance",
        note="restored",
    )
    model = world.directory.read_model(T0)
    current = {a["authority_id"]: a for a in model["current_organizational_authority"]}
    assert current["a.land.be.chair"]["state"] == "ACTIVE"

    history = [h for h in model["authority_history"] if h["authority_id"] == "a.land.be.chair"]
    assert [h["state"] for h in history] == ["ACTIVE", "SUSPENDED", "ACTIVE"]
    assert history[1]["note"] == "level 2"


def test_read_model_carries_every_required_projection(world: World) -> None:
    model = world.directory.read_model(T0)
    for key in (
        "current_organizational_authority",
        "authority_source",
        "authority_history",
        "session_quarantine_state",
        "current_restrictions",
        "temporary_supervision",
        "service_credential_state",
        "human_credential_state",
        "trust_key_references",
    ):
        assert key in model, key


def test_inventory_json_payload_is_complete() -> None:
    payload = inventory_to_json_obj()
    assert payload["counts"]["actions_total"] == len(INVENTORY)
    assert len(payload["actions"]) == len(INVENTORY)
    for entry in payload["actions"]:
        assert entry["voting_domain_boundary"] != "INSIDE_VOTING_DOMAIN"


def test_audit_desk_holds_no_mutation_right_anywhere(world: World) -> None:
    for authority in world.directory.authorities_of("p.auditor"):
        forbidden = {
            Right.EXECUTE,
            Right.ACTIVATE,
            Right.SUSPEND_OR_QUARANTINE,
            Right.REVOKE,
            Right.RESTORE,
            Right.ROTATE_OR_REPLACE,
            Right.DESTROY,
            Right.APPROVE,
        }
        assert not (authority.capabilities & forbidden), authority.authority_id


def test_read_path_refuses_a_mutation_action(world: World) -> None:
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.read(
            action_id="AUTH.ASSIGN",
            principal_id="p.auditor",
            session_id="s.p.auditor",
            scope=LAND_BE,
            object_ref="authority.target",
            moment=T0,
        )
    assert excinfo.value.reason_code == "CTRL_READ_PATH_MISUSE"


def test_auditor_can_read_provenance(world: World) -> None:
    run_governed_flow(
        world,
        request_id="req-inv-read",
        action_id="AUTH.ASSIGN",
        requester="p.land.be.chair",
        approvers=("p.land.be.deputy", "p.land.be.secretary"),
        executor="p.land.be.chair",
        scope=LAND_BE,
    )
    result = world.plane.read(
        action_id="AUDIT.LOOKUP",
        principal_id="p.auditor",
        session_id="s.p.auditor",
        scope=world.directory.current_authority("a.auditor").scope,  # type: ignore[union-attr]
        object_ref="evidence.1",
        moment=T0,
    )
    assert result["action_id"] == "AUDIT.LOOKUP"
    assert world.journal.find(result="READ")
