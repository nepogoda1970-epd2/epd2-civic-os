"""Live runtime scenario proofs over one deployed preview instance
(INFRA03 §12, §21, §23, §24, §27..§34, §38..§47).

One deployment session executes every runtime scenario against the real
running stack — TLS/mTLS negatives, PostgreSQL behavior, health/readiness
truth, graceful shutdown, failure injection and recovery, redeploy,
rollback safety, drift, seed/reset, voting isolation, observability
privacy, resource boundaries and destructive safety. Every scenario
returns machine-readable evidence; refusals that are required behavior are
recorded as such — a required refusal that does not happen is a finding.
"""

from __future__ import annotations

import http.client
import json
import signal
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from scripts.infra03 import codes
from scripts.infra03.postgres import PG_BINDIR
from scripts.infra03.supervisor import Supervisor, probe
from scripts.infra03.trust import TrustAuthority

FIXTURE_FILE = Path("infra/runtime/fixtures/identity_preview_fixture.sql")


class ScenarioSession:
    """Scenario executor bound to a live, already-deployed supervisor."""

    def __init__(self, supervisor: Supervisor, repo_root: Path) -> None:
        self.sup = supervisor
        self.root = repo_root
        self.findings: list[str] = []

    # -- helpers -----------------------------------------------------------

    def _fail(self, code: str, subject: str, detail: str) -> None:
        self.findings.append(f"{code}: {subject}: {detail}")

    def _app_ca(self) -> TrustAuthority:
        return self.sup.authorities["application-ca"]

    def _voting_ca(self) -> TrustAuthority:
        return self.sup.authorities["voting-ca"]

    def _client_pair(self, authority: TrustAuthority, workload: str) -> tuple[Path, Path]:
        cert = authority.directory / f"client-{workload}.crt"
        key = authority.directory / f"client-{workload}.key"
        if not cert.is_file():
            authority.issue(workload, "client", ("localhost",))
        return cert, key

    def _expect_refusal(self, subject: str, code: str, action: Any, detail: str) -> dict[str, Any]:
        """Run an action that MUST fail; success is the defect."""
        try:
            action()
        except (ssl.SSLError, ssl.CertificateError, OSError, ConnectionError) as error:
            return {"subject": subject, "refused": True, "reason": type(error).__name__}
        self._fail(code, subject, detail)
        return {"subject": subject, "refused": False}

    # -- TLS (§23) ---------------------------------------------------------

    def tls_scenarios(self) -> dict[str, Any]:
        gateway = self.sup.services["ingress-gateway"]
        app_ca = self._app_ca()
        results: dict[str, Any] = {}

        status, _ = probe(gateway.port, "/healthz", app_ca.cert_path, server_hostname="localhost")
        results["valid_cert_path"] = {"status": status, "ok": status == 200}
        if status != 200:
            self._fail(codes.TRUST_MATERIAL_INVALID, "ingress", "valid TLS path did not serve")

        results["wrong_ca_rejected"] = self._expect_refusal(
            "ingress-with-voting-ca-trust",
            codes.UNTRUSTED_CA,
            lambda: probe(gateway.port, "/healthz", self._voting_ca().cert_path),
            "a client trusting only a foreign CA accepted the server",
        )
        results["wrong_hostname_rejected"] = self._expect_refusal(
            "ingress-wrong-hostname",
            codes.HOSTNAME_MISMATCH,
            lambda: probe(
                gateway.port, "/healthz", app_ca.cert_path, server_hostname="evil.example"
            ),
            "hostname/SAN validation did not reject a wrong hostname",
        )

        def _plaintext() -> None:
            connection = http.client.HTTPConnection("127.0.0.1", gateway.port, timeout=3)
            connection.request("GET", "/healthz")
            response = connection.getresponse()
            if response.status:  # any HTTP response over plaintext = fallback
                raise AssertionError("served plaintext")

        try:
            _plaintext()
            self._fail(
                codes.PLAINTEXT_FALLBACK_FORBIDDEN, "ingress", "TLS port served plaintext HTTP"
            )
            results["plaintext_refused"] = {"refused": False}
        except (OSError, http.client.HTTPException):
            results["plaintext_refused"] = {"refused": True}
        except AssertionError:
            self._fail(
                codes.PLAINTEXT_FALLBACK_FORBIDDEN, "ingress", "TLS port served plaintext HTTP"
            )
            results["plaintext_refused"] = {"refused": False}

        expired_cert, expired_key = app_ca.issue(
            "expired-demo", "server", ("localhost",), expired=True
        )
        results["expired_cert_rejected"] = self._expired_server_demo(expired_cert, expired_key)
        return results

    def _expired_server_demo(self, cert: Path, key: Path) -> dict[str, Any]:
        """A throwaway listener with an expired certificate must be refused."""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class _H(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(200)
                self.end_headers()

            def log_message(self, *_: Any) -> None:
                pass

        server = HTTPServer(("127.0.0.1", 0), _H)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = self._expect_refusal(
                "expired-server-certificate",
                codes.TRUST_MATERIAL_INVALID,
                lambda: probe(port, "/", self._app_ca().cert_path),
                "an expired server certificate was accepted",
            )
        finally:
            server.shutdown()
        return result

    # -- mTLS (§24) --------------------------------------------------------

    def mtls_scenarios(self) -> dict[str, Any]:
        identity = self.sup.services["identity-runtime-shell"]
        app_ca = self._app_ca()
        results: dict[str, Any] = {}

        results["missing_client_cert_rejected"] = self._expect_refusal(
            "identity-shell-no-client-cert",
            codes.CLIENT_CERT_MISSING,
            lambda: probe(
                identity.port,
                "/healthz",
                app_ca.cert_path,
                server_hostname="identity-runtime-shell",
            ),
            "an mTLS endpoint served a client without a certificate",
        )

        voting_cert, voting_key = self._client_pair(self._voting_ca(), "foreign-domain-client")
        results["wrong_ca_client_rejected"] = self._expect_refusal(
            "identity-shell-voting-ca-client",
            codes.UNTRUSTED_CA,
            lambda: probe(
                identity.port,
                "/healthz",
                app_ca.cert_path,
                client_cert=voting_cert,
                client_key=voting_key,
                server_hostname="identity-runtime-shell",
            ),
            "a client certificate from a foreign trust domain was accepted",
        )

        good_cert, good_key = self._client_pair(app_ca, "scenario-client")
        status, _ = probe(
            identity.port,
            "/healthz",
            app_ca.cert_path,
            client_cert=good_cert,
            client_key=good_key,
            server_hostname="identity-runtime-shell",
        )
        results["valid_client_accepted"] = {"status": status, "ok": status == 200}
        if status != 200:
            self._fail(codes.TRUST_MATERIAL_INVALID, "identity-shell", "valid mTLS client refused")

        results["workload_identity_enforced"] = self._expect_refusal(
            "identity-shell-as-membership",
            codes.WORKLOAD_IDENTITY_MISMATCH,
            lambda: probe(
                identity.port,
                "/healthz",
                app_ca.cert_path,
                client_cert=good_cert,
                client_key=good_key,
                server_hostname="membership-runtime-shell",
            ),
            "a server certificate for one workload satisfied another workload's identity check",
        )

        expired_cert, expired_key = app_ca.issue(
            "expired-client-demo", "client", ("localhost",), expired=True
        )
        results["expired_client_rejected"] = self._expect_refusal(
            "identity-shell-expired-client",
            codes.TRUST_MATERIAL_INVALID,
            lambda: probe(
                identity.port,
                "/healthz",
                app_ca.cert_path,
                client_cert=expired_cert,
                client_key=expired_key,
                server_hostname="identity-runtime-shell",
            ),
            "an expired client certificate was accepted",
        )
        return results

    # -- ingress hygiene (§21) ---------------------------------------------

    def ingress_scenarios(self) -> dict[str, Any]:
        gateway = self.sup.services["ingress-gateway"]
        app_ca = self._app_ca()
        results: dict[str, Any] = {}

        def _request(
            path: str, headers: dict[str, str] | None = None, body: bytes = b""
        ) -> tuple[int, dict[str, Any]]:
            context = ssl.create_default_context(cafile=str(app_ca.cert_path))
            raw = context.wrap_socket(
                socket.create_connection(("127.0.0.1", gateway.port), timeout=10),
                server_hostname="localhost",
            )
            connection = http.client.HTTPSConnection("127.0.0.1", context=context)
            connection.sock = raw
            try:
                method = "POST" if body else "GET"
                connection.request(method, path, body=body or None, headers=headers or {})
                response = connection.getresponse()
                data = response.read()
                try:
                    return response.status, json.loads(data)
                except json.JSONDecodeError:
                    return response.status, {}
            finally:
                connection.close()

        status, payload = _request("/identity-shell/healthz")
        results["routing"] = {"status": status, "ok": status == 200}
        if status != 200:
            self._fail(codes.PARTIAL_UNSAFE_EXPOSURE, "ingress-routing", "route did not serve")

        status, payload = _request(
            "/identity-shell/internal/forwarded",
            headers={"X-Forwarded-For": "6.6.6.6", "X-Forwarded-Proto": "gopher"},
        )
        spoof_survived = payload.get("x_forwarded_for") == "6.6.6.6"
        results["forwarded_header_hygiene"] = {
            "status": status,
            "backend_saw": payload,
            "spoof_stripped": not spoof_survived,
        }
        if spoof_survived:
            self._fail(
                codes.FORWARDED_HEADER_UNTRUSTED,
                "ingress",
                "spoofed X-Forwarded-For survived the trust boundary",
            )

        status, _ = _request("/identity-shell/admin/anything")
        results["admin_refused_via_ingress"] = {"status": status, "refused": status == 403}
        if status != 403:
            self._fail(codes.ADMIN_ENDPOINT_PUBLIC, "ingress", "admin route reachable via ingress")

        status, _ = _request("/identity-shell/internal/consequential", body=b"{}")
        results["internal_refused_via_ingress"] = {"status": status, "refused": status == 403}
        if status != 403:
            self._fail(
                codes.ADMIN_ENDPOINT_PUBLIC,
                "ingress",
                "internal consequential endpoint reachable via ingress",
            )

        try:
            status, _ = _request("/identity-shell/echo", body=b"x" * (2 * 1024 * 1024))
            limited = status == 413
            results["request_limit"] = {"status": status, "refused": limited}
        except (ssl.SSLError, OSError):
            # the gateway refused the oversized body and closed the
            # connection before consuming it — a refusal, not a failure
            limited = True
            results["request_limit"] = {"refused": True, "mode": "connection-refused"}
        if not limited:
            self._fail(codes.PARTIAL_UNSAFE_EXPOSURE, "ingress", "oversized request not limited")
        return results

    # -- egress / segmentation (§19, §22) ----------------------------------

    def egress_scenarios(self) -> dict[str, Any]:
        listening = self.sup._listening_ports()
        non_loopback: list[int] = []
        for table in ("/proc/net/tcp", "/proc/net/tcp6"):
            try:
                lines = Path(table).read_text().splitlines()[1:]
            except OSError:
                continue
            for line in lines:
                parts = line.split()
                if len(parts) > 3 and parts[3] == "0A":
                    address, port_hex = parts[1].rsplit(":", 1)
                    port = int(port_hex, 16)
                    if port in range(8400, 8500) and address not in (
                        "0100007F",
                        "00000000000000000000000001000000",
                    ):
                        non_loopback.append(port)
        for port in non_loopback:
            self._fail(
                codes.UNDECLARED_EGRESS,
                f"port {port}",
                "runtime port bound beyond loopback without a declared exposure",
            )
        declared_egress = [
            {"service": name, "egress": service.get("egress")}
            for name, service in self.sup.topology["services"].items()
            if service.get("egress")
        ]
        return {
            "runtime_ports_loopback_only": not non_loopback,
            "non_loopback_ports": non_loopback,
            "declared_external_egress": declared_egress,
            "listening_runtime_ports": sorted(p for p in listening if p in range(8400, 8500)),
            "enforcement_note": (
                "policy default-deny with socket-level verification; kernel-level "
                "egress filtering is deferred to real infrastructure (known limitation)"
            ),
        }

    # -- PostgreSQL (§12, §13, §15, §36) -----------------------------------

    def postgres_scenarios(self) -> dict[str, Any]:
        cluster = self.sup.cluster
        secrets = self.sup.secrets
        assert cluster is not None and secrets is not None
        results: dict[str, Any] = {}
        password = secrets.value("db-password/rt_identity")

        version = cluster.admin_sql("SHOW server_version").strip()
        num = cluster.admin_sql("SHOW server_version_num").strip()
        results["server_version"] = {"version": version, "server_version_num": num}
        if not num.startswith("16"):
            self._fail(codes.NON_POSTGRES_SUBSTITUTION, "cluster", f"unexpected engine {version}")

        tls_row = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()",
        ).stdout.strip()
        results["client_connection_tls"] = {"ssl": tls_row}
        if tls_row != "t":
            self._fail(codes.PLAINTEXT_FALLBACK_FORBIDDEN, "postgres", "client session not TLS")

        cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "BEGIN; INSERT INTO account_registry_record "
            "(account_id, account_status, scope_level, scope_unit_id, created_at, "
            "anonymization_state, version, document) VALUES "
            "('preview-txn-rollback', 'active', 'federal', 'u', 'now', 'none', 1, '{}'); ROLLBACK;",
        )
        rolled_back = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT count(*) FROM account_registry_record WHERE account_id='preview-txn-rollback'",
        ).stdout.strip()
        results["transaction_rollback"] = {"rows_after_rollback": rolled_back}
        if rolled_back != "0":
            self._fail(codes.MIGRATION_LEDGER_VIOLATION, "transactions", "rollback left state")

        denied = cluster.client_sql(
            "rt_identity", password, "epd2_membership", "SELECT 1", check=False
        )
        results["credential_isolation"] = {
            "cross_database_denied": denied.returncode != 0,
            "detail": denied.stderr.strip()[-120:],
        }
        if denied.returncode == 0:
            self._fail(
                codes.ENVIRONMENT_ISOLATION_BREACH,
                "rt_identity->epd2_membership",
                "role connected to a foreign service database",
            )

        import os as _os

        env = dict(_os.environ)
        env["PGPASSWORD"] = password
        env["PGSSLMODE"] = "disable"
        plaintext = subprocess.run(
            [
                str(PG_BINDIR / "psql"),
                "-h",
                "127.0.0.1",
                "-p",
                str(cluster.port),
                "-U",
                "rt_identity",
                "-d",
                "epd2_identity",
                "-c",
                "SELECT 1",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
            check=False,
        )
        results["plaintext_tcp_refused"] = {"refused": plaintext.returncode != 0}
        if plaintext.returncode == 0:
            self._fail(
                codes.PLAINTEXT_FALLBACK_FORBIDDEN, "postgres", "non-TLS TCP session accepted"
            )

        cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "INSERT INTO account_registry_record (account_id, account_status, scope_level, "
            "scope_unit_id, created_at, anonymization_state, version, document) VALUES "
            "('preview-persistence-proof', 'active', 'federal', 'u', 'now', 'none', 1, '{}') "
            "ON CONFLICT (account_id) DO NOTHING",
        )
        cluster.stop()
        cluster.start()
        if not cluster.wait_ready(60):
            self._fail(codes.HIDDEN_FAILURE_SUCCESS, "postgres", "cluster restart failed")
        persisted = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT count(*) FROM account_registry_record "
            "WHERE account_id='preview-persistence-proof'",
        ).stdout.strip()
        results["restart_persistence"] = {"row_survived_restart": persisted == "1"}
        if persisted != "1":
            self._fail(
                codes.PERSISTENCE_CLASS_VIOLATION,
                "postgres",
                "persistent data did not survive a service restart",
            )
        return results

    # -- health/readiness truth + failure/recovery (§28..§31, §44, §45) ----

    def failure_recovery_scenarios(self) -> dict[str, Any]:
        cluster = self.sup.cluster
        assert cluster is not None
        results: dict[str, Any] = {}

        def _op(key: str) -> tuple[int, dict[str, Any]]:
            service = self.sup.topology["services"]["identity-runtime-shell"]
            authority = self._service_authority(service)
            cert, keyfile = self._client_pair(authority, "scenario-client")
            context = ssl.create_default_context(cafile=str(authority.cert_path))
            context.load_cert_chain(str(cert), str(keyfile))
            raw = context.wrap_socket(
                socket.create_connection(("127.0.0.1", 8451), timeout=10),
                server_hostname="identity-runtime-shell",
            )
            connection = http.client.HTTPSConnection("127.0.0.1", context=context)
            connection.sock = raw
            try:
                connection.request(
                    "POST", "/internal/consequential", body=json.dumps({"operation_key": key})
                )
                response = connection.getresponse()
                return response.status, json.loads(response.read())
            finally:
                connection.close()

        status, payload = _op("op-alpha")
        results["consequential_first"] = {"status": status, **payload}
        status, payload = _op("op-alpha")
        results["consequential_repeat"] = {"status": status, **payload}
        if not payload.get("duplicate"):
            self._fail(
                codes.DUPLICATE_CONSEQUENTIAL_OPERATION,
                "op-alpha",
                "repeated consequential operation executed twice",
            )

        cluster.stop()
        deadline = time.monotonic() + 30
        db_unready = False
        while time.monotonic() < deadline:
            status, _ = self.sup._probe_service("identity-runtime-shell", "/readyz")
            if status == 503:
                db_unready = True
                break
            time.sleep(0.5)
        live_status, _ = self.sup._probe_service("identity-runtime-shell", "/livez")
        results["db_outage"] = {
            "readiness_failed_closed": db_unready,
            "liveness_still_true": live_status == 200,
            "classification": "FAIL_CLOSED (readiness) / EXPLICIT_UNAVAILABLE (dependency)",
        }
        if not db_unready:
            self._fail(
                codes.READINESS_ALWAYS_TRUE,
                "identity-shell",
                "service stayed ready through a database outage",
            )
        if live_status != 200:
            self._fail(codes.HIDDEN_FAILURE_SUCCESS, "identity-shell", "liveness died with the DB")

        status, payload = _op("op-during-outage")
        results["consequential_during_outage"] = {"status": status, **payload}
        if status != 503:
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "op-during-outage",
                "consequential operation claimed success during the outage",
            )

        cluster.start()
        cluster.wait_ready(60)
        deadline = time.monotonic() + 45
        recovered = False
        while time.monotonic() < deadline:
            status, _ = self.sup._probe_service("identity-runtime-shell", "/readyz")
            if status == 200:
                recovered = True
                break
            time.sleep(0.5)
        results["recovery"] = {"ready_again_without_restart": recovered}
        if not recovered:
            self._fail(codes.HIDDEN_FAILURE_SUCCESS, "identity-shell", "no recovery after outage")

        status, payload = _op("op-during-outage")
        results["consequential_retry_after_recovery"] = {"status": status, **payload}
        if status != 200 or not payload.get("executed"):
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "op-retry",
                "safe retry after recovery did not execute exactly once",
            )
        status, payload = _op("op-during-outage")
        if not payload.get("duplicate"):
            self._fail(
                codes.DUPLICATE_CONSEQUENTIAL_OPERATION,
                "op-retry",
                "post-recovery retry executed the operation twice",
            )

        # DNS/network failure classification (§44)
        import os as _os

        env = dict(_os.environ)
        env["PGSSLMODE"] = "verify-full"
        env["PGCONNECT_TIMEOUT"] = "3"
        dns = subprocess.run(
            [str(PG_BINDIR / "psql"), "-h", "db.nonexistent.invalid", "-c", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False,
        )
        results["dns_failure"] = {
            "refused": dns.returncode != 0,
            "classification": "EXPLICIT_UNAVAILABLE",
        }
        if dns.returncode == 0:
            self._fail(codes.HIDDEN_FAILURE_SUCCESS, "dns", "unresolvable host reported success")
        return results

    def _service_authority(self, service: dict[str, Any]) -> TrustAuthority:
        return self.sup.authorities[
            "voting-ca" if service.get("network_segment") == "voting" else "application-ca"
        ]

    # -- health output privacy (§28) ---------------------------------------

    def health_privacy_scenarios(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        sensitive_markers = ("password", "dsn", "secret", "token", "/home/", "postgresql://")
        for name in sorted(self.sup.services):
            _, payload = self.sup._probe_service(name, "/healthz")
            text = json.dumps(payload).lower()
            leaks = [marker for marker in sensitive_markers if marker in text]
            results[name] = {"sensitive_markers_found": leaks}
            for marker in leaks:
                self._fail(
                    codes.SENSITIVE_HEALTH_OUTPUT,
                    name,
                    f"health output carries sensitive marker {marker!r}",
                )
        return results

    # -- graceful shutdown (§23/§30) ---------------------------------------

    def shutdown_scenarios(self) -> dict[str, Any]:
        managed = self.sup.services["membership-runtime-shell"]
        process = managed.process
        assert process is not None
        process.send_signal(signal.SIGTERM)
        unready_during_drain = False
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                status, _ = self.sup._probe_service("membership-runtime-shell", "/readyz")
            except (OSError, ssl.SSLError):
                break  # closed already
            if status == 503:
                unready_during_drain = True
                break
            time.sleep(0.2)
        try:
            exit_code = process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            exit_code = -1
        results = {
            "readiness_removed_before_exit": unready_during_drain,
            "exit_code": exit_code,
            "bounded": exit_code is not None,
        }
        if not unready_during_drain and exit_code != 0:
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "membership-shell-shutdown",
                "no drain signal observed and exit was not clean",
            )
        if exit_code != 0:
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "membership-shell-shutdown",
                f"graceful shutdown exited {exit_code}",
            )
        # bring it back for the remaining scenarios
        self.sup._restart_service("membership-runtime-shell")
        unready = self.sup.wait_all_ready(60)
        if unready:
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "membership-shell-restart",
                f"restart after shutdown drill did not converge: {sorted(unready)}",
            )
        return results

    # -- voting isolation (§20, §39) + observability privacy (§33, §38) ----

    def voting_isolation_scenarios(self) -> dict[str, Any]:
        voting = self.sup.services["voting-runtime-shell"]
        voting_ca = self._voting_ca()
        cert, key = self._client_pair(voting_ca, "voting-scenario-client")
        results: dict[str, Any] = {}

        status, _ = probe(
            voting.port,
            "/healthz",
            voting_ca.cert_path,
            client_cert=cert,
            client_key=key,
            server_hostname="voting-runtime-shell",
        )
        results["clean_request_served"] = {"status": status, "ok": status == 200}
        if status != 200:
            self._fail(codes.TRUST_MATERIAL_INVALID, "voting-shell", "voting shell unreachable")

        refusals: dict[str, bool] = {}
        for header in ("X-Member-Id", "X-Session-Id", "X-Correlation-Id", "X-Person-Id"):
            context = ssl.create_default_context(cafile=str(voting_ca.cert_path))
            context.load_cert_chain(str(cert), str(key))
            raw = context.wrap_socket(
                socket.create_connection(("127.0.0.1", voting.port), timeout=10),
                server_hostname="voting-runtime-shell",
            )
            connection = http.client.HTTPSConnection("127.0.0.1", context=context)
            connection.sock = raw
            try:
                connection.request("GET", "/healthz", headers={header: "member-123456"})
                response = connection.getresponse()
                response.read()
                refusals[header] = response.status == 403
                if response.status != 403:
                    self._fail(
                        codes.VOTING_PERSON_ID_LEAK,
                        header,
                        "identity/correlation header crossed the voting boundary",
                    )
            finally:
                connection.close()
        results["identity_headers_refused"] = refusals

        app_cert, app_key = self._client_pair(self._app_ca(), "scenario-client")
        results["application_ca_client_refused"] = self._expect_refusal(
            "voting-shell-app-ca-client",
            codes.SHARED_VOTING_OBSERVABILITY,
            lambda: probe(
                voting.port,
                "/healthz",
                voting_ca.cert_path,
                client_cert=app_cert,
                client_key=app_key,
                server_hostname="voting-runtime-shell",
            ),
            "an application-CA identity was accepted inside the voting segment",
        )

        collected = self.sup.instance.log_dir / "collected.log"
        collected_text = collected.read_text(encoding="utf-8") if collected.is_file() else ""
        voting_in_shared = '"service": "voting-runtime-shell"' in collected_text or (
            "voting-runtime-shell" in collected_text
        )
        results["voting_absent_from_shared_observability"] = not voting_in_shared
        if voting_in_shared:
            self._fail(
                codes.SHARED_VOTING_OBSERVABILITY,
                "collected.log",
                "voting-domain telemetry reached the shared collector",
            )
        return results

    def observability_scenarios(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        secret_probe = "supersecret-token-a1b2c3d4e5"
        import contextlib

        with contextlib.suppress(OSError, ssl.SSLError):
            self.sup._probe_service("identity-runtime-shell", f"/healthz?token={secret_probe}")
        time.sleep(1.0)
        scan_targets = [self.sup.instance.log_dir]
        leaked: list[str] = []
        for target in scan_targets:
            for path in sorted(p for p in target.rglob("*") if p.is_file()):
                if secret_probe in path.read_text(encoding="utf-8", errors="replace"):
                    leaked.append(str(path))
        results["query_secret_redacted_in_logs"] = {"leaked_in": leaked, "ok": not leaked}
        for leak_path in leaked:
            self._fail(
                codes.OBSERVABILITY_PRIVACY_VIOLATION, leak_path, "sensitive query material logged"
            )

        assert self.sup.secrets is not None
        secret_findings = self.sup.secrets.scan_for_leaks(
            [self.sup.instance.log_dir, self.sup.instance.config_dir, self.root / "validation"]
        )
        results["generated_secret_leak_scan"] = {
            "findings": [f.describe() for f in secret_findings]
        }
        self.findings.extend(f.describe() for f in secret_findings)

        collector = self.sup.services["observability-collector"].process
        assert collector is not None
        collector.send_signal(signal.SIGTERM)
        collector.wait(timeout=15)
        status, _ = self.sup._probe_service("identity-runtime-shell", "/readyz")
        results["collector_outage"] = {
            "application_still_ready": status == 200,
            "classification": "EXPLICIT_UNAVAILABLE (collector) / SAFE_RETRY (producers)",
        }
        if status != 200:
            self._fail(
                codes.HIDDEN_FAILURE_SUCCESS,
                "observability-outage",
                "an observability outage took application readiness down",
            )
        self.sup._restart_service("observability-collector")
        self.sup.wait_all_ready(60)
        return results

    # -- resource boundaries (§35) -----------------------------------------

    def resource_scenarios(self) -> dict[str, Any]:
        import resource as _resource

        declared = {
            name: service.get("resources")
            for name, service in self.sup.topology["services"].items()
        }
        undeclared = [name for name, resources in declared.items() if not resources]
        for name in undeclared:
            self._fail(codes.RESOURCE_BOUNDARY_UNDECLARED, name, "no resource profile declared")

        def _limited() -> None:
            limit = 48 * 1024 * 1024
            _resource.setrlimit(_resource.RLIMIT_AS, (limit, limit))

        constrained = subprocess.run(
            [sys.executable, "-c", "data = bytearray(256 * 1024 * 1024); print('allocated')"],
            capture_output=True,
            text=True,
            timeout=60,
            preexec_fn=_limited,
            check=False,
        )
        contained = constrained.returncode != 0 and "allocated" not in constrained.stdout
        if not contained:
            self._fail(
                codes.RESOURCE_BOUNDARY_UNDECLARED,
                "constrained-scenario",
                "the resource limit did not contain the over-allocation",
            )
        return {
            "declared_profiles": declared,
            "constrained_scenario": {
                "limit_bytes": 48 * 1024 * 1024,
                "attempted_bytes": 256 * 1024 * 1024,
                "contained": contained,
                "exit_code": constrained.returncode,
            },
        }

    # -- drift (§40) --------------------------------------------------------

    def drift_scenarios(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        clean = self.sup.drift_scan()
        results["clean_scan_findings"] = [f.describe() for f in clean]
        if clean:
            self._fail(codes.DRIFT_IGNORED, "clean-scan", "false drift on a truthful runtime")

        rogue = socket.socket()
        rogue.bind(("127.0.0.1", 8490))
        rogue.listen(1)
        try:
            with_rogue = self.sup.drift_scan()
            detected = any(f.code == codes.UNDECLARED_SERVICE for f in with_rogue)
            results["undeclared_service_detected"] = detected
            if not detected:
                self._fail(
                    codes.DRIFT_IGNORED, "rogue-listener", "undeclared listener not detected"
                )
        finally:
            rogue.close()
        return results

    # -- redeploy (§41) -----------------------------------------------------

    def redeploy_scenarios(self, artifact_zip: Path) -> dict[str, Any]:
        digest_before = self.sup.release_digest
        findings = self.sup.redeploy(artifact_zip)
        self.findings.extend(f.describe() for f in findings)
        mismatch = self.sup.redeploy(Path("/nonexistent-artifact.zip"))
        refused = any(f.code == codes.ARTIFACT_DIGEST_MISMATCH for f in mismatch)
        if not refused:
            self._fail(
                codes.NON_IDEMPOTENT_REDEPLOY,
                "foreign-artifact",
                "redeploy accepted a non-identical artifact",
            )
        return {
            "same_release_redeploy_findings": [f.describe() for f in findings],
            "release_digest_stable": self.sup.release_digest == digest_before,
            "foreign_artifact_refused": refused,
        }

    # -- rollback safety (§42) ----------------------------------------------

    def rollback_scenarios(self) -> dict[str, Any]:
        migrations_dir = self.sup.instance.deploy_dir / "services/identity-service/migrations"
        current_set = sorted(p.name for p in migrations_dir.glob("*.sql"))
        allowed = self.sup.rollback_check(self.sup.release_digest, current_set)
        schema_unsafe = self.sup.rollback_check(self.sup.release_digest, current_set[:-1])
        unknown = self.sup.rollback_check("0" * 64, current_set)
        if allowed:
            self._fail(
                codes.UNSAFE_ROLLBACK,
                "same-release",
                "rollback to the verified deployed release was refused",
            )
        if not any(f.code == codes.UNSAFE_ROLLBACK for f in schema_unsafe):
            self._fail(
                codes.UNSAFE_ROLLBACK,
                "schema-safety",
                "rollback past applied migrations was not refused",
            )
        if not any(f.code == codes.UNSAFE_ROLLBACK for f in unknown):
            self._fail(
                codes.UNSAFE_ROLLBACK,
                "unknown-target",
                "rollback to a never-verified release was not refused",
            )
        return {
            "rollback_to_verified_release_allowed": not allowed,
            "schema_unsafe_rollback_refused": [f.describe() for f in schema_unsafe],
            "unknown_target_refused": [f.describe() for f in unknown],
        }

    # -- seed / reset (§34) --------------------------------------------------

    def seed_reset_scenarios(self) -> dict[str, Any]:
        cluster = self.sup.cluster
        secrets = self.sup.secrets
        assert cluster is not None and secrets is not None
        password = secrets.value("db-password/rt_identity")
        results: dict[str, Any] = {}

        fixture = self.root / FIXTURE_FILE
        import os as _os

        env = dict(_os.environ)
        env["PGPASSWORD"] = password
        env["PGSSLMODE"] = "verify-full"
        env["PGSSLROOTCERT"] = str(cluster.ca_cert)
        subprocess.run(
            [
                str(PG_BINDIR / "psql"),
                "-h",
                "localhost",
                "-p",
                str(cluster.port),
                "-U",
                "rt_identity",
                "-d",
                "epd2_identity",
                "-v",
                "ON_ERROR_STOP=1",
                "-q",
                "-f",
                str(fixture),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            check=True,
        )
        seeded = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT count(*) FROM account_registry_record "
            "WHERE account_id LIKE 'preview-fixture-%'",
        ).stdout.strip()
        results["fixtures_seeded"] = {"fixture_rows": seeded}

        cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "INSERT INTO account_registry_record (account_id, account_status, scope_level, "
            "scope_unit_id, created_at, anonymization_state, version, document) VALUES "
            "('preview-stale-marker', 'active', 'federal', 'u', 'now', 'none', 1, '{}') "
            "ON CONFLICT (account_id) DO NOTHING",
        )

        # Reset: drop and rebuild the database deterministically.
        cluster.admin_sql("DROP DATABASE epd2_identity WITH (FORCE)")
        cluster.admin_sql("CREATE DATABASE epd2_identity OWNER rt_identity")
        cluster.admin_sql("REVOKE CONNECT ON DATABASE epd2_identity FROM PUBLIC")
        cluster.admin_sql("GRANT CONNECT ON DATABASE epd2_identity TO rt_identity")
        migrations = self.sup.instance.deploy_dir / "services/identity-service/migrations"
        applied, migration_findings = cluster.apply_migrations(
            "epd2_identity", migrations, role="rt_identity"
        )
        self.findings.extend(f.describe() for f in migration_findings)
        stale = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT count(*) FROM account_registry_record "
            "WHERE account_id IN ('preview-stale-marker', 'preview-persistence-proof') "
            "OR account_id LIKE 'preview-fixture-%'",
        ).stdout.strip()
        results["reset"] = {
            "migrations_reapplied": len(applied),
            "stale_rows_after_reset": stale,
            "old_state_proven_gone": stale == "0",
        }
        if stale != "0":
            self._fail(
                codes.STALE_STATE_AFTER_RESET,
                "epd2_identity",
                f"{stale} pre-reset row(s) survived the reset",
            )
        subprocess.run(
            [
                str(PG_BINDIR / "psql"),
                "-h",
                "localhost",
                "-p",
                str(cluster.port),
                "-U",
                "rt_identity",
                "-d",
                "epd2_identity",
                "-v",
                "ON_ERROR_STOP=1",
                "-q",
                "-f",
                str(fixture),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            check=True,
        )
        reseeded = cluster.client_sql(
            "rt_identity",
            password,
            "epd2_identity",
            "SELECT count(*) FROM account_registry_record "
            "WHERE account_id LIKE 'preview-fixture-%'",
        ).stdout.strip()
        results["deterministic_reseed"] = {
            "fixture_rows": reseeded,
            "deterministic": reseeded == seeded,
        }
        return results

    # -- environment isolation / destroy safety (§46, §47) -------------------

    def isolation_scenarios(self) -> dict[str, Any]:
        marker = json.loads(self.sup.instance.marker.read_text(encoding="utf-8"))
        refused_production = self.sup.verify_destroy_target("production", marker["instance_id"])
        refused_foreign = self.sup.verify_destroy_target("preview", "preview-not-this-instance")
        allowed = self.sup.verify_destroy_target(marker["environment"], marker["instance_id"])
        if not any(f.code == codes.AMBIGUOUS_DESTRUCTIVE_TARGET for f in refused_production):
            self._fail(
                codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                "production-target",
                "production-like destroy target was not refused",
            )
        if not any(f.code == codes.AMBIGUOUS_DESTRUCTIVE_TARGET for f in refused_foreign):
            self._fail(
                codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                "foreign-instance",
                "destroy of a non-matching instance id was not refused",
            )
        if allowed:
            self._fail(
                codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                "exact-target",
                "destroy of the exact running instance was refused",
            )
        config_text = "".join(
            p.read_text(encoding="utf-8") for p in self.sup.instance.config_dir.glob("*.json")
        )
        production_markers = [
            marker_text
            for marker_text in ("prod.", "production", ".live.", "amqps://prod")
            if marker_text in config_text.lower()
        ]
        for marker_text in production_markers:
            self._fail(
                codes.ENVIRONMENT_ISOLATION_BREACH,
                marker_text,
                "preview configuration references production-like resources",
            )
        return {
            "production_destroy_refused": [f.describe() for f in refused_production],
            "foreign_instance_destroy_refused": [f.describe() for f in refused_foreign],
            "exact_target_destroy_allowed": not allowed,
            "production_markers_in_config": production_markers,
        }
