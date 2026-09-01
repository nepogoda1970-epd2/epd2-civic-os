# PACK-16B — FIR Coverage Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Assessed against the **cumulative Master Future Implementation Register**
carried in this archive at its canonical path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, which is the
only authoritative register. **No standalone register version is used and
no second register is created.**

**No FIR entry is marked `implemented` by this round, and none may be.**

Treatment values permitted for a specification stage:

```text
specified                        assessed
selected for architectural review
deferred to PACK-16C / 16D / 17
blocked pending cryptographic review
blocked pending legal assessment
unchanged
```

Treatment values **prohibited** for this round:

```text
implemented · externally verified · production ready · legally activated
```

**New FIR identifiers created by this round: none.**
**FIR identifiers removed, renamed or downgraded: none.**
**Statuses changed in the register: none.**

---

## 1. Roadmap

| FIR               | Status before | Treatment                             | References                        | Obligation that remains                                                                                                                                                                                         |
| ----------------- | ------------- | ------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-ROADMAP-005` | `approved`    | **unchanged**                         | —                                 | Untouched                                                                                                                                                                                                       |
| `FIR-ROADMAP-006` | `approved`    | **selected for architectural review** | whole pack; `ADR-100`             | **Status stays `approved`.** PACK-16B performs the parameter, ceremony and trustee stage only. Ballot casting, vote verification and tally controls remain unimplemented, and the target version stays `0.16.0` |
| `FIR-ROADMAP-007` | `approved`    | **deferred to PACK-17**               | `CQL` §5; `IN-*`; `TV-14`…`TV-18` | Ceremony resilience, incident readiness, archive re-verification operations and independent-verification operations                                                                                             |
| `FIR-ROADMAP-008` | `approved`    | **unchanged**                         | —                                 | Untouched                                                                                                                                                                                                       |
| `FIR-ROADMAP-009` | `approved`    | **unchanged**                         | —                                 | Untouched                                                                                                                                                                                                       |

**`FIR-ROADMAP-006` MUST NOT move to `implemented`, `scheduled` or any
status implying delivery on the strength of this round.**

---

## 2. Hard invariants

| FIR                                               | Status before | Treatment                                  | References                                                  | Obligation that remains                                                                                                                                           |
| ------------------------------------------------- | ------------- | ------------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-INV-001` No global user ID                   | `approved`    | **specified** for the ceremony domain      | `IN-34`; `RN-C06`; `CT-13`…`CT-17`                          | The ceremony domain references **no participant at all**; guardian identity is a published role, not a user ID                                                    |
| `FIR-INV-002` Identity/ballot unlinkability       | `approved`    | **not closed — reinforced, not advanced**  | `IS-01`…`IS-06`; `IN-34`; `RS-16B-07`, `RS-16B-08`          | **This round cannot close it and does not.** §2.1                                                                                                                 |
| `FIR-INV-003` Voting Client isolation             | `approved`    | **specified — extended categorically**     | `IM-28`…`IM-32`                                             | **No guardian secret material ever exists in a browser context.** The client's cryptographic operations must be reproducible outside the browser                  |
| `FIR-INV-004` Eligibility/credential separation   | `approved`    | **specified** for the ceremony boundary    | `RS-16B-07`, `RS-16B-08`; `IS-01`…`IS-06`                   | The Credential Authority and Eligibility Administrator are **prohibited from being guardians**                                                                    |
| `FIR-INV-005` No intermediate tally               | `approved`    | **specified — architecturally enforced**   | `CM-20`…`CM-23`; `FM-16B-25`; `RN-C12`                      | **No operation exists** that produces a decryption share before `voting_closed`; no `decryption.*` code carries a count or aggregate                              |
| `FIR-INV-006` Safe feature flags                  | `approved`    | **specified**                              | `FM-16B-24`; `RN-14`…`RN-17`; `CM-20`                       | No flag, build mode or configuration may reach a deterministic seed, a test key, a pre-closure decryption or a reduced quorum                                     |
| `FIR-INV-007` DLP and controlled export           | `approved`    | **specified** for ceremony evidence        | `IM-20`…`IM-27`; `IN-41`; `CT-13`…`CT-17`                   | No secret in logs, dumps, telemetry, exception text, URLs or the transcript; the incident channel is not a bypass                                                 |
| `FIR-INV-008` Security/System Admin separation    | `approved`    | **specified — structurally**               | `RS-16B-04`, `RS-16B-05`; `KU-08`; `GI-12`                  | Neither role is a guardian, neither administers a guardian device, and neither appears in the ceremony RACI                                                       |
| `FIR-INV-009` JIT and break-glass governance      | `approved`    | **specified — categorically**              | `CM-18`, `CM-19`; `BR-09`…`BR-12`; `FM-16B-22`; `RS-16B-13` | **No break-glass decryption exists.** The Election Board possesses nothing, and a proposal to change that is a design-review rejection                            |
| `FIR-INV-010` Document version integrity          | `approved`    | **specified** for the pinned specification | `PS-*` `specification_digest`; `CA-01`…`CA-05`              | The upstream document is pinned by SHA-256; a new digest is a new profile                                                                                         |
| `FIR-INV-011` Statistical Disclosure Control      | `approved`    | **unchanged**                              | —                                                           | No value changed; the ceremony publishes no participant-level data at all                                                                                         |
| `FIR-INV-012` Accessibility as Definition of Done | `approved`    | **specified** for the ceremony             | `KY-34`…`KY-43`; `RCA` §7                                   | Venue accessibility is a selection criterion; assistance never touches secret material; a guardian set that cannot be assembled accessibly has not been assembled |
| `FIR-INV-013` Bund/Land/Kreis isolation           | `approved`    | **specified** — keys are per context       | `GQ-08`, `GQ-09`; `KU-16`                                   | Keys are not reused across contexts even where the specification would permit it                                                                                  |
| `FIR-INV-014` No universal administration         | `approved`    | **specified — extended to the key domain** | `RS-16B-03`…`RS-16B-13`; `KU-17`…`KU-20`; `GI-15`           | **An HSM does not convert one administrator into a threshold.** If one party can assemble `k` shares, the architecture fails                                      |
| `FIR-INV-015` No false production claims          | `approved`    | **specified and enforced**                 | `RN-C09`; every document header; `TV-09`, `TV-13`           | A missing review is published as missing; no code may assert a prohibited claim; no upstream gap is described as closed by an EPD² document                       |

