"""PACK-15 audit-side versioned API.

Two claims are under test, and only one of them is about endpoints.

The first is ordinary: the catalogue is well formed, the obligations are
not waived, the roles are scoped, every declared reason code is in the
PACK-15 registry, and each handler does what it says on its happy path
and refuses what it says it refuses.

The second is the architectural one. A request that would span the
identity-side and voting-side stream groups has to be refused, and a
runtime that *could* serve one has to be impossible to assemble. The
tests below therefore attack the runtime as well as the API: a store
sharing a connection with the other side, an export log filed beside a
side's records, and two databases claiming the same stream are all
refused at construction, because by request time a shared connection is
already a join anybody holding it can write.
"""

from __future__ import annotations

import re
import sqlite3
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from epd2_audit_core.voting_audit_sql_storage import (
    IDENTITY_SIDE_DATABASE_STREAMS,
    NEUTRAL_DATABASE_STREAMS,
    VOTING_SIDE_DATABASE_STREAMS,
    SqlEvidenceBundleExportStore,
    SqlVotingAuditStreamStore,
    VotingAuditRecord,
    open_identity_side_audit_database,
    open_neutral_audit_database,
    open_voting_side_audit_database,
)
from epd2_audit_core.voting_evidence_api import (
    BUNDLE_EXPORT_ROLES,
    EVIDENCE_CATALOGUE,
    EVIDENCE_ENDPOINTS,
    STREAM_READER_ROLES,
    STREAM_WRITER_ROLES,
    AuditDatabaseNotSeparatedError,
    VotingEvidenceApi,
    VotingEvidenceRuntime,
    build_voting_evidence_api,
)
from epd2_audit_core.voting_evidence_bundle import (
    BUNDLE_SECTIONS,
    AuditStream,
    BundleSigningCustody,
    EvidenceBundleScopeRefusedError,
)
from epd2_core.api_contracts import (
    ApiContractError,
    ApiRequest,
    EndpointSpec,
    TrustSide,
    assert_response_safe,
    build_catalogue,
)

NOW = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)

ORIGIN = "https://audit.epd2.example"
FOREIGN_ORIGIN = "https://vote.epd2.example"
ORIGINS = (ORIGIN,)

WRITER = "voting_operations_officer"
AUDITOR = "independent_auditor"

REPO_ROOT = Path(__file__).resolve().parents[3]
REASON_CODE_REGISTRY = REPO_ROOT / "contracts" / "reason-codes" / "pack-15.yml"

Databases = tuple[sqlite3.Connection, sqlite3.Connection, sqlite3.Connection]


@pytest.fixture
def databases() -> Iterator[Databases]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        identity = open_identity_side_audit_database(root / "audit-identity.db", applied_at=NOW)
        voting = open_voting_side_audit_database(root / "audit-voting.db", applied_at=NOW)
        neutral = open_neutral_audit_database(root / "audit-neutral.db", applied_at=NOW)
        try:
            yield (identity, voting, neutral)
        finally:
            for connection in (identity, voting, neutral):
                connection.close()


def _runtime(databases: Databases) -> VotingEvidenceRuntime:
    identity, voting, neutral = databases
    return VotingEvidenceRuntime(
        identity_side=SqlVotingAuditStreamStore(identity, IDENTITY_SIDE_DATABASE_STREAMS),
        voting_side=SqlVotingAuditStreamStore(voting, VOTING_SIDE_DATABASE_STREAMS),
        neutral=SqlVotingAuditStreamStore(neutral, NEUTRAL_DATABASE_STREAMS),
        exports=SqlEvidenceBundleExportStore(neutral),
        custody=BundleSigningCustody(),
    )


@pytest.fixture
def api(databases: Databases) -> VotingEvidenceApi:
    return build_voting_evidence_api(_runtime(databases), allowed_origins=ORIGINS)


def _request(
    operation: str,
    body: dict[str, Any],
    *,
    origin: str = ORIGIN,
    role: str = WRITER,
    idempotency_key: str | None = "idem-1",
    expected_version: int | None = 1,
) -> ApiRequest:
    return ApiRequest(
        operation=operation,
        origin=origin,
        body=body,
        actor_role=role,
        idempotency_key=idempotency_key,
        expected_version=expected_version,
    )


