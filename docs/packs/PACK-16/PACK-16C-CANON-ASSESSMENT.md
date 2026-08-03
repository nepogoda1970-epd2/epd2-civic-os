# PACK-16C — Canon Assessment

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Verdict

```text
CANON CLARIFICATION REQUIRED
```

**`CANON_VERSION` remains `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
and `docs/canonical/canon-version.json` are not modified by this round.**

**No amendment is proposed.** Eight clarifications are recorded
(`CQ-P16C-01`…`CQ-P16C-08`) and three amendment candidates
(`CAM-P16C-01`…`CAM-P16C-03`), stated precisely enough that a round which
owns the canon can decide them without re-deriving the analysis.

### 0.1 The finding this round could not avoid

PACK-16C is the first round to specify artefacts that are **published,
permanent, ballot-bearing and public**. The canon has an append-only public
publication primitive — `PublicLedgerEntry` (19a.1) — and that primitive
**explicitly prohibits a link to `VoteEnvelope`** (19a.1, *Запрещённые
связи*).

```text
That prohibition is CORRECT and this round does not challenge it.

It also means the bulletin board is NOT a PublicLedgerEntry, and the
canon currently has no other primitive for it. That gap is the
finding — CQ-P16C-01 and CAM-P16C-01.
```

---

## 1. What PACK-16C touches in the canon

| Canon section | What PACK-16C relies on | What PACK-16C does **not** do |
| ------------- | ----------------------- | ----------------------------- |
| **5.9 Tally Context** | Ownership of ballot-set verification and a signed result | Redefine it; move tally artefacts out of it |
| **5.11 Transparency Context** | Public publication as a bounded context | Extend its scope to ballots |
| **15.1 `Ballot`, 15.2 `BallotOption`** | Manifest-side shapes | Modify either |
| **15.3 `VoteEnvelope`** | Its forbidden-field set (`account ID`, name, email, membership ID, IdP reference) — **all of which PACK-16C also forbids** | Add a field, remove a field, or reach a prohibited value — §2.2, §2.3 |
| **15.4 `VoteReceipt`** | Inclusion-checkable without revealing the choice | Change what a receipt proves |
| **15.5 `Tally`** | `input_set_hash`, `algorithm_version`, `tally_signature` | Add a guardian, share or proof field — §2.5 |
| **15.6 `ResultPublication`** | Its count set and non-finality rule | Publish any count before closure |
| **18.1 `AuditEvent`** | The audit primitive as it stands | Route board evidence through it — §3.2 |
| **19a.1 `PublicLedgerEntry`** | The append-only chained-publication primitive, its immutability rule and **its prohibition on `VoteEnvelope`** | Use it for the bulletin board — §2.1 |
| **19a.3 `DisclosurePolicy`** | Generalised role labels rather than raw role IDs | Publish a raw `published_by_role_id` |
| **§21 canonical event envelope** | Unchanged | Add transport metadata or a second envelope |
| **19d.18, 19e.22, 19f.23** | Every prohibited edge | Create any of them |

**Nothing above is modified by this round.**

---

## 2. The six canonical questions raised

### `CQ-P16C-01` — Which canonical primitive is the bulletin board?

**The board is not `PublicLedgerEntry`, and this round does not make it one.**

19a.1 prohibits `PublicLedgerEntry → VoteEnvelope`. The board publishes
encrypted ballots, their proofs and their confirmation codes — artefacts
that *correspond to* vote envelopes even where they are not modelled as
them. Routing the board through `PublicLedgerEntry` would either violate the
prohibition or require pretending a published ballot is not a ballot.

```text
The prohibition exists so that a public ledger entry can never be
walked back to an envelope, and through it toward a person. That is
exactly the property PACK-16C is built to preserve.

