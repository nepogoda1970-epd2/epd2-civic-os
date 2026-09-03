"""EPD2 preview runtime shell (INFRA03 §21, §24, §26..§31, §38, §39).

One parameterized process implementing *infrastructure* semantics only — no
business logic: TLS/mTLS serving with per-workload identity, fail-closed
startup configuration validation, dependency-aware readiness (poll, never
sleep), truthful liveness/readiness/health separation, artifact identity
observation (``/identity``), privacy-safe observability, graceful shutdown
with drain, an idempotent consequential-operation path for
recovery-without-duplicates proofs, ingress proxying with forwarded-header
hygiene, and the voting-domain boundary guard.

Started by the supervisor as::

    python -m scripts.infra03.service --config <instance>/config/<service>.json

The config file carries classified configuration; secrets arrive only as
file references into the instance secret store, never as values.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from scripts.infra03.artifacts import tree_digest_of_directory
from scripts.infra03.config import validate_startup_config
from scripts.infra03.postgres import PG_BINDIR

#: Identity-bearing headers that must never cross into the voting segment
#: (§20, §39): persistent member/person identifiers, account/session
#: identity and generic application correlation ids.
VOTING_FORBIDDEN_HEADERS = (
    "x-member-id",
    "x-person-id",
    "x-account-id",
    "x-session-id",
    "x-user-id",
    "x-correlation-id",
)

_REDACTIONS = (
    re.compile(r"(?i)(password|token|secret|authorization|cookie)[=:]\s*\S+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
)


def _redact(text: str) -> str:
    for pattern in _REDACTIONS:
        text = pattern.sub("[REDACTED]", text)
    return text


class ShellState:
    """Mutable runtime state shared between the server and control threads."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.started_at = time.time()
        self.ready = False
        self.draining = False
        self.observed_digest: str | None = None
        self.checks: dict[str, str] = {}
        self.active_requests = 0
        self.lock = threading.Lock()
        self.log_path = Path(config["log_file"]) if config.get("log_file") else None

    def log(self, level: str, event: str, **fields: Any) -> None:
        record = {
            "ts": round(time.time(), 3),
            "service": self.config.get("service_id"),
            "level": level,
            "event": event,
            **fields,
        }
        line = _redact(json.dumps(record, sort_keys=True))
        if self.log_path is not None:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        self._forward(line)

    def _forward(self, line: str) -> None:
        """Ship the log line to the shared collector (non-voting only)."""
        endpoint = self.config.get("observability_endpoint")
        if not endpoint or str(self.config.get("voting_domain")).lower() == "true":
            return  # voting observability is private by policy (§20)
        try:
            context = ssl.create_default_context(cafile=self.config["trust_ca"])
            context.load_cert_chain(
                self.config["observability_client_cert"], self.config["observability_client_key"]
            )
            host, port = endpoint.rsplit(":", 1)
            connection = http.client.HTTPSConnection(
                "127.0.0.1", int(port), context=context, timeout=2
            )
            connection.sock = context.wrap_socket(
                socket.create_connection(("127.0.0.1", int(port)), timeout=2),
                server_hostname=host,
            )
            connection.request("POST", "/ingest", body=line.encode())
            connection.getresponse().read()
            connection.close()
        except OSError:
            # Observability outage degrades observability, never the service
            # (§44: EXPLICIT_UNAVAILABLE for the collector, SAFE_RETRY here).
            pass


