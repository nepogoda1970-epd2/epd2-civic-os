# CLAUDE-PACK-05 — Governance Context: Technical Specification

**Status: proposed.** This document specifies the next candidate
implementation package. It is not itself an ADR and authorizes no code.
Per canon section 26, every design decision below marked "requires ADR"
must reach `accepted` status before any corresponding working code is
written. **No PACK-05 service directory, schema, contract, or
implementation code exists yet** — this specification is the entire
PACK-05 deliverable at this stage.

This pack is different in kind from both PACK-03 and PACK-04. PACK-03
implemented entities canon had already fully defined; PACK-04 proposed
entirely new entities for a context canon only sketched in prose
(5.11). PACK-05 is **both at once, entity by entity**: one in-scope
entity (`RoleAssignment`, canon 8.4) is already fully defined and has
never been implemented; the rest of canon's Governance responsibility
list (5.12 — system roles, authority policy, rules versioning, audit
access, review procedures) has no formal entity at all and must be
proposed the same way PACK-04 proposed `PublicLedgerEntry`. Sections
3–8 below are marked accordingly, entity by entity, rather than
uniformly.

This pack is also the first to propose a **write edge** into two other
packs' owned entities (`Ballot`, `ResultPublication`) rather than a
purely read-only edge — flagged up front because it is this
specification's single most consequential open decision (section 5,
D2), stated as directly as ADR-009/010 already state it must be
resolved: those two ADRs explicitly deferred ballot-invalidation
authorization and result-finality determination to "a future
Governance service" / "a future Governance pack" and this is that
pack's specification.

## 0. Canon dependency

