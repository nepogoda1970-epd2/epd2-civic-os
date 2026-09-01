"""Reference administrative surfaces and observability contracts
(PACK-13 §30, §32).

**PACK-13 is not FRONT-PACK** (`P13-FE-001`). What this module provides
is *contract-level* administrative surfaces: typed, minimal view models
for the seven administrative concerns §32 enumerates — schema review,
compatibility result, migration status, consumer readiness, dead-letter
review, projection health, outbox backlog — plus the operational
data-plane status that ties them together.

Six prohibitions are enforced by what these view models **cannot
carry**, which is a stronger guarantee than a rule a renderer is
expected to follow:

- **No universal admin console** (`P13-FE-002`). Each surface is its own
  narrow type; there is no aggregate "everything" view.
- **No arbitrary SQL from any surface** (`P13-FE-005`). No field here
  holds a statement, a query or a filter expression, and
  `refuse_query_surface` exists to say so with a reason code.
- **No secrets and no unrestricted raw database content**
  (`P13-FE-004`). Every surface is assembled through
  `_safe_view`, which applies the same prohibited-key guard the outbox
  applies.
- **No bypass of a PACK-12 privileged grant** (`P13-FE-006`). The
  dead-letter surface returns identifiers, and reading one record is a
  privileged act performed elsewhere.
- **The frontend is not a security boundary** (`P13-FE-003`). Nothing
  here decides anything; every value is a projection of a decision made
  by a service that re-checks it.
- **No surface claims that production infrastructure is active**
  (`P13-FE-008`). `OperationalStatus.implementation_status` is fixed to
  the truthful value and validated.

Observability (§30) follows the same rule. `TelemetrySample` refuses the
seven forbidden categories `P13-OBS-002` names, and
`TraceCorrelation` exists specifically to keep a trace identifier from
becoming an identity correlation identifier (`P13-OBS-003`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    DATA_PLANE_IMPLEMENTATION_STATUS,
    DELIVERY_GUARANTEE,
    FORBIDDEN_DELIVERY_CLAIM,
    OrganizationScopeReference,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    ManualSqlProhibitedError,
    PermissionDeniedError,
)
from epd2_data_plane_service.projections import ProjectionHealth


def _safe_view(values: Mapping[str, object], *, surface: str) -> Mapping[str, object]:
    """Apply the payload guard to an administrative view.

    The same guard the outbox applies, for the same reason: a surface
    that displayed a secret or a person key would have had to hold one
    first."""
    reject_prohibited_payload_keys(dict(values), context=f"admin surface {surface!r}")
    return dict(values)


def refuse_query_surface(submitted_text: str) -> None:
    """Refuse any surface that would accept a query.

    Takes the submitted text only to include its length in the refusal —
    never its content, since `P13-OBS-002` forbids unrestricted query
    text in telemetry and a refusal message is telemetry."""
    raise ManualSqlProhibitedError(
        f"no administrative surface executes a query ({len(submitted_text)} characters "
        f"submitted, none of them evaluated); direct SQL happens in a governed migration or "
        f"an emergency context that leaves PACK-12 session evidence (P13-FE-005)"
    )


# ---------------------------------------------------------------------------
# The seven administrative surfaces
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SchemaReviewItem:
    """One schema version awaiting review.

    Carries the digest and the reference, never the document
    (`P13-EVT-005`'s discipline applied to a surface)."""

    schema_version_id: UUID
    family_name: str
    version_label: str
    owner_domain: str
    lifecycle_state: str
    content_digest: str
    awaiting: str

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "schema_version_id": str(self.schema_version_id),
                "family_name": self.family_name,
                "version_label": self.version_label,
                "owner_domain": self.owner_domain,
                "lifecycle_state": self.lifecycle_state,
                "content_digest": self.content_digest,
                "awaiting": self.awaiting,
            },
            surface="schema_review",
        )


@dataclass(frozen=True, slots=True)
class CompatibilityResultItem:
    """One compatibility assessment as an operator sees it.

    The automated and human verdicts are two fields on the surface too,
    not one: a surface that showed a single "verdict" would hide the case
    where a reviewer disagreed with the tool."""

    assessment_id: UUID
    automated_verdict: str
    human_verdict: str | None
    combined_verdict: str
    semantic_risk_classes: tuple[str, ...]
    review_required: bool

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "assessment_id": str(self.assessment_id),
                "automated_verdict": self.automated_verdict,
                "human_verdict": self.human_verdict,
                "combined_verdict": self.combined_verdict,
                "semantic_risk_classes": sorted(self.semantic_risk_classes),
                "review_required": self.review_required,
            },
            surface="compatibility_result",
        )


