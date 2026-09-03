#!/usr/bin/env python3
"""Shared CTRL-04 evidence helpers: the runtime source digest that binds every
evidence file to the exact runtime bytes it was produced from."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    "services/control-plane-service/src/epd2_control_plane_service/operations_console.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_adapters.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_api.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_console.html",
)


def runtime_source_digest() -> str:
    """SHA-256 over the CTRL-04 runtime files, in a fixed order."""
    digest = hashlib.sha256()
    for relative in RUNTIME_FILES:
        digest.update(relative.encode())
        digest.update((ROOT / relative).read_bytes())
    return digest.hexdigest()
