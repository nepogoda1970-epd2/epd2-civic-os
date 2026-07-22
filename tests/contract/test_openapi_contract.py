"""Validates `contracts/openapi/pack-02.yaml` against pack section 11's
minimum operation list, and that it reflects service boundaries (no path
returns identity data together with a credential - the identity-leakage
half of this is covered in `test_ct00_08_identity_leakage.py`).

Requires PyYAML; skipped locally (see LOCAL_VERIFICATION.md), run for real
in CI.
"""

from __future__ import annotations

from typing import Any

import pytest
from _schema_helpers import OPENAPI_PATH

yaml = pytest.importorskip("yaml")

_REQUIRED_OPERATIONS = {
    "recordIdentityVerification",
    "evaluateEligibility",
    "createEligibilitySnapshot",
    "issueParticipationCredential",
    "validateParticipationCredential",
    "revokeParticipationCredential",
    "getAuditEventById",
}


def _spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def test_openapi_file_is_well_formed_yaml() -> None:
    spec = _spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec


def test_all_pack_section_11_operations_are_present() -> None:
    spec = _spec()
    operation_ids = {
        operation["operationId"]
        for path_item in spec["paths"].values()
        for method, operation in path_item.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }
    missing = _REQUIRED_OPERATIONS - operation_ids
    assert not missing, f"OpenAPI contract is missing required operations: {missing}"


def test_no_single_path_returns_both_identity_and_credential_data() -> None:
    """Pack section 11: OpenAPI must not create an endpoint that returns
    identity together with a credential. Checked structurally: no path
    item references both an identity-record schema and a
    participation-credential schema in the same operation."""
    spec = _spec()
    for path, path_item in spec["paths"].items():
        path_text = str(path_item)
        has_identity_ref = "identity-record.schema.json" in path_text
        has_credential_ref = "participation-credential.schema.json" in path_text
        assert not (has_identity_ref and has_credential_ref), (
            f"path {path!r} references both identity-record and "
            f"participation-credential schemas in the same operation"
        )


def test_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"
