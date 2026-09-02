"""The runtime route table.

This is the *runtime* surface: the set of (method, path) endpoints the control
plane actually serves. It is deliberately a second, independently maintained
source rather than a projection of the inventory, because a congruence check
between an artifact and itself proves nothing. Gate G04 reconciles this table
against `inventory.py` in both directions, so a route added here without a
governed inventory entry — or an inventory entry with no route — is a finding.

Adding an endpoint means adding it in both places, on purpose.
"""

from __future__ import annotations

__all__ = ["ROUTE_TABLE", "mutation_action_ids", "route_action_ids"]

#: (method, path) -> action_id
ROUTE_TABLE: dict[tuple[str, str], str] = {
    ("POST", "/ctrl/v1/ai_oversight/ai/review_draft"): "AI.REVIEW_DRAFT",
    ("POST", "/ctrl/v1/assemblies/assembly/publish_minutes"): "ASSEMBLY.PUBLISH_MINUTES",
    ("GET", "/ctrl/v1/audit/audit/lookup"): "AUDIT.LOOKUP",
    ("POST", "/ctrl/v1/authority/auth/assign"): "AUTH.ASSIGN",
    ("GET", "/ctrl/v1/authority/auth/read_provenance"): "AUTH.READ_PROVENANCE",
    ("POST", "/ctrl/v1/authority/auth/restore"): "AUTH.RESTORE",
    ("POST", "/ctrl/v1/authority/auth/revoke"): "AUTH.REVOKE",
    ("POST", "/ctrl/v1/authority/auth/suspend"): "AUTH.SUSPEND",
    ("POST", "/ctrl/v1/casework/case/ombuds_decide"): "CASE.OMBUDS_DECIDE",
    ("POST", "/ctrl/v1/citizen_office/citizen_office/route_case"): "CITIZEN_OFFICE.ROUTE_CASE",
    (
        "POST",
        "/ctrl/v1/correspondence/correspondence/send_official",
    ): "CORRESPONDENCE.SEND_OFFICIAL",
    ("POST", "/ctrl/v1/credential/cred/high_assurance_recovery"): "CRED.HIGH_ASSURANCE_RECOVERY",
    ("POST", "/ctrl/v1/credential/cred/human_enroll"): "CRED.HUMAN_ENROLL",
    ("POST", "/ctrl/v1/credential/cred/human_revoke"): "CRED.HUMAN_REVOKE",
    ("POST", "/ctrl/v1/election_admin/election/admin_action"): "ELECTION.ADMIN_ACTION",
    ("POST", "/ctrl/v1/emergency/emergency/activate"): "EMERGENCY.ACTIVATE",
    ("POST", "/ctrl/v1/emergency/emergency/approve"): "EMERGENCY.APPROVE",
    ("POST", "/ctrl/v1/emergency/emergency/request"): "EMERGENCY.REQUEST",
    ("POST", "/ctrl/v1/emergency/emergency/review"): "EMERGENCY.REVIEW",
    ("POST", "/ctrl/v1/emergency/emergency/revoke"): "EMERGENCY.REVOKE",
    ("POST", "/ctrl/v1/finance/finance/approve_payment"): "FINANCE.APPROVE_PAYMENT",
    (
        "POST",
        "/ctrl/v1/intervention/intervene/authority_suspension",
    ): "INTERVENE.AUTHORITY_SUSPENSION",
    ("POST", "/ctrl/v1/intervention/intervene/lift"): "INTERVENE.LIFT",
    ("GET", "/ctrl/v1/intervention/intervene/read_active"): "INTERVENE.READ_ACTIVE",
    (
        "POST",
        "/ctrl/v1/intervention/intervene/regional_action_restriction",
    ): "INTERVENE.REGIONAL_ACTION_RESTRICTION",
    ("POST", "/ctrl/v1/intervention/intervene/session_quarantine"): "INTERVENE.SESSION_QUARANTINE",
    (
        "POST",
        "/ctrl/v1/intervention/intervene/temporary_supervision",
    ): "INTERVENE.TEMPORARY_SUPERVISION",
    ("POST", "/ctrl/v1/privileged/jit/request"): "JIT.REQUEST",
    ("POST", "/ctrl/v1/key_trust/key/destroy"): "KEY.DESTROY",
    ("POST", "/ctrl/v1/key_trust/key/mark_compromised"): "KEY.MARK_COMPROMISED",
    ("GET", "/ctrl/v1/key_trust/key/read_trust_state"): "KEY.READ_TRUST_STATE",
    ("POST", "/ctrl/v1/key_trust/key/request_generation"): "KEY.REQUEST_GENERATION",
    ("POST", "/ctrl/v1/key_trust/key/rotate"): "KEY.ROTATE",
    ("POST", "/ctrl/v1/membership/membership/admin_mutate"): "MEMBERSHIP.ADMIN_MUTATE",
    ("POST", "/ctrl/v1/moderation/moderation/decide"): "MODERATION.DECIDE",
    ("POST", "/ctrl/v1/offices/office/assign_mandate"): "OFFICE.ASSIGN_MANDATE",
    ("GET", "/ctrl/v1/platform/platform/read_health"): "PLATFORM.READ_HEALTH",
    ("POST", "/ctrl/v1/platform/platform/service_task"): "PLATFORM.SERVICE_TASK",
    ("POST", "/ctrl/v1/privacy/privacy/review_export"): "PRIVACY.REVIEW_EXPORT",
    ("POST", "/ctrl/v1/procurement/procurement/approve_vendor"): "PROCUREMENT.APPROVE_VENDOR",
    ("POST", "/ctrl/v1/records/records/apply_retention"): "RECORDS.APPLY_RETENTION",
    ("POST", "/ctrl/v1/protected_reporting/reporting/custody_access"): "REPORTING.CUSTODY_ACCESS",
    (
        "POST",
        "/ctrl/v1/representative/representative/open_desk_update",
    ): "REPRESENTATIVE.OPEN_DESK_UPDATE",
    ("POST", "/ctrl/v1/service_identity/service_cred/issue"): "SERVICE_CRED.ISSUE",
    ("POST", "/ctrl/v1/service_identity/service_cred/revoke"): "SERVICE_CRED.REVOKE",
    ("POST", "/ctrl/v1/service_identity/service_cred/rotate"): "SERVICE_CRED.ROTATE",
    ("POST", "/ctrl/v1/session/session/revoke"): "SESSION.REVOKE",
    ("POST", "/ctrl/v1/transparency/transparency/publish"): "TRANSPARENCY.PUBLISH",
}


#: Endpoints served with a state-changing method.
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def route_action_ids() -> frozenset[str]:
    return frozenset(ROUTE_TABLE.values())


def mutation_action_ids() -> frozenset[str]:
    return frozenset(
        action for (method, _), action in ROUTE_TABLE.items() if method in _MUTATING_METHODS
    )
