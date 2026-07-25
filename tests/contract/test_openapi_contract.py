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

Also validates `contracts/openapi/pack-07.yaml` (added alongside, not
replacing, the PACK-02 through PACK-06 assertions above): it exists,
parses as well-formed OpenAPI 3.x, and every operation's `tags` value is a
subset of PACK-07's two real service names (`eligibility-service`,
`membership-service`) - mirroring PACK-03's own "subset of many services"
check rather than PACK-04/05/06's exact-match check, since PACK-07 (like
PACK-03) has more than one owning service. Also checks that the four
ADR-027 narrow cross-pack reads (`get_identity_participation_claims`,
`check_authentication_step_up_satisfied`,
`get_membership_derived_claims`, `read_participant_eligibility_decision`)
have no OpenAPI path of their own, mirroring PACK-06's own
`verify_role_assignment_for_action` precedent check.

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
    PACK06_OPENAPI_PATH,
    PACK07_OPENAPI_PATH,
    PACK07_SERVICE_DIRS,
    PACK08_OPENAPI_PATH,
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

#: PACK-07's own two service names, as used for OpenAPI `tags`. NOT simply
#: `set(PACK07_SERVICE_DIRS)` - that constant (see `_schema_helpers.py`)
#: intentionally lists only `membership-service` (PACK-07's one wholly new
#: service directory); `eligibility-service` is PACK-07's *other* owning
#: service, but it is a pre-existing PACK-02 directory extended in place,
#: so it lives in `PACK02_SERVICE_DIRS` instead. Both are real PACK-07
#: OpenAPI tags regardless of which directory-grouping constant they fall
#: under.
_PACK07_SERVICE_NAMES = set(PACK07_SERVICE_DIRS) | {"eligibility-service"}


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


def _pack06_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK06_OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack07_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK07_OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack08_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK08_OPENAPI_PATH.read_text(encoding="utf-8"))
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


# --- PACK-06 (contracts/openapi/pack-06.yaml) -------------------------------


def test_pack06_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack06_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack06_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack06_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack06_tags_are_exactly_ai_processing_service() -> None:
    """ADR-021: PACK-06 has exactly one service. Every operation's `tags`
    value in `pack-06.yaml` must be `["ai-processing-service"]` - never a
    stray/misspelled tag, and never a PACK-02/03/04/05 service name
    (PACK-06's own contract owns only PACK-06 paths)."""
    spec = _pack06_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags == {"ai-processing-service"}, (
        f"pack-06.yaml must use exactly the tag 'ai-processing-service', found: {used_tags}"
    )


def test_pack06_verify_role_assignment_for_action_has_no_openapi_path() -> None:
    """ADR-022: `verify_role_assignment_for_action` is a narrow, internal,
    cross-pack read `ai-processing-service`'s own commands call directly
    - never a PACK-06 HTTP endpoint in its own right."""
    spec = _pack06_spec()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation_id = operation.get("operationId", "")
            assert "verifyRoleAssignment" not in operation_id, (
                f"operationId {operation_id!r} suggests verify_role_assignment_for_action is "
                "exposed as its own PACK-06 endpoint, contradicting ADR-022"
            )


# --- PACK-07 (contracts/openapi/pack-07.yaml) -------------------------------


def test_pack07_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack07_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack07_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack07_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack07_tags_are_a_subset_of_the_two_pack07_service_names() -> None:
    """Every operation's `tags` value in `pack-07.yaml` must name one of
    the two real PACK-07 owning services (`eligibility-service`,
    `membership-service`) - never a stray/misspelled tag, and never a
    PACK-02 through PACK-06 service name (PACK-07's own contract owns
    only PACK-07 paths). Mirrors PACK-03's own "subset of many services"
    check rather than the single-service packs' exact-match check, since
    PACK-07 (like PACK-03) has more than one owning service."""
    spec = _pack07_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags, "expected at least one tagged operation in pack-07.yaml"
    unexpected = used_tags - _PACK07_SERVICE_NAMES
    assert not unexpected, (
        f"pack-07.yaml uses tag(s) outside the two PACK-07 services: {unexpected}"
    )


