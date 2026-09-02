"""Test configuration for `control-plane-service`.

Puts this directory on `sys.path` so the sibling `_control_plane_builders`
module can be imported as a plain top-level module, following the precedent of
the other services. The helper is named distinctly rather than `_builders` so
that it cannot shadow another service's helper of that name during a
whole-repository collection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from _control_plane_builders import World, build_world  # noqa: E402


@pytest.fixture
def world() -> World:
    return build_world()
