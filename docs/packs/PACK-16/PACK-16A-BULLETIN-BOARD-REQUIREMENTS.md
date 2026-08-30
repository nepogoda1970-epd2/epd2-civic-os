# PACK-16A — Bulletin Board Requirements

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**PACK-16A does not implement, design or specify the wire format of a
bulletin board.** It states the requirements a board must satisfy and
declares it a distinct trust boundary. The specification is PACK-16C's.

---

## 1. Why the board is a separate trust boundary

The selected protocol family **does not provide one**. ElectionGuard
assumes a broadcast channel exists and leaves it to the administrator:
_"In many verifiable election systems, it is assumed that a public bulletin
board exists for publishing these records. In practice, it has most often
taken the form of a simple web page"_ `[E-07]`.

Belenios makes the same assumption and then documents what happens when it
is not met — its own caveats list _"Absence of a proper bulletin board"_ as
a known limitation, noting that the board is in practice a webpage served
by the voting server and that a dishonest server _"may provide inconsistent
views to the participants"_ `[E-15]`. Verificatum ships a board and calls
it a convenience: _"it is easy to replace"_ `[E-32]`.

Three mature systems, three assumptions, no implementations. **The board is
where the field's published verifiability claims are weakest, and it is
entirely EPD²'s to build** (`RR-10`).

It is a **separate trust boundary** because the Voting Service, the board
and the Verification Client must be able to fail independently. A board
operated by the party that accepts ballots can drop a ballot and serve a
consistent-looking view of a world in which it was never cast.

```text
[WS-03 Voting Client]  →  [Voting Service]  →  [Bulletin Board]  →  [Mirrors]
                                                      ↑
                                       [Verification Client, third origin]
```

---

## 2. Minimal properties

