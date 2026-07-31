"""PACK-15 governance-side versioned API.

The catalogue is checked for the properties that have to hold for every
endpoint - obligations, trust side, scoped roles, registered reason codes
- and each handler for its happy path and its principal refusal.

The interesting assertions are the negative ones. A registry that can be
configured without naming the version acted on, activated by one person
twice, or reported as suspended while it is still running would satisfy
every positive test here and none of the ones below.
"""

from __future__ import annotations

import re
import sqlite3
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from epd2_core.api_contracts import (
    ApiContractError,
    ApiRequest,
    EndpointSpec,
    TrustSide,
    assert_response_safe,
    build_catalogue,
)
from epd2_governance_service.voting_context_api import (
    CONFIGURATION_ROLES,
    REGISTRY_READER_ROLES,
    VOTING_CONTEXT_CATALOGUE,
    VOTING_CONTEXT_ENDPOINTS,
    VotingContextApi,
    VotingContextRuntime,
    build_voting_context_api,
)
from epd2_governance_service.voting_context_sql_storage import (
    SqlVotingContextStore,
    open_voting_context_registry,
)
from epd2_governance_service.voting_contexts import (
    FORBIDDEN_FIELD_NAMES,
    compute_snapshot_digest,
)

NOW = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)

ORIGIN = "https://governance.epd2.example"
FOREIGN_ORIGIN = "https://vote.epd2.example"
ORIGINS = (ORIGIN,)

OFFICER = "voting_operations_officer"
AUDITOR = "security_auditor"

REPO_ROOT = Path(__file__).resolve().parents[3]
REASON_CODE_REGISTRY = REPO_ROOT / "contracts" / "reason-codes" / "pack-15.yml"


@pytest.fixture
def api() -> Iterator[VotingContextApi]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_voting_context_registry(Path(directory) / "registry.db", applied_at=NOW)
        try:
            yield build_voting_context_api(
                VotingContextRuntime(
                    connection=connection, contexts=SqlVotingContextStore(connection)
                ),
                allowed_origins=ORIGINS,
            )
        finally:
            connection.close()


def _request(
    operation: str,
    body: dict[str, Any],
    *,
    origin: str = ORIGIN,
    role: str = OFFICER,
    idempotency_key: str | None = "idem-1",
    expected_version: int | None = 0,
) -> ApiRequest:
    return ApiRequest(
        operation=operation,
        origin=origin,
        body=body,
        actor_role=role,
        idempotency_key=idempotency_key,
        expected_version=expected_version,
    )


def _draft_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "voting_context_reference": "vc-1",
        "voting_type": "internal_party_vote",
        "organizational_scope": "DE-BE",
        "voting_window_start": (NOW + timedelta(days=1)).isoformat(),
        "voting_window_end": (NOW + timedelta(days=3)).isoformat(),
        "issuance_window_start": NOW.isoformat(),
        "issuance_window_end": (NOW + timedelta(days=2)).isoformat(),
        "revocation_cutoff": (NOW + timedelta(days=2)).isoformat(),
        "eligibility_rule_set_reference": "rs-1",
        "eligibility_rule_set_version": "1.0.0",
        "required_assurance": "substantial",
        "participation_class": "full_member",
        "privacy_profile": "standard",
        "audit_profile": "standard",
        "eligible_population": 400,
    }
    body.update(overrides)
    return body


def _activation_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "voting_context_reference": "vc-1",
        "first_approver_principal": "ops-1",
        "first_approver_role": OFFICER,
        "second_approver_principal": "sec-1",
        "second_approver_role": AUDITOR,
        "grant_reference": "grant-7",
        "now": NOW.isoformat(),
    }
    body.update(overrides)
    return body


def _draft(api: VotingContextApi, **overrides: Any) -> Any:
    return api.dispatch(_request("voting_context.draft", _draft_body(**overrides)))


def _configure(api: VotingContextApi, version: int, **changes: Any) -> Any:
    body: dict[str, Any] = {"voting_context_reference": "vc-1"}
    body.update(changes or {"required_assurance": "high"})
    return api.dispatch(_request("voting_context.configure", body, expected_version=version))


def _activate(api: VotingContextApi, version: int, **overrides: Any) -> Any:
    return api.dispatch(
        _request(
            "voting_context.activate",
            _activation_body(**overrides),
            expected_version=version,
        )
    )


def _registered_reason_codes() -> set[str]:
    text = REASON_CODE_REGISTRY.read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", text, flags=re.MULTILINE))


# =============================================================================
# 1. The catalogue
# =============================================================================


