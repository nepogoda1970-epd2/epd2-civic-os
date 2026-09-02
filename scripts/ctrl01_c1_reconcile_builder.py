#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

P1_SHA256 = "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
P1_BASE_MAIN = "cb02b231e701d0b4f12db89c86bc56a9fe11f71a"
BASE_MAIN = "217559b7f21c338d6fe8d4e4676082cd3840251c"
BASE_TREE = "eb8a3254c2b8a30feff71318d4377eff2435605c"
CANDIDATE_NAME = "EPD2_CTRL01_GOVERNED_CONTROL_PLANE_CANDIDATE_0.1_C1"

CANONICAL_BLOBS: dict[str, str] = {
    "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md": "4b69cf500f2171399f7fb0b4213cb1bddcc8cf07",
    "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md": "aad828e377889e96f0bce16245f4e9ed1d97ed4a",
    "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md": "7f5c6a9a88f8e653b43dc542a595ac37bf7a0692",
    "docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md": "15dd290a1bcb6f44b4242e7c33b71119e404553a",
}

ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {
    "docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json": "7f8b16ca16a11f4916f1988ef53243b977e1862d",
    "docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json": "0f41555a4aa5f0bf80fa7a1a95be905c02d692c5",
    "docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json": "fab2833e6769bc9e71876e47b168848e6c386e96",
    "docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json": "e35f0ff0438419db445580f8739575ccba3f6551",
    "docs/frontend/FRONT-04-C2-ACCEPTANCE-RECORD.json": "5eb35c0699434f1f93c63bfc23a87097c609ca06",
    "docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json": "ced7d78a779343b5507a5cd612ad8620e8c821cd",
    "docs/frontend/FRONT-02-C2.1-ACCEPTANCE-RECORD.json": "8f22eab702d7d674be115916defb2e12e63d7680",
    "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json": "5618144cf503b55bea96550c80d80cac78580963",
    "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json": "95df6e5c5288b16aee62621157fc28a790b68bfc",
    "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json": "0b23469ac20c34fa7891653cb41d0eaa44437ac6",
    "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json": "3d4baa96b957693244507aaa76f2d685226f88b6",
}

DELTA_PREFIXES = (
    "services/control-plane-service/",
    "docs/ctrl/CTRL-01/",
    "scripts/ctrl01_validator.py",
    "scripts/ctrl01_registry_export.py",
    "scripts/system_trial_preview_prepare.py",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(*cmd: str, cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)
    return p.stdout.strip()


def git_blob(repo: Path, rel: str) -> str:
    return run("git", "rev-parse", f"HEAD:{rel}", cwd=repo)


def assert_base(repo: Path) -> None:
    head = run("git", "rev-parse", "HEAD", cwd=repo)
    tree = run("git", "rev-parse", "HEAD^{tree}", cwd=repo)
    if head != BASE_MAIN:
        raise SystemExit(f"wrong base main: {head} != {BASE_MAIN}")
    if tree != BASE_TREE:
        raise SystemExit(f"wrong base tree: {tree} != {BASE_TREE}")
    for rel, expected in {**CANONICAL_BLOBS, **ACCEPTED_PREDECESSOR_BLOBS}.items():
        actual = git_blob(repo, rel)
        if actual != expected:
            raise SystemExit(f"canonical blob drift: {rel}: {actual} != {expected}")


def assert_no_source_overlap(repo: Path) -> None:
    try:
        run("git", "cat-file", "-e", f"{P1_BASE_MAIN}^{{commit}}", cwd=repo)
    except subprocess.CalledProcessError:
        return
    changed = run("git", "diff", "--name-only", P1_BASE_MAIN, BASE_MAIN, cwd=repo).splitlines()
    overlap = [p for p in changed if any(p == x or p.startswith(x) for x in DELTA_PREFIXES)]
    if overlap:
        raise SystemExit(
            "P1/current-main source overlap requires manual reconciliation: " + ", ".join(overlap)
        )


def replace_mapping(text: str, name: str, mapping: dict[str, str]) -> str:
    pattern = rf"{re.escape(name)}: dict\[str, str\] = \{{.*?\n\}}"
    rows: list[str] = []
    for key, value in mapping.items():
        rows.extend([f"    {key!r}: (", f"        {value!r}", "    ),"])
    replacement = name + ": dict[str, str] = {\n" + "\n".join(rows) + "\n}"
    new, n = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"unable to replace {name}")
    return new


