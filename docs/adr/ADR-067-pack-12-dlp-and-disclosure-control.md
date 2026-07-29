# ADR-067: DLP controls and statistical disclosure control foundation

## Status

`proposed`

## Date

2026-07-29

## Context

`FIR-INV-011` requires small samples and sensitive aggregates to use
disclosure controls; `AGR-20` is the architecture gap. `FIR-INV-007`
requires DLP checks on search and export. PACK-10 already implements a
narrow version of the same idea — `assert_no_small_cell_disclosure` and a
`MINIMUM_CELL_SIZE` floor in its publication projections — and is careful
to describe that floor as "a floor this code will not go below, not a
legal threshold it claims to know".

PACK-12 must generalise that from one domain's publications to every
export and release, without pretending to ship an analytics engine.

## Problem

1. A threshold is the control everyone implements and the control that is
   easiest to defeat: by differencing two queries, by reading a total, by
   combining neighbouring cohorts, or by issuing the same query as two
   people.
2. Individually compliant releases can be jointly re-identifying, and
   nothing in a per-request check sees that.
3. "May read the raw data" and "may publish a statistic derived from it"
   are different authorities that are routinely conflated.
4. DLP controls that produce a finding and then let the export proceed
   because the detector timed out are worse than no controls, because
   they generate the appearance of assurance.

## Considered options

- **Option A — cohort threshold only.** Rejected: `P12-SDC-005` exists
  precisely to forbid this.
- **Option B — full differential-privacy budget accounting.** Principled,
  and disproportionate for a specification round with no data plane
  (PACK-13) and no analytics engine. It would also fix a mechanism before
  the requirement is understood. Rejected for now, not forbidden later.
- **Option C — a contract-level foundation: eighteen named DLP controls,
  seven disclosure entities, mandatory assessment before decision,
  fail-closed detection, cumulative and differencing accounting stated as
  requirements, and an explicit statement that the production engine is
  PACK-13-dependent.** **Chosen.**

## Decision

Eighteen DLP controls MUST be available at policy level
(`P12-DLP-001`), from field suppression through destruction confirmation.

Four rules shape how they are used:

- The assessment completes **before** the decision and is evented
  (`P12-DLP-002`).
- The officer who assessed MUST NOT approve what they assessed
  (`P12-DLP-003`).
- Detection **fails closed**: an assessment the system could not complete
  blocks the export pending manual review (`P12-DLP-005`).
- No guarantee is claimed for watermarking, expiry or revocation
  (`P12-DLP-004`). These are deterrent, attribution and containment
  controls, and their limits must be stated wherever an operator sees
  them.

For disclosure control, seven entities are defined — `CohortPolicy`,
`DisclosureRule`, `DisclosureRiskAssessment`, `ReleaseHistoryReference`,
`SuppressionDecision`, `DisclosureExceptionRequest`,
`DisclosureExceptionDecision` — and eight rules, of which three are the
load-bearing ones: a threshold is never the only protection
(`P12-SDC-005`); suppressed values must not be recoverable through
totals, facets or neighbouring cohorts (`P12-SDC-007`); and cumulative
release across several individually-permissible exports must be assessed
(`P12-SDC-004`).

Privilege to access raw data does not imply authority to publish or
export it (`P12-SDC-002`). That separation is why
`disclosure_control_reviewer` and `data_owner` are an incompatible pair.

## Consequences

Easier: disclosure risk becomes an explicit, reviewable, appealable
decision with a named reviewer, rather than an implicit property of
whoever wrote the query.

Harder: cumulative accounting requires release history, which requires
storage and a retention decision of its own — and any bound on that
history creates a window in which cumulative risk is invisible.
`OD-P12-08` is open on exactly this, and the honest position is that the
window exists.

## Security impact

Addresses T-P12-14 (small-cohort re-identification), T-P12-15
(repeated-query differencing) and T-P12-16 (cumulative export
disclosure).

Residual risk stated: external auxiliary data can re-identify cohorts
that pass every internal rule. Thresholds and suppression reduce this;
they do not eliminate it, and no wording in the implementation may
suggest they do.

## Data impact

Introduces `DLPAssessment` and the seven disclosure entities. No existing
canonical entity changes. PACK-10's own `MINIMUM_CELL_SIZE` and
`assert_no_small_cell_disclosure` remain finance's; PACK-12 generalises
the pattern without taking over that implementation.

## Migration impact

None in this round.

## Reversibility

The control set is extensible and tunable. Removing fail-closed
behaviour, or reducing to threshold-only, would reintroduce the threats
this ADR exists for and should require its own ADR.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
