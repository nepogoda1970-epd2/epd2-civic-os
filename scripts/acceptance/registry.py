"""Machine-readable check registry (INFRA01-HI-03).

Loads and validates ``check_registry.json``. Registry integrity is itself a
mandatory check: duplicate identifiers, empty stages, command checks without
commands or unknown expectation parsers make the registry invalid and the
whole run fails closed with :data:`codes.REGISTRY_INTEGRITY_FAILURE`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json, sha256_file

REGISTRY_FILE = Path(__file__).resolve().parent / "check_registry.json"

VALID_STATES = ("PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE_GOVERNED")
KNOWN_PARSERS = ("pytest", "vitest", "nodetest", "playwright")


@dataclass(frozen=True)
class Expectation:
    sentinel: str | None
    parsers: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Check:
    check_id: str
    stage_id: str
    title: str
    kind: str
    mandatory: bool
    command: tuple[str, ...]
    timeout_seconds: int
    expects: Expectation


@dataclass(frozen=True)
class Stage:
    stage_id: str
    title: str
    mandatory: bool
    checks: tuple[Check, ...]


@dataclass(frozen=True)
class Registry:
    schema: str
    registry_version: str
    registry_sha256: str
    stages: tuple[Stage, ...]
    problems: list[str] = field(default_factory=list)

    def all_checks(self) -> list[Check]:
        return [check for stage in self.stages for check in stage.checks]

    def mandatory_check_ids(self) -> list[str]:
        return [check.check_id for check in self.all_checks() if check.mandatory]


def _parse_expectation(raw: dict[str, Any], problems: list[str], check_id: str) -> Expectation:
    sentinel = raw.get("sentinel")
    parsers: list[tuple[str, int]] = []
    for parser in raw.get("parsers", []):
        parser_type = str(parser.get("type", ""))
        if parser_type not in KNOWN_PARSERS:
            problems.append(f"{check_id}: unknown expectation parser {parser_type!r}")
            continue
        parsers.append((parser_type, int(parser.get("min", 1))))
    return Expectation(
        sentinel=str(sentinel) if sentinel is not None else None, parsers=tuple(parsers)
    )


def load_registry(registry_file: Path = REGISTRY_FILE) -> Registry:
    document = load_json(registry_file)
    problems: list[str] = []
    stages: list[Stage] = []
    seen_check_ids: set[str] = set()
    seen_stage_ids: set[str] = set()

    for raw_stage in document.get("stages", []):
        stage_id = str(raw_stage.get("id", ""))
        if not stage_id:
            problems.append("stage without id")
            continue
        if stage_id in seen_stage_ids:
            problems.append(f"duplicate stage id {stage_id!r}")
        seen_stage_ids.add(stage_id)
        checks: list[Check] = []
        for raw_check in raw_stage.get("checks", []):
            check_id = str(raw_check.get("id", ""))
            if not check_id:
                problems.append(f"stage {stage_id!r}: check without id")
                continue
            if check_id in seen_check_ids:
                problems.append(f"duplicate check id {check_id!r}")
            seen_check_ids.add(check_id)
            kind = str(raw_check.get("kind", ""))
            command = tuple(str(part) for part in raw_check.get("command", []))
            if kind not in ("command", "internal"):
                problems.append(f"{check_id}: unknown check kind {kind!r}")
            if kind == "command" and not command:
                problems.append(f"{check_id}: command check without a command")
            if kind == "internal" and command:
                problems.append(f"{check_id}: internal check must not declare a command")
            checks.append(
                Check(
                    check_id=check_id,
                    stage_id=stage_id,
                    title=str(raw_check.get("title", check_id)),
                    kind=kind,
                    mandatory=bool(raw_check.get("mandatory", True)),
                    command=command,
                    timeout_seconds=int(raw_check.get("timeout_seconds", 600)),
                    expects=_parse_expectation(
                        dict(raw_check.get("expects", {})), problems, check_id
                    ),
                )
            )
        if not checks:
            problems.append(f"stage {stage_id!r} has no checks")
        stages.append(
            Stage(
                stage_id=stage_id,
                title=str(raw_stage.get("title", stage_id)),
                mandatory=bool(raw_stage.get("mandatory", True)),
                checks=tuple(checks),
            )
        )
    if not stages:
        problems.append("registry declares no stages")

    return Registry(
        schema=str(document.get("schema", "")),
        registry_version=str(document.get("registry_version", "")),
        registry_sha256=sha256_file(registry_file),
        stages=tuple(stages),
        problems=problems,
    )


def registry_findings(registry: Registry) -> list[str]:
    """Fail-closed problems as detector-coded strings."""
    return [f"{codes.REGISTRY_INTEGRITY_FAILURE}: {problem}" for problem in registry.problems]
