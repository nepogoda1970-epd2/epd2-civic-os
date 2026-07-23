# ADR-011: Transparency service decomposition (PACK-04)

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. The single-service decomposition
(Decision, below — `services/transparency-service` owning all four of
ADR-013's proposed entities) is approved exactly as drafted, with no
amendments. Implementation of the service itself remains a separate,
later task, not authorized by this acceptance alone; no
`services/transparency-service` directory is created as part of this
acceptance.

## Context

`docs/handover/PACK-04-SPEC.md` section 3 proposes four new entities for
the Transparency Context (canon section 5.11): `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy`, `LobbyLogEntry`. None of these
entities exist in canon's section 22 ownership matrix today — ADR-013
(this same governance round) is the proposal to add them. This ADR
answers a narrower, separate question that does not depend on ADR-013's
acceptance to be decided in principle: assuming these four entities are
accepted in some form, how many physical `uv` workspace services should
own them?

This is the same kind of decision ADR-005 made for PACK-03's eighteen
entities across twelve canon-named modules, and PACK-02's own
`eligibility-service` established the precedent for before that: canon
section 22 (once ADR-013 extends it) would name one "module" owner per
entity, not one physical deployable per module.

## Problem

Left undecided, a future implementation could default to four separate
tiny services (one per entity — `public-ledger-service`,
`audit-export-service`, `disclosure-policy-service`, `lobby-log-service`),
adding real cross-service call/deploy overhead for four entities that, in
PACK-04's own proposed usage, are tightly coupled: a `PublicLedgerEntry`
is only ever published under an active `DisclosurePolicy`, and its
correctness is what `AuditExportPackage` is exported to prove. A single
oversized service is the opposite risk — it would make ownership
boundaries convention-only rather than the kind of thing
`tests/repository/test_service_boundaries.py` can structurally check, the
same concern ADR-005 raised about its own Option C.

## Considered options

- Option A — four services, one per proposed entity, maximizing literal
  one-entity-one-service correspondence.
- Option B — one service, `services/transparency-service`
  (`epd2_transparency_service`), owning all four proposed entities, on the
  reasoning that all four are write-once/append-only, low-state-machine-
  complexity records with no cross-cutting concern serious enough to
  warrant separate deployables — closely analogous to PACK-02's
  `eligibility-service` consolidation of `EligibilityRule`,
  `EligibilityDecision`, and `EligibilitySnapshot`.
- Option C — two services: one for public-facing published content
  (`PublicLedgerEntry`, `LobbyLogEntry`) and one for audit/policy
  machinery (`AuditExportPackage`, `DisclosurePolicy`), on the theory that
  "what the public sees" and "how publication is governed/proven" are
  different concerns.

## Decision

Option B, `docs/handover/PACK-04-SPEC.md` section 4's proposal, restated
here as the formal decision this ADR asks the project owner to ratify:

**`services/transparency-service`** (`epd2_transparency_service`) —
`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
`LobbyLogEntry`.

Option A is rejected as disproportionate: none of the four proposed
entities has independent operational value without the others (a
`PublicLedgerEntry` with no `DisclosurePolicy` to have been published
under has no governance story; an `AuditExportPackage` with no
`PublicLedgerEntry` history to prove has nothing to attest to). Option C
is rejected because `DisclosurePolicy` is consulted at the moment a
`PublicLedgerEntry` or `LobbyLogEntry` is published, not at some later,
separable stage — splitting policy evaluation from the entity it governs
across a service boundary would add a synchronous cross-service call on
every publish action for no corresponding gain in structural clarity;
`tests/repository/test_service_boundaries.py` can enforce ownership
boundaries just as well with these four entities inside one service as
it already does for PACK-02's `eligibility-service` three-entity group.

This is a **smaller** service surface than PACK-03's six — proportionate
to a pack whose job is publication and proof of already-decided facts,
not new decision-making workflows.

## Consequences

One new workspace member joins the eleven PACK-02/03 services plus
`epd2-core`, bringing the total to twelve Python packages plus
`epd2-core` (assuming PACK-04 is the next pack implemented; the count is
unaffected by ADR-013's outcome). `tests/repository/test_service_boundaries.py`
gains one new row (own package + `epd2_core` + `epd2_audit_core` allowed;
PACK-02/03 read edges handled separately by ADR-012). The service gets
its own `pyproject.toml`, `src/`, `tests/`, `README.md`, and a new scoped
`mypy` invocation in `Makefile`'s `typecheck` target, following the exact
pattern every prior service used.

## Security impact

None directly — this is a deployment/ownership-boundary decision. It does
set the boundary CT-00-08/09 (section 10 of `docs/handover/PACK-04-SPEC.md`)
are later verified against for this pack specifically, so getting this
grouping wrong would make those checks harder to reason about — the same
concern ADR-005 raised for its own decision.

## Data impact

No canonical entity, field, or status is created or changed by this ADR
— that is ADR-013's proposal, decided separately. This ADR only assigns a
physical package boundary to whatever ADR-013 ultimately defines (or, if
ADR-013 is rejected or amended to a different entity set, to whatever
resulting entity set the project owner approves).

## Migration impact

None — no PACK-04 service exists yet; there is no prior physical layout
to migrate away from.

## Reversibility

Reversible with cost before code exists (this stage, the same as
ADR-005's own assessment); reversible with significant cost once the
service is implemented and has real published data, since re-splitting
after the fact means moving persisted records and rewriting call sites.

## Related canon version

Authored against canon version `0.2.0`. Proposes no canon change itself
— this ADR only decides how ADR-013's proposed entities (if accepted)
would map to `uv` workspace packages, exactly as ADR-005 did for PACK-03
relative to canon's existing (not proposed) ownership matrix.
