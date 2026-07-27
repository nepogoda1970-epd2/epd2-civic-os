# CLAUDE-PACK-10 — Cross-pack boundaries and dependency matrix

PACK-10 is not implemented. `PACK-10-SPECIFICATION.md` and ADR-049 have
already decided, concept by concept, who owns what across PACK-08,
PACK-09, PACK-10, PACK-11 and PACK-35; this document does not
re-decide anything. It restates that decision as one operational
reference: which pack owns each concept PACK-10 touches, which reads a
future finance-service implementation would make into other services,
which typed references PACK-10 consumes and which it would export, and
the edges that must never exist. The goal is a single place an
implementation round — and any reviewer checking it — can check itself
against, without re-deriving the boundary from the specification's
prose each time.

Nothing here authorizes implementation, creates a canonical entity, or
amends canon. Where this document restates a hard invariant (`HI-_n_`)
or an open decision (`OD-_n_`), the specification and ADR-049 remain
the authoritative source; this document only indexes them for a
finance-service implementation round to check itself against.

## 1. Ownership matrix

The fourth column uses three values only, in order of decreasing
access: **read via interface** (a call into another service's
published `application`-layer function, returning current state, never
cached across calls where the concept can change out from under a
finance decision); **hold a typed reference** (a `ScopedRef`- or
`PlaceholderRef`-shaped id that carries scope but no content, per
section 3); and **nothing** (PACK-10 has no path to the concept at
all, by design, not by omission).

| Concept                                            | Owning pack        | Owning service                                                                                     | What PACK-10 may do                                                                                                                                                    |
| -------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Organizations                                      | PACK-08            | `organization-service`                                                                             | Read via published interface; hold no local copy of state                                                                                                              |
| Organizational units                               | PACK-08            | `organization-service`                                                                             | Read via published interface                                                                                                                                           |
| Organizational scope                               | PACK-08            | `organization-service`                                                                             | Resolve and carry on every aggregate (HI-3, HI-4); never invent a scope locally                                                                                        |
| Institutional authority                            | PACK-08            | `organization-service`                                                                             | Resolve `OrganizationalAuthority`/`RoleAssignment` per action; never trust a role-name string (HI-53)                                                                  |
| Inheritance policy                                 | PACK-08            | `organization-service`                                                                             | Read via published interface for consolidation and cross-scope reads                                                                                                   |
| Legal cases                                        | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`LegalCaseRef`); open or cite, never decide procedure                                                                                          |
| Filings                                            | PACK-09            | `compliance-service`                                                                               | Nothing — `FilingRef` is PACK-11's to consume, not PACK-10's (references.py)                                                                                           |
| Procedural deadlines                               | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`DeadlineRef`, `DeadlineTriggerRef`)                                                                                                           |
| Official notices                                   | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`NoticeRef`); no legal effect from this alone                                                                                                  |
| Notice-effect decisions                            | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`NoticeEffectRef`); the only object that starts a deadline or gives legal effect                                                               |
| Legal holds                                        | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`HoldRef`); re-read immediately before disposal, never cache (HI-23)                                                                           |
| Record classes                                     | PACK-09            | `compliance-service`                                                                               | Hold a typed reference (`RecordClassRef`) for retention binding                                                                                                        |
| Retention                                          | PACK-09            | `compliance-service`                                                                               | Nothing beyond the `RecordClassRef` binding; retention semantics and supersession stay PACK-09's                                                                       |
| Processing registry                                | PACK-09            | `compliance-service`                                                                               | Nothing today — `ProcessingActivityRef`/`DPIARef` exist but no section-11 use case names them                                                                          |
| Data-subject requests                              | PACK-09            | `compliance-service`                                                                               | Nothing — no PACK-09 reference type for this exists; PACK-10 has no path to it                                                                                         |
| Documents, document bytes, version chains          | PACK-11            | none yet                                                                                           | Hold a typed placeholder (`FinanceEvidenceReference`) to metadata only; never bytes or content                                                                         |
| Signed originals                                   | PACK-11            | none yet                                                                                           | Nothing; fails closed with `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` until PACK-11 exists                                                                               |
| Evidence content and custody                       | PACK-11            | none yet                                                                                           | Nothing                                                                                                                                                                |
| Admissibility                                      | PACK-11            | none yet                                                                                           | Nothing                                                                                                                                                                |
| Publication renditions                             | PACK-11            | none yet                                                                                           | Cite a rendition identifier once PACK-11 exists; never generate one itself                                                                                             |
| Privileged administration, DLP                     | PACK-12            | none yet                                                                                           | Nothing                                                                                                                                                                |
| Production database, event bus, schema registry    | PACK-13            | none yet                                                                                           | Nothing; `finance-service` uses an in-memory reference adapter, same as every other repository service                                                                 |
| IAM/eID, credential issuance, qualified signatures | PACK-14            | `credential-service` (issuance only, PACK-02); real IAM/eID and qualified signatures not yet owned | Nothing                                                                                                                                                                |
| Voting, ballots, tally, delegation                 | PACK-15/16         | `voting-service`, `tally-service`, `delegation-service`                                            | Nothing; structurally isolated, no import in either direction (HI-37, HI-38)                                                                                           |
| Lobbying contacts, meetings, access, calendars     | PACK-35            | none yet                                                                                           | Nothing; PACK-10 implements no PACK-35 entity (HI-21). May expose a typed reference (`SponsorshipRef`, `ExternalFinancialBenefit`) for a future PACK-35 record to cite |
| Mandate-holder disclosure                          | PACK-35            | none yet                                                                                           | Nothing                                                                                                                                                                |
| Identity records                                   | identity-service   | `identity-service`                                                                                 | Nothing; PACK-10 owns neither `IdentityRecord` nor a reference into it (section 9.1)                                                                                   |
| Memberships                                        | membership-service | `membership-service`                                                                               | Hold a purpose-scoped dues reference issued by `membership-service`; resolvable only there                                                                             |
| Public transparency ledger and disclosure policy   | PACK-04            | `transparency-service`                                                                             | Reuse the disclosure-policy mechanism (`FinancePolicy(public_disclosure)`), never the ledger's storage                                                                 |
| AI processing                                      | PACK-06            | `ai-processing-service`                                                                            | Nothing                                                                                                                                                                |

