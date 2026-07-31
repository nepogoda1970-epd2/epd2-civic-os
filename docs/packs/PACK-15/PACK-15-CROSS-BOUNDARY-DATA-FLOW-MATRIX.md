# PACK-15 — Cross-Boundary Data Flow Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Every hop in the flow, what may cross it, what must be absent, and what
enforces the absence.

**Corrected by this revision:** the queue and pickup hops are added, the
delivery hops are re-drawn so that credential material never leaves WS-03
(`OD-P15-07`), and the store table records the Assertion Issuer's separate
storage and key custody (`OD-P15-01`).

---

## 1. The hops

```text
H-01  membership / identity source        → Eligibility Service        [identity, internal]
H-02  identity-service (PACK-14 handoff)  → Handoff Boundary           [identity, internal]
H-03  Eligibility Service                 → Assertion Issuer           [identity, module boundary]
H-04  Assertion Issuer                    → issuance queue → release   [identity, internal]
H-05  ordinary workspace (WS-02)          → participant                [one-time handoff artifact ONLY]
═════════════════════ TRUST BOUNDARY ═════════════════════
H-06  WS-03                               → Handoff Boundary           [pickup: artifact in, assertion out]
H-07  WS-03                               → Credential Issuer          [assertion in, credential out]
H-08  WS-03                               → Credential Issuer          [redemption]
H-09  Credential Issuer                   → voting domain (PACK-16)    [continuation capability]
H-10  voting domain                       → tally domain (PACK-16)     [out of scope here]
H-11  every component                     → its own audit stream       [six separate streams]
H-12  audit streams                       → Independent Auditor        [evidence bundle only]
```

`H-06` is the only hop on which an identity-side component answers a
request originating inside WS-03, and it returns **the assertion and
nothing else** — no account, no session, no pseudonym, no case reference.

---

## 2. Per-hop contract

| Hop    | May carry                                                                                    | Must be absent                                                                                                  | Enforced by                                                                   |
| ------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `H-01` | Scoped predicates declared by the frozen rule-set version; scope; participation class        | Member record, address, email, phone, member number, account ID, person ID, persona, DOB, name                  | Governed adapter with a declared input set; prohibited-key scan               |
| `H-02` | The fact that a valid single-use artifact was redeemed for a stated context; the context ref | The account, the session, any PACK-14 identifier, any reverse-resolution capability                             | ADR-088's artifact properties; no read edge back to `identity-service` stores |
| `H-03` | Decision result, class, scope, assurance-satisfied flag, context reference                   | Criteria inputs, reason history, evidence, the context-scoped pseudonym, everything in `H-01`'s absent list     | Separate storage boundary; the Assertion Issuer's declared input type         |
| `H-04` | The assertion, held; batch and cohort state                                                  | Any participant reference in the queue's own metadata; precise release timestamps in logs                       | Queue keyed on the assertion, not the participant; timing-class logging       |
| `H-05` | **The one-time handoff artifact, and nothing else**                                          | The assertion; the credential; any eligibility data; any case reference                                         | ADR-088; the workspace has no interface that returns an assertion             |
| `H-06` | Inbound: the artifact. Outbound: the assertion                                               | Account, session, pseudonym, case reference, evidence, any identity-side identifier                             | Audience and origin binding; one-time pickup state                            |
| `H-07` | Inbound: the assertion. Outbound: the opaque credential                                      | Any identity-side identifier; any shared trace or correlation ID; any session; the assertion ID in the response | Trace break at the boundary; credential field set                             |
| `H-08` | Inbound: the credential. Outbound: the continuation capability                               | Identity; membership data; anything about the participant; a reusable session                                   | Response shape; atomic redemption                                             |
| `H-09` | A minimal single-use continuation capability                                                 | The credential ID, any identity, any persistent identifier                                                      | Capability ≠ credential; PACK-16's acceptance                                 |
| `H-10` | PACK-16's business                                                                           | Identity, credentials, eligibility — none of which exist on that side                                           | PACK-16; canon 15.3                                                           |
| `H-11` | Stream-appropriate evidence                                                                  | Any field from another stream's key space                                                                       | Separate keys, separate authorization, separate retention                     |
| `H-12` | A versioned evidence bundle: totals, versions, commitments, disclosure metadata              | Raw records; identity; pseudonyms; credential or assertion identifiers; ballot data                             | Bundle schema; export authorization; complementary suppression                |

---

## 3. What may never cross the trust boundary, in either direction

| Category                     | Examples                                                                                       |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| Identity                     | Account ID, person record ID, membership ID, member number, name, DOB                          |
| Contact                      | Email, phone, address, communication persona                                                   |
| Session                      | Any cookie, token, session reference or authentication context                                 |
| Evidence                     | Any PACK-11 document or reference to one                                                       |
| Eligibility internals        | Criteria inputs, reason history, reviewer identity, case reference                             |
| **Context-scoped pseudonym** | In any encoding, in any field, in either direction                                             |
| Correlation aids             | Trace IDs, request IDs shared with the identity side, correlation IDs, shared idempotency keys |
| Persistent identifiers       | Any identifier stable across two contexts, in any encoding                                     |
| Outcome data, before closure | Anything from which an outcome can be inferred                                                 |
| Ballot content               | In either direction, at any time                                                               |

**Both directions matter.** A response that carries a voting-side
identifier back into the ordinary workspace is as damaging as a request
that carried identity out.

---

## 4. Credential material — where it may exist

