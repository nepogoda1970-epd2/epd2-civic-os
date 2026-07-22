# ADR-004: Centralized PACK-02 reason-code registry and additive codes

## Status

Accepted for CLAUDE-PACK-02 v0.1.0

## Date

2026-07-21

## Context

Pack section 10 requires a single centralized reason-code registry at
`contracts/reason-codes/pack-02.yml`, with minimum groups `IDENTITY_*`,
`ELIGIBILITY_*`, `CREDENTIAL_*`, `EVENT_*`, `AUDIT_*`, `PERMISSION_*`,
`VALIDATION_*`, and requires every entry to carry a stable meaning,
severity, human-safe description, retryability, owner, and
`introduced_in_version`. Canon section 24 defines a fixed list of 22
reason codes and states "reason code не заменяется свободным текстом"
(a reason code is never replaced by free text). While building the
registry from the five services' actual `reason_code = "..."` call sites
(`exceptions.py`, `validation.py`, `application.py` across all five
services), two problems surfaced that this ADR resolves before the
registry file is written, per the pack's own required order of work
(section 18).

## Problem

1. **Coverage gap.** The five services collectively raise several reason
   codes with no equivalent in canon's closed 22-code list — most are
   validation-layer codes generic across entities (`VALIDATION_UNKNOWN_STATUS`,
   `VALIDATION_FORBIDDEN_TRANSITION`), audit-integrity codes
   (`AUDIT_EVENT_CONFLICT`, `AUDIT_CHAIN_BROKEN`), and several
   credential-validation-specific failure codes
   (`CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT`, `CREDENTIAL_REVOKED`,
   `CREDENTIAL_RULE_VERSION_MISMATCH`, `CREDENTIAL_DIGEST_MISMATCH`,
   `CREDENTIAL_REQUIRED_FIELD_MISSING`, `ELIGIBILITY_RULE_VERSION_FROZEN`).
   None of these overload or contradict an existing canon code; they are
   all genuinely new, specific failure conditions the canon's example list
   does not anticipate. Canon section 25 treats "backward compatible"
   additions as a minor-version concern, not a major one — the same class
   of change as this ADR's proposals.
2. **Real mislabeling bug found during this audit.** Three exceptions —
   `identity-service`'s `UnknownIdentityRecordError`, `eligibility-service`'s
   `UnknownEligibilityRuleError`, and `credential-service`'s
   `UnknownCredentialError` — are all raised for a plain lookup miss (no
   entity exists for the given ID), but their `reason_code` class
   attributes were set to `IDENTITY_NOT_VERIFIED`, `ELIGIBILITY_NOT_MET`,
   and `CREDENTIAL_UNKNOWN_STATUS` respectively. All three are wrong:
   `IDENTITY_NOT_VERIFIED` and `ELIGIBILITY_NOT_MET` are canon codes with a
   specific, different business meaning (a business-rule refusal on a
   record that _does_ exist), and `CREDENTIAL_UNKNOWN_STATUS` does not
   exist in canon at all and was never intended to mean "not found". No
   test asserted on these three exact strings, so nothing currently
   depends on the wrong values; this is a genuine correctness defect being
   fixed here, not a deliberate reuse.
3. **`AuditEvent.reason_code` (canon section 18.1) has no example
   values.** Every canon-section-24 code describes a refusal or
   limitation, but `AuditEvent` (per INV-04) records politically
   significant actions generally — including successful ones (a credential
   was issued, an identity was verified, an eligibility snapshot was
   created). Using a refusal-oriented code to classify a successful audit
   entry would be meaningless (e.g. there is no canon code that means
   "a credential was successfully issued"). The registry needs codes for
   these audited-but-successful classifications too, or every audit
   append would need to either invent a free-text reason (forbidden by
   canon section 24) or use a semantically wrong existing code.

## Considered options

- Option A — restrict every service to only the 22 canon codes, forcing
  imprecise reuse (e.g. `INTEGRITY_CHECK_FAILED` for every not-found and
  validation-layer condition) to avoid adding anything.
- Option B — add the additive codes needed (validation-layer, audit
  integrity, credential-validation-specific, and audit action
  classifications) as a documented, ADR-governed, backward-compatible
  extension of the canon's reason-code standard, keeping every existing
  canon code's meaning untouched, and fix the three mislabeled codes to a
  new precise code rather than force-fitting an existing one.
- Option C — maintain two separate registries (one canon-only, one
  pack-local) instead of the single centralized file the pack requires.

## Decision