PACK-10 itself owns 21 authoritative aggregates (section 8.1 of the
specification), grouped by module:

- **Ledger and provenance** (`ledger.py`, `imports.py`):
  `FinanceAccount`, `AccountingPeriod`, `JournalEntry`,
  `FinancialTransaction`, `ReconciliationRecord`, `ImportBatch`.
- **Contributions and external influence** (`contributions.py`):
  `Contribution`, `SponsorshipAgreement`, `ExternalFinancialBenefit`.
- **Expenses** (`expenses.py`): `ExpenseClaim`,
  `PaymentAuthorization`.
- **Positions** (`positions.py`): `FinancialAsset`,
  `FinancialObligation`.
- **Budgets** (`budgets.py`): `Budget`.
- **Reporting** (`reporting.py`): `ReportingObligation`,
  `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`.
- **Audit** (`audit_engagement.py`): `AuditEngagement`.
- **Policy and party identity** (`policy.py`, `partyregistry.py`):
  `FinancePolicy`, `FinancePartyHandle`.

## 2. Reads PACK-10 would make

| Read                                       | Target service         | Purpose                                                                                                   | Failure mode when unavailable                                                                                                                                                                   | Why it cannot be replaced by a local copy                                                                                                                                    |
| ------------------------------------------ | ---------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Resolve organizational scope and authority | `organization-service` | Determine `OrganizationalScope` and check `OrganizationalAuthority`/`RoleAssignment` before any command   | `ORGANIZATION_SCOPE_UNDETERMINED` (scope); `FINANCE_AUTHORITY_MISSING` (authority) — always fail closed                                                                                         | Authority is revocable and reassignable; a cached copy would authorize with stale privilege (HI-53)                                                                          |
| Resolve inheritance policy                 | `organization-service` | Resolve `OrganizationalInheritancePolicy` for consolidation and cross-scope reads                         | `ORGANIZATION_SCOPE_UNDETERMINED` — fails closed rather than assuming a hierarchy shape                                                                                                         | The policy is effective-dated and can change; a stale copy could consolidate against a superseded hierarchy (HI-54)                                                          |
| Check legal hold state                     | `compliance-service`   | Confirm no `LegalHold` blocks a disposal-relevant finance action, via `HoldRef`                           | `RECORD_UNDER_LEGAL_HOLD`; `LEGAL_HOLD_STATE_UNKNOWN` if indeterminate — never proceeds                                                                                                         | HI-23 requires re-reading, never caching; a hold placed after a cached read would be silently ignored                                                                        |
| Resolve record class / retention binding   | `compliance-service`   | Bind a finance record to its retention schedule via `RecordClassRef`                                      | `FINANCE_RETENTION_BINDING_MISSING`                                                                                                                                                             | Retention semantics and the supersession rule stay PACK-09's; a local copy could shorten an active obligation (HI-24)                                                        |
| Resolve deadline state                     | `compliance-service`   | Know a reporting, correction, return or response deadline via `DeadlineRef`/`DeadlineTriggerRef`          | No dedicated `FINANCE_*` code exists; the call fails closed on PACK-09's own not-found/undetermined response, and the deadline-dependent action is refused rather than assuming a default state | Only PACK-09's own governed trigger can start a deadline exactly once; a locally cached deadline could drift from the authoritative one                                      |
| Resolve notice-effect decision             | `compliance-service`   | Determine whether an authority response is legally effective, via `NoticeEffectRef`                       | `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE` — delivery or read telemetry is never substituted                                                                                          | Only a governed `NoticeEffectDecision` (ADR-043) is legal effect; a cached "delivered" flag would let telemetry masquerade as legal effect (HI-27, HI-28)                    |
| Resolve jurisdiction determination         | `compliance-service`   | Determine the competent authority for a finance case kind and scope, via `JurisdictionRef`                | No dedicated `FINANCE_*` code; falls back to PACK-09's own not-found/undetermined response and refuses the case-dependent action                                                                | Jurisdiction is itself a governed casework decision that can be re-determined; PACK-10 may not assume a static answer                                                        |
| Resolve a membership-issued dues reference | `membership-service`   | Accept a purpose-scoped dues reference for membership-contribution aggregation, without a `membership_id` | Resolution stays in `membership-service`; PACK-10 has no fallback, so unavailability simply blocks the dues-dependent action                                                                    | Only `membership-service` may resolve the handle; a local resolution would recreate the platform-wide identifier PACK-10 is structurally forbidden from having (HI-1, HI-48) |

