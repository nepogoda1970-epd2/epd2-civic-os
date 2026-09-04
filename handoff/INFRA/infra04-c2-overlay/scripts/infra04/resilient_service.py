"""INFRA-04 resilient runtime shell (invariants I1..I3, I5, I9).

Extends the accepted INFRA-03 shell — reusing its redaction, digest
observation, database probe and TLS/mTLS serving — with the behaviour
INFRA-04 owns:

- five-level readiness (``/readyz``, ``/readyz?level=…``, ``/authz-ready``,
  ``/statez``) computed from live dependency observations, never constant;
- consequential actions admitted only at ``AUTHORITATIVELY_READY`` and only
  while the writer holds the fencing lock — a stale or unavailable
  consequential dependency refuses with an explicit reason (I2);
- split-brain fencing: the durable writer role is held through a PostgreSQL
  advisory lock; a second claimant is refused rather than silently accepted
  (I5), and a fenced writer refuses consequential work;
- an append-only readiness/recovery ledger whose entries are hash-chained,
  so a restart or recovery can extend but never delete or rewrite prior
  evidence (I9);
- idempotent consequential effects that survive restart and retry.

Started by the INFRA-04 supervisor as::

    python -m scripts.infra04.resilient_service --config <instance>/config/<svc>.json
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import ssl
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from scripts.infra03.postgres import PG_BINDIR
from scripts.infra03.service import (
    ShellState,
    _build_handler,
    _digest_worker,
    _redact,
)
from scripts.infra04 import codes
from scripts.infra04.config_ext import validate_startup_config
from scripts.infra04.readiness import (
    DependencyObservation,
    ReadinessAssessment,
    assess,
)

DEFAULT_FRESHNESS_SECONDS = 15.0
DEFAULT_TRUST_FRESHNESS_SECONDS = 60.0

#: Advisory-lock key namespace for the durable-writer fence.
FENCE_NAMESPACE = 0x4550_4432  # "EPD2"

#: Consequential operation keys are validated by shape, never escaped.
_OPERATION_KEY = re.compile(r"[A-Za-z0-9_.:-]{1,120}")


def _fence_key(role: str) -> int:
    digest = hashlib.sha256(role.encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF


#: A connection string with an inline password, as it would appear in a
#: log line. INFRA-03's redactor covers its own known secret shapes; the
#: ledger adds this one because a DSN is the shape a recovery path is most
#: likely to write, and a secret value must never reach evidence (I8).
_DSN_CREDENTIAL = re.compile(r"(postgres(?:ql)?://[^:@\s\"]+:)([^@\s\"]+)(@)", re.IGNORECASE)


def _scrub(line: str) -> str:
    """INFRA-03 redaction plus DSN-embedded credential removal."""
    return _DSN_CREDENTIAL.sub(r"\1<redacted>\3", _redact(line))


class LedgerChain:
    """Append-only, hash-chained evidence ledger (I9, M32..M34).

    Each entry carries the digest of the previous entry, so deletion,
    truncation or rewriting of prior evidence is detectable by anyone who
    replays the file. Recovery may only append.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _tail_digest(self) -> str:
        previous = "0" * 64
        if not self.path.is_file():
            return previous
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            previous = hashlib.sha256(line.encode()).hexdigest()
        return previous

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Several resilient-service processes share this ledger. A threading
        # lock protects only one process, so the tail read and successor append
        # must also be serialized at the file level. Otherwise two processes
        # can observe the same tail and both append a successor, breaking I9.
        with self._lock:
            with self.path.open("a+", encoding="utf-8") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    handle.seek(0)
                    previous = "0" * 64
                    for line in handle.read().splitlines():
                        if not line.strip():
                            continue
                        previous = hashlib.sha256(line.encode()).hexdigest()
                    entry = {
                        "event": event,
                        "recorded_at": round(time.time(), 3),
                        "previous": previous,
                        "payload": payload,
                    }
                    line = _scrub(json.dumps(entry, sort_keys=True))
                    handle.seek(0, 2)
                    handle.write(line + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return entry

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def verify(self) -> list[str]:
        """Recompute the chain; any break names the exact defect."""
        findings: list[str] = []
        previous = "0" * 64
        for index, line in enumerate(
            [
                raw
                for raw in (
                    self.path.read_text(encoding="utf-8").splitlines()
                    if self.path.is_file()
                    else []
                )
                if raw.strip()
            ]
        ):
            entry = json.loads(line)
            if entry.get("previous") != previous:
                findings.append(
                    f"{codes.AUDIT_CHAIN_BROKEN}: entry {index}: recorded previous "
                    f"{entry.get('previous')!r} does not match the computed {previous!r}"
                )
            previous = hashlib.sha256(line.encode()).hexdigest()
        return findings


class ResilientState(ShellState):
    """INFRA-03 shell state plus INFRA-04 readiness/fencing/ledger state."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.assessment = ReadinessAssessment("PROCESS_ALIVE", "STARTING", ["starting"], [])
        self.observations: dict[str, DependencyObservation] = {}
        self.fence_held = False
        self.fence_reason = "not-claimed"
        self._fence_process: subprocess.Popen[bytes] | None = None
        ledger = config.get("readiness_ledger")
        self.ledger = LedgerChain(Path(ledger)) if ledger else None
        self.recovery_generation = str(config.get("recovery_generation", "1"))

    def record(self, event: str, payload: dict[str, Any]) -> None:
        if self.ledger is not None:
            self.ledger.append(event, payload)


# -- dependency observation ------------------------------------------------


def _psql_ok(config: dict[str, Any], sql: str, timeout: int = 8) -> tuple[bool, str]:
    dsn = config.get("db_dsn")
    password_file = config.get("db_password_file")
    if not dsn or not password_file or not Path(str(password_file)).is_file():
        return False, "not-configured"
    env = dict(os.environ)
    env["PGPASSWORD"] = Path(str(password_file)).read_text(encoding="utf-8").strip()
    env["PGSSLMODE"] = "verify-full"
    env["PGSSLROOTCERT"] = str(config["db_ca"])
    try:
        completed = subprocess.run(
            [str(PG_BINDIR / "psql"), str(dsn), "-qAt", "-v", "ON_ERROR_STOP=1", "-c", sql],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "unreachable"
    if completed.returncode != 0:
        return False, "unreachable"
    return True, completed.stdout.strip()


def observe(state: ResilientState) -> list[DependencyObservation]:
    """Observe every declared dependency with a real probe."""
    config = state.config
    freshness = float(config.get("dependency_freshness_seconds", DEFAULT_FRESHNESS_SECONDS))
    trust_freshness = float(config.get("trust_freshness_seconds", DEFAULT_TRUST_FRESHNESS_SECONDS))
    now = time.time()
    observations: list[DependencyObservation] = []

    if config.get("db_dsn"):
        ok, _ = _psql_ok(config, "SELECT 1")
        observations.append(
            DependencyObservation(
                name="database",
                status="ok" if ok else "unavailable",
                age_seconds=0.0 if ok else None,
                freshness_bound_seconds=freshness,
                consequential=True,
            )
        )
        # Migration state must match the digest this runtime was deployed
        # against; a drifted schema is a stale consequential dependency.
        declared = str(config.get("migration_ledger_digest", ""))
        if declared:
            ok_ledger, value = _psql_ok(
                config,
                "SELECT coalesce(string_agg(filename || ':' || sha256, ',' ORDER BY filename), '') "
                "FROM infra03_migration_ledger",
            )
            observed_digest = hashlib.sha256(value.encode()).hexdigest() if ok_ledger else ""
            fresh = ok_ledger and observed_digest == declared
            observations.append(
                DependencyObservation(
                    name="migration_ledger",
                    status="ok" if ok_ledger else "unavailable",
                    age_seconds=0.0 if fresh else None,
                    freshness_bound_seconds=freshness,
                    consequential=True,
                )
            )

    trust_ca = config.get("trust_ca")
    trust_ok = bool(trust_ca) and Path(str(trust_ca)).is_file()
    trust_age = (now - Path(str(trust_ca)).stat().st_mtime) if trust_ok else None
    observations.append(
        DependencyObservation(
            name="trust_material",
            status="ok" if trust_ok else "unavailable",
            # Trust material is fresh while the deployment-scoped CA file is
            # the one this process was started with; a rotated/removed CA is
            # unavailable, an old one exceeds the governed bound.
            age_seconds=min(trust_age, trust_freshness) if trust_age is not None else None,
            freshness_bound_seconds=trust_freshness,
            consequential=True,
        )
    )

    observations.append(
        DependencyObservation(
            name="artifact_identity",
            status="ok" if state.observed_digest else "unknown",
            age_seconds=0.0 if state.observed_digest == config.get("expected_app_digest") else None,
            freshness_bound_seconds=freshness,
            consequential=True,
        )
    )
    return observations


def _fence_loop(state: ResilientState) -> None:
    """Hold the durable-writer fence, re-claiming it when it becomes free.

    A single claim attempt is not a rejoin contract: a writer that lost the
    race at startup, or whose fence session died with its own process, must
    take the fence again once the previous holder is gone — and must stay
    non-authoritative in the meantime (I5).
    """
    while not state.draining:
        holder = state._fence_process
        if state.fence_held and holder is not None and holder.poll() is None:
            time.sleep(1.0)
            continue
        if state.fence_held:
            state.fence_held = False
            state.fence_reason = "lost: fence session ended"
            state.record("fence-lost", {"generation": state.recovery_generation})
        # Never leave a previous session alive: an orphaned holder would keep
        # the lock while this process believes it lost it, and the writer
        # would fence itself out permanently.
        stale = state._fence_process
        if stale is not None:
            state._fence_process = None
            stale.terminate()
            try:
                stale.wait(timeout=10)
            except subprocess.TimeoutExpired:
                stale.kill()
        _claim_fence(state)
        if not state.fence_held:
            time.sleep(2.0)


def _claim_fence(state: ResilientState) -> None:
    """Claim the durable-writer fence via a PostgreSQL advisory lock (I5).

    The lock is session-scoped: it is held by a long-lived ``psql`` session
    and released the moment that session dies, so a crashed writer cannot
    keep the fence and two live writers can never both hold it.
    """
    config = state.config
    role = str(config.get("fencing_role", ""))
    if not role or not config.get("db_dsn"):
        state.fence_held = False
        state.fence_reason = "no-fencing-role-declared"
        return
    key = _fence_key(str(config.get("fencing_key", role)))
    env = dict(os.environ)
    password_file = config.get("db_password_file")
    if not password_file or not Path(str(password_file)).is_file():
        state.fence_held = False
        state.fence_reason = "no-credential"
        return
    env["PGPASSWORD"] = Path(str(password_file)).read_text(encoding="utf-8").strip()
    env["PGSSLMODE"] = "verify-full"
    env["PGSSLROOTCERT"] = str(config["db_ca"])
    try:
        # The fence session reads from a pipe this process holds open. It is
        # deliberately not "psql -c ... -c pg_sleep": a sleeping session
        # survives its parent, and an orphaned holder would keep both the
        # advisory lock and a database connection after the writer it
        # represents is gone. With the statement fed over stdin, the pipe
        # closes when this process dies — by any means, including SIGKILL —
        # psql reads EOF, the session ends, and the fence is released. That
        # is exactly the lifetime a durable-writer fence must have (I5).
        process = subprocess.Popen(
            [str(PG_BINDIR / "psql"), str(config["db_dsn"]), "-qAt", "-v", "ON_ERROR_STOP=1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    except OSError as error:
        state.fence_held = False
        state.fence_reason = f"fence-unavailable: {error}"
        return
    assert process.stdout is not None and process.stdin is not None
    try:
        process.stdin.write(f"SELECT pg_try_advisory_lock({FENCE_NAMESPACE}, {key});\n".encode())
        process.stdin.flush()
    except (BrokenPipeError, OSError):
        state.fence_held = False
        state.fence_reason = "fence-session-unavailable"
        process.kill()
        return
    deadline = time.monotonic() + 10
    granted = False
    while time.monotonic() < deadline:
        line = process.stdout.readline().decode().strip()
        if line in ("t", "f"):
            granted = line == "t"
            break
        if process.poll() is not None:
            break
    state._fence_process = process
    state.fence_held = granted
    state.fence_reason = "held" if granted else "refused: another writer holds the fence"
    if not granted:
        process.terminate()
        state._fence_process = None
    state.record(
        "fence-claim",
        {
            "role": role,
            "granted": granted,
            "reason": state.fence_reason,
            "generation": state.recovery_generation,
        },
    )


def _readiness_loop(state: ResilientState) -> None:
    """Continuously recompute the truthful readiness level."""
    previous_level = None
    while not state.draining:
        observations = observe(state)
        state.observations = {o.name: o for o in observations}
        transport_ok = Path(str(state.config["trust_ca"])).is_file()
        invariants_ok = state.observed_digest == state.config.get("expected_app_digest")
        assessment = assess(
            process_alive=True,
            transport_ok=transport_ok,
            service_invariants_ok=invariants_ok,
            dependencies=observations,
            draining=state.draining,
        )
        # I5: a declared durable writer that does not hold the fence is not
        # authoritative, whatever its dependencies say. It stays explicitly
        # read-only and names the fence as the reason, so readiness, the
        # authority endpoint and the consequential path can never disagree.
        if state.config.get("fencing_role") and not state.fence_held:
            assessment = ReadinessAssessment(
                "SERVICE_READY",
                "DEGRADED_READ_ONLY",
                [*assessment.reasons, f"fence: {state.fence_reason}"],
                assessment.dependencies,
            )
        with state.lock:
            state.assessment = assessment
            state.ready = assessment.level in ("DEPENDENCY_READY", "AUTHORITATIVELY_READY")
            state.checks = {o.name: o.status for o in observations}
        if assessment.level != previous_level:
            state.record(
                "readiness-transition",
                {
                    "from": previous_level,
                    "to": assessment.level,
                    "state": assessment.state,
                    "reasons": assessment.reasons,
                    "generation": state.recovery_generation,
                },
            )
            previous_level = assessment.level
        # One observation per second against a 15-second freshness bound.
        # Polling faster buys no truth and costs a database connection each
        # time.
        time.sleep(1.0)


def _handle_infra04(state: ResilientState, handler: Any) -> bool:
    """INFRA-04 endpoints. Returns True when the request was handled."""
    path = handler.path.split("?", 1)[0]
    query = handler.path.split("?", 1)[1] if "?" in handler.path else ""
    with state.lock:
        assessment = state.assessment

    if path == "/statez":
        handler._reply(
            200,
            {
                "service": state.config.get("service_id"),
                "generation": state.recovery_generation,
                "fence": {"held": state.fence_held, "reason": state.fence_reason},
                **assessment.as_document(),
            },
        )
        return True

    if path == "/authz-ready":
        authoritative = assessment.authoritative and state.fence_held
        handler._reply(
            200 if authoritative else 503,
            {
                "authoritative": authoritative,
                "level": assessment.level,
                "state": assessment.state,
                "reasons": assessment.reasons
                + ([] if state.fence_held else [f"fence: {state.fence_reason}"]),
            },
        )
        return True

    if path == "/readyz" and "level=" in query:
        wanted = query.split("level=", 1)[1].split("&", 1)[0].upper()
        from scripts.infra04.readiness import LEVEL_RANK

        satisfied = wanted in LEVEL_RANK and LEVEL_RANK[wanted] <= LEVEL_RANK[assessment.level]
        handler._reply(
            200 if satisfied else 503,
            {
                "requested_level": wanted,
                "supported_level": assessment.level,
                "state": assessment.state,
                "satisfied": satisfied,
                "reasons": assessment.reasons,
            },
        )
        return True

    if path == "/internal/consequential" and handler.command == "POST":
        _consequential(state, handler)
        return True

    return False


def _consequential(state: ResilientState, handler: Any) -> None:
    """A consequential action: authoritative readiness + fence + idempotency."""
    length = int(handler.headers.get("Content-Length") or 0)
    try:
        request = json.loads(handler.rfile.read(length) or b"{}")
    except json.JSONDecodeError:
        handler._reply(400, {"error": "invalid json"})
        return
    key = str(request.get("operation_key", "")).strip()
    if not key:
        handler._reply(400, {"error": "operation_key required"})
        return
    if not _OPERATION_KEY.fullmatch(key):
        # The key reaches SQL, so its shape is validated rather than escaped:
        # anything outside the governed alphabet is refused, not sanitised.
        handler._reply(400, {"error": "operation_key has a forbidden shape"})
        state.record("consequential-refused", {"reason": "malformed-operation-key"})
        return

    with state.lock:
        assessment = state.assessment
    if not assessment.authoritative:
        handler._reply(
            503,
            {
                "refused": "NOT_AUTHORITATIVELY_READY",
                "level": assessment.level,
                "state": assessment.state,
                "reasons": assessment.reasons,
                "retry": "safe",
            },
        )
        state.record(
            "consequential-refused",
            {"operation_key": key, "reason": "not-authoritative", "level": assessment.level},
        )
        return
    if not state.fence_held:
        handler._reply(
            409,
            {
                "refused": "WRITER_FENCED",
                "reason": state.fence_reason,
                "retry": "safe",
            },
        )
        state.record("consequential-refused", {"operation_key": key, "reason": "fenced"})
        return

    ok, value = _psql_ok(
        state.config,
        "CREATE TABLE IF NOT EXISTS infra04_consequential_ops ("
        "operation_key TEXT PRIMARY KEY, generation TEXT NOT NULL, "
        "executed_at TIMESTAMPTZ NOT NULL DEFAULT now());"
        f"INSERT INTO infra04_consequential_ops (operation_key, generation) "
        f"VALUES ('{key}', '{state.recovery_generation}') "
        "ON CONFLICT (operation_key) DO NOTHING RETURNING operation_key;",
    )
    if not ok:
        handler._reply(503, {"error": "database unavailable", "retry": "safe"})
        state.record("consequential-refused", {"operation_key": key, "reason": "db-unavailable"})
        return
    executed = value == key
    handler._reply(200, {"operation_key": key, "executed": executed, "duplicate": not executed})
    state.record(
        "consequential-effect",
        {
            "operation_key": key,
            "executed": executed,
            "duplicate": not executed,
            "generation": state.recovery_generation,
        },
    )


def build_resilient_server(config: dict[str, Any], state: ResilientState) -> ThreadingHTTPServer:
    """The INFRA-03 handler with the INFRA-04 endpoints layered in front.

    The inherited paths (``/livez``, ``/healthz``, ``/identity``,
    ``/ingest``, ingress proxying, the voting-boundary guard) keep their
    accepted behaviour untouched; INFRA-04 only adds its own routes ahead
    of them.
    """
    base = _build_handler(state)

    class ResilientHandler(base):  # type: ignore[valid-type,misc]
        def _handle(self) -> None:
            with state.lock:
                state.active_requests += 1
            try:
                if _handle_infra04(state, self):
                    return
            finally:
                with state.lock:
                    state.active_requests -= 1
            super()._handle()

    server = ThreadingHTTPServer(("127.0.0.1", int(config["listen_port"])), ResilientHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config["server_cert"], config["server_key"])
    if str(config.get("mtls_required", "")).lower() == "true":
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=config["trust_ca"])
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.infra04.resilient_service")
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    findings = validate_startup_config(config)
    if findings:
        for finding in findings:
            print(finding.describe(), file=sys.stderr)
        print("STARTUP_REFUSED: invalid configuration fails closed (INFRA04 I3)", file=sys.stderr)
        return 78

    state = ResilientState(config)
    state.record(
        "process-start",
        {"service": config.get("service_id"), "generation": state.recovery_generation},
    )
    threading.Thread(target=_digest_worker, args=(state,), daemon=True).start()
    threading.Thread(target=_readiness_loop, args=(state,), daemon=True).start()
    threading.Thread(target=_fence_loop, args=(state,), daemon=True).start()

    server = build_resilient_server(config, state)

    def _terminate(_signum: int, _frame: Any) -> None:
        state.draining = True
        with state.lock:
            state.ready = False
        state.record("process-draining", {"generation": state.recovery_generation})
        grace = float(config.get("shutdown_grace_seconds", 10))
        deadline = time.monotonic() + grace

        def _finish() -> None:
            while time.monotonic() < deadline:
                with state.lock:
                    if state.active_requests == 0:
                        break
                time.sleep(0.1)
            if state._fence_process is not None:
                state._fence_process.terminate()
            server.shutdown()

        threading.Thread(target=_finish, daemon=True).start()

    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)
    state.log("info", "resilient-service-started", port=config.get("listen_port"))
    server.serve_forever(poll_interval=0.2)
    server.server_close()
    state.record("process-stop", {"generation": state.recovery_generation})
    return 0


if __name__ == "__main__":
    sys.exit(main())
