"""Tests for epd2_core.clock."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from epd2_core.clock import FixedClock, SequenceClock, SystemClock


def test_system_clock_returns_timezone_aware_datetime() -> None:
    result = SystemClock().now()
    assert result.tzinfo is not None


def test_fixed_clock_always_returns_same_instant() -> None:
    fixed_at = datetime(2026, 1, 1, tzinfo=UTC)
    clock = FixedClock(fixed_at)
    assert clock.now() == fixed_at
    assert clock.now() == fixed_at


def test_fixed_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 1, 1))


def test_sequence_clock_returns_instants_in_order() -> None:
    first = datetime(2026, 1, 1, tzinfo=UTC)
    second = datetime(2026, 1, 2, tzinfo=UTC)
    clock = SequenceClock([first, second])
    assert clock.now() == first
    assert clock.now() == second


def test_sequence_clock_raises_when_exhausted() -> None:
    clock = SequenceClock([datetime(2026, 1, 1, tzinfo=UTC)])
    clock.now()
    with pytest.raises(StopIteration):
        clock.now()


def test_sequence_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SequenceClock([datetime(2026, 1, 1)])
