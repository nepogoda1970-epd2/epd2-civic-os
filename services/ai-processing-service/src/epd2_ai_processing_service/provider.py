"""Model/provider abstraction (required scope item 12; ADR-025 §6, canon
19c.9's "no external model provider ever gains Civic OS mutation
authority" invariant).

`AIModelProvider` is deliberately the narrowest possible surface: one
method to submit prepared input and get structured output back, one
method to best-effort cancel. **There is no callback, tool-calling, or
command-issuing parameter anywhere on this Protocol** — a provider
implementation structurally cannot be handed any interface capable of
mutating Civic OS, because no such interface is ever constructed or
passed to it in the first place. Real external provider credentials and
any live third-party integration are explicitly out of this pack's scope
(required scope item 19) — only this abstraction and a scripted,
in-memory test double exist here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from epd2_ai_processing_service.domain import UseClass
from epd2_ai_processing_service.exceptions import AIPolicyConflictError

#: Repository-side, closed allow-list of processing regions this pack
#: recognizes at all — anything else (including `None`) is fail-closed
#: for an external-provider submission (required scope item 12: "unknown
#: retention mode or processing region is fail-closed").
KNOWN_PROCESSING_REGIONS: frozenset[str] = frozenset({"eu", "eu-central", "eu-west"})

#: Repository-side, closed allow-list of data-retention modes.
KNOWN_DATA_RETENTION_MODES: frozenset[str] = frozenset({"none", "ephemeral", "policy_defined"})

#: Use classes an external (non-self-hosted) provider may ever be used
#: for — deliberately narrow ("explicitly approved, sufficiently
#: redacted low-risk classes", required scope item 12). Every other use
#: class, including `anomaly_indication` (self-hosted processing is
#: mandatory for it, never merely preferred), is self-hosted-only.
LOW_RISK_EXTERNAL_PROVIDER_USE_CLASSES: frozenset[UseClass] = frozenset(
    {UseClass.SUMMARIZATION, UseClass.DRAFTING, UseClass.RECOMMENDATION}
)


def assert_external_provider_use_allowed(
    use_class: UseClass,
    *,
    external_provider_flag: bool,
    processing_region: str | None,
    data_retention_mode: str | None,
) -> None:
    """Fail-closed gate on whether an external provider may be used at
    all for this run. A purely self-hosted submission
    (`external_provider_flag = False`) is never restricted by this
    function."""
    if not external_provider_flag:
        return
    if use_class not in LOW_RISK_EXTERNAL_PROVIDER_USE_CLASSES:
        raise AIPolicyConflictError(
            f"external providers are not approved for use class {use_class.value!r} "
            "(self-hosted processing is required)"
        )
    if processing_region is None or processing_region not in KNOWN_PROCESSING_REGIONS:
        raise AIPolicyConflictError(
            f"unknown processing_region {processing_region!r} is fail-closed for an external "
            "provider submission"
        )
    if data_retention_mode is None or data_retention_mode not in KNOWN_DATA_RETENTION_MODES:
        raise AIPolicyConflictError(
            f"unknown data_retention_mode {data_retention_mode!r} is fail-closed for an "
            "external provider submission"
        )


@dataclass(frozen=True, slots=True)
class PreparedInputSubmission:
    """Everything a provider needs to process a request — deliberately
    excludes any raw, unredacted content; `prepared_input_reference` is
    an opaque reference to input that has already passed redaction
    validation (`processing_status = input_prepared`), never the raw
    input itself."""

    ai_processing_record_id: UUID
    model_provider: str
    model_name: str
    model_version: str
    deployment_version: str | None
    processing_region: str | None
    data_retention_mode: str | None
    external_provider_flag: bool
    prepared_input_reference: str
    generation_settings: dict[str, object] | None
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class ProviderOutcome:
    output_reference: str
    output_hash: str
    confidence_score: float | None
    uncertainty_indicator: str | None
    explanation_reference: str | None
    reason_codes: tuple[str, ...]


class AIModelProvider(Protocol):
    """No callback, tool, or command interface capable of mutating Civic
    OS is ever a parameter here — this Protocol's narrowness is itself
    the structural enforcement of that invariant (required scope item
    12; canon 19c.9)."""

    def submit(self, submission: PreparedInputSubmission) -> ProviderOutcome:
        """Raises `exceptions.AIModelUnavailableError`,
        `exceptions.AIProcessingTimeoutError`,
        `exceptions.AIOutputMalformedError`, or
        `exceptions.AIModelVersionUnsupportedError` — deterministic error
        mapping (ADR-025 §6), never an unmapped/raw provider exception."""
        ...

    def cancel(self, ai_processing_record_id: UUID) -> None:
        """Best-effort cancellation. A provider with no true cancel
        support may implement this as a no-op."""
        ...


class ScriptedAIModelProvider:
    """In-memory, deterministic test double — the only `AIModelProvider`
    implementation this pack ships (real external provider credentials
    are out of scope, required scope item 19). Configured with either a
    fixed `ProviderOutcome` to return or an exception instance/type to
    raise on `submit`."""

    def __init__(
        self,
        *,
        outcome: ProviderOutcome | None = None,
        raises: BaseException | type[BaseException] | None = None,
    ) -> None:
        if (outcome is None) == (raises is None):
            raise ValueError("exactly one of outcome/raises must be provided")
        self._outcome = outcome
        self._raises = raises
        self.submitted: list[PreparedInputSubmission] = []
        self.cancelled: list[UUID] = []

    def submit(self, submission: PreparedInputSubmission) -> ProviderOutcome:
        self.submitted.append(submission)
        if self._raises is not None:
            if isinstance(self._raises, type):
                raise self._raises("scripted provider failure")
            raise self._raises
        assert self._outcome is not None
        return self._outcome

    def cancel(self, ai_processing_record_id: UUID) -> None:
        self.cancelled.append(ai_processing_record_id)
