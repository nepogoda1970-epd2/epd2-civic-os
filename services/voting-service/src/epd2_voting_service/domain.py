"""`Ballot`, `BallotOption`, `VoteEnvelope`, `VoteReceipt`, per
`docs/canonical/TZ-00-domain-event-canon.md`, sections 15.1-15.4 (ADR-005
consolidates "Ballot Definition Service", "Vote Casting Service", and
"Receipt Service" into this one package).

`VoteEnvelope`/`VoteReceipt` are the vote-linkability-critical entities
(CT-00-09, canon section 15.3's "Запрет"): see `FORBIDDEN_FIELD_NAMES`
below, mirrored in style from
`epd2_credential_service.domain.FORBIDDEN_FIELD_NAMES`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_voting_service.exceptions import (
    ForbiddenBallotOptionTransitionError,
    ForbiddenBallotTransitionError,
    ForbiddenVoteEnvelopeTransitionError,
    ForbiddenVoteReceiptTransitionError,
    UnknownBallotOptionStatusError,
    UnknownBallotStatusError,
    UnknownVoteEnvelopeStatusError,
    UnknownVoteReceiptStatusError,
)

# ============================================================================
# Ballot (canon 15.1)
# ============================================================================


class BallotMethod(StrEnum):
    """ADR-009 item 4 (accepted): the pilot restricts `ballot_method` to
    exactly these two values. Ranked-choice/multi-select is explicitly
    out of scope for this pack and would need its own future ADR - do not
    add values here without one."""

    SINGLE_CHOICE = "single_choice"
    YES_NO = "yes_no"


class BallotStatus(StrEnum):
    """Canon section 15.1's exact status list (11 values)."""

    DRAFT = "draft"
    CONFIGURATION_REVIEW = "configuration_review"
    SCHEDULED = "scheduled"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"
    TALLYING = "tallying"
    TALLIED = "tallied"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    INVALIDATED = "invalidated"


def parse_ballot_status(value: str) -> BallotStatus:
    try:
        return BallotStatus(value)
    except ValueError as exc:
        raise UnknownBallotStatusError(f"unknown ballot status: {value!r}") from exc


#: Exact transition table given by spec. `closed` never returns to
#: `open`; `tallying`/`tallied` never precede `closed`. The `invalidated`
#: transitions exist ONLY at this structural level (ADR-009 item 14,
#: amended): no `application.py` command may ever reach `invalidated` -
#: see README.md.
ALLOWED_TRANSITIONS: frozenset[tuple[BallotStatus, BallotStatus]] = frozenset(
    {
        (BallotStatus.DRAFT, BallotStatus.CONFIGURATION_REVIEW),
        (BallotStatus.CONFIGURATION_REVIEW, BallotStatus.SCHEDULED),
        (BallotStatus.SCHEDULED, BallotStatus.OPEN),
        (BallotStatus.OPEN, BallotStatus.PAUSED),
        (BallotStatus.PAUSED, BallotStatus.OPEN),
        (BallotStatus.OPEN, BallotStatus.CLOSED),
        (BallotStatus.CLOSED, BallotStatus.TALLYING),
        (BallotStatus.TALLYING, BallotStatus.TALLIED),
        (BallotStatus.TALLIED, BallotStatus.PUBLISHED),
        (BallotStatus.DRAFT, BallotStatus.CANCELLED),
        (BallotStatus.CONFIGURATION_REVIEW, BallotStatus.CANCELLED),
        (BallotStatus.SCHEDULED, BallotStatus.CANCELLED),
        (BallotStatus.DRAFT, BallotStatus.INVALIDATED),
        (BallotStatus.CONFIGURATION_REVIEW, BallotStatus.INVALIDATED),
        (BallotStatus.SCHEDULED, BallotStatus.INVALIDATED),
    }
)


