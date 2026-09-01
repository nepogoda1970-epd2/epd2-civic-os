"""INFRA-01 mutation/adversarial suite for the acceptance harness itself.

Assignment §9: representative acceptance inputs are deliberately corrupted
and every corruption class must be detected. Each mutation asserts the exact
detector code that catches it, and a closing test proves the sixteen classes
map onto sixteen *distinct* detectors — no shared "poison marker" may make
dozens of mutations pass through one unrelated detector and be counted as
independent coverage (INFRA01-HI-05).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json, seal_document, sha256_file, write_canonical_json
from scripts.acceptance.evidence import build_manifest, emit_manifest, verify_evidence
from scripts.acceptance.executor import CheckResult, evaluate_output
from scripts.acceptance.freeze import FreezeInventory, take_inventory
from scripts.acceptance.frozen import verify_tree
from scripts.acceptance.governance import verify_governance
from scripts.acceptance.hygiene import scan_archive
from scripts.acceptance.identity import CandidateIdentity, lock_mismatches
from scripts.acceptance.package import build_archive, verify_archive_against_inventory
from scripts.acceptance.registry import Check, Expectation, Registry, load_registry
from scripts.acceptance.secrets_scan import scan_archive as secrets_scan_archive

#: mutation class -> the one detector code that must catch it.
EXPECTED_DETECTORS: dict[str, str] = {
    "M01-remove-mandatory-evidence": codes.EVIDENCE_MISSING,
    "M02-foreign-pass-log": codes.EVIDENCE_HASH_MISMATCH,
    "M03-frozen-artifact-byte-flip": codes.FROZEN_ARTIFACT_MISMATCH,
    "M04-forbidden-cache-directory": codes.FORBIDDEN_PATH,
    "M05-source-change-after-testing": codes.TREE_MUTATION_AFTER_FREEZE,
    "M06-source-change-inside-zip-only": codes.ARCHIVE_BYTE_MISMATCH,
    "M07-fake-test-count": codes.TEST_COUNT_MISMATCH,
    "M08-suppress-mandatory-command": codes.MANDATORY_CHECK_MISSING,
    "M09-exit-zero-missing-output": codes.EXPECTED_OUTPUT_MISSING,
    "M10-injected-secret": codes.SECRET_DETECTED,
    "M11-version-mismatch": codes.VERSION_MISMATCH,
    "M12-lock-hash-mismatch": codes.LOCK_HASH_MISMATCH,
    "M13-manifest-changed-after-seal": codes.MANIFEST_INTEGRITY_FAILURE,
    "M14-undeclared-archive-entry": codes.UNDECLARED_ARCHIVE_ENTRY,
    "M15-duplicate-archive-path": codes.DUPLICATE_ARCHIVE_PATH,
    "M16-second-canonical-register": codes.COMPETING_REGISTER,
}

ARCHIVE_ROOT = "MUTATION_CANDIDATE"
_ALLOWLIST = {
    "governed_additions": ["SHA256SUMS.txt", "ACCEPTANCE/FREEZE-INVENTORY.json"],
    "allowed_nested_archives": [],
    "allowed_empty_directories": [],
}


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "mutation",
            "GIT_AUTHOR_EMAIL": "mutation@example.invalid",
            "GIT_COMMITTER_NAME": "mutation",
            "GIT_COMMITTER_EMAIL": "mutation@example.invalid",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(root),
        },
    )


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    """A tiny committed repository to freeze, package and corrupt."""
    root = tmp_path / "mini"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "README.md").write_text("mutation fixture\n", encoding="utf-8")
    _git(root, "init", "--quiet")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "fixture")
    return root


def _synthetic_registry(tmp_path: Path) -> Registry:
    document = {
        "schema": "epd2.infra01.check-registry/1",
        "registry_version": "0.0.1-mutation",
        "stages": [
            {
                "id": "verify-backend",
                "checks": [
                    {
                        "id": "backend.pytest",
                        "kind": "command",
                        "mandatory": True,
                        "command": ["true"],
                        "expects": {"parsers": [{"type": "pytest", "min": 1}]},
                    },
                    {
                        "id": "backend.mandatory-extra",
                        "kind": "command",
                        "mandatory": True,
                        "command": ["true"],
                        "expects": {},
                    },
                ],
            }
        ],
    }
    target = tmp_path / "mutation_registry.json"
    target.write_text(json.dumps(document), encoding="utf-8")
    return load_registry(target)


def _identity(run_id: str = "cafe" * 8, commit: str = "d0d0" * 10) -> CandidateIdentity:
    return CandidateIdentity(
        run_id=run_id,
        started_at="2026-08-31T00:00:00+00:00",
        git_commit=commit,
        git_tree="beef" * 10,
        git_dirty=False,
        dirty_paths=[],
        repository_version="0.16.0",
        canon_version="0.8.0",
        versions={"python.REPOSITORY_VERSION": "0.16.0", "python.CANON_VERSION": "0.8.0"},
        lock_hashes={"uv.lock": "1" * 64},
        platform="mutation-fixture",
        python_version="3.12",
    )


def _write_log(log_dir: Path, check_id: str, body: str) -> tuple[str, str]:
    log_dir.mkdir(parents=True, exist_ok=True)
    name = f"{check_id.replace('/', '_')}.log"
    path = log_dir / name
    path.write_text(body, encoding="utf-8")
    return name, sha256_file(path)


def _synthetic_run(tmp_path: Path, registry: Registry) -> Path:
    """A complete, internally consistent PASS run to corrupt."""
    run_id = "cafe" * 8
    run_dir = tmp_path / f"run-{run_id}"
    log_dir = run_dir / "logs"
    results: list[CheckResult] = []

    pytest_log, pytest_sha = _write_log(log_dir, "backend.pytest", "==== 5 passed in 0.10s ====\n")
    results.append(
        CheckResult(
            check_id="backend.pytest",
            stage_id="verify-backend",
            state="PASS",
            exit_code=0,
            started_at="2026-08-31T00:00:01+00:00",
            finished_at="2026-08-31T00:00:02+00:00",
            log_file=pytest_log,
            log_sha256=pytest_sha,
            test_counts={"pytest": 5},
        )
    )
    extra_log, extra_sha = _write_log(log_dir, "backend.mandatory-extra", "ok\n")
    results.append(
        CheckResult(
            check_id="backend.mandatory-extra",
            stage_id="verify-backend",
            state="PASS",
            exit_code=0,
            started_at="2026-08-31T00:00:03+00:00",
            finished_at="2026-08-31T00:00:04+00:00",
            log_file=extra_log,
            log_sha256=extra_sha,
        )
    )
    manifest = build_manifest(
        identity=_identity(run_id=run_id),
        tools={"git": "git version 2.x"},
        registry=registry,
        results=results,
        finished_at="2026-08-31T00:00:05+00:00",
        verdict="PASS",
        evidence_files={},
        freeze_tree_digest="f" * 64,
        final_archive_sha256=None,
        unresolved=[],
    )
    emit_manifest(run_dir, manifest)
    assert verify_evidence(run_dir, registry) == []
    return run_dir


def _codes_from_evidence(run_dir: Path, registry: Registry) -> set[str]:
    return {finding.code for finding in verify_evidence(run_dir, registry)}


def _package_fixture(mini_repo: Path, tmp_path: Path) -> tuple[Path, FreezeInventory]:
    inventory = take_inventory(mini_repo)
    additions = {
        "ACCEPTANCE/FREEZE-INVENTORY.json": json.dumps(inventory.as_document()).encode(),
        "SHA256SUMS.txt": b"placeholder\n",
    }
    archive = tmp_path / "candidate.zip"
    result = build_archive(
        mini_repo, inventory, archive, ARCHIVE_ROOT, additions, allowlist=_ALLOWLIST
    )
    assert result.findings == []
    return archive, inventory


# -- M01 remove mandatory evidence ----------------------------------------


def test_m01_removed_evidence_is_detected(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    (run_dir / "logs/backend.pytest.log").unlink()
    assert codes.EVIDENCE_MISSING in _codes_from_evidence(run_dir, registry)


# -- M02 replace PASS log with another run's PASS log ----------------------


def test_m02_foreign_pass_log_is_detected(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    foreign_registry = _synthetic_registry(foreign)
    foreign_run = _synthetic_run(foreign, foreign_registry)
    # the foreign run passed too, but its log bytes differ (different content)
    (foreign_run / "logs/backend.pytest.log").write_text(
        "==== 5 passed in 0.42s ==== (other commit)\n", encoding="utf-8"
    )
    shutil.copyfile(foreign_run / "logs/backend.pytest.log", run_dir / "logs/backend.pytest.log")
    assert codes.EVIDENCE_HASH_MISMATCH in _codes_from_evidence(run_dir, registry)


def test_m02b_commit_binding_rejects_other_commits_evidence(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    findings = verify_evidence(run_dir, registry, expected_git_commit="1111" * 10)
    assert codes.COMMIT_MISMATCH in {finding.code for finding in findings}


# -- M03 modify one frozen artifact byte ----------------------------------


def test_m03_frozen_artifact_byte_flip_is_detected(tmp_path: Path) -> None:
    artifact = tmp_path / "frozen/EPD2-CRYPTO-1.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b'{"profile": "EPD2-CRYPTO-1"}\n')
    pins = {"frozen/EPD2-CRYPTO-1.json": sha256_file(artifact)}
    assert verify_tree(tmp_path, pins) == []
    data = bytearray(artifact.read_bytes())
    data[0] ^= 0x01
    artifact.write_bytes(bytes(data))
    findings = verify_tree(tmp_path, pins)
    assert [finding.code for finding in findings] == [codes.FROZEN_ARTIFACT_MISMATCH]


# -- M04 insert forbidden cache directory ---------------------------------


def test_m04_forbidden_cache_directory_in_archive_is_detected(
    mini_repo: Path, tmp_path: Path
) -> None:
    archive, _ = _package_fixture(mini_repo, tmp_path)
    with zipfile.ZipFile(archive, "a") as bundle:
        bundle.writestr(f"{ARCHIVE_ROOT}/src/__pycache__/module.cpython-312.pyc", b"\0")
    found = {finding.code for finding in scan_archive(archive, allowlist=_ALLOWLIST)}
    assert codes.FORBIDDEN_PATH in found


# -- M05 alter one source file after testing ------------------------------


def test_m05_source_change_between_freeze_and_packaging_is_refused(
    mini_repo: Path, tmp_path: Path
) -> None:
    inventory = take_inventory(mini_repo)
    (mini_repo / "src/module.py").write_text("VALUE = 2\n", encoding="utf-8")
    archive = tmp_path / "candidate.zip"
    result = build_archive(mini_repo, inventory, archive, ARCHIVE_ROOT, {}, allowlist=_ALLOWLIST)
    assert [finding.code for finding in result.findings] == [codes.TREE_MUTATION_AFTER_FREEZE]
    assert not archive.exists(), "a refused package must not leave an archive behind"


# -- M06 alter one source file inside the ZIP only ------------------------


def test_m06_tamper_inside_zip_only_is_detected(mini_repo: Path, tmp_path: Path) -> None:
    archive, inventory = _package_fixture(mini_repo, tmp_path)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(tampered, "w") as target:
        for info in source.infolist():
            data = source.read(info)
            if info.filename == f"{ARCHIVE_ROOT}/src/module.py":
                data = b"VALUE = 666\n"
            target.writestr(info.filename, data)
    findings = verify_archive_against_inventory(
        tampered, ARCHIVE_ROOT, inventory, allowlist=_ALLOWLIST
    )
    assert codes.ARCHIVE_BYTE_MISMATCH in {finding.code for finding in findings}


# -- M07 fake a test count -------------------------------------------------


def test_m07_faked_test_count_is_detected(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    manifest = load_json(run_dir / "EXECUTION-MANIFEST.json")
    for result in manifest["results"]:
        if result["check_id"] == "backend.pytest":
            result["test_counts"]["pytest"] = 5000
    manifest.pop("manifest_sha256")
    write_canonical_json(run_dir / "EXECUTION-MANIFEST.json", seal_document(manifest))
    assert codes.TEST_COUNT_MISMATCH in _codes_from_evidence(run_dir, registry)


# -- M08 suppress a mandatory command -------------------------------------


def test_m08_suppressed_mandatory_command_is_detected(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    manifest = load_json(run_dir / "EXECUTION-MANIFEST.json")
    manifest["results"] = [
        result for result in manifest["results"] if result["check_id"] != "backend.mandatory-extra"
    ]
    manifest.pop("manifest_sha256")
    write_canonical_json(run_dir / "EXECUTION-MANIFEST.json", seal_document(manifest))
    assert codes.MANDATORY_CHECK_MISSING in _codes_from_evidence(run_dir, registry)


# -- M09 exit code 0 with missing expected output -------------------------


def test_m09_exit_zero_with_missing_output_fails(tmp_path: Path) -> None:
    check = Check(
        check_id="unit.sentinel",
        stage_id="unit",
        title="sentinel",
        kind="command",
        mandatory=True,
        command=("true",),
        timeout_seconds=10,
        expects=Expectation(sentinel=r"OK: all \d+ checks passed", parsers=()),
    )
    result = evaluate_output(check, 0, "")
    assert result.state == "FAIL"
    assert codes.EXPECTED_OUTPUT_MISSING in result.detector_codes


# -- M10 inject candidate secret material ---------------------------------


def test_m10_injected_secret_in_archive_is_detected(mini_repo: Path, tmp_path: Path) -> None:
    token = "AKIA" + "ZZZZZZZZZZZZZZZZ"
    (mini_repo / "src/config.py").write_text(f'aws_access_key = "{token}"\n', encoding="utf-8")
    _git(mini_repo, "add", ".")
    _git(mini_repo, "commit", "--quiet", "-m", "inject")
    archive, _ = _package_fixture(mini_repo, tmp_path)
    hits = secrets_scan_archive(archive, allowed=set())
    assert {hit.code for hit in hits} == {codes.SECRET_DETECTED}


# -- M11 mismatch repository/canon version --------------------------------


def _write_version_fixture(root: Path, ts_repo_version: str) -> None:
    py_dir = root / "packages/python/epd2-core/src/epd2_core"
    ts_dir = root / "packages/typescript/epd2-types/src"
    canon_dir = root / "docs/canonical"
    for directory in (py_dir, ts_dir, canon_dir, root / "docs/roadmap"):
        directory.mkdir(parents=True, exist_ok=True)
    (py_dir / "version.py").write_text(
        'CANON_VERSION = "0.8.0"\nREPOSITORY_VERSION = "0.16.0"\n', encoding="utf-8"
    )
    (ts_dir / "version.ts").write_text(
        f'export const CANON_VERSION = "0.8.0";\n'
        f'export const REPOSITORY_VERSION = "{ts_repo_version}";\n',
        encoding="utf-8",
    )
    (canon_dir / "canon-version.json").write_text(
        json.dumps({"canon_version": "0.8.0"}), encoding="utf-8"
    )
    (root / "CHANGELOG.md").write_text("## [0.16.0] - fixture\n", encoding="utf-8")
    for name in (
        "EPD2_PROJECT_ENTRYPOINT.md",
        "EPD2_PROGRAM_CONTROL_REGISTER.md",
        "EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
    ):
        (root / "docs/roadmap" / name).write_text("fixture\n", encoding="utf-8")


def _governance_tracked(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_m11_version_mismatch_is_detected(tmp_path: Path) -> None:
    _write_version_fixture(tmp_path, ts_repo_version="0.99.0")
    findings = verify_governance(tmp_path, _governance_tracked(tmp_path))
    assert codes.VERSION_MISMATCH in {finding.code for finding in findings}


# -- M12 mismatch lock-file hash ------------------------------------------


def test_m12_lock_hash_mismatch_is_detected(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text("version = 1\n", encoding="utf-8")
    recorded = {"uv.lock": sha256_file(lock)}
    assert lock_mismatches(tmp_path, recorded) == []
    lock.write_text("version = 1\n# regenerated\n", encoding="utf-8")
    findings = lock_mismatches(tmp_path, recorded)
    assert findings and all(f.startswith(codes.LOCK_HASH_MISMATCH) for f in findings)


# -- M13 change manifest after sealing ------------------------------------


def test_m13_manifest_edit_after_seal_is_detected(tmp_path: Path) -> None:
    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    manifest = load_json(run_dir / "EXECUTION-MANIFEST.json")
    manifest["verdict"] = "PASS_WITH_ENVIRONMENT_LIMITATION"
    write_canonical_json(run_dir / "EXECUTION-MANIFEST.json", manifest)
    assert _codes_from_evidence(run_dir, registry) == {codes.MANIFEST_INTEGRITY_FAILURE}


# -- M14 add undeclared archive entry -------------------------------------


def test_m14_undeclared_archive_entry_is_detected(mini_repo: Path, tmp_path: Path) -> None:
    archive, inventory = _package_fixture(mini_repo, tmp_path)
    with zipfile.ZipFile(archive, "a") as bundle:
        bundle.writestr(f"{ARCHIVE_ROOT}/EXTRA-UNDECLARED.txt", "smuggled\n")
    findings = verify_archive_against_inventory(
        archive, ARCHIVE_ROOT, inventory, allowlist=_ALLOWLIST
    )
    assert codes.UNDECLARED_ARCHIVE_ENTRY in {finding.code for finding in findings}


# -- M15 duplicate archive path -------------------------------------------


@pytest.mark.filterwarnings("ignore:Duplicate name:UserWarning")
def test_m15_duplicate_archive_path_is_detected(tmp_path: Path) -> None:
    archive = tmp_path / "dup.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{ARCHIVE_ROOT}/src/module.py", "VALUE = 1\n")
        bundle.writestr(f"{ARCHIVE_ROOT}/src/module.py", "VALUE = 2\n")
    found = {finding.code for finding in scan_archive(archive, allowlist=_ALLOWLIST)}
    assert codes.DUPLICATE_ARCHIVE_PATH in found


# -- M16 introduce an unauthorized second canonical register ---------------


def test_m16_second_canonical_register_is_detected(tmp_path: Path) -> None:
    _write_version_fixture(tmp_path, ts_repo_version="0.16.0")
    rogue = tmp_path / "docs/packs/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text("competing register\n", encoding="utf-8")
    findings = verify_governance(tmp_path, _governance_tracked(tmp_path))
    assert codes.COMPETING_REGISTER in {finding.code for finding in findings}


# -- no shared poison marker ----------------------------------------------


def test_every_mutation_class_has_its_own_detector() -> None:
    detectors = list(EXPECTED_DETECTORS.values())
    assert len(detectors) == 16
    assert len(set(detectors)) == 16, (
        "mutation classes share a detector code; independent coverage claims "
        "would be inflated by a shared poison marker"
    )


# -- emitted manifest conforms to the governed schema ----------------------


def test_emitted_manifest_validates_against_execution_manifest_schema(tmp_path: Path) -> None:
    import jsonschema

    registry = _synthetic_registry(tmp_path)
    run_dir = _synthetic_run(tmp_path, registry)
    schema = load_json(
        Path(__file__).resolve().parents[2]
        / "scripts/acceptance/schemas/execution_manifest.schema.json"
    )
    manifest = load_json(run_dir / "EXECUTION-MANIFEST.json")
    jsonschema.Draft202012Validator(schema).validate(manifest)
