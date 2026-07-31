"""PACK-15 eligibility determination and the minimized assertion.

Eligibility is decided **on the identity side, before the trust boundary**
(ADR-089). This module holds the case, the rule-set reference, the
decision, the participation-unit ledger that enforces one assertion per
participation unit, and the assertion itself with its queued release and
one-time pickup.

Nothing here holds a voting credential, a redemption outcome, or any
reference to one: the pairing prohibition of ADR-093 is a property of the
field sets below, not of a policy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_eligibility_service.voting_attributes import ScopedAttribute
from epd2_eligibility_service.voting_timing import CohortSizeClass, coarsen
from epd2_eligibility_service.voting_trust_exceptions import (
    AssertionRevokedError,
    EligibilityDecisionExpiredError,
    VotingBoundaryIntegrityError,
)

#: Fields that may never appear on any artifact in this module, in any
#: encoding. Mirrors `voting_attributes.PROHIBITED_ATTRIBUTE_NAMES` and is
#: asserted structurally by the identity-leakage tests.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "identity_record_id",
        "membership_id",
        "member_number",
        "email",
        "phone",
        "full_name",
        "date_of_birth",
        "address",
        "communication_persona_id",
        "eid_subject",
        "ballot_id",
        "vote_content",
        "voting_credential_id",
        "credential_id",
    }
)


class EligibilityCriterion(StrEnum):
    """The fourteen criteria of the eligibility matrix."""

    MEMBERSHIP_STATUS = "EC-01"
    MEMBERSHIP_START_DATE = "EC-02"
    ORGANIZATIONAL_LEVEL = "EC-03"
    ORGANIZATIONAL_SCOPE = "EC-04"
    ROLE = "EC-05"
    AGE_THRESHOLD = "EC-06"
    SUSPENSION_RESTRICTION = "EC-07"
    PARTICIPATION_CLASS = "EC-08"
    CONFLICT_OF_INTEREST = "EC-09"
    CANDIDACY_STATUS = "EC-10"
    VOTING_WINDOW = "EC-11"
    ASSURANCE_LEVEL = "EC-12"
    MANUAL_EXCEPTION = "EC-13"
    GOVERNED_RULE = "EC-14"


class EligibilityDecisionStatus(StrEnum):
    REQUESTED = "requested"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    DENIED = "denied"
    REVIEW_REQUIRED = "review_required"
    UNDER_REVIEW = "under_review"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DISPUTED = "disputed"
    WITHDRAWN = "withdrawn"


#: Permitted decision-status transitions. A transition absent from this
#: table is refused; `approved -> superseded` is permitted only while no
#: assertion has been minted (enforced in the application layer, which is
#: the only layer that can see the ledger).
DECISION_TRANSITIONS: Mapping[EligibilityDecisionStatus, frozenset[EligibilityDecisionStatus]] = {
    EligibilityDecisionStatus.REQUESTED: frozenset(
        {
            EligibilityDecisionStatus.EVALUATING,
            EligibilityDecisionStatus.WITHDRAWN,
            EligibilityDecisionStatus.EXPIRED,
        }
    ),
    EligibilityDecisionStatus.EVALUATING: frozenset(
        {
            EligibilityDecisionStatus.APPROVED,
            EligibilityDecisionStatus.DENIED,
            EligibilityDecisionStatus.REVIEW_REQUIRED,
            EligibilityDecisionStatus.EXPIRED,
        }
    ),
    EligibilityDecisionStatus.REVIEW_REQUIRED: frozenset(
        {
            EligibilityDecisionStatus.UNDER_REVIEW,
            EligibilityDecisionStatus.EXPIRED,
            EligibilityDecisionStatus.DISPUTED,
        }
    ),
    EligibilityDecisionStatus.UNDER_REVIEW: frozenset(
        {
            EligibilityDecisionStatus.APPROVED,
            EligibilityDecisionStatus.DENIED,
            EligibilityDecisionStatus.EXPIRED,
        }
    ),
    EligibilityDecisionStatus.APPROVED: frozenset(
        {
            EligibilityDecisionStatus.SUPERSEDED,
            EligibilityDecisionStatus.EXPIRED,
            EligibilityDecisionStatus.DISPUTED,
        }
    ),
    EligibilityDecisionStatus.DENIED: frozenset({EligibilityDecisionStatus.DISPUTED}),
    EligibilityDecisionStatus.SUPERSEDED: frozenset(),
    EligibilityDecisionStatus.EXPIRED: frozenset({EligibilityDecisionStatus.DISPUTED}),
    EligibilityDecisionStatus.DISPUTED: frozenset(
        {EligibilityDecisionStatus.APPROVED, EligibilityDecisionStatus.DENIED}
    ),
    EligibilityDecisionStatus.WITHDRAWN: frozenset(),
}


def transition_permitted(
    current: EligibilityDecisionStatus, target: EligibilityDecisionStatus
) -> bool:
    return target in DECISION_TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class EligibilityRuleSetReference:
    """A frozen rule-set **version**, never a rule-set.

    Canon 9.1's rule freeze, extended from the rule to the set: a context
    references a version, and a later version does not retroactively
    change a decision (specification section 8.2).
    """

    rule_set_id: str
    rule_set_version: str
    declared_attribute_names: frozenset[str]
    criteria: tuple[EligibilityCriterion, ...]

    def __post_init__(self) -> None:
        if not self.rule_set_id or not self.rule_set_version:
            raise ValueError("a rule-set reference names both an id and a version")
        if not self.criteria:
            raise ValueError("a rule-set version evaluates at least one criterion")


@dataclass(frozen=True, slots=True)
class EligibilityEvidenceReference:
    """A PACK-11 governed-document reference. Never content."""

    evidence_reference: str
    evidence_class: str
    referenced_at: datetime

    def __post_init__(self) -> None:
        if not self.evidence_reference:
            raise ValueError("an evidence reference is never empty")
        if self.referenced_at.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")


@dataclass(frozen=True, slots=True)
class EligibilityDecisionReason:
    """One reason-coded finding. Free text is additional, never the reason."""

    reason_code: str
    criterion: EligibilityCriterion | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.reason_code:
            raise ValueError("a decision reason carries a registered reason code")


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """A context-, rule-version-, source-version- and time-bound decision."""

    decision_id: UUID
    case_id: UUID
    voting_context_reference: str
    status: EligibilityDecisionStatus
    rule_set: EligibilityRuleSetReference
    source_versions: Mapping[str, str]
    reasons: tuple[EligibilityDecisionReason, ...]
    eligibility_class: str
    organizational_scope: str
    required_assurance_satisfied: bool
    decided_at: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("every eligibility decision is reason-coded")
        if not self.source_versions:
            raise ValueError("a decision names the source-data versions it relied on")
        if self.decided_at.tzinfo is None or self.valid_until.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")
        if self.valid_until <= self.decided_at:
            raise ValueError("a decision's validity window ends after it starts")

    @property
    def approved(self) -> bool:
        return self.status is EligibilityDecisionStatus.APPROVED

    def assert_usable(self, now: datetime) -> None:
        """Refuse a decision that can no longer authorize an assertion."""
        if self.status is EligibilityDecisionStatus.SUPERSEDED:
            raise EligibilityDecisionExpiredError("the decision was superseded by a source change")
        if now >= self.valid_until:
            raise EligibilityDecisionExpiredError("the decision's validity window has elapsed")


@dataclass(frozen=True, slots=True)
class EligibilityCase:
    """The identified, identity-side case. Identification stops here."""

    case_id: UUID
    voting_context_reference: str
    participant_reference: str
    participation_class: str
    requested_at: datetime
    status: EligibilityDecisionStatus
    scoped_attributes: tuple[ScopedAttribute, ...] = ()
    evidence: tuple[EligibilityEvidenceReference, ...] = ()
    assisted_by: str | None = None

    def __post_init__(self) -> None:
        if not self.participant_reference:
            raise ValueError("an eligibility case names the participant it decides about")
        if self.requested_at.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")


@dataclass(frozen=True, slots=True)
class ParticipationUnitLedgerEntry:
    """One entry per participation unit per voting context.

    Enforces **one assertion per participation unit**. It records *that* an
    assertion was minted - never *which one*, because the pair is the link
    ADR-093 forbids.
    """

    voting_context_reference: str
    participation_unit_key: str
    assertion_minted: bool
    minted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.participation_unit_key:
            raise ValueError("a ledger entry names its participation unit")
        if self.assertion_minted and self.minted_at is None:
            raise ValueError("a minted entry records when it was minted")


# ---------------------------------------------------------------------------
# The minimized eligibility assertion
# ---------------------------------------------------------------------------


class AssertionStatus(StrEnum):
    MINTED = "minted"
    QUEUED = "queued"
    RELEASED = "released"
    PICKED_UP = "picked_up"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REDEEMED = "redeemed"
    REPLAY_REJECTED = "replay_rejected"


ASSERTION_TRANSITIONS: Mapping[AssertionStatus, frozenset[AssertionStatus]] = {
    AssertionStatus.MINTED: frozenset({AssertionStatus.QUEUED, AssertionStatus.REVOKED}),
    AssertionStatus.QUEUED: frozenset(
        {AssertionStatus.RELEASED, AssertionStatus.REVOKED, AssertionStatus.EXPIRED}
    ),
    AssertionStatus.RELEASED: frozenset(
        {AssertionStatus.PICKED_UP, AssertionStatus.REVOKED, AssertionStatus.EXPIRED}
    ),
    AssertionStatus.PICKED_UP: frozenset(
        {AssertionStatus.REDEEMED, AssertionStatus.EXPIRED, AssertionStatus.REPLAY_REJECTED}
    ),
    AssertionStatus.REDEEMED: frozenset({AssertionStatus.REPLAY_REJECTED}),
    AssertionStatus.REVOKED: frozenset(),
    AssertionStatus.EXPIRED: frozenset(),
    AssertionStatus.REPLAY_REJECTED: frozenset(),
}

#: The only permitted purpose. An assertion authenticates nothing and
#: authorizes nothing else.
ASSERTION_PURPOSE = "voting_credential_issuance"

#: The only permitted result. A denial is never asserted across the
#: boundary: the voting side has no use for the fact that someone was
#: refused, and telling it would give it a fact about a person.
ASSERTION_RESULT_APPROVED = "approved"

#: The closed twelve-field list of the crossing artifact (ADR-091).
ASSERTION_FIELD_NAMES: tuple[str, ...] = (
    "assertion_id",
    "voting_context_reference",
    "eligibility_result",
    "eligibility_class",
    "organizational_scope",
    "required_assurance_satisfied",
    "issued_at_bucket",
    "expires_at",
    "audience",
    "purpose",
    "nonce",
    "status",
)


@dataclass(frozen=True, slots=True)
class EligibilityAssertion:
    """The only artifact that crosses the trust boundary.

    Twelve fields, a closed list. Adding a field is an amendment to
    ADR-091, not a change to this dataclass.
    """

    assertion_id: UUID
    voting_context_reference: str
    eligibility_result: str
    eligibility_class: str
    organizational_scope: str
    required_assurance_satisfied: bool
    issued_at_bucket: datetime
    expires_at: datetime
    audience: str
    purpose: str
    nonce: str
    status: AssertionStatus
    integrity_metadata: Mapping[str, str] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if self.eligibility_result != ASSERTION_RESULT_APPROVED:
            raise VotingBoundaryIntegrityError(
                "only an approved eligibility result crosses the trust boundary"
            )
        if self.purpose != ASSERTION_PURPOSE:
            raise VotingBoundaryIntegrityError(
                f"an assertion's purpose is {ASSERTION_PURPOSE!r} and nothing else"
            )
        if not self.nonce:
            raise ValueError("an assertion carries a one-time nonce")
        if not self.audience:
            raise ValueError("an assertion is audience-bound")
        if self.issued_at_bucket.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")
        if self.expires_at <= self.issued_at_bucket:
            raise ValueError("an assertion expires after it is issued")

    def wire_payload(self) -> dict[str, object]:
        """The exact crossing payload. No field outside the closed list."""
        payload: dict[str, object] = {
            "assertion_id": str(self.assertion_id),
            "voting_context_reference": self.voting_context_reference,
            "eligibility_result": self.eligibility_result,
            "eligibility_class": self.eligibility_class,
            "organizational_scope": self.organizational_scope,
            "required_assurance_satisfied": self.required_assurance_satisfied,
            "issued_at_bucket": self.issued_at_bucket.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "audience": self.audience,
            "purpose": self.purpose,
            "nonce": self.nonce,
            "status": self.status.value,
        }
        assert_no_forbidden_fields(payload)
        return payload

    def assert_live(self, now: datetime) -> None:
        if self.status is AssertionStatus.REVOKED:
            raise AssertionRevokedError("the assertion was revoked before use")
        if now >= self.expires_at:
            raise EligibilityDecisionExpiredError("the assertion has expired")


@dataclass(frozen=True, slots=True)
class AssertionQueueEntry:
    """A minted assertion waiting for its governed release schedule."""

    assertion_id: UUID
    voting_context_reference: str
    batch_reference: str
    enqueued_at: datetime
    release_not_before: datetime
    cohort_wait_deadline: datetime
    released_at: datetime | None = None
    cohort_size_class: CohortSizeClass | None = None
    below_minimum_cohort: bool = False

    def __post_init__(self) -> None:
        if self.release_not_before < self.enqueued_at:
            raise ValueError("a release cannot be scheduled before enqueueing")
        if self.cohort_wait_deadline < self.release_not_before:
            raise ValueError("the cohort deadline is never before the earliest release")


@dataclass(frozen=True, slots=True)
class AssertionPickup:
    """A one-time pickup, bound to the PACK-14 handoff artifact.

    Redeemed from inside the isolated voting origin. It returns the
    assertion and nothing else - no account, no session, no case
    reference, no context-scoped pseudonym.
    """

    pickup_id: UUID
    assertion_id: UUID
    voting_context_reference: str
    handoff_artifact_digest: str
    audience_origin: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.handoff_artifact_digest:
            raise ValueError("a pickup is bound to exactly one handoff artifact")
        if self.expires_at <= self.created_at:
            raise ValueError("a pickup expires after it is created")

    @property
    def consumed(self) -> bool:
        return self.consumed_at is not None


def assert_no_forbidden_fields(payload: Mapping[str, object]) -> None:
    """Refuse a payload carrying any forbidden identity or ballot field."""
    offending = sorted(set(payload) & FORBIDDEN_FIELD_NAMES)
    if offending:
        raise VotingBoundaryIntegrityError(
            "forbidden fields in a voting-trust payload: " + ", ".join(offending)
        )


def assert_no_assertion_credential_pair(payload: Mapping[str, object]) -> None:
    """Refuse a payload that pairs an assertion with a credential.

    ADR-093's structural rule, applied to a single payload: **no store,
    log, event, trace or export contains both an eligibility-side and a
    voting-side reference for the same participation.**
    """
    keys = set(payload)
    assertion_keys = {"assertion_id", "eligibility_assertion_id", "nonce", "assertion_reference"}
    credential_keys = {
        "voting_credential_id",
        "credential_id",
        "credential_reference",
        "redemption_reference",
    }
    if keys & assertion_keys and keys & credential_keys:
        raise VotingBoundaryIntegrityError(
            "a payload may never carry both an assertion reference and a credential reference"
        )


def build_assertion_payload(
    assertion: EligibilityAssertion,
    *,
    granularity_seconds: int,
) -> dict[str, object]:
    """The audit payload for an assertion event.

    Coarsened, minimized, and checked against both structural rules before
    it can become an envelope.
    """
    payload: dict[str, object] = {
        "assertion_id": str(assertion.assertion_id),
        "voting_context_reference": assertion.voting_context_reference,
        "eligibility_class": assertion.eligibility_class,
        "organizational_scope": assertion.organizational_scope,
        "status": assertion.status.value,
        "issued_at_bucket": coarsen(assertion.issued_at_bucket, granularity_seconds).isoformat(),
        "expires_at": coarsen(assertion.expires_at, granularity_seconds).isoformat(),
        "audience": assertion.audience,
    }
    assert_no_forbidden_fields(payload)
    assert_no_assertion_credential_pair(payload)
    return payload


def decision_reason_codes(reasons: Sequence[EligibilityDecisionReason]) -> tuple[str, ...]:
    return tuple(reason.reason_code for reason in reasons)
