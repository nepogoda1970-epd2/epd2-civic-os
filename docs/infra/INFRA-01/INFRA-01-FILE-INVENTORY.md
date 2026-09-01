# INFRA-01 — Exact Changed/Added/Deleted File Inventory

**Entering baseline:** commit `8ff32c3e9ed654768ae86ac569a9c498f78c5aa2`
(tree `13e1c439f8f5b0bd37cb6519f109d9f4c02f1ef9`).

Machine-derivable at any time from the candidate's Git history:
`git diff --stat 8ff32c3e9ed654768ae86ac569a9c498f78c5aa2..HEAD`.

<!-- INVENTORY:BEGIN -->

Added files: 35
Modified files: 148
Deleted files: 0

## Added

- `.github/workflows/infra01-acceptance.yml`
- `docs/infra/INFRA-01/INFRA-01-ACCEPTANCE-MATRIX.md`
- `docs/infra/INFRA-01/INFRA-01-FILE-INVENTORY.md`
- `docs/infra/INFRA-01/INFRA-01-FIR-COVERAGE-MATRIX.md`
- `docs/infra/INFRA-01/INFRA-01-IMPLEMENTATION-REPORT.md`
- `docs/infra/INFRA-01/INFRA-01-KNOWN-LIMITATIONS.md`
- `docs/infra/INFRA-01/examples/deployment-manifest.example.json`
- `docs/infra/INFRA-01/examples/readiness-contract.example.json`
- `scripts/acceptance/__init__.py`
- `scripts/acceptance/__main__.py`
- `scripts/acceptance/boundaries.py`
- `scripts/acceptance/canonical.py`
- `scripts/acceptance/check_registry.json`
- `scripts/acceptance/codes.py`
- `scripts/acceptance/deployment_manifest.py`
- `scripts/acceptance/evidence.py`
- `scripts/acceptance/executor.py`
- `scripts/acceptance/freeze.py`
- `scripts/acceptance/frozen.py`
- `scripts/acceptance/frozen_artifacts.json`
- `scripts/acceptance/governance.py`
- `scripts/acceptance/hygiene.py`
- `scripts/acceptance/identity.py`
- `scripts/acceptance/package.py`
- `scripts/acceptance/packaging_allowlist.json`
- `scripts/acceptance/readiness.py`
- `scripts/acceptance/registry.py`
- `scripts/acceptance/schemas/check_registry.schema.json`
- `scripts/acceptance/schemas/deployment_manifest.schema.json`
- `scripts/acceptance/schemas/execution_manifest.schema.json`
- `scripts/acceptance/schemas/readiness_contract.schema.json`
- `scripts/acceptance/secret_allowlist.json`
- `scripts/acceptance/secrets_scan.py`
- `tests/repository/test_infra01_harness_units.py`
- `tests/repository/test_infra01_mutation_suite.py`

## Modified

Substantive modifications:

