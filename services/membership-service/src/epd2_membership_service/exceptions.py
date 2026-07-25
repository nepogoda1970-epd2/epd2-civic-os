"""Membership Service exceptions, tied to stable reason codes (PACK-07,
canon-0.6.0). Generic-code reuses mirror this repository's established
precedent (e.g. `eligibility-service`'s own PACK-07 exceptions module):
a non-status enum or a plain lookup miss reuses the existing generic
code, never inventing a near-duplicate. Only genuinely new failure
shapes get a new code.
"""

from __future__ import annotations


class UnknownCriticalPolicyStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenCriticalPolicyTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownPartyMembershipEligibilityPolicyError(ValueError):
    """Plain lookup miss - no `PartyMembershipEligibilityPolicy` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class CriticalPolicyActivationNotAuthorizedError(ValueError):
    """Canon 19d.7's four-gate critical-policy activation rule, this
    service's own duplicated copy of `epd2_eligibility_service.exceptions.
    CriticalPolicyActivationNotAuthorizedError` (same reason code,
    independently declared - see `domain.assert_critical_policy_activation_gate`'s
    own docstring for why this is a documented duplicate, not an import)."""

    reason_code = "CRITICAL_POLICY_ACTIVATION_NOT_AUTHORIZED"


class CriticalPolicyVersionFrozenError(ValueError):
    """This service's own copy of `epd2_eligibility_service.exceptions.
    CriticalPolicyVersionFrozenError` (same reason code, independently
    declared). Declared for forward compatibility but deliberately
    UNRAISED in this implementation round - see that class's own
    docstring for why: enforcing it needs a persisted Process/Election
    aggregate this pack does not introduce."""

    reason_code = "CRITICAL_POLICY_VERSION_FROZEN"


class UnknownMembershipError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownMembershipStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenMembershipTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownMembershipApplicationError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownMembershipApplicationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenMembershipApplicationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class MembershipHumanApprovalRequiredError(ValueError):
    """Canon 19d.16's hard human-control invariant: raised whenever a
    code path would otherwise reach admission, rejection, activation,
    suspension, termination, an incompatibility finding, or restoration
    without a recorded, authorized human decision reference."""

    reason_code = "MEMBERSHIP_HUMAN_APPROVAL_REQUIRED"


class MembershipDecisionAuthorityInvalidError(ValueError):
    """Raised when a Stage B decision's `decision_authority_reference`
    does not resolve to a real, `approved` `GovernanceDecision`
    (`governance-service.verify_decision_authorizes_policy_activation`,
    reused generically - ADR-027)."""

    reason_code = "MEMBERSHIP_DECISION_AUTHORITY_INVALID"


class MembershipStatusDisclosureProhibitedError(ValueError):
    """ADR-030 item 5: membership status/existence is restricted by
    default - raised when a caller requests disclosure without a
    recorded opt-in consent or legal-mandate basis."""

    reason_code = "MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED"


class MembershipPublicationConsentMissingError(ValueError):
    """ADR-030 item 5: raised when publication is claimed to be opt-in
    but no consent evidence reference is supplied."""

    reason_code = "MEMBERSHIP_PUBLICATION_CONSENT_MISSING"


class UnknownAffiliationDeclarationError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAffiliationTypeError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAffiliationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAffiliationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownAffiliationVerificationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownConflictAssessmentError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownConflictTypeError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownIncompatibilityLevelError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownConflictAssessmentStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenConflictAssessmentTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ConflictReviewSelfApprovalProhibitedError(ValueError):
    """Canon 19d.11: the reviewer verifying `decision_authority_reference`
    must never be the same actor who submitted the underlying
    `AffiliationDeclaration` (ADR-029's registered code, reused here)."""

    reason_code = "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"


class ConflictDecisionAuthorityRequiredError(ValueError):
    """Canon 19d.11: `decision_authority_reference` is mandatory once a
    `ConflictAssessment` reaches `resolved_incompatible`."""

    reason_code = "MEMBERSHIP_DECISION_AUTHORITY_INVALID"


class UnknownAppealStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAppealTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownAppealError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"
