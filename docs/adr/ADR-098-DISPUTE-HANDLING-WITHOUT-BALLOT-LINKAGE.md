# ADR-098 — Disputes are resolved without ballot content and without the ability to link a person to a ballot

**Status:** proposed
**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation (specification and ADR only)
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

## Context

A voting system without a real dispute path is not legitimate. Members will
be denied eligibility wrongly, placed in the wrong scope, refused a
credential by a false replay detection, or locked out by an outage. Each of
those is contestable, and a system that cannot hear the contest has decided
the question by silence.

But dispute handling is also the most natural back door in this
architecture. A dispute is precisely the situation in which someone has a
sympathetic reason to ask "what actually happened to this person's vote",
and where refusing looks like obstruction rather than design. If the
Dispute Reviewer can be given, for good reasons, the ability to link a
person to a ballot, then the ability exists — and once it exists, the
architecture's central claim is false for everyone, not only for
disputants.

`FIR-INV-002` does not have an exception for hard cases.

## Decision

**Every decision and refusal is contestable. No appeal requires or accepts
ballot content, and no dispute path grants anyone the ability to link a
person to a ballot — including by correlation, including under a grant,
including at the participant's own request.**

1. **Twelve registered dispute grounds**, each with its evidence, its
   reviewer, its remedy and its limit
   (`PACK-15-WORKFLOW-MATRIX.md` §3): eligibility denied; wrong
   organizational scope; stale membership data; credential not issued;
   credential lost; credential revoked; duplicate issuance rejected;
   handoff expired; false replay detection; system outage; accessibility
   failure; assisted-channel dispute.

2. **Every refusal names a reason code, the responsible body and the next
   possible step.** A refusal without a way forward is not a permissible
   text in this system.

3. **The dispute case schema cannot hold ballot content.** Not as a field,
   not as an attachment, not as free text the reviewer is expected to
   ignore. A participant who volunteers how they voted has that statement
   refused rather than filed.

4. **The Dispute Reviewer holds no correlation capability** (`SD-11`): no
   search over credentials, no cross-stream read, no grant spanning the
   boundary, and case records carrying timing _classes_ rather than precise
   timestamps — because case timing correlated with redemption timing is a
   link obtained by arithmetic rather than by access.

5. **Voting-side facts enter a dispute only through references the
   participant supplies.** `credential.get_privacy_safe_status` returns the
   same shape for an unknown reference as for a revoked one, so it cannot
   be used as an oracle.

6. **Where a remedy would require the link, the remedy is unavailable and
   the case is resolved at context level** — re-evaluation, scope
   correction, window extension, re-run, annulment — or recorded as an
   irreducible loss with reasons. The participant is told this plainly
   (`PACK-15-CONTENT-CATALOGUE-DE.md` §6, §11) rather than left to infer
   it from a stalled case.

7. **`ballot_correction` is not among the available remedies**, and its
   absence is specified rather than left as an omission.

8. **The organization's silence never closes a dispute.** A missed deadline
   on the organization's side does not resolve the case, following canon
   19d's `INV-10` discipline that silence is never approval.

## Consequences

**Some participants will have a real grievance with no individual remedy.**
Someone whose credential was redeemed by another person, or who lost access
after the revocation cutoff, cannot have their participation restored in
that context. The honest response is a context-level examination — was the
integrity stream showing replay or boundary violations? does the evidence
support suspending or re-running? — and an explicit statement of what
cannot be done and why. **The round refuses to trade the central guarantee
for one recovery**, and it says so to the person affected rather than
burying it.

**Reviewers must be trained against their instincts.** The reflex in a
dispute is to gather everything relevant. Here, gathering everything is the
violation, and the constraint has to be built into the tooling rather than
left to discipline.

**The dispute path becomes the individual-level complement to
bundle-based audit** (ADR-097): system integrity is verified without
participation records, individual handling is examined only with the
participant's own references and consent. Between them the coverage is
complete without the chain.

## Alternatives rejected

**Allow the reviewer a scoped, audited, time-boxed correlation grant.**
Rejected: the capability exists as soon as the grant shape exists, and a
capability that can be granted can be compelled.

**Allow the participant to waive unlinkability for their own case.**
Rejected for two reasons. The waiver is coercible — "prove you voted for
us and waive it" — and unlinkability is not only the participant's
property: the ballot secrecy of an election is a property of the election,
not a per-person setting.

**Resolve individual disputes after closure, when it is "safe".** Rejected:
the link does not become safe after closure, and the records that would
make it possible are exactly the ones this architecture declines to keep.
