"""Validates `contracts/openapi/pack-02.yaml` against pack section 11's
minimum operation list, and that it reflects service boundaries (no path
returns identity data together with a credential - the identity-leakage
half of this is covered in `test_ct00_08_identity_leakage.py`).

Also validates `contracts/openapi/pack-03.yaml` (added alongside, not
replacing, the PACK-02 assertions above - this file previously assumed
there was exactly one OpenAPI contract file in the repository; PACK-03
adds a second, sibling one): it exists, parses as well-formed OpenAPI 3.x,
and every operation's `tags` value is a subset of the six PACK-03 service
names (mirroring PACK-02's own
`test_each_operation_is_owned_by_exactly_one_service_tag` check, applied
to the new file).

Also validates `contracts/openapi/pack-04.yaml` (added alongside, not
replacing, the PACK-02/PACK-03 assertions above): it exists, parses as
well-formed OpenAPI 3.x, and every operation's `tags` value is exactly
`["transparency-service"]` (ADR-011's single-service decomposition - a
one-service pack has no "subset of many services" question to check;
this is a stricter, exact-match assertion for that reason).

Also validates `contracts/openapi/pack-05.yaml` (added alongside, not
replacing, the PACK-02/PACK-03/PACK-04 assertions above): it exists,
parses as well-formed OpenAPI 3.x, and every operation's `tags` value is
exactly `["governance-service"]` (ADR-016's single-service
decomposition, mirroring PACK-04's own exact-match assertion). Also
checks that `contracts/openapi/pack-03.yaml`'s new `invalidateBallot`
operation (ADR-017 Option B) is tagged `voting-service`, not
`governance-service` - it is physically owned by voting-service even
though it reads a GovernanceDecision produced by governance-service.

Requires PyYAML; skipped locally (see LOCAL_VERIFICATION.md), run for real
in CI.
"""

from __future__ import annotations

from typing import Any

import pytest
from _schema_helpers import (
    OPENAPI_PATH,
    PACK03_OPENAPI_PATH,
    PACK03_SERVICE_DIRS,
    PACK04_OPENAPI_PATH,
    PACK05_OPENAPI_PATH,
)

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

#: PACK-03's own six service names, as used for OpenAPI `tags` - identical
#: strings to `PACK03_SERVICE_DIRS` (the directory names double as the
#: canonical service/tag names throughout this monorepo).
_PACK03_SERVICE_NAMES = set(PACK03_SERVICE_DIRS)


def _spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack03_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK03_OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack04_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK04_OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack05_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK05_OPENAPI_PATH.read_text(encoding="utf-8"))
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


# --- PACK-03 (contracts/openapi/pack-03.yaml) -------------------------------


def test_pack03_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack03_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack03_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack03_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack03_tags_are_a_subset_of_the_six_pack03_service_names() -> None:
    """Every operation's `tags` value in `pack-03.yaml` must name one of
    the six real PACK-03 services (`initiative-service`,
    `deliberation-service`, `moderation-service`, `voting-service`,
    `tally-service`, `delegation-service`) - never a stray/misspelled tag,
    and never a PACK-02 service name (PACK-03's own contract owns only
    PACK-03 paths)."""
    spec = _pack03_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags, "expected at least one tagged operation in pack-03.yaml"
    unexpected = used_tags - _PACK03_SERVICE_NAMES
    assert not unexpected, (
        f"pack-03.yaml uses tag(s) outside the six PACK-03 services: {unexpected}"
    )


# --- PACK-04 (contracts/openapi/pack-04.yaml) -------------------------------


def test_pack04_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack04_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack04_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack04_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack04_tags_are_exactly_transparency_service() -> None:
    """ADR-011: PACK-04 has exactly one service. Every operation's `tags`
    value in `pack-04.yaml` must be `["transparency-service"]` - never a
    stray/misspelled tag, and never a PACK-02/03 service name (PACK-04's
    own contract owns only PACK-04 paths)."""
    spec = _pack04_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags == {"transparency-service"}, (
        f"pack-04.yaml must use exactly the tag 'transparency-service', found: {used_tags}"
    )


# --- PACK-05 (contracts/openapi/pack-05.yaml) -------------------------------


def test_pack05_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack05_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack05_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack05_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack05_tags_are_exactly_governance_service() -> None:
    """ADR-016: PACK-05 has exactly one service. Every operation's `tags`
    value in `pack-05.yaml` must be `["governance-service"]` - never a
    stray/misspelled tag, and never a PACK-02/03/04 service name
    (PACK-05's own contract owns only PACK-05 paths)."""
    spec = _pack05_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags == {"governance-service"}, (
        f"pack-05.yaml must use exactly the tag 'governance-service', found: {used_tags}"
    )


def test_pack05_bootstrap_seed_command_has_no_openapi_path() -> None:
    """PACK-05 required scope item 6: the deployment-time bootstrap seed
    command is not exposed through normal API. Structurally verified: no
    operationId in pack-05.yaml ever mentions "bootstrap" or "seed"."""
    spec = _pack05_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation_id = operation.get("operationId", "")
            lowered = operation_id.lower()
            assert "bootstrap" not in lowered and "seed" not in lowered, (
                f"{path} {method} operationId {operation_id!r} suggests the bootstrap seed "
                "command is exposed through the API contract, contradicting required scope item 6"
            )


def test_pack03_invalidate_ballot_operation_is_tagged_voting_service() -> None:
    """ADR-017 Option B: `invalidate_ballot` is physically owned by
    voting-service (PACK-03), not governance-service, even though it
    reads a GovernanceDecision. Its OpenAPI operation must live in
    `pack-03.yaml` tagged `voting-service`, never in `pack-05.yaml`."""
    pack03_spec = _pack03_spec()
    found = False
    for path_item in pack03_spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if operation.get("operationId") == "invalidateBallot":
                found = True
                assert operation.get("tags") == ["voting-service"], (
                    f"invalidateBallot must be tagged voting-service, not {operation.get('tags')}"
                )
    assert found, "expected an invalidateBallot operation in pack-03.yaml"

    pack05_spec = _pack05_spec()
    pack05_operation_ids = {
        operation.get("operationId")
        for path_item in pack05_spec["paths"].values()
        for method, operation in path_item.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }
    assert "invalidateBallot" not in pack05_operation_ids, (
        "invalidateBallot must not also appear in pack-05.yaml - it is owned by voting-service"
    )