**Update, 2026-07-23:** this specification was originally authored
against canon `0.3.0` (checksum
`9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad`),
stating that canon "was not opened for editing to produce this
specification" and "would move `0.3.0 → 0.4.0`" only if design decision
D3/ADR-018 (and ADR-020, for its own repository-side content) were
accepted. ADR-018 and ADR-020 have since been accepted (both with
amendments) and ADR-018's canon-edit task carried out as its own
separate, dedicated step (canon section 26's precondition) — the
current canon dependency is now:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  61232dc8488f1dd96ea030fa3c41bd397c1c5cf1c7c8cee484bda0568d02c202
CANON_VERSION = 0.4.0
```

Canon section 19b, section 20.15, and three new section 22 rows now
formally define `GovernancePolicy`, `GovernanceDecision`, and
`TechnicalChallenge` — the canon-silence finding this section originally
documented (below) is resolved for these three entities specifically,
and `RoleAssignment` (8.4) is now fully integrated alongside them. This
specification document itself is not being retroactively rewritten into
an implementation plan; sections 1–17 below remain as originally
authored and should be read as the proposal that led to ADR-016–020 and
the now-completed canon edit, not as a description of already-built
service code (`governance-service` still does not exist).

`REPOSITORY_VERSION` (currently `0.4.0`, PACK-04 PASS) is not touched by
this canon edit. It would move to `0.5.0` only once PACK-05
implementation code actually lands — the two version numbers would
briefly coincide again, as they did transiently around PACK-04, but
remain tracked independently, per this repository's own established
convention (root `README.md`).

## 1. Scope — context separation

The user's request for this pack is explicit that Governance,
Transparency, AI-processing, and Emergency/Crisis Override must be kept
conceptually distinct and never silently combined. The table below is
that separation, checked directly against canon sections 5.11/5.12/17/19:

| Canon context / concern                         | Canon section | In PACK-05 scope                                        | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------------------- | ------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Governance Context                              | 5.12          | **Yes**                                                 | This pack's entire subject — system roles, authority policy, rules versioning, audit access, review procedures. **Except** the two items named explicitly below, which stay excluded even though 5.12 lists them.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Transparency Context                            | 5.11          | **No**                                                  | PACK-04, already implemented and PASSed. PACK-05 does not read from or write to `transparency-service`; nothing proposed here needs a public-ledger read, and Governance decisions becoming public is a future Transparency-side publication concern, not this pack's.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| AI-processing (`AIProcessingRecord`)            | 17.1          | **No**                                                  | No entity proposed in section 3 requires an `AIProcessingRecord` to exist. "Review procedures" (5.12) means human oversight/review of governance and moderation actions, not AI output review (canon 17's own subject) — see section 8's exclusion detail.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Emergency / Crisis Override (`EmergencyAction`) | 19/19.1       | **No, explicitly excluded per this task's instruction** | Canon 5.12 lists "emergency procedures" and "crisis override" as Governance responsibilities, and canon section 22 already labels `EmergencyAction`'s owner **"Governance / Crisis Service"** — textually, canon anticipates one combined service. This specification deliberately does **not** propose implementing `EmergencyAction` or any emergency workflow now, per the user's explicit instruction to keep Governance and Emergency/Crisis Override separate unless canon requires a hard dependency. No entity proposed in section 3 requires `EmergencyAction` to exist, so no hard dependency exists — see the canon-silence/naming finding in section 2 for the full analysis of this specific tension. |

**Why Emergency is not a hard dependency for PACK-05**, checked
explicitly per the user's requirement not to silently combine the two:

- None of the four entities proposed in section 3 (`RoleAssignment`
  implementation, `GovernancePolicy`, `GovernanceDecision`,
  `TechnicalChallenge`) reads, writes, or references `EmergencyAction`
  in any field.
- "Crisis override" and "emergency procedures" in canon 5.12 describe a
  distinct, time-boxed, higher-urgency mechanism (platform read-only,
  credential-issuance pause, ballot pause/cancel, forced logout,
  credential revocation, service isolation, evidence preservation —
  canon 19.1's eight `EmergencyAction` types) with its own status
  machine and its own two-independent-confirmations rule already fully
  specified in canon. None of PACK-05's proposed governance workflows
  (role assignment, policy adoption, ballot-invalidation authorization,
  technical-challenge adjudication, result-finality determination) is a
  type of `EmergencyAction`, nor does any of them require one to exist
  first.
- The one real tension — canon section 22 already names the _future_
  owner of `EmergencyAction` "Governance / Crisis Service", implying a
  single combined service — is a naming/decomposition question for a
  **future** pack to resolve (section 13), not a scope justification for
  folding `EmergencyAction` into this pack's implementation now. This
  specification's own service-decomposition proposal (section 4) is
  named `governance-service`, deliberately left open as to whether a
  later Emergency/Crisis pack extends this same physical service or
  introduces its own — an explicit open question, not a silent decision,
  exactly as this task requires.

AI-processing is excluded for the same reason PACK-02, PACK-03, and
PACK-04 all gave (`docs/review/OPEN_QUESTIONS.md` item 7 notes canon
section 29's own deferral list; no pack to date has needed
`AIProcessingRecord`): no entity actually proposed in this pack's scope
needs it. CT-00-11 is expected to remain a genuine **not-applicable**
marker a fourth time; CT-00-12 likewise, since `EmergencyAction` stays
excluded here (section 10).

## 2. Canon-textual basis and canon-silence findings

Everything canon actually says about the Governance Context, quoted in
full because — as with PACK-04's own 5.11 — there is not much more to
quote:

> **5.12. Governance Context** — Ответственность: системные роли;
> политика полномочий; версии правил; emergency procedures; crisis
> override; audit access; review procedures.

Unlike PACK-04's `PublicLedgerEntry`, one Governance-relevant entity
**is** already fully defined, with fields and a status enum, even though
canon does not group it under a "5.12" heading anywhere in its own
entity-definition sections:

> **8.4. RoleAssignment** — Поля: `role_assignment_id`, `actor_id`,
> `role_code`, `scope_id`, `valid_from`, `valid_until`, `assigned_by`,
> `approval_reference`. Статусы: `pending`, `active`, `suspended`,
> `expired`, `revoked`.

And the ownership matrix (section 22) already assigns it an owner,
distinct from the `governance-service` this pack proposes:

> **Section 22** — `RoleAssignment → Permission / Role Service`

A second entity, `EmergencyAction` (19.1), is also fully defined and
already carries an owner label naming Governance explicitly —
`EmergencyAction → Governance / Crisis Service` — but is excluded from
this pack's scope regardless (section 1).

Checked systematically against every other place canon defines entity
detail or process, and confirmed absent for the rest of Governance's
5.12 responsibilities:

- **Sections 7–19 (entity definitions)** — no section defines a
  `GovernancePolicy`/authority-rules-version entity, a
  governance-decision or mandate entity, or a technical-challenge
  entity. `RoleAssignment` (8.4) and `EmergencyAction` (19.1) are the
  only two Governance-adjacent entities canon defines; "версии правил"
  and "review procedures" have no corresponding entity anywhere.
- **Sections 20.1–20.14 (canonical event catalog)** — fourteen
  per-context event lists exist (Account through Transparency, added by
  ADR-013). **None is for Governance.** Zero Governance events are
  canonically named anywhere in this document — not even for
  `RoleAssignment`, despite that entity's fields being fully specified.
- **Section 22 (ownership matrix)** — 31 entities are listed with their
  owning module. `RoleAssignment` and `EmergencyAction` both appear;
  no `GovernancePolicy`/decision/challenge entity does, because none is
  yet canonically named.
- **Section 23 (forbidden links)** — one directly relevant, previously
  unexamined entry: `AdministratorRole → право расшифровать тайные
голоса` ("the right to decrypt secret votes"). **`AdministratorRole`
  is never formally defined anywhere else in canon** — it appears in
  exactly this one forbidden-link line, with no field list, no status
  enum, and no entry in section 22's ownership matrix. It is not
  textually stated whether `AdministratorRole` is meant to be a
  `RoleAssignment.role_code` value (e.g. `"administrator"`), a
  structurally distinct entity, or informal prose shorthand. This is a
  genuine canon-silence finding this specification surfaces rather than
  resolves — proposed as an explicit open item for D3/ADR-018 (section 6) to settle, since any Governance implementation that grants an
  "administrator"-shaped role must know which of these three canon
  actually means before INV-06 (vote secrecy) can be enforced against
  it structurally.
- **Section 24 (reason-code standard)** — the fixed canon list has no
  codes scoped to role assignment, policy adoption, governance decision,
  or technical challenge.
- **Section 27 (CT-00 contract tests)** — exactly twelve tests are
  defined (CT-00-01 through CT-00-12); canon reserves no additional
  numbers for a Governance-specific test. Section 10 below maps existing
  CT-00 tests onto this pack's proposed scope rather than proposing new
  ones.
- **Section 29 (open questions before Voting)** — items 12–14 are
  Governance-shaped and were already partially resolved by ADR-009/010,
  each explicitly naming a future Governance pack as the place the
  remainder must be decided:
  - Item 12, "Когда результат считается окончательным?" — ADR-009
    proposed, accepted: final only after `challenge_deadline_at` elapses
    with **no accepted integrity challenge**; ADR-010 (accepted, with
    amendment) added the `challenge_deadline_at` field itself and
    stated explicitly that expiry is "necessary, but not by itself
    sufficient" for finality, and that **no module may auto-declare
    finality** until a technical-challenge registration/adjudication
    mechanism exists. This is section 11's direct mandate.
  - Item 13, "Какой срок предусмотрен для технического оспаривания
    результата?" — resolved by ADR-010: `challenge_window_hours` on
    `Ballot`, default 72 hours, `ResultPublication.challenge_deadline_at`
    computed from it. The **mechanism** itself (registration,
    adjudication) was explicitly left to "its own ADR" — this pack's
    section 10.
  - Item 14, "Кто вправе признать голосование недействительным?" —
    ADR-009 (amended, accepted): PACK-03 implements the canonical
    `invalidated` `Ballot` status structurally (so CT-00-02/03 can be
    tested against it) but **no PACK-03 command may ever reach it**.
    "Authorization and two-actor approval for invalidation belongs
    entirely to the future Governance service" — this pack, verbatim.

**Conclusion, stated plainly for the record:** this pack has a stronger,
more explicit canon and ADR mandate than PACK-04 had at its own
specification stage — two prior, already-accepted ADRs name this exact
pack as the place their own deferred decisions must land. What canon
itself is silent on is the same shape of gap PACK-04 found in 5.11: a
responsibility list (5.12) with almost no formal entity backing it, one
partially-defined stray reference (`AdministratorRole`) with no
definition at all, and zero reserved event names. Section 6's canon
addition proposal is this pack's ADR-013-equivalent — the project owner
should read it, and the write-boundary question in section 5, before
any other design decision in this document.

## 3. Proposed entities in scope

| Entity               | Canon status                                         | Rationale                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Modeled after                                                                                                    |
| -------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `RoleAssignment`     | **Already fully defined** (canon 8.4), unimplemented | Implements canon's existing entity exactly as specified — fields, statuses, and owner (`Permission / Role Service`, section 22) are not proposals, they are canon text this pack would finally build. Every other entity below, and every existing PACK-03/04 `actor_is_authorized`/`RoleAssignment`-gated check, depends on a real implementation existing somewhere.                                                                                                                                                                                      | N/A — canon-defined already                                                                                      |
| `GovernancePolicy`   | **Not named in canon** — proposal                    | Covers 5.12's "политика полномочий; версии правил" (authority policy; rule versions) — a versioned, activatable policy record, the Governance-context analogue of PACK-04's `DisclosurePolicy` (`draft → active → superseded`, at most one active version per scope at a time).                                                                                                                                                                                                                                                                             | `DisclosurePolicy` (canon 19a.3, versioned activation pattern)                                                   |
| `GovernanceDecision` | **Not named in canon** — proposal                    | Covers 5.12's "review procedures" plus the user's "governance decisions and mandates," "ballot invalidation authorization," and "oversight and review workflows." One entity with a `decision_type` discriminator (`ballot_invalidation`, `result_finality_determination`, `mandate`, `oversight_directive`) rather than four near-duplicate entities — the same consolidation reasoning PACK-04-SPEC.md section 3 used for `PublicLedgerEntry`'s `subject_type`. Every `decision_type` requires the two-actor approval INV-08 already demands (section 9). | `PublicLedgerEntry` (canon 19a.1, discriminator pattern); `EmergencyAction` (19.1, `initiated_by`/`approved_by`) |
| `TechnicalChallenge` | **Not named in canon** — proposal                    | Directly implements the mechanism ADR-009 item 13 and ADR-010 both name as still-missing: registration of a challenge against a `ResultPublication` before `challenge_deadline_at`, and its adjudication. A challenge's `upheld` outcome is what triggers a `GovernanceDecision` of type `result_finality_determination` (section 11) — the two entities are deliberately kept distinct (challenge intake vs. governance ruling) rather than merged, mirroring how `ModerationCase`/`ModerationDecision` are kept distinct in canon 14.                     | `ModerationCase` → `ModerationDecision` (intake/ruling split)                                                    |

Two things are **deliberately not proposed as separate entities**,
per this section's own consolidation reasoning:

- **Two-actor approval** is not its own entity — it is a cross-cutting
  invariant (INV-08) implemented as a required second, distinct
  `RoleAssignment`-holding actor on every `GovernanceDecision` and every
  `GovernancePolicy` activation, mirroring `EmergencyAction`'s existing
  `initiated_by`/`approved_by` field pair and canon's own "два
  независимых подтверждения" (two independent confirmations) rule
  (19.1). Section 9 makes this rule explicit and operational.
- **Oversight and review workflows** are not a separate entity — they
  are one more `GovernanceDecision.decision_type` value
  (`oversight_directive`), not a fifth proposed entity, for the same
  reason `PublicLedgerEntry` did not need five subject-specific entity
  types in PACK-04.

Every field list for these entities is deliberately **not** written out
in this specification, for the same reason PACK-04-SPEC.md section 3
gave: per canon section 26 and this project's standing rule, inventing
entity field lists is exactly the kind of canon content that must be
drafted, reviewed, and accepted _as_ an ADR (ADR-018, section 6) before
it has any authority. `RoleAssignment`'s fields are the one exception —
they are not proposed here, they are quoted verbatim from canon 8.4
above, and implementing them requires no canon edit at all, only
ADR-016 (service decomposition, section 4).

## 4. Design decision D1 — service decomposition (requires ADR-016)

Proposed: **one** new service, following the same "one group per set of
entities with no forbidden-link or ownership conflict" test PACK-03 and
PACK-04 both applied:

- **`services/governance-service`** (`epd2_governance_service`) —
  `RoleAssignment`, `GovernancePolicy`, `GovernanceDecision`,
  `TechnicalChallenge`. All four are authority/adjudication records with
  comparable lifecycle complexity to `ModerationCase`/`ModerationDecision`
  (PACK-03's two-entity moderation pair) — a single service is
  proportionate, and keeps the two-actor approval invariant (section 9)
  enforceable in one place rather than duplicated across services.

**Explicitly left open, not decided by this specification:** whether a
later Emergency/Crisis Override pack extends this same physical
`governance-service` (since canon section 22 already labels
`EmergencyAction`'s owner "Governance / Crisis Service", suggesting one
combined service) or introduces its own `emergency-service`. This
specification takes no position — deciding it now would risk exactly the
"silently combine Governance and Emergency" outcome the user's
instruction forbids. Whichever future pack implements `EmergencyAction`
should make this decomposition call explicitly, informed by whatever
`governance-service` actually looks like once PACK-05 ships, not
pre-committed today.

This is a comparably small service surface to PACK-04's own single
service, proportionate to a pack whose core job is authorizing and
recording decisions about other packs' entities rather than owning a
large data model itself. **This decomposition must be ratified as
ADR-016** before any service directory is created, exactly as ADR-011
was required before PACK-04's first service directory.

## 5. Design decision D2 — cross-pack dependency matrix and the ballot/result write-boundary question (requires ADR-017)

`governance-service` needs read access to state two other packs' services
already own, and — unlike every previous pack's cross-pack ADR — needs to
_cause a state change_ in entities it does not own (`Ballot.status →
invalidated`; a new finality-shaped field on `ResultPublication`).
This is the pack's most consequential open decision, more so than D1,
because it is the first time this project's established one-way,
read-only cross-pack boundary (ADR-008, ADR-012) does not, by itself,
describe how the actual required behavior — an authorized governance
ruling actually changing another service's entity — can happen at all.

**Read edges, proposed (uncontroversial, same pattern as ADR-008/012):**

| Upstream service                                                                         | Pack    | Read for                                                                                                                                         | Included?                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `voting-service`                                                                         | PACK-03 | `get_ballot` (already exists, ADR-012-sanctioned) — confirm a `Ballot`'s current status/existence before authorizing invalidation                | **Yes** — read-only, reuses an existing sanctioned function                                                                                                                                                                                          |
| `tally-service`                                                                          | PACK-03 | `get_result_publication` (already exists, ADR-012-sanctioned) — read `challenge_deadline_at` and current state for challenge intake/adjudication | **Yes** — read-only, reuses an existing sanctioned function                                                                                                                                                                                          |
| `epd2_audit_core`                                                                        | PACK-02 | `list_by_target_types` (already exists, added by PACK-04) — read governance-relevant audit history for oversight/review `GovernanceDecision`s    | **Yes** — read-only, reuses an existing sanctioned function                                                                                                                                                                                          |
| `transparency-service`                                                                   | PACK-04 | —                                                                                                                                                | **No** — nothing proposed in section 3 needs to read the public ledger; a `GovernanceDecision` becoming publicly visible is a future Transparency-side publication concern (its own `PublicLedgerEntry.subject_type` addition, not this pack's read) |
| `initiative-service`, `moderation-service`, `deliberation-service`, `delegation-service` | PACK-03 | —                                                                                                                                                | **No** — no entity proposed in section 3 needs initiative, discussion, moderation, or delegation data directly                                                                                                                                       |
| `credential-service`, `identity-service`, `account-service`, `eligibility-service`       | PACK-02 | —                                                                                                                                                | **No** — hard exclusion, same reasoning ADR-012 gave: nothing proposed here needs identity or credential data, and excluding these four entirely is a stronger, simpler-to-audit guarantee than "read but redact"                                    |

**The write-boundary question — the actual open decision:**

Two options, presented for the project owner's ADR-017 decision, not
resolved by this specification:

- **Option A — a new write edge.** `governance-service` calls directly
  into `voting-service`'s and `tally-service`'s `application` layers with
  a new _mutating_ call, bypassing each service's existing "only that
  service's own commands mutate its own entities" boundary. **Not
  recommended.** This would be the first write edge of any kind between
  packs in this project's history (every prior cross-pack call, ADR-008
  and ADR-012 alike, is read-only), and it breaks the section 22
  ownership-matrix invariant that each entity has exactly one module
  that ever mutates it — `Ballot` would gain a second mutator
  (`governance-service`) alongside `voting-service`.
- **Option B — extend the existing pattern (recommended).**
  `voting-service` gains one new, narrowly-scoped application command —
  e.g. `invalidate_ballot(ballot_id, governance_decision_id, actor,
...)` — and `tally-service` gains one new command — e.g.
  `determine_result_finality(result_publication_id,
governance_decision_id, actor, ...)`. Each new command is the _only_
  way its own service's entity is ever mutated for this purpose (single
  writer preserved), and each internally calls a new, read-only,
  ADR-017-sanctioned function —
  `epd2_governance_service.application.get_governance_decision` — to
  confirm the caller-supplied `governance_decision_id` refers to an
  `approved` decision, of the correct `decision_type`, targeting exactly
  this `ballot_id`/`result_publication_id`. This is structurally
  identical to how PACK-04's `publish_ledger_entry` takes
  caller-supplied `raw_content` rather than reaching into another
  service's storage (section 6 of `PACK-04-REPORT.md`) — the mutating
  service still does its own mutation, gated by a read of another
  service's already-authorized decision.

This specification's working recommendation is **Option B**, because it
is the only one of the two that does not require weakening or
special-casing the ownership-matrix invariant every prior pack has kept
absolute. **This must be ratified as ADR-017** before any cross-pack
import — read or write-adjacent — exists in code; no PACK-05 code may
assume either option until the ADR is accepted. If Option B is accepted,
`tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
must be extended twice: once for `governance-service`'s own three read
edges above, and once for the _reverse_ edge (`voting-service` and
`tally-service` each importing exactly one new
`epd2_governance_service.application` read function) — the only
instance in this project of a bidirectional-at-the-service-level (but
still one-writer-per-entity, still read-only-in-either-direction)
relationship between two packs.

## 6. Design decision D3 — canon addition for Governance entities and event catalog (requires ADR-018)

Mirrors PACK-04-SPEC.md section 6 exactly in kind: this proposes **new
canonical content** — formal field lists and status enums for
`GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge`
(section 3), new section 22 ownership-matrix rows for those three (
`RoleAssignment`'s row already exists and needs no change), and a new
section 20.x-style event catalog for Governance (canon currently has
none). This is a **minor** version bump under canon section 25 — canon
`0.3.0 → 0.4.0` — via the same "propose in an ADR, get it accepted, then
edit the canon document in one dedicated task" path ADR-010 and ADR-013
both already used.

ADR-018 must also resolve the `AdministratorRole` canon-silence finding
from section 2: whether it is a `RoleAssignment.role_code` value, a
distinct future entity, or informal prose that should be replaced with
an explicit reference to `RoleAssignment` — this pack's implementation
of INV-06-adjacent guarantees (no role, however named, may decrypt a
secret vote) depends on knowing which.

Proposed event names (pending ADR-018; **none of these exist in canon
today** — listed here only to make the scope of the proposed addition
concrete, not as a pre-decided catalog):

`governance.role_assignment_requested`, `governance.role_assignment_activated`,
`governance.role_assignment_revoked`, `governance.policy_defined`,
`governance.policy_activated`, `governance.policy_superseded`,
`governance.decision_proposed`, `governance.decision_approved`,
`governance.decision_rejected`, `governance.technical_challenge_submitted`,
`governance.technical_challenge_adjudicated`.

If ADR-017 (section 5) accepts Option B, this ADR-018 canon addition
must also record, in `Ballot` and `ResultPublication`'s own canon
sections (15.1/15.6), that a governance-authorized invalidation/finality
determination is now a recognized (if externally-triggered) transition
— without changing either entity's owner or existing fields, since that
would be a **major**, not minor, canon change under section 25's own
"изменение владельца сущности" / "жизненного цикла критического
объекта" test. Whether this is best expressed as a new optional
`ResultPublication.finality_status` field (proposal) or purely as a
`governance-service`-side record with no `ResultPublication` field
change at all is an explicit open question for ADR-018, not resolved
here — the conservative default this specification leans toward is _no_
new field on `ResultPublication` itself (keeping tally-service's owned
schema untouched) with finality state living entirely in
`GovernanceDecision`/`TechnicalChallenge`, queried by anyone who needs
it via the new read function section 5 already proposes.

**No PACK-05 code may be written against these proposed entities/events
until ADR-018 is accepted and the canon document itself is amended** —
the same harder gate PACK-04-SPEC.md section 6 already established for
its own canon-addition ADR.

## 7. Reason codes (requires ADR-019)

Canon section 24's fixed list has no codes scoped to role assignment,
policy adoption, governance decisions, or technical challenges.
Proposed additive codes for `contracts/reason-codes/pack-05.yml`
(ADR-006/ADR-014 precedent — a new per-pack registry file, not a canon
edit):

`ROLE_ASSIGNMENT_NOT_ACTIVE`, `ROLE_ASSIGNMENT_SCOPE_MISMATCH`,
`GOVERNANCE_POLICY_VIOLATION`, `TWO_ACTOR_APPROVAL_REQUIRED`,
`SAME_ACTOR_APPROVAL_REJECTED`, `TECHNICAL_CHALLENGE_WINDOW_CLOSED`,
`TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED`,
`GOVERNANCE_DECISION_NOT_APPROVED`, `BALLOT_INVALIDATION_NOT_AUTHORIZED`,
`RESULT_FINALITY_NOT_AUTHORIZED`.

Reused generic codes: `PERMISSION_DENIED`, `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`.

`docs/review/OPEN_QUESTIONS.md` item 10 (PACK-02's additive codes never
folded back into canon) is now four additive layers deep if this pack
proceeds (PACK-02, PACK-03, PACK-04, PACK-05) — worth the project
owner's attention again, not a blocker for this pack's own Definition of
Done.

## 8. Design decision D4 — two-actor approval, policy defaults, and challenge-lifecycle specifics (requires ADR-020)

Conservative, fail-closed defaults proposed for the project owner's
review, in the same spirit as ADR-009's section-29 defaults —
proposals, not decisions:

1. **What counts as a "critical action" requiring two-actor approval?**
   Proposed: every `GovernanceDecision` regardless of `decision_type`,
   and every `GovernancePolicy` `draft → active` transition — the same
   scope INV-08 already names generically ("критические действия") and
   the same pattern ADR-009 item 7 already applied narrowly (a second,
   distinct actor for `Ballot`'s own `configuration_review → scheduled`
   transition). Proposed mechanically: the approving actor's
   `RoleAssignment.actor_id` must differ from the proposing actor's, and
   both must be independently `active` and in-scope at approval time —
   never inferred from role alone.
2. **Who may create/hold which `role_code` values?** **Open question,
   not resolved by this specification.** Canon defines `RoleAssignment`'s
   shape but not its closed set of `role_code` values, nor who is
   authorized to grant which role to whom (a bootstrapping problem: some
   initial authority must exist to grant the first roles). Flagged for
   explicit ADR-020 owner decision — this specification deliberately
   does not propose a default role taxonomy.
3. **Technical-challenge submission window and eligibility.** Proposed:
   a `TechnicalChallenge` may only be submitted by a `RoleAssignment`-
   gated actor, strictly before the referenced `ResultPublication.
challenge_deadline_at` (read via the section 5 upstream call);
   submissions after the deadline are rejected
   (`TECHNICAL_CHALLENGE_WINDOW_CLOSED`), consistent with ADR-010's own
   "no hidden, pack-local challenge process" rule.
4. **Result-finality determination trigger.** Proposed: a
   `TechnicalChallenge` reaching `upheld` or `rejected` status is what
   creates a `GovernanceDecision` of type `result_finality_determination`
   (never the reverse) — adjudication is always the direct cause of a
   finality ruling, never a standalone act. If `challenge_deadline_at`
   elapses with zero challenges submitted, a `result_finality_
determination` `GovernanceDecision` must still be explicitly created
   (even if procedurally close to automatic) rather than any module
   silently treating the elapsed deadline itself as finality — the exact
   thing ADR-010 forbids.
5. **Oversight/review workflow scope.** Proposed: `oversight_directive`-
   type `GovernanceDecision`s are advisory/directive records only (e.g.
   "review this `ModerationDecision`," "audit this actor's recent
   `RoleAssignment` history") — they do not themselves mutate any other
   pack's entity; only `ballot_invalidation` and
   `result_finality_determination` decision types ever trigger the
   section 5 write-boundary calls. **Open question, not resolved by this
   specification:** whether a future oversight decision type should gain
   its own write-triggering behavior (e.g. directly reopening a
   `ModerationCase`) is left to a later ADR, not defaulted here.

**This must be ratified as ADR-020** before any two-actor-approval or
challenge-adjudication code ships, with items 2 and 5 specifically
requiring the project owner's explicit decision rather than accepting
this document's conservative defaults by silence.

## 9. Separation-of-authority rules (INV-08, operationalized)

INV-08 states plainly: one person or one service must never, alone,
change access rules and confirm their own change; run crisis override
and delete its own trace; set voting parameters and alone publish the
outcome; build Vote Casting and be its only auditor; change a tally and
confirm its own tally. This pack is where INV-08 stops being prose and
becomes an enforced, testable rule for governance actions specifically:

- **No self-approval.** Every `GovernanceDecision` and every
  `GovernancePolicy` activation requires two distinct
  `RoleAssignment.actor_id` values — the proposer and the approver.
  `SAME_ACTOR_APPROVAL_REJECTED` (section 7) is raised, not silently
  corrected, if the same actor is supplied for both.
- **No unilateral ballot invalidation.** Per ADR-009 item 14, no actor —
  however privileged — may invalidate a `Ballot` through a single
  action. The `ballot_invalidation` `GovernanceDecision` must itself
  already carry two-actor approval _before_ `voting-service`'s
  `invalidate_ballot` command (section 5, Option B) will act on it —
  the two-actor rule is enforced once, at the `GovernanceDecision`
  layer, not re-implemented inside `voting-service` itself.
- **No unilateral result finality.** Symmetric to the above:
  `result_finality_determination` decisions require two-actor approval
  before `tally-service`'s `determine_result_finality` command will act
  on them.
- **Structural, not just procedural.** Mirroring how PACK-04 enforced
  its own structural guarantees (`FORBIDDEN_FIELD_NAMES`,
  `assert_no_forbidden_fields`, checked unconditionally before any
  policy is consulted), this pack's two-actor check is proposed as an
  unconditional precondition inside every mutating `governance-service`
  command — never a check the caller can bypass by supplying a
  particular `role_code`, and never optional per-`decision_type`.
- **Existing precedent already in this codebase.** ADR-009 item 7
  already applies this exact pattern narrowly, inside `voting-service`
  itself, for `Ballot`'s own `configuration_review → scheduled`
  transition. This pack generalizes that one narrow instance into a
  reusable, governance-owned primitive every future critical-action
  pattern can reference, rather than each service re-implementing its
  own bespoke two-actor check.

## 10. Technical-challenge lifecycle

Proposed status machine for `TechnicalChallenge`
(`submitted → under_review → upheld` / `submitted → under_review →
rejected`; no further transition once adjudicated):

1. **`submitted`** — a `RoleAssignment`-gated actor registers a
   challenge against a specific `ResultPublication`, strictly before its
   `challenge_deadline_at` (section 8 item 3). Requires
   `challenge_reason_code` and `evidence_references`, mirroring
   `EmergencyAction`'s own `reason_code`/`evidence_references` shape
   (canon 19.1).
2. **`under_review`** — an adjudicating actor (distinct from the
   submitter; two-actor approval applies to the _outcome_, not the
   submission itself, since submission is an intake action, not yet a
   critical decision) begins adjudication. No `Ballot`/`ResultPublication`
   state changes yet.
3. **`upheld`** — adjudication concludes the challenge is valid. This
   creates a `result_finality_determination` `GovernanceDecision`
   (section 8 item 4) whose approved outcome, once two-actor approved,
   is the caller-supplied authorization `tally-service`'s
   `determine_result_finality` command consumes (section 5). An upheld
   challenge **may**, depending on its `challenge_reason_code`, also
   justify a separate `ballot_invalidation` `GovernanceDecision` — the
   two are proposed as always-distinct decisions (section 3), never
   automatically chained, so that an integrity finding about a result
   does not silently also invalidate the underlying ballot without its
   own independent two-actor approval.
4. **`rejected`** — adjudication concludes the challenge is not valid.
   This still creates a `result_finality_determination`
   `GovernanceDecision` (recording that finality proceeds normally,
   section 8 item 4) — rejection is not silence, it is itself a
   recorded governance ruling.

No `TechnicalChallenge` may be resubmitted once adjudicated
(`TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED`) — a new integrity concern
about the same `ResultPublication` requires a new, separately-tracked
challenge record, preserving a complete history rather than overwriting
one outcome with another.

## 11. Result-finality lifecycle

Directly operationalizes ADR-009 item 12 and ADR-010's finality
clarification, neither of which any pack has yet implemented:

1. `ResultPublication.published_at` is set (already implemented,
   PACK-03/`tally-service`) — the result is **tallied-but-provisional**
   from this moment.
2. `challenge_deadline_at` (already a canon field, ADR-010) is the
   earliest a `result_finality_determination` may be created — not
   itself a finality trigger.
3. Exactly one of two paths reaches finality, per section 10:
   - **No challenge submitted** before `challenge_deadline_at` elapses:
     an explicit `result_finality_determination` `GovernanceDecision` is
     still required (section 8 item 4) — the elapsed deadline is a
     precondition for creating it, never a substitute for it.
   - **One or more challenges submitted**: finality is deferred until
     every submitted `TechnicalChallenge` against that
     `ResultPublication` reaches `upheld` or `rejected` (section 10);
     each adjudication outcome feeds its own
     `result_finality_determination` `GovernanceDecision`.
4. `tally-service`'s proposed `determine_result_finality` command
   (section 5, Option B) is the **only** path by which a
   `ResultPublication` is ever treated as finalized anywhere in this
   system — no report, dashboard, or export (including PACK-04's own
   `AuditExportPackage`/`PublicLedgerEntry`) may independently declare a
   result final by any other rule, per ADR-010's own explicit
   prohibition.
5. **Until ADR-017/018 are accepted and this command exists, every
   `ResultPublication` in this system remains, correctly, permanently
   provisional** — this is not a bug in PACK-03 or PACK-04, it is
   exactly the gap this pack exists to close, stated plainly rather than
   left implicit.

## 12. Schemas and OpenAPI scope

Following the existing repository convention exactly
(`contracts/schemas/`, currently 30 files across PACK-02/03/04;
`contracts/openapi/pack-02.yaml`/`pack-03.yaml`/`pack-04.yaml`):

- `contracts/schemas/role-assignment.schema.json`,
  `governance-policy.schema.json`, `governance-decision.schema.json`,
  `technical-challenge.schema.json` — one JSON Schema per entity in
  scope (section 3); `role-assignment.schema.json` can be drafted
  directly from canon 8.4 today (no ADR-018 dependency), the other three
  only after ADR-018 fixes their actual field lists.
- `contracts/events/*.v1.schema.json` — one per proposed event
  (section 6), pending ADR-018.
- `contracts/openapi/pack-05.yaml` — one path per real application
  command, tagged `governance-service`, same tagging convention as
  `pack-04.yaml`. Includes the two new upstream commands proposed for
  `voting-service`/`tally-service` (section 5, Option B) as entries
  tagged `voting-service`/`tally-service` respectively, not
  `governance-service` — they are those services' own commands, gated
  by a governance-supplied authorization, not governance-service's own
  endpoints.

## 13. CT-00 applicability

| Contract test                      | Applies to PACK-05?                 | Notes                                                                                                                                                                                                                         |
| ---------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-00-01 Schema Validation         | Yes                                 | Standard, once schemas exist (section 12).                                                                                                                                                                                    |
| CT-00-02 Unknown Status            | Yes                                 | `RoleAssignment` (5 statuses, canon-fixed), `GovernancePolicy`/`GovernanceDecision`/`TechnicalChallenge` (pending ADR-018).                                                                                                   |
| CT-00-03 Forbidden Transition      | Yes                                 | `RoleAssignment`'s canon-fixed statuses give this real content immediately; the other three depend on ADR-018.                                                                                                                |
| CT-00-04 Event Idempotency         | Yes                                 | Every new command needs a caller-supplied idempotency key, uniform from the start, continuing PACK-03/04's own closure of `docs/review/OPEN_QUESTIONS.md` item 11.                                                            |
| CT-00-05 Unsupported Event Version | Yes                                 | Standard mechanism, exercised against section 6's new event types.                                                                                                                                                            |
| **CT-00-06 Missing Permission**    | **Yes — most central to this pack** | Every proposed command is `RoleAssignment`-gated by definition; this is this pack's core guarantee, not an incidental check.                                                                                                  |
| CT-00-07 Audit Creation            | Yes                                 | Every `GovernanceDecision`/`GovernancePolicy` mutation is, by INV-08's own framing, a critical action requiring an `AuditEvent` — directly on point.                                                                          |
| CT-00-08 Identity Leakage          | Yes                                 | `RoleAssignment.actor_id` and related fields must never leak into anything this pack itself might later expose publicly (though this pack proposes no public-facing payloads itself — that is Transparency's job, section 1). |
| CT-00-09 Vote Linkability          | Yes, narrowly                       | `TechnicalChallenge`/`GovernanceDecision` records referencing a `Ballot`/`ResultPublication` must never expose or reconstruct individual `VoteEnvelope` linkage — inherited obligation, not a new one this pack invents.      |
| CT-00-10 Rule Freeze               | Yes, narrowly                       | An `active` `GovernancePolicy` version's rules must not change in place — only superseded by a new version (mirrors `DisclosurePolicy`'s own PACK-04 precedent).                                                              |
| CT-00-11 AI Human Control          | **Not applicable**                  | No `AIProcessingRecord` in this pack's proposed scope (section 1).                                                                                                                                                            |
| CT-00-12 Emergency Stop            | **Not applicable**                  | `EmergencyAction` explicitly excluded from this pack's scope (section 1), per the user's instruction.                                                                                                                         |

## 14. Privacy and separation guarantees (summary)

- Structural, not just policy-level: every proposed schema (section 12)
  uses `additionalProperties: false`, following CT-00-08's established
  precedent.
- Two-actor approval (section 9) is proposed as an unconditional
  precondition, checked before any `decision_type`-specific logic runs
  — the same "checked first, independent of any other rule"
  structure PACK-04's `assert_no_forbidden_fields` already established
  for disclosure.
- The write-boundary design (section 5, Option B) is deliberately
  structured so that no pack ever gains a second mutator for an entity
  it does not own — `governance-service` never writes to `Ballot` or
  `ResultPublication` directly, it only supplies an authorization that
  each owning service's own new command consumes.
- Three explicit open questions are deliberately left undecided by this
  specification and deferred to ADR-020's owner review, per the user's
  requirement to identify (not silently resolve) design decisions
  requiring ADRs: the closed set of `role_code` values and who may grant
  them (section 8 item 2), whether oversight decisions ever gain their
  own write-triggering behavior (section 8 item 5), and the
  `AdministratorRole` canon-silence finding (section 2, deferred to
  ADR-018).

## 15. Definition of Done (for a future implementation pass)

Mirrors PACK-04-SPEC.md section 12's structure:

1. ADR-016 (service decomposition), ADR-017 (cross-pack dependency
   matrix and the write-boundary decision — Option A or B, section 5),
   ADR-018 (canon addition for Governance entities/events, canon
   `0.3.0 → 0.4.0`, plus the `AdministratorRole` finding), ADR-019
   (reason-code additions), and ADR-020 (two-actor approval and policy
   defaults, with items 2 and 5 from section 8 explicitly decided rather
   than defaulted) all reach `accepted` status before the corresponding
   code is written.
2. `services/governance-service` exists as an independent `uv` workspace
   member with its own `pyproject.toml`, `src/`, `tests/`, `README.md`.
3. Every entity ADR-018 defines (plus `RoleAssignment`, already
   canon-defined) has a JSON Schema and, where produced by an event, an
   event-payload schema.
4. `contracts/openapi/pack-05.yaml` documents every new `governance-service`
   path, plus the two new upstream commands in `voting-service`/
   `tally-service` (if ADR-017 accepts Option B), tagged accordingly.
5. `contracts/reason-codes/pack-05.yml` exists, structurally validated,
   every literal reason code used anywhere in the new service (and the
   two upstream commands, if applicable) is registered.
6. CT-00-01 through CT-00-10 pass for this pack's scope (section 13),
   with CT-00-06 given the most scrutiny per that section's notes;
   CT-00-11/12 remain genuine, documented not-applicable markers.
7. `tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
   is extended for `governance-service`'s three read edges and, if
   ADR-017 accepts Option B, the reverse read edges from
   `voting-service`/`tally-service` back into
   `epd2_governance_service.application` — the first bidirectional
   (still one-writer-per-entity, still read-only-in-either-direction)
   pair in this project.
8. Two-actor approval (section 9) is enforced with a real test proving a
   same-actor proposal-and-approval pair is rejected
   (`SAME_ACTOR_APPROVAL_REJECTED`), not merely documented.
9. A real end-to-end test proves the full result-finality lifecycle
   (section 11): a provisional `ResultPublication` cannot be treated as
   final by any code path other than the proposed
   `determine_result_finality` command.
10. `scripts/check_repository.py`'s `REQUIRED_PATHS` extended for every
    new path.
11. `REPOSITORY_VERSION` bumped `0.4.0 → 0.5.0`; canon SHA-256 updated to
    match the post-ADR-018 canon text (recorded in a new report,
    `docs/handover/PACK-05-REPORT.md`, following the same
    revision-by-revision honest-verification structure PACK-02/03/04 all
    used).
12. Exactly one clean canonical archive exported at the end, no
    pack-specific change needed to
    `.github/workflows/verify-and-package.yml` (already pack-agnostic,
    confirmed unchanged through four packs now).

## 16. Explicitly excluded from this pack

- **Emergency/Crisis Override (19/19.1, `EmergencyAction`)** — per the
  user's explicit instruction. No entity proposed in section 3 requires
  it; the service-decomposition question of whether a future
  Emergency/Crisis pack extends `governance-service` or introduces its
  own is deliberately left open (section 4), not decided here.
- **AI-processing (17.1, `AIProcessingRecord`)** — "review procedures"
  in canon 5.12 is read as human oversight of governance/moderation
  actions (section 8's `oversight_directive` decision type), not review
  of AI-generated output, which remains canon 17's own, separate,
  unimplemented subject.
- **Transparency Context (5.11) / any change to `transparency-service`**
  — PACK-04, already implemented and PASSed. No entity proposed here
  reads from or writes to it; whether/how governance decisions become
  publicly visible is a future Transparency-side concern (its own
  `PublicLedgerEntry.subject_type` addition), not proposed by this
  specification.
- **A closed `role_code` taxonomy** — section 8 item 2 explicitly defers
  this to ADR-020 owner review rather than proposing a default set.
- **Any implementation of the `AdministratorRole → decrypt secret votes`
  forbidden link's positive-authorization side** — this specification
  only surfaces the canon-silence finding (section 2/6); resolving what
  `AdministratorRole` actually refers to, and enforcing the prohibition
  structurally, is ADR-018's job plus a later implementation task, not
  this document's.
- **Frontend/UI work** — `frontend/web-shell` is unchanged by this
  specification, consistent with the user's instruction that no frontend
  implementation is expected unless strictly required for contract
  verification (it is not — this pack's CT-00 suite, like PACK-02/03/04's,
  is backend-only).
- **Any change to `Ballot` or `ResultPublication`'s existing canon
  fields** — only a possible new field addition is proposed (section 6),
  and only as an open question, never a change to an existing field's
  meaning or either entity's owner (which would be a major, not minor,
  canon version change, forbidden by this pack's own scope).
- **Cryptographic signing of governance decisions** — two-actor approval
  (section 9) is proposed as a structural record-keeping and
  authorization-gating rule, not a cryptographic signature scheme; that
  would be its own future ADR, same non-cryptographic boundary
  PACK-03/04 both already drew for their own domains.

## 17. Summary — ADRs required before any implementation

| ADR     | Subject                                                                                                                                                   | Canon impact                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| ADR-016 | Service decomposition (section 4)                                                                                                                         | None                                                |
| ADR-017 | Cross-pack dependency matrix and the ballot/result write-boundary decision (section 5)                                                                    | None                                                |
| ADR-018 | Canon addition: `GovernancePolicy`/`GovernanceDecision`/`TechnicalChallenge` + Governance event catalog, plus the `AdministratorRole` finding (section 6) | **Yes — canon `0.3.0 → 0.4.0`, minor**              |
| ADR-019 | Reason-code additions (section 7)                                                                                                                         | None (registry file, per ADR-006/014/019 precedent) |
| ADR-020 | Two-actor approval, policy defaults, and challenge-lifecycle specifics, with items 2/5 of section 8 requiring explicit owner decision                     | None                                                |

ADR-007 is reserved/unused (`docs/adr/README.md`); ADR-005/006/008/009/010
are PACK-03; ADR-011 through ADR-015 are PACK-04 — this pack's five ADRs
are the next five free numbers, ADR-016 through ADR-020, drafted only
after this specification itself is reviewed and, if accepted, acted on.

**No code, schema, contract, or canon edit has been produced by this
specification.** `services/governance-service` does not exist;
`contracts/schemas/role-assignment.schema.json` and its three siblings
do not exist; `docs/canonical/TZ-00-domain-event-canon.md` remains
byte-identical to the PACK-04 PASS state (section 0). This document's
only deliverable is the proposal itself, exactly as this task requires.
