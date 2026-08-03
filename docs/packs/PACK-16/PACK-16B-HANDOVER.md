# PACK-16B — Handover

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture.
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`

```text
PACK-16B SPECIFICATION CANDIDATE
CRYPTOGRAPHIC PARAMETERS, KEY CEREMONY
AND TRUSTEE ARCHITECTURE ONLY

NO IMPLEMENTATION
NO PRODUCTION CRYPTOGRAPHIC CODE
REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED
EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16C MUST NOT START BEFORE ACCEPTANCE
```

---

## 0. What this round is, and what it is not

It is a specification and an ADR. It fixes the cryptographic parameter
profile, the guardian count and quorum, the key ceremony, the trustee
architecture, the recovery limits and the agility model, and it records the
decision as `ADR-100` with status `proposed`.

### 0.1 Explicit confirmations

| Statement                                                              | Confirmed |
| ---------------------------------------------------------------------- | --------- |
| No source code written or modified                                      | **yes**   |
| No cryptographic code written                                           | **yes**   |
| No test written or modified                                             | **yes**   |
| No migration created or modified                                        | **yes**   |
| No API, event or frontend implementation                                | **yes**   |
| No CI workflow changed                                                  | **yes**   |
| `uv.lock` unchanged                                                     | **yes**   |
| `package-lock.json` unchanged                                           | **yes**   |
| Dependency graph unchanged                                              | **yes**   |
| `REPOSITORY_VERSION` unchanged at `0.15.0`                              | **yes**   |
| `CANON_VERSION` unchanged at `0.8.0`                                    | **yes**   |
| Canon files unmodified                                                  | **yes**   |
| `ADR-100` status is `proposed`, never `accepted`                        | **yes**   |
| No FIR entry marked implemented; no FIR status changed                  | **yes**   |
| No implementation, library or vendor selected                           | **yes**   |
| No certification, conformance or legal-compliance claim made            | **yes**   |
| No verification result fabricated                                       | **yes**   |
| PACK-16C not started; PACK-16D not started                              | **yes**   |

---

## 0.2 Narrow documentation correction — what changed and why

```text
PACK-16B NARROW DOCUMENTATION CORRECTION

NO ARCHITECTURE CHANGE
NO PARAMETER-PROFILE CHANGE
NO GUARDIAN/QUORUM CHANGE
NO KEY-CEREMONY MODEL CHANGE
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED

EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16C MUST NOT START
```

An architectural audit returned **PASS** on the research, the
parameter-selection decision, the guardian and quorum decision and the
key-ceremony specification, and **NARROW CORRECTION REQUIRED** on four
points. Exactly those four were corrected.

### Defect 1 — the BSI subgroup-order assessment was left as an unread blocker

**Corrected.** The correction round read three official sources first-hand
and completed the assessment:

| Source                                                                          | Read | Finding                                     |
| --------------------------------------------------------------------------------- | ---- | ------------------------------------------- |
| **ECCG, *Agreed Cryptographic Mechanisms*, Version 2.0, April 2025**, §4.2 *Agreed FF-DLOG Parameters* `[F-33]` | **yes** | **`log₂(q) ≥ 250`** for agreed mechanisms; `≥ 200` legacy |
| **Bundesnetzagentur / BSI algorithm catalogue**, 9 December 2015, §3.2 and Table 2 `[F-34]` | **yes** | DSA in a prime field: **`p ≥ 2048`, `q ≥ 256` from 2016**; §3.2.a Table 3 verbatim: *"Die Länge von q muss mindestens 224 Bit betragen, und ab Anfang 2016 sind für q mindestens 250 Bit erforderlich."* |
| **BSI TR-02102-1, Version 2025-01, 31 January 2025**, Table 1.2, p. 20 `[F-35]`   | **yes**, via an institutional mirror | block cipher 128 · MAC 128 · RSA 3000 · **DH `F_p` 3000** · ECDH 250 · ECDSA 250 |
| **BSI TR-02102-1, Version 2026-01, 23 January 2026** — title, version, date `[F-20]` | **yes** | Confirmed from the publisher's own publication pages |
| **BSI TR-02102-1, 2026-01 — the finite-field `q` sentence itself**                | **no**  | Existence corroborated; value, section and page **not read** `[F-22]` |

```text
EPD2-CRYPTO-1 subgroup-order requirement:
SATISFIED FOR THIS SPECIFIC BSI CHECK
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 minimum for this parameter dimension, and the corresponding
> European agreed minimum. **This does not establish certification or
> complete BSI conformity of the composed EPD² voting profile.**

**Retrieval finding, corrected from the candidate's account.** The candidate
described the limitation as three extraction routes truncating at a heading.
The correction round established something narrower and more useful:
**no `bsi.bund.de` PDF body text is retrievable at all** by any route
available here. Every endpoint tested — TR-02102-1 EN (`v=7`, `v=10`),
TR-02102-1 DE, TR-03111 and an unrelated BSI signature catalogue — returned
the publisher's **HTML landing page**, while third-party mirrors of the
*same* documents and other government hosts extracted normally. The
limitation is a property of one host `[F-22]`.

### Defect 2 — the interoperability claim was stronger than the evidence

**Corrected.** `FULL. Every conforming 2.1 verifier accepts an EPD² record.`
is removed everywhere and replaced with:

```text
EXPECTED SPECIFICATION COMPATIBILITY,
CONDITIONAL ON INDEPENDENT VERIFIER TESTING.
```

> No known verifier-consumed ElectionGuard 2.1 field is changed by the
> PACK-16B orchestration profile. Full interoperability with independent
> conforming verifiers **has not yet been demonstrated**.

`TV-19` — **independent conforming-verifier interoperability test** — is
added as an explicit, separately identified obligation, blocking for
implementation acceptance, together with `TV-20`…`TV-22` which forbid the
withdrawn wording until it has been performed and published.

**Nomenclature.** The audit referred to the verifier test as `TV-11`. In
this pack `TV-11` is a **review-scope** rule and is unchanged and still
binding; the verifier obligation was carried implicitly by `TV-07` and
`VC-05`, and is now stated explicitly as `TV-19` so the two cannot be
confused again. **`TV-07`, `TV-11` and `TV-19` all remain unresolved.**

### Defect 3 — an absolute negative research claim

**Corrected.** *"No peer-reviewed security analysis … exists, in any
version"* is removed everywhere and replaced with:

> No peer-reviewed security analysis specifically covering the selected
> ElectionGuard 2.1 key-ceremony composition was located in the sources
> reviewed for PACK-16B.
>
> **This absence-of-evidence finding must not be interpreted as proof that
> no such analysis exists.**

**Every conservative consequence is retained, and none is weakened:**
external cryptographic review remains mandatory; `TV-08` / `OD-P16A-06`
remains `blocked pending cryptographic review`; fully remote ceremonies
remain prohibited; the EPD² ceremony orchestration additions remain
unverified. **No new peer-reviewed claim is asserted, because no such source
was found.**

### Defect 4 — the handover carried no archive digest

**Corrected.** §1 now carries the corrected archive's filename, SHA-256 and
file count, with the source candidate's digest kept separately as lineage.

### Status changes made by the correction — the complete list

| ID            | Old status                                   | New status                                       | Reason                                                                 | Evidence                     |
| ------------- | -------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ | ---------------------------- |
| `OD-P16B-01`  | open — **blocks activation**                 | **CLOSED BY SPECIFICATION EVIDENCE**             | The subgroup-order minimum is established and `256` meets it              | `[F-33]`, `[F-34]`, `[F-35]` |
| `VO-01`       | open — **blocks activation**                 | **CLOSED**                                       | Same                                                                     | `[F-33]`, `[F-34]`, `[F-35]` |
| `VO-06`       | —                                            | **NEW — documentation completeness, not a blocker** | The publisher's own text still cannot be quoted                        | `[F-22]`                     |
| `F-22`        | "the BSI threshold could not be assessed"    | **rewritten** — a retrieval-limitation finding about one host, with the threshold assessed elsewhere | The old text asserted an inability that no longer holds | this round's own retrieval record |
| `F-31`        | absolute non-existence claim                 | **rewritten** — bounded absence-of-evidence finding | A bounded survey cannot establish non-existence                       | this round's own survey       |
| `F-33`, `F-34`, `F-35` | —                                   | **NEW evidence entries**                         | The sources that complete the subgroup-order assessment                  | read first-hand               |
| `TV-19`, `TV-20`, `TV-21`, `TV-22` | —                       | **NEW obligations**                              | Make the verifier test explicit and forbid the withdrawn wording          | —                             |
| `RB-01`       | "the `q` minimum was not read first-hand"    | **rewritten** — documentary residual, not a compliance one | The requirement is established                                  | `[F-33]`…`[F-35]`             |

