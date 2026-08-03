# PACK-16B — Ceremony Transcript Specification

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What the transcript is, and what it is not

The **ceremony transcript** is EPD²'s append-only public record of how a
context's keys came to exist. It is **not** the election record: the
election record is defined by the upstream specification and consumed by a
conforming verifier, and it does not contain the encrypted shares, the
commitment round or the complaints `[F-12]`.

```text
ELECTION RECORD     upstream-defined · consumed by any conforming verifier
CEREMONY TRANSCRIPT EPD²-defined · consumed by auditors, guardians and the public
                    · a superset in ceremony scope, disjoint in ballot scope
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CT-01`  | The transcript **contains** the election record's guardian-record fields, and adds the EPD² material of §3          |
| `CT-02`  | **No conforming verifier is required to read the transcript** (`DS-13`). Verification of the outcome does not depend on it |
| `CT-03`  | The transcript is published on the bulletin board, under the ceremony's own namespace, and mirrored (`BB-07`)       |
| `CT-04`  | Transcript hashes use the **EPD² hash domain** `H_X` and string tags (`DS-09`…`DS-11`)                              |

---

## 2. Required properties

```text
canonical · append-only · signed · independently verifiable
archivable · mirrorable · non-repudiable
```

| ID       | Property                | Requirement                                                                                            |
| -------- | ----------------------- | -------------------------------------------------------------------------------------------------------- |
| `CT-05`  | **Canonical**           | One byte encoding per content, under `EPD2-ENC-1`; **non-canonical is rejected, never normalised** (`FS-12`) |
| `CT-06`  | **Append-only**         | No entry is modified or removed. A correction is a new entry that references the earlier one (`BB-01`)  |
| `CT-07`  | **Signed**              | Chained, signed checkpoints, with the signing key distinct from every other key in the architecture (`BB-06`) |
| `CT-08`  | **Independently verifiable** | Every published claim is checkable from published data by a party with no EPD² credential          |
| `CT-09`  | **Mirrorable**          | Published to at least two mirrors under distinct organisational control (`BB-07`, `BB-28`)             |
| `CT-10`  | **Archivable**          | Verifiable after archival with no live service (`BB-20`, `CA-20`)                                       |
| `CT-11`  | **Non-repudiable**      | Every guardian act is bound to that guardian's published key, so that a guardian cannot later deny a published contribution |

`CT-11` has an honest limit worth stating here rather than in a footnote:
the share ciphertexts carry a proof of knowledge of the *encryption nonce*,
which binds the ciphertext to someone who formed it — but the sender's
identity is a hash input rather than a signed assertion `[F-13]`.
Guardian-to-guardian authenticity therefore rests on the record-comparison
step, exactly as the companion paper states `[F-14]`. **Non-repudiation is
strong for published contributions and weaker for the share exchange**, and
`CT-25` records the consequence.

---

## 3. Contents

### 3.1 Context and parameters

```text
election context identifier
profile identifier                       EPD2-HOM-1
parameter_set_id                         EPD2-CRYPTO-1
specification lineage, version and DIGEST
domain-separation registry version       EPD2-DS-1
encoding version                         EPD2-ENC-1
randomness profile                       EPD2-RND-1
manifest digest
quorum rule                              k of n
```

### 3.2 Guardians

```text
guardian roster: index, name, organisation
guardian organization identifiers
independence declarations
pairwise independence assessment outcomes
composition-test outcome
Auditor concurrence on composition
accessibility assistants, where any, named as assistants (KY-41)
```

### 3.3 Ceremony material

```text
ceremony session identifier
software build identity of the ceremony application
device attestation outcomes (outcome only, not device identifiers)
randomness health-test outcomes (outcome only)

EPD² pre-commitments  C_1 … C_n                       [EPD² addition]
guardian public contributions: K_{i,j}, K̂_{i,j}, κ_i
proofs of possession (aggregated Schnorr proofs)
commitment/opening match verdicts                      [EPD² addition]

encrypted shares E_ℓ(P_i(ℓ), P̂_i(ℓ)) for every ordered pair,
   with their nonce proofs                             [EPD² addition]
share verification verdict per ordered pair            [EPD² addition]

complaints, with evidence references
complaint adjudications and their grounds
disqualifications and their grounds

joint public keys K and K̂
extended base hash H_E
guardian record comparison hash H_G
```

### 3.4 Acceptance

```text
per-guardian transcript confirmations (all n)
Independent Auditor verdict and verifier version
Election Board acceptance
signed ceremony checkpoint
ACTIVATION LOCK record, with coarsened timestamp
```

---

## 4. Prohibited content — normative

The transcript **must not contain**, in any field, in any encoding, or in a
form from which they can be derived:

