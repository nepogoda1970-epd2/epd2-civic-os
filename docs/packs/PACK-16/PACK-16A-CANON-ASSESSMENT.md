# PACK-16A — Canon Assessment

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Verdict

```text
CANON CLARIFICATION REQUIRED
```

**`CANON_VERSION` remains `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
and `docs/canonical/canon-version.json` are not modified by this round.**

Six clarifications are required before PACK-16C, and **one of them is
likely to become an amendment proposal at PACK-16C or PACK-16D** (§4).
Recording that now, at the point of discovery, is the whole purpose of
this assessment; deferring it to the round that needs it is how an
amendment gets made by an implementation instead of by a decision.

---

## 1. What PACK-16A touches in the canon

Nothing structurally. But the selected ballot model must eventually be
expressed in canonical terms, and this round is where the fit is checked.

| Canon section                           | What PACK-16A relies on                                                                                                                  | What PACK-16A does **not** do                               |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **5.9 Tally Context**                   | Ballot-set verification, counting, repeatability, invalid-record handling, a signed result                                               | Redefine the context or move its owner                      |
| **15.1 `Ballot`**                       | `ballot_method`, `secrecy_mode`, `eligibility_rule_version`, `quorum_rule`, `threshold_rule`, `configuration_hash`, the status lifecycle | Add a field, add a status, change a status meaning          |
| **15.2 `BallotOption`**                 | Options locked after opening                                                                                                             | Change the locking rule                                     |
| **15.3 `VoteEnvelope`**                 | `credential_proof`, `encrypted_or_encoded_choice`, `integrity_hash`, `validation_status`, `included_in_tally`, the forbidden-field set   | Add an identity field, weaken the prohibition               |
| **15.4 `VoteReceipt`**                  | _"Receipt должен позволять проверить включение бюллетеня без публичного раскрытия выбранного варианта"_                                  | Change the receipt's obligation                             |
| **15.5 `Tally`**                        | `input_set_hash`, `algorithm_version`, `result_data`, `tally_signature`                                                                  | Change the aggregate's shape                                |
| **15.6 `ResultPublication`**            | `eligible_count`, `credential_count`, `accepted_vote_count`, `rejected_vote_count`, `challenge_deadline_at` and its non-finality rule    | Make the result final on a deadline alone                   |
| **19a.1 `PublicLedgerEntry`**           | The append-only chained-publication primitive                                                                                            | **Use it for the bulletin board — canon forbids it** (§3.1) |
| **§21 canonical event envelope**        | Unchanged, as PACK-13 and PACK-15 leave it                                                                                               | Add transport metadata or a second envelope                 |
| **19d.18, 19e.22, 19f.23 prohibitions** | Every prohibited edge into `VoteEnvelope` / `Tally` / `Ballot`                                                                           | Create any of them                                          |

**Nothing above is modified by this round.**

---

## 2. The six canonical questions raised

### `CQ-01` — Does `VoteEnvelope.credential_proof` become a credential reference?

**No, and the clarification is needed to keep it so.**

Canon 15.3 gives `VoteEnvelope` a field `credential_proof`, and its
forbidden-field set names account ID, name, email, membership ID and
identity-provider reference — it does **not** name a credential
identifier, because canon 10.1 already forbids identity fields on
`ParticipationCredential` and the two prohibitions were written for
different purposes.

PACK-15 closed this on its side: `VotingCredentialId` is _"never used as,
derived into, or stored beside a ballot identifier"_ (PACK-15 §11), and the
consumption record is a **set, not a map** (ADR-093). PACK-16A restates it
as `BM-02` and `CC-04`.

**Clarification required:** that `credential_proof` is a _proof that a
valid authorisation was consumed_, carrying no credential identifier, no
continuation reference and nothing from which either is derivable — and
that this reading is normative rather than merely conventional.

**Not an amendment**, because it narrows an existing prohibition rather
than changing a structure. But it must be written down, because a field
called `credential_proof` will otherwise eventually hold a credential
reference, for the best of reasons.

### `CQ-02` — Is `VoteEnvelope.status = superseded` reachable?

**Not in `EPD2-HOM-1`.** Canon 15.3 lists `superseded` among
`VoteEnvelope`'s statuses, and the round's revoting decision makes it
unreachable (`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §3.4).