def patch_validator(path: Path) -> None:
    t = path.read_text()
    t = replace_mapping(t, "CANONICAL_BLOBS", CANONICAL_BLOBS)
    t = replace_mapping(t, "ACCEPTED_PREDECESSOR_BLOBS", ACCEPTED_PREDECESSOR_BLOBS)
    t = replace_mapping(
        t,
        "UNRECONCILED_DEPENDENCIES",
        {"API-06": "NEXT / NOT ACCEPTED; API layer remains open until API-06 closes"},
    )
    t, n = re.subn(
        r'BASELINE_COMMIT = "[0-9a-f]{40}"',
        f'BASELINE_COMMIT = "{BASE_MAIN}"',
        t,
        count=1,
    )
    if n != 1:
        raise SystemExit("unable to replace BASELINE_COMMIT")

    start = t.find("def _register_conflicts()")
    end = t.find("\n\ndef _write(", start)
    if start < 0 or end < 0:
        raise SystemExit("unable to locate _register_conflicts")
    replacement = '''def _register_conflicts() -> list[dict[str, str]]:
    """Fail closed on material current-state disagreement only."""
    register = REPO_ROOT / "docs" / "roadmap" / "EPD2_PROGRAM_CONTROL_REGISTER.md"
    if not register.exists():
        return [{"conflict_id": "PCR-MISSING", "statement_a": "PCR missing"}]
    text = register.read_text(errors="replace")
    required = {
        "PCR-API05": "API-05 = ACCEPTED / CLOSED",
        "PCR-API06": "API-06 = NEXT",
        "PCR-INFRA02": "INFRA-02 ACCEPTED / CLOSED",
        "PCR-OPS02": "OPS-02 ACCEPTED / CLOSED",
        "PCR-CTRL": "| CTRL | `NOT_STARTED` |",
    }
    conflicts: list[dict[str, str]] = []
    for cid, needle in required.items():
        if needle not in text:
            conflicts.append({
                "conflict_id": cid,
                "statement_a": f"required current PCR fact missing: {needle}",
                "ctrl01_position": "fail closed pending governed reconciliation",
            })
    return conflicts
'''
    t = t[:start] + replacement + t[end:]

    t = t.replace(
        '"reconcile exact accepted API-05 identity or record it as not yet accepted",\n                ',
        "",
    )
    t = t.replace(
        '"reconcile INFRA-02 and OPS-02 if accepted before CTRL-01 seal",\n                ',
        "",
    )
    t = t.replace(
        '"reconcile exact accepted API-06 identity or record it as not yet accepted",',
        '"keep API-06 NEXT / NOT ACCEPTED unless later authoritative acceptance exists",',
    )
    t = t.replace(
        '"API-04": "event/messaging semantics not consumed by CTRL-01 preseal work",\n                "INFRA-01":',
        '"API-04": "event/messaging semantics not consumed by CTRL-01 bounded work",\n'
        '                "API-05": "accepted API-05 C1 authority record",\n'
        '                "INFRA-01":',
    )
    t = t.replace(
        '"OPS-01": "incident, recovery and change-control separation-of-duties conventions",',
        '"INFRA-02": "accepted bounded CI/CD and supply-chain foundation",\n'
        '                "OPS-01": "incident/recovery/change-control SoD conventions",\n'
        '                "OPS-02": "accepted bounded OPS-02 implementation",',
    )
    path.write_text(t)


def patch_trial(path: Path) -> None:
    t = path.read_text()
    replacements = {
        '"API-05": "API-05 is ACTIVE / IN DEVELOPMENT / NOT ACCEPTED.",': (
            '"API-05": "API-05 C1 is ACCEPTED / CLOSED; not a current checkpoint blocker.",'
        ),
        '"INFRA-02": "INFRA preview-readiness minimum is not recorded as met.",': (
            '"INFRA-02": "INFRA-02 is ACCEPTED / CLOSED; joint preview remains governed.",'
        ),
        '{"item": "remaining API surface", "source": "API-05 / API-06", "state": "NOT_ACCEPTED"}': (
            '{"item": "remaining API surface", "source": "API-06", "state": "NEXT_NOT_ACCEPTED"}'
        ),
    }
    for old, new in replacements.items():
        t = t.replace(old, new)
    t = t.replace(
        '"OPS preview-readiness minimum (deploy, observe, recover, reset) is not recorded as met."',
        '"OPS-02 C3 is ACCEPTED / CLOSED; joint preview remains separately governed."',
    )
    path.write_text(t)


