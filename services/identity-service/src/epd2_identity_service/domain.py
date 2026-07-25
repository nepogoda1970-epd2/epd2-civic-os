"""`IdentityRecord`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 7.3.

Forbidden per canon: voting lists, chosen options, initiative lists,
political preferences, delegations. None of those fields exist here -
enforced structurally by this dataclass's field set, and by
`tests/test_identity_leakage.py` at the repository root.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    ForbiddenVerificationTransitionError,
    UnknownAuthenticationAssuranceLevelError,
    UnknownIdentityAssuranceLevelError,
    UnknownVerificationStatusError,
)


class IdentityAssuranceLevel(StrEnum):
    """Canon 19d.2's exact four-value scale for `IdentityRecord.
    identity_assurance_level` — trust in the identity verification
    itself. Deliberately a *different* Python type from
    `AuthenticationAssuranceLevel` below even though the value set is
    identical, so a caller (and mypy) cannot silently pass one where the
    other is expected — canon 19d.8: "пять раздельных, никогда не
    взаимозаменяемых понятий."""

    NONE = "none"
    LOW = "low"
    SUBSTANTIAL = "substantial"
    HIGH = "high"


class AuthenticationAssuranceLevel(StrEnum):
    """Canon 19d.8's exact four-value scale for `AuthenticationContext.
    authentication_assurance_level` / `AssuranceRequirement.
    required_authentication_assurance_level` — trust in *this session's*
    authentication, never a proxy for identity verification quality."""

    NONE = "none"
    LOW = "low"
    SUBSTANTIAL = "substantial"
    HIGH = "high"


def parse_identity_assurance_level(value: str) -> IdentityAssuranceLevel:
    try:
        return IdentityAssuranceLevel(value)
    except ValueError as exc:
        raise UnknownIdentityAssuranceLevelError(
            f"unknown identity_assurance_level: {value!r}"
        ) from exc


def parse_authentication_assurance_level(value: str) -> AuthenticationAssuranceLevel:
    try:
        return AuthenticationAssuranceLevel(value)
    except ValueError as exc:
        raise UnknownAuthenticationAssuranceLevelError(
            f"unknown authentication_assurance_level: {value!r}"
        ) from exc


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
    """Canon section 7.3's original ten fields, plus canon 19d.2's eight
    additive fields (canon-0.6.0, ADR-026 through ADR-031). The eight new
    fields all default to their "nothing asserted yet" value so every
    pre-existing call site in this repository keeps constructing valid
    records unchanged — canon 19d.2 is explicitly a backward-compatible,
    minor-version addition (canon section 25), never a breaking one.

    `citizenship_status` is always a tuple (never a single value) per
    canon 19d.2: "допускает безгражданство и множественное гражданство,
    никогда не единственное булево значение." `identity_assurance_level`
    is never derived from, and never a substitute for,
    `citizenship_status` (canon 19d.2's "обязательное разделение, без
    исключений").
    """

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
    # --- canon 19d.2 additions (canon-0.6.0) --------------------------
    date_of_birth: date | None = None
    citizenship_status: tuple[str, ...] = ()
    residence_status: Mapping[str, object] | None = None
    identity_assurance_level: IdentityAssuranceLevel = IdentityAssuranceLevel.NONE
    identity_scheme: str | None = None
    attribute_verification_level: str | None = None
    attribute_verified_at: datetime | None = None
    attribute_valid_until: datetime | None = None

    def __post_init__(self) -> None:
        if self.verified_at is not None and self.verified_at.tzinfo is None:
            raise ValueError("verified_at must be timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        if self.attribute_verified_at is not None and self.attribute_verified_at.tzinfo is None:
            raise ValueError("attribute_verified_at must be timezone-aware")
        if self.attribute_valid_until is not None and self.attribute_valid_until.tzinfo is None:
            raise ValueError("attribute_valid_until must be timezone-aware")
        if (
            self.attribute_valid_until is not None
            and self.attribute_verified_at is not None
            and self.attribute_valid_until < self.attribute_verified_at
        ):
            raise ValueError("attribute_valid_until must not precede attribute_verified_at")
        if self.identity_scheme is not None and not self.identity_scheme:
            raise ValueError("identity_scheme must not be an empty string when provided")

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
        `None` keeps the current value unchanged. The eight canon-0.6.0
        fields are always carried over unchanged — this method only ever
        touches verification-lifecycle fields, never identity/attribute
        data (canon 19d.2 is a wholly separate concern from
        `verification_status`).
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
            date_of_birth=self.date_of_birth,
            citizenship_status=self.citizenship_status,
            residence_status=self.residence_status,
            identity_assurance_level=self.identity_assurance_level,
            identity_scheme=self.identity_scheme,
            attribute_verification_level=self.attribute_verification_level,
            attribute_verified_at=self.attribute_verified_at,
            attribute_valid_until=self.attribute_valid_until,
        )

    def with_attributes(
        self,
        *,
        date_of_birth: date | None = None,
        citizenship_status: tuple[str, ...] | None = None,
        residence_status: Mapping[str, object] | None = None,
        identity_assurance_level: IdentityAssuranceLevel | None = None,
        identity_scheme: str | None = None,
        attribute_verification_level: str | None = None,
        attribute_verified_at: datetime | None = None,
        attribute_valid_until: datetime | None = None,
    ) -> IdentityRecord:
        """Record or refresh one or more of canon 19d.2's additive
        fields, leaving every verification-lifecycle field (`verification_
        status`, `verified_at`, `expires_at`, `duplicate_check_status`)
        and the original canon 7.3 fields completely untouched — the
        structural mirror of `with_status` above, for the other side of
        canon 19d.2's field split. Any parameter left `None` keeps the
        current value unchanged."""
        return IdentityRecord(
            identity_record_id=self.identity_record_id,
            account_id=self.account_id,
            verification_provider=self.verification_provider,
            verification_level=self.verification_level,
            verification_status=self.verification_status,
            verified_at=self.verified_at,
            expires_at=self.expires_at,
            country=self.country,
            duplicate_check_status=self.duplicate_check_status,
            provider_reference=self.provider_reference,
            date_of_birth=date_of_birth if date_of_birth is not None else self.date_of_birth,
            citizenship_status=(
                citizenship_status if citizenship_status is not None else self.citizenship_status
            ),
            residence_status=(
                residence_status if residence_status is not None else self.residence_status
            ),
            identity_assurance_level=(
                identity_assurance_level
                if identity_assurance_level is not None
                else self.identity_assurance_level
            ),
            identity_scheme=(
                identity_scheme if identity_scheme is not None else self.identity_scheme
            ),
            attribute_verification_level=(
                attribute_verification_level
                if attribute_verification_level is not None
                else self.attribute_verification_level
            ),
            attribute_verified_at=(
                attribute_verified_at
                if attribute_verified_at is not None
                else self.attribute_verified_at
            ),
            attribute_valid_until=(
                attribute_valid_until
                if attribute_valid_until is not None
                else self.attribute_valid_until
            ),
        )


# ---------------------------------------------------------------------------
# AuthenticationContext (canon 19d.8, canon-0.6.0)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuthenticationContext:
    """Canon 19d.8's `AuthenticationContext` fields exactly. Owned by
    `identity-service`. Distinct from `IdentityRecord.
    identity_assurance_level` (identity verification quality) and from
    `StepUpAuthenticationRequirement` (`eligibility-service`, canon
    19d.8 — the *policy* naming what assurance an action requires); this
    entity is the current, observed state of *this session's*
    authentication, nothing more."""

    authentication_context_id: UUID
    account_id: UUID
    authentication_method: str
    authentication_assurance_level: AuthenticationAssuranceLevel
    session_authenticated_at: datetime
    provider_reference: str
    step_up_completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.authentication_method:
            raise ValueError("authentication_method must not be empty")
        if self.session_authenticated_at.tzinfo is None:
            raise ValueError("session_authenticated_at must be timezone-aware")
        if not self.provider_reference:
            raise ValueError("provider_reference must not be empty")
        if self.step_up_completed_at is not None and self.step_up_completed_at.tzinfo is None:
            raise ValueError("step_up_completed_at must be timezone-aware")

    def with_step_up_completed(self, completed_at: datetime) -> AuthenticationContext:
        if completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")
        return AuthenticationContext(
            authentication_context_id=self.authentication_context_id,
            account_id=self.account_id,
            authentication_method=self.authentication_method,
            authentication_assurance_level=self.authentication_assurance_level,
            session_authenticated_at=self.session_authenticated_at,
            provider_reference=self.provider_reference,
            step_up_completed_at=completed_at,
        )


# =============================================================================
# ADR-027 narrow cross-pack reads: `eligibility-service` and
# `membership-service` are, per that ADR, the only two callers of
# `get_identity_participation_claims`/`check_authentication_step_up_satisfied`
# below (`epd2_identity_service.application`, enforced in
# `tests/repository/test_service_boundaries.py`). Both functions return only
# derived booleans (plus a reason code where false) - never
# `date_of_birth`/`citizenship_status`/`residence_status`/
# `provider_reference`/`session_authenticated_at` themselves (ADR-027's own
# "explicitly prohibited" clause).
# =============================================================================

#: Local order for this module's own two assurance-level enums - a
#: deliberate, small duplicate of `epd2_eligibility_service.domain.
#: _ASSURANCE_ORDER` (that module's own zero-dependency-on-identity-service
#: boundary forbids importing this module's enums; this module owning the
#: enums forbids importing eligibility-service's string constant back).
#: Kept honest by `tests/repository/test_pack07_duplicated_logic_parity.py`.
_ASSURANCE_ORDER: dict[str, int] = {"none": 0, "low": 1, "substantial": 2, "high": 3}


