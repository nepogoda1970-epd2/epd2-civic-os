from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys

API06_FILENAME = "EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip"
API06_SHA256 = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
API06_SIZE = 44012716
API06_RUN = 33629147572
API06_JOB = 100243984921
OLD_MAIN = "217559b7f21c338d6fe8d4e4676082cd3840251c"
OLD_TREE = "eb8a3254c2b8a30feff71318d4377eff2435605c"
BINDING_REL = "validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_api06_record(root: pathlib.Path) -> dict:
    path = root / "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json"
    record = _load(path)
    candidate = record.get("candidate", {})
    authoritative = record.get("authoritative", {})
    expected = {
        "decision": (record.get("decision"), "ACCEPTED_CLOSED"),
        "api_layer_state": (record.get("api_layer_state"), "CLOSED"),
        "candidate.filename": (candidate.get("filename"), API06_FILENAME),
        "candidate.sha256": (candidate.get("sha256"), API06_SHA256),
        "candidate.size_bytes": (candidate.get("size_bytes"), API06_SIZE),
        "candidate.self_accepted": (candidate.get("self_accepted"), False),
        "authoritative.run_id": (authoritative.get("run_id"), API06_RUN),
        "authoritative.job_id": (authoritative.get("job_id"), API06_JOB),
        "authoritative.conclusion": (authoritative.get("conclusion"), "SUCCESS"),
        "authoritative.passed_gates": (authoritative.get("passed_gates"), 40),
        "authoritative.failed_gates": (authoritative.get("failed_gates"), 0),
        "open_blockers": (record.get("open_blockers"), []),
    }
    bad = [f"{name}: {got!r} != {want!r}" for name, (got, want) in expected.items() if got != want]
    if bad:
        raise SystemExit("API-06 canonical acceptance identity mismatch: " + "; ".join(bad))
    return record


def _verify_api06_artifact() -> pathlib.Path:
    raw = os.environ.get("EPD2_OPS03_ACCEPTED_API06_ZIP", "").strip()
    if not raw:
        raise SystemExit("EPD2_OPS03_ACCEPTED_API06_ZIP is not set")
    path = pathlib.Path(raw)
    if not path.is_file():
        raise SystemExit(f"accepted API-06 artifact is missing: {path}")
    defects = []
    if path.name != API06_FILENAME:
        defects.append(f"filename {path.name!r}")
    if path.stat().st_size != API06_SIZE:
        defects.append(f"size {path.stat().st_size}")
    digest = _sha256(path)
    if digest != API06_SHA256:
        defects.append(f"sha256 {digest}")
    if defects:
        raise SystemExit("accepted API-06 artifact identity mismatch: " + "; ".join(defects))
    return path


