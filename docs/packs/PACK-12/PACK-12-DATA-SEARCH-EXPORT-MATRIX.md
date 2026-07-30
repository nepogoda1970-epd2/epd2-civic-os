# PACK-12 — Data, Search and Export Matrix

Specification-only. No code. Not implemented.

> **Status note, updated by the PACK-12 FINAL PASS round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the _specification round_ that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification; the implementation reached **FINAL PASS** at repository
> version `0.12.0`.
>
> **PACK-12 is now FINAL PASS** at repository version `0.12.0`, verified
> by an external GitHub Actions run. **NOT PRODUCTION READY. NOT LEGALLY
> ACTIVATED.** See `docs/handover/PACK-12-FINAL-PASS-REPORT.md`.

Companion to `PACK-12-SPECIFICATION.md` sections 7–11.

---

## 1. Purpose and the authority of source classification

This document answers, per data class: may it be indexed, may it be
searched and by whom, may it be exported, and under what controls.

**The source classification is authoritative and PACK-12 does not
replace it.** An earlier draft collapsed everything into four levels
borrowed from PACK-09's `RecordSensitivity`; that was a simplification
that would have silently overwritten richer canonical values. The
correction is section 2, and it is normative.

`P12-CLS-001` The canonical or source classification of a record is
authoritative. PACK-12 MUST NOT change it, MUST NOT lower it, MUST NOT
override a domain-specific restriction, and MUST NOT substitute for an
authoritative record-class policy.

`P12-CLS-002` A **PACK-12 enforcement tier** is a derived policy
abstraction only. It exists so that indexing, search and export rules can
be expressed once rather than per domain. It carries no authority of its
own, and where it and the source classification disagree, the source
classification governs.

`P12-CLS-003` Where a domain imposes a stricter rule than the tier this
matrix assigns, the domain's rule governs. This matrix is a floor.

---

## 2. Canonical classification → PACK-12 enforcement tier

Normative mapping. Read left to right: the left column is authoritative,
everything to its right is derived policy.

| Canonical / source classification | PACK-12 enforcement tier | Indexing default                                | Search default                                              | Export default                                  | Required approvals                                       | Disclosure-control requirement                        |
| --------------------------------- | ------------------------ | ----------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------- |
| **Public / approved**             | `T0-open`                | General index                                   | General search                                              | Governed export                                 | Data owner                                               | None unless aggregated over persons                   |
| **Public authoritative**          | `T0-open-authoritative`  | General index                                   | General search                                              | Governed export, rendition-bound                | Data owner; publication authority for the rendition      | None; the authoritative surface owns its own controls |
| **Internal**                      | `T1-internal`            | Scoped index                                    | Scoped search                                               | Governed export                                 | Data owner + export approver                             | Assessment if aggregated                              |
| **Confidential / regulated**      | `T2-confidential`        | Scoped index, field-gated                       | Scoped search, purpose-bound                                | Governed export, DLP mandatory                  | Data owner + export approver + DLP officer               | Assessment mandatory                                  |
| **Confidential case metadata**    | `T2-case-metadata`       | Scoped index, metadata only; never case content | Scoped search, purpose-bound                                | Governed export of metadata only                | Data owner + export approver                             | Assessment mandatory; cohort rules apply              |
| **Derived decision**              | `T1-derived`             | Scoped index                                    | Scoped search; derivation never widens access to its inputs | Governed export of the decision, not its inputs | Data owner                                               | Assessment if the decision reveals a small cohort     |
| **Highly confidential**           | `T3-restricted`          | **Excluded by default**                         | Domain surface only, purpose-bound                          | Governed export, manual approval                | Data owner + export approver + DLP + disclosure reviewer | Assessment mandatory; independent review              |
| **Absolutely excluded** (§4.1)    | `T4-prohibited`          | **Never**                                       | **Never**                                                   | **Never**                                       | n/a — no approval path exists                            | n/a                                                   |

