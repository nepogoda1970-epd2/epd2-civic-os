#!/usr/bin/env python3
"""SYSTEM TRIAL PREVIEW — preparation harness.

Status: `PREPARATION_ONLY / CHECKPOINT_NOT_OPEN`.

The canonical preview may open only after authoritative API-06 acceptance, API
layer closure and a recorded INFRA/OPS preview-readiness minimum. None of those
exist yet, so this script prepares the harness and states today's truth: every
journey's *current* classification is bounded by what the accepted baseline
actually supports, and a separate target classification records what the journey
is expected to become once the checkpoint opens.

Two invariants are enforced mechanically, not promised:

* no journey may be classified `SUPPORTED_REAL_PATH` today while the checkpoint
  is closed;
* no journey backed only by a mock may be classified as supported in either
  column.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "validation" / "system_trial_preview"

CHECKPOINT_STATE = "CHECKPOINT_NOT_OPEN"

CLASSIFICATIONS = (
    "SUPPORTED_REAL_PATH",
    "SUPPORTED_WITH_DECLARED_LIMITATION",
    "UNSUPPORTED_FOR_TRIAL",
    "BLOCKED_BY_DEPENDENCY",
)

BLOCKERS = {
    "API-06": "API-06 has no authoritative acceptance; the API layer is not closed.",
    "API-05": "API-05 C1 is ACCEPTED / CLOSED; not a current checkpoint blocker.",
    "INFRA-02": "INFRA-02 is ACCEPTED / CLOSED; joint preview remains governed.",
    "OPS-02": ("OPS-02 C3 is ACCEPTED / CLOSED; joint preview remains separately governed."),
    "CTRL-01": "CTRL-01 is preseal and not accepted; control surfaces are specification-level.",
    "VOTING-LAW": (
        "Non-binding voting exposure requires a separate lawful and technical authorization."
    ),
}


@dataclass(slots=True)
class Journey:
    journey_id: str
    category: str
    persona: str
    preconditions: tuple[str, ...]
    dependencies: tuple[str, ...]
    browser_steps: tuple[str, ...]
    runtime_paths: tuple[str, ...]
    expected_result: str
    expected_evidence: str
    owning_layer: str
    classification_today: str
    classification_target: str
    blocking_dependencies: tuple[str, ...] = ()
    limitation: str = ""
    mock_backed: bool = False

    @property
    def is_mock_backed(self) -> bool:
        """Derived from the declared runtime paths, not hand-set.

        A flag nobody ever sets to true cannot enforce "never mark a mock-only
        path as supported"; reading the journey's own declared paths can.
        """
        haystack = " ".join(self.runtime_paths).lower()
        return self.mock_backed or any(
            token in haystack for token in ("mock", "stub", "simulated", "fake", "placeholder")
        )

    def to_obj(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "category": self.category,
            "persona": self.persona,
            "preconditions": list(self.preconditions),
            "dependencies": list(self.dependencies),
            "browser_steps": list(self.browser_steps),
            "api_runtime_paths": list(self.runtime_paths),
            "expected_result": self.expected_result,
            "expected_audit_evidence": self.expected_evidence,
            "owning_layer_for_defects": self.owning_layer,
            "status_today": self.classification_today,
            "status_target_at_checkpoint": self.classification_target,
            "blocking_dependencies": [
                {"dependency": d, "reason": BLOCKERS.get(d, "unrecorded dependency")}
                for d in self.blocking_dependencies
            ],
            "declared_limitation": self.limitation,
            "mock_backed": self.is_mock_backed,
        }


def _j(*args: Any, **kwargs: Any) -> Journey:
    return Journey(*args, **kwargs)


JOURNEYS: tuple[Journey, ...] = (
    # -- public anonymous ---------------------------------------------------
    _j(
        "J-PUB-01",
        "public_anonymous",
        "anonymous visitor",
        ("preview environment deployed", "public content seeded"),
        ("FRONT-02 C2.1", "INFRA preview minimum"),
        (
            "open the preview base URL",
            "navigate the public information architecture",
            "open one public page",
        ),
        ("GET public page routes served by the accepted FRONT-02 shell",),
        "public pages render, are navigable and state that this is a trial environment",
        "web/access log only; no personal data",
        "FRONT",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
        limitation="Content is trial seed content and is labelled as such.",
    ),
    _j(
        "J-PUB-02",
        "public_anonymous",
        "anonymous visitor",
        ("preview environment deployed",),
        ("FRONT-02 C2.1",),
        ("open a page that does not exist", "open a page requiring authentication"),
        ("404 and 401/403 responses from the accepted route set",),
        "a non-misleading refusal page; no partial private content is rendered",
        "refusal is logged with a reason code and no subject identifier",
        "FRONT",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
    ),
    _j(
        "J-PUB-03",
        "public_anonymous",
        "anonymous visitor",
        ("preview environment deployed",),
        ("FRONT-00 accessibility baseline",),
        ("navigate by keyboard only", "run the accessibility check on two public pages"),
        ("static route rendering",),
        "keyboard navigation and the accepted accessibility baseline hold",
        "no evidence beyond the trial observation record",
        "FRONT",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("INFRA-02",),
        limitation="Only the accepted FRONT-02 page set is in scope.",
    ),
    # -- authentication / session ------------------------------------------
    _j(
        "J-AUTH-01",
        "authentication_session",
        "trial member with a seeded account",
        ("test account fixture provisioned", "authenticator enrolled"),
        ("API-02 C13", "INFRA preview minimum"),
        (
            "open the sign-in page",
            "authenticate with the seeded factor",
            "land on the member home surface",
        ),
        ("accepted API-02 authentication and session issuance runtime",),
        "an authenticated session is established at the expected assurance level",
        "authentication context event; no credential material",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
    ),
    _j(
        "J-AUTH-02",
        "authentication_session",
        "trial member",
        ("authenticated session exists",),
        ("API-02 C13",),
        ("sign out", "attempt to reuse the previous session by navigating back"),
        ("session revocation and re-validation on the accepted runtime",),
        "the revoked session is refused; the back-navigation does not restore access",
        "session state change recorded",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
    ),
    _j(
        "J-AUTH-03",
        "authentication_session",
        "trial member",
        ("authenticated session exists", "operator quarantines the session"),
        ("API-02 C13", "CTRL-01 session quarantine surface"),
        ("keep a browser tab open", "operator quarantines the session", "act in the open tab"),
        ("session state re-evaluation at use time",),
        "the open tab is refused at the next consequential act",
        "reason-coded refusal evidence",
        "CTRL",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("CTRL-01", "INFRA-02"),
        limitation=(
            "Quarantine is issued through a CTRL-01 specification-level surface until CTRL-01 is "
            "accepted."
        ),
    ),
    _j(
        "J-AUTH-04",
        "authentication_session",
        "trial member without an enrolled factor",
        ("account fixture without an authenticator",),
        ("API-02 C13",),
        ("attempt sign-in", "start the governed recovery intake"),
        ("recovery workflow entry on the accepted runtime",),
        "recovery is offered as a governed workflow, never as an administrator override",
        "recovery request evidence, separately protected",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("INFRA-02", "OPS-02"),
        limitation=(
            "High-assurance recovery approval requires a second human and is exercised as a "
            "scripted step."
        ),
    ),
    # -- applicant / member -------------------------------------------------
    _j(
        "J-MEM-01",
        "applicant_member",
        "prospective member",
        ("preview environment deployed", "application intake seeded"),
        ("PILOT-02 lineage", "API-02 C13"),
        ("open the membership application", "complete and submit it", "view the submitted state"),
        ("membership application intake on the accepted runtime",),
        "the application is recorded in a pending state with a visible status",
        "application state event without excess personal data",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02", "OPS-02"),
        limitation="Only trial fixtures are used; no real applicant data enters the preview.",
    ),
    _j(
        "J-MEM-02",
        "applicant_member",
        "trial member",
        ("authenticated session exists",),
        ("PILOT-02 lineage",),
        (
            "open the member profile",
            "change a permitted profile field",
            "verify the change is shown",
        ),
        ("member self-service mutation on the accepted runtime",),
        "the change is applied within the member's own scope only",
        "self-service change evidence",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Field set limited to the accepted self-service surface.",
    ),
    _j(
        "J-MEM-03",
        "applicant_member",
        "trial member of Land A",
        ("two seeded Länder", "authenticated session in Land A"),
        ("API-02 C13", "organization scope model"),
        ("attempt to open a Land B administrative surface by direct URL",),
        ("scope authorization on the accepted runtime",),
        "refusal; no Land B content is rendered or leaked in the response",
        "reason-coded scope refusal evidence",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
    ),
    # -- participation / application ---------------------------------------
    _j(
        "J-PART-01",
        "participation",
        "trial member",
        ("authenticated session exists", "an open initiative is seeded"),
        ("PILOT-03 lineage",),
        ("open the initiative list", "open one initiative", "submit a contribution"),
        ("initiative and deliberation runtime",),
        "the contribution is recorded and visible in the correct scope",
        "contribution status event",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Moderation and AI-assisted paths are out of trial scope.",
    ),
    _j(
        "J-PART-02",
        "participation",
        "trial member",
        ("authenticated session exists", "a seeded assembly with an agenda"),
        ("PILOT-03 lineage",),
        ("open the assembly", "read the agenda and a motion", "read published minutes"),
        ("assembly and motion read surfaces",),
        "assembly material is readable within scope",
        "read access evidence per existing rules",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Live assembly conduct is not exercised.",
    ),
    # -- organization / regional views -------------------------------------
    _j(
        "J-ORG-01",
        "organization_regional",
        "trial member",
        ("authenticated session exists", "organization graph seeded"),
        ("organization service", "FRONT-02 regional operating model"),
        ("open the organization overview", "navigate Bund -> Land -> Kreis -> Ort"),
        ("organization graph read model",),
        "the hierarchy is displayed without implying inherited administrative authority",
        "read access evidence",
        "FRONT",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Display must not present a generic regional admin role.",
    ),
    _j(
        "J-ORG-02",
        "organization_regional",
        "regional office holder",
        ("authenticated session exists", "an OrganizationalAuthority is seeded"),
        ("CTRL-01 authority read model", "API-02 C13"),
        ("open the authority provenance view", "inspect rule version and source decision"),
        ("authority provenance read model",),
        "office, scope, rule version and source decision are all shown",
        "provenance read evidence",
        "CTRL",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("CTRL-01", "INFRA-02"),
        limitation="Served by the CTRL-01 read model, which is preseal and not accepted.",
    ),
    # -- representative / transparency -------------------------------------
    _j(
        "J-REP-01",
        "representative_transparency",
        "anonymous visitor",
        ("preview environment deployed", "representative desk fixtures seeded"),
        ("PILOT-05 C3",),
        ("open the representative desk", "open one published transparency item"),
        ("transparency publication read surfaces",),
        "published items are readable and clearly marked as trial content",
        "publication read evidence",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Only seeded transparency fixtures are published.",
    ),
    _j(
        "J-REP-02",
        "representative_transparency",
        "citizen",
        ("preview environment deployed",),
        ("PILOT-05 C3",),
        ("submit a citizen-office enquiry", "observe the routing acknowledgement"),
        ("citizen office intake and routing",),
        "the enquiry is acknowledged and routed to the correct scope",
        "case routing evidence without case content in generic logs",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("API-06", "INFRA-02"),
        limitation="Trial personas only; no real casework enters the preview.",
    ),
    # -- voting boundary ----------------------------------------------------
    _j(
        "J-VOTE-01",
        "voting_boundary",
        "trial member",
        ("authenticated session exists",),
        ("PILOT-04 C9", "voting isolation profile"),
        ("open the member surface", "observe that no voting-client control surface is reachable"),
        ("route set exclusion; no voting-domain route is served from an administrative surface",),
        "the Voting Client is unreachable from every administrative and member control surface",
        "no voting-linkable identifier appears in any control or trial log",
        "CTRL",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        "SUPPORTED_REAL_PATH",
        (),
        limitation=(
            "Provable today as a negative property against the CTRL-01 inventory and route set; "
            "the full end-to-end proof needs the deployed preview."
        ),
    ),
    _j(
        "J-VOTE-02",
        "voting_boundary",
        "trial member",
        ("a lawful non-binding trial vote is separately authorized",),
        ("PILOT-04 C9", "FRONT-04 C2 voting client", "separate legal authorization"),
        ("open the non-binding trial ballot", "cast a trial ballot", "verify the receipt"),
        ("voting client and non-binding tally path",),
        "a non-binding trial vote completes with unlinkability preserved",
        "voting-domain evidence only, under voting-domain rules",
        "PILOT",
        "UNSUPPORTED_FOR_TRIAL",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("VOTING-LAW", "API-06", "INFRA-02", "OPS-02"),
        limitation=(
            "Excluded until a separate lawful and technical authorization exists. It is not "
            "simulated: an unavailable voting path is shown as unavailable, never mocked."
        ),
    ),
    # -- refusal / permission-denied states --------------------------------
    _j(
        "J-REF-01",
        "refusal_states",
        "trial member without the required authority",
        ("authenticated session exists",),
        ("API-02 C13", "CTRL-01 negative suite"),
        ("navigate directly to an administrative route", "observe the refusal"),
        ("server-side authorization refusal",),
        "a clear, non-leaking refusal; frontend visibility never substitutes for authorization",
        "reason-coded refusal evidence",
        "API",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("INFRA-02", "OPS-02"),
    ),
    _j(
        "J-REF-02",
        "refusal_states",
        "trial member whose authority expired",
        ("authenticated session exists", "authority validity window ended"),
        ("CTRL-01 commit-time reauthorization",),
        ("begin a workflow while authorized", "complete it after expiry"),
        ("commit-time reauthorization refusal",),
        "the commit is refused even though the workflow started while authorized",
        "commit-time refusal evidence",
        "CTRL",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("CTRL-01", "INFRA-02"),
        limitation="Exercised against the CTRL-01 preseal runtime.",
    ),
    # -- degraded dependency states ----------------------------------------
    _j(
        "J-DEG-01",
        "degraded_dependency",
        "trial member",
        ("preview environment deployed", "one backing service stopped"),
        ("OPS preview minimum",),
        ("stop a dependency", "attempt an affected journey", "observe the degraded state"),
        ("health/readiness endpoints and fail-closed behaviour",),
        "the surface degrades safely and states the limitation; it does not fail open",
        "operational event without personal data",
        "OPS",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("OPS-02", "INFRA-02"),
    ),
    _j(
        "J-DEG-02",
        "degraded_dependency",
        "trial member",
        ("preview environment deployed", "database unavailable"),
        ("OPS preview minimum",),
        ("stop the database", "attempt a read and a write journey"),
        ("fail-closed persistence behaviour",),
        "reads and writes fail closed with an honest message; no stale write is accepted",
        "operational event",
        "OPS",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("OPS-02", "INFRA-02"),
    ),
    # -- recovery / reset ---------------------------------------------------
    _j(
        "J-RST-01",
        "recovery_reset",
        "trial operator",
        ("preview environment deployed", "fixture version recorded"),
        ("OPS preview minimum", "seed and reset design"),
        ("run the documented reset", "re-verify the fixture digest", "re-run one smoke journey"),
        ("reset tooling and fixture loader",),
        "the environment returns to the exact recorded fixture version",
        "reset evidence including the fixture digest before and after",
        "OPS",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("OPS-02",),
    ),
    _j(
        "J-RST-02",
        "recovery_reset",
        "trial operator",
        ("preview environment deployed", "a backup exists"),
        ("OPS preview minimum",),
        ("restore from backup", "verify integrity", "confirm no production data is present"),
        ("backup and restore tooling",),
        "restore completes and the environment is provably free of production data",
        "restore evidence",
        "OPS",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("OPS-02",),
    ),
    # -- control-plane observation -----------------------------------------
    _j(
        "J-CTRL-01",
        "control_plane",
        "independent auditor",
        ("authenticated session exists", "auditor authority seeded"),
        ("CTRL-01 audit read model",),
        ("open the audit lookup", "inspect one executed act and one refusal"),
        ("immutable audit read path",),
        "both the act and the refusal are visible with reason codes and authority basis",
        "read access evidence; the auditor holds no mutation right",
        "CTRL",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_WITH_DECLARED_LIMITATION",
        ("CTRL-01", "INFRA-02"),
        limitation="CTRL-01 is preseal; the surface is specification-level until accepted.",
    ),
    _j(
        "J-CTRL-02",
        "control_plane",
        "trial operator",
        ("preview environment deployed",),
        ("OPS preview minimum", "FIR-OPS-001"),
        ("open the operational health view", "confirm no personal data is displayed"),
        ("privacy-safe health and readiness endpoints",),
        "health state is visible and carries no personal or voting-linkable data",
        "no evidence beyond the operational event",
        "OPS",
        "BLOCKED_BY_DEPENDENCY",
        "SUPPORTED_REAL_PATH",
        ("OPS-02",),
    ),
)


ENVIRONMENT_READINESS: dict[str, list[dict[str, Any]]] = {
    "services": [
        {
            "item": "identity/authentication runtime",
            "source": "accepted API-02 C13",
            "state": "NOT_DEPLOYED",
        },
        {
            "item": "service-to-service trust runtime",
            "source": "accepted API-03 C5",
            "state": "NOT_DEPLOYED",
        },
        {
            "item": "events and messaging runtime",
            "source": "accepted API-04 C1",
            "state": "NOT_DEPLOYED",
        },
        {"item": "remaining API surface", "source": "API-06", "state": "NEXT_NOT_ACCEPTED"},
        {
            "item": "web shell",
            "source": "accepted FRONT-02 C2.1 / FRONT-03 C1",
            "state": "NOT_DEPLOYED",
        },
    ],
    "databases": [
        {
            "item": "PostgreSQL 16.15",
            "source": "accepted acceptance evidence baseline",
            "state": "NOT_PROVISIONED",
        },
        {
            "item": "identity-side / voting-side / neutral audit streams",
            "source": "audit-core migrations",
            "state": "NOT_PROVISIONED",
        },
    ],
    "trust_material": [
        {
            "item": "preview-only TLS and mTLS material",
            "source": "INFRA preview minimum",
            "state": "NOT_ISSUED",
            "note": "Preview trust material must be distinct from any production trust chain.",
        },
        {
            "item": "voting-domain trust material",
            "source": "voting domain",
            "state": "OUT_OF_SCOPE",
            "note": "Never provisioned by the preview harness.",
        },
    ],
    "network_boundaries": [
        {
            "item": "voting-domain network isolation",
            "source": "FIR-VOTE-NET-001",
            "state": "REQUIRED_NOT_VERIFIED",
        },
        {
            "item": "administrative surface origin separation",
            "source": "FIR-CTRL-001",
            "state": "REQUIRED_NOT_VERIFIED",
        },
    ],
    "health_readiness": [
        {
            "item": "per-service readiness endpoint",
            "source": "OPS preview minimum",
            "state": "REQUIRED_NOT_VERIFIED",
        },
        {
            "item": "aggregate environment health view",
            "source": "FIR-OPS-001",
            "state": "REQUIRED_NOT_VERIFIED",
        },
    ],
    "observability": [
        {
            "item": "privacy-safe log pipeline",
            "source": "FIR-OPS-001",
            "state": "REQUIRED_NOT_VERIFIED",
            "note": "No voting-linkable identifier may reach observability.",
        },
    ],
    "backup_reset": [
        {
            "item": "deterministic fixture loader",
            "source": "this harness",
            "state": "DESIGNED_NOT_IMPLEMENTED",
        },
        {
            "item": "one-command environment reset",
            "source": "OPS preview minimum",
            "state": "REQUIRED_NOT_VERIFIED",
        },
    ],
    "operator_runbooks": [
        {
            "item": "start / stop / reset runbook",
            "source": "accepted OPS-01 C2 conventions",
            "state": "REQUIRED_NOT_WRITTEN",
        },
        {
            "item": "incident and stop-condition runbook",
            "source": "accepted OPS-01 C2 conventions",
            "state": "REQUIRED_NOT_WRITTEN",
        },
    ],
    "seed_data": [
        {
            "item": "deterministic trial fixture set",
            "source": "this harness",
            "state": "DESIGNED_NOT_IMPLEMENTED",
        },
    ],
    "test_accounts": [
        {
            "item": "trial personas with synthetic credentials",
            "source": "this harness",
            "state": "DESIGNED_NOT_IMPLEMENTED",
            "note": "No real personal secrets, ever.",
        },
    ],
    "voting_isolation_controls": [
        {
            "item": "voting client excluded from all administrative surfaces",
            "source": "CTRL-01 inventory",
            "state": "SPECIFIED_AND_TESTED_AT_PRESEAL",
        },
        {
            "item": "no voting-linkable identifier in trial logs",
            "source": "CTRL-01 privacy screen",
            "state": "SPECIFIED_AND_TESTED_AT_PRESEAL",
        },
    ],
}


SEED_AND_RESET: dict[str, Any] = {
    "principles": [
        "no real personal data and no real personal secrets enter the preview",
        "fixtures are deterministic and reproducible from a recorded version and digest",
        "every fixture load is reversible by the documented reset",
        "production data is excluded by construction, not by policy statement",
    ],
    "fixture_version": "CTRL01-STP-FIXTURES-0.1",
    "fixture_digest": "TO_BE_COMPUTED_AT_FIXTURE_BUILD",
    "production_data_exclusion": {
        "rule": (
            "the preview environment has no credential, network path or trust material that "
            "reaches production"
        ),
        "verification": (
            "environment readiness matrix rows 'trust_material' and 'network_boundaries' "
            "must be verified before the checkpoint opens"
        ),
    },
    "organizations": [
        {"scope": "BUND:trial-bund", "note": "one Bundesverband"},
        {"scope": "LAND:trial-land-a", "note": "used for in-scope journeys"},
        {"scope": "LAND:trial-land-b", "note": "used to prove cross-Land refusal"},
        {"scope": "KREIS:trial-kreis-a1", "note": "child of Land A"},
        {"scope": "ORT:trial-ort-a1a", "note": "child of Kreis A1"},
    ],
    "personas": [
        {"persona": "anonymous visitor", "credentials": "none"},
        {"persona": "trial member (Land A)", "credentials": "synthetic authenticator"},
        {"persona": "trial member (Land B)", "credentials": "synthetic authenticator"},
        {"persona": "prospective member", "credentials": "none until application"},
        {
            "persona": "regional office holder (Land A)",
            "credentials": "synthetic authenticator + seeded authority",
        },
        {
            "persona": "independent auditor",
            "credentials": "synthetic authenticator + read-only authority",
        },
        {
            "persona": "trial operator",
            "credentials": "synthetic operator account, platform scope only",
        },
    ],
    "application_states": ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "DECIDED"],
    "reset": {
        "mode": "full deterministic reset to the recorded fixture version",
        "steps": [
            "stop trial traffic",
            "drop and recreate the trial schemas",
            "load the fixture set for the recorded version",
            "recompute and compare the fixture digest",
            "run the smoke journey set",
            "record reset evidence including before/after digests",
        ],
        "reversibility": "every reset returns the environment to the same recorded digest",
    },
}


FAILURE_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "scenario_id": "F-01",
        "name": "service unavailable",
        "trigger": "stop one backing service",
        "expected": (
            "affected journeys fail closed with an honest degraded state; unaffected journeys "
            "continue"
        ),
        "owning_layer": "OPS",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-02",
        "name": "database unavailable",
        "trigger": "stop the database",
        "expected": "reads and writes fail closed; no partial write is acknowledged",
        "owning_layer": "OPS",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-03",
        "name": "session revoked mid-journey",
        "trigger": "revoke an active session",
        "expected": "the next consequential act is refused with a reason code",
        "owning_layer": "API",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-04",
        "name": "authority revoked mid-workflow",
        "trigger": "revoke an OrganizationalAuthority",
        "expected": "commit-time reauthorization refuses the commit",
        "owning_layer": "CTRL",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-05",
        "name": "time or expiry anomaly",
        "trigger": "advance a grant past its expiry",
        "expected": "the expired grant authorizes nothing and is not renewable in place",
        "owning_layer": "CTRL",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-06",
        "name": "partial dependency outage",
        "trigger": "degrade one dependency",
        "expected": "the surface states the limitation rather than silently omitting data",
        "owning_layer": "OPS",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-07",
        "name": "operator recovery",
        "trigger": "follow the recovery runbook after F-01",
        "expected": "the environment returns to a known-good state within the recorded target",
        "owning_layer": "OPS",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-08",
        "name": "rollback and reset",
        "trigger": "run the documented reset",
        "expected": "the fixture digest matches the recorded version exactly",
        "owning_layer": "OPS",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-09",
        "name": "stale browser state",
        "trigger": "act from a tab opened before a state change",
        "expected": "the stale page is refused; it is never an authorization guarantee",
        "owning_layer": "CTRL",
        "stop_condition": False,
    },
    {
        "scenario_id": "F-10",
        "name": "voting-linkable identifier observed in a log",
        "trigger": "observation",
        "expected": "immediate stop condition; the trial halts and the finding is escalated",
        "owning_layer": "CTRL",
        "stop_condition": True,
    },
    {
        "scenario_id": "F-11",
        "name": "real personal data observed in the preview",
        "trigger": "observation",
        "expected": "immediate stop condition; the trial halts and the environment is reset",
        "owning_layer": "OPS",
        "stop_condition": True,
    },
    {
        "scenario_id": "F-12",
        "name": "cross-scope data leak observed",
        "trigger": "observation",
        "expected": (
            "immediate stop condition; the finding is routed to the owning layer as blocking"
        ),
        "owning_layer": "API",
        "stop_condition": True,
    },
)


FINDING_ROUTING: dict[str, Any] = {
    "severities": [
        {
            "severity": "BLOCKING",
            "definition": "a trust, privacy, authorization or voting-boundary defect, or any "
            "stop condition",
            "retest": "mandatory before the checkpoint proceeds",
        },
        {
            "severity": "MAJOR",
            "definition": "a governed journey cannot complete on a real path",
            "retest": "mandatory in the owning layer's next candidate",
        },
        {
            "severity": "MINOR",
            "definition": "usability, wording or presentation defect with no trust impact",
            "retest": "at the owning layer's discretion",
        },
    ],
    "owning_layers": ["DATA", "API", "INFRA", "OPS", "CTRL", "FRONT", "PILOT", "SEC"],
    "required_fields": [
        "finding_id",
        "journey_id or scenario_id",
        "owning_layer",
        "severity",
        "reproduction steps",
        "evidence reference (privacy-safe)",
        "whether an accepted baseline correction is required",
        "retest requirement",
    ],
    "hard_rules": [
        "a trial finding never silently modifies an accepted baseline",
        (
            "a correction to an accepted baseline goes through that layer's normal governed "
            "candidate and acceptance lineage"
        ),
        "no finding is closed by the person who introduced the defect alone",
        "evidence attached to a finding is privacy-safe and carries no voting-linkable identifier",
    ],
}


FRESH_EYES_SCRIPT = """# System Trial Preview — external fresh-eyes script (preparation)