@dataclass(frozen=True, slots=True)
class IdentityParticipationClaims:
    """ADR-027's exact six-boolean return shape for
    `get_identity_participation_claims` - never the raw `IdentityRecord`
    fields that produced them."""

    identity_verified: bool
    identity_assurance_requirement_met: bool
    age_requirement_met: bool
    citizenship_requirement_met: bool
    residence_requirement_met: bool
    territorial_scope_requirement_met: bool
    reason_codes: tuple[str, ...]


def _rule_matches(actual: Mapping[str, object] | None, rule: Mapping[str, object] | None) -> bool:
    """A rule of `None` imposes no requirement (always satisfied). A
    non-`None` rule requires every one of its key/value pairs to be
    present, with an equal value, in `actual` - fail-closed to `False`
    when `actual` is `None` but a rule is set."""
    if rule is None:
        return True
    if actual is None:
        return False
    return all(actual.get(key) == value for key, value in rule.items())


def evaluate_identity_participation_claims(
    record: IdentityRecord | None,
    *,
    required_identity_assurance_level: str,
    minimum_age: int | None,
    eligible_citizenship_set: tuple[str, ...],
    residence_rule: Mapping[str, object] | None,
    territorial_scope_rule: Mapping[str, object] | None,
    evaluated_at: datetime,
) -> IdentityParticipationClaims:
    """Pure, side-effect-free evaluation backing
    `application.get_identity_participation_claims` (ADR-027). Fail-closed
    throughout: a missing or unverified record yields every claim `False`,
    never a default `True`."""
    if record is None or record.verification_status is not VerificationStatus.VERIFIED:
        return IdentityParticipationClaims(
            identity_verified=False,
            identity_assurance_requirement_met=False,
            age_requirement_met=False,
            citizenship_requirement_met=False,
            residence_requirement_met=False,
            territorial_scope_requirement_met=False,
            reason_codes=("IDENTITY_NOT_VERIFIED",),
        )

    reason_codes: list[str] = []

    assurance_met = (
        _ASSURANCE_ORDER[record.identity_assurance_level.value]
        >= _ASSURANCE_ORDER[required_identity_assurance_level]
    )
    if not assurance_met:
        reason_codes.append("IDENTITY_ASSURANCE_REQUIREMENT_NOT_MET")

    if minimum_age is None:
        age_met = True
    elif record.date_of_birth is None:
        age_met = False
        reason_codes.append("IDENTITY_AGE_REQUIREMENT_NOT_MET")
    else:
        years = (
            evaluated_at.date().year
            - record.date_of_birth.year
            - (
                (evaluated_at.date().month, evaluated_at.date().day)
                < (record.date_of_birth.month, record.date_of_birth.day)
            )
        )
        age_met = years >= minimum_age
        if not age_met:
            reason_codes.append("IDENTITY_AGE_REQUIREMENT_NOT_MET")

    if not eligible_citizenship_set:
        citizenship_met = True
    else:
        citizenship_met = bool(set(record.citizenship_status) & set(eligible_citizenship_set))
        if not citizenship_met:
            reason_codes.append("IDENTITY_CITIZENSHIP_REQUIREMENT_NOT_MET")

    residence_met = _rule_matches(record.residence_status, residence_rule)
    if not residence_met:
        reason_codes.append("IDENTITY_RESIDENCE_REQUIREMENT_NOT_MET")

    territorial_met = _rule_matches(record.residence_status, territorial_scope_rule)
    if not territorial_met:
        reason_codes.append("IDENTITY_TERRITORIAL_SCOPE_REQUIREMENT_NOT_MET")

    return IdentityParticipationClaims(
        identity_verified=True,
        identity_assurance_requirement_met=assurance_met,
        age_requirement_met=age_met,
        citizenship_requirement_met=citizenship_met,
        residence_requirement_met=residence_met,
        territorial_scope_requirement_met=territorial_met,
        reason_codes=tuple(reason_codes),
    )


