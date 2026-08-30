# PACK-16B — Guardian Lifecycle

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. States

```text
nominated
due_diligence_pending
approved
ceremony_enrolled
authenticated
contribution_generated
share_exchange_pending
share_verified
ceremony_complete
active                          ← ACTIVATION LOCK sits immediately before this
temporarily_unavailable
suspected_compromise
confirmed_compromise
disqualified_before_activation
absent_at_decryption
decryption_share_submitted
completed
retired
```

**The activation lock is the hinge of this document.** Before it, a
guardian can be added, removed, replaced or disqualified and the ceremony
restarts. After it, none of those is possible, and every state exists to
describe what happens to an election that must proceed anyway.

---

## 2. Transitions

Reversibility: **none** (absorbing) · **pre-activation** (reversible only
by restarting the ceremony) · **operational** (reversible within a context).

| From → To                                             | Actor                                | Authority                                                   | Evidence                                                                                          | Reversibility          | Effect on the election                                                | Public                                                | Audit |
| ----------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- | ----- |
| — → `nominated`                                       | Election Board                       | Board decision                                              | Nomination record with organisation                                                               | pre-activation         | none                                                                  | yes                                                   | yes   |
| `nominated` → `due_diligence_pending`                 | Ceremony Coordinator                 | —                                                           | Independence declarations (`GI-04`)                                                               | pre-activation         | none                                                                  | yes                                                   | yes   |
| `due_diligence_pending` → `approved`                  | Election Board                       | **+ Independent Auditor concurrence**                       | Pairwise and composition assessment (`GI-01`, `GI-13`)                                            | pre-activation         | none                                                                  | yes                                                   | yes   |
| `due_diligence_pending` → _nomination refused_        | Election Board                       | Board decision                                              | Recorded ground; hard-test failure needs no mitigation                                            | n/a                    | none                                                                  | yes (that a refusal occurred and the class of ground) | yes   |
| `approved` → `ceremony_enrolled`                      | Ceremony Coordinator                 | —                                                           | Enrolment record; device attestation reference                                                    | pre-activation         | none                                                                  | yes                                                   | yes   |
| `ceremony_enrolled` → `authenticated`                 | Guardian                             | PACK-14 authentication at ceremony assurance (`KC-06`)      | Authentication evidence; device attestation                                                       | pre-activation         | none                                                                  | no (that it occurred: yes)                            | yes   |
| `authenticated` → `contribution_generated`            | Guardian                             | —                                                           | Coefficient commitments, `κ_i`, Schnorr proofs; **preceded by the EPD² pre-commitment** (`KY-07`) | pre-activation         | none                                                                  | yes                                                   | yes   |
| `contribution_generated` → `share_exchange_pending`   | Guardian                             | —                                                           | Encrypted shares, published in the transcript (`CT-09`)                                           | pre-activation         | none                                                                  | yes                                                   | yes   |
| `share_exchange_pending` → `share_verified`           | Receiving guardians                  | —                                                           | Verification of the Feldman equation for every received share                                     | pre-activation         | none                                                                  | yes                                                   | yes   |
| `share_verified` → `ceremony_complete`                | All guardians                        | Unanimous confirmation                                      | Joint key, transcript, Auditor verification, Board acceptance                                     | pre-activation         | none                                                                  | yes                                                   | yes   |
| **`ceremony_complete` → `active`**                    | **Election Board**                   | **+ Independent Auditor concurrence — the ACTIVATION LOCK** | Signed ceremony checkpoint                                                                        | **none**               | The context may proceed to `issuance_open`                            | yes                                                   | yes   |
| any pre-activation → `disqualified_before_activation` | Election Board                       | **+ Independent Auditor concurrence**                       | Complaint record and adjudication (complaint model)                                               | none for that guardian | **Ceremony restarts from scratch**                                    | yes                                                   | yes   |
| `active` → `temporarily_unavailable`                  | Guardian, or Coordinator on evidence | —                                                           | Declared unavailability                                                                           | **operational**        | none while `n − k` margin remains                                     | yes                                                   | yes   |
| `temporarily_unavailable` → `active`                  | Guardian                             | Re-authentication                                           | Authentication evidence                                                                           | operational            | none                                                                  | yes                                                   | yes   |
| `active` → `suspected_compromise`                     | Anyone, with evidence                | Incident Commander acknowledges                             | Incident record                                                                                   | operational            | §4 of the compromise model                                            | yes                                                   | yes   |
| `suspected_compromise` → `active`                     | Election Board                       | **+ Auditor concurrence**                                   | Investigation outcome, published                                                                  | operational            | none                                                                  | yes                                                   | yes   |
| `suspected_compromise` → `confirmed_compromise`       | Election Board                       | **+ Auditor concurrence**                                   | Investigation outcome, published                                                                  | **none**               | §4 of the compromise model                                            | yes                                                   | yes   |
| `active` → `absent_at_decryption`                     | Ceremony Coordinator                 | —                                                           | Attendance record at the decryption ceremony                                                      | none for that ceremony | Tolerated while `\|U\| ≥ k`; **published, never concealed** (`KC-11`) | yes                                                   | yes   |
| `active` → `decryption_share_submitted`               | Guardian                             | —                                                           | The share and its proof, verified (`KC-10`)                                                       | none                   | Contributes to the tally                                              | yes                                                   | yes   |
| `decryption_share_submitted` → `completed`            | system                               | —                                                           | Tally published                                                                                   | none                   | none                                                                  | yes                                                   | yes   |
| `absent_at_decryption` → `completed`                  | system                               | —                                                           | Tally published without that guardian                                                             | none                   | none                                                                  | yes                                                   | yes   |
| `completed` → `retired`                               | Guardian                             | —                                                           | **Destruction attestation for the guardian's share**                                              | none                   | none                                                                  | yes                                                   | yes   |

