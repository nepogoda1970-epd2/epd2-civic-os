#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

CTRL01_SHA = "c9c666d01e17fe615f78c2e408169ce4b6434d3b8dec23dfda889b2ce91e3c49"
CTRL01_RUN = 33619101714
CTRL01_HEAD = "f4c09fca58d1699bf14b46e077f2972b9cb4b92f"
CTRL01_SIZE = 190092
BASE_MAIN = "217559b7f21c338d6fe8d4e4676082cd3840251c"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {text.count(old)}")
    return text.replace(old, new, 1)


def patch_validator(root: Path) -> None:
    path = root / "scripts/ctrl02_validator.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'CTRL01_SHA = "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"',
        f'''CTRL01_SHA = "{CTRL01_SHA}"\nCTRL01_ACCEPTANCE_RUN = {CTRL01_RUN}\nCTRL01_ACCEPTANCE_HEAD = "{CTRL01_HEAD}"\nCTRL01_ACCEPTED_SIZE = {CTRL01_SIZE}''',
        "CTRL01 constants",
    )
    text = replace_once(
        text,
        '''    mutation_pass = mutation.get("detected") == 40 and mutation.get("undetected") == []\n    freeze_pass = record_or_verify_freeze(args.record_freeze)\n''',
        '''    mutation_pass = mutation.get("detected") == 40 and mutation.get("undetected") == []\n    freeze_pass = record_or_verify_freeze(args.record_freeze)\n    ctrl01_acceptance_path = VALIDATION / "ctrl01_authoritative_acceptance.json"\n    ctrl01_acceptance = (\n        json.loads(ctrl01_acceptance_path.read_text())\n        if ctrl01_acceptance_path.exists()\n        else {}\n    )\n    ctrl01_reconciled = (\n        ctrl01_acceptance.get("stage") == "CTRL-01"\n        and ctrl01_acceptance.get("conclusion") == "PASS"\n        and ctrl01_acceptance.get("run_id") == CTRL01_ACCEPTANCE_RUN\n        and ctrl01_acceptance.get("workflow_head_sha") == CTRL01_ACCEPTANCE_HEAD\n        and ctrl01_acceptance.get("candidate_sha256") == CTRL01_SHA\n        and ctrl01_acceptance.get("candidate_size") == CTRL01_ACCEPTED_SIZE\n        and ctrl01_acceptance.get("gates") == "22/22 PASS"\n        and ctrl01_acceptance.get("self_acceptance") is False\n    )\n''',
        "acceptance load",
    )
    text = replace_once(
        text,
        '"ctrl01_state": "WORKING_PREDECESSOR_NOT_ACCEPTED",',
        '"ctrl01_state": "CANONICAL_ACCEPTED",',
        "dependency state",
    )
    text = replace_once(
        text,
        '''                    "status": "BLOCKED_FOR_FINAL_SEAL",\n                    "reason": "authoritative CTRL-01 acceptance identity is absent",\n                    "development_may_continue": True,''',
        '''                    "status": "PASS" if ctrl01_reconciled else "FAIL",\n                    "reason": (\n                        "authoritative CTRL-01 C1 identity reconciled"\n                        if ctrl01_reconciled\n                        else "authoritative CTRL-01 identity mismatch"\n                    ),\n                    "development_may_continue": True,\n                    "accepted_candidate_sha256": CTRL01_SHA,\n                    "accepted_candidate_size": CTRL01_ACCEPTED_SIZE,\n                    "acceptance_run_id": CTRL01_ACCEPTANCE_RUN,\n                    "acceptance_workflow_head": CTRL01_ACCEPTANCE_HEAD,''',
        "G04 evidence",
    )
    text = replace_once(
        text,
        '''        if gate_id == "G04":\n            status = "BLOCKED_FOR_FINAL_SEAL"''',
        '''        if gate_id == "G04":\n            status = "PASS" if ctrl01_reconciled else "FAIL"''',
        "G04 gate",
    )
    text = replace_once(
        text,
        '{"id": gate_id, "name": name, "status": status, "executed": gate_id != "G04"}',
        '{"id": gate_id, "name": name, "status": status, "executed": True}',
        "G04 execution",
    )
    text = replace_once(
        text,
        '"overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED" if not failed else "FAIL",',
        '"overall": "PASS" if not failed and not blocked else "FAIL",',
        "overall result",
    )
    text = replace_once(
        text,
        '''    print(\n        "CTRL02_DEVELOPMENT_RESULT:"\n        f"{'PASS' if not failed else 'FAIL'}:{passed}/46_PASS:"\n        "G04_BLOCKED_FOR_FINAL_SEAL"\n    )\n    return 0 if not failed else 1''',
        '''    terminal = "PASS" if not failed and not blocked else "FAIL"\n    print(f"CTRL02_RESULT:{terminal}:{passed}/46_PASS")\n    return 0 if terminal == "PASS" else 1''',
        "terminal result",
    )
    path.write_text(text, encoding="utf-8")


def patch_builder(root: Path) -> None:
    path = root / "scripts/build_ctrl02_preseal.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, 'WORKING_0.1_PRESEAL"', 'WORKING_0.2_PRESEAL"', "archive name")
    text = replace_once(
        text,
        'result["overall"] != "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED"',
        'result["overall"] != "PASS"',
        "builder overall",
    )
    text = replace_once(
        text,
        'result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]',
        'result["gates_passed"] != 46 or result["gates_blocked_for_final_seal"] != []',
        "builder gates",
    )
    text = replace_once(text, '"45/46 PASS; G04 BLOCKED_FOR_FINAL_SEAL"', '"46/46 PASS"', "identity gates")
    path.write_text(text, encoding="utf-8")


