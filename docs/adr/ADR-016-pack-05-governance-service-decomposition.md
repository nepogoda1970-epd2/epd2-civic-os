# ADR-016: Governance service decomposition (PACK-05)

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. The single-service decomposition
(Decision, below — `services/governance-service` owning `RoleAssignment`,
`GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge`) is
approved exactly as drafted, with no amendments. Emergency/Crisis
Override remains outside PACK-05, and the future physical-service
relationship with any later Emergency/Crisis pack remains explicitly
unresolved, exactly as proposed. Implementation of the service itself
remains a separate, later task, not authorized by this acceptance alone;
no `services/governance-service` directory is created as part of this
acceptance.

## Context

`docs/handover/PACK-05-SPEC.md` section 3 proposes four entities in
scope for the Governance Context (canon section 5.12): `RoleAssignment`
(already fully defined by canon 8.4, never implemented),
`GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge` (the
latter three new, proposed by ADR-018). None of the three new entities
exist in canon's section 22 ownership matrix today; `RoleAssignment`
already has a canon-declared owner label, "Permission / Role Service"
(section 22), distinct from any physical service name this project has
used so far. This ADR answers the same narrow, separable question
ADR-005 and ADR-011 each answered for their own packs: assuming these
four entities are implemented in some form, how many physical `uv`
workspace services should own them?

Canon section 22 also already labels `EmergencyAction`'s (19.1) owner
"Governance / Crisis Service" — textually suggesting canon's own authors
anticipated one combined Governance/Crisis service. This task's explicit
instruction is that Emergency/Crisis Override remains outside PACK-05
regardless, so this ADR must decide PACK-05's own decomposition without
resolving that separate, later question.

## Problem

Left undecided, a future implementation could default to four separate
tiny services (`role-assignment-service`, `governance-policy-service`,
`governance-decision-service`, `technical-challenge-service`), adding
real cross-service call overhead for four entities that are tightly
coupled in this pack's own proposed usage: every `GovernanceDecision`
and every `GovernancePolicy` activation requires two distinct, active
`RoleAssignment`s to approve it (INV-08), and a `TechnicalChallenge`'s
adjudication directly produces a `GovernanceDecision`
(`technical_challenge_adjudication`). A single oversized service is the
opposite risk — it would make the two-actor-approval boundary
(section 9 of the specification) convention-only rather than something
`tests/repository/test_service_boundaries.py` can check structurally.

## Considered options

- Option A — four services, one per entity, maximizing literal
  one-entity-one-service correspondence.
- Option B — one service, `services/governance-service`
  (`epd2_governance_service`), owning all four entities, on the
  reasoning that all four are authority/adjudication records with
  comparable lifecycle complexity to PACK-03's own
  `ModerationCase`/`ModerationDecision` pair, and that keeping the
  two-actor approval invariant enforceable in one place is more
  important than granular service separation.
- Option C — two services: one for role/policy administration
  (`RoleAssignment`, `GovernancePolicy`) and one for adjudication
  (`GovernanceDecision`, `TechnicalChallenge`), on the theory that
  "who holds what authority" and "what was decided" are different
  concerns.

## Decision

**Option B, per the owner's binding proposal for this draft.**

**`services/governance-service`** (`epd2_governance_service`) —
`RoleAssignment`, `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`.

Option A is rejected as disproportionate, for the same reason ADR-011
rejected it for Transparency: none of the four entities has independent
operational value without the others, and splitting them would turn
every two-actor approval check and every challenge-to-decision link into
a cross-service call for no corresponding gain in structural clarity.
Option C is rejected because `GovernanceDecision`'s two-actor approval
rule (section 9 of the specification) applies identically whether the
decision concerns a role, a policy, a ballot invalidation, or a
technical-challenge outcome — splitting "administration" from
"adjudication" would duplicate that enforcement logic across two
services rather than centralizing it once.

**Emergency/Crisis Override remains outside PACK-05, explicitly.** No
`EmergencyAction`-related code, entity, or service directory is created
by this ADR. This decomposition decision is scoped strictly to the four
entities above.

**The future physical-service relationship between `governance-service`
and any later Emergency/Crisis Override implementation is explicitly
left unresolved by this ADR**, per the owner's binding instruction.
Canon section 22 already labels `EmergencyAction`'s owner "Governance /
Crisis Service," which textually suggests — but does not mandate — a
single combined physical service. Whether a future Emergency/Crisis pack
extends this same `governance-service` package or introduces its own
`emergency-service` is a decision for that future pack's own
decomposition ADR, informed by whatever `governance-service` actually
looks like once PACK-05 ships. This ADR takes no position either way,
and no code, test, or documentation produced under this ADR may assume
one outcome over the other.

## Consequences

One new workspace member joins the twelve PACK-02/03/04 services plus
`epd2-core`, bringing the total to thirteen Python packages plus
`epd2-core`. `tests/repository/test_service_boundaries.py` gains one new
row (own package + `epd2_core` + `epd2_audit_core` allowed; PACK-02/03/04
read edges and the new bidirectional edges with `voting-service` handled
separately by ADR-017). The service gets its own `pyproject.toml`,
`src/`, `tests/`, `README.md`, and a new scoped `mypy` invocation in
`Makefile`'s `typecheck` target, following the exact pattern every prior
service used.

## Security impact

None directly — this is a deployment/ownership-boundary decision. It
does set the boundary the two-actor approval check (section 9 of the
specification) is later verified against, and centralizing all four
entities in one service is itself a security-relevant choice: it means
there is exactly one place, not up to four, where "does this proposer
differ from this approver" must be enforced correctly.

## Data impact

No canonical entity, field, or status is created or changed by this ADR
— that is ADR-018's proposal, decided separately. `RoleAssignment`'s
canon-declared owner label ("Permission / Role Service", canon
section 22) is not changed by this ADR; this ADR only assigns the
physical package (`governance-service`) that implements that
canonically-named module, the same "module ≠ physical service"
relationship every prior consolidated service in this repository already
has (e.g. `eligibility-service` implementing three canon-named modules).

## Migration impact

None — no PACK-05 service exists yet; there is no prior physical layout
to migrate away from.

## Reversibility

Reversible with cost before code exists (this stage); reversible with
significant cost once the service is implemented and holds real
`RoleAssignment`/`GovernanceDecision` records, since re-splitting after
the fact means moving persisted authority records and rewriting every
two-actor-approval call site.

## Related canon version

Authored against canon version `0.3.0`. Proposes no canon change itself
— this ADR only decides how ADR-018's proposed entities (if accepted),
plus canon's already-existing `RoleAssignment` (8.4), would map to `uv`
workspace packages.
