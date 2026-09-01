"""Check execution with fail-closed result semantics (INFRA01-HI-03 / HI-04).

Every command check runs as a subprocess with its complete output captured to
an evidence log. The recorded state distinguishes::

    test executed and passed   != test did not execute != evidence says PASS

- a missing tool or un-runnable command is ``BLOCKED``, never a skip;
- a non-zero exit is ``FAIL``;
- a zero exit without the required sentinel is ``FAIL``
  (:data:`codes.EXPECTED_OUTPUT_MISSING`) — exit code 0 with missing
  expected output is treated as a suppressed or degraded execution;
- a zero exit whose output shows zero executed tests where tests are
  expected is ``FAIL`` (:data:`codes.ZERO_TESTS_EXECUTED`) — a test
  collection matching nothing must never count as green;
- any reported test failures make the check ``FAIL`` even on exit code 0.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.acceptance import codes
from scripts.acceptance.canonical import sha256_file
from scripts.acceptance.identity import utc_now
from scripts.acceptance.registry import Check

_PARSER_PATTERNS: dict[str, tuple[re.Pattern[str], re.Pattern[str] | None]] = {
    # (passed-count pattern, failure pattern)
    "pytest": (
        re.compile(r"(\d+) passed"),
        re.compile(r"(\d+) (?:failed|error)|no tests ran"),
    ),
    "vitest": (
        re.compile(r"Tests\s+(\d+) passed"),
        re.compile(r"Tests\s+\d+ failed|No test files found"),
    ),
    "nodetest": (
        re.compile(r"# pass (\d+)"),
        re.compile(r"# fail [1-9]\d*"),
    ),
    "playwright": (
        re.compile(r"(\d+) passed"),
        re.compile(r"[1-9]\d* (?:failed|flaky)|no tests found", re.IGNORECASE),
    ),
}


@dataclass
class CheckResult:
    check_id: str
    stage_id: str
    state: str
    detector_codes: list[str] = field(default_factory=list)
    exit_code: int | None = None
    started_at: str = ""
    finished_at: str = ""
    log_file: str | None = None
    log_sha256: str | None = None
    test_counts: dict[str, int] = field(default_factory=dict)
    detail: str = ""

    def as_document(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "stage_id": self.stage_id,
            "state": self.state,
            "detector_codes": sorted(self.detector_codes),
            "exit_code": self.exit_code,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "log_file": self.log_file,
            "log_sha256": self.log_sha256,
            "test_counts": dict(sorted(self.test_counts.items())),
            "detail": self.detail,
        }


_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(output: str) -> str:
    """Terminal color/control sequences must never hide or fake a count."""
    return _ANSI_ESCAPE.sub("", output)


def parse_test_counts(parser_type: str, output: str) -> tuple[int | None, bool]:
    """Return (passed count or None, failure marker seen)."""
    output = strip_ansi(output)
    passed_pattern, failure_pattern = _PARSER_PATTERNS[parser_type]
    matches = passed_pattern.findall(output)
    passed = sum(int(value) for value in matches) if matches else None
    failed = bool(failure_pattern.search(output)) if failure_pattern else False
    return passed, failed


def evaluate_output(check: Check, exit_code: int, output: str) -> CheckResult:
    """Apply the fail-closed expectation rules to a completed command."""
    result = CheckResult(check_id=check.check_id, stage_id=check.stage_id, state="PASS")
    result.exit_code = exit_code

    if exit_code != 0:
        result.state = "FAIL"
        result.detail = f"exit code {exit_code}"
        return result

    output = strip_ansi(output)
    if check.expects.sentinel is not None and not re.search(check.expects.sentinel, output):
        result.state = "FAIL"
        result.detector_codes.append(codes.EXPECTED_OUTPUT_MISSING)
        result.detail = (
            f"exit code 0 but required output sentinel {check.expects.sentinel!r} is absent"
        )
        return result

    for parser_type, minimum in check.expects.parsers:
        passed, failed = parse_test_counts(parser_type, output)
        if failed:
            result.state = "FAIL"
            result.detail = f"{parser_type}: failure marker present in output"
            return result
        if passed is None:
            result.state = "FAIL"
            result.detector_codes.append(codes.EXPECTED_OUTPUT_MISSING)
            result.detail = f"{parser_type}: no executed-test evidence in output"
            return result
        if passed < minimum:
            result.state = "FAIL"
            result.detector_codes.append(codes.ZERO_TESTS_EXECUTED)
            result.detail = f"{parser_type}: {passed} tests executed, minimum {minimum} expected"
            return result
        result.test_counts[parser_type] = passed
    return result


def run_command_check(
    check: Check, root: Path, log_dir: Path, environ: dict[str, str]
) -> CheckResult:
    """Execute one command check, capturing complete evidence."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{check.check_id.replace('/', '_')}.log"
    started = utc_now()
    try:
        completed = subprocess.run(
            list(check.command),
            cwd=root,
            capture_output=True,
            text=True,
            timeout=check.timeout_seconds,
            check=False,
            env=environ,
        )
        output = completed.stdout + ("\n" + completed.stderr if completed.stderr else "")
        result = evaluate_output(check, completed.returncode, output)
    except FileNotFoundError as error:
        output = f"BLOCKED: command not executable: {error}\n"
        result = CheckResult(
            check_id=check.check_id,
            stage_id=check.stage_id,
            state="BLOCKED",
            detail=f"tool unavailable: {error}",
            detector_codes=[codes.CHECK_NOT_EXECUTED],
        )
    except subprocess.TimeoutExpired as error:
        output = f"FAIL: timeout after {check.timeout_seconds}s: {error}\n"
        result = CheckResult(
            check_id=check.check_id,
            stage_id=check.stage_id,
            state="FAIL",
            detail=f"timeout after {check.timeout_seconds}s",
        )
    result.started_at = started
    result.finished_at = utc_now()
    log_path.write_text(
        f"# check: {check.check_id}\n# command: {' '.join(check.command)}\n"
        f"# started: {result.started_at}\n# finished: {result.finished_at}\n"
        f"# exit_code: {result.exit_code}\n\n{output}",
        encoding="utf-8",
    )
    result.log_file = log_path.name
    result.log_sha256 = sha256_file(log_path)
    return result


def internal_result(
    check: Check,
    findings: list[str],
    log_dir: Path,
    detail_lines: list[str] | None = None,
) -> CheckResult:
    """Record the result of an internal (in-process) check with evidence."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{check.check_id.replace('/', '_')}.log"
    started = utc_now()
    state = "PASS" if not findings else "FAIL"
    detector: list[str] = sorted({finding.split(":", 1)[0] for finding in findings})
    body_lines = [f"# check: {check.check_id}", f"# started: {started}", f"# state: {state}", ""]
    body_lines.extend(detail_lines or [])
    body_lines.extend(findings)
    result = CheckResult(
        check_id=check.check_id,
        stage_id=check.stage_id,
        state=state,
        detector_codes=detector,
        started_at=started,
        finished_at=utc_now(),
        detail=f"{len(findings)} finding(s)" if findings else "",
    )
    body_lines.append(f"# finished: {result.finished_at}")
    log_path.write_text("\n".join(body_lines) + "\n", encoding="utf-8")
    result.log_file = log_path.name
    result.log_sha256 = sha256_file(log_path)
    return result