**Status:** preparation only. The trial checkpoint is not open, so this script
is not yet to be executed against a live environment.

You have not worked on this system. That is the point: please do what the tasks
describe and record what actually happened, not what you think was intended.

## Before you start

- You will be given one URL and one persona (an account and a password or
  passkey prepared for the trial). Use only that persona.
- Everything you see is trial data. It is invented. Nothing you do affects a
  real person, a real membership or a real vote.
- Please keep the notes sheet open as you go. Recording a moment of confusion is
  as useful as recording an error message.

## Ground rules for screenshots and notes

- Screenshots are welcome for anything visual that confused you.
- Do not copy out anything that looks like a code, token, key or long random
  string, even from trial data. Describe where you saw it instead.
- If you ever see something that looks like a real person's data, stop and tell
  the trial contact immediately. Do not screenshot it.

## Tasks

Do these in order. For each one, note: what you expected, what happened, and how
long it took.

1. Open the URL without signing in. Look around for two or three minutes. What
   do you think this system is for? What can you do without an account?
2. Find out how someone would become a member. Go as far as the system lets you
   without inventing personal details you are uncomfortable with.
3. Sign in with your persona. Note anything that surprised you about signing in.
4. Find something about your own region. Then try to find the same thing for a
   different region. Note what you can and cannot see.
