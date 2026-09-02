from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_MAIN = "217559b7f21c338d6fe8d4e4676082cd3840251c"
ACCEPTANCE_RUN_ID = 33618683269
CANDIDATE_FILE = "EPD2_CTRL01_GOVERNED_CONTROL_PLANE_CANDIDATE_0.1_C1.zip"
CANDIDATE_SHA256 = "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
CANDIDATE_SIZE = 190099
P1_SHA256 = "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
WORKFLOW_COMMIT = "246824a099fd1e7359e79650a7107d7cfa8ddb43"
BUILD_JOB_ID = 100210392348
AUTHORITATIVE_JOB_ID = 100210596079
CANDIDATE_ARTIFACT_ID = 9842006799
BUILD_EVIDENCE_ARTIFACT_ID = 9842007526
AUTHORITATIVE_EVIDENCE_ARTIFACT_ID = 9842027832
AUTHORITATIVE_EVIDENCE_ARTIFACT_SHA256 = "4f4454f9cbdf17059882136ee7588e470e61458636795885adb8c74c03ae82ef"
ROOT_NAME = "EPD2_CTRL01_GOVERNED_CONTROL_PLANE_CANDIDATE_0.1_C1"
PAYLOAD_TOP_LEVEL = ("docs", "scripts", "services", "validation")
TEMP_ALLOWED = {
    ".github/workflows/ctrl01-c1-promote-canonical.yml",
    ".github/workflows/pilot-roadmap-guard.yml",
    "scripts/ctrl01_canonical_promote.py",
}


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(args, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(message)


def safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts:
            fail(f"unsafe archive member: {name}")
        mode = info.external_attr >> 16
        if mode & 0o170000 == 0o120000:
            fail(f"symlink archive member refused: {name}")
        target = (destination / name).resolve()
        if root != target and root not in target.parents:
            fail(f"archive escape refused: {name}")
    zf.extractall(destination)


def verify_internal_seal(candidate_root: Path) -> None:
    sums = candidate_root / "SHA256SUMS.txt"
    if not sums.is_file():
        fail("candidate SHA256SUMS.txt missing")
    seen: set[str] = set()
    for raw in sums.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, rel = raw.split(maxsplit=1)
        rel = rel.lstrip(" *")
        path = candidate_root / rel
        if not path.is_file():
            fail(f"sealed file missing: {rel}")
        actual = sha256_file(path)
        if actual != digest:
            fail(f"sealed hash mismatch: {rel}: {actual} != {digest}")
        seen.add(rel)
    if not seen:
        fail("empty SHA256SUMS.txt")


def locate_single(directory: Path, name: str) -> Path:
    matches = list(directory.rglob(name))
    if len(matches) != 1:
        fail(f"expected exactly one {name}, found {len(matches)}")
    return matches[0]


def verify_acceptance_basis(candidate_root: Path, evidence_path: Path) -> dict[str, object]:
    identity = json.loads((candidate_root / "candidate_identity.json").read_text(encoding="utf-8"))
    assert identity["self_state"] == "CANDIDATE_NOT_ACCEPTED", identity
    assert identity["base_main_commit"] == BASE_MAIN, identity
    assert identity["api06_state"] == "NEXT / NOT ACCEPTED", identity
    assert identity["system_trial_preview"] == "CHECKPOINT_NOT_OPEN", identity
    assert identity["ctrl_layer_state"] == "OPEN / NOT CLOSED", identity

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["conclusion"] == "PASS", evidence
    assert evidence["candidate_sha256"] == CANDIDATE_SHA256, evidence
    assert evidence["candidate_size"] == CANDIDATE_SIZE, evidence
    assert evidence["base_main"] == BASE_MAIN, evidence
    assert evidence["run_id"] == ACCEPTANCE_RUN_ID, evidence
    assert evidence["job"] == "authoritative-review", evidence
    assert evidence["gates"] == "22/22 PASS", evidence
    assert evidence["mutations"] == "37/37 DETECTED", evidence
    assert evidence["self_acceptance"] is False, evidence
    assert set(evidence["unreconciled_dependencies"]) == {"API-06"}, evidence
    assert evidence["system_trial_preview"] == "CHECKPOINT_NOT_OPEN / API-06 BLOCKED", evidence
    assert evidence["ctrl_layer_state"] == "OPEN / NOT CLOSED", evidence
    marker = f"CTRL01_C1_AUTHORITATIVE_RESULT:PASS:{CANDIDATE_SHA256}:{CANDIDATE_SIZE}"
    assert evidence["terminal_marker"] == marker, evidence
    return evidence


def assert_pre_promotion_drift(repo: Path) -> str:
    run("git", "fetch", "origin", "main")
    trigger = run("git", "rev-parse", "HEAD", capture=True)
    origin = run("git", "rev-parse", "origin/main", capture=True)
    if trigger != origin:
        fail(f"main moved during promotion setup: HEAD={trigger}, origin/main={origin}")
    run("git", "merge-base", "--is-ancestor", BASE_MAIN, "HEAD")
    changed = run("git", "diff", "--name-only", f"{BASE_MAIN}..HEAD", capture=True).splitlines()
    unexpected = sorted(set(changed) - TEMP_ALLOWED)
    if unexpected:
        fail("unexpected canonical drift before promotion: " + ", ".join(unexpected))
    return trigger


def install_payload(repo: Path, candidate_root: Path) -> dict[str, str]:
    installed: dict[str, str] = {}
    for top in PAYLOAD_TOP_LEVEL:
        source_top = candidate_root / top
        if not source_top.exists():
            continue
        for source in sorted(p for p in source_top.rglob("*") if p.is_file()):
            rel = source.relative_to(candidate_root)
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            digest = sha256_file(source)
            if sha256_file(target) != digest:
                fail(f"installed byte mismatch: {rel}")
            installed[rel.as_posix()] = digest
    if not any(path.startswith("services/control-plane-service/") for path in installed):
        fail("control-plane-service payload was not installed")
    return installed


def write_acceptance(repo: Path, evidence: dict[str, object], installed: dict[str, str], trigger: str) -> None:
    out = repo / "docs/ctrl/CTRL-01"
    out.mkdir(parents=True, exist_ok=True)

    evidence_path = out / "CTRL01_C1_AUTHORITATIVE_ACCEPTANCE_RESULT.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = {
        "schema": "epd2.ctrl01.acceptance-record/1",
        "stage": "CTRL-01 — Governed Control Plane",
        "decision": "ACCEPTED / CLOSED",
        "decision_date": "2026-09-02",
        "authority": "Project Owner",
        "scope": "BOUNDED_CTRL01_STAGE_ONLY",
        "previous_state": "NOT_STARTED / PRESEAL PARALLEL WORK NOT ACCEPTED",
        "overall_ctrl_layer": "OPEN / NOT CLOSED",
        "system_trial_preview": "CHECKPOINT_NOT_OPEN / API-06 BLOCKED",
        "candidate": {
            "file": CANDIDATE_FILE,
            "sha256": CANDIDATE_SHA256,
            "size_bytes": CANDIDATE_SIZE,
            "base_main": BASE_MAIN,
            "p1_sha256": P1_SHA256,
            "self_state_before_governance_decision": "CANDIDATE_NOT_ACCEPTED",
        },
        "authoritative_review": {
            "workflow": ".github/workflows/ctrl01-c1-canonical.yml",
            "workflow_commit": WORKFLOW_COMMIT,
            "run_id": ACCEPTANCE_RUN_ID,
            "build_job_id": BUILD_JOB_ID,
            "authoritative_job_id": AUTHORITATIVE_JOB_ID,
            "conclusion": "PASS",
            "terminal_marker": f"CTRL01_C1_AUTHORITATIVE_RESULT:PASS:{CANDIDATE_SHA256}:{CANDIDATE_SIZE}",
            "candidate_artifact": {
                "name": "ctrl01-c1-sealed-candidate-33618683269",
                "id": CANDIDATE_ARTIFACT_ID,
                "artifact_zip_sha256": "12898d5a9ad7658aefe02c0ad62be4c91328e2420e41c7c56291647afd05dbb3",
            },
            "build_evidence_artifact": {
                "name": "ctrl01-c1-build-evidence-33618683269",
                "id": BUILD_EVIDENCE_ARTIFACT_ID,
                "artifact_zip_sha256": "a722f8a2bb614a69e089d63a14a494b3466588791ba1bc018d252bdd1c3d7b7e",
            },
            "authoritative_evidence_artifact": {
                "name": "ctrl01-c1-authoritative-evidence-33618683269",
                "id": AUTHORITATIVE_EVIDENCE_ARTIFACT_ID,
                "artifact_zip_sha256": AUTHORITATIVE_EVIDENCE_ARTIFACT_SHA256,
            },
        },
        "verification": {
            "ruff": "PASS",
            "mypy": "PASS / 17 source files",
            "pytest_build": "178 passed",
            "pytest_authoritative": "178 passed",
            "governance_gates": "22/22 PASS",
            "mutations": "37/37 DETECTED",
            "commit_time_reauthorization_mutations": 43,
            "same_bytes_and_internal_sha256s": "PASS",
            "canonical_payload_installation": "EXACT SEALED C1 PAYLOAD BYTES INSTALLED",
            "self_acceptance": False,
        },
        "dependencies": {"API-06": "NEXT / NOT ACCEPTED; API layer remains open until API-06 closes"},
        "open_blockers_for_ctrl01_acceptance": [],
        "remaining_program_blockers": ["API-06 authoritative acceptance before API closure and System Trial Preview opening"],
        "master_future_register": {
            "changed": False,
            "reason": "No FIR status promotion is requested or evidenced by bounded CTRL-01 C1 acceptance.",
        },
        "nonclaims": [
            "overall CTRL layer closure",
            "System Trial Preview opening",
            "production readiness",
            "legal activation",
            "BSI/Common Criteria/EAL4 certification",
            "final security acceptance",
        ],
    }
    (out / "CTRL01_C1_ACCEPTANCE_RECORD.json").write_text(
        json.dumps(acceptance, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    disposition = {
        "schema": "epd2.ctrl01.dependency-disposition/1",
        "stage": "CTRL-01 C1",
        "decision": "BOUNDED_ACCEPTANCE_ALLOWED",
        "api06": "NEXT / NOT ACCEPTED",
        "api_layer": "OPEN",
        "system_trial_preview": "CHECKPOINT_NOT_OPEN",
        "overall_ctrl_layer": "OPEN / NOT CLOSED",
        "classification": "API-06 is not a blocker to bounded CTRL-01 C1 acceptance; it remains a blocker to API-layer closure and System Trial Preview opening.",
        "authoritative_acceptance_run": ACCEPTANCE_RUN_ID,
        "candidate_sha256": CANDIDATE_SHA256,
    }
    (out / "CTRL01_C1_DEPENDENCY_DISPOSITION.json").write_text(
        json.dumps(disposition, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    installation = {
        "schema": "epd2.ctrl01.canonical-installation-manifest/1",
        "stage": "CTRL-01 C1",
        "candidate_sha256": CANDIDATE_SHA256,
        "candidate_size": CANDIDATE_SIZE,
        "authoritative_run_id": ACCEPTANCE_RUN_ID,
        "promotion_trigger_commit": trigger,
        "installed_file_count": len(installed),
        "installed_files": installed,
        "verification": "EXACT_BYTES_MATCH_SEALED_C1",
    }
    (out / "CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json").write_text(
        json.dumps(installation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def update_pcr(repo: Path) -> None:
    p = repo / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
    text = p.read_text(encoding="utf-8")
    old = "| CTRL | `NOT_STARTED` | Control-plane specifications may be prepared; integrated closure follows OPS/INFRA. |"
    new = "| CTRL | `CTRL-01 ACCEPTED / CLOSED; CTRL LAYER OPEN` | Exact bounded CTRL-01 C1 Governed Control Plane is accepted/closed and its exact sealed payload is installed in canonical main. The overall CTRL layer remains open; API-06 remains NEXT / NOT ACCEPTED and System Trial Preview remains CHECKPOINT_NOT_OPEN. Later CTRL work and whole-layer closure remain separately governed. |"
    if text.count(old) != 1:
        fail(f"unexpected CTRL row count: {text.count(old)}")
    text = text.replace(old, new, 1)
    marker = "\n\n## 2. Program phase state"
    note = f"""

**CTRL-01 authoritative acceptance and bounded stage closure (2026-09-02):** exact sealed candidate `{CANDIDATE_FILE}`, SHA-256 `{CANDIDATE_SHA256}`, size `190,099` bytes, passed independent exact-byte GitHub Actions review in `.github/workflows/ctrl01-c1-canonical.yml`, authoritative run `{ACCEPTANCE_RUN_ID}`, build job `{BUILD_JOB_ID}`, authoritative job `{AUTHORITATIVE_JOB_ID}`, workflow commit `{WORKFLOW_COMMIT}`, conclusion `success`. The independent replay verified the complete internal SHA-256 seal, locked dependencies, Ruff, mypy, `178/178` runtime tests, all `22/22` governed CTRL gates, `37/37` mutation attacks detected, and `43` commit-time reauthorization mutations. Terminal marker: `CTRL01_C1_AUTHORITATIVE_RESULT:PASS:{CANDIDATE_SHA256}:{CANDIDATE_SIZE}`. The canonical promotion installs the exact sealed C1 payload bytes under `docs/ctrl/CTRL-01`, `scripts`, `services/control-plane-service` and `validation`, and records their hashes in `docs/ctrl/CTRL-01/CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json`. The sealed candidate correctly retained `CANDIDATE_NOT_ACCEPTED`; that no-self-acceptance state is superseded only for this bounded module by `docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json`. **CTRL-01 C1 is therefore `ACCEPTED / CLOSED` as a bounded Governed Control Plane stage.** The overall CTRL layer remains **OPEN / NOT CLOSED**. `API-06` remains `NEXT / NOT ACCEPTED`; the API layer remains open and System Trial Preview remains **CHECKPOINT_NOT_OPEN**. No production-readiness, legal-activation, BSI/Common Criteria/EAL4 or final-security claim follows.
"""
    if text.count(marker) != 1:
        fail(f"unexpected phase marker count: {text.count(marker)}")
    p.write_text(text.replace(marker, note + marker, 1), encoding="utf-8")


def final_semantic_assertions(repo: Path, installed: dict[str, str]) -> None:
    out = repo / "docs/ctrl/CTRL-01"
    a = json.loads((out / "CTRL01_C1_ACCEPTANCE_RECORD.json").read_text(encoding="utf-8"))
    r = json.loads((out / "CTRL01_C1_AUTHORITATIVE_ACCEPTANCE_RESULT.json").read_text(encoding="utf-8"))
    d = json.loads((out / "CTRL01_C1_DEPENDENCY_DISPOSITION.json").read_text(encoding="utf-8"))
    i = json.loads((out / "CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json").read_text(encoding="utf-8"))
    assert a["decision"] == "ACCEPTED / CLOSED"
    assert a["scope"] == "BOUNDED_CTRL01_STAGE_ONLY"
    assert a["overall_ctrl_layer"] == "OPEN / NOT CLOSED"
    assert a["open_blockers_for_ctrl01_acceptance"] == []
    assert a["verification"]["self_acceptance"] is False
    assert r["conclusion"] == "PASS" and r["gates"] == "22/22 PASS" and r["mutations"] == "37/37 DETECTED"
    assert d["decision"] == "BOUNDED_ACCEPTANCE_ALLOWED" and d["system_trial_preview"] == "CHECKPOINT_NOT_OPEN"
    assert i["installed_file_count"] == len(installed) and i["verification"] == "EXACT_BYTES_MATCH_SEALED_C1"
    pcr = (repo / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md").read_text(encoding="utf-8")
    assert "| CTRL | `CTRL-01 ACCEPTED / CLOSED; CTRL LAYER OPEN` |" in pcr
    assert "**CTRL-01 C1 is therefore `ACCEPTED / CLOSED` as a bounded Governed Control Plane stage.**" in pcr
    for rel, digest in installed.items():
        if sha256_file(repo / rel) != digest:
            fail(f"post-install byte drift: {rel}")
    run("git", "diff", "--check")


def restore_transport(repo: Path) -> None:
    run("git", "checkout", BASE_MAIN, "--", ".github/workflows/pilot-roadmap-guard.yml")
    for rel in (".github/workflows/ctrl01-c1-promote-canonical.yml", "scripts/ctrl01_canonical_promote.py"):
        path = repo / rel
        if path.exists():
            path.unlink()


def commit_and_push(trigger: str) -> str:
    run("git", "config", "user.name", "epd2-governance-bot")
    run("git", "config", "user.email", "epd2-governance-bot@users.noreply.github.com")
    run("git", "add", "-A")
    if subprocess.run(("git", "diff", "--cached", "--quiet")).returncode == 0:
        fail("no canonical governance delta")
    staged = run("git", "diff", "--cached", "--name-only", capture=True).splitlines()
    forbidden_temp = TEMP_ALLOWED.intersection(staged)
    if forbidden_temp:
        fail("temporary transport path would remain in final commit: " + ", ".join(sorted(forbidden_temp)))
    if "services/control-plane-service/pyproject.toml" not in staged:
        fail("control-plane-service is not staged for canonical installation")
    if "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json" not in staged:
        fail("acceptance record not staged")
    if "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md" not in staged:
        fail("PCR transition not staged")
    run("git", "commit", "-m", "governance(ctrl01): accept and install bounded CTRL-01 C1")
    run("git", "fetch", "origin", "main")
    origin = run("git", "rev-parse", "origin/main", capture=True)
    if origin != trigger:
        fail(f"canonical main moved before push: {origin} != {trigger}")
    run("git", "push", "origin", "HEAD:main")
    return run("git", "rev-parse", "HEAD", capture=True)


def main() -> None:
    repo = Path.cwd().resolve()
    candidate_dir = Path(os.environ["CTRL01_CANDIDATE_DIR"]).resolve()
    evidence_dir = Path(os.environ["CTRL01_EVIDENCE_DIR"]).resolve()
    candidate_zip = locate_single(candidate_dir, CANDIDATE_FILE)
    if candidate_zip.stat().st_size != CANDIDATE_SIZE:
        fail(f"candidate size mismatch: {candidate_zip.stat().st_size} != {CANDIDATE_SIZE}")
    actual = sha256_file(candidate_zip)
    if actual != CANDIDATE_SHA256:
        fail(f"candidate sha mismatch: {actual} != {CANDIDATE_SHA256}")
    evidence_path = locate_single(evidence_dir, "ctrl01_c1_authoritative_acceptance_result.json")

    trigger = assert_pre_promotion_drift(repo)
    work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ctrl01-canonical-promotion"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with zipfile.ZipFile(candidate_zip) as zf:
        safe_extract(zf, work)
    candidate_root = work / ROOT_NAME
    if not candidate_root.is_dir():
        fail(f"candidate root missing: {candidate_root}")
    verify_internal_seal(candidate_root)
    evidence = verify_acceptance_basis(candidate_root, evidence_path)
    installed = install_payload(repo, candidate_root)
    write_acceptance(repo, evidence, installed, trigger)
    update_pcr(repo)
    final_semantic_assertions(repo, installed)
    restore_transport(repo)
    final_sha = commit_and_push(trigger)
    print(f"CTRL01_C1_CANONICAL_PROMOTION:PASS:{final_sha}")


if __name__ == "__main__":
    main()
