"""PACK-15 voting credential domain (VC-04).

The voting side of the trust boundary. This module knows a context, a
class, a nonce and a credential. It does not know - and has no field,
column or parameter through which it could learn - who the participant is.

**The load-bearing property (ADR-093).** The spent-nonce record is a
*set*, not a map: `SpentNonce` carries the nonce and nothing it produced,
and `VotingCredential` carries no assertion reference. There is therefore
no row anywhere that contains both, so no compromise, collusion, export,
backup or legal compulsion can produce the pairing from this system's data.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_credential_service.voting_credential_exceptions import (
    CredentialAlreadyRedeemedError,
    CredentialAudienceMismatchError,
    CredentialContextMismatchError,
    CredentialExpiredError,
    CredentialOriginRefusedError,
    CredentialRevocationCutoffPassedError,
    CredentialRevokedError,
    DeliveryChannelRefusedError,
    ForbiddenCredentialFieldError,
)

#: Structurally absent from every artifact in this module. Canon 10.1's
#: existing prohibition on `ParticipationCredential`, extended by PACK-15
#: with the two additions that make the cut real.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "identity_record_id",
        "person_id",
        "person_record_id",
        "account_id",
        "membership_id",
        "member_number",
        "full_name",
        "date_of_birth",
        "address",
        "email",
        "phone",
        "eid_subject",
        "communication_persona_id",
        # PACK-15's additions - the load-bearing ones:
        "assertion_id",
        "eligibility_assertion_id",
        "assertion_reference",
        "nonce",
        "context_pseudonym",
        "participant_reference",
        "ballot_id",
        "vote_content",
    }
)

#: The only permitted delivery channel. Credential material exists only
#: inside the isolated voting origin (`OD-P15-07`).
PERMITTED_DELIVERY_CHANNEL = "isolated_ws03_origin"

#: The ten prohibited channels, named so that a refusal can name one.
PROHIBITED_DELIVERY_CHANNELS: frozenset[str] = frozenset(
    {
        "email",
        "sms",
        "clipboard",
        "url_query",
        "downloadable_file",
        "on_screen_copyable_text",
        "push_notification",
        "print_or_pdf",
        "operator_visible_surface",
        "persistent_client_storage",
    }
)


class CredentialStatus(StrEnum):
    REQUESTED = "requested"
    ELIGIBLE = "eligible"
    QUEUED = "queued"
    ISSUED = "issued"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REDEEMED = "redeemed"
    REPLAY_REJECTED = "replay_rejected"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


#: Permitted transitions. `redeemed` is **absorbing**: it maps to the
#: empty set, and no privileged path adds an edge out of it.
CREDENTIAL_TRANSITIONS: Mapping[CredentialStatus, frozenset[CredentialStatus]] = {
    CredentialStatus.REQUESTED: frozenset(
        {CredentialStatus.ELIGIBLE, CredentialStatus.CANCELLED, CredentialStatus.DISPUTED}
    ),
    CredentialStatus.ELIGIBLE: frozenset({CredentialStatus.QUEUED, CredentialStatus.CANCELLED}),
    CredentialStatus.QUEUED: frozenset({CredentialStatus.ISSUED, CredentialStatus.CANCELLED}),
    CredentialStatus.ISSUED: frozenset(
        {
            CredentialStatus.REDEEMED,
            CredentialStatus.REVOKED,
            CredentialStatus.EXPIRED,
            CredentialStatus.CANCELLED,
            CredentialStatus.DISPUTED,
        }
    ),
    CredentialStatus.REDEEMED: frozenset(),
    CredentialStatus.REVOKED: frozenset({CredentialStatus.DISPUTED}),
    CredentialStatus.EXPIRED: frozenset({CredentialStatus.DISPUTED}),
    CredentialStatus.CANCELLED: frozenset(),
    CredentialStatus.REPLAY_REJECTED: frozenset(),
    CredentialStatus.DISPUTED: frozenset({CredentialStatus.REVOKED, CredentialStatus.EXPIRED}),
}


def transition_permitted(current: CredentialStatus, target: CredentialStatus) -> bool:
    return target in CREDENTIAL_TRANSITIONS[current]


def assert_absorbing_redeemed(current: CredentialStatus) -> None:
    """`redeemed` never leaves `redeemed`.

    Stated as its own function so the property is asserted directly by a
    test rather than inferred from the transition table.
    """
    if current is CredentialStatus.REDEEMED:
        raise CredentialAlreadyRedeemedError(
            "redeemed is an absorbing state: no act moves a credential out of it"
        )


def assert_no_forbidden_credential_fields(payload: Mapping[str, object]) -> None:
    offending = sorted(set(payload) & FORBIDDEN_FIELD_NAMES)
    if offending:
        raise ForbiddenCredentialFieldError(
            "forbidden fields in a voting-side payload: " + ", ".join(offending)
        )


def assert_delivery_channel_permitted(channel: str) -> None:
    """Credential material leaves no surface but the isolated origin."""
    if channel != PERMITTED_DELIVERY_CHANNEL:
        raise DeliveryChannelRefusedError(
            f"delivery via {channel!r} is refused; credential material exists only "
            "inside the isolated voting origin"
        )


@dataclass(frozen=True, slots=True)
class SpentNonce:
    """A **set** member, not a map entry.

    There is deliberately no `credential_id` field here and none may be
    added: this record answers "was this nonce used?" and never "what did
    it produce?" (ADR-093).
    """

    nonce: str
    voting_context_reference: str
    spent_at_bucket: datetime

    def __post_init__(self) -> None:
        if not self.nonce:
            raise ValueError("a spent-nonce record carries the nonce it spent")
        if self.spent_at_bucket.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")


@dataclass(frozen=True, slots=True)
class VotingCredential:
    """Opaque, single-use, context- and audience-bound.

    No identity field, **no assertion reference** and no pseudonym: see
    `FORBIDDEN_FIELD_NAMES`, which the persistence tests assert against the
    dataclass's own field set.
    """

    voting_credential_id: UUID
    credential_type: str
    status: CredentialStatus
    voting_context_reference: str
    issued_at_bucket: datetime
    expires_at: datetime
    redeemed_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    redemption_reference: str | None = None
    audience_origin: str = ""

    def __post_init__(self) -> None:
        if not self.credential_type:
            raise ValueError("a credential names its type, which follows the context type")
        if self.issued_at_bucket.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")
        if self.expires_at <= self.issued_at_bucket:
            raise ValueError("a credential expires after it is issued")
        if self.revoked_at is not None and self.revocation_reason is None:
            raise ValueError("a revocation carries a registered reason code")

    @property
    def redeemed(self) -> bool:
        return self.status is CredentialStatus.REDEEMED

    def assert_redeemable(
        self,
        *,
        now: datetime,
        voting_context_reference: str,
        audience_origin: str,
    ) -> None:
        """Every check the atomic redemption performs, in order."""
        if audience_origin != self.audience_origin:
            raise CredentialAudienceMismatchError(
                "the credential was presented at an origin it is not bound to"
            )
        if voting_context_reference != self.voting_context_reference:
            raise CredentialContextMismatchError(
                "the credential belongs to a different voting context"
            )
        if self.status is CredentialStatus.REDEEMED:
            raise CredentialAlreadyRedeemedError("the credential has already been redeemed")
        if self.status is CredentialStatus.REVOKED:
            raise CredentialRevokedError("the credential was revoked before redemption")
        if self.status is CredentialStatus.EXPIRED or now >= self.expires_at:
            raise CredentialExpiredError("the credential has expired")
        if self.status is not CredentialStatus.ISSUED:
            raise CredentialContextMismatchError(
                f"a credential in status {self.status.value} cannot be redeemed"
            )

    def privacy_safe_status(self) -> dict[str, object]:
        """The only status shape ever returned to a holder.

        Deliberately uniform: an unknown reference and a revoked credential
        produce the same shape, so the lookup cannot be used as an oracle.
        """
        payload: dict[str, object] = {
            "status_class": self.status.value,
            "voting_context_reference": self.voting_context_reference,
            "expires_at_bucket": self.expires_at.isoformat(),
        }
        assert_no_forbidden_credential_fields(payload)
        return payload


@dataclass(frozen=True, slots=True)
class CredentialIssuanceRequest:
    """One issuance attempt, keyed for idempotency on the nonce."""

    request_id: UUID
    voting_context_reference: str
    idempotency_key: str
    origin: str
    requested_at: datetime

    def __post_init__(self) -> None:
        if not self.idempotency_key:
            raise ValueError("an issuance request carries an idempotency key")


@dataclass(frozen=True, slots=True)
class CredentialIssuanceIdempotencyRecord:
    """A bounded retry-window cache entry.

    It maps the idempotency key to the credential so a retry returns the
    same outcome - and it **expires**. `assert_not_durable` is what stops
    it from quietly becoming the assertion-to-credential map ADR-093
    forbids.
    """

    idempotency_key: str
    voting_credential_id: UUID
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if self.expires_at <= self.created_at:
            raise ValueError("an idempotency record expires after it is created")

    def expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def assert_not_durable(self, max_window_seconds: int) -> None:
        window = int((self.expires_at - self.created_at).total_seconds())
        if window > max_window_seconds:
            raise ValueError(
                f"an idempotency window of {window}s exceeds the bounded maximum "
                f"{max_window_seconds}s; a longer window is a durable map"
            )


@dataclass(frozen=True, slots=True)
class CredentialRevocation:
    voting_credential_id: UUID
    reason_code: str
    revoked_at: datetime
    authority_role: str
    dual_control_reference: str | None = None
    before_cutoff: bool = True

    def __post_init__(self) -> None:
        if not self.reason_code:
            raise ValueError("a revocation carries a registered reason code")
        if not self.before_cutoff:
            raise CredentialRevocationCutoffPassedError(
                "a revocation after the cutoff is refused, not recorded"
            )


@dataclass(frozen=True, slots=True)
class CredentialRedemption:
    """The atomic redemption record and its continuation capability."""

    redemption_reference: str
    voting_credential_id: UUID
    voting_context_reference: str
    redeemed_at_bucket: datetime
    continuation_capability: str

    def __post_init__(self) -> None:
        if not self.continuation_capability:
            raise ValueError("a redemption yields a minimal continuation capability")
        if self.continuation_capability == str(self.voting_credential_id):
            raise ValueError(
                "the continuation capability is never the credential; PACK-16 must not "
                "receive a value derived from the credential identifier"
            )


@dataclass(frozen=True, slots=True)
class CredentialReplayRecord:
    """A replay attempt. Carries no holder, because none is knowable."""

    replay_id: UUID
    voting_context_reference: str
    reason_code: str
    detected_at_bucket: datetime
    timing_class: str = "bucketed"
    forbidden: Mapping[str, object] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if self.forbidden:
            raise ForbiddenCredentialFieldError(
                "a replay record carries no attribution of any kind"
            )


def assert_origin_is_voting_client(origin: str, allowed_origins: tuple[str, ...]) -> None:
    """Issuance and redemption originate from the isolated origin only."""
    if origin not in allowed_origins:
        raise CredentialOriginRefusedError(
            "credential operations originate from the isolated voting origin only"
        )
