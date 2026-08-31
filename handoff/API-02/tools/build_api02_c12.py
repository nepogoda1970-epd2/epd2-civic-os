from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import stat
import zipfile

C11_SHA = "62da62bbf3ea8a1d8352e5c39d6f2abcd5d8d8b1abc7d15d022e3e76232c0732"
C11_SIZE = 34651116
C11_FILES = 3951
C11_NAME = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11.zip"
C12_ROOT = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12"
C12_NAME = C12_ROOT + ".zip"
CLASS = "VALIDATOR_STALE_AUDIT_CORRECTION_CANDIDATE"


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_stale_audit(root: pathlib.Path) -> None:
    p = root / "scripts/api02/build_stale_audit.py"
    text = p.read_text()
    old = '''def _past_round_cue_pattern() -> str:\n    rounds = past_rounds()\n    if not rounds:\n        return r"C(?!)"\n    return r"(?:" + "|".join(re.escape(round_name) for round_name in rounds) + r")"\n'''
    new = '''def _past_round_cue_pattern() -> str:\n    rounds = sorted(past_rounds(), key=lambda value: (-len(value), value))\n    if not rounds:\n        return r"C(?!)"\n    return r"(?:" + "|".join(re.escape(round_name) for round_name in rounds) + r")"\n'''
    if old not in text:
        raise SystemExit("C12: expected C11 past-round cue builder not found")
    text = text.replace(old, new)
    old = '''def _classify_text(text: str, *, heading: str = "") -> tuple[str, str]:\n    """One classifier, used by every file kind, so the rule is one rule."""\n    if MUTATION_PAYLOAD_MARKER in text:\n'''
    new = '''CURRENT_IDENTITY_CUES: tuple[str, ...] = (\n    r"\\bthis candidate\\b",\n    r"\\bcurrent candidate\\b",\n    r"\\*\\*Candidate:\\*\\*",\n    r"\\*\\*Role:\\*\\*",\n)\n\n\ndef _classify_text(text: str, *, heading: str = "") -> tuple[str, str]:\n    """Classify one current-state context.\n\n    An explicit claim about this/current candidate is CURRENT by definition.\n    It cannot be downgraded to HISTORICAL because the same block also names\n    an entering predecessor or contains a past-round cue. N5/N6 enforce this.\n    """\n    if MUTATION_PAYLOAD_MARKER in text:\n'''
    if old not in text:
        raise SystemExit("C12: expected C11 classifier header not found")
    text = text.replace(old, new)
    anchor = '''    if DURABLE_NAME_MARKER in text:\n        return (\n            CLASS_FALSE_POSITIVE,\n            "line marked as a durable name (a schema field, group label or worked example)",\n        )\n'''
    insert = anchor + '''    for pattern in CURRENT_IDENTITY_CUES:\n        if re.search(pattern, text, re.IGNORECASE):\n            return CLASS_CURRENT, f"explicit current-candidate identity cue {pattern}"\n'''
    if anchor not in text:
        raise SystemExit("C12: durable-name classifier anchor not found")
    p.write_text(text.replace(anchor, insert))


