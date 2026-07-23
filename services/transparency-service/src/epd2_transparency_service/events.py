"""Canonical events emitted by Transparency Service.

Verbatim event-name list, canon section 20.14 (added by canon 0.3.0,
ADR-013): `transparency.ledger_entry_published`,
`transparency.ledger_entry_corrected`, `transparency.audit_export_generated`,
`transparency.audit_export_published`, `transparency.disclosure_policy_defined`,
`transparency.disclosure_policy_activated`,
`transparency.disclosure_policy_superseded`,
`transparency.lobby_log_entry_submitted`, `transparency.lobby_log_entry_published`,
`transparency.lobby_log_entry_corrected`.

`*_corrected` events are emitted when a new, superseding row is created —
never when an existing row is mutated (canon section 20.14: "не при
изменении существующей строки, поскольку такое изменение не допускается").

This module is also where canon section 19a.6's "never published verbatim"
rule for the four `*_role_id` fields is actually drawn: every
`*_public_payload` function below omits them entirely (there is no
`replacement_label` substitution at this layer, since none of the four
entities' own canon field lists include a `*_role_label` field — a future
pack that wants to surface a generalized role-scope label in the public
payload would add that as its own additive field, not by leaking the raw
role id here in the meantime).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_transparency_service.domain import (
    AuditExportPackage,
    DisclosurePolicy,
    LobbyLogEntry,
    PublicLedgerEntry,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


# ---------------------------------------------------------------------------
# PublicLedgerEntry payloads/events
# ---------------------------------------------------------------------------


def ledger_entry_public_payload(entry: PublicLedgerEntry) -> dict[str, object]:
    """Public event payload for a `PublicLedgerEntry` — omits
    `published_by_role_id` entirely (canon section 19a.6)."""
    return {
        "public_ledger_entry_id": str(entry.public_ledger_entry_id),
        "subject_type": entry.subject_type.value,
        "subject_id": str(entry.subject_id),
        "subject_event_id": str(entry.subject_event_id),
        "published_at": entry.published_at.isoformat(),
        "content_snapshot": dict(entry.content_snapshot),
        "content_hash": entry.content_hash,
        "previous_entry_hash": entry.previous_entry_hash,
        "disclosure_policy_id": str(entry.disclosure_policy_id),
        "redaction_notice": entry.redaction_notice,
        "supersedes_entry_id": (
            str(entry.supersedes_entry_id) if entry.supersedes_entry_id is not None else None
        ),
        "status": entry.status.value,
    }


def ledger_entry_full_state_payload(entry: PublicLedgerEntry) -> dict[str, object]:
    """Full snapshot including `published_by_role_id`, used only for Audit
    Core's `before_hash`/`after_hash` (an internal, non-public audit
    record) — never for the public event payload or `PublicLedgerEntry`
    publication itself."""
    payload = ledger_entry_public_payload(entry)
    payload["published_by_role_id"] = str(entry.published_by_role_id)
    return payload


def build_ledger_entry_published_event(
    *,
    event_id: UUID,
    entry: PublicLedgerEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.ledger_entry_published",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="public_ledger_entry", subject_id=entry.public_ledger_entry_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=ledger_entry_public_payload(entry),
    )


def build_ledger_entry_corrected_event(
    *,
    event_id: UUID,
    entry: PublicLedgerEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.ledger_entry_corrected",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="public_ledger_entry", subject_id=entry.public_ledger_entry_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=ledger_entry_public_payload(entry),
    )


# ---------------------------------------------------------------------------
# AuditExportPackage payloads/events
# ---------------------------------------------------------------------------


def audit_export_package_public_payload(package: AuditExportPackage) -> dict[str, object]:
    """Public event payload for an `AuditExportPackage` — omits
    `requested_by_role_id` entirely (canon section 19a.6). `chain_proof`
    items are already public-safe by construction (`domain.ChainProofItem`
    never carries `actor_id`/`actor_type`/`before_hash`/`after_hash`)."""
    return {
        "audit_export_package_id": str(package.audit_export_package_id),
        "scope_description": package.scope_description,
        "included_target_types": [t.value for t in package.included_target_types],
        "event_count": package.event_count,
        "chain_proof": [
            {
                "event_hash": item.event_hash,
                "previous_event_hash": item.previous_event_hash,
                "event_type": item.event_type,
                "occurred_at": item.occurred_at.isoformat(),
                "target_type": item.target_type,
                "target_id": str(item.target_id),
                "action": item.action,
                "reason_code": item.reason_code,
                "correlation_id": str(item.correlation_id),
                "source_service": item.source_service,
                "sequence_position": item.sequence_position,
            }
            for item in package.chain_proof
        ],
        "package_digest": package.package_digest,
        "integrity_proof": package.integrity_proof,
        "generated_at": package.generated_at.isoformat(),
        "redaction_notice": package.redaction_notice,
        "supersedes_package_id": (
            str(package.supersedes_package_id)
            if package.supersedes_package_id is not None
            else None
        ),
        "status": package.status.value,
    }


def audit_export_package_full_state_payload(package: AuditExportPackage) -> dict[str, object]:
    """Full snapshot including `requested_by_role_id`, used only for Audit
    Core's `before_hash`/`after_hash`."""
    payload = audit_export_package_public_payload(package)
    payload["requested_by_role_id"] = str(package.requested_by_role_id)
    return payload