---

## 3. Secret-material handling per state

| State                                  | Holds secret material?                                  | Rule                                                                                                                  |
| -------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `nominated` … `authenticated`          | **No**                                                  | Nothing exists yet                                                                                                    |
| `contribution_generated`               | **Yes** — coefficients, `ζ_i`, Schnorr nonces           | On the dedicated device only; never exported                                                                          |
| `share_exchange_pending`               | Yes                                                     | Shares are encrypted to the recipient's `κ_ℓ` before leaving the device                                               |
| `share_verified` … `ceremony_complete` | Yes                                                     | —                                                                                                                     |
| **on completion of the ceremony**      | **Reduced** — the guardian retains only `z_i` and `ẑ_i` | The specification states initial secrets _"may be discarded"_ `[F-13]`; **EPD² requires their destruction** (`GL-16`) |
| `active`                               | `z_i`, `ẑ_i`                                            | Per-guardian custody only                                                                                             |
| `temporarily_unavailable`              | Yes, retained                                           | Custody unchanged; the material does not move                                                                         |
| `suspected_compromise`                 | Yes, and treated as exposed                             | The material is **not** moved, deleted or rotated during investigation — it is evidence                               |
| `confirmed_compromise`                 | Assume disclosed                                        | Compromise model §4                                                                                                   |
| `absent_at_decryption`                 | Retained by the absent guardian                         | **Never reconstructed by anyone else** `[F-11]`                                                                       |
| `completed`                            | Retained until retirement                               | Retained through any dispute window                                                                                   |
| `retired`                              | **None**                                                | Destroyed, with an attestation recorded (`GL-17`)                                                                     |

