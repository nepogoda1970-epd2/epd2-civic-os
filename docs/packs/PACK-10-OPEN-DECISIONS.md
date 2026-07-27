# CLAUDE-PACK-10 — Open decisions

Consolidates every question `docs/packs/PACK-10-SPECIFICATION.md` and
ADR-048 through ADR-053 refused to answer by guessing, in one place,
for owner/legal/security review before any PACK-10 implementation
round is authorized. Nothing below is decided. Each item states the
question, why it is open, and — where one is defensible — a
recommended default. **A legally unverified default is not law and
must not be seeded into an implementation without owner and legal
confirmation.** Resolving an item does not, by itself, authorize
implementation — per the specification's own section 22 and the
governing baseline, only an explicit owner/legal/security-reviewed
authorization does that.

## OD-1 — Exact German legal report taxonomy

Which sections and line items must the `Rechenschaftsbericht`
(financial accountability report) actually contain, in what order,
under which headings, and with which mandatory subtotals? This is a
statutory question (Parteiengesetz reporting form) that the
specification deliberately declines to encode. **Recommended default,
legally unverified:** the report structure is driven entirely by a
`FinancePolicy(report_structure)` version, seeded from a template a
lawyer has reviewed line by line, and it is never hard-coded into
`reporting.py`. No implementation may ship a fixed section list as a
constant. Depends on / affects: `PACK-10-SPECIFICATION.md` sections
4.9 and 13; `PACK-10-ACCEPTANCE-MATRIX.md` report-lifecycle tests;
ADR-051.

## OD-2 — Membership-dues indirection

May dues accounting lawfully use a purpose-scoped dues reference
issued by `membership-service`, rather than accepting a
`membership_id` directly? Section 9.4 chose the indirection to avoid
giving the finance domain a membership register, but whether German
party-finance law and the party's own statutes permit dues accounting
at that level of indirection is unresolved. Depends on / affects:
`PACK-10-SPECIFICATION.md` section 9.4; ADR-050.

## OD-3 — Contribution aggregation perimeter

At which organizational perimeter is aggregation legally required:
the party's single legal entity, each Landesverband, or each
Kreisverband? The specification aggregates on `(handle, policy
period, perimeter, policy version)` but leaves "perimeter" itself
undefined as a legal fact. **Recommended default, legally
unverified:** aggregate at the party's legal reporting perimeter, as
named by the applicable `FinancePolicy(report_perimeter)` version for
the relevant jurisdiction — never at an arbitrary organizational
scope chosen by convenience. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 4.4 and 10; hard invariant 14;
ADR-050.

## OD-4 — Legally relevant contributor categories

Which contributor categories are legally significant (natural person,
legal person, unincorporated association, foreign entity, and so
on), and which of them are prohibited or restricted from contributing
at all? Section 4.4 requires these as "policy-governed values" but
proposes none as fact. Depends on / affects:
`PACK-10-SPECIFICATION.md` section 4.4; hard invariants 16 and 17;
`FinancePolicy(contribution_classification)`,
`FinancePolicy(contribution_restriction)`; ADR-050.

## OD-5 — Reporting and disclosure thresholds

What are the actual monetary values above which a contribution must
be reported, aggregated, or disclosed with a donor's name? These are
legal facts specific to German party-finance law and this round
asserts none of them, deliberately (section 4.4, section 13 rule 4).
No default is offered here; a default for a legal threshold is exactly
the kind of guess this document exists to refuse. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 4.4, 4.9 and 13;
`FinancePolicy(disclosure_threshold)`,
`FinancePolicy(approval_threshold)`; ADR-050; overlaps OD-1.

## OD-6 — Related contributors and intermediary chains

What legally and structurally constitutes a "related party" or an
"intermediary" for aggregation purposes — shared beneficial
ownership, a declared control relationship, a documented pass-through
payment, or something narrower or broader? Hard invariant 15 requires
that known related or intermediary contributions aggregate with their
principal, but the specification leaves the definition of "known
related" to a future policy. Depends on / affects:
`PACK-10-SPECIFICATION.md` section 4.4; hard invariant 15;
`related_party_group_reference`; ADR-050.

## OD-7 — Public disclosure granularity