def test_the_catalogue_declares_exactly_the_five_registry_operations() -> None:
    assert set(VOTING_CONTEXT_CATALOGUE) == {
        "voting_context.draft",
        "voting_context.configure",
        "voting_context.activate",
        "voting_context.read",
        "voting_context.transition",
    }


def test_every_endpoint_is_neutral_and_in_the_voting_context_area() -> None:
    """The registry holds configuration, so no endpoint takes a side.

    An endpoint declared on a side would be an endpoint that could return
    a fact about a participation, and there is no such fact here to
    return."""
    for spec in VOTING_CONTEXT_ENDPOINTS:
        assert spec.trust_side is TrustSide.NEUTRAL
        assert spec.area == "voting_context"


def test_every_consequential_endpoint_takes_all_three_obligations() -> None:
    for spec in VOTING_CONTEXT_ENDPOINTS:
        if spec.consequential:
            assert spec.idempotency_key_required
            assert spec.version_check_required
            assert spec.audit_evidence_required


def test_only_the_read_endpoint_waives_the_obligations() -> None:
    waiving = {spec.operation for spec in VOTING_CONTEXT_ENDPOINTS if not spec.consequential}
    assert waiving == {"voting_context.read"}


def test_every_write_endpoint_is_scoped_to_the_configuration_roles() -> None:
    for spec in VOTING_CONTEXT_ENDPOINTS:
        if spec.consequential:
            assert spec.authorized_roles == CONFIGURATION_ROLES


def test_reading_is_wider_than_writing_but_still_scoped() -> None:
    """Both sides read the registry; neither may configure it."""
    assert set(CONFIGURATION_ROLES) < set(REGISTRY_READER_ROLES)
    assert "voting_client_operator" not in REGISTRY_READER_ROLES
    assert "tally_authority" not in REGISTRY_READER_ROLES


def test_no_governance_endpoint_is_unauthenticated_by_design() -> None:
    """Every act here is administrative and has a named actor."""
    for spec in VOTING_CONTEXT_ENDPOINTS:
        assert not spec.unauthenticated_by_design


def test_every_declared_reason_code_is_in_the_pack15_registry() -> None:
    registered = _registered_reason_codes()
    assert registered, "the PACK-15 reason-code registry did not parse"
    for spec in VOTING_CONTEXT_ENDPOINTS:
        unknown = sorted(set(spec.reason_codes) - registered)
        assert not unknown, f"{spec.operation} declares unregistered codes: {unknown}"


def test_a_consequential_endpoint_may_not_waive_an_obligation() -> None:
    """The rule that keeps the catalogue honest as it grows."""
    with pytest.raises(ApiContractError):
        build_catalogue(
            [
                EndpointSpec(
                    operation="voting_context.shortcut",
                    area="voting_context",
                    trust_side=TrustSide.NEUTRAL,
                    consequential=True,
                    idempotency_key_required=False,
                    version_check_required=True,
                    audit_evidence_required=True,
                    authorized_roles=(OFFICER,),
                    reason_codes=("VOTING_CONTEXT_NOT_ACTIVE",),
                )
            ]
        )


def test_an_unknown_operation_is_refused_by_the_closed_catalogue(
    api: VotingContextApi,
) -> None:
    response = api.dispatch(_request("voting_context.delete", {}))
    assert not response.ok
    assert response.reason_code == "API_OPERATION_UNKNOWN"


# =============================================================================
# 2. Obligations, origin and role
# =============================================================================


def test_a_consequential_call_without_an_idempotency_key_is_refused(
    api: VotingContextApi,
) -> None:
    response = api.dispatch(_request("voting_context.draft", _draft_body(), idempotency_key=None))
    assert response.reason_code == "API_IDEMPOTENCY_KEY_REQUIRED"


def test_a_consequential_call_without_a_version_is_refused(api: VotingContextApi) -> None:
    response = api.dispatch(_request("voting_context.draft", _draft_body(), expected_version=None))
    assert response.reason_code == "API_VERSION_CHECK_REQUIRED"


