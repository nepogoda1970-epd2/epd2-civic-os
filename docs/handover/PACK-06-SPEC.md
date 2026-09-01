# CLAUDE-PACK-06 — AI Processing Context: Technical Specification

**Status: proposed.** This document specifies the next candidate
implementation package. It is not itself an ADR and authorizes no code.
Per canon section 26, every design decision below marked "requires ADR"
must reach `accepted` status before any corresponding working code is
written. **No PACK-06 service directory, schema, contract, ADR, or
implementation code exists yet, and canon is not edited by this
document** — this specification is the entire PACK-06 deliverable at
this stage.

This pack is different in kind from PACK-04 and PACK-05. Both of those
packs proposed entirely new entities for a context canon only sketched
in a one-line responsibility list (5.11, 5.12) or, for `RoleAssignment`,
one fully fielded but unimplemented entity. AI Processing is a third
shape again: canon already defines `AIProcessingRecord` (17.1) with
twelve fields and a six-value `human_review_status` enum, already names
its future owner ("AI Accountability Service", section 22), already
states a hard invariant about what AI may and may not do (INV-07), and
already contains one forward-declared cross-pack touchpoint — PACK-04's
own `PublicLedgerEntry.subject_type = ai_processing_record`, explicitly
built and accepted (ADR-013, D3.5) as a **currently-dormant** value
precisely so that a future AI-processing pack could exist without
Transparency ever depending on it. This is the least canon-silent
starting point of any pack so far — and also the one with the most
consequential safety requirements, since this is the first pack whose
entire subject is a system that must remain **structurally incapable**
of being anything other than advisory.

## 0. Canon dependency

This specification was authored against the current, unchanged canon
state:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  61232dc8488f1dd96ea030fa3c41bd397c1c5cf1c7c8cee484bda0568d02c202
CANON_VERSION = 0.4.0
REPOSITORY_VERSION = 0.5.0 (CLAUDE-PACK-05, externally PASSed)
```

Canon was not opened for editing to produce this specification and
remains byte-identical to the PACK-05 PASS state. Section 13 identifies
that canon would need to move `0.4.0 → 0.5.0` (a **minor** bump per
canon section 25 — additive fields/statuses/events on an
already-existing entity) if the design decisions below are accepted —
this is analysis, not an edit; no canon text has been touched.

## 1. Scope — context separation

The user's request for this pack is explicit that AI Processing,
Governance, Moderation, Transparency, Emergency/Crisis Override, and the
Identity/Credential layers must be kept conceptually distinct and never
silently combined. Checked directly against canon:

| Context / concern                               | Canon section | In PACK-06 scope                                        | Why                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------------- | ------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI Processing (`AIProcessingRecord`, INV-07)    | 17, 17.1      | **Yes**                                                 | This pack's entire subject — advisory AI assistance across the six use classes in section 5, with `AIProcessingRecord` as the sole record of every AI-assisted action.                                                                                                                                                      |
| Governance Context (`RoleAssignment` etc.)      | 5.12, 19b     | **No**                                                  | PACK-05, already implemented and PASSed. PACK-06 proposes no read or write edge into `governance-service`; a human reviewer's authorization uses this project's existing `actor_is_authorized` boolean-flag convention (section 12), not a live `RoleAssignment` read — see section 11's explicit rejection of that option. |
| Moderation Context (`ModerationCase` etc.)      | 14            | **No**                                                  | PACK-03, already implemented and PASSed. AI classification/anomaly output can at most _inform_ a human who then opens a `ModerationCase` through `moderation-service`'s own existing command — PACK-06 never opens, decides, or mutates one itself.                                                                         |
| Transparency Context (`PublicLedgerEntry` etc.) | 5.11, 19a     | **No**                                                  | PACK-04, already implemented and PASSed. `PublicLedgerEntry.subject_type = ai_processing_record` already exists (ADR-013, D3.5) and requires no change — publication, if it ever happens, is `transparency-service`'s own `publish_ledger_entry` call with caller-supplied redacted content, never a read into this pack.   |
| Emergency / Crisis Override (`EmergencyAction`) | 19, 19.1      | **No, explicitly excluded per this task's instruction** | Nothing proposed in section 3 reads, writes, or references `EmergencyAction`. No hard dependency exists in either direction.                                                                                                                                                                                                |
| Identity and Credential layers                  | 7, 9, 10      | **No**                                                  | Hard exclusion. Nothing proposed here reads `Account`, `IdentityRecord`, `EligibilityDecision`, or `ParticipationCredential` directly — only caller-supplied, already-redacted content ever reaches this pack (section 9).                                                                                                  |

**Why Emergency is not a hard dependency for PACK-06:** none of the
proposed `AIProcessingRecord` extensions (section 3) reference
`EmergencyAction` in any field, and none of the six AI use classes
(section 5) requires an emergency mechanism to exist first. Canon
section 22 labels `EmergencyAction`'s future owner "Governance / Crisis
Service" — a Governance-adjacent naming question, not an AI-processing
one; this specification takes no position on it, exactly as
`PACK-05-SPEC.md` section 4 already declined to for the same reason.

**Why Governance/Moderation/Transparency are not hard dependencies
either**, checked explicitly rather than assumed: every one of the six
AI use classes in section 5 is designed so that its only structural
output is an `AIProcessingRecord` plus, optionally, a piece of draft
text or a flag a human then acts on through that other service's own,
already-existing, unmodified command. No new field is proposed on
`Initiative`, `InitiativeVersion`, `ModerationCase`, `ModerationDecision`,
`Ballot`, `ResultPublication`, `GovernanceDecision`, `TechnicalChallenge`,
or `PublicLedgerEntry` anywhere in this document — the single canon
change proposed (section 13) is scoped entirely to `AIProcessingRecord`
itself (17.1) and its own event catalog (20.12).

## 2. Canon-textual basis and canon-silence findings

Unlike PACK-04's and PACK-05's near-total canon silence, AI Processing
already has real canon text to build from. Quoted in full because it is
short enough to:

> **INV-07. ИИ не принимает окончательное политическое решение** — ИИ
> может: структурировать; классифицировать; искать сходство; формировать
> проект резюме; выделять аргументы; указывать возможные правовые
> вопросы; предлагать модератору обратить внимание на контент. ИИ не
> может самостоятельно: отклонить инициативу; лишить пользователя права
> участия; определить итог голосования; вынести окончательное
> модерационное решение; принять апелляционное решение; изменить
> программу; выдать окончательное юридическое заключение.

> **17.1. AIProcessingRecord** — Поля: `ai_processing_record_id`,
> `purpose_code`, `target_type`, `target_id`, `input_version`,
> `model_provider`, `model_name`, `model_version`,
> `prompt_template_version`, `output_reference`, `created_at`,
> `human_review_status`, `correction_reference`. Статусы human review:
> `not_required`, `pending`, `approved`, `approved_with_changes`,
> `rejected`, `superseded`. Для официального резюме инициативы
> обязательна человеческая проверка.

This is materially more than PACK-04 or PACK-05 started with: a fully
fielded entity, an explicit allow/forbid list (INV-07), an existing
owner name (section 22: `AIProcessingRecord → AI Accountability
Service`), an existing forbidden link (section 23: `AIProcessingRecord →
скрытый IdentityRecord`, если личность не требуется для заявленной
операции), an existing five-event catalog (20.12), and one already-live
forward reference from another pack's own accepted ADR (ADR-013, D3.5,
quoted in the introduction above). Checked systematically for what is
still genuinely silent or inconsistent:

- **No processing-pipeline status exists.** `human_review_status` (six
  values) covers only the human-review dimension — it says nothing about
  whether the model call itself succeeded, timed out, produced malformed
  output, or was blocked by a policy check before a human ever saw it.
  This is the gap section 6 and section 10 (fail-closed behavior) exist
  to close. **This specification does not assume the user's proposed
  ten-value list (`requested`, `input_prepared`, `processing`,
  `completed`, `failed`, `rejected_by_policy`, `reviewed`,
  `accepted_by_human`, `rejected_by_human`, `superseded`) is canonical —
  it is not; canon defines only `human_review_status` today.** Section 6
  presents this as an explicit two-option design decision for ADR-023,
  because the user's literal list blends the (already-canonical) review
  dimension with a (not-yet-canonical) processing dimension.
- **No model/deployment/prompt-policy governance fields beyond
  `model_provider`/`model_name`/`model_version`/`prompt_template_version`.**
  Confidence/uncertainty, explanation references, redaction-before-access
  confirmation, deployment version, system-policy version, generation
  settings, processing region, data-retention mode, an external-provider
  flag, a human-reviewer reference, and content-hash/checksum fields are
  all genuinely absent from 17.1 today — section 3 proposes them, marked
  as proposals throughout.
- **No allowed/prohibited `target_type` or `purpose_code` value list.**
  Both fields exist but are open strings in canon, with no enumerated
  values — mirroring exactly how canon leaves `RoleAssignment.role_code`
  an open string (8.4) that ADR-020 then closed only at the repository
  layer, never canon. Section 8 proposes the same treatment here.
- **A naming inconsistency in the existing event catalog.** Canon 20.12
  lists five AI events: `ai.processing_requested`, `ai.output_created`,
  `ai.output_reviewed`, **`ai.output.corrected`** (a literal dot, not the
  underscore every other canonical event name in this document uses —
  compare `transparency.ledger_entry_corrected`,
  `governance.decision_rejected`), and `ai.output_rejected`. This is a
  genuine textual inconsistency, not a proposal-worthy design question —
  flagged for ADR-023 to correct to `ai.output_corrected` alongside its
  other, additive changes, rather than silently carried forward or
  silently fixed without record.
- **Two `human_review_status` values have no corresponding event at
  all.** The five existing 20.12 events cover `pending`
  (`ai.output_reviewed`, read as "entered review"),
  `approved_with_changes` (`ai.output.corrected`, typo aside), and
  `rejected` (`ai.output_rejected`) — but **`approved`** (the plain
  accept-with-no-changes outcome) and **`superseded`** both have no
  named event anywhere in 20.12. Section 6 proposes closing this gap
  (`ai.output_accepted`, `ai.processing_record_superseded`) as part of
  the same additive event-catalog extension.
- **The one existing cross-pack touchpoint requires no change.** ADR-013
  (D3.5, accepted) already added `ai_processing_record` as a
  currently-dormant `PublicLedgerEntry.subject_type` value specifically
  so a future AI-processing pack would not need a Transparency-side
  canon edit to become publishable. This specification confirms that
  value needs no modification — publication remains `transparency-
