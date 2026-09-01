"""Frozen/reference evidence integrity (INFRA01-HI-07).

Accepted frozen artifacts are immutable inputs. Their exact accepted SHA-256
digests are pinned in ``frozen_artifacts.json`` and verified at five
lifecycle boundaries: before testing, after testing, before packaging,
during packaging (against the staged bytes) and against the bytes inside the
produced archive. A deliberate one-byte mutation at any of those points
causes refusal with :data:`codes.FROZEN_ARTIFACT_MISMATCH`.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json, sha256_bytes, sha256_file

PIN_FILE = Path(__file__).resolve().parent / "frozen_artifacts.json"


@dataclass(frozen=True)
class FrozenFinding:
    code: str
    path: str
    detail: str


def load_pins(pin_file: Path = PIN_FILE) -> dict[str, str]:
    document = load_json(pin_file)
    pins: dict[str, str] = {}
    for entry in document["artifacts"]:
        pins[str(entry["path"])] = str(entry["sha256"])
    if not pins:
        raise ValueError(f"frozen-artifact pin list is empty: {pin_file}")
    return pins


def verify_tree(root: Path, pins: dict[str, str] | None = None) -> list[FrozenFinding]:
    """Verify every pinned artifact inside a working tree."""
    findings: list[FrozenFinding] = []
    for rel_path, expected in sorted((pins or load_pins()).items()):
        target = root / rel_path
        if not target.is_file():
            findings.append(
                FrozenFinding(codes.FROZEN_ARTIFACT_MISSING, rel_path, "pinned artifact missing")
            )
            continue
        actual = sha256_file(target)
        if actual != expected:
            findings.append(
                FrozenFinding(
                    codes.FROZEN_ARTIFACT_MISMATCH,
                    rel_path,
                    f"expected {expected}, found {actual}",
                )
            )
    return findings


def verify_archive(
    archive: Path, archive_root: str, pins: dict[str, str] | None = None
) -> list[FrozenFinding]:
    """Verify every pinned artifact against the bytes inside an archive."""
    findings: list[FrozenFinding] = []
    resolved_pins = pins or load_pins()
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        for rel_path, expected in sorted(resolved_pins.items()):
            member = f"{archive_root}/{rel_path}" if archive_root else rel_path
            if member not in names:
                findings.append(
                    FrozenFinding(
                        codes.FROZEN_ARTIFACT_MISSING, rel_path, "pinned artifact absent in archive"
                    )
                )
                continue
            actual = sha256_bytes(bundle.read(member))
            if actual != expected:
                findings.append(
                    FrozenFinding(
                        codes.FROZEN_ARTIFACT_MISMATCH,
                        rel_path,
                        f"archive bytes {actual} do not match accepted {expected}",
                    )
                )
    return findings
