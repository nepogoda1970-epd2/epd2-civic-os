"""Fault-hook boundary (PACK-16D §43).

The reference implementation must be testable for rollback and recovery at
eleven named points without importing test code into the production path.
The compromise is this module: production code depends only on a
:class:`FaultHook` protocol and calls it through :func:`trip`, which is a
no-op when no hook is installed. The *only* implementation that raises is
``reference.testing.faults.FaultInjector``, which lives under ``testing``
and is never constructed by production code.

There is no global registry and no environment switch. A hook can only be
installed by passing it explicitly into a call, so a deployed system that
never passes one cannot have a fault injected into it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FaultHook(Protocol):
    """Anything that can be asked to fail at a named point."""

    def trip(self, point: str) -> None:
        """Raise if this point is armed. Return ``None`` otherwise."""


def trip(hook: FaultHook | None, point: str) -> None:
    """Call ``hook`` if one was supplied. A missing hook is not an error."""
    if hook is not None:
        hook.trip(point)
