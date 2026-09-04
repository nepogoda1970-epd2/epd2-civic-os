#!/usr/bin/env python3
"""FRONT-05 authorization-negative catalogue, derived from executed tests.

The assignment lists the negatives that must fail safely: another
representative's case, another mandate, an unassigned or restricted case, expired
authority, a conflict-restricted case, direct URL guessing, a stale cached route.
A hand-written table saying each of those "fails safely" is a claim. This record
is built from the test run instead: each entry names the executed test that
demonstrates it and carries that test's observed outcome.

Where a scenario is demonstrated by a unit test rather than a browser test, the
record says so — the point is that every scenario is tied to something that ran,
not that everything ran in a browser.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

RAW = "validation/front05/raw/authorization-negative.log"
BROWSER_RAW = "validation/front05/raw/browser.log"
UNIT_RAW = "validation/front05/raw/unit-tests.log"

# scenario id, description, the substring identifying the test that shows it,
# and which raw log to look in.
CASES = [
    (
        "AN-01",
        "another representative's case within a foreign mandate",
        "every negative case outcome renders identical text",
        BROWSER_RAW,
    ),
    (
        "AN-02",
        "a case in another mandate, reached by direct URL",
        "every negative case outcome renders identical text",
        BROWSER_RAW,
    ),
    (
        "AN-03",
        "a case that does not exist, reached by URL guessing",
        "every negative case outcome renders identical text",
        BROWSER_RAW,
    ),
    (
        "AN-04",
        "a conflict-restricted case",
        "the refusal names no resource and no reason",
        BROWSER_RAW,
    ),
    (
        "AN-05",
        "a malformed or traversal-shaped case identifier",
        "every negative case outcome renders identical text",
        BROWSER_RAW,
    ),
    (
        "AN-06",
        "a restricted case is not linked and its subject is withheld in the list",
        "a restricted case is not linked and its subject is withheld",
        BROWSER_RAW,
    ),
    (
        "AN-07",
        "no mandate resolved: every protected read refuses",
        "no mandate is resolved, and the interface says so",
        RAW,
    ),
    (
        "AN-08",
        "a case detail under the production profile discloses nothing",
        "a case detail refuses without disclosing existence",
        RAW,
    ),
    (
        "AN-09",
        "a consequential action is refused with nothing committed",
        "every consequential action is refused with nothing committed",
        RAW,
    ),
    (
        "AN-10",
        "an unreadable conflict register keeps access restricted",
        "the conflict register is unreadable, so access stays restricted",
        RAW,
    ),
    (
        "AN-11",
        "no universal or cross-mandate mode is offered on any route",
        "offers no universal or cross-mandate mode",
        BROWSER_RAW,
    ),
    (
        "AN-12",
        "no unscoped search surface exists on any route",
        "offers no unscoped search field",
        BROWSER_RAW,
    ),
    (
        "AN-13",
        "no case content reaches a browser store, a URL or the title",
        "writes nothing to a browser store",
        BROWSER_RAW,
    ),
    (
        "AN-14",
        "a typed draft never reaches a store even when the save is refused",
        "a case body typed into a draft never reaches a store",
        BROWSER_RAW,
    ),
    (
        "AN-15",
        "expired, revoked and scope-changed sessions clear scope and role",
        "expiry and revocation clear the scope and the role",
        UNIT_RAW,
    ),
    (
        "AN-16",
        "no terminal session state returns to a working state",
        "no event returns a terminal negative state to a working state",
        UNIT_RAW,
    ),
    (
        "AN-17",
        "a stale route: a scope change forces loaded content to be cleared",
        "a scope change forces previously loaded content to be cleared",
        UNIT_RAW,
    ),
    (
        "AN-18",
        "a wrong-mandate binding is refused non-disclosingly",
        "the wrong-mandate refusal is non-disclosing",
        UNIT_RAW,
    ),
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    logs = {
        name: (root / name).read_text(encoding="utf-8", errors="replace")
        if (root / name).is_file()
        else ""
        for name in {RAW, BROWSER_RAW, UNIT_RAW}
    }

    cases = []
    for identifier, scenario, needle, log_name in CASES:
        body = logs.get(log_name, "")
        present = needle in body
        # A Playwright line reporter prints a failing test again under a
        # numbered failure heading; a TAP run prints "not ok". Either is a fail.
        failed = bool(
            re.search(rf"^\s+\d+\)\s.*{re.escape(needle)}", body, re.M)
            or re.search(rf"^not ok \d+ - .*{re.escape(needle)}", body, re.M)
        )
        observed = (
            "refused safely"
            if present and not failed
            else ("TEST_FAILED" if failed else "NO_EXECUTED_TEST_FOUND")
        )
        cases.append(
            {
                "id": identifier,
                "scenario": scenario,
                "expected": "refused safely",
                "observed": observed,
                "evidence": f"{log_name} :: {needle}",
                "evidence_kind": "browser" if log_name != UNIT_RAW else "unit",
            }
        )

    out = {
        "schema": "epd2.front05.authorization-negatives/1",
        "authority": "NON_AUTHORITATIVE",
        "stage": "FRONT-05 — WS-04 Representative Workspace",
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "derivation": (
            "Each entry names an executed test and reports that test's observed "
            "outcome. Nothing here is asserted independently of a run."
        ),
        "case_count": len(cases),
        "satisfied": sum(1 for c in cases if c["observed"] == c["expected"]),
        "cases": cases,
    }
    path = root / "validation/front05/authorization_negatives.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out['satisfied']}/{out['case_count']} authorization negatives satisfied")
    for case in cases:
        if case["observed"] != case["expected"]:
            print(f"  {case['id']}: {case['observed']} ({case['evidence']})")
    return 0 if out["satisfied"] == out["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