Must a donor be named in public disclosure, and if so, under what
conditions and at what aggregation level? Section 9.6 is explicit that
PACK-10 holds no name and that any required naming is a separate,
authorized disclosure act sourced from a PACK-11 declaration document
— but whether naming is required at all, and at what threshold, is a
legal question the specification refuses to resolve. Depends on /
affects: `PACK-10-SPECIFICATION.md` section 9.6; hard invariants 35
and 36; `FinancePolicy(public_disclosure)`; overlaps OD-5 and OD-13.

## OD-8 — Sponsorship versus donation classification

What is the precise counter-performance test that separates a
sponsorship (payment with agreed counter-performance) from a donation
(contribution without one)? Section 4.5 and hard invariant 20 require
that the distinction never be inferred from amount or payer alone, but
the test itself — what counts as adequate counter-performance, and
who evaluates adequacy — is not specified. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 3 item 4 and 4.5; hard invariant
20; `FinancePolicy(sponsorship_classification)`; ADR-053.

## OD-9 — External sign-off model

Which body approves the `Rechenschaftsbericht`, who is the legally
responsible signatory, and may the preparer of the report also be its
signatory? Section 4.9 separates `approved`, `signed`,
`accepted_by_authority` as distinct states, and section 4.10
separates report preparer from report approver from legally
responsible signatory as distinguishable actions — but does not
decide whether one natural person may hold more than one of those
positions. **Recommended default, conservative and legally
unverified:** preparer and auditor must always be different
authorities (this much is already closed by hard invariant 31); a
preparer may serve as signatory only where German law and the
party's own statutes explicitly permit it, and absent explicit
permission the default is to keep preparer and signatory separate.
Depends on / affects: `PACK-10-SPECIFICATION.md` sections 4.9 and
4.10; hard invariant 34; ADR-051.

## OD-10 — `finance_administrator` versus `organizational_administrator`

Is the new institutional role `finance_administrator` incompatible
with PACK-08's existing `organizational_administrator` role in the
same scope, the way it is already incompatible with `finance_auditor`
(hard invariant 31, canon 19e.16 rule 3)? The specification's
incompatibility analysis (section 4.10, ADR-052) enumerates
`finance_administrator` against auditor and against the other new
finance roles, but does not state a position on this specific pair,
and no such incompatibility appears anywhere in the specification
text. **Recommended default:** incompatible — an
`organizational_administrator` in a scope should not also hold
`finance_administrator` in that same scope, for the same reason
self-assigned institutional authority is already forbidden (PACK-08
section 9.3 rule 6). Depends on / affects:
`PACK-10-SPECIFICATION.md` section 4.10; ADR-052; PACK-08 section 9.3.

## OD-11 — Organizational consolidation policy

Whether, and on what authority, higher organizational levels may
consolidate lower-level budgets and reports is named as something
section 4.8 and section 10 must specify — and section 10 does specify
the mechanism (descendant-mode read, `ConsolidationRecord`,
`FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED` on absence of authority) —
but not the governing question of _which_ scopes are legally required
or merely permitted to consolidate, and under what statutory or
statutes-based authority. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 4.8 and 10; hard invariant 39;
ADR-050.

## OD-12 — Historical corrections versus restatements

Which corrections to a closed or submitted period require a full
restatement (a new report version, section 4.9) versus a next-period
adjustment (an ordinary correcting entry in the current open period,
section 4.1)? The specification distinguishes correction from
mutation structurally (section 3 item 2) and preserves prior versions
(hard invariant 26), but does not draw the line for which class of
error requires which remedy. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 4.1 and 4.9; hard invariants 6,
25 and 26; ADR-049; ADR-051.

## OD-13 — Statistical disclosure control thresholds

What minimum cell size, and what combination/suppression rules,
should apply before a public financial view is emitted, per hard
invariant 36? **Recommended default, statistically and legally
unverified:** mirror PACK-04's accepted small-cell precedent
(ADR-015) as the starting minimum-cell-size rule, pending its own
statistical and legal review specific to finance data — it is not
adopted as correct for this domain, only as the nearest accepted
precedent. Depends on / affects: `PACK-10-SPECIFICATION.md` section
4.11; hard invariant 36; `FinancePolicy(statistical_disclosure)`;
PACK-04 ADR-015; overlaps OD-7.

