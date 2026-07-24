"""AI Processing Service reason-code exceptions — one class per
registered `contracts/reason-codes/pack-06.yml` entry this service's own
`src/` actually raises (ADR-024). Generic/reused codes
(`PERMISSION_DENIED`, `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`) are
redeclared locally here, following the same "each pack's services
independently redeclare shared generic codes" convention every prior
pack's own `exceptions.py` already uses. `ForbiddenProcessingStatusTransitionError`/
`ForbiddenHumanReviewStatusTransitionError` and
`AITargetReferenceMalformedError` live in `domain.py` instead (the same
module that owns their transition tables/allow-lists), not redefined
here — import them from `epd2_ai_processing_service.domain`, not from
this module.
"""

from __future__ import annotations


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


class UnknownAIProcessingRecordError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownProcessingStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownHumanReviewStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class AIProcessingRecordConflictError(ValueError):
    """This service's own additive duplicate-conflict code (not from
    ADR-024's list — the same "this service's own" pattern every prior
    pack's own registry already includes, e.g. governance-service's
    `ROLE_ASSIGNMENT_DUPLICATE_CONFLICT`)."""

    reason_code = "AI_PROCESSING_RECORD_DUPLICATE_CONFLICT"


class AIModelUnavailableError(RuntimeError):
    reason_code = "AI_MODEL_UNAVAILABLE"


class AIProcessingTimeoutError(RuntimeError):
    reason_code = "AI_PROCESSING_TIMEOUT"


class AIOutputMalformedError(ValueError):
    reason_code = "AI_OUTPUT_MALFORMED"


class AIModelVersionUnsupportedError(ValueError):
    reason_code = "AI_MODEL_VERSION_UNSUPPORTED"


class AIConfidenceBelowThresholdError(ValueError):
    reason_code = "AI_CONFIDENCE_BELOW_THRESHOLD"


class AIPolicyConflictError(ValueError):
    reason_code = "AI_POLICY_CONFLICT"


class AIRedactionFailureError(ValueError):
    reason_code = "AI_REDACTION_FAILURE"


class AIPromptInjectionSuspectedError(ValueError):
    reason_code = "AI_PROMPT_INJECTION_SUSPECTED"


class AIProhibitedInputDetectedError(ValueError):
    reason_code = "AI_PROHIBITED_INPUT_DETECTED"


class AIHumanReviewerMissingError(ValueError):
    reason_code = "AI_HUMAN_REVIEWER_MISSING"


class AIHumanReviewRequiredError(ValueError):
    reason_code = "AI_HUMAN_REVIEW_REQUIRED"


class AIOutputRejectedByHumanError(ValueError):
    reason_code = "AI_OUTPUT_REJECTED_BY_HUMAN"


class AIProcessingRecordSupersededError(ValueError):
    reason_code = "AI_PROCESSING_RECORD_SUPERSEDED"


class AIAutonomousActionProhibitedError(PermissionError):
    reason_code = "AI_AUTONOMOUS_ACTION_PROHIBITED"


class AIReviewerRoleInvalidError(PermissionError):
    reason_code = "AI_REVIEWER_ROLE_INVALID"


class AIReviewerScopeMismatchError(PermissionError):
    reason_code = "AI_REVIEWER_SCOPE_MISMATCH"


class AIReviewSelfApprovalProhibitedError(PermissionError):
    reason_code = "AI_REVIEW_SELF_APPROVAL_PROHIBITED"


class AIRedactionManifestInvalidError(ValueError):
    reason_code = "AI_REDACTION_MANIFEST_INVALID"


class AIInputProvenanceUnverifiedError(ValueError):
    reason_code = "AI_INPUT_PROVENANCE_UNVERIFIED"


class AIPublicDisclosureRequiredError(ValueError):
    reason_code = "AI_PUBLIC_DISCLOSURE_REQUIRED"


class AIConsequentialOutputNotReviewedError(ValueError):
    reason_code = "AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED"
