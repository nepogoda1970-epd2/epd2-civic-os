"""Repository-level structural test (CLAUDE-PACK-02, `docs/architecture/
service-boundaries.md`; CLAUDE-PACK-03, `docs/adr/ADR-005-pack-03-service-decomposition.md`
and `docs/adr/ADR-008-pack-03-pack-02-integration-boundary.md`): no service
imports another service's package from within its own `src/` except the
one intentional, one-directional dependency every service has on
`epd2_audit_core` (see `docs/architecture/audit-kernel.md`), plus the
specific, narrow, `.application`-only PACK-03 -> PACK-02 edges ADR-008
enumerates.

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
PACK02_SERVICE_PACKAGES = {
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

# package import name -> its src/ directory, for every PACK-03 service
# (ADR-005's six-service decomposition).
PACK03_SERVICE_PACKAGES = {
    "epd2_initiative_service": (
        REPO_ROOT / "services/initiative-service/src/epd2_initiative_service"
    ),
    "epd2_deliberation_service": (
        REPO_ROOT / "services/deliberation-service/src/epd2_deliberation_service"
    ),
    "epd2_moderation_service": (
        REPO_ROOT / "services/moderation-service/src/epd2_moderation_service"
    ),
    "epd2_voting_service": REPO_ROOT / "services/voting-service/src/epd2_voting_service",
    "epd2_tally_service": REPO_ROOT / "services/tally-service/src/epd2_tally_service",
    "epd2_delegation_service": (
        REPO_ROOT / "services/delegation-service/src/epd2_delegation_service"
    ),
}

# package import name -> its src/ directory, for the one PACK-04 service
# (ADR-011's single-service decomposition).
PACK04_SERVICE_PACKAGES = {
    "epd2_transparency_service": (
        REPO_ROOT / "services/transparency-service/src/epd2_transparency_service"
    ),
}

# Every service in the repository (all three packs).
SERVICE_PACKAGES = {
    **PACK02_SERVICE_PACKAGES,
    **PACK03_SERVICE_PACKAGES,
    **PACK04_SERVICE_PACKAGES,
}

# Every service may depend on epd2_core (shared, non-domain primitives - see
# docs/architecture/service-boundaries.md) and on epd2_audit_core (the one
# intentional, one-directional dependency: every service appends to the
# audit kernel, the audit kernel depends on no service). Otherwise, a
# service's own package name is the only same-pack service import it may
# make, except the narrow PACK-03 -> PACK-02 edges below (ADR-008).
ALWAYS_ALLOWED = {"epd2_core", "epd2_audit_core"}

# ADR-008 Decision item 1: the exact, enumerated PACK-03 -> PACK-02 edges,
# each scoped to the OTHER service's `.application` submodule only - never
# `.storage`/`.domain` (INV-03; this is the security-critical boundary
# CT-00-08/CT-00-09 depend on, per ADR-008's own Security impact section).
# A PACK-03 service not listed here (deliberation-service, moderation-
# service, tally-service, delegation-service) has NO PACK-02 dependency at
# all - ADR-008 requires any newly-discovered need to go through its own
# ADR amendment first, never a silent import.
ALLOWED_PACK03_TO_PACK02_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_initiative_service": frozenset(
        {
            "epd2_credential_service.application",
            "epd2_eligibility_service.application",
        }
    ),
    "epd2_deliberation_service": frozenset(),
    "epd2_moderation_service": frozenset(),
    "epd2_voting_service": frozenset(
        {
            "epd2_credential_service.application",
            "epd2_eligibility_service.application",
        }
    ),
    "epd2_tally_service": frozenset(),
    "epd2_delegation_service": frozenset(),
}

# ADR-012 Decision: the exact, enumerated PACK-04 -> PACK-03 edges, each
# scoped to the OTHER service's `.application` submodule only - never
# `.storage`/`.domain` (the same INV-03 boundary ADR-008 already drew for
# PACK-03 -> PACK-02). `transparency-service` is the only PACK-04 service
# (ADR-011) and is the first service in this project to read from another
# same-generation pack rather than an older one. Explicitly excluded (not
# merely absent): `epd2_deliberation_service`, `epd2_delegation_service`,
# and every PACK-02 identity/credential-adjacent service - ADR-012's own
# Decision names none of them as an edge.
ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_transparency_service": frozenset(
        {
            "epd2_initiative_service.application",
            "epd2_moderation_service.application",
            "epd2_voting_service.application",
            "epd2_tally_service.application",
        }
    ),
}

#: PACK-04 services (i.e. `transparency-service`) may read from these
#: upstream PACK-03 services' `.application` layer (ADR-012) - a strict
#: subset of all PACK-03 services, explicitly excluding
#: `epd2_deliberation_service` and `epd2_delegation_service`.
PACK04_ALLOWED_PACK03_ROOTS = frozenset(
    {
        "epd2_initiative_service",
        "epd2_moderation_service",
        "epd2_voting_service",
        "epd2_tally_service",
    }
)


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


def _imported_module_paths(source_file: Path) -> set[str]:
    """Full dotted module paths actually imported (e.g.
    `epd2_credential_service.application`, not just the root package name
    `epd2_credential_service`) - needed to enforce ADR-008's `.application`
    -only restriction, which a root-name-only check cannot express."""
    with open(source_file, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    paths: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            paths.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            paths.add(node.module)
    return paths


def test_no_pack02_service_imports_another_pack02_services_package_except_audit_core() -> None:
    """Unchanged PACK-02 behaviour (CLAUDE-PACK-02's own five-service
    matrix) - re-run, not weakened, now that PACK-03 exists alongside it."""
    violations: list[str] = []
    for package_name, src_dir in PACK02_SERVICE_PACKAGES.items():
        allowed = ALWAYS_ALLOWED | {package_name}
        forbidden = set(PACK02_SERVICE_PACKAGES) - allowed
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden cross-service imports found:\n" + "\n".join(violations)


def test_no_pack03_service_imports_another_pack03_services_package() -> None:
    """ADR-008 Decision item 3 / ADR-005: no PACK-03 service may import
    another PACK-03 service's package - the six services communicate only
    through canonical events or an explicit, separately-named interface
    (neither of which is a Python import of the sibling package)."""
    violations: list[str] = []
    for package_name, src_dir in PACK03_SERVICE_PACKAGES.items():
        forbidden = set(PACK03_SERVICE_PACKAGES) - {package_name}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden PACK-03<->PACK-03 imports found:\n" + "\n".join(violations)


def test_no_pack02_service_imports_any_pack03_service() -> None:
    """ADR-008 Decision item 2: the dependency direction is one-way. PACK-02
    shipped and passed verification before PACK-03 existed and must remain
    ignorant of participation/decision concerns."""
    violations: list[str] = []
    for src_dir in PACK02_SERVICE_PACKAGES.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK03_SERVICE_PACKAGES)
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "PACK-02 must not import any PACK-03 service:\n" + "\n".join(
        violations
    )


def test_pack03_services_only_call_pack02_applications_named_in_adr008() -> None:
    """ADR-008 Decision item 1: a PACK-03 service may depend on a PACK-02
    service ONLY via that service's `.application` submodule, and only on
    the specific edges ADR-008 enumerates - never `.storage`/`.domain`
    (INV-03), and never a PACK-02 service not named for it at all."""
    violations: list[str] = []
    for package_name, src_dir in PACK03_SERVICE_PACKAGES.items():
        allowed_paths = ALLOWED_PACK03_TO_PACK02_APPLICATION_MODULES[package_name]
        allowed_pack02_roots = {path.split(".")[0] for path in allowed_paths}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            touched_pack02_roots = roots & set(PACK02_SERVICE_PACKAGES) - {"epd2_audit_core"}
            if not touched_pack02_roots:
                continue
            # Every touched PACK-02 root must itself be an allowed edge...
            unauthorized_roots = touched_pack02_roots - allowed_pack02_roots
            if unauthorized_roots:
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports unauthorized PACK-02 "
                    f"service(s) {sorted(unauthorized_roots)} (not an ADR-008 edge for "
                    f"{package_name})"
                )
                continue
            # ...and every such import must resolve to exactly the
            # `.application` module path, never a bare root import or a
            # `.storage`/`.domain` submodule.
            module_paths = _imported_module_paths(py_file)
            for root in touched_pack02_roots:
                touched_dotted = {p for p in module_paths if p == root or p.startswith(root + ".")}
                bad_paths = touched_dotted - allowed_paths
                if bad_paths:
                    root_allowed = sorted(p for p in allowed_paths if p.startswith(root))
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad_paths)} - "
                        f"only {root_allowed} is authorized for {package_name} (ADR-008)"
                    )
    assert violations == [], "Unauthorized PACK-03 -> PACK-02 imports found:\n" + "\n".join(
        violations
    )


def test_no_pack04_service_imports_another_pack04_services_package() -> None:
    """There is only one PACK-04 service today (ADR-011), so this is
    currently vacuous, but it is kept for symmetry with
    `test_no_pack03_service_imports_another_pack03_services_package` and
    to fail loudly if a second PACK-04 service is ever added without
    updating this file."""
    violations: list[str] = []
    for package_name, src_dir in PACK04_SERVICE_PACKAGES.items():
        forbidden = set(PACK04_SERVICE_PACKAGES) - {package_name}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden PACK-04<->PACK-04 imports found:\n" + "\n".join(violations)


def test_no_pack02_or_pack03_service_imports_pack04_service() -> None:
    """ADR-012's dependency direction is one-way: `transparency-service`
    reads from PACK-02/03; no PACK-02/03 service may import it back."""
    violations: list[str] = []
    for src_dir in {**PACK02_SERVICE_PACKAGES, **PACK03_SERVICE_PACKAGES}.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK04_SERVICE_PACKAGES)
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "PACK-02/03 must not import any PACK-04 service:\n" + "\n".join(
        violations
    )


def test_pack04_service_only_calls_upstream_applications_named_in_adr012() -> None:
    """ADR-012 Decision: `transparency-service` may depend on an upstream
    PACK-03 service ONLY via that service's `.application` submodule, and
    only on the specific edges ADR-012 enumerates - never
    `.storage`/`.domain`, and never a PACK-02/03 service not named for it
    (in particular, never `epd2_deliberation_service`,
    `epd2_delegation_service`, or any PACK-02 identity/credential-adjacent
    service)."""
    violations: list[str] = []
    for package_name, src_dir in PACK04_SERVICE_PACKAGES.items():
        allowed_paths = ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES[package_name]
        allowed_roots = {path.split(".")[0] for path in allowed_paths}
        forbidden_roots = (set(PACK02_SERVICE_PACKAGES) | set(PACK03_SERVICE_PACKAGES)) - {
            "epd2_audit_core"
        }
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            touched_forbidden_universe = roots & forbidden_roots
            if not touched_forbidden_universe:
                continue
            unauthorized_roots = touched_forbidden_universe - allowed_roots
            if unauthorized_roots:
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports unauthorized service(s) "
                    f"{sorted(unauthorized_roots)} (not an ADR-012 edge for {package_name})"
                )
                continue
            module_paths = _imported_module_paths(py_file)
            for root in touched_forbidden_universe:
                touched_dotted = {p for p in module_paths if p == root or p.startswith(root + ".")}
                bad_paths = touched_dotted - allowed_paths
                if bad_paths:
                    root_allowed = sorted(p for p in allowed_paths if p.startswith(root))
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad_paths)} - "
                        f"only {root_allowed} is authorized for {package_name} (ADR-012)"
                    )
    assert violations == [], "Unauthorized PACK-04 -> upstream imports found:\n" + "\n".join(
        violations
    )


def test_pack04_service_never_imports_deliberation_or_delegation_or_pack02_identity_services() -> (
    None
):
    """ADR-012's explicit exclusions, tested as positive assertions (not
    merely "unlisted") per that ADR's own instruction: `transparency-
    service` must never import `epd2_deliberation_service`,
    `epd2_delegation_service`, `epd2_account_service`,
    `epd2_identity_service`, `epd2_eligibility_service`, or
    `epd2_credential_service`, under any module path."""
    excluded = frozenset(
        {
            "epd2_deliberation_service",
            "epd2_delegation_service",
            "epd2_account_service",
            "epd2_identity_service",
            "epd2_eligibility_service",
            "epd2_credential_service",
        }
    )
    violations: list[str] = []
    for src_dir in PACK04_SERVICE_PACKAGES.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & excluded
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], (
        "ADR-012-excluded imports found in transparency-service:\n" + "\n".join(violations)
    )


def test_audit_core_depends_on_no_other_service() -> None:
    """The audit kernel is a leaf dependency (docs/architecture/audit-kernel.md):
    every service may append to it, but it must never import any of them
    back - that would create a cycle and break its status as a shared,
    independently-verifiable ledger. Applies across both packs."""
    src_dir = PACK02_SERVICE_PACKAGES["epd2_audit_core"]
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