## OD-14 — Legal retention periods for finance records

What are the actual retention durations for each class of finance
record (journal entries, contributions, sponsorship agreements,
report versions, audit engagements), and how do they bind to PACK-09's
`RecordClass` taxonomy? Section 11 and hard invariant 24 establish
that finance records bind to a PACK-09 `RecordClassRef` and that
PACK-09 retention semantics govern — including PACK-09's own
supersession rule — but the specific record-class-to-retention-period
mapping for finance records is not stated anywhere in this
specification. Depends on / affects: `PACK-10-SPECIFICATION.md`
section 11; hard invariant 24; PACK-09 `RecordClass`/retention model.

## OD-15 — Typed `FinanceRecordRef` on `FinanceEvidenceRef`

Should PACK-09 later accept a typed `FinanceRecordRef` in place of the
opaque `external_reference` string currently carried by
`FinanceEvidenceRef`? Section 11.1 names this explicitly as an
"optional future step, explicitly not required," requiring its own
PACK-09-side ADR in a separate round if adopted. **Recommended
default:** not now — keep the addition-only path open by having
PACK-10 mint `external_reference` strings in a documented, parseable,
scoped form from day one, so a future typed alias can be added without
breaking existing references, but do not attempt the PACK-09-side
migration in this round or the next implementation round. Depends on
/ affects: `PACK-10-SPECIFICATION.md` section 11.1;
`PACK-10-CROSS-PACK-BOUNDARIES.md` section 3.2; ADR-053.

## OD-16 — Ownership of external-authority integration surfaces

Who owns the external-authority submission gateway, payment-provider
and bank/PSD2 integration, and tax filing integration? Section 5 is
explicit that "no pack owns these yet" and that PACK-10 models only
the governed facts (`PaymentAuthorization`, `SubmissionRecord`,
`ImportBatch`) such an integration would later feed. This is a
genuine ownership gap, not merely an open question about how an
existing owner should behave. Depends on / affects:
`PACK-10-SPECIFICATION.md` section 5; ADR-053; future pack
assignment (none exists yet).

## OD-17 — Currency scope

Is PACK-10 EUR-only, or must it support multiple currencies from the
first implementation round — and if multi-currency, who owns the
conversion policy (rate source, rate date, rounding) referenced by
hard invariant 8's "no cross-currency arithmetic without a recorded
conversion"? The specification's `Money` model (section 4.1, hard
invariants 8 and 9) is currency-explicit and currency-agnostic in
shape, but does not decide the scope question itself. Depends on /
affects: `PACK-10-SPECIFICATION.md` section 4.1; hard invariants 8, 9
and 55; ADR-049.

## OD-18 — Chart of accounts

Should the implementation adopt a standard German party-finance chart
of accounts, or a party-specific one, and who approves changes to it
once adopted? Section 4.1 and section 8 fix the mechanism —
`AccountClassification` is `FinancePolicy(chart_of_accounts)` content
plus a code on the account, never a free string — but not the content
of the chart itself or its governance process. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 4.1 and 8; `FinancePolicy
(chart_of_accounts)`; ADR-048.

## OD-19 — PACK-10 / PACK-35 division

Where exactly does PACK-10's financial-external-influence ownership
end and PACK-35's general lobbying and meeting disclosure ownership
begin? Section 4.5 states the boundary rule in principle — PACK-10
owns a subject with a measurable financial value, PACK-35 owns a
contact, meeting, access or influence relationship without one — and
gives a worked example (a meeting that produces a sponsorship
agreement yields two records, neither owning the other). What remains
open is every case that does not cleanly fall on one side: a
subsidized service with a disputed valuation, an in-kind benefit whose
financial character is contested, or a relationship that starts
non-financial and becomes financial mid-lifecycle. Depends on /
affects: `PACK-10-SPECIFICATION.md` section 4.5;
`PACK-10-CROSS-PACK-BOUNDARIES.md` section 5; ADR-053.

## OD-20 — Repository-compatibility range versus canon-first ordering

