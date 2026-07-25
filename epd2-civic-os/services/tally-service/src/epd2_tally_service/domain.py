"""`Tally` (canon section 15.5) and `ResultPublication` (canon section
15.6), per `docs/canonical/TZ-00-domain-event-canon.md`.

Consolidates the canon-named "Tally Service" and "Result Publication
Service" into one owner package, per
`docs/adr/ADR-005-pack-03-service-decomposition.md` item 5: a
`ResultPublication`'s aggregate counts are a published view of the same
completed `Tally`, and canon gives no reason a WIP tally needs an
independent owner from its eventual publication.

**No PACK-02 or PACK-03 sibling import** (ADR-008 item 3: no
PACK-03<->PACK-03 import is allowed, and ADR-008's own enumerated edge
list names no PACK-02 dependency for `tally-service` either). A `Tally`
is constructed from a caller-supplied, already-validated set of vote
facts (a vote-count breakdown, an `input_set_hash`, an invalid-vote
count, ...) passed in as plain function parameters by whatever wires
services together - this module never imports `epd2_voting_service` and
never sees a real `VoteEnvelope`/`Ballot` object. See `README.md`.

`result_data`'s shape (`Mapping[str, int]`, e.g. `{"option_code": count}`)
is this service's own judgment call: canon section 15.5 lists the
`result_data` field but does not specify its internal shape, so it is
kept as a generic string-to-int vote-count-per-option breakdown rather
than something ballot-method-specific (e.g. ranked-choice tallies, out of
this pilot's scope per ADR-009 item 4).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_tally_service.exceptions import (
    ForbiddenTallyTransitionError,
    UnknownQuorumResultError,
    UnknownTallyVerificationStatusError,
    UnknownThresholdResultError,
)

#: Identity-separation guarantee (ADR-009 item 15: "aggregate counts +
#: hash-only audit-chain proof, never vote contents"), mirrored in style
#: exactly from `epd2_voting_service.domain.FORBIDDEN_FIELD_NAMES`. No
#: field named here may ever appear on `Tally` or `ResultPublication` -
#: both entities carry aggregate counts and administrative fields only,
#: never anything that could resolve back to an individual voter (see
#: `tests/test_domain.py`'s `assert set(__dataclass_fields__) &
#: FORBIDDEN_FIELD_NAMES == set()` checks on both dataclasses).
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset({"account_id", "person_id", "identity_record_id"})

# ---------------------------------------------------------------------------
# Tally (canon section 15.5)
# ---------------------------------------------------------------------------


class TallyVerificationStatus(StrEnum):
    """Canon section 15.5's exact status list."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    VERIFICATION_FAILED = "verification_failed"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"


def parse_verification_status(value: str) -> TallyVerificationStatus:
    try:
        return TallyVerificationStatus(value)
    except ValueError as exc:
        raise UnknownTallyVerificationStatusError(
            f"unknown tally verification_status: {value!r}"
        ) from exc


#: This task's own exact transition graph (Step 2). Two of these seven
#: edges (`verification_failed -> running`, `verified -> superseded`) have
#: no corresponding public `application` command yet - only `start_tally`,
#: `complete_tally`, `verify_tally`, and `publish_result` are exposed
#: (canon events section 20.10's own verbatim event list gives no event
#: name for a tally "retry" or "supersede" action). The graph is
#: implemented in full here so CT-00-02/CT-00-03-style structural tests
#: can validate it, mirroring `docs/adr/ADR-009-voting-delegation-quorum-defaults.md`
#: item 14's precedent of implementing a canon status/transition
#: structurally without necessarily exposing a command that reaches it.
ALLOWED_TRANSITIONS: frozenset[tuple[TallyVerificationStatus, TallyVerificationStatus]] = frozenset(
    {
        (TallyVerificationStatus.PENDING, TallyVerificationStatus.RUNNING),
        (TallyVerificationStatus.RUNNING, TallyVerificationStatus.COMPLETED),
        (TallyVerificationStatus.RUNNING, TallyVerificationStatus.VERIFICATION_FAILED),
        (TallyVerificationStatus.COMPLETED, TallyVerificationStatus.VERIFIED),
        (TallyVerificationStatus.COMPLETED, TallyVerificationStatus.VERIFICATION_FAILED),
        (TallyVerificationStatus.VERIFICATION_FAILED, TallyVerificationStatus.RUNNING),
        (TallyVerificationStatus.VERIFIED, TallyVerificationStatus.SUPERSEDED),
    }
)


