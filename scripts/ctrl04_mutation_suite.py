#!/usr/bin/env python3
"""CTRL-04 mutation / negative harness.

Forty-eight source mutants, one per family of `04_MUTATION_AND_NEGATIVE_TEST_PLAN`,
are applied to an isolated copy of the CTRL-04 runtime and the executable CTRL-04
test suite is run against each. A mutant is DETECTED only when the suite fails.
An UNDETECTED mutant means the tests do not actually enforce that obligation and
the candidate must not be sealed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services/control-plane-service"
PACKAGE = SERVICE / "src/epd2_control_plane_service"
TESTS = SERVICE / "tests"
VALIDATION = ROOT / "validation/ctrl04"
CONSOLE = "operations_console.py"
ADAPTERS = "operations_adapters.py"
API = "operations_api.py"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    family: str
    file: str
    edits: tuple[tuple[str, str], ...]


def policy_flip(mutation_id: str, family: str, obligation: str) -> Mutation:
    return Mutation(
        mutation_id,
        family,
        CONSOLE,
        ((f"    {obligation}: bool = True\n", f"    {obligation}: bool = False\n"),),
    )


MUTATIONS: tuple[Mutation, ...] = (
    policy_flip("M01", "remove commit-time reauthorization", "commit_time_reauthorization"),
    policy_flip("M02", "allow stale approval", "enforce_approval_freshness"),
    policy_flip("M03", "allow revoked session", "enforce_session_state"),
    policy_flip("M04", "ignore changed target identity", "enforce_target_version"),
    policy_flip("M05", "ignore changed deployment identity", "enforce_deployment_identity"),
    policy_flip("M06", "ignore changed parameters digest", "enforce_parameters_digest"),
    policy_flip("M07", "collapse requester and approver permissions", "reject_self_approval"),
    policy_flip(
        "M08", "allow approver to execute despite SoD rule", "separate_approval_from_execution"
    ),
    Mutation(
        "M09",
        "expose raw secret field",
        ADAPTERS,
        (
            (
                "        key_hit = any(marker in lowered for marker in SECRET_KEY_MARKERS) "
                "and not is_reference\n",
                "        key_hit = False\n",
            ),
        ),
    ),
    Mutation(
        "M10",
        "leak token into log/evidence",
        CONSOLE,
        (
            (
                "        if self.policy.enforce_secret_redaction:\n"
                "            # Secret-looking keys are dropped",
                "        if False:\n            # Secret-looking keys are dropped",
            ),
        ),
    ),
    policy_flip("M11", "bypass CTRL-02 policy", "enforce_ctrl02_state"),
    policy_flip("M12", "bypass CTRL-03 scoped authority", "enforce_ctrl03_trust"),
    policy_flip(
        "M13", "allow voting-origin operation from general console", "enforce_voting_boundary"
    ),
    policy_flip("M14", "treat dispatch ACK as success", "dispatch_is_not_success"),
    Mutation(
        "M15",
        "silently swallow provider failure",
        CONSOLE,
        (("        if not ack.accepted:\n", "        if False:\n"),),
    ),
    policy_flip(
        "M16", "permit unsupported operation as simulated success", "enforce_unsupported_explicit"
    ),
    policy_flip("M17", "disable idempotency", "enforce_idempotency"),
    Mutation(
        "M18",
        "permit duplicate execution",
        CONSOLE,
        (
            (
                "                if action.state in TERMINAL_ACTION_STATES or action.state is "
                "ActionState.EXECUTING:\n"
                "                    raise AuthorizationRefused(\n"
                '                        f"action already {action.state.value}; no duplicate '
                'execution",\n',
                "                if False:\n"
                "                    raise AuthorizationRefused(\n"
                '                        f"action already {action.state.value}; no duplicate '
                'execution",\n',
            ),
        ),
    ),
    policy_flip("M19", "break concurrency guard", "enforce_concurrency_guard"),
    Mutation(
        "M20",
        "permit replayed request",
        CONSOLE,
        (
            (
                "                        raise AuthorizationRefused(\n"
                '                            "idempotency key reused with different content",\n'
                "                            reason_code=OpsRefusal.IDEMPOTENCY_CONFLICT,\n"
                "                        )\n",
                "                        return existing\n",
            ),
        ),
    ),
    policy_flip("M21", "mutate historical evidence", "enforce_evidence_immutability"),
    Mutation(
        "M22",
        "omit actor provenance",
        CONSOLE,
        (
            (
                '            "schema": "epd2.ctrl04.evidence.v1",\n'
                '            "action_id": action.action_id,\n'
                '            "request_id": action.request_id,\n'
                '            "action_type": action.action_type.value,\n'
                '            "actor_ref": action.actor_ref,\n',
                '            "schema": "epd2.ctrl04.evidence.v1",\n'
                '            "action_id": action.action_id,\n'
                '            "request_id": action.request_id,\n'
                '            "action_type": action.action_type.value,\n'
                '            "actor_ref": "",\n',
            ),
        ),
    ),
    Mutation(
        "M23",
        "omit target provenance",
        CONSOLE,
        (
            (
                '            "target_ref": f"{action.target_id}@v{action.target_version}",\n',
                '            "target_ref": "",\n',
            ),
        ),
    ),
    Mutation(
        "M24",
        "omit deployment identity",
        CONSOLE,
        (
            (
                '            "result_state": action.result_state.value,\n'
                '            "deployment_identity_ref": action.deployment_identity_ref,\n'
                '            "evidence_digest": digest,\n',
                '            "result_state": action.result_state.value,\n'
                '            "deployment_identity_ref": "",\n'
                '            "evidence_digest": digest,\n',
            ),
        ),
    ),
    Mutation(
        "M25",
        "omit approval evidence",
        CONSOLE,
        (
            (
                "                approval_refs=(approval.approval_id,),\n",
                "                approval_refs=(),\n",
            ),
        ),
    ),
    policy_flip("M26", "allow expired request", "enforce_request_expiry"),
    Mutation(
        "M27",
        "allow expired maintenance window",
        CONSOLE,
        (
            (
                "            self.state is MaintenanceWindowState.ACTIVE and "
                "self.starts_at <= moment < self.ends_at\n",
                "            self.state is MaintenanceWindowState.ACTIVE and "
                "self.starts_at <= moment\n",
            ),
        ),
    ),
    policy_flip("M28", "ignore environment mismatch", "enforce_environment_match"),
    Mutation(
        "M29",
        "ignore region/scope mismatch at commit",
        CONSOLE,
        (
            (
                "        if self.policy.enforce_exact_scope and target.scope.key != "
                "action.scope_key:\n",
                "        if False:\n",
            ),
        ),
    ),
    Mutation(
        "M30",
        "authorize by role name without exact scope",
        CONSOLE,
        (
            (
                "        if self.policy.enforce_exact_scope and "
                "projection.scope_key != scope.key:\n",
                "        if False:\n",
            ),
            (
                "                scope=scope\n"
                "                if self.policy.enforce_exact_scope\n"
                "                else self._any_scope(principal_id, capability, scope),\n",
                "                scope=self._any_scope(principal_id, capability, scope),\n",
            ),
        ),
    ),
    Mutation(
        "M31",
        "allow hierarchy-inherited admin",
        CONSOLE,
        (
            (
                "        if self.policy.enforce_exact_scope and "
                "projection.scope_key != scope.key:\n",
                "        if not scope.key.startswith(projection.scope_key.split(':')[0][:2]):\n",
            ),
            (
                "                scope=scope\n"
                "                if self.policy.enforce_exact_scope\n"
                "                else self._any_scope(principal_id, capability, scope),\n",
                "                scope=self._any_scope(principal_id, capability, scope),\n",
            ),
        ),
    ),
    Mutation(
        "M32",
        "add universal super-admin",
        CONSOLE,
        (
            (
                '        if universal or "*" in capability or "*" in projection.capability:\n',
                "        if False:\n",
            ),
        ),
    ),
    Mutation(
        "M33",
        "allow direct shell/SSH command execution surface",
        API,
        (
            (
                '    "/ops/v1/shell",\n    "/ops/v1/exec",\n',
                "",
            ),
            ('    "/ops/v1/ssh",\n', ""),
        ),
    ),
    Mutation(
        "M34",
        "allow arbitrary SQL/admin command",
        API,
        (('    "/ops/v1/sql",\n', ""),),
    ),
    Mutation(
        "M35",
        "bypass backend adapter contract",
        CONSOLE,
        (
            (
                "        ack = adapter.dispatch(request)\n",
                '        ack = DispatchAck(True, "direct:" + execution.execution_id)\n',
            ),
            (
                "    DispatchRequest,\n    OperationsAdapter,\n",
                "    DispatchAck,\n    DispatchRequest,\n    OperationsAdapter,\n",
            ),
        ),
    ),
    Mutation(
        "M36",
        "bypass audit write on failure",
        CONSOLE,
        (
            (
                "        self._record(\n"
                "            now=moment,\n"
                "            actor_ref=actor_ref,\n"
                "            authority_basis=(\n",
                "        if state in {ActionState.FAILED, ActionState.PARTIAL_FAILURE}:\n"
                "            return updated\n"
                "        self._record(\n"
                "            now=moment,\n"
                "            actor_ref=actor_ref,\n"
                "            authority_basis=(\n",
            ),
        ),
    ),
    Mutation(
        "M37",
        "bypass audit write on cancellation",
        CONSOLE,
        (
            (
                "        self._record(\n"
                "            now=moment,\n"
                "            actor_ref=actor_ref,\n"
                "            authority_basis=(\n",
                "        if state is ActionState.CANCELLED:\n"
                "            return updated\n"
                "        self._record(\n"
                "            now=moment,\n"
                "            actor_ref=actor_ref,\n"
                "            authority_basis=(\n",
            ),
        ),
    ),
    Mutation(
        "M38",
        "collapse failure into generic success",
        CONSOLE,
        (
            (
                "                BackendState.FAILED: (\n"
                "                    ActionState.FAILED,\n"
                "                    ResultState.FAILED,\n"
                "                    FailureClassification.PROVIDER_FAILURE,\n"
                "                    ExecutionState.FAILED,\n",
                "                BackendState.FAILED: (\n"
                "                    ActionState.SUCCEEDED,\n"
                "                    ResultState.SUCCEEDED,\n"
                "                    FailureClassification.NONE,\n"
                "                    ExecutionState.COMPLETED,\n",
            ),
        ),
    ),
    Mutation(
        "M39",
        "hide partial failure",
        CONSOLE,
        (
            (
                "                BackendState.PARTIAL: (\n"
                "                    ActionState.PARTIAL_FAILURE,\n"
                "                    ResultState.PARTIAL_FAILURE,\n"
                "                    FailureClassification.PARTIAL_PROVIDER_FAILURE,\n"
                "                    ExecutionState.PARTIAL,\n",
                "                BackendState.PARTIAL: (\n"
                "                    ActionState.SUCCEEDED,\n"
                "                    ResultState.SUCCEEDED,\n"
                "                    FailureClassification.NONE,\n"
                "                    ExecutionState.COMPLETED,\n",
            ),
        ),
    ),
    Mutation(
        "M40",
        "allow rollback to unverified artifact",
        CONSOLE,
        (("        if not self.ctrl03.is_verified(digest):\n", "        if False:\n"),),
    ),
    Mutation(
        "M41",
        "allow restart of wrong deployment target",
        CONSOLE,
        (
            (
                "            capability=spec.capability,\n"
                "            target_id=target.target_id,\n",
                "            capability=spec.capability,\n"
                "            target_id=next(iter(self._targets)),\n",
            ),
        ),
    ),
    Mutation(
        "M42",
        "allow restore against mismatched backup identity",
        CONSOLE,
        (
            (
                "        if latest.target_id != target.target_id or "
                "latest.backup_identity_digest != digest:\n",
                "        if False:\n",
            ),
        ),
    ),
    policy_flip(
        "M43",
        "allow destructive operation without strong confirmation",
        "enforce_destructive_confirmation",
    ),
    policy_flip("M44", "allow UI execution while read-only", "enforce_read_only_sessions"),
    Mutation(
        "M45",
        "let browser supply authoritative approval state",
        API,
        (("        self._reject_client_state(body)\n", "        pass\n"),),
    ),
    Mutation(
        "M46",
        "let browser supply authoritative execution result",
        API,
        (('        "result_state",\n        "result",\n', ""),),
    ),
    policy_flip(
        "M47", "accept unsigned/untrusted authority projection", "enforce_projection_signature"
    ),
    Mutation(
        "M48",
        "self-acceptance marker mutation",
        CONSOLE,
        (
            (
                'SELF_STATE: Final = "CANDIDATE_NOT_ACCEPTED"\n',
                'SELF_STATE: Final = "ACCEPTED"\n',
            ),
        ),
    ),
)


def apply(mutation: Mutation, package: Path) -> None:
    path = package / mutation.file
    text = path.read_text()
    for old, new in mutation.edits:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"{mutation.mutation_id}: anchor occurs {count} times in {mutation.file}: {old!r}"
            )
        text = text.replace(old, new)
    path.write_text(text)


def run_one(mutation: Mutation, python: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"ctrl04-{mutation.mutation_id}-") as td:
        work = Path(td)
        src = work / "src"
        shutil.copytree(SERVICE / "src", src, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        tests = work / "tests"
        shutil.copytree(TESTS, tests, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        apply(mutation, src / "epd2_control_plane_service")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(src)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [
                python,
                "-m",
                "pytest",
                "-q",
                "-x",
                "-p",
                "no:cacheprovider",
                "--rootdir",
                str(work),
                *sorted(str(p) for p in tests.glob("test_ctrl04_*.py")),
            ],
            cwd=work,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        detected = completed.returncode != 0
        tail = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
        return {
            "mutation_id": mutation.mutation_id,
            "family": mutation.family,
            "file": mutation.file,
            "status": "DETECTED" if detected else "UNDETECTED",
            "returncode": completed.returncode,
            "summary": tail[:200],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=str(ROOT / ".venv/bin/python"))
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    if len(MUTATIONS) != 48 or len({m.mutation_id for m in MUTATIONS}) != 48:
        raise SystemExit("mutation corpus must contain exactly 48 distinct fixtures")
    # Baseline: the unmutated suite must pass, otherwise "detection" means nothing.
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SERVICE / "src")
    baseline = subprocess.run(
        [args.python, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TESTS)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if baseline.returncode != 0:
        print(baseline.stdout[-2000:])
        raise SystemExit("baseline test suite fails; mutation results would be meaningless")
    results = []
    for mutation in MUTATIONS:
        if args.only and mutation.mutation_id not in args.only:
            continue
        result = run_one(mutation, args.python)
        results.append(result)
        print(f"{result['mutation_id']} {result['status']:<10} {result['family']}", flush=True)
    detected = [r["mutation_id"] for r in results if r["status"] == "DETECTED"]
    undetected = [r["mutation_id"] for r in results if r["status"] != "DETECTED"]
    payload = {
        "schema": "epd2.ctrl04.mutation-result/1",
        "stage": "CTRL-04",
        "required": 48,
        "executed": len(results),
        "detected": len(detected),
        "undetected": undetected,
        "baseline_summary": baseline.stdout.strip().splitlines()[-1],
        "results": results,
        "self_state": "CANDIDATE_NOT_ACCEPTED",
    }
    if args.only is None:
        VALIDATION.mkdir(parents=True, exist_ok=True)
        (VALIDATION / "mutation_result.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
    print(f"CTRL04_MUTATIONS:{len(detected)}/{len(results)}_DETECTED")
    return 0 if not undetected and len(results) == 48 else 1


if __name__ == "__main__":
    sys.exit(main())
