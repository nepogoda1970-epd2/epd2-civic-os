"""Document Service — PACK-11's one wholly new service (ADR-055).

Sole authoritative owner of the governed-document and evidence bounded
context: the document register (`GovernedDocument`), immutable
cryptographically linked versions (`DocumentVersion`, `verify_version_chain`),
document content (`ContentStore` — this is the one context canon 19f.22
makes the owner of document bytes), controlled review and approval
(`ReviewRecord`, `ApprovalRecord`), the publication lifecycle
(`PublicationAuthorization`, `PublicationRendition`), correction,
supersession and revocation (`SupersessionRecord`, `RevocationRecord`),
governed determinations (`SignatureDetermination`,
`AdmissibilityDetermination`), evidence with provenance and chain of
custody (`EvidenceRecord`, `CustodyEvent`, `EvidenceBundle`), retention
and legal-hold bindings, and the restricted and public projections.

Module map, in dependency order — each module imports only from those
above it:

- `exceptions` — one class per registered reason code, no domain knowledge.
- `domain` — value objects, identity minimisation, the content boundary,
  the governed taxonomies. No I/O, no clock, no storage.
- `versions` — immutable versions and the hash-linked chain (FIR-INV-010).
- `authorization` — roles, actions, the incompatibility matrix,
  separation-of-duties and access assertions.
- `documents` — the `GovernedDocument` aggregate, review requirements,
  approval, publication, supersession, revocation.
- `evidence` — evidence records, chain of custody, sealed bundles.
- `determinations` — the governed signature and admissibility
  determinations, and reference resolution (ADR-053's four consumer
  requirements).
- `references` — the typed references this context exports and consumes.
- `events` — the twenty-five canonical event builders.
- `storage` — storage ports and in-memory reference adapters. No delete
  method exists on any port.
- `projections` — derived, versioned, non-authoritative read models,
  restricted and public.
- `application` — the commands and queries: scope, authority, separation
  of duties, idempotency, optimistic concurrency, reason-coded refusals,
  canonical events and audit appends.

**Domain-neutral by design.** The taxonomy in `domain.DocumentKind` names
meeting minutes, decision records, candidacy documents, initiative
attachments, legal and expert opinions, finance evidence, official
correspondence, appeal records, SEPA mandate evidence and public
transparency documents — and this package implements **none** of those
domains. It gives them one governed shape, so that the later packages the
master register schedules do not each grow their own divergent document
model with its own divergent version history.

**What this service is not.** It carries no production data plane: every
adapter in `storage` is in-memory, and PACK-13 owns the durable one. It
decides no retention schedule and no legal hold (PACK-09 owns both; this
service records their answers and fails closed without them). It
implements no privileged, JIT or break-glass access (PACK-12). It verifies
no signature and decides no admissibility — it *records* determinations
made by an authority, and reports their absence as absence. It holds no
identity: there is no user, person or member identifier anywhere in this
package.

**No claim of legal validity or operational readiness.** The version chain
is tamper *evidence*, not tamper resistance, and nothing here establishes
that a stored document is a legally valid original, a qualified electronic
signature, an admissible exhibit or a compliant publication. Each of those
remains a human legal judgement made outside this system, recorded here as
a determination with its own authority and reason code. See
`docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.
"""

from __future__ import annotations

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

#: The context this service implements, and the status that implementation
#: has. `reference_implementation` is the truthful value: the governed
#: workflow, the integrity model and the consumer interface are real and
#: tested, and the production data plane is not.
DOCUMENT_CONTEXT_IMPLEMENTATION_STATUS = "reference_implementation"

#: The FIR entries this package fully implements. Foundation-only entries
#: are listed in `docs/packs/PACK-11-FIR-TRACEABILITY.md` and are
#: deliberately absent here — a foundation is not an implementation.
IMPLEMENTED_FIR_ENTRIES: tuple[str, ...] = ("FIR-ROADMAP-001", "FIR-INV-010")

__all__ = [
    "CANON_VERSION",
    "DOCUMENT_CONTEXT_IMPLEMENTATION_STATUS",
    "IMPLEMENTED_FIR_ENTRIES",
    "REPOSITORY_VERSION",
]
