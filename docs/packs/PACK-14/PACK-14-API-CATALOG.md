**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`

> **Superseding status note, added by the PACK-14 FINAL PASS round
> (2026-07-30).** The header above records the implementation-candidate
> round that wrote this document and is retained unchanged as the
> historical record. External GitHub Actions has since run against this
> exact tree and **passed every stage**, so PACK-14 is now **FINAL PASS**
> at `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0`. The PASS changes
> the _round's_ status and nothing else: no limitation below is closed by
> it, and **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md` and
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`.

# PACK-14 — API Catalog

**42 operations catalogued; 12 of them routed by a runnable reference
adapter.** Both halves of that sentence are load-bearing, and both are
constants in the code rather than claims in prose:
`service_api.ROUTED_OPERATIONS` has 12 entries and
`service_api.CONTRACT_ONLY_OPERATIONS` has 30, and a test asserts their
union is exactly the catalogue. No document can therefore imply that all
42 run.

The catalogue itself is `epd2_identity_service.api.ENDPOINTS` — data
rather than prose, so a test can check it. It states each operation's
obligations (§1), and it is what §7's adapter dispatches against.

Like PACK-10 through PACK-13, this round exposes no **HTTP** surface, so
there is deliberately no `contracts/openapi/pack-14.yaml`: an OpenAPI
document describing an unbound transport would make the contract suite
assert against a fiction. The reference adapter is transport-agnostic by
construction — `ApiRequest` and `ApiResponse` are dataclasses — and
binding it to HTTP, along with the framework and the gateway that
implies, is a deployment's job and not this round's.

## 1. The obligations every consequential operation carries

`EndpointSpec` has no default for `idempotency_key_required`,
`version_check_required`, `audit_evidence_required` or
`required_assurance`. A new endpoint must state all four, and
`assert_consequential_contract` refuses a spec that calls itself
consequential and then waives one. That is how "all consequential
endpoints require an idempotency key" survives the tenth endpoint someone
adds in a hurry.

## 2. The operations

| Area           | Operations                                                                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Account        | `create`, `activate`, `get_security_state`, `request_closure`, `cancel_closure`, `close`, `list_restrictions`                                      |
| Contacts       | `add`, `verify`, `change`, `remove`                                                                                                                |
| Credentials    | `begin_passkey_enrollment`, `complete_passkey_enrollment`, `list`, `revoke`, `enroll_mfa`, `verify_mfa`, `remove_mfa`, `regenerate_recovery_codes` |
| Authentication | `begin`, `complete`, `begin_step_up`, `complete_step_up`                                                                                           |
| Sessions       | `list`, `revoke`, `revoke_all`                                                                                                                     |
| Recovery       | `request`, `submit_evidence_reference`, `review`, `approve`, `reject`, `complete`, `dispute`                                                       |
| Proofing       | `begin_case`, `attach_evidence_reference`, `record_decision`, `get_state`                                                                          |
| Bootstrap      | `create_request`, `authorize`, `redeem`                                                                                                            |
| Voting handoff | `issue`, `redeem`                                                                                                                                  |

## 3. The two unauthenticated-but-consequential exemptions

Both set `unauthenticated_by_design=True` and both carry a written
justification, checked by a test:

- **`account.create`** — registration is reachable without a session by
  definition. Its consequence is bounded: a new account is `pending` and
  can do nothing at all until a contact channel is verified.
- **`voting_handoff.redeem`** — there is no session on this side of the
  boundary at all. The redeeming party is WS-03 presenting an
  identity-free artifact, and requiring a session here would be requiring
  the identity ADR-088 forbids.

## 4. What is deliberately absent

No `account.list_all`, no `identity.export`, no `account.impersonate`, no
administrative read-through and no reverse resolution of a redeemed
voting artifact. **PACK-14 builds no universal identity console**, and a
test asserts that the catalogue contains none of these.

## 5. Response discipline

Every response view model passes `assert_response_safe`, which runs the
same `reject_prohibited_payload_keys` the event builder uses. One rule
rather than two, so there is never a question of which surface is
stricter.

`AccountSecurityStateView` carries counts and classes only — no
credential reference, no device fingerprint, no contact value. A security
summary that would help an attacker who obtained it has failed at the one
thing it is for.

`SessionView` carries an opaque `session_reference` and the device label
the holder chose. There is no session identifier in it and none in any
URL that reaches it: revocation takes the reference in the request body.

## 6. Errors

`ApiError` requires a registered reason code; there is no free-text-only
variant. The authentication surfaces return the uniform public code from
`authentication.py`, so a response never becomes an account-existence
oracle. Each endpoint spec enumerates the codes it may return.

## 7. The runnable reference boundary

`epd2_identity_service.service_api.IdentityServiceApi` is the adapter
that makes the twelve routed operations executable.
`runtime.build_identity_service` wires it to the durable stores, and
`services/identity-service/tests/test_pack14_service_api.py` drives a
full account lifecycle through it.

**What it does.**

| Step                | What happens                                                                                                                                  |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Routing             | The operation name is looked up in `ROUTED_OPERATIONS`; an unrouted one is refused, not silently accepted                                     |
| Envelope validation | Origin → session → idempotency → version, in that fixed order, against the endpoint spec's declared obligations                               |
| Origin              | Checked against the ten declared workspace origins; an undeclared origin is refused                                                           |
| Audience            | `_assert_audience` refuses a session presented to the wrong workspace                                                                         |
| Session context     | `SessionContext` carries the authenticated caller; an operation that requires one and has none is refused                                     |
| Idempotency         | The key is recorded durably, so a replayed request after a **restart** returns the first answer rather than acting twice                      |
| Version             | The optimistic-concurrency version travels in the request and a stale one is refused by the store, not by the adapter                         |
| Parsing             | A malformed body is `API_REQUEST_MALFORMED`, never a `KeyError` reaching the caller                                                           |
| Transactions        | A dispatch that fails rolls back; there is no partially applied operation                                                                     |
| Serialization       | `ApiResponse.__post_init__` runs `assert_response_safe`, so a response carrying a prohibited identifier or a secret **cannot be constructed** |

**Every response carries a reason code**, including the successful ones —
those are the `*_RECORDED` classifications canon §24 requires, because
canon §24's registry is refusal-only and a success still needs a stable
thing to name it.

**A governed refusal is an answer, not an exception.** `dispatch` catches
any exception carrying a `reason_code` and returns
`status="refused"` with that code. An exception with **no** registered
code is re-raised deliberately: an ungoverned failure must not be
laundered into a tidy response.

**What it is not.** No HTTP server, no TLS termination, no routing
framework, no gateway, no public deployment, no rate-limiting
infrastructure, no external provider. Those are deployment concerns and
they remain excluded.
