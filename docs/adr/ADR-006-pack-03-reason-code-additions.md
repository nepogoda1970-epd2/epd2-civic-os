# ADR-006: PACK-03 reason-code registry and additive codes

## Status

`accepted`

## Date

2026-07-22

## Owner decision

Accepted as proposed, 2026-07-22. The project owner approved creating a
new, separate `contracts/reason-codes/pack-03.yml` registry (Decision,
below), mirroring PACK-02's `pack-02.yml` mechanism, with no amendments.
The exact enumerated additive code list remains intentionally unfixed by
this ADR (Decision's own note) and will be finalized when the registry
file is actually written against PACK-03's real service source — that
remains a later, separate implementation task, not authorized by this
acceptance alone.

## Context

Canon section 24 defines twenty-two reason codes and states "reason code
не заменяется свободным текстом" (a reason code is never replaced by free
text). Of those twenty-two, nine are explicitly relevant to PACK-03's
scope: `BALLOT_NOT_OPEN`, `BALLOT_ALREADY_CLOSED`,
`BALLOT_CONFIGURATION_LOCKED`, `DUPLICATE_SUPPORT`, `DUPLICATE_VOTE`,
`DELEGATION_CYCLE`, `DELEGATION_EXPIRED`, `MODERATION_POLICY_VIOLATION`,
`APPEAL_DEADLINE_EXPIRED`. PACK-02's ADR-004 already established the
pattern for what happens when a pack's real services need more precision
than canon's fixed list provides: a centralized, ADR-governed, additive
registry (`contracts/reason-codes/pack-02.yml`) that copies canon's codes
verbatim and adds new ones under a documented `source` tag, validated by
a contract test that scans every service's source for `reason_code`
literals.

## Problem

`docs/handover/PACK-03-SPEC.md` section 6 already anticipates that
PACK-03's six services will need additive codes canon does not name —
concretely, at minimum:

1. Canon section 16.1 prohibits self-delegation and "two competing active
   delegations of the same scope" but names no reason code for either
   refusal.
2. Canon section 11.3 states one participant may not have more than one
   active `SupportRecord` on one initiative — `DUPLICATE_SUPPORT` already
   covers this one directly, so no gap here, but there is no code for an
   initiative that fails completeness review (`revision_required`
   status, section 11.1) versus one that is outright rejected.
3. Canon gives `Ballot.quorum_rule`/`threshold_rule` as configurable
   fields but no code for "quorum not met" or "threshold not met" as a
   distinct `ResultPublication`/`Tally` outcome classification (distinct
   from `BALLOT_NOT_OPEN`/`BALLOT_ALREADY_CLOSED`, which are about
   _when_ a vote may be cast, not the eventual count's outcome).
4. Canon section 11.4 gives `Amendment` a `superseded` status but no code
   for "this amendment's target version no longer exists / was
   superseded before a decision was reached".
5. `AuditEvent.reason_code` (canon section 18.1, per ADR-004's own
   precedent for PACK-02) needs classification codes for PACK-03's own
   successful, audited actions (a vote was received and validated, a
   tally completed, a result was published, a moderation decision was
   issued, a delegation was created/revoked) — canon's fixed list is
   entirely refusal-oriented, the same gap ADR-004 already documented and
   solved for PACK-02.

Left unresolved, PACK-03 services would either misuse an existing canon
code with a different real meaning (repeating the exact mislabeling bug
ADR-004 found and fixed for PACK-02: three exceptions that reused
`IDENTITY_NOT_VERIFIED`/`ELIGIBILITY_NOT_MET`/`CREDENTIAL_UNKNOWN_STATUS`
for a plain not-found condition) or fall back to free text, which canon
section 24 forbids outright.

## Considered options

- Option A — restrict PACK-03 to only the nine directly-named canon codes
  plus reused PACK-02 generics, forcing imprecise reuse for every gap
  listed above (repeats the exact anti-pattern ADR-004 fixed).
- Option B — a new, separate `contracts/reason-codes/pack-03.yml`
  registry, following ADR-004's exact structure (canon codes copied
  verbatim, additive codes tagged with their introducing ADR, one
  centralized file, one contract test scanning all six new services).
