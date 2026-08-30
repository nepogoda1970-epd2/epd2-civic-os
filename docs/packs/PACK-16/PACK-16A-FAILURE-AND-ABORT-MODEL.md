# PACK-16A — Failure and Election-Abort Model

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Extends `PACK-15-FAILURE-MODE-MATRIX.md`, which remains in force. The
governing rule is PACK-15 §27's, unchanged:

> **Fail closed wherever failing open would produce a wrong participation,
> and fail visibly always.**

---

## 1. Outcome vocabulary

| Outcome    | Meaning                                                                           |
| ---------- | --------------------------------------------------------------------------------- |
| `continue` | Proceed; the event is recorded                                                    |
| `pause`    | Stop accepting new ballots; existing ballots stand; the window clock is suspended |
| `suspend`  | Stop the context indefinitely pending a governance decision                       |
| `extend`   | Lengthen the window; requires a recorded decision and participant notification    |
| `abort`    | Stop the context before a result; no result is produced                           |
| `annul`    | Declare a produced or producible result void                                      |
| `re-run`   | Hold the context again, with new keys, new parameters and new authorisations      |

Two structural rules:

```text
A context that is ABORTED or ANNULLED is never partially salvaged.
A RE-RUN is a new context: new manifest, new key ceremony, new
   authorisations, new board. It never reuses a key, a parameter set,
   an authorisation or a board from the failed context.
```

The second rule exists because reusing a key across a failed and a
re-run context makes the failed context's ballots decryptable by the
re-run's ceremony.

---

## 2. The matrix

**Decider** is the party with authority. **Concurrence** marks where the
Independent Auditor's agreement is required, not merely their notification.

