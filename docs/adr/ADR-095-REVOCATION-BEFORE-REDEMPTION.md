# ADR-095 — Revocation exists only before redemption, is bounded by a cutoff, and can never be targeted at a person

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
> **The normative rule is now stated explicitly**, in the five sentences an
> implementation must be able to point at
> (`PACK-15-REVOCATION-MATRIX.md` §0): before issuance eligibility may be
> invalidated; after issuance and before redemption the credential may be
> revoked; **after redemption no person-level revocation and no ballot
> lookup is possible**; **no identity-side operation may locate, delete,
> replace or invalidate a specific ballot**; and **any later election-wide
> invalidation belongs to PACK-16 governance and must not create identity
> linkage**.
>
> One honest consequence of `OD-P15-07`: because issuance and redemption now
> occur in a single WS-03 visit, the _practical_ window of the
> after-issuance regime is usually seconds. The regime that does most of the
> work is therefore the **assertion** regime, before pickup — which is also
> the regime in which nothing is lost. The cutoff maxima are unchanged.

## Context

Every revocation request arrives with a good reason attached. A member's
membership lapsed. A credential was issued in error. A batch went out with
the wrong scope. Someone reports a device was stolen. Each is legitimate,
and each is also the shape of the request an attacker or a partisan
administrator would make.

The capability to revoke during a vote is the capability to remove
participation, and a system that can revoke can be compelled to. So
revocation has to exist — issuance faults are real — and it has to be
bounded in a way that makes selective disenfranchisement inexpressible
rather than merely forbidden.

There is a second problem specific to this architecture: after redemption,
revocation would require finding what the credential produced, which is
exactly the link ADR-093 makes structurally absent.

## Decision

**Revocation acts on the decision before an assertion exists, on the
assertion before it is presented, and on the credential before it is
redeemed and before the cutoff. After redemption, nothing is revocable.
Revocation is never targeted at a participant.**

1. **Three regimes, three artifacts.** Before assertion issuance, an
   eligibility change supersedes the decision and nothing is lost. Between
   assertion and presentation, the assertion may be revoked per the
   context's declared policy. Between issuance and redemption, the
   credential may be revoked on governed conditions. After redemption,
   **nothing**.

2. **`RevocationCutoff` is per-context governed configuration with a
   mandatory maximum**: never later than the opening of the voting window
   for `organizational_election` and `candidate_nomination`, and never
   later than the close of the issuance window for every other type. The
   maximum is enforced at configuration time, not by convention.

3. **Revocation inside the final window before the cutoff requires dual
   control plus Independent Auditor notification**, and is recorded in the
   integrity stream as an exceptional act with a per-context count
   available to the auditor. A context with many late revocations is a
   context whose result deserves scrutiny, and the evidence for that
   scrutiny must exist.

4. **Revocation cannot be targeted by participant, because the interface
   cannot express it.** The Credential Issuer does not know which
   credential belongs to whom. It can revoke a credential whose reference
   is presented, or a set defined by the fault — an issuance batch, a
   context, a window. **Selective disenfranchisement is not expressible.**

5. **Every revocation carries a registered reason code, an authority, a
   position relative to the cutoff, and evidence in the credential stream
   only.** Never free text as the reason, and never a participant
   identifier in any field.

6. **After redemption the remedy is at the level of the context** —
   suspension, annulment, re-run — each a governed decision under its own
   authority with its own announcement. Slower, more visible, more
   accountable than a quiet per-ballot correction, which is the point.

7. **Whether a source change may revoke an already-issued assertion is a
   per-context policy declared in advance**, not a global rule: revoking on
   source change keeps the electorate exact and hands an administrator a
   lever; not revoking accepts a small staleness window and removes the
   lever. The context declares its choice publicly before it opens.

## Consequences

**A genuine issuance fault found after the cutoff cannot be corrected for
the affected participant in that context.** That is the cost of the bound,
paid knowingly. The alternative — a late cutoff — buys correction at the
price of a live disenfranchisement capability, and the round judges that
price higher.

**Support cannot revoke on request without a reference.** A participant
reporting a lost credential must supply the reference they hold, or accept
that nothing can be revoked. This is stated plainly in the governed texts
rather than presented as a system limitation.

**Break-glass does not help.** No privileged path moves a credential out of
`redeemed`, and no grant spans both sides to find one.

**The audit gains a signal worth having**: late revocations are countable,
attributable and visible to an independent party, which makes revocation
abuse detectable after the fact even where it cannot be prevented in the
moment.

## Alternatives rejected

**Revocation throughout the voting window, with strong audit.** Rejected:
audit is after the fact, and a removed participation is not restored by a
finding.

**Post-redemption revocation "in exceptional circumstances".** Rejected:
the exception requires the person→ballot link, and an exception that
requires the link _is_ the link.

**A global cutoff for all context types.** Rejected: an assembly decision
and a contested office election have different fault profiles and different
abuse profiles; one number would be wrong for one of them.

**No revocation at all.** Rejected: issuance faults are real, and a system
that cannot correct a mis-issued batch before voting opens has traded a
small risk for a large one.
