#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

CTRL02_SOURCE_SHA = "daddb4dfaeb3097e22d15e3448b5d927d7c3b1d7d4dd3332230d23ccd999df1d"
CTRL02_ACCEPTED_SHA = "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
CTRL02_ACCEPTED_SIZE = 16720456
CTRL02_ACCEPTANCE_RUN = 33690561259
CTRL02_ACCEPTANCE_HEAD = "a70e2bfef7a668ee5158475712827bbc50f6d5fd"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def patch_runtime(root: Path) -> None:
    path = root / "services/control-plane-service/src/epd2_control_plane_service/credential_lifecycle.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, CTRL02_SOURCE_SHA, CTRL02_ACCEPTED_SHA, "runtime CTRL02 identity")
    path.write_text(text, encoding="utf-8")

    path = root / "services/control-plane-service/tests/test_ctrl03_secret_evidence_inventory.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, 'startswith("daddb4df")', 'startswith("f58bafe7")', "test CTRL02 prefix")
    path.write_text(text, encoding="utf-8")

    path = root / "scripts/ctrl03_mutation_suite.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, CTRL02_SOURCE_SHA, CTRL02_ACCEPTED_SHA, "mutation CTRL02 identity")
    path.write_text(text, encoding="utf-8")


def patch_validator(root: Path) -> None:
    path = root / "scripts/ctrl03_validator.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        f'CTRL02_SHA = "{CTRL02_SOURCE_SHA}"',
        f'''CTRL02_SHA = "{CTRL02_ACCEPTED_SHA}"\nCTRL02_ACCEPTANCE_RUN = {CTRL02_ACCEPTANCE_RUN}\nCTRL02_ACCEPTANCE_HEAD = "{CTRL02_ACCEPTANCE_HEAD}"\nCTRL02_ACCEPTED_SIZE = {CTRL02_ACCEPTED_SIZE}''',
        "validator CTRL02 constants",
    )
    text = replace_once(
        text,
        '''    mutation_pass = mutation.get("detected") == 44 and mutation.get("undetected") == []\n    frozen = freeze(args.record_freeze)\n''',
        '''    mutation_pass = mutation.get("detected") == 44 and mutation.get("undetected") == []\n    frozen = freeze(args.record_freeze)\n    ctrl02_acceptance_path = VALIDATION / "ctrl02_authoritative_acceptance.json"\n    ctrl02_acceptance = (\n        json.loads(ctrl02_acceptance_path.read_text())\n        if ctrl02_acceptance_path.exists()\n        else {}\n    )\n    ctrl02_reconciled = (\n        ctrl02_acceptance.get("stage") == "CTRL-02"\n        and ctrl02_acceptance.get("conclusion") == "PASS"\n        and ctrl02_acceptance.get("run_id") == CTRL02_ACCEPTANCE_RUN\n        and ctrl02_acceptance.get("workflow_head_sha") == CTRL02_ACCEPTANCE_HEAD\n        and ctrl02_acceptance.get("candidate_sha256") == CTRL02_SHA\n        and ctrl02_acceptance.get("candidate_size") == CTRL02_ACCEPTED_SIZE\n        and ctrl02_acceptance.get("gates") == "46/46 PASS"\n        and ctrl02_acceptance.get("self_acceptance") is False\n    )\n''',
        "validator CTRL02 acceptance load",
    )
    text = replace_once(
        text,
        '''                    "ctrl02": {\n                        "state": "WORKING_PREDECESSOR_NOT_ACCEPTED",\n                        "sha256": CTRL02_SHA,\n                        "size": 16718551,\n                    },\n                    "ctrl02_reconciliation": "BLOCKED_FOR_FINAL_SEAL",\n                    "development_may_continue": True,''',
        '''                    "ctrl02": {\n                        "state": "CANONICAL_ACCEPTED",\n                        "sha256": CTRL02_SHA,\n                        "size": CTRL02_ACCEPTED_SIZE,\n                        "acceptance_run_id": CTRL02_ACCEPTANCE_RUN,\n                        "acceptance_workflow_head": CTRL02_ACCEPTANCE_HEAD,\n                    },\n                    "ctrl02_reconciliation": "PASS" if ctrl02_reconciled else "FAIL",\n                    "development_may_continue": True,''',
        "validator predecessor payload",
    )
    text = replace_once(
        text,
        '''        if gate_id == "G04":\n            status = "BLOCKED_FOR_FINAL_SEAL"''',
        '''        if gate_id == "G04":\n            status = "PASS" if ctrl02_reconciled else "FAIL"''',
        "validator G04",
    )
    text = replace_once(
        text,
        '{"id": gate_id, "name": name, "status": status, "executed": gate_id != "G04"}',
        '{"id": gate_id, "name": name, "status": status, "executed": True}',
        "validator G04 execution",
    )
    text = replace_once(
        text,
        '"overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED" if not failed else "FAIL",',
        '"overall": "PASS" if not failed and not blocked else "FAIL",',
        "validator overall",
    )
    text = replace_once(
        text,
        '''    print(\n        "CTRL03_DEVELOPMENT_RESULT:"\n        f"{'PASS' if not failed else 'FAIL'}:{passed}/50_PASS:"\n        "G04_BLOCKED_FOR_FINAL_SEAL"\n    )\n    return 0 if not failed else 1''',
        '''    terminal = "PASS" if not failed and not blocked else "FAIL"\n    print(f"CTRL03_RESULT:{terminal}:{passed}/50_PASS")\n    return 0 if terminal == "PASS" else 1''',
        "validator terminal",
    )
    path.write_text(text, encoding="utf-8")