### 2.1 `FIR-INV-002` — why this round moves it no further

PACK-15 closed `identity → credential`. PACK-16A **specified** the
architecture of `credential → ballot`. PACK-16B touches neither half: it
specifies the key material that makes decryption possible and the boundary
that keeps decryption away from anyone who knows who voted.

```text
What this round adds:      guardians are structurally separated from
                           eligibility, issuance and casting (RS-16B-06…09)
What this round does not:  demonstrate the "cannot be paired" property
What this round cannot:    close an invariant that needs a built system
```

`FIR-INV-002` stays **partially addressed and future**, exactly as PACK-15
and PACK-16A left it.

---

## 3. Roles

| FIR                                                      | Status before | Treatment                    | References                                          | Obligation that remains                                                                                |
| -------------------------------------------------------- | ------------- | ---------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `FIR-ROLE-001` DPO                                       | `approved`    | **specified**                | `IN-14`, `IN-15` notification lists                 | The DPO is notified of compromise events and holds no ceremony capability                              |
| `FIR-ROLE-002` Election board/officer                    | `approved`    | **specified — bounded**      | `RS-16B-12`, `RS-16B-13`; `GQ-11`…`GQ-13`           | The Board decides and possesses nothing; the Officer cannot lower a quorum                             |
| `FIR-ROLE-003` Independent auditor                       | `approved`    | **specified — strengthened** | `RS-16B-10`; `FM-16B-18`; RACI phases 8, 14, 16, 17 | The Auditor is **accountable** for proof verification and joint-key formation, and cannot be overruled |
| `FIR-ROLE-004` Finance auditor                           | `approved`    | **unchanged**                | —                                                   | Untouched                                                                                              |
| `FIR-ROLE-005` Election Administration Separation Matrix | `approved`    | **specified — extended**     | `PACK-16B-ROLE-SEPARATION-MATRIX.md`                | Two roles added (`R-17`, `R-18`); three PACK-16A cells tightened; a 20-phase RACI added                |
| `FIR-ROLE-006` Finance separation                        | `approved`    | **unchanged**                | —                                                   | Untouched                                                                                              |

