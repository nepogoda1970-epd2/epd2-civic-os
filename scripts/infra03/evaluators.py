"""Pure fail-closed evaluators shared by the live gates and the mutation
suite (INFRA03 §60, §61).

Each function is the *single* implementation of one refusal rule: the gate
path feeds it live runtime observations, the mutation suite feeds it
deliberately corrupted observations and asserts the exact detector code.
A detector that exists only in a test is a dead detector; these are the
live ones.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.infra03 import codes

_SENSITIVE_HEALTH_MARKERS = ("password", "dsn", "secret", "token", "/home/", "postgresql://")

#: Persistent member/person/account/session identifier shapes that must not
#: appear in voting-domain telemetry (§20, §38, §39).
_VOTING_IDENTITY_PATTERNS = (
    re.compile(r"(?i)\bmember[-_]?id\b"),
    re.compile(r"(?i)\bperson[-_]?id\b"),
    re.compile(r"(?i)\baccount[-_]?id\b"),
    re.compile(r"(?i)\bsession[-_]?id\b"),
    re.compile(r"(?i)\bmember-\d{3,}\b"),
)

#: The application correlation-id namespace (ingress-issued request ids).
_APP_CORRELATION_PATTERN = re.compile(r"\bapp-[0-9a-f]{8,}\b")

_PRODUCTION_DB_MARKERS = ("prod", "live", ".corp", "production")


def check_forwarded(backend_view: dict[str, Any], spoofed_value: str) -> list[str]:
    """§21: a spoofed forwarded header surviving to the backend fails."""
    text = " ".join(str(value) for value in backend_view.values())
    if spoofed_value and spoofed_value in text:
        return [
            f"{codes.FORWARDED_HEADER_UNTRUSTED}: ingress: spoofed forwarded header "
            f"{spoofed_value!r} survived the trust boundary"
        ]
    return []


def check_plaintext(served_plaintext: bool, subject: str) -> list[str]:
    if served_plaintext:
        return [
            f"{codes.PLAINTEXT_FALLBACK_FORBIDDEN}: {subject}: a TLS endpoint served "
            "plaintext; no fallback is permitted"
        ]
    return []


def check_readiness_truth(dependency_down: bool, reported_ready: bool, subject: str) -> list[str]:
    """§29: ready while a required dependency is down is a lie."""
    if dependency_down and reported_ready:
        return [
            f"{codes.READINESS_ALWAYS_TRUE}: {subject}: readiness reported true while "
            "a required dependency was down"
        ]
    return []


def check_health_output(payload: dict[str, Any], subject: str) -> list[str]:
    """§28: health endpoints expose states, never sensitive material."""
    import json as _json

    text = _json.dumps(payload).lower()
    return [
        f"{codes.SENSITIVE_HEALTH_OUTPUT}: {subject}: health output carries sensitive "
        f"marker {marker!r}"
        for marker in _SENSITIVE_HEALTH_MARKERS
        if marker in text
    ]


def check_crashloop(failed: bool, reported_healthy: bool, subject: str) -> list[str]:
    """§31: a crash-looping service must never appear healthy."""
    if failed and reported_healthy:
        return [
            f"{codes.CRASHLOOP_MARKED_HEALTHY}: {subject}: service exceeded its restart "
            "budget yet is reported healthy"
        ]
    return []


def check_deploy_outcome(had_findings: bool, exit_code: int, claimed_success: bool) -> list[str]:
    """§43: a failed deploy that claims success or exits zero fails closed."""
    findings: list[str] = []
    if had_findings and claimed_success:
        findings.append(
            f"{codes.FAILED_DEPLOY_MARKED_SUCCESS}: deploy: failure was reported as success"
        )
    if had_findings and exit_code == 0:
        findings.append(
            f"{codes.FAILED_DEPLOY_MARKED_SUCCESS}: deploy: failed deployment exited zero"
        )
    return findings


def check_redeploy(digest_before: str, digest_after: str, converged: bool) -> list[str]:
    """§41: redeploying the same release must converge and keep identity."""
    findings: list[str] = []
    if digest_before != digest_after:
        findings.append(
            f"{codes.NON_IDEMPOTENT_REDEPLOY}: release: redeploy changed the release "
            f"identity ({digest_before[:12]} -> {digest_after[:12]})"
        )
    if not converged:
        findings.append(
            f"{codes.NON_IDEMPOTENT_REDEPLOY}: readiness: identical redeploy did not "
            "converge to ready"
        )
    return findings


def check_drift_scan(drift_present: bool, reported_findings: int) -> list[str]:
    """§40: a scanner that sees nothing while drift exists is itself broken."""
    if drift_present and reported_findings == 0:
        return [
            f"{codes.DRIFT_IGNORED}: drift-scan: drift is present but the scanner "
            "reported a clean runtime"
        ]
    return []


def check_reset(stale_rows: int, subject: str) -> list[str]:
    """§34: reset must prove old state is gone."""
    if stale_rows:
        return [
            f"{codes.STALE_STATE_AFTER_RESET}: {subject}: {stale_rows} pre-reset row(s) "
            "survived the reset"
        ]
    return []


def scan_voting_telemetry(text: str, subject: str) -> list[str]:
    """§20/§38/§39: voting telemetry must carry no person/member/account/
    session identifiers and no application correlation ids."""
    findings: list[str] = []
    for pattern in _VOTING_IDENTITY_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(
                f"{codes.VOTING_PERSON_ID_LEAK}: {subject}: identity-shaped material "
                f"{match.group(0)!r} in voting telemetry"
            )
            break
    if _APP_CORRELATION_PATTERN.search(text):
        findings.append(
            f"{codes.VOTING_GLOBAL_CORRELATION}: {subject}: application correlation id "
            "namespace present in voting telemetry — a global key would link normal "
            "identity to voting activity"
        )
    return findings


def check_shared_observability(collected_text: str) -> list[str]:
    """§20: the shared collector must carry nothing from the voting segment."""
    if "voting-runtime-shell" in collected_text:
        return [
            f"{codes.SHARED_VOTING_OBSERVABILITY}: collected.log: voting-domain "
            "telemetry reached the shared collector"
        ]
    return []


def check_preview_dsn(dsn: str, subject: str) -> list[str]:
    """§46 / §12: preview must use a local, real PostgreSQL — never a
    production-like host and never a non-PostgreSQL engine."""
    findings: list[str] = []
    lowered = dsn.lower()
    if not lowered.startswith(("postgresql://", "postgres://")):
        findings.append(
            f"{codes.NON_POSTGRES_SUBSTITUTION}: {subject}: DSN scheme is not "
            "PostgreSQL; engine substitution is refused"
        )
        return findings
    host_part = lowered.split("@")[-1].split("/")[0].split(":")[0]
    if host_part not in ("localhost", "127.0.0.1", ""):
        for marker in _PRODUCTION_DB_MARKERS:
            if marker in host_part:
                findings.append(
                    f"{codes.PRODUCTION_DB_IN_PREVIEW}: {subject}: DSN host "
                    f"{host_part!r} looks like a production database"
                )
                return findings
        findings.append(
            f"{codes.PRODUCTION_DB_IN_PREVIEW}: {subject}: preview DSN points outside "
            f"the instance ({host_part!r}); external databases are refused"
        )
    return findings


def check_engine_version(server_version_num: str) -> list[str]:
    if not server_version_num.strip().startswith("16"):
        return [
            f"{codes.NON_POSTGRES_SUBSTITUTION}: cluster: engine version "
            f"{server_version_num!r} is not the governed PostgreSQL 16 series"
        ]
    return []


def check_post_test_bytes(digest_at_test: str, digest_at_package: str) -> list[str]:
    """§61/§62: bytes may not mutate between testing and packaging."""
    if digest_at_test != digest_at_package:
        return [
            f"{codes.POST_TEST_BYTE_MUTATION}: tree: tested digest {digest_at_test[:12]} "
            f"differs from packaged digest {digest_at_package[:12]}; "
            "tested bytes == packaged bytes is violated"
        ]
    return []


def require_refusal(refused: bool, code: str, subject: str, detail: str) -> list[str]:
    """Shared shape for handshake/trust refusal proofs: the corrupted
    handshake succeeding is the defect."""
    if not refused:
        return [f"{code}: {subject}: {detail}"]
    return []
