# ADR-057: Immutable document versions and cryptographically linked history

## Status

`proposed`

## Date

2026-07-28

## Context

`FIR-INV-010` states the requirement this ADR implements: "Historical
versions must never be rewritten. Documents must preserve cryptographically
linked history." Canon 19f.22 assigns "cryptographic version chains" to
PACK-11 by name. `audit-core` (ADR-003) already runs a sequential
SHA-256 hash chain over audit events.

## Problem

1. Immutability enforced only by convention is immutability that a
   migration script removes.
2. A per-record hash with no linkage detects a rewritten record and not a
   *removed* one - and deleting an inconvenient version is the more likely
   attack.
3. A chain over records alone does not notice content swapped behind an
   untouched record; a digest check over content alone does not notice a
   record rewritten together with its digest.
4. If the chain covered lifecycle state, every legitimate approval would
   break the chain for every later version - so breaks would be routine
   and a real one would go unnoticed.

## Decision

**1. The same chaining rule as `audit-core`.**

```text
version_hash = sha256(canonical_dumps(hashable_fields(version)) + previous_version_hash)
```

`canonical_dumps` from `epd2_core.canonical_json`; `GENESIS_PREVIOUS_HASH`
is sixty-four zeros, the same constant `audit-core` uses. Two chaining
schemes in one repository is one too many: an auditor who has verified one
can verify the other without learning a second convention.

**2. `hashable_fields` covers identity, scope, kind, sensitivity, the
title reference, the complete content descriptor, the complete provenance,
the recording moment, the recording authority in full (including
`actor_reference`) and the correction linkage.** Attribution is inside the
hash because "who recorded this" is the half of FIR-INV-010 a
content-only hash would leave rewritable.

**3. `state` and `history` are deliberately excluded** - see Problem 4.
A governed transition is a fact *about* a version, not a change *to* it,
and `with_state` therefore does not recompute the hash.

**4. The content digest is inside the hashed fields, and content is
verified separately.** `verify_document_integrity` runs both, because
neither catches both attacks (Problem 3).

**5. Three independent defences, not one.**
   - `versions.verify_version_chain` *detects* a rewrite after the fact;
   - `storage.InMemoryDocumentVersionStore.append` *refuses to perform*
     one: no replacement of a stored version, no version number that is
     not head+1, no `previous_version_hash` that is not the head's hash;
   - `storage.record_state_change` compares `hashable_fields` rather than
     only the stored hash, so a caller that altered a covered field
     without resealing cannot slip past a hash-only comparison.

**6. Every command re-verifies the chain before acting.** More expensive
than checking at read time, and the point: a governed act recorded against
a history that no longer verifies adds a trustworthy-looking row to an
untrustworthy history.

**7. Revision is version N+1, never a reopened version N.**
`returned_for_revision` is terminal for that version. That is what makes
"historical versions are never rewritten" true of the workflow and not
only of the storage layer.

**8. Verification returns a result rather than raising.** An operator
sweeping a whole store needs every finding, not the first one.
`assert_version_chain_intact` is the raising form commands use.

## Consequences

The chain is **tamper evidence, not tamper resistance**, and this ADR says
so rather than letting the phrase "cryptographically linked" carry more
weight than it earns. An actor with write access to the entire store could
rewrite every version and recompute every hash. Countersigning by an
external party and anchoring the head hash outside this repository are the
controls that would close that gap; neither is in this round, and
`docs/handover/PACK-11-KNOWN-LIMITATIONS.md` records it as a named gap
rather than a footnote.

Rewriting version 2 *and* resealing it does not escape detection: version
3 still links to the old hash, so the break moves one step later. Only
rewriting the entire tail escapes, which is exactly the property claimed
above.

## Alternatives considered

**Merkle tree over versions.** Rejected for this round: it buys efficient
inclusion proofs, which nothing in this repository consumes yet, at the
cost of a second, unfamiliar verification procedure.

**Sign each version.** Rejected as premature: PACK-14 owns key material
and identity, and a signing scheme chosen here would be chosen without
its owner.

**Hash the state too.** Rejected: see Problem 4.

## Security impact

Detection, not prevention, is the honest claim. The value is that a
rewritten or removed version cannot be made to look untouched to anybody
who runs `verify_document_integrity` - and that running it is a cheap,
scriptable sweep rather than a forensic exercise.
