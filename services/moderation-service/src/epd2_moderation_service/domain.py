"""`ModerationCase`, `ModerationDecision`, `Appeal`, per
`docs/canonical/TZ-00-domain-event-canon.md`, sections 14.1/14.2/14.3.

This package consolidates canon's separately-named "Moderation Service"
and "Appeal Service" into one physical `uv` workspace member (ADR-005,
decomposition item 3). That consolidation is safe only because of one
hard, tested precondition (CT-00-06; canon section 14.3: "Апелляцию не
должен окончательно рассматривать автор исходного решения" — an appeal
must not be finally decided by the author of the original decision) —
enforced in `application.decide_appeal`, never in this module. This
module only encodes the three entities' own shapes and state machines;
role/actor authorization is strictly an application-layer concern here,
the same boundary every other PACK-02 service already draws between
`domain.py` (structural invariants) and `application.py`
(`actor_is_authorized`-style checks).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_moderation_service.exceptions import (
    ForbiddenAppealTransitionError,
    ForbiddenModerationCaseTransitionError,
    UnknownAppealStatusError,
    UnknownModerationCaseStatusError,
    UnknownModerationDecisionTypeError,
)

# ---------------------------------------------------------------------------
# ModerationCase (canon 14.1)
# ---------------------------------------------------------------------------


class ModerationCaseStatus(StrEnum):
    """Canon section 14.1's exact status list."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    ACTION_PROPOSED = "action_proposed"
    DECIDED = "decided"
    APPEALED = "appealed"
    CLOSED = "closed"


#: Canon section 14.1's transition table, verbatim. `closed` is terminal
#: (no outgoing transition from it).
CASE_ALLOWED_TRANSITIONS: frozenset[tuple[ModerationCaseStatus, ModerationCaseStatus]] = frozenset(
    {
        (ModerationCaseStatus.OPEN, ModerationCaseStatus.UNDER_REVIEW),
        (ModerationCaseStatus.UNDER_REVIEW, ModerationCaseStatus.ACTION_PROPOSED),
        (ModerationCaseStatus.ACTION_PROPOSED, ModerationCaseStatus.DECIDED),
        (ModerationCaseStatus.DECIDED, ModerationCaseStatus.APPEALED),
        (ModerationCaseStatus.DECIDED, ModerationCaseStatus.CLOSED),
        (ModerationCaseStatus.APPEALED, ModerationCaseStatus.CLOSED),
    }
)


def parse_case_status(value: str) -> ModerationCaseStatus:
    try:
        return ModerationCaseStatus(value)
    except ValueError as exc:
        raise UnknownModerationCaseStatusError(
            f"unknown moderation case status: {value!r}"
        ) from exc


def assert_case_transition_allowed(
    current: ModerationCaseStatus, target: ModerationCaseStatus
) -> None:
    if (current, target) not in CASE_ALLOWED_TRANSITIONS:
        raise ForbiddenModerationCaseTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class ModerationCase:
    """Canon section 14.1 fields exactly.

    `opened_by`/`assigned_moderator` are bare actor-id `UUID`s (not
    `epd2_core.event_envelope.ActorRef`) — this mirrors every other
    PACK-02 domain entity (e.g. `EligibilityDecision.subject_reference`):
    the envelope's richer `ActorRef` (with `actor_type`) is an
    event/command-layer concept, not a stored domain field.
    """

    moderation_case_id: UUID
    target_type: str
    target_id: UUID
    opened_by: UUID
    trigger_type: str
    policy_version: str
    status: ModerationCaseStatus
    assigned_moderator: UUID | None

    def __post_init__(self) -> None:
        if not self.target_type:
            raise ValueError("target_type must not be empty")
        if not self.trigger_type:
            raise ValueError("trigger_type must not be empty")
        if not self.policy_version:
            raise ValueError("policy_version must not be empty")

    def with_status(self, new_status: ModerationCaseStatus) -> ModerationCase:
        """Plain status transition, unaccompanied by any other field
        change. Use `with_assigned_moderator` for `open -> under_review`,
        which atomically sets `assigned_moderator` too."""
        assert_case_transition_allowed(self.status, new_status)
        return _replace_case(self, status=new_status)

    def with_assigned_moderator(self, moderator_id: UUID) -> ModerationCase:
        """`open -> under_review`, atomically recording who was
        assigned. Canon names no separate "assign without transition"
        operation — assignment and entering review are the one domain
        event `moderation.case_assigned`."""
        assert_case_transition_allowed(self.status, ModerationCaseStatus.UNDER_REVIEW)
        return _replace_case(
            self, status=ModerationCaseStatus.UNDER_REVIEW, assigned_moderator=moderator_id
        )


