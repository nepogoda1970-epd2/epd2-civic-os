# ADR-054: Canon minor-version addition: Party Finance & Financial Accountability Context (0.7.0 → 0.8.0)

## Status

`proposed`

## Date

2026-07-27

## Context

`docs/packs/PACK-10-SPECIFICATION.md` and its six decision ADRs —
ADR-048 (`finance-service` decomposition), ADR-049 (ledger, balanced
posting, correction model), ADR-050 (purpose-scoped financial party
references, lawful aggregation), ADR-051 (`Rechenschaftsbericht`
lifecycle, snapshot, authority semantics), ADR-052 (finance authority
separation, incompatible roles, independent audit) and ADR-053
(PACK-09/PACK-11/PACK-35 boundaries) — are all `proposed`, not
`accepted`, and each declines to authorize implementation.
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md` is the governing
determination: it tests PACK-10 against the same two-option framework
ADR-037's own round used for PACK-08, and concludes, concept by
concept (its section 3, nine concepts), that a canon amendment is
required and **not conditional** — every disqualifying condition for
"no amendment" is present at once: a new cross-system invariant
(balanced posting, period-closure enforcement, snapshot-before-report,
submission-is-not-acceptance), a new institutional role set, a new
trust boundary (PACK-35, PACK-11, delivery-telemetry-is-not-
legal-effect), and new shared vocabulary (`Money`, `JournalEntry`,
`AuditConclusion`, `ReportSnapshot`, `FinancePartyHandle`, more).

The precedent for how this is done is exact:
`docs/packs/PACK-08-SPECIFICATION.md` and ADR-032 through ADR-036 were
each accepted while explicitly declining canon authority, and ADR-037
was the single, dedicated, later round whose acceptance both
authorized and performed the canon edit `0.6.0 → 0.7.0`.
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` is this round's
counterpart to ADR-037's own drafting step — reviewed text for
section `19f`, section `20.17`, and the section `22`/`23`/`24`
additions. This ADR is the governing ADR of that dedicated round,
exactly as ADR-037 was for PACK-08's — the amended canon text's own
preamble (`19f`'s opening paragraph) already names ADR-054 as
"управляющий ADR раунда" ("the round's governing ADR").

## Problem

Canon section 22 is the only place an entity's owning module is fixed
(`INV-02`); section 23 is the only canonical list of prohibited edges;
section 20 is the event catalogue, with section 21's envelope reused
unchanged; and only canon can state that one entity name is not
another domain's entity of the same name. No pack-level artifact —
ADR, specification, or a future `contracts/reason-codes/pack-10.yml`
registry — can add a row to section 22, an entry to section 23, a
name to section 20, or vocabulary binding across services. PACK-10
needs all four: twenty-one ownership-matrix rows, forbidden-link
entries, an event-catalogue subsection, and entity names distinguished
from three existing canon names (`Contribution`, 13.2; `Account`,
7.2; `PublicLedgerEntry`, 19a.1). Four new `role_code` values and an
incompatibility-matrix extension likewise cannot come from pack-level
configuration alone, because the incompatibility baseline itself is
canon text (19e.16). None of this is achievable short of a canon
minor version.

## Considered options

- Option A — Specify PACK-10 purely as an implementation of already
  accepted general canon concepts, with no canon edit. Rejected: the
  amendment assessment's section 3 finds this false outright for at
  least three concepts (3.1 authoritative financial record, 3.2
  balance as an invariant, 3.8 the financial external-influence
  boundary — none has any accepted canon analogue), and only
  partially true for the remaining six, where canon supplies a
  general principle but never the specific mechanism PACK-10 needs.
  Twenty-one aggregates with no section 22 row leave `INV-02`
  unsatisfiable, and PACK-10's events would form a second, competing
  catalogue outside section 20.
- Option B — Amend the canon as a minor version, adding a new lettered
  section between 19e and 20 by the same non-renumbering technique
  already used for 19a–19e. **Chosen.**
- Option C — A major canon version bump. Rejected: canon section 25's
  `Major` category is reserved for changing an existing required
  field, event meaning, entity owner, architectural invariant,
  anonymity rule, or critical-object lifecycle; this amendment changes
  none of those — every addition is new and additive, the same
  standard every prior canon addition (`0.2.0` through `0.7.0`) was
  held to, so section 25's `Minor` criteria apply exactly.
- Option D — Defer the amendment to the implementation round, letting
  a future `finance-service` build define canon-relevant concepts as
  it goes. Rejected: this is precisely the ordering failure
  `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md` section 7 and
  ADR-037's own precedent exist to prevent — implementation with no
  section 22 rows would violate `INV-02` from its first commit, and
  letting code fix canon vocabulary afterward is how a second
  catalogue would emerge.

## Decision

**Amend canon to `0.8.0`, adding new section `19f`** ("Партийные
финансы и финансовая отчётность / Party Finance & Financial
Accountability Context"), inserted between sections 19e and 20 without
renumbering any existing section — the same non-renumbering technique
already used for 19a through 19e. As in ADR-037, this ADR's acceptance
would be what authorizes the edit; in this candidate archive the edit
is already performed alongside this ADR, for review as one unit — it
is not yet an accepted canon edit (see Status).

The canon edit, as it stands in this archive, does the following.

- Inserts section `19f` with twenty-five subsections, `19f.1` through
  `19f.25`: entity overview (`19f.1`); four terminology separations
  against 13.2, 7.2, 19a.1, 18.1 (`19f.2`); `Money` and monetary
  determinism (`19f.3`); the authoritative ledger and balanced posting
  (`19f.4`); accounting period and controlled reopening (`19f.5`); the
  transaction register, provenance, import and reconciliation
  (`19f.6`); the contribution lifecycle and its exceptional states
  (`19f.7`); aggregation and the anti-splitting rule (`19f.8`);
  sponsorship, external benefit and the PACK-35 boundary (`19f.9`);
  expenses and the authorize/execute split (`19f.10`); assets and
  obligations (`19f.11`); budgets and actuals (`19f.12`); the
  `ФИН-01`–`ФИН-45` hard finance-invariant register (`19f.13`);
  institutional roles of the finance domain (`19f.14`);
  `FinancePartyHandle` (`19f.15`); reporting obligation, perimeter and
  report snapshot (`19f.16`); the `Rechenschaftsbericht` lifecycle
  (`19f.17`); independent finance audit and `AuditConclusion`
  (`19f.18`); organizational consolidation (`19f.19`); finance policy,
  effective dating and version binding (`19f.20`); public financial
  views and disclosure control (`19f.21`); boundaries with other packs
  (`19f.22`); structural separation from every other context (`19f.23`);
  the events/codes/links/ownership cross-reference (`19f.24`); and the
  implementation gate (`19f.25`).
- Fixes the normative `ФИН-01` through `ФИН-45` register of forty-five
  hard finance invariants in `19f.13`: no global identifier, scope
  isolation and fail-closed handling, ledger immutability and
  balancing, period-closure and dual-control reopening,
  budget-never-a-source-of-truth, anti-splitting aggregation,
  contribution fail-closed handling, snapshot-before-report,
  telemetry-is-never-legal-effect, auditor independence,
  authority-name-is-not-proof, public-view non-authoritativeness,
  statistical disclosure control, no correlation into voting,
  consolidation-is-read-only, and provenance/duplicate detection.
  `ФИН-44`/`ФИН-45` directly restate `INV-03` and 19e.12 for finance.
- Extends the **open** `role_code` list of 19e.15 with four new roles
  — `finance_administrator`, `payment_authorizer`, `payment_executor`,
  `report_signatory` — alongside `finance_auditor`, already canon and
  unchanged. Extends the 19e.16 incompatibility baseline, stricter and
  never softer: `finance_auditor` incompatible with each of the four
  new roles and with whoever prepared or approved the report it
  reviews; `payment_authorizer` incompatible with `payment_executor`
  for the same payment; a claimant incompatible with reviewing,
  approving, authorizing or executing their own claim; and, recorded
  explicitly as **an adopted owner decision** rather than a
  specification default, `finance_administrator` incompatible with
  `organizational_administrator` within the same legally relevant
  scope — reviewed against 19e.15/19e.16 and found to conflict with
  nothing already accepted. Four further separations (transaction
  creator/reviewer, report preparer/approver) stay action-level
  authority references on the act itself, never institutional roles,
  so the privileged role surface does not expand by nine roles where
  four suffice. This closes a canon defect rather than creating one:
  19e.16 rule 3 already forbade combining `finance auditor` with
  `finance administrator`, while `finance_administrator` was never a
  member of 19e.15's enumerated `role_code` values — canon forbade a
  combination involving a role it never itself defined; `19f.14`
  closes this by enumerating `finance_administrator`.
- Defines `FinancePartyHandle` (`19f.15`): an opaque, service-minted
  identifier valid for exactly one reporting perimeter and one declared
  purpose, never derived from a name, account, membership, credential,
  participation or voting-linked value, or from another handle;
  sameness of one legal party is a governed, reason-coded, audited
  matching act; resolution needs a separate authority and emits an
  access-audit event carrying no resolved value; the handle is
  personal data, never published, and the section names by name what
  it never stores — identity, address, birth date, tax/national
  identifiers, banking details, identity-document data, contact data,
  credential values, membership/participation identifiers,
  voting-linked values.
- Defines the twelve-state `Rechenschaftsbericht` lifecycle (`19f.17`):
  `draft` → `internally_reviewed` → `auditor_reviewed` → `approved` →
  `signed` → `submitted` → `externally_acknowledged` →
  `externally_accepted` → `published` → `amended` → `restated` →
  `superseded`, with `externally_accepted` reachable only from an
  explicit authoritative reference (a governed `NoticeEffectDecision`/
  `NoticeEffectRef`, PACK-09, ADR-043 semantics), never from delivery,
  receipt or read telemetry.
- Defines governed, effective-dated `FinancePolicy` (`19f.20`), the
  sole carrier of every threshold, category, chart-of-accounts entry,
  disclosure class and approval rule; an open `policy_kind` list of at
  least seventeen kinds, extensible at repository level and never by
  canon edit (the `organization_profile` technique, 19e.3); binding of
  every protected decision to a policy version; and a hard rule
  against backdating `effective_from` into a closed or submitted
  period.
- Defines safe public financial projections (`19f.21`): derived,
  versioned, never authoritative, publishable only from a `published`
  report version, carrying their own provenance, with statistical
  disclosure control applied before emission and no
  `FinancePartyHandle` or handle-deriving value ever exposed.
- Fixes the implementation gate (`19f.25`, detailed below): this
  section defines the canonical model only, and authorizes no code,
  database, migration, event bus, schema, registry, frontend or
  production integration by itself.
- Adds section `20.17` ("Партийные финансы"), fixing **seventy-two**
  finance event names in six groups, all created exclusively by
  `finance-service`: sixty-nine names verbatim from
  `docs/packs/PACK-10-SPECIFICATION.md` section 14, plus three names
  this edition adds — `import_batch.duplicate_detected`
  (duplicate/replay import detection, `19f.6`), `finance_report.amended`
  and `finance_report.superseded` (the twelve-state lifecycle,
  `19f.17`). Every event's minimum/prohibited payload, effective/
  recorded time, policy-version reference, audit linkage and
  idempotency are documented in `20.17` itself; section 21's envelope
  is reused unchanged, so no `event_version` bump is implied.
- Extends section 22 (ownership matrix) with **twenty-one** new rows,
  one per aggregate, all owned by `Finance Service`: `FinanceAccount`,
  `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`,
  `ImportBatch`, `ReconciliationRecord`, `FinanceContribution`,
  `SponsorshipAgreement`, `ExternalFinancialBenefit`, `ExpenseClaim`,
  `PaymentAuthorization`, `Budget`, `FinancialAsset`,
  `FinancialObligation`, `ReportingObligation`,
  `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`,
  `AuditEngagement`, `FinancePolicy`, `FinancePartyHandle` — all
  physically realized by one new service, `finance-service` (ADR-048,
  not created by this round), the "one physical service, several
  canonically named modules" principle already used for
  `transparency-service`, `governance-service` and
  `organization-service`. No existing row changes.
- Extends section 23 (forbidden links) with new entries, each carrying
  the `(добавлено 0.8.0, 19f.x)` marker: voting/tally/ballot/delegation
  isolation; `FinancePartyHandle` non-reuse/non-publication and
  resolution-only-by-registry-module; budget-line actual-value/ledger
  write prohibitions; public-view non-authoritativeness;
  document-reference non-assertion of authenticity/admissibility;
  telemetry-is-not-legal-effect; role-name-is-not-proof-of-authority;
  policy backdating; posted-entry/frozen-snapshot in-place edit;
  reclassification-as-bypass; consolidating-scope and audit-authority
  write prohibitions.
- Extends section 24 (reason codes) with **forty-five** new codes:
  forty-four `FINANCE_*` codes verbatim from
  `docs/packs/PACK-10-SPECIFICATION.md` section 15.2, plus
  `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`, introduced by `19f.17` for
  the rejected transition into `externally_accepted` absent an
  authoritative reference. Thirty-two existing codes are reused
  verbatim; none is renamed or repurposed.
- Moves `CANON_VERSION` `0.7.0 → 0.8.0`, mirrored across
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py` and
  `packages/typescript/epd2-types/src/version.ts`, with both
  packages' version-constant tests updated to expect `0.8.0`, and
  `scripts/verify_versions.py` passing across all three sources plus
  the canon file (canon section 25: backward-compatible, additive,
  minor — no existing required field, event meaning, entity owner,
  invariant, anonymity rule or critical-object lifecycle is altered).

**`REPOSITORY_VERSION` stays `0.9.0`.** This is a canon-only change.
**No `services/finance-service` directory, source file, JSON Schema,
OpenAPI file, migration, frontend page, or reason-code registry file
was created** by this round. Implementation remains a separate, later
round, gated on **both** ADR-048 through ADR-053 **and** this canon
content — authorized by **neither alone** (19f.25). This ADR is itself
`proposed`, so the amended canon text present in this candidate
archive is a **CANDIDATE awaiting review**, not an accepted canon
edit; nothing in this round claims otherwise.

## Consequences

**Easier:** a future, separate `finance-service` round has a single,
stable vocabulary to build against — twenty-one named aggregates each
with a fixed owner, seventy-two named events, and forty-five named
reason codes — instead of inventing one and risking a second,
competing catalogue. The `ФИН-01`–`ФИН-45` register gives that round,
and its tests, a fixed checklist instead of scattered specification
prose. The closed 19e.16/19e.15 defect (`finance_administrator` now
enumerated) removes an inconsistency that blocked a literal reading.

**Harder:** canon section 19f is long — twenty-five subsections — and
any future refinement of finance policy thresholds, the
non-combinable-role matrix, or the report lifecycle must be read
against this full text. The `finance_administrator` ×
`organizational_administrator` incompatibility is now a canon-level
constraint, so any exception needs its own governed policy decision,
never a silent combination. Because this text is additive and not yet
implemented, consequences are entirely for a future implementation
round.

## Security impact

The amendment adds **prohibitions**, not capabilities: no new data
access is granted. `FinancePartyHandle` resolution needs a separate,
explicitly issued authority and emits an access-audit event carrying
no value (`19f.15`); public views may never expose a handle, a
handle-deriving value, bank details, identity-document data, or
vote-linked data (`19f.21`, `19f.23`); no financial entity, event, or
payload forms a correlation bridge into voting (`19f.23`, `ФИН-36`);
and no event carries identity data beyond identifiers, enumerations,
time, codes and versions (`ФИН-02`). `grants_data_access` and
`grants_procedural_authority` remain independent fields on PACK-08
authority records, unchanged by this round. The four new role codes
and extended incompatibility baseline close a real separation-of-
duties gap (authorizer ≠ executor, claimant ≠ approver, auditor ≠
administrator) without any new grantable capability beyond what
19e.15/19e.17 already govern. Independence re-verification at audit
opening, at each finding, and at conclusion (`19f.18`, `ФИН-29`)
strengthens `INV-08` rather than weakening it.

## Data impact

**Additive only.** No existing canonical entity, field, status, owner,
event or reason code is changed, renamed or repurposed:
`Contribution` (13.2), `Account` (7.2), `PublicLedgerEntry` (19a.1),
`AuditEvent` (18.1), `Organization` (8.1), `RoleAssignment` (8.4),
`OrganizationalAuthority` (19e.15) and `Membership` (8.3) are
unchanged. Deliberate divergences from the specification are named,
not silently introduced: the canon report lifecycle states
`externally_accepted`, `amended`, `restated` and `superseded` replace
the specification's `accepted_by_authority` and `amended_or_restated`
(specification section 8's own phrasing); three events are added
beyond the specification's catalogue —
`import_batch.duplicate_detected`, `finance_report.amended`,
`finance_report.superseded`; and one reason code is added beyond its
list — `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`. Each divergence is
recorded in canon text itself (`19f.17`, `19f.24`).

## Migration impact

**None for data.** There is no finance data, no
`services/finance-service`, database or schema to migrate — canon
defines the model only. The four new `role_code` values are
**additive configuration on PACK-08's already extensible field**:
19e.15 declares the list open, so no existing
`OrganizationalAuthority`/`RoleAssignment` record changes or needs
revalidation; the extended 19e.16 baseline constrains only future
assignments. `PACK-09` reference types (`LegalCaseRef`, `DeadlineRef`,
`NoticeRef`, `NoticeEffectRef`, `HoldRef`, `RecordClassRef`,
`JurisdictionRef`, `CasePartyRef`) are unchanged; 19f consumes them
as-is. `docs/canonical/canon-version.json` gains compatibility
metadata: `"minimum_repository_version": "0.9.0"` and
`"finance_context_implementation_status": "not_implemented"`,
alongside the existing `"repository_compatibility"` band.

## Reversibility

**Reversible only by a further canon version.** Once accepted, undoing
or narrowing any part of section `19f` — removing an aggregate, an
event, an ownership row, a `ФИН-` invariant, or a `role_code` value —
is itself a canon edit and must go through the same governed process
this ADR follows, exactly as ADR-037 already established for 19e.
Today, nothing depends on this text: no service reads it, no data is
shaped by it, and no test suite outside this candidate archive assumes
it, because no code implements `finance-service` and none is
authorized to (`19f.25`). Reverting this candidate, before acceptance,
remains a documentation-only change with no downstream effect.

## Related canon version

Authored against canon `0.7.0`. This ADR, once accepted, would be the
authorization for the canon-text edit to `0.8.0` — in this candidate
archive the edit is already present alongside this ADR for review as
one unit, exactly as ADR-037 both authorized and performed the `0.7.0`
edit for PACK-08. See `docs/canonical/TZ-00-domain-event-canon.md`
section `19f` for the complete canonical text this ADR would
authorize and record:

```text
CANON_VERSION = 0.8.0 (candidate, this archive)
Previous version: CANON_VERSION = 0.7.0
```

This is a canon-only change: no `services/finance-service` directory,
JSON Schema, OpenAPI file, or reason-code registry was created, and no
PACK-01 through PACK-09 source code was touched. `REPOSITORY_VERSION`
remains `0.9.0`; `finance-service` implementation remains a separate,
later task, gated on this canon content **and** ADR-048 through
ADR-053, authorized by neither alone. **This ADR's status is
`proposed`, not `accepted`** — the amended canon text here is a
CANDIDATE for review, matching the assessment's and proposal's own
repeated qualification that no version bump, ADR acceptance, or
implementation authorization is performed by determination or
proposal alone.
