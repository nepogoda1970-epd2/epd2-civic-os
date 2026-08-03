# PACK-16D — FIR Coverage Matrix

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment. A correction
of the PACK-16D reference-implementation candidate, not a new round.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Rules

| ID | Rule |
| -- | ---- |
| `FC-01` | The single register is `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`. This matrix is a view of it, never a second register |
| `FC-02` | **Permitted outcomes are exactly the six §55 allows**: `implemented in reference form`, `partially implemented`, `test harness complete`, `deferred to PACK-17`, `blocked pending external review`, `production hardening required`. No row here reads `implemented`, `closed` or `satisfied` |
| `FC-03` | **Eight items may not be closed by this round and are not:** external cryptographic review, independent implementation, production HSM, production key ceremony, formal verification, legal assessment, BSI `VO-08`, production deployment |
| `FC-04` | **New FIR IDs created by this round: none.** **FIR statuses changed by this round: none.** The register gained one round record (§1.23) and one paragraph under `FIR-ROADMAP-006`; no entry's `Status:` line was edited. The correction extended both, and still edited no `Status:` line |
| `FC-04d` | The **lockfile / provenance / matrix** correction changed no FIR outcome either, and could not: it corrected an acceptance-matrix status and recorded two environment blockers. Neither is a delivery. `FIR-SEC-002` in particular stays **blocked pending external review** — a round that could not even regenerate a lock file has certainly not produced cryptographic assurance |
| `FC-04c` | The **provider** correction changed no FIR outcome at all. It replaced a cryptographic primitive with a vetted library, pinned parameter provenance and extended cross-checks to the target profile — all of which improve the *evidence* behind `FIR-ROADMAP-006`, `FIR-SEC-002` and `FIR-TRUST-001` without moving any of them. `FIR-SEC-002` in particular stays **blocked pending external review**: swapping in OpenSSL reduces implementation risk and produces no assurance, which is what that entry is about |
| `FC-04b` | The first correction **improved the delivered form** of three entries — `FIR-ROADMAP-006`, `FIR-SEC-002`, `FIR-TRUST-001` — without changing any outcome to a value `FC-02` forbids. `FIR-TRUST-001` moved from `deferred to PACK-17` to `partially implemented`, which is the only outcome change in this document |

## 2. Entries this round touched

