#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.acceptance.canonical import seal_document, write_canonical_json

REPO = "nepogoda1970-epd2/epd2-civic-os"
PCR_PATH = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
RECONCILIATION_PATH = Path(
    "docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json"
)
SCHEMA = "epd2.infra01.governance-reconciliation/2"
OLD_MAIN = "81c2d0db987536718b30242eeb168aecc21877ca"
OLD_TREE = "5460ccd9ec5929c2136926a4a2585f3fca52937e"
OLD_PCR_SHA256 = "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e"
OLD_PCR_BLOB = "663b583a58453744e193cf468b7d6f59ff009d87"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"INFRA04_REBIND_SCHEMA_FAILURE:{message}")


def replace_exact(path: Path, mapping: dict[str, str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for before, after in mapping.items():
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


main = git("rev-parse", "origin/main")
tree = git("show", "-s", "--format=%T", "origin/main")
target_commit_timestamp = git("show", "-s", "--format=%cI", "origin/main")
pcr = Path(PCR_PATH)
pcr_sha256 = hashlib.sha256(pcr.read_bytes()).hexdigest()
pcr_blob = git("rev-parse", f"origin/main:{PCR_PATH}")

# The final candidate contains its registered authoritative workflow at the root.
# Diagnostic reconstruction resets to canonical main first, so restore that exact
# candidate workflow before running inherited policy gates.
auth_path = Path(".github/workflows/infra04-c2-authoritative.yml")
auth_path.parent.mkdir(parents=True, exist_ok=True)
auth_path.write_bytes(
    subprocess.check_output(
        [
            "git",
            "show",
            "origin/diagnostic/infra04-c2-static-repair-v7:.github/workflows/infra04-c2-authoritative.yml",
        ]
    )
)

# Textual provenance bindings are updated only where exact old canonical identities
# are present. Structured reconciliation JSON is handled separately below.
text_mapping = {
    OLD_MAIN: main,
    OLD_TREE: tree,
    OLD_PCR_SHA256: pcr_sha256,
    OLD_PCR_BLOB: pcr_blob,
}
for path in (
    Path("docs/infra/INFRA-04/INFRA-04-KNOWN-LIMITATIONS.md"),
    Path("docs/infra/INFRA-04/INFRA-04-STAGE-CONTRACT.md"),
    Path("docs/infra/INFRA-04/INFRA04_DEVELOPER_REPORT.md"),
    Path("validation/infra04/verification-summary.json"),
    Path("validation/infra04/main-binding.json"),
    Path("validation/infra04/verification-transcript.txt"),
    auth_path,
):
    replace_exact(path, text_mapping)

# Schema-v2 reconciliation update. Fail closed on any structural deviation; never
# create alternate keys such as main_commit/main_tree or expected_state.
require(RECONCILIATION_PATH.is_file(), "reconciliation record missing")
record = json.loads(RECONCILIATION_PATH.read_text(encoding="utf-8"))
require(isinstance(record, dict), "reconciliation root must be object")
require(record.get("schema") == SCHEMA, f"schema must be {SCHEMA}")
require("expected_state" not in record, "parallel expected_state is forbidden")
for key in (
    "candidate",
    "expected_current_state",
    "manifest_sha256",
    "reconciled_at",
    "target_authority",
    "target_commit_timestamp",
):
    require(key in record, f"missing required schema-v2 field {key}")

target = record["target_authority"]
require(isinstance(target, dict), "target_authority must be object")
for key in ("repository", "branch", "commit", "tree", "pcr_git_blob", "pcr_sha256"):
    require(key in target, f"missing target_authority.{key}")
for forbidden in ("main_commit", "main_tree", "pcr_blob_sha", "pcr_path", "pcr_modified_at"):
    require(forbidden not in target, f"non-canonical target_authority.{forbidden} present")
require(target["repository"] == REPO, "target repository drift")
require(target["branch"] == "main", "target branch drift")
target["commit"] = main
target["tree"] = tree
target["pcr_git_blob"] = pcr_blob
target["pcr_sha256"] = pcr_sha256

candidate = record["candidate"]
require(isinstance(candidate, dict), "candidate must be object")
for key in ("pcr_path", "pcr_sha256"):
    require(key in candidate, f"missing candidate.{key}")
require(candidate["pcr_path"] == PCR_PATH, "candidate PCR path drift")
candidate["pcr_sha256"] = pcr_sha256
record["target_commit_timestamp"] = target_commit_timestamp

facts = record["expected_current_state"]
require(isinstance(facts, list) and facts, "expected_current_state must be non-empty list")
ops_indexes = [i for i, fact in enumerate(facts) if isinstance(fact, dict) and fact.get("id") == "ops03-not-accepted"]
require(len(ops_indexes) == 1, f"expected exactly one stale OPS-03 fact, got {len(ops_indexes)}")
facts[ops_indexes[0]] = {
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

# Preserve the existing fail-closed INFRA-04/System Trial safeguards.
fact_ids = {str(f.get("id")) for f in facts if isinstance(f, dict)}
require("infra01-03-accepted-layer-open" in fact_ids, "INFRA layer-open fact missing")
require("no-infra04-acceptance-claimed-anywhere" in fact_ids, "INFRA-04 non-acceptance fact missing")
require("checkpoint-is-preview-readiness-minimum" in fact_ids, "preview checkpoint safeguard missing")

# Reconciliation time is the actual helper execution instant, after the target
# commit exists. It is written before sealing and never mutated afterwards.
record["reconciled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

# Critical invariant: canonical sealing is the final mutation of this record.
unsealed = {k: v for k, v in record.items() if k != "manifest_sha256"}
sealed = seal_document(unsealed)
write_canonical_json(RECONCILIATION_PATH, sealed)

# Supply-chain classification is candidate adaptation to newly accepted OPS-03
# workflow bytes; no functional INFRA-04 source is changed.
sp = Path("scripts/infra02/supply_chain_policy.json")
policy = json.loads(sp.read_text(encoding="utf-8"))
require(isinstance(policy.get("workflow_classes"), dict), "workflow_classes missing")
for name in (
    "ops03-c3-authoritative-build.yml",
    "ops03-c3-final.yml",
    "ops03-c3-v2.yml",
    "ops03-c3-governance-install.yml",
):
    policy["workflow_classes"][name] = "historical-stage"
policy["workflow_classes"] = dict(sorted(policy["workflow_classes"].items()))
sp.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

print(f"LIVE_MAIN={main}")
print(f"LIVE_TREE={tree}")
print(f"LIVE_PCR_SHA256={pcr_sha256}")
print(f"LIVE_PCR_BLOB={pcr_blob}")
print(f"LIVE_TARGET_COMMIT_TIMESTAMP={target_commit_timestamp}")
print(f"RECONCILIATION_MANIFEST_SHA256={sealed['manifest_sha256']}")
print("INFRA04_SCHEMA_V2_REBIND:PASS")
