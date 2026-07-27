#!/usr/bin/env python3
"""Check the PACK-10 canon 0.8.0 amendment (documentation and version state).

Usage:
    python scripts/check_canon_0_8_0.py

This is a canon-amendment checker, not a business-behaviour checker. It
verifies what the 0.8.0 round is allowed to have changed and, just as
importantly, what it must not have changed:

    - the canon version is 0.8.0 in all three declaration sites;
    - REPOSITORY_VERSION is still 0.9.0 (19f.25 - this round ships no code);
    - canon-version.json still accepts a repository at 0.9.0;
    - PACK-10 is declared `not_implemented`;
    - no finance runtime implementation exists anywhere in the tree;
    - the finance bounded context (section 19f, 20.17, 22, 23, 24) is
      present, complete and internally consistent;
    - `FinancePartyHandle` is not a global identity;
    - finance carries no edge into voting;
    - no accepted ADR was rewritten by this round.

Exits with a non-zero status and prints every problem found. Run from
anywhere; the repository root is resolved relative to this script's
location.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Expected version state
# ---------------------------------------------------------------------------

EXPECTED_CANON_VERSION = "0.8.0"
EXPECTED_REPOSITORY_VERSION = "0.9.0"

CANON_FILE = "docs/canonical/TZ-00-domain-event-canon.md"
CANON_VERSION_FILE = "docs/canonical/canon-version.json"
PY_VERSION_FILE = "packages/python/epd2-core/src/epd2_core/version.py"
TS_VERSION_FILE = "packages/typescript/epd2-types/src/version.ts"

EXPECTED_FINANCE_IMPLEMENTATION_STATUS = "not_implemented"

# ---------------------------------------------------------------------------
# Finance context (section 19f) expectations
# ---------------------------------------------------------------------------

# 19f.1: the twenty-one authoritative finance aggregates, each of which
# must own exactly one section-22 ownership row (INV-02).
FINANCE_ENTITIES: tuple[str, ...] = (
    "FinanceAccount",
    "AccountingPeriod",
    "JournalEntry",
    "FinancialTransaction",
    "ImportBatch",
    "ReconciliationRecord",
    "FinanceContribution",
    "SponsorshipAgreement",
    "ExternalFinancialBenefit",
    "ExpenseClaim",
    "PaymentAuthorization",
    "Budget",
    "FinancialAsset",
    "FinancialObligation",
    "ReportingObligation",
    "ReportingPerimeterDefinition",
    "FinanceReport",
    "ReportSnapshot",
    "AuditEngagement",
    "FinancePolicy",
    "FinancePartyHandle",
)

FINANCE_OWNER = "Finance Service"
MINIMUM_FINANCE_OWNERSHIP_ROWS = 21
MINIMUM_FINANCE_EVENT_NAMES = 72
MINIMUM_FINANCE_REASON_CODES = 45

FINANCE_SECTION_HEADING = "# 19f."
FINANCE_EVENT_SECTION_HEADING = "## 20.17."
OWNERSHIP_SECTION_HEADING = "# 22."
FORBIDDEN_LINK_SECTION_HEADING = "# 23."
REASON_CODE_SECTION_HEADING = "# 24."

# Tokens that would reintroduce a global platform identity into finance.
GLOBAL_IDENTITY_TOKENS: tuple[str, ...] = ("PersonId", "UserId", "GlobalUserId")

# A token occurrence is acceptable only inside an explicit prohibition.
NEGATION_MARKERS: tuple[str, ...] = ("не ", "запрещ", "никогда", "запрет")

# 19f.14 writes its incompatibility matrix with the multiplication sign;
# this literal quotes the canon verbatim, so the ambiguous-character rule
# is suppressed rather than the canon transcribed inaccurately.
FINANCE_AUDITOR_INCOMPATIBLE_PAIR = "finance_auditor × finance_administrator"  # noqa: RUF001

# Entries the 20.17 prohibited-payload list must name explicitly.
PROHIBITED_PAYLOAD_TOKENS: tuple[str, ...] = (
    "значение credential",
    "информация о голосовании",  # noqa: RUF001
)

# Roots under which a finance runtime implementation would live if the
# 0.8.0 round had (wrongly) shipped one. 19f.25 forbids all of it.
FINANCE_SCAN_ROOTS: tuple[str, ...] = (
    "services",
    "packages",
    "frontend",
    "contracts",
)

FORBIDDEN_FINANCE_SERVICE_DIR = "services/finance-service"

IGNORED_DIRECTORY_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)

# ---------------------------------------------------------------------------
# ADR expectations
# ---------------------------------------------------------------------------

# ADR-001 .. ADR-043 predate this round and must be untouched by it.
ADR_PRE_EXISTING_RANGE: tuple[int, int] = (1, 43)
# ADR-044 .. ADR-050 are this round's own ADRs and must all be `proposed`.
ADR_THIS_ROUND_RANGE: tuple[int, int] = (44, 50)

# ADR-007 is documented as "reserved - not used by this governance round"
# in docs/adr/README.md and has never existed. The ADR list in
# scripts/check_repository.py skips it for the same reason (ADR-006 is
# followed there by ADR-008). It is a recorded numbering gap, not a
# weakening of this check.
ADR_NUMBERS_KNOWN_ABSENT: frozenset[int] = frozenset({7})

EXPECTED_THIS_ROUND_ADR_STATUS = "proposed"

_BULLET_RE = re.compile(r"^\s*(?:[-*+]\s|\d+\.\s)")
_EVENT_NAME_RE = re.compile(r"^\s*-\s+`([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)`")
_REASON_CODE_RE = re.compile(r"^-\s+`([A-Z][A-Z0-9_]*)`")
_OWNERSHIP_ROW_RE = re.compile(r"^\|\s*([A-Za-z][A-Za-z0-9_]*)\s*\|\s*([^|]+?)\s*\|\s*$")
_COMPATIBILITY_RE = re.compile(r"^>=\s*(\d+\.\d+\.\d+)\s+<\s*(\d+\.\d+\.\d+)$")
_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------


def _read_text(root: Path, relative_path: str) -> str | None:
    """Return the file's text, or None if it is absent or unreadable."""
    path = root / relative_path
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _normalize(text: str) -> str:
    """Collapse every whitespace run to a single space.

    The canon is hard-wrapped at ~72 columns, so a single canonical rule
    is routinely split across two or three physical lines. Substring
    assertions must therefore run against the unwrapped text.
    """
    return " ".join(text.split())


