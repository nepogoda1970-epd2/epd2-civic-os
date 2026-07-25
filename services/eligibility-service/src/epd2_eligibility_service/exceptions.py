"""Eligibility Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownEligibilityDecisionValueError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class RuleVersionFrozenError(ValueError):
    """Raised when a caller attempts to re-submit an existing
    `(eligibility_rule_id, rule_version)` with different content - the
    canon section 9.1 "rule freeze" requirement applied to `EligibilityRule`.
    """

    reason_code = "ELIGIBILITY_RULE_VERSION_FROZEN"


class UnknownEligibilityRuleError(ValueError):
    """Raised for a plain lookup miss (no `EligibilityRule` exists for the
    given `(eligibility_rule_id, rule_version)`) - distinct from
    `ELIGIBILITY_NOT_MET`, which describes a real decision outcome against
    a rule that exists (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- PACK-07 additions (canon 19d.4-19d.14, canon-0.6.0) --------------------
# Generic-code reuses mirror this repository's established precedent
# (e.g. `UnknownModerationDecisionTypeError`): a non-status enum or a
# plain lookup miss reuses the existing generic code, never inventing a
# near-duplicate. Only genuinely new failure shapes get a new code.


class UnknownCriticalPolicyStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenCriticalPolicyTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownParticipantEligibilityPolicyError(ValueError):
    """Plain lookup miss - no `ParticipantEligibilityPolicy` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownProcessEligibilityPolicyError(ValueError):
    """Plain lookup miss - no `ProcessEligibilityPolicy` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownStepUpAuthenticationRequirementError(ValueError):
    """Plain lookup miss - no `StepUpAuthenticationRequirement` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownDigitalDecisionError(ValueError):
    """Plain lookup miss - no `DigitalDecision` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAssemblyDecisionError(ValueError):
    """Plain lookup miss - no `AssemblyDecision` exists."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAssuranceLevelError(ValueError):
    """Local, dependency-free re-validation of an assurance-level string
    (`none`/`low`/`substantial`/`high`) - this module never imports
    `epd2_identity_service.domain.IdentityAssuranceLevel`/
    `AuthenticationAssuranceLevel` (the same zero-dependency boundary
    this module's own docstring already establishes for every other
    identity-service type)."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class CriticalPolicyActivationNotAuthorizedError(ValueError):
    """Canon 19d.7's four-gate critical-policy activation rule: raised
    fail-closed when any one of the four independent gates (approved
    `GovernanceDecision`, `multi_person_approval_met`,
    `signed_policy_digest_reference`, `transparency_log_commitment_reference`)
    is not satisfied."""

    reason_code = "CRITICAL_POLICY_ACTIVATION_NOT_AUTHORIZED"


class CriticalPolicyVersionFrozenError(ValueError):
    """Canon 19d.7's version-freeze rule (relates to CT-00-10): an active
    critical-policy version already in use by an active process should
    not be superseded until that process reaches a terminal state.

    Declared for forward compatibility but deliberately UNRAISED in this
    implementation round: enforcing it requires knowing whether an active
    process is currently relying on a given policy version, which needs a
    persisted Process/Election aggregate this pack does not introduce (no
    such entity exists anywhere in this repository through PACK-07 - see
    `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`'s CT-00-10 mapping
    and task 19's "full Regional Organization model" deferral). Raising
    this from a caller-supplied, unverified "is a process using this"
    flag would be worse than not enforcing it at all (a false sense of
    safety); a future pack that introduces process-lifecycle tracking is
    the correct place to wire this up for real, against real process
    state - not this one, honestly reported per task 18's no-false-
    applicability-claims requirement."""

    reason_code = "CRITICAL_POLICY_VERSION_FROZEN"


class StepUpAuthenticationNotSatisfiedError(ValueError):
    """Canon 19d.8's fail-closed `StepUpAuthenticationRequirement`
    evaluation: raised when authentication assurance, identity
    assurance, session freshness, or attribute freshness do not all
    hold simultaneously - or when the `AuthenticationContext` is
    missing, expired, or unresolvable. Never a default allow."""

    reason_code = "STEP_UP_AUTHENTICATION_NOT_SATISFIED"


class UnknownDigitalDecisionStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenDigitalDecisionTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownAssemblyDecisionStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAssemblyDecisionTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class AssemblyDecisionDivergenceExplanationRequiredError(ValueError):
    """Canon 19d.12: 'расхождение между final_legal_decision и
    digital_result без заполненного divergence_explanation отклоняется
    валидацией'."""

    reason_code = "ASSEMBLY_DECISION_DIVERGENCE_EXPLANATION_REQUIRED"


class AtomicCapabilityCheckDeniedError(ValueError):
    """Canon 19d.14's atomic capability check, in its fail-closed
    denial shape - raised by callers that choose to raise rather than
    branch on `AtomicCapabilityResult.authorized`."""

    reason_code = "ATOMIC_CAPABILITY_CHECK_DENIED"
