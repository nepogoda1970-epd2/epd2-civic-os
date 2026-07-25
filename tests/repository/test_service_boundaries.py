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

# package import name -> its src/ directory, for the one PACK-05 service
# (ADR-016's single-service decomposition).
PACK05_SERVICE_PACKAGES = {
    "epd2_governance_service": (
        REPO_ROOT / "services/governance-service/src/epd2_governance_service"
    ),
}

# package import name -> its src/ directory, for the one PACK-06 service
# (ADR-021's single-service decomposition).
PACK06_SERVICE_PACKAGES = {
    "epd2_ai_processing_service": (
        REPO_ROOT / "services/ai-processing-service/src/epd2_ai_processing_service"
    ),
}

# package import name -> its src/ directory, for the one PACK-07 service
# (ADR-026's single-new-service decomposition - PACK-07 also *extends*
# eligibility-service, already a PACK-02 service, with new command/read
# functions rather than a new package; `membership-service` is the only
# wholly new package this implementation round introduces).
PACK07_SERVICE_PACKAGES = {
    "epd2_membership_service": (
        REPO_ROOT / "services/membership-service/src/epd2_membership_service"
    ),
}

# Every service in the repository (all six packs).
SERVICE_PACKAGES = {
    **PACK02_SERVICE_PACKAGES,
    **PACK03_SERVICE_PACKAGES,
    **PACK04_SERVICE_PACKAGES,
    **PACK05_SERVICE_PACKAGES,
    **PACK06_SERVICE_PACKAGES,
    **PACK07_SERVICE_PACKAGES,
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

# ADR-017 Decision: the exact, enumerated PACK-05 -> PACK-03 read edges,
# each scoped to the OTHER service's `.application` submodule only -
# never `.storage`/`.domain` (the same INV-03 boundary ADR-008/ADR-012
# already drew). `governance-service` is the only PACK-05 service
# (ADR-016). Explicitly excluded (not merely absent): every PACK-02
# service, `epd2_deliberation_service`, `epd2_delegation_service`,
# `epd2_initiative_service`, `epd2_moderation_service` - ADR-017's own
# Decision names only `epd2_voting_service`/`epd2_tally_service` as read
# edges for this pack.
ALLOWED_PACK05_TO_UPSTREAM_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_governance_service": frozenset(
        {
            "epd2_voting_service.application",
            "epd2_tally_service.application",
        }
    ),
}

# ADR-017 Decision's own reverse edge: `voting-service` (PACK-03) is
# authorized to read back from `governance-service` (PACK-05), via
# `epd2_governance_service.application` only - the first bidirectional
# cross-pack relationship in this project. No other PACK-02/03/04
# service may import `epd2_governance_service` at all (tested below).
ALLOWED_PACK03_TO_PACK05_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_voting_service": frozenset({"epd2_governance_service.application"}),
}

# ADR-022 Decision: the exact, enumerated PACK-06 -> PACK-05 read edge,
# scoped to `epd2_governance_service.application` only - never
# `.storage`/`.domain` (the same INV-03 boundary every other cross-pack
# edge in this project already respects).
ALLOWED_PACK06_TO_PACK05_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_ai_processing_service": frozenset({"epd2_governance_service.application"}),
}

# ADR-022's own stated aspiration ("a future contract test" to confirm
# only one function is imported) - the strictest, single-function entry
# in this whole matrix: `ai-processing-service` may import exactly
# `verify_role_assignment_for_action` from `epd2_governance_service.
# application`, never `get_role_assignment`, `get_governance_decision`,
# `propose_governance_decision`, or any other function on that module.
ALLOWED_PACK06_GOVERNANCE_FUNCTIONS: frozenset[str] = frozenset(
    {"verify_role_assignment_for_action"}
)

# ADR-025 §5's disclosure protocol: the exact, enumerated PACK-06 ->
# PACK-04 read/write edge (the first PACK-06 -> PACK-04 edge in this
# project), scoped to `epd2_transparency_service.application` only -
# never `.storage`/`.domain`.
ALLOWED_PACK06_TO_PACK04_APPLICATION_MODULES: dict[str, frozenset[str]] = {
    "epd2_ai_processing_service": frozenset({"epd2_transparency_service.application"}),
}

