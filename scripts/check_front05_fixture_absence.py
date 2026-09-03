#!/usr/bin/env python3
"""Prove the governed test fixture is absent from the production build.

`next.config.ts` rewrites every request for `runtime/governedTestRuntime` to
`runtime/fixtureAbsent.ts` unless the governed test flag is exactly "1", so the
fixture module should not be in the emitted bundle at all. "Should" is not
evidence, and an unreachable-but-present fixture is one flag away from being a
reachable one, so this scans the built output for the markers instead.

The markers are chosen to fail loudly rather than cleverly: the unique fixture
string, and the prototype prefixes that every fixture record carries. If any of
them appears in a production build, fabricated citizen cases could reach a
representative's screen, which is the failure the whole arrangement exists to
prevent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BUILD_DIR = "frontend/representative-workspace/.next"

MARKERS = (
    "EPD2_FRONT05_GOVERNED_TEST_FIXTURE_MARKER",
    "PROTOTYP-VORGANG",
    "PROTOTYP-MANDAT",
    "PROTOTYP-POSITION",
    "PROTOTYP-ABWEICHUNG",
    "PROTOTYP-ERKLAERUNG",
    "PROTOTYP-VORSCHLAG",
    "PROTOTYP-BESCHRAENKUNG",
    "createGovernedTestRuntime",
)

SCANNED_SUFFIXES = {".js", ".mjs", ".json", ".html", ".css", ".txt"}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    build = root / BUILD_DIR
    if not build.is_dir():
        print("FAIL: no build directory to scan")
        return 2

    scanned = 0
    hits: list[str] = []
    for path in build.rglob("*"):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        # The server-side build legitimately contains the replacement module's
        # own error string; scan the client bundle, which is what ships to a
        # browser, plus the server chunks that could stream fixture data into it.
        if "cache" in path.parts:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for marker in MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(root).as_posix()}: {marker}")

    result = {
        "schema": "epd2.front05.fixture-absence/1",
        "build_dir": BUILD_DIR,
        "files_scanned": scanned,
        "markers": list(MARKERS),
        "hits": hits,
        "fixture_absent": not hits,
    }
    print(json.dumps(result, indent=1))
    if hits:
        print(f"FAIL: {len(hits)} fixture marker(s) present in the production build")
        return 1
    print(f"PASS: {scanned} files scanned, no fixture marker present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
