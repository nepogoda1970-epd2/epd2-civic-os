"""INFRA-03 mutation/adversarial suite (assignment §60, §61).

Thirty-six corruption classes, each detected by its own distinct ``I03_*``
detector. Trust-material classes are proven with *real* TLS handshakes
against in-process servers; artifact classes with real ZIP bytes; runtime
policy classes against the same validators and evaluators the live gates
execute. A closing test proves the 36 classes map onto 36 distinct codes.
"""

from __future__ import annotations

import http.client
import json
import socket
import ssl
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from scripts.infra03 import codes, evaluators
from scripts.infra03.artifacts import (
    deploy_artifact,
    verify_approved_artifact,
    verify_predecessor_record,
)
from scripts.infra03.mutations import MUTATION_DETECTORS
from scripts.infra03.secrets import SecretStore, scan_manifest_for_secrets
from scripts.infra03.supervisor import PreviewInstance, Supervisor
from scripts.infra03.topology import (
    validate_flow_inventory,
    validate_topology,
)
from scripts.infra03.trust import TrustAuthority, verify_trust_layout

REPO_ROOT = Path(__file__).resolve().parents[2]


def _codes_of(findings: list[Any]) -> set[str]:
    return {str(f).split(":", 1)[0] if isinstance(f, str) else f.code for f in findings}


# -- topology fixture -------------------------------------------------------


def _mini_topology(**service_overrides: Any) -> dict[str, Any]:
    service: dict[str, Any] = {
        "role": "fixture",
        "artifact": "accepted",
        "network_segment": "application",
        "ports": {"mtls": 8451},
        "ingress": {"public_endpoint": False},
        "egress": [],
        "dependencies": [],
        "secrets": [],
        "config": [],
        "trust": {"trusts": ["application-ca"]},
        "probes": {"liveness": "/livez", "readiness": "/readyz"},
        "persistence": "ephemeral",
        "resources": {"cpu_shares": 1, "memory_bytes": 268435456},
        "restart_policy": {"mode": "on-failure", "max_restarts": 1},
        "shutdown": {"grace_seconds": 5},
        "voting_domain": False,
    }
    service.update(service_overrides)
    return {
        "schema": "epd2.infra03.topology/1",
        "environment": "preview",
        "artifacts": {
            "accepted": {
                "class": "accepted-candidate-archive",
                "filename": "EPD2_CANDIDATE.zip",
                "sha256": "d" * 64,
            }
        },
        "network_segments": {
            name: {"description": name}
            for name in (
                "public",
                "application",
                "data",
                "admin_ops",
                "voting",
                "observability",
            )
        },
        "services": {"fixture-service": service},
    }


def test_clean_mini_topology_is_valid() -> None:
    assert validate_topology(_mini_topology()) == []


# -- M01..M04: artifact identity -------------------------------------------


def test_m01_mutable_latest_reference_is_refused() -> None:
    topology = _mini_topology()
    topology["artifacts"]["accepted"]["filename"] = "epd2-civic-os:latest"
    findings = validate_topology(topology)
    assert codes.MUTABLE_ARTIFACT_REFERENCE in _codes_of(findings)


def test_m01b_missing_digest_pin_is_refused() -> None:
    topology = _mini_topology()
    topology["artifacts"]["accepted"]["sha256"] = "abc123"
    findings = validate_topology(topology)
    assert codes.MUTABLE_ARTIFACT_REFERENCE in _codes_of(findings)


def test_m02_wrong_artifact_digest_is_refused(tmp_path: Path) -> None:
    forged = tmp_path / "forged.zip"
    forged.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    findings = verify_approved_artifact(forged)
    assert codes.ARTIFACT_DIGEST_MISMATCH in _codes_of(findings)


