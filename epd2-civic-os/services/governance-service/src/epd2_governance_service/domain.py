"""`RoleAssignment`, `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`, plus the derived `FinalityStatus` read model, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 19b (added by canon
0.4.0, ADR-018) and section 8.4 (`RoleAssignment`, unchanged, its first
physical implementation here per ADR-016).

This package consolidates canon's Governance Context into one physical
`uv` workspace member, `governance-service` (ADR-016), alongside the
already-canon-defined `RoleAssignment`.

Two implementation decisions this module documents up front, since canon
19b deliberately leaves them to repository-level design (the same way
canon 19a left `DisclosurePolicy.field_rules`'s exact shape to
PACK-04's own ADR-013 amendment):

1. `RoleAssignment.role_code` is stored as an open string (canon 19b.1:
   "role_code остаётся открытой строкой на уровне канона (8.4)") — the
   closed, eight-value pilot taxonomy (ADR-020 §5) is enforced only at
   the `application.py` command layer (`PILOT_ROLE_CODES`), never as a
   structural `__post_init__` invariant here, so this domain object
   never contradicts canon's own explicit "still an open string" text.
2. `scope_id` matching for authorization ("both RoleAssignments must be
   ... in scope", ADR-020 item 1) is implemented as: the RoleAssignment's
   `scope_id` equals the specific subject being acted on (e.g. a
   `Ballot`/`ResultPublication`/`TechnicalChallenge` id), OR equals
   `GLOBAL_SCOPE_ID` — a reserved sentinel representing a role scoped to
   the entire pilot deployment (typically only ever held by a
   bootstrap-seeded actor, see `bootstrap.py`). Canon's own `scope_id`
   field (8.4) is deliberately generic and does not define this
   convention itself; it is this package's own reading of "in scope".
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_governance_service.exceptions import (
    ForbiddenGovernanceDecisionTransitionError,
    ForbiddenGovernancePolicyTransitionError,
    ForbiddenRoleAssignmentTransitionError,
    ForbiddenTechnicalChallengeTransitionError,
    UnknownGovernanceDecisionStatusError,
    UnknownGovernancePolicyStatusError,
    UnknownRoleAssignmentStatusError,
    UnknownTechnicalChallengeStatusError,
)

#: A reserved sentinel `scope_id` meaning "this RoleAssignment's authority
#: covers the entire pilot deployment", not one specific ballot / result
#: publication / policy subject. Used almost exclusively by
#: bootstrap-seeded RoleAssignments (`bootstrap.py`); an ordinary,
#: later-granted RoleAssignment is expected to carry a real, specific
#: `scope_id` instead. Deliberately not the RFC 4122 nil UUID, so a
#: caller cannot confuse an accidentally-unset scope with a deliberate
#: global grant.
GLOBAL_SCOPE_ID: UUID = UUID("00000000-0000-0000-0000-0000000005c0")

#: Canon 19b.1 / ADR-020 §5's closed pilot role taxonomy — see this
#: module's docstring, point 1, for why this is enforced at the
#: application layer, not here.
PILOT_ROLE_CODES: frozenset[str] = frozenset(
    {
        "governance_policy_proposer",
        "governance_policy_approver",
        "governance_reviewer",
        "technical_challenge_reviewer",
        "ballot_invalidation_proposer",
        "ballot_invalidation_approver",
        "oversight_reviewer",
        "observer",
    }
)


def scope_covers(role_scope_id: UUID, subject_scope_id: UUID) -> bool:
    """`True` if a `RoleAssignment` whose `scope_id` is `role_scope_id`
    is authorized to act on a subject scoped to `subject_scope_id` —
    either an exact match or `GLOBAL_SCOPE_ID` (this module's docstring,
    point 2)."""
    return role_scope_id in (subject_scope_id, GLOBAL_SCOPE_ID)


# ---------------------------------------------------------------------------
# RoleAssignment (canon 8.4, integrated 19b.1)
# ---------------------------------------------------------------------------


class RoleAssignmentStatus(StrEnum):
    """Canon section 8.4's exact status list (five values)."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


