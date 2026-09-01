# PACK-16B — Parameter Set Specification

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The selection

```text
SELECTED PARAMETER PROFILE

  EPD2-CRYPTO-1

  = the ElectionGuard 2.1.0 standard baseline parameters, unmodified,
    bound into an EPD² profile that adds obligations, pins provenance,
    fixes dates and changes no value.
```

**Nothing is changed. That is the decision, and it took the most work to
justify.**

---

## 2. The finite-field versus elliptic-curve decision

PACK-16A recorded a tension between the specification's fixed finite-field
parameters and German cryptographic guidance, and required this round to
choose explicitly among four options.

```text
A. Preserve the ElectionGuard 2.1 finite-field parameter profile.   ← SELECTED
B. Define a formally analysed EPD²-compatible finite-field profile.    rejected
C. Define an elliptic-curve adaptation.                                rejected
D. Block progression because none is currently justified.              rejected
```

### 2.1 Option assessment

| Criterion                               | **A — preserve**                                                                                                                       | B — own finite-field profile                                    | C — elliptic-curve adaptation                                                                                                    | D — block |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------- |
| Security-proof reuse                    | **Full** — the published IND-CPA theorem applies as stated `[F-17]`                                                                    | Partial; the theorem's parameter hypothesis must be re-argued   | **None** — a new group is a new analysis                                                                                         | n/a       |
| Verifier interoperability               | **Expected, not demonstrated** — no verifier-consumed field is changed; independent verifier testing (`TV-07`, `TV-19`) is outstanding | **Broken** — Verification 1.B–1.D require bit-equality `[F-05]` | **Broken**, and additionally the record format changes                                                                           | n/a       |
| `BM-28` (a verifier EPD² did not write) | **Satisfiable**                                                                                                                        | **Unsatisfiable without commissioning one**                     | **Unsatisfiable without commissioning one**                                                                                      | n/a       |
| Implementation maturity                 | Poor but shared with everyone else                                                                                                     | Worse — no implementation would exist at all                    | Worse still                                                                                                                      | n/a       |
| Constant-time implementation            | Modular exponentiation; well-understood                                                                                                | Same                                                            | Better in principle; but a new implementation is a new risk                                                                      | n/a       |
| Side-channel risk                       | Known class, 4096-bit exponentiations                                                                                                  | Same                                                            | Different class, and unassessed in this construction                                                                             | n/a       |
| Encoding complexity                     | Fixed 512/32/4 bytes, specified `[F-09]`                                                                                               | Same lengths                                                    | **Every length changes**; every domain-separation input changes                                                                  | n/a       |
| Subgroup checks                         | `x^q mod p = 1`, specified and verifier-enforced `[F-05]`                                                                              | Same                                                            | Point validation and cofactor handling must be re-specified                                                                      | n/a       |
| Cofactor risk                           | Cofactor `r` large, membership check mandatory                                                                                         | Same                                                            | Small-cofactor pitfalls are a distinct and live attack class                                                                     | n/a       |
| Challenge derivation                    | `H_q` valid as specified                                                                                                               | Valid if `q` unchanged                                          | **`H_q` must be redesigned** — it is _"tailored to the specific choice of q = 2²⁵⁶ − 189"_ `[F-07]`                              | n/a       |
| German-guidance alignment               | **Meets** verified recommendations (assessment §3)                                                                                     | Meets, at best equally                                          | Would meet; but BSI's recommended curve set does not include the curves an EG-style adaptation would most naturally use `[F-23]` | n/a       |
| Performance                             | Slowest of the three                                                                                                                   | Same                                                            | **Fastest**                                                                                                                      | n/a       |
| Browser feasibility                     | 4096-bit exponentiation in a client is heavy — real, and treated in `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` §5                | Same                                                            | Better                                                                                                                           | n/a       |
| Independent verifier feasibility        | **Best** — the specification chose integers _"to make construction of election verifiers as simple as possible"_ `[F-02]`              | Good                                                            | Worse — a bespoke verifier, maintained by EPD² indefinitely                                                                      | n/a       |
| Long-term archival verification         | **Best** — an unmodified third-party verifier reads a 2030 record in 2045                                                              | Good                                                            | **Worst** — archived records depend on EPD²'s own verifier surviving                                                             | n/a       |
| Formal-analysis requirement             | Inherited work applies; the profile as composed still needs review (`VO-05`)                                                           | A new analysis                                                  | **A full new analysis**                                                                                                          | n/a       |

### 2.2 Why A

Three reasons, in order of weight.

**First, the parameters are not a variable.** Note 3.1 states that this
version _"fixes the parameters as above"_, and Verification 1 requires
bit-equality `[F-04]`, `[F-05]`. Options B and C are therefore not
parameter choices at all — they are **protocol adaptations** that fork the
verifier ecosystem. Presenting either as "selecting parameters" would be
exactly the silent substitution `PACK-16B-SCOPE-AND-BOUNDARY.md` §1
forbids.

