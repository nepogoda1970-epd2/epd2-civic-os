# ADR-058: Evidence provenance, chain of custody and sealed bundles

## Status

`proposed`

## Date

2026-07-28

## Context

PACK-09's `references.EvidenceRef` docstring already records what a later
admissibility decision needs from this context: "provenance, integrity,
custody, relevance decision and preserved version". PACK-11 owns the first
three and the last; the relevance decision belongs to the body deciding
the matter.

## Problem

1. Evidence modelled as a second kind of document would duplicate content,
   provenance and review state, creating two places where "what is this
   document?" is answered.
2. A citation that resolved "the document" at read time would silently
   follow the document forward - and evidence that follows the document
   forward is not evidence of anything.
3. A custody record that validates each event in isolation admits a forged
   intermediate link: every field individually valid, nobody having handed
   the item to that holder.
4. A citable set of evidence that could still change would make every
   prior citation ambiguous.

## Decision

**1. An `EvidenceRecord` is a governed *use* of an exact
`DocumentVersion`**, not a second object. It stores `document_id`,
`version_number` **and** `version_hash`, and adds only what makes that
version usable as evidence: matter, provenance, custody, integrity state.
The stored `version_hash` is the "preserved version" PACK-09 asked for
(Problem 2).

**2. Custody is verified as a chain, not per event.** Three conditions:
gap-free sequence starting at 1 with exactly one acquisition, first;
time never running backwards; and each event's `received_from_reference`
equal to the previous event's `holder_reference`. The third is the one
that catches Problem 3.

**3. Holders are opaque per-matter references.** The chain needs
*continuity* - was somebody always accountable? - not *identity*. Asking
for identity would put a cross-domain correlation key on every piece of
evidence (`FIR-INV-001`).

**4. Appending a custody event re-verifies the whole chain**, not only the
new link. A chain that was already broken must not accept new links and
look healthy at the tip.

**5. `EvidenceIntegrityState.UNVERIFIED` is a real state, distinct from
`INTACT`.** An item nobody has checked is an item nobody can say is
unaltered, and a bundle sealing over it would be sealing over an
assumption.

**6. A bundle is sealed, and sealing is what makes it citable.**
`bundle_digest` covers the bundle id and every item's ordinal, identity
and version hash - **including order**, because a numbered exhibit list is
not a set. Once sealed, adding an item raises (Problem 4). An empty bundle
cannot be sealed: "the empty set of evidence, sealed" is a citable object
that says nothing while looking authoritative.

**7. Assembly and sealing are one command**, unlike approval and
publication which are deliberately two. An *unsealed* bundle is not a
governed object at all - it is a working set - and letting one exist
between two commands would create a window in which a bundle is citable
but still mutable.

**8. There is no `CustodyAction.DESTROYED`.** Destruction of evidence is a
PACK-09-authorized disposition recorded on the document, not a custody
event this service can record on its own.

## Consequences

A PACK-09 case, a PACK-19 candidacy appeal or a PACK-10 audit engagement
can cite `epd2-bundle:<id>:<digest-prefix>` and mean exactly one set of
material. `EvidenceBundleProjection` carries the digest, the item count
and the per-item version references - and no provenance, no custody and no
matter substance, because a consumer needs to know *which* material, not
who held it.

## Alternatives considered

**Store evidence content separately from document content.** Rejected:
two content stores means two integrity stories.

**Let a bundle be re-sealed after amendment.** Rejected: an amended bundle
is a new bundle, and reusing the id would silently change what a prior
citation meant.

## Security impact

The continuity rule is the control against a fabricated custody history;
the seal is the control against a bundle that quietly grows or shrinks
after being cited.