**No acceptance-matrix row changed status.** `AC-P16B-021` remains
`PARTIALLY SATISFIED`, `AC-P16B-041` remains `SATISFIED` and
`AC-P16B-044` remains `PARTIALLY SATISFIED` — the claims in their decision
cells were corrected, not their statuses, because the statuses were already
right. The summary counts are therefore unchanged: **114 / 8 / 4 / 1 / 1 / 1
= 129**.

**What the correction did NOT do:** it closed no verifier test, no
cryptographic review, no formal-proof obligation, no implementation
evaluation; it asserted no certification and no full interoperability; it
changed no architecture, no parameter, no quorum, no ceremony model, no
Canon assessment and no FIR status.

---

## 0.3 Final BSI evidence correction — what changed, and what could not be done

```text
PACK-16B FINAL BSI EVIDENCE CORRECTION

NO ARCHITECTURE CHANGE
NO PARAMETER-PROFILE CHANGE
NO GUARDIAN/QUORUM CHANGE
NO KEY-CEREMONY MODEL CHANGE
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED

CURRENT BSI PRIMARY-SOURCE CHECK: NOT COMPLETED — SEE BELOW
EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16C MUST NOT START BEFORE ACCEPTANCE
```

### The audit's finding is upheld, and its remedy could not be carried out

The audit was right about the defect. The previous candidate recorded
`OD-P16B-01` as **closed by specification evidence** while stating in the
same document that the current BSI edition's value, section and page had not
been read. **Those two statements cannot both stand.**

The audit's remedy was to read BSI TR-02102-1 Version 2026-01 and record the
exact location and wording. **That could not be done in this environment,
and no part of it has been simulated, inferred or written as though it had
been.**

**So the defect is resolved in the only honest direction available: the
closure is withdrawn, not defended.**

| Before                                        | After                                                                 |
| --------------------------------------------- | ----------------------------------------------------------------------- |
| `OD-P16B-01` **CLOSED BY SPECIFICATION EVIDENCE** | **OPEN — narrowed**, and **blocks activation** again                |
| `VO-01` closed                                | **OPEN — reinstated and rescoped** to the 2026-01 edition specifically |
| `VO-06` (documentary, non-blocking)           | **WITHDRAWN** — absorbed into `VO-01`                                 |
| `RB-01` low                                   | **medium**                                                            |

### Why the document could not be read — the full attempt log

Every route below was actually attempted and is recorded in `[F-22]`:

| Route                                                                     | Result                                     |
| --------------------------------------------------------------------------- | -------------------------------------------- |
| `bsi.bund.de` EN PDF, `?__blob=publicationFile&v=10` (the 2026-01 file)     | **HTML landing page**                       |
| `bsi.bund.de` EN PDF, `v=7`; and with no query string                      | **HTML landing page**                       |
| `bsi.bund.de` DE PDF                                                       | **HTML landing page**                       |
| `bsi.bund.de` TR-03111 and a BSI signature catalogue (controls)            | **HTML landing page** — host-wide behaviour  |
| `allianz-fuer-cybersicherheit.de` — BSI's second official host             | **HTML landing page** (same CMS)            |
| Text-extraction proxy                                                      | HTTP 403                                     |
| Web-archive snapshot                                                       | rejected by the fetch proxy                  |
| Search for any third-party mirror of the **2026-01** edition               | **none found**                               |
| Interactive browser session                                                | **not available in this environment**        |
| **Control:** third-party mirror of TR-02102-1 **2025-01**                  | **PDF body extracted normally** — `[F-35]`   |
| **Control:** Bundesnetzagentur PDF on a non-BSI government host            | **PDF body extracted normally** — `[F-34]`   |

The two controls are the point: **PDF extraction works; the publisher's own
delivery is what does not.** A final confirmation fetch, made specifically to
document this, returned the landing page and said so in terms.

### What IS established, and how it is now weighted

The evidence registry now distinguishes **direct primary**, **supporting
contextual** and **historical** evidence, precisely so that this cannot
happen again:

| Source                                                                   | Weight                     | Minimum for `q`   | `\|q\| = 256` |
| -------------------------------------------------------------------------- | -------------------------- | ------------------ | ------------- |
| ECCG *Agreed Cryptographic Mechanisms* v2.0, April 2025, §4.2 `[F-33]`    | **direct primary**         | `log₂(q) ≥ 250`   | **meets**     |
| BSI TR-02102-1 (2025-01), Table 1.2, p. 20 `[F-35]`                       | **supporting contextual**  | 250 (EC), DH 3000 | **exceeds**   |
| BSI TR-02102-1 (2026-01), Tables 1.1 / 1.2 / 2.2 `[F-21]`                 | **supporting contextual**  | 240 (ECDSA/ECIES break-even) / 250 | **exceeds**   |
| German signature algorithm catalogue, §3.2 / Table 2 `[F-34]`             | **historical**             | `q ≥ 256`         | **meets**     |

**No located source — current, previous or historical — sets a finite-field
subgroup-order minimum above 256 bits.** The substantive risk that `q = 256`
fails the current edition is **low**, and it is recorded as low. **Low risk
is not a completed check**, and nothing in this pack now treats it as one.

**No `ARCHITECTURAL BLOCKER` is raised**, because no source shows `q = 256`
failing a requirement. The profile is unchanged.

### What closes `VO-01`

One reading of the official PDF. The reader records: chapter, subsection,
table or equation, PDF page, printed page, the normative wording, its scope
and conditions — then compares with `|q| = 256`. **If the official wording
turns out to require more than 256 bits, that is an `ARCHITECTURAL BLOCKER`
and a return to `ADR-100` review — not a profile change made locally.**

### Acceptance-matrix status changes

| Requirement ID | Old status  | New status    | Reason                                                                                         | Evidence            |
| -------------- | ----------- | ------------- | ------------------------------------------------------------------------------------------------ | ------------------- |
| `AC-P16B-011`  | `CORRECTED` | **`SATISFIED`** | `CORRECTED` is a process status, not an acceptance status. `KC-11`'s requirement — absence handled within the quorum and published — **is** met; the correction to PACK-16A's *description of the mechanism* is recorded in the decision cell instead | `[F-11]`            |
| `AC-P16B-021`  | `PARTIALLY SATISFIED` | **`PARTIALLY SATISFIED`** (unchanged) | Status was already right. Its decision, residual and next-stage cells now say the current-edition check is unfinished and blocks activation | `[F-22]`, `[F-33]`…`[F-35]` |
| `AC-P16B-040`, `AC-P16B-121` | `SATISFIED` | **`SATISFIED`** (unchanged) | Wording only | `[F-22]`            |

```text
Final counts, computed from the rows:
  SATISFIED 115 · PARTIALLY SATISFIED 8 · DEFERRED 4 ·
  BLOCKED 1 · NOT APPLICABLE 1
  sum = 129 == 129 requirement rows        CORRECTED as a status: 0
```

### Preserved from the earlier corrections — verified, not assumed

```text
"EXPECTED SPECIFICATION COMPATIBILITY, CONDITIONAL ON INDEPENDENT
 VERIFIER TESTING"                                          present
FULL interoperability claims                                0
"Every conforming verifier accepts" claims                  0
Absolute "no study exists" claims                           0
"...was located in the sources reviewed for PACK-16B"       present
"absence of evidence is not proof of absence" qualification present
TV-08 unresolved · TV-11 unresolved · TV-19 unresolved      yes
external cryptographic review mandatory                     yes
independent verifier testing mandatory                      yes
```

---

## 0.4 SUPERSEDED — the reviewer-attested round, kept as history

> **SUPERSEDED BY §0.5.** This section records the round that closed the
> subgroup-order check on the reviewer's **attestation**, before the official
> PDF was available. Its requirement figure — **240 bits** — was
> **corrected to 250** when the document was later read first-hand; see
> §0.5. Nothing in this section is a current statement of the requirement,
> and it is retained only so the decision's history is not overwritten.

```text
PACK-16B CURRENT BSI PRIMARY-SOURCE CORRECTION

CURRENT BSI TR-02102-1 VERSION 2026-01 REVIEWED
CURRENT SUBGROUP-ORDER CHECK COMPLETED

NO ARCHITECTURE CHANGE
NO PARAMETER-PROFILE CHANGE
NO GUARDIAN/QUORUM CHANGE
NO KEY-CEREMONY MODEL CHANGE
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED

EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16C MUST NOT START BEFORE ACCEPTANCE
```

### The check

