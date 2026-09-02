from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/api06"))

from run_api06_mutations import run_mutations  # noqa: E402


def test_all_thirty_governed_mutations_are_detected():
    result = run_mutations()
    assert result["result"] == "PASS"
    assert result["detected"] == result["mutation_count"] == 30
    assert result["missed"] == 0