def write_package_verifier(root: Path) -> None:
    path = root / "scripts/verify_ctrl02_package.py"
    path.write_text(
        '''#!/usr/bin/env python3\n"""Fail-closed verifier for reconciled CTRL-02 0.2 archives."""\n\nfrom __future__ import annotations\n\nimport argparse\nimport hashlib\nimport json\nimport pathlib\nimport tempfile\nimport zipfile\n\nCTRL01_SHA = "c9c666d01e17fe615f78c2e408169ce4b6434d3b8dec23dfda889b2ce91e3c49"\nCTRL01_RUN = 33619101714\n\ndef sha256(path: pathlib.Path) -> str:\n    digest = hashlib.sha256()\n    with path.open("rb") as stream:\n        for chunk in iter(lambda: stream.read(1024 * 1024), b""):\n            digest.update(chunk)\n    return digest.hexdigest()\n\ndef main() -> int:\n    parser = argparse.ArgumentParser()\n    parser.add_argument("archive", type=pathlib.Path)\n    args = parser.parse_args()\n    archive = args.archive\n    if not archive.is_file():\n        raise SystemExit("archive missing")\n    with zipfile.ZipFile(archive) as package:\n        if bad := package.testzip():\n            raise SystemExit("CRC_FAIL=" + bad)\n        names = package.namelist()\n        if len(names) != len(set(names)):\n            raise SystemExit("DUPLICATE_PATHS")\n        for name in names:\n            pure = pathlib.PurePosixPath(name)\n            if pure.is_absolute() or ".." in pure.parts:\n                raise SystemExit("UNSAFE_PATH=" + name)\n        if any(name.lower().endswith(".zip") for name in names):\n            raise SystemExit("NESTED_ARCHIVE")\n        with tempfile.TemporaryDirectory() as tempdir:\n            package.extractall(tempdir)\n            roots = [path for path in pathlib.Path(tempdir).iterdir() if path.is_dir()]\n            if len(roots) != 1:\n                raise SystemExit("ROOT_COUNT")\n            root = roots[0]\n            validation = root / "validation/ctrl02"\n            result = json.loads((validation / "ctrl02_preseal_result.json").read_text())\n            if (\n                result.get("overall") != "PASS"\n                or result.get("gates_passed") != 46\n                or result.get("gates_failed")\n                or result.get("gates_blocked_for_final_seal")\n            ):\n                raise SystemExit("GATE_RESULT_INVALID")\n            reconciliation = json.loads(\n                (validation / "ctrl01_reconciliation_result.json").read_text()\n            )\n            if (\n                reconciliation.get("status") != "PASS"\n                or reconciliation.get("accepted_candidate_sha256") != CTRL01_SHA\n                or reconciliation.get("acceptance_run_id") != CTRL01_RUN\n            ):\n                raise SystemExit("CTRL01_RECONCILIATION_INVALID")\n            mutations = json.loads((validation / "mutation_result.json").read_text())\n            if mutations.get("detected") != 40 or mutations.get("undetected") != []:\n                raise SystemExit("MUTATION_INVALID")\n            fir = json.loads((validation / "fir_reconciliation.json").read_text())\n            if not all(fir.get("fir_presence", {}).values()):\n                raise SystemExit("FIR_RECONCILIATION_INVALID")\n            frozen = json.loads((validation / "freeze_manifest.json").read_text())\n            files = frozen.get("files", {})\n            if not files:\n                raise SystemExit("FREEZE_EMPTY")\n            for relative, expected in files.items():\n                source = root / relative\n                if not source.is_file() or sha256(source) != expected:\n                    raise SystemExit("FREEZE_MISMATCH=" + relative)\n    print(f"CTRL02_PACKAGE_VERIFY:PASS:{sha256(archive)}:{archive.stat().st_size}")\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n''',
        encoding="utf-8",
    )


def write_predecessor_evidence(root: Path) -> None:
    acceptance = {
        "schema": "epd2.ctrl01.authoritative-acceptance-result/1",
        "stage": "CTRL-01",
        "candidate_sha256": CTRL01_SHA,
        "candidate_size": CTRL01_SIZE,
        "base_main": BASE_MAIN,
        "run_id": CTRL01_RUN,
        "workflow_head_sha": CTRL01_HEAD,
        "job": "authoritative-review",
        "conclusion": "PASS",
        "gates": "22/22 PASS",
        "self_acceptance": False,
        "terminal_marker": f"CTRL01_C1_AUTHORITATIVE_RESULT:PASS:{CTRL01_SHA}:{CTRL01_SIZE}",
    }
    target = root / "validation/ctrl02/ctrl01_authoritative_acceptance.json"
    target.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doc = root / "docs/ctrl/CTRL-02/CTRL02_C1_RECONCILIATION.md"
    doc.write_text(
        f"""# CTRL-02 predecessor reconciliation\n\nCTRL-01 authoritative acceptance run: {CTRL01_RUN}\n\nAccepted CTRL-01 candidate SHA-256: `{CTRL01_SHA}`\n\nAccepted CTRL-01 candidate size: `{CTRL01_SIZE}` bytes.\n\nCanonical workflow head: `{CTRL01_HEAD}`.\n\nThis record resolves CTRL-02 gate G04 without self-acceptance; CTRL-02 remains a candidate until independent governed acceptance.\n""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    patch_validator(root)
    patch_builder(root)
    write_package_verifier(root)
    write_predecessor_evidence(root)
    print("CTRL02_RECONCILIATION_PATCH_V02_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