**Second, verifiability is the property this architecture is built on.**
`BM-26` requires the record to be verifiable without trusting any EPD²
component; `BM-28` requires a verifier written by someone else; `BB-33` and
`BB-34` require the same of the board. A group change makes all three
depend on EPD² commissioning and maintaining a verifier — which converts an
independence property into a funding commitment. The specification's own
stated reason for choosing integers over curves is _"to make construction
of election verifiers as simple as possible"_ `[F-02]`, which is the same
priority, arrived at independently.

**Third, the guidance is met.** The assessment's verified figures — 4096
against a recommended 3000, 256 against a break-even of 240 and a
recommendation of 250 — leave no margin argument for a change
(`PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` §3).

**Option C was not rejected because it is slower to build.** It was
rejected because it is a different protocol wearing the word "parameters",
and because the round is explicitly forbidden from choosing an
elliptic-curve adaptation on performance grounds.

**Option D — blocking — was assessed and rejected** because none of the six
blocker conditions in `PACK-16B-SCOPE-AND-BOUNDARY.md` §7 is met. Blocking
when nothing is broken would be as dishonest as proceeding when something
is.

### 2.3 What would make this decision wrong

```text
A published break of the construction or of these parameters.
A first-hand reading of BSI guidance showing q = 256 bits is insufficient.
Arrival of a quantum-safe successor with verifier support — which makes
   a successor profile right, not this decision wrong.
Abandonment of the specification without a successor (RB-06).
A cryptographic reviewer finding the profile-as-composed unsound (VO-05).
```

---

## 3. `CryptographicParameterSet` — the governed registry

**Specification-level only. No registry is implemented, no schema is
written, and the Canonical Schema Registry is not modified.**

### 3.1 Fields

```text
parameter_set_id                  profile_id
specification_lineage             specification_version
specification_digest              status
group_definition                  generator_definition
hash_suite                        kdf_suite
domain_separation_registry_version
encoding_version                  randomness_profile
minimum_verifier_version          activation_date
deprecation_date                  prohibition_date
approval_evidence                 security_review_reference
migration_rule
```

`specification_digest` is an EPD² addition to the required field list, and
it exists because the upstream specification has **no errata process and
marks two versions simultaneously "Recommended"** `[F-30]`. A lineage
reference that is not pinned by digest is a reference to a moving target.

### 3.2 The instance

| Field                                | Value                                                                                                                                                                                                          |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `parameter_set_id`                   | `EPD2-CRYPTO-1`                                                                                                                                                                                                |
| `profile_id`                         | `EPD2-HOM-1`                                                                                                                                                                                                   |
| `specification_lineage`              | ElectionGuard Design Specification                                                                                                                                                                             |
| `specification_version`              | `2.1.0`, title page **"Version 2.1.0 / August 12, 2024"**, 110 pages                                                                                                                                           |
| `specification_digest`               | SHA-256 `a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936`, 813 495 bytes; retrieved from the canonical release asset. **Independent second-path confirmation is `VO-04` and is not yet done** |
| `status`                             | `under_review` — it becomes `approved` only on acceptance of `ADR-100`, and `active` only through the governance gate                                                                                          |
| `group_definition`                   | Prime-order subgroup `Z_p^r` of `F_p*`; `p` the 4096-bit constant of spec §3.1.1; `q = 2²⁵⁶ − 189`; `r = (p−1)/q` with `r/2` prime                                                                             |
| `generator_definition`               | `g = 2^r mod p`                                                                                                                                                                                                |
| `hash_suite`                         | `H = HMAC-SHA-256` with a fixed 32-byte key slot; `H_q = H(...) mod q`                                                                                                                                         |
| `kdf_suite`                          | NIST SP 800-108r1 counter-mode HMAC, with the specification's label and context strings                                                                                                                        |
| `domain_separation_registry_version` | `EPD2-DS-1` — the 27-entry table of spec §5.5 with the two errata resolved (`PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` §7)                                                                                |
| `encoding_version`                   | `EPD2-ENC-1` — fixed-length big-endian, 512 / 32 / 4 bytes, length-prefixed variable data, **non-canonical rejected**                                                                                          |
| `randomness_profile`                 | `EPD2-RND-1` (`PACK-16B-RANDOMNESS-ARCHITECTURE.md`)                                                                                                                                                           |
| `minimum_verifier_version`           | A verifier conforming to ElectionGuard specification `2.1.0`                                                                                                                                                   |
| `activation_date`                    | **unset** — set by the governance gate, never by configuration                                                                                                                                                 |
| `deprecation_date`                   | **2030-12-31** for high-assurance contexts; **2031-12-31** otherwise `[F-25]`                                                                                                                                  |
| `prohibition_date`                   | **2032-12-31** `[F-20]`                                                                                                                                                                                        |
| `approval_evidence`                  | `ADR-100` (status `proposed`) plus the governance-gate record. **Not present**                                                                                                                                 |
| `security_review_reference`          | **none — `VO-05` is open and blocks activation**                                                                                                                                                               |
| `migration_rule`                     | A successor profile must exist before `deprecation_date`; migration never re-opens an archived record (`PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` §6)                                                           |

