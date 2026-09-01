# ADR-053: PACK-10 / PACK-09 / PACK-11 / PACK-35 ownership boundaries

## Status

`proposed`

## Date

2026-07-27

## Context

PACK-10 (party finance) sits at the busiest ownership intersection of
any pack proposed so far. It is downstream of PACK-08
(`Organization`/`OrganizationalUnit`/`OrganizationalScope`/
`OrganizationalAuthority`) and PACK-09 (`LegalCase`/
`ProceduralDeadline`/`OfficialNotice`/`NoticeEffectDecision`/
`LegalHold`/`RecordClass`), and upstream of two packs that do not exist
yet: PACK-11 (governed documents and evidence) and PACK-35 (general
lobbying, meeting and non-financial influence disclosure).
`PACK-10-SPECIFICATION.md` sections 4.5, 5, 11 and 12 already state,
concept by concept, who owns what and why — this ADR does not
originate that decision, it records it as a formal boundary ADR so the
discipline ADR-012 and ADR-027 established for earlier packs (an
enumerated allow-list, named exclusions, a decidable test rather than
a vibe) applies here too, before any finance-service code exists.

PACK-09 already anticipated this intersection: its own `references.py`
(Architecture & Domain Framework 0.8.1 section 13.1) exports
`FinanceEvidenceRef` — a `PlaceholderRef` naming PACK-10 as owner — so a
PACK-09 case, filing, hearing or notice can point at finance material
without PACK-09 acquiring it. PACK-10's own specification revisits
whether that placeholder still holds now that PACK-10's entity set is
known, and separately defines the placeholder shape PACK-10 exports
toward PACK-11. Both questions, plus the PACK-10/PACK-35 division and
the concerns PACK-10 does not own, are decided together here because
they are one boundary problem, not four.

## Problem

Four risks exist without an explicit, enumerated ownership record:

1. Finance and lobbying/influence disclosure could silently overlap or
   silently gap — a sponsorship agreement negotiated in a meeting could
   be modelled twice (once financially, once as a contact record) with
   no shared reference, or modelled nowhere if each pack assumes the
   other owns it.
2. A future implementation could read `FinanceEvidenceRef` literally
   and conclude PACK-09 or PACK-10 owns evidence content, quietly
   duplicating what will become PACK-11's authoritative document and
   custody model.
3. A future PACK-10 implementation could treat a
   `FinanceEvidenceReference` (the placeholder PACK-10 exports toward
   PACK-11) as proof of authenticity, signature or admissibility simply
   because a reference exists, which would let an unverified document
   pointer masquerade as a governed fact.
4. Without a named list of what PACK-10 does not own — payment rails,
   tax filing, procurement, campaign management, voting — a later
   implementation could be asked to "just add" one under
   finance-service, reproducing the monolith risk ADR-048 already
   rejected for PACK-10's own decomposition, one level up, at the
   inter-pack boundary this time.

## Considered options

- Option A — no enumerated ownership table; each future pack's own
  specification (PACK-11, PACK-35) silently decides contested concepts
  as it is written, on a first-come basis.
