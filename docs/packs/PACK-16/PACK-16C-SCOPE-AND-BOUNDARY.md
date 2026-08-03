# PACK-16C — Scope and Boundary

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What this round is

PACK-16A chose the protocol. PACK-16B fixed the parameters and the people
who hold the key. **PACK-16C specifies the part a voter actually touches** —
how an anonymous capability becomes an encrypted ballot, how that ballot is
accepted and published, what the voter is given afterwards, and how anyone
at all can check the result.

```text
IN SCOPE
  casting flow, end to end
  continuation-capability consumption and the acceptance boundary
  ballot preparation, canonical envelope, ballot identity
  cast-or-challenge (Benaloh) flow
  server-side validation pipeline
  ballot lifecycle
  receipt model and its honest limits
  Verification Client architecture
  independent verifier requirements
  bulletin-board architecture, entries, append-only and consistency
  publication atomicity
  election record and its completeness rules
  turnout confidentiality and metadata privacy
  dispute and support boundary
  accessibility
  API, event and reason-code catalogues — specification only
```

```text
OUT OF SCOPE — and not started
  PACK-16D  implementation candidate, library selection, code
  PACK-17   independent verification operations, resilience, incident runbooks
```

---

## 2. What this round may not revisit

These are settled by `ADR-099` and `ADR-100`. **PACK-16C consumes them and
changes none of them.**

```text
EPD2-HOM-1                       ElectionGuard 2.1 specification lineage
homomorphic exponential-ElGamal  Benaloh cast-or-challenge
NIZK well-formedness proofs      no revoting
no intermediate tally            no person-to-ballot linkage

EPD2-CRYPTO-1                    p = 4096 bits · q = 256 bits
HMAC-SHA-256 profile             3-of-5 default quorum
4-of-7 high-assurance quorum     controlled hybrid ceremony
fully remote ceremony prohibited no hidden master key
no break-glass decryption        no compensated decryption
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `SB-01`  | **PACK-16C specifies how the chosen protocol is operated, not what the protocol is.** Any change to the list above is a return to `ADR-099` or `ADR-100`, not a PACK-16C decision |
| `SB-02`  | Where this round finds an **incompatibility** with `ADR-099` or `ADR-100`, it raises an **`ARCHITECTURAL BLOCKER`**, names the affected assumption, stops the dependent decision, and **does not amend the protocol** |
| `SB-03`  | No document in this pack may weaken an inherited invariant by restating it more loosely. Where a restatement is needed, the inherited identifier is cited |

**No `ARCHITECTURAL BLOCKER` was raised by this round.** §7 records the
conditions that were checked.

---

## 3. `VO-08` — inherited, referenced, not touched

```text
VO-08  ElectionGuard 2.1 published parameter family
       versus BSI TR-02102-1 Remark 2.12 preference

Owner:        PACK-16B external cryptographic review
Assurance:    PACK-17
NOT owned by: PACK-16C
Status:       OPEN
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `SB-04`  | **PACK-16C inherits `VO-08` as a constraint and may not close, narrow, re-own or reinterpret it**                     |
| `SB-05`  | **PACK-16C may not alter the parameter family and may not claim approval of it.** The manifest binds a parameter-set identifier and reproduces it; it does not endorse it |
| `SB-06`  | **No document in this pack makes a complete-BSI-conformity claim**, and none may. `VO-08` blocks production implementation acceptance, production and legal activation, complete BSI-conformity claims and final cryptographic assurance |
| `SB-07`  | Every activation gate this round defines carries `VO-08` in its precondition list, so that it cannot be satisfied by PACK-16C work alone |

---

## 4. What PACK-16C receives from PACK-15

**One thing:** an anonymous, single-use **continuation capability**.

```text
It is NOT identity.              It is NOT a credential.
It is NOT a credential ID.       It is NOT a ballot ID.
It is NOT a reusable session.    It cannot be reverse-resolved.
It may NOT be persisted as a voter identifier.
```

The consumption boundary, replay prevention, lifecycle, one-time use,
failure and timeout semantics are specified in
`PACK-16C-CONTINUATION-CONSUMPTION-AND-ACCEPTANCE.md`. The property that
governs all of them is inherited from PACK-15 and restated here once:

> **The pair never exists to be joined.**

---

## 5. The three questions this round exists to answer

```text
1. When exactly is the capability consumed, relative to cryptographic
   validation and acceptance — and what does that ordering prevent?
2. What may a voter be given afterwards that lets them check their ballot
   without letting anyone else learn their choice?
3. What must be published so that a stranger with no account, no
   credential and no trust in EPD² can check the outcome?
```

Each has a document, a decision and an acceptance row. Where the honest
answer is "this cannot be fully achieved", it is written as that — §6.

---

## 6. What this round does not claim

Stated at the front so that no later section has to be read defensively.

