"""W11 — the mutation / anti-cheat corpus.

Each fixture describes one way the governed model could be weakened, and builds
the `Scenario` that expresses it. A fixture is *detected* when running the
shared governed check suite against its scenario produces at least one failure,
and the fixture declares which check is expected to catch it — so a mutation
that starts being caught by an unrelated check is itself reported.

The corpus deliberately mixes three kinds of weakening: removing an enforcement
(a policy obligation), corrupting data (an inserted universal admin, a rewritten
journal), and lying in the packaging (a freeze mismatch, a forbidden self-state
claim). All three are ways a candidate could pass while being wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import Any

from epd2_control_plane_service.breakglass import BreakGlassService
from epd2_control_plane_service.domain import (
    ActorClass,
    AuthorityState,
    InterventionType,
    Right,
)
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
)
from epd2_control_plane_service.verification import Scenario, run_checks

__all__ = ["MUTATIONS", "Mutation", "MutationOutcome", "apply_and_detect"]

#: Repository root, so the freeze mutation can re-hash a real packaged file.
_REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class Mutation:
    mutation_id: str
    title: str
    kind: str  # POLICY | DATA | INVENTORY | PACKAGING | RUNTIME
    expected_check: str
    build: Any  # Callable[[], Scenario]


@dataclass(frozen=True, slots=True)
class MutationOutcome:
    mutation_id: str
    detected: bool
    expected_check: str
    failing_checks: tuple[str, ...]
    caught_by_expected: bool


# ---------------------------------------------------------------------------
# helpers for building mutated worlds / inventories
# ---------------------------------------------------------------------------


def _policy(obligation: str) -> Scenario:
    return Scenario(policy=ControlPolicy.governed().without(obligation))


def _mutate_action(action_id: str, **changes: Any) -> ActionInventory:
    actions = []
    for action in INVENTORY:
        actions.append(replace(action, **changes) if action.action_id == action_id else action)
    return ActionInventory(actions)


def _drop_action(action_id: str) -> ActionInventory:
    return ActionInventory(a for a in INVENTORY if a.action_id != action_id)


def _insert_universal_admin(world: World) -> None:
    """A root account of the shape one is actually built.

    It stops one right short of the full set — nobody gives root the auditor
    right — and holds every mutating action code. A check that only looks for
    "all twelve rights" misses exactly this.
    """
    world.directory.record_authority(
        _authority(
            "a.root.superadmin",
            "p.ordinary.member",
            "ROOT",
            LAND_BE,
            set(Right) - {Right.REVIEW_OR_AUDIT},
            {a.action_id for a in INVENTORY if a.mutation},
        ),
        recorded_at=T0,
        recorded_by="mutation",
    )


def _implicit_bund_takeover(world: World) -> None:
    """Widen the one governed oversight grant to every scope."""
    current = world.directory.current_authority("a.bund.oversight")
    assert current is not None
    world.directory.record_authority(
        replace(
            current, oversight_of=frozenset({LAND_BE.key, LAND_BY.key, BUND.key, PLATFORM.key})
        ),
        recorded_at=T0,
        recorded_by="bootstrap",
    )


def _repoint_oversight(world: World) -> None:
    """Keep a single oversight scope, but not the one the decision names."""
    current = world.directory.current_authority("a.bund.oversight")
    assert current is not None
    world.directory.record_authority(
        replace(current, oversight_of=frozenset({LAND_BY.key})),
        recorded_at=T0,
        recorded_by="bootstrap",
    )


def _direct_state_mutation(world: World) -> None:
    """One un-evidenced write, straight into the directory."""
    world.directory.set_authority_state(
        "a.land.be.deputy", AuthorityState.REVOKED, recorded_at=T0, recorded_by="direct-db-write"
    )


def _records(world: World) -> list[Any]:
    """Reach the journal's storage the way an attacker with database access
    would. The tamper helpers live here, in the attacker model, rather than in
    the production evidence module."""
    return world.journal._records


def _rebuild(record: Any, **changes: Any) -> Any:
    from dataclasses import replace as _dc_replace

    return _dc_replace(record, **changes)


def _remove_audit_event(world: World) -> None:
    """Delete an interior record — the naive shape."""
    rows = _records(world)
    rows[:] = [r for r in rows if r.sequence != 1]


def _truncate_newest_event(world: World) -> None:
    """Delete the newest record.

    This is the shape that hides a committed act: an unanchored walk over the
    remaining records sees a perfectly valid chain.
    """
    rows = _records(world)
    del rows[-1]


def _overwrite_history(world: World) -> None:
    """Rewrite a record and leave its stale hash in place."""
    rows = _records(world)
    rows[0] = _rebuild(rows[0], actor_ref="p.someone.else", reason_code="CTRL_AUTHORIZED")


def _rechain_history(world: World) -> None:
    """Rewrite a record and recompute every hash forward.

    A careful tamperer does this, and the result is internally consistent. Only
    the append-time anchor distinguishes it from the real history.
    """
    rows = _records(world)
    rewritten = _rebuild(rows[0], actor_ref="p.someone.else", reason_code="CTRL_AUTHORIZED")
    rewritten = _rebuild(rewritten, event_hash=rewritten.compute_hash())
    rows[0] = rewritten
    for index in range(1, len(rows)):
        linked = _rebuild(rows[index], previous_event_hash=rows[index - 1].event_hash)
        rows[index] = _rebuild(linked, event_hash=linked.compute_hash())


class _RenewableBreakGlass(BreakGlassService):
    """A break-glass service with a renewal path — exactly what must not exist."""

    def renew(self, grant_id: str, *, moment: Any) -> Any:  # pragma: no cover - fixture only
        return self._require(grant_id)


def _renewable_factory(policy: ControlPolicy, inventory: ActionInventory) -> BreakGlassService:
    return _RenewableBreakGlass(policy, inventory)


def _indefinite_restriction() -> Any:
    """A restriction row with a NULL `valid_until`.

    Built by bypassing the constructor on purpose: this models a record that
    reached the runtime from storage rather than through the governed service,
    which is the only way an indefinite restriction can exist at all.
    """
    from epd2_control_plane_service.domain import RegionalAdministrationRestriction as _R

    row = object.__new__(_R)
    values: dict[str, Any] = {
        "restriction_id": "restr-indefinite",
        "intervention_type": InterventionType.REGIONAL_ACTION_RESTRICTION,
        "target_scope": LAND_BE,
        "affected_authority_ids": frozenset(),
        "affected_action_codes": frozenset({"AUTH.ASSIGN"}),
        "valid_from": T0,
        "valid_until": None,
        "reason_code": "GOV_INTERVENTION_ONGOING_REVIEW",
        "rule_version": "SATZUNG-2026.03",
        "decision_ref": "BESCHLUSS",
        "initiating_authority_id": "a.bund.oversight",
        "approving_authority_id": "a.bund.chair",
        "notification_evidence_ref": "NOTIF",
        "review_deadline": T0 + timedelta(days=14),
        "evidence_refs": (),
        "superseded_by": None,
        "revoked_at": None,
    }
    for name, value in values.items():
        object.__setattr__(row, name, value)
    return row


def _voting_action_inventory() -> ActionInventory:
    return _mutate_action("KEY.ROTATE", voting_domain_boundary="INSIDE_VOTING_DOMAIN")


# ---------------------------------------------------------------------------
# corpus
# ---------------------------------------------------------------------------

MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "MUT-01",
        "universal administrator inserted",
        "DATA",
        "CHK-NO-UNIVERSAL-ADMIN",
        lambda: Scenario(world_mutator=_insert_universal_admin),
    ),
    Mutation(
        "MUT-02",
        "region scope check removed",
        "POLICY",
        "CHK-SCOPE-ISOLATION",
        lambda: _policy("enforce_scope_isolation"),
    ),
    Mutation(
        "MUT-03",
        "self-approval enabled",
        "POLICY",
        "CHK-SELF-APPROVAL-REJECTED",
        lambda: _policy("reject_self_approval"),
    ),
    Mutation(
        "MUT-04",
        "quorum reduced below four-eyes",
        "INVENTORY",
        "CHK-QUORUM-ENFORCED",
        lambda: Scenario(
            inventory=_mutate_action("AUTH.ASSIGN", quorum_required=1, four_eyes=False)
        ),
    ),
    Mutation(
        "MUT-05",
        "quorum enforcement removed",
        "POLICY",
        "CHK-QUORUM-ENFORCED",
        lambda: _policy("enforce_quorum"),
    ),
    Mutation(
        "MUT-06",
        "commit-time reauthorization removed",
        "POLICY",
        "CHK-COMMIT-TIME-REAUTH",
        lambda: _policy("commit_time_reauthorization"),
    ),
    Mutation(
        "MUT-07",
        "revoked authority accepted",
        "POLICY",
        "CHK-REVOKED-AUTHORITY-REFUSED",
        lambda: _policy("enforce_authority_state"),
    ),
    Mutation(
        "MUT-08",
        "intervention enforcement removed",
        "POLICY",
        "CHK-INTERVENTION-ENFORCED",
        lambda: _policy("enforce_interventions"),
    ),
    Mutation(
        "MUT-09",
        "intervention becomes a coarse regional disable",
        "POLICY",
        "CHK-NO-COARSE-REGIONAL-DISABLE",
        lambda: _policy("enforce_closed_action_codes"),
    ),
    Mutation(
        "MUT-10",
        "emergency expiry removed",
        "POLICY",
        "CHK-EMERGENCY-EXPIRY",
        lambda: _policy("enforce_emergency_expiry"),
    ),
    Mutation(
        "MUT-11",
        "break-glass made renewable forever",
        "RUNTIME",
        "CHK-EMERGENCY-NOT-RENEWABLE",
        lambda: Scenario(emergency_factory=_renewable_factory),
    ),
    Mutation(
        "MUT-12",
        "emergency scope confinement removed",
        "POLICY",
        "CHK-EMERGENCY-SCOPE",
        lambda: _policy("enforce_emergency_scope"),
    ),
    Mutation(
        "MUT-13",
        "service identity accepted as human administrator",
        "POLICY",
        "CHK-ACTOR-CLASS-SEPARATION",
        lambda: _policy("enforce_actor_class"),
    ),
    Mutation(
        "MUT-14",
        "human action reclassified as a workload action",
        "INVENTORY",
        "CHK-ACTOR-CLASS-SEPARATION",
        lambda: Scenario(
            inventory=_mutate_action("MEMBERSHIP.ADMIN_MUTATE", actor_class=ActorClass.SERVICE)
        ),
    ),
    Mutation(
        "MUT-15",
        "audit event removed",
        "DATA",
        "CHK-EVIDENCE-IMMUTABLE",
        lambda: Scenario(journal_mutator=_remove_audit_event),
    ),
    Mutation(
        "MUT-16",
        "history overwritten",
        "DATA",
        "CHK-EVIDENCE-IMMUTABLE",
        lambda: Scenario(journal_mutator=_overwrite_history),
    ),
    Mutation(
        "MUT-16B",
        "newest audit event truncated to hide a committed act",
        "DATA",
        "CHK-EVIDENCE-IMMUTABLE",
        lambda: Scenario(journal_mutator=_truncate_newest_event),
    ),
    Mutation(
        "MUT-16C",
        "history overwritten and re-chained forward",
        "DATA",
        "CHK-EVIDENCE-IMMUTABLE",
        lambda: Scenario(journal_mutator=_rechain_history),
    ),
    Mutation(
        "MUT-17",
        "stale evidence accepted (immutability enforcement removed)",
        "POLICY",
        "CHK-EVIDENCE-IMMUTABLE",
        lambda: Scenario(
            policy=ControlPolicy.governed().without("enforce_evidence_immutability"),
            journal_mutator=_overwrite_history,
        ),
    ),
    Mutation(
        "MUT-18",
        "hidden privileged field mass-assigned through request parameters",
        "RUNTIME",
        "CHK-NO-MASS-ASSIGNMENT",
        lambda: Scenario(honour_request_parameters=True),
    ),
    Mutation(
        "MUT-19",
        "implicit Bund takeover: oversight grant re-pointed away from its decision",
        "DATA",
        "CHK-NO-IMPLICIT-BUND-TAKEOVER",
        lambda: Scenario(
            policy=ControlPolicy.governed().without("enforce_oversight_binding"),
            world_mutator=_repoint_oversight,
        ),
    ),
    Mutation(
        "MUT-20",
        "key secret made readable to an ordinary approver",
        "POLICY",
        "CHK-SECRET-VISIBILITY-SEPARATION",
        lambda: _policy("enforce_secret_visibility"),
    ),
    Mutation(
        "MUT-21",
        "voting member/person identifier added to control telemetry",
        "POLICY",
        "CHK-PRIVACY-MINIMIZATION",
        lambda: _policy("enforce_privacy_minimization"),
    ),
    Mutation(
        "MUT-22",
        "voting hard boundary removed",
        "POLICY",
        "CHK-VOTING-BOUNDARY",
        lambda: _policy("enforce_voting_boundary"),
    ),
    Mutation(
        "MUT-23",
        "a control action moved inside the voting trust domain",
        "INVENTORY",
        "CONSTRUCTION_REFUSED",
        lambda: Scenario(inventory=_voting_action_inventory()),
    ),
    Mutation(
        "MUT-24",
        "direct database mutation accepted as a control action",
        "DATA",
        "CHK-NO-DIRECT-STATE-MUTATION",
        lambda: Scenario(world_mutator=_direct_state_mutation),
    ),
    Mutation(
        "MUT-25",
        "unsafe failure converted to success (fail-open on unknown state)",
        "POLICY",
        "CHK-FAIL-CLOSED-ON-UNKNOWN",
        lambda: _policy("fail_closed_on_unknown"),
    ),
    Mutation(
        "MUT-26",
        "session state check removed",
        "POLICY",
        "CHK-SESSION-STATE-ENFORCED",
        lambda: _policy("enforce_session_state"),
    ),
    Mutation(
        "MUT-27",
        "generated runtime route absent from the inventory",
        "INVENTORY",
        "CHK-INVENTORY-CONGRUENT",
        lambda: Scenario(
            inventory=_drop_action("MEMBERSHIP.ADMIN_MUTATE"),
            runtime_action_ids=INVENTORY.mutation_ids(),
        ),
    ),
    Mutation(
        "MUT-28",
        "undocumented mutation endpoint added",
        "RUNTIME",
        "CHK-INVENTORY-CONGRUENT",
        lambda: Scenario(runtime_action_ids=INVENTORY.mutation_ids() | {"ADMIN.SHADOW_ENDPOINT"}),
    ),
    Mutation(
        "MUT-29",
        "candidate changed after verification (package/freeze mismatch)",
        "PACKAGING",
        "CHK-FREEZE-SAME-BYTES",
        lambda: Scenario(
            freeze_mismatches=("validation/ctrl01/ctrl_action_inventory.json: sha256 mismatch",)
        ),
    ),
    Mutation(
        "MUT-30",
        "excluded preseal state changed to accepted",
        "PACKAGING",
        "CHK-SELF-STATE-BOUNDED",
        lambda: Scenario(self_state_text="CTRL ACCEPTED / PRODUCTION READY"),
    ),
    Mutation(
        "MUT-31",
        "platform operator granted party-organ competence",
        "DATA",
        "CHK-PLATFORM-GRANTS-NO-POLITICAL-AUTHORITY",
        lambda: Scenario(
            world_mutator=lambda w: w.directory.record_authority(
                _authority(
                    "a.platform.political",
                    "p.privileged.operator",
                    "PLATFORM_OPERATOR",
                    PLATFORM,
                    {Right.REQUEST, Right.EXECUTE, Right.READ_METADATA},
                    {"AUTH.ASSIGN", "MEMBERSHIP.ADMIN_MUTATE"},
                ),
                recorded_at=T0,
                recorded_by="mutation",
            )
        ),
    ),
    Mutation(
        "MUT-32",
        "credential state check removed",
        "POLICY",
        "CHK-CREDENTIAL-STATE-ENFORCED",
        lambda: _policy("enforce_credential_state"),
    ),
    Mutation(
        "MUT-33",
        "oversight binding to one target scope removed",
        "POLICY",
        "CHK-NO-IMPLICIT-BUND-TAKEOVER",
        lambda: Scenario(
            policy=ControlPolicy.governed().without("enforce_oversight_binding"),
            world_mutator=_implicit_bund_takeover,
        ),
    ),
    Mutation(
        "MUT-35",
        "indefinite intervention injected from persistence",
        "DATA",
        "CHK-INTERVENTION-TIME-BOUNDED",
        lambda: Scenario(injected_restrictions=(_indefinite_restriction(),)),
    ),
    Mutation(
        "MUT-34",
        "inventory binding removed (unmapped action executes)",
        "POLICY",
        "CHK-INVENTORY-CONGRUENT",
        lambda: Scenario(
            policy=ControlPolicy.governed().without("enforce_inventory_binding"),
            runtime_action_ids=INVENTORY.mutation_ids() | {"ADMIN.UNMAPPED"},
        ),
    ),
)


def apply_and_detect(mutation: Mutation) -> MutationOutcome:
    """Run the governed suite against one mutated scenario.

    A mutation the model refuses to even construct — an action declared inside
    the voting trust domain, for instance — is detected at construction time,
    which is a stronger result than detecting it at check time.
    """
    try:
        scenario = mutation.build()
    except Exception as error:
        return MutationOutcome(
            mutation_id=mutation.mutation_id,
            detected=True,
            expected_check=mutation.expected_check,
            failing_checks=(f"CONSTRUCTION_REFUSED:{type(error).__name__}",),
            caught_by_expected=mutation.expected_check == "CONSTRUCTION_REFUSED",
        )
    results = run_checks(scenario)
    failing = tuple(sorted(r.check_id for r in results if not r.passed))
    return MutationOutcome(
        mutation_id=mutation.mutation_id,
        detected=bool(failing),
        expected_check=mutation.expected_check,
        failing_checks=failing,
        caught_by_expected=mutation.expected_check in failing,
    )
