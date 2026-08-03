"""Finite capacity plan (PACK-16C `TC-59`..`TC-77`, PACK-16D §27).

`L_max = E * (K + A)`, computed from the maximum number of **valid
continuation capabilities**, never from expected or plausible turnout.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

K_PUBLIC_CHALLENGES_PER_CONTINUATION = 1
A_ACCEPTED_CASTS_PER_CONTINUATION = 1


class SlotClass(StrEnum):
    CAST_RESERVED = "cast_reserved"
    CHALLENGE_RESERVED = "challenge_reserved"
    SHARED_RESERVE = "shared_reserve"


class CapacityPlanInvalidError(ValueError):
    reason_code = "ELECTION_CAPACITY_PLAN_INVALID"


class CapacityExhaustedError(RuntimeError):
    reason_code = "BULLETIN_BOARD_BATCH_CAPACITY_EXHAUSTED"


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """TEST PROFILE values are always marked as such by the caller."""

    election_context_id: str
    max_valid_continuations: int
    interval_count: int
    primary_capacity: int
    reserve_capacity: int
    reserve_commitments: int
    cast_reserved_per_batch: int
    challenge_reserved_per_batch: int
    shared_reserve_per_batch: int
    safety_reserve: int
    profile_label: str = "TEST PROFILE ONLY - NOT A PRODUCTION DEFAULT"

    @property
    def k(self) -> int:
        return K_PUBLIC_CHALLENGES_PER_CONTINUATION

    @property
    def a(self) -> int:
        return A_ACCEPTED_CASTS_PER_CONTINUATION

    @property
    def l_max(self) -> int:
        return self.max_valid_continuations * (self.k + self.a)

    @property
    def batches_per_interval(self) -> int:
        return 1 + self.reserve_commitments

    @property
    def capacity_per_interval(self) -> int:
        return self.primary_capacity + self.reserve_commitments * self.reserve_capacity

    @property
    def total_capacity(self) -> int:
        return self.capacity_per_interval * self.interval_count

    def slot_capacity(self, slot_class: SlotClass, batch_capacity: int) -> int:
        if slot_class is SlotClass.CAST_RESERVED:
            return self.cast_reserved_per_batch
        if slot_class is SlotClass.CHALLENGE_RESERVED:
            return self.challenge_reserved_per_batch
        del batch_capacity  # the shared reserve is declared, never inferred
        return self.shared_reserve_per_batch

    def validate(self) -> CapacityPlan:
        """Fail closed: a plan that does not cover `L_max` is not activated."""
        if self.max_valid_continuations <= 0:
            raise CapacityPlanInvalidError("E must be positive")
        if self.interval_count <= 0:
            raise CapacityPlanInvalidError("interval count must be positive")
        if self.primary_capacity <= 0:
            raise CapacityPlanInvalidError("primary batch capacity must be positive")
        partition = (
            self.cast_reserved_per_batch
            + self.challenge_reserved_per_batch
            + self.shared_reserve_per_batch
        )
        if partition != self.primary_capacity:
            raise CapacityPlanInvalidError(
                f"slot partition {partition} does not exactly cover primary batch "
                f"capacity {self.primary_capacity}; an unclassified slot is an "
                "adaptive-overflow hole"
            )
        if self.total_capacity < self.l_max + self.safety_reserve:
            raise CapacityPlanInvalidError(
                f"total capacity {self.total_capacity} < L_max {self.l_max} "
                f"+ safety reserve {self.safety_reserve}"
            )
        return self
