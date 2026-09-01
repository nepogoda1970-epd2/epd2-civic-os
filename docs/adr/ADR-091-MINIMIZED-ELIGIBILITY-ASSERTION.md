# ADR-091 — The assertion carries a decision, not a person, and its permitted content is a closed list

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
> **Two closures tighten this ADR and reverse nothing.**
>
> **The pseudonym leaves the assertion entirely (`OD-P15-03`).** The
> pre-correction text permitted an ephemeral context-scoped pseudonym as a
> subject-continuity mechanism that could appear on the voting side. It
> cannot. The default is **no pseudonym**; where one exists it is permitted
> only for **context-local exactly-once enforcement**, it is identity-side
> only, and it is **never present in the assertion, the pickup, the
> credential, a redemption record, a ballot, a tally or an evidence
> bundle**. The closed twelve-field list is unchanged; the prohibited-content
> list gains the pseudonym and the precise timestamp.
>
> **The assertion is queued, not issued on demand (`OD-P15-02`).** Minting
> is followed by a governed queued release — batching, a minimum cohort of
> five, a uniform 30–300 s release delay, and a hard rule that a **cohort of
> one is never released immediately**. `IssuedAt` and `ExpiresAt` are
> coarsened (300 s by default, ≥ 3600 s for small electorates). Statuses
> become `minted` · `queued` · `released` · `picked_up` · `revoked` ·
> `expired` · `redeemed` · `replay_rejected`.

## Context

Something has to cross the trust boundary, or nobody can vote. Whatever
crosses becomes, permanently, the maximum amount the voting side can ever
know about a participant — because a field that crosses once will be
logged, cached, retried, error-reported and eventually retained somewhere
nobody remembers.

The pressure on this artifact is asymmetric. Every future requirement will
want one more field: a scope for reporting, a class for filtering, a
subject for support, a timestamp for reconciliation, a trace ID for
debugging. None of them individually looks like an identity leak. Together
they are one.

`FIR-INV-001` (no global user ID) and `FIR-INV-002` (identity/ballot
unlinkability) both fail at this artifact if it fails.

## Decision

**The eligibility assertion states that a decision was made, of what class,
for which context, valid until when — and nothing else. Its permitted
content is a closed list of twelve fields, and adding to it is a change to
this ADR.**

Permitted, in full:

```text
EligibilityAssertionId       VotingContextReference
EligibilityResult            EligibilityClass
OrganizationalScope          RequiredAssuranceSatisfied
IssuedAt                     ExpiresAt
Audience                     Purpose
Nonce                        Status
```

Binding rules:

1. **`EligibilityResult` carries only `approved`.** A denial is never
   asserted across the boundary. The voting side has no use for the fact
   that someone was refused, and telling it would give it a fact about a
   person.

2. **Prohibited content is prohibited by derivability, not by field name.**
   A hash of the member number is the member number. A per-member salt
   reused across contexts is a persistent subject identifier in a costume.
   A "stable anonymous ID for analytics" is a global user ID with a
   marketing department. The implementation-stage test must demonstrate
   that no field is a stable function of participant data across contexts,
   which a name scan alone cannot do.

3. **The nonce is random and non-derived**, one-time and context-scoped.
   Deriving it from participant data would recreate the assertion→credential
   map without storing it.

4. **The assertion is audience-, purpose- and context-bound, short-lived,
   replay-protected and revocable before use.** Each mismatch is a distinct
   registered reason code, because each implies a different next step.

5. **It is not a general identity token.** It authenticates nothing and
   authorizes nothing except the issuance of one credential in one context.
   Presenting it anywhere else is a refusal, never a partial success.

6. **Subject continuity, where a context genuinely needs it, uses an
   ephemeral context-scoped pseudonym** derived with a context-scoped
   secret held only on the identity side, never reusable or derivable
   across contexts, destroyed with its secret at the context's retention
   boundary, and never present in a credential, a redemption record, a
   ballot or a tally. Whether any context needs one at all is `OD-P15-03`,
   and the default is no.

7. **`IssuedAt` is coarsened** where the context's privacy profile requires
   it, because a precise issuance timestamp is a correlation key in a
   low-volume context.

## Consequences

**The voting side cannot personalize anything.** No greeting, no "welcome
back", no per-participant help, no support context. That is the intended
outcome and it constrains the Voting Client's design, which is why
FRONT-PACK inherits it as a requirement rather than discovering it.

**Every future field request is a decision, not a ticket.** The closed list
means that adding a field is an amendment to this ADR with its own
justification, which is slower and more visible than adding a property to a
payload — deliberately.

**Analytics on the voting side are structurally impossible**, not merely
prohibited. There is nothing to key them on.

**Support on the voting side works from references the holder supplies**,
which is what makes `credential.get_privacy_safe_status` safe and why it
has no search.

## Alternatives rejected

**A signed eligibility token carrying member attributes, "encrypted for the
issuer".** Rejected: the issuer decrypts it, so the issuer holds identity —
this is ADR-089's rejected alternative in a different wrapper.

**A stable per-member pseudonym across contexts, "so we can support
people".** Rejected: it is a global user ID, and it links every context a
person ever participated in.

**A subject-free assertion plus a side channel carrying the subject.**
Rejected: the side channel is the assertion, minus the review.

**An extensible claim set with a registry.** Rejected: extensibility is
how closed lists stop being closed, and a registry moves the decision from
an ADR to a configuration file.
