"""Governed enforcement policy.

Every field is an enforcement obligation that the accepted governance model
requires. They exist as explicit switches for exactly one reason: the W11
mutation/anti-cheat suite flips them to prove that the governed check suite
actually fails when an enforcement is removed. A candidate whose checks still
pass with an enforcement disabled has not proved anything.

The only value permitted in a preseal candidate is `ControlPolicy.governed()`,
in which every obligation is enforced. `is_governed()` is asserted by gate G20
and by the freeze gate, so a mutated policy can never be packaged.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace

__all__ = ["ControlPolicy"]


@dataclass(frozen=True, slots=True)
class ControlPolicy:
    """Enforcement obligations. All default to enforced."""

    #: Scope must match exactly; hierarchy grants nothing (FIR-GOV-005 s1).
    enforce_scope_isolation: bool = True
    #: Cross-scope oversight requires an explicit, rule-bound grant.
    enforce_oversight_binding: bool = True
    #: An expired/suspended/revoked authority authorizes nothing.
    enforce_authority_state: bool = True
    #: A principal may not approve their own request (FIR-GOV-005 s18).
    reject_self_approval: bool = True
    #: Approvals must reach the inventory-declared quorum.
    enforce_quorum: bool = True
    #: Authority is re-resolved at commit, not only at request (no TOCTOU).
    commit_time_reauthorization: bool = True
    #: Active FIR-GOV-004 restrictions block their named action codes.
    enforce_interventions: bool = True
    #: Quarantined/revoked sessions authorize nothing.
    enforce_session_state: bool = True
    #: A revoked or replaced authentication credential authorizes nothing.
    enforce_credential_state: bool = True
    #: Break-glass grants expire absolutely and are never renewed in place.
    enforce_emergency_expiry: bool = True
    #: Emergency use is confined to the approved action codes and scope.
    enforce_emergency_scope: bool = True
    #: Human/service actor classes are disjoint.
    enforce_actor_class: bool = True
    #: Secret visibility is a separate right from approval.
    enforce_secret_visibility: bool = True
    #: Evidence is append-only and hash-chained.
    enforce_evidence_immutability: bool = True
    #: Evidence is screened for voting-linkable and protected fields.
    enforce_privacy_minimization: bool = True
    #: Voting-domain objects are refused to every control-plane right.
    enforce_voting_boundary: bool = True
    #: Every runtime mutation must resolve to one inventory entry.
    enforce_inventory_binding: bool = True
    #: Unresolvable authority state is a refusal, never a default-permit.
    fail_closed_on_unknown: bool = True
    #: Only inventory-registered action codes may appear in a restriction.
    enforce_closed_action_codes: bool = True

    @classmethod
    def governed(cls) -> ControlPolicy:
        """The only policy permitted in a preseal candidate."""
        return cls()

    def is_governed(self) -> bool:
        return all(getattr(self, f.name) is True for f in fields(self))

    def disabled_obligations(self) -> tuple[str, ...]:
        return tuple(f.name for f in fields(self) if getattr(self, f.name) is not True)

    def without(self, obligation: str) -> ControlPolicy:
        """Return a mutated policy with one obligation removed. Test-only."""
        if obligation not in {f.name for f in fields(self)}:
            raise KeyError(f"unknown obligation: {obligation}")
        return replace(self, **{obligation: False})
