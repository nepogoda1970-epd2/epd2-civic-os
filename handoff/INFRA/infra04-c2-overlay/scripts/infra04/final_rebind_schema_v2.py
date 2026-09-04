from __future__ import annotations

from copy import deepcopy
from typing import Any

from scripts.acceptance.canonical import seal_document

SCHEMA = "epd2.infra01.governance-reconciliation/2"
PCR_PATH = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
REQUIRED_TARGET_KEYS = {
    "repository",
    "branch",
    "commit",
    "tree",
    "pcr_git_blob",
    "pcr_sha256",
}
FORBIDDEN_TARGET_KEYS = {
    "main_commit",
    "main_tree",
    "pcr_blob_sha",
    "pcr_path",
    "pcr_modified_at",
}


class RebindSchemaError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RebindSchemaError(message)


def rebind_reconciliation_v2(
    source: dict[str, Any],
    *,
    repository: str,
    commit: str,
    tree: str,
    pcr_git_blob: str,
    pcr_sha256: str,
    target_commit_timestamp: str,
    reconciled_at: str,
) -> dict[str, Any]:
    """Return a canonically sealed schema-v2 reconciliation bound to live authority.

    This function changes only stale authority/state facts. It fails closed on
    alternate field names or a structurally different record. The integrity
    digest is calculated after every governed mutation and is the final content
    mutation performed here.
    """
    record = deepcopy(source)
    _require(record.get("schema") == SCHEMA, f"schema must be {SCHEMA}")
    _require("expected_state" not in record, "parallel expected_state is forbidden")
    for key in (
        "candidate",
        "expected_current_state",
        "manifest_sha256",
        "reconciled_at",
        "target_authority",
        "target_commit_timestamp",
    ):
        _require(key in record, f"missing required schema-v2 field {key}")

    target = record["target_authority"]
    _require(isinstance(target, dict), "target_authority must be object")
    _require(REQUIRED_TARGET_KEYS.issubset(target), "canonical target_authority keys missing")
    _require(not (FORBIDDEN_TARGET_KEYS & set(target)), "non-canonical target_authority key present")
    _require(target["branch"] == "main", "target branch must remain main")
    target["repository"] = repository
    target["commit"] = commit
    target["tree"] = tree
    target["pcr_git_blob"] = pcr_git_blob
    target["pcr_sha256"] = pcr_sha256

    candidate = record["candidate"]
    _require(isinstance(candidate, dict), "candidate must be object")
    _require(candidate.get("pcr_path") == PCR_PATH, "candidate pcr_path drift")
    _require("pcr_sha256" in candidate, "candidate.pcr_sha256 missing")
    candidate["pcr_sha256"] = pcr_sha256
    record["target_commit_timestamp"] = target_commit_timestamp
    record["reconciled_at"] = reconciled_at

    facts = record["expected_current_state"]
    _require(isinstance(facts, list) and facts, "expected_current_state must be non-empty list")
    stale = [i for i, fact in enumerate(facts) if isinstance(fact, dict) and fact.get("id") == "ops03-not-accepted"]
    _require(len(stale) == 1, f"expected exactly one stale OPS-03 fact, got {len(stale)}")
    facts[stale[0]] = {
        "id": "ops03-accepted-closed-layer-open",
        "region": "layer_table",
        "must_include": [
            "OPS-01 ACCEPTED / CLOSED",
            "OPS-02 ACCEPTED / CLOSED",
            "OPS-03 ACCEPTED / CLOSED",
            "OPS LAYER OPEN",
        ],
        "must_exclude": [
            "OPS-03 QUALIFICATION ELIGIBLE",
            "OPS LAYER CLOSED",
        ],
    }

    fact_ids = {str(f.get("id")) for f in facts if isinstance(f, dict)}
    _require("infra01-03-accepted-layer-open" in fact_ids, "INFRA layer-open fact missing")
    _require("no-infra04-acceptance-claimed-anywhere" in fact_ids, "INFRA-04 non-acceptance fact missing")
    _require("checkpoint-is-preview-readiness-minimum" in fact_ids, "preview checkpoint safeguard missing")

    # Seal last. Callers must serialize this result without further mutation.
    return seal_document({k: v for k, v in record.items() if k != "manifest_sha256"})