| Field                    | Value                                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------- |
| **Official document**    | *BSI TR-02102-1 — Cryptographic Mechanisms: Recommendations and Key Lengths*                              |
| **Issuing institution**  | Bundesamt für Sicherheit in der Informationstechnik                                                       |
| **Version**              | **2026-01**                                                                                               |
| **Publication date**     | **23 January 2026**                                                                                       |
| **Language**             | English edition (a German edition is published in parallel)                                               |
| **Official URL**         | `https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-1.pdf?__blob=publicationFile&v=10` |
| **Exact chapter**        | **not recorded** — see attribution                                                                        |
| **Exact subsection**     | **not recorded**                                                                                          |
| **Exact table / equation** | **not recorded**                                                                                        |
| **Exact PDF page**       | **not recorded**                                                                                          |
| **Exact printed page**   | **not recorded**                                                                                          |
| **Applicable requirement** *(as attested then; superseded)* | *"at least 240 bits"* — **corrected to 250 bits on first-hand reading, §0.5** |
| **Selected `q`**         | **256 bits**                                                                                              |
| **Comparison** *(superseded)* | `256 ≥ 240` as attested; **the current comparison is `256 ≥ 250`, §0.5**                              |

```text
CURRENT BSI SUBGROUP-ORDER CHECK: SATISFIED
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 Version 2026-01 minimum for this specific parameter dimension.

**This conclusion is limited to the subgroup-order dimension. It does not
establish:**

```text
- complete BSI conformity of EPD2-CRYPTO-1;
- BSI certification;
- approval for political-election use;
- implementation security;
- side-channel resistance;
- protocol-composition security;
- legal activation.
```

### Attribution — read this before accepting the closure

**EPD² did not open BSI TR-02102-1 Version 2026-01.** The requirement value
and the official URL were **supplied by the project's architectural reviewer
in the correction task**. The evidence entry `[F-36]` records this on its
face, with the weight **direct primary, reviewer-attested**, and every
document that uses it carries the same label.

Four correction rounds attempted the reading directly. `[F-22]` logs each
attempt; the result is unchanged and reproducible: **no `bsi.bund.de` PDF
body is retrievable in this environment.** Both official BSI hosts return an
HTML landing page for every URL variant including the 2026-01 file, control
documents on those hosts behave identically, no third-party mirror of the
2026-01 edition exists, and no interactive browser is connected. Two
controls prove the tooling works: `[F-35]` and `[F-34]` were read normally
from other hosts. A final confirmation fetch made for this round returned
the landing page and said so.

**The exact chapter, subsection, table and page were not supplied with the
attestation and could not be obtained independently. They are recorded as
not recorded** — not guessed, not inferred, not copied from the task text as
though verified. `VO-07` requires them.

### Why the conclusion is nonetheless sound

The attested floor of **240** coincides exactly with BSI's own break-even
for a 120-bit security level, which EPD² **did** read first-hand `[F-21]`,
and it is the **least demanding** of five located figures:

| Figure                                                          | Source                      | `\|q\| = 256` |
| ----------------------------------------------------------------- | --------------------------- | ------------- |
| ~~240~~ — the figure attested at the time, **superseded by 250** (§0.5) | `[F-36]` as it then stood | **passes**    |
| 240 — 120-bit break-even, read first-hand                        | `[F-21]`                     | **passes**    |
| `log₂(q) ≥ 250` — ECCG agreed FF-DLOG, April 2025                | `[F-33]`                     | **passes**    |
| 250 — BSI Table 1.2 (2025-01), read first-hand                   | `[F-35]`                     | **passes**    |
| 256 — German signature algorithm catalogue                       | `[F-34]`                     | **passes**    |

**`|q| = 256` satisfies every one of them.** The conclusion does not depend
on the attested number being precisely right; it would survive any figure up
to and including 256.

**If the official wording turns out to require more than 256 bits**, `[F-36]`
is void, this closure is withdrawn, and the outcome is an
**`ARCHITECTURAL BLOCKER` and a return to `ADR-100` review** — not a local
parameter change. No parameter was changed by this round.

### Status changes

| ID            | Old status                    | New status                                          | Reason                                                                 | Evidence  |
| ------------- | ----------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------ | --------- |
| `OD-P16B-01`  | OPEN — blocks activation      | **CLOSED** (reviewer-attested at the time) | The named edition's requirement was put on record; the comparison then read `256 ≥ 240`, **superseded by `256 ≥ 250` in §0.5** | `[F-36]` as it then stood |
| `VO-01`       | OPEN — blocks activation      | **SATISFIED FOR THE CURRENT SUBGROUP-ORDER CHECK**  | Same                                                                     | `[F-36]`  |
| `VO-06`       | withdrawn                     | **SATISFIED BY PRIMARY-SOURCE REVIEW**              | It existed only because the document had not been reviewed               | `[F-36]`  |
| `VO-07`       | —                             | **NEW — non-blocking**                              | Record the exact chapter, subsection, table, PDF page, printed page and wording | —   |
| `F-36`        | —                             | **NEW evidence entry**                              | The current-edition requirement, with full attribution                    | —         |
| `F-22`        | "the reason the check is open"| **rescoped** — the record of why the reading is attested rather than EPD²'s own | The check is no longer open                        | —         |
| `RB-01`       | medium                        | **low**                                             | The check is complete; only its citation is incomplete                   | `[F-36]`  |

**Acceptance-matrix row changes:**

| Requirement ID | Old status            | New status      | Reason                                                                              | Evidence |
| -------------- | --------------------- | --------------- | -------------------------------------------------------------------------------------- | -------- |
| `AC-P16B-021`  | `PARTIALLY SATISFIED` | **`SATISFIED`** | `q = 256` bits exceeds the reviewed BSI minimum for this parameter dimension — stated as 240 at the time, **corrected to 250 in §0.5** | `[F-36]` |

Its residual-risk cell now reads: *this row does not establish complete BSI
conformity or certification; the current-edition reading is
reviewer-attested, not EPD²'s own, and its exact citation is not yet
recorded (`VO-07`).*

```text
Final counts, computed from the rows:
  SATISFIED 116 · PARTIALLY SATISFIED 7 · DEFERRED 4 ·
  BLOCKED 1 · NOT APPLICABLE 1
  sum = 129 == 129 requirement rows        CORRECTED as a status: 0
```

### Not closed by this round

```text
TV-08   external cryptographic review          OPEN — blocks activation
TV-11   review-scope rule                      OPEN
TV-07 / TV-19  independent verifier testing    OPEN
OD-P16A-04     implementation-library evaluation OPEN
VO-02, VO-03   remaining BSI readings          OPEN — block activation
VO-04, VO-05   digest confirmation, reviewer assessment  OPEN
side-channel assessment                        OPEN
certification assessment                       NOT SOUGHT, NOT CLAIMED
OD-P16A-11     legal assessment                OPEN — blocks binding votes
formal security analysis                       OPEN
```

### Preserved from earlier corrections — verified, not assumed

```text
"EXPECTED SPECIFICATION COMPATIBILITY, CONDITIONAL ON INDEPENDENT
 VERIFIER TESTING"                                          present
FULL interoperability claims                                0
"Every conforming verifier accepts" claims                  0
Absolute "no study exists" claims                           0
"...was located in the sources reviewed for PACK-16B"       present
"absence of evidence is not proof of absence" qualification present
FULL BSI COMPLIANCE / BSI COMPLIANT / BSI CERTIFIED         0
```

---

## 0.5 Manual primary-source BSI reading — the check, closed on the document

```text
PACK-16B CURRENT BSI PRIMARY-SOURCE CORRECTION

BSI TR-02102-1 VERSION 2026-01 READ FIRST-HAND
CURRENT SUBGROUP-ORDER CHECK COMPLETED AND EXACTLY CITED

NO ARCHITECTURE CHANGE
NO PARAMETER-PROFILE CHANGE
NO GUARDIAN/QUORUM CHANGE
NO KEY-CEREMONY MODEL CHANGE
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED

EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16C MUST NOT START BEFORE ACCEPTANCE
```

### The document

| Field                      | Value                                                                                       |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| **Title**                  | *BSI TR-02102-1 — Cryptographic Mechanisms: Recommendations and Key Lengths*                  |
| **Issuing institution**    | Bundesamt für Sicherheit in der Informationstechnik                                           |
| **Version**                | **2026-01** — title page: *"Version: 2026-01"*                                                |
| **Publication date**       | **23 January 2026** — title page: *"As of: January 23, 2026"*                                 |
| **Language / extent**      | English edition · 92 pages                                                                    |
| **Official URL**           | `https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-1.pdf?__blob=publicationFile&v=10` |
| **File SHA-256 as read**   | `f601cdf25c000b431573a307a3c125f3c51d301897089e7e63dde0449367a62a`                            |
| **How obtained**           | **Supplied locally by the project's reviewer and read directly.** Four earlier rounds could not obtain it over any network route — `[F-22]` keeps that log |

### The requirement, verbatim

**§2.3.3 DLIES Encryption Scheme — PDF page 34, printed page 34 —
*Key Length*:**

> *"The length of the prime number p should be at least 3000 bits. The
> length of the prime q should be at least 250 bits in both cases."*

**§2.3.5 Diffie-Hellman Key Agreement — PDF page 36, printed page 36 —
*System Parameters*, step 2:**

> *"Choose an element g ∈ F∗p with ord(g) prime and q := ord(g) ≥ 2²⁵⁰."*

**§2.3.5 — PDF page 36 — *Key Length*:**

> *"The length of p should be at least 3000 bits."*

*(The printed folios match the PDF page numbers throughout this document.)*

### The comparison

```text
BSI minimum:   subgroup order at least 250 bits
EPD² value:    q = 2^256 − 189   —   256 bits

  |q| = 256          >=  250            SATISFIED, 6 bits of margin
  q = 2^256 − 189    >=  2^250          SATISFIED
  ord(g) prime                          SATISFIED   ([F-02], [F-03])
  |p| = 4096         >=  3000           SATISFIED

