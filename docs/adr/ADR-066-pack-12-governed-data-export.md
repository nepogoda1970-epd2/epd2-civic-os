# ADR-066: Export as a governed object, not a download

## Status

`proposed`

## Date

2026-07-29

## Context

`FIR-INV-007` requires search and export to use scoped access, reason
codes, export purpose, DLP checks, rate limits, approval where required
and audit evidence. `AGR-24` requires export to be governed by purpose
and record class.

Export is where data leaves the platform's trust boundary. Every control
in every earlier pack — PACK-09's retention and holds, PACK-10's
disclosure projections, PACK-11's sealed evidence and publication
renditions — applies to data inside the system. Export is the moment
those controls stop applying, which makes it the moment they matter most.

## Problem

1. Modelled as a download, export inherits whatever read permission the
   requester already has, and a read permission scoped to "may open one
   record" silently becomes "may take the whole class".
2. Without an object, there is nothing to expire, nothing to revoke,
   nothing to audit access against, and nothing to attach an obligation
   to.
3. Without field exclusion **before** generation, denied fields ride
   along in metadata, hidden columns and format internals.
4. Without a rule about regeneration, a stale approval authorises a fresh
   extraction against data that has since changed.

## Considered options

- **Option A — download with permission check.** Rejected on all four
  counts above.
- **Option B — export request with approval, but a plain file as the
  result.** Better, and still leaves an artifact with no expiry, no
  revocation, no access audit and no manifest binding.
- **Option C — export as a governed object with a full lifecycle,
  bound to an immutable manifest, expiring, revocable, access-audited,
  carrying explicit recipient obligations, and regenerated only against
  current authorization and policy.** **Chosen.**

## Decision

The lifecycle is `requested → dlp_assessment → disclosure_assessment →
approved|denied → artifact_generated → delivered → accessed* →
expired|revoked → destruction_attested`.

Five decisions inside it carry most of the weight:

- **Authority is not inherited.** Search permission is not export
  permission (`P12-EXP-004`); read permission is not bulk-export
  permission (`P12-EXP-005`); administrative privilege is not export
  authority (`P12-EXP-006`). Export authority derives from the
  `data_owner` for the record class in scope plus a distinct
  `export_approver`.
- **Denied fields are excluded before the artifact exists**
  (`P12-EXP-008`). Filtering at delivery or hiding at presentation is
  explicitly not equivalent.
- **Every artifact expires** (`P12-EXP-010`), every access is audited
  (`P12-EXP-011`), and revocation is possible before expiry
  (`P12-EXP-012`).
- **Revocation is not deletion** (`P12-EXP-013`). It withdraws
  authorization and blocks further platform-mediated access. It does not
  reach a copy the recipient already holds, and the system must say so
  rather than imply otherwise.
- **Each export is formed against current state** (`P12-EXP-019`). A
  prior approval never authorises a later regeneration.

Every item in `P12-VOTE-001` — ballot-level material and intermediate,
partial or non-certified tally material — is not exportable by any path,
purpose, role or emergency condition (`P12-EXP-003`). A final
**certified** result is not covered by that prohibition: it is released
through the authoritative voting and result-certification domain under
`P12-VOTE-004`, never through a PACK-12 export path, and PACK-12 may
audit only the fact that a governed publication occurred
(`P12-VOTE-005`).

Field permission is evaluated against the derived enforcement tier mapped
from the authoritative source classification, which governs wherever the
two differ (`P12-CLS-001`, `P12-CLS-002`). A legal hold is not authorization to export
(`P12-EXP-017`). Raw database access is a control failure, not an
alternative path (`P12-EXP-007`).

## Consequences

Easier: a complete answer to "what left, when, to whom, under what
purpose and obligation, and is it still valid"; retention and hold
obligations follow the data out; revocation and expiry become real
operations.

Harder: exporting anything is now a workflow with an approver and an
assessment, which is materially slower than a download button. Where an
organization needs routine bulk movement, the honest answer is a
pre-approved recurring export profile — still an object, still expiring,
still audited — not an exemption.

## Security impact

Addresses T-P12-12 (unauthorized bulk extraction), T-P12-13 (export of
hidden fields) and T-P12-17 (malicious or compromised recipient), and
makes T-P12-22 (direct database bypass) detectable by reconciliation.

Two residual risks are stated rather than mitigated: once delivered, data
is outside the trust boundary (T-P12-17), and revocation does not remove
an external copy (T-P12-18). `P12-DLP-004` forbids claiming otherwise.

## Data impact

Introduces seventeen governed objects, from `ExportRequest` through
`ExportDestructionAttestation`, all owned by PACK-12. `ExportArtifact` is
explicitly **not** an authoritative domain record (`P12-EXP-020`).

## Migration impact

None in this round.

## Reversibility

Reversible with cost. Once obligations and attestations exist for
delivered exports, reverting to ungoverned download would orphan them.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
