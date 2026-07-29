# PACK-12 — Known Limitations

Companion to `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`.

This document exists so that nobody has to infer a limit from an absence.
Everything below is a deliberate boundary of the PACK-12 implementation
candidate at repository version `0.12.0`, not a defect and not an
oversight. Where a later package owns the missing piece, it is named.

---

## 1. Verification

**External CI has not passed.** The build environment for this round
cannot reach PyPI or the npm registry (`403 Forbidden` on both), so
`uv sync --all-groups --frozen` and `npm ci` could not run, and therefore
`make verify` could not run in full. What did run, and what did not, is
enumerated exactly in section 5 of the implementation-candidate report.

This is the single reason this round ships as a **candidate** rather than
as a reference implementation, and the reason `FIR-ROADMAP-002` moves only
to `scheduled`. No amount of green local output substitutes for the
external arbiter.

---

## 2. Integrity is tamper *evidence*, not tamper resistance

`sessions.SealedPrivilegedSession` chains each sealed session to the
previous head with `sha256(canonical_dumps(payload) + previous_hash)` —
the same rule PACK-02's audit chain and PACK-11's document versions use,
so one verification procedure covers all three.

What this buys: any alteration of a sealed payload, and any reordering or
removal in the chain, becomes **detectable**.

What it does not buy: prevention. An actor with write access to the store
can rewrite the whole chain consistently. Detecting *that* requires an
anchor outside the system — a countersignature, a published head, an
independent witness — and PACK-12 has none. This is the same boundary
`OD-20` records for PACK-11's document chain, and it is why nothing in
this package uses the phrase "tamper-resistant".

**Owner of the fix:** a future round that introduces external anchoring.

---

## 3. Every adapter is in-memory

`storage.py` ships storage *ports* and in-memory reference adapters.
There is no production database, no durable event bus, and no persistence
of any kind that survives a process.

`storage.EventSink` publishes into a list. A real bus, its ordering
guarantees and its delivery semantics are PACK-13's.

**Owner:** PACK-13 (production data plane and contract evolution).

---

## 4. No identity, no authentication, no MFA, no HSM

`roles.AuthorizationPort` is how this service learns about authority, and
it is a *port*. PACK-12 mints no identity, issues no session token,
verifies no credential and holds no secret. `AuthorityReference` carries
an assignment id and a role code; who the human behind it is, is
deliberately not knowable from anywhere in this package (`FIR-INV-001`).

Multi-factor authentication, an external IdP and hardware-backed key
custody are all named in the PACK-12 specification as *out of scope* and
are not partially implemented here — a partial MFA is worse than none,
because it looks like a control.

**Owner:** PACK-14 (identity and external gateway), PACK-17 (security
operations).

---

## 5. Out-of-band notification is a contract, not a transport

`breakglass.NotificationPort` is the seam through which a break-glass
activation notifies oversight. `storage.ReferenceNotificationAdapter`
implements it well enough to test the *governed* behaviour — that a
suppressed notification is refused, and that an undelivered one escalates
and still raises — and it sends nothing anywhere.

The real out-of-band channel (email, SMS, pager, an incident platform)
and its own independence from the activator's control are PACK-17's.

**Owner:** PACK-17.

---

## 6. Search is an enforcement core, not a search engine

`search.py` implements admission, result-time re-resolution of source
authorization, tier-based suppression, snippet policy, facet policy and
cache partitioning. It does not implement an index. `InMemorySearchIndexStore`
holds records in a list and `execute_query` scans them.

A production search engine introduces its own problems this package does
not address: index freshness under load, partial results, relevance
ranking as an information channel, and the operational question of who
can read the index files directly.

**Owner:** PACK-13.

---

## 7. DLP is a control model, not a detector

`dlp.py` defines eighteen controls, a named fail-closed subset, the volume
and frequency rules, and the transform functions. It performs **no
content inspection**: `DlpControl.FORBIDDEN_DATA_DETECTION` is a control
whose *outcome* is recorded, not a classifier that finds forbidden data.
A `DlpFinding` carries a `detail_reference`, never the matched value —
quoting the match would put the very data the control exists to protect
into the assessment record.

**Owner:** a production DLP provider, integrated in a later round.

---

## 8. The cumulative-release model is bounded, and that is a limit

`OD-P12-08` asked for a cumulative-disclosure model. The answer
implemented is bounded: a policy window
(`cumulative_release_window`), a policy limit
(`cumulative_release_limit`), and a `ReleaseHistory` that must be
**available** — `assert_available()` fails closed when it is not.

An unbounded "every release ever, against every other" model was
considered and rejected as unimplementable at any real scale, and an
unimplementable model quietly becomes no model at all. The consequence is
honest and worth stating: a disclosure attack assembled from releases
spread beyond the window will not be caught by this rule.

**Owner:** the operator, through policy; and a later round if a stronger
model becomes tractable.

---

## 9. Pseudonymisation is call-scoped

`dlp.apply_transforms` gives a stable pseudonym per distinct value
*within one call*. It is not a cryptographic pseudonymisation scheme,
carries no key, and does not produce a pseudonym that is stable across
exports. Linking two exports of the same population by pseudonym is
therefore not possible — which is usually what you want — but neither is
legitimate re-identification by an authorised recipient.

**Owner:** a later round, if a keyed scheme is required.

---

## 10. No frontend

The PACK-12 specification names twelve administrative surfaces. **None is
implemented.** No frontend workspace, component, route or view model was
added this round.

That was a deliberate choice given the verification limit in section 1:
the frontend toolchain (`node_modules`, `vitest`, `tsc`, Playwright,
eslint) could not be installed or run in this environment, and adding
unverifiable frontend code to a repository whose frontend pipeline is
currently green would risk breaking it with no way to know. The PACK-12
task's own instruction permits exactly this: where no suitable frontend
integration point exists, implement contracts and state the limitation.

**Owner:** FRONT-PACK, and `FIR-FRONT-001`/`FIR-FRONT-003` record the
obligation.

---

## 11. No legal or regulatory claim

Nothing in this package establishes that:

- a privileged act was lawful;
- an export satisfied a legal basis under any data-protection regime;
- a disclosure control met any statistical authority's standard;
- a session record is admissible as evidence anywhere;
- a recipient obligation is enforceable.

Each remains a human legal judgement made outside this system. Where such
a judgement exists, this package records it as a determination with its
own authority and reason code — and records its absence as absence.

---

## 12. Reason codes are registered, not adjudicated

`contracts/reason-codes/pack-12.yml` guarantees that every refusal this
service raises carries a registered code with a stated meaning. It does
not guarantee that the code is the *right* one for a given situation in
any legal or regulatory sense, and the registry is not a mapping to any
external taxonomy.
