# PACK-16B — Incident and Notification Model

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The principle this model is built on

```text
A ceremony that only publishes its successes has published nothing.
```

The transcript already publishes what happened *inside* the ceremony
(`PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md`). This document specifies
what is **announced**, to whom, how quickly, and with what precision — for
nineteen events, of which nine are failures and four are the events an
operator would most prefer not to announce at all.

Three rules govern every row below.

| ID       | Rule                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `IN-20`  | **Notification is not discretionary.** No role may decide that an event on this list is not worth announcing; the only decisions available are *when* within the stated bound and *with what wording* from the governed catalogue |
| `IN-21`  | **Notification carries no secret material.** No share, no nonce, no partial decryption, no ballot, no ciphertext, no key, no credential, no person-to-ballot correlate. `RC-*` codes are the vocabulary, and §5 fixes what they may contain |
| `IN-22`  | **The notification and the evidence are separate objects.** The notification is a short public statement; the evidence is the transcript entry it points to. A notification is never the only record of what it announces |

---

## 1. The nineteen events

**Public** = published on the bulletin board and in the ceremony record,
readable without accreditation (`BB-36`).
**Auditor** = pushed to the Independent Auditor's channel, signed.
**Out-of-band** = a channel that does not depend on the system reporting the
problem — email/telephone to named individuals, per `IN-25`.

| ID      | Event                                | Public | Auditor | Out-of-band | Reason code                                    | Responsible actor              | Timing bound                          |
| ------- | ------------------------------------ | ------ | ------- | ----------- | ---------------------------------------------- | ------------------------------ | ------------------------------------- |
| `IN-01` | **Ceremony started**                 | **Yes — in advance** | Yes | Guardians | `ceremony.started`                    | Ceremony Coordinator (`R-08`)  | Announced **≥ 14 days before**; started at the announced time |
| `IN-02` | **Guardian nominated**               | **Yes** | Yes    | No          | `guardian.nominated`                           | Election Board (`R-01`)        | On nomination, **≥ 14 days before phase 5** |
| `IN-03` | **Guardian changed before ceremony** | **Yes** | Yes    | Guardians   | `guardian.replaced_before_ceremony`            | Election Board                 | Within 24 h of the decision, **with the reason** |
| `IN-04` | **Guardian authentication failed**   | Yes    | **Yes** | Guardian + their organization | `guardian_authentication.failed` | Ceremony Coordinator         | Immediately in-ceremony; publicly at the next checkpoint |
| `IN-05` | **Invalid contribution**             | **Yes** | **Yes** | The guardian concerned | `dkg.contribution_invalid`            | Ceremony Coordinator           | **Immediately** — it is arithmetically checkable by anyone |
| `IN-06` | **Invalid share**                    | **Yes** | **Yes** | Both guardians concerned | `share_verification.failed`          | The receiving guardian         | **Immediately**; the complaint follows within the phase-12 window |
| `IN-07` | **Complaint opened**                 | **Yes** | **Yes** | Respondent  | `complaint.opened`                             | The complainant                | **Immediately, before adjudication** (`CD-03`) |
| `IN-08` | **Guardian disqualified**            | **Yes** | **Yes** | All guardians, the organization | `disqualification.recorded`  | Election Board                 | Within 24 h of adjudication, **with the ground** |
| `IN-09` | **Ceremony aborted**                 | **Yes** | **Yes** | All roles   | `ceremony.aborted`                             | Ceremony Coordinator           | **Within 1 h**, with the abort condition's `FM-16B-*` identifier |
| `IN-10` | **Ceremony completed**               | **Yes** | Yes    | All roles   | `ceremony.completed`                           | Ceremony Coordinator           | At the phase-19 checkpoint                |
| `IN-11` | **Joint key published**              | **Yes** | Yes    | No          | `joint_key.published`                          | Bulletin-Board Operator (`R-06`) | At phase 14 completion; **before any ballot may be encrypted** |
| `IN-12` | **Quorum shortfall**                 | **Yes** | **Yes** | Election Board, all guardians | `quorum.shortfall`           | Election Officer (`R-02`)      | **When the available margin reaches 1** — not when it reaches 0 |
| `IN-13` | **Guardian unavailable**             | **Yes** | Yes    | Election Board | `guardian.unavailable`                      | Ceremony Coordinator           | Within 24 h of it becoming known           |
| `IN-14` | **Guardian compromise suspected**    | **Yes — see §3** | **Yes** | Election Board, DPO, the guardian | `guardian.compromise_suspected` | Incident Commander (`R-14`) | Auditor and Board **within 1 h**; public within 24 h |
| `IN-15` | **Guardian compromise confirmed**    | **Yes** | **Yes** | Everyone, incl. participants | `guardian.compromise_confirmed` | Election Board             | **Within 24 h**, and before any further ceremony step |
| `IN-16` | **Decryption ceremony started**      | **Yes — in advance** | Yes | Guardians | `decryption.ceremony_started`         | Ceremony Coordinator           | Announced ≥ 7 days before; **never before `voting_closed`** (`CM-20`) |
| `IN-17` | **Decryption share submitted**       | **Yes** | Yes    | No          | `decryption.share_submitted`                   | The guardian                   | At the checkpoint; **the share's proof is published, the share is a public value** |
| `IN-18` | **Compensation invoked**             | **n/a — the operation does not exist** | n/a | n/a | `compensation.not_applicable` | — | §4                    |
| `IN-19` | **Quorum lost**                      | **Yes** | **Yes** | Everyone, incl. participants | `quorum.lost`                | Election Board                 | Within 24 h of declaration, **with the recovery attempt record** (`CM-15`) |

