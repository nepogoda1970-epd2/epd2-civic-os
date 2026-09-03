#!/usr/bin/env python3
"""Independently verify a sealed CTRL-04 candidate archive on its exact bytes.

Checks archive safety and hygiene, the complete internal `SHA256SUMS.txt`,
the developer evidence disposition (52/52 gates, 48/48 mutations, 20/20 E2E,
browser PASS), the exact CTRL-01/02/03 and INFRA/OPS predecessor identities,
and that the candidate never self-accepts. Prints
`CTRL04_PACKAGE_VERIFY:PASS:<sha256>:<size>` on success.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
PREDECESSORS = {
    "CTRL-01": ("07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5", 190099),
    "CTRL-02": ("f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e", 16720456),
    "CTRL-03": ("89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff", 16788860),
}
INFRA_OPS = {
    "INFRA-01": "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
    "INFRA-02": "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
    "OPS-01": "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27",
    "OPS-02": "ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"CTRL04_PACKAGE_VERIFY:FAIL:{message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if not args.archive.is_file():
        fail("archive missing")
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if not names or any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
            fail("unsafe archive path")
        if any(set(Path(n).parts) & FORBIDDEN_PARTS for n in names):
            fail("archive hygiene failure")
        if any(Path(n).suffix.lower() in {".pyc", ".pyo", ".db", ".sqlite", ".zip"} for n in names):
            fail("forbidden runtime or nested archive")
        if len({Path(n).parts[0] for n in names}) != 1:
            fail("archive must have one root")
        if len(names) != len(set(names)):
            fail("duplicate archive entries")
        with tempfile.TemporaryDirectory(prefix="ctrl04-verify-") as td:
            archive.extractall(td)
            root = Path(td) / Path(names[0]).parts[0]
            manifest = root / "SHA256SUMS.txt"
            if not manifest.is_file():
                fail("manifest missing")
            expected_files: set[str] = set()
            for line in manifest.read_text().splitlines():
                expected, relative = line.split("  ", 1)
                expected_files.add(relative)
                target = root / relative
                if not target.is_file() or digest(target) != expected:
                    fail(f"same-byte mismatch: {relative}")
            actual = {
                p.relative_to(root).as_posix()
                for p in root.rglob("*")
                if p.is_file() and p.name != "SHA256SUMS.txt"
            }
            if actual != expected_files:
                fail("manifest coverage mismatch")
            validation = root / "validation/ctrl04"
            result = json.loads((validation / "ctrl04_preseal_result.json").read_text())
            if (
                result["overall"] != "PASS"
                or result["gates_passed"] != 52
                or result["gates_failed"]
                or result["gates_blocked_for_final_seal"]
            ):
                fail("gate evidence mismatch")
            if (
                result["self_state"] != "CANDIDATE_NOT_ACCEPTED"
                or result["self_acceptance"] is not False
            ):
                fail("developer self-acceptance forbidden")
            mutation = json.loads((validation / "mutation_result.json").read_text())
            if mutation["detected"] != 48 or mutation["undetected"] or mutation["executed"] != 48:
                fail("mutation evidence mismatch")
            e2e = json.loads((validation / "e2e_journeys_result.json").read_text())
            if (
                e2e["journeys_passed"] != 20
                or e2e["integration_class"] != "REFERENCE_AND_LOCAL_REAL_ADAPTERS"
            ):
                fail("e2e evidence mismatch")
            browser = json.loads((validation / "browser_journeys_result.json").read_text())
            if browser.get("status") != "PASS":
                fail("browser evidence mismatch")
            predecessors = json.loads(
                (validation / "predecessor_dependency_result.json").read_text()
            )
            for stage, (sha, size) in PREDECESSORS.items():
                recorded = predecessors["ctrl"][stage]
                if recorded[0] != sha or recorded[1] != size:
                    fail(f"{stage} predecessor identity mismatch")
            for stage, sha in INFRA_OPS.items():
                layer = "infra" if stage.startswith("INFRA") else "ops"
                if (
                    predecessors[layer][stage]["expected_sha256"] != sha
                    or not predecessors[layer][stage]["bound"]
                ):
                    fail(f"{stage} identity mismatch")
            for stage in ("INFRA-03", "OPS-03"):
                layer = "infra" if stage.startswith("INFRA") else "ops"
                if predecessors[layer][stage].get("claimed_as_canonical_dependency") is not False:
                    fail(f"{stage} must not be claimed as accepted")
            candidate = json.loads(
                (root / "docs/ctrl/CTRL-04/CTRL04_C1_CANDIDATE_MANIFEST.json").read_text()
            )
            if (
                candidate["candidate_state"] != "CANDIDATE_NOT_ACCEPTED"
                or candidate["self_acceptance"] is not False
            ):
                fail("candidate manifest self-state")
            report = (root / "docs/ctrl/CTRL-04/CTRL04_DEVELOPER_REPORT.md").read_text()
            for phrase in (
                "CTRL-04 — ACCEPTED",
                "CTRL-04 = ACCEPTED",
                "CANON PASS",
                "PRODUCTION READY",
                "BSI/CC CERTIFIED",
                "SECURITY CERTIFIED",
            ):
                if (
                    phrase in report
                    and "must never" not in report.split(phrase, 1)[0][-200:]
                    and "does not claim" not in report.split(phrase, 1)[0][-200:]
                ):
                    fail(f"forbidden developer conclusion in report: {phrase}")
            source = root / "services/control-plane-service/src/epd2_control_plane_service"
            source = source / "operations_console.py"
            if 'SELF_STATE: Final = "CANDIDATE_NOT_ACCEPTED"' not in source.read_text():
                fail("runtime self-state mutated")
    print(f"CTRL04_PACKAGE_VERIFY:PASS:{digest(args.archive)}:{args.archive.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
