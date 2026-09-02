"""Deterministic API-06 surface derivation from accepted API-01 runtime governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def runtime_keys(inventory: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (name, route["method"], route["path"])
        for name, app in inventory["applications"].items()
        for route in app["routes"]
    }


def registry_keys(registry: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (route["upstream"], route["method"], route["upstream_path"])
        for route in registry["routes"]
        if route["status"] != "planned"
    }


def compare_declared_runtime(root: Path) -> tuple[list[str], list[str]]:
    inventory = _load(root / "contracts/api/api01-runtime-inventory.json")
    registry = _load(root / "contracts/api/api01-route-registry.json")
    runtime = runtime_keys(inventory)
    declared = registry_keys(registry)
    return (
        sorted(f"{u} {m} {p}" for u, m, p in runtime - declared),
        sorted(f"{u} {m} {p}" for u, m, p in declared - runtime),
    )


def build_surface(root: Path) -> dict[str, Any]:
    registry = _load(root / "contracts/api/api01-route-registry.json")
    routes = []
    for row in registry["routes"]:
        if row["status"] == "planned":
            continue
        mutation = row["method"] not in {"GET", "HEAD", "OPTIONS"}
        routes.append(
            {
                "route_id": row["route_id"],
                "route": row["path"],
                "method": row["method"],
                "bounded_context": row["domain_owner"],
                "service_owner": row["domain_service"],
                "authentication_requirement": row["authentication"],
                "authorization_requirement": row["gateway_authorization"],
                "authority_source": row["authorization_owner"],
                "tenant_region_scope": "governed-authority-scope",
                "request_schema": f"registry:{row['route_id']}:request",
                "response_schema": f"registry:{row['route_id']}:response",
                "error_model": "epd2.api06.error/1",
                "idempotency_rule": row["idempotency"],
                "transaction_semantics": "commit-time-reauthorization" if mutation else "read-only",
                "audit_requirement": row["audit_required"],
                "privacy_classification": row["trace_profile"],
                "rate_abuse_class": row["rate_limit_class"],
                "external_side_effects": mutation,
                "voting_boundary_relevance": row["ingress_class"] == "VOTING",
                "runtime_upstream": row["upstream"],
                "runtime_path": row["upstream_path"],
            }
        )
    return {
        "schema": "epd2.api06.surface/1",
        "state": "CANDIDATE_NOT_ACCEPTED",
        "source": "contracts/api/api01-route-registry.json",
        "route_count": len(routes),
        "routes": routes,
    }
