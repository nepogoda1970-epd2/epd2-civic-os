# PACK-16A — Election Profile Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**No election type below is activated by this document.** Support values
describe what the selected ballot model can express; activation is a
separate governance act with its own gate
(`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8).

---

## 1. Support values

| Value                             | Meaning                                                                                                   |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **supported initially**           | Expressible in `EPD2-HOM-1`; specified; awaiting implementation and a governance gate                     |
| **supported in future**           | Expressible in principle; requires a decision or a mechanism this round defers                             |
| **not supported**                 | Not expressible in `EPD2-HOM-1`; would require `EPD2-MIX-1`, which is not selected                        |
| **prohibited pending research**   | Must not be built or activated until a named question is answered in a later round                        |

---

## 2. The matrix

| Election type                  | `EPD2-HOM-1` support           | Ballot construction                                     | Tally                          | Why                                                                                                              |
| ------------------------------ | ------------------------------ | ------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Yes/no referendum**          | **supported initially**        | One contest, two options, selection limit 1             | Homomorphic                    | The simplest cardinal ballot; two per-option totals                                                               |
| **Single-choice election**     | **supported initially**        | One contest, m options, selection limit 1               | Homomorphic                    | Plurality; the default case                                                                                       |
| **Multiple-choice (n-of-m)**   | **supported initially**        | One contest, selection limit n, option limit 1          | Homomorphic                    | Contest-sum proof bounds the total at n `[E-08]`                                                                  |
| **Approval voting**            | **supported initially**        | Selection limit = option count `[E-08]`                 | Homomorphic                    | Explicitly supported by the construction                                                                          |
| **Multi-seat election**        | **supported initially**, by approval or n-of-m | Selection limit = seats, or approval    | Homomorphic; seats by highest totals | Seat allocation is a **counting rule applied to published totals**, not a cryptographic operation (§4)     |
| **Candidate nomination**       | **supported initially for internal, non-statutory selection only** | Single-choice or n-of-m per position | Homomorphic         | **Statutory nomination for public office is prohibited** — §5 and the legal boundary §5                          |
| **Constitutional-amendment vote** | **supported initially** as a yes/no on a fixed text | One contest, two options              | Homomorphic                    | The ballot is trivial; the difficulty is quorum and majority rules, which are governance, not cryptography       |
| **Party-policy consultation**  | **supported initially**        | One or more independent contests                        | Homomorphic                    | Must be labelled non-binding on every surface (PACK-15 §7.1 `advisory_consultation`)                              |
| **Binding member resolution**  | **supported initially**        | One contest, yes/no/abstain                             | Homomorphic                    | Abstention as an explicit option is a ballot option, not an absence                                               |
| **Ranked-choice / IRV**        | **not supported**              | —                                                       | —                              | *"Ranked choice voting is not supported in this version"* `[E-08]`; requires `EPD2-MIX-1`                          |
| **STV**                        | **not supported**              | —                                                       | —                              | Multi-round elimination is not expressible in a homomorphic aggregate `[E-08]`                                    |
| **Condorcet**                  | **not supported**              | —                                                       | —                              | Requires the pairwise matrix, i.e. the joint pattern within a ballot                                              |
| **Majority Judgment**          | **not supported**              | —                                                       | —                              | Requires per-ballot grade distributions and a median rule over them                                               |
| **Free-form write-ins**        | **prohibited pending research**| —                                                       | —                              | *"Verifiable tallying of free-form write-ins may be best done with a mixnet design"* `[E-08]`; and free text is a covert channel |
| **Any public political election** | **prohibited pending research** and **prohibited by default** | — | —                | Legal boundary §5, §8; `PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT`                                          |

---

## 3. Per-type analysis

Columns: whether the tally is homomorphic-expressible; whether a mixnet
would be required; **whether plaintext individual ballots are ever
produced**; proof complexity; recount implications; audit implications;
small-group disclosure risk; compatibility with no-intermediate-tally,
receipt-freeness and remote voting.

| Type                        | Homomorphic | Mixnet required | Plaintext individual ballots | Proof complexity                        | Recount                                   | Audit                                  | Small-group risk                        | No-interm. tally | Receipt-freeness posture | Remote |
| --------------------------- | ----------- | --------------- | ---------------------------- | --------------------------------------- | ----------------------------------------- | -------------------------------------- | --------------------------------------- | ---------------- | ------------------------ | ------ |
| Yes/no referendum           | **yes**     | no              | **never**                    | 2 range proofs + 1 sum proof            | Re-verify proofs and re-aggregate; no re-decryption of ballots | Full, from the record          | **low** unless electorate < 5           | compatible       | code reveals nothing     | yes    |
| Single choice               | **yes**     | no              | **never**                    | m range proofs + 1 sum proof            | Same                                      | Full                                   | **medium** — a unanimous small body is self-revealing | compatible | same         | yes    |
| n-of-m                      | **yes**     | no              | **never**                    | m range proofs + sum proof bounded at n | Same                                      | Full                                   | **medium**                              | compatible       | same                     | yes    |
| Approval                    | **yes**     | no              | **never**                    | m range proofs; sum proof bounded at m  | Same                                      | Full                                   | **medium**                              | compatible       | same                     | yes    |
| Multi-seat (approval/n-of-m)| **yes**     | no              | **never**                    | As above                                | Same; **tie resolution is a governance rule, published in advance** | Full          | **medium–high** — per-seat totals in a small body | compatible | same        | yes    |
| Candidate nomination (internal) | **yes** | no              | **never**                    | As above                                | Same                                      | Full                                   | **high** — nominating bodies are small   | compatible       | same                     | yes, but §5 |
| Constitutional amendment    | **yes**     | no              | **never**                    | 2 range proofs + sum proof              | Same                                      | Full                                   | **low–medium**                          | compatible       | same                     | yes    |
| Policy consultation         | **yes**     | no              | **never**                    | Per-contest as above                    | Same                                      | Full                                   | **medium**                              | compatible       | same                     | yes    |
| Binding member resolution   | **yes**     | no              | **never**                    | 3 range proofs + sum proof              | Same                                      | Full                                   | **medium**                              | compatible       | same                     | yes    |
| Ranked / IRV                | **no**      | **yes**         | **YES — published in the clear after shuffling** `[E-12]` | Shuffle proof over the whole set | Requires re-running the mix or trusting the published plaintexts | Full but privacy-costly | **severe** — the ranking is a quasi-identifier | compatible in principle | **pattern signature is a receipt** | risky |
| STV                         | **no**      | **yes**         | **YES**                      | Same                                    | Same                                      | Same                                   | **severe**                              | compatible in principle | same             | risky  |
| Condorcet                   | **no**      | **yes**         | **YES**                      | Same                                    | Same                                      | Same                                   | **severe**                              | compatible in principle | same             | risky  |
| Majority Judgment           | **no**      | **yes**         | **YES**                      | Same                                    | Same                                      | Same                                   | **severe**                              | compatible in principle | same             | risky  |
| Write-ins                   | **no**      | **yes**         | **YES**, and free text       | Highest                                 | Manual adjudication of text               | Adjudication is not verifiable         | **severe**, plus a covert channel       | compatible in principle | **text is a receipt** | no     |

**The column that decides everything is "plaintext individual ballots".**
Every type marked **never** is compatible with EPD²'s small bodies, its
receipt-freeness posture and its small-cell disclosure regime. Every type
marked **YES** carries a preference-pattern channel that neither
`disclosure_min_cell` nor complementary suppression can close, because the
ballot *is* the cell.

### 3.1 Not all election types are automatically compatible with one profile

Stated because the task of this round is to prevent the opposite
assumption from being made silently. The nine supported types share a
single property — the tally is a **linear function of per-option bounded
integer values** — and the five unsupported types share a single property —
the tally depends on the **joint pattern within a ballot**. That is the
line, it is a property of the mathematics rather than of the
implementation, and no amount of engineering moves a type across it.

---

## 4. Multi-seat elections — the part that is not cryptography

A multi-seat election in `EPD2-HOM-1` produces per-candidate totals. Turning
totals into seats is a **counting rule**, and the following must be true of
it:

| ID       | Requirement                                                                                                                    |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `MS-01`  | The counting rule, including the tie-resolution rule, is published **before** `voting_open` and is part of the election manifest |
| `MS-02`  | The rule is deterministic given the published totals, or, where a random tie-break is used, the randomness is publicly verifiable |
| `MS-03`  | Seat allocation is computed from the **published** totals and is independently reproducible by any reader                       |
| `MS-04`  | A quota rule (gender parity, list balance, minimum support) is part of the manifest, never an after-the-fact adjustment         |
| `MS-05`  | Where a quota rule makes the outcome depend on data outside the ballot, that data is published with the result                  |

`MS-01` and `MS-04` exist because the most common way to lose an election's
legitimacy without touching a ballot is to decide the counting rule after
seeing the totals.

---

## 5. Candidate nomination — the sharpest boundary in this matrix

`EPD2-HOM-1` can express a nomination ballot. **German law decides whether
it may be used, and for statutory nominations it currently does not.**

| Use                                                                     | Technical support   | Permitted?                                                                                              |
| ----------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------- |
| Internal shortlisting, pre-selection, indicative member consultation    | supported initially | Yes — electronic tooling is expressly permitted for *Vorermittlung, Sammlung und Vorauswahl* `[E-51]`     |
| Internal party bodies electing their own officers                       | supported initially | Yes — § 15 Abs. 2a PartG permits binding electronic elections, subject to secrecy under § 15 Abs. 2 `[E-49]` |
| **Aufstellung von Wahlbewerbern for Bundestag or Landtag**              | supported initially | **NO** — § 17 PartG delegates to the *Wahlgesetze*; the operative guidance requires simultaneous physical presence at one location and written secret paper ballots `[E-50]`, `[E-51]` |

**A context of type `candidate_nomination` used for a statutory nomination
is prohibited by default and must be refused at configuration time**, with
`VOTING_CONTEXT_LEGAL_BASIS_MISSING`. This is not a caution; a nomination
conducted electronically risks *Zurückweisung des Wahlvorschlags*, which
disenfranchises the entire body it was meant to serve.
`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §5 is the full treatment.

---

## 6. Small-group disclosure applied to published results

PACK-15 established `disclosure_min_cell = 5` and complementary suppression
for **participation** signals. This section extends the same regime to
**results**, which PACK-15 did not have to consider. **No PACK-15 value is
changed, and no change is proposed.**

### 6.1 Rules

| ID       | Rule                                                                                                                                                                                  |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SD-01`  | The **default publication unit is the whole context**. Organizational sub-scope results are published only where the context declares it **and** every sub-scope cell passes `disclosure_min_cell` |
| `SD-02`  | **Complementary suppression is applied jointly** across the result, the aggregate participation figures, any auditor evidence bundle and any previously published figure for the same context |
| `SD-03`  | A cell below the minimum is **suppressed, not rounded**; suppression is flagged; where suppression would empty a breakdown, the breakdown is declared suppressed as a whole              |
| `SD-04`  | Where the whole electorate is below `small_electorate_threshold` (default 50), **only the aggregate outcome is published**, and per-scope figures are not published at all              |
| `SD-05`  | **Reverse calculation is treated as disclosure.** A published set from which a suppressed cell can be recovered by differencing against totals, against another context, or against a prior bundle, has disclosed it |
| `SD-06`  | The disclosure decision is taken by the **Election Board**, recorded as an act with a reason, and reflected in append-only evidence. It is not an operator setting and not a default    |
| `SD-07`  | A **full unsuppressed result** may be released to the Independent Auditor under a time-boxed PACK-12 grant, **after closure only**, one context per grant, itself audited               |
| `SD-08`  | Where an outcome cannot be published without disclosure, the outcome is **withheld from publication and still binding**, and the withholding is itself published with its reason        |
| `SD-09`  | Small-cell dashboards may not be used to reconstruct an intermediate tally: per-scope operational metrics are prohibited outright below the small-electorate threshold (PACK-15 §19.4)  |

### 6.2 Bodies too small to vote secretly at all

Some bodies cannot hold a secret ballot electronically or otherwise. The
German operative guidance records the floor plainly: *"Der Grundsatz der
geheimen Wahl erfordert eine Abstimmung von mindestens drei Personen"*
`[E-51]`.

| Electorate size | Position                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------- |
| < 3             | **A secret ballot is not possible.** The context is refused at configuration time                                    |
| 3 … 4           | Below `disclosure_min_cell`; the outcome is publishable only as a decision, never as a distribution                  |
| 5 … 49          | Small-electorate policy (PACK-15 §19.4) applies in full, plus `SD-04`; activation requires governance acknowledgement |
| ≥ 50            | Standard regime                                                                                                      |

**The honest statement, carried forward from PACK-15 §19.4 unchanged:** in
a body of eleven people, no technical control makes participation or
outcome unlinkable to an observer who knows the eleven. The controls reduce
what the *system* discloses; they do not change what a small group knows
about itself. The governance acknowledgement exists so that this is decided
rather than discovered.

---

## 7. Compatibility summary by property

| Property                        | Supported types (all nine)                                            | Unsupported types (ranked family)                                    |
| ------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| No intermediate tally           | **compatible** — nothing decrypts before closure                      | compatible in principle; the shuffle happens after closure           |
| Receipt-freeness posture        | **compatible** — the confirmation code reveals nothing `[E-05]`       | **incompatible in small bodies** — the published ranking is a receipt |
| Small-cell disclosure control   | **compatible** — totals can be suppressed                             | **incompatible** — the ballot is the cell                            |
| Remote voting                   | compatible, within the coercion limits of §5 of the coercion boundary | compatible technically, worse in practice                            |
| Individual verifiability        | **compatible** — code presence on the board                           | compatible                                                            |
| Universal verifiability         | **compatible** — aggregate and proofs published                       | compatible, with a mixnet verifier                                    |
| PACK-15 unlinkability           | **compatible**                                                        | compatible at the identity boundary; broken by pattern signature      |

---

## 8. What activation would require

No type in §2 is activated by this document. Activation of any type
requires, per `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8, all of:

```text
legal basis
election-specific authorization
approved election profile
independent security assessment
accessibility assessment
operational readiness evidence
approved key ceremony
incident and recovery plan
public-verifiability plan
data-protection assessment
```

**SPECIFIED. ASSESSED. NOT ACTIVATED. REQUIRES LEGAL ASSESSMENT. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED.**
