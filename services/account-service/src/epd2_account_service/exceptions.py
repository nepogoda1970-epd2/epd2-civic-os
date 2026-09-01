"""Account Service exceptions, each tied to a stable reason code from
`contracts/reason-codes/pack-02.yml`.
"""

from __future__ import annotations


class UnknownAccountStatusError(ValueError):
    """Raised when a status value is not a recognized `AccountStatus`
    (CT-00-02: unknown status is never accepted). Fail-closed per INV-10.
    """

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAccountTransitionError(ValueError):
    """Raised when a requested status transition is not in
    `domain.ALLOWED_TRANSITIONS` (CT-00-03)."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownAccountError(ValueError):
    """Raised for a plain lookup miss (no `Account` exists for the given
    `account_id`) - the same generic code identity-service,
    eligibility-service, and credential-service use for their own
    lookup-miss exceptions (ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"
