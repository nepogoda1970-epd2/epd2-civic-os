"""Credential Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownCredentialStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenCredentialTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownCredentialError(ValueError):
    """Raised for a plain lookup miss (no `ParticipationCredential` exists
    for the given `credential_id`) - distinct from
    `UnknownCredentialStatusError` (`VALIDATION_UNKNOWN_STATUS`), which
    describes an out-of-enum status value on a credential that does exist
    (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class CredentialIssuanceConflictError(ValueError):
    """A repeated issuance request with the same `credential_id` but
    different content (CT-00-04 analogue for issuance)."""

    reason_code = "CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT"
