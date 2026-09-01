"""Canonical events emitted by the Privileged Access Service (PACK-12
Event Catalog).

Forty-four event types in six families, no more and no fewer. Names carry
the **aggregate prefix**, not a service prefix, following the convention
canon section 20 uses throughout: `privileged_access.requested`, never
`pack12.privileged_access_requested` (`P12-EVT-004`).

The envelope from canon section 21 is used unchanged, so `event_version`
stays at `1.0` and no envelope field is added, removed or reinterpreted
(`P12-EVT-002`).

Two payload jobs, deliberately not interchangeable:

- **State payloads** (`to_state_payload` on the aggregates themselves)
  are full, canonically-hashable snapshots for Audit Core's
  `before_hash`/`after_hash`. They cover every field. None is ever a wire
  payload.
- **Wire payloads** are what the builders below assemble: identifiers,
  enum values, timestamps, one reason code, policy versions, opaque
  references. Nothing else.

Every assembled payload passes through `reject_prohibited_payload_keys`
and `assert_no_voting_material` before an envelope is built, so a future
builder that reaches for a secret or a tally fails closed rather than
shipping it (`P12-EVT-003`).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import (
    ActorRef,
    EventEnvelope,
    SubjectRef,
    build_event_envelope,
)
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import UnknownStatusError
from epd2_privileged_access_service.references import assert_no_voting_material

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})
_PRODUCER = "privileged-access-service"

PRIVILEGED_ACCESS_EVENT_TYPES: tuple[str, ...] = (
    # privileged_access / privileged_session - 11
    "privileged_access.requested",
    "privileged_access.approved",
    "privileged_access.denied",
    "privileged_access.activated",
    "privileged_access.expired",
    "privileged_access.revoked",
    "privileged_session.started",
    "privileged_session.ended",
    "privileged_session.evidence_sealed",
    "privileged_access.review_requested",
    "privileged_access.review_completed",
    # break_glass - 7
    "break_glass.requested",
    "break_glass.approved",
    "break_glass.activated",
    "break_glass.notification_dispatched",
    "break_glass.expired",
    "break_glass.revoked",
    "break_glass.independent_review_completed",
    # search_query / search_index - 8
    "search_query.submitted",
    "search_query.authorized",
    "search_query.denied",
    "search_query.executed",
    "search_query.restricted_result_suppressed",
    "search_index.policy_changed",
    "search_index.reindex_requested",
    "search_index.removal_evidenced",
    # data_export / export_artifact - 11
    "data_export.requested",
    "data_export.dlp_assessment_completed",
    "data_export.disclosure_assessment_completed",
    "data_export.approved",
    "data_export.denied",
    "export_artifact.generated",
    "export_artifact.delivered",
    "export_artifact.accessed",
    "data_export.revoked",
    "export_artifact.expired",
    "data_export.destruction_attested",
    # disclosure_control - 7
    "disclosure_control.risk_assessed",
    "disclosure_control.suppression_applied",
    "disclosure_control.exception_requested",
    "disclosure_control.exception_approved",
    "disclosure_control.exception_denied",
    "disclosure_control.cumulative_risk_flagged",
    "disclosure_control.governed_publication_observed",
)

_EVENT_TYPE_SET: frozenset[str] = frozenset(PRIVILEGED_ACCESS_EVENT_TYPES)

EVENT_AGGREGATE_BY_PREFIX: dict[str, str] = {
    "privileged_access": "privileged_access_grant",
    "privileged_session": "privileged_session",
    "break_glass": "break_glass_activation",
    "search_query": "query_audit",
    "search_index": "index_policy",
    "data_export": "export_request",
    "export_artifact": "export_artifact",
    "disclosure_control": "disclosure_assessment",
}

#: Events that may appear in a public projection. Deliberately empty:
#: every PACK-12 event describes a privileged act, a search, an export or
#: a disclosure decision, and none of those is public information. An
#: empty set is the honest answer, not an oversight.
PUBLIC_PROJECTION_ALLOWED: frozenset[str] = frozenset()


def aggregate_for(event_type: str) -> str:
    prefix = event_type.split(".", 1)[0]
    aggregate = EVENT_AGGREGATE_BY_PREFIX.get(prefix)
    if aggregate is None:
        raise UnknownStatusError(f"unknown PACK-12 event prefix {prefix!r}")
    return aggregate


def assert_known_event_type(event_type: str) -> None:
    if event_type not in _EVENT_TYPE_SET:
        raise UnknownStatusError(f"unknown PACK-12 event type {event_type!r}")


def build_privileged_event(
    *,
    event_id: UUID,
    event_type: str,
    occurred_at: datetime,
    actor: ActorRef,
    aggregate_id: UUID,
    scope: OrganizationalScopeRef,
    payload: Mapping[str, object],
    correlation_id: UUID,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    """Build one canonical envelope.

    The mandatory safe metadata canon 20 requires - the organizational
    scope and the stable aggregate identifier - is added here and not by
    forty-four hand-written copies, so no builder can forget it.

    Both payload guards run before the envelope exists: a payload that
    would carry a secret or a tally never becomes an event, not even
    briefly."""
    assert_known_event_type(event_type)
    require_timezone(occurred_at, context="build_privileged_event.occurred_at")
    body: dict[str, object] = dict(payload)
    body["organization_scope"] = scope.to_payload()
    body["aggregate_id"] = str(aggregate_id)
    reject_prohibited_payload_keys(body, context=f"event {event_type}")
    assert_no_voting_material(body, context=f"event {event_type}")
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type=aggregate_for(event_type), subject_id=aggregate_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=body,
    )


# ---------------------------------------------------------------------------
# Wire payload builders
# ---------------------------------------------------------------------------


def access_requested_payload(
    *,
    request_id: UUID,
    role: str,
    operations: frozenset[str],
    risk_class: str,
    data_classes: frozenset[str],
    purpose: str,
    valid_from: str,
    valid_until: str,
) -> dict[str, object]:
    return {
        "request_id": str(request_id),
        "requested_role": role,
        "requested_operations": sorted(operations),
        "risk_class": risk_class,
        "data_classes": sorted(data_classes),
        "purpose": purpose,
        "valid_from": valid_from,
        "valid_until": valid_until,
    }


def access_decision_payload(
    *,
    grant_id: UUID,
    approver_references: tuple[str, ...],
    reason_code: str,
    policy_version: str,
    evaluation_reference: str | None = None,
) -> dict[str, object]:
    return {
        "grant_id": str(grant_id),
        "approver_count": len(approver_references),
        "reason_code": reason_code,
        "policy_version": policy_version,
        "sod_evaluation_reference": evaluation_reference,
    }


def access_state_payload(
    *, grant_id: UUID, state: str, reason_code: str, policy_version: str, at: str
) -> dict[str, object]:
    return {
        "grant_id": str(grant_id),
        "state": state,
        "reason_code": reason_code,
        "policy_version": policy_version,
        "occurred_at": at,
    }


def session_started_payload(
    *,
    session_id: UUID,
    grant_reference: UUID,
    effective_role: str,
    purpose: str,
    permitted_operations: frozenset[str],
    break_glass_marker: bool,
) -> dict[str, object]:
    return {
        "session_id": str(session_id),
        "grant_reference": str(grant_reference),
        "effective_role": effective_role,
        "purpose": purpose,
        "permitted_operations": sorted(permitted_operations),
        "break_glass_marker": break_glass_marker,
    }


def session_ended_payload(
    *, session_id: UUID, operation_count: int, ended_at: str
) -> dict[str, object]:
    return {
        "session_id": str(session_id),
        "operation_count": operation_count,
        "ended_at": ended_at,
    }


def session_sealed_payload(
    *, session_id: UUID, integrity_reference: str, evidence_bundle_reference: str
) -> dict[str, object]:
    return {
        "session_id": str(session_id),
        "integrity_reference": integrity_reference,
        "evidence_bundle_reference": evidence_bundle_reference,
    }


def review_payload(
    *, review_id: UUID, grant_id: UUID, review_kind: str, outcome: str, reason_code: str
) -> dict[str, object]:
    return {
        "review_id": str(review_id),
        "grant_id": str(grant_id),
        "review_kind": review_kind,
        "outcome": outcome,
        "reason_code": reason_code,
    }


def break_glass_payload(
    *,
    activation_id: UUID,
    condition_reference: str,
    condition_class: str,
    permitted_operations: frozenset[str],
    valid_until: str,
    reason_code: str,
) -> dict[str, object]:
    return {
        "activation_id": str(activation_id),
        "condition_reference": condition_reference,
        "condition_class": condition_class,
        "permitted_operations": sorted(permitted_operations),
        "valid_until": valid_until,
        "reason_code": reason_code,
    }


def notification_dispatched_payload(
    *,
    activation_id: UUID,
    recipient_class: str,
    delivered: bool,
    dispatch_reference: str,
    failure_reason: str | None,
) -> dict[str, object]:
    """Emitted whether the dispatch succeeded or failed.

    A failed dispatch is a governed fact that escalates (`P12-BG-008`),
    so the event exists in both cases and carries the failure reason."""
    return {
        "activation_id": str(activation_id),
        "recipient_class": recipient_class,
        "delivered": delivered,
        "dispatch_reference": dispatch_reference,
        "failure_reason": failure_reason,
    }


def query_submitted_payload(
    *, query_id: UUID, mode: str, purpose: str, query_digest: str, domains: frozenset[str]
) -> dict[str, object]:
    """Carries a query **digest**, never the query string: a query can
    itself contain personal data."""
    return {
        "query_id": str(query_id),
        "mode": mode,
        "purpose": purpose,
        "query_digest": query_digest,
        "domains": sorted(domains),
    }


def query_executed_payload(
    *, query_id: UUID, authorized_count: int, suppressed_band: str, policy_version: str
) -> dict[str, object]:
    """`suppressed_band`, not an exact count: an exact suppression count
    is itself a disclosure of how many restricted records matched."""
    return {
        "query_id": str(query_id),
        "authorized_count": authorized_count,
        "suppressed_band": suppressed_band,
        "policy_version": policy_version,
    }


def query_denied_payload(*, query_id: UUID, reason_code: str) -> dict[str, object]:
    return {"query_id": str(query_id), "reason_code": reason_code}


def query_authorized_payload(
    *, query_id: UUID, mode: str, purpose: str, grant_reference: UUID | None
) -> dict[str, object]:
    """The admission decision, separate from the execution result.

    Carries the grant reference where the purpose required one
    (`GRANT_REQUIRED_PURPOSES`), so an investigative or legal-proceeding
    query can be tied back to the grant that admitted it without reading
    the query itself."""
    return {
        "query_id": str(query_id),
        "mode": mode,
        "purpose": purpose,
        "grant_reference": str(grant_reference) if grant_reference else None,
    }


def query_suppressed_payload(
    *, query_id: UUID, suppressed_band: str, policy_version: str
) -> dict[str, object]:
    """Emitted when a query returned fewer results than it matched.

    A band, never a count, and no reference to what was withheld: the
    identity of a suppressed result is the thing suppression exists to
    protect (`P12-SRCH-007`)."""
    return {
        "query_id": str(query_id),
        "suppressed_band": suppressed_band,
        "policy_version": policy_version,
    }


def index_policy_changed_payload(
    *, index_name: str, previous_version: str, new_version: str, authority_reference: str
) -> dict[str, object]:
    return {
        "index_name": index_name,
        "previous_policy_version": previous_version,
        "new_policy_version": new_version,
        "authority_reference": authority_reference,
    }


def index_removal_payload(
    *, removal_id: UUID, record_reference: str, source_decision_reference: str, reason_code: str
) -> dict[str, object]:
    return {
        "removal_id": str(removal_id),
        "record_reference": record_reference,
        "source_decision_reference": source_decision_reference,
        "reason_code": reason_code,
    }


def export_requested_payload(
    *,
    export_id: UUID,
    purpose: str,
    domains: frozenset[str],
    record_classes: frozenset[str],
    recipient_category: str,
    requested_format: str,
) -> dict[str, object]:
    return {
        "export_id": str(export_id),
        "purpose": purpose,
        "domains": sorted(domains),
        "record_classes": sorted(record_classes),
        "recipient_category": recipient_category,
        "requested_format": requested_format,
    }


def export_assessment_payload(
    *, export_id: UUID, assessment_reference: str, outcome: str, assessment_kind: str
) -> dict[str, object]:
    return {
        "export_id": str(export_id),
        "assessment_reference": assessment_reference,
        "outcome": outcome,
        "assessment_kind": assessment_kind,
    }


def export_decision_payload(
    *,
    export_id: UUID,
    approver_reference: str | None,
    reason_code: str,
    permitted_field_digest: str,
) -> dict[str, object]:
    return {
        "export_id": str(export_id),
        "approver_reference": approver_reference,
        "reason_code": reason_code,
        "permitted_field_digest": permitted_field_digest,
    }


def artifact_generated_payload(
    *, artifact_id: UUID, export_id: UUID, manifest_digest: str, expires_at: str, item_count: int
) -> dict[str, object]:
    return {
        "artifact_id": str(artifact_id),
        "export_id": str(export_id),
        "manifest_digest": manifest_digest,
        "expires_at": expires_at,
        "item_count": item_count,
    }


def artifact_access_payload(
    *, artifact_id: UUID, accessor_reference: str, access_count: int, accessed_at: str
) -> dict[str, object]:
    return {
        "artifact_id": str(artifact_id),
        "accessor_reference": accessor_reference,
        "access_count": access_count,
        "accessed_at": accessed_at,
    }


def export_revoked_payload(
    *, export_id: UUID, revoking_authority: str, reason_code: str
) -> dict[str, object]:
    """Revocation withdraws authorization and blocks further
    platform-mediated access. It is not deletion of a delivered copy, and
    no field here says otherwise (`P12-EXP-013`)."""
    return {
        "export_id": str(export_id),
        "revoking_authority": revoking_authority,
        "reason_code": reason_code,
    }


def destruction_attested_payload(
    *, export_id: UUID, attesting_party: str, attestation_reference: str, attested_at: str
) -> dict[str, object]:
    """Records an **attestation** - a statement by the recipient, not a
    verified fact."""
    return {
        "export_id": str(export_id),
        "attesting_party": attesting_party,
        "attestation_reference": attestation_reference,
        "attested_at": attested_at,
    }


def disclosure_assessed_payload(
    *,
    assessment_id: UUID,
    release_class: str,
    outcome: str,
    rule_families: tuple[str, ...],
    policy_version: str,
) -> dict[str, object]:
    return {
        "assessment_id": str(assessment_id),
        "release_class": release_class,
        "outcome": outcome,
        "rule_families": sorted(rule_families),
        "policy_version": policy_version,
    }


def suppression_applied_payload(
    *, decision_id: UUID, suppressed_count: int, rule_reference: str
) -> dict[str, object]:
    return {
        "decision_id": str(decision_id),
        "suppressed_cohort_count": suppressed_count,
        "rule_reference": rule_reference,
    }


def disclosure_exception_payload(
    *, exception_id: UUID, reviewer_reference: str, approved: bool, reason_code: str
) -> dict[str, object]:
    return {
        "exception_id": str(exception_id),
        "reviewer_reference": reviewer_reference,
        "approved": approved,
        "reason_code": reason_code,
    }


def cumulative_risk_payload(
    *, assessment_id: UUID, release_history_reference: str, rule_reference: str
) -> dict[str, object]:
    return {
        "assessment_id": str(assessment_id),
        "release_history_reference": release_history_reference,
        "rule_reference": rule_reference,
    }


def governed_publication_observed_payload(
    *,
    publication_reference: str,
    certification_reference: str,
    publication_decision_reference: str,
) -> dict[str, object]:
    """PACK-12 observing that a governed publication happened elsewhere.

    Certification, publication-decision and rendition references and **no
    result content**. PACK-12 does not certify, does not decide closure
    and does not publish (`P12-VOTE-005`); an event of this type is never
    evidence that PACK-12 released anything."""
    return {
        "publication_reference": publication_reference,
        "certification_reference": certification_reference,
        "publication_decision_reference": publication_decision_reference,
    }