def parse_role_assignment_status(value: str) -> RoleAssignmentStatus:
    try:
        return RoleAssignmentStatus(value)
    except ValueError as exc:
        raise UnknownRoleAssignmentStatusError(
            f"unknown role assignment status: {value!r}"
        ) from exc


#: This package's own transition table — canon 8.4 lists only the status
#: values, not a transition table, since `RoleAssignment` had never been
#: physically implemented before this pack (ADR-016). `suspended`/
#: `expired` are included for completeness with canon's status list and
#: for CT-00-03 (forbidden-transition) coverage, even though no
#: dedicated `application.py` command currently drives them — see
#: README.md's "Known gaps" (the same documented-gap pattern
#: `epd2_transparency_service` used for `LobbyLogEntry`'s publication
#: deadline).
ROLE_ASSIGNMENT_ALLOWED_TRANSITIONS: frozenset[
    tuple[RoleAssignmentStatus, RoleAssignmentStatus]
] = frozenset(
    {
        (RoleAssignmentStatus.PENDING, RoleAssignmentStatus.ACTIVE),
        (RoleAssignmentStatus.PENDING, RoleAssignmentStatus.REVOKED),
        (RoleAssignmentStatus.ACTIVE, RoleAssignmentStatus.SUSPENDED),
        (RoleAssignmentStatus.SUSPENDED, RoleAssignmentStatus.ACTIVE),
        (RoleAssignmentStatus.ACTIVE, RoleAssignmentStatus.EXPIRED),
        (RoleAssignmentStatus.SUSPENDED, RoleAssignmentStatus.EXPIRED),
        (RoleAssignmentStatus.ACTIVE, RoleAssignmentStatus.REVOKED),
        (RoleAssignmentStatus.SUSPENDED, RoleAssignmentStatus.REVOKED),
    }
)


