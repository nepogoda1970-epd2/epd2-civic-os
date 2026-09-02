"""W3 — separation of duties.

A SoD rule names two responsibilities that a single consequential operation may
not concentrate in one principal. One natural person may hold several offices
where policy allows it; what is forbidden is discharging both halves of a rule
*within the same operation* (`FIR-SEC-004` authority roles).

`Bund oversight` is included as a responsibility because `FIR-GOV-005` section
15 forbids a technical operator from deciding the political merits of an
intervention: the acting regional principal and the confirming oversight organ
must be distinct.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from epd2_control_plane_service.domain import ControlAction, Right
from epd2_control_plane_service.policy import ControlPolicy

__all__ = ["SOD_RULES", "Responsibility", "SodEngine", "SodRule", "SodViolation"]


class Responsibility(StrEnum):
    """A discharged responsibility within one operation."""

    REQUEST = "REQUEST"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"
    AUDIT = "AUDIT"
    SECRET_VISIBILITY = "SECRET_VISIBILITY"
    CREDENTIAL_ISSUANCE = "CREDENTIAL_ISSUANCE"
    KEY_CUSTODY = "KEY_CUSTODY"
    POLICY_APPROVAL = "POLICY_APPROVAL"
    EMERGENCY_GRANT = "EMERGENCY_GRANT"
    EMERGENCY_REVIEW = "EMERGENCY_REVIEW"
    DESTRUCTIVE_OPERATION = "DESTRUCTIVE_OPERATION"
    DESTRUCTIVE_CONFIRMATION = "DESTRUCTIVE_CONFIRMATION"
    REGIONAL_ACTION = "REGIONAL_ACTION"
    BUND_OVERSIGHT = "BUND_OVERSIGHT"


@dataclass(frozen=True, slots=True)
class SodRule:
    rule_id: str
    left: Responsibility
    right: Responsibility
    reason_code: str
    governing_fir: str
    description: str

    def pair(self) -> frozenset[Responsibility]:
        return frozenset({self.left, self.right})


@dataclass(frozen=True, slots=True)
class SodViolation:
    rule_id: str
    principal_id: str
    left: Responsibility
    right: Responsibility
    reason_code: str


#: The W3 minimum matrix. Additional rules may be added by a later governed
#: policy; none of these may be weakened.
SOD_RULES: tuple[SodRule, ...] = (
    SodRule(
        "SOD-01",
        Responsibility.REQUEST,
        Responsibility.APPROVE,
        "CTRL_SELF_APPROVAL",
        "FIR-GOV-005",
        "The principal who requests a consequential act may not approve it.",
    ),
    SodRule(
        "SOD-02",
        Responsibility.APPROVE,
        Responsibility.EXECUTE,
        "CTRL_APPROVE_EXECUTE_MERGED",
        "FIR-SEC-004",
        "Approval and execution/custody are separate authorities.",
    ),
    SodRule(
        "SOD-03",
        Responsibility.EXECUTE,
        Responsibility.AUDIT,
        "CTRL_EXECUTE_AUDIT_MERGED",
        "FIR-CTRL-001",
        "An actor may not audit or review their own executed act.",
    ),
    SodRule(
        "SOD-04",
        Responsibility.SECRET_VISIBILITY,
        Responsibility.APPROVE,
        "CTRL_SECRET_VISIBILITY_APPROVER",
        "FIR-SEC-004",
        "An approver never requires plaintext private material to approve.",
    ),
    SodRule(
        "SOD-05",
        Responsibility.CREDENTIAL_ISSUANCE,
        Responsibility.AUDIT,
        "CTRL_ISSUANCE_AUDIT_MERGED",
        "FIR-SEC-004",
        "The issuer of a credential may not be its independent reviewer.",
    ),
    SodRule(
        "SOD-06",
        Responsibility.KEY_CUSTODY,
        Responsibility.POLICY_APPROVAL,
        "CTRL_CUSTODY_POLICY_MERGED",
        "FIR-TRUST-002",
        "Key custody does not carry the authority to approve the key policy it executes.",
    ),
    SodRule(
        "SOD-07",
        Responsibility.EMERGENCY_GRANT,
        Responsibility.EMERGENCY_REVIEW,
        "CTRL_EMERGENCY_SELF_REVIEW",
        "FIR-SEC-004",
        "An actor of a break-glass grant may not conduct its mandatory post-use review.",
    ),
    SodRule(
        "SOD-08",
        Responsibility.DESTRUCTIVE_OPERATION,
        Responsibility.DESTRUCTIVE_CONFIRMATION,
        "CTRL_DESTRUCTIVE_SELF_CONFIRM",
        "FIR-TRUST-002",
        "A destructive operation is confirmed by a principal other than the one performing it.",
    ),
    SodRule(
        "SOD-09",
        Responsibility.REGIONAL_ACTION,
        Responsibility.BUND_OVERSIGHT,
        "CTRL_OVERSIGHT_SELF_CONFIRM",
        "FIR-GOV-005",
        "The acting regional principal may not also supply the higher-level confirmation.",
    ),
)


class SodEngine:
    """Evaluates a responsibility assignment against `SOD_RULES`."""

    def __init__(
        self, policy: ControlPolicy | None = None, rules: tuple[SodRule, ...] = SOD_RULES
    ) -> None:
        self._policy = policy or ControlPolicy.governed()
        self._rules = rules

    @property
    def rules(self) -> tuple[SodRule, ...]:
        return self._rules

    def evaluate(
        self, assignment: Mapping[Responsibility, tuple[str, ...]]
    ) -> tuple[SodViolation, ...]:
        """`assignment` maps each discharged responsibility to the principals
        that discharged it. Returns every violated rule."""
        violations: list[SodViolation] = []
        for rule in self._rules:
            if rule.reason_code == "CTRL_SELF_APPROVAL" and not self._policy.reject_self_approval:
                continue
            left = set(assignment.get(rule.left, ()))
            right = set(assignment.get(rule.right, ()))
            for principal in sorted(left & right):
                violations.append(
                    SodViolation(rule.rule_id, principal, rule.left, rule.right, rule.reason_code)
                )
        return tuple(violations)

    def responsibilities_for(self, action: ControlAction) -> frozenset[Responsibility]:
        """Which responsibilities this action's workflow actually discharges."""
        responsibilities = {Responsibility.REQUEST, Responsibility.EXECUTE, Responsibility.AUDIT}
        if action.required_right_approve is not None and action.quorum_required >= 1:
            responsibilities.add(Responsibility.APPROVE)
        if action.secret_visibility_right is not None:
            responsibilities.add(Responsibility.SECRET_VISIBILITY)
        if action.domain == "credential":
            responsibilities.add(Responsibility.CREDENTIAL_ISSUANCE)
        if action.domain == "key_trust":
            responsibilities.add(Responsibility.KEY_CUSTODY)
            responsibilities.add(Responsibility.POLICY_APPROVAL)
        if action.domain == "emergency":
            responsibilities.add(Responsibility.EMERGENCY_GRANT)
            responsibilities.add(Responsibility.EMERGENCY_REVIEW)
        if action.required_right_execute is Right.DESTROY:
            responsibilities.add(Responsibility.DESTRUCTIVE_OPERATION)
            responsibilities.add(Responsibility.DESTRUCTIVE_CONFIRMATION)
        if action.domain == "intervention":
            responsibilities.add(Responsibility.REGIONAL_ACTION)
            responsibilities.add(Responsibility.BUND_OVERSIGHT)
        return frozenset(responsibilities)

    def matrix(self) -> list[dict[str, str]]:
        return [
            {
                "rule_id": r.rule_id,
                "left": r.left.value,
                "right": r.right.value,
                "reason_code": r.reason_code,
                "governing_fir": r.governing_fir,
                "description": r.description,
            }
            for r in self._rules
        ]
