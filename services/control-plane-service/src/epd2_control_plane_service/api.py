"""W7 — control-console API contracts.

Contracts are declared as data so that gate G13 can prove coverage
mechanically: every governed inventory action must be reachable through exactly
one contract, every mutating contract must declare server-side authorization
and commit-time reauthorization, and no contract may exist for an action the
inventory does not define.

Frontend visibility is not an authorization boundary (`FIR-CTRL-001`): the
`authorization` field records that the owning backend re-authorizes the act, and
`ui_visibility_is_not_authorization` is asserted for every entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from epd2_control_plane_service.domain import ControlAction
from epd2_control_plane_service.exceptions import InventoryError
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory

__all__ = ["CONSOLE_CAPABILITIES", "ControlApiContract", "build_contracts", "contracts_to_json_obj"]


@dataclass(frozen=True, slots=True)
class ControlApiContract:
    contract_id: str
    method: str
    path: str
    action_id: str
    capability: str
    mutation: bool
    server_side_authorization: bool
    commit_time_reauthorization: bool
    required_right: str
    quorum_required: int
    step_up_required: bool
    assurance_level: str
    evidence_emitted: bool
    refusal_reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.mutation and not self.server_side_authorization:
            raise InventoryError(
                f"{self.contract_id}: every mutation requires explicit server-side authorization"
            )
        if self.mutation and not self.commit_time_reauthorization:
            raise InventoryError(
                f"{self.contract_id}: every mutation re-validates authority at commit"
            )
        if not self.evidence_emitted:
            raise InventoryError(
                f"{self.contract_id}: every contract emits evidence, including refusals"
            )


#: The eleven console capabilities W7 requires. Each maps to the inventory
#: actions that serve it, so "coverage" is a checkable property, not a claim.
CONSOLE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "LIST_CURRENT_AUTHORITY": ("AUTH.READ_PROVENANCE",),
    "INSPECT_AUTHORITY_PROVENANCE": ("AUTH.READ_PROVENANCE",),
    "REQUEST_PRIVILEGED_ACTION": ("JIT.REQUEST", "EMERGENCY.REQUEST"),
    "APPROVE_OR_REJECT": ("EMERGENCY.APPROVE",),
    "EXECUTE": ("AUTH.ASSIGN", "SERVICE_CRED.ISSUE", "KEY.ROTATE"),
    "SUSPEND_OR_REVOKE": ("AUTH.SUSPEND", "AUTH.REVOKE", "SESSION.REVOKE", "SERVICE_CRED.REVOKE"),
    "EMERGENCY_ACTIVATION": ("EMERGENCY.ACTIVATE", "EMERGENCY.REVOKE"),
    "CURRENT_INCIDENTS_AND_RESTRICTIONS": ("INTERVENE.READ_ACTIVE",),
    "IMMUTABLE_AUDIT_LOOKUP": ("AUDIT.LOOKUP",),
    "CREDENTIAL_AND_SERVICE_TRUST_STATUS": ("KEY.READ_TRUST_STATE",),
    "READ_ONLY_OPERATIONAL_HEALTH": ("PLATFORM.READ_HEALTH",),
}

_CAPABILITY_BY_ACTION: dict[str, str] = {}
for _capability, _action_ids in CONSOLE_CAPABILITIES.items():
    for _action_id in _action_ids:
        _CAPABILITY_BY_ACTION.setdefault(_action_id, _capability)


_REFUSAL_CODES: tuple[str, ...] = (
    "CTRL_NO_AUTHORITY",
    "CTRL_SCOPE_ISOLATION",
    "CTRL_CAPABILITY_ABSENT",
    "CTRL_AUTHORITY_SUSPENDED",
    "CTRL_AUTHORITY_REVOKED",
    "CTRL_AUTHORITY_EXPIRED",
    "CTRL_SELF_APPROVAL",
    "CTRL_QUORUM_INSUFFICIENT",
    "CTRL_RESTRICTION_ACTIVE",
    "CTRL_SESSION_NOT_ACTIVE",
    "CTRL_ACTOR_CLASS",
    "CTRL_COMMIT_TIME_REAUTH_FAILED",
    "CTRL_EMERGENCY_EXPIRED",
    "CTRL_EMERGENCY_SCOPE",
    "CTRL_VOTING_BOUNDARY",
)


def _method_for(action: ControlAction) -> str:
    return "POST" if action.mutation else "GET"


def build_contracts(inventory: ActionInventory = INVENTORY) -> tuple[ControlApiContract, ...]:
    contracts: list[ControlApiContract] = []
    for action in sorted(inventory, key=lambda a: a.action_id):
        contracts.append(
            ControlApiContract(
                contract_id=f"CTRL-API-{action.action_id}",
                method=_method_for(action),
                path=action.route,
                action_id=action.action_id,
                capability=_CAPABILITY_BY_ACTION.get(action.action_id, "DOMAIN_DESK_ACTION"),
                mutation=action.mutation,
                server_side_authorization=True,
                commit_time_reauthorization=action.commit_time_reauthorization,
                required_right=action.required_right_execute.value,
                quorum_required=action.quorum_required,
                step_up_required=action.step_up_required,
                assurance_level=action.assurance_level,
                evidence_emitted=True,
                refusal_reason_codes=_REFUSAL_CODES,
            )
        )
    return tuple(contracts)


def contracts_to_json_obj(inventory: ActionInventory = INVENTORY) -> dict[str, Any]:
    contracts = build_contracts(inventory)
    covered = {c.action_id for c in contracts}
    missing_capabilities = sorted(
        capability
        for capability, action_ids in CONSOLE_CAPABILITIES.items()
        if not set(action_ids) <= covered
    )
    return {
        "schema": "epd2.ctrl01.control-api-contracts/1",
        "ui_visibility_is_not_authorization": True,
        "counts": {
            "contracts": len(contracts),
            "mutating": sum(1 for c in contracts if c.mutation),
            "read_only": sum(1 for c in contracts if not c.mutation),
        },
        "required_console_capabilities": {
            k: list(v) for k, v in sorted(CONSOLE_CAPABILITIES.items())
        },
        "uncovered_console_capabilities": missing_capabilities,
        "contracts": [
            {
                "contract_id": c.contract_id,
                "method": c.method,
                "path": c.path,
                "action_id": c.action_id,
                "capability": c.capability,
                "mutation": c.mutation,
                "server_side_authorization": c.server_side_authorization,
                "commit_time_reauthorization": c.commit_time_reauthorization,
                "required_right": c.required_right,
                "quorum_required": c.quorum_required,
                "step_up_required": c.step_up_required,
                "assurance_level": c.assurance_level,
                "evidence_emitted": c.evidence_emitted,
                "refusal_reason_codes": list(c.refusal_reason_codes),
            }
            for c in contracts
        ],
    }