def test_a_request_from_a_foreign_origin_is_refused(api: VotingContextApi) -> None:
    response = api.dispatch(_request("voting_context.draft", _draft_body(), origin=FOREIGN_ORIGIN))
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_a_role_the_endpoint_does_not_name_is_refused(api: VotingContextApi) -> None:
    response = api.dispatch(
        _request("voting_context.draft", _draft_body(), role="eligibility_officer")
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_reading_needs_neither_an_idempotency_key_nor_a_version(
    api: VotingContextApi,
) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.read",
            {"voting_context_reference": "vc-1"},
            role="eligibility_officer",
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.ok


# =============================================================================
# 3. Draft
# =============================================================================


def test_a_draft_registers_version_one(api: VotingContextApi) -> None:
    response = _draft(api)
    assert response.ok
    assert response.body["version"] == 1
    assert response.body["status"] == "draft"


def test_a_second_draft_of_the_same_reference_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = _draft(api)
    assert response.reason_code == "VOTING_CONTEXT_CONFIGURATION_INVALID"


def test_a_draft_that_expects_an_existing_version_is_refused(api: VotingContextApi) -> None:
    """A create acts on the absence of a version and says so."""
    response = api.dispatch(_request("voting_context.draft", _draft_body(), expected_version=1))
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_draft_carrying_a_participant_field_is_refused(api: VotingContextApi) -> None:
    response = _draft(api, participant_reference="p-1")
    assert response.reason_code == "VOTING_CONTEXT_CONFIGURATION_INVALID"


def test_a_draft_whose_issuance_outlasts_the_vote_is_refused(api: VotingContextApi) -> None:
    response = _draft(api, issuance_window_end=(NOW + timedelta(days=4)).isoformat())
    assert response.reason_code == "VOTING_CONTEXT_CONFIGURATION_INVALID"


def test_a_draft_with_an_unknown_voting_type_is_refused(api: VotingContextApi) -> None:
    response = _draft(api, voting_type="referendum")
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_draft_with_a_naive_timestamp_is_refused(api: VotingContextApi) -> None:
    response = _draft(api, revocation_cutoff="2026-08-05T08:00:00")
    assert response.reason_code == "API_REQUEST_MALFORMED"


# =============================================================================
# 4. Configure
# =============================================================================


def test_configuring_writes_a_successor_version(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = _configure(api, 1, required_assurance="high")
    assert response.ok
    assert response.body["version"] == 2
    assert response.body["supersedes_version"] == 1
    assert response.body["status"] == "configured"


def test_a_configuration_against_a_superseded_version_is_refused(
    api: VotingContextApi,
) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _configure(api, 1, required_assurance="low")
    assert response.reason_code == "VOTING_CONTEXT_VERSION_CONFLICT"


def test_configuring_an_unregistered_reference_is_refused(api: VotingContextApi) -> None:
    response = _configure(api, 1)
    assert response.reason_code == "VOTING_CONTEXT_NOT_FOUND"


def test_a_parameter_the_registry_does_not_version_is_refused(
    api: VotingContextApi,
) -> None:
    """An unknown field is refused rather than dropped: the caller
    believed the registry would act on it."""
    assert _draft(api).ok
    response = _configure(api, 1, turnout_target=90)
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_configuring_an_activated_context_starts_a_new_version(
    api: VotingContextApi,
) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    assert _activate(api, 2).ok
    response = _configure(api, 2, privacy_profile="enhanced")
    assert response.ok
    assert response.body["version"] == 3
    assert response.body["status"] == "configured"


def test_a_configuration_that_states_no_change_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.configure",
            {"voting_context_reference": "vc-1"},
            expected_version=1,
        )
    )
    assert response.reason_code == "API_REQUEST_MALFORMED"


# =============================================================================
# 5. Activation
# =============================================================================


def test_activation_freezes_the_critical_parameters(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2)
    assert response.ok
    assert response.body["status"] == "active"
    assert len(response.body["activation_snapshot_digest"]) == 64
    read = api.dispatch(
        _request(
            "voting_context.read",
            {"voting_context_reference": "vc-1"},
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert read.body["activation_snapshot_digest"] == (response.body["activation_snapshot_digest"])


def test_the_published_digest_commits_to_the_parameters_that_were_read_back(
    api: VotingContextApi,
) -> None:
    """The digest is only useful if it is the digest of what is stored."""
    assert _draft(api).ok
    assert _configure(api, 1).ok
    assert _activate(api, 2).ok
    stored = api.runtime.contexts.get("vc-1", 2)
    assert stored is not None
    assert stored.activation_snapshot is not None
    assert stored.activation_snapshot.snapshot_digest == compute_snapshot_digest(
        stored.critical_parameters()
    )


def test_one_principal_approving_twice_is_not_dual_control(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2, second_approver_principal="ops-1")
    assert response.reason_code == "DUAL_CONTROL_REQUIRED"


def test_a_second_approver_in_the_same_role_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2, second_approver_role=OFFICER)
    assert response.reason_code == "SEPARATION_OF_DUTIES_REFUSED"


def test_activation_without_a_time_boxed_grant_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2, grant_reference="")
    assert response.reason_code == "PRIVILEGED_APPROVAL_MISSING"


def test_an_approver_role_outside_the_matrix_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2, second_approver_role="chief_administrator")
    assert response.reason_code == "PERMISSION_DENIED"