def assert_ballot_transition_allowed(current: BallotStatus, target: BallotStatus) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenBallotTransitionError(
            f"ballot transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: Canon section 15.1 (ADR-010, canon 0.2.0): "необязательно; при
#: отсутствии значения применяется репозиторный default (72 часа)".
DEFAULT_CHALLENGE_WINDOW_HOURS: int = 72

#: The fields `configuration_hash` covers (plus `BallotOption` rows,
#: enforced separately at the application/store layer) - frozen once
#: `Ballot.status` reaches `configuration_review` or later (CT-00-10).
_CONFIGURATION_FIELD_NAMES: tuple[str, ...] = (
    "ballot_method",
    "secrecy_mode",
    "eligibility_rule_version",
    "delegation_policy_version",
    "quorum_rule",
    "threshold_rule",
    "opens_at",
    "closes_at",
    "challenge_window_hours",
)


@dataclass(frozen=True, slots=True)
class Ballot:
    """Canon section 15.1 fields exactly - no extra public field. Internal
    bookkeeping (`created_by_actor_id` for ADR-009 item 7's second-actor
    approval check, and the frozen `EligibilitySnapshot.digest` this
    ballot's `configuration_hash` was computed against) lives in
    `storage.py`, never on this public dataclass - see README.md."""

    ballot_id: UUID
    space_id: UUID
    subject_type: str
    subject_id: UUID
    question: str
    ballot_method: BallotMethod
    secrecy_mode: str
    eligibility_rule_version: int
    delegation_policy_version: int
    quorum_rule: str
    threshold_rule: str
    opens_at: datetime
    closes_at: datetime
    status: BallotStatus
    configuration_hash: str | None
    challenge_window_hours: int | None

    def __post_init__(self) -> None:
        for name in ("opens_at", "closes_at"):
            value = getattr(self, name)
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be after opens_at")
        if self.eligibility_rule_version < 1:
            raise ValueError("eligibility_rule_version must be >= 1")
        if self.delegation_policy_version < 1:
            raise ValueError("delegation_policy_version must be >= 1")
        if self.challenge_window_hours is not None and self.challenge_window_hours < 0:
            raise ValueError("challenge_window_hours must not be negative")

    def with_status(self, new_status: BallotStatus) -> Ballot:
        assert_ballot_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)

    def with_configuration_locked(self, configuration_hash: str) -> Ballot:
        """The single `draft -> configuration_review` transition also
        freezes `configuration_hash` in the same step (there is no
        earlier point at which a real `configuration_hash` value could
        exist) - see `application.submit_ballot_for_configuration_review`."""
        assert_ballot_transition_allowed(self.status, BallotStatus.CONFIGURATION_REVIEW)
        return replace(
            self, status=BallotStatus.CONFIGURATION_REVIEW, configuration_hash=configuration_hash
        )


def effective_challenge_window_hours(ballot: Ballot) -> int:
    """Canon section 15.1: absent `challenge_window_hours` falls back to
    the repository default of 72 hours; present values override it
    per-ballot."""
    return (
        ballot.challenge_window_hours
        if ballot.challenge_window_hours is not None
        else DEFAULT_CHALLENGE_WINDOW_HOURS
    )


def configuration_fields(ballot: Ballot) -> tuple[object, ...]:
    """The ordered tuple of `_CONFIGURATION_FIELD_NAMES` values, using the
    *effective* (default-resolved) challenge window - used both to
    compute `configuration_hash` and, in `storage.py`, to detect an
    attempted mutation of a frozen ballot (CT-00-10)."""
    return (
        ballot.ballot_method.value,
        ballot.secrecy_mode,
        ballot.eligibility_rule_version,
        ballot.delegation_policy_version,
        ballot.quorum_rule,
        ballot.threshold_rule,
        ballot.opens_at,
        ballot.closes_at,
        effective_challenge_window_hours(ballot),
    )


