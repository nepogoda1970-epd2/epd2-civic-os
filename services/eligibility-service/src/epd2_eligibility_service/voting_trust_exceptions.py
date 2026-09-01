"""PACK-15 voting-trust refusals raised by `eligibility-service`.

One class per registered reason code, following the repository's existing
convention (ADR-004): the code is a plain class attribute, and this module
imports nothing from the reason-code registry so that a service never
depends on the YAML at runtime. Every literal below is registered in
`contracts/reason-codes/pack-15.yml` and the correspondence is asserted by
`tests/contract/test_reason_codes_registry.py`.

**There is no generic voting error here, and none may be added.** Where two
failures differ in what the participant must do next, they are two classes
(PACK-15 specification section 28).
"""

from __future__ import annotations


class VotingTrustError(ValueError):
    """Base class for every PACK-15 refusal raised on the identity side.

    Carries no `reason_code` of its own: a refusal without a registered
    code is not a permissible refusal in this domain, so the base class is
    never raised directly.
    """


class EligibilityDeniedError(VotingTrustError):
    reason_code = "ELIGIBILITY_DENIED"


class EligibilityReviewRequiredError(VotingTrustError):
    """Not a denial. Presenting it as one is a documented content error."""

    reason_code = "ELIGIBILITY_REVIEW_REQUIRED"


class EligibilityMembershipInactiveError(VotingTrustError):
    reason_code = "ELIGIBILITY_MEMBERSHIP_INACTIVE"


class EligibilityScopeMismatchError(VotingTrustError):
    reason_code = "ELIGIBILITY_SCOPE_MISMATCH"


class EligibilityRuleNotSatisfiedError(VotingTrustError):
    reason_code = "ELIGIBILITY_RULE_NOT_SATISFIED"


class EligibilityAssuranceInsufficientError(VotingTrustError):
    reason_code = "ELIGIBILITY_ASSURANCE_INSUFFICIENT"


class EligibilitySourceStaleError(VotingTrustError):
    reason_code = "ELIGIBILITY_SOURCE_STALE"


class EligibilitySourceUnavailableError(VotingTrustError):
    reason_code = "ELIGIBILITY_SOURCE_UNAVAILABLE"


class EligibilityEvidenceIncompleteError(VotingTrustError):
    reason_code = "ELIGIBILITY_EVIDENCE_INCOMPLETE"


class EligibilityDecisionExpiredError(VotingTrustError):
    reason_code = "ELIGIBILITY_DECISION_EXPIRED"


class EligibilityDecisionSupersededError(VotingTrustError):
    reason_code = "ELIGIBILITY_DECISION_SUPERSEDED"


class EligibilitySelfReviewRefusedError(VotingTrustError):
    reason_code = "ELIGIBILITY_SELF_REVIEW_REFUSED"


class UnknownEligibilityCaseError(VotingTrustError):
    reason_code = "ELIGIBILITY_CASE_NOT_FOUND"


class UndeclaredAttributeError(VotingTrustError):
    """An attribute the frozen rule-set version does not declare.

    Refused rather than dropped: a dropped attribute still travelled
    through a transport, a deserializer and, on a bad day, a request log.
    """

    reason_code = "ELIGIBILITY_ATTRIBUTE_NOT_DECLARED"


class ProhibitedAttributeError(VotingTrustError):
    """An attribute on the prohibited identity set reached the adapter."""

    reason_code = "ELIGIBILITY_ATTRIBUTE_PROHIBITED"


class AssertionRevokedError(VotingTrustError):
    reason_code = "ASSERTION_REVOKED"


class UnknownAssertionError(VotingTrustError):
    reason_code = "ASSERTION_NOT_FOUND"


class AssertionReleasePendingError(VotingTrustError):
    reason_code = "ASSERTION_RELEASE_PENDING"


class AssertionPickupAlreadyUsedError(VotingTrustError):
    reason_code = "ASSERTION_PICKUP_ALREADY_USED"


class AssertionPickupExpiredError(VotingTrustError):
    reason_code = "ASSERTION_PICKUP_EXPIRED"


class CredentialAlreadyIssuedError(VotingTrustError):
    """One assertion per participation unit per voting context.

    Raised on the identity side, which is the only side that knows the
    participant. The voting side never learns who (ADR-089).
    """

    reason_code = "CREDENTIAL_ALREADY_ISSUED"


class HandoffInvalidError(VotingTrustError):
    reason_code = "HANDOFF_INVALID"


class HandoffExpiredError(VotingTrustError):
    reason_code = "HANDOFF_EXPIRED"


class HandoffAlreadyUsedError(VotingTrustError):
    reason_code = "HANDOFF_ALREADY_USED"


class HandoffAudienceMismatchError(VotingTrustError):
    reason_code = "HANDOFF_AUDIENCE_MISMATCH"


class HandoffOriginMismatchError(VotingTrustError):
    reason_code = "HANDOFF_ORIGIN_MISMATCH"


class VotingContextNotActiveError(VotingTrustError):
    reason_code = "VOTING_CONTEXT_NOT_ACTIVE"


class VotingContextScopeMismatchError(VotingTrustError):
    reason_code = "VOTING_CONTEXT_SCOPE_MISMATCH"


class TimingProfileOutOfBoundsError(VotingTrustError):
    """A governed timing value outside its permitted range.

    Refused, never clamped silently: a silently clamped privacy control is
    a disabled privacy control (PACK-15 specification section 19.2).
    """

    reason_code = "TIMING_PROFILE_OUT_OF_BOUNDS"


class IssuanceWindowGuaranteeError(VotingTrustError):
    reason_code = "ISSUANCE_WINDOW_GUARANTEE_UNSATISFIED"


class ManualReviewRequiredError(VotingTrustError):
    reason_code = "MANUAL_REVIEW_REQUIRED"


class DualControlRequiredError(VotingTrustError):
    reason_code = "DUAL_CONTROL_REQUIRED"


class SeparationOfDutiesRefusedError(VotingTrustError):
    reason_code = "SEPARATION_OF_DUTIES_REFUSED"


class DisputeOpenError(VotingTrustError):
    reason_code = "DISPUTE_OPEN"


class SystemDependencyUnavailableError(VotingTrustError):
    reason_code = "SYSTEM_DEPENDENCY_UNAVAILABLE"


class IntermediateTallyProhibitedError(VotingTrustError):
    """A request that would have disclosed outcome-bearing data.

    Refused **and recorded**: the attempt is worth knowing about
    (ADR-094).
    """

    reason_code = "INTERMEDIATE_TALLY_PROHIBITED"


class CorrelationRiskDetectedError(VotingTrustError):
    reason_code = "CORRELATION_RISK_DETECTED"


class VotingBoundaryIntegrityError(VotingTrustError):
    reason_code = "VOTING_BOUNDARY_INTEGRITY_VIOLATION"
