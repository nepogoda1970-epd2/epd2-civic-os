# ADR-020: PACK-05 authority, roles, and challenge-lifecycle defaults

## Status

`accepted`, with amendments to technical-challenge submission
authorization (aligning with ADR-018's own amendment) and the bootstrap
governance-authority mechanism (see Owner decision, below).

## Date

2026-07-23

## Owner decision

Accepted with amendments, 2026-07-23. §1 (two-actor approval scope) and
§5's role taxonomy (table) are accepted exactly as proposed, no changes.
Two amendments are required and now incorporated directly into this
ADR's own text below:

1. **Challenge submission aligned with amended ADR-018 (§2)** — eligible
   participants submit through a valid, ballot-scoped
   `ParticipationCredential`; observers/reviewers submit through an
   active, in-scope `RoleAssignment`; submission still does not require
   a governance decision-making role; adjudication and approval still
   require governance roles. This is a terminology/mechanism alignment
   with ADR-018's own `submitter_authorization_type`/
   `submitter_authorization_reference` amendment, not a change in
   substance from this ADR's original proposal.
2. **Bootstrap governance authority, fully specified (§5)** — the
   original proposal's bootstrap mechanism (an out-of-band, logged seed
   of two initial role-holders) is accepted in principle and now made
   concrete rather than left as this ADR's own flagged-open item: the
   two-distinct-actor rule is kept; it is implemented **only** through a
   dedicated deployment-time seed command, never through the normal API;
   it requires exactly two distinct initial actors; it produces an
   immutable seed manifest, checksum, and `AuditEvent`; the seed command
   is **permanently disabled** after its first successful run; no seeded
   actor may seed or approve their own assignment; and every later role
   grant uses the normal two-actor governance flow. This resolves the
   one item the owner-decisions checklist flagged as still open after
   the drafting round.

§3 (multiple-challenges rule) and §4 (no-challenge path) are confirmed
accepted **unchanged** — the owner's acceptance explicitly restates them
verbatim rather than amending them, and this ADR's own text below is
unchanged for both.

**Per this task's explicit instruction, canon `0.3.0` is not edited and
no PACK-05 code is implemented as part of this acceptance.**
`role_code`'s taxonomy and the bootstrap seed command are both
repository-side content (not canon text) — this ADR's acceptance
authorizes both to be built once `governance-service` implementation
begins, a separate, later task not authorized by this acceptance alone.

## Canon implementation (2026-07-23, follow-on task)

The dedicated canon-edit task gated on this ADR's (and ADR-018's)
acceptance has now been carried out, as its own separate task. This
ADR's own content — the closed pilot `role_code` taxonomy and the
bootstrap seed-command mechanism (§5) — remains repository-side content,
not canon text, exactly as stated above; no part of §5's taxonomy or
seed-command mechanics was added to
`docs/canonical/TZ-00-domain-event-canon.md` itself. What canon 0.4.0
(section 19b) _does_ record from this ADR is the structural content that
is canon-shaped: `RoleAssignment`'s integration and the closed taxonomy
listed for cross-reference (19b.1, naming the eight `role_code` values
this ADR fixes, without itself constraining `role_code` as a canon
field beyond its pre-existing open-string definition, 8.4); the
two-actor approval scope this ADR's §1 requires, reflected in
`GovernancePolicy`/`GovernanceDecision`'s transition rules (19b.2, 19b.3);
and the multiple-challenge/no-challenge-path rules this ADR's §3/§4
restate, reflected in 19b.5. `canon_version` moved `0.3.0 → 0.4.0` as
part of the same edit ADR-018 performed — see ADR-018's own "Canon
implementation" section for the checksum. This was a canon-only change;
no `services/governance-service` directory, schema, OpenAPI file, or
reason-code registry was created, and no PACK-02/03/04 source code was
touched. `governance-service` implementation — including the bootstrap
seed command itself — remains a separate, later task.

## Context

`docs/handover/PACK-05-SPEC.md` section 8 identified several
Governance-specific defaults as requiring explicit owner decision rather
than a silently-assumed default: what counts as a "critical action"
needing two-actor approval, who may hold which `role_code`, the
technical-challenge submission window and eligibility, the
result-finality determination trigger, and oversight/review workflow
scope. This ADR records the owner's binding decisions on each, in the
same spirit as ADR-009's own section-29 defaults round for PACK-03.

## Problem

Left undecided, `governance-service` implementation would need to invent
these rules ad hoc — exactly the risk canon section 26 and this
project's INV-08 both exist to prevent for anything touching separation
of authority, since an incorrectly-defaulted two-actor check or an
unbounded `role_code` taxonomy would undermine the entire pack's
purpose.

## Considered options

- Option A — defer all of these questions to implementation-time
  judgment, documented only in code comments.
