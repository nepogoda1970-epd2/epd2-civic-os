# ADR-048: PACK-10 finance domain service decomposition

## Status

`proposed`

## Date

2026-07-27

## Context

PACK-08 delivered the organizational substrate (`Organization`,
`OrganizationalUnit`, `OrganizationalScope`, `OrganizationalAuthority`).
PACK-09 delivered the compliance and legal-workflow substrate
(retention, legal hold, the processing registry, governed cases,
deadlines, official notices, arbitration). Neither carries the domain
PACK-10 must specify: internal party accounting, legally governed
income and expenditure, donation and contribution governance,
sponsorship and other financially relevant external influence,
reimbursement and expense workflows, financial assets and
obligations, organizationally scoped budgets and accounting periods,
the preparation through publication lifecycle of the German party
financial accountability report (`Rechenschaftsbericht`), independent
finance audit, and public financial transparency views that do not
expose protected personal data.

This round is specification-only (`PACK-10-SPECIFICATION.md` section
0 and section 2): no code, no service directory, no runtime schema, no
OpenAPI operation. This ADR is the architectural determination
everything else in the specification depends on.

The finance domain pulls in two directions at once. Toward one
service: a balanced double-entry ledger write and the contribution
decision that produced it must commit inside a single transaction
boundary, or the ledger can go out of balance relative to what
contribution governance believes was accepted. Toward several
services: the domain is large — ledger, imports, contributions,
expenses, positions, budgets, reporting, audit engagement, policy, and
a restricted party-handle registry are each substantial areas with
their own lifecycle rules (`PACK-10-SPECIFICATION.md` section 6, rows
1-55; section 8).

Two facts bound the decision further. First, the baseline has no
production event bus and no production database — both are PACK-13's
responsibility (`PACK-10-SPECIFICATION.md` section 5) — so a design
requiring cross-service consistency (an outbox, a saga, an
eventual-consistency job) would need machinery this repository does
not have. Second, every earlier pack that introduced a new domain
added exactly one new service: PACK-08 added `organization-service`
(ADR-032, over folding into `governance-service` or
`membership-service`), and PACK-09 added `compliance-service`
(ADR-038, rejecting both an in-place extension of four services and a
three-way split of its six entity families). Both reach the same
reasoning this ADR reaches independently: a shared scope, authority
and audit pattern belongs in one service, since splitting it
multiplies cross-service edges for no ownership benefit.

## Problem

Where should the finance domain live — one service, several services
split by sub-domain, or folded into an existing service — and,
whichever shape is chosen, what may it import and how is its internal
separation kept from decaying into an undifferentiated monolith as
the domain grows?

Three sub-questions have to be answered together:

- Does a balanced ledger write and its governing contribution decision
  ever cross a service boundary mid-transaction? If yes, no design is
  safe without distributed-transaction machinery this repository does
  not have.
- Which module boundaries are load-bearing — a security or integrity
  property depends on one module being unable to import another —
  versus merely organizational?
- What must the finance domain never hold or resolve, given PACK-07's
  anti-correlation guarantees and PACK-09's identity-minimization
  precedent (`CasePartyReference`)?

## Considered options

- **Option 1 — one undifferentiated `finance-service`.** All ledger,
  contribution, expense, budget, reporting, audit and projection
  logic lives in one flat module surface with no enforced internal
  boundary.
- **Option 2 — three services: `ledger-service`,
  `contribution-service`, `reporting-service`.** Ledger and accounting
  periods in one service; contributions, sponsorship and external
  benefits in a second; reporting, consolidation, submission,
  publication and audit engagement in a third.
- **Option 3 — one bounded context, `services/finance-service`, with
  explicitly separated internal modules**, each module owning a
  distinct set of aggregates and each boundary enforced by an
  architecture test rather than by convention alone.
- **Option 4 — a narrower split: `finance-service` plus
  `finance-reporting-service`.** Ledger, imports, contributions,
  expenses, positions and budgets stay together; reporting and
  `audit_engagement` move to a second service on the theory that they
  are naturally "downstream" of the ledger and deserve isolation.

## Decision

