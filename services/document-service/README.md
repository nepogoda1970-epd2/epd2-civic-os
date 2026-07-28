# document-service

PACK-11's one wholly new service (ADR-055). Sole authoritative owner of the
governed-document and evidence bounded context that canon 19f.22 assigns to
PACK-11: **document bytes, authoritative versions, signatures, cryptographic
version chains, evidence content and the chain of custody.**

Implements `FIR-ROADMAP-001` and `FIR-INV-010` in full. Provides foundation
only for `FIR-DEC-001`, `FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`,
`FIR-PROG-002`, `FIR-INIT-021`, `FIR-PAY-003` and `FIR-DATA-003` — see
`docs/packs/PACK-11-FIR-TRACEABILITY.md`.

## Modules

Strict dependency order; each imports only from those above it.

| Module           | What it owns                                                                                                     |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| `exceptions`     | One class per registered reason code. No domain knowledge.                                                        |
| `domain`         | Value objects, identity minimisation, the content boundary, the governed taxonomies. No I/O, no clock, no storage. |
| `versions`       | Immutable `DocumentVersion` and the SHA-256 hash-linked chain (`FIR-INV-010`).                                    |
| `authorization`  | Eight roles, twenty-one actions, the symmetric incompatibility matrix, per-act separation of duties, access.       |
| `documents`      | The `GovernedDocument` aggregate, review requirements, approval, publication, supersession, revocation.           |
| `evidence`       | Evidence records, chains of custody, sealed bundles.                                                              |
| `determinations` | The governed signature and admissibility determinations, and reference resolution (ADR-053's four requirements).   |
| `references`     | The typed references this context exports and consumes.                                                           |
| `events`         | Twenty-five canonical event builders and the emission boundary.                                                    |
| `storage`        | Storage ports and in-memory adapters, including a content-addressed `ContentStore`. No delete method on any port.  |
| `projections`    | Restricted and public read models. Neither authoritative, neither carrying content.                                |
| `application`    | Commands and queries: one guard frame, one finish tail.                                                            |

## The three guarantees

**1. A stored version is never modified, and any modification is
detectable.** `version_hash = sha256(canonical_dumps(hashable_fields(v)) +
previous_version_hash)` — the same rule `audit-core` uses, so one
verification procedure covers both chains. Three independent defences:
`verify_version_chain` detects a rewrite, the store refuses to perform one,
and every command re-verifies before acting. This is tamper **evidence**,
not tamper resistance — see `docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.

**2. Content is held here and never travels.** This is the one context that
owns document bytes, which is exactly why no event payload, audit field or
projection may carry them. `domain.assert_emission_safe` runs at one
chokepoint over content, identity and voting-linkage keys.

**3. Nothing is asserted that no authority decided.** Signature status and
admissibility are *recorded* determinations bound to an exact version hash.
Absence is reported as an explicit `not_determined`, never inferred.

## Boundaries

This service imports `epd2-core` and `epd2-audit-core` and nothing else.
PACK-09 owns retention, legal hold and destruction authorization; PACK-08
owns organizational scope and authority; PACK-12 will own privileged access;
PACK-13 owns the production data plane; PACK-14 owns identity and keys. All
of them arrive as typed references in `references.py`, never as imports —
`tests/repository/test_service_boundaries.py` enforces it.

## What this service is not

No production persistence (every adapter is in-memory). No HTTP surface. No
signature verification. No legal or admissibility judgement. No identity:
there is no user, person or member identifier anywhere in the package.

**No claim of legal validity or operational readiness.** Whether a stored
document is a legally valid original, a qualified electronic signature, an
admissible exhibit or a compliant publication remains a human legal
judgement made outside this system, recorded here as a determination with
its own authority and reason code.
