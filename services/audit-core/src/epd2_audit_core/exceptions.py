"""Audit Core exceptions.

Each maps to a stable reason code from `contracts/reason-codes/pack-02.yml`
(`AUDIT_*` group) - the reason code string itself lives on the exception so
callers can surface it without inventing free text (pack section 10).
"""

from __future__ import annotations


class AuditEventConflictError(ValueError):
    """Raised when appending an `audit_event_id` that already exists with
    different content. Reason code: `AUDIT_EVENT_CONFLICT`.
    """

    reason_code = "AUDIT_EVENT_CONFLICT"


class AuditChainBrokenError(ValueError):
    """Raised by `verify_chain` callers (or internal consistency checks)
    when a stored record's `previous_event_hash` does not match the prior
    record's `event_hash`. Reason code: `AUDIT_CHAIN_BROKEN`.
    """

    reason_code = "AUDIT_CHAIN_BROKEN"
