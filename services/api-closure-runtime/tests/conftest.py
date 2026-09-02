from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "services/api-closure-runtime/src"
sys.path.insert(0, str(SRC))
