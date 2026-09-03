#!/usr/bin/env python3
"""CTRL-04 end-to-end journeys J01-J20 over the real HTTP API.

The journeys drive the Operations Console through its HTTP transport against:

* `LocalProcessAdapter` — restarts a real operating-system process;
* `LocalFilesystemBackupAdapter` — writes and restores real archives;
* `ReferenceOperationsAdapter` — for degraded/unavailable/rollback/queue paths
  that need deterministic injection;
* `JsonFileStore` — real persisted evidence that survives a console restart.

The accepted OPS/INFRA provider runtimes are not installed on canonical `main`
(only their acceptance records are), so this evidence is explicitly classed
as REFERENCE_AND_LOCAL_REAL_ADAPTERS. It is not a claim of provider
integration and is recorded as such in the result file.
"""

from __future__ import annotations

import json
import secrets
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/control-plane-service/src"))
sys.path.insert(0, str(ROOT / "scripts"))

from epd2_control_plane_service.credential_lifecycle import Ctrl02State  # noqa: E402
from epd2_control_plane_service.operations_adapters import (  # noqa: E402
    AdapterCapability,
    JsonFileStore,
    LocalFilesystemBackupAdapter,
    LocalProcessAdapter,
    ReferenceOperationsAdapter,
)
from epd2_control_plane_service.operations_api import ConsoleApp, serve  # noqa: E402
from epd2_control_plane_service.operations_console import (  # noqa: E402
    AuthorityProjectionSigner,
    ConsoleSession,
    Ctrl03TrustState,
    DeploymentIdentity,
    EnvironmentClass,
    EvidenceSealer,
    OperationalIncidentRef,
    OperationalTarget,
    OperationsConsoleService,
    SessionState,
    TargetClass,
    TargetDomain,
)
from epd2_control_plane_service.regional_operations import (  # noqa: E402
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)

from ctrl04_common import runtime_source_digest  # type: ignore[import-not-found]  # noqa: E402

VALIDATION = ROOT / "validation/ctrl04"
BERLIN = ExactScope("DE-BE", "org-berlin")
ART_A = "a" * 64
ART_B = "b" * 64
ART_X = "c" * 64


class Clock:
    def __init__(self) -> None:
        self.offset = timedelta(0)
        self._last = datetime.now(UTC)

    def now(self) -> datetime:
        # Monotonic within the run, plus an explicit offset for time-travel journeys.
        current = datetime.now(UTC) + self.offset
        if current <= self._last:
            current = self._last + timedelta(microseconds=1)
        self._last = current
        return current


class Http:
    def __init__(self, base: str) -> None:
        self.base = base

    def call(
        self, method: str, path: str, body: dict[str, Any] | None = None, session: str | None = None
    ) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if session:
            headers["X-EPD2-Session"] = session
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            try:
                return exc.code, json.loads(payload or b"{}")
            except json.JSONDecodeError:
                return exc.code, {"raw": payload.decode(errors="replace")}


GRANTS = (
    ("g-reader", "reader", "OPS.READ", None),
    ("g-req", "requester", "OPS.READ", None),
    ("g-req-r", "requester", "OPS.REQUEST", None),
    ("g-ic", "incident-commander", "OPS.APPROVE", ApproverClass.INCIDENT_COMMANDER),
    ("g-ic-read", "incident-commander", "OPS.READ", None),
    ("g-sec", "security-officer", "OPS.APPROVE", ApproverClass.SECURITY),
    ("g-trust", "trust-custodian", "OPS.APPROVE", ApproverClass.TRUST_CUSTODIAN),
    ("g-exec", "executor", "OPS.EXECUTE", None),
    ("g-exec-read", "executor", "OPS.READ", None),
    ("g-rev", "reviewer", "OPS.REVIEW", None),
    ("g-rev-read", "reviewer", "OPS.READ", None),
    ("g-ro", "readonly-operator", "OPS.READ", None),
    ("g-ro-req", "readonly-operator", "OPS.REQUEST", None),
)


