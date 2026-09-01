"""Candidate packaging and package verification (INFRA01-HI-02 / HI-06).

``build_archive`` writes exactly the frozen inventory plus the governed
additions from the canonical allowlist, verifying each staged member against
the freeze digest *as it is written*. ``verify_archive_against_inventory``
independently proves, from the archive side, that packaged bytes equal frozen
bytes, that no member is undeclared and that no frozen member is missing.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance import codes
from scripts.acceptance.canonical import sha256_bytes, sha256_file
from scripts.acceptance.freeze import FreezeInventory
from scripts.acceptance.hygiene import HygieneFinding, load_allowlist


@dataclass(frozen=True)
class PackageResult:
    archive: Path
    archive_sha256: str
    member_count: int
    findings: list[HygieneFinding]


def build_archive(
    root: Path,
    inventory: FreezeInventory,
    archive: Path,
    archive_root: str,
    governed_additions: dict[str, bytes],
    allowlist: dict[str, list[str]] | None = None,
) -> PackageResult:
    """Package the frozen inventory; refuse on any staged-byte mismatch."""
    resolved = allowlist or load_allowlist()
    allowed_additions = set(resolved["governed_additions"])
    findings: list[HygieneFinding] = []

    undeclared = sorted(set(governed_additions) - allowed_additions)
    for rel in undeclared:
        findings.append(
            HygieneFinding(
                codes.UNDECLARED_ARCHIVE_ENTRY,
                rel,
                "addition is not in the canonical governed allowlist",
            )
        )
    if findings:
        return PackageResult(archive, "", 0, findings)

    archive.parent.mkdir(parents=True, exist_ok=True)
    member_count = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for rel, frozen_digest in sorted(inventory.files.items()):
            source = root / rel
            data = source.read_bytes()
            staged_digest = sha256_bytes(data)
            if staged_digest != frozen_digest:
                findings.append(
                    HygieneFinding(
                        codes.TREE_MUTATION_AFTER_FREEZE,
                        rel,
                        f"bytes changed between freeze and packaging: "
                        f"{frozen_digest} -> {staged_digest}",
                    )
                )
                continue
            bundle.writestr(f"{archive_root}/{rel}", data)
            member_count += 1
        for rel, data in sorted(governed_additions.items()):
            bundle.writestr(f"{archive_root}/{rel}", data)
            member_count += 1
    if findings:
        archive.unlink(missing_ok=True)
        return PackageResult(archive, "", 0, findings)
    return PackageResult(archive, sha256_file(archive), member_count, findings)


def verify_archive_against_inventory(
    archive: Path,
    archive_root: str,
    inventory: FreezeInventory,
    allowlist: dict[str, list[str]] | None = None,
) -> list[HygieneFinding]:
    """Independent archive-side proof that packaged bytes == frozen bytes."""
    resolved = allowlist or load_allowlist()
    allowed_additions = set(resolved["governed_additions"])
    findings: list[HygieneFinding] = []
    prefix = f"{archive_root}/"

    with zipfile.ZipFile(archive) as bundle:
        members: dict[str, str] = {}
        for info in bundle.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not name.startswith(prefix):
                findings.append(
                    HygieneFinding(codes.UNSAFE_ARCHIVE_PATH, name, "member outside candidate root")
                )
                continue
            rel = name[len(prefix) :]
            members[rel] = sha256_bytes(bundle.read(info))

    for rel, digest in sorted(members.items()):
        expected = inventory.files.get(rel)
        if expected is None:
            if rel not in allowed_additions:
                findings.append(
                    HygieneFinding(
                        codes.UNDECLARED_ARCHIVE_ENTRY,
                        rel,
                        "archive member neither frozen nor governed addition",
                    )
                )
            continue
        if digest != expected:
            findings.append(
                HygieneFinding(
                    codes.ARCHIVE_BYTE_MISMATCH,
                    rel,
                    f"archive bytes {digest} do not equal frozen bytes {expected}",
                )
            )
    for rel in sorted(set(inventory.files) - set(members)):
        findings.append(
            HygieneFinding(codes.MISSING_ARCHIVE_ENTRY, rel, "frozen file absent from archive")
        )
    return findings