def test_m03_local_rebuild_substitution_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rebuilt = tmp_path / "rebuilt.zip"
    with zipfile.ZipFile(rebuilt, "w") as bundle:
        bundle.writestr("ROOT/src/module.py", "VALUE = 'locally rebuilt'\n")
    from scripts.acceptance.canonical import sha256_file
    from scripts.infra03 import PREDECESSOR

    # The staged bytes hash correctly (attacker controls both), but the
    # extracted tree cannot reproduce the accepted freeze tree digest.
    monkeypatch.setitem(PREDECESSOR, "zip_sha256", sha256_file(rebuilt))
    monkeypatch.setitem(PREDECESSOR, "size_bytes", rebuilt.stat().st_size)
    _digest, findings = deploy_artifact(rebuilt, tmp_path / "deploy")
    assert codes.LOCAL_REBUILD_SUBSTITUTION in _codes_of(findings)


def test_m04_missing_handoff_artifact_is_refused(tmp_path: Path) -> None:
    findings = verify_approved_artifact(tmp_path / "absent.zip")
    assert codes.SUPPLY_CHAIN_HANDOFF_BYPASSED in _codes_of(findings)


# -- M05: undeclared service ------------------------------------------------


def test_m05_undeclared_listener_is_detected(tmp_path: Path) -> None:
    supervisor = Supervisor(REPO_ROOT, PreviewInstance(tmp_path / "instance"))
    rogue = socket.socket()
    rogue.bind(("127.0.0.1", 8493))
    rogue.listen(1)
    try:
        findings = supervisor.drift_scan()
        assert codes.UNDECLARED_SERVICE in {f.code for f in findings}
    finally:
        rogue.close()


# -- M06..M08: topology policy ----------------------------------------------


def test_m06_public_admin_port_is_refused() -> None:
    topology = _mini_topology(network_segment="admin_ops", ports={"admin": 9000})
    findings = validate_topology(topology)
    assert codes.ADMIN_ENDPOINT_PUBLIC in _codes_of(findings)


def test_m06b_public_endpoint_outside_public_segment_is_refused() -> None:
    topology = _mini_topology(ingress={"public_endpoint": True})
    findings = validate_topology(topology)
    assert codes.ADMIN_ENDPOINT_PUBLIC in _codes_of(findings)


def test_m07_wrong_segment_is_refused() -> None:
    topology = _mini_topology(network_segment="datacenter-x")
    findings = validate_topology(topology)
    assert codes.WRONG_NETWORK_SEGMENT in _codes_of(findings)


def test_m08_dependency_without_declared_flow_is_refused(tmp_path: Path) -> None:
    topology = _mini_topology(dependencies=["other-service"])
    topology["services"]["other-service"] = _mini_topology()["services"]["fixture-service"]
    inventory = tmp_path / "flows.json"
    inventory.write_text(
        json.dumps({"schema": "x", "default_policy": "DENY_UNDECLARED", "flows": []}),
        encoding="utf-8",
    )
    findings = validate_flow_inventory(tmp_path, topology, Path("flows.json"))
    assert codes.UNDECLARED_FLOW in _codes_of(findings)


# -- M09/M10: ingress hygiene ------------------------------------------------


def test_m09_surviving_forwarded_spoof_is_detected() -> None:
    findings = evaluators.check_forwarded({"x_forwarded_for": "6.6.6.6"}, "6.6.6.6")
    assert codes.FORWARDED_HEADER_UNTRUSTED in _codes_of(findings)
    assert evaluators.check_forwarded({"x_forwarded_for": "127.0.0.1"}, "6.6.6.6") == []


def test_m10_plaintext_fallback_is_detected() -> None:
    findings = evaluators.check_plaintext(served_plaintext=True, subject="ingress")
    assert codes.PLAINTEXT_FALLBACK_FORBIDDEN in _codes_of(findings)
    assert evaluators.check_plaintext(False, "ingress") == []


# -- M11..M15: real TLS handshake mutations ----------------------------------


