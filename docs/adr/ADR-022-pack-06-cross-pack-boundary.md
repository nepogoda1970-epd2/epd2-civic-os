# ADR-022: PACK-06 cross-pack boundary — one narrow read into `governance-service`

## Status

`accepted`, with an amendment replacing the reviewer-verification
mechanism with a new, dedicated `governance-service` application function
(see Owner decision, below).

## Date

2026-07-24

## Owner decision

Accepted with amendment, 2026-07-24. The one-narrow-read-edge decision
(`ai-processing-service → governance-service`, for reviewer verification
only; `target_type`/`target_id` remain caller-supplied and opaque) is
approved in principle. **One amendment is required and is now
incorporated directly into this ADR's own Decision text below:** the
originally-drafted design — `ai-processing-service` calling the existing
`get_role_assignment` read and then computing `is_active_at`/
`scope_covers`/`role_code`-membership checks itself, against the plain
returned field values — is **replaced**. `ai-processing-service` must not
reimplement Governance's role-validity, scope, suspension, revocation, or
time-window semantics locally, even against plain field values. Instead,
`governance-service` gains one new, narrow application function,
`verify_role_assignment_for_action`, that performs the entire check
itself and returns only a minimal verdict. Actually adding this function
to `governance-service`'s own `application` module, and `ai-processing-
service`'s own call site for it, remain separate, later implementation
tasks, not authorized by this acceptance alone.

## Context

`docs/handover/PACK-06-SPEC.md` section 12 proposed **zero** cross-pack
dependencies in either direction for `ai-processing-service`, with
human-reviewer authorization resting entirely on the existing,
project-wide `actor_is_authorized` boolean-flag convention. This ADR's
own original draft amended that to one narrow read
(`get_role_assignment`) plus local verification logic inside
`ai-processing-service`. The project owner has now amended that draft
further: even reading plain `RoleAssignment` field values and
recomputing `is_active_at`/`scope_covers` locally still means
`ai-processing-service` carries a second, independent copy of
Governance's own authority-interpretation logic — a copy that could
silently drift from `governance-service`'s own rules (e.g. if a future
ADR changes `is_active_at`'s exact semantics, `ai-processing-service`'s
local copy would not automatically follow). `governance-service` must
remain the **single, authoritative** place this logic lives.

## Problem

A local reimplementation of active/scope/suspension/revocation/
time-window checks inside `ai-processing-service`, even a faithful one at
drafting time, is a duplicated authority surface: two independent code
paths, in two different packs, each deciding whether a given
`RoleAssignment` currently authorizes an action. Divergence between the
two — through an unnoticed governance-side rule change, a subtle
off-by-one in a re-implemented time-window check, or a scope-coverage
edge case handled differently — would silently weaken this pack's central
human-control guarantee without either pack's own tests necessarily
catching it, since each pack's `test_service_boundaries.py`/contract
tests exercise only their own copy of the logic.

## Considered options

- Option A (specification's own rejected option, unchanged) — validate
  `target_type`/`target_id` via reads into each of up to six upstream
  services. Still rejected, for the same reason the specification gave.
- Option B (specification's own recommended option for `target_type`/
  `target_id`, retained unamended) — `target_type`/`target_id` stay
  caller-supplied, opaque, never dereferenced through any service.
- Option C (this ADR's original draft, now superseded) — one narrow read,
  `governance-service.get_role_assignment`, with `ai-processing-service`
  computing the active/scope/role-code checks itself against the plain
  returned fields.
- Option D (the project owner's amendment, adopted) — one narrow **read
  operation purpose-built for this exact question**,
  `governance-service.verify_role_assignment_for_action`, which performs
  the entire active/scope/suspension/revocation/time-window/role-code
  check **inside** `governance-service` itself and returns only a minimal
  pass/fail verdict — `ai-processing-service` never sees, and never
  reimplements, the underlying logic.

## Decision

**Option B is retained unamended for `target_type`/`target_id`. Option D
replaces Option C for reviewer authorization.**

### `target_type`/`target_id` — unchanged

`target_type` and `target_id` (canon 17.1, unchanged) remain
caller-supplied, opaque references. `ai-processing-service` never
dereferences them through `initiative-service`, `deliberation-service`,
`moderation-service`, `voting-service`, `tally-service`,
`delegation-service`, or `transparency-service` — unchanged from this
ADR's original draft.

### Reviewer authorization — one new, purpose-built governance read

`ai-processing-service` gains exactly one new, read-only, forward
dependency: **`ai-processing-service → governance-service`**, using one
new function on `governance-service`'s own `application` module:

```text
governance-service.application.verify_role_assignment_for_action(
    role_assignment_id: UUID,
    required_role_codes: frozenset[str],
    required_scope_id: UUID,
    action_code: str,
    evaluated_at: datetime,
) -> RoleVerificationResult
```

**`governance-service` remains the sole authority for:**

- active-status interpretation (what "active" means against
  `RoleAssignment.status`, canon 8.4's five-value enum);
- `valid_from`/`valid_until` time-window evaluation;
- suspension, expiry, and revocation semantics;
- global-scope and scope-coverage semantics (`scope_covers`,
  `GLOBAL_SCOPE_ID`);
- role-code applicability — whether a given `role_code` is acceptable for
  the calling pack's stated `required_role_codes` and `action_code`.

All of this logic executes **inside** `governance-service`'s own
`application`/`domain` modules, using its own already-existing internal
helpers (`is_active_at`, `scope_covers`, the same functions
`_require_active_in_scope_role` already uses for governance-service's own
commands) — none of it is exposed to, duplicated by, or reimplemented in
`ai-processing-service`.

**The result exposes only the minimum needed**, as a
`RoleVerificationResult` value (name illustrative; exact type fixed at
implementation time):

- `authorized: bool` — the single, authoritative verdict.
- `verified_actor_reference` — an opaque reference derived from the
  verified `RoleAssignment.actor_id` (the same kind of already-opaque
  UUID reference this project's other cross-pack boundaries already
  treat as safe to pass across a service boundary, e.g.
  `TechnicalChallenge.submitter_authorization_reference`) — present only
  when `authorized = true`.
- `verified_scope_reference` — an opaque reference derived from the
  verified `RoleAssignment.scope_id` — present only when
  `authorized = true`.
- `reason_code` — populated only when `authorized = false`, drawn from
  `governance-service`'s own registered codes
  (`contracts/reason-codes/pack-05.yml`: e.g.
  `ROLE_ASSIGNMENT_NOT_ACTIVE`, `ROLE_ASSIGNMENT_SCOPE_MISMATCH`,
  `PERMISSION_DENIED` for a `role_code` outside `required_role_codes`, or
  `VALIDATION_RECORD_NOT_FOUND` if `role_assignment_id` does not resolve)
  — **never** a `pack-06.yml` code, since this is `governance-service`'s
  own reasoning about its own entity, not `ai-processing-service`'s.

**`ai-processing-service` never receives the underlying `RoleAssignment`
row itself** — not `role_code`, not `scope_id`, not `status`, not
`valid_from`/`valid_until`. It receives only the four fields above. This
is the structural mechanism that makes "must not import Governance domain
helpers or duplicate Governance policy logic" true by construction rather
than by convention: there is nothing for `ai-processing-service` to
recompute, because it never holds the inputs those computations would
need.

**`action_code`** is supplied by `ai-processing-service` itself (e.g. a
value identifying "review of a summarization output" versus "review of a
policy-compliance-assistance output") and is passed through to
`governance-service` for its own audit/logging purposes and as a forward-
compatible hook — a future `GovernancePolicy` (`policy_type` extension)
could key role-applicability rules on `action_code` without changing this
function's signature. It does not itself carry checking logic on the
`ai-processing-service` side.

**`required_role_codes`** is supplied by `ai-processing-service`,
populated from its own reviewer-role taxonomy below (this pack's own
repository-side configuration, not governance-service's) — mapping which
`purpose_code` requires which role remains `ai-processing-service`'s own
concern; only the **verification** that a specific `RoleAssignment`
actually holds an acceptable role, in scope, right now, is delegated to
`governance-service`.

Upon `authorized = false`, `ai-processing-service` raises its own
registered code (`AI_REVIEWER_ROLE_INVALID` or
`AI_REVIEWER_SCOPE_MISMATCH`, ADR-024) — never `governance-service`'s
`reason_code` literal directly, though that value may be surfaced as
read-only supplementary context (e.g. in a log or an
`explanation_reference`, ADR-023 D4) without being registered in
`pack-06.yml`. `human_review_status` never advances past `pending` on a
failed check, consistent with INV-10's fail-closed principle.

**Minimal repository-level reviewer role taxonomy** (unchanged from this
ADR's original draft, repository-side only, not a canon-level
enumeration):

| `role_code`               | Authorizes review of...                                                                                                                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai_output_reviewer`      | General-purpose review for summarization, recommendation, and drafting output not otherwise covered by a more specific role below (default reviewer role).                                                |
| `ai_moderation_reviewer`  | Review of classification output (section 4.2 of the specification) whose `target_type` is moderation-adjacent (e.g. `contribution`, `initiative`).                                                        |
| `ai_governance_reviewer`  | Review of policy-compliance-assistance output (section 4.6) whose `target_type` is a `governance_policy_draft`.                                                                                           |
| `ai_publication_reviewer` | Review of any output whose human-approved result is intended for official or public content (e.g. an official initiative summary, or any output feeding the mandatory AI disclosure package, ADR-025 §5). |