5. Find something that was published for the public — a document, a decision, a
   representative's page. Try to work out when it was published and by whom.
6. Try to reach an administrative or management screen. You are expected to be
   refused. Note exactly what the refusal said and whether it made sense.
7. Sign out. Then press the browser Back button and try to continue where you
   were. Note what happened.
8. Find how you would report a problem or ask a question through the system.

## What to record for each task

- What you were trying to do, in your own words.
- What the system did.
- Anything that was unclear, slow, or made you hesitate.
- Anything that made you doubt whether the system had understood you.
- Anything you found by accident.

## Blocking vs non-blocking

Mark a finding **blocking** if any of these happened:

- you saw data that appears to belong to another person or another region;
- you were allowed to do something you expected to be refused;
- you saw anything resembling a vote or a ballot linked to a person;
- the system lost something you had entered, without saying so.

Everything else — confusing wording, layout problems, slowness, dead ends — is
**non-blocking** but still worth recording.

## Stop conditions

Stop immediately and contact the trial contact if:

- you believe you are seeing real personal data;
- you gain access to something that is clearly meant to be restricted;
- anything voting-related appears connected to an identifiable person;
- the environment behaves in a way that makes you uncomfortable to continue.

Stopping is never the wrong call. A stopped trial with one clear finding is
worth more than a completed trial with an unrecorded one.
"""


def _validate() -> list[str]:
    """Harness self-checks. These are the invariants, not the aspiration."""
    findings: list[str] = []
    ids = [j.journey_id for j in JOURNEYS]
    if len(ids) != len(set(ids)):
        findings.append("duplicate journey ids")
    for journey in JOURNEYS:
        for value in (journey.classification_today, journey.classification_target):
            if value not in CLASSIFICATIONS:
                findings.append(f"{journey.journey_id}: invalid classification {value}")
        if journey.is_mock_backed and (
            journey.classification_today.startswith("SUPPORTED")
            or journey.classification_target.startswith("SUPPORTED")
        ):
            findings.append(f"{journey.journey_id}: a mock-backed path is marked supported")
        if (
            CHECKPOINT_STATE == "CHECKPOINT_NOT_OPEN"
            and journey.classification_today == "SUPPORTED_REAL_PATH"
        ):
            findings.append(
                f"{journey.journey_id}: SUPPORTED_REAL_PATH claimed "
                f"while the checkpoint is not open"
            )
        if (
            journey.classification_today == "BLOCKED_BY_DEPENDENCY"
            and not journey.blocking_dependencies
        ):
            findings.append(f"{journey.journey_id}: blocked without a named dependency")
        if (
            journey.classification_today == "SUPPORTED_WITH_DECLARED_LIMITATION"
            and not journey.limitation
        ):
            findings.append(f"{journey.journey_id}: limitation claimed but not declared")
        if not journey.owning_layer:
            findings.append(f"{journey.journey_id}: no owning layer for defects")
        if not journey.expected_evidence:
            findings.append(f"{journey.journey_id}: no expected evidence")
    # Negative fixture: the rule must actually fire on a mock-backed journey.
    probe = Journey(
        journey_id="J-SELFTEST",
        category="public_anonymous",
        persona="harness self-test",
        preconditions=(),
        dependencies=(),
        browser_steps=(),
        runtime_paths=("mock response served by a stub",),
        expected_result="n/a",
        expected_evidence="n/a",
        owning_layer="OPS",
        classification_today="SUPPORTED_WITH_DECLARED_LIMITATION",
        classification_target="SUPPORTED_REAL_PATH",
        limitation="self-test",
    )
    if not probe.is_mock_backed:
        findings.append("the mock-backed rule does not detect a mock-only runtime path")

    categories = {j.category for j in JOURNEYS}
    required = {
        "public_anonymous",
        "authentication_session",
        "applicant_member",
        "participation",
        "organization_regional",
        "representative_transparency",
        "voting_boundary",
        "refusal_states",
        "degraded_dependency",
        "recovery_reset",
    }
    missing = sorted(required - categories)
    if missing:
        findings.append(f"journey categories not covered: {missing}")
    if not any(s["stop_condition"] for s in FAILURE_SCENARIOS):
        findings.append("no stop condition defined")
    return findings


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload)
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    findings = _validate()
    now = datetime.now(UTC).isoformat()

    _write(
        OUT_DIR / "journey_catalog.json",
        {
            "schema": "epd2.system-trial-preview.journey-catalog/1",
            "status": "PREPARATION_ONLY / CHECKPOINT_NOT_OPEN",
            "generated_at": now,
            "counts": {
                "journeys": len(JOURNEYS),
                "categories": len({j.category for j in JOURNEYS}),
            },
            "journeys": [j.to_obj() for j in JOURNEYS],
        },
    )
    _write(
        OUT_DIR / "preview_capability_matrix.json",
        {
            "schema": "epd2.system-trial-preview.capability-matrix/1",
            "status": "PREPARATION_ONLY / CHECKPOINT_NOT_OPEN",
            "allowed_classifications": list(CLASSIFICATIONS),
            "rule": "a mock-only path is never classified as supported",
            "checkpoint_state": CHECKPOINT_STATE,
            "checkpoint_preconditions": [
                "authoritative API-06 acceptance",
                "API layer CLOSED",
                "recorded INFRA/OPS preview-readiness minimum",
            ],
            "summary_today": {
                classification: sum(1 for j in JOURNEYS if j.classification_today == classification)
                for classification in CLASSIFICATIONS
            },
            "summary_target_at_checkpoint": {
                classification: sum(
                    1 for j in JOURNEYS if j.classification_target == classification
                )
                for classification in CLASSIFICATIONS
            },
            "entries": [
                {
                    "journey_id": j.journey_id,
                    "category": j.category,
                    "status_today": j.classification_today,
                    "status_target_at_checkpoint": j.classification_target,
                    "blocking_dependencies": [d for d in j.blocking_dependencies],
                    "declared_limitation": j.limitation,
                }
                for j in JOURNEYS
            ],
        },
    )
    _write(
        OUT_DIR / "environment_readiness_matrix.json",
        {
            "schema": "epd2.system-trial-preview.environment-readiness/1",
            "status": "PREPARATION_ONLY / CHECKPOINT_NOT_OPEN",
            "generated_at": now,
            "matrix": ENVIRONMENT_READINESS,
        },
    )
    _write(
        OUT_DIR / "seed_and_reset_design.json",
        {"schema": "epd2.system-trial-preview.seed-reset/1", "generated_at": now, **SEED_AND_RESET},
    )
    _write(
        OUT_DIR / "failure_recovery_scenarios.json",
        {
            "schema": "epd2.system-trial-preview.failure-scenarios/1",
            "generated_at": now,
            "scenarios": list(FAILURE_SCENARIOS),
            "stop_conditions": [s["scenario_id"] for s in FAILURE_SCENARIOS if s["stop_condition"]],
        },
    )
    _write(
        OUT_DIR / "finding_routing_model.json",
        {
            "schema": "epd2.system-trial-preview.finding-routing/1",
            "generated_at": now,
            **FINDING_ROUTING,
        },
    )
    _write(OUT_DIR / "external_fresh_eyes_script.md", FRESH_EYES_SCRIPT)

    result = {
        "schema": "epd2.system-trial-preview.preseal-result/1",
        "status": "PREPARATION_ONLY / CHECKPOINT_NOT_OPEN",
        "generated_at": now,
        "overall": "PASS" if not findings else "FAIL",
        "findings": findings,
        "artifacts": sorted(p.name for p in OUT_DIR.glob("*")),
        "self_state": ["PRESEAL_READY", "NOT_ACCEPTED"],
        "not_claimed": [
            "SYSTEM TRIAL PASS",
            "checkpoint opened",
            "preview readiness achieved",
            "INFRA or OPS closure",
        ],
    }
    _write(OUT_DIR / "system_trial_preview_preseal_result.json", result)

    print(f"STP_RESULT:{result['overall']}:{OUT_DIR / 'system_trial_preview_preseal_result.json'}")
    for finding in findings:
        print(f"  - {finding}")
    print(f"  journeys={len(JOURNEYS)} scenarios={len(FAILURE_SCENARIOS)}")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
