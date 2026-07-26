# PACK-09 — Compliance, Records Governance & Legal Workflows (specification)

|                           |                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Repository version before | `0.8.0`                                                                                                                              |
| Repository version after  | `0.9.0`                                                                                                                              |
| Canon version             | `0.7.0` (unchanged — PACK-09 proposes no canon amendment)                                                                            |
| New services              | `services/compliance-service` (one, ADR-038)                                                                                         |
| ADRs                      | ADR-038, ADR-039, ADR-040, ADR-041, ADR-042 (all `accepted` 2026-07-26)                                                              |
| Builds on                 | PACK-08's organizational substrate (`Organization`, `OrganizationalRelation`, `OrganizationalScope`), referenced by opaque UUID only |

## 1. Purpose

PACK-09 adds the legal-governance layer above PACK-08's Bund /
Landesverband / Kreisverband organization model: what may be kept and for
how long, who may destroy it and on what evidence, what litigation freezes,
what personal data is processed under which recorded basis, how a
data-subject request is handled inside a deadline, and how an internal
dispute is arbitrated independently.

It provides a **governed workflow, evidence references and
auditability**. It does **not** determine legal compliance — see section 6.

## 2. Scope

1. Record classification and versioned retention schedules.
2. Explicit retention-start facts and deterministic due-date calculation.
3. Disposal eligibility evaluation with a fixed, observable refusal order.
4. A three-step controlled destruction workflow producing immutable
   evidence.
5. Legal Hold lifecycle, including an explicit `indeterminate` state.
6. Data Catalog and Processing Registry, with legal basis as a managed
   field.
7. Governed procedural cases: workflow type, status lifecycle, required
   steps, evidence references, decisions, closure.
8. Deadlines: definitions, instances, due-date calculation, suspension,
   resumption, extension, escalation, expiration, completion — all
   append-only, all timezone-explicit.
9. Data-subject and other legal requests, including identity-verification
   _status_ without identity data.
10. Party arbitration and internal disputes with enforced procedural
    independence and explicit conflict-of-interest states.
11. Flat organizational scope isolation plus explicit, presented,
    capability-scoped cross-scope authority grants.

## 3. Hard invariants

These are requirements, not goals. Each row names where it is enforced and
where it is proven.

