# ADR-088 — The voting handoff carries no identity, and PACK-14 defines only its boundary

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-30).** The decision below is unchanged.
> The open questions it left are now closed; the closures are recorded in
> `docs/packs/PACK-14/PACK-14-SPECIFICATION.md` §29 and summarised per ADR
> in the note that follows.
>
> **The artifact is named and its properties fixed (OD-P14-06).** The
> outbound boundary object is the **`VotingHandoffArtifact`**: **opaque**,
> **single-use**, **short-lived**, **audience-bound**, **purpose-bound**,
> **voting-context-bound**, carrying **no account, person-record,
> membership, member-number, communication-persona or contact identifier**,
> with **no reusable bearer semantics** and **no reverse identity
> resolution** — neither from the artifact nor from the issuance and
> redemption records, jointly or separately.
>
> **Still outside PACK-14 (OD-P14-10):** the eligibility assertion, voting
> credential issuance, ballot casting, verification and tally. How an
> eligibility statement reaches the voting domain with no identity attached
> is PACK-15's problem, taken with PACK-15's own threat model.

## Context

`FIR-INV-002` (identity/ballot unlinkability) and `FIR-INV-003` (Voting
Client isolation) are the guarantees on which the entire system's claim to
be a voting platform rests. FRONT-00 declares WS-03 as a separate origin
with no shared cookies, storage, identity session, analytics, fingerprinting
or telemetry, and no persistent member identifier. PACK-13 refused to
choose the voting domain's broker topics, connection topology, service
names, credential topology or transport, on the grounds that settling a
security architecture from outside the pack that owns it is itself a
vulnerability.

PACK-14 inherits that discipline. It is the round that issues sessions, so
it must say how a member gets _from_ an authenticated workspace _to_ the
Voting Client — and it must say no more than that.

## Decision

**PACK-14 defines the handoff boundary. It does not define the voting
credential protocol, and it implements nothing in the voting domain.**

The handoff artifact is:

1. **One-time.** A second presentation is a refusal with a distinct reason
   code (`VOTING_HANDOFF_ALREADY_USED`), never a silent re-issue.
2. **Purpose-scoped.** It authorises entry to one voting context and
   nothing else.
3. **Short-lived**, with an explicit expiry that is checked at redemption.
4. **Audience-restricted** to the Voting Client origin, and **not a bearer
   token** usable elsewhere.
5. **Carrying no identity.** It contains no `account_id`, no
   `person_record_id`, no `membership_id`, no `member_number`, no
   `communication_persona_id`, no email, no phone, no device identifier and
   no provider subject claim.
6. **Not reversible.** Nothing in the artifact or its issuance record may
   allow the Voting Client, or anyone holding voting-side data, to resolve
   backwards to the account that obtained it.

Structural absences, following PACK-13's pattern of guarantees that are
absences rather than checks: WS-03 shares no cookie, no localStorage, no
sessionStorage, no IndexedDB, no cache, no service worker, no identity
session, no analytics, no telemetry and no fingerprinting with any other
workspace, and holds no persistent member identifier.

**Out of scope for PACK-14, explicitly:** the voting credential itself,
eligibility determination, ballot casting, verification, tally, and any
cryptographic voting protocol. Those are PACK-15 and PACK-16, taken with
PACK-15's own threat model.

## Consequences

The handoff must be usable by someone whose session is in WS-02 and whose
voting takes place in WS-03 without any shared state, which constrains the
frontend: the Mobile App profile already requires opening WS-03 in the
system browser rather than a WebView, and this ADR is why.

An eligibility statement must reach the voting domain without an identity
attached. PACK-14 does not solve that — it records it as the dependency it
is, and leaves the solution to the pack that owns the threat model.