class _TlsFixture:
    """A real TLS server with configurable trust for handshake mutations."""

    def __init__(
        self,
        tmp_path: Path,
        require_client_cert: bool = True,
        trust_ca: Path | None = None,
    ) -> None:
        self.authority = TrustAuthority("application-ca", tmp_path / "app-ca")
        self.foreign = TrustAuthority("voting-ca", tmp_path / "voting-ca")
        cert, key = self.authority.issue("identity-runtime-shell", "server", ("localhost",))

        class _H(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *_: Any) -> None:
                pass

        self.server = HTTPServer(("127.0.0.1", 0), _H)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        if require_client_cert:
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=str(trust_ca or self.authority.cert_path))
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def connect(
        self,
        ca: Path,
        server_hostname: str = "identity-runtime-shell",
        client_cert: tuple[Path, Path] | None = None,
        check_hostname: bool = True,
    ) -> int:
        context = ssl.create_default_context(cafile=str(ca))
        if not check_hostname:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
        if client_cert is not None:
            context.load_cert_chain(str(client_cert[0]), str(client_cert[1]))
        raw = context.wrap_socket(
            socket.create_connection(("127.0.0.1", self.port), timeout=5),
            server_hostname=server_hostname,
        )
        connection = http.client.HTTPSConnection("127.0.0.1", context=context, timeout=5)
        connection.sock = raw
        try:
            connection.request("GET", "/")
            return connection.getresponse().status
        finally:
            connection.close()

    def close(self) -> None:
        self.server.shutdown()


def test_m11_wrong_ca_mutation(tmp_path: Path) -> None:
    strict = _TlsFixture(tmp_path / "strict")
    foreign_pair = strict.foreign.issue("foreign-client", "client", ("localhost",))
    refused = False
    try:
        strict.connect(strict.authority.cert_path, client_cert=foreign_pair)
    except (ssl.SSLError, OSError):
        refused = True
    finally:
        strict.close()
    assert evaluators.require_refusal(refused, codes.UNTRUSTED_CA, "strict", "x") == []

    # Mutation: a server misconfigured to trust the foreign CA accepts it.
    permissive = _TlsFixture(
        tmp_path / "permissive", trust_ca=(tmp_path / "strict/voting-ca/voting-ca.crt")
    )
    accepted = False
    try:
        accepted = (
            permissive.connect(permissive.authority.cert_path, client_cert=foreign_pair) == 200
        )
    except (ssl.SSLError, OSError):
        accepted = False
    finally:
        permissive.close()
    findings = evaluators.require_refusal(
        not accepted, codes.UNTRUSTED_CA, "permissive-server", "foreign CA accepted"
    )
    assert codes.UNTRUSTED_CA in _codes_of(findings)


def test_m12_wrong_hostname_mutation(tmp_path: Path) -> None:
    fixture = _TlsFixture(tmp_path, require_client_cert=False)
    try:
        refused = False
        try:
            fixture.connect(fixture.authority.cert_path, server_hostname="evil.example")
        except (ssl.SSLError, ssl.CertificateError, OSError):
            refused = True
        assert evaluators.require_refusal(refused, codes.HOSTNAME_MISMATCH, "s", "x") == []

        # Mutation: hostname checking disabled — the wrong host is accepted.
        status = fixture.connect(
            fixture.authority.cert_path, server_hostname="evil.example", check_hostname=False
        )
        findings = evaluators.require_refusal(
            status != 200, codes.HOSTNAME_MISMATCH, "no-hostname-check", "wrong hostname accepted"
        )
        assert codes.HOSTNAME_MISMATCH in _codes_of(findings)
    finally:
        fixture.close()


def test_m13_missing_client_cert_mutation(tmp_path: Path) -> None:
    strict = _TlsFixture(tmp_path / "strict")
    refused = False
    try:
        strict.connect(strict.authority.cert_path)
    except (ssl.SSLError, OSError):
        refused = True
    finally:
        strict.close()
    assert evaluators.require_refusal(refused, codes.CLIENT_CERT_MISSING, "s", "x") == []

    permissive = _TlsFixture(tmp_path / "permissive", require_client_cert=False)
    try:
        status = permissive.connect(permissive.authority.cert_path)
    finally:
        permissive.close()
    findings = evaluators.require_refusal(
        status != 200,
        codes.CLIENT_CERT_MISSING,
        "no-mtls-server",
        "certificate-less client accepted on a governed mTLS path",
    )
    assert codes.CLIENT_CERT_MISSING in _codes_of(findings)