def assert_role_assignment_transition_allowed(
    current: RoleAssignmentStatus, target: RoleAssignmentStatus
) -> None:
    if (current, target) not in ROLE_ASSIGNMENT_ALLOWED_TRANSITIONS:
        raise ForbiddenRoleAssignmentTransitionError(
            f"role assignment transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    """Canon section 8.4 fields exactly, unchanged by canon 0.4.0
    (19b.1). `assigned_by` is a UUID referencing the *granting*
    `RoleAssignment.role_assignment_id` that authorized this grant —
    for the two bootstrap-seeded rows, `bootstrap.
    BOOTSTRAP_ASSIGNED_BY_MARKER` is used instead, since no prior
    `RoleAssignment` can exist yet at that point (see `bootstrap.py`).
    """

    role_assignment_id: UUID
    actor_id: UUID
    role_code: str
    scope_id: UUID
    valid_from: datetime
    valid_until: datetime | None
    assigned_by: UUID
    approval_reference: str | None
    status: RoleAssignmentStatus

    def __post_init__(self) -> None:
        if not self.role_code:
            raise ValueError("role_code must not be empty")
        if self.valid_from.tzinfo is None:
            raise ValueError("valid_from must be timezone-aware")
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("valid_until must be timezone-aware")
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")

    def with_status(self, new_status: RoleAssignmentStatus) -> RoleAssignment:
        assert_role_assignment_transition_allowed(self.status, new_status)
        return _replace_role_assignment(self, status=new_status)

    def is_active_at(self, at: datetime) -> bool:
        """`True` if `status == active` and `at` falls within
        `[valid_from, valid_until)` (an unset `valid_until` never
        expires)."""
        if self.status is not RoleAssignmentStatus.ACTIVE:
            return False
        if at < self.valid_from:
            return False
        return not (self.valid_until is not None and at >= self.valid_until)


def _replace_role_assignment(
    assignment: RoleAssignment, *, status: RoleAssignmentStatus
) -> RoleAssignment:
    return RoleAssignment(
        role_assignment_id=assignment.role_assignment_id,
        actor_id=assignment.actor_id,
        role_code=assignment.role_code,
        scope_id=assignment.scope_id,
        valid_from=assignment.valid_from,
        valid_until=assignment.valid_until,
        assigned_by=assignment.assigned_by,
        approval_reference=assignment.approval_reference,
        status=status,
    )


# ---------------------------------------------------------------------------
# GovernancePolicy (canon 19b.2)
# ---------------------------------------------------------------------------


class GovernancePolicyType(StrEnum):
    """Canon section 19b.2's exact `policy_type` list."""

    ROLE_TAXONOMY = "role_taxonomy"
    APPROVAL_RULE = "approval_rule"
    CHALLENGE_RULE = "challenge_rule"
    OVERSIGHT_RULE = "oversight_rule"


class GovernancePolicyStatus(StrEnum):
    """Canon section 19b.2's exact status list."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


#: Canon section 19b.2's transition table: `draft -> active` (requires
#: `approved_by_role_id` distinct from `proposed_by_role_id`, INV-08);
#: `active -> superseded` (only when a new version activates for the
#: same `policy_type` — never a standalone command). No return to `draft`.
GOVERNANCE_POLICY_ALLOWED_TRANSITIONS: frozenset[
    tuple[GovernancePolicyStatus, GovernancePolicyStatus]
] = frozenset(
    {
        (GovernancePolicyStatus.DRAFT, GovernancePolicyStatus.ACTIVE),
        (GovernancePolicyStatus.ACTIVE, GovernancePolicyStatus.SUPERSEDED),
    }
)


def parse_governance_policy_status(value: str) -> GovernancePolicyStatus:
    try:
        return GovernancePolicyStatus(value)
    except ValueError as exc:
        raise UnknownGovernancePolicyStatusError(
            f"unknown governance policy status: {value!r}"
        ) from exc


def assert_governance_policy_transition_allowed(
    current: GovernancePolicyStatus, target: GovernancePolicyStatus
) -> None:
    if (current, target) not in GOVERNANCE_POLICY_ALLOWED_TRANSITIONS:
        raise ForbiddenGovernancePolicyTransitionError(
            f"governance policy transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    """Canon section 19b.2 fields exactly. Unlike
    `epd2_transparency_service.domain.DisclosurePolicy.
    approved_by_role_id` (nullable until `active`), canon 19b.2 states
    `approved_by_role_id` is "не nullable" — this package's reading
    (documented here since canon leaves the exact mechanics to
    implementation) is that both the proposer and the *designated*
    approver are known and recorded from the moment a `GovernancePolicy`
    is proposed, not only once activation has actually happened;
    `application.activate_governance_policy` re-validates both
    references are still active/in-scope/distinct at the moment of
    activation, since validity can change between proposal and
    activation.
    """

    governance_policy_id: UUID
    policy_type: GovernancePolicyType
    rule_definition: Mapping[str, object]
    effective_from: datetime
    proposed_by_role_id: UUID
    approved_by_role_id: UUID
    version: int
    status: GovernancePolicyStatus

    def __post_init__(self) -> None:
        if self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if self.approved_by_role_id == self.proposed_by_role_id:
            raise ValueError(
                "approved_by_role_id must differ from proposed_by_role_id (INV-08, ADR-020 item 1)"
            )

    def with_status(self, new_status: GovernancePolicyStatus) -> GovernancePolicy:
        assert_governance_policy_transition_allowed(self.status, new_status)
        return _replace_governance_policy(self, status=new_status)


def _replace_governance_policy(
    policy: GovernancePolicy, *, status: GovernancePolicyStatus
) -> GovernancePolicy:
    return GovernancePolicy(
        governance_policy_id=policy.governance_policy_id,
        policy_type=policy.policy_type,
        rule_definition=policy.rule_definition,
        effective_from=policy.effective_from,
        proposed_by_role_id=policy.proposed_by_role_id,
        approved_by_role_id=policy.approved_by_role_id,
        version=policy.version,
        status=status,
    )


# ---------------------------------------------------------------------------
# GovernanceDecision (canon 19b.3)
# ---------------------------------------------------------------------------


class GovernanceDecisionType(StrEnum):
    """Canon section 19b.3's exact minimum required `decision_type`
    list (canon: "обязан включать не менее")."""

    BALLOT_INVALIDATION = "ballot_invalidation"
    TECHNICAL_CHALLENGE_ADJUDICATION = "technical_challenge_adjudication"
    RESULT_FINALITY_DETERMINATION = "result_finality_determination"
    MANDATE = "mandate"
    OVERSIGHT_DIRECTIVE = "oversight_directive"


class GovernanceDecisionStatus(StrEnum):
    """Canon section 19b.3's exact *stored* status list. `superseded` is
    deliberately absent — it is never a stored value (19b.3)."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


class FinalityOutcome(StrEnum):
    """Canon section 19b.3's exact stored `finality_outcome` values —
    only meaningful when `decision_type = result_finality_determination`
    and only ever set once, at the moment of transition to `approved`.
    Deliberately a *different* type from `FinalityStatus` below (canon
    19b.3: "обязательно к реализации как два различных определения типа
    ... никогда как один общий четырёхзначный enum")."""

    FINAL = "final"
    INVALIDATED = "invalidated"


class FinalityStatus(StrEnum):
    """Canon section 19b.3's derived, four-value read-model type —
    never a stored field of any entity; only ever returned by
    `application.get_finality_status`. See this class's own values'
    docstrings in canon 19b.3 for the full derivation rule; summarized:
    `provisional`/`finality_blocked` are always computed fresh from
    `TechnicalChallenge` state and the absence of a qualifying decision;
    `final`/`invalidated` mirror an existing approved, non-superseded
    `result_finality_determination` decision's `finality_outcome`."""

    PROVISIONAL = "provisional"
    FINALITY_BLOCKED = "finality_blocked"
    FINAL = "final"
    INVALIDATED = "invalidated"


#: Canon section 19b.3's transition table: `proposed -> approved`
#: (requires `approved_by_role_id` distinct from `proposed_by_role_id`);
#: `proposed -> rejected` (requires `rejected_by_role_id` distinct from
#: `proposed_by_role_id`). No transition into any `superseded` value
#: exists, because no such stored value exists. No transition out of
#: `approved`/`rejected` — a `GovernanceDecision` is immutable once
#: decided (19b.3); a correction is always a brand-new record with
#: `supersedes_decision_id` set, never a further transition of this row.
GOVERNANCE_DECISION_ALLOWED_TRANSITIONS: frozenset[
    tuple[GovernanceDecisionStatus, GovernanceDecisionStatus]
] = frozenset(
    {
        (GovernanceDecisionStatus.PROPOSED, GovernanceDecisionStatus.APPROVED),
        (GovernanceDecisionStatus.PROPOSED, GovernanceDecisionStatus.REJECTED),
    }
)


def parse_governance_decision_status(value: str) -> GovernanceDecisionStatus:
    try:
        return GovernanceDecisionStatus(value)
    except ValueError as exc:
        raise UnknownGovernanceDecisionStatusError(
            f"unknown governance decision status: {value!r}"
        ) from exc


def assert_governance_decision_transition_allowed(
    current: GovernanceDecisionStatus, target: GovernanceDecisionStatus
) -> None:
    if (current, target) not in GOVERNANCE_DECISION_ALLOWED_TRANSITIONS:
        raise ForbiddenGovernanceDecisionTransitionError(
            f"governance decision transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    """Canon section 19b.3 fields exactly. Immutable once `approved` or
    `rejected` — no field, including `finality_outcome`,
    `evidence_references`, or `reason_code`, may ever be rewritten by a
    later command; a correction is always a new
    `GovernanceDecision` row with `supersedes_decision_id` set (19b.3).
    """

    governance_decision_id: UUID
    decision_type: GovernanceDecisionType
    subject_reference: Mapping[str, object]
    proposed_by_role_id: UUID
    approved_by_role_id: UUID | None
    rejected_by_role_id: UUID | None
    reason_code: str
    evidence_references: tuple[str, ...]
    finality_outcome: FinalityOutcome | None
    created_at: datetime
    decided_at: datetime | None
    supersedes_decision_id: UUID | None
    status: GovernanceDecisionStatus

    def __post_init__(self) -> None:
        if not self.reason_code:
            raise ValueError("reason_code must not be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.decided_at is not None and self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")
        if (self.status is GovernanceDecisionStatus.PROPOSED) != (self.decided_at is None):
            raise ValueError("decided_at must be set if and only if status is not 'proposed'")
        if self.status is GovernanceDecisionStatus.APPROVED:
            if self.approved_by_role_id is None:
                raise ValueError("approved_by_role_id must be set when status is 'approved'")
            if self.approved_by_role_id == self.proposed_by_role_id:
                raise ValueError(
                    "approved_by_role_id must differ from proposed_by_role_id "
                    "(INV-08, ADR-020 item 1)"
                )
        if self.status is GovernanceDecisionStatus.REJECTED:
            if self.rejected_by_role_id is None:
                raise ValueError("rejected_by_role_id must be set when status is 'rejected'")
            if self.rejected_by_role_id == self.proposed_by_role_id:
                raise ValueError(
                    "rejected_by_role_id must differ from proposed_by_role_id "
                    "(INV-08, ADR-020 item 1)"
                )
        if self.finality_outcome is not None:
            if self.decision_type is not GovernanceDecisionType.RESULT_FINALITY_DETERMINATION:
                raise ValueError(
                    "finality_outcome is only meaningful for "
                    "decision_type='result_finality_determination'"
                )
            if self.status is not GovernanceDecisionStatus.APPROVED:
                raise ValueError("finality_outcome may only be set on an 'approved' decision")
        if "vote_envelope_id" in self.subject_reference:
            raise ValueError(
                "subject_reference must never reference a VoteEnvelope directly (canon 19b.3)"
            )

    def with_approved(
        self,
        *,
        approved_by_role_id: UUID,
        decided_at: datetime,
        finality_outcome: FinalityOutcome | None,
    ) -> GovernanceDecision:
        assert_governance_decision_transition_allowed(
            self.status, GovernanceDecisionStatus.APPROVED
        )
        return _replace_governance_decision(
            self,
            status=GovernanceDecisionStatus.APPROVED,
            approved_by_role_id=approved_by_role_id,
            rejected_by_role_id=None,
            decided_at=decided_at,
            finality_outcome=finality_outcome,
        )

    def with_rejected(
        self, *, rejected_by_role_id: UUID, decided_at: datetime
    ) -> GovernanceDecision:
        assert_governance_decision_transition_allowed(
            self.status, GovernanceDecisionStatus.REJECTED
        )
        return _replace_governance_decision(
            self,
            status=GovernanceDecisionStatus.REJECTED,
            approved_by_role_id=None,
            rejected_by_role_id=rejected_by_role_id,
            decided_at=decided_at,
            finality_outcome=None,
        )


def _replace_governance_decision(
    decision: GovernanceDecision,
    *,
    status: GovernanceDecisionStatus,
    approved_by_role_id: UUID | None,
    rejected_by_role_id: UUID | None,
    decided_at: datetime | None,
    finality_outcome: FinalityOutcome | None,
) -> GovernanceDecision:
    return GovernanceDecision(
        governance_decision_id=decision.governance_decision_id,
        decision_type=decision.decision_type,
        subject_reference=decision.subject_reference,
        proposed_by_role_id=decision.proposed_by_role_id,
        approved_by_role_id=approved_by_role_id,
        rejected_by_role_id=rejected_by_role_id,
        reason_code=decision.reason_code,
        evidence_references=decision.evidence_references,
        finality_outcome=finality_outcome,
        created_at=decision.created_at,
        decided_at=decided_at,
        supersedes_decision_id=decision.supersedes_decision_id,
        status=status,
    )


# ---------------------------------------------------------------------------
# TechnicalChallenge (canon 19b.4)
# ---------------------------------------------------------------------------


class SubmitterAuthorizationType(StrEnum):
    """Canon section 19b.4's exact `submitter_authorization_type` list."""

    PARTICIPATION_CREDENTIAL = "participation_credential"
    ROLE_ASSIGNMENT = "role_assignment"


class TechnicalChallengeStatus(StrEnum):
    """Canon section 19b.4's exact status list."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    REJECTED = "rejected"


#: Canon section 19b.4's transition table: `submitted -> under_review`;
#: `under_review -> upheld` / `under_review -> rejected` (both only
#: through a linked `GovernanceDecision`, 19b.3 —
#: `application.approve_governance_decision`/`reject_governance_decision`
#: apply these as a side effect when `decision_type =
#: technical_challenge_adjudication`, never a standalone command). No
#: transition out of `upheld`/`rejected` — a new integrity concern
#: requires an entirely new `TechnicalChallenge` row (19b.4).
TECHNICAL_CHALLENGE_ALLOWED_TRANSITIONS: frozenset[
    tuple[TechnicalChallengeStatus, TechnicalChallengeStatus]
] = frozenset(
    {
        (TechnicalChallengeStatus.SUBMITTED, TechnicalChallengeStatus.UNDER_REVIEW),
        (TechnicalChallengeStatus.UNDER_REVIEW, TechnicalChallengeStatus.UPHELD),
        (TechnicalChallengeStatus.UNDER_REVIEW, TechnicalChallengeStatus.REJECTED),
    }
)


def parse_technical_challenge_status(value: str) -> TechnicalChallengeStatus:
    try:
        return TechnicalChallengeStatus(value)
    except ValueError as exc:
        raise UnknownTechnicalChallengeStatusError(
            f"unknown technical challenge status: {value!r}"
        ) from exc


def assert_technical_challenge_transition_allowed(
    current: TechnicalChallengeStatus, target: TechnicalChallengeStatus
) -> None:
    if (current, target) not in TECHNICAL_CHALLENGE_ALLOWED_TRANSITIONS:
        raise ForbiddenTechnicalChallengeTransitionError(
            f"technical challenge transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: `TechnicalChallenge` statuses for which the challenge is still
#: unresolved (canon 19b.5: finality is blocked while any challenge
#: against the same `ResultPublication` remains in one of these).
UNRESOLVED_TECHNICAL_CHALLENGE_STATUSES: frozenset[TechnicalChallengeStatus] = frozenset(
    {TechnicalChallengeStatus.SUBMITTED, TechnicalChallengeStatus.UNDER_REVIEW}
)


@dataclass(frozen=True, slots=True)
class TechnicalChallenge:
    """Canon section 19b.4 fields exactly.
    `submitter_authorization_reference` is a real, stored, opaque
    reference — this domain object still stores it (mirroring
    `PublicLedgerEntry.published_by_role_id`'s precedent, canon 19a.1);
    the "never published verbatim" rule (canon 19b.4) is enforced one
    layer up, in `events.py`'s `*_public_payload`, the only function
    anyone should serialize a `TechnicalChallenge` through for external
    consumption.
    """

    technical_challenge_id: UUID
    result_publication_id: UUID
    submitter_authorization_type: SubmitterAuthorizationType
    submitter_authorization_reference: str
    challenge_reason_code: str
    evidence_references: tuple[str, ...]
    submitted_at: datetime
    governance_decision_id: UUID | None
    status: TechnicalChallengeStatus

    def __post_init__(self) -> None:
        if not self.submitter_authorization_reference:
            raise ValueError("submitter_authorization_reference must not be empty")
        if not self.challenge_reason_code:
            raise ValueError("challenge_reason_code must not be empty")
        if self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware")
        if (
            self.status
            in (
                TechnicalChallengeStatus.UPHELD,
                TechnicalChallengeStatus.REJECTED,
            )
            and self.governance_decision_id is None
        ):
            raise ValueError(
                "governance_decision_id must be set once status is 'upheld' or 'rejected'"
            )

    def with_status(
        self, new_status: TechnicalChallengeStatus, *, governance_decision_id: UUID | None = None
    ) -> TechnicalChallenge:
        assert_technical_challenge_transition_allowed(self.status, new_status)
        return _replace_technical_challenge(
            self,
            status=new_status,
            governance_decision_id=(
                governance_decision_id
                if governance_decision_id is not None
                else self.governance_decision_id
            ),
        )


def _replace_technical_challenge(
    challenge: TechnicalChallenge,
    *,
    status: TechnicalChallengeStatus,
    governance_decision_id: UUID | None,
) -> TechnicalChallenge:
    return TechnicalChallenge(
        technical_challenge_id=challenge.technical_challenge_id,
        result_publication_id=challenge.result_publication_id,
        submitter_authorization_type=challenge.submitter_authorization_type,
        submitter_authorization_reference=challenge.submitter_authorization_reference,
        challenge_reason_code=challenge.challenge_reason_code,
        evidence_references=challenge.evidence_references,
        submitted_at=challenge.submitted_at,
        governance_decision_id=governance_decision_id,
        status=status,
    )
