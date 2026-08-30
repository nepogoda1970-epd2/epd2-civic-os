# PACK-16B — Specification Report

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What was asked, and what was produced

PACK-16A chose a protocol and deliberately left four things open: what the
parameters are, who holds the threshold, how the key comes into existence,
and what happens when a guardian is lost or turns. This round answers those
four.

```text
PARAMETER PROFILE    EPD2-CRYPTO-1 — the specification's fixed 4096-bit
                     finite-field parameters, adopted UNMODIFIED
GUARDIANS / QUORUM   k = 3 of n = 5 default; k = 4 of n = 7 high assurance
CEREMONY             twenty phases; in person or controlled hybrid;
                     FULLY REMOTE PROHIBITED
RECOVERY LIMITS      per-guardian own-share backup only; no escrow;
                     no break-glass; no pre-closure decryption
AGILITY              pinned by digest; dated deprecation; no downgrade path
ADR                  ADR-100, status proposed
```

29 documents under `docs/packs/PACK-16/`, one ADR, one additive Master
Register entry. **Nothing else in the repository was touched.**

**Corrected candidate.** A narrow documentation correction round advanced
the BSI subgroup-order assessment, narrowed the interoperability claim to
what the evidence supports, replaced an absolute negative research claim
with a bounded absence-of-evidence finding, and inserted the corrected
archive's digest into the handover. A final BSI evidence round then
**withdrew the closure of `OD-P16B-01`**, because the current edition of the
document that decision names could not be retrieved and a closure resting on
other editions is not the closure claimed. Two further rounds then closed it
properly: first on the reviewer's attestation, then — when the official PDF
was supplied locally — on **a first-hand reading of the document itself**,
which also corrected the figure from 240 to **250** and surfaced one
recommendation-level divergence `[F-36]`. **No architectural decision
changed in any of the four rounds**; `PACK-16B-HANDOVER.md` §0.2…§0.5 record
the diffs.

---

## 2. The four findings that changed the shape of the round

### 2.1 The parameters are fixed upstream — which decides the FF/EC question

The decision was expected to be a trade-off between finite fields and
elliptic curves. It is not, because the specification **fixes** its
parameters `[F-04]` and a conforming verifier requires **bit-equality**
`[F-05]`.

```text
That converts options B and C from parameter choices into
verifier-forking protocol adaptations — each needing its own ADR,
its own security analysis and its own verifier.
```

Option A is therefore the only choice consistent with `BM-26`, `BM-28` and
`BB-33`. **Elliptic curves were not rejected for being faster or slower**
(`IM-46` forbids that reasoning); they were rejected because choosing them
would mean no conforming verifier could read an EPD² record.

A second, independent reason: `H_q` is *"tailored to the specific choice of
`q = 2²⁵⁶ − 189"* `[F-07]`, so a different group order would require
redesigning challenge derivation.

### 2.2 Compensated decryption does not exist — a correction, not a change

PACK-16A `KC-11` describes lost-trustee handling in terms of **compensated
shares**. That mechanism belonged to the 1.x lineage. **The word does not
appear in the pinned 2.1 specification** `[F-11]`, which instead computes
partial decryptions over the available set and explicitly refuses to
reconstruct an absent guardian's secret, _"to prevent the secret from being
used for additional decryptions without the cooperation of at least `k`
guardians."_

**That is `KC-15`'s own policy, reached independently by the specification's
authors.** The requirement is unchanged; only the described mechanism is
corrected, and the correction is recorded in
`PACK-16B-SCOPE-AND-BOUNDARY.md` §5 rather than applied silently to an
accepted pack.

This is a **better** position than the one PACK-16A anticipated: compensation
material is stored material whose possession is consequential, with five
places where the effective threshold can drift without anyone deciding that
it should. A construction that has none of it cannot drift.

### 2.3 The specification leaves exactly two things unspecified that EPD² needs

```text
1. Complaint and disqualification. The upstream treatment is three
   sentences — abort, investigate out of band, restart from scratch [F-12].
   No roles, no deadlines, no evidence standard, no adjudicator.
