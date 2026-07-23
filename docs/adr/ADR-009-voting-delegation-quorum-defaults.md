# ADR-009: Voting, delegation, quorum, tie, challenge, and finality defaults

## Status

`accepted`, with amendments to items 13 and 14 (see Owner decision and the
amended Decision entries below).

## Date

2026-07-22

## Owner decision

Accepted with amendments, 2026-07-22. Items 1–12 and 15 are accepted
exactly as proposed. Items 13 and 14 are accepted only in amended form,
superseding the originally proposed text for those two items (the
amended text is now the Decision, not the original proposal — both are
kept below for the record, with the amendment clearly marked):

- **Item 13 (technical-challenge deadline)**: the 72-hour default and
  per-ballot-type configurability are accepted, but the owner rejected
  deferring the required canon change to an unspecified future ADR.
  The canon change is being progressed now, through the proper process:
  `docs/adr/ADR-010-ballot-challenge-window-canon-addition.md` (new,
  `proposed`) specifies the exact canon minor-version addition this item
  needs. `docs/canonical/TZ-00-domain-event-canon.md` itself is **not**
  edited by this acceptance — canon immutability (this project's standing
  rule, and canon section 26) requires ADR-010 to independently reach
  `accepted` before the canon document changes. `ResultPublication`
  remains provisional until the configured challenge window elapses
  without an accepted integrity challenge, exactly as item 12 already
  states.
- **Item 14 (ballot invalidation)**: the owner rejected introducing any
  provisional Governance/Crisis role inside PACK-03, including as a
  placeholder. PACK-03 may implement the canonical `invalidated` `Ballot`
  status and the validation/state-machine structures around it (so
  CT-00-02/CT-00-03 can test it structurally), but no public
  application-layer command in PACK-03 may actually invalidate a ballot.
  Authorization and two-actor approval for invalidation belongs entirely
  to the future Governance service (canon 5.12, out of PACK-03's scope),
  not to any interim PACK-03 role.

## Context

Canon section 29 ("Открытые решения до разработки голосования") lists
fifteen questions the canon itself defers: "не блокируют инфраструктурный
этап, но должны быть решены до пакета Voting" (do not block the
infrastructure stage, but must be resolved before the Voting package).
`docs/review/OPEN_QUESTIONS.md` item 7 already flags that these fifteen
questions exist and are the project owner's to decide, not something to
answer unilaterally. PACK-03 (`docs/handover/PACK-03-SPEC.md` section 8)
is the Voting package canon section 29 anticipates — these questions can
no longer be deferred without blocking implementation.

## Problem

None of the fifteen questions has a canon-mandated answer. Some already
have a partial structural hint in the entity fields canon defines (e.g.
`VoteEnvelope.status` already includes `superseded`, which only makes
sense if vote-changing is allowed at all) but none is actually decided.
Implementing PACK-03 without explicit answers would force silent,
undocumented choices buried in code — exactly what canon section 29
exists to prevent by naming the questions up front.

## Considered options

- Option A — leave every question unanswered until the project owner
  responds, blocking all PACK-03 implementation indefinitely.
- Option B — propose a specific, conservative, fail-closed default for
  every question, each traceable to a canon invariant or field already in
  place, and record every proposal in one ADR so the project owner can
  accept, reject, or amend each individually rather than the pack
  blocking on a fifteen-question survey with no starting point.
- Option C — silently choose defaults during implementation and document
  them only after the fact in the pack's handover report, the way an
  incidental design choice would be recorded.

## Decision