Two rules bind every row above, restated because an implementation
could accidentally cross either one while wiring a read:

- **No read gives PACK-10 write access anywhere.** Every row above is
  a read of another service's published interface or a typed
  reference; none of them returns a capability to mutate the target
  service's state. Consolidation, the closest case, still only ever
  writes PACK-10's own `ConsolidationRecord` in PACK-10's own scope
  (HI-39, section 10 of the specification).
- **No read touches another service's storage** (canon INV-03,
  HI-47). `finance-service` imports only `epd2_core` and
  `epd2_audit_core`; every fact in the table above arrives through a
  published `application`-layer interface call or a typed reference,
  never a store or domain import from `organization-service`,
  `compliance-service`, `membership-service`, `identity-service`, or
  any other service.

## 3. References

### 3.1 References PACK-10 consumes

PACK-10 consumes PACK-09 exclusively through the reference types
PACK-09's own `references.py` exports, matching the table
`PACK-10-SPECIFICATION.md` section 11 and ADR-049 both already fix:

| PACK-09 reference type | Used for                                                                                 | Must never be inferred from holding it                                                                                                 |
| ---------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `LegalCaseRef`         | Opening or citing a case about a finance violation, dispute or correction                | Case admissibility, lifecycle stage or outcome — the case's own lifecycle stays PACK-09's                                              |
| `DeadlineRef`          | A procedural deadline for reporting, correction, return or response                      | That the deadline has started — only a `DeadlineTriggerRef` records that fact                                                          |
| `DeadlineTriggerRef`   | The recorded fact that one specific governed trigger started that deadline, exactly once | That the trigger can be reused to start a second deadline, or substituted for the deadline itself                                      |
| `NoticeRef`            | A notice document-shape from or to an authority, before legal effect                     | Legal effect — a notice is not yet an effect until a `NoticeEffectRef` exists                                                          |
| `NoticeEffectRef`      | The governed decision that gives a notice legal effect (ADR-043)                         | Legal effect from delivery or read telemetry — only this reference, backed by a governed `NoticeEffectDecision`, counts (HI-27, HI-28) |
| `HoldRef`              | A legal hold freezing finance records                                                    | A stable answer — hold state is re-read immediately before disposal, never cached (HI-23)                                              |
| `RecordClassRef`       | Retention-class binding for a finance record                                             | That rebinding a class can shorten an already-active retention obligation                                                              |
| `JurisdictionRef`      | The competent-authority determination for a finance case kind and scope                  | A permanent answer — jurisdiction is itself a governed, re-determinable casework decision                                              |
| `CasePartyRef`         | A party to a finance-related case                                                        | A person, member or account — it is a per-case handle, resolvable to nobody, by PACK-10 or anyone else (HI-1)                          |