def reconciliation_banner() -> str:
    return f'''\n> **CTRL-01 C1 canonical reconciliation — 2026-09-02.** This candidate is\n> reconciled to canonical `main@{BASE_MAIN}`. P1 statements that API-05,\n> INFRA-02 or OPS-02 were not accepted are historical and superseded for current-state\n> interpretation. Their exact accepted governance records are bound by Git blob identity.\n> API-06 remains `NEXT / NOT ACCEPTED`; the API layer remains open and System Trial\n> Preview remains `CHECKPOINT_NOT_OPEN`. This bounded CTRL-01 acceptance does not claim\n> `CTRL CLOSED`, production readiness, legal activation, or BSI/Common Criteria certification.\n\n'''


def patch_text_doc(path: Path) -> None:
    t = path.read_text()
    t = t.replace(P1_BASE_MAIN, BASE_MAIN)
    t = t.replace("1ea6161335044dc4d1e50a6b1588bad6627f7af5", BASE_TREE)
    t = t.replace(
        "`API-05`, `API-06`, `INFRA-02` and `OPS-02` are **not accepted**",
        "`API-05`, `INFRA-02` and `OPS-02` are **ACCEPTED / CLOSED as bounded stages**; "
        "`API-06` remains **NEXT / NOT ACCEPTED**",
    )
    t = t.replace(
        "`API-05`, `API-06`, `INFRA-02` and `OPS-02` are not accepted.",
        "`API-05`, `INFRA-02` and `OPS-02` are accepted/closed as bounded stages; "
        "`API-06` remains NEXT / NOT ACCEPTED.",
    )
    t = t.replace(
        "API-05 is ACTIVE / IN DEVELOPMENT / NOT ACCEPTED", "API-05 C1 is ACCEPTED / CLOSED"
    )
    t = t.replace(
        "reconcile exact accepted API-05 identity or record it as not yet accepted",
        "preserve the exact accepted API-05 C1 identity",
    )
    t = t.replace(
        "reconcile INFRA-02 and OPS-02 if either is accepted by then",
        "preserve the exact accepted INFRA-02 and OPS-02 identities",
    )
    if "CTRL-01 C1 canonical reconciliation" not in t:
        first_nl = t.find("\n")
        if first_nl >= 0:
            t = t[: first_nl + 1] + reconciliation_banner() + t[first_nl + 1 :]
        else:
            t = reconciliation_banner() + t
    path.write_text(t)


def overlay(p1: Path, repo: Path) -> None:
    if sha256(p1) != P1_SHA256:
        raise SystemExit("P1 SHA mismatch")
    assert_base(repo)
    assert_no_source_overlap(repo)

    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(p1) as z:
            bad = z.testzip()
            if bad is not None:
                raise SystemExit(f"P1 CRC failure: {bad}")
            z.extractall(td)
        roots = [p for p in Path(td).iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise SystemExit("unexpected P1 root")
        src = roots[0]
        required = [
            "services/control-plane-service",
            "docs/ctrl/CTRL-01",
            "scripts/ctrl01_validator.py",
            "scripts/ctrl01_registry_export.py",
            "scripts/system_trial_preview_prepare.py",
            "README.md",
        ]
        missing = [rel for rel in required if not (src / rel).exists()]
        if missing:
            raise SystemExit("P1 missing required paths: " + ", ".join(missing))

        for rel in ["services/control-plane-service", "docs/ctrl/CTRL-01"]:
            dst = repo / rel
            if dst.exists():
                shutil.rmtree(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src / rel, dst)
        for rel in [
            "scripts/ctrl01_validator.py",
            "scripts/ctrl01_registry_export.py",
            "scripts/system_trial_preview_prepare.py",
        ]:
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / rel, dst)
        shutil.copy2(src / "README.md", repo / "CTRL01_CANDIDATE_README.md")

    patch_validator(repo / "scripts/ctrl01_validator.py")
    patch_trial(repo / "scripts/system_trial_preview_prepare.py")
    patch_text_doc(repo / "CTRL01_CANDIDATE_README.md")
    for p in sorted((repo / "docs/ctrl/CTRL-01").glob("*.md")):
        patch_text_doc(p)

    reconcile = {
        "schema": "epd2.ctrl01.canonical-reconciliation/1",
        "p1_sha256": P1_SHA256,
        "p1_base_main": P1_BASE_MAIN,
        "canonical_base_main": BASE_MAIN,
        "canonical_base_tree": BASE_TREE,
        "canonical_blobs": CANONICAL_BLOBS,
        "accepted_predecessor_blobs": ACCEPTED_PREDECESSOR_BLOBS,
        "unreconciled_dependencies": {"API-06": "NEXT / NOT ACCEPTED"},
        "source_overlap_with_p1_to_current_governance_delta": [],
        "bounded_acceptance_semantics": (
            "CTRL-01 may be accepted independently; CTRL layer remains open/not closed"
        ),
        "system_trial_preview": "CHECKPOINT_NOT_OPEN",
    }
    out = repo / "validation/ctrl01/canonical_reconciliation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reconcile, indent=2, sort_keys=True) + "\n")
    print("CTRL01_C1_RECONCILIATION:READY")