---

## 4. Entries this round engages without closing

| FIR                                                     | Treatment                                                     | Why it is engaged                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-TRUST-001` Signature, seal and timestamp framework | **specified, partially — deferred to PACK-16D**               | PACK-16A deferred this to PACK-16B. This round specifies **what must be signed** (complaints `CD-02`, checkpoints, the Auditor's verdict, destruction attestations) and **what must not be relied on as a signature** (`F-13`, `F-14` — guardian share authenticity is record comparison, not signed identity). The framework itself remains PACK-16D's |
| `FIR-SEC-001` Security incident and breach response     | **specified, partially — deferred to PACK-17**                | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` fixes nineteen events, their notification classes, timing and responsible actors. Runbooks and rehearsal remain PACK-17's                                                                                                                                                                                 |
| `FIR-SEC-002` Backup verification and recovery testing  | **specified — the boundary, not the testing**                 | `BR-01`…`BR-16` fix what a backup may be. Verification and rehearsal of recovery are PACK-17's, and `CM-24`, `CM-25` bound how a readiness check may be run                                                                                                                                                                                             |
| `FIR-OSS-006` Open verification, reproducible builds    | **specified — criteria fixed, delivery deferred to PACK-16D** | `IM-33`…`IM-38` make reproducible build and dependency provenance **mandatory pass/fail criteria**; `IM-31` requires a non-browser independent verifier                                                                                                                                                                                                 |
| `FIR-CONFIG-001` Governed operational configuration     | **specified**                                                 | The parameter set, `k`, `n`, guardian set, custody classes and ceremony form are governed configuration, frozen before `issuance_open` and immutable thereafter                                                                                                                                                                                         |
| `FIR-COMM-002` Neutral sensitive notifications          | **specified**                                                 | `IN-31` — suspicion notifications state a class and do not characterise a person; `IN-30` requires withdrawal to be as prominent                                                                                                                                                                                                                        |
| `FIR-DELIVERY-001` Official delivery and receipt        | **specified, partially**                                      | `IN-25`…`IN-29` — out-of-band notification is registered, tested in advance, and logged as sent with receipt recorded separately and permitted to be unknown                                                                                                                                                                                            |
| `FIR-QUALITY-001` Data quality and discrepancy handling | **specified, partially**                                      | `FM-16B-16` split view, `FM-16B-17` joint-key mismatch, `FM-16B-33` archive verification failure — each published, none quietly repaired                                                                                                                                                                                                                |
| `FIR-DATA-003` Legal Hold                               | **assessed**                                                  | A legal hold may not extend the life of secret material, compel a guardian, or produce a decryption. `IN-28` handles the one case where a legal authority may require non-notification, and requires the requirement itself to be published when it lapses                                                                                              |
| `FIR-GOV-001` Emergency governance                      | **specified — bounded**                                       | `FM-16B-00`: no condition has "governance decides" as its outcome. Three conditions have bounded choices, eight permitted outcomes, all named                                                                                                                                                                                                           |
| `FIR-INCLUSION-001` Assisted and alternative channels   | **specified** for the ceremony                                | `KY-39`…`KY-41` — assistance never touches secret material, dual control where it approaches it, the assistant named as an assistant                                                                                                                                                                                                                    |
| `FIR-METRIC-002` Count, facet and small-cohort controls | **unchanged**                                                 | The ceremony produces no counts                                                                                                                                                                                                                                                                                                                         |
| `FIR-CAND-001` Candidacy & Nomination                   | **unchanged**                                                 | Untouched; `GQ-07` merely restates that a candidate holds no role in their own context                                                                                                                                                                                                                                                                  |
| `FIR-ASM-006`, `FIR-ASM-007`                            | **unchanged — remain deferred to PACK-16C**                   | Untouched by this round                                                                                                                                                                                                                                                                                                                                 |
| `FIR-PROG-001` Program formation lifecycle              | **unchanged**                                                 | Untouched                                                                                                                                                                                                                                                                                                                                               |

