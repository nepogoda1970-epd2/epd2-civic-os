"""PACK-15 voting-side versioned API.

What this file defends is the property the voting-side catalogue exists
to make structural rather than customary: **this side cannot be asked a
question about a person.** There is no search operation, no endpoint that
takes a participant reference, and no inbound field from which one could
be reconstructed - so "has this member voted" is not a request a client
can express, however it is authenticated.

Three groups:

1. **The catalogue.** Every endpoint is declared `VOTING`, no operation
   name is one the identity side also serves, no consequential endpoint
   waives an obligation, every exemption from authentication says why,
   every reason code it may return is registered, and no declaration
   anywhere names an account, a session or a participant.
2. **The inbound boundary.** A request carrying an identity field is
   refused rather than accommodated by dropping it: whoever sent it built
   a client that had the value, and silently continuing hides that.
3. **The four acts.** Issue, revoke, redeem and status, with the
   refusals that carry the guarantee: one credential per assertion nonce,
   an idempotent retry that mints nothing new, an absorbing `redeemed`
   state, and a status lookup that answers in one shape whether or not
   the reference exists.

The negative assertions are the load-bearing ones. An API that returned
the authorizing nonce beside the credential it authorized, or that let a
spent credential be presented twice, would satisfy every happy path here
and none of the tests that follow them.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from epd2_core.api_contracts import (
    ApiContractError,
    ApiRequest,
    ApiResponseUnsafeError,
    EndpointSpec,
    TrustSide,
    assert_consequential_contract,
    assert_no_endpoint_spans_the_boundary,
    assert_response_safe,
)
from epd2_credential_service.voting_credential_api import (
    CREDENTIAL_CATALOGUE,
    CREDENTIAL_ENDPOINTS,
    PROHIBITED_REQUEST_FIELDS,
    IdentityFieldInVotingRequestError,
    VotingCredentialApi,
    assert_no_identity_field,
    build_voting_credential_api,
)
from epd2_credential_service.voting_credential_application import AssertionVerifier
from epd2_credential_service.voting_credential_runtime import (
    build_voting_credential_service,
)
from epd2_credential_service.voting_credentials import PERMITTED_DELIVERY_CHANNEL

NOW = datetime(2026, 8, 5, 11, 30, tzinfo=UTC)

#: The isolated voting workspace (WS-03). Every endpoint here is refused
#: from anywhere else.
ORIGIN = "https://vote.epd2.example"
FOREIGN_ORIGIN = "https://mitwirkung.epd2.example"
ORIGINS = (ORIGIN,)

AUDIENCE = "voting-credential-issuer"
VALID_SIGNATURE = "valid-reference-signature"

ISSUER = "credential_issuer"
OPERATIONS_OFFICER = "voting_operations_officer"
CLIENT_OPERATOR = "voting_client_operator"

CONTEXT = "vc-1"

REPO_ROOT = Path(__file__).resolve().parents[3]
REASON_CODE_REGISTRY = REPO_ROOT / "contracts" / "reason-codes" / "pack-15.yml"

#: The identity side's operation names, restated here rather than
#: imported. A test in `credential-service` that imported
#: `eligibility-service` would itself be the cross-service edge the
#: architecture forbids, so the disjointness is asserted against a stated
#: list and the *mechanism* that enforces it is asserted separately.
IDENTITY_SIDE_OPERATIONS = frozenset(
    {
        "eligibility.case.open",
        "eligibility.case.read",
        "eligibility.decision.record",
        "assertion.mint",
        "assertion.release.evaluate",
        "handoff.accept",
        "assertion.pickup.consume",
        "dispute.open",
        "dispute.resolve",
    }
)

#: Fragments that would make an operation a question about a person
#: rather than about a credential the caller is already holding.
PERSON_LEVEL_OPERATION_FRAGMENTS = (
    "search",
    "lookup",
    "list",
    "find",
    "query",
    "voted",
    "participant",
    "person",
    "member",
    "holder",
    "account",
    "session",
)


@pytest.fixture
def api() -> Iterator[VotingCredentialApi]:
    with tempfile.TemporaryDirectory() as directory:
        runtime = build_voting_credential_service(
            applied_at=NOW,
            verifier=AssertionVerifier(
                verify=lambda message, signature: signature == VALID_SIGNATURE,
                expected_audience=AUDIENCE,
            ),
            allowed_origins=ORIGINS,
            database=str(Path(directory) / "voting-credentials.db"),
        )
        try:
            yield build_voting_credential_api(
                runtime,
                allowed_origins=ORIGINS,
                canonical_message_of=lambda assertion: assertion.nonce.encode("utf-8"),
            )
        finally:
            runtime.close()


def _request(
    operation: str,
    body: dict[str, Any],
    *,
    origin: str = ORIGIN,
    role: str = CLIENT_OPERATOR,
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


def _terms_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "voting_context_reference": CONTEXT,
        "credential_type": "internal_party_vote",
        "audience_origin": ORIGIN,
        "issuance_window_start": (NOW - timedelta(hours=1)).isoformat(),
        "issuance_window_end": (NOW + timedelta(hours=5)).isoformat(),
        "redemption_window_end": (NOW + timedelta(hours=6)).isoformat(),
        "revocation_cutoff": (NOW + timedelta(hours=4)).isoformat(),
        "timestamp_granularity_seconds": 300,
        "minting_delay_min_seconds": 5,
        "minting_delay_max_seconds": 30,
    }
    payload.update(overrides)
    return payload


def _assertion_payload(**overrides: Any) -> dict[str, Any]:
    """The closed twelve-field crossing artifact, plus its signature."""
    payload: dict[str, Any] = {
        "assertion_id": str(uuid4()),
        "voting_context_reference": CONTEXT,
        "eligibility_result": "approved",
        "eligibility_class": "full_member",
        "organizational_scope": "DE-BE-01",
        "required_assurance_satisfied": True,
        "issued_at_bucket": NOW.isoformat(),
        "expires_at": (NOW + timedelta(hours=2)).isoformat(),
        "audience": AUDIENCE,
        "purpose": "voting_credential_issuance",
        "nonce": "nonce-" + uuid4().hex,
        "status": "picked_up",
        "signature": VALID_SIGNATURE,
        "key_identifier": "test-assertion-signing-key-v1",
    }
    payload.update(overrides)
    return payload


def _issue_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "assertion": _assertion_payload(),
        "terms": _terms_payload(),
        "now": NOW.isoformat(),
        "minting_delay_seconds": 10,
        "delivery_channel": PERMITTED_DELIVERY_CHANNEL,
    }
    body.update(overrides)
    return body


def _issue(api: VotingCredentialApi, *, idempotency_key: str = "idem-1", **overrides: Any) -> Any:
    return api.dispatch(
        _request(
            "credential.issue",
            _issue_body(**overrides),
            role=ISSUER,
            idempotency_key=idempotency_key,
        )
    )


def _revoke(api: VotingCredentialApi, credential_id: str, **overrides: Any) -> Any:
    body: dict[str, Any] = {
        "voting_credential_id": credential_id,
        "terms": _terms_payload(),
        "reason_code": "CREDENTIAL_REVOKED",
        "dual_control_reference": "dual-1",
        "now": NOW.isoformat(),
    }
    body.update(overrides)
    return api.dispatch(
        _request("credential.revoke", body, role=OPERATIONS_OFFICER, idempotency_key="idem-r")
    )


def _redeem(api: VotingCredentialApi, credential_id: str, **overrides: Any) -> Any:
    body: dict[str, Any] = {
        "voting_credential_id": credential_id,
        "terms": _terms_payload(),
        "now": (NOW + timedelta(minutes=5)).isoformat(),
    }
    body.update(overrides)
    return api.dispatch(
        _request("credential.redeem", body, role=CLIENT_OPERATOR, idempotency_key="idem-d")
    )


def _status(api: VotingCredentialApi, credential_id: str) -> Any:
    return api.dispatch(
        _request(
            "credential.status",
            {"voting_credential_id": credential_id},
            role=CLIENT_OPERATOR,
            idempotency_key=None,
            expected_version=None,
        )
    )


def _registered_reason_codes() -> set[str]:
    text = REASON_CODE_REGISTRY.read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", text, flags=re.MULTILINE))


# =============================================================================
# 1. The catalogue
# =============================================================================


def test_the_catalogue_declares_exactly_the_four_credential_operations() -> None:
    assert set(CREDENTIAL_CATALOGUE) == {
        "credential.issue",
        "credential.revoke",
        "credential.redeem",
        "credential.status",
    }
    assert len(CREDENTIAL_ENDPOINTS) == len(CREDENTIAL_CATALOGUE)


def test_every_endpoint_is_declared_on_the_voting_side() -> None:
    for spec in CREDENTIAL_ENDPOINTS:
        assert spec.trust_side is TrustSide.VOTING, spec.operation


def test_no_voting_side_operation_is_also_an_identity_side_operation() -> None:
    assert not set(CREDENTIAL_CATALOGUE) & IDENTITY_SIDE_OPERATIONS


def test_one_operation_declared_on_both_sides_is_refused() -> None:
    """The mechanism behind the disjointness, asserted directly.

    One operation name served by both catalogues is a single call that
    reads both sides - the correlation ADR-093 forbids, arrived at through
    routing rather than through SQL.
    """
    issue = CREDENTIAL_CATALOGUE["credential.issue"]
    twin = EndpointSpec(
        operation=issue.operation,
        area=issue.area,
        trust_side=TrustSide.IDENTITY,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        authorized_roles=("eligibility_officer",),
        reason_codes=("CREDENTIAL_ALREADY_ISSUED",),
    )
    with pytest.raises(ApiContractError):
        assert_no_endpoint_spans_the_boundary([issue, twin])


def test_every_consequential_endpoint_declares_all_three_obligations() -> None:
    for spec in CREDENTIAL_ENDPOINTS:
        assert_consequential_contract(spec)
        if spec.consequential:
            assert spec.idempotency_key_required
            assert spec.version_check_required
            assert spec.audit_evidence_required


def test_every_unauthenticated_endpoint_states_why_it_is_one() -> None:
    """Inside the isolated origin there is no account context to require.

    The exemption is therefore real, and each one names the ADR that made
    it so - an exemption with no reason on the record is how the next one
    gets added without an argument.
    """
    exempt = {spec.operation for spec in CREDENTIAL_ENDPOINTS if spec.unauthenticated_by_design}
    assert exempt == {"credential.issue", "credential.redeem", "credential.status"}
    for spec in CREDENTIAL_ENDPOINTS:
        if spec.unauthenticated_by_design:
            assert spec.justification.strip(), spec.operation


def test_no_endpoint_is_open_to_every_role() -> None:
    for spec in CREDENTIAL_ENDPOINTS:
        assert spec.authorized_roles, spec.operation
        assert all(role.strip() for role in spec.authorized_roles), spec.operation


def test_every_declared_reason_code_is_in_the_pack15_registry() -> None:
    registered = _registered_reason_codes()
    assert registered, "the PACK-15 reason-code registry did not parse"
    for spec in CREDENTIAL_ENDPOINTS:
        unknown = sorted(set(spec.reason_codes) - registered)
        assert not unknown, f"{spec.operation} declares unregistered codes: {unknown}"


def test_no_declaration_anywhere_names_a_participant_an_account_or_a_session() -> None:
    """Not one endpoint may take an identity parameter, under any name.

    Scanned across the whole declaration - operation, area, roles, reason
    codes and justification - because a parameter smuggled in as a reason
    code or a role name would be exactly as effective at reintroducing the
    link as one in the body.
    """
    for spec in CREDENTIAL_ENDPOINTS:
        declaration = " ".join(
            (
                spec.operation,
                spec.area,
                *spec.authorized_roles,
                *spec.reason_codes,
                spec.justification,
            )
        ).lower()
        offending = sorted(field for field in PROHIBITED_REQUEST_FIELDS if field in declaration)
        assert not offending, f"{spec.operation} names {offending}"


def test_no_operation_name_suggests_a_search_or_a_person_level_status() -> None:
    """`credential.status` answers about a reference the caller already
    holds. An operation named for a person, or for a search, would be one
    whose answer is a participation statement about somebody."""
    for spec in CREDENTIAL_ENDPOINTS:
        name = spec.operation.lower()
        offending = [fragment for fragment in PERSON_LEVEL_OPERATION_FRAGMENTS if fragment in name]
        assert not offending, f"{spec.operation} suggests {offending}"


# =============================================================================
# 2. Dispatch: origin, role and the obligations
# =============================================================================


def test_an_unknown_operation_is_refused_by_the_closed_catalogue(
    api: VotingCredentialApi,
) -> None:
    response = api.dispatch(_request("credential.search", {}))
    assert not response.ok
    assert response.reason_code == "API_OPERATION_UNKNOWN"


def test_a_request_from_the_ordinary_workspace_is_refused_and_not_redirected(
    api: VotingCredentialApi,
) -> None:
    """A redirect would make the ordinary workspace a participant in the
    flow, which is the thing origin isolation exists to prevent."""
    response = api.dispatch(
        _request("credential.issue", _issue_body(), origin=FOREIGN_ORIGIN, role=ISSUER)
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"
    assert response.body == {}


def test_a_role_the_endpoint_does_not_name_is_refused(api: VotingCredentialApi) -> None:
    response = api.dispatch(
        _request("credential.revoke", {}, role=CLIENT_OPERATOR, idempotency_key="idem-r")
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_a_consequential_call_without_an_idempotency_key_is_refused(
    api: VotingCredentialApi,
) -> None:
    response = api.dispatch(
        _request("credential.issue", _issue_body(), role=ISSUER, idempotency_key=None)
    )
    assert response.reason_code == "API_IDEMPOTENCY_KEY_REQUIRED"


def test_a_consequential_call_without_an_expected_version_is_refused(
    api: VotingCredentialApi,
) -> None:
    response = api.dispatch(
        _request("credential.issue", _issue_body(), role=ISSUER, expected_version=None)
    )
    assert response.reason_code == "API_VERSION_CHECK_REQUIRED"


def test_a_status_lookup_needs_neither_an_idempotency_key_nor_a_version(
    api: VotingCredentialApi,
) -> None:
    assert _status(api, str(uuid4())).ok


def test_an_unauthenticated_endpoint_is_reachable_without_a_role(
    api: VotingCredentialApi,
) -> None:
    """Requiring a session inside the isolated origin would recreate the
    link the origin removes (ADR-090)."""
    response = api.dispatch(
        _request("credential.issue", _issue_body(), role="", idempotency_key="idem-anon")
    )
    assert response.ok


def test_a_malformed_credential_reference_is_refused_without_being_echoed(
    api: VotingCredentialApi,
) -> None:
    response = _status(api, "not-a-uuid")
    assert response.reason_code == "API_REQUEST_MALFORMED"
    assert response.body == {}


# =============================================================================
# 3. The inbound identity boundary
# =============================================================================


@pytest.mark.parametrize(
    "field",
    ["participant_reference", "account_id", "person_id", "session_id", "context_pseudonym"],
)
def test_a_request_carrying_an_identity_field_is_refused(
    api: VotingCredentialApi, field: str
) -> None:
    """Refused, not sanitized.

    Dropping the field and continuing would serve a client that had the
    value in hand and believed this side would act on it; the refusal is
    what makes that client's author find out.
    """
    response = _issue(api, **{field: "whatever-it-was"})
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


def test_the_identity_field_scan_names_the_offending_field(
    api: VotingCredentialApi,
) -> None:
    assert_no_identity_field({"voting_credential_id": str(uuid4())})
    with pytest.raises(IdentityFieldInVotingRequestError) as refusal:
        assert_no_identity_field({"membership_id": "m-1", "terms": {}})
    assert "membership_id" in str(refusal.value)


def test_a_redemption_carrying_an_identity_field_is_refused(
    api: VotingCredentialApi,
) -> None:
    issued = _issue(api)
    assert issued.ok
    response = _redeem(api, issued.body["voting_credential_id"], participant_reference="p-1")
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


# =============================================================================
# 4. Issuance
# =============================================================================


def test_an_issued_credential_never_carries_the_nonce_that_authorized_it(
    api: VotingCredentialApi,
) -> None:
    """Returning the nonce beside the credential reference would be the
    ADR-093 pairing in a payload rather than in a table - and a payload is
    the easier of the two to log."""
    response = _issue(api)
    assert response.ok
    assert set(response.body) == {"voting_credential_id", "status", "expires_at"}
    assert response.body["status"] == "issued"
    assert "nonce" not in response.body
    assert "assertion_id" not in response.body
    assert_response_safe(response.body)


def test_a_retried_issuance_returns_the_first_credential_and_mints_nothing(
    api: VotingCredentialApi,
) -> None:
    body = _issue_body()
    first = api.dispatch(
        _request("credential.issue", body, role=ISSUER, idempotency_key="idem-retry")
    )
    second = api.dispatch(
        _request("credential.issue", body, role=ISSUER, idempotency_key="idem-retry")
    )
    assert first.ok and second.ok
    assert first.body["voting_credential_id"] == second.body["voting_credential_id"]


def test_one_assertion_nonce_authorizes_exactly_one_credential(
    api: VotingCredentialApi,
) -> None:
    """The voting-side half of the split exactly-once rule.

    The identity side allows one assertion per participation unit; this
    side allows one credential per nonce. Neither holds the other's
    identifier, and between them the effect is exactly-once.
    """
    assertion = _assertion_payload()
    assert _issue(api, idempotency_key="idem-a", assertion=assertion).ok
    response = _issue(api, idempotency_key="idem-b", assertion=assertion)
    assert response.reason_code == "ASSERTION_ALREADY_USED"


def test_delivery_outside_the_isolated_origin_is_refused(
    api: VotingCredentialApi,
) -> None:
    response = _issue(api, delivery_channel="email")
    assert response.reason_code == "DELIVERY_CHANNEL_REFUSED"


def test_an_assertion_that_does_not_verify_authorizes_nothing(
    api: VotingCredentialApi,
) -> None:
    response = _issue(api, assertion=_assertion_payload(signature="forged"))
    assert response.reason_code == "ASSERTION_INVALID"


def test_an_issuance_outside_the_governed_window_is_refused(
    api: VotingCredentialApi,
) -> None:
    response = _issue(
        api,
        terms=_terms_payload(issuance_window_end=(NOW - timedelta(minutes=1)).isoformat()),
    )
    assert response.reason_code == "CREDENTIAL_ISSUANCE_WINDOW_CLOSED"


# =============================================================================
# 5. Revocation and redemption
# =============================================================================


def test_a_revocation_names_a_credential_and_can_name_nothing_else(
    api: VotingCredentialApi,
) -> None:
    """`credential.revoke` has no participant parameter, so "revoke this
    person's vote" is not a request the interface can carry."""
    issued = _issue(api)
    assert issued.ok
    response = _revoke(api, issued.body["voting_credential_id"])
    assert response.ok
    assert response.body["status"] == "revoked"
    assert set(response.body) == {"voting_credential_id", "status"}


