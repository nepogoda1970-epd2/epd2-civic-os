# ADR-005: PACK-03 service decomposition (Participation and Decision Kernel)

## Status

`accepted`

## Date

2026-07-22

## Owner decision

Accepted as proposed, 2026-07-22. The project owner approved the
six-service decomposition (Decision, below) exactly as drafted, with no
amendments. This satisfies canon section 26's precondition for PACK-03
service directories and implementation code to exist consistent with this
decomposition; implementation itself is a separate, later task and is not
authorized by this acceptance alone (the owner's acceptance message
explicitly deferred all PACK-03 service code to a future task — see
`docs/review/PACK-03-OWNER-DECISIONS.md`).

## Context

`docs/canonical/TZ-00-domain-event-canon.md` section 22 (the ownership
matrix) declares one "module" owner per entity, not one physical service
per module. CLAUDE-PACK-03 (`docs/handover/PACK-03-SPEC.md`) is scoped to
six canon bounded contexts (Initiative 5.5, Deliberation 5.6, Moderation
5.7, Voting 5.8, Tally 5.9, Delegation 5.10), covering eighteen entities
across twelve distinct canon-declared module names:

| Entity                             | Canon section | Canon-declared owner            |
| ---------------------------------- | ------------- | ------------------------------- |
| Initiative, InitiativeVersion      | 11.1, 11.2    | Initiative Service              |
| SupportRecord                      | 11.3          | (not named separately by canon) |
| Amendment                          | 11.4          | Amendment Service               |
| SourceRecord                       | 12.1          | Evidence Service                |
| Discussion, Contribution           | 13.1, 13.2    | Discussion Service              |
| ModerationCase, ModerationDecision | 14.1, 14.2    | Moderation Service              |
| Appeal                             | 14.3          | Appeal Service                  |
| Ballot                             | 15.1          | Ballot Definition Service       |
| BallotOption                       | 15.2          | (not named separately by canon) |
| VoteEnvelope                       | 15.3          | Vote Casting Service            |
| VoteReceipt                        | 15.4          | Receipt Service                 |
| Tally                              | 15.5          | Tally Service                   |
| ResultPublication                  | 15.6          | Result Publication Service      |
| Delegation                         | 16.1          | Delegation Service              |
| DelegationSnapshot                 | 16.2          | Delegation Resolution Engine    |

There is precedent for consolidating multiple canon-declared modules into
one physical deployable: PACK-02's `eligibility-service` is the single
`uv` workspace member for canon's `EligibilityRule`, `EligibilityDecision`,
and `EligibilitySnapshot` — three entities the canon's own ownership
matrix lists under one owner name ("Eligibility Engine"), implemented as
one Python package. That precedent was accepted implicitly as part of
PACK-02's Definition of Done, not through its own dedicated ADR — this ADR
is the first time the _decomposition question itself_ is being put through
the ADR process explicitly, at the scale PACK-03 requires it.

## Problem

INV-02 ("one owner per entity") must hold for every entity above. It does
not, by itself, say how many physical `uv` workspace members / deployable
services those owners map to. Left undecided, PACK-03 implementation could
default to twelve tiny services (one per canon-named module, adding
significant cross-service call/deploy overhead for entities that are
tightly coupled in practice — e.g. `Ballot` and `VoteEnvelope` share a
lifecycle and a `ballot_id` foreign key on every write) or to one large
service (violating INV-02's spirit by blurring ownership boundaries and
making the `tests/repository/test_service_boundaries.py`-style structural
check meaningless). A specific, justified grouping is needed before any
service directory is created.

## Considered options

- Option A — twelve services, one per canon-declared module name,
  maximizing literal fidelity to the ownership matrix's naming.
- Option B — six services, grouping only where two canon-named modules
  already share the same natural key and lifecycle (no cross-cutting
  merge of unrelated concerns), following the exact reasoning PACK-02's
  `eligibility-service` already established as acceptable precedent.
- Option C — one large `participation-service` covering all eighteen
  entities, minimizing service count at the cost of internal ownership
  boundaries becoming convention-only rather than structurally enforced.

## Decision

Option B. Six new `uv` workspace services:

1. **`services/initiative-service`** (`epd2_initiative_service`) —
   `Initiative`, `InitiativeVersion`, `SupportRecord`, `Amendment`,
   `SourceRecord`. Consolidates "Initiative Service", "Amendment
   Service", and "Evidence Service": the first four entities share
   `initiative_id` as their natural key and one status workflow;
   `SourceRecord` is included because canon section 5.5's own
   responsibility list for the Initiative Context explicitly names
   "источники" (sources) as part of that context, not a separate one.