def assert_transition_allowed(
    current: TallyVerificationStatus, target: TallyVerificationStatus
) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenTallyTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


def compute_input_set_hash(vote_records: Iterable[tuple[UUID, str]]) -> str:
    """Deterministic digest over the caller-supplied input vote set a
    `Tally` covers - a `(vote_envelope_id, choice)` pair per counted
    `VoteEnvelope` (canon section 15.5's `input_set_hash`), mirroring
    `epd2_eligibility_service.domain.compute_snapshot_digest`'s exact
    determinism style: sorting first makes the digest independent of
    collection order, so two calls built from the same logical vote set
    always match regardless of iteration order.

    This service never has a real `VoteEnvelope` to hash directly (ADR-008
    item 3: no PACK-03<->PACK-03 import) - the caller that wires
    `voting-service` and `tally-service` together is responsible for
    reading the real, validated `VoteEnvelope` set and passing its
    `(vote_envelope_id, encrypted_or_encoded_choice)` pairs in here before
    calling `application.start_tally` with the resulting digest.
    """
    payload = {
        "vote_records": sorted(
            (str(vote_envelope_id), choice) for vote_envelope_id, choice in vote_records
        )
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Tally:
    """Canon section 15.5 fields exactly. `result_data` carries aggregate
    per-option vote counts only - see `FORBIDDEN_FIELD_NAMES` above, which
    applies to this dataclass too (`tests/test_domain.py`)."""

    tally_id: UUID
    ballot_id: UUID
    input_set_hash: str
    algorithm_version: str
    started_at: datetime
    completed_at: datetime | None
    result_data: Mapping[str, int]
    invalid_vote_count: int
    tally_signature: str | None
    verification_status: TallyVerificationStatus

    def __post_init__(self) -> None:
        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")
        if self.completed_at is not None and self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")
        if self.invalid_vote_count < 0:
            raise ValueError("invalid_vote_count must not be negative")
        for option_code, count in self.result_data.items():
            if count < 0:
                raise ValueError(f"result_data[{option_code!r}] must not be negative")

    def with_status(self, new_status: TallyVerificationStatus) -> Tally:
        """A plain status-only transition (no other field changes) -
        `pending -> running`, `completed -> verified`,
        `completed -> verification_failed`, `verification_failed ->
        running`, `verified -> superseded`. `running -> completed` always
        goes through `with_completion` instead, since it also sets
        `completed_at`/`result_data`/`invalid_vote_count`/`tally_signature`."""
        assert_transition_allowed(self.verification_status, new_status)
        return replace(self, verification_status=new_status)

    def with_completion(
        self,
        *,
        completed_at: datetime,
        result_data: Mapping[str, int],
        invalid_vote_count: int,
        tally_signature: str | None,
    ) -> Tally:
        """The `running -> completed` transition, which also records the
        tally's computed result in the same step."""
        assert_transition_allowed(self.verification_status, TallyVerificationStatus.COMPLETED)
        return replace(
            self,
            verification_status=TallyVerificationStatus.COMPLETED,
            completed_at=completed_at,
            result_data=dict(result_data),
            invalid_vote_count=invalid_vote_count,
            tally_signature=tally_signature,
        )


# ---------------------------------------------------------------------------
# ResultPublication (canon section 15.6, including the ADR-010/canon-0.2.0
# `challenge_deadline_at` addition)
# ---------------------------------------------------------------------------


class QuorumResult(StrEnum):
    """Canon section 15.6 lists `quorum_result` as a field but gives no
    explicit enum for its values; this is this service's own minimal,
    documented choice. `NOT_REQUIRED` covers `Ballot.quorum_rule` being
    unset (ADR-009 item 5, accepted: "`Ballot.quorum_rule` is already an
    optional, per-ballot field; default to no quorum requirement unless a
    specific ballot configures one") - distinct from `QUORUM_NOT_MET`,
    which means a quorum *was* required and the ballot fell short of it."""

    QUORUM_MET = "quorum_met"
    QUORUM_NOT_MET = "quorum_not_met"
    NOT_REQUIRED = "not_required"


def parse_quorum_result(value: str) -> QuorumResult:
    try:
        return QuorumResult(value)
    except ValueError as exc:
        raise UnknownQuorumResultError(f"unknown quorum_result: {value!r}") from exc


class ThresholdResult(StrEnum):
    """Canon section 15.6 lists `threshold_result` as a field but gives no
    explicit enum for its values; this is this service's own minimal,
    documented choice. Per ADR-009 item 11 (accepted): a tie MUST be
    recorded as `TIE_NO_DECISION` - never silently resolved by an implicit
    tie-break rule."""

    THRESHOLD_MET = "threshold_met"
    THRESHOLD_NOT_MET = "threshold_not_met"
    TIE_NO_DECISION = "tie_no_decision"


def parse_threshold_result(value: str) -> ThresholdResult:
    try:
        return ThresholdResult(value)
    except ValueError as exc:
        raise UnknownThresholdResultError(f"unknown threshold_result: {value!r}") from exc


def compute_quorum_result(
    *, accepted_vote_count: int, quorum_threshold: int | None
) -> QuorumResult:
    """Compute `quorum_result` from a caller-resolved absolute threshold.

    `quorum_threshold` is the minimum `accepted_vote_count` required for
    quorum, already resolved by the caller from the real `Ballot`'s
    `quorum_rule` (canon section 15.1) - which canon does not further
    specify the shape of (e.g. it may itself be an absolute count or a
    percentage of `eligible_count`, resolved by the caller before calling
    here). This keeps `tally-service` free of any need to know
    `quorum_rule`'s shape or to import `epd2_voting_service` (ADR-008 item
    3). `None` means no quorum requirement applies (ADR-009 item 5's
    default).
    """
    if quorum_threshold is None:
        return QuorumResult.NOT_REQUIRED
    if quorum_threshold < 0:
        raise ValueError("quorum_threshold must not be negative")
    if accepted_vote_count < 0:
        raise ValueError("accepted_vote_count must not be negative")
    if accepted_vote_count >= quorum_threshold:
        return QuorumResult.QUORUM_MET
    return QuorumResult.QUORUM_NOT_MET


def compute_threshold_result(option_counts: Mapping[str, int]) -> ThresholdResult:
    """Compute `threshold_result` from a plain vote-count-per-option
    breakdown.

    This service's own documented judgment call, since canon gives no
    `threshold_rule` shape and `publish_result`'s own parameter list (Step
    3) supplies only `option_counts`, no separate threshold-rule
    parameter: the winner is whichever option has the strictly highest
    count; `THRESHOLD_MET` requires that winner to hold an absolute
    majority (`count * 2 > total_votes`) of the counted options, not
    merely a plurality - so a three-way split where the leading option
    has 40% of the vote is `THRESHOLD_NOT_MET`, not a false "met". If two
    or more options share the top count, the result is `TIE_NO_DECISION`
    (ADR-009 item 11) regardless of what fraction of the total that count
    represents - ties are never silently broken here. An empty
    `option_counts`, or one where every option has zero votes, is treated
    as `THRESHOLD_NOT_MET` (no votes cast, no majority possible) rather
    than `TIE_NO_DECISION` - "nobody voted" is a distinct concept from "a
    genuine contest ended in a tie", even though both technically share a
    maximum count across every option.
    """
    for option_code, count in option_counts.items():
        if count < 0:
            raise ValueError(f"option_counts[{option_code!r}] must not be negative")

    if not option_counts or all(count == 0 for count in option_counts.values()):
        return ThresholdResult.THRESHOLD_NOT_MET

    max_count = max(option_counts.values())
    leaders = [code for code, count in option_counts.items() if count == max_count]
    if len(leaders) > 1:
        return ThresholdResult.TIE_NO_DECISION

    total = sum(option_counts.values())
    if max_count * 2 > total:
        return ThresholdResult.THRESHOLD_MET
    return ThresholdResult.THRESHOLD_NOT_MET


#: ADR-010 / canon 0.2.0: `Ballot.challenge_window_hours` defaults to 72
#: hours repository-wide when unset. This is `tally-service`'s own local
#: copy of the same repository-wide constant `voting-service` (the owner
#: of `Ballot`) independently documents on its own `Ballot.challenge_window_hours`
#: field - duplicating it here is expected and intentional, not a bug: the
#: two services are independent by design (ADR-008 item 3 forbids a
#: PACK-03<->PACK-03 import that could otherwise share one constant), and
#: each is individually responsible for matching the repository-wide
#: default ADR-010 specifies.
DEFAULT_CHALLENGE_WINDOW_HOURS: int = 72


def compute_challenge_deadline(
    published_at: datetime, challenge_window_hours: int | None
) -> datetime:
    """`challenge_deadline_at = published_at + effective_challenge_window_hours`
    (ADR-010), where the effective window is the referenced `Ballot`'s
    `challenge_window_hours` if set, else `DEFAULT_CHALLENGE_WINDOW_HOURS`.

    `challenge_window_hours` is accepted as a plain parameter (never read
    from a real `Ballot` object this module could otherwise import) - the
    caller that wires `voting-service` and `tally-service` together is
    responsible for reading the real `Ballot.challenge_window_hours` and
    passing it in here, per ADR-008 item 3.
    """
    if published_at.tzinfo is None:
        raise ValueError("published_at must be timezone-aware")
    hours = (
        challenge_window_hours
        if challenge_window_hours is not None
        else DEFAULT_CHALLENGE_WINDOW_HOURS
    )
    if hours <= 0:
        raise ValueError("challenge_window_hours must be a positive number of hours")
    return published_at + timedelta(hours=hours)


@dataclass(frozen=True, slots=True)
class ResultPublication:
    """Canon section 15.6 fields exactly, including the ADR-010/canon
    0.2.0 addition `challenge_deadline_at`.

    No status enum: canon lists no `status` field for `ResultPublication`
    (unlike `Tally`) - like `EligibilitySnapshot`/`InitiativeVersion`, it
    is created once, immutable thereafter, and never appears here as a
    field canon does not list.
    """

    result_publication_id: UUID
    ballot_id: UUID
    tally_id: UUID
    eligible_count: int
    credential_count: int
    accepted_vote_count: int
    rejected_vote_count: int
    quorum_result: QuorumResult
    threshold_result: ThresholdResult
    published_at: datetime
    audit_package_reference: str
    challenge_deadline_at: datetime

    def __post_init__(self) -> None:
        if self.published_at.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        if self.challenge_deadline_at.tzinfo is None:
            raise ValueError("challenge_deadline_at must be timezone-aware")
        if self.challenge_deadline_at < self.published_at:
            raise ValueError("challenge_deadline_at must not precede published_at")
        for name in (
            "eligible_count",
            "credential_count",
            "accepted_vote_count",
            "rejected_vote_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        if not self.audit_package_reference:
            raise ValueError("audit_package_reference must not be empty")


class FinalityState(StrEnum):
    """ADR-010's finality clarification, implemented exactly, not
    softened: expiry of `challenge_deadline_at` is necessary but NOT
    sufficient for finality. There is deliberately **no third member**
    meaning "final" - PACK-03 must never automatically declare a
    `ResultPublication` final merely because the deadline elapsed, and no
    hidden, pack-local challenge process may be invented to fill that gap
    (ADR-010, Owner decision). Until a canonical or explicitly approved
    technical-challenge registration/adjudication mechanism exists (its
    own future ADR), every `ResultPublication` this service produces
    remains provisional at the application level - permanently, as far as
    this module is concerned.
    """

    PROVISIONAL_BEFORE_DEADLINE = "provisional_before_deadline"
    PROVISIONAL_PENDING_CHALLENGE_MECHANISM = "provisional_pending_challenge_mechanism"


def compute_finality_state(result: ResultPublication, now: datetime) -> FinalityState:
    """`now < challenge_deadline_at` -> `PROVISIONAL_BEFORE_DEADLINE`;
    `now >= challenge_deadline_at` -> `PROVISIONAL_PENDING_CHALLENGE_MECHANISM`.

    No code path in this function, or anywhere else in this service, ever
    returns or claims a "final" state - see ADR-010's Owner decision,
    quoted in `FinalityState`'s own docstring, and
    `tests/test_domain.py::test_domain_module_never_defines_a_final_state_member`.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if now < result.challenge_deadline_at:
        return FinalityState.PROVISIONAL_BEFORE_DEADLINE
    return FinalityState.PROVISIONAL_PENDING_CHALLENGE_MECHANISM
