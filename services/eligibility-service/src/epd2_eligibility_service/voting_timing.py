"""PACK-15 issuance timing controls (`OD-P15-02`, ADR-093).

An assertion issued on the identity side and a credential minted on the
voting side within the same quiet minute are plausibly the same
participation. `ADR-093` makes the *stored* link structurally impossible;
this module bounds the *timing* channel that survives it.

Nine controls, each with a governed reference default, a permitted range
and a **hard lower bound that configuration cannot go below**. A value
outside its range is refused with `TIMING_PROFILE_OUT_OF_BOUNDS`, never
clamped silently - a silently clamped privacy control is a disabled
privacy control.

Two properties are load-bearing and are asserted by the unit tests:

* **A cohort of one is never released immediately.** It waits for further
  assertions until `cohort_wait_max`.
* **Access is never denied for want of a cohort.** At `cohort_wait_max`
  the assertion is released anyway and the exception is recorded with the
  cohort-size *class*. Disenfranchising a participant to protect their own
  unlinkability is not an acceptable trade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from epd2_eligibility_service.voting_trust_exceptions import (
    IssuanceWindowGuaranteeError,
    TimingProfileOutOfBoundsError,
)

#: The only permitted issuance mode. Immediate minting is not a mode.
ISSUANCE_MODE_QUEUED = "queued"

#: Reference defaults, from the corrected specification section 19.2.
DEFAULT_TIMESTAMP_GRANULARITY_SECONDS = 300
DEFAULT_RELEASE_DELAY_MIN_SECONDS = 30
DEFAULT_RELEASE_DELAY_MAX_SECONDS = 300
DEFAULT_BATCH_INTERVAL_SECONDS = 120
DEFAULT_BATCH_MAX_SIZE = 250
DEFAULT_MINIMUM_COHORT_SIZE = 5
DEFAULT_COHORT_WAIT_MAX_SECONDS = 3600
DEFAULT_MINTING_DELAY_MIN_SECONDS = 5
DEFAULT_MINTING_DELAY_MAX_SECONDS = 30
DEFAULT_SMALL_ELECTORATE_THRESHOLD = 50
DEFAULT_DISCLOSURE_MIN_CELL = 5
DEFAULT_ISSUANCE_WINDOW_MIN_DURATION_SECONDS = 4 * 3600

#: Hard lower bounds. Configuration may not go below these, per context,
#: for any reason, under any flag.
MIN_TIMESTAMP_GRANULARITY_SECONDS = 60
MIN_RELEASE_DELAY_MIN_SECONDS = 10
MIN_RELEASE_DELAY_MAX_SECONDS = 60
MIN_BATCH_INTERVAL_SECONDS = 60
MIN_BATCH_MAX_SIZE = 50
MIN_COHORT_SIZE = 3
MIN_COHORT_WAIT_MAX_SECONDS = 600
MIN_MINTING_DELAY_MIN_SECONDS = 2
MIN_MINTING_DELAY_MAX_SECONDS = 10
MIN_SMALL_ELECTORATE_THRESHOLD = 20
MIN_DISCLOSURE_MIN_CELL = 5
MIN_ISSUANCE_WINDOW_DURATION_SECONDS = 4 * 3600

#: Upper bounds, where the specification fixes one.
MAX_TIMESTAMP_GRANULARITY_SECONDS = 3600
MAX_RELEASE_DELAY_MIN_SECONDS = 300
MAX_RELEASE_DELAY_MAX_SECONDS = 1800
MAX_BATCH_INTERVAL_SECONDS = 900
MAX_BATCH_MAX_SIZE = 2000
MAX_COHORT_SIZE = 50
MAX_COHORT_WAIT_MAX_SECONDS = 21600
MAX_MINTING_DELAY_MIN_SECONDS = 60
MAX_MINTING_DELAY_MAX_SECONDS = 300
MAX_SMALL_ELECTORATE_THRESHOLD = 200

#: Small-electorate hardening (specification section 19.4).
SMALL_ELECTORATE_TIMESTAMP_GRANULARITY_SECONDS = 3600
SMALL_ELECTORATE_ISSUANCE_WINDOW_MIN_SECONDS = 24 * 3600
SMALL_ELECTORATE_COHORT_FRACTION = 0.1


class CohortSizeClass(StrEnum):
    """Cohort sizes are reported as classes, never as exact numbers.

    An exact cohort size in a small electorate is a participation
    statement (`T-P15-37`).
    """

    SINGLE = "single"
    BELOW_MINIMUM = "below_minimum"
    AT_MINIMUM = "at_minimum"
    ABOVE_MINIMUM = "above_minimum"


def classify_cohort_size(size: int, minimum: int) -> CohortSizeClass:
    """Map a cohort size onto its reportable class."""
    if size <= 0:
        raise ValueError("a released cohort holds at least one assertion")
    if size == 1:
        return CohortSizeClass.SINGLE
    if size < minimum:
        return CohortSizeClass.BELOW_MINIMUM
    if size == minimum:
        return CohortSizeClass.AT_MINIMUM
    return CohortSizeClass.ABOVE_MINIMUM


def _require_range(name: str, value: int, low: int, high: int, hard_floor: int) -> None:
    if value < hard_floor:
        raise TimingProfileOutOfBoundsError(
            f"{name}={value} is below the hard lower bound {hard_floor}"
        )
    if value < low or value > high:
        raise TimingProfileOutOfBoundsError(
            f"{name}={value} is outside the permitted range {low}..{high}"
        )


@dataclass(frozen=True, slots=True)
class IssuanceTimingProfile:
    """Governed timing configuration attached to one voting context.

    Every field is governed configuration (`FIR-CONFIG-001`), never a
    constant, and every field is validated on construction.
    """

    issuance_mode: str = ISSUANCE_MODE_QUEUED
    timestamp_granularity_seconds: int = DEFAULT_TIMESTAMP_GRANULARITY_SECONDS
    release_delay_min_seconds: int = DEFAULT_RELEASE_DELAY_MIN_SECONDS
    release_delay_max_seconds: int = DEFAULT_RELEASE_DELAY_MAX_SECONDS
    batch_interval_seconds: int = DEFAULT_BATCH_INTERVAL_SECONDS
    batch_max_size: int = DEFAULT_BATCH_MAX_SIZE
    minimum_cohort_size: int = DEFAULT_MINIMUM_COHORT_SIZE
    cohort_wait_max_seconds: int = DEFAULT_COHORT_WAIT_MAX_SECONDS
    minting_delay_min_seconds: int = DEFAULT_MINTING_DELAY_MIN_SECONDS
    minting_delay_max_seconds: int = DEFAULT_MINTING_DELAY_MAX_SECONDS
    small_electorate_threshold: int = DEFAULT_SMALL_ELECTORATE_THRESHOLD
    disclosure_min_cell: int = DEFAULT_DISCLOSURE_MIN_CELL
    issuance_window_min_duration_seconds: int = DEFAULT_ISSUANCE_WINDOW_MIN_DURATION_SECONDS

    def __post_init__(self) -> None:
        if self.issuance_mode != ISSUANCE_MODE_QUEUED:
            raise TimingProfileOutOfBoundsError(
                f"issuance_mode={self.issuance_mode!r}: queued issuance is the only mode"
            )
        _require_range(
            "timestamp_granularity_seconds",
            self.timestamp_granularity_seconds,
            MIN_TIMESTAMP_GRANULARITY_SECONDS,
            MAX_TIMESTAMP_GRANULARITY_SECONDS,
            MIN_TIMESTAMP_GRANULARITY_SECONDS,
        )
        _require_range(
            "release_delay_min_seconds",
            self.release_delay_min_seconds,
            MIN_RELEASE_DELAY_MIN_SECONDS,
            MAX_RELEASE_DELAY_MIN_SECONDS,
            MIN_RELEASE_DELAY_MIN_SECONDS,
        )
        _require_range(
            "release_delay_max_seconds",
            self.release_delay_max_seconds,
            MIN_RELEASE_DELAY_MAX_SECONDS,
            MAX_RELEASE_DELAY_MAX_SECONDS,
            MIN_RELEASE_DELAY_MAX_SECONDS,
        )
        if self.release_delay_max_seconds < 4 * self.release_delay_min_seconds:
            raise TimingProfileOutOfBoundsError(
                "release_delay_max_seconds must be at least four times "
                "release_delay_min_seconds so the release window is not a fixed offset"
            )
        _require_range(
            "batch_interval_seconds",
            self.batch_interval_seconds,
            MIN_BATCH_INTERVAL_SECONDS,
            MAX_BATCH_INTERVAL_SECONDS,
            MIN_BATCH_INTERVAL_SECONDS,
        )
        _require_range(
            "batch_max_size",
            self.batch_max_size,
            MIN_BATCH_MAX_SIZE,
            MAX_BATCH_MAX_SIZE,
            MIN_BATCH_MAX_SIZE,
        )
        _require_range(
            "minimum_cohort_size",
            self.minimum_cohort_size,
            MIN_COHORT_SIZE,
            MAX_COHORT_SIZE,
            MIN_COHORT_SIZE,
        )
        _require_range(
            "cohort_wait_max_seconds",
            self.cohort_wait_max_seconds,
            MIN_COHORT_WAIT_MAX_SECONDS,
            MAX_COHORT_WAIT_MAX_SECONDS,
            MIN_COHORT_WAIT_MAX_SECONDS,
        )
        _require_range(
            "minting_delay_min_seconds",
            self.minting_delay_min_seconds,
            MIN_MINTING_DELAY_MIN_SECONDS,
            MAX_MINTING_DELAY_MIN_SECONDS,
            MIN_MINTING_DELAY_MIN_SECONDS,
        )
        _require_range(
            "minting_delay_max_seconds",
            self.minting_delay_max_seconds,
            MIN_MINTING_DELAY_MAX_SECONDS,
            MAX_MINTING_DELAY_MAX_SECONDS,
            MIN_MINTING_DELAY_MAX_SECONDS,
        )
        if self.minting_delay_max_seconds < 3 * self.minting_delay_min_seconds:
            raise TimingProfileOutOfBoundsError(
                "minting_delay_max_seconds must be at least three times minting_delay_min_seconds"
            )
        _require_range(
            "small_electorate_threshold",
            self.small_electorate_threshold,
            MIN_SMALL_ELECTORATE_THRESHOLD,
            MAX_SMALL_ELECTORATE_THRESHOLD,
            MIN_SMALL_ELECTORATE_THRESHOLD,
        )
        if self.disclosure_min_cell < MIN_DISCLOSURE_MIN_CELL:
            raise TimingProfileOutOfBoundsError(
                f"disclosure_min_cell={self.disclosure_min_cell} is below the floor "
                f"{MIN_DISCLOSURE_MIN_CELL}; a small electorate raises it, never lowers it"
            )
        if self.issuance_window_min_duration_seconds < MIN_ISSUANCE_WINDOW_DURATION_SECONDS:
            raise TimingProfileOutOfBoundsError(
                "issuance_window_min_duration_seconds is below the four-hour floor"
            )

    # -- small electorates ------------------------------------------------

    def is_small_electorate(self, eligible_population: int) -> bool:
        return eligible_population < self.small_electorate_threshold

    def effective_minimum_cohort(self, eligible_population: int) -> int:
        """`k = max(3, ceil(0.1 x N))` for a small electorate."""
        if not self.is_small_electorate(eligible_population):
            return self.minimum_cohort_size
        scaled = math.ceil(SMALL_ELECTORATE_COHORT_FRACTION * eligible_population)
        return max(MIN_COHORT_SIZE, scaled)

    def effective_timestamp_granularity(self, eligible_population: int) -> int:
        if self.is_small_electorate(eligible_population):
            return max(
                self.timestamp_granularity_seconds,
                SMALL_ELECTORATE_TIMESTAMP_GRANULARITY_SECONDS,
            )
        return self.timestamp_granularity_seconds

    def effective_issuance_window_minimum(self, eligible_population: int) -> int:
        if self.is_small_electorate(eligible_population):
            return SMALL_ELECTORATE_ISSUANCE_WINDOW_MIN_SECONDS
        return self.issuance_window_min_duration_seconds

    def per_scope_metrics_permitted(self, eligible_population: int) -> bool:
        """A small electorate publishes no per-scope operational metric.

        Not thresholded, not delayed: none at all.
        """
        return not self.is_small_electorate(eligible_population)

    # -- window guarantee -------------------------------------------------

    def release_guarantee_seconds(self) -> int:
        """The latest a queued assertion can wait before it is released."""
        return self.cohort_wait_max_seconds + self.release_delay_max_seconds

    def assert_window_guarantee(
        self,
        *,
        issuance_window_start: datetime,
        issuance_window_end: datetime,
        eligible_population: int,
    ) -> None:
        """Refuse a profile that could strand an assertion in its own queue.

        The queue must guarantee release at least
        `cohort_wait_max + release_delay_max` before the credential
        issuance window closes.
        """
        if issuance_window_end <= issuance_window_start:
            raise IssuanceWindowGuaranteeError("the issuance window ends before it starts")
        duration = int((issuance_window_end - issuance_window_start).total_seconds())
        minimum = self.effective_issuance_window_minimum(eligible_population)
        if duration < minimum:
            raise IssuanceWindowGuaranteeError(
                f"the issuance window is {duration}s; this context requires at least {minimum}s"
            )
        if duration <= self.release_guarantee_seconds():
            raise IssuanceWindowGuaranteeError(
                "the issuance window is shorter than the queue's own release guarantee"
            )

    def latest_safe_enqueue(self, issuance_window_end: datetime) -> datetime:
        """The last moment an assertion can enter the queue and still be
        guaranteed a release inside the window."""
        return issuance_window_end - timedelta(seconds=self.release_guarantee_seconds())


#: The reference profile. Governed configuration binds a per-context
#: instance; this constant is the documented default, not a hard-coded
#: policy.
REFERENCE_TIMING_PROFILE = IssuanceTimingProfile()


def coarsen(moment: datetime, granularity_seconds: int) -> datetime:
    """Truncate a timestamp to the governed granularity.

    Applied to every crossing artifact and every voting-side record. A
    microsecond timestamp is a correlation key.
    """
    if moment.tzinfo is None:
        raise ValueError("timestamps are timezone-aware at this boundary")
    if granularity_seconds < MIN_TIMESTAMP_GRANULARITY_SECONDS:
        raise TimingProfileOutOfBoundsError(
            f"granularity {granularity_seconds}s is below the hard lower bound"
        )
    epoch_seconds = int(moment.timestamp())
    bucket = epoch_seconds - (epoch_seconds % granularity_seconds)
    return datetime.fromtimestamp(bucket, tz=moment.tzinfo)