Every `purpose_code` maps to exactly one (or, for the
publication-crossing case, one plus `ai_publication_reviewer`) of these
four required `role_code` values, passed as `required_role_codes` to
`verify_role_assignment_for_action` — the mapping itself remains
repository-side configuration, fixed at implementation time.

### Rules restated as this ADR's own explicit boundary (per the owner's instruction)

- **No identity, account, credential, voting, tally, moderation, or
  transparency storage access.** This ADR adds exactly one read edge, to
  `governance-service` only.
- **No direct cross-service storage access.** The one permitted edge is
  through `governance-service.application.verify_role_assignment_for_action`
  only — never a direct read of `governance-service`'s underlying
  `RoleAssignmentStore`/database.
- **`ai-processing-service` must not import `governance-service.domain`,
  and must not import or call `governance-service.application.
get_role_assignment`** (the function this ADR's original draft would
  have used) **or any other `governance-service.application` function**
  (`propose_governance_policy`, `activate_governance_policy`,
  `propose_governance_decision`, `approve_governance_decision`,
  `reject_governance_decision`, `get_governance_decision`,
  `is_current_approved_decision`, `get_finality_status`,
  `submit_technical_challenge`, `begin_technical_challenge_review`,
  `get_technical_challenge`, or any role-assignment mutating command) —
  `verify_role_assignment_for_action` is the **only** function
  `ai-processing-service` may call on `governance-service`.
