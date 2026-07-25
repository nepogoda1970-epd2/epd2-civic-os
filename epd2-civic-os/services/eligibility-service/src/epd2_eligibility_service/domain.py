"""`EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`, per
`docs/canonical/TZ-00-domain-event-canon.md`, section 9.

This module has zero import dependency on `epd2_identity_service` - see
README.md for why that boundary matters.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_eligibility_service.exceptions import UnknownEligibilityDecisionValueError


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
