# PACK-16A — FIR Coverage Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Assessed against the **cumulative Master Future Implementation Register
carried in the PACK-15 FINAL PASS archive** at its canonical path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, which is the
only authoritative register. **No standalone register version is used and
no second register is created.**

**No FIR entry is marked `implemented` by this round, and none may be.**

Treatment values permitted for a specification stage:

```text
specified                        assessed
selected for architectural review
deferred to PACK-16B / 16C / 16D / 17
blocked pending legal assessment
unchanged
```

Treatment values **prohibited** for this round:

```text
implemented · externally verified · production ready · legally activated
```

**New FIR identifiers created by this round: none.**
**FIR identifiers removed, renamed or downgraded: none.**

---

## 1. Roadmap

| FIR               | Status before | Treatment                            | References                        | Obligation that remains                                                                                       |
| ----------------- | ------------- | ------------------------------------ | --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `FIR-ROADMAP-005` | `approved`    | **unchanged**                        | —                                 | PACK-15 remains as it was; this round consumes its output and changes nothing in it                            |
| `FIR-ROADMAP-006` | `approved`    | **selected for architectural review** | whole pack; `ADR-099`             | **Status stays `approved`.** PACK-16A performs the research and selection stage only; the scope items — ballot casting, vote verification, tally controls — remain unimplemented |
| `FIR-ROADMAP-007` | `approved`    | **deferred to PACK-17**              | threat model §9; privacy flows §14 | Network metadata, backup/restore topology, resilience, incident readiness and independent-verification operations |
| `FIR-ROADMAP-008` | `approved`    | **unchanged**                        | —                                 | Untouched                                                                                                       |
| `FIR-ROADMAP-009` | `approved`    | **unchanged**                        | —                                 | Untouched                                                                                                       |

**`FIR-ROADMAP-006` MUST NOT move to `implemented`, `scheduled` or any
status implying delivery on the strength of this round.** Its target
version stays `0.16.0` and belongs to the implementation candidate.

---

## 2. Hard invariants

| FIR                                                    | Status before | Treatment                                  | References                                                        | Obligation that remains                                                                                                    |
| ------------------------------------------------------ | ------------- | ------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `FIR-INV-001` No global user ID                        | `approved`    | **specified** for the ballot domain        | `BM-01`…`BM-04`; §3.2 prohibited content; `T-P16A-09`             | Prohibited-key and derivability scans over every ballot-domain artifact                                                     |
| `FIR-INV-002` Identity/ballot unlinkability            | `approved`    | **partially addressed — architecture of the second half specified** | `ADR-099`; `CC-01`…`CC-10`; `BM-01`…`BM-06`; threat model §2 | **This entry cannot be closed by PACK-16A.** PACK-15 closed the identity→credential half; PACK-16A **specifies** the architecture of the credential→ballot half; **neither half alone closes the invariant, and specification is not closure** |
| `FIR-INV-003` Voting Client isolation                  | `approved`    | **specified**, client deferred             | scope §4; `CC-07`; `BB-14`                                        | The isolation contract is extended to a third verification origin; the clients are FRONT-PACK and PACK-16C                 |
| `FIR-INV-004` Eligibility/credential separation        | `approved`    | **unchanged**                              | —                                                                 | PACK-15 owns it; PACK-16A consumes its output and adds nothing                                                             |
| `FIR-INV-005` No intermediate tally                    | `approved`    | **specified** for the tally domain         | `BM-21`, `BM-22`; `NIT-01`…`NIT-07`; `BB-11`; `SD-09`             | PACK-15 forbade pre-closure disclosure; PACK-16A specifies a tally that has no pre-closure decryption path at all           |
| `FIR-INV-006` Safe feature flags                       | `approved`    | **specified**                              | `NIT-06`; `BM-21`, `BM-22`; challenge/spoil non-disablable        | No flag may disable proof verification, board publication, the quorum, challenge/spoil or the no-intermediate-tally rule    |
| `FIR-INV-007` DLP and controlled export                | `approved`    | **specified**                              | `DF-10`; `SD-07`; `AUDIT_EXPORT_REFUSED`                          | PACK-12 owns the mechanism; PACK-16A adds the no-two-contexts and pre-closure-section rules for the ballot domain           |
| `FIR-INV-008` Security/System Admin separation         | `approved`    | **specified** for the ballot domain        | role matrix §2, §3; `KC-16`                                       | Neither role may hold guardian material; the `✗` in the matrix is structural                                               |
| `FIR-INV-009` JIT and break-glass governance           | `approved`    | **specified**                              | role matrix §7; `KC-18`                                           | No break-glass path decrypts, assembles a quorum, writes to the board or spans the trust boundary                          |
| `FIR-INV-010` Document version integrity               | `approved`    | **unchanged**                              | —                                                                 | Reused from PACK-11                                                                                                        |
| `FIR-INV-011` Statistical Disclosure Control           | `approved`    | **specified** for published results        | `SD-01`…`SD-09`; `T-P16A-41`                                      | `disclosure_min_cell = 5` **unchanged**; complementary suppression extended to results, jointly across the published set    |
| `FIR-INV-012` Accessibility as Definition of Done      | `approved`    | **specified** at protocol level            | `AX-01`…`AX-43`                                                   | Protocol-level constraints recorded; the interface obligations remain FRONT-PACK's                                          |
| `FIR-INV-013` Bund/Land/Kreis isolation                | `approved`    | **unchanged**                              | —                                                                 | Untouched; scope handling is inherited                                                                                     |
| `FIR-INV-014` No universal administration              | `approved`    | **specified** for the ballot domain        | role matrix §2, §5; `RS-06`                                       | No principal holds eligibility, issuance and tally authority; the dangerous-collusion list is normative                    |
| `FIR-INV-015` No false production claims               | `approved`    | **specified and enforced**                 | coercion boundary §7, §8; acceptance `AC-P16A-071`…`074`          | Permitted- and prohibited-claims registries with a scannable enforcement obligation                                        |

