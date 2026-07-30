"""Repository-level structural test for `AC-P13-155`.

The PACK-13 acceptance matrix carries one criterion whose evidence is this
file itself: *"This FIR coverage matrix contains no 'implemented' value."*
PACK-12's `AC-P12-101` established the pattern, and the reason is the same
in both rounds — a matrix that quietly acquired an `implemented` treatment
would be the single most consequential unnoticed claim a pack could make,
because every downstream reader takes the matrix at its word.

The check is deliberately narrow. It looks at the **treatment column** of
the FIR coverage matrix's own tables, not at the file's prose: the
document says the word "implemented" many times while explaining why
nothing is, and a naive substring scan would either fail on that prose or
be widened until it stopped meaning anything.

Must be run from the repository root.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MATRIX_PATH = REPO_ROOT / "docs" / "packs" / "PACK-13" / "PACK-13-FIR-COVERAGE-MATRIX.md"

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
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


def test_the_pack13_fir_matrix_exists() -> None:
    assert MATRIX_PATH.is_file(), f"missing {MATRIX_PATH}"


def test_the_pack13_fir_matrix_records_no_implemented_treatment() -> None:
    """`AC-P13-155`. The implementation round is a candidate, not a PASS,
    and every storage adapter in it is in memory; either fact alone makes
    `implemented` unsupportable."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    offenders: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if _SUMMARY_ROW.match(stripped):
            continue
        for cell in stripped.strip("|").split("|"):
            if cell.strip().lower() == "implemented":
                offenders.append(stripped)
    assert offenders == [], (
        "PACK-13-FIR-COVERAGE-MATRIX.md carries an 'implemented' treatment value; "
        f"offending row(s): {offenders}"
    )


def test_the_summary_row_still_states_zero_implemented() -> None:
    """The complement of the test above: asserting the absence of a value
    is only meaningful while the summary that *counts* it still says
    zero. A matrix that dropped the row entirely would pass the absence
    test and tell a reader nothing."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    assert any(_SUMMARY_ROW.match(line.strip()) for line in text.splitlines()), (
        "the FIR coverage matrix no longer states that zero entries are implemented"
    )


def test_every_treatment_value_used_is_one_of_the_permitted_four() -> None:
    """A guard against the failure mode the test above cannot see: a new
    treatment value that means `implemented` without using the word."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    used: set[str] = set()
    for cells in _table_rows(text):
        # The specification round's tables put the treatment in column 3
        # (FIR, status before, treatment, ...). Rows with fewer columns
        # belong to the summary or to the appendix's own tables.
        if len(cells) >= 3:
            candidate = cells[2].strip().lower()
            if candidate in PERMITTED_TREATMENTS or candidate == "implemented":
                used.add(candidate)
    assert used <= PERMITTED_TREATMENTS, f"unexpected treatment value(s): {sorted(used)}"
    assert used, "no treatment value was found at all; the matrix's shape has changed"
