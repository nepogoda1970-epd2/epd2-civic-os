# PACK-02 Threat Model

Scope: the five CLAUDE-PACK-02 services (`account-service`,
`identity-service`, `eligibility-service`, `credential-service`,
`audit-core`) as implemented in this repository — an in-memory reference
implementation with no production deployment, database, network transport,
or authentication layer (see `docs/review/KNOWN_LIMITATIONS.md`). This
document covers the ten threats pack section 14.1 requires at minimum. It
does not attempt a full platform threat model; later packs (Voting,
Delegation, Moderation, Governance) will need their own.

For each threat: asset, attacker, attack path, current mitigation,
residual risk, deferred control.

## 1. Insider with access to Identity Service

- **Asset**: `IdentityRecord` (verified identity data) and any downstream
  ability to infer who holds a given `ParticipationCredential`.
- **Attacker**: an operator or engineer with legitimate read/write access
  to Identity Service's own storage.
- **Attack path**: read `IdentityRecord` directly; there is no technical
  barrier stopping someone with that access from viewing every field
  Identity Service stores.
- **Current mitigation**: architectural, not access-control — Identity
  Service never receives or stores `ParticipationCredential` data, and no
  PACK-02 API lets Identity Service look up which credential resulted from
  a given `IdentityRecord` (the eligibility snapshot digest is one-way:
  Eligibility Service computes it from identity-derived claims, but
  Credential Service never reports the credential it issued back to
  Identity or Eligibility Service). So this insider sees identity data,
  but has no system-provided path from an `IdentityRecord` to a
  `ParticipationCredential`.
- **Residual risk**: an insider at this level can still see and export raw
  identity data itself (name-equivalent claims, verification outcome) —
  this reference implementation has no field-level encryption, no access
  audit on reads, and no data-minimization enforcement beyond "don't store
  more than needed" (pack section 5.4, not independently verified by an
  automated test in this pack).
- **Deferred control**: field-level access logging/audit on Identity
  Service reads, encryption at rest, and a real data-minimization review
  of what `IdentityRecord` actually needs to store, are all out of scope
  for PACK-02 (no production database exists yet) and are deferred to
  whichever future pack introduces real persistence.

## 2. Insider with access to Credential Service

- **Asset**: `ParticipationCredential` records and the ability to link a
  credential to a person.
- **Attacker**: an operator or engineer with legitimate access to
  Credential Service's storage.
- **Attack path**: read every stored `ParticipationCredential`.
- **Current mitigation**: `ParticipationCredential` structurally cannot
  carry an identity-linking field (`FORBIDDEN_FIELD_NAMES`, enforced by
  `test_ct00_08_identity_leakage.py` and Hypothesis in
  `test_property_based.py`; `additionalProperties: false` on the schema).
  So even full read access to Credential Service's own storage yields no
  identity linkage — the insider sees `scope_type`/`scope_id`,
  `credential_type`, timestamps, and `eligibility_snapshot_digest`, none
  of which resolve to a person without also compromising Eligibility or
  Identity Service and correlating by hand (see threat 4).
- **Residual risk**: `eligibility_snapshot_digest` is a stable value tied
  to one specific `EligibilityDecision`. If the same insider also gets
  access to Eligibility Service (a separate compromise, not covered by
  this mitigation alone), the digest becomes a join key back to whatever
  claims produced that decision. This is a deliberate, documented
  trade-off: the digest exists so a credential's authorization basis can
  be verified without carrying identity data on the credential itself; it
  is not designed to resist a _combined_ compromise of two services.
- **Deferred control**: a future pack could evaluate whether the digest
  should also be made unrecoverable from Eligibility Service's own storage
  after issuance (e.g. one-way hash discarding the decision), trading
  auditability for stronger compartmentalization — not attempted here to
  avoid weakening `EligibilityDecision`'s own audit requirements (pack
  section 7.2) without a dedicated ADR.

## 3. Log leakage

- **Asset**: identity claims, credential linkage, any data that should
  never appear in a log line.
- **Attacker**: anyone with read access to application or infrastructure
  logs (which are typically retained longer, replicated more widely, and
  access-controlled more loosely than primary data stores).
- **Attack path**: an exception message, a debug log statement, or a
  structured-log field accidentally includes raw identity claims or a
  credential-to-identity linkage.
- **Current mitigation**: pack section 13.1 forbids logging raw identity
  claims or including PII in exceptions; section 13.2 requires structured
  logs keyed on correlation id, service name, operation, and reason code,
  with no identity attributes. This implementation has no logging
  framework wired up yet (no service emits structured logs at all — see
  `docs/review/KNOWN_LIMITATIONS.md`), so the concrete mitigation today is
  narrower: every exception type in every service
  (`services/*/src/*/exceptions.py`) carries a `reason_code` class
  attribute and a message built from non-identity fields (ids, statuses,
  reason codes) — never a raw claim value — checked by inspection, not yet
  by an automated "no PII in exception text" test.
