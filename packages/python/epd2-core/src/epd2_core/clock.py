"""Dependency-injected clock, per CLAUDE-PACK-02 section 13.3.

Domain logic must never call system time directly - it must accept a
`Clock` so tests can be deterministic. This module only provides the
protocol and two generic implementations; it makes no domain decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """A source of the current time, injectable for deterministic tests."""

    def now(self) -> datetime:
        """Return the current time as a timezone-aware UTC `datetime`."""
        ...


class SystemClock:
    """A `Clock` backed by the real system time (UTC)."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """A `Clock` that always returns the same fixed instant.

    Intended for tests: construct with an explicit, timezone-aware
    `datetime` and every `now()` call returns it unchanged.
    """

    def __init__(self, fixed_at: datetime) -> None:
        if fixed_at.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime")
        self._fixed_at = fixed_at

    def now(self) -> datetime:
        return self._fixed_at


class SequenceClock:
    """A `Clock` that returns successive instants from a fixed sequence.

    Useful for tests that need `occurred_at` to strictly increase across
    several calls without depending on real elapsed time. Raises
    `StopIteration` if called more times than the sequence provides.
    """

    def __init__(self, instants: list[datetime]) -> None:
        for instant in instants:
            if instant.tzinfo is None:
                raise ValueError("SequenceClock requires timezone-aware datetimes")
        self._instants = list(instants)
        self._index = 0

    def now(self) -> datetime:
        if self._index >= len(self._instants):
            raise StopIteration("SequenceClock exhausted")
        value = self._instants[self._index]
        self._index += 1
        return value