`P12-CLS-004` `T4-prohibited` is not a tier an approval can lift. There
is no approver, no purpose, no emergency condition and no configuration
that moves a record out of it.

`P12-CLS-005` Where a source classification not listed above is
encountered, the enforcement tier MUST default to `T3-restricted` and the
act MUST be refused pending an explicit mapping decision. An unmapped
classification fails closed; it does not fall through to `T1-internal`.

### 2.1 Relationship to PACK-09 and PACK-11 sensitivity values

PACK-09's `RecordSensitivity` and PACK-11's `SensitivityClass`
(`public`, `internal`, `confidential`, `restricted`) remain those packs'
own authoritative values for their own records. They are **inputs** to
the tier mapping, not a replacement for it, and PACK-12 adds no fifth
level to either.

---

## 3. Data class matrix

Index: `Y` general, `S` scoped only, `N` never. Export: `G` governed
export only, `N` never.

| Data class                                   | Source classification      | Tier                    | Index       | Search mode                   | Export      | Mandatory controls                                                                       |
| -------------------------------------------- | -------------------------- | ----------------------- | ----------- | ----------------------------- | ----------- | ---------------------------------------------------------------------------------------- |
| Public transparency documents (PACK-11)      | Public authoritative       | `T0-open-authoritative` | Y           | general                       | G           | Rendition-bound; manifest; expiry                                                        |
| Published finance projections (PACK-10)      | Public authoritative       | `T0-open-authoritative` | Y           | general                       | G           | Manifest; expiry; disclosure assessment                                                  |
| Organizational structure (PACK-08)           | Public / approved          | `T0-open`               | Y           | general, scoped               | G           | Org scope; manifest                                                                      |
| Governed documents, internal (PACK-11)       | Internal                   | `T1-internal`           | S           | scoped                        | G           | Org scope; field policy; DLP assessment                                                  |
| Governance decisions (PACK-05)               | Derived decision           | `T1-derived`            | S           | scoped                        | G           | Decision exportable; its inputs are not                                                  |
| Membership records (PACK-07)                 | Confidential / regulated   | `T2-confidential`       | S           | scoped                        | G           | Data owner; DLP; pseudonymization; cohort threshold                                      |
| Finance transaction register (PACK-10)       | Confidential / regulated   | `T2-confidential`       | S           | scoped                        | G           | Data owner; DLP; disclosure assessment                                                   |
| Procedural case metadata (PACK-09)           | Confidential case metadata | `T2-case-metadata`      | S           | scoped, purpose-bound         | G           | Metadata only; case content excluded                                                     |
| Procedural case content (PACK-09)            | Confidential / regulated   | `T2-confidential`       | S           | scoped, purpose-bound         | G           | Data owner; DLP; redaction                                                               |
| Compliance case content, sensitive (PACK-09) | Highly confidential        | `T3-restricted`         | N           | domain surface, purpose-bound | G           | Manual approval; disclosure review                                                       |
| Legal and disciplinary case content          | Highly confidential        | `T3-restricted`         | N           | domain surface, purpose-bound | G           | As above, plus independent review                                                        |
| Sealed evidence bundles (PACK-11)            | Highly confidential        | `T3-restricted`         | N           | reference only, never content | G           | Reference-only export; bundle stays sealed                                               |
| Privileged session evidence (PACK-12)        | Highly confidential        | `T3-restricted`         | N           | reviewer surfaces only        | G           | Reviewer and custodian only; contains no secrets by design                               |
| Audit records (PACK-02)                      | Highly confidential        | `T3-restricted`         | N           | audit surfaces only           | G           | Custodian; immutable; export never mutates source                                        |
| Protected citizen correspondence             | Highly confidential        | `T3-restricted`         | N           | domain surface only           | G           | Data owner; redaction; recipient obligation                                              |
| Medical / special-category data (if any)     | Highly confidential        | `T3-restricted`         | N           | domain surface only           | G           | Explicit legal basis; disclosure review; manual approval                                 |
| Whistleblower identity and submissions       | Absolutely excluded        | `T4-prohibited`         | N           | **never**                     | N           | Excluded from ordinary, admin, HR and management access                                  |
| Cryptographic credentials and key material   | Absolutely excluded        | `T4-prohibited`         | N           | **never**                     | N           | Never indexed, never exported                                                            |
| Ballot-level and intermediate-tally material | Absolutely excluded        | `T4-prohibited`         | N           | **never**                     | N           | See section 4                                                                            |
| **Final certified result**                   | Public authoritative       | `T0-open-authoritative` | N (PACK-12) | not via PACK-12 admin search  | N (PACK-12) | Published only by the authoritative voting/result-certification domain — see section 4.2 |

