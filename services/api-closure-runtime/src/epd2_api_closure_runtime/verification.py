"""Independent invariants used by the API-06 anti-cheat suite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ClosureInvariantError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureInvariantError(message)


def verify_snapshot(snapshot: dict[str, Any], root: Path | None = None) -> None:
    inv = snapshot["invariants"]
    _require(snapshot["state"] == "CANDIDATE_NOT_ACCEPTED", "state")
    _require(snapshot["accepted"] is False, "self acceptance")
    _require(inv["undocumented_routes"] == 0, "undocumented route")
    _require(inv["routes_without_auth"] == 0, "route auth")
    _require(inv["mutations_without_authorization"] == 0, "mutation authorization")
    _require(inv["role_policy"] == "bounded_authority", "weakened role")
    _require(inv["regional_scope_enforced"] is True, "regional scope")
    _require(inv["revocation_enforced"] is True, "revocation")
    _require(inv["commit_time_reauthorization"] is True, "commit reauthorization")
    _require(inv["s2s_audience_enforced"] is True, "S2S audience")
    _require(inv["replay_protected"] is True, "replay")
    _require(inv["anonymous_internal_trust"] is False, "anonymous internal")
    _require(inv["voting_member_identifier"] is False, "voting member identifier")
    _require(inv["voting_global_correlation"] is False, "voting correlation")
    _require(inv["response_pii_delta"] == 0, "response PII")
    _require(inv["secret_log_fields"] == [], "secret log")
    _require(inv["stack_trace_exposure"] is False, "stack trace")
    _require(inv["server_owned_fields_assignable"] is False, "mass assignment")
    _require(inv["duplicate_effects"] == 0, "duplicate state")
    _require(inv["partial_success_is_success"] is False, "partial success")
    _require(inv["provider_failure_is_success"] is False, "provider failure")
    _require(inv["database_failure_is_success"] is False, "database failure")
    _require(inv["max_page_size"] <= 100, "page bound")
    _require(inv["max_body_bytes"] <= 1_048_576, "body bound")
    _require(inv["clock_rollback_resurrection"] is False, "clock rollback")
    _require(inv["audit_coverage_percent"] == 100, "audit coverage")
    _require(inv["openapi_drift"] == 0, "OpenAPI drift")
    _require(inv["migration_data_loss"] is False, "migration loss")
    _require(inv["fake_preview_capabilities"] == 0, "fake preview")
    _require(inv["api_closure_blockers"] >= 1, "hidden blockers")
    _require(inv["tested_tree_digest"] == inv["frozen_tree_digest"], "changed after testing")
    _require(inv["frozen_tree_digest"] == inv["packaged_tree_digest"], "package differs")
    if root is not None:
        surface = root / "contracts/api/api06_api_surface.json"
        _require(surface.is_file(), "surface missing")
        _require(
            hashlib.sha256(surface.read_bytes()).hexdigest() == snapshot["surface_sha256"],
            "surface hash",
        )


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())
