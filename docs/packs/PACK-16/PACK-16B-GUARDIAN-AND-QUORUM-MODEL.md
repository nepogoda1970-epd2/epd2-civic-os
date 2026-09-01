# PACK-16B — Guardian and Quorum Model

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
DEFAULT PROFILE            k = 3 of n = 5
HIGH-ASSURANCE PROFILE     k = 4 of n = 7
SMALL-ELECTORATE PROFILE   k = 3 of n = 5   — identical to default, by rule
```

**There is no smaller profile, and none may be created.**

| Bound              | Value                                                                     | Basis                                                                                                                                                            |
| ------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| minimum `n`        | **5**                                                                     | `TP-01` (k ≥ 3) together with `TP-03` (n − k ≥ 2) forces n ≥ 5                                                                                                   |
| maximum `n`        | **9**                                                                     | Beyond nine the ceremony's coordination cost and the independence requirement of §4 stop being satisfiable in practice; a larger `n` needs its own justification |
| minimum `k`        | **3**                                                                     | `TP-01`                                                                                                                                                          |
| permitted formulas | `k = 3, n = 5` · `k = 4, n = 7` · `k = 5, n = 9` (permitted, not default) | each satisfies `TP-01`…`TP-07`                                                                                                                                   |

The specification itself constrains only `1 ≤ k ≤ n` `[F-18]` — _"the only
constraint"_. Everything above is EPD²'s, and `TP-01`…`TP-07` are why.

---

## 2. What k and n actually control

Getting this backwards is the standard error, so it is stated before the
comparison.

| Quantity  | Controls                                                                                                                                                     |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **k**     | **Confidentiality.** `k` colluding guardians can decrypt individual ballots. Raising `k` raises the cost of collusion                                        |
| **n − k** | **Availability.** Up to `n − k` guardians may be absent at decryption and the result is still obtainable. Lowering `k` or raising `n` improves survivability |
| **n**     | The size of the pool from which both are drawn, and the ceremony's coordination cost                                                                         |

The specification says the same thing in its own words: _"The reason for
not setting the quorum value k too low is that it will also be possible for
k guardians to jointly decrypt individual ballots"_ `[F-18]`, and its
accompanying note spells out the coercion consequence — any `k`-set that
can decrypt individual ballots, combined with a voter's confirmation code,
can coerce that voter `[F-18]`.

**That note is why `k` cannot be 2.** A two-party quorum is one meeting.

---

## 3. The comparison

| Option     | Collusion needed to break secrecy | Absences tolerated | Independence achievable?                                                     | Ceremony cost | Decryption cost | Human-error exposure             | Verdict                                                         |
| ---------- | --------------------------------- | ------------------ | ---------------------------------------------------------------------------- | ------------- | --------------- | -------------------------------- | --------------------------------------------------------------- |
| **2-of-3** | **2**                             | 1                  | Weak — two people can be one lunch                                           | lowest        | lowest          | high — one loss leaves no margin | **REJECTED** — violates `TP-01` (k ≥ 3) and `TP-03` (n − k ≥ 2) |
| **3-of-5** | **3**                             | **2**              | Achievable — 3 organisations minimum                                         | moderate      | moderate        | moderate — two may fail          | **SELECTED as default**                                         |
| **4-of-7** | **4**                             | **3**              | Achievable, harder                                                           | high          | high            | low                              | **SELECTED as high-assurance**                                  |
| **5-of-9** | **5**                             | **4**              | Hard — nine independent bodies is a real constraint for a party organisation | highest       | highest         | lowest                           | **PERMITTED**, not default — §3.2                               |

### 3.1 Why 3-of-5 is the default

**Collusion cost.** Three guardians must agree, and under `TP-02` they
cannot all come from one organisation — so breaking secrecy requires
cross-organisational conspiracy among publicly named parties `[F-18]`.
That is a materially different act from an insider decision.

**Availability.** Two guardians may be unavailable at decryption and the
result is still produced. Given that absence is the failure this model
sees most often — illness, travel, a lost device — a margin of two is the
difference between an inconvenience and an annulled election.

**Achievability.** Five guardians from at least three genuinely independent
organisations is demanding but reachable for a party that wants to hold
binding internal votes. Nine is not, for most of them, and a quorum model
nobody can staff is a quorum model that gets quietly relaxed.

**Symmetry with the failure model.** `n − k = 2` means the quorum-loss path
of `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` §5 requires **three**
simultaneous losses. That is rare enough to be a genuine incident and
common enough to be worth planning for.

### 3.2 When 4-of-7 applies, and when 5-of-9 may

| Context class                                              | Profile                               |
| ---------------------------------------------------------- | ------------------------------------- |
| Advisory consultation, non-binding                         | 3-of-5                                |
| Binding party resolution                                   | 3-of-5                                |
| Internal board election (`geheim` under § 15 Abs. 2 PartG) | **4-of-7**                            |
| Constitutional-amendment vote                              | **4-of-7**                            |
| Any context the Election Board declares high-assurance     | **4-of-7**                            |
| Anything for which 4-of-7 is judged insufficient           | 5-of-9, with a recorded justification |

**A context may move up a profile and never down.** Downgrading is a
`k`-reduction under another name and is refused by `GQ-05`.

### 3.3 Why not more guardians for small electorates

`TP-06` states it and this document keeps it: **`k` and `n` are not reduced
for a small electorate.** The temptation runs the other way — a vote among
nineteen people feels like it should not need five guardians from three
organisations — and the temptation is wrong. In a small body the
consequences of a decryption leak are individual and attributable, so the
threshold matters more, not less.

The small-electorate profile is therefore **identical to the default**, and
saying so explicitly is the point.

---

## 4. Composition rules

| ID      | Rule                                                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GQ-01` | **No single organization may control a quorum.** With `k = 3`, no organisation supplies 3 guardians; with `k = 4`, none supplies 4 (`TP-02`)                                      |
| `GQ-02` | **No single natural person may control more than one guardian**, directly or through a role, a device or a delegation                                                             |
| `GQ-03` | Guardians are drawn from at least **`k` organisationally distinct bodies** (`KC-05`)                                                                                              |
| `GQ-04` | `k` and `n` are fixed in the manifest **before `issuance_open`** and are immutable for the context (`TP-05`)                                                                      |
| `GQ-05` | **`k` may never be reduced**, and `n` may never be reduced below `k + 2`, at any time, for any reason, by any authority                                                           |
| `GQ-06` | Guardian **identity and organisation are published** in the manifest (`TP-07`). A secret guardian is not a check on anyone                                                        |
| `GQ-07` | A **candidate** in a context may hold no role in that context, guardian included (`RS-04`)                                                                                        |
| `GQ-08` | Guardian appointment is **per context**. A guardian for one context is not thereby a guardian for another (`RS-05`)                                                               |
| `GQ-09` | **Keys are not reused across contexts.** The specification permits limited reuse `[F-18]`; EPD² prohibits it — see §4.1                                                           |
| `GQ-10` | Where an organisation cannot supply guardians meeting §4 and `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md`, the correct outcome is **not to hold the vote electronically** (`RS-07`) |

