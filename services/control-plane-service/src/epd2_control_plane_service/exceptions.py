"""Reason-coded control-plane refusals.

Every refusal carries a stable `reason_code`. Refusals are evidence-bearing
events, not silent denials: the application layer records each one on the
immutable journal before raising, so that an attempted escalation leaves the
same audit trail as a successful act.
"""

from __future__ import annotations

__all__ = [
    "AuthorizationRefused",
    "ControlPlaneError",
    "EvidenceIntegrityError",
    "InventoryError",
    "PrivacyBoundaryViolation",
    "VotingBoundaryViolation",
]


class ControlPlaneError(Exception):
    """Base class. `reason_code` is stable and machine-readable."""

    reason_code = "CTRL_ERROR"

    def __init__(self, message: str, *, reason_code: str | None = None) -> None:
        super().__init__(message)
        if reason_code is not None:
            self.reason_code = reason_code


class AuthorizationRefused(ControlPlaneError):
    """The requested control act is not authorized in the current state."""

    reason_code = "CTRL_AUTHORIZATION_REFUSED"


class InventoryError(ControlPlaneError):
    """The action inventory is missing, malformed or inconsistent with the
    runtime. This always fails closed: an unmapped runtime mutation is refused
    rather than executed under a default policy."""

    reason_code = "CTRL_INVENTORY_INCONSISTENT"


class EvidenceIntegrityError(ControlPlaneError):
    """An attempt to rewrite, delete or reorder historical evidence."""

    reason_code = "CTRL_EVIDENCE_IMMUTABLE"


class PrivacyBoundaryViolation(ControlPlaneError):
    """Evidence carried a protected payload, secret or excess personal data."""

    reason_code = "CTRL_PRIVACY_MINIMIZATION"


class VotingBoundaryViolation(ControlPlaneError):
    """A control act attempted to reach into the voting trust domain."""

    reason_code = "CTRL_VOTING_BOUNDARY"