def compute_ballot_configuration_hash(
    *,
    ballot_method: BallotMethod,
    secrecy_mode: str,
    eligibility_rule_version: int,
    delegation_policy_version: int,
    quorum_rule: str,
    threshold_rule: str,
    opens_at: datetime,
    closes_at: datetime,
    challenge_window_hours: int,
    eligibility_snapshot_digest: str,
) -> str:
    """Deterministic digest over exactly the fields `configuration_hash`
    covers, per CT-00-10, mirroring
    `epd2_eligibility_service.domain.compute_snapshot_digest`'s style.

    `eligibility_snapshot_digest` (the real `EligibilitySnapshot.digest`
    this ballot's `eligibility_rule_version` resolved to at freeze time,
    fetched via `epd2_eligibility_service.application.get_eligibility_snapshot`,
    ADR-008) is folded into the hash so the freeze is checked against
    actual frozen snapshot content, not a bare version number - a
    snapshot digest mismatch after the fact is structurally detectable.
    """
    payload = {
        "ballot_method": ballot_method.value,
        "secrecy_mode": secrecy_mode,
        "eligibility_rule_version": eligibility_rule_version,
        "delegation_policy_version": delegation_policy_version,
        "quorum_rule": quorum_rule,
        "threshold_rule": threshold_rule,
        "opens_at": opens_at,
        "closes_at": closes_at,
        "challenge_window_hours": challenge_window_hours,
        "eligibility_snapshot_digest": eligibility_snapshot_digest,
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


# ============================================================================
# BallotOption (canon 15.2)
# ============================================================================


class BallotOptionStatus(StrEnum):
    """Canon section 15.2 enumerates no explicit status list beyond
    "После открытия Ballot варианты блокируются" (options lock once the
    ballot opens) - this minimal two-value enum is this service's own
    documented completion of that requirement."""

    ACTIVE = "active"
    LOCKED = "locked"


def parse_ballot_option_status(value: str) -> BallotOptionStatus:
    try:
        return BallotOptionStatus(value)
    except ValueError as exc:
        raise UnknownBallotOptionStatusError(f"unknown ballot option status: {value!r}") from exc


ALLOWED_OPTION_TRANSITIONS: frozenset[tuple[BallotOptionStatus, BallotOptionStatus]] = frozenset(
    {
        (BallotOptionStatus.ACTIVE, BallotOptionStatus.LOCKED),
    }
)


def assert_ballot_option_transition_allowed(
    current: BallotOptionStatus, target: BallotOptionStatus
) -> None:
    if (current, target) not in ALLOWED_OPTION_TRANSITIONS:
        raise ForbiddenBallotOptionTransitionError(
            f"ballot option transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class BallotOption:
    """Canon section 15.2 fields exactly. Per ADR-009 item 3 (accepted):
    abstention MUST be modeled as an explicit `BallotOption` (e.g.
    `option_code = "abstain"`) - there is no special-cased abstention
    field or branch anywhere in this service; it is just another option
    row."""

    ballot_option_id: UUID
    ballot_id: UUID
    option_code: str
    label: str
    description: str
    display_order: int
    status: BallotOptionStatus

    def __post_init__(self) -> None:
        if self.display_order < 0:
            raise ValueError("display_order must not be negative")

    def with_status(self, new_status: BallotOptionStatus) -> BallotOption:
        assert_ballot_option_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)


# ============================================================================
# VoteEnvelope (canon 15.3) - THE MOST SAFETY-CRITICAL ENTITY IN THIS PACK
# ============================================================================


class VoteEnvelopeStatus(StrEnum):
    """Canon section 15.3's exact status list."""

    RECEIVED = "received"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    INCLUDED = "included"
    QUARANTINED = "quarantined"


def parse_vote_envelope_status(value: str) -> VoteEnvelopeStatus:
    try:
        return VoteEnvelopeStatus(value)
    except ValueError as exc:
        raise UnknownVoteEnvelopeStatusError(f"unknown vote envelope status: {value!r}") from exc


ALLOWED_VOTE_ENVELOPE_TRANSITIONS: frozenset[tuple[VoteEnvelopeStatus, VoteEnvelopeStatus]] = (
    frozenset(
        {
            (VoteEnvelopeStatus.RECEIVED, VoteEnvelopeStatus.VALIDATED),
            (VoteEnvelopeStatus.RECEIVED, VoteEnvelopeStatus.REJECTED),
            (VoteEnvelopeStatus.RECEIVED, VoteEnvelopeStatus.QUARANTINED),
            (VoteEnvelopeStatus.VALIDATED, VoteEnvelopeStatus.SUPERSEDED),
            (VoteEnvelopeStatus.VALIDATED, VoteEnvelopeStatus.INCLUDED),
            (VoteEnvelopeStatus.QUARANTINED, VoteEnvelopeStatus.VALIDATED),
            (VoteEnvelopeStatus.QUARANTINED, VoteEnvelopeStatus.REJECTED),
        }
    )
)


def assert_vote_envelope_transition_allowed(
    current: VoteEnvelopeStatus, target: VoteEnvelopeStatus
) -> None:
    if (current, target) not in ALLOWED_VOTE_ENVELOPE_TRANSITIONS:
        raise ForbiddenVoteEnvelopeTransitionError(
            f"vote envelope transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: Canon section 15.3's "Запрет" / CT-00-09 (Vote Linkability), mirrored
#: in style exactly from
#: `epd2_credential_service.domain.FORBIDDEN_FIELD_NAMES`. No field named
#: here may ever appear on `VoteEnvelope` or `VoteReceipt` (see
#: `tests/test_domain.py`'s `assert set(__dataclass_fields__) &
#: FORBIDDEN_FIELD_NAMES == set()`).
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "identity_record_id",
        "full_name",
        "email",
        "membership_id",
        "identity_provider_reference",
    }
)