def test_revoking_a_reference_no_credential_answers_to_is_refused(
    api: VotingCredentialApi,
) -> None:
    response = _revoke(api, str(uuid4()))
    assert response.reason_code == "CREDENTIAL_NOT_FOUND"


def test_a_redeemed_credential_can_no_longer_be_revoked(
    api: VotingCredentialApi,
) -> None:
    """`redeemed` is absorbing. A revocation after the fact would be an
    administrative act with nothing to act on, and recording one would
    suggest a participation had been withdrawn when it had not."""
    issued = _issue(api)
    assert _redeem(api, issued.body["voting_credential_id"]).ok
    response = _revoke(api, issued.body["voting_credential_id"])
    assert response.reason_code == "CREDENTIAL_ALREADY_REDEEMED"


def test_a_revocation_after_the_cutoff_is_refused(api: VotingCredentialApi) -> None:
    issued = _issue(api)
    response = _revoke(
        api,
        issued.body["voting_credential_id"],
        now=(NOW + timedelta(hours=5)).isoformat(),
    )
    assert response.reason_code == "CREDENTIAL_REVOCATION_CUTOFF_PASSED"


def test_a_redemption_hands_back_a_capability_that_is_not_the_credential(
    api: VotingCredentialApi,
) -> None:
    """PACK-16 receives the continuation capability and nothing else. If
    it were a function of the credential identifier, the ballot stage
    would hold the credential after all."""
    issued = _issue(api)
    response = _redeem(api, issued.body["voting_credential_id"])
    assert response.ok
    assert response.body["continuation_capability"]
    assert response.body["continuation_capability"] != issued.body["voting_credential_id"]
    assert response.body["redemption_reference"] != issued.body["voting_credential_id"]
    assert_response_safe(response.body)


