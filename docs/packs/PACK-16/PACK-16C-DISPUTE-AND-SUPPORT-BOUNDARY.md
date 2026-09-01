# PACK-16C — Dispute and Support Boundary

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The boundary, stated first

```text
Support can help a voter USE the system.
Support can NEVER help a voter's BALLOT.

There is no operator, no administrator, no engineer, no auditor and no
combination of them who can find, read, change, re-cast, recover or
delete a specific person's ballot. Not because they are forbidden to —
because the system does not contain the link that would let them.
```

| ID      | Rule                                                                                                                                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP-01` | **Support's inability to act on a ballot is architectural, not procedural** (`CC-04`, `VP-15`). A policy could be waived; this cannot                                                                      |
| `DP-02` | **This is told to voters before they vote, not when they ask for help.** A person who believes support can fix a mistaken cast will make different decisions from one who knows it cannot (`CF-*` step 13) |

---

## 1. What support can and cannot do

| Request                                                                                 | Can support act?                     | What actually happens                                                                                                               |
| --------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| "The page will not load"                                                                | **yes**                              | Ordinary technical help; no ballot involvement                                                                                      |
| "I do not understand the difference between a local check and a public audit challenge" | **yes**                              | Explanation from the governed catalogue (`CH-52`); no advice on _what_ to choose                                                    |
| "I used my public audit challenge and want another"                                     | **no**                               | One per capability in the initial profile (`CH-43`). **Local checks remain unlimited and the cast entitlement is intact** (`CH-45`) |
| "How many slots are left?"                                                              | **no**                               | Occupancy is never disclosed to anyone (`TC-81`, `RN-16C-29`)                                                                       |
| "My device says my ballot could not be encrypted"                                       | **yes**                              | Client diagnosis, build check; the voter re-runs the flow, nothing is spent (`VP-04`)                                               |
| "I never got a response after submitting"                                               | **yes**                              | Status-check path by retry token, voter-initiated (`CN-26`); support does not perform it _for_ the voter                            |
| "My code is not in its batch commitment"                                                | **yes, as a dispute, during voting** | `DP-05`, `DP-19`; publication failure is a first-class outcome (`RE-08`)                                                            |
| "I lost my receipt"                                                                     | **yes**                              | Re-derivable from the confirmation code; if the code is lost too, nothing can be recovered — and nothing is lost either (`RE-04`)   |
| "I voted for the wrong option"                                                          | **no**                               | No revoting exists (`BL-07`). Support may not offer, imply or arrange a remedy                                                      |
| "Please tell me what I voted for"                                                       | **no**                               | Nobody holds it (`VP-15`)                                                                                                           |
| "Please delete my ballot"                                                               | **no**                               | Append-only; no deletion operation exists (`BL-03`)                                                                                 |
| "Please tell me whether X voted"                                                        | **no**                               | The fact is not held in a queryable form (`TC-08`)                                                                                  |
| "Please re-open the election for me"                                                    | **no**                               | Window is fixed by signed checkpoints                                                                                               |
| "I was coerced"                                                                         | **partially**                        | Governance and legal path; the ballot itself cannot be identified or withdrawn (`CB-*`)                                             |

| ID      | Rule                                                                                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP-03` | **No support tool exists that takes a ballot identifier as input and does anything privileged with it.** Such a tool is prohibited from being built, and its absence is checkable (`FIR-INV-*` lineage) |
| `DP-04` | **A support interaction never requires the voter to reveal their confirmation code**, and support never records it. A code in a support record is a participation proof in a case file                  |

---

## 2. Dispute classes

| Class                                                   | Trigger                                                                                                                                    | Who decides                              | Public?                                  | Remedy available                                                                         |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------- |
| `D-01` **Code not committed**                           | The voter's leaf is absent from its **named** sealed batch window, detectable **before closure** by the voter's own inclusion-proof lookup | Board operator, then Auditor             | **yes, as an incident, without a count** | Publish, or `publication_disputed` → election-level (`PA-*`, `FM-16C-20`)                |
| `D-10` **Capacity pause**                               | Publication-bearing submissions are refused because every predeclared slot in the interval is unavailable                                  | Election Board, with Auditor concurrence | **yes, as an incident with no figure**   | Pause · governed extension · abort · re-run (`FM-16C-29`)                                |
| `D-11` **Public audit challenge refused**               | The entitlement is spent, or no challenge-reserved slot could be reserved                                                                  | system, then support                     | aggregate after closure                  | Local checks remain available and the cast entitlement is intact (`CH-45`, `TC-75`)      |
| `D-09` **Batch artefact missing or invalid at closure** | A commitment without an opening, a root that does not recompute, a duplicate leaf opening, or a reconciliation that does not close         | Auditor                                  | **yes, always**                          | `abort` or `annul` (`FM-16C-22`…`FM-16C-27`); **never a silent re-derivation** (`TC-54`) |
| `D-02` **Board inconsistency**                          | A verifier or mirror reports divergence                                                                                                    | Auditor                                  | **yes, always**                          | Investigate; potentially uncertifiable (`FM-P16A-10`)                                    |
| `D-03` **Ballot fails verification**                    | Independent verifier reports `INVALID_BALLOT_PROOF`                                                                                        | Election Board + Auditor                 | **yes**                                  | Exclude with public reason; escalate if outcome-changing                                 |
| `D-04` **Challenge shows a mismatch**                   | A voter's challenge reveals the client encrypted something else                                                                            | Auditor, urgently                        | **yes**                                  | Suspend the client build; `FM-16C-13`; potentially annul                                 |
| `D-05` **Client build mismatch**                        | Published build digest ≠ served build                                                                                                      | Auditor                                  | **yes**                                  | Suspend; investigate (`FM-16C-01`)                                                       |
| `D-06` **Access failure**                               | A voter could not vote at all                                                                                                              | Election Board                           | aggregate                                | Extend, re-run, or alternative channel — never a substitute ballot                       |
| `D-07` **Coercion report**                              | A voter reports pressure                                                                                                                   | Governance, legal                        | as governance requires                   | Outside the cryptography; the ballot is not identifiable                                 |
| `D-08` **Result contested**                             | A party disputes the announced result                                                                                                      | Election Board + Auditor                 | **yes**                                  | Independent re-verification of the published record (`IV-*`)                             |

