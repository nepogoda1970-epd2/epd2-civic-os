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
    PACK09_OPENAPI_PATH,
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


def _pack09_spec() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(PACK09_OPENAPI_PATH.read_text(encoding="utf-8"))
    return parsed


def _pack09_operations() -> list[tuple[str, str, dict[str, Any]]]:
    """Every (path, method, operation) triple in `pack-09.yaml`."""
    spec = _pack09_spec()
    found: list[tuple[str, str, dict[str, Any]]] = []
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                found.append((path, method, operation))
    return found


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


# --- PACK-09 (contracts/openapi/pack-09.yaml) -------------------------------


def test_pack09_openapi_file_is_well_formed_yaml() -> None:
    spec = _pack09_spec()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert len(spec["paths"]) > 0


def test_pack09_each_operation_is_owned_by_exactly_one_service_tag() -> None:
    for path, method, operation in _pack09_operations():
        tags = operation.get("tags", [])
        assert len(tags) == 1, f"{path} {method} must have exactly one owning service tag"


def test_pack09_tags_are_exactly_compliance_service() -> None:
    """ADR-038: PACK-09 has exactly one service. Every operation's `tags`
    value must be `["compliance-service"]` - never a stray/misspelled tag
    and never a PACK-02 through PACK-08 service name, mirroring PACK-04's,
    PACK-05's, PACK-06's and PACK-08's own exact-match assertions."""
    used_tags = {tag for _, _, operation in _pack09_operations() for tag in operation["tags"]}
    assert used_tags == {"compliance-service"}, (
        f"pack-09.yaml must use exactly the tag 'compliance-service', found: {used_tags}"
    )


def test_pack09_every_operation_declares_a_request_body_or_is_a_read() -> None:
    """A write path that documents no request body documents nothing a
    caller can act on. Every PACK-09 POST carries one; GETs must not."""
    for path, method, operation in _pack09_operations():
        if method == "post":
            assert "requestBody" in operation, f"{path} POST declares no requestBody"
        if method == "get":
            assert "requestBody" not in operation, f"{path} GET must not declare a requestBody"


def test_pack09_every_operation_documents_at_least_one_reason_coded_denial() -> None:
    """PACK-09 required invariant 14: every security-, scope-, hold- and
    workflow-denial returns a stable machine-readable reason code. An
    operation whose contract lists only success responses would leave a
    caller unable to distinguish a scope refusal from a hold refusal."""
    for path, method, operation in _pack09_operations():
        codes = set(operation["responses"])
        errors = {code for code in codes if code.startswith("4")}
        assert errors, f"{path} {method} documents no error response at all"
        described = " ".join(
            str(operation["responses"][code].get("description", "")) for code in errors
        )
        assert any(char.isupper() for char in described), (
            f"{path} {method} documents error responses without naming any reason code"
        )


def test_pack09_no_delete_method_exists_for_any_governed_resource() -> None:
    """PACK-09 required invariant 4, at the contract level: destruction is
    a three-step governed workflow (evaluate -> authorize -> execute) that
    produces immutable evidence. There is deliberately no HTTP DELETE
    anywhere in this contract, and no operationId shaped like one."""
    for path, method, operation in _pack09_operations():
        assert method != "delete", f"{path} exposes an HTTP DELETE"
        operation_id = operation.get("operationId", "")
        for fragment in ("deleteRecord", "removeRecord", "purge", "eraseRecord", "dropRecord"):
            assert fragment.lower() not in operation_id.lower(), (
                f"operationId {operation_id!r} suggests a plain delete path, contradicting the "
                "controlled disposal workflow"
            )


def test_pack09_destruction_is_a_three_step_workflow() -> None:
    """The evaluate/authorize/execute triple must all be present: any one
    of them missing would collapse the controlled workflow into something
    a single call could complete."""
    operation_ids = {operation["operationId"] for _, _, operation in _pack09_operations()}
    for required in (
        "evaluateDisposalEligibility",
        "authorizeDestruction",
        "executeDestruction",
    ):
        assert required in operation_ids, f"pack-09.yaml is missing {required}"


def test_pack09_exposes_no_bulk_directory_or_cross_organization_listing() -> None:
    """No path lists governed material across organizations, and no path
    is a directory-shaped export - the same rule PACK-08's own contract
    test applies to its regional scopes."""
    spec = _pack09_spec()
    for path in spec["paths"]:
        lowered = path.lower()
        for fragment in ("directory", "export", "/all", "search"):
            assert fragment not in lowered, (
                f"path {path!r} suggests a bulk/directory-shaped endpoint"
            )
    for path, method, _ in _pack09_operations():
        if method != "get":
            continue
        assert "{" in path, (
            f"GET {path} is an unscoped collection read; every PACK-09 read resolves one "
            "identified resource inside the caller's own scope"
        )


def test_pack09_carries_no_identity_or_voting_field_anywhere_in_the_contract() -> None:
    """PACK-09 required invariants 1, 11 and 12, checked against the
    contract text itself rather than only the implementation: no property
    name anywhere in `pack-09.yaml` is an identity attribute, a global
    person identifier, or a ballot/vote/tally/delegation reference."""
    forbidden_property_names = {
        "account_id",
        "address",
        "authentication_secret",
        "ballot_id",
        "credential_id",
        "date_of_birth",
        "delegation_id",
        "eid_attributes",
        "eid_token",
        "email",
        "first_name",
        "full_name",
        "global_user_id",
        "identity_id",
        "kyc_payload",
        "last_name",
        "member_id",
        "national_id",
        "person_id",
        "phone",
        "result_publication_id",
        "tally_id",
        "user_id",
        "vote_envelope_id",
        "vote_id",
    }
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    found.update(set(value) & forbidden_property_names)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(_pack09_spec())
    assert not found, f"pack-09.yaml declares forbidden propert(ies): {sorted(found)}"


