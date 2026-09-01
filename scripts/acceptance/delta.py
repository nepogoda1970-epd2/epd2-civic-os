"""Deterministic exact-delta accounting between sealed candidates (INFRA-01 C2).

INFRA01-C2-01: an "exact" inventory that omits changed paths is objectively
false. This module recomputes the ``added / modified / removed / unchanged``
delta from **archive bytes** — never from a pre-package source tree — and
verifies a declared inventory against it, comparing both path membership and
declared counts. Any divergence, including an omitted packaging-metadata
path such as ``SHA256SUMS.txt`` or ``ACCEPTANCE/FREEZE-INVENTORY.json``, is
a fail-closed :data:`codes.CORRECTION_INVENTORY_MISMATCH`.

Self-referential generated files (the inventory document itself, packaging
checksum metadata) may be *classified* as ``modified_or_self`` /
``generated_metadata`` but may never be omitted from counts or path
accounting.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.acceptance import codes
from scripts.acceptance.canonical import sha256_bytes


@dataclass(frozen=True)
class DeltaFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


@dataclass(frozen=True)
class ArchiveDelta:
    added: tuple[str, ...]
    modified: tuple[str, ...]
    removed: tuple[str, ...]
    unchanged: tuple[str, ...]

    def counts(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "modified": len(self.modified),
            "removed": len(self.removed),
            "unchanged": len(self.unchanged),
        }


def archive_file_hashes(archive: Path) -> dict[str, str]:
    """Map of root-stripped member path to SHA-256 of the member bytes."""
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            if info.is_dir():
                continue
            name = info.filename
            rel = name.split("/", 1)[1] if "/" in name else name
            hashes[rel] = sha256_bytes(bundle.read(info))
    return hashes


def compute_delta(predecessor: dict[str, str], candidate: dict[str, str]) -> ArchiveDelta:
    """Exact path delta between two byte-hash maps; every path accounted."""
    added: list[str] = []
    modified: list[str] = []
    removed: list[str] = []
    unchanged: list[str] = []
    for rel in sorted(set(predecessor) | set(candidate)):
        if rel not in predecessor:
            added.append(rel)
        elif rel not in candidate:
            removed.append(rel)
        elif predecessor[rel] != candidate[rel]:
            modified.append(rel)
        else:
            unchanged.append(rel)
    return ArchiveDelta(tuple(added), tuple(modified), tuple(removed), tuple(unchanged))


def _declared_paths(document: dict[str, Any], keys: tuple[str, ...]) -> set[str]:
    paths: set[str] = set()
    for key in keys:
        value = document.get(key, [])
        if isinstance(value, list):
            paths.update(str(item) for item in value)
    return paths


def verify_inventory(
    document: dict[str, Any],
    predecessor: dict[str, str],
    candidate: dict[str, str],
) -> list[DeltaFinding]:
    """Verify a declared exact inventory against recomputed archive deltas.

    Declared "modified" membership may be split across the keys
    ``modified``, ``modified_or_self`` and ``generated_metadata`` —
    classification is free, omission is not.
    """
    findings: list[DeltaFinding] = []
    actual = compute_delta(predecessor, candidate)

    declared = {
        "added": _declared_paths(document, ("added",)),
        "modified": _declared_paths(
            document, ("modified", "modified_or_self", "generated_metadata")
        ),
        "removed": _declared_paths(document, ("removed",)),
    }
    actual_sets = {
        "added": set(actual.added),
        "modified": set(actual.modified),
        "removed": set(actual.removed),
    }
    for kind in ("added", "modified", "removed"):
        for missing in sorted(actual_sets[kind] - declared[kind]):
            findings.append(
                DeltaFinding(
                    codes.CORRECTION_INVENTORY_MISMATCH,
                    missing,
                    f"path is {kind} between the exact archives but omitted from the "
                    "declared inventory — 'exact' accounting admits no exclusions",
                )
            )
        for phantom in sorted(declared[kind] - actual_sets[kind]):
            findings.append(
                DeltaFinding(
                    codes.CORRECTION_INVENTORY_MISMATCH,
                    phantom,
                    f"path declared {kind} but the exact archives do not support it",
                )
            )

    raw_counts = document.get("counts", {})
    declared_counts = (
        {
            key: int(value)
            for key, value in raw_counts.items()
            if isinstance(value, (int, float))
            and key in ("added", "modified", "removed", "unchanged")
        }
        if isinstance(raw_counts, dict)
        else {}
    )
    actual_counts = actual.counts()
    for key, actual_value in actual_counts.items():
        declared_value = declared_counts.get(key)
        if declared_value != actual_value:
            findings.append(
                DeltaFinding(
                    codes.CORRECTION_INVENTORY_MISMATCH,
                    f"counts.{key}",
                    f"declared {declared_value!r}, measured {actual_value} from archive bytes",
                )
            )
    return findings


def verify_inventory_between_archives(
    inventory_path: Path, predecessor_zip: Path, candidate_zip: Path
) -> list[DeltaFinding]:
    from scripts.acceptance.canonical import load_json

    document = load_json(inventory_path)
    if not isinstance(document, dict):
        return [
            DeltaFinding(
                codes.CORRECTION_INVENTORY_MISMATCH,
                inventory_path.name,
                "inventory document is not an object",
            )
        ]
    return verify_inventory(
        document, archive_file_hashes(predecessor_zip), archive_file_hashes(candidate_zip)
    )