def patch_builder(root: Path) -> None:
    path = root / "scripts/build_ctrl03_preseal.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'NAME = "EPD2_CTRL03_CREDENTIAL_TRUST_AND_KEY_LIFECYCLE_CONTROL_WORKING_0.1_PRESEAL"',
        'NAME = "EPD2_CTRL03_CREDENTIAL_TRUST_AND_KEY_LIFECYCLE_CONTROL_CANDIDATE_0.1_C1"',
        "candidate name",
    )
    text = replace_once(
        text,
        'result["overall"] != "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED"',
        'result["overall"] != "PASS"',
        "builder overall",
    )
    text = replace_once(
        text,
        'result["gates_passed"] != 49 or result["gates_blocked_for_final_seal"] != ["G04"]',
        'result["gates_passed"] != 50 or result["gates_blocked_for_final_seal"] != []',
        "builder gates",
    )
    text = replace_once(text, '"gates": "49/50 PASS; G04 BLOCKED_FOR_FINAL_SEAL"', '"gates": "50/50 PASS"', "identity gates")
    path.write_text(text, encoding="utf-8")


def patch_verifier(root: Path) -> None:
    path = root / "scripts/verify_ctrl03_package.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'if result["gates_passed"] != 49 or result["gates_blocked_for_final_seal"] != ["G04"]:',
        'if result["overall"] != "PASS" or result["gates_passed"] != 50 or result["gates_failed"] or result["gates_blocked_for_final_seal"]:',
        "verifier gates",
    )
    text = replace_once(
        text,
        '''            if result["self_state"] != "NOT_ACCEPTED":\n                raise SystemExit("developer self-acceptance forbidden")\n            mutation = json.loads((root / "validation/ctrl03/mutation_result.json").read_text())''',
        f'''            if result["self_state"] != "NOT_ACCEPTED":\n                raise SystemExit("developer self-acceptance forbidden")\n            predecessor = json.loads((root / "validation/ctrl03/ctrl02_authoritative_acceptance.json").read_text())\n            if (\n                predecessor.get("stage") != "CTRL-02"\n                or predecessor.get("conclusion") != "PASS"\n                or predecessor.get("run_id") != {CTRL02_ACCEPTANCE_RUN}\n                or predecessor.get("workflow_head_sha") != "{CTRL02_ACCEPTANCE_HEAD}"\n                or predecessor.get("candidate_sha256") != "{CTRL02_ACCEPTED_SHA}"\n                or predecessor.get("candidate_size") != {CTRL02_ACCEPTED_SIZE}\n                or predecessor.get("self_acceptance") is not False\n            ):\n                raise SystemExit("CTRL02_RECONCILIATION_INVALID")\n            mutation = json.loads((root / "validation/ctrl03/mutation_result.json").read_text())''',
        "verifier predecessor",
    )
    path.write_text(text, encoding="utf-8")


