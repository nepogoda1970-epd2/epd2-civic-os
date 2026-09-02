"""Freeze / same-bytes preseal identity.

`tested bytes == verified bytes == frozen bytes == packaged bytes`. The manifest
records each artifact's SHA-256 and size; `verify_manifest` recomputes them from
disk. A file changed after the manifest was written — the "candidate changed
after verification" mutation — is detected here rather than trusted.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

__all__ = ["build_manifest", "file_digest", "manifest_digest", "verify_manifest"]


def file_digest(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def build_manifest(root: Path, paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for path in sorted(paths):
        digest, size = file_digest(path)
        manifest[str(path.relative_to(root))] = {"sha256": digest, "size_bytes": size}
    return manifest


def manifest_digest(manifest: Mapping[str, Mapping[str, Any]]) -> str:
    """One digest over the whole manifest, order-independent."""
    joined = "\n".join(
        f"{name}:{entry['sha256']}:{entry['size_bytes']}"
        for name, entry in sorted(manifest.items())
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def verify_manifest(root: Path, manifest: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    """Return the list of mismatches. Empty means frozen bytes still match."""
    problems: list[str] = []
    for name, entry in sorted(manifest.items()):
        path = root / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        digest, size = file_digest(path)
        if digest != entry["sha256"]:
            problems.append(f"{name}: sha256 mismatch")
        elif size != entry["size_bytes"]:
            problems.append(f"{name}: size mismatch")
    return tuple(problems)
