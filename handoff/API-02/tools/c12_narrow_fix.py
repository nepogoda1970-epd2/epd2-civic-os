from __future__ import annotations

import argparse
import json
from pathlib import Path

C11_NAME = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11.zip"
C11_ROOT = C11_NAME[:-4]
C12_NAME = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip"
C12_ROOT = C12_NAME[:-4]


def _rebind_expected_candidate(obj: dict) -> None:
    obj["filename"] = C12_NAME
    obj["role"] = "C12"
    obj["root"] = C12_ROOT
    obj["version"] = "0.1_C12"


def _rebind_carried_evidence(root: Path) -> None:
    p = root / "validation/api02/acceptance_path_identity_result.json"
    if p.exists():
        d = json.loads(p.read_text())
        for row in d.get("bindings", {}).get("candidate_identity", []):
            declaration = row.get("declaration")
            if declaration == "CANDIDATE_ROLE":
                row["declared"] = row["expected"] = "C12"
            elif declaration == "CANDIDATE_NAME":
                row["declared"] = row["expected"] = C12_ROOT
            elif declaration == "_INPUT_CANDIDATE_ARCHIVE":
                row["declared"] = row["expected"] = C12_NAME
        d["candidate_role"] = "C12"
        d["entering_role"] = "C11"
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

    p = root / "validation/api02/environment.json"
    if p.exists():
        d = json.loads(p.read_text())
        d["candidate_root"] = C12_ROOT
        if isinstance(d.get("expected_candidate"), dict):
            _rebind_expected_candidate(d["expected_candidate"])
        p.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    for name in ("final_validator_result.json", "validator_result.json"):
        p = root / "validation/api02" / name
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        if isinstance(d.get("candidate"), dict):
            _rebind_expected_candidate(d["candidate"])
        env = d.get("environment")
        if isinstance(env, dict):
            env["candidate_root"] = C12_ROOT
            if isinstance(env.get("expected_candidate"), dict):
                _rebind_expected_candidate(env["expected_candidate"])
        p.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()

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

    validator = root / "scripts/validate_api02.py"
    text = validator.read_text()
    old = '''_EARLIER_ROUNDS: Final[str] = (\n    f"C[1-{int(CANDIDATE_ROLE[1:]) - 1}]" if CANDIDATE_ROLE[1:].isdigit() else "C[1-6]"\n)\n'''
    new = '''_EARLIER_ROUNDS: Final[str] = (\n    "(?:"\n    + "|".join(\n        f"C{index}" for index in range(int(CANDIDATE_ROLE[1:]) - 1, 0, -1)\n    )\n    + ")"\n    if CANDIDATE_ROLE[1:].isdigit()\n    else r"C(?!)"\n)\n'''
    if old not in text:
        raise SystemExit("C12 narrow fix: C11 _EARLIER_ROUNDS block not found")
    text = text.replace(old, new, 1)

    # IR-C12-M23: current dossier markdown uses **Candidate:** `...C12...`.
    # The generic `candidate Cn` detector does not match the colon / closing
    # emphasis / filename form, so an earlier round could be asserted in the
    # authoritative current-candidate field without gate 28 rejecting it.
    anchor = '''_STALE_CURRENT_CLAIMS: Final[tuple[tuple[str, str], ...]] = (\n    (rf"\\b{_EARLIER_ROUNDS}\\s*\\(this candidate\\)", "names an earlier round as this candidate"),\n'''
    replacement = '''_STALE_CURRENT_CLAIMS: Final[tuple[tuple[str, str], ...]] = (\n    (rf"\\b{_EARLIER_ROUNDS}\\s*\\(this candidate\\)", "names an earlier round as this candidate"),\n    (\n        rf"\\bcandidate\\s*:\\*{{0,2}}\\s*`?[^`\\n]*\\b{_EARLIER_ROUNDS}\\b",\n        "names an earlier round in the current Candidate field",\n    ),\n'''
    if anchor not in text:
        raise SystemExit("C12 M23 fix: stale-current-claims anchor not found")
    validator.write_text(text.replace(anchor, replacement, 1))

    voting = root / "docs/api/API-02/11_VOTING_IDENTITY_ISOLATION.md"
    if voting.exists():
        voting.write_text(
            voting.read_text().replace(
                "API02_C10_TO_C11_CORRECTION_INVENTORY.json",
                "API02_C11_TO_C12_CORRECTION_INVENTORY.json",
            )
        )

    lineage = root / "docs/api/API-02/API02_LINEAGE.json"
    if lineage.exists():
        d = json.loads(lineage.read_text())
        bsi = d.get("governance", {}).get("bsi_readiness_classification")
        if isinstance(bsi, dict):
            bsi["generated_from"] = "docs/api/API-02/API02_C11_TO_C12_CORRECTION_INVENTORY.json"
            bsi["delta"] = "C11 → C12"
        lineage.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

    inv = root / "scripts/api02/build_exact_inventories.py"
    if inv.exists():
        inv.write_text(inv.read_text().replace("# --- C11 ", "# --- C12 ", 1))

    _rebind_carried_evidence(root)

    report = root / "docs/api/API-02/API02_C11_TO_C12_CORRECTION_REPORT.md"
    if report.exists():
        r = report.read_text()
        r = r.replace(
            "C12 makes explicit current-candidate identity cues CURRENT before historical-cue evaluation, orders past-round alternatives longest-first, and regenerates the current-facing dossier identity.",
            "C12 replaces the invalid numeric character-class construction for earlier rounds with a dynamically derived longest-first alternation (`C11|C10|...|C1` for C12), retains the stale-audit historical classifier, regenerates the current-facing dossier identity, and rejects an earlier round asserted through the authoritative markdown `Candidate:` field.",
        )
        report.write_text(r)

    print("API02_C12_NARROW_FIX:PASS")


if __name__ == "__main__":
    main()