@dataclass(frozen=True, slots=True)
class VoteEnvelope:
    """Canon section 15.3 fields exactly.

    `credential_proof` must reference a `ParticipationCredential`, never
    an `account_id` - it is that credential's own opaque `credential_id`
    (a UUID), validated via
    `epd2_credential_service.application.validate_participation_credential`
    (ADR-008) *before* this envelope is ever constructed - see
    `application.cast_vote`. Nothing in this module ever resolves a
    `VoteEnvelope` back to an `Account`/`IdentityRecord`: there is no
    import of `epd2_account_service` or `epd2_identity_service` anywhere
    in this package (see README.md and
    `tests/test_domain.py::test_no_code_path_resolves_a_vote_envelope_to_an_account`).
    """

    vote_envelope_id: UUID
    ballot_id: UUID
    credential_proof: UUID
    encrypted_or_encoded_choice: str
    submitted_at: datetime
    integrity_hash: str
    validation_status: VoteEnvelopeStatus
    included_in_tally: bool

    def __post_init__(self) -> None:
        if self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware")
        if not self.encrypted_or_encoded_choice:
            raise ValueError("encrypted_or_encoded_choice must not be empty")
        if not self.integrity_hash:
            raise ValueError("integrity_hash must not be empty")
        if self.included_in_tally and self.validation_status != VoteEnvelopeStatus.INCLUDED:
            raise ValueError("included_in_tally requires validation_status == included")

    def with_status(self, new_status: VoteEnvelopeStatus) -> VoteEnvelope:
        assert_vote_envelope_transition_allowed(self.validation_status, new_status)
        included = self.included_in_tally
        if new_status == VoteEnvelopeStatus.INCLUDED:
            included = True
        elif new_status in (VoteEnvelopeStatus.SUPERSEDED, VoteEnvelopeStatus.REJECTED):
            included = False
        return replace(self, validation_status=new_status, included_in_tally=included)