def build_world(
    tmp: Path,
) -> tuple[OperationsConsoleService, dict[str, Any], JsonFileStore, AuthorityDirectory]:
    authorities = AuthorityDirectory(
        AuthorityGrant(gid, actor, ActorClass.HUMAN, cap, BERLIN, 1, approver_class=cls)
        for gid, actor, cap, cls in GRANTS
    )
    signer = AuthorityProjectionSigner(secrets.token_bytes(32))
    process = LocalProcessAdapter("local-process")
    process.manage("svc-web-real")
    process.manage("svc-fixed-real", restart_supported=False)
    data = tmp / "datastore"
    data.mkdir()
    (data / "members.csv").write_text("id,name\n1,alpha\n2,beta\n")
    backup = LocalFilesystemBackupAdapter(tmp / "backups", "local-backup")
    backup.manage("db-members-real", data)
    reference = ReferenceOperationsAdapter("reference-adapter")
    for target_id, caps, health in (
        (
            "svc-ref",
            frozenset(
                {
                    AdapterCapability.RESTART,
                    AdapterCapability.ROLLBACK,
                    AdapterCapability.MAINTENANCE,
                }
            ),
            "HEALTHY",
        ),
        ("int-payment", frozenset(), "DEGRADED"),
        ("svc-legacy", frozenset({AdapterCapability.MAINTENANCE}), "UNAVAILABLE"),
        ("svc-voting-tally", frozenset(AdapterCapability), "HEALTHY"),
    ):
        reference.configure_target(
            target_id,
            capabilities=caps,
            health=health,
            metadata={
                "provider_region": "eu-central",
                "api_token": "sk_live_e2e_secret",
                "secret_ref": "vault://ops",
            },
        )
    ctrl03 = Ctrl03TrustState()
    ctrl03.attest(ART_A)
    ctrl03.attest(ART_B)
    store = JsonFileStore(tmp / "state" / "ctrl04.json")
    sealer = EvidenceSealer(secrets.token_bytes(32))
    service = OperationsConsoleService(
        authorities=authorities,
        signer=signer,
        adapters={"local-process": process, "local-backup": backup, "reference-adapter": reference},
        ctrl02=Ctrl02State(),
        ctrl03=ctrl03,
        store=store,
        sealer=sealer,
    )
    for dep, digest, rel, chg, verified in (
        ("dep-web-1", ART_A, "rel-1.4.0", "chg-101", True),
        ("dep-web-0", ART_B, "rel-1.3.9", "chg-099", True),
        ("dep-web-x", ART_X, "rel-1.5.0-rc", "chg-102", False),
        ("dep-db-1", "d" * 64, "rel-db-2", "chg-050", True),
    ):
        service.register_deployment(
            DeploymentIdentity(dep, digest, f"oci://epd2@sha256:{digest}", rel, chg, 1, verified)
        )
    targets = (
        ("svc-web-real", TargetClass.SERVICE, TargetDomain.GENERAL, "dep-web-1", "local-process"),
        ("svc-fixed-real", TargetClass.SERVICE, TargetDomain.GENERAL, "dep-web-1", "local-process"),
        (
            "db-members-real",
            TargetClass.DATASTORE,
            TargetDomain.GENERAL,
            "dep-db-1",
            "local-backup",
        ),
        ("svc-ref", TargetClass.SERVICE, TargetDomain.GENERAL, "dep-web-1", "reference-adapter"),
        (
            "int-payment",
            TargetClass.INTEGRATION,
            TargetDomain.GENERAL,
            "dep-web-1",
            "reference-adapter",
        ),
        ("svc-legacy", TargetClass.SERVICE, TargetDomain.GENERAL, "dep-web-0", "reference-adapter"),
        (
            "svc-voting-tally",
            TargetClass.SERVICE,
            TargetDomain.VOTING,
            "dep-web-1",
            "reference-adapter",
        ),
    )
    adapters: dict[str, Any] = {
        "local-process": process,
        "local-backup": backup,
        "reference-adapter": reference,
    }
    for target_id, klass, domain, dep, adapter_id in targets:
        service.register_target(
            OperationalTarget(
                target_id=target_id,
                target_class=klass,
                domain=domain,
                environment=EnvironmentClass.PRODUCTION_LIKE,
                scope=BERLIN,
                deployment_identity_ref=dep,
                adapter_id=adapter_id,
                version=1,
                capabilities=adapters[adapter_id].capabilities(target_id),
                display_name=target_id,
            )
        )
    service.register_incident(OperationalIncidentRef("INC-E2E-1", "svc-web-real", "SEV2", "OPEN"))
    now = datetime.now(UTC)
    for principal in {g[1] for g in GRANTS}:
        service.open_session(
            ConsoleSession(
                session_id=f"sess-{principal}",
                principal_id=principal,
                state=SessionState.ACTIVE,
                established_at=now,
                expires_at=now + timedelta(hours=8),
                read_only=principal == "readonly-operator",
            )
        )
    return service, adapters, store, authorities