### 3.3 Statuses

```text
draft → under_review → approved → active
                                    ↓
                              deprecated → retired_for_new_contexts
                                    ↓
                              verification_only
       (any state) → prohibited        [emergency, one-way]
```

| Status                     | New contexts | Running contexts      | Archived verification         |
| -------------------------- | ------------ | --------------------- | ----------------------------- |
| `draft`                    | no           | n/a                   | n/a                           |
| `under_review`             | no           | n/a                   | n/a                           |
| `approved`                 | no           | n/a                   | n/a                           |
| `active`                   | **yes**      | yes                   | yes                           |
| `deprecated`               | **no**       | **yes — they finish** | yes                           |
| `retired_for_new_contexts` | no           | none remain           | yes                           |
| `verification_only`        | no           | none remain           | **yes**                       |
| `prohibited`               | no           | **see §5**            | yes, with a published warning |

**`approved` does not authorise use.** Only `active` does, and the
transition from `approved` to `active` is the governance gate of
`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8. A parameter set cannot activate
itself by being approved, and an ADR cannot activate one by being accepted.

---

## 4. Invariants

| ID      | Invariant                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------ |
| `PS-01` | A parameter set is **immutable after `approved`**. A change is a new `parameter_set_id`, never an edit                   |
| `PS-02` | An election context binds **exactly one** parameter set                                                                  |
| `PS-03` | The binding is **immutable after the context reaches `configured`**                                                      |
| `PS-04` | **No silent default.** A context with no declared parameter set fails configuration validation                           |
| `PS-05` | **No environment-dependent selection.** The set may not vary by deployment, host, tenant, build or environment variable  |
| `PS-06` | **No feature-flag downgrade.** No flag, toggle, header or configuration may substitute a weaker set (`FIR-INV-006`)      |
| `PS-07` | An **unknown** parameter set is rejected, never defaulted                                                                |
| `PS-08` | A **prohibited** parameter set is rejected in every state and every code path                                            |
| `PS-09` | A **deprecated** set cannot start a new context; contexts already open finish under it                                   |
| `PS-10` | A **historical verifier must still interpret archived records** — verification capability is never withdrawn             |
| `PS-11` | The parameter set, its digest and its provenance are **published in the election manifest before `issuance_open`**       |
| `PS-12` | The set is **published on the bulletin board** with the manifest (`BB-16`) and reproduced in the ceremony transcript     |
| `PS-13` | Approval of a parameter set is an **Election Board act with Independent Auditor concurrence**, never an operator setting |
| `PS-14` | `status` transitions are **monotonic** except that `prohibited` is reachable from any state and is **one-way**           |
| `PS-15` | A parameter set whose `security_review_reference` is empty **may not reach `active`**                                    |

`PS-15` is the one most likely to be inconvenient, and it is deliberate:
it is what stops `EPD2-CRYPTO-1` from being used before `VO-05` is done.

---

## 5. Emergency prohibition

A parameter set may be moved to `prohibited` at any time by the Election
Board with Independent Auditor concurrence, on published evidence.

| Situation                                | Effect                                                                                                                                                                                                                                                                                                   |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No context is open                       | No new context may use it. Nothing else happens                                                                                                                                                                                                                                                          |
| A context is **configured but not open** | The context is discarded and reconstituted under a successor set — never re-keyed in place                                                                                                                                                                                                               |
| A context is **open for voting**         | **Governance decision, bounded**: `pause` → then `abort` and `re-run`, or `continue to closure with a published prohibition notice`. There is no third option, and `continue` is permissible only where the prohibition ground does not bear on the confidentiality or integrity of ballots already cast |
| A context is **closed but not tallied**  | The tally proceeds — the ballots are already fixed — and the result carries a published prohibition notice                                                                                                                                                                                               |
| A context is **archived**                | Verification capability is retained (`PS-10`). The archive carries the notice                                                                                                                                                                                                                            |

**Prohibition never triggers re-keying of a running election** — `KC-12`
and `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` §6 forbid it, because a
key rotation mid-election either invalidates cast ballots or requires
decrypting them.

---

## 6. What is deliberately absent from this specification

```text
No alternative parameter set, because the upstream specification permits none.
No "reduced" or "test-scale" production parameter set.
   The appendix parameters of the specification are NOT conforming and are
   permitted only in the test and rehearsal domains (ceremony spec §9).
No per-context tuning of any cryptographic value.
No negotiation of any kind, at any layer, between any two parties.
No parameter selection reachable from configuration, environment or flag.
```

**SPECIFIED. SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL
CRYPTOGRAPHIC REVIEW. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
