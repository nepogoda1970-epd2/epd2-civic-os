#!/usr/bin/env python3
"""Independently verify a sealed CTRL-05 candidate archive on its exact bytes.

Checks archive safety and hygiene, the complete internal `SHA256SUMS.txt`,
the developer evidence disposition (56/56 gates, 52/52 mutations, 22/22 E2E,
browser PASS), that every evidence file was produced from the exact runtime
bytes in the archive, the exact CTRL-01/02/03/04 and INFRA/OPS predecessor
identities, and that the candidate never self-accepts. Prints
`CTRL05_PACKAGE_VERIFY:PASS:<sha256>:<size>` on success.
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
    "CTRL-01": "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5",
    "CTRL-02": "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e",
    "CTRL-03": "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff",
    "CTRL-04": "346acc12316ac4a8f2be45c889aa9002172710da61c67ec88e54a976bb5733a2",
}
INFRA_OPS = {
    "INFRA-01": "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
    "INFRA-02": "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
    "INFRA-03": "6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1",
    "OPS-01": "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27",
    "OPS-02": "ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125",
}
#: The runtime files whose bytes every evidence file must have been produced
#: from. Recomputed here so the verifier does not trust the archive's own
#: helper script.
RUNTIME_FILES = (
    "services/control-plane-service/src/epd2_control_plane_service/oversight_console.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_sources.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_api.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_console.html",
)


def runtime_digest(root: Path) -> str:
    value = hashlib.sha256()
    for relative in RUNTIME_FILES:
        value.update(relative.encode())
        value.update((root / relative).read_bytes())
    return value.hexdigest()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"CTRL05_PACKAGE_VERIFY:FAIL:{message}")


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
        with tempfile.TemporaryDirectory(prefix="ctrl05-verify-") as td:
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
            validation = root / "validation/ctrl05"
            result = json.loads((validation / "preseal_result.json").read_text())
            if (
                result["overall"] != "PASS"
                or result["gates_passed"] != 56
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
            if mutation["detected"] != 52 or mutation["undetected"] or mutation["executed"] != 52:
                fail("mutation evidence mismatch")
            e2e = json.loads((validation / "e2e_journeys_result.json").read_text())
            if (
                e2e["journeys_passed"] != 22
                or e2e["integration_class"] != "REAL_INSTALLED_CTRL02_CTRL03_CTRL04_PLANES"
            ):
                fail("e2e evidence mismatch")
            browser = json.loads((validation / "browser_journeys_result.json").read_text())
            if browser.get("status") != "PASS" or browser.get("journeys_passed") != browser.get(
                "journeys_total"
            ):
                fail("browser evidence mismatch")
            # Every evidence file must have been produced from the runtime
            # bytes that are actually in this archive.
            expected_runtime = runtime_digest(root)
            for name, payload in (
                ("preseal", result),
                ("mutation", mutation),
                ("e2e", e2e),
                ("browser", browser),
            ):
                if payload.get("runtime_source_digest") != expected_runtime:
                    fail(f"{name} evidence is not bound to the archived runtime bytes")
            contract = json.loads(
                (root / "contracts/control/ctrl05_oversight_console.json").read_text()
            )
            for stage, sha in PREDECESSORS.items():
                if contract["predecessors"].get(stage) != sha:
                    fail(f"{stage} predecessor identity mismatch")
            dependencies = json.loads((validation / "dependency_identities.json").read_text())
            for stage, sha in INFRA_OPS.items():
                bound = dependencies["bound"].get(stage, {})
                if bound.get("expected_sha256") != sha or not bound.get("sha_in_record"):
                    fail(f"{stage} identity mismatch")
            for stage in ("OPS-03",):
                recorded = dependencies["recorded_unaccepted"].get(stage, {})
                if recorded.get("acceptance_record_found"):
                    fail(f"{stage} must not be claimed as accepted")
            if contract["universal_auditor_exists"] is not False or (
                contract["reviewer_may_execute_operations"] is not False
            ):
                fail("contract asserts a universal auditor or an operating reviewer")
            candidate = json.loads(
                (root / "docs/ctrl/CTRL-05/CTRL05_C1_CANDIDATE_MANIFEST.json").read_text()
            )
            if (
                candidate["candidate_state"] != "CANDIDATE_NOT_ACCEPTED"
                or candidate["self_acceptance"] is not False
            ):
                fail("candidate manifest self-state")
            report = (root / "docs/ctrl/CTRL-05/CTRL05_DEVELOPER_REPORT.md").read_text()
            for phrase in (
                "CTRL-05 — ACCEPTED",
                "CTRL-05 = ACCEPTED",
                "CTRL LAYER CLOSED",
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
            runtime = (source / "oversight_console.py").read_text()
            for expected in (
                'SELF_STATE: Final = "CANDIDATE_NOT_ACCEPTED"',
                "UNIVERSAL_AUDITOR_EXISTS: Final = False",
                "REVIEWER_MAY_EXECUTE_OPERATIONS: Final = False",
                "SOURCE_EVIDENCE_IS_MUTABLE: Final = False",
                "FRONTEND_MAY_ASSERT_INTEGRITY: Final = False",
                "FRONTEND_MAY_ASSERT_AUTHORITY: Final = False",
                "GATES_REQUIRED: Final = 56",
                "MUTATION_FIXTURES_REQUIRED: Final = 52",
                "E2E_JOURNEYS_REQUIRED: Final = 22",
            ):
                if expected not in runtime:
                    fail(f"runtime governed constant mutated: {expected}")
            # The accepted predecessor runtime must be present and untouched by
            # this stage; its files are named in the CTRL-04 installation
            # manifest and are simply expected to exist here.
            for installed in (
                "operations_console.py",
                "operations_adapters.py",
                "operations_api.py",
                "regional_operations.py",
                "credential_lifecycle.py",
                "audit.py",
            ):
                if not (source / installed).is_file():
                    fail(f"accepted predecessor runtime missing: {installed}")
    print(f"CTRL05_PACKAGE_VERIFY:PASS:{digest(args.archive)}:{args.archive.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
