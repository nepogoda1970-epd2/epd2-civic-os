#!/usr/bin/env python3
"""Check that required repository files and directories exist.

Usage:
    python scripts/check_repository.py

Exits with a non-zero status and prints every missing path if anything
required is absent. Run from anywhere; the repository root is resolved
relative to this script's location.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Required top-level files and directories, per CLAUDE-PACK-01 section 5
# ("Final repository structure"). Paths are relative to the repository
# root. This intentionally does not enumerate every possible file - it
# enumerates the files and directories the package definition requires to
# exist.
REQUIRED_PATHS: tuple[str, ...] = (
    # Root
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    "CHANGELOG.md",
    "LOCAL_VERIFICATION.md",
    "Makefile",
    ".editorconfig",
    ".gitignore",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    # GitHub
    ".github/workflows/ci.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/architecture_change.yml",
    # Docs: canonical
    "docs/canonical/README.md",
    "docs/canonical/TZ-00-domain-event-canon.md",
    "docs/canonical/canon-version.json",
    # Docs: architecture
    "docs/architecture/system-context.md",
    "docs/architecture/service-boundaries.md",
    "docs/architecture/data-ownership.md",
    # Docs: adr
    "docs/adr/README.md",
    "docs/adr/ADR-000-template.md",
    "docs/adr/ADR-001-repository-strategy.md",
    "docs/adr/ADR-002-identity-participation-separation.md",
    "docs/adr/ADR-003-append-only-audit-hash-chain.md",
    "docs/adr/ADR-004-reason-code-registry.md",
    # Docs: development
    "docs/development/local-development.md",
    "docs/development/repository-rules.md",
    "docs/development/new-module-guide.md",
    # Docs: review
    "docs/review/OPEN_QUESTIONS.md",
    "docs/review/KNOWN_LIMITATIONS.md",
    # Docs: handover
    "docs/handover/PACK-01-REPORT.md",
    "docs/handover/PACK-02-REPORT.md",
    # Contracts
    "contracts/README.md",
    "contracts/openapi",
    "contracts/events",
    "contracts/schemas",
    "contracts/reason-codes/README.md",
    "contracts/fixtures",
    # Contracts: PACK-02 reason codes registry
    "contracts/reason-codes/pack-02.yml",
    # Contracts: PACK-02 JSON Schemas
    "contracts/schemas/event-envelope.schema.json",
    "contracts/schemas/account.schema.json",
    "contracts/schemas/identity-record.schema.json",
    "contracts/schemas/eligibility-rule.schema.json",
    "contracts/schemas/eligibility-decision.schema.json",
    "contracts/schemas/eligibility-snapshot.schema.json",
    "contracts/schemas/participation-credential.schema.json",
    "contracts/schemas/audit-event.schema.json",
    # Contracts: PACK-02 event payload schemas
    "contracts/events/account-event-payload.v1.schema.json",
    "contracts/events/identity-event-payload.v1.schema.json",
    "contracts/events/eligibility-evaluated-payload.v1.schema.json",
    "contracts/events/eligibility-snapshot-created-payload.v1.schema.json",
    "contracts/events/credential-issued-or-revoked-payload.v1.schema.json",
    "contracts/events/credential-validation-failed-payload.v1.schema.json",
    # Contracts: PACK-02 OpenAPI
    "contracts/openapi/pack-02.yaml",
    # Services (placeholder)
    "services/README.md",
    # Services: account-service
    "services/account-service/README.md",
    "services/account-service/pyproject.toml",
    "services/account-service/src/epd2_account_service/__init__.py",
    "services/account-service/src/epd2_account_service/domain.py",
    "services/account-service/src/epd2_account_service/application.py",
    "services/account-service/src/epd2_account_service/events.py",
    "services/account-service/src/epd2_account_service/exceptions.py",
    "services/account-service/src/epd2_account_service/storage.py",
    "services/account-service/tests/test_domain.py",
    "services/account-service/tests/test_application.py",
    # Services: identity-service
    "services/identity-service/README.md",
    "services/identity-service/pyproject.toml",
    "services/identity-service/src/epd2_identity_service/__init__.py",
    "services/identity-service/src/epd2_identity_service/domain.py",
    "services/identity-service/src/epd2_identity_service/application.py",
    "services/identity-service/src/epd2_identity_service/events.py",
    "services/identity-service/src/epd2_identity_service/exceptions.py",
    "services/identity-service/src/epd2_identity_service/storage.py",
    "services/identity-service/tests/test_domain.py",
    "services/identity-service/tests/test_application.py",
    # Services: eligibility-service
    "services/eligibility-service/README.md",
    "services/eligibility-service/pyproject.toml",
    "services/eligibility-service/src/epd2_eligibility_service/__init__.py",
    "services/eligibility-service/src/epd2_eligibility_service/domain.py",
    "services/eligibility-service/src/epd2_eligibility_service/application.py",
    "services/eligibility-service/src/epd2_eligibility_service/events.py",
    "services/eligibility-service/src/epd2_eligibility_service/exceptions.py",
    "services/eligibility-service/src/epd2_eligibility_service/storage.py",
    "services/eligibility-service/tests/test_domain.py",
    "services/eligibility-service/tests/test_application.py",
    # Services: credential-service
    "services/credential-service/README.md",
    "services/credential-service/pyproject.toml",
    "services/credential-service/src/epd2_credential_service/__init__.py",
    "services/credential-service/src/epd2_credential_service/domain.py",
    "services/credential-service/src/epd2_credential_service/application.py",
    "services/credential-service/src/epd2_credential_service/events.py",
    "services/credential-service/src/epd2_credential_service/exceptions.py",
    "services/credential-service/src/epd2_credential_service/storage.py",
    "services/credential-service/src/epd2_credential_service/validation.py",
    "services/credential-service/tests/test_domain.py",
    "services/credential-service/tests/test_application.py",
    "services/credential-service/tests/test_storage.py",
    "services/credential-service/tests/test_validation.py",
    # Services: audit-core
    "services/audit-core/README.md",
    "services/audit-core/pyproject.toml",
    "services/audit-core/src/epd2_audit_core/__init__.py",
    "services/audit-core/src/epd2_audit_core/domain.py",
    "services/audit-core/src/epd2_audit_core/application.py",
    "services/audit-core/src/epd2_audit_core/exceptions.py",
    "services/audit-core/src/epd2_audit_core/hash_chain.py",
    "services/audit-core/src/epd2_audit_core/storage.py",
    "services/audit-core/tests/test_domain.py",
    "services/audit-core/tests/test_application.py",
    "services/audit-core/tests/test_hash_chain.py",
    "services/audit-core/tests/test_storage.py",
    # Python packages
    "packages/python/README.md",
    "packages/python/epd2-core/README.md",
    "packages/python/epd2-core/pyproject.toml",
    "packages/python/epd2-core/src/epd2_core/__init__.py",
    "packages/python/epd2-core/src/epd2_core/version.py",
    "packages/python/epd2-core/src/epd2_core/identifiers.py",
    "packages/python/epd2-core/tests/test_version.py",
    "packages/python/epd2-core/tests/test_identifiers.py",
    # TypeScript packages
    "packages/typescript/README.md",
    "packages/typescript/epd2-types/README.md",
    "packages/typescript/epd2-types/package.json",
    "packages/typescript/epd2-types/tsconfig.json",
    "packages/typescript/epd2-types/src/index.ts",
    "packages/typescript/epd2-types/src/version.ts",
    "packages/typescript/epd2-types/tests/version.test.ts",
    # Frontend
    "frontend/README.md",
    "frontend/web-shell/README.md",
    "frontend/web-shell/package.json",
    "frontend/web-shell/next.config.ts",
    "frontend/web-shell/tsconfig.json",
    "frontend/web-shell/eslint.config.mjs",
    "frontend/web-shell/app/layout.tsx",
    "frontend/web-shell/app/page.tsx",
    "frontend/web-shell/tests/smoke.test.ts",
    # Scripts
    "scripts/check_repository.py",
    "scripts/check_forbidden_files.py",
    "scripts/verify_versions.py",
    # Tests
    "tests/repository/test_required_files.py",
    "tests/repository/test_forbidden_paths.py",
    "tests/repository/test_version_consistency.py",
    "tests/repository/test_service_boundaries.py",
    # Tests: PACK-02 contract test suite
    "tests/contract/conftest.py",
    "tests/contract/_schema_helpers.py",
    "tests/contract/test_ct00_01_schema_validation.py",
    "tests/contract/test_ct00_02_unknown_status.py",
    "tests/contract/test_ct00_03_forbidden_transition.py",
    "tests/contract/test_ct00_04_event_idempotency.py",
    "tests/contract/test_ct00_05_unsupported_event_version.py",
    "tests/contract/test_ct00_06_missing_permission.py",
    "tests/contract/test_ct00_07_audit_creation.py",
    "tests/contract/test_ct00_08_identity_leakage.py",
    "tests/contract/test_ct00_09_vote_linkability.py",
    "tests/contract/test_ct00_10_rule_freeze.py",
    "tests/contract/test_ct00_11_12_not_applicable.py",
    "tests/contract/test_state_transitions.py",
    "tests/contract/test_audit.py",
    "tests/contract/test_reason_codes_registry.py",
    "tests/contract/test_openapi_contract.py",
    "tests/contract/test_property_based.py",
)


def find_missing_required_paths(root: Path) -> list[str]:
    """Return the list of required paths (relative, as strings) that are
    missing under `root`."""
    missing: list[str] = []
    for rel_path in REQUIRED_PATHS:
        if not (root / rel_path).exists():
            missing.append(rel_path)
    return missing


def main() -> int:
    missing = find_missing_required_paths(REPO_ROOT)
    if missing:
        print("Missing required paths:")
        for path in missing:
            print(f"  - {path}")
        return 1
    print(f"OK: all {len(REQUIRED_PATHS)} required paths are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