---

## 4. Voting material — two distinct categories

An earlier draft carried the blanket rule _"ballot content, vote
envelopes, tallies — never, under any condition"_. That was too broad:
it would have forbidden the publication of a final certified result,
which is a legitimate, indeed necessary, governed act. The rule is split.

### 4.1 Absolute prohibition — `T4-prohibited`

`P12-VOTE-001` The following MUST NEVER be reachable through any PACK-12
search or export path, under any purpose, role, approval or emergency
condition:

- ballot content;
- individual vote selections;
- vote envelopes;
- eligibility- or credential-to-ballot linkage;
- voter-to-choice linkage;
- cryptographic voting secrets;
- intermediate tally;
- partial tally;
- non-certified tally material;
- raw tally inputs from which individual choices could be reconstructed.

`P12-VOTE-002` This prohibition MUST be structural, not configurational:
PACK-12 defines no reference type capable of pointing at any of the
above, following the precedent PACK-10 and PACK-11 set at the same
boundary. There is nothing to misconfigure.

`P12-VOTE-003` `P12-BG-010` extends this to break-glass: no emergency
condition reaches any item in section 4.1.

Refusals use `SEARCH_BALLOT_CONTENT_PROHIBITED` and
`EXPORT_BALLOT_CONTENT_PROHIBITED`. Either occurring is an incident, not
a routine denial.

### 4.2 Final certified result — permitted, but not by PACK-12

`P12-VOTE-004` A final certified result MAY be published or transmitted,
and PACK-12 MUST NOT be read as forbidding it. It is permitted only when
**all** of the following hold:

- it flows through the authoritative voting and result-certification
  domain, which owns the semantics;
- the vote is formally closed;
- certification has occurred;
- it is released through an approved publication rendition;
- it carries no ballot-level data;
- it carries no correlation identifiers;
- it is not obtained through privileged administrative search;
- it is not obtained through any PACK-12 raw export path;
- it carries an evidence reference to the certification decision and to
  the publication decision.

`P12-VOTE-005` PACK-12 MAY audit **the fact** that a governed
publication occurred — recording the certification and publication
references and the access events on the rendition. PACK-12 MUST NOT
become the owner of voting-result semantics, MUST NOT certify, MUST NOT
decide closure, and MUST NOT be a publication path of its own.

`P12-VOTE-006` Until certification and closure have occurred, result
material remains in section 4.1. "Not yet certified" is
`T4-prohibited`, not a weaker tier.

---

## 5. Search enforcement points

| Point            | What is checked                                              | Requirement    |
| ---------------- | ------------------------------------------------------------ | -------------- |
| Index admission  | Data class permitted in this index by `IndexPolicy` and tier | `P12-SRCH-004` |
| Field projection | Field permitted by `IndexFieldPolicy`                        | `P12-SRCH-004` |
| Query admission  | Scope present; purpose valid; mode permitted                 | `P12-SRCH-010` |
| Result retrieval | Source authorization re-resolved against current state       | `P12-SRCH-005` |
| Snippet          | Same restriction as source record                            | `P12-SRCH-006` |
| Count            | Computed over authorized set only                            | `P12-SRCH-007` |
| Facet/suggestion | No restricted value or term disclosed                        | `P12-SRCH-008` |
| Cache read       | Key includes effective authorization context                 | `P12-SRCH-009` |
| Post-deletion    | Removed from index; removal evidenced                        | `P12-SRCH-015` |