```text
private keys of any kind
private polynomial coefficients
plaintext shares
Schnorr commitment nonces
share-encryption nonces
recovery secrets of any kind
any ballot-side identifier
any credential-side identifier
any continuation-capability reference
any voter identity, roll or participation data
identity data about guardians beyond name, organisation and role
device serial numbers, MAC addresses or hardware identifiers
network addresses
uncoarsened timestamps
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CT-12`  | Every entry passes a prohibited-content check **before publication**; publication is **refused**, never redacted afterwards (`BB-21`) |
| `CT-13`  | Timestamps are coarsened to the context's `timestamp_granularity`                                                  |
| `CT-14`  | Device attestation records an **outcome**, not an identifier — a device identifier is a correlation handle          |
| `CT-15`  | Randomness health tests record an **outcome**, never a sample, a seed or an output (`RN-10`)                        |
| `CT-16`  | **The transcript touches no ballot-side and no credential-side value.** The ceremony and the ballot domain share nothing but the joint public key |

`CT-16` is the PACK-15 boundary applied to this document: a ceremony
transcript that named a voter, a credential or a ballot would be the pair
that must never exist.

---

## 5. Structure and checkpoints

```text
Entries are appended in canonical order within a ceremony session.
Every entry carries: session id, phase number, entry index,
                     entry type, content, content hash.
A checkpoint carries: the running chain hash, the entry range,
                      a coarsened time, and a signature.
Checkpoints chain: each includes the previous checkpoint's hash.
```

| ID       | Rule                                                                                                    |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| `CT-17`  | A checkpoint is published **at the end of every phase**, and at minimum after phases 7, 11, 13, 14, 19 and 20 |
| `CT-18`  | The chain is verifiable from the first entry with no privileged access                                   |
| `CT-19`  | Mirrors publish their own signature over each checkpoint they have seen (`BB-30`)                        |
| `CT-20`  | **Mirror divergence halts the ceremony** (`BB-31`), and the divergent checkpoints are published in full   |
| `CT-21`  | The final checkpoint — the activation lock — is published on **every** mirror before the context may open |

---

## 6. What a reader can verify, and what they cannot

The honest inventory, because a transcript that implies more than it proves
is worse than a shorter one.

| Claim                                                              | Verifiable by anyone? | How                                                            |
| ------------------------------------------------------------------ | --------------------- | ---------------------------------------------------------------- |
| The parameters are the published ones                              | **Yes**               | Re-derive from the published rule (`TV-01`)                     |
| Each guardian knows the secret behind its commitments              | **Yes**               | The aggregated Schnorr proofs                                   |
| The joint key is the product of the published contributions        | **Yes**               | Recompute `K`, `K̂`                                             |
| Each guardian published only after all commitments                 | **Yes**               | Commitment/opening comparison (`KY-10`)                         |
| A share ciphertext is the one its sender published                 | **Yes**               | Hash comparison against the transcript (`KY-15`)                |
| A share ciphertext was formed by someone knowing its nonce         | **Yes**               | The nonce proof                                                 |
| **The plaintext inside a share is correct**                        | **No, not without the recipient opening it** | Complaint model §5                       |
| The guardians are actually independent                             | **No** — organisational, declared, assessed | `GI-01`…`GI-13`                          |
| The randomness was sound                                           | **No** — undetectable in either direction  | Randomness architecture §7                |
| A guardian's device was not compromised                            | **No**                | Attestation attests to itself                                   |
| No `k` guardians colluded                                          | **No** — undetectable | `T-P16A-19`; prevention only                                    |

| ID       | Rule                                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CT-22`  | The transcript **publishes this table with itself** — what it does not establish, alongside what it does (`BB-37`) |
| `CT-23`  | No transcript field, label or summary may imply a property from §6's lower half                              |
| `CT-24`  | A transcript that verifies establishes that the ceremony was **procedurally correct as recorded**; it does not establish that the guardians were honest, independent in fact, or well-equipped |
| `CT-25`  | Where non-repudiation is weaker — the share exchange (`CT-11`) — the transcript says so at the point of publication |

---

## 7. Retention and archival

| ID       | Rule                                                                                                  |
| -------- | --------------------------------------------------------------------------------------------------------- |
| `CT-26`  | The transcript is retained with the election record and archived with it (`BB-19`)                     |
| `CT-27`  | It verifies after archival with **no live EPD² service** (`BB-20`)                                     |
| `CT-28`  | Retention is governed by `OD-P16A-07`, which this round does not close — but the transcript contains **no ciphertext of a ballot**, so the long-term secrecy tension of `T-P16A-40` applies to it only through the joint public key, which is public by design |
| `CT-29`  | Destruction attestations (`GL-16`, `GL-17`) are appended to the transcript after the ceremony and after retirement, so the record of what was destroyed outlives the material |

`CT-28` is a small but real result: the ceremony transcript is **not** a
long-term secrecy liability in the way the published ballot set is, because
everything in it is either public by construction or a ciphertext readable
only by a guardian whose share is destroyed on retirement.

---

## 8. What this document does not decide

```text
The transcript wire format and serialization  → PACK-16C
The checkpoint interval and signing scheme     → PACK-16C
The mirror synchronisation protocol            → PACK-16C
Retention periods                              → OD-P16A-07, PACK-09
The publication interface                      → FRONT-PACK
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