def test_m14_wrong_workload_cert_mutation(tmp_path: Path) -> None:
    fixture = _TlsFixture(tmp_path, require_client_cert=False)
    try:
        refused = False
        try:
            fixture.connect(fixture.authority.cert_path, server_hostname="membership-runtime-shell")
        except (ssl.SSLError, ssl.CertificateError, OSError):
            refused = True
        assert evaluators.require_refusal(refused, codes.WORKLOAD_IDENTITY_MISMATCH, "s", "x") == []

        # Mutation: verifying against a generic name instead of the workload
        # identity lets any service impersonate any other.
        status = fixture.connect(fixture.authority.cert_path, server_hostname="localhost")
        findings = evaluators.require_refusal(
            status != 200,
            codes.WORKLOAD_IDENTITY_MISMATCH,
            "generic-hostname-verification",
            "workload identity was not part of the verification",
        )
        assert codes.WORKLOAD_IDENTITY_MISMATCH in _codes_of(findings)
    finally:
        fixture.close()


def test_m15_universal_service_cert_is_detected(tmp_path: Path) -> None:
    authority = TrustAuthority("application-ca", tmp_path / "application-ca")
    TrustAuthority("data-ca", tmp_path / "data-ca")
    TrustAuthority("voting-ca", tmp_path / "voting-ca")
    cert, _key = authority.issue("identity-runtime-shell", "server", ("localhost",))
    # Mutation: the same key pair reused for a second workload.
    shared = tmp_path / "application-ca" / "server-membership-runtime-shell.crt"
    shared.write_bytes(cert.read_bytes())
    findings = verify_trust_layout(tmp_path)
    assert codes.UNIVERSAL_SERVICE_CERT in {f.code for f in findings}


# -- M16..M19: secrets and databases -----------------------------------------


def test_m16_secret_in_manifest_is_detected() -> None:
    findings = scan_manifest_for_secrets("db:\n  password: hunter2-super-secret\n", "topology")
    assert codes.SECRET_IN_MANIFEST in _codes_of([f.describe() for f in findings])


def test_m17_secret_value_in_logs_is_detected(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "secrets")
    value = store.generate("db-password/rt_demo", "db-credential")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "service.log").write_text(f"connecting with {value}\n", encoding="utf-8")
    findings = store.scan_for_leaks([log_dir])
    assert codes.SECRET_IN_LOGS in {f.code for f in findings}
    (log_dir / "service.log").write_text("clean\n", encoding="utf-8")
    assert store.scan_for_leaks([log_dir]) == []


def test_m18_production_db_in_preview_is_detected() -> None:
    findings = evaluators.check_preview_dsn(
        "postgresql://rt@db.prod.epd2.example:5432/epd2_identity", "identity"
    )
    assert codes.PRODUCTION_DB_IN_PREVIEW in _codes_of(findings)
    assert (
        evaluators.check_preview_dsn(
            "postgresql://rt@localhost:8432/epd2_identity?sslmode=verify-full", "identity"
        )
        == []
    )


def test_m19_sqlite_substitution_is_detected() -> None:
    findings = evaluators.check_preview_dsn("sqlite:///tmp/preview.db", "identity")
    assert codes.NON_POSTGRES_SUBSTITUTION in _codes_of(findings)
    assert codes.NON_POSTGRES_SUBSTITUTION in _codes_of(evaluators.check_engine_version("90600"))


# -- M20..M25: lifecycle truth ------------------------------------------------


def test_m20_readiness_always_true_is_detected() -> None:
    findings = evaluators.check_readiness_truth(
        dependency_down=True, reported_ready=True, subject="shell"
    )
    assert codes.READINESS_ALWAYS_TRUE in _codes_of(findings)
    assert evaluators.check_readiness_truth(True, False, "shell") == []


def test_m21_sensitive_health_output_is_detected() -> None:
    findings = evaluators.check_health_output(
        {"checks": {"db": "postgresql://rt:pw@localhost/epd2"}}, "shell"
    )
    assert codes.SENSITIVE_HEALTH_OUTPUT in _codes_of(findings)
    assert evaluators.check_health_output({"ready": True, "checks": {"db": "ok"}}, "shell") == []