def _replace_case(
    case: ModerationCase,
    *,
    status: ModerationCaseStatus,
    assigned_moderator: UUID | None = None,
) -> ModerationCase:
    return ModerationCase(
        moderation_case_id=case.moderation_case_id,
        target_type=case.target_type,
        target_id=case.target_id,
        opened_by=case.opened_by,
        trigger_type=case.trigger_type,
        policy_version=case.policy_version,
        status=status,
        assigned_moderator=(
            assigned_moderator if assigned_moderator is not None else case.assigned_moderator
        ),
    )


# ---------------------------------------------------------------------------
# ModerationDecision (canon 14.2)
# ---------------------------------------------------------------------------


class ModerationDecisionType(StrEnum):
    """Canon section 14.2's exact `decision_type` list. This is a type
    enum, not a status — there is no transition table (a
    `ModerationDecision` is immutable once created; see the dataclass's
    own docstring below), but it still needs CT-00-02 unknown-value
    rejection via `parse_decision_type`."""

    NO_ACTION = "no_action"
    WARNING = "warning"
    TEMPORARY_HIDE = "temporary_hide"
    RESTORE = "restore"
    PARTICIPATION_LIMIT = "participation_limit"
    ACCOUNT_RESTRICTION_REQUEST = "account_restriction_request"
    ESCALATE = "escalate"
    REMOVE_FROM_PUBLIC_VIEW = "remove_from_public_view"


def parse_decision_type(value: str) -> ModerationDecisionType:
    try:
        return ModerationDecisionType(value)
    except ValueError as exc:
        raise UnknownModerationDecisionTypeError(f"unknown decision_type: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class ModerationDecision:
    """Canon section 14.2 fields exactly.

    Immutable once created — there is no update/patch command in this
    pack. Canon names no "amend a decision" operation, and PACK-03's own
    spec does not list one either; a correction is always a *new*
    `ModerationDecision` referencing the same `case_id` (out of this
    pack's scope to model as a first-class "supersedes" link — left as an
    explicit, documented gap; see README.md).

    `reason_code` here is canon's own field name (section 14.2) — a
    reason-code-registry STRING VALUE describing *why* the decision was
    made (e.g. `"MODERATION_POLICY_VIOLATION"`). This is a wholly
    different concept from this package's own Python exception classes'
    `reason_code` CLASS ATTRIBUTES (in `exceptions.py`), which describe
    *failures of this service's own API* — the two must never be
    conflated: this field only ever holds a value from the *decision*
    reason-code space, never one of this module's own exception codes
    (`VALIDATION_*`, `PERMISSION_DENIED`, etc).

    `audit_reference` is populated by `application.issue_decision` at
    construction time with the same id used as that call's
    `AppendAuditEventRequest.audit_event_id` — see that function's
    docstring for why this is correct from the moment the object is
    created rather than patched in afterward.
    """

    moderation_decision_id: UUID
    case_id: UUID
    decision_type: ModerationDecisionType
    reason_code: str
    policy_reference: str
    decided_by: UUID
    effective_from: datetime
    effective_until: datetime | None
    public_explanation: str
    audit_reference: str

    def __post_init__(self) -> None:
        if not self.reason_code:
            raise ValueError("reason_code must not be empty")
        if not self.policy_reference:
            raise ValueError("policy_reference must not be empty")
        if not self.audit_reference:
            raise ValueError("audit_reference must not be empty")
        if self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.effective_until is not None:
            if self.effective_until.tzinfo is None:
                raise ValueError("effective_until must be timezone-aware")
            if self.effective_until < self.effective_from:
                raise ValueError("effective_until must not precede effective_from")


# ---------------------------------------------------------------------------
# Appeal (canon 14.3)
# ---------------------------------------------------------------------------


class AppealStatus(StrEnum):
    """Canon section 14.3's exact status list."""

    SUBMITTED = "submitted"
    ADMISSIBILITY_REVIEW = "admissibility_review"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    PARTIALLY_UPHELD = "partially_upheld"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


#: The final REVIEW outcomes `application.decide_appeal` may produce —
#: deliberately excludes `WITHDRAWN` (a submitter-initiated action, not a
#: reviewer decision outcome; see `application.decide_appeal`'s own
#: docstring for why withdrawal has no dedicated application command in
#: this pack) and excludes the non-final statuses.
FINAL_APPEAL_OUTCOMES: frozenset[AppealStatus] = frozenset(
    {AppealStatus.UPHELD, AppealStatus.PARTIALLY_UPHELD, AppealStatus.REJECTED}
)

#: Canon section 14.3's transition table, verbatim. Every status in
#: `FINAL_APPEAL_OUTCOMES` plus `WITHDRAWN` is terminal.
APPEAL_ALLOWED_TRANSITIONS: frozenset[tuple[AppealStatus, AppealStatus]] = frozenset(
    {
        (AppealStatus.SUBMITTED, AppealStatus.ADMISSIBILITY_REVIEW),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.UNDER_REVIEW),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.REJECTED),
        (AppealStatus.UNDER_REVIEW, AppealStatus.UPHELD),
        (AppealStatus.UNDER_REVIEW, AppealStatus.PARTIALLY_UPHELD),
        (AppealStatus.UNDER_REVIEW, AppealStatus.REJECTED),
        (AppealStatus.SUBMITTED, AppealStatus.WITHDRAWN),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.WITHDRAWN),
        (AppealStatus.UNDER_REVIEW, AppealStatus.WITHDRAWN),
    }
)