# The disclosure protocol (19c.7 step 3) uses exactly one existing
# transparency-service command, `publish_ledger_entry` - never
# `correct_ledger_entry`, `define_disclosure_policy`,
# `activate_disclosure_policy`, or any other function on that module.
# `ai-processing-service` never writes `PublicLedgerEntry` itself; this
# is the one sanctioned call site.
ALLOWED_PACK06_TRANSPARENCY_FUNCTIONS: frozenset[str] = frozenset({"publish_ledger_entry"})

# ADR-027 Decision (PACK-07 implementation round, canon-0.6.0): the exact,
# enumerated cross-service edges `eligibility-service` gains, each scoped
# to the OTHER service's `.application` submodule only - never
# `.storage`/`.domain` (the same INV-03 boundary every other cross-pack
# edge in this project already respects). `epd2_credential_service` was
# already same-generation (both PACK-02) but had never actually been used
# until PACK-07's scoped-capability-token mechanism
# (`derive_and_issue_scoped_capability_token` ->
# `issue_participation_credential`); `epd2_identity_service` and
# `epd2_membership_service` are wholly new edges for this service;
# `epd2_governance_service` reuses PACK-05's existing
# `verify_decision_authorizes_policy_activation` (the same function
# `membership-service` also reuses - see below). `epd2_account_service`
# remains fully excluded - ADR-027 names no such edge.
ALLOWED_ELIGIBILITY_PACK07_APPLICATION_MODULES: frozenset[str] = frozenset(
    {
        "epd2_identity_service.application",
        "epd2_membership_service.application",
        "epd2_credential_service.application",
        "epd2_governance_service.application",
    }
)

