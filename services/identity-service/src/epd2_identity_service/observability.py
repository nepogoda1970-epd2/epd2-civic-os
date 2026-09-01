"""Privacy-preserving metrics, and the redaction that makes them safe.

Two obligations, and they pull in opposite directions. Operating an
authentication system needs numbers - success and failure counts, reason
code aggregates, session issue and revoke rates, replay detections,
recovery and proofing workflow counts, adapter failures, latency. Not
disclosing who anyone is needs those numbers to carry no identity.

This module resolves that by making the **label set** the enforcement
point. `MetricLabels` admits only enum-derived, low-information values,
`record()` rejects any label that is not in the permitted set, and a
counter whose label combination could identify a single person is
suppressed below a minimum count.

`redact()` is the other half: every log line and every audit payload this
package produces passes through it, and a value matching any prohibited
key is replaced rather than truncated - a truncated password is still a
password prefix.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from epd2_identity_service.identifiers import (
    PROHIBITED_IDENTIFIER_KEYS,
    PROHIBITED_SECRET_KEYS,
)

#: The replacement value. A fixed string rather than a length-preserving
#: mask, because a mask that preserves length leaks length.
REDACTED = "[redacted]"

#: Below this count a labelled metric is suppressed. A counter reading
#: "1" for a rare label combination is a report about one person.
MINIMUM_DISCLOSABLE_COUNT = 5


class MetricName(StrEnum):
    """Every metric this package emits. A closed set, so a new metric is
    a visible change rather than a string appearing in a log."""

    AUTHENTICATION_SUCCEEDED = "identity_authentication_succeeded_total"
    AUTHENTICATION_FAILED = "identity_authentication_failed_total"
    SESSION_ISSUED = "identity_session_issued_total"
    SESSION_REVOKED = "identity_session_revoked_total"
    SESSION_REPLAY_DETECTED = "identity_session_replay_detected_total"
    STEP_UP_REQUESTED = "identity_step_up_requested_total"
    STEP_UP_SUCCEEDED = "identity_step_up_succeeded_total"
    RECOVERY_REQUESTED = "identity_recovery_requested_total"
    RECOVERY_COMPLETED = "identity_recovery_completed_total"
    PROOFING_STARTED = "identity_proofing_started_total"
    PROOFING_DECIDED = "identity_proofing_decided_total"
    PROVIDER_ADAPTER_FAILED = "identity_provider_adapter_failed_total"
    BOOTSTRAP_REDEEMED = "identity_bootstrap_redeemed_total"
    VOTING_HANDOFF_ISSUED = "identity_voting_handoff_issued_total"
    VOTING_HANDOFF_REFUSED = "identity_voting_handoff_refused_total"
    OPERATION_LATENCY_MS = "identity_operation_latency_ms"


#: The only label keys any metric may carry. Every one of them is an enum
#: value or a registered reason code - a closed, low-cardinality domain.
#: There is no `account`, no `subject` and no `origin` label, because each
#: would make the metric a per-person time series.
PERMITTED_LABEL_KEYS: frozenset[str] = frozenset(
    {
        "method_class",
        "factor_class",
        "reason_code",
        "workspace",
        "assurance_level",
        "outcome",
        "risk_state",
        "operation",
    }
)


@dataclass(frozen=True, slots=True)
class MetricLabels:
    """A validated label set."""

    values: Mapping[str, str]

    def __post_init__(self) -> None:
        unknown = set(self.values) - PERMITTED_LABEL_KEYS
        if unknown:
            raise ValueError(
                f"metric labels admit only {sorted(PERMITTED_LABEL_KEYS)}; got {sorted(unknown)}"
            )
        for key, value in self.values.items():
            if len(value) > 64:
                raise ValueError(f"label {key!r} is too high-cardinality to be a label")

    def key(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self.values.items()))


@dataclass
class MetricsRecorder:
    """An in-memory counter set with a disclosure floor.

    A reference adapter: a deployment binds a real backend. What is
    **not** the deployment's choice is the label validation and the
    suppression floor, both of which live here so no backend can be
    configured out of them.
    """

    counters: dict[tuple[MetricName, tuple[tuple[str, str], ...]], int] = field(
        default_factory=dict
    )

    def record(self, metric: MetricName, labels: MetricLabels, *, value: int = 1) -> None:
        key = (metric, labels.key())
        self.counters[key] = self.counters.get(key, 0) + value

    def disclosable(self) -> dict[tuple[MetricName, tuple[tuple[str, str], ...]], int]:
        """Only the series that clear the floor.

        Series below `MINIMUM_DISCLOSABLE_COUNT` are withheld entirely
        rather than rounded: a rounded low count still tells a reader
        that the combination occurred at all, which for a rare label set
        is the disclosure.
        """
        return {
            key: count for key, count in self.counters.items() if count >= MINIMUM_DISCLOSABLE_COUNT
        }


def redact(payload: Mapping[str, object]) -> dict[str, object]:
    """Replace every prohibited value before anything is logged.

    Walks nested mappings and sequences, because a secret one level down
    is still a secret. Returns a new mapping rather than mutating, so a
    caller cannot accidentally log the original after redacting a copy.
    """
    prohibited = PROHIBITED_SECRET_KEYS | PROHIBITED_IDENTIFIER_KEYS
    redacted: dict[str, object] = {}
    for key, value in payload.items():
        if key in prohibited:
            redacted[key] = REDACTED
        elif isinstance(value, Mapping):
            redacted[key] = redact(value)
        elif isinstance(value, list | tuple):
            redacted[key] = [redact(item) if isinstance(item, Mapping) else item for item in value]
        else:
            redacted[key] = value
    return redacted


def assert_no_secret_in_log_line(line: str, *, known_secrets: tuple[str, ...]) -> None:
    """A belt-and-braces check for the log path.

    `redact()` handles structured payloads; this catches the case where a
    secret was interpolated into a formatted string before it reached
    one. Test-only in practice, and cheap enough to keep on the real path
    where a deployment wants it.
    """
    for secret in known_secrets:
        if secret and secret in line:
            from epd2_identity_service.exceptions import SecretInPayloadRefusedError

            raise SecretInPayloadRefusedError("a secret value reached a log line")