STRICT_MODULE = r'''"""OPS-03 C2 exact accepted API-06 dependency binding.

This module is intentionally narrow. Runtime load/soak mechanics stay in the
C1-derived ``api06_binding`` helper; this C2 wrapper makes the governance
identity exact before those mechanics can be used by G05.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

from epd2_qualification import api06_binding as runtime_binding

ACCEPTED_API06_CANDIDATE_FILENAME = "EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip"
ACCEPTED_API06_CANDIDATE_SHA256 = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
ACCEPTED_API06_CANDIDATE_SIZE_BYTES = 44012716
ACCEPTED_API06_AUTHORITATIVE_RUN_ID = 33629147572
ACCEPTED_API06_AUTHORITATIVE_JOB_ID = 100243984921
BINDING_RELATIVE_PATH = "validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_acceptance_record(repo_root: pathlib.Path) -> dict[str, Any]:
    path = repo_root / "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json"
    if not path.is_file():
        raise RuntimeError("canonical API-06 acceptance record is missing")
    record = json.loads(path.read_text(encoding="utf-8"))
    candidate = record.get("candidate", {})
    authoritative = record.get("authoritative", {})
    checks = {
        "decision": (record.get("decision"), "ACCEPTED_CLOSED"),
        "api_layer_state": (record.get("api_layer_state"), "CLOSED"),
        "candidate.filename": (candidate.get("filename"), ACCEPTED_API06_CANDIDATE_FILENAME),
        "candidate.sha256": (candidate.get("sha256"), ACCEPTED_API06_CANDIDATE_SHA256),
        "candidate.size_bytes": (candidate.get("size_bytes"), ACCEPTED_API06_CANDIDATE_SIZE_BYTES),
        "candidate.self_accepted": (candidate.get("self_accepted"), False),
        "authoritative.run_id": (authoritative.get("run_id"), ACCEPTED_API06_AUTHORITATIVE_RUN_ID),
        "authoritative.job_id": (authoritative.get("job_id"), ACCEPTED_API06_AUTHORITATIVE_JOB_ID),
        "authoritative.conclusion": (authoritative.get("conclusion"), "SUCCESS"),
        "authoritative.passed_gates": (authoritative.get("passed_gates"), 40),
        "authoritative.failed_gates": (authoritative.get("failed_gates"), 0),
        "open_blockers": (record.get("open_blockers"), []),
    }
    defects = [
        f"{name}: {got!r} != {want!r}"
        for name, (got, want) in checks.items()
        if got != want
    ]
    if defects:
        raise RuntimeError("forged/stale API-06 acceptance record: " + "; ".join(defects))
    return {
        "decision": "ACCEPTED_CLOSED",
        "api_layer_state": "CLOSED",
        "candidate_filename": ACCEPTED_API06_CANDIDATE_FILENAME,
        "candidate_sha256": ACCEPTED_API06_CANDIDATE_SHA256,
        "candidate_size": ACCEPTED_API06_CANDIDATE_SIZE_BYTES,
        "authoritative_run_id": ACCEPTED_API06_AUTHORITATIVE_RUN_ID,
        "authoritative_job_id": ACCEPTED_API06_AUTHORITATIVE_JOB_ID,
        "authoritative_passed_gates": 40,
    }


def verify_binding_evidence(repo_root: pathlib.Path) -> dict[str, Any]:
    path = repo_root / BINDING_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError(f"required API-06 binding evidence is missing: {BINDING_RELATIVE_PATH}")
    evidence = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "stage": "OPS-03",
        "dependency": "API-06",
        "state": "ACCEPTED_CLOSED",
        "candidate_filename": ACCEPTED_API06_CANDIDATE_FILENAME,
        "candidate_sha256": ACCEPTED_API06_CANDIDATE_SHA256,
        "candidate_size": ACCEPTED_API06_CANDIDATE_SIZE_BYTES,
        "authoritative_run_id": ACCEPTED_API06_AUTHORITATIVE_RUN_ID,
        "authoritative_job_id": ACCEPTED_API06_AUTHORITATIVE_JOB_ID,
        "api_layer_state": "CLOSED",
        "binding_result": "PASS",
        "system_trial_preview_state": "NOT_OPEN",
    }
    defects = [
        f"{key}: {evidence.get(key)!r} != {value!r}"
        for key, value in expected.items()
        if evidence.get(key) != value
    ]
    if defects:
        raise RuntimeError("stale/forged API-06 binding evidence: " + "; ".join(defects))
    return evidence


def verify_archive(path: pathlib.Path) -> tuple[dict[str, Any], str]:
    if path.name != ACCEPTED_API06_CANDIDATE_FILENAME:
        raise RuntimeError(
            f"accepted API-06 candidate filename mismatch: {path.name!r} != "
            f"{ACCEPTED_API06_CANDIDATE_FILENAME!r}"
        )
    if path.stat().st_size != ACCEPTED_API06_CANDIDATE_SIZE_BYTES:
        raise RuntimeError("accepted API-06 candidate size mismatch")
    if _sha256(path) != ACCEPTED_API06_CANDIDATE_SHA256:
        raise RuntimeError("accepted API-06 candidate SHA-256 mismatch")
    archive, prefix = runtime_binding.verify_archive(path)
    archive["filename"] = path.name
    return archive, prefix


def qualify(repo_root: pathlib.Path, artifact: pathlib.Path) -> dict[str, Any]:
    acceptance = verify_acceptance_record(repo_root)
    binding = verify_binding_evidence(repo_root)
    archive, prefix = verify_archive(artifact)
    runtime = runtime_binding.run_runtime_load_soak(artifact, prefix)
    return {
        "accepted_api06_record": acceptance,
        "accepted_api06_binding_evidence": binding,
        "accepted_api06_archive": archive,
        "accepted_api06_runtime_load_soak": runtime,
        "production_capacity_claim": False,
        "production_rto_rpo_claim": False,
        "system_trial_preview_opened": False,
    }
'''