2. **`services/deliberation-service`** (`epd2_deliberation_service`) —
   `Discussion`, `Contribution`. Canon already assigns both to one owner
   ("Discussion Service") — no consolidation judgment call required here.
3. **`services/moderation-service`** (`epd2_moderation_service`) —
   `ModerationCase`, `ModerationDecision`, `Appeal`. Consolidates
   "Moderation Service" and "Appeal Service". Canon's explicit prohibition
   ("an appeal must not be finally decided by the author of the original
   decision", section 14.3) is a role-separation invariant enforced by an
   application-layer actor check (`appeal.reviewer_actor_id !=
original_decision.decided_by`), not a deployment-separation invariant
   — the same shape as PACK-02's existing `actor_is_authorized` checks,
   which live inside single services, not across separate ones.
4. **`services/voting-service`** (`epd2_voting_service`) — `Ballot`,
   `BallotOption`, `VoteEnvelope`, `VoteReceipt`. Consolidates "Ballot
   Definition Service", "Vote Casting Service", and "Receipt Service".
   CT-00-09 (Vote Linkability) is a data-shape invariant on
   `VoteEnvelope`'s own schema (no `account_id`/identity field, canon
   section 15.3), enforced the same structural way PACK-02 enforced
   CT-00-08 for `ParticipationCredential` — consolidating vote casting
   and receipt issuance into one service does not weaken that guarantee,
   since neither ever handles identity data.
5. **`services/tally-service`** (`epd2_tally_service`) — `Tally`,
   `ResultPublication`. Consolidates "Tally Service" and "Result
   Publication Service": a `ResultPublication`'s aggregate counts are a
   published view of the same completed `Tally`, and canon gives no
   reason a WIP tally needs an independent owner from its eventual
   publication.
6. **`services/delegation-service`** (`epd2_delegation_service`) —
   `Delegation`, `DelegationSnapshot`. Consolidates "Delegation Service"
   and "Delegation Resolution Engine": a snapshot is a frozen resolution
   of that same service's own live delegation graph.

Option A is rejected as disproportionate operational overhead for entities
that are not independently useful without each other (a `VoteEnvelope`
with no `Ballot` service, or a `Tally` with no `ResultPublication`
service, has no meaningful standalone existence). Option C is rejected
because it removes the one mechanism (`tests/repository/test_service_boundaries.py`'s
per-service AST import check) that makes ownership boundaries something
this repository actually tests, rather than something only documented in
prose.

## Consequences

Six new workspace members join the eleven created by PACK-01/02
(`epd2-core` plus five PACK-02 services), bringing the total to twelve
Python packages plus `epd2-core`. `tests/repository/test_service_boundaries.py`'s
forbidden-pair matrix must be extended with six new rows/columns (own
package + `epd2_core` + `epd2_audit_core` allowed; every other PACK-03
package forbidden; PACK-02 imports handled separately by ADR-008). Each
service gets its own `pyproject.toml`, `src/`, `tests/`, `README.md`, and
mypy needs a new scoped invocation per service in `Makefile`'s
`typecheck` target (the same reason PACK-02 already scopes mypy per
service rather than running one repo-wide invocation — see PACK-02's
Makefile comment on `Duplicate module named`).

## Security impact

None directly — this ADR is a deployment/ownership-boundary decision, not
a data or access-control change. It does, however, set the boundary that
CT-00-09 (Vote Linkability, item 4 above) and the appeal role-separation
check (item 3) are later verified against; getting the grouping wrong
would make those checks harder to reason about, which is why this ADR
records the specific justification for each merge rather than leaving it
implicit.

## Data impact

No new canonical entity, field, or status — this ADR only assigns
physical package boundaries to entities the canon (section 22) already
names. No existing PACK-02 entity's owner changes.

## Migration impact

None — no PACK-03 service exists yet; there is no prior physical layout
to migrate away from.

## Reversibility

Reversible with cost before code exists (this stage); reversible with
significant cost once services are implemented and have real data,
since re-splitting or re-merging services after the fact means moving
persisted records and rewriting cross-service call sites — the same
reasoning canon section 25 applies to "changing an entity's owner"
(a major-version-equivalent change once real).

## Related canon version

Authored against canon version `0.1.0`. Proposes no canon change — the
canon's own ownership matrix (section 22) is unaffected; this ADR only
decides how those canon-named owners map to `uv` workspace packages.