PACK-16C therefore specifies the board as its OWN publication
structure (BA-*, AO-*, BE-*), NOT as a canonical aggregate, and
records the gap rather than closing it by analogy.
```

**What a future round must decide:** whether the canon gains a distinct
`ElectionBoardEntry`-style primitive with its own prohibitions, or whether
the board stays outside the canonical event model as a published document
structure — as PACK-16B concluded for the ceremony transcript
(`CQ-P16B-01`). **This round takes no position between the two**, and
`CAM-P16C-01` states what either choice would have to contain.

### `CQ-P16C-02` — Does `VoteEnvelope.credential_proof` survive `EPD2-HOM-1`?

**Under this profile, the submitted envelope carries no credential artefact
at all.** The continuation capability is presented alongside the submission,
validated, consumed inside the atomic boundary, and **never stored with the
ballot** (`DM-01`, `DM-03`, `DM-04`, `CC-04`).

```text
CANONICAL FIELD   VoteEnvelope.credential_proof
PACK-16C READING  under EPD2-HOM-1 this field is EMPTY, and must be,
                  because a persisted credential proof beside a ballot
                  is the person-to-ballot link the architecture removes
```

**This is a clarification, not a conflict.** The field is optional in effect
and unused by this profile. A future profile that populated it would need a
new ADR and would have to answer `FIR-INV-002` first. **This round proposes
no change to 15.3.**

### `CQ-P16C-03` — Does `VoteEnvelope.submitted_at` conflict with timestamp granularity?

`ER-09` and `DM-12` forbid any timestamp finer than the context's
`timestamp_granularity` anywhere in the record, because an exact submission
time is a correlation handle (`PM-*` #13, `T-P16C-01`).

```text
CANONICAL FIELD   VoteEnvelope.submitted_at
PACK-16C READING  the field's PRECISION is the question, not its
                  existence. PACK-16C requires that any submitted_at
                  which reaches a published artefact be at granularity,
                  and that no exact value be retained anywhere.
```

**Clarification recorded.** Whether the canon should state a precision
constraint on time fields generally — this is not the only one — is
`CAM-P16C-02`. **This round proposes no change.**

### `CQ-P16C-04` — What is `VoteReceipt.vote_envelope_reference` under this profile?

PACK-16C's receipt carries a `confirmation_code` derived only from the
ballot's encryptions and `H_E`, and explicitly **not** an internal object ID
(`RE-*` §2, `BP-*`).

```text
CANONICAL FIELD   VoteReceipt.vote_envelope_reference
PACK-16C READING  the reference is the CONFIRMATION CODE — a public,
                  recomputable value — and never an internal identifier,
                  a board position or a database key.
```

15.4's own requirement — that a receipt permit checking inclusion without
publicly revealing the choice — is **satisfied exactly** by `RE-*`.
Clarification recorded; **no change proposed.**

### `CQ-P16C-05` — Is `VoteEnvelope.status = superseded` reachable?

**No.** `EPD2-HOM-1` has no revoting (`ADR-099`, `BL-07`), and PACK-16C's
lifecycle keeps `superseded_if_permitted` **defined and unreachable**
(`BL-10`).

```text
CANONICAL STATUS  superseded
PACK-16C READING  present in the canon, UNREACHABLE in this profile.
                  No transition, no actor, no precondition, no reason
                  code produces it. An implementation offering one is
                  defective.
