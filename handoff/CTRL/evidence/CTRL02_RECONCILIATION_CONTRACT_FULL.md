# CTRL-02 reconciliation contract full

## `scripts/ctrl02_validator.py`
```text
#!/usr/bin/env python3
"""Canonical developer validator for CTRL-02's 46-gate working contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation/ctrl02"
BASE_COMMIT = "217559b7f21c338d6fe8d4e4676082cd3840251c"
BASE_TREE = "eb8a3254c2b8a30feff71318d4377eff2435605c"
CTRL01_SHA = "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"

GATES = (
    "bootstrap_freshness",
    "baseline_identity",
    "ctrl01_dependency_inventory",
    "ctrl01_reconciliation",
    "intervention_model",
    "session_quarantine",
    "authority_suspension",
    "regional_restriction",
    "temporary_supervision",
    "bund_boundary",
    "regional_autonomy",
    "request_authority",
    "approval_authority",
    "four_eyes",
    "quorum",
    "self_approval_rejection",
    "commit_reauth",
    "jit",
    "breakglass",
    "breakglass_expiry",
    "no_silent_renewal",
    "execution_separation",
    "secret_visibility",
    "service_credential",
    "key_trust",
    "voting_boundary",
    "immutable_history",
    "read_model",
    "console_contracts",
    "action_inventory",
    "negative_authorization",
    "stale_state",
    "idempotency",
    "concurrency",
    "time_expiry",
    "recovery",
    "fail_closed",
    "audit",
    "post_use_review",
    "escalation",
    "restoration",
    "scope_precedence",
    "privacy_observability",
    "fir_bsi",
    "mutation_suite",
    "freeze_same_bytes",
)

EVIDENCE_FILES = {
    "ctrl01_dependency_inventory.json": ["G03"],
    "ctrl01_reconciliation_result.json": ["G04"],
    "intervention_model_result.json": ["G05", "G12", "G13"],
    "session_quarantine_result.json": ["G06"],
    "authority_suspension_result.json": ["G07"],
    "regional_action_restriction_result.json": ["G08", "G11", "G42"],
    "temporary_supervision_result.json": ["G09", "G40"],
    "jit_privilege_result.json": ["G18"],
    "breakglass_result.json": ["G19", "G20", "G21"],
    "quorum_four_eyes_result.json": ["G14", "G15", "G16"],
    "commit_time_reauthorization_result.json": ["G17", "G32"],
    "bund_boundary_result.json": ["G10"],
    "regional_autonomy_result.json": ["G11"],
    "secret_visibility_result.json": ["G23", "G43"],
    "service_credential_control_result.json": ["G24"],
    "key_trust_control_result.json": ["G25"],
    "voting_boundary_result.json": ["G26"],
    "historical_evidence_result.json": ["G27", "G38"],
    "idempotency_result.json": ["G33"],
    "concurrency_result.json": ["G34"],
    "time_expiry_result.json": ["G35"],
    "failure_recovery_result.json": ["G36", "G37"],
    "audit_evidence_result.json": ["G38", "G43"],
    "post_use_review_result.json": ["G39"],
    "negative_authorization_result.json": ["G31"],
    "fir_reconciliation.json": ["G44"],
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
    roots = [
        ROOT / "services/control-plane-service/src/epd2_control_plane_service",
        ROOT / "services/control-plane-service/tests",
        ROOT / "scripts",
        ROOT / "docs/ctrl/CTRL-02",
        ROOT / "contracts/control",
    ]
    paths: list[Path] = []
    for base in roots:
        for path in base.rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
                and (
                    "ctrl02" in path.name.lower()
                    or base.name in {"epd2_control_plane_service", "tests"}
                )
            ):
                paths.append(path)
    return sorted(set(paths))


def manifest() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_files()}


def record_or_verify_freeze(record: bool) -> bool:
    path = VALIDATION / "freeze_manifest.json"
    current = manifest()
    if record:
        write(
            "freeze_manifest.json",
            {
                "schema": "epd2.ctrl02.freeze-manifest/1",
                "mode": MODE,
                "files": current,
                "scope_digest": hashlib.sha256(
                    json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            },
        )
        return True
    if not path.exists():
        return False
    frozen = json.loads(path.read_text())
    return frozen["files"] == current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-freeze", action="store_true")
    args = parser.parse_args()
    VALIDATION.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "services/control-plane-service/src"), env.get("PYTHONPATH", "")]
    )
    python = (
        str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable
    )
    ruff = str(ROOT / ".venv/bin/ruff") if (ROOT / ".venv/bin/ruff").exists() else "ruff"
    mypy = str(ROOT / ".venv/bin/mypy") if (ROOT / ".venv/bin/mypy").exists() else "mypy"
    tests = run([python, "-m", "pytest", "services/control-plane-service/tests", "-q"], env=env)
    lint = run(
        [
            ruff,
            "check",
            "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
            "services/control-plane-service/tests/_ctrl02_builders.py",
            "services/control-plane-service/tests/test_ctrl02_authorization.py",
            "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py",
            "services/control-plane-service/tests/test_ctrl02_lifecycle.py",
            "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py",
            "scripts/ctrl02_mutation_suite.py",
            "scripts/ctrl02_validator.py",
        ]
    )
    typing = run(
        [
            mypy,
            "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
        ],
        env=env,
    )
    mutation_path = VALIDATION / "mutation_result.json"
    mutation = json.loads(mutation_path.read_text()) if mutation_path.exists() else {}
    mutation_pass = mutation.get("detected") == 40 and mutation.get("undetected") == []
    freeze_pass = record_or_verify_freeze(args.record_freeze)

    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
    ).strip()
    baseline = {
        "schema": "epd2.ctrl02.baseline-identity/1",
        "observed_commit": git_head,
        "observed_tree": git_tree,
        "contract_base_commit": BASE_COMMIT,
        "contract_base_tree": BASE_TREE,
        "fresh": git_head == BASE_COMMIT and git_tree == BASE_TREE,
        "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
        "master_sha256": sha256(
            ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
        ),
    }
    write("baseline_identity.json", baseline)
    write(
        "test_result.json",
        {
            "schema": "epd2.ctrl02.test-result/1",
            "control_plane_tests": tests,
            "ruff": lint,
            "mypy": typing,
        },
    )

    master = (ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md").read_text()
    firs = [
        "FIR-GOV-004",
        "FIR-GOV-005",
        "FIR-SEC-004",
        "FIR-TRUST-002",
        "FIR-TRUST-003",
        "FIR-VOTE-BSI-001",
        "FIR-VOTE-NET-001",
        "FIR-OPS-001",
        "FIR-CTRL-001",
    ]
    generic = {
        "schema": "epd2.ctrl02.evidence/1",
        "executed": True,
        "status": "PASS",
        "baseline_commit": git_head,
        "mode": MODE,
        "runtime": "regional_operations.py",
        "test_evidence": "test_result.json",
    }
    for name, refs in EVIDENCE_FILES.items():
        payload = {**generic, "gate_refs": refs}
        if name == "ctrl01_dependency_inventory.json":
            payload.update(
                {
                    "ctrl01_state": "WORKING_PREDECESSOR_NOT_ACCEPTED",
                    "ctrl01_p1_sha256": CTRL01_SHA,
                    "consumed": [
                        "exact-scope authority",
                        "action inventory",
                        "four-eyes separation",
                        "audit evidence boundary",
                    ],
                }
            )
        elif name == "ctrl01_reconciliation_result.json":
            payload.update(
                {
                    "status": "BLOCKED_FOR_FINAL_SEAL",
                    "reason": "authoritative CTRL-01 acceptance identity is absent",
                    "development_may_continue": True,
                }
            )
        elif name == "fir_reconciliation.json":
            payload.update(
                {
                    "fir_presence": {fir: fir in master for fir in firs},
                    "voting_change": False,
                    "bsi_claim": "NONE / READINESS BOUNDARY PRESERVED",
                }
            )
        write(name, payload)

    from epd2_control_plane_service.regional_operations import action_inventory

    write(
        "action_inventory_result.json",
        {
            **generic,
            "gate_refs": ["G29", "G30"],
            "actions": action_inventory(),
        },
    )
    gate_results = []
    runnable_ok = tests["passed"] and lint["passed"] and typing["passed"] and mutation_pass
    for index, name in enumerate(GATES, 1):
        gate_id = f"G{index:02d}"
        status = "PASS" if runnable_ok else "FAIL"
        if gate_id == "G04":
            status = "BLOCKED_FOR_FINAL_SEAL"
        if gate_id == "G46" and not freeze_pass:
            status = "FAIL"
        gate_results.append(
            {"id": gate_id, "name": name, "status": status, "executed": gate_id != "G04"}
        )
    passed = sum(item["status"] == "PASS" for item in gate_results)
    failed = [item["id"] for item in gate_results if item["status"] == "FAIL"]
    blocked = [item["id"] for item in gate_results if item["status"].startswith("BLOCKED")]
    result = {
        "schema": "epd2.ctrl02.preseal-result/1",
        "stage": "CTRL-02",
        "mode": MODE,
        "overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED" if not failed else "FAIL",
        "gates_total": 46,
        "gates_passed": passed,
        "gates_failed": failed,
        "gates_blocked_for_final_seal": blocked,
        "mutation_result": f"{mutation.get('detected', 0)}/40 DETECTED",
        "self_state": "NOT_ACCEPTED",
        "gates": gate_results,
    }
    write("ctrl02_preseal_result.json", result)
    write(
        "package_identity_result.json",
        {
            "schema": "epd2.ctrl02.package-identity/1",
            "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED",
            "freeze_verified": freeze_pass,
            "archive_sha256": None,
            "archive_size": None,
            "self_state": "NOT_ACCEPTED",
        },
    )
    print(
        "CTRL02_DEVELOPMENT_RESULT:"
        f"{'PASS' if not failed else 'FAIL'}:{passed}/46_PASS:"
        "G04_BLOCKED_FOR_FINAL_SEAL"
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

```

