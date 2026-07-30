"""The WS-03 outbound boundary - and nothing on the other side of it.

**No Voting Client is implemented here.** Eligibility assertion, voting
credential issuance, ballot casting, verification and tally are PACK-15
and PACK-16, taken with PACK-15's own threat model. What PACK-14 owns is
the boundary the artifact crosses (ADR-088).

The `VotingHandoffArtifact` is deliberately the emptiest object in this
package. It is opaque, single-use, short-lived, audience-bound,
purpose-bound and voting-context-bound, and it carries **no identifier of
any kind**: no account ID, no person record, no membership ID, no member
number, no communication persona, no contact value and no general session
token. There is no field on any dataclass here that could hold one, which
is the structural version of the promise rather than a policy about it.

The property that takes the most care is the last one:

> Neither the artifact nor the issuance and redemption records, jointly
> or separately, permit resolving a redemption back to the account that
> obtained it.

So `VotingHandoffIssuance` holds no account reference at all - not even a
scoped one - and the redemption record holds only the artifact digest.
`refuse_reverse_resolution()` exists so that a caller who asks the
question gets a refusal with a registered reason code, making the attempt
auditable rather than merely impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from epd2_identity_service.configuration import IdentityConfiguration
from epd2_identity_service.exceptions import (
    VotingHandoffAlreadyUsedError,
    VotingHandoffAudienceMismatchError,
    VotingHandoffExpiredError,
    VotingHandoffInvalidError,
    VotingHandoffPurposeMismatchError,
    VotingHandoffReverseResolutionRefusedError,
)
from epd2_identity_service.identifiers import require_timezone
from epd2_identity_service.secret_storage import HashedSecret, SecureRandom, hash_token
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

#: The only purpose a handoff artifact may carry. A second value would be
#: a general-purpose artifact, which is what "purpose-bound" exists to
#: prevent.
VOTING_ENTRY_PURPOSE = "voting_entry"

#: The only audience. WS-03's origin, and no other.
VOTING_AUDIENCE_ORIGIN = workspace_origin(WorkspaceId.VOTING_CLIENT)


@dataclass(frozen=True, slots=True)
class VotingHandoffRequest:
    """A request for entry to **one** voting context.

    The requesting session is named here because the issuing side must
    check assurance and step-up before minting anything - and it is
    deliberately *not* carried onto the artifact or the issuance record.
    """

    request_id: UUID
    voting_context_id: UUID
    audience_origin: str
    requested_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, "requested_at")
        if self.audience_origin != VOTING_AUDIENCE_ORIGIN:
            raise VotingHandoffAudienceMismatchError(
                f"the only permitted handoff audience is {VOTING_AUDIENCE_ORIGIN}"
            )


@dataclass(frozen=True, slots=True)
class VotingHandoffArtifact:
    """The artifact, as the voting side receives it.

    Six fields, and not one of them identifies a person. `value` is a
    high-entropy opaque string with no internal structure to parse or
    correlate; `artifact_id` is a random UUID with no derivation from
    anything about the holder.
    """

    artifact_id: UUID
    value: str
    audience_origin: str
    purpose: str
    voting_context_id: UUID
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.expires_at, "expires_at")
        if self.purpose != VOTING_ENTRY_PURPOSE:
            raise VotingHandoffPurposeMismatchError(
                f"a handoff artifact carries the purpose {VOTING_ENTRY_PURPOSE!r} and no other"
            )
        if self.audience_origin != VOTING_AUDIENCE_ORIGIN:
            raise VotingHandoffAudienceMismatchError(
                f"the only permitted handoff audience is {VOTING_AUDIENCE_ORIGIN}"
            )
        if not self.value:
            raise VotingHandoffInvalidError("a handoff artifact carries an opaque value")


@dataclass(frozen=True, slots=True)
class VotingHandoffIssuance:
    """The issuing side's record.

    **There is no account field, no session field and no scoped actor
    reference.** The issuing decision - assurance, step-up, eligibility
    to be here at all - is made *before* this record exists and is
    audited on the account's own side; what survives here is that an
    artifact for a voting context was issued and when it expires. That is
    the whole content of the non-reversibility property.
    """

    artifact_id: UUID
    value_digest: HashedSecret
    voting_context_id: UUID
    purpose: str
    audience_origin: str
    issued_at: datetime
    expires_at: datetime
    redeemed_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.redeemed_at is not None:
            require_timezone(self.redeemed_at, "redeemed_at")

    def is_spent(self) -> bool:
        return self.redeemed_at is not None


@dataclass(frozen=True, slots=True)
class VotingHandoffRedemptionReference:
    """What the voting side gets back, and what is recorded.

    It names the voting context and the moment. It does not name, and
    cannot be joined to, the account that obtained the artifact.
    """

    redemption_id: UUID
    artifact_id: UUID
    voting_context_id: UUID
    redeemed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.redeemed_at, "redeemed_at")


def issue_voting_handoff(
    request: VotingHandoffRequest,
    *,
    artifact_id: UUID,
    issued_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> tuple[VotingHandoffArtifact, VotingHandoffIssuance]:
    """Mint one artifact for one voting context.

    The caller has already established assurance `high`, a valid step-up
    and the account's usability; none of that is passed in, because
    passing it in would mean storing it, and storing it is the reverse
    bridge ADR-088 forbids.
    """
    moment = require_timezone(issued_at, "issued_at")
    expires_at = moment + configuration.voting_handoff_lifetime
    value = random.token()
    artifact = VotingHandoffArtifact(
        artifact_id=artifact_id,
        value=value,
        audience_origin=request.audience_origin,
        purpose=VOTING_ENTRY_PURPOSE,
        voting_context_id=request.voting_context_id,
        expires_at=expires_at,
    )
    issuance = VotingHandoffIssuance(
        artifact_id=artifact_id,
        value_digest=hash_token(value),
        voting_context_id=request.voting_context_id,
        purpose=VOTING_ENTRY_PURPOSE,
        audience_origin=request.audience_origin,
        issued_at=moment,
        expires_at=expires_at,
    )
    return artifact, issuance


def redeem_voting_handoff(
    issuance: VotingHandoffIssuance | None,
    *,
    presented_value: str,
    presenting_origin: str,
    voting_context_id: UUID,
    redemption_id: UUID,
    now: datetime,
) -> tuple[VotingHandoffIssuance, VotingHandoffRedemptionReference]:
    """Redeem once, at one origin, for one voting context.

    Note what the failure responses do **not** vary by: an unknown
    artifact and a value that does not match produce the same
    `VOTING_HANDOFF_INVALID`, so a caller outside the issuing boundary
    cannot use the refusal to learn whether a given artifact ever
    existed.
    """
    moment = require_timezone(now, "now")
    if issuance is None:
        raise VotingHandoffInvalidError("the voting handoff artifact did not verify")
    if issuance.is_spent():
        raise VotingHandoffAlreadyUsedError("this single-use artifact has already been redeemed")
    if moment >= issuance.expires_at:
        raise VotingHandoffExpiredError("the voting handoff artifact has expired")
    if presenting_origin != issuance.audience_origin:
        raise VotingHandoffAudienceMismatchError(
            "the artifact was presented to an origin it is not bound to"
        )
    if voting_context_id != issuance.voting_context_id:
        raise VotingHandoffPurposeMismatchError(
            "the artifact is bound to a different voting context"
        )
    if not issuance.value_digest.matches(presented_value):
        raise VotingHandoffInvalidError("the voting handoff artifact did not verify")
    return (
        replace(issuance, redeemed_at=moment),
        VotingHandoffRedemptionReference(
            redemption_id=redemption_id,
            artifact_id=issuance.artifact_id,
            voting_context_id=issuance.voting_context_id,
            redeemed_at=moment,
        ),
    )


def refuse_reverse_resolution(redemption: VotingHandoffRedemptionReference) -> None:
    """ADR-088, as a call site. Always raises.

    Any administrative surface, support tool or query path that is asked
    "which account obtained this artifact?" calls this. It exists so the
    attempt is *auditable*: an operation that is merely impossible leaves
    no trace when somebody tries, and knowing that somebody tried is the
    point.
    """
    raise VotingHandoffReverseResolutionRefusedError(
        f"redemption {redemption.redemption_id} is never resolved back to an account; "
        "no record on either side of this boundary permits it"
    )


def handoff_payload(issuance: VotingHandoffIssuance) -> dict[str, object]:
    """The event payload for a handoff issuance.

    Purpose scope and expiry, and nothing else - exactly what the event
    catalog's §9 permits. There is no branch of this function that adds a
    field, and the payload it returns is checked again by
    `reject_prohibited_payload_keys` before an envelope exists.
    """
    return {
        "purpose": issuance.purpose,
        "voting_context_id": str(issuance.voting_context_id),
        "expires_at": issuance.expires_at.isoformat(),
    }