def _append_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "stream": AuditStream.ELIGIBILITY.value,
        "voting_context_reference": "vc-1",
        "event_type": "epd2.pack15.eligibility.recorded.v1",
        "reason_code": "ELIGIBILITY_APPROVED",
        "recorded_at_bucket": NOW.isoformat(),
        "subject": "case-1",
        "payload_hash": "c" * 64,
        "payload": {"decision_class": "standard"},
        "retention_class": "voting_audit",
    }
    body.update(overrides)
    return body


def _bundle_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "voting_context_reference": "vc-1",
        "context_metadata": {"voting_type": "internal_party_vote", "scope": "DE-BE"},
        "configuration_versions": {"rule_set_version": "1.0.0", "context_version": "2"},
        "eligibility_totals": {"approved": 120, "denied": 8},
        "assertion_totals": {"minted": 120, "queued": 120, "released": 118, "picked_up": 110},
        "credential_totals": {"issued": 110, "redeemed": 95},
        "integrity_commitments": {"as01_head": "a" * 64, "as03_head": "b" * 64},
        "provenance": {"builder": "audit-core", "profile": "standard"},
        "minimum_cell": 5,
        "generated_at_bucket": NOW.isoformat(),
        "context_closed": True,
    }
    body.update(overrides)
    return body


def _export_body(**overrides: Any) -> dict[str, Any]:
    body = _bundle_body()
    body.update(
        {
            "grant_reference": "grant-9",
            "streams": [AuditStream.INDEPENDENT.value],
        }
    )
    body.update(overrides)
    return body


def _append(api: VotingEvidenceApi, **overrides: Any) -> Any:
    return api.dispatch(_request("evidence.stream.append", _append_body(**overrides)))


def _read(api: VotingEvidenceApi, streams: list[str], reference: str = "vc-1") -> Any:
    return api.dispatch(
        _request(
            "evidence.stream.read",
            {"streams": streams, "voting_context_reference": reference},
            role=AUDITOR,
            idempotency_key=None,
            expected_version=None,
        )
    )


def _build(api: VotingEvidenceApi, **overrides: Any) -> Any:
    return api.dispatch(_request("evidence.bundle.build", _bundle_body(**overrides), role=AUDITOR))


def _export(api: VotingEvidenceApi, **overrides: Any) -> Any:
    return api.dispatch(_request("evidence.bundle.export", _export_body(**overrides), role=AUDITOR))


def _registered_reason_codes() -> set[str]:
    text = REASON_CODE_REGISTRY.read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", text, flags=re.MULTILINE))


# =============================================================================
# 1. The catalogue
# =============================================================================


def test_the_catalogue_declares_exactly_the_four_evidence_operations() -> None:
    assert set(EVIDENCE_CATALOGUE) == {
        "evidence.stream.append",
        "evidence.stream.read",
        "evidence.bundle.build",
        "evidence.bundle.export",
    }


def test_every_endpoint_is_neutral_and_in_the_evidence_area() -> None:
    """Neutral is a claim about the adapter, not about the streams: one
    request never touches more than one side."""
    for spec in EVIDENCE_ENDPOINTS:
        assert spec.trust_side is TrustSide.NEUTRAL
        assert spec.area == "evidence"


def test_every_consequential_endpoint_takes_all_three_obligations() -> None:
    for spec in EVIDENCE_ENDPOINTS:
        if spec.consequential:
            assert spec.idempotency_key_required
            assert spec.version_check_required
            assert spec.audit_evidence_required


def test_only_the_stream_read_endpoint_waives_the_obligations() -> None:
    waiving = {spec.operation for spec in EVIDENCE_ENDPOINTS if not spec.consequential}
    assert waiving == {"evidence.stream.read"}


def test_every_declared_reason_code_is_in_the_pack15_registry() -> None:
    registered = _registered_reason_codes()
    assert registered, "the PACK-15 reason-code registry did not parse"
    for spec in EVIDENCE_ENDPOINTS:
        unknown = sorted(set(spec.reason_codes) - registered)
        assert not unknown, f"{spec.operation} declares unregistered codes: {unknown}"


def test_no_evidence_endpoint_is_unauthenticated_by_design() -> None:
    for spec in EVIDENCE_ENDPOINTS:
        assert not spec.unauthenticated_by_design


