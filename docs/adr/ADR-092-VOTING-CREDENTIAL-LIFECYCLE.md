# ADR-092 — The voting credential is opaque, single-use, context-bound, and its redeemed state is absorbing

**Status:** proposed
**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation (specification and ADR only)
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-31).** The decision below is unchanged
> and is not reversed. The open questions it left are now closed; the
> closures are recorded in `docs/packs/PACK-15/PACK-15-SPECIFICATION.md`
> §32 and summarised for this ADR in the note that follows. The
> authoritative register is now
> `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`, carried at
> the canonical path, which preserves every prior entry and adds
> `FIR-OSS-001` … `FIR-OSS-006`.
>
> **Delivery is closed (`OD-P15-07`), and it makes this ADR stricter.**
> Credential material is delivered **only inside the isolated WS-03
> boundary**, in volatile page memory, and is never displayed, copied,
> downloaded, printed, mailed, texted, pushed, cached, logged or made
> visible to any operator. Ten delivery channels are prohibited by name.
> The ordinary workspace transmits only the one-time handoff artifact.
>
> **A consequence, stated rather than discovered:** issuance and redemption
> occur in **one WS-03 visit**, so `CredentialIssuanceWindow` governs when a
> participant may *enter* the voting origin, not a period during which they
> hold a credential outside it. **Advance issuance across separate visits is
> out of scope for this round** and is deferred to PACK-16 with
> `OD-P15-05`, because holding a credential between visits requires a
> holder-side custody decision that WS-03's isolation forbids.
>
> Minting also applies a **randomized 5–30 s delay** (`OD-P15-02`), shown as
> a waiting state with no countdown and no queue position.

## Context

Canon 10.1 already defines `ParticipationCredential` with a structural
prohibition on identity fields, enforced in the baseline by a
forbidden-field set and a repository-wide identity-leakage test suite.
Canon 15.3 already requires `VoteEnvelope.credential_proof` to reference a
credential rather than an account.

What canon does not define — because no round has needed it — is the
credential's **lifecycle**: how it is requested, issued exactly once,
revoked, expired, redeemed, and what happens when the same request arrives
twice through three different failure paths. That lifecycle is where
exactly-once participation is won or lost, and it has to work while neither
side of the boundary knows what the other knows.

## Decision

**The voting credential is opaque, single-use, short-lived, context- and
audience-bound, non-replayable, identity-free, and once redeemed it never
leaves the redeemed state.**

Lifecycle:

```text
requested → eligible → issued → redeemed
                    ↘ revoked   ↘ expired
                    ↘ cancelled ↘ replay_rejected
                    ↘ disputed
```

Binding rules:

1. **`redeemed` is absorbing.** No administrative act, no break-glass
   grant, no incident response and no privileged path moves a credential
   out of it, because doing so would imply the ability to find and act on
   what it produced.

2. **Issuance is atomic with spending the assertion nonce.** A crash
   leaves the nonce unspent and the retry idempotent; it never leaves a
   half-issued credential.

3. **Idempotency is keyed on the assertion nonce**, voting side only, with
   a bounded cache window. **The cache must not become a durable
   assertion→credential map** — the window is explicit, tested, and short.

4. **Exactly-once is achieved by a split**: one assertion per participation
   unit (identity side), one credential per nonce (voting side), one
   redemption per credential, one ballot per redemption (PACK-16).

5. **No silent reissue.** A reissue is a governed request with its own
   decision, dual control, evidence on both streams, and a
   revoke-then-reissue sequence — never issue-then-hope.

6. **`VotingCredentialId` is never used as, derived into, or stored beside
   a ballot identifier.** PACK-16 must not extend `credential_proof` into
   a retained mapping, and this round records that as an obligation rather
   than assuming it.

7. **Credential type follows context type.** A nomination credential is not
   a consultation credential, and cross-context presentation is a refusal
   with a distinct code.

8. **Non-transferability is claimed only as far as it is enforceable.** A
   person can hand their credential to someone else and nothing here stops
   them. Single use, context binding, audience binding, short lifetime and
   the absence of post-redemption bearer semantics are what is enforced.
   Coercion resistance is a protocol property and belongs to PACK-16.

## Consequences

**A lost credential after redemption is unrecoverable.** This is the
sharpest consequence of the architecture and it is stated to participants
plainly (`PACK-15-CONTENT-CATALOGUE-DE.md` §5) rather than presented as a
system limitation to be worked around later. Recovering it would require
the person→credential→ballot chain, and the round refuses that trade.

**The "delivery uncertain" case has a defined resolution** — holder-only
retrieval for the rest of the issuance window, then governed
revoke-then-reissue before the cutoff, then an honest loss. Three steps,
each with evidence, none requiring a link.

**Operators cannot help by looking things up.** Every voting-side support
interaction starts from a reference the holder supplies. This is
unfamiliar, and it is the property that makes `SD-03` real.

**The design is deliberately replaceable.** The spent-nonce set is the
weakest structure that gives exactly-once, chosen so that PACK-16 can
substitute a cryptographic construction (`OD-P15-05`) without redesigning
the boundary.

## Alternatives rejected

**A credential bound to the participant "for their protection".** Rejected:
the binding is the link, and the protection it offers is smaller than the
attribution it creates.

**A reusable session after redemption.** Rejected: PACK-14 issued no
session for WS-03 deliberately, and adding one here would undo ADR-088.

**Reissue by minting a fresh credential without revoking the old one.**
Rejected: two live credentials for one participation unit is a double vote
waiting for a race.

**Allowing an administrator to revoke after redemption "in exceptional
cases".** Rejected: the exception requires the link, and an exception that
requires the link is the link.
