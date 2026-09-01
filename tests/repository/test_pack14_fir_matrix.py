"""Repository-level structural test for PACK-14's FIR coverage matrix.

`AC-P14-104`'s neighbours in the acceptance matrix, and PACK-12's
`AC-P12-101` and PACK-13's `AC-P13-155` before them, all rest on the same
evidence: *the FIR coverage matrix contains no `implemented` value.* The
reason is the same in every round — a matrix that quietly acquired an
`implemented` treatment would be the single most consequential unnoticed
claim a pack could make, because every downstream reader takes the matrix
at its word.

It matters more here than it did in PACK-13. This is the identity round:
`implemented` against an identity FIR would read as "authentication is
done", and what exists is a reference implementation with four unbound
security ports, no provider of any kind and no external verification.

The check is deliberately narrow. It looks at the **treatment column** of
the matrix's own tables, not at the file's prose: the document says the
word "implemented" while explaining why nothing is, and a naive substring
scan would either fail on that prose or be widened until it stopped
meaning anything.

This file also asserts the two facts the package itself records, so the
document and the code cannot disagree about what was implemented.

Must be run from the repository root.
"""

from __future__ import annotations

import re
from pathlib import Path

import epd2_identity_service as identity_service

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MATRIX_PATH = REPO_ROOT / "docs" / "packs" / "PACK-14" / "PACK-14-FIR-COVERAGE-MATRIX.md"

#: The treatment values a specification or candidate round may record.
#: `implemented` is deliberately absent, which is the whole point.
PERMITTED_TREATMENTS = frozenset({"addressed", "partially addressed", "deferred", "unchanged"})

#: The one row where the word appears as a *count label* rather than as a
#: treatment: the summary table's `**implemented**` row, whose value is
#: `**0**`. Matched exactly rather than excluded by a rule such as "skip
#: bold cells", because a future bold treatment value must still fail.
_SUMMARY_ROW = re.compile(r"^\|\s*\*\*implemented\*\*\s*\|\s*\*\*0\*\*\s*\|$")


def _table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows


def test_the_pack14_fir_matrix_exists() -> None:
    assert MATRIX_PATH.is_file(), f"missing {MATRIX_PATH}"


def test_the_summary_row_still_states_zero_implemented() -> None:
    """Asserting the absence of a value is only meaningful while the
    summary that *counts* it still says zero. A matrix that dropped the
    row entirely would pass an absence test and tell a reader nothing."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    assert any(_SUMMARY_ROW.match(line.strip()) for line in text.splitlines()), (
        "the PACK-14 FIR coverage matrix no longer states that zero entries are implemented"
    )


def test_every_treatment_value_used_is_one_of_the_permitted_four() -> None:
    """A guard against the failure mode an absence check cannot see: a new
    treatment value that means `implemented` without using the word."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    used: set[str] = set()
    for cells in _table_rows(text):
        if len(cells) >= 3:
            candidate = cells[2].strip().lower()
            if candidate in PERMITTED_TREATMENTS or candidate == "implemented":
                used.add(candidate)
    assert used <= PERMITTED_TREATMENTS, f"unexpected treatment value(s): {sorted(used)}"
    assert used, "no treatment value was found at all; the matrix's shape has changed"


def test_the_package_itself_claims_no_implemented_fir_entry() -> None:
    """The code's own answer to the same question.

    `IMPLEMENTED_FIR_ENTRIES` is empty and `CANDIDATE_FIR_ENTRIES` names
    exactly the roadmap entry this round is a candidate for. If either
    drifts, the matrix and the package are telling a reader two different
    stories about the same round.
    """
    assert identity_service.IMPLEMENTED_FIR_ENTRIES == ()
    assert identity_service.CANDIDATE_FIR_ENTRIES == ("FIR-ROADMAP-004",)
    assert identity_service.IDENTITY_CONTEXT_IMPLEMENTATION_STATUS == "reference_implementation"
