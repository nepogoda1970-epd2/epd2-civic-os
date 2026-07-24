# ADR-017: PACK-05 cross-pack boundary — reads, and the ballot/result write question

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. The asymmetric write-boundary decision
(Decision, below) is approved exactly as drafted, with no amendments:
Option B for ballot invalidation (`voting-service` remains the sole
writer of `Ballot`, gains one new `invalidate_ballot` command validating
an approved `GovernanceDecision`); no new `tally-service` command and no
new `ResultPublication` field for result finality, which is instead
represented and queried entirely through `governance-service`. The
enumerated read edges (`voting-service.get_ballot`,
`tally-service.get_result_publication`,
`epd2_audit_core.list_by_target_types`, all already-existing functions)
and the one new reverse read edge (`voting-service` →
`governance-service.get_governance_decision`) are accepted exactly as
proposed. Actually writing the new commands, the new read functions, and
extending `tests/repository/test_service_boundaries.py` remain a later,
separate implementation task, not authorized by this acceptance alone.

**Note on `finality_outcome`/`FinalityStatus` terminology:** ADR-018's
own acceptance (this same round) amends how `GovernanceDecision`
represents finality — `finality_outcome` now stores only `final`/
`invalidated`, with a separate `FinalityStatus` read-model type
(`provisional`/`finality_blocked`/`final`/`invalidated`) as
`get_finality_status`'s actual return type. This ADR's own Decision text
below, which already describes `get_finality_status` returning one of
four status values, remains accurate under that refinement — the
function's behavior and signature are unchanged; only the internal
distinction between what is persisted and what is derived was clarified
by ADR-018's amendment, not something this ADR itself needed to change.

## Context

`governance-service` (ADR-016) needs to read state two other packs'
services already own — `voting-service`'s `Ballot` and `tally-service`'s
`ResultPublication` — and, unlike every prior cross-pack ADR in this
project (ADR-008, ADR-012), needs some way for an authorized governance
ruling to actually take effect on an entity it does not own:
`Ballot.status → invalidated`, and some representation of whether a
`ResultPublication` has reached finality. `docs/handover/PACK-05-SPEC.md`
section 5 identified this as the pack's single most consequential open
decision and presented it as a two-option choice for the owner. This ADR
records that choice, made asymmetrically for the two entities involved,
per the owner's binding instruction for this draft.

## Problem

