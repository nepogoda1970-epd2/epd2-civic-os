"""Preview deployment supervisor (INFRA03 §32, §40..§47).

Deploys exactly what ``infra/runtime/topology.yaml`` declares into one
isolated preview instance directory: verifies the approved artifact digest,
provisions per-deployment trust and secrets, initializes the real
PostgreSQL cluster, renders per-service configuration, starts the runtime
shells with resource limits and restart accounting, waits for truthful
readiness, probes every service, and provides drift scanning, idempotent
redeploy, bounded safe rollback and destructive-action safety.

A failed deploy returns non-zero, emits evidence, never claims readiness
and leaves a stopped, known state (§43). Destroy/reset requires the explicit
target identity of the running instance and refuses ambiguous or
production-like targets (§47).
"""

from __future__ import annotations

import http.client
import json
import resource
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.acceptance.canonical import sha256_file
from scripts.infra03 import PREDECESSOR, codes
from scripts.infra03.artifacts import deploy_artifact
from scripts.infra03.postgres import PostgresCluster
from scripts.infra03.secrets import SecretStore, write_secret_inventory
from scripts.infra03.topology import validate_topology
from scripts.infra03.trust import TrustAuthority, provision_trust

SHELL_PORT_RANGE = range(8400, 8500)


@dataclass(frozen=True)
class SupervisorFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


@dataclass
class ManagedService:
    name: str
    port: int
    config_path: Path
    process: subprocess.Popen[bytes] | None = None
    restart_count: int = 0
    restart_reasons: list[str] = field(default_factory=list)
    failed: bool = False


