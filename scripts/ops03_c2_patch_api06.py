from __future__ import annotations

import pathlib
import sys

API06_SHA = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
API06_SIZE = 44012716

MODULE = r'''"""Exact accepted API-06 binding and bounded operational qualification for OPS-03 C2."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import zipfile
from typing import Any

ACCEPTED_API06_CANDIDATE_SHA256 = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
ACCEPTED_API06_CANDIDATE_SIZE_BYTES = 44012716
ACCEPTED_API06_BUILDER_RUN_ID = 33628261946
ACCEPTED_API06_AUTHORITATIVE_RUN_ID = 33629147572
ARTIFACT_ENV = "EPD2_OPS03_ACCEPTED_API06_ZIP"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_from_env() -> pathlib.Path:
    raw = os.environ.get(ARTIFACT_ENV, "").strip()
    if not raw:
        raise RuntimeError(f"{ARTIFACT_ENV} is not set")
    path = pathlib.Path(raw)
    if not path.is_file():
        raise RuntimeError(f"accepted API-06 candidate is not a file: {path}")
    return path


def verify_acceptance_record(repo_root: pathlib.Path) -> dict[str, Any]:
    path = repo_root / "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json"
    if not path.is_file():
        raise RuntimeError("canonical API-06 acceptance record is missing")
    record = json.loads(path.read_text(encoding="utf-8"))
    candidate = record.get("candidate", {})
    authoritative = record.get("authoritative", {})
    defects: list[str] = []
    if record.get("decision") != "ACCEPTED_CLOSED":
        defects.append("API-06 decision is not ACCEPTED_CLOSED")
    if record.get("api_layer_state") != "CLOSED":
        defects.append("API layer is not CLOSED in the API-06 acceptance record")
    if candidate.get("sha256") != ACCEPTED_API06_CANDIDATE_SHA256:
        defects.append("API-06 accepted candidate SHA does not match the bound C2 identity")
    if candidate.get("size_bytes") != ACCEPTED_API06_CANDIDATE_SIZE_BYTES:
        defects.append("API-06 accepted candidate size does not match the bound C2 identity")
    if candidate.get("self_accepted") is not False:
        defects.append("API-06 candidate record violates no-self-acceptance")
    if authoritative.get("conclusion") != "SUCCESS":
        defects.append("API-06 authoritative acceptance conclusion is not SUCCESS")
    if authoritative.get("passed_gates") != 40 or authoritative.get("failed_gates") != 0:
        defects.append("API-06 authoritative acceptance is not exact 40/40 PASS")
    if authoritative.get("run_id") != ACCEPTED_API06_AUTHORITATIVE_RUN_ID:
        defects.append("API-06 authoritative run identity drifted")
    if record.get("open_blockers") != []:
        defects.append("API-06 acceptance record still has open blockers")
    if defects:
        raise RuntimeError("; ".join(defects))
    return {
        "decision": record["decision"],
        "api_layer_state": record["api_layer_state"],
        "candidate_sha256": candidate["sha256"],
        "candidate_size_bytes": candidate["size_bytes"],
        "builder_run_id": candidate.get("builder_run_id"),
        "authoritative_run_id": authoritative.get("run_id"),
        "authoritative_passed_gates": authoritative.get("passed_gates"),
    }


def _archive_root(names: list[str]) -> str:
    roots = {
        name.split("/", 1)[0]
        for name in names
        if "/" in name and not name.startswith("__MACOSX/")
    }
    if len(roots) != 1:
        raise RuntimeError(f"accepted API-06 archive has ambiguous roots: {sorted(roots)}")
    return next(iter(roots)) + "/"


def verify_archive(path: pathlib.Path) -> tuple[dict[str, Any], str]:
    observed_sha = sha256_file(path)
    observed_size = path.stat().st_size
    if observed_sha != ACCEPTED_API06_CANDIDATE_SHA256:
        raise RuntimeError(
            f"accepted API-06 candidate SHA mismatch: {observed_sha} != {ACCEPTED_API06_CANDIDATE_SHA256}"
        )
    if observed_size != ACCEPTED_API06_CANDIDATE_SIZE_BYTES:
        raise RuntimeError(
            f"accepted API-06 candidate size mismatch: {observed_size} != {ACCEPTED_API06_CANDIDATE_SIZE_BYTES}"
        )

    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"accepted API-06 ZIP integrity failure at {bad}")
        names = zf.namelist()
        prefix = _archive_root(names)
        sums_name = prefix + "SHA256SUMS.txt"
        if sums_name not in names:
            raise RuntimeError("accepted API-06 archive has no SHA256SUMS.txt")
        rows = zf.read(sums_name).decode("utf-8").splitlines()
        verified = 0
        for row in rows:
            if not row.strip():
                continue
            digest, rel = row.split(None, 1)
            rel = rel.strip()
            member = prefix + rel
            if member not in names:
                raise RuntimeError(f"API-06 sealed member missing: {rel}")
            actual = _sha256_bytes(zf.read(member))
            if actual != digest:
                raise RuntimeError(f"API-06 sealed member digest mismatch: {rel}")
            verified += 1

        identity_name = prefix + "docs/api/API-06/API06_CANDIDATE_IDENTITY.json"
        seal_name = prefix + "docs/api/API-06/API06_C1_SEAL_RECORD.json"
        identity = json.loads(zf.read(identity_name))
        seal = json.loads(zf.read(seal_name))
        if (
            identity.get("state") != "CANDIDATE_NOT_ACCEPTED"
            or identity.get("self_accepted") is not False
        ):
            raise RuntimeError("accepted API-06 sealed identity violates no-self-acceptance")
        if identity.get("builder_run_id") != ACCEPTED_API06_BUILDER_RUN_ID:
            raise RuntimeError("accepted API-06 sealed builder identity drifted")
        if (
            seal.get("governed_gates") != "40/40 PASS"
            or seal.get("mutations") != "30/30 detected"
        ):
            raise RuntimeError("accepted API-06 sealed gate/mutation evidence is not terminal PASS")

    return (
        {
            "sha256": observed_sha,
            "size_bytes": observed_size,
            "sealed_members_verified": verified,
            "sealed_identity_state": identity.get("state"),
            "sealed_builder_run_id": identity.get("builder_run_id"),
            "sealed_gates": seal.get("governed_gates"),
            "sealed_mutations": seal.get("mutations"),
        },
        prefix,
    )


def run_runtime_load_soak(path: pathlib.Path, prefix: str) -> dict[str, Any]:
    runtime_prefix = prefix + "services/api-closure-runtime/src/"
    with tempfile.TemporaryDirectory(prefix="epd2-ops03-api06-") as tmp:
        tmp_path = pathlib.Path(tmp)
        with zipfile.ZipFile(path) as zf:
            members = [
                name
                for name in zf.namelist()
                if name.startswith(runtime_prefix) and not name.endswith("/")
            ]
            if not members:
                raise RuntimeError("accepted API-06 archive has no api-closure-runtime source")
            for member in members:
                rel = pathlib.PurePosixPath(member).relative_to(runtime_prefix)
                target = tmp_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))

        program = r"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from epd2_api_closure_runtime import (
    ApiError,
    AuthoritySnapshot,
    ClosureGuard,
    EndpointPolicy,
    IdempotencyLedger,
    RequestContext,
)

now = datetime.now(UTC)
authority = AuthoritySnapshot(
    principal_id="principal:ops03-c2",
    audience="epd2-api",
    authorities=frozenset({"authority:representative-write"}),
    organization_scope="org:qualification",
    region_scope="region:qualification",
    issued_at=now - timedelta(minutes=1),
    expires_at=now + timedelta(hours=1),
    generation=7,
)
policy = EndpointPolicy(
    route_id="OPS03-C2-API06-QUALIFICATION",
    method="POST",
    required_authority="authority:representative-write",
    audience="epd2-api",
    organization_scope="org:qualification",
    region_scope="region:qualification",
    mutation=True,
    commit_time_reauthorization=True,
    idempotency_required=True,
    max_body_bytes=4096,
    allowed_fields=frozenset({"value"}),
)
context = RequestContext(authority=authority, now=now, body_size=32, json_depth=1)
guard = ClosureGuard()

start = time.perf_counter()
validated = 0
for i in range(12000):
    got = guard.validate_request(policy, context, {"value": i % 17})
    if got is None or got.principal_id != authority.principal_id:
        raise AssertionError("closure guard lost accepted authority under load")
    guard.reauthorize_commit(policy, authority, authority, now)
    validated += 1

guard_elapsed = time.perf_counter() - start
ledger = IdempotencyLedger()
counter = 0
counter_lock = threading.Lock()


def operation():
    global counter
    with counter_lock:
        counter += 1
    return {"result": "committed"}


def one_call(_):
    result, replayed = ledger.execute(
        authority.principal_id,
        "ops03-c2-idempotency-key",
        {"value": 1},
        operation,
    )
    if result != {"result": "committed"}:
        raise AssertionError("unexpected idempotency result")
    return replayed


start = time.perf_counter()
with ThreadPoolExecutor(max_workers=16) as pool:
    replay_flags = list(pool.map(one_call, range(8000)))
ledger_elapsed = time.perf_counter() - start
if counter != 1:
    raise AssertionError(f"consequential operation executed {counter} times")
if sum(replay_flags) != 7999:
    raise AssertionError("idempotency replay accounting mismatch")

conflict_refused = False
try:
    ledger.execute(
        authority.principal_id,
        "ops03-c2-idempotency-key",
        {"value": 2},
        operation,
    )
except ApiError as exc:
    conflict_refused = exc.code == "IDEMPOTENCY_CONFLICT" and exc.http_status == 409
if not conflict_refused:
    raise AssertionError("idempotency key reuse with another payload was not refused")

print(json.dumps({
    "guard_operations": validated,
    "guard_elapsed_seconds": round(guard_elapsed, 6),
    "idempotency_calls": len(replay_flags),
    "idempotency_replays": sum(replay_flags),
    "consequential_executions": counter,
    "ledger_elapsed_seconds": round(ledger_elapsed, 6),
    "conflicting_payload_refused": conflict_refused,
    "errors": 0,
}, sort_keys=True))
"""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)
        completed = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "accepted API-06 runtime qualification failed: "
                + (completed.stderr.strip() or completed.stdout.strip())[-2000:]
            )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError("accepted API-06 runtime qualification emitted no result")
        result = json.loads(lines[-1])
        if result.get("errors") != 0:
            raise RuntimeError("accepted API-06 runtime qualification reported errors")
        if result.get("guard_operations") != 12000:
            raise RuntimeError("accepted API-06 guard load accounting is incomplete")
        if (
            result.get("idempotency_calls") != 8000
            or result.get("consequential_executions") != 1
        ):
            raise RuntimeError("accepted API-06 idempotency soak accounting is incomplete")
        if result.get("conflicting_payload_refused") is not True:
            raise RuntimeError("accepted API-06 conflicting idempotency payload was not refused")
        return result


def qualify(repo_root: pathlib.Path, artifact: pathlib.Path) -> dict[str, Any]:
    acceptance = verify_acceptance_record(repo_root)
    archive, prefix = verify_archive(artifact)
    runtime = run_runtime_load_soak(artifact, prefix)
    return {
        "accepted_api06_record": acceptance,
        "accepted_api06_archive": archive,
        "accepted_api06_runtime_load_soak": runtime,
        "production_capacity_claim": False,
        "production_rto_rpo_claim": False,
    }
'''


