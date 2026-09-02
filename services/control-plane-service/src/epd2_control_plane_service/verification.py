"""The governed check suite.

One definition of "checked" is shared by three consumers: the CTRL-01 gates, the
W11 mutation suite, and the preseal validator. A mutation is "detected" when it
makes at least one of these checks fail, so the anti-cheat evidence is a
statement about the same checks that produce the gate results — not a parallel
set of assertions that could drift.

Every check is written to fail *closed*: an exception inside a check is a
failure, never a skip.
"""

from __future__ import annotations

import hashlib
import traceback
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace
from datetime import timedelta
from typing import Any

from epd2_control_plane_service import SELF_STATE_ALLOWED
from epd2_control_plane_service.audit import (
    GENESIS_PREVIOUS_HASH,
    ControlEvidenceEvent,
)
from epd2_control_plane_service.breakglass import BreakGlassService
from epd2_control_plane_service.domain import (
    ActorClass,
    AuthorityState,
    CredentialState,
    InterventionType,
    Right,
    ScopeLevel,
    SessionState,
)
from epd2_control_plane_service.exceptions import ControlPlaneError
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory
from epd2_control_plane_service.policy import ControlPolicy
from epd2_control_plane_service.reference_world import (
    BUND,
    LAND_BE,
    LAND_BY,
    PLATFORM,
    T0,
    World,
    _authority,
    build_world,
)

__all__ = [
    "CHECKS",
    "CHECK_IDS",
    "FORBIDDEN_SELF_STATES",
    "CheckResult",
    "Scenario",
    "recompute_chain",
    "run_checks",
    "suite_digest",
]

