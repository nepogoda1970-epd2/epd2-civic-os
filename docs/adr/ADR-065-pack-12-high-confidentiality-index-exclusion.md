# ADR-065: Default exclusion of highly confidential domains from general search

## Status

`proposed`

## Date

2026-07-29

## Context

ADR-064 makes search authorization-aware. That is necessary and
not sufficient. Some material is dangerous to index even when the
authorization check is correct, because the index concentrates it, the
operational surface around an index is wide (backups, replicas, debug
tooling, vendor support), and a single misconfiguration reaches
everything at once.

The register is unambiguous about the strongest case: `FIR-INV-002`
requires identity/ballot unlinkability, `FIR-INV-003` requires Voting
Client isolation, and `FIR-INV-005` forbids intermediate tally. PACK-10
and PACK-11 both handled the same boundary structurally rather than by
permission — neither defines any reference type that can point at voting
material, so there is nothing to misconfigure.

## Problem

1. An authorization-correct index of whistleblower submissions is still a
   single object whose compromise exposes every reporter.
2. "Restricted, but indexed with the right ACL" is a sentence that has
   preceded a large share of real-world disclosure incidents.
3. Without a default-exclusion list, each domain must remember to opt
   out, and the failure mode of opt-out is silence.

## Considered options

- **Option A — index everything, rely on ACLs.** Rejected: makes
  correctness of the whole index a precondition for the safety of the
  most sensitive material in the platform.
- **Option B — per-domain opt-in to indexing, with no central list.**
  Better, but leaves no single place to check the answer, and no rule for
  a domain that has not yet thought about it.
- **Option C — a default-exclusion list of eleven categories, stated as a
  floor that a stricter domain rule always overrides, with four
  categories excluded absolutely.** **Chosen.**

## Decision

`P12-HCD-001` excludes eleven categories from the general search index by
default: voting secrets and ballot content; whistleblower reporter
identity and protected submissions; cryptographic credentials and secret
material; highly sensitive legal and disciplinary case content; medical
or comparable special-category data; protected citizen correspondence;
raw privileged-session secrets; sealed evidence; legally restricted
finance and compliance material; and anything an authoritative
record-class policy marks restricted.

Exclusion is expressed against the derived enforcement tier that
`PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` section 2 maps from the
authoritative source classification; the source classification governs
wherever the two differ (`P12-CLS-001`, `P12-CLS-002`).

Four are absolute, with no configuration path and no emergency
exception:

- ballot-level material and intermediate, partial or non-certified tally
  material (`P12-VOTE-001`, `P12-HCD-003`, and `P12-BG-010` closes the
  emergency path). A final **certified** result is deliberately not in
  this list: it is released by the authoritative voting and
  result-certification domain under `P12-VOTE-004`, and PACK-12 neither
  forbids that release nor performs it;
- cryptographic credentials and key material (`P12-HCD-004`);
- whistleblower reporter identity and protected submissions, excluded
  from ordinary, administrative, HR and management access alike
  (`P12-HCD-002`);
- raw privileged-session secrets, which `P12-SES-002` prevents from
  existing in the first place.

`P12-HCD-005` fixes the layering: this list is a floor. Where a domain is
stricter, the domain governs. PACK-12 MUST NOT be read as permitting
anything a domain forbids merely because this list did not name it.

The strongest form of the ballot exclusion is structural, following
PACK-10 and PACK-11: PACK-12 defines no reference type that can point at
voting material, so the exclusion does not depend on a configuration
being right.

## Consequences

Easier: the most sensitive material is out of the highest-aggregation
object by default; a reviewer can check the list rather than audit every
domain's configuration.

Harder: legitimate work on excluded domains cannot use general search and
needs a domain surface instead. That is a real cost in operator
convenience, and the alternative is worse.

## Security impact

Addresses T-P12-21 (privileged access to ballot-level and intermediate-tally material) and materially
reduces the impact of T-P12-09 and T-P12-10 by removing the most damaging
material from the index they operate on.

## Data impact

No new entity; this ADR constrains `IndexPolicy` from
ADR-064.

## Migration impact

None in this round.

## Reversibility

The four absolute exclusions are intended to be irreversible. The other
seven are policy and may be tightened; loosening any of them should
require its own ADR and a named legal basis.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
