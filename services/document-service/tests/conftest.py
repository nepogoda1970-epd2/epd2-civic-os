"""Test configuration for `document-service`.

Puts this directory on `sys.path` so the sibling `_builders` module can be
imported as a plain top-level module, without requiring `__init__.py`
files in the tests directory.

This mirrors `tests/contract/conftest.py`'s own precedent and exists for
the same reason: the repository runs pytest with
`--import-mode=importlib` (see the root `pyproject.toml`), which resolves
same-named test files across services by full path but does not make
sibling helper modules importable on its own.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
