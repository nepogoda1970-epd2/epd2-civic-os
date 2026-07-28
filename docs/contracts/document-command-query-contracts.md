# Document Service command and query contracts

> PACK-11. Every command is a governed act with a reason-coded refusal
> vocabulary; every query is scoped and, where it answers a governed
> question, fails closed.

## Shared preconditions

Every state-changing command enforces, in this order:

1. determined organizational scope (`ORGANIZATION_SCOPE_UNDETERMINED`);
2. target scope match (`ORGANIZATION_SCOPE_MISMATCH`);
3. resolved authority for the action (`DOCUMENT_AUTHORITY_MISSING`);
4. role incompatibility, re-checked now (`AUTHORITY_ROLE_INCOMPATIBLE`);
5. per-act separation (`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`);
6. conflict declaration (`CONFLICT_OF_INTEREST_UNDECLARED` /
   `..._BLOCKING`);
7. idempotency (`DOCUMENT_IDEMPOTENCY_CONFLICT`);
8. optimistic concurrency (`OPTIMISTIC_CONCURRENCY_CONFLICT`);
9. version-chain integrity (`DOCUMENT_VERSION_CHAIN_BROKEN`).

## Commands

| Command | Required role | Notable additional refusals |
| ------- | ------------- | --------------------------- |
| `register_document` | custodian, author | — |
| `record_version` | author, custodian | `DOCUMENT_CORRECTION_TARGET_INVALID`, `VALIDATION_FORBIDDEN_TRANSITION` (closed document) |
| `submit_for_review` | author, custodian | `VALIDATION_FORBIDDEN_TRANSITION` |
| `record_review` | reviewer / legal reviewer | `DOCUMENT_AUTHORITY_MISSING` (unqualified reviewer for an opinion) |
| `return_for_revision` | reviewer, legal reviewer, approver | `VALIDATION_FORBIDDEN_TRANSITION` |
| `approve_version` | approver **only** | `DOCUMENT_REVIEW_INCOMPLETE` |
| `authorize_publication` | publication officer | `DOCUMENT_APPROVAL_MISSING` |
| `publish_version` | publication officer | `PUBLICATION_NOT_ALLOWED`, `DOCUMENT_ALREADY_PUBLISHED` |
| `issue_publication_rendition` | publication officer | `DOCUMENT_APPROVAL_MISSING` |
| `supersede_version` | approver, custodian | `DOCUMENT_SUPERSESSION_INVALID` |
| `revoke_version` | approver | `DOCUMENT_REVOCATION_INVALID` |
| `bind_retention` | custodian | `DOCUMENT_RETENTION_BINDING_MISSING` |
| `record_legal_hold` | custodian | — |
| `authorize_disposition` | custodian | `RECORD_UNDER_LEGAL_HOLD`, `LEGAL_HOLD_STATE_UNKNOWN`, `DOCUMENT_DISPOSITION_NOT_AUTHORIZED` |
| `determine_signature_status` | custodian, evidence custodian | `DOCUMENT_DETERMINATION_NOT_PERMITTED` |
| `determine_admissibility` | legal reviewer **only** | — |
| `register_evidence` | evidence custodian | `VALIDATION_FORBIDDEN_TRANSITION` (non-citable version) |
| `transfer_custody` | evidence custodian | `DOCUMENT_EVIDENCE_CUSTODY_BROKEN` |
| `seal_evidence_bundle` | evidence custodian | `DOCUMENT_EVIDENCE_BUNDLE_INCOMPLETE`, `DOCUMENT_EVIDENCE_BUNDLE_ALREADY_SEALED` |

## Queries

| Query | Answer on absence / foreign scope |
| ----- | ---------------------------------- |
| `resolve_document_reference` | `exists=False`, `kind=None` — identical for "not in your scope" and "does not exist" |
| `get_signature_status` | `SignatureStatus.NOT_DETERMINED` (also for a stale determination) |
| `get_admissibility_status` | `AdmissibilityStatus.NOT_DETERMINED` |
| `read_document_content` | `DOCUMENT_ACCESS_PROFILE_INSUFFICIENT`, `VALIDATION_RECORD_NOT_FOUND`, `DOCUMENT_CONTENT_DIGEST_MISMATCH` |
| `restricted_projection` | as above |
| `verify_document_integrity` | a `ChainVerificationResult` with `valid=False`, never a partial answer |

## Two-tier scope errors

A record in a foreign scope is reported with the *same* error and the same
message shape as a record that does not exist. Distinguishing them would let
a caller confirm the existence of another organization's documents by
probing identifiers.

## Technical failures are not governed refusals

`DocumentTechnicalError` carries the generic `SERVICE_STATE_READ_ONLY` code
only so the base-class contract holds. It is an infrastructure failure and
must not be presented to a user as a reason-coded decision.