---

## 5. Entries preserved and explicitly untouched

**Required by the round definition to be preserved. Verified present and
unmodified in the register carried in this archive.**

| FIR               | Title                                                              | State                                                  |
| ----------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| `FIR-UX-011`      | Page Specification and Screen Content Governance                   | **preserved, unchanged**                               |
| `FIR-OSS-001`     | EUPL-1.2 Project Licensing Baseline                                | **preserved, unchanged**                               |
| `FIR-OSS-002`     | Source Availability for Network-Provided Modified Versions         | **preserved, unchanged**                               |
| `FIR-OSS-003`     | Third-Party Licence and Dependency Compliance                      | **preserved, unchanged**                               |
| `FIR-OSS-004`     | Contribution, Copyright and Provenance Governance                  | **preserved, unchanged**                               |
| `FIR-OSS-005`     | Trademark, Name and Official Instance Separation                   | **preserved, unchanged**                               |
| `FIR-OSS-006`     | Open Verification, Reproducible Builds and Public Security Process | **preserved, unchanged** — engaged in §4, not modified |
| `FIR-INV-002`     | Identity/ballot unlinkability                                      | **preserved, unchanged**                               |
| `FIR-INV-008`     | Security/System Administrator separation                           | **preserved, unchanged**                               |
| `FIR-INV-015`     | No false production claims                                         | **preserved, unchanged**                               |
| `FIR-ROADMAP-006` | Voting and Elections                                               | **preserved, unchanged**                               |

### 5.1 A licensing note that is not a change

The pinned artefact is a **specification document**, and this round creates
**no code dependency of any licence**. `OD-P16A-08` is unchanged and
unanswered, and no `FIR-OSS-*` compliance is claimed.

---

## 6. Statuses that are `blocked`, and why that is the honest value

| FIR / obligation       | Blocked value                                        | Blocking artefact                                                                                                                                                                                                                               |
| ---------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P16A-06` / `TV-08` | **blocked pending cryptographic review**             | An external review that has not been obtained, and none was located `[F-31]`                                                                                                                                                                    |
| `VO-02`, `VO-03`       | **blocked pending source verification**              | BSI AIS 20/31 class and hash/MAC tables not yet read first-hand. **`OD-P16B-01`, `VO-01`, `VO-06` and `VO-07` are closed** on a first-hand reading of the named edition `[F-36]`                                                                |
| `TV-07` / `TV-19`      | **blocked pending independent verifier testing**     | Interoperability is expected and **not demonstrated**                                                                                                                                                                                           |
| `VO-08`                | **blocked pending independent cryptographic review** | The published parameter family diverges from Remark 2.12's preference. Owner: **PACK-16B external cryptographic review**, confirmed by **PACK-17** — **not PACK-16C**. Blocks production and legal activation; does not block PACK-16C drafting |
| `OD-P16A-11`           | **blocked pending legal assessment**                 | § 15 Abs. 2a PartG mapping                                                                                                                                                                                                                      |

**Five blocked items, none of them dressed as progress.** One former blocker
— the subgroup-order check — was closed, withdrawn, closed again on an
attestation, and finally closed on a first-hand reading of the document it
names. The reading corrected the figure from 240 to **250** and surfaced one
recommendation-level divergence (`VO-08`), which is recorded rather than
absorbed.

---

## 7. Summary

| Measure                                     | Value                                    |
| ------------------------------------------- | ---------------------------------------- |
| FIR entries assessed                        | all entries in the canonical register    |
| FIR entries **specified** by this round     | 24                                       |
| FIR entries **deferred** with a named owner | 5                                        |
| FIR entries **blocked**                     | 0 entries; 3 obligations (§6)            |
| FIR entries **unchanged**                   | all others                               |
| FIR entries marked `implemented`            | **0**                                    |
| FIR entries created                         | **0**                                    |
| FIR entries removed, renamed or downgraded  | **0**                                    |
| FIR **statuses changed** in the register    | **0**                                    |
| Register copies in the archive              | **1**, at the canonical path             |
| `FIR-INV-002` closed                        | **no — and it cannot be, by this round** |

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