**No amendment is required.** A canonical status that a profile does not
use is not a canon conflict, and removing it would foreclose a future
profile. **Clarification required:** that reachability of `superseded` is a
**profile property**, that `EPD2-HOM-1` does not reach it, and that any
profile which does must first discharge `SU-01` … `SU-05`.

### `CQ-03` — Does the bulletin board fit `PublicLedgerEntry`?

**No. Canon forbids it, explicitly.**

Canon 19a.1 gives `PublicLedgerEntry` exactly the shape a bulletin board
needs — `content_hash`, `previous_entry_hash`, append-only with correction
only by a new entry, `supersedes_entry_id`, `disclosure_policy_id`. And
canon 19a.1's prohibition list states:

```text
PublicLedgerEntry → VoteEnvelope — запрещено.
```

The prohibition is correct and must stand: it exists so that the public
ledger cannot become a route from a published fact to an individual cast
ballot. **PACK-16A does not propose weakening it.**

But the consequence is architectural: **the bulletin board cannot be
modelled as `PublicLedgerEntry`**, and the canon currently has no aggregate
for a per-ballot public record. This is the finding most likely to become
an amendment (§4).

**Clarification required now:** that the bulletin board is a **distinct
publication surface** from the public ledger; that `ResultPublication` is
published via `PublicLedgerEntry` as canon already provides (19a.5, via
`subject_type = result_publication`); and that the two surfaces do not
merge.

### `CQ-04` — Is the confirmation code a `VoteReceipt`?

**Structurally yes; the obligation is already canonical.** Canon 15.4
requires that a receipt permit checking inclusion _without publicly
disclosing the chosen option_, which is exactly `BM-03`.

Two clarifications:

1. `VoteReceipt.vote_envelope_reference` must not be a value that a third
   party can use to _locate the voter_; it locates the **envelope**. The
   selected construction satisfies this because the confirmation code
   derives only from the ballot's own encryptions `[E-05]`.
2. Canon 15.4 does not say a receipt must not prove **participation**. It
   cannot be made not to, and `T-P16A-25` records the residual. The
   clarification is that canon 15.4's guarantee is about **content**, not
   about the fact of participation.

### `CQ-05` — Does `Tally.result_data` admit a homomorphic aggregate and trustee shares?

**Yes for the aggregate; the shares have no canonical home.**

`Tally` carries `input_set_hash` — which maps cleanly to the closure
checkpoint fixing the ballot set (`BM-20`) — `algorithm_version`,
`result_data` and `tally_signature`. A homomorphic aggregate and a decrypted
result fit `result_data`.

**Decryption shares and their proofs do not fit anywhere in canon 15.5**,
and they must be published (`BB-17`, `KC-10`). Nor do the key ceremony's
artefacts. This is the second half of the finding in §4.

**Clarification required:** that `Tally.verification_status` is not
satisfied by an internal check — that it requires verification against
published artefacts by a party other than the tally service (`BM-24`,
`BM-28`).

### `CQ-06` — Does `ResultPublication`'s count set conflict with `NO INTERMEDIATE TALLY`?

**No, provided the timing rule is explicit.** Canon 15.6 gives
`ResultPublication` an `eligible_count`, a `credential_count`, an
`accepted_vote_count` and a `rejected_vote_count`. Each of these is a
turnout figure or derivable from one, and each is prohibited before closure
by `ADR-094` and `IT-11`.

Canon does not state when they may be populated, because canon 15.6
describes a _publication_, which by definition follows the tally.

**Clarification required:** that these counts exist **only** in a
`ResultPublication`, that a `ResultPublication` exists only after
`voting_closed`, that no projection, metric, dashboard or export may
compute them earlier, and that they are subject to `SD-01` … `SD-09`
disclosure control on publication.

Also noted and **not** changed: canon 15.6's rule that the passing of
`challenge_deadline_at` is _"необходимое, но не достаточное условие
окончательности результата"_ — a necessary but not sufficient condition for
finality — aligns exactly with `PACK-16A-FAILURE-AND-ABORT-MODEL.md` §5's
uncertifiable-result path, and PACK-16A relies on it.

---

## 3. What is **not** a canonical question