def test_pack09_every_timestamp_property_declares_an_explicit_date_time_format() -> None:
    """Timestamps must have an explicit format so a consumer never has to
    guess whether a value is a date, a naive local time or an instant."""
    offenders: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for name, spec in properties.items():
                    if not isinstance(spec, dict):
                        continue
                    is_timestamp = name.endswith(
                        ("_at", "_at_before", "_at_after", "_from", "_until")
                    )
                    if is_timestamp and spec.get("format") != "date-time":
                        offenders.append(name)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(_pack09_spec())
    assert not offenders, (
        f"timestamp propert(ies) without format: date-time: {sorted(set(offenders))}"
    )


def test_pack09_component_schemas_all_reference_real_contract_files() -> None:
    spec = _pack09_spec()
    components = spec["components"]["schemas"]
    assert components
    for name, entry in components.items():
        reference = entry["$ref"]
        target = (PACK09_OPENAPI_PATH.parent / reference).resolve()
        assert target.exists(), f"{name} references a missing schema file: {reference}"


# --- PACK-09, Architecture & Domain Framework 0.8.1 additions ---------------


def test_pack09_notice_issuance_service_and_effect_are_three_separate_operations() -> None:
    """Framework 0.8.1 hard invariants 39 and 40, at the contract level.

    Collapsing any two of these into one path would produce an API where
    dispatching a notice, or a provider reporting delivery, is
    indistinguishable from the notice having taken legal effect. All
    three must exist separately, and only the third may describe itself
    as establishing effect."""
    operations = {operation["operationId"]: operation for _, _, operation in _pack09_operations()}
    for required in ("issueOfficialNotice", "recordServiceAttempt", "determineServiceEffect"):
        assert required in operations, f"pack-09.yaml is missing {required}"

    for telemetry_operation in ("issueOfficialNotice", "recordServiceAttempt"):
        description = operations[telemetry_operation]["description"].lower()
        assert "starts nothing" in description or "nothing more" in description, (
            f"{telemetry_operation} does not state that it establishes no legal effect"
        )

    effect_description = operations["determineServiceEffect"]["description"].lower()
    assert "only operation" in effect_description


def test_pack09_only_the_notice_effect_operation_can_start_a_deadline() -> None:
    """`triggerProceduralDeadline` documents the two telemetry sources as
    inexpressible, and its request schema's `source` enum omits them."""
    operations = {operation["operationId"]: operation for _, _, operation in _pack09_operations()}
    trigger = operations["triggerProceduralDeadline"]
    source_enum = set(
        trigger["requestBody"]["content"]["application/json"]["schema"]["properties"]["source"][
            "enum"
        ]
    )
    assert "delivery_telemetry" not in source_enum
    assert "read_telemetry" not in source_enum
    assert source_enum == {
        "notice_effect_decision",
        "governed_decision",
        "filing_receipt",
        "statutory_date",
    }


def test_pack09_decision_effect_finality_and_enforceability_are_three_paths() -> None:
    """A single `status` field would let a caller collapse three facts the
    Framework requires to stay apart: a decision may be in effect while
    still appealable, and final while not enforceable."""
    operation_ids = {operation["operationId"] for _, _, operation in _pack09_operations()}
    for required in ("changeDecisionEffect", "makeDecisionFinal", "makeDecisionEnforceable"):
        assert required in operation_ids, f"pack-09.yaml is missing {required}"


def test_pack09_still_exposes_no_delete_for_any_governed_object() -> None:
    """Round 1 asserted this for governed records. The Framework additions
    extend the set: no delete for a legal case, a filing, a hearing, a
    procedural decision, a notice or a record class either. A rejected
    filing keeps its docket position; a closed case is reopened by a
    successor case, never by rewriting the closed one."""
    spec = _pack09_spec()
    for path, methods in spec["paths"].items():
        assert "delete" not in methods, f"{path} exposes an HTTP DELETE"
    for _, _, operation in _pack09_operations():
        operation_id = operation["operationId"].lower()
        for fragment in ("delete", "remove", "erase", "destroycase", "purge"):
            assert fragment not in operation_id, (
                f"operationId {operation['operationId']!r} suggests a delete path"
            )


def test_pack09_declares_no_endpoint_belonging_to_a_later_pack() -> None:
    """Framework 0.8.1 section 13.2 excludes candidacy, assemblies,
    communications channels, finance and document storage from PACK-09.
    PACK-09 publishes typed references to them; it must not publish
    endpoints for them."""
    spec = _pack09_spec()
    forbidden_path_fragments = (
        "candidac",
        "nomination",
        "ballot",
        "assembl",
        "channel",
        "message",
        "template",
        "invoice",
        "donation",
        "ledger",
        "document-store",
        "attachment",
        "upload",
    )
    for path in spec["paths"]:
        lowered = path.lower()
        for fragment in forbidden_path_fragments:
            assert fragment not in lowered, f"path {path!r} belongs to a later pack, not to PACK-09"


def test_pack09_every_framework_operation_documents_a_scope_refusal() -> None:
    """Every new write path can be reached by a caller in the wrong
    organization, so every one of them must document the refusal - a 403
    with a named code, a 404 that discloses nothing, or both."""
    for path, method, operation in _pack09_operations():
        responses = set(operation["responses"])
        assert "403" in responses or "404" in responses, (
            f"{method.upper()} {path} documents no scope refusal at all"
        )


def test_pack09_operation_ids_are_unique() -> None:
    ids = [operation["operationId"] for _, _, operation in _pack09_operations()]
    assert len(ids) == len(set(ids)), "duplicate operationId in pack-09.yaml"