### 2.1 `FIR-INV-002` — why this round does not close it

PACK-15 records that `identity → credential` and `credential → ballot` are
**two parts of one invariant**, and that neither half alone closes it. This
round:

- **specifies** the architecture of the second half;
- **does not implement** it;
- **does not demonstrate** the "cannot be paired" property, which requires a
  built system to demonstrate against;
- leaves the strongest residual — timing correlation — **reduced and
  bounded, not eliminated** (`T-P16A-04`, extending PACK-15 `T-P15-13`).

`FIR-INV-002` therefore stays **partially addressed and future**, exactly
as PACK-15 left it, with the treatment upgraded from "architecture unknown"
to "architecture specified, unproven".

---

## 3. Roles

| FIR            | Status before | Treatment       | References                    | Obligation that remains                                                        |
| -------------- | ------------- | --------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| `FIR-ROLE-001` DPO                    | `approved` | **specified** | role matrix `R-13`; `DF-10`   | The DPO receives no plaintext ballot access by role, because none exists       |
| `FIR-ROLE-002` Election board/officer | `approved` | **specified** | role matrix `R-01`, `R-02`    | The Election Board's authority over exclusion, abort and annulment is defined  |
| `FIR-ROLE-003` Independent auditor    | `approved` | **specified** | role matrix `R-11`; §4        | Concurrence required for grave acts; access remains evidence-bundle access     |
| `FIR-ROLE-004` Finance auditor        | `approved` | **unchanged** | —                             | Untouched                                                                      |
| `FIR-ROLE-005` Election Administration Separation Matrix | `approved` | **specified — extended** | `PACK-16A-ROLE-SEPARATION-MATRIX.md` | PACK-15's matrix stands; six ballot-domain roles and ten dangerous collusion combinations are added |
| `FIR-ROLE-006` Finance separation     | `approved` | **unchanged** | —                             | Untouched                                                                      |

---

## 4. Entries this round engages without closing

