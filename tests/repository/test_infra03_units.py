"""INFRA-03 unit suite: validators, evaluators and refusal paths not already
exercised as governed mutation classes in ``test_infra03_mutation_suite.py``.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import pytest
from scripts.infra03 import PREDECESSOR, codes
from scripts.infra03.artifacts import (
    tree_digest_of_directory,
    verify_observed_digest,
    verify_predecessor_record,
)
from scripts.infra03.config import classify, validate_startup_config
from scripts.infra03.gates import GATES
from scripts.infra03.mutations import MUTATION_DETECTORS
from scripts.infra03.secrets import SecretStore, write_secret_inventory
from scripts.infra03.service import VOTING_FORBIDDEN_HEADERS, _redact
from scripts.infra03.supervisor import stale_state_check
from scripts.infra03.topology import (
    load_topology,
    validate_catalog,
    validate_flow_inventory,
    validate_topology,
)
from scripts.infra03.trust import TrustAuthority, peer_workload_identity, verify_trust_layout

REPO_ROOT = Path(__file__).resolve().parents[2]


def _codes_of(findings: list[Any]) -> set[str]:
    return {str(f).split(":", 1)[0] if isinstance(f, str) else f.code for f in findings}


# -- the real governed documents ---------------------------------------------


def test_real_environment_catalog_is_valid() -> None:
    assert validate_catalog(REPO_ROOT) == []


def test_real_topology_and_flow_inventory_are_valid() -> None:
    topology = load_topology(REPO_ROOT)
    manifest_text = (REPO_ROOT / "infra/runtime/topology.yaml").read_text(encoding="utf-8")
    assert validate_topology(topology, manifest_text) == []
    assert validate_flow_inventory(REPO_ROOT, topology) == []


def test_topology_parses_deterministically() -> None:
    assert load_topology(REPO_ROOT) == load_topology(REPO_ROOT)


def test_gate_registry_has_42_gates() -> None:
    assert len(GATES) == 42
    assert sorted(GATES) == [f"G{i:02d}" for i in range(1, 43)]


def test_predecessor_constants_match_accepted_identity() -> None:
    assert PREDECESSOR["zip_sha256"] == (
        "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c"
    )
    assert PREDECESSOR["size_bytes"] == 15980332
    assert len(MUTATION_DETECTORS) == 36


# -- environment catalog refusals --------------------------------------------


def test_catalog_missing_environment_is_refused(tmp_path: Path) -> None:
    (tmp_path / "infra/runtime").mkdir(parents=True)
    (tmp_path / "infra/runtime/environment_catalog.json").write_text(
        json.dumps({"environments": {"local_dev": {}}}), encoding="utf-8"
    )
    findings = validate_catalog(tmp_path)
    assert codes.ENVIRONMENT_CATALOG_INVALID in _codes_of(findings)


def test_catalog_missing_fields_are_refused(tmp_path: Path) -> None:
    (tmp_path / "infra/runtime").mkdir(parents=True)
    entry = {"purpose": "x"}  # everything else missing
    (tmp_path / "infra/runtime/environment_catalog.json").write_text(
        json.dumps({"environments": {"local_dev": entry, "ci_runtime": entry, "preview": entry}}),
        encoding="utf-8",
    )
    findings = validate_catalog(tmp_path)
    assert codes.ENVIRONMENT_CATALOG_INVALID in _codes_of(findings)


# -- topology structural refusals --------------------------------------------


def _fixture_topology() -> dict[str, Any]:
    # Deliberately duplicated from test_infra03_mutation_suite.py: the
    # repository's mypy grouping maps test files as top-level modules, so
    # test modules do not import from each other.
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


def test_port_collision_is_refused() -> None:
    topology = _fixture_topology()
    service = dict(topology["services"]["fixture-service"])
    topology["services"]["second-service"] = service  # same port 8451
    findings = validate_topology(topology)
    assert codes.TOPOLOGY_INCOMPLETE in _codes_of(findings)


def test_undeclared_dependency_is_refused() -> None:
    topology = _fixture_topology()
    topology["services"]["fixture-service"]["dependencies"] = ["ghost-service"]
    findings = validate_topology(topology)
    assert codes.TOPOLOGY_INCOMPLETE in _codes_of(findings)


def test_missing_mandatory_field_is_refused() -> None:
    topology = _fixture_topology()
    del topology["services"]["fixture-service"]["probes"]
    findings = validate_topology(topology)
    assert codes.TOPOLOGY_INCOMPLETE in _codes_of(findings)


def test_voting_segment_must_not_trust_application_ca() -> None:
    topology = _fixture_topology()
    topology["services"]["fixture-service"].update(
        network_segment="voting",
        voting_domain=True,
        trust={"trusts": ["application-ca", "voting-ca"]},
    )
    findings = validate_topology(topology)
    assert codes.SHARED_VOTING_OBSERVABILITY in _codes_of(findings)


def test_flow_inventory_requires_deny_default(tmp_path: Path) -> None:
    (tmp_path / "flows.json").write_text(
        json.dumps({"default_policy": "ALLOW", "flows": []}), encoding="utf-8"
    )
    findings = validate_flow_inventory(tmp_path, {"services": {}}, Path("flows.json"))
    assert codes.UNDECLARED_FLOW in _codes_of(findings)


def test_flow_inventory_requires_complete_fields(tmp_path: Path) -> None:
    (tmp_path / "flows.json").write_text(
        json.dumps(
            {
                "default_policy": "DENY_UNDECLARED",
                "flows": [{"id": "F01", "source": "a", "destination": "b"}],
            }
        ),
        encoding="utf-8",
    )
    findings = validate_flow_inventory(tmp_path, {"services": {}}, Path("flows.json"))
    assert codes.UNDECLARED_FLOW in _codes_of(findings)


# -- configuration contract ---------------------------------------------------


def test_missing_required_config_refuses_startup() -> None:
    findings = validate_startup_config({"service_id": "x"})
    assert codes.CONFIG_INVALID_STARTUP in _codes_of(findings)


def test_unknown_critical_config_refuses_startup() -> None:
    complete = {
        "service_id": "x",
        "network_segment": "application",
        "environment": "preview",
        "instance_id": "preview-1",
        "app_root": "/tmp/app",
        "listen_port": 8451,
        "server_cert": "/tmp/c.crt",
        "server_key": "/tmp/c.key",
        "trust_ca": "/tmp/ca.crt",
        "mtls_required": "true",
        "expected_app_digest": "d" * 64,
        "voting_domain": "false",
    }
    assert validate_startup_config(complete) == []
    corrupted = dict(complete)
    corrupted["auth_bypass_mode"] = "on"
    findings = validate_startup_config(corrupted)
    assert codes.CONFIG_INVALID_STARTUP in _codes_of(findings)


def test_disabling_mtls_in_internal_segment_is_refused() -> None:
    findings = validate_startup_config({"network_segment": "application", "mtls_required": "false"})
    assert codes.PERMISSIVE_DEFAULT_FORBIDDEN in _codes_of(findings)


def test_config_classification_covers_all_classes() -> None:
    classified = classify({"service_id": "x", "db_password_file": "f", "server_cert": "c"})
    assert classified["service_id"] == "non_secret_static"
    assert classified["db_password_file"] == "secret"
    assert classified["server_cert"] == "trust_material"


# -- secrets ------------------------------------------------------------------


def test_unknown_credential_class_is_refused(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "secrets")
    with pytest.raises(PermissionError, match=codes.SECRET_INJECTION_UNCLASSIFIED):
        store.generate("slot", "coffee-credential")


def test_voting_key_material_is_never_provisionable(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "secrets")
    with pytest.raises(PermissionError, match="voting"):
        store.generate("voting-master-key", "voting-domain-key-material")


def test_secret_inventory_carries_no_values(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "secrets")
    value = store.generate("db-password/rt_x", "db-credential")
    target = tmp_path / "inventory.json"
    write_secret_inventory(store, target)
    assert value not in target.read_text(encoding="utf-8")


def test_secret_files_are_owner_only(tmp_path: Path) -> None:
    store = SecretStore(tmp_path / "secrets")
    store.generate("db-password/rt_x", "db-credential")
    for path in (tmp_path / "secrets").iterdir():
        assert (path.stat().st_mode & 0o077) == 0


# -- trust --------------------------------------------------------------------


def test_trust_layout_of_fresh_provisioning_is_clean(tmp_path: Path) -> None:
    for name in ("application-ca", "data-ca", "voting-ca"):
        TrustAuthority(name, tmp_path / name)
    assert verify_trust_layout(tmp_path) == []


def test_absent_ca_is_refused(tmp_path: Path) -> None:
    TrustAuthority("application-ca", tmp_path / "application-ca")
    findings = verify_trust_layout(tmp_path)
    assert codes.TRUST_MATERIAL_INVALID in _codes_of(findings)


def test_world_readable_key_is_refused(tmp_path: Path) -> None:
    for name in ("application-ca", "data-ca", "voting-ca"):
        TrustAuthority(name, tmp_path / name)
    key = tmp_path / "application-ca" / "application-ca.key"
    key.chmod(0o644)
    findings = verify_trust_layout(tmp_path)
    assert codes.TRUST_MATERIAL_INVALID in _codes_of(findings)


def test_peer_workload_identity_reads_the_cn(tmp_path: Path) -> None:
    authority = TrustAuthority("application-ca", tmp_path / "application-ca")
    cert_path, _ = authority.issue("identity-runtime-shell", "client", ("localhost",))
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import Encoding

    certificate = x509.load_pem_x509_certificate(cert_path.read_bytes())
    assert peer_workload_identity(certificate.public_bytes(Encoding.DER)) == (
        "identity-runtime-shell"
    )


def test_issued_certificates_have_bounded_validity(tmp_path: Path) -> None:
    authority = TrustAuthority("application-ca", tmp_path / "application-ca", validity_days=7)
    cert_path, _ = authority.issue("x", "server", ("localhost",))
    from cryptography import x509

    certificate = x509.load_pem_x509_certificate(cert_path.read_bytes())
    lifetime = certificate.not_valid_after_utc - certificate.not_valid_before_utc
    assert lifetime <= datetime.timedelta(days=9)


# -- artifacts ----------------------------------------------------------------


def test_tree_digest_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a/x.txt").write_text("one", encoding="utf-8")
    first = tree_digest_of_directory(tmp_path)
    assert first == tree_digest_of_directory(tmp_path)
    (tmp_path / "a/x.txt").write_text("two", encoding="utf-8")
    assert tree_digest_of_directory(tmp_path) != first


def test_observed_digest_mismatch_is_refused() -> None:
    findings = verify_observed_digest("f" * 64, "identity-runtime-shell")
    assert codes.ARTIFACT_DIGEST_MISMATCH in _codes_of(findings)
    assert verify_observed_digest(str(PREDECESSOR["freeze_tree_digest"]), "x") == []


def test_exact_predecessor_record_verifies_clean() -> None:
    record: dict[str, object] = {
        "decision": "ACCEPTED / CLOSED",
        "candidate": {
            "sha256": PREDECESSOR["zip_sha256"],
            "size_bytes": PREDECESSOR["size_bytes"],
            "freeze_tree_digest": PREDECESSOR["freeze_tree_digest"],
        },
    }
    assert verify_predecessor_record(record) == []


def test_unaccepted_predecessor_decision_is_refused() -> None:
    record: dict[str, object] = {
        "decision": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
        "candidate": {
            "sha256": PREDECESSOR["zip_sha256"],
            "size_bytes": PREDECESSOR["size_bytes"],
            "freeze_tree_digest": PREDECESSOR["freeze_tree_digest"],
        },
    }
    findings = verify_predecessor_record(record)
    assert codes.STALE_PREDECESSOR in _codes_of(findings)


# -- runtime shell helpers ----------------------------------------------------


def test_redaction_strips_secret_shapes() -> None:
    assert "hunter2" not in _redact("password=hunter2-super")
    # assembled at runtime so the repository's own secret scanner does not
    # flag this synthetic fixture as a committed key block
    pem_fixture = "-----BEGIN " + "PRIVATE KEY-----\nabc\n-----END " + "PRIVATE KEY-----"
    assert "abc" not in _redact(pem_fixture)
    assert _redact("plain message") == "plain message"


def test_voting_forbidden_headers_cover_identity_and_correlation() -> None:
    lowered = set(VOTING_FORBIDDEN_HEADERS)
    for required in (
        "x-member-id",
        "x-person-id",
        "x-account-id",
        "x-session-id",
        "x-correlation-id",
    ):
        assert required in lowered


def test_stale_state_check_refuses_leftovers(tmp_path: Path) -> None:
    target = tmp_path / "instance"
    target.mkdir()
    (target / "leftover").write_text("x", encoding="utf-8")
    findings = stale_state_check(target)
    assert codes.CLEAN_ROOM_VIOLATION in _codes_of([f.describe() for f in findings])
    assert stale_state_check(tmp_path / "fresh") == []
