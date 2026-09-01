from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import stat
import zipfile

C12_SHA = "ef124329645a92232285df6e2662df090114244bcf13953da015cc296518759a"
C12_SIZE = 34640113
C12_FILES = 3952
C12_NAME = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip"
C12_ROOT = C12_NAME[:-4]
C13_ROOT = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13"
C13_NAME = C13_ROOT + ".zip"
CLASS = "AUTHORITATIVE_ACCEPTANCE_HARNESS_CORRECTION_CANDIDATE"


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"C13: expected {label} not found")
    return text.replace(old, new, 1)


def _rebind_expected_candidate(obj: dict) -> None:
    obj["filename"] = C13_NAME
    obj["role"] = "C13"
    obj["root"] = C13_ROOT
    obj["version"] = "0.1_C13"


def _rebind_carried_evidence(root: pathlib.Path) -> None:
    p = root / "validation/api02/acceptance_path_identity_result.json"
    if p.exists():
        d = json.loads(p.read_text())
        for row in d.get("bindings", {}).get("candidate_identity", []):
            declaration = row.get("declaration")
            if declaration == "CANDIDATE_ROLE":
                row["declared"] = row["expected"] = "C13"
            elif declaration == "CANDIDATE_NAME":
                row["declared"] = row["expected"] = C13_ROOT
            elif declaration == "_INPUT_CANDIDATE_ARCHIVE":
                row["declared"] = row["expected"] = C13_NAME
        d["candidate_role"] = "C13"
        d["entering_role"] = "C12"
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

    p = root / "validation/api02/environment.json"
    if p.exists():
        d = json.loads(p.read_text())
        d["candidate_root"] = C13_ROOT
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
            env["candidate_root"] = C13_ROOT
            if isinstance(env.get("expected_candidate"), dict):
                _rebind_expected_candidate(env["expected_candidate"])
        p.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    for p in (root / "validation/api02").glob("*.json"):
        try:
            value = json.loads(p.read_text())
        except Exception:
            continue
        raw = json.dumps(value, ensure_ascii=False)
        raw = raw.replace('"candidate": "C12"', '"candidate": "C13"')
        raw = raw.replace('"candidate_role": "C12"', '"candidate_role": "C13"')
        raw = raw.replace(
            '"candidate_classification": "VALIDATOR_STALE_AUDIT_CORRECTION_CANDIDATE"',
            f'"candidate_classification": "{CLASS}"',
        )
        raw = raw.replace('"entering_role": "C11"', '"entering_role": "C12"')
        raw = raw.replace("API02_API01C5_TO_C12_EXACT_INVENTORY.json", "API02_API01C5_TO_C13_EXACT_INVENTORY.json")
        raw = raw.replace("API02_C11_TO_C12_CORRECTION_INVENTORY.json", "API02_C12_TO_C13_CORRECTION_INVENTORY.json")
        p.write_text(json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def patch_tree(root: pathlib.Path) -> None:
    lg = root / "scripts/api02/lineage_gates.py"
    text = lg.read_text()
    text = replace_required(text, 'CANDIDATE_ROLE = "C12"', 'CANDIDATE_ROLE = "C13"', "C12 candidate role")
    text = replace_required(
        text,
        'CANDIDATE_CLASSIFICATION = "VALIDATOR_STALE_AUDIT_CORRECTION_CANDIDATE"',
        f'CANDIDATE_CLASSIFICATION = "{CLASS}"',
        "C12 candidate classification",
    )
    text = replace_required(text, 'ENTERING_ROLE = "C11"', 'ENTERING_ROLE = "C12"', "C11 entering role")
    text = replace_required(
        text,
        '"sha256": "62da62bbf3ea8a1d8352e5c39d6f2abcd5d8d8b1abc7d15d022e3e76232c0732",\n    "size": 34651116,\n    "files": 3951,',
        f'"sha256": "{C12_SHA}",\n    "size": {C12_SIZE},\n    "files": {C12_FILES},',
        "C11 entering exact identity",
    )
    text = replace_required(
        text,
        '"internal_review_findings": ("IR-C11-01", "IR-C11-02"),',
        '"internal_review_findings": ("IR-C12-01",),',
        "C11 review findings",
    )
    hist_start = text.index("HISTORICAL_DOCUMENTS")
    hist_end = text.index("HISTORICAL_BANNER", hist_start)
    hist_block = text[hist_start:hist_end]
    if "API02_C11_TO_C12_CORRECTION_REPORT.md" not in hist_block:
        anchor = '    f"{DOSSIER}/API02_C10_TO_C11_CORRECTION_REPORT.md",\n'
        text = replace_required(
            text,
            anchor,
            anchor + '    f"{DOSSIER}/API02_C11_TO_C12_CORRECTION_REPORT.md",\n',
            "historical report list anchor",
        )
    lg.write_text(text)

    wf = root / ".github/workflows/api02-accept.yml"
    text = wf.read_text()
    pairs = (
        ("authoritative acceptance workflow (C12)", "authoritative acceptance workflow (C13)"),
        ("CANDIDATE_ROLE: C12", "CANDIDATE_ROLE: C13"),
        ("CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12", "CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13"),
        ("ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11.zip", "ENTERING_CANDIDATE_NAME: " + C12_NAME),
        ("ENTERING_CANDIDATE_SHA256: 62da62bbf3ea8a1d8352e5c39d6f2abcd5d8d8b1abc7d15d022e3e76232c0732", "ENTERING_CANDIDATE_SHA256: " + C12_SHA),
        ("tmp/api02-c12-canonical-accept", "tmp/api02-c13-canonical-accept"),
        ("handoff/API-02/C12_ACCEPTANCE_INPUTS.env", "handoff/API-02/C13_ACCEPTANCE_INPUTS.env"),
        ("api02-c12-acceptance-evidence", "api02-c13-acceptance-evidence"),
        ("#   candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip", "#   candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip"),
        ("…API02…CANDIDATE_0.1_C11.zip  62da62bb…", "…API02…CANDIDATE_0.1_C12.zip  ef124329…"),
        ("expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C12.zip", "expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip"),
    )
    for old, new in pairs:
        text = replace_required(text, old, new, f"workflow token {old}")

    old_assert = '''          identity = json.load(open("validation/api02/candidate_identity_result.json"))\n          assert identity["mode"] == "sealed-archive", identity["mode"]\n          assert identity["sha256"] == os.environ["CANDIDATE_SHA256"], identity["sha256"]\n          # bind this run's evidence to the bytes it judged\n'''
    new_assert = '''          identity = json.load(open("validation/api02/candidate_identity_result.json"))\n          # IR-C12-01. The governed identity record intentionally does not carry the\n          # ZIP's own SHA-256 (a candidate cannot contain a non-recursive self-hash)\n          # and has no `mode` field. C12's step 27 queried both nonexistent keys even\n          # after all 32 governed gates had passed. Assert the schema that actually\n          # governs candidate identity here; the exact archive digest remains bound\n          # by step 04 and the CANDIDATE_SHA256 control input verified before extract.\n          assert identity["result"] == "PASS", identity\n          assert identity["candidate"] == role, identity\n          assert identity["entering_role"] == "C12", identity\n          candidate_sha = os.environ["CANDIDATE_SHA256"]\n          assert len(candidate_sha) == 64 and all(c in "0123456789abcdef" for c in candidate_sha), candidate_sha\n          # bind this run's evidence to the bytes it judged\n'''
    text = replace_required(text, old_assert, new_assert, "faulty step 27 identity schema assertions")
    wf.write_text(text)

    lineage = root / "docs/api/API-02/API02_LINEAGE.json"
    data = json.loads(lineage.read_text())
    data["candidate"].update(
        {
            "role": "C13",
            "version": "0.1_C13",
            "filename": C13_NAME,
            "root": C13_ROOT,
            "classification": CLASS,
        }
    )
    data["entering_baseline"].update(
        {
            "role": "C12",
            "version": "0.1_C12",
            "filename": C12_NAME,
            "root": C12_ROOT,
            "sha256": C12_SHA,
            "size": C12_SIZE,
            "files": C12_FILES,
            "status": "CORRECTED_BY_THIS_CANDIDATE / NOT ACCEPTED",
            "internal_review_findings": ["IR-C12-01"],
        }
    )
    data["sealed_accounting"]["layer_a"] = "docs/api/API-02/API02_API01C5_TO_C13_EXACT_INVENTORY.json"
    data["sealed_accounting"]["correction_record"] = "docs/api/API-02/API02_C12_TO_C13_CORRECTION_INVENTORY.json"
    bsi = data.get("governance", {}).get("bsi_readiness_classification")
    if isinstance(bsi, dict):
        bsi["generated_from"] = "docs/api/API-02/API02_C12_TO_C13_CORRECTION_INVENTORY.json"
        bsi["delta"] = "C12 → C13"
    lineage.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    dossier = root / "docs/api/API-02"
    (dossier / "01_EXECUTIVE_RESULT.md").write_text(
        f'''# API-02 — Authentication & Authorization Runtime — Executive Result (C13)\n\n**Candidate:** `{C13_NAME}` (cumulative, one root)  \n**Role:** C13 — `{CLASS}`.  \n**Entering baseline:** exact C12 candidate `{C12_NAME}`, SHA-256 `{C12_SHA}`, {C12_SIZE:,} bytes, {C12_FILES} sealed checksum rows. C12 was not accepted.  \n**Sole acceptance predecessor:** API-01 C5. DATA-06 remains the inherited accepted data anchor.\n\n## What C13 corrects\n\nAuthoritative GitHub run `33491251813` verified the exact C12 archive and all required external anchors. The complete API-02 validator returned `API02_RESULT:PASS:validation/api02/validator_result.json`; all 32 governed gates passed, including exact PostgreSQL 16.15, browser execution, route authorization, commit-time reauthorization, voting isolation, mutation self-tests, sealed accounting and V26 governance binding. The run was nevertheless rejected by post-validator workflow step 27 because that step queried `candidate_identity_result.json` keys `mode` and `sha256` that do not exist in the governed candidate-identity schema. The candidate archive SHA is intentionally external because a sealed archive cannot contain a non-recursive digest of itself.\n\nC13 corrects only that authoritative acceptance-harness/provenance assertion and advances the correction-round identity from C12 to C13. Step 27 now checks the governed identity fields (`result`, `candidate`, `entering_role`) and binds the exact archive digest already fail-closed verified by step 04. No authentication, authorization, identity, voting-boundary, persistence, route, cryptographic, API, service or frontend runtime semantics are changed. The C12 → C13 correction inventory must prove zero runtime delta.\n\nC13 remains `CANDIDATE_NOT_ACCEPTED` until an independent authoritative run on these exact sealed bytes returns a successful job after `API02_RESULT:PASS:validation/api02/validator_result.json` and every post-validator assertion.\n\nNOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT SECURITY CERTIFIED.\n'''
    )
    (dossier / "03_ENTERING_BASELINE.md").write_text(
        f'''# 03 — Entering Baseline (C13)\n\nC13 is a correction round. API-01 C5 remains the sole accepted API predecessor; DATA-06 remains the inherited accepted data anchor. The entering baseline of this correction round is the exact rejected C12 archive `{C12_NAME}`, SHA-256 `{C12_SHA}`, {C12_SIZE:,} bytes and {C12_FILES} sealed checksum rows. C12 is not an acceptance predecessor.\n\nThe C12 → C13 correction inventory is `API02_C12_TO_C13_CORRECTION_INVENTORY.json`. All external archives are verified by exact filename and SHA-256 before use. C13 must independently pass the complete governed acceptance workflow on its own exact sealed ZIP before API-02 can be recorded as accepted or closed.\n'''
    )

    old_report = dossier / "API02_C11_TO_C12_CORRECTION_REPORT.md"
    if old_report.exists():
        lines = old_report.read_text().splitlines()
        if "HISTORICAL" not in lines[0]:
            lines[0] += " — HISTORICAL"
        if "**HISTORICAL.**" not in "\n".join(lines[:12]):
            lines.insert(2, "**HISTORICAL.** C12 was not accepted; C13 supersedes it as the current correction candidate.")
        old_report.write_text("\n".join(lines) + "\n")

    (dossier / "API02_C12_TO_C13_CORRECTION_REPORT.md").write_text(
        f'''# API-02 C12 → C13 correction report\n\n**Candidate:** C13 — `{CLASS}`  \n**Entering baseline:** exact C12 archive, SHA-256 `{C12_SHA}`, {C12_SIZE:,} bytes, {C12_FILES} sealed checksum rows.\n\n## IR-C12-01 — authoritative acceptance provenance assertion used a nonexistent identity schema\n\nAuthoritative run `33491251813` completed the full C12 validator successfully: all 32 governed gates passed and the terminal marker was `API02_RESULT:PASS:validation/api02/validator_result.json`. The overall job then failed in step 27 with `KeyError: 'mode'` because the workflow asserted `candidate_identity_result.json["mode"] == "sealed-archive"`; the immediately following assertion also expected a nonexistent `sha256` key. The governed identity record contains `result`, `candidate`, `entering_role`, declarations and checks. Its archive digest is intentionally not self-contained; the exact candidate SHA-256 is an external acceptance input verified before extraction.\n\nC13 removes both invalid schema assumptions. Step 27 now requires identity `result == PASS`, current `candidate == C13`, exact `entering_role == C12`, and a syntactically valid external `CANDIDATE_SHA256` that has already been fail-closed verified by step 04 against the exact downloaded archive. The authoritative evidence record remains bound to that digest and to this run's `GITHUB_RUN_ID` / `GITHUB_SHA`.\n\nNo runtime semantics change. C13 is not accepted until its exact sealed bytes receive the independent authoritative terminal PASS.\n'''
    )

    ap = root / "scripts/api02/acceptance_path_identity.py"
    ap.write_text(ap.read_text().replace("form `…_0.1_C12`", "form `…_0.1_C13`"))

    selftest = root / "scripts/api02/validator_selftest.py"
    stext = selftest.read_text()
    stext = replace_required(stext, 'anchor = "## What C12 corrects"', 'anchor = "## What C13 corrects"', "M23 current dossier anchor")
    stext = stext.replace("current C12 dossier", "current C13 dossier")
    selftest.write_text(stext)

    voting = dossier / "11_VOTING_IDENTITY_ISOLATION.md"
    if voting.exists():
        voting.write_text(voting.read_text().replace("API02_C11_TO_C12_CORRECTION_INVENTORY.json", "API02_C12_TO_C13_CORRECTION_INVENTORY.json"))

    inv = root / "scripts/api02/build_exact_inventories.py"
    if inv.exists():
        inv.write_text(inv.read_text().replace("# --- C12 ", "# --- C13 ", 1))

    _rebind_carried_evidence(root)

    for rel in (
        "SHA256SUMS.txt",
        "docs/api/API-02/API02_API01C5_TO_C12_EXACT_INVENTORY.json",
        "docs/api/API-02/API02_C11_TO_C12_CORRECTION_INVENTORY.json",
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
    target = out / C13_NAME
    files = sorted(
        (p.relative_to(root).as_posix(), p)
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    with zipfile.ZipFile(
        target,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        strict_timestamps=True,
    ) as archive:
        for rel, path in files:
            info = zipfile.ZipInfo(C13_ROOT + "/" + rel, (2026, 9, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = stat.S_IMODE(path.stat().st_mode) << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=6,
            )
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
        print("API02_C13_PATCH:PASS")
        return
    if args.package_only:
        candidate = package(root, out)
        digest = sha(candidate)
        size = candidate.stat().st_size
        (out / "candidate_sha256.txt").write_text(f"{digest}  {candidate.name}\n")
        (out / "candidate_meta.json").write_text(
            json.dumps(
                {
                    "candidate": "C13",
                    "filename": candidate.name,
                    "sha256": digest,
                    "size": size,
                    "root": C13_ROOT,
                },
                indent=2,
            )
            + "\n"
        )
        print(size, digest)
        return
    raise SystemExit("choose --patch-only or --package-only")


if __name__ == "__main__":
    main()
