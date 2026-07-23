# ADR-012: PACK-04 cross-pack read boundary and dependency matrix

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. The enumerated read-only dependency
edges (`initiative-service`, `moderation-service`,
`voting-service`/`tally-service`, `epd2_audit_core`), the explicit
exclusions (`deliberation-service`, `delegation-service`, and all four
PACK-02 identity/credential-adjacent services), and the one-way
dependency direction (Decision, below) are approved exactly as drafted,
with no amendments. Actually writing the cross-service call sites and
extending `tests/repository/test_service_boundaries.py` remain a later,
separate implementation task, not authorized by this acceptance alone.

## Context

`transparency-service` (ADR-011) does not itself decide, moderate, or
tally anything — it publishes records of decisions other services have
already made. To do that it must read state four other packs' services
already own: `initiative-service`'s published `Initiative`/
`InitiativeVersion` records, `moderation-service`'s issued
`ModerationDecision` records, `voting-service`/`tally-service`'s
published `ResultPublication` aggregate counts, and `epd2_audit_core`'s
`AuditEvent` records. INV-03 forbids any service from importing another
service's storage module or reaching into its store directly; ADR-008
already established the pattern PACK-03 used to satisfy this for its own
PACK-02 reads (call the owning service's public `application`-layer
function, never its `storage`/`domain` internals). This ADR is the same
question asked for PACK-04's own, differently-shaped set of reads —
notably the first time a pack reads from another same-generation pack's
services (PACK-03) rather than only from an already-shipped, earlier pack
(PACK-02), and the first time a pack's dependency list is deliberately
_narrower_ than "every sibling service in the packs below it."

## Problem

Left unresolved, `transparency-service` could be implemented with an
unreviewed, ad hoc dependency list — including, worst case, a dependency
on `delegation-service` or one of PACK-02's four identity/credential-
adjacent services, either of which would put this pack one incautious
import away from structurally undermining CT-00-08/09, the exact
guarantee this pack's own purpose (public disclosure) makes it the
highest-scrutiny consumer of to date. `tests/repository/test_service_boundaries.py`
has no rule at all yet for a `transparency-service` edge in either
direction; without an enumerated allow-list, that check cannot express
"this pack may read exactly these four things and nothing else."

## Considered options

- Option A — no enumerated boundary; each read is added ad hoc as
  `transparency-service` implementation reveals a need.
- Option B — `transparency-service` calls exactly four upstream
  `application`-layer read functions, explicitly enumerated in this ADR,
  with every other PACK-02/03 service explicitly named as excluded
  (not merely unlisted); the dependency direction is one-way
  (`transparency-service` reads from PACK-02/03; no PACK-02/03 service
  ever imports `transparency-service`).
- Option C — grant `transparency-service` blanket read access to every
  PACK-02/03 service's `application` layer, on the theory that a
  publication service legitimately might need to read anything eventually.

## Decision

Option B. `docs/handover/PACK-04-SPEC.md` section 5's dependency matrix,
restated here as the formal decision:

**Included, read-only, `application`-layer only:**

1. `transparency-service` → `epd2_initiative_service.application` — read
   published `Initiative`/`InitiativeVersion` records for
   `PublicLedgerEntry.subject_type` in (`initiative`, `initiative_version`).
2. `transparency-service` → `epd2_moderation_service.application` — read
   issued `ModerationDecision` records for
   `PublicLedgerEntry.subject_type = "moderation_decision"`.
3. `transparency-service` → `epd2_voting_service.application` and
   `epd2_tally_service.application` — read published `ResultPublication`
   aggregate counts for `PublicLedgerEntry.subject_type =
"result_publication"`.
4. `transparency-service` → `epd2_audit_core` — read `AuditEvent` records
   for `AuditExportPackage` construction (the same package PACK-02/03
   services already write to directly, now also read from for export
   purposes — the one dependency this pack shares in kind, not just
   pattern, with every prior service).

**Explicitly excluded, named rather than left unlisted:**

- `epd2_deliberation_service` — canon 5.11 does not list discussion
  content as a transparency artifact; `Discussion`/`Contribution` records
  may themselves be subject to moderation and are not "результаты"
  (results) in the sense the rest of 5.11's list uses that word.
