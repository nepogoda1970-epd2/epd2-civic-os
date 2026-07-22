"""`IdentityRecord`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 7.3.

Forbidden per canon: voting lists, chosen options, initiative lists,
political preferences, delegations. None of those fields exist here -
enforced structurally by this dataclass's field set, and by
`tests/test_identity_leakage.py` at the repository root.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    ForbiddenVerificationTransitionError,
    UnknownVerificationStatusError,
)


class VerificationStatus(StrEnum):
    """Mapped 1:1 onto canon section 20.2's canonical identity events
    (`identity.verification_started` -> PENDING, `identity.verified` ->
    VERIFIED, `identity.verification_failed` -> FAILED,
    `identity.verification_expired` -> EXPIRED,
    `identity.duplicate_suspected` -> DUPLICATE_SUSPECTED,
    `identity.manual_review_required` -> MANUAL_REVIEW_REQUIRED).
    """

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    DUPLICATE_SUSPECTED = "duplicate_suspected"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


ALLOWED_TRANSITIONS: frozenset[tuple[VerificationStatus, VerificationStatus]] = frozenset(
    {
        (VerificationStatus.PENDING, VerificationStatus.VERIFIED),
        (VerificationStatus.PENDING, VerificationStatus.FAILED),
        (VerificationStatus.PENDING, VerificationStatus.DUPLICATE_SUSPECTED),
        (VerificationStatus.PENDING, VerificationStatus.MANUAL_REVIEW_REQUIRED),
        (VerificationStatus.MANUAL_REVIEW_REQUIRED, VerificationStatus.VERIFIED),
        (VerificationStatus.MANUAL_REVIEW_REQUIRED, VerificationStatus.FAILED),
        (VerificationStatus.DUPLICATE_SUSPECTED, VerificationStatus.MANUAL_REVIEW_REQUIRED),
        (VerificationStatus.DUPLICATE_SUSPECTED, VerificationStatus.FAILED),
        (VerificationStatus.VERIFIED, VerificationStatus.EXPIRED),
        (VerificationStatus.FAILED, VerificationStatus.PENDING),
        (VerificationStatus.EXPIRED, VerificationStatus.PENDING),
    }
)

CANONICAL_EVENT_FOR_TRANSITION: dict[tuple[VerificationStatus, VerificationStatus], str] = {
    (VerificationStatus.PENDING, VerificationStatus.VERIFIED): "identity.verified",
    (VerificationStatus.MANUAL_REVIEW_REQUIRED, VerificationStatus.VERIFIED): "identity.verified",
    (VerificationStatus.PENDING, VerificationStatus.FAILED): "identity.verification_failed",
    (
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
        VerificationStatus.FAILED,
    ): "identity.verification_failed",
    (
        VerificationStatus.DUPLICATE_SUSPECTED,
        VerificationStatus.FAILED,
    ): "identity.verification_failed",
    (
        VerificationStatus.PENDING,
        VerificationStatus.DUPLICATE_SUSPECTED,
    ): "identity.duplicate_suspected",
    (
        VerificationStatus.PENDING,
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
    ): "identity.manual_review_required",
    (
        VerificationStatus.DUPLICATE_SUSPECTED,
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
    ): "identity.manual_review_required",
    # ADR-002: explicit revocation and natural expiry both map to the
    # canonical identity.verification_expired event - canon defines no
    # separate revocation event.
    (VerificationStatus.VERIFIED, VerificationStatus.EXPIRED): "identity.verification_expired",
}


def parse_status(value: str) -> VerificationStatus:
    try:
        return VerificationStatus(value)
    except ValueError as exc:
        raise UnknownVerificationStatusError(f"unknown verification status: {value!r}") from exc


def assert_transition_allowed(current: VerificationStatus, target: VerificationStatus) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenVerificationTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    """Canon section 7.3 fields exactly."""

    identity_record_id: UUID
    account_id: UUID
    verification_provider: str
    verification_level: str
    verification_status: VerificationStatus
    verified_at: datetime | None
    expires_at: datetime | None
    country: str
    duplicate_check_status: str
    provider_reference: str

    def __post_init__(self) -> None:
        if self.verified_at is not None and self.verified_at.tzinfo is None:
            raise ValueError("verified_at must be timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")

    def with_status(
        self,
        new_status: VerificationStatus,
        *,
        verified_at: datetime | None = None,
        expires_at: datetime | None = None,
        duplicate_check_status: str | None = None,
    ) -> IdentityRecord:
        """Return a new `IdentityRecord` transitioned to `new_status`.
        Any of `verified_at`/`expires_at`/`duplicate_check_status` left as
        `None` keeps the current value unchanged.
        """
        assert_transition_allowed(self.verification_status, new_status)
        return IdentityRecord(
            identity_record_id=self.identity_record_id,
            account_id=self.account_id,
            verification_provider=self.verification_provider,
            verification_level=self.verification_level,
            verification_status=new_status,
            verified_at=verified_at if verified_at is not None else self.verified_at,
            expires_at=expires_at if expires_at is not None else self.expires_at,
            country=self.country,
            duplicate_check_status=(
                duplicate_check_status
                if duplicate_check_status is not None
                else self.duplicate_check_status
            ),
            provider_reference=self.provider_reference,
        )
