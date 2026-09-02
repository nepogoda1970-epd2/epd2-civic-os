#!/usr/bin/env python3
"""API-06 governed 30-case behavioral mutation/anti-cheat runner."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api-closure-runtime/src"))

from epd2_api_closure_runtime.verification import (  # noqa: E402
    ClosureInvariantError,
    load_snapshot,
    verify_snapshot,
)

SNAPSHOT = ROOT / "docs/api/API-06/API06_CLOSURE_SNAPSHOT.json"


def set_invariant(name: str, value: Any) -> Callable[[dict[str, Any]], None]:
    return lambda doc: doc["invariants"].__setitem__(name, value)


MUTATIONS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("M01_UNDOCUMENTED_ROUTE", set_invariant("undocumented_routes", 1)),
    ("M02_ROUTE_WITHOUT_AUTH", set_invariant("routes_without_auth", 1)),
    ("M03_MUTATION_WITHOUT_AUTHORIZATION", set_invariant("mutations_without_authorization", 1)),
    ("M04_WEAKENED_ROLE", set_invariant("role_policy", "admin-everything")),
    ("M05_WRONG_REGION_ACCEPTED", set_invariant("regional_scope_enforced", False)),
    ("M06_REVOKED_AUTHORITY_ACCEPTED", set_invariant("revocation_enforced", False)),
    ("M07_COMMIT_REAUTH_REMOVED", set_invariant("commit_time_reauthorization", False)),
    ("M08_S2S_WRONG_AUDIENCE", set_invariant("s2s_audience_enforced", False)),
    ("M09_REPLAY_ACCEPTED", set_invariant("replay_protected", False)),
    ("M10_ANONYMOUS_INTERNAL_TRUST", set_invariant("anonymous_internal_trust", True)),
    ("M11_MEMBER_ID_IN_VOTING", set_invariant("voting_member_identifier", True)),
    ("M12_GLOBAL_CORRELATION_IN_VOTING", set_invariant("voting_global_correlation", True)),
    ("M13_PII_ADDED_TO_RESPONSE", set_invariant("response_pii_delta", 1)),
    ("M14_SECRET_ADDED_TO_LOG", set_invariant("secret_log_fields", ["provider_secret"])),
    ("M15_STACK_TRACE_EXPOSED", set_invariant("stack_trace_exposure", True)),
    ("M16_HIDDEN_PRIVILEGED_FIELD", set_invariant("server_owned_fields_assignable", True)),
    ("M17_DUPLICATE_MUTATION", set_invariant("duplicate_effects", 1)),
    ("M18_PARTIAL_SUCCESS_REPORTED_SUCCESS", set_invariant("partial_success_is_success", True)),
    ("M19_PROVIDER_FAIL_REPORTED_SUCCESS", set_invariant("provider_failure_is_success", True)),
    ("M20_DB_FAIL_REPORTED_SUCCESS", set_invariant("database_failure_is_success", True)),
    ("M21_UNBOUNDED_PAGE", set_invariant("max_page_size", 100000)),
    ("M22_OVERSIZED_BODY_ACCEPTED", set_invariant("max_body_bytes", 1073741824)),
    ("M23_CLOCK_ROLLBACK_REVIVAL", set_invariant("clock_rollback_resurrection", True)),
    ("M24_AUDIT_ENTRY_OMITTED", set_invariant("audit_coverage_percent", 99)),
    ("M25_OPENAPI_MISMATCH", set_invariant("openapi_drift", 1)),
    ("M26_MIGRATION_DATA_LOSS", set_invariant("migration_data_loss", True)),
    ("M27_FAKE_PREVIEW_SUPPORTED", set_invariant("fake_preview_capabilities", 1)),
    ("M28_BLOCKER_HIDDEN", set_invariant("api_closure_blockers", 0)),
    ("M29_CANDIDATE_CHANGED_AFTER_TEST", set_invariant("tested_tree_digest", "changed")),
    ("M30_PACKAGE_DIFFERS_FROM_FREEZE", set_invariant("packaged_tree_digest", "changed")),
]


def run_mutations() -> dict[str, Any]:
    base = load_snapshot(SNAPSHOT)
    verify_snapshot(base, ROOT)
    rows = []
    for name, mutate in MUTATIONS:
        candidate = copy.deepcopy(base)
        mutate(candidate)
        try:
            verify_snapshot(candidate, ROOT)
        except ClosureInvariantError as exc:
            rows.append({"id": name, "result": "DETECTED", "reason": str(exc)})
        else:
            rows.append({"id": name, "result": "MISSED"})
    detected = sum(row["result"] == "DETECTED" for row in rows)
    return {
        "schema": "epd2.api06.mutations/1",
        "state": "CANDIDATE_NOT_ACCEPTED",
        "mutation_count": len(rows),
        "detected": detected,
        "missed": len(rows) - detected,
        "result": "PASS" if detected == len(rows) else "FAIL",
        "mutations": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="validation/api06/mutation_result.json")
    args = parser.parse_args()
    result = run_mutations()
    target = ROOT / args.out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"API06_MUTATIONS:{result['result']}:{result['detected']}/{result['mutation_count']}")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
