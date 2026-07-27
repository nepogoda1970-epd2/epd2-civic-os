# ADR-046: Purpose-scoped financial party references and lawful aggregation without a global user ID

## Status

`proposed`

## Date

2026-07-27

## Context

PACK-10 (party finance) has to identify five kinds of financial
counterparty — a contributor, a sponsor, an expense claimant, an
obligation counterparty, a report signatory — well enough to run
threshold evaluation, prevent split-transaction evasion, enforce
auditor independence and self-approval bans, and answer "who gave how
much" for public disclosure. Canon INV-01 and the PACK-10
specification's hard invariant 1 ("no global user ID",
`docs/packs/PACK-10-SPECIFICATION.md` section 6, row 1) forbid the
obvious shortcut: a single, reusable identifier for a person that
finance, membership, voting and identity could all resolve the same
way.

This is not a new problem class for the repository. ADR-031 (PACK-07)
already rejected one universal identity hash across domains and
introduced the `DomainPseudonymReference` concept — a pseudonym scoped
to a domain, non-linkable across domains without the issuing service's
own cooperation. PACK-09's `references.py` already restates the same
doctrine operationally: "a reference is never a person" — `CasePartyRef`
wraps a per-case handle minted by `casework.mint_case_party_reference`,
meaningless outside the case, resolvable by no one but the casework
module itself. PACK-10 needs the same shape, adapted to finance's own
governed-matching and aggregation requirements, which is what this ADR
records (`PACK-10-SPECIFICATION.md` sections 4.4, 6 invariants 1, 2,
14, 15, 16, 37, 38, 48, 8.2.7, 8.2.21, and 9 — hereafter cited by
section number alone).

Finance also has a complication neither ADR-031 nor PACK-09's case
parties fully face: many financial counterparties are not platform
participants at all. A donor may hold no `IdentityRecord`, no
`Membership`, no credential of any kind. Section 9.1 states this
explicitly as a three-way split in who owns identity, and the design
below has to work for all three cases with one reference shape, not
three.

## Problem

Without a resolved design, PACK-10 faces two failure modes that pull
in opposite directions:

1. **Under-identification.** If contributions cannot be linked to the
   same contributor, threshold evaluation and split-transaction
   evasion detection (HI-14, HI-15) are impossible — a donor could
   split one large, reportable contribution into several
   below-threshold ones and no mechanism could recognize the pattern.
2. **Over-identification.** If PACK-10 solves (1) by minting or
   reusing a person-scoped identifier — a `PersonId`, or worse, the
   contributor's `Membership` or `IdentityRecord` id — it creates
   exactly the correlation bridge canon INV-01 and HI-37/HI-38 forbid:
   an actor who can read both finance records and participation or
   voting records could now link a person's financial behavior to
   their political participation, which is the one linkage this
   platform's entire security architecture (ADR-031) exists to
   prevent.

A third pressure compounds both: public transparency law can require
naming a donor above a threshold, which looks like it demands storing
a name — but section 9.6 and this ADR both hold that it does not.

## Considered options

- **Option A — a global `PersonId`/contributor id shared across
  domains.** Rejected. Violates canon INV-01 and HI-1 directly: a
  single identifier resolvable in finance, membership and identity
  contexts alike is precisely the "one universal identity hash"
  ADR-031 already closed off for the identity/voting boundary, and
  extending it to finance would reopen the same class of error for a
  domain ADR-031 did not anticipate.

