# Changelog

## FRONT-00 foundation candidate correction 0.1.1

- Replaced five simplified examples with faithful non-production migrations of
  the exact `EPD_Front.zip` source compositions.
- Added the missing component/native-pattern catalogue, 13 rendered behavior
  tests, Playwright visual/browser coverage, axe and keyboard accessibility
  coverage, and CI commands.
- Corrected source/migration/showcase terminology and the collision-safe mypy
  command without changing repository 0.9.0 or canon 0.7.0.

## FRONT-00 Implementation Candidate - 2026-07-27

- Extracted EPD_Front visual tokens into the existing Next.js web shell.
- Added shared shell/components, 19 presentation states, five representative
  fixtures and declarative route/workspace/storage/telemetry policies.
- Added architecture/component tests and FRONT-00 documentation.
- Added Proposed ADR-044 through ADR-047.
- No dependency, backend, canon-version or repository-version change.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - canon minor version 0.7.0 (Organization & Regional Scope Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.6.0 →
0.7.0` (ADR-037, accepted, following ADR-032 through ADR-036's own
  prior acceptance in the PACK-08 spec-correction round) — the sixth
  edit to this document's own text since its original acceptance
  (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 → 0.3.0`,
  ADR-018/ADR-020's `0.3.0 → 0.4.0`, ADR-023/ADR-025's `0.4.0 → 0.5.0`,
  and ADR-026 through ADR-031's `0.5.0 → 0.6.0`). Adds a new section 19e
  ("Организация и региональная авторизация — расширение / Organization
  & Regional Scope Context"), inserted between sections 19d and 20, the
  same non-renumbering technique used for 19a/19b/19c/19d. Extends
  `Organization` (8.1) with six additive fields
  (`organization_profile`, `parent_reference`, `effective_from`,
  `effective_until`, `dissolved_at`, `successor_reference`); confirms
  `CivicSpace` (8.2) unchanged; defines four wholly new canonical
  entities owned by `organization-service` (`OrganizationalUnit`,
  `OrganizationalRelation`, `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`) plus `OrganizationalAuthority`
  (distinct from, and cross-referenced only by opaque reference with,
  the unchanged `RoleAssignment`, 8.4) and the reusable
  `OrganizationalScope` value shape (not separately owned, the same
  status as `RedactionManifest`/`AIDisclosurePackage`). Canonizes:
  four non-interchangeable concepts (Organization/Jurisdiction/
  CivicSpace/process-local Scope) and a no-silent-field-reinterpretation
  rule for `organization_id`/`jurisdiction`/`region_code`/`scope_id`/
  `civic_space_id`; multiple typed directed graphs for organizational
  relationships (not a strict tree), with relation-type-specific cycle
  and overlap rules; `parent_reference`'s non-authoritative,
  derived-projection status; uniform effective dating (valid_from/
  valid_until/recorded_at/supersedes/historical queryability/
  future-dated changes/overlap validation) across `Organization`/
  `OrganizationalUnit`/`OrganizationalRelation`/`OrganizationalAuthority`;
  canonical reorganization rules (creation/activation/suspension/
  dissolution/merger/split/successor/renaming/territorial reassignment)
  with a hard no-automatic-rights-transfer invariant; default-deny
  regional scope authorization with six explicit access modes and hard
  anti-confused-deputy/anti-role-name-as-proof/no-universal-
  administrator rules; inheritance-policy ownership (restrict-never-
  broaden); a 90-day default maximum for temporary supervision; seven
  named institutional roles and a minimum eight-bullet non-combinable-
  role baseline (subject to legal refinement); role/authority lifecycle
  rules; extended identity-minimization rules; and a six-category
  classification requirement for `RoleAssignment.scope_id` (8.4 itself
  unchanged in fields/status/owner). Section 20.5 (Organization events)
  gains thirteen entries and full payload/timing/audit/privacy
  documentation; section 22 gains five new ownership-matrix rows;
  section 23 gains new forbidden-link entries; section 24 gains ten new
  reason codes (`ORGANIZATION_NOT_ACTIVE` through
  `HISTORICAL_SCOPE_NOT_EFFECTIVE`) — no existing code or event name
  renamed or repurposed; no naming conflict found.
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.7.0`) — this is a canon-only change, per CLAUDE-PACK-08's
  own canon-amendment round (`docs/adr/ADR-037`;
  `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`). No
  `organization-service` code, database, migration, event bus, frontend,
  schema, OpenAPI file, or reason-code registry file was created.
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`.

### Verified

- **Local, honest self-report only — no external GitHub Actions run was
  performed or is claimed for PACK-08, at any stage, including this
  canon-amendment round.** Fresh local re-run in this sandbox: Ruff
  (lint + format) clean; mypy clean for `epd2-core`/`scripts`/
  `tests/repository`/`tests/contract` and for all 15 services
  individually; Python test suite: 2020 passed, 5 skipped, 1 failed (the
  expected, self-resolving `test_no_forbidden_paths_present`
  cache-artifact detection — 0 real failures); all 402 required paths
  present; version consistency passed. Full detail:
  `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` section 6.

## [0.9.0] - compliance, records governance & legal workflows (implementation)

CLAUDE-PACK-09. One wholly new service (`compliance-service`, ADR-038)
plus its contracts and tests. No canon change: `CANON_VERSION` stays
`0.7.0`, and no canon-owned file was touched.

### Added

- `services/compliance-service` — PACK-09's one new service, owning six
  entity families across `domain.py`, `application.py`, `events.py`,
  `storage.py` and `exceptions.py`:
  - **Records governance** (ADR-039): `RetentionPolicy` (append-only by
    `(policy_id, policy_version)`), `RetentionStartEvent` (retention never
    starts implicitly), `GovernedRecord`, `DisposalEligibility`,
    `DestructionAuthorization`, `DestructionEvidence` (create-once).
    Destruction is a three-step controlled workflow — evaluate → authorize
    → execute — and no store in the service exposes a delete method.
  - **Legal Hold** (ADR-039): `LegalHold` with three states
    (`active`/`released`/**`indeterminate`**), additive scope over record
    ids / record classes / case ids, append-only history, and explicit
    release. An indeterminate hold fails closed with
    `LEGAL_HOLD_STATE_UNKNOWN`.
  - **Data Catalog & Processing Registry** (ADR-040): `DataAsset`,
    `ProcessingActivity`, and `LegalBasis` as a closed, managed
    classification enum. Mandatory retention references are resolved
    against the policy store, not merely typed. Identity field names are
    rejected at construction.
  - **Governed cases & deadlines** (ADR-041): `ProceduralCase` with
    constrained transitions, required steps and referenced evidence;
    `DeadlineDefinition` with a required IANA timezone; and
    `ProceduralDeadline` whose `status` and `due_at` are _derived_ from an
    append-only history — neither is a stored field.
  - **Data-subject and legal requests** (ADR-040/ADR-041):
    `DataSubjectRequest` holding an identity-verification _status_ plus an
    opaque reference, and no identity attribute anywhere.
  - **Party arbitration and disputes** (ADR-042): `DisputeParties`,
    `CaseRoleAssignment`, `ConflictOfInterestDeclaration` (explicit
    `ConflictState`, not free text), `CaseDecision`, `AppealReference`, and
    `domain.assert_decision_maker_eligible` — the single gate that blocks
    self-appointment, party appointment, handler appointment, undeclared
    conflicts and blocking conflicts.
  - **Organizational scope isolation**: `RequestContext` plus
    `CrossScopeAuthorityGrant` with enumerated `ScopeCapability` values.
    No hierarchy-derived inheritance; crossing a boundary requires a grant
    issued by the target organization _and_ presented by the caller.
- ADR-038 through ADR-042 (full template, accepted 2026-07-26).
- `contracts/reason-codes/pack-09.yml` — 40 codes, each carrying all seven
  fields `epd2_core.reason_codes.ReasonCodeRegistry` requires.
- Fifteen new entity schemas and eight new event payload schemas under
  `contracts/schemas/` and `contracts/events/`.
- `contracts/openapi/pack-09.yaml` — 28 operations, every one tagged
  `compliance-service`, with request bodies, reason-coded error responses
  and no DELETE method anywhere.
- Repository verification wiring for PACK-09: `PACK09_*` constants in
  `tests/contract/_schema_helpers.py`; a pack-09 row in
  `tests/contract/test_reason_codes_registry.py`; PACK-09 sections in
  `tests/contract/test_openapi_contract.py`,
  `test_ct00_08_identity_leakage.py` and
  `test_ct00_09_vote_linkability.py`; a new
  `tests/contract/test_ct00_01_pack09_schema_validation.py`; PACK-09
  boundary tests in `tests/repository/test_service_boundaries.py`; and 44
  new required paths in `scripts/check_repository.py`.

### Changed

- `REPOSITORY_VERSION`: `0.8.0 → 0.9.0`. `CANON_VERSION` remains `0.7.0`;
  `docs/canonical/canon-version.json` `repository_compatibility` widened to
  `>=0.1.0 <0.10.0`.
- `Makefile` `typecheck` target now also runs `mypy` over
  `services/organization-service` and `services/compliance-service`, which
  were both absent from it.

### Added — Architecture & Domain Framework 0.8.1 (same 0.9.0 round)

The **EPD² Architecture & Domain Framework 0.8.1** (Roadmap Amendment)
became the authoritative scope document for PACK-09 mid-round. Nothing
above was rewritten; the following was added to the same service, under
the same dependency rule, with `CANON_VERSION` still `0.7.0`.

- `services/compliance-service/src/epd2_compliance_service/casework.py` —
  the **common legal-case substrate** (Framework 13.1): `LegalCase`
  (status derived from an append-only transition history, never stored),
  `JurisdictionDetermination` (appended, never rewritten; a transfer
  keeps the outgoing determination's own authority reference and gains a
  pointer to its successor), `CaseParty` and `RepresentationMandate`
  (enumerated authorities, not a role name), `Filing` (immutable docket:
  store-assigned sequence, rejection preserved in place, correction by
  supersession, `submitted_at` and `received_at` distinct), `Hearing`,
  `InterimMeasure` (a _granted_ measure is constructible only by a human
  authority, and only with an end or review date plus reasons),
  `ProceduralDecision` (effect, finality and enforceability as three
  independent derived facts), `Remedy`, `RecusalRecord` and
  `ReplacementAssignment`, plus the gates
  `assert_may_decide_substantively`, `assert_due_process_complete` and
  `assert_actor_not_recused`.
- `services/compliance-service/src/epd2_compliance_service/notices.py` —
  the **official-notice trust boundary** (ADR-043, new): `OfficialNotice`
  (an authorized object; starts nothing), `ServiceAttempt` (provider
  telemetry, with `is_reconciled` gating every deemed-service rule),
  `NoticeEffectDecision` (the only object that can start a procedural
  deadline) and `DeadlineTrigger` (create-once per deadline).
  `TriggerSource` names `delivery_telemetry` and `read_telemetry`
  precisely so both can be refused _by name_ rather than by omission.
- `services/compliance-service/src/epd2_compliance_service/dataprotection.py`
  — **data-protection governance and the DPIA gate**:
  `DPIARequirementDetermination` (recorded even when the answer is "no",
  because its absence is what blocks activation),
  `DataProtectionImpactAssessment`, `ProcessingActivationDecision`,
  `TransferAssessment`, `ConsentWithdrawalRecord`, plus
  `assert_activation_permitted` and `assert_dpo_independence`.
- `services/compliance-service/src/epd2_compliance_service/references.py`
  — the **stable typed references** PACK-09 publishes to
  PACK-10/11/19/21-24 (`LegalCaseRef`, `DeadlineRef`, `NoticeEffectRef`,
  `HoldRef`, `RecordClassRef` and siblings), plus explicit
  `PlaceholderRef` forward declarations for objects later packs own.
  There is no `PersonRef`, `UserRef` or `MemberRef` and there must never
  be one.
- `domain.py` additions: `RecordClass` (record owner and disposition
  authority must differ), `DataClassification`,
  `SearchExportEligibility`, `HoldPropagationRecord`, `PropagationState`
  and `assert_hold_propagation_resolved`.
- `events.py`: **33 new event types** (41 in total), each with a wire
  payload that carries no party or authority handle at all;
  `ALL_EVENT_TYPES` and `NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES` make the
  set and the prohibition testable.
- `application.py`: 34 new commands, each with scope guards, `event_id`
  idempotency through Audit Core, an audit append with canonical
  before/after hashes, and reason-coded refusal — plus
  `assert_destruction_propagation_resolved` as a separate assertion
  rather than a widened `authorize_destruction` signature.
- `storage.py`: 18 new Protocol/in-memory store pairs, including
  create-once stores for notice effects and deadline triggers and an
  append-only filing store that compares ten immutable fields on update.
- `contracts/`: 22 new entity schemas, 33 new event payload schemas,
  34 new OpenAPI operations (62 in total), and 32 new refusal reason
  codes plus 18 additive audit classifications in `pack-09.yml` (88 in
  total).
- `docs/adr/ADR-043-official-notice-legal-effect-trust-boundary.md` —
  the round's one new ADR. ADR-038 through ADR-042 each gained a
  Framework 0.8.1 amendment section.
- `docs/handover/PACK-09-KNOWN-LIMITATIONS.md` — what this pack does not
  do, and where each partial guarantee ends.
- Tests: `test_casework.py`, `test_notices.py`, `test_dataprotection.py`
  and `test_framework_application.py` in the service suite;
  `tests/contract/_pack09_framework_samples.py` and
  `test_ct00_01_pack09_framework_schema_validation.py`; new PACK-09
  sections in `test_openapi_contract.py` and
  `test_ct00_08_identity_leakage.py`.

### Changed — Architecture & Domain Framework 0.8.1 (same 0.9.0 round)

- Two reason codes introduced earlier in this same **unreleased** 0.9.0
  round were renamed in place rather than duplicated:
  `CROSS_ORGANIZATION_CASE_ACCESS_DENIED` → `CROSS_SCOPE_ACCESS_DENIED`
  and `DECISION_AUTHORITY_MISSING` → `DECISION_AUTHORITY_DENIED`. The old
  exception class names remain as aliases, so no call site changed.
  Registering synonyms would have left two codes meaning one thing.
- `notices.determine_notice_effect` returns a recorded `NOT_EFFECTIVE`
  determination when every authorized attempt positively failed, rather
  than raising. A refusal that raised would leave no record for the
  parties to see or challenge.
- Two constructor guards that previously raised a bare `ValueError` now
  raise their registered reason-coded errors:
  `InterimMeasure` without an end or review date
  (`INTERIM_MEASURE_AUTHORITY_DENIED`) and `DeadlineTrigger` from a
  telemetry source (`DEADLINE_TRIGGER_INVALID`).
- `scripts/check_repository.py`: 489 → 554 required paths.

### Verified

- **PACK-09 IMPLEMENTATION 0.9.0 — EXTERNAL CI PASS.** The full pipeline
  ran on GitHub Actions (ubuntu-latest, Python 3.12, Node.js 22) against
  the locked toolchain and passed: 556 required paths, no forbidden
  paths, Prettier PASS, `ruff format` PASS, `ruff check` PASS, `mypy`
  PASS for every service including `organization-service` and
  `compliance-service`, Python tests 2659 passed / 4 skipped / 0 failed,
  TypeScript package tests 3 passed, frontend tests 11 passed, Next.js
  production build PASS. Overall: all checks passed. The runner output is
  archived at `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`.
  `REPOSITORY_VERSION` stays `0.9.0` and `CANON_VERSION` stays `0.7.0`;
  the canon document is byte-identical. This records verification only —
  not production readiness, deployment or legal activation.

## [0.8.0] - organization & regional scope context (implementation)

### Added

- A new, independent, in-memory-backed service, `organization-service`
  (CLAUDE-PACK-08 IMPLEMENTATION ROUND, "Organization & Regional Scope
  Context"), with its own `README.md`, `pyproject.toml`, `src/`,
  `tests/`, storage interfaces, and in-memory reference adapters —
  implementing canon 0.7.0 section 19e and ADR-032 through ADR-037
  (all `accepted`) with no further canon edit. Sole authoritative owner
  of `Organization`, `OrganizationalUnit`, `CivicSpace` (first real
  implementation in this repository), `OrganizationalRelation`,
  `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`, `OrganizationalAuthority`, and the
  reusable `OrganizationalScope` value shape.
- Organization lifecycle: create/activate/suspend/dissolve/rename,
  reorganization (merge/split/declare-successor) with a hard
  no-automatic-role/authority/access-transfer invariant
  (`assert_successor_transfer_has_own_decision`), effective dating
  (`valid_from`/`valid_until`/`recorded_at`/`supersedes`, deterministic
  current/historical/future-dated queries).
- `OrganizationalRelation`: nine relation types across three derived
  categories (hierarchy/continuity/cooperation); deterministic
  hierarchy-cycle detection (`would_create_hierarchy_cycle`) and
  temporary-supervision-cycle detection
  (`would_create_supervision_cycle`); policy-gated overlap validation
  (`OrganizationalHierarchyOverlapPolicy`); territorial reassignment;
  a derived, non-authoritative `parent_reference` read model
  (`recompute_parent_reference`, never itself a source of truth).
- Regional scope authorization (canon 19e.12): a default-deny, pure,
  side-effect-free atomic capability check
  (`check_regional_scope_access`) implementing all six access modes
  (exact/ancestor/descendant-scope, delegated cross-scope via the new
  `ScopeDelegationGrant` reference entity, temporary supervision,
  institutional oversight without data access); inheritance-policy
  ownership (`OrganizationalInheritancePolicy`, restrict-never-broaden);
  a separate, explicit grant/revocation recording step
  (`record_regional_scope_access_grant`/
  `record_regional_scope_access_revocation`) that emits
  `regional_scope_access.granted`/`.revoked` only for modes 2–5.
- Temporary supervision (canon 19e.14): mandatory `valid_from`/
  `valid_until`, a 90-day default maximum
  (`TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS`), rejection of open-ended
  windows, extension only through a new governed decision with its own
  audit record (`extend_temporary_supervision`).
- Institutional authority (canon 19e.15–19e.17): `OrganizationalAuthority`
  with canon's own exact field names (`role_code`/`scope`, not
  `authority_type`/four separate scope fields — the same reconciliation
  ADR-037 itself performed); self-assignment rejection; the eight-rule
  role-incompatibility baseline (`PAIRWISE_INCOMPATIBLE_ROLES`, version
  `"1.0"`, versioned/extensible); dual-control enforcement (`proposed`
  status plus a distinct-actor `activate_organizational_authority`
  step); expired/revoked/suspended-authority rejection
  (`assert_authority_usable`).
- Thirteen canonical events (canon 20.5/19e.20): `organization.created`
  (first real implementation) plus `organization.activated`/
  `.suspended`/`.dissolved`/`.merged`/`.split`/`.successor_declared`,
  `organizational_relation.created`/`.ended`,
  `organizational_authority.assigned`/`.revoked`,
  `regional_scope_access.granted`/`.revoked` — minimum-necessary payload
  only, no global user identifiers, no unrelated identity data.
- Ten canon section 24 reason codes (`ORGANIZATION_NOT_ACTIVE` through
  `HISTORICAL_SCOPE_NOT_EFFECTIVE`) plus 22 narrowly-necessary additive
  implementation reason codes (audit/event bookkeeping, dual-control and
  self-assignment guards, temporary-supervision window/extension guards)
  — `contracts/reason-codes/pack-08.yml`, 32 entries total.
- Five new entity JSON Schemas (`organization`, `organizational-unit`,
  `civic-space`, `organizational-relation`, `organizational-authority`)
  and seven new event-payload JSON Schemas under `contracts/schemas/`/
  `contracts/events/`; `contracts/openapi/pack-08.yaml` (nine minimal
  reference operations, per this round's own "minimal reference APIs
  only" instruction — organization lifecycle-transition commands and
  OrganizationalUnit management are deliberately not exposed as HTTP
  paths, mirroring PACK-05's own bootstrap-seed precedent).
- `docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`: the complete,
  per-`role_code` enumeration `docs/packs/PACK-08-MIGRATION-MATRIX.md`
  section 2.3 (OD-11) required before any migration touching
  `RoleAssignment.scope_id` could begin — all 12 `role_code` values
  found in the repository classified against the six-category scheme,
  none migration-blocked (`oversight_reviewer` carries a documented dual
  classification, `observer` a documented not-yet-load-bearing note,
  neither an unresolved ambiguity). Closes OD-11 fully.
- `docs/packs/PACK-08-IMPLEMENTATION.md`,
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`.

### Changed

- `REPOSITORY_VERSION`: `0.7.0 → 0.8.0`
  (`packages/python/epd2-core/src/epd2_core/version.py`,
  `packages/typescript/epd2-types/src/version.ts`, both
  version-consistency unit tests updated). `CANON_VERSION` unchanged at
  `0.7.0` — no canon-owned file was touched this round; `sha256sum
docs/canonical/TZ-00-domain-event-canon.md` still returns
  `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072`,
  confirmed unchanged.
- `docs/canonical/canon-version.json`: `repository_compatibility` upper
  bound widened `<0.8.0 → <0.9.0`.
- `docs/architecture/data-ownership.md`: `Organization`/`CivicSpace`
  rows updated from "Not implemented" to "Implemented (PACK-08)"; new
  rows added for `OrganizationalUnit`/`OrganizationalRelation`/
  `OrganizationalHierarchyOverlapPolicy`/
  `OrganizationalInheritancePolicy`/`OrganizationalAuthority`.
- `tests/repository/test_service_boundaries.py`: new
  `PACK08_SERVICE_PACKAGES` (`organization-service`, the one wholly new
  PACK-08 service) plus positive-assertion boundary tests confirming it
  depends on no other service this round and no other service depends on
  it.
- `tests/contract/_schema_helpers.py`, `test_reason_codes_registry.py`,
  `test_openapi_contract.py`: extended with PACK-08's own registry/
  contract constants and checks, following the PACK-04/05/06/07
  single-service exact-tag-match precedent.
- `tests/contract/test_ct00_01_pack08_schema_validation.py`: new file
  (mirroring the `test_ct00_01_pack07_schema_validation.py` precedent of
  a dedicated file per schema-heavy pack).
- `scripts/check_repository.py`: `REQUIRED_PATHS` extended with every
  file above, plus this round's own `docs/packs/PACK-08-*.md`/
  `docs/handover/PACK-08-*.md` entries (the PACK-07/ADR-026–037/
  `docs/packs/` entries from earlier rounds were not previously present
  in `REQUIRED_PATHS` and are a pre-existing gap this round does not
  retroactively backfill — see the implementation report).

### Verified

- **Local, honest self-report only — no external GitHub Actions run was
  performed or is claimed for this implementation round.** Full detail:
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`.

## [0.7.0] - participation & membership context (implementation)

### Added

- A new, independent, in-memory-backed service, `membership-service`
  (CLAUDE-PACK-07, "Participation & Membership Context"), with its own
  `README.md`, `pyproject.toml`, `src/`, `tests/`, storage interfaces,
  and in-memory reference adapters, plus in-place extensions to the two
  pre-existing PACK-02 services `eligibility-service` and
  `identity-service` — implementing exactly the canon 0.6.0 section 19d
  text and ADR-026 through ADR-031 (all `accepted`) with no further
  canon edit.
- `eligibility-service`: `ParticipantEligibilityPolicy` and
  `ProcessEligibilityPolicy` (canon 19d.4/19d.5), each a versioned,
  activatable critical policy with the shared four-gate activation rule
  (canon 19d.7: approved `GovernanceDecision`, multi-person approval,
  signed policy digest, transparency-log commitment); the four
  separated electoral-eligibility claims (canon 19d.3) computed by
  `evaluate_process_eligibility_claims`, replacing the generic
  `electoral_eligibility_met` concept everywhere; `StepUpAuthenticationRequirement`
  and its fail-closed `check_step_up_requirement` evaluation (canon
  19d.8); `DigitalDecision`/`AssemblyDecision` and the formal-confirmation
  lifecycle (canon 19d.12: `DigitalDecision → FormalConfirmationRequired
→ AssemblyDecision → Confirmed | Rejected | ReturnedForRevision`, with
  a required `divergence_explanation` whenever the final legal decision
  diverges from the digital result, and no silent-approval timeout);
  `AtomicCapabilityResult`/`check_atomic_capability` and scoped
  capability-token issuance (canon 19d.14) via the narrow
  `epd2_credential_service.application.issue_participation_credential`
  read (ADR-027) — `ParticipationRightsProfile` itself stays internal,
  derived, non-authoritative, and non-persisted throughout.
- `membership-service`: `PartyMembershipEligibilityPolicy` (canon 19d.6,
  structurally separate from `ParticipantEligibilityPolicy`, sharing its
  lifecycle plus `incompatibility_rules`/`membership_duration_rules`);
  `MembershipApplication`'s six-state lifecycle (canon 19d.9:
  `application_pending → eligibility_review → human_decision_pending →
approved → rejected → activated`), with Stage A
  (`evaluate_membership_application_eligibility`) _always_ landing on
  `human_decision_pending` regardless of its own recommendation, and
  Stage B (`record_membership_human_decision`) the only path to
  `approved`/`rejected` — each requiring an externally-verified
  `decision_authority_reference`; `activate_membership` as the _only_
  function in the service that ever constructs an `active`
  `Membership` row, layered without overloading `Membership.membership_status`
  (canon 8.3, unchanged, first real implementation); `AffiliationDeclaration`
  (canon 19d.10, immutable/versioned, `declared_reference` an opaque
  reference never a free-text organization name); `ConflictAssessment`
  (canon 19d.11, `decision_authority_reference` mandatory once
  `resolved_incompatible`, enforced fail-closed at construction); the
  polymorphic `Appeal` model reused (a documented, tested duplicate of
  `epd2_moderation_service.domain.Appeal` — no separate `MembershipAppeal`
  was needed, so no new ADR was required per required scope item 9).
- `identity-service`: `AuthenticationContext` (canon 19d.8) and
  `record_step_up_completion`; `IdentityRecord` (7.3) gains eight new
  fields (`date_of_birth`, `citizenship_status`, `residence_status`,
  `identity_assurance_level`, `identity_scheme`,
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`) — all-`None`/empty/`none`-default, backward
  compatible; the two narrow ADR-027 cross-pack reads
  `get_identity_participation_claims`/`check_authentication_step_up_satisfied`.
- Canon 19d.16's hard human-control invariant (no automated process may
  finally decide membership rejection/suspension/expulsion/incompatibility/
  denial of fundamental rights/restoration denial) is structurally
  enforced, not just documented: every consequential membership/conflict
  outcome requires an externally-verified `decision_authority_reference`,
  proven end-to-end in `services/membership-service/tests/test_application.py`
  (`test_stage_a_always_transitions_to_human_decision_pending_regardless_of_recommendation`,
  `test_activate_membership_is_the_only_path_to_active_status`,
  `test_record_conflict_decision_requires_decision_authority_when_incompatible`).
- Membership disclosure restricted by default (ADR-030 item 5): no
  application/status/rejection/suspension/termination/affiliation/conflict
  evidence is exposed on any wire event payload — proven structurally in
  `tests/contract/test_ct00_08_identity_leakage.py`'s new PACK-07
  section (eight tests, one per restricted field/entity).
- The ADR-027 cross-service edge matrix, all `.application`-only:
  `eligibility-service → {identity-service, membership-service,
governance-service, credential-service}`,
  `membership-service → {identity-service, eligibility-service,
governance-service}` — enforced by seven new/extended AST-based tests
  in `tests/repository/test_service_boundaries.py`, and three
  deliberately-duplicated (never imported) logic pieces — the four-gate
  critical-policy activation gate, the polymorphic `Appeal` entity, and
  the step-up assurance-evaluation logic — proven byte-for-byte
  equivalent across their service copies by the new
  `tests/repository/test_pack07_duplicated_logic_parity.py`.
- `contracts/openapi/pack-07.yaml` (tags `eligibility-service`/
  `membership-service`; the four ADR-027 narrow cross-pack reads
  deliberately have no HTTP-shaped path), `contracts/reason-codes/pack-07.yml`
  (38 entries, including the four separated-electoral-eligibility-claim
  codes and four membership human-control codes required scope item 15
  names explicitly). Ten new entity JSON Schemas
  (`participant-eligibility-policy`, `process-eligibility-policy`,
  `step-up-authentication-requirement`, `digital-decision`,
  `assembly-decision`, `party-membership-eligibility-policy`,
  `membership`, `membership-application`, `affiliation-declaration`,
  `conflict-assessment`) and twelve new event-payload JSON Schemas (the
  thirteenth named event, `EligibilityEvaluated`, reuses PACK-02's
  existing schema unchanged), all validated against real,
  directly-constructed domain instances in the new
  `tests/contract/test_ct00_01_pack07_schema_validation.py`.
  `contracts/schemas/identity-record.schema.json` updated to add canon
  19d.2's eight additive fields to `required`/`properties` (the one
  real, pre-existing contract-test gap this round found and fixed).
- `tests/contract/test_ct00_02_unknown_status.py` through
  `test_ct00_09_vote_linkability.py` each extended with a PACK-07
  section as applicable (19 new unknown-status/type `parse_*` cases
  across both services' 12 new enums; 12 forbidden-transition cases;
  event-idempotency and unsupported-event-version checks for
  representative commands from both services; missing-permission and
  audit-creation checks across both services' command surfaces; the
  eight identity-leakage proofs named above; an AST-based import scan
  confirming neither PACK-07 service imports voting/tally/delegation
  domain code, plus a direct-construction proof that
  `ProcessEligibilityClaims`/`MembershipLayerClaims` carry no
  vote/ballot-linkable field). CT-00-11 (AI Human Control) and CT-00-12
  (Emergency Stop) are explicitly documented not-applicable for this
  pack (required scope item 19 excludes new AI-processing functionality
  and no `EmergencyAction` exists in scope) — extending
  `test_ct00_12_emergency_stop_not_applicable.py`'s historical
  not-applicable list a fourth/fifth time. CT-00-10 (Rule Freeze) is
  also documented not-applicable, honestly reporting one related gap
  rather than glossing over it: canon 19d.7's `CriticalPolicyVersionFrozenError`
  is declared in both services' `exceptions.py` for forward
  compatibility but deliberately never raised this round — enforcing it
  needs a persisted Process/Election lifecycle-tracking aggregate this
  pack does not introduce (see that exception class's own docstring).
- One genuine, pre-existing production bug found and fixed via this
  round's own contract-test work (not present in any external report):
  `epd2_membership_service.events.conflict_assessment_state_payload`
  (documented as a "full, canonically-hashable snapshot ... used for
  Audit Core's `after_hash`") was silently missing three of
  `ConflictAssessment`'s thirteen fields (`evidence_references`,
  `supersedes_conflict_assessment_id`, `re_evaluation_due_at`) — those
  three fields were outside Audit Core's tamper-evidence hash. Fixed to
  cover all thirteen fields.
- `REPOSITORY_VERSION` `0.6.0 → 0.7.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts`,
  both version-consistency unit tests, and `docs/canonical/canon-
version.json`'s `repository_compatibility` upper bound widened to admit
  it). `CANON_VERSION` is unchanged (`0.6.0`) — this round implements the
  already-accepted canon 19d text; no further canon edit was made.
  `packages/typescript/epd2-types` deliberately gains no PACK-07 domain
  types — this shared package has held "no business logic" (only
  version constants) as an explicit, unbroken architectural boundary
  since PACK-01, honored here rather than overridden; canon
  cross-language contract parity is carried entirely by the JSON
  Schemas and OpenAPI spec named above, exactly as it has been for
  PACK-02 through PACK-06.
- `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`.

### Verified

- **External GitHub Actions run: PASS.** Real network access, real
  dependency installation. Exact results: all 402 required paths present;
  no forbidden paths; version consistency passed; Ruff formatting (359
  files already formatted) and lint passed; Prettier passed; ESLint
  passed; mypy passed for all services; Python 2028 passed / 4 skipped /
  0 failed; TypeScript 3/3 passed; frontend 2/2 passed; Next.js 15.5.21
  production build passed. This closes out PACK-07 implementation as a
  genuine external PASS, not a local self-report.
- Full local verification suite also run in this repository's sandboxed,
  network-restricted environment during implementation (see
  `LOCAL_VERIFICATION.md`): Ruff (lint + format) clean; mypy clean
  per-service and for `packages/python/epd2-core`/`scripts`/
  `tests/repository`/`tests/contract` (run separately per the
  `Makefile`'s own documented `--import-mode=importlib` limitation); the
  complete Python test suite passing (2020 passed, 5 skipped — the
  `hypothesis`-unavailable skip and cache-related forbidden-paths check
  that the external, clean-checkout run above doesn't hit), including
  PACK-07's own `tests/contract`/`tests/repository` additions, using the
  standalone-`pytest`/`PYTHONPATH` workaround `LOCAL_VERIFICATION.md`
  documents. TypeScript/Prettier/frontend-build verification was
  unavailable in this sandbox alone (no network access to install
  `npm`/`prettier`/Next.js toolchain dependencies) — that gap is exactly
  what the external GitHub Actions run above closes. Full detail,
  including every command's literal output and the external PASS
  results: `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`.

## [Unreleased] - canon minor version 0.6.0 (Participation & Membership Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.5.0 →
0.6.0` (ADR-026 through ADR-031, all `accepted`, no further amendment)
  — the fifth edit to this document's own text since its original
  acceptance (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 →
0.3.0`, ADR-018/ADR-020's `0.3.0 → 0.4.0`, and ADR-023/ADR-025's `0.4.0
→ 0.5.0`). Adds a new section 19d ("Участие и членство / Participation
  & Membership Context"), inserted between sections 19c and 20, the same
  non-renumbering technique used for 19a/19b/19c. Ten new canonical
  entities: `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `StepUpAuthenticationRequirement`, `DigitalDecision`,
  `AssemblyDecision` (owner: Eligibility Engine, i.e. `eligibility-service`,
  extended for the first time since PACK-02); `PartyMembershipEligibilityPolicy`,
  `AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`
  (owner: Membership Service, i.e. the new `membership-service`);
  `AuthenticationContext` (owner: Identity Verification Service, i.e.
  `identity-service`, extended). `IdentityRecord` (7.3) gains eight new
  fields (`date_of_birth`, `citizenship_status`, `residence_status`,
  `identity_assurance_level`, `identity_scheme`,
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`); its existing ten fields are unchanged. The
  generic `electoral_eligibility_met` concept — never itself a canonical
  field — is replaced everywhere by four separated claims
  (`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`). `MembershipApplication`'s
  six-state lifecycle (`application_pending`, `eligibility_review`,
  `human_decision_pending`, `approved`, `rejected`, `activated`) is
  layered on top of, without overloading, `Membership.membership_status`
  (8.3), which keeps all eight existing fields, seven existing status
  values, and its owner unchanged. `AffiliationDeclaration` gains five
  temporal/verification fields (`valid_from`, `valid_until`,
  `verification_status`, `verified_at`, `verified_by`).
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, and `StepUpAuthenticationRequirement`
  are classified as "critical policies," each gaining
  `signed_policy_digest_reference`/`transparency_log_commitment_reference`
  and a four-independent-gate activation rule (verified
  `GovernanceDecision`, `multi_person_approval_met`, signed digest,
  transparency-log commitment) plus a policy-freeze rule extending
  CT-00-10. `ProcessEligibilityPolicy` also carries seven legal-effect
  fields (`decision_effect`, `formal_confirmation_required`,
  `formal_confirmation_authority`, `secret_ballot_required`,
  `permitted_participation_mode`, `required_assurance_level`,
  `accessibility_profile`) and the `DigitalDecision → AssemblyDecision`
  formal-confirmation lifecycle. `ParticipationRightsProfile` is
  characterized as an internal, non-authoritative, never-stored derived
  model; the only two permitted enforcement mechanisms anywhere in this
  context are an atomic capability check or a single-purpose scoped
  capability token. `Appeal` (14.3) gains a documentation clarification
  only (`decision_id` as a polymorphic target reference, a standing
  default for any future appealable decision type) — no field, status,
  or owner change. The consequential-human-control hard invariant widens
  to a seventh, open-ended category (denial of a fundamental member
  right, however produced). `DomainPseudonymReference`,
  `AntiCorrelationInvariant`, and `CryptographicProtocolProfile` are
  named with their governing invariants stated (the latter's gate now
  nine items, adding timing/transport unlinkability and
  privacy-preserving revocation) but not defined as fully fielded
  entities, deferred to future implementing ADRs. A future
  architectural requirement for consequential AI-generated summaries
  (deterministic source-reference mapping, coverage metadata, human-
  review status, immutable `AIProcessingRecord` linkage) is recorded by
  reference only — `AIProcessingRecord` (17.1, 19c) itself is not
  modified. Section 20 gains a new event catalog subsection (20.16) and
  three completing `Membership` (20.5) event names
  (`membership.terminated`, `.rejected`, `.expired`). Section 22 gains
  ten new ownership-matrix rows; section 23 gains new forbidden-link
  entries. `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.6.0`) since no `membership-service` or
  `eligibility-service` extension code exists yet — this is a canon-only
  change, per CLAUDE-PACK-07's own governance round (`docs/adr/ADR-026`
  through `ADR-031`, all `accepted`; `docs/review/PACK-07-OWNER-DECISIONS.md`).
- `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`.

### Verified

- **PACK-07 canon round PASS**, confirmed by a complete external GitHub
  Actions run with real network access: 1822 Python tests passed, 3
  skipped (the same genuine CT-00-10/CT-00-12 not-applicable markers as
  the PACK-06 PASS baseline above — this canon-only round touched no
  test file besides the two version-consistency unit tests, which
  pass), TypeScript tests passed (3/3), frontend tests passed (2/2), a
  successful Next.js production build, and Prettier, Ruff, ESLint, and
  mypy all clean, with all 363 required paths present and no forbidden
  files. See `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` (§7) for
  the full breakdown, including reconciliation against this sandbox's
  own local run (1815 passed, 4 skipped — `hypothesis` cannot be
  installed here, so its one property-based test module import-skips
  as a single unit instead of running its seven tests individually).
  This is a canon/ADR-acceptance PASS only — no `membership-service`/
  `eligibility-service` implementation PASS is claimed; that remains a
  distinct, future implementation round.

## [Unreleased] - canon minor version 0.5.0 (AI Processing Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.4.0 →
0.5.0` (ADR-023 and ADR-025, both accepted with amendments) — the
  fourth edit to this document's own text since its original acceptance
  (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 → 0.3.0`, and
  ADR-018/ADR-020's `0.3.0 → 0.4.0`). Adds a new section 19c ("ИИ-
  обработка — расширение / AI Processing Context"), extending the
  already-existing section 17 (`AIProcessingRecord`, unchanged twelve
  fields and six-value `human_review_status`) rather than defining a new
  entity. Adds a new, independent `processing_status` field
  (`requested`/`input_prepared`/`processing`/`completed`/`failed`/
  `rejected_by_policy` — deliberately no stored `superseded` value) kept
  structurally separate from `human_review_status`; a unified
  `supersedes_ai_processing_record_id` field generalizing
  `GovernanceDecision.supersedes_decision_id`'s derived-supersession
  pattern to cover both a superseded processing run and a superseded
  review outcome; fifteen further fields (model/deployment governance,
  provenance/integrity, confidence/uncertainty, explainability,
  human-reviewer provenance, lifecycle timestamps); a new
  `redaction_manifest` embedded, immutable value object (nine sub-
  fields: `redaction_policy_reference`, `redaction_policy_version`,
  `input_classification`, `checked_field_categories`,
  `removed_field_categories`, `prepared_input_hash`, `validator_version`,
  `validated_at`, `result`) replacing what would otherwise have been a
  flat `redaction_policy_reference`/`redaction_applied` field pair; three
  disclosure-lifecycle fields (`disclosure_required`,
  `disclosure_package_reference`, `disclosure_receipt_reference`) plus a
  derived, non-stored `DisclosureStatus` read-model type
  (`not_required`/`pending_package`/`pending_publication`/`published`),
  mirroring `GovernanceDecision`/`FinalityStatus`'s own stored-vs-derived
  split; and `AIDisclosurePackage`, defined explicitly as a contract/
  value object — never a canonical system-of-record entity, never
  persisted by either `ai-processing-service` or `transparency-service`,
  its only durable trace being the resulting `PublicLedgerEntry` row
  (already canon, 19a.1, owned by `transparency-service`, unchanged) plus
  the two opaque reference fields on `AIProcessingRecord`. A mandatory,
  explicit five-step disclosure protocol is recorded (19c.7): verified
  human approval, immutable `AIDisclosurePackage` creation,
  `transparency-service` publication through its existing
  `publish_ledger_entry` path, receipt recording, and fail-closed
  finalization gating on `DisclosureStatus = published`. Section 20.12's
  AI event catalog is corrected (`ai.output.corrected` →
  `ai.output_corrected`) and expanded with six new events. Section 22's
  ownership matrix gains no new row (`AIProcessingRecord`'s existing "AI
  Accountability Service" ownership is unchanged; `redaction_manifest`
  and `AIDisclosurePackage` are, respectively, an embedded value object
  and a contract/value object, not separately owned entities). Section
  23's forbidden-links list gains new entries covering no-autonomous-
  decision, no-identity-reverse-lookup, no-vote-linkage-reconstruction,
  no-model-provider-mutation-authority, no-raw-private-input-in-
  disclosure, and no-hidden-reasoning-claim invariants.
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.5.0`) since no `ai-processing-service` code exists yet —
  this is a canon-only change, per CLAUDE-PACK-06's own governance round
  (`docs/adr/ADR-021` through `ADR-025`, all `accepted`;
  `docs/review/PACK-06-OWNER-DECISIONS.md`).

## [0.6.0] - AI processing context (implementation)

### Added

- A new, independent, in-memory-backed service, `ai-processing-service`
  (CLAUDE-PACK-06, "AI Processing Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, model-provider
  and redaction-validator abstractions, and in-memory reference adapters,
  implementing exactly the canon 0.5.0 section 19c text and ADR-021
  through ADR-025 (all `accepted`) with no further canon edit.
- The one canon entity this pack owns, `AIProcessingRecord` (canon 17.1,
  extended by 19c), with two independent, structurally separate status
  planes: `processing_status` (`requested -> input_prepared -> processing
-> {completed | failed | rejected_by_policy}`, `rejected_by_policy`
  also directly reachable from `requested`; no stored `superseded` value)
  and `human_review_status` (canon's unchanged six-value enum; `superseded`
  is never directly stored, only ever surfaced by the derived
  `derive_effective_human_review_status` read model, mirroring
  `GovernanceDecision`/`FinalityStatus`'s own stored-vs-derived split).
  Both statuses' `superseded` meaning route through one shared field,
  `supersedes_ai_processing_record_id`. The embedded, immutable
  `RedactionManifest` value object (nine fields) and the
  `AIDisclosurePackage` contract/value object (never persisted by either
  `ai-processing-service` or `transparency-service` — its only durable
  trace is the resulting `PublicLedgerEntry` row plus two opaque
  reference fields on `AIProcessingRecord`) are both implemented exactly
  per canon 19c.4/19c.6.
- Fifteen application-layer commands (`request_ai_processing`,
  `prepare_input`, `begin_processing`, `complete_processing_with_provider`,
  `fail_processing`, `reject_processing_by_policy`, `review_ai_output`,
  `supersede_ai_processing_record`, `assert_consequential_output_reviewed`,
  `create_disclosure_package`, `publish_ai_disclosure`,
  `assert_disclosure_complete_for_official_finalization`,
  `get_ai_processing_record`, `get_disclosure_status`,
  `get_effective_human_review_status`), each with `epd2_audit_core` audit
  entries, CT-00-04 idempotency where applicable, and eleven canonical AI
  events (canon section 20.12, corrected `ai.output.corrected` ->
  `ai.output_corrected`, plus six new events).
- `human_review_status` decided exactly once, at `request_ai_processing`
  (`pending` if `is_consequential`, else `not_required`); silence,
  timeout, a missing reviewer, or missing role verification never imply
  approval — every consequential output can finish only through an
  explicit `approved`/`approved_with_changes`/`rejected` outcome recorded
  by `review_ai_output`.
- Fourteen named fail-closed conditions (model unavailable, timeout,
  malformed output, unsupported model version, low confidence, policy
  conflict, redaction failure, prompt-injection signal, prohibited data,
  missing human reviewer, invalid reviewer role, reviewer scope mismatch,
  unverified input provenance, missing required disclosure), each mapped
  to its own registered reason code and exercised end-to-end.
- The narrow governance read dependency (ADR-022):
  `epd2_governance_service.application.verify_role_assignment_for_action`,
  returning only `authorized`/`verified_actor_reference`/
  `verified_scope_reference`/`reason_code` — the sole function
  `ai-processing-service` ever imports from `governance-service`, enforced
  by an AST-based contract test. Four reviewer roles
  (`ai_output_reviewer`, `ai_moderation_reviewer`, `ai_governance_reviewer`,
  `ai_publication_reviewer`), purpose/scope-specific authorization, and
  self-review prohibition for moderation/governance/ballot-adjacent/
  official-publication uses.
- Six closed use classes (`summarization`, `classification`,
  `recommendation`, `drafting`, `anomaly_indication`,
  `policy_compliance_assistance`) with closed `purpose_code`/`target_type`
  allow-lists (ADR-025 §2) — `anomaly_indication`'s allow-list contains no
  vote/ballot-linked `target_type` at all, structurally preventing AI
  processing from ever reconstructing vote linkage.
- A provider abstraction (`AIModelProvider` Protocol: `submit`/`cancel`
  only, no callback/tool/command parameter of any kind, so a model
  provider structurally cannot mutate Civic OS) and a redaction-validator
  abstraction (`RedactionValidator` Protocol), both with scripted test
  doubles. External providers are forbidden for voting/tally/
  participation-pattern/credential/identity/governance-sensitive/
  unrestricted-audit data and for `anomaly_indication` (self-hosted
  required); unknown `processing_region`/`data_retention_mode` is
  fail-closed.
- The mandatory five-step disclosure protocol (ADR-025 §5, canon 19c.7):
  verified approval, immutable `AIDisclosurePackage` creation,
  `transparency-service` publication through its existing
  `publish_ledger_entry` (never a direct transparency-storage write by
  this service), receipt recording, and fail-closed finalization gating
  on `DisclosureStatus = published`.
- `contracts/openapi/pack-06.yaml` (tag `ai-processing-service`;
  `verify_role_assignment_for_action` deliberately has no HTTP-shaped
  path), `contracts/reason-codes/pack-06.yml` (29 entries: 4 generic/canon,
  15 from the PACK-06 spec, 7 additive per ADR-024, 1 this service's own
  duplicate-conflict code, plus 1 audit-classification code and 1
  governance-owned code registered here purely for this file's own
  completeness, following the same cross-pack duplication precedent
  `PERMISSION_DENIED` already uses). Two entity JSON Schemas
  (`ai-processing-record`, `ai-disclosure-package`) and one event-payload
  JSON Schema, all validated against real generated payloads.
- `tests/repository/test_service_boundaries.py` extended with seven new
  PACK-06 boundary tests (no PACK-06-to-PACK-06 cross-service import, no
  other service imports PACK-06, PACK-06 calls only the ADR-022/ADR-025-
  named upstream applications, PACK-06 never imports the excluded
  identity/account/credential/eligibility/initiative/deliberation/
  moderation/delegation/voting/tally services, and the governance-service
  and transparency-service edges are each restricted by an AST-based
  scan to exactly one named function).
- `tests/contract/test_ct00_01_schema_validation.py` through
  `test_ct00_09_vote_linkability.py` each extended with a PACK-06 section
  as applicable (schema validation and unknown-`processing_status`/
  `human_review_status` rejection; the two new `parse_processing_status`
  and `parse_human_review_status` functions and their
  `UnknownProcessingStatusError`/`UnknownHumanReviewStatusError`
  exceptions newly added to `domain.py`; forbidden-transition cases for
  both status planes; event idempotency, unsupported-event-version, and
  audit-creation checks for `request_ai_processing`; the flagship
  self-review-prohibition authorization test for `review_ai_output`;
  structural schema/OpenAPI/event-payload identity- and vote-leakage
  checks; a direct-construction proof that no `anomaly_indication`
  target type is vote/ballot-linked; and an AST-based import scan
  confirming `ai-processing-service` never imports voting/tally/
  delegation/account/identity/credential service code at all). CT-00-11
  (AI Human Control) moves from not-applicable to fully and centrally
  passing for the first time, in a new dedicated file,
  `test_ct00_11_ai_human_control.py` (five end-to-end proofs: no review
  at all, silence never implying approval, an explicit rejection, a
  successful approval, and the official-publication path's additional
  published-disclosure requirement). CT-00-10 (Rule Freeze) and CT-00-12
  (Emergency Stop) are explicitly documented not-applicable for this
  pack (required scope item 17); `test_ct00_11_12_not_applicable.py` is
  renamed `test_ct00_12_emergency_stop_not_applicable.py` to reflect
  that CT-00-11 is no longer among the not-applicable markers it
  records.
- `REPOSITORY_VERSION` `0.5.0 → 0.6.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts`,
  both version-consistency unit tests, and `docs/canonical/canon-
version.json`'s `repository_compatibility` upper bound widened to admit
  it). `CANON_VERSION` is unchanged (`0.5.0`) — this round implements the
  already-accepted canon 19c text; no further canon edit was made.
- `docs/handover/PACK-06-REPORT.md`.

### Verified

- **PACK-06 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1822 Python tests passed, 3 skipped
  (genuine CT-00-10/CT-00-12 not-applicable-in-earlier-packs markers —
  CT-00-11 is no longer among them, now fully applicable and passing
  for PACK-06, section 0 above), TypeScript tests passed (3/3), frontend
  tests passed (2/2), a successful Next.js production build, and
  Prettier, Ruff, ESLint, and mypy all clean, with all 363 required
  paths present and no forbidden files. Three real, externally-found
  gaps were fixed en route to this PASS, each touching exactly one file
  and no implementation logic, schema, canon, or ADR content: a
  six-file Prettier formatting gap (revision 2); a Markdown authoring
  defect in this file's own PACK-06 test-coverage bullet — asterisks
  used as informal wildcard shorthand inside/adjacent to inline code
  spans, plus missing whitespace collapsing distinct words together
  (revision 3); and a stale hardcoded TypeScript version-test literal in
  `version.test.ts` still expecting `CANON_VERSION 0.4.0`/
  `REPOSITORY_VERSION 0.5.0` instead of the correct `0.5.0`/`0.6.0`
  (revision 4). Full detail, including every command's literal output
  and the external run's exact results: `docs/handover/PACK-06-REPORT.md`.

## [Unreleased] - canon minor version 0.4.0 (Governance Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.3.0 →
0.4.0` (ADR-018 and ADR-020, both accepted with amendments) — the third
  edit to this document's own text since its original acceptance (after
  ADR-010's `0.1.0 → 0.2.0` and ADR-013's `0.2.0 → 0.3.0`). Adds a new
  section 19b ("Governance Context") defining three new canonical
  entities — `GovernancePolicy`, `GovernanceDecision`,
  `TechnicalChallenge` — with full fields, identifiers, statuses,
  owners, invariants, allowed transitions, forbidden links, and immutable
  correction/superseding semantics, and fully integrating the
  already-canon-defined `RoleAssignment` (8.4, unchanged) as the
  authority reference every new entity relies on; a new section 20.15
  with the twelve-event Governance canonical event catalog; three new
  section 22 ownership-matrix rows; and section 23 forbidden-link
  entries reworded (the undefined `AdministratorRole` reference
  generalized to any `RoleAssignment` regardless of `role_code`) and
  extended for the three new entities. `GovernanceDecision`'s stored
  status enum is exactly `proposed`/`approved`/`rejected` (no stored
  `superseded` value; corrections use `supersedes_decision_id`,
  superseded-ness is derived at query time); `finality_outcome` stores
  only `final`/`invalidated`, with a separate four-value `FinalityStatus`
  read-model type (`provisional`/`finality_blocked`/`final`/
  `invalidated`) documented as a query/read-model, not a stored field.
  `TechnicalChallenge` uses `submitter_authorization_type`
  (`participation_credential`/`role_assignment`) plus an opaque
  `submitter_authorization_reference`, never a mandatory
  `RoleAssignment`-only reference. The accepted cross-pack write
  boundary (ADR-017) is recorded as its own subsection (19b.6):
  `voting-service` remains the sole writer of `Ballot`; `governance-service`
  never mutates `Ballot` or `ResultPublication` storage; result finality
  is represented and queried entirely through `governance-service`.
  Transparency Context (19a), AI-processing (section 17), and
  Emergency/Crisis Override (section 19) remain explicitly untouched and
  unimplemented by this addition (19b.7). `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is unchanged
  (`0.4.0`) since no `governance-service` code exists yet — this is a
  canon-only change, per CLAUDE-PACK-05's own governance round
  (`docs/adr/ADR-016` through `ADR-020`, all `accepted`;
  `docs/review/PACK-05-OWNER-DECISIONS.md`).

## [0.5.0] - governance context (implementation)

### Added

- A new, independent, in-memory-backed service, `governance-service`
  (CLAUDE-PACK-05, "Governance Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, and in-memory
  reference adapters, implementing exactly the canon 0.4.0 section 19b
  text and ADR-016 through ADR-020 (all `accepted`) with no further canon
  edit.
- All four canon 19b entities: `RoleAssignment` (canon 8.4, physically
  relocated into `governance-service` per ADR-016; `role_code` remains an
  open string at canon level, with the closed 8-value pilot taxonomy
  enforced only at the application layer), `GovernancePolicy`,
  `GovernanceDecision` (a single entity with a `decision_type`
  discriminator covering `ballot_invalidation`,
  `technical_challenge_adjudication`, `result_finality_determination`,
  `mandate`, `oversight_directive`; stored status is exactly
  `proposed`/`approved`/`rejected` — no stored `superseded` value,
  corrections use `supersedes_decision_id`), and `TechnicalChallenge`,
  plus the derived, never-stored `FinalityStatus` read model
  (`provisional`/`finality_blocked`/`final`/`invalidated`, a distinct type
  from the stored `finality_outcome`).
- Fourteen application-layer commands (`request_role_assignment`,
  `activate_role_assignment`, `revoke_role_assignment`,
  `get_role_assignment`, `propose_governance_policy`,
  `activate_governance_policy`, `propose_governance_decision`,
  `approve_governance_decision`, `reject_governance_decision`,
  `get_governance_decision`, `is_current_approved_decision`,
  `get_finality_status`, `submit_technical_challenge`,
  `begin_technical_challenge_review`, `get_technical_challenge`), each
  with `epd2_audit_core` audit entries, CT-00-04 idempotency, and the
  twelve canonical Governance events (canon section 20.15).
- Two-actor approval enforced end-to-end (ADR-020 item 1): proposer and
  approver must resolve to distinct `actor_id`s via two active, in-scope
  `RoleAssignment`s, required for `GovernancePolicy` activation, every
  `GovernanceDecision` approval/rejection, ballot invalidation, and
  result-finality determination; no role may approve or grant its own
  assignment (`SAME_ACTOR_APPROVAL_REJECTED`).
- The pilot role taxonomy (`PILOT_ROLE_CODES`, ADR-020 §5):
  `governance_policy_proposer`, `governance_policy_approver`,
  `governance_reviewer`, `technical_challenge_reviewer`,
  `ballot_invalidation_proposer`, `ballot_invalidation_approver`,
  `oversight_reviewer`, `observer`, enforced only where a `RoleAssignment`
  is created or used, never as a canon-level closed enum.
- A deployment-time-only bootstrap seed (`bootstrap.py`,
  `run_bootstrap_seed`): not exposed through the normal API surface,
  creates exactly two distinct-actor initial `RoleAssignment`s, produces
  an immutable, checksummed `BootstrapSeedManifest`, records real
  `AuditEvent`s, and is permanently disabled after its first successful
  execution (`BootstrapAlreadyExecutedError`).
- `TechnicalChallenge` submission and adjudication (canon 19b.4/19b.5):
  eligible participants via a caller-supplied, never-dereferenced
  `participation_credential`-type reference (mirroring PACK-04's
  `publish_ledger_entry` `raw_content` precedent), or authorized
  observers/reviewers via a locally-validated, active, in-scope
  `role_assignment`-type reference; adjudication is always a side effect
  of approving/rejecting the linked `technical_challenge_adjudication`
  `GovernanceDecision`, never a standalone command; finality is blocked
  while any challenge remains `submitted`/`under_review`; a zero-challenge
  result still requires an explicit two-actor
  `result_finality_determination` decision (deadline expiry alone is
  never sufficient).
- Ballot invalidation via the accepted ADR-017 Option B: `voting-service`
  remains the sole writer of `Ballot`, gaining one narrow new command
  (`epd2_voting_service.application.invalidate_ballot`) that verifies an
  approved, correctly-scoped `ballot_invalidation` `GovernanceDecision`
  (read via the new `epd2_governance_service.application.
get_governance_decision`/`is_current_approved_decision`, the first
  bidirectional cross-pack `.application`-only read edge in this
  project) before transitioning `Ballot` to `invalidated`;
  `governance-service` never writes `voting-service` storage directly.
- `contracts/openapi/pack-05.yaml` (17 operations, tag
  `governance-service`; the bootstrap seed command deliberately has no
  HTTP-shaped path at all, per required scope item 6), plus a new
  `invalidateBallot` operation added to `contracts/openapi/pack-03.yaml`
  under the `voting-service` tag. `contracts/reason-codes/pack-05.yml`
  (27 entries: 9 carried forward from the PACK-05 spec, 4 new per
  ADR-019, reused generics, and this service's own additive
  duplicate-conflict/audit-classification codes);
  `BALLOT_INVALIDATION_NOT_AUTHORIZED` independently redeclared in
  `contracts/reason-codes/pack-03.yml` too, since the literal is used by
  a real `voting-service` guard. Four entity JSON Schemas
  (`role-assignment`, `governance-policy`, `governance-decision`,
  `technical-challenge`) and four event-payload JSON Schemas, all
  validated against real generated payloads.
- `tests/repository/test_service_boundaries.py` extended with seven new
  PACK-05 boundary tests (no PACK-05-to-PACK-05 cross-service import, no
  PACK-02/04 service imports PACK-05, only `voting-service` among PACK-03
  may import `governance-service`, that edge is `.application`-only in
  both directions and matches ADR-017, PACK-05 calls only the
  ADR-017-named upstream applications
  `epd2_voting_service.application`/`epd2_tally_service.application`,
  PACK-05 never imports the excluded identity/account/eligibility/
  credential/initiative/deliberation/moderation/delegation/transparency
  services, and `tally-service` never imports `governance-service`).
- `tests/contract/test_ct00_01_schema_validation.py` through
  `test_ct00_10_rule_freeze.py` each extended with a PACK-05 section
  (schema validation for all four entities and their event payloads;
  unknown-status/forbidden-transition parametrized cases for all four
  status enums; event idempotency, unsupported-event-version,
  audit-creation checks for `request_role_assignment`; the flagship
  two-actor authorization test for `activate_governance_policy`; and
  `GovernanceDecision`'s "immutable once approved/rejected" freeze
  invariant). `test_ct00_08_identity_leakage.py` and
  `test_ct00_09_vote_linkability.py` extended with structural schema
  checks, a real end-to-end command call proving `actor_id`/
  `assigned_by`/`*_role_id`/`submitter_authorization_reference` never
  reach a public event payload, an AST-based import scan confirming
  `governance-service` never imports `epd2_delegation_service`/
  `epd2_account_service`/`epd2_identity_service` or
  `epd2_voting_service.domain`/`epd2_tally_service.domain` directly, and
  a direct-construction proof that `GovernanceDecision.subject_reference`
  rejects `vote_envelope_id` (no reverse vote-linkability path).
  `test_ct00_11_12_not_applicable.py` updated to record PACK-05's
  identical AI-processing/Emergency-Override exclusion (required scope
  item 13) alongside PACK-02's and PACK-03's.
- `REPOSITORY_VERSION` `0.4.0 → 0.5.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/
version.ts`, both version-consistency unit tests, and
  `docs/canonical/canon-version.json`'s `repository_compatibility` upper
  bound widened to admit it). `CANON_VERSION` is unchanged (`0.4.0`) —
  this round implements the already-accepted canon 19b text; no further
  canon edit was made.
- `docs/handover/PACK-05-REPORT.md`.

### Verified

- **PACK-05 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1719 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript tests passed (3/3),
  frontend tests passed (2/2), a successful Next.js production build, and
  Prettier, lint, and type checks all clean, with all 336 required paths
  present and no forbidden files. Two real, externally-found Prettier
  gaps were fixed en route (a two-file formatting gap, and a malformed
  Markdown table in `services/governance-service/README.md`) before this
  PASS; neither changed any implementation logic, schema, test, canon, or
  ADR content. Full detail: `docs/handover/PACK-05-REPORT.md`.

## [Unreleased] - canon minor version 0.3.0 (Transparency Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.2.0 →
0.3.0` (ADR-013, accepted with amendments) — the second edit to this
  document's own text since its original acceptance (the first was
  ADR-010's `0.1.0 → 0.2.0`). Adds a new section 19a ("Прозрачность /
  Transparency Context") defining four new canonical entities —
  `PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
  `LobbyLogEntry` — with full fields, identifiers, statuses, owners,
  invariants, forbidden links, and immutable/correction semantics; a new
  section 20.14 with the ten-event Transparency canonical event catalog;
  four new section 22 ownership-matrix rows; and new section 23
  forbidden-link entries covering identity, credential, vote-envelope,
  delegation, private audit payload, and internal role-reference
  exposure. Governance Context (5.12), AI-processing (section 17), and
  Emergency/Crisis Override (section 19) remain explicitly untouched and
  unimplemented by this addition (canon 19a's own closing subsection).
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is unchanged
  (`0.3.0`) since no `transparency-service` code exists yet — this is a
  canon-only change, per CLAUDE-PACK-04's own governance round
  (`docs/adr/ADR-011` through `ADR-015`, all `accepted`;
  `docs/review/PACK-04-OWNER-DECISIONS.md`).

## [0.4.0] - transparency context (implementation)

### Added

- A new, independent, in-memory-backed service, `transparency-service`
  (CLAUDE-PACK-04, "Transparency Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, and in-memory
  reference adapters, implementing exactly the canon 0.3.0 section 19a
  text and ADR-011 through ADR-015 (all `accepted`) with no further canon
  edit.
- All four canon 19a entities: `PublicLedgerEntry`, `AuditExportPackage`,
  `DisclosurePolicy`, `LobbyLogEntry` — domain models, `StrEnum` statuses,
  `ALLOWED_TRANSITIONS` state machines where canon defines one
  (`AuditExportPackage`'s `generated -> published -> superseded`,
  `DisclosurePolicy`'s `draft -> active -> superseded`,
  `LobbyLogEntry`'s `submitted -> published`), and permanent
  content-immutability with no transition table at all for
  `PublicLedgerEntry` (a correction is always a new superseding row, per
  canon 19a.1).
- Ten application-layer commands (`publish_ledger_entry`,
  `correct_ledger_entry`, `generate_audit_export_package`,
  `publish_audit_export_package`, `verify_audit_export_package`,
  `define_disclosure_policy`, `activate_disclosure_policy`,
  `submit_lobby_log_entry`, `publish_lobby_log_entry`,
  `correct_lobby_log_entry`), each with `epd2_audit_core` audit entries,
  CT-00-04 idempotency, and the ten canonical Transparency events (canon
  section 20.14).
- Per-field `DisclosurePolicy` rules (`public`/`redacted`/`restricted`/
  `prohibited` classes; missing or ambiguous rules default to
  `prohibited`; prohibited fields cannot be overridden by any rule;
  role-scope generalization uses labels only; a structural
  `FORBIDDEN_FIELD_NAMES` set — identity, account, credential,
  vote-envelope, and internal role-UUID fields — is stripped
  unconditionally before any policy is even consulted); a
  `small_cell_threshold` of `10` for analytics-shaped fields, with
  `ResultPublication` counts explicitly exempt (exact official counts
  remain exact).
- Lobby Log rules: a 7-calendar-day publication deadline
  (`is_within_publication_deadline`), mandatory automated completeness
  and prohibited-field validation on every publish, no mandatory human
  pre-publication approval by default, and corrections only through a
  new superseding entry (`correct_lobby_log_entry`), never a rewrite.
- Public audit export rules (`AuditExportPackage`): a
  `ChainProofItem`-based proof of continuity, ordering, and integrity for
  an exported hash-chain segment (`event_hash`, `previous_event_hash`,
  public-safe metadata, and sequence position per item), a
  package-level `package_digest` and an `integrity_proof`
  signature-shaped field, and an explicit non-claim of full recomputation
  of redacted private `AuditEvent` hashes (`verify_audit_export_package`
  checks the exported segment's own internal consistency only).
- `contracts/openapi/pack-04.yaml` (10 operations, tag
  `transparency-service`), `contracts/reason-codes/pack-04.yml` (18
  entries), four entity JSON Schemas (`public-ledger-entry`,
  `audit-export-package`, `disclosure-policy`, `lobby-log-entry`) and
  four event-payload JSON Schemas, all validated against real generated
  payloads.
- Additive, read-only upstream `.application`-layer functions (ADR-012):
  `epd2_audit_core.application.list_by_target_types` (used directly by
  `generate_audit_export_package`), plus four further sanctioned-but-
  not-yet-called functions (`get_published_initiative`,
  `get_initiative_version`, `get_moderation_decision`, `get_ballot`,
  `get_result_publication`) added to their respective upstream services
  and enforced as PACK-04's only permitted upstream `.application`
  imports by `tests/repository/test_service_boundaries.py`.
- `tests/repository/test_service_boundaries.py` extended with four new
  PACK-04 boundary tests (no PACK-04-to-PACK-04 cross-service import, no
  PACK-02/03 service imports PACK-04, PACK-04 calls only the
  ADR-012-named upstream applications, PACK-04 never imports
  deliberation-service, delegation-service, or the PACK-02 identity
  services).
- `tests/contract/test_ct00_08_identity_leakage.py` and
  `tests/contract/test_ct00_09_vote_linkability.py` extended with a
  PACK-04 section each: structural schema checks that no entity or event
  schema exposes an identity/credential/vote-envelope/role-UUID field,
  and a real end-to-end command call proving a caller-supplied
  vote-envelope-shaped field is dropped before it ever reaches a public
  payload.
- `REPOSITORY_VERSION` `0.3.0 → 0.4.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/
version.ts`, both version-consistency unit tests, and
  `docs/canonical/canon-version.json`'s `repository_compatibility` upper
  bound widened to admit it). `CANON_VERSION` is unchanged (`0.3.0`) —
  this round implements the already-accepted canon 19a text; no further
  canon edit was made.
- `docs/handover/PACK-04-REPORT.md`.

### Verified

- **PACK-04 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1599 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript tests passed, frontend
  tests passed, a successful Next.js production build, and Ruff,
  Prettier, ESLint, and mypy all clean, with all 305 required paths
  present and no forbidden files. Full detail:
  `docs/handover/PACK-04-REPORT.md`.

## [0.3.0] - participation and decision kernel

### Added

- Six independent, in-memory-backed services (CLAUDE-PACK-03,
  "Participation and Decision Kernel"): `initiative-service`,
  `deliberation-service`, `moderation-service`, `voting-service`,
  `tally-service`, `delegation-service`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter, following ADR-005's service decomposition.
- All 18 canon-scoped entities across the six new services: `Initiative`,
  `InitiativeVersion`, `SupportRecord`, `Amendment`, `SourceRecord`
  (initiative-service); `Discussion`, `Contribution`
  (deliberation-service); `ModerationCase`, `ModerationDecision`, `Appeal`
  (moderation-service); `Ballot`, `BallotOption`, `VoteEnvelope`,
  `VoteReceipt` (voting-service); `Tally`, `ResultPublication`
  (tally-service); `Delegation`, `DelegationSnapshot`
  (delegation-service) - each with its explicit `ALLOWED_TRANSITIONS`
  state machine (where canon defines a status enum), application-layer
  commands, canonical event construction, and `epd2_audit_core` audit
  entries for every state-changing action.
- `docs/adr/ADR-005` through `ADR-006`, `ADR-008` through `ADR-010`
  (service decomposition, reason-code additions, PACK-02 integration
  boundary, voting/delegation/quorum/tie/challenge/finality defaults, and
  the canon minor-version addition those defaults required), all accepted
  (ADR-009/ADR-010 with owner amendments) prior to this implementation.
- Structural, fail-closed enforcement of every accepted ADR-009 voting
  default: vote changes allowed until close with only the latest valid
  envelope counted (items 1-2); abstention modeled as an explicit
  `BallotOption` (item 3); `Ballot.ballot_method` restricted to
  `single_choice`/`yes_no` for this pilot (item 4); quorum optional per
  ballot (item 5); a second, distinct actor required to approve final
  ballot configuration (item 7, INV-08); `Delegation`/`DelegationSnapshot`
  implemented fully but disabled by default per ballot, maximum
  delegation depth 1 (items 8-9); a delegator's own direct vote overrides
  their delegate's (item 10); ties recorded as an explicit
  `tie_no_decision` outcome, never silently broken (item 11); and
  `Ballot.challenge_window_hours`/`ResultPublication.challenge_deadline_at`
  (canon 0.2.0, ADR-010) implemented with a 72-hour repository default,
  configurable per ballot, and a `compute_finality_state` function that
  can only ever return a provisional value - no PACK-03 code path may
  declare a `ResultPublication` final (items 12-13).
- ADR-009 item 14 (accepted with amendment): the canonical `invalidated`
  `Ballot` status and its transition structure are implemented, but no
  PACK-03 application-layer command can reach it - ballot invalidation
  authorization belongs entirely to the future Governance service.
- Structural identity-separation and vote-linkability guarantees
  (CT-00-08/CT-00-09) extended to `VoteEnvelope`, `VoteReceipt`, `Tally`,
  `ResultPublication`, `SupportRecord`, and `Delegation`: none may contain
  `account_id`, `person_id`, or `identity_record_id`, enforced via
  `additionalProperties: false` JSON Schemas and per-entity
  `FORBIDDEN_FIELD_NAMES` structural tests, plus a positive-space
  regression test proving no code path resolves a `VoteEnvelope` to an
  `Account`.
- The narrow, ADR-008-governed PACK-03 -> PACK-02 read boundary:
  `initiative-service` and `voting-service` call
  `epd2_credential_service.application.validate_participation_credential`
  and two new, additive, read-only `epd2_eligibility_service.application`
  query functions (`get_eligibility_decision`, `get_eligibility_snapshot`)
  - never either service's `storage`/`domain` modules. No other PACK-03
    service depends on PACK-02, no PACK-02 service depends on PACK-03, and
    no PACK-03 service imports another PACK-03 service's package.
- `contracts/reason-codes/pack-03.yml` (70 entries: 9 PACK-03-relevant
  canon section-24 codes, 5 reused generic canon codes, and PACK-03's own
  additive codes per ADR-006), 18 entity JSON Schemas and 18 event-payload
  JSON Schemas (`contracts/schemas/`, `contracts/events/`), and
  `contracts/openapi/pack-03.yaml` (71 paths, one per real application
  command, tagged per service).
- CT-00-01 through CT-00-10 extended to cover all six new services
  (`tests/contract/`); CT-00-11/12 remain explicitly not-applicable for
  PACK-03 (no `AIProcessingRecord`/`EmergencyAction` in scope), the same
  treatment PACK-02 gave them.
- `tests/repository/test_service_boundaries.py` extended with the PACK-03
  service matrix, the ADR-008 `.application`-only PACK-03->PACK-02 edges,
  and the one-way PACK-02/PACK-03 dependency direction, as their own
  dedicated, AST-based structural tests (not merely re-running the
  existing PACK-02-only check).
- `docs/handover/PACK-03-REPORT.md`.

### Changed

- `scripts/check_repository.py` `REQUIRED_PATHS` extended for every new
  PACK-03 path (six services, contracts, and the report).
- Root `pyproject.toml` / `package.json` workspace membership, `ruff`,
  `mypy`, and `pytest` configuration extended to cover the six new
  services; `Makefile`'s `typecheck` target gained six new scoped mypy
  invocations.
- `docs/canonical/canon-version.json`'s `repository_compatibility` range
  widened from `>=0.1.0 <0.3.0` to `>=0.1.0 <0.4.0` to admit
  `REPOSITORY_VERSION 0.3.0` - this is repository-side bookkeeping, not
  canon-immutable content; the canon document's own text and checksum are
  unchanged by this pack (still `0.2.0`,
  `5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a`).

### Verified

- **PACK-03 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1525 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript 3/3, frontend tests
  2/2, a successful Next.js production build, and Ruff, Prettier,
  ESLint, and mypy all clean, with all 277 required paths present and no
  forbidden files. Full detail: `docs/handover/PACK-03-REPORT.md`.

## [Unreleased] - canon minor version 0.2.0

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.1.0 →
0.2.0` (ADR-010, accepted with amendment) — the first edit to this
  document's own text since its original acceptance. Adds two
  backward-compatible fields: `Ballot.challenge_window_hours` (optional,
  repository default 72 hours, configurable per ballot) and
  `ResultPublication.challenge_deadline_at` (computed as `published_at +
challenge_window_hours`), plus a clarifying note that reaching
  `challenge_deadline_at` is necessary but not sufficient for finality —
  a canonical or explicitly approved technical-challenge registration and
  adjudication mechanism must exist first (its own future ADR).
  `docs/canonical/canon-version.json`, `packages/python/epd2-core/src/epd2_core/version.py`,
  and `packages/typescript/epd2-types/src/version.ts` updated to match;
  `REPOSITORY_VERSION` is unchanged (`0.2.0`) since no PACK-03 service
  code exists yet.

## [0.2.0] - identity separation and audit kernel

### Added

- Five independent, in-memory-backed services (CLAUDE-PACK-02):
  `account-service`, `identity-service`, `eligibility-service`,
  `credential-service`, `audit-core`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter.
- `epd2-audit-core`: append-only, hash-chained `AuditEvent` store
  (canon 18.1, INV-04/INV-05) with idempotent append by `audit_event_id`
  and fail-closed conflict detection on a duplicate id with different
  content.
- Identity/participation separation (INV-01): `Account` -> `IdentityRecord`
  -> `EligibilityRule`/`EligibilityDecision`/`EligibilitySnapshot` ->
  `ParticipationCredential`, with no identity-linking field on the
  credential, enforced by an automated identity-leakage test suite.
- Centralized, executable reason-code registry
  (`contracts/reason-codes/pack-02.yml`), JSON Schemas
  (`contracts/schemas/`), event payload schemas (`contracts/events/`), and
  a transport-neutral OpenAPI contract (`contracts/openapi/pack-02.yaml`).
- Contract test suite (`tests/contract/`): CT-00-01 through CT-00-10,
  CT-00-11/12 explicitly marked not-applicable; identity-leakage,
  state-transition, audit, and Hypothesis property-based tests.
- ADR-002 (identity/participation separation and canonical event/name
  resolution), ADR-003 (append-only audit hash chain), ADR-004
  (centralized reason-code registry), plus new architecture docs
  (`docs/architecture/identity-participation-separation.md`,
  `docs/architecture/audit-kernel.md`) and
  `docs/review/PACK-02-THREAT-MODEL.md`.
- `docs/handover/PACK-02-REPORT.md`.

### Changed

- `scripts/check_repository.py` and `scripts/check_forbidden_files.py`
  updated for PACK-02 (new required paths; a filename-based check for a
  forbidden central identity-participation mapping table/file, pack
  section 15).
- Root `pyproject.toml` / `package.json` workspace membership, `mypy`,
  and `pytest` configuration extended to cover the five new services and
  `tests/contract/`.

## [0.1.0] - initial repository skeleton

### Added

- Repository skeleton for EPD² Civic OS (CLAUDE-PACK-01).
- Canonical domain and event model (TZ-00, canon version 0.1.0) placed at
  `docs/canonical/TZ-00-domain-event-canon.md`.
- Architecture documentation (`docs/architecture/`) and initial ADRs
  (`docs/adr/`).
- Root Python workspace managed with `uv`, and the `epd2-core` shared
  package (version constants, UUID identifier helpers).
- Shared TypeScript package `epd2-types` (version constants).
- Minimal Next.js frontend skeleton (`frontend/web-shell`).
- Repository structure checks and top-level tests
  (`scripts/`, `tests/repository/`).
- `Makefile` with a unified command interface (`setup`, `format`, `lint`,
  `typecheck`, `test`, `check-repository`, `verify`, `clean`).
- Pre-commit configuration and GitHub Actions CI workflow.
- Contribution, security, and CODEOWNERS documentation.