| Not a canon issue             | Why                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------- |
| The choice of protocol family | Canon describes domain structure, not cryptographic construction              |
| Challenge/spoil               | `Ballot` already carries `challenge_window_hours` (15.1) and ADR-010 added it |
| The no-revoting decision      | A profile property; canon permits both (`CQ-02`)                              |
| `disclosure_min_cell`         | PACK-12/`FIR-INV-011`; unchanged, and no change proposed                      |
| Role separation               | `FIR-ROLE-005`; a register and matrix concern, not a canonical one            |
| Reason-code namespaces        | The Canonical Schema Registry is a registry, not the canon                    |
| The legal boundary            | Governance, not canon                                                         |

---

## 4. The finding that is likely to become an amendment — recorded, not proposed

**Three artefact classes required by the selected architecture have no
canonical home:**

```text
1. The bulletin board's per-ballot public entries and its signed,
   chained checkpoints — and PublicLedgerEntry may not be used (CQ-03).
2. The trustee / guardian model: guardian identity, key-ceremony evidence,
   polynomial commitments, decryption shares and their proofs (CQ-05).
3. The mirror set and mirror-divergence evidence (BB-28 … BB-32).
```

**PACK-16A does not propose an amendment**, for three reasons:

1. **Nothing is built.** An amendment adopted for a specification that
   later changes is an amendment made twice.
2. **The shapes are not yet fixed.** They depend on PACK-16B's parameter
   and ceremony decisions and PACK-16C's board specification, neither of
   which exists.
3. **The discipline this project has kept.** PACK-13, PACK-14 and PACK-15
   each refused to settle a decision from outside the round that owns it,
   and PACK-15 §31 closed six canonical questions **without** an amendment
   on exactly this reasoning.

**What is recorded instead**, so that it cannot be discovered late:

| ID      | Amendment candidate                                         | Owning round        | Affected canon clauses                            |
| ------- | ----------------------------------------------------------- | ------------------- | ------------------------------------------------- |
| `CA-01` | A bulletin-board publication aggregate and checkpoint chain | **PACK-16C**        | new section under 15; 19a.1 prohibition preserved |
| `CA-02` | A trustee / key-ceremony evidence aggregate                 | **PACK-16B or 16C** | new section under 15; 5.9 Tally Context           |
| `CA-03` | A mirror registry and divergence-evidence record            | **PACK-16C**        | new section; 18.1 `AuditEvent` interaction        |

If an amendment is proposed, it must carry — as PACK-10's amendment
material did — affected clauses, rationale, compatibility consequences,
security consequences, migration consequences and the required approval.
**None of that is produced here, and none of it is deemed approved.**

---

## 5. Compatibility statement

| Check                                                   | Result                                                         |
| ------------------------------------------------------- | -------------------------------------------------------------- |
| Does PACK-16A add a canonical aggregate?                | **No**                                                         |
| Does it add a field to an existing aggregate?           | **No**                                                         |
| Does it add or change a status?                         | **No**                                                         |
| Does it change an owner?                                | **No**                                                         |
| Does it create a prohibited edge?                       | **No** — §1 and §3 check every relevant prohibition            |
| Does it weaken any canonical prohibition?               | **No** — every clarification narrows rather than relaxes       |
| Does it modify `TZ-00-domain-event-canon.md`?           | **No**                                                         |
| Does it modify `canon-version.json`?                    | **No**                                                         |
| Does it change `CANON_VERSION`?                         | **No — it stays `0.8.0`**                                      |
| Does it require a canon amendment **now**?              | **No**                                                         |
| Does it identify amendment candidates for later rounds? | **Yes — `CA-01`, `CA-02`, `CA-03`, recorded and not proposed** |

Note for completeness: `docs/canonical/canon-version.json` declares
`repository_compatibility: ">=0.1.0 <0.16.0"`. This round leaves
`REPOSITORY_VERSION` at `0.15.0`, inside that range. **A future
implementation candidate targeting `0.16.0` will need that bound revisited
— which is a version-governance act belonging to PACK-16D, not a canon
amendment, and it is noted here so that it is not discovered at packaging
time.** `OD-P16A-12` records it.

---

## 6. Conclusion

```text
NO CANON CHANGE MADE
CANON CLARIFICATION REQUIRED — six clarifications, CQ-01 … CQ-06
CANON AMENDMENT NOT PROPOSED
CANON AMENDMENT CANDIDATES RECORDED — CA-01, CA-02, CA-03
CANON_VERSION REMAINS 0.8.0
```

**ASSESSED. NO CANON CHANGE. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**