| #   | Invariant                                         | Enforced by                                                                                                                                                        | Proven by                                                                                                                                                                                 |
| --- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | No global user ID                                 | `domain.mint_case_party_reference`; no identity field on any entity                                                                                                | `test_ct00_08_identity_leakage.py` (PACK-09 section, exhaustive over every dataclass)                                                                                                     |
| 2   | Organization scope isolation                      | `RequestContext`, `_require_scope`, `_load_case_for_write`, `_raise_not_found`, `CrossScopeAuthorityGrant`                                                         | `test_application.py` scope-isolation section; `test_storage.py` scoped-lookup tests                                                                                                      |
| 3   | Legal Hold overrides destruction                  | `LegalHold.is_blocking` re-checked in both `authorize_destruction` and `execute_destruction`                                                                       | `test_a_hold_placed_after_authorization_still_blocks_execution`                                                                                                                           |
| 4   | No silent deletion                                | No delete method anywhere in `storage.py`; three-step workflow; create-once evidence                                                                               | `test_service_boundaries.py::test_compliance_service_storage_exposes_no_delete_operation`; `test_openapi_contract.py::test_pack09_no_delete_method_exists_for_any_governed_resource`      |
| 5   | No policy rewrite to bypass retention             | `supersede_retention_policy` + `GovernedRecord.rebound_to_policy_version` + authorization version binding                                                          | `test_superseding_a_policy_invalidates_a_standing_authorization`; `test_changing_the_retention_policy_does_not_bypass_an_active_hold`                                                     |
| 6   | Deadline history is append-only                   | `ProceduralDeadline` has no stored `status`/`due_at`; store refuses non-extending writes                                                                           | `test_status_and_due_at_are_derived_properties_not_stored_fields`; `test_the_whole_history_survives_every_transition_in_order`; `test_the_deadline_store_only_accepts_history_extensions` |
| 7   | No silent deadline reset                          | `start_deadline` refuses a second live deadline without explicit `supersedes_deadline_id`                                                                          | `test_a_second_live_deadline_of_the_same_code_needs_an_explicit_supersession`                                                                                                             |
| 8   | Separation of procedural roles                    | `ProceduralCase.__post_init__` distinctness check; `SEPARATED_ROLES`                                                                                               | `test_the_three_separated_roles_must_be_three_distinct_references`                                                                                                                        |
| 9   | No self-appointment of independent decision-maker | `domain.assert_decision_maker_eligible`                                                                                                                            | five dedicated tests in `test_domain.py` plus two in `test_application.py`                                                                                                                |
| 10  | Conflict-of-interest handling                     | `ConflictState` enum + `BLOCKING_CONFLICT_STATES`; undeclared fails closed                                                                                         | `test_an_undeclared_conflict_fails_closed_and_a_blocking_one_refuses`                                                                                                                     |
| 11  | No identity expansion                             | No identity import edge; `reject_identity_payload_keys`; verification is status + opaque reference                                                                 | `test_ct00_08_identity_leakage.py`; `test_service_boundaries.py`                                                                                                                          |
| 12  | No voting linkage                                 | No import of voting/tally/delegation; no vote-shaped field or schema property                                                                                      | `test_ct00_09_vote_linkability.py` (PACK-09 section)                                                                                                                                      |
| 13  | Audit metadata carries no prohibited payload      | Event payloads carry ids, enums, timestamps, reason codes only                                                                                                     | `test_processing_registry_writes_carry_no_identity_payload_into_audit`; `test_no_compliance_event_payload_carries_a_party_reference_or_identity_field`                                    |
| 14  | Reason-coded denial                               | One exception class per registered code; 40-code registry                                                                                                          | `test_reason_codes_registry.py` pack-09 row; `test_pack09_every_operation_documents_at_least_one_reason_coded_denial`                                                                     |
| 15  | Fail closed                                       | `ORGANIZATION_SCOPE_UNDETERMINED`, `RETENTION_START_UNDETERMINED`, `LEGAL_HOLD_STATE_UNKNOWN`, `DEADLINE_TIMEZONE_UNDETERMINED`, `CONFLICT_OF_INTEREST_UNDECLARED` | one dedicated test each                                                                                                                                                                   |

## 4. Explicitly out of scope

Party finance and Rechenschaftsbericht, sponsorship/lobbying registry
(PACK-10); document storage, evidence content, cryptographic document
version chains (PACK-11); privileged JIT/break-glass administration, DLP
(PACK-12); production database, event bus, schema registry (PACK-13); real
IAM/eID, credential issuance (PACK-14); voting threat model, cryptographic
voting (PACK-15/16); production incident response (PACK-17); user-facing
applications (PACK-18).

Only typed references and interface boundaries needed by PACK-09 itself
exist for these: `evidence_references`,
`completion_evidence_reference` and `search_result_references` (opaque
strings) and `identity_verification_reference` (opaque UUID).

## 5. Interfaces

- `contracts/openapi/pack-09.yaml` — 28 operations, all tagged
  `compliance-service`. No DELETE method. Transport-neutral: no HTTP
  server ships in this pack.
- `contracts/schemas/` — fifteen entity schemas.
- `contracts/events/` — eight event payload schemas, all using canon
  section 21's envelope.
- `contracts/reason-codes/pack-09.yml` — 40 codes.

## 6. No claim of legal compliance

PACK-09 does not, and must not be read to, establish compliance with the
GDPR, the BDSG, the Parteiengesetz or any other law. `LegalBasis` is a
_managed classification field_: choosing a value records which basis the
organization has documented, and asserts nothing about whether that basis
is sufficient or correctly chosen. Retention schedules, deadline
durations, response decisions and arbitration outcomes are all inputs
supplied by humans; the system computes deterministically from them and
records what happened. Every legal determination remains a human judgement
made outside this system.