- Option B — the decision below: one ownership table naming exactly
  one owner per contested concept, decided now and binding on
  PACK-08/09/10/11/12/13/14/35; a decidable PACK-10/PACK-35 test
  instead of a case-by-case judgment call; PACK-09 consumption
  restricted to its published reference types; a disposition for
  `FinanceEvidenceRef` (keep it, correct its documentation, add
  PACK-10's own reference types); one placeholder shape for the
  PACK-10 → PACK-11 boundary with no assertion fields; and a named
  list of concerns PACK-10 does not own, each with its actual or
  not-yet-existing future owner. Where the division is legally
  uncertain, the uncertainty is recorded as an open decision rather
  than resolved by assumption.
- Option C — merge PACK-10 and PACK-35 into one "external influence"
  pack on the theory that sponsorship and lobbying are causally
  related and a merged pack would need no boundary at all.

## Decision

**Option B.**

### Ownership table

| Concept                                                                                                                             | Owner   |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------- |
| Legal procedure, procedural deadlines, official notices and notice-effect decisions, legal holds, record classes/retention          | PACK-09 |
| Governed documents, document bytes, document-version chains, signed originals, evidence content and custody, admissibility          | PACK-11 |
| Finance records, financial valuation, financial disclosure of sponsorship and other financially measurable external benefits        | PACK-10 |
| General lobbying contacts, meetings, access, calendars, non-financial influence disclosure, parliamentary mandate-holder disclosure | PACK-35 |
| Organizations, organizational units, organizational scope, institutional authority                                                  | PACK-08 |
| Production data plane and schema registry                                                                                           | PACK-13 |
| Privileged administration and DLP                                                                                                   | PACK-12 |
| Real IAM/eID and qualified electronic signatures                                                                                    | PACK-14 |

Every concept above has exactly one owner. No row is jointly owned;
where two packs both touch a concept (e.g. a sponsorship agreement is
both a finance record and, potentially, a lobbying-adjacent event), the
resolution is two separately owned records connected by a typed
reference, never one record with two owners (below).

### The PACK-10 / PACK-35 test

Stated so it is decidable, not a matter of judgment per instance: a
record is PACK-10's when its subject is a **measurable financial value
or a financially valued benefit** attributable to a party organization.
A record is PACK-35's when its subject is a **contact, meeting, access
or influence relationship with no financial value recorded**. The test
applies to the record's subject, not to its origin — a finance record
and a lobbying record can originate from the same real-world event
without becoming the same record.

A meeting that produced a sponsorship is the canonical case: the
meeting itself, its participants, its calendar entry and its
non-financial purpose are PACK-35's `LobbyingMeeting`-shaped record; the
resulting agreement, its value and its counter-performance are PACK-10's
`SponsorshipAgreement`. This is **two records, one typed reference,
neither owning the other** — PACK-10 does not gain a meeting entity by
recording a sponsorship, and PACK-35 does not gain a valuation field by
recording a meeting.

PACK-10 implements no PACK-35 entity (HI-21, section 4.5, section 6
row 21): no meeting, contact, calendar or access entity exists anywhere
in `finance-service`, structurally enforced by
`test_service_boundaries.py::test_no_pack35_lobbying_entity_exists_in_finance_service`.
PACK-10 exposes only typed integration points for PACK-35 to consume
later (`PACK-10-CROSS-PACK-BOUNDARIES.md` section 5) — PACK-10 does not
import, call, or depend on PACK-35, since PACK-35 does not exist yet;
the dependency direction, once PACK-35 is specified, runs PACK-35 →
PACK-10, mirroring the general rule that a newer pack may read an
older one's published references but not vice versa.

Where the financial/non-financial division is legally uncertain — a
subsidized venue whose market-value gap is disputed, or an access
arrangement whose benefit is real but not yet valued — this ADR
records the uncertainty as **OD-19**, not a silent resolution. A record
in that state stays wherever it was first created until OD-19 is
resolved by the project owner; this ADR picks no default owner for the
uncertain case, since doing so would be the silent resolution the
boundary rule above forbids.

### PACK-09 consumption — reference-only

PACK-10 consumes PACK-09 exclusively through PACK-09's published
`services/compliance-service/src/epd2_compliance_service/references.py`
types. No PACK-09 reference is ever resolved by PACK-10 into PACK-09's
storage or domain layer (HI-47, canon INV-03).

| PACK-09 reference type | PACK-10 use case                                                     |
| ---------------------- | -------------------------------------------------------------------- |
| `LegalCaseRef`         | A legal case about a finance violation, dispute or correction        |
| `DeadlineRef`          | A procedural deadline for reporting, correction, return or response  |
| `DeadlineTriggerRef`   | The recorded fact that a specific trigger started that deadline      |
| `NoticeRef`            | A notice document-shape from or to an authority, before legal effect |
| `NoticeEffectRef`      | The governed decision that gives a notice legal effect (ADR-043)     |
| `HoldRef`              | A legal hold freezing finance records                                |
| `RecordClassRef`       | Retention-class binding for a finance record                         |
| `JurisdictionRef`      | The competent-authority determination for a finance case kind/scope  |
| `CasePartyRef`         | A party to a finance-related case — never resolved to a person       |

Four rules bind every use of this table, restated here as the formal
boundary decision rather than mere guidance:

1. **PACK-10 does not decide PACK-09 case procedure.** It opens or
   cites a case by `LegalCaseRef`; the case's own lifecycle,
   admissibility, hearings, decisions and remedies stay PACK-09's.
2. **PACK-10 derives no legal effect from delivery or read telemetry.**
   Only a governed `NoticeEffectDecision`, surfaced as a
   `NoticeEffectRef`, starts a deadline or makes an authority response
   legally effective (ADR-043; HI-27, HI-28, section 4.9).
3. **PACK-10 cannot destroy held records.** It re-reads PACK-09 hold
   state, by `HoldRef`, immediately before any disposal-relevant
   action, and never caches it (HI-23).
4. **No cross-service direct storage access.** Every PACK-09 fact
   PACK-10 needs arrives through one of the reference types above, or
   through a published PACK-09 `application`-layer read function —
   never a PACK-09 storage or domain import (canon INV-03, HI-47).

### `FinanceEvidenceRef` — remains sufficient, corrected and extended

PACK-09 already exports `FinanceEvidenceRef` (`PlaceholderRef` subclass,
`owner = PlaceholderOwner.PACK_10_FINANCE`, open `kind`, opaque
`external_reference`, `organization_id`) so a PACK-09 case, filing,
hearing or notice can point at finance material without PACK-09 owning
it. This ADR's disposition: **it remains sufficient and needs no
replacement now**, with three specified changes, none implemented in
this round.

1. **Documentation-level semantic correction.** The name says
   "evidence," but the object it points at is a PACK-10 _finance
   record_ — a transaction, contribution, sponsorship agreement, report
   version or snapshot — not evidence content, which is PACK-11's
   (HI-22, ownership table above). This ADR and PACK-10's own
   `references.py` must both state this so no reader infers that
   holding a `FinanceEvidenceRef` means holding evidence.
2. **Addition, not migration.** PACK-10 exports its own `ScopedRef`-
   shaped reference types for later packs and for PACK-09's own use:
   `FinanceRecordRef`, `FinanceReportRef`, `FinanceReportVersionRef`,
   `ContributionRef`, `SponsorshipRef`, `FinanceAuditEngagementRef` and
   `FinancePartyHandleRef`. Each carries an id plus organizational
   scope and nothing else, mirroring PACK-09's `ScopedRef` shape and
   its load-bearing reasons (a reference carries its scope, carries no
   content, and is never a person). `FinancePartyHandleRef` is
   resolvable by nobody outside `partyregistry.py`.
3. **Optional future step, explicitly not required now.** PACK-09
   could later accept a typed `FinanceRecordRef` in place of the opaque
   `external_reference` string on `FinanceEvidenceRef`. That would be a
   change to PACK-09's own module, and therefore a PACK-09-side ADR, in
   a separate round, with its own review (`PACK-10-CROSS-PACK-
BOUNDARIES.md` section 3.2, **OD-15**). This ADR records the option and
   specifies what would need to be true to exercise it; it does not
   implement it and does not require it.

**Migration path, specified now so the option stays open later:**
PACK-10 mints `external_reference` strings in a documented, parseable,
scoped form from day one — not an arbitrary opaque string. If the
project owner later exercises option 3, PACK-09 can add a typed alias
that parses the same strings without breaking any reference already in
existence. This is specified, not implemented, in this round.

### PACK-11 boundary — one placeholder shape, no assertion fields

PACK-10 defines exactly one placeholder shape for material PACK-11
will own: `FinanceEvidenceReference`, mirroring PACK-09's
`PlaceholderRef` precedent — `owner = PlaceholderOwner.PACK_11_DOCUMENTS`,
an open `kind` string that **PACK-11, not PACK-10, defines the
taxonomy for**, an opaque `external_reference`, and organizational
scope: invoices, receipts, contracts, bank statements, valuation
reports, donation declarations, sponsorship agreement documents, audit
working papers, signed reports, submission receipts and publication
renditions.

PACK-10 stores metadata and scoped references only: which kind of
document is expected, whether one is present, which finance record it
belongs to, and when the reference was recorded. PACK-10 never stores
document bytes, document content, signatures, cryptographic chains or
evidence custody (HI-22, ownership table above).

**Structural, not conventional, non-assertion.** `FinanceEvidenceReference`
has no `is_authentic`, `is_signed`, `is_admitted`, `is_valid` or
`is_publishable` field — the type itself makes it impossible to read
such a fact off a reference, rather than relying on a naming
convention nobody is forced to follow. Wherever a finance action would
need one of those assertions, it fails closed instead of assuming one:
`FINANCE_EVIDENCE_REFERENCE_MISSING` when no reference exists at all,
and `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` when a reference exists
but the governed determination it would require does not.

**Four future PACK-11 interface requirements**, stated as requirements
PACK-10 will consume rather than a design PACK-10 imposes on PACK-11:

1. resolve a reference to a document's existence and kind within an
   organizational scope;
2. report a signature or signed-original status as a governed
   determination, not an inferred one;
3. report an admissibility determination;
4. produce a publication rendition identifier that a public finance
   view can cite without exposing document content.

Until all four exist, PACK-10 records the reference and the absence of
the assertion — it does not simulate any of the four with a local
heuristic.

### Explicitly out of scope, with named future owners

PACK-10 does not own, and this ADR does not assign to any existing
pack, the following — each is either an already-named future owner or
an open decision:

- **Payment providers, bank/PSD2 integration, automated transfers, tax
  filing, a real external-authority submission gateway** — no pack owns
  these yet (**OD-16**). PACK-10 models only the governed facts such an
  integration would later feed (`PaymentAuthorization`,
  `SubmissionRecord`, `ImportBatch`), and nothing else.
- **Voting, tally, delegation** — structurally isolated from PACK-10,
  no import edge in either direction (HI-37, HI-38), owned by the
  existing accepted PACK-15/16 architecture.
- **Public procurement as a general domain** — not owned by PACK-10,
  which covers only its own financially governed procurement facts
  (expenditure classification, payment authorization; section 4.3).
- **Campaign management beyond financially governed references** — not
  owned by PACK-10, which covers only the financial facts a campaign
  produces (expenditure, sponsorship, in-kind contributions), never
  planning, messaging or operations.

## Consequences

`finance-service`'s `pyproject.toml` will, at implementation time,
declare no dependency on any future `pack-11-documents` or
`pack-35-lobbying` package — the boundary this ADR fixes is references
and placeholders, not a runtime import. `references.py` gains seven new
exported types (`FinanceRecordRef`, `FinanceReportRef`,
`FinanceReportVersionRef`, `ContributionRef`, `SponsorshipRef`,
`FinanceAuditEngagementRef`, `FinancePartyHandleRef`) and one exported
placeholder shape (`FinanceEvidenceReference`). PACK-09's own
`references.py` needs no code change to satisfy this ADR — its existing
`FinanceEvidenceRef` and `PlaceholderOwner.PACK_10_FINANCE` are kept as
is; only its module-level documentation gains the semantic correction
in item 1 above. `test_service_boundaries.py` gains a structural test
asserting no PACK-35 entity exists anywhere in `finance-service`, and
the acceptance matrix gains the two `FINANCE_EVIDENCE_*` fail-closed
tests. A future PACK-11 round can treat this ADR's four interface
requirements as a fixed consumer contract; a future PACK-35 round can
treat the PACK-10/PACK-35 test and the named integration points as
fixed, and inherits OD-19 as an open question it must help resolve,
not one it can silently answer alone.

## Security impact

The ownership table forecloses a failure this project has repeatedly
guarded against at every prior boundary (ADR-012, ADR-027): a concept
with two plausible owners silently gets a second, divergent
implementation, after which an auditor can no longer tell which record
is authoritative. The PACK-10/PACK-35 test closes a narrower version of
the same risk for the case most likely to arise in practice — a
sponsorship meeting — by fixing, in advance, that the financial fact
and the meeting fact are always two records connected by reference,
never one record asserting both. The `FinanceEvidenceReference`
non-assertion design is itself a security control: without it, a
careless finance-service code path could treat "a reference was
recorded" as equivalent to "the document is authentic and admitted,"
silently downgrading PACK-11's future admissibility guarantee to an
unverified claim. The PACK-09 four-rule consumption discipline extends
the narrow-read guarantees this project applies to every cross-pack
read (narrow, purpose-built, reference-only, re-read rather than
cached for hold state) to PACK-10's own first cross-pack read set.

## Data impact

No new canonical entity and no change to any PACK-08 or PACK-09
canonical entity, field, status, or owner. PACK-09's
`FinanceEvidenceRef` and `PlaceholderOwner.PACK_10_FINANCE` are
unchanged in shape; only their documented meaning is clarified. This
ADR specifies seven new PACK-10 reference types and one new PACK-10
placeholder type (`FinanceEvidenceReference`); all eight are additive,
`ScopedRef`- or `PlaceholderRef`-shaped, non-canon repository types —
consistent with how ADR-027 characterized its own new read functions.

## Migration impact

None. `services/finance-service` does not exist yet; PACK-11 and
PACK-35 do not exist yet. No existing PACK-01 through PACK-09 code,
schema, or published interface changes as a result of this ADR. The
one specified-but-not-required migration path (PACK-10 minting
parseable `external_reference` strings from day one, so PACK-09 could
later add a typed alias under OD-15) is a forward-compatibility
discipline, not a migration of anything that exists today.

## Reversibility

Reversible with high cost. The ownership table, the PACK-10/PACK-35
test, and the PACK-11 placeholder shape are boundary decisions this
project has consistently treated as expensive to reverse once either
side is implemented (ADR-012, ADR-027): moving ownership of a concept
between packs after both exist means migrating persisted data,
rewriting every typed reference that pointed at the old owner, and
re-auditing every consumer that relied on the old boundary. Reversing
this ADR before PACK-10, PACK-11 or PACK-35 has any implemented code —
the state as of this ADR — is comparatively cheap: a specification and
reference-type change, not a data migration.

## Related canon version

Authored against canon version `0.7.0`. PACK-10 as a whole requires a
canon amendment (`0.7.0 → 0.8.0`, proposed — see
`PACK-10-CANON-AMENDMENT-ASSESSMENT.md` and
`PACK-10-CANON-AMENDMENT-PROPOSAL.md`), but this ADR itself proposes no
canon edit: the ownership table, the PACK-10/PACK-35 test, and the
PACK-09/PACK-11 boundary rules it fixes are repository-level and
reference-type decisions, not canon entities, statuses, or invariants.
Where this ADR overlaps canon-amendment material (e.g. HI-21's
structural test), the canon-amendment proposal documents remain
authoritative for the amendment itself; this ADR does not restate or
supersede them.
