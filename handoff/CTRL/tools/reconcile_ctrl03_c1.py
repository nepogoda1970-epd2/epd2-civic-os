#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_HELPER_COMMIT = "a5b9f6be3cdbc48b35bd1ef61eae1efca119dbb1"
BASE_HELPER_PATH = "handoff/CTRL/tools/reconcile_ctrl03_c1.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()

    # Execute the already-reviewed deterministic predecessor reconciliation exactly
    # from its immutable commit, then apply the packaging-only seal repair below.
    source = subprocess.check_output(
        ["git", "show", f"{BASE_HELPER_COMMIT}:{BASE_HELPER_PATH}"], text=True
    )
    with tempfile.TemporaryDirectory() as td:
        helper = Path(td) / "reconcile_ctrl03_c1_base.py"
        helper.write_text(source, encoding="utf-8")
        subprocess.run([sys.executable, str(helper), str(root)], check=True)

    builder = root / "scripts/build_ctrl03_preseal.py"
    text = builder.read_text(encoding="utf-8")
    old = 'files = [path for path in sorted(stage.rglob("*")) if path.is_file()]'
    new = (
        'files = [\n'
        '            path\n'
        '            for path in sorted(stage.rglob("*"))\n'
        '            if path.is_file() and path.name != "SHA256SUMS.txt"\n'
        '        ]'
    )
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"manifest self-hash repair: expected one anchor, got {count}")
    builder.write_text(text.replace(old, new, 1), encoding="utf-8")

    print("CTRL03_C1_PREDECESSOR_RECONCILIATION_PASS")
    print("CTRL03_C1_MANIFEST_SELF_HASH_REPAIR_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