- **Caller-supplied `actor_is_authorized` alone is not sufficient for
  consequential AI review.** It remains the ordinary gate on whether a
  caller may invoke an `ai-processing-service` command at all
  (submission, non-consequential internal assistance, routine reads) —
  unchanged from every other PACK-02/03/04/05 command's use of the same
  flag — but is not, by itself, sufficient to move a **consequential**
  action's `human_review_status` out of `pending`. That transition
  additionally requires an `authorized: true` result from
  `verify_role_assignment_for_action`.
- **`target_type` and `target_id` remain caller-supplied opaque
  references and are not dereferenced through other services** —
  unchanged.

## Consequences

`ai-processing-service`'s `pyproject.toml` will declare exactly one
upstream package dependency beyond `epd2_core`: `epd2_governance_service`
— the second pack (after `voting-service`, ADR-017) to depend on
`governance-service`. `governance-service`'s own `application` module
gains one new public function, `verify_role_assignment_for_action` — the
first case, in this project, of a downstream pack's cross-pack read being
served by a function purpose-built for that read (rather than an
existing, more general function reused as-is, as `voting-service`'s
`get_governance_decision` and this ADR's own original
`get_role_assignment` draft both were). `tests/repository/
test_service_boundaries.py`'s forbidden-pair matrix gains one new
allow-list entry (`ai-processing-service → governance-service`) scoped,
in a future contract test, to confirm only
`verify_role_assignment_for_action` is ever imported — the strictest,
single-function entry in that matrix.

## Security impact

This amendment closes a subtler gap than the one ADR-022's original draft
closed: it prevents a second, independently-maintained copy of
Governance's own authority-interpretation logic from ever existing.
Centralizing all active/scope/suspension/revocation/time-window/
role-code logic inside `governance-service` means a future correction to
any of those rules (e.g. a stricter `is_active_at` definition) takes
effect for every consumer — including `ai-processing-service` — the
moment `governance-service` itself is updated, with no separate,
easy-to-miss update required in a second pack's own code. The minimal
four-field result (`authorized`, two opaque references, a reason code)
is deliberately narrow enough that `ai-processing-service` cannot
reconstruct the underlying `RoleAssignment` from it.

## Data impact

No new field on `RoleAssignment` or any other canonical entity. One new
`governance-service.application` function
(`verify_role_assignment_for_action`) and its result type — both
repository-side, not canon text. The reviewer role taxonomy remains
repository-side data, unchanged from this ADR's original draft.

## Migration impact

None — no `services/ai-processing-service` exists yet, and
`verify_role_assignment_for_action` does not yet exist on
`governance-service` either; both are created together as one later
implementation task.

## Reversibility

Reversible with cost once real `AIProcessingRecord`/`RoleAssignment`
review data exists: removing this read edge later would require
replacing the reviewer-verification mechanism with something else before
any consequential review could still be trusted. Comparatively easy to
reverse before any code exists (this stage) — more so than the original
draft's `get_role_assignment`-plus-local-checks design would have been,
since there is now exactly one function's contract to replace rather than
two packs' worth of duplicated logic to reconcile.

## Related canon version

Authored against canon version `0.4.0`. Proposes no canon change itself —
`RoleAssignment` (8.4) and its five-value status enum are unchanged; this
ADR only authorizes one new cross-pack read edge, one new
`governance-service` application function, and one repository-side
reviewer-role taxonomy, none of which is canon text.
