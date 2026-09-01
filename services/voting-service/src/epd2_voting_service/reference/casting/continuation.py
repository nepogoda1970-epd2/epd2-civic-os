"""Anonymous continuation capability state machine (PACK-16C `CN-33`..`CN-38`).

Three booleans, no counter, and nothing that could be joined to a person.
The capability record deliberately has no field for an identity, a
credential, a ballot reference or an artefact reference: the join is
absent from the type, not merely forbidden by policy.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

FORBIDDEN_CAPABILITY_FIELDS: frozenset[str] = frozenset(
    {
        "identity",
        "identity_record_id",
        "member_id",
        "membership_id",
        "credential_id",
        "account_id",
        "email",
        "name",
        "ballot_id",
        "artifact_reference",
        "public_challenge_artifact_id",
    }
)


class CastEntitlementExhaustedError(ValueError):
    reason_code = "CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED"


class PublicChallengeEntitlementExhaustedError(ValueError):
    reason_code = "CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED"


class CapabilityUnknownError(LookupError):
    reason_code = "CONTINUATION_INVALID"


@dataclass(frozen=True, slots=True)
class ContinuationState:
    """`DM-20`: exactly three booleans plus an opaque anonymous reference."""

    capability_reference: str
    election_context_id: str
    cast_entitlement_available: bool = True
    public_challenge_entitlement_available: bool = True
    capability_consumed: bool = False

    def spend_public_challenge(self) -> ContinuationState:
        if not self.public_challenge_entitlement_available:
            raise PublicChallengeEntitlementExhaustedError(
                "the public evidentiary challenge entitlement is already spent"
            )
        if self.capability_consumed:
            # A consumed capability has no entitlement of any kind left.
            # This is a challenge path, so it reports the challenge
            # entitlement as exhausted; reporting the *cast* entitlement
            # here would tell a caller about a state it did not ask about.
            raise PublicChallengeEntitlementExhaustedError("the capability is already consumed")
        return replace(self, public_challenge_entitlement_available=False)

    def consume_for_cast(self) -> ContinuationState:
        if not self.cast_entitlement_available or self.capability_consumed:
            raise CastEntitlementExhaustedError("the cast entitlement is already spent")
        return replace(
            self,
            cast_entitlement_available=False,
            public_challenge_entitlement_available=False,
            capability_consumed=True,
        )
