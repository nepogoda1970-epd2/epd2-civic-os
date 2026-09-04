from __future__ import annotations

import hashlib
import json
import pathlib
import sys

C2_SHA = "d86bb4f7bb40e052af877bcae27257859c00168bff3184d2aed951eb6d236072"
OPS02_SHA = "ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125"

G02 = """    def g02_ops02_binding(self, result: GateResult) -> None:
        record_path = (
            self.repo_root / "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json"
        )
        if not record_path.is_file():
            raise GateFailure(
                "the accepted OPS-02 C3 acceptance record is missing at "
                f"{record_path}"
            )
        record = json.loads(record_path.read_text(encoding="utf-8"))
        candidate = record.get("candidate", {})
        bound = {
            "candidate_sha256": ACCEPTED_OPS02_CANDIDATE_SHA256,
            "freeze_tree_digest": ACCEPTED_OPS02_FREEZE_TREE_DIGEST,
            "source_commit": ACCEPTED_OPS02_SOURCE_COMMIT,
        }
        recorded = {
            "candidate_sha256": candidate.get("sha256"),
            "freeze_tree_digest": candidate.get("freeze_tree_digest"),
            "source_commit": candidate.get("source_commit"),
        }
        mismatched = {
            key: (bound[key], recorded[key])
            for key in bound
            if bound[key] != recorded[key]
        }
        if mismatched:
            _fail(
                result,
                [
                    "the bound accepted OPS-02 "
                    f"{key} does not match canonical governance: "
                    f"bound {value[0]!r}, recorded {value[1]!r}"
                    for key, value in sorted(mismatched.items())
                ],
            )
        if record.get("decision") != "ACCEPTED / CLOSED":
            _fail(
                result,
                [f"OPS-02 is recorded as {record.get('decision')!r}, not accepted"],
            )
        authoritative = (
            self.repo_root
            / "docs/ops/OPS-02/OPS02_C3_AUTHORITATIVE_ACCEPTANCE_RESULT.json"
        )
        if not authoritative.is_file():
            _fail(result, ["the OPS-02 C3 authoritative acceptance result is missing"])
        else:
            doc = json.loads(authoritative.read_text(encoding="utf-8"))
            passed = (
                doc.get("verdict") == "PASS"
                or doc.get("decision") == "PASS"
                or doc.get("result", {}).get("gates_passed") == 42
            )
            if not passed:
                _fail(result, ["the OPS-02 C3 authoritative acceptance result is not PASS"])
            result.measurements["ops02_authoritative_acceptance"] = doc
        archive = self._accepted_artifact_path(
            "EPD2_OPS02_", ACCEPTED_OPS02_CANDIDATE_SHA256
        )
        if archive is None:
            raise GateBlocked(
                "the exact accepted OPS-02 C3 bytes are not present; supply sha256 "
                f"{ACCEPTED_OPS02_CANDIDATE_SHA256} via EPD2_OPS03_ACCEPTED_ARTIFACTS"
            )
        result.measurements["accepted_ops02"] = {
            **bound,
            "acceptance_record": recorded,
        }
        result.measurements["accepted_archive"] = str(archive)
        result.observations.append(
            "OPS-02 predecessor is bound to exact independently accepted C3 bytes "
            "and authoritative PASS; its historical harness is not replayed because "
            "its G04 dependency-state assumption predates API-layer closure"
        )

"""


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c3_patch_from_c2.py <extracted-c2-root>")
    root = pathlib.Path(sys.argv[1]).resolve()
    validator = root / "scripts/validation/validate_ops03.py"
    text = validator.read_text(encoding="utf-8")
    start = text.index("    def g02_ops02_binding(self, result: GateResult) -> None:\n")
    end = text.index("    def g03_ops01_foundation(self, result: GateResult) -> None:\n", start)
    text = text[:start] + G02 + text[end:]
    text = text.replace("    ACCEPTED_OPS02_SOURCE_BUNDLE_SHA256,\n", "")
    validator.write_text(text, encoding="utf-8")

    state_path = root / "OPS03_CANDIDATE_SELF_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        candidate_role="C3",
        candidate_self_state="CANDIDATE_NOT_ACCEPTED",
        self_accepted=False,
        supersedes_candidate_sha256=C2_SHA,
    )
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    correction = root / "docs/ops/OPS-03/OPS03_C3_CORRECTION_RECORD.json"
    correction.parent.mkdir(parents=True, exist_ok=True)
    correction.write_text(
        json.dumps(
            {
                "schema": "epd2.ops03.c3-correction/1",
                "stage": "OPS-03",
                "candidate_role": "C3",
                "source_candidate_sha256": C2_SHA,
                "accepted_ops02_candidate_sha256": OPS02_SHA,
                "correction": (
                    "G02 binds exact accepted OPS-02 C3 bytes plus canonical authoritative "
                    "acceptance; historical OPS-02 harness is not replayed after later "
                    "API-layer closure"
                ),
                "self_acceptance": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    excluded_prefixes = (
        ".venv/",
        ".git/",
        ".pytest_cache/",
        ".ruff_cache/",
        ".mypy_cache/",
        "validation/ops03/",
    )
    excluded_names = {"OPS03_FREEZE_MANIFEST.json", "SHA256SUMS.txt"}
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        if (
            rel in excluded_names
            or rel.startswith(excluded_prefixes)
            or "/__pycache__/" in f"/{rel}"
            or rel.endswith(".pyc")
        ):
            continue
        files[rel] = sha256(path)
    canonical = json.dumps(
        dict(sorted(files.items())), sort_keys=True, separators=(",", ":")
    ).encode()
    manifest = {
        "schema": "epd2.ops03.freeze-manifest/1",
        "stage": "OPS-03",
        "candidate_role": "C3",
        "file_count": len(files),
        "files": files,
        "tree_digest": hashlib.sha256(canonical).hexdigest(),
    }
    (root / "OPS03_FREEZE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    rows: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        if (
            rel == "SHA256SUMS.txt"
            or rel.startswith(".venv/")
            or "/__pycache__/" in f"/{rel}"
            or rel.endswith(".pyc")
        ):
            continue
        rows.append(f"{sha256(path)}  {rel}")
    (root / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"OPS03_C3_PATCH:PASS:{len(files)}:{manifest['tree_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
