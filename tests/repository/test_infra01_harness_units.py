"""INFRA-01 acceptance-harness unit coverage.

Behavioural checks of the harness building blocks: canonical sealing,
registry integrity, fail-closed executor semantics, hygiene and secret
detectors, frozen-artifact pins, deployment-manifest validation and the
runtime readiness contract. The dedicated corruption-class coverage lives in
``test_infra01_mutation_suite.py``.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from scripts.acceptance import codes
from scripts.acceptance.canonical import (
    canonical_json_bytes,
    seal_document,
    verify_sealed_document,
)
from scripts.acceptance.deployment_manifest import validate_manifest
from scripts.acceptance.executor import evaluate_output, parse_test_counts, strip_ansi
from scripts.acceptance.frozen import load_pins, verify_tree
from scripts.acceptance.hygiene import scan_archive, scan_tree
from scripts.acceptance.readiness import MANDATORY_DIMENSIONS, evaluate
from scripts.acceptance.registry import Check, Expectation, load_registry
from scripts.acceptance.secrets_scan import (
    load_allowlist,
    sanitize_evidence,
    scan_bytes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _command_check(sentinel: str | None = None, parsers: tuple[tuple[str, int], ...] = ()) -> Check:
    return Check(
        check_id="unit.check",
        stage_id="unit",
        title="unit",
        kind="command",
        mandatory=True,
        command=("true",),
        timeout_seconds=10,
        expects=Expectation(sentinel=sentinel, parsers=parsers),
    )


# -- canonical serialization ----------------------------------------------


def test_canonical_serialization_is_deterministic() -> None:
    first = canonical_json_bytes({"b": 1, "a": [2, 1]})
    second = canonical_json_bytes({"a": [2, 1], "b": 1})
    assert first == second
    assert first.endswith(b"\n")


def test_sealed_document_round_trip() -> None:
    sealed = seal_document({"x": 1, "nested": {"y": [1, 2]}})
    assert verify_sealed_document(sealed)


# -- registry --------------------------------------------------------------


def test_live_registry_is_internally_consistent() -> None:
    registry = load_registry()
    assert registry.problems == []
    check_ids = [check.check_id for check in registry.all_checks()]
    assert len(check_ids) == len(set(check_ids))
    assert registry.mandatory_check_ids(), "a registry without mandatory checks is meaningless"
    stage_ids = [stage.stage_id for stage in registry.stages]
    for required_stage in (
        "bootstrap",
        "verify-governance",
        "verify-repository",
        "verify-dependencies",
        "verify-backend",
        "verify-frontend",
        "verify-build",
        "verify-browser",
        "verify-accessibility",
        "verify-visual",
        "verify-secrets",
        "verify-frozen-artifacts",
        "verify-evidence",
        "freeze",
        "package",
        "verify-package",
        "emit-manifest",
    ):
        assert required_stage in stage_ids, f"canonical stage {required_stage} missing"


def test_registry_detects_duplicate_and_malformed_checks(tmp_path: Path) -> None:
    bad = {
        "schema": "epd2.infra01.check-registry/1",
        "registry_version": "0.0.1",
        "stages": [
            {
                "id": "s1",
                "checks": [
                    {"id": "dup", "kind": "command", "command": ["true"]},
                    {"id": "dup", "kind": "command", "command": ["true"]},
                    {"id": "no-command", "kind": "command"},
                    {"id": "weird", "kind": "wat"},
                ],
            },
            {"id": "s1", "checks": []},
        ],
    }
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(bad), encoding="utf-8")
    registry = load_registry(target)
    joined = "\n".join(registry.problems)
    assert "duplicate check id" in joined
    assert "without a command" in joined
    assert "unknown check kind" in joined
    assert "duplicate stage id" in joined
    assert "has no checks" in joined


# -- executor fail-closed semantics ---------------------------------------


def test_nonzero_exit_fails() -> None:
    result = evaluate_output(_command_check(), 3, "everything looked fine")
    assert result.state == "FAIL"


def test_pass_requires_declared_sentinel() -> None:
    check = _command_check(sentinel="OK: all good")
    assert evaluate_output(check, 0, "OK: all good\n").state == "PASS"


def test_parser_counts_survive_ansi_noise() -> None:
    noisy = "\x1b[2m Tests \x1b[22m \x1b[1m\x1b[32m342 passed\x1b[39m\x1b[22m (342)"
    assert strip_ansi(noisy) == " Tests  342 passed (342)"
    passed, failed = parse_test_counts("vitest", noisy)
    assert passed == 342
    assert failed is False


def test_pytest_failure_marker_wins_over_exit_code() -> None:
    check = _command_check(parsers=(("pytest", 1),))
    result = evaluate_output(check, 0, "1 failed, 100 passed in 3.21s")
    assert result.state == "FAIL"


def test_no_tests_ran_is_failure() -> None:
    check = _command_check(parsers=(("pytest", 1),))
    result = evaluate_output(check, 0, "no tests ran in 0.01s")
    assert result.state == "FAIL"


# -- hygiene ---------------------------------------------------------------


def test_tree_scan_flags_cache_and_nested_repository(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src/__pycache__").mkdir()
    (tmp_path / "src/__pycache__/ok.cpython-312.pyc").write_bytes(b"\0\0")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor/.git").mkdir()
    found = {finding.code for finding in scan_tree(tmp_path)}
    assert codes.FORBIDDEN_PATH in found
    assert codes.NESTED_REPOSITORY in found


def test_archive_scan_flags_machine_local_and_unsafe_paths(tmp_path: Path) -> None:
    archive = tmp_path / "candidate.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("ROOT/ok.txt", "fine")
        bundle.writestr("ROOT/C:\\Users\\dev\\leak.txt", "oops")
        bundle.writestr("ROOT/../escape.txt", "oops")
    found = {finding.code for finding in scan_archive(archive)}
    assert codes.MACHINE_LOCAL_PATH in found
    assert codes.UNSAFE_ARCHIVE_PATH in found


# -- frozen artifacts ------------------------------------------------------


def test_all_frozen_pins_match_this_tree() -> None:
    assert verify_tree(REPO_ROOT, load_pins()) == []


# -- secrets ---------------------------------------------------------------


def test_secret_detectors_fire_and_allowlist_is_narrow() -> None:
    aws_line = b"aws_key = 'AKIA" + b"ABCDEFGHIJKLMNOP'\n"
    hits = scan_bytes("config.py", aws_line, set())
    assert [hit.detector for hit in hits] == ["aws-access-key-id"]
    allowed = {("config.py", "aws-access-key-id", hits[0].line_sha256)}
    assert scan_bytes("config.py", aws_line, allowed) == []
    assert scan_bytes("other.py", aws_line, allowed), "allowlist entries must be path-exact"


def test_live_allowlist_entries_still_match_their_lines() -> None:
    allowed = load_allowlist()
    assert allowed, "allowlist unexpectedly empty"
    for path, detector, line_sha in sorted(allowed):
        target = REPO_ROOT / path
        assert target.is_file(), f"allowlisted file vanished: {path}"
        hits_without_allow = scan_bytes(path, target.read_bytes(), set())
        matching = {(hit.path, hit.detector, hit.line_sha256) for hit in hits_without_allow}
        assert (path, detector, line_sha) in matching, (
            f"stale allowlist entry: {path} / {detector} — the governed line no longer "
            "exists, so the entry must be removed rather than kept as a blanket pass"
        )


def test_public_reference_crypto_material_is_not_flagged() -> None:
    pins = load_pins()
    rels = sorted(pins)
    hits = []
    for rel in rels:
        hits.extend(scan_bytes(rel, (REPO_ROOT / rel).read_bytes(), set()))
    assert hits == [], "public governed reference material must not trip the secret gate"


def test_evidence_sanitation_detects_auth_headers(tmp_path: Path) -> None:
    log = tmp_path / "check.log"
    log.write_text("request ok\nAuthorization: Bearer abcdef123456789\n", encoding="utf-8")
    hits = sanitize_evidence(tmp_path)
    assert any(hit.code == codes.EVIDENCE_SANITATION_FAILURE for hit in hits)


# -- deployment manifest (FIR-REL-001 foundation) --------------------------


def _manifest_document(revisions: tuple[str, str], mode: str) -> dict[str, Any]:
    def component(name: str, revision: str) -> dict[str, Any]:
        return {
            "name": name,
            "artifact_digest": "sha256:" + "a" * 64,
            "source_revision": revision,
            "dependency_lock_digest": "sha256:" + "b" * 64,
            "contract_versions": {"events": "0.8.0"},
            "configuration_version": "cfg-1",
            "migration_set": [],
        }

    return {
        "schema": "epd2.infra01.deployment-manifest/1",
        "manifest_id": "manifest-0001",
        "environment": "staging",
        "components": [
            component("gateway", revisions[0]),
            component("identity", revisions[1]),
        ],
        "compatibility": {"mode": mode},
        "sovereignty_profile": {
            "region": "eu-de",
            "jurisdiction": "DE/EU",
            "tenancy_isolation_class": "UNDECIDED",
            "data_residency_policy": "EU-only, provider-neutral, governed by FIR-INFRA-SOV-001",
            "operator_access_model": "governed separation of duties; no standing access",
            "key_custody_model": "governed by FIR-SEC-004 / FIR-TRUST-003; provider-neutral",
            "provider_role": "infrastructure adapter only; provider != trust assumption",
            "backup_location": "EU-only, declared per environment",
            "trust_assumptions": ["provider is outside the trust boundary"],
        },
        "approval": {"state": "draft", "authority": "EPD2 governance"},
    }


def test_uniform_deployment_manifest_validates() -> None:
    assert validate_manifest(_manifest_document(("a" * 40, "a" * 40), "uniform")) == []


def test_mixed_versions_without_matrix_fail_closed() -> None:
    findings = validate_manifest(_manifest_document(("a" * 40, "b" * 40), "uniform"))
    assert [finding.code for finding in findings] == [codes.COMPATIBILITY_NOT_DECLARED]


def test_mixed_versions_with_exact_matrix_entry_pass() -> None:
    document = _manifest_document(("a" * 40, "b" * 40), "mixed-by-declared-matrix")
    document["compatibility"]["matrix"] = [
        {
            "components": {"gateway": "a" * 40, "identity": "b" * 40},
            "evidence": "compat-suite run 42, both directions",
        }
    ]
    assert validate_manifest(document) == []


def test_mixed_versions_with_wrong_matrix_entry_fail() -> None:
    document = _manifest_document(("a" * 40, "b" * 40), "mixed-by-declared-matrix")
    document["compatibility"]["matrix"] = [
        {"components": {"gateway": "a" * 40, "identity": "c" * 40}, "evidence": "stale"}
    ]
    findings = validate_manifest(document)
    assert [finding.code for finding in findings] == [codes.COMPATIBILITY_NOT_DECLARED]


# -- readiness contract (FIR-READY-001 foundation) -------------------------


def _readiness_document(**overrides: dict[str, Any]) -> dict[str, Any]:
    dimensions: dict[str, Any] = {
        name: {"status": "READY", "evidence": "unit fixture"} for name in MANDATORY_DIMENSIONS
    }
    dimensions.update(overrides)
    return {
        "schema": "epd2.infra01.readiness-contract/1",
        "service": "unit-service",
        "deployment_manifest_id": "manifest-0001",
        "evaluated_at": "2026-08-31T00:00:00+00:00",
        "dimensions": dimensions,
    }


def test_all_ready_dimensions_yield_ready() -> None:
    verdict = evaluate(_readiness_document())
    assert verdict.overall == "READY"
    assert verdict.findings == []


def test_unknown_dimension_fails_closed() -> None:
    verdict = evaluate(_readiness_document(key_trust_anchor_readiness={"status": "UNKNOWN"}))
    assert verdict.overall == "NOT_READY"
    assert verdict.findings[0].code == codes.READINESS_UNKNOWN_FAILS_CLOSED


def test_stale_projection_watermark_is_not_ready() -> None:
    verdict = evaluate(
        _readiness_document(
            projection_freshness={
                "status": "READY",
                "watermark": "000041",
                "required_position": "000107",
            }
        )
    )
    assert verdict.overall == "NOT_READY"
    assert any(finding.code == codes.READINESS_DIMENSION_NOT_READY for finding in verdict.findings)


def test_not_applicable_requires_governed_rule() -> None:
    verdict = evaluate(
        _readiness_document(restore_reconciliation_state={"status": "NOT_APPLICABLE_GOVERNED"})
    )
    assert verdict.overall == "NOT_READY"
    ok = evaluate(
        _readiness_document(
            restore_reconciliation_state={
                "status": "NOT_APPLICABLE_GOVERNED",
                "governed_rule": "no restore in scope for unit-service; OPS-governed",
            }
        )
    )
    assert ok.overall == "READY"


def test_declared_overall_cannot_contradict_evaluation() -> None:
    document = _readiness_document(dependency_readiness={"status": "NOT_READY"})
    document["overall"] = "READY"
    verdict = evaluate(document)
    assert verdict.overall == "NOT_READY"


# -- schemas and governed example instances --------------------------------


def test_live_check_registry_validates_against_its_schema() -> None:
    import jsonschema

    schema = json.loads(
        (REPO_ROOT / "scripts/acceptance/schemas/check_registry.schema.json").read_text()
    )
    document = json.loads((REPO_ROOT / "scripts/acceptance/check_registry.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(document)


def test_example_deployment_manifest_is_valid() -> None:
    document = json.loads(
        (REPO_ROOT / "docs/infra/INFRA-01/examples/deployment-manifest.example.json").read_text()
    )
    assert validate_manifest(document) == []


def test_example_readiness_contract_is_ready() -> None:
    document = json.loads(
        (REPO_ROOT / "docs/infra/INFRA-01/examples/readiness-contract.example.json").read_text()
    )
    verdict = evaluate(document)
    assert verdict.overall == "READY"
    assert verdict.findings == []
