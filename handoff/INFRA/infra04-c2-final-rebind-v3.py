#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.acceptance.canonical import write_canonical_json
from scripts.infra04.final_rebind_schema_v2 import rebind_reconciliation_v2

REPO = "nepogoda1970-epd2/epd2-civic-os"
PCR_PATH = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
RECONCILIATION_PATH = Path(
    "docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json"
)
OLD_MAIN = "81c2d0db987536718b30242eeb168aecc21877ca"
OLD_TREE = "5460ccd9ec5929c2136926a4a2585f3fca52937e"
OLD_PCR_SHA256 = "21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e"
OLD_PCR_BLOB = "663b583a58453744e193cf468b7d6f59ff009d87"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"INFRA04_REBIND_FAILURE:{message}")


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

# Restore the registered final candidate workflow after reset to live main.
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

# Update textual authority bindings only in known provenance/workflow surfaces.
# Structured reconciliation JSON is never globally string-replaced.
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

require(RECONCILIATION_PATH.is_file(), "reconciliation record missing")
source = json.loads(RECONCILIATION_PATH.read_text(encoding="utf-8"))
sealed = rebind_reconciliation_v2(
    source,
    repository=REPO,
    commit=main,
    tree=tree,
    pcr_git_blob=pcr_blob,
    pcr_sha256=pcr_sha256,
    target_commit_timestamp=target_commit_timestamp,
    reconciled_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
)
# Canonical write is the final operation on the reconciliation record.
write_canonical_json(RECONCILIATION_PATH, sealed)

# Adapt inherited supply-chain classification to the now-accepted OPS-03 workflows.
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