- `epd2_delegation_service` — `Delegation`/`DelegationSnapshot` are
  structurally vote-adjacent (CT-00-09's own concern). Publishing
  anything derived from delegation state risks reconstructing
  delegate/delegator linkage indirectly, which is exactly the harm
  CT-00-09 exists to prevent; excluding the entire service is a stronger,
  simpler-to-audit guarantee than "read but redact the sensitive fields."
- `epd2_credential_service`, `epd2_identity_service`,
  `epd2_account_service`, `epd2_eligibility_service` — hard exclusion,
  all four. None of ADR-011's four proposed entities needs identity or
  credential data for any purpose identified in `docs/handover/PACK-04-SPEC.md`;
  excluding these services entirely (not merely excluding their sensitive
  fields at read time) is a stronger, structurally simpler guarantee to
  audit than "read the service but never touch certain fields."

**Forbidden regardless of direction:** no PACK-02 or PACK-03 service may
ever import `epd2_transparency_service` (one-way dependency, the same
rule ADR-008 established for PACK-03 relative to PACK-02).
`tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
must be extended (not merely re-run) to encode every edge above as an
explicit allow-list entry and every named exclusion as an explicitly
tested forbidden pair, not merely an absent one — the same distinction
ADR-008 drew between "not yet listed" and "affirmatively forbidden."

Option A is rejected for the reason ADR-008 already gave for the
equivalent PACK-03 question: it risks silently reproducing exactly the
kind of unreviewed cross-service import `tests/repository/test_service_boundaries.py`
exists to catch, at higher stakes here than for PACK-03 since this pack's
entire purpose is public disclosure. Option C is rejected because a
"publication service" being granted blanket read access to every other
service is precisely the opposite of the narrow, enumerated,
audit-friendly boundary this project has used at every prior step (ADR-008),
and would make `delegation-service`/PACK-02's four identity-adjacent
services reachable "just in case," which is the failure mode this ADR
exists to foreclose.

## Consequences

`transparency-service`'s `pyproject.toml` dependency list will contain
exactly four upstream package dependencies (plus `epd2_core`), each
narrower in scope than PACK-03's own PACK-02 dependency list was for any
single PACK-03 service. `tests/repository/test_service_boundaries.py`
grows again, this time to express a PACK-03→PACK-04 edge for the first
time (previously only PACK-02→PACK-03 existed) alongside the continuing
PACK-02→PACK-04 edge for `epd2_audit_core`. `transparency-service`'s own
`README.md` must document, per PACK-03's own established convention,
exactly which upstream `application` functions it calls and why.

## Security impact

This is the exact boundary CT-00-08 (Identity Leakage) and CT-00-09 (Vote
Linkability) depend on holding for this pack specifically — arguably more
so than for PACK-03, since PACK-03's guarantee was "this data is never
identity-linked internally," while PACK-04's guarantee is "this data,
already internally identity-free, is now also safe to show the public,"
a stronger claim that a narrower dependency surface makes easier to
defend. Excluding `delegation-service` and all four PACK-02
identity-adjacent services entirely (Decision, above) is itself a
security control, not an architectural tidiness preference — the same
framing ADR-008 used for its own enumerated function list.

## Data impact

No new canonical entity or field. This ADR does not change any PACK-02/03
entity, schema, or ownership — it only defines how PACK-04 code may read
already-published PACK-02/03 state through those services' own already-
published interfaces.

## Migration impact

None — no PACK-04 service exists yet, and no PACK-02/03 service's public
`application`-layer interface needs to change to satisfy this ADR (every
function referenced in Decision's item 1–3 already exists as of PACK-03's
own PASS state; item 4's `epd2_audit_core` read interface would need a
new, additive, read-only query function — a small, backward-compatible
addition to `epd2_audit_core`, not a change to any existing function's
signature).

## Reversibility

Reversible with cost: once `transparency-service` depends on these four
`application` functions (plus the new `epd2_audit_core` read function),
changing those functions' signatures becomes a cross-pack breaking
change requiring coordinated updates, the same reversibility profile
ADR-008 already assigned to its own equivalent decision.

## Related canon version

Authored against canon version `0.2.0`. Proposes no canon change — INV-03
already requires exactly the boundary this ADR operationalizes; this ADR
only specifies which functions satisfy it for PACK-04's specific
cross-pack reads, and does not depend on ADR-013's acceptance to be
decided in principle (though the exact `PublicLedgerEntry.subject_type`
values referenced above are ADR-013's proposal, not yet canon).