---

## 2. Per-event detail — what may and may not be said

| ID      | Published fields                                                             | Explicitly NOT published                                    |
| ------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `IN-01` | Context, time, location form, guardian names, `k`, `n`, parameter-set ID      | Venue address where a guardian's safety is at issue (`IN-27`) |
| `IN-02` | Guardian name, organization, custody class, declared relationships            | Contact details, home address, device serial numbers          |
| `IN-03` | Who left, who replaced them, the ground, the phase reached                    | Health or personal detail beyond "personal reasons"           |
| `IN-04` | That authentication failed, the guardian index, the attempt count             | The credential, the factor, the failure's technical cause where it names a product |
| `IN-05` | Guardian index, the failing equation, the values needed to recheck it         | Nothing further is needed — the check is public               |
| `IN-06` | Sender index, receiver index, which check failed                              | The share, the decryption key, the plaintext of the share     |
| `IN-07` | Ground, complainant, respondent, phase, evidence reference                    | Free-text allegation on arithmetic grounds (`CD-04`)          |
| `IN-08` | Guardian index and name, ground, adjudicating body, whether a restart follows | Deliberation content beyond the published ground              |
| `IN-09` | Phase reached, abort condition, `FM-16B-*` ID, what happens to the material   | Any material that existed at abort                            |
| `IN-12` | Available count, `k`, the margin, the reason each absent guardian is absent   | Personal detail; the absence reason is at the `IN-13` level of generality |
| `IN-14` | That a suspicion exists, its class (`CM` severity), what is being suspended   | The evidence trail, where doing so aids the adversary — but the **existence and the class are always published** |
| `IN-15` | The finding, the affected context(s), the consequence chosen, the authority   | Forensic detail whose publication would harm an investigation, **named as withheld** |
| `IN-19` | Available count, `k`, the recovery attempts made, the annulment decision      | Nothing — this is the event with the least to protect and the most to explain |

| ID       | Rule                                                                                                                     |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `IN-23`  | **Where a field is withheld, the withholding is published** — the fact that something is withheld, the category, and the authority that decided. A silent omission is prohibited |
| `IN-24`  | **A guardian index is public; a guardian's personal circumstances are not.** The index is the operative identifier in every arithmetic notification |

---

## 3. Out-of-band notification

An incident that involves the system cannot be announced only by the system.

| ID       | Rule                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `IN-25`  | Every ceremony role registers an **out-of-band contact** before phase 5, and the register is tested before the ceremony, not during an incident |
| `IN-26`  | `IN-09`, `IN-14`, `IN-15` and `IN-19` are **always** delivered out of band, regardless of whether the system is functioning     |
| `IN-27`  | Out-of-band notification **carries no secret material and no evidence** — it says that something happened and where the record is. A telephone call is not an evidence channel |
| `IN-28`  | A guardian who is the subject of a suspicion is **notified**, unless a named legal authority has required otherwise — in which case the existence of that requirement is recorded and published when it lapses |
| `IN-29`  | Out-of-band notification is **logged as sent**, with time and recipient role, in the transcript. Whether it was received is recorded separately and may be "unknown" |

### 3.1 The one genuinely hard case

`IN-14` — suspected compromise — is where the pressure to stay quiet is
strongest, and the argument for quiet is not frivolous: publishing a
suspicion damages a named person who may be innocent, and may warn an
adversary.

**EPD²'s position:** the *existence* and *class* of a suspicion are always
published within 24 hours; the *evidence* may be withheld under `IN-23`;
and the affected person is notified under `IN-28`.

```text
The reason is that the alternative has one failure mode and it is fatal:
an unpublished suspicion is indistinguishable from a concealed one,
and a process that conceals cannot ask to be trusted afterwards.
```

The cost — reputational damage to a person later cleared — is real, is
borne by a volunteer, and is mitigated only by the requirement that a
withdrawal be published as prominently as the suspicion (`IN-30`).

