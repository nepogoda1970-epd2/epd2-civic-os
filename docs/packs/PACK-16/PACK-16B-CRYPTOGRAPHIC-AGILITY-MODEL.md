# PACK-16B — Cryptographic Agility Model

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The problem agility usually creates

Agility and downgrade are the same mechanism seen from two sides. A system
that can use a newer algorithm can usually be persuaded to use an older
one, and the persuasion happens at the layer where the choice is made. The
only reliable defence is to move the choice somewhere an attacker cannot
reach.

**In this architecture the choice lives in the election manifest, is
approved before `issuance_open`, is published, and is immutable
thereafter.** There is no other place where it can be made.

---

## 2. Six kinds of agility, separated

Conflating these is how downgrade paths get built.

| Kind                              | Question it answers                                        | Mechanism                                                   |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------- |
| **New-context agility**           | What may a *new* election use?                             | Parameter-set `status` = `active` at configuration time      |
| **Historical-verification compatibility** | Can a 2030 record still be verified in 2045?         | `PS-10` — verification capability is never withdrawn         |
| **Emergency prohibition**         | How is a broken set stopped?                                | `PS-08`, `PS-14`; parameter-set specification §5              |
| **Algorithm migration**           | How does the construction itself change?                    | A new profile, a new ADR — §5                                 |
| **Parameter migration**           | How do values change within one construction?               | **Not applicable** — the values are fixed upstream `[F-04]`   |
| **Protocol migration**            | How does the protocol family change?                        | Re-opens `ADR-099`; outside every later PACK-16 stage         |

**Parameter migration does not exist in `EPD2-CRYPTO-1`**, because the
upstream specification fixes the values and a conforming verifier requires
bit-equality `[F-05]`. That is a limitation of the profile and
simultaneously its strongest anti-downgrade property.

---

## 3. Prohibited constructions — normative

```text
NO runtime negotiation between client and server.
NO "choose the strongest mutually supported" logic, anywhere.
NO fallback to an older parameter set on any error, timeout or absence.
NO automatic compatibility mode.
NO silent verifier downgrade.
NO parameter selection from a request header, query parameter, cookie,
   user agent, feature flag, environment variable or deployment profile.
NO per-tenant, per-scope or per-device parameter variation.
NO "try the new one, fall back to the old one" retry.
```

| ID       | Rule                                                                                                                     |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `CA-01`  | The parameter set is a **manifest field**, decided before `issuance_open` and immutable thereafter (`PS-03`, `PS-11`)     |
| `CA-02`  | Every participant — client, service, board, verifier — reads the set **from the manifest**, and refuses if it cannot     |
| `CA-03`  | A mismatch between an expected and a presented parameter set is a **refusal**, never a renegotiation                     |
| `CA-04`  | An unrecognised parameter set is a **refusal**, never a default (`PS-07`)                                                |
| `CA-05`  | A verifier that does not support the record's declared set **reports that it cannot verify**; it never verifies partially or approximately |
| `CA-06`  | There is **no protocol message** in which a parameter set is proposed, offered, requested or agreed                       |
| `CA-07`  | No flag may relax `CA-01`…`CA-06` (`FIR-INV-006`)                                                                        |

`CA-05` matters more than it looks. A verifier that silently skips checks
it does not understand is worse than one that refuses, because it converts
absent verification into apparent verification — the failure mode of
`F-INF-3`.

---

## 4. The dated migration this profile already has

`EPD2-CRYPTO-1` is a purely classical discrete-log profile, and current
German guidance recommends classical key agreement **only until the end of
2031**, with **the end of 2030** for very high protection requirements
`[F-25]`.

```text
2030-12-31   deprecation_date for high-assurance contexts
2031-12-31   deprecation_date for all other contexts
2032-12-31   prohibition_date
```

| ID       | Obligation                                                                                                                            |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `CA-08`  | A successor profile must exist and be `active` **before** the deprecation date, or **no new context may be opened after it**            |
| `CA-09`  | The successor is expected to be **hybrid** — quantum-safe combined with classical — because the guidance states quantum-safe mechanisms are *"generally not yet trusted to the same extent as the established classical mechanisms"* `[F-25]` |
| `CA-10`  | Successor work is **`OD-P16B-06`**, owned by a future round, and is **not started here**                                               |
| `CA-11`  | The deprecation date is a **registry field**, surfaced in configuration validation, not a note in a document                            |
| `CA-12`  | Approaching deprecation produces a governed notification at 24, 12 and 3 months (`PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` §6)     |

**The successor is not a parameter change.** A hybrid construction is a
different protocol: different ciphertexts, different proofs, different
verifier, different security argument. Under
`PACK-16B-PARAMETER-SET-SPECIFICATION.md` §2 it is an algorithm migration
requiring its own ADR — and, because it changes the ballot construction, it
also touches `ADR-099` and cannot be decided inside PACK-16.

Recording the date now, as a field, is the whole point: **a cliff nobody
wrote down is a cliff somebody walks off.**

---

## 5. Algorithm migration — how a successor arrives

