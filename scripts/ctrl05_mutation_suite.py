#!/usr/bin/env python3
"""CTRL-05 mutation / negative harness.

Fifty-two source mutants — one per obligation family of the CTRL-05
assignment — are applied to an isolated copy of the runtime and the executable
CTRL-05 test suite is run against each. A mutant is DETECTED only when the
suite fails. An UNDETECTED mutant means the tests do not actually enforce that
obligation, and the candidate must not be sealed.

The corpus is deliberately split: twenty-eight fixtures flip one governed
policy obligation each, and twenty-four edit the enforcing code directly, so
that a test cannot pass by asserting the policy object instead of the
behaviour.
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
TESTS = SERVICE / "tests"
VALIDATION = ROOT / "validation/ctrl05"
CONSOLE = "oversight_console.py"
SOURCES = "oversight_sources.py"
API = "oversight_api.py"


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
    # -- the twenty-eight governed obligations, one flip each ---------------
    policy_flip("M01", "accept a revoked or expired session", "enforce_session_state"),
    policy_flip("M02", "accept a mutation without its CSRF token", "enforce_csrf"),
    policy_flip("M03", "ignore organization scope", "enforce_organization_scope"),
    policy_flip("M04", "ignore oversight unit scope", "enforce_unit_scope"),
    policy_flip("M05", "ignore the mandated evidence planes", "enforce_plane_mandate"),
    policy_flip("M06", "accept a mandate with no governing rule", "enforce_competence_source"),
    policy_flip(
        "M07", "ignore the authority grant a mandate is bound to", "enforce_authority_version"
    ),
    policy_flip("M08", "remove commit-time reauthorization", "commit_time_reauthorization"),
    policy_flip("M09", "ignore the rights a mandate carries", "enforce_rights"),
    policy_flip("M10", "let an operational right grant oversight", "reject_operational_rights"),
    policy_flip("M11", "skip independent integrity verification", "enforce_integrity_verification"),
    policy_flip(
        "M12",
        "let a finding rest on untrustworthy evidence",
        "require_trustworthy_evidence_for_findings",
    ),
    policy_flip(
        "M13", "ignore evidence that changed since it was read", "enforce_evidence_divergence_check"
    ),
    policy_flip(
        "M14", "report an unavailable plane as no evidence", "fail_closed_on_source_unavailable"
    ),
    policy_flip("M15", "allow an unbounded evidence query", "enforce_query_bounds"),
    policy_flip("M16", "allow an unbounded correlation graph", "enforce_graph_bounds"),
    policy_flip("M17", "let review history be rewritten", "enforce_append_only_history"),
    policy_flip("M18", "ignore the case version at commit time", "enforce_case_version"),
    policy_flip("M19", "disable idempotency", "enforce_idempotency"),
    policy_flip(
        "M20",
        "attest without a prior disposition",
        "enforce_disposition_before_attestation",
    ),
    policy_flip(
        "M21",
        "raise a finding without an exact evidence reference",
        "enforce_finding_evidence_reference",
    ),
    policy_flip("M22", "export without a governed purpose", "enforce_export_purpose"),
    policy_flip("M23", "export without recording the redaction", "enforce_export_redaction_record"),
    policy_flip("M24", "stop redacting secret material", "enforce_secret_redaction"),
    policy_flip("M25", "stop screening person identifiers", "enforce_person_identifier_screen"),
    policy_flip("M26", "admit voting-domain evidence", "enforce_voting_boundary"),
    policy_flip("M27", "stop journaling refusals", "enforce_evidence_on_refusal"),
    policy_flip("M28", "accept a rewritten oversight journal", "enforce_journal_immutability"),
    # -- twenty-four direct edits to the enforcing code ---------------------
    Mutation(
        "M29",
        "accept a wildcard capability as oversight competence",
        CONSOLE,
        (
            (
                "            wildcard = [g for g in operational if _is_universal(g.capability)]\n",
                "            wildcard = []\n",
            ),
        ),
    ),
    Mutation(
        "M30",
        "match a bare unit label instead of the exact oversight scope",
        CONSOLE,
        (
            (
                "            if assigned is None or assigned != scope.key:\n",
                "            if assigned is not None and "
                'assigned.split(":")[-1] != scope.unit_id:\n',
            ),
        ),
    ),
    Mutation(
        "M31",
        "ignore the query's own plane filter",
        CONSOLE,
        (
            (
                "            planes = (query.planes & mandate.planes) "
                "if query.planes else mandate.planes\n",
                "            planes = mandate.planes\n",
            ),
        ),
    ),
    Mutation(
        "M32",
        "treat an unmapped evidence stream as visible",
        CONSOLE,
        (
            (
                "            if assigned is None or assigned != scope.key:\n",
                "            if assigned is not None and assigned != scope.key:\n",
            ),
        ),
    ),
    Mutation(
        "M33",
        "silently drop an unavailable plane instead of reporting it",
        SOURCES,
        (("            unavailable[source.plane.value] = exc.detail\n", "            pass\n"),),
    ),
    Mutation(
        "M34",
        "trust the recorded hash instead of re-deriving it",
        SOURCES,
        (("        if recomputed != recorded_hash:\n", "        if False:\n"),),
    ),
    Mutation(
        "M35",
        "treat a broken chain as trustworthy",
        SOURCES,
        (
            (
                "TRUSTWORTHY_STATES = frozenset({IntegrityState.VERIFIED})\n",
                "TRUSTWORTHY_STATES = frozenset(IntegrityState)\n",
            ),
        ),
    ),
    Mutation(
        "M36",
        "accept a coarse correlation anchor",
        CONSOLE,
        (
            (
                "                if not correlation_ref or correlation_ref in COARSE_TARGETS:\n",
                "                if False:\n",
            ),
        ),
    ),
    Mutation(
        "M37",
        "accept a coarse correlation graph anchor",
        CONSOLE,
        (
            (
                "                if not anchor or anchor in COARSE_TARGETS:\n",
                "                if False:\n",
            ),
        ),
    ),
    Mutation(
        "M38",
        "let a person identifier be used as a graph anchor",
        CONSOLE,
        (
            (
                "                if anchor.lower() in PERSON_IDENTIFIER_FIELDS:\n",
                "                if False:\n",
            ),
        ),
    ),
    Mutation(
        "M39",
        "leave the reauthorization ticket reusable",
        CONSOLE,
        (
            (
                '            ticket["consumed"] = True\n'
                '            self._remember(actor_ref, idempotency_key, "DISPOSE"',
                '            self._remember(actor_ref, idempotency_key, "DISPOSE"',
            ),
        ),
    ),
    Mutation(
        "M40",
        "drop the ticket actor and act binding",
        CONSOLE,
        (
            (
                '        if ticket["actor_ref"] != actor_ref or ticket["act"] != act:\n',
                "        if False:\n",
            ),
        ),
    ),
    Mutation(
        "M41",
        "ignore the ticket expiry",
        CONSOLE,
        (('        if moment >= _dt(ticket["expires_at"]):\n', "        if False:\n"),),
    ),
    Mutation(
        "M42",
        "prepare without capturing the evidence digests",
        CONSOLE,
        (
            (
                '                "evidence_digests": digests,\n',
                '                "evidence_digests": {},\n',
            ),
        ),
    ),
    Mutation(
        "M43",
        "close a case that was never attested",
        CONSOLE,
        (
            (
                "                if case.state is not ReviewState.ATTESTED:\n",
                "                if False:\n",
            ),
        ),
    ),
    Mutation(
        "M44",
        "replace a disposition instead of appending it",
        CONSOLE,
        (
            (
                "                disposition_ids=(*case.disposition_ids, record.disposition_id)\n"
                "                if self.policy.enforce_append_only_history\n",
                "                disposition_ids=(record.disposition_id,)\n"
                "                if self.policy.enforce_append_only_history\n",
            ),
        ),
    ),
    Mutation(
        "M45",
        "widen the export allow-list to every field",
        CONSOLE,
        (
            (
                "            allowed = EXPORT_PURPOSES.get(purpose, frozenset())\n",
                "            allowed = frozenset(k for e in envelopes for k in e.as_dict())\n",
            ),
        ),
    ),
    Mutation(
        "M46",
        "export without keeping the redaction decision",
        CONSOLE,
        (
            (
                "            self._redactions[decision.decision_id] = decision\n",
                "            pass\n",
            ),
        ),
    ),
    Mutation(
        "M47",
        "export without binding the payload digest",
        CONSOLE,
        (
            (
                "            digest = hashlib.sha256("
                "canonical_dumps(payload).encode()).hexdigest()\n",
                '            digest = "0" * 64\n',
            ),
        ),
    ),
    Mutation(
        "M48",
        "load a checkpoint whose tables disagree with the journal",
        CONSOLE,
        (("        service._verify_state_against_journal()\n", "        pass\n"),),
    ),
    Mutation(
        "M49",
        "load a re-chained checkpoint without verifying the keyed seal",
        CONSOLE,
        (
            (
                "            elif seal is None or not self.sealer.verify(count, head, seal):\n",
                "            elif False:\n",
            ),
        ),
    ),
    Mutation(
        "M50",
        "refuse without appending the refusal to the journal",
        CONSOLE,
        (
            (
                "        if self.policy.enforce_evidence_on_refusal:\n            self._record(\n",
                "        if False:\n            self._record(\n",
            ),
        ),
    ),
    Mutation(
        "M51",
        "let the client supply authoritative fields",
        API,
        (
            (
                "        present = sorted(set(body) & FORBIDDEN_CLIENT_FIELDS)\n",
                "        present = []\n",
            ),
        ),
    ),
    Mutation(
        "M52",
        "stop refusing the absent execution surfaces",
        API,
        (
            (
                "            if path in FORBIDDEN_SURFACES or any(\n"
                '                path.startswith(p + "/") for p in FORBIDDEN_SURFACES\n'
                "            ):\n",
                "            if False:\n",
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
    with tempfile.TemporaryDirectory(prefix=f"ctrl05-{mutation.mutation_id}-") as td:
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
                *sorted(str(p) for p in tests.glob("test_ctrl05_*.py")),
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
    if len(MUTATIONS) != 52 or len({m.mutation_id for m in MUTATIONS}) != 52:
        raise SystemExit("mutation corpus must contain exactly 52 distinct fixtures")
    sys.path.insert(0, str(ROOT / "scripts"))
    from ctrl05_common import runtime_source_digest  # type: ignore[import-not-found]

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
        "schema": "epd2.ctrl05.mutation-result/1",
        "stage": "CTRL-05",
        "required": 52,
        "executed": len(results),
        "detected": len(detected),
        "undetected": undetected,
        "baseline_summary": baseline.stdout.strip().splitlines()[-1],
        "runtime_source_digest": runtime_source_digest(),
        "results": results,
        "self_state": "CANDIDATE_NOT_ACCEPTED",
    }
    if args.only is None:
        VALIDATION.mkdir(parents=True, exist_ok=True)
        (VALIDATION / "mutation_result.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
    print(f"CTRL05_MUTATIONS:{len(detected)}/{len(results)}_DETECTED")
    return 0 if not undetected and len(results) == 52 else 1


if __name__ == "__main__":
    sys.exit(main())
