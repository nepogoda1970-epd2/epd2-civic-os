from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()

    # Revert the over-broad interim CURRENT-cue classifier. Historical
    # correction reports must remain historical even when their own old
    # headings contain "Candidate:" / "Role:".
    stale = root / "scripts/api02/build_stale_audit.py"
    text = stale.read_text()
    broad_header = '''CURRENT_IDENTITY_CUES: tuple[str, ...] = (\n    r"\\bthis candidate\\b",\n    r"\\bcurrent candidate\\b",\n    r"\\*\\*Candidate:\\*\\*",\n    r"\\*\\*Role:\\*\\*",\n)\n\n\ndef _classify_text(text: str, *, heading: str = "") -> tuple[str, str]:\n    """Classify one current-state context.\n\n    An explicit claim about this/current candidate is CURRENT by definition.\n    It cannot be downgraded to HISTORICAL because the same block also names\n    an entering predecessor or contains a past-round cue. N5/N6 enforce this.\n    """\n'''
    original_header = '''def _classify_text(text: str, *, heading: str = "") -> tuple[str, str]:\n    """One classifier, used by every file kind, so the rule is one rule."""\n'''
    if broad_header not in text:
        raise SystemExit("C12 narrow fix: interim broad classifier header not found")
    text = text.replace(broad_header, original_header, 1)
    broad_loop = '''    for pattern in CURRENT_IDENTITY_CUES:\n        if re.search(pattern, text, re.IGNORECASE):\n            return CLASS_CURRENT, f"explicit current-candidate identity cue {pattern}"\n'''
    if broad_loop not in text:
        raise SystemExit("C12 narrow fix: interim broad classifier loop not found")
    text = text.replace(broad_loop, "", 1)
    stale.write_text(text)

    # IR-C11-02 / N5-N6: a regex character class is not a numeric round
    # range. C[1-11] matches one character after C, so C8/C9/C10/C11 are
    # not represented correctly. Derive an explicit longest-first alternation.
    validator = root / "scripts/validate_api02.py"
    text = validator.read_text()
    old = '''_EARLIER_ROUNDS: Final[str] = (\n    f"C[1-{int(CANDIDATE_ROLE[1:]) - 1}]" if CANDIDATE_ROLE[1:].isdigit() else "C[1-6]"\n)\n'''
    new = '''_EARLIER_ROUNDS: Final[str] = (\n    "(?:"\n    + "|".join(\n        f"C{index}"\n        for index in range(int(CANDIDATE_ROLE[1:]) - 1, 0, -1)\n    )\n    + ")"\n    if CANDIDATE_ROLE[1:].isdigit()\n    else r"C(?!)"\n)\n'''
    if old not in text:
        raise SystemExit("C12 narrow fix: C11 _EARLIER_ROUNDS block not found")
    validator.write_text(text.replace(old, new, 1))

    report = root / "docs/api/API-02/API02_C11_TO_C12_CORRECTION_REPORT.md"
    if report.exists():
        r = report.read_text()
        r = r.replace(
            "C12 makes explicit current-candidate identity cues CURRENT before historical-cue evaluation, orders past-round alternatives longest-first, and regenerates the current-facing dossier identity.",
            "C12 replaces the invalid numeric character-class construction for earlier rounds with a dynamically derived longest-first alternation (`C11|C10|...|C1` for C12), retains the stale-audit historical classifier, and regenerates the current-facing dossier identity.",
        )
        report.write_text(r)

    print("API02_C12_NARROW_FIX:PASS")


if __name__ == "__main__":
    main()