```

**The canonical status is not removed and not deprecated by this round.** A
profile that permits supersession would need it, and removing it would make
that future profile invent one silently — the same reasoning PACK-16A used.

### `CQ-P16C-07` — Where do the sealed batch artefacts live?

**Added by the turnout correction.** The three new board entry types —
`sealed_batch_commitment`, `sealed_batch_opening` and
`batch_reconciliation_record` (`BE-24`…`BE-26`) — raise exactly the question
`CQ-P16C-01` already raised, and **no new one**.

```text
They are board entries, and the board is not a PublicLedgerEntry
(CQ-P16C-01). They are therefore specified on the board's own terms,
in the entry catalogue, and are not modelled as canonical aggregates.
```

| Property | Canonical reading |
| -------- | ----------------- |
| Append-only, hash-chained, corrected only by supersession | **Same semantics as 19a.1**, applied to a primitive the canon does not have |
| Carries no link to `Account`, `IdentityRecord`, `ParticipationCredential` or any capability | **Stricter than 19a.1 requires** (`BE-24` prohibited fields) |
| Carries no timestamp finer than the context's granularity | `ER-09`, `DM-12` — the constraint `CAM-P16C-02` would generalise |
| `sealed_batch_commitment` is a **commitment to** ballot artefacts, never a link to a `VoteEnvelope` | **The 19a.1 prohibition is not approached, let alone crossed** — a hiding commitment is not a reference |

| ID | Rule |
| -- | ---- |
| `CAN-P16C-04` | **The sealed batch layer does not create a canonical aggregate and does not require one.** It extends `CAM-P16C-01`'s scope by three entry types and changes neither its shape nor its alternative |
| `CAN-P16C-05` | **A commitment is not a link.** `PublicLedgerEntry → VoteEnvelope` prohibits a reference; a `commitment_root` is a hash over hiding commitments from which no envelope is reachable. **The prohibition is honoured more strictly after this correction than before it**, because before closure the board no longer publishes ballot artefacts at all |

---

### `CQ-P16C-08` — Does the public-challenge entitlement need a canonical aggregate?

**Added by the bounded-challenge correction. Answer: no, and it must not
have one.**

```text
The entitlement is PRIVATE ANONYMOUS CAPABILITY STATE — three booleans
inside the continuation boundary (DM-20). It is not an identity-bearing
aggregate, it is not published, and it must NEVER appear in the public
election record.
```

| Property | Canonical reading |
| -------- | ----------------- |
| Holds no identity, no credential, no ballot reference, no artefact ID | **Below the canon's aggregate threshold entirely** (`CN-36`) |
| Never published, never in the record, never in an event payload | Nothing for `PublicLedgerEntry` to publish (`EV-71`, `EV-72`) |
| Three booleans with no counter | Cannot become an activity aggregate by accumulation (`CN-37`, `DM-23`) |
| Lives only inside the anonymous continuation boundary | PACK-15's capability lineage, unchanged |

| ID | Rule |
| -- | ---- |
| `CAN-P16C-06` | **No new public canonical identity-bearing aggregate is introduced by the bounded-challenge model.** The entitlement is private anonymous capability state and must not appear in the public election record |
| `CAN-P16C-07` | **A canonical aggregate for entitlement state would be a defect, not an improvement.** Modelling it canonically invites publication, and publishing it would create a per-capability activity record — exactly what `CC-04` removes |
| `CAN-P16C-08` | **The capacity plan (`DM-22`) is public manifest content, not a canonical aggregate**, and is published as part of `BE-01` and `BE-26` (`BE-32`). It carries nothing voter-specific |
| `CAN-P16C-09` | **Removing event-bus propagation of a capability reference requires no canon amendment.** Deleting `capability.consumed` and `challenge.public_entitlement_consumed` removes two integration events; it creates no aggregate, changes no canonical field, and **strengthens** 19a.1's separation rather than touching it (`EV-71`, `EV-78`) |

---

### `CQ-P16C-06` — Where do the tally's cryptographic artefacts live?

15.5 `Tally` carries `input_set_hash`, `algorithm_version`, `result_data`,
`invalid_vote_count` and `tally_signature`. PACK-16C's record requires,
additionally: aggregate ciphertexts per contest and option, guardian
decryption shares, proofs of correct decryption, the contributing-guardian
set, the quorum satisfied, and the closure checkpoint that fixes the input
set (`ER-*` artefacts 16, 18–22).

```text
PACK-16C READING  input_set_hash maps naturally to the CLOSURE
                  CHECKPOINT's fixing of the eligible set.
                  The share, proof and guardian artefacts have NO
                  canonical home, and this round does not invent one.
