# PACK-15 — Revocation Decision Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Revocation is where a privacy architecture is most often quietly undone,
because every revocation request arrives with a good reason attached.

**Corrected by this revision:** §0 states the normative rule explicitly, in
the five sentences an implementation must be able to point at.

---

## 0. The normative rule — explicit

1. **Before issuance, eligibility may be invalidated.** A source change, a
   restriction, a scope change or a corrected fact supersedes the decision
   and prevents assertion minting. A minted assertion may be revoked
   **before pickup** and before use, where the context's declared policy
   permits it.
2. **After issuance and before redemption, the credential may be
   revoked** — on governed conditions, before `RevocationCutoff`, with dual
   control and Independent Auditor notification inside the final window.
3. **After redemption, no person-level revocation and no ballot lookup is
   possible.** Not by an operator, not by an administrator, not under
   break-glass, not under legal compulsion executed through this system.
4. **No identity-side operation may locate, delete, replace or invalidate a
   specific ballot.** No such operation exists, none may be added, and the
   identity side holds nothing that could address one. This is a structural
   property, not an access-control rule.
5. **Any later election-wide invalidation belongs to PACK-16 governance** —
   annulment, re-run, suspension of a result — **and must not create
   identity linkage.** An invalidation that required knowing whose ballots
   were affected would _be_ the link and is refused; an election-wide
   invalidation acts on the context, never on participants.

---

## 1. The regimes

| Regime                                | What can be withdrawn         | Who may                                      | Effect on a ballot    |
| ------------------------------------- | ----------------------------- | -------------------------------------------- | --------------------- |
| Before assertion minting              | The eligibility decision      | Eligibility Service, on a source change      | none — nothing exists |
| After minting, before pickup          | The assertion                 | Assertion Issuer, per the context's policy   | none                  |
| After pickup, before credential issue | The assertion, only by expiry | Clock                                        | none                  |
| After issuance, before redemption     | The credential                | Credential Issuer, before `RevocationCutoff` | none                  |
| **After redemption**                  | **Nothing**                   | **Nobody**                                   | **none, ever**        |

Because the correction makes issuance and redemption a **single WS-03
visit** (`OD-P15-07`), the practical window of regime four is usually
seconds. That is stated plainly rather than hidden: the regime that does
most of the work in practice is the **assertion** regime, before pickup,
which is also the regime in which nothing is lost.

---

## 2. Before minting — decision supersession

| Trigger                           | Effect                                 | Reason code                            | Participant told        |
| --------------------------------- | -------------------------------------- | -------------------------------------- | ----------------------- |
| Membership becomes inactive       | Decision `superseded`; no assertion    | `ELIGIBILITY_MEMBERSHIP_INACTIVE`      | yes, with the next step |
| Restriction or suspension applied | Decision `superseded`                  | `ELIGIBILITY_RULE_NOT_SATISFIED`       | yes                     |
| Organizational scope changes      | Decision `superseded`                  | `ELIGIBILITY_SCOPE_MISMATCH`           | yes                     |
| Source data corrected             | Re-evaluation; outcome may flip        | `ELIGIBILITY_SOURCE_STALE`             | yes                     |
| Rule-set fault discovered         | Context-level decision, not per person | `VOTING_CONTEXT_CONFIGURATION_INVALID` | context announcement    |
| Assurance falls below requirement | Decision `superseded`                  | `ELIGIBILITY_ASSURANCE_INSUFFICIENT`   | yes                     |

Nothing is lost in this regime, which is why fault detection **before**
assertion minting is a design goal rather than an operational preference.

---

## 3. After minting, before pickup

| Trigger                         | Permitted?                       | Control                                   | Reason code         |
| ------------------------------- | -------------------------------- | ----------------------------------------- | ------------------- |
| Context suspended or cancelled  | yes                              | Voting Operations Officer + reason code   | `ASSERTION_REVOKED` |
| Issuance fault detected         | yes                              | Assertion Issuer                          | `ASSERTION_REVOKED` |
| Eligibility source change       | **policy-dependent per context** | Declared in the context's privacy profile | `ASSERTION_REVOKED` |
| Participant request             | yes, before pickup               | Participant-initiated                     | `ASSERTION_REVOKED` |
| Administrative decision         | yes, with dual control           | PACK-12 grant + reason code               | `ASSERTION_REVOKED` |
| Still queued (not yet released) | yes — the cheapest moment        | Assertion Issuer                          | `ASSERTION_REVOKED` |

**Whether a source change may revoke an already-minted assertion is a
per-context policy declared in advance**, not a global rule: revoking on
source change keeps the electorate exact and hands an administrator a
lever; not revoking accepts a small staleness window and removes the lever.
The context declares its choice publicly before it opens.

---

## 4. After issuance, before redemption