`docs/canonical/canon-version.json` currently declares
`"repository_compatibility": ">=0.1.0 <0.10.0"`. A PACK-10
implementation round that moves `REPOSITORY_VERSION` to `0.10.0`, as
section 19 proposes, would fall outside that declared range. Two
sub-questions are open together: whether the declared range is widened
to admit `0.10.0`, or the canon amendment round lands first and moves
the range itself; and the ordering question — the specification's own
position (section 17, section 19) is that the canon amendment round
(`CANON_VERSION` `0.7.0` to `0.8.0`) must land before any PACK-10
implementation round, but this is recorded here as the owner decision
it actually requires, not as something already settled by the
specification alone. Depends on / affects:
`PACK-10-SPECIFICATION.md` sections 17 and 19;
`docs/canonical/canon-version.json`;
`PACK-10-CANON-AMENDMENT-PROPOSAL.md`.

## OD-21 — In-kind valuation methodology

Which valuation standards are acceptable for an in-kind contribution
or benefit (market value, replacement cost, a party-specific method),
and who approves a given valuation method for use? Hard invariant 19
requires a valuation method, valuation date and evidence reference for
every in-kind contribution, and hard invariant 55 requires the method
be recorded rather than implicit — but the specification does not
name which methods are acceptable or who authorizes them. Depends on
/ affects: `PACK-10-SPECIFICATION.md` sections 4.4 and 4.7; hard
invariants 19 and 55; `InKindValuation`.

## OD-22 — Home of the purpose-scoped party handle registry

Should the purpose-scoped party handle registry (`FinancePartyHandle`
minting and resolution) live inside `finance-service` at all, or in a
future dedicated party-register pack shared by finance and other
purpose-scoped identity needs? Section 7 currently assigns this to
`partyregistry.py` within `finance-service`, restricted to a single
module with its own resolution authority (section 9.5).
**Recommended default:** `finance-service` owns it now, confined to
`partyregistry.py` exactly as specified, with the extraction into a
dedicated pack left open as a future option rather than pre-built.
Depends on / affects: `PACK-10-SPECIFICATION.md` sections 7 and 9;
ADR-050.

## Status summary

| ID    | One-line question                                         | Default offered       | Resolves via         |
| ----- | --------------------------------------------------------- | --------------------- | -------------------- |
| OD-1  | Legal report taxonomy of the `Rechenschaftsbericht`       | Yes (policy-driven)   | Legal                |
| OD-2  | Dues indirection via `membership-service` reference       | No                    | Legal                |
| OD-3  | Aggregation perimeter (entity/Land/Kreis)                 | Yes (unverified)      | Legal                |
| OD-4  | Legally relevant contributor categories                   | No                    | Legal                |
| OD-5  | Reporting and disclosure threshold values                 | No                    | Legal                |
| OD-6  | Definition of related party / intermediary chain          | No                    | Legal                |
| OD-7  | Public donor-naming granularity                           | No                    | Legal                |
| OD-8  | Sponsorship counter-performance test                      | No                    | Legal                |
| OD-9  | Sign-off model: approver, signatory, preparer overlap     | Yes (unverified)      | Owner / Legal        |
| OD-10 | `finance_administrator` vs `organizational_administrator` | Yes                   | Owner / Architecture |
| OD-11 | Consolidation authority across organizational levels      | No                    | Owner / Legal        |
| OD-12 | Correction versus restatement boundary                    | No                    | Legal / Architecture |
| OD-13 | Statistical disclosure control thresholds                 | Yes (unverified)      | Legal / Security     |
| OD-14 | Retention periods bound to PACK-09 record classes         | No                    | Legal                |
| OD-15 | Typed `FinanceRecordRef` on PACK-09's placeholder         | Yes (not now)         | Architecture         |
| OD-16 | Owner of external-authority/bank/tax integration          | No                    | Owner                |
| OD-17 | Currency scope and conversion-policy ownership            | No                    | Owner / Architecture |
| OD-18 | Chart of accounts source and change approval              | No                    | Owner / Legal        |
| OD-19 | Financial-influence boundary against PACK-35              | No                    | Architecture / Legal |
| OD-20 | Repository-compatibility range and round ordering         | Yes (canon-first)     | Owner / Architecture |
| OD-21 | In-kind valuation methodology and approval                | No                    | Legal / Architecture |
| OD-22 | Home of the purpose-scoped party handle registry          | Yes (finance-service) | Architecture         |

No test, build, lint or CI run was performed to produce this document;
it is a documentation-only artefact and nothing in it was executed.