- **Option B — reuse `Membership` or `IdentityRecord` identifiers
  inside finance records.** Rejected. Even without a new identifier
  type, embedding an existing membership or identity id in a
  `Contribution` or `SponsorshipAgreement` creates a correlation
  bridge between finance and participation/voting the moment any
  actor or export can see both sides (HI-38). It also violates
  section 9.1's ownership split: PACK-10 would be reading
  `membership-service`'s and `identity-service`'s owned data directly,
  contrary to HI-47 (no direct access to another service's storage).

- **Option C — a purpose-scoped, service-minted opaque handle
  (`FinancePartyHandle`) with a governed matching act.** **Chosen.**
  Mints an id inside PACK-10 itself, derived from nothing external,
  scoped so it cannot travel outside its own purpose and perimeter,
  with sameness established by an audited act rather than by shared
  key material.

- **Option D — fully anonymous contributions with no sameness
  tracking.** Rejected. Satisfies HI-1 trivially by refusing to solve
  the problem: without any mechanism for recognizing that two
  contributions came from the same party, HI-14 and HI-15 (aggregation
  cannot be defeated by splitting; known related or intermediary
  contributions must aggregate) become unenforceable, and the
  legally required threshold evaluation in section 4.4 is impossible.

| Option | Solves aggregation | Avoids global ID  | Avoids correlation bridge |
| ------ | ------------------ | ----------------- | ------------------------- |
| A      | yes                | no                | no                        |
| B      | yes                | yes (no new type) | no                        |
| C      | yes                | yes               | yes                       |
| D      | no                 | yes               | yes                       |

## Decision

**Option C.** PACK-10 introduces `FinancePartyHandle`
(`partyregistry.py`, section 8.2.21), an opaque, service-minted UUID.
It is derived from nothing: not a name, not an account, not a
membership, not a credential, not a participation identifier, and not
another handle (HI-1, HI-38, HI-48). It is scoped to a
**(reporting perimeter, declared purpose, handle-policy version)**
triple. The declared purpose is one of: contribution, sponsorship,
expense claimant, obligation counterparty, signatory (section 9.2).

### Sameness is a governed act, not a computed link

A handle does not encode who its holder is, so recognizing "these two
contributions are from the same contributor" cannot be a lookup — it
has to be a decision. `partyregistry.py` is the only module that may
make it: an authorized actor, with the relevant declaration and
PACK-11 evidence references in front of them, records that a
contribution belongs to an existing handle or mints a new one. The act
is reason-coded and audited (section 9.4). Handle merges — when two
previously separate handles are later determined to be the same legal
person within the same perimeter and purpose — are governed,
authorized and append-only (section 8.2.21); a merge is never a silent
rewrite.

### Aggregation runs on the handle, not the transaction

Threshold evaluation and split-transaction detection use the
aggregation key **(handle, policy period, perimeter, policy version)**
(HI-14). Declared `related_party_group_reference` and intermediary
declarations extend that key, so contributions that arrive through a
declared related party or intermediary chain still aggregate with
their principal even though they are separate transactions (HI-15).
An unresolved aggregation fails closed:
`FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`. The decisive aggregate
for a given assessment is frozen into an `AggregationSnapshot`
attached to that assessment's append-only history entry (section
8.2.7), so a later handle-policy version can never silently rewrite a
past acceptance, rejection or threshold decision — the snapshot is
what was actually decided on, permanently.

### Three-way ownership of identity

Section 9.1's split is binding on this design, not incidental to it:

| Party kind                        | Authoritative identity owner            | What PACK-10 holds                                                                           |
| --------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------- |
| Platform participant (member)     | `identity-service` (`IdentityRecord`)   | Nothing of `IdentityRecord`; a `FinancePartyHandle` only                                     |
| Platform participant (membership) | `membership-service` (`Membership`)     | A purpose-scoped dues reference, not a `membership_id`                                       |
| External donor, sponsor, vendor   | A PACK-11 document (nobody on-platform) | A `FinanceEvidenceReference` plus `identity_verification_status` and the recording authority |
| Actor performing a finance action | PACK-08 (`OrganizationalAuthority`)     | The authority reference, never the person                                                    |

For platform members contributing dues, PACK-10 does **not** accept a
`membership_id`. It accepts a purpose-scoped dues reference issued by
`membership-service` — the same domain-pseudonym pattern ADR-031
already anticipated for the identity/participation boundary — and only
`membership-service` can resolve it. This makes dues accounting
possible without giving the finance domain a membership register.
Whether German party-finance law and the party's own statutes permit
dues accounting at that level of indirection is an **open legal
question (OD-2)**; this ADR records it as open and does not resolve
it, consistent with `PACK-10-SPECIFICATION.md`'s own treatment.

### What is stored, and what must never be

| Stored (section 9.2)                                              | Never stored (section 9.3)                              |
| ----------------------------------------------------------------- | ------------------------------------------------------- |
| `FinancePartyHandle` (opaque UUID, purpose- and perimeter-scoped) | Names                                                   |
| Legally required party category (policy-governed value)           | Addresses, dates of birth                               |
| `identity_verification_status` + recording authority              | National or tax identifiers                             |
| `FinanceEvidenceReference` to PACK-11 material                    | Bank-account details (IBAN, account/card numbers)       |
| `related_party_group_reference` (itself a handle)                 | Identity-document numbers or images                     |
| —                                                                 | Email addresses, telephone numbers                      |
| —                                                                 | Credential values, membership/participation identifiers |
| —                                                                 | Vote-related values                                     |
| —                                                                 | Free-text fields that could carry any of the above      |

