# ADR-097 — Six audit streams, never unified, and the auditor works from bundles rather than records

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
> **The bundle is now defined (`OD-P15-04`).** `EvidenceBundle` schema
> version **1**, scoped to exactly one voting context, with a **closed list
> of eight permitted sections** — context metadata; rule-set and
> configuration versions; aggregate eligibility totals; assertion issuance
> integrity totals; credential totals; integrity commitments and signature
> metadata; disclosure-control metadata; bundle provenance — and a
> normative prohibited-content list that includes **any per-participation
> record, any identifier, any pseudonym and any ballot data**.
>
> Validation has nine checks including count consistency and
> **reproducibility by a second auditor**; a failing bundle is **rejected,
> not repaired**. Export requires the Independent Auditor role plus a
> time-boxed PACK-12 grant, is **one context per bundle**, refuses any
> request for raw stream content, and is restricted before closure to the
> non-outcome sections under dual control. Suppression is complementary
> across cells and across time.
>
> The division this ADR drew — system-level integrity from bundles,
> individual-level integrity from participant-initiated dispute cases — is
> unchanged and is now operational rather than aspirational.

## Context

Audit is the most likely place for this architecture to fail, because audit
is the one domain where holding everything looks like a virtue. Every
argument for the pairing that ADR-093 forbids can be re-made in the
language of accountability: an auditor cannot verify what they cannot see;
an investigation needs the full picture; a regulator will ask for the
chain.

The arguments are not dishonest. They are just wrong about what an auditor
actually needs. An auditor needs to establish that the process was
followed, that the counts are consistent, that privileged acts were
authorized, and that the boundaries held. None of those requires the chain,
and a system that hands the auditor the chain has made the auditor the
correlation it was built to prevent.

There is also a practical failure mode that has nothing to do with
principle: the SIEM. Streams that are individually well-separated are
routinely shipped to one index because that is what observability platforms
do, and the join reappears in the place nobody reviews.

## Decision

**Six audit streams, separately keyed, separately authorized, separately
retained, and never unified. The Independent Auditor works from
privacy-preserving evidence bundles, not from raw streams.**

The streams: eligibility audit (`AS-01`), assertion audit (`AS-02`),
credential audit (`AS-03`), voting integrity audit (`AS-04`), independent
audit (`AS-05`), system integrity (`AS-06`).

1. **No role reads both `AS-01`/`AS-02` and `AS-03`.** That single row is
   the audit-side statement of the whole architecture, and an
   implementation that grants a role both has broken it whatever its
   documentation says.

2. **No unified table, index, view, query, report, export, warehouse, lake,
   SIEM or incident tool ingests two streams.** The prohibition binds
   infrastructure, not only application code.

3. **Every consequential act writes evidence to exactly one stream**, and
   no consequential act proceeds when its stream is unavailable
   (`FM-10`). No unlogged issuance, revocation or redemption, ever, under
   any load, with any flag.

4. **`AS-04` contains no identity in any field**, so it can be retained
   long and read widely without cost.

5. **The Independent Auditor's access is bundle-based** (`SD-10`). The
   bundle format (`OD-P15-04`) must deliver: verifiable counts without
   per-participation records; independently verifiable integrity of each
   stream; consistency between issuance and redemption **counts** rather
   than identities; evidence of every privileged act and every late
   revocation; evidence of every boundary-violation detection; no
   correlation key, no per-participation record, no ballot content; and
   reproducibility by a second auditor from the same inputs.

6. **The Dispute Reviewer's `AS-03` access is case-scoped status only**,
   obtainable against a reference the participant supplies, never by
   search. A reviewer who can search the credential stream can correlate.

7. **`AS-02` is reduced to counts after the dispute margin** — a privacy
   control rather than housekeeping. It is the last identity-side artifact
   that could, combined with a future compromise, narrow the field.

## Consequences

**Some questions become unanswerable by audit and are answered elsewhere.**
"Was this specific person's participation handled correctly?" is not a
bundle question. It is answered through the dispute path, where the
participant supplies their own references and consents to the examination
of their own case. That division — system-level integrity from bundles,
individual-level integrity from participant-initiated cases — is the honest
one, and it is stated rather than glossed.

**A regulator or court asking for the chain receives a true answer**: the
organization does not hold it and cannot produce it. That answer is only
available if it is true, which is why ADR-093 is structural.

**Observability tooling must be configured against its defaults.** Shipping
everything to one index is the normal operation of every platform in this
category, and the implementation round must demonstrate the separation in
the sink inventory, not only in the emitters.

**Incident response is constrained** and gains a defined escalation: an
incident that genuinely requires a cross-stream view is a context-level
event decided by governance, not a temporary grant.

## Alternatives rejected

**One audit store, six logical partitions, strong access control.**
Rejected: one store is one compromise, one backup and one export away from
a unified chain.

**Give the auditor everything and trust the auditor.** Rejected: the
auditor becomes the single point at which the whole architecture can be
undone, and independence is not the same as invulnerability.

**Unify streams after the context closes.** Rejected: the chain is as
dangerous a month later as it was during the vote, and archives outlive
the reasons they were made.