| Location                                    | Permitted   | Note                                                            |
| ------------------------------------------- | ----------- | --------------------------------------------------------------- |
| Credential Issuer's own store               | yes         | Its status record, with no identity and no assertion ref        |
| WS-03 page memory, during one visit         | yes         | Volatile only                                                   |
| WS-03 persistent storage                    | **no**      | ADR-096; and the content is forbidden as well as the store      |
| The ordinary workspace, in any form         | **no**      | `H-05` carries the artifact only                                |
| Email, SMS, push payload                    | **no**      | §5                                                              |
| Clipboard                                   | **no**      | Readable across origins and by extensions                       |
| URL query or fragment                       | **no**      | Logged by proxies, servers, history and referrers               |
| Downloadable file, print or PDF             | **no**      | Persists outside the boundary                                   |
| On screen as copyable or transcribable text | **no**      | Becomes a transferable bearer value and a coercion instrument   |
| Any operator-visible surface                | **no**      | A helper who can see it can retain it                           |
| Logs, traces, metrics, error reports        | **no**      | Reason codes only                                               |
| Backups                                     | status only | The status record is backed up; there is no material to back up |

---

## 5. Browser-boundary controls in WS-03

| Control           | Requirement                                                                                                                                     |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Origin            | Separate origin; `sessionSharing: forbidden`; nothing inherited from a sibling origin                                                           |
| Cookies           | None for identity; no parent-domain cookie; no cookie shared with any other workspace                                                           |
| Storage           | No localStorage, sessionStorage, IndexedDB or cache entry as identity or cross-context state — **and no credential material**                   |
| Service worker    | Not shared; none that persists participation state or intercepts credential exchanges                                                           |
| CSP               | Own policy; `frame-ancestors 'none'`; no third-party script origin; no inline script without a nonce; no `connect-src` to an ordinary workspace |
| Redirects         | Allow-list only; no caller-supplied raw URL; no open redirect                                                                                   |
| Referrer          | `no-referrer` on entry and on exit                                                                                                              |
| Cache             | `no-store` on every credential-, assertion- and status-bearing response                                                                         |
| Clipboard         | No programmatic clipboard write of any credential or assertion value                                                                            |
| Analytics         | None. No tag manager, no session replay, no product analytics, no A/B framework                                                                 |
| Fingerprinting    | None, including implicit probes                                                                                                                 |
| Error reporting   | Reason codes only; no identity, no credential or assertion value, no pseudonym, no stack containing either                                      |
| Return navigation | Carries no identity-bearing token and no voting-side identifier                                                                                 |

---

## 6. Data-at-rest boundaries

| Store                         | Owner     | Contains                                                                                                                                                                           | Must never contain                                    |
| ----------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Voting context store          | VC-01     | Context configuration incl. `IssuanceTimingProfile`                                                                                                                                | Any participant data                                  |
| Eligibility case store        | VC-02     | Cases, decisions, reason codes, evidence refs                                                                                                                                      | Assertion nonce, credential ref, ballot, tally        |
| Participation-unit ledger     | VC-02     | One entry per participation unit per context, with an "assertion minted" flag; keyed on a participant reference or, where the privacy profile requires, a context-scoped pseudonym | Which assertion; any credential ref                   |
| **Assertion issuance store**  | **VC-03** | Assertion IDs, queue and release state, status                                                                                                                                     | Credential refs; redemption outcomes; identity        |
| **Assertion signing key**     | **VC-03** | Its own key custody                                                                                                                                                                | Any co-location with the decision store's credentials |
| Pickup store                  | VC-05     | One-time pickup state                                                                                                                                                              | The account; the credential; the pseudonym            |
| Spent-nonce set               | VC-04     | Nonces, as a **set**                                                                                                                                                               | Credential IDs; any mapping                           |
| Credential store              | VC-04     | Credentials, status, revocation, redemption                                                                                                                                        | Assertion refs; identity; pseudonyms; ballot refs     |
| Continuation capability store | PACK-16   | Capabilities                                                                                                                                                                       | Credential IDs; identity                              |
| Six audit streams             | VC-06     | Per-stream evidence                                                                                                                                                                | Cross-stream keys                                     |
| Evidence bundle store         | VC-06     | Versioned bundles: totals and commitments                                                                                                                                          | Per-participation records; identifiers; ballot data   |

**No backup, replica, export, snapshot or archive may combine the
assertion issuance store with the spent-nonce set or the credential
store.** The prohibition applies to infrastructure, not only to application
code, and the implementation round's evidence must include the backup
topology.

---

## 7. Observability boundaries

| Signal          | Permitted                                                        | Prohibited                                                                                                                                |
| --------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Metrics         | Counts and health, aggregated, disclosure-controlled             | Per-participant series; per-scope series below the threshold; anything outcome-inferring; **queue depth per scope in a small electorate** |
| Logs            | Reason codes, timing classes, context references                 | Identifiers from the other side; minimized attribute values; nonces; credential or assertion material                                     |
| Traces          | Within one side                                                  | **Across the boundary**                                                                                                                   |
| Alerts          | Reason-code rates, integrity violations, cohort-threshold events | Alerts naming a participant or a credential holder                                                                                        |
| Dashboards      | Health and error rates                                           | Participation journeys; per-scope redemption breakdowns during voting                                                                     |
| Profiling / APM | Within one side, without payload capture                         | Payload capture anywhere on the flow; any APM inside WS-03                                                                                |

The trace boundary fails by default: modern instrumentation propagates
context automatically, and the implementation round must **break it
explicitly at `H-05`/`H-06`** and prove the break, rather than trusting
that nobody enabled propagation.
