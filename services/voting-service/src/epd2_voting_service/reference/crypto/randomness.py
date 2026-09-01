"""Randomness architecture (PACK-16B `RB-*`, PACK-16D §15).

Two sources exist and they cannot be confused:

* :class:`ProductionRandomSource` draws from the OS CSPRNG and fails
  closed if that is unavailable. It has no seed parameter at all, so no
  caller can accidentally make it deterministic.
* :class:`DeterministicTestRandomSource` is seeded, reproducible, and
  refuses to construct unless the process is explicitly in a test profile.

`select_source` is the only factory production code may call, and it can
never return the deterministic source.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Protocol, runtime_checkable

TEST_PROFILE_ENV = "EPD2_VOTING_REFERENCE_TEST_PROFILE"


class RandomnessUnavailableError(RuntimeError):
    """The OS CSPRNG failed. Fail closed: never fall back to a weaker source."""

    reason_code = "CRYPTO_RANDOMNESS_UNAVAILABLE"


class DeterministicSourceForbiddenError(RuntimeError):
    """A deterministic source was requested outside a test profile."""

    reason_code = "CRYPTO_TEST_MODE_REACHABLE"


@runtime_checkable
class RandomSource(Protocol):
    """The only randomness interface cryptographic code may depend on."""

    is_deterministic: bool

    def random_bytes(self, count: int) -> bytes: ...

    def random_below(self, bound: int) -> int: ...


class ProductionRandomSource:
    """OS CSPRNG. No seed, no fallback, no reseed hook."""

    is_deterministic = False

    def random_bytes(self, count: int) -> bytes:
        if count <= 0:
            raise ValueError("count must be positive")
        try:
            raw = secrets.token_bytes(count)
        except Exception as exc:  # pragma: no cover - OS CSPRNG failure
            raise RandomnessUnavailableError("OS CSPRNG unavailable") from exc
        if len(raw) != count:  # pragma: no cover - defensive
            raise RandomnessUnavailableError("OS CSPRNG returned short read")
        return raw

    def random_below(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("bound must be positive")
        # Rejection sampling over whole bytes rather than ``secrets.randbelow``
        # so that this method fails closed through the same path as
        # ``random_bytes``. A CSPRNG failure here must not surface as a bare
        # OSError from deep inside the stdlib.
        width = (bound.bit_length() + 7) // 8
        limit = (256**width // bound) * bound
        while True:
            candidate = int.from_bytes(self.random_bytes(width), "big")
            if candidate < limit:
                return candidate % bound


class DeterministicTestRandomSource:
    """Seeded, reproducible, test-only.

    Construction requires `allow_in_test=True` **and** the test-profile
    environment marker. Both are required so that neither a stray keyword
    argument nor a stray environment variable is enough on its own.
    """

    is_deterministic = True

    def __init__(self, seed: bytes, *, allow_in_test: bool = False) -> None:
        if not allow_in_test:
            raise DeterministicSourceForbiddenError(
                "DeterministicTestRandomSource requires allow_in_test=True"
            )
        if os.environ.get(TEST_PROFILE_ENV) != "1":
            raise DeterministicSourceForbiddenError(
                f"DeterministicTestRandomSource requires {TEST_PROFILE_ENV}=1"
            )
        if not seed:
            raise ValueError("seed must be non-empty")
        self._seed = seed
        self._counter = 0

    def random_bytes(self, count: int) -> bytes:
        if count <= 0:
            raise ValueError("count must be positive")
        out = bytearray()
        while len(out) < count:
            block = hashlib.sha256(self._seed + self._counter.to_bytes(8, "big")).digest()
            self._counter += 1
            out.extend(block)
        return bytes(out[:count])

    def random_below(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("bound must be positive")
        width = (bound.bit_length() + 7) // 8 + 8
        return int.from_bytes(self.random_bytes(width), "big") % bound


def select_source(profile: str) -> RandomSource:
    """The only factory production code calls.

    It returns a production source for every profile name it accepts, and
    raises for anything else. There is no profile string that yields a
    deterministic source, which is what makes `test_rng_unreachable`
    provable rather than merely asserted.
    """
    if profile != "production":
        raise DeterministicSourceForbiddenError(
            f"select_source accepts only 'production', got {profile!r}"
        )
    return ProductionRandomSource()