def test_no_auditing_role_may_write_the_evidence_it_reads() -> None:
    """An auditor who can append is an auditor whose findings are their
    own composition."""
    assert "independent_auditor" not in STREAM_WRITER_ROLES
    assert "security_auditor" not in STREAM_WRITER_ROLES
    assert "independent_auditor" in STREAM_READER_ROLES


def test_export_names_only_the_role_its_authorization_accepts() -> None:
    assert BUNDLE_EXPORT_ROLES == ("independent_auditor",)


def test_a_consequential_endpoint_may_not_waive_an_obligation() -> None:
    with pytest.raises(ApiContractError):
        build_catalogue(
            [
                EndpointSpec(
                    operation="evidence.stream.purge",
                    area="evidence",
                    trust_side=TrustSide.NEUTRAL,
                    consequential=True,
                    idempotency_key_required=True,
                    version_check_required=True,
                    audit_evidence_required=False,
                    authorized_roles=(WRITER,),
                    reason_codes=("AUDIT_UNAVAILABLE",),
                )
            ]
        )


def test_an_unknown_operation_is_refused_by_the_closed_catalogue(
    api: VotingEvidenceApi,
) -> None:
    response = api.dispatch(_request("evidence.stream.join", {}))
    assert response.reason_code == "API_OPERATION_UNKNOWN"


# =============================================================================
# 2. Obligations, origin and role
# =============================================================================


def test_an_append_without_an_idempotency_key_is_refused(api: VotingEvidenceApi) -> None:
    response = api.dispatch(
        _request("evidence.stream.append", _append_body(), idempotency_key=None)
    )
    assert response.reason_code == "API_IDEMPOTENCY_KEY_REQUIRED"


def test_an_append_without_a_version_is_refused(api: VotingEvidenceApi) -> None:
    response = api.dispatch(
        _request("evidence.stream.append", _append_body(), expected_version=None)
    )
    assert response.reason_code == "API_VERSION_CHECK_REQUIRED"