Option B. Fifteen proposed defaults, one per canon section 29 question,
each requiring explicit owner sign-off before its corresponding code is
written (canon section 26; no default below is authorized for
implementation by this ADR's existence alone — only by its acceptance):

1. **Can a participant change their vote before close?** Proposed: yes.
   `VoteEnvelope.status` already includes `superseded` for exactly this
   case; only the latest valid envelope per credential is counted.
2. **Which choice counts if the vote changed?** Proposed: the most recent
   valid `VoteEnvelope` received strictly before `Ballot.closes_at`.
3. **Is abstention a distinct option?** Proposed: yes — modeled as an
   explicit `BallotOption` (e.g. `option_code = "abstain"`), never
   inferred from a missing vote, keeping quorum/threshold math and audit
   trails explicit rather than implicit.
4. **Which voting methods are in the pilot?** Proposed: single-choice /
   yes-no only for the first release; ranked-choice or multi-select
   deferred to a later canon minor version once the simpler case is
   proven end-to-end.
5. **Is quorum required for every procedure?** Proposed: no.
   `Ballot.quorum_rule` is already an optional, per-ballot field; default
   to no quorum requirement unless a specific ballot configures one.
6. **Who may create a ballot?** Proposed: gated by `RoleAssignment`
   scoped to the relevant `CivicSpace` — never a bare `Account` — mirroring
   PACK-02's existing `actor_is_authorized` pattern.
7. **Who approves final ballot parameters?** Proposed: a second, distinct
   authorized actor from the one who created the ballot, required for the
   `configuration_review → scheduled` transition — a direct application
   of INV-08 ("critical actions require separation of authority") to this
   specific transition.
8. **Is delegation enabled in the first pilot?** Proposed: `Delegation`/
   `DelegationSnapshot` are implemented fully in PACK-03 regardless
   (canon requires them in this pack's scope), but new `Ballot`s default
   to `delegation_policy_version = null` (delegation resolution disabled)
   for the first real ballot type; enabling it is a per-ballot-type
   configuration choice, not a repository-wide switch.
9. **Maximum delegation depth?** Proposed: a small, explicit bounded
   constant (depth 1 — no re-delegation chains) for the pilot,
   configurable later. This is a hard cap in addition to, not instead of,
   `delegation.cycle_detected`/`DELEGATION_CYCLE` cycle detection — the
   two are complementary, not redundant.
10. **Can a delegator override their delegate for one ballot?** Proposed:
    yes — a delegator's own valid `VoteEnvelope` for that `Ballot`,
    received before `DelegationSnapshot` resolution closes, takes
    precedence over any vote cast by their delegate using that specific
    delegation for that same ballot. The precise ordering/cutoff rule
    must be specified in the corresponding implementation task before
    code is written, not left to inline comments.
11. **How are ties handled?** Proposed: no silent tie-break. A tied
    result is recorded as its own explicit `ResultPublication` outcome
    (e.g. `threshold_result = "tie_no_decision"`); any specific tie-break
    method must be an explicit, documented, per-ballot `threshold_rule`
    configuration — never an implicit fallback baked into tally logic.
12. **When is a result final?** Proposed: after `ResultPublication.published_at`
    plus the technical-challenge window (item 13) elapses with no accepted
    integrity challenge. Before that, the result is tallied-but-provisional
    and must be represented as such, not silently treated as final.
13. **Technical-challenge deadline?** **Amended, accepted.** A
    configurable window, defaulting to 72 hours, configurable per ballot
    type. Canon has no existing field for this; rather than defer the
    canon change to an unspecified future ADR (the original proposal),
    the required canon minor-version addition is being prepared now as
    `ADR-010-ballot-challenge-window-canon-addition.md` (`proposed`,
    pending its own acceptance before the canon document itself is
    edited — see Owner decision). `ResultPublication` remains provisional
    until the configured challenge window expires without an accepted
    integrity challenge (ties directly to item 12).

    _Original proposal (superseded): a configurable fixed window (72
    hours suggested) with the canon change deferred to an unspecified
    future ADR "once this default is accepted, not something to hardcode
    ad hoc in the meantime." The owner rejected the deferral specifically
    — the 72-hour/per-ballot-type default itself was accepted unchanged._

14. **Who may invalidate a ballot?** **Amended, accepted.** No
    provisional Governance/Crisis role is introduced inside PACK-03, not
    even as a placeholder. PACK-03 implements the canonical `invalidated`
    `Ballot` status and the validation/state-machine structures around it
    (so CT-00-02 Unknown Status and CT-00-03 Forbidden Transition can be
    tested against it structurally), but **no public application-layer
    command in PACK-03 may invalidate a ballot** — the status exists and
    is validated, but is unreachable through any PACK-03 API. Full
    authorization and two-actor approval for invalidation belongs
    entirely to the future Governance service (canon 5.12, out of
    PACK-03's scope, `docs/handover/PACK-03-SPEC.md` section 1).

    _Original proposal (superseded): gate invalidation behind a
    narrowly-scoped `RoleAssignment` role with two-actor approval,
    provisional pending PACK-05+. The owner rejected introducing any
    interim role at all — PACK-03 implements the state, not a command to
    reach it._

15. **What audit-package data is published openly?** Proposed:
    `ResultPublication`'s aggregate counts (`eligible_count`,
    `credential_count`, `accepted_vote_count`, `rejected_vote_count`,
    `quorum_result`, `threshold_result`) plus a redacted audit-chain proof
    (hashes only, never full `AuditEvent` payloads) — never individual
    `VoteEnvelope` contents or anything identity-linked. Full public
    disclosure design belongs to the Transparency Context (canon 5.11,
    out of PACK-03's scope); this is only the minimum PACK-03 itself must
    expose to make CT-00-09/CT-00-10 independently verifiable by a third
    party.

Option A is rejected because it blocks all PACK-03 implementation
indefinitely on a fifteen-question survey with no proposed starting
point, which is not what canon section 29 asks for ("должны быть решены",
must be resolved — not "must be re-derived from nothing"). Option C is
rejected because canon section 26 and this project's own established
practice (ADR-002 through ADR-004) require exactly this kind of decision
to be recorded and reviewed _before_ the corresponding code exists, not
narrated afterward as an incidental implementation detail.

## Consequences

Every one of the fifteen defaults above becomes a specific, reviewable
implementation requirement once accepted (or a specific point of
disagreement once amended) rather than an undocumented assumption buried
across six services' worth of code. `docs/review/PACK-03-OWNER-DECISIONS.md`
restates these fifteen items (plus ADR-005/006/008's own decision points)
as the concrete list the project owner needs to act on before
implementation proceeds.

## Security impact

Every default above is chosen to be fail-closed (INV-10) where canon
gives no explicit rule: no silent tie-break (item 11), no implicit
finality before a challenge window elapses (items 12-13), separation of
authority for ballot approval (item 7), no PACK-03-reachable ballot
invalidation at all rather than an interim authorization path with its
own attack surface (item 14, as amended), and no vote-content disclosure
beyond aggregate counts (item 15). Item 14's amendment is, if anything,
more conservative than the original proposal from a security standpoint:
an unreachable status has no authorization logic to get wrong, whereas an
interim role would have been a second, provisional access-control path
to reason about and eventually retire. None of these defaults weakens
CT-00-09 (Vote Linkability) or CT-00-10 (Rule Freeze) as specified in
`docs/handover/PACK-03-SPEC.md`.

## Data impact

Item 13 (a technical-challenge deadline field) is the only default above
that implies a new canonical field not currently named by the canon.
Per the owner's amendment, this is not deferred: `ADR-010-ballot-challenge-window-canon-addition.md`
specifies the exact field(s) now, as a `proposed` canon minor-version
addition — the canon document itself is unchanged until ADR-010
separately reaches `accepted`. Item 14, as amended, adds no new field —
`Ballot.status = "invalidated"` is already canon-defined (section 15.1);
PACK-03 only implements the validation/state-machine structures around a
status the canon already lists, without exposing a command to reach it.
Every other default configures behavior using fields the canon already
defines (`Ballot.quorum_rule`, `Ballot.threshold_rule`,
`Ballot.delegation_policy_version`, `VoteEnvelope.status`,
`BallotOption`).

## Migration impact

None — no `Ballot` has ever been created in this repository; there is no
existing data whose behavior these defaults would retroactively change.

## Reversibility

Reversible with cost proportional to how many real ballots have run under
a given default by the time it changes — e.g. changing item 9's depth
cap after ballots have used depth-1 delegation chains is straightforward
(widening a limit); changing item 3 (making abstention implicit after
ballots have already modeled it as an explicit option) would require a
data migration and is effectively irreversible once results have been
published under the original rule. Each default is annotated in
`docs/review/PACK-03-OWNER-DECISIONS.md` with which category it falls
into where that distinction matters. Item 14 as amended is cheaply
reversible in the direction that matters most: adding a real,
Governance-owned invalidation command later is a pure addition (no
existing behavior to unwind), whereas the original proposal's interim
role would have been the harder direction to reverse (retiring a role
real ballots may have already relied on). Item 13's canon field addition
(via ADR-010) is reversible with the same cost profile canon section 25
gives any additive field once real `Ballot`s exist and use it.

## Related canon version

Authored against canon version `0.1.0`, directly resolving the fifteen
questions canon section 29 raises. Item 13's challenge-deadline field is
now the subject of a specific, prepared follow-up ADR
(`ADR-010-ballot-challenge-window-canon-addition.md`, `proposed`) rather
than an unspecified future one, per the owner's amendment. No existing
canon field, event, or status is changed by this ADR itself — any actual
canon edit happens only if and when ADR-010 independently reaches
`accepted`.
