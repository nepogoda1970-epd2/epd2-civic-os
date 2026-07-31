# PACK-15 — Event Catalog

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Every event uses **PACK-13's canonical envelope unchanged** (canon §21):
`event_id`, `event_type`, `event_version`, `occurred_at`, `producer`,
`actor`, `subject`, `correlation_id`, `causation_id`, `payload`,
`integrity`. No transport metadata is added; ADR-071's boundary stands.

**No event below is implemented, and no schema file is produced by this
round.**

---

## 0. Payload rules that apply to every family

1. **No ballot content, ever, in any field, in any family.**
2. **No ordinary identity, ever** — no account, person record, membership,
   member number, persona, email, phone, name, address or date of birth.
3. **No payload contains both an assertion reference and a credential
   reference.** This is the pairing prohibition applied to the event
   stream, and it binds `correlation_id` and `causation_id` as strictly as
   it binds `payload`.
4. **`correlation_id` does not cross the trust boundary.** An
   identity-side correlation chain ends at assertion issuance; the
   voting side begins a new one. A chain that spans both is the link.
5. Every failure-shaped event carries a **registered reason code**.
6. Payloads are minimal: an event says what happened, not everything known.
7. Timestamps are coarsened where the context's privacy profile requires
   it, and a timing class is used in place of a precise value in the
   voting-side families.
8. Each family is published to **one** audit stream, never to two.

---

## 1. Voting context family — stream `AS-06`, producer VC-01

| Event                       | Subject         | Notable payload                                                        |
| --------------------------- | --------------- | ---------------------------------------------------------------------- |
| `VotingContextCreated`      | voting context  | Type, organizational scope, rule-set version reference, audit profile, privacy profile |
| `VotingContextActivated`    | voting context  | Activating authority, dual-control references, windows                 |
| `VotingContextSuspended`    | voting context  | Reason code, authority, effect on issuance and redemption              |
| `VotingContextClosed`       | voting context  | Closing authority, final window boundaries                             |
| `VotingWindowOpened`        | voting context  | Window boundaries                                                      |
| `VotingWindowClosed`        | voting context  | Window boundaries; **no counts, no totals, no turnout**                |

`VotingWindowClosed` is the event most likely to acquire a turnout field
during implementation "because it is convenient". It must not.

---

## 2. Eligibility family — stream `AS-01`, producer VC-02

| Event                          | Subject           | Notable payload                                                          |
| ------------------------------ | ----------------- | ------------------------------------------------------------------------ |
| `EligibilityRequested`         | eligibility case  | Context reference, request channel, assisted-by reference where applicable |
| `EligibilityEvaluationStarted` | eligibility case  | Rule-set version                                                         |
| `EligibilityApproved`          | eligibility case  | Rule-set version, reason codes, validity window, participation class     |
| `EligibilityDenied`            | eligibility case  | Rule-set version, reason codes, appeal path reference                    |
| `EligibilityReviewRequired`    | eligibility case  | Trigger reason code, review queue reference                              |
| `EligibilityEvidenceReferenced`| eligibility case  | PACK-11 reference only — **never content**                               |
| `EligibilityDecisionExpired`   | eligibility case  | Reason code                                                              |
| `EligibilityDisputed`          | eligibility case  | Dispute reference, ground reason code                                    |
| `EligibilityDisputeResolved`   | eligibility case  | Outcome, reason code, reviewer role, remedy class                        |

The subject of every event in this family is the **eligibility case**,
which is identity-side. That is correct and is the last family in which it
is true.

---

## 3. Assertion family — stream `AS-02`, producer VC-03

| Event                              | Subject   | Notable payload                                                     |
| ---------------------------------- | --------- | ------------------------------------------------------------------- |
| `EligibilityAssertionIssued`       | assertion | Context reference, class, expiry, audience, integrity metadata      |
| `EligibilityAssertionRevoked`      | assertion | Reason code, authority                                              |
| `EligibilityAssertionExpired`      | assertion | —                                                                   |
| `EligibilityAssertionRedeemed`     | assertion | Context reference, timing class — **no credential reference**       |
| `EligibilityAssertionReplayRejected` | assertion | Reason code, timing class                                          |

`EligibilityAssertionRedeemed` is produced by the voting side about an
identity-side artifact, and is therefore the single most dangerous event in
the catalogue. It carries the assertion reference and **must never** carry
the credential that was minted, must never share a `correlation_id` with
`VotingCredentialIssued`, and must never be published to `AS-03`.

---

## 4. Credential family — stream `AS-03`, producer VC-04

| Event                                | Subject    | Notable payload                                                   |
| ------------------------------------ | ---------- | ----------------------------------------------------------------- |
| `VotingCredentialRequested`          | credential | Context reference, timing class                                   |
| `VotingCredentialIssued`             | credential | Context reference, credential type, expiry — **no assertion reference** |
| `VotingCredentialRevoked`            | credential | Reason code, authority, dual-control reference where required, position relative to the cutoff |
| `VotingCredentialExpired`            | credential | —                                                                 |
| `VotingCredentialRedeemed`           | credential | Context reference, timing class, redemption reference             |
| `VotingCredentialReplayRejected`     | credential | Reason code, timing class                                         |
| `DuplicateCredentialIssuanceRejected`| credential request | Reason code                                                |

---

## 5. Handoff family — stream `AS-06`, producer VC-05

| Event                          | Subject | Notable payload                                     |
| ------------------------------ | ------- | --------------------------------------------------- |
| `VotingHandoffAccepted`        | handoff | Context reference, audience, origin validation result |
| `VotingHandoffRejected`        | handoff | Reason code                                         |
| `VotingHandoffExpired`         | handoff | —                                                   |
| `VotingHandoffReplayRejected`  | handoff | Reason code                                         |