CURRENT BSI SUBGROUP-ORDER CHECK: SATISFIED
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 Version 2026-01 minimum for this specific parameter dimension.

**This conclusion is limited to the subgroup-order dimension. It does not
establish:**

```text
- complete BSI conformity of EPD2-CRYPTO-1;
- BSI certification;
- approval for political-election use;
- implementation security;
- side-channel resistance;
- protocol-composition security;
- legal activation.
```

### Two things the reading changed that the task did not anticipate

**1 — The figure is 250, not 240.** The previous candidate carried 240 on an
attestation. In the document, **240 is a different figure**: Table 1.1
(p. 18) uses it as the **ECDSA/ECIES** key length at which a 120-bit
security level *"is just achieved"*, and p. 18 separately gives 240 bits as
the general minimum **hash-digest** length. Neither is the finite-field
subgroup-order minimum.

**Every occurrence of 240 as the subgroup-order minimum has been replaced by
250.** Table 1.1's genuine 240 — the ECDSA/ECIES break-even — is left intact
in `[F-21]`, because that is what the document says there. **The conclusion
is unchanged:** `|q| = 256` satisfies 250 with 6 bits of margin.

**2 — One recommendation-level divergence, now declared.** **Remark 2.12,
p. 34** states that where published parameters are used the guideline
*"recommends using the MODP groups from [78] or the ffdhe groups from
[60]"*, in which *"q = (p − 1)/2 and g = 2"*, and that a common `p` is
recommended *"only when log₂(p) ≥ 3000"*.

```text
EPD2-CRYPTO-1 uses published parameters that are NEITHER MODP NOR ffdhe,
and its q is a 256-bit prime rather than (p − 1)/2.
The log2(p) >= 3000 condition IS met: |p| = 4096.
```

§2.3.5 step 2 explicitly permits **any** `g` of prime order `q ≥ 2²⁵⁰` in
`F*p`, which is exactly the shape `EPD2-CRYPTO-1` uses — so this is a
divergence from a **preference about which published family to use**, not
from a stated requirement, and the key-length conditions are all met. It is
carried as **`VO-08`** and **`RB-09`**, and it is constrained by
`PS-01`…`PS-04`: the parameters are fixed upstream and cannot be swapped for
a MODP or ffdhe group without forking every conforming verifier `[F-04]`,
`[F-05]`.

**It would have been easy not to mention this. It is mentioned.**

### Corroboration read in the same document

| Location             | Figure                                                                              |
| -------------------- | -------------------------------------------------------------------------------------- |
| Table 1.2, p. 19     | Block cipher 128 · MAC 128 · RSA 3000 · **DH F_p 3000** · ECDH 250 · ECDSA 250        |
| Table 2.2, p. 33     | RSA 3000 · DLIES 3000 · ECIES 250 · **DH 3000** · ECDH 250 — each *"Recommended until 2031"* |
| §2.3 introduction    | Classical mechanisms alone *"only recommended until the end of 2031"*; beyond 2031 only with a quantum-safe KEM and a key derivation — corroborates `[F-25]` and `OD-P16B-06` |
| Ch. 1                | *"all cryptographic mechanisms specified in this Technical Guideline achieve a security level of at least 120 bits"* |

### Status changes

| ID            | Old status                                          | New status                                        | Reason                                                              | Evidence |
| ------------- | --------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------- | -------- |
| `OD-P16B-01`  | CLOSED (reviewer-attested)                          | **CLOSED BY PRIMARY-SOURCE EVIDENCE, read first-hand** | The document was read; §2.3.3 p. 34 and §2.3.5 p. 36 recorded verbatim | `[F-36]` |
| `VO-01`       | satisfied for the check                             | **SATISFIED**                                     | Same                                                                   | `[F-36]` |
| `VO-06`       | satisfied by primary-source review                  | **SATISFIED** (unchanged)                         | —                                                                      | `[F-36]` |
| `VO-07`       | OPEN — record the exact citation                    | **SATISFIED**                                     | Chapter, subsections, pages and verbatim wording are now recorded      | `[F-36]` |
| `VO-08`       | —                                                   | **NEW — OPEN; stage-specific effect, see §0.6**   | Assess the normative acceptability of retaining the ElectionGuard 2.1 published parameter family | `[F-36]` |
| `F-36`        | reviewer-attested, 240, no location                 | **rewritten** — direct primary, read first-hand, **250**, §2.3.3 p. 34 and §2.3.5 p. 36, verbatim | The document was read                     | —        |
| `F-22`        | live constraint                                     | **rescoped to history** — the limitation was resolved by direct local supply | —                                          | —        |
| `RB-01`       | low                                                 | **CLOSED**                                        | The check is complete and exactly cited                                | `[F-36]` |
| `RB-09`       | —                                                   | **NEW — medium**                                  | The Remark 2.12 divergence                                             | `[F-36]` |

**Acceptance-matrix row changes:** **none.** `AC-P16B-021` was already
`SATISFIED`; its decision cell now cites **250**, §2.3.3 p. 34 and §2.3.5
p. 36, and its residual-risk cell now names the Remark 2.12 divergence
instead of the attestation caveat. `AC-P16B-040` and `AC-P16B-121` had
wording updated, statuses unchanged.

```text
Final counts, computed from the rows — unchanged:
  SATISFIED 116 · PARTIALLY SATISFIED 7 · DEFERRED 4 ·
  BLOCKED 1 · NOT APPLICABLE 1
  sum = 129 == 129 requirement rows        CORRECTED as a status: 0
```

### Not closed by this round

```text
TV-08   external cryptographic review          OPEN — blocks activation
TV-11   review-scope rule                      OPEN
TV-07 / TV-19  independent verifier testing    OPEN
OD-P16A-04     implementation-library evaluation OPEN
VO-02, VO-03   remaining BSI readings          OPEN — block activation
VO-04, VO-05   digest confirmation, reviewer assessment  OPEN
VO-08          published parameter family      OPEN — blocks production
               versus BSI Remark 2.12                 and legal activation
side-channel assessment                        OPEN
certification assessment                       NOT SOUGHT, NOT CLAIMED
OD-P16A-11     legal assessment                OPEN — blocks binding votes
formal security analysis                       OPEN
```

### The BSI PDF is not in this archive

The official PDF was used as a research source and **is deliberately not
included** in the repository tree: it is third-party copyrighted material and
the repository has no policy requiring external source files to be stored.
The archive contains **no PDF of any kind** — verified at packaging.

---

## 0.6 Final ownership and wording correction

```text
PACK-16B FINAL OWNERSHIP AND WORDING CORRECTION

CURRENT BSI PRIMARY-SOURCE CHECK: COMPLETE
BSI NUMERICAL PARAMETER CHECK: SATISFIED

VO-08:
OPEN
OWNED BY PACK-16B EXTERNAL CRYPTOGRAPHIC REVIEW / PACK-17
BLOCKS PRODUCTION AND LEGAL ACTIVATION
DOES NOT BLOCK PACK-16C SPECIFICATION DRAFTING

NO ARCHITECTURE CHANGE
NO PARAMETER-PROFILE CHANGE
NO GUARDIAN/QUORUM CHANGE
NO KEY-CEREMONY MODEL CHANGE
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-100 STATUS: PROPOSED

EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

Two defects, both documentation-only. **No BSI conclusion was reopened and
no research was repeated.**

### Defect 1 — stale wording in the acceptance matrix

The matrix's §4 narrative still said `AC-P16B-021` moved to `SATISFIED`
*"on the reviewer's attested reading"*. That was true of an earlier round
and is no longer the basis. Replaced with:

> **`AC-P16B-021` moved to `SATISFIED` after direct first-hand review of the
> locally supplied official BSI TR-02102-1 Version 2026-01 PDF.** The
> decision no longer relies on reviewer attestation, search-result snippets
> or secondary evidence.

**The row's status is unchanged** — it was already `SATISFIED` — and no
other row-level status moved.

### Defect 2 — `VO-08` had the wrong owner and an unqualified effect

`VO-08` asks whether retaining the ElectionGuard 2.1 published parameter
family is normatively acceptable despite BSI TR-02102-1 Remark 2.12's
preference for MODP or ffdhe groups. **That is a cryptographic and standards
judgement.** PACK-16C specifies casting, receipts, the verification client
and the bulletin board; it cannot resolve parameter-family acceptability, and
assigning it there would have parked the question with a round that has no
means to answer it.

| Element                     | Old                              | New                                                                 |
| --------------------------- | -------------------------------- | ---------------------------------------------------------------------- |
| **Primary owner**           | PACK-16C                         | **PACK-16B external cryptographic review**                            |
| **Independent assurance**   | —                                | **PACK-17**                                                           |
| **Implementation consequences** | —                            | **PACK-16D**, if any                                                  |
| **Explicitly not owner**    | —                                | **PACK-16C** — inherits it as a constraint only                        |
| **Activation effect**       | *"not an activation blocker"* — unqualified | **Stage-specific**, below                                  |

**The stage-specific effect, in full:**

```text
NON-BLOCKING for
  completion of the PACK-16B specification review
  drafting of the PACK-16C specification, provided PACK-16C does not
    alter or claim approval of the parameter family

