# PACK-08 IMPLEMENTATION ROUND — `RoleAssignment.scope_id` migration table

Required by the "PACK-08 IMPLEMENTATION ROUND" governing request, item 15:
"Before implementing migration behavior, inspect all existing `role_code`
values in the repository." This document is that inspection, performed
before any of this round's implementation code was written, plus the
resulting per-`role_code` classification the item requires. It supersedes
nothing — `docs/packs/PACK-08-MIGRATION-MATRIX.md` section 2.3 already
fixed the six-category scheme and the policy-level rule that this table
must exist before any migration touching `RoleAssignment.scope_id`
begins (tracked there as OD-11, "enumeration still open"). This document
closes that enumeration.

**No field, schema, event, or API is changed by this document.** Every
row records a classification and a migration action for a _future_
implementation to execute, individually, under its own review — exactly
as section 2.3 of the migration matrix already stipulated. This
implementation round's own code (`organization-service`) does not
consume, validate, or rewrite any `RoleAssignment` row; it introduces a
structurally distinct field, `OrganizationalAuthority.role_code` (canon
19e.15), which is a new, separate namespace, not an extension of
`governance-service`'s `RoleAssignment.role_code`. The two are never
conflated: see `docs/packs/PACK-08-IMPLEMENTATION.md` section on
cross-service boundaries.

**Correction round (2026-07-25, "PACK-08 MIGRATION TABLE CORRECTION",
pre-CI):** section 2.7 (`oversight_reviewer`) was corrected in place.
The original text classified this one role_code as carrying two scope
classes ("dual") based on the role_code alone. That is corrected: a
`role_code` alone is insufficient to determine scope; scope
classification depends on the governed assignment context. Section 2.7
is now split into two context-specific rows (2.7.1, 2.7.2), each keyed
explicitly by `GovernanceDecision.decision_type`, and the section 3
summary table gained an explicit **Context key** column reflecting the
same principle for every row. No downstream service may infer scope
from the role_code name alone. This correction changes no
implementation code, no `RoleAssignment` schema, no event, no API, no
`REPOSITORY_VERSION`/`CANON_VERSION`/canon checksum, and no ADR status —
see `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` section 10 for the
corresponding report update and the honest re-verification this
correction round ran.

## 1. How every `role_code` value in the repository was found

`RoleAssignment.scope_id` (canon 8.4) is owned exclusively by
`governance-service`; `RoleAssignment.role_code` is stored as an open
string at the canon level (canon 19b.1) and enforced against a
repository-side closed taxonomy, `PILOT_ROLE_CODES`
(`services/governance-service/src/epd2_governance_service/domain.py`).
A repository-wide search for every place a `role_code` literal is
defined, required, or asserted (source, not test-only negative
fixtures) found exactly two services that define or consume real
`role_code` values against this field:

1. `governance-service` — defines and enforces `PILOT_ROLE_CODES`
   (8 values) via its own proposer/approver role tables
   (`_POLICY_PROPOSER_ROLES`, `_POLICY_APPROVER_ROLES`,
   `_DECISION_PROPOSER_ROLES`, `_DECISION_APPROVER_ROLES`) and the
   `bootstrap.py` seed.
2. `ai-processing-service` — consumes the _same_ `RoleAssignment`/
   `scope_id` field via `governance-service`'s narrow read,
   `verify_role_assignment_for_action` (ADR-022's one sanctioned
   cross-service edge), and defines its own 4-value reviewer taxonomy,
   `REVIEWER_ROLE_CODES`, whose values are granted as ordinary
   `governance-service` `RoleAssignment.role_code` values (same field,
   same store — `ai-processing-service` does not own a second,
   parallel `role_code` concept).

