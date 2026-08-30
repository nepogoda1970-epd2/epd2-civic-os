# PACK-16D — Continuation State Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

`casting/continuation.py`, its two call sites in `casting/transactions.py`,
the capability-side half of `casting/store.py`, and the constants in
`publication/capacity.py`. This is the implementation of PACK-16C's
anonymous continuation capability (`CN-33`…`CN-38`, `DM-20`) and of the
identity-separation invariant `DM-10`.

## 2. The state is three booleans and an opaque reference

```text
ContinuationState                        (frozen, slotted)
  capability_reference : str             opaque, anonymous
  election_context_id  : str
  cast_entitlement_available             : bool = True
  public_challenge_entitlement_available : bool = True
  capability_consumed                    : bool = False
```

| ID      | Rule                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-01` | The state is **exactly three booleans plus an opaque anonymous reference and the election context**. There is no counter, no attempt tally, no last-seen time, no device, no session and no address                   |
| `CS-02` | There is **no counter on purpose.** A counter is a number that grows with a person's behaviour; two booleans and a consumed flag express the same entitlement arithmetic (`K = 1`, `A = 1`) while carrying no history |
| `CS-03` | The dataclass is **frozen**. Every transition returns a _new_ value via `dataclasses.replace`; nothing mutates in place, so a partially applied transition cannot exist                                               |
| `CS-04` | `capability_reference` is opaque. It is not derived from an identity, a credential or a ballot, and nothing in the record allows it to be joined to one                                                               |
| `CS-05` | The three flags are asserted at their documented defaults by `test_continuation_state_has_exactly_three_booleans`                                                                                                     |

## 3. The two transitions

| ID      | Transition                 | Preconditions                                                                                                                                                                                                                                     | Effect                                                                                                                    |
| ------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `CS-06` | `spend_public_challenge()` | `public_challenge_entitlement_available` must be `True`, else `PublicChallengeEntitlementExhaustedError` (`CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED`); `capability_consumed` must be `False`, else `PublicChallengeEntitlementExhaustedError` again | sets `public_challenge_entitlement_available = False` **and nothing else**                                                |
| `CS-07` | `consume_for_cast()`       | `cast_entitlement_available` must be `True` **and** `capability_consumed` must be `False`, else `CastEntitlementExhaustedError` (`CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED`)                                                                       | sets `cast_entitlement_available = False`, `public_challenge_entitlement_available = False`, `capability_consumed = True` |

There are **exactly two transitions and no third**. There is no reset, no
refund, no re-issue and no un-consume. A capability that has been consumed
has no path back to any other state.

| ID      | Rule                                                                                                                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-08` | **A public challenge does not consume the cast entitlement.** After `spend_public_challenge()`, `cast_entitlement_available` is still `True` and `capability_consumed` is still `False`                                                                                                                          |
| `CS-09` | `CS-08` is a protocol requirement, not an implementation convenience: challenging a ballot is how a voter tests whether the client encrypted what they chose. If challenging spent the vote, the check would cost the voter their ballot and nobody would run it. The verification mechanism must be free to use |
| `CS-10` | The reverse does **not** hold. `consume_for_cast()` clears the public-challenge entitlement as well, because the capability as a whole is spent once the ballot is accepted. After a cast, a challenge attempt fails on the entitlement check                                                                    |
| `CS-11` | Ordering is irrelevant to the arithmetic: challenge-then-cast and cast-alone both end with `capability_consumed = True`, and neither ordering permits two casts or two challenges                                                                                                                                |

Evidence: `test_p10_public_challenge_does_not_consume_cast_entitlement`
asserts each flag after `spend_public_challenge()`, then completes the cast
and asserts consumption, then asserts the cast-alone ordering.
`test_neg_duplicate_public_challenge`, `test_neg_duplicate_cast` and
`test_neg_capability_replay` assert the three exhaustion paths with their
expected reason codes; `test_neg_unknown_capability` asserts an unissued
capability raises `CapabilityUnknownError` (`CONTINUATION_INVALID`).
`test_c03_*` races a cast and a challenge on the same capability across
real OS threads, twelve repeats. It asserts the **order-dependent**
outcome: the cast is accepted either way and the final state has
`capability_consumed = True` and
`public_challenge_entitlement_available = False`; if the challenge won the
race it also published and the two submissions took different leaves,
while if the cast won, the challenge is refused with
`PublicChallengeEntitlementExhaustedError` and took no leaf at all.

## 4. `K = 1` and `A = 1`