def _db_check(config: dict[str, Any]) -> str:
    """Role-scoped TLS connectivity check to the service's own database."""
    dsn = config.get("db_dsn")
    if not dsn:
        return "not-configured"
    password_file = config.get("db_password_file")
    if not password_file or not Path(password_file).is_file():
        return "secret-missing"
    env = dict(os.environ)
    env["PGPASSWORD"] = Path(password_file).read_text(encoding="utf-8").strip()
    env["PGSSLMODE"] = "verify-full"
    env["PGSSLROOTCERT"] = str(config["db_ca"])
    try:
        completed = subprocess.run(
            [str(PG_BINDIR / "psql"), dsn, "-qAt", "-v", "ON_ERROR_STOP=1", "-c", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unreachable"
    return "ok" if completed.returncode == 0 and completed.stdout.strip() == "1" else "unreachable"


def _readiness_loop(state: ShellState) -> None:
    """Dependency-aware readiness: poll dependencies, never sleep-and-hope
    (§27). Readiness is recomputed continuously so dependency outages turn
    the service unready (§29) and recovery turns it ready again (§45)."""
    config = state.config
    while not state.draining:
        checks: dict[str, str] = {}
        digest_ok = True
        if state.observed_digest is None:
            checks["artifact"] = "computing"
            digest_ok = False
        elif state.observed_digest != config.get("expected_app_digest"):
            checks["artifact"] = "digest-mismatch"
            digest_ok = False
        else:
            checks["artifact"] = "ok"
        db_state = _db_check(config)
        checks["database"] = db_state
        db_ok = db_state in ("ok", "not-configured")
        checks["trust"] = "ok" if Path(config["trust_ca"]).is_file() else "missing"
        with state.lock:
            state.checks = checks
            state.ready = digest_ok and db_ok and checks["trust"] == "ok" and not state.draining
        time.sleep(0.5)


def _digest_worker(state: ShellState) -> None:
    root = Path(state.config["app_root"])
    state.observed_digest = tree_digest_of_directory(root)
    state.log("info", "artifact-digest-observed", digest=state.observed_digest)


def _build_handler(state: ShellState) -> type[BaseHTTPRequestHandler]:
    config = state.config
    is_voting = str(config.get("voting_domain")).lower() == "true"
    is_ingress = bool(config.get("ingress_routes"))
    max_body = int(config.get("max_body_bytes", 1048576))

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "epd2-shell"

        def log_message(self, format: str, *args: Any) -> None:
            state.log("info", "http", detail=_redact(format % args), path=self.path)

        def _reply(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _guard_voting_boundary(self) -> bool:
            if not is_voting:
                return True
            for header in VOTING_FORBIDDEN_HEADERS:
                if self.headers.get(header):
                    self._reply(
                        403,
                        {
                            "refused": "voting-domain boundary",
                            "detail": f"identity/correlation header {header!r} may not "
                            "cross into voting infrastructure",
                        },
                    )
                    state.log(
                        "warning",
                        "voting-boundary-refusal",
                        category="identity-or-correlation-header",
                    )
                    return False
            return True

        def _proxy(self) -> None:
            routes: dict[str, Any] = config["ingress_routes"]
            match = next(((p, b) for p, b in routes.items() if self.path.startswith(p)), None)
            if match is None:
                self._reply(404, {"error": "no route"})
                return
            prefix, backend = match
            length = int(self.headers.get("Content-Length") or 0)
            if length > max_body:
                self._reply(413, {"refused": "request body exceeds the declared limit"})
                return
            body = self.rfile.read(length) if length else b""
            context = ssl.create_default_context(cafile=config["trust_ca"])
            context.load_cert_chain(config["client_cert"], config["client_key"])
            try:
                raw = context.wrap_socket(
                    socket.create_connection(("127.0.0.1", int(backend["port"])), timeout=10),
                    server_hostname=backend["workload"],  # workload identity == SAN
                )
            except (OSError, ssl.SSLError) as error:
                state.log("error", "proxy-backend-unreachable", backend=backend["workload"])
                self._reply(502, {"error": "backend unavailable", "detail": str(error)[:120]})
                return
            connection = http.client.HTTPSConnection("127.0.0.1", context=context)
            connection.sock = raw
            # Forwarded-header hygiene (§21): inbound X-Forwarded-* is never
            # trusted or propagated; the gateway asserts its own values.
            headers = {
                key: value
                for key, value in self.headers.items()
                if not key.lower().startswith("x-forwarded-") and key.lower() != "host"
            }
            headers["X-Forwarded-For"] = self.client_address[0]
            headers["X-Forwarded-Proto"] = "https"
            headers["X-Request-Id"] = f"app-{uuid.uuid4().hex[:16]}"
            target_path = self.path[len(prefix.rstrip("/")) :] or "/"
            if target_path.startswith("/admin"):
                self._reply(403, {"refused": "admin endpoints are not routable via ingress"})
                return
            if target_path.startswith("/internal/") and target_path != "/internal/forwarded":
                # Internal endpoints are east-west only; the forwarded echo is
                # deliberately routable as part of the ingress-hygiene proof.
                self._reply(403, {"refused": "internal endpoints are not routable via ingress"})
                return
            try:
                connection.request(self.command, target_path, body=body, headers=headers)
                response = connection.getresponse()
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() in ("content-type", "content-length"):
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
            except OSError as error:
                self._reply(502, {"error": "backend failed", "detail": str(error)[:120]})
            finally:
                connection.close()

        def _consequential(self) -> None:
            """Idempotent consequential operation (§30, §45): the same
            operation key never executes twice, outage retries included."""
            length = int(self.headers.get("Content-Length") or 0)
            try:
                request = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._reply(400, {"error": "invalid json"})
                return
            key = str(request.get("operation_key", "")).strip()
            if not key or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", key):
                self._reply(400, {"error": "operation_key required"})
                return
            dsn = config.get("db_dsn")
            password_file = config.get("db_password_file")
            if not dsn or not password_file:
                self._reply(503, {"error": "no database configured"})
                return
            env = dict(os.environ)
            env["PGPASSWORD"] = Path(password_file).read_text(encoding="utf-8").strip()
            env["PGSSLMODE"] = "verify-full"
            env["PGSSLROOTCERT"] = str(config["db_ca"])
            sql = (
                "CREATE TABLE IF NOT EXISTS infra03_consequential_ops ("
                "operation_key TEXT PRIMARY KEY, executed_at TIMESTAMPTZ NOT NULL DEFAULT now());"
                f"INSERT INTO infra03_consequential_ops (operation_key) VALUES ('{key}') "
                "ON CONFLICT (operation_key) DO NOTHING RETURNING operation_key;"
            )
            try:
                completed = subprocess.run(
                    [str(PG_BINDIR / "psql"), dsn, "-qAt", "-v", "ON_ERROR_STOP=1", "-c", sql],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                self._reply(503, {"error": "database unavailable", "retry": "safe"})
                return
            if completed.returncode != 0:
                self._reply(503, {"error": "database unavailable", "retry": "safe"})
                return
            executed = completed.stdout.strip() == key
            self._reply(
                200, {"operation_key": key, "executed": executed, "duplicate": not executed}
            )
            state.log("info", "consequential-operation", executed=executed)

        def _handle(self) -> None:
            with state.lock:
                state.active_requests += 1
            try:
                if not self._guard_voting_boundary():
                    return
                if self.path == "/livez":
                    self._reply(200, {"alive": True})
                elif self.path == "/readyz":
                    with state.lock:
                        ready = state.ready
                    if ready:
                        self._reply(200, {"ready": True})
                    else:
                        self._reply(503, {"ready": False})
                elif self.path == "/healthz":
                    # Health output carries states only — no config values,
                    # paths, DSNs or identifiers (§28).
                    with state.lock:
                        payload = {
                            "service": config.get("service_id"),
                            "ready": state.ready,
                            "checks": dict(state.checks),
                            "uptime_seconds": round(time.time() - state.started_at, 1),
                        }
                    self._reply(200, payload)
                elif self.path == "/identity":
                    self._reply(
                        200,
                        {
                            "service": config.get("service_id"),
                            "observed_app_digest": state.observed_digest,
                            "environment": config.get("environment"),
                        },
                    )
                elif self.path == "/internal/consequential" and self.command == "POST":
                    self._consequential()
                elif self.path == "/internal/forwarded":
                    # Echo of forwarded-identity headers as received, so the
                    # ingress hygiene proof can show spoofed values never
                    # survive the boundary (§21).
                    self._reply(
                        200,
                        {
                            "x_forwarded_for": self.headers.get("X-Forwarded-For"),
                            "x_forwarded_proto": self.headers.get("X-Forwarded-Proto"),
                            "x_request_id": self.headers.get("X-Request-Id"),
                        },
                    )
                elif self.path == "/ingest" and self.command == "POST":
                    length = int(self.headers.get("Content-Length") or 0)
                    line = self.rfile.read(length).decode("utf-8", errors="replace")
                    sink = Path(config["app_root"]).parent / "collected.log"
                    if config.get("collector_sink"):
                        sink = Path(config["collector_sink"])
                    with sink.open("a", encoding="utf-8") as handle:
                        handle.write(_redact(line.rstrip("\n")) + "\n")
                    self._reply(200, {"accepted": True})
                elif is_ingress:
                    self._proxy()
                else:
                    self._reply(404, {"error": "unknown path"})
            finally:
                with state.lock:
                    state.active_requests -= 1

        def do_GET(self) -> None:
            self._handle()

        def do_POST(self) -> None:
            self._handle()

    return Handler


def build_server(config: dict[str, Any], state: ShellState) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", int(config["listen_port"])), _build_handler(state))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config["server_cert"], config["server_key"])
    if str(config.get("mtls_required", "")).lower() == "true":
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=config["trust_ca"])
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.infra03.service")
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    findings = validate_startup_config(config)
    if findings:
        for finding in findings:
            print(finding.describe(), file=sys.stderr)
        print("STARTUP_REFUSED: invalid configuration fails closed (INFRA03 §26)", file=sys.stderr)
        return 78  # EX_CONFIG

    state = ShellState(config)
    threading.Thread(target=_digest_worker, args=(state,), daemon=True).start()
    threading.Thread(target=_readiness_loop, args=(state,), daemon=True).start()
    server = build_server(config, state)

    def _terminate(_signum: int, _frame: Any) -> None:
        # Graceful shutdown (§30): readiness off first, then bounded drain.
        state.draining = True
        with state.lock:
            state.ready = False
        grace = float(config.get("shutdown_grace_seconds", 10))
        deadline = time.monotonic() + grace

        def _finish() -> None:
            while time.monotonic() < deadline:
                with state.lock:
                    if state.active_requests == 0:
                        break
                time.sleep(0.1)
            server.shutdown()

        threading.Thread(target=_finish, daemon=True).start()

    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)
    state.log("info", "service-started", port=config.get("listen_port"))
    server.serve_forever(poll_interval=0.2)
    server.server_close()
    state.log("info", "service-stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
