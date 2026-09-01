from __future__ import annotations

import argparse
import json
from pathlib import Path

OLD_INV = "docs/api/API-02/API02_C11_TO_C12_CORRECTION_INVENTORY.json"
NEW_INV = "docs/api/API-02/API02_C12_TO_C13_CORRECTION_INVENTORY.json"
OLD_LAYER_A = "docs/api/API-02/API02_API01C5_TO_C12_EXACT_INVENTORY.json"
NEW_LAYER_A = "docs/api/API-02/API02_API01C5_TO_C13_EXACT_INVENTORY.json"


def rewrite_current_refs(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key == "evidence_path" and item == OLD_INV:
                out[key] = NEW_INV
            else:
                out[key] = rewrite_current_refs(item)
        return out
    if isinstance(value, list):
        return [rewrite_current_refs(item) for item in value]
    if isinstance(value, str):
        return value.replace(OLD_LAYER_A, NEW_LAYER_A)
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
    rewritten = rewrite_current_refs(data)
    if rewritten == data:
        raise SystemExit("C13 follow-up: stale lineage references not found")
    lineage.write_text(
        json.dumps(rewritten, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("API02_C13_FOLLOWUP_FIX:PASS")


if __name__ == "__main__":
    main()
