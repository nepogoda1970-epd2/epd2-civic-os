# PACK-16D — Scope and Implementation Boundary

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What this round is

PACK-16A chose the protocol. PACK-16B fixed the parameters, the key
ceremony and the trustee architecture. PACK-16C specified casting, the
receipt, the bulletin board and the election record. All three were
specification only.

**PACK-16D is the first PACK-16 round that ships code.** It exists to make
the three preceding specifications executable and independently checkable,
and to find out — by running them — which of their statements were
under-specified. Two real defects and one unsafe construction were found
this way; they are recorded in
`PACK-16D-IMPLEMENTATION-ARCHITECTURE.md` and
`PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md` rather than quietly repaired. A
third defect — an ambiguous canonical sequence and struct encoding, where
two different values shared a digest — was found by the correction round's
independent cross-implementation oracle and is recorded in
`PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` and the negative corpus.

Everything shipped this round lives under one package:

```text
services/voting-service/src/epd2_voting_service/reference/
```

```text
IN SCOPE
  canonical binary encoding (EPD2-ENC-1)
  domain-separation registry (EPD2-DS-1) and the hashing profile
  the EPD2-CRYPTO-1 target profile: artefact, fail-closed load,
    validation on every load, pinned digest, no fallback path
  parameter-profile loading and fail-closed validation
  randomness architecture, production and deterministic-test sources
  exponential ElGamal, homomorphic accumulation, bounded decoding
  disjunctive and Chaum-Pedersen proofs, prove and verify
  threshold guardians: Feldman-VSS distributed key generation, generic
    k-of-n with 3-of-5 and 4-of-7, Lagrange threshold decryption with
    per-share Chaum-Pedersen proofs, and ceremony verification
  checkpoint authenticity: Ed25519 (RFC 8032) signing and verification,
    a declared signer registry as trust anchor, and key-rotation windows
  Merkle tree with inclusion and consistency proofs
  ballot preparation, envelope, confirmation code, challenge opening
  the two atomic transactions and the reference store
  capacity plan, sealed batches, cover leaves, sealing
  bulletin board, checkpoints, outbox
  election record builder, the no-intermediate-tally gate, export
  reference verifier and its result-code table
  feature-flag guard, logging boundary, audit chain, schema registry
  fault-injection hooks, fixtures, scenarios and the test-vector catalogue
  three-class conformance evidence: internal-stability, primary-source
    and cross-implementation, with two independent out-of-process oracles
```

---

## 2. What this round explicitly does not do

Each row below is **not implemented**. Where a specification for it exists,
the specification is named; a specification is not an implementation and
must not be read as one.

| ID      | Not done this round                                                                                                                                                                                                                                                                                   | Where it is owned                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `SB-01` | **Production deployment.** Nothing here is deployed, deployable or intended to be deployed                                                                                                                                                                                                            | PACK-17, and governance                            |
| `SB-02` | **Real identity integration.** No connection to the PACK-14 identity and authentication surface exists in this package                                                                                                                                                                                | PACK-14, PACK-17                                   |
| `SB-03` | **Production eligibility and credential issuance.** The continuation capability is a test fixture: a string naming a row in the reference store                                                                                                                                                       | PACK-15, PACK-17                                   |
| `SB-04` | **Production key ceremony.** A _reference_ Feldman-VSS ceremony is executed, transcribed and verified by this code (`SB-13`), but it exchanges shares in-process with no authenticated channel, no ceremony script, no witnesses and no custody. None of that is a production ceremony (`OD-P16D-11`) | PACK-16B, PACK-17                                  |
| `SB-05` | **HSM procurement, custody or integration.** No hardware security module is used, addressed or simulated. Guardian secret shares and the board's Ed25519 signing seed live in process memory (`OD-P16D-11`)                                                                                           | PACK-16B key-custody requirements, PACK-17         |
| `SB-29` | **Authorisation of the signer registry.** The verifier checks a checkpoint against the registry it was given; establishing that the Election Board authorised that registry is outside its reach (`OD-P16D-12`)                                                                                       | Governance, PACK-17                                |
| `SB-06` | **Cloud or any other infrastructure deployment.** There is no infrastructure artefact, image, manifest or pipeline in this round's change set                                                                                                                                                         | PACK-17                                            |
| `SB-07` | **Mobile release.** No mobile artefact was built. The Node and frontend toolchain was not executed at all this round (`npm ci` returns HTTP 403 in this environment)                                                                                                                                  | PACK-17                                            |
| `SB-08` | **A real election user interface.** `api.py` is a local call surface for the harness and nothing else                                                                                                                                                                                                 | PACK-16C Verification Client architecture, PACK-17 |
| `SB-09` | **Legal certification or activation.** No certification claim of any kind is made, and public-election activation remains prohibited by default                                                                                                                                                       | Legal assessment, governance                       |
| `SB-10` | **Production monitoring, alerting or operations.** The logging boundary constrains what may be logged; it is not a monitoring system                                                                                                                                                                  | PACK-17                                            |
| `SB-11` | **Real election configuration.** Every manifest, context and parameter profile exercised this round is a fixture on a TEST profile                                                                                                                                                                    | Governance, PACK-17                                |
| `SB-12` | **All PACK-17 work** — independent verification operations, resilience, incident runbooks, production datastore isolation evidence, interoperability evidence                                                                                                                                         | PACK-17                                            |

