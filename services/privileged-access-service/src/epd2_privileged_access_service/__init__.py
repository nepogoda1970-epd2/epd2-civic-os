"""Privileged Access Service — PACK-12's one wholly new service (ADR-061).

Sole authoritative owner of three logical bounded contexts that share one
package boundary, one command frame and one audit path (`OD-P12-04`):

1. **Privileged administration** — the privileged-access grant lifecycle
   (`PrivilegedAccessGrant`), the nine operational assignment roles, the
   separation-of-duties matrix, the governed break-glass workflow and
   tamper-evident privileged sessions.
2. **Authorization-aware search** — index policy, query admission,
   result-time re-resolution of source authorization, suppression bands
   and the authorization-context-keyed result cache.
3. **Governed export, DLP and disclosure control** — the export
   lifecycle, the closed recipient taxonomy, the DLP assessment and
   transforms, and the statistical-disclosure-control rule families.

They are one package because they are one control surface: a privileged
grant that could be reasoned about without the search and export it
authorises would be a control in name only. They are *not* one module —
each has its own aggregates, its own roles and its own refusals.

Module map, in dependency order — each module imports only from those
above it:

- `exceptions` — one class per registered reason code, no domain knowledge.
- `domain` — value objects, purpose, effective dating, the prohibited
  payload keys, the request context. No I/O, no clock, no storage.
- `policy` — the versioned numeric policy and its hard ceilings.
- `classification` — the canonical source→tier classification mapping.
- `roles` — institutional roles consumed, operational assignments
  introduced, the pairwise incompatibility matrix and the authorization
  port.
- `access` — the grant aggregate and its lifecycle.
- `breakglass` — the separate emergency workflow.
- `sessions` — privileged sessions and the sealed, hash-chained evidence.
- `search` — index policy, query admission and execution.
- `export` — the export lifecycle, recipients, manifests and artifacts.
- `dlp` — controls, findings, assessment and transforms.
- `disclosure` — cohort policy, the four rule families, release history.
- `references` — the typed references this context exports and consumes.
- `events` — the forty-four canonical event builders.
- `storage` — storage ports and in-memory reference adapters. No delete
  method exists on any port.
- `application` — the commands: scope, authority, separation of duties,
  purpose, idempotency, optimistic concurrency, reason-coded refusals,
  canonical events and audit appends.

**No bypass exists, by construction.** There is no feature flag,
environment switch, deployment mode, privileged grant or emergency path
that disables any invariant, audit append or separation check in this
package (`roles.NO_BYPASS_NOTE`, `P12-BG-009`, FIR-INV-006). Emergency
access is a separate, dual-controlled, notified, expiring, independently
reviewed workflow that *adds* obligations — never one that removes them.

**No second anything.** This package creates no parallel architecture, no
second audit framework, no second evidence system, no second reason-code
registry and no second master register. It appends to PACK-02's audit
chain and holds no mutating control over it (`OD-P12-06`), seals session
evidence into PACK-11's evidence bundles (`P12-SES-005`), observes
PACK-09's retention and legal-hold decisions without making them, and
registers its reason codes in `contracts/reason-codes/pack-12.yml`
alongside every earlier pack's.

**No universal console and no all-domain role.** No role in the
separation matrix, in any combination and under any emergency condition,
reaches ballot content or mutates an audit record — the two all-`N` rows
in the capability matrix are the load-bearing ones (FIR-INV-014,
FIR-INV-002).

**What this service is not.** It carries no production data plane: every
adapter in `storage` is in-memory. It implements no production database,
no real event bus, no external IAM or identity provider, no MFA, no HSM
or PKI, no production search engine, no production DLP provider, no
voting, no incident-response platform and no external recipient portal.
It mints no identity and defines no institutional office.

**Tamper-evident, not tamper-resistant.** The session hash chain makes
alteration *detectable*; nothing here prevents it. Watermarking marks a
copy; it does not stop one being made
(`dlp.WATERMARK_LIMITATION_NOTE`). Export revocation withdraws
authorization and blocks further platform-mediated access; it does not
retrieve a delivered copy (`P12-EXP-013`). A destruction attestation is a
recipient's statement, not a verified fact.

**No claim of legal validity or operational readiness.** Nothing here
establishes that a privileged act was lawful, that an export satisfied a
legal basis, that a disclosure control met a statistical authority's
standard, or that any of it is admissible. Each remains a human legal
judgement made outside this system, recorded here as a determination with
its own authority and reason code. See
`docs/handover/PACK-12-KNOWN-LIMITATIONS.md`.
"""

from __future__ import annotations

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

#: The contexts this service implements, and the status that
#: implementation has. `reference_implementation` is the truthful value:
#: the governed workflows, the separation model and the refusal surface
#: are real and tested; the production data plane is not.
PRIVILEGED_ACCESS_CONTEXT_IMPLEMENTATION_STATUS = "reference_implementation"

#: The FIR entries this package fully implements. Every other entry the
#: PACK-12 FIR Coverage Matrix touches is foundation-only or a recorded
#: dependency, and is deliberately absent here — a foundation is not an
#: implementation.
IMPLEMENTED_FIR_ENTRIES: tuple[str, ...] = ("FIR-ROADMAP-002",)

__all__ = [
    "CANON_VERSION",
    "IMPLEMENTED_FIR_ENTRIES",
    "PRIVILEGED_ACCESS_CONTEXT_IMPLEMENTATION_STATUS",
    "REPOSITORY_VERSION",
]
