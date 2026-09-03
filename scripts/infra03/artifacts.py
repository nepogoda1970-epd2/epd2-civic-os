"""Immutable artifact identity and supply-chain handoff (INFRA03 §9, §49).

The chain proven for every deployment::

    approved artifact digest == deployed artifact digest == observed runtime digest

- *approved*: the SHA-256 and freeze-tree digest recorded in the INFRA-02
  acceptance record on canonical ``main`` (the supply-chain handoff);
- *deployed*: recomputed from the exact bytes staged for deployment — the
  candidate ZIP is hashed before extraction, and the extracted source tree's
  digest is recomputed with the same convention the acceptance harness uses
  (``sha256`` over ``path \\0 sha256(bytes) \\n`` in sorted path order);
- *observed*: each running service recomputes the digest of the application
  root it actually serves and reports it on its ``/identity`` endpoint; the
  supervisor compares.

Mutable references, local rebuild substitution and digest drift fail closed
(:data:`codes.MUTABLE_ARTIFACT_REFERENCE`,
:data:`codes.LOCAL_REBUILD_SUBSTITUTION`,
:data:`codes.ARTIFACT_DIGEST_MISMATCH`). A predecessor record that does not
match the exact accepted identity is :data:`codes.STALE_PREDECESSOR`.
"""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance.canonical import sha256_file
from scripts.infra03 import PREDECESSOR, codes

#: Non-source members of a sealed candidate archive (generated packaging
#: metadata); the freeze tree digest covers everything else.
PACKAGING_MEMBERS = ("SHA256SUMS.txt", "ACCEPTANCE/FREEZE-INVENTORY.json")


@dataclass(frozen=True)
class ArtifactFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def tree_digest_of_directory(root: Path) -> str:
    """The canonical tree digest over every file under ``root``."""
    entries: list[tuple[str, str]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        entries.append((rel, sha256_file(path)))
    payload = b"".join(
        rel.encode() + b"\0" + digest.encode() + b"\n" for rel, digest in sorted(entries)
    )
    return hashlib.sha256(payload).hexdigest()


def verify_approved_artifact(artifact_zip: Path) -> list[ArtifactFinding]:
    """The staged ZIP bytes must be the exact accepted predecessor (§49)."""
    if not artifact_zip.is_file():
        return [
            ArtifactFinding(
                codes.SUPPLY_CHAIN_HANDOFF_BYPASSED,
                str(artifact_zip),
                "approved artifact not staged; deployment without the supply-chain "
                "handoff is refused",
            )
        ]
    actual = sha256_file(artifact_zip)
    if actual != PREDECESSOR["zip_sha256"]:
        return [
            ArtifactFinding(
                codes.ARTIFACT_DIGEST_MISMATCH,
                artifact_zip.name,
                f"staged artifact digest {actual} is not the approved accepted "
                f"digest {PREDECESSOR['zip_sha256']}; mutable or substituted bytes "
                "are refused",
            )
        ]
    size = artifact_zip.stat().st_size
    if size != PREDECESSOR["size_bytes"]:
        return [
            ArtifactFinding(
                codes.ARTIFACT_DIGEST_MISMATCH,
                artifact_zip.name,
                f"staged artifact size {size} differs from accepted {PREDECESSOR['size_bytes']}",
            )
        ]
    return []


def deploy_artifact(artifact_zip: Path, deploy_dir: Path) -> tuple[str, list[ArtifactFinding]]:
    """Extract the approved artifact and prove the deployed tree digest.

    Returns (deployed source tree digest, findings). The digest must equal
    the acceptance record's freeze tree digest — a local rebuild or a
    tampered extraction cannot reproduce it.
    """
    findings = verify_approved_artifact(artifact_zip)
    if findings:
        return "", findings
    deploy_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact_zip) as bundle:
        for info in bundle.infolist():
            if info.is_dir():
                continue
            name = info.filename
            rel = name.split("/", 1)[1] if "/" in name else name
            if rel in PACKAGING_MEMBERS:
                continue
            if rel.startswith("/") or ".." in rel.split("/"):
                return "", [
                    ArtifactFinding(
                        codes.ARTIFACT_DIGEST_MISMATCH, rel, "unsafe member path in artifact"
                    )
                ]
            target = deploy_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(info))
    digest = tree_digest_of_directory(deploy_dir)
    if digest != PREDECESSOR["freeze_tree_digest"]:
        findings.append(
            ArtifactFinding(
                codes.LOCAL_REBUILD_SUBSTITUTION,
                str(deploy_dir),
                f"deployed tree digest {digest} does not reproduce the accepted "
                f"freeze tree digest {PREDECESSOR['freeze_tree_digest']}; the deployed "
                "content is not the approved artifact",
            )
        )
        return digest, findings
    return digest, []


def verify_observed_digest(observed: str, subject: str) -> list[ArtifactFinding]:
    """The digest a running service reports must be the approved one."""
    if observed != PREDECESSOR["freeze_tree_digest"]:
        return [
            ArtifactFinding(
                codes.ARTIFACT_DIGEST_MISMATCH,
                subject,
                f"observed runtime digest {observed!r} differs from the approved "
                f"{PREDECESSOR['freeze_tree_digest']}",
            )
        ]
    return []


def verify_predecessor_record(record: dict[str, object]) -> list[ArtifactFinding]:
    """G03: the acceptance-record identity used must be the exact one (§4)."""
    findings: list[ArtifactFinding] = []
    raw = record.get("candidate")
    candidate: dict[str, object] = raw if isinstance(raw, dict) else {}
    checks = (
        ("sha256", PREDECESSOR["zip_sha256"]),
        ("size_bytes", PREDECESSOR["size_bytes"]),
        ("freeze_tree_digest", PREDECESSOR["freeze_tree_digest"]),
    )
    for field, expected in checks:
        actual = candidate.get(field)
        if actual != expected:
            findings.append(
                ArtifactFinding(
                    codes.STALE_PREDECESSOR,
                    f"candidate.{field}",
                    f"acceptance record carries {actual!r}, governed predecessor is "
                    f"{expected!r}; a stale predecessor cannot enter deployment",
                )
            )
    if str(record.get("decision", "")).upper() not in ("ACCEPTED / CLOSED", "ACCEPTED/CLOSED"):
        findings.append(
            ArtifactFinding(
                codes.STALE_PREDECESSOR,
                "decision",
                f"predecessor record decision {record.get('decision')!r} is not an acceptance",
            )
        )
    return findings
