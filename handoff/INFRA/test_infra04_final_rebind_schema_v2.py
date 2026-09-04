from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HELPER = Path(__file__).with_name("infra04-c2-final-rebind-v4.py")
SPEC = importlib.util.spec_from_file_location("infra04_final_rebind", HELPER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

from scripts.acceptance.canonical import load_json, seal_document, verify_sealed_document, write_canonical_json  # noqa: E402


def base_record() -> dict:
    return seal_document({
        "schema": mod.SCHEMA,
        "reconciled_at": "2026-09-04T09:11:00+00:00",
        "target_commit_timestamp": "2026-09-04T08:03:25+00:00",
        "note": "fixture",
        "target_authority": {
            "repository": mod.REPO,
            "branch": "main",
            "commit": "81c2d0db987536718b30242eeb168aecc21877ca",
            "tree": "5460ccd9ec5929c2136926a4a2585f3fca52937e",
            "pcr_git_blob": "663b583a58453744e193cf468b7d6f59ff009d87",
            "pcr_sha256": "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e",
        },
        "candidate": {"pcr_path": mod.PCR_PATH, "pcr_sha256": "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e"},
        "expected_current_state": [
            {"id": "ops03-not-accepted", "region": "layer_table", "must_include": ["OPS-01 ACCEPTED / CLOSED", "OPS-02 ACCEPTED / CLOSED", "OPS-03 QUALIFICATION ELIGIBLE"], "must_exclude": ["OPS-03 ACCEPTED / CLOSED"]},
            {"id": "checkpoint-is-preview-readiness-minimum", "region": "immediate_execution", "must_include": ["INFRA/OPS PREVIEW-READINESS MINIMUM"], "must_exclude": ["INFRA-04 = ACCEPTED"]},
            {"id": "no-infra04-acceptance-claimed-anywhere", "region": "immediate_execution", "must_include": [], "must_exclude": ["INFRA-04 ACCEPTED / CLOSED", "INFRA LAYER CLOSED"]},
        ],
    })


def write_record(tmp_path: Path, record: dict | None = None) -> Path:
    path = tmp_path / "record.json"
    write_canonical_json(path, record or base_record())
    return path


def rebind(path: Path) -> dict:
    return mod.rebind_reconciliation(
        path,
        main_commit="7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5",
        main_tree="64447ec51a0f8e2cb4bbf8819ecafafd760c37fd",
        pcr_git_blob="e6bebf6051341d5577fa154a0a93da6e726679ba",
        pcr_sha256="4bce151f0c50c53a99c9e132e21cc5652e8eca6c331f540bc428ea188a384f0b",
        target_commit_timestamp="2026-09-04T10:32:54+00:00",
        reconciled_at="2026-09-04T13:30:00+00:00",
    )


def test_authority_rebind_updates_all_schema_v2_identity_fields(tmp_path: Path) -> None:
    record = rebind(write_record(tmp_path))
    assert record["target_authority"] == {
        "repository": mod.REPO,
        "branch": "main",
        "commit": "7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5",
        "tree": "64447ec51a0f8e2cb4bbf8819ecafafd760c37fd",
        "pcr_git_blob": "e6bebf6051341d5577fa154a0a93da6e726679ba",
        "pcr_sha256": "4bce151f0c50c53a99c9e132e21cc5652e8eca6c331f540bc428ea188a384f0b",
    }
    assert record["candidate"]["pcr_sha256"] == record["target_authority"]["pcr_sha256"]
    assert record["target_commit_timestamp"] == "2026-09-04T10:32:54+00:00"


def test_ops03_transition_is_current_and_preview_remains_closed(tmp_path: Path) -> None:
    record = rebind(write_record(tmp_path))
    encoded = json.dumps(record, ensure_ascii=False)
    assert "OPS-03 QUALIFICATION ELIGIBLE" not in encoded
    fact = next(f for f in record["expected_current_state"] if f["id"] == "ops03-accepted-layer-open")
    assert "OPS-03 ACCEPTED / CLOSED" in fact["must_include"]
    assert "OPS LAYER OPEN" in fact["must_include"]
    assert "System Trial Preview is NOT OPENED" in fact["must_include"]
    checkpoint = next(f for f in record["expected_current_state"] if f["id"] == "checkpoint-is-preview-readiness-minimum")
    assert "only by a separate checkpoint-opening decision" in checkpoint["must_include"]
    assert "SYSTEM TRIAL PREVIEW = OPEN" in checkpoint["must_exclude"]


def test_reseal_accepts_preseal_mutation_and_detects_postseal_mutation(tmp_path: Path) -> None:
    path = write_record(tmp_path)
    record = load_json(path)
    record["note"] = "mutated before reseal"
    write_canonical_json(path, seal_document({k: v for k, v in record.items() if k != "manifest_sha256"}))
    assert verify_sealed_document(load_json(path))
    rebound = rebind(path)
    assert verify_sealed_document(rebound)
    rebound["note"] = "tampered after reseal"
    write_canonical_json(path, rebound)
    assert not verify_sealed_document(load_json(path))
    with pytest.raises(ValueError, match="SCHEMA_V2_INPUT_SEAL_INVALID"):
        mod.assert_schema_v2(load_json(path), require_valid_seal=True)


@pytest.mark.parametrize("mutator,pattern", [
    (lambda r: r["target_authority"].update({"main_commit": r["target_authority"].pop("commit")}), "SCHEMA_V2_TARGET_KEYS"),
    (lambda r: r.update({"expected_state": copy.deepcopy(r["expected_current_state"])}), "SCHEMA_V2_FORBIDDEN_TOP_LEVEL"),
    (lambda r: r.pop("target_commit_timestamp"), "SCHEMA_V2_MISSING_TOP_LEVEL"),
])
def test_wrong_or_parallel_schema_fields_fail_closed(tmp_path: Path, mutator, pattern: str) -> None:
    record = base_record()
    mutator(record)
    record = seal_document({k: v for k, v in record.items() if k != "manifest_sha256"})
    path = write_record(tmp_path, record)
    with pytest.raises(ValueError, match=pattern):
        rebind(path)