```text
1. A successor profile is specified in its own round, with its own ADR.
2. It is registered as a new parameter_set_id in status `draft`.
3. Cryptographic review (VO-05 equivalent) → `under_review` → `approved`.
4. Governance gate → `active`.
5. New contexts may declare it. Existing contexts do not change.
6. The predecessor moves to `deprecated` on its date, then to
   `retired_for_new_contexts`, then to `verification_only`.
7. Verification capability for the predecessor is retained indefinitely.
```

| ID       | Rule                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------- |
| `CA-13`  | Two parameter sets may be `active` simultaneously; a **context** still binds exactly one (`PS-02`)             |
| `CA-14`  | A running context **never migrates**. There is no in-place upgrade of an open election                        |
| `CA-15`  | A configured-but-unopened context may be **discarded and reconstituted** under the successor — never re-keyed  |
| `CA-16`  | Migration never re-opens, re-signs, re-encrypts or re-tallies an archived record                              |
| `CA-17`  | The successor's arrival does not invalidate a completed election, and no completed result is re-characterised as unverified because a newer profile exists |

`CA-17` exists because it is the natural thing to get wrong. A result
produced correctly under the guidance of its time remains correctly
produced; what changes is what may be *started* afterwards.

---

## 6. Historical verification

| ID       | Requirement                                                                                                     |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CA-18`  | Every archived record carries its `parameter_set_id`, its `specification_version` and its `specification_digest` |
| `CA-19`  | The parameter values and their derivation rule are archived **with** the record, not by reference alone           |
| `CA-20`  | An archived record verifies with **an unmodified conforming verifier** and no live EPD² service (`BB-20`)         |
| `CA-21`  | Retiring a parameter set never removes the ability to verify records made under it                                |
| `CA-22`  | Where a set is `prohibited` for a security reason, archived verification continues **with a published notice** stating what was found and when |

`CA-22` is the honest handling of the uncomfortable case: an election
verified under a construction later found weak. The record still verifies
in its own terms; what the notice adds is the reader's ability to know
that, which is strictly more information than withdrawing the verifier
would give them.

---

## 7. Who may do what

| Act                                           | Decider                    | Concurrence         | Published |
| --------------------------------------------- | -------------------------- | ------------------- | --------- |
| Propose a parameter set (`draft`)             | Cryptographic Reviewer     | —                   | yes       |
| Move to `under_review`                        | Election Board             | —                   | yes       |
| Move to `approved`                            | Election Board             | **Independent Auditor** + Cryptographic Reviewer sign-off | yes |
| Move to `active`                              | **Legal Activation Authority** + Election Board, through the governance gate | Independent Auditor | yes |
| Bind a set to a context                       | Election Board, in the manifest | —              | yes       |
| Publish the set with the manifest             | Bulletin-Board Operator    | —                   | yes       |
| Verify the set is as published                | **anyone**                 | —                   | n/a       |
| Move to `deprecated`                          | automatic on date, or Election Board earlier | —   | yes       |
| Move to `prohibited`                          | Election Board             | **Independent Auditor** | yes   |
| Emergency advisory intake                     | Cryptographic Reviewer     | —                   | yes       |

**Who cannot:**

```text
System Administrator cannot activate, bind, change or prohibit a set.
Security Administrator cannot either.
Election Officer cannot bind a set not already `active`.
Voting-System Operator has no role at all.
Bulletin-Board Operator publishes; it does not choose.
Incident Commander may pause a context; may not change its parameters.
No automated process may change a status.
```

---

## 8. Security-advisory intake

The upstream specification has **no errata document, no specification-level
security-reporting path, and marks two versions simultaneously
"Recommended"** `[F-30]`. EPD² therefore cannot rely on being told.

| ID       | Requirement                                                                                                        |
| -------- | -------------------------------------------------------------------------------------------------------------------- |
| `CA-23`  | The Cryptographic Reviewer role holds a standing obligation to monitor the upstream repository, release notes and the cryptographic literature for defects affecting the pinned specification |
| `CA-24`  | An advisory is assessed within a governed period and produces one of: no action · clarification in the EPD² profile · deprecation · **prohibition** |
| `CA-25`  | The assessment and its outcome are **published**, including "no action" and its reasoning                          |
| `CA-26`  | An advisory arriving **during a running election** follows `PACK-16B-PARAMETER-SET-SPECIFICATION.md` §5, whose options are bounded and do not include re-keying |
| `CA-27`  | EPD² maintains its **own errata record** for the pinned specification, including the two internal inconsistencies already identified (`PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` §7) |

`CA-27` is not optional politeness. Two inconsistencies were found in the
specification's hash section by a single reading pass `[F-19]`; a project
that depends on that document and keeps no errata record of its own is
depending on a document it has not accounted for.

---

## 9. What agility this profile does **not** have, stated plainly

```text
It cannot change its group.            It cannot change its modulus.
It cannot change its subgroup order.   It cannot change its generator.
It cannot change its hash function.    It cannot change its encoding.
```

That is not flexibility deferred; it is flexibility **absent**, by upstream
design. The consequence is that when the 2031 cliff arrives, the answer
cannot be a configuration change — it must be a successor profile, and the
work to produce one must start early enough to be reviewed rather than
rushed. `CA-08` and `CA-12` exist to make that impossible to forget.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
