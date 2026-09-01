"""Logging boundary (PACK-16D §46).

The reference implementation logs through one narrow structured sink. The
sink accepts an allow-list of field names and rejects everything else,
including field names that merely *look* like a forbidden one. There is no
redaction step: a forbidden field is a defect in the caller, not a value to
be masked, so the record is refused and the failure surfaces in tests.

This is a field-name boundary. It cannot detect a capability reference
smuggled inside an allowed free-text field, which is why
``ALLOWED_FIELDS`` contains no free-text field and ``reason_code`` is
constrained to the PACK-16C catalogue shape.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

#: Never logged, under any level, in any environment.
FORBIDDEN_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "continuation_capability",
        "capability",
        "capability_reference",
        "credential",
        "credential_id",
        "identity",
        "identity_id",
        "voter_id",
        "member_id",
        "ballot_plaintext",
        "plaintext",
        "ballot_nonce",
        "nonce",
        "exact_timestamp",
        "timestamp",
        "ip",
        "ip_address",
        "client_ip",
        "challenge_to_cast_correlation",
        "trace_id",
        "correlation_id",
        "session_id",
        "user_agent",
    }
)

#: The complete set of loggable fields. Nothing else may be emitted.
ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        "component",
        "reason_code",
        "coarse_time_bucket",
        "election_context_id",
        "outcome",
        "count",
        "internal_transaction_id",
    }
)

_REASON_CODE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$|^[A-Z][A-Z0-9_]*$")


class ForbiddenLogFieldError(RuntimeError):
    """A caller tried to log a field outside the allow-list."""

    reason_code = "LOG_FIELD_REJECTED"


@dataclass(frozen=True, slots=True)
class LogRecord:
    """A record that has already passed the boundary."""

    component: str
    reason_code: str
    fields: tuple[tuple[str, str], ...]


def _check(name: str) -> str:
    normalized = name.strip().lower()
    if normalized in FORBIDDEN_LOG_FIELDS:
        raise ForbiddenLogFieldError(f"field {name!r} is forbidden in logs")
    if normalized not in ALLOWED_FIELDS:
        raise ForbiddenLogFieldError(
            f"field {name!r} is not in the logging allow-list; add it to the "
            "PACK-16D logging boundary with a decision, or do not log it"
        )
    return normalized


@dataclass
class ReferenceLogger:
    """Structured logger with a hard allow-list. Never formats free text.

    ``internal_transaction_id`` is accepted because §46 permits a
    non-sensitive internal transaction identifier. The three rules that
    make it safe — not exported, not shared across an identity domain,
    never election-record material — are obligations on whoever mints it.
    **No code here enforces them and no test verifies them**, because the
    reference implementation never mints one: the field exists so that a
    caller which does has a declared place to put it. Verifying those
    rules against a real minting path is a PACK-17 obligation.
    """

    component: str
    records: list[LogRecord] = field(default_factory=list)

    def emit(self, reason_code: str, **fields: object) -> LogRecord:
        if not _REASON_CODE.match(reason_code):
            raise ForbiddenLogFieldError(
                f"reason_code {reason_code!r} is not a catalogue reason code"
            )
        checked: list[tuple[str, str]] = []
        for name, value in sorted(fields.items()):
            checked.append((_check(name), str(value)))
        record = LogRecord(component=self.component, reason_code=reason_code, fields=tuple(checked))
        self.records.append(record)
        return record


def scan_mapping(payload: Mapping[str, object]) -> tuple[str, ...]:
    """Return any forbidden field names present. Used by event tests too."""
    return tuple(sorted(name for name in payload if name.strip().lower() in FORBIDDEN_LOG_FIELDS))
