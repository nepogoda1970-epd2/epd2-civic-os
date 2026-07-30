# PACK-13 — Data Ownership Matrix

Specification-only. No code. Not implemented.

Companion to `PACK-13-SPECIFICATION.md` §4, §5, §7 and
`ADR-070-DOMAIN-DATA-OWNERSHIP.md`.

---

## 1. What ownership means here

An owner is a **domain**, never a platform team and never a database role.
The owner is answerable for the record's invariants, its migrations, its
retention semantics and its authorization. Ownership is not "the team that
wrote the table"; it is "the context whose rules the record obeys".

Four consequences, all normative:

1. **Only the owner writes.** No other service issues `INSERT`, `UPDATE` or
   `DELETE` against an owned table, under any circumstance including
   migration and incident response. This holds for `audit-core` too:
   "every domain appends to audit" describes **submission** through a
   governed ingestion contract, not direct persistence — see §3.3, which
   resolves the apparent contradiction rather than carving an exception
   out of this rule.
2. **Direct reads by others are not an integration pattern.** A read that
   works is not thereby permitted.
3. **Others hold typed references, not access.** A `DocumentRef` is a
   pointer plus a promise about its shape — not a licence to open the row.
4. **Emergency access is not integration.** A break-glass session that
   reads another domain's table is a governed incident with evidence, not
   a supported pathway that happens to require paperwork.

## 2. The four admissible integration mechanisms

| #   | Mechanism                  | What it is                                                                                             |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1   | **Owned API**              | The owner exposes a versioned contract; callers use it                                                 |
| 2   | **Versioned events**       | The owner publishes; consumers subscribe and build their own state                                     |
| 3   | **Governed projection**    | An explicitly approved read model, carrying the narrowest authorization of its inputs (`P13-PROJ-005`) |
| 4   | **Approved read contract** | A narrow, named, versioned read the owner has agreed to and the registry records                       |

Anything else — a shared table, a cross-schema join, a replica query, a
backup extract, an analytics warehouse copy — is **not** an integration
mechanism. Each of those is a way the boundary is lost while every code
review passes.

---

## 3. Ownership matrix

`W` = owns and writes. `E` = publishes versioned events others may consume.
`R` = may read **only** through mechanisms 1–4. `—` = no relationship.
**No cell in this matrix authorises a direct cross-schema read or write.**

### 3.1 Existing implemented owners

These bounded contexts exist in the PACK-12 FINAL PASS baseline as
**reference implementations**, and their data-plane ownership is settled by
PACK-13.

| Data area                                         | Owning domain                                              | Schema isolation                        | Scope column      | Record class (PACK-09) | Immutable history                        | May be consumed by                                                                            |
| ------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------- | ----------------- | ---------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------- |
| Membership                                        | `membership-service`                                       | own schema                              | required          | yes                    | no                                       | organization, finance, governance (E)                                                         |
| Organization, scope, authority                    | `organization-service`                                     | own schema                              | required          | yes                    | authority assignments effective-dated    | **all** domains (E) — scope is universal input                                                |
| Institutional authority assignments               | `organization-service`                                     | own schema                              | required          | yes                    | effective-dated, superseding             | privileged-access, finance, governance (E)                                                    |
| Audit events                                      | `audit-core`                                               | own schema                              | required          | yes                    | **hash-chained, no UPDATE/DELETE**       | all domains **submit** through the governed audit-ingestion contract (§3.3); read is governed |
| Records governance, retention, holds              | `compliance-service`                                       | own schema                              | required          | yes                    | destruction evidence immutable           | all domains (R via API — they _ask_, never decide)                                            |
| Governed documents and evidence                   | `document-service`                                         | own schema                              | required          | yes                    | **hash-linked versions, sealed bundles** | all domains via `DocumentRef`/`EvidenceBundleRef` (R)                                         |
| Party finance                                     | `finance-service`                                          | own schema                              | required          | yes                    | postings immutable                       | governance, transparency (E)                                                                  |
| Privileged access, sessions, query audit, exports | `privileged-access-service`                                | own schema                              | required          | yes                    | **sealed sessions hash-chained**         | none directly; oversight reads are governed                                                   |
| Export requests and artifacts                     | `privileged-access-service`                                | own schema                              | required          | yes                    | manifests immutable                      | none directly (`P13-EXPORT-004`)                                                              |
| Initiatives, deliberation, moderation             | respective services                                        | own schema                              | required          | yes                    | decisions immutable                      | transparency (E)                                                                              |
| Delegation                                        | `delegation-service`                                       | own schema                              | required          | yes                    | no                                       | governance (E)                                                                                |
| Governance decisions                              | `governance-service`                                       | own schema                              | required          | yes                    | decisions immutable                      | transparency (E)                                                                              |
| Transparency publication                          | `transparency-service`                                     | own schema                              | required          | yes                    | publications immutable                   | public projections                                                                            |
| AI processing records                             | `ai-processing-service`                                    | own schema                              | required          | yes                    | records immutable                        | governance (E)                                                                                |
| Search index and projections                      | search projection owner                                    | **projection store, not authoritative** | required          | derived                | no                                       | PACK-12 search path only (`P13-SRCH-006`)                                                     |
| Schema registry                                   | PACK-13 registry context                                   | own schema                              | n/a (system-wide) | yes                    | **schema versions immutable**            | all domains (R via API)                                                                       |
| Outbox                                            | per owning domain, **co-located with the domain's schema** | with the domain                         | required          | yes                    | immutable but for delivery metadata      | dispatcher only                                                                               |
| Migration records                                 | PACK-13 migration context                                  | own schema                              | n/a               | yes                    | **immutable once applied**               | operators (R, governed)                                                                       |