@dataclass(frozen=True, slots=True)
class MigrationStatusItem:
    """One migration execution's status.

    No statement text, no affected rows, no schema diff: counts,
    positions and references only (`P13-EVT-006`'s discipline applied to
    a surface)."""

    execution_id: UUID
    plan_id: UUID
    status: str
    migration_class: str
    checkpoints: int
    destructive: bool
    approval_present: bool
    dry_run_present: bool

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "execution_id": str(self.execution_id),
                "plan_id": str(self.plan_id),
                "status": self.status,
                "migration_class": self.migration_class,
                "checkpoints": self.checkpoints,
                "destructive": self.destructive,
                "approval_present": self.approval_present,
                "dry_run_present": self.dry_run_present,
            },
            surface="migration_status",
        )


@dataclass(frozen=True, slots=True)
class ConsumerReadinessItem:
    """Which consumers are ready for a target version.

    Carries counts and names, never what a consumer sent
    (`P13-API-013`)."""

    family_id: UUID
    target_version_id: UUID
    ready_count: int
    not_ready_count: int
    unregistered_are_unprotected: bool = True

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "family_id": str(self.family_id),
                "target_version_id": str(self.target_version_id),
                "ready_count": self.ready_count,
                "not_ready_count": self.not_ready_count,
                "unregistered_consumers_receive_no_compatibility_protection": (
                    self.unregistered_are_unprotected
                ),
            },
            surface="consumer_readiness",
        )


@dataclass(frozen=True, slots=True)
class DeadLetterReviewItem:
    """One dead-letter record as a review queue shows it.

    **Identifiers, reason code and classification only.** A dead-letter
    store may contain personal data and is excluded from general
    operator visibility (`P13-DEL-014`), so opening one record is a
    separate, privileged act that this surface does not perform."""

    dead_letter_id: UUID
    event_type: str
    reason_code: str
    attempt_count: int
    classification_tier: str
    requires_privileged_read: bool = True

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "dead_letter_id": str(self.dead_letter_id),
                "event_type": self.event_type,
                "reason_code": self.reason_code,
                "attempt_count": self.attempt_count,
                "classification_tier": self.classification_tier,
                "requires_privileged_read": self.requires_privileged_read,
            },
            surface="dead_letter_review",
        )

    def open_record(self) -> None:
        """Refuse to open the record from this surface.

        The refusal is a method rather than an absence so that a caller
        reaching for it gets a reason code and a pointer to the governed
        path, instead of an `AttributeError` that reads like an
        oversight."""
        raise PermissionDeniedError(
            f"dead-letter record {self.dead_letter_id} is classified "
            f"{self.classification_tier!r} and is read through a PACK-12 governed path, not "
            f"from a review surface (P13-FE-006, P13-DEL-014)"
        )


@dataclass(frozen=True, slots=True)
class ProjectionHealthItem:
    """One projection's health.

    Reports the **lag band**, not the exact lag (`P13-EVT-009`): an exact
    figure across organizations is itself information."""

    projection_id: UUID
    projection_name: str
    health: ProjectionHealth
    lag_band: str
    acceptable_for_consequential_use: bool

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "projection_id": str(self.projection_id),
                "projection_name": self.projection_name,
                "health": self.health.value,
                "lag_band": self.lag_band,
                "acceptable_for_consequential_use": self.acceptable_for_consequential_use,
            },
            surface="projection_health",
        )


@dataclass(frozen=True, slots=True)
class OutboxBacklogItem:
    """The backlog as a health signal (§29).

    Counts and thresholds; no payloads, because a backlog surface showing
    payloads would be an unrestricted read of every domain's events."""

    scope: OrganizationScopeReference
    pending_count: int
    oldest_pending_age_seconds: int
    alert_threshold: int
    exceeds_threshold: bool

    def to_view(self) -> Mapping[str, object]:
        return _safe_view(
            {
                "organization_id": str(self.scope.organization_id),
                "pending_count": self.pending_count,
                "oldest_pending_age_seconds": self.oldest_pending_age_seconds,
                "alert_threshold": self.alert_threshold,
                "exceeds_threshold": self.exceeds_threshold,
            },
            surface="outbox_backlog",
        )


#: The seven surfaces §32 admits, by name. Enumerated so a test can
#: assert that no eighth appears and that none of them is a console.
ADMINISTRATIVE_SURFACES: tuple[str, ...] = (
    "schema_review",
    "compatibility_result",
    "migration_status",
    "consumer_readiness",
    "dead_letter_review",
    "projection_health",
    "outbox_backlog",
)


@dataclass(frozen=True, slots=True)
class OperationalStatus:
    """The operational data-plane status a surface displays.

    `implementation_status` and `delivery_guarantee` are validated on
    construction: `P13-FE-008` forbids a surface claiming production
    infrastructure is active, and `P13-DEL-002` forbids the stronger
    delivery phrase appearing on any operator interface."""

    observed_at: datetime
    implementation_status: str = DATA_PLANE_IMPLEMENTATION_STATUS
    delivery_guarantee: str = DELIVERY_GUARANTEE
    production_infrastructure_active: bool = False
    legally_activated: bool = False

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="OperationalStatus.observed_at")
        if self.implementation_status != DATA_PLANE_IMPLEMENTATION_STATUS:
            raise PermissionDeniedError(
                f"an operational surface reports {DATA_PLANE_IMPLEMENTATION_STATUS!r}; no "
                f"surface claims that production infrastructure is active (P13-FE-008)"
            )
        if FORBIDDEN_DELIVERY_CLAIM in self.delivery_guarantee.lower():
            raise PermissionDeniedError(
                "no surface describes the delivery guarantee with the stronger phrase; what "
                "the system provides is at-least-once delivery with effectively-once consumer "
                "effect (P13-DEL-002)"
            )
        if self.production_infrastructure_active or self.legally_activated:
            raise PermissionDeniedError(
                "no production-readiness claim and no legal-activation claim is made by this "
                "round (FIR-INV-015)"
            )


