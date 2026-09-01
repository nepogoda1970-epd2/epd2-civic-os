# CLAUDE-PACK-04 — Transparency Context: Technical Specification

**Status: proposed.** This document specifies the next candidate
implementation package. It is not itself an ADR and authorizes no code.
Per canon section 26, every design decision below marked "requires ADR"
must reach `accepted` status before any corresponding working code is
written. **No PACK-04 service directory, schema, contract, or
implementation code exists yet** — this specification is the entire
PACK-04 deliverable at this stage.

This pack differs from PACK-03 in one structurally important way, called
out up front because it shapes almost every section below: PACK-03's
canon dependency (`docs/handover/PACK-03-SPEC.md` section 2) was a matter
of _implementing_ eighteen entities the canon had already fully defined
(sections 11–16). PACK-04's canon dependency is different in kind — the
canon **names** the Transparency Context's responsibilities (section
5.11) and references exactly one Transparency-owned entity by name in a
forbidden-link rule (section 23), but **never formally defines any
Transparency entity's fields, statuses, or events**. Sections 3–7 below
are therefore proposals for new canonical content, not implementation
plans for existing canonical content, and are marked as such throughout.

## 0. Canon dependency

**Update, 2026-07-23:** this specification was originally authored
against canon `0.2.0` (checksum
`5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a`),
stating that canon "makes no change" here and "would move `0.2.0 →
0.3.0`" only if design decision D3/ADR-013 were accepted. ADR-013 has
since been accepted (with amendments) and its canon-edit task carried
out as its own separate, dedicated step (canon section 26's
precondition) — the current canon dependency is now:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
CANON_VERSION = 0.3.0
```

Canon section 19a, section 20.14, and four new section 22 rows now
formally define `PublicLedgerEntry`, `AuditExportPackage`,
`DisclosurePolicy`, and `LobbyLogEntry` — the canon-silence finding this
section originally documented (below) is resolved for these four
entities specifically. This specification document itself is not being
retroactively rewritten into an implementation plan; sections 1–13 below
remain as originally authored and should be read as the proposal that
led to ADR-011–015 and the now-completed canon edit, not as a
description of already-built service code (`transparency-service` still
does not exist).

`REPOSITORY_VERSION` (currently `0.3.0`, PACK-03 PASS) is not touched by
this specification. It would move to `0.4.0` only once PACK-04
implementation code actually lands, tracked in the same three places
every prior pack tracked its own bump.

## 1. Scope — context separation

The user's request for this pack is explicit that Transparency,
Governance, AI-processing, and Emergency/Crisis Override must be kept
conceptually distinct and never silently combined. The table below is
that separation, checked directly against canon sections 5.11/5.12/17/19:

| Canon context / concern              | Canon section | In PACK-04 scope | Why                                                                                                                                                                                           |
| ------------------------------------ | ------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Transparency Context                 | 5.11          | **Yes**          | This pack's entire subject.                                                                                                                                                                   |
| Governance Context                   | 5.12          | **No**           | See below — not a hard dependency for anything this pack needs to do.                                                                                                                         |
| AI-processing (`AIProcessingRecord`) | 17.1          | **No**           | No canon entity in this pack's proposed scope requires an `AIProcessingRecord` to exist; "журналы ИИ" (5.11) is publication _of_ existing AI logs, not creation of new ones — see section 13. |
| Emergency / Crisis Override          | 19.1          | **No**           | No canon entity in this pack's proposed scope requires an `EmergencyAction` to exist; "crisis override" (5.12) is Governance's own responsibility, not Transparency's.                        |

**Why Governance is not a hard dependency for PACK-04**, checked
explicitly per the user's requirement not to silently combine the two
contexts:

- Canon section 5.11 (Transparency) lists "публичный реестр инициатив,
  реестр решений, история версий, результаты, журналы модерации, журналы
  ИИ, финансовая прозрачность, lobbying log, audit exports" — every item
  is _publishing a record of something another context already produced_
  (an initiative, a result, a moderation decision, an AI log entry, a
  ledger entry). None of these require a system role, a permissions
  policy, a rules version, an emergency procedure, or a crisis override
  to exist first.
