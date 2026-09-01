"""Governance-state verification (INFRA01-HI-03 support, repository gate).

Structural, fail-closed checks derived from the canonical project entrypoint:
the three canonical bootstrap/control/master files must exist exactly once,
no competing control or master register may exist anywhere in the candidate,
and the declared repository/canon versions must be internally consistent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.acceptance import codes
from scripts.acceptance.canonical import (
    load_json,
    seal_document,
    sha256_bytes,
    sha256_file,
    verify_sealed_document,
)
from scripts.verify_versions import find_mismatches

CANONICAL_GOVERNANCE_FILES = (
    "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md",
    "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md",
    "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
)

#: Filename shapes that would constitute a competing canonical register if
#: they appear anywhere other than the canonical paths above.
_REGISTER_NAME_PATTERN = re.compile(
    r"(MASTER_FUTURE_IMPLEMENTATION_REGISTER|PROGRAM_CONTROL_REGISTER)", re.IGNORECASE
)


@dataclass(frozen=True)
class GovernanceFinding:
    code: str
    path: str
    detail: str


def verify_governance(root: Path, tracked: list[str]) -> list[GovernanceFinding]:
    findings: list[GovernanceFinding] = []
    tracked_set = set(tracked)

    for canonical in CANONICAL_GOVERNANCE_FILES:
        if canonical not in tracked_set or not (root / canonical).is_file():
            findings.append(
                GovernanceFinding(
                    codes.GOVERNANCE_FILE_MISSING, canonical, "canonical governance file missing"
                )
            )

    for rel in sorted(tracked_set):
        if rel in CANONICAL_GOVERNANCE_FILES:
            continue
        name = rel.rsplit("/", 1)[-1]
        if _REGISTER_NAME_PATTERN.search(name):
            findings.append(
                GovernanceFinding(
                    codes.COMPETING_REGISTER,
                    rel,
                    "competing copy of a canonical register outside its governed path",
                )
            )

    try:
        for mismatch in find_mismatches(root):
            findings.append(GovernanceFinding(codes.VERSION_MISMATCH, "versions", mismatch))
    except (OSError, KeyError, ValueError) as error:
        findings.append(
            GovernanceFinding(
                codes.VERSION_MISMATCH, "versions", f"version sources unreadable: {error}"
            )
        )
    return findings


# -- governance freshness / current-target reconciliation (INFRA-01 C1) ----
#
# ``canonical files exist != canonical files are unique != canonical files
# are current``. The three original checks prove existence and uniqueness;
# the mechanism below proves currency against the governed target authority
# used at seal time, fail closed.
#
# The sealed reconciliation record binds: the exact target authority
# (repository / branch / commit / tree / canonical-file identities) used as
# the reconciliation base, the exact candidate Program Control Register
# bytes produced by that reconciliation, and the expected current execution
# facts, each anchored to a specific *current-state region* of the register
# so that preserved historical statements are never mistaken for current
# state. A stale register cannot be made self-valid by rehashing it into
# the record: rewriting the recorded facts or the recorded target authority
# changes exactly the fields the independent reviewer compares against the
# real current target, and regressing the register against intact recorded
# facts is detected semantically below.

RECONCILIATION_FILE = "docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json"
PCR_FILE = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"

#: The current-state regions of the Program Control Register. Everything
#: outside these regions is treated as preserved history and never judged.
_REGION_SPECS: tuple[tuple[str, str, str], ...] = (
    # (region id, start marker, end marker) — text between the first
    # occurrence of start marker and the next occurrence of end marker.
    ("primary_position", "Current primary position:", "###"),
    ("layer_table", "## 2. Program phase state", "Canonical primary closure sequence"),
    ("immediate_execution", "## 9. Immediate execution decision", "\n## "),
)


def extract_current_state_regions(pcr_text: str) -> dict[str, str]:
    """Extract the register's current-state regions; absent regions omitted."""
    regions: dict[str, str] = {}
    for region_id, start_marker, end_marker in _REGION_SPECS:
        start = pcr_text.find(start_marker)
        if start < 0:
            continue
        rest = pcr_text[start + len(start_marker) :]
        end = rest.find(end_marker)
        regions[region_id] = rest if end < 0 else rest[:end]
    return regions