# ---------------------------------------------------------------------------
# Observability (§30)
# ---------------------------------------------------------------------------


class TelemetryKind(StrEnum):
    """What §30 requires be exposed (`P13-OBS-001`)."""

    QUEUE_LAG = "queue_lag"
    OUTBOX_BACKLOG = "outbox_backlog"
    MIGRATION_PROGRESS = "migration_progress"
    SCHEMA_COMPATIBILITY_FAILURE = "schema_compatibility_failure"
    CONSUMER_ERROR = "consumer_error"
    RETRY_COUNT = "retry_count"
    DEAD_LETTER_VOLUME = "dead_letter_volume"
    PROJECTION_STALENESS = "projection_staleness"
    DATABASE_SATURATION = "database_saturation"
    HEALTH = "health"


#: What is forbidden in **any** telemetry (`P13-OBS-002`), enumerated so
#: the prohibition is a value a test can assert against rather than a
#: sentence in a document.
FORBIDDEN_TELEMETRY_CONTENT: tuple[str, ...] = (
    "plaintext secrets",
    "full personal records",
    "ballot content",
    "document payload",
    "export payload",
    "global identity correlation",
    "unrestricted query text",
)


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One emitted metric.

    `labels` passes the prohibited-key guard, and `value` is numeric: a
    telemetry system whose value could be a string is one where a payload
    eventually becomes one."""

    kind: TelemetryKind
    value: int
    labels: Mapping[str, str]
    observed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="TelemetrySample.observed_at")
        reject_prohibited_payload_keys(dict(self.labels), context=f"telemetry {self.kind.value}")


@dataclass(frozen=True, slots=True)
class TraceCorrelation:
    """A trace correlation identifier that is **not** an identity
    correlation identifier (`P13-OBS-003`).

    The distinction is enforced by `carries_subject_reference` being
    fixed to `False`: a trace ID that carried a subject reference across
    domains would be the global correlation key FIR-INV-001 forbids,
    arriving through the observability stack instead of the schema."""

    trace_id: UUID
    span_name: str
    carries_subject_reference: bool = False

    def __post_init__(self) -> None:
        if self.carries_subject_reference:
            raise PermissionDeniedError(
                "a trace correlation identifier is not an identity correlation identifier and "
                "must not become one by carrying a subject reference across domains "
                "(P13-OBS-003)"
            )


@dataclass(frozen=True, slots=True)
class OperationalLogRecord:
    """An operational log line.

    `classification_tier` is required: log volume is not an excuse for
    lower classification, and operational logs containing personal data
    are classified and retained as such (`P13-OBS-004`)."""

    message: str
    classification_tier: str
    recorded_at: datetime
    labels: Mapping[str, str]

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, field="OperationalLogRecord.recorded_at")
        if not self.classification_tier:
            raise PermissionDeniedError(
                "an operational log record carries a classification; log volume is not an "
                "excuse for lower classification (P13-OBS-004)"
            )
        reject_prohibited_payload_keys(dict(self.labels), context="operational log labels")
        if FORBIDDEN_DELIVERY_CLAIM in self.message.lower():
            raise PermissionDeniedError(
                "no log message describes the delivery guarantee with the stronger phrase "
                "(P13-DEL-002)"
            )


def assemble_status_view(
    *,
    status: OperationalStatus,
    schema_review: Sequence[SchemaReviewItem] = (),
    migrations: Sequence[MigrationStatusItem] = (),
    projections: Sequence[ProjectionHealthItem] = (),
    backlogs: Sequence[OutboxBacklogItem] = (),
) -> Mapping[str, object]:
    """Assemble the operational status view from its parts.

    Deliberately takes each surface's already-typed items rather than
    querying anything: this function composes, it does not read. A view
    assembler with database access would be the universal console
    `P13-FE-002` forbids, one refactor later."""
    return _safe_view(
        {
            "observed_at": status.observed_at.isoformat(),
            "implementation_status": status.implementation_status,
            "delivery_guarantee": status.delivery_guarantee,
            "production_infrastructure_active": status.production_infrastructure_active,
            "legally_activated": status.legally_activated,
            "schema_review": [item.to_view() for item in schema_review],
            "migration_status": [item.to_view() for item in migrations],
            "projection_health": [item.to_view() for item in projections],
            "outbox_backlog": [item.to_view() for item in backlogs],
        },
        surface="operational_status",
    )
