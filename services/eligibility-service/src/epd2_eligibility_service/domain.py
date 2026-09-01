"""`EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 9.

This module has zero import dependency on `epd2_identity_service` - see
README.md for why that boundary matters.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import replace as dataclasses_replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_eligibility_service.exceptions import (
    AssemblyDecisionDivergenceExplanationRequiredError,
    CriticalPolicyActivationNotAuthorizedError,
    ForbiddenAssemblyDecisionTransitionError,
    ForbiddenCriticalPolicyTransitionError,
    StepUpAuthenticationNotSatisfiedError,
    UnknownAssemblyDecisionStatusError,
    UnknownAssuranceLevelError,
    UnknownCriticalPolicyStatusError,
    UnknownDigitalDecisionStatusError,
    UnknownEligibilityDecisionValueError,
)


class EligibilityDecisionValue(StrEnum):
    """Canon section 9.2's exact `decision` value list."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING = "pending"
    EXPIRED = "expired"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


def parse_decision_value(value: str) -> EligibilityDecisionValue:
    try:
        return EligibilityDecisionValue(value)
    except ValueError as exc:
        raise UnknownEligibilityDecisionValueError(f"unknown decision value: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class EligibilityRule:
    """Canon section 9.1 fields exactly. Immutable: a "change" is always a
    new object with an incremented `rule_version`, never a mutation.
    """

    eligibility_rule_id: UUID
    rule_version: int
    scope_type: str
    scope_id: UUID
    required_membership_status: str
    required_verification_level: str
    region_constraint: str | None
    minimum_membership_age: int | None
    exclusion_conditions: tuple[str, ...]
    valid_from: datetime
    valid_until: datetime | None

    def __post_init__(self) -> None:
        if self.rule_version < 1:
            raise ValueError("rule_version must be >= 1")
        if self.valid_from.tzinfo is None:
            raise ValueError("valid_from must be timezone-aware")
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("valid_until must be timezone-aware")


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Canon section 9.2 fields, plus pack section 7.2's additive
    `correlation_id`/`evaluator_version`/`evaluated_claims` extension
    fields (ADR-002: additive, not conflicting with canon).
    """

    eligibility_decision_id: UUID
    subject_reference: UUID
    process_id: UUID
    eligibility_rule_id: UUID
    rule_version: int
    decision: EligibilityDecisionValue
    reason_codes: tuple[str, ...]
    evaluated_at: datetime
    expires_at: datetime | None
    correlation_id: UUID
    evaluator_version: str
    evaluated_claims: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.evaluated_at.tzinfo is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class EligibilitySnapshot:
    """Canon section 9.3: immutable, has a hash, records the rule
    version, and supports independent verification of the admitted count
    without exposing any individual identity.
    """

    eligibility_snapshot_id: UUID
    eligibility_rule_id: UUID
    rule_version: int
    created_at: datetime
    eligible_decision_ids: tuple[UUID, ...]
    eligible_count: int
    digest: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.eligible_count != len(self.eligible_decision_ids):
            raise ValueError("eligible_count must equal len(eligible_decision_ids)")


def compute_snapshot_digest(
    *,
    eligibility_rule_id: UUID,
    rule_version: int,
    created_at: datetime,
    eligible_decision_ids: tuple[UUID, ...],
) -> str:
    """Deterministic digest per canon section 9.3 ("имеет hash"). Sorting
    `eligible_decision_ids` first makes the digest independent of
    collection order, so two snapshots built from the same logical set of
    decisions always match.
    """
    payload = {
        "eligibility_rule_id": eligibility_rule_id,
        "rule_version": rule_version,
        "created_at": created_at,
        "eligible_decision_ids": sorted(eligible_decision_ids, key=str),
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


# =============================================================================
# PACK-07 additions (canon 19d.4-19d.14, canon-0.6.0, ADR-026 through
# ADR-031). `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
# `StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`
# are all owned by `eligibility-service` (canon section 22). This module's
# zero-import-dependency-on-`epd2_identity_service` boundary (module
# docstring above) still holds: assurance-level strings below are
# re-validated locally (`_ASSURANCE_LEVELS`), never imported from
# `epd2_identity_service.domain.IdentityAssuranceLevel`/
# `AuthenticationAssuranceLevel`.
# =============================================================================

#: Local, dependency-free copy of identity-service's four-value assurance
#: scale (canon 19d.2/19d.8) - deliberately duplicated, never imported,
#: per this module's zero-dependency-on-identity-service boundary.
_ASSURANCE_LEVELS = frozenset({"none", "low", "substantial", "high"})


def _validate_assurance_level(value: str, *, field_name: str) -> None:
    if value not in _ASSURANCE_LEVELS:
        raise UnknownAssuranceLevelError(f"unknown {field_name}: {value!r}")


class CriticalPolicyStatus(StrEnum):
    """Canon 19d.7's shared status list for every critical policy this
    service owns (`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
    `StepUpAuthenticationRequirement`) - the same three-value shape
    `GovernancePolicyStatus` already established for `governance-service`."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


CRITICAL_POLICY_ALLOWED_TRANSITIONS: frozenset[
    tuple[CriticalPolicyStatus, CriticalPolicyStatus]
] = frozenset(
    {
        (CriticalPolicyStatus.DRAFT, CriticalPolicyStatus.ACTIVE),
        (CriticalPolicyStatus.ACTIVE, CriticalPolicyStatus.SUPERSEDED),
    }
)


def parse_critical_policy_status(value: str) -> CriticalPolicyStatus:
    try:
        return CriticalPolicyStatus(value)
    except ValueError as exc:
        raise UnknownCriticalPolicyStatusError(
            f"unknown critical policy status: {value!r}"
        ) from exc


def assert_critical_policy_transition_allowed(
    current: CriticalPolicyStatus, target: CriticalPolicyStatus
) -> None:
    if (current, target) not in CRITICAL_POLICY_ALLOWED_TRANSITIONS:
        raise ForbiddenCriticalPolicyTransitionError(
            f"critical policy transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class CriticalPolicyActivationGate:
    """The four independent gates canon 19d.7 requires, all at once, for
    any critical policy's `draft -> active` transition. `decision_authorized`
    and `multi_person_approval_met` come from `governance-service`'s
    `verify_decision_authorizes_policy_activation` (gates 1-2); the two
    reference fields are this policy's own, already-set field values
    (gates 3-4) - this dataclass never fetches them itself."""

    decision_authorized: bool
    multi_person_approval_met: bool
    signed_policy_digest_reference: str | None
    transparency_log_commitment_reference: str | None


def assert_critical_policy_activation_gate(gate: CriticalPolicyActivationGate) -> None:
    """Fail-closed: every one of the four gates must independently hold.
    Canon 19d.7: 'отсутствие любого одного - fail-closed отказ активации'.

    This exact four-gate check is independently re-implemented (never
    imported) in `epd2_membership_service.domain` for
    `PartyMembershipEligibilityPolicy`'s own activation - `epd2_core`'s
    own charter forbids holding domain business rules
    (`packages/python/epd2-core/README.md`, "Границы"), so a shared
    Python type is not an option; the two copies are kept honest by
    `tests/repository/test_pack07_duplicated_logic_parity.py`, which
    asserts both functions accept/reject the exact same four-gate truth
    table.
    """
    if not gate.decision_authorized:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires an authorized GovernanceDecision"
        )
    if not gate.multi_person_approval_met:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires multi_person_approval_met"
        )
    if not gate.signed_policy_digest_reference:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires signed_policy_digest_reference"
        )
    if not gate.transparency_log_commitment_reference:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires transparency_log_commitment_reference"
        )


class DecisionEffect(StrEnum):
    """Canon 19d.5/19d.12's exact `decision_effect` value list."""

    ADVISORY = "advisory"
    POLITICALLY_BINDING = "politically_binding"
    INTERNALLY_BINDING = "internally_binding"
    LEGALLY_FINAL = "legally_final"
    REQUIRES_FORMAL_CONFIRMATION = "requires_formal_confirmation"


@dataclass(frozen=True, slots=True)
class AgeThreshold:
    """Embedded value object for `ParticipantEligibilityPolicy.age_thresholds`
    (canon 19d.4)."""

    action_code: str
    minimum_age: int | None
    maximum_age: int | None

    def __post_init__(self) -> None:
        if not self.action_code:
            raise ValueError("action_code must not be empty")
        if self.minimum_age is not None and self.minimum_age < 0:
            raise ValueError("minimum_age must not be negative")
        if self.maximum_age is not None and self.maximum_age < 0:
            raise ValueError("maximum_age must not be negative")
        if (
            self.minimum_age is not None
            and self.maximum_age is not None
            and self.minimum_age > self.maximum_age
        ):
            raise ValueError("minimum_age must not exceed maximum_age")


@dataclass(frozen=True, slots=True)
class AssuranceRequirement:
    """Embedded value object (canon 19d.8) - `required_attribute_freshness`
    is the maximum age an attribute verification may have and still
    count as fresh; `None` means no freshness requirement."""

    required_identity_assurance_level: str
    required_authentication_assurance_level: str
    required_attribute_freshness: timedelta | None = None

    def __post_init__(self) -> None:
        _validate_assurance_level(
            self.required_identity_assurance_level, field_name="required_identity_assurance_level"
        )
        _validate_assurance_level(
            self.required_authentication_assurance_level,
            field_name="required_authentication_assurance_level",
        )
        if (
            self.required_attribute_freshness is not None
            and self.required_attribute_freshness < timedelta(0)
        ):
            raise ValueError("required_attribute_freshness must not be negative")


@dataclass(frozen=True, slots=True)
class ParticipantEligibilityPolicy:
    """Canon 19d.4 fields exactly. A versioned, activatable critical
    policy of general platform participation eligibility - structurally
    separate from `PartyMembershipEligibilityPolicy` (`membership-service`,
    canon 19d.1/19d.6): neither is a special case of the other."""

    policy_id: UUID
    policy_version: int
    status: CriticalPolicyStatus
    scope_type: str | None
    scope_id: UUID | None
    effective_from: datetime | None
    effective_until: datetime | None
    adopted_by_decision_id: UUID
    age_thresholds: tuple[AgeThreshold, ...] = ()
    citizenship_conditions: tuple[Mapping[str, object], ...] = ()
    residence_conditions: tuple[Mapping[str, object], ...] = ()
    exemptions: tuple[Mapping[str, object], ...] = ()
    transitional_rules: tuple[Mapping[str, object], ...] = ()
    supersedes_policy_id: UUID | None = None
    signed_policy_digest_reference: str | None = None
    transparency_log_commitment_reference: str | None = None

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if self.status is CriticalPolicyStatus.ACTIVE:
            if not self.signed_policy_digest_reference:
                raise ValueError("signed_policy_digest_reference is required when status=active")
            if not self.transparency_log_commitment_reference:
                raise ValueError(
                    "transparency_log_commitment_reference is required when status=active"
                )
        if self.effective_from is not None and self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.effective_until is not None and self.effective_until.tzinfo is None:
            raise ValueError("effective_until must be timezone-aware")

    def with_status(self, new_status: CriticalPolicyStatus) -> ParticipantEligibilityPolicy:
        assert_critical_policy_transition_allowed(self.status, new_status)
        return _replace(self, status=new_status)


def _replace(
    policy: ParticipantEligibilityPolicy, *, status: CriticalPolicyStatus
) -> ParticipantEligibilityPolicy:
    return ParticipantEligibilityPolicy(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        status=status,
        scope_type=policy.scope_type,
        scope_id=policy.scope_id,
        effective_from=policy.effective_from,
        effective_until=policy.effective_until,
        adopted_by_decision_id=policy.adopted_by_decision_id,
        age_thresholds=policy.age_thresholds,
        citizenship_conditions=policy.citizenship_conditions,
        residence_conditions=policy.residence_conditions,
        exemptions=policy.exemptions,
        transitional_rules=policy.transitional_rules,
        supersedes_policy_id=policy.supersedes_policy_id,
        signed_policy_digest_reference=policy.signed_policy_digest_reference,
        transparency_log_commitment_reference=policy.transparency_log_commitment_reference,
    )


#: Canon 19d.5's own illustrative, non-exhaustive minimum list of nine
#: `process_type` categories - `ProcessEligibilityPolicy.process_type`
#: itself stays an open `str` (canon: "открытая строка"), this tuple is
#: documentation/test fixture material only, never an enforced enum.
PROCESS_TYPE_MINIMUM_CATEGORIES: tuple[str, ...] = (
    "bundestag_election",
    "european_parliament_election_de",
    "land_election",
    "municipal_district_election",
    "epd_public_consultation",
    "epd_participant_poll",
    "epd_member_vote",
    "epd_party_office_election",
    "epd_public_candidate_nomination",
)


@dataclass(frozen=True, slots=True)
class ProcessEligibilityPolicy:
    """Canon 19d.5 fields exactly, plus 19d.5's own additional
    legal-effect/formal-confirmation fields (which canon co-locates in
    the same section). Parametrizes eligibility for one concrete
    process - never a permanent property of a person (canon 19d.5's own
    framing)."""

    policy_id: UUID
    policy_version: int
    status: CriticalPolicyStatus
    process_type: str
    jurisdiction: str
    scope_type: str | None
    scope_id: UUID | None
    adopted_by: UUID
    eligible_citizenship_set: tuple[str, ...] = ()
    citizenship_rule_reference: str | None = None
    residence_rule: Mapping[str, object] | None = None
    habitual_residence_rule: Mapping[str, object] | None = None
    minimum_age: int | None = None
    active_electoral_eligibility_rule: Mapping[str, object] | None = None
    passive_electoral_eligibility_rule: Mapping[str, object] | None = None
    party_internal_voting_rule: Mapping[str, object] | None = None
    party_office_candidacy_rule: Mapping[str, object] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    legal_basis: str | None = None
    supersedes_policy_id: UUID | None = None
    signed_policy_digest_reference: str | None = None
    transparency_log_commitment_reference: str | None = None
    # --- legal-effect / formal-confirmation fields (canon 19d.5/19d.12) --
    decision_effect: DecisionEffect = DecisionEffect.ADVISORY
    formal_confirmation_required: bool = False
    formal_confirmation_authority: str | None = None
    secret_ballot_required: bool = False
    permitted_participation_mode: tuple[str, ...] = ()
    required_assurance_level: AssuranceRequirement | None = None
    accessibility_profile: str | None = None

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if not self.process_type:
            raise ValueError("process_type must not be empty")
        if not self.jurisdiction:
            raise ValueError("jurisdiction must not be empty")
        if self.minimum_age is not None and self.minimum_age < 0:
            raise ValueError("minimum_age must not be negative")
        if self.status is CriticalPolicyStatus.ACTIVE:
            if not self.signed_policy_digest_reference:
                raise ValueError("signed_policy_digest_reference is required when status=active")
            if not self.transparency_log_commitment_reference:
                raise ValueError(
                    "transparency_log_commitment_reference is required when status=active"
                )
        if self.formal_confirmation_required and not self.formal_confirmation_authority:
            raise ValueError(
                "formal_confirmation_authority is required when formal_confirmation_required"
            )
        if (
            self.decision_effect is DecisionEffect.REQUIRES_FORMAL_CONFIRMATION
            and not self.formal_confirmation_required
        ):
            raise ValueError(
                "formal_confirmation_required must be true when "
                "decision_effect=requires_formal_confirmation"
            )

    def with_status(self, new_status: CriticalPolicyStatus) -> ProcessEligibilityPolicy:
        assert_critical_policy_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)


@dataclass(frozen=True, slots=True)
class StepUpAuthenticationRequirement:
    """Canon 19d.8 fields exactly - a critical policy (canon 19d.7)
    naming what assurance a given `action_code` requires."""

    requirement_id: UUID
    requirement_version: int
    status: CriticalPolicyStatus
    action_code: str
    required_authentication_context: str
    assurance_requirement: AssuranceRequirement
    fresh_authentication_required: bool
    reauthentication_reason: str
    maximum_authentication_age: timedelta | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    supersedes_requirement_id: UUID | None = None
    signed_policy_digest_reference: str | None = None
    transparency_log_commitment_reference: str | None = None

    def __post_init__(self) -> None:
        if self.requirement_version < 1:
            raise ValueError("requirement_version must be >= 1")
        if not self.action_code:
            raise ValueError("action_code must not be empty")
        if not self.reauthentication_reason:
            raise ValueError("reauthentication_reason must not be empty")
        if self.status is CriticalPolicyStatus.ACTIVE:
            if not self.signed_policy_digest_reference:
                raise ValueError("signed_policy_digest_reference is required when status=active")
            if not self.transparency_log_commitment_reference:
                raise ValueError(
                    "transparency_log_commitment_reference is required when status=active"
                )

    def with_status(self, new_status: CriticalPolicyStatus) -> StepUpAuthenticationRequirement:
        assert_critical_policy_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)


@dataclass(frozen=True, slots=True)
class ObservedAuthenticationState:
    """The narrow, caller-supplied snapshot of an `AuthenticationContext`
    (identity-service, canon 19d.8) `check_step_up_requirement` below
    evaluates against. This module never imports `epd2_identity_service`
    - a caller in a real deployment fetches the live
    `AuthenticationContext` itself and translates it into this shape."""

    identity_assurance_level: str
    authentication_assurance_level: str
    session_authenticated_at: datetime | None
    attribute_verified_at: datetime | None

    def __post_init__(self) -> None:
        _validate_assurance_level(
            self.identity_assurance_level, field_name="identity_assurance_level"
        )
        _validate_assurance_level(
            self.authentication_assurance_level, field_name="authentication_assurance_level"
        )


_ASSURANCE_ORDER: dict[str, int] = {"none": 0, "low": 1, "substantial": 2, "high": 3}


def check_step_up_requirement(
    requirement: StepUpAuthenticationRequirement,
    observed: ObservedAuthenticationState | None,
    *,
    evaluated_at: datetime,
) -> None:
    """Canon 19d.8's fail-closed evaluation: every one of assurance,
    identity assurance, session freshness (where applicable), and
    attribute freshness (where applicable) must hold **simultaneously**.
    Raises `StepUpAuthenticationNotSatisfiedError` on any failure,
    including a missing `observed` state - never a default allow.
    """
    if observed is None:
        raise StepUpAuthenticationNotSatisfiedError(
            "no AuthenticationContext available for step-up evaluation"
        )
    req = requirement.assurance_requirement
    if (
        _ASSURANCE_ORDER[observed.authentication_assurance_level]
        < _ASSURANCE_ORDER[req.required_authentication_assurance_level]
    ):
        raise StepUpAuthenticationNotSatisfiedError(
            "authentication_assurance_level below required threshold"
        )
    if (
        _ASSURANCE_ORDER[observed.identity_assurance_level]
        < _ASSURANCE_ORDER[req.required_identity_assurance_level]
    ):
        raise StepUpAuthenticationNotSatisfiedError(
            "identity_assurance_level below required threshold"
        )
    if requirement.fresh_authentication_required:
        if observed.session_authenticated_at is None:
            raise StepUpAuthenticationNotSatisfiedError("no authenticated session on record")
        if requirement.maximum_authentication_age is not None:
            age = evaluated_at - observed.session_authenticated_at
            if age > requirement.maximum_authentication_age:
                raise StepUpAuthenticationNotSatisfiedError("authenticated session is too old")
    if req.required_attribute_freshness is not None:
        if observed.attribute_verified_at is None:
            raise StepUpAuthenticationNotSatisfiedError("no attribute verification on record")
        if evaluated_at - observed.attribute_verified_at > req.required_attribute_freshness:
            raise StepUpAuthenticationNotSatisfiedError("attribute verification is stale")


# ---------------------------------------------------------------------------
# Four separated electoral-eligibility claims (canon 19d.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProcessEligibilityClaims:
    """Canon 19d.3's four independently-computed booleans. There is, and
    never will be, a fifth generic `electoral_eligibility_met` field on
    this or any type in this repository."""

    active_electoral_eligibility_met: bool
    active_electoral_eligibility_reason_codes: tuple[str, ...]
    passive_electoral_eligibility_met: bool
    passive_electoral_eligibility_reason_codes: tuple[str, ...]
    party_internal_voting_eligibility_met: bool
    party_internal_voting_eligibility_reason_codes: tuple[str, ...]
    party_office_candidacy_eligibility_met: bool
    party_office_candidacy_eligibility_reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IdentityLayerClaims:
    """The narrow, caller-supplied set of identity-layer facts
    `evaluate_process_eligibility_claims` needs - never a live
    `IdentityRecord` (this module's zero-dependency-on-identity-service
    boundary). A real caller fetches the record from `identity-service`
    and translates it into this shape."""

    age: int
    citizenship_status: tuple[str, ...]
    residence_territorial_connection: str | None


@dataclass(frozen=True, slots=True)
class MembershipLayerClaims:
    """The narrow set of membership-derived claims
    `membership-service.get_membership_derived_claims` returns (canon
    19d.1/19d.3) - `membership-service` never computes an electoral
    claim itself; this is the only membership-related input this
    module's evaluation function accepts."""

    required_membership_status_met: bool
    membership_duration_requirement_met: bool


def evaluate_process_eligibility_claims(
    policy: ProcessEligibilityPolicy,
    *,
    identity: IdentityLayerClaims,
    membership: MembershipLayerClaims | None,
) -> ProcessEligibilityClaims:
    """Canon 19d.3's evaluation, pure and side-effect-free. `membership`
    is `None` for process types with no party dimension at all (the two
    party-related claims are then always `False`, never silently
    treated as "met").
    """
    reasons_active: list[str] = []
    reasons_passive: list[str] = []
    if policy.minimum_age is not None and identity.age < policy.minimum_age:
        reasons_active.append("ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET")
        reasons_passive.append("PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET")
    if policy.eligible_citizenship_set and not (
        set(identity.citizenship_status) & set(policy.eligible_citizenship_set)
    ):
        if "ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET" not in reasons_active:
            reasons_active.append("ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET")
        if "PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET" not in reasons_passive:
            reasons_passive.append("PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET")

    reasons_party_internal: list[str] = []
    reasons_party_office: list[str] = []
    if policy.party_internal_voting_rule is None:
        party_internal_met = False
        reasons_party_internal.append("PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET")
    else:
        party_internal_met = membership is not None and membership.required_membership_status_met
        if not party_internal_met:
            reasons_party_internal.append("PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET")

    if policy.party_office_candidacy_rule is None:
        party_office_met = False
        reasons_party_office.append("PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET")
    else:
        party_office_met = (
            membership is not None
            and membership.required_membership_status_met
            and membership.membership_duration_requirement_met
        )
        if not party_office_met:
            reasons_party_office.append("PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET")

    return ProcessEligibilityClaims(
        active_electoral_eligibility_met=not reasons_active,
        active_electoral_eligibility_reason_codes=tuple(reasons_active),
        passive_electoral_eligibility_met=not reasons_passive,
        passive_electoral_eligibility_reason_codes=tuple(reasons_passive),
        party_internal_voting_eligibility_met=party_internal_met,
        party_internal_voting_eligibility_reason_codes=tuple(reasons_party_internal),
        party_office_candidacy_eligibility_met=party_office_met,
        party_office_candidacy_eligibility_reason_codes=tuple(reasons_party_office),
    )


# ---------------------------------------------------------------------------
# Atomic capability check / scoped capability token (canon 19d.14)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AtomicCapabilityResult:
    """Canon 19d.14's atomic capability check result - one boolean (or a
    small closed set of booleans) for exactly one authorization question
    about exactly one action, never the underlying claims themselves."""

    authorized: bool
    reason_code: str | None


def check_atomic_capability(*, claim_met: bool, denial_reason_code: str) -> AtomicCapabilityResult:
    """The generic shape of every atomic capability check in this
    module: wraps a single already-computed boolean claim (e.g. one
    field of `ProcessEligibilityClaims`) into the narrow
    `AtomicCapabilityResult` shape canon 19d.14 requires, never exposing
    any other claim or the policy that produced it."""
    if claim_met:
        return AtomicCapabilityResult(authorized=True, reason_code=None)
    return AtomicCapabilityResult(authorized=False, reason_code=denial_reason_code)


# ---------------------------------------------------------------------------
# DigitalDecision / AssemblyDecision - formal confirmation (canon 19d.12)
# ---------------------------------------------------------------------------


class DigitalDecisionStatus(StrEnum):
    FINAL = "final"
    FORMAL_CONFIRMATION_REQUIRED = "formal_confirmation_required"


def parse_digital_decision_status(value: str) -> DigitalDecisionStatus:
    try:
        return DigitalDecisionStatus(value)
    except ValueError as exc:
        raise UnknownDigitalDecisionStatusError(
            f"unknown digital decision status: {value!r}"
        ) from exc


@dataclass(frozen=True, slots=True)
class DigitalDecision:
    """Canon 19d.12 fields exactly. `status` is set once, at
    construction, from the applicable `ProcessEligibilityPolicy.
    decision_effect`/`formal_confirmation_required` - never transitioned
    afterward by this class itself (a `formal_confirmation_required`
    `DigitalDecision` is immutable; only its associated `AssemblyDecision`
    progresses)."""

    digital_decision_id: UUID
    process_reference: Mapping[str, object]
    digital_result: str
    decision_effect: DecisionEffect
    formal_confirmation_required: bool
    status: DigitalDecisionStatus
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.digital_result:
            raise ValueError("digital_result must not be empty")
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")
        expected_status = (
            DigitalDecisionStatus.FORMAL_CONFIRMATION_REQUIRED
            if self.formal_confirmation_required
            else DigitalDecisionStatus.FINAL
        )
        if self.status is not expected_status:
            raise ValueError(
                f"status must be {expected_status.value!r} when "
                f"formal_confirmation_required={self.formal_confirmation_required!r}"
            )


class AssemblyDecisionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    RETURNED_FOR_REVISION = "returned_for_revision"


ASSEMBLY_DECISION_ALLOWED_TRANSITIONS: frozenset[
    tuple[AssemblyDecisionStatus, AssemblyDecisionStatus]
] = frozenset(
    {
        (AssemblyDecisionStatus.PENDING, AssemblyDecisionStatus.CONFIRMED),
        (AssemblyDecisionStatus.PENDING, AssemblyDecisionStatus.REJECTED),
        (AssemblyDecisionStatus.PENDING, AssemblyDecisionStatus.RETURNED_FOR_REVISION),
    }
)


def parse_assembly_decision_status(value: str) -> AssemblyDecisionStatus:
    try:
        return AssemblyDecisionStatus(value)
    except ValueError as exc:
        raise UnknownAssemblyDecisionStatusError(
            f"unknown assembly decision status: {value!r}"
        ) from exc


def assert_assembly_decision_transition_allowed(
    current: AssemblyDecisionStatus, target: AssemblyDecisionStatus
) -> None:
    if (current, target) not in ASSEMBLY_DECISION_ALLOWED_TRANSITIONS:
        raise ForbiddenAssemblyDecisionTransitionError(
            f"assembly decision transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class AssemblyDecision:
    """Canon 19d.12 fields exactly. Created only when a `DigitalDecision`
    has `status=formal_confirmation_required`. An expired
    `confirmation_deadline` never auto-transitions this record - canon
    19d.12/INV-10: 'молчание никогда не считается одобрением'."""

    assembly_decision_id: UUID
    digital_decision_id: UUID
    confirming_authority: str
    legal_basis: str
    confirmation_deadline: datetime
    protocol_or_evidence_reference: str
    status: AssemblyDecisionStatus
    final_legal_decision: str | None = None
    divergence_explanation: str | None = None
    decided_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.confirming_authority:
            raise ValueError("confirming_authority must not be empty")
        if not self.legal_basis:
            raise ValueError("legal_basis must not be empty")
        if self.confirmation_deadline.tzinfo is None:
            raise ValueError("confirmation_deadline must be timezone-aware")
        if not self.protocol_or_evidence_reference:
            raise ValueError("protocol_or_evidence_reference must not be empty")
        if (self.status is AssemblyDecisionStatus.PENDING) != (self.decided_at is None):
            raise ValueError("decided_at must be set if and only if status is not 'pending'")
        if self.decided_at is not None and self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")

    def with_decision(
        self,
        *,
        new_status: AssemblyDecisionStatus,
        final_legal_decision: str,
        digital_result: str,
        divergence_explanation: str | None,
        decided_at: datetime,
    ) -> AssemblyDecision:
        """Canon 19d.12: a `final_legal_decision` diverging from the
        originating `DigitalDecision.digital_result` requires a filled
        `divergence_explanation`, enforced fail-closed here."""
        assert_assembly_decision_transition_allowed(self.status, new_status)
        if final_legal_decision != digital_result and not divergence_explanation:
            raise AssemblyDecisionDivergenceExplanationRequiredError(
                "divergence_explanation is required when final_legal_decision "
                "differs from digital_result"
            )
        return AssemblyDecision(
            assembly_decision_id=self.assembly_decision_id,
            digital_decision_id=self.digital_decision_id,
            confirming_authority=self.confirming_authority,
            legal_basis=self.legal_basis,
            confirmation_deadline=self.confirmation_deadline,
            protocol_or_evidence_reference=self.protocol_or_evidence_reference,
            status=new_status,
            final_legal_decision=final_legal_decision,
            divergence_explanation=divergence_explanation,
            decided_at=decided_at,
        )