- `.gitignore`
- `.prettierignore`
- `Makefile`
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
- `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
- `scripts/check_pilot_roadmap.py`
- `scripts/check_repository.py`
- `services/voting-service/tests/reference/test_property.py`
- `services/voting-service/tests/reference/test_target_conformance.py`
- `tests/repository/test_pack16d_signature_dependency.py`

Mechanical Prettier normalization only (content-identical reflow by the repository's locked formatter; see Known Limitations L-06):

- `.github/workflows/consolidation-c1-accept.yml`
- `.github/workflows/pilot-roadmap-guard.yml`
- `.github/workflows/pilot04-c9-accept.yml`
- `.github/workflows/pilot04-c9-smoke.yml`
- `.github/workflows/pilot04-c9-stage1.yml`
- `CHANGELOG.md`
- `docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md`
- `docs/adr/ADR-102-CRYPTOGRAPHIC-REFERENCE-IMPLEMENTATION-ATOMIC-PERSISTENCE-AND-VERIFICATION-HARNESS.md`
- `docs/adr/ADR-101-CASTING-RECEIPT-VERIFICATION-BULLETIN-BOARD-AND-ELECTION-RECORD.md`
- `docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md`
- `docs/frontend/FRONT-02-LANGUAGE-AND-LOCALIZATION-MODEL.md`
- `docs/governance/EPD2_PARTY_ORGAN_COMPETENCE_AND_DIGITAL_AUTHORITY_MODEL_0.1.md`
- `docs/governance/EPD2_RESILIENT_TRUST_DELEGATED_REGIONAL_RECOVERY_AUDIT_MODEL_0.1.md`
- `docs/packs/PACK-16/PACK-16A-ACCEPTANCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-ACCESSIBILITY-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16A-BALLOT-MODEL-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16A-CANON-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16A-ELECTION-PROFILE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-FAILURE-AND-ABORT-MODEL.md`
- `docs/packs/PACK-16/PACK-16A-FIR-COVERAGE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-GERMAN-LEGAL-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16A-HANDOVER.md`
- `docs/packs/PACK-16/PACK-16A-OPEN-DECISIONS.md`
- `docs/packs/PACK-16/PACK-16A-PRIVACY-DATA-FLOW-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-PROTOCOL-COMPARISON.md`
- `docs/packs/PACK-16/PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-REASON-CODE-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md`
- `docs/packs/PACK-16/PACK-16A-ROLE-SEPARATION-MATRIX.md`
- `docs/packs/PACK-16/PACK-16A-SCOPE-AND-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16A-SPECIFICATION-REPORT.md`
- `docs/packs/PACK-16/PACK-16A-THREAT-MODEL.md`
- `docs/packs/PACK-16/PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16B-ACCEPTANCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md`
- `docs/packs/PACK-16/PACK-16B-CANON-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md`
- `docs/packs/PACK-16/PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md`
- `docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md`
- `docs/packs/PACK-16/PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16B-FAILURE-AND-ABORT-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md`
- `docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md`
- `docs/packs/PACK-16/PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-GUARDIAN-LIFECYCLE.md`
- `docs/packs/PACK-16/PACK-16B-HANDOVER.md`
- `docs/packs/PACK-16/PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md`
- `docs/packs/PACK-16/PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md`
- `docs/packs/PACK-16/PACK-16B-KEY-CEREMONY-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16B-KEY-CUSTODY-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16B-OPEN-DECISIONS.md`
- `docs/packs/PACK-16/PACK-16B-PARAMETER-SET-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-RANDOMNESS-ARCHITECTURE.md`
- `docs/packs/PACK-16/PACK-16B-REASON-CODE-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16B-ROLE-SEPARATION-MATRIX.md`
- `docs/packs/PACK-16/PACK-16B-SCOPE-AND-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16B-SPECIFICATION-REPORT.md`
- `docs/packs/PACK-16/PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16C-ACCEPTANCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-ACCESSIBILITY-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16C-API-CATALOG.md`
- `docs/packs/PACK-16/PACK-16C-APPEND-ONLY-AND-CONSISTENCY-MODEL.md`
- `docs/packs/PACK-16/PACK-16C-BALLOT-LIFECYCLE.md`
- `docs/packs/PACK-16/PACK-16C-BALLOT-PREPARATION-AND-ENVELOPE-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16C-BALLOT-VALIDATION-PIPELINE.md`
- `docs/packs/PACK-16/PACK-16C-BULLETIN-BOARD-ARCHITECTURE.md`
- `docs/packs/PACK-16/PACK-16C-BULLETIN-BOARD-ENTRY-CATALOG.md`
- `docs/packs/PACK-16/PACK-16C-CANON-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16C-CAST-OR-CHALLENGE-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16C-CASTING-FLOW-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16C-COERCION-AND-RECEIPT-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16C-CONTINUATION-CONSUMPTION-AND-ACCEPTANCE.md`
- `docs/packs/PACK-16/PACK-16C-DISPUTE-AND-SUPPORT-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16C-ELECTION-RECORD-COMPLETENESS-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-ELECTION-RECORD-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16C-EVENT-CATALOG.md`
- `docs/packs/PACK-16/PACK-16C-FAILURE-AND-ABORT-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-FIR-COVERAGE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-HANDOVER.md`
- `docs/packs/PACK-16/PACK-16C-INDEPENDENT-VERIFIER-REQUIREMENTS.md`
- `docs/packs/PACK-16/PACK-16C-OPEN-DECISIONS.md`
- `docs/packs/PACK-16/PACK-16C-PRIVACY-AND-METADATA-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-PROTOCOL-EVIDENCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16C-PUBLICATION-ATOMICITY-MODEL.md`
- `docs/packs/PACK-16/PACK-16C-REASON-CODE-CATALOG.md`
- `docs/packs/PACK-16/PACK-16C-RECEIPT-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16C-SCOPE-AND-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16C-SPECIFICATION-REPORT.md`
- `docs/packs/PACK-16/PACK-16C-THREAT-MODEL-EXTENSION.md`
- `docs/packs/PACK-16/PACK-16C-TURNOUT-CONFIDENTIALITY-MODEL.md`
- `docs/packs/PACK-16/PACK-16C-VERIFICATION-CLIENT-ARCHITECTURE.md`
- `docs/packs/PACK-16/PACK-16D-ACCEPTANCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16D-ATOMIC-CAST-ACCEPTANCE.md`
- `docs/packs/PACK-16/PACK-16D-ATOMIC-CHALLENGE-TRANSACTION.md`
- `docs/packs/PACK-16/PACK-16D-BALLOT-CRYPTOGRAPHY-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-BULLETIN-BOARD-REFERENCE-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-CANON-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16D-CANONICAL-ENCODING-SPECIFICATION.md`
- `docs/packs/PACK-16/PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md`
- `docs/packs/PACK-16/PACK-16D-CONCURRENCY-TEST-MATRIX.md`
- `docs/packs/PACK-16/PACK-16D-CONTINUATION-STATE-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md`
- `docs/packs/PACK-16/PACK-16D-DOMAIN-SEPARATION-REGISTRY.md`
- `docs/packs/PACK-16/PACK-16D-ELECTION-RECORD-BUILDER.md`
- `docs/packs/PACK-16/PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`
- `docs/packs/PACK-16/PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md`
- `docs/packs/PACK-16/PACK-16D-FAULT-INJECTION-MATRIX.md`
- `docs/packs/PACK-16/PACK-16D-FIR-COVERAGE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16D-HANDOVER.md`
- `docs/packs/PACK-16/PACK-16D-IDEMPOTENCY-AND-REPLAY-MODEL.md`
- `docs/packs/PACK-16/PACK-16D-IMPLEMENTATION-ARCHITECTURE.md`
- `docs/packs/PACK-16/PACK-16D-IMPLEMENTATION-REPORT.md`
- `docs/packs/PACK-16/PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md`
- `docs/packs/PACK-16/PACK-16D-LOGGING-AND-AUDIT-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16D-NEGATIVE-TEST-CORPUS.md`
- `docs/packs/PACK-16/PACK-16D-OPEN-DECISIONS.md`
- `docs/packs/PACK-16/PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-PERSISTENCE-AND-TRANSACTION-MODEL.md`
- `docs/packs/PACK-16/PACK-16D-PROOF-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-PROTOCOL-EVIDENCE-MATRIX.md`
- `docs/packs/PACK-16/PACK-16D-RANDOMNESS-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-REASON-CODE-COVERAGE.md`
- `docs/packs/PACK-16/PACK-16D-REFERENCE-VERIFIER.md`
- `docs/packs/PACK-16/PACK-16D-SCHEMA-REGISTRY.md`
- `docs/packs/PACK-16/PACK-16D-SCOPE-AND-IMPLEMENTATION-BOUNDARY.md`
- `docs/packs/PACK-16/PACK-16D-SEALED-BATCH-IMPLEMENTATION.md`
- `docs/packs/PACK-16/PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md`
- `docs/packs/PACK-16/PACK-16D-TEST-VECTOR-CATALOG.md`
- `docs/packs/PACK-16/PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md`
- `docs/roadmap/EPD2_GITHUB_HANDOFF_MAP.md`
- `docs/roadmap/EPD2_PILOT_ROADMAP_LOCK.md`
- `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`

## Deleted

None.

<!-- INVENTORY:END -->