2. A pre-publication commitment round. The DKG omits Pedersen's
   commit-then-open step; GJKR shows a party acting last can bias the
   joint key — 3/4 rather than 1/2 [F-15]. The same specification uses
   the right countermeasure in its DECRYPTION protocol and not in key
   generation [F-16].
```

Both were filled **at the orchestration layer**: no hash input, no
challenge, no proof and no verifier-consumed field changes, and
interoperability is preserved. EPD²'s own domain uses **string** tags under
`H_X = H(H_B; "epd2_ceremony_v1")`, so EPD² cannot squat an upstream tag
byte.

**The commitment round is claimed as a mitigation of an analogous exposure,
not as a fix**, and `TV-08` must assess it. `F-32` — Pedersen-DKG bias is
provably survivable for _some_ DL-based schemes at the cost of a larger
modulus — is the counterweight, and it says _some schemes_, not _this
scheme_.

### 2.4 The component the architecture depends on most has the least scrutiny

```text
No peer-reviewed security analysis specifically covering the selected
ElectionGuard 2.1 key-ceremony composition was located in the sources
reviewed for PACK-16B.   [F-31]

This absence-of-evidence finding must not be interpreted as proof that
no such analysis exists.
```

This is the single most consequential finding of the round, and it drove every
close call toward the conservative answer: fully remote ceremonies
prohibited, `k ≥ 3`, no compensation reintroduced, no cryptographic
invention, and `OD-P16A-06` recorded as `blocked pending cryptographic
review` rather than described as addressed.

---

## 3. The decisions, in one place

| Question                  | Decision                                                                                                                                 | Where                     |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Parameter profile         | `EPD2-CRYPTO-1`, unmodified upstream parameters (Option A)                                                                               | `PSS` §2                  |
| Specification pinning     | By SHA-256, not by URL; a new digest is a new profile                                                                                    | `PSS` §3, `CA-01`…`CA-05` |
| BSI verdict               | `q = 256` exceeds the BSI minimum of **250** — §2.3.3 p. 34, §2.3.5 p. 36, read first-hand `[F-36]`; complete conformity **not** claimed | `CPA` §3, §3.2            |
| Deprecation / prohibition | 2030-12-31 (high assurance) / 2031-12-31; prohibited 2032-12-31                                                                          | `PS-*`, `CA-08`           |
| Fiat–Shamir               | Strong FS, statement and context in every challenge                                                                                      | `FSDS` §3                 |
| Domain separation         | 27 upstream tag bytes + EPD² **string** tags under `H_X`                                                                                 | `FSDS` §5                 |
| Canonical encoding        | Fixed-length big-endian 512/32/4, non-canonical **rejected**                                                                             | `FSDS` §4                 |
| Randomness                | `EPD2-RND-1`; PTG.2 never used directly; fail-closed                                                                                     | `RND` §1, §6              |
| Guardian count            | `n = 5` default, `n = 7` high assurance; `5 ≤ n ≤ 9`, `n ≥ k + 2`                                                                        | `GQM` §2                  |
| Quorum                    | `k = 3` default, `k = 4` high assurance; `k ≥ 3` always; never reducible                                                                 | `GQM` §2, `GQ-05`         |
| Independence              | 15 pairwise tests, hard/soft; internal guardians capped at `k − 1`                                                                       | `GIM` §2, `GQ-11`         |
| Key ceremony              | 20 phases + EPD² pre-publication commitment round                                                                                        | `KCS` §3, §4              |
| Transcript                | One canonical published artefact, not a canonical aggregate                                                                              | `CTS`, `CAN` `CQ-P16B-01` |
| Complaints                | 11 grounds, 7 arithmetically checkable; no administrative resolution                                                                     | `CDM` §2, `CD-08`         |
| Custody                   | Dedicated devices, smart cards, HSMs one-per-guardian; **no cloud KMS**                                                                  | `KCR` §2, §4.1            |
| Backup                    | Per-guardian, own share, own custody, second dedicated medium only                                                                       | `BRC` §3                  |
| Compensation              | **Does not exist** in the pinned version; not reintroduced                                                                               | `BRC` §5                  |
| Compromise                | 9 classes; bounded by activation state, never by preference                                                                              | `CQL` §3, §4              |
| Quorum loss               | The result is unobtainable; the context is annulled; ballots never decrypted                                                             | `CQL` §5                  |
| Break-glass               | **None.** Enforced by absence of the operation                                                                                           | `CQL` §6                  |
| Pre-closure decryption    | **Prohibited.** An attempt aborts and annuls                                                                                             | `CQL` §7                  |
| Remote ceremony           | Fully remote **prohibited**; controlled hybrid expected                                                                                  | `RCA` §1                  |
| Roles                     | 12 ceremony roles + 2 new; 20-phase RACI; 19 prohibitions                                                                                | `RSM` §1…§3               |
| Incidents                 | 19 events with class, actor, timing bound and code                                                                                       | `INM` §1                  |
| Reason codes              | 22 namespaces, 129 codes, closed field vocabulary                                                                                        | `RCS`                     |
| Failures                  | 35 conditions; 8 outcomes; **no "governance decides"**                                                                                   | `FAM`                     |
| Implementation            | Criteria fixed; `OD-P16A-04` **not** closed                                                                                              | `IEC`                     |
| Formal review             | `TV-01`…`TV-08`, 14 vector classes; `OD-P16A-06` **blocked**                                                                             | `TVR`                     |

---

## 4. Verification performed locally

| Check                                         | Result                                                   |
| --------------------------------------------- | -------------------------------------------------------- |
| `scripts/check_repository.py`                 | **OK — all 983 required paths present**                  |
| `scripts/verify_versions.py`                  | **OK — all version sources consistent**                  |
| `scripts/check_canon_0_8_0.py`                | **OK — all 18 canon 0.8.0 amendment checks passed**      |
| `scripts/check_forbidden_files.py`            | **OK — no forbidden paths found**                        |
| Required documents present                    | **29 of 29** under `docs/packs/PACK-16/`                 |
| `ADR-100` path and status                     | Correct path; status **`proposed`**                      |
| Evidence registries in PACK-16B               | **1**                                                    |
| `[F-nn]` references unresolved                | **0** (35 defined; every reference resolves)             |
| Conflicting evidence definitions              | **0**                                                    |
| Evidence sequence gaps                        | **0** (`F-01`…`F-35` contiguous)                         |
| Acceptance-matrix rows                        | **129**, `AC-P16B-001`…`AC-P16B-129`                     |
| Duplicate requirement IDs                     | **0**                                                    |
| `sum(status counts) == requirement rows`      | **129 == 129 ✓**                                         |
| Reason codes defined                          | **129**, across 22 namespaces (20 required + 2 declared) |
| Duplicate reason codes                        | **0**                                                    |
| Reason codes used but undefined               | **0**                                                    |
| Source / test / migration / CI / lock changes | **0**                                                    |
| `REPOSITORY_VERSION`                          | **`0.15.0`, unchanged**                                  |
| `CANON_VERSION`                               | **`0.8.0`, unchanged**                                   |

**Cross-reference resolution:** every PACK-16A identifier cited by a
PACK-16B document (`KC-*`, `BM-*`, `BB-*`, `TP-*`, `RS-*`, `T-P16A-*`,
`FM-P16A-*`, `MX-*`, `SD-*`, `AX-*`, `RR-*`, `E-*`) was checked against the
PACK-16A documents in this tree. **Unresolved: 0.**

```text
PARTIAL LOCAL VERIFICATION ONLY.
EXTERNAL ARCHITECTURAL REVIEW REQUIRED.
EXTERNAL CRYPTOGRAPHIC REVIEW REQUIRED BEFORE ANY ACTIVATION.
```

No CI was run, no test was executed, no build was produced, and **no
verification result is fabricated**. The four scripts above were run
against this tree and their output is quoted verbatim.

---

## 5. The architectural invariants this round enforces

```text
NO HIDDEN MASTER KEY
NO SINGLE-ADMIN DECRYPTION
NO BREAK-GLASS DECRYPTION
NO PRE-CLOSURE DECRYPTION
NO COMPENSATION MATERIAL
NO ESCROW, IN ANY FORM, UNDER ANY NAME
NO PARAMETER NEGOTIATION
NO DOWNGRADE PATH
NO GUARDIAN SECRET IN A BROWSER
NO PERSON-TO-BALLOT LINK
```

Each is enforced by the **absence of an operation** rather than by a check,
because a check can be bypassed by whoever operates it and an operation that
was never specified has to be added in public.

---

## 6. What this round did not do

```text
No code, no cryptographic code, no tests, no migrations.
No API, event or frontend implementation. No CI change.
No dependency, uv.lock or package-lock.json change.
No version bump. No canon change. No FIR status change.
No implementation, library or vendor selected.
No certification, conformance or legal claim.
PACK-16C not started. PACK-16D not started.
```

**It also did not close four things it could have pretended to close:**
`OD-P16A-04` (implementation), `OD-P16A-06` (cryptographic review),
and `OD-P16A-11` (the legal _Stand der Technik_ mapping).

---

## 7. Residual risks, ranked

| Rank | Risk                                                                                                                                                                                                                                                  | Rating   | Carried by                                       |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------ |
| 1    | **No peer-reviewed analysis of the key ceremony was located** `[F-31]`                                                                                                                                                                                | **high** | `TV-08`, `OD-P16A-06`                            |
| 2    | **No production-grade implementation of the pinned version exists**                                                                                                                                                                                   | **high** | `OD-P16A-04`, `OD-P16B-02`                       |
| 3    | The classical-cryptography recommendation lapses end-2031 / end-2030 `[F-25]`                                                                                                                                                                         | **high** | `OD-P16B-06`, `CA-08`                            |
| 4    | Upstream has no errata process and marks two versions "Recommended" `[F-30]`                                                                                                                                                                          | medium   | `CA-19`…`CA-27`                                  |
| 5    | A weak or duplicated nonce in a browser is **silent and undetectable** `RB-08`                                                                                                                                                                        | medium   | `IM-43`, PACK-16D                                |
| 6    | Independence declarations are self-reported                                                                                                                                                                                                           | medium   | `GI-*`, governance                               |
| 7    | Two specification inconsistencies resolved on EPD²'s own reading `[F-19]`                                                                                                                                                                             | medium   | `DS-16`, `CA-27`                                 |
| 8    | Guardian volunteers bear real personal exposure through publication                                                                                                                                                                                   | medium   | governance                                       |
| 9    | **Published parameter family normative divergence** — Remark 2.12 prefers MODP or ffdhe groups; `EPD2-CRYPTO-1` uses neither, though every numerical condition is met `[F-36]`. **Not a claim of insecurity.** Blocks production and legal activation | medium   | `VO-08` — external cryptographic review, PACK-17 |
| —    | A quorum loss makes a result genuinely unobtainable                                                                                                                                                                                                   | accepted | `CM-14`…`CM-19`                                  |

---

## 8. Honest statement of what this round is

```text
This is a specification. Nothing here has been built, tested,
independently reviewed or legally assessed.

The parameters were reproduced but not independently reviewed.
The ceremony was specified but never rehearsed.
The guardians do not exist.
The implementation does not exist.
The cryptographic review does not exist, and its absence is the
   single largest risk this architecture carries.

What has been done is to make every one of those absences visible,
named, owned and dated — so that none of them can be closed by
someone in a hurry.
```

**SPECIFIED. REQUIRES EXTERNAL ARCHITECTURAL REVIEW. REQUIRES EXTERNAL
CRYPTOGRAPHIC REVIEW BEFORE ANY ACTIVATION. NOT A FINAL PASS. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION
PROHIBITED BY DEFAULT.**