| ID      | Property                                  | Requirement                                                                                                                                                      |
| ------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-01` | **Append-only semantics**                 | No operation modifies or removes a published entry. Deletion is not an authorised act, not an emergency act and not a break-glass act                            |
| `BB-02` | **Canonical election-scoped namespace**   | One board per voting context. Entries carry the context reference. No entry is addressable outside its context                                                   |
| `BB-03` | **Canonical ordering**                    | A total order defined by board sequence, published as a rule, independent of arrival time (`BM-06`)                                                              |
| `BB-04` | **Global consistency**                    | Every reader who verifies a checkpoint sees the same content for that checkpoint. Consistency is a property of the checkpoint chain, not of the server           |
| `BB-05` | **Equivocation resistance**               | Divergent views are detectable by comparing signed checkpoints across independent mirrors                                                                        |
| `BB-06` | **Signed checkpoints**                    | Periodic signed commitments over the board's content to that point, chained, with the signing key distinct from every other key                                  |
| `BB-07` | **Independent mirroring**                 | At least two mirrors under **distinct organisational control**, each publishing checkpoints and full content                                                     |
| `BB-08` | **Proof publication**                     | Every ballot's well-formedness and plaintext-knowledge proofs are published with it                                                                              |
| `BB-09` | **Full-content availability**             | The whole board is downloadable as a single artifact with a published hash. Per-entry lookup is never the only access path (`T-P16A-08`)                         |
| `BB-10` | **Accepted-ballot publication**           | Every accepted ballot appears with its identifier, ciphertexts, proofs and confirmation code                                                                     |
| `BB-11` | **Batched, delayed publication**          | Entries are published in batches with a randomized delay, so that publication order does not reveal submission order (`T-P16A-04/05`)                            |
| `BB-12` | **Challenged/spoiled-ballot publication** | Spoiled ballots are published with their openings, distinctly marked, and excluded from the tally by construction (`BM-09`)                                      |
| `BB-13` | **Supersession evidence where permitted** | Not applicable in `EPD2-HOM-1`; if a future profile permits it, the superseded entry stays and is marked (`SU-01`)                                               |
| `BB-14` | **Verification on a separate origin**     | The Verification Client is a third origin, not served from the casting origin, holding no session and no identity                                                |
| `BB-15` | **Manifest publication**                  | The election manifest — contests, options, selection limits, counting rule, windows, profile — is published **before** `voting_open` and is immutable thereafter |
| `BB-16` | **Cryptographic-parameter publication**   | The parameter set, its identifier and its **provenance** are published with the manifest (`BM-33`)                                                               |
| `BB-17` | **Trustee-contribution publication**      | The trustee list, key-ceremony evidence, public keys and decryption-share proofs are published                                                                   |
| `BB-18` | **Tally-artifact publication**            | The aggregate, the result, the decryption shares and their proofs are published together after closure                                                           |
| `BB-19` | **Retention**                             | The record is retained for a governed period sufficient for dispute, audit and archival verification — bounded by `OD-P16A-07`                                   |
| `BB-20` | **Archival verification**                 | An archived record verifies with the same verifier and the same published parameters, without any live service                                                   |
| `BB-21` | **Privacy filtering**                     | Every entry is checked against the prohibited-content list before publication; publication is refused, never redacted after the fact                             |

### 2.1 Prohibited board content — normative

The board **must not contain**, in any field, in any encoding, or in a form
from which they can be derived:

```text
any identity-bearing field of any kind
any account, person, membership or member-number reference
any name, email, phone, address or persona
any credential ID
any assertion ID or nonce
any continuation-capability reference
any context-scoped pseudonym
any identity-side request ID, correlation ID or trace ID
any network address
any device fingerprint or user-agent string
any uncoarsened timestamp
any voter roll, voter list or participation list
```

**`BB-21` refuses publication rather than redacting afterwards**, because a
value published for one second was published. This is the same discipline
as PACK-15's refusal of "monitoring detects a crossing after it happened".

**The voter-roll prohibition is a direct rejection of the Helios design**,
which publishes voter names beside encrypted ballots by default `[E-21]`.

---

## 3. Publication and audience models

| Model                              | Description                                                                      | Assessment                                                                                                   |
| ---------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Fully public board**             | Anyone may read everything at any time                                           | Maximal scrutiny; maximal small-group exposure; and pre-closure counting of entries is turnout               |
| **Auditor-readable board**         | Only accredited auditors may read                                                | Contradicts universal verifiability and the German publicity principle; concentrates trust in the accreditor |
| **Layered public and audit views** | A public view and a restricted audit view, with a declared, justified difference | **SELECTED**                                                                                                 |

### 3.1 The selected model and its justification

```text
LAYERED PUBLIC AND AUDIT VIEWS
```

**Public view, before closure:** the manifest, the parameter set and its
provenance, the trustee list, the ceremony evidence, and the checkpoint
chain. **Not** the ballot entries, and **not** any count of them.

**Public view, after closure:** everything — all accepted ballots with
their proofs and confirmation codes, all spoiled ballots with their
openings, the closure checkpoint, the aggregate, the shares, the proofs and
the result.

**Audit view:** the same content, plus the board's own operational
integrity evidence, available to the Independent Auditor under a time-boxed
PACK-12 grant, one context per grant.

**Why the ballot entries are withheld before closure — the only restriction
on publicity, and it is justified rather than assumed.** A live, publicly
readable list of accepted ballots is a live turnout counter. `ADR-094` and
`IT-11` prohibit turnout disclosure before closure without qualification,
and in a body of thirty an accurate live count is close to an outcome
signal. The restriction is therefore **required by an inherited
invariant**, not chosen for convenience.

**What is preserved.** A voter must still be able to confirm that her
ballot was recorded, before closure — that is `recorded as cast`, and
deferring it to after closure would make the property useless. §4 resolves
this without publishing a count.

**What is given up, stated.** Pre-closure public scrutiny of the ballot set
is not available. The compensating controls are the checkpoint chain, the
independent mirrors, and full publication at closure — after which any
divergence from the checkpointed history is detectable. **This is a real
reduction in transparency and it is recorded as a residual risk**
(`RR-11`, below).

---

## 4. Individual verification without a live count

| ID      | Requirement                                                                                                                                   |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-22` | Before closure, a voter may query **her own confirmation code** and receive presence-or-absence, and nothing else                             |
| `BB-23` | The query returns **no position, no index, no neighbours, no total and no timestamp finer than the context's granularity**                    |
| `BB-24` | The query is rate-limited per code, not per participant, and is unauthenticated — it requires only the code                                   |
| `BB-25` | The query result is accompanied by the current checkpoint, so a voter can later confirm that the checkpoint she saw is in the published chain |
| `BB-26` | The absence of a code is a **first-class outcome** with a reason code and a dispute path (`BM-19`), never a generic error                     |
| `BB-27` | Query volume is not published, exported or displayed before closure — it is a turnout proxy                                                   |

`BB-25` is what makes the pre-closure query trustworthy without publishing
the board: the voter obtains a commitment she can check against the full
record after closure. A board that lied to her before closure has to lie in
a way that survives publication, and it cannot.

---

## 5. Defences against the board's own attacks

