"""Secret-leakage hard gate (INFRA01-HI-08, foundation for FIR-SEC-SECRET-001).

Deterministic pattern-based scanning of (1) the current governed source tree,
(2) generated/distribution material staged for packaging, (3) the bytes of
the final candidate archive, and (4) persisted CI evidence before it is
bundled (sanitation).

Allowlisting is central and narrow: every permitted finding is declared in
``secret_allowlist.json`` with the exact file path, detector, SHA-256 of the
matching line and an evidence-backed classification (synthetic test material
or intentionally public reference material). There is no inline-comment
bypass mechanism, and no broad path or pattern exemption. An unlisted match
is a hard FAIL with :data:`codes.SECRET_DETECTED`.

The design deliberately scans *content handed to it* rather than Git history;
the same detector set can later be pointed at every publishable historical
ref to satisfy the full public-release criteria of ``FIR-SEC-SECRET-001``.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json, sha256_bytes

ALLOWLIST_FILE = Path(__file__).resolve().parent / "secret_allowlist.json"

#: (detector id, compiled pattern). Patterns are anchored to realistic token
#: shapes so that governed public cryptographic reference material (hex
#: digests, public keys, NIZK artifacts) does not trip the gate — a public
#: value is not a secret merely because it is cryptographic.
DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key-block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY( BLOCK)?-----")),
    ("aws-access-key-id", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "github-token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}\b|github_pat_[A-Za-z0-9_]{60,}"),
    ),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9][A-Za-z0-9-]{9,}\b")),
    ("stripe-live-key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    (
        "signed-jwt",
        re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{16,}\b"),
    ),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(password|passwd|client_secret|api_key|apikey|auth_token|access_token"
            r"|refresh_token|database_url)\b\s*[:=]\s*[\"'](?!\s*$)[^\"']{8,}[\"']"
        ),
    ),
)

#: Additional detectors applied to persisted CI evidence before bundling.
SANITATION_DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("authorization-header", re.compile(r"(?i)\bauthorization:\s*(bearer|basic)\s+[^\s*]{8,}")),
    ("set-cookie-header", re.compile(r"(?i)\bset-cookie:\s*\S+=\S{8,}")),
    ("proxy-credentials", re.compile(r"://[^/\s:]+:[^@\s/]{4,}@")),
)

_TEXT_PROBE_BYTES = 8000
_MAX_SCAN_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class SecretFinding:
    code: str
    path: str
    detector: str
    line_number: int
    line_sha256: str

    def describe(self) -> str:
        return (
            f"{self.code}: {self.path}:{self.line_number} detector={self.detector} "
            f"line_sha256={self.line_sha256}"
        )


def load_allowlist(allowlist_file: Path = ALLOWLIST_FILE) -> set[tuple[str, str, str]]:
    """Return the allow set of (path, detector, line_sha256) triples."""
    document = load_json(allowlist_file)
    allowed: set[tuple[str, str, str]] = set()
    for entry in document["entries"]:
        classification = str(entry["classification"])
        if classification not in {"synthetic-test-material", "intentionally-public-reference"}:
            raise ValueError(f"ungoverned allowlist classification: {classification}")
        allowed.add((str(entry["path"]), str(entry["detector"]), str(entry["line_sha256"])))
    return allowed


def _looks_binary(data: bytes) -> bool:
    return b"\0" in data[:_TEXT_PROBE_BYTES]


def scan_bytes(
    rel_path: str,
    data: bytes,
    allowed: set[tuple[str, str, str]],
    detectors: tuple[tuple[str, re.Pattern[str]], ...] = DETECTORS,
    code: str = codes.SECRET_DETECTED,
) -> list[SecretFinding]:
    if _looks_binary(data) or len(data) > _MAX_SCAN_BYTES:
        return []
    findings: list[SecretFinding] = []
    text = data.decode("utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for detector, pattern in detectors:
            if pattern.search(line):
                line_digest = sha256_bytes(line.strip().encode("utf-8"))
                if (rel_path, detector, line_digest) in allowed:
                    continue
                findings.append(SecretFinding(code, rel_path, detector, line_number, line_digest))
    return findings


def scan_files(
    root: Path,
    rel_paths: list[str],
    allowed: set[tuple[str, str, str]] | None = None,
) -> list[SecretFinding]:
    """Scan a list of files (relative to ``root``) — the tree/staging scan."""
    allow = load_allowlist() if allowed is None else allowed
    findings: list[SecretFinding] = []
    for rel in sorted(rel_paths):
        target = root / rel
        if not target.is_file():
            continue
        findings.extend(scan_bytes(rel, target.read_bytes(), allow))
    return findings


def scan_archive(
    archive: Path, allowed: set[tuple[str, str, str]] | None = None
) -> list[SecretFinding]:
    """Scan the actual bytes inside a produced candidate archive."""
    allow = load_allowlist() if allowed is None else allowed
    findings: list[SecretFinding] = []
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            if info.is_dir():
                continue
            rel = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename
            findings.extend(scan_bytes(rel, bundle.read(info), allow))
    return findings


def sanitize_evidence(
    evidence_root: Path, allowed: set[tuple[str, str, str]] | None = None
) -> list[SecretFinding]:
    """Sanitation gate for persisted CI evidence (logs, manifests, bundles)."""
    allow = load_allowlist() if allowed is None else allowed
    findings: list[SecretFinding] = []
    for path in sorted(p for p in evidence_root.rglob("*") if p.is_file()):
        rel = path.relative_to(evidence_root).as_posix()
        data = path.read_bytes()
        findings.extend(scan_bytes(rel, data, allow))
        findings.extend(
            scan_bytes(
                rel,
                data,
                allow,
                detectors=SANITATION_DETECTORS,
                code=codes.EVIDENCE_SANITATION_FAILURE,
            )
        )
    return findings