- **Residual risk**: without an actual structured-logging integration,
  there is no automated enforcement that a _future_ log statement added
  during PACK-03+ development won't include identity data — the current
  safety is "no logging exists yet to leak from," not a tested guardrail.
- **Deferred control**: a structured-logging library integration plus a
  static or runtime check that log call sites never receive an
  `IdentityRecord`/raw claim value is deferred to whichever pack first
  wires up real logging infrastructure.

## 4. Correlation through timestamps

- **Asset**: unlinkability between a `ParticipationCredential` and the
  `IdentityRecord`/`Account` that led to it.
- **Attacker**: anyone able to observe timestamps across two or more
  service's audit trails or event streams (e.g. someone with read access
  to Audit Core plus Identity Service's own event history).
- **Attack path**: identity verification completes at time T; shortly
  after, a credential is issued for the same civic space. If verification
  events are rare enough, timestamp proximity alone can narrow down which
  credential belongs to which identity, even with no shared identifier
  field.
- **Current mitigation**: none implemented. This reference implementation
  does not add jitter/batching to issuance timing, and `AuditEvent`
  timestamps (`occurred_at`, `recorded_at`) are real, per-action
  timestamps by design (INV-04 requires an accurate trace, which is in
  direct tension with timing obfuscation).
- **Residual risk**: real, and explicitly acknowledged rather than
  papered over. In a low-volume civic space (few verifications per day),
  timestamp correlation could plausibly narrow credential-holder identity
  even without any field-level leak. This is a known limitation of opaque
  credential references generally (pack section 6 explicitly does not
  claim anonymity beyond what's implemented).
- **Deferred control**: issuance-time batching/jitter, k-anonymity-style
  minimum batch sizes before a credential batch is released, or a
  formally-anonymous credential scheme (blind signatures, zero-knowledge)
  are all explicitly out of scope for PACK-02 (pack section 6, section
  13.1 forbids claiming anonymity not backed by code) and deferred to a
  dedicated future anonymity-focused pack, if the project decides to
  pursue one.

## 5. Repeated issuance

- **Asset**: eligibility integrity — one eligible person/account should not
  be able to obtain more participation credentials than the rule allows.
- **Attacker**: a credential holder (or a compromised Credential Service
  client) requesting `IssueParticipationCredential` multiple times for the
  same scope.
- **Attack path**: call the issuance command repeatedly, hoping either to
  get multiple valid credentials for the same eligibility basis, or to
  create audit-trail ambiguity about how many were actually issued.
- **Current mitigation**: `CredentialStore`'s storage-level dedup on
  `credential_id` plus content (same `credential_id` and same content =
  same stored record, no duplicate); a caller-supplied `event_id` on
  `issue_participation_credential` makes a retried identical request
  produce exactly one `AuditEvent` too (CT-00-04,
  `test_ct00_04_event_idempotency.py`). A conflicting resubmission (same
  `credential_id`, different content) is rejected fail-closed
  (`CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT`).
- **Residual risk**: this protects against _duplicate_ issuance requests
  for the same `credential_id`; it does not, by itself, enforce a business
  rule like "at most one active credential per (account, civic_space)" —
  that policy decision belongs to Eligibility Service's rule design
  (`EligibilityRule`), not to Credential Service's idempotency mechanism,
  and this pack does not implement or test such a cross-request rate
  limit.
- **Deferred control**: an explicit "at most N active credentials per
  scope per identity" enforcement, if desired, is a future eligibility-rule
  feature, not a PACK-02 deliverable.

## 6. Stolen credential

- **Asset**: the participation right a valid `ParticipationCredential`
  represents.
- **Attacker**: anyone who obtains a copy of a valid credential reference
  belonging to someone else (e.g. via a compromised client, a leaked
  request, or physical device access).
- **Attack path**: present the stolen credential reference to
  `ValidateParticipationCredential` (or, in a future participation
  system, to cast a vote or otherwise participate).
- **Current mitigation**: `RevokeParticipationCredential` exists and moves
  the credential to a terminal `REVOKED` status; once revoked, validation
  fails closed (`CREDENTIAL_REVOKED`) regardless of any other field's
  validity. Detection of theft (as opposed to response to a reported
  theft) is out of scope — this reference implementation is opaque
  bearer-reference credentials (pack section 6), which by design do not
  carry a binding to a specific holder's device or session.
- **Residual risk**: this is a bearer-credential model — anyone holding a
  valid, unrevoked credential reference can use it. There is no
  possession-proof (e.g. a signature challenge tied to the original
  holder) implemented; revocation is reactive (requires the theft to be
  reported/detected) not preventive.
- **Deferred control**: a possession-binding mechanism (e.g. a
  holder-specific secret the credential is bound to, checked at
  validation time) is a significant scope addition explicitly excluded
  from PACK-02 (section 3.2: no cryptographic voting, no production
  deployment) and deferred to whichever future pack designs the real
  participation-facing validation flow.

## 7. Replay

- **Asset**: the integrity of "this credential was validated/used exactly
  when and where it should have been."
- **Attacker**: anyone able to intercept and resend a prior valid
  validation request or event.
- **Attack path**: capture an earlier `ValidateParticipationCredential`
  call (or its result) and resend/replay it later, e.g. to make a revoked
  or expired credential appear to validate again, or to duplicate an
  audit entry.
- **Current mitigation**: `validate_participation_credential` is a
  pure read-side query evaluated against current state (`now`, injected
  via `Clock`) every time it is called — replaying the same request
  simply re-evaluates the same current state, which fail-closes correctly
  if the credential has since expired or been revoked (there is no cached
  "was valid at time X" result that a replay could exploit). On the audit
  side, Audit Core's `event_id`-keyed idempotency (threat 5, section 5 of
  `docs/architecture/audit-kernel.md`) means replaying an _issuance_ or
  _revocation_ request with the same `event_id` produces one audit entry,
  not a duplicated or ambiguous trail.