def parse_appeal_status(value: str) -> AppealStatus:
    try:
        return AppealStatus(value)
    except ValueError as exc:
        raise UnknownAppealStatusError(f"unknown appeal status: {value!r}") from exc


def assert_appeal_transition_allowed(current: AppealStatus, target: AppealStatus) -> None:
    if (current, target) not in APPEAL_ALLOWED_TRANSITIONS:
        raise ForbiddenAppealTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Appeal:
    """Canon section 14.3 fields exactly.

    `result` is a free-text summary of the appeal's outcome, distinct
    from `status` (the enum recording *which* final state —
    `upheld`/`partially_upheld`/`rejected`/`withdrawn` — was reached).
    Canon names both fields (section 14.3) without further specifying
    `result`'s shape; modeled here as `str | None` (`None` until a final
    outcome is reached), the same shape
    `ModerationDecision.public_explanation` already uses for a free-text
    field that is not itself a reason code.

    `reviewer_actor_id` is the actor who is (or, once decided, was)
    reviewing this appeal — the field CT-00-06's role-separation check
    (`application.decide_appeal`) compares against the original
    `ModerationDecision.decided_by`.
    """

    appeal_id: UUID
    decision_id: UUID
    submitted_by: UUID
    grounds: str
    status: AppealStatus
    reviewer_actor_id: UUID | None
    result: str | None

    def __post_init__(self) -> None:
        if not self.grounds:
            raise ValueError("grounds must not be empty")

    def with_status(self, new_status: AppealStatus) -> Appeal:
        """Plain status transition with no reviewer/result change — used
        e.g. for a submitter-initiated `withdrawn` transition."""
        assert_appeal_transition_allowed(self.status, new_status)
        return _replace_appeal(self, status=new_status)

    def with_reviewer_and_status(
        self, *, reviewer_actor_id: UUID, new_status: AppealStatus, result: str | None
    ) -> Appeal:
        """Atomically record who reviewed this appeal, the new status,
        and (once a final outcome is reached) the free-text `result` —
        used by `application.decide_appeal` for each hop of its
        `submitted -> admissibility_review -> under_review -> <final>`
        walk."""
        assert_appeal_transition_allowed(self.status, new_status)
        return _replace_appeal(
            self, status=new_status, reviewer_actor_id=reviewer_actor_id, result=result
        )


def _replace_appeal(
    appeal: Appeal,
    *,
    status: AppealStatus,
    reviewer_actor_id: UUID | None = None,
    result: str | None = None,
) -> Appeal:
    return Appeal(
        appeal_id=appeal.appeal_id,
        decision_id=appeal.decision_id,
        submitted_by=appeal.submitted_by,
        grounds=appeal.grounds,
        status=status,
        reviewer_actor_id=(
            reviewer_actor_id if reviewer_actor_id is not None else appeal.reviewer_actor_id
        ),
        result=result if result is not None else appeal.result,
    )