This project's established cross-pack pattern (ADR-008 for PACK-03→
PACK-02, ADR-012 for PACK-04→PACK-02/03) is strictly one-way and
read-only: a downstream pack calls an upstream service's `application`-
layer read function, never mutates it. Governance authorization does not
fit that pattern by itself — an approved `GovernanceDecision` to
invalidate a `Ballot` must eventually cause `Ballot.status` to actually
change, and `voting-service` remains the sole entity owner section 22's
ownership matrix assigns it. Left unresolved, an implementation could
either invent an unprecedented direct write edge from `governance-service`
into `voting-service`'s storage (violating the ownership-matrix
invariant every prior pack has kept absolute), or silently do nothing
(leaving ADR-009 item 14's mandate unfulfilled).

## Considered options

- Option A — `governance-service` calls directly into `voting-service`'s
  and `tally-service`'s `application` layers with a new, genuinely
  mutating call, bypassing each service's own "only that service's own
  commands mutate its own entities" boundary.
- Option B — each owning service gains its own new, narrowly-scoped
  application command, gated by reading an approved `GovernanceDecision`
  from `governance-service`; the owning service remains the sole
  mutator of its own entity in every case.
- Option C — no write edge of any kind; `Ballot`/`ResultPublication`
  state is never affected by any `GovernanceDecision`, and any
  consumer wanting to know about an invalidation or a finality
  determination must separately query `governance-service` and
  `voting-service`/`tally-service` and reconcile the two itself.

## Decision

**Option B for ballot invalidation. A variant of Option C —
"no `ResultPublication` write, finality represented and queried
entirely through `governance-service`" — for result finality.** This
asymmetry is deliberate, per the owner's binding instruction, and is
recorded precisely because the two entities are not treated identically:

### Ballot invalidation — Option B

`voting-service` remains the **sole writer** of `Ballot`. It gains
exactly one new, narrowly-scoped application command —
`invalidate_ballot(ballot_id, governance_decision_id, actor,
actor_is_authorized, correlation_id, clock, event_id=None)` — which
internally calls a new, read-only, ADR-017-sanctioned function,
`epd2_governance_service.application.get_governance_decision`, to
confirm that the caller-supplied `governance_decision_id` refers to a
`GovernanceDecision` that is: `approved` (its own two-actor approval,
section 9 of the specification, already satisfied), of
`decision_type = "ballot_invalidation"`, and targets exactly this
`ballot_id`. Only if all three hold does `voting-service`'s own command
proceed to transition `Ballot.status → invalidated` (the already-canon-
defined status, canon 15.1) and emit its own event. `governance-service`
never writes to `Ballot` directly, and gains no new write-capable
function of any kind pointed at `voting-service`.

### Result finality — no `ResultPublication` write

**`tally-service` gains no new mutating command, and
`ResultPublication` itself gains no new field.** Per the owner's
explicit instruction, `determine_result_finality` is **not** added as a
`tally-service` command, because `ResultPublication` (canon 15.6)
remains textually unchanged by this pack — this is a deliberate,
narrower choice than `docs/handover/PACK-05-SPEC.md` section 5's own
working recommendation, which had proposed a symmetric `tally-service`
write. Instead:

- A `result_finality_determination` `GovernanceDecision` (ADR-018)
  records the ruling entirely within `governance-service`'s own storage,
  referencing `result_publication_id` but never writing to
  `tally-service`.
- `governance-service` gains a new, read-only query function —
  `epd2_governance_service.application.get_finality_status(
result_publication_id)` — that any consumer (including a future
  Transparency-side publication, out of this pack's scope) calls to
  learn whether a given `ResultPublication` is `provisional`, `final`,
  `finality_blocked`, or `invalidated` (ADR-018's four-value enum).
  `tally-service` itself is never asked, and has nothing new to answer,
  since it never gains finality-relevant state.
- `governance-service` reads `tally-service`'s `get_result_publication`
  (already exists, ADR-012-sanctioned) only to confirm a referenced
  `result_publication_id` exists and to read its `challenge_deadline_at`
  when validating `TechnicalChallenge` submission timing (ADR-020) — a
  read, not a write, and not a new function.

**Read edges, proposed:**

| Upstream service  | Pack    | Read for                                                                                                        | Function                                                                                     |
| ----------------- | ------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `voting-service`  | PACK-03 | Confirm a `Ballot`'s existence/current status before an approved `ballot_invalidation` decision may be acted on | `epd2_voting_service.application.get_ballot` (already exists, ADR-012-sanctioned)            |
| `tally-service`   | PACK-03 | Read `challenge_deadline_at` and current state for `TechnicalChallenge` intake/adjudication timing (ADR-020)    | `epd2_tally_service.application.get_result_publication` (already exists, ADR-012-sanctioned) |
| `epd2_audit_core` | PACK-02 | Read governance-relevant audit history for `oversight_directive` `GovernanceDecision`s                          | `epd2_audit_core.application.list_by_target_types` (already exists, added by PACK-04)        |

**The one new reverse read edge:** `voting-service`'s new
`invalidate_ballot` command imports exactly one new
`epd2_governance_service.application` function,
`get_governance_decision` — the first bidirectional (still one-writer-
per-entity, still read-only-in-either-direction) relationship between
two packs in this project. No other PACK-02/03/04 service gains any
import of `epd2_governance_service`.

**Explicitly excluded, named rather than left unlisted:**

- `initiative-service`, `moderation-service`, `deliberation-service`,
  `delegation-service` — no entity proposed for PACK-05 needs initiative,
  discussion, moderation, or delegation data directly.
- `transparency-service` — nothing proposed here reads from or writes to
  the public ledger; a `GovernanceDecision` becoming publicly visible is
  a future Transparency-side concern, not this pack's read or write.
- `credential-service`, `identity-service`, `account-service`,
  `eligibility-service` — hard exclusion, same reasoning ADR-012 already
  gave: nothing proposed here needs identity or credential data, and
  excluding these four entirely is a stronger, simpler-to-audit
  guarantee than "read but redact."

Option A is rejected: it is the only option that would give `Ballot` or
`ResultPublication` a second mutator, breaking the section 22
ownership-matrix invariant every prior pack has kept absolute. Option C
in its pure form (no write edge at all, not even for ballot invalidation)
is rejected for `Ballot` specifically, because ADR-009 item 14's mandate
— "authorization and two-actor approval for invalidation belongs
entirely to the future Governance service" — requires that an approved
decision actually be able to invalidate a ballot, not merely be recorded
alongside an unreachable `Ballot.status`. The Option-C-shaped choice is
retained, deliberately, for `ResultPublication` only, per the owner's
explicit instruction that finality must be represented and queried
through `governance-service`, never by rewriting `ResultPublication`.

## Consequences

`governance-service`'s `pyproject.toml` will declare exactly three
upstream package dependencies (`epd2_voting_service`, `epd2_tally_service`,
`epd2_audit_core`) plus `epd2_core`. `voting-service`'s own
`pyproject.toml` gains exactly one new dependency,
`epd2_governance_service`, for its own `invalidate_ballot` command's
validation read — the first time any PACK-02/03/04 service depends on a
later pack's service. `tests/repository/test_service_boundaries.py`
must be extended twice: once for `governance-service`'s three read
edges (forward direction), and once for `voting-service`'s single new
read edge into `governance-service` (reverse direction) — both encoded
as explicit allow-list entries, with every other pair (including
`tally-service → governance-service`, which does not exist under this
decision) explicitly tested as forbidden, not merely absent.

## Security impact

This is the first ADR in this project to authorize any kind of
authority-bearing cross-pack interaction beyond a pure read. The design
keeps the single-writer-per-entity guarantee intact: `voting-service`
is still the only code that ever writes `Ballot.status`, and
`tally-service`/`ResultPublication` are untouched entirely. The
two-actor approval check (ADR-020) happens once, inside
`governance-service`'s own `GovernanceDecision` approval flow, before
`get_governance_decision` would ever report a decision as `approved` —
`voting-service`'s own `invalidate_ballot` command does not re-implement
or duplicate that check, it only trusts the read result, the same
trust relationship ADR-008/012 already established for every prior
upstream/downstream read.

## Data impact

No new field on `Ballot` beyond its already-canon-defined `invalidated`
status (canon 15.1, already structurally present since PACK-03, per
ADR-009 item 14's "PACK-03 implements the status, but no command may
reach it"). **No new field on `ResultPublication`** — this ADR
explicitly declines to add one, per the owner's instruction; finality
state lives entirely in `governance-service`'s own `GovernanceDecision`
entity (ADR-018).

## Migration impact

None — no PACK-05 service exists yet, and no PACK-03 service's public
`application`-layer interface needs to change except the two additive
functions this ADR introduces (`voting-service.invalidate_ballot`,
a new command, not a change to any existing function's signature; and
`governance-service.get_governance_decision`/`get_finality_status`,
both new).

## Reversibility

Reversible with cost: once `voting-service.invalidate_ballot` depends on
`governance-service.get_governance_decision`'s signature, changing that
signature becomes a cross-pack breaking change. The decision to keep
`ResultPublication` unchanged is comparatively easy to reverse later (a
future ADR could still add a field to `ResultPublication` and migrate
finality state onto it), whereas retrofitting `Ballot.invalidated`
reachability after the fact would not be — this asymmetry in
reversibility is itself a point in favor of the more conservative
choice made here for `ResultPublication`.

## Related canon version

Authored against canon version `0.3.0`. Proposes no canon change itself
in the sense of a field addition to `Ballot`/`ResultPublication` — it
only specifies how an already-canonical `Ballot.invalidated` status
(reachable, per this decision, for the first time) is reached, and
confirms `ResultPublication` gains no new canon field under this
decision. ADR-018 is the ADR that proposes the new canonical
`GovernanceDecision` entity this ADR's mechanism depends on.