| ID      | Rule                                                                                                                                                                                                                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-12` | `K_PUBLIC_CHALLENGES_PER_CONTINUATION = 1` and `A_ACCEPTED_CASTS_PER_CONTINUATION = 1`, defined once in `publication/capacity.py` and exposed as the `CapacityPlan.k` and `CapacityPlan.a` properties. They are **constants, not configuration**                                                                       |
| `CS-13` | `L_max = E × (K + A) = E × 2`, where `E = max_valid_continuations`. `CapacityPlan.l_max` computes exactly this                                                                                                                                                                                                         |
| `CS-14` | **`L_max` is derived from the maximum number of valid continuation capabilities, never from turnout**, never from an expected participation rate and never from an observed load. A capacity bound that moved with turnout would publish turnout                                                                       |
| `CS-15` | Because `K = 1` and `A = 1`, the three booleans are a complete encoding of the entitlement: one challenge, one cast, then nothing. If `K` or `A` were ever raised above `1`, the boolean encoding would no longer suffice and this design would have to be revisited — that is a deliberate coupling, not an oversight |

`test_l_max_is_derived_from_capabilities_not_turnout` asserts both
constants are `1`, that `plan.l_max == plan.max_valid_continuations * 2`,
and that total capacity covers `l_max` plus the safety reserve.
`test_reconciliation_reports_every_class` asserts the published
reconciliation record carries `(k, a) == (1, 1)` and the same
`max_valid_continuations` the plan declared, so a reader can check the plan
they were promised against the plan that was executed.

## 5. `FORBIDDEN_CAPABILITY_FIELDS` and the `DM-10` rule

`FORBIDDEN_CAPABILITY_FIELDS` is a frozenset of eleven names:

```text
identity                 identity_record_id       member_id
membership_id            credential_id            account_id
email                    name                     ballot_id
artifact_reference       public_challenge_artifact_id
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-16` | **`DM-10`: the two sides of the acceptance boundary share no key.** A capability record may not name a ballot; a ballot record may not name a capability. Neither side carries a value from which the other can be found                                                                                                                                                                                              |
| `CS-17` | The prohibition is expressed **in the type**, not in policy. `ContinuationState` has no field for any of the eleven names, so there is nothing to populate, nothing to forget to clear and nothing to leak in a serialisation                                                                                                                                                                                         |
| `CS-18` | `ballot_id` is in the list, and that is the load-bearing entry: a capability that could name a ballot would be exactly the join this architecture exists to prevent. `test_continuation_state_carries_no_forbidden_field` asserts both that `ContinuationState.__slots__` is disjoint from the frozenset **and** that `ballot_id` is a member of the frozenset, so the check cannot be weakened by shrinking the list |
| `CS-19` | The store enforces the same separation structurally: `continuations` is keyed by capability reference and holds no ballot reference; `accepted_ballots` and `spoiled_ballots` are keyed by ballot id and hold canonical envelope bytes, which carry no identity field of any kind (`BC-18`…`BC-20`). **They are separate maps with no shared key**                                                                    |
| `CS-20` | `LeafReservation` (`DM-21`) carries a `submission_reference` — the ballot id of the submission in flight — and **never** a capability. The reservation is anonymous with respect to the capability side                                                                                                                                                                                                               |
| `CS-21` | `PublicationObligation` and every outbox row carry `artifact_internal_reference`, `artifact_type`, `election_context_id` and a **coarse** window bucket. `FORBIDDEN_OUTBOX_FIELDS` names eight values that may never appear on such a row: `capability_reference`, `continuation_capability`, `credential_id`, `identity`, `voter_id`, `trace_id`, `correlation_id`, `exact_timestamp`                                |
| `CS-22` | Audit records accept **no** additional fields: passing one raises `AuditFieldRejected`. An audit log that accepted a capability field would be a capability-to-ballot map with a retention policy                                                                                                                                                                                                                     |
| `CS-23` | The logging boundary has 23 forbidden field names and a 7-name allow-list, and there is **no redaction step**: a forbidden field is a caller defect, so the record is refused (`ForbiddenLogFieldError`) and nothing is written                                                                                                                                                                                       |

## 6. The tests that assert this over every persisted row

| ID      | Test                                                                                            | What it scans                                                                                                                                                                                                                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-24` | `test_no_capability_to_ballot_leakage_in_any_persisted_row`                                     | after a challenge **and** a cast on the same capability: **every** reservation, **every** obligation, **every** outbox row and **every** idempotency key and value must not contain the capability reference; and **every** continuation state must not contain either ballot id. The check is `capability not in str(row)`, i.e. it covers the whole serialised row, not a field list |
| `CS-25` | `test_event_payloads_carry_no_forbidden_field`                                                  | **every** persisted outbox row, field by field, through `scan_mapping()` and against `FORBIDDEN_OUTBOX_FIELDS`                                                                                                                                                                                                                                                                         |
| `CS-26` | `test_continuation_state_carries_no_forbidden_field`                                            | `ContinuationState.__slots__` against `FORBIDDEN_CAPABILITY_FIELDS`                                                                                                                                                                                                                                                                                                                    |
| `CS-27` | `test_ballot_envelope_carries_no_identity_field`                                                | `BallotEnvelope.__slots__` — set equality against the six permitted names                                                                                                                                                                                                                                                                                                              |
| `CS-28` | `test_audit_log_is_not_a_capability_to_ballot_map` and `test_audit_records_reject_extra_fields` | the audit record's slots, and the rejection of an extra `capability_reference` argument                                                                                                                                                                                                                                                                                                |
| `CS-29` | `test_verifier_needs_no_store_or_capability`, plus the two `ast`-based tests                    | the verifier package must import none of `casting.store`, `casting.continuation`, `casting.transactions`, `casting.idempotency` or `api`, and the words `capability_reference`, `credential_id`, `voter_id`, `continuation_capability` must not appear **anywhere** in its source                                                                                                      |
| `CS-30` | `test_publication_state_reveals_nothing_about_others`                                           | the API's publication-state response carries no `capability_reference`, no `turnout` and no `accepted_count`, and reports `included = False` before closure                                                                                                                                                                                                                            |

