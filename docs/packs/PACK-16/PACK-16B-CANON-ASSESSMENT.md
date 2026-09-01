# PACK-16B — Canon Assessment

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Verdict

```text
CANON CLARIFICATION REQUIRED
```

**`CANON_VERSION` remains `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
and `docs/canonical/canon-version.json` are not modified by this round.**

PACK-16A recorded `CA-02` — _a trustee / key-ceremony evidence aggregate_ —
as an amendment candidate owned by "PACK-16B or 16C". **This round has now
produced the shapes that candidate was waiting for, and it still does not
propose the amendment.** §4 says why, and §5 states exactly what a future
proposal would have to contain, so that the decision is made by a round that
owns it rather than by an implementation that needs it.

### 0.1 A naming collision, stated so it cannot mislead

PACK-16A used `CA-01`…`CA-03` for **canon amendment candidates**. PACK-16B
uses `CA-01`…`CA-27` for **cryptographic agility rules** in
`PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md`. The two namespaces are
unrelated, and to avoid extending the confusion **this document uses the
prefix `CAM-P16B-*` for its own amendment candidates** and refers to
PACK-16A's candidates by their full context.

---

## 1. What PACK-16B touches in the canon

**Nothing structurally.** The ceremony is a governance and cryptographic
process whose artefacts are documents and published evidence, not domain
events — and that is a finding, not an omission.

| Canon section                    | What PACK-16B relies on                                                                 | What PACK-16B does **not** do                                 |
| -------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **5.9 Tally Context**            | The context owns ballot-set verification and a signed result                            | Redefine it; add a ceremony stage to it                       |
| **15.3 `VoteEnvelope`**          | Its forbidden-field set, unchanged                                                      | Reference it at all — the ceremony domain touches no envelope |
| **15.5 `Tally`**                 | `input_set_hash`, `algorithm_version`, `tally_signature`                                | Add a guardian field, a share field or a proof field          |
| **15.6 `ResultPublication`**     | Its count set and non-finality rule                                                     | Publish any count from the ceremony domain (`RN-C12`)         |
| **18.1 `AuditEvent`**            | The audit primitive, as it stands                                                       | Route ceremony evidence through it — §3.2                     |
| **19a.1 `PublicLedgerEntry`**    | The append-only chained-publication primitive and **its prohibition on `VoteEnvelope`** | Use it for the ceremony transcript — §3.1                     |
| **§21 canonical event envelope** | Unchanged                                                                               | Add transport metadata or a second envelope                   |
| **19d.18, 19e.22, 19f.23**       | Every prohibited edge                                                                   | Create any of them                                            |

**Nothing above is modified by this round.**

---

## 2. The five canonical questions raised

### `CQ-P16B-01` — Does the ceremony transcript need a canonical aggregate?

**Answer: not yet, and the reason matters.**

The ceremony transcript is a **published document with a hash chain**, not a
stream of domain events. Its readers are the Independent Auditor, the
Election Board and the public; its producer is a ceremony, not a service;
and its integrity comes from `H_X`-domain hashing and cross-location
comparison, not from an event log.

```text
Making it a canonical aggregate would put the ceremony's evidence
inside the system whose behaviour the ceremony exists to constrain.
```

That is the substantive argument, and it is stronger than the convenience
argument on the other side. **The transcript stays a published artefact.**

What _does_ eventually need a canonical home is narrower: the **reference**
from a context to its ceremony transcript and joint key — a pointer and a
digest, not the transcript. That is `CAM-P16B-01`.

### `CQ-P16B-02` — Is the ceremony transcript a `PublicLedgerEntry`?

**No, for the same reason the bulletin board is not** (PACK-16A `CQ-03`).

Canon 19a.1 carries `PublicLedgerEntry → VoteEnvelope — запрещено`. The
ceremony transcript never references a `VoteEnvelope`, so the prohibition is
not violated by using the primitive — but two other properties make it the
wrong fit:

| Property                  | `PublicLedgerEntry`        | Ceremony transcript                                     |
| ------------------------- | -------------------------- | ------------------------------------------------------- |
| Producer                  | A service, appending       | A convened ceremony, with named human participants      |
| Reader's trust basis      | The system's own chain     | **Independent recomputation from published values**     |
| Multi-view reconciliation | Not a concept              | **Load-bearing** — `RC-07`, `RC-08`, `FM-16B-16`        |
| Content                   | Domain publication records | Commitments, proofs, complaints, verdicts, attestations |

**Using `PublicLedgerEntry` would import a trust model the transcript
deliberately does not have.** Recorded as `CAM-P16B-01`, not proposed.

### `CQ-P16B-03` — Does the guardian organization need a canonical entity?

**No.** `R-17` is a **role in a published manifest**, not a domain entity.
It holds nothing (`RS-16B-14`), it has no lifecycle the system manages, and
representing it canonically would create exactly the wrong impression — that
the organization has standing in the key architecture, when the entire point
of `RS-16B-14` is that it does not.

The guardian **person** is likewise published in the manifest, not modelled
as a user: `FIR-INV-001` forbids a global user ID, and a guardian's
operative identifier in every arithmetic context is an **index**
(`RN-C06`).

### `CQ-P16B-04` — Does the cryptographic parameter registry need a canonical home?

**This is the closest call in the round, and the answer is still no —
narrowly.**

`CryptographicParameterSet` (parameter-set specification §3) is governed
configuration with a lifecycle: `draft`, `active`, `deprecated`,
`prohibited`, with dated transitions and an approving authority. That is
aggregate-shaped.

Against it:

```text
There is exactly ONE parameter set (EPD2-CRYPTO-1), and the profile's
central decision is that its values CANNOT CHANGE (PS-01…PS-04).
A registry of one immutable entry is a published document, not an aggregate.
```

The shape becomes real when a **second** profile exists — which is
`OD-P16B-06`'s successor, no earlier than the 2030 horizon. Recorded as
`CAM-P16B-02`.

Meanwhile the **manifest** already carries the parameter-set identifier and
its digest (`FIR-CONFIG-001`, governed configuration), which is what a
context actually needs.

### `CQ-P16B-05` — Does ceremony evidence belong in `AuditEvent` (18.1)?

**No.** `AuditEvent` records what the system did. The ceremony's evidence
records what **people** did, in a room, verified by recomputation.

Three concrete mismatches:

| Ceremony property                                              | `AuditEvent` handles it? |
| -------------------------------------------------------------- | ------------------------ |
| Two published views of the same event, compared before signing | No                       |
| A complaint with a respondent, a deadline and an adjudication  | No                       |
| A record whose verification requires no system access at all   | No — that is the point   |

**The system may emit `AuditEvent`s about ceremony-adjacent operations**
(a parameter load, a published checkpoint), and those are ordinary audit
events. The ceremony's own evidence is not one of them.

---

## 3. Two prohibitions this round strengthens without touching

### 3.1 `PublicLedgerEntry → VoteEnvelope`

Untouched, and reinforced from a new direction: `IN-34` forbids **any**
ceremony notification from referencing a participant, a credential, a ballot
or a cast time, and `RN-C14` forbids any ceremony-namespace reason code from
reaching a participant. The ceremony domain and the ballot domain do not
meet, so the prohibited edge has nothing to be constructed from.

### 3.2 Append-only public record

The transcript is append-only (`IN-38`), corrections are new entries
referencing corrected ones, and nothing is edited or deleted. That is Canon
19a.1's discipline applied **outside** the canonical primitive, which is the
honest position: EPD² adopts the property without claiming the aggregate.

---

## 4. Why `CA-02` is still not proposed

PACK-16A recorded _a trustee / key-ceremony evidence aggregate_ as owned by
"PACK-16B or 16C". PACK-16B now has the shapes — 29 transcript
requirements, 36 complaint rules, a 20-phase lifecycle — and declines.

**Three reasons, and the third is the one that decides it:**

1. **Nothing is built.** An amendment adopted for a specification that later
   changes is an amendment made twice.
2. **PACK-16C will change the shape.** The bulletin board consumes the joint
   key and publishes alongside the transcript; designing the canonical
   relationship before the board exists fixes the wrong half first.
3. **This round's own finding is that the transcript should _not_ be a
   canonical aggregate at all** (`CQ-P16B-01`, `CQ-P16B-02`). Proposing
   `CA-02` as PACK-16A imagined it would canonise a decision this round
   examined and rejected. **The right amendment is smaller than the one that
   was anticipated**, and saying so is the useful output.

---

## 5. Amendment candidates — recorded, not proposed

| ID            | Candidate                                                                                                                                                        | Owning round            | Affected clauses                                      | Precondition                                           |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| `CAM-P16B-01` | A **reference** from an election context to its ceremony transcript digest, joint public key and parameter-set ID — a pointer and hashes, **not** the transcript | **PACK-16C**            | new field group under 15; 19a.1 prohibition preserved | The bulletin-board aggregate exists (PACK-16A `CA-01`) |
| `CAM-P16B-02` | A cryptographic parameter-set registry aggregate                                                                                                                 | **The successor round** | new section under 15; `FIR-CONFIG-001` interaction    | A **second** parameter profile exists (`OD-P16B-06`)   |
| `CAM-P16B-03` | A ceremony-incident evidence reference, if `AuditEvent` proves insufficient in practice                                                                          | **PACK-17**             | 18.1 `AuditEvent`                                     | Operational experience, not speculation                |

**PACK-16A's `CA-02` is hereby narrowed, not discharged:** the trustee /
key-ceremony evidence aggregate as originally conceived is **not
recommended**; `CAM-P16B-01` is what remains of it. The narrowing is
recorded here and is not applied to PACK-16A's own document, which is
unchanged.

If an amendment is proposed, it must carry affected clauses, rationale,
compatibility consequences, security consequences, migration consequences
and the required approval. **None of that is produced here, and none of it
is deemed approved.**

---

## 6. Compatibility statement

| Check                                                         | Result                                                                                                |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Does PACK-16B add a canonical aggregate?                      | **No**                                                                                                |
| Does it add a field to an existing aggregate?                 | **No**                                                                                                |
| Does it add or change a status?                               | **No**                                                                                                |
| Does it change an owner?                                      | **No**                                                                                                |
| Does it create a prohibited edge?                             | **No**                                                                                                |
| Does it weaken any canonical prohibition?                     | **No** — every clarification narrows                                                                  |
| Does it use `PublicLedgerEntry` for ceremony evidence?        | **No** — `CQ-P16B-02`                                                                                 |
| Does it route ceremony evidence through `AuditEvent`?         | **No** — `CQ-P16B-05`                                                                                 |
| Does it modify `TZ-00-domain-event-canon.md`?                 | **No**                                                                                                |
| Does it modify `canon-version.json`?                          | **No**                                                                                                |
| Does it change `CANON_VERSION`?                               | **No — it stays `0.8.0`**                                                                             |
| Does it require a canon amendment **now**?                    | **No**                                                                                                |
| Does it identify amendment candidates for later rounds?       | **Yes — `CAM-P16B-01`…`CAM-P16B-03`, recorded and not proposed**                                      |
| Does it change PACK-16A's `CQ-01`…`CQ-06` or `CA-01`…`CA-03`? | **No** — PACK-16A's canon assessment is unmodified; §5 records a narrowing for the round that owns it |

`docs/canonical/canon-version.json` declares
`repository_compatibility: ">=0.1.0 <0.16.0"`. This round leaves
`REPOSITORY_VERSION` at `0.15.0`, inside that range. `OD-P16A-12` is
unchanged.

---

## 7. Conclusion

```text
NO CANON CHANGE MADE
CANON CLARIFICATION REQUIRED — five clarifications, CQ-P16B-01 … CQ-P16B-05
CANON AMENDMENT NOT PROPOSED
CANON AMENDMENT CANDIDATES RECORDED — CAM-P16B-01, CAM-P16B-02, CAM-P16B-03
PACK-16A CA-02 NARROWED, NOT DISCHARGED
CANON_VERSION REMAINS 0.8.0
```

**ASSESSED. NO CANON CHANGE. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**