---

## 3. Two boundary statements that must be in the body, not a footnote

### 3.1 Threshold DKG and the multi-guardian quorum are implemented — in reference form

`OD-P16D-07` is **closed**. The gap this section used to record is filled,
and it is replaced by the new state and by the boundary that new state has,
rather than deleted.

`reference/guardians/` implements a **Feldman verifiable-secret-sharing
distributed key generation** in the shape ElectionGuard uses. Guardian `i`
draws a polynomial of degree `k-1` over `Z_q`, publishes commitments to
every coefficient and a Schnorr proof of possession of its constant term;
guardian `l` verifies each received share against the sender's published
commitments, so a wrong share is _detectable_ rather than discovered at
tally time. The joint public key is the product of the constant-term
commitments, and **no party ever holds the joint secret**. Threshold
decryption is Lagrange interpolation in the exponent, each share carrying
a Chaum–Pedersen proof against a public share key derived from the
commitments alone. The engine is generic `k`-of-`n`; PACK-16B's 3-of-5
default and 4-of-7 high-assurance configurations are both exercised, and a
3-of-5 ceremony also runs on `EPD2-CRYPTO-1`.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SB-13` | **A PACK-16D document, code comment or test name may now state that threshold DKG and a `k`-of-`n` quorum are implemented, and only in _reference_ form.** The permitted §55 outcome is `implemented in reference form`, never `implemented`. What is implemented is the mathematics and the verification; what is not is any of the operational apparatus a real ceremony consists of                                                                                                                                                                                                                         |
| `SB-14` | **The quorum is not reducible at runtime and no compensation path exists.** `combine_shares` takes the policy from the ceremony transcript, never from its caller, and `QuorumPolicy.validate()` additionally rejects `2k <= n` so that two disjoint sets cannot each decrypt. `compensated_decryption_share()` exists **only** to raise `CompensatedDecryptionProhibited`, so the prohibition is discoverable in the code rather than only in a document; a test reads the threshold module's source and asserts the words `compensate`, `reconstruct_secret`, `escrow` and `break_glass` do not appear in it |
| `SB-30` | **The ceremony's boundary, stated as plainly as the gap it replaced.** Shares are exchanged **in-process**. There is no authenticated channel, no HSM, no air gap, no human ceremony script, no witness role and no key custody, and `run_ceremony()` returns the guardian secrets because a reference ceremony has to hand them to the test that will decrypt with them — which is exactly the property a production ceremony must not have. This is `OD-P16D-11`, new this round, and it is a production blocker rather than a simplification                                                                |

### 3.2 There is no production authentication

`OD-P16D-08`. `reference/api.py` performs **no authentication**. Its module
docstring says so, and `API_BANNER` prints
`REFERENCE API / NOT PRODUCTION AUTHENTICATION` for any harness that mounts
the surface. The `capability_reference` parameter is a test-only anonymous
capability fixture — a bare string, passed by the caller, naming a row in
the reference store.

| ID      | Rule                                                                                                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SB-15` | **The reference API is not an authentication boundary and may not be placed behind one and called production.** In a production system the equivalent value arrives through the PACK-14/PACK-15 credential boundary and is never a caller-supplied string |
| `SB-16` | `api.py` contains no business logic on purpose. An API layer that could decide anything would be a second place where an invariant lives. Any future production surface inherits this rule                                                                |

---

## 4. The boundary between "reference implementation" and "production code"