- Option B — resolve each question explicitly in this ADR, as concrete,
  owner-reviewed defaults, mirroring ADR-009's own per-question
  structure.
- Option C — resolve only the two-actor approval question now (the one
  every other question depends on), deferring role taxonomy and
  challenge-lifecycle specifics to a later, narrower ADR.

## Decision

**Option B**, per the owner's binding proposal for this draft — five
numbered decisions, mirroring the structure of the owner's own
instruction exactly.

### 1. Two-actor approval scope

Two distinct, `active`, in-scope actors (`RoleAssignment.actor_id`
values that differ, both currently `active` and scoped correctly for
the action in question) are **required** for:

- `GovernancePolicy` activation (`draft → active`).
- Every `GovernanceDecision` approval (`proposed → approved`), for
  every `decision_type` without exception.
- Ballot invalidation specifically — the `ballot_invalidation`
  `GovernanceDecision` that `voting-service.invalidate_ballot`
  (ADR-017) reads must itself already be two-actor approved before that
  command will act on it; the two-actor check is enforced once, at the
  `GovernanceDecision` layer, never re-implemented inside
  `voting-service`.
- Result-finality determination specifically — the
  `result_finality_determination` `GovernanceDecision` (ADR-018, D4/D6)
  requires the identical two-actor approval before
  `governance-service.get_finality_status` will ever report `final` or
  `invalidated` for the `ResultPublication` it concerns.

`SAME_ACTOR_APPROVAL_REJECTED` (ADR-019) is raised, not silently
corrected, whenever the same `RoleAssignment.actor_id` is supplied as
both proposer and approver for any of the above.

### 2. Technical-challenge submission eligibility (amended, Owner decision item 1)

- A `TechnicalChallenge` **may be submitted by an eligible participant
  or an explicitly authorized observer/reviewer** — submission does
  **not** require holding a governance decision-making role (i.e., a
  `role_code` from the §5 taxonomy's proposer/approver categories is not
  required to submit). This is deliberately more permissive than
  approval: raising an integrity concern about a published result
  should not itself be gated behind the same authority a ruling on that
  concern requires.
- **Aligned with ADR-018's amended `submitter_authorization_type`/
  `submitter_authorization_reference` model (Owner decision item 1):**
  - An **eligible participant** submits through a valid, ballot-scoped
    `ParticipationCredential` — `submitter_authorization_type =
"participation_credential"`.
  - An **authorized observer/reviewer** submits through an active,
    in-scope `RoleAssignment` — `submitter_authorization_type =
"role_assignment"` (typically `role_code = "observer"`, or another
    role for which submission is not itself the primary grant, per §5).
- **Adjudication and approval require governance roles** — only a
  `governance_reviewer` or `technical_challenge_reviewer`
  `RoleAssignment` (§5) may move a `TechnicalChallenge` to
  `under_review`, and only the two-actor approval flow (§1) may resolve
  the resulting `technical_challenge_adjudication` `GovernanceDecision`
  to `approved`/`rejected`.
