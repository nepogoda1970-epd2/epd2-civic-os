"""Tally Service exceptions, tied to stable reason codes.

Reason codes are drawn from `docs/canonical/TZ-00-domain-event-canon.md`
section 24's stable list wherever an exact match exists
(`VALIDATION_UNKNOWN_STATUS`, `VALIDATION_FORBIDDEN_TRANSITION`,
`VALIDATION_RECORD_NOT_FOUND`, `PERMISSION_DENIED`,
`INTEGRITY_CHECK_FAILED`). Two additive, service-local codes are used for
storage-level idempotency conflicts (`TALLY_RECORD_CONFLICT`,
`RESULT_PUBLICATION_RECORD_CONFLICT`), following the exact precedent
already established by `credential-service`'s
`CredentialIssuanceConflictError` (`CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT`)
and `eligibility-service`'s `RuleVersionFrozenError`
(`ELIGIBILITY_RULE_VERSION_FROZEN`) — neither of which is in canon section
24 either, since canon does not enumerate every service's own
storage-conflict bookkeeping code.
"""

from __future__ import annotations


class UnknownTallyVerificationStatusError(ValueError):
    """Raised when a `Tally.verification_status` string does not match any
    `TallyVerificationStatus` member (canon section 15.5's exact status
    list)."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenTallyTransitionError(ValueError):
    """Raised when a `Tally` transition is attempted outside
    `ALLOWED_TRANSITIONS`, or when a command's own precondition on
    `Tally.verification_status` is not met (e.g. `publish_result`
    requires a `verified` `Tally`)."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownQuorumResultError(ValueError):
    """Raised when a `quorum_result` string does not match any
    `QuorumResult` member. Reuses `VALIDATION_UNKNOWN_STATUS` per
    `eligibility-service`'s `UnknownEligibilityDecisionValueError`
    precedent (an unknown enum value on a non-"status"-named field is
    still the same class of failure)."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownThresholdResultError(ValueError):
    """Raised when a `threshold_result` string does not match any
    `ThresholdResult` member. See `UnknownQuorumResultError`'s docstring
    for why this reuses `VALIDATION_UNKNOWN_STATUS`."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownTallyError(ValueError):
    """Raised for a plain lookup miss (no `Tally` exists for the given
    `tally_id`) - distinct from `UnknownTallyVerificationStatusError`,
    which describes an out-of-enum status value on a `Tally` that does
    exist (see ADR-004's precedent for this exact distinction in
    credential-service)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownResultPublicationError(ValueError):
    """Raised for a plain lookup miss (no `ResultPublication` exists for
    the given `result_publication_id`)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class TallyRecordConflictError(ValueError):
    """Raised when a repeated `start_tally`/`TallyStore.create` request
    with the same `tally_id` carries different content than what is
    already stored - the CT-00-04 idempotency-vs-conflict distinction
    applied to `Tally` creation."""

    reason_code = "TALLY_RECORD_CONFLICT"


class ResultPublicationConflictError(ValueError):
    """Raised when a repeated `publish_result`/`ResultPublicationStore.create`
    request with the same `result_publication_id` carries different
    content than what is already stored."""

    reason_code = "RESULT_PUBLICATION_RECORD_CONFLICT"