# ADR-027 Decision: the exact, enumerated cross-service edges
# `membership-service` (PACK-07's one new service) is authorized to
# depend on, each scoped to `.application` only. Never
# `epd2_account_service`, `epd2_credential_service`,
# `epd2_moderation_service` (its own `Appeal` is a documented duplicate,
# never an import - see `epd2_membership_service.domain`'s own module
# docstring and `test_pack07_duplicated_logic_parity.py`), or any other
# service.
ALLOWED_MEMBERSHIP_APPLICATION_MODULES: frozenset[str] = frozenset(
    {
        "epd2_identity_service.application",
        "epd2_eligibility_service.application",
        "epd2_governance_service.application",
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


def _imported_names_from_module(source_file: Path, module: str) -> set[str]:
    """The specific names imported via `from <module> import name1, name2`
    - needed for ADR-022's stricter, single-function check (only
    `verify_role_assignment_for_action` may ever be imported from
    `epd2_governance_service.application`, not merely "some function on
    that module"). A bare `import <module>` (never used by any real call
    site in this repository for a cross-pack edge) is not resolved here -
    only the `from ... import ...` form this project's convention
    actually uses."""
    with open(source_file, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def test_no_pack02_service_imports_another_pack02_services_package_except_audit_core() -> None:
    """Unchanged PACK-02 behaviour (CLAUDE-PACK-02's own five-service
    matrix) - re-run, not weakened, now that PACK-03 exists alongside it.

    `epd2_eligibility_service` gets one narrow exception for PACK-07
    (ADR-027): it may additionally import `epd2_identity_service` and
    `epd2_credential_service` (both still same-generation PACK-02
    services) - checked precisely, application-only, exact-edge, in
    `test_eligibility_service_pack07_edges_are_application_only_and_match_adr027`
    below. No other PACK-02 service gets any such exception here."""
    violations: list[str] = []
    for package_name, src_dir in PACK02_SERVICE_PACKAGES.items():
        allowed = ALWAYS_ALLOWED | {package_name}
        if package_name == "epd2_eligibility_service":
            allowed = allowed | {"epd2_identity_service", "epd2_credential_service"}
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


def test_no_pack05_service_imports_another_pack05_services_package() -> None:
    """There is only one PACK-05 service today (ADR-016), so this is
    currently vacuous, but it is kept for symmetry with
    `test_no_pack04_service_imports_another_pack04_services_package` and
    to fail loudly if a second PACK-05 service is ever added without
    updating this file."""
    violations: list[str] = []
    for package_name, src_dir in PACK05_SERVICE_PACKAGES.items():
        forbidden = set(PACK05_SERVICE_PACKAGES) - {package_name}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden PACK-05<->PACK-05 imports found:\n" + "\n".join(violations)


def test_no_pack02_or_pack04_service_imports_pack05_service() -> None:
    """ADR-017's dependency direction: `governance-service` reads from
    PACK-03 (`voting-service`/`tally-service` only); no PACK-02 service,
    and no PACK-04 service, may import it back. (PACK-03's own reverse
    edge is checked separately below, since `voting-service` is the one
    explicitly authorized exception - ADR-017's bidirectional edge.)

    `epd2_eligibility_service` gets one additional, narrow exception for
    PACK-07 (ADR-027): it reuses `verify_decision_authorizes_policy_activation`
    for critical-policy activation - checked precisely, application-only,
    exact-function, in
    `test_eligibility_service_pack07_edges_are_application_only_and_match_adr027`
    below."""
    violations: list[str] = []
    for package_name, src_dir in {**PACK02_SERVICE_PACKAGES, **PACK04_SERVICE_PACKAGES}.items():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK05_SERVICE_PACKAGES)
            if bad and package_name == "epd2_eligibility_service":
                continue
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "PACK-02/04 must not import any PACK-05 service:\n" + "\n".join(
        violations
    )


def test_only_voting_service_among_pack03_may_import_pack05_service() -> None:
    """ADR-017's one bidirectional edge: `voting-service` may import
    `epd2_governance_service` (via `.application` only, checked in
    `test_pack03_to_pack05_edge_is_application_only_and_matches_adr017`
    below); every other PACK-03 service
    (`initiative-service`/`deliberation-service`/`moderation-service`/
    `tally-service`/`delegation-service`) must not."""
    violations: list[str] = []
    for package_name, src_dir in PACK03_SERVICE_PACKAGES.items():
        if package_name == "epd2_voting_service":
            continue
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK05_SERVICE_PACKAGES)
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], (
        "Only voting-service may import a PACK-05 service (ADR-017):\n" + "\n".join(violations)
    )


def test_pack03_to_pack05_edge_is_application_only_and_matches_adr017() -> None:
    """ADR-017's one bidirectional edge, `voting-service` ->
    `governance-service`, is scoped to `.application` only - never
    `.storage`/`.domain` (the same INV-03 boundary every other cross-pack
    edge in this project already respects)."""
    violations: list[str] = []
    for package_name, allowed_paths in ALLOWED_PACK03_TO_PACK05_APPLICATION_MODULES.items():
        src_dir = PACK03_SERVICE_PACKAGES[package_name]
        allowed_roots = {path.split(".")[0] for path in allowed_paths}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            touched = roots & set(PACK05_SERVICE_PACKAGES)
            if not touched:
                continue
            unauthorized_roots = touched - allowed_roots
            if unauthorized_roots:
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports unauthorized PACK-05 "
                    f"service(s) {sorted(unauthorized_roots)}"
                )
                continue
            module_paths = _imported_module_paths(py_file)
            for root in touched:
                touched_dotted = {p for p in module_paths if p == root or p.startswith(root + ".")}
                bad_paths = touched_dotted - allowed_paths
                if bad_paths:
                    root_allowed = sorted(p for p in allowed_paths if p.startswith(root))
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad_paths)} - "
                        f"only {root_allowed} is authorized for {package_name} (ADR-017)"
                    )
    assert violations == [], "Unauthorized PACK-03 -> PACK-05 imports found:\n" + "\n".join(
        violations
    )


