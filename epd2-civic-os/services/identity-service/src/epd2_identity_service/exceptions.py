"""Identity Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownVerificationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenVerificationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownIdentityRecordError(ValueError):
    """Raised for a plain lookup miss (no `IdentityRecord` exists for the
    given `identity_record_id`) - distinct from `IDENTITY_NOT_VERIFIED`,
    which describes a record that exists but has not passed verification
    (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"