TEST_MODULE = r'''from __future__ import annotations

import copy
import json
import os
import pathlib

import pytest

from epd2_qualification import api06_binding_c2

ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORD = ROOT / "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json"
BINDING = ROOT / "validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"
OLD_MAIN = "217559b7f21c338d6fe8d4e4676082cd3840251c"


def _write_record(tmp_path: pathlib.Path, record: dict) -> pathlib.Path:
    path = tmp_path / "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    return tmp_path


def test_exact_canonical_api06_acceptance_record_passes() -> None:
    result = api06_binding_c2.verify_acceptance_record(ROOT)
    assert result["decision"] == "ACCEPTED_CLOSED"
    assert result["authoritative_job_id"] == 100243984921


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("decision",), "NEXT"),
        (("api_layer_state",), "OPEN"),
        (("candidate", "filename"), "wrong.zip"),
        (("candidate", "sha256"), "0" * 64),
        (("candidate", "size_bytes"), 44012715),
        (("candidate", "self_accepted"), True),
        (("authoritative", "run_id"), 1),
        (("authoritative", "job_id"), 1),
        (("authoritative", "conclusion"), "FAILURE"),
        (("authoritative", "passed_gates"), 39),
    ],
)
def test_forged_or_stale_api06_acceptance_record_fails_closed(
    tmp_path: pathlib.Path, path: tuple[str, ...], value: object
) -> None:
    record = copy.deepcopy(json.loads(RECORD.read_text(encoding="utf-8")))
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    root = _write_record(tmp_path, record)
    with pytest.raises(RuntimeError, match="forged/stale"):
        api06_binding_c2.verify_acceptance_record(root)


def test_exact_sealed_api06_archive_identity_is_rechecked() -> None:
    path = pathlib.Path(os.environ["EPD2_OPS03_ACCEPTED_API06_ZIP"])
    archive, _ = api06_binding_c2.verify_archive(path)
    assert archive["filename"] == api06_binding_c2.ACCEPTED_API06_CANDIDATE_FILENAME
    assert archive["sha256"] == api06_binding_c2.ACCEPTED_API06_CANDIDATE_SHA256
    assert archive["size_bytes"] == api06_binding_c2.ACCEPTED_API06_CANDIDATE_SIZE_BYTES


def test_missing_api_binding_fails_closed(tmp_path: pathlib.Path) -> None:
    with pytest.raises(RuntimeError, match="binding evidence is missing"):
        api06_binding_c2.verify_binding_evidence(tmp_path)


def test_exact_api_binding_evidence_is_present() -> None:
    evidence = api06_binding_c2.verify_binding_evidence(ROOT)
    assert evidence["binding_result"] == "PASS"
    assert evidence["authoritative_job_id"] == 100243984921


def test_old_entering_baseline_is_rejected_by_the_c2_identity() -> None:
    baseline = json.loads(
        (ROOT / "docs/ops/OPS-03/OPS03_ENTERING_BASELINE_IDENTITY.json").read_text(
            encoding="utf-8"
        )
    )
    assert baseline["base_commit"] != OLD_MAIN
    assert baseline["api06_state_at_entry"] == "ACCEPTED_CLOSED"
    assert baseline["api_layer_state_at_entry"] == "CLOSED"


def test_ops03_candidate_never_self_accepts_or_opens_system_trial_preview() -> None:
    state = json.loads((ROOT / "OPS03_CANDIDATE_SELF_STATE.json").read_text(encoding="utf-8"))
    assert state["candidate_self_state"] == "CANDIDATE_NOT_ACCEPTED"
    assert state["self_accepted"] is False
    assert state["system_trial_preview_state"] == "NOT_OPEN"
'''


def _patch_validator(root: pathlib.Path) -> None:
    path = root / "scripts/validation/validate_ops03.py"
    text = path.read_text(encoding="utf-8")
    old = "from epd2_qualification import api06_binding\n"
    new = "from epd2_qualification import api06_binding_c2 as api06_binding\n"
    if old not in text:
        raise SystemExit("G05 API-06 import insertion point not found after C1 patch")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def _patch_preview_prerequisite(root: pathlib.Path) -> None:
    path = root / "packages/python/epd2-qualification/src/epd2_qualification/preview_minimum.py"
    text = path.read_text(encoding="utf-8")
    start_marker = '    Prerequisite(\n        "PRQ-OPS03-16",'
    next_marker = '    Prerequisite(\n        "PRQ-OPS03-17",'
    start = text.find(start_marker)
    end = text.find(next_marker, start + 1)
    if start < 0 or end < 0:
        raise SystemExit("PRQ-OPS03-16 block not found")
    replacement = '''    Prerequisite(\n        "PRQ-OPS03-16",\n        "The exact accepted API-06 runtime is bound and operationally qualified",\n        "OPS",\n        ("G05",),\n        ("validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json",),\n    ),\n'''
    text = text[:start] + replacement + text[end:]
    path.write_text(text, encoding="utf-8")