def test_pack05_service_only_calls_upstream_applications_named_in_adr017() -> None:
    """ADR-017 Decision: `governance-service` may depend on an upstream
    PACK-03 service ONLY via that service's `.application` submodule,
    and only on the specific edges ADR-017 enumerates
    (`epd2_voting_service`/`epd2_tally_service`) - never
    `.storage`/`.domain`, and never a service not named for it (in
    particular, never `epd2_initiative_service`,
    `epd2_deliberation_service`, `epd2_moderation_service`, or
    `epd2_delegation_service`)."""
    violations: list[str] = []
    for package_name, src_dir in PACK05_SERVICE_PACKAGES.items():
        allowed_paths = ALLOWED_PACK05_TO_UPSTREAM_APPLICATION_MODULES[package_name]
        allowed_roots = {path.split(".")[0] for path in allowed_paths}
        forbidden_roots = set(PACK03_SERVICE_PACKAGES)
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            touched_forbidden_universe = roots & forbidden_roots
            if not touched_forbidden_universe:
                continue
            unauthorized_roots = touched_forbidden_universe - allowed_roots
            if unauthorized_roots:
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports unauthorized service(s) "
                    f"{sorted(unauthorized_roots)} (not an ADR-017 edge for {package_name})"
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
                        f"only {root_allowed} is authorized for {package_name} (ADR-017)"
                    )
    assert violations == [], "Unauthorized PACK-05 -> upstream imports found:\n" + "\n".join(
        violations
    )


def test_pack05_service_never_imports_excluded_services() -> None:
    """ADR-017's explicit exclusions, tested as positive assertions (not
    merely "unlisted") per that ADR's own instruction and this project's
    own requirement (no PACK-05 access to identity/account/eligibility/
    credential storage): `governance-service` must never import
    `epd2_account_service`, `epd2_identity_service`,
    `epd2_eligibility_service`, `epd2_credential_service`,
    `epd2_membership_service` (PACK-07: `governance-service` is read BY
    both `eligibility-service` and `membership-service`, never the other
    way around), `epd2_initiative_service`, `epd2_deliberation_service`,
    `epd2_moderation_service`, `epd2_delegation_service`, or
    `epd2_transparency_service`, under any module path."""
    excluded = frozenset(
        {
            "epd2_account_service",
            "epd2_identity_service",
            "epd2_eligibility_service",
            "epd2_credential_service",
            "epd2_membership_service",
            "epd2_initiative_service",
            "epd2_deliberation_service",
            "epd2_moderation_service",
            "epd2_delegation_service",
            "epd2_transparency_service",
        }
    )
    violations: list[str] = []
    for src_dir in PACK05_SERVICE_PACKAGES.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & excluded
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "ADR-017-excluded imports found in governance-service:\n" + "\n".join(
        violations
    )


def test_tally_service_never_imports_governance_service() -> None:
    """Explicit forbidden pair (`docs/review/PACK-05-OWNER-DECISIONS.md`):
    `tally-service` is read BY `governance-service`
    (`get_result_publication`), never the other way around -
    `tally-service` must never import `epd2_governance_service`."""
    src_dir = PACK03_SERVICE_PACKAGES["epd2_tally_service"]
    violations: list[str] = []
    for py_file in sorted(src_dir.rglob("*.py")):
        roots = _imported_roots(py_file)
        bad = roots & set(PACK05_SERVICE_PACKAGES)
        if bad:
            violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "tally-service must not import governance-service:\n" + "\n".join(
        violations
    )


def test_no_pack06_service_imports_another_pack06_services_package() -> None:
    """There is only one PACK-06 service today (ADR-021), so this is
    currently vacuous, but it is kept for symmetry with
    `test_no_pack05_service_imports_another_pack05_services_package` and
    to fail loudly if a second PACK-06 service is ever added without
    updating this file."""
    violations: list[str] = []
    for package_name, src_dir in PACK06_SERVICE_PACKAGES.items():
        forbidden = set(PACK06_SERVICE_PACKAGES) - {package_name}
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & forbidden
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "Forbidden PACK-06<->PACK-06 imports found:\n" + "\n".join(violations)


