"""Redaction/provenance validation abstraction (canon 19c.4; required
scope item 6, ADR-025 §1). `ai-processing-service` performs this
validation itself — a caller-supplied `redaction_applied`-style boolean
is never trusted; `application.prepare_input` only ever accepts a
`RedactionManifest` produced by calling a `RedactionValidator`, never one
handed to it directly by a caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_ai_processing_service.domain import RedactionManifest


@dataclass(frozen=True, slots=True)
class RedactionValidationRequest:
    ai_processing_record_id: UUID
    input_reference: str
    declared_input_classification: str
    now: datetime


class RedactionValidator(Protocol):
    def validate(self, request: RedactionValidationRequest) -> RedactionManifest:
        """Always returns a `RedactionManifest` — a `result = fail`
        outcome is itself a fixed, recorded fact about this attempt
        (canon 19c.4), never something this method raises an exception
        for instead of reporting structurally."""
        ...


class ScriptedRedactionValidator:
    """In-memory, deterministic test double — returns a pre-configured
    `RedactionManifest` regardless of the request. The real production
    validator's actual detection algorithm is out of this pack's scope;
    only the structural contract (a manifest is always produced by this
    service itself, never accepted from a caller) is implemented here.
    """

    def __init__(self, manifest: RedactionManifest) -> None:
        self._manifest = manifest
        self.validated: list[RedactionValidationRequest] = []

    def validate(self, request: RedactionValidationRequest) -> RedactionManifest:
        self.validated.append(request)
        return self._manifest