def _logical_lines(text: str) -> list[str]:
    """Split hard-wrapped Markdown into logical lines.

    A logical line is one bullet item, one heading, one fenced-code block
    or one paragraph - i.e. the unit an author writes a single sentence
    in, before the 72-column wrap breaks it up. Blank lines, bullet
    starts, headings and fence markers all end the current unit.
    """
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            flush()
            continue
        if _BULLET_RE.match(raw) or stripped.startswith("#") or stripped.startswith("```"):
            flush()
        current.append(stripped)
    flush()
    return blocks


def _extract_section(text: str, heading: str) -> str:
    """Return the text of the Markdown section introduced by `heading`.

    The section runs from its heading line to the next heading of the
    same or a higher level (a deeper subheading stays inside). Returns an
    empty string when the heading is absent.
    """
    lines = text.splitlines()
    level = len(heading) - len(heading.lstrip("#"))

    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith(heading):
            start = index
            break
    if start is None:
        return ""

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if not line.startswith("#"):
            continue
        hashes = len(line) - len(line.lstrip("#"))
        if hashes <= level and line[hashes : hashes + 1] == " ":
            end = index
            break
    return "\n".join(lines[start:end])


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    """Parse `X.Y.Z` into a comparable tuple, or None if malformed."""
    match = _SEMVER_RE.match(value.strip())
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _extract_py_constant(text: str, name: str) -> str | None:
    match = re.search(rf'^{name}\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def _extract_ts_constant(text: str, name: str) -> str | None:
    match = re.search(rf'export const {name}\s*=\s*"([^"]+)";', text)
    return match.group(1) if match else None


def _load_canon_metadata(root: Path) -> tuple[dict[str, object] | None, str | None]:
    """Return (parsed canon-version.json, problem message)."""
    text = _read_text(root, CANON_VERSION_FILE)
    if text is None:
        return None, f"{CANON_VERSION_FILE}: file is missing or unreadable."
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"{CANON_VERSION_FILE}: is not valid JSON ({exc})."
    if not isinstance(parsed, dict):
        return None, f"{CANON_VERSION_FILE}: top-level value is not a JSON object."
    return parsed, None


def _adr_path(root: Path, number: int) -> Path | None:
    """Return the single docs/adr/ADR-NNN-*.md file, or None if absent."""
    matches = sorted((root / "docs/adr").glob(f"ADR-{number:03d}-*.md"))
    return matches[0] if matches else None


def _adr_status(text: str) -> str:
    """Return the ADR's declared status, lowercased and de-quoted."""
    section = _extract_section(text, "## Status")
    body = [line.strip().strip("`").strip() for line in section.splitlines()[1:] if line.strip()]
    return " ".join(body).lower()


# ---------------------------------------------------------------------------
# Check 1 - canon version is 0.8.0 in all three declaration sites
# ---------------------------------------------------------------------------


def check_canon_version_declared(root: Path) -> list[str]:
    """The canon version must be exactly 0.8.0 in JSON, Python and TypeScript."""
    problems: list[str] = []

    metadata, error = _load_canon_metadata(root)
    if error is not None:
        problems.append(error)
    elif metadata is not None:
        declared = metadata.get("canon_version")
        if declared != EXPECTED_CANON_VERSION:
            problems.append(
                f"{CANON_VERSION_FILE}: canon_version is {declared!r}, "
                f"expected {EXPECTED_CANON_VERSION!r}."
            )

    py_text = _read_text(root, PY_VERSION_FILE)
    if py_text is None:
        problems.append(f"{PY_VERSION_FILE}: file is missing or unreadable.")
    else:
        value = _extract_py_constant(py_text, "CANON_VERSION")
        if value is None:
            problems.append(f'{PY_VERSION_FILE}: no CANON_VERSION = "..." assignment found.')
        elif value != EXPECTED_CANON_VERSION:
            problems.append(
                f"{PY_VERSION_FILE}: CANON_VERSION is {value!r}, "
                f"expected {EXPECTED_CANON_VERSION!r}."
            )

    ts_text = _read_text(root, TS_VERSION_FILE)
    if ts_text is None:
        problems.append(f"{TS_VERSION_FILE}: file is missing or unreadable.")
    else:
        value = _extract_ts_constant(ts_text, "CANON_VERSION")
        if value is None:
            problems.append(
                f'{TS_VERSION_FILE}: no export const CANON_VERSION = "..."; statement found.'
            )
        elif value != EXPECTED_CANON_VERSION:
            problems.append(
                f"{TS_VERSION_FILE}: CANON_VERSION is {value!r}, "
                f"expected {EXPECTED_CANON_VERSION!r}."
            )

    return problems


# ---------------------------------------------------------------------------
# Check 2 - REPOSITORY_VERSION is untouched by this round
# ---------------------------------------------------------------------------


def check_repository_version_unchanged(root: Path) -> list[str]:
    """19f.25: a canon-only round must leave REPOSITORY_VERSION at 0.9.0."""
    problems: list[str] = []

    py_text = _read_text(root, PY_VERSION_FILE)
    if py_text is None:
        problems.append(f"{PY_VERSION_FILE}: file is missing or unreadable.")
    else:
        value = _extract_py_constant(py_text, "REPOSITORY_VERSION")
        if value is None:
            problems.append(f'{PY_VERSION_FILE}: no REPOSITORY_VERSION = "..." assignment found.')
        elif value != EXPECTED_REPOSITORY_VERSION:
            problems.append(
                f"{PY_VERSION_FILE}: REPOSITORY_VERSION is {value!r}, expected "
                f"{EXPECTED_REPOSITORY_VERSION!r} - a canon-only round must not "
                f"bump the repository version (19f.25)."
            )

    ts_text = _read_text(root, TS_VERSION_FILE)
    if ts_text is None:
        problems.append(f"{TS_VERSION_FILE}: file is missing or unreadable.")
    else:
        value = _extract_ts_constant(ts_text, "REPOSITORY_VERSION")
        if value is None:
            problems.append(
                f'{TS_VERSION_FILE}: no export const REPOSITORY_VERSION = "..."; statement found.'
            )
        elif value != EXPECTED_REPOSITORY_VERSION:
            problems.append(
                f"{TS_VERSION_FILE}: REPOSITORY_VERSION is {value!r}, expected "
                f"{EXPECTED_REPOSITORY_VERSION!r} - a canon-only round must not "
                f"bump the repository version (19f.25)."
            )

    return problems


# ---------------------------------------------------------------------------
# Check 3 - compatibility metadata accepts a repository at 0.9.0
# ---------------------------------------------------------------------------


def check_repository_compatibility(root: Path) -> list[str]:
    """canon-version.json must still accept a repository at 0.9.0."""
    problems: list[str] = []

    metadata, error = _load_canon_metadata(root)
    if error is not None:
        return [error]
    if metadata is None:  # pragma: no cover - defensive, _load returns one or the other
        return [f"{CANON_VERSION_FILE}: could not be read."]

    raw_range = metadata.get("repository_compatibility")
    if not isinstance(raw_range, str):
        problems.append(
            f"{CANON_VERSION_FILE}: repository_compatibility is {raw_range!r}, "
            f"expected a range string of the form '>=X.Y.Z <A.B.C'."
        )
    else:
        match = _COMPATIBILITY_RE.match(raw_range.strip())
        if not match:
            problems.append(
                f"{CANON_VERSION_FILE}: repository_compatibility {raw_range!r} does "
                f"not parse as '>=X.Y.Z <A.B.C'."
            )
        else:
            lower = _parse_semver(match.group(1))
            upper = _parse_semver(match.group(2))
            current = _parse_semver(EXPECTED_REPOSITORY_VERSION)
            if lower is None or upper is None or current is None:
                problems.append(
                    f"{CANON_VERSION_FILE}: repository_compatibility {raw_range!r} "
                    f"contains a malformed version."
                )
            elif not (lower <= current < upper):
                problems.append(
                    f"{CANON_VERSION_FILE}: repository_compatibility {raw_range!r} does "
                    f"not include the current repository version "
                    f"{EXPECTED_REPOSITORY_VERSION}."
                )

    minimum = metadata.get("minimum_repository_version")
    if minimum != EXPECTED_REPOSITORY_VERSION:
        problems.append(
            f"{CANON_VERSION_FILE}: minimum_repository_version is {minimum!r}, "
            f"expected {EXPECTED_REPOSITORY_VERSION!r}."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 4 - PACK-10 is not declared implemented
# ---------------------------------------------------------------------------


def check_finance_implementation_status(root: Path) -> list[str]:
    """canon-version.json must declare the finance context `not_implemented`."""
    metadata, error = _load_canon_metadata(root)
    if error is not None:
        return [error]
    if metadata is None:  # pragma: no cover - defensive
        return [f"{CANON_VERSION_FILE}: could not be read."]

    status = metadata.get("finance_context_implementation_status")
    if status != EXPECTED_FINANCE_IMPLEMENTATION_STATUS:
        return [
            f"{CANON_VERSION_FILE}: finance_context_implementation_status is "
            f"{status!r}, expected {EXPECTED_FINANCE_IMPLEMENTATION_STATUS!r} "
            f"(19f.25 - this round authorizes no implementation)."
        ]
    return []


# ---------------------------------------------------------------------------
# Check 5 - no finance runtime implementation exists
# ---------------------------------------------------------------------------


def _iter_scanned_paths(root: Path, scan_root: str) -> list[Path]:
    """Return every file and directory under `scan_root`, skipping build dirs."""
    base = root / scan_root
    if not base.is_dir():
        return []

    found: list[Path] = []
    stack: list[Path] = [base]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name in IGNORED_DIRECTORY_NAMES:
                    continue
                found.append(entry)
                stack.append(entry)
            else:
                found.append(entry)
    return found


def check_no_finance_runtime_implementation(root: Path) -> list[str]:
    """19f.25: `services/finance-service` must not exist, and no path under
    services/, packages/, frontend/ or contracts/ may be named for finance."""
    problems: list[str] = []

    if (root / FORBIDDEN_FINANCE_SERVICE_DIR).exists():
        problems.append(
            f"{FORBIDDEN_FINANCE_SERVICE_DIR} exists - 19f.25 states it must not "
            f"be created by the canon round."
        )

    for scan_root in FINANCE_SCAN_ROOTS:
        for path in _iter_scanned_paths(root, scan_root):
            if "finance" in path.name.lower():
                problems.append(
                    f"{path.relative_to(root).as_posix()}: a finance-named path exists "
                    f"under {scan_root}/ - 19f.25 authorizes no finance implementation."
                )

    return sorted(problems)


# ---------------------------------------------------------------------------
# Check 6 - the finance bounded context is present in the canon
# ---------------------------------------------------------------------------


def _finance_ownership_rows(canon_text: str) -> list[str]:
    """Return the entity names owned by Finance Service in section 22 only."""
    section = _extract_section(canon_text, OWNERSHIP_SECTION_HEADING)
    owned: list[str] = []
    for line in section.splitlines():
        match = _OWNERSHIP_ROW_RE.match(line)
        if match and match.group(2).strip() == FINANCE_OWNER:
            owned.append(match.group(1))
    return owned


def check_finance_context_present(root: Path) -> list[str]:
    """Section 19f, subsection 20.17 and the section-22 ownership block must exist."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    problems: list[str] = []

    if not _extract_section(canon_text, FINANCE_SECTION_HEADING):
        problems.append(
            f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section heading - the "
            f"finance bounded context is absent."
        )
    if not _extract_section(canon_text, FINANCE_EVENT_SECTION_HEADING):
        problems.append(f"{CANON_FILE}: no '{FINANCE_EVENT_SECTION_HEADING}' event subsection.")

    rows = _finance_ownership_rows(canon_text)
    if len(rows) < MINIMUM_FINANCE_OWNERSHIP_ROWS:
        problems.append(
            f"{CANON_FILE}: section 22 has {len(rows)} '| <Entity> | {FINANCE_OWNER} |' "
            f"ownership rows, expected at least {MINIMUM_FINANCE_OWNERSHIP_ROWS}."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 7 - every finance aggregate has its own ownership row
# ---------------------------------------------------------------------------


def check_finance_entity_ownership(root: Path) -> list[str]:
    """INV-02: each of the twenty-one finance aggregates owns a section-22 row."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    owned = _finance_ownership_rows(canon_text)
    problems: list[str] = []

    for entity in FINANCE_ENTITIES:
        count = owned.count(entity)
        if count == 0:
            problems.append(
                f"{CANON_FILE}: section 22 has no '| {entity} | {FINANCE_OWNER} |' "
                f"ownership row (INV-02)."
            )
        elif count > 1:
            problems.append(
                f"{CANON_FILE}: section 22 has {count} ownership rows for {entity}, "
                f"expected exactly one (INV-02)."
            )

    return problems


# ---------------------------------------------------------------------------
# Check 8 - FinancePartyHandle is not a global identity
# ---------------------------------------------------------------------------


def check_finance_party_handle_not_global_identity(root: Path) -> list[str]:
    """INV-01 / FIN-01: section 19f may name PersonId, UserId or GlobalUserId
    only inside an explicit prohibition."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _extract_section(canon_text, FINANCE_SECTION_HEADING)
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section to scan."]

    problems: list[str] = []
    for logical_line in _logical_lines(section):
        present = [token for token in GLOBAL_IDENTITY_TOKENS if token in logical_line]
        if not present:
            continue
        if any(marker in logical_line for marker in NEGATION_MARKERS):
            continue
        problems.append(
            f"{CANON_FILE}: section 19f introduces {', '.join(present)} without an "
            f"explicit prohibition: {logical_line[:120]!r}"
        )

    return problems


# ---------------------------------------------------------------------------
# Check 9 - finance carries no edge into voting
# ---------------------------------------------------------------------------


def check_finance_voting_links_forbidden(root: Path) -> list[str]:
    """Section 23 must forbid finance -> Ballot, VoteEnvelope and voting credential."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _extract_section(canon_text, FORBIDDEN_LINK_SECTION_HEADING)
    if not section:
        return [f"{CANON_FILE}: no '{FORBIDDEN_LINK_SECTION_HEADING}' section found."]

    finance_markers = ("финанс", "20.17", "Finance", "finance")
    entries = [
        line for line in _logical_lines(section) if _BULLET_RE.match(line) or line.startswith("-")
    ]
    finance_entries = [
        entry for entry in entries if any(marker in entry for marker in finance_markers)
    ]

    problems: list[str] = []
    required_targets: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("Ballot", ("`Ballot`",)),
        ("VoteEnvelope", ("`VoteEnvelope`",)),
        (
            "a participation/voting credential",
            ("`ParticipationCredential`", "голосовательный credential"),
        ),
    )
    for label, tokens in required_targets:
        if not any(
            "→" in entry and any(token in entry for token in tokens) for entry in finance_entries
        ):
            problems.append(
                f"{CANON_FILE}: section 23 has no forbidden-link entry connecting a "
                f"finance concept to {label}."
            )

    return problems


# ---------------------------------------------------------------------------
# Check 10 - the ledger balances and posted entries are immutable
# ---------------------------------------------------------------------------


def check_ledger_immutability_and_balancing(root: Path) -> list[str]:
    """19f.4: the balanced-posting rule and the posted-entry-immutability rule."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _normalize(_extract_section(canon_text, FINANCE_SECTION_HEADING))
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section to scan."]

    problems: list[str] = []
    required: tuple[tuple[str, str], ...] = (
        (
            "Сумма дебетовых минорных единиц равна сумме кредитовых",
            "the balanced-posting rule (19f.4)",
        ),
        (
            "Проведённая запись неизменяема по содержанию",
            "the posted-entry-immutability rule (19f.4)",
        ),
        (
            "исправление — только новая сторнирующая или корректирующая запись",
            "the correction-by-reversal rule (19f.4, INV-05)",
        ),
    )
    for needle, label in required:
        if needle not in section:
            problems.append(f"{CANON_FILE}: section 19f does not state {label}.")

    return problems


# ---------------------------------------------------------------------------
# Check 11 - the finance-auditor incompatibility is registered
# ---------------------------------------------------------------------------


def check_finance_auditor_incompatibility(root: Path) -> list[str]:
    """19f.14: `finance_auditor` is incompatible with `finance_administrator`."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _normalize(_extract_section(canon_text, FINANCE_SECTION_HEADING))
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section to scan."]

    problems: list[str] = []
    if FINANCE_AUDITOR_INCOMPATIBLE_PAIR not in section:
        problems.append(
            f"{CANON_FILE}: section 19f does not register the pair "
            f"'{FINANCE_AUDITOR_INCOMPATIBLE_PAIR}' in the incompatibility matrix "
            f"(19f.14)."
        )
    if "несовместимост" not in section:
        problems.append(
            f"{CANON_FILE}: section 19f names no incompatibility ('несовместимость') "
            f"rule at all (19f.14)."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 12 - submission is not acceptance
# ---------------------------------------------------------------------------


def check_report_submission_distinct_from_acceptance(root: Path) -> list[str]:
    """19f.17: `submitted` and `externally_accepted` are distinct report states."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _normalize(_extract_section(canon_text, FINANCE_SECTION_HEADING))
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section to scan."]

    problems: list[str] = []
    for state in ("submitted", "externally_accepted"):
        if state not in section:
            problems.append(
                f"{CANON_FILE}: section 19f does not name the report state {state!r} (19f.17)."
            )

    if "Подача не подразумевает ни подтверждения получения, ни принятия" not in section:
        problems.append(
            f"{CANON_FILE}: section 19f does not state that submission alone is "
            f"neither acknowledgement nor acceptance (19f.17)."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 13 - PACK-11 and PACK-35 keep their domains
# ---------------------------------------------------------------------------


def check_cross_pack_ownership_unchanged(root: Path) -> list[str]:
    """19f.22: PACK-11 still owns documents/evidence, PACK-35 lobbying/meetings."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _normalize(_extract_section(canon_text, FINANCE_SECTION_HEADING))
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_SECTION_HEADING}' section to scan."]

    problems: list[str] = []
    required: tuple[tuple[str, str], ...] = (
        (
            "**PACK-11** владеет байтами документов",
            "that PACK-11 still owns document bytes and authoritative versions",
        ),
        (
            "содержимым доказательств",
            "that PACK-11 still owns evidence content",
        ),
        (
            "**PACK-35** владеет лоббистскими контактами, раскрытием встреч",
            "that PACK-35 still owns lobbying contacts and meeting disclosure",
        ),
    )
    for needle, label in required:
        if needle not in section:
            problems.append(f"{CANON_FILE}: section 19f does not state {label} (19f.22).")

    return problems


# ---------------------------------------------------------------------------
# Check 14 - the finance event catalogue is complete and governed
# ---------------------------------------------------------------------------


def _finance_event_names(canon_text: str) -> set[str]:
    section = _extract_section(canon_text, FINANCE_EVENT_SECTION_HEADING)
    return {
        match.group(1)
        for match in (_EVENT_NAME_RE.match(line) for line in section.splitlines())
        if match is not None
    }


def check_finance_event_catalogue(root: Path) -> list[str]:
    """20.17: one owner, an explicit prohibited payload, and >= 72 event names."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    section = _extract_section(canon_text, FINANCE_EVENT_SECTION_HEADING)
    if not section:
        return [f"{CANON_FILE}: no '{FINANCE_EVENT_SECTION_HEADING}' event subsection."]

    normalized = _normalize(section)
    problems: list[str] = []

    if "**Канонический владелец** — `finance-service`" not in normalized:
        problems.append(
            f"{CANON_FILE}: section 20.17 carries no owner statement naming "
            f"`finance-service` for every event of the section."
        )
    if "Ни один другой сервис не создаёт событий раздела 20.17" not in normalized:
        problems.append(
            f"{CANON_FILE}: section 20.17 does not state that no other service "
            f"creates or owns its events."
        )
    if "**Запрещённый payload** —" not in normalized:
        problems.append(f"{CANON_FILE}: section 20.17 carries no prohibited-payload statement.")
    else:
        for token in PROHIBITED_PAYLOAD_TOKENS:
            if token not in normalized:
                problems.append(
                    f"{CANON_FILE}: the section 20.17 prohibited-payload list does not "
                    f"mention {token!r}."
                )

    names = _finance_event_names(canon_text)
    if len(names) < MINIMUM_FINANCE_EVENT_NAMES:
        problems.append(
            f"{CANON_FILE}: section 20.17 defines {len(names)} distinct backticked "
            f"event names, expected at least {MINIMUM_FINANCE_EVENT_NAMES}."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 15 - the reason code registry is unique and complete
# ---------------------------------------------------------------------------


def _reason_code_entries(canon_text: str) -> list[str]:
    section = _extract_section(canon_text, REASON_CODE_SECTION_HEADING)
    return [
        match.group(1)
        for match in (_REASON_CODE_RE.match(line) for line in section.splitlines())
        if match is not None
    ]


def check_reason_code_registry(root: Path) -> list[str]:
    """Section 24: every defined code is unique, and >= 45 are `FINANCE_*`."""
    canon_text = _read_text(root, CANON_FILE)
    if canon_text is None:
        return [f"{CANON_FILE}: file is missing or unreadable."]

    codes = _reason_code_entries(canon_text)
    if not codes:
        return [f"{CANON_FILE}: section 24 defines no reason codes at all."]

    problems: list[str] = []

    seen: set[str] = set()
    duplicates: list[str] = []
    for code in codes:
        if code in seen and code not in duplicates:
            duplicates.append(code)
        seen.add(code)
    for code in duplicates:
        problems.append(f"{CANON_FILE}: section 24 defines reason code {code!r} more than once.")

    finance_codes = [code for code in codes if code.startswith("FINANCE_")]
    if len(finance_codes) < MINIMUM_FINANCE_REASON_CODES:
        problems.append(
            f"{CANON_FILE}: section 24 defines {len(finance_codes)} FINANCE_* reason "
            f"codes, expected at least {MINIMUM_FINANCE_REASON_CODES}."
        )

    return problems


# ---------------------------------------------------------------------------
# Check 16 - no accepted ADR was rewritten by this round
# ---------------------------------------------------------------------------


def check_adr_set_unchanged(root: Path) -> list[str]:
    """ADR-001..043 survive untouched by 0.8.0; ADR-044..050 are `proposed`.

    The strong form of this check would compare accepted ADRs byte for
    byte against their pre-round content, which a self-contained checker
    cannot do. The weaker, self-contained form used here: every
    pre-existing ADR must still be present, and none of them may carry
    `0.8.0` in its Status or Date block - i.e. this round re-statused
    none of them.
    """
    problems: list[str] = []

    for number in range(ADR_PRE_EXISTING_RANGE[0], ADR_PRE_EXISTING_RANGE[1] + 1):
        if number in ADR_NUMBERS_KNOWN_ABSENT:
            continue
        path = _adr_path(root, number)
        if path is None:
            problems.append(f"docs/adr/ADR-{number:03d}-*.md is missing.")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            problems.append(f"{path.relative_to(root).as_posix()}: unreadable.")
            continue
        for heading in ("## Status", "## Date"):
            block = _extract_section(text, heading)
            if EXPECTED_CANON_VERSION in block:
                problems.append(
                    f"{path.relative_to(root).as_posix()}: its '{heading}' block "
                    f"mentions {EXPECTED_CANON_VERSION} - a canon round must not "
                    f"re-status or re-date a pre-existing ADR."
                )

    for number in range(ADR_THIS_ROUND_RANGE[0], ADR_THIS_ROUND_RANGE[1] + 1):
        if number in ADR_NUMBERS_KNOWN_ABSENT:
            continue
        path = _adr_path(root, number)
        if path is None:
            problems.append(f"docs/adr/ADR-{number:03d}-*.md is missing.")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            problems.append(f"{path.relative_to(root).as_posix()}: unreadable.")
            continue
        status = _adr_status(text)
        if EXPECTED_THIS_ROUND_ADR_STATUS not in status:
            problems.append(
                f"{path.relative_to(root).as_posix()}: Status is {status!r}, expected "
                f"{EXPECTED_THIS_ROUND_ADR_STATUS!r} - the 0.8.0 round accepts no ADR."
            )

    return problems


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

CHECKS: tuple[tuple[str, str], ...] = (
    ("check_canon_version_declared", "canon version is 0.8.0 everywhere"),
    ("check_repository_version_unchanged", "REPOSITORY_VERSION is still 0.9.0"),
    ("check_repository_compatibility", "compatibility metadata accepts 0.9.0"),
    ("check_finance_implementation_status", "PACK-10 declared not_implemented"),
    ("check_no_finance_runtime_implementation", "no finance runtime implementation"),
    ("check_finance_context_present", "finance bounded context present"),
    ("check_finance_entity_ownership", "all 21 finance aggregates owned"),
    ("check_finance_party_handle_not_global_identity", "no global identity in 19f"),
    ("check_finance_voting_links_forbidden", "finance-to-voting links forbidden"),
    ("check_ledger_immutability_and_balancing", "ledger balances and is immutable"),
    ("check_finance_auditor_incompatibility", "finance auditor incompatibility"),
    ("check_report_submission_distinct_from_acceptance", "submission is not acceptance"),
    ("check_cross_pack_ownership_unchanged", "PACK-11 / PACK-35 keep their domains"),
    ("check_finance_event_catalogue", "20.17 event catalogue governed"),
    ("check_reason_code_registry", "reason codes unique and complete"),
    ("check_adr_set_unchanged", "no accepted ADR rewritten"),
)


def find_problems(root: Path) -> list[str]:
    """Return every problem found by every check, empty if the 0.8.0 canon
    amendment is in the state it declares itself to be in."""
    problems: list[str] = []
    problems.extend(check_canon_version_declared(root))
    problems.extend(check_repository_version_unchanged(root))
    problems.extend(check_repository_compatibility(root))
    problems.extend(check_finance_implementation_status(root))
    problems.extend(check_no_finance_runtime_implementation(root))
    problems.extend(check_finance_context_present(root))
    problems.extend(check_finance_entity_ownership(root))
    problems.extend(check_finance_party_handle_not_global_identity(root))
    problems.extend(check_finance_voting_links_forbidden(root))
    problems.extend(check_ledger_immutability_and_balancing(root))
    problems.extend(check_finance_auditor_incompatibility(root))
    problems.extend(check_report_submission_distinct_from_acceptance(root))
    problems.extend(check_cross_pack_ownership_unchanged(root))
    problems.extend(check_finance_event_catalogue(root))
    problems.extend(check_reason_code_registry(root))
    problems.extend(check_adr_set_unchanged(root))
    return problems


def main() -> int:
    problems = find_problems(REPO_ROOT)
    if problems:
        print("Canon 0.8.0 amendment problems found:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"OK: all {len(CHECKS)} canon 0.8.0 amendment checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
