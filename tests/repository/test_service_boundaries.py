"""Repository-level structural test (CLAUDE-PACK-02, `docs/architecture/
service-boundaries.md`): no PACK-02 service imports another PACK-02
service's package from within its own `src/`, except the one intentional,
one-directional dependency every service has on `epd2_audit_core` (see
`docs/architecture/audit-kernel.md`).

This is the repository-wide counterpart to the single-pair check already in
`services/eligibility-service/tests/test_domain.py`
(`test_eligibility_service_has_no_import_dependency_on_identity_service`),
which only exercises one direction. This test walks every service's actual
`import`/`from ... import` AST nodes (not a text/grep match, so a docstring
or comment mentioning another service's name is never a false positive) and
checks the full N x N matrix of forbidden cross-service import pairs.

Must be run from the repository root.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# package import name -> its src/ directory, for every PACK-02 service.
SERVICE_PACKAGES = {
    "epd2_account_service": REPO_ROOT / "services/account-service/src/epd2_account_service",
    "epd2_identity_service": REPO_ROOT / "services/identity-service/src/epd2_identity_service",
    "epd2_eligibility_service": (
        REPO_ROOT / "services/eligibility-service/src/epd2_eligibility_service"
    ),
    "epd2_credential_service": (
        REPO_ROOT / "services/credential-service/src/epd2_credential_service"
    ),
    "epd2_audit_core": REPO_ROOT / "services/audit-core/src/epd2_audit_core",
}

# Every service may depend on epd2_core (shared, non-domain primitives - see
# docs/architecture/service-boundaries.md) and on epd2_audit_core (the one
# intentional, one-directional dependency: every service appends to the
# audit kernel, the audit kernel depends on no service). Otherwise, a
# service's own package name is the only PACK-02 service import it may make.
ALWAYS_ALLOWED = {"epd2_core", "epd2_audit_core"}


def _imported_roots(source_file: Path) -> set[str]:
    with open(source_file, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_no_service_imports_another_services_package_except_audit_core() -> None:
    violations: list[str] = []
    for package_name, src_dir in SERVICE_PACKAGES.items():
        allowed = ALWAYS_ALLOWED | {package_name}
        forbidden = set(SERVICE_PACKAGES) - allowed
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden cross-service imports found:\n" + "\n".join(violations)


def test_audit_core_depends_on_no_other_service() -> None:
    """The audit kernel is a leaf dependency (docs/architecture/audit-kernel.md):
    every service may append to it, but it must never import any of them
    back - that would create a cycle and break its status as a shared,
    independently-verifiable ledger."""
    src_dir = SERVICE_PACKAGES["epd2_audit_core"]
    other_services = set(SERVICE_PACKAGES) - {"epd2_audit_core"}
    violations: list[str] = []
    for py_file in sorted(src_dir.rglob("*.py")):
        roots = _imported_roots(py_file)
        bad = roots & other_services
        if bad:
            violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "epd2_audit_core must not import any service:\n" + "\n".join(
        violations
    )
