"""Runtime readiness contract foundation (INFRA01-HI-10, FIR-READY-001).

Fail-closed evaluation of a machine-readable readiness contract::

    process alive != runtime safe for consequential traffic

Overall readiness is READY only when every mandatory dimension is READY or
explicitly ``NOT_APPLICABLE_GOVERNED`` (which requires a governed rule
reference). ``UNKNOWN`` fails closed: an operator who cannot prove a
dimension has not proven readiness. INFRA-01 establishes the canonical
mechanism and semantics; wiring live services onto it is later INFRA/OPS
work.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json

SCHEMA_FILE = Path(__file__).resolve().parent / "schemas/readiness_contract.schema.json"

MANDATORY_DIMENSIONS = (
    "process_alive",
    "deployment_manifest_identity",
    "configuration_compatibility",
    "schema_compatibility",
    "key_trust_anchor_readiness",
    "dependency_readiness",
    "projection_freshness",
    "trusted_time",
    "migration_state",
    "restore_reconciliation_state",
)


@dataclass(frozen=True)
class ReadinessFinding:
    code: str
    dimension: str
    detail: str


@dataclass(frozen=True)
class ReadinessVerdict:
    overall: str
    findings: list[ReadinessFinding]


def load_schema(schema_file: Path = SCHEMA_FILE) -> dict[str, Any]:
    schema = load_json(schema_file)
    if not isinstance(schema, dict):
        raise ValueError(f"readiness-contract schema is not an object: {schema_file}")
    return schema


def evaluate(document: dict[str, Any]) -> ReadinessVerdict:
    """Evaluate one readiness contract; fail closed on anything unproven."""
    findings: list[ReadinessFinding] = []
    validator = jsonschema.Draft202012Validator(load_schema())
    for error in sorted(validator.iter_errors(document), key=lambda item: str(item.json_path)):
        findings.append(
            ReadinessFinding(
                codes.READINESS_UNKNOWN_FAILS_CLOSED,
                "contract",
                f"{error.json_path}: {error.message}",
            )
        )
    if findings:
        return ReadinessVerdict("NOT_READY", findings)

    dimensions = document["dimensions"]
    for name in MANDATORY_DIMENSIONS:
        entry = dimensions[name]
        status = str(entry["status"])
        if status == "READY":
            continue
        if status == "NOT_APPLICABLE_GOVERNED":
            if not str(entry.get("governed_rule", "")).strip():
                findings.append(
                    ReadinessFinding(
                        codes.READINESS_UNKNOWN_FAILS_CLOSED,
                        name,
                        "NOT_APPLICABLE_GOVERNED without a governed rule reference",
                    )
                )
            continue
        if status == "UNKNOWN":
            findings.append(
                ReadinessFinding(
                    codes.READINESS_UNKNOWN_FAILS_CLOSED,
                    name,
                    "readiness unknown; unknown fails closed",
                )
            )
        else:
            findings.append(
                ReadinessFinding(codes.READINESS_DIMENSION_NOT_READY, name, "dimension NOT_READY")
            )

    freshness = dimensions["projection_freshness"]
    if str(freshness["status"]) == "READY":
        watermark = freshness.get("watermark")
        required = freshness.get("required_position")
        if watermark is not None and required is not None and str(watermark) < str(required):
            findings.append(
                ReadinessFinding(
                    codes.READINESS_DIMENSION_NOT_READY,
                    "projection_freshness",
                    f"projection watermark {watermark!r} behind required authoritative "
                    f"position {required!r}; stale read models must not serve as current "
                    "authority",
                )
            )

    overall = "READY" if not findings else "NOT_READY"
    declared = document.get("overall")
    if declared is not None and str(declared) != overall:
        findings.append(
            ReadinessFinding(
                codes.READINESS_UNKNOWN_FAILS_CLOSED,
                "overall",
                f"declared overall {declared!r} contradicts evaluated {overall!r}",
            )
        )
        overall = "NOT_READY"
    return ReadinessVerdict(overall, findings)