_MAX_FUTURE_SKEW = timedelta(minutes=10)


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _temporal_findings(record: dict[str, object]) -> list[GovernanceFinding]:
    """Temporal provenance (INFRA01-C2-02): mechanically enforced, never left
    to human inspection of timestamps.

    ``reconciled_at`` and ``target_commit_timestamp`` must both be present,
    timezone-aware and parseable; reconciliation cannot predate the target
    commit it claims to have used, and cannot lie in the future relative to
    validation time (beyond a small clock-skew allowance).
    """
    findings: list[GovernanceFinding] = []
    reconciled_at = _parse_timestamp(record.get("reconciled_at"))
    target_ts = _parse_timestamp(record.get("target_commit_timestamp"))
    if reconciled_at is None:
        findings.append(
            GovernanceFinding(
                codes.RECONCILIATION_TIME_INVALID,
                "reconciled_at",
                "missing or unparseable timezone-aware reconciliation timestamp",
            )
        )
    if target_ts is None:
        findings.append(
            GovernanceFinding(
                codes.RECONCILIATION_TIME_INVALID,
                "target_commit_timestamp",
                "missing or unparseable timezone-aware target-commit timestamp",
            )
        )
    if reconciled_at is None or target_ts is None:
        return findings
    if reconciled_at < target_ts:
        findings.append(
            GovernanceFinding(
                codes.RECONCILIATION_TIME_INVALID,
                "reconciled_at",
                f"reconciliation claims {reconciled_at.isoformat()} — before its own "
                f"target commit at {target_ts.isoformat()}; temporally impossible "
                "provenance",
            )
        )
    now = datetime.now(tz=UTC)
    if reconciled_at - now > _MAX_FUTURE_SKEW:
        findings.append(
            GovernanceFinding(
                codes.RECONCILIATION_TIME_INVALID,
                "reconciled_at",
                f"reconciliation timestamp {reconciled_at.isoformat()} lies in the "
                "future relative to validation time; impossible ordering",
            )
        )
    return findings


def build_reconciliation_record(
    target_authority: dict[str, str],
    candidate_pcr_sha256: str,
    expected_current_state: list[dict[str, object]],
    reconciled_at: str,
    target_commit_timestamp: str,
    note: str = "",
) -> dict[str, object]:
    """Build and seal a governance reconciliation record.

    ``target_commit_timestamp`` is the committer timestamp of the exact
    target commit the reconciliation used, and ``reconciled_at`` must be
    truthful: a sealed record whose reconciliation claims to predate its own
    target authority is temporally impossible provenance and is refused by
    :func:`verify_freshness` (INFRA01-C2-02).
    """
    document: dict[str, object] = {
        "schema": "epd2.infra01.governance-reconciliation/2",
        "reconciled_at": reconciled_at,
        "target_commit_timestamp": target_commit_timestamp,
        "note": note,
        "target_authority": dict(sorted(target_authority.items())),
        "candidate": {"pcr_path": PCR_FILE, "pcr_sha256": candidate_pcr_sha256},
        "expected_current_state": expected_current_state,
    }
    return seal_document(document)


def _fact_findings(fact: dict[str, object], regions: dict[str, str]) -> list[GovernanceFinding]:
    findings: list[GovernanceFinding] = []
    fact_id = str(fact.get("id", "unnamed-fact"))
    region_id = str(fact.get("region", ""))
    region = regions.get(region_id)
    if region is None:
        findings.append(
            GovernanceFinding(
                codes.GOVERNANCE_REGION_MISSING,
                fact_id,
                f"current-state region {region_id!r} not found in the register",
            )
        )
        return findings
    must_include = fact.get("must_include", [])
    for required in must_include if isinstance(must_include, list) else []:
        if str(required) not in region:
            findings.append(
                GovernanceFinding(
                    codes.GOVERNANCE_TRANSITION_MISSING,
                    fact_id,
                    f"required current-state fact absent from {region_id}: {required!r} — "
                    "the register lacks a transition the target authority records",
                )
            )
    must_exclude = fact.get("must_exclude", [])
    for forbidden in must_exclude if isinstance(must_exclude, list) else []:
        if str(forbidden) in region:
            findings.append(
                GovernanceFinding(
                    codes.STALE_GOVERNANCE_STATE,
                    fact_id,
                    f"stale/regressed statement present in current-state region "
                    f"{region_id}: {forbidden!r}",
                )
            )
    return findings


