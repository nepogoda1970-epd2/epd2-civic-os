# PACK-15 — Canon Assessment

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

## Verdict

```text
CANON AMENDMENT NOT REQUIRED
```

`CANON_VERSION` remains `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
is not modified by this round.

---

## Why — the reasoning, not the conclusion

A canon amendment is required when a round needs a concept the canon does
not have, or needs to change the meaning of one it does. PACK-15 needs
neither, and the reason is worth stating precisely rather than asserted,
because "the invariants already imply it" is exactly the kind of claim that
hides an amendment.

### 1. The eligibility model already exists and is already owned

Canon 9 defines `EligibilityRule`, `EligibilityDecision` and
`EligibilitySnapshot` with `eligibility-service` as owner, and canon 9.1
already imposes the **rule freeze**: a versioned, immutable rule whose
re-submission with different content is refused. Canon 19d.4 adds
`ParticipantEligibilityPolicy` with the same owner and the fail-closed
conjunction rule for assurance.

PACK-15 needs: a rule-**set** version, frozen; a context-bound decision;
reason codes; a validity window. The first is the existing freeze applied
to a set rather than a rule — a specification-level composition of an
existing canonical property, not a new one. The rest are operational
detail around a canonical aggregate. **No new canonical entity, and no
changed meaning.**

### 2. The credential prohibition already exists, and PACK-15 only tightens it

Canon 10.1 defines `ParticipationCredential`, owned by
`credential-service`, with an explicit prohibition list —
`identity_record_id`, `person_id`, `account_id`, `full_name`,
`date_of_birth`, `address`, `email`, `eid_subject` — enforced structurally
in the baseline through a forbidden-field set.

PACK-15 adds one prohibition: **no assertion identifier alongside a
credential identifier.** Adding to a prohibition list is not an amendment
in any direction that matters: it removes possibilities, it does not
change a meaning, and canon nowhere permits the field being forbidden. If
the direction were reversed — if PACK-15 needed canon to _permit_
something 10.1 forbids — this verdict would be different.

### 3. The ballot's identity-freedom already exists

Canon 15.3's prohibition already makes `VoteEnvelope` and `VoteReceipt`
structurally identity-free, and already requires `credential_proof` to
reference a `ParticipationCredential` rather than an account. PACK-15
touches neither, and its requirement that the reference not be retained as
a durable mapping is a **PACK-16 obligation recorded here**, not a change
to canon 15.

### 4. The ownership boundaries already exist

Canon's ownership matrix already places eligibility in
`eligibility-service`, credentials in `credential-service`, ballots in
`voting-service`, tally in `tally-service`, roles in
`governance-service`, and already forbids read and write edges from
`eligibility-service` and `membership-service` to `voting-service`,
`tally-service` and `VoteEnvelope` — directly or through
`ParticipationRightsProfile`. PACK-15's bounded contexts land on those
owners without moving one of them.

The one context PACK-15 places somewhere canon does not name — the Voting
Context Registry, in `governance-service` — is a **pack-level module
placement**, not a canonical aggregate. Canon has no `VotingContext`
entity and PACK-15 does not create one; the registry is an administrative
configuration store, in the same category as PACK-14's `SessionRecord`,
which OD-P14-05 already decided is a service-level aggregate rather than a
canonical one.

### 5. The invariants are already canonical commitments

`FIR-INV-002` (identity/ballot unlinkability), `FIR-INV-003` (Voting Client
isolation), `FIR-INV-004` (eligibility/credential separation) and
`FIR-INV-005` (no intermediate tally) are all `approved` in the Master
Register and are already reflected in canon 15.3's prohibition and in the
Architecture Framework. PACK-15 **derives** its architecture from them
rather than adding to them.

---

## What would have required an amendment, and was avoided

| Tempting move                                                                      | Why it would have amended canon                      | What PACK-15 does instead                                                                                      |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A canonical `VotingContext` aggregate                                              | Adds a canonical entity with an owner                | Pack-level configuration store in `governance-service`; canonical treatment deferred to PACK-16 if ever needed |
| A canonical `EligibilityAssertion` entity                                          | Same                                                 | A pack-level artifact whose events use canon §21's envelope unchanged                                          |
| A new eligibility-assurance scale for voting                                       | A second assurance vocabulary beside canon 19d.8's   | Reuses canon's four values and asserts only a boolean across the boundary                                      |
| Extending canon 10.1's `ParticipationCredential` with a context field as canonical | Changes a canonical entity's shape                   | Specifies context binding at pack level; the canonical shape is unchanged                                      |
| A canonical linkage table between eligibility and credentials                      | Directly contradicts `FIR-INV-002` and `FIR-INV-004` | The pairing is structurally absent; ADR-093                                                                    |
| A canonical unified audit chain                                                    | Adds a canonical aggregate and breaks `FIR-INV-002`  | Six separately keyed streams at pack level                                                                     |
| Declaring `credential_proof` a retained mapping                                    | Changes canon 15.3's meaning                         | Records the non-retention requirement as PACK-16's obligation                                                  |

---

## Canonical questions this round raises and closes without an amendment

| Question                                                                        | Decision                                                                                                              | Canon effect |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------ |
| Does the voting context belong in canon?                                        | **No.** It is administrative configuration, not a domain aggregate, and PACK-16 may revisit it with the casting model | **None**     |
| Does the eligibility assertion belong in canon?                                 | **No.** It is a short-lived boundary artifact; its events use canon §21 unchanged                                     | **None**     |
| Does the rule-**set** need a canonical form beside canon 9's `EligibilityRule`? | **No.** A set version is a composition of frozen rules; the freeze property is canon's and is reused                  | **None**     |
| Does `ParticipationCredential` need canonical extension for context binding?    | **No.** Binding is a pack-level constraint on how the existing entity is issued                                       | **None**     |
| Does the six-stream audit separation need a canonical audit model?              | **No.** `audit-core` provides primitives; the separation is a pack-level authorization and keying decision            | **None**     |

---

## What is deferred to PACK-16, and might amend canon then

Recorded honestly rather than pre-empted:

- If PACK-16 adopts a cryptographic issuance construction (blind
  signatures, anonymous credentials), `ParticipationCredential`'s canonical
  shape may need to change. **That is PACK-16's assessment to make**, and
  this round deliberately does not make it from outside.
- If verifiable tally introduces canonical evidence entities, canon 15 may
  need extension. Also PACK-16's.

**This round amends nothing.**

---

## The architecture correction (2026-07-31) — verdict unchanged

```text
CANON AMENDMENT NOT REQUIRED
```

Five open decisions were closed. Each closure was resolved in the direction
that needs no canon change, and that was a selection criterion rather than
a coincidence.

| Closure                               | Canonical question it raises                                                      | Decision                                                                                                                                                                                 | Canon effect |
| ------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `OD-P15-01` Assertion Issuer boundary | Does a module boundary inside `eligibility-service` change a canonical ownership? | **No.** Canon 9 and 19d.4 assign ownership to the service; internal module and storage boundaries are pack-level, exactly as PACK-14 treated its six identity modules                    | **None**     |
| `OD-P15-02` Timing controls           | Do queueing, cohorts and delays introduce a canonical entity?                     | **No.** `IssuanceTimingProfile` is governed configuration attached to a pack-level context object, not a canonical aggregate; `FIR-CONFIG-001` owns the class                            | **None**     |
| `OD-P15-03` Context-scoped pseudonym  | Does a pseudonym create a canonical identifier space?                             | **No** — and the closure makes it _less_ canonical, not more: the pseudonym is now internal to one service, absent from every crossing artifact, and never a subject identifier anywhere | **None**     |
| `OD-P15-04` Evidence bundle           | Does the bundle need a canonical evidence entity?                                 | **No.** `audit-core` provides the primitives; the bundle is a pack-level export format with its own schema version, governed by ADR-074's evolution rules                                | **None**     |
| `OD-P15-07` Credential delivery       | Does restricting delivery change canon 10.1's `ParticipationCredential`?          | **No.** Delivery is a boundary constraint on how an existing entity reaches its holder. Canon 10.1's shape and prohibition list are untouched; PACK-15 only adds prohibitions            | **None**     |

**The direction of every closure matters.** Each one _removes_
possibilities: immediate issuance becomes unavailable, the pseudonym stops
crossing the boundary, ten delivery channels become structurally absent,
the assertion field list stays closed, and the bundle's content list is
closed. A round that only forbids things does not need a canon that permits
more.

### `FIR-OSS-001` … `FIR-OSS-006` and the canon

The register's new §29 selects `EUPL-1.2` as the intended project licence
and adds six approved obligations. **None of them is a canonical concept,
none is touched by this round, and none affects this verdict.** Licensing
governs the distribution of software; the canon governs the domain event
model. They do not intersect, and this round neither implements nor claims
compliance with any `FIR-OSS-*` obligation.

**This round, including its architecture correction, amends nothing.**
`CANON_VERSION` remains `0.8.0` and
`docs/canonical/TZ-00-domain-event-canon.md` is neither modified nor
included in this archive.