PACK-09's `references.py` also exports `FilingRef` and
`ProcessingActivityRef`. Neither is a PACK-10 consumption today:
`FilingRef` is documented in PACK-09's own module as consumed by
PACK-11, not PACK-10, and `PACK-10-SPECIFICATION.md` section 11's
table does not name it; `ProcessingActivityRef` (and `DPIARef`,
`ProcessingActivationDecisionRef`) exist for the processing registry
but no PACK-10 use case in the specification names them either. Both
remain available in principle — a future finance processing activity
could register through `ProcessingActivityRef` — but neither is part
of the consumed set this round, and this document does not expand
that set on its own authority.

### 3.2 References PACK-10 would export, and the `FinanceEvidenceRef` question

PACK-10 would export its own `ScopedRef`-shaped reference types,
mirroring PACK-09's shape and its load-bearing reasons — a reference
carries its scope, carries no content, and is never a person:

- `FinanceRecordRef` — a general pointer into a PACK-10 finance
  record, for consumers that do not need a more specific type.
- `FinanceReportRef` — points at a `FinanceReport`.
- `FinanceReportVersionRef` — points at one immutable
  `FinanceReportVersion` in a report's append-only chain.
- `ContributionRef` — points at a `Contribution` (the donation/dues
  concept; deliberately namespaced away from PACK-03's unrelated
  deliberation `Contribution`, per the specification's own
  reason-code collision analysis, section 15.3).
- `SponsorshipRef` — points at a `SponsorshipAgreement`.
- `FinanceAuditEngagementRef` — points at an `AuditEngagement`.
- `FinancePartyHandleRef` — carries a handle id and purpose;
  resolvable by nobody outside `partyregistry.py` (section 5 of this
  document, and section 6 below).

**The `FinanceEvidenceRef` question.** PACK-09 already exports
`FinanceEvidenceRef`, a `PlaceholderRef` subclass with
`owner = PlaceholderOwner.PACK_10_FINANCE`, so a PACK-09 case, filing,
hearing or notice can point at finance material without PACK-09
owning it. Both the specification (section 11.1) and ADR-049 reach
the same disposition: **it remains sufficient and needs no
replacement**, with one documentation-level semantic correction —
the name says "evidence", but the object it points at is a PACK-10
_finance record_ (a transaction, contribution, sponsorship agreement,
report version or snapshot), not evidence content, which stays
PACK-11's (HI-22). PACK-10's own `references.py`, once implemented,
and any PACK-11 integration ADR must both say this, so no reader
concludes that holding a `FinanceEvidenceRef` means holding evidence.

**The parseable `external_reference` form.** PACK-10 would mint the
opaque `external_reference` string on `FinanceEvidenceRef` in a
documented, parseable, scoped form from day one — not an arbitrary
opaque string. The exact grammar is an implementation-round decision,
not fixed here; the requirement is only that it be stable and
parseable, encoding the reference kind, the organizational scope and
the record id in a way a later typed alias could parse without
breaking any reference already minted.

**OD-15, not implemented here.** PACK-09 could later accept a typed
`FinanceRecordRef` in place of the string `external_reference`. That
is a change to PACK-09's own module, and therefore a PACK-09-side
ADR in a separate round, with its own review — recorded as **OD-15**,
specified but not required, and not implemented by this document, the
specification, or ADR-049.

## 4. PACK-11 integration requirements

