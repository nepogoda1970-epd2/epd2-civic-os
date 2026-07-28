# Finance Service — the party-finance bounded context

Status: implemented for CLAUDE-PACK-10. This document describes
`services/finance-service`, the sole authoritative owner of the
party-finance bounded context canon `0.8.0` section 19f defines, and the
boundaries it holds against six neighbouring packs. The decomposition
decision is `docs/adr/ADR-048-pack-10-finance-service-decomposition.md`;
the cross-pack boundary analysis is
`docs/packs/PACK-10-CROSS-PACK-BOUNDARIES.md`; what the round shipped
and what it deferred is `docs/packs/PACK-10-IMPLEMENTATION.md`.

## 1. What the service owns

Canon 19f.1 lists twenty-one authoritative finance aggregates, all owned
by this service. Sixteen of those exist here as aggregates, alongside
two records canon 19f.1 does not name at all — `Reimbursement` and
`GovernedTransfer`, both introduced by the specification:

- the chart of accounts and the posting lock — `FinanceAccount`,
  `AccountingPeriod`;
- the authoritative accounting register — `JournalEntry` with its
  ordered `PostingLine` tuple;
- the authoritative record of business fact and provenance —
  `FinancialTransaction`, and `GovernedTransfer` for movement between
  units;
- income and external influence with a financial value —
  `FinanceContribution`, `SponsorshipAgreement`,
  `ExternalFinancialBenefit`;
- spending with separated authorisation and execution — `ExpenseClaim`,
  `PaymentAuthorization`, `Reimbursement`;
- positions — `FinancialAsset`, `FinancialObligation`;
- reporting — `ReportingObligation`, `ReportingPerimeterDefinition`,
  `ReportSnapshot`, `FinanceReportVersion`;
- the independent audit — `AuditEngagement` with its append-only
  `AuditFinding` tuple and its create-once `AuditConclusion`;
- the purpose-scoped party reference — `FinancePartyHandle`.

Five of the canon's twenty-one have no aggregate this round: `Budget`,
`ReconciliationRecord`, `FinancePolicy`, `ImportBatch` (present as
`storage.ImportBatchRecord`, an infrastructure record of an ingestion
act rather than an aggregate) and `FinanceReport` as an identity
separate from its versions — the service models
`FinanceReportVersion` with a `report_id`, and no aggregate owns the
series. Each is listed with what stands in its place in
`PACK-10-IMPLEMENTATION.md` section 6.

Two separations run through the ownership and are the point of ADR-049.
`JournalEntry` is the authoritative record of monetary effect;
`FinancialTransaction` is the authoritative record of the business fact
and its provenance. Neither is a cache of the other. A transaction whose
status asserts monetary effect without a posted entry cannot be
constructed — the constructor refuses it as the incomplete state canon
19f.6 says must fail closed. Balances, trial balances and period totals
are derived views in `projections.py` and are authoritative for nothing.

## 2. Module dependency order

Twelve modules. Each imports only from those above it, and the order is
a real acyclic graph rather than a documented intention.

```text
exceptions      no domain knowledge; one class per reason code
domain          value objects, identity minimisation, Money, pure rules
authorization   roles, incompatibility matrix, action requirements, port
ledger          accounts, periods, balanced postings, corrections
records         contributions, sponsorship, benefit, expenses, positions
reporting       obligation, perimeter, snapshot, report lifecycle, audit
events          72 canonical builders, full-state audit payloads
references      the typed pointers in and out, and the refusals
storage         ports and in-memory adapters; no delete method exists
projections     derived, versioned, non-authoritative read models
application     commands and queries: guard, idempotency, audit, events
```

`references` sits below `records` because it re-exports
`records.assert_not_lobbying_subject` rather than reimplementing it —
one implementation of the PACK-35 refusal, not two that can drift.

`ledger`, `records`, `reporting` and `authorization` are pure: no I/O,
no clock, no storage, no cross-service import. Every identifier, every
timestamp and every sequence number is passed in by `application`. That
is what makes each invariant testable without constructing a store, the
same property PACK-09 achieved with
`domain.assert_decision_maker_eligible`.

## 3. Boundaries, and how each is held

`finance-service` declares exactly two dependencies in its
`pyproject.toml`: `epd2-core` and `epd2-audit-core`. It imports no other
service package, which
`test_the_finance_package_imports_no_other_service_package` checks
structurally rather than by grep. Every fact owned by another context
arrives as a typed opaque pointer in `references.py`, carrying an
identifier and the organizational scope and no content at all.

