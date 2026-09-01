# PACK-16B — Implementation Evaluation Criteria

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**No library, product, language or vendor is selected here, and none may be
inferred from this document.** `OD-P16A-04` — the choice of cryptographic
implementation — remains open. What this round does is fix the criteria
against which PACK-16D must make that choice, so that the decision is made
against a written standard rather than against whatever is convenient at the
time.

---

## 0. Why criteria, and not a choice

PACK-16A left `OD-P16A-04` open for a good reason: the implementation
question depends on answers this round produces (fixed parameters, no
compensation, `H` as HMAC-SHA-256, a fixed encoding). Those answers now
exist, and they narrow the field sharply — but they do not select.

```text
A library is not correct because it is popular.
A library is not correct because it is fast.
A library is not correct because it is FIPS-validated.
A library is correct if it reproduces the specification's test vectors
   bit for bit, and if someone independent has said so.
```

| ID      | Rule                                                                                                                                                        |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IM-01` | **PACK-16D selects; PACK-16B does not.** A candidate is assessed against §2…§8, and the assessment is published with the choice                             |
| `IM-02` | **A candidate that fails any MANDATORY criterion is rejected**, regardless of its score elsewhere. There is no aggregate that overrides a mandatory failure |
| `IM-03` | The assessment is **published with its evidence**, including the criteria the selected candidate fails                                                      |

---

## 1. The inherited requirements this document discharges

`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §6 handed four
implementation obligations forward. They are stated here **as PACK-16A
wrote them**, not as they are sometimes remembered:

| PACK-16A ID | Obligation, as written                                                                                                    | Discharged into                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `KC-23`     | Verify that the chosen implementation uses **strong Fiat–Shamir**, _by test against the specification, not by assumption_ | `IM-07` (MANDATORY) + `TV-06`, `VC-07` — the test, named                          |
| `KC-24`     | Verify the implementation's output against an **independent verifier it did not ship**                                    | `IM-44` (weighted) + `TV-07`, `VC-05` (blocking for activation)                   |
| `KC-25`     | **Pin and record** the implementation's version, provenance and supply chain                                              | `IM-33`…`IM-38` (MANDATORY)                                                       |
| `KC-26`     | Where no implementation satisfies `KC-23`–`KC-25`, **do not proceed** (`FM-P16A-22`)                                      | `IM-02` — a mandatory failure is a rejection, with no aggregate that overrides it |

`KC-27` — a migration path that does not require re-opening a past
election's record — is discharged by
`PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` (`CA-06`…`CA-10`, `PS-10`), not
here.

**The side-channel, zeroization and secret-containment criteria in §3–§5 are
this round's own additions.** PACK-16A did not require them; the round task
does, and an implementation that met `KC-23`–`KC-26` while logging a nonce
would be useless.

---

## 2. Correctness — MANDATORY

| ID      | Criterion                                                                                                                   | Evidence required                               |
| ------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `IM-04` | **Reproduces the official upstream test vectors bit for bit** (`TV-02`)                                                     | Vector run output, published                    |
| `IM-05` | **Reproduces the fixed parameters** from their published derivation (`TV-01`)                                               | Derivation transcript                           |
| `IM-06` | **Implements the fixed-length big-endian encoding exactly** — 512/32/4 bytes — and rejects non-canonical encodings on input | Serialization vectors (`TV-05`), negative cases |
| `IM-07` | **Implements `H` as HMAC-SHA-256 with the 32-byte key slot**, and `H_q` as `H(…) mod q`, with the 27 domain tags exactly    | Domain-separation vectors (`TV-06`)             |
| `IM-08` | **Validates every received group element** for subgroup membership before use — no exceptions, no sampling                  | Negative vectors; code review                   |
| `IM-09` | **Rejects a malformed proof rather than treating it as absent**, and distinguishes the two in its error signal              | Malformed-proof vectors (`TV-04`)               |

**`IM-06` and `IM-08` are the two most commonly failed in practice**, and
both fail silently: a lenient decoder and an unvalidated element produce
plausible output on adversarial input.

---

## 3. Side-channel resistance — MANDATORY

| ID      | Criterion                                                                                                           | Applies to                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `IM-10` | **Constant-time modular exponentiation with secret exponents** — share operations, partial decryption, nonce use    | Ceremony device, decryption                      |
| `IM-11` | **No secret-dependent branch** in any operation touching `z_i`, `ẑ_i`, `s_i`, `ζ_i`, a nonce or a seed              | Ceremony device, client encryption               |
| `IM-12` | **No secret-dependent memory access pattern** — no table lookup indexed by secret material                          | Both                                             |
| `IM-13` | **Constant-time equality comparison** for every secret or authenticator comparison                                  | Both                                             |
| `IM-14` | **Documented side-channel posture**: what the implementation claims, what it does not claim, and on which platforms | Both — a claim without a platform is not a claim |

