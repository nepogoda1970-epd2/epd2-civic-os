"""W4 — bounded regional intervention (`FIR-GOV-004`).

The rule this module exists to enforce is "contain authority, not the region".
It provides the four governed levels and refuses, structurally, to provide a
fifth coarse one: `open_restriction` validates every action code against the
governed inventory, so a caller cannot freeze "everything" by passing a
wildcard, an unknown code or an empty set.

It also protects regional continuity: `preserved_capabilities` lists what an
intervention may never take away without its own separate legal decision, and
`assert_continuity` proves a proposed restriction does not reach them.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from epd2_control_plane_service.domain import (
    MAX_SUPERVISION_DAYS,
    InterventionType,
    RegionalAdministrationRestriction,
    Scope,
    TemporarySupervision,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory
from epd2_control_plane_service.policy import ControlPolicy

__all__ = [
    "PRESERVED_MEMBER_CAPABILITIES",
    "VOTING_DOMAIN_PROHIBITED_EFFECTS",
    "InterventionService",
]

#: `FIR-GOV-004` regional continuity: an intervention against regional
#: administration does not touch these without a separate, independently
#: authorized decision.
PRESERVED_MEMBER_CAPABILITIES: tuple[str, ...] = (
    "PUBLIC_READ_APPROVED_MATERIAL",
    "ORDINARY_MEMBER_ACCESS_IN_EXISTING_SCOPE",
    "DISCUSSION_AND_INITIATIVE_PARTICIPATION",
    "EXISTING_MEETINGS_DOCUMENTS_DECISIONS_AS_HISTORY",
    "AUDIT_AND_EVIDENCE_VISIBILITY_UNDER_EXISTING_RULES",
    "CASE_AND_CORRESPONDENCE_HISTORY",
    "PATH_TO_RESTORE_LAWFUL_REGIONAL_SELF_ADMINISTRATION",
)

#: Effects that regional intervention may never produce by itself.
VOTING_DOMAIN_PROHIBITED_EFFECTS: tuple[str, ...] = (
    "READ_BALLOT_CONTENT",
    "REVEAL_IDENTITY_VOTE_LINKAGE",
    "MINT_VOTING_CREDENTIALS",
    "OPERATE_TRUSTEE_KEYS",
    "ALTER_TALLY_EVIDENCE",
)


class InterventionService:
    """Creates and lifts governed interventions."""

    def __init__(
        self, policy: ControlPolicy | None = None, inventory: ActionInventory = INVENTORY
    ) -> None:
        self._policy = policy or ControlPolicy.governed()
        self._inventory = inventory

    def _validate_action_codes(self, action_codes: Iterable[str]) -> frozenset[str]:
        codes = frozenset(action_codes)
        if not self._policy.enforce_closed_action_codes:
            return codes
        if not codes:
            raise AuthorizationRefused(
                "an intervention must name the exact action codes it affects",
                reason_code="CTRL_RESTRICTION_UNBOUNDED",
            )
        unknown = sorted(code for code in codes if code not in self._inventory)
        if unknown:
            raise AuthorizationRefused(
                f"restriction references action codes outside the governed inventory: {unknown}",
                reason_code="CTRL_RESTRICTION_FREE_TEXT",
            )
        for code in codes:
            if not self._inventory.get(code).mutation:
                raise AuthorizationRefused(
                    f"{code} is a read action; freezing it would remove evidence visibility",
                    reason_code="CTRL_RESTRICTION_TOUCHES_PRESERVED",
                )
        return codes

    def assert_continuity(self, affected_capabilities: Iterable[str]) -> None:
        """Refuse a proposed intervention that reaches preserved capabilities."""
        touched = sorted(set(affected_capabilities) & set(PRESERVED_MEMBER_CAPABILITIES))
        if touched:
            raise AuthorizationRefused(
                f"intervention would remove preserved member/regional capabilities {touched}; "
                "that requires its own competent legal decision",
                reason_code="CTRL_RESTRICTION_TOUCHES_PRESERVED",
            )

    def assert_no_voting_effect(self, claimed_effects: Iterable[str]) -> None:
        if not self._policy.enforce_voting_boundary:
            return
        touched = sorted(set(claimed_effects) & set(VOTING_DOMAIN_PROHIBITED_EFFECTS))
        if touched:
            raise AuthorizationRefused(
                f"regional intervention may not produce voting-domain effects {touched}",
                reason_code="CTRL_VOTING_BOUNDARY",
            )

    def open_restriction(
        self,
        *,
        restriction_id: str,
        intervention_type: InterventionType,
        target_scope: Scope,
        affected_action_codes: Iterable[str],
        affected_authority_ids: Iterable[str] = (),
        valid_from: datetime,
        valid_until: datetime,
        reason_code: str,
        rule_version: str,
        decision_ref: str,
        initiating_authority_id: str,
        approving_authority_id: str | None,
        notification_evidence_ref: str,
        review_deadline: datetime,
        evidence_refs: tuple[str, ...] = (),
    ) -> RegionalAdministrationRestriction:
        if intervention_type is InterventionType.TEMPORARY_SUPERVISION:
            raise AuthorizationRefused(
                "temporary supervision is opened through open_supervision, not as a restriction",
                reason_code="CTRL_INTERVENTION_TYPE",
            )
        codes = self._validate_action_codes(affected_action_codes)
        if (
            intervention_type
            in {
                InterventionType.AUTHORITY_SUSPENSION,
                InterventionType.REGIONAL_ACTION_RESTRICTION,
            }
            and approving_authority_id is None
        ):
            # FIR-GOV-004 levels 2-4 require two distinct authorized humans.
            raise AuthorizationRefused(
                f"{intervention_type.value} requires a distinct approving authority",
                reason_code="CTRL_QUORUM_INSUFFICIENT",
            )
        if approving_authority_id is not None and approving_authority_id == initiating_authority_id:
            raise AuthorizationRefused(
                "the initiating and approving authority must be distinct",
                reason_code="CTRL_SELF_APPROVAL",
            )
        return RegionalAdministrationRestriction(
            restriction_id=restriction_id,
            intervention_type=intervention_type,
            target_scope=target_scope,
            affected_authority_ids=frozenset(affected_authority_ids),
            affected_action_codes=codes,
            valid_from=valid_from,
            valid_until=valid_until,
            reason_code=reason_code,
            rule_version=rule_version,
            decision_ref=decision_ref,
            initiating_authority_id=initiating_authority_id,
            approving_authority_id=approving_authority_id,
            notification_evidence_ref=notification_evidence_ref,
            review_deadline=review_deadline,
            evidence_refs=evidence_refs,
        )

    def open_supervision(
        self,
        *,
        supervision_id: str,
        supervised_scope: Scope,
        supervisor_authority_id: str,
        granted_action_codes: Iterable[str],
        valid_from: datetime,
        valid_until: datetime,
        decision_ref: str,
        rule_version: str,
        review_deadline: datetime,
        confirmation_organ: str,
    ) -> TemporarySupervision:
        codes = self._validate_action_codes(granted_action_codes)
        return TemporarySupervision(
            supervision_id=supervision_id,
            supervised_scope=supervised_scope,
            supervisor_authority_id=supervisor_authority_id,
            granted_action_codes=codes,
            valid_from=valid_from,
            valid_until=valid_until,
            decision_ref=decision_ref,
            rule_version=rule_version,
            review_deadline=review_deadline,
            confirmation_organ=confirmation_organ,
        )

    def extend(
        self,
        restriction: RegionalAdministrationRestriction,
        *,
        new_valid_until: datetime,
        new_decision_ref: str,
        new_restriction_id: str,
        initiating_authority_id: str,
        approving_authority_id: str,
        review_deadline: datetime,
        notification_evidence_ref: str,
    ) -> RegionalAdministrationRestriction:
        """Extension is a *new* governed decision that supersedes the old
        restriction. There is deliberately no in-place prolongation."""
        if new_decision_ref == restriction.decision_ref:
            raise AuthorizationRefused(
                "extension requires a new governed decision and new audit evidence",
                reason_code="CTRL_SILENT_EXTENSION",
            )
        return RegionalAdministrationRestriction(
            restriction_id=new_restriction_id,
            intervention_type=restriction.intervention_type,
            target_scope=restriction.target_scope,
            affected_authority_ids=restriction.affected_authority_ids,
            affected_action_codes=restriction.affected_action_codes,
            valid_from=restriction.valid_until or restriction.valid_from,
            valid_until=new_valid_until,
            reason_code=restriction.reason_code,
            rule_version=restriction.rule_version,
            decision_ref=new_decision_ref,
            initiating_authority_id=initiating_authority_id,
            approving_authority_id=approving_authority_id,
            notification_evidence_ref=notification_evidence_ref,
            review_deadline=review_deadline,
            evidence_refs=restriction.evidence_refs,
        )

    @staticmethod
    def max_supervision_window(start: datetime) -> datetime:
        return start + timedelta(days=MAX_SUPERVISION_DAYS)
