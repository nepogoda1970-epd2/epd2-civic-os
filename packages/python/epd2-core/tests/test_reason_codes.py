"""Tests for epd2_core.reason_codes.

Requires PyYAML. Skips (not fails) if it is not installed - this sandbox
cannot install it without network access (see LOCAL_VERIFICATION.md); CI
(.github/workflows/verify-and-package.yml) has it installed via
`uv sync --all-groups` and runs these for real.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from epd2_core.reason_codes import (  # noqa: E402
    InvalidReasonCodeRegistryError,
    ReasonCodeRegistry,
    UnknownReasonCodeError,
)

_VALID_ENTRY = {
    "code": "TEST_CODE",
    "meaning": "Used only in tests",
    "severity": "error",
    "description": "A reason code used only by this test module.",
    "retryable": False,
    "owner": "test-owner",
    "introduced_in_version": "0.1.0",
}


def _write_yaml(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    path = tmp_path / "codes.yml"
    path.write_text(yaml.safe_dump(entries), encoding="utf-8")
    return path


def test_load_and_require_known_code(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, [_VALID_ENTRY])
    registry = ReasonCodeRegistry.load_from_yaml(path)
    code = registry.require("TEST_CODE")
    assert code.severity == "error"
    assert code.retryable is False
    assert "TEST_CODE" in registry
    assert registry.all_codes() == ("TEST_CODE",)


def test_require_unknown_code_raises(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, [_VALID_ENTRY])
    registry = ReasonCodeRegistry.load_from_yaml(path)
    with pytest.raises(UnknownReasonCodeError):
        registry.require("NOT_REGISTERED")


def test_get_unknown_code_returns_none(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, [_VALID_ENTRY])
    registry = ReasonCodeRegistry.load_from_yaml(path)
    assert registry.get("NOT_REGISTERED") is None


def test_duplicate_code_is_rejected(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, [_VALID_ENTRY, _VALID_ENTRY])
    with pytest.raises(InvalidReasonCodeRegistryError, match="duplicate"):
        ReasonCodeRegistry.load_from_yaml(path)


def test_missing_field_is_rejected(tmp_path: Path) -> None:
    incomplete = dict(_VALID_ENTRY)
    del incomplete["owner"]
    path = _write_yaml(tmp_path, [incomplete])
    with pytest.raises(InvalidReasonCodeRegistryError, match="missing fields"):
        ReasonCodeRegistry.load_from_yaml(path)


def test_invalid_severity_is_rejected(tmp_path: Path) -> None:
    bad = dict(_VALID_ENTRY)
    bad["severity"] = "catastrophic"
    path = _write_yaml(tmp_path, [bad])
    with pytest.raises(InvalidReasonCodeRegistryError, match="severity"):
        ReasonCodeRegistry.load_from_yaml(path)


def test_non_list_top_level_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "codes.yml"
    path.write_text(yaml.safe_dump({"not": "a list"}), encoding="utf-8")
    with pytest.raises(InvalidReasonCodeRegistryError, match="top-level YAML list"):
        ReasonCodeRegistry.load_from_yaml(path)