| FIR                                                     | Treatment                             | Why it is engaged                                                                                                     |
| ------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `FIR-CAND-001` Candidacy & Nomination                   | **blocked pending legal assessment**  | Statutory nomination requires physical presence and paper ballots `[E-50]`, `[E-51]`; internal pre-selection is supported |
| `FIR-ASM-006` Advance voting                            | **deferred to PACK-16C**              | Interaction between an assembly's advance vote and a `EPD2-HOM-1` context is unspecified                              |
| `FIR-ASM-007` Closed confidential poll                  | **deferred to PACK-16C**              | A session-bound context type exists in PACK-15 §7.1; its ballot handling is not designed here                         |
| `FIR-COMM-002` Neutral sensitive notifications          | **specified**                         | Failure-model §7 restates the prohibition on person-level participation statements                                    |
| `FIR-DELIVERY-001` Official delivery and receipt        | **specified**, partially              | Notification classes extended for pause, extension, abort, annulment and uncertifiable result                         |
| `FIR-INCLUSION-001` Assisted and alternative channels   | **specified** at protocol level       | Accessibility §6, §7; the fallback is a different channel, and `AX-42` refuses activation without one                 |
| `FIR-CONFIG-001` Governed operational configuration     | **specified**                         | Profile, parameter set, k and n, mirror list and counting rule are governed configuration frozen in the manifest      |
| `FIR-METRIC-002` Count, facet and small-cohort controls | **specified** for results             | `SD-01`…`SD-09`; no value changed                                                                                    |
| `FIR-SEC-001` Security incident and breach response     | **deferred to PACK-17**               | Failure model names outcomes; runbooks are PACK-17's                                                                 |
| `FIR-SEC-002` Backup verification and recovery testing  | **deferred to PACK-17**               | `DF-12`; `T-P16A-10`                                                                                                 |
| `FIR-TRUST-001` Signature, seal and timestamp framework | **deferred to PACK-16B**              | Board checkpoints, ceremony evidence and archive commitments will need it                                            |
| `FIR-QUALITY-001` Data quality and discrepancy handling | **specified**, partially              | `AUDIT_DISCREPANCY_DETECTED`, `ARCHIVE_DISCREPANCY_DETECTED`, and the uncertifiable-result path                      |
| `FIR-DATA-003` Legal Hold                               | **assessed**                          | A legal hold must not extend the life of a correlation capability — PACK-15 §10.3's rule applies to ballot-domain evidence |
| `FIR-GOV-001` Emergency governance                      | **specified**, partially              | Abort, annul and re-run authorities named; `KC-18` forbids silent break-glass                                        |
| `FIR-PROG-001` Program formation lifecycle              | **unchanged**                         | Consultation contexts are supported; the lifecycle is untouched                                                      |

---

## 5. Entries preserved and explicitly untouched

**Required by the round definition to be preserved. Verified present and
unmodified in the register carried in this archive.**

| FIR            | Title                                                        | State                |
| -------------- | ------------------------------------------------------------ | -------------------- |
| `FIR-UX-011`   | Page Specification and Screen Content Governance             | **preserved, unchanged** |
| `FIR-OSS-001`  | EUPL-1.2 Project Licensing Baseline                          | **preserved, unchanged** |
| `FIR-OSS-002`  | Source Availability for Network-Provided Modified Versions   | **preserved, unchanged** |
| `FIR-OSS-003`  | Third-Party Licence and Dependency Compliance                | **preserved, unchanged** |
| `FIR-OSS-004`  | Contribution, Copyright and Provenance Governance            | **preserved, unchanged** |
| `FIR-OSS-005`  | Trademark, Name and Official Instance Separation             | **preserved, unchanged** |
| `FIR-OSS-006`  | Open Verification, Reproducible Builds and Public Security Process | **preserved, unchanged** |

`FIR-UX-003` … `FIR-UX-011` apply in full and are untouched. PACK-16A
produces the **domain side** of `FIR-UX-011`'s responsibility split and
**none** of its artefacts.

### 5.1 A licensing note that is not a change

The selected specification is MIT-licensed `[E-10a]`, which creates no
dependency on the unresolved `FIR-OSS-*` work. The rejected alternative
Belenios is AGPL-3.0 `[E-10]`, whose interaction with the intended
`EUPL-1.2` baseline is a question for `FIR-OSS-001` and `FIR-OSS-003`.
**This round neither answers it nor implements any `FIR-OSS-*` obligation,
and claims compliance with none.** `OD-P16A-08` records it.

`FIR-OSS-006` — open verification and reproducible builds — is engaged in
substance by `BM-28` (an independent verifier) and `KC-25` (pinned,
recorded provenance), and is **deferred to PACK-16D** for delivery.

---

## 6. Summary

| Measure                                                  | Value                                        |
| -------------------------------------------------------- | -------------------------------------------- |
| FIR entries assessed                                     | all entries in the canonical register        |
| FIR entries **specified** by this round                  | 20                                           |
| FIR entries **deferred** with a named owner              | 8                                            |
| FIR entries **blocked pending legal assessment**         | 1 (`FIR-CAND-001`)                           |
| FIR entries **unchanged**                                | all others                                   |
| FIR entries marked `implemented`                         | **0**                                        |
| FIR entries created                                      | **0**                                        |
| FIR entries removed, renamed or downgraded               | **0**                                        |
| Register copies in the archive                           | **1**, at the canonical path                 |
| `FIR-INV-002` closed                                     | **no — and it cannot be, by this round**     |

**SPECIFIED. ASSESSED. NO OBLIGATION CLOSED. REQUIRES EXTERNAL REVIEW. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED.**
