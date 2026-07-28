# PACK-11 — open decisions

Decisions this round deliberately did **not** make, each with what it is
waiting on. Recorded here rather than resolved silently, so a later round
finds the question rather than an accidental answer.

## OD-20 — External anchoring of the version-chain head

`FIR-INV-010` is satisfied as tamper *evidence*. Tamper *resistance* needs
the chain head anchored somewhere this repository does not control, or
countersigned by a party that is not the store operator.

**Not decided here** because the choice (a timestamping authority, a
notary, a transparency log, a periodic published digest) is a trust
decision with legal and operational consequences, and PACK-14 owns external
trust providers. `GovernedDocument.head_version_hash` exists partly so the
anchor has one obvious place to be recorded.

**Waiting on:** PACK-14, plus a governance decision about which external
party is acceptable.

## OD-21 — Whether PACK-09 and PACK-10 should consume PACK-11's real references

ADR-053's four requirements are now closed, so PACK-10 *could* stop
recording "the reference and the absence of the assertion". This round does
not change PACK-10.

**Not decided here** because it is PACK-10's decision, under a PACK-10 ADR,
at a time PACK-10 chooses — and because the moment those placeholders
become imports, two service manifests acquire a dependency they do not
declare today.

**Waiting on:** a PACK-10 or PACK-09 round.

## OD-22 — The document-content encryption model

Content is stored as bytes in a content-addressed store. Encryption at rest,
per-document keys, and key rotation are unaddressed.

**Not decided here** because PACK-13 owns the production data plane and
PACK-14 owns key material, and a scheme chosen now would be chosen without
either owner.

**Waiting on:** PACK-13 and PACK-14.

## OD-23 — Rendition generation

`issue_publication_rendition` takes rendition bytes from the caller. It does
not generate a PDF from a source document, and it does not verify that a
rendition faithfully represents its source.

**Not decided here** because faithful rendition is a rendering-pipeline
problem with an accessibility dimension (`FIR-INV-012`), and asserting
faithfulness without verifying it would be exactly the kind of unearned
assertion ADR-059 forbids elsewhere.

**Waiting on:** a frontend/publication round.

## OD-24 — Whether an approved version may ever be un-approved

Currently: no. An approval is create-once, and the paths away from
`approved` are `published`, `superseded` and `revoked`. A mistaken approval
is therefore handled by revocation plus a new version.

**Not decided here** whether a narrower "approval withdrawn before
publication" transition is worth adding. It would be convenient and it
would also create a state in which a version was approved and then was not,
with no record of the interval unless the transition is itself governed.

**Waiting on:** operational experience.

## OD-25 — Retention of the *content* after disposition

`authorize_disposition` records the PACK-09 authorization and closes the
document. It destroys nothing: PACK-13 owns the data plane, and executing a
disposal against an in-memory reference store would be a durability claim
this round has no basis for.

**Not decided here:** what a disposition should leave behind — a tombstone
version, a destruction-evidence record mirroring PACK-09's
`DestructionEvidence`, or nothing but the document record.

**Waiting on:** PACK-13, and a PACK-09 alignment round.

## OD-26 — Cross-organization document sharing

A document belongs to exactly one organizational scope. A Land-level body
that must read a Bund-level document has no path here except a PACK-08
cross-scope authority, which this service does not interpret.

**Not decided here** because PACK-08 owns the six cross-scope access modes,
and re-implementing any of them in this service would create a second,
divergent answer to "may this scope read that scope's material?".

**Waiting on:** a PACK-08 alignment round.