class Runner:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(self, journey: str, title: str, ok: bool, observations: dict[str, Any]) -> None:
        self.results.append(
            {
                "journey": journey,
                "title": title,
                "status": "PASS" if ok else "FAIL",
                "observations": observations,
            }
        )
        print(f"{journey} {'PASS' if ok else 'FAIL'} {title}", flush=True)


def request_action(
    http: Http, session: str, action_type: str, target: str, params: dict[str, str], key: str
) -> tuple[int, Any]:
    return http.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": action_type,
            "target_id": target,
            "parameters": params,
            "idempotency_key": key,
            "purpose": key,
        },
        session,
    )


def approve_all(http: Http, action: dict[str, Any]) -> list[int]:
    sessions = {
        "INCIDENT_COMMANDER": "sess-incident-commander",
        "SECURITY": "sess-security-officer",
        "TRUST_CUSTODIAN": "sess-trust-custodian",
    }
    codes = []
    for cls in action["required_approver_classes"]:
        status, _ = http.call(
            "POST",
            f"/ops/v1/actions/{action['action_id']}/approve",
            {"approver_class": cls},
            sessions[cls],
        )
        codes.append(status)
    return codes


def finish(http: Http, action_id: str, session: str = "sess-executor") -> dict[str, Any]:
    status, payload = http.call("POST", f"/ops/v1/actions/{action_id}/commit", {}, session)
    if status != 200:
        return {"commit_status": status, **payload}
    for _ in range(20):
        status, payload = http.call(
            "POST", f"/ops/v1/actions/{action_id}/resolve", {}, "sess-reader"
        )
        if payload["state"] != "EXECUTING":
            break
        time.sleep(0.05)
    payload["commit_status"] = 200
    final: dict[str, Any] = payload
    return final