service`'s own `publish_ledger_entry` call with caller-supplied
  `raw_content`, exactly as ADR-013 already designed it, with zero read
  edge from either pack into the other (section 11).
- **Section 24 (reason-code standard)** has no codes scoped to AI
  processing, model failures, or human-review gating — section 9
  proposes an additive registry file, per the established
  ADR-006/014/019 per-pack-registry precedent, not a canon edit.
- **Section 27 (CT-00 contract tests)** reserves no new test number for
  this pack — CT-00-11 (AI Human Control) already exists and is this
  pack's central, non-negotiable test (section 15); no new CT-00 number
  is proposed.

**Conclusion, stated plainly for the record:** this pack does not need
to invent an entity from nothing, the way PACK-04 invented
`PublicLedgerEntry` or PACK-05 invented `GovernancePolicy`. It needs to
**extend** an already-real entity with the governance/provenance/
explainability/fail-closed fields a genuinely safety-critical advisory
system requires, resolve one real internal tension in how the user's
requested status lifecycle maps onto canon's already-existing
`human_review_status` enum (section 6), and correct one small textual
inconsistency (the `ai.output.corrected` typo) found along the way.

## 3. Proposed `AIProcessingRecord` field extensions (requires ADR-023)

Canon 17.1's twelve existing fields are **unchanged** by this proposal —
listed here only for contrast with what is newly proposed:

**Existing (canon 17.1, unchanged):** `ai_processing_record_id`,
`purpose_code`, `target_type`, `target_id`, `input_version`,
`model_provider`, `model_name`, `model_version`,
`prompt_template_version`, `output_reference`, `created_at`,
`human_review_status`, `correction_reference`.

**Proposed new fields, grouped by purpose (all pending ADR-023, none
exist in canon today):**

- **Model and deployment governance** (item 10 of the user's request):
  `deployment_version` (the running deployment/build identifier, distinct
  from `model_version`), `system_policy_version` (the safety/system
  prompt or policy configuration version in effect, distinct from
  `prompt_template_version`, which already exists), `generation_settings`
  (a small structured record of decoding parameters — temperature or an
  equivalent — captured only where the underlying model exposes them;
  never assumed present for every provider), `processing_region` (where
  the inference actually ran), `data_retention_mode` (one of a proposed
  closed set — section 10's fail-closed defaults propose the values),
  `external_provider_flag` (boolean; distinguishes a self-hosted model
  from a third-party API provider — load-bearing for section 8's "no
  external provider gains system-of-record authority" guarantee).
- **Provenance and integrity** (item 10's "checksum or content-hash
  references"): `input_hash` and `output_hash` (content-hash digests of
  the _prepared, already-redacted_ input and the raw model output,
  computed the same way `content_hash` is already computed on
  `InitiativeVersion`/`PublicLedgerEntry` elsewhere in this repository —
  never the raw pre-redaction input itself, which is never stored, per
  section 9).
- **Confidence and uncertainty** (item 1/11): `confidence_score` (a
  bounded numeric or categorical indicator, meaning defined per
  `purpose_code` — a classification confidence is not the same
  measurement as a summarization confidence, and this field does not
  pretend otherwise) and `uncertainty_indicator` (a structured flag for
  cases where the model itself signals low certainty, distinct from a
  numeric confidence score, for providers that expose one but not the
  other).
- **Explainability** (item 11, section 7): `explanation_reference` (a
  structured reference — reason codes plus evidence references, never
  free-form private content) and `reason_codes` (the list of this pack's
  own registry codes, section 9, that explain _why_ a given output was
  produced or blocked — not a restatement of the model's internal
  reasoning, which this pack never claims to have access to, section 7).
- **Redaction and human-reviewer provenance**: `redaction_policy_reference`
  and `redaction_applied` (confirms, structurally, that the minimum-
  necessary redaction step — section 9 — actually ran before the model
  ever saw the input; `redaction_applied = false` is a fail-closed
  condition, section 10) and `human_reviewer_reference` (an opaque
  reference to the reviewing actor's authorization, mirroring
  `TechnicalChallenge.submitter_authorization_reference`'s existing
  caller-supplied-opaque-reference pattern, canon 19b.4 — never a raw
  identity, never a `RoleAssignment` UUID exposed in public output).
- **Lifecycle timestamps** (item 10's "timestamps", plural — `created_at`
  already exists): `completed_at` (when a terminal `processing_status`,
  section 6, was reached) and `reviewed_at` (when `human_review_status`
  last changed).
- **Processing-pipeline status**: `processing_status` — its own proposed
  enum, kept deliberately distinct from `human_review_status`; section 6
  is this proposal's own dedicated design decision, not folded in here,
  because it is the one genuine two-option tension this specification
  found (section 2).

No field is proposed on any entity other than `AIProcessingRecord`
itself. This is a **minor** canon version change under section 25
("Добавление обратно совместимой сущности, поля, события или статуса")
— every new field is additive and backward-compatible; no existing
field's meaning, type, or owner changes.

## 4. Proposed AI use classes (item 8)

Six classes, each directly traceable to INV-07's own allow-list
("структурировать; классифицировать; искать сходство; формировать
проект резюме; выделять аргументы; указывать возможные правовые
вопросы; предлагать модератору обратить внимание на контент") plus the
user's explicit anomaly-indication and policy-compliance-assistance
additions. Every class shares three properties, stated once here rather
than repeated six times: **(a)** allowed inputs are always
already-redacted, minimum-necessary content (section 9) — never raw
identity, credential, or vote data; **(b)** required human control is
never optional — every class is advisory only, per INV-07 and section 8;
**(c)** every invocation creates exactly one `AIProcessingRecord`
(section 6), regardless of outcome, including failures (section 10).

### 4.1. Summarization

Drafting a candidate summary of an `InitiativeVersion`, `Discussion`, or
set of `Contribution`s (INV-07's "формировать проект резюме"). Canon
17.1's own closing line — "для официального резюме инициативы
обязательна человеческая проверка" — makes this class's human-review
requirement canon-explicit already, not merely this pack's own policy.
**Allowed inputs:** already-public or already-authorized-for-processing
initiative/discussion/contribution text. **Prohibited inputs:** any
identity/account field, `ParticipationCredential` content, `VoteEnvelope`
content, unrestricted `AuditEvent` export. **Allowed outputs:** draft
summary text, `output_reference` to the draft artifact. **Required human
control:** mandatory pre-publication human review (canon-stated).
**Public disclosure:** only the human-approved final text, through that
entity's own existing publication path (`InitiativeVersion` creation,
or optionally a future `transparency-service` `PublicLedgerEntry` of
`subject_type = ai_processing_record`) — never the raw draft.
**Retention:** short, redacted by default (section 10 default).
**Audit:** `AIProcessingRecord` always; an `AuditEvent` on the human's
own accept/reject action, per CT-00-07.

### 4.2. Classification

Categorizing `Contribution`/`Initiative` content for a human moderator's
attention (INV-07's "классифицировать" and "предлагать модератору
обратить внимание на контент"), or duplicate/similarity detection
against existing `Initiative`/`SupportRecord` entries ("искать сходство").
**Allowed inputs:** the content already visible in context, redacted of
participant identity (CT-00-08 boundary carried forward). **Prohibited
inputs:** raw account/identity data. **Allowed outputs:** category
labels, a similarity score, a suggested (not created) `trigger_type`
value a human may use when opening a `ModerationCase` through
`moderation-service`'s own existing command. **Required human control:**
mandatory — canon INV-07 forbids AI from reaching a final moderation
decision; this class never opens or decides a `ModerationCase` itself.
**Public disclosure:** none by default (internal signal). **Retention:**
short, redacted. **Audit:** `AIProcessingRecord` always; no `AuditEvent`
unless and until a human acts, at which point the human's own action
(through `moderation-service`) creates it, optionally referencing this
`AIProcessingRecord`.

### 4.3. Recommendation

General "consider this" suggestions to a human actor — related
`SourceRecord`s, possible legal questions (INV-07's "указывать возможные
правовые вопросы"), or argument extraction ("выделять аргументы").
**Allowed / prohibited inputs:** identical boundary to 4.1/4.2.
**Allowed outputs:** ranked suggestions, `confidence_score`,
`explanation_reference`. **Required human control:** advisory only; the
human decides whether to act, through whichever entity's own existing
command applies. **Public disclosure:** none by default. **Retention:**
short. **Audit:** `AIProcessingRecord` only, unless a human action
follows.

### 4.4. Drafting

Drafting text for a human to incorporate into an entity another service
owns — an `InitiativeVersion.problem_statement`/`proposed_solution`, a
`GovernanceDecision`'s rationale text, a `ModerationDecision.
public_explanation`. **Allowed inputs:** the human-supplied prompt/
context, already redacted. **Prohibited inputs:** identical boundary,
plus never seeded directly from secret-ballot content or an unrestricted
audit export. **Allowed outputs:** draft text only —
**structurally never written directly to any other service's storage**
(section 8's non-authority guarantee applies with full force to this
pack's own output, not only to external providers). **Required human
control:** mandatory; a draft becomes real entity content only when a
human explicitly submits it through that entity's own existing
create/publish command. **Public disclosure:** only the human-finalized
entity, through its own existing channel. **Retention:** the draft is
retained only long enough for human review, then redacted/ephemeral by
default. **Audit:** `AIProcessingRecord` plus the eventual human
`AuditEvent` on whatever entity is actually created.

### 4.5. Anomaly indication

Flagging statistically unusual patterns (submission-rate anomalies
across `SupportRecord`/`VoteEnvelope` counts, timing irregularities) for
human integrity review — never a fraud conclusion, never an invalidation.
**Allowed inputs:** aggregate/statistical signals only — counts, rates,
timing distributions. **Prohibited inputs:** any individual
`VoteEnvelope` content, any identity-linked participation data, any
unrestricted `AuditEvent` export — INV-06/CT-00-09's secrecy boundary
applies with full, unweakened force; an anomaly signal is computed over
aggregates a caller has already prepared, never over raw secret-ballot
content this service is ever given access to. **Allowed outputs:** an
anomaly flag, `confidence_score`, aggregate (non-identifying) evidence
references. **Required human control:** mandatory and structurally
bounded — an anomaly indication can at most prompt a human to submit a
`TechnicalChallenge` (`governance-service`) or open a `ModerationCase`
(`moderation-service`); it can **never** itself invalidate a ballot or
determine result finality, both explicitly listed prohibited autonomous
actions (section 8). **Public disclosure:** none by default. **Retention:**
short, redacted, aggregate-only. **Audit:** `AIProcessingRecord`; any
resulting `TechnicalChallenge`/`ModerationCase` is its own,
separately-audited human-initiated action.

### 4.6. Policy-compliance assistance

An advisory pre-check against structural rules (redaction completeness,
forbidden-field presence) on a draft `GovernancePolicy`,
`ModerationDecision`, or `LobbyLogEntry`, layered **on top of**, never
**instead of**, the deterministic structural checks already enforced in
code (e.g. `transparency-service`'s own `assert_no_forbidden_fields`,
which is ordinary Python, not AI, and remains the actual enforcement
mechanism, per INV-10). **Allowed inputs:** the draft content, redacted.
**Prohibited inputs:** identical boundary. **Allowed outputs:** a
compliance-flag list, `confidence_score`, `explanation_reference` —
never a binding pass/fail. **Required human control:** mandatory; a
compliance-assistance flag never blocks or approves anything by itself.
**Public disclosure:** none by default. **Retention:** short. **Audit:**
`AIProcessingRecord` only.

## 5. Reference table — use classes at a glance

| Use class                    | Mandatory human review     | Default public disclosure       | Default retention               |
| ---------------------------- | -------------------------- | ------------------------------- | ------------------------------- |
| Summarization                | Yes (canon-stated)         | Only the human-approved text    | Short, redacted                 |
| Classification               | Yes                        | None                            | Short, redacted                 |
| Recommendation               | Yes (advisory)             | None                            | Short                           |
| Drafting                     | Yes                        | Only the human-finalized entity | Short, then redacted            |
| Anomaly indication           | Yes (structurally bounded) | None                            | Short, redacted, aggregate-only |
| Policy-compliance assistance | Yes                        | None                            | Short                           |

## 6. Design decision D1 — `processing_status`, and its relationship to the existing `human_review_status` (requires ADR-023)

This is the one genuine internal tension this specification's own
canon-cross-reference (section 2) found, and it is presented as an
explicit choice rather than silently resolved:

**The tension.** The user's requested lifecycle
(`requested`, `input_prepared`, `processing`, `completed`, `failed`,
`rejected_by_policy`, `reviewed`, `accepted_by_human`, `rejected_by_human`,
`superseded`) blends two conceptually different tracks into one list:
a **technical processing-pipeline** track (did the model call itself
succeed?) and the **human-review** track canon's `human_review_status`
already owns (`not_required`, `pending`, `approved`,
`approved_with_changes`, `rejected`, `superseded`).

- **Option A — two orthogonal fields (recommended).** Add a new field,
  `processing_status`, scoped **only** to the technical-pipeline portion:
  `requested → input_prepared → processing → {completed | failed |
rejected_by_policy}`, plus its own `superseded` value meaning "this
  processing run was superseded by a later re-attempt for the same
  `purpose_code`/`target_type`/`target_id`" — a different, narrower
  meaning than `human_review_status.superseded`'s "this review outcome
  was superseded by a later review," kept deliberately distinct rather
  than conflated. `human_review_status` is **left completely unchanged**
  — still six values, still canon 17.1's own text, still meaning exactly
  what it means today. A `completed` `processing_status` is simply the
  precondition for `human_review_status` to leave `not_required`/`pending`
  at all. This is a **minor**, additive-only canon change: two fields,
  each with its own closed enum, neither altering the other's existing
  meaning.
- **Option B — fold everything into one field, as the user's list
  literally reads.** Replace `human_review_status` with a single, wider
  `processing_status` covering both tracks in one ten-value enum. **Not
  recommended.** This would change the _meaning_ of an existing canon
  field (`human_review_status`) — canon section 25 classifies "изменение
  смысла события" and "жизненного цикла критического объекта" as
  **major**, not minor, changes. It would also need an eleventh value
  (`approved_with_changes` has no clean equivalent among `reviewed`/
  `accepted_by_human`/`rejected_by_human`) to stay lossless, meaning the
  user's literal ten-value list cannot represent today's canon text
  without either dropping a value or growing an eleventh one — worth the
  project owner seeing plainly rather than having it silently
  "resolved" by dropping `approved_with_changes`.

**This specification's working recommendation is Option A**, because it
is the only one of the two that keeps this change at **minor** canon
severity and leaves canon 17.1's own already-accepted text completely
untouched. **This must be ratified as ADR-023** before either field is
implemented; no PACK-06 code may assume either option until then.

**Proposed `processing_status` values (Option A):** `requested` →
`input_prepared` → `processing` → `completed` | `failed` |
`rejected_by_policy`; `superseded` (technical re-run only, see above). No
value in this new field ever implies a human-review outcome — that
remains `human_review_status`'s job, unchanged.

**Proposed event-catalog additions (20.12, same ADR-023):** the existing
five events are unchanged in meaning; one typo is corrected
(`ai.output.corrected → ai.output_corrected`, section 2), and four new
events are proposed: `ai.input_prepared`, `ai.processing_failed`,
`ai.processing_rejected_by_policy`, `ai.processing_record_superseded`,
plus `ai.output_accepted` to give the plain `approved` outcome its own
event name (section 2 found it currently has none). Twelve total after
the ADR: five existing (one corrected), five processing-pipeline
additions, one review-outcome completion (`ai.output_accepted`), and
one review-outcome supersession (`ai.output_record_superseded` — kept
textually distinct from `ai.processing_record_superseded` above, for the
same reason the two `superseded` field values above are kept distinct).

## 7. Explainability without storing unnecessary private content (item 11)

Directly extends INV-09 ("отказ должен быть объяснимым" — machine reason
code, human-readable explanation, applied-rule reference, valid next
step, appeal path if one exists) to every AI-assisted action, not only
to outright rejections:

- **Structured reason codes** (section 9) — every non-`completed`
  `processing_status` and every non-`approved` `human_review_status`
  carries at least one reason code from this pack's own registry.
- **Evidence references** — `explanation_reference` (section 3) points
  to structured, already-redacted evidence (which input snippet, which
  matched rule, which aggregate signal) — never a raw excerpt of private
  content beyond what the use class already permits as input (section 4).
- **Uncertainty indicators** — `confidence_score`/`uncertainty_indicator`
  (section 3) are surfaced alongside every output, not only failures, so
  a reviewing human can weigh low-confidence output appropriately rather
  than treating every AI output as uniformly authoritative.
- **A human-readable summary** — a short, structured explanation string,
  generated deterministically from the reason code(s) and evidence
  references above, not a restatement of anything resembling model
  "reasoning."
- **No claim of access to hidden reasoning.** This specification
  explicitly does **not** propose storing, exposing, or claiming access
  to a model's internal chain-of-thought or hidden reasoning trace, for
  any provider. `explanation_reference` is built entirely from this
  pack's own structured reason codes and evidence references — never
  from provider-internal reasoning output, which this pack treats as
  unavailable and unverifiable by design, regardless of what any given
  provider's API might expose.

## 8. Prohibited autonomous actions and human-control invariants (items 2–3)

**Structural, not merely documented.** Every action below is prohibited
because **no PACK-06 command exists, or will ever be proposed, that
could perform it** — not because a runtime check happens to catch an
attempt. `AIProcessingRecord` is a record of advisory output; it is
never itself an authorization, and no other service's command accepts
an `AIProcessingRecord` reference as a substitute for that service's own
existing authorization/approval mechanism.

AI must never autonomously: approve or reject an `Initiative`; invalidate
a `Ballot`; determine result finality; assign or revoke a `RoleAssignment`;
impose a `ModerationDecision` sanction; publish an official
`GovernanceDecision`; execute an `EmergencyAction`; deanonymize a
participant; reconstruct vote linkage; change canonical policy or rules
(the canon document itself, or any `GovernancePolicy`/`DisclosurePolicy`).
Every one of these actions already belongs, exclusively, to another
pack's own existing (PACK-03/04/05) or not-yet-built (Emergency) command
surface — this pack proposes **zero** new commands on any of those
entities, and **zero** read-or-write edge that would let it call one
(section 11).

**Every consequential AI-assisted action requires, structurally:**

1. **A human decision-maker** — identified via `human_reviewer_reference`
   (section 3), never bypassed.
2. **An explicit human confirmation** — a real state transition on
   `human_review_status` (`pending → approved` /
   `approved_with_changes` / `rejected`), never inferred from silence,
   a timeout, or a default value.
3. **A recorded `AIProcessingRecord`** — created for every invocation,
   including every failure mode (section 10), never only for successes.
4. **A reference to the final human decision** — `correction_reference`
   (existing canon field) or the entity the human ultimately created/
   modified through its own owning service's command, so the
   `AIProcessingRecord` and the real-world outcome are always linkable.
5. **A structural distinction between AI recommendation and human
   outcome** — the `AIProcessingRecord`'s own `output_reference` (the
   AI's draft/suggestion) is never the same value as the entity the
   human actually publishes; the two are always separately identifiable,
   so no report or export could conflate "the AI suggested this" with
   "a human decided this."

## 9. Redaction before model access and the data-flow/privacy boundary (item 5)

**Minimum necessary, already-redacted input only.** This pack's own
commands accept only content the caller has already prepared and
redacted — this pack never reaches into any other service's storage to
assemble its own input (section 11 rejects that option explicitly).
Structurally forbidden from ever appearing in input this pack receives,
mirroring and extending canon's own `FORBIDDEN_FIELD_NAMES` precedent
(PACK-04's `assert_no_forbidden_fields`, section 8 there): raw identity
data (`Account`, `IdentityRecord` fields), `ParticipationCredential`
secret content, `VoteEnvelope` content or any field that would allow
reconstructing vote linkage, secret-ballot content of any kind, and an
unrestricted `AuditEvent` export (only the same kind of already-redacted,
target-type-scoped summary `AuditExportPackage` already produces,
canon 19a.2, may ever reach this pack — never a raw `AuditEvent` stream).
`redaction_applied` (section 3) is a structural field precisely so a
missing or failed redaction step is a recorded, fail-closed condition
(section 10), not a silent gap.

**No model provider may become a system-of-record.** `AIProcessingRecord`
itself, owned entirely by `ai-processing-service` (section 11), is the
only system-of-record this pack introduces. A model provider never
receives write access to any Civic OS storage, never receives an
`actor_id` or credential capable of calling any other service's command,
and `external_provider_flag` (section 3) makes this distinction
structurally visible on every record rather than implicit.

**External providers never gain mutating authority.** This is the same
guarantee section 8 states for this pack's own drafting output, applied
one layer further out: whatever a third-party model API returns is
**always** treated as `output_reference`-shaped draft content requiring
the full human-review path (section 8) — never as a command, an
approval, or a state transition on any entity, regardless of how
confidently or authoritatively an external response is phrased.

## 10. Fail-closed behavior (item 4, requires ADR-025)

Directly extends INV-10 ("если система не может надёжно подтвердить...
операция не выполняется... неопределённость не трактуется как
разрешение") to the ten failure classes the user specifically named.
Each maps to a `processing_status` outcome (section 6) and a reason code
(section 9) — no failure is silent, per INV-09:

| Failure class             | `processing_status` outcome                                                               | Notes                                                                                                                                                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unavailable model         | `failed`                                                                                  | No retry-until-success loop proposed; a caller may resubmit as a new, separately-recorded request.                                                                                                                  |
| Timeout                   | `failed`                                                                                  | Same as above.                                                                                                                                                                                                      |
| Malformed output          | `failed`                                                                                  | The raw malformed output is never forwarded to a human as if valid; `output_reference` records the failure, not fabricated content.                                                                                 |
| Unsupported model version | `rejected_by_policy`                                                                      | Checked against a repository-level allow-list (section 8 default), never silently accepted.                                                                                                                         |
| Low confidence            | `completed`, but `human_review_status` forced to `pending` with an elevated-scrutiny flag | Low confidence is surfaced, never hidden or silently upgraded to "confident" (section 7).                                                                                                                           |
| Policy conflict           | `rejected_by_policy`                                                                      | E.g. a `purpose_code`/`target_type` combination outside the repository's allowed set (section 8).                                                                                                                   |
| Redaction failure         | `rejected_by_policy`                                                                      | `redaction_applied = false` — processing never proceeds on unredacted input, full stop (section 9).                                                                                                                 |
| Prompt-injection signal   | `rejected_by_policy`                                                                      | Detected by a caller-side or repository-side check before/при submission; this pack does not claim a complete injection-detection capability, only that a detected signal is fail-closed, never silently processed. |
| Prohibited data detected  | `rejected_by_policy`                                                                      | The structural forbidden-input list (section 9) is checked before any model call, not after.                                                                                                                        |
| Missing human reviewer    | Blocks `human_review_status` progression                                                  | A `completed` `AIProcessingRecord` with no assigned `human_reviewer_reference` cannot advance past `pending` — never defaults to `approved`.                                                                        |

**Uncertainty is never treated as permission**, restated for this pack's
own domain exactly as INV-10 already states it generally: any of the ten
conditions above defaults to blocking progress, never to proceeding
optimistically.

## 11. Design decision D2 — service decomposition (requires ADR-021)

Proposed: **one** new service, following the same "one service per
canon-named owner with no forbidden-link conflict" test PACK-03/04/05
all applied:

- **`services/ai-processing-service`** (`epd2_ai_processing_service`) —
  owns `AIProcessingRecord` exclusively, matching canon section 22's
  already-existing owner label, "AI Accountability Service" (the
  developer-facing service directory name need not match that prose
  label verbatim — the same convention already established for
  `governance-service` owning "Permission / Role Service"'s
  `RoleAssignment`, and `audit-core` owning "Audit Core").

This is a small, single-entity service — proportionate to a pack whose
entire canon surface is one entity (section 3) plus its own event
catalog, comparable in size to PACK-04's transparency-service at its own
specification stage. **This decomposition must be ratified as ADR-021**
before any service directory is created.

## 12. Design decision D3 — cross-pack dependency matrix and read boundary (requires ADR-022)

**Proposed: zero cross-pack dependencies, in either direction** — a
stronger, narrower boundary than any prior pack has proposed for itself.

| Upstream/downstream service                                                                                                           | Read or write edge with `ai-processing-service`? | Why                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `initiative-service`, `deliberation-service`, `moderation-service`, `voting-service`, `tally-service`, `delegation-service` (PACK-03) | **No**                                           | `target_type`/`target_id` (canon 17.1, unchanged) are accepted as caller-supplied, opaque references — never dereferenced or validated for existence by this pack (Option B below). The caller (a human-facing orchestration layer, not this service) is responsible for supplying already-redacted input.                                                       |
| `governance-service` (PACK-05)                                                                                                        | **No**                                           | Human-reviewer authorization uses the existing project-wide `actor_is_authorized` boolean-flag convention (every PACK-02/03/04/05 command already works this way — even `governance-service`'s own two-actor approval check compares `RoleAssignment.actor_id` values it already stores itself, never a cross-pack read) — not a new live `RoleAssignment` read. |
| `transparency-service` (PACK-04)                                                                                                      | **No**                                           | `PublicLedgerEntry.subject_type = ai_processing_record` (ADR-013, D3.5, already accepted) is designed to be populated by a caller-supplied, already-redacted `raw_content` snapshot — the existing, already-implemented `publish_ledger_entry` command, never a read into this pack's storage.                                                                   |
| `account-service`, `identity-service`, `eligibility-service`, `credential-service` (PACK-02)                                          | **No**                                           | Hard exclusion, same reasoning every prior pack's cross-pack ADR gave: nothing this pack does needs identity or credential data directly.                                                                                                                                                                                                                        |
| `epd2_audit_core` (PACK-02)                                                                                                           | **No**                                           | This pack creates its own audit trail via `epd2_audit_core` the same way every other service does (a write, not a read) — no read-back dependency is proposed.                                                                                                                                                                                                   |

**The one real design choice, presented rather than silently decided:**

- **Option A — validate `target_type`/`target_id` via reads into each
  upstream service.** Would require up to six new read edges (one per
  PACK-03 service, plus PACK-04/05) just to confirm a caller-supplied
  reference points to something real. **Not recommended** — it would
  make `ai-processing-service` this project's single most
  cross-pack-coupled service, for a marginal benefit (existence-checking
  a reference this pack never otherwise uses), directly working against
  the "structurally isolated, advisory-only" design goal sections 8–9
  establish.
- **Option B — caller-supplied, opaque, never dereferenced (recommended).**
  Mirrors the precedent already established twice in this project:
  `TechnicalChallenge.submitter_authorization_reference` (canon 19b.4)
  and `PublicLedgerEntry`'s own `subject_id`/`content_snapshot` pair
  (canon 19a.1) are both caller-supplied and never independently
  re-verified by the service that stores them. This specification
  recommends the same treatment for `target_type`/`target_id`.

**This must be ratified as ADR-022** before any cross-pack import — read
or otherwise — exists in code (there should be none). If accepted as
proposed, `tests/repository/test_service_boundaries.py`'s forbidden-pair
matrix gains a new row confirming `ai-processing-service` imports
**nothing** from any other pack's `application`/`domain`/`storage`
module — the strictest boundary entry in that matrix so far.

## 13. Canon version impact (item 15)

Section 3 (new `AIProcessingRecord` fields) and section 6 (new
`processing_status` field/enum plus five event-catalog additions and one
typo correction) are both additive, backward-compatible changes to an
already-existing entity and its already-existing event catalog — this
is a **minor** version bump under canon section 25
("Добавление обратно совместимой сущности, поля, события или статуса"),
the same category ADR-010, ADR-013, and ADR-018 each already used:

```text
CANON_VERSION 0.4.0 → 0.5.0  (proposed; not performed by this document)
```

Consistent with this project's own established sequencing
(`docs/adr/README.md`; ADR-010/013/018 pattern): the canon edit itself
would be performed only after the corresponding ADR (ADR-023) reaches
`accepted`, as its own separate, dedicated task — never inside this
specification, and never inside the ADR-drafting step itself.
`REPOSITORY_VERSION` (currently `0.5.0`, PACK-05 PASS) is unaffected by
a canon-only edit — it would move to `0.6.0` only once
`ai-processing-service` implementation code actually lands, mirroring
exactly how PACK-04's and PACK-05's own canon-only rounds left
`REPOSITORY_VERSION` untouched until their respective implementation
passes.

## 14. Reason codes (requires ADR-024)

Canon section 24's fixed list has no codes scoped to AI processing.
Proposed additive codes for `contracts/reason-codes/pack-06.yml`
(ADR-006/014/019 precedent — a new per-pack registry file, not a canon
edit):

`AI_MODEL_UNAVAILABLE`, `AI_PROCESSING_TIMEOUT`, `AI_OUTPUT_MALFORMED`,
`AI_MODEL_VERSION_UNSUPPORTED`, `AI_CONFIDENCE_BELOW_THRESHOLD`,
`AI_POLICY_CONFLICT`, `AI_REDACTION_FAILURE`,
`AI_PROMPT_INJECTION_SUSPECTED`, `AI_PROHIBITED_INPUT_DETECTED`,
`AI_HUMAN_REVIEWER_MISSING`, `AI_HUMAN_REVIEW_REQUIRED`,
`AI_OUTPUT_REJECTED_BY_HUMAN`, `AI_PROCESSING_RECORD_SUPERSEDED`,
`AI_AUTONOMOUS_ACTION_PROHIBITED` (the structural guard code raised if
any caller attempts to treat an `AIProcessingRecord` as if it were an
authorization for another service's command), `AI_TARGET_REFERENCE_MALFORMED`
(a basic structural check on the caller-supplied `target_type`/`target_id`
shape — not an existence check, per section 12's Option B).

Reused generic codes (already defined in other packs' registries, per
the established Option B multi-registry pattern): `PERMISSION_DENIED`,
`VALIDATION_UNKNOWN_STATUS`, `VALIDATION_FORBIDDEN_TRANSITION`,
`VALIDATION_RECORD_NOT_FOUND`. Reused canon-fixed codes (section 24):
`EVENT_VERSION_UNSUPPORTED`, `INTEGRITY_CHECK_FAILED`.

## 15. Design decision D4 — AI use-class policy, redaction defaults, and repository-level allow-lists (requires ADR-025)

Conservative, fail-closed defaults proposed for the project owner's
review, in the same spirit as ADR-009's and ADR-020's own section-level
defaults — proposals, not decisions:

1. **Closed `purpose_code`/`target_type` allow-lists.** Canon leaves both
   fields open strings (section 2). Proposed: a repository-level
   (application-layer only, never canon-level) closed set for the pilot
   — `purpose_code` drawn from the six use classes (section 4);
   `target_type` drawn from `initiative_version`, `discussion`,
   `contribution`, `moderation_case`, `support_record_aggregate`
   (an aggregate-only shape for anomaly indication, never a raw
   `VoteEnvelope`/`SupportRecord`), `governance_policy_draft`,
   `moderation_decision_draft` — mirroring exactly how ADR-020 closed
   `RoleAssignment.role_code` only at the repository layer, never canon.
2. **Default `data_retention_mode`.** Proposed: `redacted_ephemeral` as
   the default for every use class (section 5) unless a specific
   `purpose_code` explicitly requires longer retention for audit
   purposes — never `retained_full` by default for any class.
3. **Default confidence threshold.** Proposed: a repository-configurable
   per-`purpose_code` minimum `confidence_score`, below which
   `human_review_status` is forced to `pending` with an elevated-scrutiny
   flag rather than silently proceeding (section 10) — the exact
   threshold value is left to implementation-time configuration, not
   fixed by this specification.
4. **External-provider restriction.** Proposed: `external_provider_flag
= true` is disallowed outright for any `target_type` touching
   aggregate voting/tally data (`support_record_aggregate` and any
   future anomaly-indication target type) — anomaly indication over
   participation patterns runs only on self-hosted models, never a
   third-party API, regardless of redaction, as an additional
   defense-in-depth layer beyond section 9's structural input
   restrictions. **Open question, not resolved by this specification:**
   whether this restriction should extend to every use class or remain
   scoped to anomaly indication alone.
5. **Who may act as `human_reviewer_reference`?** **Open question, not
   resolved by this specification**, mirroring ADR-020's own
   role-taxonomy deferral: this pack proposes no new `RoleAssignment`
   role code and no read into `governance-service` (section 12) — the
   reviewer's authorization is asserted via the existing
   `actor_is_authorized` boolean-flag convention. Whether a future
   hardening pass should instead require a real, governance-service-
   verified role is explicitly left to the project owner, not defaulted
   here.

**This must be ratified as ADR-025** before any use-class policy,
retention default, or allow-list ships, with items 4 and 5 specifically
requiring the project owner's explicit decision rather than accepting
this document's conservative defaults by silence.

## 16. Schemas and OpenAPI scope

Following the existing repository convention exactly
(`contracts/schemas/`, currently 32 files across PACK-02/03/04/05;
`contracts/openapi/pack-02.yaml` through `pack-05.yaml`):

- `contracts/schemas/ai-processing-record.schema.json` — one JSON Schema
  for the extended entity (section 3), pending ADR-023 for the exact
  field list.
- `contracts/events/ai-processing-record-payload.v1.schema.json` — one
  shared public-payload shape across the (proposed) twelve canonical
  events (section 6), following the existing one-schema-per-shared-
  payload-shape convention (e.g. `governance-*-payload.v1.schema.json`).
- `contracts/openapi/pack-06.yaml` — one path per real application
  command, tagged `ai-processing-service`, same tagging convention as
  `pack-05.yaml`. No path is added to any other pack's OpenAPI file —
  unlike PACK-05's `invalidateBallot` addition to `pack-03.yaml`, this
  pack proposes zero new commands on any other service (section 12).

## 17. CT-00 applicability (item 12)

| Contract test                      | Applies to PACK-06?                                        | Notes                                                                                                                                                                                                                                                            |
| ---------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-00-01 Schema Validation         | Yes                                                        | Standard, once schemas exist (section 16).                                                                                                                                                                                                                       |
| CT-00-02 Unknown Status            | Yes                                                        | Both `processing_status` (new, pending ADR-023) and `human_review_status` (existing, unchanged) get real coverage.                                                                                                                                               |
| CT-00-03 Forbidden Transition      | Yes                                                        | E.g. `processing_status` may never jump `requested → completed` without passing through `input_prepared`/`processing`; `human_review_status`'s existing rules are unchanged.                                                                                     |
| CT-00-04 Event Idempotency         | Yes                                                        | Every command needs a caller-supplied idempotency key, continuing this project's established convention.                                                                                                                                                         |
| CT-00-05 Unsupported Event Version | Yes                                                        | Standard mechanism, exercised against section 6's proposed event additions.                                                                                                                                                                                      |
| CT-00-06 Missing Permission        | Yes                                                        | Every command remains gated by the existing `actor_is_authorized` boolean-flag convention (section 12).                                                                                                                                                          |
| CT-00-07 Audit Creation            | Yes                                                        | Every `AIProcessingRecord` creation and every `human_review_status` transition is audited, per section 8.                                                                                                                                                        |
| CT-00-08 Identity Leakage          | Yes                                                        | The structural forbidden-input list (section 9) is this pack's direct extension of CT-00-08's existing guarantee.                                                                                                                                                |
| CT-00-09 Vote Linkability          | Yes, narrowly                                              | Anomaly indication (section 4.5) is the one use class touching voting-adjacent aggregates; it must never expose or reconstruct individual `VoteEnvelope` linkage.                                                                                                |
| CT-00-10 Rule Freeze               | Not directly applicable                                    | `AIProcessingRecord` has no "open ballot"-shaped configuration-freeze window; not proposed as a forced-applicable test for this pack.                                                                                                                            |
| **CT-00-11 AI Human Control**      | **Yes — fully applicable and central, for the first time** | Every prior pack (PACK-02 through PACK-05) marked this genuinely not-applicable because no `AIProcessingRecord` existed anywhere. This is the pack that finally gives it real content: section 8's human-control invariants are exactly what this test verifies. |
| CT-00-12 Emergency Stop            | **Not applicable**                                         | `EmergencyAction` explicitly excluded from this pack's scope (section 1), per the user's instruction; no hard dependency exists.                                                                                                                                 |

## 18. Privacy and separation guarantees (summary)

- Structural, not just policy-level: the proposed schema (section 16)
  uses `additionalProperties: false`, following CT-00-08's established
  precedent.
- The redaction boundary (section 9) is proposed as an unconditional
  precondition, checked before any model call, mirroring PACK-04's
  `assert_no_forbidden_fields` "checked first, independent of any other
  rule" structure.
- The cross-pack boundary (section 12) is deliberately the narrowest
  proposed anywhere in this project — zero edges in either direction —
  so that no other pack's own code needs to change to accommodate this
  one, and this pack's own removal (if ever needed) would touch no other
  service.
- Four explicit open questions are deliberately left undecided by this
  specification and deferred to ADR-025's owner review: the scope of the
  external-provider restriction (section 15 item 4), who may act as
  `human_reviewer_reference` (section 15 item 5), and — carried from
  section 6 — the two-option `processing_status`/`human_review_status`
  design choice itself, which is presented, not silently resolved, for
  ADR-023.

## 19. Definition of Done (for a future implementation pass)

Mirrors `PACK-05-SPEC.md` section 15's structure:

1. ADR-021 (service decomposition), ADR-022 (cross-pack boundary —
   confirming zero dependencies, section 12), ADR-023 (canon addition:
   `AIProcessingRecord` field/status/event extension, canon
   `0.4.0 → 0.5.0`, plus the `processing_status`/`human_review_status`
   design decision and the `ai.output.corrected` typo fix), ADR-024
   (reason-code additions), and ADR-025 (use-class policy, redaction
   defaults, allow-lists, with items 4 and 5 from section 15 explicitly
   decided rather than defaulted) all reach `accepted` status before the
   corresponding code is written.
2. `services/ai-processing-service` exists as an independent `uv`
   workspace member with its own `pyproject.toml`, `src/`, `tests/`,
   `README.md`.
3. `AIProcessingRecord`'s extended field set (section 3) has a JSON
   Schema and an event-payload schema (section 16).
4. `contracts/openapi/pack-06.yaml` documents every new
   `ai-processing-service` path — no path is added to any other pack's
   OpenAPI file (section 12).
5. `contracts/reason-codes/pack-06.yml` exists, structurally validated,
   every literal reason code used anywhere in the new service is
   registered.
6. CT-00-01 through CT-00-09 pass for this pack's scope (section 17);
   **CT-00-11 passes with real, non-trivial content for the first time
   in this project's history** — a genuine test that an AI-produced
   result cannot become official without the required human
   confirmation (section 8); CT-00-10/12 remain genuine, documented
   not-applicable/not-directly-applicable markers.
7. `tests/repository/test_service_boundaries.py`'s forbidden-pair matrix
   gains a row confirming `ai-processing-service` imports nothing from
   any other pack (section 12) — the strictest entry in that matrix.
8. A real end-to-end test proves the core human-control guarantee
   (section 8): an `AIProcessingRecord` whose `human_review_status`
   never reaches `approved`/`approved_with_changes` cannot be the
   direct cause of any state change on any other entity.
9. A real end-to-end test proves every fail-closed condition (section 10) actually blocks progress rather than defaulting to permissive
   behavior — at minimum, a missing `human_reviewer_reference` and a
   `redaction_applied = false` case.
10. `scripts/check_repository.py`'s `REQUIRED_PATHS` extended for every
    new path.
11. `REPOSITORY_VERSION` bumped `0.5.0 → 0.6.0`; canon SHA-256 updated to
    match the post-ADR-023 canon text (recorded in a new report,
    `docs/handover/PACK-06-REPORT.md`, following the same
    revision-by-revision honest-verification structure PACK-02 through
    PACK-05 all used).
12. Exactly one clean canonical archive exported at the end, no
    pack-specific change needed to
    `.github/workflows/verify-and-package.yml` (already pack-agnostic,
    confirmed unchanged through five packs now).

## 20. Explicitly excluded from this pack

- **Emergency/Crisis Override (19/19.1, `EmergencyAction`)** — per the
  user's explicit instruction (item 13). Nothing proposed here requires
  it; not silently combined.
- **Governance, Moderation, Transparency decision-making** — this pack
  never opens, decides, approves, rejects, or publishes any
  `GovernanceDecision`, `ModerationDecision`, `Ballot` outcome, or
  `PublicLedgerEntry` itself; it only ever produces advisory output a
  human then acts on through that service's own existing command
  (section 8).
- **Identity and Credential layers** — hard exclusion (section 1); no
  read edge proposed into any PACK-02 service.
- **A closed `purpose_code`/`target_type` taxonomy at canon level** —
  section 15 item 1 proposes a repository-level allow-list only, never
  a canon-level enum, mirroring `RoleAssignment.role_code`'s own
  treatment.
- **Real model-provider integration, API credentials, or infrastructure**
  — this specification defines the data model, lifecycle, and boundary;
  it does not select, configure, or integrate any specific model
  provider, self-hosted or external. That remains an implementation-time
  concern outside this document's scope.
- **Frontend/UI work** — `frontend/web-shell` is unchanged by this
  specification, consistent with the user's instruction and every prior
  pack's own precedent that no frontend implementation is expected
  unless strictly required for contract verification (it is not).
- **Any new field on any entity other than `AIProcessingRecord`** —
  section 1 confirms zero proposed changes to `Initiative`,
  `InitiativeVersion`, `ModerationCase`, `ModerationDecision`, `Ballot`,
  `ResultPublication`, `GovernanceDecision`, `TechnicalChallenge`, or
  `PublicLedgerEntry`.
- **Cryptographic signing or provenance attestation** — `input_hash`/
  `output_hash` (section 3) are content-hash digests for integrity
  bookkeeping, the same non-cryptographic-signature boundary PACK-03/04/05
  already drew for their own domains — not a cryptographic signature or
  attestation scheme, which would be its own future ADR.

## 21. Summary — ADRs required before any implementation

| ADR     | Subject                                                                                                                                                                                                     | Canon impact                                    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| ADR-021 | Service decomposition (section 11)                                                                                                                                                                          | None                                            |
| ADR-022 | Cross-pack dependency matrix — confirming zero dependencies (section 12)                                                                                                                                    | None                                            |
| ADR-023 | Canon addition: `AIProcessingRecord` field/status extension, event-catalog additions, the `processing_status`/`human_review_status` design decision, and the `ai.output.corrected` typo fix (sections 3, 6) | **Yes — canon `0.4.0 → 0.5.0`, minor**          |
| ADR-024 | Reason-code additions (section 14)                                                                                                                                                                          | None (registry file, per established precedent) |
| ADR-025 | Use-class policy, redaction defaults, allow-lists, and fail-closed defaults, with items 4/5 of section 15 requiring explicit owner decision                                                                 | None                                            |

ADR-007 is reserved/unused; ADR-005/006/008/009/010 are PACK-03;
ADR-011 through ADR-015 are PACK-04; ADR-016 through ADR-020 are
PACK-05 — this pack's five ADRs are the next five free numbers,
ADR-021 through ADR-025, drafted only after this specification itself
is reviewed and, if accepted, acted on.

**No code, schema, contract, ADR, or canon edit has been produced by
this specification.** `services/ai-processing-service` does not exist;
`contracts/schemas/ai-processing-record.schema.json` does not exist;
`docs/canonical/TZ-00-domain-event-canon.md` remains byte-identical to
the PACK-05 PASS state (section 0). This document's only deliverable is
the proposal itself, exactly as this task requires.