**Option 3.** PACK-10 specifies exactly one new bounded context,
`services/finance-service`, with seventeen internal modules, each
with a single owning responsibility:

| Module                | Owns                                                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `domain.py`           | Value objects (`Money`, `PostingLine`, `InKindValuation`), pure invariants, no I/O                                               |
| `ledger.py`           | `FinanceAccount`, `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`, `ReconciliationRecord`                             |
| `imports.py`          | `ImportBatch`, provenance and duplicate detection                                                                                |
| `contributions.py`    | `Contribution`, aggregation and threshold evaluation, `SponsorshipAgreement`, `ExternalFinancialBenefit`                         |
| `expenses.py`         | `ExpenseClaim`, `PaymentAuthorization`                                                                                           |
| `positions.py`        | `FinancialAsset`, `FinancialObligation`                                                                                          |
| `budgets.py`          | `Budget`, `BudgetVersion`, `BudgetLine`                                                                                          |
| `reporting.py`        | `ReportingObligation`, `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`, consolidation, submission, publication |
| `audit_engagement.py` | `AuditEngagement`, `AuditFinding`, `AuditConclusion`                                                                             |
| `policy.py`           | `FinancePolicy` (all policy kinds), version binding, effective dating                                                            |
| `partyregistry.py`    | `FinancePartyHandle` minting and the restricted resolution surface                                                               |
| `projections.py`      | Derived read models, public views, statistical disclosure control                                                                |
| `events.py`           | Canonical event builders and full-state payload snapshots                                                                        |
| `storage.py`          | One `Protocol` per aggregate plus an in-memory reference adapter; no delete method                                               |
| `application.py`      | Commands, guards, Audit Core append, reason-coded refusals                                                                       |
| `references.py`       | The typed references PACK-10 exports to later packs                                                                              |
| `exceptions.py`       | One class per registered reason code                                                                                             |

This restates `PACK-10-SPECIFICATION.md` section 7, which names this
ADR as the source of the analysis and defers to it; this ADR treats
the specification's module table as authoritative.

**Dependency rule.** `finance-service` imports `epd2_core` and
`epd2_audit_core` and nothing else — the rule ADR-038 fixed for
`compliance-service`. Facts owned by PACK-08 (organization state,
authority assignments) and PACK-09 (record class, retention state,
hold state, legal case, deadline, notice-effect decision) reach
`finance-service` only through those services' published typed
references (`OrganizationalScope`, `RecordClassRef`, `HoldRef`,
`LegalCaseRef`, `NoticeEffectRef`), never by reading their stores —
canon INV-03, checked by
`test_service_boundaries.py::test_finance_service_imports_only_shared_packages`.

**Criteria and how each option scores against them:**

- **Aggregate consistency / ledger balancing / organizational scope.**
  A `JournalEntry` must be balanced at construction and again at
  posting (invariant 7), and its governing contribution decision must
  not be separable from the posting. Options 1 and 3 keep both in one
  transaction; Option 2 splits them across `ledger-service`/
  `contribution-service`; Option 4 keeps them together but makes the
  analogous split one layer down, between the ledger and the
  reporting/audit path. All four options carry `OrganizationalScope`
  on every aggregate, so scope alone does not distinguish them.
- **Report consolidation.** Consolidation reads lower-scope ledger and
  contribution state and writes only a `ConsolidationRecord` in the
  consolidating scope (invariant 39). Options 1 and 3 make this a
  local read; Options 2 and 4 make it a synchronous cross-service call
  — the same coupling ADR-038 rejected for `compliance-service`'s
  Option B: the first thing a separated service needs is a read back
  into the one it was split from.
- **Audit independence.** Independence (invariant 30) is a property of
  who may write, not which process runs the code: `audit_engagement.py`
  must not write to any aggregate it audits. A module-level import
  restriction proves this as well as a service boundary would.
- **Transaction boundaries — the deciding criterion.** Options 1 and 3
  commit the balanced posting and its contribution decision in one
  transaction; Options 2 and 4 do not, and neither the baseline
  repository nor any accepted PACK-13 scope provides an outbox, saga
  coordinator or two-phase commit primitive to make a split-service
  posting safe. Choosing Option 2 or 4 today means inventing the
  distributed-consistency mechanism invariant 7 needs — a mechanism
  PACK-13 owns and has not built.
