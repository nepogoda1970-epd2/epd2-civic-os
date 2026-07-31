# PACK-15 — Security evidence

```text
PACK-15 IMPLEMENTATION CANDIDATE
PARTIAL LOCAL VERIFICATION ONLY
DEPENDENCY INSTALLATION BLOCKED BY SANDBOX NETWORK POLICY
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

---

## 1. Trust boundaries, and what crosses each

| Boundary                                             | Direction permitted | What crosses                                                               | What may not                                                                                             |
| ---------------------------------------------------- | ------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Ordinary workspace -> isolated voting origin (WS-03) | one way             | PACK-14's opaque, single-use, audience- and context-bound handoff artifact | account, session, device, persona - ten prohibited fields, refused on arrival rather than trusted absent |
| Identity side -> voting side                         | one way             | the twelve-field eligibility assertion                                     | anything else; the field list is closed and enforced in `wire_payload()`                                 |
| Voting side -> identity side                         | **none**            | -                                                                          | there is no read edge, and ADR-089 exists to keep it that way                                            |
| Governance registry -> both sides                    | read only           | administrative configuration                                               | the registry has no column for a participant, an assertion, a credential, a ballot or a turnout figure   |

The asymmetry is the design. A voting-side component that could read
identity-side state would make every other control cosmetic.

---

## 2. Authentication and authorization

### 2.1 Ten roles, one matrix

`services/governance-service/src/epd2_governance_service/voting_authorization.py`
holds the ten roles, their capabilities, and the separation rules as
executable assertions rather than prose. `assert_matrix_is_complete()`
runs **at import time**, so a role added without capabilities fails when
the module loads, not when someone exercises the gap in production.

The structural rules, each its own named function raising a reason-coded
exception:

| Rule                                                                                                           | What it prevents                                                                      |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| No role holds eligibility **and** issuance **and** tally                                                       | One principal deciding who may vote, minting their credential and counting the result |
| The Credential Issuer holds no ordinary identity-record access                                                 | The one component that sees credentials also seeing who people are                    |
| The Eligibility Officer holds no credential-secret access                                                      | The mirror of the above                                                               |
| No auditor role spans the identity-side and voting-side audit streams                                          | An auditor reconstructing the link by reading both sides                              |
| No role spans the audit stream groups, auditor or not                                                          | The same, arrived at through a job title nobody classified as auditing                |
| Security administrator and system administrator are distinct, with neither capability set containing the other | The "two roles" that are one person with one login                                    |
| No self-review                                                                                                 | An officer reviewing their own decision                                               |
| Privileged export and break-glass need two **distinct** approvers holding **different** roles                  | One person approving twice                                                            |

### 2.2 The API boundary

`epd2_core.api_contracts` applies six checks to every request, in this
order: operation lookup against a closed catalogue, origin validation,
role authorization, obligation checks (idempotency key, expected
version), the handler, and a response-safety scan.

Two properties are enforced at declaration time rather than at call time:

- `EndpointSpec` has **no defaults** for `idempotency_key_required`,
  `version_check_required`, `audit_evidence_required` or
  `authorized_roles`. A new endpoint must state all of them.
- `assert_consequential_contract` refuses a spec that calls itself
  consequential and then waives an obligation, and
  `assert_no_endpoint_spans_the_boundary` refuses an operation name
  declared on both sides of the trust boundary - so the correlation
  removed from SQL cannot be rebuilt in routing.

`unauthenticated_by_design` endpoints exist (four of them) and each
carries a `justification` that is validated as non-empty. They are the
handoff acceptance, the one-time pickup, credential issuance and
credential redemption - all reached from inside the isolated origin,
where an account context would be exactly the linkage the origin removes.

---

## 3. Fail-closed defaults

An unconfigured deployment must fail at its first real operation, not
after an incident.

| Port                             | Default binding                        | Behaviour                                                                                                                                                                            |
| -------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Assertion signing custody        | `FutureKeyServiceCustody`              | every method raises `SYSTEM_DEPENDENCY_UNAVAILABLE`                                                                                                                                  |
| Assertion verifier (voting side) | **none - a required argument**         | `build_voting_credential_service` has no default; there is no fallback verifier that accepts                                                                                         |
| Storage adapters                 | `Sql*` in both composition roots       | `tests/repository/test_pack15_default_binding.py` asserts no in-memory adapter is named by either root, and walks a built runtime to catch a binding made through a default argument |
| Identity-side databases          | **none - both are required arguments** | a default would have to be either one shared database, which collapses the boundary, or a pair of names nobody chose                                                                 |

`assert_production_custody` refuses any custody whose key identifier
starts with `test-`, so a test key cannot sign a real assertion by
omission.

---

## 4. Replay, reuse and exactly-once

The exactly-once guarantee is deliberately **split** across the boundary,
because a single enforcement point would need to see both sides:

| Side     | Rule                                             | Enforced by                                                                 |
| -------- | ------------------------------------------------ | --------------------------------------------------------------------------- |
| Identity | one assertion per participation unit per context | `participation_unit_ledger` composite primary key - the INSERT is the check |
| Voting   | one credential per assertion nonce               | `spent_nonce` primary key - again, the INSERT is the check                  |

Neither side can enforce the other's half, and neither needs to know the
other's data to enforce its own. Both are decided by the database, so a
concurrent second attempt loses on a constraint rather than on a
check-then-act read that raced. This is executed under real thread
contention in the persistence tests: eight threads, eight connections,
one winner.

Single-use artefacts and how a second presentation is refused:

| Artefact          | Key                                               | Second presentation             |
| ----------------- | ------------------------------------------------- | ------------------------------- |
| Handoff artifact  | SHA-256 digest, primary key                       | `HANDOFF_ALREADY_USED`          |
| Assertion pickup  | `consumed_at IS NULL` inside the UPDATE predicate | `ASSERTION_PICKUP_ALREADY_USED` |
| Voting credential | `uq_credential_redemption_credential`             | `CREDENTIAL_ALREADY_REDEEMED`   |
| Assertion nonce   | `uq_eligibility_assertion_nonce`                  | refused at insert               |

The artifact **value** is never stored - only its digest. A record
holding the value would be a replayable secret at rest.

---

## 5. Two defects found and fixed during this round

Both were found by an adversarial review of the API layer after it was
written, and both are recorded here rather than quietly repaired, because
a security document that lists only the controls that worked first time
is not evidence.

### 5.1 A failed mint left a participation-unit claim behind

`mint_assertion` claims the participation unit before minting, because
that ordering is what makes the identity-side half of exactly-once
survive a retry. The cost of that ordering is that a mint which then
fails - an unbound key service, a malformed field, a storage error - left
an **uncommitted** INSERT that the next successful write on the same
connection would commit.

The consequence was the worst available: the participation unit would be
marked used while no assertion existed, and the participant would be
refused forever with `CREDENTIAL_ALREADY_ISSUED` for an assertion they
never received. A privacy architecture that silently disenfranchises
someone has failed at something more important than privacy.

Fixed by a rollback guard around everything after the claim, and pinned
by two tests: one asserting the ledger is empty after a refused mint even
once a later write commits, and one asserting the same unit is still
mintable afterwards.

### 5.2 The voting side's identity-field scan was shallow

`assert_no_identity_field` scanned only top-level request keys, while the
outbound `assert_response_safe` walked every nesting depth. The inbound
bodies are nested (`assertion`, `terms`), so the shape a caller would
actually send an identity field in was the one that passed.

Fixed by walking every depth on the way in as well. Two tests now send
`person_id` inside `assertion` and `participant_reference` inside `terms`.

### 5.3 Two smaller corrections in the same pass

- A client-controlled `minting_delay_seconds` outside the governed window
  raised a bare `ValueError` from the domain, which has no reason code,
  so the dispatcher re-raised it and the boundary failed open into a
  stack trace. The value is now bounded where it arrives and refused with
  `API_REQUEST_MALFORMED`.
- `credential.revoke` declared `DUAL_CONTROL_REQUIRED` while no code path
  could return it. Rather than deleting the declaration, the boundary now
  requires a second signature - a declared code no path can produce is a
  contract that reads stricter than the system is, and a reviewer reads
  the contract.

---

## 6. Cryptography

| Use                       | Implementation                                          | Status                                                                                                  |
| ------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Assertion integrity       | HMAC-SHA256 over a canonical message                    | **reference implementation**; production custody is unbound and refuses                                 |
| Evidence bundle signature | HMAC-SHA256, a key distinct from every other function's | **reference implementation**; key identifier is `test-` prefixed and refused outside a test trust store |
| Handoff artifact digest   | SHA-256                                                 | production-shaped; the digest is the stored key and the value is never stored                           |
| Audience comparison       | `hmac.compare_digest`                                   | constant-time, so audience checking is not a timing oracle                                              |
| Nonce generation          | `secrets.token_hex`                                     | production-shaped                                                                                       |

No asymmetric signing, no HSM or KMS integration, and no key rotation
procedure exists in this round. `FutureKeyServiceCustody` is the declared
seam and every one of its methods raises.

---

## 7. Audit

Six streams, three **separate database files**: identity-side (AS-01,
AS-02), voting-side (AS-03, AS-04) and neutral (AS-05, AS-06 plus the
export log).

The separation is expressed as the absence of a join path. Selecting the
voting-side table through the identity-side connection is not a
permission failure - the table does not exist there. A test asserts
exactly that, by catching the `OperationalError`.

Each stream has its own key space: AS-01 carries a case reference, AS-02
an assertion reference, AS-03 a credential reference, and AS-04 through
AS-06 carry no subject at all. **No table carries two of them.** That is
the ADR-093 pairing prohibition written in DDL.

Pre-closure evidence export requires a dual-control reference as a
**CHECK constraint**, not an application-layer assertion, so it is not a
step an operator can skip on a busy evening.

---

## 8. Residual risk

1. **No production key custody.** Everything signed here is signed with a
   reference HMAC key. This is the single largest gap and it is declared,
   not hidden.
2. **No transport layer.** The API is transport-agnostic values; TLS,
   rate limiting, request-size limits, WAF behaviour and DoS resistance
   are all deployment concerns this repository does not implement or
   test.
3. **The frontend is unverified.** The isolated voting origin's client
   code exists and has never been executed, type-checked or rendered in
   this environment.
4. **No penetration test, no threat-model review by a second party, no
   dependency vulnerability scan** has been performed. The dependency
   scan in particular could not run: the registries return HTTP 403.
5. **SQLite is the reference persistence.** Its concurrency model is not
   a production database's. The constraints that carry the guarantees
   (primary keys, unique indexes, CHECKs) port directly; the isolation
   behaviour under real load does not, and re-verifying the concurrency
   tests against the production engine is required work that has not
   happened.
6. **`ALREADY_VOTED` cannot be emitted by this system**, but nothing here
   prevents an operator building a component outside it that correlates
   two exports by hand. The architecture removes the data; it cannot
   remove a determined human with two spreadsheets and enough time - it
   can only make that the visible, auditable, effortful path it now is.
