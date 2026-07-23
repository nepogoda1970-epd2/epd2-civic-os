"""Transparency Service exceptions, tied to stable reason codes (ADR-004 /
ADR-006 / ADR-014 pattern: one exception class per distinct failure shape,
never free text — canon section 24: "reason code не заменяется свободным
текстом"). The five codes ADR-014 adds for this pack —
`DISCLOSURE_POLICY_VIOLATION`, `PUBLICATION_NOT_ALLOWED`,
`REDACTION_REQUIRED`, `LOBBY_LOG_ENTRY_INCOMPLETE`,
`AUDIT_EXPORT_INTEGRITY_FAILED`, `LEDGER_ENTRY_ALREADY_PUBLISHED` — are
each represented here by exactly one class.
"""

from __future__ import annotations


class UnknownAuditExportPackageStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenAuditExportPackageTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownDisclosurePolicyStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenDisclosurePolicyTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownLobbyLogEntryStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenLobbyLogEntryTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownPublicLedgerEntryError(ValueError):
    """Plain lookup miss — no `PublicLedgerEntry` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAuditExportPackageError(ValueError):
    """Plain lookup miss — no `AuditExportPackage` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownDisclosurePolicyError(ValueError):
    """Plain lookup miss — no `DisclosurePolicy` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownLobbyLogEntryError(ValueError):
    """Plain lookup miss — no `LobbyLogEntry` exists for the given id."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class PublicLedgerEntryConflictError(ValueError):
    """A repeated `publish_ledger_entry`/`correct_ledger_entry` request
    with the same `public_ledger_entry_id` but different content."""

    reason_code = "LEDGER_ENTRY_DUPLICATE_CONFLICT"


class AuditExportPackageConflictError(ValueError):
    """A repeated `generate_audit_export_package` request with the same
    `audit_export_package_id` but different content."""

    reason_code = "AUDIT_EXPORT_PACKAGE_DUPLICATE_CONFLICT"


class DisclosurePolicyConflictError(ValueError):
    """A repeated `define_disclosure_policy` request with the same
    `disclosure_policy_id` but different content."""

    reason_code = "DISCLOSURE_POLICY_DUPLICATE_CONFLICT"


class LobbyLogEntryConflictError(ValueError):
    """A repeated `submit_lobby_log_entry` request with the same
    `lobby_log_entry_id` but different content."""

    reason_code = "LOBBY_LOG_ENTRY_DUPLICATE_CONFLICT"


class LedgerEntryAlreadyPublishedError(ValueError):
    """ADR-014 code. Raised by `application.publish_ledger_entry` when a
    non-superseded `PublicLedgerEntry` already exists for the same
    `subject_event_id` — the caller must use `correct_ledger_entry`
    instead of publishing a second, unrelated entry for the same
    underlying domain event."""

    reason_code = "LEDGER_ENTRY_ALREADY_PUBLISHED"


class DisclosurePolicyViolationError(ValueError):
    """ADR-014 code. Raised when applying a `DisclosurePolicy` to
    candidate content would still leave a structurally forbidden field
    present — a defense-in-depth check; this should never be reachable
    given `domain.assert_no_forbidden_fields`'s unconditional filtering,
    but the code exists so the failure mode has a stable, importable
    identity if it is ever reached."""

    reason_code = "DISCLOSURE_POLICY_VIOLATION"


class PublicationNotAllowedError(ValueError):
    """ADR-014 code. Raised when no `active` `DisclosurePolicy` exists for
    the relevant `applies_to_subject_type` at the moment a publish command
    is attempted — publication cannot proceed with no governing policy
    (fail-closed, INV-10)."""

    reason_code = "PUBLICATION_NOT_ALLOWED"


class RedactionRequiredError(ValueError):
    """ADR-014 code. Reserved for a caller that explicitly demands a field
    be disclosed as `public` when `domain.resolve_field_rule` has resolved
    it to `prohibited` (missing or ambiguous rule) — `apply_disclosure_
    policy` itself never raises this (it silently drops the field,
    fail-closed); this class exists for any future caller-facing API that
    wants to surface the distinction between "silently redacted" and "the
    caller's request was itself invalid"."""

    reason_code = "REDACTION_REQUIRED"


class LobbyLogEntryIncompleteError(ValueError):
    """ADR-014 code. Raised by `application.submit_lobby_log_entry` (and
    re-checked by `publish_lobby_log_entry`) when a mandatory field
    (`organization_name`, `related_subject_type`, `related_subject_id`,
    `contact_date`, `topic_summary`, `submitted_by_role_id`) is missing or
    empty — canon section 19a.4: an entry "отсутствующим обязательным
    полем отклоняется при подаче" (rejected on submission if a mandatory
    field is missing) and "публикуется в неполном виде" never happens
    (never published incomplete)."""

    reason_code = "LOBBY_LOG_ENTRY_INCOMPLETE"


class AuditExportIntegrityFailedError(ValueError):
    """ADR-014 code. Raised by `application.verify_audit_export_package`
    when a recomputed digest over `chain_proof` does not match the
    package's stored `package_digest` — the public, chain-continuity/
    non-modification check canon section 19a.2's "Семантика проверки"
    describes (never a check of the original private `AuditEvent.
    event_hash` values themselves)."""

    reason_code = "AUDIT_EXPORT_INTEGRITY_FAILED"