This is the distinction the whole round rests on, so it is stated as rules
rather than as adjectives.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SB-17` | **A reference implementation exists to be read, executed and disagreed with.** Its purpose is to make a specification checkable. Production code exists to run an election. The two have different obligations and this round discharges only the first                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `SB-18` | **Correctness of logic is claimed; correctness of execution environment is not.** The reference store is an in-memory structure guarded by a re-entrant lock. It demonstrates that the transaction _logic_ is race-free under the serialisation that store provides. It demonstrates **nothing** about a production datastore, where the same invariants must come from row-level locking or a serialisable isolation level (`OD-P16D-04`)                                                                                                                                                                                                                                                              |
| `SB-19` | **No side-channel property is claimed.** Python big-integer arithmetic and `pow(a, b, m)` are not constant-time. A production implementation needs a constant-time bignum path (`OD-P16D-05`). See `PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `SB-20` | **Secret material is not zeroized.** Python cannot reliably zeroize an immutable `int` or `bytes`, and the garbage collector may copy. This is stated as an unsolved limitation, not as a solved problem                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `SB-21` | **Test-only code is reachable only through an explicit two-guard path and never through production factories.** `select_source` accepts only the literal string `"production"`; `DeterministicTestRandomSource` requires both `allow_in_test=True` and the environment marker `EPD2_VOTING_REFERENCE_TEST_PROFILE=1`. That `select_source` cannot return a deterministic source is asserted by test, not by convention                                                                                                                                                                                                                                                                                  |
| `SB-22` | **Fault injection is a testing capability that production code cannot invoke.** Production modules depend only on the `FaultHook` protocol in `reference/hooks.py` and call it through `trip()`, which is a no-op when no hook is passed. There is no global registry and no environment switch. The only implementation that raises lives under `reference/testing/`                                                                                                                                                                                                                                                                                                                                   |
| `SB-23` | **Everything under `reference/testing/` is out of the production path by construction.** No module outside `testing/` imports it — this is checked, and the only occurrence of the string `reference.testing` outside that package is a prose reference in `hooks.py`'s docstring                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `SB-24` | **A fixture is never a default, and a test profile can never be mistaken for the target.** Both shipped `.params` files are named `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` and `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` and open with the banner `# TEST ONLY` / `# NOT EPD2-CRYPTO-1` / `# NOT ELECTIONGUARD 2.1 CONFORMANCE` / `# NOT PRODUCTION`. `TEST_ONLY_MARKER = "TESTONLY-NOTCONFORMANT"` and a test asserts every non-target profile id contains it. `production_use_permitted` is `False` on **every** registered profile, the target included                                                                                                                                               |
| `SB-25` | **A test profile may never stand in for the target, and no path lets it.** `EPD2-CRYPTO-1` now ships as a profile artefact and loads; `OD-P16D-01` is closed. What replaced the fail-closed-because-absent behaviour is a fail-closed-on-substitution one: `load_profile` contains no `except`, no default and no reference to a test profile — asserted structurally by a test — and `require_target_profile()` raises `ProfileSubstitutionError` for anything that is not the target. Validation runs on **every** load with no cached-validation path and no fast path keyed on the profile name, and the expected bit lengths come from `PROFILE_BIT_LENGTHS` in code rather than from the artefact |
| `SB-26` | **An unchecked claim never reads as a passed one.** The verifier adds `board.consistency_proofs` to `checks_run` only when proofs were actually supplied, adds `board.checkpoint_signatures` only when a signer registry and signed checkpoints were both supplied, and prints its **nine-entry** `NOT_CHECKED` list with **every** result, including `VERIFIED`. Two of the nine are new this round and replaced the entry that said checkpoint signatures were never verified: that the signer registry's own authorisation is outside the verifier's reach (`OD-P16D-12`), and that a valid signature is never evidence of a single view (`OD-P16D-06`)                                              |

---

## 5. `VO-08` — inherited, referenced, not touched

```text
VO-08  ElectionGuard 2.1 published parameter family
       versus BSI TR-02102-1 Remark 2.12 preference

Owner:        PACK-16B external cryptographic review
Assurance:    independent confirmation in PACK-17
NOT owned by: PACK-16D
Status:       OPEN
```

| ID      | Rule                                                                                                                                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SB-27` | **PACK-16D does not close, narrow, re-own or reinterpret `VO-08`, and makes no BSI-conformity claim.** One of the verifier's `NOT_CHECKED` entries names `VO-08` as open, so a reader of any verification result is told |
| `SB-28` | `ADR-102` is `proposed`. `ADR-099`, `ADR-100` and `ADR-101` all remain `proposed`; **`ADR-102` declares none of them accepted**                                                                                          |

---

## 6. What this round does not claim

Stated at the front so that no later document has to be read defensively.
Each line is a prohibition on every PACK-16D artefact, including code
comments and test names.

```text
NOT CLAIMED  BSI conformity, or that VO-08 is closed
NOT CLAIMED  constant-time execution or side-channel resistance, on any of
             the four surfaces the security document separates
NOT CLAIMED  interoperability with ElectionGuard — two independent oracles
             and primary-source parameters are not a comparison against
             another *complete* implementation (OD-P16D-02). Every vector
             in the stability catalogue remains self-generated on a TEST
             profile and says so in its own `source` field
