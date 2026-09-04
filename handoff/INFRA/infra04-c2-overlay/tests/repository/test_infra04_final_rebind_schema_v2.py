from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.acceptance.canonical import verify_sealed_document, write_canonical_json
from scripts.acceptance.governance import RECONCILIATION_FILE, verify_freshness
from scripts.infra04.final_rebind_schema_v2 import (
    PCR_PATH,
    RebindSchemaError,
    rebind_reconciliation_v2,
)

NEW = {
    "repository": "nepogoda1970-epd2/epd2-civic-os",
    "commit": "7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5",
    "tree": "64447ec51a0f8e2cb4bbf8819ecafafd760c37fd",
    "pcr_git_blob": "e6bebf6051341d5577fa154a0a93da6e726679ba",
    "pcr_sha256": "4bce151f0c50c53a99c9e132e21cc5652e8eca6c331f540bc428ea188a384f0b",
    "target_commit_timestamp": "2026-09-04T10:32:54+00:00",
    "reconciled_at": "2026-09-04T13:30:00+00:00",
}


def _source(pcr_sha256: str | None = None) -> dict[str, object]:
    pcr_sha = pcr_sha256 or NEW["pcr_sha256"]
    return {
        "schema": "epd2.infra01.governance-reconciliation/2",
        "candidate": {"pcr_path": PCR_PATH, "pcr_sha256": "0" * 64},
        "expected_current_state": [
            {
                "id": "infra01-03-accepted-layer-open",
                "region": "primary_position",
                "must_include": [
                    "INFRA-01 = ACCEPTED / CLOSED",
                    "INFRA-02 = ACCEPTED / CLOSED",
                    "INFRA-03 = ACCEPTED / CLOSED",
                    "INFRA = OPEN / NOT CLOSED",
                ],
                "must_exclude": ["INFRA-04 = ACCEPTED", "INFRA = CLOSED"],
            },
            {
                "id": "ops03-not-accepted",
                "region": "layer_table",
                "must_include": [
                    "OPS-01 ACCEPTED / CLOSED",
                    "OPS-02 ACCEPTED / CLOSED",
                    "OPS-03 QUALIFICATION ELIGIBLE",
                ],
                "must_exclude": ["OPS-03 ACCEPTED / CLOSED"],
            },
            {
                "id": "checkpoint-is-preview-readiness-minimum",
                "region": "immediate_execution",
                "must_include": ["INFRA/OPS PREVIEW-READINESS MINIMUM"],
                "must_exclude": ["INFRA-04 is therefore `ACCEPTED", "INFRA-04 = ACCEPTED"],
            },
            {
                "id": "no-infra04-acceptance-claimed-anywhere",
                "region": "immediate_execution",
                "must_include": [],
                "must_exclude": ["INFRA-04 ACCEPTED / CLOSED", "INFRA LAYER CLOSED"],
            },
        ],
        "manifest_sha256": "0" * 64,
        "note": "synthetic final-rebind regression fixture",
        "reconciled_at": "2026-09-04T09:11:00+00:00",
        "target_authority": {
            "repository": NEW["repository"],
            "branch": "main",
            "commit": "81c2d0db987536718b30242eeb168aecc21877ca",
            "tree": "5460ccd9ec5929c2136926a4a2585f3fca52937e",
            "pcr_git_blob": "663b583a58453744e193cf468b7d6f59ff009d87",
            "pcr_sha256": "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e",
        },
        "target_commit_timestamp": "2026-09-04T08:03:25+00:00",
    }


def _rebind(source: dict[str, object]) -> dict[str, object]:
    return rebind_reconciliation_v2(
        source,
        repository=NEW["repository"],
        commit=NEW["commit"],
        tree=NEW["tree"],
        pcr_git_blob=NEW["pcr_git_blob"],
        pcr_sha256=NEW["pcr_sha256"],
        target_commit_timestamp=NEW["target_commit_timestamp"],
        reconciled_at=NEW["reconciled_at"],
    )


def test_final_rebind_updates_all_exact_authority_fields() -> None:
    sealed = _rebind(_source())
    target = sealed["target_authority"]
    assert target["commit"] == NEW["commit"]
    assert target["tree"] == NEW["tree"]
    assert target["pcr_git_blob"] == NEW["pcr_git_blob"]
    assert target["pcr_sha256"] == NEW["pcr_sha256"]
    assert sealed["candidate"]["pcr_sha256"] == NEW["pcr_sha256"]
    assert sealed["target_commit_timestamp"] == NEW["target_commit_timestamp"]
    assert sealed["reconciled_at"] == NEW["reconciled_at"]
    assert verify_sealed_document(sealed)


def test_final_rebind_promotes_ops03_fact_without_closing_ops_or_preview() -> None:
    sealed = _rebind(_source())
    encoded = json.dumps(sealed, sort_keys=True)
    assert "OPS-03 QUALIFICATION ELIGIBLE" in encoded  # retained only as must_exclude
    facts = sealed["expected_current_state"]
    ops = next(f for f in facts if f["id"] == "ops03-accepted-closed-layer-open")
    assert "OPS-03 ACCEPTED / CLOSED" in ops["must_include"]
    assert "OPS LAYER OPEN" in ops["must_include"]
    assert "OPS LAYER CLOSED" in ops["must_exclude"]
    assert any(f["id"] == "no-infra04-acceptance-claimed-anywhere" for f in facts)
    assert any(f["id"] == "checkpoint-is-preview-readiness-minimum" for f in facts)


def test_reseal_passes_and_postseal_mutation_fails_integrity(tmp_path: Path) -> None:
    current_pcr = Path(PCR_PATH).read_bytes()
    current_sha = hashlib.sha256(current_pcr).hexdigest()
    source = _source(current_sha)
    sealed = rebind_reconciliation_v2(
        source,
        repository=NEW["repository"],
        commit=NEW["commit"],
        tree=NEW["tree"],
        pcr_git_blob=NEW["pcr_git_blob"],
        pcr_sha256=current_sha,
        target_commit_timestamp=NEW["target_commit_timestamp"],
        reconciled_at=NEW["reconciled_at"],
    )
    assert verify_sealed_document(sealed)

    root = tmp_path
    (root / PCR_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / PCR_PATH).write_bytes(current_pcr)
    record_path = root / RECONCILIATION_FILE
    write_canonical_json(record_path, sealed)
    assert not verify_freshness(root)

    tampered = copy.deepcopy(sealed)
    tampered["target_authority"]["tree"] = "f" * 40
    write_canonical_json(record_path, tampered)
    findings = verify_freshness(root)
    assert findings
    assert any(f.code == "RECONCILIATION_INTEGRITY_FAILURE" for f in findings)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r["target_authority"].update(
            {"main_commit": r["target_authority"].pop("commit")}
        ),
        lambda r: r.update({"expected_state": r["expected_current_state"]}),
        lambda r: r.pop("target_commit_timestamp"),
        lambda r: r["candidate"].pop("pcr_sha256"),
    ],
)
def test_schema_v2_wrong_or_missing_fields_fail_closed(mutator) -> None:
    source = _source()
    mutator(source)
    with pytest.raises(RebindSchemaError):
        _rebind(source)