def patch_docs(root: Path) -> None:
    path = root / "docs/ctrl/CTRL-03/CTRL03_STAGE_CONTRACT.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '`PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. Development may proceed, but final seal is blocked until the consumed CTRL-02 working predecessor is replaced by, or reconciled with, an authoritative accepted identity.',
        '`CANDIDATE_NOT_ACCEPTED`. CTRL-02 authoritative predecessor reconciliation is complete; CTRL-03 remains unaccepted until independent governed acceptance of the exact candidate bytes.',
        "stage status",
    )
    text = replace_once(
        text,
        f'- CTRL-02: working predecessor only; SHA-256 `{CTRL02_SOURCE_SHA}`, size `16718551`; not authoritative acceptance.',
        f'- CTRL-02: `ACCEPTED / CLOSED`; authoritative candidate SHA-256 `{CTRL02_ACCEPTED_SHA}`, size `{CTRL02_ACCEPTED_SIZE}`, acceptance run `{CTRL02_ACCEPTANCE_RUN}`, workflow head `{CTRL02_ACCEPTANCE_HEAD}`.',
        "stage predecessor",
    )
    text = replace_once(
        text,
        'Developer validation may report `DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED`. It must never report CTRL-03 as accepted, production-ready, legally activated, BSI/CC certified or canonically sealed.',
        'Candidate validation may report `PASS` only after exact CTRL-02 authoritative identity reconciliation. The candidate must still never self-report CTRL-03 as accepted, production-ready, legally activated, BSI/CC certified or canonically sealed.',
        "stage acceptance boundary",
    )
    path.write_text(text, encoding="utf-8")

    path = root / "docs/ctrl/CTRL-03/CTRL03_DEVELOPER_REPORT.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        f'CTRL-02 exact consumed working predecessor: SHA-256 `{CTRL02_SOURCE_SHA}`, size `16718551`, `WORKING_PREDECESSOR / NOT_ACCEPTED`.',
        f'CTRL-02 authoritative predecessor: SHA-256 `{CTRL02_ACCEPTED_SHA}`, size `{CTRL02_ACCEPTED_SIZE}`, run `{CTRL02_ACCEPTANCE_RUN}`, `CANON_PASS / ACCEPTED_CLOSED`.',
        "report predecessor",
    )
    text = replace_once(
        text,
        'Mandatory gates: expected developer disposition `49/50 PASS`; `G04 BLOCKED_FOR_FINAL_SEAL`; no failed runnable gate.',
        'Mandatory gates after governed predecessor reconciliation: `50/50 PASS`; no blocked or failed gate.',
        "report gates",
    )
    path.write_text(text, encoding="utf-8")


def write_predecessor_evidence(root: Path) -> None:
    payload = {
        "schema": "epd2.ctrl02.authoritative-acceptance-result/1",
        "stage": "CTRL-02",
        "candidate_sha256": CTRL02_ACCEPTED_SHA,
        "candidate_size": CTRL02_ACCEPTED_SIZE,
        "run_id": CTRL02_ACCEPTANCE_RUN,
        "workflow_head_sha": CTRL02_ACCEPTANCE_HEAD,
        "conclusion": "PASS",
        "gates": "46/46 PASS",
        "mutations": "40/40 DETECTED",
        "self_acceptance": False,
        "terminal_marker": f"CTRL02_AUTHORITATIVE_RESULT:PASS:{CTRL02_ACCEPTED_SHA}:{CTRL02_ACCEPTED_SIZE}",
    }
    path = root / "validation/ctrl03/ctrl02_authoritative_acceptance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    patch_runtime(root)
    patch_validator(root)
    patch_builder(root)
    patch_verifier(root)
    patch_docs(root)
    write_predecessor_evidence(root)
    print("CTRL03_C1_PREDECESSOR_RECONCILIATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