| Pack    | What it owns that finance needs                                      | How the boundary is held                                                                                                     |
| ------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| PACK-08 | Organizational scope, authority assignments, effective dating        | `OrganizationalScopeReference` outward, `OrganizationalScopeRef` inward, and `authorization.AuthorizationPort` for authority |
| PACK-09 | Legal case, legal hold, record class, notice-effect decision         | `LegalCaseReference`, `LegalHoldReference`, `RetentionClassReference`, `NoticeEffectReference`                               |
| PACK-11 | Document identity, version, bytes, signature, custody, admissibility | `DocumentReference` plus `assert_no_document_content`                                                                        |
| PACK-12 | Privileged access, emergency access, DLP and export control          | No reference type. See below                                                                                                 |
| PACK-13 | Production persistence, migrations, the production event plane       | No reference type. See below                                                                                                 |
| PACK-35 | Lobbying contacts, meetings, access, non-financial influence         | `LobbyingContactReference` plus `records.assert_not_lobbying_subject`                                                        |

Four of these are worth reading in full.

PACK-08. Finance neither stores an authority assignment nor mints one.
`AuthorizationPort` is a `Protocol` with two questions — does this
presented authority resolve to an active, effective-dated,
scope-matching assignment, and which finance roles does this actor
actually hold in this scope — and finance believes the answers. It never
interprets the organizational hierarchy: `_partition_by_scope` and
`OrganizationalScopeRef.assert_matches` compare `organization_id` alone,
so a parent scope is not this scope, and a consolidating scope reads a
lower one but never acts in it (canon 19f.19, `ФИН-37`).

PACK-09. `LegalHoldReference` deliberately carries no `is_active` and no
`held_until`. Hold state is re-read immediately before every
disposal-relevant action and never cached; a boolean on the reference
would be a cache, and a stale one would authorise exactly the
destruction `ФИН-22` forbids. `observed_at` records when the pointer was
taken, which is a different fact and is labelled as one. Finance
re-declares PACK-09's reference shapes as finance-side mirrors rather
than importing `epd2_compliance_service.references`, because importing
would make a cross-service code edge out of what canon 19f.22 requires
to be a typed reference through a published interface (`ФИН-44`).

PACK-11. `DocumentReference` carries an identity, an open `kind` string
and an opaque `version_reference`, and nothing else. No reference type
in the module has an `is_authentic`, `is_signed`, `is_admitted`,
`is_valid` or `is_publishable` field. `assert_no_document_content` is
the backstop for payloads assembled elsewhere: it refuses both document
content keys and assertion keys, both with
`FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`, since canon section 24
registers no separate code for the first and inventing one would put an
unregistered string on a governed refusal. The function sees key names
and not values — a scanned invoice hidden in a field called
`note_reference` passes it, and the real defence is that no type in the
module has a field for such a value.

PACK-35. Canon 19f.9 draws the line at whether a financial value is
recorded: finance owns financially measurable influence and its
disclosure, PACK-35 owns the contact, the meeting, the access and the
relationship. A meeting that produced a sponsorship is two records
linked by one typed reference, and neither owns the other.
`assert_not_lobbying_subject` refuses a PACK-35 subject kind being
recorded as a finance record; `LobbyingContactReference.contact_kind` is
deliberately not validated against the same set, because there the
PACK-35 kind labels somebody else's record and validating it would
refuse the integration canon 19f.9 requires.

PACK-12 and PACK-13 have no reference type, and the absence is
deliberate rather than an omission. PACK-12 appears in this service as
an explicit non-path: `authorization.NO_BREAK_GLASS_NOTE` records that
no feature flag, environment switch, deployment mode, privileged-access
grant or emergency path may bypass any check in that module, and the
`AuthorizationPort` docstring states that an adapter returning `True`
because a caller held an emergency grant would be implementing the
bypass `ФИН-42` forbids. A PACK-12 grant can make a caller able to reach
a finance command, never able to pass one. PACK-12's other role, export
and DLP control, is served by `projections.py` being the single
emission chokepoint. PACK-13 appears as the absence of any durable
adapter: every store in `storage.py` is in-memory, none is
concurrency-safe, and several adapters say in their own docstrings which
guarantee a durable backend would have to supply instead.