- **Submitter identity remains restricted and is never public.**
  `TechnicalChallenge.submitter_authorization_reference` (ADR-018, D5,
  amended) is forbidden from appearing verbatim in any public-facing
  view, and no future Transparency-side publication of challenge
  outcomes (out of this pack's own scope) may expose it either — this
  restriction travels with the entity, not merely with this pack's own
  code.
- `TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE` (ADR-019) is raised when:
  a `role_assignment`-type submission's `RoleAssignment` is not
  `active` or not scoped to the relevant `Ballot`/`ResultPublication`
  (validated directly by `governance-service`, a local lookup); or a
  `participation_credential`-type submission fails whatever
  structural/format check `governance-service` can perform on an opaque
  reference without dereferencing it (ADR-018, D5's validation-boundary
  note — full credential validity is the referring caller's
  responsibility, not an upstream read this pack's dependency matrix,
  ADR-017, has ever included).

### 3. Multiple challenges against one result

- **Each `TechnicalChallenge` receives its own adjudication decision** —
  a `technical_challenge_adjudication` `GovernanceDecision` is always
  one-to-one with the specific challenge it rules on (ADR-018, D6);
  challenges are never batched into one shared ruling.
- **Exactly one aggregate `result_finality_determination` decision is
  created for a `ResultPublication`, after all of its submitted
  challenges are adjudicated** — never before, and never more than one
  standing, non-superseded aggregate ruling per `ResultPublication`
  (`RESULT_FINALITY_DETERMINATION_DUPLICATE`, ADR-019).
- **Finality is prohibited while any challenge remains unresolved**
  (`submitted` or `under_review`) —
  `RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE` (ADR-019) is raised on any
  attempt to create a `result_finality_determination` decision while
  this holds.
- **Contradictory finality decisions are forbidden** — once an
  `approved`, non-superseded `result_finality_determination` decision
  exists for a `ResultPublication`, no second, independent ruling may
  be created for the same `ResultPublication`.
- **Correction requires a new superseding decision, never mutation** —
  identical to ADR-018 D4's general immutability rule, restated here
  specifically for the finality-determination case since it is this
  pack's single highest-stakes decision type.

### 4. No-challenge path

- **After `challenge_deadline_at` elapses, an explicit, two-actor-
  approved `GovernanceDecision` (`result_finality_determination`) is
  still required to mark a result final.** The elapsed deadline is
  strictly a **precondition** for creating that decision (it makes
  finality determination newly permissible, alongside "no open
  challenges" — trivially true if none were ever submitted), never a
  trigger that determines finality automatically or implicitly.
- **Deadline expiry alone is never sufficient** — restating ADR-010's
  own prohibition ("no module may auto-declare finality") as a rule this
  pack's own `governance-service` must itself enforce, not merely avoid
  violating by omission. Absent an explicit `result_finality_determination`
  decision, `get_finality_status` (ADR-017) continues returning
  `provisional` indefinitely, however long past `challenge_deadline_at`
  the query occurs.

### 5. Role taxonomy — minimal closed pilot set

Per the owner's binding instruction, the following closed `role_code`
taxonomy is proposed for `GovernancePolicy`'s first
`policy_type = "role_taxonomy"` version (ADR-018, D3), rather than left
to ADR-020 owner review as an entirely open question (as
`docs/handover/PACK-05-SPEC.md` section 8 item 2 had originally
proposed leaving it):

| `role_code`                    | Grants authority to...                                                                                                                                                      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `governance_policy_proposer`   | Propose a new `GovernancePolicy` version (`draft`).                                                                                                                         |
| `governance_policy_approver`   | Approve a `GovernancePolicy` activation (`draft → active`); must differ from the proposer (§1).                                                                             |
| `governance_reviewer`          | Move a `GovernanceDecision` to `under_review`-equivalent scrutiny and participate in approving/rejecting `mandate`/`oversight_directive` decisions.                         |
| `technical_challenge_reviewer` | Move a `TechnicalChallenge` to `under_review` and participate in approving/rejecting `technical_challenge_adjudication` decisions.                                          |
| `ballot_invalidation_proposer` | Propose a `ballot_invalidation` `GovernanceDecision`.                                                                                                                       |
| `ballot_invalidation_approver` | Approve a `ballot_invalidation` `GovernanceDecision`; must differ from the proposer (§1).                                                                                   |
| `oversight_reviewer`           | Propose and participate in approving `oversight_directive` decisions (audits, directed reviews of other packs' decisions).                                                  |
| `observer`                     | No approval/proposal authority of any kind; may submit a `TechnicalChallenge` (§2) and read governance-service's own read-only endpoints; the baseline non-privileged role. |

**Who may grant each role, and the bootstrap rule:**

- In steady state, granting any `role_code` above `observer` requires an
  `active` `governance_policy_approver`-or-higher `RoleAssignment` to
  countersign the grant, itself represented as a `mandate`-type
  `GovernanceDecision` (two-actor approved, per §1) referencing the
  `RoleAssignment` being created — role grants are governance decisions
  like any other, not a separate, ungoverned side-channel.
- **No role may self-grant or approve its own assignment** — the
  identical INV-08 rule §1 already states, applied specifically to
  `RoleAssignment` creation/activation itself: the actor being granted a
  role may never also be the proposer or approver of the
  `GovernanceDecision` that grants it.
- **Bootstrap rule (amended, Owner decision item 2, now fully
  specified):** the very first `governance_policy_approver` and
  `ballot_invalidation_approver` `RoleAssignment`s cannot be
  countersigned by an existing governance authority, since none yet
  exists — this unavoidable cold-start problem is resolved as follows,
  per the owner's explicit mechanics (not left as this ADR's own
  under-specified proposal):
  - **Keep the two-distinct-actor bootstrap rule** — exactly two
    distinct initial actors are seeded, never one (which would make the
    very first grant unilateral, violating INV-08 at the one moment it
    matters most) and never seeded incrementally one at a time by an
    already-seeded actor acting alone.
  - **Implemented only through a dedicated deployment-time seed
    command, never through the normal API.** This is not a
    `governance-service` application-layer command reachable by any
    ordinary caller — it is a separate, purpose-built operation run
    once, out-of-band, at initial deployment (e.g. a standalone script,
    not an HTTP-reachable endpoint), structurally distinct from every
    other `RoleAssignment`-granting path in this pack.
  - **Requires exactly two distinct initial actors** — the seed command
    itself validates this at the moment it runs, refusing to proceed if
    given the same actor identifier twice.
  - **Produces an immutable seed manifest, checksum, and `AuditEvent`.**
    The seed command's own output is a manifest record (the two
    resulting `RoleAssignment` ids, the actors they belong to, and the
    seed operation's own timestamp), a checksum over that manifest (so
    the seed event itself is later verifiable, the same "provably
    unmodified" property `AuditExportPackage`'s `package_digest`
    already gives PACK-04's own exports), and a real `AuditEvent`
    recorded through `epd2_audit_core` exactly as every other critical
    action in this project is (CT-00-07) — the bootstrap is auditable
    from the moment it happens, not a silent, undocumented exception to
    this project's audit-everything rule.
  - **The seed command is permanently disabled after its first
    successful run.** Once exactly one successful seed has occurred,
    the command refuses to run again — there is no path to re-seeding
    or adding a third "founding" actor through this mechanism; any
    later addition to governance authority goes exclusively through the
    normal two-actor `mandate`-decision flow described below.
  - **No seeded actor may seed or approve their own assignment** — the
    seed command itself creates both `RoleAssignment` records
    atomically as part of the one seeding operation; neither seeded
    actor takes any action, as proposer or approver, to bring their own
    `RoleAssignment` into existence. This is the bootstrap-specific
    instance of the general "no role may self-grant or approve its own
    assignment" rule stated below.
  - **Every later role grant uses the normal two-actor governance flow**
    — including any additional `governance_policy_approver`, using the
    two seeded actors (or their properly-granted successors) as the
    initial authority. No second bootstrap-shaped exception is ever
    introduced.

Option A is rejected because it is exactly the "undocumented deviation"
canon section 26 exists to prevent, at the highest-stakes point in this
entire project (separation of authority itself). Option C is rejected
because the role taxonomy and challenge-lifecycle specifics are not
separable from the two-actor approval question in practice — the two-
actor rule is meaningless without a defined set of roles capable of
proposing and approving, and the challenge lifecycle is what the
two-actor rule concretely applies to for this pack's most complex
workflow.

## Consequences

`governance-service`'s first `GovernancePolicy` row (once implemented)
is the role taxonomy above, itself created and activated through the
now fully-specified bootstrap mechanism (§5, amended). Every
`RoleAssignment`-gated command in `governance-service` (and
`voting-service.invalidate_ballot`'s validation read, ADR-017) checks
against this taxonomy from day one, rather than an open-ended
`role_code` string space. The deployment-time seed command becomes a
required, one-time step in `governance-service`'s own initial
deployment procedure, to be documented in its `README.md` at
implementation time.

## Security impact

This ADR is, functionally, this pack's entire security model. The
bootstrap mechanism (§5, amended) is no longer this ADR's flagged-open
weak point — the owner's amendment fully specifies it as a one-time,
permanently-self-disabling, dual-actor, audited operation, structurally
distinct from and unreachable by the normal API, closing the gap the
original proposal could only flag rather than resolve. Every other rule
in this ADR (two-actor approval, no self-grant, submitter-identity
restriction, immutability of adjudicated challenges) is a direct,
enumerable security control. The amended challenge-submission model
(§2) is itself security-relevant: making participation-credential-based
submission possible without a `RoleAssignment` widens who may raise an
integrity concern, while ADR-018's validation-boundary note (D5)
ensures this does not implicitly reopen a credential-service dependency
this pack's boundary (ADR-017) never included.

## Data impact

No new canonical entity — this ADR only fixes the closed value set for
`RoleAssignment.role_code` (a repository-level taxonomy choice, not a
canon field-shape change), the initial content of `governance-
service`'s first `GovernancePolicy` row (ordinary data, not canon), and
the seed command's own manifest/checksum record (ordinary operational
data, not a canonical entity).

## Migration impact

None — no `governance-service` exists yet. The bootstrap seed command
described in §5 (amended) is itself the pack's own first, one-time
deployment step, to be fully implemented per this ADR's now-concrete
specification, not invented ad hoc at implementation time.

## Reversibility

The two-actor approval rule and role taxonomy are reversible with
significant cost once real `RoleAssignment`/`GovernanceDecision` data
exists — changing who may hold which role, or loosening the two-actor
requirement, would need its own future ADR and would affect every
already-granted role. The bootstrap mechanism itself is a one-time,
low-reversibility event by nature (it only ever happens once, at first
deployment).

## Related canon version

Authored against canon version `0.3.0`. Accepted with amendments per
Owner decision, above. Proposes no canon change itself — `role_code`'s
taxonomy is repository-side content, consistent with how canon 8.4
already leaves `role_code` as an open string rather than a
canon-enumerated value.
