"""Central invariant guard (PACK-16D §45).

Feature flags exist in this repository, and PACK-16D must make it
structurally impossible for one to switch off a security property. The
mechanism is deliberately blunt: a fixed frozenset of invariant names that
no flag may address, checked once at startup. An attempt to override one
does not degrade to a warning and does not fall back to the safe value —
it fails startup.

The guard is a *name* guard, not a behaviour guard. It stops a flag from
reaching the code path at all; it cannot prove that the code path behind
the name is correct. That is what the invariant tests are for, and the
distinction is stated here rather than left implicit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

#: Invariants no feature flag may weaken, disable, bypass or reconfigure.
IMMUTABLE_INVARIANTS: frozenset[str] = frozenset(
    {
        "parameter_validation",
        "proof_verification",
        "capability_limits",
        "atomic_acceptance",
        "batch_reservation",
        "batch_shape",
        "no_intermediate_tally",
        "receipt_semantics",
        "identity_separation",
        "event_privacy",
    }
)

#: Flags the reference implementation is permitted to read at all.
PERMITTED_FLAGS: frozenset[str] = frozenset(
    {
        "reference_api_enabled",
        "verbose_verification_output",
        "batch_seal_dry_run",
    }
)


class UnsafeFeatureFlagError(RuntimeError):
    """A flag addressed an immutable invariant. Startup must not continue."""

    reason_code = "CONFIGURATION_REJECTED"


class UnknownFeatureFlagError(RuntimeError):
    """A flag outside the permitted set. Fail closed rather than ignore."""

    reason_code = "CONFIGURATION_REJECTED"


@dataclass(frozen=True, slots=True)
class FeatureFlags:
    """An immutable, validated flag set.

    Construct through :meth:`load`; the constructor is not a validation
    boundary and must not be treated as one.
    """

    values: tuple[tuple[str, bool], ...] = ()

    def get(self, name: str) -> bool:
        for key, value in self.values:
            if key == name:
                return value
        return False

    @classmethod
    def load(cls, candidate: Mapping[str, bool]) -> FeatureFlags:
        """Validate and freeze. Raises before returning anything usable."""
        for name in candidate:
            normalized = name.strip().lower().replace("-", "_")
            # A flag may not address an invariant under any prefix or suffix:
            # ``disable_no_intermediate_tally`` is the same attack as
            # ``no_intermediate_tally``.
            for invariant in IMMUTABLE_INVARIANTS:
                if invariant in normalized:
                    raise UnsafeFeatureFlagError(
                        f"feature flag {name!r} addresses immutable invariant "
                        f"{invariant!r}; startup refused"
                    )
            if normalized not in PERMITTED_FLAGS:
                raise UnknownFeatureFlagError(
                    f"feature flag {name!r} is not in the permitted set; startup refused"
                )
        return cls(tuple(sorted((k, bool(v)) for k, v in candidate.items())))


def enforce_startup_invariants(candidate: Mapping[str, bool]) -> FeatureFlags:
    """The single startup entry point. Any caller that skips it is a defect."""
    return FeatureFlags.load(candidate)
