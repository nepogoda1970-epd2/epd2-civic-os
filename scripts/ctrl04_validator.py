#!/usr/bin/env python3
"""CTRL-04 fifty-two-gate developer validator.

Every gate executes a probe against the real runtime, the repository or a
governed evidence file, and records what it observed. A gate PASSes only on
the evidence its probe produced; no gate inherits PASS from another gate.
The validator emits `CTRL04_RESULT:PASS|FAIL:<n>/52_PASS` and a PRESEAL
result file whose self-state is always `CANDIDATE_NOT_ACCEPTED`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services/control-plane-service"
VALIDATION = ROOT / "validation/ctrl04"
sys.path.insert(0, str(SERVICE / "src"))
sys.path.insert(0, str(SERVICE / "tests"))
sys.path.insert(0, str(ROOT / "packages/python/epd2-core/src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ctrl04_common import runtime_source_digest  # type: ignore[import-not-found]  # noqa: E402

BASE_COMMIT = "8a4d336589f2322984dbf03b1af3b5a575643005"
BASE_TREE = "ee38a1a51f70f4c9652dd75eab4d0d1034d7135c"
MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
SELF_STATE = "CANDIDATE_NOT_ACCEPTED"

PREDECESSORS = {
    "CTRL-01": (
        "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json",
        "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5",
        190099,
    ),
    "CTRL-02": (
        "docs/ctrl/CTRL-02/CTRL02_ACCEPTANCE_RECORD.json",
        "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e",
        16720456,
    ),
    "CTRL-03": (
        "docs/ctrl/CTRL-03/CTRL03_C1_ACCEPTANCE_RECORD.json",
        "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff",
        16788860,
    ),
}
INFRA = {
    "INFRA-01": (
        "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
        "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
        15854311,
    ),
    "INFRA-02": (
        "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json",
        "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
        15980332,
    ),
}
OPS = {
    "OPS-01": (
        "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json",
        "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27",
        16457357,
    ),
    "OPS-02": (
        "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json",
        "ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125",
        16632939,
    ),
}
NOT_ACCEPTED_DEPENDENCIES = ("INFRA-03", "OPS-03")

GATE_NAMES = (
    "exact_repository_baseline_recorded",
    "mandatory_bootstrap_docs_read_and_digested",
    "exact_ctrl01_accepted_identity_bound",
    "exact_ctrl02_accepted_identity_bound",
    "exact_ctrl03_accepted_identity_bound",
    "relevant_infra_accepted_identities_bound",
    "relevant_ops_accepted_identities_bound",
    "no_universal_admin_capability",
    "no_raw_secret_key_exposure",
    "no_direct_provider_coupling_in_control_api",
    "no_voting_isolation_bypass",
    "no_governance_political_authority_inheritance",
    "no_historical_evidence_mutation",
    "read_vs_execute_permissions_separated",
    "typed_target_identity",
    "typed_action_request",
    "typed_approval_state",
    "typed_execution_state",
    "typed_final_result",
    "explicit_deployment_identity",
    "explicit_environment_scope",
    "explicit_regional_scope_context",
    "unsupported_backend_capability_fails_explicitly",
    "dispatch_acknowledgement_is_not_success",
    "partial_failure_represented_explicitly",
    "cancellation_expiry_represented_explicitly",
    "request_time_authorization",
    "approval_authorization_where_required",
    "execution_authorization_separate_from_approval",
    "commit_time_reauthorization",
    "stale_authority_rejected",
    "stale_approval_rejected",
    "changed_target_rejected",
    "changed_parameters_digest_rejected",
    "revoked_expired_session_rejected",
    "high_impact_dual_control_path_tested",
    "idempotency_key_enforced",
    "replay_rejected_or_safely_deduplicated",
    "duplicate_execution_prevented",
    "conflicting_concurrent_execution_handled",
    "rollback_semantics_deterministic",
    "maintenance_state_transition_guarded",
    "every_privileged_mutation_has_immutable_action_id",
    "actor_authority_provenance_recorded",
    "target_deployment_identity_recorded",
    "request_parameters_digest_recorded",
    "approval_provenance_recorded",
    "execution_result_evidence_recorded",
    "secret_values_absent_from_evidence",
    "audit_evidence_survives_restart",
    "frontend_api_negative_paths_verified",
    "package_pre_post_verification_and_review_readiness",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(name: str, payload: dict[str, Any]) -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load(name: str) -> dict[str, Any]:
    path = VALIDATION / name
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def refusal(fn: Callable[[], Any]) -> str | None:
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    try:
        fn()
    except AuthorizationRefused as exc:
        return str(exc.reason_code)
    return None


# ---------------------------------------------------------------------------
# Gate probes. Each returns (passed, observations).
# ---------------------------------------------------------------------------

Probe = Callable[[], tuple[bool, dict[str, Any]]]


def g01() -> tuple[bool, dict[str, Any]]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    obs: dict[str, Any] = {
        "observed_commit": head,
        "observed_tree": tree,
        "contract_commit": BASE_COMMIT,
        "contract_tree": BASE_TREE,
        "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
        "master_sha256": sha256(
            ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
        ),
    }
    write("baseline_identity.json", {"schema": "epd2.ctrl04.baseline-identity/1", **obs})
    return bool(head == BASE_COMMIT and tree == BASE_TREE), obs


def g02() -> tuple[bool, dict[str, Any]]:
    docs = [
        "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md",
        "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md",
        "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
        "docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md",
        "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json",
        "docs/ctrl/CTRL-02/CTRL02_ACCEPTANCE_RECORD.json",
        "docs/ctrl/CTRL-03/CTRL03_STAGE_CONTRACT.md",
        "docs/ctrl/CTRL-03/CTRL03_C1_ACCEPTANCE_RECORD.json",
        "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
        "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json",
        "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json",
        "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json",
        "docs/ops/OPS-02/OPS02_C3_PREVIEW_READINESS_DISPOSITION.json",
    ]
    digests = {d: sha256(ROOT / d) if (ROOT / d).is_file() else None for d in docs}
    pcr = (ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md").read_text()
    master = (ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md").read_text()
    firs = [
        "FIR-CTRL-001",
        "FIR-GOV-004",
        "FIR-GOV-005",
        "FIR-SEC-004",
        "FIR-TRUST-002",
        "FIR-OPS-001",
        "FIR-OSS-007",
        "FIR-VOTE-NET-001",
    ]
    obs: dict[str, Any] = {
        "documents": digests,
        "pcr_states_ctrl_layer_open": "CTRL LAYER OPEN" in pcr,
        "pcr_states_ctrl03_closed": "CTRL-03 = ACCEPTED / CLOSED" in pcr,
        "pcr_states_ops03_not_accepted": "OPS-03 QUALIFICATION ELIGIBLE" in pcr,
        "master_firs_present": {f: f in master for f in firs},
    }
    write("bootstrap_digest.json", {"schema": "epd2.ctrl04.bootstrap/1", **obs})
    ok = (
        all(digests.values())
        and obs["pcr_states_ctrl_layer_open"]
        and obs["pcr_states_ctrl03_closed"]
        and all(obs["master_firs_present"].values())
    )
    return ok, obs


def _predecessor(
    stage: str,
    table: dict[str, tuple[str, str, int]],
    sha_key: tuple[str, ...],
    size_key: tuple[str, ...],
) -> tuple[bool, dict[str, Any]]:
    path, expected_sha, expected_size = table[stage]
    record = json.loads((ROOT / path).read_text())
    node: Any = record
    for key in sha_key:
        node = node[key]
    size: Any = record
    for key in size_key:
        size = size[key]
    decision = str(record.get("decision", ""))
    obs: dict[str, Any] = {
        "record": path,
        "record_sha256": sha256(ROOT / path),
        "recorded_candidate_sha256": node,
        "recorded_size": size,
        "expected_sha256": expected_sha,
        "expected_size": expected_size,
        "decision": decision,
    }
    return bool(node == expected_sha and int(size) == expected_size and "ACCEPTED" in decision), obs


def g03() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import CTRL01_ACCEPTED_SHA256

    ok, obs = _predecessor(
        "CTRL-01", PREDECESSORS, ("candidate", "sha256"), ("candidate", "size_bytes")
    )
    obs["runtime_constant_matches"] = obs["expected_sha256"] == CTRL01_ACCEPTED_SHA256
    return bool(ok and obs["runtime_constant_matches"]), obs


def g04() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import CTRL02_ACCEPTED_SHA256

    ok, obs = _predecessor(
        "CTRL-02", PREDECESSORS, ("candidate", "sha256"), ("candidate", "size_bytes")
    )
    obs["runtime_constant_matches"] = obs["expected_sha256"] == CTRL02_ACCEPTED_SHA256
    return bool(ok and obs["runtime_constant_matches"]), obs


def g05() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import CTRL03_ACCEPTED_SHA256

    ok, obs = _predecessor(
        "CTRL-03", PREDECESSORS, ("candidate", "sha256"), ("candidate", "size_bytes")
    )
    obs["runtime_constant_matches"] = obs["expected_sha256"] == CTRL03_ACCEPTED_SHA256
    manifest = json.loads(
        (ROOT / "docs/ctrl/CTRL-03/CTRL03_C1_CANONICAL_INSTALLATION_MANIFEST.json").read_text()
    )
    drift = {}
    for rel, digest in manifest["files"].items():
        path = ROOT / rel
        actual = sha256(path) if path.is_file() else None
        if actual != digest:
            drift[rel] = actual
    obs["installed_ctrl03_payload_files"] = len(manifest["files"])
    obs["installed_ctrl03_payload_drift"] = drift
    return bool(ok and obs["runtime_constant_matches"] and not drift), obs


def g06() -> tuple[bool, dict[str, Any]]:
    results: dict[str, Any] = {}
    for stage in INFRA:
        ok, obs = _predecessor(stage, INFRA, ("candidate", "sha256"), ("candidate", "size_bytes"))
        results[stage] = {"bound": ok, **obs}
    results["INFRA-03"] = {
        "bound": False,
        "state": "WORKING_PRESEAL_NOT_ACCEPTED",
        "claimed_as_canonical_dependency": False,
    }
    write(
        "predecessor_dependency_result.json",
        {
            "schema": "epd2.ctrl04.predecessors/1",
            "ctrl": {k: v[1:] for k, v in PREDECESSORS.items()},
            "infra": results,
            "ops": {},
            "not_accepted_dependencies": list(NOT_ACCEPTED_DEPENDENCIES),
        },
    )
    return all(results[s]["bound"] for s in INFRA), results


def g07() -> tuple[bool, dict[str, Any]]:
    results: dict[str, Any] = {}
    for stage in OPS:
        ok, obs = _predecessor(stage, OPS, ("candidate", "sha256"), ("candidate", "size_bytes"))
        results[stage] = {"bound": ok, **obs}
    results["OPS-03"] = {
        "bound": False,
        "state": "QUALIFICATION_ELIGIBLE_NOT_ACCEPTED",
        "claimed_as_canonical_dependency": False,
    }
    payload = load("predecessor_dependency_result.json")
    payload["ops"] = results
    payload["runtime_payload_installed_on_main"] = False
    payload["runtime_binding"] = (
        "by accepted identity and adapter contract only; no OPS/INFRA runtime code imported"
    )
    write("predecessor_dependency_result.json", payload)
    return all(results[s]["bound"] for s in OPS), results


def world(**kwargs: Any) -> Any:
    from _ctrl04_builders import World  # type: ignore[import-not-found]

    return World(**kwargs)


def g08() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import UNIVERSAL_ADMIN_EXISTS, OpsRefusal

    w = world()
    request = refusal(lambda: w.request(principal="root"))
    read = refusal(
        lambda: w.service.authorize_read(
            actor_ref="root",
            session_id="sess-root",
            projection=w.projection("root", "OPS.REQUEST"),
            action_type=__import__(
                "epd2_control_plane_service.operations_console", fromlist=["ActionType"]
            ).ActionType.HEALTH_READ,
            target_id="svc-web",
            now=w.tick(),
        )
    )
    obs: dict[str, Any] = {
        "constant": UNIVERSAL_ADMIN_EXISTS,
        "wildcard_principal_request": request,
        "wildcard_principal_read": read,
    }
    return (
        UNIVERSAL_ADMIN_EXISTS is False
        and request == OpsRefusal.UNIVERSAL_ADMIN.value
        and read == OpsRefusal.UNIVERSAL_ADMIN.value,
        obs,
    )


def g09() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.exceptions import PrivacyBoundaryViolation
    from epd2_control_plane_service.operations_console import OperationsPolicy

    w = world()
    health = w.service.health("svc-web", now=w.now)
    done = w.full_restart()
    surfaces = (
        json.dumps(w.service.read_model(now=w.now))
        + json.dumps(w.service.evidence_record(done.action_id))
        + json.dumps(w.service.checkpoint())
        + json.dumps([r.hashable() for r in w.service.journal.records()])
    )
    leaked = [m for m in ("sk_live_", "hunter2", "-----BEGIN") if m in surfaces]
    weak = world(policy=OperationsPolicy.governed().without("enforce_secret_redaction"))
    try:
        weak.full_restart()
        journal_screen = "NOT_ENFORCED"
    except PrivacyBoundaryViolation as exc:
        journal_screen = str(exc.reason_code)
    obs: dict[str, Any] = {
        "health_api_token": health.details.get("api_token"),
        "redacted_fields": list(health.redacted_fields),
        "leaked_markers": leaked,
        "journal_secret_screen_without_redaction": journal_screen,
    }
    return health.details.get(
        "api_token"
    ) == "[REDACTED]" and not leaked and journal_screen == "CTRL_SECRET_IN_AUDIT", obs


def g10() -> tuple[bool, dict[str, Any]]:
    forbidden = re.compile(
        r"^\s*(import|from)\s+(docker|kubernetes|boto3|paramiko|psycopg|psycopg2|sqlite3|fabric|subprocess|pexpect|asyncssh)\b",
        re.M,
    )
    hits: dict[str, list[str]] = {}
    for name in ("operations_console.py", "operations_api.py"):
        text = (SERVICE / "src/epd2_control_plane_service" / name).read_text()
        found = forbidden.findall(text)
        hits[name] = [f[1] for f in found]
        if "os.system" in text or "shell=True" in text:
            hits[name].append("shell")
    adapters = (SERVICE / "src/epd2_control_plane_service/operations_adapters.py").read_text()
    obs: dict[str, Any] = {
        "control_api_provider_imports": hits,
        "adapter_module_owns_execution": "class LocalProcessAdapter" in adapters
        and "def dispatch" in adapters,
        "console_dispatches_via_protocol": "adapter.dispatch(request)"
        in (SERVICE / "src/epd2_control_plane_service/operations_console.py").read_text(),
    }
    return not any(hits.values()) and obs["adapter_module_owns_execution"] and obs[
        "console_dispatches_via_protocol"
    ], obs


def g11() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import ActionType, OpsRefusal, TargetDomain

    w = world()
    obs: dict[str, Any] = {
        "listed": "svc-voting-tally" in {t.target_id for t in w.service.targets()},
        "request": refusal(lambda: w.request(target_id="svc-voting-tally")),
        "health": refusal(lambda: w.service.health("svc-voting-tally", now=w.now)),
        "read": refusal(
            lambda: w.service.authorize_read(
                actor_ref="reader",
                session_id="sess-reader",
                projection=w.projection("reader", "OPS.READ"),
                action_type=ActionType.STATUS_READ,
                target_id="svc-voting-tally",
                now=w.tick(),
            )
        ),
    }
    action = w.request()
    w.approve(action.action_id)
    w.service.register_target(replace(w.service.target("svc-web"), domain=TargetDomain.VOTING))
    obs["reclassified_at_commit"] = refusal(lambda: w.commit(action.action_id))
    ok = not obs["listed"] and all(
        v == OpsRefusal.VOTING_BOUNDARY.value for k, v in obs.items() if k != "listed"
    )
    return ok, obs


def g12() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import BUND
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    obs: dict[str, Any] = {
        "bund_principal_on_land_target": refusal(
            lambda: w.request(principal="bund-admin", scope=BUND)
        )
    }
    # A grant whose scope is a textual prefix/parent of the target scope, and a
    # grant on a sibling region, both resolve to nothing: containment is equality.
    from epd2_control_plane_service.regional_operations import (
        ActorClass,
        AuthorityGrant,
        ExactScope,
    )

    for gid, region, org in (
        ("g-prefix", "DE-B", "org-berlin"),
        ("g-parent-org", "DE-BE", "org"),
        ("g-wildcard-org", "DE-BE", "org-berlin-*"),
    ):
        w.authorities.add(
            AuthorityGrant(
                gid, "bund-admin", ActorClass.HUMAN, "OPS.REQUEST", ExactScope(region, org), 1
            )
        )
        scope = ExactScope(region, org)

        def attempt(scope: ExactScope = scope) -> Any:
            return w.request(principal="bund-admin", scope=scope)

        obs[gid] = refusal(attempt)
    text = (SERVICE / "src/epd2_control_plane_service/operations_console.py").read_text()
    obs["governance_action_codes_absent"] = not re.search(r"GOV\.|POLITICAL|PARTY_ORGAN", text)
    from epd2_control_plane_service.operations_console import ACTION_CATALOGUE

    obs["catalogue_is_operational_only"] = all(a.value.startswith("OPS.") for a in ACTION_CATALOGUE)
    return bool(
        all(
            obs[k] == OpsRefusal.WRONG_SCOPE.value
            for k in ("bund_principal_on_land_target", "g-prefix", "g-parent-org", "g-wildcard-org")
        )
        and obs["governance_action_codes_absent"]
        and obs["catalogue_is_operational_only"]
    ), obs


def g13() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.exceptions import EvidenceIntegrityError
    from epd2_control_plane_service.operations_adapters import JsonFileStore
    from epd2_control_plane_service.operations_console import OperationsConsoleService, OpsRefusal

    with tempfile.TemporaryDirectory() as td:
        store = JsonFileStore(Path(td) / "s.json")
        w = world(store=store)
        w.full_restart()
        loaded = store.load()
        assert loaded is not None
        loaded["journal"][1]["result"] = "SUCCEEDED-FORGED"
        tampered = refusal(
            lambda: OperationsConsoleService.from_checkpoint(
                loaded,
                authorities=w.authorities,
                signer=w.signer,
                adapters={"reference-adapter": w.adapter},
            )
        )
        loaded2 = store.load()
        assert loaded2 is not None
        loaded2["journal"].pop()
        truncated = refusal(
            lambda: OperationsConsoleService.from_checkpoint(
                loaded2,
                authorities=w.authorities,
                signer=w.signer,
                adapters={"reference-adapter": w.adapter},
            )
        )
        # Whole-chain rewrite with recomputed anchor: refused only by the keyed seal.
        import secrets

        from epd2_control_plane_service.audit import EvidenceJournal
        from epd2_control_plane_service.operations_console import EvidenceSealer

        sealer = EvidenceSealer(secrets.token_bytes(32))
        w.service.sealer = sealer
        w.full_restart()
        sealed = store.load()
        assert sealed is not None
        forged = EvidenceJournal()
        for record in sealed["journal"]:
            forged.append(
                occurred_at=__import__("datetime").datetime.fromisoformat(record["occurred_at"]),
                actor_ref="ghost" if record["result"] == "SUCCEEDED" else record["actor_ref"],
                actor_class=record["actor_class"],
                authority_basis=record["authority_basis"],
                action_id=record["action_id"],
                scope_key=record["scope_key"],
                object_ref=record["object_ref"],
                result=record["result"],
                reason_code=record["reason_code"],
                approval_refs=tuple(record["approval_refs"]),
                correlation_ref=record["correlation_ref"],
                attributes=record["attributes"],
            )
        sealed["journal"] = forged.export()
        sealed["journal_anchor"] = list(forged.anchor())
        rechained = refusal(
            lambda: OperationsConsoleService.from_checkpoint(
                sealed,
                authorities=w.authorities,
                signer=w.signer,
                adapters={"reference-adapter": w.adapter},
                sealer=sealer,
            )
        )
        table_forged = store.load()
        assert table_forged is not None
        any_action = next(iter(table_forged["actions"]))
        table_forged["actions"][any_action]["actor_ref"] = "ghost"
        tables = refusal(
            lambda: OperationsConsoleService.from_checkpoint(
                table_forged,
                authorities=w.authorities,
                signer=w.signer,
                adapters={"reference-adapter": w.adapter},
                sealer=sealer,
            )
        )
        records = w.service.journal._records
        records[0] = replace(records[0], actor_ref="ghost")
        try:
            w.service.journal.verify()
            live = "NOT_DETECTED"
        except EvidenceIntegrityError:
            live = "DETECTED"
    public = [n for n in dir(w.service.journal) if not n.startswith("_")]
    obs: dict[str, Any] = {
        "tampered_checkpoint": tampered,
        "truncated_checkpoint": truncated,
        "rechained_checkpoint_against_seal": rechained,
        "action_table_disagreeing_with_journal": tables,
        "live_rewrite": live,
        "journal_public_surface": public,
    }
    return (
        tampered == OpsRefusal.EVIDENCE_IMMUTABLE.value
        and truncated == OpsRefusal.EVIDENCE_IMMUTABLE.value
        and rechained == OpsRefusal.EVIDENCE_IMMUTABLE.value
        and tables == OpsRefusal.EVIDENCE_IMMUTABLE.value
        and live == "DETECTED"
        and not any(
            n.startswith(("delete", "remove", "update", "rewrite", "truncate")) for n in public
        ),
        obs,
    )


def g14() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import ActionType, OpsRefusal

    w = world()
    target, _grant = w.service.authorize_read(
        actor_ref="readonly-operator",
        session_id="sess-readonly-operator",
        projection=w.projection("readonly-operator", "OPS.READ"),
        action_type=ActionType.HEALTH_READ,
        target_id="svc-web",
        now=w.tick(),
    )
    obs: dict[str, Any] = {
        "read_only_read": target.target_id,
        "read_only_request": refusal(lambda: w.request(principal="readonly-operator")),
    }
    action = w.request()
    w.approve(action.action_id)
    obs["read_only_commit"] = refusal(
        lambda: w.commit(action.action_id, principal="readonly-operator")
    )
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    try:
        w.projection("reader", "OPS.REQUEST")
        obs["reader_has_request_right"] = True
    except AuthorizationRefused:
        obs["reader_has_request_right"] = False
    return obs["read_only_read"] == "svc-web" and obs[
        "read_only_request"
    ] == OpsRefusal.READ_ONLY_SESSION.value and obs[
        "read_only_commit"
    ] == OpsRefusal.READ_ONLY_SESSION.value and not obs["reader_has_request_right"], obs


def g15() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import BERLIN
    from epd2_control_plane_service.operations_console import (
        EnvironmentClass,
        OperationalTarget,
        OpsRefusal,
        TargetClass,
        TargetDomain,
    )

    w = world()
    rejected = []
    for bad in ("*", "ALL", "GLOBAL", "REGION_DISABLED", "has space"):
        try:
            OperationalTarget(
                bad,
                TargetClass.SERVICE,
                TargetDomain.GENERAL,
                EnvironmentClass.PRODUCTION_LIKE,
                BERLIN,
                "dep",
                "a",
                1,
            )
        except ValueError:
            rejected.append(bad)
    obs: dict[str, Any] = {
        "coarse_rejected": rejected,
        "coarse_request": refusal(lambda: w.request(target_id="*")),
        "unknown_request": refusal(lambda: w.request(target_id="svc-none")),
        "target_fields": sorted(OperationalTarget.__dataclass_fields__),
    }
    return len(rejected) == 5 and obs["coarse_request"] == OpsRefusal.COARSE_TARGET.value and obs[
        "unknown_request"
    ] == OpsRefusal.UNKNOWN_TARGET.value and {
        "target_id",
        "target_class",
        "domain",
        "environment",
        "scope",
        "deployment_identity_ref",
        "version",
    } <= set(obs["target_fields"]), obs


def g16() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import (
        OperationalActionRequest,
        OpsRefusal,
        parameters_digest,
    )

    w = world()
    action = w.request(parameters={"reason": "g16", "drain_seconds": "5"})
    obs: dict[str, Any] = {
        "fields": sorted(OperationalActionRequest.__dataclass_fields__),
        "digest_matches": action.parameters_digest
        == parameters_digest({"reason": "g16", "drain_seconds": "5"}),
        "unknown_parameter": refusal(lambda: w.request(parameters={"reason": "x", "shell": "id"})),
        "frozen": OperationalActionRequest.__dataclass_params__.frozen,  # type: ignore[attr-defined]
    }
    required = {
        "action_id",
        "request_id",
        "idempotency_key",
        "action_type",
        "impact",
        "actor_ref",
        "authority_ref",
        "authority_version",
        "target_id",
        "target_version",
        "deployment_identity_ref",
        "environment",
        "scope_key",
        "parameters_digest",
        "policy_version",
        "state",
        "approval_state",
        "execution_state",
        "result_state",
        "review_state",
    }
    return required <= set(obs["fields"]) and obs["digest_matches"] and obs[
        "unknown_parameter"
    ] == OpsRefusal.PARAMETER_INVALID.value and obs["frozen"], obs


def g17() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import ApprovalState, EnvironmentClass

    w = world()
    a = w.request()
    states = [a.approval_state.value]
    w.approve(a.action_id)
    states.append(w.service.action(a.action_id).approval_state.value)
    w.now = w.now + timedelta(minutes=31)
    refusal(lambda: w.commit(a.action_id))
    states.append(w.service.approvals_of(a.action_id)[0].state.value)
    np_world = world(environment=EnvironmentClass.NON_PRODUCTION)
    states.append(np_world.request().approval_state.value)
    obs: dict[str, Any] = {"observed": states, "enum": [s.value for s in ApprovalState]}
    return states == ["PENDING", "GRANTED", "EXPIRED", "NOT_REQUIRED"], obs


def g18() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState
    from epd2_control_plane_service.operations_console import ExecutionState

    w = world()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=1)
    a = w.request()
    seen = [a.execution_state.value]
    w.approve(a.action_id)
    seen.append(w.commit(a.action_id).execution_state.value)
    seen.append(w.resolve(a.action_id).execution_state.value)
    seen.append(w.resolve(a.action_id).execution_state.value)
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=100)
    b = w.request(idempotency_key="g18b")
    w.approve(b.action_id)
    w.commit(b.action_id)
    w.now = w.now + timedelta(minutes=31)
    seen.append(w.resolve(b.action_id).execution_state.value)
    obs: dict[str, Any] = {"observed": seen, "enum": [s.value for s in ExecutionState]}
    return seen == ["NOT_DISPATCHED", "DISPATCHED", "RUNNING", "COMPLETED", "TIMED_OUT"], obs


def g19() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState
    from epd2_control_plane_service.operations_console import ActionState, ResultState

    schema_terminal = {"SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED", "UNSUPPORTED"}
    w = world()
    observed: dict[str, str] = {}
    for state in (
        BackendState.COMPLETED,
        BackendState.FAILED,
        BackendState.PARTIAL,
        BackendState.UNSUPPORTED,
    ):
        w.adapter.inject_outcome("svc-web", state)
        observed[state.value] = w.full_restart().result_state.value
    a = w.request(idempotency_key="g19c")
    w.tick()
    observed["CANCEL"] = w.service.cancel(
        action_id=a.action_id, actor_ref="requester", session_id="sess-requester", now=w.now
    ).result_state.value
    obs: dict[str, Any] = {
        "observed": observed,
        "result_states": [s.value for s in ResultState],
        "terminal_action_states": sorted(
            s.value
            for s in ActionState
            if s.value not in {"REQUESTED", "AWAITING_APPROVAL", "APPROVED", "EXECUTING"}
        ),
    }
    return observed == {
        "COMPLETED": "SUCCEEDED",
        "FAILED": "FAILED",
        "PARTIAL": "PARTIAL_FAILURE",
        "UNSUPPORTED": "UNSUPPORTED",
        "CANCEL": "CANCELLED",
    } and schema_terminal <= set(obs["result_states"]), obs


def g20() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    done = w.full_restart()
    record = w.service.evidence_record(done.action_id)
    identity = w.service.deployment_identity("svc-web")
    a = w.request(idempotency_key="g20")
    w.approve(a.action_id)
    w.service.register_target(
        replace(w.service.target("svc-web"), deployment_identity_ref="dep-web-0")
    )
    obs: dict[str, Any] = {
        "action_ref": done.deployment_identity_ref,
        "evidence_ref": record["deployment_identity_ref"],
        "artifact_digest": None if identity is None else identity.artifact_digest,
        "release_ref": None if identity is None else identity.release_ref,
        "changed_identity_at_commit": refusal(lambda: w.commit(a.action_id)),
    }
    return done.deployment_identity_ref == "dep-web-1" == record["deployment_identity_ref"] and obs[
        "artifact_digest"
    ] == "a" * 64 and obs[
        "changed_identity_at_commit"
    ] == OpsRefusal.STALE_DEPLOYMENT_IDENTITY.value, obs


def g21() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import EnvironmentClass, OpsRefusal

    prod = world()
    a = prod.request()
    non = world(environment=EnvironmentClass.NON_PRODUCTION)
    b = non.request()
    prod.approve(a.action_id)
    prod.service.register_target(
        replace(prod.service.target("svc-web"), environment=EnvironmentClass.NON_PRODUCTION)
    )
    obs: dict[str, Any] = {
        "production_requires": list(a.required_approver_classes),
        "non_production_requires": list(b.required_approver_classes),
        "environment_on_action": a.environment.value,
        "environment_change_at_commit": refusal(lambda: prod.commit(a.action_id)),
    }
    return a.required_approver_classes == (
        "INCIDENT_COMMANDER",
    ) and b.required_approver_classes == () and obs[
        "environment_change_at_commit"
    ] == OpsRefusal.ENVIRONMENT_MISMATCH.value, obs


def g22() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import BAVARIA, BERLIN
    from epd2_control_plane_service.operations_console import OpsRefusal
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.authorities.add(
        AuthorityGrant("g-exec-by", "executor", ActorClass.HUMAN, "OPS.EXECUTE", BAVARIA, 1)
    )
    w.service.register_target(replace(w.service.target("svc-web"), scope=BAVARIA))
    obs: dict[str, Any] = {
        "scope_on_action": a.scope_key,
        "wrong_scope_request": refusal(
            lambda: world().request(principal="bavaria-requester", scope=BAVARIA)
        ),
        "scope_change_at_commit": refusal(lambda: w.commit(a.action_id, scope=BAVARIA)),
        "evidence_region": w.service.evidence_record(a.action_id)["region_scope"],
    }
    return a.scope_key == BERLIN.key and obs[
        "wrong_scope_request"
    ] == OpsRefusal.WRONG_SCOPE.value and obs[
        "scope_change_at_commit"
    ] == OpsRefusal.WRONG_SCOPE.value and obs["evidence_region"] == BERLIN.key, obs


def g23() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState
    from epd2_control_plane_service.operations_console import ActionType

    w = world()
    a = w.request(ActionType.SERVICE_RESTART, "svc-legacy")
    w.approve(a.action_id)
    done = w.commit(a.action_id)
    w.adapter.inject_outcome("svc-web", BackendState.UNSUPPORTED)
    runtime = w.full_restart()
    obs: dict[str, Any] = {
        "capability_missing": done.state.value,
        "classification": w.service.result_of(a.action_id).failure_classification.value,
        "runtime_unsupported": runtime.state.value,
        "dispatch_count": w.adapter.dispatch_count,
    }
    return (
        done.state.value == "UNSUPPORTED"
        and obs["classification"] == "UNSUPPORTED_CAPABILITY"
        and runtime.state.value == "UNSUPPORTED"
        and w.adapter.dispatch_count == 1,
        obs,
    )


def g24() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState
    from epd2_control_plane_service.operations_console import DISPATCH_ACK_IS_SUCCESS

    w = world()
    w.adapter.inject_outcome("svc-web", BackendState.FAILED, polls=1)
    a = w.request()
    w.approve(a.action_id)
    after_commit = w.commit(a.action_id)
    running = w.resolve(a.action_id)
    final = w.resolve(a.action_id)
    obs: dict[str, Any] = {
        "constant": DISPATCH_ACK_IS_SUCCESS,
        "after_dispatch": [after_commit.state.value, after_commit.result_state.value],
        "while_running": [running.state.value, running.result_state.value],
        "final": [final.state.value, final.result_state.value],
    }
    return DISPATCH_ACK_IS_SUCCESS is False and obs["after_dispatch"] == [
        "EXECUTING",
        "PENDING",
    ] and obs["while_running"] == ["EXECUTING", "PENDING"] and obs["final"] == [
        "FAILED",
        "FAILED",
    ], obs


def g25() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState

    w = world()
    w.adapter.inject_outcome("svc-web", BackendState.PARTIAL)
    done = w.full_restart()
    result = w.service.result_of(done.action_id)
    obs: dict[str, Any] = {
        "state": done.state.value,
        "result_state": done.result_state.value,
        "classification": None if result is None else result.failure_classification.value,
        "journal": w.service.journal.records()[-1].result,
    }
    return obs == {
        "state": "PARTIAL_FAILURE",
        "result_state": "PARTIAL_FAILURE",
        "classification": "PARTIAL_PROVIDER_FAILURE",
        "journal": "PARTIAL_FAILURE",
    }, obs


def g26() -> tuple[bool, dict[str, Any]]:
    w = world()
    a = w.request()
    w.tick()
    cancelled = w.service.cancel(
        action_id=a.action_id, actor_ref="requester", session_id="sess-requester", now=w.now
    )
    b = w.request(idempotency_key="g26b")
    w.now = w.now + timedelta(hours=5)
    expired = w.service.expire_due(now=w.now)
    obs: dict[str, Any] = {
        "cancelled": [cancelled.state.value, cancelled.result_state.value],
        "expired_ids": list(expired),
        "expired_state": w.service.action(b.action_id).state.value,
        "journal_tail": [r.result for r in w.service.journal.records()[-2:]],
    }
    return obs["cancelled"] == ["CANCELLED", "CANCELLED"] and expired == (b.action_id,) and obs[
        "expired_state"
    ] == "EXPIRED" and "CANCELLED" in obs["journal_tail"] + [
        r.result for r in w.service.journal.records()
    ], obs


def g27() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    forged = replace(w.projection("reader", "OPS.READ"), capability="OPS.REQUEST")
    from epd2_control_plane_service.operations_console import ActionType

    def attempt(projection: Any, principal: str) -> Any:
        return w.service.request(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            projection=projection,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key=f"g27-{principal}-{w.tick().timestamp()}",
            purpose="x",
            now=w.now,
        )

    obs: dict[str, Any] = {
        "forged_projection": refusal(lambda: attempt(forged, "reader")),
        "mismatched_projection": refusal(
            lambda: attempt(w.projection("reader", "OPS.READ"), "reader")
        ),
        "decision_recorded": len(w.service.decisions_of("OPA-000001")) == 1
        and not w.service.decisions_of("OPA-000001")[0].allowed,
        "granted": w.request().state.value,
    }
    return obs["forged_projection"] == OpsRefusal.PROJECTION_UNTRUSTED.value and obs[
        "mismatched_projection"
    ] == OpsRefusal.PROJECTION_MISMATCH.value and obs["decision_recorded"] and obs[
        "granted"
    ] == "AWAITING_APPROVAL", obs


def g28() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal
    from epd2_control_plane_service.regional_operations import ApproverClass

    w = world()
    a = w.request()
    obs: dict[str, Any] = {
        "wrong_class": refusal(
            lambda: w.approve(a.action_id, "security-officer", ApproverClass.SECURITY)
        ),
        "self": refusal(
            lambda: w.approve(
                w.request(principal="dual-hat", idempotency_key="g28d").action_id, "dual-hat"
            )
        ),
        "approve_without_grant": refusal(
            lambda: w.projection(
                "executor", "OPS.APPROVE", approver=ApproverClass.INCIDENT_COMMANDER
            )
        ),
        "granted": w.approve(a.action_id).approval_state.value,
    }
    return obs["wrong_class"] == OpsRefusal.APPROVER_CLASS_MISSING.value and obs[
        "self"
    ] == OpsRefusal.SELF_APPROVAL.value and obs["approve_without_grant"] is not None and obs[
        "granted"
    ] == "GRANTED", obs


def g29() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import BERLIN
    from epd2_control_plane_service.operations_console import OpsRefusal
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    w = world()
    w.authorities.add(
        AuthorityGrant(
            "g-ic-exec", "incident-commander", ActorClass.HUMAN, "OPS.EXECUTE", BERLIN, 1
        )
    )
    a = w.request()
    w.approve(a.action_id)
    obs: dict[str, Any] = {
        "approver_executes": refusal(lambda: w.commit(a.action_id, principal="incident-commander")),
        "dispatches_after_refusal": w.adapter.dispatch_count,
        "distinct_executor": w.commit(a.action_id).state.value,
    }
    return obs["approver_executes"] == OpsRefusal.APPROVER_EXECUTES.value and obs[
        "dispatches_after_refusal"
    ] == 0 and obs["distinct_executor"] == "EXECUTING", obs


def g30() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OperationsPolicy

    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.authorities.update("g-req-r", suspended=True)
    strict = refusal(lambda: w.commit(a.action_id))
    weak = world(policy=OperationsPolicy.governed().without("commit_time_reauthorization"))
    b = weak.request()
    weak.approve(b.action_id)
    weak.authorities.update("g-req-r", suspended=True)
    weak_result = refusal(lambda: weak.commit(b.action_id))
    decisions = [d.stage for d in w.service.decisions_of(a.action_id)]
    obs: dict[str, Any] = {
        "governed_commit": strict,
        "without_obligation_commit": weak_result,
        "decision_stages": decisions,
    }
    return strict == "OPS_STALE_AUTHORITY" and weak_result is None and decisions[
        -1
    ] == "COMMIT", obs


def g31() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.authorities.update("g-req-r")
    version = refusal(lambda: w.commit(a.action_id))
    w2 = world()
    b = w2.request()
    w2.approve(b.action_id)
    w2.authorities.update("g-req-r", revoked=True)
    revoked = refusal(lambda: w2.commit(b.action_id))
    w3 = world()
    stale_projection = w3.projection("requester", "OPS.REQUEST")
    w3.authorities.update("g-req-r")
    from epd2_control_plane_service.operations_console import ActionType

    projection_stale = refusal(
        lambda: w3.service.request(
            actor_ref="requester",
            session_id="sess-requester",
            projection=stale_projection,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="g31",
            purpose="x",
            now=w3.tick(),
        )
    )
    obs: dict[str, Any] = {
        "version_changed": version,
        "revoked": revoked,
        "stale_projection_at_request": projection_stale,
    }
    return (
        version == OpsRefusal.STALE_AUTHORITY.value
        and revoked == OpsRefusal.STALE_AUTHORITY.value
        and projection_stale == OpsRefusal.STALE_AUTHORITY.value,
        obs,
    )


def g32() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.now = w.now + timedelta(minutes=31)
    expired = refusal(lambda: w.commit(a.action_id))
    w2 = world()
    b = w2.request()
    w2.approve(b.action_id)
    w2.authorities.update("g-ic", revoked=True)
    approver_revoked = refusal(lambda: w2.commit(b.action_id))
    w3 = world()
    c = w3.request()
    w3.approve(c.action_id)
    w3.service._actions[c.action_id] = replace(
        w3.service.action(c.action_id),
        parameters={"reason": "swapped"},
        parameters_digest=__import__(
            "epd2_control_plane_service.operations_console", fromlist=["parameters_digest"]
        ).parameters_digest({"reason": "swapped"}),
    )
    rebound = refusal(lambda: w3.commit(c.action_id))
    obs: dict[str, Any] = {
        "expired_approval": expired,
        "approver_authority_revoked": approver_revoked,
        "approval_bound_to_other_digest": rebound,
    }
    return (
        expired == OpsRefusal.STALE_APPROVAL.value
        and approver_revoked == OpsRefusal.STALE_APPROVAL.value
        and rebound == OpsRefusal.STALE_APPROVAL.value,
        obs,
    )


def g33() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    a = w.request()
    w.service.bump_target_version("svc-web")
    at_approval = refusal(lambda: w.approve(a.action_id))
    w2 = world()
    b = w2.request()
    w2.approve(b.action_id)
    w2.service.bump_target_version("svc-web")
    at_commit = refusal(lambda: w2.commit(b.action_id))
    obs: dict[str, Any] = {"at_approval": at_approval, "at_commit": at_commit}
    return (
        at_approval == OpsRefusal.STALE_TARGET.value and at_commit == OpsRefusal.STALE_TARGET.value,
        obs,
    )


def g34() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.service._actions[a.action_id] = replace(
        w.service.action(a.action_id), parameters={"reason": "tampered"}
    )
    obs: dict[str, Any] = {
        "tampered_parameters": refusal(lambda: w.commit(a.action_id)),
        "digest_in_evidence": w.service.evidence_record(a.action_id)["parameters_digest"]
        == a.parameters_digest,
    }
    return obs["tampered_parameters"] == OpsRefusal.STALE_PARAMETERS.value and obs[
        "digest_in_evidence"
    ], obs


def g35() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    w.service.revoke_session("sess-requester")
    revoked = refusal(lambda: w.request())
    w2 = world()
    w2.now = w2.now + timedelta(hours=9)
    expired = refusal(lambda: w2.request())
    w3 = world()
    a = w3.request()
    w3.approve(a.action_id)
    w3.service.revoke_session("sess-requester")
    requester_at_commit = refusal(lambda: w3.commit(a.action_id))
    w4 = world()
    b = w4.request()
    w4.approve(b.action_id)
    w4.service.revoke_session("sess-executor")
    executor_at_commit = refusal(lambda: w4.commit(b.action_id))
    w5 = world()
    w5.ctrl02.quarantined_sessions.add("sess-requester")
    quarantined = refusal(lambda: w5.request())
    obs: dict[str, Any] = {
        "revoked": revoked,
        "expired": expired,
        "requester_session_at_commit": requester_at_commit,
        "executor_session_at_commit": executor_at_commit,
        "ctrl02_quarantine": quarantined,
    }
    return (
        revoked == OpsRefusal.SESSION_REVOKED.value
        and expired == OpsRefusal.SESSION_EXPIRED.value
        and requester_at_commit == OpsRefusal.SESSION_REVOKED.value
        and executor_at_commit == OpsRefusal.SESSION_REVOKED.value
        and quarantined == OpsRefusal.CTRL02_RESTRICTED.value,
        obs,
    )


def g36() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import ARTIFACT_B
    from epd2_control_plane_service.operations_console import ActionType, OpsRefusal
    from epd2_control_plane_service.regional_operations import ApproverClass

    w = world()
    a = w.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "g36", "target_artifact_digest": ARTIFACT_B},
        principal="req-exec",
    )
    w.approve(a.action_id)
    one = refusal(lambda: w.commit(a.action_id))
    dup = refusal(lambda: w.approve(a.action_id))
    w.approve(a.action_id, "security-officer", ApproverClass.SECURITY)
    requester = refusal(lambda: w.commit(a.action_id, principal="req-exec"))
    done = w.commit(a.action_id)
    backup = w.completed_backup()
    w.active_window("db-members")
    r = w.request(
        ActionType.RESTORE_REQUEST,
        "db-members",
        parameters={
            "reason": "g36",
            "backup_set_id": "set-1",
            "backup_identity_digest": backup.backup_identity_digest,
            "confirmation": "CONFIRM-DESTRUCTIVE:db-members",
        },
    )
    for who, cls in (
        ("incident-commander", ApproverClass.INCIDENT_COMMANDER),
        ("security-officer", ApproverClass.SECURITY),
    ):
        w.approve(r.action_id, who, cls)
    two_of_three = refusal(lambda: w.commit(r.action_id))
    w.approve(r.action_id, "trust-custodian", ApproverClass.TRUST_CUSTODIAN)
    restore = w.commit(r.action_id)
    obs: dict[str, Any] = {
        "rollback_required": list(a.required_approver_classes),
        "one_approval_commit": one,
        "same_class_twice": dup,
        "requester_executes": requester,
        "rollback_dispatched": done.state.value,
        "restore_required": list(r.required_approver_classes),
        "two_of_three": two_of_three,
        "restore_dispatched": restore.state.value,
    }
    return (
        one == OpsRefusal.QUORUM_NOT_MET.value
        and dup == OpsRefusal.DUPLICATE_APPROVAL.value
        and requester == OpsRefusal.REQUESTER_EXECUTES.value
        and done.state.value == "EXECUTING"
        and two_of_three == OpsRefusal.QUORUM_NOT_MET.value
        and restore.state.value == "EXECUTING"
        and len(r.required_approver_classes) == 3,
        obs,
    )


def g37() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    a = w.request(idempotency_key="g37")
    b = w.request(idempotency_key="g37")
    conflict = refusal(lambda: w.request(idempotency_key="g37", parameters={"reason": "other"}))
    obs: dict[str, Any] = {
        "same_action": a.action_id == b.action_id,
        "actions": len(w.service.actions()),
        "conflict": conflict,
        "empty_key": refusal(lambda: w.request(idempotency_key="")),
    }
    return obs["same_action"] and obs[
        "actions"
    ] == 1 and conflict == OpsRefusal.IDEMPOTENCY_CONFLICT.value, obs


def g38() -> tuple[bool, dict[str, Any]]:
    w = world()
    a = w.request(idempotency_key="g38")
    w.approve(a.action_id)
    w.commit(a.action_id)
    replay_request = w.request(idempotency_key="g38")
    replay_commit = refusal(lambda: w.commit(a.action_id))
    ack = w.adapter.dispatch(w.adapter.dispatch_log[-1])
    obs: dict[str, Any] = {
        "request_replay_deduplicated": replay_request.action_id == a.action_id,
        "commit_replay": replay_commit,
        "adapter_replay_duplicate_flag": ack.duplicate,
        "dispatches": w.adapter.dispatch_count,
    }
    return (
        obs["request_replay_deduplicated"]
        and replay_commit == "OPS_DUPLICATE_EXECUTION"
        and ack.duplicate
        and w.adapter.dispatch_count == 1,
        obs,
    )


def g39() -> tuple[bool, dict[str, Any]]:
    w = world()
    a = w.request()
    w.approve(a.action_id)
    w.commit(a.action_id)
    first = refusal(lambda: w.commit(a.action_id))
    w.resolve(a.action_id)
    second = refusal(lambda: w.commit(a.action_id))
    obs: dict[str, Any] = {
        "while_executing": first,
        "after_terminal": second,
        "dispatches": w.adapter.dispatch_count,
    }
    return bool(first == second == "OPS_DUPLICATE_EXECUTION" and w.adapter.dispatch_count == 1), obs


def g40() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState

    w = world()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=3)
    a = w.request(idempotency_key="g40a")
    b = w.request(idempotency_key="g40b", principal="requester-2")
    w.approve(a.action_id)
    w.approve(b.action_id)
    w.commit(a.action_id)
    conflict = refusal(lambda: w.commit(b.action_id))
    for _ in range(4):
        w.resolve(a.action_id)
    after = w.commit(b.action_id).state.value
    obs: dict[str, Any] = {
        "conflict": conflict,
        "after_first_terminal": after,
        "dispatches": w.adapter.dispatch_count,
    }
    return (
        conflict == "OPS_CONFLICTING_EXECUTION"
        and after == "EXECUTING"
        and w.adapter.dispatch_count == 2,
        obs,
    )


def g41() -> tuple[bool, dict[str, Any]]:
    from _ctrl04_builders import ARTIFACT_B, ARTIFACT_UNATTESTED, ARTIFACT_UNVERIFIED
    from epd2_control_plane_service.operations_console import ActionType, OpsRefusal
    from epd2_control_plane_service.regional_operations import ApproverClass

    w = world()
    unverified = refusal(
        lambda: w.request(
            ActionType.DEPLOYMENT_ROLLBACK,
            parameters={"reason": "x", "target_artifact_digest": ARTIFACT_UNVERIFIED},
        )
    )
    unattested = refusal(
        lambda: w.request(
            ActionType.DEPLOYMENT_ROLLBACK,
            parameters={"reason": "x", "target_artifact_digest": ARTIFACT_UNATTESTED},
        )
    )
    a = w.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "x", "target_artifact_digest": ARTIFACT_B},
    )
    w.approve(a.action_id)
    w.approve(a.action_id, "security-officer", ApproverClass.SECURITY)
    w.ctrl03.retract(ARTIFACT_B)
    retracted = refusal(lambda: w.commit(a.action_id))
    w2 = world()
    b = w2.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "x", "target_artifact_digest": ARTIFACT_B},
    )
    w2.approve(b.action_id)
    w2.approve(b.action_id, "security-officer", ApproverClass.SECURITY)
    w2.commit(b.action_id)
    done = w2.resolve(b.action_id)
    sent = w2.adapter.dispatch_log[-1].parameters["target_artifact_digest"]
    unsupported = w2.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        "svc-api",
        parameters={"reason": "x", "target_artifact_digest": ARTIFACT_B},
    )
    w2.approve(unsupported.action_id)
    w2.approve(unsupported.action_id, "security-officer", ApproverClass.SECURITY)
    unsupported_state = w2.commit(unsupported.action_id).state.value
    obs: dict[str, Any] = {
        "unverified": unverified,
        "unattested": unattested,
        "trust_retracted_at_commit": retracted,
        "verified_result": done.state.value,
        "dispatched_digest_matches": sent == ARTIFACT_B,
        "unsupported_target": unsupported_state,
    }
    return (
        unverified == OpsRefusal.UNVERIFIED_ARTIFACT.value
        and unattested == OpsRefusal.UNVERIFIED_ARTIFACT.value
        and retracted == OpsRefusal.STALE_CTRL03_TRUST.value
        and done.state.value == "SUCCEEDED"
        and sent == ARTIFACT_B
        and unsupported_state == "UNSUPPORTED",
        obs,
    )


def g42() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import ActionType, OpsRefusal
    from epd2_control_plane_service.regional_operations import ApproverClass

    w = world()
    too_long = refusal(
        lambda: w.request(
            ActionType.MAINTENANCE_ENTER, parameters={"reason": "x", "duration_minutes": "481"}
        )
    )
    zero = refusal(
        lambda: w.request(
            ActionType.MAINTENANCE_ENTER, parameters={"reason": "x", "duration_minutes": "0"}
        )
    )
    backup = w.completed_backup()
    r = w.request(
        ActionType.RESTORE_REQUEST,
        "db-members",
        parameters={
            "reason": "x",
            "backup_set_id": "set-1",
            "backup_identity_digest": backup.backup_identity_digest,
            "confirmation": "CONFIRM-DESTRUCTIVE:db-members",
        },
    )
    for who, cls in (
        ("incident-commander", ApproverClass.INCIDENT_COMMANDER),
        ("security-officer", ApproverClass.SECURITY),
        ("trust-custodian", ApproverClass.TRUST_CUSTODIAN),
    ):
        w.approve(r.action_id, who, cls)
    no_window = refusal(lambda: w.commit(r.action_id))
    window_id = w.active_window("db-members", minutes=10)
    w.now = w.now + timedelta(minutes=11)
    w.service.expire_due(now=w.now)
    state = {x.window_id: x for x in w.service.maintenance_windows()}[window_id].state.value
    expired_window = refusal(lambda: w.commit(r.action_id))
    unknown_exit = refusal(
        lambda: w.request(
            ActionType.MAINTENANCE_EXIT,
            "svc-web",
            parameters={"reason": "x", "window_id": "MW-nope"},
        )
    )
    obs: dict[str, Any] = {
        "too_long": too_long,
        "zero": zero,
        "restore_without_window": no_window,
        "window_state_after_expiry": state,
        "restore_with_expired_window": expired_window,
        "exit_unknown_window": unknown_exit,
    }
    return (
        too_long == OpsRefusal.MAINTENANCE_WINDOW_INVALID.value
        and zero == OpsRefusal.MAINTENANCE_WINDOW_INVALID.value
        and no_window == OpsRefusal.MAINTENANCE_REQUIRED.value
        and state == "EXPIRED"
        and expired_window == OpsRefusal.MAINTENANCE_REQUIRED.value
        and unknown_exit == OpsRefusal.MAINTENANCE_WINDOW_INVALID.value,
        obs,
    )


def _evidence_world() -> tuple[Any, Any, dict[str, Any]]:
    w = world()
    done = w.full_restart()
    w.review(done.action_id)
    return w, done, w.service.evidence_record(done.action_id)


def g43() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import ActionType

    w = world()
    ids = [w.full_restart().action_id for _ in range(3)]
    link = w.request(
        ActionType.INCIDENT_LINK,
        "svc-web",
        parameters={"incident_id": "INC-1", "linked_action_id": ids[0]},
    )
    w.commit(link.action_id)
    pattern = re.compile(r"^OPA-\d{6}$")
    trails = {
        i: [r.result for r in w.service.journal.records() if r.correlation_ref == i]
        for i in [*ids, link.action_id]
    }
    refusal(
        lambda: w.request(
            principal="bavaria-requester", scope=__import__("_ctrl04_builders").BAVARIA
        )
    )
    refused_record = w.service.journal.records()[-1]
    obs: dict[str, Any] = {
        "ids": [*ids, link.action_id],
        "well_formed": all(pattern.match(i) for i in [*ids, link.action_id]),
        "unique": len(set(ids)) == 3,
        "trails": trails,
        "refusal_has_action_id": bool(pattern.match(refused_record.correlation_ref)),
    }
    return obs["well_formed"] and obs["unique"] and all(
        len(t) >= 2 for t in trails.values()
    ) and obs["refusal_has_action_id"], obs


def g44() -> tuple[bool, dict[str, Any]]:
    w, done, record = _evidence_world()
    journal = [r for r in w.service.journal.records() if r.correlation_ref == done.action_id]
    obs: dict[str, Any] = {
        "actor_ref": record["actor_ref"],
        "authority_ref": record["authority_ref"],
        "decisions": [
            (d["stage"], d["actor_ref"], d["authority_ref"])
            for d in record["authorization_decision"]
        ],
        "journal_actors": [(r.actor_ref, r.authority_basis) for r in journal],
    }
    return record["actor_ref"] == "requester" and record["authority_ref"] == "g-req-r@v1" and obs[
        "decisions"
    ] == [
        ("REQUEST", "requester", "g-req-r"),
        ("APPROVE", "incident-commander", "g-ic"),
        ("COMMIT", "executor", "g-exec"),
        ("REVIEW", "reviewer", "g-rev"),
    ] and ("executor", "g-exec@v1") in obs["journal_actors"], obs


def g45() -> tuple[bool, dict[str, Any]]:
    w, done, record = _evidence_world()
    journal = [r for r in w.service.journal.records() if r.correlation_ref == done.action_id]
    obs: dict[str, Any] = {
        "target_ref": record["target_ref"],
        "deployment_identity_ref": record["deployment_identity_ref"],
        "journal_object_refs": sorted({r.object_ref for r in journal}),
        "journal_deployment_attr": journal[0].attributes.get("deployment_identity_ref"),
    }
    return record["target_ref"] == "svc-web@v1" and record[
        "deployment_identity_ref"
    ] == "dep-web-1" and obs["journal_object_refs"] == ["svc-web"] and obs[
        "journal_deployment_attr"
    ] == "dep-web-1", obs


def g46() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_console import parameters_digest

    w, done, record = _evidence_world()
    journal = [r for r in w.service.journal.records() if r.correlation_ref == done.action_id]
    expected = parameters_digest({"reason": "test"})
    obs: dict[str, Any] = {
        "record_digest": record["parameters_digest"],
        "expected": expected,
        "journal_digests": [
            r.attributes.get("parameters_digest")
            for r in journal
            if "parameters_digest" in r.attributes
        ],
    }
    return record["parameters_digest"] == expected and obs["journal_digests"] and all(
        d == expected for d in obs["journal_digests"]
    ), obs


def g47() -> tuple[bool, dict[str, Any]]:
    w, done, record = _evidence_world()
    journal = [r for r in w.service.journal.records() if r.correlation_ref == done.action_id]
    approvals = record["approval_ref"]
    obs: dict[str, Any] = {
        "approval_records": approvals,
        "journal_approval_refs": [list(r.approval_refs) for r in journal],
    }
    return len(approvals) == 1 and approvals[0][
        "approver_ref"
    ] == "incident-commander" and approvals[0]["authority_ref"] == "g-ic@v1" and approvals[0][
        "approver_class"
    ] == "INCIDENT_COMMANDER" and any(
        r.approval_refs == (approvals[0]["approval_id"],) for r in journal
    ), obs


def g48() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import BackendState

    w, _done, record = _evidence_world()
    w.adapter.inject_outcome("svc-web", BackendState.FAILED)
    failed = w.full_restart()
    failed_record = w.service.evidence_record(failed.action_id)
    journal = [r for r in w.service.journal.records() if r.correlation_ref == failed.action_id]
    obs: dict[str, Any] = {
        "success": [
            record["execution_state"],
            record["result_state"],
            record["backend_operation_ref"] is not None,
            record["evidence_digest"][:16],
        ],
        "failure": [
            failed_record["execution_state"],
            failed_record["result_state"],
            failed_record["failure_classification"],
        ],
        "failure_journal": [r.result for r in journal],
    }
    return obs["success"][:3] == ["COMPLETED", "SUCCEEDED", True] and obs["failure"] == [
        "FAILED",
        "FAILED",
        "PROVIDER_FAILURE",
    ] and obs["failure_journal"][-1] == "FAILED", obs


def g49() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.audit import SECRET_FIELD_MARKERS

    w, _done, record = _evidence_world()
    schema = (
        json.loads((ROOT / "docs/ctrl/CTRL-04/CTRL04_EVIDENCE_SCHEMA.json").read_text())
        if (ROOT / "docs/ctrl/CTRL-04/CTRL04_EVIDENCE_SCHEMA.json").is_file()
        else {}
    )
    forbidden = set(schema.get("forbidden_fields_examples", [])) | {
        "password",
        "private_key",
        "secret_value",
        "access_token",
        "refresh_token",
        "recovery_secret",
        "seed_phrase",
        "raw_hsm_material",
    }
    text = json.dumps(record) + json.dumps([r.hashable() for r in w.service.journal.records()])
    keys_present = sorted(k for k in forbidden if f'"{k}"' in text)
    values_present = [m for m in ("sk_live_", "hunter2") if m in text]
    obs: dict[str, Any] = {
        "forbidden_keys_present": keys_present,
        "secret_values_present": values_present,
        "journal_markers": list(SECRET_FIELD_MARKERS),
        "required_present": [k for k in schema.get("required", []) if k in record],
    }
    return not keys_present and not values_present and (
        not schema or len(obs["required_present"]) == len(schema["required"])
    ), obs


def g50() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_adapters import JsonFileStore
    from epd2_control_plane_service.operations_console import OperationsConsoleService

    with tempfile.TemporaryDirectory() as td:
        store = JsonFileStore(Path(td) / "ctrl04.json")
        w = world(store=store)
        done = w.full_restart()
        before = w.service.evidence_record(done.action_id)
        head = w.service.journal.head_hash()
        loaded = store.load()
        assert loaded is not None
        revived = OperationsConsoleService.from_checkpoint(
            loaded,
            authorities=w.authorities,
            signer=w.signer,
            adapters={"reference-adapter": w.adapter},
            ctrl02=w.ctrl02,
            ctrl03=w.ctrl03,
            store=store,
        )
        after = revived.evidence_record(done.action_id)
        revived.journal.verify()
        e2e = load("e2e_journeys_result.json")
        j19: dict[str, Any] = next(
            (j for j in e2e.get("journeys", []) if j["journey"] == "J19"), {}
        )
    obs: dict[str, Any] = {
        "same_record": before == after,
        "same_head": revived.journal.head_hash() == head,
        "records": len(revived.journal),
        "e2e_J19": j19.get("status"),
        "e2e_bound_to_runtime_digest": e2e.get("runtime_source_digest") == runtime_source_digest(),
    }
    return bool(
        obs["same_record"]
        and obs["same_head"]
        and j19.get("status") == "PASS"
        and obs["e2e_bound_to_runtime_digest"]
    ), obs


def g51() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.operations_api import ConsoleApp
    from epd2_control_plane_service.operations_console import OpsRefusal

    w = world()
    app = ConsoleApp(w.service, clock=lambda: w.tick())

    def call(
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        session: str | None = "sess-requester",
    ) -> tuple[int, Any]:
        headers = {} if session is None else {"X-EPD2-Session": session}
        status, payload, _ = app.handle(
            method, path, headers, json.dumps(body).encode() if body is not None else b""
        )
        return status, payload

    checks: dict[str, Any] = {
        "no_session": call("GET", "/ops/v1/targets", session=None)[0] == 401,
        "shell_surface": call("POST", "/ops/v1/shell", {"command": "id"})[1].get("error")
        == "OPS_DIRECT_EXECUTION_SURFACE_ABSENT",
        "sql_surface": call("POST", "/ops/v1/sql", {"query": "select 1"})[1].get("error")
        == "OPS_DIRECT_EXECUTION_SURFACE_ABSENT",
        "client_approval_state": call(
            "POST",
            "/ops/v1/actions",
            {
                "action_type": "OPS.SERVICE.RESTART",
                "target_id": "svc-web",
                "parameters": {"reason": "x"},
                "idempotency_key": "k",
                "approval_state": "GRANTED",
            },
        )[1].get("error")
        == "OPS_BROWSER_STATE_NOT_AUTHORITATIVE",
        "client_result_state": call(
            "POST", "/ops/v1/actions/OPA-000001/resolve", {"result_state": "SUCCEEDED"}
        )[1].get("error")
        == "OPS_BROWSER_STATE_NOT_AUTHORITATIVE",
        "reader_cannot_request": call(
            "POST",
            "/ops/v1/actions",
            {
                "action_type": "OPS.SERVICE.RESTART",
                "target_id": "svc-web",
                "parameters": {"reason": "x"},
                "idempotency_key": "k",
            },
            session="sess-reader",
        )[0]
        == 403,
        "read_only_cannot_request": call(
            "POST",
            "/ops/v1/actions",
            {
                "action_type": "OPS.SERVICE.RESTART",
                "target_id": "svc-web",
                "parameters": {"reason": "x"},
                "idempotency_key": "k",
            },
            session="sess-readonly-operator",
        )[1].get("error")
        == "OPS_READ_ONLY_SESSION",
        "voting_target": call(
            "GET", "/ops/v1/status?target_id=svc-voting-tally", session="sess-reader"
        )[1].get("error")
        == "OPS_VOTING_BOUNDARY",
        "wrong_scope_read": call(
            "GET", "/ops/v1/status?target_id=svc-web", session="sess-bavaria-requester"
        )[0]
        == 403,
        "unknown_action": call(
            "POST",
            "/ops/v1/actions",
            {"action_type": "OPS.NUKE", "target_id": "svc-web", "idempotency_key": "k"},
        )[0]
        == 400,
        "missing_idempotency": call(
            "POST",
            "/ops/v1/actions",
            {
                "action_type": "OPS.SERVICE.RESTART",
                "target_id": "svc-web",
                "parameters": {"reason": "x"},
            },
        )[0]
        == 400,
        "unknown_evidence": call("GET", "/ops/v1/evidence/OPA-999999", session="sess-reader")[0]
        == 404,
        "malformed_json": app.handle(
            "POST", "/ops/v1/actions", {"X-EPD2-Session": "sess-requester"}, b"{oops"
        )[0]
        == 400,
    }
    browser = load("browser_journeys_result.json")
    checks["browser_journeys_executed_pass"] = (
        browser.get("status") == "PASS" and browser.get("journeys_passed") == 4
    )
    checks["browser_bound_to_runtime_digest"] = (
        browser.get("runtime_source_digest") == runtime_source_digest()
    )
    w.service.revoke_session("sess-reader")
    checks["revoked_session_refused_on_list_route"] = (
        call("GET", "/ops/v1/targets", session="sess-reader")[1].get("error")
        == OpsRefusal.SESSION_REVOKED.value
    )
    obs: dict[str, Any] = {
        **checks,
        "browser": {k: browser.get(k) for k in ("status", "journeys_passed", "browser")},
    }
    return all(checks.values()), obs


def source_files() -> list[Path]:
    """Governed source scope of the freeze: runtime, tests, scripts, docs and
    contracts. Validation outputs are deliberately outside the freeze because
    they are regenerated by every run; the sealed archive binds them by
    SHA256SUMS instead."""
    paths: list[Path] = []
    bases = (
        SERVICE / "src/epd2_control_plane_service",
        SERVICE / "tests",
        ROOT / "scripts",
        ROOT / "docs/ctrl/CTRL-04",
        ROOT / "contracts/control",
    )
    for base in bases:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if (
                base.name in {"epd2_control_plane_service", "CTRL-04"}
                or "ctrl04" in path.name.lower()
            ):
                paths.append(path)
    return sorted(set(paths))


def manifest() -> dict[str, str]:
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in source_files()}


def g52(record_freeze: bool, runs: dict[str, dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    mutation = load("mutation_result.json")
    e2e = load("e2e_journeys_result.json")
    current = manifest()
    path = VALIDATION / "freeze_manifest.json"
    if record_freeze:
        payload = {
            "schema": "epd2.ctrl04.freeze-manifest/1",
            "mode": MODE,
            "files": current,
            "scope_digest": hashlib.sha256(
                json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        write("freeze_manifest.json", payload)
        frozen = True
        drift: list[str] = []
    else:
        recorded = json.loads(path.read_text()).get("files", {}) if path.is_file() else {}
        drift = sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))
        frozen = path.is_file() and not drift
    obs: dict[str, Any] = {
        "tests_passed": runs["tests"]["passed"],
        "tests_summary": runs["tests"]["summary"],
        "ruff_passed": runs["ruff"]["passed"],
        "ruff_format_passed": runs["ruff_format"]["passed"],
        "mypy_passed": runs["mypy"]["passed"],
        "mutation": f"{mutation.get('detected', 0)}/48 DETECTED",
        "mutation_undetected": mutation.get("undetected"),
        "e2e": f"{e2e.get('journeys_passed', 0)}/20 PASS",
        "e2e_integration_class": e2e.get("integration_class"),
        "freeze_files": len(current),
        "freeze_verified": frozen,
        "freeze_drift": drift[:20],
        "self_acceptance": False,
        "package_identity": (
            "EXTERNAL: produced and verified by scripts/build_ctrl04_candidate.py / "
            "verify_ctrl04_package.py on sealed bytes"
        ),
    }
    ok = (
        runs["tests"]["passed"]
        and runs["ruff"]["passed"]
        and runs["ruff_format"]["passed"]
        and runs["mypy"]["passed"]
        and mutation.get("detected") == 48
        and not mutation.get("undetected")
        and e2e.get("journeys_passed") == 20
        and frozen
    )
    return ok, obs


def run(command: list[str], env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    lines = completed.stdout.strip().splitlines()
    return {
        "command": command,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "summary": lines[-1] if lines else "",
        "output_tail": lines[-15:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-freeze", action="store_true")
    args = parser.parse_args()
    VALIDATION.mkdir(parents=True, exist_ok=True)
    python = str(ROOT / ".venv/bin/python")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(SERVICE / "src"), env.get("PYTHONPATH", "")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    targets = [
        "services/control-plane-service/src/epd2_control_plane_service/operations_console.py",
        "services/control-plane-service/src/epd2_control_plane_service/operations_adapters.py",
        "services/control-plane-service/src/epd2_control_plane_service/operations_api.py",
        *[str(p.relative_to(ROOT)) for p in sorted((SERVICE / "tests").glob("*ctrl04*.py"))],
        *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "scripts").glob("*ctrl04*.py"))],
    ]
    runs = {
        "tests": run(
            [
                python,
                "-m",
                "pytest",
                "services/control-plane-service/tests",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            env,
        ),
        "ruff": run([str(ROOT / ".venv/bin/ruff"), "check", *targets], env),
        "ruff_format": run([str(ROOT / ".venv/bin/ruff"), "format", "--check", *targets], env),
        "mypy": run([str(ROOT / ".venv/bin/mypy"), *targets[:3]], env),
    }
    forbidden = (
        "-----BEGIN " + "PRIVATE KEY-----",
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "AKIA" + "IOSFODNN7EXAMPLE",
    )
    secret_hits = [
        p.relative_to(ROOT).as_posix()
        for p in source_files()
        if p.suffix != ".png" and any(m in p.read_text(errors="ignore") for m in forbidden)
    ]
    write(
        "test_result.json",
        {
            "schema": "epd2.ctrl04.test-result/1",
            **runs,
            "secret_scan": {"passed": not secret_hits, "hits": secret_hits},
        },
    )

    probes: list[Probe] = [
        g01,
        g02,
        g03,
        g04,
        g05,
        g06,
        g07,
        g08,
        g09,
        g10,
        g11,
        g12,
        g13,
        g14,
        g15,
        g16,
        g17,
        g18,
        g19,
        g20,
        g21,
        g22,
        g23,
        g24,
        g25,
        g26,
        g27,
        g28,
        g29,
        g30,
        g31,
        g32,
        g33,
        g34,
        g35,
        g36,
        g37,
        g38,
        g39,
        g40,
        g41,
        g42,
        g43,
        g44,
        g45,
        g46,
        g47,
        g48,
        g49,
        g50,
        g51,
    ]
    results = []
    for index, probe in enumerate(probes, 1):
        gate_id = f"G{index:02d}"
        try:
            passed, obs = probe()
        except Exception as exc:
            passed, obs = False, {"exception": f"{type(exc).__name__}: {exc}"}
        results.append(
            {
                "id": gate_id,
                "name": GATE_NAMES[index - 1],
                "status": "PASS" if passed else "FAIL",
                "executed": True,
                "observations": obs,
            }
        )
        print(f"{gate_id} {'PASS' if passed else 'FAIL'} {GATE_NAMES[index - 1]}", flush=True)
    write("gate_results.json", {"schema": "epd2.ctrl04.gate-results/1", "gates": results})
    passed52, obs52 = g52(args.record_freeze, runs)
    if secret_hits:
        passed52 = False
        obs52["secret_scan_hits"] = secret_hits
    results.append(
        {
            "id": "G52",
            "name": GATE_NAMES[51],
            "status": "PASS" if passed52 else "FAIL",
            "executed": True,
            "observations": obs52,
        }
    )
    print(f"G52 {'PASS' if passed52 else 'FAIL'} {GATE_NAMES[51]}", flush=True)
    write("gate_results.json", {"schema": "epd2.ctrl04.gate-results/1", "gates": results})
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed = [r["id"] for r in results if r["status"] != "PASS"]
    mutation = load("mutation_result.json")
    result = {
        "schema": "epd2.ctrl04.preseal-result/1",
        "stage": "CTRL-04",
        "mode": MODE,
        "overall": "PASS" if not failed else "FAIL",
        "gates_total": 52,
        "gates_passed": passed_count,
        "gates_failed": failed,
        "gates_blocked_for_final_seal": [],
        "mutation_result": f"{mutation.get('detected', 0)}/48 DETECTED",
        "e2e_result": f"{load('e2e_journeys_result.json').get('journeys_passed', 0)}/20 PASS",
        "browser_result": load("browser_journeys_result.json").get("status"),
        "tests": runs["tests"]["summary"],
        "self_state": SELF_STATE,
        "self_acceptance": False,
        "gates": [{k: v for k, v in r.items() if k != "observations"} for r in results],
    }
    write("ctrl04_preseal_result.json", result)
    write(
        "package_identity_result.json",
        {
            "schema": "epd2.ctrl04.package-identity/1",
            "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED",
            "freeze_verified": obs52.get("freeze_verified"),
            "archive_sha256": None,
            "archive_size": None,
            "self_state": SELF_STATE,
        },
    )
    terminal = "PASS" if not failed else "FAIL"
    print(f"CTRL04_RESULT:{terminal}:{passed_count}/52_PASS")
    return 0 if terminal == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