Four independent enforcement points, not one, is the design: index-time
filtering alone fails when authorization changes; query-time filtering
alone means restricted content sat in a shared index.

---

## 6. Export field policy

`P12-EXP-008` requires denied fields to be excluded before artifact
generation. The decision order:

```text
requested fields
→ source classification and enforcement tier
→ record-class field policy
→ purpose filter
→ recipient-category filter
→ DLP transform (mask / redact / pseudonymize / aggregate)
→ disclosure assessment (cohort, cumulative, differencing)
→ permitted field set
→ artifact generation
```

A field failing any stage MUST NOT reach the artifact. Filtering at
delivery, or hiding at presentation, MUST NOT be treated as equivalent.

---

## 7. Export control profile by recipient category

| Recipient category           | Example                            | Minimum controls                                                             |
| ---------------------------- | ---------------------------------- | ---------------------------------------------------------------------------- |
| Internal, same organization  | Domain administrator in scope      | Purpose, expiry, access audit                                                |
| Internal, other organization | Federal body reading a Land record | Cross-scope basis (`P12-ORG-006`), purpose, expiry, access audit             |
| Independent oversight        | Auditor, DPO, arbitrator           | Purpose, expiry, access audit, no re-sharing without basis                   |
| External authority           | Supervisory or electoral authority | Legal basis reference, obligation record, watermark, destruction attestation |
| External processor           | Contracted service provider        | Obligation record, transfer-channel restriction, destruction attestation     |
| Public                       | Transparency publication           | Disclosure assessment mandatory; aggregation; no personal data               |

`P12-EXP-014` requires the obligation to be explicit on the export
object. `P12-DLP-004` forbids describing any of these as guaranteeing
deletion at the recipient.

---

## 8. Interaction with retention, legal hold and deletion

| Situation               | Search                                | Export                                              |
| ----------------------- | ------------------------------------- | --------------------------------------------------- |
| Within retention        | Per matrix                            | Per matrix                                          |
| Under legal hold        | Unchanged access; hold widens nothing | Hold is not authorization (`P12-EXP-017`)           |
| Disposal-authorized     | Still retrievable until disposed      | New exports SHOULD be refused pending disposal      |
| Destroyed               | Not retrievable; removal evidenced    | Not exportable; prior artifacts unaffected in place |
| Access revoked          | Not retrievable (`P12-SRCH-012`)      | Not includable in new exports (`P12-EXP-018`)       |
| Export artifact expired | n/a                                   | No further access; artifact record retained         |
| Export artifact revoked | n/a                                   | No further platform-mediated access                 |

PACK-09 decides retention, disposal and hold state. PACK-12 observes
those decisions and MUST NOT re-decide them (`P12-ORG-002`).

---

## 9. Statistical disclosure control hooks

| Hook                   | Applies to                        | Requirement   |
| ---------------------- | --------------------------------- | ------------- |
| Cohort threshold       | Any aggregate release             | `P12-SDC-001` |
| Suppression            | Cells below threshold             | `P12-SDC-007` |
| Complement protection  | Totals, facets, neighbour cohorts | `P12-SDC-007` |
| Differencing detection | Successive similar queries        | `P12-SDC-003` |
| Cumulative accounting  | Multiple permitted exports        | `P12-SDC-004` |
| Exception decision     | Any override                      | `P12-SDC-006` |
| Release history        | Reviewer visibility               | `P12-SDC-008` |

`P12-SDC-005`: a threshold alone is not protection. The hooks are
cumulative, and an implementation shipping only the threshold has not
satisfied this matrix.