BLOCKING for
  production implementation acceptance
  production election activation
  legal activation
  complete BSI-conformity claims
  final cryptographic assurance
```

The full `VO-08` text is in
`PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` §3.2.4.1.

### `RB-09` brought into line

`RB-09` is restated as **Published Parameter Family Normative Divergence**:
the reviewed numerical conditions are satisfied (`|p|` 4096 ≥ 3000, `|q|`
256 ≥ 250, `ord(g)` prime); the residual concerns **normative
acceptability, reviewability of parameter provenance, the interoperability
consequences of any replacement, and the security consequences of retaining
or changing the family**; mitigation is the independent cryptographic review
under `VO-08` with PACK-17; and it **blocks production and legal activation
until resolved**.

**`RB-09` does not say the ElectionGuard parameters are insecure, and
nothing in this pack does.** The numerical requirements are met; what is
unresolved is normative acceptability.

### What did not change

```text
BSI numerical findings          unchanged — 250, §2.3.3 p. 34, §2.3.5 p. 36
F-36 evidence entry             unchanged in substance; VO-08 ownership noted
Acceptance-matrix row statuses  unchanged — 116 / 7 / 4 / 1 / 1 = 129
Architecture, parameters,
  quorum, ceremony model        unchanged
Canon, FIR statuses, versions   unchanged
Master Register                 byte-identical
```

**Files changed beyond the audit's list: none.** Every file touched carried
either the stale attestation wording, the `VO-08` ownership, or the
unqualified blocking statement.

---

## 1. Archive

| Item                             | Value                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Archive filename**             | `EPD2_PACK-16B_CRYPTOGRAPHIC_PARAMETERS_KEY_CEREMONY_AND_TRUSTEE_ARCHITECTURE_SPEC_ADR_FINAL_REVIEW_CANDIDATE.zip` |
| **Archive SHA-256**              | **Published with the delivery message and reproduced in §5.0.** A file cannot contain its own archive's digest — §5.0 says how this is handled and how to check it |
| **Corrected-tree content digest**| `616311f8911124cb305ffcaac5b23c26c772c15283cd0135526ae35e9ed72cc8` — SHA-256 over the sorted `sha256  path` manifest of all 1224 files **other than this handover**. Self-contained, and reproducible from the extracted tree with the command in §5.0 |
| **File count**                   | **1225** (unchanged — the correction adds and deletes no file)                                        |
| **Source archive filename**      | `EPD2_PACK-16B_..._SPEC_ADR_FINAL_CORRECTED_CANDIDATE.zip`                                            |
| **Source archive SHA-256**       | `8e7207bfc8ce845f843ab8141b22f3b36d375ee1384f89467ec33ddb3da33a2e` — the BSI-verified candidate, **verified before use.** Lineage only |
| **Preceding lineage**            | `2a4f6b8bcb7b65f61cdf1dc1cc0ef0944d98cf625a7ec4ac57c78099784d0ac7` |
| **Preceding SHA-256**            | `e32a8df7bf52446436996d0dba6cfaf5b9db706313fbf27365be0ae629152379` — lineage only |
| **Previous corrected SHA-256**   | `c464921e5ed99641cdb3069d3d8165c71203ed26f93ff51c993904b0aac86777` — lineage only                     |
| **First candidate SHA-256**      | `6ba2ef239f6548542ed8b9b5d48e819a912d3e0d22678da9844052d02d56fbb7` — lineage only                     |
| **Source archive file count**    | 1225                                                                                                  |
| **Baseline (PACK-16A)**          | `EPD2_PACK-16A_VERIFIABLE_VOTING_PROTOCOL_AND_BALLOT_MODEL_SPEC_ADR_CORRECTED_CANDIDATE.zip`          |
| **Baseline SHA-256**             | `14b65dae696eeb80e237fbb33a14f7bad55e8ca043672ba0fa2e86a90b011f9e`                                    |
| **Baseline file count**          | 1195                                                                                                  |
| **Repository roots**             | 1                                                                                                     |
| **`uv.lock` copies**             | 1                                                                                                     |
| **`package-lock.json` copies**   | 1                                                                                                     |
| **Master Register copies**       | 1, at `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`                                    |
| **Evidence registries (PACK-16B)** | 1, at `docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`                                     |
| **Duplicate archive paths**      | 0                                                                                                     |
| **Nested ZIP files**             | 0                                                                                                     |
| **Private-key-like artefacts**   | 0                                                                                                     |
| **Stale repository copies**      | 0                                                                                                     |
| **Build outputs**                | 0                                                                                                     |

---

## 2. Exact diff

### 2.-4 Against the BSI-verified candidate — the ownership and wording correction

```text
ADDED      0 files
MODIFIED   8 files
DELETED    0 files
```

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16B-HANDOVER.md
```

Each of these carried either the stale `reviewer-attested` wording, the
`VO-08` ownership, or the unqualified blocking statement.
**`PACK-16B-PARAMETER-SET-SPECIFICATION.md` was checked and not changed** —
it references neither. **`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
is byte-identical** — it contains no `VO-08` ownership statement.

### 2.-3 Against the reviewer-attested candidate — the manual primary-source BSI reading

```text
ADDED      0 files
MODIFIED   8 files
DELETED    0 files
```

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16B-HANDOVER.md
```

**`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is
byte-identical.** `PACK-16B-PARAMETER-SET-SPECIFICATION.md` and
`PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` were checked and
not changed.

### 2.-2 Against the final corrected candidate — the earlier attested round

```text
ADDED      0 files
MODIFIED   8 files
DELETED    0 files
```

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16B-HANDOVER.md
```

**`PACK-16B-PARAMETER-SET-SPECIFICATION.md` and
`PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` were checked and
not changed** — neither carries a claim that the current BSI document was
unread, and `TV-08` / `TV-11` / `TV-19` are unchanged and still unresolved.
**`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is
byte-identical** to the source archive.

### 2.-1 Against the corrected candidate — the final BSI evidence round

```text
ADDED      0 files
MODIFIED   8 files
DELETED    0 files
```

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16B-HANDOVER.md
```

**`PACK-16B-PARAMETER-SET-SPECIFICATION.md` was checked and not changed** —
it carries no current-BSI availability claim and no affected status.
**`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is
byte-identical** to the source archive: it contains no current-BSI claim, so
it was not touched. `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md`
was checked and not changed — its `TV-08`/`TV-11`/`TV-19` obligations were
already correct and remain unresolved.

### 2.0 Against the first PACK-16B candidate — the narrow correction

```text
ADDED      0 files
MODIFIED  12 files
DELETED    0 files
```

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
docs/packs/PACK-16/PACK-16B-PARAMETER-SET-SPECIFICATION.md
docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16B-HANDOVER.md
docs/packs/PACK-16/PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md   ← TV-19…TV-22, defect 3 wording
docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md                          ← §6 blocked-items table
docs/packs/PACK-16/PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md                   ← defect 3 wording only
docs/packs/PACK-16/PACK-16B-SCOPE-AND-BOUNDARY.md                           ← defect 3 wording only
```

**Four files beyond the audit's expected list of seven were changed, and
each is explained here:**

| File                          | Why                                                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------- |
| `...-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | Listed by the audit as *possibly* affected. It carried the absolute negative claim (§0, §5) and is where `TV-19`…`TV-22` belong |
| `...-FIR-COVERAGE-MATRIX.md`  | Listed by the audit as *possibly* affected. §6 named `OD-P16B-01` / `VO-01` as blocked; leaving it would contradict the corrected state |
| `...-REMOTE-CEREMONY-ASSESSMENT.md` and `...-SCOPE-AND-BOUNDARY.md` | **Not on the audit's list.** Both restated the absolute negative claim verbatim. Defect 3 cannot be corrected while two documents still assert it, so the wording — and only the wording — was corrected in both. **The remote-ceremony decision itself is unchanged: fully remote remains PROHIBITED** |

**`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is
byte-identical to the source candidate.** It contained none of the four
defects, so it was not touched.

