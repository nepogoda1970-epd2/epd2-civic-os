"""Eligibility Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownEligibilityDecisionValueError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class RuleVersionFrozenError(ValueError):
    """Raised when a caller attempts to re-submit an existing
    `(eligibility_rule_id, rule_version)` with different content - the
    canon section 9.1 "rule freeze" requirement applied to `EligibilityRule`.
    """

    reason_code = "ELIGIBILITY_RULE_VERSION_FROZEN"


class UnknownEligibilityRuleError(ValueError):
    """Raised for a plain lookup miss (no `EligibilityRule` exists for the
    given `(eligibility_rule_id, rule_version)`) - distinct from
    `ELIGIBILITY_NOT_MET`, which describes a real decision outcome against
    a rule that exists (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"
