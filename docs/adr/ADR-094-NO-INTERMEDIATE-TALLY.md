# ADR-094 — Nothing may pre-empt the official tally, including operational telemetry

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
> **The thresholds are now numbers (`OD-P15-02`, `OD-P15-04`).**
> `disclosure_min_cell` is **5**, is a floor rather than a default, and is
> never lowered per context — small electorates raise it. Suppression is
> **complementary**, applied across cells **and across bundles over time**,
> because two evidence bundles and arithmetic are a differencing attack
> (`T-P15-39`).
>
> **Pre-closure evidence export is restricted** to the non-outcome-bearing
> sections of the bundle (context metadata, versions, commitments,
> disclosure metadata, provenance) and requires **dual control** — an
> auditor's legitimate need to verify *process* before closure does not
> extend to *totals*. Queue depth, cohort size and release-batch size join
> the prohibited-disclosure list wherever they could narrow a cohort.

## Context

`FIR-INV-005` says no intermediate tally or partial distribution may be
shown before closure. It reads as a rule about results pages, and the
implementations that violate it almost never build a results page.

They build a dashboard. Credentials issued per hour. Redemptions by Kreis.
Queue depth by organizational scope. A quorum progress bar for the assembly
chair. A Grafana panel someone added during load testing and nobody
removed. Each of these is operationally reasonable, none is called a tally,
and in a body of eleven eligible members a per-Kreis redemption count
during an open window is an outcome projection with a dashboard's
credibility.

The asymmetry is what makes this matter. An operator who can see the shape
of participation an hour before anyone else has something worth having in a
political organization, and something worth acquiring. The prohibition is
not secrecy for its own sake; it removes an asymmetry that would otherwise
be valuable.

## Decision

**Before the official tally, no surface — page, endpoint, event, metric,
log, export, alert or dashboard — may disclose an outcome or permit one to
be inferred. The prohibition covers telemetry, and telemetry is where it
will be violated.**

1. **Prohibited absolutely**: vote distributions, option or candidate
   totals, partial results by any dimension, ballot content, turnout,
   quorum progress, person-level participation state, participation
   correlated with identity, live redemption counts broken down by scope or
   fine-grained time, leaderboards, forecasts, projections, pre-closure
   exports of voting-side data, pre-closure auditor access to
   outcome-bearing data, and sampling or "spot checks" of ballots.

2. **Permitted, conditionally**: service health, queue depth, issuance
   failure counts, replay-attempt counts, error rates by reason code,
   latency percentiles, integrity-violation counts, late-revocation counts
   — and aggregate credential-processing counts **only** where they pass
   disclosure control.

3. **Every permitted signal must satisfy**: a minimum aggregation
   threshold with suppression (not rounding) below it; no participant
   dimension in any label; no scope dimension below the threshold; PACK-12's
   disclosure-control mechanism reused unchanged; and delay where the
   context's privacy profile requires it.

4. **Disclosure control applies to the set of published signals, not to
   each one alone.** Three individually permitted metrics can jointly
   reveal a suppressed cell, and composition is the rule that gets missed.

5. **A request that would disclose outcome-bearing data before closure is
   refused and recorded** as `IntermediateTallyAttemptRejected`. The
   refusal is evidence, because the attempt is worth knowing about.

6. **`VotingWindowClosed` carries no counts.** It is the event most likely
   to acquire a turnout field during implementation, and it must not.

7. **A context's dashboards are reviewed before activation**, by
   governance, as part of activating the context — not as an operations
   task afterwards.

## Consequences

**Operations lose visibility they would normally expect.** "How is turnout
looking?" has no answer during a vote, for anyone, including the people
running it. Capacity decisions are made from health and queue signals
rather than participation signals. This is a real cost.

**The assembly quorum case needs a governed answer.** An assembly chair may
legitimately need to know whether a quorum is met. That need is met by a
disclosure-controlled, thresholded, governance-approved signal defined per
context — not by a live counter — and where the body is small enough that
even a thresholded signal is revealing, the answer is procedural rather
than technical.

**The permitted list is short and closed**, which means new telemetry is a
decision rather than a configuration change.

## Alternatives rejected

**Allow internal dashboards, restrict publication.** Rejected: the asymmetry
is created by anyone seeing it, and "internal" is a wide set during an
election.

**Allow turnout but not results.** Rejected: turnout in a small,
politically coherent body predicts the result, which is why campaigns want
it.

**Allow live counts with a delay.** Rejected: a delay shorter than the
window is still an early signal, and a delay longer than the window is the
official result. What is actually needed — a delay past the inference
window — is what the privacy profile specifies for the few signals that
survive.