def test_m22_sleep_based_readiness_is_refused() -> None:
    topology = _mini_topology(probes={"liveness": "/livez", "readiness": "sleep 30"})
    findings = validate_topology(topology)
    assert codes.SLEEP_BASED_READINESS in _codes_of(findings)


def test_m23_crashloop_marked_healthy_is_detected() -> None:
    findings = evaluators.check_crashloop(failed=True, reported_healthy=True, subject="shell")
    assert codes.CRASHLOOP_MARKED_HEALTHY in _codes_of(findings)
    assert evaluators.check_crashloop(True, False, "shell") == []


def test_m24_failed_deploy_marked_success_is_detected() -> None:
    findings = evaluators.check_deploy_outcome(had_findings=True, exit_code=0, claimed_success=True)
    assert codes.FAILED_DEPLOY_MARKED_SUCCESS in _codes_of(findings)
    assert evaluators.check_deploy_outcome(True, 1, claimed_success=False) == []


def test_m25_partial_unready_deploy_fails_closed_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real mini-deploy whose only shell cannot start must fail closed:
    non-zero findings, no readiness claim, runtime stopped (§43)."""
    from scripts.acceptance.canonical import sha256_file
    from scripts.infra03 import PREDECESSOR

    source = tmp_path / "source"
    (source / "src").mkdir(parents=True)
    (source / "src/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    artifact = tmp_path / "candidate.zip"
    with zipfile.ZipFile(artifact, "w") as bundle:
        bundle.write(source / "src/module.py", "ROOT/src/module.py")
    monkeypatch.setitem(PREDECESSOR, "zip_sha256", sha256_file(artifact))
    monkeypatch.setitem(PREDECESSOR, "size_bytes", artifact.stat().st_size)
    extracted = tmp_path / "digest-probe"
    from scripts.infra03.artifacts import deploy_artifact as _deploy

    digest, _ = _deploy(artifact, extracted)
    monkeypatch.setitem(PREDECESSOR, "freeze_tree_digest", digest)

    topology = _mini_topology(
        resources={"cpu_shares": 1, "memory_bytes": 33554432},  # too small to start
        restart_policy={"mode": "on-failure", "max_restarts": 1, "backoff_seconds": 0.1},
    )
    topology["services"]["postgres-preview"] = {
        **_mini_topology()["services"]["fixture-service"],
        "network_segment": "data",
        "ports": {"tls": 8437},
        "artifact": "accepted",
    }
    # pytest's tmp tree is 0700; the cluster's non-root OS user needs a
    # traversable instance path, so the live instance goes under /tmp directly
    import shutil
    import tempfile

    instance_root = Path(tempfile.mkdtemp(prefix="epd2-infra03-m25-", dir="/tmp"))
    instance_root.chmod(0o711)
    supervisor = Supervisor(REPO_ROOT, PreviewInstance(instance_root / "instance"))
    try:
        evidence, findings = supervisor.deploy(topology, artifact, readiness_timeout=8.0)
    finally:
        supervisor.stop_all()
        shutil.rmtree(instance_root, ignore_errors=True)
    assert findings, "a deploy that cannot reach readiness must fail"
    assert codes.PARTIAL_UNSAFE_EXPOSURE in {f.code for f in findings}
    assert not any(step["step"] == "readiness" and step["ok"] for step in evidence["steps"])


# -- M26..M29: rollback / redeploy / drift / egress ---------------------------


def test_m26_rollback_to_unverified_release_is_refused(tmp_path: Path) -> None:
    supervisor = Supervisor(REPO_ROOT, PreviewInstance(tmp_path / "instance"))
    supervisor.release_digest = "a" * 64
    findings = supervisor.rollback_check("b" * 64, [])
    assert codes.UNSAFE_ROLLBACK in {f.code for f in findings}


def test_m27_non_idempotent_redeploy_is_detected() -> None:
    findings = evaluators.check_redeploy("a" * 64, "b" * 64, converged=True)
    assert codes.NON_IDEMPOTENT_REDEPLOY in _codes_of(findings)
    assert evaluators.check_redeploy("a" * 64, "a" * 64, converged=True) == []


def test_m28_ignored_drift_is_detected() -> None:
    findings = evaluators.check_drift_scan(drift_present=True, reported_findings=0)
    assert codes.DRIFT_IGNORED in _codes_of(findings)
    assert evaluators.check_drift_scan(True, 3) == []


def test_m29_undeclared_egress_is_refused() -> None:
    topology = _mini_topology(egress=["https://telemetry.example.com"])
    findings = validate_topology(topology)
    assert codes.UNDECLARED_EGRESS in _codes_of(findings)


# -- M30..M33: voting isolation / reset ---------------------------------------


def test_m30_voting_person_id_leak_is_detected() -> None:
    findings = evaluators.scan_voting_telemetry(
        '{"event": "ballot-open", "member_id": "member-123456"}', "voting.log"
    )
    assert codes.VOTING_PERSON_ID_LEAK in _codes_of(findings)


def test_m31_voting_global_correlation_is_detected() -> None:
    findings = evaluators.scan_voting_telemetry(
        '{"event": "ballot-open", "request": "app-0123456789abcdef"}', "voting.log"
    )
    assert codes.VOTING_GLOBAL_CORRELATION in _codes_of(findings)
    assert evaluators.scan_voting_telemetry('{"event": "ballot-open"}', "voting.log") == []


def test_m32_shared_voting_observability_is_detected() -> None:
    findings = evaluators.check_shared_observability(
        '{"service": "voting-runtime-shell", "event": "x"}\n'
    )
    assert codes.SHARED_VOTING_OBSERVABILITY in _codes_of(findings)
    assert evaluators.check_shared_observability('{"service": "ingress-gateway"}\n') == []


def test_m33_stale_state_after_reset_is_detected() -> None:
    findings = evaluators.check_reset(stale_rows=2, subject="epd2_identity")
    assert codes.STALE_STATE_AFTER_RESET in _codes_of(findings)
    assert evaluators.check_reset(0, "epd2_identity") == []


# -- M34..M36: destructive safety / predecessor / bytes -----------------------


def test_m34_ambiguous_destructive_target_is_refused(tmp_path: Path) -> None:
    supervisor = Supervisor(REPO_ROOT, PreviewInstance(tmp_path / "instance"))
    findings = supervisor.verify_destroy_target("production", "whatever")
    assert codes.AMBIGUOUS_DESTRUCTIVE_TARGET in {f.code for f in findings}
    findings = supervisor.verify_destroy_target("preview", "no-marker-instance")
    assert codes.AMBIGUOUS_DESTRUCTIVE_TARGET in {f.code for f in findings}


def test_m35_stale_predecessor_record_is_refused() -> None:
    stale: dict[str, object] = {
        "decision": "ACCEPTED / CLOSED",
        "candidate": {
            "sha256": "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
            "size_bytes": 15854311,
            "freeze_tree_digest": "d" * 64,
        },
    }
    findings = verify_predecessor_record(stale)
    assert codes.STALE_PREDECESSOR in {f.code for f in findings}


def test_m36_post_test_byte_mutation_is_detected() -> None:
    findings = evaluators.check_post_test_bytes("a" * 64, "b" * 64)
    assert codes.POST_TEST_BYTE_MUTATION in _codes_of(findings)
    assert evaluators.check_post_test_bytes("a" * 64, "a" * 64) == []


# -- distinctness -------------------------------------------------------------


def test_every_infra03_mutation_class_has_its_own_detector() -> None:
    detectors = list(MUTATION_DETECTORS.values())
    assert len(MUTATION_DETECTORS) == 36
    assert len(set(detectors)) == len(detectors), (
        "the 36 mutation classes must map onto 36 distinct detector codes; a shared "
        "poison marker is not independent coverage"
    )
    for detector in detectors:
        assert detector.startswith("I03_")