def test_pack07_both_services_are_actually_used_as_tags() -> None:
    """Sanity check the other direction from the subset test above: both
    real PACK-07 services must actually own at least one operation each -
    a spec that (say) only ever tagged `eligibility-service` would still
    pass the subset check but would silently be missing membership-service
    entirely."""
    spec = _pack07_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags == _PACK07_SERVICE_NAMES, (
        f"expected both PACK-07 services to be used as tags, found: {used_tags}"
    )


def test_pack07_adr027_narrow_cross_pack_reads_have_no_openapi_path() -> None:
    """ADR-027: `get_identity_participation_claims`,
    `check_authentication_step_up_satisfied` (identity-service),
    `get_membership_derived_claims`, and
    `read_participant_eligibility_decision` (membership-service) are
    narrow, internal, cross-pack reads one specific other service's own
    commands call directly - never exposed as their own PACK-07 HTTP
    endpoints, mirroring PACK-06's own `verify_role_assignment_for_action`
    precedent check."""
    spec = _pack07_spec()
    forbidden_operation_id_fragments = (
        "getIdentityParticipationClaims",
        "checkAuthenticationStepUpSatisfied",
        "getMembershipDerivedClaims",
        "readParticipantEligibilityDecision",
    )
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation_id = operation.get("operationId", "")
            for fragment in forbidden_operation_id_fragments:
                assert fragment not in operation_id, (
                    f"operationId {operation_id!r} suggests {fragment} is exposed as its own "
                    "PACK-07 endpoint, contradicting ADR-027"
                )


# --- PACK-08 (contracts/openapi/pack-08.yaml) -------------------------------


def test_pack08_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack08_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack08_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    spec = _pack08_spec()
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tags = operation.get("tags", [])
            assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack08_tags_are_exactly_organization_service() -> None:
    """ADR-032 through ADR-037: PACK-08 has exactly one service. Every
    operation's `tags` value in `pack-08.yaml` must be
    `["organization-service"]` - never a stray/misspelled tag, and never
    a PACK-02 through PACK-07 service name (PACK-08's own contract owns
    only PACK-08 paths)."""
    spec = _pack08_spec()
    used_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            used_tags.update(operation.get("tags", []))
    assert used_tags == {"organization-service"}, (
        f"pack-08.yaml must use exactly the tag 'organization-service', found: {used_tags}"
    )


def test_pack08_lifecycle_transition_commands_have_no_openapi_path() -> None:
    """Task section 19's own 'minimal reference APIs only' instruction:
    organization lifecycle-transition commands (activate/suspend/
    dissolve/merge/split/declare_successor) exist in the application
    layer but are deliberately not exposed as their own HTTP paths in
    this minimal reference contract - mirroring PACK-05's own precedent
    of omitting its bootstrap-seed command."""
    spec = _pack08_spec()
    forbidden_operation_id_fragments = (
        "activateOrganization",
        "suspendOrganization",
        "dissolveOrganization",
        "mergeOrganization",
        "splitOrganization",
        "declareSuccessor",
    )
    for path_item in spec["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation_id = operation.get("operationId", "")
            for fragment in forbidden_operation_id_fragments:
                assert fragment not in operation_id, (
                    f"operationId {operation_id!r} suggests {fragment} is exposed as its own "
                    "PACK-08 endpoint, contradicting the minimal reference API scope"
                )


def test_pack08_no_bulk_cross_regional_directory_endpoint() -> None:
    """Task section 19: 'no bulk cross-regional directory endpoint' and
    'no public member directory' - every PACK-08 GET operation is scoped
    to a specific id or a specific (scope_type, scope_reference) pair,
    never an unscoped list-everything query."""
    spec = _pack08_spec()
    for path in spec["paths"]:
        lowered = path.lower()
        assert "directory" not in lowered, f"path {path!r} suggests a directory-shaped endpoint"