| ID | FIR entry | Outcome | What was actually delivered | What is missing |
| -- | --- | --- | --- | --- |
| `FC-05` | `FIR-ROADMAP-006` — PACK-16 Verifiable Voting Implementation | **implemented in reference form**, partially. Register status stays `approved` | The casting, publication, threshold-tally, election-record and verification path as **45 modules and 7 392 lines with 464 reference tests**, running on the **real `EPD2-CRYPTO-1` parameters**. `REPOSITORY_VERSION` reached this entry's target `0.16.0` | Audited protocol integration (`VO-08` open, `OD-P16D-02`); production data plane and authentication (`OD-P16D-08`); a production key ceremony with custody, authenticated channels and an HSM (`OD-P16D-11`); the authorisation of the signer registry itself (`OD-P16D-12`) |
| `FC-06` | `FIR-INV-002` — no `credential → ballot` linkage | **partially implemented** | Separate maps with no shared key; `LeafReservation` names a submission and never a capability; `FORBIDDEN_OUTBOX_FIELDS` scanned over every persisted row; tests assert no row pairs the two | An in-memory reference store is not a production data plane. The operator-with-database-access-to-both-stores residual is unchanged. **Not closed**, exactly as PACK-15 and PACK-16A/B/C left it |
| `FC-07` | `FIR-ROADMAP-007` — PACK-17 Independent Verification, Resilience & Incident Readiness | **deferred to PACK-17** | Nothing. This round produces the artefacts PACK-17 will verify, which is not the same as verifying them | Everything in the entry's scope |
| `FC-08` | `FIR-SEC-002` — cryptographic parameter assurance | **blocked pending external review** | The parameter validation mechanism, fail-closed, with expected bit lengths declared in code — **and the parameters themselves.** `EPD2-CRYPTO-1` carries the ElectionGuard 2.1 §3.1.1 standard baseline constants, transcribed from a primary source and verified by mathematics (`q = 2²⁵⁶−189`, `q \| p−1`, `p = qr+1`, `g^q = 1`, `p`/`q`/`r/2` probable-prime, both 256-bit one-runs, the `ln(2)` middle). The whole suite runs on them | **The assurance, not the arithmetic.** That these are the correct parameters *for a binding German election* is `VO-08`, and `VO-08` is open. No external cryptographer has reviewed the transcription or the implementation. The outcome stays `blocked pending external review` for exactly that reason |
| `FC-09` | `FIR-ASM-006`, `FIR-ASM-007` — assurance obligations PACK-16B deferred here and PACK-16C specified partially | **test harness complete**, for the parts that are testable in reference form | Fault injection at 11 points, 9 concurrency races, a **39-case** negative corpus, 23 stability vectors and **13 conformance entries across two independent oracles** — the harness an assurance argument would be built on | The assurance argument itself, which needs an external party |
| `FC-10` | `FIR-TRUST-001` — signature and timestamp framework | **partially implemented** | The signature half, now on a **vetted provider** rather than an implementation written here: Ed25519 (RFC 8032) checkpoint signing and verification, a `SignerRegistry` trust anchor that is supplied alongside the export rather than read out of it, declared-in-advance key rotation windows, and five distinct failure outcomes with distinct exit codes. Cross-checked against OpenSSL out-of-process | The timestamp half entirely — no trusted timestamping, no RFC 3161, no time authority. And the registry's *own* authorisation is outside the verifier's reach (`OD-P16D-12`). A framework also implies key custody and issuance, which `OD-P16D-11` says does not exist |
| `FC-11` | `FIR-SEC-001` — runbooks and rehearsal | **deferred to PACK-17** | Nothing | Everything |
| `FC-12` | `FIR-OSS-006` — delivery | **deferred to PACK-17** | Nothing | Everything |

## 3. Entries this round assessed and deliberately did not touch

| ID | Entry | Why untouched |
| -- | --- | --- |
| `FC-13` | `FIR-DATA-003` | Retention is governance, and `OD-P16A-07` owns the period. The reference implementation retains nothing beyond a test run |
| `FC-14` | `FIR-ROADMAP-005`, `FIR-ROADMAP-008`, `FIR-ROADMAP-009` | Out of this round's scope |
| `FC-15` | `FIR-ROLE-004`, `FIR-ROLE-006` | Role separation is enforced by the services PACK-12 and PACK-15 built, not by a reference cryptographic package |
| `FC-16` | `FIR-CAND-001`, `FIR-PROG-001`, `FIR-ASM-008`, `FIR-OSS-001` … `FIR-OSS-005` | Out of scope |
| `FC-17` | Every entry not named in this matrix | **Intentionally left unchanged.** Silence here means untouched, never satisfied |

## 4. The eight that may not be closed

Restated as a checklist, because §55 makes it the load-bearing part of this
document.

