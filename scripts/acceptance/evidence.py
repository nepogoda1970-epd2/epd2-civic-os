"""Execution manifest emission and adversarial evidence validation.

``build_manifest``/``emit_manifest`` produce the sealed canonical execution
manifest (assignment §5). ``verify_evidence`` is the independent validator
(INFRA01-HI-04 / HI-05): it never trusts a self-declared result file, but
reconciles the manifest against the actual execution evidence — the check
registry, the captured logs, the run/commit/archive identity binding and the
recomputed test counts. The validator is part of the attack surface, so the
mutation suite drives every one of its refusal paths.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.acceptance import HARNESS_NAME, HARNESS_VERSION, codes
from scripts.acceptance.canonical import (
    load_json,
    seal_document,
    sha256_file,
    verify_sealed_document,
    write_canonical_json,
)
from scripts.acceptance.executor import CheckResult, parse_test_counts
from scripts.acceptance.identity import CandidateIdentity
from scripts.acceptance.registry import VALID_STATES, Registry

MANIFEST_NAME = "EXECUTION-MANIFEST.json"
LOG_DIR_NAME = "logs"


@dataclass(frozen=True)
class EvidenceFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def build_manifest(
    identity: CandidateIdentity,
    tools: dict[str, str],
    registry: Registry,
    results: list[CheckResult],
    finished_at: str,
    verdict: str,
    evidence_files: dict[str, str],
    freeze_tree_digest: str | None,
    final_archive_sha256: str | None,
    unresolved: list[str],
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema": "epd2.infra01.execution-manifest/1",
        "harness_name": HARNESS_NAME,
        "harness_version": HARNESS_VERSION,
        "identity": identity.as_document(),
        "tools": dict(sorted(tools.items())),
        "registry": {
            "schema": registry.schema,
            "registry_version": registry.registry_version,
            "registry_sha256": registry.registry_sha256,
            "mandatory_check_ids": sorted(registry.mandatory_check_ids()),
        },
        "results": [result.as_document() for result in results],
        "finished_at": finished_at,
        "freeze_tree_digest": freeze_tree_digest,
        "final_archive_sha256": final_archive_sha256,
        "evidence_files": dict(sorted(evidence_files.items())),
        "unresolved": sorted(unresolved),
        "verdict": verdict,
    }
    return seal_document(document)


def emit_manifest(run_dir: Path, manifest: dict[str, Any]) -> str:
    digest = write_canonical_json(run_dir / MANIFEST_NAME, manifest)
    (run_dir / "EXECUTION-MANIFEST.sha256").write_text(digest + "\n", encoding="utf-8")
    return digest


def compute_verdict(results: list[CheckResult], extra_findings: int) -> str:
    """PASS only when every mandatory result is PASS/N-A-governed and nothing
    else is outstanding. Anything unprovable is FAIL/BLOCKED, never
    'PASS WITH ENVIRONMENT LIMITATION'."""
    states = {result.state for result in results}
    if extra_findings:
        return "FAIL"
    if "FAIL" in states:
        return "FAIL"
    if "BLOCKED" in states:
        return "BLOCKED"
    if states - {"PASS", "NOT_APPLICABLE_GOVERNED"}:
        return "FAIL"
    return "PASS"


def _reparse_counts(
    log_path: Path, declared: dict[str, int], subject: str
) -> list[EvidenceFinding]:
    findings: list[EvidenceFinding] = []
    output = log_path.read_text(encoding="utf-8", errors="replace")
    for parser_type, declared_count in declared.items():
        recomputed, failed = parse_test_counts(parser_type, output)
        if failed:
            findings.append(
                EvidenceFinding(
                    codes.TEST_COUNT_MISMATCH,
                    subject,
                    f"{parser_type}: log carries a failure marker but result is declared PASS",
                )
            )
        if recomputed != declared_count:
            findings.append(
                EvidenceFinding(
                    codes.TEST_COUNT_MISMATCH,
                    subject,
                    f"{parser_type}: declared {declared_count}, log supports {recomputed}",
                )
            )
    return findings


def verify_evidence(
    run_dir: Path,
    registry: Registry,
    expected_git_commit: str | None = None,
    expected_archive_sha256: str | None = None,
) -> list[EvidenceFinding]:
    """Adversarial reconciliation of one run's persisted evidence."""
    findings: list[EvidenceFinding] = []
    manifest_path = run_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return [EvidenceFinding(codes.EVIDENCE_MISSING, MANIFEST_NAME, "manifest absent")]
    try:
        manifest = load_json(manifest_path)
    except ValueError as error:
        return [
            EvidenceFinding(codes.MANIFEST_INTEGRITY_FAILURE, MANIFEST_NAME, f"unreadable: {error}")
        ]
    if not isinstance(manifest, dict) or not verify_sealed_document(manifest):
        return [
            EvidenceFinding(
                codes.MANIFEST_INTEGRITY_FAILURE,
                MANIFEST_NAME,
                "manifest integrity digest does not match manifest content",
            )
        ]

    identity = manifest.get("identity", {})
    if expected_git_commit is not None and identity.get("git_commit") != expected_git_commit:
        findings.append(
            EvidenceFinding(
                codes.COMMIT_MISMATCH,
                "identity.git_commit",
                f"manifest bound to {identity.get('git_commit')!r}, "
                f"expected {expected_git_commit!r}",
            )
        )
    if (
        expected_archive_sha256 is not None
        and manifest.get("final_archive_sha256") != expected_archive_sha256
    ):
        findings.append(
            EvidenceFinding(
                codes.ARCHIVE_SHA_MISMATCH,
                "final_archive_sha256",
                f"manifest records {manifest.get('final_archive_sha256')!r}, "
                f"expected {expected_archive_sha256!r}",
            )
        )
    for required in ("run_id", "git_commit", "git_tree", "repository_version", "canon_version"):
        value = identity.get(required)
        if not value or value == "UNKNOWN":
            findings.append(
                EvidenceFinding(
                    codes.IDENTITY_INCOMPLETE,
                    f"identity.{required}",
                    "acceptance evidence without exact candidate identity is invalid",
                )
            )
    registry_block = manifest.get("registry", {})
    if registry_block.get("registry_sha256") != registry.registry_sha256:
        findings.append(
            EvidenceFinding(
                codes.STALE_EVIDENCE,
                "registry.registry_sha256",
                "manifest was produced against a different check registry",
            )
        )

    results = manifest.get("results", [])
    seen: dict[str, dict[str, Any]] = {}
    for raw in results:
        check_id = str(raw.get("check_id", ""))
        if check_id in seen:
            findings.append(
                EvidenceFinding(
                    codes.INTERNAL_INCONSISTENCY, check_id, "duplicate result for one check"
                )
            )
        seen[check_id] = raw
        state = raw.get("state")
        if state not in VALID_STATES:
            findings.append(
                EvidenceFinding(
                    codes.INTERNAL_INCONSISTENCY, check_id, f"unknown result state {state!r}"
                )
            )

    log_dir = run_dir / LOG_DIR_NAME
    for check in registry.all_checks():
        raw = seen.get(check.check_id)
        if raw is None:
            if check.mandatory:
                findings.append(
                    EvidenceFinding(
                        codes.MANDATORY_CHECK_MISSING,
                        check.check_id,
                        "mandatory governed check has no recorded result",
                    )
                )
            continue
        state = str(raw.get("state"))
        if state == "NOT_APPLICABLE_GOVERNED" and check.mandatory:
            findings.append(
                EvidenceFinding(
                    codes.CHECK_NOT_EXECUTED,
                    check.check_id,
                    "mandatory check declared not applicable without a governed rule",
                )
            )
        log_file = raw.get("log_file")
        log_sha = raw.get("log_sha256")
        if not log_file or not log_sha:
            findings.append(
                EvidenceFinding(
                    codes.EVIDENCE_MISSING, check.check_id, "result carries no execution evidence"
                )
            )
            continue
        log_path = log_dir / str(log_file)
        if not log_path.is_file():
            findings.append(
                EvidenceFinding(
                    codes.EVIDENCE_MISSING, check.check_id, f"evidence log absent: {log_file}"
                )
            )
            continue
        if log_path.stat().st_size == 0:
            findings.append(
                EvidenceFinding(codes.EVIDENCE_TRUNCATED, check.check_id, "evidence log is empty")
            )
            continue
        actual_sha = sha256_file(log_path)
        if actual_sha != log_sha:
            findings.append(
                EvidenceFinding(
                    codes.EVIDENCE_HASH_MISMATCH,
                    check.check_id,
                    f"log bytes {actual_sha} do not match recorded {log_sha}",
                )
            )
            continue
        if state == "PASS" and check.kind == "command":
            declared_counts = {
                str(key): int(value) for key, value in dict(raw.get("test_counts", {})).items()
            }
            expected_parsers = {parser for parser, _ in check.expects.parsers}
            if expected_parsers - set(declared_counts):
                findings.append(
                    EvidenceFinding(
                        codes.EXPECTED_OUTPUT_MISSING,
                        check.check_id,
                        "PASS without executed-test evidence for "
                        f"{sorted(expected_parsers - set(declared_counts))}",
                    )
                )
            findings.extend(_reparse_counts(log_path, declared_counts, check.check_id))
            if check.expects.sentinel is not None:
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
                if not re.search(check.expects.sentinel, log_text):
                    findings.append(
                        EvidenceFinding(
                            codes.EXPECTED_OUTPUT_MISSING,
                            check.check_id,
                            f"PASS log lacks required sentinel {check.expects.sentinel!r}",
                        )
                    )

    run_id = str(identity.get("run_id", ""))
    if run_id and run_dir.name not in (run_id, f"run-{run_id}") and run_id not in run_dir.name:
        findings.append(
            EvidenceFinding(
                codes.RUN_BINDING_MISMATCH,
                "run_id",
                f"evidence directory {run_dir.name!r} is not bound to run {run_id!r}",
            )
        )

    for name, digest in dict(manifest.get("evidence_files", {})).items():
        target = run_dir / str(name)
        if not target.is_file():
            findings.append(
                EvidenceFinding(codes.EVIDENCE_MISSING, str(name), "declared evidence file absent")
            )
        elif sha256_file(target) != str(digest):
            findings.append(
                EvidenceFinding(
                    codes.EVIDENCE_HASH_MISMATCH, str(name), "evidence file bytes changed"
                )
            )
    return findings