def _update_candidate_state(root: pathlib.Path, main_commit: str, main_tree: str) -> None:
    baseline_path = root / "docs/ops/OPS-03/OPS03_ENTERING_BASELINE_IDENTITY.json"
    baseline = _load(baseline_path)
    if baseline.get("base_commit") != main_commit or baseline.get("base_tree") != main_tree:
        raise SystemExit(
            "reconciler did not bind the requested current main: "
            f"{baseline.get('base_commit')} / {baseline.get('base_tree')}"
        )
    baseline.update(
        {
            "accepted_api06_candidate_filename": API06_FILENAME,
            "accepted_api06_candidate_sha256": API06_SHA256,
            "accepted_api06_candidate_size_bytes": API06_SIZE,
            "accepted_api06_authoritative_run": API06_RUN,
            "accepted_api06_authoritative_job": API06_JOB,
            "api06_state_at_entry": "ACCEPTED_CLOSED",
            "api_layer_state_at_entry": "CLOSED",
            "system_trial_preview_state_at_entry": "NOT_OPENED",
            "next_permitted_stage": "INFRA/OPS PREVIEW-READINESS MINIMUM",
            "c1_stale_entering_main_commit": OLD_MAIN,
            "c1_stale_entering_main_tree": OLD_TREE,
        }
    )
    baseline["governed_path"] = [
        "API-06 ACCEPTED / CLOSED",
        "API layer CLOSED",
        "INFRA/OPS PREVIEW-READINESS MINIMUM may be qualified",
        "System Trial Preview remains NOT OPEN until a separate governed checkpoint-opening decision",
    ]
    _write_json(baseline_path, baseline)

    state_path = root / "OPS03_CANDIDATE_SELF_STATE.json"
    state = _load(state_path)
    state.update(
        {
            "candidate_role": "C2",
            "candidate_self_state": "CANDIDATE_NOT_ACCEPTED",
            "self_accepted": False,
            "harness": "PASS_TARGET_REQUALIFICATION",
            "api06_state": "ACCEPTED_CLOSED",
            "api_layer_state": "CLOSED",
            "system_trial_preview_state": "NOT_OPEN",
            "entering_main_commit": main_commit,
            "entering_main_tree": main_tree,
            "accepted_api06_candidate_filename": API06_FILENAME,
            "accepted_api06_candidate_sha256": API06_SHA256,
            "accepted_api06_candidate_size_bytes": API06_SIZE,
            "accepted_api06_authoritative_run": API06_RUN,
            "accepted_api06_authoritative_job": API06_JOB,
            "declared_blockers": [],
        }
    )
    state["nonclaims"] = [
        "OPS-03 is not accepted or closed by these candidate bytes",
        "System Trial Preview is NOT OPEN and requires a separate governed checkpoint-opening decision",
        "no production-capacity or production RTO/RPO claim is made",
        "no production-readiness claim is made",
        "no BSI, Common Criteria or EAL4 claim is made",
        "no legal-activation claim is made",
    ]
    _write_json(state_path, state)


def _write_binding(root: pathlib.Path, main_commit: str, main_tree: str, artifact: pathlib.Path) -> None:
    binding = {
        "schema": "epd2.ops03.api06-accepted-runtime-binding/1",
        "stage": "OPS-03",
        "dependency": "API-06",
        "state": "ACCEPTED_CLOSED",
        "candidate_filename": API06_FILENAME,
        "candidate_sha256": API06_SHA256,
        "candidate_size": API06_SIZE,
        "candidate_size_bytes": API06_SIZE,
        "authoritative_run_id": API06_RUN,
        "authoritative_job_id": API06_JOB,
        "api_layer_state": "CLOSED",
        "canonical_acceptance_record": "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json",
        "artifact_filename_observed": artifact.name,
        "artifact_sha256_observed": _sha256(artifact),
        "artifact_size_observed": artifact.stat().st_size,
        "entering_main_commit": main_commit,
        "entering_main_tree": main_tree,
        "c1_stale_entering_main_commit": OLD_MAIN,
        "system_trial_preview_state": "NOT_OPEN",
        "preview_boundary": (
            "OPS-03 may qualify preview-readiness minimum; System Trial Preview remains NOT OPEN "
            "until a separate governed checkpoint-opening decision"
        ),
        "binding_result": "PASS",
    }
    _write_json(root / BINDING_REL, binding)


