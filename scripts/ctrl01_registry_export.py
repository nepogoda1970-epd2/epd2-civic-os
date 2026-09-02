#!/usr/bin/env python3
"""Export the FIR-CTRL-001 Control Plane Registry from the governed inventory.

The registry is generated, never hand-maintained: a hand-written CSV would drift
from the runtime the moment an action changed. Running this script is the only
supported way to update it, and gate G22 detects a CSV edited by hand.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "services" / "control-plane-service" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from epd2_control_plane_service.inventory import INVENTORY, NO_UI_DECISIONS  # noqa: E402

TARGET = REPO_ROOT / "docs" / "ctrl" / "CTRL-01" / "EPD2_Control_Plane_Registry.csv"

COLUMNS = [
    "console_id",
    "desk_id",
    "workspace",
    "origin",
    "role",
    "action_id",
    "authority_action_set",
    "organization_scope",
    "backend_service",
    "route",
    "authentication_assurance",
    "step_up_required",
    "maker_checker_dual_control",
    "incompatible_roles",
    "sensitive_data_classes",
    "audit_evidence_obligation",
    "break_glass_eligible",
    "break_glass_notification",
    "activation_state",
    "governing_fir",
]

WORKSPACE = {
    "CONSOLE_SECURITY": "security-operations",
    "CONSOLE_IDENTITY": "identity-operations",
    "CONSOLE_GOVERNANCE": "party-governance",
    "CONSOLE_OVERSIGHT": "independent-oversight",
    "CONSOLE_OPERATIONS": "platform-operations",
    "CONSOLE_WORKDESK": "domain-work-desks",
}

ORIGIN = {
    "CONSOLE_SECURITY": "https://security.ctrl.epd2.invalid",
    "CONSOLE_IDENTITY": "https://identity.ctrl.epd2.invalid",
    "CONSOLE_GOVERNANCE": "https://governance.ctrl.epd2.invalid",
    "CONSOLE_OVERSIGHT": "https://oversight.ctrl.epd2.invalid",
    "CONSOLE_OPERATIONS": "https://operations.ctrl.epd2.invalid",
    "CONSOLE_WORKDESK": "https://desks.ctrl.epd2.invalid",
}

BACKEND = {
    "authority": "organization-service + governance-service",
    "intervention": "organization-service + privileged-access-service",
    "credential": "identity-service + credential-service",
    "session": "identity-service",
    "privileged": "privileged-access-service",
    "emergency": "privileged-access-service",
    "service_identity": "identity-service (workload identity)",
    "key_trust": "key/trust platform (external custody)",
    "audit": "audit-core",
    "privacy": "compliance-service",
    "protected_reporting": "privileged-access-service (separate custody)",
    "casework": "compliance-service",
    "records": "document-service",
    "procurement": "finance-service",
    "membership": "membership-service",
    "offices": "organization-service",
    "assemblies": "deliberation-service",
    "election_admin": "governance-service",
    "finance": "finance-service",
    "correspondence": "document-service",
    "ai_oversight": "ai-processing-service",
    "transparency": "transparency-service",
    "citizen_office": "transparency-service",
    "representative": "transparency-service",
    "moderation": "moderation-service",
    "platform": "data-plane-service",
}


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with TARGET.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for action in sorted(INVENTORY, key=lambda a: (a.console_id, a.desk_id, a.action_id)):
            incompatible = ";".join(
                sorted(f"{a.value}!={b.value}" for a, b in action.incompatible_rights)
            )
            writer.writerow(
                [
                    action.console_id,
                    action.desk_id,
                    WORKSPACE.get(action.console_id, "unassigned"),
                    ORIGIN.get(action.console_id, "unassigned"),
                    action.desk_id.replace("DESK_", ""),
                    action.action_id,
                    action.required_right_execute.value,
                    action.scope_level.value,
                    BACKEND.get(action.domain, "unassigned"),
                    action.route,
                    action.assurance_level,
                    "yes" if action.step_up_required else "no",
                    f"quorum={action.quorum_required};"
                    f"four_eyes={'yes' if action.four_eyes else 'no'}",
                    incompatible,
                    ";".join(sorted(action.sensitive_data_classes)) or "none",
                    "immutable" if action.immutable_evidence_required else "none",
                    "yes" if action.emergency_eligible else "no",
                    "out-of-band notification + mandatory post-use review"
                    if action.emergency_eligible
                    else "n/a",
                    "PRESEAL_NOT_ACCEPTED",
                    ";".join(action.governing_fir_refs),
                ]
            )
        for entry in NO_UI_DECISIONS:
            writer.writerow(
                [
                    "NO_CONSOLE",
                    "NO_DESK",
                    "n/a",
                    "n/a",
                    entry["role"],
                    "NO_UI",
                    "none",
                    "n/a",
                    "n/a",
                    "n/a",
                    "n/a",
                    "no",
                    "n/a",
                    "n/a",
                    "none",
                    "n/a",
                    "no",
                    "n/a",
                    "NO_UI_DECISION",
                    entry["governing_fir"],
                ]
            )
    print(
        f"wrote {TARGET.relative_to(REPO_ROOT)} ({len(list(INVENTORY)) + len(NO_UI_DECISIONS)} "
        f"rows)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