Option B. `contracts/reason-codes/pack-02.yml` is the single source of
truth (Option C is rejected — it would violate the pack's explicit "one
centralized registry" requirement in section 10). It contains:

1. All 22 canon section-24 codes verbatim, `introduced_in_version: "0.1.0"`
   (canon's own version), meaning/description/severity/retryable/owner
   assigned from context in canon sections 5, 19, 21, 24 for codes not yet
   exercised by any PACK-02 service (they remain listed for forward
   compatibility with later packs — Voting, Delegation, Moderation,
   Governance/Crisis Override — so the registry does not need to grow
   again just to document a code canon already named).
2. A new generic validation-layer code, `VALIDATION_RECORD_NOT_FOUND`,
   replacing the three mislabeled codes described in Problem #2. This
   follows the exact precedent already set by
   `VALIDATION_UNKNOWN_STATUS`/`VALIDATION_FORBIDDEN_TRANSITION` — a
   generic, cross-entity, validation-layer code reused verbatim by
   `account-service`, `identity-service`, `eligibility-service`, and
   `credential-service`, rather than one not-found code per entity type.
3. Additive refusal/integrity codes used by exactly one service:
   `AUDIT_EVENT_CONFLICT`, `AUDIT_CHAIN_BROKEN` (audit-core),
   `CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT`, `CREDENTIAL_REVOKED`,
   `CREDENTIAL_RULE_VERSION_MISMATCH`, `CREDENTIAL_DIGEST_MISMATCH`,
   `CREDENTIAL_REQUIRED_FIELD_MISSING` (credential-service),
   `ELIGIBILITY_RULE_VERSION_FROZEN` (eligibility-service).
4. New `AuditEvent.reason_code` action-classification codes for
   successful, audited actions: `CREDENTIAL_ISSUED` (credential-service),
   `IDENTITY_VERIFIED` (identity-service), `ELIGIBILITY_MET`,
   `ELIGIBILITY_SNAPSHOT_CREATED` (eligibility-service),
   `ACCOUNT_STATUS_CHANGED` (account-service, reused across all
   transitions that reach an auditable canonical event — the specific
   transition is already carried by `AuditEvent.event_type`, so one
   generic classification code avoids inventing one code per transition).
   `AuditEvent.reason_code` for a _failed_ or _refused_ audited action
   (e.g. `identity.verification_failed`, `credential.validation_failed`,
   `identity.verification_expired`) reuses the matching existing refusal
   code (`IDENTITY_NOT_VERIFIED`, the relevant `CREDENTIAL_*` failure code,
   `IDENTITY_VERIFICATION_EXPIRED`) rather than inventing a parallel
   "failed" variant — one registry entry, two legitimate call sites
   (a `ValidationResult`/`EligibilityDecision` and an `AuditEvent` can
   share the same code when they describe the same real-world condition).
   Three further identity-specific audit classifications were added while
   wiring `identity-service` to Audit Core: `IDENTITY_VERIFICATION_REVOKED`
   (an explicit revocation, which reaches the same canonical
   `identity.verification_expired` event as a natural expiry per ADR-002,
   but whose audit reason_code should still distinguish "an administrator
   revoked this" from "this expired on its own" — the event name cannot
   carry that distinction, so the audit trail's reason_code does),
   `IDENTITY_DUPLICATE_SUSPECTED`, and `IDENTITY_MANUAL_REVIEW_REQUIRED`
   (audit classifications for the two `IdentityRecord` outcomes with no
   existing refusal-style code to reuse). All additive codes get
   `introduced_in_version: "pack-02-0.1.0"` to mark them as introduced by
   this pack rather than by the canon itself.
5. All three mislabeled exceptions
   (`services/identity-service/.../UnknownIdentityRecordError`,
   `services/eligibility-service/.../UnknownEligibilityRuleError`,
   `services/credential-service/.../UnknownCredentialError`) are corrected
   to `reason_code = "VALIDATION_RECORD_NOT_FOUND"`.

No canon code's existing meaning is changed, narrowed, or reused for a
different purpose than canon assigns it (this would require a major
version per canon section 25); every addition here is purely additive.

## Consequences

`contracts/reason-codes/pack-02.yml` is now the one file every service's
`reason_code` string literal must appear in — this is enforced by a
contract test (`tests/contract/test_reason_codes_registry.py`, added under
Task 20) that scans all five services' source for `reason_code = "..."`
and `reason_codes=(...)`/`.append("...")` literals and asserts each is a
registered code. `docs/review/OPEN_QUESTIONS.md` gets a new entry
recommending these additive codes for a future canon minor-version
proposal (0.1.0 → 0.2.0), consistent with how ADR-002 handled the
`identity.verification_revoked` event-name gap.

## Security impact

None of the additive codes weaken fail-closed behavior (INV-10) or make
any refusal less specific — they make refusals _more_ specific
(replacing a wrong/reused code with a correct dedicated one), which
strengthens INV-09 (a refusal must be explicable) by removing a case
where the returned code did not actually describe the failure that
occurred.

## Data impact

None — reason codes are metadata on existing entities/events, not new
canonical entities or fields.

## Migration impact

None — no PACK-02 service has shipped externally yet; the three corrected
codes have no external consumers to migrate.

## Reversibility

Reversible with cost: removing an additive code later requires confirming
no caller still emits it (a major-version-equivalent change per the
registry's own stability guarantee, even though the registry itself is
not the canon document).

## Related canon version

Authored against canon version `0.1.0`. Recommends (but does not itself
perform) a future minor-version proposal to fold the additive codes listed
in Decision item 2-4 into canon section 24 — see
`docs/review/OPEN_QUESTIONS.md`.