def test_an_approver_role_the_capability_does_not_admit_is_refused(
    api: VotingContextApi,
) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = _activate(api, 2, second_approver_role="independent_auditor")
    assert response.reason_code == "PRIVILEGED_APPROVAL_MISSING"


def test_activating_a_draft_version_is_refused(api: VotingContextApi) -> None:
    """A context is activated from `configured`, never straight from a
    draft nobody reviewed."""
    assert _draft(api).ok
    response = _activate(api, 1)
    assert response.reason_code == "VOTING_CONTEXT_NOT_ACTIVE"


def test_the_public_election_profile_is_never_activated(api: VotingContextApi) -> None:
    assert _draft(api, voting_type="public_election_profile").ok
    assert _configure(api, 1).ok
    response = _activate(api, 2)
    assert response.reason_code == "VOTING_CONTEXT_CONFIGURATION_INVALID"


# =============================================================================
# 6. Read
# =============================================================================


def test_reading_without_a_version_returns_the_current_one(api: VotingContextApi) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    response = api.dispatch(
        _request(
            "voting_context.read",
            {"voting_context_reference": "vc-1"},
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.ok
    assert response.body["version"] == 2


def test_reading_an_unregistered_reference_is_refused(api: VotingContextApi) -> None:
    response = api.dispatch(
        _request(
            "voting_context.read",
            {"voting_context_reference": "vc-absent"},
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.reason_code == "VOTING_CONTEXT_NOT_FOUND"


def test_a_read_never_carries_a_participant_field_or_the_electorate_size(
    api: VotingContextApi,
) -> None:
    """The small-electorate flag is what a reader needs; the count itself
    is a disclosure-controlled figure."""
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.read",
            {"voting_context_reference": "vc-1"},
            role="independent_auditor",
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.ok
    assert "eligible_population" not in response.body
    assert not set(response.body) & FORBIDDEN_FIELD_NAMES
    assert response.body["small_electorate"] is False
    assert_response_safe(response.body)


# =============================================================================
# 7. Transition
# =============================================================================


def test_a_permitted_transition_is_recorded(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.transition",
            {
                "voting_context_reference": "vc-1",
                "target_status": "cancelled",
                "dual_control_reference": "dc-3",
            },
            expected_version=1,
        )
    )
    assert response.ok
    assert response.body["status"] == "cancelled"
    assert response.body["previous_status"] == "draft"
    stored = api.runtime.contexts.get("vc-1", 1)
    assert stored is not None and stored.status.value == "cancelled"


def test_cancellation_without_dual_control_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.transition",
            {"voting_context_reference": "vc-1", "target_status": "cancelled"},
            expected_version=1,
        )
    )
    assert response.reason_code == "DUAL_CONTROL_REQUIRED"


def test_a_transition_the_lifecycle_forbids_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.transition",
            {"voting_context_reference": "vc-1", "target_status": "voting_open"},
            expected_version=1,
        )
    )
    assert response.reason_code == "VOTING_CONTEXT_NOT_ACTIVE"


def test_an_unknown_target_status_is_refused(api: VotingContextApi) -> None:
    assert _draft(api).ok
    response = api.dispatch(
        _request(
            "voting_context.transition",
            {"voting_context_reference": "vc-1", "target_status": "paused"},
            expected_version=1,
        )
    )
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_transition_the_registry_will_not_record_is_refused(
    api: VotingContextApi,
) -> None:
    """An activated version's row is frozen, so the store silently
    ignores the write. Reporting success would tell an operator that a
    suspension happened when the context is still running."""
    assert _draft(api).ok
    assert _configure(api, 1).ok
    assert _activate(api, 2).ok
    response = api.dispatch(
        _request(
            "voting_context.transition",
            {"voting_context_reference": "vc-1", "target_status": "suspended"},
            expected_version=2,
        )
    )
    assert response.reason_code == "VOTING_CONTEXT_VERSION_FROZEN"
    stored = api.runtime.contexts.get("vc-1", 2)
    assert stored is not None and stored.status.value == "active"


def test_the_registry_holds_one_row_per_version_after_a_full_lifecycle(
    api: VotingContextApi,
) -> None:
    assert _draft(api).ok
    assert _configure(api, 1).ok
    assert _activate(api, 2).ok
    assert _configure(api, 2, audit_profile="enhanced").ok
    versions = api.runtime.contexts.versions("vc-1")
    assert tuple(item.version for item in versions) == (1, 2, 3)
    assert versions[1].activation_snapshot is not None
    assert versions[2].activation_snapshot is None


def test_the_runtime_holds_a_durable_store(api: VotingContextApi) -> None:
    assert isinstance(api.runtime.contexts, SqlVotingContextStore)
    assert isinstance(api.runtime.connection, sqlite3.Connection)
