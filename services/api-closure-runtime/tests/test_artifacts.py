from __future__ import annotations

import json
from pathlib import Path

from epd2_api_closure_runtime.verification import load_snapshot, verify_snapshot

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/api/API-06"


def load(name):
    return json.loads((DOC / name).read_text())


def test_exact_entering_baseline_records_all_required_identities():
    baseline = load("API06_ENTERING_BASELINE_IDENTITY.json")
    assert baseline["mode"] == "CANDIDATE_NOT_ACCEPTED"
    assert set(baseline["predecessors"]) == {
        "API-01",
        "API-02",
        "API-03",
        "API-04",
        "API-05",
        "INFRA-01",
        "OPS-01",
    }
    assert (
        baseline["predecessors"]["API-04"]["sha256"]
        == "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337"
    )
    assert (
        baseline["predecessors"]["API-05"]["sha256"]
        == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"
    )


def test_api05_reconciliation_is_exact_and_blocks_final_seal():
    row = load("API06_API05_RECONCILIATION.json")
    assert (
        row["accepted_api05_sha256"]
        == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"
    )
    assert row["acceptance_result"] == "PASS"
    assert row["final_reconciliation_result"] == "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE"
    assert len(row["affected_gates_to_rerun"]) == 40


def test_authorization_matrix_covers_every_mutation():
    matrix = load("API06_AUTHORIZATION_COVERAGE_MATRIX.json")
    assert matrix["mutation_count"] == 60
    assert all(
        r["commit_time_reauthorization"] and r["revocation_sensitive"] for r in matrix["rows"]
    )


def test_cross_service_contracts_have_no_implicit_internal_trust():
    closure = load("API06_CROSS_SERVICE_CONTRACT_CLOSURE.json")
    assert closure["anonymous_internal_trust"] is False
    assert closure["localhost_trust"] is False
    assert all(r["authentication"] and r["authorization"] for r in closure["calls"])


def test_error_model_forbids_sensitive_diagnostics():
    model = load("API06_ERROR_MODEL.json")
    assert {"SQL", "stack_trace", "secret", "cryptographic_material"} <= set(
        model["forbidden_details"]
    )


def test_data_exposure_matrix_covers_all_routes():
    matrix = load("API06_DATA_EXPOSURE_MATRIX.json")
    assert matrix["row_count"] == 91
    assert all(
        "no member/person identifier enters voting domain" in r["cross_context_restrictions"]
        for r in matrix["rows"]
    )


def test_voting_boundary_contract_has_no_persistent_member_identifier():
    surface = json.loads((ROOT / "contracts/api/api06_api_surface.json").read_text())
    voting = [r for r in surface["routes"] if r["voting_boundary_relevance"]]
    forbidden = {"member_id", "person_id", "global_correlation_id", "ballot_content"}
    assert all(not forbidden & set(r) for r in voting)


def test_preview_readiness_does_not_open_trial_or_fake_capabilities():
    preview = load("API06_SYSTEM_TRIAL_PREVIEW_READINESS.json")
    assert preview["state"] == "HANDOFF_PREPARED_TRIAL_NOT_OPEN"
    assert "binding-production-vote" in preview["intentionally_unsupported"]
    assert "API layer not closed" in preview["known_preview_limitations"]


def test_api_gap_register_hides_no_current_closure_blocker():
    gaps = load("API06_FINAL_API_GAP_REGISTER.json")
    blockers = [r for r in gaps["rows"] if r["API_closure_blocking"] and r["status"] == "OPEN"]
    assert gaps["api_closure_blocker_count"] == len(blockers) == 1
    assert gaps["preseal_implementation_blocker_count"] == 0


def test_fir_disposition_invents_no_new_fir():
    fir = load("API06_FIR_DISPOSITION.json")
    assert fir["new_fir_ids"] == []
    assert all(r["disposition"] != "IMPLEMENTED" for r in fir["rows"])


def test_contract_baseline_hashes_are_current():
    baseline = load("API06_CONTRACT_BASELINE.json")
    import hashlib

    for row in baseline["contracts"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]


def test_closure_snapshot_satisfies_all_independent_invariants():
    snapshot = load_snapshot(DOC / "API06_CLOSURE_SNAPSHOT.json")
    verify_snapshot(snapshot, ROOT)
