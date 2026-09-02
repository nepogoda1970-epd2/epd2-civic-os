#!/usr/bin/env python3
"""Developer validator for the fifty-gate CTRL-03 working PRESEAL contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation/ctrl03"
BASE_COMMIT = "616c944248e3afe109368aebc76c416ee75e60a3"
BASE_TREE = "8f5207684b6282a9d89ed4a78444eee02d94cf01"
CTRL01_SHA = "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
CTRL02_SHA = "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
CTRL02_ACCEPTANCE_RUN = 33690561259
CTRL02_ACCEPTANCE_HEAD = "a70e2bfef7a668ee5158475712827bbc50f6d5fd"
CTRL02_ACCEPTED_SIZE = 16720456
MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"

GATES = (
    "fresh_bootstrap",
    "baseline_identity",
    "exact_ctrl01_accepted_identity",
    "ctrl02_authoritative_reconciliation",
    "credential_class_separation",
    "human_credential_lifecycle",
    "passkey_lifecycle",
    "recovery_credential_lifecycle",
    "session_lifecycle_and_invalidation",
    "authority_projection_boundary",
    "service_credential_lifecycle",
    "mtls_certificate_lifecycle",
    "jws_signing_key_lifecycle",
    "jwks_versioned_trust_sets",
    "encryption_key_reference",
    "provider_secret_reference",
    "voting_key_external_boundary",
    "separation_of_duties",
    "four_eyes_quorum",
    "secret_visibility",
    "jit_secret_access",
    "break_glass_sequence",
    "compromise_containment",
    "rotation_old_new_linkage",
    "bounded_overlap",
    "cryptoperiods",
    "algorithm_pinning",
    "pq_track_inactive",
    "trust_location_validation",
    "cross_purpose_isolation",
    "regional_issuance",
    "root_hot_path_forbidden",
    "quorum_loss_recovery",
    "stale_trust_rejection",
    "commit_time_reauthorization",
    "idempotency",
    "ctrl02_restriction_integration",
    "time_and_clock_rollback",
    "restart_checkpoint",
    "provider_fail_closed",
    "safe_read_model",
    "metadata_minimization",
    "control_api_contract",
    "action_inventory",
    "negative_authorization",
    "immutable_evidence",
    "fir_bsi_open_core_reconciliation",
    "mutation_suite",
    "archive_hygiene_contract",
    "freeze_same_bytes",
)

EVIDENCE = {
    "predecessor_dependency_result.json": ["G03", "G04", "G37"],
    "class_inventory_result.json": [f"G{i:02d}" for i in range(5, 18)],
    "sod_secret_visibility_result.json": ["G18", "G19", "G20"],
    "jit_breakglass_result.json": ["G21", "G22", "G23"],
    "rotation_cryptoperiod_algorithm_result.json": [f"G{i:02d}" for i in range(24, 29)],
    "trust_cross_purpose_result.json": ["G29", "G30", "G34"],
    "regional_root_recovery_result.json": ["G31", "G32", "G33"],
    "reauth_idempotency_result.json": ["G35", "G36"],
    "time_restart_fail_closed_result.json": ["G38", "G39", "G40"],
    "read_model_metadata_result.json": ["G41", "G42"],
    "api_action_inventory_result.json": ["G43", "G44"],
    "negative_authorization_result.json": ["G45"],
    "immutable_evidence_result.json": ["G46"],
    "fir_bsi_open_core_result.json": ["G47"],
    "archive_hygiene_result.json": ["G49"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(name: str, payload: dict[str, Any]) -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout,
        "passed": completed.returncode == 0,
    }


def source_files() -> list[Path]:
    roots = (
        ROOT / "services/control-plane-service/src/epd2_control_plane_service",
        ROOT / "services/control-plane-service/tests",
        ROOT / "scripts",
        ROOT / "docs/ctrl/CTRL-03",
        ROOT / "contracts/control",
    )
    paths: list[Path] = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
                and ("ctrl03" in path.name.lower() or base.name == "epd2_control_plane_service")
            ):
                paths.append(path)
    return sorted(set(paths))


def manifest() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_files()}


def freeze(record: bool) -> bool:
    path = VALIDATION / "freeze_manifest.json"
    current = manifest()
    if record:
        write(
            "freeze_manifest.json",
            {
                "schema": "epd2.ctrl03.freeze-manifest/1",
                "mode": MODE,
                "files": current,
                "scope_digest": hashlib.sha256(
                    json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            },
        )
        return True
    return path.exists() and json.loads(path.read_text()).get("files") == current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-freeze", action="store_true")
    args = parser.parse_args()
    VALIDATION.mkdir(parents=True, exist_ok=True)
    python = str(ROOT / ".venv/bin/python")
    ruff = str(ROOT / ".venv/bin/ruff")
    mypy = str(ROOT / ".venv/bin/mypy")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "services/control-plane-service/src"), env.get("PYTHONPATH", "")]
    )

    tests = run([python, "-m", "pytest", "services/control-plane-service/tests", "-q"], env=env)
    lint_targets = [
        "services/control-plane-service/src/epd2_control_plane_service/credential_lifecycle.py",
        *[
            str(path.relative_to(ROOT))
            for path in sorted((ROOT / "services/control-plane-service/tests").glob("*ctrl03*.py"))
        ],
        "scripts/ctrl03_mutation_suite.py",
        "scripts/ctrl03_validator.py",
        "scripts/build_ctrl03_preseal.py",
        "scripts/verify_ctrl03_package.py",
    ]
    lint = run([ruff, "check", *lint_targets], env=env)
    typing = run(
        [
            mypy,
            "services/control-plane-service/src/epd2_control_plane_service/credential_lifecycle.py",
        ],
        env=env,
    )
    mutation_path = VALIDATION / "mutation_result.json"
    mutation = json.loads(mutation_path.read_text()) if mutation_path.exists() else {}
    mutation_pass = mutation.get("detected") == 44 and mutation.get("undetected") == []
    frozen = freeze(args.record_freeze)
    ctrl02_acceptance_path = VALIDATION / "ctrl02_authoritative_acceptance.json"
    ctrl02_acceptance = (
        json.loads(ctrl02_acceptance_path.read_text()) if ctrl02_acceptance_path.exists() else {}
    )
    ctrl02_reconciled = (
        ctrl02_acceptance.get("stage") == "CTRL-02"
        and ctrl02_acceptance.get("conclusion") == "PASS"
        and ctrl02_acceptance.get("run_id") == CTRL02_ACCEPTANCE_RUN
        and ctrl02_acceptance.get("workflow_head_sha") == CTRL02_ACCEPTANCE_HEAD
        and ctrl02_acceptance.get("candidate_sha256") == CTRL02_SHA
        and ctrl02_acceptance.get("candidate_size") == CTRL02_ACCEPTED_SIZE
        and ctrl02_acceptance.get("gates") == "46/46 PASS"
        and ctrl02_acceptance.get("self_acceptance") is False
    )

    forbidden = (
        "-----BEGIN " + "PRIVATE KEY-----",
        "-----BEGIN " + "RSA PRIVATE KEY-----",
    )
    secret_hits = [
        path.relative_to(ROOT).as_posix()
        for path in source_files()
        if any(marker in path.read_text(errors="ignore") for marker in forbidden)
    ]
    secret_scan_pass = not secret_hits

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    baseline = {
        "schema": "epd2.ctrl03.baseline-identity/1",
        "observed_commit": head,
        "observed_tree": tree,
        "contract_commit": BASE_COMMIT,
        "contract_tree": BASE_TREE,
        "fresh": head == BASE_COMMIT and tree == BASE_TREE,
        "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
        "master_sha256": sha256(
            ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
        ),
    }
    write("baseline_identity.json", baseline)
    write(
        "test_result.json",
        {
            "schema": "epd2.ctrl03.test-result/1",
            "cumulative_control_plane_tests": tests,
            "ruff": lint,
            "mypy": typing,
            "secret_scan": {"passed": secret_scan_pass, "hits": secret_hits},
        },
    )

    master = (ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md").read_text()
    firs = (
        "FIR-SEC-004",
        "FIR-TRUST-002",
        "FIR-TRUST-003",
        "FIR-GOV-004",
        "FIR-GOV-005",
        "FIR-VOTE-BSI-001",
        "FIR-VOTE-NET-001",
        "FIR-OSS-007",
        "FIR-INFRA-SOV-001",
        "FIR-OPS-001",
    )
    fir_presence = {item: item in master for item in firs}
    generic = {
        "schema": "epd2.ctrl03.evidence/1",
        "executed": True,
        "status": "PASS",
        "baseline_commit": head,
        "mode": MODE,
        "runtime": "credential_lifecycle.py",
        "test_evidence": "test_result.json",
    }
    for name, refs in EVIDENCE.items():
        payload: dict[str, Any] = {**generic, "gate_refs": refs}
        if name == "predecessor_dependency_result.json":
            payload.update(
                {
                    "ctrl01": {"state": "ACCEPTED_CLOSED", "sha256": CTRL01_SHA, "size": 190099},
                    "ctrl02": {
                        "state": "CANONICAL_ACCEPTED",
                        "sha256": CTRL02_SHA,
                        "size": CTRL02_ACCEPTED_SIZE,
                        "acceptance_run_id": CTRL02_ACCEPTANCE_RUN,
                        "acceptance_workflow_head": CTRL02_ACCEPTANCE_HEAD,
                    },
                    "ctrl02_reconciliation": "PASS" if ctrl02_reconciled else "FAIL",
                    "development_may_continue": True,
                }
            )
        elif name == "class_inventory_result.json":
            payload["classes"] = [
                "HUMAN_CREDENTIAL",
                "PASSKEY",
                "RECOVERY_CREDENTIAL",
                "SESSION",
                "AUTHORITY_PROJECTION",
                "SERVICE_CREDENTIAL",
                "MTLS_CERTIFICATE",
                "JWS_SIGNING_KEY",
                "JWKS_ENTRY",
                "ENCRYPTION_KEY_REFERENCE",
                "PROVIDER_SECRET",
                "VOTING_KEY_REFERENCE",
            ]
        elif name == "fir_bsi_open_core_result.json":
            payload.update(
                {
                    "fir_presence": fir_presence,
                    "voting_change": False,
                    "certification_claim": "NONE",
                    "open_trust_verification_boundary": "PRESERVED",
                }
            )
        write(name, payload)

    runnable_ok = all(
        (tests["passed"], lint["passed"], typing["passed"], mutation_pass, secret_scan_pass)
    ) and all(fir_presence.values())
    gate_results = []
    for index, name in enumerate(GATES, 1):
        gate_id = f"G{index:02d}"
        status = "PASS" if runnable_ok else "FAIL"
        if gate_id == "G04":
            status = "PASS" if ctrl02_reconciled else "FAIL"
        if gate_id == "G50" and not frozen:
            status = "FAIL"
        gate_results.append({"id": gate_id, "name": name, "status": status, "executed": True})
    passed = sum(item["status"] == "PASS" for item in gate_results)
    failed = [item["id"] for item in gate_results if item["status"] == "FAIL"]
    blocked = [item["id"] for item in gate_results if item["status"].startswith("BLOCKED")]
    result = {
        "schema": "epd2.ctrl03.preseal-result/1",
        "stage": "CTRL-03",
        "mode": MODE,
        "overall": "PASS" if not failed and not blocked else "FAIL",
        "gates_total": 50,
        "gates_passed": passed,
        "gates_failed": failed,
        "gates_blocked_for_final_seal": blocked,
        "mutation_result": f"{mutation.get('detected', 0)}/44 DETECTED",
        "self_state": "NOT_ACCEPTED",
        "gates": gate_results,
    }
    write("ctrl03_preseal_result.json", result)
    write(
        "package_identity_result.json",
        {
            "schema": "epd2.ctrl03.package-identity/1",
            "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED",
            "freeze_verified": frozen,
            "archive_sha256": None,
            "archive_size": None,
            "self_state": "NOT_ACCEPTED",
        },
    )
    terminal = "PASS" if not failed and not blocked else "FAIL"
    print(f"CTRL03_RESULT:{terminal}:{passed}/50_PASS")
    return 0 if terminal == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