NOT CLAIMED  that `uv sync --frozen`, `npm ci` or any npm script passed —
             none of them was executed (PyPI and the npm registry both
             return HTTP 403 in this environment)
NOT CLAIMED  that branch coverage was measured — no tool for it is
             installable here; line coverage was measured with the stdlib
             `trace` module
NOT CLAIMED  that the guardian ceremony is a production ceremony — it has
             no authenticated channel, no HSM, no air gap and no key
             custody (OD-P16D-11)
NOT CLAIMED  that the verifier can tell you the signer registry it was
             given was itself authorised (OD-P16D-12)
NOT CLAIMED  that cross-mirror split-view detection is implemented — the
             verifier detects equivocation within a single exported view,
             including between two validly signed checkpoints; gossip
             across mirrors is not implemented and the standards
             landscape is unsettled (OD-P16D-06)
NOT CLAIMED  production readiness, certification, or legal activation
NOT CLAIMED  that ADR-099, ADR-100, ADR-101 or ADR-102 is accepted
NOT CLAIMED  a FINAL PASS — this is a candidate requiring external review
```

---

## 7. Open decisions carried out of this round

| ID           | Decision left open                                                                                                                                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `OD-P16D-02` | **Narrowed, not closed.** Two independent out-of-process oracles and primary-source parameters now exist, but there is no comparison against another _complete_ ElectionGuard implementation. Interoperability remains unestablished |
| `OD-P16D-03` | Property tests are deterministic seeded loops, not `hypothesis` strategies — `hypothesis` could not be installed                                                                                                                     |
| `OD-P16D-04` | Concurrency evidence covers the reference in-memory store only, not a production datastore's isolation level                                                                                                                         |
| `OD-P16D-05` | Constant-time and side-channel behaviour is not claimed; Python big-integer arithmetic is not constant-time, and neither is the Ed25519 signing path                                                                                 |
| `OD-P16D-06` | Cross-mirror split-view detection (gossip) is not implemented                                                                                                                                                                        |
| `OD-P16D-08` | No production authentication; the reference API takes a test-only anonymous capability string                                                                                                                                        |
| `OD-P16D-10` | The reference tally handles one ballot style                                                                                                                                                                                         |
| `OD-P16D-11` | **New this round.** The reference ceremony exchanges shares in-process, with no authenticated channel, no HSM, no air gap and no key custody                                                                                         |
| `OD-P16D-12` | **New this round.** The signer registry's own authorisation is outside the verifier's reach: it checks a checkpoint against the registry it was given, not that the Election Board authorised that registry                          |

Three decisions this section used to carry are **closed by the correction
round**, and are recorded as closed rather than removed:

| ID           | Decision closed                                                                                                                                                                                                                                 |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P16D-01` | The `EPD2-CRYPTO-1` constants were not present and the profile failed closed. **Closed:** the profile artefact ships, loads under fail-closed validation with a pinned digest, and every test and E2E path can run on it                        |
| `OD-P16D-07` | The guardian model was single-guardian. **Closed:** Feldman-VSS DKG with generic `k`-of-`n`, 3-of-5 and 4-of-7, is implemented in reference form (`SB-13`, `SB-14`, `SB-30`)                                                                    |
| `OD-P16D-09` | Checkpoint signatures were carried but never verified. **Closed:** checkpoints are Ed25519-signed and the verifier checks them against a declared signer registry. The residual is `OD-P16D-12`, which is narrower and is not the same decision |

Closing an open decision is permitted only where the implementation
discharges it, and the three above are the only ones closed. The permitted
outcomes for a follow-up item are exactly: _implemented in reference form_,
_partially implemented_, _test harness complete_, _deferred to PACK-17_,
_blocked pending external review_, _production hardening required_.
External cryptographic review, independent implementation, production HSM,
production key ceremony, formal verification, legal assessment, `VO-08`
and production deployment all remain **open**.

---

## 8. What this document does not decide

```text
Layering, placement and dependency direction   → PACK-16D-IMPLEMENTATION-ARCHITECTURE.md
Language and dependency policy                  → PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md
Cryptographic module surfaces and rules         → PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md
Parameter appropriateness                       → VO-08, PACK-16B external review
Interoperability with a complete implementation → OD-P16D-02, PACK-17
Production datastore isolation                  → OD-P16D-04, PACK-17
Production ceremony, custody and HSM            → OD-P16D-11, PACK-16B, PACK-17
Authorisation of the signer registry            → OD-P16D-12, PACK-17, governance
Production authentication surface               → OD-P16D-08, PACK-14, PACK-15, PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
