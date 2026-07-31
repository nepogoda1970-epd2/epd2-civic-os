"""PACK-15 identity-side versioned API.

What this file defends is the claim the identity-side catalogue makes by
existing: that every operation reachable on this boundary is an
identity-side operation, that it cannot be reached without the
obligations its declaration states, and that nothing it returns carries
what an event on this side would have been refused for.

Three groups:

1. **The catalogue.** Every endpoint is declared `IDENTITY`, no
   consequential endpoint waives an obligation, every exemption from
   authentication says why, every reason code it may return is in the
   central registry, and no operation name is one the voting side also
   serves - because an operation served by both sides is the ADR-093
   correlation reached through routing.
2. **Dispatch.** Origin, role, idempotency key and expected version are
   refused at the boundary rather than trusted, and each refusal carries
   a registered code and never the refused value.
3. **The handlers.** The happy paths, and the refusals that matter: a
   second assertion for one participation unit, a second presentation of
   a single-use handoff artifact, a second consumption of a one-time
   pickup. Each of those is a place where a permissive answer would let
   one participant hold two crossing artifacts.

The load-bearing assertions here are the negative ones. An API that
returned the assertion identifier beside its batch, or that let a
participation unit be minted twice, would satisfy every happy path below
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
    build_catalogue,
)
from epd2_eligibility_service.voting_assertion_issuer import (
    MinimizedDecisionInput,
    TestKeyCustody,
)
from epd2_eligibility_service.voting_eligibility import AssertionPickup
from epd2_eligibility_service.voting_handoff import HandoffBinding, artifact_digest
from epd2_eligibility_service.voting_trust_api import (
    ELIGIBILITY_CATALOGUE,
    ELIGIBILITY_ENDPOINTS,
    AssertionAlreadyMintedForUnitError,
    EligibilityApi,
    build_eligibility_api,
)
from epd2_eligibility_service.voting_trust_runtime import (
    VotingTrustRuntime,
    build_voting_trust_runtime,
)
from epd2_eligibility_service.voting_trust_sql_storage import (
    SqlParticipationUnitLedger,
    open_eligibility_database,
)

NOW = datetime(2026, 8, 4, 9, 0, tzinfo=UTC)

ORIGIN = "https://mitwirkung.epd2.example"
FOREIGN_ORIGIN = "https://vote.epd2.example"
ORIGINS = (ORIGIN,)

AUDIENCE = "voting-credential-issuer"

OFFICER = "eligibility_officer"
REVIEWER = "eligibility_reviewer"
DISPUTE_REVIEWER = "dispute_reviewer"
OPERATIONS_OFFICER = "voting_operations_officer"
CLIENT_OPERATOR = "voting_client_operator"

CONTEXT = "vc-1"
POPULATION = 800

REPO_ROOT = Path(__file__).resolve().parents[3]
REASON_CODE_REGISTRY = REPO_ROOT / "contracts" / "reason-codes" / "pack-15.yml"

#: The voting side's operation names, restated here rather than imported.
#: A test in `eligibility-service` that imported `credential-service`
#: would itself be the cross-service edge the architecture forbids, so the
#: disjointness is asserted against a stated list and the *mechanism* that
#: enforces it is asserted separately below.
VOTING_SIDE_OPERATIONS = frozenset(
    {"credential.issue", "credential.revoke", "credential.redeem", "credential.status"}
)


@pytest.fixture
def api() -> Iterator[EligibilityApi]:
    with tempfile.TemporaryDirectory() as directory:
        runtime = _runtime(Path(directory))
        try:
            yield build_eligibility_api(
                runtime,
                handoff_binding=HandoffBinding(expected_audience=AUDIENCE, allowed_origins=ORIGINS),
                allowed_origins=ORIGINS,
            )
        finally:
            runtime.close()


def _runtime(directory: Path) -> VotingTrustRuntime:
    """Two databases, never one: the factory takes both and defaults neither."""
    return build_voting_trust_runtime(
        applied_at=NOW,
        audience=AUDIENCE,
        eligibility_database=str(directory / "eligibility.db"),
        assertion_issuer_database=str(directory / "issuer.db"),
        custody=TestKeyCustody(),
    )


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


def _case_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "case_id": str(uuid4()),
        "voting_context_reference": CONTEXT,
        "participant_reference": "participant-1",
        "participation_class": "full_member",
        "requested_at": NOW.isoformat(),
    }
    body.update(overrides)
    return body


def _open_case(api: EligibilityApi, **overrides: Any) -> Any:
    return api.dispatch(_request("eligibility.case.open", _case_body(**overrides)))


def _mint_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "voting_context_reference": CONTEXT,
        "eligibility_class": "full_member",
        "organizational_scope": "DE-BE-01",
        "required_assurance_satisfied": True,
        "participation_unit_key": "unit-1",
        "now": NOW.isoformat(),
        "expires_at": (NOW + timedelta(hours=6)).isoformat(),
        "eligible_population": POPULATION,
        "batch_reference": "batch-1",
        "jitter_fraction": 0.5,
    }
    body.update(overrides)
    return body


def _mint(api: EligibilityApi, **overrides: Any) -> Any:
    return api.dispatch(_request("assertion.mint", _mint_body(**overrides), role=OFFICER))


def _handoff_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "artifact_value": "artifact-" + uuid4().hex,
        "voting_context_reference": CONTEXT,
        "audience": AUDIENCE,
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "now": NOW.isoformat(),
    }
    body.update(overrides)
    return body


def _accept_handoff(api: EligibilityApi, **overrides: Any) -> Any:
    return api.dispatch(
        _request("handoff.accept", _handoff_body(**overrides), role=CLIENT_OPERATOR)
    )


def _store_pickup(api: EligibilityApi, *, digest: str) -> None:
    """Put one minted assertion and its one-time pickup in the store.

    Written directly against the stores rather than through `assertion.mint`
    because the mint endpoint deliberately does not hand back the assertion
    identifier, which is exactly the property asserted further down.
    """
    assertion = api.runtime.issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=6),
        eligible_population=POPULATION,
    )
    api.runtime.assertion_store.save_assertion(assertion)
    api.runtime.assertion_store.save_pickup(
        AssertionPickup(
            pickup_id=uuid4(),
            assertion_id=assertion.assertion_id,
            voting_context_reference=CONTEXT,
            handoff_artifact_digest=digest,
            audience_origin=ORIGIN,
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
        )
    )
    api.runtime.assertion_issuer_connection.commit()


def _decision() -> MinimizedDecisionInput:
    return MinimizedDecisionInput(
        voting_context_reference=CONTEXT,
        eligibility_result="approved",
        eligibility_class="full_member",
        organizational_scope="DE-BE-01",
        required_assurance_satisfied=True,
    )


def _registered_reason_codes() -> set[str]:
    text = REASON_CODE_REGISTRY.read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", text, flags=re.MULTILINE))


# =============================================================================
# 1. The catalogue
# =============================================================================


def test_the_catalogue_declares_exactly_the_nine_identity_side_operations() -> None:
    assert set(ELIGIBILITY_CATALOGUE) == {
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
    assert len(ELIGIBILITY_ENDPOINTS) == len(ELIGIBILITY_CATALOGUE)


def test_every_endpoint_is_declared_on_the_identity_side() -> None:
    """An endpoint on this catalogue that named the voting side would be a
    single call able to read both sides, which is the join ADR-093 makes
    inexpressible in SQL and which must stay inexpressible in routing."""
    for spec in ELIGIBILITY_ENDPOINTS:
        assert spec.trust_side is TrustSide.IDENTITY, spec.operation


def test_no_identity_side_operation_is_also_a_voting_side_operation() -> None:
    assert not set(ELIGIBILITY_CATALOGUE) & VOTING_SIDE_OPERATIONS


def test_one_operation_declared_on_both_sides_is_refused() -> None:
    """The mechanism behind the disjointness, asserted directly.

    Without this the property above is an observation about today's two
    lists rather than a rule the tenth endpoint has to obey.
    """
    minted = ELIGIBILITY_CATALOGUE["assertion.mint"]
    twin = EndpointSpec(
        operation=minted.operation,
        area=minted.area,
        trust_side=TrustSide.VOTING,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        authorized_roles=(CLIENT_OPERATOR,),
        reason_codes=("CREDENTIAL_ALREADY_ISSUED",),
    )
    with pytest.raises(ApiContractError):
        assert_no_endpoint_spans_the_boundary([minted, twin])


def test_every_consequential_endpoint_declares_all_three_obligations() -> None:
    for spec in ELIGIBILITY_ENDPOINTS:
        assert_consequential_contract(spec)
        if spec.consequential:
            assert spec.idempotency_key_required
            assert spec.version_check_required
            assert spec.audit_evidence_required


def test_every_unauthenticated_endpoint_states_why_it_is_one() -> None:
    """An exemption with no reason on the record is an exemption nobody
    decided; it is how the next one gets added without argument."""
    exempt = {spec.operation for spec in ELIGIBILITY_ENDPOINTS if spec.unauthenticated_by_design}
    assert exempt == {"handoff.accept", "assertion.pickup.consume"}
    for spec in ELIGIBILITY_ENDPOINTS:
        if spec.unauthenticated_by_design:
            assert spec.justification.strip(), spec.operation


def test_no_endpoint_is_open_to_every_role() -> None:
    for spec in ELIGIBILITY_ENDPOINTS:
        assert spec.authorized_roles, spec.operation
        assert all(role.strip() for role in spec.authorized_roles), spec.operation


def test_every_declared_reason_code_is_in_the_pack15_registry() -> None:
    registered = _registered_reason_codes()
    assert registered, "the PACK-15 reason-code registry did not parse"
    for spec in ELIGIBILITY_ENDPOINTS:
        unknown = sorted(set(spec.reason_codes) - registered)
        assert not unknown, f"{spec.operation} declares unregistered codes: {unknown}"


def test_no_endpoint_may_claim_that_a_participant_voted() -> None:
    """The identity side knows an assertion was minted for a participation
    unit and knows nothing about a ballot. `ALREADY_VOTED` here would be a
    claim this side cannot support from anything it holds."""
    for spec in ELIGIBILITY_ENDPOINTS:
        assert "ALREADY_VOTED" not in spec.reason_codes
        assert "PARTICIPATION_CONFIRMED" not in spec.reason_codes
    assert AssertionAlreadyMintedForUnitError.reason_code == "CREDENTIAL_ALREADY_ISSUED"


def test_a_consequential_endpoint_may_not_waive_an_obligation() -> None:
    with pytest.raises(ApiContractError):
        build_catalogue(
            [
                EndpointSpec(
                    operation="assertion.shortcut",
                    area="assertion",
                    trust_side=TrustSide.IDENTITY,
                    consequential=True,
                    idempotency_key_required=True,
                    version_check_required=True,
                    audit_evidence_required=False,
                    authorized_roles=(OFFICER,),
                    reason_codes=("ASSERTION_ISSUED",),
                )
            ]
        )


# =============================================================================
# 2. Dispatch: origin, role and the obligations
# =============================================================================


def test_an_unknown_operation_is_refused_by_the_closed_catalogue(api: EligibilityApi) -> None:
    response = api.dispatch(_request("assertion.list", {}))
    assert not response.ok
    assert response.reason_code == "API_OPERATION_UNKNOWN"


def test_a_request_from_a_foreign_origin_is_refused(api: EligibilityApi) -> None:
    response = api.dispatch(_request("eligibility.case.open", _case_body(), origin=FOREIGN_ORIGIN))
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_a_role_the_endpoint_does_not_name_is_refused(api: EligibilityApi) -> None:
    response = api.dispatch(_request("eligibility.case.open", _case_body(), role=CLIENT_OPERATOR))
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_a_consequential_call_without_an_idempotency_key_is_refused(
    api: EligibilityApi,
) -> None:
    response = api.dispatch(_request("eligibility.case.open", _case_body(), idempotency_key=None))
    assert response.reason_code == "API_IDEMPOTENCY_KEY_REQUIRED"


def test_a_consequential_call_without_an_expected_version_is_refused(
    api: EligibilityApi,
) -> None:
    response = api.dispatch(_request("eligibility.case.open", _case_body(), expected_version=None))
    assert response.reason_code == "API_VERSION_CHECK_REQUIRED"


def test_an_unauthenticated_endpoint_is_reachable_without_a_role(
    api: EligibilityApi,
) -> None:
    """The participant presenting a handoff artifact has no session on this
    side, and requiring one would mean this boundary learning an account -
    which is the linkage ADR-088 removed."""
    response = api.dispatch(_request("handoff.accept", _handoff_body(), role=""))
    assert response.ok


def test_a_malformed_identifier_is_refused_without_being_echoed(
    api: EligibilityApi,
) -> None:
    response = api.dispatch(
        _request("eligibility.case.read", {"case_id": "not-a-uuid"}, role=REVIEWER)
    )
    assert response.reason_code == "API_REQUEST_MALFORMED"
    assert response.body == {}


def test_a_naive_timestamp_is_refused_at_the_boundary(api: EligibilityApi) -> None:
    response = _open_case(api, requested_at="2026-08-04T09:00:00")
    assert response.reason_code == "API_REQUEST_MALFORMED"


# =============================================================================
# 3. Eligibility cases
# =============================================================================


def test_opening_a_case_confirms_it_without_echoing_the_participant(
    api: EligibilityApi,
) -> None:
    """The participant reference is identity-side data the caller already
    holds; returning it puts it into a second place for no gain."""
    body = _case_body()
    response = _open_case(api, **body)
    assert response.ok
    assert response.body == {"case_id": body["case_id"], "status": "requested"}
    assert "participant_reference" not in response.body
    assert_response_safe(response.body)


def test_reading_a_case_returns_the_stored_facts(api: EligibilityApi) -> None:
    """Reading is the one operation free of the obligations, so it is
    dispatched here with neither an idempotency key nor an expected
    version - and it still never returns the participant."""
    body = _case_body()
    assert _open_case(api, **body).ok
    response = api.dispatch(
        _request(
            "eligibility.case.read",
            {"case_id": body["case_id"]},
            role=REVIEWER,
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.ok
    assert response.body["voting_context_reference"] == CONTEXT
    assert response.body["participation_class"] == "full_member"
    assert response.body["status"] == "requested"
    assert response.body["decision_count"] == 0
    assert "participant_reference" not in response.body


def test_reading_a_case_that_does_not_exist_is_refused(api: EligibilityApi) -> None:
    response = api.dispatch(
        _request(
            "eligibility.case.read",
            {"case_id": str(uuid4())},
            role=REVIEWER,
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.reason_code == "ELIGIBILITY_CASE_NOT_FOUND"


def test_recording_a_decision_names_the_case_and_its_reason_codes(
    api: EligibilityApi,
) -> None:
    body = _case_body()
    assert _open_case(api, **body).ok
    response = api.dispatch(
        _request(
            "eligibility.decision.record",
            {
                "case_id": body["case_id"],
                "status": "approved",
                "reason_codes": ["ELIGIBILITY_APPROVED"],
            },
        )
    )
    assert response.ok
    assert response.body["status"] == "approved"
    assert response.body["reason_codes"] == ("ELIGIBILITY_APPROVED",)


# =============================================================================
# 4. Minting and queued release
# =============================================================================


def test_minting_returns_the_batch_and_never_the_assertion(api: EligibilityApi) -> None:
    """The participant collects the artifact through the one-time pickup.

    An assertion identifier handed back here would be a second copy of it
    in a channel that has an account context attached - the one place the
    crossing artifact must never appear.
    """
    response = _mint(api)
    assert response.ok
    assert set(response.body) == {"status", "batch_reference", "release_not_before"}
    assert response.body["status"] == "minted"
    assert response.body["batch_reference"] == "batch-1"
    assert "assertion_id" not in response.body
    assert "nonce" not in response.body
    assert_response_safe(response.body)


def test_a_second_assertion_for_one_participation_unit_is_refused(
    api: EligibilityApi,
) -> None:
    """The identity-side half of the split exactly-once rule.

    The claim is taken before the mint, so a retry loses on the ledger's
    primary key before a second assertion exists to be handed out.
    """
    assert _mint(api).ok
    response = _mint(api)
    assert response.reason_code == "CREDENTIAL_ALREADY_ISSUED"
    assert api.runtime.participation_ledger.count_minted(CONTEXT) == 1


def test_release_reports_a_cohort_class_and_never_a_cohort_count(
    api: EligibilityApi,
) -> None:
    """An exact cohort size in a small electorate is a participation
    statement about the people in it."""
    assert _mint(api).ok
    entry = api.runtime.assertion_store.pending_batch("batch-1")[0]
    response = api.dispatch(
        _request(
            "assertion.release.evaluate",
            {
                "assertion_id": str(entry.assertion_id),
                "cohort_size": 1,
                "now": entry.cohort_wait_deadline.isoformat(),
                "eligible_population": POPULATION,
            },
            role=OPERATIONS_OFFICER,
        )
    )
    assert response.ok
    assert response.body["release_now"] is True
    assert response.body["below_minimum_cohort"] is True
    assert isinstance(response.body["cohort_size_class"], str)
    assert "cohort_size" not in response.body
    assert_response_safe(response.body)


def test_evaluating_the_release_of_an_unqueued_assertion_is_refused(
    api: EligibilityApi,
) -> None:
    response = api.dispatch(
        _request(
            "assertion.release.evaluate",
            {
                "assertion_id": str(uuid4()),
                "cohort_size": 25,
                "now": NOW.isoformat(),
                "eligible_population": POPULATION,
            },
            role=OPERATIONS_OFFICER,
        )
    )
    assert response.reason_code == "ASSERTION_NOT_FOUND"


# =============================================================================
# 5. The handoff and the one-time pickup
# =============================================================================


def test_an_accepted_handoff_confirms_the_context_and_returns_no_digest(
    api: EligibilityApi,
) -> None:
    """The digest is this side's one-time key. A caller holding it could
    probe whether a given artifact had already been presented."""
    response = _accept_handoff(api)
    assert response.ok
    assert response.body == {"accepted": True, "voting_context_reference": CONTEXT}
    assert "artifact_digest" not in response.body


def test_a_second_presentation_of_one_artifact_is_refused(api: EligibilityApi) -> None:
    body = _handoff_body()
    assert _accept_handoff(api, **body).ok
    response = _accept_handoff(api, **body)
    assert response.reason_code == "HANDOFF_ALREADY_USED"


def test_a_handoff_bound_to_another_audience_is_refused(api: EligibilityApi) -> None:
    response = _accept_handoff(api, audience="tally-service")
    assert response.reason_code == "HANDOFF_AUDIENCE_MISMATCH"


def test_a_handoff_from_an_origin_the_binding_does_not_name_is_refused() -> None:
    """The dispatcher's allowed origins and the handoff binding's are two
    decisions. A deployment that widened the first without widening the
    second must still refuse, or the binding is advisory."""
    with tempfile.TemporaryDirectory() as directory:
        runtime = _runtime(Path(directory))
        try:
            api = build_eligibility_api(
                runtime,
                handoff_binding=HandoffBinding(expected_audience=AUDIENCE, allowed_origins=ORIGINS),
                allowed_origins=(ORIGIN, FOREIGN_ORIGIN),
            )
            response = api.dispatch(
                _request(
                    "handoff.accept",
                    _handoff_body(),
                    origin=FOREIGN_ORIGIN,
                    role=CLIENT_OPERATOR,
                )
            )
            assert response.reason_code == "HANDOFF_ORIGIN_MISMATCH"
        finally:
            runtime.close()


def test_the_one_time_pickup_serves_the_closed_crossing_payload(
    api: EligibilityApi,
) -> None:
    """`wire_payload` is the one place an assertion identifier and a nonce
    legitimately leave this service, and only into the isolated origin."""
    digest = artifact_digest("artifact-pickup-1")
    _store_pickup(api, digest=digest)
    response = api.dispatch(
        _request(
            "assertion.pickup.consume",
            {"handoff_artifact_digest": digest, "now": NOW.isoformat()},
            role=CLIENT_OPERATOR,
        )
    )
    assert response.ok
    payload = response.body["assertion"]
    assert set(payload) == {
        "assertion_id",
        "voting_context_reference",
        "eligibility_result",
        "eligibility_class",
        "organizational_scope",
        "required_assurance_satisfied",
        "issued_at_bucket",
        "expires_at",
        "audience",
        "purpose",
        "nonce",
        "status",
    }
    assert_response_safe(response.body)


def test_a_second_consumption_of_one_pickup_is_refused(api: EligibilityApi) -> None:
    digest = artifact_digest("artifact-pickup-2")
    _store_pickup(api, digest=digest)
    body = {"handoff_artifact_digest": digest, "now": NOW.isoformat()}
    assert api.dispatch(_request("assertion.pickup.consume", body, role=CLIENT_OPERATOR)).ok
    response = api.dispatch(_request("assertion.pickup.consume", body, role=CLIENT_OPERATOR))
    assert response.reason_code == "ASSERTION_PICKUP_ALREADY_USED"


def test_a_pickup_for_an_unknown_digest_is_refused(api: EligibilityApi) -> None:
    response = api.dispatch(
        _request(
            "assertion.pickup.consume",
            {"handoff_artifact_digest": "a" * 64, "now": NOW.isoformat()},
            role=CLIENT_OPERATOR,
        )
    )
    assert response.reason_code == "ASSERTION_NOT_FOUND"


def test_a_response_may_not_pair_an_assertion_with_a_credential(
    api: EligibilityApi,
) -> None:
    """The crossing payload is safe on its own. The same payload beside a
    credential reference is the ADR-093 pairing in a body rather than in a
    table, and is refused before it leaves."""
    digest = artifact_digest("artifact-pickup-3")
    _store_pickup(api, digest=digest)
    response = api.dispatch(
        _request(
            "assertion.pickup.consume",
            {"handoff_artifact_digest": digest, "now": NOW.isoformat()},
            role=CLIENT_OPERATOR,
        )
    )
    assert response.ok
    assert_response_safe(response.body)
    with pytest.raises(ApiResponseUnsafeError):
        assert_response_safe({**response.body, "voting_credential_id": str(uuid4())})


# =============================================================================
# 6. Disputes
# =============================================================================


def test_a_dispute_is_opened_and_resolved_against_a_known_case(
    api: EligibilityApi,
) -> None:
    body = _case_body()
    assert _open_case(api, **body).ok
    opened = api.dispatch(
        _request("dispute.open", {"case_id": body["case_id"]}, role=DISPUTE_REVIEWER)
    )
    assert opened.ok
    assert opened.body["dispute_status"] == "open"
    resolved = api.dispatch(
        _request(
            "dispute.resolve",
            {"case_id": body["case_id"], "outcome": "upheld"},
            role=DISPUTE_REVIEWER,
        )
    )
    assert resolved.ok
    assert resolved.body["dispute_status"] == "resolved"
    assert resolved.body["outcome"] == "upheld"


# =============================================================================
# Regressions: the failure that silently disenfranchises
# =============================================================================


def test_a_failed_mint_does_not_leave_the_participation_unit_claimed() -> None:
    """The worst failure in this flow, and the reason `mint` rolls back.

    `mint_assertion` claims the participation unit before it mints,
    because that ordering is what makes the identity-side half of the
    exactly-once rule survive a retry. The cost of that ordering is that
    a mint which then fails must not leave the claim behind: an
    uncommitted INSERT that the next successful write commits would mark
    the unit as used while no assertion exists, and the participant would
    be refused forever with `CREDENTIAL_ALREADY_ISSUED` for an assertion
    they never received.
    """
    with tempfile.TemporaryDirectory() as directory:
        eligibility_path = Path(directory) / "eligibility.db"
        runtime = build_voting_trust_runtime(
            applied_at=NOW,
            audience=AUDIENCE,
            eligibility_database=str(eligibility_path),
            assertion_issuer_database=str(Path(directory) / "issuer.db"),
            # No custody argument: the default refuses every call, which
            # is exactly the shape of an unconfigured deployment.
        )
        try:
            api = build_eligibility_api(
                runtime,
                handoff_binding=HandoffBinding(expected_audience=AUDIENCE, allowed_origins=ORIGINS),
                allowed_origins=ORIGINS,
            )
            refused = _mint(api)
            assert not refused.ok
            assert refused.reason_code == "SYSTEM_DEPENDENCY_UNAVAILABLE"

            # A later successful write on the same connection must not
            # carry the abandoned claim into the database with it.
            assert _open_case(api).ok
        finally:
            runtime.close()

        verify = open_eligibility_database(eligibility_path, applied_at=NOW)
        try:
            assert SqlParticipationUnitLedger(verify).count_minted(CONTEXT) == 0
        finally:
            verify.close()


def test_the_unit_is_still_mintable_after_a_failed_mint() -> None:
    """The participant is not locked out by a failure that was not theirs."""
    with tempfile.TemporaryDirectory() as directory:
        paths = (
            str(Path(directory) / "eligibility.db"),
            str(Path(directory) / "issuer.db"),
        )
        failing = build_voting_trust_runtime(
            applied_at=NOW,
            audience=AUDIENCE,
            eligibility_database=paths[0],
            assertion_issuer_database=paths[1],
        )
        try:
            refused = _mint(
                build_eligibility_api(
                    failing,
                    handoff_binding=HandoffBinding(
                        expected_audience=AUDIENCE, allowed_origins=ORIGINS
                    ),
                    allowed_origins=ORIGINS,
                )
            )
            assert not refused.ok
        finally:
            failing.close()

        working = build_voting_trust_runtime(
            applied_at=NOW,
            audience=AUDIENCE,
            eligibility_database=paths[0],
            assertion_issuer_database=paths[1],
            custody=TestKeyCustody(),
        )
        try:
            granted = _mint(
                build_eligibility_api(
                    working,
                    handoff_binding=HandoffBinding(
                        expected_audience=AUDIENCE, allowed_origins=ORIGINS
                    ),
                    allowed_origins=ORIGINS,
                )
            )
            assert granted.ok, granted.reason_code
        finally:
            working.close()