def test_a_second_presentation_of_a_spent_credential_is_a_replay(
    api: VotingCredentialApi,
) -> None:
    issued = _issue(api)
    assert _redeem(api, issued.body["voting_credential_id"]).ok
    response = _redeem(api, issued.body["voting_credential_id"])
    assert response.reason_code == "CREDENTIAL_REPLAY_DETECTED"


# =============================================================================
# 6. Status, and what a response may never carry
# =============================================================================


def test_an_unknown_reference_answers_in_the_same_shape_as_a_withdrawn_one(
    api: VotingCredentialApi,
) -> None:
    """The lookup must not be an oracle.

    If an unknown reference answered in a different shape from a
    credential that exists, anyone holding a list of candidate references
    could learn which of them were issued - without ever holding one.
    """
    issued = _issue(api)
    assert _revoke(api, issued.body["voting_credential_id"]).ok
    known = _status(api, issued.body["voting_credential_id"])
    unknown = _status(api, str(uuid4()))
    assert known.ok and unknown.ok
    assert set(known.body) == set(unknown.body)
    assert set(known.body) == {
        "status_class",
        "voting_context_reference",
        "expires_at_bucket",
    }


def test_a_response_may_not_pair_a_credential_with_an_assertion() -> None:
    """The two reference families may not meet in a payload, at any depth.

    Either alone is a reference somebody legitimately holds. Together they
    are the map between a participant and a ballot that ADR-093 makes
    inexpressible in storage, reassembled in transit.
    """
    assert_response_safe({"voting_credential_id": str(uuid4()), "status": "issued"})
    assert_response_safe({"assertion_reference": "a-1"})
    with pytest.raises(ApiResponseUnsafeError):
        assert_response_safe({"voting_credential_id": str(uuid4()), "issued_for": {"nonce": "n-1"}})