Bank details are named explicitly (not merely implied by "identity
data") because a finance service is the one place they would feel
natural to store; PACK-10's payment-rail exclusion (section 5) means
nothing in this pack needs them, and the threat model tracks
bank-detail leakage as its own threat (`PACK-10-THREAT-MODEL.md`
T-26).

### Resolution is separately authorized and separately audited

`partyregistry.py` is the only module permitted to resolve a handle —
the operation that connects a handle back to the evidence that
identifies its holder. Resolution requires a **separate, explicitly
granted resolution authority**, distinct from the authority that mints
handles or assesses contributions, and every resolution emits its own
`finance_party_handle.resolved` access-audit event recording who
resolved it, under what authority, and for what stated purpose — and
**never the resolved value itself** (section 9.5). An attempt to
resolve without that authority fails closed:
`FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`.

### No cross-purpose or cross-perimeter presentation

A handle minted for the contribution purpose is meaningless in the
sponsorship purpose, in membership, in voting, or in another
reporting perimeter. There is no cross-purpose lookup anywhere in the
design (HI-48); presenting a handle outside its own (perimeter,
purpose) pair fails closed with
`FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH`.

### Public reporting without names

PACK-10 holds no names, so a legally required naming of a large donor
cannot be produced from PACK-10 data by construction. Where the law
requires it, naming is a separate, explicitly authorized disclosure
act, sourced from the PACK-11 declaration document, and recorded as
its own governed decision outside PACK-10's ordinary public-projection
path (section 9.6). **The absence of names in PACK-10 is the design,
not a gap the implementation round is expected to fill.** What must
legally be published, and under what circumstances, is an **open
legal question (OD-7)**, recorded as open.

## Consequences

Aggregation, threshold evaluation and split-contribution detection
become possible without a global identifier, because sameness is a
recorded governed act rather than a computed correlation. Auditor
independence and self-approval checks (HI-30–HI-32) can bind to a
stable handle across a party's history within one purpose and
perimeter. What becomes harder: every "who is this contributor"
question that is not a resolution act with recorded authority and
purpose is, by design, unanswerable from stored data — including to
PACK-10's own developers reading the database directly. Cross-domain
reporting that would want to say "this donor is also a member" cannot
be built inside PACK-10 at all; it would require a separate, governed,
cross-service act outside this pack's scope. Handle merges being
append-only means a mis-mint that is later corrected leaves the
original, now-`merged_into`, handle permanently visible in history
rather than removed — accepted as the cost of an auditable correction
trail.

## Security impact

Pseudonymization alone does not create anonymity. A
`FinancePartyHandle` is personal data: it is re-identifiable by
design, by an authorized actor, through the registry's own governed
matching and resolution acts. The model limits _correlation_ (a handle
cannot be used to reach another purpose, perimeter or domain) and
_accidental exposure_ (resolution is separately authorized and
audited, and no handle or resolved value ever reaches an event
payload, public view, report snapshot or audit payload — HI-2). It
does **not** by itself satisfy any data-protection obligation:
PACK-09's processing registry, legal-basis determination and DPIA
machinery apply to PACK-10's processing exactly as they do to any
other service's, unchanged, and PACK-10 claims no exemption from them
(section 9.8).

Toward voting specifically, the anti-correlation guarantee is
absolute by construction, not by policy: no vote, ballot, delegation,
credential or tally linkage exists anywhere in PACK-10 (HI-37 —
enforced structurally, by the absence of any import of voting, tally,
delegation, credential or eligibility modules), and a
`FinancePartyHandle` must not be correlatable to any participation
reference (HI-38) — it is derived from nothing that could make such a
correlation possible in the first place, extending ADR-031's
anti-correlation invariant from the identity/voting boundary to the
finance/voting boundary it did not originally cover.

`projections.py` is the single export chokepoint for every public or
cross-service view (HI-35, section 9.7); a future PACK-12 data-loss-
prevention layer attaches there, and only there, rather than needing
to audit every call site in the service.

## Data impact

New, proposed canonical concepts this ADR identifies for a future
canon-edit task (not added to canon by this ADR): `FinancePartyHandle`,
`ContributionPartyRef`, `related_party_group_reference`,
`AggregationSnapshot`, `FinanceEvidenceReference`, and
`identity_verification_status` as a field on the party-handle
aggregate. No existing canonical entity outside PACK-10's own new
aggregates gains or loses a field. No global user identifier, voter
identifier, credential identifier or ballot identifier is introduced
anywhere (HI-1, HI-37), mirroring canon section 9's own opening
statement.

## Migration impact

None. No PACK-10 code, schema or canon content exists yet; this ADR
fixes a reference architecture and a set of open legal questions
(OD-2, OD-7), not an implementation. `PACK-10-SPECIFICATION.md`
section 17 already determines that PACK-10 as a whole requires a
canon amendment (`CANON_VERSION` moving `0.7.0 → 0.8.0` in a separate,
dedicated round); this ADR does not perform that amendment and does
not itself change `docs/canonical/canon-version.json`.

## Reversibility

Reversible at this stage, in the same sense ADR-031 is: this ADR fixes
an abstraction and a set of invariants, not a concrete handle-minting
algorithm or storage technology. Once an implementation exists, a
specific handle-policy version can be superseded by a new one without
breaking the design, because handles are already versioned by
`handle-policy version` and every governed decision binds to the
policy version it used. What would carry real migration cost is
reversing the _shape_ of the decision itself — for example,
introducing a shared identifier across purposes after real handles and
`AggregationSnapshot`s exist — which would require re-deriving every
historical aggregation and would conflict with the frozen-snapshot
guarantee this ADR relies on to keep past decisions stable.

## Related canon version

Authored against canon version `0.7.0`. This ADR proposes no canon
edit itself. PACK-10 as a whole requires a canon amendment
(`docs/packs/PACK-10-SPECIFICATION.md` section 17: `CANON_VERSION`
`0.7.0 → 0.8.0`, proposed, as a separate, dedicated round); the
concepts this ADR identifies (`FinancePartyHandle` and related types)
are candidates for that amendment, gated on it, not on this ADR's own
acceptance. No test, build or verification step was run for this ADR;
it is a documentation-only record of a design decision.