@dataclass(frozen=True, slots=True)
class StepUpSatisfactionResult:
    """ADR-030 item 7's exact return shape for
    `check_authentication_step_up_satisfied` - a single boolean plus,
    where unmet, the resolved `StepUpAuthenticationRequirement`'s own
    `reauthentication_reason` (never a generic failure, per ADR-030 item
    7's "reauthentication_reason surfacing" rule)."""

    satisfied: bool
    reauthentication_reason: str | None


def evaluate_step_up_satisfaction(
    *,
    context: AuthenticationContext | None,
    identity_assurance_level: IdentityAssuranceLevel | None,
    attribute_verified_at: datetime | None,
    required_authentication_assurance_level: str,
    required_identity_assurance_level: str,
    fresh_authentication_required: bool,
    maximum_authentication_age: timedelta | None,
    required_attribute_freshness: timedelta | None,
    reauthentication_reason: str,
    evaluated_at: datetime,
) -> StepUpSatisfactionResult:
    """Pure, side-effect-free evaluation backing `application.
    check_authentication_step_up_satisfied` (ADR-030 item 7). Every one of
    assurance, identity assurance, session freshness (where applicable),
    and attribute freshness (where applicable) must hold **simultaneously**
    - any single failed condition fails the whole requirement, and a
    missing/expired `AuthenticationContext` is unconditionally
    fail-closed, never a default allow. Deliberately mirrors
    `epd2_eligibility_service.domain.check_step_up_requirement`'s own
    four-condition structure - a documented duplicate, not an import (see
    that function's own docstring), kept honest by
    `tests/repository/test_pack07_duplicated_logic_parity.py`."""
    if context is None or identity_assurance_level is None:
        return StepUpSatisfactionResult(
            satisfied=False, reauthentication_reason=reauthentication_reason
        )
    if (
        _ASSURANCE_ORDER[context.authentication_assurance_level.value]
        < _ASSURANCE_ORDER[required_authentication_assurance_level]
    ):
        return StepUpSatisfactionResult(
            satisfied=False, reauthentication_reason=reauthentication_reason
        )
    if (
        _ASSURANCE_ORDER[identity_assurance_level.value]
        < _ASSURANCE_ORDER[required_identity_assurance_level]
    ):
        return StepUpSatisfactionResult(
            satisfied=False, reauthentication_reason=reauthentication_reason
        )
    if fresh_authentication_required and maximum_authentication_age is not None:
        age = evaluated_at - context.session_authenticated_at
        if age > maximum_authentication_age:
            return StepUpSatisfactionResult(
                satisfied=False, reauthentication_reason=reauthentication_reason
            )
    if required_attribute_freshness is not None:
        if attribute_verified_at is None:
            return StepUpSatisfactionResult(
                satisfied=False, reauthentication_reason=reauthentication_reason
            )
        if evaluated_at - attribute_verified_at > required_attribute_freshness:
            return StepUpSatisfactionResult(
                satisfied=False, reauthentication_reason=reauthentication_reason
            )
    return StepUpSatisfactionResult(satisfied=True, reauthentication_reason=None)