### 3.2 Reserved future ownership boundaries

The areas below are **conceptual data-plane boundaries**, not existing
deployable services and not settled ownership. Some have reference-
implementation services in the baseline (`account-service`,
`identity-service`, `eligibility-service`, `credential-service`,
`voting-service`, `tally-service`, all from PACK-02 and PACK-03). **The
existence of a reference implementation does not settle production
data-plane ownership**, and PACK-13 does not settle it either.

| Reserved boundary                                                                    | Ownership                       | Schema                     | PACK-13 constraints that already bind it                                                                                                                               |
| ------------------------------------------------------------------------------------ | ------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **future identity domain — owner to be established by PACK-14**                      | to be established by PACK-14    | **not created by PACK-13** | no global user ID; separate account/person/membership identifiers; scoped actor references; no identity correlation via convenience keys (`P13-ID-001`..`007`)         |
| **future eligibility domain — owner to be established by PACK-15**                   | to be established by PACK-15    | **not created by PACK-13** | organizational scope mandatory; **never joined to ballot material** (`P13-VOTE-003`)                                                                                   |
| **future credential domain — owner to be established by PACK-15**                    | to be established by PACK-15    | **not created by PACK-13** | separation from eligibility is structural (`FIR-INV-004`); credentials outside the general plane (`P13-ID-007`)                                                        |
| **future voting domain — owner to be established by PACK-15/16**                     | to be established by PACK-15/16 | **not created by PACK-13** | ballot content and voting secrets never in the general plane; no identity-to-ballot join; no identity-linked ballot payload on the general bus (`P13-VOTE-001`..`008`) |
| **future tally/result-certification domain — owner to be established by PACK-15/16** | to be established by PACK-15/16 | **not created by PACK-13** | no intermediate tally in any general analytics projection; no partial-result publication (`P13-VOTE-004`, `P13-VOTE-005`)                                              |
| **future communications domain**                                                     | not yet established             | **not created by PACK-13** | scoped communication persona rather than a membership or account identifier                                                                                            |
| **future assemblies domain**                                                         | not yet established             | **not created by PACK-13** | organizational scope mandatory                                                                                                                                         |
| **future candidacy domain**                                                          | not yet established             | **not created by PACK-13** | organizational scope mandatory                                                                                                                                         |

`P13-OWN-009` A reserved boundary is a **conceptual boundary, not an
existing deployable service**.

`P13-OWN-010` **PACK-13 assigns no final service name** to any reserved
boundary. Names appearing in the baseline are reference-implementation
artifacts, not production topology decisions.

`P13-OWN-011` **PACK-13 creates no schema ownership on behalf of a future
PACK.** No table, column, foreign key or reserved namespace is created for
a reserved boundary (`P13-OWN-001`).

`P13-OWN-012` A future owner, once established, **must comply with the
PACK-13 data-plane contracts** — ownership rules, transaction boundaries,
concurrency, outbox, delivery semantics, schema registry, migration
discipline, projection governance and retention integration.

`P13-OWN-013` **Final topology and ownership for each reserved boundary are
approved by the corresponding PACK** (PACK-14 for identity; PACK-15 for
eligibility and credential; PACK-15/16 for voting and
tally/result-certification), not by PACK-13.