| ID      | Rule                                                                                                                                                                                                                                                                                                              |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GL-16` | On ceremony completion the guardian **destroys** the initial secret `s_i`, `ŝ_i`, all polynomial coefficients and all Schnorr nonces, retaining only `z_i` and `ẑ_i`. The specification permits discarding; **EPD² requires it and requires an attestation**                                                      |
| `GL-17` | On retirement the guardian destroys `z_i` and `ẑ_i` and attests to it; the attestation is published                                                                                                                                                                                                               |
| `GL-18` | **No secret material leaves the guardian's device in unencrypted form, ever**, including during an investigation                                                                                                                                                                                                  |
| `GL-19` | The specification's suggested forensic procedure — all guardians releasing their secret information to investigate a failure `[F-12]` — is **permitted only before activation** and only under the complaint model's controls. **After activation it is prohibited**, because it reconstructs the election secret |

`GL-19` is the most consequential rule in this document. The upstream
specification offers full-secret release as _"one possible way"_ to
investigate `[F-12]`. Before activation that is a reasonable forensic tool
against material that protects nothing yet. After activation it is a
quorum-equivalent disclosure with a procedure attached.

---

## 4. Prohibited after activation

```text
NO silent guardian replacement.
NO guardian substitution, silent or otherwise.
NO threshold reduction.
NO quorum reconfiguration.
NO new guardian enrolment.
NO private-key rotation in place.
NO re-run of the key ceremony for the same context.
```

| ID      | Rule                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `GL-14` | After the activation lock, the guardian set is **fixed for the context**. A guardian who is lost is _absent_, not replaced  |
| `GL-15` | `k` and `n` are fixed at the same moment and cannot change (`GQ-05`, `TP-05`)                                               |
| `GL-20` | A context needing a different guardian set needs a **different context**: new manifest, new ceremony, new keys, new board   |
| `GL-21` | There is **no operation** that adds, removes, substitutes or re-keys a guardian in an active context, and none may be added |

`GL-21` is written as a structural statement rather than a policy because
policies get exceptions under pressure and missing operations do not.

---

## 5. Absence versus compromise versus loss

Three different things that get conflated, with three different outcomes.

| Situation                                 | State                                              | Election effect                                                                                                                        | Recovery                                   |
| ----------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Guardian is travelling and unreachable    | `temporarily_unavailable`                          | None while `n − k` margin remains                                                                                                      | They return                                |
| Guardian misses the decryption ceremony   | `absent_at_decryption`                             | Tolerated while `\|U\| ≥ k`; **published**                                                                                             | Not needed — the remaining quorum decrypts |
| Guardian's device is lost or destroyed    | `temporarily_unavailable` → `absent_at_decryption` | Same as absence, **provided the share was backed up under that guardian's own custody** (backup doc §3); otherwise a permanent absence | Per-guardian backup, or none               |
| Guardian's material may have been exposed | `suspected_compromise`                             | Compromise model §3                                                                                                                    | Investigation                              |
| Guardian's material is known exposed      | `confirmed_compromise`                             | Compromise model §4                                                                                                                    | None — the exposure is a fact              |
| More than `n − k` guardians unavailable   | quorum loss                                        | **The result is unobtainable**                                                                                                         | **Re-run only** — compromise model §5      |

**Absence is normal and is planned for; compromise is an incident; loss of
quorum is an annulment.** Collapsing them is how a system ends up with an
escrow.

---

## 6. Due diligence, before nomination is confirmed

| ID      | Check                                                                                                                       |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `GL-01` | Identity of the natural person, at PACK-14 identity-proofing assurance                                                      |
| `GL-02` | The organisation they represent, and their authority to represent it                                                        |
| `GL-03` | **Independence declarations** for every pair (`GI-04`)                                                                      |
| `GL-04` | **Not a candidate** in this context (`GQ-07`)                                                                               |
| `GL-05` | **Not holding a prohibited role** for this context (guardian/quorum model §6)                                               |
| `GL-06` | Custody arrangement declared and meeting the custody requirements                                                           |
| `GL-07` | Device attestation available, or an accepted alternative recorded                                                           |
| `GL-08` | Availability for both the key ceremony and the decryption ceremony, with dates                                              |
| `GL-09` | Accessibility needs declared, so that they are met rather than worked around (`PACK-16B-KEY-CEREMONY-SPECIFICATION.md` §10) |
| `GL-10` | Understanding of the obligations, including that **no replacement is possible after activation**                            |
| `GL-11` | Agreement to publication of name and organisation (`GQ-06`)                                                                 |
| `GL-12` | Agreement to the destruction obligations (`GL-16`, `GL-17`)                                                                 |
| `GL-13` | Board approval **with Independent Auditor concurrence**                                                                     |

`GL-10` is a due-diligence item and not a formality: a guardian who does
not understand that their unavailability at decryption is survivable but
their absence beyond `n − k` is not, cannot make an informed commitment.

---

## 7. Publication

| Published                                              | Not published                                               |
| ------------------------------------------------------ | ----------------------------------------------------------- |
| Name, organisation, and state transitions              | Authentication credentials and device identifiers           |
| Public keys, commitments and Schnorr proofs            | Any secret, share, coefficient or nonce                     |
| That a guardian was absent at decryption               | Why they were absent                                        |
| That a nomination was refused, and the class of ground | Personal details behind the ground                          |
| Disqualification and its adjudicated basis             | Material that would identify a complainant beyond necessity |
| Destruction attestations                               | —                                                           |

**Absence is published, never concealed** (`KC-11`). The published fact is
that the tally was produced by a set `U` that did not include guardian `i`
— which anyone can already infer from the decryption shares, so concealing
it would only mislead the people who did not check.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
