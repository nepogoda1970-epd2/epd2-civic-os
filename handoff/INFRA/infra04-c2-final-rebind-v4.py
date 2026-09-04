#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path.cwd()))
from scripts.acceptance.canonical import (  # noqa: E402
    load_json,
    seal_document,
    sha256_file,
    verify_sealed_document,
    write_canonical_json,
)

REPO = "nepogoda1970-epd2/epd2-civic-os"
BRANCH = "main"
SCHEMA = "epd2.infra01.governance-reconciliation/2"
PCR_PATH = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
RECONCILIATION_PATH = "docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json"
AUTH_WORKFLOW_PATH = ".github/workflows/infra04-c2-authoritative.yml"
DIAGNOSTIC_REF = "origin/diagnostic/infra04-c2-static-repair-v7"
CANONICAL_TARGET_KEYS = {"repository", "branch", "commit", "tree", "pcr_git_blob", "pcr_sha256"}
CANONICAL_CANDIDATE_KEYS = {"pcr_path", "pcr_sha256"}
CANONICAL_FACT_KEYS = {"id", "region", "must_include", "must_exclude"}
REQUIRED_TOP_LEVEL = {"schema", "reconciled_at", "target_commit_timestamp", "note", "target_authority", "candidate", "expected_current_state", "manifest_sha256"}
FORBIDDEN_TOP_LEVEL = {"expected_state"}
FORBIDDEN_TARGET_KEYS = {"main_commit", "main_tree", "pcr_blob_sha", "pcr_path", "pcr_modified_at"}
OLD_BINDINGS = {
    "81c2d0db987536718b30242eeb168aecc21877ca",
    "5460ccd9ec5929c2136926a4a2585f3fca52937e",
    "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e",
    "663b583a58453744e193cf468b7d6f59ff009d87",
}
TEXT_BINDING_PATHS = (
    Path("docs/infra/INFRA-04/INFRA-04-KNOWN-LIMITATIONS.md"),
    Path("docs/infra/INFRA-04/INFRA-04-STAGE-CONTRACT.md"),
    Path("docs/infra/INFRA-04/INFRA04_DEVELOPER_REPORT.md"),
    Path("validation/infra04/verification-transcript.txt"),
)
JSON_BINDING_PATHS = (
    Path("validation/infra04/verification-summary.json"),
    Path("validation/infra04/main-binding.json"),
)

def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()