class PreviewInstance:
    """Filesystem layout and identity marker of one preview instance."""

    def __init__(self, instance_dir: Path, environment: str = "preview") -> None:
        self.instance_dir = instance_dir
        self.environment = environment
        self.instance_id = f"{environment}-{uuid.uuid4().hex[:12]}"
        self.deploy_dir = instance_dir / "deploy" / "current"
        self.trust_dir = instance_dir / "trust"
        self.secret_dir = instance_dir / "secrets"
        self.config_dir = instance_dir / "config"
        self.log_dir = instance_dir / "logs"
        self.marker = instance_dir / "instance.json"

    def write_marker(self, release_digest: str) -> None:
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        self.marker.write_text(
            json.dumps(
                {
                    "schema": "epd2.infra03.instance/1",
                    "environment": self.environment,
                    "instance_id": self.instance_id,
                    "release_digest": release_digest,
                    "created_at": time.time(),
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def probe(
    port: int,
    path: str,
    ca_file: Path,
    client_cert: Path | None = None,
    client_key: Path | None = None,
    server_hostname: str = "localhost",
    timeout: float = 5.0,
) -> tuple[int, dict[str, Any]]:
    """One TLS/mTLS probe against a runtime endpoint."""
    context = ssl.create_default_context(cafile=str(ca_file))
    if client_cert is not None and client_key is not None:
        context.load_cert_chain(str(client_cert), str(client_key))
    raw = context.wrap_socket(
        socket.create_connection(("127.0.0.1", port), timeout=timeout),
        server_hostname=server_hostname,
    )
    connection = http.client.HTTPSConnection("127.0.0.1", context=context, timeout=timeout)
    connection.sock = raw
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body.decode("utf-8", errors="replace")[:200]}
        return response.status, payload
    finally:
        connection.close()


class Supervisor:
    """Deploys and operates one preview instance."""

    def __init__(self, repo_root: Path, instance: PreviewInstance) -> None:
        self.repo_root = repo_root
        self.instance = instance
        self.services: dict[str, ManagedService] = {}
        self.authorities: dict[str, TrustAuthority] = {}
        self.secrets: SecretStore | None = None
        self.cluster: PostgresCluster | None = None
        self.topology: dict[str, Any] = {}
        self.release_digest: str = ""
        self._monitors_stop = threading.Event()

    # -- deployment --------------------------------------------------------

    def deploy(
        self,
        topology: dict[str, Any],
        artifact_zip: Path,
        readiness_timeout: float = 90.0,
    ) -> tuple[dict[str, Any], list[SupervisorFinding]]:
        """The canonical deterministic deploy path. Returns (evidence, findings).

        Any unexpected internal error is converted into a fail-closed finding
        with the runtime stopped — a failed deploy never claims success and
        never leaves an unsafe partial state (§43).
        """
        evidence: dict[str, Any] = {"steps": []}
        findings: list[SupervisorFinding] = []
        self.topology = topology
        try:
            return self._deploy_inner(topology, artifact_zip, readiness_timeout, evidence, findings)
        except Exception as error:
            findings.append(
                SupervisorFinding(
                    codes.HIDDEN_FAILURE_SUCCESS,
                    "deploy",
                    f"internal deployment error, runtime stopped: {error!r}"[:300],
                )
            )
            self.stop_all()
            return evidence, findings

    def _deploy_inner(
        self,
        topology: dict[str, Any],
        artifact_zip: Path,
        readiness_timeout: float,
        evidence: dict[str, Any],
        findings: list[SupervisorFinding],
    ) -> tuple[dict[str, Any], list[SupervisorFinding]]:

        def step(name: str, ok: bool, detail: str = "") -> None:
            evidence["steps"].append({"step": name, "ok": ok, "detail": detail})

        lint = validate_topology(topology)
        if lint:
            for item in lint:
                findings.append(SupervisorFinding(item.code, item.subject, item.detail))
            step("topology-lint", False, f"{len(lint)} finding(s)")
            return evidence, findings
        step("topology-lint", True)

        digest, artifact_findings = deploy_artifact(artifact_zip, self.instance.deploy_dir)
        if artifact_findings:
            findings.extend(
                SupervisorFinding(f.code, f.subject, f.detail) for f in artifact_findings
            )
            step("artifact-identity", False)
            return evidence, findings
        self.release_digest = digest
        self.instance.write_marker(digest)
        step("artifact-identity", True, f"deployed tree digest {digest}")

        self.authorities = provision_trust(self.instance.trust_dir)
        step("trust-provisioned", True, "application-ca, data-ca, voting-ca")
        self.secrets = SecretStore(self.instance.secret_dir)

        services = topology["services"]
        pg_service = services.get("postgres-preview", {})
        pg_port = int(pg_service.get("ports", {}).get("tls", 8432))
        data_ca = self.authorities["data-ca"]
        pg_cert, pg_key = data_ca.issue("postgres-preview", "server", ("localhost",))
        self.cluster = PostgresCluster(self.instance.instance_dir, pg_port)
        self.cluster.init(pg_cert, pg_key, data_ca.cert_path)
        self.cluster.start()
        if not self.cluster.wait_ready(60):
            findings.append(
                SupervisorFinding(
                    codes.HIDDEN_FAILURE_SUCCESS, "postgres-preview", "cluster never became ready"
                )
            )
            step("postgres", False)
            self.stop_all()
            return evidence, findings
        version = self.cluster.admin_sql("SHOW server_version").strip()
        step("postgres", True, f"PostgreSQL {version} on port {pg_port}")

        databases: dict[str, tuple[str, str]] = {}
        for name, service in services.items():
            database = service.get("database")
            if not database:
                continue
            role, dbname = str(database["role"]), str(database["name"])
            password = self.secrets.generate(f"db-password/{role}", "db-credential")
            self.cluster.create_role_and_database(role, password, dbname)
            databases[name] = (role, dbname)
        write_secret_inventory(self.secrets, self.instance.instance_dir / "secret_inventory.json")
        step("databases", True, ", ".join(sorted(db for _, db in databases.values())))

        if any(dbname == "epd2_identity" for _, dbname in databases.values()):
            migrations = self.instance.deploy_dir / "services/identity-service/migrations"
            applied, migration_findings = self.cluster.apply_migrations(
                "epd2_identity", migrations, role="rt_identity"
            )
            findings.extend(
                SupervisorFinding(f.code, f.subject, f.detail) for f in migration_findings
            )
            step("migrations", not migration_findings, f"epd2_identity: {len(applied)} applied")
            if migration_findings:
                self.stop_all()
                return evidence, findings

        for name, service in services.items():
            if name == "postgres-preview":
                continue
            self._start_shell(name, service, databases.get(name))
        step("services-started", True, ", ".join(sorted(self.services)))

        unready = self.wait_all_ready(timeout_seconds=readiness_timeout)
        if unready:
            findings.append(
                SupervisorFinding(
                    codes.PARTIAL_UNSAFE_EXPOSURE,
                    ",".join(sorted(unready)),
                    "deployment did not reach readiness; the deploy fails, claims "
                    "nothing, and stops the partial runtime",
                )
            )
            step("readiness", False, f"unready: {sorted(unready)}")
            self.stop_all()
            return evidence, findings
        step("readiness", True, "every declared service is ready")
        evidence["release_digest"] = digest
        evidence["instance_id"] = self.instance.instance_id
        return evidence, findings

    def _service_ca(self, service: dict[str, Any]) -> TrustAuthority:
        return self.authorities[
            "voting-ca" if service.get("network_segment") == "voting" else "application-ca"
        ]

    def _start_shell(
        self, name: str, service: dict[str, Any], database: tuple[str, str] | None
    ) -> None:
        assert self.secrets is not None and self.cluster is not None
        authority = self._service_ca(service)
        server_cert, server_key = authority.issue(name, "server", ("localhost",))
        client_cert, client_key = authority.issue(name, "client", ("localhost",))
        port = int(next(iter(service.get("ports", {}).values())))
        self.instance.config_dir.mkdir(parents=True, exist_ok=True)
        self.instance.log_dir.mkdir(parents=True, exist_ok=True)
        config: dict[str, Any] = {
            "service_id": name,
            "network_segment": service.get("network_segment"),
            "environment": self.instance.environment,
            "instance_id": self.instance.instance_id,
            "app_root": str(self.instance.deploy_dir),
            "listen_port": port,
            "server_cert": str(server_cert),
            "server_key": str(server_key),
            "client_cert": str(client_cert),
            "client_key": str(client_key),
            "trust_ca": str(authority.cert_path),
            "mtls_required": "true" if service.get("network_segment") != "public" else "false",
            "expected_app_digest": PREDECESSOR["freeze_tree_digest"],
            "voting_domain": "true" if service.get("voting_domain") else "false",
            "log_file": str(self.instance.log_dir / f"{name}.log"),
            "shutdown_grace_seconds": (service.get("shutdown") or {}).get("grace_seconds", 10),
        }
        if database is not None:
            role, dbname = database
            config["db_dsn"] = (
                f"postgresql://{role}@localhost:{self.cluster.port}/{dbname}?sslmode=verify-full"
            )
            config["db_password_file"] = str(self.instance.secret_dir / f"db-password__{role}")
            config["db_ca"] = str(self.authorities["data-ca"].cert_path)
        if service.get("network_segment") == "application":
            obs_port = (
                self.topology["services"]
                .get("observability-collector", {})
                .get("ports", {})
                .get("mtls")
            )
            if obs_port:
                config["observability_endpoint"] = f"observability-collector:{obs_port}"
                config["observability_client_cert"] = str(client_cert)
                config["observability_client_key"] = str(client_key)
        if name == "ingress-gateway":
            config["ingress_routes"] = {
                "/identity-shell": {"workload": "identity-runtime-shell", "port": 8451},
                "/membership-shell": {"workload": "membership-runtime-shell", "port": 8452},
            }
            config["max_body_bytes"] = (
                (service.get("ingress") or {})
                .get("request_limits", {})
                .get("max_body_bytes", 1048576)
            )
        if name == "observability-collector":
            config["collector_sink"] = str(self.instance.log_dir / "collected.log")

        config_path = self.instance.config_dir / f"{name}.json"
        config_path.write_text(json.dumps(config, indent=1, sort_keys=True), encoding="utf-8")
        managed = ManagedService(name=name, port=port, config_path=config_path)
        self.services[name] = managed
        self._spawn(managed, service)
        threading.Thread(
            target=self._monitor, args=(managed, service), daemon=True, name=f"monitor-{name}"
        ).start()

    def _spawn(self, managed: ManagedService, service: dict[str, Any]) -> None:
        resources = service.get("resources") or {}
        memory_bytes = int(resources.get("memory_bytes", 0)) or None

        def limits() -> None:
            if memory_bytes:
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

        managed.process = subprocess.Popen(
            [sys.executable, "-m", "scripts.infra03.service", "--config", str(managed.config_path)],
            cwd=self.repo_root,
            stdout=(self.instance.log_dir / f"{managed.name}.out").open("ab"),
            stderr=subprocess.STDOUT,
            preexec_fn=limits,
        )

    def _monitor(self, managed: ManagedService, service: dict[str, Any]) -> None:
        """Restart accounting (§31): a crash-looping service is FAILED and
        never reported healthy; every restart records its reason."""
        policy = service.get("restart_policy") or {}
        max_restarts = int(policy.get("max_restarts", 3))
        backoff = float(policy.get("backoff_seconds", 2))
        while not self._monitors_stop.is_set():
            process = managed.process
            if process is None:
                return
            code = process.poll()
            if code is None:
                time.sleep(0.3)
                continue
            if self._monitors_stop.is_set() or code == 0:
                return
            managed.restart_reasons.append(f"exit code {code}")
            if managed.restart_count >= max_restarts:
                managed.failed = True
                return
            managed.restart_count += 1
            time.sleep(backoff)
            self._spawn(managed, service)

    # -- readiness / probes ------------------------------------------------

    def _probe_service(self, name: str, path: str) -> tuple[int, dict[str, Any]]:
        service = self.topology["services"][name]
        authority = self._service_ca(service)
        managed = self.services[name]
        needs_client = service.get("network_segment") != "public"
        supervisor_cert = authority.directory / "client-supervisor-probe.crt"
        if needs_client and not supervisor_cert.is_file():
            authority.issue("supervisor-probe", "client", ("localhost",))
        return probe(
            managed.port,
            path,
            authority.cert_path,
            client_cert=(authority.directory / "client-supervisor-probe.crt")
            if needs_client
            else None,
            client_key=(authority.directory / "client-supervisor-probe.key")
            if needs_client
            else None,
            server_hostname=name,
        )

    def wait_all_ready(self, timeout_seconds: float = 60.0) -> set[str]:
        deadline = time.monotonic() + timeout_seconds
        pending = {name for name in self.services}
        while pending and time.monotonic() < deadline:
            for name in sorted(pending):
                if self.services[name].failed:
                    continue
                try:
                    status, _ = self._probe_service(name, "/readyz")
                except (OSError, ssl.SSLError):
                    continue
                if status == 200:
                    pending.discard(name)
            time.sleep(0.5)
        return pending | {n for n, s in self.services.items() if s.failed}

    # -- drift (§40) -------------------------------------------------------

    def _listening_ports(self) -> set[int]:
        ports: set[int] = set()
        for table in ("/proc/net/tcp", "/proc/net/tcp6"):
            try:
                lines = Path(table).read_text().splitlines()[1:]
            except OSError:
                continue
            for line in lines:
                parts = line.split()
                if len(parts) > 3 and parts[3] == "0A":  # LISTEN
                    ports.add(int(parts[1].rsplit(":", 1)[1], 16))
        return ports

    def drift_scan(self) -> list[SupervisorFinding]:
        findings: list[SupervisorFinding] = []
        declared_ports = {managed.port for managed in self.services.values()}
        if self.cluster is not None:
            declared_ports.add(self.cluster.port)
        listening = self._listening_ports()
        for port in sorted(p for p in SHELL_PORT_RANGE if p in listening):
            if port not in declared_ports:
                findings.append(
                    SupervisorFinding(
                        codes.UNDECLARED_SERVICE,
                        f"port {port}",
                        "something undeclared is listening inside the runtime port range",
                    )
                )
        for name, managed in sorted(self.services.items()):
            process = managed.process
            if managed.failed or process is None or process.poll() is not None:
                findings.append(
                    SupervisorFinding(
                        codes.UNDECLARED_SERVICE, name, "declared service not running"
                    )
                )
                continue
            if managed.port not in listening:
                findings.append(
                    SupervisorFinding(
                        codes.WRONG_NETWORK_SEGMENT, name, f"declared port {managed.port} not bound"
                    )
                )
            try:
                _, payload = self._probe_service(name, "/identity")
            except (OSError, ssl.SSLError) as error:
                findings.append(
                    SupervisorFinding(codes.DRIFT_IGNORED, name, f"identity unobservable: {error}")
                )
                continue
            observed = str(payload.get("observed_app_digest") or "")
            if observed and observed != self.release_digest:
                findings.append(
                    SupervisorFinding(
                        codes.ARTIFACT_DIGEST_MISMATCH,
                        name,
                        f"observed runtime digest {observed} differs from deployed "
                        f"{self.release_digest}",
                    )
                )
        return findings

    # -- redeploy / rollback (§41, §42) ------------------------------------

    def redeploy(self, artifact_zip: Path) -> list[SupervisorFinding]:
        """Idempotent redeploy of the exact same release."""
        digest_before = self.release_digest
        if not artifact_zip.is_file():
            return [
                SupervisorFinding(
                    codes.ARTIFACT_DIGEST_MISMATCH,
                    artifact_zip.name,
                    "redeploy artifact absent; nothing verified to redeploy",
                )
            ]
        actual = sha256_file(artifact_zip)
        if actual != PREDECESSOR["zip_sha256"]:
            return [
                SupervisorFinding(
                    codes.ARTIFACT_DIGEST_MISMATCH,
                    artifact_zip.name,
                    "redeploy artifact is not the deployed release",
                )
            ]
        for name in sorted(self.services):
            self._restart_service(name)
        unready = self.wait_all_ready(90)
        findings: list[SupervisorFinding] = []
        if unready:
            findings.append(
                SupervisorFinding(
                    codes.NON_IDEMPOTENT_REDEPLOY,
                    ",".join(sorted(unready)),
                    "redeploy of the identical release did not converge to ready",
                )
            )
        if self.release_digest != digest_before:
            findings.append(
                SupervisorFinding(
                    codes.NON_IDEMPOTENT_REDEPLOY,
                    "release_digest",
                    "redeploy changed the release identity",
                )
            )
        return findings

    def _restart_service(self, name: str) -> None:
        managed = self.services[name]
        process = managed.process
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        self._spawn(managed, self.topology["services"][name])

    def rollback_check(
        self, target_release_digest: str, target_migrations: list[str]
    ) -> list[SupervisorFinding]:
        """Bounded rollback safety (§42): the rollback target must be a
        previously verified release and must not require discarding applied
        schema history."""
        findings: list[SupervisorFinding] = []
        if target_release_digest != self.release_digest:
            findings.append(
                SupervisorFinding(
                    codes.UNSAFE_ROLLBACK,
                    target_release_digest[:16],
                    "rollback target was never verified/deployed in this instance",
                )
            )
            return findings
        assert self.cluster is not None
        applied = [
            line
            for line in self.cluster.admin_sql(
                "SELECT filename FROM infra03_migration_ledger ORDER BY filename",
                database="epd2_identity",
            ).splitlines()
            if line.strip()
        ]
        missing = sorted(set(applied) - set(target_migrations))
        if missing:
            findings.append(
                SupervisorFinding(
                    codes.UNSAFE_ROLLBACK,
                    ",".join(missing[:3]),
                    "rollback target does not carry migrations already applied to the "
                    "database; schema safety refuses the rollback",
                )
            )
        return findings

    # -- destroy / reset safety (§47) --------------------------------------

    def verify_destroy_target(self, environment: str, instance_id: str) -> list[SupervisorFinding]:
        findings: list[SupervisorFinding] = []
        lowered = f"{environment} {instance_id}".lower()
        if any(marker in lowered for marker in ("prod", "live", "production")):
            findings.append(
                SupervisorFinding(
                    codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                    environment,
                    "production-like destroy target refused",
                )
            )
        if not self.instance.marker.is_file():
            findings.append(
                SupervisorFinding(
                    codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                    instance_id,
                    "no instance marker; refusing to destroy an unidentified target",
                )
            )
            return findings
        marker = json.loads(self.instance.marker.read_text(encoding="utf-8"))
        if marker.get("environment") != environment or marker.get("instance_id") != instance_id:
            findings.append(
                SupervisorFinding(
                    codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
                    instance_id,
                    "destroy target does not match the running instance identity",
                )
            )
        return findings

    def destroy(self, environment: str, instance_id: str) -> list[SupervisorFinding]:
        findings = self.verify_destroy_target(environment, instance_id)
        if findings:
            return findings
        self.stop_all()
        return []

    def stop_all(self) -> None:
        self._monitors_stop.set()
        for managed in self.services.values():
            process = managed.process
            if process is not None and process.poll() is None:
                process.send_signal(signal.SIGTERM)
        for managed in self.services.values():
            process = managed.process
            if process is not None:
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
        if self.cluster is not None:
            self.cluster.stop()


def new_instance(base_dir: Path, environment: str = "preview") -> PreviewInstance:
    instance_dir = base_dir / f"instance-{uuid.uuid4().hex[:8]}"
    return PreviewInstance(instance_dir, environment)


def stale_state_check(instance_dir: Path) -> list[SupervisorFinding]:
    """Clean-room precondition (§33): a deploy must not inherit leftovers."""
    if instance_dir.exists() and any(instance_dir.iterdir()):
        return [
            SupervisorFinding(
                codes.CLEAN_ROOM_VIOLATION,
                str(instance_dir),
                "instance directory is not empty; clean-room deployment refuses "
                "developer leftovers",
            )
        ]
    return []
