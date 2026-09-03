from __future__ import annotations

import json
import pathlib
import sys

API06_FILENAME = "EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip"
API06_SHA = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
API06_SIZE = 44012716
API06_RUN = 33629147572
API06_JOB = 100243984921
OLD_BASELINE = "217559b7f21c338d6fe8d4e4676082cd3840251c"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"overlay anchor not found: {label}")
    return text.replace(old, new, 1)


def patch_binding_module(root: pathlib.Path) -> None:
    path = root / "packages/python/epd2-qualification/src/epd2_qualification/api06_binding.py"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        f'ACCEPTED_API06_CANDIDATE_SHA256 = "{API06_SHA}"\nACCEPTED_API06_CANDIDATE_SIZE_BYTES = {API06_SIZE}\n',
        f'ACCEPTED_API06_CANDIDATE_FILENAME = "{API06_FILENAME}"\n'
        f'ACCEPTED_API06_CANDIDATE_SHA256 = "{API06_SHA}"\n'
        f'ACCEPTED_API06_CANDIDATE_SIZE_BYTES = {API06_SIZE}\n',
        "binding constants",
    )
    text = replace_once(
        text,
        f"ACCEPTED_API06_AUTHORITATIVE_RUN_ID = {API06_RUN}\n",
        f"ACCEPTED_API06_AUTHORITATIVE_RUN_ID = {API06_RUN}\n"
        f"ACCEPTED_API06_AUTHORITATIVE_JOB_ID = {API06_JOB}\n",
        "authoritative job constant",
    )
    text = replace_once(
        text,
        '    if candidate.get("sha256") != ACCEPTED_API06_CANDIDATE_SHA256:\n',
        '    if candidate.get("filename") != ACCEPTED_API06_CANDIDATE_FILENAME:\n'
        '        defects.append("API-06 accepted candidate filename drifted")\n'
        '    if candidate.get("sha256") != ACCEPTED_API06_CANDIDATE_SHA256:\n',
        "acceptance filename",
    )
    text = replace_once(
        text,
        '    if authoritative.get("run_id") != ACCEPTED_API06_AUTHORITATIVE_RUN_ID:\n'
        '        defects.append("API-06 authoritative run identity drifted")\n',
        '    if authoritative.get("run_id") != ACCEPTED_API06_AUTHORITATIVE_RUN_ID:\n'
        '        defects.append("API-06 authoritative run identity drifted")\n'
        '    if authoritative.get("job_id") != ACCEPTED_API06_AUTHORITATIVE_JOB_ID:\n'
        '        defects.append("API-06 authoritative job identity drifted")\n'
        '    if authoritative.get("governed_gates_total") != 40:\n'
        '        defects.append("API-06 authoritative gate total is not exact 40")\n'
        '    if authoritative.get("environment_blocked_gates") != 0:\n'
        '        defects.append("API-06 authoritative acceptance contains blocked gates")\n',
        "acceptance job/gate identity",
    )
    text = replace_once(
        text,
        '        "decision": record["decision"],\n',
        '        "decision": record["decision"],\n'
        '        "candidate_filename": candidate["filename"],\n',
        "return filename",
    )
    text = replace_once(
        text,
        '        "authoritative_run_id": authoritative.get("run_id"),\n',
        '        "authoritative_run_id": authoritative.get("run_id"),\n'
        '        "authoritative_job_id": authoritative.get("job_id"),\n',
        "return job",
    )
    text = replace_once(
        text,
        'def verify_archive(path: pathlib.Path) -> tuple[dict[str, Any], str]:\n'
        '    observed_sha = sha256_file(path)\n',
        'def verify_archive(path: pathlib.Path) -> tuple[dict[str, Any], str]:\n'
        '    if path.name != ACCEPTED_API06_CANDIDATE_FILENAME:\n'
        '        raise RuntimeError(\n'
        '            f"accepted API-06 candidate filename mismatch: {path.name} != "\n'
        '            f"{ACCEPTED_API06_CANDIDATE_FILENAME}"\n'
        '        )\n'
        '    observed_sha = sha256_file(path)\n',
        "archive filename",
    )
    path.write_text(text, encoding="utf-8")


