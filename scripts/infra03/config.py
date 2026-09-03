"""Runtime configuration classification and startup validation (INFRA03 §25, §26).

Every configuration item a service consumes is classified as one of:
``non_secret_static``, ``environment_specific``, ``runtime_derived``,
``secret`` or ``trust_material``. A service refuses to start (never
"starts permissively") when required configuration is missing, unknown
critical configuration appears, or a secret/trust item arrives through a
non-secret channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.infra03 import codes

CONFIG_CLASSES = (
    "non_secret_static",
    "environment_specific",
    "runtime_derived",
    "secret",
    "trust_material",
)


@dataclass(frozen=True)
class ConfigFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


@dataclass(frozen=True)
class ConfigItem:
    name: str
    config_class: str
    required: bool = True


#: The governed configuration contract of the runtime shells.
SERVICE_CONFIG_CONTRACT: tuple[ConfigItem, ...] = (
    ConfigItem("service_id", "non_secret_static"),
    ConfigItem("network_segment", "non_secret_static"),
    ConfigItem("environment", "environment_specific"),
    ConfigItem("instance_id", "runtime_derived"),
    ConfigItem("app_root", "environment_specific"),
    ConfigItem("listen_port", "environment_specific"),
    ConfigItem("server_cert", "trust_material"),
    ConfigItem("server_key", "trust_material"),
    ConfigItem("trust_ca", "trust_material"),
    ConfigItem("mtls_required", "non_secret_static"),
    ConfigItem("db_dsn", "environment_specific", required=False),
    ConfigItem("db_password_file", "secret", required=False),
    ConfigItem("db_ca", "trust_material", required=False),
    ConfigItem("client_cert", "trust_material", required=False),
    ConfigItem("client_key", "trust_material", required=False),
    ConfigItem("observability_endpoint", "environment_specific", required=False),
    ConfigItem("observability_client_cert", "trust_material", required=False),
    ConfigItem("observability_client_key", "trust_material", required=False),
    ConfigItem("expected_app_digest", "non_secret_static"),
    ConfigItem("voting_domain", "non_secret_static"),
)

_CRITICAL_UNKNOWN_PREFIXES = ("db_", "trust_", "secret_", "tls_", "auth_")


def validate_startup_config(provided: dict[str, Any]) -> list[ConfigFinding]:
    """Fail-closed startup validation (§26): missing/unknown critical config
    refuses startup instead of activating permissive defaults."""
    findings: list[ConfigFinding] = []
    contract = {item.name: item for item in SERVICE_CONFIG_CONTRACT}
    for item in SERVICE_CONFIG_CONTRACT:
        value = provided.get(item.name)
        if item.required and (value is None or str(value) == ""):
            findings.append(
                ConfigFinding(
                    codes.CONFIG_INVALID_STARTUP,
                    item.name,
                    f"required {item.config_class} configuration missing; the service "
                    "must fail startup, not guess a default",
                )
            )
    for name in provided:
        if name in contract:
            continue
        if str(name).startswith(_CRITICAL_UNKNOWN_PREFIXES):
            findings.append(
                ConfigFinding(
                    codes.CONFIG_INVALID_STARTUP,
                    str(name),
                    "unknown critical configuration item; refusing rather than "
                    "silently ignoring security-relevant input",
                )
            )
    if str(provided.get("mtls_required", "")).lower() in ("false", "0", "no", "off"):
        segment = str(provided.get("network_segment", ""))
        if segment in ("application", "voting", "observability"):
            findings.append(
                ConfigFinding(
                    codes.PERMISSIVE_DEFAULT_FORBIDDEN,
                    "mtls_required",
                    f"disabling mTLS in segment {segment!r} is a permissive default and is refused",
                )
            )
    return findings


def classify(provided: dict[str, Any]) -> dict[str, str]:
    """Classification of every provided item (unknown items marked)."""
    contract = {item.name: item.config_class for item in SERVICE_CONFIG_CONTRACT}
    return {name: contract.get(str(name), "UNKNOWN") for name in sorted(provided)}
