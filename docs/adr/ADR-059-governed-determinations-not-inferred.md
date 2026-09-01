# ADR-059: Governed determinations: signature and admissibility are recorded, never inferred

## Status

`proposed`

## Date

2026-07-28

## Context

ADR-053 fixed four interface requirements PACK-10 would consume once
PACK-11 existed, and recorded that until all four exist, PACK-10 "records
the reference and the absence of the assertion - it does not simulate any
of the four with a local heuristic". Canon 19f.22 states the same rule
from the other side: "a reference to a document implies neither
authenticity, nor signature, nor legal validity, nor admissibility, nor
publishability; where an assertion unavailable to the domain is needed,
the action is refused closed."

## Problem

1. A signature check is cryptographic, PKI-dependent and
   jurisdiction-dependent; an admissibility determination is legal. A
   service that guessed either would produce an answer that _looks_
   authoritative to every consumer downstream - and consumers do not
   re-derive what an authoritative source already told them. The wrong
   answer would propagate exactly as far as the right one.
2. `None` as "no determination" invites a consumer to read it as "no".
3. A determination that travelled forward onto a later version would
   assert something about material it never examined.

## Decision

**1. Every determination is recorded, never computed.** No function in
`determinations` inspects content. Each determination carries the
authority that made it, the moment, the exact version hash examined and a
registered reason code.

**2. Absence is an explicit value, not `None`.**
`SignatureStatus.NOT_DETERMINED` and
`AdmissibilityStatus.NOT_DETERMINED` are what a consumer receives when
nothing has been determined, produced through the named functions
`absent_signature_status()` and `absent_admissibility_status()` so every
consumer-facing absence goes through one greppable place. A _recorded_
determination may not carry either value.

**3. Staleness is structural.** `determined_version_hash` is compared
against the version as stored; a mismatch raises
`DocumentDeterminationStaleError` rather than returning a slightly-wrong
answer. The consumer-facing query functions report a stale determination
as **absent**, because a determination made against a different state does
not apply, and reporting it as an answer would be worse than reporting
nothing.

**4. Four honest signature values, not two.** `NOT_SIGNED`,
`SIGNED_UNVERIFIED`, `SIGNED_VERIFIED`, `SIGNATURE_INVALID`.
`SIGNED_UNVERIFIED` is the correct answer for a scanned ink signature or a
certificate chain no configured trust anchor covers; collapsing it into
either neighbour would be this service inventing the verification it just
said it could not perform. `is_signed_original` is the single boolean a
consumer may read off the record and it is `True` only for
`SIGNED_VERIFIED`.

**5. Signature _form_ is recorded and never ranked.** Legal weight differs
sharply between a scanned handwritten signature and a qualified electronic
one, and ranking them is jurisdiction-dependent law.

**6. Admissibility is procedure-bound.** An admission in one procedure
says nothing about another; silently reusing it would extend a body's
decision beyond what that body decided. `ADMITTED_WITH_LIMITATION` exists
because the realistic outcome of a contested evidence question is rarely a
clean yes, and it _does_ permit reliance - returning `False` would be
safer-looking and would suppress material a competent body admitted.

**7. Determinations live on their own records, never on a reference.**
PACK-11 _may_ make these determinations - it is the pack canon names as
their owner - and it still does not put them on a pointer. A status on a
reference would be a cached answer that outlives the version, and for
admissibility also the procedure, it was true of.

**8. The fourth requirement is `PublicationRendition.citation_reference`**
(ADR-060), and the first is `application.resolve_document_reference`,
which returns existence and kind and reports a foreign scope exactly as it
reports a missing document.

## Consequences

ADR-053's four requirements are closed. PACK-10 can stop recording "the
reference and the absence of the assertion" and start asking - and will
still get a reason-coded refusal, not a guess, wherever no authority has
decided.

## Alternatives considered

**Verify signatures here.** Rejected: PACK-14 owns identity, keys and
external trust providers, and a verification implemented without its owner
would be a trust decision made in the wrong place.

**Return `None` for absence.** Rejected: see Problem 2.

**Let a determination cover a document rather than a version.** Rejected:
that is the drift Problem 3 describes.

## Security impact

The failure this forecloses is the most dangerous one available to a
document register: an unverified pointer masquerading as a governed fact.
Every path that would need such a fact and lacks it refuses with its own
code.
