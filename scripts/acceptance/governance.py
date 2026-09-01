"""Governance-state verification (INFRA01-HI-03 support, repository gate).

Structural, fail-closed checks derived from the canonical project entrypoint:
the three canonical bootstrap/control/master files must exist exactly once,
no competing control or master register may exist anywhere in the candidate,
and the declared repository/canon versions must be internally consistent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance import codes
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