| Governed condition                               | Dual control | Auditor notified | Reason code                           |
| ------------------------------------------------ | ------------ | ---------------- | ------------------------------------- |
| Context suspended or cancelled                   | no           | yes              | `CREDENTIAL_REVOKED`                  |
| Detected issuance fault                          | no           | yes              | `CREDENTIAL_REVOKED`                  |
| Confirmed duplicate issuance                     | no           | yes              | `CREDENTIAL_DUPLICATE_REQUEST`        |
| Security event affecting this context            | yes          | yes              | `CREDENTIAL_REVOKED`                  |
| Holder-initiated report through the client       | no           | no               | `CREDENTIAL_REVOKED`                  |
| Governed reissue (revoke-then-reissue)           | yes          | yes              | `CREDENTIAL_REVOKED`                  |
| Administrative decision, inside the final window | **yes**      | **yes**          | `CREDENTIAL_REVOKED`                  |
| After the cutoff                                 | **refused**  | —                | `CREDENTIAL_REVOCATION_CUTOFF_PASSED` |

Not permitted under any condition: revocation on the basis of _how someone
is expected to vote_; revocation of a set selected by any attribute other
than the fault that justifies it; revocation without a registered reason
code; revocation that requires resolving a credential to a person.

**Revocation is never targeted by participant.** The Credential Issuer
cannot select a participant's credential, because it does not know which
one it is. It can revoke _a credential_ whose reference is presented, or _a
set defined by the fault_ — an issuance batch, a context, a window. That
limitation is a feature: **selective disenfranchisement is not expressible
in this system's revocation interface.**

---

## 5. The cutoff and its trade-off

| Option                               | Protects against       | Creates the risk of                                |
| ------------------------------------ | ---------------------- | -------------------------------------------------- |
| Late cutoff (into the voting window) | Faults discovered late | Selective disenfranchisement; compelled revocation |
| Early cutoff (at issuance close)     | Both of those          | An uncorrectable fault found after it              |

**Decision.** `RevocationCutoff` is per-context governed configuration with
a mandatory maximum:

| Context type              | Maximum cutoff                          |
| ------------------------- | --------------------------------------- |
| `organizational_election` | Opening of the voting window            |
| `candidate_nomination`    | Opening of the voting window            |
| `internal_party_vote`     | Close of the credential issuance window |
| `programme_vote`          | Close of the credential issuance window |
| `assembly_decision`       | Close of the session's issuance window  |
| `advisory_consultation`   | Close of the credential issuance window |
| `public_election_profile` | **Defined by law. Not activated.**      |

A configuration outside the maximum is refused with
`VOTING_CONTEXT_CONFIGURATION_INVALID`, never clamped silently.

Any revocation inside the final window before the cutoff requires **dual
control plus Independent Auditor notification**, is recorded in `AS-04` as
an exceptional act, and is counted per context in the evidence bundle
(§20.2 of the specification). A context with many late revocations is a
context whose result deserves scrutiny, and the evidence for that scrutiny
must exist.

---

## 6. After redemption — what revocation must never do

| Prohibited                              | Why                                                          |
| --------------------------------------- | ------------------------------------------------------------ |
| Find the ballot                         | Requires the credential→ballot link the architecture forbids |
| Delete the ballot                       | Same, plus it would make the tally unverifiable              |
| Replace the ballot                      | Same, plus it is indistinguishable from tampering            |
| Link the ballot to a person             | The central guarantee                                        |
| Mark a person as "not counted"          | A person-level participation statement                       |
| Produce a list of affected participants | The list is the link                                         |
| Move a credential out of `redeemed`     | The absorbing state is absorbing for privileged actors too   |

**The remedy after redemption is at the level of the context** —
suspension, annulment, re-run — each a governed **PACK-16** decision under
its own authority, with its own evidence and its own announcement, and
**none of which may create identity linkage.** Slower, more visible and
more accountable than a quiet per-ballot correction, which is the point.

---

## 7. Evidence produced by every revocation

| Field                        | Required    | Note                                              |
| ---------------------------- | ----------- | ------------------------------------------------- |
| Artifact class revoked       | yes         | decision / assertion / credential                 |
| Context reference            | yes         | —                                                 |
| Reason code                  | yes         | Registered; never free text                       |
| Authority                    | yes         | The role and the grant reference where applicable |
| Dual-control second approver | conditional | Where §3 or §4 requires it                        |
| Timing class                 | yes         | Relative to the cutoff; never a precise timestamp |
| Auditor notification         | conditional | Where required                                    |
| Participant notification     | conditional | Where the participant can be told without a link  |
| **Participant identity**     | **never**   | Not in the credential stream, in any form         |

---

## 8. What an operator cannot do, restated

An operator with full administrative rights over the Credential Issuer can
revoke credentials, suspend a context and stop issuance. They **cannot**
determine who holds a credential, revoke the credential of a named person,
learn whether a named person redeemed one, or reach a ballot.

An operator with full administrative rights over the voting-trust service
can deny eligibility, approve exceptions, revoke assertions before pickup
and see who applied. They **cannot** reach a credential, a redemption or a
ballot.

Neither operator can do the other's job, and the combination of both roles
in one person is prohibited by `SD-06` and by `FIR-INV-006` — no feature
flag, grant or emergency may assemble it.