```

They are specified as **election-record artefacts**, published and
verifiable, and are not modelled as canonical aggregate fields.
`CAM-P16C-03` states what an amendment would need. **No change proposed.**

---

## 3. Three prohibitions this round strengthens without touching

### 3.1 `PublicLedgerEntry → VoteEnvelope` — untouched and reinforced

The prohibition stands exactly as written. PACK-16C **adds** to the same
principle at the data-model level: `DM-03` and `DM-04` may share no key, and
`EV-06` forbids a trace spanning the atomic boundary. **The canon prohibits
one edge; this round prohibits the shape that would make the edge
constructible.**

### 3.2 `AuditEvent` is not the board

Board evidence — checkpoints, inclusion proofs, batch publications — is
**not** routed through 18.1. An `AuditEvent` records that something
happened; a checkpoint *is* the evidence, verifiable by a stranger with no
access to EPD² systems (`IV-*`). Conflating them would make universal
verifiability depend on trusting an internal audit stream. **18.1 is
untouched.**

### 3.3 `published_by_role_id` is never published raw

19a.3's generalised-label rule is honoured throughout: board entries carry
signer identities that are **published roles and keys**, not raw role IDs,
and no participant identity appears anywhere (`BE-*`, `ER-*` §2).

---

## 4. Why no amendment is proposed

```text
An amendment proposed by a round that does not own the canon, to
support artefacts that are not implemented, for a profile whose ADR
is still `proposed` and whose parameter family carries an OPEN
verification obligation (VO-08), would bind the canon to a design
that external review has not yet seen.
```

| ID | Rule |
| -- | ---- |
| `CAN-P16C-01` | **The gap in §2.1 is real and is recorded as a gap.** PACK-16C does not close it by declaring the board a `PublicLedgerEntry`, which would violate 19a.1, nor by declaring published ballots not to be ballots, which would be false |
| `CAN-P16C-02` | **`CANON_VERSION` stays `0.8.0` and the canon files are byte-identical.** A clarification is not a version change |
| `CAN-P16C-03` | **PACK-16A's `CA-02` and PACK-16B's `CAM-P16B-01`…`CAM-P16B-03` are untouched.** This round neither advances nor discharges them |

---

## 5. Amendment candidates — recorded, not proposed

### `CAM-P16C-01` — A publication primitive for the election board

**Would have to contain:** an append-only, hash-chained, signed structure
with the same immutability and correction-by-supersession semantics as
19a.1; its own prohibited-links list, which must at minimum prohibit links
to `Account`, `IdentityRecord`, `ParticipationCredential` and any
capability aggregate; a statement that an entry's publication order is not
its arrival order; an explicit statement that the primitive carries **no
timestamp finer than a declared granularity**; and — added by the turnout
correction — a statement that **an entry's serialized size may not vary with
the number of subjects it covers** (`TC-33`).

**Must not contain:** any link that would let a published entry be walked
toward a person. **The alternative — leaving the board outside the canonical
event model entirely — is equally acceptable to this round**, and is what
PACK-16B chose for the ceremony transcript.

### `CAM-P16C-02` — A precision constraint on canonical time fields

**Would have to contain:** a general rule that a time field reaching a
published artefact is expressed at a declared granularity, with the
granularity itself published. **Scope beyond voting is not assessed by this
round**, which is precisely why it is a candidate and not a proposal.

### `CAM-P16C-03` — Cryptographic tally artefacts

**Would have to contain:** shapes for aggregate ciphertexts, decryption
shares, proofs of correct decryption, and the contributing-guardian set —
or an explicit canonical statement that these are **published record
artefacts and deliberately not canonical aggregates**, which is this round's
own reading and may well be the right answer.

---

## 6. Compatibility statement

```text
Canon sections modified by this round ....................... 0
Canonical aggregates created ................................ 0
Canonical fields added, removed or redefined ................ 0
Canonical statuses added, removed or deprecated ............. 0
Prohibited links created .................................... 0
Prohibited links weakened ................................... 0
PublicLedgerEntry → VoteEnvelope prohibition ................ UNTOUCHED
CANON_VERSION ............................................... 0.8.0, unchanged
docs/canonical/ files modified .............................. 0
Clarifications recorded ..................................... 8
Amendment candidates recorded ............................... 3
Amendments proposed ......................................... 0
Canonical aggregates required by the sealed batch layer ..... 0
Canonical aggregates required by the entitlement model ...... 0
Public canonical identity-bearing aggregates introduced ..... 0
```

---

## 7. Conclusion

PACK-16C fits inside the canon everywhere except one place, and that place
is a **gap rather than a conflict**: the canon has no publication primitive
for a public ballot-bearing board, because the only append-only public
primitive it has is prohibited — correctly — from touching vote envelopes.

**This round specifies the board on its own terms, records the gap, and
leaves the decision to a round that owns the canon.** The prohibition that
created the gap is the prohibition this whole architecture exists to
protect, and it is not weakened by a single line of this pack.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