- **Cross-service coupling.** Options 1 and 3 add zero new edges within
  the finance domain. Option 2 adds at least three (ledger↔
  contribution, reporting↔ledger, reporting↔contribution); Option 4
  adds one (reporting/audit↔ledger) — smaller but not zero, and
  exactly the edge carrying the consolidation read above.
- **Later production data-plane migration (PACK-13).** A single
  service with clean internal boundaries is easier to onboard onto
  PACK-13's future event bus and database than services whose
  boundary already assumes synchronous cross-service reads, which
  PACK-13 would then have to keep synchronous or convert to
  asynchronous, reopening the invariant-7 consistency question.
- **Repository conventions.** ADR-032 and ADR-038 are the only two
  precedents for adding a wholly new domain here, and both chose one
  service over a split, on the same "shared scope model, shared
  authority model, shared audit pattern" reasoning that applies to
  finance. A different answer here would be the first departure from
  that convention without a strong domain-specific reason.
- **Testability.** Module-boundary invariants translate directly into
  `tests/repository/test_service_boundaries.py` import-graph
  assertions under Options 1 and 3. Under Options 2 or 4 the same
  guarantee (e.g. "reporting cannot write into the ledger it
  consolidates") can only be proven partly, by contract tests against
  a live boundary — weaker and slower than a static import check.
- **Risk of a finance monolith.** Option 1's failure mode: without
  enforced internal boundaries, `budgets.py` drifts into writing
  ledger actuals, `projections.py` drifts into an authoritative write
  path, and `audit_engagement.py` drifts into writing what it audits —
  the drift invariants 12, 30 and 35 exist to prevent. Option 1 has the
  right transaction boundary but no mechanism to stop that decay.
- **Risk of premature microservice fragmentation.** Options 2 and 4's
  failure mode: splitting before a distributed-consistency mechanism
  exists buys no independent scaling or deployment today — only more
  network calls and a second place the "may this organization reach
  that record" check must stay consistent, the multiplication ADR-038
  already refused for `compliance-service`.

**Why Option 4 specifically fails.** Reporting and audit engagement
look separable because they mostly read rather than write:
`FinanceReportVersion` is built by reading `ledger.py` and
`contributions.py`, and `audit_engagement.py` reads nearly every other
module while writing to none of them (invariant 30). Isolating that
reader removes no write dependency — there is none to remove — but
converts every consolidation and audit read into a network call still
bound by `ORGANIZATION_SCOPE_MISMATCH` and
`FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`, and splits
`FinanceReport`'s version chain (HI-26) from the ledger state it must
represent, for no stronger guarantee than Option 3 gives for free.
Option 4 fails for the same core reason as Option 2.

**Module separation is load-bearing, not cosmetic.** Four boundaries
carry a specific integrity property in the import graph, not a naming
convention: `budgets.py` may not import a ledger store (invariant
12); `projections.py` may not perform an authoritative write
(invariant 35); `audit_engagement.py` may not write to any aggregate
it audits (invariant 30); and `partyregistry.py` is the only module
that may resolve a `FinancePartyHandle` (section 9, invariants 1 and
48). These are the module-boundary architecture tests
`PACK-10-ACCEPTANCE-MATRIX.md` section 6 plans, and the mechanism by
which Option 3 avoids Option 1's monolith risk without Options 2/4's
coupling cost.

## Consequences

Easier: one transaction boundary for every balanced posting and its
governing decision; one place to audit the organizational-scope
guard; one reason-code registry (`contracts/reason-codes/pack-10.yml`,
once implemented); one import-graph check
(`test_finance_service_imports_only_shared_packages`) proving the
whole service, not one per sub-domain, respects canon INV-03. A
reviewer can read `application.py`'s guard helpers once and know how
every boundary in the domain is enforced, as ADR-038 observed for
`compliance-service`.

Harder: `finance-service` will be a comparatively large service once
built, with seventeen modules instead of the five or six a narrower
split would give any one of them. Its internal boundaries must be
actively defended by architecture tests rather than by process
isolation, and a future pack needing only part of it (e.g. PACK-11's
evidence linkage into `expenses.py` or `contributions.py`) will add a
narrow, ADR-sanctioned typed reference rather than depend on a
smaller service — the same cost shape ADR-038 accepted for
`compliance-service`, accepted here for the same reason: the
alternative moves a transactional consistency requirement onto
infrastructure this repository does not yet have.

## Security impact

Moderate, and mostly about what this decision prevents. The
dependency rule (`epd2_core` and `epd2_audit_core` only) is the
primary control: a service that cannot import `organization-service`
or `compliance-service` cannot accumulate a private copy of
organizational or legal state, and must take every fact as an opaque
typed reference resolved through the owning service's published
interface. This mirrors ADR-038 exactly and is checked by the same
class of structural test (`test_service_boundaries.py`).

The `partyregistry.py` restriction (only that module may resolve a
`FinancePartyHandle`) extends PACK-07's anti-correlation model
(ADR-031) and PACK-09's `CasePartyReference` precedent: resolution
confined to one module, rather than one service among several, does
not weaken the guarantee, because the guarantee is about which code
path may resolve a handle, not which network boundary surrounds it.

Choosing one service also removes a risk this ADR does not have to
accept: a multi-service split without a production event bus would
require either trusting another service's unverified writes or an ad
hoc synchronization mechanism outside PACK-13's scope. Option 3 avoids
that risk entirely rather than mitigating it.

## Data impact

None from this ADR by itself. No schema, contract or entity is
created here. The aggregates and read models the decomposition will
eventually own are enumerated in `PACK-10-SPECIFICATION.md` section 8,
not here, and none of the seventeen modules exist as code yet. No
existing canonical entity's ownership, status set or field list
changes. Once implemented, entity schemas will be owned exclusively
by `finance-service` under this module table, with no other service
gaining a write path into any of them.

## Migration impact

None. There is no existing finance data in this repository to
migrate, and no other service's stored shape changes. This ADR fixes
a decomposition for later implementation; it performs no migration
itself because it performs no implementation.

## Reversibility

Reversible with cost, asymmetrically by direction. Splitting one of
the seventeen modules into its own service later is reversible at
moderate cost precisely because Option 3 already separates the
modules cleanly: `storage.py`'s per-aggregate protocols, `events.py`'s
payload builders and `references.py`'s typed exports already draw the
seams a future extraction would need. Merging services back together
would be far harder: once separate services exist with their own
deployed contracts (`references.py` exports, OpenAPI operations,
reason-code registrations), a later round would have to negotiate a
compatibility ADR for every consumer, in the shape ADR-038
anticipated for `compliance-service`'s own contracts. Choosing the
harder-to-reverse shape now, on the weaker evidence a monolith risk
alone provides, would be the wrong side of that asymmetry to accept
first.

## Related canon version

Authored against canon `0.7.0`. **This ADR does not itself amend the
canon.** `CANON_VERSION` stays `0.7.0` as a direct result of this ADR.

PACK-10 as a whole, however, does require a canon amendment: the
domain introduces or materially clarifies system-wide concepts no
accepted canon section currently covers — an authoritative financial
record, an immutable balanced ledger, independent finance audit as a
workflow, a purpose-scoped financial party reference, and the
submission-versus-acceptance distinction for a financial report among
them. The determination and reasoning are in
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`, with the proposed
text in `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` and the
proposed step `0.7.0 → 0.8.0`. That amendment is a separate, dedicated
round from this ADR, in the shape ADR-032 and ADR-037 kept the
organizational-scope canon amendment separate from the ownership
decision itself.

Neither this ADR's acceptance nor the canon amendment landing alone
authorizes implementation of `services/finance-service`. No service
directory, package, schema, OpenAPI file or reason-code registry file
is created by this round. Implementation is separate and later,
gated on both this ADR reaching `accepted` and the canon amendment
landing — neither authorizes it alone.
