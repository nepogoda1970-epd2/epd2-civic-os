"""Governance Service exceptions, tied to stable reason codes (ADR-004 /
ADR-006 / ADR-014 / ADR-019 pattern: one exception class per distinct
failure shape, never free text — canon section 24: "reason code не
заменяется свободным текстом"). The nine codes carried forward from
`docs/handover/PACK-05-SPEC.md` section 7 and the four codes ADR-019
added are each represented here by exactly one class.
"""

from __future__ import annotations

# --- RoleAssignment ---------------------------------------------------------


class UnknownRoleAssignmentStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenRoleAssignmentTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownRoleAssignmentError(ValueError):
    """Plain lookup miss — no `RoleAssignment` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class RoleAssignmentConflictError(ValueError):
    """A repeated `request_role_assignment` request with the same
    `role_assignment_id` but different content."""

    reason_code = "ROLE_ASSIGNMENT_DUPLICATE_CONFLICT"


class RoleAssignmentNotActiveError(ValueError):
    """ADR-020 §1/§5. Raised when a command requires an `active`,
    unexpired `RoleAssignment` and the referenced one is not (wrong
    status, or `valid_until` has passed as of the command's clock)."""

    reason_code = "ROLE_ASSIGNMENT_NOT_ACTIVE"


class RoleAssignmentScopeMismatchError(ValueError):
    """ADR-020 §1. Raised when a `RoleAssignment` is active but its
    `scope_id` does not cover the subject of the action being
    authorized (neither an exact match nor `domain.GLOBAL_SCOPE_ID`)."""

    reason_code = "ROLE_ASSIGNMENT_SCOPE_MISMATCH"


# --- GovernancePolicy --------------------------------------------------------


class UnknownGovernancePolicyStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenGovernancePolicyTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownGovernancePolicyError(ValueError):
    """Plain lookup miss — no `GovernancePolicy` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class GovernancePolicyConflictError(ValueError):
    """A repeated `propose_governance_policy` request with the same
    `governance_policy_id` but different content."""

    reason_code = "GOVERNANCE_POLICY_DUPLICATE_CONFLICT"


class GovernancePolicyViolationError(ValueError):
    """Reserved (ADR-019 carried-forward code). No command in this
    package currently raises it directly — kept for a future caller
    that resolves a `GovernancePolicy` of `policy_type = approval_rule`
    / `challenge_rule` / `oversight_rule` against candidate content and
    needs a stable identity for "this violates the active policy",
    mirroring `epd2_transparency_service.exceptions.
    DisclosurePolicyViolationError`'s own reserved-code precedent."""

    reason_code = "GOVERNANCE_POLICY_VIOLATION"


# --- GovernanceDecision -------------------------------------------------------


class UnknownGovernanceDecisionStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenGovernanceDecisionTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownGovernanceDecisionError(ValueError):
    """Plain lookup miss — no `GovernanceDecision` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class GovernanceDecisionConflictError(ValueError):
    """A repeated `propose_governance_decision` request with the same
    `governance_decision_id` but different content."""

    reason_code = "GOVERNANCE_DECISION_DUPLICATE_CONFLICT"


class GovernanceDecisionNotApprovedError(ValueError):
    """Raised when a command requires an `approved`, non-superseded
    `GovernanceDecision` of a specific `decision_type`/subject and the
    referenced decision does not qualify (wrong status, wrong
    `decision_type`, or does not reference the expected subject).
    This is the exact code `voting-service.invalidate_ballot` raises
    when the `GovernanceDecision` it is given is not a qualifying,
    approved `ballot_invalidation` decision for that `Ballot` (ADR-017
    Option B)."""

    reason_code = "GOVERNANCE_DECISION_NOT_APPROVED"


class GovernanceDecisionSupersededError(ValueError):
    """ADR-019 code. Raised when any command attempts to act on a
    `GovernanceDecision` that has since been superseded (another,
    later `GovernanceDecision` exists with `supersedes_decision_id`
    equal to this one's id) — only the superseding decision, never the
    superseded one, may authorize a downstream action."""

    reason_code = "GOVERNANCE_DECISION_SUPERSEDED"


class ResultFinalityBlockedByOpenChallengeError(ValueError):
    """ADR-019 code / canon 19b.5. Raised when a
    `result_finality_determination` `GovernanceDecision` is proposed or
    approved for a `ResultPublication` that still has one or more
    `submitted`/`under_review` `TechnicalChallenge` records."""

    reason_code = "RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE"


class ResultFinalityDeterminationDuplicateError(ValueError):
    """ADR-019 code / canon 19b.5. Raised when a second, independent
    `result_finality_determination` decision is attempted for a
    `ResultPublication` that already has an `approved`, non-superseded
    one — a correction must set `supersedes_decision_id` instead."""

    reason_code = "RESULT_FINALITY_DETERMINATION_DUPLICATE"


class ResultFinalityNotAuthorizedError(ValueError):
    """ADR-019 code, narrowed by ADR-017: applies only to a would-be
    direct query/action against `ResultPublication` finality state
    that bypasses `get_finality_status` entirely — no `tally-service`
    command exists for this code to gate, so no command in this
    package currently raises it; kept for a future caller that adds
    such a bypass-detection check."""

    reason_code = "RESULT_FINALITY_NOT_AUTHORIZED"


# --- TechnicalChallenge -------------------------------------------------------


class UnknownTechnicalChallengeStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenTechnicalChallengeTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownTechnicalChallengeError(ValueError):
    """Plain lookup miss — no `TechnicalChallenge` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class TechnicalChallengeConflictError(ValueError):
    """A repeated `submit_technical_challenge` request with the same
    `technical_challenge_id` but different content."""

    reason_code = "TECHNICAL_CHALLENGE_DUPLICATE_CONFLICT"


class TechnicalChallengeWindowClosedError(ValueError):
    """Raised by `submit_technical_challenge` when `submitted_at` does
    not strictly precede the challenged `ResultPublication`'s
    `challenge_deadline_at` (canon 19b.4)."""

    reason_code = "TECHNICAL_CHALLENGE_WINDOW_CLOSED"


class TechnicalChallengeAlreadyAdjudicatedError(ValueError):
    """Raised when a command attempts to move a `TechnicalChallenge`
    that is already `upheld` or `rejected` — canon 19b.4: no transition
    exists out of either terminal status."""

    reason_code = "TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED"


class TechnicalChallengeSubmitterIneligibleError(ValueError):
    """ADR-019 code / ADR-020 item 2. Raised by `submit_technical_
    challenge` when the caller's `submitter_authorization_type =
    role_assignment` reference resolves to a `RoleAssignment` that is
    not `active`, not in scope, or does not exist."""

    reason_code = "TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE"


# --- Cross-cutting two-actor / authority codes (ADR-020 §1) ------------------


class TwoActorApprovalRequiredError(ValueError):
    """ADR-020 item 1 / INV-08. Raised when a command that structurally
    requires two distinct, active, in-scope `RoleAssignment` actors
    (GovernancePolicy activation, every GovernanceDecision approval —
    which includes ballot invalidation and result-finality
    determination as named `decision_type` values, and RoleAssignment
    grant self-grant prevention) is missing one of the two required
    references."""

    reason_code = "TWO_ACTOR_APPROVAL_REQUIRED"


class SameActorApprovalRejectedError(ValueError):
    """ADR-020 item 1 / INV-08. Raised when the proposer and approver
    (or, for `RoleAssignment`, the granter and the actor being granted
    the role) resolve to the same underlying actor — "no role may
    approve or grant its own assignment"."""

    reason_code = "SAME_ACTOR_APPROVAL_REJECTED"


class BallotInvalidationNotAuthorizedError(ValueError):
    """Raised by `voting-service.invalidate_ballot` (not by this
    package directly, but this class is the stable, shared identity
    for that failure — see `docs/handover/PACK-05-SPEC.md` section 7)
    when no qualifying, approved `ballot_invalidation`
    `GovernanceDecision` for the target `Ballot` can be found."""

    reason_code = "BALLOT_INVALIDATION_NOT_AUTHORIZED"