def patch_validator(root: pathlib.Path) -> None:
    path = root / "scripts/validation/validate_ops03.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("    def g05_api_binding(self, result: GateResult) -> None:\n")
    end = text.index("\n    def g06_governance_freshness", start)
    replacement = '''    def g05_api_binding(self, result: GateResult) -> None:\n        from epd2_qualification import api06_binding\n\n        register = (self.repo_root / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md").read_text(\n            encoding="utf-8"\n        )\n        api_rows = [line for line in register.splitlines() if line.startswith("| API |")]\n        if len(api_rows) != 1:\n            raise GateFailure(\n                f"the register declares {len(api_rows)} API rows; exactly one is required"\n            )\n        row = api_rows[0]\n        upper = row.upper()\n        result.measurements["api_row"] = row.strip()\n        if ("API-06 " + "ACCEPTED") not in upper:\n            _fail(result, ["the register does not record API-06 as accepted"])\n        if ("API LAYER " + "CLOSED") not in upper:\n            _fail(result, ["the register does not record the API layer as closed"])\n\n        try:\n            artifact = api06_binding.artifact_from_env()\n            qualification = api06_binding.qualify(self.repo_root, artifact)\n        except Exception as exc:  # gate reports exact dependency failure, never assumes PASS\n            _fail(result, [f"exact accepted API-06 qualification failed: {exc}"])\n            return\n\n        result.measurements.update(qualification)\n        result.measurements["accepted_api06_candidate_sha256"] = (\n            api06_binding.ACCEPTED_API06_CANDIDATE_SHA256\n        )\n        result.observations.append(\n            "exact accepted API-06 C1 bytes were digest-bound and exercised under bounded "\n            "representative load/soak; this is trial qualification, not production capacity"\n        )\n'''
    text = text[:start] + replacement + text[end:]
    old = (
        "declared_sha256=ACCEPTED_OPS02_CANDIDATE_SHA256,\n"
        "            observed_sha256=\"0\" * 64,\n"
        "            stage=\"OPS-02\","
    )
    new = (
        f"declared_sha256=\"{API06_SHA}\",\n"
        "            observed_sha256=\"0\" * 64,\n"
        "            stage=\"API-06\","
    )
    if old not in text:
        raise RuntimeError("MUT-02 API runtime mutation anchor not found")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_docs(root: pathlib.Path) -> None:
    known = root / "docs/ops/OPS-03/OPS03_KNOWN_LIMITATIONS.md"
    if known.is_file():
        text = known.read_text(encoding="utf-8")
        text = text.replace(
            "**G05 is BLOCKED.** Load and soak qualification was executed against the OPS-owned runtime, not against the accepted final API runtime, because none exists: API-06 is `NEXT` and the API layer is open.",
            "**G05 prerequisite resolved in C2.** The exact accepted API-06 C1 archive is digest-bound and its closure runtime is exercised under bounded representative load/soak in addition to the OPS-owned runtime qualification.",
        )
        text = text.replace(
            "API-06 authoritative acceptance and API layer closure",
            "RESOLVED — exact accepted API-06 C1 authoritative identity bound in C2",
        )
        known.write_text(text, encoding="utf-8")

    addendum = root / "docs/ops/OPS-03/OPS03_C2_API06_BINDING.md"
    addendum.write_text(
        "# OPS-03 C2 — accepted API-06 binding\n\n"
        f"C2 binds the independently accepted API-06 C1 candidate at SHA-256 `{API06_SHA}` "
        f"and exact size `{API06_SIZE}` bytes. G05 verifies the canonical API-06 acceptance "
        "record, the exact archive identity, the archive's internal SHA256 seal, its no-self-acceptance "
        "state, and executes bounded representative load/soak against `api-closure-runtime`.\n\n"
        "This closes the C1 dependency blocker only. It does not claim production capacity, "
        "production RTO/RPO, OPS-layer closure, System Trial Preview opening, legal activation, "
        "or security certification.\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c2_patch_api06.py ROOT")
    root = pathlib.Path(sys.argv[1]).resolve()
    module = root / "packages/python/epd2-qualification/src/epd2_qualification/api06_binding.py"
    module.parent.mkdir(parents=True, exist_ok=True)
    module.write_text(MODULE, encoding="utf-8")
    patch_validator(root)
    patch_docs(root)
    print(f"OPS03_C2_API06_PATCH:PASS:{API06_SHA}:{API06_SIZE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
