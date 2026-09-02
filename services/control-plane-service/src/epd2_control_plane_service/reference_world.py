"""A deterministic governed world.

This lives in the package rather than in the test tree on purpose: the CTRL-01
validator executes the same world the tests do, so a gate result and a test
result describe the same runtime rather than two similar ones.

The world is small but structurally complete: two Länder, one Kreis, one
platform scope, and principals whose rights are deliberately narrow. Nobody in
this world holds a right they do not need — a permissive fixture would let a
broken authorization check still pass.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from epd2_control_plane_service.application import ControlPlane, ExecutionOutcome
from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.authority import AuthorityDirectory
from epd2_control_plane_service.breakglass import BreakGlassService
from epd2_control_plane_service.domain import (
    ActorClass,
    AuthorityState,
    CredentialClass,
    CredentialState,
    OrganizationalAuthority,
    Principal,
    Right,
    Scope,
    ScopeLevel,
    ServiceCredential,
    Session,
    SessionState,
    TrustKeyReference,
)
from epd2_control_plane_service.intervention import InterventionService
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory
from epd2_control_plane_service.policy import ControlPolicy
from epd2_control_plane_service.sod import SodEngine

T0 = datetime(2026, 9, 2, 9, 0, 0, tzinfo=UTC)

PLATFORM = Scope(ScopeLevel.PLATFORM, "epd2-platform")
BUND = Scope(ScopeLevel.BUND, "bundesverband")
LAND_BE = Scope(ScopeLevel.LAND, "land-berlin")
LAND_BY = Scope(ScopeLevel.LAND, "land-bayern")
KREIS_BE = Scope(ScopeLevel.KREIS, "kreis-berlin-mitte")

RULE = "SATZUNG-2026.03"


@dataclass(slots=True)
class World:
    plane: ControlPlane
    directory: AuthorityDirectory
    journal: EvidenceJournal
    policy: ControlPolicy

    def at(self, **delta: float) -> datetime:
        return T0 + timedelta(**delta)


def _authority(
    authority_id: str,
    subject: str,
    office: str,
    scope: Scope,
    rights: set[Right],
    action_codes: set[str],
    *,
    state: AuthorityState = AuthorityState.ACTIVE,
    valid_from: datetime = T0 - timedelta(days=30),
    valid_until: datetime | None = None,
    oversight_of: frozenset[str] = frozenset(),
    oversight_decision_scope: str | None = None,
    decision: str = "BESCHLUSS-2026-001",
) -> OrganizationalAuthority:
    return OrganizationalAuthority(
        authority_id=authority_id,
        subject_ref=subject,
        office_code=office,
        scope=scope,
        capabilities=frozenset(rights),
        action_codes=frozenset(action_codes),
        rule_version=RULE,
        source_decision_ref=decision,
        appointed_by_ref=f"ORGAN:{scope.key}",
        valid_from=valid_from,
        valid_until=valid_until,
        state=state,
        evidence_refs=(f"EVID:{authority_id}",),
        oversight_of=oversight_of,
        oversight_decision_scope=oversight_decision_scope,
    )


#: (principal_id, actor_class)
PRINCIPALS: tuple[tuple[str, ActorClass], ...] = (
    ("p.land.be.chair", ActorClass.HUMAN),
    ("p.land.be.deputy", ActorClass.HUMAN),
    ("p.land.be.secretary", ActorClass.HUMAN),
    ("p.land.by.chair", ActorClass.HUMAN),
    ("p.bund.chair", ActorClass.HUMAN),
    ("p.bund.oversight", ActorClass.HUMAN),
    ("p.bund.deputy", ActorClass.HUMAN),
    ("p.bund.treasurer", ActorClass.HUMAN),
    ("p.security.operator", ActorClass.HUMAN),
    ("p.credential.operator", ActorClass.HUMAN),
    ("p.recovery.approver", ActorClass.HUMAN),
    ("p.recovery.second", ActorClass.HUMAN),
    ("p.key.custodian", ActorClass.HUMAN),
    ("p.key.policy.approver", ActorClass.HUMAN),
    ("p.service.owner", ActorClass.HUMAN),
    ("p.privileged.operator", ActorClass.HUMAN),
    ("p.emergency.controller", ActorClass.HUMAN),
    ("p.auditor", ActorClass.HUMAN),
    ("p.ordinary.member", ActorClass.HUMAN),
    ("svc.scheduler", ActorClass.SERVICE),
    ("svc.rogue", ActorClass.SERVICE),
)


def build_world(
    policy: ControlPolicy | None = None,
    inventory: ActionInventory = INVENTORY,
    *,
    emergency_factory: Callable[[ControlPolicy, ActionInventory], BreakGlassService] | None = None,
    honour_request_parameters: bool = False,
    runtime_action_ids: frozenset[str] | None = None,
) -> World:
    policy = policy or ControlPolicy.governed()
    directory = AuthorityDirectory(policy)
    journal = EvidenceJournal(policy)
    emergency = (
        emergency_factory(policy, inventory)
        if emergency_factory
        else BreakGlassService(policy, inventory)
    )
    plane = ControlPlane(
        directory=directory,
        journal=journal,
        policy=policy,
        inventory=inventory,
        sod=SodEngine(policy),
        interventions=InterventionService(policy, inventory),
        emergency=emergency,
        honour_request_parameters=honour_request_parameters,
        runtime_action_ids=runtime_action_ids,
    )

    for principal_id, actor_class in PRINCIPALS:
        plane.register_principal(Principal(principal_id, actor_class, principal_id))
        directory.put_session(
            Session(
                session_id=f"s.{principal_id}",
                principal_id=principal_id,
                state=SessionState.ACTIVE,
                established_at=T0 - timedelta(hours=1),
                assurance_level="AAL2",
            )
        )

    gov_actions = {
        "AUTH.ASSIGN",
        "AUTH.SUSPEND",
        "AUTH.RESTORE",
        "AUTH.REVOKE",
        "AUTH.READ_PROVENANCE",
        "MEMBERSHIP.ADMIN_MUTATE",
        "TRANSPARENCY.PUBLISH",
        "FINANCE.APPROVE_PAYMENT",
    }
    intervention_actions = {
        "INTERVENE.AUTHORITY_SUSPENSION",
        "INTERVENE.REGIONAL_ACTION_RESTRICTION",
        "INTERVENE.TEMPORARY_SUPERVISION",
        "INTERVENE.LIFT",
        "INTERVENE.READ_ACTIVE",
    }

    records = [
        # --- Land Berlin: an ordinary regional board. Requesters and approvers
        # are distinct people; nobody holds request+approve+execute together.
        _authority(
            "a.land.be.chair",
            "p.land.be.chair",
            "LANDESVORSITZ",
            LAND_BE,
            {
                Right.REQUEST,
                Right.EXECUTE,
                Right.SUSPEND_OR_QUARANTINE,
                Right.REVOKE,
                Right.READ_METADATA,
                Right.RESTORE,
            },
            gov_actions,
        ),
        _authority(
            "a.land.be.deputy",
            "p.land.be.deputy",
            "LANDESVORSTAND_STELLV",
            LAND_BE,
            {Right.APPROVE, Right.READ_METADATA},
            gov_actions,
        ),
        _authority(
            "a.land.be.secretary",
            "p.land.be.secretary",
            "LANDESGESCHAEFTSFUEHRUNG",
            LAND_BE,
            {Right.APPROVE, Right.REQUEST, Right.READ_METADATA},
            gov_actions,
        ),
        # --- Land Bayern: identical office, different scope. Must not reach Berlin.
        _authority(
            "a.land.by.chair",
            "p.land.by.chair",
            "LANDESVORSITZ",
            LAND_BY,
            {
                Right.REQUEST,
                Right.EXECUTE,
                Right.APPROVE,
                Right.SUSPEND_OR_QUARANTINE,
                Right.READ_METADATA,
            },
            gov_actions,
        ),
        # --- Bund: holds Bund scope only. No hierarchy-derived reach into a Land.
        _authority(
            "a.bund.chair",
            "p.bund.chair",
            "BUNDESVORSITZ",
            BUND,
            {Right.REQUEST, Right.EXECUTE, Right.APPROVE, Right.READ_METADATA},
            gov_actions | intervention_actions,
        ),
        _authority(
            "a.bund.deputy",
            "p.bund.deputy",
            "BUNDESVORSTAND_STELLV",
            BUND,
            {Right.APPROVE, Right.READ_METADATA},
            gov_actions,
        ),
        _authority(
            "a.bund.treasurer",
            "p.bund.treasurer",
            "BUNDESSCHATZMEISTER",
            BUND,
            {Right.APPROVE, Right.READ_METADATA},
            gov_actions,
        ),
        # --- Bund oversight: an explicit, rule-bound intervention competence over
        # Land Berlin only. This is the only cross-scope grant in the world.
        _authority(
            "a.bund.oversight",
            "p.bund.oversight",
            "BUNDESVORSTAND_AUFSICHT",
            BUND,
            {
                Right.REQUEST,
                Right.APPROVE,
                Right.SUSPEND_OR_QUARANTINE,
                Right.RESTORE,
                Right.READ_METADATA,
            },
            intervention_actions,
            oversight_of=frozenset({LAND_BE.key}),
            oversight_decision_scope=LAND_BE.key,
            decision="BUNDESVORSTAND-BESCHLUSS-2026-014",
        ),
        # --- Security operations: containment only. No office, no restoration.
        _authority(
            "a.security.operator",
            "p.security.operator",
            "SECURITY_OPERATOR",
            PLATFORM,
            {
                Right.REQUEST,
                Right.EXECUTE,
                Right.SUSPEND_OR_QUARANTINE,
                Right.REVOKE,
                Right.READ_METADATA,
            },
            {
                "INTERVENE.SESSION_QUARANTINE",
                "SESSION.REVOKE",
                "SERVICE_CRED.REVOKE",
                "KEY.MARK_COMPROMISED",
            },
            decision="INCIDENT-POLICY-2026-002",
        ),
        _authority(
            "a.security.be",
            "p.security.operator",
            "SECURITY_OPERATOR",
            LAND_BE,
            {
                Right.REQUEST,
                Right.EXECUTE,
                Right.SUSPEND_OR_QUARANTINE,
                Right.REVOKE,
                Right.READ_METADATA,
            },
            {"INTERVENE.SESSION_QUARANTINE", "SESSION.REVOKE"},
            decision="INCIDENT-POLICY-2026-002",
        ),
        # --- Identity/credential operations.
        _authority(
            "a.credential.operator",
            "p.credential.operator",
            "CREDENTIAL_OPERATOR",
            PLATFORM,
            {Right.REQUEST, Right.EXECUTE, Right.ACTIVATE, Right.REVOKE, Right.READ_METADATA},
            {"CRED.HUMAN_ENROLL", "CRED.HUMAN_REVOKE", "CRED.HIGH_ASSURANCE_RECOVERY"},
            decision="IDENTITY-POLICY-2026-003",
        ),
        _authority(
            "a.recovery.approver",
            "p.recovery.approver",
            "RECOVERY_APPROVER",
            PLATFORM,
            {Right.APPROVE, Right.READ_METADATA},
            {"CRED.HIGH_ASSURANCE_RECOVERY", "CRED.HUMAN_ENROLL", "CRED.HUMAN_REVOKE"},
            decision="IDENTITY-POLICY-2026-003",
        ),
        _authority(
            "a.recovery.second",
            "p.recovery.second",
            "IDENTITY_GOVERNANCE_APPROVER",
            PLATFORM,
            {Right.APPROVE, Right.READ_METADATA},
            {"CRED.HIGH_ASSURANCE_RECOVERY"},
            decision="IDENTITY-POLICY-2026-003",
        ),
        # --- Key custody vs key policy approval: deliberately different people.
        _authority(
            "a.key.custodian",
            "p.key.custodian",
            "KEY_CUSTODIAN",
            PLATFORM,
            {
                Right.REQUEST,
                Right.EXECUTE,
                Right.ROTATE_OR_REPLACE,
                Right.DESTROY,
                Right.READ_METADATA,
                Right.VIEW_OR_EXPORT_SECRET,
            },
            {"KEY.REQUEST_GENERATION", "KEY.ROTATE", "KEY.DESTROY", "KEY.READ_TRUST_STATE"},
            decision="KEY-POLICY-2026-004",
        ),
        _authority(
            "a.key.policy.approver",
            "p.key.policy.approver",
            "KEY_POLICY_APPROVER",
            PLATFORM,
            {Right.APPROVE, Right.READ_METADATA},
            {"KEY.REQUEST_GENERATION", "KEY.ROTATE", "KEY.DESTROY"},
            decision="KEY-POLICY-2026-004",
        ),
        _authority(
            "a.key.second.approver",
            "p.service.owner",
            "SERVICE_OWNER",
            PLATFORM,
            {Right.REQUEST, Right.APPROVE, Right.READ_METADATA},
            {"KEY.DESTROY", "KEY.ROTATE", "SERVICE_CRED.ISSUE", "SERVICE_CRED.ROTATE"},
            decision="SERVICE-POLICY-2026-005",
        ),
        _authority(
            "a.service.issuer",
            "p.credential.operator",
            "SERVICE_CREDENTIAL_ISSUER",
            PLATFORM,
            {Right.EXECUTE, Right.ACTIVATE, Right.ROTATE_OR_REPLACE, Right.READ_METADATA},
            {"SERVICE_CRED.ISSUE", "SERVICE_CRED.ROTATE"},
            decision="SERVICE-POLICY-2026-005",
        ),
        _authority(
            "a.service.approver",
            "p.privileged.operator",
            "PLATFORM_APPROVER",
            PLATFORM,
            {Right.APPROVE, Right.READ_METADATA},
            {"SERVICE_CRED.ISSUE", "SERVICE_CRED.ROTATE", "KEY.REQUEST_GENERATION"},
            decision="SERVICE-POLICY-2026-005",
        ),
        # --- Privileged access / emergency.
        _authority(
            "a.privileged.operator",
            "p.privileged.operator",
            "PRIVILEGED_ACCESS_OPERATOR",
            PLATFORM,
            {Right.REQUEST, Right.EXECUTE, Right.ACTIVATE, Right.REVOKE, Right.READ_METADATA},
            {"JIT.REQUEST", "EMERGENCY.REQUEST", "EMERGENCY.ACTIVATE", "EMERGENCY.REVOKE"},
            decision="PACK12-POLICY-2026-006",
        ),
        _authority(
            "a.emergency.controller",
            "p.emergency.controller",
            "EMERGENCY_CONTROLLER",
            PLATFORM,
            {Right.APPROVE, Right.EXECUTE, Right.READ_METADATA},
            {"EMERGENCY.APPROVE", "EMERGENCY.REQUEST", "EMERGENCY.ACTIVATE"},
            decision="PACK12-POLICY-2026-006",
        ),
        # --- A protected-reporting desk authority that deliberately lacks the
        # secret-visibility right the action requires.
        _authority(
            "a.reporting.intake",
            "p.privileged.operator",
            "PROTECTED_REPORTING_INTAKE",
            LAND_BE,
            {Right.REQUEST, Right.APPROVE, Right.READ_METADATA},
            {"REPORTING.CUSTODY_ACCESS"},
            decision="OVERSIGHT-POLICY-2026-007",
        ),
        # --- Independent audit: read/review only. Holds no mutation right at all.
        _authority(
            "a.auditor",
            "p.auditor",
            "INDEPENDENT_AUDITOR",
            PLATFORM,
            {Right.REVIEW_OR_AUDIT, Right.READ_METADATA},
            {
                "AUDIT.LOOKUP",
                "EMERGENCY.REVIEW",
                "AUTH.READ_PROVENANCE",
                "KEY.READ_TRUST_STATE",
                "INTERVENE.READ_ACTIVE",
                "PLATFORM.READ_HEALTH",
            },
            decision="OVERSIGHT-POLICY-2026-007",
        ),
        _authority(
            "a.auditor.be",
            "p.auditor",
            "INDEPENDENT_AUDITOR",
            LAND_BE,
            {Right.REVIEW_OR_AUDIT, Right.READ_METADATA},
            {"AUDIT.LOOKUP", "AUTH.READ_PROVENANCE", "INTERVENE.READ_ACTIVE"},
            decision="OVERSIGHT-POLICY-2026-007",
        ),
        # --- A workload identity. It can run its own platform task and nothing else.
        _authority(
            "a.svc.scheduler",
            "svc.scheduler",
            "WORKLOAD",
            PLATFORM,
            {Right.REQUEST, Right.EXECUTE, Right.READ_METADATA},
            {"PLATFORM.SERVICE_TASK"},
            decision="SERVICE-POLICY-2026-005",
        ),
        # --- A workload that (incorrectly) claims a human action's rights. The
        # actor-class guard, not the right set, is what must refuse it.
        _authority(
            "a.svc.rogue",
            "svc.rogue",
            "WORKLOAD",
            LAND_BE,
            {Right.REQUEST, Right.EXECUTE, Right.APPROVE, Right.READ_METADATA},
            gov_actions,
            decision="SERVICE-POLICY-2026-005",
        ),
    ]
    for record in records:
        directory.record_authority(
            record, recorded_at=T0 - timedelta(days=30), recorded_by="bootstrap"
        )

    for principal_id, actor_class in PRINCIPALS:
        if actor_class is ActorClass.HUMAN:
            directory.put_human_credential(
                f"cred.{principal_id}", principal_id, CredentialState.ACTIVE
            )
    directory.put_service_credential(
        ServiceCredential(
            credential_id="svc.cred.scheduler",
            holder_service="svc.scheduler",
            credential_class=CredentialClass.SERVICE_WORKLOAD,
            state=CredentialState.ACTIVE,
            scope=PLATFORM,
        )
    )
    directory.put_key_reference(
        TrustKeyReference(
            key_reference_id="key.platform.signing.1",
            key_class="PLATFORM_SIGNING",
            credential_class=CredentialClass.PLATFORM_KEY,
            algorithm="ES384",
            trust_state="CURRENT",
            custody_policy_ref="KEY-POLICY-2026-004",
            quorum_m=2,
            quorum_n=4,
        )
    )
    directory.put_key_reference(
        TrustKeyReference(
            key_reference_id="key.voting.trustee.1",
            key_class="VOTING_TRUSTEE",
            credential_class=CredentialClass.VOTING_DOMAIN,
            algorithm="Ed25519",
            trust_state="EXTERNAL_GOVERNED_REFERENCE",
            custody_policy_ref="VOTING-TRUSTEE-POLICY",
            exportable=False,
        )
    )

    return World(plane=plane, directory=directory, journal=journal, policy=policy)


def run_governed_flow(
    world: World,
    *,
    request_id: str,
    action_id: str,
    requester: str,
    approvers: tuple[str, ...],
    executor: str,
    scope: Scope,
    object_ref: str = "object.1",
    moment: datetime | None = None,
    commit_moment: datetime | None = None,
    auditor_id: str | None = None,
) -> ExecutionOutcome:
    """Drive one complete REQUEST -> APPROVE* -> EXECUTE flow."""
    now = moment or T0
    world.plane.submit_request(
        request_id=request_id,
        action_id=action_id,
        principal_id=requester,
        session_id=f"s.{requester}",
        scope=scope,
        object_ref=object_ref,
        purpose="governed test flow",
        moment=now,
    )
    for approver in approvers:
        world.plane.approve(
            request_id=request_id,
            principal_id=approver,
            session_id=f"s.{approver}",
            moment=now + timedelta(minutes=1),
        )
    return world.plane.execute(
        request_id=request_id,
        principal_id=executor,
        session_id=f"s.{executor}",
        moment=commit_moment or (now + timedelta(minutes=2)),
        auditor_id=auditor_id,
    )