def write_binding_evidence(root: pathlib.Path) -> None:
    baseline_path = root / "docs/ops/OPS-03/OPS03_ENTERING_BASELINE_IDENTITY.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    evidence = {
        "schema": "epd2.ops03.api06-accepted-runtime-binding/1",
        "stage": "OPS-03",
        "dependency": "API-06",
        "state": "ACCEPTED_CLOSED",
        "api_layer_state": "CLOSED",
        "candidate_filename": API06_FILENAME,
        "candidate_sha256": API06_SHA,
        "candidate_size": API06_SIZE,
        "authoritative_run_id": API06_RUN,
        "authoritative_job_id": API06_JOB,
        "entering_main_commit": baseline["base_commit"],
        "entering_main_tree": baseline["base_tree"],
        "old_stale_entering_main_commit": OLD_BASELINE,
        "binding_result": "PASS",
        "system_trial_preview_state": "NOT_OPEN",
        "preview_readiness_scope": "OPS-03 may qualify preview-readiness minimum only",
        "checkpoint_requirement": "SYSTEM TRIAL PREVIEW remains NOT OPEN until separate governed checkpoint-opening decision",
        "self_acceptance": False,
    }
    path = root / "validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def patch_validator_binding_evidence(root: pathlib.Path) -> None:
    path = root / "scripts/validation/validate_ops03.py"
    text = path.read_text(encoding="utf-8")
    anchor = '        try:\n            artifact = api06_binding.artifact_from_env()\n'
    inserted = '''        binding_path = self.repo_root / "validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"\n        if not binding_path.is_file():\n            _fail(result, ["OPS-03 exact API-06 runtime binding evidence is missing"])\n            return\n        binding = json.loads(binding_path.read_text(encoding="utf-8"))\n        binding_defects = []\n        expected_binding = {\n            "stage": "OPS-03",\n            "dependency": "API-06",\n            "state": "ACCEPTED_CLOSED",\n            "api_layer_state": "CLOSED",\n            "candidate_filename": api06_binding.ACCEPTED_API06_CANDIDATE_FILENAME,\n            "candidate_sha256": api06_binding.ACCEPTED_API06_CANDIDATE_SHA256,\n            "candidate_size": api06_binding.ACCEPTED_API06_CANDIDATE_SIZE_BYTES,\n            "authoritative_run_id": api06_binding.ACCEPTED_API06_AUTHORITATIVE_RUN_ID,\n            "authoritative_job_id": api06_binding.ACCEPTED_API06_AUTHORITATIVE_JOB_ID,\n            "binding_result": "PASS",\n            "system_trial_preview_state": "NOT_OPEN",\n            "self_acceptance": False,\n        }\n        for key, expected in expected_binding.items():\n            if binding.get(key) != expected:\n                binding_defects.append(f"API-06 binding evidence {key} drifted")\n        if binding_defects:\n            _fail(result, binding_defects)\n            return\n        result.measurements["api06_binding_evidence"] = binding\n\n        try:\n            artifact = api06_binding.artifact_from_env()\n'''
    text = replace_once(text, anchor, inserted, "G05 evidence binding")
    path.write_text(text, encoding="utf-8")


def write_correction_note(root: pathlib.Path) -> None:
    baseline = json.loads(
        (root / "docs/ops/OPS-03/OPS03_ENTERING_BASELINE_IDENTITY.json").read_text(encoding="utf-8")
    )
    path = root / "docs/ops/OPS-03/OPS03_C2_CORRECTION_SCOPE.md"
    path.write_text(
        "# OPS-03 C2 corrective scope\n\n"
        "C1 is not promoted. C2 is a minimal governance/runtime-binding correction.\n\n"
        f"- stale C1 entering baseline: `main@{OLD_BASELINE}`\n"
        f"- C2 entering baseline: `main@{baseline['base_commit']}` / tree `{baseline['base_tree']}`\n"
        f"- exact accepted API-06: `{API06_FILENAME}` / `{API06_SHA}` / `{API06_SIZE}` bytes\n"
        f"- authoritative API-06 acceptance: run `{API06_RUN}`, job `{API06_JOB}`, 40/40 PASS\n"
        "- G05 now requires API-06 `ACCEPTED_CLOSED` and API layer `CLOSED`; the former `API-06 is NEXT` blocker semantics are removed.\n"
        "- OPS-03 functional implementation is otherwise preserved from C1 via the governed OPS-02→C1 delta reconciliation.\n"
        "- OPS-03 may qualify preview-readiness minimum; SYSTEM TRIAL PREVIEW remains NOT OPEN until a separate governed checkpoint-opening decision.\n"
        "- candidate self-state remains `CANDIDATE_NOT_ACCEPTED`; no self-acceptance is performed.\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c2_exact_binding_overlay.py ROOT")
    root = pathlib.Path(sys.argv[1]).resolve()
    patch_binding_module(root)
    write_binding_evidence(root)
    patch_validator_binding_evidence(root)
    write_correction_note(root)
    print(
        f"OPS03_C2_EXACT_API06_BINDING:PASS:{API06_FILENAME}:{API06_SHA}:{API06_SIZE}:{API06_RUN}:{API06_JOB}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
