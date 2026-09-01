"""Canonical acceptance entry point (assignment §4).

There is exactly one canonical acceptance command::

    uv run python -m scripts.acceptance run

It executes the governed stage sequence — bootstrap, verify-governance,
verify-repository, verify-dependencies, verify-backend, verify-frontend,
verify-build, verify-browser, verify-accessibility, verify-visual,
verify-secrets, verify-frozen-artifacts, verify-boundaries, verify-evidence,
freeze, package, verify-package, emit-manifest — and emits the sealed
execution manifest plus the evidence bundle. GitHub Actions invokes this same
command; there is no second implementation of acceptance logic.

Exit code 0 is issued only for a complete fail-closed ``PASS``. A PASS from
this harness is still only a local/canonical execution result: it is not
external governed acceptance, not production readiness and not legal
activation.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

from scripts.acceptance import HARNESS_NAME, HARNESS_VERSION, codes
from scripts.acceptance import boundaries as boundaries_mod
from scripts.acceptance import frozen as frozen_mod
from scripts.acceptance.canonical import (
    load_json,
    sha256_file,
    write_canonical_json,
)
from scripts.acceptance.deployment_manifest import validate_manifest
from scripts.acceptance.evidence import (
    LOG_DIR_NAME,
    build_manifest,
    compute_verdict,
    emit_manifest,
    verify_evidence,
)
from scripts.acceptance.executor import CheckResult, internal_result, run_command_check
from scripts.acceptance.freeze import (
    FreezeInventory,
    freeze_problems,
    take_inventory,
    tracked_files,
)
from scripts.acceptance.governance import verify_governance
from scripts.acceptance.hygiene import scan_archive as hygiene_scan_archive
from scripts.acceptance.identity import (
    CandidateIdentity,
    collect_identity,
    lock_mismatches,
    tool_inventory,
    utc_now,
)
from scripts.acceptance.package import build_archive, verify_archive_against_inventory
from scripts.acceptance.readiness import evaluate as evaluate_readiness
from scripts.acceptance.registry import Registry, load_registry
from scripts.acceptance.secrets_scan import (
    sanitize_evidence,
    scan_files,
)
from scripts.acceptance.secrets_scan import (
    scan_archive as secrets_scan_archive,
)

CANDIDATE_NAME = "EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1"
DISCLAIMER = (
    "LOCAL CANONICAL HARNESS RESULT ONLY. EXTERNAL GOVERNED ACCEPTANCE: NOT PERFORMED. "
    "NOT PRODUCTION READY. NOT LEGALLY ACTIVATED."
)


class _Pipeline:
    """One acceptance run over the repository at ``root``."""

    def __init__(self, root: Path, output_root: Path | None) -> None:
        self.root = root
        self.registry: Registry = load_registry()
        self.identity: CandidateIdentity = collect_identity(root, dict(os.environ))
        base = output_root or (root / ".acceptance-run")
        self.run_dir = base / f"run-{self.identity.run_id}"
        self.log_dir = self.run_dir / LOG_DIR_NAME
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.tools: dict[str, str] = {}
        self.results: list[CheckResult] = []
        self.pipeline_findings: list[str] = []
        self.frozen_pins = frozen_mod.load_pins()
        self.inventory: FreezeInventory | None = None
        self.archive_path: Path | None = None
        self.archive_sha256: str | None = None
        self.environ = dict(os.environ)
        self.environ.setdefault("NO_COLOR", "1")
        self.environ.setdefault("FORCE_COLOR", "0")
        self.environ.setdefault("CI", "1")

    # -- internal checks -------------------------------------------------

    def _internal(self, check_id: str) -> list[str]:
        handler = {
            "bootstrap.identity": self._check_identity,
            "bootstrap.tools": self._check_tools,
            "bootstrap.registry-integrity": self._check_registry_integrity,
            "bootstrap.frozen-pre-test": self._check_frozen_tree,
            "governance.canonical-registers": self._check_governance,
            "dependencies.locks-unchanged": self._check_locks_unchanged,
            "secrets.tree-scan": self._check_secrets_tree,
            "frozen.post-test": self._check_frozen_tree,
            "boundaries.non-ownership": self._check_boundaries,
            "evidence.reconciliation": self._check_evidence_midrun,
            "freeze.preconditions": self._check_freeze_preconditions,
            "freeze.inventory": self._check_freeze_inventory,
            "freeze.frozen-pre-package": self._check_frozen_tree,
            "package.build": self._check_package_build,
            "verify-package.byte-identity": self._check_package_byte_identity,
            "verify-package.hygiene": self._check_package_hygiene,
            "verify-package.frozen-in-archive": self._check_frozen_in_archive,
            "verify-package.secret-scan": self._check_archive_secrets,
            "verify-package.evidence-sanitation": self._check_evidence_sanitation,
            "manifest.emit": self._check_manifest_placeholder,
        }[check_id]
        return handler()

    def _check_identity(self) -> list[str]:
        findings = [f"{codes.IDENTITY_INCOMPLETE}: {p}" for p in self.identity.problems]
        if self.identity.git_dirty:
            findings.append(
                f"{codes.DIRTY_TREE}: working tree diverges from commit "
                f"{self.identity.git_commit}: {sorted(self.identity.dirty_paths)[:10]}"
            )
        return findings

    def _check_tools(self) -> list[str]:
        self.tools = tool_inventory(self.root)
        return [
            f"{codes.CHECK_NOT_EXECUTED}: required tool unavailable: {name}"
            for name, version in sorted(self.tools.items())
            if version == "UNAVAILABLE"
        ]

    def _check_registry_integrity(self) -> list[str]:
        return [f"{codes.REGISTRY_INTEGRITY_FAILURE}: {p}" for p in self.registry.problems]

    def _check_frozen_tree(self) -> list[str]:
        return [
            f"{f.code}: {f.path}: {f.detail}"
            for f in frozen_mod.verify_tree(self.root, self.frozen_pins)
        ]

    def _check_governance(self) -> list[str]:
        tracked = tracked_files(self.root)
        return [f"{f.code}: {f.path}: {f.detail}" for f in verify_governance(self.root, tracked)]

    def _check_locks_unchanged(self) -> list[str]:
        return lock_mismatches(self.root, self.identity.lock_hashes)

    def _check_secrets_tree(self) -> list[str]:
        hits = scan_files(self.root, tracked_files(self.root))
        return [hit.describe() for hit in hits]

    def _check_boundaries(self) -> list[str]:
        return [
            f"{f.code}: {f.path}: {f.detail}" for f in boundaries_mod.check_boundaries(self.root)
        ]

    def _check_evidence_midrun(self) -> list[str]:
        """Reconcile the evidence produced so far against the registry."""
        findings: list[str] = []
        executed = {result.check_id: result for result in self.results}
        for check in self.registry.all_checks():
            if check.stage_id in (
                "verify-evidence",
                "freeze",
                "package",
                "verify-package",
                "emit-manifest",
            ):
                continue
            result = executed.get(check.check_id)
            if result is None:
                if check.mandatory:
                    findings.append(
                        f"{codes.MANDATORY_CHECK_MISSING}: {check.check_id}: "
                        "mandatory check produced no result before evidence reconciliation"
                    )
                continue
            if result.log_file is None or not (self.log_dir / result.log_file).is_file():
                findings.append(
                    f"{codes.EVIDENCE_MISSING}: {check.check_id}: no captured execution log"
                )
        return findings

    def _check_freeze_preconditions(self) -> list[str]:
        return [f"{f.code}: {f.path}: {f.detail}" for f in freeze_problems(self.root)]

    def _check_freeze_inventory(self) -> list[str]:
        self.inventory = take_inventory(self.root)
        write_canonical_json(self.run_dir / "FREEZE-INVENTORY.json", self.inventory.as_document())
        return []

    def _sha256sums_bytes(self, inventory: FreezeInventory) -> bytes:
        lines = [f"{digest}  {path}" for path, digest in sorted(inventory.files.items())]
        inventory_doc = (self.run_dir / "FREEZE-INVENTORY.json").read_bytes()
        lines.append(
            f"{hashlib.sha256(inventory_doc).hexdigest()}  ACCEPTANCE/FREEZE-INVENTORY.json"
        )
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _check_package_build(self) -> list[str]:
        if self.inventory is None:
            return [f"{codes.CHECK_NOT_EXECUTED}: package.build: no freeze inventory available"]
        additions = {
            "ACCEPTANCE/FREEZE-INVENTORY.json": (
                self.run_dir / "FREEZE-INVENTORY.json"
            ).read_bytes(),
            "SHA256SUMS.txt": self._sha256sums_bytes(self.inventory),
        }
        archive = self.run_dir / f"{CANDIDATE_NAME}.zip"
        result = build_archive(self.root, self.inventory, archive, CANDIDATE_NAME, additions)
        if result.findings:
            return [f"{f.code}: {f.path}: {f.detail}" for f in result.findings]
        self.archive_path = result.archive
        self.archive_sha256 = result.archive_sha256
        return []

    def _check_package_byte_identity(self) -> list[str]:
        if self.archive_path is None or self.inventory is None:
            return [f"{codes.CHECK_NOT_EXECUTED}: verify-package: no archive produced"]
        findings = verify_archive_against_inventory(
            self.archive_path, CANDIDATE_NAME, self.inventory
        )
        return [f"{f.code}: {f.path}: {f.detail}" for f in findings]

    def _check_package_hygiene(self) -> list[str]:
        if self.archive_path is None:
            return [f"{codes.CHECK_NOT_EXECUTED}: verify-package: no archive produced"]
        return [f"{f.code}: {f.path}: {f.detail}" for f in hygiene_scan_archive(self.archive_path)]

    def _check_frozen_in_archive(self) -> list[str]:
        if self.archive_path is None:
            return [f"{codes.CHECK_NOT_EXECUTED}: verify-package: no archive produced"]
        return [
            f"{f.code}: {f.path}: {f.detail}"
            for f in frozen_mod.verify_archive(self.archive_path, CANDIDATE_NAME, self.frozen_pins)
        ]

    def _check_archive_secrets(self) -> list[str]:
        if self.archive_path is None:
            return [f"{codes.CHECK_NOT_EXECUTED}: verify-package: no archive produced"]
        return [hit.describe() for hit in secrets_scan_archive(self.archive_path)]

    def _check_evidence_sanitation(self) -> list[str]:
        return [hit.describe() for hit in sanitize_evidence(self.log_dir)]

    def _check_manifest_placeholder(self) -> list[str]:
        return []

    # -- execution -------------------------------------------------------

    def run(self) -> int:
        for stage in self.registry.stages:
            for check in stage.checks:
                if check.kind == "command":
                    result = run_command_check(check, self.root, self.log_dir, self.environ)
                else:
                    try:
                        findings = self._internal(check.check_id)
                    except Exception as error:
                        findings = [
                            f"{codes.INTERNAL_INCONSISTENCY}: {check.check_id}: "
                            f"internal check raised {error!r}"
                        ]
                    result = internal_result(check, findings, self.log_dir)
                self.results.append(result)
                print(f"[{result.state:>7}] {check.check_id}", flush=True)

        finished_at = utc_now()
        evidence_files = (
            {"FREEZE-INVENTORY.json": sha256_file(self.run_dir / "FREEZE-INVENTORY.json")}
            if (self.run_dir / "FREEZE-INVENTORY.json").is_file()
            else {}
        )
        verdict = compute_verdict(self.results, len(self.pipeline_findings))
        manifest = build_manifest(
            identity=self.identity,
            tools=self.tools,
            registry=self.registry,
            results=self.results,
            finished_at=finished_at,
            verdict=verdict,
            evidence_files=evidence_files,
            freeze_tree_digest=self.inventory.tree_digest if self.inventory else None,
            final_archive_sha256=self.archive_sha256,
            unresolved=self.pipeline_findings,
        )
        emit_manifest(self.run_dir, manifest)

        post_findings = verify_evidence(
            self.run_dir,
            self.registry,
            expected_git_commit=self.identity.git_commit,
            expected_archive_sha256=self.archive_sha256,
        )
        if post_findings:
            verdict = "FAIL"
            for finding in post_findings:
                print(f"POST-EMIT EVIDENCE FINDING: {finding.describe()}", flush=True)

        print()
        print(f"{HARNESS_NAME} {HARNESS_VERSION}")
        print(f"run: {self.run_dir}")
        print(f"commit: {self.identity.git_commit}")
        print(f"tree digest: {self.inventory.tree_digest if self.inventory else 'NOT_FROZEN'}")
        print(f"candidate archive: {self.archive_path or 'NOT_PACKAGED'}")
        print(f"candidate sha256: {self.archive_sha256 or 'NOT_PACKAGED'}")
        print(f"INFRA01_ACCEPTANCE_RESULT:{verdict}:{self.run_dir}")
        print(DISCLAIMER)
        return 0 if verdict == "PASS" else 1


def _cmd_run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    output = Path(args.output).resolve() if args.output else None
    return _Pipeline(root, output).run()


def _cmd_verify_evidence(args: argparse.Namespace) -> int:
    findings = verify_evidence(
        Path(args.run_dir).resolve(),
        load_registry(),
        expected_git_commit=args.expect_commit,
        expected_archive_sha256=args.expect_archive_sha256,
    )
    for finding in findings:
        print(finding.describe())
    print(f"INFRA01_EVIDENCE_RESULT:{'PASS' if not findings else 'FAIL'}")
    return 0 if not findings else 1


def _cmd_validate_deployment_manifest(args: argparse.Namespace) -> int:
    document = load_json(Path(args.manifest))
    findings = validate_manifest(document)
    for finding in findings:
        print(f"{finding.code}: {finding.detail}")
    print(f"INFRA01_DEPLOYMENT_MANIFEST_RESULT:{'PASS' if not findings else 'FAIL'}")
    return 0 if not findings else 1


def _cmd_evaluate_readiness(args: argparse.Namespace) -> int:
    document = load_json(Path(args.contract))
    verdict = evaluate_readiness(document)
    for finding in verdict.findings:
        print(f"{finding.code}: {finding.dimension}: {finding.detail}")
    print(f"INFRA01_READINESS_RESULT:{verdict.overall}")
    return 0 if verdict.overall == "READY" else 1


def _cmd_registry(_args: argparse.Namespace) -> int:
    registry = load_registry()
    for stage in registry.stages:
        print(f"{stage.stage_id} ({'mandatory' if stage.mandatory else 'optional'})")
        for check in stage.checks:
            flag = "mandatory" if check.mandatory else "optional"
            print(f"  {check.check_id} [{check.kind}, {flag}] {check.title}")
    print(f"registry {registry.registry_version} sha256 {registry.registry_sha256}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.acceptance", description="EPD2 INFRA-01 canonical acceptance harness"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="execute the complete canonical acceptance pipeline")
    run_parser.add_argument("--root", default=".", help="repository root")
    run_parser.add_argument("--output", default=None, help="evidence output root")
    run_parser.set_defaults(func=_cmd_run)

    verify_parser = sub.add_parser(
        "verify-evidence", help="adversarially validate a run's evidence"
    )
    verify_parser.add_argument("--run-dir", required=True)
    verify_parser.add_argument("--expect-commit", default=None)
    verify_parser.add_argument("--expect-archive-sha256", default=None)
    verify_parser.set_defaults(func=_cmd_verify_evidence)

    manifest_parser = sub.add_parser(
        "validate-deployment-manifest", help="validate a deployment manifest (FIR-REL-001)"
    )
    manifest_parser.add_argument("manifest")
    manifest_parser.set_defaults(func=_cmd_validate_deployment_manifest)

    readiness_parser = sub.add_parser(
        "evaluate-readiness", help="evaluate a runtime readiness contract (FIR-READY-001)"
    )
    readiness_parser.add_argument("contract")
    readiness_parser.set_defaults(func=_cmd_evaluate_readiness)

    registry_parser = sub.add_parser("registry", help="print the governed check registry")
    registry_parser.set_defaults(func=_cmd_registry)

    args = parser.parse_args(argv)
    handler: Any = args.func
    return int(handler(args))


if __name__ == "__main__":
    sys.exit(main())