#: Claims a preseal candidate may never make about itself.
FORBIDDEN_SELF_STATES: tuple[str, ...] = (
    "CTRL ACCEPTED",
    "CTRL CLOSED",
    "PRODUCTION READY",
    "FINAL SEC PASS",
    "BSI CERTIFIED",
    "CC CERTIFIED",
    "EAL4",
    "LEGALLY ACTIVATED",
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    check_id: str
    passed: bool
    detail: str


@dataclass(slots=True)
class Scenario:
    """Everything a mutation may perturb.

    Defaults describe the governed baseline; the W11 suite constructs mutated
    scenarios by overriding exactly one field at a time.
    """

    policy: ControlPolicy = field(default_factory=ControlPolicy.governed)
    inventory: ActionInventory = INVENTORY
    #: Applied to the world after construction (data-level mutations).
    world_mutator: Callable[[World], None] | None = None
    #: Applied to the journal after a governed flow ran (evidence tampering).
    journal_mutator: Callable[[World], None] | None = None
    #: Replaces the break-glass service (used to inject a renewal path).
    emergency_factory: Callable[[ControlPolicy, ActionInventory], BreakGlassService] | None = None
    #: Runtime routes claimed by the running service, if they differ from the
    #: inventory (used by the "undocumented endpoint" mutation).
    runtime_action_ids: frozenset[str] | None = None
    #: Artifact manifest mismatches reported by the freeze check.
    freeze_mismatches: tuple[str, ...] = ()
    #: Text scanned for forbidden self-state claims.
    self_state_text: str = " ".join(SELF_STATE_ALLOWED)
    #: Restriction records that reached the runtime from persistence rather than
    #: through the intervention service (a NULL `valid_until` row, for example).
    injected_restrictions: tuple[Any, ...] = ()
    #: Models a runtime that merges caller-supplied request parameters onto the
    #: acting authority (the mass-assignment defect).
    honour_request_parameters: bool = False
    #: A recorded freeze manifest and the root to verify it against. When set,
    #: the freeze check re-hashes the real files instead of reporting a constant.
    freeze_manifest: Mapping[str, Mapping[str, Any]] | None = None
    freeze_root: Any = None

    def world(self) -> World:
        world = build_world(
            self.policy,
            self.inventory,
            emergency_factory=self.emergency_factory,
            honour_request_parameters=self.honour_request_parameters,
            runtime_action_ids=self.runtime_action_ids,
        )
        if self.world_mutator is not None:
            self.world_mutator(world)
        return world


def recompute_chain(
    records: Sequence[ControlEvidenceEvent], anchor: tuple[int, str] | None = None
) -> tuple[bool, str]:
    """Independent chain recomputation.

    Deliberately does not consult the policy: a candidate that switched
    immutability enforcement off must still be caught here.

    `anchor` is the (count, head) pair observed at append time. Without it, two
    realistic tampering shapes survive a chain walk: deleting the newest record,
    and rewriting a record while recomputing every hash forward. Both leave a
    chain that is internally perfect, and both disagree with the anchor.
    """
    if anchor is not None:
        expected_count, expected_head = anchor
        if len(records) != expected_count:
            return (
                False,
                f"record count {len(records)} does not match the {expected_count} appended",
            )
        actual_head = records[-1].event_hash if records else GENESIS_PREVIOUS_HASH
        if actual_head != expected_head:
            return False, "chain head does not match the append-time anchor"
    previous = GENESIS_PREVIOUS_HASH
    for index, record in enumerate(records, start=1):
        if record.sequence != index:
            return False, f"sequence break at position {index}"
        if record.previous_event_hash != previous:
            return False, f"chain break at sequence {record.sequence}"
        if record.compute_hash() != record.event_hash:
            return False, f"record {record.sequence} was rewritten after sealing"
        previous = record.event_hash
    return True, "chain intact"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _refused(call: Callable[[], Any]) -> tuple[bool, str]:
    """True when the call was refused. A call that succeeds is the failure."""
    try:
        call()
    except ControlPlaneError as error:
        return True, error.reason_code
    except Exception as error:
        return True, type(error).__name__
    return False, "permitted"


def _governed_assign(world: World, request_id: str = "chk-assign") -> None:
    world.plane.submit_request(
        request_id=request_id,
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="governed check",
        moment=T0,
    )
    for approver in ("p.land.be.deputy", "p.land.be.secretary"):
        world.plane.approve(
            request_id=request_id,
            principal_id=approver,
            session_id=f"s.{approver}",
            moment=T0 + timedelta(minutes=1),
        )


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def check_inventory_congruent(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    runtime = (
        scenario.runtime_action_ids
        if scenario.runtime_action_ids is not None
        else world.plane.runtime_mutation_ids()
    )
    declared = scenario.inventory.mutation_ids()
    missing = sorted(runtime - declared)
    orphan = sorted(declared - runtime)
    ok = not missing and not orphan
    return CheckResult(
        "CHK-INVENTORY-CONGRUENT",
        ok,
        "runtime and inventory agree" if ok else f"runtime-only={missing} inventory-only={orphan}",
    )


def check_no_universal_admin(scenario: Scenario) -> CheckResult:
    """No authority or action aggregates administrative power.

    Three shapes are rejected, not one. A real root account is rarely given the
    auditor right and rarely needs read-only actions, so "holds all twelve
    rights" and "holds every action id" are the shapes that never appear in
    practice; what appears is every *mutating* action code, or every right
    except review.
    """
    world = scenario.world()
    every_right = set(Right)
    operative_rights = every_right - {Right.REVIEW_OR_AUDIT}
    all_mutations = scenario.inventory.mutation_ids()
    offenders: list[str] = []
    for entry in world.directory.read_model(T0)["current_organizational_authority"]:
        rights = {Right(r) for r in entry["capabilities"]}
        codes = set(entry["action_codes"])
        if rights >= every_right:
            offenders.append(f"{entry['authority_id']}:all-rights")
        if rights >= operative_rights:
            offenders.append(f"{entry['authority_id']}:every-operative-right")
        if all_mutations and codes >= all_mutations:
            offenders.append(f"{entry['authority_id']}:every-mutating-action")
    for action in scenario.inventory:
        held = {
            action.required_right_request,
            action.required_right_execute,
            action.required_right_audit,
        }
        held |= {
            r
            for r in (action.required_right_approve, action.required_right_revoke)
            if r is not None
        }
        if held >= every_right:
            offenders.append(f"{action.action_id}:action-holds-all-rights")
    return CheckResult(
        "CHK-NO-UNIVERSAL-ADMIN",
        not offenders,
        "no universal administrator"
        if not offenders
        else f"universal authority present: {sorted(set(offenders))}",
    )


def check_scope_isolation(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-scope",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.by.chair",
            session_id="s.p.land.by.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="cross-Land",
            moment=T0,
        )
    )
    return CheckResult("CHK-SCOPE-ISOLATION", refused, code)


def check_no_implicit_bund_takeover(scenario: Scenario) -> CheckResult:
    """A cross-scope oversight grant is one decision over one target scope.

    The probe uses `p.bund.oversight`, the world's only oversight holder, and
    widens its grant to several scopes. If the runtime honours the widened
    grant, hierarchy has become inheritance. A Bund principal with no oversight
    grant at all would be refused by ordinary scope isolation and would prove
    nothing about this rule, so it is deliberately not the subject here.
    """
    world = scenario.world()
    oversight = world.directory.current_authority("a.bund.oversight")
    if oversight is None:
        return CheckResult(
            "CHK-NO-IMPLICIT-BUND-TAKEOVER", False, "no oversight authority in the world"
        )

    # Baseline: the single-scope grant must still work, or the probe below would
    # pass for the wrong reason.
    baseline = world.directory.resolve(
        subject_ref="p.bund.oversight",
        required_right=Right.REQUEST,
        action_id="INTERVENE.REGIONAL_ACTION_RESTRICTION",
        scope=LAND_BE,
        moment=T0,
    )
    if not baseline.granted:
        return CheckResult(
            "CHK-NO-IMPLICIT-BUND-TAKEOVER",
            False,
            f"the governed single-scope oversight grant does not resolve: {baseline.reason_code}",
        )

    honoured: list[str] = []

    # Vector 1: widen the grant to several scopes.
    widened = dataclass_replace(
        oversight, oversight_of=frozenset({LAND_BE.key, LAND_BY.key, BUND.key, PLATFORM.key})
    )
    world.directory.record_authority(widened, recorded_at=T0, recorded_by="check-probe")
    if world.directory.resolve(
        subject_ref="p.bund.oversight",
        required_right=Right.REQUEST,
        action_id="INTERVENE.REGIONAL_ACTION_RESTRICTION",
        scope=LAND_BY,
        moment=T0,
    ).granted:
        honoured.append("widened-to-several-scopes")

    # Vector 2: keep one scope, but point it somewhere the decision never named.
    repointed = dataclass_replace(oversight, oversight_of=frozenset({LAND_BY.key}))
    world.directory.record_authority(repointed, recorded_at=T0, recorded_by="check-probe")
    if world.directory.resolve(
        subject_ref="p.bund.oversight",
        required_right=Right.REQUEST,
        action_id="INTERVENE.REGIONAL_ACTION_RESTRICTION",
        scope=LAND_BY,
        moment=T0,
    ).granted:
        honoured.append("re-pointed-away-from-the-source-decision")

    return CheckResult(
        "CHK-NO-IMPLICIT-BUND-TAKEOVER",
        not honoured,
        "oversight is honoured only for the scope its source decision names"
        if not honoured
        else f"oversight grant honoured beyond its decision: {honoured}",
    )


def check_self_approval(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    # The secretary holds BOTH the request and the approve right, so the only
    # thing that can refuse this is the self-approval rule itself.
    world.plane.submit_request(
        request_id="chk-self",
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.secretary",
        session_id="s.p.land.be.secretary",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="self approval",
        moment=T0,
    )
    refused, code = _refused(
        lambda: world.plane.approve(
            request_id="chk-self",
            principal_id="p.land.be.secretary",
            session_id="s.p.land.be.secretary",
            moment=T0 + timedelta(minutes=1),
        )
    )
    return CheckResult("CHK-SELF-APPROVAL-REJECTED", refused, code)


def check_quorum(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    action = scenario.inventory.get("AUTH.ASSIGN")
    if action.quorum_required < 2:
        return CheckResult(
            "CHK-QUORUM-ENFORCED", False, f"AUTH.ASSIGN quorum reduced to {action.quorum_required}"
        )
    world.plane.submit_request(
        request_id="chk-quorum",
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="single approval",
        moment=T0,
    )
    world.plane.approve(
        request_id="chk-quorum",
        principal_id="p.land.be.deputy",
        session_id="s.p.land.be.deputy",
        moment=T0 + timedelta(minutes=1),
    )
    refused, code = _refused(
        lambda: world.plane.execute(
            request_id="chk-quorum",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            moment=T0 + timedelta(minutes=2),
        )
    )
    return CheckResult("CHK-QUORUM-ENFORCED", refused, code)


def check_commit_time_reauthorization(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _governed_assign(world, "chk-reauth")
    # An APPROVER loses authority after approving. The executor is untouched, so
    # only the commit-time re-validation of approvals can catch this.
    world.directory.set_authority_state(
        "a.land.be.deputy", AuthorityState.REVOKED, recorded_at=T0, recorded_by="governance"
    )
    refused, code = _refused(
        lambda: world.plane.execute(
            request_id="chk-reauth",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            moment=T0 + timedelta(minutes=5),
        )
    )
    return CheckResult("CHK-COMMIT-TIME-REAUTH", refused, code)


def check_revoked_authority_refused(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.REVOKED, recorded_at=T0, recorded_by="governance"
    )
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-revoked",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="revoked authority",
            moment=T0,
        )
    )
    return CheckResult("CHK-REVOKED-AUTHORITY-REFUSED", refused, code)


def _open_restriction(world: World, codes: Iterable[str] = ("AUTH.ASSIGN",)):  # type: ignore[no-untyped-def]
    return world.plane.interventions.open_restriction(
        restriction_id="chk-restr",
        intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
        target_scope=LAND_BE,
        affected_action_codes=set(codes),
        valid_from=T0,
        valid_until=T0 + timedelta(days=30),
        reason_code="GOV_INTERVENTION_ONGOING_REVIEW",
        rule_version="SATZUNG-2026.03",
        decision_ref="BUNDESVORSTAND-BESCHLUSS-2026-030",
        initiating_authority_id="a.bund.oversight",
        approving_authority_id="a.bund.chair",
        notification_evidence_ref="NOTIF-2026-030",
        review_deadline=T0 + timedelta(days=14),
    )


def check_intervention_enforced(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    world.directory.put_restriction(_open_restriction(world))
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-restricted",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="frozen action",
            moment=T0 + timedelta(days=1),
        )
    )
    return CheckResult("CHK-INTERVENTION-ENFORCED", refused, code)


def check_no_coarse_regional_disable(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    refused, code = _refused(lambda: _open_restriction(world, codes=("*", "EVERYTHING")))
    empty_refused, _ = _refused(lambda: _open_restriction(world, codes=()))
    ok = refused and empty_refused and not any("DISABLE" in t.value for t in InterventionType)
    return CheckResult("CHK-NO-COARSE-REGIONAL-DISABLE", ok, code)


def check_indefinite_intervention_impossible(scenario: Scenario) -> CheckResult:
    world = scenario.world()

    def _forever() -> Any:
        return world.plane.interventions.open_restriction(
            restriction_id="chk-forever",
            intervention_type=InterventionType.REGIONAL_ACTION_RESTRICTION,
            target_scope=LAND_BE,
            affected_action_codes={"AUTH.ASSIGN"},
            valid_from=T0,
            valid_until=None,  # type: ignore[arg-type]
            reason_code="GOV_INTERVENTION_ONGOING_REVIEW",
            rule_version="SATZUNG-2026.03",
            decision_ref="BESCHLUSS",
            initiating_authority_id="a.bund.oversight",
            approving_authority_id="a.bund.chair",
            notification_evidence_ref="NOTIF",
            review_deadline=T0 + timedelta(days=14),
        )

    refused, code = _refused(_forever)
    # Persistence can still hand the runtime a row the constructor would have
    # rejected, so stored restrictions are re-checked rather than trusted.
    indefinite = [
        getattr(r, "restriction_id", "<unknown>")
        for r in (*scenario.injected_restrictions, *world.directory.restrictions())
        if getattr(r, "valid_until", None) is None
    ]
    ok = refused and not indefinite
    return CheckResult(
        "CHK-INTERVENTION-TIME-BOUNDED",
        ok,
        code if not indefinite else f"indefinite restriction(s) present: {indefinite}",
    )


def _activated_grant(world: World, grant_id: str = "chk-grant") -> None:
    world.plane.emergency.request(
        grant_id=grant_id,
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="governed check incident",
        scope=PLATFORM,
        action_codes={"SERVICE_CRED.REVOKE"},
        requested_at=T0,
    )
    world.plane.emergency.approve(grant_id, approver_id="p.emergency.controller", approved_at=T0)
    world.plane.emergency.activate(grant_id, activated_at=T0)


def check_emergency_expiry(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _activated_grant(world)
    refused, code = _refused(
        lambda: world.plane.emergency.use(
            "chk-grant",
            action_id="SERVICE_CRED.REVOKE",
            scope=PLATFORM,
            moment=T0 + timedelta(hours=4),
            use_ref="chk",
        )
    )
    return CheckResult("CHK-EMERGENCY-EXPIRY", refused, code)


def check_emergency_not_renewable(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    emergency = world.plane.emergency
    _activated_grant(world, "chk-renew")
    emergency.expire_due(T0 + timedelta(hours=4))
    has_renew = any(hasattr(emergency, name) for name in ("renew", "extend", "prolong"))
    refused, code = _refused(
        lambda: emergency.activate("chk-renew", activated_at=T0 + timedelta(hours=4))
    )
    ok = refused and not has_renew
    return CheckResult(
        "CHK-EMERGENCY-NOT-RENEWABLE",
        ok,
        code if not has_renew else "a renewal path exists on the grant service",
    )


def check_emergency_scope(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _activated_grant(world, "chk-scope-grant")
    refused, code = _refused(
        lambda: world.plane.emergency.use(
            "chk-scope-grant",
            action_id="KEY.MARK_COMPROMISED",
            scope=PLATFORM,
            moment=T0 + timedelta(minutes=1),
            use_ref="chk",
        )
    )
    return CheckResult("CHK-EMERGENCY-SCOPE", refused, code)


def check_actor_class(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-actorclass",
            action_id="AUTH.ASSIGN",
            principal_id="svc.rogue",
            session_id="s.svc.rogue",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="workload as administrator",
            moment=T0,
        )
    )
    # A workload class belongs only to platform operations. A party-governance,
    # oversight or work-desk action reclassified as workload-only would let a
    # service identity discharge a human decision.
    human_only_consoles = {
        "CONSOLE_GOVERNANCE",
        "CONSOLE_OVERSIGHT",
        "CONSOLE_WORKDESK",
        "CONSOLE_IDENTITY",
    }
    misclassified = sorted(
        a.action_id
        for a in scenario.inventory
        if a.actor_class is ActorClass.SERVICE
        and (a.console_id in human_only_consoles or a.scope_level is not ScopeLevel.PLATFORM)
    )
    ok = refused and not misclassified
    return CheckResult(
        "CHK-ACTOR-CLASS-SEPARATION",
        ok,
        code
        if not misclassified
        else f"human desk actions reclassified as workload-only: {misclassified}",
    )


def check_secret_visibility_separation(scenario: Scenario) -> CheckResult:
    """An approver that also holds the secret-visibility right must be refused
    for an action whose inventory entry declares that right (SOD-04)."""
    world = scenario.world()
    world.directory.record_authority(
        _authority(
            "a.approver.with.secret",
            "p.recovery.approver",
            "PLATFORM_APPROVER_WITH_SECRET",
            PLATFORM,
            {Right.APPROVE, Right.VIEW_OR_EXPORT_SECRET, Right.READ_METADATA},
            {"SERVICE_CRED.ISSUE"},
        ),
        recorded_at=T0,
        recorded_by="check",
    )
    world.plane.submit_request(
        request_id="chk-secret",
        action_id="SERVICE_CRED.ISSUE",
        principal_id="p.service.owner",
        session_id="s.p.service.owner",
        scope=PLATFORM,
        object_ref="svc.cred.scheduler",
        purpose="issue service credential",
        moment=T0,
    )
    refused, code = _refused(
        lambda: world.plane.approve(
            request_id="chk-secret",
            principal_id="p.recovery.approver",
            session_id="s.p.recovery.approver",
            moment=T0 + timedelta(minutes=1),
        )
    )
    return CheckResult("CHK-SECRET-VISIBILITY-SEPARATION", refused, code)


def check_session_state(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    world.directory.set_session_state("s.p.land.be.chair", SessionState.QUARANTINED)
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-session",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="quarantined session",
            moment=T0,
        )
    )
    return CheckResult("CHK-SESSION-STATE-ENFORCED", refused, code)


def check_credential_state(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _governed_assign(world, "chk-cred")
    world.directory.set_human_credential_state("cred.p.land.be.chair", CredentialState.REVOKED)
    refused, code = _refused(
        lambda: world.plane.execute(
            request_id="chk-cred",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            moment=T0 + timedelta(minutes=5),
        )
    )
    return CheckResult("CHK-CREDENTIAL-STATE-ENFORCED", refused, code)


def check_fail_closed_on_unknown(scenario: Scenario) -> CheckResult:
    """No session context means authority state cannot be established."""
    world = scenario.world()
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-failclosed",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id=None,
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="unknown authority state",
            moment=T0,
        )
    )
    return CheckResult("CHK-FAIL-CLOSED-ON-UNKNOWN", refused, code)


def check_voting_boundary(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    refused, code = _refused(
        lambda: world.plane.submit_request(
            request_id="chk-voting",
            action_id="KEY.ROTATE",
            principal_id="p.key.custodian",
            session_id="s.p.key.custodian",
            scope=PLATFORM,
            object_ref="key.voting.trustee.1",
            purpose="operate trustee key",
            moment=T0,
        )
    )
    voting_actions = [
        a.action_id
        for a in scenario.inventory
        if a.voting_domain_boundary == "INSIDE_VOTING_DOMAIN"
    ]
    ok = refused and not voting_actions
    return CheckResult(
        "CHK-VOTING-BOUNDARY",
        ok,
        code if not voting_actions else f"in-domain actions {voting_actions}",
    )


def check_privacy_minimization(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    refused, code = _refused(
        lambda: world.journal.append(
            occurred_at=T0,
            actor_ref="p.land.be.chair",
            actor_class="HUMAN",
            authority_basis="a.land.be.chair",
            action_id="AUTH.ASSIGN",
            scope_key=LAND_BE.key,
            object_ref="o",
            result="EXECUTED",
            reason_code="CTRL_AUTHORIZED",
            correlation_ref="c",
            attributes={"voting_member_id": "m-1"},
        )
    )
    return CheckResult("CHK-PRIVACY-MINIMIZATION", refused, code)


def check_evidence_emitted(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _governed_assign(world, "chk-evidence")
    world.plane.execute(
        request_id="chk-evidence",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        moment=T0 + timedelta(minutes=5),
    )
    executed = world.journal.find(action_id="AUTH.ASSIGN", result="EXECUTED")
    ok = (
        len(executed) == 1 and bool(executed[0].authority_basis) and executed[0].approval_refs != ()
    )
    return CheckResult("CHK-EVIDENCE-EMITTED", ok, f"{len(executed)} executed record(s)")


def check_evidence_immutable(scenario: Scenario) -> CheckResult:
    world = scenario.world()
    _governed_assign(world, "chk-immutable")
    world.plane.execute(
        request_id="chk-immutable",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        moment=T0 + timedelta(minutes=5),
    )
    anchor = world.journal.anchor()
    if scenario.journal_mutator is not None:
        scenario.journal_mutator(world)
    intact, detail = recompute_chain(world.journal.records(), anchor)
    return CheckResult("CHK-EVIDENCE-IMMUTABLE", intact, detail)


#: Writers the directory journal may legitimately record outside a governed
#: control act: the bootstrap load, and the check harness's own probes.
GOVERNED_DIRECTORY_WRITERS: frozenset[str] = frozenset({"bootstrap", "check-probe"})


def check_no_direct_state_mutation(scenario: Scenario) -> CheckResult:
    """Every authority state change must be attributable to a governed act.

    A change written straight into the directory — the "direct DB mutation
    accepted as a control action" attack — carries a writer the governed set
    does not contain. One such write is enough to fail this check; there is no
    tolerance budget, because a single un-evidenced authority change is exactly
    the thing being prevented.
    """
    world = scenario.world()
    _governed_assign(world, "chk-direct")
    world.plane.execute(
        request_id="chk-direct",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        moment=T0 + timedelta(minutes=5),
    )
    offenders = sorted(
        {
            r.recorded_by
            for r in world.directory.journal()
            if r.recorded_by not in GOVERNED_DIRECTORY_WRITERS
        }
    )
    return CheckResult(
        "CHK-NO-DIRECT-STATE-MUTATION",
        not offenders,
        "every directory write is attributable"
        if not offenders
        else f"un-evidenced directory writer(s): {offenders}",
    )


def check_no_mass_assignment(scenario: Scenario) -> CheckResult:
    """Request parameters must not be able to widen authority.

    The probe submits a request carrying privileged-looking parameters and then
    asks whether the acting principal gained anything: a right it did not hold,
    or reach into a scope it did not cover. A runtime that merges caller fields
    onto the authority record fails here.
    """
    world = scenario.world()
    before = world.directory.resolve(
        subject_ref="p.land.by.chair",
        required_right=Right.REQUEST,
        action_id="AUTH.ASSIGN",
        scope=LAND_BE,
        moment=T0,
    )
    injected = {
        "capabilities": "ALL",
        "oversight_of": f"{LAND_BE.key},{BUND.key}",
        "quorum_required": "0",
    }
    submitted = True
    try:
        world.plane.submit_request(
            request_id="chk-massassign",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.by.chair",
            session_id="s.p.land.by.chair",
            scope=LAND_BY,
            object_ref="authority.target",
            purpose="mass assignment attempt",
            moment=T0,
            parameters=injected,
        )
    except ControlPlaneError:
        # Refusing the unknown parameters outright is the governed behaviour.
        submitted = False

    after_scope = world.directory.resolve(
        subject_ref="p.land.by.chair",
        required_right=Right.REQUEST,
        action_id="AUTH.ASSIGN",
        scope=LAND_BE,
        moment=T0,
    )
    after_right = world.directory.resolve(
        subject_ref="p.land.by.chair",
        required_right=Right.VIEW_OR_EXPORT_SECRET,
        action_id="AUTH.ASSIGN",
        scope=LAND_BY,
        moment=T0,
    )
    widened_scope = after_scope.granted and not before.granted
    widened_right = after_right.granted
    ok = not widened_scope and not widened_right
    detail = (
        "parameters changed nothing" if ok else "request parameters widened the acting authority"
    )
    if ok and submitted:
        detail = "parameters accepted from the governed set only; authority unchanged"
    return CheckResult("CHK-NO-MASS-ASSIGNMENT", ok, detail)


def check_freeze_same_bytes(scenario: Scenario) -> CheckResult:
    """Recompute the recorded manifest against the files on disk.

    When a manifest and a root are supplied the files are re-hashed here, so the
    result is a measurement. `freeze_mismatches` remains available for a caller
    that has already performed the comparison.
    """
    mismatches = tuple(scenario.freeze_mismatches)
    measured = False
    if scenario.freeze_manifest is not None and scenario.freeze_root is not None:
        from epd2_control_plane_service.freeze import verify_manifest

        mismatches = mismatches + verify_manifest(scenario.freeze_root, scenario.freeze_manifest)
        measured = True
    ok = not mismatches
    if ok:
        detail = (
            "frozen bytes match (recomputed)"
            if measured
            else "no recorded manifest to compare against"
        )
    else:
        detail = f"mismatches: {list(mismatches)}"
    return CheckResult("CHK-FREEZE-SAME-BYTES", ok, detail)


def check_self_state_bounded(scenario: Scenario) -> CheckResult:
    text = scenario.self_state_text.upper()
    claimed = [claim for claim in FORBIDDEN_SELF_STATES if claim in text]
    return CheckResult(
        "CHK-SELF-STATE-BOUNDED",
        not claimed,
        "only permitted self-states present" if not claimed else f"forbidden claim(s): {claimed}",
    )


def check_scope_levels_complete(scenario: Scenario) -> CheckResult:
    """Platform scope must exist and must not be the top of the political
    hierarchy: no platform authority may carry a governance action code."""
    world = scenario.world()
    offenders: list[str] = []
    governance_actions = {
        "AUTH.ASSIGN",
        "AUTH.RESTORE",
        "OFFICE.ASSIGN_MANDATE",
        "MEMBERSHIP.ADMIN_MUTATE",
    }
    for entry in world.directory.read_model(T0)["current_organizational_authority"]:
        if (
            entry["scope"].startswith(ScopeLevel.PLATFORM.value)
            and set(entry["action_codes"]) & governance_actions
        ):
            offenders.append(entry["authority_id"])
    return CheckResult(
        "CHK-PLATFORM-GRANTS-NO-POLITICAL-AUTHORITY",
        not offenders,
        "platform scope carries no party competence"
        if not offenders
        else f"offenders: {offenders}",
    )


#: Stable id per check function, so a check that *raises* still reports the id
#: it was going to produce rather than a Python function name.
CHECK_IDS: dict[str, str] = {
    "check_inventory_congruent": "CHK-INVENTORY-CONGRUENT",
    "check_no_universal_admin": "CHK-NO-UNIVERSAL-ADMIN",
    "check_scope_isolation": "CHK-SCOPE-ISOLATION",
    "check_no_implicit_bund_takeover": "CHK-NO-IMPLICIT-BUND-TAKEOVER",
    "check_self_approval": "CHK-SELF-APPROVAL-REJECTED",
    "check_quorum": "CHK-QUORUM-ENFORCED",
    "check_commit_time_reauthorization": "CHK-COMMIT-TIME-REAUTH",
    "check_revoked_authority_refused": "CHK-REVOKED-AUTHORITY-REFUSED",
    "check_intervention_enforced": "CHK-INTERVENTION-ENFORCED",
    "check_no_coarse_regional_disable": "CHK-NO-COARSE-REGIONAL-DISABLE",
    "check_indefinite_intervention_impossible": "CHK-INTERVENTION-TIME-BOUNDED",
    "check_emergency_expiry": "CHK-EMERGENCY-EXPIRY",
    "check_emergency_not_renewable": "CHK-EMERGENCY-NOT-RENEWABLE",
    "check_emergency_scope": "CHK-EMERGENCY-SCOPE",
    "check_actor_class": "CHK-ACTOR-CLASS-SEPARATION",
    "check_secret_visibility_separation": "CHK-SECRET-VISIBILITY-SEPARATION",
    "check_session_state": "CHK-SESSION-STATE-ENFORCED",
    "check_credential_state": "CHK-CREDENTIAL-STATE-ENFORCED",
    "check_fail_closed_on_unknown": "CHK-FAIL-CLOSED-ON-UNKNOWN",
    "check_voting_boundary": "CHK-VOTING-BOUNDARY",
    "check_privacy_minimization": "CHK-PRIVACY-MINIMIZATION",
    "check_evidence_emitted": "CHK-EVIDENCE-EMITTED",
    "check_evidence_immutable": "CHK-EVIDENCE-IMMUTABLE",
    "check_no_direct_state_mutation": "CHK-NO-DIRECT-STATE-MUTATION",
    "check_no_mass_assignment": "CHK-NO-MASS-ASSIGNMENT",
    "check_freeze_same_bytes": "CHK-FREEZE-SAME-BYTES",
    "check_self_state_bounded": "CHK-SELF-STATE-BOUNDED",
    "check_scope_levels_complete": "CHK-PLATFORM-GRANTS-NO-POLITICAL-AUTHORITY",
}

CHECKS: tuple[Callable[[Scenario], CheckResult], ...] = (
    check_inventory_congruent,
    check_no_universal_admin,
    check_scope_isolation,
    check_no_implicit_bund_takeover,
    check_self_approval,
    check_quorum,
    check_commit_time_reauthorization,
    check_revoked_authority_refused,
    check_intervention_enforced,
    check_no_coarse_regional_disable,
    check_indefinite_intervention_impossible,
    check_emergency_expiry,
    check_emergency_not_renewable,
    check_emergency_scope,
    check_actor_class,
    check_secret_visibility_separation,
    check_session_state,
    check_credential_state,
    check_fail_closed_on_unknown,
    check_voting_boundary,
    check_privacy_minimization,
    check_evidence_emitted,
    check_evidence_immutable,
    check_no_direct_state_mutation,
    check_no_mass_assignment,
    check_freeze_same_bytes,
    check_self_state_bounded,
    check_scope_levels_complete,
)


def run_checks(scenario: Scenario | None = None) -> tuple[CheckResult, ...]:
    """Run the whole suite. An exception inside a check is a failure."""
    scenario = scenario or Scenario()
    results: list[CheckResult] = []
    for check in CHECKS:
        try:
            results.append(check(scenario))
        except Exception:
            name = getattr(check, "__name__", "unknown")
            results.append(
                CheckResult(
                    CHECK_IDS.get(name, name),
                    False,
                    f"check raised: {traceback.format_exc(limit=2).strip().splitlines()[-1]}",
                )
            )
    return tuple(results)


def suite_digest(results: Iterable[CheckResult]) -> str:
    payload = "\n".join(
        f"{r.check_id}:{'PASS' if r.passed else 'FAIL'}"
        for r in sorted(results, key=lambda x: x.check_id)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