def copy_tree(src: Path, dst: Path) -> None:
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {
            n
            for n in names
            if n in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
            or n.endswith(".pyc")
        }

    shutil.copytree(src, dst, ignore=ignore)


def package(repo: Path, out: Path, run_id: str) -> None:
    required = [
        repo / "services/control-plane-service",
        repo / "docs/ctrl/CTRL-01",
        repo / "scripts/ctrl01_validator.py",
        repo / "scripts/ctrl01_registry_export.py",
        repo / "scripts/system_trial_preview_prepare.py",
        repo / "validation/ctrl01",
        repo / "validation/system_trial_preview",
        repo / "CTRL01_CANDIDATE_README.md",
    ]
    missing = [str(p.relative_to(repo)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("cannot package; missing: " + ", ".join(missing))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / CANDIDATE_NAME
        root.mkdir()
        copy_tree(repo / "services/control-plane-service", root / "services/control-plane-service")
        copy_tree(repo / "docs/ctrl/CTRL-01", root / "docs/ctrl/CTRL-01")
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        for name in [
            "ctrl01_validator.py",
            "ctrl01_registry_export.py",
            "system_trial_preview_prepare.py",
        ]:
            shutil.copy2(repo / "scripts" / name, root / "scripts" / name)
        copy_tree(repo / "validation/ctrl01", root / "validation/ctrl01")
        copy_tree(
            repo / "validation/system_trial_preview",
            root / "validation/system_trial_preview",
        )
        shutil.copy2(repo / "CTRL01_CANDIDATE_README.md", root / "README.md")

        identity = {
            "schema": "epd2.ctrl01.candidate-identity/1",
            "stage": "CTRL-01",
            "candidate": CANDIDATE_NAME,
            "self_state": "CANDIDATE_NOT_ACCEPTED",
            "p1_sha256": P1_SHA256,
            "base_main_commit": BASE_MAIN,
            "base_main_tree": BASE_TREE,
            "api06_state": "NEXT / NOT ACCEPTED",
            "system_trial_preview": "CHECKPOINT_NOT_OPEN",
            "ctrl_layer_state": "OPEN / NOT CLOSED",
            "generated_by_workflow_run": int(run_id),
        }
        (root / "candidate_identity.json").write_text(
            json.dumps(identity, indent=2, sort_keys=True) + "\n"
        )

        members = sorted(
            p
            for p in root.rglob("*")
            if p.is_file()
            and p.name != "SHA256SUMS.txt"
            and "__pycache__" not in p.parts
            and not p.name.endswith(".pyc")
        )
        sums = "".join(f"{sha256(p)}  {p.relative_to(root).as_posix()}\n" for p in members)
        (root / "SHA256SUMS.txt").write_text(sums)

        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    arc = f"{CANDIDATE_NAME}/{p.relative_to(root).as_posix()}"
                    z.write(p, arc)

    result = {
        "schema": "epd2.ctrl01.candidate-build/1",
        "candidate_file": out.name,
        "sha256": sha256(out),
        "size": out.stat().st_size,
        "base_main": BASE_MAIN,
        "run_id": int(run_id),
        "self_state": "CANDIDATE_NOT_ACCEPTED",
    }
    print(json.dumps(result, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("overlay")
    p.add_argument("--p1", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p = sub.add_parser("package")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--run-id", required=True)
    args = ap.parse_args()
    if args.cmd == "overlay":
        overlay(args.p1, args.repo)
    else:
        package(args.repo, args.out, args.run_id)


if __name__ == "__main__":
    main()