| ID           | Condition                                            | Outcome                                                  | Decider          | Auditor concurrence | Evidence preserved                              | Told to participants                                         | Published                                | Never silently corrected                                  |
| ------------ | ---------------------------------------------------- | -------------------------------------------------------- | ---------------- | ------------------- | ----------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------- | --------------------------------------------------------- |
| `FM-P16A-01` | **Invalid election manifest**                        | refuse activation                                        | `R-01`           | no                  | Validation record                               | Vote not opened; reason                                      | Reason code                              | The manifest is never edited after `voting_open`          |
| `FM-P16A-02` | **Invalid cryptographic parameters**                 | refuse activation                                        | `R-01`           | **yes**             | Validation record; parameter provenance         | Vote not opened; reason                                      | Reason code, parameter identifier        | Parameters are never "fixed up"                           |
| `FM-P16A-03` | **Handoff validation failure**                       | fail closed, per participant                             | system           | no                  | Credential stream                               | Retry; assisted path                                         | none                                     | —                                                         |
| `FM-P16A-04` | **Continuation-capability replay**                   | reject, distinct reason code                             | system           | no                  | Credential stream; integrity stream             | Already used; contact the dispute path                       | Aggregate after closure                  | Never re-issued automatically (`CC-08`)                   |
| `FM-P16A-05` | **Client proof-generation failure**                  | fail closed; no ballot submitted                         | system           | no                  | Client reason code only                         | Try again; use another device; assisted path                 | Aggregate after closure                  | A ballot is never submitted without proofs                |
| `FM-P16A-06` | **Weak randomness detected in the client**           | **fail closed; refuse to encrypt**                       | system           | no                  | Reason code                                     | This device cannot be used safely; alternatives              | Aggregate after closure                  | Never degrade to a weaker source                          |
| `FM-P16A-07` | **Submission interrupted after consumption**         | **fail closed; capability not restored**                 | system           | no                  | Credential stream                               | **The participation is lost for this context**; dispute path | Aggregate after closure                  | §3                                                        |
| `FM-P16A-08` | **Duplicate submission**                             | reject, distinct reason code                             | system           | no                  | Board stream                                    | Already recorded                                             | Aggregate after closure                  | Never overwrite (`BM-05`)                                 |
| `FM-P16A-09` | **Bulletin-board outage**                            | **pause** casting                                        | `R-01` or `R-14` | no                  | Board and system streams                        | Voting paused; expected resumption                           | Pause event and reason                   | Ballots are never accepted while unpublishable            |
| `FM-P16A-10` | **Bulletin-board equivocation detected**             | **abort — uncertifiable**                                | `R-01`           | **yes**             | Divergent checkpoints from every mirror         | Vote stopped; independent evidence being examined            | Divergence evidence in full              | Never reconcile by picking a view                         |
| `FM-P16A-11` | **Mirror inconsistency**                             | **pause**, then abort if unresolved                      | `R-01`           | **yes**             | Per-mirror checkpoint chains                    | Voting paused; reason                                        | Divergence evidence                      | Never "resync" the minority silently                      |
| `FM-P16A-12` | **Proof-verification failure on a published ballot** | exclude with public reason; escalate if outcome-changing | `R-01`           | **yes**             | The ballot, its proofs, the verification result | An exclusion occurred; the count and the reason              | Exclusion with reason code (`EX-03`)     | Never remove the ballot from the board                    |
| `FM-P16A-13` | **Trustee unavailable, quorum still met**            | `continue`                                               | `R-08`           | notified            | Ceremony record; compensated-share evidence     | none required                                                | Absence recorded                         | Absence is never concealed (`KC-11`)                      |
| `FM-P16A-14` | **Quorum lost**                                      | **pause → abort → annul → re-run**                       | `R-01`           | **yes**             | Ceremony record; share inventory                | The result cannot be produced; the vote will be held again   | Quorum-loss event and reason             | **No escrow, ever** (`KC-15`, §4)                         |
| `FM-P16A-15` | **A partial tally is produced**                      | **abort; annul**                                         | `R-01`           | **yes**             | Full incident record                            | The vote is void; it will be held again                      | The incident, the reason, the remedy     | Never "unpublish" and continue                            |
| `FM-P16A-16` | **Unexpected plaintext exposure**                    | **abort; annul**                                         | `R-01`           | **yes**             | Full incident record; DPO notified              | The vote is void; what was exposed; what was not             | The incident and its scope               | Never continue after secrecy is lost                      |
| `FM-P16A-17` | **Identity correlation detected**                    | **suspend; investigate; annul if confirmed**             | `R-01`           | **yes**             | Correlation-risk event; integrity stream        | The vote is suspended and why                                | The finding, without the correlated data | Never resolve by deleting the evidence                    |
| `FM-P16A-18` | **Cross-boundary trace detected**                    | **suspend**; annul if the trace was persisted            | `R-01`           | **yes**             | Integrity stream; trace configuration record    | Same                                                         | Same                                     | Never remove the trace and carry on                       |
| `FM-P16A-19` | **Software-integrity failure**                       | **pause**; abort if ballots were affected                | `R-01` + `R-14`  | **yes**             | Build attestations; artefact hashes             | Voting paused; reason                                        | The finding                              | Never redeploy over the evidence                          |
| `FM-P16A-20` | **Supply-chain integrity failure**                   | **pause**; abort if ballots were affected                | `R-01` + `R-14`  | **yes**             | Dependency inventory; attestations              | Same                                                         | The finding                              | Same                                                      |
| `FM-P16A-21` | **Clock inconsistency beyond the declared bound**    | **pause**; `extend` or abort                             | `R-01`           | **yes**             | Checkpoint chain; skew measurements             | Window adjusted, or vote stopped                             | The adjustment and its reason            | Never adjust a window retroactively                       |
| `FM-P16A-22` | **No implementation satisfies `KC-23`–`KC-25`**      | **do not proceed** — the context is never activated      | `R-01`           | **yes**             | Assessment record                               | The vote will be held by another means                       | The reason                               | Never proceed on an unverifiable library                  |
| `FM-P16A-23` | **Archive verification failure**                     | **suspend archive operations; investigate**              | `R-16` + `R-01`  | **yes**             | Archive integrity record; last good commitment  | If a result is affected, the participants are told           | The failure and its scope                | Never re-create the archive from working data             |
| `FM-P16A-24` | **Post-election evidence loss**                      | **the result becomes uncertifiable** (§5)                | `R-01`           | **yes**             | Whatever survives; the loss itself              | The result can no longer be independently verified           | The loss, its extent and its consequence | Never reconstruct evidence from a privacy-breaking backup |
| `FM-P16A-25` | **Denial of service against casting**                | `extend` if participation was impaired                   | `R-01`           | notified            | Availability records                            | Window extended; reason                                      | The extension and its reason             | Never extend silently                                     |

---

## 3. `FM-P16A-07` — the uncomfortable one, stated in full

A participant consumes their continuation capability, the submission fails,
and the capability is not restored. **They cannot vote in that context.**

This is the direct consequence of `CC-08`, and the reasoning is PACK-15's
in a new place: a capability that can be re-obtained after a failed cast can
be re-obtained after a _successful_ cast whose success signal was lost, and
that is a double-vote path. Distinguishing the two cases requires knowing
whether a ballot from that participation reached the board — which requires
the link this architecture exists to prevent.

**The governed remedy**, and it is deliberately narrow:

1. The failure is recorded with a distinct reason code.
2. Where the failure was **systemic** — a board outage, a service failure,
   a client defect affecting a class of participants — the Election Board
   may `extend` the window and authorise a **fresh eligibility decision and
   a fresh authorisation** through the PACK-15 revoke-then-reissue path,
   under dual control, before the revocation cutoff. This works because the
   remedy operates on the **identity side**, where the participant is
   known, and never asks the voting side who anyone is.
3. Where the failure was **individual** and the cutoff has passed, **the
   participation is lost for that context** and the dispute path records it
   as an irreducible loss.

**Inventing a recovery that requires linking a person to a ballot would
trade the system's central guarantee for one voter's convenience, and that
trade is refused.** PACK-15 §13.2's sentence, applied one step further
along the chain.

---

## 4. Quorum loss and the refusal to build a way out

`FM-P16A-14` is the failure most likely to produce pressure for a
"pragmatic" solution. The prohibited responses are enumerated in
`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §4.2 and restated here
because this is where they would be proposed:

```text
No key escrow.
No recovery guardian.
No single-location share backup.
No administrative decryption override.
No lowering of k after ballots are cast.
No reconstruction of a lost share outside a quorum ceremony.
```

**The trade:** an unrecoverable election is preferable to a recoverable
secret. **The cost:** every participant in that context voted for nothing
and must vote again. Both halves are stated, and the second is not
minimised.

---

## 5. Uncertifiable results

A result is **uncertifiable** when the published evidence is insufficient
for an independent party to verify it. A result may be uncertifiable and
still be _arithmetically correct_; certifiability is about evidence, not
about arithmetic.

Conditions producing an uncertifiable result:

```text
bulletin-board equivocation that cannot be resolved from evidence
irrecoverable loss of the checkpoint chain
loss of decryption-share proofs
loss of the published parameter set or its provenance
archive verification failure covering the result
detection that the proofs were verified by an implementation later shown
   to be unsound (F-INF-2)
```

**What happens:**

1. The Election Board, **with Independent Auditor concurrence**, declares
   the result uncertifiable.
2. The declaration is published with its reason and its evidence.
3. The result is **not published as verified** and, if already published,
   is republished with the declaration attached.
4. Governance decides: annul and re-run, or accept a recorded irreducible
   loss.
5. **The declaration is never withdrawn by later assertion.** It can only be
   superseded by evidence that resolves the specific defect.

**An uncertifiable result is not the same as a wrong result, and calling it
one would be as dishonest as concealing it.** The published statement must
say which it is, and where the evidence stops.

---

## 6. Dependencies never bypassed

Extending PACK-15 §27's two — the audit stream and the replay store — with
four more. **Under no load, with no flag, in no incident:**

```text
the audit stream
the replay / spent-authorisation store
proof verification before acceptance          (BM-16)
bulletin-board publication before acceptance is reported to the voter
the closure checkpoint before aggregation      (BM-20)
the trustee quorum before any decryption       (BM-22)
```

A ballot that cannot be published is a ballot that has not been recorded,
and telling a voter otherwise is the failure mode that makes every
verifiability claim in this pack false.

---

## 7. Participant communication

| Situation                     | What participants are told                                                                         | What they are **not** told                     |
| ----------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Pause                         | Voting is paused, why in plain language, and when it is expected to resume                         | How many ballots exist                         |
| Extension                     | The window is longer, why, and the new closing time                                                | Turnout, or why it was low                     |
| Abort                         | The vote has stopped, why, and what happens next                                                   | Any partial outcome                            |
| Annulment                     | The result is void, why, and when the vote will be held again                                      | Any result figure from the annulled context    |
| Uncertifiable result          | The result cannot be independently verified, what evidence is missing, and what governance decided | A reassurance that it is nevertheless correct  |
| Individual submission failure | The submission did not complete, what to do now, and the dispute path                              | Whether anyone else succeeded                  |
| Individual participation lost | The participation could not be completed for this context, and how to raise it                     | Anything implying a person did or did not vote |

**Never sent, in any failure communication:** ballot content · person-level
participation status · any confirmation that a person did or did not
participate · turnout · any partial outcome. PACK-15 §24's prohibitions
apply unchanged.

---

## 8. What PACK-16A does not decide

```text
Availability targets, capacity and resilience         → PACK-17
Incident-response runbooks                            → PACK-17
The clock-skew bound                                   → PACK-16C
Notification channel selection and timing              → FRONT-PACK, PACK-09
Retention of failure evidence                          → OD-P16A-07, PACK-09
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