There is one forbidden direction with no reference type at all. No
entity, field, import or scope path in this service reaches `Ballot`,
`VoteEnvelope`, `Tally`, `Delegation`, `DelegationSnapshot` or
`ParticipationCredential`. `references.FORBIDDEN_INBOUND_REFERENCE_KINDS`
refuses the kind before any identifier is stored, which is the only
point at which the refusal is cheap: once a ballot reference is inside a
governed append-only record it cannot be deleted (`ФИН-05`), only
regretted. The check is an exact match on a normalised token, not a
substring scan, so `ballot_id_for_audit` passes it — the key-level
defence for that is `domain.reject_identity_payload_keys`, and the
structural fact behind both is that no type in the package has a field
for any of these (`ФИН-36`).

## 4. The identity-minimisation model

There is no `UserId`, `GlobalUserId`, `PersonId`, member identifier,
voter identifier, credential identifier or ballot identifier anywhere in
this package (`ФИН-01`). Party finance nevertheless has a legally
unavoidable identification requirement — a contributor above a
threshold, a claimant being reimbursed, an obligation counterparty and a
report signatory all have to be identifiable to the finance function and
to an auditor. The model that satisfies both is one value object.

`domain.FinancePartyHandle` is an opaque service-minted UUID bound to
exactly one `HandlePurpose` and exactly one perimeter. It is derived
from nothing: not from a name, an account, a membership, a credential or
another handle. `assert_usable_for` refuses a handle presented for
another purpose or outside its perimeter, so two handles for the same
legal person in two purposes are unequal by construction and nothing in
this service can join them. `as_reference()` produces the opaque
`fph:<purpose>:<uuid>` string, and that string is the only shape a party
may take in a record, an event payload or a projection —
`_require_party_handle_reference` in `ledger.py` and `records.py`
refuses anything else presented as a party.

`domain.PROHIBITED_IDENTITY_KEYS` is a frozen set of thirty-six key
names that may never appear in a finance record, a finance event payload
or a projection: person and account identifiers, voting identifiers, contact
details, names, addresses, dates of birth, national and tax identifiers,
bank details, card numbers and secrets. It is deliberately about shapes
of identity rather than one service's naming, so any of them arriving at
a finance boundary is a forbidden linkage whoever produced it.
`reject_identity_payload_keys` walks nested structures, because a
prohibited key one level down is the same leak as one at the top
(`ФИН-02`), and it runs over every assembled event payload and every
projection payload. The check is blunt on purpose — which is why
`FinanceAccount.account_id` serialises as `finance_account_id`
everywhere, since `account_id` means a user account in every other
context in this repository.

Four tests hold the model rather than describing it:
`test_no_dataclass_field_in_the_finance_package_is_a_prohibited_identity_key`
scans every dataclass in the package;
`test_no_module_names_a_prohibited_identity_key_in_its_executable_code`
scans the source, with
`test_the_permitted_register_is_the_one_place_those_strings_are_spelled`
as its carve-out and
`test_the_source_scan_would_notice_a_prohibited_key_if_one_were_added`
as its own negative control.

Pseudonymisation is not anonymity, and the code says so in
`FinancePartyHandle`'s own docstring. A handle is personal data. It is
re-identifiable by design, by an authorised resolver, through a
governed, reason-coded, audited act that emits
`finance_party_handle.resolved` without the resolved value. What the
handle buys is limited correlation and limited accidental exposure. It
does not remove the requirement for a legal basis, it does not make the
underlying data non-personal, and public disclosure still has to go
through redaction, aggregation and a publication policy (`ФИН-01`,
19f.15, 19f.21).

## 5. No claim of legal compliance or operational readiness

Canon `ФИН-43` states that no assertion of legal compliance, acceptance
by an authority, or operational readiness follows from section 19f. It
does not follow from this implementation either.

What this service provides is a governed workflow: separated
authorities, reason-coded refusals, an append-only audit trail with
canonical-JSON hashing, immutable posted entries, frozen snapshots and
derived non-authoritative public views. What it does not provide, and
does not claim, is a judgement about whether any accounting treatment,
valuation method, aggregation rule, disclosure threshold, minimum cell
size, retention schedule, report or publication satisfies the
Parteiengesetz, German statutory accounting rules, the GDPR, the BDSG or
any authority's requirements. Those remain human legal and accounting
judgements taken outside this system, and nothing in this service should
be read as having made one.