def test_no_other_service_imports_pack06_service() -> None:
    """ADR-021/ADR-022: the dependency direction is one-way -
    `ai-processing-service` reads from `governance-service` and
    `transparency-service`; no service anywhere in the repository
    (PACK-02 through PACK-05) may import it back. Nobody ever reads
    `AIProcessingRecord` via a Python import - only the resulting opaque
    `PublicLedgerEntry`, once published, is externally visible."""
    violations: list[str] = []
    other_packages = {
        **PACK02_SERVICE_PACKAGES,
        **PACK03_SERVICE_PACKAGES,
        **PACK04_SERVICE_PACKAGES,
        **PACK05_SERVICE_PACKAGES,
    }
    for src_dir in other_packages.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK06_SERVICE_PACKAGES)
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "No other service may import a PACK-06 service:\n" + "\n".join(
        violations
    )


def test_pack06_service_only_calls_upstream_applications_named_in_adr022_and_adr025() -> None:
    """ADR-022/ADR-025 §5 Decision: `ai-processing-service` may depend on
    an upstream service ONLY via that service's `.application` submodule,
    and only on the specific edges these ADRs enumerate
    (`epd2_governance_service`/`epd2_transparency_service`) - never
    `.storage`/`.domain`, and never a service not named for it (in
    particular, never any PACK-02 identity/account/eligibility/
    credential service, `epd2_initiative_service`,
    `epd2_deliberation_service`, `epd2_moderation_service`,
    `epd2_voting_service`, `epd2_tally_service`, or
    `epd2_delegation_service`)."""
    violations: list[str] = []
    allowed_paths = (
        ALLOWED_PACK06_TO_PACK05_APPLICATION_MODULES["epd2_ai_processing_service"]
        | ALLOWED_PACK06_TO_PACK04_APPLICATION_MODULES["epd2_ai_processing_service"]
    )
    allowed_roots = {path.split(".")[0] for path in allowed_paths}
    forbidden_roots = (
        set(PACK02_SERVICE_PACKAGES)
        | set(PACK03_SERVICE_PACKAGES)
        | set(PACK05_SERVICE_PACKAGES)
        | set(PACK04_SERVICE_PACKAGES)
    ) - {"epd2_audit_core"}
    src_dir = PACK06_SERVICE_PACKAGES["epd2_ai_processing_service"]
    for py_file in sorted(src_dir.rglob("*.py")):
        roots = _imported_roots(py_file)
        touched_forbidden_universe = roots & forbidden_roots
        if not touched_forbidden_universe:
            continue
        unauthorized_roots = touched_forbidden_universe - allowed_roots
        if unauthorized_roots:
            violations.append(
                f"{py_file.relative_to(REPO_ROOT)} imports unauthorized service(s) "
                f"{sorted(unauthorized_roots)} (not an ADR-022/ADR-025 edge)"
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
                    f"only {root_allowed} is authorized for epd2_ai_processing_service "
                    "(ADR-022/ADR-025)"
                )
    assert violations == [], "Unauthorized PACK-06 -> upstream imports found:\n" + "\n".join(
        violations
    )


def test_pack06_service_never_imports_excluded_services() -> None:
    """ADR-022's explicit exclusions, tested as positive assertions (not
    merely "unlisted") per this project's own convention: `ai-processing-
    service` must never import any PACK-02 identity/account/eligibility/
    credential service, `epd2_initiative_service`,
    `epd2_deliberation_service`, `epd2_moderation_service`,
    `epd2_voting_service`, `epd2_tally_service`, or
    `epd2_delegation_service` - no identity/account/credential/voting/
    tally/moderation storage access anywhere (required scope item 16)."""
    excluded = frozenset(
        {
            "epd2_account_service",
            "epd2_identity_service",
            "epd2_eligibility_service",
            "epd2_credential_service",
            "epd2_initiative_service",
            "epd2_deliberation_service",
            "epd2_moderation_service",
            "epd2_voting_service",
            "epd2_tally_service",
            "epd2_delegation_service",
        }
    )
    violations: list[str] = []
    for src_dir in PACK06_SERVICE_PACKAGES.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & excluded
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], (
        "ADR-022-excluded imports found in ai-processing-service:\n" + "\n".join(violations)
    )


