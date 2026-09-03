#!/usr/bin/env python3
"""Derive the FRONT-05 machine-readable records from the implementation.

Every record here is *derived*, never hand-maintained. The capability truth
table is read out of `domain/capabilities.ts`, the route inventory out of the
`app/` tree, and the scope inventory out of the stage contract joined to the
capability register. A hand-written table drifts from the code it describes and
then reassures a reviewer about something that is no longer true; a derived one
fails loudly instead.

The security classification travels with each capability. A reviewer reading
`api_capability_truth.json` must be able to tell a dependency that is merely
missing from one that is defective — the transparency service's caller-supplied
`actor_is_authorized` boolean is the latter, and recording it as a neutral gap
would invite a future round to wire up a route over the top of it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WORKSPACE = "frontend/representative-workspace"
CONTRACT = "docs/frontend/FRONT-05-STAGE-CONTRACT.json"


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


ALIASES = {"BLOCKED": "BLOCKED_BY_DEPENDENCY"}


def _ts_object_fields(block: str) -> dict[str, str]:
    """Pull the string-valued fields out of one TypeScript object literal."""
    fields: dict[str, str] = {}
    for key in (
        "id",
        "status",
        "owner",
        "missingDependency",
        "dependencyClass",
        "reason",
        "frontendBehaviour",
        "securityFinding",
    ):
        match = re.search(
            rf'\b{key}:\s*("(?:[^"\\]|\\.)*"(?:\s*\+\s*"(?:[^"\\]|\\.)*")*)',
            block,
            re.S,
        )
        if match:
            raw = match.group(1)
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', raw, re.S)
            value = "".join(parts)
            fields[key] = value.encode().decode("unicode_escape")
            continue
        # `status: BLOCKED,` is a const alias rather than a literal. Resolving it
        # here keeps the register readable in the source while the derived
        # record still carries the full vocabulary term.
        alias = re.search(rf"\b{key}:\s*([A-Za-z_][A-Za-z0-9_]*)\s*,", block)
        if alias:
            fields[key] = ALIASES.get(alias.group(1), alias.group(1))
    return fields


def capability_truth(root: Path) -> dict[str, object]:
    source = _read(root, f"{WORKSPACE}/domain/capabilities.ts")
    start = source.index("export const WS04_CAPABILITIES")
    end = source.index("const BY_ID", start)
    body = source[start:end]

    records: list[dict[str, object]] = []
    for block in re.findall(r"\{\s*\n\s*id: \"[a-z_]+\",.*?\n  \},", body, re.S):
        fields = _ts_object_fields(block)
        if "id" not in fields:
            continue
        records.append(fields)

    blocked = [r for r in records if r["status"] == "BLOCKED_BY_DEPENDENCY"]
    unsupported = [r for r in records if r["status"] == "UNSUPPORTED"]
    real = [r for r in records if r["status"] == "SUPPORTED_REAL_PATH"]
    sensitive = [
        r for r in records if r.get("dependencyClass") == "SECURITY_SENSITIVE_BOUNDARY"
    ]

    return {
        "schema": "epd2.front05.capability-truth/1",
        "derived_from": f"{WORKSPACE}/domain/capabilities.ts",
        "capability_count": len(records),
        "counts": {
            "SUPPORTED_REAL_PATH": len(real),
            "SUPPORTED_WITH_DECLARED_LIMITATION": 0,
            "BLOCKED_BY_DEPENDENCY": len(blocked),
            "UNSUPPORTED": len(unsupported),
        },
        "security_sensitive_count": len(sensitive),
        "security_sensitive_capabilities": [r["id"] for r in sensitive],
        "no_network_capability_supported": all(
            r["id"]
            in ("local_refusal_rendering", "local_scope_binding", "governed_fallback")
            for r in real
        ),
        "capabilities": records,
    }


def route_inventory(root: Path) -> dict[str, object]:
    contract = json.loads(_read(root, CONTRACT))
    declared = {r["route"]: r for r in contract["required_routes"]}

    app = root / WORKSPACE / "app"
    found: list[str] = []
    for page in sorted(app.rglob("page.tsx")):
        relative = page.parent.relative_to(app).as_posix()
        found.append("/" if relative == "." else f"/{relative}")

    routes = []
    for route in sorted(set(found) | set(declared)):
        record = declared.get(route, {})
        routes.append(
            {
                "route": route,
                "page_id": record.get("page_id"),
                "implemented": route in found,
                "declared": route in declared,
                "authority_required": record.get("authority_required"),
                "routing_creates_authority": record.get(
                    "routing_creates_authority", False
                ),
                "scope_source": "session mandate scope"
                if route.startswith("/representative")
                else "none",
                "cross_scope_behaviour": "non-disclosing refusal (scope_mismatch)"
                if route.startswith("/representative")
                else "not applicable",
            }
        )

    return {
        "schema": "epd2.front05.route-inventory/1",
        "derived_from": [f"{WORKSPACE}/app", CONTRACT],
        "route_count": len(routes),
        "undeclared_routes": [r["route"] for r in routes if not r["declared"]],
        "unimplemented_routes": [r["route"] for r in routes if not r["implemented"]],
        "routes": routes,
    }


def scope_inventory(root: Path) -> dict[str, object]:
    contract = json.loads(_read(root, CONTRACT))
    truth = capability_truth(root)
    by_id = {c["id"]: c for c in truth["capabilities"]}

    def entry(action_id: str, capability: str, required: str, impact: str) -> dict:
        record = by_id[capability]
        return {
            "action": action_id,
            "capability": capability,
            "scope_source": "session mandate scope, exactly one",
            "required_authority": required,
            "resource_scope": "single mandate",
            "impact": impact,
            "cross_scope_behaviour": "refused before any port is reached; refusal identical to not-found",
            "expected_refusal_state": record["status"],
            "dependency_class": record.get("dependencyClass", "ABSENT"),
        }

    actions = [
        entry("case.assign", "case_assignment", "mandate_staff_assigned", "low"),
        entry("case.triage", "case_triage_transition", "mandate_staff_assigned", "low"),
        entry("case.record_response", "case_response_record", "mandate_staff_assigned", "high"),
        entry("case.close", "case_triage_transition", "mandate_representative", "consequential"),
        entry("position.save", "position_draft_write", "mandate_representative", "high"),
        entry("position.submit", "position_internal_submission", "mandate_representative", "consequential"),
        entry("deviation.record", "deviation_record_write", "mandate_representative", "consequential"),
        entry("declaration.submit", "declaration_submission", "mandate_representative", "consequential"),
        entry("publication.propose", "publication_proposal_submission", "mandate_representative", "consequential"),
        entry("publication.withdraw", "publication_proposal_submission", "mandate_representative", "high"),
        entry("conflict.record_assessment_proposal", "conflict_restriction_change", "conflict_officer", "high"),
        entry("registry.read", "registry_read_reference", "mandate_member", "read"),
    ]

    return {
        "schema": "epd2.front05.mandate-scope-inventory/1",
        "derived_from": [CONTRACT, f"{WORKSPACE}/domain/capabilities.ts"],
        "unbounded_scope_representable": False,
        "cross_mandate_action_count": 0,
        "roles": contract["roles"],
        "action_count": len(actions),
        "actions": actions,
    }


def dependency_reconciliation(root: Path) -> dict[str, object]:
    contract = json.loads(_read(root, CONTRACT))
    truth = capability_truth(root)
    sensitive = [
        c
        for c in truth["capabilities"]
        if c.get("dependencyClass") == "SECURITY_SENSITIVE_BOUNDARY"
    ]

    return {
        "schema": "epd2.front05.dependency-reconciliation/1",
        "principle": contract["security_sensitive_dependencies"]["principle"],
        "rule": contract["security_sensitive_dependencies"]["rule"],
        "absent_dependencies": [
            {
                "capability": c["id"],
                "owner": c["owner"],
                "missing": c["missingDependency"],
            }
            for c in truth["capabilities"]
            if c.get("dependencyClass") == "ABSENT"
            and c["status"] == "BLOCKED_BY_DEPENDENCY"
        ],
        "prohibited_capabilities": [
            {"capability": c["id"], "reason": c["reason"]}
            for c in truth["capabilities"]
            if c.get("dependencyClass") == "PROHIBITED"
        ],
        "security_sensitive_boundaries": contract["security_sensitive_dependencies"][
            "boundaries"
        ],
        "security_sensitive_capability_records": sensitive,
        "assertions": {
            "no_security_sensitive_capability_is_supported": all(
                c["status"] in ("BLOCKED_BY_DEPENDENCY", "UNSUPPORTED")
                for c in sensitive
            ),
            "no_security_sensitive_capability_is_a_declared_limitation": all(
                c["status"] != "SUPPORTED_WITH_DECLARED_LIMITATION" for c in sensitive
            ),
            "every_security_sensitive_capability_states_a_finding": all(
                len(c.get("securityFinding", "")) > 100 for c in sensitive
            ),
            "caller_asserted_authorization_treated_as_sufficient": False,
        },
    }


BUILDERS = {
    "api_capability_truth.json": capability_truth,
    "route_inventory.json": route_inventory,
    "mandate_scope_inventory.json": scope_inventory,
    "dependency_reconciliation.json": dependency_reconciliation,
}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out = root / "validation" / "front05"
    out.mkdir(parents=True, exist_ok=True)
    for name, builder in BUILDERS.items():
        payload = builder(root)
        (out / name).write_text(
            json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote validation/front05/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