# =============================================================================
# Regressions: the boundary refuses at every depth, and never crashes
# =============================================================================


def test_an_identity_field_nested_inside_the_assertion_is_refused(
    api: VotingCredentialApi,
) -> None:
    """A top-level-only scan would be worth very little here.

    The inbound bodies are nested (`assertion`, `terms`), so the shape a
    caller would actually send an identity field in is a nested one.
    `assert_response_safe` walks every depth on the way out; the way in
    has to match, or the rule holds only against the clumsiest client.
    """
    body = _issue_body()
    body["assertion"]["person_id"] = "p-1"
    response = api.dispatch(
        _request("credential.issue", body, role=CLIENT_OPERATOR, idempotency_key="idem-x")
    )
    assert not response.ok
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


def test_an_identity_field_nested_inside_the_terms_is_refused(
    api: VotingCredentialApi,
) -> None:
    body = _issue_body()
    body["terms"]["participant_reference"] = "participant-1"
    response = api.dispatch(
        _request("credential.issue", body, role=CLIENT_OPERATOR, idempotency_key="idem-x")
    )
    assert not response.ok
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


def test_a_minting_delay_outside_the_governed_window_is_reason_coded(
    api: VotingCredentialApi,
) -> None:
    """A client-controlled number is a malformed request, not a crash.

    The domain raises a bare `ValueError` for an out-of-range delay, and a
    bare exception has no reason code, so the dispatcher would re-raise it
    and the boundary would fail open into a stack trace. Bounding the
    value where it arrives is what keeps that a refusal.
    """
    response = api.dispatch(
        _request(
            "credential.issue",
            _issue_body(minting_delay_seconds=10_000),
            role=CLIENT_OPERATOR,
            idempotency_key="idem-x",
        )
    )
    assert not response.ok
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_revocation_without_a_second_signature_is_refused(
    api: VotingCredentialApi,
) -> None:
    """`DUAL_CONTROL_REQUIRED` is declared on this endpoint, so a path has
    to be able to return it.

    A declared reason code no code path can produce is a contract that
    reads stricter than the system is - which is worse than not declaring
    it, because a reviewer reads the contract.
    """
    issued = _issue(api)
    assert issued.ok, issued.reason_code
    response = _revoke(api, issued.body["voting_credential_id"], dual_control_reference=None)
    assert not response.ok
    assert response.reason_code == "DUAL_CONTROL_REQUIRED"


def test_every_declared_reason_code_on_credential_issue_has_a_path_or_a_reason() -> None:
    """The declared list and the raisable set are checked against each
    other, so neither drifts silently."""
    declared = set(CREDENTIAL_CATALOGUE["credential.issue"].reason_codes)
    assert "API_REQUEST_MALFORMED" in declared
    assert "ASSERTION_AUDIENCE_MISMATCH" in declared
    assert "ASSERTION_CONTEXT_MISMATCH" in declared


def test_an_assertion_whose_assurance_was_not_met_is_refused(
    api: VotingCredentialApi,
) -> None:
    """The assurance flag crosses the boundary so this side can act on it.

    The identity side is the only side that can evaluate assurance, and it
    records the outcome in the crossing artifact. Carrying that flag
    across and never reading it would make it decoration, and the failure
    mode of decoration in an assurance control is a credential issued
    against an assertion whose assurance requirement was not met.
    """
    body = _issue_body()
    body["assertion"]["required_assurance_satisfied"] = False
    response = api.dispatch(
        _request("credential.issue", body, role=CLIENT_OPERATOR, idempotency_key="idem-a")
    )
    assert not response.ok
    assert response.reason_code == "ELIGIBILITY_ASSURANCE_INSUFFICIENT"