### 3.1 What is honestly out of reach

```text
A browser cannot offer a constant-time guarantee. JIT compilation,
garbage collection, shared caches and a hostile tab are all outside
the implementation's control, and no amount of careful coding changes it.
```

This is not a reason to abandon the browser; it is a reason to be exact
about what runs where — §6.

---

## 4. Memory hygiene — MANDATORY

| ID      | Criterion                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IM-15` | **Secret material is zeroised** as soon as it is no longer needed, and the zeroisation is not removable by the optimiser                                                                                                             |
| `IM-16` | **Ceremony secrets are destroyed at ceremony completion** (`GL-16`) by the implementation, not by an operator remembering                                                                                                            |
| `IM-17` | **No secret material is written to swap** where the platform allows control; where it does not, the limitation is declared                                                                                                           |
| `IM-18` | **No secret material in a core dump or crash report.** Crash reporting is disabled on ceremony devices, or scrubbed and proven scrubbed                                                                                              |
| `IM-19` | **No secret material in browser storage of any kind** — no `localStorage`, no `sessionStorage`, no IndexedDB, no service-worker cache. Nonces and plaintext selections live in memory for the life of the operation and nowhere else |

---

## 5. Secret containment — MANDATORY

| ID      | Criterion                                                                                                                                                            |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IM-20` | **No secret in logs**, at any level, including debug builds. A debug build that logs a nonce is a production incident waiting for a misconfigured deployment         |
| `IM-21` | **No secret in exception text.** An exception naming a value is a log entry, an error report and a screenshot                                                        |
| `IM-22` | **No secret in telemetry, metrics or traces** — including lengths and timings that are secret-dependent (`IM-12`)                                                    |
| `IM-23` | **No secret in a reason code or its fields** — `RN-C05`'s closed field list is the enforcement point                                                                 |
| `IM-24` | **No secret in a URL, a query parameter, a header or a referrer**                                                                                                    |
| `IM-25` | **No secret in a transcript**, per `CT-13`…`CT-17`, enforced by the implementation and not only by procedure                                                         |
| `IM-26` | **No ballot content anywhere outside the encryption operation** — the plaintext selection exists in the client, for the duration of the encryption, and is then gone |
| `IM-27` | **No secret crosses a process boundary** except as the construction's own encrypted share                                                                            |

---

## 6. Browser versus native/WASM — the split

The Voting Client is a browser application, the ceremony is not, and
pretending they have the same requirements would produce either an unusable
client or an unsafe ceremony.

| Operation                                        | Browser                    | Native / independently verifiable module | Rationale                                                         |
| ------------------------------------------------ | -------------------------- | ---------------------------------------- | ----------------------------------------------------------------- |
| **Ballot encryption** (exponential ElGamal)      | **Permitted**              | Also permitted                           | The secret is a per-ballot nonce, short-lived, single-use         |
| **NIZK well-formedness proof generation**        | **Permitted**              | Also permitted                           | Same nonce lifetime                                               |
| **Benaloh challenge** (nonce disclosure)         | **Permitted**              | Also permitted                           | The nonce is deliberately disclosed                               |
| **Manifest and parameter validation**            | **Permitted**              | Also permitted                           | Public inputs only                                                |
| **Verifier recomputation** (public verification) | **Permitted, encouraged**  | **Required to also exist**               | A verifier only a browser can run is not independently verifiable |
| **Guardian key generation**                      | **PROHIBITED**             | **Required**                             | Long-lived secret, on a device that must be dedicated (`KU-05`)   |
| **Polynomial and commitment generation**         | **PROHIBITED**             | **Required**                             | Same                                                              |
| **Share encryption and decryption**              | **PROHIBITED**             | **Required**                             | Same                                                              |
| **Partial decryption**                           | **PROHIBITED**             | **Required**                             | This is the operation the entire architecture protects            |
| **Any use of `z_i`, `ẑ_i`, `s_i`, `ζ_i`**        | **PROHIBITED**             | **Required**                             | Categorical                                                       |
| **Tally aggregation** (homomorphic addition)     | Permitted for verification | Required for the official run            | Public ciphertexts; a verifier must be able to redo it            |