def build_audit_export_generated_event(
    *,
    event_id: UUID,
    package: AuditExportPackage,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.audit_export_generated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="audit_export_package", subject_id=package.audit_export_package_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=audit_export_package_public_payload(package),
    )


def build_audit_export_published_event(
    *,
    event_id: UUID,
    package: AuditExportPackage,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.audit_export_published",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="audit_export_package", subject_id=package.audit_export_package_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=audit_export_package_public_payload(package),
    )


# ---------------------------------------------------------------------------
# DisclosurePolicy payloads/events
# ---------------------------------------------------------------------------


def disclosure_policy_public_payload(policy: DisclosurePolicy) -> dict[str, object]:
    """Public event payload for a `DisclosurePolicy` — omits
    `approved_by_role_id` entirely (canon section 19a.6)."""
    return {
        "disclosure_policy_id": str(policy.disclosure_policy_id),
        "applies_to_subject_type": policy.applies_to_subject_type,
        "field_rules": [
            {
                "field_path": r.field_path,
                "disclosure_class": r.disclosure_class.value,
                "transformation": r.transformation.value,
                "replacement_label": r.replacement_label,
            }
            for r in policy.field_rules
        ],
        "small_cell_threshold": policy.small_cell_threshold,
        "effective_from": policy.effective_from.isoformat(),
        "version": policy.version,
        "status": policy.status.value,
    }


def disclosure_policy_full_state_payload(policy: DisclosurePolicy) -> dict[str, object]:
    """Full snapshot including `approved_by_role_id`, used only for Audit
    Core's `before_hash`/`after_hash`."""
    payload = disclosure_policy_public_payload(policy)
    payload["approved_by_role_id"] = (
        str(policy.approved_by_role_id) if policy.approved_by_role_id is not None else None
    )
    return payload


def build_disclosure_policy_defined_event(
    *,
    event_id: UUID,
    policy: DisclosurePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.disclosure_policy_defined",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="disclosure_policy", subject_id=policy.disclosure_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=disclosure_policy_public_payload(policy),
    )


def build_disclosure_policy_activated_event(
    *,
    event_id: UUID,
    policy: DisclosurePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.disclosure_policy_activated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="disclosure_policy", subject_id=policy.disclosure_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=disclosure_policy_public_payload(policy),
    )


def build_disclosure_policy_superseded_event(
    *,
    event_id: UUID,
    policy: DisclosurePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.disclosure_policy_superseded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="disclosure_policy", subject_id=policy.disclosure_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=disclosure_policy_public_payload(policy),
    )


# ---------------------------------------------------------------------------
# LobbyLogEntry payloads/events
# ---------------------------------------------------------------------------


def lobby_log_entry_public_payload(entry: LobbyLogEntry) -> dict[str, object]:
    """Public event payload for a `LobbyLogEntry` — omits
    `submitted_by_role_id` entirely (canon section 19a.6)."""
    return {
        "lobby_log_entry_id": str(entry.lobby_log_entry_id),
        "organization_name": entry.organization_name,
        "related_subject_type": entry.related_subject_type.value,
        "related_subject_id": str(entry.related_subject_id),
        "contact_date": entry.contact_date.isoformat(),
        "contact_method": entry.contact_method.value,
        "topic_summary": entry.topic_summary,
        "submitted_at": entry.submitted_at.isoformat(),
        "published_at": entry.published_at.isoformat() if entry.published_at is not None else None,
        "supersedes_entry_id": (
            str(entry.supersedes_entry_id) if entry.supersedes_entry_id is not None else None
        ),
        "status": entry.status.value,
    }


def lobby_log_entry_full_state_payload(entry: LobbyLogEntry) -> dict[str, object]:
    """Full snapshot including `submitted_by_role_id`, used only for Audit
    Core's `before_hash`/`after_hash`."""
    payload = lobby_log_entry_public_payload(entry)
    payload["submitted_by_role_id"] = str(entry.submitted_by_role_id)
    return payload


def build_lobby_log_entry_submitted_event(
    *,
    event_id: UUID,
    entry: LobbyLogEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.lobby_log_entry_submitted",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(subject_type="lobby_log_entry", subject_id=entry.lobby_log_entry_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=lobby_log_entry_public_payload(entry),
    )


def build_lobby_log_entry_published_event(
    *,
    event_id: UUID,
    entry: LobbyLogEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.lobby_log_entry_published",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(subject_type="lobby_log_entry", subject_id=entry.lobby_log_entry_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=lobby_log_entry_public_payload(entry),
    )


def build_lobby_log_entry_corrected_event(
    *,
    event_id: UUID,
    entry: LobbyLogEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="transparency.lobby_log_entry_corrected",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="transparency-service",
        actor=actor,
        subject=SubjectRef(subject_type="lobby_log_entry", subject_id=entry.lobby_log_entry_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=lobby_log_entry_public_payload(entry),
    )