PACK-10 defines exactly one placeholder shape for material PACK-11
will own: `FinanceEvidenceReference`, mirroring PACK-09's
`PlaceholderRef` precedent (`owner = PACK_11_DOCUMENTS`, an open
`kind` string that PACK-11 — not PACK-10 — defines the taxonomy for,
an opaque `external_reference`, and organizational scope).

It points at eleven document kinds: invoices, receipts, contracts,
bank statements, valuation reports, donation declarations,
sponsorship agreement documents, audit working papers, signed
reports, submission receipts and publication renditions.

PACK-10 stores metadata and scoped references only: which kind of
document is expected, whether one is present, which finance record it
belongs to, and when the reference was recorded. PACK-10 never stores
document bytes, document content, signatures, cryptographic chains or
evidence custody (HI-22).

**Why a reference can never be read as authentic, signed, admitted,
authoritative, legally valid or publishable.** The prevention is
structural, not conventional: `FinanceEvidenceReference` has no
`is_authentic`, `is_signed`, `is_admitted`, `is_valid` or
`is_publishable` field. There is nothing to read such a fact off,
regardless of how careful or careless the calling code is. Wherever a
finance action would need one of those assertions, it fails closed
instead of assuming one — `FINANCE_EVIDENCE_REFERENCE_MISSING` when
no reference exists at all, and `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`
when a reference exists but the governed determination it would
require does not.

Four future PACK-11 interface requirements, stated as requirements
PACK-10 will consume rather than a design PACK-10 imposes on PACK-11:

1. resolve a reference to a document's existence and kind within an
   organizational scope;
2. report a signature or signed-original status as a governed
   determination, never an inferred one;
3. report an admissibility determination;
4. produce a publication rendition identifier that a public finance
   view can cite without exposing document content.

Until all four exist, PACK-10 records the reference and the absence
of the assertion — it does not simulate any of the four with a local
heuristic.

The eleven document kinds map onto PACK-10's own aggregates rather
than existing independently of them: an invoice or receipt evidences
an `ExpenseClaim` or `FinancialTransaction`; a contract or bank
statement evidences a `FinanceAccount` reconciliation; a valuation
report evidences an `InKindValuation`; a donation declaration or
sponsorship agreement document evidences a `Contribution` or
`SponsorshipAgreement`; audit working papers evidence an
`AuditEngagement`; and signed reports, submission receipts and
publication renditions evidence the `FinanceReportVersion` lifecycle.
None of these mappings gives PACK-10 a second copy of the document —
only the finance record the document is expected to support.

## 5. PACK-35 integration points

The PACK-10/PACK-35 division is decidable, not a judgment call per
instance: a record belongs to PACK-10 when its subject is a
**measurable financial value or a financially valued benefit**
attributable to a party organization; it belongs to PACK-35 when its
subject is a **contact, meeting, access or influence relationship**
with no financial value recorded. The test applies to the record's
subject, not to its origin.

PACK-10 exposes typed integration points for PACK-35 to consume once
it exists — a `SponsorshipRef` or an `ExternalFinancialBenefit`
reference that a future PACK-35 meeting or contact record may cite —
and implements no PACK-35 entity itself: no meeting, contact,
calendar or access entity exists anywhere in `finance-service` (HI-21,
section 4.5 of the specification). PACK-10 does not import, call or
depend on PACK-35, since PACK-35 does not exist yet; once PACK-35 is
specified, the dependency direction runs PACK-35 → PACK-10, mirroring
the general rule that a newer pack may read an older one's published
references but not vice versa.

**Worked example.** A meeting produces a sponsorship. The meeting
itself, its participants, its calendar entry and its non-financial
purpose are PACK-35's future `LobbyingMeeting`-shaped record; the
resulting agreement, its value and its counter-performance are
PACK-10's `SponsorshipAgreement`. This is two records, one typed
reference, neither owning the other — PACK-10 does not gain a meeting
entity by recording a sponsorship, and PACK-35 does not gain a
valuation field by recording a meeting.

**OD-19.** Where the financial/non-financial division is legally
uncertain — a subsidized venue whose market-value gap is disputed, or
an access arrangement whose benefit is real but not yet valued — the
uncertainty is recorded as **OD-19**, not silently resolved. A record
in that state stays wherever it was first created until OD-19 is
resolved by the project owner; neither this document nor ADR-049
picks a default owner for the uncertain case.

