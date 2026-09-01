# ADR-068: Privileged session evidence — references, not an archive

## Status

`proposed`

## Date

2026-07-29

## Context

A privileged grant answers "who was allowed to do what". It does not
answer "what did they actually do". `FIR-INV-009` requires privileged
access to be fully audited; `AGR-23` requires the evidence that makes
post-access review and independent review possible.

Two existing models are directly relevant. PACK-02's `audit-core` gives
an append-only, hash-chained `AuditEvent` whose chaining rule
(`event_hash = sha256(canonical_dumps(hashable_fields(e)) +
previous_event_hash)`) PACK-11 reused verbatim for document versions, so
one verification procedure covers both chains. PACK-11's evidence bundles
give a sealed, digest-bound collection with provenance and custody.

## Problem

1. Session evidence detailed enough to review is, by construction, a
   record of what sensitive material someone looked at. Stored naively it
   becomes a second copy of the platform's most sensitive content, held
   in the one subsystem that is deliberately hardest to delete from.
2. Command capture that records raw input will capture credentials,
   tokens and personal data sooner or later — usually sooner.
3. Evidence that can be altered by the actor it describes evidences
   nothing.
4. A parallel evidence store would mean two sealing mechanisms, two
   integrity models and two things for an auditor to reconcile.

## Considered options

- **Option A — full session recording (keystrokes, payloads, screens).**
  Maximum reviewability, and it turns the audit subsystem into an
  unbounded archive of exactly the content every other control restricts.
  It also cannot be redacted after the fact without breaking the chain.
  Rejected.
- **Option B — grant records only, no session evidence.** Cheapest and
  answers nothing about what happened. Rejected.
- **Option C — a fixed field set of eighteen items, recording governed
  operation summaries and **references to** accessed resources, sealed at
  session end with an integrity reference, reusing PACK-11's evidence
  bundles rather than defining a parallel store.** **Chosen.**

## Decision

`P12-SES-001` fixes eighteen mandatory fields: session identifier; actor;
effective privileged role; source grant; purpose; target system; target
domain; organization scope; permitted operations; start and end;
governed operation summaries; accessed resource references; search and
export actions triggered within the session; approval references;
break-glass marker; integrity reference; evidence bundle reference;
review status.

Three prohibitions bound it:

- No secrets, plaintext credentials, private key material or full
  sensitive payloads (`P12-SES-002`).
- References to accessed resources, **not copies** — the audit subsystem
  must not become an unbounded archive of user content (`P12-SES-003`).
- Readable by the `independent_privileged_access_reviewer` and the
  `audit_custodian`, alterable by neither (`P12-SES-006`).

Sealing at session end is its own event (`P12-SES-004`), and reuses
PACK-11's evidence-bundle model by reference (`P12-SES-005`) so that one
sealing mechanism and one verification procedure serve both.

`P12-SES-007` states the limit explicitly: **tamper evidence is not
tamper resistance.** Sealed session evidence is detectably altered, not
unalterable. An actor with sufficient infrastructure access can rewrite
and recompute, because there is no external anchor. PACK-11 made the same
statement about its version chain and put it in
`PACK-11-KNOWN-LIMITATIONS.md` rather than softening it; PACK-12 follows
that precedent.

## Consequences

Easier: independent review has a defined, bounded object to review;
search and export actions taken under privilege are linked to the session
that authorised them; one integrity model across audit, documents and
sessions.

Harder: "governed operation summaries" is a design obligation, not a free
outcome — someone must decide, per operation, what summary is
reviewable without being a content copy. Getting that wrong in either
direction is a real risk: too little and review is impossible, too much
and the archive problem returns.

## Security impact

Addresses T-P12-07 (audit suppression) partially and supports T-P12-01,
T-P12-04 and T-P12-19 by making review possible at all.

Two residual risks stated: no external anchoring, so storage-level
rewriting is detectable only while the chain itself is trusted; and
attribution is only as strong as the authentication behind the actor
reference, which is PACK-14's (T-P12-05, T-P12-06).

## Data impact

Introduces `PrivilegedSession` and `PrivilegedSessionEvidence`, bound by
reference to PACK-11's `EvidenceBundleRef` and to PACK-02's audit chain.
No existing canonical entity changes.

## Migration impact

None in this round.

## Reversibility

Reversible with cost. Reducing the field set after sessions are sealed
would leave historical evidence in a shape the reader no longer expects;
adding fields is additive and safe.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
