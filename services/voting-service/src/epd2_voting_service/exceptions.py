"""Voting Service exceptions, tied to stable reason codes.

Per-entity `Unknown*StatusError`/`Forbidden*TransitionError`/`Unknown*Error`
triples mirror `epd2_credential_service.exceptions`'s style exactly, one
triple per owned entity's own state machine (`Ballot`, `BallotOption`,
`VoteEnvelope`, `VoteReceipt`) rather than one shared generic triple,
since each entity has its own independent status enum and transition
table.
"""

from __future__ import annotations

# --- Ballot ---------------------------------------------------------------


class UnknownBallotStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenBallotTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownBallotError(ValueError):
    """Raised for a plain lookup miss (no `Ballot` exists for the given
    `ballot_id`) - distinct from `UnknownBallotStatusError`, which
    describes an out-of-enum status value on a ballot that does exist
    (see ADR-004's precedent, reused here)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class BallotCreationConflictError(ValueError):
    """A repeated `create_ballot` request with the same `ballot_id` but
    different content (CT-00-04 analogue for creation, mirroring
    `CredentialIssuanceConflictError`)."""

    reason_code = "BALLOT_DUPLICATE_CREATION_CONFLICT"


class BallotConfigurationLockedError(ValueError):
    """CT-00-10: once `Ballot.status` reaches `configuration_review` or
    later, the fields covered by `configuration_hash` and this ballot's
    `BallotOption` rows are frozen - any attempted mutation raises this
    (canon section-24 reason code, reused verbatim)."""

    reason_code = "BALLOT_CONFIGURATION_LOCKED"


class BallotNotOpenError(ValueError):
    """`cast_vote` requires `Ballot.status == open` (canon section-24
    reason code, reused verbatim)."""

    reason_code = "BALLOT_NOT_OPEN"


class BallotAlreadyClosedError(ValueError):
    """`cast_vote` requires `now < Ballot.closes_at` (canon section-24
    reason code, reused verbatim)."""

    reason_code = "BALLOT_ALREADY_CLOSED"


class UnknownEligibilitySnapshotReferenceError(ValueError):
    """Raised by `submit_ballot_for_configuration_review` when the
    `eligibility_snapshot_id` it is asked to freeze against does not
    resolve to a real `EligibilitySnapshot` via
    `epd2_eligibility_service.application.get_eligibility_snapshot`
    (ADR-008). Reuses `VALIDATION_RECORD_NOT_FOUND` - the referenced
    record does not exist, the same shape as a local lookup miss, just
    against an upstream PACK-02 service instead of this service's own
    store."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- BallotOption -----------------------------------------------------------


class UnknownBallotOptionStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenBallotOptionTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownBallotOptionError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- VoteEnvelope -----------------------------------------------------------


class UnknownVoteEnvelopeStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenVoteEnvelopeTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownVoteEnvelopeError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class VoteEnvelopeCreationConflictError(ValueError):
    """A repeated `cast_vote` request with the same `vote_envelope_id` but
    different content - distinct from a legitimate CT-00-04 replay (same
    id, same content, which is idempotent - see `storage.py`)."""

    reason_code = "VOTE_ENVELOPE_DUPLICATE_SUBMISSION_CONFLICT"


class DuplicateVoteError(ValueError):
    """A genuinely duplicate/rejected vote resubmission attempt for a
    credential that already has a `validated` envelope on this ballot,
    arriving after `Ballot.closes_at` (ADR-009 items 1-2: a pre-close
    resubmission is a legitimate vote change handled via supersession in
    `cast_vote`, not this error; canon section-24 reason code, reused
    verbatim)."""

    reason_code = "DUPLICATE_VOTE"


class VoteEnvelopeNotReceiptEligibleError(ValueError):
    """`issue_vote_receipt` requires the referenced `VoteEnvelope` to be
    `validated` or `included` - a `received`, `rejected`, `superseded`, or
    `quarantined` envelope has nothing verifiable to issue a receipt
    for."""

    reason_code = "VOTE_ENVELOPE_NOT_RECEIPT_ELIGIBLE"


# --- VoteReceipt -------------------------------------------------------------


class UnknownVoteReceiptStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenVoteReceiptTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownVoteReceiptError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class VoteReceiptCreationConflictError(ValueError):
    reason_code = "RECEIPT_DUPLICATE_ISSUANCE_CONFLICT"