| ID      | Rule                                                                                                                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `DP-05` | **`D-01` is never answered with "not found".** It has its own reason code, its own path and a published outcome, because a missing code is either a voter error, a client defect or a broken promise, and the three must be distinguished in public (`RE-08`, `RN-16C-28`)                                   |
| `DP-19` | **`D-01` is now raisable during voting, not only after it.** The named batch window gives the voter a definite moment at which their ballot should have been committed, and a privacy-safe way to check (`PA-12`, `TC-36`). Under the first candidate's model this dispute could not be raised until closure |
| `DP-21` | **`D-11` is not a fault and is not styled as one.** The entitlement was announced before use, and refusing a check while cast capacity is intact is the partition working as designed (`TC-75`, `FMR-23`)                                                                                                    |
| `DP-22` | **`D-10` is answered with a governed plain-language pause message carrying no figures** (`TC-81`, `XA-34`)                                                                                                                                                                                                   |
| `DP-20` | **A `D-01` response never discloses occupancy.** It confirms or denies the voter's own leaf and nothing about the batch (`TC-40`)                                                                                                                                                                            |
| `DP-06` | **Every dispute class has exactly one owner and one published outcome.** A dispute that is resolved without a published outcome is not resolved                                                                                                                                                              |
| `DP-07` | **No dispute is resolved by acting on an individual ballot.** Every remedy is at the level of the build, the board, the context or the election                                                                                                                                                              |

---

## 3. Evidence a voter can bring

| Evidence                      | What it proves                                                  | What it does not prove                                 |
| ----------------------------- | --------------------------------------------------------------- | ------------------------------------------------------ |
| Confirmation code             | That a ballot with this code should be findable                 | Nothing about content                                  |
| Receipt                       | Publication status at issuance, and the checkpoint then current | Nothing about content (`RE-01`)                        |
| Signed publication commitment | That the service undertook to publish                           | That it did                                            |
| Challenge transcript          | That a _spoiled_ ballot opened to a stated content              | **Nothing about the ballot they later cast** (`CB-05`) |
| Screenshot                    | Nothing cryptographic                                           | —                                                      |

| ID      | Rule                                                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP-08` | **A voter's evidence is checked against public artefacts only.** No dispute requires a privileged lookup, because none exists                                                     |
| `DP-09` | **A challenge transcript is never treated as evidence of how the voter voted**, in a dispute or anywhere else, and the dispute process says so explicitly (`CB-06`)               |
| `DP-10` | **A voter is never asked to prove their identity in order to raise `D-01`**, because the dispute concerns a public artefact and identity would create the link the design removes |

---

## 4. Records and privacy

| ID      | Rule                                                                                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP-11` | **A support or dispute record never contains a ballot identifier, a confirmation code, a continuation reference or ballot content** (`PM-*` #31)                                                  |
| `DP-12` | **Published dispute outcomes never name the complainant**, and where the context is small enough that the class alone identifies them, the outcome is published in aggregate at closure (`TC-17`) |
| `DP-13` | **Support records follow PACK-15's retention lineage** and are not extended because an election record is retained (`ER-25`)                                                                      |
| `DP-14` | **The existence and count of disputes is published with the record** (artefact 29), because an election with no disputes and an election that absorbed them quietly must not look identical       |

---

## 5. Escalation

```text
support            → cannot act on ballots; routes to a class
board operator      → publication and board integrity only
Election Board      → context-level decisions, with published grounds
Independent Auditor → concurrence required for exclusion, annulment,
                      certification, and for D-02 / D-04 outcomes
governance / legal  → coercion, access, statute
```

| ID      | Rule                                                                                                                                                                                   |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP-15` | **No escalation path ends in an operator with ballot-level power**, because no such operator exists. Escalation increases the _scope_ of the decision, never the _reach_ into a ballot |
| `DP-16` | **The Auditor's concurrence is required for every remedy that changes the tallied set**, and the Auditor is independent of the Election Board (PACK-15 lineage, `EX-*`)                |
| `DP-17` | **An unresolved dispute at certification time is published as unresolved.** Certification with an open `D-02`, `D-03`, `D-04` or `D-08` is prohibited                                  |

---

## 6. What the voter is told in advance

```text
Once you cast, it is final. There is no undo, and nobody can undo it
for you — not support, not an administrator, not the party.

Nobody can see what you voted. That includes us. That is why nobody
can correct it either.

If your ballot does not appear on the public list by the published
deadline, tell us. That is a failure on our side, and it is handled
in public.
```

| ID      | Rule                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `DP-18` | **This text is in the governed catalogue and is shown before the irreversible step**, not only in a help page (`XA-15`, `CF-*`) |

---

## 7. What this document does not decide

```text
Support tooling and its interface           → PACK-16D, within DP-03
Dispute procedure under party statute        → GOVERNANCE
Legal remedies                                → outside EPD²'s specification
Retention periods for support records         → PACK-15 lineage, GOVERNANCE
Alternative-channel design                    → OD-P16A-09
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