No other service (`account-service`, `identity-service`,
`eligibility-service`, `credential-service`, `audit-core`,
`initiative-service`, `deliberation-service`, `moderation-service`,
`voting-service`, `tally-service`, `delegation-service`,
`transparency-service`, `membership-service`) defines or requires a
`role_code` against this field. `transparency-service`'s
`published_by_role_id`/`requested_by_role_id`/`approved_by_role_id`/
`submitted_by_role_id` fields were checked and are `role_assignment_id`
foreign-key references (pointing at a specific `RoleAssignment` row),
never `role_code` values themselves — out of this table's scope
entirely, no classification needed.

One additional literal, `"not_a_real_role"`, appears in
`services/governance-service/tests/test_bootstrap.py` — it is a
negative-test fixture proving `run_bootstrap_seed` rejects any
`role_code` outside `PILOT_ROLE_CODES`, not a real, grantable
`role_code`. Excluded from the table below; noted here so its absence
is not mistaken for an oversight.

## 2. The 12 real `role_code` values and their classification

Categories, fixed by `docs/packs/PACK-08-MIGRATION-MATRIX.md` section
2.3 (the governing request's own six-category scheme):
**1** organization scope, **2** jurisdiction scope, **3** CivicSpace
scope, **4** process-local scope, **5** global/system scope,
**6** invalid/legacy ambiguous (migration-blocked).

### 2.1 `governance_policy_proposer`

- **Source file / owner:** `services/governance-service/src/epd2_governance_service/application.py` (`_POLICY_PROPOSER_ROLES`); `governance-service`.
- **Current meaning:** proposes a `GovernancePolicy` (`propose_governance_policy`). `scope_id` is checked against the literal `GLOBAL_SCOPE_ID` constant, hardcoded at the call site — never a caller-supplied or subject-derived value.
- **Target scope class:** **5 — global/system scope.**
- **Canonical owner going forward:** unchanged — `governance-service`.
- **Migration action:** none required. A future `organization-service`-aware read may _additionally_ verify the acting actor's own `Organization`/`OrganizationalAuthority` standing before honoring a global-scoped grant (defense in depth), but the `RoleAssignment.scope_id` field itself needs no change.
- **Compatibility rule:** global scope never implies universal administrative access (HI-11) — unchanged whether or not `organization-service` is ever consulted for this role_code.
- **Authorization impact:** none — `governance-service`'s own proposer check is unaffected by PACK-08.
- **Event impact:** none — `governance-role-assignment-payload.v1.schema.json` unaffected.
- **API impact:** none.
- **Test requirement:** none beyond the existing suite; a future implementation pack may add a regression test proving this role_code's global scope never widens into cross-organizational data access.
- **Blocking ambiguity:** none.

### 2.2 `governance_policy_approver`

- **Source file / owner:** same file, `_POLICY_APPROVER_ROLES`; `governance-service`.
- **Current meaning:** approves a proposed `GovernancePolicy` (`approve_governance_policy`, dual-control with a distinct proposer actor). `scope_id` checked against `GLOBAL_SCOPE_ID`, hardcoded.
- **Target scope class:** **5 — global/system scope.**
- **Canonical owner / migration action / compatibility rule / impacts / test requirement:** identical reasoning to 2.1.
- **Blocking ambiguity:** none.

### 2.3 `ballot_invalidation_proposer`

- **Source file / owner:** `_DECISION_PROPOSER_ROLES[BALLOT_INVALIDATION]`; `governance-service`.
- **Current meaning:** proposes a ballot-invalidation `GovernanceDecision`. `scope_id` must cover the specific `Ballot`'s own id (`_decision_subject_scope_id` resolves `subject_reference["ballot_id"]`), not a global sentinel.
- **Target scope class:** **4 — process-local scope** (the referenced object is a specific `Ballot` instance, owned by `voting-service`/`tally-service`, not an `Organization`).
- **Canonical owner going forward:** unchanged — `governance-service` continues to own `RoleAssignment.scope_id`; the ballot itself remains owned by `voting-service`/`tally-service`.
- **Migration action:** none — remains process-local. No future edge to `organization-service` is warranted for this role_code; a `Ballot` is never an organizational entity.
- **Compatibility rule:** none needed.
- **Authorization impact / event impact / API impact:** none.
- **Test requirement:** none beyond existing coverage; the general false-reinterpretation regression note in `PACK-08-MIGRATION-MATRIX.md` section 2.4 already covers "never treat a process-local scope_id as an organization reference."
- **Blocking ambiguity:** none.

### 2.4 `ballot_invalidation_approver`

- **Source file / owner:** `_DECISION_APPROVER_ROLES[BALLOT_INVALIDATION]`; `governance-service`.
- **Current meaning / target scope class / everything else:** identical to 2.3 — same decision type, same scope resolution, dual-control counterpart role.
- **Blocking ambiguity:** none.

### 2.5 `technical_challenge_reviewer`

- **Source file / owner:** `_DECISION_PROPOSER_ROLES[TECHNICAL_CHALLENGE_ADJUDICATION]` and `_DECISION_APPROVER_ROLES[TECHNICAL_CHALLENGE_ADJUDICATION]`; `governance-service`.
- **Current meaning:** proposes/reviews a technical-challenge adjudication decision. `scope_id` must cover the _challenged `ResultPublication`'s_ id (`_decision_subject_scope_id`'s own documented reasoning: scoped ahead of time against the result being reviewed, not the challenge's own randomly-generated id).
- **Target scope class:** **4 — process-local scope** (`ResultPublication` is owned by `tally-service`, not an organizational entity).
- **Canonical owner going forward / migration action / compatibility rule / impacts:** unchanged, no organization-service edge warranted — identical reasoning to 2.3.
- **Test requirement:** none beyond existing coverage.
- **Blocking ambiguity:** none.

### 2.6 `governance_reviewer`

- **Source file / owner:** appears in `_DECISION_PROPOSER_ROLES[TECHNICAL_CHALLENGE_ADJUDICATION]`, `_DECISION_PROPOSER_ROLES[RESULT_FINALITY_DETERMINATION]`, and `_DECISION_APPROVER_ROLES[RESULT_FINALITY_DETERMINATION]`; `governance-service`.
- **Current meaning:** every one of this role_code's three current uses resolves `scope_id` to a specific `ResultPublication`'s id via `_decision_subject_scope_id` — never `GLOBAL_SCOPE_ID`. Unlike `oversight_reviewer` (2.7 below), this role_code's scope meaning is uniform across all of its current uses and needs no context key.
- **Target scope class:** **4 — process-local scope** (uniform).
- **Canonical owner / migration action / compatibility rule / impacts / test requirement:** identical reasoning to 2.3.
- **Blocking ambiguity:** none.

### 2.7 `oversight_reviewer` — context-dependent scope class (requires an explicit context key, not migration-blocked)

**Correction note (2026-07-25, PACK-08 MIGRATION TABLE CORRECTION round):**
this section originally classified `oversight_reviewer` as a single row
carrying two scope classes ("dual — 5 for X, 4 for Y") keyed on the
role_code alone. That framing is corrected here: **`role_code` alone is
insufficient to determine scope.** Scope classification for this
role_code depends on the governed assignment context — specifically,
which `GovernanceDecision.decision_type` the particular `RoleAssignment`
grant is being exercised for. This section is therefore split into two
context-specific rows (2.7.1, 2.7.2), each carrying its own explicit
context key, rather than one row asserting two scope classes for the
same bare role_code. **No downstream service may infer scope from the
role_code name alone** — the context key (`decision_type`) must always
be read and dispatched on explicitly, exactly as
`_decision_subject_scope_id` already does in `governance-service`'s own
source today. This split is **not a blocking ambiguity**: both
context-specific classifications below are fully pinned down by
existing code, not unknowns; nothing about the underlying source
changed, only how this table represents it.

#### 2.7.1 `oversight_reviewer` — context: `decision_type` ∈ {`MANDATE`, `OVERSIGHT_DIRECTIVE`}

- **Source / context:** `_DECISION_PROPOSER_ROLES`/`_DECISION_APPROVER_ROLES` for `GovernanceDecision.decision_type` ∈ {`MANDATE`, `OVERSIGHT_DIRECTIVE`} (both propose and approve); `governance-service`. Context key: `decision_type`, read from the specific `GovernanceDecision` the `RoleAssignment` grant is being checked against.
- **Current meaning:** `scope_id` resolves to `GLOBAL_SCOPE_ID` (`_decision_subject_scope_id`'s fallback branch — canon 19b.3 leaves the exact subject-form of these two decision types to a later implementation task; today's code treats them as platform-wide).
- **Target scope class:** **5 — global/system scope**, for this context only.
- **Canonical owner:** unchanged — `governance-service`.
- **Migration action:** none required for PACK-08. A future `organization-service`-aware read may additionally verify the acting actor's own `Organization`/`OrganizationalAuthority` standing before honoring this global-scoped grant (defense in depth); the `RoleAssignment.scope_id` field itself needs no change. Any future classification or authorization logic must condition explicitly on `decision_type ∈ {MANDATE, OVERSIGHT_DIRECTIVE}` before applying this row — **never on `role_code == "oversight_reviewer"` alone.** No change to the `RoleAssignment` schema is required — the distinguishing context key (`decision_type`) already exists on the `GovernanceDecision` being checked; this is a call-site dispatch discipline, not a stored field.
- **Compatibility rule:** global scope never implies universal administrative access (HI-11); this global-scoped grant must never be conflated with, or treated as satisfying, the process-local grant in 2.7.2, and vice versa.
- **Authorization impact:** none to existing behavior — this row documents current behavior, changes nothing.
- **Event impact:** none — `governance-role-assignment-payload.v1.schema.json` unaffected.
- **API impact:** none.
- **Test requirement:** a future implementation pack adds a regression test proving an `oversight_reviewer` `RoleAssignment` granted/checked in a `MANDATE`/`OVERSIGHT_DIRECTIVE` context (this row) is never silently accepted as authorizing a `RESULT_FINALITY_DETERMINATION` decision about a specific `ResultPublication` (2.7.2), and that no code path derives this row's scope class from the role_code string without also consulting `decision_type`.
- **Blocking ambiguity:** none.

#### 2.7.2 `oversight_reviewer` — context: `decision_type` = `RESULT_FINALITY_DETERMINATION`

- **Source / context:** `_DECISION_PROPOSER_ROLES[RESULT_FINALITY_DETERMINATION]`/`_DECISION_APPROVER_ROLES[RESULT_FINALITY_DETERMINATION]` (both); `governance-service`. Context key: `decision_type == RESULT_FINALITY_DETERMINATION`, read from the specific `GovernanceDecision` the `RoleAssignment` grant is being checked against.
- **Current meaning:** `scope_id` resolves to the specific `result_publication_id` (`_decision_subject_scope_id`'s process-local branch) — identical in shape to `governance_reviewer`'s (2.6) grant for the same decision type.
- **Target scope class:** **4 — process-local scope**, for this context only.
- **Canonical owner:** unchanged — `governance-service`; the referenced `ResultPublication` remains owned by `tally-service`.
- **Migration action:** none required for PACK-08. No future edge to `organization-service` is warranted for this context — a `ResultPublication` is never an organizational entity. Any future classification or authorization logic must condition explicitly on `decision_type == RESULT_FINALITY_DETERMINATION` before applying this row — **never on `role_code == "oversight_reviewer"` alone.**
- **Compatibility rule:** this process-local grant must never be treated as though it were global (see 2.7.1's grant), even though both share the same bare `role_code`.
- **Authorization impact:** none to existing behavior — this row documents current behavior, changes nothing.
- **Event impact:** none.
- **API impact:** none.
- **Test requirement:** a future implementation pack adds a regression test proving a `GLOBAL_SCOPE_ID`-scoped `oversight_reviewer` grant (2.7.1's context) is not silently assumed sufficient for a `RESULT_FINALITY_DETERMINATION` decision about a specific `ResultPublication` it was never actually scoped to.
- **Blocking ambiguity:** none.

**Explicit statement governing this role_code going forward:**
`role_code` alone is insufficient to determine scope for
`oversight_reviewer` — scope classification depends on the governed
assignment context (`decision_type`), per the two context-specific rows
above. No downstream service, migration, or future implementation may
infer scope from the role_code name alone; the context key must always
be read and dispatched on explicitly, exactly as
`_decision_subject_scope_id` already does today. This context-specific
split is **not a blocking ambiguity**: both rows are fully pinned down by
existing source, not unknowns.

### 2.8 `observer`

- **Source file / owner:** `PILOT_ROLE_CODES` (`domain.py`); granted via `bootstrap.py`/`application.request_role_assignment` in tests. **Not required by any proposer/approver table in `application.py`** — no command in `governance-service` currently checks for or requires this role_code to authorize any action.
- **Current meaning:** every existing grant of this role_code found in the repository (all test fixtures in `test_application.py`, `test_storage.py`) uses `scope_id=GLOBAL_SCOPE_ID`, with zero counterexamples. However, because no application-layer command actually consumes/requires this role_code today, its scope semantics have never been exercised in anger — the consistent `GLOBAL_SCOPE_ID` usage reflects "this is how every existing caller has chosen to grant it so far," not a resolved, load-bearing design decision the way `governance_policy_proposer`'s hardcoded check is.
- **Target scope class:** **5 — global/system scope, based on actual current usage** (every existing instance is global-scoped; no invented meaning). Flagged here, distinctly from 2.1/2.2, so a future implementer does not mistake "consistent so far" for "structurally guaranteed" the way the hardcoded `GLOBAL_SCOPE_ID` checks in 2.1/2.2 are.
- **Canonical owner going forward:** unchanged — `governance-service`.
- **Migration action:** **before this role_code is wired into any authorization-consequential logic (organization-scope-aware or otherwise), a future implementation must add an explicit proposer/approver-style requirement for it** (there is none today), fixing its scope semantics deliberately rather than by continued convention. Until that happens, this role_code carries no authorization weight in `governance-service` beyond being grantable and storable.
- **Compatibility rule:** global scope never implies universal administrative access (HI-11) — applies the moment this role_code is ever wired into a real check.
- **Authorization impact:** none currently (unconsumed).
- **Event impact / API impact:** none.
- **Test requirement:** a future implementation pack that wires `observer` into a real authorization check must add the same false-reinterpretation regression coverage as 2.1/2.2, plus a test proving the pre-existing, uncontested `GLOBAL_SCOPE_ID` convention is preserved rather than silently narrowed.
- **Blocking ambiguity:** none for classification (5, based on actual usage) — but flagged as **not yet load-bearing**, distinctly from every other row in this table, so no future implementer mistakes "no code checks this today" for "safe to assume any particular authorization behavior."

### 2.9 `ai_output_reviewer`

- **Source file / owner:** `services/ai-processing-service/src/epd2_ai_processing_service/domain.py` (`REVIEWER_ROLE_CODES`, `required_reviewer_role_codes`'s default branch); granted as an ordinary `governance-service` `RoleAssignment.role_code` value, verified via `governance-service.verify_role_assignment_for_action` (ADR-022).
- **Current meaning:** the default reviewer role required for `review_ai_output` when the target is not moderation-adjacent and not a policy-compliance-assistance use class. `scope_id` (as `reviewer_subject_scope_id`) is caller-supplied per call, meant to represent the scope of the specific `AIProcessingRecord`'s own target (`target_type` ∈ `initiative`/`initiative_version`/`contribution`/`discussion_post`/`moderation_case`/`governance_policy_draft`/`participation_pattern_report`) — a specific content/process instance, never an `Organization`. Existing tests commonly pass `GLOBAL_SCOPE_ID` as a convenience default (`ai-processing-service` does not itself enforce narrower scoping yet), with at least one test deliberately passing a mismatched `uuid4()` to exercise the scope-mismatch rejection path.
- **Target scope class:** **4 — process-local scope** (the target it reviews is a specific content/process instance, by design never organizational) — the `GLOBAL_SCOPE_ID` values seen in tests are a convenience default, not evidence this role_code is actually global-scoped by design, unlike 2.1/2.2/2.8.
- **Canonical owner going forward:** unchanged — `governance-service` continues to own the `RoleAssignment`/`scope_id` field; `ai-processing-service` continues to own which role_codes it requires and for which target.
- **Migration action:** none required for PACK-08. A future implementation pack may narrow `ai-processing-service`'s own callers to always pass the actual target's process-local scope id instead of the `GLOBAL_SCOPE_ID` convenience default seen in tests today — that is an `ai-processing-service`-owned test-fixture cleanup, not a schema or field migration.
- **Compatibility rule:** none needed.
- **Authorization impact / event impact / API impact:** none.
- **Test requirement:** none beyond existing coverage.
- **Blocking ambiguity:** none.

### 2.10 `ai_moderation_reviewer`

- **Source file / owner:** same file, `required_reviewer_role_codes`'s moderation-adjacent branch (`target_type` ∈ `{contribution, initiative}` under `UseClass.CLASSIFICATION`).
- **Current meaning / target scope class / everything else:** identical reasoning to 2.9 — process-local, same scope-resolution mechanism, same caller (`review_ai_output`).
- **Blocking ambiguity:** none.

### 2.11 `ai_governance_reviewer`

- **Source file / owner:** same file, `required_reviewer_role_codes`'s `UseClass.POLICY_COMPLIANCE_ASSISTANCE` branch.
- **Current meaning / target scope class / everything else:** identical reasoning to 2.9 — process-local (the target is a `governance_policy_draft` instance, not an `Organization` — note the name similarity to `governance_reviewer` (2.6) is coincidental; the two are unrelated role_codes in unrelated taxonomies, a second "false cognate" in the spirit of `PACK-08-MIGRATION-MATRIX.md` section 2.10).
- **Blocking ambiguity:** none.

### 2.12 `ai_publication_reviewer`

- **Source file / owner:** same file, `review_ai_output`'s `is_official_publication=True` branch (superseding the use-class default, requiring this role specifically from a second, independently-authorized reviewer).
- **Current meaning / target scope class / everything else:** identical reasoning to 2.9 — process-local.
- **Blocking ambiguity:** none.

## 3. Summary table

The table below carries an explicit **Context key** column. For every
row except `oversight_reviewer`, the scope class is uniform across all
current uses of the role_code, so the context key is "n/a (single
context)" — recorded explicitly here so that "no context key" is itself
a documented finding, not a silent omission. `oversight_reviewer` is the
one role_code whose scope class depends on an explicit context key
(`decision_type`) and is therefore represented as two separate rows, one
per context — never as a single row asserting two scope classes for one
bare role_code (see the correction note in section 2.7).

| `role_code`                    | Context key                                          | Owning service                                         | Target scope class                                        | Migration-blocked?                                                                |
| ------------------------------ | ---------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `governance_policy_proposer`   | n/a (single context)                                 | governance-service                                     | 5 — global/system                                         | No                                                                                |
| `governance_policy_approver`   | n/a (single context)                                 | governance-service                                     | 5 — global/system                                         | No                                                                                |
| `ballot_invalidation_proposer` | n/a (single context)                                 | governance-service                                     | 4 — process-local                                         | No                                                                                |
| `ballot_invalidation_approver` | n/a (single context)                                 | governance-service                                     | 4 — process-local                                         | No                                                                                |
| `technical_challenge_reviewer` | n/a (single context)                                 | governance-service                                     | 4 — process-local                                         | No                                                                                |
| `governance_reviewer`          | n/a (single context)                                 | governance-service                                     | 4 — process-local                                         | No                                                                                |
| `oversight_reviewer` (2.7.1)   | `decision_type` ∈ {`MANDATE`, `OVERSIGHT_DIRECTIVE`} | governance-service                                     | 5 — global/system                                         | No                                                                                |
| `oversight_reviewer` (2.7.2)   | `decision_type` = `RESULT_FINALITY_DETERMINATION`    | governance-service                                     | 4 — process-local                                         | No                                                                                |
| `observer`                     | n/a (single context)                                 | governance-service                                     | 5 — global/system (by actual usage; not yet load-bearing) | No (classification safe; authorization wiring itself does not exist yet, see 2.8) |
| `ai_output_reviewer`           | n/a (single context)                                 | ai-processing-service (via governance-service's field) | 4 — process-local                                         | No                                                                                |
| `ai_moderation_reviewer`       | n/a (single context)                                 | ai-processing-service (via governance-service's field) | 4 — process-local                                         | No                                                                                |
| `ai_governance_reviewer`       | n/a (single context)                                 | ai-processing-service (via governance-service's field) | 4 — process-local                                         | No                                                                                |
| `ai_publication_reviewer`      | n/a (single context)                                 | ai-processing-service (via governance-service's field) | 4 — process-local                                         | No                                                                                |

**No `role_code` in the repository is classified into category 6
(invalid/legacy ambiguous) or marked BLOCKED.** Every value has a
complete, source-verified current meaning. `oversight_reviewer` is
represented as two context-specific rows (2.7.1, 2.7.2) rather than one
row with two scope classes — a role_code alone is insufficient to
determine its scope; the governed assignment context (`decision_type`)
determines it, and no downstream service may infer scope from the
role_code name alone. `observer` carries a documented "classified but
not yet load-bearing" note. Both are called out distinctly above
precisely so neither is later mistaken for a plain, single-context
classification like the other ten rows.

**This round's own new field, `OrganizationalAuthority.role_code`
(canon 19e.15, `organization-service`), is a structurally separate
namespace and is not part of this table** — it is not
`RoleAssignment.scope_id`, it is not owned by `governance-service`, and
no existing `RoleAssignment` row is read, written, or reinterpreted by
`organization-service` in this implementation round (see cross-service
boundary decision, `docs/packs/PACK-08-IMPLEMENTATION.md`).

## 4. Whether this blocks any part of PACK-08

**No.** Every `role_code` found is classifiable without inventing
meaning, and none requires a schema, event, or API change to close its
classification. Per item 28 of the governing request: this inspection
reveals no blocking ambiguity, so no part of PACK-08's implementation
is blocked by it, in whole or in subset. The entries carrying an
explicit caveat (`oversight_reviewer`'s context-dependent scope class,
split into the two context-specific rows 2.7.1/2.7.2 rather than one
row asserting two scope classes for a bare role_code; `observer`'s
not-yet-load-bearing status) are forward-looking notes for whichever
future implementation pack first wires `governance-service` role_codes
into `organization-service`-aware authorization logic — not blockers to
this round, which introduces no such wiring at all.

## 5. Cross-reference

- Policy-level scheme and the OD-11 commitment this table closes:
  `docs/packs/PACK-08-MIGRATION-MATRIX.md` section 2.3.
- Open items this table does not itself resolve:
  `docs/packs/PACK-08-OPEN-DECISIONS.md` items OD-11 (now closed by
  this document), OD-12, OD-13 (unaffected).
- This implementation round's own scope and cross-service boundary
  decisions: `docs/packs/PACK-08-IMPLEMENTATION.md`.