def test_a_request_from_a_foreign_origin_is_refused(api: VotingEvidenceApi) -> None:
    response = api.dispatch(
        _request("evidence.stream.append", _append_body(), origin=FOREIGN_ORIGIN)
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_a_role_the_endpoint_does_not_name_is_refused(api: VotingEvidenceApi) -> None:
    response = api.dispatch(
        _request("evidence.stream.append", _append_body(), role="independent_auditor")
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_exporting_as_any_other_role_never_reaches_the_handler(
    api: VotingEvidenceApi,
) -> None:
    response = api.dispatch(
        _request("evidence.bundle.export", _export_body(), role="voting_operations_officer")
    )
    assert response.reason_code == "API_ORIGIN_REFUSED"


def test_reading_a_stream_needs_neither_key_nor_version(api: VotingEvidenceApi) -> None:
    response = _read(api, [AuditStream.ELIGIBILITY.value])
    assert response.ok


# =============================================================================
# 3. The runtime's structural separation
# =============================================================================


def test_a_runtime_sharing_one_connection_across_two_sides_is_refused(
    databases: Databases,
) -> None:
    identity, _voting, neutral = databases
    with pytest.raises(AuditDatabaseNotSeparatedError):
        VotingEvidenceRuntime(
            identity_side=SqlVotingAuditStreamStore(identity, IDENTITY_SIDE_DATABASE_STREAMS),
            voting_side=SqlVotingAuditStreamStore(identity, VOTING_SIDE_DATABASE_STREAMS),
            neutral=SqlVotingAuditStreamStore(neutral, NEUTRAL_DATABASE_STREAMS),
            exports=SqlEvidenceBundleExportStore(neutral),
            custody=BundleSigningCustody(),
        )


def test_a_runtime_whose_export_log_sits_beside_a_side_is_refused(
    databases: Databases,
) -> None:
    """ "Which bundles were exported" may not be a question only one side
    can answer."""
    identity, voting, neutral = databases
    with pytest.raises(AuditDatabaseNotSeparatedError):
        VotingEvidenceRuntime(
            identity_side=SqlVotingAuditStreamStore(identity, IDENTITY_SIDE_DATABASE_STREAMS),
            voting_side=SqlVotingAuditStreamStore(voting, VOTING_SIDE_DATABASE_STREAMS),
            neutral=SqlVotingAuditStreamStore(neutral, NEUTRAL_DATABASE_STREAMS),
            exports=SqlEvidenceBundleExportStore(identity),
            custody=BundleSigningCustody(),
        )


def test_two_databases_claiming_the_same_stream_are_refused(databases: Databases) -> None:
    identity, voting, neutral = databases
    with pytest.raises(AuditDatabaseNotSeparatedError):
        VotingEvidenceRuntime(
            identity_side=SqlVotingAuditStreamStore(identity, IDENTITY_SIDE_DATABASE_STREAMS),
            voting_side=SqlVotingAuditStreamStore(voting, VOTING_SIDE_DATABASE_STREAMS),
            neutral=SqlVotingAuditStreamStore(neutral, IDENTITY_SIDE_DATABASE_STREAMS),
            exports=SqlEvidenceBundleExportStore(neutral),
            custody=BundleSigningCustody(),
        )


def test_each_stream_routes_to_the_database_that_owns_it(api: VotingEvidenceApi) -> None:
    runtime = api.runtime
    for stream in IDENTITY_SIDE_DATABASE_STREAMS:
        assert runtime.store_for(stream) is runtime.identity_side
    for stream in VOTING_SIDE_DATABASE_STREAMS:
        assert runtime.store_for(stream) is runtime.voting_side
    for stream in NEUTRAL_DATABASE_STREAMS:
        assert runtime.store_for(stream) is runtime.neutral


def test_the_two_sides_never_share_a_connection(api: VotingEvidenceApi) -> None:
    runtime = api.runtime
    assert runtime.identity_side.connection is not runtime.voting_side.connection
    assert runtime.exports.connection is runtime.neutral.connection


def test_a_stream_no_database_serves_is_refused_rather_than_defaulted(
    databases: Databases,
) -> None:
    """Writing an unrouted stream somewhere plausible is how an
    identity-side record ends up where the voting side can read it."""
    identity, voting, neutral = databases
    runtime = VotingEvidenceRuntime(
        identity_side=SqlVotingAuditStreamStore(identity, IDENTITY_SIDE_DATABASE_STREAMS),
        voting_side=SqlVotingAuditStreamStore(voting, VOTING_SIDE_DATABASE_STREAMS),
        neutral=SqlVotingAuditStreamStore(neutral, frozenset({AuditStream.INDEPENDENT})),
        exports=SqlEvidenceBundleExportStore(neutral),
        custody=BundleSigningCustody(),
    )
    with pytest.raises(EvidenceBundleScopeRefusedError):
        runtime.store_for(AuditStream.SYSTEM_INTEGRITY)
    restricted = build_voting_evidence_api(runtime, allowed_origins=ORIGINS)
    response = restricted.dispatch(
        _request(
            "evidence.stream.append",
            _append_body(stream=AuditStream.SYSTEM_INTEGRITY.value, subject="scheduler"),
        )
    )
    assert response.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"


# =============================================================================
# 4. Appending
# =============================================================================


def test_a_record_lands_in_the_database_that_owns_its_stream(
    api: VotingEvidenceApi,
) -> None:
    response = _append(api)
    assert response.ok
    assert response.body["stream"] == "AS-01"
    assert api.runtime.identity_side.count(AuditStream.ELIGIBILITY, "vc-1") == 1
    assert api.runtime.voting_side.count(AuditStream.CREDENTIAL, "vc-1") == 0


def test_a_voting_side_record_lands_in_the_voting_side_database(
    api: VotingEvidenceApi,
) -> None:
    response = _append(
        api,
        stream=AuditStream.CREDENTIAL.value,
        subject="cred-1",
        reason_code="CREDENTIAL_REDEEMED",
    )
    assert response.ok
    assert api.runtime.voting_side.count(AuditStream.CREDENTIAL, "vc-1") == 1
    assert api.runtime.identity_side.count(AuditStream.ASSERTION, "vc-1") == 0


def test_the_append_response_does_not_echo_the_subject(api: VotingEvidenceApi) -> None:
    """The caller supplied it, so returning it teaches nobody anything and
    puts a copy in a channel with weaker retention."""
    response = _append(api)
    assert "subject" not in response.body
    assert_response_safe(response.body)


def test_a_payload_naming_a_participant_is_refused_at_append(
    api: VotingEvidenceApi,
) -> None:
    response = _append(api, payload={"pseudonym": "px-1"})
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"
    assert api.runtime.identity_side.count(AuditStream.ELIGIBILITY, "vc-1") == 0


def test_an_unknown_stream_identifier_is_refused(api: VotingEvidenceApi) -> None:
    response = _append(api, stream="AS-99")
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_record_without_a_subject_is_refused(api: VotingEvidenceApi) -> None:
    response = _append(api, subject="")
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_naive_recording_timestamp_is_refused(api: VotingEvidenceApi) -> None:
    response = _append(api, recorded_at_bucket="2026-08-03T08:00:00")
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_payload_that_is_not_a_mapping_is_refused(api: VotingEvidenceApi) -> None:
    response = _append(api, payload=["decision_class"])
    assert response.reason_code == "API_REQUEST_MALFORMED"


# =============================================================================
# 5. Reading one stream
# =============================================================================


def test_reading_one_stream_returns_its_records_for_that_context(
    api: VotingEvidenceApi,
) -> None:
    assert _append(api).ok
    assert _append(api, subject="case-2").ok
    response = _read(api, [AuditStream.ELIGIBILITY.value])
    assert response.ok
    assert response.body["record_count"] == 2
    assert {record["subject"] for record in response.body["records"]} == {"case-1", "case-2"}


def test_a_read_naming_both_sides_of_the_boundary_is_refused(
    api: VotingEvidenceApi,
) -> None:
    """The refusal happens before the read: once one principal has seen
    both sides, no later error removes the link."""
    response = _read(api, [AuditStream.ASSERTION.value, AuditStream.CREDENTIAL.value])
    assert response.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"


def test_a_read_naming_two_streams_from_one_side_is_still_refused(
    api: VotingEvidenceApi,
) -> None:
    """Not the same rule: AS-01 and AS-02 do not span the boundary, but
    serving them together is a joined view no store produced."""
    response = _read(api, [AuditStream.ELIGIBILITY.value, AuditStream.ASSERTION.value])
    assert response.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"


def test_a_read_of_another_context_returns_nothing(api: VotingEvidenceApi) -> None:
    assert _append(api).ok
    response = _read(api, [AuditStream.ELIGIBILITY.value], reference="vc-2")
    assert response.ok
    assert response.body["record_count"] == 0


def test_the_streams_argument_must_be_a_list(api: VotingEvidenceApi) -> None:
    response = api.dispatch(
        _request(
            "evidence.stream.read",
            {"streams": "AS-01", "voting_context_reference": "vc-1"},
            role=AUDITOR,
            idempotency_key=None,
            expected_version=None,
        )
    )
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_record_written_around_the_api_cannot_be_read_back(
    api: VotingEvidenceApi,
) -> None:
    """The response scan is the backstop for records the append rule never
    saw - refusing rather than filtering, because a body that has to be
    scrubbed was built by code that had the value in hand."""
    api.runtime.identity_side.append(
        VotingAuditRecord(
            record_id=uuid4(),
            stream=AuditStream.ELIGIBILITY,
            voting_context_reference="vc-1",
            event_type="epd2.pack15.eligibility.recorded.v1",
            reason_code="ELIGIBILITY_APPROVED",
            recorded_at_bucket=NOW,
            subject="case-9",
            payload_hash="d" * 64,
            payload={"pseudonym": "px-9"},
            retention_class="voting_audit",
        )
    )
    api.runtime.identity_side.connection.commit()
    response = _read(api, [AuditStream.ELIGIBILITY.value])
    assert response.reason_code == "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


# =============================================================================
# 6. Building a bundle
# =============================================================================


def test_a_closed_bundle_is_built_validated_and_summarized(
    api: VotingEvidenceApi,
) -> None:
    response = _build(api)
    assert response.ok
    assert response.body["bundle_schema_version"] == 1
    assert response.body["pre_closure"] is False
    assert response.body["sections"] == list(BUNDLE_SECTIONS)
    assert response.body["suppressed_cell_count"] == 0


def test_the_build_response_carries_no_section_content(api: VotingEvidenceApi) -> None:
    """A second copy of the bundle here would be a copy that ran none of
    the export's authorization."""
    response = _build(api)
    assert set(response.body["sections"]) == set(BUNDLE_SECTIONS)
    assert all(isinstance(name, str) for name in response.body["sections"])
    assert "context_metadata" not in response.body
    assert_response_safe(response.body)


def test_a_pre_closure_bundle_carries_no_outcome_totals(api: VotingEvidenceApi) -> None:
    response = _build(api, context_closed=False)
    assert response.ok
    assert response.body["pre_closure"] is True


def test_an_outcome_key_in_a_pre_closure_request_is_refused(
    api: VotingEvidenceApi,
) -> None:
    response = _build(api, context_closed=False, turnout=412)
    assert response.reason_code == "INTERMEDIATE_TALLY_PROHIBITED"


def test_a_minimum_cell_below_the_floor_is_refused(api: VotingEvidenceApi) -> None:
    response = _build(api, minimum_cell=3)
    assert response.reason_code == "EVIDENCE_BUNDLE_INVALID"


def test_small_cells_are_suppressed_rather_than_rounded(api: VotingEvidenceApi) -> None:
    """One suppressed cell is recoverable by subtraction, so a second one
    goes with it."""
    response = _build(api, eligibility_totals={"approved": 120, "denied": 3})
    assert response.ok
    assert response.body["suppressed_cell_count"] == 2


def test_inconsistent_assertion_totals_are_refused(api: VotingEvidenceApi) -> None:
    response = _build(api, assertion_totals={"minted": 100, "queued": 120})
    assert response.reason_code == "EVIDENCE_BUNDLE_INVALID"


def test_more_redemptions_than_issuances_are_refused(api: VotingEvidenceApi) -> None:
    response = _build(api, credential_totals={"issued": 90, "redeemed": 95})
    assert response.reason_code == "EVIDENCE_BUNDLE_INVALID"


def test_a_total_that_is_not_a_count_is_refused(api: VotingEvidenceApi) -> None:
    response = _build(api, credential_totals={"issued": "many"})
    assert response.reason_code == "API_REQUEST_MALFORMED"


def test_a_bundle_request_carrying_a_participant_reference_is_refused(
    api: VotingEvidenceApi,
) -> None:
    response = _build(api, context_metadata={"participant_reference": "p-1"})
    assert response.reason_code == "EVIDENCE_BUNDLE_INVALID"


# =============================================================================
# 7. Exporting a bundle
# =============================================================================


def test_an_authorized_export_is_persisted(api: VotingEvidenceApi) -> None:
    response = _export(api)
    assert response.ok
    assert response.body["reason_code"] == "EVIDENCE_BUNDLE_EXPORTED"
    exports = api.runtime.exports.exports_for_context("vc-1")
    assert len(exports) == 1
    assert exports[0]["exported_by_role"] == "independent_auditor"


def test_an_export_without_a_time_boxed_grant_is_refused(api: VotingEvidenceApi) -> None:
    response = _export(api, grant_reference="")
    assert response.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"
    assert api.runtime.exports.exports_for_context("vc-1") == ()


def test_an_export_naming_streams_from_both_sides_is_refused(
    api: VotingEvidenceApi,
) -> None:
    response = _export(api, streams=[AuditStream.ASSERTION.value, AuditStream.CREDENTIAL.value])
    assert response.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"
    assert api.runtime.exports.exports_for_context("vc-1") == ()


def test_a_pre_closure_export_without_dual_control_is_refused(
    api: VotingEvidenceApi,
) -> None:
    response = _export(api, context_closed=False)
    assert response.reason_code == "EVIDENCE_BUNDLE_PRECLOSURE_REFUSED"
    assert api.runtime.exports.exports_for_context("vc-1") == ()


def test_a_pre_closure_export_under_dual_control_is_persisted(
    api: VotingEvidenceApi,
) -> None:
    response = _export(api, context_closed=False, dual_control_reference="dc-4")
    assert response.ok
    assert response.body["pre_closure"] is True
    exports = api.runtime.exports.exports_for_context("vc-1")
    assert len(exports) == 1
    assert exports[0]["dual_control_reference"] == "dc-4"


def test_the_export_response_never_carries_a_forbidden_key(
    api: VotingEvidenceApi,
) -> None:
    response = _export(api)
    assert response.ok
    assert_response_safe(response.body)
    assert "context_metadata" not in response.body


def test_an_export_authorizes_the_context_the_bundle_actually_names(
    api: VotingEvidenceApi,
) -> None:
    """One context per bundle cannot be satisfied by naming one context
    and exporting another: the authorization reads the built bundle."""
    response = _export(api, voting_context_reference="vc-7")
    assert response.ok
    assert api.runtime.exports.exports_for_context("vc-1") == ()
    assert len(api.runtime.exports.exports_for_context("vc-7")) == 1