- **Residual risk**: there is no transport layer in PACK-02 (no HTTP
  server, no TLS, no request signing/nonce scheme — pack section 3.2
  excludes production deployment), so "replay" here is scoped to
  application-level idempotency, not network-level replay protection
  (e.g. a captured, re-sent HTTP request with a valid session token). That
  is a transport-layer concern for whichever future pack adds a real API
  server.
- **Deferred control**: request signing / nonces / TLS at the transport
  layer, once an actual HTTP server exists.

## 8. Revocation failure

- **Asset**: the guarantee that a revoked credential can no longer be used.
- **Attacker**: not necessarily malicious — this threat is about a system
  failure (a revocation that doesn't take effect), not an attacker action.
- **Attack path**: `RevokeParticipationCredential` is called, but a
  subsequent `ValidateParticipationCredential` call incorrectly reports
  the credential as still valid (e.g. due to a race, a stale cache, or a
  status-transition bug).
- **Current mitigation**: revocation is a synchronous state transition on
  the single authoritative in-memory store (no cache, no async
  propagation delay in this reference implementation); `validate_credential`
  checks `status` directly against the same store on every call.
  `test_state_transitions.py` exhaustively checks every
  `CredentialStatus` × `CredentialStatus` pair, confirming `REVOKED` is a
  terminal state no further transition can leave (an already-revoked
  credential cannot be un-revoked by any code path), and
  `test_ct00_10_rule_freeze.py`-adjacent fail-closed tests confirm an
  unknown/corrupted status is always treated as invalid (INV-10).
- **Residual risk**: this guarantee is only as strong as "one process, one
  in-memory store." A real deployment with multiple Credential Service
  instances and a shared or replicated datastore would need to solve
  read-after-write consistency for revocation — not a problem this
  reference implementation faces, but also not one it has solved.
- **Deferred control**: consistency guarantees for a real, possibly
  distributed datastore are deferred to whichever future pack replaces
  the in-memory adapter with a production store (pack section 4.1 already
  anticipates this: "interfaces should allow a separate store per service
  later without changing domain logic").

## 9. Event tampering

- **Asset**: the integrity of the `AuditEvent` history.
- **Attacker**: anyone with write access to Audit Core's underlying
  storage (not through the public API, which exposes no update/delete —
  see `docs/architecture/audit-kernel.md` section 2 — but through direct
  data manipulation, e.g. editing the process's memory or a future
  persisted store's files directly).
- **Attack path**: mutate a previously-appended `AuditEvent`'s payload
  field, or its `previous_event_hash` link, hoping the tampering goes
  unnoticed.
- **Current mitigation**: the global sequential hash chain
  (`docs/adr/ADR-003-append-only-audit-hash-chain.md`) makes both classes
  of tampering detectable by `verify_chain()`: a payload edit changes that
  record's own recomputed `event_hash` (no longer matching the stored
  value); a `previous_event_hash` edit breaks the link to the prior
  record. Both are directly tested
  (`test_verify_chain_detects_a_tampered_payload`,
  `test_verify_chain_detects_a_broken_previous_hash_link`).
- **Residual risk**: as ADR-003 states explicitly, this is **not**
  cryptographically signed and **not** distributed. An attacker with full
  write access to the store can, in principle, regenerate every
  subsequent hash after their edit and produce an internally-consistent
  _alternate_ chain that `verify_chain()` would accept — the mechanism
  detects an edit left in place without also regenerating everything
  downstream of it; it does not make a full, self-consistent rewrite
  impossible. This is the honest limit of an in-memory, single-process,
  unsigned hash chain, and is why the pack itself (section 9.2) forbids
  presenting this as "qualified electronic evidence."
- **Deferred control**: periodic external anchoring of the chain head
  (e.g. publishing `event_hash` to an independent, append-only channel
  outside the operator's write access), cryptographic signing per record,
  or a real distributed ledger, are all deferred — explicitly not claimed
  here (pack section 13.1 forbids claiming guarantees the code doesn't
  provide).

## 10. Accidental schema regression introducing PII

- **Asset**: the guarantee that `ParticipationCredential` (and its events,
  and its audit payload) never gains an identity field, even by accident
  in a future change.
- **Attacker**: not malicious — a well-intentioned future code change that
  adds a field to `ParticipationCredential` (e.g. "just for debugging," or
  because a new feature seems to need a quick reference back to the
  account) without realizing it reintroduces exactly the linkage INV-01
  forbids.
- **Attack path**: a future PR adds `account_id` (or similar) directly to
  `ParticipationCredential`, its event payload, or `AuditEvent`'s
  credential-related payload, and it passes ordinary code review because
  the reviewer doesn't independently re-derive the full list of forbidden
  fields.
- **Current mitigation**: multiple independent, automated layers, not
  reliance on review discipline alone:
  - `tests/contract/test_ct00_08_identity_leakage.py` checks the
    dataclass, the event payloads, the validation result, the OpenAPI
    response shape, and the audit payload all at once, against the actual
    `FORBIDDEN_FIELD_NAMES` list.
  - `tests/contract/test_property_based.py` uses Hypothesis to check
    arbitrary subsets of `FORBIDDEN_FIELD_NAMES`, not just the specific
    names anticipated when the test was written — a new forbidden-looking
    field added to the list itself is automatically covered without
    editing the test.
  - `contracts/schemas/participation-credential.schema.json` sets
    `additionalProperties: false`, so a schema-valid credential JSON
    payload cannot carry an extra field even if the Python dataclass
    somehow gained one and serialization forgot to strip it.
  - `tests/contract/test_ct00_09_vote_linkability.py` checks the
    weaker but broader structural property (no shared `*_id` field name
    with `Account`/`IdentityRecord`), which would catch a differently-named
    but still identity-shaped field the exact-name list might miss.
- **Residual risk**: all of the above are name-based/structural checks.
  A field that encodes identity-derived information under an innocuous
  name (e.g. a `metadata` blob containing an encoded identity value) would
  not be caught by any of these tests — content-based leakage detection is
  not implemented.
- **Deferred control**: a content-based check (e.g. verifying no
  credential field's _value_ round-trips to any known `IdentityRecord`/
  `Account` field value across the whole test fixture set) is a more
  expensive, fixture-coupled test not implemented in PACK-02; deferred as
  a recommended addition for a future pack if a richer, encoded-field
  attack surface emerges.

## Summary table

| #   | Threat                                       | Mitigated                                     | Residual risk level (qualitative)                                                    |
| --- | -------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | Insider — Identity Service                   | Partially (architectural, not access-control) | Medium — raw identity data still fully visible to this insider                       |
| 2   | Insider — Credential Service                 | Yes, for single-service compromise            | Low-Medium — combined compromise with Eligibility Service reopens linkage via digest |
| 3   | Log leakage                                  | Partially (no logging exists yet)             | Medium — no automated guardrail against future log statements                        |
| 4   | Correlation through timestamps               | No                                            | Medium-High — acknowledged, not mitigated                                            |
| 5   | Repeated issuance                            | Yes (idempotency + conflict)                  | Low — no cross-request rate-limit rule implemented                                   |
| 6   | Stolen credential                            | Partially (revocation exists, reactive)       | Medium — bearer model, no possession binding                                         |
| 7   | Replay                                       | Yes at application layer                      | Medium — no transport layer exists yet to protect                                    |
| 8   | Revocation failure                           | Yes (single-process, synchronous)             | Low — untested at distributed-store scale                                            |
| 9   | Event tampering                              | Yes (detects in-place edits)                  | Medium — full self-consistent rewrite not preventable                                |
| 10  | Accidental schema regression introducing PII | Yes (name/structure-based)                    | Low-Medium — content-based encoding not covered                                      |

No residual risk in this table is claimed as fully resolved; each is
carried forward explicitly rather than implied-fixed. See
`docs/review/OPEN_QUESTIONS.md` and `docs/review/KNOWN_LIMITATIONS.md` for
how these interact with other known gaps in the repository.