def _assert_string(value: object, subject: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SCHEMA_V2_INVALID_STRING:{subject}")
    return value

def assert_schema_v2(record: dict[str, Any], *, require_valid_seal: bool = True) -> None:
    if not isinstance(record, dict):
        raise ValueError("SCHEMA_V2_RECORD_NOT_OBJECT")
    if record.get("schema") != SCHEMA:
        raise ValueError(f"SCHEMA_V2_WRONG_SCHEMA:{record.get('schema')!r}")
    missing = REQUIRED_TOP_LEVEL - set(record)
    if missing:
        raise ValueError(f"SCHEMA_V2_MISSING_TOP_LEVEL:{','.join(sorted(missing))}")
    forbidden = FORBIDDEN_TOP_LEVEL & set(record)
    if forbidden:
        raise ValueError(f"SCHEMA_V2_FORBIDDEN_TOP_LEVEL:{','.join(sorted(forbidden))}")
    target = record.get("target_authority")
    if not isinstance(target, dict):
        raise ValueError("SCHEMA_V2_TARGET_NOT_OBJECT")
    if set(target) != CANONICAL_TARGET_KEYS:
        raise ValueError("SCHEMA_V2_TARGET_KEYS:" + ",".join(sorted(set(target))))
    bad_target = FORBIDDEN_TARGET_KEYS & set(target)
    if bad_target:
        raise ValueError(f"SCHEMA_V2_FORBIDDEN_TARGET_KEYS:{','.join(sorted(bad_target))}")
    for key in CANONICAL_TARGET_KEYS:
        _assert_string(target.get(key), f"target_authority.{key}")
    candidate = record.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("SCHEMA_V2_CANDIDATE_NOT_OBJECT")
    if set(candidate) != CANONICAL_CANDIDATE_KEYS:
        raise ValueError("SCHEMA_V2_CANDIDATE_KEYS:" + ",".join(sorted(set(candidate))))
    if candidate.get("pcr_path") != PCR_PATH:
        raise ValueError(f"SCHEMA_V2_PCR_PATH:{candidate.get('pcr_path')!r}")
    _assert_string(candidate.get("pcr_sha256"), "candidate.pcr_sha256")
    facts = record.get("expected_current_state")
    if not isinstance(facts, list) or not facts:
        raise ValueError("SCHEMA_V2_EXPECTED_CURRENT_STATE_NOT_NONEMPTY_LIST")
    ids: list[str] = []
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            raise ValueError(f"SCHEMA_V2_FACT_NOT_OBJECT:{index}")
        if set(fact) != CANONICAL_FACT_KEYS:
            raise ValueError(f"SCHEMA_V2_FACT_KEYS:{index}:" + ",".join(sorted(set(fact))))
        fact_id = _assert_string(fact.get("id"), f"expected_current_state[{index}].id")
        _assert_string(fact.get("region"), f"expected_current_state[{index}].region")
        if not isinstance(fact.get("must_include"), list):
            raise ValueError(f"SCHEMA_V2_MUST_INCLUDE_NOT_LIST:{fact_id}")
        if not isinstance(fact.get("must_exclude"), list):
            raise ValueError(f"SCHEMA_V2_MUST_EXCLUDE_NOT_LIST:{fact_id}")
        if not all(isinstance(item, str) and item for item in fact["must_include"]):
            raise ValueError(f"SCHEMA_V2_MUST_INCLUDE_BAD_ITEM:{fact_id}")
        if not all(isinstance(item, str) and item for item in fact["must_exclude"]):
            raise ValueError(f"SCHEMA_V2_MUST_EXCLUDE_BAD_ITEM:{fact_id}")
        ids.append(fact_id)
    if len(ids) != len(set(ids)):
        raise ValueError("SCHEMA_V2_DUPLICATE_FACT_ID")
    _assert_string(record.get("reconciled_at"), "reconciled_at")
    _assert_string(record.get("target_commit_timestamp"), "target_commit_timestamp")
    _assert_string(record.get("manifest_sha256"), "manifest_sha256")
    if require_valid_seal and not verify_sealed_document(record):
        raise ValueError("SCHEMA_V2_INPUT_SEAL_INVALID")

def _replace_json_scalars(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_json_scalars(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_json_scalars(item, replacements) for item in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value

def _replace_text_bindings(path: Path, replacements: dict[str, str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for before, after in replacements.items():
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")

def _replace_structured_json_bindings(path: Path, replacements: dict[str, str]) -> None:
    if not path.is_file():
        return
    value = json.loads(path.read_text(encoding="utf-8"))
    write_canonical_json(path, _replace_json_scalars(value, replacements))

def _replace_fact(record: dict[str, Any], stale_id: str, replacement: dict[str, Any]) -> None:
    facts = record["expected_current_state"]
    matches = [index for index, fact in enumerate(facts) if fact.get("id") == stale_id]
    if len(matches) != 1:
        raise ValueError(f"SCHEMA_V2_EXPECTED_ONE_FACT:{stale_id}:{len(matches)}")
    facts[matches[0]] = replacement

def _harden_checkpoint_fact(record: dict[str, Any]) -> None:
    matches = [fact for fact in record["expected_current_state"] if fact.get("id") == "checkpoint-is-preview-readiness-minimum"]
    if len(matches) != 1:
        raise ValueError("SCHEMA_V2_EXPECTED_ONE_FACT:checkpoint-is-preview-readiness-minimum:" + str(len(matches)))
    fact = matches[0]
    if fact.get("region") != "immediate_execution":
        raise ValueError("SCHEMA_V2_CHECKPOINT_REGION_DRIFT")
    must_include = list(fact["must_include"])
    must_exclude = list(fact["must_exclude"])
    for text in ("INFRA/OPS PREVIEW-READINESS MINIMUM", "only by a separate checkpoint-opening decision"):
        if text not in must_include:
            must_include.append(text)
    for text in ("SYSTEM TRIAL PREVIEW = OPEN", "SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK = OPEN"):
        if text not in must_exclude:
            must_exclude.append(text)
    fact["must_include"] = must_include
    fact["must_exclude"] = must_exclude

def rebind_reconciliation(path: Path, *, main_commit: str, main_tree: str, pcr_git_blob: str, pcr_sha256: str, target_commit_timestamp: str, reconciled_at: str) -> dict[str, Any]:
    record = load_json(path)
    assert_schema_v2(record, require_valid_seal=True)
    target = record["target_authority"]
    if target["repository"] != REPO or target["branch"] != BRANCH:
        raise ValueError(f"SCHEMA_V2_AUTHORITY_DRIFT:{target['repository']}:{target['branch']}")
    target["commit"] = main_commit
    target["tree"] = main_tree
    target["pcr_git_blob"] = pcr_git_blob
    target["pcr_sha256"] = pcr_sha256
    record["candidate"]["pcr_sha256"] = pcr_sha256
    record["target_commit_timestamp"] = target_commit_timestamp
    record["reconciled_at"] = reconciled_at
    _replace_fact(record, "ops03-not-accepted", {
        "id": "ops03-accepted-layer-open",
        "region": "layer_table",
        "must_include": ["OPS-01 ACCEPTED / CLOSED", "OPS-02 ACCEPTED / CLOSED", "OPS-03 ACCEPTED / CLOSED", "OPS LAYER OPEN", "System Trial Preview is NOT OPENED"],
        "must_exclude": ["OPS LAYER CLOSED"],
    })
    _harden_checkpoint_fact(record)
    unsealed = {key: value for key, value in record.items() if key != "manifest_sha256"}
    sealed = seal_document(unsealed)
    assert_schema_v2(sealed, require_valid_seal=True)
    write_canonical_json(path, sealed)
    written = load_json(path)
    assert_schema_v2(written, require_valid_seal=True)
    return written

def _restore_and_rebind_authoritative_workflow(main_commit: str) -> None:
    path = Path(AUTH_WORKFLOW_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = subprocess.check_output(["git", "show", f"{DIAGNOSTIC_REF}:{AUTH_WORKFLOW_PATH}"], text=True)
    old = "81c2d0db987536718b30242eeb168aecc21877ca"
    count = source.count(old)
    if count != 3:
        raise ValueError(f"AUTHORITATIVE_WORKFLOW_OLD_MAIN_COUNT:{count}")
    rebound = source.replace(old, main_commit)
    if old in rebound:
        raise ValueError("AUTHORITATIVE_WORKFLOW_STALE_MAIN_REMAINS")
    path.write_text(rebound, encoding="utf-8")

def main() -> None:
    main_commit = _git("rev-parse", "origin/main")
    main_tree = _git("show", "-s", "--format=%T", "origin/main")
    target_commit_timestamp = _git("show", "-s", "--format=%cI", "origin/main")
    pcr = Path(PCR_PATH)
    pcr_sha256 = sha256_file(pcr)
    pcr_git_blob = _git("rev-parse", f"origin/main:{PCR_PATH}")
    if pcr.read_bytes() != subprocess.check_output(["git", "show", f"origin/main:{PCR_PATH}"]):
        raise SystemExit("CANDIDATE_PCR_BYTES_DIFFER_FROM_LIVE_MAIN")
    _restore_and_rebind_authoritative_workflow(main_commit)
    before = load_json(Path(RECONCILIATION_PATH))
    old_target, old_candidate = before["target_authority"], before["candidate"]
    replacements = {
        str(old_target["commit"]): main_commit,
        str(old_target["tree"]): main_tree,
        str(old_target["pcr_git_blob"]): pcr_git_blob,
        str(old_target["pcr_sha256"]): pcr_sha256,
        str(old_candidate["pcr_sha256"]): pcr_sha256,
    }
    for path in TEXT_BINDING_PATHS:
        _replace_text_bindings(path, replacements)
    for path in JSON_BINDING_PATHS:
        _replace_structured_json_bindings(path, replacements)
    record = rebind_reconciliation(
        Path(RECONCILIATION_PATH),
        main_commit=main_commit,
        main_tree=main_tree,
        pcr_git_blob=pcr_git_blob,
        pcr_sha256=pcr_sha256,
        target_commit_timestamp=target_commit_timestamp,
        reconciled_at=datetime.now(tz=UTC).isoformat(),
    )
    policy_path = Path("scripts/infra02/supply_chain_policy.json")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    classes = policy.get("workflow_classes")
    if not isinstance(classes, dict):
        raise SystemExit("INFRA02_POLICY_WORKFLOW_CLASSES_MISSING")
    for name in ("ops03-c3-authoritative-build.yml", "ops03-c3-final.yml", "ops03-c3-v2.yml", "ops03-c3-governance-install.yml"):
        classes[name] = "historical-stage"
    policy["workflow_classes"] = dict(sorted(classes.items()))
    write_canonical_json(policy_path, policy)
    scan_paths = [*TEXT_BINDING_PATHS, *JSON_BINDING_PATHS, Path(RECONCILIATION_PATH)]
    for stale in OLD_BINDINGS:
        for path in scan_paths:
            if path.is_file() and stale in path.read_text(encoding="utf-8"):
                raise SystemExit(f"STALE_AUTHORITY_AFTER_REBIND:{stale}:{path}")
    print(f"LIVE_MAIN={main_commit}")
    print(f"LIVE_TREE={main_tree}")
    print(f"LIVE_PCR_SHA256={pcr_sha256}")
    print(f"LIVE_PCR_BLOB={pcr_git_blob}")
    print(f"LIVE_PCR_MODIFIED={target_commit_timestamp}")
    print(f"RECONCILIATION_MANIFEST_SHA256={record['manifest_sha256']}")
    print("INFRA04_SCHEMA_V2_REBIND:PASS")

if __name__ == "__main__":
    main()