def test_pack06_to_pack05_edge_imports_only_verify_role_assignment_for_action() -> None:
    """ADR-022's own stated aspiration, now enforced: the single strictest
    entry in this whole matrix - `ai-processing-service` may import
    exactly one name, `verify_role_assignment_for_action`, from
    `epd2_governance_service.application`. Never `get_role_assignment`,
    never `.domain` (`RoleAssignment`/`RoleAssignmentStatus`/
    `scope_covers`/`GLOBAL_SCOPE_ID`), never any policy/decision/
    technical-challenge command."""
    src_dir = PACK06_SERVICE_PACKAGES["epd2_ai_processing_service"]
    violations: list[str] = []
    for py_file in sorted(src_dir.rglob("*.py")):
        imported_names = _imported_names_from_module(py_file, "epd2_governance_service.application")
        unauthorized = imported_names - ALLOWED_PACK06_GOVERNANCE_FUNCTIONS
        if unauthorized:
            violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(unauthorized)}")
    assert violations == [], (
        "Unauthorized epd2_governance_service.application imports found (ADR-022 requires "
        "exactly verify_role_assignment_for_action):\n" + "\n".join(violations)
    )


def test_pack06_to_pack04_edge_imports_only_publish_ledger_entry() -> None:
    """ADR-025 §5: `ai-processing-service` may import exactly one name,
    `publish_ledger_entry`, from `epd2_transparency_service.application`
    - never `correct_ledger_entry`, `define_disclosure_policy`,
    `activate_disclosure_policy`, or any other function; never `.domain`
    (`LedgerSubjectType` is resolved by the caller and passed through as
    an opaque `subject_type` parameter - see `application.
    publish_ai_disclosure`'s own docstring)."""
    src_dir = PACK06_SERVICE_PACKAGES["epd2_ai_processing_service"]
    violations: list[str] = []
    for py_file in sorted(src_dir.rglob("*.py")):
        imported_names = _imported_names_from_module(
            py_file, "epd2_transparency_service.application"
        )
        unauthorized = imported_names - ALLOWED_PACK06_TRANSPARENCY_FUNCTIONS
        if unauthorized:
            violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(unauthorized)}")
    assert violations == [], (
        "Unauthorized epd2_transparency_service.application imports found (ADR-025 §5 requires "
        "exactly publish_ledger_entry):\n" + "\n".join(violations)
    )


# =============================================================================
# PACK-07 (canon-0.6.0, ADR-026 through ADR-031) cross-service edges.
# =============================================================================


def test_eligibility_service_pack07_edges_are_application_only_and_match_adr027() -> None:
    """ADR-027 Decision: `eligibility-service` may depend on
    `identity-service`/`membership-service`/`credential-service`/
    `governance-service` ONLY via their `.application` submodule, and
    only for the four edges ADR-027 enumerates - never `.storage`/
    `.domain` (INV-03), and never `epd2_account_service` (not named by
    ADR-027 at all - still fully excluded by the blanket PACK-02 test
    above)."""
    violations: list[str] = []
    src_dir = PACK02_SERVICE_PACKAGES["epd2_eligibility_service"]
    touched_roots_universe = {
        "epd2_identity_service",
        "epd2_membership_service",
        "epd2_credential_service",
        "epd2_governance_service",
    }
    allowed_roots = {p.split(".")[0] for p in ALLOWED_ELIGIBILITY_PACK07_APPLICATION_MODULES}
    for py_file in sorted(src_dir.rglob("*.py")):
        roots = _imported_roots(py_file)
        touched = roots & touched_roots_universe
        if not touched:
            continue
        unauthorized_roots = touched - allowed_roots
        if unauthorized_roots:
            violations.append(
                f"{py_file.relative_to(REPO_ROOT)} imports unauthorized service(s) "
                f"{sorted(unauthorized_roots)} (not an ADR-027 edge)"
            )
            continue
        module_paths = _imported_module_paths(py_file)
        for root in touched:
            touched_dotted = {p for p in module_paths if p == root or p.startswith(root + ".")}
            bad_paths = touched_dotted - ALLOWED_ELIGIBILITY_PACK07_APPLICATION_MODULES
            if bad_paths:
                root_allowed = sorted(
                    p for p in ALLOWED_ELIGIBILITY_PACK07_APPLICATION_MODULES if p.startswith(root)
                )
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad_paths)} - "
                    f"only {root_allowed} is authorized for epd2_eligibility_service (ADR-027)"
                )
    assert violations == [], "Unauthorized eligibility-service PACK-07 imports found:\n" + (
        "\n".join(violations)
    )