def compute_vote_envelope_integrity_hash(
    *,
    ballot_id: UUID,
    credential_proof: UUID,
    encrypted_or_encoded_choice: str,
    submitted_at: datetime,
) -> str:
    """Deterministic tamper-evidence digest for one `VoteEnvelope`'s own
    content, mirroring `compute_snapshot_digest`'s style. Deliberately
    includes `encrypted_or_encoded_choice` (this hash is internal to the
    envelope itself, used by `application.validate_vote` to detect
    tampering) - contrast with `compute_vote_receipt_hash` below, which
    deliberately does NOT re-derive anything from the choice directly, so
    a receipt cannot be used to reconstruct it."""
    payload = {
        "ballot_id": ballot_id,
        "credential_proof": credential_proof,
        "encrypted_or_encoded_choice": encrypted_or_encoded_choice,
        "submitted_at": submitted_at,
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


# ============================================================================
# VoteReceipt (canon 15.4)
# ============================================================================


class VoteReceiptVerificationStatus(StrEnum):
    """Canon section 15.4 enumerates no explicit status list - this
    minimal three-value enum is this service's own documented completion,
    matching the "issued / verified / invalid" lifecycle canon's own
    prose implies ("должен позволять проверить включение бюллетеня")."""

    ISSUED = "issued"
    VERIFIED = "verified"
    INVALID = "invalid"


def parse_vote_receipt_verification_status(value: str) -> VoteReceiptVerificationStatus:
    try:
        return VoteReceiptVerificationStatus(value)
    except ValueError as exc:
        raise UnknownVoteReceiptStatusError(
            f"unknown vote receipt verification status: {value!r}"
        ) from exc


ALLOWED_RECEIPT_TRANSITIONS: frozenset[
    tuple[VoteReceiptVerificationStatus, VoteReceiptVerificationStatus]
] = frozenset(
    {
        (VoteReceiptVerificationStatus.ISSUED, VoteReceiptVerificationStatus.VERIFIED),
        (VoteReceiptVerificationStatus.ISSUED, VoteReceiptVerificationStatus.INVALID),
    }
)


def assert_receipt_transition_allowed(
    current: VoteReceiptVerificationStatus, target: VoteReceiptVerificationStatus
) -> None:
    if (current, target) not in ALLOWED_RECEIPT_TRANSITIONS:
        raise ForbiddenVoteReceiptTransitionError(
            f"vote receipt transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class VoteReceipt:
    """Canon section 15.4 fields exactly.

    A receipt must let the voter verify their ballot was included
    *without* publicly revealing which option they chose (canon
    section 15.4). `receipt_hash` is therefore always constructed from
    the referenced `VoteEnvelope`'s own `integrity_hash`/
    `vote_envelope_id` (see `compute_vote_receipt_hash`) - NEVER from
    `encrypted_or_encoded_choice` directly, even hashed, since that could
    in principle be dictionary-attacked back to a small option set (e.g.
    `single_choice`/`yes_no` ballots have very few possible values). A
    receipt is exactly as identity-free as the envelope it proves
    inclusion for - `FORBIDDEN_FIELD_NAMES` applies here too (see
    `tests/test_domain.py`)."""

    receipt_id: UUID
    ballot_id: UUID
    vote_envelope_reference: UUID
    receipt_hash: str
    issued_at: datetime
    verification_status: VoteReceiptVerificationStatus

    def __post_init__(self) -> None:
        if self.issued_at.tzinfo is None:
            raise ValueError("issued_at must be timezone-aware")
        if not self.receipt_hash:
            raise ValueError("receipt_hash must not be empty")

    def with_status(self, new_status: VoteReceiptVerificationStatus) -> VoteReceipt:
        assert_receipt_transition_allowed(self.verification_status, new_status)
        return replace(self, verification_status=new_status)


def compute_vote_receipt_hash(*, vote_envelope_id: UUID, integrity_hash: str) -> str:
    """`receipt_hash` per canon section 15.4: a hash of the envelope's own
    `vote_envelope_id`/`integrity_hash` only - never
    `encrypted_or_encoded_choice`, so the receipt cannot be reversed (nor
    dictionary-attacked, given the small option sets `BallotMethod`
    allows) to reveal the chosen option."""
    payload = {"vote_envelope_id": vote_envelope_id, "integrity_hash": integrity_hash}
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()