| ID       | Rule                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------- |
| `IN-30`  | **A suspicion that is withdrawn is published as withdrawn**, in the same places, with the same prominence, naming the person cleared |
| `IN-31`  | Suspicion notifications state their class and **do not characterise the person** — `guardian.compromise_suspected` with a `CM` class, never an accusation of conduct |

---

## 4. `IN-18` — compensation invoked

**This event cannot occur.** Compensated decryption does not exist in the
selected specification version and is prohibited by `BR-13`
(`PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` §5).

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `IN-32`  | The event identifier is **retained and defined as unreachable**, so that the round task's list is answered and so that a future reintroduction cannot slip in as an unlisted event |
| `IN-33`  | An attempt to emit `compensation.*` in any form is a **defect and an incident** — `FM-16B-21`, and it is reported as a design-boundary violation, not as an operational event |

Absence beyond `n − k` is announced as `IN-19`, not as a compensation
failure.

---

## 5. Timing precision — the trap

Precise timestamps on ceremony events are safe. Precise timestamps on
**voter-facing** events are not, and PACK-15 fixed that boundary
(`IssuanceTimingProfile`, granularity 300 s, cohort `k = 5`).

| Event class                                | Timestamp precision       | Why                                                                     |
| ------------------------------------------ | ------------------------- | ------------------------------------------------------------------------- |
| Ceremony events (`IN-01`…`IN-11`, `IN-16`…`IN-19`) | **Exact, to the second** | The actors are public role-holders; precision is the point               |
| Guardian availability (`IN-12`, `IN-13`)    | Exact                     | Same                                                                     |
| Compromise events (`IN-14`, `IN-15`)        | Exact for the notification; **the detection time may be coarsened** where precision would identify a monitoring capability | Stated as coarsened when it is |
| **Anything referencing a participant**      | **Coarsened per PACK-15** | An exact time is a correlation handle, and the ceremony has no reason to want one |

| ID       | Rule                                                                                                                    |
| -------- | --------------------------------------------------------------------------------------------------------------------------- |
| `IN-34`  | **No ceremony notification references a participant, a credential, a ballot or a cast time.** The ceremony domain and the ballot domain do not meet here either |
| `IN-35`  | Ceremony timestamps are **UTC, ISO-8601, second precision**, and are part of the transcript's hashed content (`CT-08`)   |
| `IN-36`  | Where a time is coarsened, the **coarsening is stated with its granularity** — a coarse timestamp that looks exact is worse than either |

---

## 6. Immutable evidence

| ID       | Rule                                                                                                                    |
| -------- | --------------------------------------------------------------------------------------------------------------------------- |
| `IN-37`  | Every notification references a **transcript entry that already exists** when the notification is sent                    |
| `IN-38`  | Notifications are **append-only**. A correction is a new notification referencing the corrected one; nothing is edited or deleted (Canon 19a.1 lineage) |
| `IN-39`  | The **evidence bundle for an incident** is fixed at the time of the incident and hashed; later analysis is a separate object |
| `IN-40`  | Incident evidence is retained under the transcript's retention rule, and its **destruction date is published in advance** |
| `IN-41`  | No incident record may contain material that `CT-13`…`CT-17` prohibit in the transcript. **The incident channel is not a bypass for the transcript's prohibitions** |

---

## 7. Escalation — who may declare what

| Declaration                          | May be made by                                  | May **not** be made by                                   | Confirmed by                        |
| ------------------------------------ | ------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------- |
| Ceremony pause                       | Ceremony Coordinator, any guardian                | —                                                          | Recorded, no confirmation needed     |
| Ceremony abort                       | Ceremony Coordinator, Election Board              | A single administrator                                     | Election Board ratifies within 24 h  |
| Suspected compromise                 | Any guardian, Incident Commander, Auditor, Security Administrator | —                                          | Election Board classifies (`CM` §3)  |
| Confirmed compromise                 | **Election Board only**                           | Incident Commander (`RS-16B-11`), Security Administrator   | Auditor concurrence recorded         |
| Quorum lost                          | **Election Board only**                           | Election Officer, Coordinator                              | Auditor concurrence; `CM-15` record  |
| Context annulment                    | **Election Board**, with `R-15` where activated   | Anyone else                                                | Published with reasons               |
| Decryption authorisation             | **The guardians themselves, after `voting_closed`** | **Everyone else, without exception**                     | `CM-20`, `CM-23`                     |

**The last row is the one this whole document exists to protect.** Every
other escalation path terminates in a decision about process; that one
terminates in plaintext, and so it has no administrative path at all.

---

## 8. What this document does not decide

```text
Notification transport and channel implementation  → PACK-16D
The German-language notification texts             → PACK-15 content catalogue lineage
Retention periods                                   → OD-P16A-07
Media handling and press policy                     → GOVERNANCE
Regulatory reporting duties (BSI/Datenschutz)       → LEGAL, OD-P16A-12
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
