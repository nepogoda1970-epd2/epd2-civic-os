"""Generic reason-code registry infrastructure.

Per CLAUDE-PACK-02 section 4.2, shared packages may contain "reason-code
infrastructure without domain decisions". This module provides the
`ReasonCode` value object and a registry that loads entries from a YAML
file (e.g. `contracts/reason-codes/pack-02.yml`) - it does not hardcode
which reason codes exist. Domain services import this module and load
their own package's registry file; they never invent ad-hoc string
reasons (CLAUDE-PACK-02 section 10: "Нельзя использовать произвольные
строки ошибок вместо reason codes").
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without the dependency
    raise ModuleNotFoundError(
        "epd2_core.reason_codes requires PyYAML. Install project dependencies "
        "with `uv sync --all-groups` (see LOCAL_VERIFICATION.md)."
    ) from exc

_REQUIRED_FIELDS = (
    "code",
    "meaning",
    "severity",
    "description",
    "retryable",
    "owner",
    "introduced_in_version",
)
_VALID_SEVERITIES = frozenset({"info", "warning", "error", "critical"})


class UnknownReasonCodeError(KeyError):
    """Raised when a code is requested that is not present in the registry."""


class InvalidReasonCodeRegistryError(ValueError):
    """Raised when a reason-code registry file is malformed."""


@dataclass(frozen=True, slots=True)
class ReasonCode:
    """A single, stable reason code entry."""

    code: str
    meaning: str
    severity: str
    description: str
    retryable: bool
    owner: str
    introduced_in_version: str

    def __post_init__(self) -> None:
        if not self.code:
            raise InvalidReasonCodeRegistryError("reason code 'code' must not be empty")
        if self.severity not in _VALID_SEVERITIES:
            raise InvalidReasonCodeRegistryError(
                f"reason code {self.code!r} has invalid severity {self.severity!r}; "
                f"must be one of {sorted(_VALID_SEVERITIES)}"
            )


class ReasonCodeRegistry:
    """An immutable, loaded set of `ReasonCode` entries, keyed by `code`."""

    def __init__(self, codes: Mapping[str, ReasonCode]) -> None:
        self._codes = dict(codes)

    @classmethod
    def load_from_yaml(cls, path: Path) -> ReasonCodeRegistry:
        """Load a registry from a YAML file shaped as a top-level list of
        mappings, each with the fields in `_REQUIRED_FIELDS`.
        """
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise InvalidReasonCodeRegistryError(
                f"{path}: expected a top-level YAML list of reason-code entries"
            )
        codes: dict[str, ReasonCode] = {}
        for index, entry in enumerate(raw):
            if not isinstance(entry, dict):
                raise InvalidReasonCodeRegistryError(f"{path}: entry #{index} is not a mapping")
            missing = [f for f in _REQUIRED_FIELDS if f not in entry]
            if missing:
                raise InvalidReasonCodeRegistryError(
                    f"{path}: entry #{index} ({entry.get('code', '?')!r}) missing fields: {missing}"
                )
            code = entry["code"]
            if code in codes:
                raise InvalidReasonCodeRegistryError(f"{path}: duplicate reason code {code!r}")
            codes[code] = ReasonCode(
                code=code,
                meaning=str(entry["meaning"]),
                severity=str(entry["severity"]),
                description=str(entry["description"]),
                retryable=bool(entry["retryable"]),
                owner=str(entry["owner"]),
                introduced_in_version=str(entry["introduced_in_version"]),
            )
        return cls(codes)

    def get(self, code: str) -> ReasonCode | None:
        return self._codes.get(code)

    def require(self, code: str) -> ReasonCode:
        """Return the `ReasonCode` for `code`, or raise
        `UnknownReasonCodeError` if it is not registered. Domain code
        should call this (not `get`) wherever a reason code is about to be
        returned to a caller, so an unregistered/misspelled code fails
        loudly instead of silently becoming a free-text string.
        """
        found = self._codes.get(code)
        if found is None:
            raise UnknownReasonCodeError(code)
        return found

    def __contains__(self, code: object) -> bool:
        return code in self._codes

    def __len__(self) -> int:
        return len(self._codes)

    def all_codes(self) -> tuple[str, ...]:
        return tuple(sorted(self._codes))


def load_registry(path: Path) -> ReasonCodeRegistry:
    """Convenience wrapper around `ReasonCodeRegistry.load_from_yaml`."""
    return ReasonCodeRegistry.load_from_yaml(path)