- Option C — append PACK-03's additive codes directly into
  `contracts/reason-codes/pack-02.yml`, on the theory that there should
  only ever be one repository-wide registry file regardless of which
  pack introduced which entry.

## Decision

Option B. `contracts/reason-codes/pack-03.yml` will be the single source
of truth for PACK-03's six services, structured exactly like
`pack-02.yml`:

1. The nine canon section-24 codes named in Context, copied verbatim,
   `introduced_in_version: "0.1.0"`.
2. New additive codes, each `introduced_in_version: "pack-03-adr-006"`,
   covering at minimum the five gaps in Problem: a self-delegation code
   (e.g. `DELEGATION_SELF_REFERENCE_FORBIDDEN`), a competing-active-
   delegation-scope code (e.g. `DELEGATION_SCOPE_CONFLICT`), an
   initiative-completeness code, quorum-not-met and threshold-not-met
   codes, an amendment-target-superseded code, and the audited-success
   classification codes PACK-03's own services need (mirroring ADR-004
   item 4's pattern exactly — one generic classification per service
   where the specific transition is already carried by the event type,
   not one code per transition).
3. The same structural validation and contract test PACK-02 already has
   (`epd2_core.reason_codes.ReasonCodeRegistry`,
   `tests/contract/test_reason_codes_registry.py`), extended to scan all
   six new services' source in addition to the existing five.

Option A is rejected for the reason ADR-004 already gave: it either
produces imprecise refusals (violating INV-09 — a refusal must be
explicable) or eventually reproduces the exact mislabeling bug ADR-004
found and fixed. Option C is rejected because `pack-02.yml`'s own header
comment documents it as PACK-02's registry specifically
(`source: pack-02-adr-004`); folding a second pack's additions into the
same file would make `introduced_in_version` provenance harder to audit,
not easier, and canon section 24 places no requirement that additive
codes live in one file across packs — only that each pack maintain one
centralized registry for itself (pack section 10's requirement, which
PACK-02 satisfied with its own file).

The exact additive code list is intentionally left to the reason-code
registry itself once written (not finalized in this ADR), consistent
with how ADR-004 finalized PACK-02's list only after auditing the real
`reason_code = "..."` call sites in the five services' actual source —
which does not yet exist for PACK-03. This ADR fixes the _mechanism and
precedent_ (a new, ADR-governed, additive registry file, never free
text), not the final enumerated list.

## Consequences

`contracts/reason-codes/pack-03.yml` becomes the one file every PACK-03
service's `reason_code` string literal must appear in, exactly as
`pack-02.yml` already is for the five PACK-02 services.
`docs/review/OPEN_QUESTIONS.md` item 10 (PACK-02's twenty-one additive
codes never folded back into canon section 24) remains open and becomes
more relevant once a second additive registry exists — this ADR does not
resolve item 10, but flags it again for the project owner
(`docs/review/PACK-03-OWNER-DECISIONS.md`).

## Security impact

None of the additive codes weaken fail-closed behavior (INV-10) — every
addition makes a refusal or audit classification more specific than an
imprecise reuse would, the same direction ADR-004 already established as
the correct one for PACK-02.

## Data impact

None — reason codes are metadata on entities/events already defined by
the canon and by `docs/handover/PACK-03-SPEC.md`; this ADR adds no new
canonical entity or field.

## Migration impact

None — no PACK-03 service has shipped; there is no prior reason-code
consumer to migrate.

## Reversibility

Reversible with cost: removing an additive code later requires confirming
no caller still emits it, the same reversibility profile ADR-004 already
assigned to PACK-02's additive codes.

## Related canon version

Authored against canon version `0.1.0`. Proposes no canon edit. Recommends
(but does not itself perform) folding PACK-03's additive codes into a
future canon minor version alongside PACK-02's still-open item 10 — see
`docs/review/PACK-03-OWNER-DECISIONS.md`.
