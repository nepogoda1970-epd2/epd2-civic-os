# PACK-11 — Governed Documents & Evidence: specification

> Target repository version `0.11.0`. Canon stays `0.8.0`.
> `FIR-ROADMAP-001`, `FIR-INV-010`. ADR-055 through ADR-060.

## 1. Why this document is normative

PACK-11 is the first implementation round in this repository with **no
canon section of its own**. Canon 0.8.0 gives finance section 19f and
organization section 19e; the governed-document and evidence context has
only ownership statements in 19f.22 and 19f.23. `CANON_VERSION` stays
`0.8.0` in this round, so the normative sources are:

- `FIR-ROADMAP-001` and `FIR-INV-010` from
  `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`;
- canon 19f.22 and 19f.23's ownership and isolation statements;
- ADR-053's four PACK-11 interface requirements;
- the register's hard invariants `FIR-INV-001`, `FIR-INV-002`,
  `FIR-INV-003`, `FIR-INV-006`, `FIR-INV-013`, `FIR-INV-014`,
  `FIR-INV-015`;
- ADR-055 through ADR-060 and this document.

A later canon round may give this context a section. Until then this
document states the model.

## 2. Objective

A governed document and evidence domain providing organization-scoped
document ownership; immutable document versions; cryptographically linked
version history; typed document and evidence references; controlled review
and approval; a publication lifecycle; restricted and public projections;
correction, supersession and revocation; legal hold; retention metadata;
evidence bundles; provenance; complete audit history; and scoped
authorization with separation of duties.

## 3. Domain neutrality

`domain.DocumentKind` names twenty-two governed kinds — meeting minutes,
decision records, agendas, motion texts, candidacy documents, nomination
packages, initiative attachments, programme provisions, legal opinions,
expert opinions, AI analysis records, finance evidence, official
correspondence, official notice proofs, appeal records, hearing records,
SEPA mandate evidence, public transparency documents, policy documents,
statute documents, audit working papers and a residual kind.

**This package implements none of those domains.** It gives them one
governed shape, so the later packages the master register schedules do not
each grow their own divergent document model with its own divergent version
history. That is the entire value proposition of the round.

The taxonomy is a **closed enum on this side** of the boundary and an
**open string on the consumer side**: a consumer that cannot yet name its
kind can still hold a reference, while a document actually stored here
always has a resolved, governed kind.

## 4. The version model

See `docs/architecture/document-version-integrity.md` and ADR-057.

Lifecycle of one version:

```text
draft ──→ in_review ──→ approved ──→ published ──→ superseded
  │           │            │            │              │
  │           └→ returned_for_revision  │              │
  │                        │            │              │
  └────────────────────────┴────────────┴──────────────┴──→ revoked
```

`returned_for_revision` is terminal for that version; the revision is
version N+1. Every pair is listed explicitly in
`_ALLOWED_VERSION_TRANSITIONS` — a rule expressed as "anything except…"
silently admits every state somebody adds later.

Lifecycle of the document as a whole: `active ⇄ closed → disposed`.

## 5. Review and approval

`ReviewRequirement` names which review **kinds** a version must carry
before approval, held on the document rather than resolved at approval
time — so a later change to the defaults cannot retroactively invalidate
documents already approved under the old ones.

Counting reviews would let two general reviews stand in for a missing legal
one, which is exactly what `FIR-PROG-002` exists to prevent. Defaults:
editorial for everything; substantive for official records; legal for legal
and expert opinions; data protection for public transparency documents.

A blocking finding is resolved only by a later, explicitly-linked,
non-blocking review. Approval refuses while one is open.

## 6. Publication

Approval and publication are two acts, two authorities, two records and two
transitions (ADR-060). A publication authorization requires a
`disclosure_obligation_reference`: this service does not decide what must
be published.

`PublicationRendition.citation_reference` is ADR-053's fourth interface
requirement: `epd2-doc:<document>:v<n>:r<rendition>`.

## 7. Correction, supersession, revocation

- **Correction** — a new version carrying `corrects_version_number` and a
  reason code. The corrected version is untouched.
- **Supersession** — an explicit record, never inferred from "highest
  number". A version can be recorded and never approved, so the highest
  number is not always the current statement.
- **Revocation** — removes _effect_. The version, its content and its place
  in the chain are untouched, and a previously published version remains
  publicly representable as a tombstone.

## 8. Retention and legal hold

PACK-09 owns the schedule, the hold decision and the destruction
authorization. PACK-11 stores the bindings and refuses without them. An
`indeterminate` hold fails closed with its own code, distinct from a known
active hold — collapsing the two would let "we could not reach PACK-09" be
read later as "there was a hold".

## 9. Evidence

See ADR-058. An `EvidenceRecord` is a governed _use_ of an exact version,
preserving `version_hash`. Custody is verified as a continuous chain. A
bundle is sealed, order-sensitive and citable; an unsealed bundle is not a
governed object.

## 10. Determinations

See ADR-059. Signature status and admissibility are recorded, never
computed. Absence is an explicit `not_determined`. Staleness is structural.

## 11. Authorization

Eight roles, twenty-one actions, a symmetric incompatibility matrix
re-checked at the moment of the act, per-act separation of duties, access
profiles as ceilings, read-time independence verification, and no
break-glass (ADR-056).

## 12. Events

Twenty-five types in five aggregate groups. Four are publicly projectable,
via a closed allow-list. `event_version` is `1.0`; the canon section-21
envelope is used unchanged.

## 13. What this round does not do

No production data plane, no HTTP surface, no external anchor for the chain
head, no signature verification, no legal judgement, no identity, no
privileged access. Each has a named owner: PACK-12, PACK-13, PACK-14, or a
human legal process outside this system.