- Canon section 5.12 (Governance) lists "системные роли, политика
  полномочий, версии правил, emergency procedures, crisis override, audit
  access, review procedures" — none of these are consumed by anything
  proposed in section 3 below. `audit access` in 5.12 is about _who is
  authorized to see_ audit data (a Governance/permissions concern);
  PACK-04's `AuditExportPackage` (section 3) is about _packaging and
  publishing_ an already-authorized export, structurally analogous to
  how PACK-03 read PACK-02's `ParticipationCredential` validity without
  needing to reimplement Eligibility.
- The one place a Governance-shaped question does appear —
  who is authorized to mark a `DisclosurePolicy` decision, approve a
  redaction override, or publish a `LobbyLogEntry` — is handled the same
  way PACK-03 handled ballot-invalidation authority (PACK-03-SPEC.md
  section 8 item 14): gated behind a narrowly-scoped `RoleAssignment`
  role (already a canon 8.4 entity, owned by Organization/Permission
  Service, consumed read-only), not by this pack defining or
  reimplementing any Governance entity. If a future Governance pack later
  defines a richer permissions model, PACK-04's role checks would be
  extended, not rewritten — the same forward-compatible relationship
  PACK-03 has with the still-unimplemented Governance context today.

AI-processing and Emergency are excluded for the same reason PACK-02 and
PACK-03 both gave (`docs/review/OPEN_QUESTIONS.md`, carried forward
again): no entity actually proposed in this pack's scope needs
`AIProcessingRecord` or `EmergencyAction` to exist. CT-00-11/CT-00-12 are
expected to remain genuine **not-applicable** markers a third time
(section 11).

## 2. Canon-textual basis and canon-silence findings

Everything canon actually says about the Transparency Context, quoted in
full because there is not more to quote:

> **5.11. Transparency Context** — Ответственность: публичный реестр
> инициатив; реестр решений; история версий; результаты; журналы
> модерации; журналы ИИ; финансовая прозрачность; lobbying log; audit
> exports.

And the one other canon reference to a Transparency-context entity by
name, from the forbidden-links list:

> **Section 23** — `PublicLedgerEntry → непубличные персональные данные`
> [forbidden]

Checked systematically against every other place canon defines entity
detail, and confirmed absent for Transparency in all four:

- **Sections 7–19 (entity definitions)** — no `## 11.x`-style section
  exists for any Transparency entity. Sections 11–16 cover Initiative
  through Delegation (PACK-03's scope); section 17 is AI, 18 is Audit,
  19 is Emergency. There is no section between 16 (Delegation) and 17
  (AI) for Transparency, and no section after 19 either. `PublicLedgerEntry`
  is referenced but never has a field list, a status enum, or a canonical
  identifier scheme defined anywhere in the document.
- **Sections 20.1–20.13 (canonical event catalog)** — thirteen
  per-context event lists exist (Account, Identity, Eligibility,
  Credential, Organization, Initiative, Amendment, Discussion,
  Moderation, Voting, Delegation, AI, Emergency). **None is for
  Transparency or Governance.** Zero Transparency events are canonically
  named anywhere in this document.
- **Section 22 (ownership matrix)** — 27 entities are listed with their
  owning module (Account through EmergencyAction). **No Transparency
  entity appears in this matrix**, including `PublicLedgerEntry` itself
  — the one entity canon names is not actually in the table that assigns
  every other named entity its owner.
- **Section 24 (reason-code standard)** — the fixed list of canon-defined
  reason codes contains none scoped to disclosure, redaction, or public
  publication.

**Conclusion, stated plainly for the record:** canon acknowledges the
Transparency Context exists and sketches its _responsibilities_ in prose,
but has never been extended with the entity/event/ownership detail every
other in-scope context received. This is exactly the situation
`docs/handover/PACK-03-SPEC.md` section 8 item 15 anticipated when it
said "full public disclosure design belongs to the Transparency Context
(5.11, out of this pack's scope)" — but it is a larger gap than PACK-03's
own canon dependency, and the ADR-013 canon addition proposed in section
6 below is a bigger, more foundational decision than any single ADR in
PACK-02 or PACK-03 to date. The project owner should read section 6
first among the ADR proposals in this document.

## 3. Proposed entities in scope

None of these entities exist in canon today. Each is a proposal for what
canon section 5.11's responsibility list would need to become concrete
entities, modeled as closely as possible on the shape and naming
conventions canon already uses for comparable entities elsewhere (audit
trail shape from `AuditEvent`, 18.1; public-facing aggregate shape from
`ResultPublication`, 15.6).

| Proposed entity      | Rationale                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Modeled after                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| `PublicLedgerEntry`  | The only Transparency entity canon names (section 23). Proposed as the single, generic "published record" wrapper covering "публичный реестр инициатив, реестр решений, история версий, результаты, журналы модерации" (5.11) — one entity type with a `subject_type` discriminator (`initiative`, `decision`, `initiative_version`, `result_publication`, `moderation_decision`) rather than five near-duplicate entities, following the same consolidation reasoning PACK-03-SPEC.md section 3 used for its own service groupings. | `AuditEvent` (append-only, hash-referencing) |
| `AuditExportPackage` | Covers 5.11's "audit exports" and directly implements INV-03's fourth legitimate integration mechanism, "специальный audit export" (section 102-116) — a batched, hash-chain-provable export of `AuditEvent` records (never full payloads for anything identity-linked; see section 12).                                                                                                                                                                                                                                             | `AuditEvent` batch semantics                 |
| `DisclosurePolicy`   | Not named in canon text, but required as soon as any entity above needs a documented, structural answer to "what gets redacted before publication, and by what rule" — every one of PACK-03-SPEC.md's own section 8 item 15 proposals (aggregate counts only, never raw envelopes) needs a place to live as data, not just as a paragraph of prose in a spec.                                                                                                                                                                        | `EligibilityRule` (versioned policy record)  |
| `LobbyLogEntry`      | Covers 5.11's explicit "lobbying log" line. Flagged as the entity with the weakest canon grounding of the four — canon's Organization Context (5.4) owns "организация, подразделения, Civic Spaces, рабочие группы, роли, членство, организационная структура" but has no concept of an external lobbying actor or disclosure obligation. Proposed schema in this pack is intentionally minimal (who logged contact with whom, when, regarding which `Initiative`/`Ballot`) with real ingestion mechanics deferred — see section 13. | New; no direct canon precedent               |

Every field list for these four entities is deliberately **not** written
out in this specification. Per canon section 26 and this project's
standing rule, inventing entity field lists is exactly the kind of canon
content that must be drafted, reviewed, and accepted _as_ an ADR (ADR-013,
section 6) before it has any authority — writing a detailed field list
here would risk it being treated as already-decided. This specification's
job is to identify that the entities are needed and why; the ADR's job is
to define them precisely.

## 4. Design decision D1 — service decomposition (requires ADR-011)

Proposed: **one** new service, following the same "one group per set of
entities with no forbidden-link or ownership conflict" test PACK-03
applied six times over (PACK-03-SPEC.md section 3):

- **`services/transparency-service`** (`epd2_transparency_service`) —
  `PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
  `LobbyLogEntry`. All four are write-once-then-public, read-mostly
  records with no state-machine complexity remotely comparable to
  `Ballot`'s 11 statuses or `Initiative`'s 15 — a single service is
  proportionate, the same way PACK-02 kept `EligibilityRule`,
  `EligibilityDecision`, and `EligibilitySnapshot` in one
  `eligibility-service`.

This is a much smaller service surface than PACK-03's six, proportionate
to a pack whose job is publication of already-decided facts rather than
new decision-making workflows. **This decomposition must be ratified as
ADR-011** before any service directory is created, exactly as ADR-005 was
required before PACK-03's first service directory.

## 5. Design decision D2 — cross-pack read boundary and dependency matrix (requires ADR-012)

`transparency-service` needs read access to state four other packs'
services already own, to publish records of things it does not itself
produce. INV-03 forbids reaching into another service's storage
directly; the proposed resolution is the same one ADR-008 established
for PACK-03 → PACK-02: call the owning service's existing public
`application`-layer functions in-process, never its `storage`/`domain`
modules.

**PACK-04 → PACK-02/PACK-03 dependency matrix (proposed):**

| Upstream service                                                                   | Pack    | Read for                                                                 | Included?                                                                                                                                                                                                                                          |
| ---------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `initiative-service`                                                               | PACK-03 | Published `Initiative`/`InitiativeVersion` records for the public ledger | **Yes** — read-only                                                                                                                                                                                                                                |
| `moderation-service`                                                               | PACK-03 | `ModerationDecision` records for the moderation-transparency log         | **Yes** — read-only                                                                                                                                                                                                                                |
| `voting-service` / `tally-service`                                                 | PACK-03 | `ResultPublication` aggregate counts for the results ledger              | **Yes** — read-only                                                                                                                                                                                                                                |
| `epd2_audit_core`                                                                  | PACK-02 | `AuditEvent` records for `AuditExportPackage` construction               | **Yes** — read-only                                                                                                                                                                                                                                |
| `deliberation-service`                                                             | PACK-03 | —                                                                        | **No** — canon 5.11 does not list discussion content as a transparency artifact; contributions may themselves be subject to moderation/redaction and are not "результаты"                                                                          |
| `delegation-service`                                                               | PACK-03 | —                                                                        | **No** — `Delegation`/`DelegationSnapshot` are structurally vote-adjacent (CT-00-09); publishing anything here risks reconstructing delegate/delegator linkage, the exact harm CT-00-09 exists to prevent                                          |
| `credential-service`, `identity-service`, `account-service`, `eligibility-service` | PACK-02 | —                                                                        | **No** — hard exclusion. Nothing in section 3's proposed entities needs identity or credential data, and excluding these four services entirely (not just their sensitive fields) is a stronger, simpler-to-audit guarantee than "read but redact" |

This is a **narrower** dependency surface than PACK-03's own (PACK-03
read from PACK-02; PACK-04 proposes reading from PACK-02 _and_ PACK-03,
but from strictly fewer of PACK-03's six services, and from none of
PACK-02's identity-adjacent four). The boundary-matrix extension this
requires:

- `transparency-service` may import: itself, `epd2_core`, `epd2_audit_core`,
  and only the four named `application` modules above (enumerated
  exhaustively in ADR-012, not left open-ended);
- no PACK-02 or PACK-03 service may import `epd2_transparency_service`
  (one-way dependency direction, same rule PACK-03 established for
  itself relative to PACK-02);
- `tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
  must be extended (not just re-run) to encode this new set of edges,
  exactly as PACK-03 extended it for its own PACK-02 edges.

**This must be ratified as ADR-012** before any cross-pack import exists
in code.

## 6. Design decision D3 — canon addition for `PublicLedgerEntry` and the Transparency event catalog (requires ADR-013)

This is the pack's most consequential open decision, flagged separately
from D1/D2 because — unlike every prior PACK-02/03 ADR, which resolved
an _implementation_ ambiguity inside an already-fully-specified canon —
this one proposes **new canonical content**: formal field lists, status
enums (if any), and a Transparency entry in section 22's ownership
matrix for the four entities in section 3, plus a full section 20.x-style
event catalog for the Transparency Context (canon currently has none —
section 2 above). This is a **minor** version bump under canon section 25
(new entities/events, no existing field/event/owner changes) — canon
`0.2.0 → 0.3.0` — using the exact same "propose in an ADR, get it
accepted, then edit the canon document in one dedicated task" path
ADR-010 already established as this project's only legitimate way to
touch canon's own text.

Proposed event names (pending ADR-013; **none of these exist in canon
today** — listed here only to make the scope of the proposed addition
concrete, not as a pre-decided catalog):

`transparency.ledger_entry_published`, `transparency.ledger_entry_redacted`,
`transparency.audit_export_created`, `transparency.audit_export_published`,
`transparency.disclosure_policy_defined`, `transparency.disclosure_policy_applied`,
`transparency.lobby_log_entry_created`, `transparency.lobby_log_entry_published`.

ADR-013 must also resolve, explicitly, whether `PublicLedgerEntry`'s
canon-named forbidden link (section 23, `PublicLedgerEntry → непубличные
персональные данные`) is best implemented the same way `VoteEnvelope`'s
forbidden links are (CT-00-08/09: `additionalProperties: false` + a
structural forbidden-field-name test) — this specification's working
assumption, but not yet a ratified decision.

**No PACK-04 code may be written against these proposed entities/events
until ADR-013 is accepted and the canon document itself is amended** —
this is a harder gate than ADR-011/012, since those two only govern this
pack's own service code, while this one governs the canon document that
every future pack also depends on.

## 7. Reason codes (requires ADR-014)

Canon section 24's fixed list has no codes scoped to disclosure,
redaction, or export integrity. Proposed additive codes for
`contracts/reason-codes/pack-04.yml` (ADR-006/ADR-014 precedent — a new
per-pack registry file, not a canon edit, since reason codes are
explicitly _not_ part of the canon's frozen entity/event content the same
way section 6's proposal is):

`DISCLOSURE_POLICY_VIOLATION`, `PUBLICATION_NOT_ALLOWED`,
`REDACTION_REQUIRED`, `LOBBY_LOG_ENTRY_INCOMPLETE`,
`AUDIT_EXPORT_INTEGRITY_FAILED`, `LEDGER_ENTRY_ALREADY_PUBLISHED`.

Reused generic codes: `PERMISSION_DENIED`, `INTEGRITY_CHECK_FAILED`,
`SERVICE_STATE_READ_ONLY`, `EVENT_VERSION_UNSUPPORTED`.

`docs/review/OPEN_QUESTIONS.md` item 10 (PACK-02's additive codes never
folded back into canon) is now three additive layers deep if this pack
proceeds (PACK-02, PACK-03, PACK-04) — worth the project owner's
attention again, not a blocker for this pack's own Definition of Done.

## 8. Design decision D4 — disclosure/redaction policy defaults and Lobby Log schema (requires ADR-015)

Conservative, fail-closed defaults proposed for the project owner's
review, in the same spirit as ADR-009's section-29 defaults — proposals,
not decisions:

1. **What gets published for a completed ballot?** Proposed: exactly the
   `ResultPublication` fields PACK-03-SPEC.md section 8 item 15 already
   named (`eligible_count`, `credential_count`, `accepted_vote_count`,
   `rejected_vote_count`, `quorum_result`, `threshold_result`) plus a
   redacted audit-chain proof (hashes only) — never raw `VoteEnvelope`
   contents, never anything CT-00-08/09 already forbids.
2. **Are moderation-decision actor identities published?** **Open
   question, not resolved by this specification.** Publishing
   `ModerationDecision.decided_by`/`Appeal.reviewer_actor_id` verbatim
   could expose individual moderators/reviewers to targeted pressure;
   omitting them weakens public accountability for moderation power.
   Flagged for explicit ADR-015 owner decision rather than a default
   assumed here.
3. **Small-cell / low-count suppression.** For any `PublicLedgerEntry`
   whose `subject_type` involves an aggregate over a small population
   (e.g. a `CivicSpace` with very few eligible participants), raw counts
   could indirectly re-identify individuals. **Open question, not
   resolved by this specification** — whether to suppress, band, or
   publish as-is below some threshold `n` is an ADR-015 decision, not a
   default this document should preempt.
4. **Lobby Log ingestion.** Proposed: `LobbyLogEntry` records are
   created only through an explicit, authenticated submission by a
   `RoleAssignment`-gated actor (mirrors ADR-009 item 6's "gated by
   RoleAssignment" pattern) — no automatic scraping or inference. Real
   lobbying-actor identity/registration is Organization Context's
   responsibility (5.4) and is out of this pack's scope until that
   context exists (section 13).

**This must be ratified as ADR-015** before any redaction/disclosure code
ships, with items 2 and 3 specifically requiring the project owner's
explicit decision rather than accepting this document's conservative
defaults by silence.

## 9. Schemas and OpenAPI scope

Following the existing repository convention exactly
(`contracts/schemas/`, currently 26 files across PACK-02/03;
`contracts/openapi/pack-02.yaml`/`pack-03.yaml`):

- `contracts/schemas/public_ledger_entry.schema.json`,
  `audit_export_package.schema.json`, `disclosure_policy.schema.json`,
  `lobby_log_entry.schema.json` — one JSON Schema per proposed entity
  (section 3), `additionalProperties: false`, drafted only after ADR-013
  fixes the actual field lists.
- `contracts/events/*.v1.schema.json` — one per proposed event (section 6).
- `contracts/openapi/pack-04.yaml` — one path per real application
  command, tagged `transparency-service`, same tagging convention as
  `pack-03.yaml`.
- `contracts/reason-codes/pack-04.yml` — section 7.

None of these files exist yet; this section records where they will go,
not their contents.

## 10. CT-00 applicability

| Contract test                      | Applies to PACK-04?                  | Notes                                                                                                                                                                                                                                                                                                                             |
| ---------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-00-01 Schema Validation         | Yes                                  | Standard, once schemas exist (section 9).                                                                                                                                                                                                                                                                                         |
| CT-00-02 Unknown Status            | Yes, if any entity has a status enum | `PublicLedgerEntry`/`AuditExportPackage` are plausibly append-only/immutable with no status enum at all — ADR-013 must decide this before this test has anything to cover.                                                                                                                                                        |
| CT-00-03 Forbidden Transition      | Likely minimal                       | Same dependency on ADR-013 resolving whether any Transparency entity actually has a state machine, or is purely write-once.                                                                                                                                                                                                       |
| CT-00-04 Event Idempotency         | Yes                                  | Every new command needs a caller-supplied idempotency key, uniform from the start (continuing PACK-03's own closure of `docs/review/OPEN_QUESTIONS.md` item 11).                                                                                                                                                                  |
| CT-00-05 Unsupported Event Version | Yes                                  | Standard mechanism, exercised against section 6's new event types.                                                                                                                                                                                                                                                                |
| CT-00-06 Missing Permission        | Yes                                  | The `RoleAssignment`-gated actions in section 8 items 1 and 4.                                                                                                                                                                                                                                                                    |
| CT-00-07 Audit Creation            | Yes                                  | INV-04 explicitly names "публикация"/"снятие с публикации" as audit-required actions — directly on point for this pack's core verb.                                                                                                                                                                                               |
| **CT-00-08 Identity Leakage**      | **Yes — most critical**              | Every proposed entity in section 3 exists specifically to be shown to the public; this is the test that must never regress.                                                                                                                                                                                                       |
| **CT-00-09 Vote Linkability**      | **Yes — most critical**              | `PublicLedgerEntry` records derived from `ResultPublication` must not, even in aggregate or combined across multiple ledger entries, become newly capable of resolving a `VoteEnvelope` to an `Account` — a stronger, cross-entity version of the guarantee CT-00-09 already tests within `voting-service`/`tally-service` alone. |
| CT-00-10 Rule Freeze               | Yes, narrowly                        | A published `PublicLedgerEntry`'s content must be immutable once published (analogous to `Ballot`'s configuration freeze) — redaction/correction, if ever needed, must be a new, auditable entry, never an in-place edit (INV-05).                                                                                                |
| CT-00-11 AI Human Control          | **Not applicable**                   | No `AIProcessingRecord` in this pack's proposed scope (section 1).                                                                                                                                                                                                                                                                |
| CT-00-12 Emergency Stop            | **Not applicable**                   | No `EmergencyAction` in this pack's proposed scope (section 1).                                                                                                                                                                                                                                                                   |

## 11. Privacy and redaction guarantees (summary)

- Structural, not just policy-level: every proposed schema (section 9)
  uses `additionalProperties: false` and an extended
  `FORBIDDEN_FIELD_NAMES` test (CT-00-08 precedent) explicitly covering
  `account_id`, `person_id`, `identity_record_id`, and — new for this
  pack — raw `VoteEnvelope`/`Delegation` identifiers, so that no
  Transparency entity can structurally reference vote- or
  delegation-linkable data even indirectly.
- Only aggregate `ResultPublication` counts are ever exposed for voting
  results (section 8 item 1) — never individual envelope contents.
- Two explicit open questions are deliberately left undecided by this
  specification and deferred to ADR-015's owner review, per the user's
  requirement to identify (not silently resolve) design decisions
  requiring ADRs: moderation/appeal reviewer actor-identity redaction,
  and small-cell/low-count aggregate suppression.

## 12. Definition of Done (for a future implementation pass)

Mirrors PACK-03-SPEC.md section 9's structure:

1. ADR-011 (service decomposition), ADR-012 (cross-pack read boundary),
   ADR-013 (canon addition for Transparency entities/events, canon
   `0.2.0 → 0.3.0`), ADR-014 (reason-code additions), and ADR-015
   (disclosure/redaction defaults, with items 2/3 from section 8
   explicitly decided rather than defaulted) all reach `accepted` status
   before the corresponding code is written.
2. `services/transparency-service` exists as an independent `uv`
   workspace member with its own `pyproject.toml`, `src/`, `tests/`,
   `README.md`.
3. Every entity ADR-013 defines has a JSON Schema
   (`contracts/schemas/*.json`) and, where produced by an event, an
   event-payload schema.
4. `contracts/openapi/pack-04.yaml` documents every new path, tagged
   `transparency-service`.
5. `contracts/reason-codes/pack-04.yml` exists, structurally validated,
   every literal reason code used anywhere in the new service is
   registered.
6. CT-00-01 through CT-00-10 pass for this pack's scope (section 10),
   with CT-00-08/09 given the most scrutiny per that section's notes;
   CT-00-11/12 remain genuine, documented not-applicable markers.
7. `tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
   is extended (not re-run only) for the four read edges in section 5's
   dependency matrix, and for the one-way dependency direction
   (no PACK-02/03 service may import `epd2_transparency_service`).
8. `scripts/check_repository.py`'s `REQUIRED_PATHS` extended for every
   new path.
9. `REPOSITORY_VERSION` bumped `0.3.0 → 0.4.0`; canon SHA-256 updated to
   match the post-ADR-013 canon text (recorded in a new report,
   `docs/handover/PACK-04-REPORT.md`, following the same
   revision-by-revision honest-verification structure PACK-02 and
   PACK-03 both used).
10. Exactly one clean canonical archive exported at the end, no
    pack-specific change needed to `.github/workflows/verify-and-package.yml`
    (already pack-agnostic, confirmed unchanged through three packs now).

## 13. Explicitly excluded from this pack

- **Governance Context (5.12) implementation** — system roles, authority
  policy, rules versioning, emergency procedures, crisis override, audit
  access policy, review procedures. Section 1 documents in detail why
  none of this pack's proposed scope has a hard dependency on Governance;
  if a future reviewer disagrees with that analysis, that is exactly the
  kind of disagreement this specification's separation is designed to
  surface for explicit owner decision, rather than have it discovered
  after Governance and Transparency code are already entangled.
- **AI-processing (17.1, `AIProcessingRecord`)** — "журналы ИИ" in canon
  5.11 is read as _publishing_ AI-processing logs that some future AI
  pack would create, not this pack creating or defining
  `AIProcessingRecord` itself.
- **Financial transparency** (named in 5.11's own responsibility list)
  — no canon entity anywhere in the document currently models a donation,
  expenditure, or financial-disclosure record; this needs its own
  canon-addition ADR at least as large as ADR-013, and is deliberately
  left out of this pack's already-substantial ADR-013 scope rather than
  folded in.
- **Lobby Log's real ingestion/verification mechanics** — proposed only
  as a minimal, manually-submitted record (section 8 item 4); a genuine
  lobbying-actor registry belongs to Organization Context (5.4), not yet
  implemented.
- **Frontend/UI work** — `frontend/web-shell` is unchanged by this
  specification, consistent with the user's instruction that no frontend
  implementation is expected unless strictly required for contract
  verification (it is not, for a read/publish-only service whose CT-00
  suite is backend-only, same as PACK-02/03's own contract tests).
- **Cryptographic proof beyond hash-chaining** — `AuditExportPackage`
  integrity is proposed as hash-chain verification only (same
  non-cryptographic-anonymity boundary PACK-03-SPEC.md section 10 already
  drew for `VoteEnvelope`); Merkle proofs, external notarization, or
  zero-knowledge disclosure proofs are out of scope and would be their
  own future ADR.
- **Emergency/Crisis Override (19.1)** — no proposed entity in this pack
  depends on `EmergencyAction`.

## 14. Summary — ADRs required before any implementation

| ADR     | Subject                                                                                                                | Canon impact                                    |
| ------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| ADR-011 | Service decomposition (section 4)                                                                                      | None                                            |
| ADR-012 | Cross-pack read boundary / dependency matrix (section 5)                                                               | None                                            |
| ADR-013 | Canon addition: `PublicLedgerEntry` + full Transparency entity/event catalog (section 6)                               | **Yes — canon `0.2.0 → 0.3.0`, minor**          |
| ADR-014 | Reason-code additions (section 7)                                                                                      | None (registry file, per ADR-004/006 precedent) |
| ADR-015 | Disclosure/redaction policy defaults + Lobby Log schema, with items 2/3 of section 8 requiring explicit owner decision | None                                            |

ADR-007 is reserved/unused (`docs/adr/README.md`); ADR-005/006/008/009/010
were used by PACK-03. PACK-04's ADRs therefore start at **ADR-011**.
