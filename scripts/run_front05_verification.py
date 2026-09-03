#!/usr/bin/env python3
"""Governed FRONT-05 verification runner.

Executes the verification order the stage contract requires, persists raw output
for every authoritative step, and binds each result to the exact source tree
that produced it.

The binding is the whole point, and it is inherited from a finding rather than
invented here: FRONT-04 finding F04-C1-03 was that a recorded PASS survived a
source change, because nothing tied the evidence to the bytes it tested. Every record this runner writes carries the source, test, config,
validator and contract digests measured at execution time, plus the SHA-256 of
its own raw log. The validator recomputes all of them.

Each raw log ends with a machine-readable trailer:

    FRONT05_RAW_RESULT command=<id> exit_code=<n> finished_at=<iso>

The trailer is inside the hashed bytes, so a summary that claims PASS while its
raw log records a non-zero exit is caught by re-derivation, and editing the raw
log to agree breaks the hash.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import front05_digest as digest

SCHEMA = "epd2.front05.evidence/1"
STAGE = "FRONT-05 — WS-04 Representative Workspace"
CANDIDATE_STATE = "CANDIDATE_NOT_ACCEPTED"

RAW_TRAILER = "FRONT05_RAW_RESULT"


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def tool_versions(root: Path) -> dict[str, str]:
    def run(cmd: list[str]) -> str:
        try:
            return (
                subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=120)
                .stdout.strip()
                .splitlines()[0]
            )
        except Exception:
            return "unavailable"

    vc = root / "frontend/representative-workspace"
    playwright = "unavailable"
    with contextlib.suppress(Exception):
        playwright = subprocess.run(
            ["npx", "playwright", "--version"],
            cwd=vc,
            capture_output=True,
            text=True,
            timeout=180,
        ).stdout.strip()
    return {
        "node_version": run(["node", "--version"]),
        "npm_version": run(["npm", "--version"]),
        "python_version": sys.version.split()[0],
        "playwright_version": playwright,
    }


class Runner:
    def __init__(self, root: Path, skip: set[str]) -> None:
        self.root = root
        self.skip = skip
        self.evidence_dir = root / "validation/front05/evidence"
        self.raw_dir = root / "validation/front05/raw"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.versions = tool_versions(root)
        self.records: dict[str, dict] = {}

    def step(
        self,
        step_id: str,
        cwd: str,
        command: list[str],
        raw_name: str,
        env: dict[str, str] | None = None,
        timeout: int = 3600,
    ) -> dict:
        """Run one authoritative step and write its bound evidence record."""
        binding = digest.summary(self.root)
        started = now()
        if step_id in self.skip:
            print(f"[skip] {step_id}")
            return {}
        environment = {**os.environ, **(env or {})}
        print(f"[run ] {step_id}: {' '.join(command)}", flush=True)
        proc = subprocess.run(
            command,
            cwd=self.root / cwd,
            capture_output=True,
            text=True,
            env=environment,
            timeout=timeout,
        )
        finished = now()
        body = proc.stdout + proc.stderr
        trailer = (
            f"\n{RAW_TRAILER} command={step_id} "
            f"exit_code={proc.returncode} finished_at={finished}\n"
        )
        raw_path = self.raw_dir / raw_name
        raw_path.write_text(body + trailer, encoding="utf-8")
        raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()

        record = {
            "schema_version": SCHEMA,
            "stage": STAGE,
            "candidate_state": CANDIDATE_STATE,
            "step_id": step_id,
            "authoritative": True,
            "source_tree_digest": binding["source_tree_digest"],
            "package_lock_sha256": binding["package_lock_sha256"],
            "test_source_digest": binding["test_source_digest"],
            "configuration_digest": binding["config_digest"],
            "validator_source_digest": binding["validator_source_digest"],
            "contract_digest": binding["contract_digest"],
            "source_file_count": binding["file_count"],
            "command": " ".join(command),
            "working_directory": cwd,
            "environment_overrides": env or {},
            "started_at": started,
            "finished_at": finished,
            "exit_code": proc.returncode,
            "result": "PASS" if proc.returncode == 0 else "FAIL",
            "raw_report_path": f"validation/front05/raw/{raw_name}",
            "raw_report_sha256": raw_sha,
            **self.versions,
        }
        record.update(self.parse_counts(step_id, body))
        out = self.evidence_dir / f"{step_id}.json"
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.records[step_id] = record
        print(f"[{record['result']}] {step_id} (exit {proc.returncode})", flush=True)
        return record

    @staticmethod
    def parse_counts(step_id: str, body: str) -> dict:
        """Derive test counts from the tool's own output, not from a claim."""
        import re

        counts: dict[str, int] = {}
        if step_id == "unit":
            tap = re.search(r"^# tests (\d+)$", body, re.M)
            tap_pass = re.search(r"^# pass (\d+)$", body, re.M)
            tap_fail = re.search(r"^# fail (\d+)$", body, re.M)
            tap_skip = re.search(r"^# skipped (\d+)$", body, re.M)
            vitest = re.search(r"Tests\s+(\d+) passed", body)
            counts = {
                "tap_tests": int(tap.group(1)) if tap else 0,
                "tap_passed": int(tap_pass.group(1)) if tap_pass else 0,
                "tap_failed": int(tap_fail.group(1)) if tap_fail else 0,
                "tap_skipped": int(tap_skip.group(1)) if tap_skip else 0,
                "vitest_passed": int(vitest.group(1)) if vitest else 0,
            }
            counts["test_count"] = counts["tap_tests"] + counts["vitest_passed"]
            counts["passed"] = counts["tap_passed"] + counts["vitest_passed"]
            counts["failed"] = counts["tap_failed"]
            counts["skipped"] = counts["tap_skipped"]
        elif step_id.startswith("browser") or step_id in {
            "visual",
            "authorization_negative",
            "security_boundary",
        }:
            passed = re.search(r"(\d+) passed", body)
            failed = re.search(r"(\d+) failed", body)
            skipped = re.search(r"(\d+) skipped", body)
            did_not_run = re.search(r"(\d+) did not run", body)
            counts = {
                "passed": int(passed.group(1)) if passed else 0,
                "failed": int(failed.group(1)) if failed else 0,
                "skipped": int(skipped.group(1)) if skipped else 0,
                "did_not_run": int(did_not_run.group(1)) if did_not_run else 0,
            }
            counts["test_count"] = counts["passed"] + counts["failed"] + counts["skipped"]
        return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--skip", default="", help="comma-separated step ids to skip")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    skip = {s for s in args.skip.split(",") if s}

    # Step 1 — initial source identity, and the exclusion audit.
    initial = digest.compute(root)
    if initial["exclusion_audit_problems"]:
        print("EXCLUSION AUDIT FAILED:")
        for problem in initial["exclusion_audit_problems"]:
            print(" -", problem)
        return 2
    manifest = {
        "schema": "epd2.front05.source-manifest/1",
        "stage": STAGE,
        "candidate_state": CANDIDATE_STATE,
        "generated_at": now(),
        **{k: v for k, v in initial.items() if k != "files"},
        "files": initial["files"],
    }
    manifest_path = root / "validation/front05/source_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"[step] initial source_tree_digest = {initial['source_tree_digest']}")

    runner = Runner(root, skip)

    # Step 2/3 — locked install. npm ci fails if package-lock.json disagrees
    # with package.json, which is itself the lockfile identity check.
    if not args.skip_install:
        runner.step("install", ".", ["npm", "ci", "--no-audit", "--no-fund"], "install.log")

    vc = "frontend/representative-workspace"
    common = {"NEXT_TELEMETRY_DISABLED": "1"}

    def clear_generated_workspace_state() -> None:
        """Remove excluded build/test output before a measured step.

        Browser profiles both use Next's fixed `.next` directory. An
        interrupted web server may leave partially-written output behind; the
        next build must start from an empty excluded output directory rather
        than race or reuse it.
        """
        workspace = root / vc
        for relative in (".next", "test-results", "playwright-report"):
            shutil.rmtree(workspace / relative, ignore_errors=True)

    clear_generated_workspace_state()

    # Derived records first. They are read out of the implementation, so they
    # must be regenerated before anything validates them — otherwise a stale
    # capability table could pass a gate that the code no longer satisfies.
    runner.step(
        "derived_records",
        ".",
        [sys.executable, "scripts/build_front05_records.py", "."],
        "derived-records.log",
    )

    # Static quality.
    runner.step(
        "format",
        ".",
        ["npm", "run", "--workspace", "representative-workspace", "format:check"],
        "format.log",
    )
    runner.step("lint", vc, ["npm", "run", "lint"], "lint.log")
    runner.step("typecheck", vc, ["npm", "run", "typecheck"], "typecheck.log")

    # Unit and component suites, recorded separately: they exercise different
    # layers and a reviewer should be able to see either one fail on its own.
    runner.step(
        "unit",
        vc,
        ["node", "--import", "tsx", "--test", "tests/front05.design.test.ts",
         "tests/front05.boundaries.test.ts", "tests/front05.isolation.test.ts",
         "tests/front05.scope.test.ts", "tests/front05.runtime.test.ts",
         "tests/front05.workflow.test.ts", "tests/front05.language.test.ts"],
        "unit-tests.log",
    )
    runner.step("component", vc, ["npx", "vitest", "run"], "component-tests.log")

    # Both build profiles. The production build is the one that ships; the
    # governed-test build is the one the journey suite walks. Recording only the
    # second would leave the shipped artifact unmeasured.
    runner.step(
        "build",
        vc,
        ["npm", "run", "build"],
        "build.log",
        env={**common, "NEXT_PUBLIC_FRONT05_GOVERNED_TEST": "1"},
    )
    runner.step(
        "build_production_profile",
        vc,
        ["npm", "run", "build"],
        "build-production.log",
        env={**common, "NEXT_PUBLIC_FRONT05_GOVERNED_TEST": "0"},
    )

    # Fixture absence, measured against the production build that was just made.
    runner.step(
        "fixture_absence",
        ".",
        [sys.executable, "scripts/check_front05_fixture_absence.py", "."],
        "fixture-absence.log",
    )

    # Browser suites, both profiles.
    clear_generated_workspace_state()
    runner.step(
        "browser",
        vc,
        ["npx", "playwright", "test", "--grep-invert", "@visual", "--reporter=line"],
        "browser.log",
        env=common,
    )
    clear_generated_workspace_state()
    runner.step(
        "browser_production",
        vc,
        ["npx", "playwright", "test", "--grep-invert", "@visual", "--reporter=line"],
        "browser-production.log",
        env={**common, "FRONT05_TEST_PROFILE": "production"},
    )
    clear_generated_workspace_state()

    # The authorization negatives are called out separately because they are the
    # suite a reviewer is most likely to want to read on its own.
    runner.step(
        "authorization_negative",
        vc,
        [
            "npx", "playwright", "test",
            "--grep", "production profile|negative case outcome|names no resource|no universal|no unscoped search|storage boundary|consequential actions|origin boundary",
            "--reporter=line",
        ],
        "authorization-negative.log",
        env={**common, "FRONT05_TEST_PROFILE": "production"},
    )
    clear_generated_workspace_state()

    runner.step(
        "visual",
        vc,
        ["npx", "playwright", "test", "--grep", "@visual", "--reporter=line"],
        "visual.log",
        env=common,
    )

    # Dependency posture. Recorded as evidence and dispositioned by the
    # validator against reachability, not waved through as "non-blocking".
    runner.step(
        "dependency_audit",
        ".",
        ["npm", "audit", "--json"],
        "dependency-audit.log",
    )

    # Derived records that read the raw logs, so they run after the suites they
    # describe. Building them earlier would let a stale catalogue claim outcomes
    # from a previous run.
    runner.step(
        "authorization_negatives_record",
        ".",
        [sys.executable, "scripts/build_front05_authorization_negatives.py", "."],
        "authorization-negatives-record.log",
    )
    runner.step(
        "dependency_findings_record",
        ".",
        [sys.executable, "scripts/build_front05_dependency_findings.py", "."],
        "dependency-findings-record.log",
    )
    runner.step(
        "identity_records",
        ".",
        [sys.executable, "scripts/build_front05_identity.py", "."],
        "identity-records.log",
    )

    # Step 11/12 — prove verification did not mutate governed source bytes.
    after = digest.compute(root)
    mutated = sorted(
        path
        for path in set(initial["files"]) | set(after["files"])
        if initial["files"].get(path) != after["files"].get(path)
    )
    integrity = {
        "schema": "epd2.front05.verification-integrity/1",
        "stage": STAGE,
        "candidate_state": CANDIDATE_STATE,
        "source_tree_digest_before": initial["source_tree_digest"],
        "source_tree_digest_after": after["source_tree_digest"],
        "source_unchanged_by_verification": initial["source_tree_digest"]
        == after["source_tree_digest"],
        "files_changed_during_verification": mutated,
        "generated_at": now(),
    }
    (root / "validation/front05/verification_integrity.json").write_text(
        json.dumps(integrity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"[step] source unchanged by verification: {integrity['source_unchanged_by_verification']}"
    )
    if mutated:
        print("       changed:", mutated)

    # `npm audit` exits non-zero whenever any advisory exists, which is a
    # finding to disposition rather than a failed verification step. The
    # validator reads the recorded JSON and decides; the runner only records.
    ADVISORY_STEPS = {"dependency_audit"}
    failed = [
        k
        for k, v in runner.records.items()
        if v.get("result") != "PASS" and k not in ADVISORY_STEPS
    ]
    print("\nSteps:", ", ".join(f"{k}={v['result']}" for k, v in runner.records.items()))
    if failed:
        print("FAILED STEPS:", failed)
    return 1 if failed or not integrity["source_unchanged_by_verification"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
