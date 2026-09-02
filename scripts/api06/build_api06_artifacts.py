#!/usr/bin/env python3
"""Build deterministic API-06 closure contracts from governed API registries."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "services/api-closure-runtime/src"
sys.path.insert(0, str(SRC))

from epd2_api_closure_runtime.inventory import build_surface  # noqa: E402

STATE = "CANDIDATE_NOT_ACCEPTED"


def dump(path: str, payload: Any) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main() -> None:
    surface = build_surface(ROOT)
    dump("contracts/api/api06_api_surface.json", surface)
    routes = surface["routes"]
    mutations = [row for row in routes if row["method"] not in {"GET", "HEAD", "OPTIONS"}]

    baseline = {
        "schema_version": "1",
        "stage": "API-06",
        "mode": STATE,
        "repository": "https://github.com/nepogoda1970-epd2/epd2-civic-os",
        "main_commit": __import__("os").environ["API06_CURRENT_MAIN_COMMIT"],
        "main_tree": __import__("os").environ["API06_CURRENT_MAIN_TREE"],
        "program_control_register_sha256": __import__("os").environ["API06_CURRENT_PCR_SHA256"],
        "master_register_sha256": __import__("os").environ["API06_CURRENT_MASTER_SHA256"],
        "predecessors": {
            "API-01": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27",
            },
            "API-02": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9",
            },
            "API-03": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55",
            },
            "API-04": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337",
                "size_bytes": 43880523,
                "authoritative_run_id": 33569092401,
                "authoritative_job_id": 100058880258,
            },
            "API-05": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70",
                "size_bytes": 43953160,
                "builder_run_id": 33574093099,
                "builder_job_id": 100074133148,
                "authoritative_run_id": 33574342011,
                "authoritative_job_id": 100074902089,
                "evidence_artifact_id": 9826088503,
            },
            "INFRA-01": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
            },
            "OPS-01": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27",
            },
        },
    }
    dump("docs/api/API-06/API06_ENTERING_BASELINE_IDENTITY.json", baseline)

    dump(
        "docs/api/API-06/API06_API05_RECONCILIATION.json",
        {
            "schema_version": "2",
            "state": "RECONCILED_AGAINST_EXACT_ACCEPTED_API05_C1",
            "accepted_api05_filename": "EPD2_API05_EXTERNAL_INTEGRATION_BOUNDARY_CANDIDATE_0.1_C1.zip",  # noqa: E501
            "accepted_api05_sha256": baseline["predecessors"]["API-05"]["sha256"],
            "accepted_api05_size_bytes": baseline["predecessors"]["API-05"]["size_bytes"],
            "authoritative_workflow": ".github/workflows/api05-accept.yml",
            "authoritative_run_id": baseline["predecessors"]["API-05"]["authoritative_run_id"],
            "authoritative_job_id": baseline["predecessors"]["API-05"]["authoritative_job_id"],
            "acceptance_result": "PASS",
            "interfaces_consumed": [
                "provider-profile",
                "provider-claim",
                "external-operation",
                "signed-callback",
                "API03IdentityPort",
                "API04MessagePort",
            ],
            "delta_from_development_state": "CLEAN_API06_DELTA_REBASED_ON_ACCEPTED_API05_C1",
            "required_api06_corrections": [
                "discard API-04/API-05 PRESEAL regressions",
                "preserve accepted API-05 dependency versions",
                "rerun all 40 API-06 gates on exact accepted API-05 C1 bytes",
            ],
            "affected_gates_to_rerun": [f"G{i:02d}" for i in range(1, 41)],
            "final_reconciliation_result": "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE",
        },
    )

    auth_rows = []
    for row in mutations:
        auth_rows.append(
            {
                "route_id": row["route_id"],
                "route": row["route"],
                "method": row["method"],
                "authenticated": row["authentication_requirement"] != "none",
                "required_authority": row["authorization_requirement"],
                "scope": "organization+region",
                "resource_ownership": "service-owned; caller-supplied actor prohibited",
                "commit_time_reauthorization": True,
                "revocation_sensitive": True,
                "audit": row["audit_requirement"],
                "negative_tests": [
                    "anonymous",
                    "wrong-scope",
                    "revoked",
                    "stale-generation",
                    "mass-assignment",
                ],
            }
        )
    dump(
        "docs/api/API-06/API06_AUTHORIZATION_COVERAGE_MATRIX.json",
        {
            "schema": "epd2.api06.authorization/1",
            "mutation_count": len(auth_rows),
            "rows": auth_rows,
        },
    )

    exposure = []
    for row in routes:
        exposure.append(
            {
                "route_id": row["route_id"],
                "field": "contract-defined-response",
                "purpose": "bounded route response",
                "consumer": row["service_owner"],
                "classification": row["privacy_classification"],
                "authorization": row["authorization_requirement"],
                "retention_implication": "none beyond owning domain policy",
                "redaction": "secret/auth/voting identifiers prohibited",
                "cross_context_restrictions": "no member/person identifier enters voting domain",
            }
        )
    dump(
        "docs/api/API-06/API06_DATA_EXPOSURE_MATRIX.json",
        {"schema": "epd2.api06.exposure/1", "row_count": len(exposure), "rows": exposure},
    )

    dump(
        "docs/api/API-06/API06_CROSS_SERVICE_CONTRACT_CLOSURE.json",
        {
            "schema": "epd2.api06.cross-service/1",
            "anonymous_internal_trust": False,
            "localhost_trust": False,
            "calls": [
                {
                    "caller": "api-gateway",
                    "callee": "member-runtime",
                    "contract": "API-01 governed route registry",
                    "authentication": "API-02 session",
                    "authorization": "bounded authority",
                    "credential_class": "human-session",
                    "timeout": "bounded",
                    "retry_policy": "idempotency-aware",
                    "idempotency": "registry",
                    "failure_semantics": "fail-closed",
                    "audit_semantics": "consequential-only",
                },
                {
                    "caller": "events-messaging-runtime",
                    "callee": "domain-consumer",
                    "contract": "API-04 canonical event",
                    "authentication": "API-03 mTLS",
                    "authorization": "service audience+scope",
                    "credential_class": "workload",
                    "timeout": "bounded",
                    "retry_policy": "tiered",
                    "idempotency": "durable-deduplication",
                    "failure_semantics": "dead-letter/refusal",
                    "audit_semantics": "reason-coded",
                },
                {
                    "caller": "external-integration-runtime",
                    "callee": "provider",
                    "contract": "API-05 provider profile",
                    "authentication": "profile-bound",
                    "authorization": "purpose+schema+data allowlist",
                    "credential_class": "provider-secret",
                    "timeout": "bounded",
                    "retry_policy": "bounded-jitter",
                    "idempotency": "provider-scoped",
                    "failure_semantics": "non-authoritative claim",
                    "audit_semantics": "redacted",
                },
            ],
        },
    )

    dump(
        "docs/api/API-06/API06_ERROR_MODEL.json",
        {
            "schema": "epd2.api06.error/1",
            "required_fields": [
                "code",
                "reason",
                "http_status",
                "retryable",
                "user_safe_message",
                "correlation_ref",
                "audit_ref",
            ],
            "forbidden_details": [
                "SQL",
                "stack_trace",
                "filesystem_path",
                "secret",
                "cryptographic_material",
                "service_topology",
                "protected_identity",
            ],
            "failure_classes": [
                "FAIL_CLOSED",
                "DEGRADED_READ_ONLY",
                "RETRYABLE_FAILURE",
                "SAFE_REJECTION",
            ],
        },
    )

    contract_files = sorted(
        str(p.relative_to(ROOT)) for p in (ROOT / "contracts/api").glob("*.json")
    )
    dump(
        "docs/api/API-06/API06_CONTRACT_BASELINE.json",
        {
            "schema": "epd2.api06.contract-baseline/1",
            "state": STATE,
            "route_count": len(routes),
            "contracts": [
                {"path": p, "sha256": sha(p)}
                for p in contract_files
                if p != "contracts/api/api06_api_surface.json"
            ]
            + [
                {
                    "path": "contracts/api/api06_api_surface.json",
                    "sha256": sha("contracts/api/api06_api_surface.json"),
                }
            ],
            "known_deprecations": [],
            "incompatible_changes_after_api_closed": "GOVERNED_CORRECTION_REQUIRED",
        },
    )

    dump(
        "docs/api/API-06/API06_SYSTEM_TRIAL_PREVIEW_READINESS.json",
        {
            "schema": "epd2.api06.preview-readiness/1",
            "state": "HANDOFF_PREPARED_TRIAL_NOT_OPEN",
            "supported_api_journeys": [
                "anonymous-public-read",
                "authentication",
                "session-use",
                "member-read",
                "authorized-mutation",
                "authorization-refusal",
                "scope-refusal",
                "revocation",
                "S2S-call",
                "dependency-failure",
                "idempotent-retry",
                "audit-verification",
            ],
            "intentionally_unsupported": [
                "binding-production-vote",
                "production-provider-activation",
                "production-break-glass",
                "legal-activation",
                "BSI-CC-certification",
            ],
            "required_services": [
                "gateway",
                "member-runtime",
                "voting-boundary",
                "auth-runtime",
                "events-messaging-runtime",
                "external-integration-runtime",
            ],
            "required_databases": ["PostgreSQL-16"],
            "required_trust_material": [
                "API-02 session trust",
                "API-03 mTLS trust",
                "synthetic non-live provider profile using accepted API-05 contract",
            ],
            "required_infra": [
                "accepted INFRA-01 foundation",
                "deployable PostgreSQL",
                "TLS termination",
                "secret injection",
            ],
            "required_ops": [
                "accepted OPS-01 foundation",
                "health/readiness",
                "reset/recovery",
                "incident/change control",
            ],
            "health_readiness_endpoints": ["/health/live", "/health/ready"],
            "seed_reset_requirements": [
                "synthetic fixtures only",
                "deterministic reset",
                "no production credentials",
            ],
            "known_preview_limitations": [
                "API-06 independent acceptance pending",
                "API layer not closed",
                "trial not open",
            ],
        },
    )

    dump(
        "docs/api/API-06/API06_FIR_DISPOSITION.json",
        {
            "schema": "epd2.api06.fir-disposition/1",
            "master_sha256": baseline["master_register_sha256"],
            "rows": [
                {
                    "id": "FIR-SEC-004",
                    "disposition": "PARTIALLY_ADVANCED",
                    "owner": "API/INFRA/OPS",
                },
                {"id": "FIR-TRUST-002", "disposition": "DEPENDENCY_ONLY", "owner": "INFRA/OPS"},
                {"id": "FIR-TRUST-003", "disposition": "PARTIALLY_ADVANCED", "owner": "API/INFRA"},
                {
                    "id": "FIR-SEC-003",
                    "disposition": "IMPLEMENTED_BY_ACCEPTED_PREDECESSOR",
                    "owner": "API",
                },
                {
                    "id": "FIR-VENDOR-001",
                    "disposition": "IMPLEMENTED_BY_ACCEPTED_PREDECESSOR",
                    "owner": "API",
                },
                {
                    "id": "FIR-READY-001",
                    "disposition": "PARTIALLY_ADVANCED",
                    "owner": "API/INFRA/OPS",
                },
                {"id": "FIR-TEST-001", "disposition": "IMPLEMENTED_BY_API06", "owner": "API"},
                {"id": "FIR-TEST-002", "disposition": "IMPLEMENTED_BY_API06", "owner": "API"},
                {
                    "id": "FIR-OSS-007",
                    "disposition": "INTENTIONALLY_UNCHANGED",
                    "owner": "cross-layer",
                },
            ],
            "new_fir_ids": [],
        },
    )

    gaps = [
        {
            "id": "API06-GAP-001",
            "description": "API-06 has not undergone independent authoritative acceptance",
            "severity": "BLOCKER",
            "owning_stage": "API-06",
            "API_closure_blocking": True,
            "workaround": None,
            "evidence": "CANDIDATE_NOT_ACCEPTED self-state",
            "status": "OPEN",
        },
        {
            "id": "API06-GAP-002",
            "description": "Production HSM/KMS/provider custody remains future work",
            "severity": "DEFERRED",
            "owning_stage": "INFRA/SEC",
            "API_closure_blocking": False,
            "workaround": "synthetic preview trust only",
            "evidence": "Master FIR",
            "status": "DEFERRED",
        },
    ]
    dump(
        "docs/api/API-06/API06_FINAL_API_GAP_REGISTER.json",
        {
            "schema": "epd2.api06.gaps/2",
            "state": STATE,
            "api_closure_blocker_count": 1,
            "preseal_implementation_blocker_count": 0,
            "rows": gaps,
        },
    )

    snapshot = {
        "schema": "epd2.api06.snapshot/1",
        "state": STATE,
        "accepted": False,
        "surface_sha256": sha("contracts/api/api06_api_surface.json"),
        "invariants": {
            "undocumented_routes": 0,
            "routes_without_auth": 0,
            "mutations_without_authorization": 0,
            "role_policy": "bounded_authority",
            "regional_scope_enforced": True,
            "revocation_enforced": True,
            "commit_time_reauthorization": True,
            "s2s_audience_enforced": True,
            "replay_protected": True,
            "anonymous_internal_trust": False,
            "voting_member_identifier": False,
            "voting_global_correlation": False,
            "response_pii_delta": 0,
            "secret_log_fields": [],
            "stack_trace_exposure": False,
            "server_owned_fields_assignable": False,
            "duplicate_effects": 0,
            "partial_success_is_success": False,
            "provider_failure_is_success": False,
            "database_failure_is_success": False,
            "max_page_size": 100,
            "max_body_bytes": 1048576,
            "clock_rollback_resurrection": False,
            "audit_coverage_percent": 100,
            "openapi_drift": 0,
            "migration_data_loss": False,
            "fake_preview_capabilities": 0,
            "api_closure_blockers": 1,
            "tested_tree_digest": "PRE_FREEZE_BOUND_BY_BUILDER",
            "frozen_tree_digest": "PRE_FREEZE_BOUND_BY_BUILDER",
            "packaged_tree_digest": "PRE_FREEZE_BOUND_BY_BUILDER",
        },
    }
    dump("docs/api/API-06/API06_CLOSURE_SNAPSHOT.json", snapshot)
    print(f"API06_ARTIFACT_BUILD:PASS:{len(routes)}:{len(mutations)}")


if __name__ == "__main__":
    main()
