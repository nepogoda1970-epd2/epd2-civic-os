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


# --- PACK-07 additions (canon 19d.2 / 19d.8, canon-0.6.0) -------------------
# Reuses the same generic `VALIDATION_UNKNOWN_STATUS` code
# `UnknownVerificationStatusError` already uses, mirroring
# `UnknownModerationDecisionTypeError`'s precedent for a non-status enum
# that still needs CT-00-02 fail-closed parsing — no new reason code is
# registered for either of these.


class UnknownIdentityAssuranceLevelError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAuthenticationAssuranceLevelError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAuthenticationContextError(ValueError):
    """Plain lookup miss - no `AuthenticationContext` exists for the
    given `authentication_context_id`."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"
