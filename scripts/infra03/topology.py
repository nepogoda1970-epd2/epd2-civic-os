"""Topology and environment-catalog loading, linting and policy validation
(INFRA03 §7, §8, §18, §20, §21).

The topology is the single declarative source of runtime truth. This module
fails closed on: incomplete service declarations, mutable artifact
references, admin/non-public services exposed publicly, undeclared network
segments, dependencies without a declared flow, voting-isolation violations
and secret values embedded in the manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.acceptance.canonical import load_json
from scripts.infra03 import codes
from scripts.infra03.secrets import scan_manifest_for_secrets

TOPOLOGY_FILE = Path("infra/runtime/topology.yaml")
CATALOG_FILE = Path("infra/runtime/environment_catalog.json")
FLOW_INVENTORY_FILE = Path("validation/infra03/network_flow_inventory.json")

REQUIRED_SERVICE_FIELDS = (
    "role",
    "artifact",
    "network_segment",
    "ports",
    "ingress",
    "egress",
    "dependencies",
    "secrets",
    "config",
    "trust",
    "probes",
    "persistence",
    "resources",
    "restart_policy",
    "shutdown",
    "voting_domain",
)

REQUIRED_CATALOG_FIELDS = (
    "purpose",
    "allowed_artifact_source",
    "network_scope",
    "db_class",
    "secret_source",
    "trust_source",
    "persistence",
    "exposure",
    "reset_policy",
    "evidence_requirements",
    "operator_ownership",
    "prohibited_use",
)

_MUTABLE_MARKERS = (":latest", "@latest", ":main", ":head", ":dev", ":nightly")


@dataclass(frozen=True)
class TopologyFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def load_topology(root: Path, topology_file: Path | None = None) -> dict[str, Any]:
    path = root / (topology_file or TOPOLOGY_FILE)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"topology is not a mapping: {path}")
    return loaded


def validate_catalog(root: Path, catalog_file: Path | None = None) -> list[TopologyFinding]:
    findings: list[TopologyFinding] = []
    document = load_json(root / (catalog_file or CATALOG_FILE))
    environments = document.get("environments", {})
    for required in ("local_dev", "ci_runtime", "preview"):
        if required not in environments:
            findings.append(
                TopologyFinding(
                    codes.ENVIRONMENT_CATALOG_INVALID,
                    required,
                    "mandatory environment absent from the catalog",
                )
            )
    for name, entry in environments.items():
        if not isinstance(entry, dict):
            findings.append(
                TopologyFinding(codes.ENVIRONMENT_CATALOG_INVALID, str(name), "not a mapping")
            )
            continue
        for field in REQUIRED_CATALOG_FIELDS:
            value = entry.get(field)
            if value is None or (isinstance(value, (str, list)) and not value):
                findings.append(
                    TopologyFinding(
                        codes.ENVIRONMENT_CATALOG_INVALID,
                        f"{name}.{field}",
                        "mandatory catalog field missing or empty",
                    )
                )
        if name != "production" and "production" in str(entry.get("purpose", "")).lower():
            findings.append(
                TopologyFinding(
                    codes.ENVIRONMENT_CATALOG_INVALID,
                    str(name),
                    "non-production environment declares a production purpose",
                )
            )
    return findings


def _artifact_findings(topology: dict[str, Any]) -> list[TopologyFinding]:
    findings: list[TopologyFinding] = []
    artifacts = topology.get("artifacts", {})
    for name, artifact in artifacts.items():
        if not isinstance(artifact, dict):
            continue
        reference = f"{artifact.get('filename', '')}{artifact.get('name', '')}"
        for marker in _MUTABLE_MARKERS:
            if marker in reference.lower():
                findings.append(
                    TopologyFinding(
                        codes.MUTABLE_ARTIFACT_REFERENCE,
                        str(name),
                        f"artifact reference carries mutable marker {marker!r}",
                    )
                )
        if artifact.get("class") == "accepted-candidate-archive":
            sha = str(artifact.get("sha256", ""))
            if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                findings.append(
                    TopologyFinding(
                        codes.MUTABLE_ARTIFACT_REFERENCE,
                        str(name),
                        "accepted artifact is not pinned by a full sha256 digest",
                    )
                )
    return findings


def validate_topology(topology: dict[str, Any], manifest_text: str = "") -> list[TopologyFinding]:
    """Fail-closed lint of the declarative topology (§8, §18, §20, §21)."""
    findings: list[TopologyFinding] = list(_artifact_findings(topology))
    segments = set(topology.get("network_segments", {}))
    for required_segment in (
        "public",
        "application",
        "data",
        "admin_ops",
        "voting",
        "observability",
    ):
        if required_segment not in segments:
            findings.append(
                TopologyFinding(
                    codes.TOPOLOGY_INCOMPLETE,
                    required_segment,
                    "mandatory network segment undeclared",
                )
            )

    services = topology.get("services", {})
    if not services:
        findings.append(TopologyFinding(codes.TOPOLOGY_INCOMPLETE, "services", "no services"))
    artifacts = set(topology.get("artifacts", {}))
    used_ports: dict[int, str] = {}
    for name, service in services.items():
        subject = str(name)
        if not isinstance(service, dict):
            findings.append(TopologyFinding(codes.TOPOLOGY_INCOMPLETE, subject, "not a mapping"))
            continue
        for field in REQUIRED_SERVICE_FIELDS:
            if field not in service:
                findings.append(
                    TopologyFinding(
                        codes.TOPOLOGY_INCOMPLETE,
                        f"{subject}.{field}",
                        "mandatory topology field undeclared",
                    )
                )
        if service.get("artifact") not in artifacts:
            findings.append(
                TopologyFinding(
                    codes.MUTABLE_ARTIFACT_REFERENCE,
                    subject,
                    f"service references undeclared artifact {service.get('artifact')!r}",
                )
            )
        segment = str(service.get("network_segment", ""))
        if segment not in segments:
            findings.append(
                TopologyFinding(
                    codes.WRONG_NETWORK_SEGMENT, subject, f"undeclared segment {segment!r}"
                )
            )
        ingress = service.get("ingress", {}) if isinstance(service.get("ingress"), dict) else {}
        public = bool(ingress.get("public_endpoint"))
        if public and segment != "public":
            findings.append(
                TopologyFinding(
                    codes.ADMIN_ENDPOINT_PUBLIC,
                    subject,
                    f"public endpoint declared outside the public segment ({segment})",
                )
            )
        if segment == "admin_ops" and (public or service.get("ports")):
            findings.append(
                TopologyFinding(
                    codes.ADMIN_ENDPOINT_PUBLIC,
                    subject,
                    "admin/ops plane must not expose network ports",
                )
            )
        for port_name, port in (service.get("ports") or {}).items():
            if not isinstance(port, int) or not (1024 <= port <= 65535):
                findings.append(
                    TopologyFinding(
                        codes.TOPOLOGY_INCOMPLETE,
                        f"{subject}.ports.{port_name}",
                        f"invalid port {port!r}",
                    )
                )
                continue
            if port in used_ports:
                findings.append(
                    TopologyFinding(
                        codes.TOPOLOGY_INCOMPLETE,
                        f"{subject}.ports.{port_name}",
                        f"port {port} collides with {used_ports[port]}",
                    )
                )
            used_ports[port] = subject
        for dependency in service.get("dependencies") or []:
            if dependency not in services:
                findings.append(
                    TopologyFinding(
                        codes.TOPOLOGY_INCOMPLETE,
                        f"{subject}.dependencies",
                        f"undeclared dependency {dependency!r}",
                    )
                )
        if service.get("egress"):
            findings.append(
                TopologyFinding(
                    codes.UNDECLARED_EGRESS,
                    subject,
                    "preview services declare no external egress; a non-empty egress "
                    "list requires separate governed approval",
                )
            )
        probes = service.get("probes", {}) if isinstance(service.get("probes"), dict) else {}
        for probe_name, spec in probes.items():
            if "sleep" in str(spec).lower():
                findings.append(
                    TopologyFinding(
                        codes.SLEEP_BASED_READINESS,
                        f"{subject}.probes.{probe_name}",
                        "sleep-based readiness is not a dependency check (INFRA03 "
                        "section 27); declare a real probe",
                    )
                )
        if bool(service.get("voting_domain")) != (segment == "voting"):
            findings.append(
                TopologyFinding(
                    codes.WRONG_NETWORK_SEGMENT,
                    subject,
                    "voting_domain flag and voting segment membership disagree",
                )
            )
        if segment == "voting":
            trust = service.get("trust", {}) if isinstance(service.get("trust"), dict) else {}
            trusts = [str(t) for t in trust.get("trusts", [])]
            if "application-ca" in trusts:
                findings.append(
                    TopologyFinding(
                        codes.SHARED_VOTING_OBSERVABILITY,
                        subject,
                        "voting segment must not trust the application CA (separate "
                        "trust domain, §17/§20)",
                    )
                )
            config_slots = [str(c) for c in service.get("config", [])]
            if "observability_endpoint" in config_slots:
                findings.append(
                    TopologyFinding(
                        codes.SHARED_VOTING_OBSERVABILITY,
                        subject,
                        "voting segment must not use the shared observability collector",
                    )
                )

    if manifest_text:
        for hit in scan_manifest_for_secrets(manifest_text, "infra/runtime/topology.yaml"):
            findings.append(TopologyFinding(hit.code, hit.subject, hit.detail))
    return findings


def validate_flow_inventory(
    root: Path, topology: dict[str, Any], inventory_file: Path | None = None
) -> list[TopologyFinding]:
    """Every dependency edge must be covered by a declared flow (§19)."""
    findings: list[TopologyFinding] = []
    document = load_json(root / (inventory_file or FLOW_INVENTORY_FILE))
    if document.get("default_policy") != "DENY_UNDECLARED":
        findings.append(
            TopologyFinding(
                codes.UNDECLARED_FLOW,
                "default_policy",
                "flow inventory must default-deny undeclared flows",
            )
        )
    flows = document.get("flows", [])
    edges = {
        (str(flow.get("source")), str(flow.get("destination")))
        for flow in flows
        if isinstance(flow, dict)
    }
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        for field in ("id", "source", "destination", "protocol", "purpose", "owning_requirement"):
            if not str(flow.get(field, "") or "").strip():
                findings.append(
                    TopologyFinding(
                        codes.UNDECLARED_FLOW,
                        str(flow.get("id", "?")),
                        f"flow lacks mandatory field {field!r}",
                    )
                )
    for name, service in (topology.get("services") or {}).items():
        for dependency in service.get("dependencies") or []:
            if (str(name), str(dependency)) not in edges:
                findings.append(
                    TopologyFinding(
                        codes.UNDECLARED_FLOW,
                        f"{name}->{dependency}",
                        "topology dependency has no declared flow in the inventory",
                    )
                )
    return findings
