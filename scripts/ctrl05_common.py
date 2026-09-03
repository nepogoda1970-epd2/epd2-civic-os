#!/usr/bin/env python3
"""Shared CTRL-05 evidence helpers.

The runtime source digest binds every CTRL-05 evidence file to the exact
runtime bytes it was produced from: a gate can then refuse evidence that was
generated before the runtime changed, rather than trusting a stale result.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    "services/control-plane-service/src/epd2_control_plane_service/oversight_console.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_sources.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_api.py",
    "services/control-plane-service/src/epd2_control_plane_service/oversight_console.html",
)


def runtime_source_digest() -> str:
    """SHA-256 over the CTRL-05 runtime files, in a fixed order."""
    digest = hashlib.sha256()
    for relative in RUNTIME_FILES:
        digest.update(relative.encode())
        digest.update((ROOT / relative).read_bytes())
    return digest.hexdigest()