These extend PACK-14's outbound artifact into PACK-15's inbound handling
and carry no account reference, consistent with ADR-088.

---

## 6. Audit and integrity family — stream `AS-04`, producer VC-06

| Event                                     | Subject          | Notable payload                                                    |
| ----------------------------------------- | ---------------- | ------------------------------------------------------------------ |
| `VotingBoundaryIntegrityViolationDetected`| detection        | Violation class, boundary, detector, severity — **no identity**    |
| `CorrelationRiskDetected`                 | detection        | Risk class (shared key, shared trace, cross-stream read, cohort size), severity |
| `IntermediateTallyAttemptRejected`        | request          | Surface class, reason code                                         |
| `PrivilegedVotingActionPerformed`         | privileged act   | Act class, role, grant reference, dual-control reference, context  |

`CorrelationRiskDetected` exists so that a near-miss is recorded rather
than fixed quietly: the cases it fires on — a shared identifier appearing
in two streams, a principal acquiring read access to both sides, an
issuance cohort of size one — are exactly the conditions that precede a
real breach.

---

## 7. Events deliberately absent

| Event that will be proposed          | Why it is refused                                                  |
| ------------------------------------ | ------------------------------------------------------------------ |
| `ParticipationCompleted`             | Joins an identity-side subject to a voting-side act                |
| `MemberVoted`                        | A person-level participation statement                             |
| `CredentialIssuedForMember`          | The pairing, as an event name                                      |
| `TurnoutUpdated`                     | An intermediate tally                                              |
| `VotingJourneyStepCompleted`         | A journey is a chain                                               |
| A generic `VotingError`              | Prohibited by the reason-code discipline                           |

---

## 8. Versioning

PACK-13's ADR-074 governs contract evolution and applies unchanged: a
payload field is added compatibly, a meaning is never changed in place, and
a breaking change is a new `event_version`. Two additional constraints from
this round:

1. **A field may never be added to an event if it would create the
   assertion/credential pair**, regardless of compatibility.
2. **A field may never be added that narrows a cohort** — a scope label, a
   fine-grained timestamp or a device class added to a voting-side event
   can turn an anonymous count into an identifying one, and compatibility
   rules do not catch that.

---

## 9. Families added by the architecture correction (2026-07-31)

### 9.1 Assertion queue and pickup — stream `AS-02`, producer VC-03 / VC-05

| Event                              | Subject   | Notable payload                                                                 |
| ---------------------------------- | --------- | ------------------------------------------------------------------------------- |
| `EligibilityAssertionMinted`       | assertion | Context reference, class, expiry (coarsened), audience, integrity metadata      |
| `EligibilityAssertionQueued`       | assertion | Context reference, batch reference, scheduled-release **window class**          |
| `EligibilityAssertionReleased`     | assertion | Context reference, batch reference, batch size **class**                        |
| `AssertionPickupCreated`           | pickup    | Context reference, expiry (coarsened) — **no account, no artifact value**       |
| `AssertionPickupRedeemed`          | pickup    | Context reference, timing class — **no credential reference**                   |
| `AssertionPickupExpired`           | pickup    | Reason code                                                                     |
| `AssertionPickupReplayRejected`    | pickup    | Reason code, timing class                                                       |

`EligibilityAssertionIssued` from §3 is retained as the family's compatible
predecessor name for the minting event; implementations emit
`EligibilityAssertionMinted` and MUST NOT emit both for one assertion.

### 9.2 Issuance timing and cohort — stream `AS-04`, producer VC-03

| Event                              | Subject   | Notable payload                                                                 |
| ---------------------------------- | --------- | ------------------------------------------------------------------------------- |
| `IssuanceCohortThresholdNotMet`    | batch     | Context reference, cohort-size **class**, `cohort_wait_max` reached — **never the exact size, never a participant** |
| `IssuanceTimingProfileApplied`     | context   | The profile values in force at activation                                       |
| `IssuanceWindowGuaranteeViolated`  | context   | Reason code; raised when the queue cannot guarantee release before the window closes |

### 9.3 Credential delivery — stream `AS-03`, producer VC-04

| Event                              | Subject    | Notable payload                                                                |
| ---------------------------------- | ---------- | ------------------------------------------------------------------------------ |
| `CredentialMintingDelayed`          | credential request | Delay class only — a progress fact, not a failure                      |
| `CredentialDeliveryChannelRefused`  | request    | Reason code, channel class — raised when any non-WS-03 delivery is attempted   |

### 9.4 Evidence bundle — stream `AS-05`, producer VC-06

| Event                       | Subject | Notable payload                                                                       |
| --------------------------- | ------- | ------------------------------------------------------------------------------------- |
| `EvidenceBundleGenerated`   | bundle  | Bundle schema version, context reference, sections included, suppression summary      |
| `EvidenceBundleExported`    | bundle  | Export authorization reference, requesting role, pre- or post-closure scope           |
| `EvidenceBundleRejected`    | bundle  | Which validation check failed, by reason code                                          |

### 9.5 Payload rules that apply to all of the above

The seven rules of §0 apply unchanged, plus three the correction adds:

8. **No exact cohort size, batch size or queue depth** in any payload —
   classes only. An exact size in a small electorate is a participation
   statement.
9. **No precise timestamps** in `AS-02`, `AS-03` or `AS-05` payloads —
   coarsened values and timing classes only.
10. **No credential or assertion material** in any payload, including in a
    diagnostic or error field.

### 9.6 Events still deliberately absent

`AssertionMintedForMember`, `CredentialIssuedForAssertion`,
`ParticipationCompleted`, `MemberVoted`, `TurnoutUpdated`,
`VotingJourneyStepCompleted` and any generic `VotingError` remain refused,
for the reasons in §7.