```text
NOT CLAIMED  that a compromised voting device can be prevented from
             encrypting a different choice — challenge DETECTS, it does
             not prevent  (T-P16A-33, RR-03)
NOT CLAIMED  full receipt-freeness or coercion resistance — the profile is
             coercion-MITIGATING, and PACK-16A's prohibited-claims registry
             stands unchanged
NOT CLAIMED  that timing correlation is eliminated — it is reduced and
             bounded, and network-layer observers remain (T-P16A-04, RR-06).
             The sealed batch layer removes the BOARD as a turnout channel;
             it does not touch the network                 (TC-56)
NOT CLAIMED  that a local diagnostic challenge is evidence against a
             malicious client — it is not, and a malicious client can
             fake one                                       (CH-40, CH-41)
NOT CLAIMED  that the finite capacity bound protects against an issuance
             policy that over-issues capabilities — L_max scales with E
                                                            (T-P16C-51)
NOT CLAIMED  that the sealed batch construction is externally sourced —
             the data structure is (G-01, G-02); its use as a turnout
             control is this round's own reasoning         (G-R09)
NOT CLAIMED  that individual verification will actually be used — take-up
             is empirically low (RR-04)
NOT CLAIMED  complete BSI conformity — SB-06, VO-08
NOT CLAIMED  that any of this is implemented, tested or reviewed
```

---

## 7. Compatibility checks performed against the inherited architecture

| Inherited commitment                                     | Checked against                                  | Result       |
| -------------------------------------------------------- | -------------------------------------------------- | ------------ |
| `BM-01`…`BM-06` identifier rules                         | Ballot-ID model, envelope, receipt, board entries  | **consistent** |
| `BM-07`…`BM-13` challenge rules                          | Cast-or-challenge specification                    | **consistent** |
| `BM-14`…`BM-16` proof rules                              | Validation pipeline                                | **consistent** |
| `BM-17`…`BM-19` publication and lookup                   | Board architecture, receipt, verification client   | **consistent** |
| `BM-20`…`BM-25` tally and exclusion                      | Election record, completeness matrix               | **consistent** |
| `BM-26`…`BM-29` verifiability                            | Independent verifier requirements                  | **consistent** |
| `NIT-01`…`NIT-07` no intermediate tally                  | Turnout model, board entry catalogue, API catalogue | **consistent** |
| `CC-01`…`CC-10` continuation capability                  | Consumption and acceptance model                   | **consistent** |
| `BB-01`…`BB-37` board requirements                       | Board architecture, append-only model, entry catalogue | **consistent** — every one is discharged or explicitly deferred |
| `EX-01`…`EX-07` exclusion                                | Ballot lifecycle                                   | **consistent** |
| PACK-16A ballot lifecycle states                         | PACK-16C lifecycle                                 | **extended, not redefined** — §7.1 |
| `NIT-01`…`NIT-07` no intermediate tally                  | Sealed batch commitment layer                      | **consistent — and the reason the first candidate's padding model was rejected** (`TC-21`) |
| `BM-12` challenge repeatability                          | Two-tier challenge model                           | **consistent — the repeatable part is preserved in full as the local diagnostic challenge** (`CH-18`, `CH-36`) |
| `ADR-100` ceremony, quorum, no pre-closure decryption     | Election record, tally artefacts                   | **consistent** |
| Canon 19a.1 `PublicLedgerEntry → VoteEnvelope` prohibited | Board data model                                   | **not violated** — `PACK-16C-CANON-ASSESSMENT.md` |

### 7.1 The one place PACK-16C extends an inherited model

PACK-16A's ballot lifecycle has 14 states. The round task requires 16,
adding `submission_uncertain`, `cryptographically_validating`,
`accepted_pending_publication`, `publication_disputed` and `rejected`, and
renaming nothing.

**This is an extension, not a redefinition.** Every PACK-16A state survives
with its meaning intact, every PACK-16A prohibited transition remains
prohibited, and `superseded_if_permitted` remains **unreachable**.
`PACK-16C-BALLOT-LIFECYCLE.md` §2 shows the mapping explicitly.

---

## 8. Identifier namespaces opened by this round

```text
SB-*        scope and boundary            CF-*     casting flow
CN-*        continuation consumption      BP-*     ballot preparation/envelope
CH-*        cast-or-challenge             VP-*     validation pipeline
BL-*        ballot lifecycle              RE-*     receipt
CB-*        coercion / receipt boundary   VC-*     Verification Client
IV-*        independent verifier          BA-*     bulletin-board architecture
BE-*        board entry catalogue         AO-*     append-only and consistency
PA-*        publication atomicity         ER-*     election record
EC-*        record completeness           PM-*     privacy and metadata
TC-*        turnout confidentiality       XA-*     accessibility
DP-*        dispute and support           API-*    API operations
EV-*        events                        RN-16C-* reason-code rules
FM-16C-*    failure and abort             T-P16C-* threat model extension
G-*         evidence registry             OD-P16C-* open decisions
AC-P16C-*   acceptance matrix             CQ-P16C-*, CAM-P16C-*,
DM-*        data models                            CAN-P16C-*  canon
```

**No identifier from PACK-16A or PACK-16B is reused, renumbered or
redefined.** Where this round needed a prefix that was already taken —
`BB-*`, `RC-*`, `AX-*`, `DS-*` — it chose a new one rather than overload it.

---

## 9. What this document does not decide

```text
Everything else in this pack. This document fixes the boundary;
the decisions live in the documents that own them, and the
acceptance matrix says where each one is.
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
