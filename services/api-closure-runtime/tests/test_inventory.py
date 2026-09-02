from __future__ import annotations

import json
from pathlib import Path

from epd2_api_closure_runtime.inventory import build_surface, compare_declared_runtime

ROOT = Path(__file__).resolve().parents[3]


def test_declared_surface_equals_runtime_derived_surface():
    runtime_only, declared_only = compare_declared_runtime(ROOT)
    assert runtime_only == []
    assert declared_only == []


def test_committed_api06_surface_is_deterministic():
    committed = json.loads((ROOT / "contracts/api/api06_api_surface.json").read_text())
    assert committed == build_surface(ROOT)


def test_every_route_has_all_closure_fields():
    surface = build_surface(ROOT)
    required = {
        "route",
        "method",
        "bounded_context",
        "service_owner",
        "authentication_requirement",
        "authorization_requirement",
        "authority_source",
        "tenant_region_scope",
        "request_schema",
        "response_schema",
        "error_model",
        "idempotency_rule",
        "transaction_semantics",
        "audit_requirement",
        "privacy_classification",
        "rate_abuse_class",
        "external_side_effects",
        "voting_boundary_relevance",
    }
    assert surface["route_count"] == 91
    assert all(required <= set(row) for row in surface["routes"])


def test_no_documented_but_dead_or_runtime_only_route_exists():
    surface = build_surface(ROOT)
    keys = {(r["runtime_upstream"], r["method"], r["runtime_path"]) for r in surface["routes"]}
    assert len(keys) == surface["route_count"]


def test_all_mutations_have_transaction_and_idempotency_classification():
    rows = [
        r for r in build_surface(ROOT)["routes"] if r["method"] not in {"GET", "HEAD", "OPTIONS"}
    ]
    assert len(rows) == 60
    assert all(r["transaction_semantics"] == "commit-time-reauthorization" for r in rows)
    assert all(r["idempotency_rule"] in {"required", "none", "not_applicable"} for r in rows)


def test_voting_routes_remain_explicitly_classified():
    rows = [r for r in build_surface(ROOT)["routes"] if r["voting_boundary_relevance"]]
    assert rows
    assert all(r["bounded_context"] == "Voting Boundary" for r in rows)


def test_surface_never_carries_client_supplied_actor_identity():
    text = (ROOT / "contracts/api/api06_api_surface.json").read_text().lower()
    assert '"client_supplied_actor_id_allowed": true' not in text


def test_surface_state_is_not_self_accepted():
    surface = build_surface(ROOT)
    assert surface["state"] == "CANDIDATE_NOT_ACCEPTED"
