"""W1 — the administrative action inventory.

The inventory is authored here as typed data rather than as a loose JSON blob
so that the runtime and the published `ctrl_action_inventory.json` cannot drift:
the JSON is *derived* from these objects, and gate G04 additionally proves that
every registered runtime mutation handler resolves to exactly one entry and that
no entry lacks a handler.

Coverage follows the `FIR-CTRL-001` minimum desk inventory. A role that
deliberately has no control-plane surface is recorded as an explicit `NO_UI`
decision in the control-plane registry rather than being silently absent.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from epd2_control_plane_service.domain import ActorClass, ControlAction, Right, ScopeLevel
from epd2_control_plane_service.exceptions import InventoryError

__all__ = [
    "ACTIONS",
    "INVENTORY",
    "NO_UI_DECISIONS",
    "ActionInventory",
    "inventory_to_json_obj",
]


def _action(
    action_id: str,
    *,
    domain: str,
    desk_id: str,
    console_id: str,
    object_class: str,
    scope_level: ScopeLevel = ScopeLevel.LAND,
    actor_class: ActorClass = ActorClass.HUMAN,
    execute: Right = Right.EXECUTE,
    approve: Right | None = Right.APPROVE,
    revoke: Right | None = Right.REVOKE,
    secret: Right | None = None,
    mutation: bool = True,
    quorum: int = 1,
    four_eyes: bool = False,
    emergency_eligible: bool = False,
    max_grant_seconds: int | None = None,
    assurance: str = "AAL2",
    step_up: bool = False,
    sensitive: Iterable[str] = (),
    voting_boundary: str = "OUTSIDE_VOTING_DOMAIN",
    firs: Iterable[str] = ("FIR-CTRL-001",),
    incompatible: Iterable[tuple[Right, Right]] = (),
    notes: str = "",
) -> ControlAction:
    default_incompatible: tuple[tuple[Right, Right], ...] = (
        (Right.REQUEST, Right.APPROVE),
        (Right.APPROVE, Right.EXECUTE),
        (Right.EXECUTE, Right.REVIEW_OR_AUDIT),
    )
    return ControlAction(
        action_id=action_id,
        domain=domain,
        actor_class=actor_class,
        required_right_request=Right.REQUEST,
        required_right_approve=approve,
        required_right_execute=execute,
        required_right_revoke=revoke,
        required_right_audit=Right.REVIEW_OR_AUDIT,
        secret_visibility_right=secret,
        scope_level=scope_level,
        object_class=object_class,
        mutation=mutation,
        quorum_required=quorum,
        four_eyes=four_eyes,
        emergency_eligible=emergency_eligible,
        max_grant_seconds=max_grant_seconds,
        commit_time_reauthorization=mutation,
        immutable_evidence_required=True,
        console_id=console_id,
        desk_id=desk_id,
        route=f"/ctrl/v1/{domain}/{action_id.lower().replace('.', '/')}",
        assurance_level=assurance,
        step_up_required=step_up,
        incompatible_rights=frozenset(tuple(incompatible) or default_incompatible),
        sensitive_data_classes=frozenset(sensitive),
        voting_domain_boundary=voting_boundary,
        governing_fir_refs=tuple(firs),
        notes=notes,
    )


_SEC = "CONSOLE_SECURITY"
_IDENT = "CONSOLE_IDENTITY"
_GOV = "CONSOLE_GOVERNANCE"
_OVER = "CONSOLE_OVERSIGHT"
_OPS = "CONSOLE_OPERATIONS"
_WORK = "CONSOLE_WORKDESK"


ACTIONS: tuple[ControlAction, ...] = (
    # -- Organizational authority lifecycle (FIR-GOV-005, FIR-SEC-004 class 4) --
    _action(
        "AUTH.ASSIGN",
        domain="authority",
        desk_id="DESK_ORG_AUTHORITY",
        console_id=_GOV,
        object_class="OrganizationalAuthority",
        quorum=2,
        four_eyes=True,
        step_up=True,
        firs=("FIR-GOV-005", "FIR-SEC-004"),
        notes="Assignment must cite the source election/appointment decision and rule version.",
    ),
    _action(
        "AUTH.SUSPEND",
        domain="authority",
        desk_id="DESK_ORG_AUTHORITY",
        console_id=_GOV,
        object_class="OrganizationalAuthority",
        execute=Right.SUSPEND_OR_QUARANTINE,
        quorum=2,
        four_eyes=True,
        firs=("FIR-GOV-004", "FIR-GOV-005"),
        notes=(
            "FIR-GOV-004 level 2. Suspension fails authorization at the moment of every affected "
            "act."
        ),
    ),
    _action(
        "AUTH.RESTORE",
        domain="authority",
        desk_id="DESK_ORG_AUTHORITY",
        console_id=_GOV,
        object_class="OrganizationalAuthority",
        execute=Right.RESTORE,
        quorum=2,
        four_eyes=True,
        firs=("FIR-GOV-004", "FIR-GOV-005"),
        notes="A technical administrator cannot restore a politically suspended office.",
    ),
    _action(
        "AUTH.REVOKE",
        domain="authority",
        desk_id="DESK_ORG_AUTHORITY",
        console_id=_GOV,
        object_class="OrganizationalAuthority",
        execute=Right.REVOKE,
        quorum=2,
        four_eyes=True,
        firs=("FIR-GOV-004", "FIR-GOV-005"),
    ),
    _action(
        "AUTH.READ_PROVENANCE",
        domain="authority",
        desk_id="DESK_ORG_AUTHORITY",
        console_id=_GOV,
        object_class="OrganizationalAuthority",
        execute=Right.READ_METADATA,
        approve=None,
        revoke=None,
        mutation=False,
        quorum=0,
        firs=("FIR-GOV-005",),
        notes="Read model. Summarises current state without erasing historical source records.",
    ),
    # -- Regional intervention (FIR-GOV-004 levels 1..4) --
    _action(
        "INTERVENE.SESSION_QUARANTINE",
        domain="intervention",
        desk_id="DESK_SECURITY_OPERATIONS",
        console_id=_SEC,
        object_class="Session",
        execute=Right.SUSPEND_OR_QUARANTINE,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=3600,
        firs=("FIR-GOV-004", "FIR-SEC-004", "FIR-TRUST-002"),
        notes=(
            "Level 1 containment may be pre-authorised by incident policy; it is not a removal "
            "from office."
        ),
    ),
    _action(
        "INTERVENE.AUTHORITY_SUSPENSION",
        domain="intervention",
        desk_id="DESK_REGIONAL_INTERVENTION",
        console_id=_GOV,
        object_class="RegionalAdministrationRestriction",
        execute=Right.SUSPEND_OR_QUARANTINE,
        quorum=2,
        four_eyes=True,
        step_up=True,
        firs=("FIR-GOV-004", "FIR-GOV-005"),
        notes="Level 2. Requires the competent organ chain and a confirmation route.",
    ),
    _action(
        "INTERVENE.REGIONAL_ACTION_RESTRICTION",
        domain="intervention",
        desk_id="DESK_REGIONAL_INTERVENTION",
        console_id=_GOV,
        object_class="RegionalAdministrationRestriction",
        execute=Right.SUSPEND_OR_QUARANTINE,
        quorum=2,
        four_eyes=True,
        step_up=True,
        firs=("FIR-GOV-004",),
        notes="Level 3. Freezes named action codes only; a scope-wide disable is prohibited.",
    ),
    _action(
        "INTERVENE.TEMPORARY_SUPERVISION",
        domain="intervention",
        desk_id="DESK_REGIONAL_INTERVENTION",
        console_id=_GOV,
        object_class="TemporarySupervision",
        execute=Right.ACTIVATE,
        quorum=2,
        four_eyes=True,
        step_up=True,
        firs=("FIR-GOV-004", "FIR-GOV-005"),
        notes="Level 4. Bounded at 90 days; extension requires a new decision.",
    ),
    _action(
        "INTERVENE.LIFT",
        domain="intervention",
        desk_id="DESK_REGIONAL_INTERVENTION",
        console_id=_GOV,
        object_class="RegionalAdministrationRestriction",
        execute=Right.RESTORE,
        quorum=2,
        four_eyes=True,
        firs=("FIR-GOV-004",),
    ),
    _action(
        "INTERVENE.READ_ACTIVE",
        domain="intervention",
        desk_id="DESK_REGIONAL_INTERVENTION",
        console_id=_GOV,
        object_class="RegionalAdministrationRestriction",
        execute=Right.READ_METADATA,
        approve=None,
        revoke=None,
        mutation=False,
        quorum=0,
        firs=("FIR-GOV-004",),
    ),
    # -- Human credential and session lifecycle (FIR-SEC-004 classes 1..3) --
    _action(
        "CRED.HUMAN_ENROLL",
        domain="credential",
        desk_id="DESK_CREDENTIAL_OPERATIONS",
        console_id=_IDENT,
        object_class="HumanAuthenticator",
        execute=Right.ACTIVATE,
        quorum=1,
        sensitive=("AUTHENTICATION_METADATA",),
        firs=("FIR-SEC-004",),
        notes=(
            "The authenticator generates the private key; the platform registers only public "
            "material."
        ),
    ),
    _action(
        "CRED.HUMAN_REVOKE",
        domain="credential",
        desk_id="DESK_CREDENTIAL_OPERATIONS",
        console_id=_IDENT,
        object_class="HumanAuthenticator",
        execute=Right.REVOKE,
        quorum=1,
        sensitive=("AUTHENTICATION_METADATA",),
        firs=("FIR-SEC-004",),
        notes=(
            "Never resurrects a revoked credential under the same identity; replacement links "
            "forward."
        ),
    ),
    _action(
        "CRED.HIGH_ASSURANCE_RECOVERY",
        domain="credential",
        desk_id="DESK_RECOVERY",
        console_id=_IDENT,
        object_class="RecoveryDecision",
        execute=Right.ACTIVATE,
        quorum=2,
        four_eyes=True,
        step_up=True,
        assurance="AAL3",
        sensitive=("RECOVERY_EVIDENCE",),
        firs=("FIR-SEC-004", "FIR-TRUST-002"),
        notes=(
            "Recovery restores the ability to authenticate. It never restores a suspended "
            "OrganizationalAuthority."
        ),
    ),
    _action(
        "SESSION.REVOKE",
        domain="session",
        desk_id="DESK_SECURITY_OPERATIONS",
        console_id=_SEC,
        object_class="Session",
        execute=Right.REVOKE,
        quorum=1,
        firs=("FIR-SEC-004",),
    ),
    # -- Privileged access and emergency (PACK-12 lineage, FIR-CTRL-001) --
    _action(
        "JIT.REQUEST",
        domain="privileged",
        desk_id="DESK_PRIVILEGED_ACCESS",
        console_id=_SEC,
        object_class="PrivilegedGrant",
        execute=Right.ACTIVATE,
        quorum=1,
        max_grant_seconds=3600,
        emergency_eligible=False,
        step_up=True,
        firs=("FIR-SEC-004", "FIR-CTRL-001"),
    ),
    _action(
        "EMERGENCY.REQUEST",
        domain="emergency",
        desk_id="DESK_EMERGENCY",
        console_id=_SEC,
        object_class="BreakGlassGrant",
        execute=Right.REQUEST,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=1800,
        step_up=True,
        firs=("FIR-SEC-004", "FIR-CTRL-001"),
    ),
    _action(
        "EMERGENCY.APPROVE",
        domain="emergency",
        desk_id="DESK_EMERGENCY",
        console_id=_SEC,
        object_class="BreakGlassGrant",
        execute=Right.APPROVE,
        quorum=1,
        four_eyes=False,
        emergency_eligible=True,
        max_grant_seconds=1800,
        step_up=True,
        firs=("FIR-SEC-004",),
        notes=(
            "Approver must be distinct from the requester; the controller is a separate principal."
        ),
    ),
    _action(
        "EMERGENCY.ACTIVATE",
        domain="emergency",
        desk_id="DESK_EMERGENCY",
        console_id=_SEC,
        object_class="BreakGlassGrant",
        execute=Right.ACTIVATE,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=1800,
        firs=("FIR-SEC-004",),
        notes="Activation sets an absolute expiry. There is no renewal path.",
    ),
    _action(
        "EMERGENCY.REVOKE",
        domain="emergency",
        desk_id="DESK_EMERGENCY",
        console_id=_SEC,
        object_class="BreakGlassGrant",
        execute=Right.REVOKE,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=1800,
        firs=("FIR-SEC-004",),
    ),
    _action(
        "EMERGENCY.REVIEW",
        domain="emergency",
        desk_id="DESK_AUDIT_OVERSIGHT",
        console_id=_OVER,
        object_class="BreakGlassGrant",
        execute=Right.REVIEW_OR_AUDIT,
        approve=None,
        revoke=Right.RESTORE,
        quorum=0,
        firs=("FIR-SEC-004", "FIR-CTRL-001"),
        notes="Mandatory post-use review. The reviewer may not be an actor of the reviewed grant.",
    ),
    # -- Service identity and key custody (FIR-SEC-004 classes 6..8, FIR-TRUST-003) --
    _action(
        "SERVICE_CRED.ISSUE",
        domain="service_identity",
        desk_id="DESK_SERVICE_IDENTITY",
        console_id=_OPS,
        object_class="ServiceCredential",
        scope_level=ScopeLevel.PLATFORM,
        actor_class=ActorClass.HUMAN,
        execute=Right.ACTIVATE,
        secret=Right.VIEW_OR_EXPORT_SECRET,
        quorum=2,
        four_eyes=True,
        sensitive=("SERVICE_CREDENTIAL_METADATA",),
        firs=("FIR-SEC-004", "FIR-TRUST-003"),
        notes="Delivery is machine-bound. Approval never requires plaintext secret visibility.",
    ),
    _action(
        "SERVICE_CRED.ROTATE",
        domain="service_identity",
        desk_id="DESK_SERVICE_IDENTITY",
        console_id=_OPS,
        object_class="ServiceCredential",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.ROTATE_OR_REPLACE,
        secret=Right.VIEW_OR_EXPORT_SECRET,
        quorum=2,
        four_eyes=True,
        firs=("FIR-SEC-004", "FIR-TRUST-003"),
    ),
    _action(
        "SERVICE_CRED.REVOKE",
        domain="service_identity",
        desk_id="DESK_SECURITY_OPERATIONS",
        console_id=_SEC,
        object_class="ServiceCredential",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.REVOKE,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=1800,
        firs=("FIR-SEC-004",),
        notes=(
            "Immediate containment may be pre-authorised; replacement activation follows full SoD."
        ),
    ),
    _action(
        "KEY.REQUEST_GENERATION",
        domain="key_trust",
        desk_id="DESK_KEY_CUSTODY",
        console_id=_OPS,
        object_class="TrustKeyReference",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.EXECUTE,
        quorum=2,
        four_eyes=True,
        step_up=True,
        assurance="AAL3",
        sensitive=("KEY_METADATA",),
        firs=("FIR-TRUST-002", "FIR-TRUST-003", "FIR-SEC-004"),
        notes=(
            "Approver and auditor need no plaintext material; high-impact classes require quorum."
        ),
    ),
    _action(
        "KEY.ROTATE",
        domain="key_trust",
        desk_id="DESK_KEY_CUSTODY",
        console_id=_OPS,
        object_class="TrustKeyReference",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.ROTATE_OR_REPLACE,
        quorum=2,
        four_eyes=True,
        assurance="AAL3",
        firs=("FIR-TRUST-003",),
    ),
    _action(
        "KEY.MARK_COMPROMISED",
        domain="key_trust",
        desk_id="DESK_SECURITY_OPERATIONS",
        console_id=_SEC,
        object_class="TrustKeyReference",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.SUSPEND_OR_QUARANTINE,
        quorum=1,
        emergency_eligible=True,
        max_grant_seconds=1800,
        firs=("FIR-TRUST-002", "FIR-TRUST-003"),
        notes="Stops new use. Grants no right to inspect unrelated secrets.",
    ),
    _action(
        "KEY.DESTROY",
        domain="key_trust",
        desk_id="DESK_KEY_CUSTODY",
        console_id=_OPS,
        object_class="TrustKeyReference",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.DESTROY,
        quorum=3,
        four_eyes=True,
        assurance="AAL3",
        step_up=True,
        firs=("FIR-TRUST-002", "FIR-TRUST-003"),
        notes=(
            "Retention and decryption-dependency check precedes destruction; no export before "
            "destroy."
        ),
    ),
    _action(
        "KEY.READ_TRUST_STATE",
        domain="key_trust",
        desk_id="DESK_KEY_CUSTODY",
        console_id=_OPS,
        object_class="TrustKeyReference",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.READ_METADATA,
        approve=None,
        revoke=None,
        mutation=False,
        quorum=0,
        firs=("FIR-TRUST-003",),
    ),
    # -- Oversight, privacy, records --
    _action(
        "AUDIT.LOOKUP",
        domain="audit",
        desk_id="DESK_AUDIT_OVERSIGHT",
        console_id=_OVER,
        object_class="ControlEvidenceEvent",
        execute=Right.REVIEW_OR_AUDIT,
        approve=None,
        revoke=None,
        mutation=False,
        quorum=0,
        firs=("FIR-CTRL-001", "FIR-OPS-001"),
        notes=(
            "Read-only by construction: the audit desk holds no mutation right on any object class."
        ),
    ),
    _action(
        "PRIVACY.REVIEW_EXPORT",
        domain="privacy",
        desk_id="DESK_DPO_PRIVACY",
        console_id=_OVER,
        object_class="GovernedExport",
        execute=Right.REVIEW_OR_AUDIT,
        approve=Right.APPROVE,
        revoke=Right.REVOKE,
        quorum=2,
        four_eyes=True,
        sensitive=("PERSONAL_DATA",),
        firs=("FIR-OPS-001", "FIR-SEC-004"),
    ),
    _action(
        "REPORTING.CUSTODY_ACCESS",
        domain="protected_reporting",
        desk_id="DESK_PROTECTED_REPORTING",
        console_id=_OVER,
        object_class="ReporterIdentityCustody",
        execute=Right.VIEW_OR_EXPORT_SECRET,
        secret=Right.VIEW_OR_EXPORT_SECRET,
        quorum=2,
        four_eyes=True,
        assurance="AAL3",
        step_up=True,
        sensitive=("REPORTER_IDENTITY",),
        firs=("FIR-CTRL-001",),
        notes="Separately protected custody; not reachable from ordinary investigation authority.",
    ),
    _action(
        "CASE.OMBUDS_DECIDE",
        domain="casework",
        desk_id="DESK_COMPLAINTS_OMBUDS",
        console_id=_OVER,
        object_class="OmbudsCase",
        quorum=1,
        sensitive=("CASE_CONTENT",),
        firs=("FIR-CTRL-001",),
    ),
    _action(
        "RECORDS.APPLY_RETENTION",
        domain="records",
        desk_id="DESK_RECORDS_RETENTION",
        console_id=_OPS,
        object_class="RecordSeries",
        quorum=2,
        four_eyes=True,
        firs=("FIR-CTRL-001",),
        notes="Retention application never removes audit evidence of the act itself.",
    ),
    _action(
        "PROCUREMENT.APPROVE_VENDOR",
        domain="procurement",
        desk_id="DESK_PROCUREMENT",
        console_id=_OPS,
        object_class="VendorEngagement",
        quorum=2,
        four_eyes=True,
        firs=("FIR-OSS-007", "FIR-CTRL-001"),
        notes="Commercial operations boundary: a vendor engagement creates no party competence.",
    ),
    # -- Domain administration desks --
    _action(
        "MEMBERSHIP.ADMIN_MUTATE",
        domain="membership",
        desk_id="DESK_MEMBERSHIP_ADMIN",
        console_id=_GOV,
        object_class="MembershipRecord",
        quorum=1,
        sensitive=("PERSONAL_DATA",),
        firs=("FIR-GOV-004", "FIR-GOV-005"),
    ),
    _action(
        "OFFICE.ASSIGN_MANDATE",
        domain="offices",
        desk_id="DESK_OFFICES_MANDATES",
        console_id=_GOV,
        object_class="OfficeAssignment",
        quorum=2,
        four_eyes=True,
        firs=("FIR-GOV-005",),
        notes="Party office and public mandate remain distinct; neither derives the other.",
    ),
    _action(
        "ASSEMBLY.PUBLISH_MINUTES",
        domain="assemblies",
        desk_id="DESK_ASSEMBLIES",
        console_id=_GOV,
        object_class="AssemblyMinutes",
        quorum=1,
        firs=("FIR-CTRL-001",),
    ),
    _action(
        "ELECTION.ADMIN_ACTION",
        domain="election_admin",
        desk_id="DESK_ELECTION_ADMIN",
        console_id=_GOV,
        object_class="ElectionAdministrationTask",
        quorum=2,
        four_eyes=True,
        voting_boundary="ELECTION_ADMINISTRATION_ONLY_NO_BALLOT_ACCESS",
        firs=("FIR-GOV-005", "FIR-VOTE-NET-001"),
        notes=(
            "Nomination, filing and election administration are separately authorised; no ballot "
            "access."
        ),
    ),
    _action(
        "FINANCE.APPROVE_PAYMENT",
        domain="finance",
        desk_id="DESK_FINANCE",
        console_id=_WORK,
        object_class="PaymentRequest",
        quorum=2,
        four_eyes=True,
        sensitive=("FINANCIAL_DATA",),
        firs=("FIR-GOV-005",),
        notes="prepare / approve / execute / book / review are separable per scope.",
    ),
    _action(
        "CORRESPONDENCE.SEND_OFFICIAL",
        domain="correspondence",
        desk_id="DESK_CORRESPONDENCE",
        console_id=_WORK,
        object_class="OfficialCorrespondence",
        quorum=1,
        sensitive=("CASE_CONTENT", "PERSONAL_DATA"),
        firs=("FIR-AI-003", "FIR-GOV-004"),
    ),
    _action(
        "AI.REVIEW_DRAFT",
        domain="ai_oversight",
        desk_id="DESK_AI_OVERSIGHT",
        console_id=_WORK,
        object_class="AiDraftProposal",
        quorum=1,
        sensitive=("CASE_CONTENT",),
        firs=("FIR-AI-003",),
        notes="A human review decision is mandatory; the model never holds the execute right.",
    ),
    _action(
        "TRANSPARENCY.PUBLISH",
        domain="transparency",
        desk_id="DESK_TRANSPARENCY_PUBLICATION",
        console_id=_WORK,
        object_class="PublicationItem",
        quorum=2,
        four_eyes=True,
        firs=("FIR-CTRL-001",),
        notes="Publication authority is confined to the actor's own official scope.",
    ),
    _action(
        "CITIZEN_OFFICE.ROUTE_CASE",
        domain="citizen_office",
        desk_id="DESK_CITIZEN_OFFICE",
        console_id=_WORK,
        object_class="CitizenCase",
        quorum=1,
        sensitive=("PERSONAL_DATA", "CASE_CONTENT"),
        firs=("FIR-AI-003", "FIR-CTRL-001"),
    ),
    _action(
        "REPRESENTATIVE.OPEN_DESK_UPDATE",
        domain="representative",
        desk_id="DESK_REPRESENTATIVE_OPEN_DESK",
        console_id=_WORK,
        object_class="RepresentativeDeskEntry",
        quorum=1,
        firs=("FIR-CTRL-001",),
    ),
    _action(
        "MODERATION.DECIDE",
        domain="moderation",
        desk_id="DESK_MODERATION",
        console_id=_WORK,
        object_class="ModerationCase",
        quorum=1,
        sensitive=("CASE_CONTENT",),
        firs=("FIR-CTRL-001",),
    ),
    # -- Platform operations (technical, explicitly non-political) --
    _action(
        "PLATFORM.READ_HEALTH",
        domain="platform",
        desk_id="DESK_PLATFORM_OPERATIONS",
        console_id=_OPS,
        object_class="OperationalHealth",
        scope_level=ScopeLevel.PLATFORM,
        execute=Right.READ_METADATA,
        approve=None,
        revoke=None,
        mutation=False,
        quorum=0,
        firs=("FIR-OPS-001",),
        notes=(
            "Privacy-safe operational state only. Deploy/restart authority grants no domain "
            "authority."
        ),
    ),
    _action(
        "PLATFORM.SERVICE_TASK",
        domain="platform",
        desk_id="DESK_PLATFORM_OPERATIONS",
        console_id=_OPS,
        object_class="OperationalTask",
        scope_level=ScopeLevel.PLATFORM,
        actor_class=ActorClass.SERVICE,
        approve=None,
        revoke=Right.REVOKE,
        quorum=0,
        firs=("FIR-OPS-001", "FIR-CTRL-001"),
        notes="Workload-only action. A human principal is refused on actor-class grounds.",
    ),
)


#: `FIR-CTRL-001` acceptance criterion 1 requires that every administrative or
#: oversight role resolve either to a desk or to an explicit `NO_UI` decision.
NO_UI_DECISIONS: tuple[Mapping[str, str], ...] = (
    {
        "role": "VOTING_TRUSTEE",
        "decision": "NO_UI",
        "rationale": (
            "The Voting Client and the voting trust domain remain outside every administrative "
            "control-plane surface (FIR-CTRL-001 acceptance criterion 7). Trustee key authority is "
            "exercised only through voting-domain components under voting-specific governance."
        ),
        "governing_fir": "FIR-CTRL-001",
    },
    {
        "role": "VOTING_KEY_CUSTODIAN",
        "decision": "NO_UI",
        "rationale": (
            "Voting-domain key material appears in the control plane only as an external governed "
            "reference (FIR-SEC-004 class 9). No control-plane right operates it."
        ),
        "governing_fir": "FIR-SEC-004",
    },
    {
        "role": "UNIVERSAL_SYSTEM_ADMINISTRATOR",
        "decision": "NO_UI",
        "rationale": (
            "Deliberately does not exist. There is no console, desk, role or route that aggregates "
            "the full right set (FIR-CTRL-001 acceptance criterion 9)."
        ),
        "governing_fir": "FIR-CTRL-001",
    },
)


class ActionInventory:
    """Indexed, validated view of the action inventory."""

    def __init__(self, actions: Iterable[ControlAction]) -> None:
        self._by_id: dict[str, ControlAction] = {}
        for action in actions:
            if action.action_id in self._by_id:
                raise InventoryError(f"duplicate action id: {action.action_id}")
            self._by_id[action.action_id] = action
        self._validate()

    def _validate(self) -> None:
        routes: dict[str, str] = {}
        for action in self._by_id.values():
            if action.route in routes:
                raise InventoryError(
                    f"route {action.route} is claimed by both {routes[action.route]} "
                    f"and {action.action_id}"
                )
            routes[action.route] = action.action_id
            if (
                action.secret_visibility_right is not None
                and action.secret_visibility_right is action.required_right_approve
            ):
                raise InventoryError(
                    f"{action.action_id}: secret visibility must not coincide with the "
                    f"approval right"
                )
            if action.voting_domain_boundary == "INSIDE_VOTING_DOMAIN":
                raise InventoryError(
                    f"{action.action_id}: no control-plane action may sit inside the voting "
                    f"trust domain"
                )

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, action_id: object) -> bool:
        return action_id in self._by_id

    def __iter__(self) -> Any:
        return iter(self._by_id.values())

    def get(self, action_id: str) -> ControlAction:
        try:
            return self._by_id[action_id]
        except KeyError:
            # Fail closed: an unmapped action is refused, never executed under a
            # default policy (FIR-CTRL-001 frontend/backend rule).
            raise InventoryError(
                f"action {action_id!r} is not present in the governed inventory"
            ) from None

    def action_ids(self) -> frozenset[str]:
        return frozenset(self._by_id)

    def mutation_ids(self) -> frozenset[str]:
        return frozenset(a.action_id for a in self._by_id.values() if a.mutation)

    def read_ids(self) -> frozenset[str]:
        return frozenset(a.action_id for a in self._by_id.values() if not a.mutation)

    def desks(self) -> frozenset[str]:
        return frozenset(a.desk_id for a in self._by_id.values())

    def consoles(self) -> frozenset[str]:
        return frozenset(a.console_id for a in self._by_id.values())

    def routes(self) -> Mapping[str, str]:
        return {a.route: a.action_id for a in self._by_id.values()}


INVENTORY = ActionInventory(ACTIONS)


def _action_to_obj(action: ControlAction) -> dict[str, Any]:
    return {
        "action_id": action.action_id,
        "domain": action.domain,
        "actor_class": action.actor_class.value,
        "required_authority": {
            "request_right": action.required_right_request.value,
            "approve_right": None
            if action.required_right_approve is None
            else action.required_right_approve.value,
            "execute_right": action.required_right_execute.value,
            "revoke_or_rollback_right": None
            if action.required_right_revoke is None
            else action.required_right_revoke.value,
            "audit_review_right": action.required_right_audit.value,
            "secret_visibility_right": None
            if action.secret_visibility_right is None
            else action.secret_visibility_right.value,
        },
        "organization_scope_level": action.scope_level.value,
        "object_scope": action.object_class,
        "mutation": action.mutation,
        "quorum_required": action.quorum_required,
        "four_eyes_required": action.four_eyes,
        "emergency_eligible": action.emergency_eligible,
        "expiry_seconds": action.max_grant_seconds,
        "commit_time_reauthorization_required": action.commit_time_reauthorization,
        "immutable_evidence_required": action.immutable_evidence_required,
        "console_id": action.console_id,
        "desk_id": action.desk_id,
        "route": action.route,
        "assurance_level": action.assurance_level,
        "step_up_required": action.step_up_required,
        "incompatible_rights": sorted(
            f"{a.value}|{b.value}" for a, b in action.incompatible_rights
        ),
        "sensitive_data_classes": sorted(action.sensitive_data_classes),
        "voting_domain_boundary": action.voting_domain_boundary,
        "governing_fir_refs": list(action.governing_fir_refs),
        "notes": action.notes,
    }


def inventory_to_json_obj(inventory: ActionInventory = INVENTORY) -> dict[str, Any]:
    """Derive the publishable `ctrl_action_inventory.json` payload."""
    actions = sorted(inventory, key=lambda a: a.action_id)
    return {
        "schema": "epd2.ctrl01.action-inventory/1",
        "stage": "CTRL-01",
        "stage_mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
        "generated_from": (
            "services/control-plane-service/src/epd2_control_plane_service/inventory.py"
        ),
        "hard_constraints": [
            "no universal administrator action exists",
            "no action grants hierarchy-derived cross-scope authority",
            "no action operates voting-domain key material or ballot content",
            "every mutation requires commit-time reauthorization and immutable evidence",
        ],
        "counts": {
            "actions_total": len(actions),
            "mutations": len(inventory.mutation_ids()),
            "read_only": len(inventory.read_ids()),
            "consoles": len(inventory.consoles()),
            "desks": len(inventory.desks()),
        },
        "no_ui_decisions": [dict(entry) for entry in NO_UI_DECISIONS],
        "actions": [_action_to_obj(a) for a in actions],
    }