| ID      | Rule                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IM-28` | **No guardian secret material ever exists in a browser context**, in any form, at any time, on any platform. This is not a performance criterion and is not waivable |
| `IM-29` | The **ceremony application is a native or WASM application on a dedicated device** (`KU-05`), not a web page                                                         |
| `IM-30` | A **WASM ceremony module is acceptable only outside a browser host** — as an embedded runtime on the dedicated device — and its host is declared                     |
| `IM-31` | The **independent verifier must exist as a non-browser implementation**, so that verification does not depend on a browser vendor (`BB-33` lineage)                  |
| `IM-32` | The client's cryptographic operations must be **reproducible outside the browser** from published inputs, so that a disputed encryption can be checked elsewhere     |

### 6.1 The honest limit of the browser client

The browser is where a voter actually is, and PACK-16A already accepted the
consequence (`T-P16A-09`, malicious client). Benaloh cast-or-challenge is
the mitigation, and it is a **detection** mechanism, not a prevention one.

```text
The browser client can be compromised. The architecture is built so that
a compromised client can be caught by the voter, not so that it cannot
happen. That is the state of the art, and it is not concealed.
```

---

## 7. Supply chain and build — MANDATORY

| ID      | Criterion                                                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IM-33` | **Reproducible build**: an independent party rebuilds the ceremony application and the client from published sources and obtains identical artefacts                                  |
| `IM-34` | **Dependency provenance**: every dependency's origin, version, signature and maintainer is recorded; transitive included                                                              |
| `IM-35` | **Pinned dependencies** with published digests. The ceremony build resolves nothing at build time                                                                                     |
| `IM-36` | **Minimal dependency surface** for ceremony code — a criterion with teeth: a candidate pulling a large transitive tree into the key-generation path scores badly and says why it must |
| `IM-37` | **Published build attestation**, verifiable against the artefact the guardians actually run (`KY-03`)                                                                                 |
| `IM-38` | **No network access from the ceremony application**, and the build enforces it rather than the operator promising it                                                                  |

---

## 8. Testing obligations on the implementation

| ID      | Criterion                                                                                                        |
| ------- | ---------------------------------------------------------------------------------------------------------------- |
| `IM-39` | **Known-answer tests** against every published vector class (`TV-02`…`TV-08`)                                    |
| `IM-40` | **Negative tests**: every rejection path in `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` has a test that reaches it    |
| `IM-41` | **Malformed-proof tests**, including proofs that are valid for a different context or a different domain tag     |
| `IM-42` | **Non-canonical-encoding tests**: leading zeros, short encodings, over-long encodings, out-of-range values       |
| `IM-43` | **Fault-injection tests** on the ceremony device where the platform permits, and a declaration where it does not |
| `IM-44` | **Differential tests** against at least one independent implementation (`TV-07`)                                 |
| `IM-45` | **Property-based tests** for the algebraic identities the construction relies on                                 |

---

## 9. The scoring frame for `OD-P16A-04`

| Class                 | Criteria                                                                          | Effect of a failure                                                     |
| --------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **MANDATORY**         | `IM-04`…`IM-38`                                                                   | **Rejection.** No compensating strength applies                         |
| **STRONGLY WEIGHTED** | `IM-39`…`IM-45`, maintenance record, advisory history, independent review history | Weighs against; may be accepted with a published gap and a dated remedy |
| **INFORMATIVE**       | Performance, ergonomics, language fit, community size                             | **Never decisive.** Recorded, and never the reason                      |

| ID      | Rule                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IM-46` | **Performance may not be the reason for a cryptographic choice** in this system — the same rule `PACK-16B-PARAMETER-SET-SPECIFICATION.md` §2 applied to the parameter decision |
| `IM-47` | **FIPS validation is evidence, not a verdict**, and specifically is not evidence of BSI compatibility (`VO-04` lineage)                                                        |
| `IM-48` | **A candidate with no independent review history is not disqualified**, but the gap is published and `TV-07`/`R-18` obligations rise accordingly                               |

---

## 10. What this document does not decide

```text
The library, language and runtime                → OD-P16A-04, PACK-16D
The ceremony device product                       → PACK-16D
Performance targets                                → PACK-16D
Hosting, deployment and operations                 → PACK-16D, PACK-17
Whether an in-house implementation is permitted    → OD-P16B-02
```

**`OD-P16A-04` IS NOT CLOSED BY THIS DOCUMENT.** It is given a standard.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
