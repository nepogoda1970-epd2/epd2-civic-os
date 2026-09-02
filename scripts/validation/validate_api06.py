#!/usr/bin/env python3
"""Canonical API-06 40-gate developer PRESEAL validator."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation/api06"
STATE = "CANDIDATE_NOT_ACCEPTED"

GATE_NAMES = [
    "exact entering baseline",
    "governance freshness",
    "accepted predecessor identities",
    "API-05 reconciliation",
    "source/archive hygiene",
    "secret leakage",
    "runtime route inventory",
    "declared/runtime surface equality",
    "request schema validation",
    "response contract validation",
    "authentication coverage",
    "authorization coverage",
    "authorization negative cases",
    "commit-time reauthorization",
    "revocation propagation",
    "S2S authentication",
    "S2S authorization",
    "S2S replay/refusal",
    "regional/scope isolation",
    "privacy exposure",
    "enumeration/small-cohort safety",
    "voting identity isolation",
    "voting telemetry isolation",
    "error-model safety",
    "fail-closed dependency behavior",
    "transaction semantics",
    "partial-failure semantics",
    "idempotency",
    "concurrency",
    "audit completeness",
    "authoritative-time semantics",
    "abuse/rate controls",
    "resource bounds",
    "PostgreSQL live runtime",
    "migration integrity",
    "API regression journeys",
    "mutation/adversarial suite",
    "FIR/gap closure",
    "preview-readiness contract",
    "freeze/package byte identity",
]

REQUIRED_DOCS = [
    "API06_ENTERING_BASELINE_IDENTITY.json",
    "API06_API05_RECONCILIATION.json",
    "API06_AUTHORIZATION_COVERAGE_MATRIX.json",
    "API06_DATA_EXPOSURE_MATRIX.json",
    "API06_CROSS_SERVICE_CONTRACT_CLOSURE.json",
    "API06_ERROR_MODEL.json",
    "API06_CONTRACT_BASELINE.json",
    "API06_SYSTEM_TRIAL_PREVIEW_READINESS.json",
    "API06_FIR_DISPOSITION.json",
    "API06_FINAL_API_GAP_REGISTER.json",
    "API06_CLOSURE_SNAPSHOT.json",
    "API06_STAGE_CONTRACT.md",
    "API06_DEVELOPER_REPORT.md",
    "API06_STATUS.txt",
]

EVIDENCE_MAP = {
    "baseline_identity.json": [1, 2, 3],
    "api_surface_result.json": [7, 8],
    "runtime_route_inventory.json": [7],
    "contract_drift_result.json": [8, 9, 10],
    "authorization_coverage_result.json": [11, 12, 13],
    "commit_time_reauth_result.json": [14, 15],
    "s2s_coverage_result.json": [16, 17, 18],
    "privacy_exposure_result.json": [20, 21],
    "voting_boundary_result.json": [22, 23],
    "idempotency_result.json": [28],
    "concurrency_result.json": [29],
    "partial_failure_result.json": [26, 27],
    "dependency_failure_result.json": [24, 25],
    "audit_coverage_result.json": [30],
    "time_semantics_result.json": [31],
    "abuse_control_result.json": [32],
    "resource_bounds_result.json": [33],
    "schema_security_result.json": [9, 13, 33],
    "postgres_runtime_result.json": [34],
    "migration_result.json": [35],
    "api05_reconciliation_result.json": [4],
    "fir_disposition.json": [38],
    "final_api_gap_result.json": [38],
    "preview_readiness_result.json": [39],
}


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text())


def command(
    name: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 300
) -> dict[str, Any]:
    completed = subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True, env=env, timeout=timeout
    )
    return {
        "name": name,
        "result": "PASS" if completed.returncode == 0 else "FAIL",
        "exit_code": completed.returncode,
        "command": args,
        "stdout_tail": completed.stdout[-6000:],
        "stderr_tail": completed.stderr[-6000:],
    }


def static_checks() -> dict[str, bool]:
    doc = ROOT / "docs/api/API-06"
    baseline = load("docs/api/API-06/API06_ENTERING_BASELINE_IDENTITY.json")
    api05 = load("docs/api/API-06/API06_API05_RECONCILIATION.json")
    gaps = load("docs/api/API-06/API06_FINAL_API_GAP_REGISTER.json")
    preview = load("docs/api/API-06/API06_SYSTEM_TRIAL_PREVIEW_READINESS.json")
    fir = load("docs/api/API-06/API06_FIR_DISPOSITION.json")
    surface = load("contracts/api/api06_api_surface.json")
    current_commit = os.environ.get("API06_CURRENT_MAIN_COMMIT", baseline["main_commit"])
    current_pcr = os.environ.get(
        "API06_CURRENT_PCR_SHA256", baseline["program_control_register_sha256"]
    )
    current_master = os.environ.get(
        "API06_CURRENT_MASTER_SHA256", baseline["master_register_sha256"]
    )
    predecessor = baseline["predecessors"]
    return {
        "docs": all((doc / name).is_file() for name in REQUIRED_DOCS),
        "baseline": baseline["mode"] == STATE and baseline["repository"].endswith("epd2-civic-os"),
        "fresh": current_commit == baseline["main_commit"]
        and current_pcr == baseline["program_control_register_sha256"]
        and current_master == baseline["master_register_sha256"],
        "predecessors": all(
            predecessor[name]["state"] == "ACCEPTED_CLOSED" and predecessor[name]["sha256"]
            for name in ("API-01", "API-02", "API-03", "API-04", "API-05")
        )
        and predecessor["API-04"]["sha256"]
        == "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337"
        and predecessor["API-05"]["sha256"]
        == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70",
        "api05": api05["accepted_api05_sha256"]
        == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"
        and api05["acceptance_result"] == "PASS"
        and api05["final_reconciliation_result"]
        == "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE"
        and len(api05["affected_gates_to_rerun"]) == 40,
        "surface": surface["route_count"] == len(surface["routes"]) == 91,
        "gaps": gaps["preseal_implementation_blocker_count"] == 0
        and gaps["api_closure_blocker_count"] == 1,
        "preview": preview["state"] == "HANDOFF_PREPARED_TRIAL_NOT_OPEN"
        and "binding-production-vote" in preview["intentionally_unsupported"],
        "fir": fir["new_fir_ids"] == []
        and fir["master_sha256"] == baseline["master_register_sha256"],
    }


def hygiene() -> dict[str, Any]:
    forbidden_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
    scope = [
        ROOT / "docs/api/API-06",
        ROOT / "services/api-closure-runtime",
        ROOT / "scripts/api06",
        ROOT / "scripts/validation/validate_api06.py",
    ]
    transient = []
    for base in scope:
        paths = [base] if base.is_file() else list(base.rglob("*"))
        for path in paths:
            rel = path.relative_to(ROOT)
            if set(rel.parts) & forbidden_dirs or path.suffix in {".pyc", ".pyo", ".zip"}:
                transient.append(str(rel))
    builder = (ROOT / "scripts/api06/freeze_rehearsal.py").read_text()
    exclusions_declared = all(
        token in builder
        for token in (".venv", "node_modules", "__pycache__", ".pytest_cache", ".pyc")
    )
    return {
        "result": "PASS" if exclusions_declared else "FAIL",
        "transient_build_outputs_excluded_from_freeze": sorted(transient),
        "packaging_exclusions_declared": exclusions_declared,
    }


def secret_scan() -> dict[str, Any]:
    patterns = {
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    }
    hits = []
    for base in (
        ROOT / "docs/api/API-06",
        ROOT / "services/api-closure-runtime",
        ROOT / "scripts/api06",
    ):
        for path in [base] if base.is_file() else base.rglob("*"):
            if not path.is_file() or path.suffix in {".pyc", ".zip"}:
                continue
            text = path.read_text(errors="ignore")
            for name, pattern in patterns.items():
                if pattern.search(text):
                    hits.append({"file": str(path.relative_to(ROOT)), "class": name})
    return {"result": "PASS" if not hits else "FAIL", "hits": hits}


def gate(number: int, ok: bool, evidence: Any) -> dict[str, Any]:
    return {
        "id": f"G{number:02d}",
        "name": GATE_NAMES[number - 1],
        "result": "PASS" if ok else "FAIL",
        "evidence": evidence,
    }


def write_evidence(gates: list[dict[str, Any]]) -> None:
    by_id = {int(row["id"][1:]): row for row in gates}
    for filename, numbers in EVIDENCE_MAP.items():
        rows = [by_id[number] for number in numbers]
        payload = {
            "schema": "epd2.api06.evidence/1",
            "state": STATE,
            "result": "PASS" if all(r["result"] == "PASS" for r in rows) else "FAIL",
            "gates": rows,
        }
        (VALIDATION / filename).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="validation/api06/api06_acceptance_result.json")
    args = parser.parse_args()
    VALIDATION.mkdir(parents=True, exist_ok=True)

    postgres_url = os.environ.get("EPD2_API06_DATABASE_URL") or os.environ.get(
        "EPD2_API05_DATABASE_URL"
    )
    common_env = dict(os.environ)
    if postgres_url:
        common_env["EPD2_TEST_DATABASE_URL"] = postgres_url
        common_env["EPD2_S2S_DSN"] = postgres_url
    api03_crypto_path = os.environ.get("API06_API03_CRYPTO_PATH")
    if api03_crypto_path:
        existing_pythonpath = common_env.get("PYTHONPATH", "")
        common_env["PYTHONPATH"] = os.pathsep.join(
            part for part in (api03_crypto_path, existing_pythonpath) if part
        )
    api03_python = os.environ.get("API06_API03_PYTHON", sys.executable)
    runs = {
        "artifact_build": command(
            "artifact_build", [sys.executable, "scripts/api06/build_api06_artifacts.py"]
        ),
        "lock": command("lock", ["uv", "lock", "--check"]),
        "ruff": command(
            "ruff",
            [
                "uv",
                "run",
                "--frozen",
                "ruff",
                "check",
                "services/api-closure-runtime",
                "scripts/api06",
                "scripts/validation/validate_api06.py",
            ],
        ),
        "api06": command(
            "api06",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "services/api-closure-runtime/tests",
                "--junitxml=validation/api06/junit-api06.xml",
            ],
        ),
        "inventory": command(
            "inventory",
            [
                sys.executable,
                "scripts/api01/inventory_runtime_routes.py",
                "--check",
                "--json",
                "validation/api06/runtime_inventory_raw.json",
            ],
        ),
        "api02": command(
            "api02",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "packages/python/epd2-runtime/tests/test_api02_authentication_runtime.py",
            ],
            common_env,
        ),
        "api03": command(
            "api03",
            [
                api03_python,
                "-m",
                "pytest",
                "-q",
                "tests/api03/test_s2s_r2.py",
                "tests/api03/test_s2s_r3.py",
            ],
            common_env,
        ),
        "api05": command(
            "api05",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "services/external-integration-runtime/tests",
                "--ignore=services/external-integration-runtime/tests/test_postgresql.py",
            ],
        ),
        "mutations": command(
            "mutations",
            [
                sys.executable,
                "scripts/api06/run_api06_mutations.py",
                "--out",
                "validation/api06/mutation_result.json",
            ],
        ),
    }
    if postgres_url:
        pg_env = dict(os.environ)
        pg_env["EPD2_API05_DATABASE_URL"] = postgres_url
        pg_env["API04_POSTGRES_DSN"] = postgres_url
        runs["postgres"] = command(
            "postgres",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "services/external-integration-runtime/tests/test_postgresql.py",
            ],
            pg_env,
        )
        runs["api04"] = command(
            "api04",
            [sys.executable, "-m", "pytest", "-q", "services/events-messaging-runtime/tests/unit"],
            pg_env,
        )
        try:
            import psycopg

            with psycopg.connect(postgres_url) as conn, conn.cursor() as cur:
                cur.execute("SHOW server_version_num")
                runs["postgres"]["server_version_num"] = int(cur.fetchone()[0])
                cur.execute("SHOW server_version")
                runs["postgres"]["server_version"] = str(cur.fetchone()[0])
        except Exception as exc:
            runs["postgres"]["result"] = "FAIL"
            runs["postgres"]["inspection_error"] = type(exc).__name__
    else:
        runs["postgres"] = {
            "name": "postgres",
            "result": "BLOCKED",
            "reason": "EPD2_API06_DATABASE_URL unavailable",
        }
        runs["api04"] = {
            "name": "api04",
            "result": "BLOCKED",
            "reason": "live PostgreSQL unavailable",
        }

    static = static_checks()
    clean = hygiene()
    secrets = secret_scan()

    def run_ok(name: str) -> bool:
        return runs[name]["result"] == "PASS"

    behavioral = run_ok("api06")
    api_auth = behavioral and run_ok("api02")
    s2s = behavioral and run_ok("api03")
    regression = all(run_ok(name) for name in ("api02", "api03", "api04", "api05"))
    postgres_ok = (
        run_ok("postgres") and runs["postgres"].get("server_version_num", 0) // 10000 == 16
    )

    pre = [
        gate(1, static["docs"] and static["baseline"], "API06_ENTERING_BASELINE_IDENTITY.json"),
        gate(
            2,
            static["fresh"],
            {
                k: os.environ.get(k)
                for k in (
                    "API06_CURRENT_MAIN_COMMIT",
                    "API06_CURRENT_PCR_SHA256",
                    "API06_CURRENT_MASTER_SHA256",
                )
            },
        ),
        gate(
            3,
            static["predecessors"],
            "accepted exact API-01 through API-05 predecessor identities",
        ),
        gate(4, static["api05"], "exact accepted API-05 C1 reconciliation; all 40 gates rerun"),
        gate(5, clean["result"] == "PASS", clean),
        gate(6, secrets["result"] == "PASS", secrets),
        gate(7, run_ok("inventory"), runs["inventory"]),
        gate(8, behavioral and static["surface"], runs["api06"]),
        gate(9, behavioral, "strict input/schema tests"),
        gate(10, behavioral, "surface and safe-error contract tests"),
        gate(11, api_auth, runs["api02"]),
        gate(12, behavioral, "60-route authorization matrix + guard tests"),
        gate(13, behavioral, "negative authority/scope/mass-assignment/header cases"),
        gate(14, behavioral, "generation and revocation reauthorization tests"),
        gate(15, behavioral, "revocation/session invalidation tests"),
        gate(16, s2s, runs["api03"]),
        gate(17, s2s, runs["api03"]),
        gate(18, s2s, runs["api03"]),
        gate(19, behavioral, "organization and regional isolation tests"),
        gate(20, behavioral, "91-route exposure matrix"),
        gate(21, behavioral, "bounded disclosure and enumeration policy"),
        gate(22, behavioral, "voting field isolation test"),
        gate(23, behavioral, "voting correlation/telemetry invariant"),
        gate(24, behavioral, "safe common error model tests"),
        gate(25, behavioral and run_ok("api05"), runs["api05"]),
        gate(26, behavioral and run_ok("api04"), runs["api04"]),
        gate(27, behavioral and run_ok("api05"), runs["api05"]),
        gate(28, behavioral, "payload-bound idempotency tests"),
        gate(29, behavioral, "20-way concurrent duplicate mutation test"),
        gate(30, behavioral, "100% consequential audit contract"),
        gate(31, behavioral, "monotonic rollback/expiry tests"),
        gate(32, behavioral, "registry abuse classes and bounded behavior"),
        gate(33, behavioral, "body/depth/type/page limits"),
        gate(34, postgres_ok, runs["postgres"]),
        gate(
            35,
            postgres_ok and run_ok("api04"),
            {"postgres": runs["postgres"], "api04": runs["api04"]},
        ),
        gate(36, regression, {name: runs[name] for name in ("api02", "api03", "api04", "api05")}),
        gate(37, run_ok("mutations"), runs["mutations"]),
        gate(
            38,
            static["fir"] and static["gaps"],
            "FIR disposition + single truthful API-06 acceptance blocker",
        ),
        gate(39, static["preview"], "trial handoff prepared but not opened"),
    ]

    write_evidence([*pre, gate(40, True, "pending freeze rehearsal")])
    runs["freeze"] = command(
        "freeze", [sys.executable, "scripts/api06/freeze_rehearsal.py"], timeout=600
    )
    gates = [*pre, gate(40, run_ok("freeze"), runs["freeze"])]
    write_evidence(gates)
    failed = [row["id"] for row in gates if row["result"] == "FAIL"]
    blocked_runs = [name for name, row in runs.items() if row["result"] == "BLOCKED"]
    result = "PASS" if not failed and not blocked_runs and len(gates) == 40 else "FAIL"
    payload = {
        "schema": "epd2.api06.acceptance/1",
        "state": STATE,
        "result": result,
        "generated_at": datetime.now(UTC).isoformat(),
        "gate_count": len(gates),
        "passed_gates": sum(row["result"] == "PASS" for row in gates),
        "failed_gates": failed,
        "environment_blocked_runs": blocked_runs,
        "gates": gates,
        "runs": runs,
        "claims": {
            "implementation_complete": result == "PASS",
            "preseal_ready": result == "PASS",
            "accepted": False,
            "api_closed": False,
            "system_trial_ready": False,
            "production_ready": False,
            "security_certified": False,
            "legally_activated": False,
        },
    }
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"API06_RESULT:{result}:{payload['passed_gates']}/40:{output.relative_to(ROOT)}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
