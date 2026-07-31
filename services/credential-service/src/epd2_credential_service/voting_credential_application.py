"""The PACK-15 Voting Credential Issuer (VC-04) application layer.

Four acts: issue, revoke, redeem, and answer a privacy-safe status. Each
is transactional at the store boundary, each writes evidence to the
credential stream only, and none of them can name a participant.

**Exactly-once without a shared identifier.** The identity side enforces
one assertion per participation unit; this side enforces one credential
per assertion nonce. Neither needs the other's identifier, and between
them the effect is exactly-once (specification section 13.1).

**The pairing prohibition, operationally.** `issue()` marks the nonce
spent and mints a credential in the same transaction, and stores the two
facts in two stores that share no key. The idempotency cache maps the
retry key to the credential for a **bounded** window and is purged; that
window is the only place the two are ever associated, it is explicit, and
`MAX_IDEMPOTENCY_WINDOW_SECONDS` bounds it.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from epd2_core.event_envelope import EventEnvelope
from epd2_credential_service.voting_credential_events import (
    CREDENTIAL_ISSUED,
    CREDENTIAL_REDEEMED,
    CREDENTIAL_REPLAY_REJECTED,
    CREDENTIAL_REVOKED,
    DUPLICATE_ISSUANCE_REJECTED,
    build_credential_event,
    build_replay_event,
)
from epd2_credential_service.voting_credential_exceptions import (
    AssertionAssuranceInsufficientError,
    AssertionAlreadyUsedError,
    AssertionAudienceMismatchError,
    AssertionContextMismatchError,
    AssertionExpiredError,
    AssertionInvalidError,
    AssertionPurposeMismatchError,
    CredentialIssuanceWindowClosedError,
    CredentialReplayDetectedError,
    CredentialRevocationCutoffPassedError,
    UnknownVotingCredentialError,
    VotingCredentialDependencyUnavailableError,
)
from epd2_credential_service.voting_credential_storage import (
    CredentialIdempotencyStore,
    CredentialRedemptionStore,
    CredentialReplayStore,
    SpentNonceSet,
    VotingCredentialStore,
)
from epd2_credential_service.voting_credentials import (
    CredentialIssuanceIdempotencyRecord,
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialRevocation,
    CredentialStatus,
    SpentNonce,
    VotingCredential,
    assert_absorbing_redeemed,
    assert_delivery_channel_permitted,
    assert_origin_is_voting_client,
)

#: The retry window. Long enough for a client retry, far too short to be a
#: durable map.
MAX_IDEMPOTENCY_WINDOW_SECONDS = 900
DEFAULT_IDEMPOTENCY_WINDOW_SECONDS = 300

#: The only permitted assertion purpose, mirrored on this side so the
#: voting side verifies rather than trusts.
EXPECTED_ASSERTION_PURPOSE = "voting_credential_issuance"
EXPECTED_ASSERTION_RESULT = "approved"


@dataclass(frozen=True, slots=True)
class PresentedAssertion:
    """The assertion as it arrives from inside the isolated origin.

    Exactly the twelve crossing fields plus its integrity metadata. There
    is no field here for a participant, and none may be added.
    """

    assertion_id: UUID
    voting_context_reference: str
    eligibility_result: str
    eligibility_class: str
    organizational_scope: str
    required_assurance_satisfied: bool
    issued_at_bucket: datetime
    expires_at: datetime
    audience: str
    purpose: str
    nonce: str
    status: str
    signature: str = ""
    key_identifier: str = ""


@dataclass(frozen=True, slots=True)
class VotingContextTerms:
    """The context facts this side needs, read from the registry.

    Deliberately a value object rather than a client: `credential-service`
    holds no read edge to a participant anywhere.
    """

    voting_context_reference: str
    credential_type: str
    audience_origin: str
    issuance_window_start: datetime
    issuance_window_end: datetime
    redemption_window_end: datetime
    revocation_cutoff: datetime
    timestamp_granularity_seconds: int
    minting_delay_min_seconds: int
    minting_delay_max_seconds: int


class AssertionVerifier:
    """Verifies a presented assertion against the issuer's trust boundary.

    Reference implementation: the same HMAC construction the Assertion
    Issuer signs with, verified here through an injected verifier callable
    so that `credential-service` holds no import path to
    `eligibility-service`.
    """

    def __init__(
        self,
        *,
        verify: Callable[[bytes, str], bool],
        expected_audience: str,
    ) -> None:
        self._verify = verify
        self._expected_audience = expected_audience

    def assert_valid(
        self,
        assertion: PresentedAssertion,
        *,
        terms: VotingContextTerms,
        now: datetime,
        canonical_message: bytes,
    ) -> None:
        if assertion.audience != self._expected_audience:
            raise AssertionAudienceMismatchError(
                "the assertion was presented to an audience it was not issued for"
            )
        if assertion.purpose != EXPECTED_ASSERTION_PURPOSE:
            raise AssertionPurposeMismatchError(
                "the assertion was presented for a purpose other than credential issuance"
            )
        if assertion.eligibility_result != EXPECTED_ASSERTION_RESULT:
            raise AssertionInvalidError("only an approved assertion authorizes an issuance")
        if not assertion.required_assurance_satisfied:
            # Fail-closed, and checked here rather than trusted upstream.
            # The flag crosses the boundary precisely so this side can act
            # on it; carrying it across and never reading it would make it
            # decoration, and the failure mode of decoration in an
            # assurance control is that a credential is issued against an
            # assertion whose assurance requirement was not met.
            raise AssertionAssuranceInsufficientError(
                "the assertion records that the context's assurance requirement was not met"
            )
        if assertion.voting_context_reference != terms.voting_context_reference:
            raise AssertionContextMismatchError(
                "the assertion belongs to a different voting context"
            )
        if now >= assertion.expires_at:
            raise AssertionExpiredError("the assertion has expired")
        if not assertion.signature or not self._verify(canonical_message, assertion.signature):
            raise AssertionInvalidError("the assertion did not verify")


def _coarsen(moment: datetime, granularity_seconds: int) -> datetime:
    epoch = int(moment.timestamp())
    return datetime.fromtimestamp(epoch - (epoch % granularity_seconds), tz=moment.tzinfo)


def _continuation_capability(redemption_reference: str) -> str:
    """A capability derived from the redemption, never from the credential.

    PACK-16 receives this and nothing else. It is not the credential, and
    it is not a function of the credential identifier.
    """
    return hashlib.sha256(("continuation:" + redemption_reference).encode("utf-8")).hexdigest()


@dataclass
class VotingCredentialIssuerService:
    """The transaction root for the voting side."""

    credentials: VotingCredentialStore
    spent_nonces: SpentNonceSet
    idempotency: CredentialIdempotencyStore
    redemptions: CredentialRedemptionStore
    replays: CredentialReplayStore
    verifier: AssertionVerifier
    allowed_origins: tuple[str, ...]
    idempotency_window_seconds: int = DEFAULT_IDEMPOTENCY_WINDOW_SECONDS

    def __post_init__(self) -> None:
        if self.idempotency_window_seconds > MAX_IDEMPOTENCY_WINDOW_SECONDS:
            raise ValueError(
                "the idempotency window is bounded; a longer window is a durable "
                "assertion-to-credential map"
            )

    # -- issuance ---------------------------------------------------------

    def issue(
        self,
        *,
        credential_id: UUID,
        assertion: PresentedAssertion,
        terms: VotingContextTerms,
        origin: str,
        idempotency_key: str,
        canonical_message: bytes,
        now: datetime,
        minting_delay_seconds: int,
        delivery_channel: str,
        event_id: UUID,
        correlation_id: UUID,
    ) -> tuple[VotingCredential, EventEnvelope]:
        """Issue exactly one credential for exactly one assertion nonce."""
        assert_origin_is_voting_client(origin, self.allowed_origins)
        assert_delivery_channel_permitted(delivery_channel)
        if not (terms.issuance_window_start <= now < terms.issuance_window_end):
            raise CredentialIssuanceWindowClosedError("the credential issuance window is not open")
        self.verifier.assert_valid(
            assertion, terms=terms, now=now, canonical_message=canonical_message
        )
        if not (
            terms.minting_delay_min_seconds
            <= minting_delay_seconds
            <= terms.minting_delay_max_seconds
        ):
            raise ValueError("the minting delay is outside the governed window")

        cached = self.idempotency.get(idempotency_key)
        if cached is not None and not cached.expired(now):
            existing = self.credentials.get(cached.voting_credential_id)
            if existing is None:
                raise VotingCredentialDependencyUnavailableError(
                    "an idempotency record points at a credential the store cannot return"
                )
            event = build_credential_event(
                event_id=event_id,
                event_type=DUPLICATE_ISSUANCE_REJECTED,
                credential=existing,
                reason_code="CREDENTIAL_DUPLICATE_REQUEST",
                granularity_seconds=terms.timestamp_granularity_seconds,
                correlation_id=correlation_id,
                occurred_at=now,
            )
            return (existing, event)

        # Atomic with issuance: the nonce is marked spent, and the spent
        # record carries nothing the credential produced.
        spent = SpentNonce(
            nonce=assertion.nonce,
            voting_context_reference=terms.voting_context_reference,
            spent_at_bucket=_coarsen(now, terms.timestamp_granularity_seconds),
        )
        if not self.spent_nonces.add(spent):
            raise AssertionAlreadyUsedError("the assertion nonce has already been spent")

        issued_at = now + timedelta(seconds=minting_delay_seconds)
        credential = VotingCredential(
            voting_credential_id=credential_id,
            credential_type=terms.credential_type,
            status=CredentialStatus.ISSUED,
            voting_context_reference=terms.voting_context_reference,
            issued_at_bucket=_coarsen(issued_at, terms.timestamp_granularity_seconds),
            expires_at=terms.redemption_window_end,
            audience_origin=terms.audience_origin,
        )
        self.credentials.save(credential)
        self.idempotency.put(
            CredentialIssuanceIdempotencyRecord(
                idempotency_key=idempotency_key,
                voting_credential_id=credential_id,
                created_at=now,
                expires_at=now + timedelta(seconds=self.idempotency_window_seconds),
            )
        )
        event = build_credential_event(
            event_id=event_id,
            event_type=CREDENTIAL_ISSUED,
            credential=credential,
            reason_code="CREDENTIAL_ISSUANCE_AUTHORIZED",
            granularity_seconds=terms.timestamp_granularity_seconds,
            correlation_id=correlation_id,
            occurred_at=issued_at,
        )
        return (credential, event)

    # -- revocation -------------------------------------------------------

    def revoke_unredeemed(
        self,
        *,
        voting_credential_id: UUID,
        terms: VotingContextTerms,
        reason_code: str,
        authority_role: str,
        dual_control_reference: str | None,
        now: datetime,
        event_id: UUID,
        correlation_id: UUID,
    ) -> tuple[VotingCredential, EventEnvelope]:
        """Revoke before redemption and before the cutoff, or refuse.

        There is no parameter here for a participant: revocation cannot be
        targeted at a person, because the interface cannot express it.
        """
        credential = self.credentials.get(voting_credential_id)
        if credential is None:
            raise UnknownVotingCredentialError("no credential exists for the given reference")
        assert_absorbing_redeemed(credential.status)
        if now >= terms.revocation_cutoff:
            raise CredentialRevocationCutoffPassedError(
                "the revocation cutoff has passed; participation can no longer be withdrawn"
            )
        revocation = CredentialRevocation(
            voting_credential_id=voting_credential_id,
            reason_code=reason_code,
            revoked_at=now,
            authority_role=authority_role,
            dual_control_reference=dual_control_reference,
            before_cutoff=True,
        )
        revoked = VotingCredential(
            voting_credential_id=credential.voting_credential_id,
            credential_type=credential.credential_type,
            status=CredentialStatus.REVOKED,
            voting_context_reference=credential.voting_context_reference,
            issued_at_bucket=credential.issued_at_bucket,
            expires_at=credential.expires_at,
            revoked_at=_coarsen(revocation.revoked_at, terms.timestamp_granularity_seconds),
            revocation_reason=reason_code,
            audience_origin=credential.audience_origin,
        )
        self.credentials.save(revoked)
        event = build_credential_event(
            event_id=event_id,
            event_type=CREDENTIAL_REVOKED,
            credential=revoked,
            reason_code=reason_code,
            granularity_seconds=terms.timestamp_granularity_seconds,
            correlation_id=correlation_id,
            occurred_at=now,
        )
        return (revoked, event)

    # -- redemption -------------------------------------------------------

    def redeem(
        self,
        *,
        voting_credential_id: UUID,
        terms: VotingContextTerms,
        origin: str,
        now: datetime,
        event_id: UUID,
        correlation_id: UUID,
        replay_id: UUID,
    ) -> tuple[CredentialRedemption, EventEnvelope]:
        """Atomically consume a credential and hand back a capability."""
        assert_origin_is_voting_client(origin, self.allowed_origins)
        credential = self.credentials.get(voting_credential_id)
        if credential is None:
            raise UnknownVotingCredentialError("no credential exists for the given reference")
        try:
            credential.assert_redeemable(
                now=now,
                voting_context_reference=terms.voting_context_reference,
                audience_origin=terms.audience_origin,
            )
        except Exception as refusal:
            reason_code = getattr(refusal, "reason_code", "CREDENTIAL_REPLAY_DETECTED")
            if reason_code == "CREDENTIAL_ALREADY_REDEEMED":
                self.replays.record(
                    CredentialReplayRecord(
                        replay_id=replay_id,
                        voting_context_reference=terms.voting_context_reference,
                        reason_code="CREDENTIAL_REPLAY_DETECTED",
                        detected_at_bucket=_coarsen(now, terms.timestamp_granularity_seconds),
                    )
                )
                raise CredentialReplayDetectedError(
                    "a further presentation of a spent credential was refused"
                ) from refusal
            raise

        redemption_reference = secrets.token_hex(16)
        redemption = CredentialRedemption(
            redemption_reference=redemption_reference,
            voting_credential_id=voting_credential_id,
            voting_context_reference=terms.voting_context_reference,
            redeemed_at_bucket=_coarsen(now, terms.timestamp_granularity_seconds),
            continuation_capability=_continuation_capability(redemption_reference),
        )
        redeemed = VotingCredential(
            voting_credential_id=credential.voting_credential_id,
            credential_type=credential.credential_type,
            status=CredentialStatus.REDEEMED,
            voting_context_reference=credential.voting_context_reference,
            issued_at_bucket=credential.issued_at_bucket,
            expires_at=credential.expires_at,
            redeemed_at=redemption.redeemed_at_bucket,
            redemption_reference=redemption_reference,
            audience_origin=credential.audience_origin,
        )
        self.credentials.save(redeemed)
        self.redemptions.save(redemption)
        event = build_credential_event(
            event_id=event_id,
            event_type=CREDENTIAL_REDEEMED,
            credential=redeemed,
            reason_code="CREDENTIAL_REDEEMED",
            granularity_seconds=terms.timestamp_granularity_seconds,
            correlation_id=correlation_id,
            occurred_at=now,
        )
        return (redemption, event)

    def record_replay(
        self,
        *,
        replay_id: UUID,
        voting_context_reference: str,
        granularity_seconds: int,
        now: datetime,
        event_id: UUID,
        correlation_id: UUID,
    ) -> EventEnvelope:
        record = CredentialReplayRecord(
            replay_id=replay_id,
            voting_context_reference=voting_context_reference,
            reason_code="CREDENTIAL_REPLAY_DETECTED",
            detected_at_bucket=_coarsen(now, granularity_seconds),
        )
        self.replays.record(record)
        return build_replay_event(
            event_id=event_id,
            event_type=CREDENTIAL_REPLAY_REJECTED,
            replay=record,
            correlation_id=correlation_id,
            occurred_at=record.detected_at_bucket,
        )

    # -- privacy-safe status ---------------------------------------------

    def privacy_safe_status(self, voting_credential_id: UUID) -> dict[str, object]:
        """Answer only against a reference the holder already supplied.

        There is no search operation on this service, and an unknown
        reference produces the same shape as a revoked one so the lookup
        cannot be used as an oracle.
        """
        credential = self.credentials.get(voting_credential_id)
        if credential is None:
            return {
                "status_class": "unknown_or_withdrawn",
                "voting_context_reference": "",
                "expires_at_bucket": "",
            }
        return credential.privacy_safe_status()