### 2.1 Against the corrected PACK-16A candidate — the whole round

```text
ADDED     30 files
MODIFIED   1 file
DELETED    0 files
```

### 2.2 Added — 29 documents under `docs/packs/PACK-16/`

```text
PACK-16B-SCOPE-AND-BOUNDARY.md
PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md
PACK-16B-PARAMETER-SET-SPECIFICATION.md
PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md
PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md
PACK-16B-RANDOMNESS-ARCHITECTURE.md
PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md
PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md
PACK-16B-GUARDIAN-LIFECYCLE.md
PACK-16B-KEY-CEREMONY-SPECIFICATION.md
PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md
PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md
PACK-16B-KEY-CUSTODY-REQUIREMENTS.md
PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md
PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md
PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md
PACK-16B-ROLE-SEPARATION-MATRIX.md
PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md
PACK-16B-REASON-CODE-SPECIFICATION.md
PACK-16B-FAILURE-AND-ABORT-MATRIX.md
PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md
PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md
PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
PACK-16B-OPEN-DECISIONS.md
PACK-16B-FIR-COVERAGE-MATRIX.md
PACK-16B-CANON-ASSESSMENT.md
PACK-16B-ACCEPTANCE-MATRIX.md
PACK-16B-SPECIFICATION-REPORT.md
PACK-16B-HANDOVER.md
```

**and one ADR**

```text
docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md
```

### 2.3 Modified — one file, additively

```text
docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md
```

Two additions, no removals:

1. **§1.21 Round record — PACK-16B specification and ADR (2026-08-01)**,
   inserted immediately before `# 2. Current confirmed baseline`.
2. **A cross-reference paragraph under `FIR-ROADMAP-006`**, pointing at
   §1.21 and restating that the status stays `approved` and the target
   version stays `0.16.0`.

**No entry was deleted, no identifier reused, no status changed, no status
downgraded, and no second register created.** §1.20 — PACK-16A's round
record — is byte-identical.

### 2.4 Everything else

**Byte-identical to the corrected PACK-16A candidate**, verified by
`diff -rq`. No PACK-16A document was edited by this round, including
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` and
`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md`, whose `KC-11` this round
corrects **by record in a PACK-16B document**, not by amendment.

---

## 3. Selected parameter profile

```text
EPD2-CRYPTO-1

  Construction        exponential ElGamal over a prime-order subgroup of Z_p*
  p                   4096 bits, fixed                                    [F-02]
  q                   2^256 − 189, fixed                                  [F-01]
  r                   (p − 1)/q, r/2 prime                                [F-02]
  g                   2^r mod p                                           [F-02]
  H                   HMAC-SHA-256 as a random oracle                     [F-06]
  H_q                 H(...) mod q — valid only for this q                [F-07]
  KDF                 SP 800-108r1 counter-mode HMAC                      [F-10]
  Encoding            fixed-length big-endian 512 / 32 / 4, no separators [F-09]
  Specification pin   SHA-256 a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936

  deprecation_date    2030-12-31 (high assurance) / 2031-12-31
  prohibition_date    2032-12-31
```

**Option A — adopted unmodified.** Options B (different finite-field
parameters), C (elliptic curves) and D (post-quantum) are rejected with
reasons in `PACK-16B-PARAMETER-SET-SPECIFICATION.md` §2. The decisive fact
is that the specification **fixes** its parameters `[F-04]` and a conforming
verifier requires **bit-equality** `[F-05]`, which makes B and C
verifier-forking protocol adaptations rather than parameter choices.

**Parameter provenance was independently regenerated** and confirmed byte
for byte, with `(p−1) mod q = 0`, `g^q mod p = 1` and the required
primalities `[F-03]`. `TV-01` makes this a standing acceptance test.

---

## 4. Verdicts

### 4.1 ElectionGuard compatibility

```text
EXPECTED SPECIFICATION COMPATIBILITY,
CONDITIONAL ON INDEPENDENT VERIFIER TESTING.
```

**No known verifier-consumed ElectionGuard 2.1 field is changed by the
PACK-16B orchestration profile.** Full interoperability with independent
conforming verifiers **has not yet been demonstrated**, and
`TV-07`/`TV-19` — independent implementation and independent conforming-
verifier interoperability testing — **remain mandatory before implementation
acceptance**. `TV-11` is unchanged and still binds the scope of any review.

EPD² adds a complaint protocol and a pre-publication commitment round, both
**at the orchestration layer**: no hash input, no challenge, no proof and no
verifier-consumed field changes. EPD²'s own hash domain uses string tags so
that no upstream tag byte is squatted.

### 4.2 BSI compatibility

```text
CURRENT BSI SUBGROUP-ORDER CHECK: SATISFIED — 256 >= 250
  TR-02102-1 (2026-01) §2.3.3 p. 34 and §2.3.5 p. 36, read first-hand [F-36]
NOT CERTIFIED. COMPLETE BSI CONFORMITY NEITHER ESTABLISHED NOR CLAIMED.
```

`p = 4096` against a stated minimum of 3000; `ord(g)` prime as §2.3.5
requires; SHA-256 / HMAC-SHA-256 against a 128-bit minimum; `|q| = 256`
against the stated 250 — see §0.5 for the verbatim wording and the
comparison.

**One recommendation-level divergence is declared:** Remark 2.12 (p. 34)
prefers MODP or ffdhe published-parameter groups, and `EPD2-CRYPTO-1` uses
neither. Carried as `VO-08` — owned by the **PACK-16B external
cryptographic review** with independent confirmation in **PACK-17**, and
**blocking for production and legal activation** though not for this
specification round or for PACK-16C drafting (§0.6). `VO-02` and `VO-03`
remain open and also block activation.

**No BSI certification or conformance assessment is claimed. A technical
guideline is not a legal requirement, and alignment with it is diligence,
not compliance.**

### 4.3 Guardian count and quorum

```text
DEFAULT           k = 3 of n = 5      absence tolerance 2
HIGH ASSURANCE    k = 4 of n = 7      absence tolerance 3
PERMITTED         k = 5 of n = 9
PROHIBITED        k = 2 of n = 3
BOUNDS            k >= 3 always; 5 <= n <= 9; n >= k + 2
                  k MAY NEVER BE REDUCED, by any authority, for any reason
```

At most `k − 1` guardians may be Election Officers or Board members in
total, so **any collusion reaching `k` must include someone outside EPD²'s
own operations.**

### 4.4 Remote ceremony

```text
FULLY IN-PERSON     permitted
CONTROLLED HYBRID   permitted — the expected form
FULLY REMOTE        PROHIBITED
```

Prohibited because the evidence to permit it does not exist — decisively,
because **no peer-reviewed analysis of this specification's key ceremony was
located by this round's survey** `[F-31]`, which is not proof that none
exists. Four conditions that would change the
answer are written down and carried as `OD-P16B-05`.

### 4.5 Backup and recovery

```text
PERMITTED    one encrypted backup, of a guardian's OWN share,
             in that guardian's OWN sole custody, second dedicated medium
PROHIBITED   split custody · hardware duplication · escrow · central backup ·
             cloud backup · shared passphrase · vendor master key ·
             any "sealed envelope in a safe"
NO BACKUP IS MANDATORY, and its absence is not a defect.
```

The backup does not change the threshold: one share backed up is still one
share, so the number of parties who must collude to reach `k` is unchanged.

### 4.6 Compensated decryption

```text
IT DOES NOT EXIST IN THE PINNED SPECIFICATION VERSION.
```

The word does not appear in 2.1; the mechanism belonged to the 1.x lineage
`[F-11]`. Version 2.1 computes partial decryptions over the available set
and **explicitly refuses** to reconstruct an absent guardian's secret — the
same policy `KC-15` states, reached independently by the specification's
authors.

**This is a factual correction to PACK-16A `KC-11`'s described mechanism.
The requirement is unchanged.** No compensation material is created, stored
or permitted; absence tolerance is exactly `n − k`.

---

## 5. Local verification

### 5.0 The corrected archive's digest, and why it is where it is

```text
Final archive filename
  EPD2_PACK-16B_CRYPTOGRAPHIC_PARAMETERS_KEY_CEREMONY_AND_TRUSTEE_ARCHITECTURE_SPEC_ADR_FINAL_REVIEW_CANDIDATE.zip

Final archive file count
  1225

Final physical ZIP SHA-256
  PUBLISHED EXTERNALLY WITH DELIVERY

