"""Moderation Service exceptions, tied to stable reason codes (ADR-004 /
ADR-006 pattern: one exception class per distinct failure shape, never
free text — canon section 24: "reason code не заменяется свободным
текстом").
"""

from __future__ import annotations


class UnknownModerationCaseStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenModerationCaseTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownModerationDecisionTypeError(ValueError):
    """`decision_type` (canon section 14.2) is a type enum, not a status —
    it has no transition table, but still needs CT-00-02 unknown-value
    rejection. Reuses the same generic `VALIDATION_UNKNOWN_STATUS` code
    `UnknownModerationCaseStatusError`/`UnknownAppealStatusError` use,
    mirroring eligibility-service's `UnknownEligibilityDecisionValueError`
    precedent for a non-status enum that still needs fail-closed parsing.
    """

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAppealStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAppealTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownModerationCaseError(ValueError):
    """Plain lookup miss — no `ModerationCase` exists for the given
    `moderation_case_id` — distinct from `UnknownModerationCaseStatusError`,
    which describes an out-of-enum status value on a case that does exist
    (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownModerationDecisionError(ValueError):
    """Plain lookup miss — no `ModerationDecision` exists for the given
    `moderation_decision_id`."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAppealError(ValueError):
    """Plain lookup miss — no `Appeal` exists for the given `appeal_id`."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class ModerationCaseConflictError(ValueError):
    """A repeated `open_moderation_case` request with the same
    `moderation_case_id` but different content (CT-00-04 analogue for
    creation, mirroring `CredentialIssuanceConflictError`)."""

    reason_code = "MODERATION_CASE_DUPLICATE_CONFLICT"


class ModerationDecisionConflictError(ValueError):
    """A repeated `issue_decision` request with the same
    `moderation_decision_id` but different content."""

    reason_code = "MODERATION_DECISION_DUPLICATE_CONFLICT"


class AppealConflictError(ValueError):
    """A repeated `submit_appeal` request with the same `appeal_id` but
    different content."""

    reason_code = "APPEAL_DUPLICATE_SUBMISSION_CONFLICT"


class AppealDeadlineExpiredError(ValueError):
    """Reserved, canon section-24 reason code, reused verbatim - NOT
    currently raised anywhere in `application.py`. Canon section 14.2/
    14.3's own field lists give neither `ModerationDecision` nor `Appeal`
    an explicit deadline field (no `appeal_deadline_at` or equivalent),
    so `submit_appeal` enforces no hardcoded deadline rather than
    inventing a canon field silently. This class exists so the reason
    code is a real, importable, documented symbol in this service ahead
    of a future pack/ADR that defines where the deadline actually lives -
    see README.md's "Known gaps" section."""

    reason_code = "APPEAL_DEADLINE_EXPIRED"
