"""Storage protocols and in-memory reference adapters for Eligibility
Service's three owned entities.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_eligibility_service.domain import (
    EligibilityDecision,
    EligibilityRule,
    EligibilitySnapshot,
)
from epd2_eligibility_service.exceptions import RuleVersionFrozenError


class EligibilityRuleStore(Protocol):
    def save(self, rule: EligibilityRule) -> EligibilityRule:
        """Save a new rule version. If `(eligibility_rule_id, rule_version)`
        already exists with identical content, returns the existing
        record (idempotent). If it exists with different content, raises
        `RuleVersionFrozenError` - versions are immutable once created
        (canon section 9.1, "rule freeze")."""
        ...

    def get(self, eligibility_rule_id: UUID, rule_version: int) -> EligibilityRule | None: ...

    def latest_version(self, eligibility_rule_id: UUID) -> EligibilityRule | None: ...


class EligibilityDecisionStore(Protocol):
    def save(self, decision: EligibilityDecision) -> None: ...

    def get(self, eligibility_decision_id: UUID) -> EligibilityDecision | None: ...


class EligibilitySnapshotStore(Protocol):
    def save(self, snapshot: EligibilitySnapshot) -> None: ...

    def get(self, eligibility_snapshot_id: UUID) -> EligibilitySnapshot | None: ...


class InMemoryEligibilityRuleStore:
    def __init__(self) -> None:
        self._rules: dict[tuple[UUID, int], EligibilityRule] = {}

    def save(self, rule: EligibilityRule) -> EligibilityRule:
        key = (rule.eligibility_rule_id, rule.rule_version)
        existing = self._rules.get(key)
        if existing is not None:
            if existing == rule:
                return existing
            raise RuleVersionFrozenError(
                f"rule {rule.eligibility_rule_id} version {rule.rule_version} "
                "already exists with different content"
            )
        self._rules[key] = rule
        return rule

    def get(self, eligibility_rule_id: UUID, rule_version: int) -> EligibilityRule | None:
        return self._rules.get((eligibility_rule_id, rule_version))

    def latest_version(self, eligibility_rule_id: UUID) -> EligibilityRule | None:
        matching = [r for (rid, _), r in self._rules.items() if rid == eligibility_rule_id]
        if not matching:
            return None
        return max(matching, key=lambda r: r.rule_version)


class InMemoryEligibilityDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[UUID, EligibilityDecision] = {}

    def save(self, decision: EligibilityDecision) -> None:
        self._decisions[decision.eligibility_decision_id] = decision

    def get(self, eligibility_decision_id: UUID) -> EligibilityDecision | None:
        return self._decisions.get(eligibility_decision_id)


class InMemoryEligibilitySnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[UUID, EligibilitySnapshot] = {}

    def save(self, snapshot: EligibilitySnapshot) -> None:
        self._snapshots[snapshot.eligibility_snapshot_id] = snapshot

    def get(self, eligibility_snapshot_id: UUID) -> EligibilitySnapshot | None:
        return self._snapshots.get(eligibility_snapshot_id)
