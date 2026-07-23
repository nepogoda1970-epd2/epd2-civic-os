# CLAUDE-PACK-03 — Participation and Decision Kernel: Technical Specification

**Status: proposed, governance in progress.** This document specifies the
next implementation package. It is not itself an ADR and authorizes no
code; per canon section 26, every design decision below marked "requires
ADR" must reach `accepted` status before any corresponding working code
is written. **Update (2026-07-22): ADR-005, ADR-006, ADR-008, ADR-009,
and ADR-010 are now `accepted`** (ADR-009 and ADR-010 with amendments —
see each ADR's own "Owner decision" section and
`docs/review/PACK-03-OWNER-DECISIONS.md`). No PACK-03 service directory
or implementation code exists yet; this specification's section 8 items
13 and 14 below describe the _original_ proposal and are superseded by
ADR-009/ADR-010's accepted (amended) text where they differ.

## 0. Canon dependency

This pack depends on `docs/canonical/TZ-00-domain-event-canon.md`, which
may only be edited through a separate, dedicated task backed by its own
accepted ADR (this project's standing rule; canon section 26) — never
in-place for a pack's convenience:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a
CANON_VERSION = 0.2.0
```

This reflects the canon minor-version bump (`0.1.0 → 0.2.0`) performed
under ADR-010 (accepted with amendment, 2026-07-22): `Ballot.challenge_window_hours`
and `ResultPublication.challenge_deadline_at`, resolving ADR-009 item 13.
Any further change this pack needs from the canon (a new field, event,
status, or reason code) is likewise a **minor** version bump under canon
section 25 and must go through the ADR process (section 26) — never an
in-place edit of the canon document itself.

`REPOSITORY_VERSION` is expected to move `0.2.0 → 0.3.0` on acceptance of
this pack, tracked in the same three places PACK-02 tracked `0.2.0`
(`epd2_core/version.py`, `epd2-types/version.ts`, `CHANGELOG.md`,
`canon-version.json`).

## 1. Scope

PACK-03 implements six of the canon's twelve bounded contexts (section 5):

| Canon context                            | Section | In scope                           |
| ---------------------------------------- | ------- | ---------------------------------- |
| Initiative Context                       | 5.5     | Yes                                |
| Deliberation Context                     | 5.6     | Yes                                |
| Moderation Context                       | 5.7     | Yes                                |
| Voting Context                           | 5.8     | Yes                                |
| Tally Context                            | 5.9     | Yes                                |
| Delegation Context                       | 5.10    | Yes                                |
| Transparency Context                     | 5.11    | **No** — deferred                  |
| Governance Context                       | 5.12    | **No** — deferred                  |
| AI-processing (section 17)               | —       | **No** — deferred, same as PACK-02 |
| Emergency / Crisis Override (section 19) | —       | **No** — deferred, same as PACK-02 |

Identity, Eligibility, Credential, Account, and Audit (PACK-02) are
**consumed**, not reimplemented. PACK-03 services never own or duplicate
those entities; they call PACK-02's already-published application-layer
interfaces (section 6 of this document specifies exactly how).

Transparency and Governance are explicitly out of scope because both
contexts assume artifacts this pack produces (published results, audit
packages, moderation logs) already exist to publish or govern — they are
natural PACK-04/PACK-05 candidates, not because they are unimportant.
AI-processing and Emergency remain out of scope for the same reason
PACK-02 gave (`docs/review/OPEN_QUESTIONS.md` items carried forward): no
canon entity in this pack's scope requires `AIProcessingRecord` or
`EmergencyAction` to exist. CT-00-11 and CT-00-12 are therefore expected
to remain genuine **not-applicable** markers in this pack too (section 7).

## 2. Entities in scope

Fields, statuses, and prohibitions for every entity below are already
fully specified in the canon at the cited section — this pack does not
redefine them, only implements them.

| Entity             | Canon section | Canon-declared owner ("module")                                                             |
| ------------------ | ------------- | ------------------------------------------------------------------------------------------- |
| Initiative         | 11.1          | Initiative Service                                                                          |
| InitiativeVersion  | 11.2          | Initiative Service                                                                          |
| SupportRecord      | 11.3          | Initiative Service (implied — canon does not list a separate owner; see design decision D1) |
| Amendment          | 11.4          | Amendment Service                                                                           |
| SourceRecord       | 12.1          | Evidence Service                                                                            |
| Discussion         | 13.1          | Discussion Service                                                                          |
| Contribution       | 13.2          | Discussion Service                                                                          |
| ModerationCase     | 14.1          | Moderation Service                                                                          |
| ModerationDecision | 14.2          | Moderation Service                                                                          |
| Appeal             | 14.3          | Appeal Service                                                                              |
| Ballot             | 15.1          | Ballot Definition Service                                                                   |
| BallotOption       | 15.2          | Ballot Definition Service (implied — see D1)                                                |
| VoteEnvelope       | 15.3          | Vote Casting Service                                                                        |
| VoteReceipt        | 15.4          | Receipt Service                                                                             |
| Tally              | 15.5          | Tally Service                                                                               |
| ResultPublication  | 15.6          | Result Publication Service                                                                  |
| Delegation         | 16.1          | Delegation Service                                                                          |
| DelegationSnapshot | 16.2          | Delegation Resolution Engine                                                                |

18 entities across 12 distinct canon-declared "modules" (section 22's
ownership matrix). INV-02 requires one owner per entity — it does not
require one physical deployable per module, exactly as PACK-02 already
established precedent for (`Eligibility Engine` owns `EligibilityRule`,
`EligibilityDecision`, and `EligibilitySnapshot`, all inside the single
`eligibility-service`). Section 3 proposes the same kind of consolidation
here, with the rationale made explicit per entity.

## 3. Design decision D1 — service decomposition (requires ADR-005)

Proposed: six `uv` workspace services, each a canon-owner-module group
chosen so that no group crosses a canon-declared **forbidden link**
(section 23) or a Vote-Linkability boundary (CT-00-09):

1. **`services/initiative-service`** (`epd2_initiative_service`) —
   `Initiative`, `InitiativeVersion`, `SupportRecord`, `Amendment`,
   `SourceRecord`. Consolidates "Initiative Service", "Amendment
   Service", and "Evidence Service": all four entities besides
   `SourceRecord` share `initiative_id` as their natural key and the same
   status-workflow lifecycle (`draft → submitted → ... → adopted`);
   `SourceRecord` is folded in because canon section 5.5's own
   responsibility list for the Initiative Context explicitly includes
   "источники" (sources) — it is not a separate bounded context in
   section 5, only a separate _entity_ section (12) for readability.
2. **`services/deliberation-service`** (`epd2_deliberation_service`) —
   `Discussion`, `Contribution`. Canon already assigns both to one owner
   ("Discussion Service") — no consolidation decision needed here beyond
   naming the package.
3. **`services/moderation-service`** (`epd2_moderation_service`) —
   `ModerationCase`, `ModerationDecision`, `Appeal`. Consolidates
   "Moderation Service" and "Appeal Service". This is the one
   consolidation that touches an explicit canon prohibition — "Апелляцию
   не должен окончательно рассматривать автор исходного решения" (section
   14.3) — but that prohibition is a **role-separation** invariant (the
   deciding actor must differ), not a **service-separation** invariant;
   PACK-02 already enforces an analogous actor-role check
   (`actor_is_authorized`) at the application layer without a separate
   physical service per role. `moderation-service`'s appeal-decision path
   must assert `appeal.reviewer_actor_id != original_decision.decided_by`
   as a hard, tested precondition (CT-00-06 test, section 7) — the
   consolidation is safe only because that check exists and is exercised.
4. **`services/voting-service`** (`epd2_voting_service`) — `Ballot`,
   `BallotOption`, `VoteEnvelope`, `VoteReceipt`. Consolidates "Ballot
   Definition Service", "Vote Casting Service", and "Receipt Service".
   CT-00-09 (Vote Linkability) is a **data-shape** invariant — `VoteEnvelope`
   structurally cannot contain `account_id`/identity fields (canon
   section 15.3's explicit prohibition list) — enforced the same way
   PACK-02 enforced CT-00-08 for `ParticipationCredential`
   (`additionalProperties: false` + a forbidden-field-name test), not by
   splitting vote casting into its own deployable. Consolidating these
   three does not weaken that guarantee, since none of the three ever
   handles identity data to begin with.
5. **`services/tally-service`** (`epd2_tally_service`) — `Tally`,
   `ResultPublication`. Consolidates "Tally Service" and "Result
   Publication Service" (a tally's own `result_data` and a
   `ResultPublication`'s aggregate counts are two views of the same
   completed count; canon lists no reason to keep a WIP tally readable
   independent of its eventual publication).
6. **`services/delegation-service`** (`epd2_delegation_service`) —
   `Delegation`, `DelegationSnapshot`. Consolidates "Delegation Service"
   and "Delegation Resolution Engine" — a snapshot is a frozen resolution
   of the same service's own live delegation graph; there is no
   information in a `DelegationSnapshot` that legitimately needs a
   different owner than the `Delegation` records it resolves.

Result: six new services (bringing the monorepo total to eleven Python
workspace members plus `epd2-core`), the same order of magnitude PACK-02
added (five). Each gets its own `pyproject.toml`, `src/`, `tests/`,
`README.md`, and workspace-member entry in the root `pyproject.toml`
(mirroring the block already there for the five PACK-02 services).

**This decomposition itself must be ratified as ADR-005** before any
service directory is created — it is exactly the kind of "deviation" canon
section 26 requires an ADR for (it fixes a many-to-one mapping the canon's
own ownership matrix leaves open), and the ADR gives the project owner an
explicit point to override any of the six groupings above before code
exists that assumes them.

## 4. Design decision D2 — cross-pack integration boundary (requires ADR-008)

PACK-03 services must read PACK-02 state (a `ParticipationCredential`'s
validity, an `EligibilityDecision`, an `EligibilitySnapshot`'s digest) to
do their own job — `SupportRecord` needs a valid `initiative_support`
credential; `VoteEnvelope` needs a valid `ballot_access` credential;
`Ballot.eligibility_rule_version` needs to freeze against a real
`EligibilityRule` version. INV-03 ("no direct access to another's
database") forbids any PACK-03 service from importing a PACK-02 service's
storage module or reaching into its store directly.

Proposed resolution: PACK-03 services call PACK-02 services' existing
public `application`-layer functions in-process (e.g.
`epd2_credential_service.application.validate_participation_credential`),
exactly the same "call the other package's published function, never its
storage" shape `tests/repository/test_service_boundaries.py` already
enforces for `epd2_core`/`epd2_audit_core` access. This is a **new**
allowed edge in that boundary matrix (today no PACK-02 service calls
another PACK-02 service; every PACK-03 service will call at least one
PACK-02 service), so `test_service_boundaries.py`'s forbidden-pair matrix
must be extended, not just re-run, to encode:

- every PACK-03 service may import: itself, `epd2_core`, `epd2_audit_core`,
  and the specific PACK-02 application modules it legitimately depends on
  (to be enumerated per service in ADR-008, not left as "anything goes");
- no PACK-03 service may import another PACK-03 service's package (each
  of the six communicates only via canonical events, section 5, or a
  narrow, explicitly whitelisted read function — e.g. `tally-service`
  reading `voting-service`'s validated `VoteEnvelope` set requires its own
  named interface, not free access to every `voting-service` internal);
- no PACK-02 service may import any PACK-03 service (the dependency
  direction is one-way — PACK-02 remains ignorant of participation/
  decision concerns, consistent with it having shipped and passed
  verification before this pack exists).

This is a real architectural question, not a mechanical one, and is
flagged here rather than silently assumed: the current codebase has no
message bus (`docs/review/KNOWN_LIMITATIONS.md`), so "communicates via
canonical events" today means "calls a function that constructs and
returns/stores the same envelope a real event bus would carry later," not
an actual asynchronous transport. ADR-008 should say so explicitly and
record it as a known simplification consistent with PACK-01/02's own
documented scope, not a hidden shortcut.

## 5. Canonical events in scope

Already fully specified, canon section 20.6–20.11 — implemented verbatim,
no new event type invented without an ADR + minor version bump:

`initiative.draft_created`, `initiative.submitted`,
`initiative.revision_requested`, `initiative.published`,
`initiative.support_added`, `initiative.support_withdrawn`,
`initiative.qualified`, `initiative.deliberation_started`,
`initiative.legal_review_requested`, `initiative.ready_for_ballot`,
`initiative.withdrawn`, `initiative.archived`, `amendment.submitted`,
`amendment.published`, `amendment.accepted`, `amendment.rejected`,
`initiative.version_created`, `discussion.opened`,
`contribution.created`, `contribution.edited`, `contribution.flagged`,
`contribution.hidden`, `contribution.restored`, `discussion.closed`,
`moderation.case_opened`, `moderation.case_assigned`,
`moderation.decision_issued`, `moderation.decision_enforced`,
`moderation.appeal_submitted`, `moderation.appeal_decided`,
`ballot.created`, `ballot.configuration_locked`, `ballot.scheduled`,
`ballot.opened`, `ballot.paused`, `ballot.resumed`, `vote.received`,
`vote.validated`, `vote.rejected`, `vote.superseded`, `ballot.closed`,
`tally.started`, `tally.completed`, `tally.verified`, `result.published`,
`ballot.cancelled`, `ballot.invalidated`, `delegation.created`,
`delegation.activated`, `delegation.revoked`, `delegation.expired`,
`delegation.cycle_detected`, `delegation.snapshot_created`.

Every event uses the canon section 21 envelope verbatim (same shape
PACK-02's `epd2_core.event_envelope` already implements) — no new
envelope field, no relaxed idempotency rule.

## 6. Reason codes

Canon section 24 already declares nine codes this pack directly needs:
`BALLOT_NOT_OPEN`, `BALLOT_ALREADY_CLOSED`, `BALLOT_CONFIGURATION_LOCKED`,
`DUPLICATE_SUPPORT`, `DUPLICATE_VOTE`, `DELEGATION_CYCLE`,
`DELEGATION_EXPIRED`, `MODERATION_POLICY_VIOLATION`,
`APPEAL_DEADLINE_EXPIRED` — plus the pack reuses existing generic codes
(`PERMISSION_DENIED`, `EVENT_VERSION_UNSUPPORTED`,
`INTEGRITY_CHECK_FAILED`, `SERVICE_STATE_READ_ONLY`,
`EMERGENCY_FREEZE_ACTIVE`) exactly as PACK-02 did.

This pack will very likely need additive codes the canon does not yet
name — e.g. a self-delegation attempt, a competing-active-delegation
conflict for the same scope (canon section 16.1 prohibits both but names
no code), an initiative failing completeness review, a quorum or
threshold miss, a superseded amendment target. Follow the exact ADR-004
precedent: a new `contracts/reason-codes/pack-03.yml` registry
(`source: canon` entries copied verbatim, `source: pack-03-adr-006`
entries new and justified) under a new **ADR-006**, with the same
`ReasonCodeRegistry` structural validation and the same
"every `reason_code` literal used in a service is registered" contract
test PACK-02 already has (`test_reason_codes_registry.py`, extended to
scan the six new services too).

`docs/review/OPEN_QUESTIONS.md` item 10 (PACK-02's 21 additive codes
never folded back into canon section 24) is still open. This pack adding
a second additive layer is a natural point to revisit that recommendation
— not required for this pack's own Definition of Done, but worth the
project owner's attention before a third additive layer makes the
divergence between "canon section 24" and "what the registry actually
contains" harder to reconcile later.

## 7. Contract tests

All twelve CT-00 tests (canon section 27) apply; most already have a
PACK-02 implementation pattern to extend rather than invent from scratch.

- **CT-00-01 Schema Validation** — a JSON Schema per entity in section 2,
  `additionalProperties: false` throughout, same as every PACK-02 schema.
- **CT-00-02 Unknown Status** — every status enum in section 2 rejects an
  unlisted value.
- **CT-00-03 Forbidden Transition** — state machines for `Initiative`
  (15 statuses), `Ballot` (11 statuses — critically: `closed` never
  returns to `open`, `tallying`/`tallied` never precede `closed`),
  `ModerationCase`/`Appeal`, and `Delegation`. PACK-02 has no precedent
  this large (its own state machines were simpler); budget real design
  time for the transition tables themselves, not just the test harness.
- **CT-00-04 Event Idempotency** — every new command accepts a
  caller-supplied `event_id`/idempotency key, the same shape
  `issue_participation_credential` already uses. This pack should close
  `docs/review/OPEN_QUESTIONS.md` item 11 (PACK-02 left this asymmetric
  across its own four services) by applying the pattern uniformly to
  every PACK-03 command from the start, not just the one canon calls out
  by name (`vote.received` — CT-00-04 is explicitly about duplicate
  `event_id` delivery, and a duplicate vote submission is the single
  highest-stakes idempotency case in this entire pack).
- **CT-00-05 Unsupported Event Version** — unchanged mechanism, exercised
  against the new event types in section 5.
- **CT-00-06 Missing Permission** — role/actor checks, most notably the
  appeal-reviewer-≠-original-decider check from section 3's D1 discussion,
  and a ballot's configuration-approval step (design decision D3, section
  8, item 7).
- **CT-00-07 Audit Creation** — every critical action in this pack
  (support added/withdrawn, vote received/validated, ballot closed, tally
  completed, result published, moderation decision issued, appeal
  decided, delegation created/revoked) writes an `AuditEvent` through
  `epd2_audit_core`, exactly as every PACK-02 service already does.
- **CT-00-08 Identity Leakage** — extended to every new entity's schema
  and OpenAPI path: `VoteEnvelope`/`VoteReceipt`/`Tally`/
  `ResultPublication`/`SupportRecord`/`Delegation` must never declare
  `account_id`/`identity_record_id`/`person_id`. The credential-service
  scoping helpers PACK-02 wrote this pass
  (`_credential_service_paths`/`_referenced_local_schema_names`/
  `_declared_property_names` in `tests/contract/test_ct00_08_identity_leakage.py`)
  should be generalized into a reusable, service-tag-parameterized helper
  rather than copy-pasted six more times — a genuine refactor opportunity
  this pack should take, not defer.
- **CT-00-09 Vote Linkability** — the pack's signature new test: prove
  that no code path in `voting-service` or `tally-service` can resolve a
  `VoteEnvelope` to an `Account`. Concretely: `VoteEnvelope.credential_proof`
  must reference a `ParticipationCredential` (itself already
  structurally identity-free per PACK-02's CT-00-08), never an
  `account_id` directly; a positive-space regression test (mirroring
  `test_identity_service_paths_may_reference_identity_record_id`'s
  pattern) should confirm the reverse lookup genuinely has no code path,
  not merely that no field exists.
- **CT-00-10 Rule Freeze** — after `Ballot.status` reaches
  `configuration_review` (or later), `configuration_hash`-covered fields,
  `BallotOption` rows, `eligibility_rule_version`, and
  `delegation_policy_version` become immutable; this is the direct
  cross-pack link to PACK-02's `EligibilitySnapshot` ("After opening a
  vote, the rule version used is frozen" — canon section 9.1), so this
  test should assert the freeze against a real `EligibilitySnapshot`
  digest, not a bare version number.
- **CT-00-11 AI Human Control** — expected **not applicable** again (no
  `AIProcessingRecord` in this pack's scope, section 1). Carry forward
  `test_ct00_11_12_not_applicable.py`'s pattern with an updated
  pack-specific justification string, exactly as PACK-02 did for PACK-01's
  version of the same file.
- **CT-00-12 Emergency Stop** — expected **not applicable** again (no
  `EmergencyAction` in this pack's scope), same treatment.

## 8. Design decision D3 — defaults for canon section 29's open questions (requires ADR-009)

Canon section 29 lists fifteen questions explicitly reserved for "before
the Voting package" — `docs/review/OPEN_QUESTIONS.md` item 7 already
notes they exist and are the project owner's to decide, not
Claude Code's. This section proposes a conservative, fail-closed default
for each, so implementation is not blocked on the project owner's
response, but **every default below is a proposal for ADR-009, not a
decision already made** — the ADR must be reviewed and accepted (or
overridden) before the corresponding code ships.

1. **Can a participant change their vote before close?** Proposed: yes.
   `VoteEnvelope.status` already has a `superseded` value for exactly
   this; only the latest valid envelope per credential counts.
2. **Which choice counts on a vote change?** Proposed: the most recent
   valid `VoteEnvelope` received strictly before `Ballot.closes_at`.
3. **Is abstention a distinct option?** Proposed: yes, modeled as an
   explicit `BallotOption` (e.g. `option_code = "abstain"`), never
   inferred from a missing vote — keeps abstention auditable and
   quorum/threshold math explicit rather than implicit.
4. **Which voting methods are in the pilot?** Proposed: start with
   single-choice / yes-no only (`ballot_method` restricted to a minimal
   enum this pass); ranked-choice or multi-select is a minor-version
   addition once the simpler case is proven end-to-end.
5. **Is quorum required for every procedure?** Proposed: no — `Ballot`'s
   existing `quorum_rule` field is already optional/per-ballot; default
   to "no quorum requirement" unless a specific ballot configures one.
6. **Who may create a ballot?** Proposed: gated by `RoleAssignment` (a
   role scoped to the relevant `CivicSpace`), never a bare `Account` —
   mirrors PACK-02's existing `actor_is_authorized` pattern.
7. **Who approves final ballot parameters?** Proposed: a second,
   distinct authorized actor from the one who created it, required for
   the `configuration_review → scheduled` transition — a direct
   application of INV-08 ("critical actions require separation of
   authority") to this specific transition, and the concrete case CT-00-06
   (section 7) should test.
8. **Is delegation enabled in the first pilot?** Proposed: implement the
   `Delegation`/`DelegationSnapshot` entities and service fully (canon
   requires them in this pack's scope regardless), but default new
   `Ballot`s to `delegation_policy_version = null` (delegation resolution
   disabled) for the first real ballot type — enabling it is a
   per-ballot-type configuration choice, not an all-or-nothing repository
   switch.
9. **Maximum delegation depth?** Proposed: a small, explicit bounded
   constant (e.g. depth 1 — no re-delegation chains) for the pilot,
   configurable later; an unbounded depth is exactly what
   `delegation.cycle_detected`/`DELEGATION_CYCLE` exist to guard against,
   but a hard depth cap is cheaper to reason about than pure cycle
   detection alone and the two are not mutually exclusive.
10. **Can a delegator override their delegate for one ballot?** Proposed:
    yes — a delegator's own valid `VoteEnvelope` for that `Ballot`,
    received before `DelegationSnapshot` resolution closes, takes
    precedence over any vote cast by their delegate using that
    delegation for that same ballot. This needs a precise ordering rule
    at implementation time and should be spelled out fully in ADR-009,
    not left to code comments.
11. **How are ties handled?** Proposed: no silent tie-break. A tied
    result is recorded as its own explicit `ResultPublication` outcome
    (e.g. `threshold_result = "tie_no_decision"`) rather than resolved by
    an undocumented default rule; any specific tie-break method must be
    an explicit, documented per-ballot `threshold_rule` configuration,
    never an implicit fallback.
12. **When is a result final?** Proposed: after `ResultPublication.published_at`
    plus the technical-challenge window (item 13) elapses with no
    accepted integrity challenge; before that, the result is
    tallied-but-provisional and should be represented as such (not
    silently equated with "final").
13. **Technical-challenge deadline?** Proposed: a configurable fixed
    window (e.g. 72 hours) after publication — canon has no existing
    field for this; adding one is a minor canon version bump and must go
    through the ADR process, not be hardcoded ad hoc.
14. **Who may invalidate a ballot?** Proposed: a Governance/Crisis-scoped
    role only, requiring two-actor approval (mirrors item 7 / INV-08) —
    this properly belongs to the Governance Context (5.12), which is out
    of this pack's scope (section 1); until that context exists, gate it
    behind an explicit, narrowly-scoped `RoleAssignment` role and document
    it as provisional pending PACK-05+.
15. **What audit-package data is published openly?** Proposed:
    `ResultPublication`'s aggregate counts (`eligible_count`,
    `credential_count`, `accepted_vote_count`, `rejected_vote_count`,
    `quorum_result`, `threshold_result`) plus a redacted audit-chain proof
    (hashes, not full `AuditEvent` payloads) — never individual
    `VoteEnvelope` contents or anything identity-linked. Full public
    disclosure design belongs to the Transparency Context (5.11, out of
    this pack's scope per section 1); this is only the minimum this pack
    itself must expose to make CT-00-09/CT-00-10 independently verifiable.

## 9. Definition of Done

Mirrors PACK-01/02's own Definition of Done, extended for this pack's
scope:

1. ADR-005 (service decomposition), ADR-006 (reason-code additions),
   ADR-008 (cross-pack integration boundary), and ADR-009 (section-29
   defaults) all reach `accepted` status before the corresponding code is
   written (canon section 26).
2. All six services exist as independent `uv` workspace members with
   their own `pyproject.toml`, `src/`, `tests/`, `README.md`.
3. Every entity in section 2 has a JSON Schema
   (`contracts/schemas/*.json`, `additionalProperties: false`) and, where
   it is produced by an event, an event-payload schema
   (`contracts/events/*.v1.schema.json`).
4. `contracts/openapi/pack-03.yaml` documents every new service's paths,
   tagged per service, following the exact tagging convention
   `_credential_service_paths` (PACK-02) already established.
5. `contracts/reason-codes/pack-03.yml` exists, structurally validated,
   and every `reason_code` literal used anywhere in the six new services
   is registered in it.
6. All twelve CT-00 tests pass for this pack's scope (section 7); CT-00-11
   and CT-00-12 remain genuine, documented not-applicable markers.
7. `tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
   is extended (not just re-run) to cover the six new services and the
   new PACK-03→PACK-02 dependency edges from design decision D2.
8. `scripts/check_repository.py`'s `REQUIRED_PATHS` is extended for every
   new required path; `scripts/check_forbidden_files.py` is re-run
   unchanged (or extended, if a new forbidden-file heuristic is needed)
   against the larger tree.
9. `REPOSITORY_VERSION` bumped `0.2.0 → 0.3.0`, canon SHA-256 unchanged,
   `docs/handover/PACK-03-REPORT.md` written following the same
   revision-by-revision, honest-verification structure
   `docs/handover/PACK-02-REPORT.md` used (including documenting any real
   bug external GitHub Actions verification finds, exactly as happened
   four times during PACK-02 — that is the expected, healthy pattern, not
   a failure to avoid).
10. `uv.lock`/`package-lock.json` regenerated for real (this sandbox's
    network restriction, section 1 of PACK-02's report, is expected to
    still apply — plan for the same GitHub Actions remediation path from
    the start rather than rediscovering it).
11. Exactly one clean canonical archive exported at the end
    (`epd2-civic-os-PACK-03-PASS.zip` or equivalent), with no manual
    GitHub edits required — `.github/workflows/verify-and-package.yml`
    needs no pack-specific change, since it is already pack-agnostic
    (PACK-02 section 0c).

## 10. Explicitly not addressed by this specification

- Exact API request/response shapes (OpenAPI paths) — implementation
  detail, not a design decision, deferred to the pack's own
  implementation pass, same as PACK-02's own spec-vs-implementation split.
- Cryptographic vote-secrecy mechanism (e.g. real mixnets, homomorphic
  tallying, threshold decryption) — `VoteEnvelope.encrypted_or_encoded_choice`
  is a canon field name, not a canon-mandated algorithm; this pack's
  Definition of Done (section 9) requires only the **structural**
  linkability guarantee (CT-00-09), consistent with
  `docs/architecture/identity-participation-separation.md`'s existing,
  explicit statement that PACK-02's guarantee is structural, not
  cryptographic-anonymity. A real cryptographic voting scheme, if ever
  required, is its own future ADR and almost certainly its own pack.
- Frontend/UI work for any of these six services — `frontend/web-shell`
  is unchanged by this specification; wiring it up is a separate,
  later task exactly as it was left out of PACK-02.
