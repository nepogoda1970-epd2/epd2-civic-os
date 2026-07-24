# PACK-06 — Decisions requiring explicit owner approval

**Status: all decisions resolved — no open items remain.** The project
owner acted on ADR-021 through ADR-025 on 2026-07-24, and ADR-023's (and,
for its repository-side content, ADR-025's) own dedicated canon-edit
task has since been carried out the same day. **No
`services/ai-processing-service` directory, schema, OpenAPI file, or
reason-code registry exists.** Implementation of `ai-processing-service`
itself remains separate and has not begun.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
REPOSITORY_VERSION = 0.5.0
```

`CANON_VERSION` moved `0.4.0 → 0.5.0` (ADR-023, ADR-025) — new canon
section 19c ("ИИ-обработка — расширение / AI Processing Context")
extends the already-canon-defined `AIProcessingRecord` (17.1) with the
new `processing_status` field, the unified
`supersedes_ai_processing_record_id` mechanism, fifteen further fields,
the canonical embedded `redaction_manifest` value object, the
disclosure-lifecycle fields plus derived `DisclosureStatus`, and
`AIDisclosurePackage` defined as a contract/value object; section 20.12's
AI event catalog is corrected and expanded; section 23 gains new
forbidden-link entries. `REPOSITORY_VERSION` is unchanged at `0.5.0` —
this was a canon-only change, since no `ai-processing-service` code
exists yet.

## 1. AI Processing service decomposition (ADR-021) — accepted

One service, `services/ai-processing-service`
(`epd2_ai_processing_service`), owning `AIProcessingRecord` exclusively,
is accepted exactly as proposed. No amendment. Emergency/Crisis Override
stays outside PACK-06; no model provider is ever a system of record, and
no provider ever gains Civic OS mutation authority.

## 2. Cross-pack boundary — one narrow read into `governance-service` (ADR-022) — accepted with amendment

`target_type`/`target_id` remain caller-supplied, opaque, never
dereferenced — unchanged. **The reviewer-verification mechanism is
amended:** rather than `ai-processing-service` calling
`governance-service.get_role_assignment` and computing active/scope/
role-code checks itself against the plain returned fields, a new,
purpose-built `governance-service` application function,
`verify_role_assignment_for_action(role_assignment_id,
required_role_codes, required_scope_id, action_code, evaluated_at)`, now
performs the entire check **inside** `governance-service` and returns
only `authorized: bool`, `verified_actor_reference`,
`verified_scope_reference`, and `reason_code`. `governance-service`
remains the sole authority for active-status interpretation,
`valid_from`/`valid_until`, suspension/expiry/revocation, global-scope
and scope-coverage semantics, and role-code applicability;
`ai-processing-service` must not import `governance-service.domain` or
any other `governance-service.application` function, and must not
reimplement any of this logic locally. The four-role reviewer taxonomy
(`ai_output_reviewer`/`ai_moderation_reviewer`/`ai_governance_reviewer`/
`ai_publication_reviewer`) is accepted unchanged.

## 3. Canon 0.4.0 → 0.5.0 AI Processing Context additions and lifecycle (ADR-023) — accepted with amendments

The independent `processing_status` lifecycle (six values, no stored
`superseded`) and the `supersedes_ai_processing_record_id` immutable-
replacement mechanism are accepted exactly as proposed, no amendment. Two
amendments are required and are now incorporated directly into ADR-023's
own text:

| #   | Amendment                                          | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `RedactionManifest` canonicalized                  | No longer an implementation-time representation choice. Defined as an immutable, embedded value object within `AIProcessingRecord` (D4a), with exactly nine fields (`redaction_policy_reference`, `redaction_policy_version`, `input_classification`, `checked_field_categories`, `removed_field_categories`, `prepared_input_hash`, `validator_version`, `validated_at`, `result`), replacing the original flat `redaction_policy_reference`/`redaction_applied` field pair. Never contains raw input, removed values, identity values, credential values, vote content, or private audit content. |
| 2   | Disclosure-lifecycle fields and `DisclosureStatus` | `AIProcessingRecord` gains `disclosure_required` (boolean), `disclosure_package_reference` (nullable opaque reference), and `disclosure_receipt_reference` (nullable opaque reference). A derived, non-stored `DisclosureStatus` (`not_required`/`pending_package`/`pending_publication`/`published`) is computed from those three fields — never independently mutable.                                                                                                                                                                                                                            |

Every sub-item of Decision (D1–D7) is accepted as amended above — no
sub-item was rejected.

**Canon edit status:** performed, 2026-07-24, as its own separate,
dedicated task following this acceptance. New canon section 19c ("ИИ-
обработка — расширение / AI Processing Context") now carries the
(amended) content above; `canon_version` moved `0.4.0 → 0.5.0`.

## 4. Reason-code additions (ADR-024) — accepted

`contracts/reason-codes/pack-06.yml` with the specification's original
fifteen codes plus the seven this ADR added
(`AI_REVIEWER_ROLE_INVALID`, `AI_REVIEWER_SCOPE_MISMATCH`,
`AI_REVIEW_SELF_APPROVAL_PROHIBITED`, `AI_REDACTION_MANIFEST_INVALID`,
`AI_INPUT_PROVENANCE_UNVERIFIED`, `AI_PUBLIC_DISCLOSURE_REQUIRED`,
`AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`), plus reused generics, is
accepted exactly as proposed. No amendment. Per ADR-022's own amendment
(this same round), `AI_REVIEWER_ROLE_INVALID`/`AI_REVIEWER_SCOPE_MISMATCH`
are now understood to be raised locally by `ai-processing-service` upon
receiving `authorized: false` from `governance-service`'s new
`verify_role_assignment_for_action` — never `governance-service`'s own
`pack-05.yml` codes directly. The exact final code list remains subject
to confirmation once `ai-processing-service`'s real source exists
(ADR-024's own standing caveat, unchanged by acceptance).

## 5. Use-class policy, redaction, providers, disclosure (ADR-025) — accepted with amendment

§1 (redaction enforcement), §2 (consequential-use boundary), §3
(reviewer separation), §4 (external providers), and §6 (provider
abstraction) are accepted exactly as proposed, no amendment (§1 is
restated against ADR-023's now-canonical `redaction_manifest`; §3 is
restated against ADR-022's `verify_role_assignment_for_action`, with no
change in substance). **§5 (mandatory transparency) is replaced** by an
explicit, five-step protocol:

1. A consequential official/public AI output receives verified human
   approval.
2. `ai-processing-service` creates an immutable, redacted
   `AIDisclosurePackage` and records its reference in
   `disclosure_package_reference`.
3. `transparency-service` publishes it through its existing
   `publish_ledger_entry` path and returns a `disclosure_receipt_reference`.
4. The receipt reference is recorded against the `AIProcessingRecord`.
5. An owning service may finalize the official/public artifact only when
   `disclosure_required = true`, `DisclosureStatus = published`, and
   `disclosure_receipt_reference` is present.

`ai-processing-service` never writes Transparency storage;
`transparency-service` remains the sole writer of `PublicLedgerEntry`;
failure to obtain the receipt is fail-closed; an official/public artifact
cannot rely only on an orchestration-layer convention or a caller's
assertion. `AIDisclosurePackage` is confirmed as a contract/value object
— a transient payload, never a new canonical system-of-record entity.

No sub-item of ADR-025 was rejected.

## 6. Not requiring a decision right now

Unchanged from the prior version of this document:

- Exact API shapes, JSON Schemas, and OpenAPI paths — implementation
  detail once `ai-processing-service` implementation begins, not an
  owner decision.
- Frontend/UI work — out of scope per `docs/handover/PACK-06-SPEC.md`.
- The future Emergency/Crisis physical-service relationship — explicitly
  deferred, unchanged from PACK-05's own deferral (ADR-016).
- Real model-provider selection, API credentials, or infrastructure —
  outside this round's scope; ADR-025 §6 specifies only the abstraction
  interface's shape.
- `docs/review/OPEN_QUESTIONS.md` item 10 (additive reason codes never
  folded back into canon) — flagged again by ADR-024, still not required
  for this pack's own Definition of Done.

## 7. What this acceptance round, and the subsequent canon-edit round, do not authorize

Per this task's explicit instructions: no PACK-06 service directory,
implementation schema, OpenAPI file, or reason-code registry file was
created as part of the acceptance round or the follow-on canon-edit
round. `services/ai-processing-service` does not exist; no
PACK-02/03/04/05 source code was touched. The canon-edit task itself
(ADR-023/ADR-025, `0.4.0 → 0.5.0`) has now been performed, 2026-07-24,
as its own separate, dedicated task — but `ai-processing-service`
implementation itself remains a separate, later task, gated on the five
accepted ADRs and the now-implemented canon content, but not authorized
by either alone.