### 4.1 Why key reuse is prohibited although the specification permits it

The specification states that where the same guardians support multiple
elections at the same threshold, _"the generated keys and key shares may be
reused across a small number of elections, although it is preferred to
generate new keys for each election"_ `[F-18]` — with no bound on "small
number".

EPD² prohibits reuse outright, for three reasons:

1. **Cross-context linkage.** A key shared between two contexts is a value
   stable across contexts, which `T-P16A-09` treats as an attack surface
   and `FIR-INV-001` forbids in general.
2. **Compromise blast radius.** A quorum compromise discovered in 2029
   would retroactively expose every context that reused the key, including
   completed and archived ones.
3. **An unbounded permission is not a permission that can be operated.**
   "A small number" cannot be configured, audited or refused.

The cost is one ceremony per context, and §5 exists to keep that cost
honest.

---

## 5. The ceremony cost, acknowledged

A ceremony per context, with five guardians from three organisations,
physically present or in a controlled hybrid arrangement
(`PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md`), is a **significant operational
burden**. It is proportionate to a binding vote and disproportionate to a
weekly consultation.

The honest consequences:

| Consequence                                                      | Treatment                                                                                |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Frequent low-stakes consultations become expensive               | They are `advisory_consultation` contexts and may be held by other means entirely        |
| Small local bodies may be unable to staff a ceremony             | `GQ-10` — do not hold it electronically. This is a permitted gate outcome, not a failure |
| Election scheduling must accommodate ceremony logistics          | An operational-readiness gate item (`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8, item 6)      |
| Guardians must be found who are neither candidates nor operators | `GQ-07`, and the role-separation matrix                                                  |

**A model whose cost is hidden gets relaxed in practice.** Stating it here
is what makes `GQ-05` and `GQ-09` survivable.

---

## 6. Who may and may not be a guardian

| Role                          | Guardian?                      | Basis                                                                       |
| ----------------------------- | ------------------------------ | --------------------------------------------------------------------------- |
| **System Administrator**      | **No**                         | `KC-16`, `FIR-INV-008`; infrastructure control plus a share is a shortcut   |
| **Security Administrator**    | **No**                         | Same                                                                        |
| **Credential Authority**      | **No**                         | Dangerous-collusion combination 3 (`PACK-16A-ROLE-SEPARATION-MATRIX.md` §5) |
| **Eligibility Administrator** | **No**                         | Combination 4                                                               |
| **Voting-System Operator**    | **No**                         | Would join casting-path control to decryption capability                    |
| **Bulletin-Board Operator**   | **No**                         | Combination 2; and `BB-29` already forbids it                               |
| **Incident Commander**        | **No**                         | Combination 8; break-glass authority plus a share                           |
| **Ceremony Coordinator**      | **No**                         | Convenes and records; **holds no secret material** (`RS-16B-03`)            |
| **Archive Custodian**         | **No**                         | Would join record custody to decryption capability                          |
| **Election Officer**          | **Permitted with constraints** | §6.1                                                                        |
| **Election Board member**     | **Permitted with constraints** | §6.1                                                                        |
| **Independent Auditor**       | **No**                         | `R-11` ✗ everything operational; the auditor verifies the ceremony          |
| **External institution**      | **Permitted and encouraged**   | §6.2                                                                        |
| **Candidate in the context**  | **No**                         | `GQ-07`                                                                     |
| **DPO**                       | **Permitted with constraints** | Treated as any other independent office-holder                              |

### 6.1 Election Officers and Board members as guardians

Permitted, because in a party organisation these are often the only people
with both standing and availability — and prohibiting them outright would
push organisations toward the operators, which is worse.

Constraints:

| ID      | Constraint                                                                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GQ-11` | **At most `k − 1`** guardians may be Election Officers or Election Board members, in total                                                                                                                                 |
| `GQ-12` | An Election Officer guardian may not exercise window control for the same context while holding a share (`R-02` ✗ `R-07` in the PACK-16A matrix stands) — the guardian role displaces the operational one for that context |
| `GQ-13` | The Election Board **as a body** cannot reconstruct a secret, and no Board decision may assemble a quorum (`KC-02`)                                                                                                        |

`GQ-11` is the load-bearing one: even if every internal guardian colluded,
they remain one short of a quorum, so at least one **external** guardian
must join any successful collusion.

### 6.2 External institutions

**Encouraged**, and for the default profile effectively required by
`GQ-11`: with `k = 3` and at most 2 internal guardians, at least one
guardian is external in practice.

Suitable classes: a notary; an auditing firm; a university institute; a
civil-society organisation with relevant standing; a partner organisation
with no interest in the outcome. Each must satisfy the independence tests
of `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md` **in fact**, not on paper.

---

## 7. Collusion thresholds, stated

```text
< k guardians colluding      → no ballot is decryptable
= k guardians colluding      → every individual ballot is decryptable,
                               and an early tally is computable offline
k guardians + board operator → the above, plus correlation of board
                               entries with decrypted content
k guardians + credential authority → a path toward participation attribution
```

| Property                                         | Default 3-of-5 | High-assurance 4-of-7 |
| ------------------------------------------------ | -------------- | --------------------- |
| Guardians who must collude                       | 3              | 4                     |
| Minimum distinct organisations in that collusion | ≥ 2 (`GQ-01`)  | ≥ 2                   |
| Minimum **external** participants (`GQ-11`)      | ≥ 1            | ≥ 1                   |
| Absences tolerated                               | 2              | 3                     |
| Losses causing quorum loss                       | 3              | 4                     |

**Quorum collusion is undetectable** (`T-P16A-19`). It leaves no trace,
produces no evidence and is caught by nothing. That is why every control
above is preventive and organisational, and why `GQ-01`, `GQ-06` and
`GQ-11` are not negotiable.

---

## 8. What this document does not decide

```text
Who the guardians are                          → GOVERNANCE
The appointment and due-diligence procedure     → GOVERNANCE, lifecycle §2
The custody medium                              → key custody requirements
The ceremony script                             → key ceremony specification
Remuneration, liability and legal agreements    → GOVERNANCE, LEGAL
```

**SPECIFIED. SELECTED FOR ARCHITECTURAL REVIEW. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**