| ID | Item | State after PACK-16D | Evidence it is not closed |
| -- | --- | --- | --- |
| `FC-18` | External cryptographic review | **OPEN** | No external party reviewed anything this round |
| `FC-19` | Independent implementation | **OPEN** | Two independent *oracles* now exist — an out-of-process OpenSSL check and a Node.js verifier written from the written grammar — and one of them found a real ambiguity in the canonical encoding. **Two single-purpose oracles are not a complete second implementation.** The verifier remains independent of the *publisher* within one codebase, enforced by `ast` tests, which is a different and weaker property |
| `FC-20` | Production HSM | **OPEN** | No key material leaves process memory. Guardian shares and the checkpoint signing seed are ordinary Python objects; there is no HSM integration and no key-storage boundary at all (`OD-P16D-11`) |
| `FC-21` | Production key ceremony | **OPEN** | A Feldman-VSS DKG with 3-of-5 and 4-of-7 quorums now exists and runs, **in one process, with no authenticated channel between guardians, no air gap, no custody and no attestation**. That is a reference path for the protocol, not a key ceremony (`OD-P16D-11`) |
| `FC-22` | Formal verification | **OPEN** | No formal method was applied. `is_probable_prime()` is Miller–Rabin and its docstring says it is not a proof |
| `FC-23` | Legal assessment | **OPEN** | Untouched by this round |
| `FC-24` | BSI `VO-08` | **OPEN** | Named in the verifier's `NOT_CHECKED` list, so every verification result — including `VERIFIED` — carries it. No BSI conformity is claimed anywhere |
| `FC-25` | Production deployment | **OPEN** | Every module carries a not-production banner; `ReferenceApi` states `NOT PRODUCTION AUTHENTICATION` |

## 5. Arithmetic

| Outcome | Rows |
| --- | --- |
| implemented in reference form | 1 (`FC-05`) |
| partially implemented | 2 (`FC-06`, `FC-10`) |
| test harness complete | 1 (`FC-09`) |
| deferred to PACK-17 | 3 (`FC-07`, `FC-11`, `FC-12`) |
| blocked pending external review | 1 (`FC-08`) |
| production hardening required | 0 |
| **Total entries touched** | **8** |
| Entries assessed and untouched | 5 groups (`FC-13` … `FC-17`) |
| New FIR IDs | 0 |
| FIR statuses changed | 0 |
| Items in `FC-03` closed | **0 of 8** |

`FC-26` — **No row is `production hardening required`**, and that absence is
deliberate rather than an oversight: production hardening is not a state any
entry has reached, because no entry has reached a production candidate.

`FC-27` — **The correction closed none of the eight.** It closed three *open
decisions* (`OD-P16D-01`, `-07`, `-09`) and opened two new ones (`OD-P16D-11`,
`-12`). An open decision and an unclosable register item are different
objects, and `FC-03`'s eight are all still `OPEN` in §4 above. Where the
correction changed a §4 row, it changed the *evidence* column — what now
exists and why it is still not enough — never the `OPEN`.

`FC-29` — **`FIR-SEC-002` did not move a second time, even though the
primitive is now a vetted library and the provenance is pinned.** The
temptation is subtler than last round's: it is easy to read "we now use
OpenSSL and the parameters reconstruct offline" as partial assurance. It is
not. Assurance is a statement an external cryptographer makes about this
system; using a well-reviewed library means somebody else's code has been
reviewed, which is a different sentence. The entry stays blocked.

`FC-30` — **The obligation that was recorded against no FIR entry has been
discharged, and it is worth saying why it never became one.** `OD-P16D-16` —
the provider declared but not locked — was a packaging defect of this round,
not a roadmap item somebody owed. Filing it against a FIR entry would have
moved it from "unfinished here" to "scheduled elsewhere", which is exactly the
reclassification the first audit refused. It stayed unfiled, and it was closed
by running `uv lock`. `OD-P16D-17`, the upstream commit pin, was handled the
same way and closed the same way. **Neither closure moves a FIR outcome:** a
hash-pinned lock and a commit-pinned corroborating source are supply-chain and
traceability properties, and `FIR-SEC-002` is about parameter *assurance*.

`FC-28` — **`FIR-SEC-002` did not move even though the parameters arrived.**
The temptation to promote it was the strongest in this round and was
refused: the entry is about parameter *assurance*, and assurance is a
statement an external cryptographer makes, not one an implementation makes
about itself. Producing the constants and checking them arithmetically is a
precondition for that review, not a substitute for it.

## 6. What this document does not decide

```text
Whether FIR-ROADMAP-006 may move to `implemented`  → PACK-17, after review
Any FIR status change                               → the register, by decision
Retention periods                                   → OD-P16A-07, governance
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
