"""pytest configuration for the identity-service test suite.

Puts this directory on `sys.path` so `_pack14_builders` imports as a
plain top-level module, matching the pattern every earlier pack's service
suite uses under `--import-mode=importlib`.
"""

from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent.resolve()

if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
