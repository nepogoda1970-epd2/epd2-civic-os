from __future__ import annotations

import argparse
import json
from pathlib import Path

OLD_INV = "docs/api/API-02/API02_C11_TO_C12_CORRECTION_INVENTORY.json"
NEW_INV = "docs/api/API-02/API02_C12_TO_C13_CORRECTION_INVENTORY.json"


def rewrite_evidence_path(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key == "evidence_path" and item == OLD_INV:
                out[key] = NEW_INV
            else:
                out[key] = rewrite_evidence_path(item)
        return out
    if isinstance(value, list):
        return [rewrite_evidence_path(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()

    workflow = root / ".github/workflows/api02-accept.yml"
    text = workflow.read_text(encoding="utf-8")
    old = "handoff/API-02/C12_ACCEPTANCE_INPUTS.env"
    if old not in text:
        raise SystemExit("C13 follow-up: remaining C12 acceptance-input path not found")
    workflow.write_text(
        text.replace(old, "handoff/API-02/C13_ACCEPTANCE_INPUTS.env"),
        encoding="utf-8",
    )

    executive = root / "docs/api/API-02/01_EXECUTIVE_RESULT.md"
    text = executive.read_text(encoding="utf-8")
    old = "Authoritative GitHub run `33491251813` verified the exact C12 archive and all required external anchors."
    new = "Authoritative GitHub run `33491251813` verified the exact entering archive and all required external anchors."
    if old not in text:
        raise SystemExit("C13 follow-up: executive stale-audit sentence not found")
    executive.write_text(text.replace(old, new, 1), encoding="utf-8")

    lineage = root / "docs/api/API-02/API02_LINEAGE.json"
    data = json.loads(lineage.read_text(encoding="utf-8"))
    rewritten = rewrite_evidence_path(data)
    if rewritten == data:
        raise SystemExit("C13 follow-up: stale lineage evidence_path not found")
    lineage.write_text(
        json.dumps(rewritten, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("API02_C13_FOLLOWUP_FIX:PASS")


if __name__ == "__main__":
    main()