def main() -> int:
    runner = Runner()
    clock = Clock()
    with tempfile.TemporaryDirectory(prefix="ctrl04-e2e-") as td:
        tmp = Path(td)
        service, adapters, store, authorities = build_world(tmp)
        process: LocalProcessAdapter = adapters["local-process"]
        backup: LocalFilesystemBackupAdapter = adapters["local-backup"]
        reference: ReferenceOperationsAdapter = adapters["reference-adapter"]
        app = ConsoleApp(service, clock=clock.now)
        server = serve(app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        http = Http(f"http://127.0.0.1:{server.server_address[1]}")
        try:
            # J01
            status, payload = http.call(
                "GET", "/ops/v1/status?target_id=svc-web-real", session="sess-reader"
            )
            ok = (
                status == 200
                and payload["health"]["state"] == "HEALTHY"
                and payload["deployment_identity"]["artifact_digest"] == ART_A
            )
            runner.record(
                "J01",
                "read environment/deployment status",
                ok,
                {
                    "status": status,
                    "health": payload.get("health", {}).get("state"),
                    "release": payload.get("deployment_identity", {}).get("release_ref"),
                    "pid": payload.get("health", {}).get("details", {}).get("pid"),
                },
            )
            # J02
            s1, p1 = http.call(
                "GET", "/ops/v1/integrations?target_id=int-payment", session="sess-reader"
            )
            s2, p2 = http.call("GET", "/ops/v1/health?target_id=svc-legacy", session="sess-reader")
            ok = (
                s1 == 200
                and p1["health"]["state"] == "DEGRADED"
                and s2 == 200
                and p2["health"]["state"] == "UNAVAILABLE"
            )
            runner.record(
                "J02",
                "read degraded/unavailable service state",
                ok,
                {
                    "int-payment": p1.get("health", {}).get("state"),
                    "svc-legacy": p2.get("health", {}).get("state"),
                },
            )
            # J03
            pid_before = process.pid_of("svc-web-real")
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-web-real",
                {"reason": "J03"},
                "j03",
            )
            approvals = approve_all(http, action)
            done = finish(http, action["action_id"])
            pid_after = process.pid_of("svc-web-real")
            ok = (
                status == 202
                and approvals == [200]
                and done["state"] == "SUCCEEDED"
                and done["result"]["state"] == "SUCCEEDED"
                and pid_before != pid_after
            )
            runner.record(
                "J03",
                "request safe restart and observe terminal result",
                ok,
                {
                    "action_id": action.get("action_id"),
                    "state": done.get("state"),
                    "execution_state": done.get("execution_state"),
                    "pid_before": pid_before,
                    "pid_after": pid_after,
                },
            )
            j03_action = action["action_id"]
            # J04
            status, payload = request_action(
                http, "sess-reader", "OPS.SERVICE.RESTART", "svc-web-real", {"reason": "J04"}, "j04"
            )
            runner.record(
                "J04",
                "forbidden restart by insufficient authority",
                status == 403 and payload.get("error") == "OPS_WRONG_SCOPE",
                {"status": status, "error": payload.get("error")},
            )
            # J05
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-web-real",
                {"reason": "J05"},
                "j05",
            )
            approve_all(http, action)
            authorities.update("g-req-r", revoked=True)
            done = finish(http, action["action_id"])
            authorities.update("g-req-r", revoked=False)
            ok = done.get("commit_status") == 403 and done.get("error") == "OPS_STALE_AUTHORITY"
            runner.record(
                "J05",
                "stale authority between request and execution refused",
                ok,
                {"commit_status": done.get("commit_status"), "error": done.get("error")},
            )
            # J06
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.DEPLOYMENT.ROLLBACK",
                "svc-ref",
                {"reason": "J06", "target_artifact_digest": ART_B},
                "j06",
            )
            _s_ic, _ = http.call(
                "POST",
                f"/ops/v1/actions/{action['action_id']}/approve",
                {"approver_class": "INCIDENT_COMMANDER"},
                "sess-incident-commander",
            )
            early = http.call(
                "POST", f"/ops/v1/actions/{action['action_id']}/commit", {}, "sess-executor"
            )
            _s_sec, _ = http.call(
                "POST",
                f"/ops/v1/actions/{action['action_id']}/approve",
                {"approver_class": "SECURITY"},
                "sess-security-officer",
            )
            done = finish(http, action["action_id"])
            ok = (
                action.get("required_approver_classes") == ["INCIDENT_COMMANDER", "SECURITY"]
                and early[0] == 403
                and early[1].get("error") == "OPS_QUORUM_NOT_MET"
                and done["state"] == "SUCCEEDED"
            )
            runner.record(
                "J06",
                "high-impact operation requires approval/dual control",
                ok,
                {
                    "required": action.get("required_approver_classes"),
                    "single_approval_commit": early[1].get("error"),
                    "final": done.get("state"),
                },
            )
            # J07
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-web-real",
                {"reason": "J07"},
                "j07",
            )
            approve_all(http, action)
            clock.offset += timedelta(minutes=31)
            done = finish(http, action["action_id"])
            ok = done.get("commit_status") == 403 and done.get("error") == "OPS_STALE_APPROVAL"
            runner.record(
                "J07",
                "approval expires before execution refused",
                ok,
                {"commit_status": done.get("commit_status"), "error": done.get("error")},
            )
            # J08
            before = reference.dispatch_count
            s_a, a1 = request_action(
                http, "sess-requester", "OPS.SERVICE.RESTART", "svc-ref", {"reason": "J08"}, "j08"
            )
            _s_b, a2 = request_action(
                http, "sess-requester", "OPS.SERVICE.RESTART", "svc-ref", {"reason": "J08"}, "j08"
            )
            approve_all(http, a1)
            done = finish(http, a1["action_id"])
            dup = http.call(
                "POST", f"/ops/v1/actions/{a1['action_id']}/commit", {}, "sess-executor"
            )
            conflict = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-ref",
                {"reason": "different"},
                "j08",
            )
            ok = (
                a1["action_id"] == a2["action_id"]
                and done["state"] == "SUCCEEDED"
                and dup[0] == 403
                and dup[1].get("error") == "OPS_DUPLICATE_EXECUTION"
                and reference.dispatch_count == before + 1
                and conflict[0] == 403
                and conflict[1].get("error") == "OPS_IDEMPOTENCY_CONFLICT"
            )
            runner.record(
                "J08",
                "duplicate request/idempotency replay: no duplicate execution",
                ok,
                {
                    "same_action": a1["action_id"] == a2["action_id"],
                    "dispatches": reference.dispatch_count - before,
                    "duplicate_commit": dup[1].get("error"),
                    "conflict": conflict[1].get("error"),
                },
            )
            # J09
            process.fail_next_restart("svc-web-real")
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-web-real",
                {"reason": "J09"},
                "j09",
            )
            approve_all(http, action)
            done = finish(http, action["action_id"])
            _s_ev, evidence = http.call(
                "GET", f"/ops/v1/evidence/{action['action_id']}", session="sess-reader"
            )
            s_h, health = http.call(
                "GET", "/ops/v1/health?target_id=svc-web-real", session="sess-reader"
            )
            ok = (
                done["state"] == "FAILED"
                and done["result"]["failure_classification"] == "PROVIDER_FAILURE"
                and evidence["result_state"] == "FAILED"
                and evidence["failure_classification"] == "PROVIDER_FAILURE"
                and health["health"]["state"] == "UNAVAILABLE"
            )
            runner.record(
                "J09",
                "provider/backend failure: explicit FAILED result + evidence",
                ok,
                {
                    "state": done.get("state"),
                    "classification": done.get("result", {}).get("failure_classification"),
                    "evidence_result": evidence.get("result_state"),
                    "health_after": health.get("health", {}).get("state"),
                },
            )
            # Recover the real process for later journeys.
            process.manage("svc-web-real")
            service.bump_target_version("svc-web-real")
            # J10
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-fixed-real",
                {"reason": "J10"},
                "j10",
            )
            approve_all(http, action)
            done = finish(http, action["action_id"])
            ok = (
                done["state"] == "UNSUPPORTED"
                and done["result"]["failure_classification"] == "UNSUPPORTED_CAPABILITY"
                and process.pid_of("svc-fixed-real") is not None
            )
            runner.record(
                "J10",
                "unsupported operation: explicit unsupported state",
                ok,
                {
                    "state": done.get("state"),
                    "classification": done.get("result", {}).get("failure_classification"),
                },
            )
            # J11
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.BACKUP.REQUEST",
                "db-members-real",
                {"reason": "J11", "backup_set_id": "nightly"},
                "j11",
            )
            approve_all(http, action)
            done = finish(http, action["action_id"])
            _s_b, backups = http.call("GET", "/ops/v1/backups", session="sess-reader")
            op = next(
                (b for b in backups.get("operations", []) if b["action_id"] == action["action_id"]),
                None,
            )
            archive_ok = (
                op is not None
                and backup.backup_path("nightly", op["backup_identity_digest"]).is_file()
            )
            _s_r, readiness = http.call(
                "GET", "/ops/v1/recovery-readiness?target_id=db-members-real", session="sess-reader"
            )
            ok = (
                done["state"] == "SUCCEEDED"
                and op is not None
                and op["state"] == "COMPLETED"
                and archive_ok
                and readiness["recovery_readiness"]["readiness"] == "READY"
            )
            runner.record(
                "J11",
                "backup operation request/status path",
                ok,
                {
                    "state": done.get("state"),
                    "backup_state": None if op is None else op["state"],
                    "archive_exists": archive_ok,
                    "readiness": readiness.get("recovery_readiness", {}).get("readiness"),
                },
            )
            backup_digest = "" if op is None else op["backup_identity_digest"]
            # J13 (before J12 mutates the data)
            status, payload = request_action(
                http,
                "sess-requester",
                "OPS.RESTORE.REQUEST",
                "db-members-real",
                {
                    "reason": "J13",
                    "backup_set_id": "nightly",
                    "backup_identity_digest": "0" * 64,
                    "confirmation": "CONFIRM-DESTRUCTIVE:db-members-real",
                },
                "j13",
            )
            runner.record(
                "J13",
                "mismatched backup/target identity refused",
                status == 403 and payload.get("error") == "OPS_BACKUP_IDENTITY_MISMATCH",
                {"status": status, "error": payload.get("error")},
            )
            # J12
            data_file = tmp / "datastore" / "members.csv"
            data_file.write_text("id,name\n1,alpha\n2,CORRUPT\n")
            params = {
                "reason": "J12",
                "backup_set_id": "nightly",
                "backup_identity_digest": backup_digest,
            }
            no_conf = request_action(
                http,
                "sess-requester",
                "OPS.RESTORE.REQUEST",
                "db-members-real",
                params,
                "j12-noconf",
            )
            status, action = request_action(
                http,
                "sess-requester",
                "OPS.RESTORE.REQUEST",
                "db-members-real",
                {**params, "confirmation": "CONFIRM-DESTRUCTIVE:db-members-real"},
                "j12",
            )
            approvals = approve_all(http, action)
            no_window = http.call(
                "POST", f"/ops/v1/actions/{action['action_id']}/commit", {}, "sess-executor"
            )
            _s_w, window = request_action(
                http,
                "sess-requester",
                "OPS.MAINTENANCE.ENTER",
                "db-members-real",
                {"reason": "J12 window", "duration_minutes": "30"},
                "j12-window",
            )
            approve_all(http, window)
            window_done = finish(http, window["action_id"])
            requester_exec = http.call(
                "POST", f"/ops/v1/actions/{action['action_id']}/commit", {}, "sess-requester"
            )
            done = finish(http, action["action_id"])
            restored = data_file.read_text() == "id,name\n1,alpha\n2,beta\n"
            ok = (
                no_conf[0] == 403
                and no_conf[1].get("error") == "OPS_DESTRUCTIVE_CONFIRMATION_MISSING"
                and action.get("required_approver_classes")
                == ["INCIDENT_COMMANDER", "SECURITY", "TRUST_CUSTODIAN"]
                and approvals == [200, 200, 200]
                and no_window[0] == 403
                and no_window[1].get("error") == "OPS_MAINTENANCE_WINDOW_REQUIRED"
                and window_done["state"] == "SUCCEEDED"
                and requester_exec[0] == 403
                and done["state"] == "SUCCEEDED"
                and restored
            )
            runner.record(
                "J12",
                "restore/recovery request guarded by stronger controls",
                ok,
                {
                    "no_confirmation": no_conf[1].get("error"),
                    "required": action.get("required_approver_classes"),
                    "no_window": no_window[1].get("error"),
                    "requester_execute": requester_exec[1].get("error"),
                    "final": done.get("state"),
                    "data_restored": restored,
                },
            )
            # J14
            _s_m, windows = http.call("GET", "/ops/v1/maintenance", session="sess-reader")
            active = [w for w in windows.get("windows", []) if w["target_id"] == "db-members-real"]
            clock.offset += timedelta(minutes=31)
            _s_m2, windows2 = http.call("GET", "/ops/v1/maintenance", session="sess-reader")
            after = [w for w in windows2.get("windows", []) if w["target_id"] == "db-members-real"]
            ok = (
                bool(active)
                and active[0]["state"] == "ACTIVE"
                and active[0]["active_now"]
                and after[0]["state"] == "EXPIRED"
                and not after[0]["active_now"]
            )
            runner.record(
                "J14",
                "maintenance window request/activation/expiry",
                ok,
                {
                    "before": None if not active else active[0]["state"],
                    "after": None if not after else after[0]["state"],
                },
            )
            # J15
            bad = request_action(
                http,
                "sess-requester",
                "OPS.DEPLOYMENT.ROLLBACK",
                "svc-ref",
                {"reason": "J15", "target_artifact_digest": ART_X},
                "j15-bad",
            )
            ok = bad[0] == 403 and bad[1].get("error") == "OPS_ROLLBACK_ARTIFACT_UNVERIFIED"
            runner.record(
                "J15",
                "rollback only to verified allowed artifact identity",
                ok,
                {"unverified": bad[1].get("error"), "verified_path": "J06"},
            )
            # J16
            ro = request_action(
                http,
                "sess-readonly-operator",
                "OPS.SERVICE.RESTART",
                "svc-web-real",
                {"reason": "J16"},
                "j16",
            )
            _s_me, me = http.call("GET", "/ops/v1/me", session="sess-readonly-operator")
            s_v, _view = http.call(
                "GET", "/ops/v1/status?target_id=svc-web-real", session="sess-readonly-operator"
            )
            ok = (
                ro[0] == 403
                and ro[1].get("error") == "OPS_READ_ONLY_SESSION"
                and me.get("read_only") is True
                and s_v == 200
            )
            runner.record(
                "J16",
                "read-only operator cannot mutate",
                ok,
                {"mutation": ro[1].get("error"), "read_status": s_v},
            )
            # J17
            s_h, health = http.call(
                "GET", "/ops/v1/health?target_id=svc-ref", session="sess-reader"
            )
            text = json.dumps(health)
            ok = (
                s_h == 200
                and health["health"]["details"].get("api_token") == "[REDACTED]"
                and "sk_live_" not in text
                and health["health"]["details"].get("secret_ref") == "vault://ops"
            )
            runner.record(
                "J17",
                "secret-bearing provider metadata rendered redacted",
                ok,
                {
                    "api_token": health.get("health", {}).get("details", {}).get("api_token"),
                    "redacted_fields": health.get("health", {}).get("redacted_fields"),
                },
            )
            # J18
            s_e, evidence = http.call(
                "GET", f"/ops/v1/evidence/{j03_action}", session="sess-reader"
            )
            required = [
                "action_id",
                "request_id",
                "action_type",
                "actor_ref",
                "authority_ref",
                "target_ref",
                "environment",
                "parameters_digest",
                "requested_at",
                "authorization_decision",
                "execution_state",
                "result_state",
                "deployment_identity_ref",
                "evidence_digest",
            ]
            ok = (
                s_e == 200
                and all(evidence.get(k) not in (None, "", []) for k in required)
                and evidence["actor_ref"] == "requester"
                and evidence["deployment_identity_ref"] == "dep-web-1"
            )
            runner.record(
                "J18",
                "audit/evidence lookup by immutable action ID",
                ok,
                {
                    "status": s_e,
                    "missing": [k for k in required if evidence.get(k) in (None, "", [])],
                    "evidence_digest": evidence.get("evidence_digest"),
                },
            )
            # J19: restart the console from the persisted store.
            head_before = service.journal.head_hash()
            count_before = len(service.journal)
            evidence_before = service.evidence_record(j03_action)
            server.shutdown()
            server.server_close()
            loaded = store.load()
            assert loaded is not None
            revived = OperationsConsoleService.from_checkpoint(
                loaded,
                authorities=authorities,
                signer=service.signer,
                adapters=adapters,
                ctrl02=service.ctrl02,
                ctrl03=service.ctrl03,
                store=store,
                sealer=service.sealer,
            )
            app = ConsoleApp(revived, clock=clock.now)
            server = serve(app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            http = Http(f"http://127.0.0.1:{server.server_address[1]}")
            _s_e2, evidence_after = http.call(
                "GET", f"/ops/v1/evidence/{j03_action}", session="sess-reader"
            )
            s_a, actions = http.call("GET", "/ops/v1/actions", session="sess-reader")
            ok = (
                revived.journal.head_hash() == head_before
                and len(revived.journal) == count_before
                and evidence_after == evidence_before
                and s_a == 200
                and len(actions["actions"]) == len(service.actions())
            )
            runner.record(
                "J19",
                "runtime restart does not erase action/evidence history",
                ok,
                {
                    "journal_head": head_before[:16],
                    "records": count_before,
                    "actions_after_restart": len(actions.get("actions", [])),
                },
            )
            # J20
            v1 = http.call(
                "GET", "/ops/v1/status?target_id=svc-voting-tally", session="sess-reader"
            )
            v2 = request_action(
                http,
                "sess-requester",
                "OPS.SERVICE.RESTART",
                "svc-voting-tally",
                {"reason": "J20"},
                "j20",
            )
            _s_t, targets = http.call("GET", "/ops/v1/targets", session="sess-reader")
            listed = any(t["target_id"] == "svc-voting-tally" for t in targets.get("targets", []))
            ok = (
                v1[0] == 403
                and v1[1].get("error") == "OPS_VOTING_BOUNDARY"
                and v2[0] == 403
                and v2[1].get("error") == "OPS_VOTING_BOUNDARY"
                and not listed
            )
            runner.record(
                "J20",
                "voting-domain operational boundary cannot be crossed",
                ok,
                {"read": v1[1].get("error"), "mutate": v2[1].get("error"), "listed": listed},
            )
            revived.journal.verify()
        finally:
            server.shutdown()
            server.server_close()
            process.stop_all()
    passed = sum(r["status"] == "PASS" for r in runner.results)
    payload = {
        "schema": "epd2.ctrl04.e2e-journeys/1",
        "stage": "CTRL-04",
        "transport": "real HTTP (ThreadingHTTPServer) over loopback",
        "integration_class": "REFERENCE_AND_LOCAL_REAL_ADAPTERS",
        "adapters": {
            "local-process": "LocalProcessAdapter: real OS process restart, live health",
            "local-backup": "LocalFilesystemBackupAdapter: real content-addressed archive backup",
            "reference-adapter": (
                "ReferenceOperationsAdapter: deterministic injection for degraded/rollback paths"
            ),
            "store": "JsonFileStore — persisted checkpoint reloaded for J19",
        },
        "non_claim": (
            "The accepted OPS-01/OPS-02/INFRA-01/INFRA-02 provider runtimes are not installed on "
            "canonical main; this evidence proves the governed control semantics over the adapter "
            "contract with real local mechanisms and is not a provider-integration claim."
        ),
        "runtime_source_digest": runtime_source_digest(),
        "journeys_total": 20,
        "journeys_passed": passed,
        "journeys": runner.results,
        "self_state": "CANDIDATE_NOT_ACCEPTED",
    }
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / "e2e_journeys_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(f"CTRL04_E2E:{passed}/20_PASS")
    return 0 if passed == 20 else 1


if __name__ == "__main__":
    sys.exit(main())
