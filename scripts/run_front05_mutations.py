#!/usr/bin/env python3
"""FRONT-05 mutation resistance harness.

Each mutation applies one hostile edit set to a copy of the package and runs the
governed validator against it. A mutation is DETECTED when it makes a gate fail
that was **not already failing** on the unmutated tree — so the harness names
the gate that caught it rather than merely observing a non-zero exit. That
distinction matters: a suite that accepted any non-zero exit would score a point
for a mutation that broke the validator itself.

Four families:

* `M-F05-P01…P16` attack the four hard prohibitions — universal admin mode,
  cross-mandate access, publication approval, registry custody, eligibility
  decisions, voting-domain access.
* `M-F05-C01…C12` attack confidentiality and the client-authority boundary —
  storage, telemetry, URLs, titles, disclosure through refusals, client-side
  decisions.
* `M-F05-E01…E10` attack the **evidence chain** — stale digests, transplanted
  records, edited raw logs, rehashed logs, competing results.
* `M-F05-S01…S06` attack the **security-sensitive dependency discipline** and
  the report identity cross-check — the two gates added beyond the assignment
  seed, each because a real failure showed the seed set had a hole. A suite that
  did not attack its own additions would be assuming exactly what it added them
  to check.

A mutation that survives is a hole in the gates, not a curiosity, so the harness
exits non-zero if any one of them is undetected. The rule when one survives is
to close the gate, never to soften the mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import front05_digest as digest

parser = argparse.ArgumentParser()
parser.add_argument("--root", default=".")
parser.add_argument("--output", required=True)
parser.add_argument("--only", default="", help="comma-separated mutation id prefixes")
args = parser.parse_args()

root = Path(args.root).resolve()
WS = "frontend/representative-workspace"
REPORT = "FRONT05_C1_DEVELOPER_REPORT.md"

IGNORE = shutil.ignore_patterns(
    "node_modules", ".next", ".git", "test-results", "playwright-report",
    "__pycache__", "*.pyc", "coverage", ".venv", ".ruff_cache",
)

Edit = tuple[str, Callable[[str], str]]


def sub(pattern: str, replacement: str, count: int = 1) -> Callable[[str], str]:
    return lambda s: re.sub(pattern, replacement, s, count=count)


def replace(needle: str, replacement: str) -> Callable[[str], str]:
    return lambda s: s.replace(needle, replacement, 1)


def append(extra: str) -> Callable[[str], str]:
    return lambda s: s + extra


def json_edit(mutate: Callable[[dict], dict]) -> Callable[[str], str]:
    def apply(body: str) -> str:
        return json.dumps(mutate(json.loads(body)), indent=1, ensure_ascii=False) + "\n"

    return apply


# ---------------------------------------------------------------- prohibitions
PROHIBITION_MUTATIONS: list[tuple[str, list[Edit]]] = [
    (
        "M-F05-P01 universal-admin-role-added",
        [(f"{WS}/policies/authority.ts",
          replace('export const WS04_ROLES = Object.freeze([',
                  'export const WS04_ROLES = Object.freeze([\n  "super_admin",'))],
    ),
    (
        "M-F05-P02 cross-mandate-access-granted",
        [(f"{WS}/policies/authority.ts",
          sub(r"export function crossMandateAccessAvailableFor\(role: string\): false \{\n  void role;\n  return false;",
              "export function crossMandateAccessAvailableFor(role: string): boolean {\n  return role === \"representative\";"))],
    ),
    (
        "M-F05-P03 scope-binding-accepts-any-mandate",
        [(f"{WS}/domain/scope.ts",
          replace("  if (requestedMandateId !== null && requestedMandateId !== scope.mandateId) {",
                  "  if (false) {"))],
    ),
    (
        "M-F05-P04 multiple-mandates-resolved",
        [(f"{WS}/domain/scope.ts",
          replace('return session.scope === null ? [] : [session.scope.mandateId];',
                  'return session.scope === null ? [] : [session.scope.mandateId, "MANDAT-B"];'))],
    ),
    (
        "M-F05-P05 publication-approval-reachable",
        [(f"{WS}/domain/publication.ts",
          replace('  proposal_submitted: { withdraw: "draft" },',
                  '  proposal_submitted: { withdraw: "draft", compose: "approved_by_publication_authority" },'))],
    ),
    (
        "M-F05-P06 ws04-may-approve-publication",
        [(f"{WS}/policies/boundaries.ts",
          sub(r"export function ws04MayApprovePublication\(\): false \{\n  return false;",
              "export function ws04MayApprovePublication(): boolean {\n  return true;"))],
    ),
    (
        "M-F05-P07 approve-action-offered",
        [(f"{WS}/domain/publication.ts",
          replace('export const PUBLICATION_ACTIONS: readonly ActionDescriptor[] = Object.freeze([',
                  'export const PUBLICATION_ACTIONS: readonly ActionDescriptor[] = Object.freeze([\n  {\n    actionId: "publication.approve",\n    label: "Freigeben",\n    required: "mandate_representative",\n    impact: "consequential",\n    capability: "publication_proposal_submission",\n  },'))],
    ),
    (
        "M-F05-P08 approval-port-method-added",
        [(f"{WS}/runtime/ports.ts",
          replace("export type PublicationPort = {",
                  "export type PublicationPort = {\n  readonly approve: (proposalId: string) => Promise<Result<never>>;"))],
    ),
    (
        "M-F05-P09 registry-mutation-permitted",
        [(f"{WS}/policies/boundaries.ts",
          sub(r"export function mayMutateRegistry\(registry: string, action: string\): false \{",
              "export function mayMutateRegistry(registry: string, action: string): boolean {\n  if (action === \"read\") return true;"))],
    ),
    (
        "M-F05-P10 registry-write-shape-added",
        [(f"{WS}/runtime/ports.ts",
          replace("export type RegistryReferencePort = {",
                  "export type RegistryReferencePort = {\n  readonly write: (key: string, value: string) => Promise<Result<never>>;"))],
    ),
    (
        "M-F05-P11 eligibility-decided-here",
        [(f"{WS}/policies/boundaries.ts",
          sub(r"export function mayDecideEligibility\(kind: string\): false \{",
              "export function mayDecideEligibility(kind: string): boolean {\n  if (kind === \"voter_eligibility\") return true;"))],
    ),
    (
        "M-F05-P12 eligibility-decision-shape-added",
        [(f"{WS}/runtime/ports.ts",
          replace("export type EligibilityDisplayPort = {",
                  "export type EligibilityDisplayPort = {\n  readonly decide: (subjectRef: string) => Promise<Result<never>>;"))],
    ),
    (
        "M-F05-P13 voting-domain-access-granted",
        [(f"{WS}/policies/boundaries.ts",
          sub(r"export function votingDomainAccessAvailableFor\(role: string\): false \{",
              "export function votingDomainAccessAvailableFor(role: string): boolean {\n  if (role === \"representative\") return true;"))],
    ),
    (
        "M-F05-P14 voting-identifier-introduced",
        [(f"{WS}/domain/types.ts",
          replace("export type CaseSummary = {",
                  "export type CaseSummary = {\n  readonly ballotId: string;\n  readonly confirmationCode: string;"))],
    ),
    (
        "M-F05-P15 self-clearing-own-conflict",
        [(f"{WS}/policies/authority.ts",
          sub(r"export function maySelfClearConflict\(role: Ws04Role\): false \{\n  void role;\n  return false;",
              "export function maySelfClearConflict(role: Ws04Role): boolean {\n  return role === \"representative\";"))],
    ),
    (
        "M-F05-P16 unknown-restriction-treated-as-cleared",
        [(f"{WS}/domain/conflict.ts",
          replace("  if (!knowledge.known) return true;\n  return knowledge.restrictions.some(",
                  "  if (!knowledge.known) return false;\n  return knowledge.restrictions.some("))],
    ),
]

# ------------------------------------------------- confidentiality and authority
CONFIDENTIALITY_MUTATIONS: list[tuple[str, list[Edit]]] = [
    (
        "M-F05-C01 case-body-written-to-localstorage",
        [(f"{WS}/components/PositionSurface.tsx",
          replace("  async function attemptSave() {",
                  "  async function attemptSave() {\n    window.localStorage.setItem(\"draft\", body);"))],
    ),
    (
        "M-F05-C02 case-content-in-session-storage",
        [(f"{WS}/components/CaseDetailSurface.tsx",
          replace("      if (result.ok) setDetail(result.value);",
                  "      if (result.ok) { window.sessionStorage.setItem(\"case\", JSON.stringify(result.value)); setDetail(result.value); }"))],
    ),
    (
        "M-F05-C03 case-content-logged-to-console",
        [(f"{WS}/components/DeskSurface.tsx",
          replace("      if (result.ok) setCases(listProjection(result.value));",
                  "      if (result.ok) { console.log(result.value); setCases(listProjection(result.value)); }"))],
    ),
    (
        "M-F05-C04 storage-policy-opened-up",
        [(f"{WS}/policies/workspace.ts",
          replace("  if (!permitted.includes(purpose)) return false;",
                  "  if (!permitted.includes(purpose)) return true;"))],
    ),
    (
        "M-F05-C05 telemetry-platform-declared-connected",
        [(f"{WS}/policies/confidentiality.ts",
          replace("export const TELEMETRY_PLATFORM_CONNECTED = false as const;",
                  "export const TELEMETRY_PLATFORM_CONNECTED = true as const;"))],
    ),
    (
        "M-F05-C06 telemetry-no-longer-fails-closed",
        [(f"{WS}/policies/confidentiality.ts",
          replace("  if (!TELEMETRY_PLATFORM_CONNECTED) return false;", "  void 0;"))],
    ),
    (
        "M-F05-C07 error-report-carries-case-content",
        [(f"{WS}/policies/confidentiality.ts",
          replace("  carriesCaseContent: false,", "  carriesCaseContent: true,"))],
    ),
    (
        "M-F05-C08 confidential-payload-stripped-not-refused",
        [(f"{WS}/policies/confidentiality.ts",
          replace("  if (found.length > 0) throw new ConfidentialityError(found, where);",
                  "  void found;"))],
    ),
    (
        "M-F05-C09 unscoped-search-surface-rendered",
        [(f"{WS}/components/DeskSurface.tsx",
          replace("      <p className=\"informational\" data-search-policy>",
                  "      <input type=\"search\" name=\"q\" aria-label=\"Suche\" />\n      <p className=\"informational\" data-search-policy>"))],
    ),
    (
        "M-F05-C10 cross-mandate-search-permitted",
        [(f"{WS}/policies/confidentiality.ts",
          replace("  crossMandateSearch: false,", "  crossMandateSearch: true,"))],
    ),
    (
        "M-F05-C11 case-detail-discloses-restriction",
        [(f"{WS}/components/CaseDetailSurface.tsx",
          replace("      ) : restricted || detail === null ? (",
                  "      ) : restricted ? (\n        <RefusalPanel title=\"Gesperrt\" refusal={RESTRICTED_DISCLOSURE} />\n      ) : detail === null ? ("))],
    ),
    (
        "M-F05-C12 client-decides-an-authoritative-subject",
        [(f"{WS}/policies/boundaries.ts",
          sub(r"export function clientMayDecide\(subject: string\): false \{",
              "export function clientMayDecide(subject: string): boolean {\n  if (subject === \"case_state\") return true;"))],
    ),
]


def _rehash_raw(work: Path, step_id: str, raw_relative: str) -> None:
    """Recompute the evidence record's hash after its raw log was edited.

    The interesting attacker is not the clumsy one. These mutations edit the raw
    evidence *and* repair the hash that binds it, so detection has to come from
    re-derivation against the source tree rather than from a broken checksum.
    """
    record_path = work / f"validation/front05/evidence/{step_id}.json"
    if not record_path.is_file():
        return
    record = json.loads(record_path.read_text())
    raw = work / raw_relative
    if raw.is_file():
        record["raw_report_sha256"] = hashlib.sha256(raw.read_bytes()).hexdigest()
    record_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _rewrite_evidence(step_id: str, mutate: Callable[[dict], dict]):
    def apply(work: Path) -> None:
        path = work / f"validation/front05/evidence/{step_id}.json"
        if not path.is_file():
            return
        record = mutate(json.loads(path.read_text()))
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return apply


def _touch_source(work: Path) -> None:
    """Change a governed source file *after* the evidence was recorded.

    This is finding F04-C1-03 in one line: the tests passed, then the source
    changed, and the old PASS stayed on disk. The binding digests are what make
    it a FAIL rather than an unremarkable file edit.
    """
    target = work / WS / "domain/scope.ts"
    target.write_text(
        target.read_text(encoding="utf-8") + "\nexport const SMUGGLED = true;\n",
        encoding="utf-8",
    )


EVIDENCE_MUTATIONS: list[tuple[str, list[Edit], Callable[[Path], None] | None]] = [
    (
        "M-F05-E01 source-changed-after-evidence-recorded",
        [],
        _touch_source,
    ),
    (
        "M-F05-E02 new-source-file-added-after-evidence",
        [(f"{WS}/domain/smuggled.ts", lambda _: "export const SMUGGLED = true;\n")],
        None,
    ),
    (
        "M-F05-E03 evidence-digest-forged-to-match",
        [],
        _rewrite_evidence("unit", lambda r: {**r, "source_tree_digest": "0" * 64}),
    ),
    (
        "M-F05-E04 failing-step-relabelled-pass",
        [],
        _rewrite_evidence(
            "dependency_audit", lambda r: {**r, "result": "PASS", "exit_code": 0}
        ),
    ),
    (
        "M-F05-E05 raw-log-contradicts-the-recorded-result-and-is-rehashed",
        [(
            "validation/front05/raw/unit-tests.log",
            sub(r"exit_code=0", "exit_code=1"),
        )],
        lambda work: _rehash_raw(work, "unit", "validation/front05/raw/unit-tests.log"),
    ),
    (
        "M-F05-E06 raw-log-trailer-removed",
        [(
            "validation/front05/raw/build.log",
            sub(r"\nFRONT05_RAW_RESULT[^\n]*\n", "\n"),
        )],
        lambda work: _rehash_raw(work, "build", "validation/front05/raw/build.log"),
    ),
    (
        "M-F05-E07 raw-log-trailer-names-another-step",
        [(
            "validation/front05/raw/lint.log",
            sub(r"command=lint", "command=typecheck"),
        )],
        lambda work: _rehash_raw(work, "lint", "validation/front05/raw/lint.log"),
    ),
    (
        "M-F05-E08 lockfile-changed-after-evidence",
        [("package-lock.json", sub(r'"lockfileVersion": (\d+)', '"lockfileVersion": 9'))],
        None,
    ),
    (
        "M-F05-E09 competing-authoritative-result-added",
        [(
            "validation/front05/friendly_result.json",
            lambda _: json.dumps({"status": "PASS", "state": "ACCEPTED"}, indent=1) + "\n",
        )],
        None,
    ),
    (
        "M-F05-E10 verification-integrity-claims-an-unchanged-tree",
        [(
            "validation/front05/verification_integrity.json",
            json_edit(lambda d: {**d, "source_tree_digest_after": "1" * 64}),
        )],
        None,
    ),
]

# ------------------------------------- the two gates added beyond the seed set
SEED_EXTENSION_MUTATIONS: list[tuple[str, list[Edit], Callable[[Path], None] | None]] = [
    (
        "M-F05-S01 security-sensitive-capability-marked-supported",
        [(f"{WS}/domain/capabilities.ts",
          sub(r'(id: "publication_state_observation",\n    status: )BLOCKED',
              r'\1"SUPPORTED_REAL_PATH"'))],
        None,
    ),
    (
        "M-F05-S02 security-sensitive-capability-downgraded-to-a-limitation",
        [(f"{WS}/domain/capabilities.ts",
          sub(r'(id: "publication_proposal_submission",\n    status: )BLOCKED',
              r'\1"SUPPORTED_WITH_DECLARED_LIMITATION"'))],
        None,
    ),
    (
        "M-F05-S03 security-classification-downgraded-to-absent",
        [(f"{WS}/domain/capabilities.ts",
          sub(r'(id: "publication_proposal_submission",[\s\S]{0,600}?)dependencyClass: "SECURITY_SENSITIVE_BOUNDARY"',
              r'\1dependencyClass: "ABSENT"'))],
        None,
    ),
    (
        "M-F05-S04 caller-asserted-authorization-accepted",
        [(f"{WS}/domain/publication.ts",
          sub(r"export function callerAssertedAuthorizationSufficient\(\): false \{\n  return false;",
              "export function callerAssertedAuthorizationSufficient(): boolean {\n  return true;"))],
        None,
    ),
    (
        "M-F05-S05 security-finding-removed-from-the-reconciliation",
        [("docs/frontend/FRONT-05-PACK-DEPENDENCY-RECONCILIATION.md",
          lambda body: body.replace("self-asserted authorization", "a gap in the service"))],
        None,
    ),
    (
        "M-F05-S06 report-quotes-a-stale-source-tree-digest",
        [(REPORT, sub(r"`[0-9a-f]{64}`", "`" + "a" * 64 + "`"))],
        None,
    ),
]


def run_validator(tree: Path) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "scripts/validate_front05.py", "."],
        cwd=tree,
        capture_output=True,
        text=True,
        timeout=900,
    )
    try:
        payload = json.loads(proc.stdout)
        failing = [k for k, v in payload["gates"].items() if v["status"] != "PASS"]
    except Exception:
        # A validator that cannot even run is not a detection: it would score a
        # point for every mutation, including the ones that broke it.
        failing = ["VALIDATOR_DID_NOT_PRODUCE_A_RESULT"]
    return proc.returncode, failing


with tempfile.TemporaryDirectory(prefix="front05-base-") as temporary:
    baseline_tree = Path(temporary) / "package"
    shutil.copytree(root, baseline_tree, ignore=IGNORE, symlinks=False)
    baseline_code, baseline_failing = run_validator(baseline_tree)
print(f"baseline failing gates: {baseline_failing or 'none'}")

selected = {s for s in args.only.split(",") if s}

ALL: list[tuple[str, list[Edit], Callable[[Path], None] | None, str]] = (
    [(name, edits, None, "prohibition") for name, edits in PROHIBITION_MUTATIONS]
    + [(name, edits, None, "confidentiality") for name, edits in CONFIDENTIALITY_MUTATIONS]
    + [(name, edits, after, "evidence_chain") for name, edits, after in EVIDENCE_MUTATIONS]
    + [(name, edits, after, "seed_extension") for name, edits, after in SEED_EXTENSION_MUTATIONS]
)

results = []
for name, edits, after, family in ALL:
    identifier = name.split()[0]
    if selected and not any(identifier.startswith(p) for p in selected):
        continue
    with tempfile.TemporaryDirectory(prefix="front05-mut-") as temporary:
        work = Path(temporary) / "package"
        shutil.copytree(root, work, ignore=IGNORE, symlinks=False)
        error = None
        for relative, mutate in edits:
            target = work / relative
            if target.is_file():
                before = target.read_text(encoding="utf-8")
                changed = mutate(before)
                if changed == before:
                    error = f"mutation was a no-op in {relative}"
                    break
                target.write_text(changed, encoding="utf-8")
            else:
                # A mutation may legitimately introduce a new file: the
                # omitted-new-source and competing-result attacks depend on it.
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(mutate(""), encoding="utf-8")
        if error:
            results.append(
                {"id": identifier, "name": name, "family": family,
                 "detected": False, "error": error}
            )
            print(f"UNDETECTED (setup): {name}: {error}")
            continue
        if after:
            after(work)
        code, failing = run_validator(work)
        newly = [g for g in failing if g not in baseline_failing]
        results.append(
            {
                "id": identifier,
                "name": name,
                "family": family,
                "targets": [relative for relative, _ in edits],
                "detected": bool(newly),
                "exit_code": code,
                "detecting_gates": newly,
                "failing_gates": failing,
            }
        )
        status = "detected" if newly else "UNDETECTED"
        print(f"{status:>10}: {name} {newly}")

current = digest.summary(root)
out = {
    "schema": "epd2.front05.mutations/1",
    "authority": "NON_AUTHORITATIVE",
    "stage": "FRONT-05 — WS-04 Representative Workspace",
    "candidate_state": "CANDIDATE_NOT_ACCEPTED",
    "baseline_source_tree_digest": current["source_tree_digest"],
    "baseline_failing_gates": baseline_failing,
    "detection_rule": (
        "a mutation is DETECTED when it makes a validator gate fail that was not "
        "already failing on the unmutated tree"
    ),
    "count": len(results),
    "detected": sum(1 for entry in results if entry["detected"]),
    "families": {
        family: sum(1 for e in results if e["family"] == family)
        for family in ("prohibition", "confidentiality", "evidence_chain", "seed_extension")
    },
    "status": "PASS" if all(entry["detected"] for entry in results) else "FAIL",
    "mutations": results,
}
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("count", "detected", "families", "status")}, indent=1))
raise SystemExit(0 if out["status"] == "PASS" else 1)
