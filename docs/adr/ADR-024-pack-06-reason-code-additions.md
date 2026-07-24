# ADR-024: PACK-06 reason-code additions

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted as proposed, 2026-07-24. The full code list (Decision, below —
the specification's original fifteen codes plus the seven new codes this
ADR added: `AI_REVIEWER_ROLE_INVALID`, `AI_REVIEWER_SCOPE_MISMATCH`,
`AI_REVIEW_SELF_APPROVAL_PROHIBITED`, `AI_REDACTION_MANIFEST_INVALID`,
`AI_INPUT_PROVENANCE_UNVERIFIED`, `AI_PUBLIC_DISCLOSURE_REQUIRED`,
`AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`) is approved exactly as drafted,
with no amendments. **Note on cross-pack reason-code interaction (from
ADR-022's own amendment, this same round):** `AI_REVIEWER_ROLE_INVALID`
and `AI_REVIEWER_SCOPE_MISMATCH` are now raised by `ai-processing-service`
upon receiving `authorized: false` from `governance-service`'s new
`verify_role_assignment_for_action` read (ADR-022) — `ai-processing-
service` raises its own registered code from this file; it does not
raise or register `governance-service`'s own `pack-05.yml` codes
(`ROLE_ASSIGNMENT_NOT_ACTIVE`, `ROLE_ASSIGNMENT_SCOPE_MISMATCH`), which
remain internal to `governance-service`'s own reasoning and may at most
be surfaced as supplementary, read-only context. Creating
`contracts/reason-codes/pack-06.yml` itself remains a separate,
implementation-time task, not authorized by this acceptance alone — the
exact final code list remains subject to confirmation once
`ai-processing-service`'s real source exists, the same standing caveat
ADR-014/ADR-019 already carried for their own packs.

## Context

Canon section 24's fixed reason-code standard has no codes scoped to AI
processing, model failures, redaction validation, or human-review
gating — the same kind of gap ADR-006, ADR-014, and ADR-019 each closed
for their own packs via an additive, non-canon registry file.
`docs/handover/PACK-06-SPEC.md` section 14 proposed an initial set; the
project owner has now added seven further codes this drafting round's
ADR-022 (reviewer verification) and ADR-025 (redaction enforcement,
consequential-use gating, mandatory disclosure) require, which the
specification itself had not yet named.

## Problem

Without a registered code, an application-layer error in
`ai-processing-service` would either reuse an unrelated existing code
(obscuring the real reason) or invent an unregistered literal (silently
bypassing `test_reason_codes_registry.py`'s registry-completeness check,
the same test every prior pack's own additive codes already satisfy).

## Considered options

- Option A — a new, separate, non-canon registry file,
  `contracts/reason-codes/pack-06.yml`, following the exact pattern
  ADR-006/ADR-014/ADR-019 already established.
- Option B — extend `contracts/reason-codes/pack-05.yml` in place, on
  the theory that AI reviewer verification (ADR-022) is "governance-
  adjacent."
- Option C — propose these codes as new canon section 24 entries,
  requiring a canon edit for what is, in every prior pack's precedent,
  registry-file content.

## Decision

**Option A**, consistent with every prior pack's own precedent (ADR-004,
ADR-006, ADR-014, ADR-019).

**Codes carried forward unchanged from `docs/handover/PACK-06-SPEC.md`
section 14:** `AI_MODEL_UNAVAILABLE`, `AI_PROCESSING_TIMEOUT`,
`AI_OUTPUT_MALFORMED`, `AI_MODEL_VERSION_UNSUPPORTED`,
`AI_CONFIDENCE_BELOW_THRESHOLD`, `AI_POLICY_CONFLICT`,
`AI_REDACTION_FAILURE`, `AI_PROMPT_INJECTION_SUSPECTED`,
`AI_PROHIBITED_INPUT_DETECTED`, `AI_HUMAN_REVIEWER_MISSING`,
`AI_HUMAN_REVIEW_REQUIRED`, `AI_OUTPUT_REJECTED_BY_HUMAN`,
`AI_PROCESSING_RECORD_SUPERSEDED`, `AI_AUTONOMOUS_ACTION_PROHIBITED`,
`AI_TARGET_REFERENCE_MALFORMED`.

**New, added by this ADR per the project owner's explicit instruction:**

| Code                                   | Raised when                                                                                                                                                                                                                                                                                                                |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AI_REVIEWER_ROLE_INVALID`             | ADR-022's `governance-service` read confirms a `RoleAssignment` exists, but its `role_code` is not one of this pack's reviewer taxonomy (`ai_output_reviewer`/`ai_moderation_reviewer`/`ai_governance_reviewer`/`ai_publication_reviewer`) or not the specific role a given `purpose_code` requires (ADR-022, ADR-025 §3). |
| `AI_REVIEWER_SCOPE_MISMATCH`           | The reviewer's `RoleAssignment.scope_id` does not cover the review's caller-supplied `subject_scope_id`, or the `RoleAssignment` is not `active` at the time of review (ADR-022).                                                                                                                                          |
| `AI_REVIEW_SELF_APPROVAL_PROHIBITED`   | The reviewer named by `human_reviewer_reference` is the same actor who submitted the underlying AI processing request, for a use requiring reviewer separation (ADR-025 §3).                                                                                                                                               |
| `AI_REDACTION_MANIFEST_INVALID`        | The `RedactionManifest` (ADR-025 §1) produced during input preparation fails its own structural validation — a missing required field, an inconsistent hash, or a validator-reported failure result — before any model call may proceed.                                                                                   |
| `AI_INPUT_PROVENANCE_UNVERIFIED`       | Input classification or provenance cannot be established with sufficient confidence for the redaction step to run correctly (ADR-025 §1) — processing is rejected rather than proceeding on an unverified assumption.                                                                                                      |
| `AI_PUBLIC_DISCLOSURE_REQUIRED`        | An official or public artifact incorporating AI output is about to be marked complete, but the mandatory AI disclosure record (ADR-025 §5) has not yet been successfully recorded — the fail-closed orchestration rule ADR-025 §5 defines.                                                                                 |
| `AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED` | A consequential AI output (ADR-025 §2) is about to be incorporated, published, or acted upon while `human_review_status` has not reached `approved`/`approved_with_changes` — the structural human-control guarantee (ADR-023, D1) this code exists to enforce.                                                            |

**Reused generic codes (unchanged from the specification):**
`PERMISSION_DENIED`, `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`. Reused
canon-fixed codes (section 24): `EVENT_VERSION_UNSUPPORTED`,
`INTEGRITY_CHECK_FAILED`.

Option B is rejected for the same reason ADR-014/ADR-019 rejected
merging into another pack's registry: AI Processing and Governance are
structurally distinct contexts (`docs/handover/PACK-06-SPEC.md` section
1), and ADR-022's one narrow read edge does not make AI Processing's own
reason codes governance-owned content. Option C is rejected because
canon section 24 is fixed, canon-immutable content — every prior pack's
additive codes have used a registry file specifically so the canon
document itself never needs editing for this kind of addition.

## Consequences

`contracts/reason-codes/pack-06.yml` would exist as a new, independent
file once implementation begins, structurally validated the same way
`test_reason_codes_registry.py` already validates `pack-02.yml` through
`pack-05.yml`. `docs/review/OPEN_QUESTIONS.md` item 10 (additive codes
never folded back into canon) is now six additive layers deep if
PACK-06 proceeds — worth the project owner's attention again, not a
blocker for this pack's own Definition of Done.

## Security impact

`AI_REVIEWER_ROLE_INVALID`, `AI_REVIEWER_SCOPE_MISMATCH`, and
`AI_REVIEW_SELF_APPROVAL_PROHIBITED` are all directly security-relevant:
they are the codes raised when ADR-022's reviewer-verification boundary
or ADR-025 §3's reviewer-separation rule is violated.
`AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED` and `AI_PUBLIC_DISCLOSURE_REQUIRED`
are the two codes that make this pack's core human-control and
transparency guarantees fail-closed rather than merely documented.

## Data impact

No canonical entity, field, or status is affected — this ADR proposes
only a non-canon registry file, the same category of addition ADR-006/
ADR-014/ADR-019 already made.

## Migration impact

None — no PACK-06 service or registry file exists yet.

## Reversibility

Reversible with low cost — a registry file's entries can be added,
renamed, or removed with a version bump to the file itself, unlike a
canon-level change; the same reversibility profile ADR-006/ADR-014/
ADR-019 already have.

## Related canon version

Authored against canon version `0.4.0`. Proposes no canon change.