def patch_tree(root: pathlib.Path) -> None:
    lg = root / "scripts/api02/lineage_gates.py"
    text = lg.read_text()
    text = text.replace('CANDIDATE_ROLE = "C11"', 'CANDIDATE_ROLE = "C12"')
    text = text.replace(
        'CANDIDATE_CLASSIFICATION = "ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE"',
        f'CANDIDATE_CLASSIFICATION = "{CLASS}"',
    )
    text = text.replace('ENTERING_ROLE = "C10"', 'ENTERING_ROLE = "C11"')
    text = text.replace(
        '"sha256": "479e17323422f20e0badec5256ced45c48392e8a103698d9a32d37324e393eeb",\n    "size": 34652031,\n    "files": 3950,',
        f'"sha256": "{C11_SHA}",\n    "size": {C11_SIZE},\n    "files": {C11_FILES},',
    )
    text = text.replace(
        '"internal_review_findings": ("IR-C10-01",),',
        '"internal_review_findings": ("IR-C11-01", "IR-C11-02"),',
    )
    historical = '    f"{DOSSIER}/API02_C9_TO_C10_CORRECTION_REPORT.md",\n'
    if "API02_C10_TO_C11_CORRECTION_REPORT.md" not in text[text.index("HISTORICAL_DOCUMENTS"):text.index("HISTORICAL_BANNER")]:
        text = text.replace(historical, historical + '    f"{DOSSIER}/API02_C10_TO_C11_CORRECTION_REPORT.md",\n')
    lg.write_text(text)

    wf = root / ".github/workflows/api02-accept.yml"
    text = wf.read_text()
    pairs = {
        "authoritative acceptance workflow (C11)": "authoritative acceptance workflow (C12)",
        "CANDIDATE_ROLE: C11": "CANDIDATE_ROLE: C12",
        "CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11": "CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12",
        "ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10.zip": "ENTERING_CANDIDATE_NAME: " + C11_NAME,
        "ENTERING_CANDIDATE_SHA256: 479e17323422f20e0badec5256ced45c48392e8a103698d9a32d37324e393eeb": "ENTERING_CANDIDATE_SHA256: " + C11_SHA,
        "tmp/api02-c11-canonical-accept": "tmp/api02-c12-canonical-accept",
        "handoff/API-02/C11_ACCEPTANCE_INPUTS.env": "handoff/API-02/C12_ACCEPTANCE_INPUTS.env",
        "api02-c11-acceptance-evidence": "api02-c12-acceptance-evidence",
        "#   candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11.zip": "#   candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip",
        "…API02…CANDIDATE_0.1_C10.zip  479e1732…": "…API02…CANDIDATE_0.1_C11.zip  62da62bb…",
        "expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11.zip": "expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip",
    }
    for old, new in pairs.items():
        text = text.replace(old, new)
    wf.write_text(text)

    lineage = root / "docs/api/API-02/API02_LINEAGE.json"
    data = json.loads(lineage.read_text())
    data["candidate"].update({
        "role": "C12", "version": "0.1_C12", "filename": C12_NAME,
        "root": C12_ROOT, "classification": CLASS,
    })
    data["entering_baseline"].update({
        "role": "C11", "version": "0.1_C11", "filename": C11_NAME,
        "root": C11_NAME[:-4], "sha256": C11_SHA, "size": C11_SIZE,
        "files": C11_FILES, "status": "CORRECTED_BY_THIS_CANDIDATE / NOT ACCEPTED",
        "internal_review_findings": ["IR-C11-01", "IR-C11-02"],
    })
    data["sealed_accounting"]["layer_a"] = "docs/api/API-02/API02_API01C5_TO_C12_EXACT_INVENTORY.json"
    data["sealed_accounting"]["correction_record"] = "docs/api/API-02/API02_C11_TO_C12_CORRECTION_INVENTORY.json"
    raw = json.dumps(data, ensure_ascii=False)
    raw = raw.replace("API02_API01C5_TO_C11_EXACT_INVENTORY.json", "API02_API01C5_TO_C12_EXACT_INVENTORY.json")
    raw = raw.replace("API02_C10_TO_C11_CORRECTION_INVENTORY.json", "API02_C11_TO_C12_CORRECTION_INVENTORY.json")
    lineage.write_text(json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n")

    dossier = root / "docs/api/API-02"
    (dossier / "01_EXECUTIVE_RESULT.md").write_text(f'''# API-02 — Authentication & Authorization Runtime — Executive Result (C12)\n\n**Candidate:** `{C12_NAME}` (cumulative, one root)  \n**Role:** C12 — `{CLASS}`.  \n**Entering baseline:** exact C11 candidate `{C11_NAME}`, SHA-256 `{C11_SHA}`, {C11_SIZE:,} bytes, {C11_FILES} sealed checksum rows. C11 was not accepted.  \n**Sole acceptance predecessor:** API-01 C5. DATA-06 remains the inherited accepted data anchor.\n\n## What C12 corrects\n\nAuthoritative GitHub run `33402330745` verified the exact C11 archive and all required external anchors, then rejected C11 in the full validator. The remaining defects were verification-layer defects: `build_stale_audit.py` was not in frozen formatter form, and N5/N6 showed that explicit current-candidate claims could be misclassified as historical. The carried executive result also still described C8 as current.\n\nC12 formats and hardens the stale-state audit, regenerates current candidate identity, and keeps all authentication, authorization, identity, voting-boundary, persistence, route, cryptographic, API, service and frontend runtime semantics unchanged. The C11 → C12 correction inventory must prove zero runtime delta.\n\nC12 remains `CANDIDATE_NOT_ACCEPTED` until an independent authoritative run on these exact sealed bytes returns `API02_RESULT:PASS:validation/api02/validator_result.json`.\n\nNOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT SECURITY CERTIFIED.\n''')
    (dossier / "03_ENTERING_BASELINE.md").write_text(f'''# 03 — Entering Baseline (C12)\n\nC12 is a correction round. API-01 C5 remains the sole accepted API predecessor; DATA-06 remains the inherited accepted data anchor. The entering baseline of this correction round is the exact rejected C11 archive `{C11_NAME}`, SHA-256 `{C11_SHA}`, {C11_SIZE:,} bytes and {C11_FILES} sealed checksum rows. C11 is not an acceptance predecessor.\n\nThe C11 → C12 correction inventory is `API02_C11_TO_C12_CORRECTION_INVENTORY.json`. All external archives are verified by exact filename and SHA-256 before use. C12 must independently pass the complete governed acceptance workflow on its own exact sealed ZIP before API-02 can be recorded as accepted or closed.\n''')

    old_report = dossier / "API02_C10_TO_C11_CORRECTION_REPORT.md"
    if old_report.exists():
        lines = old_report.read_text().splitlines()
        if "HISTORICAL" not in lines[0]:
            lines[0] += " — HISTORICAL"
        if "**HISTORICAL.**" not in "\n".join(lines[:12]):
            lines.insert(2, "**HISTORICAL.** C11 was not accepted; C12 supersedes it as the current correction candidate.")
        old_report.write_text("\n".join(lines) + "\n")
    (dossier / "API02_C11_TO_C12_CORRECTION_REPORT.md").write_text(f'''# API-02 C11 → C12 correction report\n\n**Candidate:** C12 — `{CLASS}`  \n**Entering baseline:** exact C11 archive, SHA-256 `{C11_SHA}`, {C11_SIZE:,} bytes.\n\n## IR-C11-01 — frozen formatter regression\n\nAuthoritative run `33402330745` rejected gate 17 because `scripts/api02/build_stale_audit.py` was not in the frozen formatter's canonical form. C12 formats that file with the frozen toolchain before sealing.\n\n## IR-C11-02 — current-identity stale-audit classification\n\nThe same run rejected validator self-test fixtures N5 and N6. C12 makes explicit current-candidate identity cues CURRENT before historical-cue evaluation, orders past-round alternatives longest-first, and regenerates the current-facing dossier identity.\n\nNo runtime semantics change. C12 is not accepted until its exact sealed bytes receive the independent authoritative terminal PASS.\n''')

    ap = root / "scripts/api02/acceptance_path_identity.py"
    ap.write_text(ap.read_text().replace("form `…_0.1_C11`", "form `…_0.1_C12`"))
    patch_stale_audit(root)

    # Advance only machine current-identity fields carried from C11.
    for p in (root / "validation/api02").glob("*.json"):
        try:
            value = json.loads(p.read_text())
        except Exception:
            continue
        raw = json.dumps(value, ensure_ascii=False)
        raw = raw.replace('"candidate": "C11"', '"candidate": "C12"')
        raw = raw.replace('"candidate_role": "C11"', '"candidate_role": "C12"')
        raw = raw.replace('"candidate_classification": "ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE"', f'"candidate_classification": "{CLASS}"')
        raw = raw.replace('"entering_role": "C10"', '"entering_role": "C11"')
        raw = raw.replace("API02_API01C5_TO_C11_EXACT_INVENTORY.json", "API02_API01C5_TO_C12_EXACT_INVENTORY.json")
        raw = raw.replace("API02_C10_TO_C11_CORRECTION_INVENTORY.json", "API02_C11_TO_C12_CORRECTION_INVENTORY.json")
        p.write_text(json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    for rel in (
        "SHA256SUMS.txt",
        "docs/api/API-02/API02_API01C5_TO_C11_EXACT_INVENTORY.json",
        "docs/api/API-02/API02_C10_TO_C11_CORRECTION_INVENTORY.json",
        "docs/api/API-02/API02_SEALED_FILE_MANIFEST.json",
        "docs/api/API-02/API02_STALE_STATE_AUDIT.json",
        "validation/api02/evidence_consistency_result.json",
    ):
        p = root / rel
        if p.exists():
            p.unlink()
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def package(root: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    target = out / C12_NAME
    files = sorted((p.relative_to(root).as_posix(), p) for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, strict_timestamps=True) as archive:
        for rel, path in files:
            info = zipfile.ZipInfo(C12_ROOT + "/" + rel, (2026, 8, 31, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = stat.S_IMODE(path.stat().st_mode) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--patch-only", action="store_true")
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.patch_only:
        patch_tree(root)
        print("API02_C12_PATCH:PASS")
        return
    if args.package_only:
        candidate = package(root, out)
        digest = sha(candidate)
        size = candidate.stat().st_size
        (out / "candidate_sha256.txt").write_text(f"{digest}  {candidate.name}\n")
        (out / "candidate_meta.json").write_text(json.dumps({"candidate": "C12", "filename": candidate.name, "sha256": digest, "size": size, "root": C12_ROOT}, indent=2) + "\n")
        print(size, digest)
        return
    raise SystemExit("choose --patch-only or --package-only")


if __name__ == "__main__":
    main()