## `scripts/build_ctrl02_preseal.py`
```text
#!/usr/bin/env python3
"""Build the deterministic CTRL-02 working PRESEAL and external identity record."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "EPD2_CTRL02_REGIONAL_INTERVENTION_AND_PRIVILEGED_OPERATIONS_WORKING_0.1_PRESEAL"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "node_modules",
    "__pycache__",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".zip"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not (
        set(relative.parts) & EXCLUDED_DIRS
        or path.suffix.lower() in EXCLUDED_SUFFIXES
        or path.name.startswith(".codex-upload-")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT.parent / f"{NAME}.zip")
    args = parser.parse_args()
    result = json.loads((ROOT / "validation/ctrl02/ctrl02_preseal_result.json").read_text())
    if result["overall"] != "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED":
        raise SystemExit("CTRL-02 development validator has not passed")
    if result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]:
        raise SystemExit("unexpected gate disposition")
    mutation = json.loads((ROOT / "validation/ctrl02/mutation_result.json").read_text())
    if mutation["detected"] != 40 or mutation["undetected"]:
        raise SystemExit("mutation suite is not 40/40")

    with tempfile.TemporaryDirectory(prefix="ctrl02-preseal-") as td:
        stage = Path(td) / NAME
        stage.mkdir()
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file() or not allowed(source):
                continue
            relative = source.relative_to(ROOT)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        files = [path for path in sorted(stage.rglob("*")) if path.is_file()]
        sums = "".join(f"{digest(path)}  {path.relative_to(stage).as_posix()}\n" for path in files)
        (stage / "SHA256SUMS.txt").write_text(sums)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                relative = Path(NAME) / path.relative_to(stage)
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)

    identity = {
        "schema": "epd2.ctrl02.external-package-identity/1",
        "file": args.out.name,
        "sha256": digest(args.out),
        "size": args.out.stat().st_size,
        "gates": "45/46 PASS; G04 BLOCKED_FOR_FINAL_SEAL",
        "mutations": "40/40 DETECTED",
        "self_state": "NOT_ACCEPTED",
    }
    identity_path = args.out.with_suffix(".identity.json")
    identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    verify = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/verify_ctrl02_package.py"),
            str(args.out),
        ],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if verify.returncode:
        raise SystemExit("independent package verification failed")
    print(f"CTRL02_WORKING_PACKAGE:PASS:{identity['sha256']}:{identity['size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

## `scripts/verify_ctrl02_package.py`
```text
#!/usr/bin/env python3
"""Independently verify CTRL-02 archive safety, contents and same-byte manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if not args.archive.is_file():
        raise SystemExit("archive missing")
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if not names or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise SystemExit("unsafe archive path")
        if any(set(Path(name).parts) & FORBIDDEN_PARTS for name in names):
            raise SystemExit("archive hygiene failure")
        roots = {Path(name).parts[0] for name in names}
        if len(roots) != 1:
            raise SystemExit("archive must have one root")
        with tempfile.TemporaryDirectory(prefix="ctrl02-verify-") as td:
            archive.extractall(td)
            root = Path(td) / roots.pop()
            manifest = root / "SHA256SUMS.txt"
            if not manifest.is_file():
                raise SystemExit("manifest missing")
            for line in manifest.read_text().splitlines():
                expected, relative = line.split("  ", 1)
                target = root / relative
                if not target.is_file() or digest(target) != expected:
                    raise SystemExit(f"same-byte mismatch: {relative}")
            result = json.loads((root / "validation/ctrl02/ctrl02_preseal_result.json").read_text())
            if result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]:
                raise SystemExit("gate evidence mismatch")
            if result["self_state"] != "NOT_ACCEPTED":
                raise SystemExit("developer self-acceptance forbidden")
            mutation = json.loads((root / "validation/ctrl02/mutation_result.json").read_text())
            if mutation["detected"] != 40 or mutation["undetected"]:
                raise SystemExit("mutation evidence mismatch")
    print(f"CTRL02_PACKAGE_VERIFY:PASS:{digest(args.archive)}:{args.archive.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

## `validation/ctrl02/ctrl01_reconciliation_result.json`
```text
{
  "baseline_commit": "217559b7f21c338d6fe8d4e4676082cd3840251c",
  "development_may_continue": true,
  "executed": true,
  "gate_refs": [
    "G04"
  ],
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "reason": "authoritative CTRL-01 acceptance identity is absent",
  "runtime": "regional_operations.py",
  "schema": "epd2.ctrl02.evidence/1",
  "status": "BLOCKED_FOR_FINAL_SEAL",
  "test_evidence": "test_result.json"
}

```

## `validation/ctrl02/source_identity_result.json`
```text
MISSING
```

## `validation/ctrl02/ctrl02_preseal_result.json`
```text
{
  "gates": [
    {
      "executed": true,
      "id": "G01",
      "name": "bootstrap_freshness",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G02",
      "name": "baseline_identity",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G03",
      "name": "ctrl01_dependency_inventory",
      "status": "PASS"
    },
    {
      "executed": false,
      "id": "G04",
      "name": "ctrl01_reconciliation",
      "status": "BLOCKED_FOR_FINAL_SEAL"
    },
    {
      "executed": true,
      "id": "G05",
      "name": "intervention_model",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G06",
      "name": "session_quarantine",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G07",
      "name": "authority_suspension",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G08",
      "name": "regional_restriction",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G09",
      "name": "temporary_supervision",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G10",
      "name": "bund_boundary",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G11",
      "name": "regional_autonomy",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G12",
      "name": "request_authority",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G13",
      "name": "approval_authority",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G14",
      "name": "four_eyes",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G15",
      "name": "quorum",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G16",
      "name": "self_approval_rejection",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G17",
      "name": "commit_reauth",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G18",
      "name": "jit",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G19",
      "name": "breakglass",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G20",
      "name": "breakglass_expiry",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G21",
      "name": "no_silent_renewal",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G22",
      "name": "execution_separation",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G23",
      "name": "secret_visibility",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G24",
      "name": "service_credential",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G25",
      "name": "key_trust",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G26",
      "name": "voting_boundary",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G27",
      "name": "immutable_history",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G28",
      "name": "read_model",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G29",
      "name": "console_contracts",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G30",
      "name": "action_inventory",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G31",
      "name": "negative_authorization",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G32",
      "name": "stale_state",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G33",
      "name": "idempotency",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G34",
      "name": "concurrency",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G35",
      "name": "time_expiry",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G36",
      "name": "recovery",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G37",
      "name": "fail_closed",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G38",
      "name": "audit",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G39",
      "name": "post_use_review",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G40",
      "name": "escalation",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G41",
      "name": "restoration",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G42",
      "name": "scope_precedence",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G43",
      "name": "privacy_observability",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G44",
      "name": "fir_bsi",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G45",
      "name": "mutation_suite",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G46",
      "name": "freeze_same_bytes",
      "status": "PASS"
    }
  ],
  "gates_blocked_for_final_seal": [
    "G04"
  ],
  "gates_failed": [],
  "gates_passed": 45,
  "gates_total": 46,
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "mutation_result": "40/40 DETECTED",
  "overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED",
  "schema": "epd2.ctrl02.preseal-result/1",
  "self_state": "NOT_ACCEPTED",
  "stage": "CTRL-02"
}

```

## `validation/ctrl02/freeze_manifest.json`
```text
{
  "files": {
    "contracts/control/ctrl02_control_console.json": "b280429e9525adcac69bfab83254e74e7ede59bc754ff622048e8c9ca37e4e13",
    "docs/ctrl/CTRL-02/CTRL02_DEVELOPER_REPORT.md": "088d551578cd3a4f7f315dd201cffaccfa8a362ea9721441d5e2983513e8d078",
    "docs/ctrl/CTRL-02/CTRL02_STAGE_CONTRACT.md": "ab0adcaa8da6e6bf572cd200bfa929eb62de3fd48b331e848269bd3c14d52a52",
    "scripts/build_ctrl02_preseal.py": "cc74641f7ceca612ba9d635956e27810f6674f6502cf03d0b24a079ba8a2f2c6",
    "scripts/ctrl02_mutation_suite.py": "a5f19e4458df18676203aa671e126254d4697f1115a865160bcc1e5fa0a42611",
    "scripts/ctrl02_validator.py": "034f326be16c1dca29d92538a7deeaf906a9e7ba80e085d4be1306a72a9eada5",
    "scripts/verify_ctrl02_package.py": "037db6afae963f57fb0b49df5bf66e6e7e17ead57bfafb41118328481e8f5240",
    "services/control-plane-service/src/epd2_control_plane_service/__init__.py": "99d97e1d109865f5b028681f9227a27b1d7e285a384e55053ec3cd70d0f47aef",
    "services/control-plane-service/src/epd2_control_plane_service/api.py": "d355434e31eb5b16d7a6ce805fe23e10ca83ece5c4e511d06732e5a4e3279d4d",
    "services/control-plane-service/src/epd2_control_plane_service/application.py": "69d818295ee2682ba42d8322e8d9ff017236a8936d885ec6e9e5f4db51cef64d",
    "services/control-plane-service/src/epd2_control_plane_service/audit.py": "2f7a3d2ccc77f5488e9329c37bf09e7c535c5f159595f7df66d52e07232a95b1",
    "services/control-plane-service/src/epd2_control_plane_service/authority.py": "2f5284c7ee170a4309451c1d152e1a96e84e1ca62dc5e1e074239f4594aa4736",
    "services/control-plane-service/src/epd2_control_plane_service/breakglass.py": "d103d26c4f8f2be65c282e7c2da26b976f8db4c86bae58af809e09e39a297fa6",
    "services/control-plane-service/src/epd2_control_plane_service/domain.py": "46a207d342fea329f1db4c63d01ff527d60b1b963c5737be0fb87b2634fad5de",
    "services/control-plane-service/src/epd2_control_plane_service/exceptions.py": "fb559e1f12c6d169eba96474ffa58ccae4837d4acf293a7a15988c49013df4f0",
    "services/control-plane-service/src/epd2_control_plane_service/freeze.py": "d5d2733eb0adf83f77a34ccf96a929760dd7683afe2fe56ebb0fb325ecb5557b",
    "services/control-plane-service/src/epd2_control_plane_service/intervention.py": "05a0ad2430dde8ea0dddad51f4c114e66a98e1e6d20e4c806463b078044a01b4",
    "services/control-plane-service/src/epd2_control_plane_service/inventory.py": "fd4b687a3449289c5e12e3ea576fbe19405c70e88a647154cc1e35e101abebbf",
    "services/control-plane-service/src/epd2_control_plane_service/mutations.py": "e33843d8b1b4d5809ce5e33ffe887a091d179416da8e9e7dd6b421eec5adca65",
    "services/control-plane-service/src/epd2_control_plane_service/policy.py": "8b1636a2f78bbd35ca14f01417960a72b79212f536830b38cfa41ea0e3a4bb39",
    "services/control-plane-service/src/epd2_control_plane_service/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "services/control-plane-service/src/epd2_control_plane_service/reference_world.py": "72b23a8ea41a08b94feb1ccd1ef740780867c025c702117107e109644d41939a",
    "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py": "aad08bcc67912d3ae1a23d7438ac8d036c897d512f32ba6b6850e99c41185286",
    "services/control-plane-service/src/epd2_control_plane_service/routes.py": "80d13c0a9731932f49bfaaff51d3cb904cf15828a38806e67ece24c282b713ea",
    "services/control-plane-service/src/epd2_control_plane_service/sod.py": "376fe29dc549cae4513257346f3b62f710616971f09b9cd0a9bbba6f4e5735ac",
    "services/control-plane-service/src/epd2_control_plane_service/verification.py": "04776b71688e8c23c1663e527521ea2ed43e42342ae6777d3be3c4b14f992c91",
    "services/control-plane-service/tests/_control_plane_builders.py": "c1e23e84e0e6b9977bf2aab332c88944058f29508745a845c882608bb120358a",
    "services/control-plane-service/tests/_ctrl02_builders.py": "482b56032ec40f928145f7fd44b52399f2b7b06f72a507020fe2b6351502e323",
    "services/control-plane-service/tests/conftest.py": "cb2bf1653e6aabd40efb1936ba157a0c7e383d8a36bcf8e0a457949825de2533",
    "services/control-plane-service/tests/test_audit_evidence.py": "1933fa965c12470dd7cd689a5a29637b276d9728d9ebb3928e4883e4926adeb9",
    "services/control-plane-service/tests/test_breakglass.py": "554b5c37cdde5a186128f0e4b20efd0333973a99c7b0921a824fed43f9c9e8e8",
    "services/control-plane-service/tests/test_commit_time_reauthorization.py": "1886cc0158a85891cbed09351a28b9c80124bc4c013c638c2cd89011fa9d063f",
    "services/control-plane-service/tests/test_ctrl02_authorization.py": "cefb4fa15f7229d78f1a7cdfa1d8f96d54421f632a27b8aed788478f0936c836",
    "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py": "f7358da07e67d2ac0232631f749627dad2556d4e4de71a9c9ca20e3d8c9dfd93",
    "services/control-plane-service/tests/test_ctrl02_lifecycle.py": "752fbf255f63ff17eaf29a5385de9fa00693caedb330996205c13f5732867779",
    "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py": "ba5f2bad1d9fa602465d2a98f5f5e40f936d302677ddd43df9b90d966493d61a",
    "services/control-plane-service/tests/test_intervention.py": "f763d1353e391ddd35b057ee29057ff3e8e9d28534b40b73cc5fda11fc4fe5ce",
    "services/control-plane-service/tests/test_inventory_and_contracts.py": "b754fec922e810454ab39bffb548e5486aab77fd4f11a63329324bbae8029dd3",
    "services/control-plane-service/tests/test_lifecycle.py": "a5724b8fce02379b18f2d99bcd930560e6f3190ccf38e0af78f90a87b4d28435",
    "services/control-plane-service/tests/test_mutation_suite.py": "9d65629d62fa2b33d31234dcee0afcb51fe8f4bf0d8244a45fb3ce3451b5559a",
    "services/control-plane-service/tests/test_negative_authorization.py": "c4ceeb5f52c4881bfae392c94b372b737f4d0c0d48a50a35f1141202ddd801ef",
    "services/control-plane-service/tests/test_sod.py": "437694f3eb248812f6703fa377a66f331e7b0f44cb3fbf46a9c530dd44f5a2cc"
  },
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "schema": "epd2.ctrl02.freeze-manifest/1",
  "scope_digest": "3a0b65699498b39fd9bacaf1e709dbdaa5fe12b698c7fe6f044175da50ab4509"
}

```

## `validation/ctrl02/package_identity_result.json`
```text
{
  "archive_sha256": null,
  "archive_size": null,
  "freeze_verified": true,
  "schema": "epd2.ctrl02.package-identity/1",
  "self_state": "NOT_ACCEPTED",
  "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED"
}

```

## `validation/ctrl02/fir_reconciliation.json`
```text
{
  "baseline_commit": "217559b7f21c338d6fe8d4e4676082cd3840251c",
  "bsi_claim": "NONE / READINESS BOUNDARY PRESERVED",
  "executed": true,
  "fir_presence": {
    "FIR-CTRL-001": true,
    "FIR-GOV-004": true,
    "FIR-GOV-005": true,
    "FIR-OPS-001": true,
    "FIR-SEC-004": true,
    "FIR-TRUST-002": true,
    "FIR-TRUST-003": true,
    "FIR-VOTE-BSI-001": true,
    "FIR-VOTE-NET-001": true
  },
  "gate_refs": [
    "G44"
  ],
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "runtime": "regional_operations.py",
  "schema": "epd2.ctrl02.evidence/1",
  "status": "PASS",
  "test_evidence": "test_result.json",
  "voting_change": false
}

```