### 3.3 Audit ingestion — the one apparent exception, resolved

`P13-OWN-014` **All domains may submit typed audit records through the
governed audit-ingestion contract; only `audit-core` persists authoritative
audit records.**

This resolves what would otherwise be a contradiction between "only the
owner writes" and "every domain appends to audit". Both are true, because
they describe different things: every domain **submits**, and exactly one
domain **persists**.

Normatively:

- **No other domain performs a direct `INSERT`, `UPDATE` or `DELETE`** against
  `audit-core` tables or schema.
- Other domains submit a **typed audit record** through the governed
  audit-ingestion port/API, or through a versioned audit command or event.
- **`audit-core` alone owns persistence** of authoritative audit records.
- **Append-only describes ingestion semantics and authoritative storage** —
  a submitted record is added, never modified or removed.
- **Application credentials of other domains carry no write grant on the
  audit schema.** The boundary is a database grant, not a coding
  convention.
- **Bulk loading and emergency SQL are not ordinary integration paths.**
- **Privileged maintenance obeys PACK-12 and does not transfer ownership.**
  A break-glass session that touches audit storage is a governed incident
  with evidence; it does not make the acting domain an owner.

---

`P13-OWN-001` A future area marked "reserved, not created" gets **no
tables, no columns and no foreign keys** in this round. Reserving space in
a schema for a domain that does not exist is how a shared table is born.

## 4. Rules that fall out of the matrix

`P13-OWN-002` **The outbox lives with its domain**, not in a central
outbox schema. A central outbox is a shared mutable table that every
domain writes to — precisely `P13-DP-015`.

`P13-OWN-003` **`organization-service` is the one universal input** and it
is consumed by event and API, never by join. Every domain stores its own
`organization_id`; none reads the organization tables directly.

`P13-OWN-004` **The eligibility and credential boundaries share no key, no
schema and no join path.** `FIR-INV-004` is a database-level fact, not only
an application-level one. It binds the baseline reference implementations
(`eligibility-service`, `credential-service`) now, and it binds whatever
owners PACK-15 establishes for those reserved boundaries later
(`P13-OWN-012`).

`P13-OWN-005` **`compliance-service` is asked, never bypassed.** A domain
that needs to know whether a record may be deleted asks; it does not read
the hold table and decide for itself.

`P13-OWN-006` **`audit-core` is append-only, and submission is not
persistence.** Every domain may submit a typed audit record through the
governed ingestion contract; no domain — and no database role used by
another domain's application credentials — may write to, update or delete
from the audit schema directly (§3.3).

`P13-OWN-007` **Ballot content, voting secrets and voting credentials are
never present in the general data plane**, no general schema contains an
identity-to-ballot join, and the general event bus never carries an
identity-linked ballot payload.

These are **data-plane constraints**, and they are all PACK-13 fixes.
PACK-13 does **not** decide the voting domain's broker topics, whether its
broker deployment is separate or shared, its connection-pool topology, its
service names, its credential topology or its transport provider — those
belong to **PACK-15/16**, together with the obligation to demonstrate
isolation and unlinkability under their own threat model. Where that threat
model requires it, **separate infrastructure is the preferred reference
direction**; it is a direction, not a topology decision already taken
here.

## 5. Cross-domain references that are permitted

Enumerated, not general. Each is a **typed reference**: an identifier plus
the owning domain, carrying no access.

| Reference                                                     | Held by                           | Points at                 | Confers                                                 |
| ------------------------------------------------------------- | --------------------------------- | ------------------------- | ------------------------------------------------------- |
| `OrganizationalScopeRef`                                      | every domain                      | organization-service      | nothing; it is a scope value                            |
| `RecordClassRef`, `RetentionBindingRef`, `LegalHoldRef`       | domains with governed records     | compliance-service        | nothing; the decision stays with PACK-09                |
| `DocumentRef`, `EvidenceBundleRef`, `PublicationRenditionRef` | domains citing documents          | document-service          | nothing; opening requires PACK-11 authority             |
| `AuditEventRef`                                               | domains citing an audited act     | audit-core                | nothing                                                 |
| `OrganizationalAuthorityRef`                                  | domains recording who acted       | organization-service      | nothing; resolution goes through the authorization port |
| `PrivilegedGrantRef`, `PrivilegedSessionRef`                  | domains recording privileged acts | privileged-access-service | nothing                                                 |

`P13-OWN-008` This list is **closed**. A new cross-domain reference type
requires an ADR naming both domains and stating what it does not confer.
