"""CTRL-05 governed Audit & Oversight Console reference runtime.

CTRL-05 lets a competent oversight actor discover, correlate, verify, review,
challenge and attest evidence produced by the accepted control planes —
without acquiring any of their powers. The pipeline is

    evidence discovery -> exact-scope filtering -> correlation -> review
    -> finding/attestation -> immutable evidence of review

and every step is bounded by an exact governed oversight mandate.

Three separations are structural here, not merely intended:

**Oversight visibility is not operational authority.** The console holds each
plane behind a read-only source projection (`oversight_sources`). It exposes
no method and no route that requests, approves, commits or resolves a CTRL-04
operation, that reads a secret, or that reaches into the voting domain. A
reviewer who *also* holds `OPS.EXECUTE` gains nothing here: CTRL-05 never
calls the operations console's mutating surface at all.

**Source evidence is immutable to CTRL-05.** Reviews annotate; they never
rewrite. There is no delete or update path to a source record, and a review
correction is a new superseding record, never an edit of the old one.

**Review history is append-only and self-evidencing.** Every oversight act —
including a refusal — is appended to a hash-chained journal that is sealed
with a key held outside the persisted state, and the case tables must agree
with that journal on every restart.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final

from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import redact_metadata, scrub_text
from epd2_control_plane_service.operations_console import EvidenceSealer
from epd2_control_plane_service.oversight_sources import (
    PERSON_IDENTIFIER_FIELDS,
    EvidenceDomain,
    EvidenceEnvelope,
    EvidencePlane,
    EvidenceReference,
    EvidenceSource,
    SourceUnavailable,
    VotingVerificationSource,
    collect,
)
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)
from epd2_core.canonical_json import canonical_dumps

__all__ = [
    "CTRL05_ACTIONS",
    "EXPORT_PURPOSES",
    "AuditRight",
    "CorrelationGraph",
    "EvidenceExportRequest",
    "EvidenceQuery",
    "FindingSeverity",
    "OversightConsoleService",
    "OversightEvent",
    "OversightMandate",
    "OversightPolicy",
    "OversightRefusal",
    "OversightScope",
    "OversightSession",
    "RedactionDecision",
    "ReviewAttestation",
    "ReviewCase",
    "ReviewDisposition",
    "ReviewFinding",
    "ReviewState",
    "SessionState",
]

# ---------------------------------------------------------------------------
# Governed constants. The mutation corpus flips these one at a time.
# ---------------------------------------------------------------------------

STAGE: Final = "CTRL-05"
SELF_STATE: Final = "CANDIDATE_NOT_ACCEPTED"
POLICY_VERSION: Final = "ctrl05-policy/1"
UNIVERSAL_AUDITOR_EXISTS: Final = False
REVIEWER_MAY_EXECUTE_OPERATIONS: Final = False
SOURCE_EVIDENCE_IS_MUTABLE: Final = False
FRONTEND_MAY_ASSERT_INTEGRITY: Final = False
FRONTEND_MAY_ASSERT_AUTHORITY: Final = False
GATES_REQUIRED: Final = 56
MUTATION_FIXTURES_REQUIRED: Final = 52
E2E_JOURNEYS_REQUIRED: Final = 22
CTRL01_ACCEPTED_SHA256: Final = "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
CTRL02_ACCEPTED_SHA256: Final = "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
CTRL03_ACCEPTED_SHA256: Final = "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff"
CTRL04_ACCEPTED_SHA256: Final = "346acc12316ac4a8f2be45c889aa9002172710da61c67ec88e54a976bb5733a2"

#: Bounded query and traversal limits (no unbounded global evidence search).
MAX_QUERY_LIMIT: Final = 500
MAX_GRAPH_NODES: Final = 200
MAX_GRAPH_DEPTH: Final = 3
MAX_SESSION_LIFETIME: Final = timedelta(hours=8)
MAX_MANDATE_LIFETIME: Final = timedelta(days=365)
MAX_ATTESTATION_STATEMENT: Final = 2048

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
COARSE_TARGETS: Final = frozenset({"*", "ALL", "GLOBAL", "ANY", "REGION"})


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AuditRight(StrEnum):
    """Separable oversight capabilities.

    They are disjoint from every operational right: no CTRL-05 right implies
    `OPS.EXECUTE`, secret visibility or key custody, and holding an operational
    right grants nothing in this console.
    """

    READ = "AUDIT.READ"
    CORRELATE = "AUDIT.CORRELATE"
    REVIEW = "AUDIT.REVIEW"
    ATTEST = "AUDIT.ATTEST"
    EXPORT = "AUDIT.EXPORT"


#: Operational/custody rights that must never be reachable from this console.
FORBIDDEN_OPERATIONAL_RIGHTS: Final = frozenset(
    {
        "OPS.REQUEST",
        "OPS.APPROVE",
        "OPS.EXECUTE",
        "LIFECYCLE.EXECUTE",
        "SECRET.RAW_READ",
        "SECRET.EXPORT",
        "KEY.CUSTODY",
        "VOTING.ADMIN",
        "AUTHORITY.UNIVERSAL_ADMIN",
    }
)


class ReviewState(StrEnum):
    OPENED = "OPENED"
    IN_REVIEW = "IN_REVIEW"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    FINDING_RAISED = "FINDING_RAISED"
    NO_FINDING = "NO_FINDING"
    REMEDIATION_LINKED = "REMEDIATION_LINKED"
    ATTESTED = "ATTESTED"
    CLOSED = "CLOSED"


#: States from which a case may still be worked. `CLOSED` is terminal.
OPEN_STATES: Final = frozenset(
    {
        ReviewState.OPENED,
        ReviewState.IN_REVIEW,
        ReviewState.NEEDS_CLARIFICATION,
        ReviewState.FINDING_RAISED,
        ReviewState.NO_FINDING,
        ReviewState.REMEDIATION_LINKED,
    }
)
DISPOSITION_STATES: Final = frozenset(
    {ReviewState.NEEDS_CLARIFICATION, ReviewState.FINDING_RAISED, ReviewState.NO_FINDING}
)


class FindingSeverity(StrEnum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingState(StrEnum):
    RAISED = "RAISED"
    DISPUTED = "DISPUTED"
    UPHELD = "UPHELD"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"


class SessionState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class OversightRefusal(StrEnum):
    """Stable reason codes. Every refusal is evidence-bearing."""

    NO_SESSION = "AUD_NO_SESSION"
    SESSION_REVOKED = "AUD_SESSION_REVOKED"
    SESSION_EXPIRED = "AUD_SESSION_EXPIRED"
    SESSION_PRINCIPAL_MISMATCH = "AUD_SESSION_PRINCIPAL_MISMATCH"
    CSRF_INVALID = "AUD_CSRF_TOKEN_INVALID"
    NO_MANDATE = "AUD_NO_OVERSIGHT_MANDATE"
    MANDATE_EXPIRED = "AUD_MANDATE_EXPIRED"
    MANDATE_SUPERSEDED = "AUD_MANDATE_SUPERSEDED"
    WRONG_ORGANIZATION_SCOPE = "AUD_WRONG_ORGANIZATION_SCOPE"
    WRONG_UNIT_SCOPE = "AUD_WRONG_UNIT_SCOPE"
    PLANE_NOT_IN_MANDATE = "AUD_PLANE_NOT_IN_MANDATE"
    NO_RIGHT = "AUD_RIGHT_ABSENT"
    STALE_AUTHORITY = "AUD_STALE_AUTHORITY"
    AUTHORITY_UNRESOLVABLE = "AUD_AUTHORITY_UNRESOLVABLE"
    COMPETENCE_SOURCE_MISSING = "AUD_COMPETENCE_SOURCE_MISSING"
    UNIVERSAL_AUDITOR = "AUD_UNIVERSAL_AUDITOR_FORBIDDEN"
    OPERATIONAL_RIGHT_NOT_USABLE = "AUD_OPERATIONAL_RIGHT_NOT_USABLE_HERE"
    EXECUTION_SURFACE_ABSENT = "AUD_EXECUTION_SURFACE_ABSENT"
    UNBOUNDED_QUERY = "AUD_UNBOUNDED_QUERY_FORBIDDEN"
    QUERY_LIMIT = "AUD_QUERY_LIMIT_EXCEEDED"
    GRAPH_LIMIT = "AUD_GRAPH_LIMIT_EXCEEDED"
    UNKNOWN_EVIDENCE = "AUD_UNKNOWN_EVIDENCE"
    EVIDENCE_UNTRUSTWORTHY = "AUD_EVIDENCE_INTEGRITY_NOT_VERIFIED"
    EVIDENCE_DIVERGED = "AUD_EVIDENCE_DIVERGED_SINCE_REVIEW"
    INTEGRITY_METADATA_MISSING = "AUD_INTEGRITY_METADATA_MISSING"
    SOURCE_UNAVAILABLE = "AUD_SOURCE_UNAVAILABLE"
    UNKNOWN_SCHEMA = "AUD_UNKNOWN_EVIDENCE_SCHEMA"
    UNKNOWN_CASE = "AUD_UNKNOWN_CASE"
    WRONG_STATE = "AUD_WRONG_REVIEW_STATE"
    STALE_CASE_VERSION = "AUD_STALE_REVIEW_VERSION"
    DISPOSITION_REQUIRED = "AUD_DISPOSITION_REQUIRED"
    FINDING_WITHOUT_EVIDENCE = "AUD_FINDING_WITHOUT_EVIDENCE"
    ATTESTATION_WITHOUT_AUTHORITY = "AUD_ATTESTATION_WITHOUT_AUTHORITY"
    HISTORY_IMMUTABLE = "AUD_HISTORY_IS_APPEND_ONLY"
    SOURCE_IMMUTABLE = "AUD_SOURCE_EVIDENCE_IMMUTABLE"
    IDEMPOTENCY_CONFLICT = "AUD_IDEMPOTENCY_CONFLICT"
    REPLAYED_REQUEST = "AUD_REPLAYED_REQUEST"
    EXPORT_PURPOSE_UNKNOWN = "AUD_EXPORT_PURPOSE_UNKNOWN"
    EXPORT_OUT_OF_PURPOSE = "AUD_EXPORT_FIELD_OUT_OF_PURPOSE"
    EXPORT_UNAUTHORIZED = "AUD_EXPORT_UNAUTHORIZED"
    EXPORT_LIMIT = "AUD_EXPORT_LIMIT_EXCEEDED"
    SECRET_VISIBILITY = "AUD_SECRET_VISIBILITY_FORBIDDEN"
    PERSON_IDENTIFIER = "AUD_PERSON_IDENTIFIER_FORBIDDEN"
    VOTING_BOUNDARY = "AUD_VOTING_BOUNDARY"
    REMEDIATION_NOT_EXECUTED = "AUD_REMEDIATION_IS_REFERENCE_ONLY"
    PARAMETER_INVALID = "AUD_PARAMETER_INVALID"
    CLOCK_ROLLBACK = "AUD_CLOCK_ROLLBACK"
    NOT_FOUND = "AUD_NOT_FOUND"
    BROWSER_STATE_REJECTED = "AUD_BROWSER_STATE_NOT_AUTHORITATIVE"


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OversightPolicy:
    """Enforcement obligations. All default to enforced; only `governed()` is
    permitted in a candidate. The anti-cheat corpus flips them one at a time."""

    enforce_session_state: bool = True
    enforce_csrf: bool = True
    enforce_organization_scope: bool = True
    enforce_unit_scope: bool = True
    enforce_plane_mandate: bool = True
    enforce_competence_source: bool = True
    enforce_authority_version: bool = True
    commit_time_reauthorization: bool = True
    enforce_rights: bool = True
    reject_operational_rights: bool = True
    enforce_integrity_verification: bool = True
    require_trustworthy_evidence_for_findings: bool = True
    enforce_evidence_divergence_check: bool = True
    fail_closed_on_source_unavailable: bool = True
    enforce_query_bounds: bool = True
    enforce_graph_bounds: bool = True
    enforce_append_only_history: bool = True
    enforce_case_version: bool = True
    enforce_idempotency: bool = True
    enforce_disposition_before_attestation: bool = True
    enforce_finding_evidence_reference: bool = True
    enforce_export_purpose: bool = True
    enforce_export_redaction_record: bool = True
    enforce_secret_redaction: bool = True
    enforce_person_identifier_screen: bool = True
    enforce_voting_boundary: bool = True
    enforce_evidence_on_refusal: bool = True
    enforce_journal_immutability: bool = True

    @classmethod
    def governed(cls) -> OversightPolicy:
        return cls()

    def is_governed(self) -> bool:
        return all(getattr(self, item.name) is True for item in fields(self))

    def disabled_obligations(self) -> tuple[str, ...]:
        return tuple(item.name for item in fields(self) if getattr(self, item.name) is not True)

    def without(self, obligation: str) -> OversightPolicy:
        if obligation not in {item.name for item in fields(self)}:
            raise KeyError(obligation)
        return replace(self, **{obligation: False})


# ---------------------------------------------------------------------------
# Typed records
# ---------------------------------------------------------------------------


#: Capability names that would make their holder a universal auditor. None of
#: them grants any oversight competence; holding one refuses everything.
UNIVERSAL_CAPABILITY_NAMES: Final = frozenset({"ADMIN", "SUPER_ADMIN", "ROOT", "AUDITOR"})


def _is_universal(capability: str) -> bool:
    return "*" in capability or capability.upper() in UNIVERSAL_CAPABILITY_NAMES


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or value in COARSE_TARGETS or not _SAFE_ID.match(value):
        raise ValueError(f"{label} must be an exact, non-coarse identifier")
    return value


@dataclass(frozen=True, slots=True)
class OversightScope:
    """An exact oversight scope: organization *and* governed oversight unit.

    Containment is equality. A scope never contains another scope: a Bund
    mandate does not reach a Land, and an operations-audit unit does not reach
    a privacy-oversight unit. `unit_id` names the exact governed oversight unit
    the mandate was created for; evidence is assigned to a unit by an explicit
    governed mapping, never by inference.
    """

    region_id: str
    org_id: str
    unit_id: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.region_id, "region_id"),
            (self.org_id, "org_id"),
            (self.unit_id, "unit_id"),
        ):
            _require_id(value, f"OversightScope.{label}")

    @property
    def key(self) -> str:
        return f"{self.region_id}:{self.org_id}:{self.unit_id}"

    @property
    def organization_key(self) -> str:
        return f"{self.region_id}:{self.org_id}"

    @property
    def exact_scope(self) -> ExactScope:
        return ExactScope(self.region_id, self.org_id)

    def contains(self, other: OversightScope) -> bool:
        """Exact-scope equality. No hierarchy, no wildcard, no inheritance."""
        return (
            self.region_id == other.region_id
            and self.org_id == other.org_id
            and self.unit_id == other.unit_id
        )


@dataclass(frozen=True, slots=True)
class OversightMandate:
    """The governed competence that makes someone a reviewer, here, now.

    A mandate is never a role label: it names the exact scope, the exact
    evidence planes it covers, the governing rule version and the source
    decision that created it, and it expires. An actor with no mandate has no
    oversight visibility at all, whatever else they hold.
    """

    mandate_id: str
    subject_ref: str
    scope: OversightScope
    planes: frozenset[EvidencePlane]
    rights: frozenset[AuditRight]
    rule_version: str
    source_decision_ref: str
    #: Exactly one live CTRL-02 grant per right the mandate carries, as
    #: ``(right value, grant id)`` pairs. Every right is backed by its own
    #: authority; a right with no binding is not exercisable, and a binding
    #: whose grant is gone, revoked or re-issued makes the mandate stale.
    authority_bindings: frozenset[tuple[str, str]]
    valid_from: datetime
    valid_until: datetime
    superseded_by: str | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_id(self.mandate_id, "OversightMandate.mandate_id")
        if not self.rule_version or not self.source_decision_ref:
            raise ValueError(
                "an oversight mandate requires an exact rule_version and source_decision_ref"
            )
        if not self.planes or not self.rights:
            raise ValueError("an oversight mandate must name its planes and rights")
        bound = {right for right, _ in self.authority_bindings}
        missing = sorted(r.value for r in self.rights if r.value not in bound)
        if missing:
            raise ValueError(f"rights without a backing authority grant: {missing}")
        span = self.valid_until - self.valid_from
        if span.total_seconds() <= 0 or span > MAX_MANDATE_LIFETIME:
            raise ValueError("oversight mandate validity must be positive and bounded")

    def usable_at(self, moment: datetime) -> tuple[bool, OversightRefusal | None]:
        if self.superseded_by is not None:
            return False, OversightRefusal.MANDATE_SUPERSEDED
        if self.revoked_at is not None and moment >= self.revoked_at:
            return False, OversightRefusal.MANDATE_EXPIRED
        if not (self.valid_from <= moment < self.valid_until):
            return False, OversightRefusal.MANDATE_EXPIRED
        return True, None

    def grant_for(self, right: AuditRight) -> str | None:
        """The grant id that backs exactly this right, or None."""
        for value, grant_id in self.authority_bindings:
            if value == right.value:
                return grant_id
        return None

    @property
    def competence_ref(self) -> str:
        return f"{self.mandate_id}@{self.rule_version}#{self.source_decision_ref}"


@dataclass(frozen=True, slots=True)
class OversightSession:
    """A console session. Carries a CSRF token that the browser must echo on
    every mutating act; the token never appears in a read response body."""

    session_id: str
    principal_id: str
    state: SessionState
    established_at: datetime
    expires_at: datetime
    csrf_token: str

    def usable_at(self, moment: datetime) -> tuple[bool, OversightRefusal | None]:
        if self.state is SessionState.REVOKED:
            return False, OversightRefusal.SESSION_REVOKED
        if self.state is SessionState.EXPIRED or moment >= self.expires_at:
            return False, OversightRefusal.SESSION_EXPIRED
        return True, None


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason_code: str
    stage: str
    actor_ref: str
    mandate_ref: str | None
    authority_ref: str | None
    authority_version: int | None
    scope_key: str | None
    policy_version: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceQuery:
    """A bounded, anchored evidence query. There is no global search."""

    scope: OversightScope
    planes: frozenset[EvidencePlane] = frozenset()
    correlation_ref: str | None = None
    action_code: str | None = None
    actor_ref: str | None = None
    object_ref: str | None = None
    result: str | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if self.limit <= 0 or self.limit > MAX_QUERY_LIMIT:
            raise ValueError(f"query limit must be within 1..{MAX_QUERY_LIMIT}")


@dataclass(frozen=True, slots=True)
class CorrelationGraph:
    """A bounded correlation view anchored on one governed correlation id.

    Nodes are evidence references; edges are governed relations only
    (`same-correlation`, `chain-successor`). No node is a person and no edge is
    derived from a personal attribute.
    """

    anchor: str
    scope_key: str
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, str], ...]
    truncated: bool
    node_limit: int
    depth: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "anchor": self.anchor,
            "scope": self.scope_key,
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "truncated": self.truncated,
            "node_limit": self.node_limit,
            "depth": self.depth,
            "person_nodes": 0,
        }


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    """A finding always names an exact immutable evidence reference."""

    finding_id: str
    case_id: str
    severity: FindingSeverity
    summary: str
    evidence_reference: EvidenceReference
    evidence_content_digest: str
    raised_by: str
    raised_at: datetime
    mandate_ref: str
    authority_ref: str
    state: FindingState = FindingState.RAISED
    superseded_by: str | None = None
    dispute_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewDisposition:
    """One append-only disposition step of a case. Never overwritten."""

    disposition_id: str
    case_id: str
    state: ReviewState
    rationale: str
    decided_by: str
    decided_at: datetime
    mandate_ref: str
    authority_ref: str
    supersedes: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewAttestation:
    """An attestation binds the exact review state to a live authority."""

    attestation_id: str
    case_id: str
    statement: str
    outcome: ReviewState
    attested_by: str
    attested_at: datetime
    mandate_ref: str
    authority_ref: str
    authority_version: int
    case_version: int
    disposition_ref: str
    finding_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reauthorized_at: datetime


@dataclass(frozen=True, slots=True)
class RemediationLink:
    """An outward reference to a remediation request owned by another plane.

    CTRL-05 records the identifier and never performs the operation: the
    remediation must travel that plane's own request/approval/execution path.
    """

    link_id: str
    case_id: str
    remediation_plane: str
    remediation_ref: str
    linked_by: str
    linked_at: datetime
    executed_by_ctrl05: bool = False


@dataclass(frozen=True, slots=True)
class ReviewCase:
    """A review case over exactly one scope and one bounded evidence set."""

    case_id: str
    title: str
    scope: OversightScope
    opened_by: str
    opened_at: datetime
    mandate_ref: str
    authority_ref: str
    state: ReviewState
    version: int
    evidence_refs: tuple[str, ...]
    disposition_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    attestation_ids: tuple[str, ...] = ()
    remediation_ids: tuple[str, ...] = ()
    clarification_ids: tuple[str, ...] = ()
    closed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Clarification:
    """An annotation. It adds to the record; it never rewrites the source."""

    clarification_id: str
    case_id: str
    text: str
    author_ref: str
    created_at: datetime
    evidence_reference: EvidenceReference | None


@dataclass(frozen=True, slots=True)
class RedactionDecision:
    """The evidenced decision about what an export dropped, and why."""

    decision_id: str
    export_id: str
    purpose: str
    policy_version: str
    allowed_fields: tuple[str, ...]
    dropped_fields: tuple[str, ...]
    redacted_values: tuple[str, ...]
    record_count: int
    decided_at: datetime
    decided_by: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "export_id": self.export_id,
            "purpose": self.purpose,
            "policy_version": self.policy_version,
            "allowed_fields": list(self.allowed_fields),
            "dropped_fields": list(self.dropped_fields),
            "redacted_values": list(self.redacted_values),
            "record_count": self.record_count,
            "decided_at": self.decided_at.isoformat(),
            "decided_by": self.decided_by,
        }


@dataclass(frozen=True, slots=True)
class EvidenceExportRequest:
    export_id: str
    purpose: str
    scope: OversightScope
    case_id: str | None
    evidence_refs: tuple[str, ...]
    requested_by: str
    requested_at: datetime
    mandate_ref: str
    authority_ref: str
    redaction_decision_id: str
    payload_digest: str
    record_count: int


@dataclass(frozen=True, slots=True)
class OversightEvent:
    """A reference to one immutable oversight-journal record."""

    event_id: str
    journal_sequence: int
    event_hash: str
    act: str
    subject_ref: str
    result: str
    reason_code: str


#: Purpose-bound export field allow-lists. A field outside the purpose is
#: dropped and the drop is recorded; the purpose is never widened silently.
EXPORT_PURPOSES: Final[dict[str, frozenset[str]]] = {
    "INTERNAL_REVIEW": frozenset(
        {
            "reference",
            "scope",
            "occurred_at",
            "actor_ref",
            "authority_ref",
            "action_code",
            "object_ref",
            "result",
            "reason_code",
            "correlation_ref",
            "approval_refs",
            "integrity",
        }
    ),
    "GOVERNANCE_REPORT": frozenset(
        {
            "reference",
            "scope",
            "occurred_at",
            "action_code",
            "object_ref",
            "result",
            "reason_code",
            "correlation_ref",
            "integrity",
        }
    ),
    "EXTERNAL_AUDITOR": frozenset(
        {"reference", "scope", "occurred_at", "action_code", "result", "integrity"}
    ),
    "STATISTICAL": frozenset({"scope", "occurred_at", "action_code", "result"}),
}
MAX_EXPORT_RECORDS: Final = 200

#: Shapes that are secret *material* wherever they appear. An export whose
#: unredacted bytes carry one of these is refused outright rather than
#: scrubbed, because a redactor that silently succeeds proves nothing.
SECRET_SHAPE_MARKERS: Final = (
    "-----BEGIN",
    "sk_live_",
    "sk_test_",
    "eyJhbGciOi",
    "AKIA",
    "ghp_",
    "glpat-",
    "xoxb-",
    "xoxp-",
    "AIza",
)

#: Machine-readable action catalogue of the console (contract surface).
CTRL05_ACTIONS: Final = (
    {"action_id": "AUDIT.EVIDENCE.SEARCH", "right": "AUDIT.READ", "mutation": False},
    {"action_id": "AUDIT.EVIDENCE.OPEN", "right": "AUDIT.READ", "mutation": False},
    {"action_id": "AUDIT.EVIDENCE.VERIFY", "right": "AUDIT.READ", "mutation": False},
    {"action_id": "AUDIT.CORRELATION.GRAPH", "right": "AUDIT.CORRELATE", "mutation": False},
    {"action_id": "AUDIT.CHAIN.OPEN", "right": "AUDIT.CORRELATE", "mutation": False},
    {"action_id": "AUDIT.CASE.OPEN", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.CASE.CLARIFY", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.CASE.DISPOSE", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.FINDING.RAISE", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.FINDING.DISPUTE", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.REMEDIATION.LINK", "right": "AUDIT.REVIEW", "mutation": True},
    {"action_id": "AUDIT.CASE.ATTEST", "right": "AUDIT.ATTEST", "mutation": True},
    {"action_id": "AUDIT.CASE.CLOSE", "right": "AUDIT.ATTEST", "mutation": True},
    {"action_id": "AUDIT.EVIDENCE.EXPORT", "right": "AUDIT.EXPORT", "mutation": True},
)


def _scrub_structure(value: Any) -> Any:
    """Scrub every string *leaf* of a structure, never the serialised bytes.

    `scrub_text` rewrites `key=<secret>` runs up to the end of the match, so
    applying it to a whole JSON document can consume the closing quote and
    everything after it: the model then either fails to parse or, worse,
    silently loses its tail. Scrubbing at the leaf keeps the structure intact
    and the redaction exact.
    """
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, dict):
        return {k: _scrub_structure(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_scrub_structure(v) for v in value]
    return value


def _content_digest(*parts: object) -> str:
    """A stable digest over the substance of one governed review record.

    The journal already names each record's id; this binds its *content* —
    severity, rationale, statement, authorship — so that a checkpoint whose
    tables were rewritten cannot agree with the journal merely by keeping the
    record counts right.
    """
    return hashlib.sha256(
        "\u001f".join("" if p is None else str(p) for p in parts).encode()
    ).hexdigest()


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return parsed


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class OversightConsoleService:
    """The CTRL-05 governed oversight surface.

    It owns review state and its own append-only journal. It owns no source
    evidence: the planes it reviews are reached only through the read-only
    projections in `oversight_sources`, and there is deliberately no attribute
    on this service that holds a mutating handle to any of them.
    """

    def __init__(
        self,
        *,
        authorities: AuthorityDirectory,
        sources: Mapping[str, EvidenceSource],
        evidence_units: Mapping[str, str] | None = None,
        voting_verification: VotingVerificationSource | None = None,
        policy: OversightPolicy | None = None,
        store: Any | None = None,
        sealer: EvidenceSealer | None = None,
    ) -> None:
        self.authorities = authorities
        #: The evidence planes, held privately. They are reachable only through
        #: `source()` / `plane_ids()`, which return the read-only adapters, so
        #: no oversight-side code can obtain a handle it could act through.
        self._sources = dict(sources)
        #: Governed mapping "plane:stream" -> exact oversight scope key
        #: ("region:org:unit"). Evidence whose stream is unmapped is refused:
        #: unit scope fails closed rather than defaulting to visible.
        self.evidence_units = dict(evidence_units or {})
        self.voting_verification = voting_verification
        self.policy = policy or OversightPolicy.governed()
        self.journal = EvidenceJournal()
        self.sealer = sealer
        self._store = store
        self._lock = threading.RLock()
        self._mandates: dict[str, OversightMandate] = {}
        self._sessions: dict[str, OversightSession] = {}
        self._cases: dict[str, ReviewCase] = {}
        self._dispositions: dict[str, ReviewDisposition] = {}
        self._findings: dict[str, ReviewFinding] = {}
        self._attestations: dict[str, ReviewAttestation] = {}
        self._clarifications: dict[str, Clarification] = {}
        self._remediations: dict[str, RemediationLink] = {}
        self._exports: dict[str, EvidenceExportRequest] = {}
        self._redactions: dict[str, RedactionDecision] = {}
        self._tickets: dict[str, dict[str, Any]] = {}
        self._decisions: dict[str, list[AuthorizationDecision]] = {}
        self._events: dict[str, list[OversightEvent]] = {}
        self._idempotency: dict[str, str] = {}
        self._counter = 0
        self._last_time = datetime(1970, 1, 1, tzinfo=UTC)

    # -- registration --------------------------------------------------------

    def register_mandate(self, mandate: OversightMandate) -> None:
        with self._lock:
            self._mandates[mandate.mandate_id] = mandate
            self._persist()

    def supersede_mandate(self, mandate_id: str, successor_id: str) -> OversightMandate:
        with self._lock:
            current = self._mandates[mandate_id]
            updated = replace(current, superseded_by=successor_id)
            self._mandates[mandate_id] = updated
            self._persist()
            return updated

    def register_evidence_unit(
        self, plane: EvidencePlane, stream_id: str, scope: OversightScope
    ) -> None:
        """Assign one evidence stream to exactly one governed oversight scope."""
        with self._lock:
            _require_id(stream_id, "stream_id")
            self.evidence_units[f"{plane.value}:{stream_id}"] = scope.key
            self._persist()

    def open_session(self, session: OversightSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session
            self._persist()

    def revoke_session(self, session_id: str) -> None:
        with self._lock:
            current = self._sessions[session_id]
            self._sessions[session_id] = replace(current, state=SessionState.REVOKED)
            self._persist()

    def session(self, session_id: str) -> OversightSession | None:
        return self._sessions.get(session_id)

    def mandate(self, mandate_id: str) -> OversightMandate | None:
        return self._mandates.get(mandate_id)

    def mandates_of(self, subject_ref: str) -> tuple[OversightMandate, ...]:
        return tuple(m for m in self._mandates.values() if m.subject_ref == subject_ref)

    def plane_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._sources))

    def _source(self, plane: EvidencePlane) -> EvidenceSource | None:
        return self._sources.get(plane.value)

    # -- helpers -------------------------------------------------------------

    def _time(
        self, supplied: datetime, *, actor_ref: str = "UNKNOWN", act: str = "AUDIT"
    ) -> datetime:
        """Advance the console clock, refusing a rollback *with evidence*.

        A rolled-back clock is the attempt a reviewer most needs to see, so it
        is journaled like any other refusal rather than raised silently.
        """
        if supplied.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        with self._lock:
            if supplied < self._last_time:
                raise self._refuse(
                    now=self._last_time,
                    actor_ref=actor_ref,
                    act=act,
                    scope_key="UNKNOWN",
                    object_ref="clock",
                    reason=OversightRefusal.CLOCK_ROLLBACK,
                    correlation="clock",
                    detail=(
                        f"clock moved backwards from {self._last_time.isoformat()} "
                        f"to {supplied.isoformat()}; refusing to act"
                    ),
                )
            self._last_time = supplied
            return supplied

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:06d}"

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save(self.checkpoint())

    def _record(
        self,
        *,
        now: datetime,
        actor_ref: str,
        authority_basis: str,
        act: str,
        scope_key: str,
        object_ref: str,
        result: str,
        reason_code: str,
        correlation: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> OversightEvent:
        attrs = {str(k): str(v) for k, v in dict(attributes or {}).items()}
        if self.policy.enforce_secret_redaction:
            attrs, redacted = redact_metadata(attrs)
            for key in redacted:
                del attrs[key]
            if redacted:
                attrs["evidence_redacted_fields"] = ",".join(sorted(redacted))
            attrs = {k: scrub_text(v) for k, v in attrs.items()}
        if self.policy.enforce_person_identifier_screen:
            for key in attrs:
                if key.lower() in PERSON_IDENTIFIER_FIELDS:
                    raise AuthorizationRefused(
                        f"journal attribute {key!r} would create a person identifier",
                        reason_code=OversightRefusal.PERSON_IDENTIFIER,
                    )
        event = self.journal.append(
            occurred_at=now,
            actor_ref=actor_ref,
            actor_class=ActorClass.HUMAN.value,
            authority_basis=authority_basis,
            action_id=act,
            scope_key=scope_key,
            object_ref=object_ref,
            result=result,
            reason_code=reason_code,
            correlation_ref=correlation,
            attributes=attrs,
        )
        reference = OversightEvent(
            event_id=f"AEV-{event.sequence:06d}",
            journal_sequence=event.sequence,
            event_hash=event.event_hash,
            act=act,
            subject_ref=actor_ref,
            result=result,
            reason_code=reason_code,
        )
        self._events.setdefault(correlation, []).append(reference)
        return reference

    def _decide(
        self,
        *,
        act: str,
        actor_ref: str,
        allowed: bool,
        reason: str,
        correlation: str,
        mandate: OversightMandate | None = None,
        grant: AuthorityGrant | None = None,
        detail: str = "",
    ) -> AuthorizationDecision:
        decision = AuthorizationDecision(
            allowed=allowed,
            reason_code=reason,
            stage=act,
            actor_ref=actor_ref,
            mandate_ref=None if mandate is None else mandate.competence_ref,
            authority_ref=None if grant is None else grant.grant_id,
            authority_version=None if grant is None else grant.version,
            scope_key=None if mandate is None else mandate.scope.key,
            policy_version=POLICY_VERSION,
            detail=detail,
        )
        self._decisions.setdefault(correlation, []).append(decision)
        return decision

    def _refuse(
        self,
        *,
        now: datetime,
        actor_ref: str,
        act: str,
        scope_key: str,
        object_ref: str,
        reason: OversightRefusal | str,
        correlation: str,
        detail: str = "",
        authority_basis: str = "NONE",
    ) -> AuthorizationRefused:
        code = reason.value if isinstance(reason, OversightRefusal) else reason
        if self.policy.enforce_evidence_on_refusal:
            self._record(
                now=now,
                actor_ref=actor_ref,
                authority_basis=authority_basis,
                act=act,
                scope_key=scope_key,
                object_ref=object_ref,
                result="REFUSED",
                reason_code=code,
                correlation=correlation,
                attributes={"detail": detail[:200]} if detail else None,
            )
            self._persist()
        return AuthorizationRefused(detail or code, reason_code=code)

    def _session(self, session_id: str, principal_id: str, now: datetime) -> OversightSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AuthorizationRefused("no session", reason_code=OversightRefusal.NO_SESSION)
        if session.principal_id != principal_id:
            raise AuthorizationRefused(
                "session does not belong to actor",
                reason_code=OversightRefusal.SESSION_PRINCIPAL_MISMATCH,
            )
        if self.policy.enforce_session_state:
            usable, why = session.usable_at(now)
            if not usable:
                assert why is not None
                raise AuthorizationRefused(f"session {why.value}", reason_code=why)
        return session

    def _check_csrf(self, session: OversightSession, csrf_token: str | None) -> None:
        if not self.policy.enforce_csrf:
            return
        if not csrf_token or not hmac.compare_digest(session.csrf_token, str(csrf_token)):
            raise AuthorizationRefused(
                "missing or stale CSRF token", reason_code=OversightRefusal.CSRF_INVALID
            )

    def _resolve_mandate(
        self,
        *,
        actor_ref: str,
        scope: OversightScope,
        right: AuditRight,
        now: datetime,
        plane: EvidencePlane | None = None,
    ) -> tuple[OversightMandate, AuthorityGrant]:
        """Resolve the exact governed mandate and its live authority grant.

        Order matters. A universal or operational capability is refused before
        anything else, so a principal cannot reach oversight through an
        administrative or operational right. Then scope, then unit, then plane,
        then right, then the live CTRL-02 grant that backs the mandate.
        """
        if self.policy.reject_operational_rights:
            operational = [
                grant
                for grant in self.authorities._grants.values()
                if grant.actor_id == actor_ref
                and (
                    grant.capability in FORBIDDEN_OPERATIONAL_RIGHTS
                    or _is_universal(grant.capability)
                )
            ]
            wildcard = [g for g in operational if _is_universal(g.capability)]
            if wildcard:
                raise AuthorizationRefused(
                    "a universal or wildcard capability grants no oversight competence",
                    reason_code=OversightRefusal.UNIVERSAL_AUDITOR,
                )
        candidates = self.mandates_of(actor_ref)
        if not candidates:
            raise AuthorizationRefused(
                f"{actor_ref} holds no oversight mandate",
                reason_code=OversightRefusal.NO_MANDATE,
            )
        scoped = [
            m
            for m in candidates
            if (not self.policy.enforce_organization_scope)
            or m.scope.organization_key == scope.organization_key
        ]
        if not scoped:
            raise AuthorizationRefused(
                f"no mandate of {actor_ref} covers organization {scope.organization_key}; "
                f"a higher organization inherits nothing",
                reason_code=OversightRefusal.WRONG_ORGANIZATION_SCOPE,
            )
        united = [
            m
            for m in scoped
            if (not self.policy.enforce_unit_scope) or m.scope.unit_id == scope.unit_id
        ]
        if not united:
            raise AuthorizationRefused(
                f"no mandate of {actor_ref} covers oversight unit {scope.unit_id}",
                reason_code=OversightRefusal.WRONG_UNIT_SCOPE,
            )
        if plane is not None and self.policy.enforce_plane_mandate:
            united = [m for m in united if plane in m.planes]
            if not united:
                raise AuthorizationRefused(
                    f"mandate does not cover evidence plane {plane.value}",
                    reason_code=OversightRefusal.PLANE_NOT_IN_MANDATE,
                )
        if self.policy.enforce_rights:
            united = [m for m in united if right in m.rights]
            if not united:
                raise AuthorizationRefused(
                    f"mandate does not carry {right.value}",
                    reason_code=OversightRefusal.NO_RIGHT,
                )
        live: OversightMandate | None = None
        last: OversightRefusal = OversightRefusal.MANDATE_EXPIRED
        for candidate in united:
            usable, why = candidate.usable_at(now)
            if usable:
                live = candidate
                break
            last = why or last
        if live is None:
            raise AuthorizationRefused("oversight mandate is not effective", reason_code=last)
        if self.policy.enforce_competence_source and not (
            live.rule_version and live.source_decision_ref
        ):
            raise AuthorizationRefused(
                "mandate carries no governing rule version or source decision",
                reason_code=OversightRefusal.COMPETENCE_SOURCE_MISSING,
            )
        if self.policy.reject_operational_rights:
            borrowed = live.grant_for(right)
            backing = None if borrowed is None else self.authorities._grants.get(borrowed)
            if backing is not None and (
                backing.capability in FORBIDDEN_OPERATIONAL_RIGHTS
                or _is_universal(backing.capability)
            ):
                # A mandate cannot borrow an operational capability as its
                # authority: request/approve/execute and secret or key custody
                # are not oversight competence, however the mandate is written.
                raise AuthorizationRefused(
                    f"{right.value} is bound to the operational capability "
                    f"{backing.capability!r}, which grants no oversight competence",
                    reason_code=OversightRefusal.OPERATIONAL_RIGHT_NOT_USABLE,
                )
        try:
            grant = self.authorities.require(
                actor_id=actor_ref,
                capability=right.value,
                scope=live.scope.exact_scope,
                now=now,
            )
        except AuthorizationRefused as exc:
            raise AuthorizationRefused(
                f"no live authority backs the mandate: {exc}",
                reason_code=OversightRefusal.STALE_AUTHORITY
                if str(exc.reason_code) in {"STALE_AUTHORITY", "GRANT_EXPIRED"}
                else OversightRefusal.AUTHORITY_UNRESOLVABLE,
            ) from exc
        bound_grant = live.grant_for(right)
        if self.policy.enforce_authority_version and grant.grant_id != bound_grant:
            raise AuthorizationRefused(
                f"{right.value} is bound to authority grant {bound_grant!r}, "
                f"not to {grant.grant_id!r}",
                reason_code=OversightRefusal.STALE_AUTHORITY,
            )
        return live, grant

    def _unit_of(self, envelope: EvidenceEnvelope) -> str | None:
        """The exact oversight scope key an evidence stream is assigned to.

        The governed mapping names a *full* scope key (`region:org:unit`), not
        a bare unit label: two organizations may name their oversight units
        identically, and a bare label would let one organization's mandate
        reach the other's unscoped evidence.
        """
        return self.evidence_units.get(
            f"{envelope.reference.plane.value}:{envelope.reference.stream_id}"
        )

    def _visibility_refusal(
        self, envelope: EvidenceEnvelope, mandate: OversightMandate, scope: OversightScope
    ) -> OversightRefusal | None:
        """Why one envelope is outside this exact mandate, or None if inside.

        Voting boundary, evidence plane, oversight unit and organization scope
        are each a distinct containment rule that can fail on its own, so each
        failure carries its own reason code: a reviewer must be able to tell
        "not your unit" from "not your organization" from "not your plane".
        """
        if self.policy.enforce_voting_boundary and envelope.domain is EvidenceDomain.VOTING:
            return OversightRefusal.VOTING_BOUNDARY
        if self.policy.enforce_plane_mandate and envelope.reference.plane not in mandate.planes:
            return OversightRefusal.PLANE_NOT_IN_MANDATE
        if self.policy.enforce_unit_scope:
            assigned = self._unit_of(envelope)
            if assigned is None or assigned != scope.key:
                return OversightRefusal.WRONG_UNIT_SCOPE
        # CTRL-02/CTRL-04 evidence is scoped "region:org"; CTRL-03 lifecycle
        # evidence is bound through its governed unit mapping instead of a
        # scope string, so an unscoped record is admitted only when its unit
        # mapping already placed it inside this mandate.
        if self.policy.enforce_organization_scope and envelope.scope_key not in {
            scope.organization_key,
            "UNSCOPED",
        }:
            return OversightRefusal.WRONG_ORGANIZATION_SCOPE
        return None

    def _visible(
        self, envelope: EvidenceEnvelope, mandate: OversightMandate, scope: OversightScope
    ) -> bool:
        return self._visibility_refusal(envelope, mandate, scope) is None

    # -- evidence discovery --------------------------------------------------

    def _all_envelopes(self) -> tuple[tuple[EvidenceEnvelope, ...], dict[str, str]]:
        return collect(self._sources.values())

    def search(
        self,
        *,
        actor_ref: str,
        session_id: str,
        query: EvidenceQuery,
        now: datetime,
    ) -> dict[str, Any]:
        """Exact-scope, bounded evidence search.

        A query is always anchored on an exact scope; there is no route that
        searches everything. Unavailable planes are reported as unavailable,
        never as an absence of evidence.
        """
        moment = self._time(now)
        correlation = self._next_id("AQ")
        with self._lock:
            try:
                if self.policy.enforce_query_bounds and query.limit > MAX_QUERY_LIMIT:
                    raise AuthorizationRefused(
                        "query limit exceeds the governed bound",
                        reason_code=OversightRefusal.QUERY_LIMIT,
                    )
                self._session(session_id, actor_ref, moment)
                mandate, grant = self._resolve_mandate(
                    actor_ref=actor_ref, scope=query.scope, right=AuditRight.READ, now=moment
                )
                envelopes, unavailable = self._all_envelopes()
            except AuthorizationRefused as exc:
                self._decide(
                    act="EVIDENCE.SEARCH",
                    actor_ref=actor_ref,
                    allowed=False,
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.EVIDENCE.SEARCH",
                    scope_key=query.scope.key,
                    object_ref="evidence",
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            planes = (query.planes & mandate.planes) if query.planes else mandate.planes
            matched: list[EvidenceEnvelope] = []
            for envelope in envelopes:
                if envelope.reference.plane not in planes:
                    continue
                if not self._visible(envelope, mandate, query.scope):
                    continue
                if query.correlation_ref and envelope.correlation_ref != query.correlation_ref:
                    continue
                if query.action_code and envelope.action_code != query.action_code:
                    continue
                if query.actor_ref and envelope.actor_ref != query.actor_ref:
                    continue
                if query.object_ref and envelope.object_ref != query.object_ref:
                    continue
                if query.result and envelope.result != query.result:
                    continue
                matched.append(envelope)
            truncated = len(matched) > query.limit
            page = matched[: query.limit]
            self._decide(
                act="EVIDENCE.SEARCH",
                actor_ref=actor_ref,
                allowed=True,
                reason="AUD_AUTHORIZED",
                correlation=correlation,
                mandate=mandate,
                grant=grant,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.EVIDENCE.SEARCH",
                scope_key=query.scope.key,
                object_ref="evidence",
                result="READ",
                reason_code="AUD_AUTHORIZED",
                correlation=correlation,
                attributes={
                    "planes": ",".join(sorted(p.value for p in planes)),
                    "matched": len(page),
                    "truncated": truncated,
                    "unavailable_planes": ",".join(sorted(unavailable)) or "NONE",
                    "mandate": mandate.competence_ref,
                },
            )
            self._persist()
            return {
                "query_id": correlation,
                "scope": query.scope.key,
                "records": [e.as_dict() for e in page],
                "matched": len(page),
                "truncated": truncated,
                "limit": query.limit,
                "unavailable_planes": unavailable,
                "integrity_summary": self._integrity_summary(page),
            }

    @staticmethod
    def _integrity_summary(envelopes: Sequence[EvidenceEnvelope]) -> dict[str, int]:
        summary: dict[str, int] = {}
        for envelope in envelopes:
            key = envelope.integrity.state.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def evidence(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        reference_key: str,
        now: datetime,
    ) -> EvidenceEnvelope:
        """Open exactly one evidence record, integrity verified, in scope."""
        moment = self._time(now)
        correlation = self._next_id("AO")
        with self._lock:
            try:
                self._session(session_id, actor_ref, moment)
                plane_value = reference_key.split(":", 1)[0]
                try:
                    plane = EvidencePlane(plane_value)
                except ValueError as exc:
                    raise AuthorizationRefused(
                        "unknown evidence plane", reason_code=OversightRefusal.UNKNOWN_EVIDENCE
                    ) from exc
                mandate, grant = self._resolve_mandate(
                    actor_ref=actor_ref,
                    scope=scope,
                    right=AuditRight.READ,
                    now=moment,
                    plane=plane,
                )
                envelope = self._locate(reference_key, mandate, scope)
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.EVIDENCE.OPEN",
                    scope_key=scope.key,
                    object_ref=reference_key,
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.EVIDENCE.OPEN",
                scope_key=scope.key,
                object_ref=reference_key,
                result="READ",
                reason_code="AUD_AUTHORIZED",
                correlation=correlation,
                attributes={
                    "integrity": envelope.integrity.state.value,
                    "event_hash": envelope.reference.event_hash,
                },
            )
            self._persist()
            return envelope

    def _locate(
        self, reference_key: str, mandate: OversightMandate, scope: OversightScope
    ) -> EvidenceEnvelope:
        envelopes, unavailable = self._all_envelopes()
        for envelope in envelopes:
            if envelope.reference.key != reference_key:
                continue
            why = self._visibility_refusal(envelope, mandate, scope)
            if why is not None:
                raise AuthorizationRefused(
                    f"evidence {reference_key} is outside this oversight mandate ({why.value})",
                    reason_code=why,
                )
            return envelope
        if unavailable and self.policy.fail_closed_on_source_unavailable:
            raise AuthorizationRefused(
                f"source planes unavailable: {sorted(unavailable)}; evidence cannot be shown",
                reason_code=OversightRefusal.SOURCE_UNAVAILABLE,
            )
        raise AuthorizationRefused(
            f"no evidence with reference {reference_key}",
            reason_code=OversightRefusal.UNKNOWN_EVIDENCE,
        )

    def verify_evidence(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        reference_key: str,
        now: datetime,
    ) -> dict[str, Any]:
        """Independently re-derive and report one record's integrity."""
        envelope = self.evidence(
            actor_ref=actor_ref,
            session_id=session_id,
            scope=scope,
            reference_key=reference_key,
            now=now,
        )
        integrity = envelope.integrity
        if not self.policy.enforce_integrity_verification:
            # The un-governed path: report what the record claims about
            # itself. A candidate must never run this way, and the anti-cheat
            # corpus flips the obligation to prove the difference is visible.
            return {
                "reference": envelope.reference.as_dict(),
                "state": integrity.state.value,
                "trustworthy": True,
                "algorithm": integrity.algorithm,
                "recorded_hash": integrity.recorded_hash,
                "recomputed_hash": integrity.recorded_hash,
                "sequence": integrity.sequence,
                "detail": "integrity verification disabled",
                "verified_by": "RECORD_SELF_REPORT",
            }
        return {
            "reference": envelope.reference.as_dict(),
            "state": integrity.state.value,
            "trustworthy": integrity.trustworthy,
            "algorithm": integrity.algorithm,
            "recorded_hash": integrity.recorded_hash,
            "recomputed_hash": integrity.recomputed_hash,
            "sequence": integrity.sequence,
            "detail": integrity.detail,
            "verified_by": "CTRL-05 independent re-derivation",
        }

    def action_chain(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        correlation_ref: str,
        now: datetime,
    ) -> dict[str, Any]:
        """The request → approval → execution → result chain for one action."""
        moment = self._time(now)
        correlation = self._next_id("AC")
        with self._lock:
            try:
                self._session(session_id, actor_ref, moment)
                mandate, grant = self._resolve_mandate(
                    actor_ref=actor_ref,
                    scope=scope,
                    right=AuditRight.CORRELATE,
                    now=moment,
                    plane=EvidencePlane.CTRL04,
                )
                if not correlation_ref or correlation_ref in COARSE_TARGETS:
                    raise AuthorizationRefused(
                        "an action chain must be anchored on an exact correlation id",
                        reason_code=OversightRefusal.UNBOUNDED_QUERY,
                    )
                envelopes, unavailable = self._all_envelopes()
                if unavailable and self.policy.fail_closed_on_source_unavailable:
                    raise AuthorizationRefused(
                        f"source planes unavailable: {sorted(unavailable)}",
                        reason_code=OversightRefusal.SOURCE_UNAVAILABLE,
                    )
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CHAIN.OPEN",
                    scope_key=scope.key,
                    object_ref=correlation_ref,
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            chain = [
                e
                for e in envelopes
                if e.correlation_ref == correlation_ref and self._visible(e, mandate, scope)
            ]
            chain.sort(key=lambda e: (e.reference.plane.value, e.reference.sequence))
            # The composed CTRL-04 action record is the richest artefact on
            # this route, so it is gated by the *same* visibility rule as the
            # chain itself: no visible step, no record. Without this the
            # anchor id alone — and action ids are sequential — would hand out
            # another organization's operational history.
            anchored = [e for e in envelopes if e.correlation_ref == correlation_ref]
            outside = [self._visibility_refusal(e, mandate, scope) for e in anchored]
            composed = None
            source = self._source(EvidencePlane.CTRL04)
            if chain and not any(outside) and source is not None:
                if not hasattr(source, "action_record"):
                    composed = None
                else:
                    composed = source.action_record(correlation_ref)
                    if composed is not None and self.policy.enforce_secret_redaction:
                        composed = _scrub_structure(composed)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.CHAIN.OPEN",
                scope_key=scope.key,
                object_ref=correlation_ref,
                result="READ",
                reason_code="AUD_AUTHORIZED",
                correlation=correlation,
                attributes={"steps": len(chain)},
            )
            self._persist()
            return {
                "correlation_ref": correlation_ref,
                "scope": scope.key,
                "steps": [e.as_dict() for e in chain],
                "composed_action_record": composed,
                "integrity_summary": self._integrity_summary(chain),
            }

    def correlation_graph(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        anchor: str,
        depth: int = 1,
        now: datetime,
    ) -> CorrelationGraph:
        """A bounded correlation graph anchored on one governed identifier.

        The graph never introduces a person node: nodes are evidence
        references and edges are governed relations between them.
        """
        moment = self._time(now)
        correlation = self._next_id("AG")
        with self._lock:
            try:
                self._session(session_id, actor_ref, moment)
                mandate, grant = self._resolve_mandate(
                    actor_ref=actor_ref, scope=scope, right=AuditRight.CORRELATE, now=moment
                )
                if not anchor or anchor in COARSE_TARGETS:
                    raise AuthorizationRefused(
                        "a correlation graph must be anchored on an exact identifier",
                        reason_code=OversightRefusal.UNBOUNDED_QUERY,
                    )
                if self.policy.enforce_graph_bounds and not 1 <= depth <= MAX_GRAPH_DEPTH:
                    raise AuthorizationRefused(
                        f"graph depth must be within 1..{MAX_GRAPH_DEPTH}",
                        reason_code=OversightRefusal.GRAPH_LIMIT,
                    )
                if anchor.lower() in PERSON_IDENTIFIER_FIELDS:
                    raise AuthorizationRefused(
                        "a correlation graph may not be anchored on a person identifier",
                        reason_code=OversightRefusal.PERSON_IDENTIFIER,
                    )
                envelopes, unavailable = self._all_envelopes()
                if unavailable and self.policy.fail_closed_on_source_unavailable:
                    # A graph drawn over an unreadable plane looks like "no
                    # correlated evidence". That is the one conclusion a
                    # reviewer must never be handed by accident.
                    raise AuthorizationRefused(
                        f"source planes unavailable: {sorted(unavailable)}; "
                        f"a correlation graph would be silently incomplete",
                        reason_code=OversightRefusal.SOURCE_UNAVAILABLE,
                    )
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CORRELATION.GRAPH",
                    scope_key=scope.key,
                    object_ref=anchor,
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            visible = [e for e in envelopes if self._visible(e, mandate, scope)]
            seeds = [e for e in visible if e.correlation_ref == anchor]
            frontier = {anchor}
            reached: dict[str, EvidenceEnvelope] = {e.reference.key: e for e in seeds}
            for _ in range(depth - 1):
                next_frontier: set[str] = set()
                for envelope in list(reached.values()):
                    for other in visible:
                        if other.object_ref and other.object_ref == envelope.object_ref:
                            next_frontier.add(other.correlation_ref)
                frontier |= next_frontier
                for envelope in visible:
                    if envelope.correlation_ref in frontier:
                        reached[envelope.reference.key] = envelope
            ordered = sorted(
                reached.values(), key=lambda e: (e.reference.plane.value, e.reference.sequence)
            )
            limit = MAX_GRAPH_NODES if self.policy.enforce_graph_bounds else len(ordered) or 1
            truncated = len(ordered) > limit
            nodes = ordered[:limit]
            edges: list[dict[str, str]] = []
            for index, envelope in enumerate(nodes):
                if envelope.correlation_ref == anchor:
                    edges.append(
                        {
                            "from": anchor,
                            "to": envelope.reference.key,
                            "relation": "same-correlation",
                        }
                    )
                if index and nodes[index - 1].reference.plane is envelope.reference.plane:
                    edges.append(
                        {
                            "from": nodes[index - 1].reference.key,
                            "to": envelope.reference.key,
                            "relation": "chain-successor",
                        }
                    )
            graph = CorrelationGraph(
                anchor=anchor,
                scope_key=scope.key,
                nodes=tuple(
                    {
                        "reference": e.reference.key,
                        "plane": e.reference.plane.value,
                        "action_code": e.action_code,
                        "result": e.result,
                        "occurred_at": e.occurred_at,
                        "integrity": e.integrity.state.value,
                    }
                    for e in nodes
                ),
                edges=tuple(edges),
                truncated=truncated,
                node_limit=limit,
                depth=depth,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.CORRELATION.GRAPH",
                scope_key=scope.key,
                object_ref=anchor,
                result="READ",
                reason_code="AUD_AUTHORIZED",
                correlation=correlation,
                attributes={"nodes": len(graph.nodes), "truncated": truncated, "depth": depth},
            )
            self._persist()
            return graph

    def voting_verification_status(
        self, *, actor_ref: str, session_id: str, scope: OversightScope, now: datetime
    ) -> dict[str, Any]:
        """Reference-only status of externally anchored voting verification.

        This is the entire voting-domain surface of CTRL-05: a published
        interface identity and its digest. No identity, no ballot, no control.
        """
        moment = self._time(now)
        correlation = self._next_id("AV")
        with self._lock:
            try:
                self._session(session_id, actor_ref, moment)
                _mandate, grant = self._resolve_mandate(
                    actor_ref=actor_ref, scope=scope, right=AuditRight.READ, now=moment
                )
                if self.voting_verification is None:
                    raise AuthorizationRefused(
                        "no voting verification interface is configured",
                        reason_code=OversightRefusal.SOURCE_UNAVAILABLE,
                    )
                references = self.voting_verification.references()
            except SourceUnavailable as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.VOTING.VERIFICATION",
                    scope_key=scope.key,
                    object_ref="voting-verification",
                    reason=OversightRefusal.SOURCE_UNAVAILABLE,
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.VOTING.VERIFICATION",
                    scope_key=scope.key,
                    object_ref="voting-verification",
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.VOTING.VERIFICATION",
                scope_key=scope.key,
                object_ref="voting-verification",
                result="READ",
                reason_code="AUD_AUTHORIZED",
                correlation=correlation,
                attributes={"interfaces": len(references)},
            )
            self._persist()
            return {
                "interfaces": [r.as_dict() for r in references],
                "voting_internal_access": "NONE",
                "voting_control_path": "NONE",
                "member_identifiers_exposed": 0,
            }

    # -- review lifecycle ----------------------------------------------------

    def _mutation_preflight(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        scope: OversightScope,
        right: AuditRight,
        now: datetime,
    ) -> tuple[OversightSession, OversightMandate, AuthorityGrant]:
        session = self._session(session_id, actor_ref, now)
        self._check_csrf(session, csrf_token)
        mandate, grant = self._resolve_mandate(
            actor_ref=actor_ref, scope=scope, right=right, now=now
        )
        return session, mandate, grant

    def _scope_of_ticket(self, ticket_id: str) -> OversightScope:
        """The exact scope a prepared ticket belongs to.

        A replayed ticket act must still name a real ticket: the ticket is
        server-held, so this is a lookup, not a client assertion.
        """
        ticket = self._tickets.get(str(ticket_id))
        if ticket is None:
            raise AuthorizationRefused(
                f"no prepared act {ticket_id}", reason_code=OversightRefusal.NOT_FOUND
            )
        return self._case(str(ticket["case_id"])).scope

    def _replay(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        key: str,
        act: str,
        journal_act: str,
        scope: OversightScope,
        right: AuditRight,
        now: datetime,
    ) -> str | None:
        """Resolve an idempotent replay under live authority, and journal it.

        An idempotent retry returns the *same* governed object, but it is not
        a free pass: the session, its CSRF token and the live mandate carrying
        the right are all re-checked, and the replay is appended to the
        journal. Without this a revoked session could still be handed the
        object its earlier self produced, leaving no evidence that it asked.
        """
        existing = self._idempotent(actor_ref, key, act)
        if existing is None:
            return None
        session = self._session(session_id, actor_ref, now)
        self._check_csrf(session, csrf_token)
        mandate, grant = self._resolve_mandate(
            actor_ref=actor_ref, scope=scope, right=right, now=now
        )
        self._decide(
            act=f"{act}.REPLAY",
            actor_ref=actor_ref,
            allowed=True,
            reason=OversightRefusal.REPLAYED_REQUEST.value,
            correlation=existing,
            mandate=mandate,
            grant=grant,
        )
        self._record(
            now=now,
            actor_ref=actor_ref,
            authority_basis=f"{grant.grant_id}@v{grant.version}",
            act=journal_act,
            scope_key=scope.key,
            object_ref=existing,
            result="REPLAYED",
            reason_code=OversightRefusal.REPLAYED_REQUEST.value,
            correlation=existing,
            attributes={"idempotency_key": key, "mandate": mandate.competence_ref},
        )
        self._persist()
        return existing

    def _idempotent(self, actor_ref: str, key: str, act: str) -> str | None:
        if not self.policy.enforce_idempotency:
            return None
        return self._idempotency.get(f"{act}:{actor_ref}:{key}")

    def _remember(self, actor_ref: str, key: str, act: str, result_id: str) -> None:
        self._idempotency[f"{act}:{actor_ref}:{key}"] = result_id

    def _scope_key_of(self, case_id: str) -> str:
        """The case's scope key, or UNKNOWN when the case does not exist.

        A refusal handler must be able to name a scope even when the failure
        *was* that the case could not be resolved.
        """
        case = self._cases.get(case_id)
        return "UNKNOWN" if case is None else case.scope.key

    def _case(self, case_id: str) -> ReviewCase:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                f"unknown review case {case_id}", reason_code=OversightRefusal.UNKNOWN_CASE
            ) from exc

    def _require_current_evidence(
        self, reference_key: str, mandate: OversightMandate, scope: OversightScope
    ) -> EvidenceEnvelope:
        """Locate evidence and refuse to build on anything not verified.

        A finding or attestation must rest on a record whose integrity CTRL-05
        has independently re-derived. Untrustworthy evidence is surfaced, never
        silently accepted as a basis for a governed conclusion.
        """
        envelope = self._locate(reference_key, mandate, scope)
        if (
            self.policy.require_trustworthy_evidence_for_findings
            and not envelope.integrity.trustworthy
        ):
            raise AuthorizationRefused(
                f"evidence {reference_key} is {envelope.integrity.state.value}; "
                f"it cannot carry a governed conclusion",
                reason_code=OversightRefusal.EVIDENCE_UNTRUSTWORTHY,
            )
        return envelope

    def open_case(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        scope: OversightScope,
        title: str,
        evidence_refs: Sequence[str],
        idempotency_key: str,
        now: datetime,
    ) -> ReviewCase:
        moment = self._time(now)
        with self._lock:
            correlation = self._next_id("ARC")
            try:
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="OPEN",
                    journal_act="AUDIT.CASE.OPEN",
                    scope=scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    return self._cases[existing]
                _require_id(idempotency_key, "idempotency_key")
                if not evidence_refs:
                    raise AuthorizationRefused(
                        "a review case must name the evidence it reviews",
                        reason_code=OversightRefusal.FINDING_WITHOUT_EVIDENCE,
                    )
                _, mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                for reference in evidence_refs:
                    self._locate(reference, mandate, scope)
            except (ValueError, TypeError) as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.OPEN",
                    scope_key=scope.key,
                    object_ref="case",
                    reason=OversightRefusal.PARAMETER_INVALID,
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            except AuthorizationRefused as exc:
                self._decide(
                    act="CASE.OPEN",
                    actor_ref=actor_ref,
                    allowed=False,
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.OPEN",
                    scope_key=scope.key,
                    object_ref="case",
                    reason=str(exc.reason_code),
                    correlation=correlation,
                    detail=str(exc),
                ) from exc
            case = ReviewCase(
                case_id=self._next_id("CASE"),
                title=scrub_text(str(title))[:256],
                scope=scope,
                opened_by=actor_ref,
                opened_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=f"{grant.grant_id}@v{grant.version}",
                state=ReviewState.OPENED,
                version=1,
                evidence_refs=tuple(evidence_refs),
            )
            self._cases[case.case_id] = case
            self._remember(actor_ref, idempotency_key, "OPEN", case.case_id)
            self._decide(
                act="CASE.OPEN",
                actor_ref=actor_ref,
                allowed=True,
                reason="AUD_AUTHORIZED",
                correlation=case.case_id,
                mandate=mandate,
                grant=grant,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=case.authority_ref,
                act="AUDIT.CASE.OPEN",
                scope_key=scope.key,
                object_ref=case.case_id,
                result="OPENED",
                reason_code="AUD_AUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "evidence_count": len(case.evidence_refs),
                    "mandate": mandate.competence_ref,
                    "title": case.title,
                    "content_digest": _content_digest(case.title, case.scope.key, case.opened_by),
                },
            )
            self._persist()
            return case

    def clarify(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        case_id: str,
        text: str,
        evidence_ref: str | None,
        idempotency_key: str,
        now: datetime,
    ) -> Clarification:
        """Add an annotation. The source record is never touched."""
        moment = self._time(now)
        with self._lock:
            try:
                case = self._case(case_id)
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="CLARIFY",
                    journal_act="AUDIT.CASE.CLARIFY",
                    scope=case.scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    return self._clarifications[existing]
                _, mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=case.scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if case.state is ReviewState.CLOSED:
                    raise AuthorizationRefused(
                        "a closed case takes no further annotation",
                        reason_code=OversightRefusal.WRONG_STATE,
                    )
                envelope = None
                if evidence_ref is not None:
                    envelope = self._locate(evidence_ref, mandate, case.scope)
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.CLARIFY",
                    scope_key=self._scope_key_of(case_id),
                    object_ref=case_id,
                    reason=str(exc.reason_code),
                    correlation=case_id,
                    detail=str(exc),
                ) from exc
            clarification = Clarification(
                clarification_id=self._next_id("CLR"),
                case_id=case_id,
                text=scrub_text(str(text))[:2048],
                author_ref=actor_ref,
                created_at=moment,
                evidence_reference=None if envelope is None else envelope.reference,
            )
            self._clarifications[clarification.clarification_id] = clarification
            self._cases[case_id] = replace(
                case,
                clarification_ids=(*case.clarification_ids, clarification.clarification_id),
                state=ReviewState.IN_REVIEW if case.state is ReviewState.OPENED else case.state,
                version=case.version + 1,
            )
            self._remember(actor_ref, idempotency_key, "CLARIFY", clarification.clarification_id)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.CASE.CLARIFY",
                scope_key=case.scope.key,
                object_ref=case_id,
                result="ANNOTATED",
                reason_code="AUD_AUTHORIZED",
                correlation=case_id,
                attributes={
                    "clarification_id": clarification.clarification_id,
                    "evidence_ref": evidence_ref or "NONE",
                    "source_evidence_mutated": "NO",
                },
            )
            self._persist()
            return clarification

    # -- two-phase commit: prepare, then reauthorize at the act ---------------

    def prepare(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        case_id: str,
        act: str,
        right: AuditRight,
        now: datetime,
    ) -> dict[str, Any]:
        """Phase one of a governed review act.

        The ticket captures exactly what the reviewer saw: the mandate, the
        authority version, the case version and the content digest of every
        evidence record in the case. Phase two re-derives all of it. Nothing in
        the ticket is authority; it is a statement of what must still be true.
        """
        moment = self._time(now)
        with self._lock:
            try:
                case = self._case(case_id)
                _, mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=case.scope,
                    right=right,
                    now=moment,
                )
                digests = {}
                for reference in case.evidence_refs:
                    envelope = self._locate(reference, mandate, case.scope)
                    digests[reference] = envelope.reference.content_digest
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act=f"AUDIT.{act}.PREPARE",
                    scope_key=self._cases[case_id].scope.key
                    if case_id in self._cases
                    else "UNKNOWN",
                    object_ref=case_id,
                    reason=str(exc.reason_code),
                    correlation=case_id,
                    detail=str(exc),
                ) from exc
            ticket_id = self._next_id("TKT")
            ticket: dict[str, Any] = {
                "ticket_id": ticket_id,
                "act": act,
                "case_id": case_id,
                "actor_ref": actor_ref,
                "mandate_id": mandate.mandate_id,
                "mandate_ref": mandate.competence_ref,
                "authority_grant_id": grant.grant_id,
                "authority_version": grant.version,
                "case_version": case.version,
                "evidence_digests": digests,
                "prepared_at": moment.isoformat(),
                "expires_at": (moment + timedelta(minutes=10)).isoformat(),
                "consumed": False,
            }
            self._tickets[ticket_id] = ticket
            self._persist()
            return dict(ticket)

    def _reauthorize(
        self,
        *,
        ticket_id: str,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        act: str,
        right: AuditRight,
        moment: datetime,
    ) -> tuple[dict[str, Any], ReviewCase, OversightMandate, AuthorityGrant]:
        """Phase two: re-derive every element of the decision at the act.

        Session, CSRF, mandate, authority version, case version and evidence
        content are all re-checked against the live state. Any drift fails
        closed; the ticket is consumed exactly once.
        """
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise AuthorizationRefused(
                "unknown preparation ticket", reason_code=OversightRefusal.NOT_FOUND
            )
        if ticket["consumed"]:
            raise AuthorizationRefused(
                "preparation ticket already used; no duplicate review effect",
                reason_code=OversightRefusal.REPLAYED_REQUEST,
            )
        if ticket["actor_ref"] != actor_ref or ticket["act"] != act:
            raise AuthorizationRefused(
                "ticket does not match this act", reason_code=OversightRefusal.PARAMETER_INVALID
            )
        case = self._case(ticket["case_id"])
        if not self.policy.commit_time_reauthorization:
            grant = self.authorities.grant(ticket["authority_grant_id"])
            mandate = self._mandates[ticket["mandate_id"]]
            return ticket, case, mandate, grant
        if moment >= _dt(ticket["expires_at"]):
            raise AuthorizationRefused(
                "preparation expired before the act", reason_code=OversightRefusal.STALE_AUTHORITY
            )
        _, mandate, grant = self._mutation_preflight(
            actor_ref=actor_ref,
            session_id=session_id,
            csrf_token=csrf_token,
            scope=case.scope,
            right=right,
            now=moment,
        )
        if mandate.mandate_id != ticket["mandate_id"]:
            raise AuthorizationRefused(
                "the mandate changed between preparation and act",
                reason_code=OversightRefusal.STALE_AUTHORITY,
            )
        if (
            grant.grant_id != ticket["authority_grant_id"]
            or grant.version != ticket["authority_version"]
        ):
            raise AuthorizationRefused(
                "the backing authority changed between preparation and act",
                reason_code=OversightRefusal.STALE_AUTHORITY,
            )
        if self.policy.enforce_case_version and case.version != ticket["case_version"]:
            raise AuthorizationRefused(
                f"case moved from version {ticket['case_version']} to {case.version}",
                reason_code=OversightRefusal.STALE_CASE_VERSION,
            )
        if self.policy.enforce_evidence_divergence_check:
            for reference, digest in ticket["evidence_digests"].items():
                envelope = self._locate(reference, mandate, case.scope)
                if envelope.reference.content_digest != digest:
                    raise AuthorizationRefused(
                        f"evidence {reference} diverged since it was reviewed",
                        reason_code=OversightRefusal.EVIDENCE_DIVERGED,
                    )
        return ticket, case, mandate, grant

    def dispose(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        ticket_id: str,
        disposition: ReviewState,
        rationale: str,
        idempotency_key: str,
        now: datetime,
    ) -> ReviewDisposition:
        """Record an append-only disposition step under commit-time reauth."""
        moment = self._time(now)
        with self._lock:
            try:
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="DISPOSE",
                    journal_act="AUDIT.CASE.DISPOSE",
                    scope=self._scope_of_ticket(ticket_id),
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    return self._dispositions[existing]
                if disposition not in DISPOSITION_STATES:
                    raise AuthorizationRefused(
                        f"{disposition.value} is not a disposition",
                        reason_code=OversightRefusal.PARAMETER_INVALID,
                    )
                ticket, case, mandate, grant = self._reauthorize(
                    ticket_id=ticket_id,
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    act="DISPOSE",
                    right=AuditRight.REVIEW,
                    moment=moment,
                )
                if case.state is ReviewState.CLOSED:
                    raise AuthorizationRefused(
                        "a closed case takes no further disposition",
                        reason_code=OversightRefusal.WRONG_STATE,
                    )
            except AuthorizationRefused as exc:
                self._decide(
                    act="CASE.DISPOSE",
                    actor_ref=actor_ref,
                    allowed=False,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.DISPOSE",
                    scope_key="UNKNOWN",
                    object_ref=ticket_id,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                ) from exc
            previous = case.disposition_ids[-1] if case.disposition_ids else None
            record = ReviewDisposition(
                disposition_id=self._next_id("DSP"),
                case_id=case.case_id,
                state=disposition,
                rationale=scrub_text(str(rationale))[:2048],
                decided_by=actor_ref,
                decided_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=f"{grant.grant_id}@v{grant.version}",
                supersedes=previous,
            )
            self._dispositions[record.disposition_id] = record
            self._cases[case.case_id] = replace(
                case,
                state=disposition,
                version=case.version + 1,
                disposition_ids=(*case.disposition_ids, record.disposition_id)
                if self.policy.enforce_append_only_history
                else (record.disposition_id,),
            )
            ticket["consumed"] = True
            self._remember(actor_ref, idempotency_key, "DISPOSE", record.disposition_id)
            self._decide(
                act="CASE.DISPOSE",
                actor_ref=actor_ref,
                allowed=True,
                reason="AUD_REAUTHORIZED",
                correlation=case.case_id,
                mandate=mandate,
                grant=grant,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=record.authority_ref,
                act="AUDIT.CASE.DISPOSE",
                scope_key=case.scope.key,
                object_ref=case.case_id,
                result=disposition.value,
                reason_code="AUD_REAUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "disposition_id": record.disposition_id,
                    "supersedes": previous or "NONE",
                    "case_version": case.version + 1,
                    "prior_dispositions_preserved": len(case.disposition_ids),
                    "content_digest": _content_digest(
                        record.state.value,
                        record.rationale,
                        record.decided_by,
                        record.supersedes,
                    ),
                },
            )
            self._persist()
            return record

    def raise_finding(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        ticket_id: str,
        severity: FindingSeverity,
        summary: str,
        evidence_ref: str,
        idempotency_key: str,
        now: datetime,
    ) -> ReviewFinding:
        """Raise a finding bound to one exact, verified evidence reference."""
        moment = self._time(now)
        with self._lock:
            try:
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="FINDING",
                    journal_act="AUDIT.FINDING.RAISE",
                    scope=self._scope_of_ticket(ticket_id),
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    return self._findings[existing]
                if self.policy.enforce_finding_evidence_reference and not evidence_ref:
                    raise AuthorizationRefused(
                        "a finding must name the exact evidence it rests on",
                        reason_code=OversightRefusal.FINDING_WITHOUT_EVIDENCE,
                    )
                ticket, case, mandate, grant = self._reauthorize(
                    ticket_id=ticket_id,
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    act="FINDING",
                    right=AuditRight.REVIEW,
                    moment=moment,
                )
                if case.state is ReviewState.CLOSED:
                    raise AuthorizationRefused(
                        "a closed case takes no further finding",
                        reason_code=OversightRefusal.WRONG_STATE,
                    )
                if self.policy.enforce_finding_evidence_reference and (
                    evidence_ref not in case.evidence_refs
                ):
                    raise AuthorizationRefused(
                        "the finding's evidence is not part of this case",
                        reason_code=OversightRefusal.FINDING_WITHOUT_EVIDENCE,
                    )
                envelope = self._require_current_evidence(evidence_ref, mandate, case.scope)
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.FINDING.RAISE",
                    scope_key="UNKNOWN",
                    object_ref=evidence_ref or "NONE",
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                ) from exc
            finding = ReviewFinding(
                finding_id=self._next_id("FND"),
                case_id=case.case_id,
                severity=severity,
                summary=scrub_text(str(summary))[:1024],
                evidence_reference=envelope.reference,
                evidence_content_digest=envelope.reference.content_digest,
                raised_by=actor_ref,
                raised_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=f"{grant.grant_id}@v{grant.version}",
            )
            self._findings[finding.finding_id] = finding
            self._cases[case.case_id] = replace(
                case,
                state=ReviewState.FINDING_RAISED,
                version=case.version + 1,
                finding_ids=(*case.finding_ids, finding.finding_id),
            )
            ticket["consumed"] = True
            self._remember(actor_ref, idempotency_key, "FINDING", finding.finding_id)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=finding.authority_ref,
                act="AUDIT.FINDING.RAISE",
                scope_key=case.scope.key,
                object_ref=case.case_id,
                result="FINDING_RAISED",
                reason_code="AUD_REAUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "finding_id": finding.finding_id,
                    "severity": severity.value,
                    "evidence_reference": envelope.reference.key,
                    "evidence_event_hash": envelope.reference.event_hash,
                    "evidence_content_digest": envelope.reference.content_digest,
                    "evidence_integrity": envelope.integrity.state.value,
                    "content_digest": _content_digest(
                        finding.severity.value,
                        finding.summary,
                        finding.raised_by,
                        finding.evidence_reference.key,
                    ),
                },
            )
            self._persist()
            return finding

    def dispute_finding(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        finding_id: str,
        rationale: str,
        idempotency_key: str,
        now: datetime,
    ) -> tuple[ReviewFinding, ReviewFinding]:
        """Dispute a finding without erasing it.

        The original finding is preserved verbatim and marked `DISPUTED`; the
        dispute is a new, separate record that points back at it. Both remain
        readable forever, which is what makes a contested review auditable.
        """
        moment = self._time(now)
        with self._lock:
            try:
                original_for_replay = self._findings.get(finding_id)
                if original_for_replay is None:
                    raise AuthorizationRefused(
                        f"no finding {finding_id}", reason_code=OversightRefusal.NOT_FOUND
                    )
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="DISPUTE",
                    journal_act="AUDIT.FINDING.DISPUTE",
                    scope=self._case(original_for_replay.case_id).scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    dispute_record = self._findings[existing]
                    disputed_id = dispute_record.dispute_ref or finding_id
                    return self._findings[disputed_id], dispute_record
                original = self._findings.get(finding_id)
                if original is None:
                    raise AuthorizationRefused(
                        "unknown finding", reason_code=OversightRefusal.NOT_FOUND
                    )
                case = self._case(original.case_id)
                _, mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=case.scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.FINDING.DISPUTE",
                    scope_key="UNKNOWN",
                    object_ref=finding_id,
                    reason=str(exc.reason_code),
                    correlation=finding_id,
                    detail=str(exc),
                ) from exc
            dispute = ReviewFinding(
                finding_id=self._next_id("FND"),
                case_id=case.case_id,
                severity=original.severity,
                summary=scrub_text(f"DISPUTE of {original.finding_id}: {rationale}")[:1024],
                evidence_reference=original.evidence_reference,
                evidence_content_digest=original.evidence_content_digest,
                raised_by=actor_ref,
                raised_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=f"{grant.grant_id}@v{grant.version}",
                state=FindingState.RAISED,
                dispute_ref=original.finding_id,
            )
            # The original is *annotated*, never removed or rewritten in
            # substance: severity, summary, evidence and authorship stand.
            if self.policy.enforce_append_only_history:
                self._findings[original.finding_id] = replace(
                    original, state=FindingState.DISPUTED, dispute_ref=dispute.finding_id
                )
            else:
                del self._findings[original.finding_id]
            self._findings[dispute.finding_id] = dispute
            self._cases[case.case_id] = replace(
                case,
                version=case.version + 1,
                finding_ids=(*case.finding_ids, dispute.finding_id)
                if self.policy.enforce_append_only_history
                else (
                    *(f for f in case.finding_ids if f != original.finding_id),
                    dispute.finding_id,
                ),
            )
            self._remember(actor_ref, idempotency_key, "DISPUTE", dispute.finding_id)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=dispute.authority_ref,
                act="AUDIT.FINDING.DISPUTE",
                scope_key=case.scope.key,
                object_ref=case.case_id,
                result="DISPUTED",
                reason_code="AUD_AUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "original_finding": original.finding_id,
                    "dispute_finding": dispute.finding_id,
                    "finding_id": dispute.finding_id,
                    "content_digest": _content_digest(
                        dispute.severity.value,
                        dispute.summary,
                        dispute.raised_by,
                        dispute.evidence_reference.key,
                    ),
                    "original_preserved": "YES",
                },
            )
            self._persist()
            return self._findings[original.finding_id], dispute

    def link_remediation(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        case_id: str,
        remediation_plane: str,
        remediation_ref: str,
        idempotency_key: str,
        now: datetime,
    ) -> RemediationLink:
        """Record an outward remediation reference.

        This writes a link and nothing else. CTRL-05 has no code path that
        requests, approves or executes the referenced operation; that must
        travel the owning plane's own governed path.
        """
        moment = self._time(now)
        with self._lock:
            try:
                case = self._case(case_id)
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="REMEDIATION",
                    journal_act="AUDIT.REMEDIATION.LINK",
                    scope=case.scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if existing is not None:
                    return self._remediations[existing]
                _require_id(remediation_ref, "remediation_ref")
                _, _mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=case.scope,
                    right=AuditRight.REVIEW,
                    now=moment,
                )
                if case.state is ReviewState.CLOSED:
                    raise AuthorizationRefused(
                        "a closed case takes no further remediation link",
                        reason_code=OversightRefusal.WRONG_STATE,
                    )
            except ValueError as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.REMEDIATION.LINK",
                    scope_key=case.scope.key,
                    object_ref=case_id,
                    reason=OversightRefusal.PARAMETER_INVALID,
                    correlation=case_id,
                    detail=str(exc),
                ) from exc
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.REMEDIATION.LINK",
                    scope_key=self._scope_key_of(case_id),
                    object_ref=case_id,
                    reason=str(exc.reason_code),
                    correlation=case_id,
                    detail=str(exc),
                ) from exc
            link = RemediationLink(
                link_id=self._next_id("RMD"),
                case_id=case_id,
                remediation_plane=scrub_text(str(remediation_plane))[:64],
                remediation_ref=remediation_ref,
                linked_by=actor_ref,
                linked_at=moment,
                executed_by_ctrl05=False,
            )
            self._remediations[link.link_id] = link
            self._cases[case_id] = replace(
                case,
                state=ReviewState.REMEDIATION_LINKED
                if case.state in DISPOSITION_STATES
                else case.state,
                version=case.version + 1,
                remediation_ids=(*case.remediation_ids, link.link_id),
            )
            self._remember(actor_ref, idempotency_key, "REMEDIATION", link.link_id)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.REMEDIATION.LINK",
                scope_key=case.scope.key,
                object_ref=case_id,
                result="LINKED",
                reason_code="AUD_AUTHORIZED",
                correlation=case_id,
                attributes={
                    "remediation_plane": link.remediation_plane,
                    "remediation_ref": link.remediation_ref,
                    "executed_by_ctrl05": "NO",
                },
            )
            self._persist()
            return link

    def attest(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        ticket_id: str,
        statement: str,
        idempotency_key: str,
        now: datetime,
    ) -> ReviewAttestation:
        """Attest the case outcome under commit-time reauthorization."""
        moment = self._time(now)
        with self._lock:
            try:
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="ATTEST",
                    journal_act="AUDIT.CASE.ATTEST",
                    scope=self._scope_of_ticket(ticket_id),
                    right=AuditRight.ATTEST,
                    now=moment,
                )
                if existing is not None:
                    return self._attestations[existing]
                ticket, case, mandate, grant = self._reauthorize(
                    ticket_id=ticket_id,
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    act="ATTEST",
                    right=AuditRight.ATTEST,
                    moment=moment,
                )
                if self.policy.enforce_disposition_before_attestation and (
                    case.state not in DISPOSITION_STATES
                    and case.state is not ReviewState.REMEDIATION_LINKED
                ):
                    raise AuthorizationRefused(
                        f"case is {case.state.value}; an attestation requires a disposition",
                        reason_code=OversightRefusal.DISPOSITION_REQUIRED,
                    )
                if not case.disposition_ids:
                    raise AuthorizationRefused(
                        "case carries no disposition record",
                        reason_code=OversightRefusal.DISPOSITION_REQUIRED,
                    )
                if len(str(statement)) > MAX_ATTESTATION_STATEMENT:
                    raise AuthorizationRefused(
                        "attestation statement exceeds the governed bound",
                        reason_code=OversightRefusal.PARAMETER_INVALID,
                    )
            except AuthorizationRefused as exc:
                self._decide(
                    act="CASE.ATTEST",
                    actor_ref=actor_ref,
                    allowed=False,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.ATTEST",
                    scope_key="UNKNOWN",
                    object_ref=ticket_id,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                ) from exc
            attestation = ReviewAttestation(
                attestation_id=self._next_id("ATT"),
                case_id=case.case_id,
                statement=scrub_text(str(statement))[:MAX_ATTESTATION_STATEMENT],
                outcome=case.state,
                attested_by=actor_ref,
                attested_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=grant.grant_id,
                authority_version=grant.version,
                case_version=case.version,
                disposition_ref=case.disposition_ids[-1],
                finding_refs=tuple(case.finding_ids),
                evidence_refs=tuple(case.evidence_refs),
                reauthorized_at=moment,
            )
            self._attestations[attestation.attestation_id] = attestation
            self._cases[case.case_id] = replace(
                case,
                state=ReviewState.ATTESTED,
                version=case.version + 1,
                attestation_ids=(*case.attestation_ids, attestation.attestation_id),
            )
            ticket["consumed"] = True
            self._remember(actor_ref, idempotency_key, "ATTEST", attestation.attestation_id)
            self._decide(
                act="CASE.ATTEST",
                actor_ref=actor_ref,
                allowed=True,
                reason="AUD_REAUTHORIZED",
                correlation=case.case_id,
                mandate=mandate,
                grant=grant,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.CASE.ATTEST",
                scope_key=case.scope.key,
                object_ref=case.case_id,
                result="ATTESTED",
                reason_code="AUD_REAUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "attestation_id": attestation.attestation_id,
                    "outcome": attestation.outcome.value,
                    "content_digest": _content_digest(
                        attestation.outcome.value,
                        attestation.statement,
                        attestation.attested_by,
                        attestation.case_version,
                    ),
                    "attested_case_version": attestation.case_version,
                    "disposition_ref": attestation.disposition_ref,
                    "findings": len(attestation.finding_refs),
                    "mandate": mandate.competence_ref,
                },
            )
            self._persist()
            return attestation

    def close_case(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        case_id: str,
        expected_version: int,
        idempotency_key: str,
        now: datetime,
    ) -> ReviewCase:
        """Close an attested case. A case is never closed without a record."""
        moment = self._time(now)
        with self._lock:
            try:
                case = self._case(case_id)
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="CLOSE",
                    journal_act="AUDIT.CASE.CLOSE",
                    scope=case.scope,
                    right=AuditRight.ATTEST,
                    now=moment,
                )
                if existing is not None:
                    return self._cases[existing]
                _, _mandate, grant = self._mutation_preflight(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    scope=case.scope,
                    right=AuditRight.ATTEST,
                    now=moment,
                )
                if self.policy.enforce_case_version and case.version != expected_version:
                    raise AuthorizationRefused(
                        f"case moved to version {case.version}",
                        reason_code=OversightRefusal.STALE_CASE_VERSION,
                    )
                if case.state is not ReviewState.ATTESTED:
                    # An unattested case and a case in the wrong state are two
                    # different governance failures and carry different codes.
                    raise AuthorizationRefused(
                        f"case is {case.state.value}; only an attested case may be closed",
                        reason_code=OversightRefusal.ATTESTATION_WITHOUT_AUTHORITY
                        if not self.attestations_of(case_id)
                        else OversightRefusal.WRONG_STATE,
                    )
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.CASE.CLOSE",
                    scope_key=self._scope_key_of(case_id),
                    object_ref=case_id,
                    reason=str(exc.reason_code),
                    correlation=case_id,
                    detail=str(exc),
                ) from exc
            closed = replace(
                case, state=ReviewState.CLOSED, version=case.version + 1, closed_at=moment
            )
            self._cases[case_id] = closed
            self._remember(actor_ref, idempotency_key, "CLOSE", case_id)
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                act="AUDIT.CASE.CLOSE",
                scope_key=case.scope.key,
                object_ref=case_id,
                result="CLOSED",
                reason_code="AUD_AUTHORIZED",
                correlation=case_id,
                attributes={
                    "attestations": len(case.attestation_ids),
                    "findings": len(case.finding_ids),
                    "dispositions": len(case.disposition_ids),
                },
            )
            self._persist()
            return closed

    # -- purpose-bound, evidenced export -------------------------------------

    def export(
        self,
        *,
        actor_ref: str,
        session_id: str,
        csrf_token: str | None,
        ticket_id: str,
        purpose: str,
        evidence_refs: Sequence[str],
        idempotency_key: str,
        now: datetime,
    ) -> dict[str, Any]:
        """Export evidence under an explicit purpose, with the redaction evidenced.

        The purpose names an allow-list of fields. Everything outside it is
        dropped, and the drop itself becomes a `RedactionDecision` record in
        the journal — so an export can never quietly widen its own scope, and
        a later reviewer can see exactly what was withheld.
        """
        moment = self._time(now)
        with self._lock:
            try:
                existing = self._replay(
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    key=idempotency_key,
                    act="EXPORT",
                    journal_act="AUDIT.EVIDENCE.EXPORT",
                    scope=self._scope_of_ticket(ticket_id),
                    right=AuditRight.EXPORT,
                    now=moment,
                )
                if existing is not None:
                    return self._export_view(self._exports[existing])
                if self.policy.enforce_export_purpose and purpose not in EXPORT_PURPOSES:
                    raise AuthorizationRefused(
                        f"unknown export purpose {purpose!r}",
                        reason_code=OversightRefusal.EXPORT_PURPOSE_UNKNOWN,
                    )
                if len(evidence_refs) > MAX_EXPORT_RECORDS:
                    raise AuthorizationRefused(
                        "export exceeds the governed record bound",
                        reason_code=OversightRefusal.EXPORT_LIMIT,
                    )
                ticket, case, mandate, grant = self._reauthorize(
                    ticket_id=ticket_id,
                    actor_ref=actor_ref,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    act="EXPORT",
                    right=AuditRight.EXPORT,
                    moment=moment,
                )
                requested = tuple(evidence_refs) or case.evidence_refs
                if self.policy.enforce_export_purpose:
                    outside = [r for r in requested if r not in case.evidence_refs]
                    if outside:
                        raise AuthorizationRefused(
                            f"{len(outside)} record(s) are outside the case being exported",
                            reason_code=OversightRefusal.EXPORT_OUT_OF_PURPOSE,
                        )
                envelopes = [self._locate(r, mandate, case.scope) for r in requested]
            except AuthorizationRefused as exc:
                self._decide(
                    act="EVIDENCE.EXPORT",
                    actor_ref=actor_ref,
                    allowed=False,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    act="AUDIT.EVIDENCE.EXPORT",
                    scope_key="UNKNOWN",
                    object_ref=purpose,
                    reason=str(exc.reason_code),
                    correlation=ticket_id,
                    detail=str(exc),
                ) from exc
            allowed = EXPORT_PURPOSES.get(purpose, frozenset())
            rows: list[dict[str, Any]] = []
            dropped: set[str] = set()
            redacted_values: set[str] = set()
            for envelope in envelopes:
                full = envelope.as_dict()
                row: dict[str, Any] = {}
                for key, value in full.items():
                    if self.policy.enforce_export_purpose and key not in allowed:
                        dropped.add(key)
                        continue
                    row[key] = value
                redacted_values.update(envelope.redacted_fields)
                rows.append(row)
            payload = {
                "schema": "epd2.ctrl05.evidence-export/1",
                "purpose": purpose,
                "scope": case.scope.key,
                "case_id": case.case_id,
                "records": rows,
                "record_count": len(rows),
            }
            raw_text = json.dumps(payload)
            if self.policy.enforce_secret_redaction:
                payload = _scrub_structure(payload)
            # The sweep is over the *unscrubbed* bytes: scrubbing first would
            # make this check unable to fail, which is not a check at all.
            for marker in SECRET_SHAPE_MARKERS:
                if marker in raw_text:
                    raise self._refuse(
                        now=moment,
                        actor_ref=actor_ref,
                        act="AUDIT.EVIDENCE.EXPORT",
                        scope_key=case.scope.key,
                        object_ref=purpose,
                        reason=OversightRefusal.SECRET_VISIBILITY,
                        correlation=case.case_id,
                        detail="export payload would carry raw secret material",
                    )
            if self.policy.enforce_person_identifier_screen:
                for row in rows:
                    for key in row:
                        if key.lower() in PERSON_IDENTIFIER_FIELDS:
                            raise self._refuse(
                                now=moment,
                                actor_ref=actor_ref,
                                act="AUDIT.EVIDENCE.EXPORT",
                                scope_key=case.scope.key,
                                object_ref=purpose,
                                reason=OversightRefusal.PERSON_IDENTIFIER,
                                correlation=case.case_id,
                                detail=f"export field {key!r} is a person identifier",
                            )
            export_id = self._next_id("EXP")
            decision = RedactionDecision(
                decision_id=self._next_id("RDC"),
                export_id=export_id,
                purpose=purpose,
                policy_version=POLICY_VERSION,
                allowed_fields=tuple(sorted(allowed)),
                dropped_fields=tuple(sorted(dropped)),
                redacted_values=tuple(sorted(redacted_values)),
                record_count=len(rows),
                decided_at=moment,
                decided_by=actor_ref,
            )
            if not self.policy.enforce_export_redaction_record:
                decision = replace(decision, dropped_fields=(), redacted_values=())
            self._redactions[decision.decision_id] = decision
            digest = hashlib.sha256(canonical_dumps(payload).encode()).hexdigest()
            export = EvidenceExportRequest(
                export_id=export_id,
                purpose=purpose,
                scope=case.scope,
                case_id=case.case_id,
                evidence_refs=tuple(requested),
                requested_by=actor_ref,
                requested_at=moment,
                mandate_ref=mandate.competence_ref,
                authority_ref=f"{grant.grant_id}@v{grant.version}",
                redaction_decision_id=decision.decision_id,
                payload_digest=digest,
                record_count=len(rows),
            )
            self._exports[export_id] = export
            ticket["consumed"] = True
            self._remember(actor_ref, idempotency_key, "EXPORT", export_id)
            self._decide(
                act="EVIDENCE.EXPORT",
                actor_ref=actor_ref,
                allowed=True,
                reason="AUD_REAUTHORIZED",
                correlation=case.case_id,
                mandate=mandate,
                grant=grant,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=export.authority_ref,
                act="AUDIT.EVIDENCE.EXPORT",
                scope_key=case.scope.key,
                object_ref=export_id,
                result="EXPORTED",
                reason_code="AUD_REAUTHORIZED",
                correlation=case.case_id,
                attributes={
                    "purpose": purpose,
                    "records": len(rows),
                    "payload_digest": digest,
                    "redaction_decision": decision.decision_id,
                    "dropped_fields": ",".join(decision.dropped_fields) or "NONE",
                    "redacted_values": ",".join(decision.redacted_values) or "NONE",
                },
            )
            self._persist()
            return {
                "export": self._export_view(export),
                "redaction_decision": decision.as_dict(),
                "payload": payload,
            }

    def _export_view(self, export: EvidenceExportRequest) -> dict[str, Any]:
        return {
            "export_id": export.export_id,
            "purpose": export.purpose,
            "scope": export.scope.key,
            "case_id": export.case_id,
            "record_count": export.record_count,
            "payload_digest": export.payload_digest,
            "requested_by": export.requested_by,
            "requested_at": export.requested_at.isoformat(),
            "mandate_ref": export.mandate_ref,
            "authority_ref": export.authority_ref,
            "redaction_decision_id": export.redaction_decision_id,
        }

    # -- read models ---------------------------------------------------------
    #
    # `case`, `cases`, `case_view`, `_export_view` and `read_model` are
    # *projections*: they take no actor and apply no authority, and they exist
    # for in-process composition and for the persistence cross-check. Nothing
    # that answers a request may call them directly. The governed read entry
    # points below are the only way in from outside: each resolves the exact
    # mandate and filters every collection to that mandate's scope.

    def _read_authority(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        act: str,
        now: datetime,
    ) -> tuple[OversightMandate, AuthorityGrant]:
        moment = self._time(now, actor_ref=actor_ref, act=act)
        try:
            self._session(session_id, actor_ref, moment)
            return self._resolve_mandate(
                actor_ref=actor_ref, scope=scope, right=AuditRight.READ, now=moment
            )
        except AuthorizationRefused as exc:
            raise self._refuse(
                now=moment,
                actor_ref=actor_ref,
                act=act,
                scope_key=scope.key,
                object_ref="read-model",
                reason=str(exc.reason_code),
                correlation="read-model",
                detail=str(exc),
            ) from exc

    def governed_cases(
        self, *, actor_ref: str, session_id: str, scope: OversightScope, now: datetime
    ) -> list[dict[str, Any]]:
        """Every case inside this exact mandate, and nothing else."""
        with self._lock:
            self._read_authority(
                actor_ref=actor_ref,
                session_id=session_id,
                scope=scope,
                act="AUDIT.CASE.LIST",
                now=now,
            )
            return [
                self.case_view(c.case_id) for c in self._cases.values() if c.scope.contains(scope)
            ]

    def governed_case(
        self,
        *,
        actor_ref: str,
        session_id: str,
        scope: OversightScope,
        case_id: str,
        now: datetime,
    ) -> dict[str, Any]:
        """One case, if it is inside this exact mandate.

        A case in another organization or another oversight unit is reported
        as unknown, not as forbidden: its existence is not this reviewer's
        information either.
        """
        with self._lock:
            self._read_authority(
                actor_ref=actor_ref,
                session_id=session_id,
                scope=scope,
                act="AUDIT.CASE.OPEN_VIEW",
                now=now,
            )
            case = self._cases.get(case_id)
            if case is None or not case.scope.contains(scope):
                raise AuthorizationRefused(
                    f"no case {case_id} in {scope.key}",
                    reason_code=OversightRefusal.UNKNOWN_CASE,
                )
            return self.case_view(case_id)

    def governed_read_model(
        self, *, actor_ref: str, session_id: str, scope: OversightScope, now: datetime
    ) -> dict[str, Any]:
        """The console read model, filtered to this exact mandate."""
        with self._lock:
            mandate, _grant = self._read_authority(
                actor_ref=actor_ref,
                session_id=session_id,
                scope=scope,
                act="AUDIT.READ_MODEL",
                now=now,
            )
            model = self.read_model(now=now)
            model["scope"] = scope.key
            model["mandate_ref"] = mandate.competence_ref
            model["cases"] = [c for c in model["cases"] if c["scope"] == scope.key]
            model["exports"] = [e for e in model["exports"] if e["scope"] == scope.key]
            # The governed unit map is itself oversight information: a reviewer
            # sees only the streams assigned to their own scope.
            model["evidence_units"] = {
                k: v for k, v in self.evidence_units.items() if v == scope.key
            }
            visible = [e for e in self._all_envelopes()[0] if self._visible(e, mandate, scope)]
            model["evidence_count"] = len(visible)
            model["integrity_summary"] = self._integrity_summary(visible)
            return model

    def governed_exports(
        self, *, actor_ref: str, session_id: str, scope: OversightScope, now: datetime
    ) -> list[dict[str, Any]]:
        with self._lock:
            self._read_authority(
                actor_ref=actor_ref,
                session_id=session_id,
                scope=scope,
                act="AUDIT.EXPORT.LIST",
                now=now,
            )
            return [self._export_view(e) for e in self._exports.values() if e.scope.contains(scope)]

    def case(self, case_id: str) -> ReviewCase:
        return self._case(case_id)

    def cases(self) -> tuple[ReviewCase, ...]:
        return tuple(self._cases.values())

    def findings_of(self, case_id: str) -> tuple[ReviewFinding, ...]:
        return tuple(self._findings[f] for f in self._case(case_id).finding_ids)

    def dispositions_of(self, case_id: str) -> tuple[ReviewDisposition, ...]:
        return tuple(self._dispositions[d] for d in self._case(case_id).disposition_ids)

    def attestations_of(self, case_id: str) -> tuple[ReviewAttestation, ...]:
        return tuple(self._attestations[a] for a in self._case(case_id).attestation_ids)

    def clarifications_of(self, case_id: str) -> tuple[Clarification, ...]:
        return tuple(self._clarifications[c] for c in self._case(case_id).clarification_ids)

    def remediations_of(self, case_id: str) -> tuple[RemediationLink, ...]:
        return tuple(self._remediations[r] for r in self._case(case_id).remediation_ids)

    def redaction(self, decision_id: str) -> RedactionDecision | None:
        return self._redactions.get(decision_id)

    def export_view(self, export_id: str) -> dict[str, Any]:
        export = self._exports.get(export_id)
        if export is None:
            raise AuthorizationRefused("unknown export", reason_code=OversightRefusal.NOT_FOUND)
        return self._export_view(export)

    def exports(self) -> tuple[EvidenceExportRequest, ...]:
        return tuple(self._exports.values())

    def decisions_of(self, correlation: str) -> tuple[AuthorizationDecision, ...]:
        return tuple(self._decisions.get(correlation, ()))

    def events_of(self, correlation: str) -> tuple[OversightEvent, ...]:
        return tuple(self._events.get(correlation, ()))

    def case_view(self, case_id: str) -> dict[str, Any]:
        """The complete, append-only history of one case.

        Every disposition, finding (including disputed ones and their
        disputes), clarification, remediation link and attestation is listed in
        the order it happened. Nothing is ever removed from this view.
        """
        case = self._case(case_id)
        return {
            "case_id": case.case_id,
            "title": case.title,
            "scope": case.scope.key,
            "organization": case.scope.organization_key,
            "unit": case.scope.unit_id,
            "state": case.state.value,
            "version": case.version,
            "opened_by": case.opened_by,
            "opened_at": case.opened_at.isoformat(),
            "closed_at": _iso(case.closed_at),
            "mandate_ref": case.mandate_ref,
            "authority_ref": case.authority_ref,
            "evidence_refs": list(case.evidence_refs),
            "dispositions": [
                {
                    "disposition_id": d.disposition_id,
                    "state": d.state.value,
                    "rationale": d.rationale,
                    "decided_by": d.decided_by,
                    "decided_at": d.decided_at.isoformat(),
                    "mandate_ref": d.mandate_ref,
                    "authority_ref": d.authority_ref,
                    "supersedes": d.supersedes,
                }
                for d in self.dispositions_of(case_id)
            ],
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "severity": f.severity.value,
                    "summary": f.summary,
                    "state": f.state.value,
                    "evidence_reference": f.evidence_reference.as_dict(),
                    "evidence_content_digest": f.evidence_content_digest,
                    "raised_by": f.raised_by,
                    "raised_at": f.raised_at.isoformat(),
                    "authority_ref": f.authority_ref,
                    "dispute_ref": f.dispute_ref,
                }
                for f in self.findings_of(case_id)
            ],
            "clarifications": [
                {
                    "clarification_id": c.clarification_id,
                    "text": c.text,
                    "author_ref": c.author_ref,
                    "created_at": c.created_at.isoformat(),
                    "evidence_reference": None
                    if c.evidence_reference is None
                    else c.evidence_reference.as_dict(),
                    "source_evidence_mutated": False,
                }
                for c in self.clarifications_of(case_id)
            ],
            "remediation_links": [
                {
                    "link_id": r.link_id,
                    "plane": r.remediation_plane,
                    "remediation_ref": r.remediation_ref,
                    "linked_by": r.linked_by,
                    "linked_at": r.linked_at.isoformat(),
                    "executed_by_ctrl05": r.executed_by_ctrl05,
                }
                for r in self.remediations_of(case_id)
            ],
            "attestations": [
                {
                    "attestation_id": a.attestation_id,
                    "statement": a.statement,
                    "outcome": a.outcome.value,
                    "attested_by": a.attested_by,
                    "attested_at": a.attested_at.isoformat(),
                    "mandate_ref": a.mandate_ref,
                    "authority_ref": f"{a.authority_ref}@v{a.authority_version}",
                    "attested_case_version": a.case_version,
                    "disposition_ref": a.disposition_ref,
                    "finding_refs": list(a.finding_refs),
                    "reauthorized_at": a.reauthorized_at.isoformat(),
                }
                for a in self.attestations_of(case_id)
            ],
            "oversight_events": [
                {
                    "event_id": e.event_id,
                    "sequence": e.journal_sequence,
                    "act": e.act,
                    "result": e.result,
                    "reason_code": e.reason_code,
                    "event_hash": e.event_hash,
                }
                for e in self.events_of(case_id)
            ],
            "history_is_append_only": True,
        }

    def read_model(self, *, now: datetime) -> dict[str, Any]:
        """Console read model. Carries no secret and no person identifier."""
        with self._lock:
            envelopes, unavailable = self._all_envelopes()
            payload = {
                "schema": "epd2.ctrl05.oversight-read-model/1",
                "stage": STAGE,
                "self_state": SELF_STATE,
                "as_of": now.isoformat(),
                "planes": sorted(self._sources),
                "unavailable_planes": unavailable,
                "evidence_units": dict(self.evidence_units),
                "evidence_count": len(envelopes),
                "integrity_summary": self._integrity_summary(envelopes),
                "cases": [self.case_view(c.case_id) for c in self._cases.values()],
                "exports": [self._export_view(e) for e in self._exports.values()],
                "oversight_journal_head": self.journal.head_hash(),
                "oversight_journal_count": len(self.journal),
                "operational_execution_surface": "ABSENT",
                "secret_surface": "ABSENT",
                "shell_sql_exec_surface": "ABSENT",
            }
            scrubbed: dict[str, Any] = _scrub_structure(payload)
            return scrubbed

    # -- persistence ---------------------------------------------------------

    def checkpoint(self) -> dict[str, Any]:
        def dump(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, OversightScope):
                return {
                    "region_id": value.region_id,
                    "org_id": value.org_id,
                    "unit_id": value.unit_id,
                }
            if isinstance(value, EvidenceReference):
                return value.as_dict()
            if isinstance(value, frozenset | set):
                return sorted(dump(v) for v in value)
            if isinstance(value, tuple | list):
                return [dump(v) for v in value]
            if isinstance(value, dict):
                return {k: dump(v) for k, v in value.items()}
            return value

        return {
            "schema": "epd2.ctrl05.checkpoint/1",
            "mandates": {k: dump(asdict(v)) for k, v in self._mandates.items()},
            # A session's CSRF token is a credential. It is held in memory
            # for the life of the session and is deliberately not persisted:
            # a checkpoint file must never be a token store.
            "sessions": {
                k: {key: value for key, value in dump(asdict(v)).items() if key != "csrf_token"}
                for k, v in self._sessions.items()
            },
            "evidence_units": dict(self.evidence_units),
            "cases": {k: dump(asdict(v)) for k, v in self._cases.items()},
            "dispositions": {k: dump(asdict(v)) for k, v in self._dispositions.items()},
            "findings": {k: dump(asdict(v)) for k, v in self._findings.items()},
            "attestations": {k: dump(asdict(v)) for k, v in self._attestations.items()},
            "clarifications": {k: dump(asdict(v)) for k, v in self._clarifications.items()},
            "remediations": {k: dump(asdict(v)) for k, v in self._remediations.items()},
            "exports": {k: dump(asdict(v)) for k, v in self._exports.items()},
            "redactions": {k: dump(asdict(v)) for k, v in self._redactions.items()},
            "tickets": {k: dump(v) for k, v in self._tickets.items()},
            "decisions": {k: [dump(asdict(d)) for d in v] for k, v in self._decisions.items()},
            "events": {k: [dump(asdict(e)) for e in v] for k, v in self._events.items()},
            "idempotency": dict(self._idempotency),
            "counter": self._counter,
            "last_time": self._last_time.isoformat(),
            "journal": self.journal.export(),
            "journal_anchor": list(self.journal.anchor()),
            "journal_seal": (
                None if self.sealer is None else self.sealer.seal(*self.journal.anchor())
            ),
        }

    @classmethod
    def from_checkpoint(
        cls,
        payload: Mapping[str, Any],
        *,
        authorities: AuthorityDirectory,
        sources: Mapping[str, EvidenceSource],
        voting_verification: VotingVerificationSource | None = None,
        policy: OversightPolicy | None = None,
        store: Any | None = None,
        sealer: EvidenceSealer | None = None,
    ) -> OversightConsoleService:
        if payload.get("schema") != "epd2.ctrl05.checkpoint/1":
            raise ValueError("unknown checkpoint schema")
        service = cls(
            authorities=authorities,
            sources=sources,
            evidence_units=dict(payload.get("evidence_units", {})),
            voting_verification=voting_verification,
            policy=policy,
            store=None,
            sealer=sealer,
        )

        def scope(value: Mapping[str, str]) -> OversightScope:
            return OversightScope(value["region_id"], value["org_id"], value["unit_id"])

        def reference(value: Mapping[str, Any]) -> EvidenceReference:
            return EvidenceReference(
                EvidencePlane(value["plane"]),
                value["stream_id"],
                value["event_id"],
                int(value["sequence"]),
                value["event_hash"],
                value["content_digest"],
            )

        for key, value in payload["mandates"].items():
            service._mandates[key] = OversightMandate(
                mandate_id=value["mandate_id"],
                subject_ref=value["subject_ref"],
                scope=scope(value["scope"]),
                planes=frozenset(EvidencePlane(p) for p in value["planes"]),
                rights=frozenset(AuditRight(r) for r in value["rights"]),
                rule_version=value["rule_version"],
                source_decision_ref=value["source_decision_ref"],
                authority_bindings=frozenset(
                    (str(r), str(g)) for r, g in value["authority_bindings"]
                ),
                valid_from=_dt(value["valid_from"]),
                valid_until=_dt(value["valid_until"]),
                superseded_by=value.get("superseded_by"),
                revoked_at=None if value.get("revoked_at") is None else _dt(value["revoked_at"]),
            )
        for key, value in payload["sessions"].items():
            service._sessions[key] = OversightSession(
                session_id=value["session_id"],
                principal_id=value["principal_id"],
                state=SessionState(value["state"]),
                established_at=_dt(value["established_at"]),
                expires_at=_dt(value["expires_at"]),
                # The token was deliberately not persisted (see `checkpoint`).
                # A restored session therefore carries a fresh server-side
                # token the old client cannot know: reads continue, and every
                # mutation must re-establish the session first. A restart
                # invalidating in-flight CSRF tokens is the safe direction.
                csrf_token=secrets.token_urlsafe(32),
            )
        for key, value in payload["cases"].items():
            service._cases[key] = ReviewCase(
                case_id=value["case_id"],
                title=value["title"],
                scope=scope(value["scope"]),
                opened_by=value["opened_by"],
                opened_at=_dt(value["opened_at"]),
                mandate_ref=value["mandate_ref"],
                authority_ref=value["authority_ref"],
                state=ReviewState(value["state"]),
                version=int(value["version"]),
                evidence_refs=tuple(value["evidence_refs"]),
                disposition_ids=tuple(value["disposition_ids"]),
                finding_ids=tuple(value["finding_ids"]),
                attestation_ids=tuple(value["attestation_ids"]),
                remediation_ids=tuple(value["remediation_ids"]),
                clarification_ids=tuple(value["clarification_ids"]),
                closed_at=None if value.get("closed_at") is None else _dt(value["closed_at"]),
            )
        for key, value in payload["dispositions"].items():
            service._dispositions[key] = ReviewDisposition(
                **{
                    **value,
                    "state": ReviewState(value["state"]),
                    "decided_at": _dt(value["decided_at"]),
                }
            )
        for key, value in payload["findings"].items():
            service._findings[key] = ReviewFinding(
                finding_id=value["finding_id"],
                case_id=value["case_id"],
                severity=FindingSeverity(value["severity"]),
                summary=value["summary"],
                evidence_reference=reference(value["evidence_reference"]),
                evidence_content_digest=value["evidence_content_digest"],
                raised_by=value["raised_by"],
                raised_at=_dt(value["raised_at"]),
                mandate_ref=value["mandate_ref"],
                authority_ref=value["authority_ref"],
                state=FindingState(value["state"]),
                superseded_by=value.get("superseded_by"),
                dispute_ref=value.get("dispute_ref"),
            )
        for key, value in payload["attestations"].items():
            service._attestations[key] = ReviewAttestation(
                **{
                    **value,
                    "outcome": ReviewState(value["outcome"]),
                    "attested_at": _dt(value["attested_at"]),
                    "reauthorized_at": _dt(value["reauthorized_at"]),
                    "finding_refs": tuple(value["finding_refs"]),
                    "evidence_refs": tuple(value["evidence_refs"]),
                }
            )
        for key, value in payload["clarifications"].items():
            service._clarifications[key] = Clarification(
                clarification_id=value["clarification_id"],
                case_id=value["case_id"],
                text=value["text"],
                author_ref=value["author_ref"],
                created_at=_dt(value["created_at"]),
                evidence_reference=None
                if value.get("evidence_reference") is None
                else reference(value["evidence_reference"]),
            )
        for key, value in payload["remediations"].items():
            service._remediations[key] = RemediationLink(
                **{**value, "linked_at": _dt(value["linked_at"])}
            )
        for key, value in payload["exports"].items():
            service._exports[key] = EvidenceExportRequest(
                **{
                    **value,
                    "scope": scope(value["scope"]),
                    "requested_at": _dt(value["requested_at"]),
                    "evidence_refs": tuple(value["evidence_refs"]),
                }
            )
        for key, value in payload["redactions"].items():
            service._redactions[key] = RedactionDecision(
                **{
                    **value,
                    "decided_at": _dt(value["decided_at"]),
                    "allowed_fields": tuple(value["allowed_fields"]),
                    "dropped_fields": tuple(value["dropped_fields"]),
                    "redacted_values": tuple(value["redacted_values"]),
                }
            )
        service._tickets = {k: dict(v) for k, v in payload["tickets"].items()}
        for key, value in payload["decisions"].items():
            service._decisions[key] = [AuthorizationDecision(**d) for d in value]
        for key, value in payload["events"].items():
            service._events[key] = [OversightEvent(**e) for e in value]
        service._idempotency = dict(payload["idempotency"])
        service._counter = int(payload["counter"])
        service._last_time = _dt(payload["last_time"])
        service._restore_journal(
            payload["journal"], payload["journal_anchor"], payload.get("journal_seal")
        )
        service._verify_state_against_journal()
        service._store = store
        return service

    def _restore_journal(
        self, records: list[dict[str, Any]], anchor: list[Any], seal: str | None
    ) -> None:
        """Re-append every record and refuse a rewritten oversight history."""
        for record in records:
            event = self.journal.append(
                occurred_at=_dt(record["occurred_at"]),
                actor_ref=record["actor_ref"],
                actor_class=record["actor_class"],
                authority_basis=record["authority_basis"],
                action_id=record["action_id"],
                scope_key=record["scope_key"],
                object_ref=record["object_ref"],
                result=record["result"],
                reason_code=record["reason_code"],
                approval_refs=tuple(record["approval_refs"]),
                correlation_ref=record["correlation_ref"],
                attributes=record["attributes"],
            )
            if self.policy.enforce_journal_immutability and (
                event.event_hash != record["event_hash"]
                or event.previous_event_hash != record["previous_event_hash"]
                or event.sequence != record["sequence"]
            ):
                raise AuthorizationRefused(
                    f"persisted oversight record {record['sequence']} does not re-verify",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
        if self.policy.enforce_journal_immutability:
            if list(self.journal.anchor()) != list(anchor):
                raise AuthorizationRefused(
                    "persisted oversight anchor does not match",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            count, head = self.journal.anchor()
            if self.sealer is None:
                if seal is not None:
                    raise AuthorizationRefused(
                        "sealed oversight history cannot be verified without the key",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
            elif seal is None or not self.sealer.verify(count, head, seal):
                raise AuthorizationRefused(
                    "persisted oversight seal does not verify; history may have been rewritten",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
        self.journal.verify()

    def _verify_state_against_journal(self) -> None:
        """Refuse a checkpoint whose case tables disagree with the journal.

        Case tables are convenience projections; the journal is the evidence.
        Every case must be backed by an OPEN record with the same actor, and
        every attestation and finding must appear in the trail.
        """
        if not self.policy.enforce_journal_immutability:
            return
        by_case: dict[str, list[Any]] = {}
        for record in self.journal.records():
            by_case.setdefault(record.correlation_ref, []).append(record)

        def acts(trail: list[Any], act: str) -> list[Any]:
            """Records of one governed act.

            Keyed on the *act*, never on the record's result: a disposition
            record carries the disposition state as its result, so
            `result == "FINDING_RAISED"` would count dispositions as findings.
            Refused attempts are excluded — a refusal is evidence that
            something was *not* done, so it backs no state.
            """
            return [
                r
                for r in trail
                if r.action_id == act and r.result != "REFUSED" and r.reason_code != "REFUSED"
            ]

        def digest_of(trail: list[Any], act: str, id_key: str, record_id: str) -> str | None:
            for record in acts(trail, act):
                if record.attributes.get(id_key) == record_id:
                    return str(record.attributes.get("content_digest", ""))
            return None

        for case in self._cases.values():
            trail = by_case.get(case.case_id, [])
            opened = acts(trail, "AUDIT.CASE.OPEN")
            if not opened or opened[0].actor_ref != case.opened_by:
                raise AuthorizationRefused(
                    f"case {case.case_id} is not backed by its oversight trail",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            # The case's own substance: title, exact scope and author. A case
            # moved into another oversight unit, retitled, or reattributed no
            # longer agrees with the record that opened it.
            if opened[0].scope_key != case.scope.key or str(
                opened[0].attributes.get("content_digest", "")
            ) != _content_digest(case.title, case.scope.key, case.opened_by):
                raise AuthorizationRefused(
                    f"case {case.case_id} does not match the record that opened it",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            if case.state is ReviewState.CLOSED and not acts(trail, "AUDIT.CASE.CLOSE"):
                raise AuthorizationRefused(
                    f"case {case.case_id} claims CLOSED with no closing record",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            if len(acts(trail, "AUDIT.CASE.ATTEST")) != len(case.attestation_ids):
                raise AuthorizationRefused(
                    f"case {case.case_id} attestation count disagrees with its trail",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            for attestation_id in case.attestation_ids:
                attestation = self._attestations.get(attestation_id)
                if attestation is None or not [
                    r
                    for r in acts(trail, "AUDIT.CASE.ATTEST")
                    if r.actor_ref == attestation.attested_by
                    and r.attributes.get("attestation_id") == attestation_id
                ]:
                    raise AuthorizationRefused(
                        f"attestation {attestation_id} is not backed by its own record",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
                if digest_of(
                    trail, "AUDIT.CASE.ATTEST", "attestation_id", attestation_id
                ) != _content_digest(
                    attestation.outcome.value,
                    attestation.statement,
                    attestation.attested_by,
                    attestation.case_version,
                ):
                    raise AuthorizationRefused(
                        f"attestation {attestation_id} disagrees with its own record",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
            for finding_id in case.finding_ids:
                finding = self._findings.get(finding_id)
                if finding is None:
                    raise AuthorizationRefused(
                        f"finding {finding_id} is missing from the restored state",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
                expected = _content_digest(
                    finding.severity.value,
                    finding.summary,
                    finding.raised_by,
                    finding.evidence_reference.key,
                )
                recorded = digest_of(
                    trail, "AUDIT.FINDING.RAISE", "finding_id", finding_id
                ) or digest_of(trail, "AUDIT.FINDING.DISPUTE", "finding_id", finding_id)
                if recorded != expected:
                    raise AuthorizationRefused(
                        f"finding {finding_id} disagrees with the record that raised it "
                        f"(severity, summary, authorship or evidence was rewritten)",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
            for disposition_id in case.disposition_ids:
                decision = self._dispositions.get(disposition_id)
                if decision is None:
                    raise AuthorizationRefused(
                        f"disposition {disposition_id} is missing from the restored state",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
                if digest_of(
                    trail, "AUDIT.CASE.DISPOSE", "disposition_id", disposition_id
                ) != _content_digest(
                    decision.state.value,
                    decision.rationale,
                    decision.decided_by,
                    decision.supersedes,
                ):
                    raise AuthorizationRefused(
                        f"disposition {disposition_id} disagrees with its own record",
                        reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                    )
            findings = len(acts(trail, "AUDIT.FINDING.RAISE")) + len(
                acts(trail, "AUDIT.FINDING.DISPUTE")
            )
            if findings != len(case.finding_ids):
                raise AuthorizationRefused(
                    f"case {case.case_id} finding count disagrees with its trail",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
            if len(acts(trail, "AUDIT.CASE.DISPOSE")) != len(case.disposition_ids):
                raise AuthorizationRefused(
                    f"case {case.case_id} disposition count disagrees with its trail",
                    reason_code=OversightRefusal.HISTORY_IMMUTABLE,
                )
