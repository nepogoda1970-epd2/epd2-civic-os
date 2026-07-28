# ADR-055: PACK-11 document-service decomposition and reason-code registry

## Status

`proposed`

## Date

2026-07-28

## Context

`FIR-ROADMAP-001` schedules PACK-11 (Governed Documents & Evidence) at
repository version `0.11.0`, and canon 19f.22 already names PACK-11 as
the owner of "document bytes, authoritative versions, signatures,
cryptographic version chains, evidence content and the chain of custody".
Three earlier packs have been holding placeholders against that
ownership: PACK-09's `references.DocumentRef`, `EvidenceRef`,
`MinutesRef` and `NoticeProofPackageRef`; PACK-10's
`references.DocumentReference` and `domain.EvidenceReference`; and
ADR-053's four named interface requirements.

Unlike every previous implementation round, this one has **no canon
section of its own**. Canon 0.8.0 gives finance section 19f, compliance
its Framework 0.8.1 counterpart, and organization section 19e; the
document/evidence context has ownership statements scattered through
19f.22 and 19f.23 and nothing more. `CANON_VERSION` stays `0.8.0` in this
round by instruction, so the normative sources this implementation is
gated by are: `FIR-ROADMAP-001` and `FIR-INV-010` from the master
register, canon 19f.22/19f.23's ownership statements, ADR-053's four
interface requirements, and the hard invariants the register states
(`FIR-INV-001`, `FIR-INV-002`, `FIR-INV-003`, `FIR-INV-006`,
`FIR-INV-013`, `FIR-INV-014`, `FIR-INV-015`).

## Problem

1. Without a decomposition decision, "governed documents" could be
   implemented as a module inside `compliance-service` - which already
   holds retention, legal hold and case records and would look like a
   natural home. That would make PACK-09 both the decider of retention
   _and_ the holder of the material retention governs, collapsing a
   separation the whole records-governance model depends on.
2. Without a reason-code decision, this round would either invent
   unregistered strings (which canon section 24's standard forbids) or
   force document refusals into finance and compliance codes that mean
   something else.
3. Without an explicit statement that canon is not amended, a later
   reader could take the `DOCUMENT_*` codes for canon-owned ones.

## Decision

**1. One wholly new service, `services/document-service`, package
`epd2_document_service`.** No existing service is extended in place. The
service depends on `epd2-core` and `epd2-audit-core` and on nothing else,
which is the same shape `compliance-service` and `finance-service` take
and for the same reason.

**2. Thirteen modules in strict dependency order**, each importing only
from those above it: `exceptions`, `domain`, `versions`, `authorization`,
`documents`, `evidence`, `determinations`, `references`, `events`,
`storage`, `projections`, `application`, plus `__init__`. `versions` sits
directly after `domain` and before everything else because the hash-linked
history is the guarantee the rest of the service is built on (ADR-057).

**3. Seventy-one reason codes in `contracts/reason-codes/pack-11.yml`**,
none of them `source: canon-0.8.0`. Thirty-three are `DOCUMENT_*`
refusals; twenty are `AuditEvent.reason_code` classifications for
successfully-audited acts (canon's section-24 list is refusal-only, the
same gap ADR-004 recorded for PACK-02); eighteen are reused verbatim from
PACK-02, PACK-04, PACK-07, PACK-08 and PACK-09.

**4. No code is shadowed.** `RECORD_UNDER_LEGAL_HOLD`,
`LEGAL_HOLD_STATE_UNKNOWN`, `GOVERNED_RECORD_DELETION_FORBIDDEN`,
`ORGANIZATION_SCOPE_MISMATCH`, `AUTHORITY_ROLE_INCOMPATIBLE`,
`CONFLICT_OF_INTEREST_*`, `PUBLICATION_NOT_ALLOWED` and
`DISCLOSURE_POLICY_VIOLATION` are reused, not re-prefixed. A
`DOCUMENT_RECORD_UNDER_LEGAL_HOLD` would create two codes for one fact
and let an operator's filter miss half the events.

**5. One deliberate near-collision is resolved by naming.**
`DOCUMENT_EVIDENCE_BUNDLE_SEALED` classifies a _successful_ seal;
the refusal for "this bundle is already sealed" is
`DOCUMENT_EVIDENCE_BUNDLE_ALREADY_SEALED`. One string meaning both "this
worked" and "this was refused" would make every audit query over it
ambiguous.

**6. This round amends no canon.** `docs/canonical/TZ-00-domain-event-canon.md`
is untouched and `CANON_VERSION` stays `0.8.0`. A future canon round may
give this context its own section; until then, ADR-055 through ADR-060
plus `FIR-ROADMAP-001` and `FIR-INV-010` are the normative record, and
`docs/packs/PACK-11-SPECIFICATION.md` states the model.

## Consequences

`document-service` is a leaf: nothing imports it, and it imports nothing
but the two shared packages. PACK-09's and PACK-10's placeholders are
**not** rewritten to import PACK-11's real reference types - the boundary
those placeholders exist to hold is the boundary this round keeps, and
converting them into imports would turn a documented boundary into a
runtime edge. A future pack that needs a document read adds that edge
under its own ADR.

`tests/contract/test_reason_codes_registry.py` gains a `pack-11` row with
a minimum size of 71 and a `_NON_REASON_CODE_LITERALS` entry for the five
`__all__` names the broad literal regex matches.

## Alternatives considered

**Extend `compliance-service`.** Rejected: see Problem 1. The separation
between who decides retention and who holds the material is load-bearing.

**Prefix every reused code.** Rejected: two codes per fact, guaranteed to
drift.

**Amend canon in this round.** Out of scope by instruction, and correctly
so: a canon amendment and an implementation are separate governed
decisions, and PACK-10's own two-round split (ADR-054 for the canon,
ADR-048 for the implementation) is the precedent.

## Security impact

The decomposition forecloses the failure ADR-012 and ADR-027 both guard
against: a concept with two plausible owners silently acquiring a second,
divergent implementation. "Where is the authoritative version of this
document?" has exactly one answer after this round.
