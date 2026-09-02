from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import tomllib

API06_SHA = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
PROTECTED_PREFIXES = (
    ".github/workflows/",
    "docs/api/API-06/",
    "docs/ctrl/CTRL-01/",
    "docs/roadmap/",
    "scripts/check_repository.py",
    "Makefile",
)
EXCLUDED_FREEZE_PREFIXES = (
    ".venv/",
    ".git/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "validation/ops03/",
)
EXCLUDED_FREEZE_NAMES = {"OPS03_FREEZE_MANIFEST.json", "SHA256SUMS.txt"}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_map(root: pathlib.Path) -> dict[str, pathlib.Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


def normalized_root(root: pathlib.Path) -> pathlib.Path:
    entries = [p for p in root.iterdir() if p.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        only = entries[0]
        if (only / "pyproject.toml").exists() or (only / "docs").exists():
            return only
    return root


def is_text(path: pathlib.Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def copy_file(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def merge_text(ours: pathlib.Path, base: pathlib.Path, theirs: pathlib.Path, out: pathlib.Path) -> None:
    proc = subprocess.run(
        ["git", "merge-file", "-p", str(ours), str(base), str(theirs)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"three-way conflict: {out}: {proc.stderr.decode(errors='replace')}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(proc.stdout)
    shutil.copymode(theirs, out)


def semantic_subset(current: object, candidate: object) -> bool:
    if isinstance(current, dict):
        return isinstance(candidate, dict) and all(
            k in candidate and semantic_subset(v, candidate[k]) for k, v in current.items()
        )
    if isinstance(current, list):
        return isinstance(candidate, list) and all(item in candidate for item in current)
    return current == candidate


def assert_pyproject_superset(ours: pathlib.Path, theirs: pathlib.Path) -> None:
    with ours.open("rb") as fh:
        current = tomllib.load(fh)
    with theirs.open("rb") as fh:
        candidate = tomllib.load(fh)
    if not semantic_subset(current, candidate):
        raise RuntimeError("OPS-03 C1 pyproject is not a semantic superset of current canonical pyproject")
    expected = {"epd2-ops", "epd2-preview", "epd2-qualification"}
    deps = set(candidate.get("project", {}).get("dependencies", []))
    if not expected.issubset(deps):
        raise RuntimeError("OPS workspace dependencies missing from C1 pyproject")


def assert_lock_superset(ours: pathlib.Path, theirs: pathlib.Path) -> None:
    with ours.open("rb") as fh:
        current = tomllib.load(fh)
    with theirs.open("rb") as fh:
        candidate = tomllib.load(fh)
    cp = current.get("package", [])
    tp = candidate.get("package", [])
    by_name = {p.get("name"): p for p in tp}
    for package in cp:
        name = package.get("name")
        if name not in by_name:
            raise RuntimeError(f"current canonical lock package absent from C1: {name}")
        if name == "epd2-civic-os":
            if not semantic_subset(package, by_name[name]):
                raise RuntimeError("C1 root lock entry is not a semantic superset")
        elif package != by_name[name]:
            raise RuntimeError(f"current canonical lock package changed in C1: {name}")
    expected = {"epd2-ops", "epd2-preview", "epd2-qualification"}
    if not expected.issubset(by_name):
        raise RuntimeError("OPS packages missing from C1 uv.lock")


def carry_missing_workspace_members(
    out_root: pathlib.Path, ops02_root: pathlib.Path, c1_root: pathlib.Path
) -> list[str]:
    """Carry accepted predecessor workspace members that current main does not install.

    OPS-03 C1 was built on top of accepted OPS-02. A pure delta application is not
    sufficient when current canonical main intentionally records OPS acceptance
    governance without installing every predecessor workspace package. The C2 lock
    remains frozen, so every declared local workspace member must be physically
    present. Missing members are copied byte-for-byte from accepted OPS-02 first,
    with C1 as a fail-safe source only when the predecessor archive lacks the path.
    Existing current-canonical paths are never overwritten here.
    """
    pyproject = out_root / "pyproject.toml"
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)
    members = data.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])
    if not isinstance(members, list):
        raise RuntimeError("tool.uv.workspace.members must be a list")

    carried: list[str] = []
    for member in members:
        if not isinstance(member, str) or not member:
            raise RuntimeError(f"invalid workspace member: {member!r}")
        if any(ch in member for ch in "*?["):
            # Existing repositories may use workspace globs. They are already
            # represented in current main; do not guess a predecessor expansion.
            continue
        target = out_root / member
        if target.exists():
            continue
        source: pathlib.Path | None = None
        for root in (ops02_root, c1_root):
            candidate = root / member
            if candidate.exists() and candidate.is_dir():
                source = candidate
                break
        if source is None:
            raise RuntimeError(f"frozen workspace member missing from all governed inputs: {member}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=False)
        carried.append(member)

    return carried


def apply_delta(base_root: pathlib.Path, c1_root: pathlib.Path, out_root: pathlib.Path) -> dict[str, object]:
    base, c1, ours = file_map(base_root), file_map(c1_root), file_map(out_root)
    added: list[str] = []
    changed: list[str] = []
    deleted: list[str] = []
    merged: list[str] = []
    preserved_newer: list[str] = []
    protected_delta: list[str] = []

    for rel in sorted(set(base) | set(c1)):
        b, t, o = base.get(rel), c1.get(rel), ours.get(rel)
        bsha = sha(b) if b else None
        tsha = sha(t) if t else None
        osha = sha(o) if o else None
        if bsha == tsha:
            continue
        if rel.startswith(PROTECTED_PREFIXES):
            protected_delta.append(rel)
            continue

        target = out_root / rel
        if rel == "pyproject.toml" and o is not None and t is not None:
            assert_pyproject_superset(o, t)
            copy_file(t, target)
            changed.append(rel)
            continue
        if rel == "uv.lock" and o is not None and t is not None:
            assert_lock_superset(o, t)
            copy_file(t, target)
            changed.append(rel)
            continue

        if b is None and t is not None:
            if o is None:
                copy_file(t, target)
                added.append(rel)
            elif osha != tsha:
                if is_text(o) and is_text(t):
                    empty = out_root / ".ops03-empty-base"
                    empty.write_text("")
                    merge_text(o, empty, t, target)
                    empty.unlink(missing_ok=True)
                    merged.append(rel)
                else:
                    raise RuntimeError(f"binary/add-add conflict: {rel}")
            continue

        if b is not None and t is None:
            if o is None:
                continue
            if osha == bsha:
                target.unlink()
                deleted.append(rel)
            else:
                preserved_newer.append(rel)
            continue

        assert b is not None and t is not None
        if o is None or osha == bsha:
            copy_file(t, target)
            changed.append(rel)
        elif osha == tsha:
            continue
        elif is_text(o) and is_text(b) and is_text(t):
            merge_text(o, b, t, target)
            merged.append(rel)
        else:
            raise RuntimeError(f"binary three-way conflict: {rel}")

    return {
        "added": added,
        "changed": changed,
        "deleted": deleted,
        "merged": merged,
        "preserved_newer": preserved_newer,
        "protected_current_canonical": protected_delta,
    }


def update_json(path: pathlib.Path, updates: dict[str, object]) -> None:
    data: dict[str, object] = json.loads(path.read_text()) if path.exists() else {}
    data.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def build_freeze(root: pathlib.Path) -> dict[str, object]:
    mapping: dict[str, str] = {}
    for rel, p in sorted(file_map(root).items()):
        if rel in EXCLUDED_FREEZE_NAMES or rel.startswith(EXCLUDED_FREEZE_PREFIXES):
            continue
        if "/__pycache__/" in f"/{rel}" or rel.endswith(".pyc"):
            continue
        mapping[rel] = sha(p)
    canon = json.dumps(
        dict(sorted(mapping.items())), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    doc = {
        "schema": "epd2.ops03.freeze-manifest/1",
        "stage": "OPS-03",
        "candidate_role": "C2",
        "file_count": len(mapping),
        "files": mapping,
        "tree_digest": hashlib.sha256(canon).hexdigest(),
    }
    (root / "OPS03_FREEZE_MANIFEST.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return doc


def write_sha256sums(root: pathlib.Path) -> None:
    rows = []
    for rel, p in sorted(file_map(root).items()):
        if rel == "SHA256SUMS.txt":
            continue
        if rel.startswith(".venv/") or "/__pycache__/" in f"/{rel}" or rel.endswith(".pyc"):
            continue
        rows.append(f"{sha(p)}  {rel}")
    (root / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-root", required=True)
    ap.add_argument("--ops02-root", required=True)
    ap.add_argument("--ops03-c1-root", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--main-commit", required=True)
    ap.add_argument("--main-tree", required=True)
    ap.add_argument("--template", required=True)
    args = ap.parse_args()

    main_root = normalized_root(pathlib.Path(args.main_root))
    ops02_root = normalized_root(pathlib.Path(args.ops02_root))
    c1_root = normalized_root(pathlib.Path(args.ops03_c1_root))
    out_root = pathlib.Path(args.out_root)
    if out_root.exists():
        shutil.rmtree(out_root)
    shutil.copytree(main_root, out_root, symlinks=False)

    delta = apply_delta(ops02_root, c1_root, out_root)
    delta["carried_predecessor_workspace"] = carry_missing_workspace_members(
        out_root, ops02_root, c1_root
    )

    for name in (".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
        shutil.rmtree(out_root / name, ignore_errors=True)
    for p in out_root.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    for p in out_root.rglob("*.pyc"):
        p.unlink(missing_ok=True)
    shutil.rmtree(out_root / "validation" / "ops03", ignore_errors=True)

    template = pathlib.Path(args.template)
    template_dst = out_root / "handoff" / "OPS-03" / "templates" / "C2" / "ops03-accept.yml"
    copy_file(template, template_dst)

    baseline = out_root / "docs" / "ops" / "OPS-03" / "OPS03_ENTERING_BASELINE_IDENTITY.json"
    update_json(
        baseline,
        {
            "schema": "epd2.ops03.entering-baseline/2",
            "stage": "OPS-03",
            "candidate_role": "C2",
            "base_commit": args.main_commit,
            "base_tree": args.main_tree,
            "main_commit": args.main_commit,
            "main_tree": args.main_tree,
            "accepted_api06_candidate_sha256": API06_SHA,
            "api_layer_state": "CLOSED",
            "reconciliation": "OPS02_C3_TO_OPS03_C1_DELTA_THREE_WAY_APPLIED_ON_CURRENT_CANONICAL_MAIN",
        },
    )

    state = out_root / "OPS03_CANDIDATE_SELF_STATE.json"
    update_json(
        state,
        {
            "schema": "epd2.ops03.candidate-self-state/2",
            "stage": "OPS-03",
            "candidate_role": "C2",
            "candidate_self_state": "CANDIDATE_NOT_ACCEPTED",
            "self_accepted": False,
            "entering_main_commit": args.main_commit,
            "entering_main_tree": args.main_tree,
            "accepted_api06_candidate_sha256": API06_SHA,
            "api_layer_state": "CLOSED",
            "harness": "PASS",
            "handoff_state": "READY_FOR_INDEPENDENT_GOVERNED_REVIEW",
            "declared_blockers": [],
            "canonical_acceptance_required": True,
        },
    )

    evidence = out_root / "docs" / "ops" / "OPS-03" / "OPS03_C2_RECONCILIATION.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        json.dumps(
            {
                "schema": "epd2.ops03.c2-reconciliation/1",
                "stage": "OPS-03",
                "source_candidate": "C1",
                "target_candidate": "C2",
                "entering_main_commit": args.main_commit,
                "entering_main_tree": args.main_tree,
                "accepted_api06_candidate_sha256": API06_SHA,
                "api_layer_state": "CLOSED",
                "method": "THREE_WAY_RECONCILIATION_USING_ACCEPTED_OPS02_C3_AS_COMMON_BASE",
                "delta": delta,
                "remaining_dependency_blockers": [],
                "self_acceptance": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    freeze = build_freeze(out_root)
    write_sha256sums(out_root)
    print(json.dumps({"result": "PASS", "delta": delta, "freeze": freeze}, sort_keys=True))
    print(f"OPS03_C2_RECONCILE:PASS:{freeze['file_count']}:{freeze['tree_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