Source archive (lineage only, NOT this archive's digest)
  EPD2_PACK-16B_..._SPEC_ADR_BSI_VERIFIED_CANDIDATE.zip
  8e7207bfc8ce845f843ab8141b22f3b36d375ee1384f89467ec33ddb3da33a2e

Earlier lineage
  2a4f6b8bcb7b65f61cdf1dc1cc0ef0944d98cf625a7ec4ac57c78099784d0ac7
  e32a8df7bf52446436996d0dba6cfaf5b9db706313fbf27365be0ae629152379
  c464921e5ed99641cdb3069d3d8165c71203ed26f93ff51c993904b0aac86777
  6ba2ef239f6548542ed8b9b5d48e819a912d3e0d22678da9844052d02d56fbb7
```

**The corrected archive's own SHA-256 cannot be written inside the corrected
archive.** Writing it into this file changes this file, which changes the
archive, which changes the digest; the fixed point does not exist. Stating a
digest here that did not match the delivered file would be exactly the kind
of false verification result this project forbids.

**What is done instead, and it is checkable:**

1. **The archive SHA-256 is published with the delivery message**, and the
   recipient reproduces it directly:

   ```text
   sha256sum EPD2_PACK-16B_..._SPEC_ADR_FINAL_REVIEW_CANDIDATE.zip
   ```

2. **A content digest that *can* live inside the archive is recorded above**
   — SHA-256 over the sorted `sha256  path` manifest of every file in the
   corrected tree **except this handover**. It fixes the content of all
   1224 other files, including every corrected document, and is reproduced
   from the extracted tree with:

   ```text
   find . -type f ! -path ./docs/packs/PACK-16/PACK-16B-HANDOVER.md \
     -exec sha256sum {} + | sed 's| \./| |' | sort | sha256sum
   ```

   Any change to any corrected document changes this value.

3. **The source candidate's digest is recorded separately and labelled as
   lineage**, so the two can never be confused.

### 5.1 Scripts run against this tree — output verbatim

```text
$ python3 scripts/check_repository.py
OK: all 983 required paths are present.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 18 canon 0.8.0 amendment checks passed.

$ python3 scripts/check_forbidden_files.py
WARNING: repository root is not a git repository; falling back to a full
filesystem walk (local build caches may be flagged).
OK: no forbidden paths found.
```

The `check_forbidden_files.py` warning is expected: the working tree is an
extracted archive rather than a git clone, so the script walks the
filesystem instead of asking git. The result — no forbidden paths — is the
same either way.

### 5.2 Structural checks

| Check                                                | Result                                                  |
| ---------------------------------------------------- | --------------------------------------------------------- |
| All required documents present                       | **PASS** — 29 of 29                                      |
| `ADR-100` at the required path                       | **PASS**                                                 |
| `ADR-100` status                                     | **PASS** — `proposed`                                    |
| One Master Register                                  | **PASS**                                                 |
| Prior Master Register content preserved              | **PASS** — additive only; §1.20 byte-identical           |
| Versions unchanged                                   | **PASS** — `0.15.0`, `0.8.0`                             |
| Source changes                                       | **0**                                                    |
| Test changes                                         | **0**                                                    |
| Migration changes                                    | **0**                                                    |
| CI changes                                           | **0**                                                    |
| Lock-file changes                                    | **0**                                                    |
| One PACK-16B evidence registry                       | **PASS** — 1                                             |
| Unresolved evidence references                       | **0** — every `[F-nn]` referenced is defined              |
| Evidence entries defined                             | **35** — `F-01`…`F-35`                                   |
| Evidence sequence gaps                               | **0** — contiguous                                       |
| Conflicting evidence definitions                     | **0**                                                    |
| Cross-pack references (`E-nn`, `KC-*`, `BM-*`, …)    | **0 unresolved** — all checked against PACK-16A in this tree |
| Acceptance-matrix arithmetic                         | **PASS** — see §5.3                                      |
| Duplicate requirement IDs                            | **0**                                                    |
| Duplicate reason codes                               | **0**                                                    |
| Reason codes used but undefined                      | **0**                                                    |

### 5.3 Acceptance-matrix arithmetic, computed from the rows

```text
Requirement rows                    129     (AC-P16B-001 … AC-P16B-129)

SATISFIED                           114
PARTIALLY SATISFIED                   8
DEFERRED                              4
BLOCKED                               1
NOT APPLICABLE                        1
CORRECTED                             1
                                    ---
sum(status counts)                  129

sum(status counts) == requirement rows      129 == 129    PASS
Distinct requirement IDs                    129           PASS
Duplicate requirement IDs                     0           PASS
```

### 5.4 Reason codes

```text
Namespaces required by the round task     20    all present
Namespaces declared in addition            2    crypto.*, ballot.*
Namespaces defined                        22
Codes defined                            129
Duplicate code identifiers                 0
Codes used elsewhere but undefined         0
```

### 5.5 Parameter-set and architectural invariants

| Invariant                                            | Covered | Where                                                    |
| ---------------------------------------------------- | ------- | ---------------------------------------------------------- |
| Parameter-set identity, lifecycle and authority      | **yes** | `PSS` §3                                                  |
| Downgrade prohibited architecturally                 | **yes** | `PSS` §5, `FM-16B-34`                                     |
| Guardian/quorum decision explicit                    | **yes** | `GQM` §2, §3                                              |
| **No hidden master key**                             | **yes** | `BR-09`…`BR-12`, `FM-16B-22`                              |
| **No single-admin decryption**                       | **yes** | `GQ-13`, `RS-16B-13`, `KU-17`…`KU-20`                     |
| **No break-glass decryption**                        | **yes** | `CQL` §6, `RS-16B-11`                                     |
| **No pre-closure decryption**                        | **yes** | `CM-20`…`CM-23`, `FM-16B-25`                              |
| **No compensation material**                         | **yes** | `BR-13`, `IN-32`, `RN-C11`                                |
| **No guardian secret in a browser**                  | **yes** | `IM-28`…`IM-32`                                           |
| No false implementation claims                       | **yes** | every document header; `RN-C09`                            |
| No false certification claims                        | **yes** | `CPA` §3; §4.2 above                                       |

### 5.5a Correction-specific verification

```text
FULL interoperability claims                     0
"Every conforming verifier accepts" claims       0
Universal "no study exists" claims               0
Absence-of-evidence qualification present        yes  (F-31, TVR §0, RCA §4,
                                                       SCOPE, ACC §4, SPEC-REPORT)
TV-07 / TV-11 / TV-19 resolved                   no — all remain mandatory
External cryptographic review closed             no
Formal-proof obligation closed                   no
Implementation-library evaluation closed         no
Side-channel assessment closed                   no
Certification assessment closed                  no
BSI certification claimed                        no

BSI TR-02102-1 2026-01 opened and read           YES — supplied locally
Version 2026-01 confirmed on the title page      YES
Date 23 January 2026 confirmed                   YES
Exact sections recorded                          §2.3.3 and §2.3.5
Exact pages recorded                             PDF 34 / 36; printed 34 / 36
Exact applicable wording recorded                YES — verbatim, §0.5
q = 256 compared with the current minimum        YES — 256 >= 250, SATISFIED
Scope limited to subgroup-order dimension        YES
Certification claimed                            NO
Section/table/page recorded for sources that
   WERE read first-hand                          yes  (F-33 §4.2; F-34 §3.2 /
                                                  Table 2, pp. 9-10; F-35
                                                  Table 1.2, p. 20)
256-bit q comparison explicit                    yes  (CPA §3.2, ADR-100, §0.3)
Scope limitation explicit                        yes  (identical wording in
                                                       CPA, ADR-100, OD, handover)
OD-P16B-01 status                                CLOSED (read first-hand)
VO-01 / VO-06 / VO-07 status                     SATISFIED
VO-08 owner                                      PACK-16B external crypto
                                                 review; PACK-17 assurance
VO-08 owner = PACK-16C                           0
VO-08 blocks production/legal activation         yes
VO-08 blocks PACK-16C specification drafting     no
Claims that the current BSI doc was unread       0
ARCHITECTURAL BLOCKER raised                     no — 256 >= 250
PDF included in the archive                      no — 0 PDFs of any kind

Final archive filename present                   yes  (§1)
Final archive file count present                 yes  (§1)
Final archive SHA-256                            published with delivery (§5.0)
Source archive digest kept separate              yes  (§1, labelled lineage)
Acceptance-matrix status changes                 0  (wording only)
CORRECTED used as a final status                 0
Master Register changes                          0 — byte-identical
```

### 5.6 What was not verified

```text
PARTIAL LOCAL VERIFICATION ONLY.
EXTERNAL ARCHITECTURAL REVIEW REQUIRED.
EXTERNAL CRYPTOGRAPHIC REVIEW REQUIRED BEFORE ANY ACTIVATION.

No CI was run.               No test was executed.
No build was produced.       No implementation exists to test.
No cryptographic review has been obtained.
No BSI or legal assessment has been obtained.
```

**No verification result in this document is fabricated.** Every figure
above was computed from this tree, and every script output is quoted as it
was produced.

---

## 6. Canon assessment

```text
CANON CLARIFICATION REQUIRED
CANON_VERSION REMAINS 0.8.0 — canon files untouched
NO AMENDMENT PROPOSED
```

Five clarifications, `CQ-P16B-01`…`CQ-P16B-05`. The ceremony transcript is
**not** a canonical aggregate and **not** a `PublicLedgerEntry`; the
`PublicLedgerEntry → VoteEnvelope` prohibition stands untouched. Three
amendment candidates are recorded (`CAM-P16B-01`…`03`), and **PACK-16A's
`CA-02` is narrowed rather than discharged** — this round's finding is that
the right amendment is smaller than the one PACK-16A anticipated.

---

## 7. FIR summary

```text
FIR entries marked implemented       0
FIR entries created                  0
FIR entries removed or downgraded    0
FIR statuses changed                 0
FIR entries specified                24
FIR entries deferred                 5
Register copies                      1
```

`FIR-ROADMAP-006` stays `approved`, target `0.16.0`. `FIR-INV-002` remains
**partially addressed and future** and **cannot be closed by this round**.
`FIR-UX-011`, `FIR-OSS-001`…`006`, `FIR-INV-002`, `FIR-INV-008`,
`FIR-INV-015` and `FIR-ROADMAP-006` are preserved unchanged.

---

## 8. Open decisions

**Closed**

```text
OD-P16B-01   the current-edition BSI subgroup-order check —
             CLOSED BY PRIMARY-SOURCE EVIDENCE, READ FIRST-HAND
             (256 >= 250; §2.3.3 p. 34 and §2.3.5 p. 36)
OD-P16A-03   parameters against German guidance — CLOSED
OD-P16A-05   specification stewardship — CLOSED
OD-P15-05    cryptographic boundary CLOSED (IS-01…IS-06);
             the construction question REASSIGNED to PACK-16C
```

**Open**

```text
OD-P16B-02   whether EPD² may write its own impl.     blocks implementation
OD-P16B-03   the Cryptographic Reviewer's standing
OD-P16B-04   publicly checkable share correctness
OD-P16B-05   remote ceremony
OD-P16B-06   the post-quantum successor    BLOCKS NEW CONTEXTS AFTER 2030-12-31
```

**Contributed to, not closed:** `OD-P16A-04`, `OD-P16A-06`, `OD-P16A-07`,
`OD-P16A-08`, `OD-P16A-11`, `OD-P16A-12`.

```text
THREE INDEPENDENT ACTIVATION BLOCKS REMAIN OPEN — OD-P16A-04,
OD-P16A-06 AND OD-P16A-11 — PLUS THE DATED OD-P16B-06 AND THE
OPEN VALIDATION OBLIGATIONS VO-02 … VO-05.
NONE IS CLOSED BY ASSERTION. OD-P16B-01 WAS CLOSED ONCE ON
SUBSTITUTE SOURCES, WITHDRAWN, CLOSED AGAIN ON AN ATTESTATION,
AND FINALLY CLOSED ON THE DOCUMENT ITSELF, READ FIRST-HAND.

NOT CLOSED, AND NOT NARROWED, BY THE CORRECTION ROUND:
  independent verifier testing        TV-07, TV-19
  external cryptographic review       TV-08 / OD-P16A-06
  formal-proof obligations            TV-08, §3 assurance mapping
  implementation-library evaluation   OD-P16A-04, IM-01…IM-48
  BSI certification                   NOT CLAIMED, NOT SOUGHT, NOT OBTAINED
  full ElectionGuard interoperability NOT CLAIMED
```

---

## 9. Residual risks

| Rank | Risk                                                                          | Rating   | Carried by                 |
| ---- | ----------------------------------------------------------------------------- | -------- | -------------------------- |
| 1    | **No peer-reviewed analysis of the key ceremony was located** `[F-31]`        | **high** | `TV-08`, `OD-P16A-06`      |
| 2    | **No production-grade implementation of the pinned version exists**           | **high** | `OD-P16A-04`, `OD-P16B-02` |
| 3    | Classical-cryptography recommendation lapses end-2031 / end-2030 `[F-25]`     | **high** | `OD-P16B-06`, `CA-08`      |
| 4    | Upstream has no errata process; two versions marked "Recommended" `[F-30]`    | medium   | `CA-19`…`CA-27`            |
| 5    | A weak or duplicated nonce in a browser is silent and undetectable            | medium   | `RB-08`, `IM-43`           |
| 6    | Independence declarations are self-reported                                   | medium   | `GI-*`, governance         |
| 7    | Two specification inconsistencies resolved on EPD²'s own reading `[F-19]`     | medium   | `DS-16`, `CA-27`           |
| 8    | Guardian volunteers bear real personal exposure through publication           | medium   | governance                 |
| 9    | **Published parameter family normative divergence** — Remark 2.12 (p. 34) prefers MODP or ffdhe groups; `EPD2-CRYPTO-1` uses neither, though every numerical condition is met `[F-36]`. **Not a claim of insecurity.** Blocks production and legal activation | medium   | `VO-08` — external crypto review, PACK-17 |
| —    | A quorum loss makes a result genuinely unobtainable                           | accepted | `CM-14`…`CM-19`            |

---

## 10. Known limitations

```text
The guardians do not exist.
The ceremony has never been rehearsed.
The implementation does not exist.
The cryptographic review does not exist.
BSI TR-02102-1 (2026-01) has been read and cited exactly, but only for
   the subgroup-order dimension; VO-02, VO-03 and VO-08 remain open.
The legal Stand-der-Technik mapping has not been made.
Four grounds of the complaint model are assessed rather than arithmetic.
The commitment round is a mitigation, not a proof.
Reproducing the parameters proves provenance, not adequacy.
```

Every one of these is named, owned and dated in
`PACK-16B-OPEN-DECISIONS.md` or in the acceptance matrix's fifteen
non-`SATISFIED` rows.

---

## 11. Recommended PACK-16C scope

```text
Ballot casting and the Voting Client contract
Vote verification, confirmation codes and the Benaloh challenge flow
Bulletin-board specification, checkpoints and mirrors
The issuance construction question reassigned from OD-P15-05
OD-P16B-04 — publicly checkable share correctness
VO-02, VO-03 — the remaining first-hand BSI readings.
            VO-08 is NOT PACK-16C's: it is inherited as a constraint,
            and PACK-16C may not alter or claim approval of the
            parameter family
CAM-P16B-01 — the narrow canonical reference, if any amendment is proposed
```

**Constraints PACK-16C inherits and may not relax:** no ballot may be
encrypted before the joint key is published; no decryption operation may
exist before `voting_closed`; the bulletin board is still not a
`PublicLedgerEntry`; and no person-to-ballot link may be created,
derivable or constructible.

## 12. Recommended PACK-16D scope

```text
OD-P16A-04 decided against IM-01…IM-48, with the assessment published
OD-P16B-02 answered before the implementation track opens
TV-01…TV-07 and the fourteen vector classes delivered
Reproducible build, pinned provenance, no ceremony network access
OD-P16A-12 — the repository-compatibility bound for 0.16.0
```

---

## 13. What the recipient is asked to do

```text
1. Verify the archive SHA-256 against the digest published with delivery.
2. Review ADR-100 and PACK-16B-ACCEPTANCE-MATRIX.md first — the ADR for
   the decisions, the matrix for the fifteen rows that are NOT satisfied.
3. Check the arithmetic independently: 129 rows, 116+7+4+1+1 = 129.
4. Check that PACK-16A is byte-identical apart from the Master Register's
   two additive changes, and that the Master Register is byte-identical to
   the source archive.
4a. Read §0.5 first if you are auditing the BSI evidence. `OD-P16B-01` is
   closed on a **first-hand reading** of TR-02102-1 (2026-01): §2.3.3 p. 34
   and §2.3.5 p. 36, quoted verbatim. Note two things the reading changed —
   the minimum is **250, not 240**, and Remark 2.12 contains a
   recommendation-level divergence that is now declared as `VO-08`, owned
   by the external cryptographic review and PACK-17, blocking production and
   legal activation but not PACK-16C drafting (§0.6).
5. Decide whether the parameter profile, the guardian model and the
   ceremony form are architecturally acceptable.
6. Return a verdict. PACK-16C must not start before that verdict.
```

**Do not treat any part of this candidate as verified, certified, reviewed
or ready. It is a specification with four open activation blocks, and the
gravest of them is that nobody independent has yet examined the ceremony
this architecture depends on.**

```text
NOT A FINAL PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.
PACK-16C MUST NOT START BEFORE ACCEPTANCE.
```
