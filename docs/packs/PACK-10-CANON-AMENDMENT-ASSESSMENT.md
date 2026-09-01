# CLAUDE-PACK-10 — Canon amendment assessment

**Status: determination only.** This document decides whether PACK-10
requires an amendment to `docs/canonical/TZ-00-domain-event-canon.md`. It
edits no canon file, changes no version constant and authorizes no
implementation; `CANON_VERSION` remains `0.7.0` and `REPOSITORY_VERSION`
`0.9.0`. The proposed canon text is in
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`. The authoritative source
for every PACK-10 fact cited here is
`docs/packs/PACK-10-SPECIFICATION.md` (sections 3, 6, 8, 9, 10, 13, 14,
15, 17), which nothing below contradicts.

## 1. The two options the governing request defines

**Option 1 — no canon amendment required.** Admissible only if PACK-10 is
fully specifiable as an _implementation of already accepted general canon
concepts_, introducing no new cross-system invariant, no new institutional
role, no new trust boundary and no new shared vocabulary. PACK-10's
concepts would then be service-local control metadata, carried entirely by
pack-level artefacts: ADRs, a specification, a
`contracts/reason-codes/pack-10.yml` registry and a future service
directory.

**Option 2 — canon amendment required.** The outcome if any one of those
four exclusions is present.

The test is not novel, and PACK-09 answered it the other way: ADR-039's
"Related canon version" section records "Canon `0.7.0`, no bump," on the
express ground that `GovernedRecord`, `RetentionPolicy` and `LegalHold`
are "compliance-side control metadata owned by one service" whose events
reuse canon section 21's envelope unchanged, and that elevating them to
canon entities "would require its own amendment ADR." PACK-09 is the live
precedent for option 1; the contrast with PACK-10 makes this
determination decidable.

## 2. Conclusion

**Option 2. A canon amendment is required — not optional, not
conditional.** This matches `docs/packs/PACK-10-SPECIFICATION.md`
section 17 and ADR-048 through ADR-053. PACK-10 fails the option-1 test
on all four exclusions at once:

- **New cross-system invariants** — balanced posting, correction-only
  change of posted entries, period-closure enforcement,
  snapshot-before-report, submission-is-not-acceptance.
- **New institutional roles** — four additions to PACK-08's
  `OrganizationalAuthority.role_code` set (`finance_administrator`,
  `payment_authorizer`, `payment_executor`, `report_signatory`) plus an
  extension of canon 19e.16's incompatibility baseline.
- **New trust boundaries** — financial external influence against
  PACK-35, document references against PACK-11, and
  delivery-telemetry-is-not-legal-effect for a financial report.
- **New shared vocabulary** — `Money`, `JournalEntry`, `AuditConclusion`,
  `ReportSnapshot`, `FinancePartyHandle` and sixteen further aggregates,
  plus three deliberate separations from existing canon names (3.2).

## 3. Concept-by-concept determination

For each of the nine concepts the governing request names: whether an
accepted canon section covers it, which one, and what is genuinely new.
Six of the nine are partially covered, and the precision matters — that is
where an amendment gets written too broadly.

### 3.1 Authoritative financial record

**Not covered by any accepted canon section.** Canon `0.7.0` contains no
concept whose subject is money. The nearest two are neither: `AuditEvent`
(18.1) records _an action_, and `PublicLedgerEntry` (19a.1) is a
_published civic transparency_ record whose `subject_type` enum has no
financial member. Canon 5's twelve contexts (5.1–5.12) contain no finance
context, and section 22 has no row that could own a financial record.
**New:** an authoritative record of monetary effect and of the business
fact behind it, a context to hold it, and owner rows in section 22.

### 3.2 Immutable balanced ledger

**Partially covered — as a principle, not a mechanism.** Immutability is
already canon: INV-05 ("Нельзя бесследно изменять историю"), 19a.1's
`Неизменяемость и исправления` (a correction is a new entry, never an
edit) and 19c.2's `supersedes_ai_processing_record_id`. PACK-10's
correction-not-mutation model is a faithful instance of that.

**New:** _balance_ as an invariant. Nothing in canon requires a record to
satisfy an arithmetic identity, and canon defines no monetary value type.
`Money` (integer minor units, currency code, scale, rounding rule), the
debit/credit `PostingLine`, and the rule that debit and credit sums are
equal per currency at construction _and_ again at posting are a new
invariant of the same rank as INV-06's rule freeze. Also new, and why
this cannot be folded into existing vocabulary: **three name
separations** — the finance `Contribution` is not canon 13.2's (a
deliberation utterance, Discussion Service), the accounting account is
not canon 7.2's `Account` (a platform user account, Account Service), and
the accounting ledger is not canon 19a's public transparency ledger.
Specification section 3 rules 1–3 and section 15.3 keep events and codes
apart with the `finance_`/`FINANCE_` prefix, but canon's ownership matrix
cannot hold two entities of one canonical name.

### 3.3 Independent finance audit

**Partially covered — the role exists, the workflow does not.**
`finance_auditor` is already canon: a listed value in
`OrganizationalAuthority.role_code` (19e.15) and one of the seven named
institutional roles in 19e.16 ("независимое ревизионное полномочие над
финансовыми записями в рамках scope"). The incompatibility is canon too —
19e.16 rule 3 forbids `finance auditor` and `finance administrator` for the
same organization and scope. PACK-10 preserves both verbatim. **New:**
everything procedural — canon has no engagement, no finding, no conclusion,
no rule on when independence is re-checked. PACK-10 adds `AuditEngagement`
(`opened` → `in_progress` → `concluded`), append-only `AuditFinding` and one
create-once `AuditConclusion` — named "conclusion" so no stored object reads
as a statutory audit opinion — plus the rules that independence is
re-verified at opening, at each finding and at conclusion, and that the
auditing module never writes into an aggregate it audits. PACK-10 also
exposes a canon defect rather than creating one: **`finance_administrator`
is named in 19e.16 rule 3 but is not a member of 19e.15's `role_code`
list**, so canon forbids a combination involving a role it never enumerates.
That list is open, so four additions are additive configuration — but the
incompatibility baseline is canon text, and extending it with
authorizer-is-not-executor and claimant-is-not-approver is a canon edit.

### 3.4 Purpose-scoped financial party reference

**Partially covered — as a deferred concept, which is the opposite of
covered.** Canon 19d.17 records `DomainPseudonymReference` and
`AntiCorrelationInvariant` as _deferred_, and 19e.18 fixes eight
identity-minimization rules PACK-10 satisfies and never weakens. PACK-09's
`CasePartyRef` is the closest precedent and was never canonized. **New:** an
owned, audited aggregate with a restricted resolution surface.
`FinancePartyHandle` is keyed on (reporting perimeter, declared purpose,
handle-policy version); sameness is established by a governed, reason-coded
matching act, never by a platform identifier; resolution needs a separate
authority and emits `finance_party_handle.resolved`, carrying no resolved
value; the handle is never published in any form. Two statements are
cross-system facts, not finance detail: threshold aggregation runs on the
handle, so anti-splitting is structural; and the handle **is personal data**
— pseudonymization is not anonymity (specification section 9.8). Canon has
no place where either can be read.

### 3.5 Report snapshot

**Partially covered — the pattern is accepted, the invariant is not.**
Canon has the freeze pattern twice, `EligibilitySnapshot` (9.3) and
`DelegationSnapshot` (16.2); if `ReportSnapshot` were only that, option 1
would be arguable for this concept alone. **New:** the gate.
`ReportSnapshot` is create-once, must survive every later report version,
and no preparation, validation or submission may occur without one
(`FINANCE_REPORT_SNAPSHOT_MISSING`) — a hard precondition on a lifecycle
canon does not contain, binding period locks, policy versions and ledger
state at one instant. The existing snapshots gate nothing.

### 3.6 Submission versus legal acceptance

**Partially covered — at ADR level, and for a different subject.** Canon
19d.12 already separates a recorded decision from its formal confirmation
(`DigitalDecision.status = formal_confirmation_required` producing an
`AssemblyDecision`), so "recorded ≠ legally effective" is accepted. The
delivery-telemetry boundary is accepted here too, but as ADR-043; canon
`0.7.0` names no `OfficialNotice`, `NoticeEffectDecision` or `LegalHold`
at all, by ADR-039's deliberate choice. **New:** a separation canon
nowhere states — submission ≠ external acknowledgement ≠ acceptance by an
authority — plus a fourth axis, publication ≠ approval.
`accepted_by_authority` is reachable only from an explicit authoritative
reference, and no delivery, receipt or read-status field may be an input
to any transition. A `Rechenschaftsbericht` is a legally consequential
external artefact, so this is a trust boundary in canon's sense.

### 3.7 Finance-specific separation of duties

**Partially covered — the principle is INV-08 and 19e.17.** INV-08
("Критические действия требуют разделения полномочий") and 19e.17's eight
lifecycle rules (no self-assignment; no dual-control act completed by one
person; proposal separated from activation) state the principle generally,
and PACK-10 restates rather than replaces them. **New:** the separations and
their count. PACK-10 separates nine acts — transaction creator, transaction
reviewer, finance administrator, payment authorizer, payment executor,
report preparer, report approver, legally responsible signatory, finance
auditor — of which four become institutional `role_code` values and five
stay action-level separations recorded on the act (ADR-052). Keeping five of
nine _out_ of the role vocabulary is itself canon-relevant: it is how the
platform declines to expand its privilege surface, and 19e.16's baseline is
where that limit belongs. Period reopening as a dual-control action, and the
claimant-cannot-approve-authorize-or-execute rule, are new named pairs.

### 3.8 Financial external-influence boundary

**Not covered.** Canon 19a.4's `LobbyLogEntry` (Lobby Log Service, with
`related_subject_type` and `contact_method`) is a contact record, not a
financial one. Canon contains no sponsorship concept, no
counter-performance concept and no rule dividing financial from
non-financial influence. **New:** the boundary rule, stated so it can be
tested — a record is PACK-10's when its subject is a measurable financial
value or a financially valued benefit attributable to a party
organization, and PACK-35's when its subject is a contact, meeting,
access or influence relationship with no financial value recorded. A
meeting that produces a sponsorship agreement yields two records, one
typed reference, neither owning the other. That is a cross-pack ownership
rule, which is what canon section 23 exists to fix.
`ExternalFinancialBenefit` (paid third-party support, in-kind campaign
support, subsidized service, guarantee, forgiven debt) is vocabulary with
no canon analogue.

### 3.9 Public financial disclosure safeguards

**Partially covered, and the case most likely to be misjudged.** Canon 19a
genuinely has a public ledger (`PublicLedgerEntry`, 19a.1), a versioned
`DisclosurePolicy` with per-field `field_rules` (19a.3), the rule that a
structurally prohibited field can never be reclassified into any class other
than `prohibited`, and a `small_cell_threshold`. PACK-10 reuses that
accepted model rather than inventing a second one. **But 19a is a
transparency ledger, not accounting.** Its subject is the publication of
civic records — initiatives, versions, moderation decisions, result
publications, audit events — and its `subject_type` enum has no financial
member. A published financial statement is not a `PublicLedgerEntry`, and
`DisclosurePolicy` does not govern figures computed from a ledger it cannot
see. **New:** derived public financial views as a named, non-authoritative,
versioned artefact class; only a published report version is publishable and
a draft never is; provenance (version, snapshot reference, perimeter,
status) on every view; statistical disclosure control _before_ emission; and
no public view may expose a party handle, a handle count, or any value from
which handle sameness could be inferred.

## 4. Why pack-level mechanisms are insufficient here

Option 1 would have to carry all of the above through artefacts a pack
owns. It cannot, and the reasons are structural, not stylistic:

| Pack-level artefact cannot | Because                                                                                                                          | Consequence if attempted                                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Add ownership-matrix rows  | Canon section 22 is the only place an entity's owning module is fixed (INV-02)                                                   | Twenty-one aggregates with no row leave INV-02 unsatisfiable for them                                                       |
| Add forbidden links        | Canon section 23 is the only canonical list of prohibited edges                                                                  | Ten edge-prohibition invariants (HI-2, HI-12, HI-21, HI-22, HI-28, HI-35, HI-37, HI-38, HI-48, HI-53) bind no other service |
| Add canonical events       | Canon section 20 is the event catalogue; section 21's envelope is reused unchanged                                               | Sixty-nine names outside section 20 form a second, competing catalogue                                                      |
| Add entity vocabulary      | Only canon can state that the finance `Contribution` is not canon 13.2's, or that a finance account is not canon 7.2's `Account` | Two entities share one canonical name by convention only                                                                    |
| Amend canon by ADR alone   | ADR-010, ADR-013, ADR-018, ADR-023, ADR-028 and ADR-037 each fixed acceptance and canon edit as two authorized steps             | ADR-048 through ADR-053 are the first step and each says so                                                                 |

## 5. What would have to be true for option 1, and is not

| Option-1 condition                                                | Fact that defeats it                                                                                                                              |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Every concept is an instance of an accepted general canon concept | 3.1, 3.2 and 3.8 — no monetary concept, no balance rule, no sponsorship concept exists                                                            |
| No new cross-system invariant                                     | Balanced posting, period-closure enforcement, snapshot-before-report, submission-is-not-acceptance — each binds beyond `finance-service`          |
| No new institutional role                                         | Four additions to 19e.15's `role_code` set; extension of 19e.16's baseline; `finance_administrator` named in 19e.16 rule 3 yet absent from 19e.15 |
| No new trust boundary                                             | PACK-10/PACK-35; PACK-10/PACK-11 (a reference asserts nothing about authenticity, signature or admissibility); telemetry versus legal effect      |
| No new shared vocabulary                                          | Twenty-one aggregate names, nine value objects, four `role_code` values, three collisions with existing canon names                               |

Every concept would additionally have to be, in ADR-039's phrase for
PACK-09, "control metadata owned by one service." A balanced general
ledger whose figures become a legally submitted report is not control
metadata, and a purpose-scoped party handle that decides whether a legal
donation threshold is met is not either.

## 6. Consequential repository finding

`docs/canonical/canon-version.json` declares
`"repository_compatibility": ">=0.1.0 <0.10.0"`. A PACK-10 implementation
round would move `REPOSITORY_VERSION` from `0.9.0` to `0.10.0`
(`docs/packs/PACK-10-SPECIFICATION.md` section 19), which falls
**outside** that range — the canon file would declare itself incompatible
with the very repository version that first implements PACK-10. This is
recorded, not resolved: widen the range, or let the canon amendment round
land first and move the range as part of its own edit; the choice is the
owner's (`docs/packs/PACK-10-OPEN-DECISIONS.md` item OD-20). The only
claim made here is that the mismatch is real.

## 7. Ordering conclusion

**The canon amendment is a separate, dedicated round, and it must land
before any PACK-10 implementation round begins.** The pattern is
PACK-08's, exactly:

1. Specification and decision ADRs accepted (there ADR-032–ADR-036, here
   ADR-048–ADR-053), each declining to authorize implementation.
2. A dedicated canon round whose governing ADR authorizes and performs
   the edit (there ADR-037, `CANON_VERSION` `0.6.0 → 0.7.0`, reported in
   `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`). Here it would move
   `CANON_VERSION` `0.7.0 → 0.8.0` and add section 19f, section 20.17,
   section 22 rows, section 23 entries and section 24 codes.
3. Only then an implementation round, gated on the canon content and the
   accepted ADRs but authorized by neither alone.

The order cannot be reversed, and not for tidiness: an implementation
creating twenty-one aggregates with no section 22 rows would violate
INV-02 from its first commit, and its sixty-nine events would live outside
canon section 20 — the second-catalogue failure mode canon exists to
prevent.

## 8. What this document does not do

- It does not edit `docs/canonical/TZ-00-domain-event-canon.md`, which
  remains at 4514 lines and `CANON_VERSION 0.7.0`.
- It does not change `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py` or
  `packages/typescript/epd2-types/src/version.ts`.
- It does not perform the amendment; the text in
  `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` is a proposal.
- It accepts no ADR (ADR-048–ADR-053 remain `proposed`), authorizes no
  implementation, and claims no legal compliance, tax compliance,
  authority acceptance or production readiness.