| Attack                      | Defence                                                                                                                       | Residual                                                                        |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Split view**              | Signed checkpoints replicated to ≥ 2 independent mirrors; auditors and any reader compare                                     | Mirrors under one operator are not independent — independence is organisational |
| **Selective omission**      | Full-board publication with a published hash (`BB-09`); per-voter presence check (`BB-22`)                                    | An omission nobody checks is undetected; take-up is the limit `[E-29]`          |
| **Rollback**                | Chained checkpoints: a rollback breaks the chain                                                                              | A rollback before the first checkpoint of a context                             |
| **Checkpoint equivocation** | Checkpoints signed with a key distinct from every other key; published to all mirrors; cross-signed by mirrors where possible | A compromised signing key                                                       |
| **Late insertion**          | Closure is a signed checkpoint fixing the ballot set (`BM-20`); the aggregate is computed over that set                       | Clock manipulation, `T-P16A-38`                                                 |
| **Post-election deletion**  | Append-only archive with an integrity commitment; archival verification without a live service (`BB-20`)                      | Loss of every copy — an availability, not an integrity, failure                 |
| **Mirror inconsistency**    | Divergence is a **detectable, publishable event** with its own reason code and its own failure behaviour (`FM-P16A-14`)       | A mirror that stops publishing is indistinguishable from one that is offline    |

### 5.1 Mirror independence — what it must mean

| ID      | Requirement                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------- |
| `BB-28` | Mirrors are operated by **organisationally distinct** parties — not distinct servers under one operator           |
| `BB-29` | No mirror operator holds a trustee share, an election-officer role, or write access to the primary board          |
| `BB-30` | A mirror publishes its own signature over each checkpoint it has seen, so divergence is attributable              |
| `BB-31` | Mirror divergence **halts the tally** pending governance decision (`FM-P16A-14`); it is not a warning             |
| `BB-32` | The mirror list is published in the manifest before `voting_open`; adding a mirror mid-election is a recorded act |

**`BB-28` is the requirement most likely to be diluted in practice**, and
the dilution is invisible: three mirrors in three availability zones look
like three mirrors and are one operator. The Swiss ordinance names the same
property for its control components — _"diverse design of the control
components and the independence of their operation and supervision"_
`[E-45]` — and it is adopted here for the same reason.

---

## 6. Independent verification

| ID      | Requirement                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-33` | The published record must be sufficient for a verifier **written by a party other than EPD²** to check the outcome (`BM-26`, `BM-28`) |
| `BB-34` | The verification steps are specified in prose sufficient to write that verifier, following `[E-09]` and `[E-30]`                      |
| `BB-35` | The record's format is versioned; a record states the specification version it conforms to (`BM-34`)                                  |
| `BB-36` | Verification requires no credential, no account and no agreement to terms                                                             |
| `BB-37` | What the verifier **cannot** check is published alongside what it can — notably cast-as-intended for a compromised device (`BM-29`)   |

`BB-36` matters more than it appears. A verification that requires
registration is a verification whose users are known, and a list of people
who checked their ballots is a participation list.

---

## 7. Residual risks specific to the board

| ID      | Residual risk                                                                                     | Owner           |
| ------- | ------------------------------------------------------------------------------------------------- | --------------- |
| `RR-10` | The board is not provided by the selected family and must be built entirely by EPD² `[E-07]`      | PACK-16C        |
| `RR-11` | **Pre-closure public scrutiny of the ballot set is given up** to satisfy `NO INTERMEDIATE TALLY`  | accepted; §3.1  |
| `RR-12` | Mirror independence is organisational and cannot be enforced technically                          | GOVERNANCE      |
| `RR-13` | Detection of board misbehaviour depends on someone checking; take-up is empirically low `[E-29]`  | PACK-16C, FRONT |
| `RR-14` | A long-retained public record of encrypted ballots is a long-term secrecy liability (`T-P16A-40`) | `OD-P16A-07`    |
| `RR-15` | The board's own availability is a single point of failure for casting                             | **PACK-17**     |

---

## 8. What PACK-16A does not decide

```text
The board's data model, wire format and API
The checkpoint interval and the signing scheme
The mirror synchronisation protocol
The number of mirrors beyond the minimum of two
The retention period
The hosting arrangement
Whether an external transparency-log technology is used
```

All of the above are **PACK-16C's**, except retention (`OD-P16A-07`,
shared with PACK-09) and hosting (PACK-17).

**SPECIFIED. REQUIRES EXTERNAL REVIEW. DEFERRED TO PACK-16C. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**
