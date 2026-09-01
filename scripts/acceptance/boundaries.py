"""Ingress/gateway/infrastructure non-ownership (INFRA01-HI-11).

Structural fail-closed checks preserving ``FIR-EDGE-001`` and
``FIR-API-001``: CI, ingress, gateway and BFF infrastructure may route and
enforce technical policy, but must never own domain truth, business
decisions, domain authorization semantics, voting semantics, publication
decisions or legal-effect decisions.

Two mechanical rules are enforced here:

1. Harness/infrastructure Python code (``scripts/``, including this package)
   must not import any domain service implementation module. Verification
   *commands* may run domain test suites as subprocesses — that is
   execution, not ownership — but infrastructure code that imports domain
   modules is a structural step toward migrating domain logic into
   infrastructure and is refused.
2. GitHub workflow definitions must not embed domain decision logic: they
   may prepare environments and invoke governed repository entry points, but
   markers of domain semantics (tally computation, eligibility decisions,
   vote handling, publication approval) inside workflow ``run`` scripts are
   refused.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.acceptance import codes

#: Import prefixes that constitute domain implementation surface.
DOMAIN_IMPORT_PREFIXES = (
    "epd2_account_service",
    "epd2_ai_processing_service",
    "epd2_audit_core",
    "epd2_compliance_service",
    "epd2_credential_service",
    "epd2_data_plane_service",
    "epd2_delegation_service",
    "epd2_deliberation_service",
    "epd2_document_service",
    "epd2_eligibility_service",
    "epd2_finance_service",
    "epd2_governance_service",
    "epd2_identity_service",
    "epd2_initiative_service",
    "epd2_membership_service",
    "epd2_moderation_service",
    "epd2_organization_service",
    "epd2_privileged_access_service",
    "epd2_tally_service",
    "epd2_transparency_service",
    "epd2_voting_service",
)

#: Domain-decision markers that must never appear in workflow run scripts.
_WORKFLOW_DOMAIN_MARKERS = (
    re.compile(r"(?i)\btally\s*(=|\+=)"),
    re.compile(r"(?i)\bcount_votes?\b"),
    re.compile(r"(?i)\bdecide_eligibility\b"),
    re.compile(r"(?i)\bapprove_publication\b"),
    re.compile(r"(?i)\blegal_effect\b"),
)


@dataclass(frozen=True)
class BoundaryFinding:
    code: str
    path: str
    detail: str


def _imported_names(source: str, path: str) -> list[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def check_infrastructure_imports(
    root: Path, infra_dirs: tuple[str, ...] = ("scripts",)
) -> list[BoundaryFinding]:
    findings: list[BoundaryFinding] = []
    for infra_dir in infra_dirs:
        base = root / infra_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            for name in _imported_names(path.read_text(encoding="utf-8"), rel):
                if name.startswith(DOMAIN_IMPORT_PREFIXES):
                    findings.append(
                        BoundaryFinding(
                            codes.DOMAIN_LOGIC_IN_INFRASTRUCTURE,
                            rel,
                            f"infrastructure code imports domain module {name!r}",
                        )
                    )
    return findings


def check_workflow_scripts(root: Path) -> list[BoundaryFinding]:
    findings: list[BoundaryFinding] = []
    workflows = root / ".github/workflows"
    if not workflows.is_dir():
        return findings
    for path in sorted(workflows.glob("*.yml")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for marker in _WORKFLOW_DOMAIN_MARKERS:
            match = marker.search(text)
            if match:
                findings.append(
                    BoundaryFinding(
                        codes.DOMAIN_LOGIC_IN_INFRASTRUCTURE,
                        rel,
                        f"workflow embeds domain-decision marker {match.group(0)!r}",
                    )
                )
    return findings


def check_boundaries(root: Path) -> list[BoundaryFinding]:
    return check_infrastructure_imports(root) + check_workflow_scripts(root)