## 6. Forbidden edges

Every edge below must never exist in a PACK-10 implementation. Each
one is, or would be, proven by a structural test named in
`PACK-10-SPECIFICATION.md` section 6 — an import-graph check, a
schema check, or an absence-of-field check — not by code review
discipline alone; the invariant number in parentheses is where that
test is planned.

- **Finance → identity payload.** No name, address, date of birth,
  national identifier, tax identifier, bank detail, document image,
  email, phone number or credential value in any finance record,
  event or view (HI-2).

- **Finance → membership identifier.** No `membership_id` field
  anywhere in `finance-service`; only a purpose-scoped dues reference
  issued and resolved by `membership-service` (HI-1, HI-48).

- **Finance → vote/ballot/tally/delegation/credential.** No import of
  voting, tally, delegation, credential or eligibility modules; no
  vote-shaped field or schema property (HI-37, HI-38).

- **Finance → another service's storage.** No import of another
  service's `storage.py` or domain layer; every cross-service fact
  arrives through a published interface (HI-47, canon INV-03).

- **Finance → document bytes or signatures.** No document content,
  hash chain or signature field anywhere in `finance-service` (HI-22).

- **Finance → PACK-35 meeting entity.** No meeting, contact, calendar
  or access entity anywhere in `finance-service` (HI-21).

- **Budget module → ledger store write.** No write path from
  `budgets.py` to a ledger store; `actual_amount` is always a derived
  read model, never a stored budget field (HI-12).

- **Projections → authoritative write.** `projections.py` performs no
  authoritative write; every public or internal view is read-only and
  carries its own source version (HI-35).

- **Audit module → write into an audited aggregate.** `audit_engagement.py`
  never writes into the aggregate it audits, preserving finance-auditor
  independence (HI-30).

- **Any module except `partyregistry.py` → handle resolution.** No
  module other than `partyregistry.py` may resolve a
  `FinancePartyHandle` to anything beyond the handle itself
  (`FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`, HI-1).

- **Telemetry field → report state transition.** No delivery-, read-
  or acknowledgement-telemetry field is an input to any
  `FinanceReport` or `FinanceReportVersion` state transition (HI-28).

- **Role-name string → authority.** No finance action is authorized
  by comparing a `role_code` string; authority is always resolved to
  a currently active, scope-matching `OrganizationalAuthority` or
  `RoleAssignment` record (HI-53).

## 7. What a later pack may rely on

Once PACK-10 is implemented, a later pack (PACK-11, PACK-35, or any
other consumer) may rely on the following as stable, and on nothing
else:

- **Reference shapes.** Every `ScopedRef`-shaped type PACK-10 exports
  (`FinanceRecordRef`, `FinanceReportRef`, `FinanceReportVersionRef`,
  `ContributionRef`, `SponsorshipRef`, `FinanceAuditEngagementRef`,
  `FinancePartyHandleRef`) and the `FinanceEvidenceReference`
  placeholder shape are additive-only: new fields are never required
  on an existing type, and an existing field is never removed or
  repurposed.

- **Event names.** Canonical event names PACK-10 registers are
  additive-only, following the same versioned-event discipline the
  rest of the repository already applies (canon section 21); a later
  round may add a new event, never redefine an existing one's
  meaning.

- **Reason codes.** Reason codes PACK-10 registers in
  `contracts/reason-codes/pack-10.yml` are additive-only, following
  ADR-004's model exactly as PACK-09's registry does; a code's
  meaning, once registered, is never silently changed underneath a
  consumer that already handles it.

Nothing else is a stability promise. In particular, internal module
boundaries (`ledger.py`, `budgets.py`, `projections.py` and the rest),
aggregate internals, storage adapters, and anything not named above
may change between implementation rounds without notice to a
consuming pack — a later pack must depend only on the reference
shapes, event names and reason codes this section names, exactly as
PACK-10 itself depends only on PACK-08's and PACK-09's published
interfaces rather than their internals.

This document itself follows the same discipline it describes: it is
additive-only alongside `PACK-10-SPECIFICATION.md` and ADR-049, not a
replacement for either. Where a later round finds that this document
and the specification disagree, the specification and ADR-049 govern,
and this document is corrected to match — never the reverse.
