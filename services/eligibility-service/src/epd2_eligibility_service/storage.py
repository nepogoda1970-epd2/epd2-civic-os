"""Storage protocols and in-memory reference adapters for Eligibility
Service's three owned entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_eligibility_service.domain import (
    AssemblyDecision,
    CriticalPolicyStatus,
    DigitalDecision,
    EligibilityDecision,
    EligibilityRule,
    EligibilitySnapshot,
    ParticipantEligibilityPolicy,
    ProcessEligibilityPolicy,
    StepUpAuthenticationRequirement,
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


# ---------------------------------------------------------------------------
# PACK-07 additions (canon 19d.4/19d.5/19d.8/19d.12, canon-0.6.0)
# ---------------------------------------------------------------------------


class ParticipantEligibilityPolicyStore(Protocol):
    def save(self, policy: ParticipantEligibilityPolicy) -> None: ...

    def get(self, policy_id: UUID) -> ParticipantEligibilityPolicy | None: ...

    def resolve_for_evaluation(
        self, *, scope_type: str | None, scope_id: UUID | None, effective_date: datetime
    ) -> ParticipantEligibilityPolicy | None:
        """The same single-active-version resolution discipline ADR-030
        item 6 establishes for `ProcessEligibilityPolicy`, applied here to
        `ParticipantEligibilityPolicy`'s own scope dimension."""
        ...


class InMemoryParticipantEligibilityPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, ParticipantEligibilityPolicy] = {}

    def save(self, policy: ParticipantEligibilityPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: UUID) -> ParticipantEligibilityPolicy | None:
        return self._policies.get(policy_id)

    def resolve_for_evaluation(
        self, *, scope_type: str | None, scope_id: UUID | None, effective_date: datetime
    ) -> ParticipantEligibilityPolicy | None:
        candidates = [
            policy
            for policy in self._policies.values()
            if (
                policy.status is CriticalPolicyStatus.ACTIVE
                and policy.scope_type == scope_type
                and policy.scope_id == scope_id
                and (policy.effective_from is None or policy.effective_from <= effective_date)
                and (policy.effective_until is None or effective_date < policy.effective_until)
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.policy_version)


class ProcessEligibilityPolicyStore(Protocol):
    def save(self, policy: ProcessEligibilityPolicy) -> None: ...

    def get(self, policy_id: UUID) -> ProcessEligibilityPolicy | None: ...

    def resolve_for_evaluation(
        self,
        *,
        process_type: str,
        jurisdiction: str,
        scope_type: str | None,
        scope_id: UUID | None,
        effective_date: datetime,
    ) -> ProcessEligibilityPolicy | None:
        """ADR-030 item 6's resolution procedure: exactly one `active`
        version whose `(process_type, jurisdiction, scope_type, scope_id)`
        matches and whose `[effective_from, effective_until)` window
        covers `effective_date`."""
        ...


class InMemoryProcessEligibilityPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, ProcessEligibilityPolicy] = {}

    def save(self, policy: ProcessEligibilityPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: UUID) -> ProcessEligibilityPolicy | None:
        return self._policies.get(policy_id)

    def resolve_for_evaluation(
        self,
        *,
        process_type: str,
        jurisdiction: str,
        scope_type: str | None,
        scope_id: UUID | None,
        effective_date: datetime,
    ) -> ProcessEligibilityPolicy | None:
        candidates = [
            policy
            for policy in self._policies.values()
            if (
                policy.status is CriticalPolicyStatus.ACTIVE
                and policy.process_type == process_type
                and policy.jurisdiction == jurisdiction
                and policy.scope_type == scope_type
                and policy.scope_id == scope_id
                and (policy.effective_from is None or policy.effective_from <= effective_date)
                and (policy.effective_until is None or effective_date < policy.effective_until)
            )
        ]
        if not candidates:
            return None
        # ADR-030 item 6: "exactly one applicable version" - in the
        # (non-enforced-by-storage) event more than one active version's
        # window somehow overlaps, the highest `policy_version` wins,
        # never an arbitrary one.
        return max(candidates, key=lambda p: p.policy_version)


class StepUpAuthenticationRequirementStore(Protocol):
    def save(self, requirement: StepUpAuthenticationRequirement) -> None: ...

    def get(self, requirement_id: UUID) -> StepUpAuthenticationRequirement | None: ...

    def resolve_for_action(
        self, *, action_code: str, effective_date: datetime
    ) -> StepUpAuthenticationRequirement | None:
        """ADR-030 item 7's "single active version" resolution, keyed on
        `action_code` rather than a process tuple."""
        ...


class InMemoryStepUpAuthenticationRequirementStore:
    def __init__(self) -> None:
        self._requirements: dict[UUID, StepUpAuthenticationRequirement] = {}

    def save(self, requirement: StepUpAuthenticationRequirement) -> None:
        self._requirements[requirement.requirement_id] = requirement

    def get(self, requirement_id: UUID) -> StepUpAuthenticationRequirement | None:
        return self._requirements.get(requirement_id)

    def resolve_for_action(
        self, *, action_code: str, effective_date: datetime
    ) -> StepUpAuthenticationRequirement | None:
        candidates = [
            requirement
            for requirement in self._requirements.values()
            if (
                requirement.status is CriticalPolicyStatus.ACTIVE
                and requirement.action_code == action_code
                and (
                    requirement.effective_from is None
                    or requirement.effective_from <= effective_date
                )
                and (
                    requirement.effective_until is None
                    or effective_date < requirement.effective_until
                )
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.requirement_version)


class DigitalDecisionStore(Protocol):
    def save(self, decision: DigitalDecision) -> None: ...

    def get(self, digital_decision_id: UUID) -> DigitalDecision | None: ...


class InMemoryDigitalDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[UUID, DigitalDecision] = {}

    def save(self, decision: DigitalDecision) -> None:
        self._decisions[decision.digital_decision_id] = decision

    def get(self, digital_decision_id: UUID) -> DigitalDecision | None:
        return self._decisions.get(digital_decision_id)


class AssemblyDecisionStore(Protocol):
    def save(self, decision: AssemblyDecision) -> None: ...

    def get(self, assembly_decision_id: UUID) -> AssemblyDecision | None: ...

    def get_for_digital_decision(self, digital_decision_id: UUID) -> AssemblyDecision | None: ...


class InMemoryAssemblyDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[UUID, AssemblyDecision] = {}

    def save(self, decision: AssemblyDecision) -> None:
        self._decisions[decision.assembly_decision_id] = decision

    def get(self, assembly_decision_id: UUID) -> AssemblyDecision | None:
        return self._decisions.get(assembly_decision_id)

    def get_for_digital_decision(self, digital_decision_id: UUID) -> AssemblyDecision | None:
        for decision in self._decisions.values():
            if decision.digital_decision_id == digital_decision_id:
                return decision
        return None