`CS-24` and `CS-25` are the ones that matter for `DM-10`, because they run
over the rows the system actually persisted after a real submission rather
than over a type declaration.

## 7. Where the transitions run

Both transitions are called **inside** `store.transaction()`, which
snapshots every map on entry and restores the full snapshot on any
exception.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CS-31` | **A capability is never spent by a submission that does not commit.** If proof verification, the leaf reservation, persistence or the outbox enqueue raises, the entitlement mutation is rolled back with everything else                                                                                                                                                                                                            |
| `CS-32` | The idempotency check runs **inside** the transaction. It originally ran before the transaction was opened; two concurrent requests sharing an idempotency key could then both observe "no record yet" and both proceed, so a conflicting request was accepted instead of rejected. `test_c04_same_idempotency_key_concurrently` found it, the check was moved inside, and the code carries a comment saying not to move it back out |
| `CS-33` | In `submit_public_challenge` the order is: idempotency, capability lookup, entitlement check, `verify_ballot_proofs`, `verify_challenge_opening`, duplicate-ballot-id check, leaf reservation, `spend_public_challenge()`, persist the spoiled ballot, commit the reservation, create and enqueue the obligation, record idempotency                                                                                                 |
| `CS-34` | In `submit_cast_ballot` the order is the same except that `consume_for_cast()` runs **after** the artefact is written to `accepted_ballots`. Both orderings are inside one transaction and therefore not externally observable; the cast ordering is the conservative one — the entitlement is spent only once the artefact it paid for is durable                                                                                   |
| `CS-35` | An unknown capability raises `CapabilityUnknownError` before any proof work, so an invalid capability cannot be used to make the service perform expensive verification                                                                                                                                                                                                                                                              |
| `CS-36` | A rejected submission leaves the capability untouched and leaves no public trace: batch size is constant, so a failed submission is not observable from the board                                                                                                                                                                                                                                                                    |

## 8. Limitations, stated plainly

| ID      | Limitation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CS-37` | **The concurrency evidence covers this store only.** The transaction boundary is a re-entrant lock over in-memory maps. Nine named races × twelve repeats prove the _logic_ is race-free under the serialisation this store provides. They prove **nothing** about a production datastore, where the same invariants must come from row-level locking or a serialisable isolation level. Demonstrating that is a PACK-17 obligation (`OD-P16D-04`)                                                                                                                                                                                                                     |
| `CS-38` | **There is no production authentication.** The reference API performs none and takes a test-only anonymous capability string; issuance, binding to an eligibility credential and revocation are outside this round (`OD-P16D-08`). Nothing here is evidence that the right person holds the capability — only that a holder can spend it at most as the arithmetic allows                                                                                                                                                                                                                                                                                              |
| `CS-39` | **`K` and `A` are module-level constants, not per-election configuration.** An election profile that needed different values would need a code change and a re-reading of `CS-15`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `CS-40` | **A reason-code imprecision that was corrected:** `spend_public_challenge()` used to raise `CastEntitlementExhaustedError` (`CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED`) when the capability was already consumed — the wrong entitlement for a challenge path, and a code that told a caller about a state it had not asked about. It now raises `PublicChallengeEntitlementExhaustedError` (`CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED`) for both refusal reasons. In the transaction path the branch is still not reached, because `consume_for_cast()` also clears the public-challenge flag and the transaction's own entitlement check fires first with the same code |
| `CS-41` | **`DM-10` is enforced for the artefacts this round persists.** It is a property of these types and these rows, not a proof that no future field could reintroduce a join. The tests are the guard, and a new persisted type needs a new row-scan test                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `CS-42` | **Cross-mirror split-view detection is not implemented** and must not be claimed; equivocation is detected only within a single exported view (`OD-P16D-06`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `CS-43` | **Nothing in this document is evidence of BSI conformity.** `VO-08` is **OPEN**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

## 9. What this document does not decide

```text
Capability issuance and eligibility binding → PACK-15, PACK-16C, PACK-17
Production authentication                   → OD-P16D-08, PACK-17
Production datastore isolation level        → OD-P16D-04, PACK-17
Values of E, batch interval and capacity    → OD-P16C-10, GOVERNANCE
Retention of continuation records            → OD-P16A-07, PACK-09/PACK-17
Cross-mirror gossip / split-view detection   → OD-P16D-06, PACK-17
BSI conformity / VO-08                       → OPEN, PACK-16B review + PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
