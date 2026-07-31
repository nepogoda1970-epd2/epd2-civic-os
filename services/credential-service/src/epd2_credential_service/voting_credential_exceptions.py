"""PACK-15 voting-side refusals raised by `credential-service`.

One class per registered reason code (ADR-004's convention). Every literal
is registered in `contracts/reason-codes/pack-15.yml`.

These are the refusals of the **voting side**, which knows a context, a
class, a nonce and a credential - and no participant. No refusal here can
name a person, because no code path here has one.
"""

from __future__ import annotations


class VotingCredentialError(ValueError):
    """Base class. Never raised directly: a refusal without a registered
    code is not a permissible refusal in this domain."""


class AssertionInvalidError(VotingCredentialError):
    reason_code = "ASSERTION_INVALID"


class AssertionExpiredError(VotingCredentialError):
    reason_code = "ASSERTION_EXPIRED"


class AssertionAudienceMismatchError(VotingCredentialError):
    reason_code = "ASSERTION_AUDIENCE_MISMATCH"


class AssertionPurposeMismatchError(VotingCredentialError):
    reason_code = "ASSERTION_PURPOSE_MISMATCH"


class AssertionContextMismatchError(VotingCredentialError):
    reason_code = "ASSERTION_CONTEXT_MISMATCH"


class AssertionAlreadyUsedError(VotingCredentialError):
    """The nonce is in the spent set.

    The spent set answers "was this nonce used?" and never "what did it
    produce?" (ADR-093).
    """

    reason_code = "ASSERTION_ALREADY_USED"


class CredentialDuplicateRequestError(VotingCredentialError):
    reason_code = "CREDENTIAL_DUPLICATE_REQUEST"


class CredentialRevokedError(VotingCredentialError):
    reason_code = "CREDENTIAL_REVOKED"


class CredentialExpiredError(VotingCredentialError):
    reason_code = "CREDENTIAL_EXPIRED"


class CredentialAlreadyRedeemedError(VotingCredentialError):
    reason_code = "CREDENTIAL_ALREADY_REDEEMED"


class CredentialReplayDetectedError(VotingCredentialError):
    reason_code = "CREDENTIAL_REPLAY_DETECTED"


class CredentialContextMismatchError(VotingCredentialError):
    reason_code = "CREDENTIAL_CONTEXT_MISMATCH"


class CredentialAudienceMismatchError(VotingCredentialError):
    reason_code = "CREDENTIAL_AUDIENCE_MISMATCH"


class CredentialOriginRefusedError(VotingCredentialError):
    reason_code = "CREDENTIAL_ORIGIN_REFUSED"


class CredentialIssuanceWindowClosedError(VotingCredentialError):
    reason_code = "CREDENTIAL_ISSUANCE_WINDOW_CLOSED"


class CredentialRedemptionWindowClosedError(VotingCredentialError):
    reason_code = "CREDENTIAL_REDEMPTION_WINDOW_CLOSED"


class CredentialRevocationCutoffPassedError(VotingCredentialError):
    reason_code = "CREDENTIAL_REVOCATION_CUTOFF_PASSED"


class UnknownVotingCredentialError(VotingCredentialError):
    """A lookup miss, answered with the same shape as a revoked credential
    so the lookup cannot be used as an oracle."""

    reason_code = "CREDENTIAL_NOT_FOUND"


class DeliveryChannelRefusedError(VotingCredentialError):
    reason_code = "DELIVERY_CHANNEL_REFUSED"


class ForbiddenCredentialFieldError(VotingCredentialError):
    reason_code = "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


class VotingCredentialDependencyUnavailableError(VotingCredentialError):
    """The replay store or the audit stream was unreachable.

    Neither is ever bypassed: an issuance without the spent-set check is a
    double credential, and an issuance without audit evidence is an
    unaccountable issuance.
    """

    reason_code = "SYSTEM_DEPENDENCY_UNAVAILABLE"

class AssertionAssuranceInsufficientError(VotingCredentialError):
    """The presented assertion says the assurance requirement was not met.

    The identity side is the only side that can evaluate assurance, and
    it records the outcome in the crossing artifact. This side has to
    *read* it: an assurance flag that is carried across and never checked
    is a control that exists only in the field list.
    """

    reason_code = "ELIGIBILITY_ASSURANCE_INSUFFICIENT"