def verify_freshness(root: Path) -> list[GovernanceFinding]:
    """Fail-closed governance-freshness verification of the candidate."""
    record_path = root / RECONCILIATION_FILE
    if not record_path.is_file():
        return [
            GovernanceFinding(
                codes.RECONCILIATION_RECORD_MISSING,
                RECONCILIATION_FILE,
                "governance reconciliation record absent; candidate currency unproven",
            )
        ]
    try:
        record = load_json(record_path)
    except ValueError as error:
        return [
            GovernanceFinding(
                codes.RECONCILIATION_INTEGRITY_FAILURE,
                RECONCILIATION_FILE,
                f"unreadable reconciliation record: {error}",
            )
        ]
    if not isinstance(record, dict) or not verify_sealed_document(record):
        return [
            GovernanceFinding(
                codes.RECONCILIATION_INTEGRITY_FAILURE,
                RECONCILIATION_FILE,
                "reconciliation record integrity digest does not match its content",
            )
        ]

    findings: list[GovernanceFinding] = []
    target = record.get("target_authority", {})
    for required_key in ("repository", "branch", "commit", "tree", "pcr_git_blob", "pcr_sha256"):
        if not str(target.get(required_key, "")).strip():
            findings.append(
                GovernanceFinding(
                    codes.RECONCILIATION_INTEGRITY_FAILURE,
                    f"target_authority.{required_key}",
                    "reconciliation record does not identify the target authority",
                )
            )

    findings.extend(_temporal_findings(record))

    candidate = record.get("candidate", {})
    pcr_path = root / str(candidate.get("pcr_path", PCR_FILE))
    if not pcr_path.is_file():
        findings.append(
            GovernanceFinding(
                codes.GOVERNANCE_FILE_MISSING, str(candidate.get("pcr_path")), "register absent"
            )
        )
        return findings
    actual_pcr_sha = sha256_file(pcr_path)
    if actual_pcr_sha != str(candidate.get("pcr_sha256", "")):
        findings.append(
            GovernanceFinding(
                codes.GOVERNANCE_RECONCILIATION_MISMATCH,
                str(candidate.get("pcr_path")),
                f"register bytes {actual_pcr_sha} do not match the reconciled "
                f"{candidate.get('pcr_sha256')!r}; the register changed after "
                "reconciliation and must be re-reconciled against the current target",
            )
        )

    facts = record.get("expected_current_state", [])
    if not isinstance(facts, list) or not facts:
        findings.append(
            GovernanceFinding(
                codes.RECONCILIATION_INTEGRITY_FAILURE,
                "expected_current_state",
                "reconciliation record carries no expected current-state facts",
            )
        )
        return findings
    regions = extract_current_state_regions(pcr_path.read_text(encoding="utf-8"))
    for fact in facts:
        if isinstance(fact, dict):
            findings.extend(_fact_findings(fact, regions))
    return findings


def compare_target_authority(root: Path, target_pcr_bytes: bytes) -> list[GovernanceFinding]:
    """Compare the record's target authority against an externally supplied
    current target register (the authoritative-path binding)."""
    record_path = root / RECONCILIATION_FILE
    if not record_path.is_file():
        return [
            GovernanceFinding(
                codes.RECONCILIATION_RECORD_MISSING, RECONCILIATION_FILE, "record absent"
            )
        ]
    record = load_json(record_path)
    recorded = str(record.get("target_authority", {}).get("pcr_sha256", ""))
    actual = sha256_bytes(target_pcr_bytes)
    if recorded != actual:
        return [
            GovernanceFinding(
                codes.TARGET_AUTHORITY_MISMATCH,
                "target_authority.pcr_sha256",
                f"recorded target register {recorded!r} is not the current target "
                f"register {actual!r}; the target has advanced (or the record was "
                "rewritten) and the candidate must be re-reconciled",
            )
        ]
    return []