def _write_internal_report(root: pathlib.Path, main_commit: str, main_tree: str) -> None:
    report = "# OPS-03 C2 corrective developer report (inside candidate)\n\n"
    report += "Status: `CANDIDATE_NOT_ACCEPTED`\n\n"
    report += (
        "This C2 is a surgical governance/runtime-binding correction of C1. "
        "The OPS-03 functional implementation is not redesigned.\n\n"
    )
    report += f"- C1 stale baseline: `main@{OLD_MAIN}` / tree `{OLD_TREE}`.\n"
    report += f"- C2 entering canonical main: `{main_commit}` / tree `{main_tree}`.\n"
    report += (
        f"- Exact API-06: `{API06_FILENAME}`, SHA-256 `{API06_SHA256}`, size `{API06_SIZE}`, "
        f"authoritative run `{API06_RUN}`, job `{API06_JOB}`, state `ACCEPTED_CLOSED`, "
        "API layer `CLOSED`.\n"
    )
    report += "- G05 correction: API-06 CLOSED is now mandatory; filename, SHA-256, size, authoritative run, authoritative job, canonical acceptance record, sealed artifact bytes and runtime load/soak are all fail-closed inputs.\n"
    report += f"- Frozen binding evidence: `{BINDING_REL}`.\n"
    report += "- Full governed qualification target: `50/50 PASS`; mutation target remains exactly `24/24 DETECTED`.\n"
    report += "- OPS-01 and OPS-02 predecessor regression must pass before terminal C2 qualification is accepted as builder evidence.\n"
    report += "- `OPS-03 may qualify preview-readiness minimum`; `SYSTEM TRIAL PREVIEW remains NOT OPEN until separate governed checkpoint-opening decision`.\n"
    report += "- Final ZIP SHA-256 and size are deliberately recorded outside the ZIP after packaging to avoid a circular self-hash claim.\n"
    (root / "docs/ops/OPS-03/OPS03_C2_CORRECTION_DEVELOPER_REPORT.md").write_text(report, encoding="utf-8")


def _assert_no_stale_current_logic(root: pathlib.Path) -> None:
    files = [
        root / "packages/python/epd2-qualification/src/epd2_qualification/preview_minimum.py",
        root / "scripts/validation/validate_ops03.py",
        root / "tests/ops03/test_ops03_declarations.py",
    ]
    forbidden = (
        "API-06 is NEXT and the API layer is open",
        "API-06 ACCEPTED means stale baseline",
        "re-bootstrap required because API closed",
    )
    hits = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            if phrase in text:
                hits.append(f"{path.relative_to(root)}: {phrase}")
    if hits:
        raise SystemExit("stale current-path API-06 logic remains: " + "; ".join(hits))


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: ops03_c2_harden_g05.py ROOT MAIN_COMMIT MAIN_TREE")
    root = pathlib.Path(sys.argv[1]).resolve()
    main_commit = sys.argv[2]
    main_tree = sys.argv[3]
    if main_commit == OLD_MAIN:
        raise SystemExit("C2 cannot enter from the stale C1 main")
    _verify_api06_record(root)
    artifact = _verify_api06_artifact()
    _update_candidate_state(root, main_commit, main_tree)
    _write_binding(root, main_commit, main_tree, artifact)
    module_path = root / "packages/python/epd2-qualification/src/epd2_qualification/api06_binding_c2.py"
    module_path.write_text(STRICT_MODULE, encoding="utf-8")
    (root / "tests/ops03/test_ops03_c2_api06_binding.py").write_text(TEST_MODULE, encoding="utf-8")
    _patch_validator(root)
    _patch_preview_prerequisite(root)
    _write_internal_report(root, main_commit, main_tree)
    _assert_no_stale_current_logic(root)
    print(
        "OPS03_C2_G05_HARDEN:PASS:"
        f"{main_commit}:{main_tree}:{API06_SHA256}:{API06_RUN}:{API06_JOB}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
