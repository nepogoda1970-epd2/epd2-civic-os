"""Tests for epd2_core.canonical_json."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from epd2_core.canonical_json import canonical_dumps


def test_key_order_does_not_affect_output() -> None:
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert canonical_dumps(a) == canonical_dumps(b)


def test_nested_structures_are_canonicalized() -> None:
    value = {"outer": {"z": 1, "a": [3, 2, {"y": 1, "x": 2}]}}
    result = canonical_dumps(value)
    assert result == canonical_dumps(value)  # deterministic across calls
    assert '"a"' in result and '"z"' in result


def test_uuid_serializes_as_string() -> None:
    value = {"id": UUID("12345678-1234-5678-1234-567812345678")}
    result = canonical_dumps(value)
    assert result == '{"id":"12345678-1234-5678-1234-567812345678"}'


def test_aware_datetime_serializes_as_isoformat() -> None:
    value = {"at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)}
    result = canonical_dumps(value)
    assert "2026-01-01T12:00:00+00:00" in result


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        canonical_dumps({"at": datetime(2026, 1, 1)})


def test_unsupported_type_is_rejected() -> None:
    class NotSerializable:
        pass

    with pytest.raises(TypeError):
        canonical_dumps({"x": NotSerializable()})


def test_two_logically_equal_but_differently_constructed_dicts_match() -> None:
    """The determinism property audit hash chaining depends on."""
    first = {}
    first["z"] = 1
    first["a"] = 2

    second = {}
    second["a"] = 2
    second["z"] = 1

    assert canonical_dumps(first) == canonical_dumps(second)