def test_membership_service_edges_are_application_only_and_match_adr027() -> None:
    """ADR-027 Decision: `membership-service` (PACK-07's one new service)
    may depend on `identity-service`/`eligibility-service`/
    `governance-service` ONLY via their `.application` submodule, and
    only for the three edges ADR-027 enumerates - never `.storage`/
    `.domain`, and never any other service (in particular, never
    `epd2_account_service`, `epd2_credential_service`, or
    `epd2_moderation_service` - its own `Appeal` is a documented
    duplicate, never an import)."""
    violations: list[str] = []
    src_dir = PACK07_SERVICE_PACKAGES["epd2_membership_service"]
    allowed_roots = {p.split(".")[0] for p in ALLOWED_MEMBERSHIP_APPLICATION_MODULES}
    forbidden_roots = (set(SERVICE_PACKAGES) - {"epd2_membership_service", "epd2_audit_core"}) | (
        allowed_roots
    )
    for py_file in sorted(src_dir.rglob("*.py")):
        roots = _imported_roots(py_file)
        touched = roots & forbidden_roots
        if not touched:
            continue
        unauthorized_roots = touched - allowed_roots
        if unauthorized_roots:
            violations.append(
                f"{py_file.relative_to(REPO_ROOT)} imports unauthorized service(s) "
                f"{sorted(unauthorized_roots)} (not an ADR-027 edge)"
            )
            continue
        module_paths = _imported_module_paths(py_file)
        for root in touched:
            touched_dotted = {p for p in module_paths if p == root or p.startswith(root + ".")}
            bad_paths = touched_dotted - ALLOWED_MEMBERSHIP_APPLICATION_MODULES
            if bad_paths:
                root_allowed = sorted(
                    p for p in ALLOWED_MEMBERSHIP_APPLICATION_MODULES if p.startswith(root)
                )
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad_paths)} - "
                    f"only {root_allowed} is authorized for epd2_membership_service (ADR-027)"
                )
    assert violations == [], "Unauthorized membership-service imports found:\n" + "\n".join(
        violations
    )


def test_no_other_service_imports_membership_service() -> None:
    """ADR-027's dependency direction: `membership-service` reads from
    `identity-service`/`eligibility-service`/`governance-service`; none
    of those, and no other service anywhere in the repository, may
    import it back. `eligibility-service`'s own read of
    `epd2_membership_service.application.get_membership_derived_claims`
    is the one, single, explicitly-authorized exception (checked
    precisely, application-only, in
    `test_eligibility_service_pack07_edges_are_application_only_and_match_adr027`
    above)."""
    violations: list[str] = []
    other_packages = {
        name: path
        for name, path in SERVICE_PACKAGES.items()
        if name not in {"epd2_membership_service", "epd2_eligibility_service"}
    }
    for src_dir in other_packages.values():
        for py_file in sorted(src_dir.rglob("*.py")):
            roots = _imported_roots(py_file)
            bad = roots & set(PACK07_SERVICE_PACKAGES)
            if bad:
                violations.append(f"{py_file.relative_to(REPO_ROOT)} imports {sorted(bad)}")
    assert violations == [], "No other service may import membership-service:\n" + "\n".join(
        violations
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
